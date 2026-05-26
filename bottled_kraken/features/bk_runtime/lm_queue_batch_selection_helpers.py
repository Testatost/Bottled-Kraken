"""Batch-Automatisierung für lokale LM-Überarbeitung über den Wartebereich.

Diese Datei überschreibt die LM-Menüpfade spät im bk_features-Ladeprozess.
Batchfähig sind nur:
- "Alle Zeilen überarbeiten"
- "LM OCR"
- Rechtsklick im Wartebereich -> "LM-Überarbeitung" als "Alle Zeilen überarbeiten"

"Aktuelle Zeile überarbeiten" und "Markierte Zeilen überarbeiten" bleiben
bewusst reine Funktionen für die aktuell geladene Vorschauseite.
"""

_BK_LM_BATCH_MODE_CURRENT_LINE = "current_line"

_BK_LM_BATCH_MODE_SELECTED_LINES = "selected_lines"

_BK_LM_BATCH_MODE_ALL_LINES = "all_lines"

_BK_LM_BATCH_MODE_LM_OCR = "lm_ocr"

_BK_LM_BATCH_MODE_LM_OCR_BOXES = "lm_ocr_boxes"

def _bk_lm_any_job_running(self) -> bool:
    return bool(
        (getattr(self, "ai_worker", None) and self.ai_worker.isRunning())
        or (getattr(self, "ai_batch_worker", None) and self.ai_batch_worker.isRunning())
        or (getattr(self, "_bk_lm_queue_batch_worker", None) and self._bk_lm_queue_batch_worker.isRunning())
        or (getattr(self, "_bk_local_json_worker", None) and self._bk_local_json_worker.isRunning())
    )

def _bk_lm_task_has_results(task) -> bool:
    if task is None or not getattr(task, "results", None):
        return False
    try:
        _text, _kr_records, _im, recs = task.results
        return bool(recs)
    except Exception:
        return False

def _bk_lm_task_has_overlay_boxes(task) -> bool:
    if not _bk_lm_task_has_results(task):
        return False
    try:
        _text, _kr_records, _im, recs = task.results
        boxes = list(getattr(task, "preset_bboxes", []) or [])
        if len(boxes) != len(recs):
            boxes = [rv.bbox for rv in recs]
        return any(bool(bb) for bb in boxes)
    except Exception:
        return False

def _bk_lm_get_current_done_task(self):
    # Für LM-Nachbearbeitung zählt hier nicht mehr ausschließlich STATUS_DONE.
    # Wenn OCR-Zeilen im Task vorhanden sind, darf auch ein Fehlerstatus weiterverarbeitet werden.
    task = self._current_task()
    try:
        self._persist_live_canvas_bboxes(task)
    except Exception:
        pass
    if not _bk_lm_task_has_results(task):
        return None
    return task

def _bk_lm_unique_tasks(tasks):
    out = []
    seen = set()
    for task in tasks or []:
        path = getattr(task, "path", None)
        if not path or path in seen:
            continue
        seen.add(path)
        out.append(task)
    return out

def _bk_lm_checked_queue_tasks_with_results(self):
    try:
        tasks = self._checked_queue_tasks()
    except Exception:
        tasks = []
    return _bk_lm_unique_tasks([t for t in tasks if _bk_lm_task_has_results(t)])

def _bk_lm_selected_queue_tasks_with_results(self):
    try:
        tasks = self._selected_queue_tasks()
    except Exception:
        tasks = []
    return _bk_lm_unique_tasks([t for t in tasks if _bk_lm_task_has_results(t)])

def _bk_lm_checked_queue_tasks_any(self):
    try:
        tasks = self._checked_queue_tasks()
    except Exception:
        tasks = []
    return _bk_lm_unique_tasks([t for t in tasks if getattr(t, "path", None)])

def _bk_lm_selected_queue_tasks_any(self):
    try:
        tasks = self._selected_queue_tasks()
    except Exception:
        tasks = []
    return _bk_lm_unique_tasks([t for t in tasks if getattr(t, "path", None)])

def _bk_lm_get_current_task_any(self):
    task = None
    try:
        task = self._current_task()
    except Exception:
        task = None
    try:
        self._persist_live_canvas_bboxes(task)
    except Exception:
        pass
    return task if getattr(task, "path", None) else None

def _bk_lm_queue_targets(self, *, allow_selected: bool = False, allow_all_if_empty: bool = False):
    checked = _bk_lm_checked_queue_tasks_with_results(self)
    if checked:
        return checked, "checked"
    if allow_selected:
        selected = _bk_lm_selected_queue_tasks_with_results(self)
        if selected:
            return selected, "selected"
    if allow_all_if_empty:
        all_items = [t for t in getattr(self, "queue_items", []) if _bk_lm_task_has_results(t)]
        if all_items:
            return _bk_lm_unique_tasks(all_items), "all"
    return [], ""

def _bk_lm_persist_visible_queue_state(self):
    try:
        self._persist_live_canvas_bboxes(self._current_task())
    except Exception:
        pass
    try:
        self._persist_loaded_preview_bboxes()
    except Exception:
        pass
