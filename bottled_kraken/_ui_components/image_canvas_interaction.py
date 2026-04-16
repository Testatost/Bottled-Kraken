"""Mixin-Methoden für die Bild-Canvas."""
from ..shared import *
from .queue_widgets import OutlinedSimpleTextItem, ResizableRectItem
from .overlay_dialogs import OverlayBoxDialog

class ImageCanvasInteractionMixin:
    def contextMenuEvent(self, event):
        pos = event.pos()
        item = self.itemAt(pos)
        menu = QMenu(self)
        tr = self.tr_func
        if not self._overlay_enabled:
            disabled = menu.addAction(
                tr("overlay_only_after_ocr") if tr else "Overlay-Bearbeitung erst nach abgeschlossener OCR möglich.")
            disabled.setEnabled(False)
            menu.exec(event.globalPos())
            return
        if isinstance(item, ResizableRectItem):
            idx = item.idx
            act_split = menu.addAction(tr("canvas_menu_split_box") if tr else "Split box")
            act_del = menu.addAction(tr("canvas_menu_delete_box") if tr else "Delete overlay box")
            menu.addSeparator()
            act_add_draw = menu.addAction(tr("canvas_menu_add_box_draw") if tr else "Add overlay box (draw)")
            chosen = menu.exec(event.globalPos())
            if not chosen:
                return
            elif chosen == act_split:
                self.start_split_box_mode(idx)
            elif chosen == act_del:
                self.overlay_delete_requested.emit(idx)
            elif chosen == act_add_draw:
                self.overlay_add_draw_requested.emit(self.mapToScene(pos))
            return
        act_add_draw = menu.addAction(tr("canvas_menu_add_box_draw") if tr else "Add overlay box (draw)")
        chosen = menu.exec(event.globalPos())
        if not chosen:
            return
        if chosen == act_add_draw:
            self.overlay_add_draw_requested.emit(self.mapToScene(pos))

    def mousePressEvent(self, event):
        if self._split_mode and event.button() == Qt.LeftButton:
            rect_item = self._rects.get(self._split_target_idx)
            if rect_item and isValid(rect_item):
                scene_rect = rect_item.mapRectToScene(rect_item.rect()).normalized()
                sp = self.mapToScene(self._event_point(event))
                if scene_rect.contains(sp):
                    split_x = max(scene_rect.left() + 8.0, min(scene_rect.right() - 8.0, sp.x()))
                    self.box_split_requested.emit(self._split_target_idx, float(split_x))
            self.stop_split_box_mode()
            event.accept()
            return
        if event.button() == Qt.LeftButton:
            it = self.itemAt(self._event_point(event))
            # Klick auf Nummernlabel auf die zugehörige Box umlenken
            if isinstance(it, QGraphicsSimpleTextItem):
                txt = it.text().strip()
                if txt.isdigit():
                    idx = int(txt) - 1
                    rect = self._rects.get(idx)
                    if rect and isValid(rect):
                        it = rect
            # 1) Zeichenmodus hat höchste Priorität
            if self._draw_mode and self._overlay_enabled and self._pixmap_item is not None:
                sp = self.mapToScene(self._event_point(event))
                self._draw_start = sp
                if self._draw_rect_item is not None:
                    try:
                        if isValid(self._draw_rect_item) and self._draw_rect_item.scene() is self.scene:
                            self.scene.removeItem(self._draw_rect_item)
                    except RuntimeError:
                        pass
                    self._draw_rect_item = None
                self._draw_rect_item = QGraphicsRectItem(QRectF(sp, sp))
                self._draw_rect_item.setPen(self._pen_draw)
                self._draw_rect_item.setBrush(self._brush_draw)
                self._draw_rect_item.setZValue(999)
                self.scene.addItem(self._draw_rect_item)
                event.accept()
                return
            # Klick direkt auf eine Overlay-Box
            if isinstance(it, ResizableRectItem):
                ctrl_pressed = bool(event.modifiers() & Qt.ControlModifier)
                if ctrl_pressed:
                    new_selection = set(self._selected_indices)
                    if it.idx in new_selection:
                        new_selection.remove(it.idx)
                    else:
                        new_selection.add(it.idx)
                    new_selection = sorted(new_selection)
                    self.select_indices(new_selection, center=False)
                    self.overlay_multi_selected.emit(new_selection)
                    if new_selection:
                        self._selected_idx = it.idx if it.idx in new_selection else min(new_selection)
                    else:
                        self._selected_idx = None
                    event.accept()
                    return
                # WICHTIG:
                # Nicht hier den Event "schlucken".
                # Die ResizableRectItem muss den Mausklick selbst bekommen,
                # damit Move/Resize funktioniert.
                super().mousePressEvent(event)
                return
            # Panning nur mit Alt + linker Maustaste
            if (
                    self._pixmap_item is not None
                    and self._zoom > (self._fit_zoom * 1.01)
                    and (event.modifiers() & Qt.AltModifier)
            ):
                self._mouse_panning = True
                self._pan_start = self._event_point(event)
                self._pan_start_h = self.horizontalScrollBar().value()
                self._pan_start_v = self.verticalScrollBar().value()
                self.setCursor(Qt.ClosedHandCursor)
                event.accept()
                return
            # Rechteckauswahl nur wenn NICHT im Zeichenmodus
            if (
                    self._overlay_enabled
                    and self._pixmap_item is not None
                    and not self._draw_mode
                    and not (event.modifiers() & Qt.AltModifier)
            ):
                sp = self.mapToScene(self._event_point(event))
                self.start_selection_mode(sp)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(self._event_point(event))
        if isinstance(item, ResizableRectItem) and event.button() == Qt.LeftButton:
            self.rect_clicked.emit(item.idx)
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        if self._split_mode and self._split_target_idx is not None:
            rect_item = self._rects.get(self._split_target_idx)
            if rect_item and isValid(rect_item):
                scene_rect = rect_item.mapRectToScene(rect_item.rect()).normalized()
                sp = self.mapToScene(self._event_point(event))
                split_x = max(scene_rect.left() + 8.0, min(scene_rect.right() - 8.0, sp.x()))
                if self._split_preview_item is None:
                    self._split_preview_item = QGraphicsLineItem()
                    self._split_preview_item.setPen(self._split_pen)
                    self._split_preview_item.setZValue(999)
                    self.scene.addItem(self._split_preview_item)
                self._split_preview_item.setLine(split_x, scene_rect.top(), split_x, scene_rect.bottom())
                event.accept()
                return
        if self._mouse_panning:
            p = self._event_point(event)
            delta = p - self._pan_start
            self.horizontalScrollBar().setValue(self._pan_start_h - delta.x())
            self.verticalScrollBar().setValue(self._pan_start_v - delta.y())
            event.accept()
            return
        if self._draw_mode and self._draw_start and self._draw_rect_item is not None:
            sp = self.mapToScene(self._event_point(event))
            r = QRectF(self._draw_start, sp).normalized()
            if isValid(self._draw_rect_item):
                self._draw_rect_item.setRect(r)
            return
        if self._selection_mode and self._selection_start and self._selection_rect_item is not None:
            sp = self.mapToScene(self._event_point(event))
            r = QRectF(self._selection_start, sp).normalized()
            if isValid(self._selection_rect_item):
                self._selection_rect_item.setRect(r)
            # Live-Vorschau: alle getroffenen Boxen sofort blau markieren
            hit = []
            for idx, rect in self._rects.items():
                if not isValid(rect):
                    continue
                scene_rect = rect.mapRectToScene(rect.rect()).normalized()
                center = scene_rect.center()
                if r.intersects(scene_rect) or r.contains(center):
                    hit.append(idx)
            self.select_indices(hit, center=False)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._draw_mode and event.button() == Qt.LeftButton and self._draw_start and self._draw_rect_item is not None:
            rect = None
            if isValid(self._draw_rect_item):
                rect = self._draw_rect_item.rect().normalized()
            self.stop_draw_box_mode()
            if rect and rect.width() >= 5 and rect.height() >= 5:
                self.box_drawn.emit(rect)
            return
        if event.button() == Qt.LeftButton and self._selection_mode:
            self._finalize_selection_rect(additive=False)
            event.accept()
            return
        if event.button() == Qt.LeftButton and self._mouse_panning:
            self._mouse_panning = False
            self.unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)
