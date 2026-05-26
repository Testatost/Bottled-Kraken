# Final LM revision merge modes and strict overlay overrides.
# Standalone-Test-Fallback: Einige Tests führen genau diese Datei einzeln aus,
# ohne vorher das Ditto-Guard-Part zu laden. Im normalen Split-Loader-Pfad sind diese
# Namen bereits durch ditto_guard.py vorhanden.
if '_bk_fix56_norm_space' not in globals():
    def _bk_fix56_norm_space(text: str) -> str:
        return re.sub(r"\s+", " ", _bk_fix56_strip_ditto_marks(text)).strip()

if '_bk_fix56_sanity_merge_line' not in globals():
    def _bk_fix56_sanity_merge_line(worker, kraken_text: str, lm_box_text: str, page_line_text: str = '', prev_final_text: str = '', full_page_context: str = '', page_index_aligned: bool = True) -> str:
        try:
            return _bk_fix54_sanity_merge_line(worker, kraken_text, lm_box_text, page_line_text, prev_final_text, full_page_context, page_index_aligned)
        except Exception:
            return _bk_fix56_norm_space(lm_box_text or kraken_text or page_line_text or '')

if '_bk_fix56_find_page_line_candidate' not in globals():
    def _bk_fix56_find_page_line_candidate(worker, rv, kraken_text: str, page_lines: List[str], local_pos: int = 0) -> str:
        try:
            return _bk_fix50_find_page_line_candidate(worker, rv, kraken_text, page_lines, local_pos)
        except Exception:
            return ''

if '_bk_fix56_pick_rich_candidate' not in globals():
    def _bk_fix56_pick_rich_candidate(worker, kraken_text: str, *candidate_texts: str) -> str:
        try:
            return _bk_fix54_pick_rich_candidate(worker, kraken_text, *candidate_texts)
        except Exception:
            return ''

# Der umfangreiche Hilfscode liegt in ditto_guard.py.
# Diese Datei bleibt bewusst der letzte LM-Sanity-Part.

try:
    _BK_FIX56_CORE_STRIP_DITTO_MARKS = _bk_fix56_strip_ditto_marks
except Exception:
    _BK_FIX56_CORE_STRIP_DITTO_MARKS = None

def _bk_fix56_strip_ditto_marks(text: str) -> str:
    if callable(_BK_FIX56_CORE_STRIP_DITTO_MARKS):
        return _BK_FIX56_CORE_STRIP_DITTO_MARKS(text)
    raw = '' if text is None else str(text)
    if not raw:
        return ''
    t = raw.replace('\r\n', '\n').replace('\r', '\n')
    t = re.sub(r"\(\s*[-–—]?\s*[\"„“”‟＂']{1,4}\s*[-–—]?\s*\)", " ", t)
    t = re.sub(r"(?<![A-Za-zÀ-ÿÄÖÜäöüß0-9])[\-–—]?\s*[\"„“”‟＂]{1,4}\s*[\-–—]?(?![A-Za-zÀ-ÿÄÖÜäöüß0-9])", " ", t)
    t = re.sub(r"(?<![A-Za-zÀ-ÿÄÖÜäöüß0-9])[']{2,4}(?![A-Za-zÀ-ÿÄÖÜäöüß0-9])", " ", t)
    t = re.sub(r"(?<![A-Za-zÀ-ÿÄÖÜäöüß0-9])[\"„“”‟＂']+(?=[A-Za-zÀ-ÿÄÖÜäöüß0-9])", "", t)
    t = re.sub(r"(?<=[A-Za-zÀ-ÿÄÖÜäöüß0-9])[\"„“”‟＂']+(?![A-Za-zÀ-ÿÄÖÜäöüß0-9])", "", t)
    t = t.translate(str.maketrans('', '', '"„“”‟＂'))
    t = re.sub(r"\(\s*\)", " ", t)
    t = re.sub(r"\s+([.,;:])", r"\1", t)
    t = re.sub(r"(\()\s+", r"\1", t)
    t = re.sub(r"\s{2,}", " ", t)
    t = re.sub(r"\n\s+", "\n", t)
    t = re.sub(r"\s+\n", "\n", t)
    return t.strip()

