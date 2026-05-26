# --- FIX8.50: page-aware sanity merge for LM line revision -----------------
# Problem in 8.49: der komplette LM-Seiten-OCR wurde zwar erzeugt, aber beim
# Merge meist nur als unstrukturierter Kontext benutzt. Dadurch konnte die gute
# Seiten-OCR-Zeile nicht direkt gegen Kraken/Box-OCR gewinnen. 8.50 extrahiert
# pro Overlay-Zeile eine wahrscheinlich passende Seiten-OCR-Zeile und behandelt
# sie als dritte OCR-Quelle.

# --- FIX8.51: JSON-/Schema-Reste aus Seiten-OCR-Zeilen entfernen ---------
# Manche lokalen OpenAI-kompatiblen Server liefern trotz json_schema einzelne
# Pretty-JSON-Zeilen weiter, z.B. "text": "...". Diese Hilfsfunktion
# normalisiert solche Fragmente zu reinem OCR-Text, bevor sie als Seiten- oder
# Box-Kandidat in die Sanity-Logik kommen.
import json as _bk_fix51_json

def _bk_fix51_clean_text_value(value) -> str:
    raw = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not raw:
        return ""
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE).strip()
    raw = re.sub(r"\s*```$", "", raw).strip()
    raw = raw.strip().strip(",").strip()

    def _finish(txt: str) -> str:
        txt = str(txt or "").replace("\\n", "\n").strip().strip(",").strip()
        # Falls nur eine einzelne JSON-String-Zeile übrig ist, korrekt entquoten.
        if len(txt) >= 2 and txt[0] in ('"', "'") and txt[-1] == txt[0]:
            quoted = txt
            try:
                if txt[0] == '"':
                    txt = str(_bk_fix51_json.loads(quoted))
                else:
                    txt = txt[1:-1]
            except Exception:
                txt = txt[1:-1]
        elif txt.startswith(('"', "'")):
            # Tolerant gegen abgeschnittene JSON-Fragmente aus Pretty-Print-Fallbacks.
            txt = txt[1:]
        txt = txt.strip().strip(",").strip()
        return _clean_ocr_text(txt)

    # Vollständige JSON-Objekte/-Listen zuerst sauber auswerten.
    parse_candidates = [raw]
    if raw.startswith("{") and not raw.endswith("}"):
        parse_candidates.append(raw.rstrip(",") + "}")
    if raw.startswith("[") and not raw.endswith("]"):
        parse_candidates.append(raw.rstrip(",") + "]")
    for candidate in parse_candidates:
        try:
            obj = _bk_fix51_json.loads(candidate)
        except Exception:
            continue
        if isinstance(obj, dict):
            for key in ("text", "line", "ocr_text", "corrected_text", "transcription", "result"):
                val = obj.get(key)
                if isinstance(val, (str, int, float)):
                    return _finish(str(val))
        if isinstance(obj, str):
            return _finish(obj)

    # Einzelne Pretty-JSON-Zeile: "text": "..." oder 'text': '...'.
    match = re.match(
        r"""(?is)^\s*['"]?(?:text|line|ocr_text|corrected_text|transcription|result)['"]?\s*:\s*(.*?)\s*,?\s*$""",
        raw,
    )
    if match:
        return _finish(match.group(1))

    return _finish(raw)

def _bk_fix50_norm_space(text: str) -> str:
    return re.sub(r"\s+", " ", _bk_fix51_clean_text_value(text or "")).strip()

def _bk_fix50_normalized_for_prefix(text: str) -> str:
    return " ".join(_bk_fix49_tokens(text))

def _bk_fix50_line_tokens(text: str) -> List[str]:
    return _bk_fix49_tokens(text)

def _bk_fix50_contains_table_completion(text: str) -> bool:
    t = str(text or "")
    # Häufige Muster in den Kirchenbuch-/Tabellenzeilen: Datum, Alter, Orts-/Nr.-Spalte.
    return bool(
        re.search(r"\b\d{1,2}\s*[./]\s*(?:[ivxlcdmIVXLCDM]{1,8}|\d{1,2})\s*[./]?", t)
        or re.search(r"\b\d{3,4}\b", t)
        or re.search(r"\b\d+\s*(?:Jahre?|Wochen?|Tage?|Stunden?)\b", t, flags=re.IGNORECASE)
    )

