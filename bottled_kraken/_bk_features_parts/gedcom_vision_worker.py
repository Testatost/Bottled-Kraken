"""GEDCOM-Funktionen für Bottled Kraken.

Konsolidierte Version aus den bisherigen Patch-Dateien 18-24:
- GEDCOM-Menüpunkt und Worker
- Vision-/Fallback-Erzeugung
- robuste Ausgabeprüfung
- strukturierte Datenextraktion
- Prüfen-/Bearbeiten-/Exportieren-Dialog
- optimierter Prompt-Editor für GEDCOM-Prompts

Die ursprüngliche Ausführungsreihenfolge bleibt innerhalb dieser Datei erhalten.
"""

# =============================================================================
# Ursprünglich: 18_bk_lm_gedcom_generation.py
# =============================================================================

"""GEDCOM-Erzeugung über lokales LM.

Ergänzt im LM-Überarbeitungsmenü den Eintrag "GEDCOM erzeugen" unterhalb
von "Neo4j-JSON erzeugen" und bindet die GEDCOM-Prompts in den bestehenden
Prompt-Editor ein.
"""

from .translation_sections.gedcom_texts import (
    BK_GEDCOM_PROMPT_DEFAULTS as _BK_GEDCOM_PROMPT_DEFAULTS,
    BK_GEDCOM_VISION_TEXTS as _BK_GEDCOM_VISION_TEXTS,
    BK_GEDCOM_SAVE_FIX_TEXTS as _BK_GEDCOM_SAVE_FIX_TEXTS,
    BK_GEDCOM_ROBUST_TEXTS as _BK_GEDCOM_ROBUST_TEXTS,
    BK_GEDCOM_STRUCTURED_TEXTS as _BK_GEDCOM_STRUCTURED_TEXTS,
    BK_GEDCOM_REVIEW_TEXTS as _BK_GEDCOM_REVIEW_TEXTS,
    BK_PROMPT_UX_EXTRA_TEXTS as _BK_PROMPT_UX_EXTRA_TEXTS,
)

def _bk_gedcom_apply_vision_translations():
    for lang, mapping in _BK_GEDCOM_VISION_TEXTS.items():
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
    try:
        _BK_LM_TOKEN_DEFAULTS["gedcom"] = 6000
    except Exception:
        pass

def _bk_gedcom_is_image_request_error(exc: Exception) -> bool:
    txt = str(exc or "").lower()
    return any(token in txt for token in (
        "image", "vision", "multimodal", "unsupported content", "content type", "image_url",
        "invalid type", "expected a string", "cannot process", "failed to process"
    ))

