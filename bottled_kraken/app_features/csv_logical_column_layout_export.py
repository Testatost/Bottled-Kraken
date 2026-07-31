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
_bk_fix53_write_csv = _bk_fix63_write_csv
_bk_fix58_write_csv = _bk_fix63_write_csv
__all__ = [
    '_bk_fix53_write_csv',
    '_bk_fix58_write_csv',
    '_bk_fix63_clean',
    '_bk_fix63_record_index',
    '_bk_fix63_standard_rows',
    '_bk_fix63_write_csv',
]
register_globals('bk', globals(), __all__)
