"""Mixin-Methoden für die Bild-Canvas."""
from ..shared import *
from .queue_widgets import OutlinedSimpleTextItem, ResizableRectItem
from .overlay_dialogs import OverlayBoxDialog

class ImageCanvasRenderingMixin:
    def clear_all(self):
        self.stop_draw_box_mode()
        self.stop_selection_mode()
        self.stop_split_box_mode()
        self.scene.clear()
        self._pixmap_item = None
        self._rects.clear()
        self._labels.clear()
        self._selected_idx = None
        self._selected_indices.clear()
        self._drop_text = None
        self.resetTransform()
        self._zoom = 1.0
        self._fit_zoom = 1.0
        self._show_drop_hint()

    def _center_drop_hint_in_view(self):
        if not self._drop_text or self._pixmap_item:
            return
        # Mittelpunkt des sichtbaren Viewports in Scene-Koordinaten
        center = self.mapToScene(self.viewport().rect().center())
        rect = self._drop_text.boundingRect()
        self._drop_text.setPos(center.x() - rect.width() / 2, center.y() - rect.height() / 2)
        # Szene so setzen, dass der Text sicher enthalten ist (sonst kann Qt komisch scrollen)
        br = self.scene.itemsBoundingRect()
        if br.isValid():
            self.setSceneRect(br.adjusted(-50, -50, 50, 50))

    def _show_drop_hint(self):
        if self._pixmap_item:
            return
        font = QFont("Arial", 20)
        font.setItalic(True)
        txt = self.tr_func("drop_hint") if self.tr_func else ""
        c = QColor("#aaa") if self._bg_color.lightness() < 128 else QColor("#555")
        # Wenn schon vorhanden: nur aktualisieren
        if self._drop_text and isValid(self._drop_text):
            self._drop_text.setFont(font)
            self._drop_text.setPlainText(txt)
            self._drop_text.setDefaultTextColor(c)
            self._center_drop_hint_in_view()
            return
        # Sonst: neu erzeugen
        self._drop_text = self.scene.addText(txt, font)
        self._drop_text.setAcceptedMouseButtons(Qt.NoButton)
        self._drop_text.setDefaultTextColor(c)
        self._center_drop_hint_in_view()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._pixmap_item:
            self._center_drop_hint_in_view()

    def load_pil_image(self, im: Image.Image, preserve_view: bool = False):
        # Aktuellen View-Status VOR dem Leeren speichern
        t = center = z = None
        if preserve_view:
            t, center, z = self._get_view_state()
        self.stop_draw_box_mode()
        self.scene.clear()
        self._pixmap_item = None
        self._rects.clear()
        self._labels.clear()
        self._selected_idx = None
        self._drop_text = None
        # WICHTIG: Nicht immer reset/fitten, wenn wir die Ansicht beibehalten sollen
        if not preserve_view:
            self.resetTransform()
            self._zoom = 1.0
        qim = ImageQt(im.convert("RGB"))
        pix = QPixmap.fromImage(qim)
        self._pixmap_item = self.scene.addPixmap(pix)
        self._pixmap_item.setZValue(0)
        self._pixmap_item.setAcceptedMouseButtons(Qt.NoButton)
        self._pixmap_item.setAcceptHoverEvents(False)
        self.setSceneRect(self.scene.itemsBoundingRect())
        if preserve_view and t is not None:
            self._restore_view_state(t, center, z)
        else:
            self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
            try:
                self._zoom = float(self.transform().m11())
                self._fit_zoom = self._zoom
            except Exception:
                self._zoom = 1.0
                self._fit_zoom = 1.0

    def refresh_overlays(self):
        if self._pixmap_item and hasattr(self, "_last_recs"):
            for r in list(self._rects.values()):
                try:
                    if isValid(r) and r.scene() is self.scene:
                        self.scene.removeItem(r)
                except RuntimeError:
                    pass
            for l in list(self._labels.values()):
                try:
                    if isValid(l) and l.scene() is self.scene:
                        self.scene.removeItem(l)
                except RuntimeError:
                    pass
            self._rects.clear()
            self._labels.clear()
            self.draw_overlays(self._last_recs)

    def _on_rect_item_changed(self, idx: int, scene_rect: QRectF):
        self.rect_changed.emit(idx, scene_rect)

    def _on_rect_item_clicked(self, idx: int):
        self.rect_clicked.emit(idx)

    def _on_rect_item_double_clicked(self, idx: int):
        self.rect_clicked.emit(idx)

    def draw_overlays(self, recs: List[RecordView]):
        self._last_recs = recs
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        for rv in recs:
            if not rv.bbox:
                continue
            x0, y0, x1, y1 = rv.bbox
            rectf = QRectF(x0, y0, x1 - x0, y1 - y0)
            ritem = ResizableRectItem(
                rectf,
                rv.idx,
                self._on_rect_item_changed,
                on_clicked=self._on_rect_item_clicked,
                on_double_clicked=self._on_rect_item_double_clicked
            )
            ritem.setPen(self._pen_normal)
            ritem.setBrush(self._brush_fill)
            ritem.setZValue(10)
            self.scene.addItem(ritem)
            self._rects[rv.idx] = ritem
            lab = OutlinedSimpleTextItem(str(rv.idx + 1))
            lab.setFont(font)
            lab.set_text_style(QColor("#000000"), QColor("#ffffff"), 1.0)
            lab.setZValue(11)
            lab.setPos(x0, max(0, y0 - 16))
            lab.setAcceptedMouseButtons(Qt.NoButton)
            self.scene.addItem(lab)
            self._labels[rv.idx] = lab

    def select_idx(self, idx: Optional[int], center: bool = True):
        if idx is None:
            self.select_indices([], center=False)
        else:
            self.select_indices([idx], center=center)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self._apply_zoom(1.25)
        else:
            self._apply_zoom(0.8)

    def _apply_zoom(self, factor: float):
        new_zoom = self._zoom * factor
        if 0.05 <= new_zoom <= 20.0:
            self.scale(factor, factor)
            self._zoom = new_zoom
        if not self._draw_mode and not self._mouse_panning:
            self.unsetCursor()
