"""Mixin für MainWindow: import lines and ocr batch."""
from ...shared import *
from ...ui_components import *
from ...workers import *
from ...dialogs import *
from ...image_edit import *

class MainWindowOcrResultsMixin:
        def on_file_started(self, path):
            item = next((i for i in self.queue_items if i.path == path), None)
            if item:
                item.status = STATUS_PROCESSING
                self._update_queue_row(path)
                self._log(self._tr_log("log_file_started", os.path.basename(path)))

        def on_file_done(self, path, text, kr_records, im, recs):
            item = next((i for i in self.queue_items if i.path == path), None)
            if item:
                # Normales OCR-Ergebnis direkt übernehmen
                text = "\n".join(rv.text for rv in recs).strip()
                item.status = STATUS_DONE
                # FIX8.54: Nur frisch erzeugte Kraken-OCR-Ergebnisse dürfen automatisch
                # in der Box-Höhe/-Breite angepasst werden. Projekt-Ladevorgänge setzen
                # dieses Flag nicht; dadurch werden gespeicherte Boxen nicht nachträglich
                # verkleinert.
                try:
                    item._bk_fresh_kraken_ocr_result = True
                    item._bk_fix52_default_box_scale_applied = False
                    item._bk_fix53_default_box_scale_applied = False
                except Exception:
                    pass
                # Speicherfix für große Batches: keine komplette PIL-Seite und keine rohen Kraken-Records
                # pro Queue-Eintrag behalten. Bilddaten werden bei Preview/Export aus item.path nachgeladen.
                item.results = (text, [], None, recs)
                item.edited = False
                item.undo_stack.clear()
                item.redo_stack.clear()
                self._update_queue_row(path)
                # nur nach erfolgreichem Anwenden leeren
                item.preset_bboxes = []
                if self.queue_table.currentRow() >= 0:
                    cur_path = self.queue_table.item(self.queue_table.currentRow(), QUEUE_COL_FILE).data(Qt.UserRole)
                    if cur_path == path:
                        self.load_results(path)
                        if self.list_lines.count() > 0:
                            self.list_lines.setCurrentRow(0)
                            self.list_lines.setFocus()
                            self.canvas.select_idx(0)
                self._log(self._tr_log("log_file_done", os.path.basename(path), len(recs)))

        def on_file_error(self, path, msg):
            item = next((i for i in self.queue_items if i.path == path), None)
            if item:
                item.status = STATUS_ERROR
                self._update_queue_row(path)
                self._log(self._tr_log("log_file_error", os.path.basename(path), msg))

        def on_batch_finished(self):
            cancelled = False
            try:
                cancelled = bool(getattr(self, "_ocr_cancel_requested", False)) or bool(
                    getattr(self, "worker", None) is not None and self.worker.isInterruptionRequested()
                ) or bool(getattr(getattr(self, "worker", None), "_bk_cancelled_by_user", False))
            except Exception:
                cancelled = bool(getattr(self, "_ocr_cancel_requested", False))

            if cancelled:
                if self.worker:
                    try:
                        self.worker.deleteLater()
                    except Exception:
                        pass
                    self.worker = None
                self._bk_reset_ocr_cancel_state(reset_processing=True, message=self._tr("msg_ocr_cancelled") if hasattr(self, "_tr") else "OCR abgebrochen.")
                try:
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except Exception:
                    pass
                return

            self.act_play.setEnabled(True)
            self.act_stop.setEnabled(False)
            self.status_bar.showMessage(self._tr("msg_finished"))
            self.progress_bar.setValue(100)
            if self.worker:
                try:
                    self.worker.deleteLater()
                except Exception:
                    pass
                self.worker = None
            try:
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass

        def on_failed(self, msg):
            msg_text = str(msg or "")
            cancelled = bool(getattr(self, "_ocr_cancel_requested", False)) or any(
                token in msg_text.lower() for token in ("abbruch", "abgebrochen", "cancel", "cancelled", "canceled", "annul")
            )
            if not cancelled:
                QMessageBox.critical(self, self._tr("err_title"), msg)
            if self.worker:
                try:
                    self.worker.deleteLater()
                except Exception:
                    pass
                self.worker = None
            if cancelled:
                self._bk_reset_ocr_cancel_state(reset_processing=True, message=self._tr("msg_ocr_cancelled") if hasattr(self, "_tr") else "OCR abgebrochen.")
            else:
                self.act_play.setEnabled(True)
                self.act_stop.setEnabled(False)
                self._set_progress_idle(0)
            try:
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass

        def _update_queue_row(self, path):
            for row in range(self.queue_table.rowCount()):
                item0 = self.queue_table.item(row, QUEUE_COL_FILE)
                if item0 and item0.data(Qt.UserRole) == path:
                    status_item = self.queue_table.item(row, QUEUE_COL_STATUS)
                    task = next((i for i in self.queue_items if i.path == path), None)
                    if task and status_item:
                        status_enum = task.status
                        status_icon = STATUS_ICONS[status_enum]
                        status_key = {
                            STATUS_WAITING: "status_waiting",
                            STATUS_PROCESSING: "status_processing",
                            STATUS_DONE: "status_done",
                            STATUS_ERROR: "status_error",
                            STATUS_AI_PROCESSING: "status_ai_processing",
                            STATUS_EXPORTING: "status_exporting",
                            STATUS_VOICE_RECORDING: "status_voice_recording",
                        }[status_enum]
                        status_item.setText(f"{status_icon} {self._tr(status_key)}")
                        if status_enum == STATUS_DONE:
                            status_item.setForeground(QBrush(QColor("green")))
                        elif status_enum == STATUS_VOICE_RECORDING:
                            status_item.setForeground(QBrush(QColor(180, 0, 180)))
                        elif status_enum == STATUS_ERROR:
                            status_item.setForeground(QBrush(QColor("red")))
                        elif status_enum == STATUS_AI_PROCESSING:
                            status_item.setForeground(QBrush(QColor(128, 0, 128)))
                        elif status_enum == STATUS_EXPORTING:
                            status_item.setForeground(QBrush(QColor(180, 120, 0)))
                        else:
                            status_item.setForeground(QBrush(QColor("blue")))
                    break

        def _current_task(self) -> Optional[TaskItem]:
            if self.queue_table.currentRow() < 0:
                return None
            path = self.queue_table.item(self.queue_table.currentRow(), QUEUE_COL_FILE).data(Qt.UserRole)
            return next((i for i in self.queue_items if i.path == path), None)

        def _update_task_preset_bboxes(self, task: TaskItem):
            if not task or not task.results:
                task.preset_bboxes = []
                return
            _, _, _, recs = task.results
            task.preset_bboxes = [rv.bbox for rv in recs]

        def _current_recs_for_ai(self, task: TaskItem) -> List[RecordView]:
            if not task or not task.results:
                return []
            # Sicherheitshalber die aktuell sichtbaren Canvas-Boxen zuerst ins Task-Modell ziehen
            self._persist_live_canvas_bboxes(task)
            _, _, _, recs = task.results
            out = []
            for i, rv in enumerate(recs):
                out.append(
                    RecordView(
                        i,
                        rv.text,
                        tuple(rv.bbox) if rv.bbox else None
                    )
                )
            return out
