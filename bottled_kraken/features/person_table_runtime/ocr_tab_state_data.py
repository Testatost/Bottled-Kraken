"""OCR tab state management."""

_ORIGINAL_LOAD_RESULTS = globals().get("_VARIANT_PREV_LOAD_RESULTS") or getattr(MainWindow, "load_results", None)
_ORIGINAL_PREVIEW_IMAGE = globals().get("_VARIANT_PREV_PREVIEW_IMAGE") or getattr(MainWindow, "preview_image", None)
_ORIGINAL_ON_FILE_DONE = globals().get("_VARIANT_PREV_ON_FILE_DONE") or getattr(MainWindow, "on_file_done", None)
_ORIGINAL_START_OCR = getattr(MainWindow, "start_ocr", None)
_ORIGINAL_TASK_TO_DICT = globals().get("_VARIANT_PREV_TASK_TO_DICT") or getattr(MainWindow, "_task_to_dict", None)
_ORIGINAL_TASK_FROM_DICT = globals().get("_VARIANT_PREV_TASK_FROM_DICT") or getattr(MainWindow, "_task_from_dict", None)

try:
    from bottled_kraken.main_window_mixins.ocr_variant_tabs import configure_ocr_variant_tab_buttons, ocr_variant_tab_display_text, ocr_variant_tab_plain_text
    from bottled_kraken.main_window_mixins.ocr_tab_name_utils import is_generated_ocr_tab_label, persistent_ocr_tab_name
except Exception:  # pragma: no cover
    def configure_ocr_variant_tab_buttons(window):
        return None
    def ocr_variant_tab_plain_text(text):
        value = str(text or "").strip()
        return value[:-1].rstrip() if value.endswith("×") else value
    def ocr_variant_tab_display_text(label):
        return ocr_variant_tab_plain_text(label) or "+"
    def is_generated_ocr_tab_label(window, text):
        return False
    def persistent_ocr_tab_name(window, text, fallback=""):
        value = ocr_variant_tab_plain_text(text)
        return value if value and value != "+" else ocr_variant_tab_plain_text(fallback)

def _ocr_tab_clone_recs(recs):
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

def _ocr_tab_recs_from_text(text: str):
    return [RecordView(i, line, None) for i, line in enumerate(str(text or "").splitlines())]

def _ocr_tab_model_name(path: str) -> str:
    try:
        return os.path.basename(str(path or "")) or str(path or "")
    except Exception:
        return str(path or "")

def _ocr_tab_entry_from_results(results, index=0, model_path="", model_name=""):
    text = ""
    kr_records = []
    image_obj = None
    recs = []
    if results:
        try:
            text, kr_records, image_obj, recs = results
        except Exception:
            text, kr_records, image_obj, recs = "", [], None, []
    recs = _ocr_tab_clone_recs(recs)
    if not recs and text:
        recs = _ocr_tab_recs_from_text(text)
    if not text and recs:
        text = "\n".join(rv.text for rv in recs).strip()
    return {
        "run_index": int(index) + 1,
        "model_path": str(model_path or ""),
        "model_name": str(model_name or _ocr_tab_model_name(model_path)),
        "text": str(text or ""),
        "kr_records": kr_records or [],
        "image": image_obj,
        "record_views": recs,
        "edited": False,
        "undo_stack": [],
        "redo_stack": [],
        "tab_name": "",
        "tab_name_custom": False,
    }

def _ocr_tab_blank_entry(index=0):
    return _ocr_tab_entry_from_results(("", [], None, []), index)

def _ocr_tab_results_from_entry(entry):
    recs = _ocr_tab_clone_recs((entry or {}).get("record_views", []) or [])
    if not recs and (entry or {}).get("text"):
        recs = _ocr_tab_recs_from_text((entry or {}).get("text", ""))
    text = "\n".join(rv.text for rv in recs).strip()
    return text, (entry or {}).get("kr_records", []) or [], (entry or {}).get("image"), recs

