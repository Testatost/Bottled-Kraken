from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())

from bottled_kraken.common import (
    _clean_ocr_text,
    _crop_single_line_to_data_url,
    _extract_json_payload,
    _extract_text_lines,
    _force_text,
    re,
    json,
)
from bottled_kraken.workers import AIRevisionWorker


def _bk_fix50_is_manual_overlay_placeholder(text: str) -> bool:
    """Detect deliberately typed filler/random text in manually drawn boxes.

    This is intentionally stricter for real OCR and broader for one-token
    keysmash strings. A detected placeholder must never protect the old line
    against a short visual result like "2", "2.", "U" or "III".
    """
    t = _clean_ocr_text(text or '')
    if not t:
        return False
    low = t.casefold().strip()
    low_flat = re.sub(r"[\s_:\-.,;]+", " ", low).strip()
    compact = re.sub(r"[^0-9a-zäöüß]", "", low)
    if not compact:
        return False
    if any(word in low_flat for word in (
        'random', 'zufall', 'dummy', 'platzhalter', 'placeholder',
        'lorem ipsum', 'testtext', 'test text', 'keysmash', 'gibberish',
    )):
        return True
    if compact in {
        'test', 'text', 'ocr', 'box', 'bbox', 'overlay', 'zeile', 'line',
        'leer', 'empty', 'abc', 'abcd', 'xyz', 'xxx', 'asdf', 'qwer',
        'qwertz', 'qwerty', 'dummy', 'random', 'platzhalter', 'placeholder',
    }:
        return True
    if re.fullmatch(r"(?:test|text|ocr|box|bbox|overlay|zeile|line|dummy|platzhalter|placeholder|random)\d*", compact):
        return True
    if len(compact) >= 3 and len(set(compact)) == 1:
        return True
    # Long single-token keyboard/random input, e.g. "adgadgadgadfgdfgsf".
    if re.search(r"\s", t):
        return False
    letters = re.sub(r"[^a-zäöüß]", "", compact)
    if len(compact) >= 8:
        for size in (2, 3, 4, 5):
            chunks = [compact[i:i + size] for i in range(0, max(0, len(compact) - size + 1))]
            if any(chunks.count(chunk) >= 3 for chunk in set(chunks)):
                return True
        if re.search(r"[bcdfghjklmnpqrstvwxz]{5,}", compact):
            return True
    if len(letters) >= 10:
        unique_ratio = len(set(letters)) / max(1, len(letters))
        vowel_ratio = sum(1 for ch in letters if ch in 'aeiouäöüy') / max(1, len(letters))
        # Avoid catching plausible German/Czech place or family names unless the token
        # is very low-information or vowel-poor.
        if unique_ratio <= 0.45 or vowel_ratio < 0.18:
            return True
    if len(compact) >= 14:
        unique_ratio = len(set(compact)) / max(1, len(compact))
        if unique_ratio <= 0.55 and not re.search(r"[A-ZÄÖÜ]", t):
            return True
    return False


def _bk_fix50_is_json_debris(text: str) -> bool:
    t = _clean_ocr_text(text or '')
    low = t.casefold()
    return bool(t.startswith('{') or t.startswith('[') or 'bbox_norm' in low or '"lines"' in low or ('"text"' in low and ('{' in t or '}' in t)))


def _bk_fix50_is_short_valid_visual_text(text: str) -> bool:
    t = _clean_ocr_text(text or '')
    if not t or '\n' in t or _bk_fix50_is_json_debris(t):
        return False
    return bool(
        re.fullmatch(r"\d{1,5}\.?", t)
        or re.fullmatch(r"\d{1,2}\s*\.\s*(?:[IVXLCDM]{1,8}|\d{1,2})\s*\.?", t, flags=re.IGNORECASE)
        or re.fullmatch(r"[IVXLCDM]{1,8}\.?", t, flags=re.IGNORECASE)
        or re.fullmatch(r"[A-Za-zÀ-ÿÄÖÜäöüß]\.?", t)
    )


def _bk_fix50_candidate_visible_text(worker, candidate: str) -> str:
    cand = _clean_ocr_text(candidate or '')
    if not cand or '\n' in cand or _bk_fix50_is_json_debris(cand):
        return ''
    if _bk_fix50_is_short_valid_visual_text(cand):
        return cand
    if _bk_fix50_is_manual_overlay_placeholder(cand):
        return ''
    try:
        bad = _bk_fix45_is_bad_candidate(worker, cand)
    except Exception:
        bad = False
    return '' if bad else cand


