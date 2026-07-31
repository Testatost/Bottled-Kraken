from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
from bottled_kraken.common import _crop_overlay_box_to_data_url_strict
def _bk_lm_behavior_for_parent(parent, scope: str = "all_lines") -> dict:
    try:
        if parent is not None and hasattr(parent, "_lm_behavior_for_scope"):
            return _bk_lm_behavior_normalized(parent._lm_behavior_for_scope(scope))
    except Exception:
        pass
    defaults = _bk_lm_behavior_defaults_for_scope(scope) if "_bk_lm_behavior_defaults_for_scope" in globals() else _BK_LM_BEHAVIOR_DEFAULTS
    return _bk_lm_behavior_normalized(globals().get("_BK_LM_BEHAVIOR_ACTIVE") or defaults)
def _bk_lm_behavior_for_worker(worker, scope: str = "all_lines") -> dict:
    data = getattr(worker, "lm_behavior", None)
    if isinstance(data, dict):
        return _bk_lm_behavior_normalized(data)
    active = globals().get("_BK_LM_BEHAVIOR_ACTIVE")
    if isinstance(active, dict):
        return _bk_lm_behavior_normalized(active)
    try:
        return _bk_lm_behavior_for_parent(worker.parent(), scope)
    except Exception:
        defaults = _bk_lm_behavior_defaults_for_scope(scope) if "_bk_lm_behavior_defaults_for_scope" in globals() else _BK_LM_BEHAVIOR_DEFAULTS
        return _bk_lm_behavior_normalized(defaults)
def _bk_lm_scope_from_batch_mode(mode: str) -> str:
    mode = str(mode or "")
    if mode == globals().get("_BK_LM_BATCH_MODE_CURRENT_LINE"):
        return "current_line"
    if mode == globals().get("_BK_LM_BATCH_MODE_SELECTED_LINES"):
        return "selected_lines"
    return "all_lines"
def _bk_lm_with_active_behavior(behavior: dict, callback):
    old = globals().get("_BK_LM_BEHAVIOR_ACTIVE")
    globals()["_BK_LM_BEHAVIOR_ACTIVE"] = _bk_lm_behavior_normalized(behavior)
    try:
        return callback()
    finally:
        globals()["_BK_LM_BEHAVIOR_ACTIVE"] = old
try:
    _BK_LM_BEHAVIOR_PREV_AI_INIT = AIRevisionWorker.__init__
except Exception:
    _BK_LM_BEHAVIOR_PREV_AI_INIT = None
def _bk_lm_behavior_ai_init(self, *args, **kwargs):
    explicit_behavior = kwargs.pop("lm_behavior", None)
    parent_arg = kwargs.get("parent", None)
    if callable(_BK_LM_BEHAVIOR_PREV_AI_INIT):
        _BK_LM_BEHAVIOR_PREV_AI_INIT(self, *args, **kwargs)
    scope = "all_lines"
    if isinstance(explicit_behavior, dict):
        behavior = explicit_behavior
        scope = str(explicit_behavior.get("scope") or explicit_behavior.get("_scope") or scope)
    elif isinstance(globals().get("_BK_LM_BEHAVIOR_ACTIVE"), dict):
        behavior = globals().get("_BK_LM_BEHAVIOR_ACTIVE")
        scope = str((behavior or {}).get("scope") or (behavior or {}).get("_scope") or scope)
    else:
        parent = parent_arg
        if parent is None:
            try:
                parent = self.parent()
            except Exception:
                parent = None
        scope = getattr(parent, "_bk_lm_behavior_scope_hint", "all_lines") if parent is not None else "all_lines"
        behavior = _bk_lm_behavior_for_parent(parent, scope)
    self.lm_behavior_scope = scope
    self.lm_behavior = _bk_lm_behavior_normalized(behavior)
    self.script_mode = _normalize_ai_script_mode(self.lm_behavior.get("script_mode", getattr(self, "script_mode", AI_SCRIPT_PRINT)))
if callable(_BK_LM_BEHAVIOR_PREV_AI_INIT):
    AIRevisionWorker.__init__ = _bk_lm_behavior_ai_init
