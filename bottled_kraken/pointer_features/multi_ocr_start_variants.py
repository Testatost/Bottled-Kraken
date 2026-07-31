from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('ptr', globals())
def _ptr_start_multi_ocr_v9(self):
    if not getattr(self, "queue_items", None):
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_queue_empty"))
        return
    try:
        self._scan_kraken_models()
    except Exception:
        pass
    rec_models = _ptr_multi_default_rec_models(self)
    if not rec_models:
        QMessageBox.warning(self, self._tr("warn_title"), _ptr_ui_tr(self, "ptr_multi_no_rec_models"))
        return
    default_selected = [self.model_path] if getattr(self, "model_path", "") else [rec_models[0][1]]
    dlg = PtrMultiOcrDialog(rec_models=rec_models, default_selected_paths=default_selected, parent=self)
    if dlg.exec() != QDialog.Accepted:
        return
    rec_paths = []
    seen = set()
    for path in dlg.selected_recognition_paths():
        if path and path not in seen:
            rec_paths.append(path)
            seen.add(path)
    if not rec_paths:
        QMessageBox.warning(self, self._tr("warn_title"), _ptr_ui_tr(self, "ptr_multi_select_rec_model"))
        return
    seg_path = getattr(self, "seg_model_path", None)
    if not seg_path or not os.path.exists(seg_path):
        QMessageBox.warning(self, self._tr("warn_title"), _ptr_ui_tr(self, "ptr_multi_select_seg_model"))
        return
    tasks = _ptr_current_or_selected_target_tasks(self)
    tasks = [task for task in tasks if task.path and os.path.exists(task.path)]
    if not tasks:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_queue_empty"))
        return
    if hasattr(dlg, "selected_image_variant_keys"):
        variant_keys = dlg.selected_image_variant_keys()
    elif hasattr(dlg, "image_variant_count"):
        variant_keys = _ptr_multi_variant_keys_from_count(dlg.image_variant_count())
    else:
        variant_keys = ["original"]
    job = PtrMultiOCRJob(
        input_paths=[task.path for task in tasks],
        recognition_model_paths=rec_paths,
        segmentation_model_path=seg_path,
        reading_direction=self.reading_direction,
        runs=dlg.runs(),
        image_variants_enabled=True,
        image_variant_count=len(variant_keys),
        image_variant_keys=variant_keys,
        language=getattr(self, "current_lang", translation.DEFAULT_LANGUAGE),
    )
    self._ptr_multi_processed_paths = []
    self._ptr_multi_ocr_worker = PtrMultiOCRWorker(job, parent=self)
    self._ptr_multi_ocr_worker.file_started.connect(self._ptr_on_multi_file_started)
    self._ptr_multi_ocr_worker.file_done.connect(self._ptr_on_multi_file_done)
    self._ptr_multi_ocr_worker.file_error.connect(self._ptr_on_multi_file_error)
    self._ptr_multi_ocr_worker.progress.connect(self.on_progress_update)
    self._ptr_multi_ocr_worker.finished_batch.connect(self._ptr_on_multi_batch_finished)
    self._ptr_multi_ocr_worker.failed.connect(self._ptr_on_multi_failed)
    self.act_play.setEnabled(False)
    self.act_stop.setEnabled(True)
    if hasattr(self, "act_ptr_multi_ocr"):
        self.act_ptr_multi_ocr.setEnabled(False)
    self._set_progress_busy()
    self._ptr_multi_ocr_worker.start()
MainWindow.ptr_start_multi_ocr = _ptr_start_multi_ocr_v9
__all__ = [
    '_ptr_start_multi_ocr_v9',
]
register_globals('ptr', globals(), __all__)
