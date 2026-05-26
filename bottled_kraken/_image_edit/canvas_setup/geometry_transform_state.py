"""Mixin-Methoden für die Bildbearbeitungs-Canvas."""
from ...shared import *
from ..common import ImageEditSeparator
from PySide6.QtGui import QPolygonF
from ..warp_mesh_utils import default_warp_grid, warp_map_rect_point

class ImageEditCanvasGeometryTransformStateMixin:
        def _transform_point_current(self, pt: QPointF) -> QPointF:
            """Transforms a selection point using the current free-transform state."""
            if not self.has_active_transform() or self.transform_src_rect is None or not self.transform_quad:
                return QPointF(pt)
            src = self.transform_src_rect
            mode = str(getattr(self, "transform_mode", "scale") or "scale")
            if mode == "warp":
                grid = self._warp_grid_tuples()
                x, y = warp_map_rect_point((src.left(), src.top(), src.right(), src.bottom()), grid, pt.x(), pt.y())
                return QPointF(x, y)

            # Projective mapping from source rectangle to current transform quad.
            # This matches the actual PIL perspective transformation much better
            # than the previous bilinear approximation.
            try:
                src_pts = [
                    (float(src.left()), float(src.top())),
                    (float(src.right()), float(src.top())),
                    (float(src.right()), float(src.bottom())),
                    (float(src.left()), float(src.bottom())),
                ]
                dst_pts = [(float(q.x()), float(q.y())) for q in self.transform_quad]
                matrix = []
                vector = []
                for (xs, ys), (xd, yd) in zip(src_pts, dst_pts):
                    matrix.append([xs, ys, 1.0, 0.0, 0.0, 0.0, -xd * xs, -xd * ys])
                    vector.append(xd)
                    matrix.append([0.0, 0.0, 0.0, xs, ys, 1.0, -yd * xs, -yd * ys])
                    vector.append(yd)
                a, b, c, d, e, f, g, h = np.linalg.solve(np.array(matrix, dtype=float), np.array(vector, dtype=float))
                denom = g * float(pt.x()) + h * float(pt.y()) + 1.0
                if abs(denom) < 1e-9:
                    return QPointF(pt)
                x = (a * float(pt.x()) + b * float(pt.y()) + c) / denom
                y = (d * float(pt.x()) + e * float(pt.y()) + f) / denom
                return QPointF(float(x), float(y))
            except Exception:
                u = (pt.x() - src.left()) / max(1.0, src.width())
                v = (pt.y() - src.top()) / max(1.0, src.height())
                q0, q1, q2, q3 = self.transform_quad
                x = (1-u)*(1-v)*q0.x() + u*(1-v)*q1.x() + u*v*q2.x() + (1-u)*v*q3.x()
                y = (1-u)*(1-v)*q0.y() + u*(1-v)*q1.y() + u*v*q2.y() + (1-u)*v*q3.y()
                return QPointF(x, y)

        def transformed_selection_polygon(self) -> Optional[List[QPointF]]:
            pts = [QPointF(p) for p in (self.transform_src_polygon or self.selection_polygon or [])]
            if len(pts) >= 2:
                return [self._transform_point_current(p) for p in pts]

            # Während einer aktiven freien Transformation darf NICHT die laufend
            # veränderte selection_rect als Quelle benutzt werden. Sonst wird der
            # Rahmen beim Zoomen/Skew/Perspektive erneut aus der schon transformierten
            # Bounding-Box berechnet und verschiebt/verzieht sich sichtbar.
            if self.has_active_transform() and self.transform_src_rect is not None:
                r = self.transform_src_rect
            else:
                r = self.selection_rect

            if r is not None:
                pts = [r.topLeft(), r.topRight(), r.bottomRight(), r.bottomLeft()]
                return [self._transform_point_current(p) for p in pts]
            return None

        def selection_exists(self) -> bool:
            return self.selection_rect is not None

        def has_active_transform(self) -> bool:
            return bool(self.free_transform_active and self.transform_quad and self.transform_src_rect)

        def _default_warp_grid_points(self) -> List[QPointF]:
            r = self.transform_src_rect or self.selection_rect
            if r is None:
                return []
            # UI-Warp nutzt ein 5x5-Mesh. Die 9 inneren Punkte liegen wirklich
            # innerhalb des Auswahlbereichs; der Rand bleibt dadurch unverändert,
            # solange nicht explizit Rand-/Eckpunkte gezogen werden.
            return [
                QPointF(r.left() + r.width() * (col / 4.0), r.top() + r.height() * (row / 4.0))
                for row in range(5) for col in range(5)
            ]

        def _warp_grid_points_from_quad(self, quad=None) -> List[QPointF]:
            q = [QPointF(p) for p in (quad or self.transform_quad or [])]
            if len(q) != 4:
                return self._default_warp_grid_points()
            q0, q1, q2, q3 = q
            def bilinear(u: float, v: float) -> QPointF:
                return QPointF(
                    (1-u)*(1-v)*q0.x() + u*(1-v)*q1.x() + u*v*q2.x() + (1-u)*v*q3.x(),
                    (1-u)*(1-v)*q0.y() + u*(1-v)*q1.y() + u*v*q2.y() + (1-u)*v*q3.y(),
                )
            return [bilinear(col / 4.0, row / 4.0) for row in range(5) for col in range(5)]

        def _warp_grid_points(self) -> List[QPointF]:
            pts = getattr(self, "transform_warp_grid", None)
            if pts and len(pts) in (9, 25):
                if len(pts) == 25:
                    return [QPointF(p) for p in pts]
                # Alte 3x3-Zwischenstände defensiv auf das neue 5x5-Mesh migrieren.
                q = [QPointF(pts[0]), QPointF(pts[2]), QPointF(pts[8]), QPointF(pts[6])]
                self.transform_warp_grid = self._warp_grid_points_from_quad(q)
                return [QPointF(p) for p in self.transform_warp_grid]
            pts = self._warp_grid_points_from_quad()
            self.transform_warp_grid = [QPointF(p) for p in pts]
            return pts

        def _warp_grid_tuples(self):
            return [(float(p.x()), float(p.y())) for p in self._warp_grid_points()]

        def _warp_free_drag_weights(self, p: QPointF) -> List[float]:
            """Weights for dragging any arbitrary point inside the warp area.

            No additional mesh points are inserted. The existing 3x3 control mesh is
            pulled with a compact radial falloff around the clicked image position.
            The strongest affected existing control point receives weight 1.0 so the
            drag feels direct even when the click is between the visible handles.
            """
            src = self.transform_src_rect or self.selection_rect
            if src is None or src.width() <= 1.0 or src.height() <= 1.0:
                return [0.0] * 25
            try:
                u = max(0.0, min(1.0, (float(p.x()) - float(src.left())) / max(1.0, float(src.width()))))
                v = max(0.0, min(1.0, (float(p.y()) - float(src.top())) / max(1.0, float(src.height()))))
                # Grid-Koordinaten passend zur 5x5-Anordnung.
                anchors = [(col / 4.0, row / 4.0) for row in range(5) for col in range(5)]
                radius = 0.72
                weights = []
                for au, av in anchors:
                    dist = math.hypot((u - au), (v - av))
                    # glatter, kompakter Falloff; außerhalb des Radius bleibt ein Punkt stabil
                    weight = max(0.0, 1.0 - dist / radius) ** 2
                    weights.append(weight)
                max_w = max(weights) if weights else 0.0
                if max_w > 1e-9:
                    weights = [float(w) / max_w for w in weights]
                return [max(0.0, min(1.0, float(w))) for w in weights]
            except Exception:
                return [0.0] * 25

        def _move_warp_grid_by(self, dx: float, dy: float):
            pts = self._warp_grid_points()
            self.transform_warp_grid = [QPointF(p.x() + dx, p.y() + dy) for p in pts]

        def start_free_transform(self) -> bool:
            if self.selection_rect is None:
                return False
            self._selection_before_transform = QRectF(self.selection_rect)
            self._selection_polygon_before_transform = [QPointF(p) for p in (self.selection_polygon or [])] if self.selection_polygon else None
            self.transform_src_rect = QRectF(self.selection_rect)
            self.transform_src_polygon = [QPointF(p) for p in (self.selection_polygon or [])] if self.selection_polygon else None
            self.transform_quad = self._quad_points_for_rect(self.selection_rect)
            self.transform_rotate_angle = 0.0
            self.transform_warp_x = 0.0
            self.transform_warp_y = 0.0
            self.transform_warp_grid = None
            self.free_transform_active = True
            self.show_selection = True
            self.transform_mode = self.transform_mode or "scale"
            self.update()
            self.changed.emit()
            return True

        def cancel_free_transform(self):
            self.free_transform_active = False
            self.transform_src_rect = None
            self.transform_src_polygon = None
            self.transform_quad = None
            self.transform_source_order = [0, 1, 2, 3]
            self.transform_rotate_angle = 0.0
            self.transform_warp_x = 0.0
            self.transform_warp_y = 0.0
            self.transform_warp_grid = None
            self.update()
            self.changed.emit()

        def _ensure_transform_inside(self):
            if self.view_image is None or not self.transform_quad:
                return
            w, h = self.view_image.size
            clamped = []
            for pt in self.transform_quad:
                clamped.append(QPointF(max(0.0, min(float(w), pt.x())), max(0.0, min(float(h), pt.y()))))
            self.transform_quad = clamped
            grid = getattr(self, "transform_warp_grid", None)
            if grid and len(grid) in (9, 25):
                self.transform_warp_grid = [QPointF(max(0.0, min(float(w), p.x())), max(0.0, min(float(h), p.y()))) for p in grid]
            if self.transform_src_rect is not None:
                self.transform_src_rect = self._clamp_rect(self.transform_src_rect)

        def _transform_corner_anchor_index(self, idx: int) -> int:
            return {0: 2, 1: 3, 2: 0, 3: 1}.get(int(idx), 2)

        def _transform_horizontal_partner_index(self, idx: int) -> int:
            return {0: 1, 1: 0, 2: 3, 3: 2}.get(int(idx), 0)

        def _rect_from_anchor_and_point(self, anchor: QPointF, point: QPointF) -> QRectF:
            left = min(anchor.x(), point.x())
            right = max(anchor.x(), point.x())
            top = min(anchor.y(), point.y())
            bottom = max(anchor.y(), point.y())
            return QRectF(left, top, max(5.0, right - left), max(5.0, bottom - top))

        def _uniform_scale_rect(self, base_rect: QRectF, idx: int, point: QPointF) -> QRectF:
            ratio = max(1e-6, float(base_rect.width()) / max(1e-6, float(base_rect.height())))
            if idx in (0, 1, 2, 3):
                anchor = self._quad_points_for_rect(base_rect)[self._transform_corner_anchor_index(idx)]
                dx = point.x() - anchor.x()
                dy = point.y() - anchor.y()
                sx = -1.0 if idx in (0, 3) else 1.0
                sy = -1.0 if idx in (0, 1) else 1.0
                w0 = max(5.0, abs(dx))
                h0 = max(5.0, abs(dy))
                if (w0 / ratio) >= h0:
                    width = w0
                    height = max(5.0, width / ratio)
                else:
                    height = h0
                    width = max(5.0, height * ratio)
                new_point = QPointF(anchor.x() + sx * width, anchor.y() + sy * height)
                return self._rect_from_anchor_and_point(anchor, new_point)
            return QRectF(base_rect)

        def _axis_locked_scale_rect(self, base_rect: QRectF, idx: int, point: QPointF) -> QRectF:
            axis = getattr(self, '_transform_scale_axis_lock', None)
            if axis is None:
                dx = point.x() - self.drag_start.x()
                dy = point.y() - self.drag_start.y()
                if abs(dx) >= 2.0 or abs(dy) >= 2.0:
                    axis = 'x' if abs(dx) >= abs(dy) else 'y'
                    self._transform_scale_axis_lock = axis
            if axis is None:
                axis = 'x'
            r = QRectF(base_rect)
            if idx in (0, 1, 2, 3):
                anchor = self._quad_points_for_rect(base_rect)[self._transform_corner_anchor_index(idx)]
                new_point = QPointF(point)
                if axis == 'x':
                    new_point.setY(self._transform_drag_points[idx].y())
                else:
                    new_point.setX(self._transform_drag_points[idx].x())
                return self._rect_from_anchor_and_point(anchor, new_point)
            if idx == 0:  # top edge
                if axis == 'y':
                    r.setTop(min(point.y(), r.bottom() - 5))
            elif idx == 1:  # right edge
                if axis == 'x':
                    r.setRight(max(point.x(), r.left() + 5))
            elif idx == 2:  # bottom edge
                if axis == 'y':
                    r.setBottom(max(point.y(), r.top() + 5))
            elif idx == 3:  # left edge
                if axis == 'x':
                    r.setLeft(min(point.x(), r.right() - 5))
            return r

        def get_transform_state_norm(self) -> Optional[dict]:
            if not self.has_active_transform() or self.view_image is None:
                return None
            vw, vh = self.view_image.size
            src = self.transform_src_rect
            return {
                "enabled": True,
                "mode": str(self.transform_mode or "scale"),
                "src_norm": (
                    src.left() / max(1.0, float(vw)),
                    src.top() / max(1.0, float(vh)),
                    src.right() / max(1.0, float(vw)),
                    src.bottom() / max(1.0, float(vh)),
                ),
                "dest_norm": [
                    (pt.x() / max(1.0, float(vw)), pt.y() / max(1.0, float(vh)))
                    for pt in self.transform_quad
                ],
                "source_order": list(self.transform_source_order or [0, 1, 2, 3]),
                "rotate_angle": float(getattr(self, "transform_rotate_angle", 0.0)),
                "warp_x": float(getattr(self, "transform_warp_x", 0.0)),
                "warp_y": float(getattr(self, "transform_warp_y", 0.0)),
                "warp_grid_norm": [
                    (p.x() / max(1.0, float(vw)), p.y() / max(1.0, float(vh)))
                    for p in self._warp_grid_points()
                ] if str(getattr(self, "transform_mode", "")) == "warp" else [],
                "src_polygon_norm": [
                    (p.x() / max(1.0, float(vw)), p.y() / max(1.0, float(vh)))
                    for p in (getattr(self, "transform_src_polygon", None) or getattr(self, "selection_polygon", None) or [])
                ],
            }

        def restore_transform_state_norm(self, state: Optional[dict]):
            if not state or self.view_image is None:
                if state is None:
                    self.cancel_free_transform()
                return
            try:
                vw, vh = self.view_image.size
                x1n, y1n, x2n, y2n = state.get("src_norm") or (0.1, 0.1, 0.9, 0.9)
                self.transform_src_rect = QRectF(
                    float(x1n) * vw,
                    float(y1n) * vh,
                    max(5.0, (float(x2n) - float(x1n)) * vw),
                    max(5.0, (float(y2n) - float(y1n)) * vh),
                )
                self.selection_rect = QRectF(self.transform_src_rect)
                src_poly_norm = state.get("src_polygon_norm") or []
                if len(src_poly_norm) >= 3:
                    self.transform_src_polygon = [QPointF(float(x) * vw, float(y) * vh) for x, y in src_poly_norm]
                    self.selection_polygon = [QPointF(p) for p in self.transform_src_polygon]
                else:
                    self.transform_src_polygon = None
                    self.selection_polygon = None
                self.show_selection = True
                dest_norm = state.get("dest_norm") or []
                if len(dest_norm) == 4:
                    self.transform_quad = [QPointF(float(x) * vw, float(y) * vh) for x, y in dest_norm]
                else:
                    self.transform_quad = self._quad_points_for_rect(self.transform_src_rect)
                self.transform_mode = str(state.get("mode") or "scale")
                self.transform_source_order = [int(v) for v in (state.get("source_order") or [0, 1, 2, 3])][:4]
                if len(self.transform_source_order) != 4:
                    self.transform_source_order = [0, 1, 2, 3]
                self.transform_rotate_angle = float(state.get("rotate_angle", 0.0) or 0.0)
                self.transform_warp_x = float(state.get("warp_x", 0.0) or 0.0)
                self.transform_warp_y = float(state.get("warp_y", 0.0) or 0.0)
                wg = state.get("warp_grid_norm") or []
                self.transform_warp_grid = [QPointF(float(x) * vw, float(y) * vh) for x, y in wg] if len(wg) in (9, 25) else None
                if self.transform_warp_grid is not None and len(self.transform_warp_grid) == 9:
                    self.transform_warp_grid = self._warp_grid_points()
                self.free_transform_active = bool(state.get("enabled", True))
                self._ensure_transform_inside()
                self.update()
            except Exception:
                self.cancel_free_transform()
