from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
from bottled_kraken.common import _load_image_color
from bottled_kraken.common import (
    List,
    RecordView,
    TaskItem,
)
from bottled_kraken.main_window import MainWindow
import csv as _bk_fix63_csv
def _bk_fix63_clean(value) -> str:
    try:
        return _bk_fix62_clean(value)
    except Exception:
        try:
            return _bk_fix36_clean_text(value)
        except Exception:
            return " ".join(str(value or "").replace("\r", "\n").split())
def _bk_fix63_trim_row(row):
    cells = [_bk_fix63_clean(cell) for cell in (row or [])]
    while cells and not cells[-1]:
        cells.pop()
    return cells
def _bk_fix63_compress_grid(grid):
    raw_rows = [list(row or []) for row in (grid or [])]
    if not raw_rows:
        return []
    width = max((len(row) for row in raw_rows), default=0)
    rect = []
    for row in raw_rows:
        rect.append([_bk_fix63_clean(cell) for cell in row] + [""] * max(0, width - len(row)))
    used_cols = []
    for col in range(width):
        if any(str(row[col]).strip() for row in rect):
            used_cols.append(col)
    if not used_cols:
        return []
    out = []
    previous_blank = False
    for row in rect:
        compact = _bk_fix63_trim_row([row[col] for col in used_cols])
        blank = not any(compact)
        if blank:
            if not previous_blank and out:
                out.append([])
            previous_blank = True
            continue
        out.append(compact)
        previous_blank = False
    while out and not out[-1]:
        out.pop()
    return out
def _bk_fix63_rows_from_blocks(blocks):
    rows = []
    for block in blocks or []:
        typ = str(block.get("type") or "").lower()
        if typ == "columns":
            cols = [list(col or []) for col in (block.get("columns") or [])]
            if not cols:
                continue
            row_count = max((len(col) for col in cols), default=0)
            if rows and rows[-1]:
                rows.append([])
            for i in range(row_count):
                row = []
                for col in cols:
                    row.append(col[i] if i < len(col) else "")
                trimmed = _bk_fix63_trim_row(row)
                if any(trimmed):
                    rows.append(trimmed)
            if rows and rows[-1]:
                rows.append([])
        elif typ == "table":
            grid_rows = _bk_fix63_compress_grid(block.get("rows") or [])
            if not grid_rows:
                continue
            if rows and rows[-1]:
                rows.append([])
            rows.extend(grid_rows)
            if rows and rows[-1]:
                rows.append([])
        else:
            text = _bk_fix63_clean(block.get("text", ""))
            if not text:
                continue
            for line in str(text).splitlines() or [text]:
                line = _bk_fix63_clean(line)
                if line:
                    rows.append([line])
    while rows and not rows[-1]:
        rows.pop()
    return rows
def _bk_fix63_export_blocks(record_views, image_size=None):
    try:
        return _bk_fix62_export_blocks(record_views, image_size)
    except Exception:
        pass
    try:
        return _bk_fix58_blocks_from_records(record_views, image_size)
    except Exception:
        return [{"type": "paragraph", "text": _bk_fix63_clean(getattr(rv, "text", ""))} for rv in (record_views or []) if _bk_fix63_clean(getattr(rv, "text", ""))]
def _bk_fix63_bbox_tuple(rv):
    bbox = getattr(rv, "bbox", None)
    if not bbox:
        return ("", "", "", "")
    try:
        values = list(bbox)
    except Exception:
        return ("", "", "", "")
    values = (values + ["", "", "", ""])[:4]
    out = []
    for value in values:
        try:
            number = float(value)
            if number.is_integer():
                out.append(str(int(number)))
            else:
                out.append(f"{number:.2f}".rstrip("0").rstrip("."))
        except Exception:
            out.append(str(value or ""))
    return tuple(out)
def _bk_fix63_record_index(rv, fallback: int) -> str:
    raw = getattr(rv, "idx", None)
    try:
        number = int(raw)
    except Exception:
        number = fallback
    if number <= 0:
        number = fallback
    return f"{number:04d}"
def _bk_fix63_standard_rows(record_views: List[RecordView]):
    rows = [["line_no", "text"]]
    for fallback, rv in enumerate(record_views or [], start=1):
        text = _bk_fix63_clean(getattr(rv, "text", ""))
        if not text:
            continue
        rows.append([_bk_fix63_record_index(rv, fallback), text])
    return rows
def _bk_fix63_write_csv(path: str, record_views: List[RecordView], image_size=None):
    rows = _bk_fix63_standard_rows(record_views)
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = _bk_fix63_csv.writer(
            fh,
            delimiter=",",
            quotechar='"',
            quoting=_bk_fix63_csv.QUOTE_ALL,
            lineterminator="\r\n",
        )
        writer.writerows(rows)
try:
    _BK_FIX63_PREV_RENDER_FILE = MainWindow._render_file
except Exception:
    _BK_FIX63_PREV_RENDER_FILE = None
def _bk_fix63_render_file(self, path: str, fmt: str, item: TaskItem):
    fmt_l = str(fmt or "").lower()
    if fmt_l in {"csv", ".csv"}:
        if not item or not getattr(item, "results", None):
            return
        _text, _kr, pil_image, record_views = item.results
        try:
            export_image = _load_image_color(item.path)
            image_size = export_image.size
        except Exception:
            image_size = getattr(pil_image, "size", None)
        return _bk_fix63_write_csv(path, record_views, image_size)
    if callable(_BK_FIX63_PREV_RENDER_FILE):
        return _BK_FIX63_PREV_RENDER_FILE(self, path, fmt, item)
    return None
try:
    MainWindow._render_file = _bk_fix63_render_file
except Exception:
    pass
_bk_fix53_write_csv = _bk_fix63_write_csv
_bk_fix58_write_csv = _bk_fix63_write_csv
__all__ = [
    '_bk_fix53_write_csv',
    '_bk_fix58_write_csv',
    '_bk_fix63_bbox_tuple',
    '_bk_fix63_clean',
    '_bk_fix63_compress_grid',
    '_bk_fix63_export_blocks',
    '_bk_fix63_record_index',
    '_bk_fix63_render_file',
    '_bk_fix63_rows_from_blocks',
    '_bk_fix63_standard_rows',
    '_bk_fix63_trim_row',
    '_bk_fix63_write_csv',
]
register_globals('bk', globals(), __all__)
