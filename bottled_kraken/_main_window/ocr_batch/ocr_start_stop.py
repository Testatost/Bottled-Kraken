from bottled_kraken.common import (
    OCRJob,
    QFileDialog,
    QMessageBox,
    QTimer,
    STATUS_DONE,
    STATUS_ERROR,
    STATUS_PROCESSING,
    STATUS_WAITING,
    os,
)
from bottled_kraken.workers import (
    ExternalBackendOCRWorker,
    OCRWorker,
    get_external_ocr_backend,
)
class MainWindowOcrStartStopMixin:
        def _bk_reset_ocr_cancel_state(self, *, reset_processing: bool = True, message: str = None):
            try:
                for flag in ("_ocr_cancel_requested", "_ocr_stop_requested", "_stop_requested", "_cancel_requested"):
                    try:
                        setattr(self, flag, False)
                    except Exception:
                        pass
                if reset_processing:
                    for task in list(getattr(self, "queue_items", []) or []):
                        try:
                            if getattr(task, "status", None) == STATUS_PROCESSING:
                                task.status = STATUS_WAITING
                                self._update_queue_row(task.path)
                        except Exception:
                            pass
                try:
                    self.act_play.setEnabled(True)
                except Exception:
                    pass
                try:
                    self.act_stop.setEnabled(False)
                except Exception:
                    pass
                try:
                    self._set_progress_idle(0)
                except Exception:
                    try:
                        self.progress_bar.setRange(0, 100)
                        self.progress_bar.setValue(0)
                    except Exception:
                        pass
                if message:
                    try:
                        self.status_bar.showMessage(message, 5000)
                    except Exception:
                        pass
                try:
                    self._update_actions_enabled()
                except Exception:
                    pass
            except Exception:
                pass
        def _bk_prepare_ocr_start_state(self) -> bool:
            try:
                worker = getattr(self, "worker", None)
                if worker is not None:
                    running = False
                    try:
                        running = bool(worker.isRunning())
                    except Exception:
                        running = False
                    if running:
                        try:
                            self.status_bar.showMessage(self._tr("msg_stopping"), 5000)
                        except Exception:
                            pass
                        return False
                    try:
                        worker.deleteLater()
                    except Exception:
                        pass
                    self.worker = None
                for task in list(getattr(self, "queue_items", []) or []):
                    try:
                        if getattr(task, "status", None) == STATUS_PROCESSING:
                            task.status = STATUS_WAITING
                            self._update_queue_row(task.path)
                    except Exception:
                        pass
                for flag in ("_ocr_cancel_requested", "_ocr_stop_requested", "_stop_requested", "_cancel_requested"):
                    try:
                        setattr(self, flag, False)
                    except Exception:
                        pass
                return True
            except Exception:
                return True
        def import_lines_for_all_images(self):
            if not self.queue_items:
                QMessageBox.information(self, self._tr("info_title"), self._tr("info_no_images_loaded"))
                return
            files, _ = QFileDialog.getOpenFileNames(
                self,
                self._tr("dlg_import_lines_all"),
                "",
                "Text/JSON (*.txt *.json)"
            )
            if not files:
                return
            matches = self._match_import_files_to_tasks(self.queue_items, files)
            if not matches:
                QMessageBox.warning(
                    self,
                    self._tr("warn_title"),
                    self._tr("warn_no_matching_import_for_loaded")
                )
                return
            for task in self.queue_items:
                fp = matches.get(task.path)
                if not fp:
                    continue
                try:
                    lines = self._read_import_lines_file(fp)
                    self._apply_imported_lines_to_task(task, lines)
                except Exception as e:
                    self._log(self._tr_log("log_import_error", task.display_name, e))
        def start_ocr(self):
            if not self._bk_prepare_ocr_start_state():
                return
            if not self.model_path or not os.path.exists(self.model_path):
                QMessageBox.critical(self, self._tr("err_title"), self._tr("warn_need_rec"))
                return
            if not self.seg_model_path or not os.path.exists(self.seg_model_path):
                QMessageBox.critical(self, self._tr("err_title"), self._tr("warn_blla_model_missing"))
                return
            checked_tasks = self._checked_queue_tasks()
            selected_tasks = self._selected_queue_tasks()
            target_tasks = checked_tasks if checked_tasks else selected_tasks
            if not target_tasks:
                current_task = self._current_task()
                if current_task and current_task.status in (STATUS_WAITING, STATUS_ERROR, STATUS_DONE):
                    target_tasks = [current_task]
            if target_tasks:
                tasks = []
                for it in target_tasks:
                    if it.status in (STATUS_WAITING, STATUS_ERROR, STATUS_DONE):
                        it.preset_bboxes = []
                        if it.status != STATUS_WAITING:
                            it.status = STATUS_WAITING
                            it.results = None
                            it.edited = False
                            it.undo_stack.clear()
                            it.redo_stack.clear()
                            self._update_queue_row(it.path)
                        tasks.append(it)
            else:
                tasks = [i for i in self.queue_items if i.status == STATUS_WAITING]
            if not tasks:
                QMessageBox.information(self, self._tr("info_title"), self._tr("warn_queue_empty"))
                return
            caps = self._gpu_capabilities()
            ok, _ = caps.get(self.device_str, (False, ""))
            if not ok:
                QMessageBox.warning(self, self._tr("warn_title"), self._tr("msg_hw_not_available"))
                self.device_str = "cpu"
                if "cpu" in self.hw_actions:
                    self.hw_actions["cpu"].setChecked(True)
            self.act_play.setEnabled(False)
            self.act_stop.setEnabled(True)
            self._set_progress_busy()
            paths = [t.path for t in tasks]
            job = OCRJob(
                input_paths=paths,
                recognition_model_path=self.model_path,
                segmentation_model_path=self.seg_model_path,
                device=self.device_str,
                reading_direction=self.reading_direction,
                export_format="pdf",
                export_dir=self.current_export_dir,
                preset_bboxes_by_path={},
                auto_revision_enabled=bool(getattr(self, "kraken_auto_revision_enabled", False)),
                auto_revision_replacements=str(getattr(self, "kraken_auto_revision_replacements", "") or ""),
            )
            external_backend = None
            if self.device_str == "cuda":
                external_backend = get_external_ocr_backend("nvidia-cuda", refresh=True)
            elif self.device_str == "rocm":
                external_backend = get_external_ocr_backend("amd-rocm", refresh=True)
            if external_backend and external_backend.ok:
                self.worker = ExternalBackendOCRWorker(job, external_backend)
                self._log(self._tr_log("log_ocr_started", len(paths), f"{self.device_str} ({external_backend.detail})", self.reading_direction))
            else:
                if self.device_str in ("cuda", "rocm"):
                    self._log(self._tr_log("log_external_backend_fallback_cpu", self.device_str))
                    self.device_str = "cpu"
                    job.device = "cpu"
                    if "cpu" in self.hw_actions:
                        self.hw_actions["cpu"].setChecked(True)
                self.worker = OCRWorker(job)
            self.worker.file_started.connect(self.on_file_started)
            self.worker.file_done.connect(self.on_file_done)
            self.worker.file_error.connect(self.on_file_error)
            self.worker.progress.connect(self.on_progress_update)
            self.worker.finished_batch.connect(self.on_batch_finished)
            self.worker.failed.connect(self.on_failed)
            self.worker.device_resolved.connect(self.on_device_resolved)
            self.worker.gpu_info.connect(self.on_gpu_info)
            if not isinstance(self.worker, ExternalBackendOCRWorker):
                self._log(self._tr_log("log_ocr_started", len(paths), self.device_str, self.reading_direction))
            self.worker.start()
        def on_device_resolved(self, dev_str: str):
            self.status_bar.showMessage(self._tr("msg_using_device", dev_str))
        def on_gpu_info(self, info: str):
            self.status_bar.showMessage(self._tr("msg_detected_gpu", info))
        def stop_ocr(self):
            worker = getattr(self, "worker", None)
            if worker and worker.isRunning():
                try:
                    self._ocr_cancel_requested = True
                    self._ocr_stop_requested = True
                except Exception:
                    pass
                try:
                    if hasattr(worker, "cancel"):
                        worker.cancel()
                    else:
                        worker.requestInterruption()
                except Exception:
                    try:
                        worker.requestInterruption()
                    except Exception:
                        pass
                try:
                    self.act_stop.setEnabled(False)
                except Exception:
                    pass
                try:
                    self._log(self._tr_log("log_stop_requested"))
                except Exception:
                    pass
                try:
                    self.status_bar.showMessage(self._tr("msg_stopping"))
                except Exception:
                    pass
                def _force_cancelled_ocr_cleanup():
                    w = getattr(self, "worker", None)
                    try:
                        if w is not None and w.isRunning():
                            try:
                                w.terminate()
                            except Exception:
                                pass
                            try:
                                w.wait(500)
                            except Exception:
                                pass
                    except Exception:
                        pass
                    try:
                        if getattr(self, "worker", None) is not None and not self.worker.isRunning():
                            try:
                                self.worker.deleteLater()
                            except Exception:
                                pass
                            self.worker = None
                    except Exception:
                        pass
                    self._bk_reset_ocr_cancel_state(reset_processing=True, message=self._tr("msg_ocr_cancelled") if hasattr(self, "_tr") else "OCR abgebrochen.")
                try:
                    QTimer.singleShot(2200, _force_cancelled_ocr_cleanup)
                except Exception:
                    pass
            else:
                self._bk_reset_ocr_cancel_state(reset_processing=True)
