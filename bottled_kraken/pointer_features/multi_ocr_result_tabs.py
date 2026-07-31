from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('ptr', globals())
try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QAbstractItemView, QTabBar
except Exception:
    Qt = None
    QAbstractItemView = None
    QTabBar = None
try:
    from bottled_kraken._main_window.ocr_variant_tabs import configure_ocr_variant_tab_buttons
except Exception:
    def configure_ocr_variant_tab_buttons(window):
        return None
_PTR_ADD_TAB_TEXT = "+"
def _ptr_clone_record_views(record_views):
    cloned = []
    for i, rv in enumerate(record_views or []):
        try:
            bbox = tuple(rv.bbox) if getattr(rv, "bbox", None) else None
            text = str(getattr(rv, "text", "") or "")
        except Exception:
            bbox = None
            text = str(rv or "")
        cloned.append(RecordView(i, text, bbox))
    return cloned
def _ptr_variant_label(window, index: int) -> str:
    try:
        return window._tr("multi_ocr_variant_tab", int(index) + 1)
    except Exception:
        return f"OCR ({int(index) + 1})"
def _ptr_variant_tooltip(window, index: int, model_name: str = "") -> str:
    label = _ptr_variant_label(window, index)
    if model_name:
        try:
            return window._tr("multi_ocr_variant_tooltip", int(index) + 1, model_name)
        except Exception:
            return f"{label}: {model_name}"
    return label
def _ptr_entry_from_task(task, index: int = 0, model_path: str = "", model_name: str = ""):
    text = ""
    kr_sorted = []
    recs = []
    if task is not None and getattr(task, "results", None):
        try:
            text, kr_sorted, _im, recs = task.results
        except Exception:
            text, kr_sorted, recs = "", [], []
    cloned = _ptr_clone_record_views(recs or [])
    if not cloned and text:
        cloned = _ptr_recs_from_text(text)
    if not text and cloned:
        text = "\n".join(rv.text for rv in cloned).strip()
    return {
        "run_index": int(index) + 1,
        "model_path": str(model_path or ""),
        "model_name": str(model_name or _ptr_model_display_name(model_path)),
        "text": str(text or ""),
        "kr_sorted": kr_sorted or [],
        "record_views": cloned,
        "undo_stack": list(getattr(task, "undo_stack", []) or []) if task is not None else [],
        "redo_stack": list(getattr(task, "redo_stack", []) or []) if task is not None else [],
        "edited": bool(getattr(task, "edited", False)) if task is not None else False,
    }
def _ptr_variant_entries_from_raw(raw_variants):
    entries = []
    for index, item in enumerate(raw_variants or [], start=1):
        if isinstance(item, dict):
            text = str(item.get("text", "") or "")
            model_path = str(item.get("model_path", "") or "")
            model_name = str(item.get("model_name", "") or _ptr_model_display_name(model_path))
            kr_sorted = item.get("kr_sorted", []) or []
            record_views = _ptr_clone_record_views(item.get("record_views", []) or [])
            undo_stack = list(item.get("undo_stack", []) or [])
            redo_stack = list(item.get("redo_stack", []) or [])
            edited = bool(item.get("edited", False))
        else:
            text = str(item or "")
            model_path = ""
            model_name = ""
            kr_sorted = []
            record_views = _ptr_recs_from_text(text)
            undo_stack = []
            redo_stack = []
            edited = False
        if not record_views and text.strip():
            record_views = _ptr_recs_from_text(text)
        if not text.strip() and record_views:
            text = "\n".join(rv.text for rv in record_views).strip()
        entries.append({
            "run_index": index,
            "model_path": model_path,
            "model_name": model_name,
            "text": text,
            "kr_sorted": kr_sorted,
            "record_views": record_views,
            "undo_stack": undo_stack,
            "redo_stack": redo_stack,
            "edited": edited,
        })
    return entries
def _ptr_task_image_object(task):
    if task is not None and getattr(task, "results", None):
        try:
            return task.results[2]
        except Exception:
            pass
    return None
def _ptr_get_task(self, path: str):
    try:
        return _ptr_find_task(self, path)
    except Exception:
        return next((t for t in getattr(self, "queue_items", []) if getattr(t, "path", "") == path), None)
