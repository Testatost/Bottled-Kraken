# Ditto guard: ditto marks are deletion-only + more tolerant page completion.
#
# Historical tables often use ditto marks (") in repeated right-hand columns.
# Earlier code resolved these marks by copying the previous row.  For the
# LM revision workflow this can create artificial repeated data and can also keep
# otherwise useful page-OCR candidates from being accepted.  From this point on,
# ditto marks are treated as OCR noise: remove them, never expand them.

_BK_FIX56_DITTO_CHARS = '"„“”‟＂'
_BK_FIX56_STOP_TOKENS = set(globals().get('_BK_FIX55_STOP_TOKENS', set())) | {
    'a', 'ad', 'as', 'sa', 'sd', 'td', 'sg', 'geb', 'weib', 'wwe', 'wwte', 'wittwe', 'witwe'
}

def _bk_fix56_strip_ditto_marks(text: str) -> str:
    """Remove ditto marks instead of copying/repeating previous-row values."""
    raw = '' if text is None else str(text)
    if not raw:
        return ''
    t = raw.replace('\r\n', '\n').replace('\r', '\n')
    # Remove classic standalone register ditto forms: ", -"-, —"—, ("), ( '' ).
    t = re.sub(r"\(\s*[-–—]?\s*[\"„“”‟＂']{1,4}\s*[-–—]?\s*\)", " ", t)
    t = re.sub(r"(?<![A-Za-zÀ-ÿÄÖÜäöüß0-9])[\-–—]?\s*[\"„“”‟＂]{1,4}\s*[\-–—]?(?![A-Za-zÀ-ÿÄÖÜäöüß0-9])", " ", t)
    t = re.sub(r"(?<![A-Za-zÀ-ÿÄÖÜäöüß0-9])[']{2,4}(?![A-Za-zÀ-ÿÄÖÜäöüß0-9])", " ", t)
    # Remove OCR-attached leading/trailing ditto quotes: "Beltzkey, Blatzen", Jahre'.
    t = re.sub(r"(?<![A-Za-zÀ-ÿÄÖÜäöüß0-9])[\"„“”‟＂']+(?=[A-Za-zÀ-ÿÄÖÜäöüß0-9])", "", t)
    t = re.sub(r"(?<=[A-Za-zÀ-ÿÄÖÜäöüß0-9])[\"„“”‟＂']+(?![A-Za-zÀ-ÿÄÖÜäöüß0-9])", "", t)
    # Drop any remaining double-quote style marks.  Single apostrophes are only
    # handled above so normal text is not aggressively damaged.
    t = t.translate(str.maketrans('', '', _BK_FIX56_DITTO_CHARS))
    # Remove empty parentheses left by a pure ditto marker.
    t = re.sub(r"\(\s*\)", " ", t)
    t = re.sub(r"\s+([.,;:])", r"\1", t)
    t = re.sub(r"(\()\s+", r"\1", t)
    t = re.sub(r"\s{2,}", " ", t)
    t = re.sub(r"\n\s+", "\n", t)
    t = re.sub(r"\s+\n", "\n", t)
    return t.strip()

try:
    _BK_FIX56_PREV_CLEAN_TEXT_VALUE = _bk_fix51_clean_text_value
except Exception:
    _BK_FIX56_PREV_CLEAN_TEXT_VALUE = None

def _bk_fix56_clean_text_value(value) -> str:
    if callable(_BK_FIX56_PREV_CLEAN_TEXT_VALUE):
        base = _BK_FIX56_PREV_CLEAN_TEXT_VALUE(value)
    else:
        base = _clean_ocr_text(value or '')
    return _bk_fix56_strip_ditto_marks(base)

try:
    _BK_FIX56_PREV_NORM_SPACE = _bk_fix50_norm_space
except Exception:
    _BK_FIX56_PREV_NORM_SPACE = None

def _bk_fix56_norm_space(text: str) -> str:
    if callable(_BK_FIX56_PREV_NORM_SPACE):
        base = _BK_FIX56_PREV_NORM_SPACE(text)
    else:
        base = _clean_ocr_text(text or '')
    return re.sub(r"\s+", " ", _bk_fix56_strip_ditto_marks(base)).strip()

