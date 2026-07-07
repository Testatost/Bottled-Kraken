from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
from bottled_kraken.common import _ai_script_crop_profile, _clean_ocr_text, _crop_single_line_to_data_url, _extract_json_payload, _extract_text_lines, _force_text, _page_to_data_url
from bottled_kraken.workers import AIRevisionRuntimeMixin
from bottled_kraken.common import List, RecordView, json, os, re, socket, traceback, urllib
from bottled_kraken.workers import AIRevisionWorker
from bottled_kraken.main_window import MainWindow
def _bk_fix46_context_excerpt_for_line(rv, page_lines: List[str], max_chars: int = 4200) -> str:
    lines = [str(x or '').strip() for x in (page_lines or []) if str(x or '').strip()]
    if not lines:
        return ''
    joined = '\n'.join(lines)
    if len(joined) <= max_chars:
        return joined
    needle = _clean_ocr_text(getattr(rv, 'text', '') or '')[:40]
    pos = joined.find(needle) if needle else -1
    if pos >= 0:
        start = max(0, pos - max_chars // 2)
        return joined[start:start + max_chars]
    return joined[:max_chars]
def _bk_fix46_parse_single_text(content: str) -> str:
    raw = str(content or '').strip()
    if not raw:
        return ''
    raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.IGNORECASE).strip()
    raw = re.sub(r'\s*```$', '', raw).strip()
    try:
        obj = json.loads(raw)
    except Exception:
        obj = _extract_json_payload(raw)
    if isinstance(obj, dict):
        for key in ('text', 'line', 'ocr_text', 'corrected_text', 'result'):
            val = obj.get(key)
            if isinstance(val, str):
                return _clean_ocr_text(val)
    lines = [_clean_ocr_text(x) for x in _extract_text_lines(raw)]
    lines = [x for x in lines if x and not _bk_fix41_is_json_debris_text(x)]
    if lines:
        return lines[0]
    return _clean_ocr_text(raw)

def _bk_fix49_is_manual_placeholder_text(text: str) -> bool:
    """Return True for deliberately typed filler/random text in manual overlay boxes.

    Such text must not protect the old line against a shorter visual LM result.
    Real OCR can legitimately be very short ("2", "3.", "U"), so this only
    flags longer, low-information artificial strings.
    """
    t = _clean_ocr_text(text or '')
    if not t:
        return False
    low = t.casefold()
    compact = re.sub(r"\s+", "", low)
    if re.search(r"\b(?:random|platzhalter|placeholder|testtext|dummy|lorem|asdf|qwerty)\b", low):
        return True
    if len(compact) >= 8 and re.fullmatch(r"[a-zäöüß]+", compact):
        # Typical manual gibberish has only a few different characters or repeated chunks.
        unique_ratio = len(set(compact)) / max(1, len(compact))
        vowels = sum(1 for ch in compact if ch in "aeiouäöüy")
        vowel_ratio = vowels / max(1, len(compact))
        repeated_chunks = bool(re.search(r"([a-zäöüß]{2,5})\1", compact))
        no_titlecase = not re.search(r"[A-ZÄÖÜ]", t)
        if no_titlecase and (unique_ratio <= 0.42 or repeated_chunks or vowel_ratio < 0.18):
            return True
    if len(compact) >= 10 and re.fullmatch(r"[a-z0-9._\-]+", compact) and not re.search(r"\s", t):
        # Long uninterrupted keyboard-like tokens are more likely placeholders than OCR lines.
        alpha = sum(1 for ch in compact if ch.isalpha())
        digit = sum(1 for ch in compact if ch.isdigit())
        if alpha >= 7 and digit <= 2 and len(set(compact)) <= max(5, int(len(compact) * 0.45)):
            return True
    return False


def _bk_fix49_is_usable_visual_text(text: str) -> bool:
    t = _clean_ocr_text(text or '')
    if not t:
        return False
    if t.startswith('{') or t.startswith('[') or 'bbox_norm' in t:
        return False
    if '\n' in t:
        return False
    # Valid OCR snippets can be extremely short: page numbers, column numbers,
    # roman numerals, separators, or one-letter headings.
    if re.fullmatch(r"[0-9IVXLCDMivxlcdmA-Za-zÄÖÜäöüß]{1,4}[.)]?", t):
        return True
    if len(t) <= 8 and re.search(r"[A-Za-zÀ-ÿÄÖÜäöüß0-9]", t):
        return True
    try:
        return not _bk_fix45_is_bad_candidate(None, t)
    except Exception:
        return True

