"""Mixin für MainWindow: whisper setup and model selection."""
from ..shared import *
from ..ui_components import *
from ..workers import *
from ..dialogs import *
from ..image_edit import *

class MainWindowWhisperSetupAndModelSelectionMixin:
    def _workers_still_running(self) -> bool:
        for w in self._all_workers():
            try:
                if w and w.isRunning():
                    return True
            except Exception:
                pass
        return False

    def _check_shutdown_complete(self):
        if not self._workers_still_running():
            self._shutdown_poll_timer.stop()
            self._shutdown_force_timer.stop()
            self._cleanup_temp_dirs()
            self._final_close()

    def _final_close(self):
        try:
            if self.voice_record_dialog:
                self.voice_record_dialog.close()
                self.voice_record_dialog = None
        except Exception:
            pass
        try:
            if self.ai_progress_dialog:
                self.ai_progress_dialog.close()
                self.ai_progress_dialog = None
        except Exception:
            pass
        try:
            if self.ai_batch_dialog:
                self.ai_batch_dialog.close()
                self.ai_batch_dialog = None
        except Exception:
            pass
        try:
            if self.export_dialog:
                self.export_dialog.close()
                self.export_dialog = None
        except Exception:
            pass
        try:
            if self.pdf_progress_dlg:
                self.pdf_progress_dlg.close()
                self.pdf_progress_dlg = None
        except Exception:
            pass
        try:
            if self.hf_download_dialog:
                self.hf_download_dialog.close()
                self.hf_download_dialog = None
        except Exception:
            pass
        self._shutdown_poll_timer.stop()
        self._shutdown_force_timer.stop()
        # Fenster wirklich schließen, ohne self.close() erneut auszulösen
        super().close()

    def _force_kill_process(self):
        # Kein harter Kill mehr.
        # Nur Diagnose, falls doch noch etwas hängt.
        running = []
        for w in self._all_workers():
            try:
                if w and w.isRunning():
                    running.append(type(w).__name__)
            except Exception:
                pass
        if running:
            print("Shutdown wartet noch auf:", ", ".join(running))
        # Letzter Versuch: regulär quitten
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def _normalize_whisper_base_dir(self, raw: str) -> str:
        return os.path.abspath((raw or "").strip()) if (raw or "").strip() else ""

    def _scan_whisper_models(self) -> List[str]:
        self.whisper_available_models = []
        base = self._normalize_whisper_base_dir(self.whisper_models_base_dir)
        if not base or not os.path.isdir(base):
            return []
        out = []
        # Fall A: Basisordner selbst ist schon ein Modellordner
        if os.path.isfile(os.path.join(base, "model.bin")):
            out.append(base)
        # Fall B: Unterordner enthalten Modelle
        try:
            for name in sorted(os.listdir(base)):
                full = os.path.join(base, name)
                if os.path.isdir(full) and os.path.isfile(os.path.join(full, "model.bin")):
                    out.append(full)
        except Exception:
            pass
        self.whisper_available_models = out
        return out

    def _find_existing_whisper_large_v3_model(self) -> str:
        candidates = []
        seen = set()
        for raw_base in [self.whisper_models_base_dir, self._default_whisper_base_dir()]:
            base = self._normalize_whisper_base_dir(raw_base)
            if not base or base in seen:
                continue
            seen.add(base)
            candidates.append(base)
        for base in candidates:
            if not os.path.isdir(base):
                continue
            # Fall A: Basisordner ist selbst schon das Modell
            if (
                    os.path.basename(base).lower() == "faster-whisper-large-v3"
                    and os.path.isfile(os.path.join(base, "model.bin"))
            ):
                return base
            # Fall B: klassischer Unterordner
            direct = os.path.join(base, "faster-whisper-large-v3")
            if os.path.isdir(direct) and os.path.isfile(os.path.join(direct, "model.bin")):
                return direct
            # Fall C: allgemein Unterordner durchsuchen
            try:
                for name in os.listdir(base):
                    full = os.path.join(base, name)
                    if (
                            os.path.isdir(full)
                            and name.lower() == "faster-whisper-large-v3"
                            and os.path.isfile(os.path.join(full, "model.bin"))
                    ):
                        return full
            except Exception:
                pass
        return ""

    def _set_whisper_model(self, model_path: str):
        model_path = os.path.abspath(model_path) if model_path else ""
        self.whisper_model_path = model_path
        self.whisper_model_name = os.path.basename(model_path) if model_path else ""
        self.whisper_model_loaded = bool(model_path)
        self._rebuild_whisper_model_submenu()
        self._update_whisper_menu_status()

    def _clear_whisper_model(self):
        self.whisper_model_path = ""
        self.whisper_model_name = ""
        self.whisper_model_loaded = False
        self._rebuild_whisper_model_submenu()
        self._update_whisper_menu_status()
        self.status_bar.showMessage(self._tr("msg_whisper_model_unloaded"))

    def _rebuild_whisper_model_submenu(self):
        if not hasattr(self, "whisper_models_submenu"):
            return
        self.whisper_models_submenu.clear()
        if not hasattr(self, "whisper_model_group") or self.whisper_model_group is None:
            self.whisper_model_group = QActionGroup(self)
            self.whisper_model_group.setExclusive(True)
        for act in list(self.whisper_model_group.actions()):
            self.whisper_model_group.removeAction(act)
        if not self.whisper_available_models:
            empty_act = QAction(self._tr("no_models_scan"), self)
            empty_act.setEnabled(False)
            self.whisper_models_submenu.addAction(empty_act)
        else:
            for model_path in self.whisper_available_models:
                name = os.path.basename(model_path)
                act = QAction(name, self)
                act.setCheckable(True)
                act.setChecked(os.path.abspath(model_path) == os.path.abspath(self.whisper_model_path or ""))
                act.triggered.connect(lambda checked, mp=model_path: self._set_whisper_model(mp))
                self.whisper_model_group.addAction(act)
                self.whisper_models_submenu.addAction(act)
        self.whisper_models_submenu.addSeparator()
        self.act_whisper_unload = QAction(self._tr("act_unload_model"), self)
        self.act_whisper_unload.triggered.connect(self._clear_whisper_model)
        self.act_whisper_unload.setEnabled(bool(self.whisper_model_loaded))
        self.whisper_models_submenu.addAction(self.act_whisper_unload)

    def _update_whisper_menu_status(self):
        model_txt = self.whisper_model_name if self.whisper_model_name else "-"
        mic_txt = self.whisper_selected_input_device_label if self.whisper_selected_input_device_label else "-"
        path_txt = self.whisper_models_base_dir if self.whisper_models_base_dir else "-"
        if hasattr(self, "act_whisper_status_model"):
            self.act_whisper_status_model.setText(self._tr("whisper_status_model", model_txt))
        if hasattr(self, "act_whisper_status_mic"):
            self.act_whisper_status_mic.setText(self._tr("whisper_status_mic", mic_txt))
        if hasattr(self, "act_whisper_status_path"):
            self.act_whisper_status_path.setText(self._tr("whisper_status_path", path_txt))
        if hasattr(self, "act_whisper_unload"):
            self.act_whisper_unload.setEnabled(bool(self.whisper_model_loaded))

    def set_whisper_base_dir_dialog(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            self._tr("dlg_whisper_model_dir"),
            self.whisper_models_base_dir or os.getcwd()
        )
        if not folder:
            return
        self.whisper_models_base_dir = self._normalize_whisper_base_dir(folder)
        self.settings.setValue("paths/whisper_models_base_dir", self.whisper_models_base_dir)
        self._scan_whisper_models()
        # falls bisheriges Modell nicht mehr im Pfad liegt -> entladen
        if self.whisper_model_path and not os.path.exists(self.whisper_model_path):
            self._clear_whisper_model()
        else:
            self._rebuild_whisper_model_submenu()
            self._update_whisper_menu_status()
        self.status_bar.showMessage(self._tr("msg_whisper_path_set", self.whisper_models_base_dir))

    def scan_whisper_models_now(self):
        models = self._scan_whisper_models()
        if models:
            if not self.whisper_model_path or self.whisper_model_path not in models:
                self._set_whisper_model(models[0])
            else:
                self._rebuild_whisper_model_submenu()
                self._update_whisper_menu_status()
            self.status_bar.showMessage(self._tr("msg_whisper_models_found", len(models)))
        else:
            self._clear_whisper_model()
            self.status_bar.showMessage(self._tr("msg_whisper_models_not_found"))

    def scan_whisper_and_select_first_mic(self):
        # 1) Whisper-Modelle scannen
        self.scan_whisper_models_now()
        # 2) erstes verfügbares Mikro automatisch setzen
        devices = self._get_input_audio_devices()
        if not devices:
            return
        first = devices[0]
        self.whisper_selected_input_device = first["index"]
        self.whisper_selected_input_device_label = first["label"]
        self._update_whisper_menu_status()
        self.status_bar.showMessage(
            self._tr("msg_microphone_set", self.whisper_selected_input_device_label)
        )

    def choose_whisper_microphone_dialog(self):
        devices = self._get_input_audio_devices()
        if not devices:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_no_audio_devices"))
            return
        labels = [d["label"] for d in devices]
        current_idx = 0
        if self.whisper_selected_input_device_label:
            try:
                current_idx = labels.index(self.whisper_selected_input_device_label)
            except ValueError:
                current_idx = 0
        selected, ok = QInputDialog.getItem(
            self,
            self._tr("dlg_choose_microphone"),
            self._tr("dlg_audio_input_device"),
            labels,
            current_idx,
            False
        )
        if not ok or not selected:
            return
        for dev in devices:
            if dev["label"] == selected:
                self.whisper_selected_input_device = dev["index"]
                self.whisper_selected_input_device_label = dev["label"]
                break
        self._update_whisper_menu_status()
        self.status_bar.showMessage(self._tr("msg_microphone_set", self.whisper_selected_input_device_label))

    def choose_rec_model_if_missing(self):
        if not self.model_path:
            self.choose_rec_model()

    def choose_seg_model_if_missing(self):
        if not self.seg_model_path:
            self.choose_seg_model()

    def export_default_shortcut(self):
        items = [
            ("Text (.txt)", "txt"),
            ("CSV (.csv)", "csv"),
            ("JSON (.json)", "json"),
            ("ALTO (.xml)", "alto"),
            ("hOCR (.html)", "hocr"),
            ("PDF (.pdf)", "pdf"),
        ]
        names = [x[0] for x in items]
        choice, ok = QInputDialog.getItem(
            self,
            "Export",
            self._tr("export_choose_format_label"),
            names,
            0,
            False
        )
        if not ok or not choice:
            return
        fmt = next(fmt for name, fmt in items if name == choice)
        self.export_flow(fmt)

    def _overlay_selected_rows(self) -> List[int]:
        return sorted(set(int(i) for i in getattr(self.canvas, "_selected_indices", set()) if i is not None))

    def _has_overlay_selection(self) -> bool:
        return len(self._overlay_selected_rows()) > 0

    def _has_line_selection(self) -> bool:
        return len(self._selected_line_rows()) > 0

    def delete_current_context(self):
        """
        Entf:
        - wenn Overlay-Box(en) ausgewählt -> Box(en) + zugehörige Zeile(n) löschen
        - sonst wenn Zeile(n) ausgewählt -> Zeile(n) + Box(en) löschen
        - sonst Queue-Löschen wie bisher
        """
        task = self._current_task()
        overlay_rows = self._overlay_selected_rows()
        line_rows = self._selected_line_rows()
        if task and task.results and task.status == STATUS_DONE:
            rows = overlay_rows if overlay_rows else line_rows
            if rows:
                self._delete_multiple_lines(task, rows)
                return
        # Fallback wie bisher
        if self.queue_table.hasFocus():
            self.delete_selected_queue_items(reset_preview=True)

    def select_all_current_context(self):
        """
        Ctrl+A:
        - wenn Zeilenliste oder Canvas aktiv -> alle Zeilen + alle Overlays auswählen
        - sonst normales Queue-Verhalten
        """
        task = self._current_task()
        if not task or not task.results:
            if self.queue_table.rowCount() > 0:
                self.queue_table.selectAll()
            return
        fw = QApplication.focusWidget()
        canvas_has_focus = (fw is self.canvas or fw is self.canvas.viewport())
        lines_has_focus = (fw is self.list_lines or self.list_lines.isAncestorOf(fw))
        if canvas_has_focus or lines_has_focus or self._has_overlay_selection() or self._has_line_selection():
            _, _, _, recs = task.results
            indices = list(range(len(recs)))
            self.list_lines.blockSignals(True)
            self.list_lines.clearSelection()
            for idx in indices:
                if 0 <= idx < self.list_lines.count():
                    it = self.list_lines.row_item(idx)
                    if it:
                        it.setSelected(True)
            if indices:
                self.list_lines.setCurrentRow(indices[0])
            self.list_lines.blockSignals(False)
            self.canvas.select_indices(indices, center=False)
            self.canvas.overlay_multi_selected.emit(indices)
            return
        # Fallback: Queue
        if self.queue_table.rowCount() > 0:
            self.queue_table.selectAll()

    def _delete_multiple_lines(self, task: TaskItem, rows: List[int]):
        if not task.results:
            return
        text, kr_records, im, recs = task.results
        clean_rows = sorted(set(int(r) for r in rows if 0 <= int(r) < len(recs)), reverse=True)
        if not clean_rows:
            return
        self._push_undo(task)
        for row in clean_rows:
            recs.pop(row)
        task.edited = True
        next_row = None
        if recs:
            lowest_removed = min(clean_rows)
            next_row = max(0, min(lowest_removed, len(recs) - 1))
        self._sync_ui_after_recs_change(task, keep_row=next_row)

    def show_shortcuts_dialog(self):
        self.show_lm_help_dialog()

    def _start_voice_line_fill(self):
        task = self._current_task()
        if not task or task.status != STATUS_DONE or not task.results:
            return
        current_row = self.list_lines.currentRow()
        if current_row < 0:
            return
        _, _, _, recs = task.results
        if not (0 <= current_row < len(recs)):
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
            QMessageBox.warning(
                self,
                self._tr("warn_title"),
                self._tr("warn_no_microphone_available")
            )
            return
        fw_device, fw_compute = self._resolve_faster_whisper_device()
        devices = self._get_input_audio_devices()
        dev_meta = next(
            (d for d in devices if d["index"] == self.whisper_selected_input_device),
            None
        )
        self.voice_worker = VoiceLineFillWorker(
            path=task.path,
            line_index=current_row,
            model_dir=self.whisper_model_path,
            device=fw_device,
            compute_type=fw_compute,
            language=None,
            input_device=self.whisper_selected_input_device,
            input_samplerate=(dev_meta.get("default_samplerate") if dev_meta else None),
            parent=self
        )
        self.voice_worker.finished_line.connect(self.on_voice_line_fill_done)
        self.voice_worker.failed_line.connect(self.on_voice_line_fill_failed)
        self.voice_worker.progress_changed.connect(self.on_voice_progress_changed)
        self.voice_worker.status_changed.connect(self.on_voice_status_changed)
        task.status = STATUS_VOICE_RECORDING
        self._update_queue_row(task.path)
        self.status_bar.showMessage(self._tr("msg_voice_started"))
        self._log(
            self._tr_log("log_voice_import_started", os.path.basename(task.path), current_row + 1, self.whisper_selected_input_device_label, self.whisper_model_name)
        )
        if self.voice_record_dialog:
            self.voice_record_dialog.set_recording_state(True)
        self._set_progress_idle(0)
        self.voice_worker.start()
