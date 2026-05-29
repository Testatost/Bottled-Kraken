from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('ptr', globals())
_VARIANT_PREV_LOAD_RESULTS = globals().get("_PTR_PREV_LOAD_RESULTS") or getattr(MainWindow, "load_results", None)
_VARIANT_PREV_PREVIEW_IMAGE = globals().get("_PTR_PREV_PREVIEW_IMAGE") or getattr(MainWindow, "preview_image", None)
_VARIANT_PREV_ON_FILE_DONE = getattr(MainWindow, "on_file_done", None)
_VARIANT_PREV_SYNC = getattr(MainWindow, "_sync_ui_after_recs_change", None)
_VARIANT_PREV_MULTI_DONE = getattr(MainWindow, "_ptr_on_multi_file_done", None)
_VARIANT_PREV_TASK_TO_DICT = getattr(MainWindow, "_task_to_dict", None)
_VARIANT_PREV_TASK_FROM_DICT = getattr(MainWindow, "_task_from_dict", None)
def _variant_load_results(self, path: str, *args, **kwargs):
    accepting_fresh_ocr = bool(getattr(self, "_ocr_variant_accepting_ocr_result", False))
    if not getattr(self, "_ocr_variant_loading", False) and not accepting_fresh_ocr:
        old_path = str(getattr(self, "_ocr_active_path", "") or "")
        if old_path and old_path != str(path or ""):
            _ptr_save_active_variant(self)
        task = _ptr_find_task(self, path)
        if task is not None:
            entries = _ptr_ensure_entries(self, path, create=True)
            index = int(self._ocr_active_variant_by_path.get(path, 0) or 0)
            index = max(0, min(index, len(entries) - 1)) if entries else 0
            if entries:
                task.results = _ptr_entry_to_results(entries[index])
                task.status = STATUS_DONE
    result = _VARIANT_PREV_LOAD_RESULTS(self, path, *args, **kwargs) if callable(_VARIANT_PREV_LOAD_RESULTS) else None
    self._ocr_active_path = str(path or "")
    self._ocr_active_index = int(getattr(self, "_ocr_active_variant_by_path", {}).get(path, 0) or 0)
    if not accepting_fresh_ocr:
        _ptr_refresh_tabs(self, path)
    return result
def _variant_preview_image(self, path: str, *args, **kwargs):
    if not getattr(self, "_ocr_variant_loading", False):
        _ptr_save_active_variant(self)
    result = _VARIANT_PREV_PREVIEW_IMAGE(self, path, *args, **kwargs) if callable(_VARIANT_PREV_PREVIEW_IMAGE) else None
    try:
        _ptr_ensure_entries(self, path, create=True)
        self._ocr_active_path = str(path or "")
        self._ocr_active_index = int(self._ocr_active_variant_by_path.get(path, 0) or 0)
        _ptr_refresh_tabs(self, path)
    except Exception:
        pass
    return result
def _variant_on_file_done(self, path, text, kr_records, im, recs):
    old_flag = bool(getattr(self, "_ocr_variant_accepting_ocr_result", False))
    self._ocr_variant_accepting_ocr_result = True
    try:
        result = _VARIANT_PREV_ON_FILE_DONE(self, path, text, kr_records, im, recs) if callable(_VARIANT_PREV_ON_FILE_DONE) else None
    finally:
        self._ocr_variant_accepting_ocr_result = old_flag
    try:
        task = _ptr_find_task(self, path)
        if task is not None:
            _ptr_store_task_in_variant(self, task=task, path=path, model_path=getattr(self, "model_path", ""))
            _ptr_refresh_tabs(self, path)
    except Exception:
        pass
    return result
def _variant_sync(self, task, keep_row=None):
    result = _VARIANT_PREV_SYNC(self, task, keep_row=keep_row) if callable(_VARIANT_PREV_SYNC) else None
    try:
        if task is not None and not getattr(self, "_ocr_variant_loading", False):
            _ptr_store_task_in_variant(self, task=task, path=getattr(task, "path", ""))
            _ptr_refresh_tabs(self, getattr(task, "path", ""))
    except Exception:
        pass
    return result
