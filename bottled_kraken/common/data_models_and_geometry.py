from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('shared', globals())
def _help_pre(text: str) -> str:
    return f"<pre>{html.escape(text)}</pre>"
BBox = Tuple[int, int, int, int]
Point = Tuple[float, float]
@dataclass
class RecordView:
    idx: int
    text: str
    bbox: Optional[BBox]
UndoSnapshot = Tuple[List[Tuple[str, Optional[BBox]]], int]
@dataclass
class TaskItem:
    path: str
    display_name: str
    status: int = STATUS_WAITING
    results: Optional[Tuple[str, list, Optional[Image.Image], List[RecordView]]] = None
    edited: bool = False
    undo_stack: List[UndoSnapshot] = field(default_factory=list)
    redo_stack: List[UndoSnapshot] = field(default_factory=list)
    source_kind: str = "image"
    relative_path: str = ""
    preset_bboxes: List[Optional[BBox]] = field(default_factory=list)
    lm_locked_bboxes: List[Optional[BBox]] = field(default_factory=list)
@dataclass
class OCRJob:
    input_paths: List[str]
    recognition_model_path: str
    segmentation_model_path: Optional[str]
    reading_direction: int
    export_format: str
    export_dir: Optional[str]
    preset_bboxes_by_path: Dict[str, List[Optional[BBox]]] = field(default_factory=dict)
    auto_revision_enabled: bool = False
    auto_revision_replacements: str = ""
    ui_language: str = "de"
def _coerce_points(obj: Any) -> List[Point]:
    if obj is None:
        return []
    if isinstance(obj, (list, tuple)):
        if not obj:
            return []
        first = obj[0]
        if isinstance(first, (list, tuple)) and len(first) == 2 and isinstance(first[0], (int, float)):
            try:
                return [(float(x), float(y)) for x, y in obj]
            except Exception:
                return []
        if isinstance(first, (list, tuple)) and first and isinstance(first[0], (list, tuple)) and len(first[0]) == 2:
            pts: List[Point] = []
            for contour in obj:
                pts.extend(_coerce_points(contour))
            return pts
    return []
def _bbox_from_points(points: List[Point], pad: int = 0) -> Optional[Tuple[int, int, int, int]]:
    if not points:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x0 = int(min(xs)) - pad
    y0 = int(min(ys)) - pad
    x1 = int(max(xs)) + pad
    y1 = int(max(ys)) + pad
    if x1 <= x0 or y1 <= y0:
        return None
    return x0, y0, x1, y1
def record_bbox(r: Any) -> Optional[Tuple[int, int, int, int]]:
    bbox = getattr(r, "bbox", None)
    if bbox:
        try:
            x0, y0, x1, y1 = bbox
            x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
            if x1 > x0 and y1 > y0:
                return x0, y0, x1, y1
        except Exception:
            pass
    for attr in ("boundary", "polygon"):
        boundary = getattr(r, attr, None)
        if boundary:
            pts = _coerce_points(boundary)
            bb = _bbox_from_points(pts, pad=2)
            if bb:
                return bb
    baseline = getattr(r, "baseline", None)
    if baseline:
        pts = _coerce_points(baseline)
        bb = _bbox_from_points(pts, pad=2)
        if bb:
            x0, y0, x1, y1 = bb
            vpad = 14
            return x0, y0 - vpad, x1, y1 + vpad
    return None
def baseline_length(bl) -> float:
    pts = _coerce_points(bl)
    if len(pts) < 2:
        return 0.0
    x1, y1 = pts[0]
    x2, y2 = pts[-1]
    return math.hypot(x2 - x1, y2 - y1)
VSEP_RE = re.compile(r'^[|│┃¦︱︳]+$')
HSEP_RE = re.compile(r'^[_\-\u2500\u2501\u2504\u2505]{3,}$')
ONLY_SYMBOL_LINE_RE = re.compile(
    r'^[\(\)\{\}\?\!\/\\\""„“\$\%\&\[\]\=,\.\-—_:;><\|\+\*#\'~`´\^°]+$'
)
NOISE_LINE_RE = re.compile(
    r'^(?:'
    r'a{3,}|e{3,}|i{3,}|o{3,}|u{3,}|'
    r'ä{3,}|ö{3,}|ü{3,}|'
    r'\.{3,}'
    r')$',
    re.IGNORECASE
)
NOISE_REPEAT_RE = re.compile(
    r'^([aäeéiioöuü])(?:[\s\.\,\-_:;]*\1){2,}$',
    re.IGNORECASE
)
DOTS_ONLY_RE = re.compile(r'^(?:\.\s*){3,}$')
def _is_symbol_only_line(text: Any) -> bool:
    txt = _clean_ocr_text(text)
    if not txt:
        return False
    return bool(ONLY_SYMBOL_LINE_RE.fullmatch(txt))
