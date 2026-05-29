from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
"""GEDCOM-Erzeugung über lokales LM.
Ergänzt im LM-Überarbeitungsmenü den Eintrag "GEDCOM erzeugen" unterhalb
von "Neo4j-JSON erzeugen" und bindet die GEDCOM-Prompts in den bestehenden
Prompt-Editor ein.
"""
from bottled_kraken.translations.translation_loader import load_named_language_mapping as _load_translation_mapping
_BK_GEDCOM_PROMPT_DEFAULTS = _load_translation_mapping("gedcom_texts", "BK_GEDCOM_PROMPT_DEFAULTS")
_BK_GEDCOM_VISION_TEXTS = _load_translation_mapping("gedcom_texts", "BK_GEDCOM_VISION_TEXTS")
_BK_GEDCOM_SAVE_FIX_TEXTS = _load_translation_mapping("gedcom_texts", "BK_GEDCOM_SAVE_FIX_TEXTS")
_BK_GEDCOM_ROBUST_TEXTS = _load_translation_mapping("gedcom_texts", "BK_GEDCOM_ROBUST_TEXTS")
_BK_GEDCOM_STRUCTURED_TEXTS = _load_translation_mapping("gedcom_texts", "BK_GEDCOM_STRUCTURED_TEXTS")
_BK_GEDCOM_REVIEW_TEXTS = _load_translation_mapping("gedcom_texts", "BK_GEDCOM_REVIEW_TEXTS")
_BK_PROMPT_UX_EXTRA_TEXTS = _load_translation_mapping("gedcom_texts", "BK_PROMPT_UX_EXTRA_TEXTS")
def _bk_gedcom_robust_install_translations():
    for lang, mapping in _BK_GEDCOM_ROBUST_TEXTS.items():
        try:
            translation.TRANSLATIONS.setdefault(lang, {}).update(mapping)
        except Exception:
            try:
                TRANSLATIONS.setdefault(lang, {}).update(mapping)
            except Exception:
                pass
        try:
            if "_BK_GEDCOM_PROMPT_DEFAULTS" in globals():
                _BK_GEDCOM_PROMPT_DEFAULTS.setdefault(lang, {}).update(mapping)
        except Exception:
            pass
def _bk_gedcom_robust_tr(self, key: str, *args) -> str:
    try:
        return self._tr(key, *args)
    except Exception:
        lang = getattr(self, "current_lang", translation.DEFAULT_LANGUAGE) if hasattr(self, "current_lang") else "de"
        data = _BK_GEDCOM_ROBUST_TEXTS.get(lang) or _BK_GEDCOM_ROBUST_TEXTS["de"]
        text = data.get(key, _BK_GEDCOM_ROBUST_TEXTS["de"].get(key, key))
        try:
            return text.format(*args) if args else text
        except Exception:
            return text
def _bk_gedcom_extract_text_from_jsonish(value) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        preferred = (
            "gedcom", "GEDCOM", "ged", "file", "output", "result", "text", "content", "message", "response"
        )
        for key in preferred:
            item = value.get(key)
            text = _bk_gedcom_extract_text_from_jsonish(item)
            if text:
                return text
        parts = []
        for item in value.values():
            text = _bk_gedcom_extract_text_from_jsonish(item)
            if text:
                parts.append(text)
        return "\n".join(parts).strip()
    if isinstance(value, (list, tuple)):
        parts = []
        for item in value:
            text = _bk_gedcom_extract_text_from_jsonish(item)
            if text:
                parts.append(text)
        return "\n".join(parts).strip()
    return ""
def _bk_gedcom_strip_code_fences(text: str) -> str:
    text = str(text or "").strip()
    text = re.sub(r"^```(?:gedcom|ged|text|json)?\s*", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"\s*```$", "", text).strip()
    return text
def _bk_gedcom_unwrap_model_text(raw: str) -> str:
    text = _bk_gedcom_strip_code_fences(raw)
    try:
        obj = json.loads(text)
        value = _bk_gedcom_extract_text_from_jsonish(obj)
        if value:
            text = _bk_gedcom_strip_code_fences(value)
    except Exception:
        pass
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()
def _bk_gedcom_has_structural_tags(text: str) -> bool:
    txt = str(text or "")
    patterns = (
        r"(?m)^0\s+HEAD\b",
        r"(?m)^0\s+@[^@\s]+@\s+INDI\b",
        r"(?m)^0\s+@[^@\s]+@\s+FAM\b",
        r"(?m)^1\s+NAME\b",
        r"(?m)^0\s+TRLR\b",
    )
    return any(re.search(p, txt, flags=re.IGNORECASE) for p in patterns)
