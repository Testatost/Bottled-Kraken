"""Mixin für MainWindow: voice input selection and ai selected lines."""
from ..shared import *
from ..ui_components import *
from ..workers import *
from ..dialogs import *
from ..image_edit import *

class MainWindowVoiceInputSelectionAndAiSelectedLinesMixin:
    def _cancel_voice_record_dialog(self):
        if self.voice_worker and self.voice_worker.isRunning():
            self.voice_worker.cancel()

    def _audio_backend_priority(self, hostapi_name: str) -> int:
        n = (hostapi_name or "").lower()
        # Linux
        if "pipewire" in n:
            return 500
        if "pulse" in n or "pulseaudio" in n:
            return 450
        if "alsa" in n:
            return 350
        if "jack" in n:
            return 250
        # Windows
        if "wasapi" in n:
            return 400
        if "directsound" in n:
            return 300
        if "mme" in n:
            return 200
        if "wdm-ks" in n:
            return 100
        # macOS
        if "core audio" in n:
            return 450
        return 0

    def _normalize_audio_device_name(self, name: str) -> str:
        txt = (name or "").strip()
        # Backend-Suffixe entfernen
        txt = re.sub(
            r"\s+\((MME|Windows DirectSound|Windows WASAPI|Windows WDM-KS)\)\s*$",
            "",
            txt,
            flags=re.IGNORECASE
        )
        # typische Dopplungen säubern
        txt = re.sub(r"\s+", " ", txt).strip()
        # System-Default hübscher anzeigen
        if txt.lower() in ("microsoft soundmapper - input", "primärer soundaufnahmetreiber"):
            return self._tr("audio_device_default_mic")
        return txt

    def _get_input_audio_devices(self) -> List[dict]:
        out = []
        try:
            devices = sd.query_devices()
        except Exception:
            return out
        try:
            default_in = sd.default.device[0]
        except Exception:
            default_in = None
        grouped: Dict[str, dict] = {}
        for i, dev in enumerate(devices):
            try:
                max_in = int(dev.get("max_input_channels", 0))
            except Exception:
                max_in = 0
            if max_in <= 0:
                continue
            raw_name = str(dev.get("name", self._tr("audio_device_generic", i))).strip()
            hostapi_idx = dev.get("hostapi", None)
            hostapi_name = ""
            try:
                if hostapi_idx is not None:
                    hostapi_name = str(sd.query_hostapis(hostapi_idx).get("name", "")).strip()
            except Exception:
                pass
            clean_name = self._normalize_audio_device_name(raw_name)
            score = self._audio_backend_priority(hostapi_name)
            if i == default_in:
                score += 10000
            candidate = {
                "index": i,
                "label": clean_name,
                "hostapi": hostapi_name,
                "score": score,
                "is_default": (i == default_in),
                "default_samplerate": int(float(dev.get("default_samplerate", VOICE_SAMPLE_RATE))),
                "max_input_channels": max_in,
            }
            # pro Hauptgerät nur die beste Variante behalten
            old = grouped.get(clean_name)
            if old is None or candidate["score"] > old["score"]:
                grouped[clean_name] = candidate
        out = list(grouped.values())
        out.sort(
            key=lambda d: (
                0 if d["is_default"] else 1,
                -d["score"],
                d["label"].lower()
            )
        )
        return out

    def _selected_line_rows(self) -> List[int]:
        return self.list_lines.selected_line_rows()

    def _choose_ai_script_mode(self) -> Optional[str]:
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle(self._tr("dlg_ai_script_title"))
        msg.setText(self._tr("dlg_ai_script_text"))
        msg.setInformativeText(
            "• " + self._tr("dlg_ai_script_hint_print") + "\n"
            + "• " + self._tr("dlg_ai_script_hint_handwriting") + "\n"
            + "• " + self._tr("dlg_ai_script_hint_mixed")
        )
        btn_print = msg.addButton(self._tr("btn_ai_script_print"), QMessageBox.AcceptRole)
        btn_hand = msg.addButton(self._tr("btn_ai_script_handwriting"), QMessageBox.AcceptRole)
        btn_mixed = msg.addButton(self._tr("btn_ai_script_mixed"), QMessageBox.AcceptRole)
        msg.addButton(self._tr("btn_cancel"), QMessageBox.RejectRole)
        msg.exec()
        clicked = msg.clickedButton()
        if clicked == btn_print:
            return AI_SCRIPT_PRINT
        if clicked == btn_hand:
            return AI_SCRIPT_HANDWRITING
        if clicked == btn_mixed:
            return AI_SCRIPT_MIXED
        return None

    def run_ai_revision_for_selected_lines(self):
        task = self._current_task()
        self._persist_live_canvas_bboxes(task)
        if not task or task.status != STATUS_DONE or not task.results:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
            return
        text, kr_records, im, recs = task.results
        rows = self._selected_line_rows()
        if not rows:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_select_multiple_lines_first"))
            return
        if len(rows) == 1:
            self.run_ai_revision_for_single_line(rows[0])
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
        selected_recs = [
            RecordView(
                idx=i,
                text=live_recs[row].text,
                bbox=live_recs[row].bbox
            )
            for i, row in enumerate(rows)
        ]
        self._ai_multi_line_context = {
            "path": task.path,
            "rows": rows,
        }
        self.act_ai_revise.setEnabled(False)
        self.status_bar.showMessage(self._tr("msg_ai_selected_lines_started", len(rows)))
        self._log(
            self._tr_log("log_ai_multi_started", os.path.basename(task.path), ", ".join(str(r + 1) for r in rows))
        )
        self.ai_progress_dialog = ProgressStatusDialog(self._tr("dlg_ai_multi_title"), self._tr, self)
        self.ai_progress_dialog.set_status(
            self._tr("dlg_ai_multi_status", len(rows))
        )
        self.ai_progress_dialog.cancel_requested.connect(self._cancel_ai_revision)
        self.ai_progress_dialog.show()
        self.ai_worker = AIRevisionWorker(
            path=task.path,
            recs=selected_recs,
            lm_model=model_id,
            endpoint=self.ai_endpoint,
            enable_thinking=self.ai_enable_thinking,
            source_kind=task.source_kind,
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
        self.ai_worker.finished_revision.connect(self.on_ai_selected_lines_revision_done)
        self.ai_worker.failed_revision.connect(self.on_ai_selected_lines_revision_failed)
        self.ai_worker.start()

    def on_ai_selected_lines_revision_done(self, path: str, revised_lines: list):
        ctx = getattr(self, "_ai_multi_line_context", None) or {}
        self._ai_multi_line_context = None
        task = next((i for i in self.queue_items if i.path == path), None)
        if not task or not task.results:
            self.act_ai_revise.setEnabled(True)
            if self.ai_progress_dialog:
                self.ai_progress_dialog.close()
                self.ai_progress_dialog = None
            return
        rows = list(ctx.get("rows", []))
        text, kr_records, im, recs = task.results
        if not rows:
            self.act_ai_revise.setEnabled(True)
            if self.ai_progress_dialog:
                self.ai_progress_dialog.close()
                self.ai_progress_dialog = None
            return
        revised_lines = [str(x).strip() for x in revised_lines]
        if len(revised_lines) < len(rows):
            for i in range(len(revised_lines), len(rows)):
                revised_lines.append(recs[rows[i]].text)
        elif len(revised_lines) > len(rows):
            revised_lines = revised_lines[:len(rows)]
        self._push_undo(task)
        new_recs = [
            RecordView(i, recs[i].text, recs[i].bbox)
            for i in range(len(recs))
        ]
        for local_idx, row in enumerate(rows):
            if 0 <= row < len(new_recs):
                new_text = revised_lines[local_idx].strip()
                if new_text:
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
            self._sync_ui_after_recs_change(task, keep_row=rows[0] if rows else 0)
            self.list_lines.blockSignals(True)
            self.list_lines.clearSelection()
            for row in rows:
                if 0 <= row < self.list_lines.count():
                    it = self.list_lines.row_item(row)
                    if it:
                        it.setSelected(True)
            if rows:
                self.list_lines.setCurrentRow(rows[0])
            self.list_lines.blockSignals(False)
        else:
            self._update_queue_row(path)
        self.act_ai_revise.setEnabled(True)
        self.status_bar.showMessage(self._tr("msg_ai_multi_done", len(rows)))
        self._log(
            self._tr_log("log_ai_multi_done", os.path.basename(path), ", ".join(str(r + 1) for r in rows))
        )
        self._close_ai_progress_dialog()

    def on_ai_selected_lines_revision_failed(self, path: str, msg: str):
        self._ai_multi_line_context = None
        self.act_ai_revise.setEnabled(True)
        if "abgebrochen" in str(msg).lower():
            self.status_bar.showMessage(self._tr("msg_ai_multi_cancelled"))
            self._log(self._tr_log("log_ai_multi_cancelled", os.path.basename(path)))
        else:
            self.status_bar.showMessage(self._tr("msg_ai_multi_failed"))
            self._log(self._tr_log("log_ai_multi_failed", os.path.basename(path), msg))
            QMessageBox.warning(self, self._tr("warn_title"), msg)
        self._close_ai_progress_dialog()

    def _cleanup_temp_dirs(self):
        for d in list(self.temp_dirs_created):
            try:
                if os.path.isdir(d):
                    shutil.rmtree(d, ignore_errors=True)
            except Exception:
                pass
        self.temp_dirs_created.clear()

    def eventFilter(self, obj, event):
        if getattr(self, "_is_closing", False):
            return False
        try:
            et = event.type()
            if et in (QEvent.ShortcutOverride, QEvent.KeyPress):
                if event.matches(QKeySequence.Paste):
                    if QApplication.activeWindow() is not self:
                        return super().eventFilter(obj, event)
                    fw = QApplication.focusWidget()
                    if isinstance(fw, (QLineEdit, QPlainTextEdit, QTextEdit)):
                        return super().eventFilter(obj, event)
                    self.paste_files_from_clipboard()
                    event.accept()
                    return True
        except Exception:
            pass
        return super().eventFilter(obj, event)

    def _is_local_port_open(self, host: str, port: int, timeout: float = 0.12) -> bool:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except Exception:
            return False

    def _reorder_lines_keep_box_slots(self, task: TaskItem, order: List[int], keep_row: Optional[int] = None):
        if not task or not task.results:
            return
        text, kr_records, im, recs = task.results
        n = len(recs)
        if len(order) != n:
            return
        try:
            order = [int(i) for i in order]
        except Exception:
            return
        if sorted(order) != list(range(n)):
            return
        self._push_undo(task)
        old_recs = list(recs)
        # GANZE Records verschieben, nicht nur Texte
        new_recs = [
            RecordView(i, old_recs[src_idx].text, old_recs[src_idx].bbox)
            for i, src_idx in enumerate(order)
        ]
        task.edited = True
        task.results = (text, kr_records, im, new_recs)
        self._sync_ui_after_recs_change(task, keep_row=keep_row)

    def _get_active_ai_model_display(self) -> str:
        return (self.ai_model_id or "").strip() or "-"

    def _update_ai_model_ui(self):
        display = self._get_active_ai_model_display()
        mode_label = self._current_ai_mode_label()
        base_url = self.ai_base_url or "-"
        if hasattr(self, "btn_ai_model"):
            self.btn_ai_model.setText(self._tr("btn_ai_model_value", display))
        if hasattr(self, "act_llm_status"):
            self.act_llm_status.setText(self._tr("llm_status_value", display))
        if hasattr(self, "act_lm_status"):
            self.act_lm_status.setText(self._tr("lm_status_model_value", display))
        if hasattr(self, "act_lm_mode"):
            self.act_lm_mode.setText(self._tr("lm_mode_value", mode_label))
        if hasattr(self, "act_lm_base_url"):
            self.act_lm_base_url.setText(self._tr("lm_server_value", base_url))

    def _process_ui(self):
        QCoreApplication.processEvents()

    def _fetch_loaded_llm_models(self, force: bool = False) -> List[str]:
        if self.ai_mode == "manual" and self.ai_manual_base_url:
            base_url = self._normalize_ai_base_url(self.ai_manual_base_url)
            if not base_url:
                self.ai_base_url = None
                self.ai_available_models = []
                return []
            self.ai_base_url = base_url
            self.ai_endpoint = base_url + "/chat/completions"
        else:
            base_url, _ = self._detect_local_openai_server(force=force)
            self.ai_mode = "auto"
            if base_url:
                self.ai_base_url = base_url
                self.ai_endpoint = base_url + "/chat/completions"
            else:
                self.ai_base_url = None
        if not base_url:
            self.ai_available_models = []
            return []
        models, _ = self._fetch_models_from_base_url(base_url, timeout=0.6)
        self.ai_available_models = models
        return models
