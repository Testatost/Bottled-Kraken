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

from ._translation_data.bk_gedcom_translations import (
    BK_GEDCOM_PROMPT_DEFAULTS as _BK_GEDCOM_PROMPT_DEFAULTS,
    BK_GEDCOM_VISION_TEXTS as _BK_GEDCOM_VISION_TEXTS,
    BK_GEDCOM_SAVE_FIX_TEXTS as _BK_GEDCOM_SAVE_FIX_TEXTS,
    BK_GEDCOM_ROBUST_TEXTS as _BK_GEDCOM_ROBUST_TEXTS,
    BK_GEDCOM_STRUCTURED_TEXTS as _BK_GEDCOM_STRUCTURED_TEXTS,
    BK_GEDCOM_REVIEW_TEXTS as _BK_GEDCOM_REVIEW_TEXTS,
    BK_PROMPT_UX_EXTRA_TEXTS as _BK_PROMPT_UX_EXTRA_TEXTS,
)



def _bk_gedcom_install_translations():
    for lang, mapping in _BK_GEDCOM_PROMPT_DEFAULTS.items():
        try:
            translation.TRANSLATIONS.setdefault(lang, {}).update(mapping)
        except Exception:
            try:
                TRANSLATIONS.setdefault(lang, {}).update(mapping)
            except Exception:
                pass

    # Bestehenden Prompt-Editor aus 17_bk_lm_token_and_prompt_options.py erweitern.
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
    lang = getattr(self, "current_lang", "de")
    data = _BK_GEDCOM_PROMPT_DEFAULTS.get(lang) or _BK_GEDCOM_PROMPT_DEFAULTS["de"]
    txt = data.get(key, _BK_GEDCOM_PROMPT_DEFAULTS["de"].get(key, key))
    try:
        return txt.format(*args) if args else txt
    except Exception:
        return txt


class BKLocalGedcomWorker(QThread):
    finished_gedcom = Signal(str, str)  # path, gedcom_text
    failed_gedcom = Signal(str, str)    # path, error
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
        self._tr = tr_func or translation.make_tr("de")
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

        # Wenn das Modell Vor-/Nachtext ausgegeben hat, auf GEDCOM-Kern beschneiden.
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


def _bk_gedcom_current_task(self):
    try:
        task = _bk_lm_get_current_done_task(self)
    except Exception:
        task = None
    if task is not None:
        return task
    try:
        task = self._current_task()
        self._persist_live_canvas_bboxes(task)
    except Exception:
        task = None
    return task if getattr(task, "results", None) else None


def _bk_gedcom_collect_current_text(self, task) -> str:
    try:
        if hasattr(self, "_bk_lm_collect_current_text"):
            return str(self._bk_lm_collect_current_text(task) or "").strip()
    except Exception:
        pass
    try:
        _text, _kr_records, _im, recs = task.results
        return "\n".join(_clean_ocr_text(rv.text) for rv in recs if _clean_ocr_text(rv.text)).strip()
    except Exception:
        return ""


def _bk_lm_cancel_gedcom(self):
    worker = getattr(self, "_bk_gedcom_worker", None)
    if worker is not None and worker.isRunning():
        try:
            worker.cancel()
        except Exception:
            pass
        try:
            if getattr(self, "_bk_gedcom_dialog", None):
                self._bk_gedcom_dialog.set_status(self._tr("msg_gedcom_cancelled"))
        except Exception:
            pass


