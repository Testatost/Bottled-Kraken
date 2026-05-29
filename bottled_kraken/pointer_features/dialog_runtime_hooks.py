from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('ptr', globals())
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
    cfg_form.addRow("", self.save_api_key_cb)
    root.addWidget(cfg_wrap)
    self.progress_label = QLabel(_ptr_ui_tr(self, "ptr_ai_progress_idle"), self)
    self.progress_bar = QProgressBar(self)
    self.progress_bar.setRange(0, 100)
    self.progress_bar.setValue(0)
    self.progress_label.setVisible(False)
    self.progress_bar.setVisible(False)
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
    result_head = QHBoxLayout()
    result_head.addWidget(QLabel(_ptr_ui_tr(self, "ptr_ai_result")))
    result_head.addStretch(1)
    self.graph_display_btn = QPushButton(_ptr_ui_tr(self, "ptr_ai_btn_graph_display"))
    self.graph_display_btn.setMinimumWidth(180)
    result_head.addWidget(self.graph_display_btn)
    self.graph_load_btn = QPushButton(_ptr_ui_tr(self, "ptr_ai_btn_graph_load"))
    self.graph_load_btn.setMinimumWidth(210)
    result_head.addWidget(self.graph_load_btn)
    try:
        self.graph_display_btn.clicked.connect(lambda: _ptr_ai_dialog_graph_display_dispatch_v4(self))
        self._bk_graph_display_connected = True
    except Exception:
        pass
    try:
        self.graph_load_btn.clicked.connect(lambda: _ptr_ai_dialog_graph_load_dispatch_v5(self))
        self._bk_graph_load_connected = True
    except Exception:
        pass
    right_layout.addLayout(result_head)
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
    self.save_sqlite_btn = QPushButton(_ptr_ui_tr(self, "ptr_ai_btn_save_sqlite"))
    for _btn in (self.merge_btn, self.postgres_btn, self.neo4j_btn, self.save_sqlite_btn):
        _btn.setMinimumWidth(180)
        row1.addWidget(_btn, 1)
    root.addLayout(row1)
    row2 = QHBoxLayout()
    self.pipeline_btn = QPushButton(_ptr_ui_tr(self, "ptr_ai_btn_pipeline"))
    self.save_merged_btn = QPushButton(_ptr_ui_tr(self, "ptr_ai_btn_save_merged"))
    self.save_result_btn = QPushButton(_ptr_ui_tr(self, "ptr_ai_btn_save_result"))
    self.clear_btn = QPushButton(_ptr_ui_tr(self, "ptr_ai_btn_clear"))
    self.close_btn = QPushButton(_ptr_ui_tr(self, "ptr_ai_btn_close"))
    for _btn in (self.pipeline_btn, self.save_merged_btn, self.save_result_btn, self.clear_btn, self.close_btn):
        _btn.setMinimumWidth(180)
        row2.addWidget(_btn, 1)
    root.addLayout(row2)
    self.merge_btn.clicked.connect(lambda: _ptr_ai_dialog_run_remote_action_with_wait_v3(self, self._on_merge))
    self.postgres_btn.clicked.connect(lambda: _ptr_ai_dialog_run_remote_action_with_wait_v3(self, self._on_postgres))
    self.neo4j_btn.clicked.connect(lambda: _ptr_ai_dialog_run_remote_action_with_wait_v3(self, self._on_neo4j))
    self.save_sqlite_btn.clicked.connect(self._save_sqlite)
    self.pipeline_btn.clicked.connect(lambda: _ptr_ai_dialog_run_remote_action_with_wait_v3(self, self._on_pipeline))
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
    self.app_url_edit.setText("")
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
        app_url="",
    )
    setattr(cfg, "save_api_key", self.save_api_key_cb.isChecked())
    try:
        cfg._bk_prompt_owner = self.parent() if self.parent() is not None else self
    except Exception:
        cfg._bk_prompt_owner = self
    return cfg
def _ptr_ai_dialog_process_events_v3():
    try:
        app = QApplication.instance()
        if app is not None:
            app.processEvents()
    except Exception:
        pass

