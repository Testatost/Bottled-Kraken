from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
from bottled_kraken.common import _load_image_color
from bottled_kraken.main_window import MainWindow
from bottled_kraken.export_layout import write_positioned_ods, write_positioned_xlsx
try:
    _BK_SPREADSHEET_PREV_RENDER_FILE = MainWindow._render_file
except Exception:
    _BK_SPREADSHEET_PREV_RENDER_FILE = None
try:
    _BK_SPREADSHEET_PREV_EXPORT_ITEMS = MainWindow._export_format_items
except Exception:
    _BK_SPREADSHEET_PREV_EXPORT_ITEMS = None
try:
    _BK_SPREADSHEET_PREV_EXPORT_EXT = MainWindow._export_ext
except Exception:
    _BK_SPREADSHEET_PREV_EXPORT_EXT = None
try:
    _BK_SPREADSHEET_PREV_EXPORT_FILTER = MainWindow._export_filter
except Exception:
    _BK_SPREADSHEET_PREV_EXPORT_FILTER = None
try:
    _BK_SPREADSHEET_PREV_EXPORT_LABEL = MainWindow._export_display_label
except Exception:
    _BK_SPREADSHEET_PREV_EXPORT_LABEL = None

def _bk_spreadsheet_label(self, key, fallback):
    try:
        value = self._tr(key)
        if value and value != key:
            return value
    except Exception:
        pass
    return fallback

def _bk_spreadsheet_export_items(self):
    if callable(_BK_SPREADSHEET_PREV_EXPORT_ITEMS):
        try:
            items = list(_BK_SPREADSHEET_PREV_EXPORT_ITEMS(self) or [])
        except Exception:
            items = []
    else:
        items = []
    without = [(name, fmt) for name, fmt in items if str(fmt).lower().lstrip('.') not in {'xlsx', 'excel', 'ods', 'calc'}]
    result = []
    xlsx_inserted = False
    ods_inserted = False
    for name, fmt in without:
        result.append((name, fmt))
        fmt_l = str(fmt).lower().lstrip('.')
        if fmt_l == 'docx' and not xlsx_inserted:
            result.append((_bk_spreadsheet_label(self, 'export_format_xlsx', 'Excel (.xlsx)'), 'xlsx'))
            xlsx_inserted = True
        if fmt_l == 'odt' and not ods_inserted:
            result.append((_bk_spreadsheet_label(self, 'export_format_ods', 'LibreOffice Calc (.ods)'), 'ods'))
            ods_inserted = True
    if not xlsx_inserted:
        result.append((_bk_spreadsheet_label(self, 'export_format_xlsx', 'Excel (.xlsx)'), 'xlsx'))
    if not ods_inserted:
        result.append((_bk_spreadsheet_label(self, 'export_format_ods', 'LibreOffice Calc (.ods)'), 'ods'))
    return result

def _bk_spreadsheet_export_ext(self, fmt: str) -> str:
    fmt_l = str(fmt or '').lower().lstrip('.')
    if fmt_l in {'xlsx', 'excel'}:
        return 'xlsx'
    if fmt_l in {'ods', 'calc'}:
        return 'ods'
    if callable(_BK_SPREADSHEET_PREV_EXPORT_EXT):
        return _BK_SPREADSHEET_PREV_EXPORT_EXT(self, fmt)
    return fmt_l or 'txt'

def _bk_spreadsheet_export_filter(self, fmt: str) -> str:
    fmt_l = str(fmt or '').lower().lstrip('.')
    if fmt_l in {'xlsx', 'excel'}:
        return 'Excel (*.xlsx)'
    if fmt_l in {'ods', 'calc'}:
        return 'LibreOffice Calc (*.ods)'
    if callable(_BK_SPREADSHEET_PREV_EXPORT_FILTER):
        return _BK_SPREADSHEET_PREV_EXPORT_FILTER(self, fmt)
    return 'All (*.*)'

def _bk_spreadsheet_export_label(self, fmt: str) -> str:
    fmt_l = str(fmt or '').lower().lstrip('.')
    if fmt_l in {'xlsx', 'excel'}:
        return _bk_spreadsheet_label(self, 'export_format_xlsx', 'Excel (.xlsx)')
    if fmt_l in {'ods', 'calc'}:
        return _bk_spreadsheet_label(self, 'export_format_ods', 'LibreOffice Calc (.ods)')
    if callable(_BK_SPREADSHEET_PREV_EXPORT_LABEL):
        return _BK_SPREADSHEET_PREV_EXPORT_LABEL(self, fmt)
    return str(fmt).upper()

def _bk_spreadsheet_render_file(self, path, fmt, item):
    fmt_l = str(fmt or '').lower().lstrip('.')
    if fmt_l in {'xlsx', 'excel', 'ods', 'calc'}:
        if not item or not getattr(item, 'results', None):
            return None
        _text, _kraken_records, pil_image, record_views = item.results
        try:
            export_image = _load_image_color(item.path)
        except Exception:
            export_image = pil_image
        if fmt_l in {'xlsx', 'excel'}:
            return write_positioned_xlsx(path, item, export_image, record_views)
        return write_positioned_ods(path, item, export_image, record_views)
    if callable(_BK_SPREADSHEET_PREV_RENDER_FILE):
        return _BK_SPREADSHEET_PREV_RENDER_FILE(self, path, fmt, item)
    return None
MainWindow._export_format_items = _bk_spreadsheet_export_items
MainWindow._export_ext = _bk_spreadsheet_export_ext
MainWindow._export_filter = _bk_spreadsheet_export_filter
MainWindow._export_display_label = _bk_spreadsheet_export_label
MainWindow._render_file = _bk_spreadsheet_render_file
__all__ = [
    '_BK_SPREADSHEET_PREV_EXPORT_EXT',
    '_BK_SPREADSHEET_PREV_EXPORT_FILTER',
    '_BK_SPREADSHEET_PREV_EXPORT_ITEMS',
    '_BK_SPREADSHEET_PREV_EXPORT_LABEL',
    '_BK_SPREADSHEET_PREV_RENDER_FILE',
    '_bk_spreadsheet_export_ext',
    '_bk_spreadsheet_export_filter',
    '_bk_spreadsheet_export_items',
    '_bk_spreadsheet_export_label',
    '_bk_spreadsheet_label',
    '_bk_spreadsheet_render_file',
]
register_globals('bk', globals(), __all__)