def _bk_fix50_numbers_compatible(reference: str, candidate: str) -> bool:
    ref_nums = _bk_fix49_number_set(reference)
    if not ref_nums:
        return True
    cand_nums = _bk_fix49_number_set(candidate)
    return not (ref_nums - cand_nums)

def _bk_fix50_candidate_kind_bonus(kind: str) -> float:
    if kind == "page_line":
        return 22.0
    if kind == "lm_box":
        return 14.0
    return 0.0

def _bk_fix50_is_bad_line_candidate(worker, candidate: str, reference: str = "", strict_single_line: bool = True) -> bool:
    cand = _bk_fix50_norm_space(candidate)
    if not cand:
        return True
    if _bk_fix49_is_json_debris(cand):
        return True
    if strict_single_line and "\n" in str(candidate or ""):
        return True
    if not re.search(r"[A-Za-zÀ-ÿÄÖÜäöüß0-9\"„“]", cand):
        return True
    ref = _bk_fix50_norm_space(reference)
    if ref:
        cand_tokens = len(_bk_fix50_line_tokens(cand))
        ref_tokens = len(_bk_fix50_line_tokens(ref))
        # Tabellenzeilen dürfen deutlich länger als Kraken sein, aber nicht
        # wie ein kompletter Absatz oder mehrere Nachbarzeilen aussehen.
        if cand_tokens > max(34, ref_tokens + 24):
            return True
        if len(cand) > max(260, len(ref) * 4 + 80):
            return True
    return False

def _bk_fix50_is_plausible_related(worker, reference: str, candidate: str, index_aligned: bool = False) -> bool:
    ref = _bk_fix50_norm_space(reference)
    cand = _bk_fix50_norm_space(candidate)
    if not cand:
        return False
    if not ref:
        return True
    if _bk_fix50_is_bad_line_candidate(worker, cand, ref):
        return False

    if not _bk_fix50_numbers_compatible(ref, cand):
        return False

    ref_tokens = _bk_fix49_token_set(ref)
    cand_tokens = _bk_fix49_token_set(cand)
    if not ref_tokens or not cand_tokens:
        return False

    overlap_min = len(ref_tokens & cand_tokens) / max(1, min(len(ref_tokens), len(cand_tokens)))
    overlap_ref = len(ref_tokens & cand_tokens) / max(1, len(ref_tokens))
    sim = _bk_fix49_similarity(worker, ref, cand)
    info_ref = max(1, _bk_fix49_info_len(ref))
    info_cand = _bk_fix49_info_len(cand)

    if index_aligned:
        # Bei gleicher Zeilenposition reicht weniger Fuzzy-Ähnlichkeit, weil die
        # Seiten-OCR gerade über die komplette Seite oft zusätzliche rechte
        # Tabellenspalten erkennt, die Kraken nicht enthält.
        if overlap_ref >= 0.34 or sim >= 0.44:
            return True
        # Sehr kurze Kraken-Zeilen wie "seite -52-" oder "Unter P." brauchen
        # einen stärkeren Bezug, damit keine Nachbarzeile gewinnt.
        return info_ref <= 12 and overlap_min >= 0.50

    if overlap_ref >= 0.50 or sim >= 0.58:
        return True

    # Falls Kraken sehr kurz/defekt ist, darf eine deutlich vollständigere LM-
    # Zeile gewinnen, wenn wenigstens ein stabiler Anker geteilt wird.
    return info_cand >= info_ref * 1.35 and overlap_min >= 0.40

