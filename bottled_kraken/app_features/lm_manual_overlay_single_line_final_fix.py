from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
from bottled_kraken.common import _crop_overlay_box_to_data_url_strict

from bottled_kraken.common import (
    _clean_ocr_text,
    _crop_single_line_to_data_url,
    _extract_json_payload,
    _extract_text_lines,
    _force_text,
    json,
    os,
    re,
)
from bottled_kraken.workers import AIRevisionWorker


def _bk_fix51_is_json_debris(text: str) -> bool:
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


def _bk_fix51_is_short_valid_visual_text(text: str) -> bool:
    t = _clean_ocr_text(text or "")
    if not t or "\n" in t or _bk_fix51_is_json_debris(t):
        return False
    return bool(
        re.fullmatch(r"\d{1,6}[.,;:)]?", t)
        or re.fullmatch(r"\d{1,2}\s*\.\s*(?:[IVXLCDM]{1,10}|\d{1,3})\s*[.,;:)]?", t, flags=re.IGNORECASE)
        or re.fullmatch(r"[IVXLCDM]{1,10}[.,;:)]?", t, flags=re.IGNORECASE)
        or re.fullmatch(r"[A-Za-zÀ-ÿÄÖÜäöüß][.,;:)]?", t)
        or re.fullmatch(r"[-–—=•·*]{1,8}", t)
    )


def _bk_fix51_is_manual_overlay_source(text: str) -> bool:
    t = _clean_ocr_text(text or "")
    if not t:
        return True
    for fn_name in (
        "_bk_fix50_is_manual_overlay_placeholder",
        "_bk_lm_behavior_is_placeholder_source_text",
        "_bk_fix49_is_manual_placeholder_text",
    ):
        fn = globals().get(fn_name)
        if callable(fn):
            try:
                if bool(fn(t)):
                    return True
            except Exception:
                pass
    low = t.casefold().strip()
    low_flat = re.sub(r"[\s_:\-.,;]+", " ", low).strip()
    compact = re.sub(r"[^0-9a-zäöüß]", "", low)
    if not compact:
        return False
    if any(word in low_flat for word in (
        "random", "zufall", "dummy", "platzhalter", "placeholder", "keysmash",
        "gibberish", "testtext", "test text", "lorem ipsum",
    )):
        return True
    if compact in {
        "test", "text", "ocr", "box", "bbox", "overlay", "zeile", "line",
        "leer", "empty", "abc", "abcd", "xyz", "xxx", "asdf", "qwer",
        "qwertz", "qwerty", "dummy", "random", "platzhalter", "placeholder",
    }:
        return True
    if len(compact) >= 8 and not re.search(r"\s", t):
        for size in (2, 3, 4, 5):
            chunks = [compact[i:i + size] for i in range(0, max(0, len(compact) - size + 1))]
            if any(chunks.count(chunk) >= 3 for chunk in set(chunks)):
                return True
        if re.search(r"[bcdfghjklmnpqrstvwxz]{5,}", compact):
            return True
        letters = re.sub(r"[^a-zäöüß]", "", compact)
        if len(letters) >= 10:
            vowels = sum(1 for ch in letters if ch in "aeiouäöüüy")
            vowel_ratio = vowels / max(1, len(letters))
            unique_ratio = len(set(letters)) / max(1, len(letters))
            if vowel_ratio < 0.20 or unique_ratio <= 0.50:
                return True
    return False


def _bk_fix51_parse_single_text(raw: str) -> str:
    text = str(raw or "").strip()
    if not text:
        return ""
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"\s*```$", "", text).strip()
    obj = None
    try:
        obj = json.loads(text)
    except Exception:
        try:
            obj = _extract_json_payload(text)
        except Exception:
            obj = None
    if isinstance(obj, dict):
        for key in ("text", "line", "ocr_text", "corrected_text", "result", "final_text"):
            value = obj.get(key)
            if isinstance(value, str):
                return _clean_ocr_text(value)
    try:
        lines = [_clean_ocr_text(x) for x in _extract_text_lines(text)]
        lines = [x for x in lines if x and not _bk_fix51_is_json_debris(x)]
        if lines:
            return lines[0]
    except Exception:
        pass
    return _clean_ocr_text(text)


