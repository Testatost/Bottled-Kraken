from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('ptr', globals())
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
    self.status_bar.showMessage(self._tr("msg_multi_ocr_done"), 3000)
    if target:
        self._ptr_open_multi_followup_for_path(target)
_old_mainwindow_all_workers = MainWindow._all_workers
def _ptr_mainwindow_init_wrapper(self, *args, **kwargs):
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
    try:
        self.ptr_update_feature_texts()
    except Exception:
        pass
def _ptr_mainwindow_all_workers_wrapper(self, *args, **kwargs):
    workers = list(_old_mainwindow_all_workers(self, *args, **kwargs))
    workers.append(getattr(self, "_ptr_multi_ocr_worker", None))
    return workers
from bottled_kraken.common.chain_consolidation import register_init_delta, register_retranslate_delta
register_init_delta(_ptr_mainwindow_init_wrapper)
register_retranslate_delta(_ptr_mainwindow_retranslate_ui_wrapper)
MainWindow._all_workers = _ptr_mainwindow_all_workers_wrapper
MainWindow._ptr_install_feature_actions = _ptr_install_feature_actions
MainWindow._ptr_on_multi_file_done = _ptr_on_multi_file_done
MainWindow._ptr_on_multi_batch_finished = _ptr_on_multi_batch_finished
MainWindow._ptr_open_multi_followup_for_path = _ptr_open_multi_followup_for_path
MainWindow.ptr_reopen_multi_followup = _ptr_reopen_multi_followup
MainWindow._ptr_apply_local_merge_to_task = _ptr_apply_local_merge_to_task
MainWindow._ptr_open_ai_tools = _ptr_open_ai_tools
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
    return translation.DEFAULT_LANGUAGE
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
__all__ = [
    '_old_mainwindow_all_workers',
    '_ptr_mainwindow_all_workers_wrapper',
    '_ptr_mainwindow_init_wrapper',
    '_ptr_mainwindow_retranslate_ui_wrapper',
    '_ptr_normalize_remote_base_url',
    '_ptr_on_multi_batch_finished',
    '_ptr_on_multi_file_done',
    '_ptr_ui_lang',
    '_ptr_ui_tr',
]
register_globals('ptr', globals(), __all__)