class BKLocalGedcomWorker(QThread):
    finished_gedcom = Signal(str, str)
    failed_gedcom = Signal(str, str)
    progress_changed = Signal(int)
    status_changed = Signal(str)

    def __init__(
        self,
        *,
        path: str,
        source_text: str = "",
        lm_model: str,
        endpoint: str,
        enable_thinking: bool = False,
        temperature: float = 0.0,
        top_p: float = 0.2,
        top_k: int = 1,
        presence_penalty: float = 0.0,
        repetition_penalty: float = 1.0,
        min_p: float = 0.0,
        max_tokens: int = 6000,
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
        self.max_tokens = int(max_tokens or 6000)
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
            "max_tokens": max(1, int(self.max_tokens or 6000)),
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

    def _page_image_data_url(self) -> str:
        if not self.path or not os.path.exists(self.path):
            return ""
        try:
            return _page_to_data_url(self.path, max_side=2300, image_format="JPEG", jpeg_quality=82)
        except Exception:
            try:
                return _page_to_data_url(self.path, max_side=1800, image_format="PNG")
            except Exception:
                return ""

    def _build_payload(self, image_data_url: str = "") -> dict:
        ocr_text = self.source_text or "[Kein OCR-Text vorhanden. Bitte primär das Seitenbild auswerten.]"
        system_prompt = self._tr("ai_prompt_gedcom_system")
        user_prompt = self._tr("ai_prompt_gedcom_user", ocr_text)
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

    def _clean_gedcom(self, raw: str) -> str:
        text = str(raw or "").strip()
        text = re.sub(r"^```(?:gedcom|ged)?\s*", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"\s*```$", "", text).strip()
        # JSON-Fallback: manche Modelle geben trotz Prompt {"gedcom": "..."} zurück.
        try:
            obj = json.loads(text)
            if isinstance(obj, dict):
                for key in ("gedcom", "GEDCOM", "text", "content"):
                    if isinstance(obj.get(key), str) and obj.get(key).strip():
                        text = obj[key].strip()
                        break
        except Exception:
            pass
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
        # Bei komplett erklärendem Text wenigstens abbrechen statt unbrauchbare Datei zu speichern.
        if not re.search(r"(?m)^0\s+@I\d+@\s+INDI\b", text, flags=re.IGNORECASE):
            # Eine reine SOUR/NOTE-Datei wäre zwar syntaktisch möglich, in Ahnenprogrammen aber kaum hilfreich.
            raise RuntimeError(
                "Das Modell hat keine GEDCOM-Personendatensätze erzeugt. "
                "Bitte nutze ein Vision-Modell, erhöhe ggf. die Token-Anzahl oder setze den GEDCOM-Prompt im Prompt-Editor zurück."
            )
        return text.strip() + "\n"

    def run(self):
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
            self.progress_changed.emit(85)
            content = self._extract_message_content(data)
            gedcom_text = self._clean_gedcom(content)
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_gedcom_cancelled"))
            self.progress_changed.emit(100)
            self.finished_gedcom.emit(self.path, gedcom_text)
        except Exception as exc:
            self.failed_gedcom.emit(self.path, str(exc))

def _bk_gedcom_current_task(self):
    try:
        task = self._current_task()
        try:
            self._persist_live_canvas_bboxes(task)
        except Exception:
            pass
        if task is not None and getattr(task, "path", None):
            return task
    except Exception:
        pass
    return None

def _bk_gedcom_collect_current_text(self, task) -> str:
    if not task or not getattr(task, "results", None):
        return ""
    try:
        if hasattr(self, "_bk_lm_collect_current_text"):
            value = str(self._bk_lm_collect_current_text(task) or "").strip()
            if value:
                return value
    except Exception:
        pass
    try:
        _text, _kr_records, _im, recs = task.results
        return "\n".join(_clean_ocr_text(rv.text) for rv in recs if _clean_ocr_text(rv.text)).strip()
    except Exception:
        return ""

def _bk_lm_generate_gedcom(self):
    task = _bk_gedcom_current_task(self)
    if not task or not getattr(task, "path", None):
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return
    source_text = _bk_gedcom_collect_current_text(self, task)
    has_image = bool(getattr(task, "path", "") and os.path.exists(task.path))
    if not source_text and not has_image:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_gedcom_needs_text_or_image"))
        return
    model_id = self._resolve_ai_model_id()
    if not model_id:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_ai_model"))
        return
    if _bk_lm_any_job_running(self):
        return
    self.act_ai_revise.setEnabled(False)
    if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
        self.btn_ai_revise_bottom.setEnabled(False)
    self._bk_gedcom_context = {"path": task.path}
    self.status_bar.showMessage(self._tr("msg_gedcom_started"))
    self._log(self._tr("log_gedcom_started", os.path.basename(task.path)))
    self._bk_gedcom_dialog = BKLocalJsonNoticeDialog(
        self._tr("dlg_gedcom_title"),
        self._tr("dlg_gedcom_notice"),
        self._tr,
        self,
    )
    self._bk_gedcom_dialog.cancel_requested.connect(lambda: _bk_lm_cancel_gedcom(self))
    self._bk_gedcom_dialog.show()
    try:
        max_tokens = self._lm_token_limit("gedcom")
    except Exception:
        max_tokens = 6000
    self._bk_gedcom_worker = BKLocalGedcomWorker(
        path=task.path,
        source_text=source_text,
        lm_model=model_id,
        endpoint=self.ai_endpoint,
        enable_thinking=self.ai_enable_thinking,
        temperature=self.ai_temperature,
        top_p=self.ai_top_p,
        top_k=self.ai_top_k,
        presence_penalty=self.ai_presence_penalty,
        repetition_penalty=self.ai_repetition_penalty,
        min_p=self.ai_min_p,
        max_tokens=max(int(max_tokens or 6000), 1000),
        tr_func=self._tr,
        parent=self,
    )
    self._bk_gedcom_worker.status_changed.connect(self._log)
    try:
        self._bk_gedcom_worker.status_changed.connect(self._bk_gedcom_dialog.set_status)
        self._bk_gedcom_worker.progress_changed.connect(self._bk_gedcom_dialog.set_progress)
    except Exception:
        pass
    self._bk_gedcom_worker.finished_gedcom.connect(lambda path, text: _bk_lm_on_gedcom_done(self, path, text))
    self._bk_gedcom_worker.failed_gedcom.connect(lambda path, msg: _bk_lm_on_gedcom_failed(self, path, msg))
    self._bk_gedcom_worker.start()

def _bk_lm_update_dropdown_state(self):
    try:
        _BK_GEDCOM_PREV_UPDATE_DROPDOWN_STATE(self)
    except Exception:
        pass
    if hasattr(self, "act_ai_menu_gedcom"):
        busy = _bk_lm_any_job_running(self)
        task = _bk_gedcom_current_task(self)
        self.act_ai_menu_gedcom.setEnabled(bool(task and getattr(task, "path", None)) and not busy)

_bk_gedcom_apply_vision_translations()

MainWindow._bk_lm_generate_gedcom = _bk_lm_generate_gedcom
