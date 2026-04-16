def _compact_grid_row(row: List[str]) -> Optional[List[str]]:
    compact = [(cell or '').strip() for cell in row if (cell or '').strip()]
    return compact or None


def _compact_grid(grid: List[List[str]]) -> List[List[str]]:
    compact_rows: List[List[str]] = []
    for row in grid:
        compact_row = _compact_grid_row(row)
        if compact_row:
            compact_rows.append(compact_row)
    return compact_rows


def table_to_rows_two_columns(records: List[RecordView], page_width: int) -> List[List[str]]:
    #   Erzwingt exakt 2 Spalten anhand Seitenmitte.
    #   Verhindert "3. Spalte" durch Einrückungen/Ausreißer.
    mid = max(1, int(page_width)) // 2
    rows = group_rows_by_y(records, page_width)
    grid: List[List[str]] = []
    for row in rows:
        left_parts = []
        right_parts = []
        for rv in row:
            if not rv.bbox:
                continue
            x0 = rv.bbox[0]
            if x0 < mid:
                left_parts.append(rv.text)
            else:
                right_parts.append(rv.text)
        grid.append([" ".join(left_parts).strip(), " ".join(right_parts).strip()])
    # Optional: kurze Restfragmente an vorige Zeile hängen
    merged: List[List[str]] = []
    for r in grid:
        if merged:
            if (not r[0]) and r[1] and len(r[1]) <= 20 and (not merged[-1][1].endswith(".")):
                merged[-1][1] = (merged[-1][1] + " " + r[1]).strip()
                continue
        merged.append(r)
    return _compact_grid(merged)

def table_to_rows(records: List[RecordView], page_width: int) -> List[List[str]]:
    # Wenn der Text explizite Trenner enthält, nutze die als "harte" Spalten,
    # statt aus BBox-Positionen eine Tabelle zu raten.
    has_pipes = any(
        (rv.text and (
                any(ch in rv.text for ch in ("|", "│", "┃")) or
                re.search(r"(?:_{2,}|\s_\s)", rv.text)  # "__" oder " _ " als Trenner
        ))
        for rv in records
    )
    if has_pipes:
        rows = group_rows_by_y(records, page_width)
        grid = []
        for row in rows:
            # links->rechts sortieren
            row = [rv for rv in row if rv.bbox]
            row.sort(key=lambda rv: rv.bbox[0] if rv.bbox else 0)
            cells: List[str] = []
            for rv in row:
                txt = (rv.text or "").strip()
                if not txt:
                    continue
                # reine Separator-Records ignorieren
                if re.fullmatch(r"[\|\u2502\u2503]+", txt):
                    continue
                # split an pipes
                if any(ch in txt for ch in ("|", "│", "┃")):
                    parts = re.split(r"\s*(?:[\|\u2502\u2503]+|_{2,}|\s_\s)\s*", txt)
                    parts = [p.strip() for p in parts if p.strip()]
                    if parts:
                        cells.extend(parts)
                else:
                    cells.append(txt)
            grid.append(cells if cells else [""])
        return _compact_grid(grid)
    # sonst: dein bestehender bbox-basierter Tabellenmodus
    rows = group_rows_by_y(records, page_width)
    cols = cluster_columns(records)
    # Wenn cluster_columns "3 Spalten" liefert, aber wir eigentlich 2-Spalten-Layout haben,
    # erzwinge 2 Spalten wie im alten Code:
    if len(cols) >= 3:
        # Heuristik: wenn zwei größte Cluster dominieren -> 2 Spalten erzwingen
        sizes = sorted([len(c) for c in cols], reverse=True)
        if sizes and (sizes[0] + (sizes[1] if len(sizes) > 1 else 0)) >= 0.80 * sum(sizes):
            return table_to_rows_two_columns(records, page_width)
    col_x = []
    for col in cols:
        xs = [rv.bbox[0] for rv in col if rv.bbox]
        col_x.append(int(sum(xs) / max(1, len(xs))) if xs else 0)
    def nearest_col(x: int) -> int:
        if not col_x:
            return 0
        best_i = 0
        best_d = abs(col_x[0] - x)
        for i in range(1, len(col_x)):
            d = abs(col_x[i] - x)
            if d < best_d:
                best_d = d
                best_i = i
        return best_i
    grid = []
    for row in rows:
        line = [""] * max(1, len(col_x))
        for rv in row:
            if not rv.bbox:
                continue
            c = nearest_col(rv.bbox[0])
            if line[c]:
                line[c] += " " + rv.text
            else:
                line[c] = rv.text
        grid.append(line)
    return _compact_grid(grid)

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
