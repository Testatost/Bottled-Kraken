"""Mixin-Methoden für den Bildbearbeitungsdialog."""
from ..shared import *
from ..dialogs import *
from .common import ImageEditSettings, WhiteBorderDialog
from .canvas import ImageEditCanvas

class ImageEditDialogActionsMixin:
    def _current_erase_action(self) -> Optional[Tuple[str, Tuple[int, int, int, int]]]:
        if not self.canvas.show_erase:
            return None
        erase_orig = self.canvas.get_erase_orig()
        if not erase_orig:
            return None
        shape = self.canvas.erase_shape or "rect"
        return shape, erase_orig

    def _commit_erase_selection(self):
        action = self._current_erase_action()
        if action is None:
            return
        shape, bbox = action
        self.erase_actions.append((shape, tuple(bbox)))
        self.canvas.erase_rect = None
        self._refresh_preview(reset_zoom=False)
        self.canvas.setFocus()

    def _undo_erase_commit(self):
        if not self.erase_actions:
            return
        self.erase_actions.pop()
        self.canvas.erase_rect = None
        self._refresh_preview(reset_zoom=False)
        self.canvas.setFocus()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Left, Qt.Key_Up):
            self._go_prev()
            event.accept()
            return
        if event.key() in (Qt.Key_Right, Qt.Key_Down):
            self._go_next()
            event.accept()
            return
        super().keyPressEvent(event)

    def _apply_selected(self):
        if callable(self.on_apply_selected):
            self._batch_apply_used = True
            self.result_images = []
            self.on_apply_selected(self)
            self.accept()

    def _apply_all(self):
        if callable(self.on_apply_all):
            self._batch_apply_used = True
            self.result_images = []
            self.on_apply_all(self)
            self.accept()

    def _update_border_button_text(self):
        if self.white_border_px > 0:
            self.btn_border.setText(self._tr("image_edit_white_border_with_px", self.white_border_px))
        else:
            self.btn_border.setText(self._tr("image_edit_white_border"))

    def _open_border_dialog(self):
        dlg = WhiteBorderDialog(self.white_border_px, self)
        if dlg.exec() == QDialog.Accepted:
            self.white_border_px = dlg.get_value()
            self._update_border_button_text()
            self._refresh_preview(reset_zoom=False)

    def _toggle_rotation_mode(self, checked: bool):
        self.canvas.rotation_mode = checked
        self.btn_rotate_mode.setText(self._tr("image_edit_rotate_on") if checked else self._tr("image_edit_rotate_off"))
        self.canvas.update()

    def _toggle_grid(self, checked: bool):
        self.canvas.show_grid = checked
        self.grid_slider.setEnabled(bool(checked))
        self.lbl_grid_size.setEnabled(bool(checked))
        self.canvas.update()

    def _on_grid_slider_changed(self, value: int):
        # oben fein = kleine Abstände
        # unten grob = große Abstände
        self.canvas.grid_spacing = int(round(6 + (value / 100.0) * 90))
        self.canvas.update()

    def _toggle_crop(self, checked: bool):
        self.canvas.show_crop = checked
        if checked and self.canvas.crop_rect is None and self.canvas.view_image is not None:
            self.canvas.create_default_crop()
        self.canvas.update()

    def _toggle_split(self, checked: bool):
        self.canvas.show_separator = checked
        self.chk_smart_split.setEnabled(checked)
        if checked and self.canvas.separator is None and self.canvas.view_image is not None:
            w, h = self.canvas.view_image.size
            self.canvas.separator = ImageEditSeparator(cx=w / 2.0, cy=h / 2.0, angle=0.0)
        if not checked:
            self.canvas.separator = None
            # Wenn Trennbalken aus ist, muss Smart-Splitting auch aus sein
            if self.chk_smart_split.isChecked():
                self.chk_smart_split.blockSignals(True)
                self.chk_smart_split.setChecked(False)
                self.chk_smart_split.blockSignals(False)
        self.canvas.update()

    def _toggle_erase_mode(self, shape: str, checked: bool):
        if checked and self.canvas.rotation_mode:
            QMessageBox.information(
                self,
                self._tr("image_edit_notice_title"),
                self._tr("image_edit_turn_off_rotation_first")
            )
            btn = self.btn_erase_rect if shape == "rect" else self.btn_erase_ellipse
            btn.blockSignals(True)
            btn.setChecked(False)
            btn.blockSignals(False)
            self.canvas.show_erase = False
            self.canvas.erase_shape = ""
            self.canvas.update()
            return
        if checked:
            if shape == "rect" and self.btn_erase_ellipse.isChecked():
                self.btn_erase_ellipse.blockSignals(True)
                self.btn_erase_ellipse.setChecked(False)
                self.btn_erase_ellipse.blockSignals(False)
            if shape == "ellipse" and self.btn_erase_rect.isChecked():
                self.btn_erase_rect.blockSignals(True)
                self.btn_erase_rect.setChecked(False)
                self.btn_erase_rect.blockSignals(False)
            self.canvas.show_erase = True
            self.canvas.erase_shape = shape
            if self.canvas.erase_rect is None and self.canvas.view_image is not None:
                w, h = self.canvas.view_image.size
                self.canvas.erase_rect = QRectF(w * 0.35, h * 0.20, w * 0.25, h * 0.25)
        else:
            if not self.btn_erase_rect.isChecked() and not self.btn_erase_ellipse.isChecked():
                self.canvas.show_erase = False
                self.canvas.erase_shape = ""
        self.canvas.update()
        self.canvas.changed.emit()

    def _clear_erase_area(self):
        self.canvas.erase_rect = None
        self.canvas.show_erase = False
        self.canvas.erase_shape = ""
        self.btn_erase_rect.blockSignals(True)
        self.btn_erase_rect.setChecked(False)
        self.btn_erase_rect.blockSignals(False)
        self.btn_erase_ellipse.blockSignals(True)
        self.btn_erase_ellipse.setChecked(False)
        self.btn_erase_ellipse.blockSignals(False)
        self.canvas.update()
        self.canvas.changed.emit()

    def _toggle_gray(self, checked: bool):
        self.color_mode = "GRAY" if checked else "RGB"
        self._refresh_preview(reset_zoom=False)

    def _toggle_contrast(self, checked: bool):
        self.contrast_enabled = bool(checked)
        self._refresh_preview(reset_zoom=False)

    def _rotate_by(self, delta: float):
        self.rotation_angle = (self.rotation_angle + delta) % 360.0
        self.canvas.crop_rect = None
        self.canvas.separator = None
        self._refresh_preview(reset_zoom=False)

    def _reset_rotation(self):
        self.rotation_angle = 0.0
        self.canvas.crop_rect = None
        self.canvas.separator = None
        self._refresh_preview(reset_zoom=False)
