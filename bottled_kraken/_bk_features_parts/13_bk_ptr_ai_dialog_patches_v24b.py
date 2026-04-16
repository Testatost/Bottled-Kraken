def _ptr_ai_dialog_worker_failed_v24(self, message: str):
    self.progress_bar.setRange(0, 100)
    self.progress_bar.setValue(0)
    self.progress_label.setText(_ptr_ui_tr(self, 'ptr_ai_progress_idle'))
    QMessageBox.critical(self, _ptr_ui_tr(self, 'ptr_ai_tools_title'), _bk_patch24_translate_error_message(self, message))

def _ptr_on_multi_file_error_v24(self, path: str, message: str):
    task = _ptr_find_task(self, path)
    if task:
        task.status = STATUS_ERROR
        self._update_queue_row(path)
    self.status_bar.showMessage(_ptr_ui_tr(self, 'ptr_multi_status_error', os.path.basename(path)), 3000)
    self._log(f"{_ptr_ui_tr(self, 'ptr_multi_status_error', os.path.basename(path))} -> {_bk_patch24_translate_error_message(self, message)}")

def _ptr_on_multi_failed_v24(self, message: str):
    self.act_play.setEnabled(True)
    self.act_stop.setEnabled(False)
    if hasattr(self, 'act_ptr_multi_ocr'):
        self.act_ptr_multi_ocr.setEnabled(True)
    self._set_progress_idle(0)
    worker = getattr(self, '_ptr_multi_ocr_worker', None)
    self._ptr_multi_ocr_worker = None
    if worker is not None:
        try:
            worker.deleteLater()
        except Exception:
            pass
    QMessageBox.critical(self, _ptr_ui_tr(self, 'ptr_multi_ocr_title'), _bk_patch24_translate_error_message(self, message))

PtrAIToolsDialog._start_worker = _ptr_ai_dialog_start_worker_v24

PtrAIToolsDialog._on_worker_failed = _ptr_ai_dialog_worker_failed_v24

MainWindow._ptr_on_multi_file_error = _ptr_on_multi_file_error_v24

MainWindow._ptr_on_multi_failed = _ptr_on_multi_failed_v24

def _bk_patch24b_is_openrouter_config(cfg) -> bool:
    provider = str(getattr(cfg, 'provider_name', '') or '').strip().lower()
    base_url = str(getattr(cfg, 'base_url', '') or '').strip().lower()
    return provider == 'openrouter' or 'openrouter.ai' in base_url

def _bk_patch24b_is_local_config(cfg) -> bool:
    if cfg is None:
        return False
    return not _bk_patch24b_is_openrouter_config(cfg)

def _bk_patch24b_has_multi_ocr_inputs(dialog) -> bool:
    try:
        texts = dialog._collect_ocr_inputs()
    except Exception:
        texts = []
    cleaned = [str(x).strip() for x in (texts or []) if str(x).strip()]
    return len(cleaned) > 1

def _bk_patch24b_sync_ai_mode_ui(self):
    cfg = self.get_config()
    is_local = _bk_patch24b_is_local_config(cfg)
    try:
        self.pipeline_btn.setEnabled(not is_local)
        self.pipeline_btn.setToolTip(
            _ptr_ui_tr(self, 'ptr_warn_local_no_pipeline') if is_local else ''
        )
    except Exception:
        pass

def _ptr_multi_ocr_dialog_init_v24b(self, rec_models: List[Tuple[str, str]], default_selected_paths: Optional[List[str]] = None, parent=None):
    QDialog.__init__(self, parent)
    self.setWindowTitle(_ptr_ui_tr(self, 'ptr_multi_ocr_title'))
    self.setMinimumWidth(520)
    self._rec_models = rec_models
    self._default_selected = set(default_selected_paths or [])
    root = QVBoxLayout(self)
    root.addWidget(QLabel(_ptr_ui_tr(self, 'ptr_multi_ocr_runs_label')))
    self.spin_runs = QSpinBox()
    self.spin_runs.setRange(1, 99)
    self.spin_runs.setSingleStep(1)
    self.spin_runs.setValue(3)
    root.addWidget(self.spin_runs)
    root.addSpacing(8)
    root.addWidget(QLabel(_ptr_ui_tr(self, 'ptr_multi_ocr_models_label')))
    self.list_models = QListWidget()
    self.list_models.setSelectionMode(QAbstractItemView.MultiSelection)
    for name, path in self._rec_models:
        it = QListWidgetItem(name)
        it.setData(Qt.UserRole, path)
        self.list_models.addItem(it)
        if path in self._default_selected:
            it.setSelected(True)
    if self.list_models.count() > 0 and not self.list_models.selectedItems():
        self.list_models.item(0).setSelected(True)
    root.addWidget(self.list_models)
    self.chk_use_seg = QCheckBox(_ptr_ui_tr(self, 'ptr_multi_ocr_use_seg'))
    self.chk_use_seg.setChecked(True)
    root.addWidget(self.chk_use_seg)
    bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    try:
        bb.button(QDialogButtonBox.Ok).setText(_ptr_ui_tr(self, 'btn_ok'))
    except Exception:
        pass
    try:
        bb.button(QDialogButtonBox.Cancel).setText(_ptr_ui_tr(self, 'btn_cancel'))
    except Exception:
        pass
    bb.accepted.connect(self.accept)
    bb.rejected.connect(self.reject)
    root.addWidget(bb)

