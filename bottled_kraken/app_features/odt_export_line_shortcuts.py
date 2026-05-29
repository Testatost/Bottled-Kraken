from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
from bottled_kraken.common import _load_image_color
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox
from bottled_kraken.common import (
    BBox,
    Image,
    List,
    Optional,
    QApplication,
    QKeySequence,
    QLineEdit,
    QPlainTextEdit,
    QShortcut,
    QSpinBox,
    QTextEdit,
    Qt,
    RecordView,
    TaskItem,
)
from bottled_kraken.main_window import MainWindow
def _bk_fix52_screen_max_width(widget=None) -> int:
    try:
        screen = (widget.screen() if widget is not None and hasattr(widget, 'screen') else QApplication.primaryScreen())
        return max(320, int(screen.availableGeometry().width()) - 80)
    except Exception:
        return 1600
def _bk_fix52_adjust_bbox(bb, image_size=None) -> Optional[BBox]:
    if not bb:
        return None
    try:
        x0, y0, x1, y1 = [float(v) for v in bb[:4]]
        w_img = h_img = None
        if image_size:
            w_img, h_img = image_size
        bw = max(1.0, x1 - x0)
        bh = max(1.0, y1 - y0)
        cx = (x0 + x1) / 2.0
        cy = (y0 + y1) / 2.0
        new_w = bw * 1.02
        new_h = bh * 0.70
        nx0 = cx - new_w / 2.0
        nx1 = cx + new_w / 2.0
        ny0 = cy - new_h / 2.0
        ny1 = cy + new_h / 2.0
        if w_img:
            nx0 = max(0.0, min(float(w_img), nx0)); nx1 = max(0.0, min(float(w_img), nx1))
        if h_img:
            ny0 = max(0.0, min(float(h_img), ny0)); ny1 = max(0.0, min(float(h_img), ny1))
        if nx1 <= nx0 + 1 or ny1 <= ny0 + 1:
            return tuple(int(round(v)) for v in (x0, y0, x1, y1))
        return (int(round(nx0)), int(round(ny0)), int(round(nx1)), int(round(ny1)))
    except Exception:
        return bb
def _bk_fix52_apply_default_box_scale_to_recs(recs, image_size=None):
    try:
        for rv in recs or []:
            bb = getattr(rv, 'bbox', None)
            if bb:
                rv.bbox = _bk_fix52_adjust_bbox(bb, image_size)
    except Exception:
        pass
    return recs
try:
    _BK_FIX52_PREV_SYNC_RECS = MainWindow._sync_ui_after_recs_change
except Exception:
    _BK_FIX52_PREV_SYNC_RECS = None
def _bk_fix52_sync_ui_after_recs_change(self, task: TaskItem, keep_row: Optional[int] = None):
    try:
        if (task is not None and getattr(task, 'results', None)
                and bool(getattr(task, '_bk_fresh_kraken_ocr_result', False))
                and not getattr(task, '_bk_fix52_default_box_scale_applied', False)):
            text, kr_records, im, recs = task.results
            image_size = getattr(im, 'size', None)
            if image_size is None and getattr(task, 'path', None):
                try:
                    image_size = _load_image_color(task.path).size
                except Exception:
                    image_size = None
            _bk_fix52_apply_default_box_scale_to_recs(recs, image_size)
            task.results = (text, kr_records, im, recs)
            task._bk_fix52_default_box_scale_applied = True
            task._bk_fix53_default_box_scale_applied = True
            task._bk_fresh_kraken_ocr_result = False
    except Exception:
        pass
    if callable(_BK_FIX52_PREV_SYNC_RECS):
        return _BK_FIX52_PREV_SYNC_RECS(self, task, keep_row=keep_row)
try:
    MainWindow._sync_ui_after_recs_change = _bk_fix52_sync_ui_after_recs_change
except Exception:
    pass
