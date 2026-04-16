def _bk_lm_any_job_running(self) -> bool:
    return bool(
        (getattr(self, "ai_worker", None) and self.ai_worker.isRunning())
        or (getattr(self, "ai_batch_worker", None) and self.ai_batch_worker.isRunning())
        or (getattr(self, "_bk_local_json_worker", None) and self._bk_local_json_worker.isRunning())
    )

def _bk_lm_get_current_done_task(self):
    task = self._current_task()
    self._persist_live_canvas_bboxes(task)
    if not task or task.status != STATUS_DONE or not task.results:
        return None
    return task

def _bk_lm_run_current_line(self):
    task = _bk_lm_get_current_done_task(self)
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return
    row = self.list_lines.currentRow()
    if row < 0:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_select_line_first"))
        return
    self.run_ai_revision_for_single_line(row)

def _bk_lm_run_selected_lines(self):
    task = _bk_lm_get_current_done_task(self)
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return
    rows = self._selected_line_rows()
    if not rows:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_select_multiple_lines_first"))
        return
    self.run_ai_revision_for_selected_lines()

def _bk_lm_run_all_lines_current_task(self):
    task = _bk_lm_get_current_done_task(self)
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return
    model_id = self._resolve_ai_model_id()
    if not model_id:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_ai_model"))
        return
    if _bk_lm_any_job_running(self):
        return
    script_mode = self._choose_ai_script_mode()
    if not script_mode:
        return
    recs_for_ai = self._current_recs_for_ai(task)
    if not recs_for_ai:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return
    task.lm_locked_bboxes = [tuple(rv.bbox) if rv.bbox else None for rv in recs_for_ai]
    self.act_ai_revise.setEnabled(False)
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
        script_mode=AI_SCRIPT_PRINT,
        temperature=self.ai_temperature,
        top_p=self.ai_top_p,
        top_k=self.ai_top_k,
        presence_penalty=self.ai_presence_penalty,
        repetition_penalty=self.ai_repetition_penalty,
        min_p=self.ai_min_p,
        max_tokens=self.ai_max_tokens,
        tr_func=self._tr,
        parent=self,
    )
    self.ai_worker.progress_changed.connect(self.ai_progress_dialog.set_progress)
    self.ai_worker.status_changed.connect(self.ai_progress_dialog.set_status)
    self.ai_worker.status_changed.connect(self._log)
    self.ai_worker.finished_revision.connect(self.on_ai_revision_done)
    self.ai_worker.failed_revision.connect(self.on_ai_revision_failed)
    self.ai_worker.start()

def _bk_lm_collect_current_text(self, task) -> str:
    recs = self._current_recs_for_ai(task)
    return "\n".join((_clean_ocr_text(rv.text) for rv in recs if _clean_ocr_text(rv.text))).strip()

def _bk_lm_cancel_local_json(self):
    worker = getattr(self, "_bk_local_json_worker", None)
    if worker is not None and worker.isRunning():
        worker.cancel()

def _bk_lm_show_json_preview(self, schema_kind: str, data: Dict[str, Any], task_path: str):
    schema_kind = (schema_kind or "postgres").strip().lower()
    if schema_kind == "neo4j":
        title = self._tr("dlg_json_preview_title_neo4j")
        hint = self._tr("dlg_json_preview_hint_neo4j")
        suffix = "_neo4j.json"
    else:
        title = self._tr("dlg_json_preview_title_postgres")
        hint = self._tr("dlg_json_preview_hint_postgres")
        suffix = "_postgres.json"
    default_name = f"{os.path.splitext(os.path.basename(task_path))[0]}{suffix}"
    dlg = BKJsonPreviewDialog(self, self._tr, title, hint, data, default_name)
    self._bk_last_json_preview = dlg
    dlg.exec()

