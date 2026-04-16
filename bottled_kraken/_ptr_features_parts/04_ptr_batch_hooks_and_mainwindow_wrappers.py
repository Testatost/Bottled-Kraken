def _ptr_on_multi_file_started(self, path: str):
    task = _ptr_find_task(self, path)
    if task:
        task.status = STATUS_PROCESSING
        self._update_queue_row(path)
    self.status_bar.showMessage(f"Multi-OCR: {os.path.basename(path)}", 1500)

def _ptr_on_multi_file_done(self, path: str, merged_text: str, last_sorted: list, im: object,
                            last_views: list, variants: list):
    task = _ptr_find_task(self, path)
    if task:
        safe_views = [RecordView(i, str(rv.text), tuple(rv.bbox) if rv.bbox else None) for i, rv in enumerate(last_views or [])]
        merged_lines = [ln for ln in (merged_text or "").splitlines()]
        if merged_lines and len(merged_lines) == len(safe_views):
            final_recs = [RecordView(i, merged_lines[i], safe_views[i].bbox) for i in range(len(merged_lines))]
        else:
            final_recs = safe_views
        task.status = STATUS_DONE
        task.results = ("\n".join(rv.text for rv in final_recs).strip(), last_sorted or [], im, final_recs)
        task.edited = False
        task.undo_stack.clear()
        task.redo_stack.clear()
        self._update_queue_row(path)
        if self._current_task() and self._current_task().path == path:
            self.load_results(path)
    self._ptr_multi_ocr_variants_by_path[path] = [str(t) for t in (variants or []) if str(t).strip()]
    if (merged_text or "").strip():
        self._ptr_ai_merged_by_path[path] = merged_text.strip()
    self._ptr_last_multi_followup_path = path
    self._ptr_multi_processed_paths.append(path)

def _ptr_on_multi_file_error(self, path: str, message: str):
    task = _ptr_find_task(self, path)
    if task:
        task.status = STATUS_ERROR
        self._update_queue_row(path)
    self.status_bar.showMessage(f"Multi-OCR Fehler: {os.path.basename(path)}", 3000)
    self._log(f"Multi-OCR Fehler: {os.path.basename(path)} -> {message}")

def _ptr_on_multi_batch_finished(self):
    self.act_play.setEnabled(True)
    self.act_stop.setEnabled(False)
    if hasattr(self, "act_ptr_multi_ocr"):
        self.act_ptr_multi_ocr.setEnabled(True)
    self._set_progress_idle(100)
    worker = getattr(self, "_ptr_multi_ocr_worker", None)
    self._ptr_multi_ocr_worker = None
    if worker is not None:
        try:
            worker.deleteLater()
        except Exception:
            pass
    target = None
    current = self._current_task()
    if current and current.path in self._ptr_multi_ocr_variants_by_path:
        target = current.path
    elif getattr(self, "_ptr_multi_processed_paths", None):
        target = self._ptr_multi_processed_paths[-1]
    elif getattr(self, "_ptr_last_multi_followup_path", None):
        target = self._ptr_last_multi_followup_path
    self.status_bar.showMessage("Multi-OCR abgeschlossen.", 3000)
    if target:
        self._ptr_open_multi_followup_for_path(target)

def _ptr_on_multi_failed(self, message: str):
    self.act_play.setEnabled(True)
    self.act_stop.setEnabled(False)
    if hasattr(self, "act_ptr_multi_ocr"):
        self.act_ptr_multi_ocr.setEnabled(True)
    self._set_progress_idle(0)
    worker = getattr(self, "_ptr_multi_ocr_worker", None)
    self._ptr_multi_ocr_worker = None
    if worker is not None:
        try:
            worker.deleteLater()
        except Exception:
            pass
    QMessageBox.critical(self, "Multi-OCR", str(message))

def _ptr_open_ai_tools_for_current_task(self):
    task = self._current_task()
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), "Bitte zuerst eine Datei auswählen.")
        return
    self._ptr_open_ai_tools(task.path)

