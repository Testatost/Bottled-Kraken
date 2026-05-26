"""Robuster Sanity-Check für LM-Zeilenüberarbeitung.

Diese Runtime-Erweiterung hält Kraken als konservativen Anker, lässt aber
LM-Box-OCR gewinnen, wenn sie plausibel ergänzt oder erkennbare Lesefehler
korrigiert, ohne Namen/Zahlen/Daten aus Kraken zu verlieren.
"""

def _bk_fix49_tokens(text: str) -> List[str]:
    return re.findall(r"[A-Za-zÀ-ÿÄÖÜäöüß0-9]+", str(text or "").casefold())

def _bk_fix49_token_set(text: str) -> set:
    return set(_bk_fix49_tokens(text))

def _bk_fix49_number_set(text: str) -> set:
    return set(re.findall(r"\b\d+(?:[./-]\d+)*\b", str(text or "")))

def _bk_fix49_info_len(text: str) -> int:
    return len("".join(_bk_fix49_tokens(text)))

def _bk_fix49_missing_ratio(reference: str, candidate: str) -> float:
    ref = _bk_fix49_token_set(reference)
    if not ref:
        return 0.0
    cand = _bk_fix49_token_set(candidate)
    if not cand:
        return 1.0
    return len(ref - cand) / max(1, len(ref))

def _bk_fix49_token_overlap_ratio(reference: str, candidate: str) -> float:
    ref = _bk_fix49_token_set(reference)
    cand = _bk_fix49_token_set(candidate)
    if not ref or not cand:
        return 0.0
    return len(ref & cand) / max(1, min(len(ref), len(cand)))

def _bk_fix49_similarity(worker, left: str, right: str) -> float:
    try:
        return float(worker._text_similarity_ratio(left, right))
    except Exception:
        import difflib
        a = " ".join(_bk_fix49_tokens(left))
        b = " ".join(_bk_fix49_tokens(right))
        if not a and not b:
            return 1.0
        if not a or not b:
            return 0.0
        return difflib.SequenceMatcher(None, a, b).ratio()

def _bk_fix49_page_support(candidate: str, page_context: str) -> float:
    # Der Seitenkontext ist bei aktueller/markierter Zeile nicht zwingend indexgenau.
    # Deshalb nur als weiches Stützsignal verwenden: Wie viele Kandidaten-Tokens
    # kommen irgendwo im Kontext vor?
    cand_tokens = _bk_fix49_token_set(candidate)
    if not cand_tokens:
        return 0.0
    page_tokens = _bk_fix49_token_set(page_context)
    if not page_tokens:
        return 0.0
    return len(cand_tokens & page_tokens) / max(1, len(cand_tokens))

def _bk_fix49_is_json_debris(text: str) -> bool:
    t = _clean_ocr_text(text or "")
    if not t:
        return False
    low = t.casefold()
    return (
        t.startswith("{")
        or t.startswith("[")
        or "bbox_norm" in low
        or '"lines"' in low
        or '"text"' in low and ("{" in t or "}" in t)
    )

def _bk_fix49_is_unsafe_single_line(worker, text: str, reference: str = "") -> bool:
    t = _clean_ocr_text(text or "")
    if not t:
        return True
    if _bk_fix49_is_json_debris(t):
        return True
    if "\n" in t:
        return True
    # Symbol-/Müll-Zeilen bleiben verdächtig, echte Ditto-Zeichen werden aber nicht
    # hier verworfen; deren Auflösung passiert später positionsbezogen.
    if not re.search(r"[A-Za-zÀ-ÿÄÖÜäöüß0-9\"„“]", t):
        return True
    ref = _clean_ocr_text(reference or "")
    if ref:
        ref_len = max(1, len(ref))
        # Mehrere Nachbarzeilen oder ein Absatz dürfen nicht als Einzelzeile gewinnen.
        if len(t) > max(180, int(ref_len * 2.4) + 48):
            return True
        if len(_bk_fix49_tokens(t)) > max(22, len(_bk_fix49_tokens(ref)) + 12):
            return True
    return False

