from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals("bk", globals())
from bottled_kraken.common import _load_image_color
from bottled_kraken.main_window import MainWindow
from bottled_kraken.export_layout import write_plain_csv, write_positioned_docx, write_positioned_odt, write_spatial_txt
try:
    _BK_FINAL_EXPORT_PREV_RENDER_FILE = MainWindow._render_file
except Exception:
    _BK_FINAL_EXPORT_PREV_RENDER_FILE = None
def _bk_final_export_render_file(self, path, fmt, item):
    fmt_name = str(fmt or "").lower().lstrip(".")
    if fmt_name in {"docx", "word", "odt", "txt", "text", "txt_plain", "csv"}:
        if not item or not getattr(item, "results", None):
            return None
        _text, _kraken_records, pil_image, record_views = item.results
        try:
            export_image = _load_image_color(item.path)
        except Exception:
            export_image = pil_image
        image_size = getattr(export_image, "size", None) or getattr(pil_image, "size", None)
        if fmt_name in {"txt", "text", "txt_plain"}:
            return write_spatial_txt(path, record_views, image_size)
        if fmt_name == "csv":
            return write_plain_csv(path, record_views, image_size)
        if fmt_name == "odt":
            return write_positioned_odt(path, item, export_image, record_views)
        return write_positioned_docx(path, item, export_image, record_views)
    if callable(_BK_FINAL_EXPORT_PREV_RENDER_FILE):
        return _BK_FINAL_EXPORT_PREV_RENDER_FILE(self, path, fmt, item)
    return None
MainWindow._render_file = _bk_final_export_render_file
__all__ = ["_BK_FINAL_EXPORT_PREV_RENDER_FILE", "_bk_final_export_render_file"]
register_globals("bk", globals(), __all__)