def _bk_fix50_parse_single_text(content: str) -> str:
    raw = str(content or '').strip()
    if not raw:
        return ''
    raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.IGNORECASE).strip()
    raw = re.sub(r'\s*```$', '', raw).strip()
    obj = None
    try:
        obj = json.loads(raw)
    except Exception:
        try:
            obj = _extract_json_payload(raw)
        except Exception:
            obj = None
    if isinstance(obj, dict):
        for key in ('text', 'line', 'ocr_text', 'corrected_text', 'result', 'final_text'):
            val = obj.get(key)
            if isinstance(val, str):
                return _clean_ocr_text(val)
    try:
        lines = [_clean_ocr_text(x) for x in _extract_text_lines(raw)]
        lines = [x for x in lines if x and not _bk_fix50_is_json_debris(x)]
        if lines:
            return lines[0]
    except Exception:
        pass
    return _clean_ocr_text(raw)


try:
    _BK_FIX50_PREV_EXTRACT_MESSAGE_CONTENT = AIRevisionWorker._extract_message_content
except Exception:
    _BK_FIX50_PREV_EXTRACT_MESSAGE_CONTENT = None


def _bk_fix50_extract_message_content(self, data: dict) -> str:
    try:
        if callable(_BK_FIX50_PREV_EXTRACT_MESSAGE_CONTENT):
            return _BK_FIX50_PREV_EXTRACT_MESSAGE_CONTENT(self, data)
    except Exception as exc:
        # Some reasoning models put the required JSON into reasoning_content while
        # message.content stays empty. Use reasoning only when it is clearly a compact
        # OCR answer or valid JSON, not as free-form chain-of-thought.
        try:
            choices = data.get('choices') if isinstance(data, dict) else None
            choice0 = choices[0] if isinstance(choices, list) and choices else {}
            message = choice0.get('message', {}) if isinstance(choice0, dict) else {}
            reasoning = message.get('reasoning_content') if isinstance(message, dict) else ''
            reasoning = str(reasoning or '').strip()
            if reasoning:
                cleaned = re.sub(r'<think>.*?</think>', '', reasoning, flags=re.DOTALL).strip()
                obj = _extract_json_payload(cleaned)
                if isinstance(obj, dict):
                    return cleaned
                parsed = _bk_fix50_parse_single_text(cleaned)
                if _bk_fix50_is_short_valid_visual_text(parsed):
                    return json.dumps({'text': parsed}, ensure_ascii=False)
        except Exception:
            pass
        raise exc
    return ''


try:
    _BK_FIX50_PREV_PLACEHOLDER = AIRevisionWorker._looks_like_manual_placeholder
except Exception:
    _BK_FIX50_PREV_PLACEHOLDER = None


def _bk_fix50_worker_placeholder(self, text: str) -> bool:
    if _bk_fix50_is_manual_overlay_placeholder(text):
        return True
    if callable(_BK_FIX50_PREV_PLACEHOLDER):
        try:
            return bool(_BK_FIX50_PREV_PLACEHOLDER(self, text))
        except Exception:
            pass
    return False


try:
    _BK_FIX50_PREV_USABLE = AIRevisionWorker._is_usable_image_line_result
except Exception:
    _BK_FIX50_PREV_USABLE = None


def _bk_fix50_worker_usable_image_line_result(self, text: str) -> bool:
    cand = _bk_fix50_candidate_visible_text(self, text)
    if cand:
        return True
    if callable(_BK_FIX50_PREV_USABLE):
        try:
            return bool(_BK_FIX50_PREV_USABLE(self, text)) and not _bk_fix50_is_manual_overlay_placeholder(text)
        except Exception:
            pass
    return False


try:
    _BK_FIX50_PREV_PLACEHOLDER_SOURCE = _bk_lm_behavior_is_placeholder_source_text
except Exception:
    _BK_FIX50_PREV_PLACEHOLDER_SOURCE = None


def _bk_lm_behavior_is_placeholder_source_text(text: str) -> bool:
    if _bk_fix50_is_manual_overlay_placeholder(text):
        return True
    if callable(_BK_FIX50_PREV_PLACEHOLDER_SOURCE):
        try:
            return bool(_BK_FIX50_PREV_PLACEHOLDER_SOURCE(text))
        except Exception:
            pass
    return False


try:
    _BK_FIX50_PREV_OVERLAY_REQUEST = _bk_fix46_request_overlay_box_revision
except Exception:
    _BK_FIX50_PREV_OVERLAY_REQUEST = None


