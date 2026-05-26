"""Zusatzmodul: Ditto-Zeichen, Tabellen-/Datenexporte, Overlay-Box-Hilfen und UI-Fixes.

Der Patch ist bewusst defensiv: Er hängt sich nur an vorhandene Methoden, wenn sie in der
jeweiligen Bottled-Kraken-Version existieren. Dadurch bleibt die Datei auch mit älteren
Zwischenständen lauffähig.
"""

from .shared import *
from .ui_components import *
from .workers import *
from .dialogs import *
from .image_edit import *
from .main_window import MainWindow

def _bk_fix59_box(rv):
    try:
        bb = getattr(rv, 'bbox', None)
        if not bb or len(bb) < 4:
            return None
        x0, y0, x1, y1 = [float(v) for v in bb[:4]]
        if x1 <= x0 or y1 <= y0:
            return None
        return x0, y0, x1, y1
    except Exception:
        return None

def _bk_fix59_row_metrics(row):
    boxes = [_bk_fix59_box(rv) for rv in (row or [])]
    boxes = [bb for bb in boxes if bb]
    if not boxes:
        return 0.0, 0.0, 0.0, 0.0, 1.0, 1.0
    x0 = min(bb[0] for bb in boxes)
    y0 = min(bb[1] for bb in boxes)
    x1 = max(bb[2] for bb in boxes)
    y1 = max(bb[3] for bb in boxes)
    cy_vals = [((bb[1] + bb[3]) / 2.0, max(1.0, bb[3] - bb[1])) for bb in boxes]
    weight = sum(w for _cy, w in cy_vals) or 1.0
    cy = sum(cy * w for cy, w in cy_vals) / weight
    return x0, y0, x1, y1, cy, max(1.0, y1 - y0)

def _bk_fix59_overlap(a0, a1, b0, b1) -> float:
    return max(0.0, min(float(a1), float(b1)) - max(float(a0), float(b0)))

def _bk_fix59_can_join_row(rv, row, med_h: float) -> bool:
    bb = _bk_fix59_box(rv)
    if not bb or not row:
        return False
    x0, y0, x1, y1 = bb
    rx0, ry0, rx1, ry1, rcy, rh = _bk_fix59_row_metrics(row)
    cy = (y0 + y1) / 2.0
    h = max(1.0, y1 - y0)
    dy = abs(cy - rcy)

    # Sehr viel enger als vorher: gleiche gedruckte Zeile hat normalerweise fast
    # denselben Mittelpunkt. Die alte 0.72*Medianhoehe hat bei Fußnoten die
    # naechste Zeile versehentlich derselben Exportzeile zugeschlagen.
    center_limit = max(2.0, min(8.0, float(med_h) * 0.38))

    y_ov = _bk_fix59_overlap(y0, y1, ry0, ry1)
    y_ratio = y_ov / max(1.0, min(h, rh))
    x_ov = _bk_fix59_overlap(x0, x1, rx0, rx1)
    x_ratio = x_ov / max(1.0, min(max(1.0, x1 - x0), max(1.0, rx1 - rx0)))

    # Zwei fast gleich breite bzw. horizontal stark ueberlappende Zeilen sind
    # in historischen Tabellen oft zwei echte Textzeilen untereinander. Wenn
    # deren y-Mittelpunkte nicht nahezu identisch sind, nicht zusammenfassen.
    if x_ratio >= 0.48 and dy > max(1.5, float(med_h) * 0.16):
        return False

    return dy <= center_limit or y_ratio >= 0.42

