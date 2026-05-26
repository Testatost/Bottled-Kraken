def _clean_table_cell_text(value: Any) -> str:
    txt = _clean_ocr_text(value)
    txt = txt.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt

def _trim_grid_row_edges(row: List[str]) -> Optional[List[str]]:
    cells = [_clean_table_cell_text(cell) for cell in row]
    first = 0
    last = len(cells) - 1
    while first <= last and not cells[first]:
        first += 1
    while last >= first and not cells[last]:
        last -= 1
    if first > last:
        return None
    return cells[first:last + 1]

def _normalize_grid_width(grid: List[List[str]]) -> List[List[str]]:
    rows: List[List[str]] = []
    for row in grid:
        trimmed = _trim_grid_row_edges(row)
        if trimmed:
            rows.append(trimmed)
    if not rows:
        return []
    width = max(len(row) for row in rows)
    if width <= 1:
        return rows
    return [row + [""] * (width - len(row)) for row in rows]

def _compact_grid_row(row: List[str]) -> Optional[List[str]]:
    # Rückwärtskompatibler Alias: Rand-Leerzellen entfernen, innere Leerzellen behalten.
    return _trim_grid_row_edges(row)

def _compact_grid(grid: List[List[str]]) -> List[List[str]]:
    return _normalize_grid_width(grid)

def _split_textual_table_cells(text: str) -> List[str]:
    txt = _clean_table_cell_text(text)
    if not txt:
        return []
    if any(ch in txt for ch in ("|", "│", "┃")) or re.search(r"(?:_{2,}|\s_\s|\t)", txt):
        parts = re.split(r"\s*(?:[\|\u2502\u2503]+|_{2,}|\s_\s|\t+)\s*", txt)
        return [p.strip() for p in parts if p.strip()]
    # Viele historische Tabellen werden im OCR-Text als Zeile mit großen Abständen erkannt.
    # Zwei oder mehr Leerzeichen sind hier ein schwaches, aber nützliches Spaltensignal.
    if re.search(r"\S\s{2,}\S", txt):
        parts = re.split(r"\s{2,}", txt)
        return [p.strip() for p in parts if p.strip()]
    return [txt]

def table_to_rows_two_columns(records: List[RecordView], page_width: int) -> List[List[str]]:
    """Erzwingt zwei visuelle Spalten anhand der Seitenmitte."""
    mid = max(1, int(page_width)) // 2
    rows = group_rows_by_y(records, page_width)
    grid: List[List[str]] = []
    for row in rows:
        left_parts = []
        right_parts = []
        for rv in sorted(row, key=lambda item: item.bbox[0] if item.bbox else 0):
            if not rv.bbox:
                continue
            x0, _y0, x1, _y1 = rv.bbox
            cx = (x0 + x1) / 2.0
            if cx < mid:
                left_parts.append(_clean_table_cell_text(rv.text))
            else:
                right_parts.append(_clean_table_cell_text(rv.text))
        grid.append([" ".join(p for p in left_parts if p).strip(), " ".join(p for p in right_parts if p).strip()])
    return _normalize_grid_width(grid)

def _rows_from_explicit_separators(records: List[RecordView], page_width: int) -> Optional[List[List[str]]]:
    has_separator_text = any(
        rv.text and (
            any(ch in rv.text for ch in ("|", "│", "┃"))
            or re.search(r"(?:_{2,}|\s_\s|\t|\S\s{2,}\S)", str(rv.text))
        )
        for rv in records
    )
    if not has_separator_text:
        return None
    rows = group_rows_by_y(records, page_width)
    grid: List[List[str]] = []
    for row in rows:
        cells: List[str] = []
        row = [rv for rv in row if rv.bbox]
        row.sort(key=lambda rv: rv.bbox[0] if rv.bbox else 0)
        for rv in row:
            txt = _clean_table_cell_text(rv.text)
            if not txt or re.fullmatch(r"[\|\u2502\u2503]+", txt):
                continue
            cells.extend(_split_textual_table_cells(txt))
        if cells:
            grid.append(cells)
    return _normalize_grid_width(grid)