def _ptr_ai_dialog_graph_display_dispatch_v4(self):
    """Dispatch the OpenRouter graph button robustly.

    Some frozen builds instantiate the OpenRouter dialog before the canonical graph
    runtime hook has connected its own button slot. The button must still start the
    graph workflow immediately, therefore this dispatcher resolves the graph method
    lazily at click time and imports the hook module if necessary.
    """
    method = getattr(self, "_bk_generate_remote_canonical_and_show_graph", None)
    if not callable(method):
        try:
            from bottled_kraken.app_features import canonical_json_remote_person_table_hooks  # noqa: F401
        except Exception:
            pass
        method = getattr(self, "_bk_generate_remote_canonical_and_show_graph", None)
    if callable(method):
        try:
            return method()
        except Exception as exc:
            try:
                QMessageBox.warning(self, _ptr_ui_tr(self, "warn_title"), str(exc))
            except Exception:
                pass
            return None
    try:
        QMessageBox.warning(self, _ptr_ui_tr(self, "warn_title"), _ptr_ui_tr(self, "ptr_canonical_no_json"))
    except Exception:
        pass
    return None


def _ptr_ai_dialog_graph_load_dispatch_v5(self):
    """Load a canonical JSON file and open the graph view without OpenRouter."""
    method = getattr(self, "_bk_load_canonical_json_and_show_graph", None)
    if not callable(method):
        try:
            from bottled_kraken.app_features import canonical_json_remote_person_table_hooks  # noqa: F401
        except Exception:
            pass
        method = getattr(self, "_bk_load_canonical_json_and_show_graph", None)
    if callable(method):
        try:
            return method()
        except Exception as exc:
            try:
                QMessageBox.warning(self, _ptr_ui_tr(self, "warn_title"), str(exc))
            except Exception:
                pass
            return None
    try:
        QMessageBox.warning(self, _ptr_ui_tr(self, "warn_title"), _ptr_ui_tr(self, "ptr_canonical_no_json"))
    except Exception:
        pass
    return None

def _ptr_ai_dialog_run_remote_action_with_wait_v3(self, action):
    """Show the OpenRouter wait/cancel dialog immediately on the button click.

    The actual request still starts through _start_worker. This wrapper exists because
    users must see feedback before validation, prompt collection or worker creation can
    take noticeable time in frozen Windows builds.
    """
    worker = getattr(self, "_worker", None)
    if worker is not None:
        try:
            if worker.isRunning():
                _ptr_ai_dialog_show_wait_window_v2(self)
                _ptr_ai_dialog_process_events_v3()
                return
        except Exception:
            pass
    _ptr_ai_dialog_show_wait_window_v2(self)
    _ptr_ai_dialog_process_events_v3()
    try:
        action()
    except Exception as exc:
        _ptr_ai_dialog_hide_wait_window_v2(self)
        try:
            self._set_busy(False)
        except Exception:
            pass
        QMessageBox.warning(self, _ptr_ui_tr(self, "ptr_ai_tools_title"), str(exc))
        return
    worker = getattr(self, "_worker", None)
    try:
        if worker is None or not worker.isRunning():
            _ptr_ai_dialog_hide_wait_window_v2(self)
            self._set_busy(False)
    except Exception:
        pass

def _ptr_ai_dialog_set_busy_v2(self, busy: bool):
    for w in [self.merge_btn, self.postgres_btn, self.neo4j_btn, self.pipeline_btn,
              self.save_merged_btn, self.save_result_btn, getattr(self, "save_sqlite_btn", None), self.clear_btn, self.close_btn,
              getattr(self, "graph_display_btn", None), getattr(self, "graph_load_btn", None), getattr(self, "canonical_json_btn", None), getattr(self, "canonical_graph_btn", None),
              self.provider_edit, self.api_key_edit, self.model_edit, self.base_url_edit,
              self.temp_edit, self.timeout_edit, self.app_name_edit,
              self.save_api_key_cb]:
        if w is not None:
            w.setEnabled(not busy)
    if busy:
        self.progress_bar.setRange(0, 0)
    else:
        self.progress_bar.setRange(0, 100)
        current_text = (self.merged_edit.toPlainText().strip() or self.result_output_edit.toPlainText().strip())
        self.progress_bar.setValue(100 if current_text else 0)
        self.progress_label.setText(_ptr_ui_tr(self, "ptr_ai_progress_idle"))
    self.setCursor(Qt.WaitCursor if busy else Qt.ArrowCursor)
