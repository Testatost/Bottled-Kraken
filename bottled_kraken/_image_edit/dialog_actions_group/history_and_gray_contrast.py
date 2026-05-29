from bottled_kraken.common import (
    QDialog,
    QMenu,
)
from bottled_kraken._image_edit.common import ImageEditSeparator, ImageEditSettings, WhiteBorderDialog, LiveValueDialog
from bottled_kraken._image_edit.canvas import ImageEditCanvas
class ImageEditDialogHistoryGrayContrastMixin:
        def _make_history_snapshot(self):
            return {
                "settings": self.get_settings(),
                "image": self.original_image.copy() if getattr(self, "original_image", None) is not None else None,
            }
        def _restore_history_snapshot(self, snap):
            if not isinstance(snap, dict):
                self.set_settings(snap)
                self._refresh_preview(reset_zoom=False)
                return
            img = snap.get("image")
            if img is not None:
                self.original_image = img.copy()
            self.set_settings(snap.get("settings"))
            self._refresh_preview(reset_zoom=False)
            self.canvas.update()
        def _history_push(self):
            if getattr(self, "_history_restoring", False):
                return
            undo = getattr(self, "_history_undo", None)
            if undo is None:
                self._history_undo = []
                undo = self._history_undo
            undo.append(self._make_history_snapshot())
            if len(undo) > 100:
                del undo[:-100]
            self._history_redo = []
        def _undo_action(self):
            undo = getattr(self, "_history_undo", [])
            if len(undo) < 2:
                return
            current = undo.pop()
            self._history_redo.append(current)
            self._history_restoring = True
            try:
                self._restore_history_snapshot(undo[-1])
            finally:
                self._history_restoring = False
            self.canvas.setFocus()
        def _redo_action(self):
            redo = getattr(self, "_history_redo", [])
            if not redo:
                return
            snap = redo.pop()
            self._history_restoring = True
            try:
                self._restore_history_snapshot(snap)
            finally:
                self._history_restoring = False
            self._history_undo.append(self._make_history_snapshot())
            self.canvas.setFocus()
        def _activate_or_start_transform_mode(self, mode: str):
            if not self.canvas.has_active_transform() and self.canvas.selection_rect is not None:
                self.canvas.start_free_transform()
            if self.canvas.has_active_transform():
                self._set_transform_mode(mode)
            self._sync_transform_mode_buttons()
            self.canvas.setFocus()
        def _gray_level_from_slider(self, value: int) -> float:
            return max(0.0, min(1.0, float(value) / 100.0))
        def _gray_slider_from_level(self, level: float) -> int:
            return int(round(max(0.0, min(1.0, float(level))) * 100.0))
        def _open_gray_dialog(self):
            prev_enabled = bool(self.color_mode == "GRAY")
            prev_level = float(getattr(self, "gray_level", 0.0)) if prev_enabled else 0.0
            dlg = LiveValueDialog(self._tr("image_edit_gray"), self._tr("image_edit_gray"), 0, 100, self._gray_slider_from_level(prev_level), self)
            dlg.slider.valueChanged.connect(lambda v: self._preview_gray_dialog_change(v))
            if dlg.exec() == QDialog.Accepted:
                value = int(dlg.value())
                self.gray_level = self._gray_level_from_slider(value)
                self.color_mode = "GRAY" if value > 0 else "RGB"
                self.chk_gray.blockSignals(True); self.chk_gray.setChecked(value > 0); self.chk_gray.blockSignals(False)
                self._refresh_preview(reset_zoom=False)
                self._history_push()
            else:
                self.color_mode = "GRAY" if prev_enabled else "RGB"
                self.gray_level = prev_level
                self.chk_gray.blockSignals(True); self.chk_gray.setChecked(prev_enabled); self.chk_gray.blockSignals(False)
                self._refresh_preview(reset_zoom=False)
        def _preview_gray_dialog_change(self, value: int):
            value = int(value)
            self.gray_level = self._gray_level_from_slider(value)
            self.color_mode = "GRAY" if value > 0 else "RGB"
            self.chk_gray.blockSignals(True); self.chk_gray.setChecked(value > 0); self.chk_gray.blockSignals(False)
            self._refresh_preview(reset_zoom=False)
        def _open_contrast_dialog(self):
            prev_enabled = bool(getattr(self, "contrast_enabled", False))
            prev_level = float(getattr(self, "contrast_level", 1.0))
            initial = int(round(((prev_level - 1.0) / 3.0) * 100.0)) if prev_enabled else 0
            dlg = LiveValueDialog(self._tr("image_edit_contrast"), self._tr("image_edit_contrast"), 0, 100, initial, self)
            dlg.slider.valueChanged.connect(lambda v: self._preview_contrast_dialog_change(v))
            if dlg.exec() == QDialog.Accepted:
                value = int(dlg.value())
                self.contrast_enabled = value > 0
                self.contrast_level = self._contrast_level_from_slider(value)
                self.chk_contrast.blockSignals(True); self.chk_contrast.setChecked(value > 0); self.chk_contrast.blockSignals(False)
                self._refresh_preview(reset_zoom=False)
                self._history_push()
            else:
                self.contrast_enabled = prev_enabled
                self.contrast_level = prev_level
                self.chk_contrast.blockSignals(True); self.chk_contrast.setChecked(prev_enabled); self.chk_contrast.blockSignals(False)
                self._refresh_preview(reset_zoom=False)
        def _preview_contrast_dialog_change(self, value: int):
            value = int(value)
            self.contrast_enabled = value > 0
            self.contrast_level = self._contrast_level_from_slider(value)
            self.chk_contrast.blockSignals(True); self.chk_contrast.setChecked(value > 0); self.chk_contrast.blockSignals(False)
            self._refresh_preview(reset_zoom=False)
        def _on_gray_button_clicked(self, checked: bool):
            if checked:
                self._open_gray_dialog()
            else:
                self.color_mode = "RGB"
                self._refresh_preview(reset_zoom=False)
                self._history_push()
        def _on_contrast_button_clicked(self, checked: bool):
            if checked:
                self._open_contrast_dialog()
            else:
                self.contrast_enabled = False
                self._refresh_preview(reset_zoom=False)
                self._history_push()
        def _show_image_context_menu(self, global_pos):
            menu = QMenu(self)
            act_rot_l = menu.addAction(self._tr("image_edit_menu_rotate_left"))
            act_rot_r = menu.addAction(self._tr("image_edit_menu_rotate_right"))
            menu.addSeparator()
            act_flip_h = menu.addAction(self._tr("image_edit_flip_horizontal"))
            act_flip_v = menu.addAction(self._tr("image_edit_flip_vertical"))
            menu.addSeparator()
            act_new_crop = menu.addAction(self._tr("image_edit_context_crop_area"))
            act_split = menu.addAction(self._tr("image_edit_separator"))
            act_split.setCheckable(True); act_split.setChecked(bool(self.chk_split.isChecked()))
            menu.addSeparator()
            act_gray = menu.addAction(self._tr("image_edit_gray"))
            act_gray.setCheckable(True); act_gray.setChecked(self.color_mode == "GRAY")
            act_contrast = menu.addAction(self._tr("image_edit_contrast"))
            act_contrast.setCheckable(True); act_contrast.setChecked(bool(getattr(self, "contrast_enabled", False)))
            chosen = menu.exec(global_pos)
            if chosen == act_rot_l:
                self._rotate_by(-90)
            elif chosen == act_rot_r:
                self._rotate_by(90)
            elif chosen == act_flip_h:
                self._flip_horizontal()
            elif chosen == act_flip_v:
                self._flip_vertical()
            elif chosen == act_new_crop:
                self._begin_crop_drag_at_global_pos(global_pos)
            elif chosen == act_split:
                self.chk_split.setChecked(not self.chk_split.isChecked())
            elif chosen == act_gray:
                if self.color_mode == "GRAY":
                    self.chk_gray.setChecked(False); self._on_gray_button_clicked(False)
                else:
                    self.chk_gray.setChecked(True); self._open_gray_dialog()
            elif chosen == act_contrast:
                if self.contrast_enabled:
                    self.chk_contrast.setChecked(False); self._on_contrast_button_clicked(False)
                else:
                    self.chk_contrast.setChecked(True); self._open_contrast_dialog()
