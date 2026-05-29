from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('ptr', globals())
try:
    from bottled_kraken._main_window.ocr_variant_tabs import configure_ocr_variant_tab_buttons
except Exception:
    def configure_ocr_variant_tab_buttons(window):
        return None
_PTR_PLUS_TAB = "+"
def _ptr_model_display_name(path: str) -> str:
    try:
        return os.path.basename(str(path or "")) or str(path or "")
    except Exception:
        return str(path or "")
def _ptr_clone_recs(recs):
    out = []
    for i, rv in enumerate(recs or []):
        try:
            bbox = tuple(rv.bbox) if getattr(rv, "bbox", None) else None
            text = str(getattr(rv, "text", "") or "")
        except Exception:
            bbox = None
            text = str(rv or "")
        out.append(RecordView(i, text, bbox))
    return out
def _ptr_recs_from_text(text: str):
    return [RecordView(i, line, None) for i, line in enumerate(str(text or "").splitlines())]
def _ptr_entry_from_results(results, index: int = 0, model_path: str = "", model_name: str = ""):
    text = ""
    kr_records = []
    image_obj = None
    recs = []
    if results:
        try:
            text, kr_records, image_obj, recs = results
        except Exception:
            text, kr_records, image_obj, recs = "", [], None, []
    recs = _ptr_clone_recs(recs)
    if not recs and text:
        recs = _ptr_recs_from_text(text)
    if not text and recs:
        text = "\n".join(rv.text for rv in recs).strip()
    return {
        "run_index": int(index) + 1,
        "model_path": str(model_path or ""),
        "model_name": str(model_name or _ptr_model_display_name(model_path)),
        "text": str(text or ""),
        "kr_records": kr_records or [],
        "image": image_obj,
        "record_views": recs,
        "edited": False,
    }
def _ptr_blank_entry(index: int = 0):
    return _ptr_entry_from_results(("", [], None, []), index)
def _ptr_entry_to_results(entry):
    recs = _ptr_clone_recs(entry.get("record_views", []) or [])
    if not recs and entry.get("text"):
        recs = _ptr_recs_from_text(entry.get("text", ""))
    text = "\n".join(rv.text for rv in recs).strip()
    return text, entry.get("kr_records", []) or [], entry.get("image"), recs
def _ptr_visible_line_texts(self):
    texts = []
    tree = getattr(self, "list_lines", None)
    if tree is None:
        return texts
    try:
        count = tree.topLevelItemCount()
        for row in range(count):
            item = tree.topLevelItem(row)
            if item is not None:
                texts.append(str(item.text(1) or ""))
        return texts
    except Exception:
        pass
    try:
        count = tree.count()
        for row in range(count):
            item = tree.row_item(row) if hasattr(tree, "row_item") else None
            if item is not None:
                texts.append(str(item.text(1) or ""))
    except Exception:
        pass
    return texts
def _ptr_results_from_current_ui(self, task):
    if task is None:
        return None
    try:
        if hasattr(self, "_persist_loaded_preview_bboxes"):
            self._persist_loaded_preview_bboxes()
        elif hasattr(self, "_persist_live_canvas_bboxes"):
            self._persist_live_canvas_bboxes(task)
    except Exception:
        pass
    results = getattr(task, "results", None)
    if not results:
        return None
    try:
        text, kr_records, image_obj, recs = results
    except Exception:
        return results
    recs = _ptr_clone_recs(recs or [])
    visible = _ptr_visible_line_texts(self)
    if visible:
        new_recs = []
        for i, line_text in enumerate(visible):
            bbox = recs[i].bbox if i < len(recs) else None
            new_recs.append(RecordView(i, line_text, bbox))
        recs = new_recs
    text = "\n".join(rv.text for rv in recs).strip()
    return text, kr_records or [], image_obj, recs
def _ptr_find_task(self, path: str = ""):
    path = str(path or "")
    if path:
        return next((t for t in getattr(self, "queue_items", []) if getattr(t, "path", "") == path), None)
    try:
        task = self._current_task()
        if task is not None:
            return task
    except Exception:
        pass
    loaded = str(getattr(self, "_loaded_preview_path", "") or "")
    return next((t for t in getattr(self, "queue_items", []) if getattr(t, "path", "") == loaded), None)
def _ptr_current_path(self) -> str:
    task = _ptr_find_task(self)
    if task is not None:
        return str(getattr(task, "path", "") or "")
    return str(getattr(self, "_loaded_preview_path", "") or "")
def _ptr_label(self, index: int) -> str:
    try:
        return self._tr("multi_ocr_variant_tab", int(index) + 1)
    except Exception:
        return f"Reiter ({int(index) + 1})"
