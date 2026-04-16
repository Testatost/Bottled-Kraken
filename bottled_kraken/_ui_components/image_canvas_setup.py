"""Mixin-Methoden für die Bild-Canvas."""
from ..shared import *
from .queue_widgets import OutlinedSimpleTextItem, ResizableRectItem
from .overlay_dialogs import OverlayBoxDialog

class ImageCanvasSetupMixin:
    def __init__(self, tr_func=None):
        super().__init__()
        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.NoDrag)
        self._space_panning = False
        # NEU: Maus-Panning (LMB drag)
        self._mouse_panning = False
        self._pan_start = QPoint()
        self._pan_start_h = 0
        self._pan_start_v = 0
        # Drag & Drop
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self._zoom = 1.0
        self._pixmap_item = None
        self._rects: Dict[int, QGraphicsRectItem] = {}
        self._labels: Dict[int, QGraphicsSimpleTextItem] = {}
        self._selected_idx: Optional[int] = None
        self._selected_indices: set[int] = set()
        self._bg_color = QColor("#333")
        self._pen_normal = QPen(QColor("#ff3b30"), 2)
        self._pen_selected = QPen(QColor("#0a84ff"), 3)
        self._brush_fill = QBrush(QColor(255, 59, 48, 30))
        self._brush_selected = QBrush(QColor(10, 132, 255, 60))
        self._drop_text = None
        self.tr_func = tr_func
        # Box-Zeichenmodus
        self._draw_mode = False
        self._draw_start = None
        self._draw_rect_item: Optional[QGraphicsRectItem] = None
        self._pen_draw = QPen(QColor("#00ff7f"), 2)
        self._brush_draw = QBrush(QColor(0, 255, 127, 40))
        # Multi-Selection per Mausziehen
        self._selection_mode = False
        self._selection_start = None
        self._selection_rect_item: Optional[QGraphicsRectItem] = None
        self._pen_selection = QPen(QColor("#0a84ff"), 2, Qt.DashLine)
        self._brush_selection = QBrush(QColor(10, 132, 255, 40))
        # Nur aktiv, nachdem die OCR abgeschlossen ist
        self._overlay_enabled = False
        # Split-Modus für bestehende Boxen
        self._split_mode = False
        self._split_target_idx: Optional[int] = None
        self._split_preview_item: Optional[QGraphicsLineItem] = None
        self._split_pen = QPen(QColor("#ffd60a"), 2, Qt.DashLine)
        self._show_drop_hint()

    def _get_view_state(self):
        # Gibt (Transform, Szenen-Zentrumspunkt, Zoom-Skalar) zurück.
        try:
            t = self.transform()
            center = self.mapToScene(self.viewport().rect().center())
            z = float(t.m11())  # angenommen: gleichmäßige Skalierung
            return t, center, z
        except Exception:
            return None, None, None

    def _restore_view_state(self, t, center, z):
        try:
            if t is not None:
                self.setTransform(t)
            if center is not None:
                self.centerOn(center)
            # internen Zoom synchron halten (wheelEvent nutzt ihn)
            if z is not None:
                self._zoom = float(z)
            else:
                self._zoom = float(self.transform().m11())
        except Exception:
            pass

    @staticmethod
    def _event_point(event) -> QPoint:
        # Funktioniert über verschiedene PySide6-Versionen hinweg: manchmal gibt es event.position(), manchmal nicht.
        try:
            p = event.position()
            return p.toPoint()
        except Exception:
            try:
                return event.pos()
            except Exception:
                return QPoint(0, 0)

    def set_overlay_enabled(self, enabled: bool):
        self._overlay_enabled = bool(enabled)

    def set_theme(self, theme: str):
        if theme == "dark":
            self._bg_color = QColor("#1e1e1e")
            self._pen_normal.setColor(QColor("#ff3b30"))
            self._pen_selected.setColor(QColor("#0a84ff"))
        else:
            self._bg_color = QColor("#f2f2f2")
            self._pen_normal.setColor(QColor("#d00000"))
            self._pen_selected.setColor(QColor("#0000ff"))
        self.setBackgroundBrush(QBrush(self._bg_color))
        if self._pixmap_item and hasattr(self, "_last_recs"):
            self.refresh_overlays()
        else:
            self._show_drop_hint()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if not event.mimeData().hasUrls():
            event.ignore()
            return
        for u in event.mimeData().urls():
            p = u.toLocalFile()
            if p and os.path.exists(p) and is_supported_drop_or_paste_file(p):
                event.acceptProposedAction()
                return
        event.ignore()

    def dragMoveEvent(self, event):
        if not event.mimeData().hasUrls():
            event.ignore()
            return
        for u in event.mimeData().urls():
            p = u.toLocalFile()
            if p and os.path.exists(p) and is_supported_drop_or_paste_file(p):
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        if not event.mimeData().hasUrls():
            event.ignore()
            return
        files = []
        for u in event.mimeData().urls():
            p = u.toLocalFile()
            if p and os.path.exists(p) and is_supported_drop_or_paste_file(p):
                files.append(p)
        if files:
            self.files_dropped.emit(files)
            event.acceptProposedAction()
        else:
            event.ignore()

    def start_draw_box_mode(self):
        if not self._overlay_enabled:
            return
        self._draw_mode = True
        self._draw_start = None
        self.setDragMode(QGraphicsView.NoDrag)

    def stop_draw_box_mode(self):
        self._draw_mode = False
        self._draw_start = None
        if self._draw_rect_item is not None:
            try:
                if isValid(self._draw_rect_item) and self._draw_rect_item.scene() is self.scene:
                    self.scene.removeItem(self._draw_rect_item)
            except RuntimeError:
                pass
            self._draw_rect_item = None
        self.setDragMode(QGraphicsView.NoDrag)

    def start_split_box_mode(self, idx: int):
        if not self._overlay_enabled:
            return
        if idx not in self._rects:
            return
        self._split_mode = True
        self._split_target_idx = idx
        self.viewport().setCursor(Qt.SplitHCursor)
        if self._split_preview_item is not None:
            try:
                if isValid(self._split_preview_item) and self._split_preview_item.scene() is self.scene:
                    self.scene.removeItem(self._split_preview_item)
            except RuntimeError:
                pass
            self._split_preview_item = None

    def stop_split_box_mode(self):
        self._split_mode = False
        self._split_target_idx = None
        self.viewport().unsetCursor()
        if self._split_preview_item is not None:
            try:
                if isValid(self._split_preview_item) and self._split_preview_item.scene() is self.scene:
                    self.scene.removeItem(self._split_preview_item)
            except RuntimeError:
                pass
            self._split_preview_item = None

    def start_selection_mode(self, scene_pos: QPointF):
        if not self._overlay_enabled:
            return
        self._selection_mode = True
        self._selection_start = scene_pos
        if self._selection_rect_item is not None:
            try:
                if isValid(self._selection_rect_item) and self._selection_rect_item.scene() is self.scene:
                    self.scene.removeItem(self._selection_rect_item)
            except RuntimeError:
                pass
            self._selection_rect_item = None
        self._selection_rect_item = QGraphicsRectItem(QRectF(scene_pos, scene_pos))
        self._selection_rect_item.setPen(self._pen_selection)
        self._selection_rect_item.setBrush(self._brush_selection)
        self._selection_rect_item.setZValue(999)
        self.scene.addItem(self._selection_rect_item)

    def stop_selection_mode(self):
        self._selection_mode = False
        self._selection_start = None
        if self._selection_rect_item is not None:
            try:
                if isValid(self._selection_rect_item) and self._selection_rect_item.scene() is self.scene:
                    self.scene.removeItem(self._selection_rect_item)
            except RuntimeError:
                pass
            self._selection_rect_item = None

    def select_indices(self, indices, center: bool = False):
        try:
            idxs = {int(i) for i in indices if i is not None}
        except Exception:
            idxs = set()
        self._selected_indices = idxs
        self._selected_idx = min(idxs) if idxs else None
        try:
            self.scene.clearSelection()
        except Exception:
            pass
        for idx, rect in self._rects.items():
            if not isValid(rect):
                continue
            is_sel = (idx in idxs)
            rect.setSelected(is_sel)
            if is_sel:
                rect.setPen(self._pen_selected)
                rect.setBrush(self._brush_selected)
                rect.setZValue(20)
            else:
                rect.setPen(self._pen_normal)
                rect.setBrush(self._brush_fill)
                rect.setZValue(10)
            rect.update()
        self.scene.update()
        self.viewport().update()
        if center and idxs:
            first = min(idxs)
            rect = self._rects.get(first)
            if rect and isValid(rect):
                self.centerOn(rect)

    def _finalize_selection_rect(self, additive: bool = False):
        if not self._selection_rect_item or not isValid(self._selection_rect_item):
            self.stop_selection_mode()
            return
        sel_rect = self._selection_rect_item.rect().normalized()
        hit = []
        for idx, rect in self._rects.items():
            if not isValid(rect):
                continue
            scene_rect = rect.mapRectToScene(rect.rect()).normalized()
            center = scene_rect.center()
            if sel_rect.intersects(scene_rect) or sel_rect.contains(center):
                hit.append(idx)
        if additive:
            hit = sorted(set(hit) | self._selected_indices)
        else:
            hit = sorted(set(hit))
        self.select_indices(hit, center=False)
        self.overlay_multi_selected.emit(hit)
        self.stop_selection_mode()
