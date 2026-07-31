from bottled_kraken.module_registry import register_globals, seed_globals
from bottled_kraken.user_storage import bottled_kraken_user_path
from bottled_kraken.runtime_logging import get_logger, install_exception_hooks
seed_globals('shared', globals())
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
def expand_segmentation_bbox(
        bb: Optional[Tuple[int, int, int, int]],
        image_width: int,
        image_height: int,
        *,
        pad_x: Optional[int] = None,
        pad_y: Optional[int] = None
) -> Optional[Tuple[int, int, int, int]]:
    if not bb:
        return None
    try:
        x0, y0, x1, y1 = [int(round(float(v))) for v in bb]
    except Exception:
        return None
    if x1 <= x0 or y1 <= y0:
        return None
    bh = max(1, y1 - y0)
    if pad_x is None:
        pad_x = max(2, int(round(bh * 0.10)))
    if pad_y is None:
        pad_y = max(1, int(round(bh * 0.08)))
    return clamp_bbox((x0 - pad_x, y0 - pad_y, x1 + pad_x, y1 + pad_y),
                      int(image_width), int(image_height))
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
def _append_error_log_entry(msg: str):
    # Compatibility entry point for older callers. New exceptions are written
    # through the rotating application logger.
    get_logger("exceptions").error("Legacy exception report:\n%s", str(msg).rstrip())

def _exception_dialog_context():
    parent = None
    lang = translation.DEFAULT_LANGUAGE
    try:
        settings_file = str(bottled_kraken_user_path("settings") / "settings.ini")
        settings = QSettings(settings_file, QSettings.IniFormat)
        configured = str(settings.value("ui/language", "") or "").strip()
        lang = configured or QLocale.system().name()
        app = QApplication.instance()
        if app is not None:
            parent = app.activeWindow()
        if parent is not None:
            lang = getattr(parent, "current_lang", lang)
    except Exception:
        get_logger("exceptions").debug("Could not resolve exception-dialog language", exc_info=True)
    return parent, translation.normalize_language_code(lang)

def _show_unhandled_exception_dialog(exc_type, exc_value, error_id: str, log_path: str):
    parent, lang = _exception_dialog_context()
    detail = f"{getattr(exc_type, '__name__', 'Exception')}: {exc_value}".strip()
    if len(detail) > 600:
        detail = detail[:597] + "…"
    message = "\n\n".join((
        translation.translate(lang, "error_unexpected_summary"),
        translation.translate(lang, "error_detail", detail),
        translation.translate(lang, "error_reference", error_id),
        translation.translate(lang, "error_log_saved_to", log_path),
    ))
    QMessageBox.critical(parent, translation.translate(lang, "error_title"), message)

def _install_exception_hook():
    install_exception_hooks(_show_unhandled_exception_dialog)
OCR_AUTO_REVISION_DEFAULT_REPLACEMENTS = [("ſ", "s"), ("⸗", "-"), ("±", "+/-")]
def _serialize_ocr_auto_revision_replacements(replacements=None) -> str:
    pairs = replacements or OCR_AUTO_REVISION_DEFAULT_REPLACEMENTS
    return "\n".join(f"{src}={dst}" for src, dst in pairs)

def _bk_autocorrect_parse_weight(value, default: float = 1.0) -> float:
    try:
        if isinstance(value, (int, float)):
            val = float(value)
        else:
            txt = str(value or "").strip().replace("\u00a0", "").replace(" ", "")
            txt = txt.replace(".", "") if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", txt) else txt
            txt = txt.replace(",", ".")
            if not re.fullmatch(r"\d+(?:\.\d+)?", txt):
                return float(default)
            val = float(txt)
        if val <= 0:
            return float(default)
        return min(val, 1000000.0)
    except Exception:
        return float(default)


def _bk_autocorrect_payload_entry(item):
    if isinstance(item, dict):
        term = item.get("term") or item.get("text") or item.get("name") or item.get("value") or item.get("word")
        weight = item.get("weight", item.get("count", item.get("frequency", item.get("anzahl", 1))))
        return str(term or "").strip(), _bk_autocorrect_parse_weight(weight, 1.0)
    if isinstance(item, (list, tuple)) and item:
        term = str(item[0] or "").strip()
        weight = item[1] if len(item) > 1 else 1
        return term, _bk_autocorrect_parse_weight(weight, 1.0)
    return str(item or "").strip(), 1.0