try:
    _BK_LM_BEHAVIOR_PREV_BATCH_INIT = AIBatchRevisionWorker.__init__
except Exception:
    _BK_LM_BEHAVIOR_PREV_BATCH_INIT = None
def _bk_lm_behavior_batch_init(self, *args, **kwargs):
    parent_arg = kwargs.get("parent", None)
    if callable(_BK_LM_BEHAVIOR_PREV_BATCH_INIT):
        _BK_LM_BEHAVIOR_PREV_BATCH_INIT(self, *args, **kwargs)
    parent = parent_arg
    if parent is None:
        try:
            parent = self.parent()
        except Exception:
            parent = None
    scope = getattr(parent, "_bk_lm_behavior_scope_hint", "all_lines") if parent is not None else "all_lines"
    self.lm_behavior_scope = scope
    self.lm_behavior = _bk_lm_behavior_for_parent(parent, scope)
    self.script_mode = _normalize_ai_script_mode(self.lm_behavior.get("script_mode", getattr(self, "script_mode", AI_SCRIPT_PRINT)))
if callable(_BK_LM_BEHAVIOR_PREV_BATCH_INIT):
    AIBatchRevisionWorker.__init__ = _bk_lm_behavior_batch_init
try:
    _BK_LM_BEHAVIOR_PREV_BATCH_REVISE_ONE = AIBatchRevisionWorker._revise_one_item
except Exception:
    _BK_LM_BEHAVIOR_PREV_BATCH_REVISE_ONE = None
def _bk_lm_behavior_batch_revise_one(self, item):
    behavior = getattr(self, "lm_behavior", None) or _BK_LM_BEHAVIOR_DEFAULTS
    return _bk_lm_with_active_behavior(behavior, lambda: _BK_LM_BEHAVIOR_PREV_BATCH_REVISE_ONE(self, item))
if callable(_BK_LM_BEHAVIOR_PREV_BATCH_REVISE_ONE):
    AIBatchRevisionWorker._revise_one_item = _bk_lm_behavior_batch_revise_one
try:
    _BK_LM_BEHAVIOR_PREV_QUEUE_INIT = BKQueueLMBatchWorker.__init__
except Exception:
    _BK_LM_BEHAVIOR_PREV_QUEUE_INIT = None
def _bk_lm_behavior_queue_init(self, *args, **kwargs):
    parent_arg = kwargs.get("parent", None)
    if callable(_BK_LM_BEHAVIOR_PREV_QUEUE_INIT):
        _BK_LM_BEHAVIOR_PREV_QUEUE_INIT(self, *args, **kwargs)
    parent = parent_arg
    if parent is None:
        try:
            parent = self.parent()
        except Exception:
            parent = None
    scope = _bk_lm_scope_from_batch_mode(getattr(self, "mode", "all_lines"))
    self.lm_behavior_scope = scope
    self.lm_behavior = _bk_lm_behavior_for_parent(parent, scope)
    self.script_mode = _normalize_ai_script_mode(self.lm_behavior.get("script_mode", getattr(self, "script_mode", AI_SCRIPT_PRINT)))
if callable(_BK_LM_BEHAVIOR_PREV_QUEUE_INIT):
    BKQueueLMBatchWorker.__init__ = _bk_lm_behavior_queue_init
try:
    _BK_LM_BEHAVIOR_PREV_QUEUE_MAKE_WORKER = BKQueueLMBatchWorker._make_worker
except Exception:
    _BK_LM_BEHAVIOR_PREV_QUEUE_MAKE_WORKER = None
def _bk_lm_behavior_queue_make_worker(self, item, worker_recs):
    behavior = _bk_lm_behavior_normalized(getattr(self, "lm_behavior", None) or _BK_LM_BEHAVIOR_DEFAULTS)
    worker = _bk_lm_with_active_behavior(
        behavior,
        lambda: _BK_LM_BEHAVIOR_PREV_QUEUE_MAKE_WORKER(self, item, worker_recs),
    )
    # Make the settings explicit on the child worker instead of relying only
    # on the temporary module-global active behavior. This prevents later
    # wrappers/import-order changes from silently falling back to defaults.
    try:
        worker.lm_behavior_scope = str(getattr(self, "lm_behavior_scope", "all_lines") or "all_lines")
        worker.lm_behavior = dict(behavior)
        worker.script_mode = _normalize_ai_script_mode(
            behavior.get("script_mode", getattr(worker, "script_mode", AI_SCRIPT_PRINT))
        )
    except Exception:
        pass
    return worker
