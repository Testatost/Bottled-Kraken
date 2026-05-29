from bottled_kraken.common import (
    Image,
    ImageDraw,
    Optional,
    QDialog,
    QMessageBox,
    QPointF,
    QRectF,
    Qt,
    Tuple,
)
from bottled_kraken._image_edit.common import ImageEditSeparator, ImageEditSettings, WhiteBorderDialog, LiveValueDialog
from bottled_kraken._image_edit.canvas import ImageEditCanvas
class ImageEditDialogSelectionCropEraseMixin:
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
        def _selection_mask_for_original_image(self):
            if self.canvas.selection_rect is None or self.canvas.view_image is None:
                return None
            bw, bh = self.original_image.size
            vw, vh = self.canvas.view_image.size
            sx = bw / max(1.0, float(vw))
            sy = bh / max(1.0, float(vh))
            mask = Image.new("L", (bw, bh), 0)
            draw = ImageDraw.Draw(mask)
            pts = list(getattr(self.canvas, "selection_polygon", None) or [])
            if len(pts) >= 3:
                draw.polygon([(p.x() * sx, p.y() * sy) for p in pts], fill=255)
            elif self.canvas.selection_rect is not None:
                r = self.canvas.selection_rect
                draw.rectangle(
                    (
                        int(round(r.left() * sx)),
                        int(round(r.top() * sy)),
                        int(round(r.right() * sx)),
                        int(round(r.bottom() * sy)),
                    ),
                    fill=255,
                )
            else:
                return None
            return mask
        def _delete_selection_content(self):
            if self.canvas.selection_rect is None:
                return False
            mask = self._selection_mask_for_original_image()
            if mask is None:
                return False
            self._history_push()
            white = Image.new("RGB", self.original_image.size, "white")
            self.original_image = self.original_image.convert("RGB")
            self.original_image.paste(white, (0, 0), mask)
            self.canvas.selection_rect = None
            self.canvas.selection_polygon = None
            self._refresh_preview(reset_zoom=False)
            self._set_selection_draw_mode("rect")
            self._history_push()
            return True
        def _delete_selected_crop_or_erase(self):
            if self.canvas.selection_rect is not None:
                if self._delete_selection_content():
                    return
            if getattr(self.canvas, "show_crop", False) and getattr(self.canvas, "selected_crop_index", -1) >= 0:
                if self.canvas.delete_selected_crop():
                    self._history_push()
                    return
            self._commit_erase_selection()
        def keyPressEvent(self, event):
            if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_Z:
                self._undo_action()
                event.accept()
                return
            if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_Y:
                self._redo_action()
                event.accept()
                return
            if event.key() == Qt.Key_Escape:
                self._clear_selection()
                event.accept()
                return
            if event.key() == Qt.Key_Delete:
                if self._delete_selection_content():
                    event.accept()
                    return
                if getattr(self.canvas, "show_crop", False) and getattr(self.canvas, "selected_crop_index", -1) >= 0:
                    if self.canvas.delete_selected_crop():
                        self._history_push()
                        event.accept()
                        return
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
            if checked and self.canvas.has_active_transform():
                self.canvas.cancel_free_transform()
            self._sync_transform_mode_buttons()
            self.canvas.update()
            self._history_push()
        def _begin_crop_drag_at_global_pos(self, global_pos):
            self.canvas.cancel_free_transform()
            self.canvas.selection_rect = None
            self.canvas.show_crop = True
            self.chk_crop.blockSignals(True)
            self.chk_crop.setChecked(True)
            self.chk_crop.blockSignals(False)
            local_pos = self.canvas.mapFromGlobal(global_pos)
            begin = getattr(self.canvas, "begin_crop_drag_from_widget_pos", None)
            if callable(begin):
                begin(QPointF(local_pos))
            self._sync_transform_mode_buttons()
        def _create_crop_area(self):
            self.canvas.cancel_free_transform()
            self.canvas.selection_rect = None
            self.canvas.show_crop = True
            self.chk_crop.blockSignals(True)
            self.chk_crop.setChecked(True)
            self.chk_crop.blockSignals(False)
            self.canvas.create_default_crop()
            self.canvas.update()
            self._sync_transform_mode_buttons()
            self._history_push()
        def _on_crop_button_clicked(self, checked: bool):
            if checked:
                self.canvas.cancel_free_transform()
                self.canvas.selection_rect = None
                self.canvas.show_crop = True
            else:
                self.canvas.show_crop = False
            self.canvas.update()
        def _set_selection_draw_mode(self, mode: str):
            mode = str(mode or "rect").lower()
            if mode not in ("rect", "ellipse", "polygon", "freehand"):
                mode = "rect"
            if mode in ("rect", "ellipse", "polygon", "freehand"):
                if hasattr(self, "chk_crop") and self.chk_crop.isChecked():
                    self.chk_crop.setChecked(False)
                self.canvas.cancel_free_transform()
                self.canvas.show_selection = True
            self.canvas.set_selection_draw_mode(mode)
            for attr, active in (
                ("btn_rect_selection", mode == "rect"),
                ("btn_ellipse_selection", mode == "ellipse"),
                ("btn_freehand_selection", mode == "freehand"),
                ("btn_polygon_selection", mode == "polygon"),
            ):
                if hasattr(self, attr):
                    btn = getattr(self, attr)
                    btn.blockSignals(True)
                    btn.setChecked(bool(active))
                    btn.blockSignals(False)
            self.canvas.setFocus()
        def _toggle_grid(self, checked: bool):
            self.canvas.show_grid = checked
            self.grid_slider.setEnabled(bool(checked))
            self.lbl_grid_size.setEnabled(bool(checked))
            self.grid_slider.setVisible(bool(checked))
            self.lbl_grid_size.setVisible(bool(checked))
            self.canvas.update()
        def _on_grid_slider_changed(self, value: int):
            self.canvas.grid_spacing = int(round(6 + (value / 100.0) * 90))
            self.canvas.update()
        def _toggle_crop(self, checked: bool):
            self.canvas.show_crop = checked
            if checked:
                self.canvas.cancel_free_transform()
                self.canvas.selection_rect = None
                self.canvas.selection_polygon = None
                self.canvas.set_selection_draw_mode("rect")
                for attr, active in (
                    ("btn_rect_selection", True),
                    ("btn_ellipse_selection", False),
                    ("btn_freehand_selection", False),
                    ("btn_polygon_selection", False),
                ):
                    if hasattr(self, attr):
                        btn = getattr(self, attr)
                        btn.blockSignals(True)
                        btn.setChecked(bool(active))
                        btn.blockSignals(False)
            elif self.canvas.has_active_transform():
                self.canvas.cancel_free_transform()
            self._sync_transform_mode_buttons()
            self.canvas.update()
            self._history_push()
        def _toggle_selection(self, checked: bool):
            self.canvas.show_selection = bool(checked)
            if not checked:
                self.canvas.selection_rect = None
                if self.canvas.has_active_transform():
                    self.canvas.cancel_free_transform()
            self._sync_transform_mode_buttons()
            self.canvas.update()
            self.canvas.changed.emit()
        def _toggle_split(self, checked: bool):
            self.canvas.show_separator = checked
            self.chk_smart_split.setEnabled(checked)
            if checked and self.canvas.separator is None and self.canvas.view_image is not None:
                w, h = self.canvas.view_image.size
                self.canvas.separator = ImageEditSeparator(cx=w / 2.0, cy=h / 2.0, angle=0.0)
            if not checked:
                self.canvas.separator = None
                if self.chk_smart_split.isChecked():
                    self.chk_smart_split.blockSignals(True)
                    self.chk_smart_split.setChecked(False)
                    self.chk_smart_split.blockSignals(False)
            if checked and self.chk_smart_split.isChecked():
                adjust = getattr(self, "_adjust_smart_split_separator", None)
                if callable(adjust):
                    adjust()
            self.canvas.update()
            self._history_push()
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
