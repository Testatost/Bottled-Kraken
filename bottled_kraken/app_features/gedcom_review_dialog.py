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
    lang = getattr(window, "current_lang", translation.DEFAULT_LANGUAGE)
    return translation.translate(lang, key, *args)
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
    try:
        setattr(worker, "_bk_gedcom_structured_data", _bk_gedcom_review_deepcopy(data))
        setattr(worker, "_bk_gedcom_used_structured", True)
    except Exception:
        pass
    if _BK_GEDCOM_REVIEW_PREV_BUILD_FROM_STRUCTURED is None:
        raise RuntimeError(_bk_gedcom_review_text(self.window, "err_structured_gedcom_builder_missing"))
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
            self.tree.collapseAll()
            self.update_btn.setEnabled(True)
            return
        general = self._make_group("gedcom_group_general")
        self._add_editable_item(general, "person_count", str(_bk_gedcom_review_person_count(self.text_edit.toPlainText())))
        general.child(general.childCount() - 1).setText(0, _bk_gedcom_review_text(self.window, "gedcom_overview_person_count"))
        self._add_editable_item(general, "family_count", str(_bk_gedcom_review_family_count(self.text_edit.toPlainText())))
        general.child(general.childCount() - 1).setText(0, _bk_gedcom_review_text(self.window, "gedcom_overview_family_count"))
        self._add_editable_item(general, "names", _bk_gedcom_review_names(self.text_edit.toPlainText()))
        general.child(general.childCount() - 1).setText(0, _bk_gedcom_review_text(self.window, "gedcom_overview_names"))
        self.tree.collapseAll()
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
def _bk_gedcom_review_init(self, *args, **kwargs):
    try:
        if hasattr(self, "act_ai_menu_gedcom") and hasattr(self, "_bk_lm_generate_gedcom"):
            try:
                self.act_ai_menu_gedcom.triggered.disconnect()
            except Exception:
                pass
            self.act_ai_menu_gedcom.triggered.connect(lambda _checked=False: self._bk_lm_generate_gedcom())
    except Exception:
        pass
def _bk_gedcom_review_retranslate(self, *args, **kwargs):
    try:
        if hasattr(self, "act_ai_menu_gedcom"):
            self.act_ai_menu_gedcom.setText(self._tr("act_lm_generate_gedcom"))
    except Exception:
        pass
_bk_gedcom_review_install_translations()
register_init_delta(_bk_gedcom_review_init)
register_retranslate_delta(_bk_gedcom_review_retranslate)
MainWindow._bk_lm_on_gedcom_done_gui = _bk_lm_on_gedcom_done_review
__all__ = [
    'BKGedcomReviewDialog',
    '_BK_GEDCOM_PROMPT_DEFAULTS',
    '_BK_GEDCOM_REVIEW_PREV_BUILD_FROM_STRUCTURED',
    '_BK_GEDCOM_REVIEW_TEXTS',
    '_BK_GEDCOM_ROBUST_TEXTS',
    '_BK_GEDCOM_SAVE_FIX_TEXTS',
    '_BK_GEDCOM_STRUCTURED_TEXTS',
    '_BK_GEDCOM_VISION_TEXTS',
    '_BK_PROMPT_UX_EXTRA_TEXTS',
    '_bk_gedcom_build_from_structured',
    '_bk_gedcom_review_deepcopy',
    '_bk_gedcom_review_family_count',
    '_bk_gedcom_review_finalize_text',
    '_bk_gedcom_review_init',
    '_bk_gedcom_review_install_translations',
    '_bk_gedcom_review_is_weak',
    '_bk_gedcom_review_names',
    '_bk_gedcom_review_person_count',
    '_bk_gedcom_review_retranslate',
    '_bk_gedcom_review_text',
    '_bk_lm_on_gedcom_done_review',
]
register_globals('bk', globals(), __all__)
