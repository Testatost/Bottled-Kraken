from bottled_kraken.common import (
    Image,
    ImageDraw,
    ImageEnhance,
    ImageOps,
)
from bottled_kraken._image_edit.common import ImageEditSeparator, ImageEditSettings, WhiteBorderDialog
from bottled_kraken._image_edit.canvas import ImageEditCanvas
from PySide6.QtGui import QPainterPath
class ImageEditDialogOptionsAndNavigationMixin:
        def _apply_options(self, img: Image.Image) -> Image.Image:
            out = img.convert("RGB")
            if bool(getattr(self, "flip_horizontal", False)):
                out = ImageOps.mirror(out)
            if bool(getattr(self, "flip_vertical", False)):
                out = ImageOps.flip(out)
            if self.color_mode == "GRAY":
                gray = ImageOps.grayscale(out).convert("RGB")
                gray_level = max(0.0, min(1.0, float(getattr(self, "gray_level", 1.0))))
                out = Image.blend(out, gray, gray_level)
            if self.contrast_enabled:
                level = max(1.0, min(4.0, float(getattr(self, "contrast_level", 2.2))))
                sharpness_level = max(1.0, min(2.0, 1.0 + ((level - 1.0) / 3.0)))
                out = ImageOps.autocontrast(out, cutoff=1)
                out = ImageEnhance.Contrast(out).enhance(level)
                out = ImageEnhance.Sharpness(out).enhance(sharpness_level)
            if abs(self.rotation_angle) > 0.01:
                out = out.rotate(
                    -self.rotation_angle,
                    expand=True,
                    resample=Image.BICUBIC,
                    fillcolor="white"
                )
            if self.white_border_px > 0:
                out = ImageOps.expand(out, border=int(self.white_border_px), fill="white")
            draw = ImageDraw.Draw(out)
            for shape, bbox in self.erase_actions:
                x1, y1, x2, y2 = bbox
                if shape == "ellipse":
                    draw.ellipse((x1, y1, x2, y2), fill="white")
                else:
                    draw.rectangle((x1, y1, x2, y2), fill="white")
            live_action = self._current_erase_action()
            if live_action:
                shape, bbox = live_action
                x1, y1, x2, y2 = bbox
                if shape == "ellipse":
                    draw.ellipse((x1, y1, x2, y2), fill="white")
                else:
                    draw.rectangle((x1, y1, x2, y2), fill="white")
            return out
        def _refresh_preview(self, reset_zoom: bool = False):
            old_crops = self.canvas.get_all_crops_orig() if hasattr(self.canvas, "get_all_crops_orig") else ([self.canvas.get_crop_orig()] if self.canvas.get_crop_orig() else [])
            old_crop_idx = getattr(self.canvas, "selected_crop_index", -1)
            old_erase = self.canvas.get_erase_orig() if self.canvas.show_erase else None
            old_transform = self.canvas.get_transform_state_norm()
            preview = self._apply_options(self.original_image)
            self.canvas.rotation_angle = self.rotation_angle
            self.canvas.set_image(preview, reset_zoom=reset_zoom)
            if self.chk_crop.isChecked() and old_crops:
                self.canvas.set_crops_from_orig(old_crops, old_crop_idx)
            if self.canvas.show_erase and old_erase:
                self.canvas.set_erase_from_orig(old_erase)
            if self.chk_split.isChecked() and self.canvas.separator is None and self.canvas.view_image is not None:
                w, h = self.canvas.view_image.size
                self.canvas.separator = ImageEditSeparator(cx=w / 2.0, cy=h / 2.0, angle=0.0)
            if self.chk_split.isChecked() and self.chk_smart_split.isChecked():
                adjust = getattr(self, "_adjust_smart_split_separator", None)
                if callable(adjust):
                    adjust()
            if old_transform:
                self.canvas.restore_transform_state_norm(old_transform)
            self.canvas.update()
            self._update_border_button_text()
            self._sync_transform_mode_buttons()
        def _sync_from_canvas(self):
            self._sync_transform_mode_buttons()
        def _on_canvas_rotation_committed(self, angle: float):
            self.rotation_angle = float(angle) % 360.0
            self.canvas.rotation_angle = 0.0
            self.canvas.preview_rotation_angle = 0.0
            self.canvas.is_preview_rotating = False
            self.canvas.crop_rect = None
            self.canvas.separator = None
            self.canvas.cancel_free_transform()
            self._refresh_preview(reset_zoom=False)
        def _toggle_smart_split(self, checked: bool):
            if checked and not self.chk_split.isChecked():
                self.chk_smart_split.blockSignals(True)
                self.chk_smart_split.setChecked(False)
                self.chk_smart_split.blockSignals(False)
                return
            if checked:
                adjust = getattr(self, "_adjust_smart_split_separator", None)
                if callable(adjust):
                    adjust()
            self.canvas.update()
        def _go_prev(self):
            if callable(self.on_prev):
                self.on_prev(self)
        def _go_next(self):
            if callable(self.on_next):
                self.on_next(self)