def _ptr_tooltip(self, index: int, entry=None) -> str:
    model = str((entry or {}).get("model_name", "") or (entry or {}).get("model_path", "") or "")
    if model:
        try:
            return self._tr("multi_ocr_variant_tooltip", int(index) + 1, model)
        except Exception:
            return f"{_ptr_label(self, index)}: {model}"
    return _ptr_label(self, index)
def _ptr_ensure_stores(self):
    canonical = getattr(self, "_ocr_variants_by_path", None)
    legacy_meta = getattr(self, "_ptr_multi_ocr_variant_meta_by_path", None)
    legacy_texts = getattr(self, "_ptr_multi_ocr_variants_by_path", None)
    if not isinstance(canonical, dict):
        canonical = {}
    if isinstance(legacy_meta, dict):
        for path, raw_entries in legacy_meta.items():
            if path not in canonical and raw_entries:
                entries = []
                for i, item in enumerate(raw_entries or []):
                    if isinstance(item, dict):
                        recs = _ptr_clone_recs(item.get("record_views", []) or [])
                        text = str(item.get("text", "") or "")
                        if not recs and text:
                            recs = _ptr_recs_from_text(text)
                        entries.append(_ptr_entry_from_results(
                            (text, item.get("kr_sorted", []) or item.get("kr_records", []) or [], item.get("image"), recs),
                            i,
                            item.get("model_path", ""),
                            item.get("model_name", ""),
                        ))
                    else:
                        text = str(item or "")
                        entries.append(_ptr_entry_from_results((text, [], None, _ptr_recs_from_text(text)), i))
                canonical[path] = entries
    if isinstance(legacy_texts, dict):
        for path, raw_texts in legacy_texts.items():
            if path not in canonical and raw_texts:
                canonical[path] = [
                    _ptr_entry_from_results((str(text or ""), [], None, _ptr_recs_from_text(str(text or ""))), i)
                    for i, text in enumerate(raw_texts or [])
                ]
    self._ocr_variants_by_path = canonical
    if not hasattr(self, "_ocr_active_variant_by_path") or not isinstance(self._ocr_active_variant_by_path, dict):
        self._ocr_active_variant_by_path = {}
    self._ptr_multi_ocr_variant_meta_by_path = self._ocr_variants_by_path
    self._ptr_multi_ocr_variants_by_path = {
        p: [e.get("text", "") for e in entries]
        for p, entries in self._ocr_variants_by_path.items()
    }
    self._ptr_multi_ocr_active_index_by_path = self._ocr_active_variant_by_path
def _ptr_ensure_entries(self, path: str, create: bool = True):
    _ptr_ensure_stores(self)
    path = str(path or "")
    if not path:
        return []
    entries = self._ocr_variants_by_path.get(path)
    if entries is None:
        raw = getattr(self, "_ptr_multi_ocr_variant_meta_by_path", {}).get(path) if hasattr(self, "_ptr_multi_ocr_variant_meta_by_path") else None
        if raw is None:
            raw = getattr(self, "_ptr_multi_ocr_variants_by_path", {}).get(path) if hasattr(self, "_ptr_multi_ocr_variants_by_path") else None
        entries = []
        for i, item in enumerate(raw or []):
            if isinstance(item, dict):
                recs = _ptr_clone_recs(item.get("record_views", []) or [])
                text = str(item.get("text", "") or "")
                if not recs and text:
                    recs = _ptr_recs_from_text(text)
                entries.append(_ptr_entry_from_results((text, item.get("kr_sorted", []) or item.get("kr_records", []) or [], item.get("image"), recs), i, item.get("model_path", ""), item.get("model_name", "")))
            else:
                text = str(item or "")
                entries.append(_ptr_entry_from_results((text, [], None, _ptr_recs_from_text(text)), i))
    if not entries and create:
        task = _ptr_find_task(self, path)
        if task is not None and getattr(task, "results", None):
            entries = [_ptr_entry_from_results(task.results, 0, getattr(self, "model_path", ""))]
        else:
            entries = [_ptr_blank_entry(0)]
    for i, entry in enumerate(entries or []):
        entry["run_index"] = i + 1
    self._ocr_variants_by_path[path] = entries or []
    self._ptr_multi_ocr_variant_meta_by_path = self._ocr_variants_by_path
    self._ptr_multi_ocr_variants_by_path[path] = [e.get("text", "") for e in self._ocr_variants_by_path[path]]
    return self._ocr_variants_by_path[path]