def _ptr_multi_followup_init_v24b(self, parent=None):
    QDialog.__init__(self, parent)
    self.setWindowTitle(_ptr_ui_tr(self, 'ptr_multi_followup_open_title'))
    self.resize(560, 220)
    self.choice = self.CHOICE_CANCEL
    root = QVBoxLayout(self)
    lbl = QLabel(_ptr_ui_tr(self, 'ptr_ai_multi_done_text'))
    lbl.setWordWrap(True)
    root.addWidget(lbl)
    row1 = QHBoxLayout()
    row2 = QHBoxLayout()
    self.local_btn = QPushButton(_ptr_ui_tr(self, 'ptr_ai_local_merge'))
    self.ai_btn = QPushButton(_ptr_ui_tr(self, 'ptr_multi_followup_open_ai'))
    self.ai_pg_btn = QPushButton(_ptr_ui_tr(self, 'ptr_ai_followup_postgres'))
    self.ai_neo_btn = QPushButton(_ptr_ui_tr(self, 'ptr_ai_followup_neo4j'))
    self.ai_both_btn = QPushButton(_ptr_ui_tr(self, 'ptr_ai_both'))
    self.cancel_btn = QPushButton(_ptr_ui_tr(self, 'btn_cancel'))
    row1.addWidget(self.local_btn)
    row1.addWidget(self.ai_btn)
    row1.addWidget(self.cancel_btn)
    row2.addWidget(self.ai_pg_btn)
    row2.addWidget(self.ai_neo_btn)
    row2.addWidget(self.ai_both_btn)
    root.addLayout(row1)
    root.addLayout(row2)
    self.local_btn.clicked.connect(lambda: self._choose(self.CHOICE_LOCAL))
    self.ai_btn.clicked.connect(lambda: self._choose(self.CHOICE_AI))
    self.ai_pg_btn.clicked.connect(lambda: self._choose(self.CHOICE_AI_POSTGRES))
    self.ai_neo_btn.clicked.connect(lambda: self._choose(self.CHOICE_AI_NEO4J))
    self.ai_both_btn.clicked.connect(lambda: self._choose(self.CHOICE_AI_BOTH))
    self.cancel_btn.clicked.connect(self.reject)

def _ptr_ai_dialog_init_v24b(self, parent=None, config: Optional[PtrRemoteAIConfig] = None):
    QDialog.__init__(self, parent)
    self.setWindowTitle(_ptr_ui_tr(self, 'ptr_ai_tools_open_title'))
    self.resize(1150, 760)
    self._worker: Optional[PtrRemoteAITaskWorker] = None
    self._ocr_inputs: List[str] = []
    self._merged_text: str = ""
    self._existing_result_data = None
    self._build_ui()
    self.set_config(config or PtrRemoteAIConfig())
    _bk_patch24b_sync_ai_mode_ui(self)

def _ptr_ai_dialog_build_ui_v24b(self):
    _ptr_ai_dialog_build_ui_v3(self)
    for _w in (getattr(self, 'provider_edit', None), getattr(self, 'base_url_edit', None)):
        if _w is None:
            continue
        try:
            _w.textChanged.connect(lambda _=None: _bk_patch24b_sync_ai_mode_ui(self))
        except Exception:
            pass
    try:
        _ptr_ai_dialog_apply_key_hints_v23(self)
    except Exception:
        pass