if callable(_BK_LM_BEHAVIOR_PREV_QUEUE_MAKE_WORKER):
    BKQueueLMBatchWorker._make_worker = _bk_lm_behavior_queue_make_worker
try:
    _BK_LM_BEHAVIOR_PREV_PAGE_CONTEXT = _bk_fix46_get_page_context
except Exception:
    _BK_LM_BEHAVIOR_PREV_PAGE_CONTEXT = None
def _bk_lm_behavior_get_page_context(worker):
    behavior = _bk_lm_behavior_for_worker(worker)
    if not behavior.get("page_ocr", True):
        return []
    if callable(_BK_LM_BEHAVIOR_PREV_PAGE_CONTEXT):
        return _BK_LM_BEHAVIOR_PREV_PAGE_CONTEXT(worker)
    return []
if callable(_BK_LM_BEHAVIOR_PREV_PAGE_CONTEXT):
    _bk_fix46_get_page_context = _bk_lm_behavior_get_page_context
try:
    _BK_LM_BEHAVIOR_PREV_SANITY_MERGE = _bk_fix46_sanity_merge_line
except Exception:
    _BK_LM_BEHAVIOR_PREV_SANITY_MERGE = None
def _bk_lm_behavior_revision_mode(behavior: dict) -> str:
    data = _bk_lm_behavior_normalized(behavior)
    value = str(data.get("weight", "") or "").strip()
    if value in {"kraken_lm_revision", "kraken_first", "lm_first"}:
        return value
    low = value.lower()
    if low in {"lm-ocr > kraken-ocr", "lm"}:
        return "lm_first"
    if low in {"kraken-ocr > lm-ocr", "kraken"}:
        return "kraken_first"
    return "kraken_lm_revision"
def _bk_lm_behavior_filter_config(behavior: dict) -> str:
    if isinstance(behavior, dict):
        if "filter_text" in behavior:
            return str(behavior.get("filter_text") or "")
        if "filters" in behavior:
            return str(behavior.get("filters") or "")
    return ""
def _bk_lm_behavior_is_json_debris(text: str) -> bool:
    t = _clean_ocr_text(text or "")
    if not t:
        return False
    low = t.casefold()
    return (
        t.startswith("{")
        or t.startswith("[")
        or "bbox_norm" in low
        or '"lines"' in low
        or ('"text"' in low and ("{" in t or "}" in t))
    )
def _bk_lm_behavior_is_short_valid_text(text: str) -> bool:
    t = _clean_ocr_text(text or "")
    if not t or "\n" in t or _bk_lm_behavior_is_json_debris(t):
        return False
    return bool(
        re.fullmatch(r"\d{1,4}[.,;:)]?", t)
        or re.fullmatch(r"\d{1,2}\s*\.\s*(?:[IVXLCDM]{1,8}|\d{1,2})\s*[.,;:)]?", t, flags=re.IGNORECASE)
        or re.fullmatch(r"[IVXLCDM]{1,8}[.,;:)]?", t, flags=re.IGNORECASE)
        or re.fullmatch(r"[A-Za-zÀ-ÿÄÖÜäöüß][.,;:)]?", t)
    )


def _bk_lm_behavior_candidate_visible_text(worker, candidate: str) -> str:
    cand = _clean_ocr_text(candidate or "")
    if not cand or "\n" in cand:
        return ""
    if _bk_lm_behavior_is_json_debris(cand):
        return ""
    if _bk_lm_behavior_is_short_valid_text(cand):
        return cand
    try:
        if _bk_fix45_is_bad_candidate(worker, cand):
            return ""
    except Exception:
        pass
    return cand