def _adaptive_column_anchors(rows: List[List[RecordView]], page_width: int) -> List[float]:
    candidates: List[Tuple[float, float]] = []
    widths: List[float] = []
    w = max(1.0, float(page_width or 1))
    for row in rows:
        for rv in row:
            if not rv.bbox:
                continue
            x0, _y0, x1, _y1 = rv.bbox
            bw = max(1.0, float(x1 - x0))
            # Sehr breite Textblöcke sind meistens Fließtext, nicht Tabellenzellen.
            if bw >= 0.82 * w and len(row) <= 1:
                continue
            widths.append(bw)
            candidates.append((float(x0), bw))
    if not candidates:
        return []
    med_w = statistics.median(widths) if widths else 40.0
    threshold = max(28.0, min(95.0, med_w * 0.55, w * 0.045))
    xs = sorted(x for x, _bw in candidates)
    clusters: List[List[float]] = []
    for x in xs:
        if not clusters or abs(x - statistics.median(clusters[-1])) > threshold:
            clusters.append([x])
        else:
            clusters[-1].append(x)
    anchors = [statistics.median(c) for c in clusters if c]
    # Nahe Dubletten noch einmal zusammenziehen.
    merged: List[List[float]] = []
    for x in anchors:
        if not merged or abs(x - statistics.median(merged[-1])) > threshold * 0.75:
            merged.append([x])
        else:
            merged[-1].append(x)
    return [statistics.median(c) for c in merged]

def _nearest_anchor_index(x: float, anchors: List[float]) -> int:
    if not anchors:
        return 0
    best_i = 0
    best_d = abs(float(x) - float(anchors[0]))
    for i in range(1, len(anchors)):
        d = abs(float(x) - float(anchors[i]))
        if d < best_d:
            best_i = i
            best_d = d
    return best_i

def _bbox_table_rows(records: List[RecordView], page_width: int) -> List[List[str]]:
    rows = group_rows_by_y(records, page_width)
    if not rows:
        return [[_clean_table_cell_text(rv.text)] for rv in records if _clean_table_cell_text(rv.text)]

    multi_cell_rows = sum(1 for row in rows if len([rv for rv in row if rv.bbox]) >= 2)
    anchors = _adaptive_column_anchors(rows, page_width)

    # Schutz gegen falsche CSV-Tabellen bei normalem Fließtext / Zeitungsspalten:
    # Erst ab mehreren echten Mehrfachzellen-Zeilen wird BBox-Tabellierung aktiviert.
    if len(anchors) <= 1 or multi_cell_rows < 2:
        plain_rows: List[List[str]] = []
        for row in rows:
            parts = [_clean_table_cell_text(rv.text) for rv in sorted(row, key=lambda rv: rv.bbox[0] if rv.bbox else 0)]
            text = " ".join(p for p in parts if p).strip()
            if text:
                plain_rows.append([text])
        return plain_rows

    grid: List[List[str]] = []
    for row in rows:
        line = [""] * len(anchors)
        for rv in sorted(row, key=lambda item: item.bbox[0] if item.bbox else 0):
            if not rv.bbox:
                continue
            x0, _y0, _x1, _y1 = rv.bbox
            c = _nearest_anchor_index(float(x0), anchors)
            txt = _clean_table_cell_text(rv.text)
            if not txt:
                continue
            if line[c]:
                line[c] = (line[c] + " " + txt).strip()
            else:
                line[c] = txt
        grid.append(line)
    return _normalize_grid_width(grid)

def table_to_rows(records: List[RecordView], page_width: int) -> List[List[str]]:
    """
    Baut CSV-/JSON-Tabellenzeilen aus OCR-Zeilen.

    Reihenfolge der Signale:
    1. harte Trenner im OCR-Text: |, │, Unterstrich- oder Mehrfach-Leerzeichen-Spalten
    2. visuelle BBox-Zeilen und adaptive Spaltenanker
    3. Fallback: eine OCR-Zeile = eine Export-Zeile
    """
    records = [rv for rv in records if _clean_table_cell_text(getattr(rv, "text", "")) or getattr(rv, "bbox", None)]
    if not records:
        return []

    explicit = _rows_from_explicit_separators(records, page_width)
    if explicit:
        return explicit

    if any(rv.bbox for rv in records):
        return _bbox_table_rows(records, page_width)

    return [[cell] for rv in records for cell in [ _clean_table_cell_text(rv.text) ] if cell]

