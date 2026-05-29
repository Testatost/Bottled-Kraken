from bottled_kraken.common import (
    QMessageBox,
    QPointF,
    QRectF,
    Qt,
    math,
)
from bottled_kraken._image_edit.common import ImageEditSeparator
class ImageEditCanvasKeyboardAndPressMixin:
        def keyPressEvent(self, event):
            parent = self.parent()
            if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_Z:
                handler = getattr(parent, "_undo_action", None)
                if callable(handler):
                    handler()
                    event.accept()
                    return
            if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_Y:
                handler = getattr(parent, "_redo_action", None)
                if callable(handler):
                    handler()
                    event.accept()
                    return
            if event.key() == Qt.Key_Escape:
                handler = getattr(parent, "_clear_selection", None)
                if callable(handler):
                    handler()
                    event.accept()
                    return
            if event.key() == Qt.Key_Delete:
                handler = getattr(parent, "_delete_selected_crop_or_erase", None)
                if callable(handler):
                    handler()
                    event.accept()
                    return
            super().keyPressEvent(event)
        def mousePressEvent(self, event):
            if self.view_image is None:
                return
            wp = event.position()
            p = self._widget_to_image(wp)
            if event.button() == Qt.RightButton:
                event.accept()
                return
            if event.button() == Qt.LeftButton and self._event_requests_pan(event) and not (self.has_active_transform() and self._transform_hit(p) is not None) and not (getattr(self, "show_selection", False) and self._selection_point_hit(p) >= 0):
                if self._can_pan_with_alt():
                    self.drag_mode = "pan"
                    self._pan_active = True
                    self._pan_start_widget = QPointF(wp)
                    self._pan_start_x = float(self._pan_x)
                    self._pan_start_y = float(self._pan_y)
                    self.setCursor(Qt.ClosedHandCursor)
                return
            if not self._image_rect_in_widget().contains(wp) and not self.rotation_mode:
                return
            if self.has_active_transform():
                hit = self._transform_hit(p)
                if hit is not None:
                    hit_type, hit_index = hit
                    mode = str(self.transform_mode or "scale")
                    self.drag_start = QPointF(p)
                    if mode == "rotate":
                        self.drag_mode = "transform_rotate"
                        self._transform_rotate_center = self._quad_center()
                        self._transform_rotate_start_angle = math.degrees(math.atan2(p.y() - self._transform_rotate_center.y(), p.x() - self._transform_rotate_center.x()))
                        self._transform_rotate_points = [QPointF(pt) for pt in self.transform_quad]
                        self._transform_rotate_start_value = float(getattr(self, "transform_rotate_angle", 0.0))
                        self.setCursor(Qt.OpenHandCursor)
                        return
                    if mode == "warp" and hit_type == "warp_point":
                        self.drag_mode = f"transform_warp_point:{int(hit_index)}"
                        self._transform_drag_index = int(hit_index)
                        self._transform_drag_points = [QPointF(pt) for pt in self.transform_quad]
                        self._transform_warp_start_grid = [QPointF(pt) for pt in self._warp_grid_points()]
                        return
                    if hit_type == "inside":
                        if mode == "warp" and not (event.modifiers() & Qt.ShiftModifier):
                            return
                        self.drag_mode = "transform_move"
                        self._transform_drag_points = [QPointF(pt) for pt in self.transform_quad]
                        self._transform_warp_start_grid = [QPointF(pt) for pt in self._warp_grid_points()] if mode == "warp" else None
                        return
                    if mode == "scale" and hit_type in ("corner", "edge"):
                        self.drag_mode = f"transform_scale:{hit_type}:{int(hit_index)}"
                        self._transform_drag_index = int(hit_index)
                        self._transform_drag_points = [QPointF(pt) for pt in self.transform_quad]
                        self._transform_scale_axis_lock = None
                        return
                    if mode == "skew" and hit_type == "edge":
                        self.drag_mode = f"transform_skew:{int(hit_index)}"
                        self._transform_drag_index = int(hit_index)
                        self._transform_drag_points = [QPointF(pt) for pt in self.transform_quad]
                        return
                    if mode == "perspective" and hit_type == "corner":
                        self.drag_mode = f"transform_corner:{int(hit_index)}"
                        self._transform_drag_index = int(hit_index)
                        self._transform_drag_points = [QPointF(pt) for pt in self.transform_quad]
                        return
                    if mode == "perspective" and hit_type == "edge":
                        self.drag_mode = f"transform_edge:{int(hit_index)}"
                        self._transform_drag_index = int(hit_index)
                        self._transform_drag_points = [QPointF(pt) for pt in self.transform_quad]
                        return
                    if hit_type == "rotate":
                        self.drag_mode = "transform_rotate"
                        self._transform_rotate_center = self._quad_center()
                        self._transform_rotate_start_angle = math.degrees(math.atan2(p.y() - self._transform_rotate_center.y(), p.x() - self._transform_rotate_center.x()))
                        self._transform_rotate_points = [QPointF(pt) for pt in self.transform_quad]
                        self.setCursor(Qt.OpenHandCursor)
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
                if sep_hit is not None or crop_hit or self.show_crop or erase_hit:
                    tr = getattr(self.parent(), "_tr", None)
                    _t = tr if callable(tr) else (lambda key, *args: key.format(*args) if args else key)
                    QMessageBox.information(
                        self,
                        _t("image_edit_notice_title"),
                        _t("image_edit_turn_off_rotation_first")
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
                hit_idx = self._crop_hit_index(p)
                if hit_idx is not None:
                    self.select_crop_index(hit_idx)
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
                self._store_active_crop()
                self.selected_crop_index = len(self.crop_rects)
                self.crop_rect = QRectF(p, p)
                self.crop_rects.append(QRectF(self.crop_rect))
                self.update()
                self.changed.emit()
                return
            if getattr(self, "show_selection", False) and event.modifiers() & Qt.AltModifier:
                hit_pt = self._selection_point_hit(p)
                if hit_pt >= 0:
                    self._ensure_selection_polygon_from_rect()
                    self.drag_mode = "selection_point_move"
                    self._selection_point_drag_index = int(hit_pt)
                    self.drag_start = p
                    self.update()
                    return
            if getattr(self, "show_selection", False) and getattr(self, "selection_draw_mode", "rect") == "polygon":
                if not self.selection_polygon:
                    self.selection_polygon = []
                self.selection_polygon.append(QPointF(p))
                if len(self.selection_polygon) >= 3:
                    self.selection_rect = self._selection_rect_from_points(self.selection_polygon)
                else:
                    self.selection_rect = None
                self.update()
                self.changed.emit()
                return
            if getattr(self, "show_selection", False) and getattr(self, "selection_draw_mode", "rect") == "freehand":
                self.drag_mode = "selection_freehand"
                self.drag_start = p
                self._freehand_points = [QPointF(p)]
                self.selection_polygon = None
                self.selection_rect = None
                self.update()
                return
            if getattr(self, "show_selection", False):
                edge = self._selection_edge_at(p)
                if self.selection_rect is not None and edge:
                    self.drag_mode = f"selection_resize:{edge}"
                    self.drag_start = p
                    self.rect_before = QRectF(self.selection_rect)
                    return
                if self.selection_rect is not None and self._point_in_selection(p):
                    self.drag_mode = "selection_move"
                    self.drag_start = p
                    self.rect_before = QRectF(self.selection_rect)
                    return
                self.drag_mode = "selection_new"
                self.drag_start = p
                self.selection_rect = None
                self.selection_polygon = None
                return
            if getattr(self, "show_selection", False) and self.selection_rect is not None:
                edge = self._selection_edge_at(p)
                if edge:
                    self.setCursor(
                        Qt.SizeHorCursor if edge in ("left", "right")
                        else Qt.SizeVerCursor if edge in ("top", "bottom")
                        else Qt.SizeFDiagCursor
                    )
                    return
                if self._point_in_selection(p):
                    self.setCursor(Qt.SizeAllCursor)
                    return