def _bk_autocorrect_terms_from_replacements(value: Any):
    raw_terms = []
    if value is None:
        return raw_terms
    for raw in str(value).splitlines():
        line = raw.strip()
        if line.startswith("#BK_AUTOCORRECT_TERMS_JSON="):
            try:
                data = json.loads(line.split("=", 1)[1])
                if isinstance(data, list):
                    raw_terms.extend(data)
            except Exception:
                pass
    by_norm = {}
    for item in raw_terms:
        term, weight = _bk_autocorrect_payload_entry(item)
        if not term:
            continue
        norm = _bk_autocorrect_norm(term)
        if len(norm) < 2:
            continue
        entry = by_norm.get(norm)
        if entry is None:
            by_norm[norm] = {"term": term, "weight": weight, "best_weight": weight}
        else:
            entry["weight"] = float(entry.get("weight", 1.0)) + weight
            if weight > float(entry.get("best_weight", 0.0)):
                entry["term"] = term
                entry["best_weight"] = weight
    return [{"term": entry["term"], "weight": float(entry.get("weight", 1.0))} for entry in by_norm.values()]


def _bk_autocorrect_norm(value: Any) -> str:
    txt = str(value or "").casefold()
    txt = txt.replace("0", "o").replace("1", "l")
    txt = txt.replace("ſ", "s")
    txt = re.sub(r"[^a-zäöüßà-ÿ]", "", txt)
    return txt


def _bk_autocorrect_distance(a: str, b: str, limit: int = 2) -> int:
    if a == b:
        return 0
    if abs(len(a) - len(b)) > limit:
        return limit + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        row_min = i
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            val = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
            cur.append(val)
            if val < row_min:
                row_min = val
        if row_min > limit:
            return limit + 1
        prev = cur
    return prev[-1]

_BK_AUTOCORRECT_WORD_CHARS = r"A-Za-zÄÖÜäöüßÀ-ÿ"
_BK_AUTOCORRECT_TOKEN_RE = re.compile(rf"(?<![{_BK_AUTOCORRECT_WORD_CHARS}0-9])[{_BK_AUTOCORRECT_WORD_CHARS}0-9][{_BK_AUTOCORRECT_WORD_CHARS}0-9'’\-]{{2,}}(?![{_BK_AUTOCORRECT_WORD_CHARS}0-9])")
_BK_AUTOCORRECT_WORD_RE = re.compile(rf"(?<![{_BK_AUTOCORRECT_WORD_CHARS}])[{_BK_AUTOCORRECT_WORD_CHARS}][{_BK_AUTOCORRECT_WORD_CHARS}'’\-]{{2,}}(?![{_BK_AUTOCORRECT_WORD_CHARS}])")
_BK_AUTOCORRECT_MONTH_NORMS = {
    "januar", "jan", "februar", "feb", "märz", "maerz", "mär", "mar",
    "april", "apr", "mai", "juni", "jun", "juli", "jul", "august", "aug",
    "september", "sept", "sep", "oktober", "okt", "november", "nov", "dezember", "dez",
}


def _bk_autocorrect_restore_case(original: str, replacement: str) -> str:
    repl = str(replacement or "")
    if not repl:
        return repl
    letters = "".join(ch for ch in str(original or "") if ch.isalpha())
    if letters and letters.isupper():
        return repl.upper()
    return repl


def _bk_autocorrect_norm_token(token: str) -> str:
    variants = _bk_autocorrect_norm_variants(token)
    return variants[0] if variants else ""


def _bk_autocorrect_add_variant(out: list, seen: set, value: str):
    norm = _bk_autocorrect_norm(value)
    if norm and norm not in seen:
        seen.add(norm)
        out.append(norm)


