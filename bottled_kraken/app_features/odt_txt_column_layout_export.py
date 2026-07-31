from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
from bottled_kraken.common import _load_image_color
from bottled_kraken.common import Any, Dict, Image, List, RecordView, TaskItem
from bottled_kraken.main_window import MainWindow
from xml.sax.saxutils import escape as _bk_fix62_xml_escape
def _bk_fix62_box(rv):
    try:
        bb = getattr(rv, "bbox", None)
        if not bb or len(bb) < 4:
            return None
        x0, y0, x1, y1 = [float(v) for v in bb[:4]]
        if x1 <= x0 or y1 <= y0:
            return None
        return x0, y0, x1, y1
    except Exception:
        return None
def _bk_fix62_clean(value) -> str:
    try:
        return _bk_fix36_clean_text(value)
    except Exception:
        return " ".join(str(value or "").replace("\r", "\n").split())
def _bk_fix62_records(record_views):
    out = []
    for pos, rv in enumerate(record_views or []):
        text = _bk_fix62_clean(getattr(rv, "text", ""))
        bb = _bk_fix62_box(rv)
        try:
            order_idx = int(getattr(rv, "idx", pos))
        except Exception:
            order_idx = int(pos)
        if not text:
            continue
        if not bb:
            out.append({"rv": rv, "text": text, "bbox": None, "x0": 0.0, "y0": 0.0, "x1": 0.0, "y1": 0.0, "idx": order_idx})
            continue
        x0, y0, x1, y1 = bb
        out.append({"rv": rv, "text": text, "bbox": bb, "x0": x0, "y0": y0, "x1": x1, "y1": y1, "idx": order_idx,
                    "cx": (x0 + x1) / 2.0, "cy": (y0 + y1) / 2.0, "w": x1 - x0, "h": y1 - y0})
    return out
def _bk_fix62_page_size(image_size, recs):
    try:
        w = int((image_size or (0, 0))[0])
        h = int((image_size or (0, 0))[1])
    except Exception:
        w = h = 0
    boxes = [r["bbox"] for r in recs if r.get("bbox")]
    if not w and boxes:
        w = int(max(bb[2] for bb in boxes))
    if not h and boxes:
        h = int(max(bb[3] for bb in boxes))
    return max(1, w or 1600), max(1, h or 2200)
def _bk_fix62_cluster_x_starts(recs, page_w: int):
    candidates = [r for r in recs if r.get("bbox") and r.get("w", 0) < page_w * 0.62]
    if len(candidates) < 8:
        return []
    vals = sorted(float(r["x0"]) for r in candidates)
    threshold = max(45.0, min(160.0, page_w * 0.085))
    clusters = []
    for x in vals:
        if not clusters:
            clusters.append([x])
            continue
        center = sum(clusters[-1]) / len(clusters[-1])
        if abs(x - center) <= threshold:
            clusters[-1].append(x)
        else:
            clusters.append([x])
    min_count = max(4, int(len(candidates) * 0.12))
    anchors = [sum(c) / len(c) for c in clusters if len(c) >= min_count]
    if not (2 <= len(anchors) <= 4):
        return []
    gaps = [anchors[i + 1] - anchors[i] for i in range(len(anchors) - 1)]
    if not gaps or max(gaps) < page_w * 0.16:
        return []
    return anchors
def _bk_fix62_numeric_density(recs) -> float:
    if not recs:
        return 0.0
    numeric = 0
    short = 0
    for r in recs:
        txt = str(r.get("text") or "")
        if any(ch.isdigit() for ch in txt):
            numeric += 1
        if len(txt) <= 10:
            short += 1
    return (numeric + short * 0.35) / max(1.0, float(len(recs)))
def _bk_fix62_is_dense_numeric_table(recs, page_w: int) -> bool:
    boxed = [r for r in recs if r.get("bbox")]
    if len(boxed) < 18:
        return False
    xs = sorted(r["x0"] for r in boxed if r.get("w", 0) < page_w * 0.36)
    if len(xs) < 12:
        return False
    clusters = []
    threshold = max(18.0, min(70.0, page_w * 0.035))
    for x in xs:
        if not clusters or abs(x - (sum(clusters[-1]) / len(clusters[-1]))) > threshold:
            clusters.append([x])
        else:
            clusters[-1].append(x)
    return len([c for c in clusters if len(c) >= 2]) >= 5 and _bk_fix62_numeric_density(boxed) >= 0.50