_bk_fix51_clean_text_value = _bk_fix56_clean_text_value
_bk_fix50_norm_space = _bk_fix56_norm_space

def _bk_fix56_delete_ditto_marks_in_lines(lines: List[str]) -> List[str]:
    return [_bk_fix56_norm_space(x) for x in (lines or [])]

def _bk_fix56_delete_ditto_marks_with_recs(recs, texts: List[str]) -> List[str]:
    return _bk_fix56_delete_ditto_marks_in_lines(texts)

def _bk_fix56_delete_ditto_marks_in_recs(recs):
    try:
        for rv in list(recs or []):
            try:
                rv.text = _bk_fix56_norm_space(getattr(rv, 'text', '') or '')
            except Exception:
                pass
    except Exception:
        pass
    return recs

# Override every historical ditto resolver name that later code may call.  All
# of them now strip marks only; none copies a value from previous rows/columns.
_bk_fix43_resolve_line_ditto_from_prev = lambda prev_line, cur_line: _bk_fix56_norm_space(cur_line)
_bk_fix42_resolve_line_ditto_from_prev = _bk_fix43_resolve_line_ditto_from_prev
_bk_fix43_resolve_ditto_marks_with_recs = _bk_fix56_delete_ditto_marks_with_recs
_bk_fix42_resolve_ditto_marks_with_recs = _bk_fix56_delete_ditto_marks_with_recs
_bk_fix43_resolve_ditto_marks_in_lines = _bk_fix56_delete_ditto_marks_in_lines
_bk_fix41_resolve_ditto_marks_in_lines = _bk_fix56_delete_ditto_marks_in_lines
_bk_fix40_resolve_ditto_marks_in_lines = _bk_fix56_delete_ditto_marks_in_lines
_bk_fix38_resolve_ditto_marks_in_lines = _bk_fix56_delete_ditto_marks_in_lines
_bk_fix37_resolve_ditto_marks_in_lines = _bk_fix56_delete_ditto_marks_in_lines
_bk_fix36_resolve_ditto_marks_in_lines = _bk_fix56_delete_ditto_marks_in_lines
_bk_fix43_resolve_ditto_marks_in_recs = _bk_fix56_delete_ditto_marks_in_recs
_bk_fix42_resolve_ditto_marks_in_recs = _bk_fix56_delete_ditto_marks_in_recs
_bk_fix41_resolve_ditto_marks_in_recs = _bk_fix56_delete_ditto_marks_in_recs
_bk_fix40_resolve_ditto_marks_in_recs = _bk_fix56_delete_ditto_marks_in_recs
_bk_fix38_resolve_ditto_marks_in_recs = _bk_fix56_delete_ditto_marks_in_recs
_bk_fix37_resolve_ditto_marks_in_recs = _bk_fix56_delete_ditto_marks_in_recs
_bk_fix36_resolve_ditto_marks_in_recs = _bk_fix56_delete_ditto_marks_in_recs
_bk_fix37_expand_ditto_text = lambda text: "\n".join(_bk_fix56_delete_ditto_marks_in_lines(str(text or '').splitlines()))
_bk_fix38_expand_ditto_text = _bk_fix37_expand_ditto_text

try:
    MainWindow.bk_resolve_ditto_marks_in_recs = lambda self, recs: _bk_fix56_delete_ditto_marks_in_recs(recs)
except Exception:
    pass