def _bk_autocorrect_norm_variants(token: str) -> list:
    token = str(token or "")
    out = []
    seen = set()
    if any(ch.isdigit() for ch in token) and any(ch.isalpha() for ch in token):
        stripped_any = re.sub(r"^\d+(?=[A-Za-zÄÖÜäöüßÀ-ÿ])|(?<=[A-Za-zÄÖÜäöüßÀ-ÿ])\d+$", "", token)
        strip_first = bool(
            re.match(r"^\d{2,}(?=[A-Za-zÄÖÜäöüßÀ-ÿ])", token)
            or re.search(r"(?<=[A-Za-zÄÖÜäöüßÀ-ÿ])\d{2,}$", token)
            or re.match(r"^\d(?=[A-ZÄÖÜÀ-Ý])", token)
        )
        if strip_first and stripped_any and stripped_any != token:
            _bk_autocorrect_add_variant(out, seen, stripped_any)
        _bk_autocorrect_add_variant(out, seen, token)
        if (not strip_first) and stripped_any and stripped_any != token:
            _bk_autocorrect_add_variant(out, seen, stripped_any)
        stripped = re.sub(r"^[\d\s\.,:;]+|[\d\s\.,:;]+$", "", token)
        if stripped and stripped != token:
            _bk_autocorrect_add_variant(out, seen, stripped)
    else:
        _bk_autocorrect_add_variant(out, seen, token)
    return out

def _bk_autocorrect_common_prefix(a: str, b: str) -> int:
    count = 0
    for ca, cb in zip(a, b):
        if ca != cb:
            break
        count += 1
    return count


def _bk_autocorrect_common_suffix(a: str, b: str) -> int:
    count = 0
    for ca, cb in zip(reversed(a), reversed(b)):
        if ca != cb:
            break
        count += 1
    return count


def _bk_autocorrect_ngrams(value: str, size: int) -> set:
    value = str(value or "")
    if len(value) < size:
        return set()
    return {value[i:i + size] for i in range(0, len(value) - size + 1)}


def _bk_autocorrect_similarity_rank(norm: str, cand_norm: str) -> int:
    norm = str(norm or "")
    cand_norm = str(cand_norm or "")
    return (
        4 * _bk_autocorrect_common_suffix(norm, cand_norm)
        + 3 * _bk_autocorrect_common_prefix(norm, cand_norm)
        + 3 * len(_bk_autocorrect_ngrams(norm, 2).intersection(_bk_autocorrect_ngrams(cand_norm, 2)))
        + len(_bk_autocorrect_ngrams(norm, 3).intersection(_bk_autocorrect_ngrams(cand_norm, 3)))
    )


def _bk_autocorrect_max_distance(norm: str) -> int:
    length = len(str(norm or ""))
    if length < 3:
        return 0
    if length == 3:
        return 1
    if length <= 8:
        return 2
    return 2


def _bk_autocorrect_weight_bonus(weight: float) -> int:
    try:
        w = float(weight)
    except Exception:
        w = 1.0
    if w >= 100:
        return 24
    if w >= 50:
        return 22
    if w >= 25:
        return 20
    if w >= 10:
        return 16
    if w >= 5:
        return 10
    if w >= 2:
        return 5
    return 0


def _bk_autocorrect_best_term(norm: str, buckets: dict, exact: dict, weights: dict = None, skip_norm: str = None):
    norm = str(norm or "")
    if not norm:
        return None, 99, None
    max_dist = _bk_autocorrect_max_distance(norm)
    if max_dist <= 0:
        return None, 99, None
    weights = weights or {}
    best_term = None
    best_norm = None
    best_dist = 99
    best_score = -1
    best_rank = -1
    best_weight = -1.0
    best_len_delta = 999
    for ln in range(max(1, len(norm) - max_dist), len(norm) + max_dist + 1):
        for cand_norm, cand_term in buckets.get(ln, []):
            if skip_norm is not None and cand_norm == skip_norm:
                continue
            dist = _bk_autocorrect_distance(norm, cand_norm, max_dist)
            if dist > max_dist:
                continue
            rank = _bk_autocorrect_similarity_rank(norm, cand_norm)
            weight = float(weights.get(cand_norm, 1.0))
            if dist >= 2 and len(norm) <= 5 and rank < 8:
                continue
            if dist == 1 and len(norm) == 3 and rank < 7 and weight < 8:
                continue
            len_delta = abs(len(norm) - len(cand_norm))
            score = rank + _bk_autocorrect_weight_bonus(weight)
            key = (dist, -score, len_delta, -rank, -weight)
            best_key = (best_dist, -best_score, best_len_delta, -best_rank, -best_weight)
            if key < best_key:
                best_dist = dist
                best_score = score
                best_rank = rank
                best_weight = weight
                best_len_delta = len_delta
                best_term = cand_term
                best_norm = cand_norm
    if best_term is None or best_dist > max_dist:
        return None, 99, None
    return best_term, best_dist, best_norm


