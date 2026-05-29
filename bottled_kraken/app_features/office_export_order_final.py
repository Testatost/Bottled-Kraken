from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
from typing import List
def _bk_fix65_row_signature(records, med_h: float):
    rows = []
    threshold = max(3.0, min(18.0, float(med_h) * 0.72))
    for r in sorted([x for x in (records or []) if x.get("bbox")], key=lambda item: (item.get("cy", item.get("y0", 0.0)), item.get("x0", 0.0))):
        cy = float(r.get("cy", (r.get("y0", 0.0) + r.get("y1", 0.0)) / 2.0))
        for row in rows:
            if abs(cy - row["cy"]) <= threshold:
                row["items"].append(r)
                row["cy"] = sum(float(x.get("cy", (x.get("y0", 0.0) + x.get("y1", 0.0)) / 2.0)) for x in row["items"]) / max(1, len(row["items"]))
                break
        else:
            rows.append({"cy": cy, "items": [r]})
    rows.sort(key=lambda row: (row["cy"], min(float(x.get("x0", 0.0)) for x in row["items"])))
    return rows
def _bk_fix65_assign_columns_with_index(recs, anchors: List[float], page_w: int):
    if not anchors:
        return None
    bounds = [-10**9]
    for i in range(len(anchors) - 1):
        bounds.append((float(anchors[i]) + float(anchors[i + 1])) / 2.0)
    bounds.append(10**9)
    columns = [[] for _ in anchors]
    full = []
    assigned = []
    for r in recs or []:
        bb = r.get("bbox")
        if not bb:
            full.append(r)
            continue
        if float(r.get("w", 0.0) or 0.0) >= max(1.0, float(page_w)) * 0.54:
            full.append(r)
            continue
        nearest_dist = min(abs(float(r.get("x0", 0.0)) - float(anchor)) for anchor in anchors)
        if nearest_dist > max(70.0, float(page_w) * 0.13):
            full.append(r)
            continue
        col_idx = 0
        x0 = float(r.get("x0", 0.0))
        for i in range(len(anchors)):
            if bounds[i] <= x0 < bounds[i + 1]:
                col_idx = i
                break
        rr = dict(r)
        rr["_bk_fix65_col"] = col_idx
        columns[col_idx].append(rr)
        assigned.append(rr)
    if any(len(c) < 3 for c in columns):
        return None
    return {"anchors": anchors, "columns": columns, "full": full, "assigned": assigned}
def _bk_fix65_detect_column_start(assigned, med_h: float):
    rows = _bk_fix65_row_signature(assigned, med_h)
    if not rows:
        return None
    for row in rows:
        cols = {int(x.get("_bk_fix65_col", -1)) for x in row["items"] if int(x.get("_bk_fix65_col", -1)) >= 0}
        if len(cols) >= 2:
            return min(float(x.get("y0", 0.0)) for x in row["items"])
    counts = {}
    for row in rows:
        for x in row["items"]:
            ci = int(x.get("_bk_fix65_col", -1))
            counts[ci] = counts.get(ci, 0) + 1
            if counts[ci] >= 3:
                return float(x.get("y0", 0.0))
    return min(float(x.get("y0", 0.0)) for x in assigned)
def _bk_fix65_bounds_for_records(records):
    boxes = [r.get("bbox") for r in (records or []) if r.get("bbox")]
    if not boxes:
        return None
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
def _bk_fix65_para_from_record(r):
    return {
        "type": "paragraph",
        "text": r.get("text", ""),
        "bbox": r.get("bbox"),
        "y0": r.get("y0", 0.0),
        "x0": r.get("x0", 0.0),
        "idx": r.get("idx", 0),
    }
