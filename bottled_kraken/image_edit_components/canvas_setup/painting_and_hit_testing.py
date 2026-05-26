"""Mixin-Methoden für die Bildbearbeitungs-Canvas."""
from ...shared import *
from ..common import ImageEditSeparator
from PySide6.QtGui import QPolygonF
from ..warp_mesh_utils import warp_map_uv
class ImageEditCanvasPaintingAndHitTestingMixin:
        def paintEvent(self, event):
            painter = QPainter(self)
            painter.fillRect(self.rect(), QColor("#e9e9e9"))
            if self.view_pixmap is None:
                painter.setPen(QColor("#888"))
                tr = getattr(self.parent(), "_tr", None)
                painter.drawText(self.rect(), Qt.AlignCenter, tr("image_edit_no_image_loaded") if callable(tr) else "No image loaded")
                return
            self._update_image_offset()
            draw_x = self._img_offset_x
            draw_y = self._img_offset_y
            w = self.view_pixmap.width()
            h = self.view_pixmap.height()
            angle = self.preview_rotation_angle if self.is_preview_rotating else 0.0
            transform_overlay = self._build_transform_overlay() if self.has_active_transform() else None
            if abs(angle) > 0.01:
                painter.save()
                painter.translate(draw_x + w / 2.0, draw_y + h / 2.0)
                painter.rotate(angle)
                painter.translate(-w / 2.0, -h / 2.0)
                painter.drawPixmap(0, 0, self.view_pixmap)
                painter.restore()
            else:
                painter.drawPixmap(int(draw_x), int(draw_y), self.view_pixmap)
            if transform_overlay is not None and abs(angle) <= 0.01:
                clear_pixmap, clear_x, clear_y, overlay_pixmap, overlay_x, overlay_y = transform_overlay
                if clear_pixmap is not None:
                    painter.drawPixmap(int(draw_x + clear_x), int(draw_y + clear_y), clear_pixmap)
                painter.drawPixmap(int(draw_x + overlay_x), int(draw_y + overlay_y), overlay_pixmap)
            painter.save()
            painter.translate(draw_x, draw_y)
            if self.show_grid:
                self._paint_grid(painter)
            if getattr(self, "show_erase", False) and getattr(self, "erase_rect", None) is not None:
                self._paint_erase(painter)
            if self.show_crop and self.crop_rect is not None:
                self._paint_crop(painter)
            if self.show_selection and (self.selection_rect is not None or getattr(self, "selection_polygon", None)) and not self.has_active_transform():
                self._paint_selection(painter)
            if self.has_active_transform():
                self._paint_free_transform(painter)
            if self.show_separator and self.separator is not None:
                self._paint_separator(painter)
            painter.restore()
        def _paint_crop(self, painter: QPainter):
            rects = list(getattr(self, "crop_rects", []) or [])
            if not rects:
                return
            handle_size = 10
            for idx, rect in enumerate(rects):
                active = idx == getattr(self, "selected_crop_index", -1)
                painter.setPen(QPen(QColor("#ff4d4d") if active else QColor("#b84a4a"), 2, Qt.SolidLine if active else Qt.DashLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(rect)
                if not active:
                    continue
                painter.setPen(QPen(QColor("black"), 1))
                corners = [rect.topLeft(), rect.topRight(), rect.bottomRight(), rect.bottomLeft()]
                mids = [QPointF(rect.center().x(), rect.top()), QPointF(rect.right(), rect.center().y()), QPointF(rect.center().x(), rect.bottom()), QPointF(rect.left(), rect.center().y())]
                painter.setBrush(QColor("#ff4d4d"))
                for p in corners:
                    painter.drawRect(QRectF(p.x() - handle_size / 2, p.y() - handle_size / 2, handle_size, handle_size))
                painter.setBrush(QColor("#ffb347"))
                for p in mids:
                    painter.drawRect(QRectF(p.x() - handle_size / 2, p.y() - handle_size / 2, handle_size, handle_size))
        def _paint_selection(self, painter: QPainter):
            rect = self.selection_rect
            pts = list(self.selection_polygon or [])
            if rect is None and not pts:
                return
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setPen(QPen(QColor("#5aa3ff"), 2, Qt.DashLine))
            painter.setBrush(QColor(90, 163, 255, 28))
            if len(pts) >= 3:
                poly = QPolygonF(pts)
                painter.drawPolygon(poly)
            elif len(pts) >= 2:
                painter.drawPolyline(QPolygonF(pts))
            elif rect is not None:
                painter.drawRect(rect)
            handle_size = 10
            painter.setPen(QPen(QColor("#0b3a75"), 1))
            painter.setBrush(QColor("#ffffff"))
            if pts:
                show_pts = str(getattr(self, "selection_draw_mode", "rect")) != "freehand"
                if show_pts:
                    for pt in pts:
                        painter.drawEllipse(QRectF(pt.x() - handle_size / 2, pt.y() - handle_size / 2, handle_size, handle_size))
            elif rect is not None:
                corners = [rect.topLeft(), rect.topRight(), rect.bottomRight(), rect.bottomLeft()]
                mids = [
                    QPointF(rect.center().x(), rect.top()),
                    QPointF(rect.right(), rect.center().y()),
                    QPointF(rect.center().x(), rect.bottom()),
                    QPointF(rect.left(), rect.center().y()),
                ]
                for pt in corners + mids:
                    painter.drawRect(QRectF(pt.x() - handle_size / 2, pt.y() - handle_size / 2, handle_size, handle_size))
        def _paint_warp_mesh(self, painter: QPainter) -> bool:
            if str(getattr(self, "transform_mode", "")) != "warp":
                return False
            grid = self._warp_grid_points() if hasattr(self, "_warp_grid_points") else []
            if len(grid) not in (9, 25):
                return False
            tuples = [(p.x(), p.y()) for p in grid]
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing, True)
            if len(grid) == 25:
                mesh_outline = [grid[i] for i in (0, 4, 24, 20)]
                mesh_lines = (0.0, 0.25, 0.5, 0.75, 1.0)
                inner_handle_indices = (6, 7, 8, 11, 12, 13, 16, 17, 18)
                border_handle_indices = (0, 2, 4, 10, 14, 20, 22, 24)
            else:
                mesh_outline = [grid[i] for i in (0, 2, 8, 6)]
                mesh_lines = (0.0, 0.5, 1.0)
                inner_handle_indices = (4,)
                border_handle_indices = (0, 1, 2, 3, 5, 6, 7, 8)
            transformed_pts = self.transformed_selection_polygon() if hasattr(self, "transformed_selection_polygon") else None
            visible_outline = [QPointF(p) for p in (transformed_pts or [])] if transformed_pts and len(transformed_pts) >= 3 else [QPointF(p) for p in mesh_outline]
            # Sichtbare Auswahlform beibehalten: Kreis/Freihand/Polygon soll auch im
            # Warp-Modus als eigentliche Auswahlform erkennbar bleiben und nicht auf
            # einen bloßen Rechteckrahmen reduziert werden.
            painter.setBrush(QColor(90, 163, 255, 24))
            painter.setPen(QPen(QColor("#5aa3ff"), 2, Qt.SolidLine))
            painter.drawPolygon(QPolygonF(visible_outline))
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(30, 70, 120, 150), 1.2, Qt.SolidLine))
            for u in mesh_lines:
                painter.drawPolyline(QPolygonF([QPointF(*warp_map_uv(tuples, u, k / 32.0)) for k in range(33)]))
            for v in mesh_lines:
                painter.drawPolyline(QPolygonF([QPointF(*warp_map_uv(tuples, k / 32.0, v)) for k in range(33)]))
            # Randgriffe bleiben separat weiß. Die 9 inneren Kontrollpunkte sind blau
            # und verformen nur das Innere, solange keine Randgriffe bewegt werden.
            painter.setPen(QPen(QColor("#0b3a75"), 1))
            for i in border_handle_indices:
                pt = grid[i]
                painter.setBrush(QColor("#ffffff"))
                painter.drawEllipse(QRectF(pt.x() - 5, pt.y() - 5, 10, 10))
            for i in inner_handle_indices:
                pt = grid[i]
                painter.setBrush(QColor("#86d0ff"))
                painter.drawEllipse(QRectF(pt.x() - 5, pt.y() - 5, 10, 10))
            br = self._bounding_rect_from_points(visible_outline)
            tr = getattr(self.parent(), "_tr", None)
            mode_text = tr("image_edit_transform_mode_warp") if callable(tr) else "Warp"
            badge = br.adjusted(0, -28, 0, -8)
            painter.fillRect(QRectF(badge.left(), badge.top(), min(220.0, badge.width()), 18), QColor(25, 45, 85, 180))
            painter.setPen(QColor("white"))
            painter.drawText(QRectF(badge.left() + 6, badge.top(), min(214.0, badge.width() - 6), 18), Qt.AlignVCenter | Qt.AlignLeft, mode_text)
            painter.restore()
            return True
        def _paint_free_transform(self, painter: QPainter):
            if not self.transform_quad or len(self.transform_quad) != 4:
                return
            if self._paint_warp_mesh(painter):
                return
            transformed_pts = self.transformed_selection_polygon() if hasattr(self, "transformed_selection_polygon") else None
            outline_pts = self._transform_visual_outline_points(transformed_pts)
            handle_quad = self._transform_visual_handle_quad(transformed_pts)
            if not outline_pts or len(outline_pts) < 3 or not handle_quad or len(handle_quad) != 4:
                return
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing, True)
            # Sichtbarer Transformationsbereich: bevorzugt die echte erzeugte Auswahlform.
            painter.setPen(QPen(QColor("#5aa3ff"), 2))
            painter.setBrush(QColor(90, 163, 255, 25))
            painter.drawPolygon(QPolygonF(outline_pts))
            # Die Griffe sitzen auf der sichtbaren Auswahlform. Bei gezielter/freier
            # Vierpunkt-Auswahl waren sie vorher noch auf der internen Bounding-Box;
            # dadurch lagen Eck- und Seitenpunkte neben dem tatsächlich transformierten
            # Ausschnitt. Für freie/elliptische Auswahlformen mit vielen Punkten bleibt
            # die interne Vierpunkt-Hülle als Steuergeometrie erhalten.
            painter.setPen(QPen(QColor("#0b3a75"), 1))
            painter.setBrush(QColor("#ffffff"))
            for idx, pt in enumerate(handle_quad):
                painter.drawRect(QRectF(pt.x() - 5, pt.y() - 5, 10, 10))
                painter.drawText(QRectF(pt.x() + 6, pt.y() - 10, 16, 16), Qt.AlignCenter, str(idx + 1))
            painter.setBrush(QColor("#86d0ff"))
            for mid in self._transform_edge_midpoints():
                painter.drawEllipse(mid, 5, 5)
            br = self._bounding_rect_from_points(handle_quad)
            # Für Kreis-/Polygon-/Freihand-Auswahlen soll keine zusätzliche
            # rechteckige Hilfshülle erscheinen. Die sichtbare Auswahlform selbst
            # ist bereits die relevante Orientierung.
            if not getattr(self, "transform_src_polygon", None):
                painter.setPen(QPen(QColor(90, 163, 255, 55), 1, Qt.DashLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(br.adjusted(-14, -14, 14, 14))
            tr = getattr(self.parent(), "_tr", None)
            mode_text = str(self.transform_mode or "scale").upper()
            if callable(tr):
                try:
                    mode_text = tr(f"image_edit_transform_mode_{self.transform_mode}")
                except Exception:
                    pass
            badge = br.adjusted(0, -28, 0, -8)
            painter.fillRect(QRectF(badge.left(), badge.top(), min(220.0, badge.width()), 18), QColor(25, 45, 85, 180))
            painter.setPen(QColor("white"))
            painter.drawText(QRectF(badge.left() + 6, badge.top(), min(214.0, badge.width() - 6), 18), Qt.AlignVCenter | Qt.AlignLeft, mode_text)
            painter.restore()
        def _paint_erase(self, painter: QPainter):
            rect = getattr(self, "erase_rect", None)
            if rect is None:
                return
            painter.setPen(QPen(QColor("#ff4d4d"), 2, Qt.DashLine))
            painter.setBrush(QColor(255, 90, 90, 70))
            shape = getattr(self, "erase_shape", "rect")
            if shape == "ellipse":
                painter.drawEllipse(rect)
            else:
                painter.drawRect(rect)
        def _paint_separator(self, painter: QPainter):
            if self.view_image is None or self.separator is None:
                return
            pts = self.separator.clipped_endpoints(*self.view_image.size)
            if pts is None:
                return
            x1, y1, x2, y2 = pts
            painter.setPen(QPen(QColor("#58d68d"), 3))
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
            painter.setPen(QPen(QColor("black"), 1))
            painter.setBrush(QColor("#ffc107"))
            for hx, hy in (self.separator.top_handle(*self.view_image.size), self.separator.bottom_handle(*self.view_image.size)):
                painter.drawEllipse(QPointF(hx, hy), self.separator.HANDLE_R, self.separator.HANDLE_R)
            rx, ry = self.separator.rotation_handle_pos()
            painter.setBrush(QColor("#ffffff"))
            painter.setPen(QPen(QColor("#555"), 1))
            painter.drawEllipse(QPointF(rx, ry), self.separator.ROT_R, self.separator.ROT_R)
            painter.setPen(QColor("#222"))
            painter.drawText(QRectF(rx - 12, ry - 12, 24, 24), Qt.AlignCenter, "↻")
        def _paint_grid(self, painter: QPainter):
            if self.view_image is None:
                return
            painter.save()
            pen = QPen(QColor(0, 0, 0, 90), 1)
            pen.setCosmetic(True)
            painter.setPen(pen)
            step = max(6, int(self.grid_spacing))
            w, h = self.view_image.size
            x = 0
            while x <= w:
                painter.drawLine(x, 0, x, h)
                x += step
            y = 0
            while y <= h:
                painter.drawLine(0, y, w, y)
                y += step
            painter.restore()
        def _point_in_crop(self, p: QPointF) -> bool:
            idx = self._crop_hit_index(p)
            if idx is None:
                return False
            rect = self.crop_rect if idx == getattr(self, "selected_crop_index", -1) and self.crop_rect is not None else self.crop_rects[idx]
            return rect is not None and rect.contains(p)
        def _crop_edge_at(self, p: QPointF):
            if self.crop_rect is None:
                return None
            return self._rect_edge_at(self.crop_rect, p)
        def _point_in_selection(self, p: QPointF) -> bool:
            if self.selection_polygon and len(self.selection_polygon) >= 3:
                return QPolygonF(self.selection_polygon).containsPoint(p, Qt.OddEvenFill)
            return self.selection_rect is not None and self.selection_rect.contains(p)
        def _selection_edge_at(self, p: QPointF):
            if self.selection_rect is None:
                return None
            return self._rect_edge_at(self.selection_rect, p) if hasattr(self, "_rect_edge_at") else self._rect_edge_at_local(self.selection_rect, p)
        def _rect_edge_at_local(self, rect: Optional[QRectF], p: QPointF) -> Optional[str]:
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
        def _separator_hit(self, p: QPointF):
            if self.separator is None or self.view_image is None:
                return None
            w, h = self.view_image.size
            rx, ry = self.separator.rotation_handle_pos()
            if (p.x() - rx) ** 2 + (p.y() - ry) ** 2 <= (self.separator.ROT_R + 5) ** 2:
                return "rotate"
            tx, ty = self.separator.top_handle(w, h)
            bx, by = self.separator.bottom_handle(w, h)
            if (p.x() - tx) ** 2 + (p.y() - ty) ** 2 <= (self.separator.HANDLE_R + 4) ** 2:
                return "top"
            if (p.x() - bx) ** 2 + (p.y() - by) ** 2 <= (self.separator.HANDLE_R + 4) ** 2:
                return "bottom"
            if self.separator.distance_to_line(p.x(), p.y(), w, h) < 8:
                return "line"
            return None
        def _quad_points_for_rect(self, rect: QRectF) -> List[QPointF]:
            return [QPointF(rect.left(), rect.top()), QPointF(rect.right(), rect.top()), QPointF(rect.right(), rect.bottom()), QPointF(rect.left(), rect.bottom())]
        def _bounding_rect_from_points(self, points: List[QPointF]) -> QRectF:
            xs = [p.x() for p in points]
            ys = [p.y() for p in points]
            return QRectF(min(xs), min(ys), max(5.0, max(xs) - min(xs)), max(5.0, max(ys) - min(ys)))
        def _transform_visual_outline_points(self, transformed_pts=None) -> List[QPointF]:
            """Visible outline of the active free-transform selection.
            The internal transform_quad is the rectangle/quadrilateral used for the
            image mapping. If the user transformed a targeted four-point selection,
            the actually visible selected area can differ from that internal helper
            quad. Painting and hit-testing must follow the visible area so the corner
            and edge handles stay attached to the transformed selection.
            """
            pts = transformed_pts
            if pts is None and hasattr(self, "transformed_selection_polygon"):
                try:
                    pts = self.transformed_selection_polygon()
                except Exception:
                    pts = None
            if pts and len(pts) >= 3:
                return [QPointF(p) for p in pts]
            return [QPointF(p) for p in (self.transform_quad or [])]
        def _outline_handle_quad_from_points(self, pts: List[QPointF]) -> List[QPointF]:
            """Approximate four transform handle positions on the visible outline.
            For ellipse/freehand/polygon selections we still keep the internal
            transform_quad as the mathematical transform basis, but visually the
            handles should sit on the actual selected outline instead of on a plain
            rectangular helper frame.
            """
            if not pts or len(pts) < 3:
                return [QPointF(p) for p in (self.transform_quad or [])]
            base_quad = [QPointF(p) for p in (self.transform_quad or [])]
            if len(base_quad) != 4:
                return [QPointF(p) for p in pts[:4]] if len(pts) >= 4 else [QPointF(p) for p in pts]
            available = [QPointF(p) for p in pts]
            chosen = []
            for target in base_quad:
                if not available:
                    chosen.append(QPointF(target))
                    continue
                best_idx = min(
                    range(len(available)),
                    key=lambda i: math.hypot(float(available[i].x()) - float(target.x()), float(available[i].y()) - float(target.y()))
                )
                chosen.append(QPointF(available.pop(best_idx)))
            return chosen
        def _transform_visual_handle_quad(self, transformed_pts=None) -> List[QPointF]:
            """Four points used for transform handles.
            If the current selection has its own visible polygon/ellipse/freehand
            outline, the transform handles should follow that outline instead of a
            generic rectangular frame. Only plain rectangular selections fall back to
            the internal transform_quad directly.
            """
            pts = transformed_pts
            if pts is None and hasattr(self, "transformed_selection_polygon"):
                try:
                    pts = self.transformed_selection_polygon()
                except Exception:
                    pts = None
            if pts and len(pts) == 4:
                return [QPointF(p) for p in pts]
            if pts and len(pts) >= 3 and getattr(self, "transform_src_polygon", None):
                return self._outline_handle_quad_from_points(pts)
            return [QPointF(p) for p in (self.transform_quad or [])]
        def _edge_midpoints_for_quad(self, pts: List[QPointF]) -> List[QPointF]:
            if not pts or len(pts) != 4:
                return []
            mids = []
            for i in range(4):
                a = pts[i]
                b = pts[(i + 1) % 4]
                mids.append(QPointF((a.x() + b.x()) / 2.0, (a.y() + b.y()) / 2.0))
            return mids
        def _transform_edge_midpoints(self) -> List[QPointF]:
            return self._edge_midpoints_for_quad(self._transform_visual_handle_quad())
        def _quad_center(self) -> QPointF:
            if not self.transform_quad:
                return QPointF()
            xs = [p.x() for p in self.transform_quad]
            ys = [p.y() for p in self.transform_quad]
            return QPointF(sum(xs) / len(xs), sum(ys) / len(ys))
        def _point_in_quad(self, p: QPointF) -> bool:
            pts = self._transform_visual_handle_quad()
            if not pts or len(pts) != 4:
                return False
            return QPolygonF(pts).containsPoint(p, Qt.OddEvenFill)
        def _distance_to_segment(self, p: QPointF, a: QPointF, b: QPointF) -> float:
            ax, ay, bx, by = a.x(), a.y(), b.x(), b.y()
            px, py = p.x(), p.y()
            vx = bx - ax
            vy = by - ay
            if abs(vx) < 1e-9 and abs(vy) < 1e-9:
                return math.hypot(px - ax, py - ay)
            t = ((px - ax) * vx + (py - ay) * vy) / max(1e-9, (vx * vx + vy * vy))
            t = max(0.0, min(1.0, t))
            cx = ax + vx * t
            cy = ay + vy * t
            return math.hypot(px - cx, py - cy)
        def _point_in_quad_or_on_border(self, p: QPointF, pts: List[QPointF], border_tol: float = 8.0) -> bool:
            if not pts or len(pts) != 4:
                return False
            poly = QPolygonF(pts)
            if poly.containsPoint(p, Qt.OddEvenFill):
                return True
            for i in range(4):
                if self._distance_to_segment(p, pts[i], pts[(i + 1) % 4]) <= float(border_tol):
                    return True
            return False
        def _transform_hit(self, p: QPointF):
            if not self.has_active_transform():
                return None
            mode = str(getattr(self, "transform_mode", "") or "")
            if mode == "warp":
                grid = self._warp_grid_points() if hasattr(self, "_warp_grid_points") else []
                # Im Warp-Modus sind die sichtbaren Randgriffe und die 9 inneren
                # Kontrollpunkte gezielt greifbar. Ein Klick in die Fläche verschiebt
                # den Rand nicht versehentlich.
                if len(grid) == 25:
                    hit_indices = (6, 7, 8, 11, 12, 13, 16, 17, 18, 0, 2, 4, 10, 14, 20, 22, 24)
                    outline = [grid[i] for i in (0, 4, 24, 20)]
                else:
                    hit_indices = tuple(range(len(grid)))
                    outline = [grid[i] for i in (0, 2, 8, 6)] if len(grid) == 9 else self._transform_visual_handle_quad()
                for idx in hit_indices:
                    if 0 <= idx < len(grid):
                        pt = grid[idx]
                        if math.hypot(p.x() - pt.x(), p.y() - pt.y()) <= 8.0:
                            return ("warp_point", idx)
                transformed_pts = self.transformed_selection_polygon() if hasattr(self, "transformed_selection_polygon") else None
                if transformed_pts and len(transformed_pts) >= 3 and getattr(self, "transform_src_polygon", None):
                    poly = QPolygonF(transformed_pts)
                    if poly.containsPoint(p, Qt.OddEvenFill):
                        return ("inside", None)
                    for i in range(len(transformed_pts)):
                        if self._distance_to_segment(p, transformed_pts[i], transformed_pts[(i + 1) % len(transformed_pts)]) <= 10.0:
                            return ("inside", None)
                    return None
                if outline and len(outline) == 4 and self._point_in_quad_or_on_border(p, outline, border_tol=10.0):
                    return ("inside", None)
                return None
            handle_quad = self._transform_visual_handle_quad()
            if not handle_quad or len(handle_quad) != 4:
                return None
            for idx, pt in enumerate(handle_quad):
                if math.hypot(p.x() - pt.x(), p.y() - pt.y()) <= 10.0:
                    return ("corner", idx)
            mids = self._edge_midpoints_for_quad(handle_quad)
            for idx, pt in enumerate(mids):
                if math.hypot(p.x() - pt.x(), p.y() - pt.y()) <= 9.0:
                    return ("edge", idx)
            br = self._bounding_rect_from_points(handle_quad)
            outer = br.adjusted(-16, -16, 16, 16)
            outline_pts = self._transform_visual_outline_points() if hasattr(self, "_transform_visual_outline_points") else None
            if outline_pts and len(outline_pts) >= 3 and getattr(self, "transform_src_polygon", None):
                in_shape = QPolygonF(outline_pts).containsPoint(p, Qt.OddEvenFill)
            else:
                in_shape = QPolygonF(handle_quad).containsPoint(p, Qt.OddEvenFill)
            if outer.contains(p) and not in_shape:
                for i in range(4):
                    if self._distance_to_segment(p, handle_quad[i], handle_quad[(i + 1) % 4]) <= 18.0:
                        return ("rotate", None)
            if in_shape:
                return ("inside", None)
            return None