def _bk_fix51_flatten_chat_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace").strip()
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("text", "content", "output_text"):
            out = _bk_fix51_flatten_chat_value(value.get(key))
            if out:
                return out
        return ""
    if isinstance(value, list):
        parts = []
        for item in value:
            txt = _bk_fix51_flatten_chat_value(item)
            if txt:
                parts.append(txt)
        return "\n".join(parts).strip()
    return _force_text(value).strip()


try:
    _BK_FIX51_PREV_EXTRACT_MESSAGE_CONTENT = AIRevisionWorker._extract_message_content
except Exception:
    _BK_FIX51_PREV_EXTRACT_MESSAGE_CONTENT = None


def _bk_fix51_extract_message_content(self, data: dict) -> str:
    # Prefer normal content, but do not lose compact JSON stored by reasoning-only
    # models such as Qwen. Only JSON/short OCR payloads are accepted from reasoning.
    try:
        if callable(_BK_FIX51_PREV_EXTRACT_MESSAGE_CONTENT):
            content = _BK_FIX51_PREV_EXTRACT_MESSAGE_CONTENT(self, data)
            if str(content or "").strip():
                return str(content).strip()
    except Exception as prev_exc:
        saved_exc = prev_exc
    else:
        saved_exc = None

    choices = data.get("choices") if isinstance(data, dict) else None
    choice0 = choices[0] if isinstance(choices, list) and choices else {}
    message = choice0.get("message", {}) if isinstance(choice0, dict) else {}
    candidates = []
    if isinstance(message, dict):
        candidates.extend([
            message.get("content"),
            message.get("text"),
            message.get("output_text"),
            message.get("reasoning_content"),
        ])
    if isinstance(choice0, dict):
        candidates.extend([choice0.get("content"), choice0.get("text"), choice0.get("output_text")])
    for cand in candidates:
        raw = _bk_fix51_flatten_chat_value(cand)
        if not raw:
            continue
        cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        if not cleaned:
            continue
        parsed = _bk_fix51_parse_single_text(cleaned)
        if cleaned.startswith("{") or '"text"' in cleaned or '"lines"' in cleaned or _bk_fix51_is_short_valid_visual_text(parsed):
            return cleaned
    if saved_exc is not None:
        raise saved_exc
    return ""


def _bk_fix51_candidate_visible_text(worker, candidate: str) -> str:
    cand = _clean_ocr_text(candidate or "")
    if not cand or "\n" in cand or _bk_fix51_is_json_debris(cand):
        return ""
    if _bk_fix51_is_short_valid_visual_text(cand):
        return cand
    debris_fn = globals().get("_bk_fix53_is_reasoning_debris")
    if callable(debris_fn):
        try:
            if debris_fn(cand):
                return ""
        except Exception:
            pass
    if _bk_fix51_is_manual_overlay_source(cand):
        return ""
    for fn_name in ("_bk_fix50_candidate_visible_text", "_bk_lm_behavior_candidate_visible_text"):
        fn = globals().get(fn_name)
        if callable(fn):
            try:
                out = _clean_ocr_text(fn(worker, cand) or "")
                if out:
                    return out
            except Exception:
                pass
    try:
        bad_fn = globals().get("_bk_fix45_is_bad_candidate")
        if callable(bad_fn) and bad_fn(worker, cand):
            return ""
    except Exception:
        pass
    return cand




def _bk_fix53_is_reasoning_debris(text: str) -> bool:
    t = _clean_ocr_text(text or "")
    if not t:
        return False
    low = t.casefold()
    if "**" in t or "```" in t:
        return True
    bad_fragments = (
        "analyze the request", "analyse the request", "analyze request",
        "request:", "reasoning", "reasoning_content", "step-by-step",
        "step by step", "the image", "the crop", "visible text", "ocr task",
        "i need", "i should", "i can", "the answer", "final answer",
        "assistant", "user asked", "markdown", "json schema",
    )
    if any(fragment in low for fragment in bad_fragments):
        return True
    if re.match(r"^\s*\d+[.)]\s*[A-Za-z*#]", t):
        return True
    if re.match(r"^\s*[-*•]\s+", t):
        return True
    return False


