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
        lang = getattr(window, "current_lang", translation.DEFAULT_LANGUAGE)
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
