"""Mixin-Methoden für die Bildbearbeitungs-Canvas."""
from ...shared import *
from ..common import ImageEditSeparator
from PySide6.QtGui import QPolygonF
from ..warp_mesh_utils import legacy_sine_warp_rgba, warp_rgba_by_grid

class ImageEditCanvasCoordinateProjectionMixin:
        def _project_to_border(self, x: float, y: float) -> Tuple[float, float]:
            if self.view_image is None:
                return x, y
            w, h = self.view_image.size
            candidates = [
                (0.0, max(0.0, min(float(h), y))),
                (float(w), max(0.0, min(float(h), y))),
                (max(0.0, min(float(w), x)), 0.0),
                (max(0.0, min(float(w), x)), float(h)),
            ]
            return min(candidates, key=lambda c: (x - c[0]) ** 2 + (y - c[1]) ** 2)

        def _mouse_angle_from_center(self, p: QPointF) -> float:
            if self.view_image is None:
                return 0.0
            w, h = self.view_image.size
            cx = w / 2.0
            cy = h / 2.0
            return math.degrees(math.atan2(p.y() - cy, p.x() - cx))

        def _pan_limits(self) -> Tuple[float, float]:
            if self.view_pixmap is None:
                return 0.0, 0.0
            max_x = max(0.0, (float(self.view_pixmap.width()) - float(self.width())) / 2.0)
            max_y = max(0.0, (float(self.view_pixmap.height()) - float(self.height())) / 2.0)
            return max_x, max_y

        def _clamp_pan(self):
            if self.view_pixmap is None or self.zoom <= 1.001:
                self._pan_x = 0.0
                self._pan_y = 0.0
                return

            view_w = float(self.view_pixmap.width())
            view_h = float(self.view_pixmap.height())
            widget_w = float(self.width())
            widget_h = float(self.height())

            if view_w <= widget_w:
                self._pan_x = 0.0
            else:
                self._pan_x = max(widget_w - view_w, min(0.0, float(self._pan_x)))

            if view_h <= widget_h:
                self._pan_y = 0.0
            else:
                self._pan_y = max(widget_h - view_h, min(0.0, float(self._pan_y)))

        def _can_pan_with_alt(self) -> bool:
            return self.view_pixmap is not None and self.zoom > 1.001

        def _update_image_offset(self):
            if self.view_pixmap is None:
                self._img_offset_x = 0.0
                self._img_offset_y = 0.0
                return
            self._clamp_pan()
            base_x = max(0.0, (self.width() - self.view_pixmap.width()) / 2.0)
            base_y = max(0.0, (self.height() - self.view_pixmap.height()) / 2.0)
            self._img_offset_x = base_x + self._pan_x
            self._img_offset_y = base_y + self._pan_y

        def _widget_to_image(self, p: QPointF) -> QPointF:
            return QPointF(p.x() - self._img_offset_x, p.y() - self._img_offset_y)

        def _image_to_widget(self, p: QPointF) -> QPointF:
            return QPointF(p.x() + self._img_offset_x, p.y() + self._img_offset_y)

        def _image_rect_in_widget(self) -> QRectF:
            if self.view_pixmap is None:
                return QRectF()
            return QRectF(
                self._img_offset_x,
                self._img_offset_y,
                float(self.view_pixmap.width()),
                float(self.view_pixmap.height())
            )

        def _warp_pil_image(self, crop: Image.Image, warp_x: float = 0.0, warp_y: float = 0.0) -> Image.Image:
            return legacy_sine_warp_rgba(crop, warp_x, warp_y)

        def _perspective_coefficients_for_preview(self, dst_points, src_points):
            matrix = []
            vector = []
            for (xd, yd), (xs, ys) in zip(dst_points, src_points):
                matrix.append([xd, yd, 1, 0, 0, 0, -xs * xd, -xs * yd])
                vector.append(xs)
                matrix.append([0, 0, 0, xd, yd, 1, -ys * xd, -ys * yd])
                vector.append(ys)
            try:
                coeffs = np.linalg.solve(np.array(matrix, dtype=float), np.array(vector, dtype=float))
                return tuple(float(v) for v in coeffs)
            except Exception:
                return None

        def _build_transformed_view_pixmap(self) -> Optional[QPixmap]:
            if not self.has_active_transform() or self.view_image is None or not self.transform_quad or self.transform_src_rect is None:
                return None
            try:
                img = self.view_image.convert("RGB").copy()
                mode = str(getattr(self, "transform_mode", "scale") or "scale")
                src_rect = self.transform_src_rect
                sx1 = int(round(max(0.0, min(float(img.size[0] - 1), src_rect.left()))))
                sy1 = int(round(max(0.0, min(float(img.size[1] - 1), src_rect.top()))))
                sx2 = int(round(max(float(sx1 + 2), min(float(img.size[0]), src_rect.right()))))
                sy2 = int(round(max(float(sy1 + 2), min(float(img.size[1]), src_rect.bottom()))))
                if sx2 - sx1 < 2 or sy2 - sy1 < 2:
                    return None

                if mode == "warp":
                    crop_rgba = img.crop((sx1, sy1, sx2, sy2)).convert("RGBA")
                    src_mask = self._selection_mask_for_rect(QRectF(sx1, sy1, sx2 - sx1, sy2 - sy1), (sx2 - sx1, sy2 - sy1))
                    crop_rgba.putalpha(src_mask)
                    warped = self._warp_pil_image(
                        crop_rgba,
                        getattr(self, "transform_warp_x", 0.0),
                        getattr(self, "transform_warp_y", 0.0),
                    ).convert("RGBA")
                    out = img.convert("RGBA").copy()
                    white = Image.new("RGBA", (sx2 - sx1, sy2 - sy1), (255, 255, 255, 255))
                    out.paste(white, (sx1, sy1), src_mask)
                    out.paste(warped, (sx1, sy1), warped.split()[-1])
                    return pil_to_qpixmap(out.convert("RGB"))

                src_corners = [(sx1, sy1), (sx2, sy1), (sx2, sy2), (sx1, sy2)]
                order = list(getattr(self, "transform_source_order", [0, 1, 2, 3]) or [0, 1, 2, 3])
                if len(order) != 4:
                    order = [0, 1, 2, 3]
                src_pts = [src_corners[int(idx) % 4] for idx in order]
                dst_pts = [(float(pt.x()), float(pt.y())) for pt in self.transform_quad]
                xs = [p[0] for p in dst_pts]
                ys = [p[1] for p in dst_pts]
                min_x = max(0, int(math.floor(min(xs))))
                min_y = max(0, int(math.floor(min(ys))))
                max_x = min(img.size[0], int(math.ceil(max(xs))))
                max_y = min(img.size[1], int(math.ceil(max(ys))))
                if max_x - min_x < 2 or max_y - min_y < 2:
                    return None
                dst_rel = [(x - min_x, y - min_y) for x, y in dst_pts]
                coeffs = self._perspective_coefficients_for_preview(dst_rel, src_pts)
                if coeffs is None:
                    return None
                transformed = img.transform(
                    (max_x - min_x, max_y - min_y),
                    Image.PERSPECTIVE,
                    coeffs,
                    resample=Image.BICUBIC,
                    fillcolor="white",
                )
                out = img.copy()
                ImageDraw.Draw(out).rectangle((sx1, sy1, sx2, sy2), fill="white")
                mask = Image.new("L", (max_x - min_x, max_y - min_y), 0)
                ImageDraw.Draw(mask).polygon(dst_rel, fill=255)
                out.paste(transformed, (min_x, min_y), mask)
                return pil_to_qpixmap(out)
            except Exception:
                return None

        def _transform_overlay_key(self):
            if not self.has_active_transform() or self.view_image is None:
                return None
            quad = tuple((round(pt.x(), 2), round(pt.y(), 2)) for pt in (self.transform_quad or []))
            src = self.transform_src_rect
            src_key = None
            if src is not None:
                src_key = (round(src.left(), 2), round(src.top(), 2), round(src.right(), 2), round(src.bottom(), 2))
            view_key = self.view_image.size if self.view_image is not None else None
            src_poly_key = tuple(
                (round(p.x(), 2), round(p.y(), 2))
                for p in (getattr(self, "transform_src_polygon", None) or getattr(self, "selection_polygon", None) or [])
            )
            return (
                view_key,
                str(getattr(self, "transform_mode", "scale") or "scale"),
                src_key,
                src_poly_key,
                quad,
                round(float(getattr(self, "transform_rotate_angle", 0.0) or 0.0), 2),
                round(float(getattr(self, "transform_warp_x", 0.0) or 0.0), 2),
                round(float(getattr(self, "transform_warp_y", 0.0) or 0.0), 2),
                tuple((round(p.x(), 2), round(p.y(), 2)) for p in (self._warp_grid_points() if str(getattr(self, "transform_mode", "")) == "warp" else [])),
                tuple(getattr(self, "transform_source_order", [0, 1, 2, 3]) or [0, 1, 2, 3]),
            )


        def _rotate_mode_base_patch(self, img, crop_rgba, src_mask, sx1, sy1, sx2, sy2):
            """Return (patch_rgba, x, y) for the current pre-rotate transform basis.

            Rotate mode must not discard the state produced by Scale/Skew/
            Perspective/Warp. Therefore the current quad/warp basis is rendered
            first and the rotation is applied to that rendered patch afterwards.
            """
            try:
                q = [QPointF(pt) for pt in (getattr(self, "transform_quad", None) or [])]
                crop_w = int(max(1, sx2 - sx1))
                crop_h = int(max(1, sy2 - sy1))
                identity = [QPointF(sx1, sy1), QPointF(sx2, sy1), QPointF(sx2, sy2), QPointF(sx1, sy2)]
                is_identity_quad = len(q) == 4 and all(
                    abs(q[i].x() - identity[i].x()) < 0.75 and abs(q[i].y() - identity[i].y()) < 0.75
                    for i in range(4)
                )
                warp_grid = getattr(self, "_rotate_base_warp_grid", None)
                if warp_grid:
                    warped, wx, wy = warp_rgba_by_grid(crop_rgba, (sx1, sy1, sx2, sy2), warp_grid, img.size)
                    return warped.convert("RGBA"), int(wx), int(wy)
                if not q or len(q) != 4 or is_identity_quad:
                    return crop_rgba.convert("RGBA"), int(sx1), int(sy1)

                src_corners = [(0, 0), (crop_w, 0), (crop_w, crop_h), (0, crop_h)]
                order = list(getattr(self, "_rotate_base_source_order", None) or getattr(self, "transform_source_order", [0, 1, 2, 3]) or [0, 1, 2, 3])
                if len(order) != 4:
                    order = [0, 1, 2, 3]
                src_pts = [src_corners[int(idx) % 4] for idx in order]
                dst_pts = [(float(pt.x()), float(pt.y())) for pt in q]
                xs = [p[0] for p in dst_pts]
                ys = [p[1] for p in dst_pts]
                min_x = max(0, int(math.floor(min(xs))))
                min_y = max(0, int(math.floor(min(ys))))
                max_x = min(img.size[0], int(math.ceil(max(xs))))
                max_y = min(img.size[1], int(math.ceil(max(ys))))
                if max_x - min_x < 2 or max_y - min_y < 2:
                    return crop_rgba.convert("RGBA"), int(sx1), int(sy1)
                dst_rel = [(x - min_x, y - min_y) for x, y in dst_pts]
                coeffs = self._perspective_coefficients_for_preview(dst_rel, src_pts)
                if coeffs is None:
                    return crop_rgba.convert("RGBA"), int(sx1), int(sy1)
                transformed = crop_rgba.transform(
                    (max_x - min_x, max_y - min_y),
                    Image.PERSPECTIVE,
                    coeffs,
                    resample=Image.BICUBIC,
                    fillcolor=(255, 255, 255, 0),
                ).convert("RGBA")
                return transformed, int(min_x), int(min_y)
            except Exception:
                return crop_rgba.convert("RGBA"), int(sx1), int(sy1)

        def _build_transform_overlay(self):
            """Erzeugt nur die transformierte Region als Overlay."""
            key = self._transform_overlay_key()
            if key is None:
                self._transform_overlay_cache_key = None
                self._transform_overlay_cache = None
                return None
            if getattr(self, "_transform_overlay_cache_key", None) == key:
                return getattr(self, "_transform_overlay_cache", None)

            if not self.has_active_transform() or self.view_image is None or not self.transform_quad or self.transform_src_rect is None:
                return None
            try:
                img = self.view_image.convert("RGB")
                mode = str(getattr(self, "transform_mode", "scale") or "scale")
                src_rect = self.transform_src_rect

                sx1 = int(round(max(0.0, min(float(img.size[0] - 1), src_rect.left()))))
                sy1 = int(round(max(0.0, min(float(img.size[1] - 1), src_rect.top()))))
                sx2 = int(round(max(float(sx1 + 2), min(float(img.size[0]), src_rect.right()))))
                sy2 = int(round(max(float(sy1 + 2), min(float(img.size[1]), src_rect.bottom()))))
                if sx2 - sx1 < 2 or sy2 - sy1 < 2:
                    return None

                crop_size = (sx2 - sx1, sy2 - sy1)
                src_rect_local = QRectF(sx1, sy1, crop_size[0], crop_size[1])
                src_mask = self._selection_mask_for_rect(src_rect_local, crop_size)

                clear_img = Image.new("RGBA", crop_size, (255, 255, 255, 0))
                white = Image.new("RGBA", crop_size, (255, 255, 255, 255))
                clear_img.paste(white, (0, 0), src_mask)
                clear_pixmap = pil_to_qpixmap(clear_img)

                if mode == "rotate":
                    crop = img.crop((sx1, sy1, sx2, sy2)).convert("RGBA")
                    crop.putalpha(src_mask)
                    base_patch, bx, by = self._rotate_mode_base_patch(img, crop, src_mask, sx1, sy1, sx2, sy2)
                    angle = float(getattr(self, "transform_rotate_angle", 0.0) or 0.0)
                    rotated = base_patch.rotate(
                        -angle,
                        expand=True,
                        resample=Image.BICUBIC,
                        fillcolor=(255, 255, 255, 0),
                    )
                    cx = bx + base_patch.size[0] / 2.0
                    cy = by + base_patch.size[1] / 2.0
                    px = int(round(cx - rotated.size[0] / 2.0))
                    py = int(round(cy - rotated.size[1] / 2.0))
                    result = (clear_pixmap, sx1, sy1, pil_to_qpixmap(rotated), px, py)
                    self._transform_overlay_cache_key = key
                    self._transform_overlay_cache = result
                    return result

                if mode == "warp":
                    crop_rgba = img.crop((sx1, sy1, sx2, sy2)).convert("RGBA")
                    crop_rgba.putalpha(src_mask)
                    warped, wx, wy = warp_rgba_by_grid(crop_rgba, (sx1, sy1, sx2, sy2), self._warp_grid_tuples(), img.size)
                    result = (clear_pixmap, sx1, sy1, pil_to_qpixmap(warped), wx, wy)
                    self._transform_overlay_cache_key = key
                    self._transform_overlay_cache = result
                    return result

                crop = img.crop((sx1, sy1, sx2, sy2)).convert("RGBA")
                crop.putalpha(src_mask)
                src_corners = [(0, 0), (sx2 - sx1, 0), (sx2 - sx1, sy2 - sy1), (0, sy2 - sy1)]
                order = list(getattr(self, "transform_source_order", [0, 1, 2, 3]) or [0, 1, 2, 3])
                if len(order) != 4:
                    order = [0, 1, 2, 3]
                src_pts = [src_corners[int(idx) % 4] for idx in order]

                dst_pts = [(float(pt.x()), float(pt.y())) for pt in self.transform_quad]
                xs = [p[0] for p in dst_pts]
                ys = [p[1] for p in dst_pts]
                min_x = max(0, int(math.floor(min(xs))))
                min_y = max(0, int(math.floor(min(ys))))
                max_x = min(img.size[0], int(math.ceil(max(xs))))
                max_y = min(img.size[1], int(math.ceil(max(ys))))
                if max_x - min_x < 2 or max_y - min_y < 2:
                    return None

                dst_rel = [(x - min_x, y - min_y) for x, y in dst_pts]
                coeffs = self._perspective_coefficients_for_preview(dst_rel, src_pts)
                if coeffs is None:
                    return None

                transformed = crop.transform(
                    (max_x - min_x, max_y - min_y),
                    Image.PERSPECTIVE,
                    coeffs,
                    resample=Image.BICUBIC,
                    fillcolor=(255, 255, 255, 0),
                ).convert("RGBA")

                result = (clear_pixmap, sx1, sy1, pil_to_qpixmap(transformed), min_x, min_y)
                self._transform_overlay_cache_key = key
                self._transform_overlay_cache = result
                return result
            except Exception:
                self._transform_overlay_cache_key = None
                self._transform_overlay_cache = None
                return None