def _bk_gedcom_extract_level_lines(text: str) -> str:
    lines = [ln.rstrip() for ln in str(text or "").split("\n")]
    head_idx = next((i for i, ln in enumerate(lines) if ln.strip().upper().startswith("0 HEAD")), None)
    if head_idx is not None:
        lines = lines[head_idx:]
    trlr_idx = next((i for i, ln in enumerate(lines) if ln.strip().upper().startswith("0 TRLR")), None)
    if trlr_idx is not None:
        lines = lines[:trlr_idx + 1]
    level_line_re = re.compile(r"^\s*[0-9]+\s+")
    if any(level_line_re.match(ln or "") for ln in lines):
        lines = [ln.strip() for ln in lines if level_line_re.match(ln or "")]
    return "\n".join(ln for ln in lines if ln.strip()).strip()
def _bk_gedcom_escape_note_lines(text: str, max_chars: int = 9000) -> List[str]:
    text = _clean_ocr_text(str(text or "")) if "_clean_ocr_text" in globals() else str(text or "")
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if len(text) > max_chars:
        text = text[:max_chars].rstrip() + " ..."
    chunks = []
    for raw_line in text.split("\n") or [text]:
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        while len(raw_line) > 180:
            cut = raw_line[:180]
            chunks.append(cut)
            raw_line = raw_line[180:].lstrip()
        if raw_line:
            chunks.append(raw_line)
    return chunks or ["Keine verwertbare Modellantwort."]
def _bk_gedcom_make_fallback_file(worker, raw: str = "", source_text: str = "") -> str:
    note_title = worker._tr("gedcom_fallback_note_title") if hasattr(worker, "_tr") else "GEDCOM fallback"
    note_lines = _bk_gedcom_escape_note_lines("\n\n".join(x for x in (note_title, raw, source_text) if str(x or "").strip()))
    lines = [
        "0 HEAD",
        "1 SOUR BottledKraken",
        "1 GEDC",
        "2 VERS 5.5.1",
        "2 FORM LINEAGE-LINKED",
        "1 CHAR UTF-8",
        "0 @I1@ INDI",
        "1 NAME Unbekannt //",
        "1 _BK_FALLBACK Y",
    ]
    if note_lines:
        lines.append("1 NOTE " + note_lines[0])
        for ln in note_lines[1:]:
            lines.append("2 CONT " + ln)
    lines.append("0 TRLR")
    return "\n".join(lines).strip() + "\n"
def _bk_gedcom_finalize_level_text(text: str) -> str:
    text = _bk_gedcom_extract_level_lines(text)
    header = (
        "0 HEAD\n"
        "1 SOUR BottledKraken\n"
        "1 GEDC\n"
        "2 VERS 5.5.1\n"
        "2 FORM LINEAGE-LINKED\n"
        "1 CHAR UTF-8"
    )
    if not re.search(r"(?m)^0\s+HEAD\b", text, flags=re.IGNORECASE):
        text = header + "\n" + text
    else:
        if not re.search(r"(?m)^1\s+SOUR\b", text, flags=re.IGNORECASE):
            text = re.sub(r"(?m)^(0\s+HEAD\b.*)$", r"\1\n1 SOUR BottledKraken", text, count=1)
        if not re.search(r"(?m)^1\s+GEDC\b", text, flags=re.IGNORECASE):
            text = re.sub(r"(?m)^(0\s+HEAD\b.*)$", r"\1\n1 GEDC\n2 VERS 5.5.1\n2 FORM LINEAGE-LINKED", text, count=1)
        if not re.search(r"(?m)^1\s+CHAR\s+UTF-?8\b", text, flags=re.IGNORECASE):
            text = re.sub(r"(?m)^(0\s+HEAD\b.*)$", r"\1\n1 CHAR UTF-8", text, count=1)
    if not re.search(r"(?m)^0\s+TRLR\b", text, flags=re.IGNORECASE):
        text = text.rstrip() + "\n0 TRLR"
    return text.strip() + "\n"
