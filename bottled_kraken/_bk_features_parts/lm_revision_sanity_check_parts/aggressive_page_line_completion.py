# --- FIX8.55: high-recall page-line completion for under-revised rows -------
# Many historical table rows share a short Kraken prefix with a much richer LM
# full-page row.  Earlier fixes only looked near the nominal row index; this
# part scans the full page for the best same-person/table-row candidate and lets
# that candidate win when it clearly adds the missing right-hand columns.

_BK_FIX55_STOP_TOKENS = {
    "jahr", "jahre", "jahren", "monat", "monate", "monaten", "woche", "wochen",
    "tag", "tage", "tagen", "stunde", "stunden", "seite", "unter", "weiterzusuchen",
    "weib", "wittwe", "witwe", "wwe", "wwte", "td", "sd", "s", "d", "n", "j",
}

def _bk_fix55_anchor_tokens(text: str) -> List[str]:
    tokens: List[str] = []
    for tok in _bk_fix49_tokens(text):
        if tok.isdigit() or len(tok) <= 1:
            continue
        if tok in _BK_FIX55_STOP_TOKENS:
            continue
        if re.fullmatch(r"[ivxlcdm]+", tok):
            continue
        tokens.append(tok)
    return tokens

def _bk_fix55_leading_person_tokens(text: str) -> List[str]:
    tokens = _bk_fix55_anchor_tokens(text)
    return tokens[:3]

def _bk_fix55_age_units(text: str) -> set:
    units = set()
    try:
        for _num, unit in _bk_fix53_age_pairs(text):
            units.add(unit)
    except Exception:
        try:
            for _num, unit in _bk_fix52_age_pairs(text):
                units.add(unit)
        except Exception:
            pass
    return units

def _bk_fix55_stable_numbers(text: str) -> set:
    try:
        return _bk_fix53_stable_numbers(text)
    except Exception:
        try:
            ref_age_nums = {num for num, _unit in _bk_fix52_age_pairs(text)}
            return _bk_fix49_number_set(text) - ref_age_nums
        except Exception:
            return _bk_fix49_number_set(text)

def _bk_fix55_has_same_person_anchor(reference: str, candidate: str) -> bool:
    ref = _bk_fix50_norm_space(reference)
    cand = _bk_fix50_norm_space(candidate)
    ref_lead = _bk_fix55_leading_person_tokens(ref)
    cand_tokens = set(_bk_fix55_anchor_tokens(cand))
    if len(ref_lead) >= 2:
        return ref_lead[0] in cand_tokens and ref_lead[1] in cand_tokens
    if ref_lead:
        return ref_lead[0] in cand_tokens
    return False

def _bk_fix55_is_rich_completion(worker, reference: str, candidate: str) -> bool:
    ref = _bk_fix50_norm_space(reference)
    cand = _bk_fix50_norm_space(candidate)
    if not ref or not cand or ref == cand:
        return False
    if _bk_fix50_is_bad_line_candidate(worker, cand, ref):
        return False
    if not _bk_fix55_has_same_person_anchor(ref, cand):
        return False

    ref_units = _bk_fix55_age_units(ref)
    cand_units = _bk_fix55_age_units(cand)
    if ref_units and cand_units and not (ref_units & cand_units):
        return False

    # Stable Kraken numbers must still be preserved.  Age numbers may differ
    # when the candidate has the same age unit and adds table-tail evidence.
    stable_missing = _bk_fix55_stable_numbers(ref) - _bk_fix49_number_set(cand)
    if stable_missing:
        return False

    ref_info = max(1, _bk_fix49_info_len(ref))
    cand_info = _bk_fix49_info_len(cand)
    if cand_info < ref_info + 8 and cand_info < int(ref_info * 1.22):
        return False
    if len(_bk_fix49_number_set(cand)) <= len(_bk_fix49_number_set(ref)):
        return False
    try:
        if not _bk_fix53_has_rich_table_tail(cand):
            return False
    except Exception:
        if not _bk_fix50_contains_table_completion(cand):
            return False
    return True