def _bk_lm_on_local_json_done(self, path: str, schema_kind: str, data: dict):
    worker = getattr(self, "_bk_local_json_worker", None)
    if worker is not None:
        try:
            worker.deleteLater()
        except Exception:
            pass
    self._bk_local_json_worker = None
    self._bk_local_json_context = None
    self.act_ai_revise.setEnabled(True)
    if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
        self.btn_ai_revise_bottom.setEnabled(True)
    if hasattr(self, "_bk_local_json_dialog") and self._bk_local_json_dialog:
        try:
            self._bk_local_json_dialog.close()
        except Exception:
            pass
        self._bk_local_json_dialog = None
    kind = (schema_kind or "postgres").strip().lower()
    if kind == "neo4j":
        self._ptr_ai_neo4j_by_path[path] = data
        self.status_bar.showMessage(self._tr("msg_local_json_done_neo4j"), 4000)
    else:
        self._ptr_ai_postgres_by_path[path] = data
        self.status_bar.showMessage(self._tr("msg_local_json_done_postgres"), 4000)
    self._log(self._tr_log("log_local_json_done", os.path.basename(path), _bk_json_schema_kind_label(self, kind)))
    _bk_lm_show_json_preview(self, kind, data, path)

def _bk_lm_on_local_json_failed(self, path: str, schema_kind: str, msg: str):
    worker = getattr(self, "_bk_local_json_worker", None)
    if worker is not None:
        try:
            worker.deleteLater()
        except Exception:
            pass
    self._bk_local_json_worker = None
    self._bk_local_json_context = None
    self.act_ai_revise.setEnabled(True)
    if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
        self.btn_ai_revise_bottom.setEnabled(True)
    if hasattr(self, "_bk_local_json_dialog") and self._bk_local_json_dialog:
        try:
            self._bk_local_json_dialog.close()
        except Exception:
            pass
        self._bk_local_json_dialog = None
    msg_l = (msg or "").lower()
    cancelled = any(token in msg_l for token in ("abgebrochen", "cancelled", "canceled", "annul"))
    if cancelled:
        self.status_bar.showMessage(self._tr("msg_local_json_cancelled"), 4000)
    else:
        self.status_bar.showMessage(self._tr("msg_local_json_failed"), 4000)
        QMessageBox.warning(self, self._tr("warn_title"), msg)
    self._log(self._tr_log("log_local_json_failed", os.path.basename(path), _bk_json_schema_kind_label(self, schema_kind), msg))

def _bk_lm_generate_local_json(self, schema_kind: str):
    task = _bk_lm_get_current_done_task(self)
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return
    source_text = _bk_lm_collect_current_text(self, task)
    if not source_text:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_no_text_for_json"))
        return
    model_id = self._resolve_ai_model_id()
    if not model_id:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_ai_model"))
        return
    if _bk_lm_any_job_running(self):
        return
    kind = (schema_kind or "postgres").strip().lower()
    self._bk_local_json_context = {"path": task.path, "schema_kind": kind}
    self.act_ai_revise.setEnabled(False)
    if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
        self.btn_ai_revise_bottom.setEnabled(False)
    if kind == "neo4j":
        self.status_bar.showMessage(self._tr("msg_local_json_started_neo4j"))
        wait_text = self._tr("dlg_local_json_wait_text_neo4j")
    else:
        self.status_bar.showMessage(self._tr("msg_local_json_started_postgres"))
        wait_text = self._tr("dlg_local_json_wait_text_postgres")
    self._log(self._tr_log("log_local_json_started", os.path.basename(task.path), _bk_json_schema_kind_label(self, kind)))
    title_key = "dlg_local_json_title_neo4j" if kind == "neo4j" else "dlg_local_json_title_postgres"
    self._bk_local_json_dialog = BusyStatusDialog(self._tr(title_key), wait_text, self._tr, self)
    self._bk_local_json_dialog.cancel_requested.connect(lambda: _bk_lm_cancel_local_json(self))
    self._bk_local_json_dialog.show()
    self._bk_local_json_worker = BKLocalStructuredJsonWorker(
        path=task.path,
        source_text=source_text,
        schema_kind=kind,
        lm_model=model_id,
        endpoint=self.ai_endpoint,
        enable_thinking=self.ai_enable_thinking,
        temperature=self.ai_temperature,
        top_p=self.ai_top_p,
        top_k=self.ai_top_k,
        presence_penalty=self.ai_presence_penalty,
        repetition_penalty=self.ai_repetition_penalty,
        min_p=self.ai_min_p,
        max_tokens=max(int(getattr(self, "ai_max_tokens", 1200) or 1200), 2200),
        tr_func=self._tr,
        parent=self,
    )
    self._bk_local_json_worker.status_changed.connect(self._log)
    self._bk_local_json_worker.finished_json.connect(lambda path, kind, data: _bk_lm_on_local_json_done(self, path, kind, data))
    self._bk_local_json_worker.failed_json.connect(lambda path, kind, msg: _bk_lm_on_local_json_failed(self, path, kind, msg))
    self._bk_local_json_worker.start()

