from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())

from bottled_kraken.common import RecordView, STATUS_DONE, _clean_ocr_text, os
from bottled_kraken.main_window import MainWindow

try:
    _BK_MANUAL_APPLY_PREV_SINGLE_DONE = MainWindow.on_ai_single_line_revision_done
except Exception:
    _BK_MANUAL_APPLY_PREV_SINGLE_DONE = None
try:
    _BK_MANUAL_APPLY_PREV_SELECTED_DONE = MainWindow.on_ai_selected_lines_revision_done
except Exception:
    _BK_MANUAL_APPLY_PREV_SELECTED_DONE = None


def _bk_manual_apply_find_task(window, path):
    try:
        return next((item for item in getattr(window, 'queue_items', []) if getattr(item, 'path', None) == path), None)
    except Exception:
        return None


def _bk_manual_apply_update_active_tab(window, task):
    if task is None or not getattr(task, 'results', None):
        return
    # Wichtig: hier NICHT _ptr_sync_active_multi_variant/_ocr_tab_save_active
    # aufrufen. Diese Funktionen lesen den noch nicht aktualisierten sichtbaren
    # Listeninhalt aus der GUI und können dadurch den gerade gesetzten LM-Text
    # sofort wieder mit dem alten Placeholder überschreiben.
    try:
        entries = getattr(task, 'ocr_tab_variants', None)
        if not entries:
            return
        index = int(getattr(task, 'ocr_tab_active_index', 0) or 0)
        index = max(0, min(index, len(entries) - 1))
        text, kr_records, im, recs = task.results
        entry = dict(entries[index] or {})
        entry['text'] = text
        entry['record_views'] = [RecordView(i, rv.text, tuple(rv.bbox) if rv.bbox else None) for i, rv in enumerate(recs)]
        entry['edited'] = True
        entries[index] = entry
        task.ocr_tab_variants = entries
        path = getattr(task, 'path', '')
        if path:
            if hasattr(window, '_ptr_multi_ocr_variant_meta_by_path'):
                window._ptr_multi_ocr_variant_meta_by_path[path] = entries
            if hasattr(window, '_ptr_multi_ocr_variants_by_path'):
                window._ptr_multi_ocr_variants_by_path[path] = [str(e.get('text', '') or '') for e in entries]
            if hasattr(window, '_ptr_multi_ocr_active_index_by_path'):
                window._ptr_multi_ocr_active_index_by_path[path] = index
            if hasattr(window, '_ocr_active_variant_by_path'):
                window._ocr_active_variant_by_path[path] = index
    except Exception:
        pass


def _bk_manual_apply_force_line(window, path, row, new_text):
    new_text = _clean_ocr_text(new_text or '')
    if not new_text:
        return False
    task = _bk_manual_apply_find_task(window, path)
    if task is None or not getattr(task, 'results', None):
        return False
    try:
        row = int(row)
    except Exception:
        return False
    text, kr_records, im, recs = task.results
    if not (0 <= row < len(recs)):
        return False
    old_text = _clean_ocr_text(getattr(recs[row], 'text', '') or '')
    if old_text == new_text:
        return True
    try:
        window._push_undo(task)
    except Exception:
        pass
    new_recs = [RecordView(i, rv.text, tuple(rv.bbox) if rv.bbox else None) for i, rv in enumerate(recs)]
    new_recs[row].text = new_text
    for i, rv in enumerate(new_recs):
        rv.idx = i
    task.results = ('\n'.join(rv.text for rv in new_recs).strip(), kr_records, im, new_recs)
    task.status = STATUS_DONE
    task.edited = True
    try:
        task.preset_bboxes = [tuple(rv.bbox) if rv.bbox else None for rv in new_recs]
    except Exception:
        pass
    _bk_manual_apply_update_active_tab(window, task)
    try:
        cur = window._current_task()
    except Exception:
        cur = None
    if cur is task or (cur is not None and getattr(cur, 'path', None) == path):
        try:
            window._sync_ui_after_recs_change(task, keep_row=row)
        except Exception:
            pass
        try:
            window.list_lines.setCurrentRow(row)
            window.canvas.select_indices([row], center=False)
        except Exception:
            pass
    else:
        try:
            window._update_queue_row(path)
        except Exception:
            pass
    return True


def _bk_manual_apply_single_done(self, path: str, revised_lines: list):
    ctx = dict(getattr(self, '_ai_single_line_context', None) or {})
    row = ctx.get('row', -1)
    value = ''
    try:
        if revised_lines:
            value = _clean_ocr_text(str(revised_lines[0] or ''))
    except Exception:
        value = ''
    result = None
    if callable(_BK_MANUAL_APPLY_PREV_SINGLE_DONE):
        result = _BK_MANUAL_APPLY_PREV_SINGLE_DONE(self, path, revised_lines)
    if value and row is not None:
        _bk_manual_apply_force_line(self, path, row, value)
    return result


def _bk_manual_apply_selected_done(self, path: str, revised_lines: list):
    ctx = dict(getattr(self, '_bk_lm_strict_result_rows_context', None) or {})
    rows = list(ctx.get('rows', []) or [])
    result = None
    if callable(_BK_MANUAL_APPLY_PREV_SELECTED_DONE):
        result = _BK_MANUAL_APPLY_PREV_SELECTED_DONE(self, path, revised_lines)
    try:
        lines = [_clean_ocr_text(str(x or '')) for x in (revised_lines or [])]
        if rows and lines:
            for i, row in enumerate(rows):
                if i < len(lines) and lines[i]:
                    _bk_manual_apply_force_line(self, path, row, lines[i])
    except Exception:
        pass
    return result


try:
    MainWindow.on_ai_single_line_revision_done = _bk_manual_apply_single_done
    MainWindow.on_ai_selected_lines_revision_done = _bk_manual_apply_selected_done
except Exception:
    pass

__all__ = [
    '_bk_manual_apply_find_task',
    '_bk_manual_apply_force_line',
    '_bk_manual_apply_selected_done',
    '_bk_manual_apply_single_done',
    '_bk_manual_apply_update_active_tab',
]
register_globals('bk', globals(), __all__)
