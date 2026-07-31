from bottled_kraken.module_registry import register_globals, seed_globals
from bottled_kraken.common.chain_consolidation import register_init_delta, register_retranslate_delta
seed_globals('bk', globals())
# BK-CLEANUP: zuvor in lm_options_prompt_dialog.py (Modul entfernt, Dialog durch
# gedcom_prompt_ux_dialog ersetzt); Capture-Position in der Ladekette unveraendert.
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
                text = override.format(*args) if args else override
            except Exception:
                text = override
        else:
            text = _BK_LM_OPTIONS_PREV_TR(self, key, *args)
        return _bk_lm_apply_custom_context(self, key, text)
    return _BK_LM_OPTIONS_PREV_TR(self, key, *args)
def _bk_lm_options_init(self, *args, **kwargs):
    _bk_lm_load_token_settings(self)
    _bk_lm_load_custom_context(self)
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
    self.act_lm_custom_context = QAction(_bk_lm_opt_text(self, "act_lm_custom_context"), self)
    self.act_lm_custom_context.triggered.connect(lambda: _bk_lm_show_custom_context_dialog(self))
    actions = self.options_menu.actions()
    before = actions[0] if actions else None
    if before is not None:
        self.options_menu.insertAction(before, self.act_lm_token_settings)
        self.options_menu.insertAction(before, self.act_lm_prompt_settings)
        self.options_menu.insertAction(before, self.act_lm_custom_context)
        self.options_menu.insertSeparator(before)
    else:
        self.options_menu.addAction(self.act_lm_token_settings)
        self.options_menu.addAction(self.act_lm_prompt_settings)
        self.options_menu.addAction(self.act_lm_custom_context)
        self.options_menu.addSeparator()
def _bk_lm_options_retranslate(self, *args, **kwargs):
    if hasattr(self, "act_lm_token_settings"):
        self.act_lm_token_settings.setText(_bk_lm_opt_text(self, "act_lm_token_settings"))
    if hasattr(self, "act_lm_prompt_settings"):
        self.act_lm_prompt_settings.setText(_bk_lm_opt_text(self, "act_lm_prompt_settings"))
    if hasattr(self, "act_lm_custom_context"):
        self.act_lm_custom_context.setText(_bk_lm_opt_text(self, "act_lm_custom_context"))
MainWindow._tr = _bk_lm_options_tr
register_init_delta(_bk_lm_options_init)
MainWindow._init_menu = _bk_lm_options_init_menu
register_retranslate_delta(_bk_lm_options_retranslate)
MainWindow._lm_token_limit = _lm_token_limit
MainWindow._bk_lm_token_limit_for_json = _bk_lm_token_limit_for_json
MainWindow._bk_lm_show_token_settings_dialog = _bk_lm_show_token_settings_dialog
MainWindow._bk_lm_show_custom_context_dialog = _bk_lm_show_custom_context_dialog
__all__ = [
    '_BK_LM_OPTIONS_PREV_TR',
    '_BK_LM_OPTIONS_PREV_INIT_MENU',
    '_bk_lm_options_init',
    '_bk_lm_options_init_menu',
    '_bk_lm_options_retranslate',
    '_bk_lm_options_tr',
]
register_globals('bk', globals(), __all__)