def _bk_fix50_score_candidate(worker, kind: str, candidate: str, kraken_text: str, box_text: str, page_line_text: str, full_page_context: str, prev_final_text: str = "", index_aligned: bool = False) -> float:
    cand = _bk_fix50_norm_space(candidate)
    kt = _bk_fix50_norm_space(kraken_text)
    lt = _bk_fix50_norm_space(box_text)
    pt = _bk_fix50_norm_space(page_line_text)

    if _bk_fix50_is_bad_line_candidate(worker, cand, kt if kt else lt):
        return -1000000.0

    score = float(_bk_fix49_info_len(cand)) + _bk_fix50_candidate_kind_bonus(kind)

    if kt and kind != "kraken":
        if not _bk_fix50_is_plausible_related(worker, kt, cand, index_aligned=(kind == "page_line" and index_aligned)):
            return -1000000.0
        missing = _bk_fix49_missing_ratio(kt, cand)
        overlap = _bk_fix49_token_overlap_ratio(kt, cand)
        sim = _bk_fix49_similarity(worker, kt, cand)
        score += 48.0 * overlap
        score += 30.0 * sim
        score -= 82.0 * missing
        if _bk_fix50_numbers_compatible(kt, cand):
            score += 14.0
        if _bk_fix49_info_len(cand) > _bk_fix49_info_len(kt):
            score += min(80.0, (_bk_fix49_info_len(cand) - _bk_fix49_info_len(kt)) * 1.35)
        elif _bk_fix49_info_len(cand) < max(4, int(_bk_fix49_info_len(kt) * 0.82)):
            score -= 80.0

    if kt and kind == "kraken":
        # Kraken bleibt Sicherheitsanker, bekommt aber keinen künstlich so hohen
        # Bonus mehr, dass plausible Ergänzungen verdrängt werden.
        score += 18.0

    if full_page_context:
        score += 10.0 * _bk_fix49_page_support(cand, full_page_context)

    if kind == "lm_box" and pt:
        score += 28.0 * _bk_fix49_similarity(worker, cand, pt)
    elif kind == "page_line" and lt:
        score += 28.0 * _bk_fix49_similarity(worker, cand, lt)

    if _bk_fix50_contains_table_completion(cand):
        score += 10.0

    if prev_final_text:
        try:
            if worker._normalize_compare_text(cand) == worker._normalize_compare_text(prev_final_text):
                score -= 42.0
        except Exception:
            pass

    return score

def _bk_fix50_find_page_line_candidate(worker, rv, kraken_text: str, page_lines: List[str], local_pos: int = 0) -> str:
    lines = [_bk_fix50_norm_space(x) for x in (page_lines or [])]
    lines = [x for x in lines if x and not _bk_fix49_is_json_debris(x)]
    if not lines:
        return ""

    idx_candidates = []
    try:
        idx = int(getattr(rv, "idx", local_pos))
        idx_candidates.append(idx)
    except Exception:
        idx = int(local_pos or 0)
        idx_candidates.append(idx)
    try:
        idx_candidates.append(int(local_pos or 0))
    except Exception:
        pass

    # Direktes Index-Mapping ist bei der aktuellen/markierten Zeile durch fix48
    # explizit bewahrt worden. Deshalb zuerst diese Zeile prüfen.
    for idx0 in idx_candidates:
        if 0 <= idx0 < len(lines):
            cand = lines[idx0]
            if _bk_fix50_is_plausible_related(worker, kraken_text, cand, index_aligned=True):
                return cand

    # Fallback: kleines Fenster um die Ziel-ID. Das fängt Seitentitel oder eine
    # überzählige/fehlende Zeile im Seiten-OCR ab, ohne die ganze Seite zu durchsuchen.
    probe_indices = []
    for base in idx_candidates:
        for delta in range(-4, 5):
            j = base + delta
            if 0 <= j < len(lines) and j not in probe_indices:
                probe_indices.append(j)

    best = (float("-inf"), "")
    for j in probe_indices:
        cand = lines[j]
        if not _bk_fix50_is_plausible_related(worker, kraken_text, cand, index_aligned=False):
            continue
        distance_penalty = min(16.0, abs(j - idx_candidates[0]) * 3.5) if idx_candidates else 0.0
        score = _bk_fix50_score_candidate(worker, "page_line", cand, kraken_text, "", cand, "\n".join(lines), "", index_aligned=False) - distance_penalty
        if score > best[0]:
            best = (score, cand)
    return best[1]

def _bk_fix50_context_excerpt_for_line(worker, rv, page_lines: List[str], page_line_candidate: str, max_chars: int = 5000) -> str:
    base = _bk_fix46_context_excerpt_for_line(rv, page_lines, max_chars=max_chars)
    cand = _bk_fix50_norm_space(page_line_candidate)
    if cand:
        return (
            "Wahrscheinlich passende Zeile aus dem kompletten LM-Seiten-OCR:\n"
            + cand
            + "\n\nKompletter LM-Seiten-OCR als zusätzlicher Kontext:\n"
            + base
        )
    return base