def _bk_fix65_build_column_blocks(record_views, image_size=None):
    recs = _bk_fix62_records(record_views)
    recs.sort(key=lambda r: (_bk_fix62_record_y0(r), _bk_fix62_record_x0(r), _bk_fix62_record_idx(r)))
    page_w, _page_h = _bk_fix62_page_size(image_size, recs)
    boxed = [r for r in recs if r.get("bbox")]
    if not boxed:
        return [{"type": "paragraph", "text": r["text"]} for r in recs]
    if _bk_fix62_is_dense_numeric_table(boxed, page_w):
        return None
    anchors = _bk_fix62_cluster_x_starts(boxed, page_w)
    assigned_pack = _bk_fix65_assign_columns_with_index(boxed, anchors, page_w)
    if not assigned_pack:
        return None
    med_h = _bk_fix62_median_height(boxed)
    y_slack = max(2.0, med_h * 0.55)
    start_y = _bk_fix65_detect_column_start(assigned_pack["assigned"], med_h)
    if start_y is None:
        return None
    columns = [[] for _ in anchors]
    full = list(assigned_pack["full"])
    for r in assigned_pack["assigned"]:
        if _bk_fix62_record_y1(r) < start_y - y_slack:
            full.append(r)
        else:
            ci = int(r.get("_bk_fix65_col", 0))
            if 0 <= ci < len(columns):
                columns[ci].append(r)
            else:
                full.append(r)
    if any(len(c) < 3 for c in columns):
        return None
    col_records = [r for col in columns for r in col]
    top_y = min(_bk_fix62_record_y0(r) for r in col_records)
    bottom_y = max(_bk_fix62_record_y1(r) for r in col_records)
    col_bbox = _bk_fix65_bounds_for_records(col_records)
    before = [r for r in full if _bk_fix62_record_y1(r) < top_y - y_slack]
    after = [r for r in full if _bk_fix62_record_y0(r) > bottom_y + y_slack]
    inside = [r for r in full if r not in before and r not in after]
    blocks = []
    for r in sorted(before, key=lambda item: (_bk_fix62_record_y0(item), _bk_fix62_record_x0(item), _bk_fix62_record_idx(item))):
        blocks.append(_bk_fix65_para_from_record(r))
    col_lines = []
    for col in columns:
        col_sorted = sorted(col, key=lambda item: (_bk_fix62_record_y0(item), _bk_fix62_record_x0(item), _bk_fix62_record_idx(item)))
        col_lines.append(_bk_fix62_column_lines(col_sorted, page_w))
    if any(col_lines):
        blocks.append({
            "type": "columns",
            "columns": col_lines,
            "bbox": col_bbox,
            "y0": top_y,
            "x0": min(float(a) for a in anchors) if anchors else 0.0,
            "idx": min(_bk_fix62_record_idx(r) for r in col_records),
        })
    for r in sorted(inside + after, key=lambda item: (_bk_fix62_record_y0(item), _bk_fix62_record_x0(item), _bk_fix62_record_idx(item))):
        blocks.append(_bk_fix65_para_from_record(r))
    return blocks
def _bk_fix65_row_is_mostly_text(row) -> bool:
    vals = [_bk_fix62_clean(x) for x in (row or []) if _bk_fix62_clean(x)]
    if not vals:
        return False
    text = " ".join(vals)
    letters = sum(1 for ch in text if ch.isalpha())
    digits = sum(1 for ch in text if ch.isdigit())
    return letters >= max(6, digits * 2)
def _bk_fix65_table_like_following_rows(rows) -> bool:
    usable = [list(r or []) for r in (rows or [])[:8] if r]
    if len(usable) < 2:
        return False
    multi = sum(1 for r in usable if len([x for x in r if _bk_fix62_clean(x)]) >= 3)
    numeric = sum(1 for r in usable if _bk_fix62_row_numeric_ratio(r) >= 0.35)
    return multi >= 2 or numeric >= 2
def _bk_fix65_should_lift_table_header(row, following_rows) -> bool:
    try:
        if _bk_fix62_should_lift_table_header(row, following_rows):
            return True
    except Exception:
        pass
    vals = [_bk_fix62_clean(x) for x in (row or []) if _bk_fix62_clean(x)]
    if not vals or not following_rows:
        return False
    if len(vals) <= 3 and _bk_fix65_row_is_mostly_text(vals) and _bk_fix65_table_like_following_rows(following_rows):
        return True
    joined = " ".join(vals).strip()
    if len(vals) == 1 and len(joined) >= 8 and _bk_fix65_row_is_mostly_text(vals) and _bk_fix65_table_like_following_rows(following_rows):
        return True
    return False
