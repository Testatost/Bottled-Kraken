# --- FIX8.53: force rich same-line age corrections when LM read is complete ---
# v25 allowed age-number corrections in the score path. In practice, selected/current
# line runs can still fall back to Kraken if a caller or hard barrier keeps the old
# short line. This final guard makes the intended case explicit: same name, same age
# unit, richer table columns => use the richer LM candidate.

_BK_FIX53_AGE_RE = re.compile(
    r"\b(\d{1,3})\s*['’´`\.]*\s*"
    r"(Jahre?|Jahren|Monate?|Monaten|Wochen|Tage?|Tagen|Stunden?)\b['’´`\.]*",
    flags=re.IGNORECASE,
)
_BK_FIX53_UNIT_MAP = {
    "jahr": "jahr", "jahre": "jahr", "jahren": "jahr",
    "monat": "monat", "monate": "monat", "monaten": "monat",
    "woche": "woche", "wochen": "woche",
    "tag": "tag", "tage": "tag", "tagen": "tag",
    "stunde": "stunde", "stunden": "stunde",
}

def _bk_fix53_age_pairs(text: str):
    out = []
    for m in _BK_FIX53_AGE_RE.finditer(str(text or "")):
        unit = _BK_FIX53_UNIT_MAP.get(m.group(2).casefold())
        if unit:
            out.append((m.group(1), unit))
    return out

def _bk_fix53_name_anchor_tokens(text: str):
    tokens = []
    for tok in _bk_fix49_tokens(text):
        if tok.isdigit():
            continue
        if tok in _BK_FIX53_UNIT_MAP:
            continue
        if re.fullmatch(r"[ivxlcdm]+", tok):
            continue
        if len(tok) <= 1:
            continue
        tokens.append(tok)
    return tokens

def _bk_fix53_stable_numbers(text: str) -> set:
    age_nums = {num for num, _unit in _bk_fix53_age_pairs(text)}
    return _bk_fix49_number_set(text) - age_nums

def _bk_fix53_has_rich_table_tail(text: str) -> bool:
    t = str(text or "")
    nums = _bk_fix49_number_set(t)
    # Datum + Jahr/Nummer oder mehrere rechte Tabellenspalten.
    if re.search(r"\b\d{1,2}\s*[./]\s*(?:[ivxlcdmIVXLCDM]{1,8}|\d{1,2})\s*[./]?", t):
        if re.search(r"\b\d{3,4}\b", t) or len(nums) >= 3:
            return True
    if re.search(r"\b\d{3,4}\b", t) and len(nums) >= 3:
        return True
    # Sehr typische OCR-Tabellenzeile: Alter + Datum + Ort + laufende Nummer.
    return bool(len(nums) >= 4 and re.search(r"[A-Za-zÀ-ÿÄÖÜäöüß]{3,}", t))

def _bk_fix53_should_force_rich_candidate(worker, kraken_text: str, candidate_text: str) -> bool:
    ref = _bk_fix50_norm_space(kraken_text)
    cand = _bk_fix50_norm_space(candidate_text)
    if not ref or not cand or ref == cand:
        return False
    if _bk_fix50_is_bad_line_candidate(worker, cand, ref):
        return False
    ref_ages = _bk_fix53_age_pairs(ref)
    cand_ages = _bk_fix53_age_pairs(cand)
    if not ref_ages or not cand_ages:
        return False
    if not ({unit for _n, unit in ref_ages} & {unit for _n, unit in cand_ages}):
        return False
    # Nicht-Alterszahlen aus Kraken bleiben weiterhin hart geschützt.
    if _bk_fix53_stable_numbers(ref) - _bk_fix49_number_set(cand):
        return False
    ref_anchor = _bk_fix53_name_anchor_tokens(ref)
    cand_anchor = set(_bk_fix53_name_anchor_tokens(cand))
    if len(ref_anchor) >= 2:
        if not (ref_anchor[0] in cand_anchor and ref_anchor[1] in cand_anchor):
            return False
    elif ref_anchor:
        if ref_anchor[0] not in cand_anchor:
            return False
    else:
        return False
    if _bk_fix49_info_len(cand) < _bk_fix49_info_len(ref) + 12:
        return False
    if len(_bk_fix49_number_set(cand)) <= len(_bk_fix49_number_set(ref)):
        return False
    if not _bk_fix53_has_rich_table_tail(cand):
        return False
    # Bei gleichem Namen + gleicher Alterseinheit + rechter Tabellenergänzung darf
    # die Alterszahl selbst korrigiert werden (62 -> 69 etc.).
    return True

_BK_FIX53_PREV_SANITY_MERGE_LINE = _bk_fix50_sanity_merge_line

def _bk_fix53_sanity_merge_line(worker, kraken_text: str, lm_box_text: str, page_line_text: str = "", prev_final_text: str = "", full_page_context: str = "", page_index_aligned: bool = True) -> str:
    best = _BK_FIX53_PREV_SANITY_MERGE_LINE(
        worker,
        kraken_text,
        lm_box_text,
        page_line_text,
        prev_final_text,
        full_page_context,
        page_index_aligned,
    )
    kt = _bk_fix50_norm_space(kraken_text)
    best_norm = _bk_fix50_norm_space(best)
    candidates = []
    for cand in (lm_box_text, page_line_text):
        cand_norm = _bk_fix50_norm_space(cand)
        if cand_norm and cand_norm not in candidates:
            candidates.append(cand_norm)
    # Wenn die beste Auswahl noch die kurze Kraken-Zeile ist, aber eine LM-Quelle
    # exakt den typischen vollständigen Tabellenfall liefert, diese Quelle erzwingen.
    if kt and best_norm == kt:
        for cand in candidates:
            if _bk_fix53_should_force_rich_candidate(worker, kt, cand):
                return cand
    return best_norm

_bk_fix50_sanity_merge_line = _bk_fix53_sanity_merge_line
_bk_fix49_sanity_merge_line = _bk_fix53_sanity_merge_line
_bk_fix46_sanity_merge_line = _bk_fix53_sanity_merge_line

def _bk_fix53_merge_candidates(worker, kraken_text: str, page_text: str, box_text: str, prev_final_text: str = "") -> str:
    return _bk_fix53_sanity_merge_line(worker, kraken_text, box_text, page_text, prev_final_text, page_text, True)

_bk_fix50_merge_candidates = _bk_fix53_merge_candidates
_bk_fix49_merge_candidates = _bk_fix53_merge_candidates
_bk_fix45_merge_candidates = _bk_fix53_merge_candidates
_bk_fix43_choose_final_kraken_first = _bk_fix53_merge_candidates
_bk_fix41_choose_final_kraken_first = _bk_fix53_merge_candidates

try:
    AIRevisionWorker._choose_final_line_text = lambda self, kraken_text, box_text, page_text, prev_final_text='': _bk_fix53_sanity_merge_line(self, kraken_text, box_text, page_text, prev_final_text, page_text, True)
    AIRevisionWorker._request_line_decision = lambda self, idx, kraken_text, page_text, box_text: _bk_fix53_sanity_merge_line(self, kraken_text, box_text, page_text, '', page_text, True)
except Exception:
    pass
