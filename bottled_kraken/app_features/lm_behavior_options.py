from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
from PySide6.QtWidgets import QComboBox, QGroupBox, QTabWidget
_BK_LM_BEHAVIOR_SCOPES = (
    ("current_line", "lm_behavior_scope_current"),
    ("selected_lines", "lm_behavior_scope_selected"),
    ("all_lines", "lm_behavior_scope_all"),
)
_BK_LM_BEHAVIOR_OLD_DEFAULT_FILTERS = "\n".join((
    "```json", "```", "text:", "line:", "transcription:", "ocr_text:",
    "bbox:", "bbox_norm:", "box:", "textbox_norm:", "textbbox_norm:",
    "normalized_bbox:", "None", "null", "True", "False",
))
_BK_LM_BEHAVIOR_DEFAULTS = {
    "page_ocr": False,
    "use_overlay": True,
    "script_mode": AI_SCRIPT_PRINT,
    "pad_x": 0,
    "pad_y": 0,
    "extra_context_y": 0,
    "weight": "kraken_lm_revision",
    "filters": "",
}
_BK_LM_BEHAVIOR_LEGACY_WEIGHTING_ALIASES = ("weight", "weighting", "revision_mode")
_BK_LM_BEHAVIOR_FILTER_ALIASES = ("filters", "filter_text")
def _bk_lm_behavior_defaults_for_scope(scope: str) -> dict:
    data = dict(_BK_LM_BEHAVIOR_DEFAULTS)
    data["page_ocr"] = str(scope or "") == "all_lines"
    return data
_BK_LM_BEHAVIOR_PRESETS = {
    AI_SCRIPT_PRINT: (0, 0, 0),
    AI_SCRIPT_HANDWRITING: (16, 8, 18),
    AI_SCRIPT_MIXED: (9, 5, 9),
}
_BK_LM_BEHAVIOR_ACTIVE = None
def _bk_lm_behavior_key(scope: str, name: str) -> str:
    return f"lm_behavior/{scope}/{name}"