def _bk_fix53_is_clean_manual_ocr_value(text: str) -> bool:
    t = _clean_ocr_text(text or "")
    if not t or "\n" in t or _bk_fix51_is_json_debris(t):
        return False
    if _bk_fix53_is_reasoning_debris(t):
        return False
    if len(t) > 120:
        return False
    if _bk_fix51_is_manual_overlay_source(t):
        return False
    # OCR text may contain names, dates, punctuation and short numbers, but not markdown/control text.
    return bool(re.search(r"[0-9A-Za-zÀ-ÿÄÖÜäöüßIVXLCDMivxlcdm]", t))


def _bk_fix52_collect_response_texts(data: dict):
    texts = []
    if not isinstance(data, dict):
        return texts
    choices = data.get("choices")
    if not isinstance(choices, list):
        return texts
    for choice in choices:
        if not isinstance(choice, dict):
            continue
        message = choice.get("message")
        if isinstance(message, dict):
            for key in ("content", "text", "output_text", "reasoning_content"):
                value = _bk_fix51_flatten_chat_value(message.get(key))
                if value:
                    texts.append(value)
        for key in ("content", "text", "output_text"):
            value = _bk_fix51_flatten_chat_value(choice.get(key))
            if value:
                texts.append(value)
    return texts


def _bk_fix52_extract_short_ocr_from_free_text(text: str) -> str:
    cleaned = str(text or "").strip()
    if not cleaned:
        return ""
    cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL).strip()
    direct = _bk_fix51_parse_single_text(cleaned)
    if _bk_fix51_is_short_valid_visual_text(direct) and not _bk_fix53_is_reasoning_debris(direct):
        return direct

    quoted = re.findall(r"[\"'`„“”]([^\"'`„“”]{1,24})[\"'`„“”]", cleaned)
    for value in reversed(quoted):
        value = _clean_ocr_text(value)
        if _bk_fix51_is_short_valid_visual_text(value) and not _bk_fix53_is_reasoning_debris(value):
            return value

    phrase_patterns = [
        r"(?:sichtbare[rnms]?\s+)?(?:text|inhalt|answer|result|ocr|wert)\s*(?:ist|is|=|:)\s*([A-Za-zÀ-ÿÄÖÜäöüßIVXLCDMivxlcdm0-9][A-Za-zÀ-ÿÄÖÜäöüßIVXLCDMivxlcdm0-9.]{0,15})",
        r"(?:lies|read|transkribiere|transcribe)[^\n]{0,60}?\b([0-9]{1,4}\.|[0-9]{1,4}|[IVXLCDMivxlcdm]{1,10}\.?)\b",
    ]
    for pattern in phrase_patterns:
        matches = re.findall(pattern, cleaned, flags=re.IGNORECASE)
        for value in reversed(matches):
            if isinstance(value, tuple):
                value = next((x for x in value if x), "")
            value = _clean_ocr_text(value)
            if _bk_fix51_is_short_valid_visual_text(value) and not _bk_fix53_is_reasoning_debris(value):
                return value

    # Prüfe nur kurze, saubere Zeilen. Reasoning-Zeilen wie "1. **Analyze..." werden ignoriert.
    lines = [_clean_ocr_text(line) for line in re.split(r"[\r\n]+", cleaned)]
    for line in reversed([line for line in lines if line]):
        if _bk_fix53_is_reasoning_debris(line):
            continue
        if _bk_fix51_is_short_valid_visual_text(line):
            return line
        tokens = re.findall(r"(?<![A-Za-zÀ-ÿ0-9])(?:\d{1,4}\.?|[IVXLCDMivxlcdm]{1,10}\.)(?![A-Za-zÀ-ÿ0-9*])", line)
        for value in reversed(tokens):
            value = _clean_ocr_text(value)
            if _bk_fix51_is_short_valid_visual_text(value):
                return value
    return ""