def _bk_fix56_anchor_counter(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for tok in _bk_fix55_anchor_tokens(_bk_fix56_norm_space(text)):
        if tok in _BK_FIX56_STOP_TOKENS or len(tok) <= 1:
            continue
        counts[tok] = counts.get(tok, 0) + 1
    return counts

def _bk_fix56_same_person_anchor(reference: str, candidate: str) -> bool:
    ref_counts = _bk_fix56_anchor_counter(reference)
    cand_counts = _bk_fix56_anchor_counter(candidate)
    if not ref_counts or not cand_counts:
        return False
    ref_order = [tok for tok in _bk_fix55_anchor_tokens(reference) if tok in ref_counts]
    ref_order = list(dict.fromkeys(ref_order))
    if len(ref_order) >= 2:
        required = ref_order[:2]
    else:
        required = ref_order[:1]
    for tok in required:
        if cand_counts.get(tok, 0) <= 0:
            return False
    # If a token is repeated in the Kraken line, it is usually part of a parent
    # context, e.g. "Ducke Andreas (S.d.Andreas)".  A candidate with only the
    # plain name "Ducke Andreas" must not steal this row.
    for tok, count in ref_counts.items():
        if count >= 2 and cand_counts.get(tok, 0) < 2:
            return False
    return True

def _bk_fix56_conflicts_repeated_context(reference: str, candidate: str) -> bool:
    ref_counts = _bk_fix56_anchor_counter(reference)
    cand_counts = _bk_fix56_anchor_counter(candidate)
    for tok, count in ref_counts.items():
        if count >= 2 and cand_counts.get(tok, 0) < 2:
            return True
    return False

def _bk_fix56_age_pairs(text: str) -> list[tuple[str, str]]:
    try:
        return _bk_fix53_age_pairs(text)
    except Exception:
        try:
            return _bk_fix52_age_pairs(text)
        except Exception:
            return []

def _bk_fix56_has_exact_age_pair(reference: str, candidate: str) -> bool:
    ref_pairs = set(_bk_fix56_age_pairs(reference))
    cand_pairs = set(_bk_fix56_age_pairs(candidate))
    return bool(ref_pairs and cand_pairs and (ref_pairs & cand_pairs))

def _bk_fix56_age_units_compatible(reference: str, candidate: str) -> bool:
    ref_units = {unit for _num, unit in _bk_fix56_age_pairs(reference)}
    cand_units = {unit for _num, unit in _bk_fix56_age_pairs(candidate)}
    if ref_units and cand_units:
        return bool(ref_units & cand_units)
    return True

def _bk_fix56_table_tail_score(text: str, reference: str = '') -> float:
    cand = _bk_fix56_norm_space(text)
    ref = _bk_fix56_norm_space(reference)
    if not cand:
        return 0.0
    score = 0.0
    if re.search(r"\b\d{1,2}\s*[./]\s*(?:[ivxlcdmIVXLCDM]{1,8}|\d{1,2})\s*[./]?", cand):
        score += 42.0
    if re.search(r"\b(?:1[5-9]\d{2}|20\d{2})\b", cand):
        score += 22.0
    extra_numbers = _bk_fix49_number_set(cand) - _bk_fix49_number_set(ref)
    score += min(30.0, len(extra_numbers) * 10.0)
    if re.search(r"\b[A-ZÄÖÜ][A-Za-zÀ-ÿÄÖÜäöüß]{3,}\b", cand):
        score += 6.0
    return score

try:
    _BK_FIX56_PREV_RICH_TABLE_TAIL = _bk_fix53_has_rich_table_tail
except Exception:
    _BK_FIX56_PREV_RICH_TABLE_TAIL = None

def _bk_fix56_has_rich_table_tail(text: str) -> bool:
    if callable(_BK_FIX56_PREV_RICH_TABLE_TAIL):
        try:
            if _BK_FIX56_PREV_RICH_TABLE_TAIL(text):
                return True
        except Exception:
            pass
    return _bk_fix56_table_tail_score(text) >= 38.0

_bk_fix53_has_rich_table_tail = _bk_fix56_has_rich_table_tail

try:
    _BK_FIX56_PREV_IS_RICH_COMPLETION = _bk_fix55_is_rich_completion
except Exception:
    _BK_FIX56_PREV_IS_RICH_COMPLETION = None

def _bk_fix56_is_rich_completion(worker, reference: str, candidate: str) -> bool:
    ref = _bk_fix56_norm_space(reference)
    cand = _bk_fix56_norm_space(candidate)
    if not ref or not cand or ref == cand:
        return False
    try:
        if _bk_fix50_is_bad_line_candidate(worker, cand, ref):
            return False
    except Exception:
        pass
    # Stricter than the previous guards: repeated name/context tokens from Kraken
    # must also be repeated in the candidate.  This prevents another same-name
    # person from stealing the row.
    if not _bk_fix56_same_person_anchor(ref, cand):
        return False
    if not _bk_fix56_age_units_compatible(ref, cand):
        return False
    stable_missing = _bk_fix55_stable_numbers(ref) - _bk_fix49_number_set(cand)
    if stable_missing:
        return False
    if _bk_fix49_info_len(cand) < max(_bk_fix49_info_len(ref) + 5, int(_bk_fix49_info_len(ref) * 1.08)):
        return False
    if _bk_fix56_table_tail_score(cand, ref) < 38.0:
        return False
    return True

_bk_fix55_is_rich_completion = _bk_fix56_is_rich_completion

try:
    _BK_FIX56_PREV_FIND_PAGE_LINE_CANDIDATE = _bk_fix50_find_page_line_candidate
except Exception:
    _BK_FIX56_PREV_FIND_PAGE_LINE_CANDIDATE = None

def _bk_fix56_page_candidate_score(worker, reference: str, candidate: str, line_index: int, preferred_indices: List[int]) -> float:
    ref = _bk_fix56_norm_space(reference)
    cand = _bk_fix56_norm_space(candidate)
    if not _bk_fix56_is_rich_completion(worker, ref, cand):
        return float('-inf')
    ref_counts = _bk_fix56_anchor_counter(ref)
    cand_counts = _bk_fix56_anchor_counter(cand)
    shared = sum(min(ref_counts.get(tok, 0), cand_counts.get(tok, 0)) for tok in ref_counts)
    sim = _bk_fix49_similarity(worker, ref, cand)
    exact_age_bonus = 34.0 if _bk_fix56_has_exact_age_pair(ref, cand) else 0.0
    info_gain = max(0, _bk_fix49_info_len(cand) - _bk_fix49_info_len(ref))
    distance = 0
    if preferred_indices:
        distance = min(abs(int(line_index) - int(idx)) for idx in preferred_indices if isinstance(idx, int))
    return (
        150.0
        + shared * 42.0
        + exact_age_bonus
        + _bk_fix56_table_tail_score(cand, ref)
        + min(80.0, info_gain * 1.4)
        + sim * 40.0
        - min(50.0, distance * 0.8)
    )

def _bk_fix56_find_page_line_candidate(worker, rv, kraken_text: str, page_lines: List[str], local_pos: int = 0) -> str:
    ref = _bk_fix56_norm_space(kraken_text)
    lines = [_bk_fix56_norm_space(x) for x in (page_lines or [])]
    lines = [x for x in lines if x and not _bk_fix49_is_json_debris(x)]
    if not lines:
        return ''

    previous = ''
    if callable(_BK_FIX56_PREV_FIND_PAGE_LINE_CANDIDATE):
        try:
            previous = _bk_fix56_norm_space(_BK_FIX56_PREV_FIND_PAGE_LINE_CANDIDATE(worker, rv, ref, lines, local_pos))
        except Exception:
            previous = ''
    if previous and _bk_fix56_is_rich_completion(worker, ref, previous):
        return previous

    preferred: List[int] = []
    try:
        preferred.append(int(getattr(rv, 'idx', local_pos)))
    except Exception:
        pass
    try:
        lp = int(local_pos or 0)
        if lp not in preferred:
            preferred.append(lp)
    except Exception:
        pass

    best_score = float('-inf')
    best_line = ''
    for j, cand in enumerate(lines):
        score = _bk_fix56_page_candidate_score(worker, ref, cand, j, preferred)
        if score > best_score:
            best_score = score
            best_line = cand

    if best_line:
        try:
            print(
                'FIX8.56 PAGE CANDIDATE:',
                f'local={local_pos}',
                f'global={getattr(rv, "idx", local_pos)}',
                'kraken=', repr(ref),
                'page=', repr(best_line),
                f'score={best_score:.1f}',
            )
        except Exception:
            pass
        return best_line
    return previous or ''

_bk_fix50_find_page_line_candidate = _bk_fix56_find_page_line_candidate
_bk_fix55_find_page_line_candidate = _bk_fix56_find_page_line_candidate

try:
    _BK_FIX56_PREV_PICK_RICH_CANDIDATE = _bk_fix55_pick_rich_candidate
except Exception:
    _BK_FIX56_PREV_PICK_RICH_CANDIDATE = None

def _bk_fix56_pick_rich_candidate(worker, kraken_text: str, *candidate_texts: str) -> str:
    best = ''
    if callable(_BK_FIX56_PREV_PICK_RICH_CANDIDATE):
        try:
            previous = _bk_fix56_norm_space(_BK_FIX56_PREV_PICK_RICH_CANDIDATE(worker, kraken_text, *candidate_texts))
            if previous and _bk_fix56_is_rich_completion(worker, kraken_text, previous):
                best = previous
        except Exception:
            best = ''
    for candidate in candidate_texts:
        cand = _bk_fix56_norm_space(candidate)
        if cand and _bk_fix56_is_rich_completion(worker, kraken_text, cand):
            if not best or _bk_fix56_page_candidate_score(worker, kraken_text, cand, 0, [0]) > _bk_fix56_page_candidate_score(worker, kraken_text, best, 0, [0]):
                best = cand
    return best

_bk_fix55_pick_rich_candidate = _bk_fix56_pick_rich_candidate
_bk_fix54_pick_rich_candidate = _bk_fix56_pick_rich_candidate

try:
    _BK_FIX56_PREV_SANITY_MERGE_LINE = _bk_fix55_sanity_merge_line
except Exception:
    _BK_FIX56_PREV_SANITY_MERGE_LINE = None

def _bk_fix56_sanity_merge_line(worker, kraken_text: str, lm_box_text: str, page_line_text: str = '', prev_final_text: str = '', full_page_context: str = '', page_index_aligned: bool = True) -> str:
    raw_lm_box = str(lm_box_text or '')
    raw_page_line = str(page_line_text or '')
    kt = _bk_fix56_norm_space(kraken_text)
    lt = '' if '\n' in raw_lm_box else _bk_fix56_norm_space(lm_box_text)
    pt = '' if '\n' in raw_page_line else _bk_fix56_norm_space(page_line_text)
    forced = _bk_fix56_pick_rich_candidate(worker, kt, lt, pt)
    if forced:
        return forced
    if callable(_BK_FIX56_PREV_SANITY_MERGE_LINE):
        best = _BK_FIX56_PREV_SANITY_MERGE_LINE(worker, kt, lt, pt, prev_final_text, full_page_context, page_index_aligned)
    else:
        best = kt or lt or pt
    best = _bk_fix56_norm_space(best)
    # Rich table completions are only allowed for the same historical person/row.
    # The older fallback merge could otherwise accept a full but unrelated line
    # just because age unit/date/year/place made it look more complete.  Keep
    # short spelling corrections tolerant, but reject rich replacements with no
    # matching name/context anchor.
    if best and best != kt:
        try:
            rich_replacement = _bk_fix56_table_tail_score(best, kt) >= 38.0 or _bk_fix56_has_rich_table_tail(best)
        except Exception:
            rich_replacement = False
        try:
            has_reference_anchor = bool(_bk_fix56_anchor_counter(kt))
        except Exception:
            has_reference_anchor = False
        if rich_replacement and has_reference_anchor and not _bk_fix56_same_person_anchor(kt, best):
            return kt
    # If the normal path picked a candidate that drops a repeated parent/name
    # context from Kraken, keep Kraken.
    if best and best != kt and _bk_fix56_conflicts_repeated_context(kt, best):
        return kt
    if best == kt:
        forced = _bk_fix56_pick_rich_candidate(worker, kt, lt, pt)
        if forced:
            return forced
    return best
