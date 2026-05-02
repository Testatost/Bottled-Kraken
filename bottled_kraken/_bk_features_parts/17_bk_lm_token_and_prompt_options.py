"""Optionen für lokale LM-Token und lokale KI-Prompts.

Diese späte Patch-Datei ergänzt unter "Optionen" zwei Dialoge:
- Token-Anzahl für lokale LM-Funktionen
- Prompt-Editor für lokale KI-Prompts

Außerdem wird im Hinweise-Dialog der erste Bereich von "Ablauf" zu
"Übersicht" umbenannt.
"""

_BK_LM_TOKEN_DEFAULTS = {
    "current_line": 1200,
    "selected_lines": 1200,
    "all_lines": 1200,
    "lm_ocr": 4500,
    "gedcom": 6000,
}

_BK_LM_TOKEN_KEYS = (
    ("current_line", "lm_token_current_line"),
    ("selected_lines", "lm_token_selected_lines"),
    ("all_lines", "lm_token_all_lines"),
    ("lm_ocr", "lm_token_lm_ocr"),
    ("gedcom", "lm_token_gedcom"),
)

_BK_LM_PROMPT_KEYS = (
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
    ("ai_prompt_gedcom_system", "lm_prompt_gedcom_system"),
    ("ai_prompt_gedcom_user", "lm_prompt_gedcom_user"),
)

from ._translation_data.bk_lm_options_translations import BK_LM_OPTIONS_TRANSLATIONS as _BK_LM_OPTIONS_TEXTS


def _bk_lm_opt_text(self, key: str, *args) -> str:
    lang = getattr(self, "current_lang", "de")
    data = _BK_LM_OPTIONS_TEXTS.get(lang) or _BK_LM_OPTIONS_TEXTS["de"]
    txt = data.get(key, _BK_LM_OPTIONS_TEXTS["de"].get(key, key))
    try:
        return txt.format(*args) if args else txt
    except Exception:
        return txt


def _bk_lm_token_settings_key(kind: str) -> str:
    return f"lm_tokens/{kind}"


def _bk_lm_prompt_settings_key(lang: str, key: str) -> str:
    return f"lm_prompts/{lang}/{key}"


def _bk_lm_default_prompt(lang: str, key: str) -> str:
    lang = lang if lang in translation.TRANSLATIONS else "de"
    if key in translation.TRANSLATIONS.get(lang, {}):
        return str(translation.TRANSLATIONS[lang].get(key, ""))
    return str(translation.TRANSLATIONS.get("de", {}).get(key, key))


def _bk_lm_prompt_override(self, key: str) -> str:
    if key not in {k for k, _label in _BK_LM_PROMPT_KEYS}:
        return ""
    settings = getattr(self, "settings", None)
    if settings is None:
        return ""
    lang = getattr(self, "current_lang", "de")
    try:
        value = settings.value(_bk_lm_prompt_settings_key(lang, key), "", str)
    except Exception:
        value = ""
    return str(value or "")


def _bk_lm_load_token_settings(self):
    defaults = dict(_BK_LM_TOKEN_DEFAULTS)
    try:
        base = int(getattr(self, "ai_max_tokens", 1200) or 1200)
    except Exception:
        base = 1200
    defaults["current_line"] = base
    defaults["selected_lines"] = base
    defaults["all_lines"] = base
    defaults["lm_ocr"] = 4500
    defaults["gedcom"] = 6000

    self.lm_token_limits = {}
    settings = getattr(self, "settings", None)
    for kind, default in defaults.items():
        value = default
        if settings is not None:
            try:
                value = int(settings.value(_bk_lm_token_settings_key(kind), default, int))
            except Exception:
                value = default
        self.lm_token_limits[kind] = max(1, int(value))


def _lm_token_limit(self, kind: str) -> int:
    if not hasattr(self, "lm_token_limits"):
        _bk_lm_load_token_settings(self)
    kind = str(kind or "all_lines")
    if kind not in self.lm_token_limits:
        kind = "all_lines"
    try:
        return max(1, int(self.lm_token_limits.get(kind) or _BK_LM_TOKEN_DEFAULTS.get(kind, 1200)))
    except Exception:
        return int(_BK_LM_TOKEN_DEFAULTS.get(kind, 1200))


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
        spin.setRange(64, 64000)
        spin.setSingleStep(100)
        spin.setValue(_lm_token_limit(self, kind))
        spin.setSuffix(" tokens")
        spins[kind] = spin
        form.addRow(_bk_lm_opt_text(self, label_key), spin)

    layout.addLayout(form)

    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    buttons.button(QDialogButtonBox.Ok).setText(_bk_lm_opt_text(self, "btn_save"))
    buttons.button(QDialogButtonBox.Cancel).setText(self._tr("btn_cancel") if hasattr(self, "_tr") else "Abbrechen")
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


