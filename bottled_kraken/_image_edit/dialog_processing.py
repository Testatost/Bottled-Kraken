"""Mixin-Methoden für den Bildbearbeitungsdialog."""
from ..shared import *
from ..dialogs import *
from .common import ImageEditSettings, WhiteBorderDialog
from .canvas import ImageEditCanvas

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
        # Smart-Splitting funktioniert nur mit aktivem Trennbalken
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

    def _accept_dialog(self):
        edited = self._apply_options(self.original_image)
        crop_area = self._get_effective_crop_area(edited)
        lines = self._separator_lines_for_processing(edited)
        if self.chk_split.isChecked() and lines:
            effective_lines = lines
            if self.chk_smart_split.isChecked():
                effective_lines = self._auto_detect_smart_splits(
                    edited,
                    crop_area,
                    guide_line_orig=lines
                ) or lines
            polys = self._compute_segments_for_crop(crop_area, effective_lines)
            self.result_images = self._build_segment_images(edited, crop_area, polys)
        else:
            ox1, oy1, ox2, oy2 = crop_area
            self.result_images = [edited.crop((ox1, oy1, ox2, oy2))]
        self.accept()

    def get_settings(self) -> ImageEditSettings:
        crop_orig = self.canvas.get_crop_orig() if self.chk_crop.isChecked() else None
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
        return ImageEditSettings(
            rotation_angle=float(self.rotation_angle),
            color_mode=str(self.color_mode),
            contrast_enabled=bool(self.contrast_enabled),
            crop_enabled=bool(self.chk_crop.isChecked()),
            crop_orig=crop_orig,
            split_enabled=bool(self.chk_split.isChecked()),
            separator_norm=separator_norm,
            smart_split_enabled=bool(self.chk_smart_split.isChecked()),
            white_border_px=int(self.white_border_px),
            erase_enabled=erase_enabled,
            erase_shape=erase_shape,
            erase_orig=erase_orig,
            erase_actions=[(shape, tuple(bbox)) for shape, bbox in self.erase_actions],
        )

    def set_settings(self, settings: ImageEditSettings):
        self.rotation_angle = float(settings.rotation_angle)
        self.color_mode = settings.color_mode
        self.contrast_enabled = bool(settings.contrast_enabled)
        self.white_border_px = int(settings.white_border_px)
        self.erase_actions = [(shape, tuple(bbox)) for shape, bbox in (settings.erase_actions or [])]
        self.chk_gray.setChecked(self.color_mode == "GRAY")
        self.chk_contrast.setChecked(self.contrast_enabled)
        self.chk_crop.setChecked(bool(settings.crop_enabled))
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
        if settings.crop_enabled and settings.crop_orig:
            self.canvas.set_crop_from_orig(settings.crop_orig)
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