def _bk_fix62_assign_columns(recs, anchors: List[float], page_w: int):
    if not anchors:
        return None
    bounds = [-10**9]
    for i in range(len(anchors) - 1):
        bounds.append((anchors[i] + anchors[i + 1]) / 2.0)
    bounds.append(10**9)
    columns = [[] for _ in anchors]
    full = []
    for r in recs:
        bb = r.get("bbox")
        if not bb:
            full.append(r)
            continue
        if r.get("w", 0) >= page_w * 0.54:
            full.append(r)
            continue
        nearest_dist = min(abs(float(r["x0"]) - float(anchor)) for anchor in anchors)
        if nearest_dist > max(70.0, page_w * 0.13):
            full.append(r)
            continue
        idx = 0
        for i in range(len(anchors)):
            if bounds[i] <= float(r["x0"]) < bounds[i + 1]:
                idx = i
                break
        columns[idx].append(r)
    if any(len(c) < 3 for c in columns):
        return None
    return {"anchors": anchors, "columns": columns, "full": full}
def _bk_fix62_column_lines(col_records: List[Dict[str, Any]], page_w: int) -> List[str]:
    try:
        rows = _bk_fix59_group_rows([r["rv"] for r in col_records], page_w)
    except Exception:
        rows = []
        for r in sorted(col_records, key=lambda item: (item.get("cy", item.get("y0", 0)), item.get("x0", 0))):
            rows.append([r["rv"]])
    lines = []
    for row in rows:
        parts = []
        for rv in sorted(row, key=lambda item: (_bk_fix62_box(item) or (0, 0, 0, 0))[0]):
            txt = _bk_fix62_clean(getattr(rv, "text", ""))
            if txt:
                parts.append(txt)
        line = " ".join(parts).strip()
        if line:
            lines.append(line)
    return lines
def _bk_fix62_record_y0(r) -> float:
    try:
        return float(r.get("y0", 0.0) or 0.0)
    except Exception:
        return 0.0
def _bk_fix62_record_y1(r) -> float:
    try:
        return float(r.get("y1", 0.0) or 0.0)
    except Exception:
        return 0.0
def _bk_fix62_record_x0(r) -> float:
    try:
        return float(r.get("x0", 0.0) or 0.0)
    except Exception:
        return 0.0
def _bk_fix62_record_idx(r) -> int:
    try:
        return int(r.get("idx", 0) or 0)
    except Exception:
        return 0
