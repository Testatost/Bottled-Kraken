from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
from bottled_kraken.common import _load_image_color
from bottled_kraken.common import (
    Any,
    Dict,
    Image,
    List,
    QFileDialog,
    QMessageBox,
    RecordView,
    TaskItem,
    group_rows_by_y,
    json,
    os,
    re,
    translation,
)
from bottled_kraken.main_window import MainWindow
def _bk_fix40_write_structured_txt_export(path: str, record_views: List[RecordView], image_size=None):
    _bk_fix40_resolve_ditto_marks_in_recs(record_views)
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Bottled Kraken line export\n")
        f.write("# idx\tx\ty\twidth\theight\ttext\n")
        for i, rv in enumerate(record_views or []):
            txt = str(getattr(rv, "text", "") or "")
            if getattr(rv, "bbox", None):
                x0, y0, x1, y1 = [int(v) for v in rv.bbox]
                cols = [
                    i,
                    x0,
                    y0,
                    max(0, x1 - x0),
                    max(0, y1 - y0),
                    json.dumps(txt, ensure_ascii=False),
                ]
            else:
                cols = [i, "", "", "", "", json.dumps(txt, ensure_ascii=False)]
            f.write("\t".join(str(c) for c in cols) + "\n")
def _bk_fix40_export_single_interactive(self, item: TaskItem, fmt: str):
    base_name = self._export_default_stem(item, fmt) if hasattr(self, "_export_default_stem") else os.path.splitext(getattr(item, "display_name", "ocr"))[0]
    base_dir = getattr(self, "current_export_dir", "") or os.path.dirname(getattr(item, "path", "") or "") or os.getcwd()
    ext = self._export_ext(fmt) if hasattr(self, "_export_ext") else str(fmt).lower()
    dest_path, _ = QFileDialog.getSaveFileName(
        self,
        self._tr("dlg_save"),
        os.path.join(base_dir, base_name),
        self._export_filter(fmt) if hasattr(self, "_export_filter") else "All (*.*)",
    )
    if not dest_path:
        return
    if ext and not dest_path.lower().endswith(f".{ext}"):
        dest_path += f".{ext}"
    try:
        self._render_file(dest_path, fmt, item)
    except Exception as e:
        QMessageBox.critical(self, self._tr("err_title"), str(e))
        return
    try:
        self.current_export_dir = os.path.dirname(dest_path)
        self._log(self._tr_log("log_export_single", item.display_name, dest_path))
        self.status_bar.showMessage(self._tr("msg_exported", os.path.basename(dest_path)))
    except Exception:
        pass
try:
    MainWindow._export_single_interactive = _bk_fix40_export_single_interactive
except Exception:
    pass
__all__ = [
    '_bk_fix40_export_single_interactive',
    '_bk_fix40_write_structured_txt_export',
]
register_globals('bk', globals(), __all__)