def _bk_lm_update_dropdown_state(self):
    if not hasattr(self, "act_ai_menu_current_line"):
        return
    task = _bk_lm_get_current_done_task(self)
    has_task = bool(task)
    row = self.list_lines.currentRow() if hasattr(self, "list_lines") else -1
    selected_rows = self._selected_line_rows() if hasattr(self, "_selected_line_rows") else []
    busy = _bk_lm_any_job_running(self)
    self.act_ai_menu_current_line.setEnabled(has_task and row >= 0 and not busy)
    self.act_ai_menu_selected_lines.setEnabled(has_task and len(selected_rows) > 0 and not busy)
    self.act_ai_menu_all_lines.setEnabled(has_task and not busy)
    self.act_ai_menu_postgres.setEnabled(has_task and not busy)
    self.act_ai_menu_neo4j.setEnabled(has_task and not busy)

def _bk_lm_install_dropdown_menu(self):
    if getattr(self, "_bk_lm_dropdown_installed", False):
        _bk_lm_update_dropdown_state(self)
        return
    self._bk_lm_dropdown_installed = True
    self.act_ai_menu_current_line = QAction(self._tr("lm_menu_current_line"), self)
    self.act_ai_menu_selected_lines = QAction(self._tr("lm_menu_selected_lines"), self)
    self.act_ai_menu_all_lines = QAction(self._tr("lm_menu_all_lines"), self)
    self.act_ai_menu_postgres = QAction(self._tr("lm_menu_generate_postgres"), self)
    self.act_ai_menu_neo4j = QAction(self._tr("lm_menu_generate_neo4j"), self)
    self.act_ai_menu_current_line.triggered.connect(lambda: _bk_lm_run_current_line(self))
    self.act_ai_menu_selected_lines.triggered.connect(lambda: _bk_lm_run_selected_lines(self))
    self.act_ai_menu_all_lines.triggered.connect(lambda: _bk_lm_run_all_lines_current_task(self))
    self.act_ai_menu_postgres.triggered.connect(lambda: _bk_lm_generate_local_json(self, "postgres"))
    self.act_ai_menu_neo4j.triggered.connect(lambda: _bk_lm_generate_local_json(self, "neo4j"))
    self.btn_ai_revise_menu = QMenu(self)
    self.btn_ai_revise_menu.aboutToShow.connect(lambda: _bk_lm_update_dropdown_state(self))
    self.btn_ai_revise_menu.addAction(self.act_ai_menu_current_line)
    self.btn_ai_revise_menu.addAction(self.act_ai_menu_selected_lines)
    self.btn_ai_revise_menu.addAction(self.act_ai_menu_all_lines)
    self.btn_ai_revise_menu.addSeparator()
    self.btn_ai_revise_menu.addAction(self.act_ai_menu_postgres)
    self.btn_ai_revise_menu.addAction(self.act_ai_menu_neo4j)
    try:
        self.btn_ai_revise_bottom.clicked.disconnect()
    except Exception:
        pass
    self.btn_ai_revise_bottom.setMenu(self.btn_ai_revise_menu)
    self.btn_ai_revise_bottom.setPopupMode(QToolButton.InstantPopup)
    self.btn_ai_revise_bottom.setToolTip(self._tr("btn_ai_revise_menu_tip"))
    _bk_lm_update_dropdown_state(self)