def _bk_fix46_is_truncated_against(ref: str, cand: str) -> bool:
    ref = _clean_ocr_text(ref or '')
    cand = _clean_ocr_text(cand or '')
    if _bk_fix49_is_manual_placeholder_text(ref):
        return False
    if not ref:
        return False
    if not cand:
        return True
    if _bk_fix43_info_len(cand) < max(4, int(_bk_fix43_info_len(ref) * 0.68)):
        return True
    ref_nums = _bk_fix45_number_set(ref)
    cand_nums = _bk_fix45_number_set(cand)
    if ref_nums and len(ref_nums - cand_nums) >= max(1, int(len(ref_nums) * 0.45)):
        return True
    return False
def _bk_fix46_request_overlay_box_revision(self, rv, page_context_lines: List[str], local_pos: int, total: int) -> str:
    crop_profile = _ai_script_crop_profile(self.script_mode)
    line_data_url = _crop_single_line_to_data_url(
        self.path,
        rv,
        pad_x=max(18, int(crop_profile.get('single_pad_x', 18) or 18)),
        pad_y=max(8, int(crop_profile.get('single_pad_y', 8) or 8)),
        extra_context_y=max(0, int(crop_profile.get('single_extra_context_y', 0) or 0)),
    )
    kraken_text = _clean_ocr_text(getattr(rv, 'text', '') or '')
    page_context = _bk_fix46_context_excerpt_for_line(rv, page_context_lines)
    system_prompt = self._tr('ai_prompt_overlay_compare_system')
    user_prompt = self._tr('ai_prompt_overlay_compare_user', int(getattr(rv, 'idx', local_pos)), kraken_text, page_context)
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
            override_max_tokens=max(280, min(max(700, int(getattr(self, 'max_tokens', 1200) or 1200)), 1600)),
        ),
    }
    data = self._post_json(payload)
    content = self._extract_message_content(data)
    try:
        print('RAW FIX8.46 OVERLAY LINE RESPONSE:')
        print(content[:2500])
    except Exception:
        pass
    text = _bk_fix46_parse_single_text(content)
    text = _clean_ocr_text(text)
    if text and _bk_fix49_is_manual_placeholder_text(kraken_text):
        return text
    if _bk_fix46_is_truncated_against(kraken_text, text):
        return kraken_text
    return text or kraken_text
def _bk_fix46_sanity_merge_line(self, kraken_text: str, lm_box_text: str, page_context_text: str, prev_final_text: str = '') -> str:
    kt = _clean_ocr_text(kraken_text or '')
    lt = _clean_ocr_text(lm_box_text or '')
    pt = _clean_ocr_text(page_context_text or '')
    if lt and _bk_fix49_is_manual_placeholder_text(kt) and _bk_fix49_is_usable_visual_text(lt):
        return lt
    candidates = []
    for label, cand in (('lm_box', lt), ('kraken', kt)):
        if not cand or _bk_fix45_is_bad_candidate(self, cand):
            continue
        score = _bk_fix43_info_len(cand)
        other = kt if label == 'lm_box' else lt
        if other:
            score += 30.0 * (1.0 - _bk_fix45_missing_ratio(other, cand))
            missing_nums = _bk_fix45_number_set(other) - _bk_fix45_number_set(cand)
            score -= 20.0 * len(missing_nums)
        if pt:
            score += 6.0 * (1.0 - min(1.0, _bk_fix45_missing_ratio(pt[:220], cand)))
        if prev_final_text and self._normalize_compare_text(cand) == self._normalize_compare_text(prev_final_text):
            score -= 25.0
        candidates.append((score, cand))
    if not candidates:
        return kt or lt or ''
    candidates.sort(key=lambda x: x[0], reverse=True)
    best = candidates[0][1]
    if lt and kt and _bk_fix43_info_len(lt) > _bk_fix43_info_len(kt) * 1.08:
        if not (_bk_fix45_number_set(kt) - _bk_fix45_number_set(lt)):
            best = lt
    if _bk_fix46_is_truncated_against(kt, best):
        best = kt
    return _clean_ocr_text(best)