def _bk_fix49_lm_may_replace_kraken(worker, kraken_text: str, lm_text: str, page_context_text: str = "") -> bool:
    kt = _clean_ocr_text(kraken_text or "")
    lt = _clean_ocr_text(lm_text or "")
    pt = _clean_ocr_text(page_context_text or "")

    if _bk_fix49_is_unsafe_single_line(worker, lt, kt):
        return False
    if not kt or _bk_fix49_is_unsafe_single_line(worker, kt, lt):
        return True

    info_kt = _bk_fix49_info_len(kt)
    info_lt = _bk_fix49_info_len(lt)
    if info_lt <= 0:
        return False

    # Harte Schutzregel: LM darf Kraken nicht offensichtlich kürzen.
    if info_lt < max(4, int(info_kt * 0.82)):
        return False

    # Zahlen, Jahreszahlen, Daten und Altersangaben aus Kraken dürfen nicht verschwinden.
    kraken_numbers = _bk_fix49_number_set(kt)
    if kraken_numbers and (kraken_numbers - _bk_fix49_number_set(lt)):
        return False

    missing_from_kraken = _bk_fix49_missing_ratio(kt, lt)
    added_by_lm = _bk_fix49_missing_ratio(lt, kt)
    overlap = _bk_fix49_token_overlap_ratio(kt, lt)
    sim = _bk_fix49_similarity(worker, kt, lt)
    page_support_lm = _bk_fix49_page_support(lt, pt)
    page_support_kraken = _bk_fix49_page_support(kt, pt)

    # Klarer Gewinn: LM enthält mehr Information, verliert aber nur wenig Kraken-Inhalt.
    if info_lt >= info_kt * 1.06 and overlap >= 0.52 and missing_from_kraken <= 0.42:
        return True

    # Wort-/Lesefehlerkorrektur: sehr ähnliche Zeile, nicht kürzer, keine Zahlen verloren.
    if sim >= 0.82 and info_lt >= int(info_kt * 0.88) and missing_from_kraken <= 0.38:
        return True

    # Seitenkontext stützt die LM-Lesung erkennbar stärker als die Kraken-Lesung.
    if sim >= 0.62 and info_lt >= int(info_kt * 0.92):
        if page_support_lm >= min(1.0, page_support_kraken + 0.10) and missing_from_kraken <= 0.45:
            return True

    # Echte Ergänzung: LM bringt zusätzliche Tokens, ohne Kraken wesentlich zu verlieren.
    if added_by_lm >= 0.22 and missing_from_kraken <= 0.35 and info_lt >= info_kt:
        return True

    return False

def _bk_fix49_pick_non_duplicate(worker, best: str, alternatives: List[str], prev_final_text: str = "") -> str:
    best = _clean_ocr_text(best or "")
    prev = _clean_ocr_text(prev_final_text or "")
    if not prev or not best:
        return best
    try:
        if worker._normalize_compare_text(best) != worker._normalize_compare_text(prev):
            return best
        for cand in alternatives:
            cand = _clean_ocr_text(cand or "")
            if not cand:
                continue
            if worker._normalize_compare_text(cand) != worker._normalize_compare_text(prev):
                return cand
    except Exception:
        return best
    return best

def _bk_fix49_sanity_merge_line(worker, kraken_text: str, lm_box_text: str, page_context_text: str = "", prev_final_text: str = "") -> str:
    kt = _clean_ocr_text(kraken_text or "")
    lt = _clean_ocr_text(lm_box_text or "")
    pt = _clean_ocr_text(page_context_text or "")

    # Standard: Kraken bleibt Anker. LM gewinnt nur nach bestandener Plausibilitätsprüfung.
    if kt and not _bk_fix49_is_unsafe_single_line(worker, kt, lt):
        best = kt
    elif lt and not _bk_fix49_is_unsafe_single_line(worker, lt, kt):
        best = lt
    else:
        best = kt or lt or ""

    if _bk_fix49_lm_may_replace_kraken(worker, kt, lt, pt):
        best = lt

    # Page-/Block-OCR darf nur dann direkt gewinnen, wenn sie wie eine einzelne Zeile
    # aussieht. Im aktuellen/markierten Modus ist pt meistens kompletter Seitenkontext.
    page_looks_single_line = bool(pt and "\n" not in pt and len(pt) <= max(140, len(best) * 2 + 40))
    if page_looks_single_line and _bk_fix49_lm_may_replace_kraken(worker, best, pt, lt):
        best = pt

    best = _bk_fix49_pick_non_duplicate(worker, best, [lt, kt, pt], prev_final_text)
    return _clean_ocr_text(best or kt or lt or pt)