def _bk_lm_retranslate_dropdown(self):
    if not getattr(self, "_bk_lm_dropdown_installed", False):
        return
    self.act_ai_menu_current_line.setText(self._tr("lm_menu_current_line"))
    self.act_ai_menu_selected_lines.setText(self._tr("lm_menu_selected_lines"))
    self.act_ai_menu_all_lines.setText(self._tr("lm_menu_all_lines"))
    self.act_ai_menu_postgres.setText(self._tr("lm_menu_generate_postgres"))
    self.act_ai_menu_neo4j.setText(self._tr("lm_menu_generate_neo4j"))
    if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
        self.btn_ai_revise_bottom.setToolTip(self._tr("btn_ai_revise_menu_tip"))
    _bk_lm_update_dropdown_state(self)

_bk_prev_mainwindow_init_v8 = MainWindow.__init__

_bk_prev_mainwindow_retranslate_v8 = MainWindow.retranslate_ui

def _bk_mainwindow_init_wrapper_v8(self, *args, **kwargs):
    _bk_prev_mainwindow_init_v8(self, *args, **kwargs)
    self._bk_local_json_worker = None
    self._bk_local_json_context = None
    self._bk_local_json_dialog = None
    self._bk_last_json_preview = None
    if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
        _bk_lm_install_dropdown_menu(self)

def _bk_mainwindow_retranslate_wrapper_v8(self, *args, **kwargs):
    _bk_prev_mainwindow_retranslate_v8(self, *args, **kwargs)
    _bk_lm_retranslate_dropdown(self)

MainWindow.__init__ = _bk_mainwindow_init_wrapper_v8

MainWindow.retranslate_ui = _bk_mainwindow_retranslate_wrapper_v8

MainWindow._bk_lm_install_dropdown_menu = _bk_lm_install_dropdown_menu

MainWindow._bk_lm_retranslate_dropdown = _bk_lm_retranslate_dropdown

MainWindow._bk_lm_generate_local_json = _bk_lm_generate_local_json

MainWindow._bk_lm_run_all_lines_current_task = _bk_lm_run_all_lines_current_task

_BK_PERSON_ROLE_STOPWORDS = {
    "b", "u", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "v", "w",
    "und", "et", "and", "oder", "or", "ou",
    "firma", "inh", "inhaber", "fabr", "fabrik", "fabrikant", "kaufm", "kaufmann", "wwe", "verw",
    "restaurateur", "mechaniker", "maurer", "parquetfußboden", "parquetfussboden", "parqueteur",
    "sattler", "schmied", "schneider", "bäcker", "baecker", "friseur", "musiker", "händler",
    "haendler", "handlung", "meister", "arbeiter", "beamter", "steueraufseher", "rettungsträger",
    "zeitungsträger", "zeitungstraeger", "glaserobermeister", "decorationsmaler", "decorationsmaler",
}

_BK_NAME_PREFIXES = {"von", "van", "de", "del", "der", "den", "du", "la", "le", "zu", "zur", "zum"}

_BK_NAME_TITLES_PATTERN = re.compile(r'^(herrn?|frau|frl\.?|hr\.?|hrn\.?|mme\.?|m\.?|dr\.?|prof\.?|professor)\s+', re.IGNORECASE)

def _bk_clean_name_fragment(value: Any) -> str:
    txt = _clean_ocr_text(value)
    txt = re.sub(r'^[\-–—\s]+', '', txt)
    txt = re.sub(r'\s+', ' ', txt).strip(' ,;:|')
    txt = _BK_NAME_TITLES_PATTERN.sub('', txt).strip(' ,;:|')
    return txt