def _ptr_ai_dialog_show_wait_window_v2(self):
    try:
        existing = getattr(self, "_ptr_remote_wait_dialog", None)
        if existing is not None:
            try:
                existing.show()
                if hasattr(existing, "spinner"):
                    existing.spinner.start()
            except Exception:
                pass
            _ptr_ai_dialog_process_events_v3()
            return
    except Exception:
        pass
    dlg = PtrOpenRouterWaitDialog(self, lambda key, *args: _ptr_ui_tr(self, key, *args))
    dlg.cancel_requested.connect(lambda: _ptr_ai_dialog_cancel_remote_request_v2(self))
    self._ptr_remote_wait_dialog = dlg
    try:
        dlg.show()
        if hasattr(dlg, "spinner"):
            dlg.spinner.start()
    except Exception:
        pass
    _ptr_ai_dialog_process_events_v3()

def _ptr_ai_dialog_hide_wait_window_v2(self):
    dlg = getattr(self, "_ptr_remote_wait_dialog", None)
    if dlg is None:
        return
    try:
        dlg.mark_finished()
        dlg.hide()
        dlg.deleteLater()
    except Exception:
        pass
    self._ptr_remote_wait_dialog = None

def _ptr_ai_dialog_force_release_cancelled_worker_v2(self, worker):
    if worker is None or worker is not getattr(self, "_worker", None) or not worker.isRunning():
        return
    try:
        worker.result_ready.disconnect(self._on_worker_result)
    except Exception:
        pass
    try:
        worker.failed.disconnect(self._on_worker_failed)
    except Exception:
        pass
    try:
        worker.canceled.disconnect(self._on_worker_canceled)
    except Exception:
        pass
    abandoned = getattr(self, "_ptr_abandoned_remote_workers", None)
    if abandoned is None:
        abandoned = []
        self._ptr_abandoned_remote_workers = abandoned
    abandoned.append(worker)
    try:
        worker.finished.connect(lambda: abandoned.remove(worker) if worker in abandoned else None)
    except Exception:
        pass
    self._worker = None
    _ptr_ai_dialog_hide_wait_window_v2(self)
    self._set_busy(False)
    try:
        self.progress_label.setText(_ptr_ui_tr(self, "ptr_ai_cancelled_status"))
    except Exception:
        pass

def _ptr_ai_dialog_cancel_remote_request_v2(self):
    worker = getattr(self, "_worker", None)
    if worker is None or not worker.isRunning():
        _ptr_ai_dialog_hide_wait_window_v2(self)
        self._set_busy(False)
        return
    try:
        worker.cancel()
    except Exception:
        try:
            worker.requestInterruption()
        except Exception:
            pass
    QTimer.singleShot(1500, lambda w=worker: _ptr_ai_dialog_force_release_cancelled_worker_v2(self, w))

def _ptr_ai_dialog_worker_finished_v2(self):
    _ptr_ai_dialog_hide_wait_window_v2(self)
    self._set_busy(False)

def _ptr_ai_dialog_worker_canceled_v2(self, message: str):
    _ptr_ai_dialog_hide_wait_window_v2(self)
    self.progress_bar.setRange(0, 100)
    self.progress_bar.setValue(0)
    self.progress_label.setText(_ptr_ui_tr(self, "ptr_ai_cancelled_status"))

def _ptr_ai_dialog_start_worker_v2(self, mode: str, *, include_postgres: bool = True, include_neo4j: bool = True):
    if self._worker and self._worker.isRunning():
        _ptr_ai_dialog_show_wait_window_v2(self)
        return
    _ptr_ai_dialog_show_wait_window_v2(self)
    _ptr_ai_dialog_process_events_v3()
    try:
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
        try:
            self._worker.canceled.connect(self._on_worker_canceled)
        except Exception:
            pass
        self._worker.finished.connect(self._on_worker_finished)
        self._set_busy(True)
        _ptr_ai_dialog_show_wait_window_v2(self)
        _ptr_ai_dialog_process_events_v3()
        self._worker.start()
    except Exception:
        _ptr_ai_dialog_hide_wait_window_v2(self)
        try:
            self._set_busy(False)
        except Exception:
            pass
        raise