def _bk_fix50_request_placeholder_visual_ocr(worker, rv, local_pos: int) -> str:
    # Use a bit of padding even if the global LM behavior is set to 0. Tiny page
    # numbers otherwise get cropped too tightly and some vision models return empty.
    behavior = {}
    try:
        behavior = _bk_lm_behavior_for_worker(worker)
    except Exception:
        behavior = {}
    pad_x = max(8, int(behavior.get('pad_x', 0) or 0))
    pad_y = max(6, int(behavior.get('pad_y', 0) or 0))
    extra_y = max(0, int(behavior.get('extra_context_y', 0) or 0))
    line_data_url = _crop_single_line_to_data_url(worker.path, rv, pad_x=pad_x, pad_y=pad_y, extra_context_y=extra_y)
    system_prompt = (
        'Du bist ein reiner OCR-Leser. Der vorhandene Zeilentext ist künstlicher Platzhalter-/Random-Text. '
        'Ignoriere den vorhandenen Text vollständig. Lies ausschließlich den Bildausschnitt. '
        'Auch sehr kurze Ergebnisse wie "2", "2.", "3", "U" oder römische Zahlen sind gültig. '
        'Antworte strikt als JSON-Objekt mit genau diesem Schema: {"text":"..."}.'
    )
    user_prompt = (
        f'Zeilen-ID: {int(getattr(rv, "idx", local_pos))}\n'
        'Transkribiere genau den sichtbaren Inhalt dieser Overlay-Box. '
        'Keine Erklärung, kein Markdown, keine Korrektur gegen den alten Text. '
        'Wenn nur eine Zahl oder ein Punkt sichtbar ist, gib genau diese Zeichen zurück.'
    )
    payload = {
        'model': worker.lm_model,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': [
                {'type': 'text', 'text': user_prompt},
                {'type': 'image_url', 'image_url': {'url': line_data_url}},
            ]},
        ],
        **worker._build_sampling_payload(
            response_format=worker._response_format_single_text(),
            override_max_tokens=260,
        ),
    }
    data = worker._post_json(payload)
    content = worker._extract_message_content(data)
    try:
        print('RAW FIX50 MANUAL OVERLAY OCR RESPONSE:')
        print(str(content)[:1800])
    except Exception:
        pass
    return _bk_fix50_candidate_visible_text(worker, _bk_fix50_parse_single_text(content))


def _bk_fix46_request_overlay_box_revision(self, rv, page_context_lines, local_pos: int, total: int) -> str:
    kraken_text = _clean_ocr_text(getattr(rv, 'text', '') or '')
    if _bk_fix50_is_manual_overlay_placeholder(kraken_text) and getattr(rv, 'bbox', None):
        try:
            visual = _bk_fix50_request_placeholder_visual_ocr(self, rv, local_pos)
            if visual:
                return visual
        except Exception as exc:
            try:
                print(f'FIX50 manual overlay visual OCR failed line {local_pos}: {exc}')
            except Exception:
                pass
        # Do not return the placeholder as a preferred OCR candidate. Let the
        # later fallback use page context if available; otherwise the callback will
        # keep the old text rather than inventing content.
        return ''
    if callable(_BK_FIX50_PREV_OVERLAY_REQUEST):
        return _BK_FIX50_PREV_OVERLAY_REQUEST(self, rv, page_context_lines, local_pos, total)
    return kraken_text


try:
    _BK_FIX50_PREV_SANITY_MERGE = _bk_fix46_sanity_merge_line
except Exception:
    _BK_FIX50_PREV_SANITY_MERGE = None


def _bk_fix46_sanity_merge_line(self, kraken_text: str, lm_box_text: str, page_context_text: str = '', prev_final_text: str = '', full_page_context: str = '', page_index_aligned: bool = True) -> str:
    kt = _clean_ocr_text(kraken_text or '')
    lt = _clean_ocr_text(lm_box_text or '')
    pt = _clean_ocr_text(page_context_text or '')
    if _bk_fix50_is_manual_overlay_placeholder(kt):
        visible = _bk_fix50_candidate_visible_text(self, lt)
        if visible:
            return visible
        page_visible = _bk_fix50_candidate_visible_text(self, pt) if '\n' not in pt else ''
        if page_visible:
            return page_visible
        return ''
    if callable(_BK_FIX50_PREV_SANITY_MERGE):
        try:
            return _BK_FIX50_PREV_SANITY_MERGE(self, kt, lt, pt, prev_final_text)
        except TypeError:
            return _BK_FIX50_PREV_SANITY_MERGE(self, kt, lt, pt, prev_final_text, full_page_context, page_index_aligned)
    return lt or kt or pt


try:
    AIRevisionWorker._extract_message_content = _bk_fix50_extract_message_content
    AIRevisionWorker._looks_like_manual_placeholder = _bk_fix50_worker_placeholder
    AIRevisionWorker._is_usable_image_line_result = _bk_fix50_worker_usable_image_line_result
except Exception:
    pass

# Export names so module_registry.synchronize() updates older monkey-patch modules
# whose AIRevisionWorker.run resolves _bk_fix46_* functions as globals.
__all__ = [
    '_bk_fix50_is_manual_overlay_placeholder',
    '_bk_fix50_is_json_debris',
    '_bk_fix50_is_short_valid_visual_text',
    '_bk_fix50_candidate_visible_text',
    '_bk_fix50_parse_single_text',
    '_bk_fix50_extract_message_content',
    '_bk_fix50_worker_placeholder',
    '_bk_fix50_worker_usable_image_line_result',
    '_bk_lm_behavior_is_placeholder_source_text',
    '_bk_fix50_request_placeholder_visual_ocr',
    '_bk_fix46_request_overlay_box_revision',
    '_bk_fix46_sanity_merge_line',
]
register_globals('bk', globals(), __all__)