def _bk_fix55_global_page_line_score(worker, reference: str, candidate: str, local_pos: int, line_index: int, preferred_indices: List[int]) -> float:
    if not _bk_fix55_is_rich_completion(worker, reference, candidate):
        return float("-inf")
    ref = _bk_fix50_norm_space(reference)
    cand = _bk_fix50_norm_space(candidate)
    ref_tokens = set(_bk_fix55_anchor_tokens(ref))
    cand_tokens = set(_bk_fix55_anchor_tokens(cand))
    shared = len(ref_tokens & cand_tokens)
    sim = _bk_fix49_similarity(worker, ref, cand)
    extra_info = max(0, _bk_fix49_info_len(cand) - _bk_fix49_info_len(ref))
    extra_nums = max(0, len(_bk_fix49_number_set(cand)) - len(_bk_fix49_number_set(ref)))
    distance = 0
    if preferred_indices:
        distance = min(abs(line_index - idx) for idx in preferred_indices if isinstance(idx, int))
    else:
        distance = abs(line_index - int(local_pos or 0))
    return 120.0 + shared * 32.0 + sim * 60.0 + min(90.0, extra_info * 1.5) + extra_nums * 10.0 - min(45.0, distance * 1.2)

_BK_FIX55_PREV_FIND_PAGE_LINE_CANDIDATE = _bk_fix50_find_page_line_candidate

def _bk_fix55_find_page_line_candidate(worker, rv, kraken_text: str, page_lines: List[str], local_pos: int = 0) -> str:
    ref = _bk_fix50_norm_space(kraken_text)
    lines = [_bk_fix50_norm_space(x) for x in (page_lines or [])]
    lines = [x for x in lines if x and not _bk_fix49_is_json_debris(x)]
    if not lines:
        return ""

    previous = ""
    try:
        previous = _BK_FIX55_PREV_FIND_PAGE_LINE_CANDIDATE(worker, rv, ref, lines, local_pos)
    except Exception:
        previous = ""
    if previous and _bk_fix55_is_rich_completion(worker, ref, previous):
        return previous

    preferred: List[int] = []
    try:
        preferred.append(int(getattr(rv, "idx", local_pos)))
    except Exception:
        pass
    try:
        lp = int(local_pos or 0)
        if lp not in preferred:
            preferred.append(lp)
    except Exception:
        pass

    best_score = float("-inf")
    best_line = ""
    for j, cand in enumerate(lines):
        score = _bk_fix55_global_page_line_score(worker, ref, cand, local_pos, j, preferred)
        if score > best_score:
            best_score = score
            best_line = cand

    if best_line:
        try:
            print(
                "FIX8.55 PAGE CANDIDATE:",
                f"local={local_pos}",
                f"global={getattr(rv, 'idx', local_pos)}",
                "kraken=", repr(ref),
                "page=", repr(best_line),
                f"score={best_score:.1f}",
            )
        except Exception:
            pass
        return best_line
    return previous or ""

_bk_fix50_find_page_line_candidate = _bk_fix55_find_page_line_candidate

_BK_FIX55_PREV_PICK_RICH_CANDIDATE = _bk_fix54_pick_rich_candidate

def _bk_fix55_pick_rich_candidate(worker, kraken_text: str, *candidate_texts: str) -> str:
    picked = ""
    try:
        picked = _BK_FIX55_PREV_PICK_RICH_CANDIDATE(worker, kraken_text, *candidate_texts)
    except Exception:
        picked = ""
    best = _bk_fix50_norm_space(picked)
    for candidate in candidate_texts:
        cand = _bk_fix50_norm_space(candidate)
        if not cand:
            continue
        if _bk_fix55_is_rich_completion(worker, kraken_text, cand):
            if not best or _bk_fix49_info_len(cand) > _bk_fix49_info_len(best):
                best = cand
    return best

