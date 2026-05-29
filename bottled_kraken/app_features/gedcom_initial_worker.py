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
def _bk_gedcom_install_translations():
    for lang, mapping in _BK_GEDCOM_PROMPT_DEFAULTS.items():
        try:
            translation.TRANSLATIONS.setdefault(lang, {}).update(mapping)
        except Exception:
            try:
                TRANSLATIONS.setdefault(lang, {}).update(mapping)
            except Exception:
                pass
    try:
        existing_prompt_keys = [k for k, _label in _BK_LM_PROMPT_KEYS]
        extra = []
        if "ai_prompt_gedcom_system" not in existing_prompt_keys:
            extra.append(("ai_prompt_gedcom_system", "lm_prompt_gedcom_system"))
        if "ai_prompt_gedcom_user" not in existing_prompt_keys:
            extra.append(("ai_prompt_gedcom_user", "lm_prompt_gedcom_user"))
        if extra:
            globals()["_BK_LM_PROMPT_KEYS"] = tuple(_BK_LM_PROMPT_KEYS) + tuple(extra)
    except Exception:
        pass
    try:
        existing_token_keys = [k for k, _label in _BK_LM_TOKEN_KEYS]
        if "gedcom" not in existing_token_keys:
            globals()["_BK_LM_TOKEN_KEYS"] = tuple(_BK_LM_TOKEN_KEYS) + (("gedcom", "lm_token_gedcom"),)
    except Exception:
        pass
    try:
        _BK_LM_TOKEN_DEFAULTS.setdefault("gedcom", 4500)
    except Exception:
        pass
    try:
        for lang, mapping in _BK_GEDCOM_PROMPT_DEFAULTS.items():
            if "_BK_LM_OPTIONS_TEXTS" in globals():
                _BK_LM_OPTIONS_TEXTS.setdefault(lang, {}).update({
                    "lm_token_gedcom": mapping["act_lm_generate_gedcom"],
                    "lm_prompt_gedcom_system": mapping["lm_prompt_gedcom_system"],
                    "lm_prompt_gedcom_user": mapping["lm_prompt_gedcom_user"],
                })
    except Exception:
        pass
def _bk_gedcom_text(self, key: str, *args) -> str:
    lang = getattr(self, "current_lang", translation.DEFAULT_LANGUAGE)
    data = _BK_GEDCOM_PROMPT_DEFAULTS.get(lang) or _BK_GEDCOM_PROMPT_DEFAULTS["de"]
    txt = data.get(key, _BK_GEDCOM_PROMPT_DEFAULTS["de"].get(key, key))
    try:
        return txt.format(*args) if args else txt
    except Exception:
        return txt
