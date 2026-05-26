def _bk_fix54_preserve_record_indices(worker, original_recs, parent=None):
    """Restore global row ids after worker construction.

    This is intentionally separate from fix48 and direct source changes because
    runtime load order can vary in older local checkouts. The full-page OCR line
    matcher must see the real row number, not the local subset index.
    """
    try:
        rows = []
        ctx_single = getattr(parent, "_ai_single_line_context", None) or {}
        ctx_multi = getattr(parent, "_ai_multi_line_context", None) or {}
        if len(getattr(worker, "recs", []) or []) == 1 and isinstance(ctx_single, dict) and "row" in ctx_single:
            rows = [int(ctx_single.get("row"))]
        elif isinstance(ctx_multi, dict) and ctx_multi.get("rows"):
            rows = [int(x) for x in list(ctx_multi.get("rows") or [])]
        elif original_recs:
            rows = [int(getattr(rv, "idx", i)) for i, rv in enumerate(original_recs)]
        for i, row in enumerate(rows):
            if 0 <= i < len(getattr(worker, "recs", []) or []):
                try:
                    worker.recs[i].idx = int(row)
                except Exception:
                    pass
    except Exception:
        pass

try:
    _BK_FIX54_PREV_AI_INIT = AIRevisionWorker.__init__
except Exception:
    _BK_FIX54_PREV_AI_INIT = None

def _bk_fix54_ai_revision_init(self, *args, **kwargs):
    original_recs = list(kwargs.get("recs", []) or (args[1] if len(args) > 1 else []) or [])
    parent = kwargs.get("parent", None)
    if parent is None and args:
        try:
            parent = args[-1] if hasattr(args[-1], "queue_items") else None
        except Exception:
            parent = None
    _BK_FIX54_PREV_AI_INIT(self, *args, **kwargs)
    _bk_fix54_preserve_record_indices(self, original_recs, parent)
    try:
        self._bk_fix54_target_global_indices = [int(getattr(rv, "idx", i)) for i, rv in enumerate(getattr(self, "recs", []) or [])]
    except Exception:
        self._bk_fix54_target_global_indices = []

if callable(_BK_FIX54_PREV_AI_INIT) and not getattr(AIRevisionWorker.__init__, "_bk_fix54_init_wrapped", False):
    _bk_fix54_ai_revision_init._bk_fix54_init_wrapped = True
    AIRevisionWorker.__init__ = _bk_fix54_ai_revision_init

def _bk_fix54_same_name_rich_candidate(worker, kraken_text: str, candidate_text: str) -> bool:
    """Last, explicit allow-rule for the observed historical-table case.

    Same name + same age unit + richer right-table columns means the LM line is
    not a destructive hallucination, even if the numeric age itself differs.
    """
    try:
        if _bk_fix53_should_force_rich_candidate(worker, kraken_text, candidate_text):
            return True
    except Exception:
        pass

    ref = _bk_fix50_norm_space(kraken_text)
    cand = _bk_fix50_norm_space(candidate_text)
    if not ref or not cand or ref == cand:
        return False
    try:
        if _bk_fix50_is_bad_line_candidate(worker, cand, ref):
            return False
    except Exception:
        pass

    try:
        ref_stable = _bk_fix53_stable_numbers(ref)
    except Exception:
        try:
            ref_age_nums = {num for num, _unit in _bk_fix52_age_pairs(ref)}
            ref_stable = _bk_fix49_number_set(ref) - ref_age_nums
        except Exception:
            ref_stable = _bk_fix49_number_set(ref)
    if ref_stable - _bk_fix49_number_set(cand):
        return False

    ref_ages = []
    cand_ages = []
    try:
        ref_ages = _bk_fix53_age_pairs(ref)
        cand_ages = _bk_fix53_age_pairs(cand)
    except Exception:
        try:
            ref_ages = _bk_fix52_age_pairs(ref)
            cand_ages = _bk_fix52_age_pairs(cand)
        except Exception:
            pass
    if not ref_ages or not cand_ages:
        return False
    if not ({unit for _num, unit in ref_ages} & {unit for _num, unit in cand_ages}):
        return False

    ref_anchor = [tok for tok in _bk_fix49_tokens(ref) if not tok.isdigit()]
    cand_anchor = set(tok for tok in _bk_fix49_tokens(cand) if not tok.isdigit())
    age_units = set(_BK_FIX53_UNIT_MAP) if "_BK_FIX53_UNIT_MAP" in globals() else set()
    ref_anchor = [tok for tok in ref_anchor if tok not in age_units and not re.fullmatch(r"[ivxlcdm]+", tok)]
    ref_anchor = [tok for tok in ref_anchor if len(tok) > 1]
    if len(ref_anchor) >= 2:
        if not (ref_anchor[0] in cand_anchor and ref_anchor[1] in cand_anchor):
            return False
    elif ref_anchor:
        if ref_anchor[0] not in cand_anchor:
            return False
    else:
        return False

    if _bk_fix49_info_len(cand) < _bk_fix49_info_len(ref) + 10:
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

def _bk_fix54_pick_rich_candidate(worker, kraken_text: str, *candidate_texts: str) -> str:
    best = ""
    for candidate in candidate_texts:
        cand = _bk_fix50_norm_space(candidate)
        if not cand:
            continue
        if _bk_fix54_same_name_rich_candidate(worker, kraken_text, cand):
            if not best or _bk_fix49_info_len(cand) > _bk_fix49_info_len(best):
                best = cand
    return best

_BK_FIX54_PREV_SANITY_MERGE_LINE = _bk_fix50_sanity_merge_line