def _ptr_ai_dialog_start_worker_v24b(self, mode: str, *, include_postgres: bool = True, include_neo4j: bool = True):
    if self._worker and self._worker.isRunning():
        return
    cfg = self.get_config()
    cfg.ui_lang = _bk_patch24_lang(self)
    is_local = _bk_patch24b_is_local_config(cfg)
    has_multi = _bk_patch24b_has_multi_ocr_inputs(self)
    if is_local and has_multi:
        QMessageBox.warning(self, _ptr_ui_tr(self, 'warn_title'), _ptr_ui_tr(self, 'ptr_warn_local_no_multi_ocr_ai'))
        return
    if is_local and (mode or '').strip().lower() == 'pipeline':
        QMessageBox.warning(self, _ptr_ui_tr(self, 'warn_title'), _ptr_ui_tr(self, 'ptr_warn_local_no_pipeline'))
        return
    texts = self._collect_ocr_inputs()
    merged = self._collect_merged_text()
    if mode == 'merge':
        merged = ''
        self.progress_label.setText(_ptr_ui_tr(self, 'ptr_ai_running_merge'))
    elif mode == 'postgres':
        self.progress_label.setText(_ptr_ui_tr(self, 'ptr_ai_running_postgres'))
    elif mode == 'neo4j':
        self.progress_label.setText(_ptr_ui_tr(self, 'ptr_ai_running_neo4j'))
    else:
        self.progress_label.setText(_ptr_ui_tr(self, 'ptr_ai_running_pipeline'))
    self._worker = PtrRemoteAITaskWorker(
        mode=mode,
        config=cfg,
        ocr_texts=texts,
        merged_text=merged,
        include_postgres=include_postgres,
        include_neo4j=include_neo4j,
        parent=self,
    )
    setattr(self._worker, 'ui_lang', _bk_patch24_lang(self))
    self._worker.result_ready.connect(self._on_worker_result)
    self._worker.failed.connect(self._on_worker_failed)
    self._worker.finished.connect(lambda: self._set_busy(False))
    self._set_busy(True)
    self._worker.start()

def _ptr_ai_dialog_worker_failed_v24b(self, message: str):
    translated = _bk_patch24_translate_error_message(_bk_patch24_lang(self), str(message))
    QMessageBox.critical(self, _ptr_ui_tr(self, 'ptr_ai_tools_open_title'), translated)

def _ptr_ai_dialog_save_merged_v24b(self):
    text = self.merged_edit.toPlainText().strip()
    if not text:
        QMessageBox.information(self, _ptr_ui_tr(self, 'ptr_ai_tools_open_title'), _ptr_ui_tr(self, 'ptr_ai_no_merged'))
        return
    path, _ = QFileDialog.getSaveFileName(
        self,
        _ptr_ui_tr(self, 'ptr_ai_save_merged_title'),
        'ai_merged.txt',
        _ptr_ui_tr(self, 'ptr_filter_text_files')
    )
    if not path:
        return
    if not path.lower().endswith('.txt'):
        path += '.txt'
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(text)

def _ptr_ai_dialog_save_result_v24b(self):
    data = self._existing_result_data
    if data is None:
        txt = self.result_output_edit.toPlainText().strip()
        if txt:
            data = txt
    if data is None:
        QMessageBox.information(self, _ptr_ui_tr(self, 'ptr_ai_tools_open_title'), _ptr_ui_tr(self, 'ptr_ai_no_result'))
        return
    path, _ = QFileDialog.getSaveFileName(
        self,
        _ptr_ui_tr(self, 'ptr_ai_save_result_title'),
        'ai_result.json',
        _ptr_ui_tr(self, 'ptr_filter_json_text_files')
    )
    if not path:
        return
    if isinstance(data, dict):
        if not path.lower().endswith('.json'):
            path += '.json'
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
    else:
        if not path.lower().endswith('.txt'):
            path += '.txt'
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(str(data))

PtrMultiOcrDialog.__init__ = _ptr_multi_ocr_dialog_init_v24b

PtrMultiOCRFollowupDialog.__init__ = _ptr_multi_followup_init_v24b

PtrAIToolsDialog.__init__ = _ptr_ai_dialog_init_v24b

PtrAIToolsDialog._build_ui = _ptr_ai_dialog_build_ui_v24b

PtrAIToolsDialog._start_worker = _ptr_ai_dialog_start_worker_v24b

PtrAIToolsDialog._on_worker_failed = _ptr_ai_dialog_worker_failed_v24b

PtrAIToolsDialog._save_merged = _ptr_ai_dialog_save_merged_v24b

PtrAIToolsDialog._save_result = _ptr_ai_dialog_save_result_v24b