class BKLocalGedcomWorker(QThread):
    finished_gedcom = Signal(str, str)
    failed_gedcom = Signal(str, str)
    progress_changed = Signal(int)
    status_changed = Signal(str)
    def __init__(
        self,
        *,
        path: str,
        source_text: str,
        lm_model: str,
        endpoint: str,
        enable_thinking: bool = False,
        temperature: float = 0.0,
        top_p: float = 0.2,
        top_k: int = 1,
        presence_penalty: float = 0.0,
        repetition_penalty: float = 1.0,
        min_p: float = 0.0,
        max_tokens: int = 4500,
        tr_func=None,
        parent=None,
    ):
        super().__init__(parent)
        self._tr = tr_func or translation.make_tr(translation.DEFAULT_LANGUAGE)
        self.path = path
        self.source_text = (source_text or "").strip()
        self.lm_model = lm_model
        self.endpoint = endpoint
        self.enable_thinking = bool(enable_thinking)
        self.temperature = float(temperature)
        self.top_p = float(top_p)
        self.top_k = int(top_k)
        self.presence_penalty = float(presence_penalty)
        self.repetition_penalty = float(repetition_penalty)
        self.min_p = float(min_p)
        self.max_tokens = int(max_tokens)
        self._cancelled = False
        self._active_conn = None
    def cancel(self):
        self._cancelled = True
        self.requestInterruption()
        conn = self._active_conn
        self._active_conn = None
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
    def _build_sampling_payload(self) -> dict:
        payload = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
            "max_tokens": max(1, int(self.max_tokens or 4500)),
            "stream": False,
        }
        if self.top_k > 0:
            payload["top_k"] = self.top_k
        if self.min_p > 0:
            payload["min_p"] = self.min_p
        if self.repetition_penalty != 1.0:
            payload["repetition_penalty"] = self.repetition_penalty
        if self.enable_thinking:
            payload["reasoning"] = {"effort": "medium"}
        return payload
    def _post_json(self, payload: dict) -> dict:
        if self._cancelled or self.isInterruptionRequested():
            raise RuntimeError(self._tr("msg_gedcom_cancelled"))
        body = json.dumps(payload).encode("utf-8")
        parsed = urllib.parse.urlparse(self.endpoint)
        if parsed.scheme not in ("http", "https"):
            raise RuntimeError(self._tr("ai_err_bad_scheme", parsed.scheme))
        host = parsed.hostname
        port = parsed.port
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query
        if not host:
            raise RuntimeError(self._tr("ai_err_invalid_endpoint"))
        conn = None
        try:
            if parsed.scheme == "https":
                conn = http.client.HTTPSConnection(host, port or 443, timeout=600)
            else:
                conn = http.client.HTTPConnection(host, port or 80, timeout=600)
            self._active_conn = conn
            conn.request(
                "POST",
                path,
                body=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer lm-studio",
                },
            )
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_gedcom_cancelled"))
            resp = conn.getresponse()
            raw = resp.read().decode("utf-8", errors="replace")
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_gedcom_cancelled"))
            if resp.status >= 400:
                raise RuntimeError(self._tr("ai_err_http", resp.status, raw))
            return json.loads(raw)
        except socket.timeout:
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_gedcom_cancelled"))
            raise RuntimeError(self._tr("ai_err_timeout"))
        except json.JSONDecodeError as e:
            raise RuntimeError(self._tr("ai_err_invalid_json", e))
        finally:
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass
            if self._active_conn is conn:
                self._active_conn = None
    def _extract_message_content(self, data: dict) -> str:
        choices = data.get("choices") if isinstance(data, dict) else None
        if not isinstance(choices, list) or not choices:
            raise RuntimeError(self._tr("ai_err_no_choices", json.dumps(data, ensure_ascii=False)[:3000]))
        choice0 = choices[0] or {}
        message = choice0.get("message", {}) if isinstance(choice0, dict) else {}
        content = message.get("content", "") if isinstance(message, dict) else ""
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, str) and part.strip():
                    parts.append(part.strip())
                elif isinstance(part, dict):
                    for key in ("text", "content", "output_text"):
                        value = part.get(key)
                        if isinstance(value, str) and value.strip():
                            parts.append(value.strip())
            return "\n".join(parts).strip()
        return str(content or "").strip()
    def _clean_gedcom(self, raw: str) -> str:
        text = str(raw or "").strip()
        text = re.sub(r"^```(?:gedcom|ged)?\s*", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"\s*```$", "", text).strip()
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = [ln.rstrip() for ln in text.split("\n")]
        head_idx = next((i for i, ln in enumerate(lines) if ln.strip().upper().startswith("0 HEAD")), None)
        if head_idx is not None:
            lines = lines[head_idx:]
        trlr_idx = next((i for i, ln in enumerate(lines) if ln.strip().upper().startswith("0 TRLR")), None)
        if trlr_idx is not None:
            lines = lines[:trlr_idx + 1]
        text = "\n".join(ln for ln in lines if ln.strip()).strip()
        if not text:
            raise RuntimeError(self._tr("warn_no_text_for_gedcom"))
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
        if not re.search(r"(?m)^0\s+TRLR\b", text, flags=re.IGNORECASE):
            text = text.rstrip() + "\n0 TRLR"
        return text.strip() + "\n"
    def run(self):
        try:
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_gedcom_cancelled"))
            if not self.source_text:
                raise RuntimeError(self._tr("warn_no_text_for_gedcom"))
            self.progress_changed.emit(5)
            self.status_changed.emit(self._tr("msg_gedcom_started"))
            system_prompt = self._tr("ai_prompt_gedcom_system")
            user_prompt = self._tr("ai_prompt_gedcom_user", self.source_text)
            payload = {
                "model": self.lm_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                **self._build_sampling_payload(),
            }
            self.progress_changed.emit(15)
            data = self._post_json(payload)
            self.progress_changed.emit(85)
            content = self._extract_message_content(data)
            gedcom_text = self._clean_gedcom(content)
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_gedcom_cancelled"))
            self.progress_changed.emit(100)
            self.finished_gedcom.emit(self.path, gedcom_text)
        except Exception as exc:
            self.failed_gedcom.emit(self.path, str(exc))
__all__ = [
    'BKLocalGedcomWorker',
    '_BK_GEDCOM_PROMPT_DEFAULTS',
    '_BK_GEDCOM_REVIEW_TEXTS',
    '_BK_GEDCOM_ROBUST_TEXTS',
    '_BK_GEDCOM_SAVE_FIX_TEXTS',
    '_BK_GEDCOM_STRUCTURED_TEXTS',
    '_BK_GEDCOM_VISION_TEXTS',
    '_BK_PROMPT_UX_EXTRA_TEXTS',
    '_bk_gedcom_install_translations',
    '_bk_gedcom_text',
]
register_globals('bk', globals(), __all__)