def _bk_lm_on_gedcom_done(self, path: str, gedcom_text: str):
    worker = getattr(self, "_bk_gedcom_worker", None)
    if worker is not None:
        try:
            worker.deleteLater()
        except Exception:
            pass
    self._bk_gedcom_worker = None
    if getattr(self, "_bk_gedcom_dialog", None):
        try:
            self._bk_gedcom_dialog.close()
        except Exception:
            pass
        self._bk_gedcom_dialog = None

    self.act_ai_revise.setEnabled(True)
    if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
        self.btn_ai_revise_bottom.setEnabled(True)

    try:
        self._bk_last_gedcom_by_path[path] = gedcom_text
    except Exception:
        self._bk_last_gedcom_by_path = {path: gedcom_text}

    base_dir = getattr(self, "current_export_dir", "") or os.path.dirname(path) or os.getcwd()
    default_name = f"{os.path.splitext(os.path.basename(path))[0]}.ged"
    dest_path, _ = QFileDialog.getSaveFileName(
        self,
        self._tr("dlg_save_gedcom"),
        os.path.join(base_dir, default_name),
        self._tr("dlg_filter_gedcom"),
    )
    if dest_path:
        if not dest_path.lower().endswith(".ged"):
            dest_path += ".ged"
        try:
            with open(dest_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(gedcom_text)
            self.current_export_dir = os.path.dirname(dest_path)
            self.status_bar.showMessage(self._tr("msg_gedcom_done", os.path.basename(dest_path)), 5000)
            self._log(self._tr("log_gedcom_done", dest_path))
        except Exception as exc:
            QMessageBox.warning(self, self._tr("warn_title"), str(exc))
    else:
        self.status_bar.showMessage(self._tr("msg_gedcom_done", "-"), 3000)

    try:
        _bk_lm_update_dropdown_state(self)
    except Exception:
        pass


def _bk_lm_on_gedcom_failed(self, path: str, msg: str):
    worker = getattr(self, "_bk_gedcom_worker", None)
    if worker is not None:
        try:
            worker.deleteLater()
        except Exception:
            pass
    self._bk_gedcom_worker = None
    if getattr(self, "_bk_gedcom_dialog", None):
        try:
            self._bk_gedcom_dialog.close()
        except Exception:
            pass
        self._bk_gedcom_dialog = None

    self.act_ai_revise.setEnabled(True)
    if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
        self.btn_ai_revise_bottom.setEnabled(True)

    if _bk_is_cancel_message_v10(msg):
        self.status_bar.showMessage(self._tr("msg_gedcom_cancelled"), 4000)
    else:
        self.status_bar.showMessage(self._tr("msg_gedcom_failed"), 4000)
        self._log(self._tr("log_gedcom_failed", os.path.basename(path), msg))
        QMessageBox.warning(self, self._tr("warn_title"), msg)

    try:
        _bk_lm_update_dropdown_state(self)
    except Exception:
        pass


def _bk_lm_generate_gedcom(self):
    task = _bk_gedcom_current_task(self)
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return
    source_text = _bk_gedcom_collect_current_text(self, task)
    if not source_text:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_no_text_for_gedcom"))
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
        max_tokens = 4500

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
        max_tokens=max(int(max_tokens or 4500), 1000),
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


_BK_GEDCOM_PREV_ANY_JOB_RUNNING = _bk_lm_any_job_running


def _bk_lm_any_job_running(self) -> bool:
    return bool(
        _BK_GEDCOM_PREV_ANY_JOB_RUNNING(self)
        or (getattr(self, "_bk_gedcom_worker", None) and self._bk_gedcom_worker.isRunning())
    )


_BK_GEDCOM_PREV_UPDATE_DROPDOWN_STATE = _bk_lm_update_dropdown_state


def _bk_lm_update_dropdown_state(self):
    try:
        _BK_GEDCOM_PREV_UPDATE_DROPDOWN_STATE(self)
    except Exception:
        pass
    if hasattr(self, "act_ai_menu_gedcom"):
        busy = _bk_lm_any_job_running(self)
        task = _bk_gedcom_current_task(self)
        self.act_ai_menu_gedcom.setEnabled(bool(task) and not busy)


def _bk_gedcom_ensure_menu_action(self):
    if not hasattr(self, "btn_ai_revise_menu") or self.btn_ai_revise_menu is None:
        return
    if not hasattr(self, "act_ai_menu_gedcom"):
        self.act_ai_menu_gedcom = QAction(self._tr("act_lm_generate_gedcom"), self)
        self.act_ai_menu_gedcom.triggered.connect(lambda: _bk_lm_generate_gedcom(self))
    actions = list(self.btn_ai_revise_menu.actions())
    if self.act_ai_menu_gedcom not in actions:
        self.btn_ai_revise_menu.addAction(self.act_ai_menu_gedcom)
    self.act_ai_menu_gedcom.setText(self._tr("act_lm_generate_gedcom"))
    try:
        _bk_lm_update_dropdown_state(self)
    except Exception:
        pass


_BK_GEDCOM_PREV_INIT = MainWindow.__init__


def _bk_gedcom_init(self, *args, **kwargs):
    _BK_GEDCOM_PREV_INIT(self, *args, **kwargs)
    self._bk_gedcom_worker = None
    self._bk_gedcom_dialog = None
    self._bk_gedcom_context = None
    self._bk_last_gedcom_by_path = {}
    _bk_gedcom_ensure_menu_action(self)


_BK_GEDCOM_PREV_RETRANSLATE = MainWindow.retranslate_ui


def _bk_gedcom_retranslate(self, *args, **kwargs):
    _BK_GEDCOM_PREV_RETRANSLATE(self, *args, **kwargs)
    try:
        _bk_gedcom_ensure_menu_action(self)
    except Exception:
        pass
    if hasattr(self, "act_ai_menu_gedcom"):
        self.act_ai_menu_gedcom.setText(self._tr("act_lm_generate_gedcom"))


_BK_GEDCOM_PREV_CANCEL_LOCAL_JSON = _bk_lm_cancel_local_json if "_bk_lm_cancel_local_json" in globals() else None


def _bk_lm_cancel_local_json(self):
    if getattr(self, "_bk_gedcom_worker", None) and self._bk_gedcom_worker.isRunning():
        _bk_lm_cancel_gedcom(self)
        return
    if _BK_GEDCOM_PREV_CANCEL_LOCAL_JSON is not None:
        return _BK_GEDCOM_PREV_CANCEL_LOCAL_JSON(self)


_bk_gedcom_install_translations()

MainWindow.__init__ = _bk_gedcom_init
MainWindow.retranslate_ui = _bk_gedcom_retranslate
MainWindow._bk_lm_generate_gedcom = _bk_lm_generate_gedcom
MainWindow._bk_lm_cancel_gedcom = _bk_lm_cancel_gedcom


# =============================================================================
# Ursprünglich: 19_bk_lm_gedcom_vision_fix.py
# =============================================================================

"""Robustere GEDCOM-Erzeugung für Standesamts-/Kirchenbuchseiten.

Erweitert die bisherige GEDCOM-Funktion so, dass nicht nur vorhandener OCR-Text,
sondern auch das aktuelle Seitenbild an ein lokales Vision-Modell gesendet wird.
Damit können Formularseiten wie Geburts-, Heirats- oder Sterbeeinträge auch dann
verwertet werden, wenn die vorherige OCR unvollständig oder leer ist.
"""



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
        self._tr = tr_func or translation.make_tr("de")
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
                raise RuntimeError(f"HTTP {resp.status}: {raw}")
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


# =============================================================================
# Ursprünglich: 20_bk_lm_gedcom_save_dialog_fix.py
# =============================================================================

"""GEDCOM-Speicherdialog-Fix und übersetzte GEDCOM-Validierung.

Problem: Der GEDCOM-Worker wurde vorher über Lambda-Slots angebunden. Je nach
PySide/Qt-Verbindung kann ein solcher Slot im Worker-Thread laufen. Ein
QFileDialog aus einem Worker-Thread wird unter KDE/Qt unzuverlässig oder gar
nicht angezeigt. Dieser Patch verbindet die Worker-Signale mit echten
MainWindow-Methoden und zeigt den Speichern-Dialog garantiert im GUI-Kontext.
"""



def _bk_gedcom_save_fix_install_translations():
    for lang, mapping in _BK_GEDCOM_SAVE_FIX_TEXTS.items():
        try:
            translation.TRANSLATIONS.setdefault(lang, {}).update(mapping)
            continue
        except Exception:
            pass
        try:
            TRANSLATIONS.setdefault(lang, {}).update(mapping)
        except Exception:
            pass


def _bk_gedcom_text_for(window, key: str, *args) -> str:
    try:
        return window._tr(key, *args)
    except Exception:
        lang = getattr(window, "current_lang", "de")
        mapping = _BK_GEDCOM_SAVE_FIX_TEXTS.get(lang) or _BK_GEDCOM_SAVE_FIX_TEXTS["de"]
        text = mapping.get(key, _BK_GEDCOM_SAVE_FIX_TEXTS["de"].get(key, key))
        try:
            return text.format(*args) if args else text
        except Exception:
            return text


def _bk_gedcom_clean_relaxed(self, raw: str) -> str:
    """Bereinigt Modellantworten, ohne fehlende INDI-Datensätze hart abzubrechen.

    Einige Vision-Modelle erzeugen zunächst nur NOTE/SOUR-Blöcke oder schwache
    GEDCOM-Strukturen. In diesem Fall soll der Speicherdialog trotzdem erscheinen,
    aber die GUI warnt vor dem Speichern.
    """
    text = str(raw or "").strip()
    text = re.sub(r"^```(?:gedcom|ged)?\s*", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"\s*```$", "", text).strip()

    # JSON-Fallback: manche Modelle geben {"gedcom": "..."} zurück.
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            for key in ("gedcom", "GEDCOM", "ged", "text", "content", "output"):
                value = obj.get(key)
                if isinstance(value, str) and value.strip():
                    text = value.strip()
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

    # Nur echte GEDCOM-Levelzeilen behalten, falls das Modell Fließtext darum herum ausgegeben hat.
    level_line_re = re.compile(r"^\s*[0-9]+\s+")
    has_any_level_line = any(level_line_re.match(ln or "") for ln in lines)
    if has_any_level_line:
        lines = [ln for ln in lines if level_line_re.match(ln or "")]

    text = "\n".join(ln.strip() for ln in lines if ln.strip()).strip()
    if not text or not has_any_level_line:
        raise RuntimeError(self._tr("warn_gedcom_no_output"))

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
    elif not re.search(r"(?m)^1\s+CHAR\s+UTF-?8\b", text, flags=re.IGNORECASE):
        text = re.sub(r"(?m)^(0\s+HEAD\b.*)$", r"\1\n1 CHAR UTF-8", text, count=1)

    if not re.search(r"(?m)^0\s+TRLR\b", text, flags=re.IGNORECASE):
        text = text.rstrip() + "\n0 TRLR"

    return text.strip() + "\n"


def _bk_gedcom_has_indi_records(gedcom_text: str) -> bool:
    return bool(re.search(r"(?m)^0\s+@[^@\s]+@\s+INDI\b", str(gedcom_text or ""), flags=re.IGNORECASE))


def _bk_lm_on_gedcom_done_gui(self, path: str, gedcom_text: str):
    worker = getattr(self, "_bk_gedcom_worker", None)
    if worker is not None:
        try:
            worker.deleteLater()
        except Exception:
            pass
    self._bk_gedcom_worker = None

    if getattr(self, "_bk_gedcom_dialog", None):
        try:
            self._bk_gedcom_dialog.close()
        except Exception:
            pass
        self._bk_gedcom_dialog = None

    try:
        self.act_ai_revise.setEnabled(True)
    except Exception:
        pass
    try:
        if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
            self.btn_ai_revise_bottom.setEnabled(True)
    except Exception:
        pass

    gedcom_text = str(gedcom_text or "").strip() + "\n"
    try:
        self._bk_last_gedcom_by_path[path] = gedcom_text
    except Exception:
        self._bk_last_gedcom_by_path = {path: gedcom_text}

    if not _bk_gedcom_has_indi_records(gedcom_text):
        warning_text = (
            _bk_gedcom_text_for(self, "warn_gedcom_no_person_records")
            + "\n\n"
            + _bk_gedcom_text_for(self, "dlg_gedcom_save_weak_question")
        )
        answer = QMessageBox.question(
            self,
            _bk_gedcom_text_for(self, "dlg_gedcom_save_weak_title"),
            warning_text,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            self.status_bar.showMessage(_bk_gedcom_text_for(self, "msg_gedcom_generated_not_saved"), 5000)
            try:
                self._log(_bk_gedcom_text_for(self, "log_gedcom_not_saved", os.path.basename(path)))
            except Exception:
                pass
            return

    try:
        self.status_bar.showMessage(_bk_gedcom_text_for(self, "msg_gedcom_save_dialog_open"), 4000)
    except Exception:
        pass

    base_dir = getattr(self, "current_export_dir", "") or os.path.dirname(path) or os.getcwd()
    default_name = f"{os.path.splitext(os.path.basename(path))[0]}.ged"
    dest_path, _ = QFileDialog.getSaveFileName(
        self,
        _bk_gedcom_text_for(self, "dlg_save_gedcom"),
        os.path.join(base_dir, default_name),
        _bk_gedcom_text_for(self, "dlg_filter_gedcom"),
    )

    if not dest_path:
        self.status_bar.showMessage(_bk_gedcom_text_for(self, "msg_gedcom_generated_not_saved"), 5000)
        try:
            self._log(_bk_gedcom_text_for(self, "log_gedcom_not_saved", os.path.basename(path)))
        except Exception:
            pass
        return

    if not dest_path.lower().endswith(".ged"):
        dest_path += ".ged"

    try:
        with open(dest_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(gedcom_text)
        self.current_export_dir = os.path.dirname(dest_path)
        self.status_bar.showMessage(_bk_gedcom_text_for(self, "msg_gedcom_done", os.path.basename(dest_path)), 5000)
        self._log(_bk_gedcom_text_for(self, "log_gedcom_done", dest_path))
    except Exception as exc:
        QMessageBox.warning(self, _bk_gedcom_text_for(self, "warn_title"), str(exc))

    try:
        _bk_lm_update_dropdown_state(self)
    except Exception:
        pass


def _bk_lm_on_gedcom_failed_gui(self, path: str, msg: str):
    worker = getattr(self, "_bk_gedcom_worker", None)
    if worker is not None:
        try:
            worker.deleteLater()
        except Exception:
            pass
    self._bk_gedcom_worker = None

    if getattr(self, "_bk_gedcom_dialog", None):
        try:
            self._bk_gedcom_dialog.close()
        except Exception:
            pass
        self._bk_gedcom_dialog = None

    try:
        self.act_ai_revise.setEnabled(True)
    except Exception:
        pass
    try:
        if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
            self.btn_ai_revise_bottom.setEnabled(True)
    except Exception:
        pass

    if _bk_is_cancel_message_v10(msg):
        self.status_bar.showMessage(_bk_gedcom_text_for(self, "msg_gedcom_cancelled"), 4000)
    else:
        self.status_bar.showMessage(_bk_gedcom_text_for(self, "msg_gedcom_failed"), 4000)
        try:
            self._log(_bk_gedcom_text_for(self, "log_gedcom_failed", os.path.basename(path), msg))
        except Exception:
            pass
        QMessageBox.warning(self, _bk_gedcom_text_for(self, "warn_title"), str(msg))

    try:
        _bk_lm_update_dropdown_state(self)
    except Exception:
        pass


def _bk_lm_generate_gedcom_gui_safe(self):
    task = _bk_gedcom_current_task(self)
    if not task or not getattr(task, "path", None):
        QMessageBox.warning(self, _bk_gedcom_text_for(self, "warn_title"), self._tr("warn_need_done_for_ai"))
        return

    source_text = _bk_gedcom_collect_current_text(self, task)
    has_image = bool(getattr(task, "path", "") and os.path.exists(task.path))
    if not source_text and not has_image:
        QMessageBox.warning(self, _bk_gedcom_text_for(self, "warn_title"), self._tr("warn_gedcom_needs_text_or_image"))
        return

    model_id = self._resolve_ai_model_id()
    if not model_id:
        QMessageBox.warning(self, _bk_gedcom_text_for(self, "warn_title"), self._tr("warn_need_ai_model"))
        return
    if _bk_lm_any_job_running(self):
        return

    try:
        self.act_ai_revise.setEnabled(False)
    except Exception:
        pass
    try:
        if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
            self.btn_ai_revise_bottom.setEnabled(False)
    except Exception:
        pass

    self._bk_gedcom_context = {"path": task.path}
    self.status_bar.showMessage(self._tr("msg_gedcom_started"))
    try:
        self._log(self._tr("log_gedcom_started", os.path.basename(task.path)))
    except Exception:
        pass

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

    # Wichtig: Direkte Verbindung zu MainWindow-Methoden, keine Lambda-Slots.
    # So läuft der Speichern-Dialog zuverlässig im GUI-Thread.
    self._bk_gedcom_worker.finished_gedcom.connect(self._bk_lm_on_gedcom_done_gui)
    self._bk_gedcom_worker.failed_gedcom.connect(self._bk_lm_on_gedcom_failed_gui)
    self._bk_gedcom_worker.start()


def _bk_gedcom_rewire_menu_action(self):
    if not hasattr(self, "btn_ai_revise_menu") or self.btn_ai_revise_menu is None:
        return
    if not hasattr(self, "act_ai_menu_gedcom"):
        self.act_ai_menu_gedcom = QAction(self._tr("act_lm_generate_gedcom"), self)
    try:
        self.act_ai_menu_gedcom.triggered.disconnect()
    except Exception:
        pass
    self.act_ai_menu_gedcom.triggered.connect(lambda _checked=False: self._bk_lm_generate_gedcom())
    self.act_ai_menu_gedcom.setText(self._tr("act_lm_generate_gedcom"))

    actions = list(self.btn_ai_revise_menu.actions())
    if self.act_ai_menu_gedcom not in actions:
        self.btn_ai_revise_menu.addAction(self.act_ai_menu_gedcom)

    try:
        _bk_lm_update_dropdown_state(self)
    except Exception:
        pass


_BK_GEDCOM_SAVE_FIX_PREV_INIT = MainWindow.__init__


def _bk_gedcom_save_fix_init(self, *args, **kwargs):
    _BK_GEDCOM_SAVE_FIX_PREV_INIT(self, *args, **kwargs)
    try:
        _bk_gedcom_rewire_menu_action(self)
    except Exception:
        pass


_BK_GEDCOM_SAVE_FIX_PREV_RETRANSLATE = MainWindow.retranslate_ui


def _bk_gedcom_save_fix_retranslate(self, *args, **kwargs):
    _BK_GEDCOM_SAVE_FIX_PREV_RETRANSLATE(self, *args, **kwargs)
    try:
        _bk_gedcom_rewire_menu_action(self)
    except Exception:
        pass


_bk_gedcom_save_fix_install_translations()

try:
    BKLocalGedcomWorker._clean_gedcom = _bk_gedcom_clean_relaxed
except Exception:
    pass

MainWindow.__init__ = _bk_gedcom_save_fix_init
MainWindow.retranslate_ui = _bk_gedcom_save_fix_retranslate
MainWindow._bk_lm_generate_gedcom = _bk_lm_generate_gedcom_gui_safe
MainWindow._bk_lm_on_gedcom_done_gui = _bk_lm_on_gedcom_done_gui
MainWindow._bk_lm_on_gedcom_failed_gui = _bk_lm_on_gedcom_failed_gui


# =============================================================================
# Ursprünglich: 21_bk_lm_gedcom_robust_output_fix.py
# =============================================================================

"""Robustere GEDCOM-Erzeugung für lokale Vision-Modelle.

Diese späte Patch-Datei erweitert die vorherige GEDCOM-Funktion:
- strengerer GEDCOM-Prompt für Standesamts-/Kirchenbuchseiten
- automatischer Reparaturversuch, wenn das Modell zuerst keinen GEDCOM-Text liefert
- letzter Fallback: importierbare GEDCOM-Hülle mit NOTE und Warnhinweis statt harter Abbruch
- Speicherdialog bleibt dadurch erreichbar, auch wenn das Modell schwach antwortet
"""



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
        lang = getattr(self, "current_lang", "de") if hasattr(self, "current_lang") else "de"
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
    # Wird an editierbare Prompts angehängt, damit alte/gespeicherte Prompts nicht mehr zu reiner Prosa führen.
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

        # Zuerst echte GEDCOM-Struktur suchen. Wenn nicht vorhanden: Reparaturversuch.
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
                # Fallback enthält vorherige und reparierte Antwort als NOTE.
                content = "\n\n".join(x for x in (raw_unwrapped, repair_unwrapped) if str(x or "").strip())

        self.progress_changed.emit(90)
        gedcom_text = self._clean_gedcom(content)
        if self._cancelled or self.isInterruptionRequested():
            raise RuntimeError(self._tr("msg_gedcom_cancelled"))
        self.progress_changed.emit(100)
        self.finished_gedcom.emit(self.path, gedcom_text)
    except Exception as exc:
        self.failed_gedcom.emit(self.path, str(exc))


# Die Speichern-Warnung aus 20_bk_lm_gedcom_save_dialog_fix.py soll auch bei Fallback-INDI greifen.
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


# =============================================================================
# Ursprünglich: 22_bk_lm_gedcom_structured_extract_fix.py
# =============================================================================

"""Strukturierter GEDCOM-Fix für schwierige Standesamts-/Kirchenbuchseiten.

Warum diese Datei existiert:
Der direkte GEDCOM-Prompt kann bei manchen lokalen Vision-Modellen scheitern.
Dann entsteht zwar eine syntaktische GEDCOM-Hülle, aber nur mit NOTE-Fallback.
Dieser späte Patch macht den Ablauf robuster:
1) zuerst strukturierte genealogische JSON-Daten aus Bild + OCR extrahieren,
2) daraus GEDCOM deterministisch im Programm erzeugen,
3) nur wenn das fehlschlägt auf den bisherigen direkten GEDCOM-/Fallback-Pfad gehen.

Die beiden neuen Extraktionsprompts werden in den vorhandenen Prompt-Editor
unter Optionen aufgenommen und können dort bearbeitet/zurückgesetzt werden.
"""



def _bk_gedcom_structured_install_translations():
    for lang, mapping in _BK_GEDCOM_STRUCTURED_TEXTS.items():
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
            if "_BK_LM_OPTIONS_TEXTS" in globals():
                _BK_LM_OPTIONS_TEXTS.setdefault(lang, {}).update({
                    "lm_prompt_gedcom_extract_system": mapping["lm_prompt_gedcom_extract_system"],
                    "lm_prompt_gedcom_extract_user": mapping["lm_prompt_gedcom_extract_user"],
                })
        except Exception:
            pass

    try:
        existing = [k for k, _label in _BK_LM_PROMPT_KEYS]
        extra = []
        if "ai_prompt_gedcom_extract_system" not in existing:
            extra.append(("ai_prompt_gedcom_extract_system", "lm_prompt_gedcom_extract_system"))
        if "ai_prompt_gedcom_extract_user" not in existing:
            extra.append(("ai_prompt_gedcom_extract_user", "lm_prompt_gedcom_extract_user"))
        if extra:
            globals()["_BK_LM_PROMPT_KEYS"] = tuple(_BK_LM_PROMPT_KEYS) + tuple(extra)
    except Exception:
        pass


def _bk_gedcom_structured_tr(worker, key: str, *args) -> str:
    try:
        return worker._tr(key, *args)
    except Exception:
        lang = "de"
        data = _BK_GEDCOM_STRUCTURED_TEXTS.get(lang) or _BK_GEDCOM_STRUCTURED_TEXTS["de"]
        text = data.get(key, _BK_GEDCOM_STRUCTURED_TEXTS["de"].get(key, key))
        try:
            return text.format(*args) if args else text
        except Exception:
            return text


def _bk_gedcom_safe_text(value) -> str:
    txt = str(value or "")
    txt = txt.replace("\r\n", "\n").replace("\r", "\n")
    txt = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", txt)
    txt = re.sub(r"[ \t]+", " ", txt)
    return txt.strip(" \t\n;,.|")


def _bk_gedcom_json_from_model_text(text: str):
    raw = str(text or "").strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE).strip()
    raw = re.sub(r"\s*```$", "", raw).strip()
    try:
        return json.loads(raw)
    except Exception:
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(raw[start:end + 1])
        except Exception:
            return None
    return None


def _bk_gedcom_person_has_data(person) -> bool:
    if not isinstance(person, dict):
        return False
    for key in ("given_names", "surname", "maiden_surname", "occupation", "residence", "religion", "note"):
        if _bk_gedcom_safe_text(person.get(key)):
            return True
    return False


def _bk_gedcom_person_name(given: str, surname: str, fallback_given: str = "Unbekannt") -> str:
    given = _bk_gedcom_safe_text(given)
    surname = _bk_gedcom_safe_text(surname)
    if not given and not surname:
        given = fallback_given
    if surname:
        return f"{given} /{surname}/".strip()
    return f"{given} //".strip()


def _bk_gedcom_note_lines(level: int, tag: str, value: str, out: list, max_chars: int = 12000):
    txt = _bk_gedcom_safe_text(value)
    if not txt:
        return
    txt = txt[:max_chars]
    parts = txt.split("\n")
    first = True
    for part in parts:
        part = _bk_gedcom_safe_text(part)
        if not part:
            continue
        while len(part) > 230:
            chunk = part[:230].rstrip()
            part = part[230:].lstrip()
            if first:
                out.append(f"{level} {tag} {chunk}")
                first = False
            else:
                out.append(f"{level + 1} CONT {chunk}")
        if first:
            out.append(f"{level} {tag} {part}")
            first = False
        else:
            out.append(f"{level + 1} CONT {part}")


def _bk_gedcom_date(value: str) -> str:
    txt = _bk_gedcom_safe_text(value)
    if not txt:
        return ""
    # Nicht aggressiv normalisieren: Ahnenprogramme akzeptieren oft Freitext-Datumsangaben besser als falsche GEDCOM-Konvertierung.
    return txt


def _bk_gedcom_setdefault_person_dict(obj: dict, key: str) -> dict:
    val = obj.get(key)
    if isinstance(val, dict):
        return val
    return {}


def _bk_gedcom_build_from_structured(worker, data: dict) -> str:
    if not isinstance(data, dict):
        raise RuntimeError("structured GEDCOM extraction did not return an object")

    record_type = _bk_gedcom_safe_text(data.get("record_type")).lower() or "unknown"
    registry_place = _bk_gedcom_safe_text(data.get("registry_place"))
    record_number = _bk_gedcom_safe_text(data.get("record_number"))
    entry_date = _bk_gedcom_date(data.get("entry_date"))
    event_date = _bk_gedcom_date(data.get("event_date"))
    event_time = _bk_gedcom_safe_text(data.get("event_time"))
    event_place = _bk_gedcom_safe_text(data.get("event_place")) or registry_place
    source_title = _bk_gedcom_safe_text(data.get("source_title"))
    transcription = _bk_gedcom_safe_text(data.get("transcription_or_notes"))
    uncertainty = bool(data.get("uncertainty", True))

    child = _bk_gedcom_setdefault_person_dict(data, "child")
    father = _bk_gedcom_setdefault_person_dict(data, "father")
    mother = _bk_gedcom_setdefault_person_dict(data, "mother")
    informant = _bk_gedcom_setdefault_person_dict(data, "informant")

    father_has = _bk_gedcom_person_has_data(father)
    mother_has = _bk_gedcom_person_has_data(mother)
    child_has = _bk_gedcom_person_has_data(child) or record_type == "birth" or event_date or father_has or mother_has
    informant_has = _bk_gedcom_person_has_data(informant)

    if not (child_has or father_has or mother_has or informant_has):
        raise RuntimeError("no usable genealogical person data extracted")

    father_surname = _bk_gedcom_safe_text(father.get("surname"))
    child_given = _bk_gedcom_safe_text(child.get("given_names"))
    child_surname = _bk_gedcom_safe_text(child.get("surname"))
    if child_has and not child_given:
        child_given = "Unbenannt" if record_type == "birth" else "Unbekannt"
    if child_has and not child_surname and father_surname:
        child_surname = father_surname
        note = _bk_gedcom_safe_text(child.get("note"))
        derived = "Familienname aus dem Vater abgeleitet; bitte prüfen."
        child["note"] = f"{note} {derived}".strip()

    out = [
        "0 HEAD",
        "1 SOUR BottledKraken",
        "1 GEDC",
        "2 VERS 5.5.1",
        "2 FORM LINEAGE-LINKED",
        "1 CHAR UTF-8",
    ]

    id_counter = 1
    ids = {}

    def next_id(prefix="I"):
        nonlocal id_counter
        ident = f"@{prefix}{id_counter}@"
        id_counter += 1
        return ident

    child_id = next_id("I") if child_has else ""
    father_id = next_id("I") if father_has else ""
    mother_id = next_id("I") if mother_has else ""

    def add_person(pid: str, person: dict, role_label: str, *, is_child=False):
        given = child_given if is_child else _bk_gedcom_safe_text(person.get("given_names"))
        surname = child_surname if is_child else _bk_gedcom_safe_text(person.get("surname"))
        out.append(f"0 {pid} INDI")
        out.append("1 NAME " + _bk_gedcom_person_name(given, surname, "Unbekannt"))
        sex = _bk_gedcom_safe_text(person.get("sex")).upper()
        if is_child:
            if sex in ("M", "F"):
                out.append(f"1 SEX {sex}")
            elif sex in ("MALE", "MÄNNLICH", "MANN", "HOMME", "MASCULIN"):
                out.append("1 SEX M")
            elif sex in ("FEMALE", "WEIBLICH", "FRAU", "FEMME", "FÉMININ"):
                out.append("1 SEX F")
            else:
                out.append("1 SEX U")
        maiden = _bk_gedcom_safe_text(person.get("maiden_surname"))
        if maiden:
            _bk_gedcom_note_lines(1, "NOTE", f"Geburtsname/Mädchenname: {maiden}", out)
        occu = _bk_gedcom_safe_text(person.get("occupation"))
        if occu:
            out.append(f"1 OCCU {occu}")
        resi = _bk_gedcom_safe_text(person.get("residence"))
        if resi:
            out.append("1 RESI")
            out.append(f"2 PLAC {resi}")
        religion = _bk_gedcom_safe_text(person.get("religion"))
        if religion:
            _bk_gedcom_note_lines(1, "NOTE", f"Religion: {religion}", out)
        if is_child and record_type == "birth":
            out.append("1 BIRT")
            if event_date:
                out.append(f"2 DATE {event_date}")
            if event_place:
                out.append(f"2 PLAC {event_place}")
            if event_time:
                _bk_gedcom_note_lines(2, "NOTE", f"Geburtszeit: {event_time}", out)
        note = _bk_gedcom_safe_text(person.get("note"))
        role_note = f"Rolle im Dokument: {role_label}."
        if note:
            role_note += f" {note}"
        _bk_gedcom_note_lines(1, "NOTE", role_note, out)
        if source_title or registry_place or record_number or entry_date:
            out.append("1 SOUR @S1@")

    if child_has:
        add_person(child_id, child, "Kind", is_child=True)
    if father_has:
        add_person(father_id, father, "Vater")
    if mother_has:
        add_person(mother_id, mother, "Mutter")

    # Anzeigende Person nur separat anlegen, wenn sie nicht offensichtlich Vater/Mutter ist.
    informant_id = ""
    if informant_has:
        inf_name = (_bk_gedcom_safe_text(informant.get("given_names")), _bk_gedcom_safe_text(informant.get("surname")))
        father_name = (_bk_gedcom_safe_text(father.get("given_names")), _bk_gedcom_safe_text(father.get("surname")))
        mother_name = (_bk_gedcom_safe_text(mother.get("given_names")), _bk_gedcom_safe_text(mother.get("surname")))
        if inf_name != father_name and inf_name != mother_name:
            informant_id = next_id("I")
            add_person(informant_id, informant, "Anzeigende Person")
        else:
            # Relation als Note an bereits vorhandenen Datensatz ergänzen wäre möglich; als SOUR/NOTE reicht hier.
            pass

    if child_has and (father_has or mother_has):
        out.append("0 @F1@ FAM")
        if father_has:
            out.append(f"1 HUSB {father_id}")
        if mother_has:
            out.append(f"1 WIFE {mother_id}")
        out.append(f"1 CHIL {child_id}")
        if child_has:
            # Rückverweis im Kind-Datensatz nachträglich nicht nötig für Import, aber FAM reicht.
            pass

    title_parts = []
    if source_title:
        title_parts.append(source_title)
    if registry_place:
        title_parts.append(f"Standesamt/Ort: {registry_place}")
    if record_number:
        title_parts.append(f"Nr. {record_number}")
    if entry_date:
        title_parts.append(f"Eintrag: {entry_date}")
    if not title_parts:
        title_parts.append(os.path.basename(getattr(worker, "path", "")) or "Quelle")
    out.append("0 @S1@ SOUR")
    out.append("1 TITL " + " | ".join(title_parts))
    if uncertainty:
        _bk_gedcom_note_lines(1, "NOTE", "Automatisch aus Bild/OCR erzeugt; unsichere Lesungen bitte prüfen.", out)
    if transcription:
        _bk_gedcom_note_lines(1, "NOTE", transcription, out)

    out.append("0 TRLR")
    text = "\n".join(out).strip() + "\n"
    if not re.search(r"(?m)^0\s+@I\d+@\s+INDI\b", text):
        raise RuntimeError("structured data produced no INDI record")
    return text


def _bk_gedcom_response_format_structured() -> dict:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "gedcom_extraction",
            "schema": {
                "type": "object",
                "properties": {
                    "record_type": {"type": "string"},
                    "registry_place": {"type": "string"},
                    "record_number": {"type": "string"},
                    "entry_date": {"type": "string"},
                    "event_date": {"type": "string"},
                    "event_time": {"type": "string"},
                    "event_place": {"type": "string"},
                    "child": {"type": "object"},
                    "father": {"type": "object"},
                    "mother": {"type": "object"},
                    "informant": {"type": "object"},
                    "source_title": {"type": "string"},
                    "transcription_or_notes": {"type": "string"},
                    "uncertainty": {"type": "boolean"},
                },
                "required": ["record_type", "child", "father", "mother", "informant", "uncertainty"],
                "additionalProperties": True,
            },
        },
    }


