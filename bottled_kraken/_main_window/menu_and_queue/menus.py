from bottled_kraken.common import _serialize_ocr_auto_revision_replacements
from bottled_kraken.common import (
    Dict,
    List,
    QAction,
    QActionGroup,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QKeySequence,
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    READING_MODES,
)
import math
import csv
import json
import os
import re
import zipfile
from bottled_kraken._main_window.menu_and_queue.menu_behavior import BKStayOpenMenu
class MainWindowMenuConstructionMixin:
        def set_kraken_auto_revision_enabled(self, checked: bool):
            self.kraken_auto_revision_enabled = bool(checked)
            try:
                self.settings.setValue("ocr/auto_revision_enabled", "true" if self.kraken_auto_revision_enabled else "false")
            except Exception:
                pass
        def _kraken_auto_revision_default_text(self) -> str:
            try:
                return _serialize_ocr_auto_revision_replacements()
            except Exception:
                return "ſ=s\n⸗=-\n±=+/-"
        def _kraken_autocorrect_flatten_json_terms(self, value) -> list:
            terms = []
            def collect(obj):
                if obj is None:
                    return
                if isinstance(obj, str):
                    txt = obj.strip()
                    if txt:
                        terms.append(txt)
                    return
                if isinstance(obj, (list, tuple, set)):
                    for item in obj:
                        collect(item)
                    return
                if isinstance(obj, dict):
                    for key, item in obj.items():
                        collect(item)
                        if item is True:
                            collect(key)
            collect(value)
            return terms

        def _kraken_autocorrect_extract_text_file(self, path: str) -> str:
            """Liest Referenzwörter aus txt/csv/json/docx/xlsx/odt/ods ohne schwere Zusatzabhängigkeiten."""
            ext = os.path.splitext(str(path or ""))[1].lower()
            try:
                if ext in {".txt", ".csv"}:
                    for enc in ("utf-8-sig", "utf-8", "latin-1"):
                        try:
                            with open(path, "r", encoding=enc, errors="replace") as handle:
                                return handle.read()
                        except UnicodeError:
                            continue
                    return ""
                if ext == ".json":
                    raw = ""
                    for enc in ("utf-8-sig", "utf-8", "latin-1"):
                        try:
                            with open(path, "r", encoding=enc, errors="replace") as handle:
                                raw = handle.read()
                            break
                        except UnicodeError:
                            continue
                    if not raw:
                        return ""
                    try:
                        data = json.loads(raw)
                        return "\n".join(self._kraken_autocorrect_flatten_json_terms(data))
                    except Exception:
                        return raw
                if ext == ".docx":
                    with zipfile.ZipFile(path) as archive:
                        data = archive.read("word/document.xml").decode("utf-8", errors="replace")
                    data = re.sub(r"<w:tab[^>]*/>", " ", data)
                    data = re.sub(r"</w:p>", "\n", data)
                    return re.sub(r"<[^>]+>", " ", data)
                if ext in {".odt", ".ods"}:
                    with zipfile.ZipFile(path) as archive:
                        data = archive.read("content.xml").decode("utf-8", errors="replace")
                    data = re.sub(r"</text:p>|</table:table-row>", "\n", data)
                    return re.sub(r"<[^>]+>", " ", data)
                if ext == ".xlsx":
                    parts = []
                    with zipfile.ZipFile(path) as archive:
                        names = set(archive.namelist())
                        if "xl/sharedStrings.xml" in names:
                            data = archive.read("xl/sharedStrings.xml").decode("utf-8", errors="replace")
                            parts.append(re.sub(r"<[^>]+>", " ", data))
                        for name in sorted(n for n in names if n.startswith("xl/worksheets/") and n.endswith(".xml"))[:20]:
                            data = archive.read(name).decode("utf-8", errors="replace")
                            # inlineStr und Rohwerte als zusätzliche Referenz; Shared-Strings liefern meist die Namen.
                            parts.append(re.sub(r"<[^>]+>", " ", data))
                    return "\n".join(parts)
            except Exception:
                return ""
            return ""

        def _kraken_autocorrect_reference_paths(self) -> list:
            exts = {".txt", ".csv", ".json", ".docx", ".xlsx", ".odt", ".ods"}
            single_file = str(getattr(self, "kraken_autocorrect_reference_file", "") or "").strip()
            # Datei und Ordner sind absichtlich Alternativen. Dadurch bleibt kein alter,
            # versteckter Referenzordner aktiv, der eine saubere Einzeldatei mit
            # fehlerhaften OCR-Exporten aus Downloads vermischen könnte.
            if single_file and os.path.isfile(single_file) and os.path.splitext(single_file)[1].lower() in exts:
                return [single_file]
            paths = []
            seen_paths = set()
            directory = str(getattr(self, "kraken_autocorrect_reference_dir", "") or "").strip()
            if directory and os.path.isdir(directory):
                for root, _dirs, files in os.walk(directory):
                    for filename in sorted(files):
                        if os.path.splitext(filename)[1].lower() not in exts:
                            continue
                        path = os.path.join(root, filename)
                        real = os.path.abspath(path)
                        if real in seen_paths:
                            continue
                        seen_paths.add(real)
                        paths.append(path)
            return paths

        def _kraken_autocorrect_reference_norm(self, value) -> str:
            txt = str(value or "").casefold()
            txt = txt.replace("0", "o").replace("1", "l").replace("ſ", "s")
            return re.sub(r"[^a-zäöüßà-ÿ]", "", txt)

        def _kraken_autocorrect_reference_weight(self, value, default: float = 1.0) -> float:
            try:
                if isinstance(value, (int, float)):
                    val = float(value)
                else:
                    txt = str(value or "").strip().replace("\u00a0", "").replace(" ", "")
                    txt = txt.replace(".", "") if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", txt) else txt
                    txt = txt.replace(",", ".")
                    if not re.fullmatch(r"\d+(?:\.\d+)?", txt):
                        return float(default)
                    val = float(txt)
                if val <= 0:
                    return float(default)
                return min(val, 1000000.0)
            except Exception:
                return float(default)

        def _kraken_autocorrect_reference_split_cell(self, value) -> list:
            text = str(value or "")
            text = re.sub(r"(?<=[a-zäöüßà-ÿ])(?=[A-ZÄÖÜÀ-Ý])", " ", text)
            parts = re.split(r"[\s,;_]+", text)
            out = []
            for part in parts:
                term = str(part or "").strip(" \t\r\n\"'’`´.,;:()[]{}<>")
                if not term:
                    continue
                # Bindestriche bleiben erhalten, weil sie bei Doppel-Namen relevant sind.
                if not re.search(r"[A-Za-zÄÖÜäöüßÀ-ÿ]", term):
                    continue
                if re.fullmatch(r"[mMwWdD]", term):
                    continue
                norm = self._kraken_autocorrect_reference_norm(term)
                if len(norm) < 2:
                    continue
                out.append(term)
            return out

        def _kraken_autocorrect_add_reference_entry(self, by_norm: dict, term, weight: float = 1.0):
            for part in self._kraken_autocorrect_reference_split_cell(term):
                norm = self._kraken_autocorrect_reference_norm(part)
                if not norm or len(norm) < 2:
                    continue
                if norm in {
                    "anzahl", "zahl", "count", "frequency", "frequenz", "haeufigkeit", "häufigkeit",
                    "vorname", "vornamen", "name", "namen", "nachname", "familienname", "familiennamen",
                    "geschlecht", "gender", "position", "rang", "rank", "ort", "orte", "stadt",
                    "strasse", "straße", "sonderzeichen", "begriff", "begriffe", "term", "terms", "wert",
                }:
                    continue
                entry = by_norm.get(norm)
                w = self._kraken_autocorrect_reference_weight(weight, 1.0)
                if entry is None:
                    by_norm[norm] = {"term": part, "weight": w, "best_weight": w}
                else:
                    entry["weight"] = float(entry.get("weight", 1.0)) + w
                    if w > float(entry.get("best_weight", 0.0)):
                        entry["term"] = part
                        entry["best_weight"] = w

        def _kraken_autocorrect_parse_delimited_reference_text(self, text: str, by_norm: dict) -> bool:
            lines = [line for line in str(text or "").splitlines() if line.strip()]
            if not lines:
                return False
            delimiters = [";", "\t", ",", "|"]
            delimiter_scores = {d: sum(line.count(d) for line in lines[:25]) for d in delimiters}
            delimiter = max(delimiter_scores, key=delimiter_scores.get)
            if delimiter_scores.get(delimiter, 0) <= 0:
                return False
            try:
                rows = list(csv.reader(lines, delimiter=delimiter))
            except Exception:
                return False
            rows = [[str(cell or "").strip() for cell in row] for row in rows if any(str(cell or "").strip() for cell in row)]
            if not rows:
                return False
            header_norms = [self._kraken_autocorrect_reference_norm(cell) for cell in rows[0]]
            term_header_norms = {
                "vorname", "vornamen", "name", "namen", "nachname", "familienname", "familiennamen",
                "ort", "orte", "stadt", "gemeinde", "strasse", "straße", "sonderzeichen",
                "begriff", "begriffe", "term", "terms", "wert", "text",
            }
            ignored_header_norms = {
                "anzahl", "zahl", "count", "frequency", "frequenz", "haeufigkeit", "häufigkeit",
                "gewicht", "weight", "geschlecht", "gender", "position", "rang", "rank", "id", "nr", "nummer",
            }
            weight_header_norms = {
                "anzahl", "zahl", "count", "frequency", "frequenz", "haeufigkeit", "häufigkeit", "gewicht", "weight",
            }
            has_header = bool(set(header_norms).intersection(term_header_norms | ignored_header_norms))
            term_cols = [idx for idx, norm in enumerate(header_norms) if norm in term_header_norms] if has_header else []
            weight_cols = [idx for idx, norm in enumerate(header_norms) if norm in weight_header_norms] if has_header else []
            data_rows = rows[1:] if has_header else rows
            parsed_any = False
            for row in data_rows:
                if not row:
                    continue
                row_weight = 1.0
                for idx in weight_cols:
                    if idx < len(row):
                        row_weight = max(row_weight, self._kraken_autocorrect_reference_weight(row[idx], 1.0))
                if not weight_cols:
                    for cell in row:
                        row_weight = max(row_weight, self._kraken_autocorrect_reference_weight(cell, 1.0))
                active_cols = term_cols
                if not active_cols:
                    active_cols = []
                    for idx, cell in enumerate(row):
                        norm = self._kraken_autocorrect_reference_norm(cell)
                        if not norm or norm in ignored_header_norms or re.fullmatch(r"[mMwWdD]", str(cell or "").strip()):
                            continue
                        if self._kraken_autocorrect_reference_weight(cell, 0.0) > 0:
                            continue
                        active_cols.append(idx)
                for idx in active_cols:
                    if idx >= len(row):
                        continue
                    before = len(by_norm)
                    self._kraken_autocorrect_add_reference_entry(by_norm, row[idx], row_weight)
                    if len(by_norm) != before:
                        parsed_any = True
            return parsed_any

        def _kraken_autocorrect_parse_plain_reference_text(self, text: str, by_norm: dict):
            cleaned = str(text or "")
            cleaned = re.sub(r"(?<=[a-zäöüßà-ÿ])(?=[A-ZÄÖÜÀ-Ý])", " ", cleaned)
            cleaned = cleaned.replace("_", " ")
            # Komma, Semikolon und Leerzeichen trennen Einträge; Bindestriche bleiben Teil des Begriffs.
            for match in re.finditer(r"[A-Za-zÄÖÜäöüßÀ-ÿ][A-Za-zÄÖÜäöüßÀ-ÿ'’\-]{1,}", cleaned):
                self._kraken_autocorrect_add_reference_entry(by_norm, match.group(0), 1.0)

        def _kraken_autocorrect_reference_terms(self) -> list:
            if not bool(getattr(self, "kraken_autocorrect_enabled", False)):
                return []
            by_norm = {}
            for path in self._kraken_autocorrect_reference_paths():
                text = self._kraken_autocorrect_extract_text_file(path)
                if not text:
                    continue
                ext = os.path.splitext(str(path or ""))[1].lower()
                parsed_structured = False
                if ext in {".csv", ".txt"}:
                    parsed_structured = self._kraken_autocorrect_parse_delimited_reference_text(text, by_norm)
                if not parsed_structured:
                    self._kraken_autocorrect_parse_plain_reference_text(text, by_norm)
                if len(by_norm) >= 20000:
                    break
            terms = []
            for norm, entry in by_norm.items():
                term = str(entry.get("term", "")).strip()
                if not term:
                    continue
                terms.append({"term": term, "weight": float(entry.get("weight", 1.0))})
                if len(terms) >= 20000:
                    break
            return terms

        def _kraken_auto_revision_runtime_replacements(self) -> str:
            """Erzeugt die Laufzeit-Konfiguration für OCR-Worker inkl. Referenz-Autokorrektur."""
            text = str(getattr(self, "kraken_auto_revision_replacements", "") or self._kraken_auto_revision_default_text())
            terms = self._kraken_autocorrect_reference_terms()
            if terms:
                try:
                    text += "\n#BK_AUTOCORRECT_TERMS_JSON=" + json.dumps(terms, ensure_ascii=False)
                except Exception:
                    pass
            return text

        def _open_kraken_auto_revision_settings(self):
            dialog = QDialog(self)
            dialog.setWindowTitle(self._tr("kraken_revision_settings_title"))
            dialog.setMinimumSize(560, 420)
            try:
                dialog.resize(620, 480)
            except Exception:
                pass
            layout = QVBoxLayout(dialog)
            info = QLabel(self._tr("kraken_revision_settings_intro"))
            info.setWordWrap(True)
            layout.addWidget(info)
            editor = QPlainTextEdit(dialog)
            editor.setPlaceholderText(self._tr("kraken_revision_replacements_placeholder"))
            editor.setMinimumHeight(170)
            editor.setPlainText(str(getattr(self, "kraken_auto_revision_replacements", "") or self._kraken_auto_revision_default_text()))
            layout.addWidget(editor, 1)
            hint = QLabel(self._tr("kraken_revision_replacements_hint"))
            hint.setWordWrap(True)
            layout.addWidget(hint)
            check = QCheckBox(self._tr("kraken_revision_enable_checkbox"), dialog)
            check.setChecked(bool(getattr(self, "kraken_auto_revision_enabled", False)))
            layout.addWidget(check)

            autocorrect_check = QCheckBox(self._tr("kraken_autocorrect_enable_checkbox"), dialog)
            autocorrect_check.setChecked(bool(getattr(self, "kraken_autocorrect_enabled", False)))
            layout.addWidget(autocorrect_check)

            ref_state = {
                "dir": str(getattr(self, "kraken_autocorrect_reference_dir", "") or ""),
                "file": str(getattr(self, "kraken_autocorrect_reference_file", "") or ""),
            }
            ref_row = QHBoxLayout()
            ref_label = QLabel(self._tr("kraken_autocorrect_reference_label"), dialog)
            ref_file_btn = QPushButton(self._tr("kraken_autocorrect_reference_file_choose"), dialog)
            ref_btn = QPushButton(self._tr("kraken_autocorrect_reference_dir_choose"), dialog)
            ref_status = QLabel("", dialog)
            ref_status.setWordWrap(True)
            def update_reference_status():
                has_file = bool(ref_state.get("file") and os.path.isfile(ref_state.get("file")))
                has_dir = bool(ref_state.get("dir") and os.path.isdir(ref_state.get("dir")))
                if has_file:
                    text = self._tr("kraken_autocorrect_reference_selected_file")
                elif has_dir:
                    text = self._tr("kraken_autocorrect_reference_selected_dir")
                else:
                    text = self._tr("kraken_autocorrect_reference_selected_none")
                ref_status.setText(text)
            def choose_reference_file():
                start_dir = os.path.expanduser("~")
                current_file = str(ref_state.get("file") or "").strip()
                current_dir = str(ref_state.get("dir") or "").strip()
                if current_file and os.path.isfile(current_file):
                    start_dir = os.path.dirname(current_file)
                elif current_dir and os.path.isdir(current_dir):
                    start_dir = current_dir
                chosen, _selected_filter = QFileDialog.getOpenFileName(
                    dialog,
                    self._tr("kraken_autocorrect_reference_file_title"),
                    start_dir,
                    self._tr("kraken_autocorrect_reference_file_filter"),
                )
                if chosen:
                    ref_state["file"] = chosen
                    ref_state["dir"] = ""
                    update_reference_status()
            def choose_reference_dir():
                start_dir = str(ref_state.get("dir") or "").strip()
                if not start_dir or not os.path.isdir(start_dir):
                    current_file = str(ref_state.get("file") or "").strip()
                    start_dir = os.path.dirname(current_file) if current_file and os.path.isfile(current_file) else os.path.expanduser("~")
                chosen = QFileDialog.getExistingDirectory(dialog, self._tr("kraken_autocorrect_reference_dir_title"), start_dir)
                if chosen:
                    ref_state["dir"] = chosen
                    ref_state["file"] = ""
                    update_reference_status()
            ref_file_btn.clicked.connect(choose_reference_file)
            ref_btn.clicked.connect(choose_reference_dir)
            ref_row.addWidget(ref_label)
            ref_row.addWidget(ref_file_btn)
            ref_row.addWidget(ref_btn)
            ref_row.addStretch(1)
            layout.addLayout(ref_row)
            update_reference_status()
            layout.addWidget(ref_status)

            ref_hint = QLabel(self._tr("kraken_autocorrect_reference_dir_hint"), dialog)
            ref_hint.setWordWrap(True)
            layout.addWidget(ref_hint)

            buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, dialog)
            if buttons.button(QDialogButtonBox.Save):
                buttons.button(QDialogButtonBox.Save).setText(self._tr("btn_save"))
            if buttons.button(QDialogButtonBox.Cancel):
                buttons.button(QDialogButtonBox.Cancel).setText(self._tr("btn_cancel"))
            reset_btn = buttons.addButton(self._tr("kraken_revision_reset_defaults"), QDialogButtonBox.ResetRole)
            reset_btn.clicked.connect(lambda: editor.setPlainText(self._kraken_auto_revision_default_text()))
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            if dialog.exec() == QDialog.Accepted:
                text = editor.toPlainText().strip() or self._kraken_auto_revision_default_text()
                self.kraken_auto_revision_replacements = text
                self.kraken_auto_revision_enabled = bool(check.isChecked())
                self.kraken_autocorrect_enabled = bool(autocorrect_check.isChecked())
                selected_file = str(ref_state.get("file") or "").strip()
                selected_dir = str(ref_state.get("dir") or "").strip()
                if selected_file and os.path.isfile(selected_file):
                    selected_dir = ""
                self.kraken_autocorrect_reference_dir = selected_dir
                self.kraken_autocorrect_reference_file = selected_file
                try:
                    self.settings.setValue("ocr/auto_revision_replacements", text)
                    self.settings.setValue("ocr/auto_revision_enabled", "true" if self.kraken_auto_revision_enabled else "false")
                    self.settings.setValue("ocr/autocorrect_enabled", "true" if self.kraken_autocorrect_enabled else "false")
                    self.settings.setValue("ocr/autocorrect_reference_dir", self.kraken_autocorrect_reference_dir)
                    self.settings.setValue("ocr/autocorrect_reference_file", self.kraken_autocorrect_reference_file)
                except Exception:
                    pass
        def _place_kraken_auto_revision_action_at_bottom(self):
            target_menu = getattr(self, "options_menu", None)
            if target_menu is None:
                return
            if not hasattr(self, "act_kraken_auto_revision_settings"):
                self.act_kraken_auto_revision_settings = QAction(self._tr("act_kraken_auto_revision_settings"), self)
                self.act_kraken_auto_revision_settings.triggered.connect(self._open_kraken_auto_revision_settings)
            sep = getattr(self, "_kraken_auto_revision_separator", None)
            for menu_name in ("models_menu", "options_menu"):
                menu_obj = getattr(self, menu_name, None)
                if menu_obj is None:
                    continue
                for action in (sep, self.act_kraken_auto_revision_settings):
                    if action is not None:
                        try:
                            menu_obj.removeAction(action)
                        except Exception:
                            pass
            self._kraken_auto_revision_separator = target_menu.addSeparator()
            target_menu.addAction(self.act_kraken_auto_revision_settings)
        def _shortcut_ctrl_label(self, suffix: str) -> str:
            lang = str(getattr(self, "current_lang", "") or "").lower()
            prefix = "Strg" if lang.startswith("de") else "Ctrl"
            return f"{prefix}+{str(suffix).lstrip('+')}"
        def _menu_text_with_shortcut(self, text: str, suffix: str) -> str:
            return f"{str(text)}\t{self._shortcut_ctrl_label(suffix)}"
        def _init_menu(self):
            menubar = self.menuBar()
            self.file_menu = BKStayOpenMenu(self._tr("menu_file"), self)
            self.edit_menu = BKStayOpenMenu(self._tr("menu_edit"), self)
            self.options_menu = BKStayOpenMenu(self._tr("menu_options"), self)
            menubar.addMenu(self.file_menu)
            menubar.addMenu(self.edit_menu)
            menubar.addMenu(self.options_menu)
            if hasattr(self, "_apply_localized_menu_shortcut_texts"):
                self._apply_localized_menu_shortcut_texts()
            self.edit_menu.addAction(self.act_undo)
            self.edit_menu.addAction(self.act_redo)
            self.edit_menu.addSeparator()
            self.act_export_log = QAction(self._tr("menu_export_log"), self)
            self.act_export_log.triggered.connect(self.export_log_txt)
            self.edit_menu.addAction(self.act_export_log)
            self.act_add_files = QAction(self._tr("act_add_files"), self)
            self.act_add_files.triggered.connect(self.choose_files)
            self.file_menu.addAction(self.act_add_files)
            self.act_paste_files_menu = QAction(self._menu_text_with_shortcut(self._tr("act_paste_clipboard"), "V"), self)
            self.act_paste_files_menu.triggered.connect(self.paste_files_from_clipboard)
            self.file_menu.addAction(self.act_paste_files_menu)
            self.act_paste_files_menu_sc = QAction(self)
            self.act_paste_files_menu_sc.setShortcut(QKeySequence.Paste)
            self.act_paste_files_menu_sc.triggered.connect(self.paste_files_from_clipboard)
            self.addAction(self.act_paste_files_menu_sc)
            self.file_menu.addSeparator()
            self.act_project_save = QAction(self._menu_text_with_shortcut(self._tr("menu_project_save"), "S"), self)
            self.act_project_save.triggered.connect(self.save_project)
            self.file_menu.addAction(self.act_project_save)
            self.act_project_save_as = QAction(self._menu_text_with_shortcut(self._tr("menu_project_save_as"), "Shift+S"), self)
            self.act_project_save_as.triggered.connect(self.save_project_as)
            self.file_menu.addAction(self.act_project_save_as)
            self.act_project_load = QAction(self._menu_text_with_shortcut(self._tr("menu_project_load"), "I"), self)
            self.act_project_load.triggered.connect(self.load_project)
            self.file_menu.addAction(self.act_project_load)
            self.file_menu.addSeparator()
            self.export_menu = BKStayOpenMenu(self._menu_text_with_shortcut(self._tr("menu_export"), "E"), self.file_menu)
            self.file_menu.addMenu(self.export_menu)
            self.formats = self._export_format_items()
            self.export_format_actions = {}
            for name, fmt in self.formats:
                act = QAction(name, self)
                act.triggered.connect(lambda checked, f=fmt: self.export_flow(f))
                self.export_format_actions[fmt] = act
                self.export_menu.addAction(act)
            self.file_menu.addSeparator()
            self.act_exit = QAction(self._menu_text_with_shortcut(self._tr("menu_exit"), "Q"), self)
            self.act_exit.triggered.connect(self.close)
            self.file_menu.addAction(self.act_exit)
            self.models_menu = BKStayOpenMenu(self._tr("menu_models"), self); menubar.addMenu(self.models_menu)
            self.act_rec = QAction(self._tr("act_load_rec_model"), self)
            self.act_rec.triggered.connect(self.choose_rec_model)
            self.models_menu.addAction(self.act_rec)
            self.act_seg = QAction(self._tr("act_load_seg_model"), self)
            self.act_seg.triggered.connect(self.choose_seg_model)
            self.models_menu.addAction(self.act_seg)
            self.models_menu.addSeparator()
            self.kraken_models_submenu = BKStayOpenMenu(self._tr("submenu_available_kraken_models"), self.models_menu); self.models_menu.addMenu(self.kraken_models_submenu)
            self.act_clear_rec = QAction(self._tr("act_clear_rec"), self)
            self.act_clear_rec.triggered.connect(self.clear_rec_model)
            self.act_clear_seg = QAction(self._tr("act_clear_seg"), self)
            self.act_clear_seg.triggered.connect(self.clear_seg_model)
            self.act_rec_status = QAction(self._tr("status_rec_model", "-"), self)
            self.act_rec_status.setEnabled(False)
            self.act_seg_status = QAction(self._tr("status_seg_model", "-"), self)
            self.act_seg_status.setEnabled(False)
            self._rebuild_kraken_models_submenu()
            self._update_kraken_menu_status()
            self.models_menu.addSeparator()
            self.models_menu.addAction(self.act_rec_status)
            self.models_menu.addAction(self.act_seg_status)
            self.models_menu.addSeparator()
            self.act_download = QAction(self._tr("act_download_model"), self)
            self.act_download.triggered.connect(self.open_download_link)
            self.models_menu.addAction(self.act_download)
            self._place_kraken_auto_revision_action_at_bottom()
            self.revision_models_menu = BKStayOpenMenu(self._tr("menu_lm_options"), self); menubar.addMenu(self.revision_models_menu)
            self.whisper_menu = BKStayOpenMenu(self._tr("menu_whisper_options"), self); menubar.addMenu(self.whisper_menu)
            self.act_whisper_set_path = QAction(self._tr("act_whisper_set_path"), self)
            self.act_whisper_set_path.triggered.connect(self.set_whisper_base_dir_dialog)
            self.whisper_menu.addAction(self.act_whisper_set_path)
            self.act_whisper_set_mic = QAction(self._tr("act_whisper_set_mic"), self)
            self.act_whisper_set_mic.triggered.connect(self.choose_whisper_microphone_dialog)
            self.whisper_menu.addAction(self.act_whisper_set_mic)
            self.whisper_menu.addSeparator()
            self.act_whisper_scan = QAction(self._tr("act_scan_local"), self)
            self.act_whisper_scan.triggered.connect(self.scan_whisper_models_now)
            self.whisper_menu.addAction(self.act_whisper_scan)
            self.whisper_models_submenu = BKStayOpenMenu(self._tr("submenu_available_whisper_models"), self.whisper_menu); self.whisper_menu.addMenu(self.whisper_models_submenu)
            self.whisper_model_group = QActionGroup(self)
            self.whisper_model_group.setExclusive(True)
            self.whisper_menu.addSeparator()
            self.act_whisper_status_model = QAction(self._tr("whisper_status_model", "-"), self)
            self.act_whisper_status_model.setEnabled(False)
            self.whisper_menu.addAction(self.act_whisper_status_model)
            self.act_whisper_status_mic = QAction(self._tr("whisper_status_mic", "-"), self)
            self.act_whisper_status_mic.setEnabled(False)
            self.whisper_menu.addAction(self.act_whisper_status_mic)
            self.act_whisper_status_path = QAction(self._tr("whisper_status_path", "-"), self)
            self.act_whisper_status_path.setEnabled(False)
            self.whisper_menu.addAction(self.act_whisper_status_path)
            self._scan_whisper_models()
            self._rebuild_whisper_model_submenu()
            self._update_whisper_menu_status()
            self.act_escriptorium = menubar.addAction(self._tr("menu_escriptorium"))
            self.act_escriptorium.triggered.connect(self.show_escriptorium_dialog)
            self.act_lm_help = menubar.addAction(self._tr("act_help"))
            self.act_lm_help.triggered.connect(self.show_lm_help_dialog)
            self.act_set_manual_lm_url = QAction(self._tr("act_set_manual_lm_url"), self)
            self.act_set_manual_lm_url.triggered.connect(self.set_manual_ai_base_url_dialog)
            self.revision_models_menu.addAction(self.act_set_manual_lm_url)
            self.act_clear_manual_lm_url = QAction(self._tr("act_clear_manual_lm_url"), self)
            self.act_clear_manual_lm_url.triggered.connect(self.clear_manual_ai_base_url)
            self.revision_models_menu.addAction(self.act_clear_manual_lm_url)
            self.revision_models_menu.addSeparator()
            self.act_scan_lm = QAction(self._tr("act_scan_local"), self)
            self.act_scan_lm.triggered.connect(self.scan_ai_models_now)
            self.revision_models_menu.addAction(self.act_scan_lm)
            self.ai_models_submenu = BKStayOpenMenu(self._tr("submenu_available_ai_models"), self.revision_models_menu); self.revision_models_menu.addMenu(self.ai_models_submenu)
            self.ai_model_group = QActionGroup(self)
            self.ai_model_group.setExclusive(True)
            self._rebuild_ai_model_submenu()
            self.revision_models_menu.addSeparator()
            self.act_lm_status = QAction(self._tr("lm_status_model_value", "-"), self)
            self.act_lm_status.setEnabled(False)
            self.revision_models_menu.addAction(self.act_lm_status)
            self.act_lm_mode = QAction(self._tr("lm_mode_value", "-"), self)
            self.act_lm_mode.setEnabled(False)
            self.revision_models_menu.addAction(self.act_lm_mode)
            self.act_lm_base_url = QAction(self._tr("lm_server_value", "-"), self)
            self.act_lm_base_url.setEnabled(False)
            self.revision_models_menu.addAction(self.act_lm_base_url)
            self._build_toolbar_language_theme_menus()
            self.act_appearance = QAction(self._tr("menu_appearance"), self)
            self.act_appearance.triggered.connect(self.open_appearance_dialog)
            self.options_menu.addAction(self.act_appearance)
            self.options_menu.addSeparator()
            self.reading_menu = BKStayOpenMenu(self._tr("menu_reading"), self.options_menu); self.options_menu.addMenu(self.reading_menu)
            read_group = QActionGroup(self)
            self.read_actions: List[QAction] = []
            for key, mode in [
                ("reading_tb_lr", READING_MODES["TB_LR"]),
                ("reading_tb_rl", READING_MODES["TB_RL"]),
                ("reading_bt_lr", READING_MODES["BT_LR"]),
                ("reading_bt_rl", READING_MODES["BT_RL"]),
            ]:
                act = QAction(self._tr(key), self)
                act.setCheckable(True)
                if mode == self.reading_direction:
                    act.setChecked(True)
                act.triggered.connect(lambda checked, m=mode: self.set_reading_direction(m))
                read_group.addAction(act)
                self.reading_menu.addAction(act)
                self.read_actions.append(act)
            self.options_menu.addSeparator()
            self.overlay_menu = BKStayOpenMenu(self._tr("act_overlay_show"), self.options_menu); self.options_menu.addMenu(self.overlay_menu)
            self.overlay_display_group = QActionGroup(self)
            self.overlay_display_group.setExclusive(True)
            self.overlay_display_actions: Dict[str, QAction] = {}
            for key, mode in [
                ("overlay_mode_none", "none"),
                ("overlay_mode_current", "current"),
                ("overlay_mode_selected", "selected"),
                ("overlay_mode_all", "all"),
            ]:
                act = QAction(self._tr(key), self)
                act.setCheckable(True)
                if mode == getattr(self, "overlay_display_mode", "all"):
                    act.setChecked(True)
                act.triggered.connect(lambda checked=False, m=mode: self._set_overlay_display_mode(m))
                self.overlay_display_group.addAction(act)
                self.overlay_menu.addAction(act)
                self.overlay_display_actions[mode] = act
            self.act_overlay_resize_boxes = QAction(self._tr("overlay_resize_menu"), self)
            self.act_overlay_resize_boxes.triggered.connect(self.resize_overlay_boxes_dialog)
            self.act_overlay = self.overlay_menu.menuAction()