def _bk_fix50_sanity_merge_line(worker, kraken_text: str, lm_box_text: str, page_line_text: str = "", prev_final_text: str = "", full_page_context: str = "", page_index_aligned: bool = True) -> str:
    # Mehrzeilige LM-Box-Antworten sind fast immer Nachbarzeilen/Erklärtext und
    # dürfen nicht durch Normalisierung zu einer scheinbaren Einzelzeile werden.
    raw_box_text = str(lm_box_text or "")
    raw_page_line_text = str(page_line_text or "")
    kt = _bk_fix50_norm_space(kraken_text)
    lt = "" if "\n" in raw_box_text else _bk_fix50_norm_space(lm_box_text)
    pt = "" if "\n" in raw_page_line_text else _bk_fix50_norm_space(page_line_text)
    context = _clean_ocr_text(full_page_context or page_line_text or "")

    candidates = []
    for kind, cand, aligned in (
        ("page_line", pt, page_index_aligned),
        ("lm_box", lt, False),
        ("kraken", kt, False),
    ):
        cand = _bk_fix50_norm_space(cand)
        if not cand:
            continue
        score = _bk_fix50_score_candidate(worker, kind, cand, kt, lt, pt, context, prev_final_text, index_aligned=aligned)
        if score > -999999.0:
            candidates.append((score, kind, cand))

    if not candidates:
        return kt or lt or pt or ""

    candidates.sort(key=lambda row: row[0], reverse=True)
    best_score, best_kind, best = candidates[0]

    # Letzte harte Barriere: keine destruktive Kürzung und kein Verlust stabiler
    # Zahlen aus Kraken. Diese Barriere ist absichtlich enger als das Scoring.
    if kt and best_kind != "kraken":
        if not _bk_fix50_numbers_compatible(kt, best):
            best = kt
        elif _bk_fix49_info_len(best) < max(4, int(_bk_fix49_info_len(kt) * 0.78)):
            best = kt
        elif not _bk_fix50_is_plausible_related(worker, kt, best, index_aligned=(best_kind == "page_line" and page_index_aligned)):
            best = kt

    # Falls die beste Wahl nur die Kraken-Zeile wäre, aber Seiten-OCR und Box-OCR
    # unabhängig sehr ähnlich sind und mehr Information enthalten, darf diese
    # gemeinsame LM-Lesung gewinnen.
    if kt and lt and pt:
        sim_lp = _bk_fix49_similarity(worker, lt, pt)
        richer = pt if _bk_fix49_info_len(pt) >= _bk_fix49_info_len(lt) else lt
        if sim_lp >= 0.78 and _bk_fix49_info_len(richer) >= _bk_fix49_info_len(kt) * 1.05:
            if _bk_fix50_is_plausible_related(worker, kt, richer, index_aligned=True):
                best = richer

    return _bk_fix50_norm_space(best)

def _bk_fix50_merge_candidates(worker, kraken_text: str, page_text: str, box_text: str, prev_final_text: str = "") -> str:
    # Kompatibilitätsfunktion für ältere Call-Sites: page_text wird hier als
    # bereits ausgerichtete Seiten-OCR-Zeile behandelt, nicht als ganzer Kontext.
    return _bk_fix50_sanity_merge_line(worker, kraken_text, box_text, page_text, prev_final_text, page_text, True)

# Aktive Merge-Namen überschreiben. Da alle bk_runtime-Teile im selben Namespace
# ausgeführt werden, greift dies auch für die zuvor definierte fix46-Run-Funktion.
_bk_fix46_sanity_merge_line = _bk_fix50_sanity_merge_line
_bk_fix45_merge_candidates = _bk_fix50_merge_candidates
_bk_fix43_choose_final_kraken_first = _bk_fix50_merge_candidates
_bk_fix41_choose_final_kraken_first = _bk_fix50_merge_candidates
_bk_fix49_sanity_merge_line = _bk_fix50_sanity_merge_line
_bk_fix49_merge_candidates = _bk_fix50_merge_candidates

