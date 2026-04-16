"""Mixin für MainWindow: undo voice fill and ai revision."""
from ..shared import *
from ..ui_components import *
from ..workers import *
from ..dialogs import *
from ..image_edit import *

class MainWindowUndoVoiceFillAndAiRevisionMixin:
    def set_ai_model_dialog(self):
        model_id, ok = QInputDialog.getText(
            self,
            self._tr("dlg_choose_ai_model"),
            self._tr("dlg_choose_ai_model_label"),
            text=self.ai_model_id
        )
        if not ok:
            return
        self.ai_model_id = model_id.strip()
        self._update_ai_model_ui()
        if self.ai_model_id:
            self.status_bar.showMessage(self._tr("msg_ai_model_set", self.ai_model_id))
        else:
            self.status_bar.showMessage(self._tr("msg_ai_model_id_cleared_auto"))

    def _resolve_faster_whisper_device(self) -> Tuple[str, str]:
        # Wichtig:
        # Whisper immer auf CPU laufen lassen.
        # Sonst kollidiert es mit Kraken-OCR und/oder LM Studio im VRAM.
        return "cpu", "int8"

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
        # Nach Whisper-Änderung UI aktualisieren
        self._sync_ui_after_recs_change(task, keep_row=line_index)
        self._update_queue_row(path)
        # Automatisch auf nächste Zeile springen
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
            # Dialog offen lassen, damit man direkt weiter aufnehmen kann
            if self.voice_record_dialog:
                self.voice_record_dialog.set_recording_state(False)
        else:
            # letzte Zeile erreicht -> Dialog schließen
            if self.voice_record_dialog:
                self.voice_record_dialog.close()
                self.voice_record_dialog = None
        self._set_progress_idle(100)
        self.status_bar.showMessage(self._tr("msg_voice_done"))
        self._log(
            f"Sprachimport abgeschlossen: {os.path.basename(path)} | "
            f"Zeile {line_index + 1} -> {new_text}"
        )

    def on_voice_line_fill_failed(self, path: str, msg: str):
        # Schutz gegen doppelte Ausführung
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
        self._log(f"Sprachimport Fehler: {os.path.basename(path)} -> {msg}")
        QMessageBox.warning(self, self._tr("warn_title"), msg)

    def run_ai_revision(self):
        checked = self._checked_queue_tasks()
        selected = self._selected_queue_tasks()
        # Priorität: Checkmarks vor Auswahl
        target_tasks = checked if checked else selected
        # Wenn mehrere markiert/selektiert sind -> Batch
        if len(target_tasks) > 1:
            items = [it for it in target_tasks if it.status == STATUS_DONE and it.results]
            if not items:
                QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
                return
            self._run_ai_revision_batch(items)
            return
        # Wenn genau ein markierter/selektierter Eintrag existiert -> diesen nehmen
        if len(target_tasks) == 1:
            task = target_tasks[0]
        else:
            # Fallback: aktuelles Vorschau-Element
            task = self._current_task()
            self._persist_live_canvas_bboxes(task)
        if not task or task.status != STATUS_DONE or not task.results:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
            return
        model_id = self._resolve_ai_model_id()
        if not model_id:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_ai_model"))
            return
        if self.ai_worker and self.ai_worker.isRunning():
            return
        _, _, _, recs = task.results
        if not recs:
            return
        task.lm_locked_bboxes = [tuple(rv.bbox) if rv.bbox else None for rv in recs]
        recs_for_ai = self._current_recs_for_ai(task)
        if not recs_for_ai:
            return
        script_mode = self._choose_ai_script_mode()
        if not script_mode:
            return
        self.act_ai_revise.setEnabled(True)
        self.status_bar.showMessage(self._tr("msg_ai_started"))
        self._log(self._tr_log("log_ai_started", os.path.basename(task.path)))
        self.ai_progress_dialog = ProgressStatusDialog(self._tr("dlg_ai_title"), self._tr, self)
        self.ai_progress_dialog.set_status(self._tr("dlg_ai_connecting"))
        self.ai_progress_dialog.cancel_requested.connect(self._cancel_ai_revision)
        self.ai_progress_dialog.show()
        self.ai_worker = AIRevisionWorker(
            path=task.path,
            recs=recs_for_ai,
            lm_model=model_id,
            endpoint=self.ai_endpoint,
            enable_thinking=self.ai_enable_thinking,
            source_kind=task.source_kind,
            script_mode=script_mode,
            temperature=self.ai_temperature,
            top_p=self.ai_top_p,
            top_k=self.ai_top_k,
            presence_penalty=self.ai_presence_penalty,
            repetition_penalty=self.ai_repetition_penalty,
            min_p=self.ai_min_p,
            max_tokens=self.ai_max_tokens,
            tr_func=self._tr,
            parent=self
        )
        self.ai_worker.progress_changed.connect(self.ai_progress_dialog.set_progress)
        self.ai_worker.status_changed.connect(self.ai_progress_dialog.set_status)
        self.ai_worker.status_changed.connect(self._log)
        self.ai_worker.finished_revision.connect(self.on_ai_revision_done)
        self.ai_worker.failed_revision.connect(self.on_ai_revision_failed)
        self.ai_worker.start()

    def run_ai_revision_for_single_line(self, row: int):
        task = self._current_task()
        self._persist_live_canvas_bboxes(task)
        if not task or task.status != STATUS_DONE or not task.results:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
            return
        text, kr_records, im, recs = task.results
        if not (0 <= row < len(recs)):
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_invalid_line"))
            return
        model_id = self._resolve_ai_model_id()
        if not model_id:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_ai_model"))
            return
        if self.ai_worker and self.ai_worker.isRunning():
            return
        script_mode = self._choose_ai_script_mode()
        if not script_mode:
            return
        live_recs = self._current_recs_for_ai(task)
        single_rec = RecordView(
            idx=0,
            text=live_recs[row].text,
            bbox=live_recs[row].bbox
        )
        self._ai_single_line_context = {
            "path": task.path,
            "row": row,
        }
        self.act_ai_revise.setEnabled(False)
        self.status_bar.showMessage(self._tr("msg_ai_single_started", row + 1))
        self._log(self._tr_log("log_ai_single_started", os.path.basename(task.path), row + 1))
        self.ai_progress_dialog = ProgressStatusDialog(self._tr("dlg_ai_single_title"), self._tr, self)
        self.ai_progress_dialog.set_status(self._tr("dlg_ai_single_status", row + 1))
        self.ai_progress_dialog.cancel_requested.connect(self._cancel_ai_revision)
        self.ai_progress_dialog.show()
        self.ai_worker = AIRevisionWorker(
            path=task.path,
            recs=[single_rec],
            lm_model=model_id,
            endpoint=self.ai_endpoint,
            enable_thinking=self.ai_enable_thinking,
            source_kind=task.source_kind,
            script_mode=script_mode,
            temperature=self.ai_temperature,
            top_p=self.ai_top_p,
            top_k=self.ai_top_k,
            presence_penalty=self.ai_presence_penalty,
            repetition_penalty=self.ai_repetition_penalty,
            min_p=self.ai_min_p,
            max_tokens=self.ai_max_tokens,
            tr_func=self._tr,
            parent=self
        )
        self.ai_worker.progress_changed.connect(self.ai_progress_dialog.set_progress)
        self.ai_worker.status_changed.connect(self.ai_progress_dialog.set_status)
        self.ai_worker.status_changed.connect(self._log)
        self.ai_worker.finished_revision.connect(self.on_ai_single_line_revision_done)
        self.ai_worker.failed_revision.connect(self.on_ai_single_line_revision_failed)
        self.ai_worker.start()

    def _run_ai_revision_batch(self, items: List[TaskItem], script_mode: Optional[str] = None):
        model_id = self._resolve_ai_model_id()
        if not model_id:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_ai_model"))
            return
        if hasattr(self, "ai_batch_worker") and self.ai_batch_worker and self.ai_batch_worker.isRunning():
            return
        if not script_mode:
            script_mode = self._choose_ai_script_mode()
            if not script_mode:
                return
        self.act_ai_revise.setEnabled(True)
        self.ai_batch_dialog = ProgressStatusDialog(self._tr("act_ai_revise_all"), self._tr, self)
        self.ai_batch_dialog.set_status(self._tr("dlg_ai_connecting"))
        self.ai_batch_dialog.cancel_requested.connect(self._cancel_ai_batch_revision)
        self.ai_batch_dialog.show()
        self.ai_batch_worker = AIBatchRevisionWorker(
            items=items,
            lm_model=model_id,
            endpoint=self.ai_endpoint,
            enable_thinking=self.ai_enable_thinking,
            script_mode=script_mode,
            temperature=self.ai_temperature,
            top_p=self.ai_top_p,
            top_k=self.ai_top_k,
            presence_penalty=self.ai_presence_penalty,
            repetition_penalty=self.ai_repetition_penalty,
            min_p=self.ai_min_p,
            max_tokens=self.ai_max_tokens,
            tr_func=self._tr,
            parent=self
        )
        self.ai_batch_worker.file_started.connect(self.on_ai_batch_file_started)
        self.ai_batch_worker.status_changed.connect(self.ai_batch_dialog.set_status)
        self.ai_batch_worker.status_changed.connect(self._log)
        self.ai_batch_worker.progress_changed.connect(self.ai_batch_dialog.set_progress)
        self.ai_batch_worker.file_finished.connect(self.on_ai_batch_file_done)
        self.ai_batch_worker.file_failed.connect(self.on_ai_batch_file_failed)
        self.ai_batch_worker.finished_batch.connect(self.on_ai_batch_finished)
        self.ai_batch_worker.start()

    def _cancel_ai_revision(self):
        if self.ai_worker and self.ai_worker.isRunning():
            self.ai_worker.cancel()

    def on_ai_revision_done(self, path: str, revised_lines: list):
        task = next((i for i in self.queue_items if i.path == path), None)
        if not task or not task.results:
            self.act_ai_revise.setEnabled(True)
            if hasattr(self, "ai_progress_dialog") and self.ai_progress_dialog:
                self.ai_progress_dialog.close()
                self.ai_progress_dialog = None
            return
        text, kr_records, im, recs = task.results
        revised_lines = [str(x).strip() for x in revised_lines]
        self._log(
            f"KI Rückgabe für {os.path.basename(path)}: {len(revised_lines)} Zeilen, OCR hatte {len(recs)} Zeilen")
        if len(revised_lines) < len(recs):
            revised_lines.extend([recs[i].text for i in range(len(revised_lines), len(recs))])
        elif len(revised_lines) > len(recs):
            revised_lines = revised_lines[:len(recs)]
        self._log(self._tr_log("log_ai_batch_debug_old_first", recs[0].text if recs else "<leer>"))
        self._log(self._tr_log("log_ai_batch_debug_new_first", revised_lines[0] if revised_lines else "<leer>"))
        self._log(self._tr_log("log_ai_batch_debug_all", revised_lines))
        self._push_undo(task)
        # WICHTIG:
        # Texte ersetzen, aber die AKTUELLEN Boxen aus task.results behalten.
        new_recs = [
            RecordView(i, revised_lines[i], recs[i].bbox)
            for i in range(len(recs))
        ]
        task.results = (
            "\n".join(rv.text for rv in new_recs).strip(),
            kr_records,
            im,
            new_recs
        )
        task.edited = True
        cur = self._current_task()
        if cur and cur.path == path:
            keep_row = self.list_lines.currentRow()
            if keep_row < 0:
                keep_row = 0 if new_recs else None
            self._sync_ui_after_recs_change(task, keep_row=keep_row)
        else:
            self._update_queue_row(path)
        self.act_ai_revise.setEnabled(True)
        self.status_bar.showMessage(self._tr("msg_ai_done"))
        self._log(self._tr_log("log_ai_done", os.path.basename(path)))
        if hasattr(self, "ai_progress_dialog") and self.ai_progress_dialog:
            self.ai_progress_dialog.close()
            self.ai_progress_dialog = None

    def on_ai_single_line_revision_done(self, path: str, revised_lines: list):
        ctx = self._ai_single_line_context or {}
        self._ai_single_line_context = None
        task = next((i for i in self.queue_items if i.path == path), None)
        if not task or not task.results:
            self.act_ai_revise.setEnabled(True)
            if self.ai_progress_dialog:
                self.ai_progress_dialog.close()
                self.ai_progress_dialog = None
            return
        row = int(ctx.get("row", -1))
        text, kr_records, im, recs = task.results
        if not (0 <= row < len(recs)):
            self.act_ai_revise.setEnabled(True)
            if self.ai_progress_dialog:
                self.ai_progress_dialog.close()
                self.ai_progress_dialog = None
            return
        new_text = ""
        if revised_lines:
            new_text = str(revised_lines[0]).strip()
        if not new_text:
            new_text = recs[row].text
        self._push_undo(task)
        new_recs = [
            RecordView(i, recs[i].text, recs[i].bbox)
            for i in range(len(recs))
        ]
        new_recs[row].text = new_text
        task.results = (
            "\n".join(rv.text for rv in new_recs).strip(),
            kr_records,
            im,
            new_recs
        )
        task.edited = True
        cur = self._current_task()
        if cur and cur.path == path:
            self._sync_ui_after_recs_change(task, keep_row=row)
        else:
            self._update_queue_row(path)
        self.act_ai_revise.setEnabled(True)
        self.status_bar.showMessage(self._tr("msg_ai_single_done", row + 1))
        self._log(self._tr_log("log_ai_single_done", os.path.basename(path), row + 1))
        self._close_ai_progress_dialog()

    def on_ai_single_line_revision_failed(self, path: str, msg: str):
        self._ai_single_line_context = None
        self.act_ai_revise.setEnabled(True)
        if "abgebrochen" in str(msg).lower():
            self.status_bar.showMessage(self._tr("msg_ai_single_cancelled"))
            self._log(self._tr_log("log_ai_single_cancelled", os.path.basename(path)))
        else:
            self.status_bar.showMessage(self._tr("msg_ai_single_failed"))
            self._log(self._tr_log("log_ai_single_failed", os.path.basename(path), msg))
            QMessageBox.warning(self, self._tr("warn_title"), msg)
        self._close_ai_progress_dialog()

    def on_ai_revision_failed(self, path: str, msg: str):
        self.act_ai_revise.setEnabled(True)
        if "abgebrochen" in str(msg).lower():
            self.status_bar.showMessage(self._tr("msg_ai_cancelled_short"))
            self._log(f"Überarbeitung abgebrochen: {os.path.basename(path)}")
        else:
            self.status_bar.showMessage(self._tr("msg_ai_failed_short"))
            self._log(self._tr_log("log_ai_error", os.path.basename(path), msg))
            QMessageBox.warning(self, self._tr("warn_title"), msg)
        if hasattr(self, "ai_progress_dialog") and self.ai_progress_dialog:
            self.ai_progress_dialog.close()
            self.ai_progress_dialog = None

    def _auto_select_best_device(self):
        caps = self._gpu_capabilities()
        # Priorität: CUDA (echtes CUDA build) > ROCm/HIP > MPS > CPU
        for dev in ("cuda", "rocm", "mps", "cpu"):
            ok, _ = caps.get(dev, (False, ""))
            if ok:
                self.device_str = dev
                break