def _bk_autocorrect_best_override_term(norm: str, buckets: dict, exact: dict, weights: dict = None):
    norm = str(norm or "")
    weights = weights or {}
    max_dist = _bk_autocorrect_max_distance(norm)
    if not norm or max_dist <= 0:
        return None, 99, None
    best_term = None
    best_norm = None
    best_dist = 99
    best_score = -1
    best_rank = -1
    best_weight = -1.0
    best_len_delta = 999
    for ln in range(max(1, len(norm) - max_dist), len(norm) + max_dist + 1):
        for cand_norm, cand_term in buckets.get(ln, []):
            if cand_norm == norm:
                continue
            dist = _bk_autocorrect_distance(norm, cand_norm, max_dist)
            if dist > max_dist:
                continue
            rank = _bk_autocorrect_similarity_rank(norm, cand_norm)
            weight = float(weights.get(cand_norm, 1.0))
            if dist >= 2 and len(norm) <= 5 and rank < 8:
                continue
            if dist == 1 and len(norm) == 3 and rank < 7 and weight < 8:
                continue
            score = rank + _bk_autocorrect_weight_bonus(weight)
            len_delta = abs(len(norm) - len(cand_norm))
            key = (-score, dist, len_delta, -rank, -weight)
            best_key = (-best_score, best_dist, best_len_delta, -best_rank, -best_weight)
            if key < best_key:
                best_term = cand_term
                best_norm = cand_norm
                best_dist = dist
                best_score = score
                best_rank = rank
                best_weight = weight
                best_len_delta = len_delta
    if best_term is None:
        return None, 99, None
    return best_term, best_dist, best_norm

def _bk_autocorrect_should_override_exact(norm: str, cand_norm: str, dist: int, weights: dict) -> bool:
    if not cand_norm or dist <= 0:
        return False
    exact_weight = float((weights or {}).get(norm, 1.0))
    cand_weight = float((weights or {}).get(cand_norm, 1.0))
    rank = _bk_autocorrect_similarity_rank(norm, cand_norm)
    if len(norm) <= 3:
        return dist == 1 and rank >= 8 and cand_weight >= max(5.0, exact_weight * 4.0)
    if len(norm) <= 5:
        return dist <= 2 and rank >= 8 and cand_weight >= max(8.0, exact_weight * 5.0)
    return dist <= 2 and rank >= 10 and cand_weight >= max(10.0, exact_weight * 6.0)


def _bk_autocorrect_correct_reference_token(token: str, buckets: dict, exact: dict, weights: dict = None) -> str:
    token = str(token or "")
    weights = weights or {}
    best_term = None
    best_dist = 99
    best_rank = -1
    best_weight = -1.0
    best_variant_index = 999
    for variant_index, norm in enumerate(_bk_autocorrect_norm_variants(token)):
        if len(norm) < 3:
            continue
        if norm in exact:
            term = exact[norm]
            dist = 0
            cand_norm = norm
            alt_term, alt_dist, alt_norm = _bk_autocorrect_best_override_term(norm, buckets, exact, weights)
            if alt_term is not None and _bk_autocorrect_should_override_exact(norm, alt_norm, alt_dist, weights):
                term, dist, cand_norm = alt_term, alt_dist, alt_norm
        else:
            term, dist, cand_norm = _bk_autocorrect_best_term(norm, buckets, exact, weights)
            if term is None:
                continue
        rank = _bk_autocorrect_similarity_rank(norm, _bk_autocorrect_norm(term))
        weight = float(weights.get(cand_norm or _bk_autocorrect_norm(term), 1.0))
        key = (dist, variant_index, -rank, -weight)
        best_key = (best_dist, 999, -best_rank, -best_weight) if best_term is None else (best_dist, best_variant_index, -best_rank, -best_weight)
        if key < best_key:
            best_term = term
            best_dist = dist
            best_rank = rank
            best_weight = weight
            best_variant_index = variant_index
    if best_term is None:
        return token
    return _bk_autocorrect_restore_case(token, best_term)