def _bk_fix59_group_rows(recs, page_width: int = 0):
    with_boxes = [rv for rv in (recs or []) if _bk_fix59_box(rv) and _bk_fix36_clean_text(getattr(rv, 'text', ''))]
    without_boxes = [rv for rv in (recs or []) if not _bk_fix59_box(rv) and _bk_fix36_clean_text(getattr(rv, 'text', ''))]
    if not with_boxes:
        return [[rv] for rv in without_boxes]

    heights = sorted(max(2.0, _bk_fix59_box(rv)[3] - _bk_fix59_box(rv)[1]) for rv in with_boxes if _bk_fix59_box(rv))
    med_h = heights[len(heights) // 2] if heights else 12.0

    rows: List[List[Any]] = []
    for rv in sorted(with_boxes, key=lambda r: (((_bk_fix59_box(r)[1] + _bk_fix59_box(r)[3]) / 2.0), _bk_fix59_box(r)[0])):
        candidates = []
        cy = (_bk_fix59_box(rv)[1] + _bk_fix59_box(rv)[3]) / 2.0
        for idx, row in enumerate(rows):
            if _bk_fix59_can_join_row(rv, row, med_h):
                _rx0, _ry0, _rx1, _ry1, rcy, _rh = _bk_fix59_row_metrics(row)
                candidates.append((abs(cy - rcy), idx))
        if candidates:
            _dist, idx = min(candidates, key=lambda item: item[0])
            rows[idx].append(rv)
        else:
            rows.append([rv])

    for row in rows:
        row.sort(key=lambda r: (_bk_fix59_box(r)[0] if _bk_fix59_box(r) else 0.0))
    rows.sort(key=lambda row: (_bk_fix59_row_metrics(row)[4], _bk_fix59_row_metrics(row)[0]))

    # Boxlose Eintraege defensiv am Ende als eigene Zeilen erhalten.
    for rv in without_boxes:
        rows.append([rv])
    return rows

_bk_fix51_group_rows = _bk_fix59_group_rows

def _bk_fix59_spatial_text_from_recs(recs) -> str:
    recs = list(recs or [])
    try:
        _bk_fix43_resolve_ditto_marks_in_recs(recs)
    except Exception:
        try:
            _bk_fix36_resolve_ditto_marks_in_recs(recs)
        except Exception:
            pass
    with_boxes = [rv for rv in recs if _bk_fix59_box(rv) and _bk_fix36_clean_text(getattr(rv, 'text', ''))]
    if not with_boxes:
        return "\n".join(
            _bk_fix36_clean_text(x)
            for x in _bk_fix38_resolve_ditto_marks_in_lines([getattr(rv, 'text', '') for rv in recs])
            if _bk_fix36_clean_text(x)
        ) + "\n"
    boxes = [_bk_fix59_box(rv) for rv in with_boxes]
    min_x = min(bb[0] for bb in boxes)
    max_x = max(bb[2] for bb in boxes)
    width_px = max(1.0, max_x - min_x)
    target_cols = max(90, min(220, int(width_px / 5.5)))
    px_per_col = max(1.0, width_px / float(target_cols))
    rows = _bk_fix59_group_rows(with_boxes, int(max_x))
    output_lines: List[str] = []
    for row in rows:
        canvas = [" "] * (target_cols + 100)
        for rv in sorted(row, key=lambda r: _bk_fix59_box(r)[0] if _bk_fix59_box(r) else 0.0):
            bb = _bk_fix59_box(rv)
            txt = _bk_fix36_clean_text(getattr(rv, 'text', ''))
            if not bb or not txt:
                continue
            col = max(0, int((bb[0] - min_x) / px_per_col))
            while col < len(canvas) and any(ch != " " for ch in canvas[col:col + min(len(txt), 12)]):
                col += 1
            end = min(len(canvas), col + len(txt))
            for i, ch in enumerate(txt[:max(0, end - col)]):
                canvas[col + i] = ch
        line = "".join(canvas).rstrip()
        if line.strip():
            output_lines.append(line)
    return "\n".join(output_lines).rstrip() + "\n"

_bk_fix38_spatial_text_from_recs = _bk_fix59_spatial_text_from_recs

_bk_fix36_table_text_from_recs = _bk_fix59_spatial_text_from_recs