def _ptr_save_active_variant(self):
    if getattr(self, "_ocr_variant_loading", False):
        return
    path = str(getattr(self, "_ocr_active_path", "") or _ptr_current_path(self) or "")
    if not path:
        return
    task = _ptr_find_task(self, path)
    if task is None:
        return
    try:
        if hasattr(self, "_persist_loaded_preview_bboxes"):
            self._persist_loaded_preview_bboxes()
        elif hasattr(self, "_persist_live_canvas_bboxes"):
            self._persist_live_canvas_bboxes(task)
    except Exception:
        pass
    entries = _ptr_ensure_entries(self, path, create=True)
    index = int(getattr(self, "_ocr_active_index", self._ocr_active_variant_by_path.get(path, 0)) or 0)
    index = max(0, min(index, len(entries) - 1)) if entries else 0
    while index >= len(entries):
        entries.append(_ptr_blank_entry(len(entries)))
    old = entries[index] if index < len(entries) else {}
    entry = _ptr_entry_from_results(
        _ptr_results_from_current_ui(self, task) or getattr(task, "results", None),
        index,
        old.get("model_path", "") or getattr(self, "model_path", ""),
        old.get("model_name", ""),
    )
    entry["edited"] = bool(getattr(task, "edited", False))
    entries[index] = entry
    self._ocr_active_variant_by_path[path] = index
    self._ocr_active_path = path
    self._ocr_active_index = index
    self._ptr_multi_ocr_variants_by_path[path] = [e.get("text", "") for e in entries]
def _ptr_refresh_tabs(self, path: str = ""):
    tabs = getattr(self, "ocr_variant_tabs", None) or getattr(self, "_ptr_multi_ocr_tabs", None)
    if tabs is None:
        return
    path = str(path or _ptr_current_path(self) or "")
    entries = _ptr_ensure_entries(self, path, create=bool(path)) if path else [_ptr_blank_entry(0)]
    active = int(getattr(self, "_ocr_active_variant_by_path", {}).get(path, 0) or 0) if path else 0
    active = max(0, min(active, max(0, len(entries) - 1)))
    try:
        self._ocr_tabs_updating = True
        tabs.blockSignals(True)
        while tabs.count() > 0:
            tabs.removeTab(0)
        for i, entry in enumerate(entries or [_ptr_blank_entry(0)]):
            tab_index = tabs.addTab(_ptr_label(self, i))
            try:
                tabs.setTabToolTip(tab_index, _ptr_tooltip(self, i, entry))
            except Exception:
                pass
        plus_index = tabs.addTab(_PTR_PLUS_TAB)
        try:
            tabs.setTabToolTip(plus_index, self._tr("multi_ocr_variant_add_tooltip"))
        except Exception:
            pass
        tabs.setCurrentIndex(active)
        tabs.setVisible(True)
        try:
            configure_ocr_variant_tab_buttons(self)
        except Exception:
            pass
        tabs.blockSignals(False)
    finally:
        self._ocr_tabs_updating = False
    try:
        tabs.updateGeometry()
        tabs.repaint()
    except Exception:
        pass
def _ptr_apply_variant(self, path: str, index: int, save_current: bool = True):
    path = str(path or _ptr_current_path(self) or "")
    if not path:
        return False
    if save_current:
        _ptr_save_active_variant(self)
    task = _ptr_find_task(self, path)
    if task is None:
        return False
    entries = _ptr_ensure_entries(self, path, create=True)
    if not entries:
        entries = [_ptr_blank_entry(0)]
    index = max(0, min(int(index or 0), len(entries) - 1))
    self._ocr_variant_loading = True
    try:
        task.results = _ptr_entry_to_results(entries[index])
        task.status = STATUS_DONE
        task.edited = bool(entries[index].get("edited", False))
        self._ocr_active_path = path
        self._ocr_active_index = index
        self._ocr_active_variant_by_path[path] = index
        self._ptr_active_multi_ocr_path = path
        self._ptr_active_multi_ocr_index = index
        try:
            if callable(_VARIANT_PREV_LOAD_RESULTS):
                _VARIANT_PREV_LOAD_RESULTS(self, path, persist_current=False)
            elif hasattr(self, "load_results"):
                self.load_results(path, persist_current=False)
        finally:
            pass
    finally:
        self._ocr_variant_loading = False
    _ptr_refresh_tabs(self, path)
    return True
def _ptr_add_variant(self, path: str = ""):
    path = str(path or _ptr_current_path(self) or "")
    if not path:
        tabs = getattr(self, "ocr_variant_tabs", None)
        if tabs is not None:
            insert_at = max(0, tabs.count() - 1)
            tabs.insertTab(insert_at, _ptr_label(self, insert_at))
            tabs.setCurrentIndex(insert_at)
        return True
    _ptr_save_active_variant(self)
    entries = _ptr_ensure_entries(self, path, create=True)
    entries.append(_ptr_blank_entry(len(entries)))
    index = len(entries) - 1
    self._ocr_active_variant_by_path[path] = index
    self._ocr_active_path = path
    self._ocr_active_index = index
    _ptr_refresh_tabs(self, path)
    _ptr_apply_variant(self, path, index, save_current=False)
    return True