def _bk_fix65_postprocess_blocks(blocks):
    out = []
    for block in blocks or []:
        if not isinstance(block, dict) or block.get("type") != "table":
            out.append(block)
            continue
        rows = [list(r or []) for r in (block.get("rows") or [])]
        lifted = []
        while len(rows) >= 3 and _bk_fix65_should_lift_table_header(rows[0], rows[1:]):
            txt = " ".join(_bk_fix62_clean(x) for x in rows.pop(0) if _bk_fix62_clean(x)).strip()
            if txt:
                lifted.append({"type": "paragraph", "text": txt})
        out.extend(lifted)
        if rows:
            nb = dict(block)
            nb["rows"] = rows
            out.append(nb)
    return out
_BK_FIX65_PREV_EXPORT_BLOCKS = globals().get("_bk_fix62_export_blocks")
def _bk_fix65_export_blocks(record_views, image_size=None):
    blocks = _bk_fix65_build_column_blocks(record_views, image_size)
    if blocks:
        return _bk_fix65_postprocess_blocks(blocks)
    try:
        blocks = _bk_fix62_fallback_blocks(record_views, image_size)
    except Exception:
        if callable(_BK_FIX65_PREV_EXPORT_BLOCKS):
            blocks = _BK_FIX65_PREV_EXPORT_BLOCKS(record_views, image_size)
        else:
            blocks = []
    return _bk_fix65_postprocess_blocks(blocks)
_bk_fix62_export_blocks = _bk_fix65_export_blocks
def _bk_fix66_assign_columns_with_index(recs, anchors: List[float], page_w: int):
    if not anchors:
        return None
    bounds = [-10**9]
    for i in range(len(anchors) - 1):
        bounds.append((float(anchors[i]) + float(anchors[i + 1])) / 2.0)
    bounds.append(10**9)
    columns = [[] for _ in anchors]
    full = []
    assigned = []
    for r in recs or []:
        bb = r.get("bbox")
        if not bb:
            full.append(r)
            continue
        if float(r.get("w", 0.0) or 0.0) >= max(1.0, float(page_w)) * 0.54:
            full.append(r)
            continue
        x0 = float(r.get("x0", 0.0) or 0.0)
        col_idx = 0
        for i in range(len(anchors)):
            if bounds[i] <= x0 < bounds[i + 1]:
                col_idx = i
                break
        nearest_dist = min(abs(x0 - float(anchor)) for anchor in anchors)
        right_bound = bounds[col_idx + 1]
        x1 = float(r.get("x1", x0) or x0)
        crosses_next_column = col_idx < len(anchors) - 1 and x1 > right_bound + max(8.0, float(page_w) * 0.012)
        if nearest_dist > max(70.0, float(page_w) * 0.13) and crosses_next_column:
            full.append(r)
            continue
        rr = dict(r)
        rr["_bk_fix65_col"] = col_idx
        columns[col_idx].append(rr)
        assigned.append(rr)
    if any(len(c) < 3 for c in columns):
        return None
    return {"anchors": anchors, "columns": columns, "full": full, "assigned": assigned}
_bk_fix65_assign_columns_with_index = _bk_fix66_assign_columns_with_index
__all__ = [
    '_BK_FIX65_PREV_EXPORT_BLOCKS',
    '_bk_fix62_export_blocks',
    '_bk_fix65_assign_columns_with_index',
    '_bk_fix65_bounds_for_records',
    '_bk_fix65_build_column_blocks',
    '_bk_fix65_detect_column_start',
    '_bk_fix65_export_blocks',
    '_bk_fix65_para_from_record',
    '_bk_fix65_postprocess_blocks',
    '_bk_fix65_row_is_mostly_text',
    '_bk_fix65_row_signature',
    '_bk_fix65_should_lift_table_header',
    '_bk_fix65_table_like_following_rows',
    '_bk_fix66_assign_columns_with_index',
]
register_globals('bk', globals(), __all__)