def _bk_fix54_sanity_merge_line(worker, kraken_text: str, lm_box_text: str, page_line_text: str = "", prev_final_text: str = "", full_page_context: str = "", page_index_aligned: bool = True) -> str:
    forced = _bk_fix54_pick_rich_candidate(worker, kraken_text, lm_box_text, page_line_text)
    if forced:
        return forced
    return _BK_FIX54_PREV_SANITY_MERGE_LINE(
        worker,
        kraken_text,
        lm_box_text,
        page_line_text,
        prev_final_text,
        full_page_context,
        page_index_aligned,
    )

_bk_fix54_merge_candidates = lambda worker, kraken_text, page_text, box_text, prev_final_text='': _bk_fix54_sanity_merge_line(worker, kraken_text, box_text, page_text, prev_final_text, page_text, True)

_bk_fix50_sanity_merge_line = _bk_fix54_sanity_merge_line
_bk_fix53_sanity_merge_line = _bk_fix54_sanity_merge_line
_bk_fix49_sanity_merge_line = _bk_fix54_sanity_merge_line
_bk_fix46_sanity_merge_line = _bk_fix54_sanity_merge_line
_bk_fix50_merge_candidates = _bk_fix54_merge_candidates
_bk_fix49_merge_candidates = _bk_fix54_merge_candidates
_bk_fix45_merge_candidates = _bk_fix54_merge_candidates
_bk_fix43_choose_final_kraken_first = _bk_fix54_merge_candidates
_bk_fix41_choose_final_kraken_first = _bk_fix54_merge_candidates

try:
    _BK_FIX54_PREV_OVERLAY_BOX_REVISION = _bk_fix50_request_overlay_box_revision
except Exception:
    _BK_FIX54_PREV_OVERLAY_BOX_REVISION = None

def _bk_fix54_request_overlay_box_revision(self, rv, page_context_lines: List[str], local_pos: int, total: int) -> str:
    text = _BK_FIX54_PREV_OVERLAY_BOX_REVISION(self, rv, page_context_lines, local_pos, total)
    try:
        kraken_text = _bk_fix50_norm_space(getattr(rv, "text", "") or "")
        forced = _bk_fix54_pick_rich_candidate(self, kraken_text, text)
        if forced:
            return forced
    except Exception:
        pass
    return text

if callable(_BK_FIX54_PREV_OVERLAY_BOX_REVISION):
    _bk_fix50_request_overlay_box_revision = _bk_fix54_request_overlay_box_revision
    _bk_fix46_request_overlay_box_revision = _bk_fix54_request_overlay_box_revision

def _bk_fix54_ai_revision_run(self):
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
        original_lines = [_bk_fix50_norm_space(getattr(rv, 'text', '') or '') for rv in self.recs]
        page_lines = _bk_fix46_get_page_context(self)
        full_page_context_text = '\n'.join([_bk_fix50_norm_space(x) for x in page_lines if _bk_fix50_norm_space(x)])

        final_lines: List[str] = []
        for i, rv in enumerate(self.recs):
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr('msg_ai_cancelled'))
            self.status_changed.emit(self._tr('ai_status_fix46_overlay_line', i + 1, total, os.path.basename(self.path)))
            kraken_text = original_lines[i] if i < len(original_lines) else _bk_fix50_norm_space(getattr(rv, 'text', '') or '')
            page_line_text = _bk_fix50_find_page_line_candidate(self, rv, kraken_text, page_lines, i)
            try:
                lm_box_text = _bk_fix50_request_overlay_box_revision(self, rv, page_lines, i, total)
            except Exception as exc:
                try:
                    print(f'FIX8.54 overlay-box OCR failed line {i}: {exc}')
                except Exception:
                    pass
                lm_box_text = page_line_text or kraken_text
            prev_final = final_lines[-1] if final_lines else ''

            forced = _bk_fix54_pick_rich_candidate(self, kraken_text, lm_box_text, page_line_text)
            if forced:
                best = forced
            else:
                best = _bk_fix54_sanity_merge_line(
                    self,
                    kraken_text,
                    lm_box_text,
                    page_line_text,
                    prev_final,
                    full_page_context_text,
                    page_index_aligned=True,
                )
            try:
                print(
                    'FIX8.54 FINAL LINE:',
                    f'local={i}',
                    f'global={getattr(rv, "idx", i)}',
                    'kraken=', repr(kraken_text),
                    'lm_box=', repr(_bk_fix50_norm_space(lm_box_text)),
                    'page=', repr(_bk_fix50_norm_space(page_line_text)),
                    'final=', repr(best),
                )
            except Exception:
                pass
            final_lines.append(best or kraken_text)
            self.progress_changed.emit(10 + int(((i + 1) / total) * 86))

        try:
            tmp_recs = [RecordView(getattr(self.recs[i], 'idx', i), final_lines[i], self.recs[i].bbox) for i in range(len(final_lines))]
            tmp_recs = _bk_fix43_resolve_ditto_marks_in_recs(tmp_recs)
            final_lines = [_bk_fix50_norm_space(getattr(rv, 'text', '') or '') for rv in tmp_recs]
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
    AIRevisionWorker.run = _bk_fix54_ai_revision_run
    AIRevisionWorker._choose_final_line_text = lambda self, kraken_text, box_text, page_text, prev_final_text='': _bk_fix54_sanity_merge_line(self, kraken_text, box_text, page_text, prev_final_text, page_text, True)
    AIRevisionWorker._request_line_decision = lambda self, idx, kraken_text, page_text, box_text: _bk_fix54_sanity_merge_line(self, kraken_text, box_text, page_text, '', page_text, True)
except Exception:
    pass
