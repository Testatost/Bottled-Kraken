from bottled_kraken.module_registry import register_globals, seed_globals
from bottled_kraken.common.chain_consolidation import register_init_delta, register_retranslate_delta
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
def _bk_gedcom_init(self, *args, **kwargs):
    self._bk_gedcom_worker = None
    self._bk_gedcom_dialog = None
    self._bk_gedcom_context = None
    self._bk_last_gedcom_by_path = {}
    _bk_gedcom_ensure_menu_action(self)
def _bk_gedcom_retranslate(self, *args, **kwargs):
    try:
        _bk_gedcom_ensure_menu_action(self)
    except Exception:
        pass
    if hasattr(self, "act_ai_menu_gedcom"):
        self.act_ai_menu_gedcom.setText(self._tr("act_lm_generate_gedcom"))
_BK_GEDCOM_PREV_CANCEL_LOCAL_JSON = _bk_lm_cancel_local_json if "_bk_lm_cancel_local_json" in globals() else None
_bk_gedcom_install_translations()
register_init_delta(_bk_gedcom_init)
register_retranslate_delta(_bk_gedcom_retranslate)
MainWindow._bk_lm_cancel_gedcom = _bk_lm_cancel_gedcom
__all__ = [
    '_BK_GEDCOM_PREV_ANY_JOB_RUNNING',
    '_BK_GEDCOM_PREV_CANCEL_LOCAL_JSON',
    '_BK_GEDCOM_PREV_UPDATE_DROPDOWN_STATE',
    '_BK_GEDCOM_PROMPT_DEFAULTS',
    '_BK_GEDCOM_REVIEW_TEXTS',
    '_BK_GEDCOM_ROBUST_TEXTS',
    '_BK_GEDCOM_SAVE_FIX_TEXTS',
    '_BK_GEDCOM_STRUCTURED_TEXTS',
    '_BK_GEDCOM_VISION_TEXTS',
    '_BK_PROMPT_UX_EXTRA_TEXTS',
    '_bk_gedcom_ensure_menu_action',
    '_bk_gedcom_init',
    '_bk_gedcom_retranslate',
    '_bk_lm_any_job_running',
    '_bk_lm_cancel_gedcom',
    '_bk_lm_on_gedcom_done',
    '_bk_lm_on_gedcom_failed',
    '_bk_lm_update_dropdown_state',
]
register_globals('bk', globals(), __all__)
