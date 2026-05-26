"""MainWindow-Anbindung für finale OCR-Tab-Zustände."""

def _ocr_tab_load_results(self, path, *args, **kwargs):
    accepting = bool(getattr(self, "_ocr_tab_accepting_fresh", False))
    if not accepting and not getattr(self, "_ocr_tab_loading", False):
        current = str(getattr(self, "_ocr_tab_active_path", "") or "")
        if current and current != str(path or ""):
            _ocr_tab_save_active(self)
        task = _ocr_tab_find_task(self, path)
        if task is not None:
            entries = _ocr_tab_entries(task, create=True)
            idx = int(getattr(task, "ocr_tab_active_index", 0) or 0)
            idx = max(0, min(idx, len(entries) - 1))
            task.results = _ocr_tab_results_from_entry(entries[idx])
    result = _ORIGINAL_LOAD_RESULTS(self, path, *args, **kwargs) if callable(_ORIGINAL_LOAD_RESULTS) else None
    task = _ocr_tab_find_task(self, path)
    if task is not None:
        self._ocr_tab_active_path = str(getattr(task, "path", "") or "")
        _ocr_tab_refresh(self, task)
    return result

def _ocr_tab_preview_image(self, path, *args, **kwargs):
    if not getattr(self, "_ocr_tab_loading", False):
        _ocr_tab_save_active(self)
    task = _ocr_tab_find_task(self, path)
    if task is not None:
        entries = _ocr_tab_entries(task, create=True)
        idx = int(getattr(task, "ocr_tab_active_index", 0) or 0)
        idx = max(0, min(idx, len(entries) - 1))
        task.results = _ocr_tab_results_from_entry(entries[idx])
    result = _ORIGINAL_PREVIEW_IMAGE(self, path, *args, **kwargs) if callable(_ORIGINAL_PREVIEW_IMAGE) else None
    if task is not None:
        self._ocr_tab_active_path = str(path or "")
        _ocr_tab_refresh(self, task)
    return result

def _ocr_tab_start_ocr(self, *args, **kwargs):
    _ocr_tab_save_active(self)
    return _ORIGINAL_START_OCR(self, *args, **kwargs) if callable(_ORIGINAL_START_OCR) else None

def _ocr_tab_on_file_done(self, path, text, kr_records, im, recs):
    old = bool(getattr(self, "_ocr_tab_accepting_fresh", False))
    self._ocr_tab_accepting_fresh = True
    try:
        result = _ORIGINAL_ON_FILE_DONE(self, path, text, kr_records, im, recs) if callable(_ORIGINAL_ON_FILE_DONE) else None
    finally:
        self._ocr_tab_accepting_fresh = old
    task = _ocr_tab_find_task(self, path)
    if task is not None:
        entries = _ocr_tab_entries(task, create=True)
        idx = int(getattr(task, "ocr_tab_active_index", 0) or 0)
        idx = max(0, min(idx, len(entries) - 1))
        model_path = getattr(self, "model_path", "")
        old_entry = entries[idx] if 0 <= idx < len(entries) else {}
        fresh_entry = _ocr_tab_entry_from_results(getattr(task, "results", None), idx, model_path, _ocr_tab_model_name(model_path))
        fresh_entry["run_index"] = _ocr_tab_stable_number(old_entry, idx)
        fresh_entry["tab_name_custom"] = bool(old_entry.get("tab_name_custom", False))
        fresh_entry["tab_name"] = str(old_entry.get("tab_name", "") or "").strip() if fresh_entry["tab_name_custom"] else persistent_ocr_tab_name(self, str(old_entry.get("tab_name", "") or ""))
        entries[idx] = fresh_entry
        task.ocr_tab_variants = entries
        task.ocr_tab_active_index = idx
        _ocr_tab_refresh(self, task)
    return result

def _ocr_tab_multi_done(self, path, merged_text, last_sorted, im, last_views, variants):
    task = _ocr_tab_find_task(self, path)
    if task is None:
        return
    entries = []
    for i, raw in enumerate(variants or []):
        if isinstance(raw, dict):
            recs = _ocr_tab_clone_recs(raw.get("record_views", []) or [])
            text = str(raw.get("text", "") or "")
            if not recs and text:
                recs = _ocr_tab_recs_from_text(text)
            entry = _ocr_tab_entry_from_results(
                (text, raw.get("kr_records", []) or raw.get("kr_sorted", []) or [], im, recs),
                i,
                raw.get("model_path", ""),
                raw.get("model_name", ""),
            )
        else:
            text = str(raw or "")
            entry = _ocr_tab_entry_from_results((text, [], im, _ocr_tab_recs_from_text(text)), i)
        entries.append(entry)
    if not entries:
        entries = [_ocr_tab_entry_from_results((merged_text, last_sorted or [], im, last_views or []), 0)]
    for i, entry in enumerate(entries):
        entry["run_index"] = i + 1
    task.ocr_tab_variants = entries
    task.ocr_tab_active_index = 0
    task.status = STATUS_DONE
    task.results = _ocr_tab_results_from_entry(entries[0])
    try:
        task.undo_stack.clear(); task.redo_stack.clear()
    except Exception:
        pass
    try:
        self._update_queue_row(path)
    except Exception:
        pass
    self._ptr_multi_ocr_variant_meta_by_path = getattr(self, "_ptr_multi_ocr_variant_meta_by_path", {}) or {}
    self._ptr_multi_ocr_variants_by_path = getattr(self, "_ptr_multi_ocr_variants_by_path", {}) or {}
    self._ptr_multi_ocr_variant_meta_by_path[path] = entries
    self._ptr_multi_ocr_variants_by_path[path] = [entry.get("text", "") for entry in entries]
    self._ptr_last_multi_followup_path = path
    if not hasattr(self, "_ptr_multi_processed_paths"):
        self._ptr_multi_processed_paths = []
    self._ptr_multi_processed_paths.append(path)
    current = _ocr_tab_find_task(self)
    if current is not None and getattr(current, "path", "") == path:
        _ocr_tab_apply(self, path, 0, save_current=False)
    else:
        _ocr_tab_refresh(self, current)