try:
    _BK_FIX56_CORE_DELETE_LINES = _bk_fix56_delete_ditto_marks_in_lines
except Exception:
    _BK_FIX56_CORE_DELETE_LINES = None

def _bk_fix56_delete_ditto_marks_in_lines(lines: List[str]) -> List[str]:
    if callable(_BK_FIX56_CORE_DELETE_LINES):
        return _BK_FIX56_CORE_DELETE_LINES(lines)
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

try:
    _BK_FIX56_PREV_OVERLAY_BOX_REVISION = _bk_fix50_request_overlay_box_revision
except Exception:
    _BK_FIX56_PREV_OVERLAY_BOX_REVISION = None

def _bk_fix56_request_overlay_box_revision(self, rv, page_context_lines: List[str], local_pos: int, total: int) -> str:
    kraken_text = _bk_fix56_norm_space(getattr(rv, 'text', '') or '')
    page_line_candidate = _bk_fix56_find_page_line_candidate(self, rv, kraken_text, page_context_lines, local_pos)
    text = ''
    if callable(_BK_FIX56_PREV_OVERLAY_BOX_REVISION):
        try:
            text = _BK_FIX56_PREV_OVERLAY_BOX_REVISION(self, rv, page_context_lines, local_pos, total)
        except Exception:
            text = ''
    text = _bk_fix56_norm_space(text)
    forced = _bk_fix56_pick_rich_candidate(self, kraken_text, text, page_line_candidate)
    if forced:
        return forced
    return text or page_line_candidate or kraken_text

_BK_FIX57_PREV_OVERLAY_BOX_REVISION = _bk_fix56_request_overlay_box_revision

def _bk_fix57_request_strict_print_overlay_box_revision(self, rv, page_context_lines: List[str], local_pos: int, total: int) -> str:
    line_data_url = _crop_single_line_to_data_url(self.path, rv, pad_x=0, pad_y=0, extra_context_y=0)
    kraken_text = _bk_fix56_norm_space(getattr(rv, 'text', '') or '')
    system_prompt = self._tr('ai_prompt_overlay_compare_system')
    try:
        user_prompt = _bk_lm_opt_text(self, 'lm_behavior_overlay_prompt', int(getattr(rv, 'idx', local_pos)), kraken_text, '')
    except Exception:
        user_prompt = self._tr('ai_prompt_overlay_compare_user', int(getattr(rv, 'idx', local_pos)), kraken_text, '')
    payload = {
        'model': self.lm_model,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': [
                {'type': 'text', 'text': user_prompt},
                {'type': 'image_url', 'image_url': {'url': line_data_url}},
            ]},
        ],
        **self._build_sampling_payload(
            response_format=self._response_format_single_text(),
            override_max_tokens=max(360, min(max(900, int(getattr(self, 'max_tokens', 1200) or 1200)), 1800)),
        ),
    }
    data = self._post_json(payload)
    content = self._extract_message_content(data)
    try:
        print('RAW FIX8.57 STRICT PRINT OVERLAY LINE RESPONSE:')
        print(content[:2500])
    except Exception:
        pass
    text = _bk_fix56_norm_space(_bk_fix46_parse_single_text(content))
    if _bk_fix49_is_json_debris(text) or '\n' in str(text or ''):
        text = ''
    return text or kraken_text

def _bk_fix57_request_overlay_box_revision(self, rv, page_context_lines: List[str], local_pos: int, total: int) -> str:
    try:
        if _bk_fix57_is_print_script_mode(getattr(self, 'script_mode', AI_SCRIPT_PRINT)):
            return _bk_fix57_request_strict_print_overlay_box_revision(self, rv, page_context_lines, local_pos, total)
    except Exception:
        pass
    if callable(_BK_FIX57_PREV_OVERLAY_BOX_REVISION):
        return _BK_FIX57_PREV_OVERLAY_BOX_REVISION(self, rv, page_context_lines, local_pos, total)
    return _bk_fix56_norm_space(getattr(rv, 'text', '') or '')