def _ocr_tab_default_label(self, index: int) -> str:
    try:
        return self._tr("multi_ocr_variant_tab", int(index) + 1)
    except Exception:
        return f"Tab ({int(index) + 1})"

def _ocr_tab_stable_number(entry, fallback: int = 0, used=None) -> int:
    try:
        number = int((entry or {}).get("run_index", 0) or 0)
    except Exception:
        number = 0
    if number <= 0 or (used is not None and number in used):
        number = max([int(fallback)] + list(used or set()) + [0]) + 1
    if used is not None:
        used.add(number)
    return number

def _ocr_tab_next_number(entries) -> int:
    return max([0] + [_ocr_tab_stable_number(entry, i) for i, entry in enumerate(entries or [])]) + 1

def _ocr_tab_next_visible_number(self, tabs) -> int:
    values = []
    try:
        for i in range(max(0, tabs.count() - 1)):
            text = ocr_variant_tab_plain_text(tabs.tabText(i))
            try:
                values.append(int(text.rsplit("(", 1)[1].split(")", 1)[0].strip()))
            except Exception:
                values.append(i + 1)
    except Exception:
        pass
    return max(values + [0]) + 1

def _ocr_tab_visible_tab_name(self, index: int, entry=None) -> str:
    old_name = str((entry or {}).get("tab_name", "") or "").strip()
    tabs = getattr(self, "ocr_variant_tabs", None)
    try:
        if tabs is not None and 0 <= int(index) < tabs.count():
            return persistent_ocr_tab_name(self, tabs.tabText(int(index)), old_name)
    except Exception:
        pass
    return persistent_ocr_tab_name(self, old_name)

def _ocr_tab_find_task(self, path=""):
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
    if loaded:
        return next((t for t in getattr(self, "queue_items", []) if getattr(t, "path", "") == loaded), None)
    return None

def _ocr_tab_current_path(self):
    task = _ocr_tab_find_task(self)
    if task is not None:
        return str(getattr(task, "path", "") or "")
    return str(getattr(self, "_loaded_preview_path", "") or "")

def _ocr_tab_normalize_entries(entries):
    normalized = []
    used_numbers = set()
    for i, item in enumerate(entries or []):
        if isinstance(item, dict):
            recs = _ocr_tab_clone_recs(item.get("record_views", []) or [])
            text = str(item.get("text", "") or "")
            if not recs and text:
                recs = _ocr_tab_recs_from_text(text)
            entry = _ocr_tab_entry_from_results(
                (text, item.get("kr_records", []) or item.get("kr_sorted", []) or [], item.get("image"), recs),
                i,
                item.get("model_path", ""),
                item.get("model_name", ""),
            )
            entry["edited"] = bool(item.get("edited", False))
            entry["undo_stack"] = list(item.get("undo_stack", []) or [])
            entry["redo_stack"] = list(item.get("redo_stack", []) or [])
            name = str(item.get("tab_name", "") or "")
            entry["tab_name_custom"] = bool(item.get("tab_name_custom", False))
            entry["tab_name"] = name if entry["tab_name_custom"] else ("" if is_generated_ocr_tab_label(None, name) else name)
        else:
            text = str(item or "")
            entry = _ocr_tab_entry_from_results((text, [], None, _ocr_tab_recs_from_text(text)), i)
        entry["run_index"] = _ocr_tab_stable_number(item if isinstance(item, dict) else entry, i, used_numbers)
        normalized.append(entry)
    return normalized