def _bk_fix46_ai_revision_run(self):
    if isinstance(self, BKFullPageLMOCRWorker):
        try:
            return _BK_FIX41_PREV_AI_RUN(self) if callable(globals().get('_BK_FIX41_PREV_AI_RUN')) else AIRevisionRuntimeMixin.run(self)
        except Exception:
            return AIRevisionRuntimeMixin.run(self)
    if self._cancelled or self.isInterruptionRequested():
        self.failed_revision.emit(self.path, self._tr('msg_ai_cancelled'))
        return
    try:
        if not self.recs:
            self.finished_revision.emit(self.path, [])
            return
        total = max(1, len(self.recs))
        original_lines = [_clean_ocr_text(getattr(rv, 'text', '') or '') for rv in self.recs]
        page_lines = _bk_fix46_get_page_context(self)
        page_context_text = '\n'.join(page_lines)
        final_lines: List[str] = []
        for i, rv in enumerate(self.recs):
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr('msg_ai_cancelled'))
            self.status_changed.emit(self._tr('ai_status_fix46_overlay_line', i + 1, total, os.path.basename(self.path)))
            kraken_text = original_lines[i] if i < len(original_lines) else _clean_ocr_text(getattr(rv, 'text', '') or '')
            try:
                lm_box_text = _bk_fix46_request_overlay_box_revision(self, rv, page_lines, i, total)
            except Exception as exc:
                try:
                    print(f'FIX8.46 overlay-box OCR failed line {i}: {exc}')
                except Exception:
                    pass
                lm_box_text = kraken_text
            prev_final = final_lines[-1] if final_lines else ''
            best = _bk_fix46_sanity_merge_line(self, kraken_text, lm_box_text, page_context_text, prev_final)
            final_lines.append(best or kraken_text)
            self.progress_changed.emit(10 + int(((i + 1) / total) * 86))
        try:
            tmp_recs = [RecordView(i, final_lines[i], self.recs[i].bbox) for i in range(len(final_lines))]
            tmp_recs = _bk_fix43_resolve_ditto_marks_in_recs(tmp_recs)
            final_lines = [_clean_ocr_text(getattr(rv, 'text', '') or '') for rv in tmp_recs]
        except Exception:
            final_lines = _bk_fix43_resolve_ditto_marks_in_lines(final_lines)
        if len(final_lines) != len(self.recs):
            raise ValueError(self._tr('ai_err_final_merge_count', len(final_lines), len(self.recs)))
        self.status_changed.emit(self._tr('ai_status_done', os.path.basename(self.path)))
        self.progress_changed.emit(100)
        self.finished_revision.emit(self.path, final_lines)
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode('utf-8', errors='replace')
        except Exception:
            body = str(e)
        self.failed_revision.emit(self.path, self._tr('err_http_with_body', e, body))
    except urllib.error.URLError as e:
        self.failed_revision.emit(self.path, self._tr('ai_err_server_unreachable', e))
    except socket.timeout:
        self.failed_revision.emit(self.path, self._tr('ai_err_timeout'))
    except RuntimeError as e:
        self.failed_revision.emit(self.path, str(e))
    except Exception as e:
        self.failed_revision.emit(self.path, ''.join(traceback.format_exception(type(e), e, e.__traceback__)))
try:
    AIRevisionWorker.run = _bk_fix46_ai_revision_run
except Exception:
    pass
def _bk_fix46_request_single_line_reread(self, line_data_url: str, idx: int, current_text: str = '') -> str:
    kraken_text = _clean_ocr_text(current_text or '')
    system_prompt = self._tr('ai_prompt_overlay_compare_system')
    user_prompt = self._tr('ai_prompt_overlay_compare_user', idx, kraken_text, '')
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
            override_max_tokens=max(280, min(max(700, int(getattr(self, 'max_tokens', 1200) or 1200)), 1600)),
        ),
    }
    data = self._post_json(payload)
    txt = _clean_ocr_text(_bk_fix46_parse_single_text(self._extract_message_content(data)))
    if txt and _bk_fix49_is_manual_placeholder_text(kraken_text):
        return txt
    if kraken_text and _bk_fix46_is_truncated_against(kraken_text, txt):
        return kraken_text
    return txt or kraken_text