def _bk_autocorrect_correct_embedded_numeric_tokens(text: str, buckets: dict, exact: dict, weights: dict) -> str:
    def repl(match):
        token = match.group(0)
        if not any(ch.isdigit() for ch in token) or not any(ch.isalpha() for ch in token):
            return token
        return _bk_autocorrect_correct_reference_token(token, buckets, exact, weights)
    return _BK_AUTOCORRECT_TOKEN_RE.sub(repl, str(text or ""))


def _bk_autocorrect_correct_word_tokens(text: str, buckets: dict, exact: dict, weights: dict) -> str:
    def repl(match):
        return _bk_autocorrect_correct_reference_token(match.group(0), buckets, exact, weights)
    return _BK_AUTOCORRECT_WORD_RE.sub(repl, str(text or ""))


def _bk_autocorrect_reference_phrase(phrase: str, buckets: dict, exact: dict, weights: dict):
    phrase = str(phrase or "").strip()
    if not phrase:
        return None
    words = list(_BK_AUTOCORRECT_WORD_RE.finditer(phrase))
    if not words:
        return None
    gap_text = _BK_AUTOCORRECT_WORD_RE.sub("", phrase)
    if re.search(r"[^\s,;:'’\-\.]+", gap_text):
        return None
    norms = [_bk_autocorrect_norm(match.group(0)) for match in words]
    if any(norm in _BK_AUTOCORRECT_MONTH_NORMS for norm in norms):
        return None
    resolved = []
    for match, norm in zip(words, norms):
        if norm in exact:
            term = exact[norm]
            alt_term, alt_dist, alt_norm = _bk_autocorrect_best_override_term(norm, buckets, exact, weights)
            if alt_term is not None and _bk_autocorrect_should_override_exact(norm, alt_norm, alt_dist, weights):
                term = alt_term
            resolved.append(_bk_autocorrect_restore_case(match.group(0), term))
            continue
        corrected = _bk_autocorrect_correct_reference_token(match.group(0), buckets, exact, weights)
        if corrected == match.group(0):
            return None
        resolved.append(_bk_autocorrect_restore_case(match.group(0), corrected))
    idx = 0
    def repl(_match):
        nonlocal idx
        item = resolved[idx]
        idx += 1
        return item
    return _BK_AUTOCORRECT_WORD_RE.sub(repl, phrase).strip(" ,;:-.\t")

def _bk_autocorrect_cleanup_numeric_reference_lines(text: str, buckets: dict, exact: dict, weights: dict) -> str:
    out = []
    for raw_line in str(text or "").splitlines(True):
        newline = ""
        line = raw_line
        if line.endswith("\r\n"):
            line, newline = line[:-2], "\r\n"
        elif line.endswith("\n") or line.endswith("\r"):
            line, newline = line[:-1], line[-1]
        leading = re.match(r"^\s*", line).group(0)
        trailing = re.search(r"\s*$", line).group(0)
        core = line.strip()
        replacement = None
        match = re.match(r"^\d{1,4}[\s\.,:;]+(.+?)$", core)
        if match:
            replacement = _bk_autocorrect_reference_phrase(match.group(1), buckets, exact, weights)
        if replacement is None:
            match = re.match(r"^(.+?)[\s\.,:;]+\d{1,4}$", core)
            if match:
                replacement = _bk_autocorrect_reference_phrase(match.group(1), buckets, exact, weights)
        if replacement:
            out.append(leading + replacement + trailing + newline)
        else:
            out.append(line + newline)
    return "".join(out)


