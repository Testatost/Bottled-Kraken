"""Mixin-Methoden für die Bildbearbeitungs-Canvas."""
from ..shared import *
from .common import ImageEditSeparator

class ImageEditCanvasInteractionMixin:
    def mousePressEvent(self, event):
        if self.view_image is None:
            return
        wp = event.position()
        p = self._widget_to_image(wp)
        if (
            event.button() == Qt.LeftButton
            and (event.modifiers() & Qt.AltModifier)
            and self._can_pan_with_alt()
        ):
            self.drag_mode = "pan"
            self._pan_active = True
            self._pan_start_widget = QPointF(wp)
            self._pan_start_x = float(self._pan_x)
            self._pan_start_y = float(self._pan_y)
            self.setCursor(Qt.ClosedHandCursor)
            return
        if not self._image_rect_in_widget().contains(wp) and not self.rotation_mode:
            return
        if self.rotation_mode:
            sep_hit = None
            if self.show_separator and self.separator is not None:
                sep_hit = self._separator_hit(p)
            crop_edge = None
            crop_hit = False
            if self.show_crop:
                crop_edge = self._crop_edge_at(p)
                crop_hit = bool(crop_edge) or self._point_in_crop(p)
            erase_hit = False
            if self.show_erase:
                erase_hit = True
                if self.erase_rect is not None:
                    erase_hit = bool(self._rect_edge_at(self.erase_rect, p)) or self.erase_rect.contains(p) or self.show_erase
            # Wenn Crop, Trennbalken oder Entfernen aktiv sind, zuerst Hinweis statt Rotation
            if sep_hit is not None or crop_hit or self.show_crop or erase_hit:
                tr = getattr(self.parent(), "_tr", None)
                QMessageBox.information(
                    self,
                    tr("image_edit_notice_title") if callable(tr) else "Notice",
                    tr("image_edit_turn_off_rotation_first") if callable(tr) else "Rotation is still active."
                )
                return
            self.drag_mode = "img_rotate"
            self.rotation_start_angle = self.rotation_angle
            self.rotation_start_mouse_angle = self._mouse_angle_from_center(p)
            self.preview_rotation_angle = 0.0
            self.is_preview_rotating = True
            self.setCursor(Qt.ClosedHandCursor)
            return
        if self.show_separator and self.separator is not None:
            hit = self._separator_hit(p)
            if hit is not None:
                self.drag_mode = {"top": "sep_top", "bottom": "sep_bottom", "line": "sep_line", "rotate": "sep_rotate"}[hit]
                if hit == "line":
                    self.sep_offset = QPointF(self.separator.cx - p.x(), self.separator.cy - p.y())
                self.drag_start = p
                self.update()
                return
        if self.show_erase:
            edge = self._rect_edge_at(self.erase_rect, p)
            if self.erase_rect is not None and edge:
                self.drag_mode = f"erase_resize:{edge}"
                self.drag_start = p
                self.rect_before = QRectF(self.erase_rect)
                return
            if self.erase_rect is not None and self.erase_rect.contains(p):
                self.drag_mode = "erase_move"
                self.drag_start = p
                self.rect_before = QRectF(self.erase_rect)
                return
            self.drag_mode = "erase_new"
            self.drag_start = p
            self.erase_rect = QRectF(p, p)
            self.update()
            self.changed.emit()
            return
        if self.show_crop:
            edge = self._crop_edge_at(p)
            if self.crop_rect is not None and edge:
                self.drag_mode = f"crop_resize:{edge}"
                self.drag_start = p
                self.rect_before = QRectF(self.crop_rect)
                return
            if self._point_in_crop(p):
                self.drag_mode = "crop_move"
                self.drag_start = p
                self.rect_before = QRectF(self.crop_rect)
                return
            self.drag_mode = "crop_new"
            self.drag_start = p
            self.crop_rect = QRectF(p, p)
            self.update()
            self.changed.emit()

    def mouseMoveEvent(self, event):
        wp = event.position()
        p = self._widget_to_image(wp)
        if self.drag_mode == "pan":
            delta = wp - self._pan_start_widget
            self._pan_x = self._pan_start_x + delta.x()
            self._pan_y = self._pan_start_y + delta.y()
            self._clamp_pan()
            self._update_image_offset()
            self.update()
            return
        if self.drag_mode == "img_rotate":
            delta = self._mouse_angle_from_center(p) - self.rotation_start_mouse_angle
            new_angle = self.rotation_start_angle + delta
            if event.modifiers() & Qt.ControlModifier:
                new_angle = round(new_angle)
            self.preview_rotation_angle = new_angle - self.rotation_angle
            self.update()
            return
        if self.drag_mode == "sep_top" and self.separator and self.view_image is not None:
            fixed = self.separator.bottom_handle(*self.view_image.size)
            dragged = self._project_to_border(p.x(), p.y())
            self.separator.set_from_points(dragged, fixed)
            self.update(); self.changed.emit(); return
        if self.drag_mode == "sep_bottom" and self.separator and self.view_image is not None:
            fixed = self.separator.top_handle(*self.view_image.size)
            dragged = self._project_to_border(p.x(), p.y())
            self.separator.set_from_points(fixed, dragged)
            self.update(); self.changed.emit(); return
        if self.drag_mode == "sep_line" and self.separator and self.view_image is not None:
            new_x = p.x() + self.sep_offset.x(); new_y = p.y() + self.sep_offset.y()
            self.separator.move_by(new_x - self.separator.cx, new_y - self.separator.cy, *self.view_image.size)
            self.update(); self.changed.emit(); return
        if self.drag_mode == "sep_rotate" and self.separator:
            dx = p.x() - self.separator.cx; dy = p.y() - self.separator.cy
            if abs(dx) > 1e-6 or abs(dy) > 1e-6:
                raw = math.atan2(dy, dx) - math.pi / 2
                if event.modifiers() & Qt.ControlModifier:
                    step = math.radians(5)
                    raw = round(raw / step) * step
                self.separator.angle = raw
                self.update(); self.changed.emit(); return
        if self.drag_mode == "erase_move" and self.erase_rect and self.rect_before:
            r = QRectF(self.rect_before)
            r.translate(p - self.drag_start)
            self.erase_rect = self._clamp_rect(r)
            self.update()
            self.changed.emit()
            return
        if self.drag_mode and str(self.drag_mode).startswith("erase_resize:") and self.rect_before:
            edge = self.drag_mode.split(":", 1)[1]
            r = QRectF(self.rect_before)
            if "left" in edge:
                r.setLeft(min(p.x(), r.right() - 5))
            if "right" in edge:
                r.setRight(max(p.x(), r.left() + 5))
            if "top" in edge:
                r.setTop(min(p.y(), r.bottom() - 5))
            if "bottom" in edge:
                r.setBottom(max(p.y(), r.top() + 5))
            self.erase_rect = self._clamp_rect(r)
            self.update()
            self.changed.emit()
            return
        if self.drag_mode == "erase_new":
            x1 = min(self.drag_start.x(), p.x())
            y1 = min(self.drag_start.y(), p.y())
            x2 = max(self.drag_start.x(), p.x())
            y2 = max(self.drag_start.y(), p.y())
            self.erase_rect = self._clamp_rect(QRectF(x1, y1, x2 - x1, y2 - y1))
            self.update()
            self.changed.emit()
            return
        if self.drag_mode == "crop_move" and self.crop_rect and self.rect_before:
            r = QRectF(self.rect_before);
            r.translate(p - self.drag_start)
            self.crop_rect = self._clamp_rect(r)
            self.update();
            self.changed.emit();
            return
        if self.drag_mode and str(self.drag_mode).startswith("crop_resize:") and self.rect_before:
            edge = self.drag_mode.split(":", 1)[1]
            r = QRectF(self.rect_before)
            if "left" in edge: r.setLeft(min(p.x(), r.right() - 5))
            if "right" in edge: r.setRight(max(p.x(), r.left() + 5))
            if "top" in edge: r.setTop(min(p.y(), r.bottom() - 5))
            if "bottom" in edge: r.setBottom(max(p.y(), r.top() + 5))
            self.crop_rect = self._clamp_rect(r)
            self.update();
            self.changed.emit();
            return
        if self.drag_mode == "crop_new":
            x1 = min(self.drag_start.x(), p.x());
            y1 = min(self.drag_start.y(), p.y())
            x2 = max(self.drag_start.x(), p.x());
            y2 = max(self.drag_start.y(), p.y())
            self.crop_rect = self._clamp_rect(QRectF(x1, y1, x2 - x1, y2 - y1))
            self.update();
            self.changed.emit();
            return
        self._update_cursor(p)

    def mouseReleaseEvent(self, event):
        if self.drag_mode == "img_rotate":
            self.rotation_angle = (self.rotation_angle + self.preview_rotation_angle) % 360.0
            self.preview_rotation_angle = 0.0
            self.is_preview_rotating = False
            self.rotation_committed.emit(float(self.rotation_angle))
        if self.drag_mode == "pan":
            self._pan_active = False
        self.drag_mode = None
        self.rect_before = None
        self.sep_offset = QPointF()
        wp = event.position()
        self._update_cursor(self._widget_to_image(wp))
        self.update()
        self.changed.emit()

    def wheelEvent(self, event):
        if self.base_image is None:
            return
        old_crop = self.get_crop_orig()
        old_erase = self.get_erase_orig() if self.show_erase else None
        self.zoom = max(0.2, min(6.0, self.zoom * (1.1 if event.angleDelta().y() > 0 else 0.9)))
        self._update_view_image()
        self._clamp_pan()
        self._update_image_offset()
        self.set_crop_from_orig(old_crop)
        if old_erase:
            self.set_erase_from_orig(old_erase)
        self._ensure_separator_inside()
        self.update()
        self.changed.emit()

    def resizeEvent(self, event):
        old_crop = self.get_crop_orig()
        old_erase = self.get_erase_orig() if self.show_erase else None
        self._update_view_image()
        self.set_crop_from_orig(old_crop)
        if old_erase:
            self.set_erase_from_orig(old_erase)
        self._ensure_separator_inside()
        self._clamp_pan()
        self._update_image_offset()
        self.update()
        super().resizeEvent(event)

    def _clamp_rect(self, rect: QRectF) -> QRectF:
        if self.view_image is None:
            return rect
        w, h = self.view_image.size
        x1 = max(0, min(rect.left(), w - 5)); y1 = max(0, min(rect.top(), h - 5))
        x2 = max(x1 + 5, min(rect.right(), w)); y2 = max(y1 + 5, min(rect.bottom(), h))
        return QRectF(x1, y1, x2 - x1, y2 - y1)

    def _update_cursor(self, p: QPointF):
        if self.rotation_mode:
            self.setCursor(Qt.OpenHandCursor)
            return
        if self._pan_active:
            self.setCursor(Qt.ClosedHandCursor)
            return
        if self._can_pan_with_alt() and (QApplication.keyboardModifiers() & Qt.AltModifier):
            self.setCursor(Qt.OpenHandCursor)
            return
        if self.show_separator and self.separator is not None:
            hit = self._separator_hit(p)
            if hit in ("rotate", "top", "bottom", "line"):
                self.setCursor(Qt.SizeAllCursor)
                return
        if self.show_erase and self.erase_rect is not None:
            edge = self._rect_edge_at(self.erase_rect, p)
            if edge:
                self.setCursor(
                    Qt.SizeHorCursor if edge in ("left", "right")
                    else Qt.SizeVerCursor if edge in ("top", "bottom")
                    else Qt.SizeFDiagCursor
                )
                return
            if self.erase_rect.contains(p):
                self.setCursor(Qt.SizeAllCursor)
                return
        if self.show_crop:
            edge = self._crop_edge_at(p)
            if edge:
                self.setCursor(
                    Qt.SizeHorCursor if edge in ("left", "right")
                    else Qt.SizeVerCursor if edge in ("top", "bottom")
                    else Qt.SizeFDiagCursor
                )
                return
            if self._point_in_crop(p):
                self.setCursor(Qt.SizeAllCursor)
                return
        self.setCursor(Qt.CrossCursor)

    def _rect_edge_at(self, rect: Optional[QRectF], p: QPointF) -> Optional[str]:
        if rect is None:
            return None
        pad = 8.0
        x = p.x()
        y = p.y()
        left = abs(x - rect.left()) <= pad
        right = abs(x - rect.right()) <= pad
        top = abs(y - rect.top()) <= pad
        bottom = abs(y - rect.bottom()) <= pad
        if left and top:
            return "left_top"
        if right and top:
            return "right_top"
        if left and bottom:
            return "left_bottom"
        if right and bottom:
            return "right_bottom"
        if left:
            return "left"
        if right:
            return "right"
        if top:
            return "top"
        if bottom:
            return "bottom"
        return None
