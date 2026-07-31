from bottled_kraken.common import (
    QPointF,
    QRectF,
    Qt,
    math,
)
from bottled_kraken._image_edit.common import ImageEditSeparator
class ImageEditCanvasMouseMoveMixin:
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
            if self.drag_mode == "selection_point_move":
                idx = int(getattr(self, "_selection_point_drag_index", -1))
                self._ensure_selection_polygon_from_rect()
                if self.selection_polygon and 0 <= idx < len(self.selection_polygon):
                    self.selection_polygon[idx] = QPointF(p)
                    self.selection_rect = self._selection_rect_from_points(self.selection_polygon)
                    self.update(); self.changed.emit(); return
            if self.drag_mode == "selection_freehand":
                pts = list(getattr(self, "_freehand_points", []) or [])
                if not pts or (abs(pts[-1].x() - p.x()) + abs(pts[-1].y() - p.y())) >= 10:
                    pts.append(QPointF(p))
                    self._freehand_points = pts
                preview_pts = self._simplify_selection_points(pts, 10.0)
                if len(preview_pts) >= 3:
                    self.selection_polygon = preview_pts[:]
                    self.selection_rect = self._selection_rect_from_points(preview_pts)
                self.update(); self.changed.emit(); return
            if self.drag_mode == "transform_move" and self._transform_drag_points:
                delta = p - self.drag_start
                self.transform_quad = [QPointF(pt.x() + delta.x(), pt.y() + delta.y()) for pt in self._transform_drag_points]
                if str(getattr(self, "transform_mode", "")) == "warp" and getattr(self, "_transform_warp_start_grid", None):
                    self.transform_warp_grid = [QPointF(pt.x() + delta.x(), pt.y() + delta.y()) for pt in self._transform_warp_start_grid]
                if self.transform_src_rect is not None:
                    self.selection_rect = self._bounding_rect_from_points(self.transform_quad)
                self._ensure_transform_inside()
                self.update(); self.changed.emit(); return
            if self.drag_mode == "transform_warp_free" and getattr(self, "_transform_warp_start_grid", None):
                start_grid = [QPointF(pt) for pt in self._transform_warp_start_grid]
                weights = list(getattr(self, "_transform_warp_free_weights", None) or [])
                if len(weights) != len(start_grid):
                    weights = self._warp_free_drag_weights(getattr(self, "_transform_warp_free_start", self.drag_start)) if hasattr(self, "_warp_free_drag_weights") else [0.0] * len(start_grid)
                delta = p - self.drag_start
                pts = []
                for pt, weight in zip(start_grid, weights):
                    w = max(0.0, min(1.0, float(weight)))
                    pts.append(QPointF(pt.x() + delta.x() * w, pt.y() + delta.y() * w))
                self.transform_warp_grid = pts
                q = [QPointF(pt) for pt in (self.transform_quad or [])]
                if len(q) == 4:
                    if len(pts) == 25:
                        q[0] = QPointF(pts[0])
                        q[1] = QPointF(pts[4])
                        q[2] = QPointF(pts[24])
                        q[3] = QPointF(pts[20])
                        self.transform_quad = q
                    elif len(pts) == 9:
                        q[0] = QPointF(pts[0])
                        q[1] = QPointF(pts[2])
                        q[2] = QPointF(pts[8])
                        q[3] = QPointF(pts[6])
                        self.transform_quad = q
                self._ensure_transform_inside()
                self.update(); self.changed.emit(); return
            if self.drag_mode and str(self.drag_mode).startswith("transform_warp_point:"):
                pts = [QPointF(pt) for pt in (getattr(self, "_transform_warp_start_grid", None) or self._warp_grid_points())]
                idx = int(str(self.drag_mode).split(":", 1)[1])
                if 0 <= idx < len(pts):
                    delta = p - self.drag_start
                    move_indices = [idx]
                    mods = event.modifiers()
                    if len(pts) == 25:
                        row = idx // 5
                        col = idx % 5
                        if 1 <= row <= 3 and 1 <= col <= 3:
                            if mods & Qt.AltModifier:
                                move_indices = [row * 5 + c for c in (1, 2, 3)]
                            elif mods & Qt.ShiftModifier:
                                move_indices = [r * 5 + col for r in (1, 2, 3)]
                    for mi in move_indices:
                        if 0 <= mi < len(pts):
                            base = (getattr(self, "_transform_warp_start_grid", None) or pts)[mi]
                            pts[mi] = QPointF(base.x() + delta.x(), base.y() + delta.y())
                    self.transform_warp_grid = pts
                    corner_map = {0: 0, 4: 1, 24: 2, 20: 3} if len(pts) == 25 else {0: 0, 2: 1, 8: 2, 6: 3}
                    if idx in corner_map:
                        q = [QPointF(pt) for pt in (self.transform_quad or [])]
                        if len(q) == 4:
                            q[corner_map[idx]] = QPointF(pts[idx])
                            self.transform_quad = q
                    self._ensure_transform_inside()
                self.update(); self.changed.emit(); return
            if self.drag_mode and str(self.drag_mode).startswith("transform_scale:") and self._transform_drag_points:
                parts = str(self.drag_mode).split(":")
                hit_type = parts[1]
                idx = int(parts[2])
                br = self._bounding_rect_from_points(self._transform_drag_points)
                r = QRectF(br)
                mods = event.modifiers()
                if mods & Qt.AltModifier:
                    r = self._axis_locked_scale_rect(br, idx, p)
                elif mods & Qt.ShiftModifier:
                    r = self._uniform_scale_rect(br, idx, p)
                else:
                    self._transform_scale_axis_lock = None
                    if hit_type == "corner":
                        if idx == 0:
                            r.setLeft(min(p.x(), r.right() - 5)); r.setTop(min(p.y(), r.bottom() - 5))
                        elif idx == 1:
                            r.setRight(max(p.x(), r.left() + 5)); r.setTop(min(p.y(), r.bottom() - 5))
                        elif idx == 2:
                            r.setRight(max(p.x(), r.left() + 5)); r.setBottom(max(p.y(), r.top() + 5))
                        elif idx == 3:
                            r.setLeft(min(p.x(), r.right() - 5)); r.setBottom(max(p.y(), r.top() + 5))
                    else:
                        if idx == 0:
                            r.setTop(min(p.y(), r.bottom() - 5))
                        elif idx == 1:
                            r.setRight(max(p.x(), r.left() + 5))
                        elif idx == 2:
                            r.setBottom(max(p.y(), r.top() + 5))
                        elif idx == 3:
                            r.setLeft(min(p.x(), r.right() - 5))
                r = self._clamp_rect(r)
                self.transform_quad = self._quad_points_for_rect(r)
                self.transform_src_rect = self.transform_src_rect or QRectF(r)
                self.selection_rect = QRectF(r)
                self._ensure_transform_inside()
                self.update(); self.changed.emit(); return
            if self.drag_mode and str(self.drag_mode).startswith("transform_skew:") and self._transform_drag_points:
                idx = int(self.drag_mode.split(":", 1)[1])
                pts = [QPointF(pt) for pt in self._transform_drag_points]
                delta = p - self.drag_start
                a = idx
                b = (idx + 1) % 4
                if idx in (0, 2):
                    dx = delta.x()
                    pts[a] = QPointF(pts[a].x() + dx, pts[a].y())
                    pts[b] = QPointF(pts[b].x() + dx, pts[b].y())
                    if event.modifiers() & Qt.ShiftModifier:
                        oa = (idx + 2) % 4
                        ob = (idx + 3) % 4
                        pts[oa] = QPointF(pts[oa].x() - dx, pts[oa].y())
                        pts[ob] = QPointF(pts[ob].x() - dx, pts[ob].y())
                else:
                    dy = delta.y()
                    pts[a] = QPointF(pts[a].x(), pts[a].y() + dy)
                    pts[b] = QPointF(pts[b].x(), pts[b].y() + dy)
                    if event.modifiers() & Qt.ShiftModifier:
                        oa = (idx + 2) % 4
                        ob = (idx + 3) % 4
                        pts[oa] = QPointF(pts[oa].x(), pts[oa].y() - dy)
                        pts[ob] = QPointF(pts[ob].x(), pts[ob].y() - dy)
                self.transform_quad = pts
                self.selection_rect = self._bounding_rect_from_points(self.transform_quad)
                self._ensure_transform_inside()
                self.update(); self.changed.emit(); return
            if self.drag_mode and str(self.drag_mode).startswith("transform_corner:") and self._transform_drag_points:
                idx = int(self.drag_mode.split(":", 1)[1])
                pts = [QPointF(pt) for pt in self._transform_drag_points]
                delta = p - self.drag_start
                if event.modifiers() & Qt.AltModifier:
                    axis = getattr(self, "_transform_perspective_axis_lock", None)
                    if axis is None:
                        axis = "x" if abs(delta.x()) >= abs(delta.y()) else "y"
                        self._transform_perspective_axis_lock = axis
                    if axis == "x":
                        pts[idx] = QPointF(self._transform_drag_points[idx].x() + delta.x(), self._transform_drag_points[idx].y())
                        partner = self._transform_horizontal_partner_index(idx)
                        pts[partner] = QPointF(self._transform_drag_points[partner].x() - delta.x(), self._transform_drag_points[partner].y())
                    else:
                        pts[idx] = QPointF(self._transform_drag_points[idx].x(), self._transform_drag_points[idx].y() + delta.y())
                        partner = {0: 3, 1: 2, 2: 1, 3: 0}.get(idx, self._transform_horizontal_partner_index(idx))
                        pts[partner] = QPointF(self._transform_drag_points[partner].x(), self._transform_drag_points[partner].y() - delta.y())
                else:
                    pts[idx] = QPointF(self._transform_drag_points[idx].x() + delta.x(), self._transform_drag_points[idx].y() + delta.y())
                    if event.modifiers() & Qt.ShiftModifier:
                        partner = self._transform_horizontal_partner_index(idx)
                        pts[partner] = QPointF(self._transform_drag_points[partner].x() - delta.x(), self._transform_drag_points[partner].y() - delta.y())
                self.transform_quad = pts
                self.selection_rect = self._bounding_rect_from_points(self.transform_quad)
                self._ensure_transform_inside()
                self.update(); self.changed.emit(); return
            if self.drag_mode and str(self.drag_mode).startswith("transform_edge:") and self._transform_drag_points:
                idx = int(self.drag_mode.split(":", 1)[1])
                pts = [QPointF(pt) for pt in self._transform_drag_points]
                delta = p - self.drag_start
                a = idx
                b = (idx + 1) % 4
                pts[a] = QPointF(pts[a].x() + delta.x(), pts[a].y() + delta.y())
                pts[b] = QPointF(pts[b].x() + delta.x(), pts[b].y() + delta.y())
                self.transform_quad = pts
                self.selection_rect = self._bounding_rect_from_points(self.transform_quad)
                self._ensure_transform_inside()
                self.update(); self.changed.emit(); return
            if self.drag_mode == "transform_rotate":
                center = self._transform_rotate_center
                start = self._transform_rotate_start_angle
                curr = math.degrees(math.atan2(p.y() - center.y(), p.x() - center.x()))
                delta = curr - start
                if event.modifiers() & Qt.AltModifier:
                    delta = round(delta / 15.0) * 15.0
                elif event.modifiers() & Qt.ShiftModifier:
                    delta = round(delta / 10.0) * 10.0
                elif event.modifiers() & Qt.ControlModifier:
                    delta = round(delta / 5.0) * 5.0
                rad = math.radians(float(delta))
                cos_a = math.cos(rad)
                sin_a = math.sin(rad)
                base_pts = [QPointF(pt) for pt in (getattr(self, "_transform_rotate_points", None) or self.transform_quad or [])]
                if len(base_pts) == 4:
                    rotated = []
                    for pt in base_pts:
                        x = pt.x() - center.x()
                        y = pt.y() - center.y()
                        rotated.append(QPointF(center.x() + x * cos_a - y * sin_a, center.y() + x * sin_a + y * cos_a))
                    self.transform_quad = rotated
                    self.selection_rect = self._bounding_rect_from_points(self.transform_quad)
                    self._ensure_transform_inside()
                self.transform_rotate_angle = 0.0
                self.update(); self.changed.emit(); return
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
            if self.drag_mode == "selection_move" and self.selection_rect and self.rect_before:
                r = QRectF(self.rect_before)
                r.translate(p - self.drag_start)
                self.selection_rect = self._clamp_rect(r)
                if getattr(self, "selection_draw_mode", "rect") == "ellipse":
                    self.selection_polygon = self._ellipse_points_for_rect(self.selection_rect, 48)
                elif getattr(self, "selection_draw_mode", "rect") == "rect":
                    self.selection_polygon = None
                if self.has_active_transform():
                    # Bewegen darf eine laufende Verformung nicht plaetten:
                    # Quad und Warp-Gitter werden mitverschoben statt aus dem
                    # Rechteck neu aufgebaut (das warf Perspektive/Neigung weg).
                    delta = self.selection_rect.topLeft() - QRectF(self.rect_before).topLeft()
                    quad = getattr(self, "transform_quad", None)
                    if quad and len(quad) == 4:
                        self.transform_quad = [QPointF(pt.x() + delta.x(), pt.y() + delta.y()) for pt in quad]
                    else:
                        self.transform_quad = self._quad_points_for_rect(self.selection_rect)
                    grid = getattr(self, "transform_warp_grid", None)
                    if grid and len(grid) in (9, 25):
                        self.transform_warp_grid = [QPointF(pt.x() + delta.x(), pt.y() + delta.y()) for pt in grid]
                self.update(); self.changed.emit(); return
            if self.drag_mode and str(self.drag_mode).startswith("selection_resize:") and self.rect_before:
                edge = self.drag_mode.split(":", 1)[1]
                r = QRectF(self.rect_before)
                if "left" in edge: r.setLeft(min(p.x(), r.right() - 5))
                if "right" in edge: r.setRight(max(p.x(), r.left() + 5))
                if "top" in edge: r.setTop(min(p.y(), r.bottom() - 5))
                if "bottom" in edge: r.setBottom(max(p.y(), r.top() + 5))
                self.selection_rect = self._clamp_rect(r)
                if getattr(self, "selection_draw_mode", "rect") == "ellipse":
                    self.selection_polygon = self._ellipse_points_for_rect(self.selection_rect, 48)
                elif getattr(self, "selection_draw_mode", "rect") == "rect":
                    self.selection_polygon = None
                if self.has_active_transform():
                    self.transform_quad = self._quad_points_for_rect(self.selection_rect)
                self.update(); self.changed.emit(); return
            if self.drag_mode == "selection_new":
                dx = p.x() - self.drag_start.x()
                dy = p.y() - self.drag_start.y()
                if abs(dx) < 6 and abs(dy) < 6:
                    self.selection_rect = None
                    self.selection_polygon = None
                    self.update()
                    return
                if event.modifiers() & Qt.AltModifier:
                    side = max(abs(dx), abs(dy))
                    dx = side if dx >= 0 else -side
                    dy = side if dy >= 0 else -side
                x1 = min(self.drag_start.x(), self.drag_start.x() + dx)
                y1 = min(self.drag_start.y(), self.drag_start.y() + dy)
                x2 = max(self.drag_start.x(), self.drag_start.x() + dx)
                y2 = max(self.drag_start.y(), self.drag_start.y() + dy)
                self.selection_rect = self._clamp_rect(QRectF(x1, y1, x2 - x1, y2 - y1))
                if getattr(self, "selection_draw_mode", "rect") == "ellipse":
                    self.selection_polygon = self._ellipse_points_for_rect(self.selection_rect, 48)
                else:
                    self.selection_polygon = None
                self.update(); self.changed.emit(); return
            if self.drag_mode == "crop_move" and self.crop_rect and self.rect_before:
                r = QRectF(self.rect_before)
                r.translate(p - self.drag_start)
                self.crop_rect = self._clamp_rect(r)
                self._store_active_crop()
                self.update(); self.changed.emit(); return
            if self.drag_mode and str(self.drag_mode).startswith("crop_resize:") and self.rect_before:
                edge = self.drag_mode.split(":", 1)[1]
                r = QRectF(self.rect_before)
                if "left" in edge: r.setLeft(min(p.x(), r.right() - 5))
                if "right" in edge: r.setRight(max(p.x(), r.left() + 5))
                if "top" in edge: r.setTop(min(p.y(), r.bottom() - 5))
                if "bottom" in edge: r.setBottom(max(p.y(), r.top() + 5))
                self.crop_rect = self._clamp_rect(r)
                self._store_active_crop()
                self.update(); self.changed.emit(); return
            if self.drag_mode == "crop_new":
                x1 = min(self.drag_start.x(), p.x())
                y1 = min(self.drag_start.y(), p.y())
                x2 = max(self.drag_start.x(), p.x())
                y2 = max(self.drag_start.y(), p.y())
                self.crop_rect = self._clamp_rect(QRectF(x1, y1, x2 - x1, y2 - y1))
                self._store_active_crop()
                self.update(); self.changed.emit(); return
            self._update_cursor(p)
