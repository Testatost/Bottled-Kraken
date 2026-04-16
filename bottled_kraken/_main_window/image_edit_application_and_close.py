"""Mixin für MainWindow: image edit application and close."""
from ..shared import *
from ..ui_components import *
from ..workers import *
from ..dialogs import *
from ..image_edit import *

class MainWindowImageEditApplicationAndCloseMixin:
    def _load_task_into_edit_dialog(self, dlg: ImageEditDialog, task: TaskItem):
        image = _load_image_color(task.path)
        dlg.original_image = image.convert("RGB")
        dlg.setWindowTitle(self._tr("image_edit_title", task.display_name))
        dlg.rotation_angle = 0.0
        dlg.erase_actions = []
        dlg.canvas.crop_rect = None
        dlg.canvas.separator = None
        dlg.canvas.erase_rect = None
        dlg.canvas.show_erase = False
        dlg.canvas.erase_shape = ""
        dlg.chk_crop.blockSignals(True)
        dlg.chk_crop.setChecked(False)
        dlg.chk_crop.blockSignals(False)
        dlg.chk_split.blockSignals(True)
        dlg.chk_split.setChecked(False)
        dlg.chk_split.blockSignals(False)
        dlg.chk_smart_split.blockSignals(True)
        dlg.chk_smart_split.setChecked(False)
        dlg.chk_smart_split.setEnabled(False)
        dlg.chk_smart_split.blockSignals(False)
        dlg.chk_gray.blockSignals(True)
        dlg.chk_gray.setChecked(False)
        dlg.chk_gray.blockSignals(False)
        dlg.chk_contrast.blockSignals(True)
        dlg.chk_contrast.setChecked(False)
        dlg.chk_contrast.blockSignals(False)
        dlg.btn_erase_rect.blockSignals(True)
        dlg.btn_erase_ellipse.blockSignals(True)
        dlg.btn_erase_rect.setChecked(False)
        dlg.btn_erase_ellipse.setChecked(False)
        dlg.btn_erase_rect.blockSignals(False)
        dlg.btn_erase_ellipse.blockSignals(False)
        dlg._refresh_preview(reset_zoom=True)

    def _finalize_image_edit_batch(self, status_message: str):
        self._refresh_queue_numbers()
        self._fit_queue_columns_exact()
        self._update_queue_hint()
        self.status_bar.showMessage(status_message)

    def _apply_image_edit_to_targets(
            self,
            targets: List[TaskItem],
            settings: ImageEditSettings,
            status_message: str
    ):
        if not targets:
            self._finalize_image_edit_batch(status_message)
            return
        total = len(targets)
        progress = QProgressDialog(
            self._tr("image_edit_batch_label", 0, total, ""),
            self._tr("btn_cancel"),
            0,
            total,
            self
        )
        progress.setWindowTitle(self._tr("image_edit_batch_title"))
        progress.setWindowModality(Qt.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.setAutoClose(True)
        progress.setAutoReset(True)
        progress.setValue(0)
        try:
            for idx, tgt in enumerate(targets, start=1):
                progress.setLabelText(
                    self._tr("image_edit_batch_label", idx, total, tgt.display_name)
                )
                progress.setValue(idx - 1)
                QCoreApplication.processEvents()
                if progress.wasCanceled():
                    self._finalize_image_edit_batch(self._tr("msg_image_edit_batch_cancelled"))
                    return
                try:
                    result_images = self._apply_image_edit_settings_to_task(tgt, settings)
                    if result_images:
                        self._create_edited_tasks_from_images(tgt, result_images)
                except Exception as e:
                    self._log(self._tr_log("log_image_edit_error", tgt.display_name, e))
                progress.setValue(idx)
                QCoreApplication.processEvents()
                if progress.wasCanceled():
                    self._finalize_image_edit_batch(self._tr("msg_image_edit_batch_cancelled"))
                    return
        finally:
            progress.close()
        self._finalize_image_edit_batch(status_message)

    def open_image_edit_dialog(self):
        task = self._current_task()
        if not task or not task.path or not os.path.exists(task.path):
            QMessageBox.information(self, self._tr("info_title"),
                                    self._tr("warn_select_image_or_pdf_page"))
            return
        try:
            image = _load_image_color(task.path)
        except Exception as e:
            QMessageBox.warning(self, self._tr("warn_title"), f"Bild konnte nicht geladen werden:\n{e}")
            return
        current_row = self.queue_table.currentRow()
        if current_row < 0:
            current_row = 0
        def _prev(dialog):
            row = self.queue_table.currentRow()
            if row > 0:
                self.queue_table.selectRow(row - 1)
                next_task = self._current_task()
                if next_task and os.path.exists(next_task.path):
                    self._load_task_into_edit_dialog(dialog, next_task)
        def _next(dialog):
            row = self.queue_table.currentRow()
            if row < self.queue_table.rowCount() - 1:
                self.queue_table.selectRow(row + 1)
                next_task = self._current_task()
                if next_task and os.path.exists(next_task.path):
                    self._load_task_into_edit_dialog(dialog, next_task)
        def _apply_selected(dialog):
            settings = dialog.get_settings()
            targets = self._selected_or_checked_tasks_for_edit()
            if not targets:
                QMessageBox.information(self, self._tr("info_title"), self._tr("info_no_marked_images_found"))
                return
            self._apply_image_edit_to_targets(
                targets,
                settings,
                self._tr("msg_image_edit_selected_applied")
            )
        def _apply_all(dialog):
            settings = dialog.get_settings()
            self._apply_image_edit_to_targets(
                list(self.queue_items),
                settings,
                self._tr("msg_image_edit_all_applied")
            )
        dlg = ImageEditDialog(
            image,
            task.display_name or os.path.basename(task.path),
            self,
            on_prev=_prev,
            on_next=_next,
            on_apply_selected=_apply_selected,
            on_apply_all=_apply_all,
        )
        if dlg.exec() != QDialog.Accepted:
            return
        if getattr(dlg, "_batch_apply_used", False):
            return
        result_images = [im for im in getattr(dlg, "result_images", []) if isinstance(im, Image.Image)]
        if not result_images:
            return
        created = self._create_edited_tasks_from_images(task, result_images)
        self._refresh_queue_numbers()
        self._fit_queue_columns_exact()
        self._update_queue_hint()
        if created:
            new_row = next(
                (r for r in range(self.queue_table.rowCount())
                 if self.queue_table.item(r, QUEUE_COL_FILE).data(Qt.UserRole) == created[0].path),
                current_row
            )
            self.queue_table.selectRow(new_row)
            self.preview_image(created[0].path)
        self.status_bar.showMessage(self._tr("image_edit_applied_single_status"))
        self._log(self._tr_log("log_image_edit_applied", task.display_name, len(result_images)))

    def closeEvent(self, event):
        if self._is_closing:
            event.ignore()
            return
        self._is_closing = True
        self.setEnabled(False)
        try:
            self.settings.setValue("ui/language", self.current_lang)
            self.settings.setValue("ui/theme", self.current_theme)
            self.settings.sync()
            self._request_all_workers_stop()
            # Threads kurz sauber auslaufen lassen
            for w in self._all_workers():
                try:
                    if w and w.isRunning():
                        w.wait(1500)
                except Exception:
                    pass
            self._cleanup_temp_dirs()
            event.accept()
        except Exception:
            event.accept()