def _bk_lm_behavior_is_placeholder_source_text(text: str) -> bool:
    t = _clean_ocr_text(text or "")
    if not t:
        return True
    low = t.casefold().strip()
    low_flat = re.sub(r"[\s_:\-.,;]+", " ", low).strip()
    compact = re.sub(r"[\s_:\-.,;]+", "", low)
    if any(word in low_flat for word in ("random", "zufall", "dummy", "platzhalter", "placeholder", "lorem ipsum")):
        return True
    if compact in {"test", "text", "ocr", "box", "bbox", "overlay", "zeile", "line", "leer", "empty", "abc", "xyz", "xxx", "asdf", "qwertz", "qwerty"}:
        return True
    if re.fullmatch(r"(?:test|text|ocr|box|bbox|overlay|zeile|line|dummy|platzhalter|placeholder)\d*", compact):
        return True
    if len(compact) >= 3 and len(set(compact)) == 1:
        return True
    return False
def _bk_lm_behavior_request_overlay_box_revision(self, rv, page_context_lines: List[str], local_pos: int, total: int) -> str:
    behavior = _bk_lm_behavior_for_worker(self)
    kraken_text = _bk_lm_behavior_filter_text(self, getattr(rv, "text", "") or "")
    mode = _bk_lm_behavior_revision_mode(behavior)
    # Standard LM transcription is always driven by the target overlay box.
    # The page-OCR checkbox controls context only; it must never replace or skip
    # the independent crop request for this line.
    if not getattr(rv, "bbox", None):
        return kraken_text
    # Build the request from the exact target overlay box.  This helper has
    # deliberately no full-page fallback: a malformed/missing box is an error,
    # not permission to send the whole page again.
    line_data_url = _crop_overlay_box_to_data_url_strict(
        self.path,
        rv,
        pad_x=int(behavior.get("pad_x", 0) or 0),
        pad_y=int(behavior.get("pad_y", 0) or 0),
        extra_context_y=int(behavior.get("extra_context_y", 0) or 0),
    )
    page_context = ""
    if behavior.get("page_ocr", True):
        try:
            page_context = _bk_fix46_context_excerpt_for_line(rv, page_context_lines)
        except Exception:
            page_context = ""
    if mode == "lm_first":
        system_prompt = (
            "Du bist ein OCR-Leser. Transkribiere die gezeigte Bildzeile exakt. "
            "Antworte sofort, ohne Analyse."
        )
        user_prompt = (
            f"Zeilen-ID: {int(getattr(rv, 'idx', local_pos))}\n"
            f"Kraken-Hinweis (nicht Zieltext): {kraken_text}\n"
            + (f"Kontext: {page_context}\n" if page_context else "")
            + "Gib genau eine Zeile zurück, kein Markdown."
        )
    else:
        system_prompt = str(self._tr("ai_prompt_overlay_compare_system"))
        user_prompt = _bk_lm_behavior_prompt(self, getattr(rv, "idx", local_pos), kraken_text, page_context)
    if not bool(getattr(self, "enable_thinking", False)):
        system_prompt = "/no_think\n" + str(system_prompt)
        user_prompt = "/no_think\n" + str(user_prompt)

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
            override_max_tokens=max(1, int(getattr(self, "max_tokens", 1200) or 1200)),
        ),
    }
    self._bk_strict_overlay_transcription_active = True
    self._bk_active_overlay_crop_data_url = line_data_url
    try:
        data = self._post_json(payload)
    finally:
        self._bk_active_overlay_crop_data_url = None
    content = self._extract_message_content(data)
    text = _bk_lm_behavior_filter_text(self, _bk_fix46_parse_single_text(content))
    if _bk_lm_behavior_is_json_debris(text) or "\n" in str(text or ""):
        text = ""
    if mode == "lm_first":
        return text
    return text or kraken_text
