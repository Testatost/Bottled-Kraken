"""Mixin-Methoden für die Bildbearbeitungs-Canvas."""
from ...shared import *
from ..common import ImageEditSeparator

class ImageEditCanvasMouseReleaseContextMixin:
        def mouseReleaseEvent(self, event):
            if self.drag_mode == "img_rotate":
                self.rotation_angle = (self.rotation_angle + self.preview_rotation_angle) % 360.0
                self.preview_rotation_angle = 0.0
                self.is_preview_rotating = False
                self.rotation_committed.emit(float(self.rotation_angle))
            finished_mode = self.drag_mode
            if self.drag_mode == "pan":
                self._pan_active = False
            if self.drag_mode == "selection_new":
                if self.selection_rect is not None and (self.selection_rect.width() < 6 or self.selection_rect.height() < 6):
                    self.selection_rect = None
                    self.selection_polygon = None
            if self.drag_mode == "selection_freehand":
                pts = self._simplify_selection_points(list(getattr(self, "_freehand_points", []) or []), 12.0)
                if len(pts) >= 3:
                    self._set_selection_polygon(pts)
                else:
                    self.selection_rect = None
                    self.selection_polygon = None
            if self.drag_mode == "crop_new":
                if self.crop_rect is not None and (self.crop_rect.width() < 6 or self.crop_rect.height() < 6):
                    self.delete_selected_crop()
                else:
                    self._store_active_crop()
            self.drag_mode = None
            parent = self.parent()
            if finished_mode and finished_mode != "pan" and parent is not None:
                hist = getattr(parent, "_history_push", None)
                if callable(hist):
                    hist()
            self.rect_before = None
            self.sep_offset = QPointF()
            self._transform_drag_points = None
            self._transform_rotate_points = None
            self._transform_drag_index = -1
            self._transform_scale_axis_lock = None
            self._transform_perspective_axis_lock = None
            self._transform_warp_start_x = 0.0
            self._transform_warp_start_y = 0.0
            self._transform_warp_start_grid = None
            self._transform_warp_free_start = None
            self._transform_warp_free_weights = None
            self._transform_rotate_start_value = 0.0
            self._selection_point_drag_index = -1
            self._freehand_points = []
            wp = event.position() if hasattr(event, "position") else QPointF(event.pos())
            self._update_cursor(self._widget_to_image(wp))
            self.update()
            self.changed.emit()

        def contextMenuEvent(self, event):
            parent = self.parent()
            if not parent:
                return super().contextMenuEvent(event)
            wp = event.position() if hasattr(event, "position") else QPointF(event.pos())
            p = self._widget_to_image(QPointF(wp))
            if self.has_active_transform() and self._transform_hit(p) is not None:
                handler = getattr(parent, "_show_transform_context_menu", None)
                if callable(handler):
                    handler(event.globalPos())
                    event.accept()
                    return
            if self.selection_exists() and (self._point_in_selection(p) or self._selection_edge_at(p)):
                handler = getattr(parent, "_show_selection_context_menu", None)
                if callable(handler):
                    handler(event.globalPos())
                    event.accept()
                    return
            crop_idx = self._crop_hit_index(p) if getattr(self, "show_crop", False) else None
            if crop_idx is not None:
                self.select_crop_index(crop_idx)
                handler = getattr(parent, "_show_crop_context_menu", None)
                if callable(handler):
                    handler(event.globalPos())
                    event.accept()
                    return
            handler = getattr(parent, "_show_image_context_menu", None)
            if callable(handler):
                handler(event.globalPos())
                event.accept()
                return
            super().contextMenuEvent(event)