def _bk_gedcom_clean_robust(self, raw: str, *, allow_fallback: bool = True) -> str:
    text = _bk_gedcom_unwrap_model_text(raw)
    level_text = _bk_gedcom_extract_level_lines(text)
    if level_text and _bk_gedcom_has_structural_tags(level_text):
        return _bk_gedcom_finalize_level_text(level_text)
    if allow_fallback:
        try:
            self.status_changed.emit(self._tr("log_gedcom_fallback_note"))
        except Exception:
            pass
        return _bk_gedcom_make_fallback_file(self, raw=text, source_text=getattr(self, "source_text", ""))
    raise RuntimeError(self._tr("warn_gedcom_no_output"))
def _bk_gedcom_strict_appendix(self) -> str:
    return (
        "\n\nZWINGENDE AUSGABEFORMAT-REGELN / STRICT OUTPUT RULES:\n"
        "- Antworte ausschließlich mit GEDCOM-Levelzeilen.\n"
        "- Jede Ausgabezeile beginnt mit einer Zahl: 0, 1, 2 oder 3.\n"
        "- Keine Einleitung, keine Erklärung, kein Markdown, keine JSON-Ausgabe.\n"
        "- Erzeuge immer mindestens: 0 HEAD, mindestens einen INDI-Datensatz, 0 TRLR.\n"
        "- Wenn keine Person sicher erkannt wird: 0 @I1@ INDI, 1 NAME Unbekannt //, 1 NOTE Unsichere Lesung.\n"
    )
def _bk_gedcom_build_payload_robust(self, image_data_url: str = "") -> dict:
    ocr_text = self.source_text or "[Kein OCR-Text vorhanden. Bitte primär das Seitenbild auswerten.]"
    system_prompt = self._tr("ai_prompt_gedcom_system") + _bk_gedcom_strict_appendix(self)
    user_prompt = self._tr("ai_prompt_gedcom_user", ocr_text) + _bk_gedcom_strict_appendix(self)
    if image_data_url:
        user_content = [
            {"type": "text", "text": user_prompt},
            {"type": "image_url", "image_url": {"url": image_data_url}},
        ]
    else:
        user_content = user_prompt
    return {
        "model": self.lm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        **self._build_sampling_payload(),
    }
def _bk_gedcom_build_repair_payload(self, previous_response: str, image_data_url: str = "") -> dict:
    ocr_text = self.source_text or "[Kein OCR-Text vorhanden.]"
    repair_text = (
        "Die vorherige Antwort war keine importierbare GEDCOM-Datei.\n"
        "Wandle dieselben Informationen jetzt strikt in GEDCOM 5.5.1 um.\n"
        "Antworte nur mit GEDCOM-Levelzeilen. Keine Erklärung. Kein Markdown.\n\n"
        "Wenn keine Person sicher lesbar ist, erzeuge wenigstens einen Platzhalter-INDI mit NOTE.\n\n"
        "OCR-Kontext:\n" + ocr_text + "\n\n"
        "Vorherige Modellantwort:\n" + str(previous_response or "")[:12000]
    ) + _bk_gedcom_strict_appendix(self)
    if image_data_url:
        user_content = [
            {"type": "text", "text": repair_text},
            {"type": "image_url", "image_url": {"url": image_data_url}},
        ]
    else:
        user_content = repair_text
    return {
        "model": self.lm_model,
        "messages": [
            {"role": "system", "content": self._tr("ai_prompt_gedcom_system") + _bk_gedcom_strict_appendix(self)},
            {"role": "user", "content": user_content},
        ],
        **self._build_sampling_payload(),
    }