_bk_fix46_request_overlay_box_revision = _bk_lm_behavior_request_overlay_box_revision
def _bk_lm_behavior_parse_single_line_response(content: str) -> str:
    try:
        return _bk_fix46_parse_single_text(content)
    except Exception:
        pass
    raw = str(content or '').strip()
    if not raw:
        return ''
    try:
        if '```' in raw:
            raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.IGNORECASE).strip()
            raw = re.sub(r'\s*```$', '', raw).strip()
        obj = json.loads(raw)
    except Exception:
        obj = None
    if isinstance(obj, dict):
        for key in ('text', 'line', 'result', 'corrected_text', 'final_text'):
            val = obj.get(key)
            if isinstance(val, str):
                return _clean_ocr_text(val)
    try:
        lines = [_clean_ocr_text(x) for x in _extract_text_lines(raw)]
        lines = [x for x in lines if x and not _bk_lm_behavior_is_json_debris(x)]
        if lines:
            return lines[0]
    except Exception:
        pass
    return _clean_ocr_text(raw)
def _bk_lm_behavior_post_single_line(worker, system_prompt: str, user_prompt: str, max_tokens: int = 520) -> str:
    payload = {
        'model': worker.lm_model,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
        **worker._build_sampling_payload(
            response_format=worker._response_format_single_text(),
            override_max_tokens=max(1, min(int(max_tokens), int(getattr(worker, 'max_tokens', max_tokens) or max_tokens))),
        ),
    }
    data = worker._post_json(payload)
    return _bk_lm_behavior_filter_text(worker, _bk_lm_behavior_parse_single_line_response(worker._extract_message_content(data)))
def _bk_lm_behavior_request_sanity_choice(worker, kraken_text: str, lm_text: str, page_text: str = '') -> str:
    kt = _clean_ocr_text(kraken_text or '')
    lt = _clean_ocr_text(lm_text or '')
    pt = _clean_ocr_text(page_text or '')
    if not kt and not lt:
        return pt
    if kt and not lt:
        return kt
    if lt and not kt:
        return lt
    system_prompt = (
        'Du bist ein OCR-Sanity-Check. Vergleiche Kraken-OCR und LM-OCR derselben Zeile. '
        'Wähle die inhaltlich bessere, vollständigere und plausiblere Zeile. '
        'Gib ausschließlich die finale einzelne Zeile zurück, keine Erklärung, kein Markdown, kein JSON.'
    )
    context = f"\nSeitenkontext, nur falls hilfreich:\n{pt[:900]}" if pt and '\n' not in pt else ''
    user_prompt = (
        'Kraken-OCR:\n'
        f'{kt}\n\n'
        'LM-OCR:\n'
        f'{lt}\n'
        f'{context}\n\n'
        'Entscheide, welche Fassung besser ist. Korrigiere nur dann minimal, wenn beide Fassungen denselben klaren OCR-Fehler zeigen. '
        'Antwort: nur die finale Zeile.'
    )
    try:
        decision = _bk_lm_behavior_post_single_line(worker, system_prompt, user_prompt, 620)
        decision = _bk_lm_behavior_candidate_visible_text(worker, decision)
        if decision:
            return decision
    except Exception as exc:
        try:
            print(f'LM behavior sanity choice failed: {exc}')
        except Exception:
            pass
    if callable(_BK_LM_BEHAVIOR_PREV_SANITY_MERGE):
        return _BK_LM_BEHAVIOR_PREV_SANITY_MERGE(worker, kt, lt, pt, '')
    return lt or kt or pt