def _ptr_queue_context_menu(self, pos):
    item = self.queue_table.itemAt(pos)
    target_path = None
    task = None
    if item is not None:
        row = item.row()
        file_item = self.queue_table.item(row, QUEUE_COL_FILE)
        if file_item is not None:
            target_path = file_item.data(Qt.UserRole)
            task = _ptr_find_task(self, target_path)
    menu = QMenu()
    start_ocr_act = menu.addAction(self._tr("act_start_ocr"))
    multi_ocr_act = menu.addAction(_ptr_lang_text(self, "Multi-OCR", "Multi-OCR"))
    ai_revise_act = menu.addAction(self._tr("act_ai_revise"))
    ai_tools_act = menu.addAction(_ptr_lang_text(self, "AI Tools", "AI Tools"))
    menu.addSeparator()
    export_merge_act = menu.addAction("Export AI-Merge")
    export_pg_act = menu.addAction("Export PostgreSQL JSON")
    export_neo_act = menu.addAction("Export Neo4j JSON")
    open_followup_act = menu.addAction("Multi-OCR-Follow-up öffnen")
    has_merge = bool(target_path and (self._ptr_ai_merged_by_path.get(target_path) or "").strip())
    has_pg = bool(target_path and isinstance(self._ptr_ai_postgres_by_path.get(target_path), dict))
    has_neo = bool(target_path and isinstance(self._ptr_ai_neo4j_by_path.get(target_path), dict))
    has_multi = bool(target_path and self._ptr_multi_ocr_variants_by_path.get(target_path))
    export_merge_act.setEnabled(has_merge)
    export_pg_act.setEnabled(has_pg)
    export_neo_act.setEnabled(has_neo)
    open_followup_act.setEnabled(has_multi)
    menu.addSeparator()
    rename_act = menu.addAction(self._tr("act_rename"))
    delete_act = menu.addAction(self._tr("act_delete"))
    menu.addSeparator()
    check_all_act = menu.addAction(self._tr("queue_ctx_check_all"))
    uncheck_all_act = menu.addAction(self._tr("queue_ctx_uncheck_all"))
    action = menu.exec(self.queue_table.viewport().mapToGlobal(pos))
    if not action:
        return
    if action == start_ocr_act:
        self.start_ocr()
        return
    if action == multi_ocr_act:
        self.ptr_start_multi_ocr()
        return
    if action == ai_revise_act:
        self.run_ai_revision()
        return
    if action == ai_tools_act:
        if target_path:
            self._ptr_open_ai_tools(target_path)
        else:
            self.ptr_open_ai_tools_for_current_task()
        return
    if action == export_merge_act and target_path:
        self._ptr_export_ai_merge_for_current(target_path)
        return
    if action == export_pg_act and target_path:
        self._ptr_export_ai_postgres_for_current(target_path)
        return
    if action == export_neo_act and target_path:
        self._ptr_export_ai_neo4j_for_current(target_path)
        return
    if action == open_followup_act and target_path:
        self._ptr_open_multi_followup_for_path(target_path)
        return
    if action == check_all_act:
        self.check_all_queue_items()
        return
    if action == uncheck_all_act:
        self.uncheck_all_queue_items()
        return
    if action == rename_act and task:
        new_name, ok = QInputDialog.getText(self, self._tr("dlg_title_rename"), self._tr("dlg_label_name"), text=task.display_name)
        if ok:
            task.display_name = new_name
            self.queue_table.item(item.row(), QUEUE_COL_FILE).setText(new_name)
        return
    if action == delete_act:
        self.delete_selected_queue_items()

_old_mainwindow_init = MainWindow.__init__

_old_mainwindow_retranslate_ui = MainWindow.retranslate_ui

_old_mainwindow_stop_ocr = MainWindow.stop_ocr

_old_mainwindow_all_workers = MainWindow._all_workers

def _ptr_mainwindow_init_wrapper(self, *args, **kwargs):
    _old_mainwindow_init(self, *args, **kwargs)
    self.ptr_remote_ai_api_key = ""
    self._ptr_multi_ocr_worker = None
    self._ptr_multi_ocr_variants_by_path = {}
    self._ptr_ai_merged_by_path = {}
    self._ptr_ai_postgres_by_path = {}
    self._ptr_ai_neo4j_by_path = {}
    self._ptr_last_multi_followup_path = None
    self._ptr_multi_processed_paths = []
    self._ptr_last_ai_dialog = None
    self.ptr_remote_ai_api_key = getattr(self, "ptr_remote_ai_api_key", "") or ""
    self._ptr_install_feature_actions()

def _ptr_mainwindow_retranslate_ui_wrapper(self, *args, **kwargs):
    _old_mainwindow_retranslate_ui(self, *args, **kwargs)
    try:
        self.ptr_update_feature_texts()
    except Exception:
        pass