def docx_layout_blocks(records: List[RecordView], page_width: int, page_height: int = 0) -> List[Dict[str, Any]]:
    """
    Bereitet OCR-Zeilen für einen DOCX-Export vor.

    Ergebnisblöcke:
    - {"type": "paragraph", "text": ..., "bbox": (...), "top": ...}
    - {"type": "table", "rows": [[...]], "bbox": (...), "anchors": [...], "top": ...}

    Die Erkennung ist bewusst konservativ: Tabellenblöcke entstehen erst, wenn
    mehrere benachbarte Zeilen mehrspaltige Signale besitzen. Einzelne normale
    Textzeilen werden als absatzbasierte Layoutzeilen mit Einzug exportiert.
    """
    records = [rv for rv in records if _clean_table_cell_text(getattr(rv, "text", "")) or getattr(rv, "bbox", None)]
    if not records:
        return []

    rows = group_rows_by_y(records, page_width) if any(getattr(rv, "bbox", None) for rv in records) else []
    if not rows:
        return [
            {"type": "paragraph", "text": _clean_table_cell_text(rv.text), "bbox": getattr(rv, "bbox", None), "top": i * 20}
            for i, rv in enumerate(records)
            if _clean_table_cell_text(rv.text)
        ]

    def row_bbox(row: List[RecordView]) -> Optional[BBox]:
        boxes = [rv.bbox for rv in row if rv.bbox]
        if not boxes:
            return None
        return (
            int(min(bb[0] for bb in boxes)),
            int(min(bb[1] for bb in boxes)),
            int(max(bb[2] for bb in boxes)),
            int(max(bb[3] for bb in boxes)),
        )

    def row_text(row: List[RecordView]) -> str:
        parts = [_clean_table_cell_text(rv.text) for rv in sorted(row, key=lambda rv: rv.bbox[0] if rv.bbox else 0)]
        return " ".join(p for p in parts if p).strip()

    def split_row_textual(row: List[RecordView]) -> List[str]:
        cells: List[str] = []
        for rv in sorted(row, key=lambda rv: rv.bbox[0] if rv.bbox else 0):
            cells.extend(_split_textual_table_cells(rv.text))
        return [c for c in cells if c]

    # Voranalyse: Welche Zeilen sehen wie Tabellenzeilen aus?
    row_infos: List[Dict[str, Any]] = []
    for row in rows:
        boxes = [rv for rv in row if rv.bbox]
        textual_cells = split_row_textual(row)
        non_empty_boxes = [rv for rv in boxes if _clean_table_cell_text(rv.text)]
        bb = row_bbox(row)
        top = bb[1] if bb else 0
        row_infos.append({
            "row": row,
            "bbox": bb,
            "top": top,
            "table_like": (len(non_empty_boxes) >= 2) or (len(textual_cells) >= 2),
            "textual_cells": textual_cells,
        })

    # Aufeinanderfolgende Tabellenzeilen zu Blöcken gruppieren. Einzelne Tabellenzeilen
    # bleiben Absatz, damit normaler Fließtext nicht versehentlich in Tabellen landet.
    blocks: List[Dict[str, Any]] = []
    i = 0
    while i < len(row_infos):
        info = row_infos[i]
        if not info["table_like"]:
            txt = row_text(info["row"])
            if txt:
                blocks.append({"type": "paragraph", "text": txt, "bbox": info["bbox"], "top": info["top"]})
            i += 1
            continue

        j = i
        while j < len(row_infos) and row_infos[j]["table_like"]:
            j += 1
        cluster = row_infos[i:j]
        if len(cluster) < 2:
            txt = row_text(cluster[0]["row"])
            if txt:
                blocks.append({"type": "paragraph", "text": txt, "bbox": cluster[0]["bbox"], "top": cluster[0]["top"]})
            i = j
            continue

        cluster_rows = [entry["row"] for entry in cluster]
        anchors = _adaptive_column_anchors(cluster_rows, page_width)
        grid: List[List[str]] = []

        if len(anchors) >= 2:
            for entry in cluster:
                line = [""] * len(anchors)
                for rv in sorted(entry["row"], key=lambda item: item.bbox[0] if item.bbox else 0):
                    txt = _clean_table_cell_text(rv.text)
                    if not txt:
                        continue
                    if rv.bbox:
                        c = _nearest_anchor_index(float(rv.bbox[0]), anchors)
                    else:
                        c = 0
                    line[c] = (line[c] + " " + txt).strip() if line[c] else txt
                grid.append(line)
        else:
            for entry in cluster:
                cells = entry.get("textual_cells") or [row_text(entry["row"])]
                grid.append(cells)

        grid = _normalize_grid_width(grid)
        if not grid or max((len(row) for row in grid), default=0) <= 1:
            for entry in cluster:
                txt = row_text(entry["row"])
                if txt:
                    blocks.append({"type": "paragraph", "text": txt, "bbox": entry["bbox"], "top": entry["top"]})
            i = j
            continue

        boxes = [entry["bbox"] for entry in cluster if entry["bbox"]]
        bb = None
        if boxes:
            bb = (
                int(min(x[0] for x in boxes)),
                int(min(x[1] for x in boxes)),
                int(max(x[2] for x in boxes)),
                int(max(x[3] for x in boxes)),
            )
        blocks.append({
            "type": "table",
            "rows": grid,
            "bbox": bb,
            "anchors": [float(a) for a in anchors],
            "top": cluster[0]["top"],
        })
        i = j

    return blocks