def _variant_multi_done(self, path, merged_text, last_sorted, im, last_views, variants):
    result = _VARIANT_PREV_MULTI_DONE(self, path, merged_text, last_sorted, im, last_views, variants) if callable(_VARIANT_PREV_MULTI_DONE) else None
    try:
        entries = []
        for i, raw in enumerate(variants or []):
            if isinstance(raw, dict):
                recs = _ptr_clone_recs(raw.get("record_views", []) or [])
                text = str(raw.get("text", "") or "")
                if not recs and text:
                    recs = _ptr_recs_from_text(text)
                entry = _ptr_entry_from_results(
                    (text, raw.get("kr_sorted", []) or [], im, recs),
                    i,
                    raw.get("model_path", ""),
                    raw.get("model_name", ""),
                )
            else:
                entry = _ptr_entry_from_results((str(raw or ""), [], im, _ptr_recs_from_text(str(raw or ""))), i)
            entries.append(entry)
        if not entries:
            entries = [_ptr_entry_from_results((merged_text, last_sorted or [], im, last_views or []), 0)]
        _ptr_ensure_stores(self)
        self._ocr_variants_by_path[path] = entries
        self._ocr_active_variant_by_path[path] = 0
        task = _ptr_find_task(self, path)
        if task is not None:
            task.status = STATUS_DONE
            task.results = _ptr_entry_to_results(entries[0])
            try:
                self._update_queue_row(path)
            except Exception:
                pass
        current = _ptr_find_task(self)
        if current is not None and getattr(current, "path", "") == path:
            _ptr_apply_variant(self, path, 0, save_current=False)
        else:
            _ptr_refresh_tabs(self, _ptr_current_path(self))
    except Exception:
        pass
    return result
def _variant_task_to_dict(self, task):
    payload = _VARIANT_PREV_TASK_TO_DICT(self, task) if callable(_VARIANT_PREV_TASK_TO_DICT) else {}
    try:
        _ptr_store_task_in_variant(self, task=task, path=getattr(task, "path", ""))
        entries = _ptr_ensure_entries(self, getattr(task, "path", ""), create=False)
        if entries:
            payload["ocr_variants"] = [_ptr_entry_to_project_dict(entry) for entry in entries]
            payload["active_ocr_variant_index"] = int(self._ocr_active_variant_by_path.get(getattr(task, "path", ""), 0) or 0)
    except Exception:
        pass
    return payload
def _variant_task_from_dict(self, data):
    task = _VARIANT_PREV_TASK_FROM_DICT(self, data) if callable(_VARIANT_PREV_TASK_FROM_DICT) else None
    try:
        if task is not None and isinstance(data, dict):
            raw = data.get("ocr_variants") or []
            if raw:
                entries = [_ptr_entry_from_project_dict(item, i) for i, item in enumerate(raw)]
                _ptr_ensure_stores(self)
                path = getattr(task, "path", "")
                self._ocr_variants_by_path[path] = entries
                active = max(0, min(int(data.get("active_ocr_variant_index", 0) or 0), len(entries) - 1))
                self._ocr_active_variant_by_path[path] = active
                task.results = _ptr_entry_to_results(entries[active])
    except Exception:
        pass
    return task
def _variant_retranslate_tabs(self):
    try:
        _ptr_refresh_tabs(self, _ptr_current_path(self))
    except Exception:
        pass
try:
    MainWindow.load_results = _variant_load_results
    MainWindow.preview_image = _variant_preview_image
    MainWindow.on_file_done = _variant_on_file_done
    MainWindow._sync_ui_after_recs_change = _variant_sync
    MainWindow._ptr_on_multi_file_done = _variant_multi_done
    MainWindow._task_to_dict = _variant_task_to_dict
    MainWindow._task_from_dict = _variant_task_from_dict
    MainWindow._ptr_show_multi_ocr_variant_tabs = _ptr_show_multi_ocr_variant_tabs
    MainWindow._ptr_apply_multi_ocr_variant = _ptr_apply_variant
    MainWindow._ptr_add_ocr_variant_tab = _ptr_add_variant
    MainWindow._ptr_delete_ocr_variant_tab = _ptr_delete_variant
    MainWindow._ptr_store_task_in_active_ocr_variant = _ptr_store_task_in_variant
    MainWindow._ptr_refresh_ocr_variant_tabs_now = _variant_retranslate_tabs
except Exception:
    pass
__all__ = [
    '_VARIANT_PREV_LOAD_RESULTS',
    '_VARIANT_PREV_MULTI_DONE',
    '_VARIANT_PREV_ON_FILE_DONE',
    '_VARIANT_PREV_PREVIEW_IMAGE',
    '_VARIANT_PREV_SYNC',
    '_VARIANT_PREV_TASK_FROM_DICT',
    '_VARIANT_PREV_TASK_TO_DICT',
    '_variant_load_results',
    '_variant_multi_done',
    '_variant_on_file_done',
    '_variant_preview_image',
    '_variant_retranslate_tabs',
    '_variant_sync',
    '_variant_task_from_dict',
    '_variant_task_to_dict',
]
register_globals('ptr', globals(), __all__)
