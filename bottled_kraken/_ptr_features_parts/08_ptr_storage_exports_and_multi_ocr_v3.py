def _ptr_store_ai_postgres_v3(self, path: str, data: dict):
    if not isinstance(data, dict):
        return
    self._ptr_ai_postgres_by_path[path] = data
    self.status_bar.showMessage(_ptr_ui_tr(self, "ptr_postgres_done", os.path.basename(path)), 3000)

def _ptr_store_ai_neo4j_v3(self, path: str, data: dict):
    if not isinstance(data, dict):
        return
    self._ptr_ai_neo4j_by_path[path] = data
    self.status_bar.showMessage(_ptr_ui_tr(self, "ptr_neo4j_done", os.path.basename(path)), 3000)

def _ptr_export_ai_merge_for_current_v3(self, path: str):
    text = self._ptr_ai_merged_by_path.get(path, "")
    default_name = f"{os.path.splitext(os.path.basename(path))[0]}_ai_merge.txt"
    self._ptr_export_text_interactive(text, _ptr_ui_tr(self, "ptr_export_ai_merge"), default_name)

def _ptr_export_ai_postgres_for_current_v3(self, path: str):
    data = self._ptr_ai_postgres_by_path.get(path)
    default_name = f"{os.path.splitext(os.path.basename(path))[0]}_postgres.json"
    self._ptr_export_json_interactive(data, _ptr_ui_tr(self, "ptr_export_postgres_json"), default_name)

def _ptr_export_ai_neo4j_for_current_v3(self, path: str):
    data = self._ptr_ai_neo4j_by_path.get(path)
    default_name = f"{os.path.splitext(os.path.basename(path))[0]}_neo4j.json"
    self._ptr_export_json_interactive(data, _ptr_ui_tr(self, "ptr_export_neo4j_json"), default_name)

def _ptr_open_multi_followup_for_path_v3(self, path: str):
    variants = self._ptr_multi_ocr_variants_by_path.get(path, [])
    if not variants:
        QMessageBox.information(self, _ptr_ui_tr(self, "ptr_multi_ocr_title"), _ptr_ui_tr(self, "ptr_multi_no_variants"))
        return
    self._ptr_last_multi_followup_path = path
    choice = PtrMultiOCRFollowupDialog.get_choice(self)
    if choice == PtrMultiOCRFollowupDialog.CHOICE_CANCEL:
        return
    if choice == PtrMultiOCRFollowupDialog.CHOICE_LOCAL:
        self._ptr_apply_local_merge_to_task(path)
        return
    if choice == PtrMultiOCRFollowupDialog.CHOICE_AI:
        self._ptr_open_ai_tools(path, auto_mode=None)
        return
    if choice == PtrMultiOCRFollowupDialog.CHOICE_AI_POSTGRES:
        self._ptr_open_ai_tools(path, auto_mode="postgres")
        return
    if choice == PtrMultiOCRFollowupDialog.CHOICE_AI_NEO4J:
        self._ptr_open_ai_tools(path, auto_mode="neo4j")
        return
    if choice == PtrMultiOCRFollowupDialog.CHOICE_AI_BOTH:
        self._ptr_open_ai_tools(path, auto_mode="pipeline")
        return

def _ptr_reopen_multi_followup_v3(self):
    target = getattr(self, "_ptr_last_multi_followup_path", None)
    if not target:
        QMessageBox.information(self, _ptr_ui_tr(self, "ptr_multi_ocr_title"), _ptr_ui_tr(self, "ptr_multi_no_followup"))
        return
    self._ptr_open_multi_followup_for_path(target)