_bk_fix54_pick_rich_candidate = _bk_fix55_pick_rich_candidate

_BK_FIX55_PREV_SANITY_MERGE_LINE = _bk_fix54_sanity_merge_line

def _bk_fix55_sanity_merge_line(worker, kraken_text: str, lm_box_text: str, page_line_text: str = "", prev_final_text: str = "", full_page_context: str = "", page_index_aligned: bool = True) -> str:
    forced = _bk_fix55_pick_rich_candidate(worker, kraken_text, lm_box_text, page_line_text)
    if forced:
        return forced
    best = _BK_FIX55_PREV_SANITY_MERGE_LINE(
        worker,
        kraken_text,
        lm_box_text,
        page_line_text,
        prev_final_text,
        full_page_context,
        page_index_aligned,
    )
    # Last chance: if the normal scorer stayed on Kraken while one LM source is
    # an obvious same-person completion, take the completion.
    if _bk_fix50_norm_space(best) == _bk_fix50_norm_space(kraken_text):
        forced = _bk_fix55_pick_rich_candidate(worker, kraken_text, lm_box_text, page_line_text)
        if forced:
            return forced
    return _bk_fix50_norm_space(best)

_bk_fix55_merge_candidates = lambda worker, kraken_text, page_text, box_text, prev_final_text='': _bk_fix55_sanity_merge_line(worker, kraken_text, box_text, page_text, prev_final_text, page_text, True)
_bk_fix54_sanity_merge_line = _bk_fix55_sanity_merge_line
_bk_fix53_sanity_merge_line = _bk_fix55_sanity_merge_line
_bk_fix50_sanity_merge_line = _bk_fix55_sanity_merge_line
_bk_fix49_sanity_merge_line = _bk_fix55_sanity_merge_line
_bk_fix46_sanity_merge_line = _bk_fix55_sanity_merge_line
_bk_fix50_merge_candidates = _bk_fix55_merge_candidates
_bk_fix49_merge_candidates = _bk_fix55_merge_candidates
_bk_fix45_merge_candidates = _bk_fix55_merge_candidates
_bk_fix43_choose_final_kraken_first = _bk_fix55_merge_candidates
_bk_fix41_choose_final_kraken_first = _bk_fix55_merge_candidates

try:
    AIRevisionWorker._choose_final_line_text = lambda self, kraken_text, box_text, page_text, prev_final_text='': _bk_fix55_sanity_merge_line(self, kraken_text, box_text, page_text, prev_final_text, page_text, True)
    AIRevisionWorker._request_line_decision = lambda self, idx, kraken_text, page_text, box_text: _bk_fix55_sanity_merge_line(self, kraken_text, box_text, page_text, '', page_text, True)
except Exception:
    pass

_BK_FIX55_PREV_OVERLAY_BOX_REVISION = _bk_fix50_request_overlay_box_revision

def _bk_fix55_request_overlay_box_revision(self, rv, page_context_lines: List[str], local_pos: int, total: int) -> str:
    kraken_text = _bk_fix50_norm_space(getattr(rv, "text", "") or "")
    page_line_candidate = _bk_fix55_find_page_line_candidate(self, rv, kraken_text, page_context_lines, local_pos)
    text = ""
    try:
        text = _BK_FIX55_PREV_OVERLAY_BOX_REVISION(self, rv, page_context_lines, local_pos, total)
    except Exception:
        text = ""
    forced = _bk_fix55_pick_rich_candidate(self, kraken_text, text, page_line_candidate)
    if forced:
        return forced
    return _bk_fix50_norm_space(text) or page_line_candidate or kraken_text

_bk_fix50_request_overlay_box_revision = _bk_fix55_request_overlay_box_revision
_bk_fix46_request_overlay_box_revision = _bk_fix55_request_overlay_box_revision