def _bk_fix52_extract_manual_ocr_response(worker, data: dict) -> str:
    for raw in _bk_fix52_collect_response_texts(data):
        short = _bk_fix52_extract_short_ocr_from_free_text(raw)
        if short:
            return short
        text = _bk_fix51_parse_single_text(raw)
        if _bk_fix53_is_clean_manual_ocr_value(text):
            return _clean_ocr_text(text)
    try:
        raw = _bk_fix51_extract_message_content(worker, data)
        short = _bk_fix52_extract_short_ocr_from_free_text(raw)
        if short:
            return short
        text = _bk_fix51_parse_single_text(raw)
        if _bk_fix53_is_clean_manual_ocr_value(text):
            return _clean_ocr_text(text)
    except Exception:
        pass
    return ""

def _bk_fix52_payload_with_optional_reasoning_disabled(base_payload: dict, disable_reasoning: bool) -> dict:
    payload = dict(base_payload)
    if disable_reasoning:
        # OpenAI-kompatible Backends nutzen unterschiedliche Schalter. Unbekannte
        # Felder werden von LM Studio/OpenRouter in der Regel ignoriert; unterstützte
        # Qwen-Backends schalten damit das Denken für diesen Mini-OCR-Fall ab.
        payload["reasoning"] = {"effort": "none"}
        payload["thinking"] = False
        payload["think"] = False
        payload["enable_thinking"] = False
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    return payload


def _bk_fix51_behavior_for_worker(worker) -> dict:
    fn = globals().get("_bk_lm_behavior_for_worker")
    if callable(fn):
        try:
            return dict(fn(worker, getattr(worker, "lm_behavior_scope", "current_line")) or {})
        except Exception:
            pass
    return {}


def _bk_fix51_request_visual_overlay_ocr(worker, rv, local_pos: int = 0) -> str:
    # Reines Box-OCR für manuell gezeichnete Placeholder-Zeilen.
    # Keine Seiten-OCR, kein Block-Kontext, keine Merge-Entscheidung.
    # Der Bildausschnitt bleibt bewusst knapp, damit benachbarte Zeilen/Labels
    # nicht in die Antwort geraten.
    pad_x = 3
    pad_y = 3
    line_data_url = _crop_overlay_box_to_data_url_strict(
        worker.path,
        rv,
        pad_x=pad_x,
        pad_y=pad_y,
        extra_context_y=0,
    )
    idx = int(getattr(rv, "idx", local_pos) if getattr(rv, "idx", None) is not None else local_pos)

    system_prompt = (
        "/no_think\n"
        "Du bist OCR. Lies nur den Bildausschnitt. "
        "Antworte ausschließlich mit dem exakt sichtbaren Text in dieser einen Box. "
        "Keine Analyse, keine Erklärung, kein Markdown, kein Kontext, keine Korrektur anhand alter Texte."
    )
    user_prompt = (
        f"/no_think\nZeile {idx}: Gib nur den sichtbaren Text zurück. "
        "Auch sehr kurze Inhalte wie 2, 2., 3., U, I, II oder III sind vollständige gültige Antworten. "
        "Nur der OCR-Wert, sonst nichts."
    )

    attempts = [
        (None, 96, True),
        (worker._response_format_single_text(), 128, True),
        (None, 128, False),
    ]
    last_error = None
    for response_format, max_tokens, disable_reasoning in attempts:
        base_payload = {
            "model": worker.lm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": line_data_url}},
                ]},
            ],
            **worker._build_sampling_payload(
                response_format=response_format,
                override_max_tokens=max_tokens,
            ),
        }
        payload = _bk_fix52_payload_with_optional_reasoning_disabled(base_payload, disable_reasoning)
        try:
            worker._bk_strict_overlay_transcription_active = True
            worker._bk_active_overlay_crop_data_url = line_data_url
            try:
                data = worker._post_json(payload)
            finally:
                worker._bk_active_overlay_crop_data_url = None
            visible = _bk_fix52_extract_manual_ocr_response(worker, data)
            if visible:
                return visible
        except Exception as exc:
            last_error = exc
            try:
                print(f"FIX51 manual single-line OCR failed response_format={bool(response_format)} disable_reasoning={disable_reasoning}: {exc}")
            except Exception:
                pass
    if last_error is not None:
        raise last_error
    return ""


