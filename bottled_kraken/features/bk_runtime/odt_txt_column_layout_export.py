"""Column-aware TXT/ODT export for OCR line boxes.

This late runtime patch fixes the common case where historic pages contain
separate text columns.  The older export path treated those columns as a grid
or flattened them into one long sequence.  Here we detect stable vertical text
bands and write them as real columns: TXT uses side-by-side monospace padding,
ODT uses a borderless table for column flow.  Dense numeric tables still fall
back to the previous grid/table exporter.
"""

from .shared import *
from .ui_components import *
from .workers import *
from .dialogs import *
from .image_edit import *
from .main_window import MainWindow

import zipfile as _bk_fix62_zipfile
from xml.sax.saxutils import escape as _bk_fix62_xml_escape

def _bk_fix62_xml_text(value) -> str:
    text = str(value or "")
    safe = []
    for ch in text:
        code = ord(ch)
        if ch in "\t\n\r" or 0x20 <= code <= 0xD7FF or 0xE000 <= code <= 0xFFFD:
            safe.append(ch)
        else:
            safe.append(" ")
    return _bk_fix62_xml_escape("".join(safe), {'"': '&quot;', "'": '&apos;'})

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

def _bk_fix62_blocks_sorted_visual(blocks):
    def key(block):
        bb = block.get("bbox") if isinstance(block, dict) else None
        if bb and len(bb) >= 4:
            return (float(bb[1]), float(bb[0]))
        return (float(block.get("y0", 10**9)) if isinstance(block, dict) else 10**9, float(block.get("x0", 0)) if isinstance(block, dict) else 0)
    return sorted([b for b in (blocks or []) if b], key=key)

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

def _bk_fix62_txt_from_blocks(blocks) -> str:
    lines = []
    for block in blocks or []:
        if block.get("type") == "columns":
            cols = [list(c or []) for c in block.get("columns") or []]
            widths = [min(78, max(12, max((len(x) for x in col), default=0) + 4)) for col in cols]
            count = max((len(c) for c in cols), default=0)
            for i in range(count):
                parts = []
                for ci, col in enumerate(cols):
                    val = col[i] if i < len(col) else ""
                    parts.append(val.ljust(widths[ci]) if ci < len(cols) - 1 else val)
                line = "  ".join(parts).rstrip()
                if line.strip():
                    lines.append(line)
            lines.append("")
        elif block.get("type") == "table":
            grid = block.get("rows") or []
            if not grid:
                continue
            cols = max((len(r) for r in grid), default=0)
            widths = []
            for c in range(cols):
                widths.append(min(42, max(4, max((len(str(row[c])) if c < len(row) else 0 for row in grid), default=0) + 2)))
            for row in grid:
                parts = []
                for c in range(cols):
                    val = _bk_fix62_clean(row[c] if c < len(row) else "")
                    parts.append(val.ljust(widths[c]) if c < cols - 1 else val)
                if any(p.strip() for p in parts):
                    lines.append(" ".join(parts).rstrip())
            lines.append("")
        else:
            text = _bk_fix62_clean(block.get("text", ""))
            if text:
                lines.append(text)
    return "\n".join(lines).rstrip() + "\n"

def _bk_fix62_odt_content_xml(blocks) -> str:
    body = []
    table_index = 1
    for block in blocks or []:
        typ = block.get("type")
        if typ == "columns":
            cols = [list(c or []) for c in block.get("columns") or []]
            if not cols:
                continue
            body.append('<table:table table:name="OCR_Columns_%d" table:style-name="ColumnTable">' % table_index)
            table_index += 1
            for _ in cols:
                body.append('<table:table-column table:style-name="ColumnCol"/>')
            body.append('<table:table-row>')
            for col in cols:
                body.append('<table:table-cell table:style-name="ColumnCell" office:value-type="string">')
                for line in col:
                    if _bk_fix62_clean(line):
                        body.append('<text:p text:style-name="ColumnP">%s</text:p>' % _bk_fix62_xml_text(line))
                body.append('</table:table-cell>')
            body.append('</table:table-row></table:table><text:p text:style-name="P1"/>')
        elif typ == "table":
            grid = block.get("rows") or []
            cols = max((len(r) for r in grid), default=0)
            if cols < 2:
                continue
            body.append('<table:table table:name="OCR_Table_%d" table:style-name="Table1">' % table_index)
            table_index += 1
            for _ in range(cols):
                body.append('<table:table-column table:style-name="TableCol"/>')
            for row in grid:
                body.append('<table:table-row>')
                for c in range(cols):
                    txt = row[c] if c < len(row) else ""
                    body.append('<table:table-cell table:style-name="TableCell" office:value-type="string"><text:p text:style-name="TableP">%s</text:p></table:table-cell>' % _bk_fix62_xml_text(txt))
                body.append('</table:table-row>')
            body.append('</table:table><text:p text:style-name="P1"/>')
        else:
            txt = _bk_fix62_clean(block.get("text", ""))
            if txt:
                body.append('<text:p text:style-name="P1">%s</text:p>' % _bk_fix62_xml_text(txt))
    return ''.join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<office:document-content ',
        'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" ',
        'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" ',
        'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" ',
        'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" ',
        'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" ',
        'xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" ',
        'office:version="1.2"><office:scripts/><office:font-face-decls>',
        '<style:font-face style:name="Arial" svg:font-family="Arial"/>',
        '<style:font-face style:name="Courier New" svg:font-family="Courier New"/>',
        '</office:font-face-decls><office:automatic-styles>',
        '<style:style style:name="P1" style:family="paragraph"><style:paragraph-properties fo:margin-bottom="0.04cm"/><style:text-properties fo:font-size="8.5pt" style:font-name="Arial"/></style:style>',
        '<style:style style:name="ColumnP" style:family="paragraph"><style:paragraph-properties fo:margin-top="0cm" fo:margin-bottom="0.02cm"/><style:text-properties fo:font-size="7.2pt" style:font-name="Arial"/></style:style>',
        '<style:style style:name="TableP" style:family="paragraph"><style:paragraph-properties fo:margin-top="0cm" fo:margin-bottom="0cm"/><style:text-properties fo:font-size="6.3pt" style:font-name="Arial"/></style:style>',
        '<style:style style:name="ColumnTable" style:family="table"><style:table-properties table:align="left"/></style:style>',
        '<style:style style:name="ColumnCol" style:family="table-column"><style:table-column-properties style:rel-column-width="32767*"/></style:style>',
        '<style:style style:name="ColumnCell" style:family="table-cell"><style:table-cell-properties fo:border="none" fo:padding="0.10cm"/></style:style>',
        '<style:style style:name="Table1" style:family="table"><style:table-properties table:align="left"/></style:style>',
        '<style:style style:name="TableCol" style:family="table-column"><style:table-column-properties style:column-width="1.15cm"/></style:style>',
        '<style:style style:name="TableCell" style:family="table-cell"><style:table-cell-properties fo:border="0.05pt solid #808080" fo:padding="0.02cm"/></style:style>',
        '</office:automatic-styles><office:body><office:text>', ''.join(body), '</office:text></office:body></office:document-content>'
    ])

