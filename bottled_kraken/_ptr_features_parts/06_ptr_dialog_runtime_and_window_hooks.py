def _ptr_mainwindow_init_wrapper_v2(self, *args, **kwargs):
    _ptr_prev_mainwindow_init(self, *args, **kwargs)
    _ptr_rebuild_secondary_button_rows(self)

def _ptr_mainwindow_retranslate_ui_wrapper_v2(self, *args, **kwargs):
    _ptr_prev_retranslate(self, *args, **kwargs)
    try:
        _ptr_update_feature_texts_v2(self)
    except Exception:
        pass

def _ptr_mainwindow_close_wrapper_v2(self, event):
    try:
        save_api_key = False
        if hasattr(self, "settings") and self.settings is not None:
            save_api_key = bool(self.settings.value("ptr_remote_ai/save_api_key", False, bool))
        if not save_api_key and hasattr(self, "settings") and self.settings is not None:
            self.settings.remove("ptr_remote_ai/api_key")
            self.ptr_remote_ai_api_key = ""
    except Exception:
        pass
    return _ptr_prev_close_event(self, event)

def _ptr_ai_dialog_build_ui_v2(self):
    self.setWindowTitle(_ptr_ui_tr(self, "ptr_ai_tools_title"))
    root = QVBoxLayout(self)
    cfg_wrap = QWidget()
    cfg_form = QFormLayout(cfg_wrap)
    self.provider_edit = QLineEdit("openrouter")
    self.api_key_edit = QLineEdit()
    self.api_key_edit.setEchoMode(QLineEdit.Password)
    self.model_edit = QLineEdit("openrouter/free")
    self.base_url_edit = QLineEdit("https://openrouter.ai/api/v1")
    self.temp_edit = QLineEdit("0.2")
    self.timeout_edit = QLineEdit("90")
    self.app_name_edit = QLineEdit("Bottled Kraken")
    self.app_url_edit = QLineEdit("")
    self.save_api_key_cb = QCheckBox(_ptr_ui_tr(self, "ptr_ai_save_key"))
    cfg_form.addRow(_ptr_ui_tr(self, "ptr_ai_provider"), self.provider_edit)
    cfg_form.addRow(_ptr_ui_tr(self, "ptr_ai_api_key"), self.api_key_edit)
    cfg_form.addRow(_ptr_ui_tr(self, "ptr_ai_model"), self.model_edit)
    cfg_form.addRow(_ptr_ui_tr(self, "ptr_ai_base_url"), self.base_url_edit)
    cfg_form.addRow(_ptr_ui_tr(self, "ptr_ai_temperature"), self.temp_edit)
    cfg_form.addRow(_ptr_ui_tr(self, "ptr_ai_timeout"), self.timeout_edit)
    cfg_form.addRow(_ptr_ui_tr(self, "ptr_ai_app_name"), self.app_name_edit)
    cfg_form.addRow(_ptr_ui_tr(self, "ptr_ai_app_url"), self.app_url_edit)
    cfg_form.addRow("", self.save_api_key_cb)
    root.addWidget(cfg_wrap)
    self.progress_label = QLabel(_ptr_ui_tr(self, "ptr_ai_progress_idle"))
    self.progress_bar = QProgressBar()
    self.progress_bar.setRange(0, 100)
    self.progress_bar.setValue(0)
    root.addWidget(self.progress_label)
    root.addWidget(self.progress_bar)
    splitter = QSplitter(Qt.Horizontal)
    left = QWidget()
    left_layout = QVBoxLayout(left)
    left_layout.addWidget(QLabel(_ptr_ui_tr(self, "ptr_ai_input_variants")))
    self.input_edit = QPlainTextEdit()
    self.input_edit.setPlaceholderText(_ptr_ui_tr(self, "ptr_ai_input_placeholder"))
    left_layout.addWidget(self.input_edit)
    right = QWidget()
    right_layout = QVBoxLayout(right)
    right_layout.addWidget(QLabel(_ptr_ui_tr(self, "ptr_ai_merged_text")))
    self.merged_edit = QPlainTextEdit()
    right_layout.addWidget(self.merged_edit)
    right_layout.addWidget(QLabel(_ptr_ui_tr(self, "ptr_ai_result")))
    self.result_output_edit = QPlainTextEdit()
    right_layout.addWidget(self.result_output_edit)
    splitter.addWidget(left)
    splitter.addWidget(right)
    splitter.setSizes([500, 600])
    root.addWidget(splitter, 1)
    row1 = QHBoxLayout()
    self.merge_btn = QPushButton(_ptr_ui_tr(self, "ptr_ai_btn_merge"))
    self.postgres_btn = QPushButton(_ptr_ui_tr(self, "ptr_ai_btn_postgres"))
    self.neo4j_btn = QPushButton(_ptr_ui_tr(self, "ptr_ai_btn_neo4j"))
    self.pipeline_btn = QPushButton(_ptr_ui_tr(self, "ptr_ai_btn_pipeline"))
    row1.addWidget(self.merge_btn)
    row1.addWidget(self.postgres_btn)
    row1.addWidget(self.neo4j_btn)
    row1.addWidget(self.pipeline_btn)
    root.addLayout(row1)
    row2 = QHBoxLayout()
    self.save_merged_btn = QPushButton(_ptr_ui_tr(self, "ptr_ai_btn_save_merged"))
    self.save_result_btn = QPushButton(_ptr_ui_tr(self, "ptr_ai_btn_save_result"))
    self.clear_btn = QPushButton(_ptr_ui_tr(self, "ptr_ai_btn_clear"))
    self.close_btn = QPushButton(_ptr_ui_tr(self, "ptr_ai_btn_close"))
    row2.addWidget(self.save_merged_btn)
    row2.addWidget(self.save_result_btn)
    row2.addWidget(self.clear_btn)
    row2.addStretch(1)
    row2.addWidget(self.close_btn)
    root.addLayout(row2)
    self.merge_btn.clicked.connect(self._on_merge)
    self.postgres_btn.clicked.connect(self._on_postgres)
    self.neo4j_btn.clicked.connect(self._on_neo4j)
    self.pipeline_btn.clicked.connect(self._on_pipeline)
    self.save_merged_btn.clicked.connect(self._save_merged)
    self.save_result_btn.clicked.connect(self._save_result)
    self.clear_btn.clicked.connect(self._clear_outputs)
    self.close_btn.clicked.connect(self.accept)