def _bk_gedcom_build_structured_payload(worker, image_data_url: str = "") -> dict:
    ocr_text = getattr(worker, "source_text", "") or "[Kein OCR-Text vorhanden. Bitte primär das Seitenbild auswerten.]"
    system_prompt = worker._tr("ai_prompt_gedcom_extract_system")
    user_prompt = worker._tr("ai_prompt_gedcom_extract_user", ocr_text)
    if image_data_url:
        user_content = [
            {"type": "text", "text": user_prompt},
            {"type": "image_url", "image_url": {"url": image_data_url}},
        ]
    else:
        user_content = user_prompt
    payload = {
        "model": worker.lm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        **worker._build_sampling_payload(),
    }
    # Viele lokale OpenAI-kompatible Server unterstützen json_schema; wenn nicht,
    # fällt der Aufruf unten automatisch in den bisherigen direkten GEDCOM-Pfad zurück.
    payload["response_format"] = _bk_gedcom_response_format_structured()
    payload["max_tokens"] = max(int(getattr(worker, "max_tokens", 6000) or 6000), 2500)
    return payload


_BK_GEDCOM_V22_PREV_RUN = BKLocalGedcomWorker.run


def _bk_gedcom_worker_run_structured(self):
    try:
        if self._cancelled or self.isInterruptionRequested():
            raise RuntimeError(self._tr("msg_gedcom_cancelled"))
        image_data_url = self._page_image_data_url()
        if not getattr(self, "source_text", "") and not image_data_url:
            raise RuntimeError(self._tr("warn_gedcom_needs_text_or_image"))

        self.progress_changed.emit(5)
        self.status_changed.emit(_bk_gedcom_structured_tr(self, "log_gedcom_structured_start"))

        try:
            self.progress_changed.emit(18)
            data = self._post_json(_bk_gedcom_build_structured_payload(self, image_data_url=image_data_url))
            content = self._extract_message_content(data)
            obj = _bk_gedcom_json_from_model_text(content)
            gedcom_text = _bk_gedcom_build_from_structured(self, obj)
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_gedcom_cancelled"))
            self.progress_changed.emit(100)
            self.status_changed.emit(_bk_gedcom_structured_tr(self, "log_gedcom_structured_success"))
            self.finished_gedcom.emit(self.path, gedcom_text)
            return
        except Exception as structured_exc:
            if self._cancelled or self.isInterruptionRequested():
                raise
            self.status_changed.emit(_bk_gedcom_structured_tr(self, "log_gedcom_structured_fallback"))
            try:
                # Für Debugging bewusst kurz halten; keine störende MessageBox.
                self.status_changed.emit(f"GEDCOM strukturierte Extraktion: {str(structured_exc)[:500]}")
            except Exception:
                pass

        # Bisherigen robusten GEDCOM-/Retry-/NOTE-Fallback nutzen.
        return _BK_GEDCOM_V22_PREV_RUN(self)
    except Exception as exc:
        self.failed_gedcom.emit(self.path, str(exc))