_bk_fix50_request_overlay_box_revision = _bk_fix57_request_overlay_box_revision
_bk_fix46_request_overlay_box_revision = _bk_fix57_request_overlay_box_revision

def _bk_fix58_choose_strict_print_final_line(worker, kraken_text: str, lm_box_text: str) -> str:
    kt = _bk_fix56_norm_space(kraken_text)
    raw_box = str(lm_box_text or '')
    lt = '' if '\n' in raw_box else _bk_fix56_norm_space(lm_box_text)
    if not lt:
        return kt
    try:
        if _bk_fix50_is_bad_line_candidate(worker, lt, kt if kt else lt):
            return kt or lt
        if kt and not _bk_fix50_is_plausible_related(worker, kt, lt, index_aligned=False):
            return kt
        if kt and not _bk_fix50_numbers_compatible(kt, lt):
            return kt
        if kt and _bk_fix49_info_len(lt) < max(4, int(_bk_fix49_info_len(kt) * 0.78)):
            return kt
    except Exception:
        if kt and lt and lt != kt:
            return kt
    return lt or kt

try:
    _BK_FIX58_PREV_SANITY_MERGE_LINE = _bk_fix56_sanity_merge_line
except Exception:
    _BK_FIX58_PREV_SANITY_MERGE_LINE = None

def _bk_fix58_sanity_merge_line(worker, kraken_text: str, lm_box_text: str, page_line_text: str = '', prev_final_text: str = '', full_page_context: str = '', page_index_aligned: bool = True) -> str:
    try:
        if _bk_fix57_is_print_script_mode(getattr(worker, 'script_mode', AI_SCRIPT_PRINT)):
            return _bk_fix58_choose_strict_print_final_line(worker, kraken_text, lm_box_text)
    except Exception:
        pass
    if callable(_BK_FIX58_PREV_SANITY_MERGE_LINE):
        return _BK_FIX58_PREV_SANITY_MERGE_LINE(worker, kraken_text, lm_box_text, page_line_text, prev_final_text, full_page_context, page_index_aligned)
    return _bk_fix56_norm_space(lm_box_text or kraken_text or page_line_text or '')

_bk_fix56_sanity_merge_line = _bk_fix58_sanity_merge_line
_bk_fix56_merge_candidates = lambda worker, kraken_text, page_text, box_text, prev_final_text='': _bk_fix56_sanity_merge_line(worker, kraken_text, box_text, page_text, prev_final_text, page_text, True)
_bk_fix55_sanity_merge_line = _bk_fix56_sanity_merge_line
_bk_fix54_sanity_merge_line = _bk_fix56_sanity_merge_line
_bk_fix53_sanity_merge_line = _bk_fix56_sanity_merge_line
_bk_fix50_sanity_merge_line = _bk_fix56_sanity_merge_line
_bk_fix49_sanity_merge_line = _bk_fix56_sanity_merge_line
_bk_fix46_sanity_merge_line = _bk_fix56_sanity_merge_line
_bk_fix50_merge_candidates = _bk_fix56_merge_candidates
_bk_fix49_merge_candidates = _bk_fix56_merge_candidates
_bk_fix45_merge_candidates = _bk_fix56_merge_candidates
_bk_fix43_choose_final_kraken_first = _bk_fix56_merge_candidates
_bk_fix41_choose_final_kraken_first = _bk_fix56_merge_candidates

try:
    AIRevisionWorker._choose_final_line_text = lambda self, kraken_text, box_text, page_text, prev_final_text='': _bk_fix58_sanity_merge_line(self, kraken_text, box_text, page_text, prev_final_text, page_text, True)
    AIRevisionWorker._request_line_decision = lambda self, idx, kraken_text, page_text, box_text: _bk_fix58_sanity_merge_line(self, kraken_text, box_text, page_text, '', page_text, True)
except Exception:
    pass