def _bk_fix52_xml_escape(value) -> str:
    return str(value or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
def _bk_fix52_odt_content_xml(blocks) -> str:
    body = []
    for block in blocks or []:
        if block.get('type') == 'table':
            grid = block.get('rows') or []
            if not grid:
                continue
            cols = max(len(r) for r in grid)
            body.append('<table:table table:name="OCR_Table">')
            for _ in range(cols):
                body.append('<table:table-column/>')
            for row in grid:
                body.append('<table:table-row>')
                for c in range(cols):
                    txt = row[c] if c < len(row) else ''
                    body.append('<table:table-cell office:value-type="string"><text:p>%s</text:p></table:table-cell>' % _bk_fix52_xml_escape(txt))
                body.append('</table:table-row>')
            body.append('</table:table>')
            body.append('<text:p/>')
        else:
            txt = str(block.get('text') or '').strip()
            if txt:
                body.append('<text:p>%s</text:p>' % _bk_fix52_xml_escape(txt))
    return ('<?xml version="1.0" encoding="UTF-8"?>'
            '<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
            'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
            'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
            'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
            'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" office:version="1.2">'
            '<office:body><office:text>%s</office:text></office:body></office:document-content>') % ''.join(body)
def _bk_fix52_write_odt(path: str, item: TaskItem, export_image: Image.Image, record_views: List[RecordView]):
    import zipfile as _zipfile
    page_w_px, _page_h_px = export_image.size
    if callable(globals().get('_bk_fix51_split_blocks')):
        blocks = _bk_fix51_split_blocks(list(record_views or []), page_w_px)
    else:
        blocks = [{'type': 'paragraph', 'text': '\n'.join(_bk_fix36_clean_text(getattr(r, 'text', '')) for r in record_views or [])}]
    content = _bk_fix52_odt_content_xml(blocks)
    styles = ('<?xml version="1.0" encoding="UTF-8"?>'
              '<office:document-styles xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
              'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
              'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
              'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
              'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" office:version="1.2">'
              '<office:styles><style:default-style style:family="paragraph"><style:text-properties fo:font-size="9pt"/>'
              '</style:default-style></office:styles></office:document-styles>')
    manifest = ('<?xml version="1.0" encoding="UTF-8"?>'
                '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.2">'
                '<manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.text"/>'
                '<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>'
                '<manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>'
                '</manifest:manifest>')
    meta = ('<?xml version="1.0" encoding="UTF-8"?>'
            '<office:document-meta xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
            'xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" office:version="1.2">'
            '<office:meta><meta:generator>Bottled Kraken</meta:generator></office:meta></office:document-meta>')
    with _zipfile.ZipFile(path, 'w') as z:
        z.writestr('mimetype', 'application/vnd.oasis.opendocument.text', compress_type=_zipfile.ZIP_STORED)
        z.writestr('content.xml', content)
        z.writestr('styles.xml', styles)
        z.writestr('meta.xml', meta)
        z.writestr('META-INF/manifest.xml', manifest)
try:
    _BK_FIX52_PREV_EXPORT_ITEMS = MainWindow._export_format_items
except Exception:
    _BK_FIX52_PREV_EXPORT_ITEMS = None
def _bk_fix52_export_format_items(self):
    items = []
    if callable(_BK_FIX52_PREV_EXPORT_ITEMS):
        try:
            items = list(_BK_FIX52_PREV_EXPORT_ITEMS(self) or [])
        except Exception:
            items = []
    if not any(str(fmt).lower() == 'odt' for _name, fmt in items):
        label = _bk_fix36_tr(self, 'export_format_odt', 'LibreOffice Writer (.odt)')
        inserted = False
        out = []
        for name, fmt in items:
            out.append((name, fmt))
            if str(fmt).lower() == 'docx':
                out.append((label, 'odt'))
                inserted = True
        items = out if inserted else items + [(label, 'odt')]
    return items
try:
    MainWindow._export_format_items = _bk_fix52_export_format_items
except Exception:
    pass
try:
    _BK_FIX52_PREV_EXPORT_EXT = MainWindow._export_ext
except Exception:
    _BK_FIX52_PREV_EXPORT_EXT = None
def _bk_fix52_export_ext(self, fmt: str) -> str:
    if str(fmt or '').lower() == 'odt':
        return 'odt'
    if callable(_BK_FIX52_PREV_EXPORT_EXT):
        return _BK_FIX52_PREV_EXPORT_EXT(self, fmt)
    return str(fmt or '').lower()
try:
    MainWindow._export_ext = _bk_fix52_export_ext
except Exception:
    pass
try:
    _BK_FIX52_PREV_EXPORT_FILTER = MainWindow._export_filter
except Exception:
    _BK_FIX52_PREV_EXPORT_FILTER = None
def _bk_fix52_export_filter(self, fmt: str) -> str:
    if str(fmt or '').lower() == 'odt':
        return 'OpenDocument Text (*.odt)'
    if callable(_BK_FIX52_PREV_EXPORT_FILTER):
        return _BK_FIX52_PREV_EXPORT_FILTER(self, fmt)
    return 'All (*.*)'
try:
    MainWindow._export_filter = _bk_fix52_export_filter
except Exception:
    pass
try:
    _BK_FIX52_PREV_RENDER_FILE = MainWindow._render_file
except Exception:
    _BK_FIX52_PREV_RENDER_FILE = None
def _bk_fix52_render_file(self, path: str, fmt: str, item: TaskItem):
    if str(fmt or '').lower() == 'odt':
        if not item or not getattr(item, 'results', None):
            return
        _text, _kr, _im, record_views = item.results
        export_image = _load_image_color(item.path)
        return _bk_fix52_write_odt(path, item, export_image, record_views)
    if callable(_BK_FIX52_PREV_RENDER_FILE):
        return _BK_FIX52_PREV_RENDER_FILE(self, path, fmt, item)
    return None
try:
    MainWindow._render_file = _bk_fix52_render_file
except Exception:
    pass
def _bk_fix52_focus_is_text_input() -> bool:
    try:
        fw = QApplication.focusWidget()
        return isinstance(fw, (QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox))
    except Exception:
        return False
def _bk_fix52_current_line_row(self) -> int:
    try:
        row = int(self.list_lines.currentRow())
        if row >= 0:
            return row
    except Exception:
        pass
    try:
        rows = self._selected_line_rows()
        if rows:
            return int(rows[0])
    except Exception:
        pass
    return -1
def _bk_fix52_line_shortcut(self, op: str):
    if _bk_fix52_focus_is_text_input():
        return
    try:
        task = self._current_task()
        if not task or not getattr(task, 'results', None):
            return
        selected_rows = []
        try:
            selected_rows = [int(r) for r in self._selected_line_rows()]
        except Exception:
            selected_rows = []
        row = _bk_fix52_current_line_row(self)
        if row < 0 and not selected_rows:
            return
        if op == 'up':
            if selected_rows:
                return self._move_selected_lines(task, selected_rows, -1)
            return self._move_line(task, row, -1)
        if op == 'down':
            if selected_rows:
                return self._move_selected_lines(task, selected_rows, 1)
            return self._move_line(task, row, 1)
        if op == 'above':
            return self._add_line(task, row)
        if op == 'below':
            return self._add_line(task, row + 1)
    except Exception as exc:
        try:
            print(f'FIX8.52 line shortcut failed: {exc}')
        except Exception:
            pass
def _bk_fix52_install_line_shortcuts(self):
    try:
        if getattr(self, '_bk_fix52_line_shortcuts_installed', False):
            return
        self._bk_fix52_line_shortcuts = []
        shortcuts = [(Qt.Key_PageUp, 'up'), (Qt.Key_PageDown, 'down'), ('N', 'above'), ('M', 'below')]
        for key, op in shortcuts:
            sc = QShortcut(QKeySequence(key), self)
            sc.setContext(Qt.ApplicationShortcut)
            sc.activated.connect(lambda w=self, o=op: _bk_fix52_line_shortcut(w, o))
            self._bk_fix52_line_shortcuts.append(sc)
        self._bk_fix52_line_shortcuts_installed = True
    except Exception as exc:
        try:
            print(f'FIX8.52 shortcut install failed: {exc}')
        except Exception:
            pass
try:
    _BK_FIX52_PREV_MAIN_INIT = MainWindow.__init__
except Exception:
    _BK_FIX52_PREV_MAIN_INIT = None
if callable(_BK_FIX52_PREV_MAIN_INIT) and not getattr(MainWindow.__init__, '_bk_fix52_wrapped', False):
    def _bk_fix52_main_init(self, *args, **kwargs):
        _BK_FIX52_PREV_MAIN_INIT(self, *args, **kwargs)
        try:
            _bk_fix52_install_line_shortcuts(self)
        except Exception:
            pass
    _bk_fix52_main_init._bk_fix52_wrapped = True
    MainWindow.__init__ = _bk_fix52_main_init
_SQLITE_PROMPT_EXTRA = (
    ('ai_prompt_sqlite_system', 'lm_prompt_sqlite_system'),
    ('ai_prompt_sqlite_user', 'lm_prompt_sqlite_user'),
)
try:
    if '_BK_LM_PROMPT_KEYS' in globals():
        current = list(_BK_LM_PROMPT_KEYS)
        seen = {k for k, _ in current}
        for item in _SQLITE_PROMPT_EXTRA:
            if item[0] not in seen:
                current.append(item)
        globals()['_BK_LM_PROMPT_KEYS'] = tuple(current)
except Exception:
    pass
__all__ = [
    '_SQLITE_PROMPT_EXTRA',
    '_bk_fix52_adjust_bbox',
    '_bk_fix52_apply_default_box_scale_to_recs',
    '_bk_fix52_current_line_row',
    '_bk_fix52_export_ext',
    '_bk_fix52_export_filter',
    '_bk_fix52_export_format_items',
    '_bk_fix52_focus_is_text_input',
    '_bk_fix52_install_line_shortcuts',
    '_bk_fix52_line_shortcut',
    '_bk_fix52_odt_content_xml',
    '_bk_fix52_render_file',
    '_bk_fix52_screen_max_width',
    '_bk_fix52_sync_ui_after_recs_change',
    '_bk_fix52_write_odt',
    '_bk_fix52_xml_escape',
]
register_globals('bk', globals(), __all__)