def _ocr_tab_entry_to_project(entry):
    recs = _ocr_tab_clone_recs(entry.get("record_views", []) or [])
    return {
        "run_index": int(entry.get("run_index", 0) or 0),
        "model_path": str(entry.get("model_path", "") or ""),
        "model_name": str(entry.get("model_name", "") or ""),
        "text": str(entry.get("text", "") or ""),
        "record_views": [
            {"idx": int(rv.idx), "text": str(rv.text or ""), "bbox": list(rv.bbox) if rv.bbox else None}
            for rv in recs
        ],
        "edited": bool(entry.get("edited", False)),
        "tab_name": str(entry.get("tab_name", "") or ""),
        "tab_name_custom": bool(entry.get("tab_name_custom", False)),
    }

def _ocr_tab_entry_from_project(raw, index):
    if not isinstance(raw, dict):
        return _ocr_tab_entry_from_results((str(raw or ""), [], None, _ocr_tab_recs_from_text(str(raw or ""))), index)
    recs = []
    for i, item in enumerate(raw.get("record_views", []) or []):
        if not isinstance(item, dict):
            continue
        bbox = item.get("bbox")
        try:
            bbox = tuple(int(x) for x in bbox) if bbox else None
        except Exception:
            bbox = None
        recs.append(RecordView(i, str(item.get("text", "") or ""), bbox))
    text = str(raw.get("text", "") or "")
    if not recs and text:
        recs = _ocr_tab_recs_from_text(text)
    entry = _ocr_tab_entry_from_results((text, [], None, recs), index, raw.get("model_path", ""), raw.get("model_name", ""))
    entry["run_index"] = _ocr_tab_stable_number(raw, index)
    entry["edited"] = bool(raw.get("edited", False))
    raw_name = str(raw.get("tab_name", "") or "")
    entry["tab_name_custom"] = bool(raw.get("tab_name_custom", False))
    entry["tab_name"] = raw_name if entry["tab_name_custom"] else ("" if is_generated_ocr_tab_label(None, raw_name) else raw_name)
    return entry

def _ocr_tab_task_to_dict(self, task):
    payload = _ORIGINAL_TASK_TO_DICT(self, task) if callable(_ORIGINAL_TASK_TO_DICT) else {}
    try:
        if task is _ocr_tab_find_task(self):
            _ocr_tab_save_active(self)
        entries = _ocr_tab_entries(task, create=False)
        if entries:
            payload["ocr_variants"] = [_ocr_tab_entry_to_project(entry) for entry in entries]
            payload["active_ocr_variant_index"] = int(getattr(task, "ocr_tab_active_index", 0) or 0)
    except Exception:
        pass
    return payload

def _ocr_tab_task_from_dict(self, data):
    task = _ORIGINAL_TASK_FROM_DICT(self, data) if callable(_ORIGINAL_TASK_FROM_DICT) else None
    try:
        if task is not None and isinstance(data, dict):
            raw = data.get("ocr_variants") or []
            if raw:
                task.ocr_tab_variants = [_ocr_tab_entry_from_project(item, i) for i, item in enumerate(raw)]
                task.ocr_tab_active_index = max(0, min(int(data.get("active_ocr_variant_index", 0) or 0), len(task.ocr_tab_variants) - 1))
                task.results = _ocr_tab_results_from_entry(task.ocr_tab_variants[task.ocr_tab_active_index])
    except Exception:
        pass
    return task

def _ocr_tab_retranslate(self):
    _ocr_tab_refresh(self, _ocr_tab_find_task(self))

try:
    MainWindow.load_results = _ocr_tab_load_results
    MainWindow.preview_image = _ocr_tab_preview_image
    MainWindow.start_ocr = _ocr_tab_start_ocr
    MainWindow.on_file_done = _ocr_tab_on_file_done
    MainWindow._ptr_on_multi_file_done = _ocr_tab_multi_done
    MainWindow._ptr_apply_multi_ocr_variant = _ocr_tab_apply
    MainWindow._ptr_add_ocr_variant_tab = _ocr_tab_add
    MainWindow._ptr_delete_ocr_variant_tab = _ocr_tab_delete
    MainWindow._ptr_rename_ocr_variant_tab = _ocr_tab_rename
    MainWindow._ptr_sync_active_multi_variant = _ocr_tab_save_active
    MainWindow._ptr_store_task_in_active_ocr_variant = lambda self, task=None, path="", **kw: _ocr_tab_save_active(self)
    MainWindow._ptr_refresh_ocr_variant_tabs_now = _ocr_tab_retranslate
    MainWindow._task_to_dict = _ocr_tab_task_to_dict
    MainWindow._task_from_dict = _ocr_tab_task_from_dict
    # Connected lambdas in older tab code resolve this global name at click time.
    _ptr_on_tab_changed = _ocr_tab_on_changed
    _ptr_apply_variant = _ocr_tab_apply
    _ptr_add_variant = _ocr_tab_add
    _ptr_delete_variant = _ocr_tab_delete
    _ptr_save_active_variant = _ocr_tab_save_active
    _ptr_refresh_tabs = lambda self, path="": _ocr_tab_refresh(self, _ocr_tab_find_task(self, path) if path else _ocr_tab_find_task(self))
except Exception:
    pass
