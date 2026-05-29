from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
from bottled_kraken.common import _load_image_color
from bottled_kraken.common import (
    Image,
    List,
    RecordView,
    TaskItem,
)
from bottled_kraken.main_window import MainWindow
import csv as _bk_fix58_csv
import re as _bk_fix58_re
import zipfile as _bk_fix58_zipfile
from xml.sax.saxutils import escape as _bk_fix58_xml_escape_lib
def _bk_fix58_xml_text(value) -> str:
    text = str(value or "")
    cleaned = []
    for ch in text:
        code = ord(ch)
        if ch in "\t\n\r" or 0x20 <= code <= 0xD7FF or 0xE000 <= code <= 0xFFFD:
            cleaned.append(ch)
        else:
            cleaned.append(" ")
    return _bk_fix58_xml_escape_lib("".join(cleaned), {'"': '&quot;', "'": '&apos;'})
def _bk_fix58_blocks_from_records(record_views, image_size=None):
    page_w = 0
    try:
        page_w = int((image_size or (0, 0))[0])
    except Exception:
        page_w = 0
    try:
        if callable(globals().get('_bk_fix51_split_blocks')):
            return _bk_fix51_split_blocks(list(record_views or []), page_w)
    except Exception:
        pass
    return [
        {'type': 'paragraph', 'text': _bk_fix36_clean_text(getattr(rv, 'text', ''))}
        for rv in (record_views or [])
        if _bk_fix36_clean_text(getattr(rv, 'text', ''))
    ]
def _bk_fix58_odt_content_xml(blocks) -> str:
    body = []
    table_index = 1
    for block in blocks or []:
        if block.get('type') == 'table':
            grid = block.get('rows') or []
            if not grid:
                continue
            cols = max((len(r) for r in grid), default=0)
            if cols < 2:
                for row in grid:
                    line = ' '.join(_bk_fix36_clean_text(c) for c in row if _bk_fix36_clean_text(c)).strip()
                    if line:
                        body.append('<text:p text:style-name="P1">%s</text:p>' % _bk_fix58_xml_text(line))
                continue
            body.append('<table:table table:name="OCR_Table_%d" table:style-name="Table1">' % table_index)
            table_index += 1
            for _ in range(cols):
                body.append('<table:table-column table:style-name="TableCol"/>')
            for row in grid:
                body.append('<table:table-row>')
                for c in range(cols):
                    txt = row[c] if c < len(row) else ''
                    body.append(
                        '<table:table-cell table:style-name="TableCell" office:value-type="string">'
                        '<text:p text:style-name="TableP">%s</text:p>'
                        '</table:table-cell>' % _bk_fix58_xml_text(txt)
                    )
                body.append('</table:table-row>')
            body.append('</table:table>')
            body.append('<text:p text:style-name="P1"/>')
        else:
            txt = str(block.get('text') or '').strip()
            if txt:
                for line in str(txt).splitlines() or [txt]:
                    line = line.strip()
                    if line:
                        body.append('<text:p text:style-name="P1">%s</text:p>' % _bk_fix58_xml_text(line))
    return ''.join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<office:document-content ',
        'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" ',
        'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" ',
        'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" ',
        'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" ',
        'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" ',
        'xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" ',
        'office:version="1.2">',
        '<office:scripts/>',
        '<office:font-face-decls>',
        '<style:font-face style:name="Arial" svg:font-family="Arial"/>',
        '<style:font-face style:name="Courier New" svg:font-family="Courier New"/>',
        '</office:font-face-decls>',
        '<office:automatic-styles>',
        '<style:style style:name="P1" style:family="paragraph"><style:text-properties fo:font-size="9pt" style:font-name="Arial"/></style:style>',
        '<style:style style:name="TableP" style:family="paragraph"><style:paragraph-properties fo:margin-top="0cm" fo:margin-bottom="0cm"/><style:text-properties fo:font-size="7pt" style:font-name="Arial"/></style:style>',
        '<style:style style:name="Table1" style:family="table"><style:table-properties table:align="left"/></style:style>',
        '<style:style style:name="TableCol" style:family="table-column"><style:table-column-properties style:column-width="1.7cm"/></style:style>',
        '<style:style style:name="TableCell" style:family="table-cell"><style:table-cell-properties fo:border="0.05pt solid #808080" fo:padding="0.03cm"/></style:style>',
        '</office:automatic-styles>',
        '<office:body><office:text>',
        ''.join(body),
        '</office:text></office:body></office:document-content>',
    ])