def _ptr_delete_variant(self, index: int):
    path = _ptr_current_path(self)
    if not path:
        return False
    _ptr_save_active_variant(self)
    entries = _ptr_ensure_entries(self, path, create=True)
    if not entries:
        entries = [_ptr_blank_entry(0)]
    index = int(index or 0)
    if not (0 <= index < len(entries)):
        return False
    active = int(self._ocr_active_variant_by_path.get(path, 0) or 0)
    if len(entries) <= 1:
        entries[:] = [_ptr_blank_entry(0)]
        active = 0
    else:
        entries.pop(index)
        if active > index:
            active -= 1
        elif active == index:
            active = min(index, len(entries) - 1)
    for i, entry in enumerate(entries):
        entry["run_index"] = i + 1
    self._ocr_active_variant_by_path[path] = max(0, min(active, len(entries) - 1))
    _ptr_refresh_tabs(self, path)
    _ptr_apply_variant(self, path, self._ocr_active_variant_by_path[path], save_current=False)
    return True
def _ptr_on_tab_changed(self, index: int):
    if getattr(self, "_ocr_tabs_updating", False) or getattr(self, "_ocr_variant_plus_handling", False):
        return
    tabs = getattr(self, "ocr_variant_tabs", None)
    if tabs is None or index < 0:
        return
    if index == tabs.count() - 1 or tabs.tabText(index).strip() == _PTR_PLUS_TAB:
        _ptr_add_variant(self)
        return
    _ptr_apply_variant(self, _ptr_current_path(self), index, save_current=True)
def _ptr_show_multi_ocr_variant_tabs(self, path: str = ""):
    _ptr_refresh_tabs(self, path)
def _ptr_store_task_in_variant(self, task=None, path: str = "", index=None, model_path: str = "", model_name: str = ""):
    task = task or _ptr_find_task(self, path or _ptr_current_path(self))
    if task is None:
        return False
    path = str(path or getattr(task, "path", "") or "")
    if not path:
        return False
    entries = _ptr_ensure_entries(self, path, create=True)
    if index is None:
        index = self._ocr_active_variant_by_path.get(path, getattr(self, "_ocr_active_index", 0))
    index = max(0, int(index or 0))
    while index >= len(entries):
        entries.append(_ptr_blank_entry(len(entries)))
    old = entries[index]
    entries[index] = _ptr_entry_from_results(
        _ptr_results_from_current_ui(self, task) or getattr(task, "results", None),
        index,
        model_path or old.get("model_path", "") or getattr(self, "model_path", ""),
        model_name or old.get("model_name", "") or _ptr_model_display_name(model_path or getattr(self, "model_path", "")),
    )
    entries[index]["edited"] = bool(getattr(task, "edited", False))
    self._ocr_active_variant_by_path[path] = index
    self._ocr_active_path = path
    self._ocr_active_index = index
    self._ptr_multi_ocr_variants_by_path[path] = [e.get("text", "") for e in entries]
    return True
def _ptr_entry_to_project_dict(entry):
    recs = _ptr_clone_recs(entry.get("record_views", []) or [])
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
    }
def _ptr_entry_from_project_dict(raw, index: int):
    if not isinstance(raw, dict):
        return _ptr_entry_from_results((str(raw or ""), [], None, _ptr_recs_from_text(str(raw or ""))), index)
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
        recs = _ptr_recs_from_text(text)
    entry = _ptr_entry_from_results((text, [], None, recs), index, raw.get("model_path", ""), raw.get("model_name", ""))
    entry["edited"] = bool(raw.get("edited", False))
    return entry
__all__ = [
    '_PTR_PLUS_TAB',
    '_ptr_add_variant',
    '_ptr_apply_variant',
    '_ptr_blank_entry',
    '_ptr_clone_recs',
    '_ptr_current_path',
    '_ptr_delete_variant',
    '_ptr_ensure_entries',
    '_ptr_ensure_stores',
    '_ptr_entry_from_project_dict',
    '_ptr_entry_from_results',
    '_ptr_entry_to_project_dict',
    '_ptr_entry_to_results',
    '_ptr_find_task',
    '_ptr_label',
    '_ptr_model_display_name',
    '_ptr_on_tab_changed',
    '_ptr_recs_from_text',
    '_ptr_refresh_tabs',
    '_ptr_results_from_current_ui',
    '_ptr_save_active_variant',
    '_ptr_show_multi_ocr_variant_tabs',
    '_ptr_store_task_in_variant',
    '_ptr_tooltip',
    '_ptr_visible_line_texts',
]
register_globals('ptr', globals(), __all__)