def _ocr_tab_entries(task, create=True):
    if task is None:
        return []
    entries = getattr(task, "ocr_tab_variants", None)
    if not isinstance(entries, list):
        entries = []
    entries = _ocr_tab_normalize_entries(entries)
    if not entries and create:
        if getattr(task, "results", None):
            entries = [_ocr_tab_entry_from_results(task.results, 0, getattr(task, "model_path", ""))]
        else:
            entries = [_ocr_tab_blank_entry(0)]
    task.ocr_tab_variants = entries
    if not hasattr(task, "ocr_tab_active_index"):
        task.ocr_tab_active_index = 0
    task.ocr_tab_active_index = max(0, min(int(task.ocr_tab_active_index or 0), max(0, len(entries) - 1)))
    return entries

def _ocr_tab_visible_texts(self):
    tree = getattr(self, "list_lines", None)
    texts = []
    if tree is None:
        return texts
    try:
        count = tree.topLevelItemCount()
        for row in range(count):
            item = tree.topLevelItem(row)
            if item is not None:
                texts.append(str(item.text(1) or ""))
    except Exception:
        pass
    return texts

def _ocr_tab_current_results(self, task):
    if task is None or not getattr(task, "results", None):
        return ("", [], None, [])
    try:
        if hasattr(self, "_persist_loaded_preview_bboxes"):
            self._persist_loaded_preview_bboxes()
        elif hasattr(self, "_persist_live_canvas_bboxes"):
            self._persist_live_canvas_bboxes(task)
    except Exception:
        pass
    try:
        _text, kr_records, image_obj, recs = task.results
    except Exception:
        return task.results
    recs = _ocr_tab_clone_recs(recs or [])
    visible = _ocr_tab_visible_texts(self)
    if visible:
        rebuilt = []
        for i, value in enumerate(visible):
            bbox = recs[i].bbox if i < len(recs) else None
            rebuilt.append(RecordView(i, value, bbox))
        recs = rebuilt
    text = "\n".join(rv.text for rv in recs).strip()
    return text, kr_records or [], image_obj, recs

def _ocr_tab_save_active(self):
    if getattr(self, "_ocr_tab_loading", False):
        return
    task = _ocr_tab_find_task(self, getattr(self, "_ocr_tab_active_path", "") or _ocr_tab_current_path(self))
    if task is None:
        return
    entries = _ocr_tab_entries(task, create=True)
    index = max(0, min(int(getattr(task, "ocr_tab_active_index", 0) or 0), len(entries) - 1))
    old = entries[index]
    persistent_name = _ocr_tab_visible_tab_name(self, index, old)
    entry = _ocr_tab_entry_from_results(
        _ocr_tab_current_results(self, task),
        index,
        old.get("model_path", "") or getattr(self, "model_path", ""),
        old.get("model_name", ""),
    )
    entry["edited"] = bool(getattr(task, "edited", False))
    entry["run_index"] = _ocr_tab_stable_number(old, index)
    entry["tab_name"] = str(old.get("tab_name", "") or "").strip() if bool(old.get("tab_name_custom", False)) else persistent_name
    entry["tab_name_custom"] = bool(old.get("tab_name_custom", False))
    try:
        entry["undo_stack"] = list(getattr(task, "undo_stack", []) or [])
        entry["redo_stack"] = list(getattr(task, "redo_stack", []) or [])
    except Exception:
        pass
    entries[index] = entry
    task.ocr_tab_variants = entries
    task.ocr_tab_active_index = index
    self._ocr_tab_active_path = str(getattr(task, "path", "") or "")

def _ocr_tab_label(self, index, entry=None):
    if bool((entry or {}).get("tab_name_custom", False)):
        custom = str((entry or {}).get("tab_name", "") or "").strip()
        if custom:
            return custom
    custom = persistent_ocr_tab_name(self, str((entry or {}).get("tab_name", "") or ""))
    if custom:
        return custom
    return _ocr_tab_default_label(self, _ocr_tab_stable_number(entry, index) - 1)

def _ocr_tab_tooltip(self, index, entry):
    model = str((entry or {}).get("model_name", "") or (entry or {}).get("model_path", "") or "")
    if model:
        try:
            return self._tr("multi_ocr_variant_tooltip", int(index) + 1, model)
        except Exception:
            return f"{_ocr_tab_label(self, index, entry)}: {model}"
    return _ocr_tab_label(self, index, entry)