def _bk_fix58_odt_styles_xml() -> str:
    return ''.join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<office:document-styles ',
        'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" ',
        'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" ',
        'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" ',
        'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" ',
        'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" ',
        'xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" ',
        'office:version="1.2">',
        '<office:font-face-decls>',
        '<style:font-face style:name="Arial" svg:font-family="Arial"/>',
        '<style:font-face style:name="Courier New" svg:font-family="Courier New"/>',
        '</office:font-face-decls>',
        '<office:styles>',
        '<style:default-style style:family="paragraph"><style:text-properties fo:font-size="9pt" style:font-name="Arial"/></style:default-style>',
        '<style:default-style style:family="table-cell"><style:table-cell-properties fo:border="none" fo:padding="0.02cm"/></style:default-style>',
        '</office:styles>',
        '<office:automatic-styles>',
        '<style:page-layout style:name="pm1"><style:page-layout-properties fo:page-width="21cm" fo:page-height="29.7cm" fo:margin-top="1cm" fo:margin-bottom="1cm" fo:margin-left="1cm" fo:margin-right="1cm"/></style:page-layout>',
        '</office:automatic-styles>',
        '<office:master-styles><style:master-page style:name="Standard" style:page-layout-name="pm1"/></office:master-styles>',
        '</office:document-styles>',
    ])
def _bk_fix58_odt_manifest_xml() -> str:
    return ''.join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.2">',
        '<manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.text"/>',
        '<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>',
        '<manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>',
        '<manifest:file-entry manifest:full-path="meta.xml" manifest:media-type="text/xml"/>',
        '<manifest:file-entry manifest:full-path="settings.xml" manifest:media-type="text/xml"/>',
        '</manifest:manifest>',
    ])
def _bk_fix58_write_odt(path: str, item: TaskItem, export_image: Image.Image, record_views: List[RecordView]):
    image_size = getattr(export_image, 'size', None) or (0, 0)
    blocks = _bk_fix58_blocks_from_records(record_views, image_size)
    content = _bk_fix58_odt_content_xml(blocks)
    styles = _bk_fix58_odt_styles_xml()
    manifest = _bk_fix58_odt_manifest_xml()
    meta = ''.join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<office:document-meta xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" ',
        'xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" office:version="1.2">',
        '<office:meta><meta:generator>Bottled Kraken</meta:generator></office:meta>',
        '</office:document-meta>',
    ])
    settings = '<?xml version="1.0" encoding="UTF-8"?><office:document-settings xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" office:version="1.2"><office:settings/></office:document-settings>'
    with _bk_fix58_zipfile.ZipFile(path, 'w') as z:
        info = _bk_fix58_zipfile.ZipInfo('mimetype')
        info.date_time = (2020, 1, 1, 0, 0, 0)
        info.compress_type = _bk_fix58_zipfile.ZIP_STORED
        z.writestr(info, 'application/vnd.oasis.opendocument.text')
        for name, data in [
            ('content.xml', content),
            ('styles.xml', styles),
            ('meta.xml', meta),
            ('settings.xml', settings),
            ('META-INF/manifest.xml', manifest),
        ]:
            zi = _bk_fix58_zipfile.ZipInfo(name)
            zi.date_time = (2020, 1, 1, 0, 0, 0)
            zi.compress_type = _bk_fix58_zipfile.ZIP_DEFLATED
            z.writestr(zi, data.encode('utf-8'))
def _bk_fix58_spatial_lines(record_views, image_size=None) -> List[str]:
    try:
        page_w = int((image_size or (0, 0))[0]) or 1600
    except Exception:
        page_w = 1600
    try:
        rows = _bk_fix51_group_rows(list(record_views or []), page_w)
        txt = _bk_fix51_text_columns(rows, page_w, max_cols=180)
    except Exception:
        txt = ''
    if not _bk_fix36_clean_text(txt):
        txt = '\n'.join(_bk_fix36_clean_text(getattr(rv, 'text', '')) for rv in (record_views or []) if _bk_fix36_clean_text(getattr(rv, 'text', '')))
    return [ln.rstrip() for ln in str(txt or '').splitlines()]
def _bk_fix58_chunks_from_line(line: str):
    chunks = []
    for m in _bk_fix58_re.finditer(r'\S+(?: \S+)*(?=(?: {2,}|\t|$))', line or ''):
        text = m.group(0).strip()
        if text:
            chunks.append((m.start(), text))
    return chunks
