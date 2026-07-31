from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('ptr', globals())
def _ptr_reopen_multi_followup_v3(self):
    target = getattr(self, "_ptr_last_multi_followup_path", None)
    if not target:
        QMessageBox.information(self, _ptr_ui_tr(self, "ptr_multi_ocr_title"), _ptr_ui_tr(self, "ptr_multi_no_followup"))
        return
    self._ptr_open_multi_followup_for_path(target)
def _ptr_on_multi_file_started_v3(self, path: str):
    task = _ptr_find_task(self, path)
    if task:
        task.status = STATUS_PROCESSING
        self._update_queue_row(path)
    self.status_bar.showMessage(_ptr_ui_tr(self, "ptr_multi_status_running", os.path.basename(path)), 1500)
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
def _ptr_open_ai_tools_for_current_task_v3(self):
    task = self._current_task()
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), _ptr_ui_tr(self, "ptr_select_file_first"))
        return
    self._ptr_open_ai_tools(task.path)
PtrMultiOcrDialog.__init__ = _ptr_multi_dialog_init_v3
PtrMultiOCRFollowupDialog.__init__ = _ptr_followup_init_v3
PtrAIToolsDialog._save_merged = _ptr_ai_dialog_save_merged_v3
PtrAIToolsDialog._save_result = _ptr_ai_dialog_save_result_v3
MainWindow.ptr_reopen_multi_followup = _ptr_reopen_multi_followup_v3
MainWindow._ptr_on_multi_file_started = _ptr_on_multi_file_started_v3
MainWindow._ptr_on_multi_batch_finished = _ptr_on_multi_batch_finished_v3
MainWindow.ptr_open_ai_tools_for_current_task = _ptr_open_ai_tools_for_current_task_v3
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
__all__ = [
    '_ptr_on_multi_batch_finished_v3',
    '_ptr_on_multi_file_started_v3',
    '_ptr_open_ai_tools_for_current_task_v3',
    '_ptr_remove_secondary_feature_buttons_v4',
    '_ptr_remove_toolbar_feature_buttons_v4',
    '_ptr_reopen_multi_followup_v3',
]
register_globals('ptr', globals(), __all__)