def _is_noise_line(text: Any) -> bool:
    txt = _clean_ocr_text(text)
    if not txt:
        return False
    if NOISE_REPEAT_RE.fullmatch(txt):
        return True
    if DOTS_ONLY_RE.fullmatch(txt):
        return True
    return False
def _estimate_safe_skew_angle(records_with_boxes) -> float:
    angles = []
    for r, _ in records_with_boxes:
        bl = getattr(r, "baseline", None)
        pts = _coerce_points(bl)
        if len(pts) < 2:
            continue
        x1, y1 = pts[0]
        x2, y2 = pts[-1]
        dx = x2 - x1
        dy = y2 - y1
        if abs(dx) <= 1.0:
            continue
        angle = math.atan2(dy, dx)
        if abs(angle) <= math.radians(15):
            angles.append(angle)
    if len(angles) < 5:
        return 0.0
    med = statistics.median(angles)
    mad = statistics.median([abs(a - med) for a in angles]) if angles else 0.0
    if mad > math.radians(3.0):
        return 0.0
    if abs(med) < math.radians(0.20):
        return 0.0
    if abs(med) > math.radians(12.0):
        return 0.0
    return med
def _sort_records_visual_order(records, image_width: int = 0, image_height: int = 0,
                               reading_mode: int = READING_MODES["TB_LR"], *, deskew: bool = True):
    """Sortiert Kraken-Ergebnisse stabil nach ihrer visuellen Lesereihenfolge.

    Kraken liefert die Segmente meistens bereits in sinnvoller Reihenfolge, kann
    bei hohen/überlappenden Boxen, leicht schiefen Seiten oder geteilten
    Textzeilen aber Ausreißer erzeugen. Entscheidend ist deshalb nicht allein
    die Boxmitte, sondern vorzugsweise die tatsächliche Baseline der Textzeile.

    Zwei Segmente werden nur dann als dieselbe visuelle Zeile behandelt, wenn
    ihre Y-Anker eng zusammenliegen UND sie horizontal weitgehend getrennt
    sind. Dadurch können linke/rechte Fragmente korrekt nebeneinander stehen,
    während sich überlappende Vollzeilen niemals allein wegen hoher Boxen zu
    einer falschen Zeile verbinden.
    """
    rev_y = reading_mode in (READING_MODES["BT_LR"], READING_MODES["BT_RL"])
    rev_x = reading_mode in (READING_MODES["TB_RL"], READING_MODES["BT_RL"])

    raw = []
    for original_index, record in enumerate(records):
        bb = record_bbox(record)
        if bb:
            raw.append((original_index, record, bb))
    if not raw:
        return list(records)

    skew_source = [(record, bb) for _, record, bb in raw]
    skew = _estimate_safe_skew_angle(skew_source) if deskew else 0.0
    page_w = max(1.0, float(image_width or max(bb[2] for _, _, bb in raw)))
    page_h = max(1.0, float(image_height or max(bb[3] for _, _, bb in raw)))
    wc = page_w / 2.0
    hc = page_h / 2.0
    cs = math.cos(-skew)
    sn = math.sin(-skew)

    def _rotate_point(x: float, y: float):
        if abs(skew) < 1e-8:
            return float(x), float(y)
        x = float(x) - wc
        y = float(y) - hc
        return (x * cs - y * sn) + wc, (x * sn + y * cs) + hc

    def _deskew_bbox(bb):
        x0, y0, x1, y1 = [float(v) for v in bb]
        pts = (
            _rotate_point(x0, y0),
            _rotate_point(x1, y0),
            _rotate_point(x1, y1),
            _rotate_point(x0, y1),
        )
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return min(xs), min(ys), max(xs), max(ys)

    items = []
    heights = []
    for original_index, record, bb in raw:
        dbb = _deskew_bbox(bb)
        left, top, right, bottom = dbb
        width = max(1.0, right - left)
        height = max(1.0, bottom - top)
        cx = (left + right) / 2.0
        cy = (top + bottom) / 2.0

        baseline_pts = _coerce_points(getattr(record, "baseline", None))
        rotated_baseline = [_rotate_point(x, y) for x, y in baseline_pts]
        baseline_ok = len(rotated_baseline) >= 2
        if baseline_ok:
            baseline_xs = [p[0] for p in rotated_baseline]
            baseline_ys = [p[1] for p in rotated_baseline]
            baseline_span = max(baseline_xs) - min(baseline_xs)
            baseline_y = statistics.median(baseline_ys)
            # Defekte oder fremde Baselines nicht als Sortieranker verwenden.
            if baseline_span < 2.0 or baseline_y < top - height or baseline_y > bottom + height:
                baseline_ok = False
        if not baseline_ok:
            # Bei Textzeilen liegt die Baseline typischerweise im unteren
            # Bereich der Box. Dieser Anker ist stabiler als die Boxmitte,
            # wenn eine Box nach oben oder unten ungewöhnlich weit ausgreift.
            baseline_y = bottom - (0.18 * height)

        heights.append(height)
        items.append({
            "record": record,
            "original_index": original_index,
            "left": left,
            "top": top,
            "right": right,
            "bottom": bottom,
            "width": width,
            "height": height,
            "cx": cx,
            "cy": cy,
            "anchor_y": float(baseline_y),
            "baseline_ok": bool(baseline_ok),
        })

    med_h = statistics.median(heights) if heights else 20.0
    # Eng genug, um benachbarte Textzeilen nicht zusammenzuwerfen, aber
    # tolerant gegenüber kleinen Baseline-/Segmentierungsabweichungen.
    same_row_anchor_tol = max(3.0, med_h * 0.32)
    same_row_fallback_tol = max(4.0, med_h * 0.42)

    def _horizontal_overlap_ratio(a, b) -> float:
        overlap = min(a["right"], b["right"]) - max(a["left"], b["left"])
        if overlap <= 0.0:
            return 0.0
        return overlap / max(1.0, min(a["width"], b["width"]))

    def _vertical_overlap_ratio(a, b) -> float:
        overlap = min(a["bottom"], b["bottom"]) - max(a["top"], b["top"])
        if overlap <= 0.0:
            return 0.0
        return overlap / max(1.0, min(a["height"], b["height"]))

    # Erst nach dem robusten Y-Anker sortieren. Der ursprüngliche Kraken-Index
    # ist der letzte Tie-Breaker, damit die Sortierung deterministisch bleibt.
    items.sort(key=lambda item: (
        item["anchor_y"],
        item["top"],
        item["left"],
        item["original_index"],
    ), reverse=rev_y)

    rows = []
    for item in items:
        best_row = None
        best_score = None
        for row in rows:
            anchor_delta = abs(item["anchor_y"] - row["anchor_y"])
            if anchor_delta > same_row_fallback_tol:
                continue

            # Eine gemeinsame visuelle Zeile darf aus mehreren horizontalen
            # Fragmenten bestehen. Stark überlappende Vollzeilen sind dagegen
            # immer getrennte Zeilen, selbst wenn ihre Boxen vertikal
            # überlappen oder ihre Mittelpunkte nahe beieinanderliegen.
            max_horizontal_overlap = max(
                (_horizontal_overlap_ratio(item, other) for other in row["items"]),
                default=0.0,
            )
            if max_horizontal_overlap > 0.22:
                continue

            vertical_overlap = max(
                (_vertical_overlap_ratio(item, other) for other in row["items"]),
                default=0.0,
            )
            both_have_baselines = item["baseline_ok"] and row["all_baselines"]
            same_anchor = anchor_delta <= same_row_anchor_tol
            same_visual_band = vertical_overlap >= 0.35 and anchor_delta <= same_row_fallback_tol
            if not (same_anchor or (not both_have_baselines and same_visual_band)):
                continue

            score = anchor_delta + (max_horizontal_overlap * med_h * 2.0)
            if best_row is None or score < best_score:
                best_row = row
                best_score = score

        if best_row is None:
            rows.append({
                "items": [item],
                "anchor_y": item["anchor_y"],
                "top": item["top"],
                "left": item["left"],
                "all_baselines": item["baseline_ok"],
            })
        else:
            best_row["items"].append(item)
            best_row["anchor_y"] = statistics.median(
                [entry["anchor_y"] for entry in best_row["items"]]
            )
            best_row["top"] = min(entry["top"] for entry in best_row["items"])
            best_row["left"] = min(entry["left"] for entry in best_row["items"])
            best_row["all_baselines"] = all(
                entry["baseline_ok"] for entry in best_row["items"]
            )

    rows.sort(key=lambda row: (
        row["anchor_y"],
        row["top"],
        row["left"],
        min(entry["original_index"] for entry in row["items"]),
    ), reverse=rev_y)

    ordered = []
    for row in rows:
        row["items"].sort(key=lambda item: (
            item["left"],
            item["cx"],
            item["anchor_y"],
            item["original_index"],
        ), reverse=rev_x)
        ordered.extend(item["record"] for item in row["items"])

    ordered_ids = {id(record) for record in ordered}
    for record in records:
        if id(record) not in ordered_ids:
            ordered.append(record)
    return ordered

__all__ = [
    'BBox',
    'DOTS_ONLY_RE',
    'HSEP_RE',
    'NOISE_LINE_RE',
    'NOISE_REPEAT_RE',
    'OCRJob',
    'ONLY_SYMBOL_LINE_RE',
    'Point',
    'RecordView',
    'TaskItem',
    'UndoSnapshot',
    'VSEP_RE',
    '_bbox_from_points',
    '_coerce_points',
    '_estimate_safe_skew_angle',
    '_help_pre',
    '_is_noise_line',
    '_is_symbol_only_line',
    '_sort_records_visual_order',
    'baseline_length',
    'record_bbox',
]
register_globals('shared', globals(), __all__)
