def sort_records_handwriting_simple(records, reading_mode: int = READING_MODES["TB_LR"]):
    raw = []
    for r in records:
        bb = record_bbox(r)
        if bb:
            raw.append(bb)
    if raw:
        image_width = int(max(bb[2] for bb in raw)) + 1
        image_height = int(max(bb[3] for bb in raw)) + 1
    else:
        image_width = image_height = 0
    return _sort_records_visual_order(records, image_width, image_height, reading_mode, deskew=False)

def sort_records_reading_order(records, image_width: int, image_height: int,
                               reading_mode: int = READING_MODES["TB_LR"]):
    return _sort_records_visual_order(records, image_width, image_height, reading_mode, deskew=True)

def clamp_bbox(bb: Tuple[int, int, int, int], w: int, h: int) -> Optional[Tuple[int, int, int, int]]:
    x0, y0, x1, y1 = bb
    return (max(0, min(w - 1, x0)), max(0, min(h - 1, y0)),
            max(0, min(w, x1)), max(0, min(h, y1)))

def _safe_int(v, default=0):
    try:
        return int(v)
    except Exception:
        return default

def _force_text(value):
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)

def _error_log_path() -> str:
    return os.path.join(os.getcwd(), "bottled_kraken_error.log")

def _cleanup_old_error_log(max_age_days: int = 20):
    log_path = _error_log_path()
    try:
        if not os.path.exists(log_path):
            return
        max_age_seconds = int(max_age_days * 24 * 60 * 60)
        file_age = time.time() - os.path.getmtime(log_path)
        if file_age >= max_age_seconds:
            os.remove(log_path)
    except Exception:
        pass

def _append_error_log_entry(msg: str):
    log_path = _error_log_path()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("\n\n" + "=" * 80 + "\n")
            f.write(f"[{timestamp}] Unbehandelte Ausnahme\n")
            f.write("-" * 80 + "\n")
            f.write(msg.rstrip() + "\n")
    except Exception:
        pass

def _install_exception_hook():
    _cleanup_old_error_log(max_age_days=20)
    def handle_exception(exc_type, exc_value, exc_tb):
        msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        _append_error_log_entry(msg)
        try:
            QMessageBox.critical(None, "Fehler", msg)
        except Exception:
            try:
                print(msg)
            except Exception:
                pass
    sys.excepthook = handle_exception

def _clean_ocr_text(text: Any) -> str:
    if text is None:
        return ""
    if isinstance(text, bytes):
        txt = text.decode("utf-8", errors="replace")
    else:
        txt = str(text)
    txt = txt.replace("\u00a0", " ")
    txt = txt.replace("\u200b", "")
    txt = txt.replace("\ufeff", "")
    txt = txt.replace("ſ", "s")
    txt = txt.replace("⸗", "-")
    txt = txt.replace("±", "+/-")
    txt = re.sub(r"[ \t\r\f\v]+", " ", txt)
    return txt.strip()

def _is_effectively_empty_ocr_text(text: Any) -> bool:
    return _clean_ocr_text(text) == ""

def _extract_json_payload(text: str):
    if not text:
        return None
    raw = _force_text(text).strip()
    raw = re.sub(r"^\s*```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```\s*$", "", raw)
    candidates = [raw]
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        chunk = raw[start:end + 1]
        candidates.append(chunk)
        candidates.append(re.sub(r",(\s*[}\]])", r"\1", chunk))
    normalized = raw.replace("’", "'").replace("‘", "'")
    normalized = normalized.replace("„", "\"").replace("“", "\"").replace("”", "\"")
    candidates.append(normalized)
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except Exception:
            pass
    return None

def _extract_json_string_lines_object(text: str):
    data = _extract_json_payload(text)
    if isinstance(data, dict) and isinstance(data.get("lines"), list):
        lines = data["lines"]
        if all(isinstance(x, str) for x in lines):
            return lines
    return None

def _pil_to_data_url(
        im: Image.Image,
        max_side: int = 5000,
        image_format: str = "PNG",
        jpeg_quality: int = 85,
) -> str:
    im = im.convert("RGB")
    w, h = im.size
    scale = min(max_side / max(w, h), 1.0)
    if scale < 1.0:
        im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    buf = BytesIO()
    fmt = (image_format or "PNG").upper()
    if fmt == "JPEG":
        im.save(buf, format="JPEG", quality=int(jpeg_quality), optimize=True)
        mime = "image/jpeg"
    else:
        im.save(buf, format="PNG", optimize=True)
        mime = "image/png"
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:{mime};base64,{b64}"