def _bk_fix49_merge_candidates(worker, kraken_text: str, page_text: str, box_text: str, prev_final_text: str = "") -> str:
    return _bk_fix49_sanity_merge_line(worker, kraken_text, box_text, page_text, prev_final_text)

# Die vorhandene fix46-Run-Funktion schaut diesen Namen zur Laufzeit global nach.
# Durch die spätere Definition wird die aktive Sanity-Merge-Logik ersetzt, ohne
# die UI-/Worker-Verkabelung für aktuelle, markierte und alle Zeilen anzufassen.
_bk_fix46_sanity_merge_line = _bk_fix49_sanity_merge_line
_bk_fix45_merge_candidates = _bk_fix49_merge_candidates
_bk_fix43_choose_final_kraken_first = _bk_fix49_merge_candidates
_bk_fix41_choose_final_kraken_first = _bk_fix49_merge_candidates

try:
    _BK_FIX49_PREV_CHOOSE_FINAL_LINE_TEXT = AIRevisionWorker._choose_final_line_text
except Exception:
    _BK_FIX49_PREV_CHOOSE_FINAL_LINE_TEXT = None

def _bk_fix49_choose_final_line_text(self, kraken_text: str, box_text: str, page_text: str, prev_final_text: str = "") -> str:
    return _bk_fix49_sanity_merge_line(self, kraken_text, box_text, page_text, prev_final_text)

try:
    AIRevisionWorker._choose_final_line_text = _bk_fix49_choose_final_line_text
except Exception:
    pass

try:
    _BK_FIX49_PREV_OVERLAY_BOX_REVISION = _bk_fix46_request_overlay_box_revision
except Exception:
    _BK_FIX49_PREV_OVERLAY_BOX_REVISION = None

def _bk_fix49_request_overlay_box_revision(self, rv, page_context_lines: List[str], local_pos: int, total: int) -> str:
    crop_profile = _ai_script_crop_profile(self.script_mode)
    line_data_url = _crop_single_line_to_data_url(
        self.path,
        rv,
        **_bk_fix57_overlay_crop_kwargs(self, crop_profile, min_pad_x=18, min_pad_y=8),
    )
    kraken_text = _clean_ocr_text(getattr(rv, "text", "") or "")
    page_context = _bk_fix46_context_excerpt_for_line(rv, page_context_lines)
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
            override_max_tokens=max(280, min(max(700, int(getattr(self, "max_tokens", 1200) or 1200)), 1600)),
        ),
    }
    data = self._post_json(payload)
    content = self._extract_message_content(data)
    try:
        print("RAW FIX8.49 OVERLAY LINE RESPONSE:")
        print(content[:2500])
    except Exception:
        pass
    text = _clean_ocr_text(_bk_fix46_parse_single_text(content))
    # Nicht mehr vorschnell auf Kraken zurückfallen, nur weil LM kürzer ist.
    # Ob Kürzung oder Verbesserung vorliegt, entscheidet der Sanity-Check im Merge.
    if _bk_fix49_is_json_debris(text) or "\n" in text:
        return kraken_text
    return text or kraken_text

_bk_fix46_request_overlay_box_revision = _bk_fix49_request_overlay_box_revision

try:
    _BK_FIX49_PREV_REQUEST_LINE_DECISION = AIRevisionWorker._request_line_decision
except Exception:
    _BK_FIX49_PREV_REQUEST_LINE_DECISION = None

def _bk_fix49_request_line_decision(self, idx: int, kraken_text: str, page_text: str, box_text: str) -> str:
    if not callable(_BK_FIX49_PREV_REQUEST_LINE_DECISION):
        return _bk_fix49_merge_candidates(self, kraken_text, page_text, box_text, "")
    decision = _BK_FIX49_PREV_REQUEST_LINE_DECISION(self, idx, kraken_text, page_text, box_text)
    decision = _clean_ocr_text(decision or "")
    # Auch direkte LM-Entscheidungen laufen durch denselben Schutz: LM darf
    # verbessern, aber keine plausible Kraken-Zeile kaputtkürzen.
    return _bk_fix49_sanity_merge_line(self, kraken_text, decision or box_text, page_text, "")

try:
    AIRevisionWorker._request_line_decision = _bk_fix49_request_line_decision
except Exception:
    pass