def _ptr_mainwindow_stop_ocr_wrapper(self, *args, **kwargs):
    worker = getattr(self, "_ptr_multi_ocr_worker", None)
    if worker and worker.isRunning():
        try:
            worker.requestInterruption()
            self.status_bar.showMessage("Breche Multi-OCR ab...", 2000)
        except Exception:
            pass
    return _old_mainwindow_stop_ocr(self, *args, **kwargs)

def _ptr_mainwindow_all_workers_wrapper(self, *args, **kwargs):
    workers = list(_old_mainwindow_all_workers(self, *args, **kwargs))
    workers.append(getattr(self, "_ptr_multi_ocr_worker", None))
    return workers

MainWindow.__init__ = _ptr_mainwindow_init_wrapper

MainWindow.retranslate_ui = _ptr_mainwindow_retranslate_ui_wrapper

MainWindow.stop_ocr = _ptr_mainwindow_stop_ocr_wrapper

MainWindow._all_workers = _ptr_mainwindow_all_workers_wrapper

MainWindow.queue_context_menu = _ptr_queue_context_menu

MainWindow._ptr_install_feature_actions = _ptr_install_feature_actions

MainWindow.ptr_update_feature_texts = _ptr_update_feature_texts

MainWindow.ptr_start_multi_ocr = _ptr_start_multi_ocr

MainWindow._ptr_on_multi_file_started = _ptr_on_multi_file_started

MainWindow._ptr_on_multi_file_done = _ptr_on_multi_file_done

MainWindow._ptr_on_multi_file_error = _ptr_on_multi_file_error

MainWindow._ptr_on_multi_batch_finished = _ptr_on_multi_batch_finished

MainWindow._ptr_on_multi_failed = _ptr_on_multi_failed

MainWindow._ptr_open_multi_followup_for_path = _ptr_open_multi_followup_for_path

MainWindow.ptr_reopen_multi_followup = _ptr_reopen_multi_followup

MainWindow._ptr_apply_local_merge_to_task = _ptr_apply_local_merge_to_task

MainWindow._ptr_open_ai_tools = _ptr_open_ai_tools

MainWindow.ptr_open_ai_tools_for_current_task = _ptr_open_ai_tools_for_current_task

MainWindow._ptr_store_ai_merge = _ptr_store_ai_merge

MainWindow._ptr_store_ai_postgres = _ptr_store_ai_postgres

MainWindow._ptr_store_ai_neo4j = _ptr_store_ai_neo4j

MainWindow._ptr_store_ai_pipeline = _ptr_store_ai_pipeline

MainWindow._ptr_export_text_interactive = _ptr_export_text_interactive

MainWindow._ptr_export_json_interactive = _ptr_export_json_interactive

MainWindow._ptr_export_ai_merge_for_current = _ptr_export_ai_merge_for_current

MainWindow._ptr_export_ai_postgres_for_current = _ptr_export_ai_postgres_for_current

MainWindow._ptr_export_ai_neo4j_for_current = _ptr_export_ai_neo4j_for_current

def _ptr_ui_lang(obj) -> str:
    try:
        lang = getattr(obj, "current_lang", None)
        if lang:
            return str(lang)
    except Exception:
        pass
    try:
        parent = obj.parent() if hasattr(obj, "parent") else None
        lang = getattr(parent, "current_lang", None)
        if lang:
            return str(lang)
    except Exception:
        pass
    return "de"

def _ptr_ui_tr(obj, key: str, *args):
    lang = _ptr_ui_lang(obj)
    try:
        return translation.translate(lang, key, *args)
    except Exception:
        return key

def _ptr_normalize_remote_base_url(base_url: str, provider_name: str = "") -> str:
    raw = (base_url or "").strip()
    if not raw:
        return ""
    raw = raw.replace("openrouterai/api", "openrouter.ai/api")
    raw = raw.replace("openrouterai", "openrouter.ai")
    if not re.match(r"^https?://", raw, flags=re.IGNORECASE):
        raw = "https://" + raw.lstrip("/")
    raw = re.sub(r"/chat/completions/?$", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"/completions/?$", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"/models/?$", "", raw, flags=re.IGNORECASE)
    if "openrouter.ai" in raw.lower() or (provider_name or "").strip().lower() == "openrouter":
        raw = re.sub(r"^https?://openrouterai", "https://openrouter.ai", raw, flags=re.IGNORECASE)
        if not re.search(r"/api/v1/?$", raw, flags=re.IGNORECASE):
            raw = raw.rstrip("/") + "/api/v1"
    elif raw.endswith("/v1/chat"):
        raw = raw[:-5]
    return raw.rstrip("/")