def _ptr_entries_for_path(self, path: str, create: bool = True):
    path = str(path or "")
    if not path:
        return []
    if not hasattr(self, "_ptr_multi_ocr_variant_meta_by_path"):
        self._ptr_multi_ocr_variant_meta_by_path = {}
    if not hasattr(self, "_ptr_multi_ocr_variants_by_path"):
        self._ptr_multi_ocr_variants_by_path = {}
    raw = self._ptr_multi_ocr_variant_meta_by_path.get(path)
    entries = _ptr_variant_entries_from_raw(raw)
    task = _ptr_get_task(self, path)
    if create and not entries:
        if task is not None and getattr(task, "results", None):
            entries = [_ptr_entry_from_task(task, 0)]
        else:
            entries = [_ptr_blank_entry(0)]
    if entries:
        self._ptr_multi_ocr_variant_meta_by_path[path] = entries
        self._ptr_multi_ocr_variants_by_path[path] = [entry.get("text", "") for entry in entries]
    return entries
def _ptr_save_active_variant(self):
    if getattr(self, "_ptr_variant_loading", False):
        return
    path = str(getattr(self, "_ptr_active_multi_ocr_path", "") or "")
    index = int(getattr(self, "_ptr_active_multi_ocr_index", -1) or -1)
    if not path or index < 0:
        return
    task = _ptr_get_task(self, path)
    entries = _ptr_entries_for_path(self, path, create=False)
    if task is None or not entries or index >= len(entries):
        return
    try:
        if hasattr(self, "_persist_loaded_preview_bboxes"):
            self._persist_loaded_preview_bboxes()
        elif hasattr(self, "_persist_live_canvas_bboxes"):
            self._persist_live_canvas_bboxes(task)
    except Exception:
        pass
    entries[index] = _ptr_entry_from_task(
        task,
        index,
        entries[index].get("model_path", ""),
        entries[index].get("model_name", ""),
    )
    self._ptr_multi_ocr_variant_meta_by_path[path] = entries
    self._ptr_multi_ocr_variants_by_path[path] = [entry.get("text", "") for entry in entries]
def _ptr_apply_variant(self, path: str, index: int, save_current: bool = True):
    path = str(path or "")
    if not path:
        return
    if save_current:
        _ptr_save_active_variant(self)
    entries = _ptr_entries_for_path(self, path, create=True)
    if not entries:
        return
    index = max(0, min(int(index or 0), len(entries) - 1))
    task = _ptr_get_task(self, path)
    if task is None:
        return
    image_obj = _ptr_task_image_object(task)
    task.results = _ptr_entry_to_results(entries[index], image_obj)
    task.status = STATUS_DONE
    task.edited = bool(entries[index].get("edited", False))
    try:
        task.undo_stack = list(entries[index].get("undo_stack", []) or [])
        task.redo_stack = list(entries[index].get("redo_stack", []) or [])
    except Exception:
        pass
    self._ptr_active_multi_ocr_path = path
    self._ptr_active_multi_ocr_index = index
    if not hasattr(self, "_ptr_multi_ocr_active_index_by_path"):
        self._ptr_multi_ocr_active_index_by_path = {}
    self._ptr_multi_ocr_active_index_by_path[path] = index
    try:
        self._ptr_variant_loading = True
        self.load_results(path, persist_current=False)
    except TypeError:
        self.load_results(path)
    finally:
        self._ptr_variant_loading = False
def _ptr_place_tabs(self, tabs):
    if tabs is None or not hasattr(self, "list_lines") or self.list_lines is None:
        return
    try:
        parent = self.list_lines.parentWidget()
        layout = parent.layout() if parent is not None else None
        if layout is None or layout.indexOf(tabs) >= 0:
            return
        idx = layout.indexOf(self.list_lines)
        if idx >= 0:
            layout.insertWidget(idx + 1, tabs, 0)
        else:
            layout.addWidget(tabs)
    except Exception:
        pass