def _bk_lm_behavior_bool(value, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    txt = str(value).strip().lower()
    if txt in {"1", "true", "yes", "ja", "on"}:
        return True
    if txt in {"0", "false", "no", "nein", "off"}:
        return False
    return bool(default)
def _bk_lm_behavior_normalized(data=None) -> dict:
    out = dict(_BK_LM_BEHAVIOR_DEFAULTS)
    if isinstance(data, dict):
        out.update(data)
        for alias in _BK_LM_BEHAVIOR_LEGACY_WEIGHTING_ALIASES:
            if alias in data and str(data.get(alias, "")).strip():
                out["weight"] = data.get(alias)
                break
        for alias in _BK_LM_BEHAVIOR_FILTER_ALIASES:
            if alias in data:
                out["filters"] = data.get(alias)
                break
    out["page_ocr"] = _bk_lm_behavior_bool(out.get("page_ocr"), _BK_LM_BEHAVIOR_DEFAULTS.get("page_ocr", False))
    out["use_overlay"] = _bk_lm_behavior_bool(out.get("use_overlay"), _BK_LM_BEHAVIOR_DEFAULTS.get("use_overlay", True))
    out["script_mode"] = _normalize_ai_script_mode(out.get("script_mode"))
    mode = str(out.get("weight") or "").lower().strip()
    if mode in {"lm_first", "lm-ocr > kraken-ocr", "lm"}:
        out["weight"] = "lm_first"
    elif mode in {"kraken_first", "kraken-ocr > lm-ocr", "kraken"}:
        out["weight"] = "kraken_first"
    else:
        out["weight"] = "kraken_lm_revision"
    out["revision_mode"] = out["weight"]
    out["weighting"] = out["weight"]
    for key in ("pad_x", "pad_y", "extra_context_y"):
        try:
            out[key] = max(0, int(out.get(key, 0) or 0))
        except Exception:
            out[key] = 0
    out["filters"] = str(out.get("filters", "") or "")
    return out
def _bk_lm_load_behavior_settings(self):
    settings = getattr(self, "settings", None)
    self.lm_behavior_settings = {}
    version = str(settings.value("lm_behavior/schema_version", "1") or "1") if settings is not None else "3"
    for scope, _label_key in _BK_LM_BEHAVIOR_SCOPES:
        data = _bk_lm_behavior_defaults_for_scope(scope)
        if settings is not None:
            if version in {"1", "2"}:
                settings.setValue(_bk_lm_behavior_key(scope, "page_ocr"), data["page_ocr"])
                old_weight = str(settings.value(_bk_lm_behavior_key(scope, "weight"), "", str) or "")
                if version == "1" or old_weight.strip().lower() in {"", "lm_first"}:
                    settings.setValue(_bk_lm_behavior_key(scope, "weight"), data["weight"])
                old = str(settings.value(_bk_lm_behavior_key(scope, "filters"), "", str) or "")
                if not old.strip() or old.strip() == _BK_LM_BEHAVIOR_OLD_DEFAULT_FILTERS.strip():
                    settings.setValue(_bk_lm_behavior_key(scope, "filters"), "")
            data["page_ocr"] = _bk_lm_behavior_bool(settings.value(_bk_lm_behavior_key(scope, "page_ocr"), data["page_ocr"]), data["page_ocr"])
            data["use_overlay"] = _bk_lm_behavior_bool(settings.value(_bk_lm_behavior_key(scope, "use_overlay"), data["use_overlay"]), data["use_overlay"])
            data["script_mode"] = str(settings.value(_bk_lm_behavior_key(scope, "script_mode"), data["script_mode"], str) or data["script_mode"])
            legacy_weight = None
            for alias in _BK_LM_BEHAVIOR_LEGACY_WEIGHTING_ALIASES:
                legacy_weight = settings.value(_bk_lm_behavior_key(scope, alias), "", str)
                if str(legacy_weight or "").strip():
                    break
            data["weight"] = str(legacy_weight or data["weight"])
            legacy_filter = None
            for alias in _BK_LM_BEHAVIOR_FILTER_ALIASES:
                legacy_filter = settings.value(_bk_lm_behavior_key(scope, alias), "", str)
                if str(legacy_filter or "").strip():
                    break
            data["filters"] = str(legacy_filter or "")
            if data["filters"].strip() == _BK_LM_BEHAVIOR_OLD_DEFAULT_FILTERS.strip():
                data["filters"] = ""
            for key in ("pad_x", "pad_y", "extra_context_y"):
                try:
                    data[key] = int(settings.value(_bk_lm_behavior_key(scope, key), data[key], int))
                except Exception:
                    pass
        self.lm_behavior_settings[scope] = _bk_lm_behavior_normalized(data)
    if settings is not None and version in {"1", "2"}:
        try:
            settings.setValue("lm_behavior/schema_version", "3")
        except Exception:
            pass
def _lm_behavior_for_scope(self, scope: str) -> dict:
    if not hasattr(self, "lm_behavior_settings"):
        _bk_lm_load_behavior_settings(self)
    scope = str(scope or "all_lines")
    if scope not in dict(_BK_LM_BEHAVIOR_SCOPES):
        scope = "all_lines"
    return _bk_lm_behavior_normalized(getattr(self, "lm_behavior_settings", {}).get(scope))
def _bk_lm_save_behavior_settings(self, values: dict):
    self.lm_behavior_settings = {}
    settings = getattr(self, "settings", None)
    for scope, _label_key in _BK_LM_BEHAVIOR_SCOPES:
        data = _bk_lm_behavior_normalized(values.get(scope, {}))
        self.lm_behavior_settings[scope] = data
        if settings is None:
            continue
        for key, value in data.items():
            try:
                settings.setValue(_bk_lm_behavior_key(scope, key), value)
            except Exception:
                pass
        try:
            settings.setValue(_bk_lm_behavior_key(scope, "revision_mode"), data.get("weight", "kraken_lm_revision"))
            settings.setValue(_bk_lm_behavior_key(scope, "filter_text"), data.get("filters", ""))
        except Exception:
            pass
def _bk_lm_behavior_apply_preset(mode_combo, pad_x, pad_y, extra_y):
    mode = mode_combo.currentData() or AI_SCRIPT_PRINT
    px, py, ey = _BK_LM_BEHAVIOR_PRESETS.get(mode, _BK_LM_BEHAVIOR_PRESETS[AI_SCRIPT_PRINT])
    pad_x.setValue(px)
    pad_y.setValue(py)
    extra_y.setValue(ey)
def _bk_lm_show_behavior_dialog(self):
    if not hasattr(self, "lm_behavior_settings"):
        _bk_lm_load_behavior_settings(self)
    dlg = QDialog(self)
    dlg.setWindowTitle(_bk_lm_opt_text(self, "dlg_lm_behavior_title"))
    dlg.resize(760, 620)
    root = QVBoxLayout(dlg)
    hint = QLabel(_bk_lm_opt_text(self, "dlg_lm_behavior_hint"))
    hint.setWordWrap(True)
    root.addWidget(hint)
    tabs = QTabWidget()
    widgets = {}
    for scope, label_key in _BK_LM_BEHAVIOR_SCOPES:
        data = _lm_behavior_for_scope(self, scope)
        page = QWidget()
        layout = QVBoxLayout(page)
        box = QGroupBox(_bk_lm_opt_text(self, "lm_behavior_group_sources"))
        form = QFormLayout(box)
        page_ocr = QCheckBox(_bk_lm_opt_text(self, "lm_behavior_page_ocr"))
        page_ocr.setChecked(bool(data["page_ocr"]))
        use_overlay = QCheckBox(_bk_lm_opt_text(self, "lm_behavior_use_overlay"))
        use_overlay.setChecked(bool(data["use_overlay"]))
        mode_combo = QComboBox()
        for mode, key in ((AI_SCRIPT_PRINT, "btn_ai_script_print"), (AI_SCRIPT_HANDWRITING, "btn_ai_script_handwriting"), (AI_SCRIPT_MIXED, "btn_ai_script_mixed")):
            mode_combo.addItem(self._tr(key), mode)
        idx = mode_combo.findData(data["script_mode"])
        mode_combo.setCurrentIndex(max(0, idx))
        pad_x = QSpinBox(); pad_x.setRange(0, 500); pad_x.setValue(int(data["pad_x"]))
        pad_y = QSpinBox(); pad_y.setRange(0, 500); pad_y.setValue(int(data["pad_y"]))
        extra_y = QSpinBox(); extra_y.setRange(0, 500); extra_y.setValue(int(data["extra_context_y"]))
        preset_btn = QPushButton(_bk_lm_opt_text(self, "lm_behavior_apply_preset"))
        preset_btn.clicked.connect(lambda _=False, c=mode_combo, x=pad_x, y=pad_y, e=extra_y: _bk_lm_behavior_apply_preset(c, x, y, e))
        weight = QComboBox()
        weight.addItem(_bk_lm_opt_text(self, "lm_behavior_weight_revision"), "kraken_lm_revision")
        weight.addItem(_bk_lm_opt_text(self, "lm_behavior_weight_kraken"), "kraken_first")
        weight.addItem(_bk_lm_opt_text(self, "lm_behavior_weight_lm"), "lm_first")
        idx = weight.findData(data["weight"])
        weight.setCurrentIndex(max(0, idx))
        filters = QPlainTextEdit()
        filters.setPlaceholderText(_bk_lm_opt_text(self, "lm_behavior_filters_placeholder"))
        filters.setPlainText(str(data["filters"] or ""))
        filters.setMinimumHeight(90)
        form.addRow(page_ocr)
        form.addRow(use_overlay)
        form.addRow(_bk_lm_opt_text(self, "lm_behavior_script_mode"), mode_combo)
        form.addRow(_bk_lm_opt_text(self, "lm_behavior_pad_x"), pad_x)
        form.addRow(_bk_lm_opt_text(self, "lm_behavior_pad_y"), pad_y)
        form.addRow(_bk_lm_opt_text(self, "lm_behavior_extra_y"), extra_y)
        form.addRow("", preset_btn)
        form.addRow(_bk_lm_opt_text(self, "lm_behavior_weight"), weight)
        form.addRow(_bk_lm_opt_text(self, "lm_behavior_filters"), filters)
        layout.addWidget(box)
        layout.addStretch(1)
        tabs.addTab(page, _bk_lm_opt_text(self, label_key))
        widgets[scope] = (page_ocr, use_overlay, mode_combo, pad_x, pad_y, extra_y, weight, filters)
    root.addWidget(tabs, 1)
    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    buttons.button(QDialogButtonBox.Ok).setText(_bk_lm_opt_text(self, "btn_save"))
    buttons.button(QDialogButtonBox.Cancel).setText(_bk_lm_opt_text(self, "btn_cancel"))
    reset_btn = buttons.addButton(_bk_lm_opt_text(self, "btn_restore_defaults"), QDialogButtonBox.ResetRole)
    def reset_defaults():
        for scope, controls in widgets.items():
            page_ocr, use_overlay, mode_combo, pad_x, pad_y, extra_y, weight, filters = controls
            d = _bk_lm_behavior_defaults_for_scope(scope)
            page_ocr.setChecked(bool(d["page_ocr"]))
            use_overlay.setChecked(bool(d["use_overlay"]))
            mode_combo.setCurrentIndex(max(0, mode_combo.findData(d["script_mode"])))
            pad_x.setValue(int(d["pad_x"])); pad_y.setValue(int(d["pad_y"])); extra_y.setValue(int(d["extra_context_y"]))
            weight.setCurrentIndex(max(0, weight.findData(d["weight"])))
            filters.setPlainText(str(d["filters"] or ""))
    def save():
        values = {}
        for scope, controls in widgets.items():
            page_ocr, use_overlay, mode_combo, pad_x, pad_y, extra_y, weight, filters = controls
            values[scope] = {
                "page_ocr": page_ocr.isChecked(),
                "use_overlay": use_overlay.isChecked(),
                "script_mode": mode_combo.currentData() or AI_SCRIPT_PRINT,
                "pad_x": pad_x.value(),
                "pad_y": pad_y.value(),
                "extra_context_y": extra_y.value(),
                "weight": weight.currentData() or "kraken_lm_revision",
                "filters": filters.toPlainText(),
            }
        _bk_lm_save_behavior_settings(self, values)
        self.status_bar.showMessage(_bk_lm_opt_text(self, "msg_lm_behavior_saved"), 4000)
        dlg.accept()
    reset_btn.clicked.connect(reset_defaults)
    buttons.accepted.connect(save)
    buttons.rejected.connect(dlg.reject)
    root.addWidget(buttons)
    dlg.exec()
def _bk_lm_rehome_options_actions(self):
    menu = getattr(self, "revision_models_menu", None)
    if menu is None:
        return
    if not hasattr(self, "act_lm_behavior_settings"):
        self.act_lm_behavior_settings = QAction(_bk_lm_opt_text(self, "act_lm_behavior_settings"), self)
        self.act_lm_behavior_settings.triggered.connect(lambda: _bk_lm_show_behavior_dialog(self))
    option_actions = [
        getattr(self, "act_lm_token_settings", None),
        getattr(self, "act_lm_prompt_settings", None),
        getattr(self, "act_lm_custom_context", None),
        getattr(self, "act_lm_behavior_settings", None),
    ]
    for action in option_actions:
        if action is None:
            continue
        try:
            self.options_menu.removeAction(action)
        except Exception:
            pass
        try:
            menu.removeAction(action)
        except Exception:
            pass
    try:
        while self.options_menu.actions() and self.options_menu.actions()[0].isSeparator():
            self.options_menu.removeAction(self.options_menu.actions()[0])
    except Exception:
        pass
    before = getattr(self, "act_ptr_ai_tools", None)
    if before not in menu.actions():
        before = None
    for action in list(menu.actions()):
        try:
            if action.isSeparator() and (bool(action.property("bk_lm_behavior_separator")) or bool(action.property("bk_lm_server_separator"))):
                menu.removeAction(action)
        except Exception:
            pass
    server_action = getattr(self, "act_lm_base_url", None)
    if server_action in menu.actions():
        sep = QAction(self)
        sep.setSeparator(True)
        sep.setProperty("bk_lm_server_separator", True)
        actions = menu.actions()
        pos = actions.index(server_action)
        next_action = actions[pos + 1] if pos + 1 < len(actions) else None
        if next_action is not None:
            menu.insertAction(next_action, sep)
        else:
            menu.addAction(sep)
    main_option_actions = [
        getattr(self, "act_lm_token_settings", None),
        getattr(self, "act_lm_prompt_settings", None),
        getattr(self, "act_lm_custom_context", None),
    ]
    for action in main_option_actions:
        if action is None:
            continue
        if before is not None:
            menu.insertAction(before, action)
        else:
            menu.addAction(action)
    behavior_action = getattr(self, "act_lm_behavior_settings", None)
    if behavior_action is not None:
        sep = QAction(self)
        sep.setSeparator(True)
        sep.setProperty("bk_lm_behavior_separator", True)
        if before is not None:
            menu.insertAction(before, sep)
            menu.insertAction(before, behavior_action)
        else:
            menu.addSeparator()
            menu.addAction(behavior_action)
def _bk_lm_behavior_filter_text(worker, text: str) -> str:
    out = _clean_ocr_text(text or "")
    behavior = _bk_lm_behavior_normalized(getattr(worker, "lm_behavior", None))
    raw = str(behavior.get("filters") or "")
    filters = []
    for part in re.split(r"[\n,;]+", raw):
        part = part.strip()
        if part:
            filters.append(part)
    for token in filters:
        out = out.replace(token, "")
    return re.sub(r"\s{2,}", " ", out).strip()
def _bk_lm_behavior_weight(worker) -> str:
    return _bk_lm_behavior_normalized(getattr(worker, "lm_behavior", None)).get("weight", "kraken_lm_revision")
def _bk_lm_behavior_prompt(self, idx, kraken_text, page_context):
    behavior = _bk_lm_behavior_normalized(getattr(self, "lm_behavior", None))
    key = "lm_behavior_revision_prompt" if behavior.get("weight") == "kraken_lm_revision" else "lm_behavior_overlay_prompt"
    return _bk_lm_opt_text(self, key, int(idx), kraken_text, page_context)
try:
    _BK_LM_BEHAVIOR_PREV_MW_INIT = MainWindow.__init__
    def _bk_lm_behavior_mw_init(self, *args, **kwargs):
        _BK_LM_BEHAVIOR_PREV_MW_INIT(self, *args, **kwargs)
        _bk_lm_load_behavior_settings(self)
    MainWindow.__init__ = _bk_lm_behavior_mw_init
except Exception:
    pass
try:
    _BK_LM_BEHAVIOR_PREV_INIT_MENU = MainWindow._init_menu
    def _bk_lm_behavior_init_menu(self, *args, **kwargs):
        _BK_LM_BEHAVIOR_PREV_INIT_MENU(self, *args, **kwargs)
        _bk_lm_rehome_options_actions(self)
    MainWindow._init_menu = _bk_lm_behavior_init_menu
except Exception:
    pass
try:
    _BK_LM_BEHAVIOR_PREV_RETRANSLATE = MainWindow.retranslate_ui
    def _bk_lm_behavior_retranslate(self, *args, **kwargs):
        _BK_LM_BEHAVIOR_PREV_RETRANSLATE(self, *args, **kwargs)
        if hasattr(self, "act_lm_behavior_settings"):
            self.act_lm_behavior_settings.setText(_bk_lm_opt_text(self, "act_lm_behavior_settings"))
        if hasattr(self, "act_lm_token_settings"):
            self.act_lm_token_settings.setText(_bk_lm_opt_text(self, "act_lm_token_settings"))
        if hasattr(self, "act_lm_prompt_settings"):
            self.act_lm_prompt_settings.setText(_bk_lm_opt_text(self, "act_lm_prompt_settings"))
        if hasattr(self, "act_lm_custom_context"):
            self.act_lm_custom_context.setText(_bk_lm_opt_text(self, "act_lm_custom_context"))
        _bk_lm_rehome_options_actions(self)
    MainWindow.retranslate_ui = _bk_lm_behavior_retranslate
except Exception:
    pass
def _bk_lm_behavior_with_scope(self, scope, fn, *args, **kwargs):
    old = getattr(self, "_bk_lm_behavior_scope_hint", None)
    self._bk_lm_behavior_scope_hint = scope
    try:
        return fn(self, *args, **kwargs)
    finally:
        if old is None:
            try:
                delattr(self, "_bk_lm_behavior_scope_hint")
            except Exception:
                pass
        else:
            self._bk_lm_behavior_scope_hint = old
def _bk_lm_patch_scope_method(name: str, scope: str):
    old = getattr(MainWindow, name, None)
    if not callable(old) or getattr(old, "_bk_lm_behavior_wrapped", False):
        return
    def wrapped(self, *args, **kwargs):
        return _bk_lm_behavior_with_scope(self, scope, old, *args, **kwargs)
    wrapped._bk_lm_behavior_wrapped = True
    setattr(MainWindow, name, wrapped)
_bk_lm_patch_scope_method("run_ai_revision_for_single_line", "current_line")
_bk_lm_patch_scope_method("run_ai_revision_for_selected_lines", "selected_lines")
_bk_lm_patch_scope_method("run_ai_revision", "all_lines")
_bk_lm_patch_scope_method("run_ai_revision_for_selected", "all_lines")
_bk_lm_patch_scope_method("run_ai_revision_for_all", "all_lines")
_bk_lm_patch_scope_method("_run_ai_revision_batch", "all_lines")
try:
    def _bk_lm_choose_ai_script_mode_from_settings(self):
        scope = getattr(self, "_bk_lm_behavior_scope_hint", "all_lines")
        return _lm_behavior_for_scope(self, scope).get("script_mode", AI_SCRIPT_PRINT)
    MainWindow._choose_ai_script_mode = _bk_lm_choose_ai_script_mode_from_settings
except Exception:
    pass
MainWindow._lm_behavior_for_scope = _lm_behavior_for_scope
MainWindow._bk_lm_show_behavior_dialog = _bk_lm_show_behavior_dialog
__all__ = [
    '_BK_LM_BEHAVIOR_ACTIVE',
    '_BK_LM_BEHAVIOR_DEFAULTS',
    '_BK_LM_BEHAVIOR_FILTER_ALIASES',
    '_BK_LM_BEHAVIOR_LEGACY_WEIGHTING_ALIASES',
    '_BK_LM_BEHAVIOR_OLD_DEFAULT_FILTERS',
    '_BK_LM_BEHAVIOR_PRESETS',
    '_BK_LM_BEHAVIOR_SCOPES',
    '_bk_lm_behavior_apply_preset',
    '_bk_lm_behavior_bool',
    '_bk_lm_behavior_defaults_for_scope',
    '_bk_lm_behavior_filter_text',
    '_bk_lm_behavior_key',
    '_bk_lm_behavior_normalized',
    '_bk_lm_behavior_prompt',
    '_bk_lm_behavior_weight',
    '_bk_lm_behavior_with_scope',
    '_bk_lm_load_behavior_settings',
    '_bk_lm_patch_scope_method',
    '_bk_lm_rehome_options_actions',
    '_bk_lm_save_behavior_settings',
    '_bk_lm_show_behavior_dialog',
    '_lm_behavior_for_scope',
]
register_globals('bk', globals(), __all__)
