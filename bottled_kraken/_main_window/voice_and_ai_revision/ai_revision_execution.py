from bottled_kraken.common import (
    List,
    Optional,
    QMessageBox,
    RecordView,
    TaskItem,
    os,
)
from bottled_kraken.workers import (
    AIBatchRevisionWorker,
    AIRevisionWorker,
)
from bottled_kraken.dialogs import (
    ProgressStatusDialog,
)
class MainWindowAiRevisionExecutionMixin:
        def run_ai_revision(self):
            target_tasks = self._ai_revision_queue_targets()
            if target_tasks:
                items = self._ai_revision_ready_tasks(target_tasks)
                if not items:
                    QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
                    return
                self._run_ai_revision_batch(items)
                return
            task = self._current_task()
            self._persist_live_canvas_bboxes(task)
            if not self._ai_revision_task_has_revisable_results(task):
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
            self._prepare_task_for_ai_revision(task)
            recs_for_ai = self._current_recs_for_ai(task)
            if not recs_for_ai:
                return
            script_mode = self._choose_ai_script_mode()
            if not script_mode:
                return
            self.act_ai_revise.setEnabled(False)
            try:
                if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
                    self.btn_ai_revise_bottom.setEnabled(False)
            except Exception:
                pass
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
                max_tokens=(self._lm_token_limit("all_lines") if hasattr(self, "_lm_token_limit") else self.ai_max_tokens),
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
            if not self._ai_revision_task_has_revisable_results(task):
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
                idx=row,
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
                max_tokens=(self._lm_token_limit("current_line") if hasattr(self, "_lm_token_limit") else self.ai_max_tokens),
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
            items = self._ai_revision_ready_tasks(items)
            if not items:
                QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
                return
            model_id = self._resolve_ai_model_id()
            if not model_id:
                QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_ai_model"))
                return
            if hasattr(self, "ai_batch_worker") and self.ai_batch_worker and self.ai_batch_worker.isRunning():
                return
            if self.ai_worker and self.ai_worker.isRunning():
                return
            if not script_mode:
                script_mode = self._choose_ai_script_mode()
                if not script_mode:
                    return
            for task in items:
                self._prepare_task_for_ai_revision(task)
            self.act_ai_revise.setEnabled(False)
            try:
                if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
                    self.btn_ai_revise_bottom.setEnabled(False)
            except Exception:
                pass
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
                max_tokens=(self._lm_token_limit("all_lines") if hasattr(self, "_lm_token_limit") else self.ai_max_tokens),
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
            self._log(self._tr_log("log_ai_batch_debug_return", os.path.basename(path), len(revised_lines), len(recs)))
            if len(revised_lines) < len(recs):
                revised_lines.extend([recs[i].text for i in range(len(revised_lines), len(recs))])
            elif len(revised_lines) > len(recs):
                revised_lines = revised_lines[:len(recs)]
            self._log(self._tr_log("log_ai_batch_debug_old_first", recs[0].text if recs else self._tr("empty_text_marker")))
            self._log(self._tr_log("log_ai_batch_debug_new_first", revised_lines[0] if revised_lines else self._tr("empty_text_marker")))
            self._log(self._tr_log("log_ai_batch_debug_all", revised_lines))
            self._push_undo(task)
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