def _ptr_ai_dialog_set_config_v2(self, config: PtrRemoteAIConfig):
    self.setWindowTitle(_ptr_ui_tr(self, "ptr_ai_tools_title"))
    self.provider_edit.setText(config.provider_name or "openrouter")
    self.api_key_edit.setText(config.api_key or "")
    self.model_edit.setText(config.model or "openrouter/free")
    self.base_url_edit.setText(_ptr_normalize_remote_base_url(config.base_url or "https://openrouter.ai/api/v1", config.provider_name))
    self.temp_edit.setText(str(config.temperature))
    self.timeout_edit.setText(str(config.timeout_seconds))
    self.app_name_edit.setText(config.app_name or "Bottled Kraken")
    self.app_url_edit.setText(config.app_url or "")
    self.save_api_key_cb.setChecked(bool(getattr(config, "save_api_key", False)))
    self.progress_label.setText(_ptr_ui_tr(self, "ptr_ai_progress_idle"))
    self.progress_bar.setRange(0, 100)
    self.progress_bar.setValue(0)

def _ptr_ai_dialog_get_config_v2(self) -> PtrRemoteAIConfig:
    def _float(text: str, default: float) -> float:
        try:
            return float(str(text).strip().replace(",", "."))
        except Exception:
            return default
    def _int(text: str, default: int) -> int:
        try:
            return int(float(str(text).strip().replace(",", ".")))
        except Exception:
            return default
    cfg = PtrRemoteAIConfig(
        provider_name=(self.provider_edit.text().strip() or "openrouter"),
        api_key=self.api_key_edit.text().strip(),
        base_url=_ptr_normalize_remote_base_url(self.base_url_edit.text().strip() or "https://openrouter.ai/api/v1", self.provider_edit.text().strip() or "openrouter"),
        model=(self.model_edit.text().strip() or "openrouter/free"),
        timeout_seconds=_int(self.timeout_edit.text(), 90),
        temperature=_float(self.temp_edit.text(), 0.2),
        app_name=(self.app_name_edit.text().strip() or "Bottled Kraken"),
        app_url=self.app_url_edit.text().strip(),
    )
    setattr(cfg, "save_api_key", self.save_api_key_cb.isChecked())
    return cfg