def _bk_fix62_median_height(recs) -> float:
    vals = []
    for r in recs or []:
        try:
            if r.get("bbox"):
                vals.append(max(1.0, float(r.get("h", 0.0) or (_bk_fix62_record_y1(r) - _bk_fix62_record_y0(r)))))
        except Exception:
            pass
    if not vals:
        return 12.0
    vals.sort()
    return vals[len(vals) // 2]
def _bk_fix62_build_column_blocks(record_views, image_size=None):
    recs = _bk_fix62_records(record_views)
    recs.sort(key=lambda r: (_bk_fix62_record_idx(r), _bk_fix62_record_y0(r), _bk_fix62_record_x0(r)))
    page_w, page_h = _bk_fix62_page_size(image_size, recs)
    boxed = [r for r in recs if r.get("bbox")]
    if not boxed:
        return [{"type": "paragraph", "text": r["text"]} for r in recs]
    if _bk_fix62_is_dense_numeric_table(boxed, page_w):
        return None
    anchors = _bk_fix62_cluster_x_starts(boxed, page_w)
    assigned = _bk_fix62_assign_columns(boxed, anchors, page_w)
    if not assigned:
        return None
    columns = assigned["columns"]
    full = assigned["full"] + [r for r in recs if not r.get("bbox")]
    top_y = min(min(r["y0"] for r in c) for c in columns if c)
    bottom_y = max(max(r["y1"] for r in c) for c in columns if c)
    med_h = _bk_fix62_median_height(boxed)
    y_slack = max(2.0, med_h * 0.45)
    col_idx_values = [_bk_fix62_record_idx(r) for col in columns for r in col]
    min_col_idx = min(col_idx_values) if col_idx_values else 10**9
    max_col_idx = max(col_idx_values) if col_idx_values else -1
    before = [r for r in full if _bk_fix62_record_idx(r) < min_col_idx or _bk_fix62_record_y1(r) < top_y - y_slack]
    after = [r for r in full if _bk_fix62_record_idx(r) > max_col_idx or _bk_fix62_record_y0(r) > bottom_y + y_slack]
    middle_full = [r for r in full if r not in before and r not in after]
    blocks = []
    for r in sorted(before, key=lambda item: (_bk_fix62_record_idx(item), _bk_fix62_record_y0(item), _bk_fix62_record_x0(item))):
        blocks.append({"type": "paragraph", "text": r["text"], "bbox": r.get("bbox"), "y0": r.get("y0", 0), "x0": r.get("x0", 0), "idx": r.get("idx", 0)})
    col_lines = [_bk_fix62_column_lines(sorted(col, key=lambda item: (_bk_fix62_record_y0(item), _bk_fix62_record_x0(item))), page_w) for col in columns]
    if any(col_lines):
        col_boxes = [r["bbox"] for col in columns for r in col if r.get("bbox")]
        col_bbox = (min(b[0] for b in col_boxes), min(b[1] for b in col_boxes), max(b[2] for b in col_boxes), max(b[3] for b in col_boxes)) if col_boxes else None
        blocks.append({"type": "columns", "columns": col_lines, "bbox": col_bbox, "y0": top_y, "x0": min(anchors) if anchors else 0, "idx": min_col_idx})
    trailing = middle_full + after
    for r in sorted(trailing, key=lambda item: (_bk_fix62_record_idx(item), _bk_fix62_record_y0(item), _bk_fix62_record_x0(item))):
        blocks.append({"type": "paragraph", "text": r["text"], "bbox": r.get("bbox"), "y0": r.get("y0", 0), "x0": r.get("x0", 0), "idx": r.get("idx", 0)})
    return blocks
def _bk_fix62_fallback_blocks(record_views, image_size=None):
    try:
        return _bk_fix58_blocks_from_records(record_views, image_size)
    except Exception:
        pass
    try:
        page_w = int((image_size or (0, 0))[0]) or 1600
        return _bk_fix51_split_blocks(list(record_views or []), page_w)
    except Exception:
        return [{"type": "paragraph", "text": _bk_fix62_clean(getattr(rv, "text", ""))} for rv in (record_views or []) if _bk_fix62_clean(getattr(rv, "text", ""))]
def _bk_fix62_row_numeric_ratio(row) -> float:
    vals = [_bk_fix62_clean(x) for x in (row or []) if _bk_fix62_clean(x)]
    if not vals:
        return 0.0
    return sum(1 for x in vals if any(ch.isdigit() for ch in x)) / float(len(vals))
def _bk_fix62_should_lift_table_header(row, following_rows) -> bool:
    vals = [_bk_fix62_clean(x) for x in (row or []) if _bk_fix62_clean(x)]
    if not vals or not following_rows:
        return False
    text = " ".join(vals)
    next_ratios = [_bk_fix62_row_numeric_ratio(r) for r in following_rows[:6] if r]
    next_numeric = sum(next_ratios) / max(1.0, float(len(next_ratios)))
    this_numeric = _bk_fix62_row_numeric_ratio(vals)
    letter_heavy = sum(ch.isalpha() for ch in text) >= max(6, sum(ch.isdigit() for ch in text) * 2)
    sparse = len(vals) <= 2
    return bool((sparse or letter_heavy) and next_numeric >= 0.45 and this_numeric < next_numeric)
def _bk_fix62_postprocess_blocks(blocks):
    out = []
    for block in blocks or []:
        if not isinstance(block, dict) or block.get("type") != "table":
            out.append(block)
            continue
        rows = [list(r or []) for r in (block.get("rows") or [])]
        lifted = []
        while len(rows) >= 3 and _bk_fix62_should_lift_table_header(rows[0], rows[1:]):
            txt = " ".join(_bk_fix62_clean(x) for x in rows.pop(0) if _bk_fix62_clean(x)).strip()
            if txt:
                lifted.append({"type": "paragraph", "text": txt})
        out.extend(lifted)
        if rows:
            nb = dict(block)
            nb["rows"] = rows
            out.append(nb)
    return out
def _bk_fix62_export_blocks(record_views, image_size=None):
    blocks = _bk_fix62_build_column_blocks(record_views, image_size)
    if blocks:
        return _bk_fix62_postprocess_blocks(blocks)
    return _bk_fix62_postprocess_blocks(_bk_fix62_fallback_blocks(record_views, image_size))
__all__ = [
    '_bk_fix62_assign_columns',
    '_bk_fix62_box',
    '_bk_fix62_build_column_blocks',
    '_bk_fix62_clean',
    '_bk_fix62_cluster_x_starts',
    '_bk_fix62_column_lines',
    '_bk_fix62_export_blocks',
    '_bk_fix62_fallback_blocks',
    '_bk_fix62_is_dense_numeric_table',
    '_bk_fix62_median_height',
    '_bk_fix62_numeric_density',
    '_bk_fix62_page_size',
    '_bk_fix62_postprocess_blocks',
    '_bk_fix62_record_idx',
    '_bk_fix62_record_x0',
    '_bk_fix62_record_y0',
    '_bk_fix62_record_y1',
    '_bk_fix62_records',
    '_bk_fix62_row_numeric_ratio',
    '_bk_fix62_should_lift_table_header',
]
register_globals('bk', globals(), __all__)