def _image_to_data_url(path: str) -> str:
    im = _load_image_gray(path)
    return _pil_to_data_url(im)

def _page_to_data_url(
        path: str,
        max_side: int = 5000,
        image_format: str = "PNG",
        jpeg_quality: int = 85,
) -> str:
    im = _load_image_color(path)
    return _pil_to_data_url(
        im,
        max_side=max_side,
        image_format=image_format,
        jpeg_quality=jpeg_quality,
    )

def _page_to_small_png_data_url(
        path: str,
        max_side: int = 1200,
) -> str:
    im = _load_image_color(path)
    w, h = im.size
    longest = max(w, h)
    if longest > max_side:
        scale = max_side / float(longest)
        im = im.resize(
            (max(1, int(w * scale)), max(1, int(h * scale))),
            Image.LANCZOS
        )
    return _pil_to_data_url(
        im,
        max_side=max_side,
        image_format="PNG",
    )

def _crop_block_to_data_url_context(
        path: str,
        recs: List["RecordView"],
        start: int,
        end: int,
        pad_x: int = 40,
        pad_y: int = 35,
) -> str:
    im = _load_image_color(path)
    boxes = [rv.bbox for rv in recs[start:end] if rv.bbox]
    if not boxes:
        return _pil_to_data_url(im, max_side=768)
    x0 = max(0, min(bb[0] for bb in boxes) - pad_x)
    y0 = max(0, min(bb[1] for bb in boxes) - pad_y)
    x1 = min(im.size[0], max(bb[2] for bb in boxes) + pad_x)
    y1 = min(im.size[1], max(bb[3] for bb in boxes) + pad_y)
    crop = im.crop((x0, y0, x1, y1))
    return _pil_to_data_url(crop, max_side=1600)

def _crop_single_line_to_data_url(
        path: str,
        rv: "RecordView",
        pad_x: int = 14,
        pad_y: int = 6,
        extra_context_y: int = 0,
) -> str:
    im = _load_image_color(path)
    if not rv.bbox:
        return _pil_to_data_url(im, max_side=1600)
    x0, y0, x1, y1 = rv.bbox
    x0 = max(0, x0 - pad_x)
    y0 = max(0, y0 - pad_y - extra_context_y)
    x1 = min(im.size[0], x1 + pad_x)
    y1 = min(im.size[1], y1 + pad_y + extra_context_y)
    crop = im.crop((x0, y0, x1, y1))
    return _pil_to_data_url(crop, max_side=1600)

AI_SCRIPT_PRINT = "print"

AI_SCRIPT_HANDWRITING = "handwriting"

AI_SCRIPT_MIXED = "mixed"

def _normalize_ai_script_mode(script_mode: Optional[str]) -> str:
    mode = str(script_mode or AI_SCRIPT_PRINT).strip().lower()
    if mode in {AI_SCRIPT_PRINT, AI_SCRIPT_HANDWRITING, AI_SCRIPT_MIXED}:
        return mode
    return AI_SCRIPT_PRINT

def _ai_script_crop_profile(script_mode: Optional[str]) -> Dict[str, int]:
    mode = _normalize_ai_script_mode(script_mode)
    if mode == AI_SCRIPT_HANDWRITING:
        return {
            "single_pad_x": 16,
            "single_pad_y": 8,
            "single_extra_context_y": 18,
            "block_pad_x": 80,
            "block_pad_y": 70,
        }
    if mode == AI_SCRIPT_MIXED:
        return {
            "single_pad_x": 9,
            "single_pad_y": 5,
            "single_extra_context_y": 9,
            "block_pad_x": 56,
            "block_pad_y": 48,
        }
    return {
        "single_pad_x": 3,
        "single_pad_y": 3,
        "single_extra_context_y": 1,
        "block_pad_x": 40,
        "block_pad_y": 35,
    }

def _ai_script_prompt_hint(script_mode: Optional[str]) -> str:
    mode = _normalize_ai_script_mode(script_mode)
    if mode == AI_SCRIPT_HANDWRITING:
        return (
            "Schriftart-Hinweis: überwiegend Handschrift. Achte stärker auf leicht außerhalb der "
            "Overlay-Box liegende Ober- und Unterlängen sowie auf verbundene Schriftzüge."
        )
    if mode == AI_SCRIPT_MIXED:
        return (
            "Schriftart-Hinweis: gemischte Schrift. Berücksichtige etwas Kontext außerhalb der "
            "Overlay-Box, aber bleibe eng an der lokalen Zielzeile."
        )
    return (
        "Schriftart-Hinweis: überwiegend Druckschrift. Bleibe eng an der lokalen Zielzeile und "
        "bevorzuge die aktuelle Box-Abgrenzung."
    )