def _bk_lm_show_prompt_settings_dialog(self):
    lang = getattr(self, "current_lang", "de")

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

    for prompt_key, label_key in _BK_LM_PROMPT_KEYS:
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

    if prompt_list.count() > 0:
        prompt_list.setCurrentRow(0)

    dlg.exec()


_BK_LM_OPTIONS_PREV_TR = MainWindow._tr


def _bk_lm_options_tr(self, key: str, *args):
    if key == "help_nav_quick":
        return _bk_lm_opt_text(self, "help_nav_overview")
    if key == "help_html_quick":
        html_text = _BK_LM_OPTIONS_PREV_TR(self, key, *args)
        overview = _bk_lm_opt_text(self, "help_h1_overview")
        replacements = (
            '<div class="h1">Ablauf</div>',
            '<div class="h1">Workflow</div>',
            '<div class="h1">Déroulement</div>',
            '<div class="h1">Flux</div>',
        )
        for old in replacements:
            html_text = html_text.replace(old, f'<div class="h1">{overview}</div>', 1)
        return html_text
    if key in {prompt_key for prompt_key, _label_key in _BK_LM_PROMPT_KEYS}:
        override = _bk_lm_prompt_override(self, key)
        if override:
            try:
                return override.format(*args) if args else override
            except Exception:
                return override
    return _BK_LM_OPTIONS_PREV_TR(self, key, *args)


_BK_LM_OPTIONS_PREV_INIT = MainWindow.__init__


def _bk_lm_options_init(self, *args, **kwargs):
    _BK_LM_OPTIONS_PREV_INIT(self, *args, **kwargs)
    _bk_lm_load_token_settings(self)


_BK_LM_OPTIONS_PREV_INIT_MENU = MainWindow._init_menu


def _bk_lm_options_init_menu(self, *args, **kwargs):
    _BK_LM_OPTIONS_PREV_INIT_MENU(self, *args, **kwargs)

    if getattr(self, "_bk_lm_options_menu_installed", False):
        return
    self._bk_lm_options_menu_installed = True

    self.act_lm_token_settings = QAction(_bk_lm_opt_text(self, "act_lm_token_settings"), self)
    self.act_lm_token_settings.triggered.connect(lambda: _bk_lm_show_token_settings_dialog(self))

    self.act_lm_prompt_settings = QAction(_bk_lm_opt_text(self, "act_lm_prompt_settings"), self)
    self.act_lm_prompt_settings.triggered.connect(lambda: _bk_lm_show_prompt_settings_dialog(self))

    actions = self.options_menu.actions()
    before = actions[0] if actions else None
    if before is not None:
        self.options_menu.insertAction(before, self.act_lm_token_settings)
        self.options_menu.insertAction(before, self.act_lm_prompt_settings)
        self.options_menu.insertSeparator(before)
    else:
        self.options_menu.addAction(self.act_lm_token_settings)
        self.options_menu.addAction(self.act_lm_prompt_settings)
        self.options_menu.addSeparator()


_BK_LM_OPTIONS_PREV_RETRANSLATE = MainWindow.retranslate_ui


def _bk_lm_options_retranslate(self, *args, **kwargs):
    _BK_LM_OPTIONS_PREV_RETRANSLATE(self, *args, **kwargs)
    if hasattr(self, "act_lm_token_settings"):
        self.act_lm_token_settings.setText(_bk_lm_opt_text(self, "act_lm_token_settings"))
    if hasattr(self, "act_lm_prompt_settings"):
        self.act_lm_prompt_settings.setText(_bk_lm_opt_text(self, "act_lm_prompt_settings"))


MainWindow._tr = _bk_lm_options_tr
MainWindow.__init__ = _bk_lm_options_init
MainWindow._init_menu = _bk_lm_options_init_menu
MainWindow.retranslate_ui = _bk_lm_options_retranslate
MainWindow._lm_token_limit = _lm_token_limit
MainWindow._bk_lm_show_token_settings_dialog = _bk_lm_show_token_settings_dialog
MainWindow._bk_lm_show_prompt_settings_dialog = _bk_lm_show_prompt_settings_dialog