def _bk_lm_behavior_request_source_revision(worker, kraken_text: str, lm_text: str, page_text: str = '') -> str:
    kt = _clean_ocr_text(kraken_text or '')
    lt = _clean_ocr_text(lm_text or '')
    pt = _clean_ocr_text(page_text or '')
    if not kt:
        return lt or pt
    if _bk_lm_behavior_is_placeholder_source_text(kt) and lt:
        return lt
    if not lt:
        return kt
    system_prompt = (
        'Du korrigierst eine OCR-Zeile sehr konservativ. Die Kraken-Zeile ist die Quelle. '
        'Nutze die LM-OCR nur als Hinweis für einzelne offensichtliche OCR-Wortfehler. '
        'Nicht umstellen, nicht zusammenfassen, nichts hinzufügen, keine neue Zeile erfinden. '
        'Gib ausschließlich eine einzelne korrigierte Zeile zurück.'
    )
    context = f"\nSeitenkontext, nur falls hilfreich:\n{pt[:900]}" if pt and '\n' not in pt else ''
    user_prompt = (
        'Quelle / Kraken-OCR:\n'
        f'{kt}\n\n'
        'Hinweis / LM-OCR derselben Box:\n'
        f'{lt}\n'
        f'{context}\n\n'
        'Ergebnis: Behalte die Kraken-Zeile bei und ersetze nur einzelne klar falsche Wörter/Zeichenfolgen, '
        'wenn die LM-OCR dafür einen plausiblen Hinweis liefert. Antwort: nur die finale Zeile.'
    )
    try:
        revised = _bk_lm_behavior_post_single_line(worker, system_prompt, user_prompt, 620)
        revised = _bk_lm_behavior_candidate_visible_text(worker, revised)
        if revised:
            try:
                if _bk_fix46_is_truncated_against(kt, revised):
                    return kt
            except Exception:
                pass
            try:
                if worker._token_overlap_ratio(kt, revised) < 0.35 and worker._text_similarity_ratio(kt, revised) < 0.45:
                    return kt
            except Exception:
                pass
            return revised
    except Exception as exc:
        try:
            print(f'LM behavior source revision failed: {exc}')
        except Exception:
            pass
    return kt
def _bk_lm_behavior_sanity_merge_line(worker, kraken_text: str, lm_box_text: str, page_line_text: str = "", prev_final_text: str = "", full_page_context: str = "", page_index_aligned: bool = True) -> str:
    behavior = _bk_lm_behavior_for_worker(worker)
    kt = _clean_ocr_text(kraken_text or "")
    lt = _bk_lm_behavior_filter_text(worker, lm_box_text)
    pt = _bk_lm_behavior_filter_text(worker, page_line_text) if behavior.get("page_ocr", True) else ""
    mode = _bk_lm_behavior_revision_mode(behavior)
    lm_visible = _bk_lm_behavior_candidate_visible_text(worker, lt)
    page_visible = _bk_lm_behavior_candidate_visible_text(worker, pt)
    if _bk_lm_behavior_is_placeholder_source_text(kt) and (lm_visible or page_visible):
        return lm_visible or page_visible or kt
    if mode == "lm_first":
        return lm_visible or page_visible or kt
    if mode == "kraken_first":
        return _bk_lm_behavior_request_sanity_choice(worker, kt, lm_visible or lt, page_visible or pt)
    if mode == "kraken_lm_revision":
        return _bk_lm_behavior_request_source_revision(worker, kt, lm_visible or lt, page_visible or pt)
    if callable(_BK_LM_BEHAVIOR_PREV_SANITY_MERGE):
        return _BK_LM_BEHAVIOR_PREV_SANITY_MERGE(worker, kt, lm_visible or lt, page_visible or pt, prev_final_text)
    return lm_visible or kt or page_visible
_bk_fix46_sanity_merge_line = _bk_lm_behavior_sanity_merge_line


# ---------------------------------------------------------------------------
# Settings-faithful, one-overlay-box-per-request LM transcription path
# ---------------------------------------------------------------------------
# Standard LM transcription scopes (current line, selected lines, all lines)
# always transcribe every target overlay box separately. A full-page OCR may be
# requested once as optional context when the user enables it, but it never
# replaces the line-by-line overlay transcription.