def _ocr_tab_configure_tab_ui(self, tabs):
    try:
        tabs.setTabsClosable(False)
    except Exception:
        pass
    try:
        configure_ocr_variant_tab_buttons(self)
    except Exception:
        pass
    try:
        if hasattr(tabs, "_update_scroll_arrow_buttons"):
            tabs._update_scroll_arrow_buttons()
    except Exception:
        pass

def _ocr_tab_refresh(self, task=None):
    tabs = getattr(self, "ocr_variant_tabs", None)
    if tabs is None:
        return
    task = task or _ocr_tab_find_task(self)
    entries = _ocr_tab_entries(task, create=True) if task is not None else [_ocr_tab_blank_entry(0)]
    active = int(getattr(task, "ocr_tab_active_index", 0) or 0) if task is not None else 0
    active = max(0, min(active, max(0, len(entries) - 1)))
    try:
        self._ocr_tabs_updating = True
        tabs.blockSignals(True)
        # OCRVariantTabBar ist eine QTabBar, kein QTabWidget.
        # QTabBar besitzt kein clear(); deshalb alle Tabs robust einzeln entfernen.
        try:
            while tabs.count() > 0:
                tabs.removeTab(0)
        except Exception:
            pass
        for i, entry in enumerate(entries or [_ocr_tab_blank_entry(0)]):
            label = _ocr_tab_label(self, i, entry)
            tab_index = tabs.addTab(ocr_variant_tab_display_text(label))
            try:
                tabs.setTabToolTip(tab_index, _ocr_tab_tooltip(self, i, entry))
            except Exception:
                pass
        plus = tabs.addTab("+")
        try:
            tabs.setTabToolTip(plus, self._tr("multi_ocr_variant_add_tooltip"))
        except Exception:
            pass
        tabs.setCurrentIndex(active)
        tabs.setVisible(True)
        _ocr_tab_configure_tab_ui(self, tabs)
        tabs.blockSignals(False)
    finally:
        self._ocr_tabs_updating = False
    try:
        _ocr_tab_configure_tab_ui(self, tabs)
        tabs.updateGeometry()
        tabs.repaint()
    except Exception:
        pass

def _ocr_tab_apply(self, path="", index=0, save_current=True):
    task = _ocr_tab_find_task(self, path or _ocr_tab_current_path(self))
    if task is None:
        return False
    if save_current:
        _ocr_tab_save_active(self)
    entries = _ocr_tab_entries(task, create=True)
    index = max(0, min(int(index or 0), len(entries) - 1))
    task.ocr_tab_active_index = index
    task.results = _ocr_tab_results_from_entry(entries[index])
    task.status = STATUS_DONE
    task.edited = bool(entries[index].get("edited", False))
    try:
        task.undo_stack = list(entries[index].get("undo_stack", []) or [])
        task.redo_stack = list(entries[index].get("redo_stack", []) or [])
    except Exception:
        pass
    self._ocr_tab_active_path = str(getattr(task, "path", "") or "")
    self._ocr_tab_loading = True
    try:
        if callable(_ORIGINAL_LOAD_RESULTS):
            _ORIGINAL_LOAD_RESULTS(self, task.path, persist_current=False)
    finally:
        self._ocr_tab_loading = False
    _ocr_tab_refresh(self, task)
    return True