def _ptr_apply_local_merge_to_task_v24c(self, path: str):
    variants = list((getattr(self, '_ptr_multi_ocr_variants_by_path', {}) or {}).get(path, []))
    if not variants:
        QMessageBox.information(self, _ptr_ui_tr(self, 'ptr_multi_ocr_title'), _ptr_ui_tr(self, 'ptr_multi_no_variants'))
        return
    merged_text = _ptr_merge_ocr_texts_local(variants)
    if not merged_text.strip():
        QMessageBox.information(self, _ptr_ui_tr(self, 'ptr_multi_ocr_title'), _ptr_ui_tr(self, 'ptr_multi_local_merge_empty'))
        return
    self._ptr_ai_merged_by_path[path] = merged_text
    task = _ptr_find_task(self, path)
    if task and task.results:
        text, kr_records, im, recs = task.results
        merged_lines = [ln for ln in merged_text.splitlines()]
        if merged_lines and len(merged_lines) == len(recs):
            new_recs = [RecordView(i, merged_lines[i], recs[i].bbox) for i in range(len(merged_lines))]
            task.results = ('\n'.join(merged_lines).strip(), kr_records, im, new_recs)
            if self._current_task() and self._current_task().path == path:
                self.load_results(path)
        self._update_queue_row(path)
    self.status_bar.showMessage(_ptr_ui_tr(self, 'ptr_multi_local_merge_done', os.path.basename(path)), 3000)

def _ptr_open_ai_tools_v24c(self, target_path: Optional[str] = None, auto_mode: Optional[str] = None):
    if not target_path:
        task = self._current_task()
        if not task:
            QMessageBox.warning(self, self._tr('warn_title'), _ptr_ui_tr(self, 'ptr_select_file_first'))
            return
        target_path = task.path
    task = _ptr_find_task(self, target_path)
    if not task:
        QMessageBox.warning(self, self._tr('warn_title'), _ptr_ui_tr(self, 'ptr_selected_file_missing'))
        return
    texts = list(self._ptr_multi_ocr_variants_by_path.get(target_path, []))
    if not texts and task.results:
        texts = [task.results[0]] if task.results[0] else []
    if not texts:
        QMessageBox.warning(self, self._tr('warn_title'), _ptr_ui_tr(self, 'ptr_no_ocr_texts'))
        return
    dlg = PtrAIToolsDialog(self, config=_ptr_feature_config_from_window(self))
    dlg.setAttribute(Qt.WA_DeleteOnClose, True)
    dlg.set_ocr_inputs(texts)
    dlg.set_existing_merged_text(self._ptr_ai_merged_by_path.get(target_path, ''))
    def _remember():
        try:
            _ptr_save_feature_config_to_window(self, dlg.get_config())
        except Exception:
            pass
    dlg.finished.connect(_remember)
    dlg.merge_completed.connect(lambda text, p=target_path: self._ptr_store_ai_merge(p, text))
    dlg.postgres_completed.connect(lambda data, p=target_path: self._ptr_store_ai_postgres(p, data))
    dlg.neo4j_completed.connect(lambda data, p=target_path: self._ptr_store_ai_neo4j(p, data))
    dlg.pipeline_completed.connect(lambda merged, pg, neo, p=target_path: self._ptr_store_ai_pipeline(p, merged, pg, neo))
    dlg.show()
    self._ptr_last_ai_dialog = dlg
    if auto_mode:
        dlg.auto_run(auto_mode)

def _ptr_store_ai_merge_v24c(self, path: str, merged_text: str):
    merged_text = (merged_text or '').strip()
    if not merged_text:
        return
    self._ptr_ai_merged_by_path[path] = merged_text
    self.status_bar.showMessage(_ptr_ui_tr(self, 'ptr_ai_merge_done', os.path.basename(path)), 3000)

def _ptr_store_ai_postgres_v24c(self, path: str, data: dict):
    if not isinstance(data, dict):
        return
    self._ptr_ai_postgres_by_path[path] = data
    self.status_bar.showMessage(_ptr_ui_tr(self, 'ptr_postgres_done', os.path.basename(path)), 3000)

def _ptr_store_ai_neo4j_v24c(self, path: str, data: dict):
    if not isinstance(data, dict):
        return
    self._ptr_ai_neo4j_by_path[path] = data
    self.status_bar.showMessage(_ptr_ui_tr(self, 'ptr_neo4j_done', os.path.basename(path)), 3000)

def _ptr_export_ai_merge_for_current_v24c(self, path: str):
    text = self._ptr_ai_merged_by_path.get(path, '')
    default_name = f"{os.path.splitext(os.path.basename(path))[0]}_ai_merge.txt"
    self._ptr_export_text_interactive(text, _ptr_ui_tr(self, 'ptr_export_ai_merge'), default_name)