_bk_gedcom_structured_install_translations()
BKLocalGedcomWorker.run = _bk_gedcom_worker_run_structured


# =============================================================================
# Ursprünglich: 23_bk_lm_gedcom_review_export_dialog.py
# =============================================================================

"""GEDCOM-Vorschau-/Bearbeitungsdialog vor dem Export.

Ersetzt den direkten Speichern-Dialog nach der GEDCOM-Erzeugung durch eine
prüfbare Übersicht mit bearbeitbaren erkannten Daten, editierbarem GEDCOM-Text
und anschließendem Export.
"""

try:
    from PySide6.QtWidgets import QTabWidget
except Exception:
    QTabWidget = None



def _bk_gedcom_review_install_translations():
    for lang, mapping in _BK_GEDCOM_REVIEW_TEXTS.items():
        try:
            translation.TRANSLATIONS.setdefault(lang, {}).update(mapping)
        except Exception:
            try:
                TRANSLATIONS.setdefault(lang, {}).update(mapping)
            except Exception:
                pass


def _bk_gedcom_review_text(window, key: str, *args) -> str:
    try:
        return window._tr(key, *args)
    except Exception:
        lang = getattr(window, "current_lang", "de")
        data = _BK_GEDCOM_REVIEW_TEXTS.get(lang) or _BK_GEDCOM_REVIEW_TEXTS["de"]
        text = data.get(key, _BK_GEDCOM_REVIEW_TEXTS["de"].get(key, key))
        try:
            return text.format(*args) if args else text
        except Exception:
            return text