def _bk_autocorrect_apply_reference_terms(text: str, replacements=None) -> str:
    terms = _bk_autocorrect_terms_from_replacements(replacements)
    if not terms:
        return text
    buckets = {}
    exact = {}
    weights = {}
    display_weights = {}
    for entry in terms:
        term, weight = _bk_autocorrect_payload_entry(entry)
        norm = _bk_autocorrect_norm(term)
        if not norm:
            continue
        old_weight = float(weights.get(norm, 0.0))
        weights[norm] = old_weight + float(weight)
        if norm not in exact or float(weight) > float(display_weights.get(norm, 0.0)):
            exact[norm] = term
            display_weights[norm] = float(weight)
    for norm, term in exact.items():
        buckets.setdefault(len(norm), []).append((norm, term))
    txt = str(text or "")
    # Erste Stufe: OCR-Zahlenmüll direkt an Referenzwörtern entfernen, z. B. "23Emilia" -> "Emilia".
    txt = _bk_autocorrect_correct_embedded_numeric_tokens(txt, buckets, exact, weights)
    # Zweite Stufe: Wortfehler gegen die Referenzliste abgleichen. Gewichtete CSV-Referenzen dürfen seltene Exakt-Treffer korrigieren, z. B. "Nia" -> "Mia", wenn "Mia" deutlich wahrscheinlicher ist.
    txt = _bk_autocorrect_correct_word_tokens(txt, buckets, exact, weights)
    # Dritte Stufe: eine alleinstehende OCR-Zahl vor/nach einem reinen Referenzbegriff entfernen, z. B. "19 Mohammad" -> "Mohammad".
    txt = _bk_autocorrect_cleanup_numeric_reference_lines(txt, buckets, exact, weights)
    return txt

def _parse_ocr_auto_revision_replacements(value: Any):
    if value is None: return list(OCR_AUTO_REVISION_DEFAULT_REPLACEMENTS)
    if isinstance(value, (list, tuple)):
        out = [(str(i[0]), str(i[1])) for i in value if isinstance(i, (list, tuple)) and len(i) >= 2 and str(i[0])]
        return out or list(OCR_AUTO_REVISION_DEFAULT_REPLACEMENTS)
    out = []
    for raw in str(value).splitlines():
        line = raw.strip()
        if not line or line.startswith("#"): continue
        sep = "=>" if "=>" in line else "=" if "=" in line else None
        if not sep: continue
        src, dst = [part.strip() for part in line.split(sep, 1)]
        if src: out.append((src, dst))
    return out or list(OCR_AUTO_REVISION_DEFAULT_REPLACEMENTS)
def _apply_ocr_auto_revision_replacements(text: Any, replacements=None) -> str:
    txt = _clean_ocr_raw_text(text)
    for src, dst in _parse_ocr_auto_revision_replacements(replacements):
        txt = txt.replace(src, dst)
    txt = _bk_autocorrect_apply_reference_terms(txt, replacements)
    return re.sub(r"[ \t\r\f\v]+", " ", txt).strip()
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
def _clean_ocr_raw_text(text: Any) -> str:
    if text is None:
        return ""
    if isinstance(text, bytes):
        txt = text.decode("utf-8", errors="replace")
    else:
        txt = str(text)
    txt = txt.replace("\u00a0", " ")
    txt = txt.replace("\u200b", "")
    txt = txt.replace("\ufeff", "")
    txt = re.sub(r"[ \t\r\f\v]+", " ", txt)
    return txt.strip()
def _clean_ocr_text_for_kraken_display(text: Any, auto_revision_enabled: bool = False, auto_revision_replacements=None) -> str:
    if bool(auto_revision_enabled):
        return _apply_ocr_auto_revision_replacements(text, auto_revision_replacements)
    return _clean_ocr_raw_text(text)
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
    try:
        if not rv.bbox:
            return _pil_to_data_url(im, max_side=1600)
        x0, y0, x1, y1 = rv.bbox
        x0 = max(0, int(x0) - int(pad_x))
        y0 = max(0, int(y0) - int(pad_y) - int(extra_context_y))
        x1 = min(im.size[0], int(x1) + int(pad_x))
        y1 = min(im.size[1], int(y1) + int(pad_y) + int(extra_context_y))
        crop = im.crop((x0, y0, x1, y1))
        try:
            return _pil_to_data_url(crop, max_side=1600)
        finally:
            try:
                crop.close()
            except Exception:
                pass
    finally:
        try:
            im.close()
        except Exception:
            pass