def _ptr_ensure_tabs(self):
    if QTabBar is None:
        return None
    tabs = getattr(self, "_ptr_multi_ocr_tabs", None) or getattr(self, "ocr_variant_tabs", None)
    if tabs is None:
        tabs = QTabBar(self)
        tabs.setObjectName("ocr_variant_tabs")
        tabs.setExpanding(False)
        tabs.setMovable(False)
        tabs.setDrawBase(True)
        try:
            tabs.setUsesScrollButtons(True)
        except Exception:
            pass
    else:
        try:
            tabs.setObjectName("ocr_variant_tabs")
        except Exception:
            pass
    try:
        tabs.setExpanding(False)
        tabs.setMovable(False)
        tabs.setDrawBase(True)
    except Exception:
        pass
    if not getattr(self, "_ptr_ocr_variant_tabs_connected", False):
        try:
            tabs.currentChanged.connect(lambda index: _ptr_on_tab_changed(self, index))
            self._ptr_ocr_variant_tabs_connected = True
        except Exception:
            pass
    self._ptr_multi_ocr_tabs = tabs
    self.ocr_variant_tabs = tabs
    _ptr_place_tabs(self, tabs)
    return tabs
def _ptr_refresh_tabs(self, path: str = ""):
    tabs = _ptr_ensure_tabs(self)
    if tabs is None:
        return
    path = str(path or _ptr_current_path(self) or "")
    entries = _ptr_entries_for_path(self, path, create=bool(path)) if path else []
    if not hasattr(self, "_ptr_multi_ocr_active_index_by_path"):
        self._ptr_multi_ocr_active_index_by_path = {}
    active = int(self._ptr_multi_ocr_active_index_by_path.get(path, 0) or 0) if entries else 0
    active = max(0, min(active, max(0, len(entries) - 1)))
    try:
        self._ptr_updating_variant_tabs = True
        tabs.blockSignals(True)
        while tabs.count() > 0:
            tabs.removeTab(0)
        count = max(1, len(entries))
        for index in range(count):
            label = _ptr_variant_label(self, index)
            tab_index = tabs.addTab(label)
            model_name = entries[index].get("model_name", "") if index < len(entries) else ""
            try:
                tabs.setTabToolTip(tab_index, _ptr_variant_tooltip(self, index, model_name))
            except Exception:
                pass
        plus_index = tabs.addTab(_PTR_ADD_TAB_TEXT)
        try:
            tabs.setTabToolTip(plus_index, self._tr("multi_ocr_variant_add_tooltip"))
        except Exception:
            pass
        tabs.setCurrentIndex(active)
        tabs.setVisible(True)
        try:
            tabs.setMinimumHeight(max(24, tabs.sizeHint().height()))
        except Exception:
            pass
        try:
            configure_ocr_variant_tab_buttons(self)
        except Exception:
            pass
        tabs.blockSignals(False)
    finally:
        self._ptr_updating_variant_tabs = False
    try:
        tabs.updateGeometry()
        tabs.repaint()
    except Exception:
        pass
def _ptr_add_variant(self, path: str):
    path = str(path or _ptr_current_path(self) or "")
    if not path:
        return False
    _ptr_save_active_variant(self)
    entries = _ptr_entries_for_path(self, path, create=True)
    entries.append(_ptr_blank_entry(len(entries)))
    self._ptr_multi_ocr_variant_meta_by_path[path] = entries
    self._ptr_multi_ocr_variants_by_path[path] = [entry.get("text", "") for entry in entries]
    self._ptr_multi_ocr_active_index_by_path[path] = len(entries) - 1
    _ptr_refresh_tabs(self, path)
    _ptr_apply_variant(self, path, len(entries) - 1, save_current=False)
    return True
__all__ = [
    '_PTR_ADD_TAB_TEXT',
    '_ptr_add_variant',
    '_ptr_apply_variant',
    '_ptr_clone_record_views',
    '_ptr_ensure_tabs',
    '_ptr_entries_for_path',
    '_ptr_entry_from_task',
    '_ptr_get_task',
    '_ptr_place_tabs',
    '_ptr_refresh_tabs',
    '_ptr_save_active_variant',
    '_ptr_task_image_object',
    '_ptr_variant_entries_from_raw',
    '_ptr_variant_label',
    '_ptr_variant_tooltip',
]
register_globals('ptr', globals(), __all__)