def _normalize_bbox(bb: Optional[BBox], img_w: int, img_h: int) -> Optional[List[float]]:
    if not bb or img_w <= 0 or img_h <= 0:
        return None
    x0, y0, x1, y1 = bb
    return [
        round(x0 / img_w, 4),
        round(y0 / img_h, 4),
        round(x1 / img_w, 4),
        round(y1 / img_h, 4),
    ]

def _extract_text_lines(text: str) -> List[str]:
    if not text:
        return []
    return [ln.strip() for ln in text.splitlines() if ln.strip()]

def pil_to_qpixmap(img: Image.Image) -> QPixmap:
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")
    return QPixmap.fromImage(ImageQt(img))

def render_pdf_page_to_pil(pdf_path: str, page_index: int, dpi: int = 300) -> Image.Image:
    doc = fitz.open(pdf_path)
    try:
        page = doc.load_page(page_index)
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    finally:
        doc.close()

def polygon_area(poly: List[Tuple[float, float]]) -> float:
    if not poly or len(poly) < 3:
        return 0.0
    area = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        area += (x1 * y2) - (x2 * y1)
    return abs(area) * 0.5

def clip_polygon_halfplane(
        poly: List[Tuple[float, float]],
        a: float,
        b: float,
        c: float
) -> List[Tuple[float, float]]:
    """
    Behält den Teil des Polygons, für den gilt:
        a*x + b*y + c >= 0
    """
    if not poly:
        return []
    def inside(p: Tuple[float, float]) -> bool:
        x, y = p
        return (a * x + b * y + c) >= 0.0
    def intersection(
            p1: Tuple[float, float],
            p2: Tuple[float, float]
    ) -> Tuple[float, float]:
        x1, y1 = p1
        x2, y2 = p2
        dx = x2 - x1
        dy = y2 - y1
        denom = a * dx + b * dy
        if abs(denom) < 1e-12:
            return p2
        t = -(a * x1 + b * y1 + c) / denom
        return (x1 + t * dx, y1 + t * dy)
    output = []
    prev = poly[-1]
    prev_inside = inside(prev)
    for curr in poly:
        curr_inside = inside(curr)
        if curr_inside:
            if not prev_inside:
                output.append(intersection(prev, curr))
            output.append(curr)
        elif prev_inside:
            output.append(intersection(prev, curr))
        prev = curr
        prev_inside = curr_inside
    return output

__all__ = [name for name in globals() if not name.startswith("__")]
