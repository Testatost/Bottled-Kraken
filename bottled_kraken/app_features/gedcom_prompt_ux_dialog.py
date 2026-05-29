from bottled_kraken.module_registry import register_globals, seed_globals
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
    ("ai_prompt_page_boxes_align_system", "lm_prompt_page_boxes_align_system"),
    ("ai_prompt_page_boxes_align_user", "lm_prompt_page_boxes_align_user"),
    ("group", "prompt_group_structured_json"),
    ("ai_prompt_canonical_system", "lm_prompt_canonical_system"),
    ("ai_prompt_canonical_user", "lm_prompt_canonical_user"),
    ("ai_prompt_postgresql_system", "lm_prompt_postgresql_system"),
    ("ai_prompt_postgresql_user", "lm_prompt_postgresql_user"),
    ("ai_prompt_neo4j_system", "lm_prompt_neo4j_system"),
    ("ai_prompt_neo4j_user", "lm_prompt_neo4j_user"),
    ("ai_prompt_sqlite_system", "lm_prompt_sqlite_system"),
    ("ai_prompt_sqlite_user", "lm_prompt_sqlite_user"),
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
    "ai_prompt_decision_user": "prompt_desc_decision_system",
    "ai_prompt_fullpage_lm_ocr_system": "prompt_desc_fullpage_ocr_system",
    "ai_prompt_fullpage_lm_ocr_user": "prompt_desc_fullpage_ocr_user",
    "ai_prompt_page_boxes_align_system": "prompt_desc_page_boxes_align_system",
    "ai_prompt_page_boxes_align_user": "prompt_desc_page_boxes_align_user",
    "ai_prompt_canonical_system": "prompt_desc_canonical_system",
    "ai_prompt_canonical_user": "prompt_desc_canonical_user",
    "ai_prompt_postgresql_system": "prompt_desc_postgresql_system",
    "ai_prompt_postgresql_user": "prompt_desc_postgresql_user",
    "ai_prompt_neo4j_system": "prompt_desc_neo4j_system",
    "ai_prompt_neo4j_user": "prompt_desc_neo4j_user",
    "ai_prompt_sqlite_system": "prompt_desc_sqlite_system",
    "ai_prompt_sqlite_user": "prompt_desc_sqlite_user",
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
        existing.update({
            "ai_prompt_canonical_system": "lm_prompt_canonical_system",
            "ai_prompt_canonical_user": "lm_prompt_canonical_user",
            "ai_prompt_postgresql_system": "lm_prompt_postgresql_system",
            "ai_prompt_postgresql_user": "lm_prompt_postgresql_user",
            "ai_prompt_neo4j_system": "lm_prompt_neo4j_system",
            "ai_prompt_neo4j_user": "lm_prompt_neo4j_user",
            "ai_prompt_sqlite_system": "lm_prompt_sqlite_system",
            "ai_prompt_sqlite_user": "lm_prompt_sqlite_user",
            "ai_prompt_page_boxes_align_system": "lm_prompt_page_boxes_align_system",
            "ai_prompt_page_boxes_align_user": "lm_prompt_page_boxes_align_user",
        })
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
        lang = getattr(window, "current_lang", translation.DEFAULT_LANGUAGE)
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
    lang = getattr(self, "current_lang", translation.DEFAULT_LANGUAGE)
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
_BK_GEDCOM_REG_PREV_BUILD_FROM_STRUCTURED = globals().get("_bk_gedcom_build_from_structured")
__all__ = [
    '_BK_GEDCOM_PROMPT_DEFAULTS',
    '_BK_GEDCOM_REG_PREV_BUILD_FROM_STRUCTURED',
    '_BK_GEDCOM_REVIEW_TEXTS',
    '_BK_GEDCOM_ROBUST_TEXTS',
    '_BK_GEDCOM_SAVE_FIX_TEXTS',
    '_BK_GEDCOM_STRUCTURED_TEXTS',
    '_BK_GEDCOM_VISION_TEXTS',
    '_BK_PROMPT_UX_ADVANCED_KEYS',
    '_BK_PROMPT_UX_DESC_KEYS',
    '_BK_PROMPT_UX_EXTRA_TEXTS',
    '_BK_PROMPT_UX_ORDER',
    '_bk_lm_show_prompt_settings_dialog',
    '_bk_prompt_ux_install_texts',
    '_bk_prompt_ux_make_group_item',
    '_bk_prompt_ux_ordered_items',
    '_bk_prompt_ux_text',
]
register_globals('bk', globals(), __all__)
