from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
def _bk_lm_show_token_settings_dialog(self):
    if not hasattr(self, "lm_token_limits"):
        _bk_lm_load_token_settings(self)
    dlg = QDialog(self)
    dlg.setWindowTitle(_bk_lm_opt_text(self, "dlg_lm_token_title"))
    dlg.setMinimumWidth(560)
    layout = QVBoxLayout(dlg)
    hint = QLabel(_bk_lm_opt_text(self, "dlg_lm_token_hint"))
    hint.setWordWrap(True)
    layout.addWidget(hint)
    form = QFormLayout()
    spins = {}
    for kind, label_key in _BK_LM_TOKEN_KEYS:
        spin = QSpinBox()
        if kind == "canonical":
            spin.setRange(9000, 128000)
        else:
            spin.setRange(64, 64000)
        spin.setSingleStep(100)
        spin.setValue(max(9000, _lm_token_limit(self, kind)) if kind == "canonical" else _lm_token_limit(self, kind))
        spin.setSuffix(_bk_lm_opt_text(self, "unit_tokens_suffix"))
        spins[kind] = spin
        form.addRow(_bk_lm_opt_text(self, label_key), spin)
    layout.addLayout(form)
    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    buttons.button(QDialogButtonBox.Ok).setText(_bk_lm_opt_text(self, "btn_save"))
    buttons.button(QDialogButtonBox.Cancel).setText(_bk_lm_opt_text(self, "btn_cancel"))
    reset_btn = buttons.addButton(_bk_lm_opt_text(self, "btn_restore_defaults"), QDialogButtonBox.ResetRole)
    def _restore_defaults():
        for kind, spin in spins.items():
            spin.setValue(_BK_LM_TOKEN_DEFAULTS.get(kind, 1200))
    def _save():
        if not hasattr(self, "lm_token_limits"):
            self.lm_token_limits = {}
        for kind, spin in spins.items():
            value = int(spin.value())
            self.lm_token_limits[kind] = value
            try:
                self.settings.setValue(_bk_lm_token_settings_key(kind), value)
            except Exception:
                pass
        self.status_bar.showMessage(_bk_lm_opt_text(self, "msg_lm_tokens_saved"), 4000)
        dlg.accept()
    reset_btn.clicked.connect(_restore_defaults)
    buttons.accepted.connect(_save)
    buttons.rejected.connect(dlg.reject)
    layout.addWidget(buttons)
    dlg.exec()
def _bk_lm_show_custom_context_dialog(self):
    if not hasattr(self, "lm_custom_context"):
        _bk_lm_load_custom_context(self)
    dlg = QDialog(self)
    dlg.setWindowTitle(_bk_lm_opt_text(self, "dlg_lm_custom_context_title"))
    dlg.resize(820, 560)
    dlg.setMinimumSize(680, 420)
    layout = QVBoxLayout(dlg)
    hint = QLabel(_bk_lm_opt_text(self, "dlg_lm_custom_context_hint"))
    hint.setWordWrap(True)
    layout.addWidget(hint)
    editor = QPlainTextEdit()
    editor.setPlaceholderText(_bk_lm_opt_text(self, "dlg_lm_custom_context_placeholder"))
    editor.setPlainText(_bk_lm_custom_context(self))
    layout.addWidget(editor, 1)
    buttons = QDialogButtonBox()
    save_btn = buttons.addButton(_bk_lm_opt_text(self, "btn_save"), QDialogButtonBox.AcceptRole)
    clear_btn = buttons.addButton(_bk_lm_opt_text(self, "btn_clear"), QDialogButtonBox.ActionRole)
    close_btn = buttons.addButton(_bk_lm_opt_text(self, "btn_close"), QDialogButtonBox.RejectRole)
    def _save():
        value = editor.toPlainText().strip()
        self.lm_custom_context = value
        try:
            if value:
                self.settings.setValue(_bk_lm_custom_context_settings_key(), value)
            else:
                self.settings.remove(_bk_lm_custom_context_settings_key())
        except Exception:
            pass
        self.status_bar.showMessage(_bk_lm_opt_text(self, "msg_lm_custom_context_saved"), 4000)
        dlg.accept()
    def _clear():
        editor.clear()
        self.lm_custom_context = ""
        try:
            self.settings.remove(_bk_lm_custom_context_settings_key())
        except Exception:
            pass
        self.status_bar.showMessage(_bk_lm_opt_text(self, "msg_lm_custom_context_cleared"), 4000)
    save_btn.clicked.connect(_save)
    clear_btn.clicked.connect(_clear)
    close_btn.clicked.connect(dlg.reject)
    layout.addWidget(buttons)
    dlg.exec()
def _bk_lm_prompt_section_label(prompt_key: str) -> str:
    key = str(prompt_key)
    if "canonical" in key or "postgresql" in key or "neo4j" in key or "sqlite" in key:
        return "section_structured_json_prompts"
    if "gedcom" in key:
        return "section_gedcom_prompts"
    return "section_local_ocr_prompts"
__all__ = [
    '_bk_lm_prompt_section_label',
    '_bk_lm_show_custom_context_dialog',
    '_bk_lm_show_token_settings_dialog',
]
register_globals('bk', globals(), __all__)
