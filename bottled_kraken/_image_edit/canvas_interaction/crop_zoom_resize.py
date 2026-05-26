"""Mixin-Methoden für die Bildbearbeitungs-Canvas."""
from ...shared import *
from ..common import ImageEditSeparator

class ImageEditCanvasCropZoomResizeMixin:
        def begin_crop_drag_from_widget_pos(self, widget_pos):
            """Startet einen neuen Crop-Bereich, der sofort mit linker Maustaste gezogen werden kann."""
            if self.view_image is None:
                return
            p = self._widget_to_image(QPointF(widget_pos))
            if not self._image_rect_in_widget().contains(QPointF(widget_pos)):
                return
            self.show_crop = True
            if not hasattr(self, "crop_rects"):
                self.crop_rects = []
            self._store_active_crop()
            self.selected_crop_index = len(self.crop_rects)
            self.crop_rect = QRectF(p, p)
            self.crop_rects.append(QRectF(self.crop_rect))
            self.drag_mode = "crop_new"
            self.drag_start = QPointF(p)
            self.update()
            self.changed.emit()

        def wheelEvent(self, event):
            if self.base_image is None:
                return
            dy = self._wheel_zoom_delta(event)
            if dy == 0:
                event.accept()
                return

            widget_pos = event.position() if hasattr(event, "position") else QPointF(event.pos())
            old_img_pos = self._widget_to_image(widget_pos)
            old_view_w = float(self.view_pixmap.width()) if self.view_pixmap is not None else 1.0
            old_view_h = float(self.view_pixmap.height()) if self.view_pixmap is not None else 1.0
            rel_x = old_img_pos.x() / max(1.0, old_view_w)
            rel_y = old_img_pos.y() / max(1.0, old_view_h)

            old_crops = self.get_all_crops_orig() if hasattr(self, "get_all_crops_orig") else []
            old_crop_idx = getattr(self, "selected_crop_index", -1)
            old_erase = self.get_erase_orig() if self.show_erase else None
            old_transform = self.get_transform_state_norm()
            old_selection = None if old_transform else (
                self.get_selection_state_orig()
                if hasattr(self, "get_selection_state_orig") and getattr(self, "show_selection", False)
                else (self.get_selection_orig() if getattr(self, "show_selection", False) else None)
            )

            self.zoom = max(0.2, min(6.0, self.zoom * (1.1 if dy > 0 else 0.9)))
            self._update_view_image()

            if self.view_pixmap is not None:
                new_view_w = float(self.view_pixmap.width())
                new_view_h = float(self.view_pixmap.height())
                base_x = max(0.0, (self.width() - new_view_w) / 2.0)
                base_y = max(0.0, (self.height() - new_view_h) / 2.0)
                target_x = rel_x * new_view_w
                target_y = rel_y * new_view_h
                self._pan_x = widget_pos.x() - base_x - target_x
                self._pan_y = widget_pos.y() - base_y - target_y
                self._clamp_pan()
                self._update_image_offset()

            self.set_crops_from_orig(old_crops, old_crop_idx)
            if old_erase:
                self.set_erase_from_orig(old_erase)
            if old_selection:
                if isinstance(old_selection, dict) and hasattr(self, "set_selection_state_from_orig"):
                    self.set_selection_state_from_orig(old_selection)
                else:
                    self.set_selection_from_orig(old_selection)
            if old_transform:
                self.restore_transform_state_norm(old_transform)
            elif old_selection:
                if isinstance(old_selection, dict) and hasattr(self, "set_selection_state_from_orig"):
                    self.set_selection_state_from_orig(old_selection)
                else:
                    self.set_selection_from_orig(old_selection)
            self._ensure_separator_inside()
            self.update()
            self.changed.emit()
            event.accept()

        def _wheel_zoom_delta(self, event) -> int:
            angle_delta = event.angleDelta()
            dy = int(angle_delta.y())
            if dy != 0:
                return dy
            try:
                mods = event.modifiers()
            except Exception:
                mods = QApplication.keyboardModifiers()
            if (mods & Qt.AltModifier) and not (mods & Qt.ShiftModifier):
                dx = int(angle_delta.x())
                if dx != 0:
                    return dx
            return 0

        def resizeEvent(self, event):
            old_crops = self.get_all_crops_orig()
            old_crop_idx = getattr(self, "selected_crop_index", -1)
            old_erase = self.get_erase_orig() if self.show_erase else None
            old_transform = self.get_transform_state_norm()
            old_selection = (
                self.get_selection_state_orig()
                if hasattr(self, "get_selection_state_orig") and getattr(self, "show_selection", False)
                else (self.get_selection_orig() if getattr(self, "show_selection", False) else None)
            )
            self._update_view_image()
            self.set_crops_from_orig(old_crops, old_crop_idx)
            if old_erase:
                self.set_erase_from_orig(old_erase)
            if old_transform:
                self.restore_transform_state_norm(old_transform)
            self._ensure_separator_inside()
            self._clamp_pan()
            self._update_image_offset()
            self.update()
            super().resizeEvent(event)