def _ocr_tab_add(self, path=""):
    task = _ocr_tab_find_task(self, path or _ocr_tab_current_path(self))
    if task is None:
        tabs = getattr(self, "ocr_variant_tabs", None)
        if tabs is not None:
            label = _ocr_tab_default_label(self, _ocr_tab_next_visible_number(self, tabs) - 1)
            idx = tabs.insertTab(max(0, tabs.count() - 1), ocr_variant_tab_display_text(label))
            tabs.setTabToolTip(idx, label)
        return True
    _ocr_tab_save_active(self)
    entries = _ocr_tab_entries(task, create=True)
    entries.append(_ocr_tab_blank_entry(_ocr_tab_next_number(entries) - 1))
    task.ocr_tab_active_index = len(entries) - 1
    task.ocr_tab_variants = entries
    _ocr_tab_apply(self, task.path, task.ocr_tab_active_index, save_current=False)
    return True

def _ocr_tab_delete(self, index):
    task = _ocr_tab_find_task(self)
    if task is None:
        tabs = getattr(self, "ocr_variant_tabs", None)
        try:
            index = int(index or 0)
            if tabs is not None and 0 <= index < tabs.count() - 1:
                if tabs.count() <= 2:
                    label = _ocr_tab_label(self, 0, _ocr_tab_blank_entry(0))
                    tabs.setTabText(0, ocr_variant_tab_display_text(label))
                    tabs.setTabToolTip(0, label)
                    tabs.setCurrentIndex(0)
                else:
                    tabs.removeTab(index)
                    tabs.setCurrentIndex(max(0, min(index, tabs.count() - 2)))
                _ocr_tab_configure_tab_ui(self, tabs)
                return True
        except Exception:
            pass
        return False
    _ocr_tab_save_active(self)
    entries = _ocr_tab_entries(task, create=True)
    if not (0 <= int(index or 0) < len(entries)):
        return False
    index = int(index or 0)
    active = int(getattr(task, "ocr_tab_active_index", 0) or 0)
    if len(entries) <= 1:
        entries[:] = [_ocr_tab_blank_entry(0)]
        active = 0
    else:
        entries.pop(index)
        if active > index:
            active -= 1
        elif active == index:
            active = min(index, len(entries) - 1)
    used_numbers = set()
    for i, entry in enumerate(entries):
        entry["run_index"] = _ocr_tab_stable_number(entry, i, used_numbers)
    task.ocr_tab_variants = entries
    task.ocr_tab_active_index = max(0, min(active, len(entries) - 1))
    _ocr_tab_apply(self, task.path, task.ocr_tab_active_index, save_current=False)
    return True

def _ocr_tab_rename(self, index, name):
    task = _ocr_tab_find_task(self)
    index = int(index or 0)
    clean = str(name or "").strip()
    if not clean:
        return False
    if task is None:
        tabs = getattr(self, "ocr_variant_tabs", None)
        if tabs is not None and 0 <= index < tabs.count() - 1:
            tabs.setTabText(index, ocr_variant_tab_display_text(clean))
            tabs.setTabToolTip(index, clean)
            _ocr_tab_configure_tab_ui(self, tabs)
            return True
        return False
    entries = _ocr_tab_entries(task, create=True)
    if not (0 <= index < len(entries)):
        return False
    entries[index]["tab_name"] = clean
    entries[index]["tab_name_custom"] = True
    task.ocr_tab_variants = entries
    try:
        tabs = getattr(self, "ocr_variant_tabs", None)
        if tabs is not None and 0 <= index < tabs.count():
            tabs.setTabText(index, ocr_variant_tab_display_text(clean))
            tabs.setTabToolTip(index, clean)
    except Exception:
        pass
    _ocr_tab_refresh(self, task)
    return True

def _ocr_tab_on_changed(self, index):
    if getattr(self, "_ocr_tabs_updating", False) or getattr(self, "_ocr_variant_plus_handling", False):
        return
    tabs = getattr(self, "ocr_variant_tabs", None)
    if tabs is None or index < 0:
        return
    if index == tabs.count() - 1 or ocr_variant_tab_plain_text(tabs.tabText(index)) == "+":
        _ocr_tab_add(self)
    else:
        _ocr_tab_apply(self, _ocr_tab_current_path(self), index, save_current=True)
