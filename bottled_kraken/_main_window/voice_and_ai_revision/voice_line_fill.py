from bottled_kraken.common import (
    QMessageBox,
    RecordView,
    STATUS_DONE,
    STATUS_ERROR,
    os,
)
from bottled_kraken.dialogs import (
    VoiceRecordDialog,
)
class MainWindowVoiceLineFillMixin:
        def run_voice_line_fill(self):
            task = self._current_task()
            self._persist_live_canvas_bboxes(task)
            if not task or task.status != STATUS_DONE or not task.results:
                QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_voice_need_done"))
                return
            current_row = self.list_lines.currentRow()
            if current_row < 0:
                QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_select_line_first"))
                return
            _, _, _, recs = task.results
            if not (0 <= current_row < len(recs)):
                QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_selected_line_invalid"))
                return
            if self.voice_worker and self.voice_worker.isRunning():
                return
            if not self.whisper_model_path or not os.path.isdir(self.whisper_model_path):
                QMessageBox.warning(
                    self,
                    self._tr("warn_title"),
                    self._tr("warn_whisper_model_not_loaded")
                )
                return
            if self.whisper_selected_input_device is None:
                devices = self._get_input_audio_devices()
                if devices:
                    self.whisper_selected_input_device = devices[0]["index"]
                    self.whisper_selected_input_device_label = devices[0]["label"]
                    self._update_whisper_menu_status()
                else:
                    QMessageBox.warning(
                        self,
                        self._tr("warn_title"),
                        self._tr("warn_no_microphone_available")
                    )
                    return
            if self.voice_record_dialog is not None:
                try:
                    self.voice_record_dialog.close()
                except Exception:
                    pass
                self.voice_record_dialog = None
            self.voice_record_dialog = VoiceRecordDialog(self._tr, self)
            self.voice_record_dialog.start_requested.connect(self._start_voice_line_fill)
            self.voice_record_dialog.stop_requested.connect(self.stop_voice_line_fill)
            self.voice_record_dialog.cancel_requested.connect(self._cancel_voice_record_dialog)
            self.voice_record_dialog.show()
        def on_voice_progress_changed(self, value: int):
            self._set_progress_idle(value)
        def on_voice_status_changed(self, text: str):
            self.status_bar.showMessage(text)
            if text.startswith("Erkannte Sprache:"):
                self._log(text)
        def stop_voice_line_fill(self):
            if self.voice_worker and self.voice_worker.isRunning():
                self.status_bar.showMessage(self._tr("msg_voice_stopped"))
                self._log(self._tr_log("log_voice_stopping"))
                if self.voice_record_dialog:
                    self.voice_record_dialog._recording = False
                    self.voice_record_dialog._processing = True
                    self.voice_record_dialog.btn_toggle.setText(self._tr("voice_record_start"))
                    self.voice_record_dialog.lbl_info.setText(self._tr("voice_record_processing"))
                    self.voice_record_dialog._keep_start_button_primary()
                self._set_progress_idle(0)
                self.voice_worker.stop()
        def on_voice_line_fill_done(self, path: str, line_index: int, new_text: str):
            task = next((i for i in self.queue_items if i.path == path), None)
            self.voice_worker = None
            if not task or not task.results:
                if self.voice_record_dialog:
                    self.voice_record_dialog.close()
                    self.voice_record_dialog = None
                return
            text, kr_records, im, recs = task.results
            if not (0 <= line_index < len(recs)):
                if self.voice_record_dialog:
                    self.voice_record_dialog.close()
                    self.voice_record_dialog = None
                return
            self._push_undo(task)
            new_recs = [
                RecordView(i, recs[i].text, recs[i].bbox)
                for i in range(len(recs))
            ]
            new_recs[line_index].text = str(new_text).strip()
            task.results = (
                "\n".join(rv.text for rv in new_recs).strip(),
                kr_records,
                im,
                new_recs
            )
            task.edited = True
            task.status = STATUS_DONE
            self._sync_ui_after_recs_change(task, keep_row=line_index)
            self._update_queue_row(path)
            next_row = line_index + 1
            if 0 <= next_row < len(new_recs):
                self.list_lines.blockSignals(True)
                self.list_lines.clearSelection()
                self.list_lines.setCurrentRow(next_row)
                next_item = self.list_lines.row_item(next_row)
                if next_item:
                    next_item.setSelected(True)
                self.list_lines.blockSignals(False)
                self.canvas.select_indices([next_row], center=True)
                self.list_lines.setFocus()
                if self.voice_record_dialog:
                    self.voice_record_dialog.set_recording_state(False)
            else:
                if self.voice_record_dialog:
                    self.voice_record_dialog.close()
                    self.voice_record_dialog = None
            self._set_progress_idle(100)
            self.status_bar.showMessage(self._tr("msg_voice_done"))
            self._log(
                self._tr_log(
                    "log_voice_import_done",
                    os.path.basename(path),
                    line_index + 1,
                    new_text,
                )
            )
        def on_voice_line_fill_failed(self, path: str, msg: str):
            if self.voice_worker is None:
                return
            task = next((i for i in self.queue_items if i.path == path), None)
            self.voice_worker = None
            if task:
                task.status = STATUS_DONE if task.results else STATUS_ERROR
                self._update_queue_row(path)
            if self.voice_record_dialog:
                self.voice_record_dialog.close()
                self.voice_record_dialog = None
            self._set_progress_idle(0)
            self.status_bar.showMessage(self._tr("msg_voice_cancelled"))
            self._log(self._tr_log("log_voice_import_error", os.path.basename(path), msg))
            QMessageBox.warning(self, self._tr("warn_title"), msg)