def _ptr_ai_dialog_set_busy_v2(self, busy: bool):
    for w in [self.merge_btn, self.postgres_btn, self.neo4j_btn, self.pipeline_btn,
              self.save_merged_btn, self.save_result_btn, self.clear_btn, self.close_btn,
              self.provider_edit, self.api_key_edit, self.model_edit, self.base_url_edit,
              self.temp_edit, self.timeout_edit, self.app_name_edit, self.app_url_edit,
              self.save_api_key_cb]:
        w.setEnabled(not busy)
    if busy:
        self.progress_bar.setRange(0, 0)
    else:
        self.progress_bar.setRange(0, 100)
        current_text = (self.merged_edit.toPlainText().strip() or self.result_output_edit.toPlainText().strip())
        self.progress_bar.setValue(100 if current_text else 0)
        self.progress_label.setText(_ptr_ui_tr(self, "ptr_ai_progress_idle"))
    self.setCursor(Qt.WaitCursor if busy else Qt.ArrowCursor)

def _ptr_ai_dialog_start_worker_v2(self, mode: str, *, include_postgres: bool = True, include_neo4j: bool = True):
    if self._worker and self._worker.isRunning():
        return
    cfg = self.get_config()
    texts = self._collect_ocr_inputs()
    merged = self._collect_merged_text()
    if mode == "merge":
        merged = ""
        self.progress_label.setText(_ptr_ui_tr(self, "ptr_ai_running_merge"))
    elif mode == "postgres":
        self.progress_label.setText(_ptr_ui_tr(self, "ptr_ai_running_postgres"))
    elif mode == "neo4j":
        self.progress_label.setText(_ptr_ui_tr(self, "ptr_ai_running_neo4j"))
    else:
        self.progress_label.setText(_ptr_ui_tr(self, "ptr_ai_running_pipeline"))
    self._worker = PtrRemoteAITaskWorker(
        mode=mode,
        config=cfg,
        ocr_texts=texts,
        merged_text=merged,
        include_postgres=include_postgres,
        include_neo4j=include_neo4j,
        parent=self,
    )
    self._worker.result_ready.connect(self._on_worker_result)
    self._worker.failed.connect(self._on_worker_failed)
    self._worker.finished.connect(lambda: self._set_busy(False))
    self._set_busy(True)
    self._worker.start()

def _ptr_ai_dialog_worker_result_v2(self, payload):
    mode = str((payload or {}).get("mode", ""))
    merged = str((payload or {}).get("merged_text", "") or "").strip()
    if merged:
        self._merged_text = merged
        self.merged_edit.setPlainText(merged)
    self.progress_bar.setRange(0, 100)
    self.progress_bar.setValue(100)
    if mode == "merge":
        self.result_output_edit.clear()
        self._existing_result_data = None
        self.merge_completed.emit(merged)
        return
    if mode == "postgres":
        data = _ptr_normalize_postgres_json(payload.get("postgres"), merged or self._collect_merged_text())
        self._existing_result_data = data
        self.result_output_edit.setPlainText(json.dumps(data, ensure_ascii=False, indent=2))
        if merged:
            self.merge_completed.emit(merged)
        self.postgres_completed.emit(data)
        return
    if mode == "neo4j":
        data = payload.get("neo4j")
        self._existing_result_data = data
        self.result_output_edit.setPlainText(json.dumps(data, ensure_ascii=False, indent=2))
        if merged:
            self.merge_completed.emit(merged)
        if isinstance(data, dict):
            self.neo4j_completed.emit(data)
        return
    if mode == "pipeline":
        pg = _ptr_normalize_postgres_json(payload.get("postgres"), merged or self._collect_merged_text()) if payload.get("postgres") is not None else None
        neo = payload.get("neo4j")
        shown = neo if isinstance(neo, dict) else pg
        if shown is not None:
            self._existing_result_data = shown
            self.result_output_edit.setPlainText(json.dumps(shown, ensure_ascii=False, indent=2))
        if merged:
            self.merge_completed.emit(merged)
        if isinstance(pg, dict):
            self.postgres_completed.emit(pg)
        if isinstance(neo, dict):
            self.neo4j_completed.emit(neo)
        self.pipeline_completed.emit(merged, pg, neo)

def _ptr_ai_dialog_worker_failed_v2(self, message: str):
    self.progress_bar.setRange(0, 100)
    self.progress_bar.setValue(0)
    self.progress_label.setText(_ptr_ui_tr(self, "ptr_ai_progress_idle"))
    QMessageBox.critical(self, _ptr_ui_tr(self, "ptr_ai_tools_title"), str(message))