def _bk_fix62_odt_styles_xml() -> str:
    return ''.join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<office:document-styles xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" office:version="1.2">',
        '<office:font-face-decls><style:font-face style:name="Arial" svg:font-family="Arial"/><style:font-face style:name="Courier New" svg:font-family="Courier New"/></office:font-face-decls>',
        '<office:styles><style:default-style style:family="paragraph"><style:text-properties fo:font-size="8.5pt" style:font-name="Arial"/></style:default-style></office:styles>',
        '<office:automatic-styles><style:page-layout style:name="pm1"><style:page-layout-properties fo:page-width="21cm" fo:page-height="29.7cm" fo:margin-top="0.8cm" fo:margin-bottom="0.8cm" fo:margin-left="0.8cm" fo:margin-right="0.8cm"/></style:page-layout></office:automatic-styles>',
        '<office:master-styles><style:master-page style:name="Standard" style:page-layout-name="pm1"/></office:master-styles></office:document-styles>'
    ])

def _bk_fix62_write_odt(path: str, item: TaskItem, export_image: Image.Image, record_views: List[RecordView]):
    image_size = getattr(export_image, "size", None) or (0, 0)
    blocks = _bk_fix62_export_blocks(record_views, image_size)
    content = _bk_fix62_odt_content_xml(blocks)
    styles = _bk_fix62_odt_styles_xml()
    meta = '<?xml version="1.0" encoding="UTF-8"?><office:document-meta xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" office:version="1.2"><office:meta><meta:generator>Bottled Kraken</meta:generator></office:meta></office:document-meta>'
    settings = '<?xml version="1.0" encoding="UTF-8"?><office:document-settings xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" office:version="1.2"><office:settings/></office:document-settings>'
    manifest = '<?xml version="1.0" encoding="UTF-8"?><manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.2"><manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.text"/><manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/><manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/><manifest:file-entry manifest:full-path="meta.xml" manifest:media-type="text/xml"/><manifest:file-entry manifest:full-path="settings.xml" manifest:media-type="text/xml"/></manifest:manifest>'
    with _bk_fix62_zipfile.ZipFile(path, "w") as z:
        info = _bk_fix62_zipfile.ZipInfo("mimetype")
        info.date_time = (2020, 1, 1, 0, 0, 0)
        info.compress_type = _bk_fix62_zipfile.ZIP_STORED
        z.writestr(info, "application/vnd.oasis.opendocument.text")
        for name, data in [("content.xml", content), ("styles.xml", styles), ("meta.xml", meta), ("settings.xml", settings), ("META-INF/manifest.xml", manifest)]:
            zi = _bk_fix62_zipfile.ZipInfo(name)
            zi.date_time = (2020, 1, 1, 0, 0, 0)
            zi.compress_type = _bk_fix62_zipfile.ZIP_DEFLATED
            z.writestr(zi, data.encode("utf-8"))

def _bk_fix62_write_txt(path: str, record_views: List[RecordView], image_size=None):
    blocks = _bk_fix62_export_blocks(record_views, image_size)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(_bk_fix62_txt_from_blocks(blocks))

try:
    _BK_FIX62_PREV_RENDER_FILE = MainWindow._render_file
except Exception:
    _BK_FIX62_PREV_RENDER_FILE = None

def _bk_fix62_render_file(self, path: str, fmt: str, item: TaskItem):
    fmt_l = str(fmt or "").lower()
    if fmt_l in {"txt", "text", "txt_plain", ".txt"}:
        if not item or not getattr(item, "results", None):
            return
        _text, _kr, pil_image, record_views = item.results
        try:
            export_image = _load_image_color(item.path)
            image_size = export_image.size
        except Exception:
            image_size = getattr(pil_image, "size", None)
        return _bk_fix62_write_txt(path, record_views, image_size)
    if fmt_l in {"odt", ".odt"}:
        if not item or not getattr(item, "results", None):
            return
        _text, _kr, pil_image, record_views = item.results
        try:
            export_image = _load_image_color(item.path)
        except Exception:
            export_image = pil_image
        return _bk_fix62_write_odt(path, item, export_image, record_views)
    if callable(_BK_FIX62_PREV_RENDER_FILE):
        return _BK_FIX62_PREV_RENDER_FILE(self, path, fmt, item)
    return None

try:
    MainWindow._render_file = _bk_fix62_render_file
except Exception:
    pass