def _ptr_start_multi_ocr_v3(self):
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
    for p in dlg.selected_recognition_paths():
        if p and p not in seen:
            rec_paths.append(p)
            seen.add(p)
    if not rec_paths:
        QMessageBox.warning(self, self._tr("warn_title"), _ptr_ui_tr(self, "ptr_multi_select_rec_model"))
        return
    seg_path = self.seg_model_path if dlg.use_segmentation() else None
    if not seg_path or not os.path.exists(seg_path):
        QMessageBox.warning(self, self._tr("warn_title"), _ptr_ui_tr(self, "ptr_multi_select_seg_model"))
        return
    tasks = _ptr_current_or_selected_target_tasks(self)
    tasks = [t for t in tasks if t.path and os.path.exists(t.path)]
    if not tasks:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_queue_empty"))
        return
    job = PtrMultiOCRJob(
        input_paths=[t.path for t in tasks],
        recognition_model_paths=rec_paths,
        segmentation_model_path=seg_path,
        device=self.device_str,
        reading_direction=self.reading_direction,
        runs=dlg.runs(),
    )
    self._ptr_multi_processed_paths = []
    self._ptr_multi_ocr_worker = PtrMultiOCRWorker(job, parent=self)
    self._ptr_multi_ocr_worker.file_started.connect(self._ptr_on_multi_file_started)
    self._ptr_multi_ocr_worker.file_done.connect(self._ptr_on_multi_file_done)
    self._ptr_multi_ocr_worker.file_error.connect(self._ptr_on_multi_file_error)
    self._ptr_multi_ocr_worker.progress.connect(self.on_progress_update)
    self._ptr_multi_ocr_worker.finished_batch.connect(self._ptr_on_multi_batch_finished)
    self._ptr_multi_ocr_worker.failed.connect(self._ptr_on_multi_failed)
    self._ptr_multi_ocr_worker.device_resolved.connect(self.on_device_resolved)
    self._ptr_multi_ocr_worker.gpu_info.connect(self.on_gpu_info)
    self.act_play.setEnabled(False)
    self.act_stop.setEnabled(True)
    if hasattr(self, "act_ptr_multi_ocr"):
        self.act_ptr_multi_ocr.setEnabled(False)
    self._set_progress_busy()
    self._ptr_multi_ocr_worker.start()

def _ptr_on_multi_file_started_v3(self, path: str):
    task = _ptr_find_task(self, path)
    if task:
        task.status = STATUS_PROCESSING
        self._update_queue_row(path)
    self.status_bar.showMessage(_ptr_ui_tr(self, "ptr_multi_status_running", os.path.basename(path)), 1500)

def _ptr_on_multi_file_error_v3(self, path: str, message: str):
    task = _ptr_find_task(self, path)
    if task:
        task.status = STATUS_ERROR
        self._update_queue_row(path)
    self.status_bar.showMessage(_ptr_ui_tr(self, "ptr_multi_status_error", os.path.basename(path)), 3000)
    self._log(f"Multi-OCR Fehler: {os.path.basename(path)} -> {message}")

def _ptr_on_multi_batch_finished_v3(self):
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
    self.status_bar.showMessage(_ptr_ui_tr(self, "ptr_multi_status_finished"), 3000)
    if target:
        self._ptr_open_multi_followup_for_path(target)

def _ptr_on_multi_failed_v3(self, message: str):
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
    QMessageBox.critical(self, _ptr_ui_tr(self, "ptr_multi_ocr_title"), str(message))

def _ptr_open_ai_tools_for_current_task_v3(self):
    task = self._current_task()
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), _ptr_ui_tr(self, "ptr_select_file_first"))
        return
    self._ptr_open_ai_tools(task.path)

def _ptr_queue_context_menu_v3(self, pos):
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
    multi_ocr_act = menu.addAction(_ptr_ui_tr(self, "ptr_multi_ocr_btn"))
    ai_revise_act = menu.addAction(self._tr("act_ai_revise"))
    ai_tools_act = menu.addAction(_ptr_ui_tr(self, "ptr_ai_tools_title"))
    menu.addSeparator()
    export_merge_act = menu.addAction(_ptr_ui_tr(self, "ptr_export_ai_merge"))
    export_pg_act = menu.addAction(_ptr_ui_tr(self, "ptr_export_postgres_json"))
    export_neo_act = menu.addAction(_ptr_ui_tr(self, "ptr_export_neo4j_json"))
    open_followup_act = menu.addAction(_ptr_ui_tr(self, "ptr_ai_followup_open"))
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