def _bk_gedcom_review_deepcopy(obj):
    try:
        return json.loads(json.dumps(obj, ensure_ascii=False))
    except Exception:
        try:
            return dict(obj)
        except Exception:
            return obj


_BK_GEDCOM_REVIEW_PREV_BUILD_FROM_STRUCTURED = globals().get("_bk_gedcom_build_from_structured")


def _bk_gedcom_build_from_structured(worker, data: dict) -> str:
    """Wrapper: strukturierte Extraktionsdaten für die spätere GUI-Übersicht merken."""
    try:
        setattr(worker, "_bk_gedcom_structured_data", _bk_gedcom_review_deepcopy(data))
        setattr(worker, "_bk_gedcom_used_structured", True)
    except Exception:
        pass
    if _BK_GEDCOM_REVIEW_PREV_BUILD_FROM_STRUCTURED is None:
        raise RuntimeError("structured GEDCOM builder is not available")
    text = _BK_GEDCOM_REVIEW_PREV_BUILD_FROM_STRUCTURED(worker, data)
    try:
        setattr(worker, "_bk_gedcom_structured_gedcom", text)
    except Exception:
        pass
    return text


def _bk_gedcom_review_person_count(text: str) -> int:
    return len(re.findall(r"(?m)^0\s+@[^@\s]+@\s+INDI\b", str(text or ""), flags=re.IGNORECASE))


def _bk_gedcom_review_family_count(text: str) -> int:
    return len(re.findall(r"(?m)^0\s+@[^@\s]+@\s+FAM\b", str(text or ""), flags=re.IGNORECASE))


def _bk_gedcom_review_names(text: str) -> str:
    names = []
    for match in re.finditer(r"(?m)^1\s+NAME\s+(.+?)\s*$", str(text or ""), flags=re.IGNORECASE):
        value = match.group(1).strip()
        if value and value not in names:
            names.append(value)
    return "; ".join(names[:20])


def _bk_gedcom_review_is_weak(gedcom_text: str) -> bool:
    txt = str(gedcom_text or "")
    fallback = bool(re.search(r"(?m)^1\s+_BK_FALLBACK\s+Y\b", txt, flags=re.IGNORECASE))
    try:
        has_indi = _bk_gedcom_has_indi_records(txt)
    except Exception:
        has_indi = bool(re.search(r"(?m)^0\s+@[^@\s]+@\s+INDI\b", txt, flags=re.IGNORECASE))
    return fallback or not has_indi


