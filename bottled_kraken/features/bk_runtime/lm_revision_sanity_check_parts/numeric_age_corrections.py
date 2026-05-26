# --- FIX8.52: age-number corrections in rich LM line candidates -------------
# Kraken numbers remain protected, but an isolated age value may be corrected
# when the LM candidate is the same person/line and adds the missing table data.

_BK_FIX52_AGE_UNITS = {
    "jahr": "jahr", "jahre": "jahr", "jahren": "jahr",
    "monat": "monat", "monate": "monat", "monaten": "monat",
    "woche": "woche", "wochen": "woche",
    "tag": "tag", "tage": "tag", "tagen": "tag",
    "stunde": "stunde", "stunden": "stunde",
}
_BK_FIX52_AGE_RE = re.compile(
    r"\b(\d{1,3})\s*['’´`\.]?\s*"
    r"(Jahre?|Jahren|Monate?|Monaten|Wochen|Tage?|Tagen|Stunden?)\b",
    flags=re.IGNORECASE,
)

def _bk_fix52_age_pairs(text: str):
    pairs = []
    for match in _BK_FIX52_AGE_RE.finditer(str(text or "")):
        unit = _BK_FIX52_AGE_UNITS.get(match.group(2).casefold())
        if unit:
            pairs.append((match.group(1), unit))
    return pairs

def _bk_fix52_non_age_anchor_tokens(text: str) -> set:
    anchors = set()
    for tok in _bk_fix49_tokens(text):
        if tok.isdigit() or tok in _BK_FIX52_AGE_UNITS:
            continue
        if re.fullmatch(r"[ivxlcdm]+", tok):
            continue
        anchors.add(tok)
    return anchors

def _bk_fix52_all_missing_numbers_are_age_corrections(reference: str, candidate: str, missing: set) -> bool:
    if not missing or len(missing) > 2:
        return False
    ref_pairs = _bk_fix52_age_pairs(reference)
    cand_pairs = _bk_fix52_age_pairs(candidate)
    if not ref_pairs or not cand_pairs:
        return False
    ref_age_numbers = {num for num, _unit in ref_pairs}
    ref_stable_numbers = _bk_fix49_number_set(reference) - ref_age_numbers
    if ref_stable_numbers - _bk_fix49_number_set(candidate):
        return False
    shared_units = {unit for _num, unit in ref_pairs} & {unit for _num, unit in cand_pairs}
    if not shared_units:
        return False
    for num in missing:
        if not any(ref_num == num and unit in shared_units for ref_num, unit in ref_pairs):
            return False
    ref_anchors = _bk_fix52_non_age_anchor_tokens(reference)
    cand_anchors = _bk_fix52_non_age_anchor_tokens(candidate)
    required_overlap = 1 if len(ref_anchors) <= 1 else 2
    if len(ref_anchors & cand_anchors) < required_overlap:
        return False
    richer = _bk_fix49_info_len(candidate) >= int(max(1, _bk_fix49_info_len(reference)) * 1.15)
    more_numbers = len(_bk_fix49_number_set(candidate)) > len(_bk_fix49_number_set(reference))
    return richer and more_numbers and _bk_fix50_contains_table_completion(candidate)

def _bk_fix50_numbers_compatible(reference: str, candidate: str) -> bool:
    ref_nums = _bk_fix49_number_set(reference)
    if not ref_nums:
        return True
    cand_nums = _bk_fix49_number_set(candidate)
    missing = ref_nums - cand_nums
    if not missing:
        return True
    return _bk_fix52_all_missing_numbers_are_age_corrections(reference, candidate, missing)