def _bk_fix58_cluster_positions(values: List[int]) -> List[int]:
    if not values:
        return []
    vals = sorted(int(v) for v in values)
    clusters = []
    threshold = 4
    for v in vals:
        if not clusters:
            clusters.append([v])
            continue
        center = sum(clusters[-1]) / len(clusters[-1])
        if abs(v - center) <= threshold:
            clusters[-1].append(v)
        else:
            clusters.append([v])
    return [int(round(sum(c) / len(c))) for c in clusters]
def _bk_fix58_rows_from_spatial_text(lines: List[str]) -> List[List[str]]:
    line_chunks = [_bk_fix58_chunks_from_line(ln) for ln in lines]
    starts = [s for chunks in line_chunks for s, txt in chunks if txt]
    anchors = _bk_fix58_cluster_positions(starts)
    if not anchors:
        return [[ln.strip()] for ln in lines if ln.strip()]
    rows = []
    for chunks in line_chunks:
        if not chunks:
            rows.append([])
            continue
        row = [''] * len(anchors)
        for start, text in chunks:
            idx = min(range(len(anchors)), key=lambda i: abs(start - anchors[i]))
            j = idx
            while j < len(row) and row[j]:
                if abs(anchors[j] - start) <= 2:
                    row[j] = (row[j] + ' ' + text).strip()
                    break
                j += 1
            else:
                if j < len(row):
                    row[j] = text
                else:
                    row[idx] = (row[idx] + ' ' + text).strip() if row[idx] else text
                continue
            if j < len(row) and row[j] == text:
                continue
        while row and not row[-1]:
            row.pop()
        rows.append(row)
    nonempty = [r for r in rows if any(c.strip() for c in r)]
    if not nonempty:
        return []
    max_len = max(len(r) for r in nonempty)
    used_cols = set()
    for r in nonempty:
        for i, c in enumerate(r):
            if str(c).strip():
                used_cols.add(i)
    if used_cols:
        first, last = min(used_cols), max(used_cols)
        rows = [(r + [''] * max(0, max_len - len(r)))[first:last + 1] for r in rows]
    return rows
def _bk_fix58_write_csv(path: str, record_views: List[RecordView], image_size=None):
    lines = _bk_fix58_spatial_lines(record_views, image_size)
    rows = _bk_fix58_rows_from_spatial_text(lines)
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = _bk_fix58_csv.writer(f, delimiter=',', quotechar='"', quoting=_bk_fix58_csv.QUOTE_ALL)
        for row in rows:
            if not row:
                writer.writerow([])
            else:
                writer.writerow([_bk_fix36_clean_text(c) for c in row])
try:
    _BK_FIX58_PREV_RENDER_FILE = MainWindow._render_file
except Exception:
    _BK_FIX58_PREV_RENDER_FILE = None
def _bk_fix58_render_file(self, path: str, fmt: str, item: TaskItem):
    fmt_l = str(fmt or '').lower()
    if fmt_l in {'csv', '.csv'}:
        if not item or not getattr(item, 'results', None):
            return
        _text, _kr, pil_image, record_views = item.results
        try:
            export_image = _load_image_color(item.path)
            image_size = export_image.size
        except Exception:
            image_size = getattr(pil_image, 'size', None)
        return _bk_fix58_write_csv(path, record_views, image_size)
    if fmt_l in {'odt', '.odt'}:
        if not item or not getattr(item, 'results', None):
            return
        _text, _kr, pil_image, record_views = item.results
        try:
            export_image = _load_image_color(item.path)
        except Exception:
            export_image = pil_image
        return _bk_fix58_write_odt(path, item, export_image, record_views)
    if callable(_BK_FIX58_PREV_RENDER_FILE):
        return _BK_FIX58_PREV_RENDER_FILE(self, path, fmt, item)
    return None
try:
    MainWindow._render_file = _bk_fix58_render_file
except Exception:
    pass
_bk_fix52_write_odt = _bk_fix58_write_odt
_bk_fix53_write_csv = _bk_fix58_write_csv
__all__ = [
    '_bk_fix52_write_odt',
    '_bk_fix53_write_csv',
    '_bk_fix58_blocks_from_records',
    '_bk_fix58_chunks_from_line',
    '_bk_fix58_cluster_positions',
    '_bk_fix58_odt_content_xml',
    '_bk_fix58_odt_manifest_xml',
    '_bk_fix58_odt_styles_xml',
    '_bk_fix58_render_file',
    '_bk_fix58_rows_from_spatial_text',
    '_bk_fix58_spatial_lines',
    '_bk_fix58_write_csv',
    '_bk_fix58_write_odt',
    '_bk_fix58_xml_text',
]
register_globals('bk', globals(), __all__)