def _bk_lm_behavior_overlay_ocr_per_line(worker, recs, page_context_lines=None) -> dict:
    """Transcribe exactly one overlay crop per model request.

    The optional full-page OCR is only passed in as textual context. It never
    replaces a crop request and several overlay boxes are never combined into
    one vision request.
    """
    behavior = _bk_lm_behavior_for_worker(
        worker,
        getattr(worker, "lm_behavior_scope", "all_lines"),
    )
    recs = list(recs or [])
    results = {}
    targets = [rv for rv in recs if getattr(rv, "bbox", None)]
    if not targets:
        return results

    total = len(targets)
    for local_pos, rv in enumerate(targets):
        if worker._cancelled or worker.isInterruptionRequested():
            raise RuntimeError(worker._tr("msg_ai_cancelled"))

        idx = int(getattr(rv, "idx", local_pos))
        try:
            worker.status_changed.emit(
                worker._tr(
                    "ai_status_fix46_overlay_line",
                    local_pos + 1,
                    total,
                    os.path.basename(getattr(worker, "path", "")),
                )
            )
        except Exception:
            pass
        try:
            text = _bk_lm_behavior_request_overlay_box_revision(
                worker,
                rv,
                page_context_lines or [],
                local_pos,
                total,
            )
            text = _bk_lm_behavior_candidate_visible_text(worker, text)
        except Exception as exc:
            # Cancellation is control flow, not a recoverable line failure.
            # Re-raise immediately so no following overlay box is requested.
            if worker._cancelled or worker.isInterruptionRequested():
                raise RuntimeError(worker._tr("msg_ai_cancelled")) from exc
            # A real failure of one overlay box must not destroy the whole page.
            # Preserve the original line for this one box and continue.
            try:
                print(f"LM overlay line {idx} failed: {exc}")
            except Exception:
                pass
            text = ""

        if text:
            results[idx] = text

        try:
            # Keep progress monotonic while reserving the first 10% for optional
            # full-page context OCR and the last 10% for final assembly.
            worker.progress_changed.emit(10 + int(((local_pos + 1) / max(1, total)) * 80))
        except Exception:
            pass

    return results


# Compatibility name retained because older feature modules/tests may still
# import it. The implementation is deliberately sequential and one-image-only.

try:
    _BK_LM_BEHAVIOR_PREV_FAST_AI_RUN = AIRevisionWorker.run
except Exception:
    _BK_LM_BEHAVIOR_PREV_FAST_AI_RUN = None