def _bk_fix50_request_overlay_box_revision(self, rv, page_context_lines: List[str], local_pos: int, total: int) -> str:
    crop_profile = _ai_script_crop_profile(self.script_mode)
    strict_print_crop = _bk_fix57_is_print_script_mode(getattr(self, "script_mode", AI_SCRIPT_PRINT))
    line_data_url = _crop_single_line_to_data_url(
        self.path,
        rv,
        **_bk_fix57_overlay_crop_kwargs(self, crop_profile, min_pad_x=40, min_pad_y=10),
    )
    kraken_text = _bk_fix50_norm_space(getattr(rv, "text", "") or "")
    page_line_candidate = _bk_fix50_find_page_line_candidate(self, rv, kraken_text, page_context_lines, local_pos)
    page_context = _bk_fix50_context_excerpt_for_line(self, rv, page_context_lines, page_line_candidate)
    system_prompt = self._tr("ai_prompt_overlay_compare_system")
    user_prompt = self._tr("ai_prompt_overlay_compare_user", int(getattr(rv, "idx", local_pos)), kraken_text, page_context)
    payload = {
        "model": self.lm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": line_data_url}},
            ]},
        ],
        **self._build_sampling_payload(
            response_format=self._response_format_single_text(),
            override_max_tokens=max(360, min(max(900, int(getattr(self, "max_tokens", 1200) or 1200)), 1800)),
        ),
    }
    data = self._post_json(payload)
    content = self._extract_message_content(data)
    try:
        print("RAW FIX8.50 OVERLAY LINE RESPONSE:")
        print(content[:2500])
    except Exception:
        pass
    text = _bk_fix50_norm_space(_bk_fix46_parse_single_text(content))
    if _bk_fix49_is_json_debris(text) or "\n" in str(text or ""):
        text = ""
    if text:
        return text
    if strict_print_crop:
        # Druckschrift strikt: Wenn die exakt ausgeschnittene Box keine sichere
        # Lesung liefert, nicht auf eine Seiten-OCR-Zeile aus der Nähe ausweichen.
        return kraken_text
    # Wenn das Box-OCR scheitert, nicht sofort auf Kraken zurückfallen: die
    # ausgerichtete Seiten-OCR-Zeile ist hier meist die hochwertigere LM-Quelle.
    if page_line_candidate and _bk_fix50_is_plausible_related(self, kraken_text, page_line_candidate, index_aligned=True):
        return page_line_candidate
    return kraken_text

_bk_fix46_request_overlay_box_revision = _bk_fix50_request_overlay_box_revision

def _bk_fix51_extract_full_page_lines(self, content: str):
    """Robuster Parser für komplette LM-Seiten-OCR.

    Wichtig für Zeilenüberarbeitung: Falls der lokale Server Pretty-JSON nicht
    als Objekt, sondern als einzelne Textzeilen durchreicht, dürfen Schlüssel
    wie "text": nicht in die sichtbaren OCR-Zeilen gelangen.
    """
    out: List[str] = []

    def add_line(value) -> None:
        txt = _bk_fix51_clean_text_value(value)
        if not txt:
            return
        try:
            if _bk_fix41_is_json_debris_text(txt):
                return
        except Exception:
            pass
        # Übrig gebliebene reine Struktur-/BBox-Zeilen konsequent verwerfen.
        if re.match(r'^[\'"]?(?:lines|rows|entries|items|idx|bbox|bbox_norm|box|textbox_norm|textbbox_norm)[\'"]?\s*:?,?\s*$', txt, flags=re.IGNORECASE):
            return
        out.append(txt)

    try:
        obj = _extract_json_payload(content)
    except Exception:
        obj = None

    if isinstance(obj, dict):
        lines = obj.get("lines") or obj.get("rows") or obj.get("entries") or obj.get("items")
        if isinstance(lines, list):
            for item in lines:
                if isinstance(item, dict):
                    add_line(item.get("text") or item.get("line") or item.get("ocr_text") or item.get("corrected_text") or item.get("transcription") or item.get("result") or "")
                else:
                    add_line(item)
        elif isinstance(obj.get("text"), str):
            for line in _extract_text_lines(obj.get("text", "")):
                add_line(line)
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict):
                add_line(item.get("text") or item.get("line") or item.get("ocr_text") or item.get("corrected_text") or item.get("transcription") or item.get("result") or "")
            else:
                add_line(item)

    if not out:
        # Falls frühere Parser vorhanden sind, deren Ergebnisse nachreinigen.
        try:
            for line in _bk_fix40_clean_lm_page_text_lines(content):
                add_line(line)
        except Exception:
            pass

    if not out:
        for line in _extract_text_lines(content or ""):
            add_line(line)

    return out

try:
    AIRevisionWorker._extract_full_page_lines = _bk_fix51_extract_full_page_lines
except Exception:
    pass
try:
    BKFullPageLMOCRWorker._extract_full_page_lines = _bk_fix51_extract_full_page_lines
except Exception:
    pass