def _ptr_mainwindow_stop_ocr_wrapper_v3(self, *args, **kwargs):
    worker = getattr(self, "_ptr_multi_ocr_worker", None)
    if worker and worker.isRunning():
        try:
            worker.requestInterruption()
            self.status_bar.showMessage(_ptr_ui_tr(self, "ptr_multi_status_cancel"), 2000)
        except Exception:
            pass
    return _old_mainwindow_stop_ocr(self, *args, **kwargs)

PtrMultiOcrDialog.__init__ = _ptr_multi_dialog_init_v3

PtrMultiOCRFollowupDialog.__init__ = _ptr_followup_init_v3

PtrAIToolsDialog._save_merged = _ptr_ai_dialog_save_merged_v3

PtrAIToolsDialog._save_result = _ptr_ai_dialog_save_result_v3

MainWindow._ptr_install_feature_actions = _ptr_install_feature_actions_v3

MainWindow._ptr_apply_local_merge_to_task = _ptr_apply_local_merge_to_task_v3

MainWindow._ptr_open_ai_tools = _ptr_open_ai_tools_v3

MainWindow._ptr_store_ai_merge = _ptr_store_ai_merge_v3

MainWindow._ptr_store_ai_postgres = _ptr_store_ai_postgres_v3

MainWindow._ptr_store_ai_neo4j = _ptr_store_ai_neo4j_v3

MainWindow._ptr_export_ai_merge_for_current = _ptr_export_ai_merge_for_current_v3

MainWindow._ptr_export_ai_postgres_for_current = _ptr_export_ai_postgres_for_current_v3

MainWindow._ptr_export_ai_neo4j_for_current = _ptr_export_ai_neo4j_for_current_v3

MainWindow._ptr_open_multi_followup_for_path = _ptr_open_multi_followup_for_path_v3

MainWindow.ptr_reopen_multi_followup = _ptr_reopen_multi_followup_v3

MainWindow.ptr_start_multi_ocr = _ptr_start_multi_ocr_v3

MainWindow._ptr_on_multi_file_started = _ptr_on_multi_file_started_v3

MainWindow._ptr_on_multi_file_error = _ptr_on_multi_file_error_v3

MainWindow._ptr_on_multi_batch_finished = _ptr_on_multi_batch_finished_v3

MainWindow._ptr_on_multi_failed = _ptr_on_multi_failed_v3

MainWindow.ptr_open_ai_tools_for_current_task = _ptr_open_ai_tools_for_current_task_v3

MainWindow.queue_context_menu = _ptr_queue_context_menu_v3

MainWindow.stop_ocr = _ptr_mainwindow_stop_ocr_wrapper_v3

def _ptr_remove_toolbar_feature_buttons_v4(window):
    toolbar = getattr(window, "toolbar", None)
    if toolbar is None:
        return
    targets = []
    for action in list(toolbar.actions()):
        txt = (action.text() or "").strip().lower().replace("&", "")
        if action in {
            getattr(window, "act_ptr_multi_ocr", None),
            getattr(window, "act_ptr_ai_tools", None),
        }:
            targets.append(action)
            continue
        if txt in {
            "multi-ocr",
            "ai tools",
            "openrouter-ki",
            "openrouter ai",
            "ia openrouter",
        }:
            targets.append(action)
    for action in targets:
        try:
            widget = toolbar.widgetForAction(action)
        except Exception:
            widget = None
        try:
            toolbar.removeAction(action)
        except Exception:
            pass
        if widget is not None:
            try:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
            except Exception:
                pass

def _ptr_remove_secondary_feature_buttons_v4(window):
    for attr in ("btn_ptr_multi_ocr_bottom", "btn_ptr_openrouter_ai_bottom"):
        btn = getattr(window, attr, None)
        if btn is None:
            continue
        try:
            btn.hide()
        except Exception:
            pass
        try:
            parent = btn.parentWidget()
            if parent is not None and parent.layout() is not None:
                parent.layout().removeWidget(btn)
        except Exception:
            pass
        try:
            btn.setParent(None)
            btn.deleteLater()
        except Exception:
            pass
        try:
            delattr(window, attr)
        except Exception:
            pass