try:
    _BK_FIX51_PREV_REQUEST_OVERLAY = _bk_fix46_request_overlay_box_revision
except Exception:
    _BK_FIX51_PREV_REQUEST_OVERLAY = None


def _bk_fix46_request_overlay_box_revision(self, rv, page_context_lines, local_pos: int, total: int) -> str:
    source_text = _clean_ocr_text(getattr(rv, "text", "") or "")
    if getattr(rv, "bbox", None) and _bk_fix51_is_manual_overlay_source(source_text):
        try:
            visual = _bk_fix51_request_visual_overlay_ocr(self, rv, local_pos)
            if visual:
                return visual
        except Exception as exc:
            try:
                print(f"FIX51 manual overlay OCR failed line {local_pos}: {exc}")
            except Exception:
                pass
        return ""
    if callable(_BK_FIX51_PREV_REQUEST_OVERLAY):
        return _BK_FIX51_PREV_REQUEST_OVERLAY(self, rv, page_context_lines, local_pos, total)
    return source_text


try:
    _BK_FIX51_PREV_SANITY_MERGE = _bk_fix46_sanity_merge_line
except Exception:
    _BK_FIX51_PREV_SANITY_MERGE = None


def _bk_fix46_sanity_merge_line(self, kraken_text: str, lm_box_text: str, page_context_text: str = "", prev_final_text: str = "", full_page_context: str = "", page_index_aligned: bool = True) -> str:
    kt = _clean_ocr_text(kraken_text or "")
    lt = _clean_ocr_text(lm_box_text or "")
    pt = _clean_ocr_text(page_context_text or "")
    if _bk_fix51_is_manual_overlay_source(kt):
        lm_visible = _bk_fix51_candidate_visible_text(self, lt)
        page_visible = _bk_fix51_candidate_visible_text(self, pt) if "\n" not in pt else ""
        return lm_visible or page_visible or ""
    if callable(_BK_FIX51_PREV_SANITY_MERGE):
        try:
            return _BK_FIX51_PREV_SANITY_MERGE(self, kt, lt, pt, prev_final_text, full_page_context, page_index_aligned)
        except TypeError:
            return _BK_FIX51_PREV_SANITY_MERGE(self, kt, lt, pt, prev_final_text)
    return lt or kt or pt


try:
    _BK_FIX51_PREV_AI_RUN = AIRevisionWorker.run
except Exception:
    _BK_FIX51_PREV_AI_RUN = None


def _bk_fix51_manual_single_line_worker(worker) -> bool:
    try:
        recs = list(getattr(worker, "recs", []) or [])
        if len(recs) != 1:
            return False
        rv = recs[0]
        return bool(getattr(rv, "bbox", None) and _bk_fix51_is_manual_overlay_source(getattr(rv, "text", "") or ""))
    except Exception:
        return False