try:
    AIRevisionWorker._request_single_line_reread = _bk_fix46_request_single_line_reread
except Exception:
    pass
try:
    _BK_FIX48_PREV_AI_INIT = AIRevisionWorker.__init__
except Exception:
    _BK_FIX48_PREV_AI_INIT = None
def _bk_fix48_task_recs_from_parent(parent, path: str):
    try:
        for task in getattr(parent, "queue_items", []) or []:
            if getattr(task, "path", None) == path and getattr(task, "results", None):
                _text, _kr_records, _im, recs = task.results
                return [RecordView(i, getattr(rv, "text", ""), tuple(rv.bbox) if getattr(rv, "bbox", None) else None) for i, rv in enumerate(recs or [])]
    except Exception:
        pass
    return []
def _bk_fix48_reassign_target_indices(worker, parent, original_recs):
    try:
        rows = []
        ctx_single = getattr(parent, "_ai_single_line_context", None) or {}
        ctx_multi = getattr(parent, "_ai_multi_line_context", None) or {}
        if len(worker.recs) == 1 and isinstance(ctx_single, dict) and "row" in ctx_single:
            rows = [int(ctx_single.get("row"))]
        elif isinstance(ctx_multi, dict) and ctx_multi.get("rows"):
            rows = [int(x) for x in list(ctx_multi.get("rows") or [])]
        elif original_recs:
            rows = [int(getattr(rv, "idx", i)) for i, rv in enumerate(original_recs)]
        for i, row in enumerate(rows):
            if 0 <= i < len(worker.recs):
                worker.recs[i].idx = int(row)
    except Exception:
        pass
def _bk_fix48_ai_revision_init(self, *args, **kwargs):
    original_recs = list(kwargs.get("recs", []) or (args[1] if len(args) > 1 else []) or [])
    parent = kwargs.get("parent", None)
    if parent is None and args:
        try:
            parent = args[-1] if hasattr(args[-1], "queue_items") else None
        except Exception:
            parent = None
    _BK_FIX48_PREV_AI_INIT(self, *args, **kwargs)
    try:
        _bk_fix48_reassign_target_indices(self, parent, original_recs)
    except Exception:
        pass
    try:
        all_recs = _bk_fix48_task_recs_from_parent(parent, getattr(self, "path", "")) if parent is not None else []
        if all_recs:
            self._bk_fix48_all_page_recs = all_recs
    except Exception:
        pass
if callable(_BK_FIX48_PREV_AI_INIT) and not getattr(AIRevisionWorker.__init__, "_bk_fix48_init_wrapped", False):
    _bk_fix48_ai_revision_init._bk_fix48_init_wrapped = True
    AIRevisionWorker.__init__ = _bk_fix48_ai_revision_init
try:
    _BK_FIX48_PREV_TARGET_ROWS = BKQueueLMBatchWorker._target_rows_for_item
except Exception:
    _BK_FIX48_PREV_TARGET_ROWS = None
def _bk_fix48_target_rows_for_item(self, item):
    rows, worker_recs = _BK_FIX48_PREV_TARGET_ROWS(self, item)
    try:
        for i, row in enumerate(rows or []):
            if 0 <= i < len(worker_recs):
                worker_recs[i].idx = int(row)
    except Exception:
        pass
    return rows, worker_recs
if callable(_BK_FIX48_PREV_TARGET_ROWS) and not getattr(BKQueueLMBatchWorker._target_rows_for_item, "_bk_fix48_wrapped", False):
    _bk_fix48_target_rows_for_item._bk_fix48_wrapped = True
    BKQueueLMBatchWorker._target_rows_for_item = _bk_fix48_target_rows_for_item
try:
    _BK_FIX48_PREV_MAKE_WORKER = BKQueueLMBatchWorker._make_worker
except Exception:
    _BK_FIX48_PREV_MAKE_WORKER = None
def _bk_fix48_make_worker(self, item, worker_recs):
    worker = _BK_FIX48_PREV_MAKE_WORKER(self, item, worker_recs)
    try:
        recs, _boxes = self._item_recs_and_boxes(item)
        if recs:
            worker._bk_fix48_all_page_recs = [RecordView(i, getattr(rv, "text", ""), tuple(rv.bbox) if getattr(rv, "bbox", None) else None) for i, rv in enumerate(recs)]
    except Exception:
        pass
    return worker