def cluster_columns(records: List[RecordView], x_threshold: int = 45):
    cols = []
    for r in records:
        if not r.bbox:
            continue
        x0 = r.bbox[0]
        placed = False
        for c in cols:
            if abs(c["x"] - x0) <= x_threshold:
                c["items"].append(r)
                c["x"] = int((c["x"] * 0.8) + (x0 * 0.2))
                placed = True
                break
        if not placed:
            cols.append({"x": x0, "items": [r]})
    cols.sort(key=lambda c: c["x"])
    return [c["items"] for c in cols]

def is_same_visual_row(a: RecordView, b: RecordView, page_width: int) -> bool:
    if not a.bbox or not b.bbox:
        return False
    ax0, ay0, ax1, ay1 = a.bbox
    bx0, by0, bx1, by1 = b.bbox
    # y-Ähnlichkeit
    if abs(ay0 - by0) > 12:
        return False
    w = max(1, int(page_width))
    mid = w // 2
    aw = ax1 - ax0
    bw = bx1 - bx0
    # Wenn beide Boxen "Textzeilen-breit" sind und in unterschiedlichen Spalten liegen,
    # dann sind das KEINE Tabellenzellen derselben Zeile.
    textish_a = aw >= int(0.30 * w)
    textish_b = bw >= int(0.30 * w)
    a_left = (ax0 < mid and ax1 <= mid + int(0.05 * w))
    b_right = (bx1 > mid and bx0 >= mid - int(0.05 * w))
    b_left = (bx0 < mid and bx1 <= mid + int(0.05 * w))
    a_right = (ax1 > mid and ax0 >= mid - int(0.05 * w))
    if textish_a and textish_b and ((a_left and b_right) or (b_left and a_right)):
        return False
    return True

def group_rows_by_y(records: List[RecordView], page_width: int):
    recs = [r for r in records if r.bbox]
    if not recs:
        return []
    w = max(1, int(page_width))
    # robuste Zeilenhöhe
    hs = sorted([(rv.bbox[3] - rv.bbox[1]) for rv in recs if (rv.bbox[3] - rv.bbox[1]) > 0])
    med_h = hs[len(hs) // 2] if hs else 14
    # enger = "Abstand geringer" (striktere Gruppierung)
    y_tol = max(10, int(0.45 * med_h))
    # Neu: horizontale Separatoren (_ / - / ─) erkennen
    sep_y: List[float] = []
    filtered_recs: List[RecordView] = []
    for rv in recs:
        txt = (rv.text or "").strip()
        x0, y0, x1, y1 = rv.bbox
        bw = (x1 - x0)
        bh = (y1 - y0)
        is_hsep = bool(HSEP_RE.match(txt)) and (bw >= 0.55 * w) and (bh <= 0.7 * med_h)
        if is_hsep:
            sep_y.append((y0 + y1) / 2.0)
        else:
            filtered_recs.append(rv)
    sep_y.sort()
    recs = filtered_recs
    def center_y(rv):
        x0, y0, x1, y1 = rv.bbox
        return (y0 + y1) / 2.0
    sorted_recs = sorted(recs, key=lambda rv: (center_y(rv), rv.bbox[0]))
    rows: List[List[RecordView]] = []
    row_y: List[float] = []
    row_band: List[int] = []
    def band_index(cy: float) -> int:
        # wie viele Separatoren liegen oberhalb? -> Band 0..n
        idx = 0
        for y in sep_y:
            if cy > y:
                idx += 1
            else:
                break
        return idx
    for r in sorted_recs:
        cy = center_y(r)
        b = band_index(cy)
        placed = False
        for i in range(len(rows)):
            if row_band[i] != b:
                continue
            if abs(cy - row_y[i]) <= y_tol:
                rows[i].append(r)
                row_y[i] = row_y[i] * 0.85 + cy * 0.15
                placed = True
                break
        if not placed:
            rows.append([r])
            row_y.append(cy)
            row_band.append(b)
    for row in rows:
        row.sort(key=lambda rv: rv.bbox[0])
    return rows