def _bk_fix51_ai_revision_run(self):
    # Exakter Sonderpfad für eine manuell gezeichnete Placeholder-Zeile:
    # nur diese Box erneut lesen und danach sofort zurückgeben. Kein Seitenkontext,
    # kein Full-Page-OCR, keine Kraken/LM-Merge-Logik als Fallback.
    if _bk_fix51_manual_single_line_worker(self):
        rv = self.recs[0]
        try:
            if self._cancelled or self.isInterruptionRequested():
                self.failed_revision.emit(self.path, self._tr("msg_ai_cancelled"))
                return
            self.status_changed.emit(self._tr("ai_status_fix46_overlay_line", 1, 1, os.path.basename(self.path)))
            self.progress_changed.emit(10)
            visual = _bk_fix51_request_visual_overlay_ocr(self, rv, 0)
            visual = _bk_fix51_candidate_visible_text(self, visual)
            if visual:
                try:
                    self.status_changed.emit(self._tr("ai_status_fix46_finalize", os.path.basename(self.path)))
                except Exception:
                    pass
                self.progress_changed.emit(100)
                self.finished_revision.emit(self.path, [visual])
                return
            try:
                self.status_changed.emit(self._tr("ai_status_fix46_finalize", os.path.basename(self.path)))
            except Exception:
                pass
            self.progress_changed.emit(100)
            self.finished_revision.emit(self.path, [_clean_ocr_text(getattr(rv, "text", "") or "")])
            return
        except Exception as exc:
            try:
                print(f"FIX51 direct manual single-line run failed without fallback: {exc}")
            except Exception:
                pass
            self.failed_revision.emit(self.path, str(exc))
            return
    if callable(_BK_FIX51_PREV_AI_RUN):
        return _BK_FIX51_PREV_AI_RUN(self)
    return None




try:
    _BK_FIX51_PREV_SINGLE_REREAD = AIRevisionWorker._request_single_line_reread
except Exception:
    _BK_FIX51_PREV_SINGLE_REREAD = None


def _bk_fix51_request_single_line_reread(self, line_data_url: str, idx: int, current_text: str = "") -> str:
    if _bk_fix51_is_manual_overlay_source(current_text):
        # Wird nur genutzt, falls ein älterer Pfad doch noch _request_single_line_reread
        # statt des direkten Sonderpfads verwendet.
        system_prompt = "/no_think\nDu bist OCR. Antworte nur mit dem sichtbaren Text der einen Box. Keine Analyse, kein Markdown."
        user_prompt = f"/no_think\nZeile {idx}: nur den OCR-Wert, keine Erklärung."
        payload = {
            "model": self.lm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": line_data_url}},
                ]},
            ],
            **self._build_sampling_payload(response_format=None, override_max_tokens=96),
        }
        payload = _bk_fix52_payload_with_optional_reasoning_disabled(payload, True)
        data = self._post_json(payload)
        return _bk_fix52_extract_manual_ocr_response(self, data)
    if callable(_BK_FIX51_PREV_SINGLE_REREAD):
        return _BK_FIX51_PREV_SINGLE_REREAD(self, line_data_url, idx, current_text)
    return ""

try:
    AIRevisionWorker._extract_message_content = _bk_fix51_extract_message_content
    AIRevisionWorker._request_single_line_reread = _bk_fix51_request_single_line_reread
    AIRevisionWorker.run = _bk_fix51_ai_revision_run
except Exception:
    pass


def _bk_lm_behavior_is_placeholder_source_text(text: str) -> bool:
    return _bk_fix51_is_manual_overlay_source(text)


__all__ = [
    "_bk_fix46_request_overlay_box_revision",
    "_bk_fix46_sanity_merge_line",
    "_bk_fix51_ai_revision_run",
    "_bk_fix51_behavior_for_worker",
    "_bk_fix51_candidate_visible_text",
    "_bk_fix51_extract_message_content",
    "_bk_fix51_flatten_chat_value",
    "_bk_fix51_is_json_debris",
    "_bk_fix51_is_manual_overlay_source",
    "_bk_fix51_is_short_valid_visual_text",
    "_bk_fix51_manual_single_line_worker",
    "_bk_fix51_request_single_line_reread",
    "_bk_fix51_parse_single_text",
    "_bk_fix51_request_visual_overlay_ocr",
    "_bk_fix52_collect_response_texts",
    "_bk_fix52_extract_manual_ocr_response",
    "_bk_fix52_extract_short_ocr_from_free_text",
    "_bk_fix52_payload_with_optional_reasoning_disabled",
    "_bk_fix53_is_clean_manual_ocr_value",
    "_bk_fix53_is_reasoning_debris",
    "_bk_lm_behavior_is_placeholder_source_text",
]
register_globals('bk', globals(), __all__)