if callable(_BK_FIX48_PREV_MAKE_WORKER) and not getattr(BKQueueLMBatchWorker._make_worker, "_bk_fix48_wrapped", False):
    _bk_fix48_make_worker._bk_fix48_wrapped = True
    BKQueueLMBatchWorker._make_worker = _bk_fix48_make_worker
def _bk_fix48_response_format_full_page_lines(self) -> dict:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "lm_full_page_ocr_context_lines",
            "schema": {
                "type": "object",
                "properties": {
                    "lines": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"text": {"type": "string"}},
                            "required": ["text"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["lines"],
                "additionalProperties": False,
            },
        },
    }
def _bk_fix48_extract_full_page_lines(self, content: str):
    out = []
    try:
        obj = _extract_json_payload(content)
        if isinstance(obj, dict):
            lines = obj.get("lines")
            if isinstance(lines, list):
                for item in lines:
                    if isinstance(item, dict):
                        txt = _clean_ocr_text(_force_text(item.get("text", "")))
                    else:
                        txt = _clean_ocr_text(_force_text(item))
                    if txt and not _bk_fix41_is_json_debris_text(txt):
                        out.append(txt)
            elif isinstance(obj.get("text"), str):
                for line in _extract_text_lines(obj.get("text", "")):
                    line = _clean_ocr_text(line)
                    if line and not _bk_fix41_is_json_debris_text(line):
                        out.append(line)
    except Exception:
        pass
    if not out:
        for line in _extract_text_lines(content or ""):
            line = _clean_ocr_text(line)
            if line and not _bk_fix41_is_json_debris_text(line):
                out.append(line)
    return out
try:
    AIRevisionWorker._response_format_full_page_lines = _bk_fix48_response_format_full_page_lines
    AIRevisionWorker._extract_full_page_lines = _bk_fix48_extract_full_page_lines
except Exception:
    pass
def _bk_fix48_request_true_full_page_ocr_context(self):
    try:
        self.status_changed.emit(self._tr("ai_status_fix48_mandatory_page_ocr", os.path.basename(getattr(self, "path", ""))))
        self.progress_changed.emit(1)
    except Exception:
        pass
    try:
        page_data_url = _page_to_data_url(self.path)
        lines = []
        try:
            lines = BKFullPageLMOCRWorker._request_full_page_ocr(self, page_data_url)
        except Exception as exc:
            try:
                print(f"FIX8.48 mandatory full-page LM OCR failed, falling back to line-context OCR: {exc}")
            except Exception:
                pass
            all_recs = getattr(self, "_bk_fix48_all_page_recs", None) or []
            if all_recs:
                lines = self._request_page_ocr_with_fixed_linecount(page_data_url, all_recs)
        out = []
        for line in lines or []:
            txt = _clean_ocr_text(line)
            if txt and not _bk_fix41_is_json_debris_text(txt):
                out.append(txt)
        out = _bk_fix43_resolve_ditto_marks_in_lines(out)
        try:
            self.progress_changed.emit(8)
        except Exception:
            pass
        return out
    except Exception:
        return []
def _bk_fix46_get_page_context(self):
    return _bk_fix48_request_true_full_page_ocr_context(self)
try:
    AIRevisionWorker.run = _bk_fix46_ai_revision_run
except Exception:
    pass
__all__ = [
    '_bk_fix46_ai_revision_run',
    '_bk_fix46_context_excerpt_for_line',
    '_bk_fix46_get_page_context',
    '_bk_fix46_is_truncated_against',
    '_bk_fix46_parse_single_text',
    '_bk_fix46_request_overlay_box_revision',
    '_bk_fix46_request_single_line_reread',
    '_bk_fix46_sanity_merge_line',
    '_bk_fix48_ai_revision_init',
    '_bk_fix48_extract_full_page_lines',
    '_bk_fix48_make_worker',
    '_bk_fix48_reassign_target_indices',
    '_bk_fix48_request_true_full_page_ocr_context',
    '_bk_fix48_response_format_full_page_lines',
    '_bk_fix48_target_rows_for_item',
    '_bk_fix49_is_manual_placeholder_text',
    '_bk_fix49_is_usable_visual_text',
    '_bk_fix48_task_recs_from_parent',
]
register_globals('bk', globals(), __all__)