def _ptr_ai_dialog_worker_result_v2(self, payload):
    _ptr_ai_dialog_hide_wait_window_v2(self)
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
    _ptr_ai_dialog_hide_wait_window_v2(self)
    self.progress_bar.setRange(0, 100)
    self.progress_bar.setValue(0)
    self.progress_label.setText(_ptr_ui_tr(self, "ptr_ai_progress_idle"))
    QMessageBox.critical(self, _ptr_ui_tr(self, "ptr_ai_tools_title"), str(message))
def _ptr_ai_dialog_save_merged_v2(self):
    text = self.merged_edit.toPlainText().strip()
    if not text:
        QMessageBox.information(self, _ptr_ui_tr(self, "ptr_ai_tools_title"), _ptr_ui_tr(self, "ptr_ai_no_merged"))
        return
    path, _ = QFileDialog.getSaveFileName(self, _ptr_ui_tr(self, "ptr_ai_btn_save_merged"), "ai_merged.txt", _ptr_ui_tr(self, "ptr_filter_text_files"))
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
    path, _ = QFileDialog.getSaveFileName(self, _ptr_ui_tr(self, "ptr_ai_btn_save_result"), "ai_result.json", _ptr_ui_tr(self, "ptr_filter_json_text_files"))
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
PtrAIToolsDialog._on_worker_canceled = _ptr_ai_dialog_worker_canceled_v2
PtrAIToolsDialog._on_worker_finished = _ptr_ai_dialog_worker_finished_v2
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
def _ptr_sqlite_clean(value) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()
def _ptr_sqlite_split_name(full_name: str):
    txt = _ptr_sqlite_clean(full_name)
    txt = re.sub(r"\([^)]*\)", " ", txt)
    txt = re.sub(r"\s+", " ", txt).strip(" ,.;")
    if not txt:
        return "", ""
    parts = txt.split()
    if len(parts) == 1:
        return parts[0], ""
    return " ".join(parts[1:]), parts[0]
__all__ = [
    '_ptr_ai_build_postgres_json',
    '_ptr_ai_dialog_build_ui_v2',
    '_ptr_ai_dialog_cancel_remote_request_v2',
    '_ptr_ai_dialog_force_release_cancelled_worker_v2',
    '_ptr_ai_dialog_get_config_v2',
    '_ptr_ai_dialog_hide_wait_window_v2',
    '_ptr_ai_dialog_save_merged_v2',
    '_ptr_ai_dialog_save_result_v2',
    '_ptr_ai_dialog_set_busy_v2',
    '_ptr_ai_dialog_show_wait_window_v2',
    '_ptr_ai_dialog_set_config_v2',
    '_ptr_ai_dialog_start_worker_v2',
    '_ptr_ai_dialog_process_events_v3',
    '_ptr_ai_dialog_graph_display_dispatch_v4',
    '_ptr_ai_dialog_graph_load_dispatch_v5',
    '_ptr_ai_dialog_run_remote_action_with_wait_v3',
    '_ptr_ai_dialog_worker_canceled_v2',
    '_ptr_ai_dialog_worker_failed_v2',
    '_ptr_ai_dialog_worker_finished_v2',
    '_ptr_ai_dialog_worker_result_v2',
    '_ptr_feature_config_from_window',
    '_ptr_guess_person_name_from_line',
    '_ptr_mainwindow_close_wrapper_v2',
    '_ptr_mainwindow_init_wrapper_v2',
    '_ptr_mainwindow_retranslate_ui_wrapper_v2',
    '_ptr_prev_close_event',
    '_ptr_prev_mainwindow_init',
    '_ptr_prev_retranslate',
    '_ptr_remote_chat_completion',
    '_ptr_save_feature_config_to_window',
    '_ptr_source_lines_for_postgres',
    '_ptr_sqlite_clean',
    '_ptr_sqlite_split_name',
    '_ptr_unique_keep_order',
]
register_globals('ptr', globals(), __all__)
