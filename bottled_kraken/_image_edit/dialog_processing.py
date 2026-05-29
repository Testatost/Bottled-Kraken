from bottled_kraken.common import Image, ImageDraw, QPointF, Tuple, clip_polygon_halfplane, math, np, polygon_area
from bottled_kraken._image_edit.common import ImageEditSeparator, ImageEditSettings, WhiteBorderDialog
from bottled_kraken._image_edit.canvas import ImageEditCanvas
from bottled_kraken._image_edit.warp_mesh_utils import legacy_sine_warp_rgba, scale_grid, warp_rgba_by_grid
class ImageEditDialogProcessingMixin:
    def _get_effective_crop_area(self, img: Image.Image) -> Tuple[int, int, int, int]:
        if self.chk_crop.isChecked():
            crop = self.canvas.get_crop_orig()
            if crop is not None:
                return crop
        return (0, 0, img.size[0], img.size[1])
    def _separator_lines_for_processing(self, img: Image.Image):
        if not self.chk_split.isChecked() or self.canvas.separator is None or self.canvas.view_image is None:
            return []
        vw, vh = self.canvas.view_image.size
        bw, bh = img.size
        sx = bw / max(1, vw)
        sy = bh / max(1, vh)
        pts = self.canvas.separator.clipped_endpoints(vw, vh)
        if pts is None:
            return []
        x1d, y1d, x2d, y2d = pts
        return [(x1d * sx, y1d * sy, x2d * sx, y2d * sy)]
    def _compute_segments_for_crop(self, crop_area, line_segments_orig):
        ox1, oy1, ox2, oy2 = crop_area
        rect_poly = [(ox1, oy1), (ox2, oy1), (ox2, oy2), (ox1, oy2)]
        if not line_segments_orig:
            return [rect_poly]
        entries = []
        for x1, y1, x2, y2 in line_segments_orig:
            vx = x2 - x1; vy = y2 - y1
            nx = -vy; ny = vx
            norm = math.hypot(nx, ny)
            if norm < 1e-12:
                continue
            nx /= norm; ny /= norm
            c = -(nx * x1 + ny * y1); d = -c
            entries.append((d, nx, ny, c))
        entries.sort(key=lambda e: e[0])
        if not entries:
            return [rect_poly]
        segments = []
        for i in range(len(entries) + 1):
            poly = rect_poly[:]
            if i == 0:
                a, b, c = entries[0][1], entries[0][2], entries[0][3]
                poly = clip_polygon_halfplane(poly, -a, -b, -c)
            elif i == len(entries):
                a, b, c = entries[-1][1], entries[-1][2], entries[-1][3]
                poly = clip_polygon_halfplane(poly, a, b, c)
            else:
                a1, b1, c1 = entries[i - 1][1], entries[i - 1][2], entries[i - 1][3]
                a2, b2, c2 = entries[i][1], entries[i][2], entries[i][3]
                poly = clip_polygon_halfplane(poly, a1, b1, c1)
                poly = clip_polygon_halfplane(poly, -a2, -b2, -c2)
            if polygon_area(poly) > 1.0:
                segments.append(poly)
        return segments
    def _build_segment_images(self, img: Image.Image, crop_area, segments_polygons):
        ox1, oy1, ox2, oy2 = crop_area
        crop = img.crop((ox1, oy1, ox2, oy2))
        if not segments_polygons:
            return [crop]
        ordered_polys = sorted(segments_polygons, key=lambda poly: sum(x for x, _ in poly) / len(poly))
        out = []
        for poly in ordered_polys:
            if not poly or polygon_area(poly) < 1.0:
                continue
            local = [(x - ox1, y - oy1) for (x, y) in poly]
            full_rgba = Image.new("RGBA", crop.size, (255, 255, 255, 0))
            mask = Image.new("L", crop.size, 0)
            ImageDraw.Draw(mask).polygon(local, fill=255)
            full_rgba.paste(crop.convert("RGBA"), (0, 0), mask)
            min_x = max(0, int(math.floor(min(x for x, _ in local))))
            min_y = max(0, int(math.floor(min(y for _, y in local))))
            max_x = min(crop.size[0], int(math.ceil(max(x for x, _ in local))))
            max_y = min(crop.size[1], int(math.ceil(max(y for _, y in local))))
            if max_x - min_x < 2 or max_y - min_y < 2:
                continue
            segment_img = full_rgba.crop((min_x, min_y, max_x, max_y))
            bg = Image.new("RGB", segment_img.size, (255, 255, 255))
            bg.paste(segment_img, (0, 0), segment_img.split()[-1])
            out.append(bg)
        return out or [crop]
    def _auto_detect_smart_splits(self, img: Image.Image, crop_area, guide_line_orig=None):
        if not guide_line_orig:
            return []
        ox1, oy1, ox2, oy2 = crop_area
        crop = img.crop((ox1, oy1, ox2, oy2)).convert("L")
        w, h = crop.size
        if w < 20 or h < 20:
            return []
        x1, y1, x2, y2 = guide_line_orig[0]
        px = crop.load()
        def expected_x(global_y):
            if abs(y2 - y1) < 1e-6:
                return (x1 + x2) * 0.5
            t = (global_y - y1) / (y2 - y1)
            return x1 + t * (x2 - x1)
        band = max(2, min(6, w // 120))
        search_radius = max(20, min(120, w // 8))
        y_step = max(6, h // 80)
        samples = []
        for local_y in range(6, h - 6, y_step):
            global_y = oy1 + local_y
            ex = int(round(expected_x(global_y) - ox1))
            xmin = max(6, ex - search_radius)
            xmax = min(w - 7, ex + search_radius)
            if xmin >= xmax:
                continue
            best_x = None
            best_score = None
            for x in range(xmin, xmax + 1):
                center_vals = []
                left_vals = []
                right_vals = []
                for yy in range(local_y - 2, local_y + 3):
                    for xx in range(x - band, x + band + 1):
                        center_vals.append(px[xx, yy])
                    for xx in range(max(0, x - 14), max(0, x - 4)):
                        left_vals.append(px[xx, yy])
                    for xx in range(min(w - 1, x + 4), min(w, x + 15)):
                        right_vals.append(px[xx, yy])
                if not center_vals or not left_vals or not right_vals:
                    continue
                center_mean = sum(center_vals) / len(center_vals)
                left_mean = sum(left_vals) / len(left_vals)
                right_mean = sum(right_vals) / len(right_vals)
                contrast = ((left_mean + right_mean) * 0.5) - center_mean
                distance_penalty = abs(x - ex) * 0.15
                score = center_mean - contrast * 1.8 + distance_penalty
                if best_score is None or score < best_score:
                    best_score = score
                    best_x = x
            if best_x is not None:
                samples.append((local_y, best_x))
        if len(samples) < 2:
            return guide_line_orig
        smoothed = []
        for i in range(len(samples)):
            xs = []
            for j in range(max(0, i - 2), min(len(samples), i + 3)):
                xs.append(samples[j][1])
            smoothed.append((samples[i][0], sum(xs) / len(xs)))
        n = len(smoothed)
        sum_y = sum(y for y, _ in smoothed)
        sum_x = sum(x for _, x in smoothed)
        sum_yy = sum(y * y for y, _ in smoothed)
        sum_yx = sum(y * x for y, x in smoothed)
        denom = n * sum_yy - sum_y * sum_y
        if abs(denom) < 1e-9:
            return guide_line_orig
        m = (n * sum_yx - sum_y * sum_x) / denom
        b = (sum_x - m * sum_y) / n
        x_top_local = b
        x_bottom_local = m * (h - 1) + b
        x_top = max(0, min(img.size[0], ox1 + x_top_local))
        x_bottom = max(0, min(img.size[0], ox1 + x_bottom_local))
        return [(
            x_top,
            oy1,
            x_bottom,
            oy2
        )]
    def _adjust_smart_split_separator(self):
        if not self.chk_split.isChecked() or not self.chk_smart_split.isChecked():
            return False
        if self.canvas.view_image is None:
            return False
        preview = self._apply_options(self.original_image)
        if self.canvas.separator is None:
            w, h = self.canvas.view_image.size
            self.canvas.separator = ImageEditSeparator(cx=w / 2.0, cy=h / 2.0, angle=0.0)
        crop_area = self._get_effective_crop_area(preview)
        lines = self._separator_lines_for_processing(preview)
        detected = self._auto_detect_smart_splits(preview, crop_area, guide_line_orig=lines)
        if not detected:
            return False
        x1, y1, x2, y2 = detected[0]
        vw, vh = self.canvas.view_image.size
        bw, bh = preview.size
        sx = vw / max(1.0, float(bw))
        sy = vh / max(1.0, float(bh))
        self.canvas.separator.set_from_points((x1 * sx, y1 * sy), (x2 * sx, y2 * sy))
        self.canvas.update()
        return True
    def _warp_pil_image_for_processing(self, crop: Image.Image, warp_x: float = 0.0, warp_y: float = 0.0) -> Image.Image:
        return legacy_sine_warp_rgba(crop, warp_x, warp_y)
    def _perspective_coefficients(self, dst_points, src_points):
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
    def _selection_mask_for_src_rect_orig(self, src_rect, size, sx: float, sy: float) -> Image.Image:
        w, h = int(size[0]), int(size[1])
        mask = Image.new("L", (max(1, w), max(1, h)), 0)
        pts = list(getattr(self.canvas, "transform_src_polygon", None) or getattr(self.canvas, "selection_polygon", None) or [])
        if len(pts) >= 3:
            rel = [
                ((p.x() - src_rect.left()) * sx, (p.y() - src_rect.top()) * sy)
                for p in pts
            ]
            ImageDraw.Draw(mask).polygon(rel, fill=255)
        else:
            ImageDraw.Draw(mask).rectangle((0, 0, max(0, w - 1), max(0, h - 1)), fill=255)
        return mask
    def _rotate_mode_base_patch_orig(self, img, crop_rgba, src_mask, src_rect, x1, y1, x2, y2, sx: float, sy: float):
        try:
            crop_w = max(1, int(x2 - x1))
            crop_h = max(1, int(y2 - y1))
            quad = [QPointF(pt) for pt in (getattr(self.canvas, "transform_quad", None) or [])]
            identity = [
                QPointF(src_rect.left(), src_rect.top()),
                QPointF(src_rect.right(), src_rect.top()),
                QPointF(src_rect.right(), src_rect.bottom()),
                QPointF(src_rect.left(), src_rect.bottom()),
            ]
            is_identity_quad = len(quad) == 4 and all(
                abs(quad[i].x() - identity[i].x()) < 0.75 and abs(quad[i].y() - identity[i].y()) < 0.75
                for i in range(4)
            )
            warp_grid = getattr(self.canvas, "_rotate_base_warp_grid", None)
            if warp_grid:
                grid = scale_grid(warp_grid, sx, sy)
                warped, wx, wy = warp_rgba_by_grid(crop_rgba, (x1, y1, x2, y2), grid, img.size)
                return warped.convert("RGBA"), int(wx), int(wy)
            if not quad or len(quad) != 4 or is_identity_quad:
                return crop_rgba.convert("RGBA"), int(x1), int(y1)
            src_corners = [(0, 0), (crop_w, 0), (crop_w, crop_h), (0, crop_h)]
            order = list(getattr(self.canvas, "_rotate_base_source_order", None) or getattr(self.canvas, "transform_source_order", [0, 1, 2, 3]) or [0, 1, 2, 3])
            if len(order) != 4:
                order = [0, 1, 2, 3]
            src_pts = [src_corners[int(idx) % 4] for idx in order]
            dst_pts = [(pt.x() * sx, pt.y() * sy) for pt in quad]
            xs = [p[0] for p in dst_pts]
            ys = [p[1] for p in dst_pts]
            min_x = max(0, int(math.floor(min(xs))))
            min_y = max(0, int(math.floor(min(ys))))
            max_x = min(img.size[0], int(math.ceil(max(xs))))
            max_y = min(img.size[1], int(math.ceil(max(ys))))
            if max_x - min_x < 2 or max_y - min_y < 2:
                return crop_rgba.convert("RGBA"), int(x1), int(y1)
            dst_rel = [(x - min_x, y - min_y) for x, y in dst_pts]
            coeffs = self._perspective_coefficients(dst_rel, src_pts)
            if coeffs is None:
                return crop_rgba.convert("RGBA"), int(x1), int(y1)
            transformed = crop_rgba.transform(
                (max_x - min_x, max_y - min_y),
                Image.PERSPECTIVE,
                coeffs,
                resample=Image.BICUBIC,
                fillcolor=(255, 255, 255, 0),
            ).convert("RGBA")
            return transformed, int(min_x), int(min_y)
        except Exception:
            return crop_rgba.convert("RGBA"), int(x1), int(y1)
    def _apply_free_transform_to_image(self, img: Image.Image) -> Image.Image:
        if not self.canvas.has_active_transform() or self.canvas.view_image is None:
            return img
        try:
            vw, vh = self.canvas.view_image.size
            bw, bh = img.size
            sx = bw / max(1.0, float(vw))
            sy = bh / max(1.0, float(vh))
            src_rect = self.canvas.transform_src_rect or self.canvas.selection_rect
            quad = self.canvas.transform_quad or []
            if src_rect is None or len(quad) != 4:
                return img
            x1 = int(round(max(0.0, min(float(bw - 1), src_rect.left() * sx))))
            y1 = int(round(max(0.0, min(float(bh - 1), src_rect.top() * sy))))
            x2 = int(round(max(float(x1 + 2), min(float(bw), src_rect.right() * sx))))
            y2 = int(round(max(float(y1 + 2), min(float(bh), src_rect.bottom() * sy))))
            crop_w = max(1, x2 - x1)
            crop_h = max(1, y2 - y1)
            src_mask = self._selection_mask_for_src_rect_orig(src_rect, (crop_w, crop_h), sx, sy)
            out = img.convert("RGB").copy()
            mode = str(getattr(self.canvas, "transform_mode", "scale") or "scale")
            if mode == "rotate":
                white = Image.new("RGB", (crop_w, crop_h), "white")
                out.paste(white, (x1, y1), src_mask)
                crop = img.crop((x1, y1, x2, y2)).convert("RGBA")
                crop.putalpha(src_mask)
                base_patch, bx, by = self._rotate_mode_base_patch_orig(img, crop, src_mask, src_rect, x1, y1, x2, y2, sx, sy)
                angle = float(getattr(self.canvas, "transform_rotate_angle", 0.0) or 0.0)
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
                out.paste(rotated.convert("RGB"), (px, py), rotated.split()[-1])
                return out
            if mode == "warp":
                white = Image.new("RGB", (crop_w, crop_h), "white")
                out.paste(white, (x1, y1), src_mask)
                crop_rgba = img.crop((x1, y1, x2, y2)).convert("RGBA")
                crop_rgba.putalpha(src_mask)
                grid = scale_grid(self.canvas._warp_grid_tuples(), sx, sy)
                warped, wx, wy = warp_rgba_by_grid(crop_rgba, (x1, y1, x2, y2), grid, img.size)
                out.paste(warped.convert("RGB"), (wx, wy), warped.split()[-1])
                return out
            white = Image.new("RGB", (crop_w, crop_h), "white")
            out.paste(white, (x1, y1), src_mask)
            crop = img.crop((x1, y1, x2, y2)).convert("RGBA")
            crop.putalpha(src_mask)
            src_corners = [(0, 0), (crop_w, 0), (crop_w, crop_h), (0, crop_h)]
            order = list(self.canvas.transform_source_order or [0, 1, 2, 3])
            if len(order) != 4:
                order = [0, 1, 2, 3]
            src_pts = [src_corners[int(idx) % 4] for idx in order]
            dst_pts = [(pt.x() * sx, pt.y() * sy) for pt in quad]
            xs = [p[0] for p in dst_pts]
            ys = [p[1] for p in dst_pts]
            min_x = max(0, int(math.floor(min(xs))))
            min_y = max(0, int(math.floor(min(ys))))
            max_x = min(bw, int(math.ceil(max(xs))))
            max_y = min(bh, int(math.ceil(max(ys))))
            if max_x - min_x < 2 or max_y - min_y < 2:
                return img
            dst_rel = [(x - min_x, y - min_y) for x, y in dst_pts]
            coeffs = self._perspective_coefficients(dst_rel, src_pts)
            if coeffs is None:
                return img
            transformed = crop.transform(
                (max_x - min_x, max_y - min_y),
                Image.PERSPECTIVE,
                coeffs,
                resample=Image.BICUBIC,
                fillcolor=(255, 255, 255, 0),
            ).convert("RGBA")
            out.paste(transformed.convert("RGB"), (min_x, min_y), transformed.split()[-1])
            return out
        except Exception:
            return img
    def _accept_dialog(self):
        edited = self._apply_options(self.original_image)
        edited = self._apply_free_transform_to_image(edited)
        crop_areas = []
        if self.chk_crop.isChecked() and hasattr(self.canvas, "get_all_crops_orig"):
            crop_areas = self.canvas.get_all_crops_orig()
        if not crop_areas:
            crop_areas = [self._get_effective_crop_area(edited)]
        lines = self._separator_lines_for_processing(edited)
        result_images = []
        for crop_area in crop_areas:
            if self.chk_split.isChecked() and lines:
                effective_lines = lines
                if self.chk_smart_split.isChecked():
                    effective_lines = self._auto_detect_smart_splits(
                        edited,
                        crop_area,
                        guide_line_orig=lines
                    ) or lines
                polys = self._compute_segments_for_crop(crop_area, effective_lines)
                result_images.extend(self._build_segment_images(edited, crop_area, polys))
            else:
                ox1, oy1, ox2, oy2 = crop_area
                result_images.append(edited.crop((ox1, oy1, ox2, oy2)))
        self.result_images = result_images
        self.accept()
    def get_settings(self) -> ImageEditSettings:
        crop_orig = self.canvas.get_crop_orig() if self.chk_crop.isChecked() else None
        crop_areas_orig = self.canvas.get_all_crops_orig() if self.chk_crop.isChecked() and hasattr(self.canvas, "get_all_crops_orig") else ([self.canvas.get_crop_orig()] if self.chk_crop.isChecked() and self.canvas.get_crop_orig() else [])
        selection_orig = self.canvas.get_selection_orig() if getattr(self.canvas, "show_selection", False) else None
        separator_norm = None
        if self.chk_split.isChecked() and self.canvas.separator and self.canvas.view_image is not None:
            w, h = self.canvas.view_image.size
            separator_norm = (
                self.canvas.separator.cx / max(1.0, float(w)),
                self.canvas.separator.cy / max(1.0, float(h)),
                float(self.canvas.separator.angle),
            )
        erase_enabled = bool(self.canvas.show_erase and self.canvas.erase_rect is not None)
        erase_shape = self.canvas.erase_shape if erase_enabled else ""
        erase_orig = self.canvas.get_erase_orig() if erase_enabled else None
        transform_state = self.canvas.get_transform_state_norm() or {}
        return ImageEditSettings(
            rotation_angle=float(self.rotation_angle),
            color_mode=str(self.color_mode),
            gray_level=float(getattr(self, "gray_level", 1.0)),
            contrast_enabled=bool(self.contrast_enabled),
            contrast_level=float(getattr(self, "contrast_level", 2.2)),
            flip_horizontal=bool(getattr(self, "flip_horizontal", False)),
            flip_vertical=bool(getattr(self, "flip_vertical", False)),
            crop_enabled=bool(self.chk_crop.isChecked()),
            crop_orig=crop_orig,
            crop_areas_orig=[tuple(c) for c in crop_areas_orig],
            active_crop_index=int(getattr(self.canvas, "selected_crop_index", -1)),
            selection_enabled=bool(getattr(self.canvas, "show_selection", False)),
            selection_orig=selection_orig,
            split_enabled=bool(self.chk_split.isChecked()),
            separator_norm=separator_norm,
            smart_split_enabled=bool(self.chk_smart_split.isChecked()),
            white_border_px=int(self.white_border_px),
            erase_enabled=erase_enabled,
            erase_shape=erase_shape,
            erase_orig=erase_orig,
            erase_actions=[(shape, tuple(bbox)) for shape, bbox in self.erase_actions],
            free_transform_enabled=bool(transform_state.get("enabled", False)),
            transform_mode=str(transform_state.get("mode", "scale")),
            transform_src_norm=tuple(transform_state.get("src_norm")) if transform_state.get("src_norm") else None,
            transform_dest_norm=[tuple(p) for p in transform_state.get("dest_norm", [])] or None,
            transform_source_order=tuple(transform_state.get("source_order", [0, 1, 2, 3])),
            transform_rotate_angle=float(transform_state.get("rotate_angle", 0.0) or 0.0),
            transform_warp_x=float(transform_state.get("warp_x", 0.0) or 0.0),
            transform_warp_y=float(transform_state.get("warp_y", 0.0) or 0.0),
            transform_warp_grid_norm=[tuple(p) for p in transform_state.get("warp_grid_norm", [])] or None,
        )
    def set_settings(self, settings: ImageEditSettings):
        self.rotation_angle = float(settings.rotation_angle)
        self.color_mode = settings.color_mode
        self.gray_level = float(getattr(settings, "gray_level", 1.0))
        self.contrast_enabled = bool(settings.contrast_enabled)
        self.contrast_level = float(getattr(settings, "contrast_level", 2.2))
        self.flip_horizontal = bool(getattr(settings, "flip_horizontal", False))
        self.flip_vertical = bool(getattr(settings, "flip_vertical", False))
        self.white_border_px = int(settings.white_border_px)
        self.erase_actions = [(shape, tuple(bbox)) for shape, bbox in (settings.erase_actions or [])]
        self.chk_gray.blockSignals(True)
        self.chk_gray.setChecked(self.color_mode == "GRAY")
        self.chk_gray.blockSignals(False)
        if hasattr(self, "contrast_slider"):
            self._set_contrast_slider_from_level(self.contrast_level)
        self.chk_contrast.blockSignals(True)
        self.chk_contrast.setChecked(self.contrast_enabled)
        self.chk_contrast.blockSignals(False)
        if hasattr(self, "contrast_controls_widget"):
            self._update_contrast_slider_ui()
        self.chk_crop.setChecked(bool(settings.crop_enabled))
        if hasattr(self, "chk_selection"):
            self.chk_selection.setChecked(bool(getattr(settings, "selection_enabled", False)))
        self.btn_erase_rect.blockSignals(True)
        self.btn_erase_ellipse.blockSignals(True)
        self.btn_erase_rect.setChecked(
            bool(settings.erase_enabled and settings.erase_shape == "rect")
        )
        self.btn_erase_ellipse.setChecked(
            bool(settings.erase_enabled and settings.erase_shape == "ellipse")
        )
        self.btn_erase_rect.blockSignals(False)
        self.btn_erase_ellipse.blockSignals(False)
        self.canvas.show_erase = bool(settings.erase_enabled)
        self.canvas.erase_shape = settings.erase_shape if settings.erase_enabled else ""
        self.canvas.erase_rect = None
        self.chk_split.setChecked(bool(settings.split_enabled))
        self.chk_smart_split.setEnabled(bool(settings.split_enabled))
        self.chk_smart_split.setChecked(
            bool(settings.smart_split_enabled) and bool(settings.split_enabled)
        )
        self._refresh_preview(reset_zoom=False)
        if settings.erase_enabled and settings.erase_orig:
            self.canvas.set_erase_from_orig(settings.erase_orig)
        if settings.crop_enabled and getattr(settings, "crop_areas_orig", None):
            self.canvas.set_crops_from_orig(list(settings.crop_areas_orig), int(getattr(settings, "active_crop_index", -1)))
        elif settings.crop_enabled and settings.crop_orig:
            self.canvas.set_crop_from_orig(settings.crop_orig)
        if getattr(settings, "selection_enabled", False) and getattr(settings, "selection_orig", None):
            self.canvas.set_selection_from_orig(settings.selection_orig)
        if (
                settings.split_enabled
                and settings.separator_norm
                and self.canvas.view_image is not None
        ):
            w, h = self.canvas.view_image.size
            cxn, cyn, ang = settings.separator_norm
            self.canvas.separator = ImageEditSeparator(
                cx=float(cxn) * w,
                cy=float(cyn) * h,
                angle=float(ang),
            )
            self.canvas.show_separator = True
            self.canvas.update()
        if settings.free_transform_enabled and self.canvas.view_image is not None:
            self.canvas.restore_transform_state_norm({
                "enabled": True,
                "mode": settings.transform_mode,
                "src_norm": settings.transform_src_norm,
                "dest_norm": settings.transform_dest_norm,
                "source_order": list(settings.transform_source_order or [0, 1, 2, 3]),
                "rotate_angle": float(getattr(settings, "transform_rotate_angle", 0.0)),
                "warp_x": float(getattr(settings, "transform_warp_x", 0.0)),
                "warp_y": float(getattr(settings, "transform_warp_y", 0.0)),
                "warp_grid_norm": getattr(settings, "transform_warp_grid_norm", None),
            })
        else:
            self.canvas.cancel_free_transform()
        self._sync_transform_mode_buttons()
