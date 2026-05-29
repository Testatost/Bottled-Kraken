from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
def _bk_lm_show_prompt_settings_dialog(self):
    lang = getattr(self, "current_lang", translation.DEFAULT_LANGUAGE)
    dlg = QDialog(self)
    dlg.setWindowTitle(_bk_lm_opt_text(self, "dlg_lm_prompts_title"))
    dlg.resize(1100, 720)
    dlg.setMinimumSize(900, 580)
    layout = QVBoxLayout(dlg)
    hint = QLabel(_bk_lm_opt_text(self, "dlg_lm_prompts_hint"))
    hint.setWordWrap(True)
    layout.addWidget(hint)
    body = QHBoxLayout()
    prompt_list = QListWidget()
    prompt_list.setMinimumWidth(300)
    editor = QPlainTextEdit()
    editor.setLineWrapMode(QPlainTextEdit.NoWrap)
    cache = {}
    for prompt_key, _label_key in _BK_LM_PROMPT_KEYS:
        override = _bk_lm_prompt_override(self, prompt_key)
        cache[prompt_key] = override if override else _bk_lm_default_prompt(lang, prompt_key)
    current_section = None
    for prompt_key, label_key in _BK_LM_PROMPT_KEYS:
        section = _bk_lm_prompt_section_label(prompt_key)
        if section != current_section:
            header = QListWidgetItem(_bk_lm_opt_text(self, section))
            header.setData(Qt.UserRole, "")
            header.setFlags(header.flags() & ~Qt.ItemIsEnabled & ~Qt.ItemIsSelectable)
            font = header.font()
            font.setBold(True)
            header.setFont(font)
            prompt_list.addItem(header)
            current_section = section
        item = QListWidgetItem(_bk_lm_opt_text(self, label_key))
        item.setData(Qt.UserRole, prompt_key)
        prompt_list.addItem(item)
    state = {"current_key": None}
    def _store_current_editor():
        key = state.get("current_key")
        if key:
            cache[key] = editor.toPlainText()
    def _load_row(row: int):
        _store_current_editor()
        item = prompt_list.item(row)
        if item is None:
            state["current_key"] = None
            editor.clear()
            return
        key = item.data(Qt.UserRole)
        if not key:
            state["current_key"] = None
            editor.clear()
            return
        state["current_key"] = key
        editor.setPlainText(cache.get(key, _bk_lm_default_prompt(lang, key)))
    prompt_list.currentRowChanged.connect(_load_row)
    body.addWidget(prompt_list, 0)
    body.addWidget(editor, 1)
    layout.addLayout(body, 1)
    buttons = QDialogButtonBox()
    save_btn = buttons.addButton(_bk_lm_opt_text(self, "btn_save"), QDialogButtonBox.AcceptRole)
    reset_selected_btn = buttons.addButton(_bk_lm_opt_text(self, "btn_reset_selected_prompt"), QDialogButtonBox.ActionRole)
    reset_all_btn = buttons.addButton(_bk_lm_opt_text(self, "btn_reset_all_prompts"), QDialogButtonBox.ActionRole)
    close_btn = buttons.addButton(_bk_lm_opt_text(self, "btn_close"), QDialogButtonBox.RejectRole)
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
        self.status_bar.showMessage(_bk_lm_opt_text(self, "msg_lm_prompts_saved"), 4000)
        dlg.accept()
    def _reset_selected():
        item = prompt_list.currentItem()
        if item is None:
            return
        key = item.data(Qt.UserRole)
        default = _bk_lm_default_prompt(lang, key)
        cache[key] = default
        editor.setPlainText(default)
        try:
            self.settings.remove(_bk_lm_prompt_settings_key(lang, key))
        except Exception:
            pass
        self.status_bar.showMessage(_bk_lm_opt_text(self, "msg_lm_prompt_reset"), 4000)
    def _reset_all():
        for prompt_key, _label_key in _BK_LM_PROMPT_KEYS:
            cache[prompt_key] = _bk_lm_default_prompt(lang, prompt_key)
            try:
                self.settings.remove(_bk_lm_prompt_settings_key(lang, prompt_key))
            except Exception:
                pass
        current = prompt_list.currentRow()
        if current >= 0:
            key = prompt_list.item(current).data(Qt.UserRole)
            editor.setPlainText(cache.get(key, ""))
        self.status_bar.showMessage(_bk_lm_opt_text(self, "msg_lm_prompts_reset_all"), 4000)
    save_btn.clicked.connect(_save_all)
    reset_selected_btn.clicked.connect(_reset_selected)
    reset_all_btn.clicked.connect(_reset_all)
    close_btn.clicked.connect(dlg.reject)
    layout.addWidget(buttons)
    for _row in range(prompt_list.count()):
        _item = prompt_list.item(_row)
        if _item is not None and _item.data(Qt.UserRole):
            prompt_list.setCurrentRow(_row)
            break
    dlg.exec()
_BK_LM_OPTIONS_PREV_TR = MainWindow._tr
__all__ = [
    '_BK_LM_OPTIONS_PREV_TR',
    '_bk_lm_show_prompt_settings_dialog',
]
register_globals('bk', globals(), __all__)
