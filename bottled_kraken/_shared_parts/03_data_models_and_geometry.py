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
    results: Optional[Tuple[str, list, Image.Image, List[RecordView]]] = None
    edited: bool = False
    undo_stack: List[UndoSnapshot] = field(default_factory=list)
    redo_stack: List[UndoSnapshot] = field(default_factory=list)
    source_kind: str = "image"  # "image" oder "pdf_page"
    relative_path: str = ""
    preset_bboxes: List[Optional[BBox]] = field(default_factory=list)
    lm_locked_bboxes: List[Optional[BBox]] = field(default_factory=list)

@dataclass
class OCRJob:
    input_paths: List[str]
    recognition_model_path: str
    segmentation_model_path: Optional[str]
    device: str
    reading_direction: int
    export_format: str
    export_dir: Optional[str]
    preset_bboxes_by_path: Dict[str, List[Optional[BBox]]] = field(default_factory=dict)

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

VSEP_RE = re.compile(r'^[|│┃¦︱︳]+$')  # | │ ┃ ¦ ︱ ︳

HSEP_RE = re.compile(r'^[_\-\u2500\u2501\u2504\u2505]{3,}$')  # _ - ─ ━ etc. (mind. 3)

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
    rev_y = reading_mode in (READING_MODES["BT_LR"], READING_MODES["BT_RL"])
    rev_x = reading_mode in (READING_MODES["TB_RL"], READING_MODES["BT_RL"])
    raw = []
    for r in records:
        bb = record_bbox(r)
        if bb:
            raw.append((r, bb))
    if not raw:
        return list(records)

    skew = _estimate_safe_skew_angle(raw) if deskew else 0.0
    page_w = max(1.0, float(image_width or max(bb[2] for _, bb in raw)))
    page_h = max(1.0, float(image_height or max(bb[3] for _, bb in raw)))
    wc = page_w / 2.0
    hc = page_h / 2.0
    cs = math.cos(-skew)
    sn = math.sin(-skew)

    def _rotate_point(x: float, y: float):
        x -= wc
        y -= hc
        xr = x * cs - y * sn
        yr = x * sn + y * cs
        return xr + wc, yr + hc

    def _norm_bb(bb):
        if abs(skew) < 1e-6:
            return tuple(float(v) for v in bb)
        x0, y0, x1, y1 = bb
        pts = [_rotate_point(x0, y0), _rotate_point(x1, y0), _rotate_point(x1, y1), _rotate_point(x0, y1)]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (min(xs), min(ys), max(xs), max(ys))

    items = []
    heights = []
    for r, bb in raw:
        dbb = _norm_bb(bb)
        top = float(dbb[1])
        bottom = float(dbb[3])
        left = float(dbb[0])
        right = float(dbb[2])
        cy = (top + bottom) / 2.0
        cx = (left + right) / 2.0
        h = max(1.0, bottom - top)
        heights.append(h)
        items.append({
            "record": r,
            "bbox": bb,
            "dbb": dbb,
            "top": top,
            "bottom": bottom,
            "left": left,
            "right": right,
            "cx": cx,
            "cy": cy,
            "h": h,
        })

    med_h = statistics.median(heights) if heights else 20.0
    top_tol = max(5.0, med_h * 0.50)
    cy_tol = max(6.0, med_h * 0.60)
    row_gap = max(4.0, med_h * 0.35)

    items.sort(key=lambda item: (item["top"], item["left"], item["cy"], item["cx"]))
    rows = []
    for item in items:
        chosen = None
        chosen_score = None
        for row in reversed(rows):
            if item["top"] > row["bottom"] + row_gap:
                break
            overlap = min(item["bottom"], row["bottom"]) - max(item["top"], row["top"])
            min_h = max(1.0, min(item["h"], row["med_h"]))
            overlap_ratio = overlap / min_h
            same_row = (
                overlap_ratio >= 0.18
                or abs(item["cy"] - row["cy"]) <= cy_tol
                or abs(item["top"] - row["top_anchor"]) <= top_tol
            )
            if not same_row:
                continue
            score = (
                abs(item["cy"] - row["cy"]) * 1.0
                + abs(item["top"] - row["top_anchor"]) * 0.8
                + abs(item["left"] - row["left_anchor"]) * 0.02
            )
            if chosen is None or score < chosen_score:
                chosen = row
                chosen_score = score
        if chosen is None:
            rows.append({
                "top_anchor": item["top"],
                "left_anchor": item["left"],
                "top": item["top"],
                "bottom": item["bottom"],
                "cy": item["cy"],
                "med_h": item["h"],
                "items": [item],
            })
        else:
            chosen["items"].append(item)
            n = len(chosen["items"])
            chosen["top_anchor"] = ((chosen["top_anchor"] * (n - 1)) + item["top"]) / n
            chosen["left_anchor"] = min(chosen["left_anchor"], item["left"])
            chosen["top"] = min(chosen["top"], item["top"])
            chosen["bottom"] = max(chosen["bottom"], item["bottom"])
            chosen["cy"] = ((chosen["cy"] * (n - 1)) + item["cy"]) / n
            chosen["med_h"] = ((chosen["med_h"] * (n - 1)) + item["h"]) / n

    rows.sort(key=lambda row: (row["top_anchor"], row["top"]), reverse=rev_y)
    ordered = []
    for row in rows:
        row["items"].sort(key=lambda item: (item["left"], item["cx"], item["top"], item["cy"]), reverse=rev_x)
        ordered.extend(item["record"] for item in row["items"])

    ordered_ids = {id(r) for r in ordered}
    for r in records:
        if id(r) not in ordered_ids:
            ordered.append(r)
    return ordered