def _crop_overlay_box_to_data_url_strict(
        path: str,
        rv: "RecordView",
        pad_x: int = 0,
        pad_y: int = 0,
        extra_context_y: int = 0,
        max_side: int = 1600,
) -> str:
    """Return only the requested overlay-box crop; never fall back to a page image.

    This is intentionally stricter than ``_crop_single_line_to_data_url``.  LM
    line transcription must never silently send a complete page when the box is
    missing or malformed, because that would make every line request behave like
    a full-page OCR request.
    """
    bbox = getattr(rv, "bbox", None)
    if not bbox or len(bbox) != 4:
        raise ValueError("Overlay box is missing or malformed; refusing full-page fallback.")

    im = _load_image_color(path)
    try:
        page_w, page_h = int(im.size[0]), int(im.size[1])
        try:
            bx0, by0, bx1, by1 = (int(round(float(v))) for v in bbox)
        except Exception as exc:
            raise ValueError(f"Invalid overlay box coordinates: {bbox!r}") from exc

        px = max(0, int(pad_x or 0))
        py = max(0, int(pad_y or 0))
        ey = max(0, int(extra_context_y or 0))
        x0 = max(0, min(page_w, bx0 - px))
        y0 = max(0, min(page_h, by0 - py - ey))
        x1 = max(0, min(page_w, bx1 + px))
        y1 = max(0, min(page_h, by1 + py + ey))
        if x1 <= x0 or y1 <= y0:
            raise ValueError(
                f"Overlay box is outside the source image or empty: bbox={bbox!r}, "
                f"image={page_w}x{page_h}."
            )
        crop_w = x1 - x0
        crop_h = y1 - y0
        if crop_w >= int(page_w * 0.98) and crop_h >= int(page_h * 0.98):
            raise ValueError(
                f"Overlay crop would contain almost the complete page; refusing line request: "
                f"bbox={bbox!r}, crop={crop_w}x{crop_h}, image={page_w}x{page_h}."
            )

        crop = im.crop((x0, y0, x1, y1))
        try:
            # The payload is built from this crop only.  No page-level fallback is
            # allowed here, even for very small boxes.
            return _pil_to_data_url(crop, max_side=max(64, int(max_side or 1600)))
        finally:
            try:
                crop.close()
            except Exception:
                pass
    finally:
        try:
            im.close()
        except Exception:
            pass
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
        "single_pad_x": 0,
        "single_pad_y": 0,
        "single_extra_context_y": 0,
        "block_pad_x": 0,
        "block_pad_y": 0,
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
    if abs(ay0 - by0) > 12:
        return False
    w = max(1, int(page_width))
    mid = w // 2
    aw = ax1 - ax0
    bw = bx1 - bx0
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
    hs = sorted([(rv.bbox[3] - rv.bbox[1]) for rv in recs if (rv.bbox[3] - rv.bbox[1]) > 0])
    med_h = hs[len(hs) // 2] if hs else 14
    y_tol = max(10, int(0.45 * med_h))
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
__all__ = [
    'AI_SCRIPT_HANDWRITING',
    'AI_SCRIPT_MIXED',
    'AI_SCRIPT_PRINT',
    'OCR_AUTO_REVISION_DEFAULT_REPLACEMENTS',
    '_ai_script_crop_profile',
    '_ai_script_prompt_hint',
    '_append_error_log_entry',
    '_apply_ocr_auto_revision_replacements',
    '_clean_ocr_raw_text',
    '_clean_ocr_text',
    '_clean_ocr_text_for_kraken_display',
    '_crop_block_to_data_url_context',
    '_crop_single_line_to_data_url',
    '_crop_overlay_box_to_data_url_strict',
    '_extract_json_payload',
    '_extract_json_string_lines_object',
    '_force_text',
    '_image_to_data_url',
    '_install_exception_hook',
    '_is_effectively_empty_ocr_text',
    '_normalize_ai_script_mode',
    '_page_to_data_url',
    '_page_to_small_png_data_url',
    '_parse_ocr_auto_revision_replacements',
    '_pil_to_data_url',
    '_safe_int',
    '_serialize_ocr_auto_revision_replacements',
    'clamp_bbox',
    'cluster_columns',
    'expand_segmentation_bbox',
    'group_rows_by_y',
    'is_same_visual_row',
    'sort_records_handwriting_simple',
    'sort_records_reading_order',
]
register_globals('shared', globals(), __all__)
