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