def _ptr_ai_dialog_save_merged_v2(self):
    text = self.merged_edit.toPlainText().strip()
    if not text:
        QMessageBox.information(self, _ptr_ui_tr(self, "ptr_ai_tools_title"), _ptr_ui_tr(self, "ptr_ai_no_merged"))
        return
    path, _ = QFileDialog.getSaveFileName(self, _ptr_ui_tr(self, "ptr_ai_btn_save_merged"), "ai_merged.txt", "Text Files (*.txt)")
    if not path:
        return
    if not path.lower().endswith(".txt"):
        path += ".txt"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)

def _ptr_ai_dialog_save_result_v2(self):
    data = self._existing_result_data
    if data is None:
        txt = self.result_output_edit.toPlainText().strip()
        if txt:
            data = txt
    if data is None:
        QMessageBox.information(self, _ptr_ui_tr(self, "ptr_ai_tools_title"), _ptr_ui_tr(self, "ptr_ai_no_result"))
        return
    path, _ = QFileDialog.getSaveFileName(self, _ptr_ui_tr(self, "ptr_ai_btn_save_result"), "ai_result.json", "JSON Files (*.json);;Text Files (*.txt)")
    if not path:
        return
    if isinstance(data, dict):
        if not path.lower().endswith(".json"):
            path += ".json"
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
    else:
        if not path.lower().endswith(".txt"):
            path += ".txt"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(str(data))

_ptr_prev_mainwindow_init = MainWindow.__init__

_ptr_prev_retranslate = MainWindow.retranslate_ui

_ptr_prev_close_event = MainWindow.closeEvent

PtrMultiOCRFollowupDialog.__init__ = _ptr_followup_init_v2

PtrAIToolsDialog._build_ui = _ptr_ai_dialog_build_ui_v2

PtrAIToolsDialog.set_config = _ptr_ai_dialog_set_config_v2

PtrAIToolsDialog.get_config = _ptr_ai_dialog_get_config_v2

PtrAIToolsDialog._set_busy = _ptr_ai_dialog_set_busy_v2

PtrAIToolsDialog._start_worker = _ptr_ai_dialog_start_worker_v2

PtrAIToolsDialog._on_worker_result = _ptr_ai_dialog_worker_result_v2

PtrAIToolsDialog._on_worker_failed = _ptr_ai_dialog_worker_failed_v2

PtrAIToolsDialog._save_merged = _ptr_ai_dialog_save_merged_v2

PtrAIToolsDialog._save_result = _ptr_ai_dialog_save_result_v2

_ptr_ai_build_postgres_json = _ptr_ai_build_postgres_json_v2

_ptr_remote_chat_completion = _ptr_remote_chat_completion_v2

_ptr_feature_config_from_window = _ptr_feature_config_from_window_v2

_ptr_save_feature_config_to_window = _ptr_save_feature_config_to_window_v2

MainWindow._ptr_install_feature_actions = _ptr_install_feature_actions_v2

MainWindow.ptr_update_feature_texts = _ptr_update_feature_texts_v2

MainWindow.__init__ = _ptr_mainwindow_init_wrapper_v2

MainWindow.retranslate_ui = _ptr_mainwindow_retranslate_ui_wrapper_v2

MainWindow.closeEvent = _ptr_mainwindow_close_wrapper_v2

def _ptr_unique_keep_order(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for item in items:
        key = str(item or '').strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(str(item).strip())
    return out

def _ptr_source_lines_for_postgres(source_text: str) -> List[str]:
    lines = []
    for raw_line in str(source_text or '').replace('\r', '').split('\n'):
        line = re.sub(r'\s+', ' ', raw_line).strip(' \t-–—;|')
        if line:
            lines.append(line)
    return lines

def _ptr_guess_person_name_from_line(line: str) -> Optional[str]:
    txt = str(line or '').strip()
    if not txt:
        return None
    txt = re.sub(r'^[\-–—\s]+', '', txt)
    primary = re.split(r'[,:;()]', txt, maxsplit=1)[0].strip()
    primary = re.sub(r'^(Herrn?|Frau|Frl\.?|Hr\.?|Hrn\.?|Mme\.?|M\.)\s+', '', primary, flags=re.IGNORECASE)
    primary = re.sub(r'\s+', ' ', primary).strip(' .,-;:')
    if not primary:
        return None
    letters = re.findall(r'[A-Za-zÀ-ÿÄÖÜäöüß]', primary)
    if len(letters) < 2:
        return None
    if any(ch.isdigit() for ch in primary):
        return None
    return primary[:140]