def _bk_gedcom_worker_run_robust(self):
    try:
        if self._cancelled or self.isInterruptionRequested():
            raise RuntimeError(self._tr("msg_gedcom_cancelled"))
        image_data_url = self._page_image_data_url()
        if not self.source_text and not image_data_url:
            raise RuntimeError(self._tr("warn_gedcom_needs_text_or_image"))
        self.progress_changed.emit(5)
        self.status_changed.emit(self._tr("msg_gedcom_started"))
        data = None
        image_error = None
        if image_data_url:
            try:
                self.progress_changed.emit(12)
                data = self._post_json(self._build_payload(image_data_url=image_data_url))
            except Exception as exc:
                image_error = exc
                if self._cancelled or self.isInterruptionRequested():
                    raise
                if not self.source_text or not _bk_gedcom_is_image_request_error(exc):
                    raise
                self.status_changed.emit(self._tr("log_gedcom_retry_text_only"))
        if data is None:
            if not self.source_text:
                raise RuntimeError(str(image_error) if image_error else self._tr("warn_gedcom_needs_text_or_image"))
            self.progress_changed.emit(25)
            data = self._post_json(self._build_payload(image_data_url=""))
        self.progress_changed.emit(72)
        content = self._extract_message_content(data)
        raw_unwrapped = _bk_gedcom_unwrap_model_text(content)
        level_text = _bk_gedcom_extract_level_lines(raw_unwrapped)
        if not (level_text and _bk_gedcom_has_structural_tags(level_text)):
            self.status_changed.emit(self._tr("log_gedcom_retry_strict"))
            self.progress_changed.emit(80)
            repair_payload = self._build_repair_payload(raw_unwrapped, image_data_url=image_data_url)
            repair_data = self._post_json(repair_payload)
            repair_content = self._extract_message_content(repair_data)
            repair_unwrapped = _bk_gedcom_unwrap_model_text(repair_content)
            repair_level_text = _bk_gedcom_extract_level_lines(repair_unwrapped)
            if repair_level_text and _bk_gedcom_has_structural_tags(repair_level_text):
                content = repair_unwrapped
            else:
                content = "\n\n".join(x for x in (raw_unwrapped, repair_unwrapped) if str(x or "").strip())
        self.progress_changed.emit(90)
        gedcom_text = self._clean_gedcom(content)
        if self._cancelled or self.isInterruptionRequested():
            raise RuntimeError(self._tr("msg_gedcom_cancelled"))
        self.progress_changed.emit(100)
        self.finished_gedcom.emit(self.path, gedcom_text)
    except Exception as exc:
        self.failed_gedcom.emit(self.path, str(exc))
def _bk_gedcom_has_indi_records(gedcom_text: str) -> bool:
    txt = str(gedcom_text or "")
    has_indi = bool(re.search(r"(?m)^0\s+@[^@\s]+@\s+INDI\b", txt, flags=re.IGNORECASE))
    is_fallback = bool(re.search(r"(?m)^1\s+_BK_FALLBACK\s+Y\b", txt, flags=re.IGNORECASE))
    return has_indi and not is_fallback
_bk_gedcom_robust_install_translations()
try:
    BKLocalGedcomWorker._build_payload = _bk_gedcom_build_payload_robust
    BKLocalGedcomWorker._build_repair_payload = _bk_gedcom_build_repair_payload
    BKLocalGedcomWorker._clean_gedcom = _bk_gedcom_clean_robust
    BKLocalGedcomWorker.run = _bk_gedcom_worker_run_robust
except Exception:
    pass
__all__ = [
    '_BK_GEDCOM_PROMPT_DEFAULTS',
    '_BK_GEDCOM_REVIEW_TEXTS',
    '_BK_GEDCOM_ROBUST_TEXTS',
    '_BK_GEDCOM_SAVE_FIX_TEXTS',
    '_BK_GEDCOM_STRUCTURED_TEXTS',
    '_BK_GEDCOM_VISION_TEXTS',
    '_BK_PROMPT_UX_EXTRA_TEXTS',
    '_bk_gedcom_build_payload_robust',
    '_bk_gedcom_build_repair_payload',
    '_bk_gedcom_clean_robust',
    '_bk_gedcom_escape_note_lines',
    '_bk_gedcom_extract_level_lines',
    '_bk_gedcom_extract_text_from_jsonish',
    '_bk_gedcom_finalize_level_text',
    '_bk_gedcom_has_indi_records',
    '_bk_gedcom_has_structural_tags',
    '_bk_gedcom_make_fallback_file',
    '_bk_gedcom_robust_install_translations',
    '_bk_gedcom_robust_tr',
    '_bk_gedcom_strict_appendix',
    '_bk_gedcom_strip_code_fences',
    '_bk_gedcom_unwrap_model_text',
    '_bk_gedcom_worker_run_robust',
]
register_globals('bk', globals(), __all__)