def _bk_gedcom_review_finalize_text(text: str) -> str:
    txt = str(text or "").strip()
    if not txt:
        return ""
    try:
        if "_bk_gedcom_finalize_level_text" in globals():
            return _bk_gedcom_finalize_level_text(txt).strip() + "\n"
    except Exception:
        pass
    txt = txt.replace("\r\n", "\n").replace("\r", "\n")
    if not re.search(r"(?m)^0\s+HEAD\b", txt, flags=re.IGNORECASE):
        header = (
            "0 HEAD\n"
            "1 SOUR BottledKraken\n"
            "1 GEDC\n"
            "2 VERS 5.5.1\n"
            "2 FORM LINEAGE-LINKED\n"
            "1 CHAR UTF-8"
        )
        txt = header + "\n" + txt
    if not re.search(r"(?m)^0\s+TRLR\b", txt, flags=re.IGNORECASE):
        txt = txt.rstrip() + "\n0 TRLR"
    return txt.strip() + "\n"


class BKGedcomReviewDialog(QDialog):
    def __init__(self, window, path: str, gedcom_text: str, structured_data=None, parent=None):
        super().__init__(parent or window)
        self.window = window
        self.path = path
        self.structured_data = _bk_gedcom_review_deepcopy(structured_data) if isinstance(structured_data, dict) else None
        self.exported_path = ""
        self.setWindowTitle(_bk_gedcom_review_text(window, "dlg_gedcom_review_title"))
        self.resize(1100, 760)

        root = QVBoxLayout(self)
        self.info_label = QLabel(_bk_gedcom_review_text(window, "gedcom_review_intro"))
        self.info_label.setWordWrap(True)
        root.addWidget(self.info_label)

        self.warning_label = QLabel("")
        self.warning_label.setWordWrap(True)
        self.warning_label.setVisible(False)
        self.warning_label.setStyleSheet("font-weight: 600; color: #d99a00;")
        root.addWidget(self.warning_label)

        if QTabWidget is not None:
            self.tabs = QTabWidget()
            root.addWidget(self.tabs, 1)
            data_page = QWidget()
            text_page = QWidget()
            self.tabs.addTab(data_page, _bk_gedcom_review_text(window, "gedcom_review_tab_data"))
            self.tabs.addTab(text_page, _bk_gedcom_review_text(window, "gedcom_review_tab_text"))
        else:
            # Fallback, falls QTabWidget unerwartet nicht verfügbar ist.
            self.tabs = None
            data_page = QWidget()
            text_page = QWidget()
            split = QSplitter(Qt.Vertical)
            split.addWidget(data_page)
            split.addWidget(text_page)
            root.addWidget(split, 1)

        data_layout = QVBoxLayout(data_page)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels([
            _bk_gedcom_review_text(window, "gedcom_review_field"),
            _bk_gedcom_review_text(window, "gedcom_review_value"),
        ])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tree.setAlternatingRowColors(True)
        data_layout.addWidget(self.tree, 1)

        self.update_btn = QPushButton(_bk_gedcom_review_text(window, "gedcom_review_update"))
        self.update_btn.clicked.connect(self.update_gedcom_from_overview)
        data_layout.addWidget(self.update_btn)

        text_layout = QVBoxLayout(text_page)
        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlainText(str(gedcom_text or "").strip() + "\n")
        self.text_edit.setLineWrapMode(QPlainTextEdit.NoWrap)
        text_layout.addWidget(self.text_edit, 1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.export_btn = QPushButton(_bk_gedcom_review_text(window, "gedcom_review_export"))
        self.close_btn = QPushButton(_bk_gedcom_review_text(window, "gedcom_review_close"))
        self.export_btn.clicked.connect(self.export_gedcom)
        self.close_btn.clicked.connect(self.reject)
        buttons.addWidget(self.export_btn)
        buttons.addWidget(self.close_btn)
        root.addLayout(buttons)

        self._populate_overview()
        self._update_warning()

    def _label_for_key(self, key: str) -> str:
        tr_key = "gedcom_field_" + str(key).split(".")[-1]
        return _bk_gedcom_review_text(self.window, tr_key)

    def _make_group(self, text_key: str):
        item = QTreeWidgetItem([_bk_gedcom_review_text(self.window, text_key), ""])
        font = item.font(0)
        font.setBold(True)
        item.setFont(0, font)
        item.setFirstColumnSpanned(False)
        self.tree.addTopLevelItem(item)
        return item

    def _add_editable_item(self, parent, key_path: str, value):
        label = self._label_for_key(key_path)
        if isinstance(value, bool):
            value_text = "true" if value else "false"
        else:
            value_text = str(value or "")
        item = QTreeWidgetItem([label, value_text])
        item.setData(0, Qt.UserRole, key_path)
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        parent.addChild(item)
        return item

    def _populate_overview(self):
        self.tree.clear()
        if isinstance(self.structured_data, dict):
            general = self._make_group("gedcom_group_general")
            for key in (
                "record_type", "registry_place", "record_number", "entry_date",
                "event_date", "event_time", "event_place", "source_title",
                "transcription_or_notes", "uncertainty",
            ):
                self._add_editable_item(general, key, self.structured_data.get(key, ""))

            for group_key, dict_key, keys in (
                ("gedcom_group_child", "child", ("given_names", "surname", "sex", "note")),
                ("gedcom_group_father", "father", ("given_names", "surname", "occupation", "residence", "religion", "note")),
                ("gedcom_group_mother", "mother", ("given_names", "surname", "maiden_surname", "occupation", "residence", "religion", "note")),
                ("gedcom_group_informant", "informant", ("given_names", "surname", "occupation", "residence", "relation", "note")),
            ):
                parent = self._make_group(group_key)
                data = self.structured_data.get(dict_key) if isinstance(self.structured_data.get(dict_key), dict) else {}
                for key in keys:
                    self._add_editable_item(parent, f"{dict_key}.{key}", data.get(key, ""))
            self.tree.expandAll()
            self.update_btn.setEnabled(True)
            return

        # Keine strukturierten Daten: wenigstens eine lesbare Zusammenfassung aus GEDCOM erzeugen.
        general = self._make_group("gedcom_group_general")
        self._add_editable_item(general, "person_count", str(_bk_gedcom_review_person_count(self.text_edit.toPlainText())))
        general.child(general.childCount() - 1).setText(0, _bk_gedcom_review_text(self.window, "gedcom_overview_person_count"))
        self._add_editable_item(general, "family_count", str(_bk_gedcom_review_family_count(self.text_edit.toPlainText())))
        general.child(general.childCount() - 1).setText(0, _bk_gedcom_review_text(self.window, "gedcom_overview_family_count"))
        self._add_editable_item(general, "names", _bk_gedcom_review_names(self.text_edit.toPlainText()))
        general.child(general.childCount() - 1).setText(0, _bk_gedcom_review_text(self.window, "gedcom_overview_names"))
        self.tree.expandAll()
        self.update_btn.setEnabled(False)
        self.warning_label.setText(_bk_gedcom_review_text(self.window, "gedcom_review_no_structured"))
        self.warning_label.setVisible(True)

    def _tree_to_structured_data(self) -> dict:
        data = _bk_gedcom_review_deepcopy(self.structured_data) if isinstance(self.structured_data, dict) else {}
        for i in range(self.tree.topLevelItemCount()):
            group = self.tree.topLevelItem(i)
            for j in range(group.childCount()):
                item = group.child(j)
                key_path = item.data(0, Qt.UserRole)
                if not key_path:
                    continue
                value = item.text(1).strip()
                if key_path == "uncertainty":
                    data[key_path] = value.lower() in ("1", "true", "yes", "ja", "oui", "wahr")
                    continue
                if "." in key_path:
                    prefix, key = key_path.split(".", 1)
                    if not isinstance(data.get(prefix), dict):
                        data[prefix] = {}
                    data[prefix][key] = value
                else:
                    data[key_path] = value
        return data

    def update_gedcom_from_overview(self):
        if not isinstance(self.structured_data, dict):
            return
        data = self._tree_to_structured_data()
        fake_worker = type("BKGedcomReviewBuildContext", (), {})()
        fake_worker.path = self.path
        try:
            gedcom_text = _BK_GEDCOM_REVIEW_PREV_BUILD_FROM_STRUCTURED(fake_worker, data)
            gedcom_text = _bk_gedcom_review_finalize_text(gedcom_text)
        except Exception as exc:
            QMessageBox.warning(
                self,
                _bk_gedcom_review_text(self.window, "warn_title"),
                _bk_gedcom_review_text(self.window, "gedcom_review_update_failed", exc),
            )
            return
        self.structured_data = data
        self.text_edit.setPlainText(gedcom_text)
        self._update_warning()

    def _update_warning(self):
        warnings = []
        if not isinstance(self.structured_data, dict):
            warnings.append(_bk_gedcom_review_text(self.window, "gedcom_review_no_structured"))
        if _bk_gedcom_review_is_weak(self.text_edit.toPlainText()):
            warnings.append(_bk_gedcom_review_text(self.window, "gedcom_review_weak_warning"))
        self.warning_label.setText("\n\n".join(warnings))
        self.warning_label.setVisible(bool(warnings))

    def export_gedcom(self):
        gedcom_text = _bk_gedcom_review_finalize_text(self.text_edit.toPlainText())
        if not gedcom_text.strip():
            QMessageBox.warning(
                self,
                _bk_gedcom_review_text(self.window, "warn_title"),
                _bk_gedcom_review_text(self.window, "gedcom_review_export_empty"),
            )
            return

        if _bk_gedcom_review_is_weak(gedcom_text):
            answer = QMessageBox.question(
                self,
                _bk_gedcom_review_text(self.window, "dlg_gedcom_save_weak_title"),
                _bk_gedcom_review_text(self.window, "gedcom_review_export_weak"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return

        base_dir = getattr(self.window, "current_export_dir", "") or os.path.dirname(self.path) or os.getcwd()
        default_name = f"{os.path.splitext(os.path.basename(self.path))[0]}.ged"
        dest_path, _ = QFileDialog.getSaveFileName(
            self,
            _bk_gedcom_review_text(self.window, "dlg_save_gedcom"),
            os.path.join(base_dir, default_name),
            _bk_gedcom_review_text(self.window, "dlg_filter_gedcom"),
        )
        if not dest_path:
            return
        if not dest_path.lower().endswith(".ged"):
            dest_path += ".ged"
        try:
            with open(dest_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(gedcom_text)
            self.window.current_export_dir = os.path.dirname(dest_path)
            self.exported_path = dest_path
            self.accept()
        except Exception as exc:
            QMessageBox.warning(
                self,
                _bk_gedcom_review_text(self.window, "warn_title"),
                _bk_gedcom_review_text(self.window, "gedcom_review_export_failed", exc),
            )


def _bk_lm_on_gedcom_done_review(self, path: str, gedcom_text: str):
    worker = getattr(self, "_bk_gedcom_worker", None)
    structured_data = None
    if worker is not None:
        try:
            structured_data = getattr(worker, "_bk_gedcom_structured_data", None)
            structured_data = _bk_gedcom_review_deepcopy(structured_data) if isinstance(structured_data, dict) else None
        except Exception:
            structured_data = None
        try:
            worker.deleteLater()
        except Exception:
            pass
    self._bk_gedcom_worker = None

    if getattr(self, "_bk_gedcom_dialog", None):
        try:
            self._bk_gedcom_dialog.close()
        except Exception:
            pass
        self._bk_gedcom_dialog = None

    try:
        self.act_ai_revise.setEnabled(True)
    except Exception:
        pass
    try:
        if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
            self.btn_ai_revise_bottom.setEnabled(True)
    except Exception:
        pass

    gedcom_text = _bk_gedcom_review_finalize_text(gedcom_text)
    try:
        self._bk_last_gedcom_by_path[path] = gedcom_text
    except Exception:
        self._bk_last_gedcom_by_path = {path: gedcom_text}

    dlg = BKGedcomReviewDialog(self, path, gedcom_text, structured_data, self)
    dlg.exec()

    if dlg.exported_path:
        self.status_bar.showMessage(_bk_gedcom_review_text(self, "gedcom_review_export_done", os.path.basename(dlg.exported_path)), 5000)
        try:
            self._log(_bk_gedcom_review_text(self, "log_gedcom_done", dlg.exported_path))
        except Exception:
            pass
    else:
        self.status_bar.showMessage(_bk_gedcom_review_text(self, "gedcom_review_export_cancelled"), 5000)
        try:
            self._log(_bk_gedcom_review_text(self, "log_gedcom_not_saved", os.path.basename(path)))
        except Exception:
            pass

    try:
        _bk_lm_update_dropdown_state(self)
    except Exception:
        pass


_BK_GEDCOM_REVIEW_PREV_INIT = MainWindow.__init__


def _bk_gedcom_review_init(self, *args, **kwargs):
    _BK_GEDCOM_REVIEW_PREV_INIT(self, *args, **kwargs)
    try:
        # Sicherstellen, dass eine bereits existierende Menüverdrahtung beim nächsten GEDCOM-Lauf
        # die neue Review-Methode verwendet.
        if hasattr(self, "act_ai_menu_gedcom") and hasattr(self, "_bk_lm_generate_gedcom"):
            try:
                self.act_ai_menu_gedcom.triggered.disconnect()
            except Exception:
                pass
            self.act_ai_menu_gedcom.triggered.connect(lambda _checked=False: self._bk_lm_generate_gedcom())
    except Exception:
        pass


_BK_GEDCOM_REVIEW_PREV_RETRANSLATE = MainWindow.retranslate_ui


def _bk_gedcom_review_retranslate(self, *args, **kwargs):
    _BK_GEDCOM_REVIEW_PREV_RETRANSLATE(self, *args, **kwargs)
    try:
        if hasattr(self, "act_ai_menu_gedcom"):
            self.act_ai_menu_gedcom.setText(self._tr("act_lm_generate_gedcom"))
    except Exception:
        pass


_bk_gedcom_review_install_translations()

MainWindow.__init__ = _bk_gedcom_review_init
MainWindow.retranslate_ui = _bk_gedcom_review_retranslate
MainWindow._bk_lm_on_gedcom_done_gui = _bk_lm_on_gedcom_done_review


# =============================================================================
# Ursprünglich: 24_bk_lm_prompt_editor_ux_opt.py
# =============================================================================

"""Optimierter Prompt-Editor für lokale KI-Prompts.

Diese späte Patch-Datei macht die GEDCOM-Prompts verständlicher:
- Hauptweg: strukturierte GEDCOM-Datenextraktion als JSON, daraus baut das Programm GEDCOM.
- Fallback: direkte GEDCOM-Erzeugung nur als Reserve, optional einblendbar.

Die Prompt-Schlüssel bleiben unverändert, damit bestehende gespeicherte Prompts
nicht verloren gehen.
"""


_BK_PROMPT_UX_ORDER = (
    ("group", "prompt_group_local_ocr"),
    ("ai_prompt_single_system", "lm_prompt_single_system"),
    ("ai_prompt_single_user", "lm_prompt_single_user"),
    ("ai_prompt_block_system", "lm_prompt_block_system"),
    ("ai_prompt_block_user", "lm_prompt_block_user"),
    ("ai_prompt_page_system", "lm_prompt_page_system"),
    ("ai_prompt_page_user", "lm_prompt_page_user"),
    ("ai_prompt_decision_system", "lm_prompt_decision_system"),
    ("ai_prompt_decision_user", "lm_prompt_decision_user"),
    ("ai_prompt_fullpage_lm_ocr_system", "lm_prompt_fullpage_ocr_system"),
    ("ai_prompt_fullpage_lm_ocr_user", "lm_prompt_fullpage_ocr_user"),
    ("group", "prompt_group_gedcom_main"),
    ("ai_prompt_gedcom_extract_system", "lm_prompt_gedcom_extract_system"),
    ("ai_prompt_gedcom_extract_user", "lm_prompt_gedcom_extract_user"),
    ("group_advanced", "prompt_group_gedcom_fallback"),
    ("ai_prompt_gedcom_system", "lm_prompt_gedcom_system"),
    ("ai_prompt_gedcom_user", "lm_prompt_gedcom_user"),
)

_BK_PROMPT_UX_ADVANCED_KEYS = {"ai_prompt_gedcom_system", "ai_prompt_gedcom_user"}

_BK_PROMPT_UX_DESC_KEYS = {
    "ai_prompt_single_system": "prompt_desc_single_system",
    "ai_prompt_single_user": "prompt_desc_single_user",
    "ai_prompt_block_system": "prompt_desc_block_system",
    "ai_prompt_block_user": "prompt_desc_block_user",
    "ai_prompt_page_system": "prompt_desc_page_system",
    "ai_prompt_page_user": "prompt_desc_page_user",
    "ai_prompt_decision_system": "prompt_desc_decision_system",
    "ai_prompt_decision_user": "prompt_desc_decision_user",
    "ai_prompt_fullpage_lm_ocr_system": "prompt_desc_fullpage_ocr_system",
    "ai_prompt_fullpage_lm_ocr_user": "prompt_desc_fullpage_ocr_user",
    "ai_prompt_gedcom_extract_system": "prompt_desc_gedcom_extract_system",
    "ai_prompt_gedcom_extract_user": "prompt_desc_gedcom_extract_user",
    "ai_prompt_gedcom_system": "prompt_desc_gedcom_system",
    "ai_prompt_gedcom_user": "prompt_desc_gedcom_user",
}


def _bk_prompt_ux_install_texts():
    for lang, mapping in _BK_PROMPT_UX_EXTRA_TEXTS.items():
        try:
            translation.TRANSLATIONS.setdefault(lang, {}).update(mapping)
        except Exception:
            try:
                TRANSLATIONS.setdefault(lang, {}).update(mapping)
            except Exception:
                pass
        try:
            if "_BK_LM_OPTIONS_TEXTS" in globals():
                _BK_LM_OPTIONS_TEXTS.setdefault(lang, {}).update(mapping)
        except Exception:
            pass

    try:
        existing = dict(_BK_LM_PROMPT_KEYS)
        ordered = []
        seen = set()
        for key, label in _BK_PROMPT_UX_ORDER:
            if key.startswith("group"):
                continue
            if key not in seen:
                ordered.append((key, label))
                seen.add(key)
        for key, label in existing.items():
            if key not in seen:
                ordered.append((key, label))
                seen.add(key)
        globals()["_BK_LM_PROMPT_KEYS"] = tuple(ordered)
    except Exception:
        pass


def _bk_prompt_ux_text(window, key: str, *args) -> str:
    try:
        return _bk_lm_opt_text(window, key, *args)
    except Exception:
        lang = getattr(window, "current_lang", "de")
        mapping = _BK_PROMPT_UX_EXTRA_TEXTS.get(lang) or _BK_PROMPT_UX_EXTRA_TEXTS["de"]
        text = mapping.get(key, _BK_PROMPT_UX_EXTRA_TEXTS["de"].get(key, key))
        try:
            return text.format(*args) if args else text
        except Exception:
            return text


def _bk_prompt_ux_ordered_items(show_advanced: bool):
    out = []
    for key, label_key in _BK_PROMPT_UX_ORDER:
        if key == "group_advanced" and not show_advanced:
            continue
        if key in _BK_PROMPT_UX_ADVANCED_KEYS and not show_advanced:
            continue
        if key == "group":
            out.append(("group", label_key))
            continue
        if key == "group_advanced":
            out.append(("group", label_key))
            continue
        out.append((key, label_key))
    return out


def _bk_prompt_ux_make_group_item(text: str):
    item = QListWidgetItem(text)
    try:
        flags = item.flags()
        item.setFlags(flags & ~Qt.ItemIsSelectable & ~Qt.ItemIsEnabled)
    except Exception:
        try:
            item.setFlags(Qt.NoItemFlags)
        except Exception:
            pass
    try:
        font = item.font()
        font.setBold(True)
        item.setFont(font)
    except Exception:
        pass
    item.setData(Qt.UserRole, "")
    return item


def _bk_lm_show_prompt_settings_dialog(self):
    lang = getattr(self, "current_lang", "de")

    dlg = QDialog(self)
    dlg.setWindowTitle(_bk_prompt_ux_text(self, "dlg_lm_prompts_title"))
    dlg.resize(1180, 760)
    dlg.setMinimumSize(980, 620)

    layout = QVBoxLayout(dlg)

    hint = QLabel(_bk_prompt_ux_text(self, "dlg_lm_prompts_hint_optimized"))
    hint.setWordWrap(True)
    layout.addWidget(hint)

    show_advanced = QCheckBox(_bk_prompt_ux_text(self, "chk_show_advanced_prompts"))
    show_advanced.setChecked(False)
    layout.addWidget(show_advanced)

    body = QHBoxLayout()
    prompt_list = QListWidget()
    prompt_list.setMinimumWidth(360)
    prompt_list.setMaximumWidth(460)

    right = QVBoxLayout()
    desc_label = QLabel("")
    desc_label.setWordWrap(True)
    desc_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
    try:
        desc_label.setStyleSheet("font-weight: 600; padding: 6px;")
    except Exception:
        pass
    editor = QPlainTextEdit()
    editor.setLineWrapMode(QPlainTextEdit.NoWrap)
    right.addWidget(desc_label)
    right.addWidget(editor, 1)

    body.addWidget(prompt_list, 0)
    body.addLayout(right, 1)
    layout.addLayout(body, 1)

    cache = {}
    for prompt_key, _label_key in _BK_LM_PROMPT_KEYS:
        override = _bk_lm_prompt_override(self, prompt_key)
        cache[prompt_key] = override if override else _bk_lm_default_prompt(lang, prompt_key)

    state = {"current_key": None, "loading": False}

    def _store_current_editor():
        if state.get("loading"):
            return
        key = state.get("current_key")
        if key:
            cache[key] = editor.toPlainText()

    def _select_first_prompt():
        for row in range(prompt_list.count()):
            item = prompt_list.item(row)
            if item and item.data(Qt.UserRole):
                prompt_list.setCurrentRow(row)
                return
        state["current_key"] = None
        editor.clear()
        desc_label.clear()

    def _rebuild_list(keep_key=None):
        if keep_key is None:
            keep_key = state.get("current_key")
        prompt_list.blockSignals(True)
        prompt_list.clear()
        target_row = -1
        for key, label_key in _bk_prompt_ux_ordered_items(show_advanced.isChecked()):
            if key == "group":
                prompt_list.addItem(_bk_prompt_ux_make_group_item(_bk_prompt_ux_text(self, label_key)))
                continue
            item = QListWidgetItem(_bk_prompt_ux_text(self, label_key))
            item.setData(Qt.UserRole, key)
            prompt_list.addItem(item)
            if key == keep_key:
                target_row = prompt_list.count() - 1
        prompt_list.blockSignals(False)
        if target_row >= 0:
            prompt_list.setCurrentRow(target_row)
        else:
            _select_first_prompt()

    def _load_row(row: int):
        _store_current_editor()
        item = prompt_list.item(row)
        key = item.data(Qt.UserRole) if item is not None else ""
        if not key:
            state["current_key"] = None
            state["loading"] = True
            editor.clear()
            desc_label.clear()
            state["loading"] = False
            return
        state["current_key"] = key
        desc_key = _BK_PROMPT_UX_DESC_KEYS.get(key, "")
        desc_label.setText(_bk_prompt_ux_text(self, desc_key) if desc_key else "")
        state["loading"] = True
        editor.setPlainText(cache.get(key, _bk_lm_default_prompt(lang, key)))
        state["loading"] = False

    def _toggle_advanced(_checked=False):
        _store_current_editor()
        _rebuild_list(state.get("current_key"))

    prompt_list.currentRowChanged.connect(_load_row)
    show_advanced.toggled.connect(_toggle_advanced)
    _rebuild_list()

    buttons = QDialogButtonBox()
    save_btn = buttons.addButton(_bk_prompt_ux_text(self, "btn_save"), QDialogButtonBox.AcceptRole)
    reset_selected_btn = buttons.addButton(_bk_prompt_ux_text(self, "btn_reset_selected_prompt"), QDialogButtonBox.ActionRole)
    reset_all_btn = buttons.addButton(_bk_prompt_ux_text(self, "btn_reset_all_prompts"), QDialogButtonBox.ActionRole)
    close_btn = buttons.addButton(_bk_prompt_ux_text(self, "btn_close"), QDialogButtonBox.RejectRole)

    def _save_all():
        _store_current_editor()
        for prompt_key, _label_key in _BK_LM_PROMPT_KEYS:
            value = str(cache.get(prompt_key, "") or "")
            default = _bk_lm_default_prompt(lang, prompt_key)
            settings_key = _bk_lm_prompt_settings_key(lang, prompt_key)
            try:
                if value == default:
                    self.settings.remove(settings_key)
                else:
                    self.settings.setValue(settings_key, value)
            except Exception:
                pass
        self.status_bar.showMessage(_bk_prompt_ux_text(self, "msg_lm_prompts_saved"), 4000)
        dlg.accept()

    def _reset_selected():
        item = prompt_list.currentItem()
        if item is None:
            return
        key = item.data(Qt.UserRole)
        if not key:
            return
        default = _bk_lm_default_prompt(lang, key)
        cache[key] = default
        state["loading"] = True
        editor.setPlainText(default)
        state["loading"] = False
        try:
            self.settings.remove(_bk_lm_prompt_settings_key(lang, key))
        except Exception:
            pass
        self.status_bar.showMessage(_bk_prompt_ux_text(self, "msg_lm_prompt_reset"), 4000)

    def _reset_all():
        for prompt_key, _label_key in _BK_LM_PROMPT_KEYS:
            cache[prompt_key] = _bk_lm_default_prompt(lang, prompt_key)
            try:
                self.settings.remove(_bk_lm_prompt_settings_key(lang, prompt_key))
            except Exception:
                pass
        key = state.get("current_key")
        if key:
            state["loading"] = True
            editor.setPlainText(cache.get(key, ""))
            state["loading"] = False
        self.status_bar.showMessage(_bk_prompt_ux_text(self, "msg_lm_prompts_reset_all"), 4000)

    save_btn.clicked.connect(_save_all)
    reset_selected_btn.clicked.connect(_reset_selected)
    reset_all_btn.clicked.connect(_reset_all)
    close_btn.clicked.connect(dlg.reject)

    layout.addWidget(buttons)
    dlg.exec()


_bk_prompt_ux_install_texts()

MainWindow._bk_lm_show_prompt_settings_dialog = _bk_lm_show_prompt_settings_dialog
# Wichtig: Die QAction aus Datei 17 nutzt einen Lambda mit dem globalen Funktionsnamen.
# Durch diese Neudefinition wird auch dieser bestehende Menüeintrag auf den optimierten
# Dialog umgeleitet.