def _bk_lm_behavior_fast_ai_run(self):
    # Dedicated full-page LM OCR is a separate explicit mode and remains on its
    # specialized worker path. The crop-only guard applies to normal line
    # transcription, not to that dedicated full-page command.
    if isinstance(self, BKFullPageLMOCRWorker):
        if callable(_BK_LM_BEHAVIOR_PREV_FAST_AI_RUN):
            return _BK_LM_BEHAVIOR_PREV_FAST_AI_RUN(self)
        return None

    # Authoritative line-transcription mode: at most one full-page image request
    # for optional context; every later image request must be the active overlay
    # crop. The low-level guard installed late in app_features enforces this.
    self._bk_strict_overlay_transcription_active = True
    self._bk_active_overlay_crop_data_url = None
    if self._cancelled or self.isInterruptionRequested():
        self.failed_revision.emit(self.path, self._tr("msg_ai_cancelled"))
        return
    try:
        recs = list(getattr(self, "recs", []) or [])
        if not recs:
            self.finished_revision.emit(self.path, [])
            return
        behavior = _bk_lm_behavior_for_worker(
            self,
            getattr(self, "lm_behavior_scope", "all_lines"),
        )
        original = [_clean_ocr_text(getattr(rv, "text", "") or "") for rv in recs]
        mode = _bk_lm_behavior_revision_mode(behavior)
        self.progress_changed.emit(2)

        page_lines = []
        if behavior.get("page_ocr", False):
            page_lines = _bk_fix46_get_page_context(self) or []
        if self._cancelled or self.isInterruptionRequested():
            raise RuntimeError(self._tr("msg_ai_cancelled"))
        self.progress_changed.emit(10)

        # Standard transcription always uses every available overlay box,
        # one box per independent vision request. The full-page OCR, when
        # enabled, is context only and is never used as a substitute result.
        overlay_by_idx = _bk_lm_behavior_overlay_ocr_per_line(self, recs, page_lines)
        if self._cancelled or self.isInterruptionRequested():
            raise RuntimeError(self._tr("msg_ai_cancelled"))

        try:
            self.status_changed.emit(self._tr("ai_status_fix46_finalize", os.path.basename(self.path)))
        except Exception:
            pass
        self.progress_changed.emit(92)

        lm_candidates = []
        for i, rv in enumerate(recs):
            idx = int(getattr(rv, "idx", i))
            candidate = overlay_by_idx.get(idx, "")
            lm_candidates.append(_bk_lm_behavior_candidate_visible_text(self, candidate))

        if mode == "lm_first":
            final_lines = [lm_candidates[i] or original[i] for i in range(len(original))]
        elif mode == "kraken_first":
            final_lines = []
            for i, kt in enumerate(original):
                if not kt or _bk_lm_behavior_is_placeholder_source_text(kt):
                    final_lines.append(lm_candidates[i] or kt)
                else:
                    final_lines.append(kt)
        else:
            # The per-overlay vision request already receives the Kraken line,
            # optional page context and the selected revision-mode prompt. Use
            # that one line-level answer directly; do not perform a second LM
            # decision/revision request, which was the main source of slowness.
            final_lines = [lm_candidates[i] or original[i] for i in range(len(original))]

        try:
            tmp_recs = [RecordView(i, final_lines[i], recs[i].bbox) for i in range(len(final_lines))]
            tmp_recs = _bk_fix43_resolve_ditto_marks_in_recs(tmp_recs)
            final_lines = [_clean_ocr_text(getattr(rv, "text", "") or "") for rv in tmp_recs]
        except Exception:
            try:
                final_lines = _bk_fix43_resolve_ditto_marks_in_lines(final_lines)
            except Exception:
                pass
        if len(final_lines) != len(recs):
            raise ValueError(self._tr("ai_err_final_merge_count", len(final_lines), len(recs)))
        if self._cancelled or self.isInterruptionRequested():
            raise RuntimeError(self._tr("msg_ai_cancelled"))
        self.progress_changed.emit(100)
        self.status_changed.emit(self._tr("ai_status_done", os.path.basename(self.path)))
        self.finished_revision.emit(self.path, final_lines)
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = str(e)
        self.failed_revision.emit(self.path, self._tr("err_http_with_body", e, body))
    except urllib.error.URLError as e:
        self.failed_revision.emit(self.path, self._tr("ai_err_server_unreachable", e))
    except socket.timeout:
        self.failed_revision.emit(self.path, self._tr("ai_err_timeout"))
    except RuntimeError as e:
        self.failed_revision.emit(self.path, str(e))
    except Exception as e:
        self.failed_revision.emit(self.path, "".join(traceback.format_exception(type(e), e, e.__traceback__)))


if callable(_BK_LM_BEHAVIOR_PREV_FAST_AI_RUN):
    AIRevisionWorker.run = _bk_lm_behavior_fast_ai_run
__all__ = [
    '_bk_fix46_request_overlay_box_revision',
    '_bk_fix46_sanity_merge_line',
    '_bk_lm_behavior_ai_init',
    '_bk_lm_behavior_batch_init',
    '_bk_lm_behavior_batch_revise_one',
    '_bk_lm_behavior_overlay_ocr_per_line',
    '_bk_lm_behavior_candidate_visible_text',
    '_bk_lm_behavior_filter_config',
    '_bk_lm_behavior_for_parent',
    '_bk_lm_behavior_for_worker',
    '_bk_lm_behavior_get_page_context',
    '_bk_lm_behavior_is_json_debris',
    '_bk_lm_behavior_is_placeholder_source_text',
    '_bk_lm_behavior_is_short_valid_text',
    '_bk_lm_behavior_parse_single_line_response',
    '_bk_lm_behavior_post_single_line',
    '_bk_lm_behavior_queue_init',
    '_bk_lm_behavior_queue_make_worker',
    '_bk_lm_behavior_request_overlay_box_revision',
    '_bk_lm_behavior_request_sanity_choice',
    '_bk_lm_behavior_request_source_revision',
    '_bk_lm_behavior_revision_mode',
    '_bk_lm_behavior_sanity_merge_line',
    '_bk_lm_scope_from_batch_mode',
    '_bk_lm_with_active_behavior',
]
register_globals('bk', globals(), __all__)
