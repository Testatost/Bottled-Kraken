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
    ("group", "prompt_group_lmx_office_export"),
    ("ai_prompt_lmx_docx_system", "lm_prompt_lmx_docx_system"),
    ("ai_prompt_lmx_docx_user", "lm_prompt_lmx_docx_user"),
    ("ai_prompt_lmx_xlsx_system", "lm_prompt_lmx_xlsx_system"),
    ("ai_prompt_lmx_xlsx_user", "lm_prompt_lmx_xlsx_user"),
    ("ai_prompt_lmx_odt_system", "lm_prompt_lmx_odt_system"),
    ("ai_prompt_lmx_odt_user", "lm_prompt_lmx_odt_user"),
    ("ai_prompt_lmx_ods_system", "lm_prompt_lmx_ods_system"),
    ("ai_prompt_lmx_ods_user", "lm_prompt_lmx_ods_user"),
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
    "ai_prompt_lmx_docx_system": "prompt_desc_lmx_docx_system",
    "ai_prompt_lmx_docx_user": "prompt_desc_lmx_docx_user",
    "ai_prompt_lmx_xlsx_system": "prompt_desc_lmx_xlsx_system",
    "ai_prompt_lmx_xlsx_user": "prompt_desc_lmx_xlsx_user",
    "ai_prompt_lmx_odt_system": "prompt_desc_lmx_odt_system",
    "ai_prompt_lmx_odt_user": "prompt_desc_lmx_odt_user",
    "ai_prompt_lmx_ods_system": "prompt_desc_lmx_ods_system",
    "ai_prompt_lmx_ods_user": "prompt_desc_lmx_ods_user",
    "ai_prompt_gedcom_extract_system": "prompt_desc_gedcom_extract_system",
    "ai_prompt_gedcom_extract_user": "prompt_desc_gedcom_extract_user",
    "ai_prompt_gedcom_system": "prompt_desc_gedcom_system",
    "ai_prompt_gedcom_user": "prompt_desc_gedcom_user",
}
_BK_LMX_PROMPT_BASES = {
    "de": {
        "formats": {
            "docx": "Word-Dokument (.docx)",
            "xlsx": "Excel-Arbeitsmappe (.xlsx)",
            "odt": "LibreOffice-Writer-Dokument (.odt)",
            "ods": "LibreOffice-Calc-Tabelle (.ods)",
        },
        "group": "KI-Office-Export (DOCX/XLSX/ODT/ODS)",
        "labels": {
            "system": "{fmt} – System-Prompt",
            "user": "{fmt} – Benutzer-Prompt",
        },
        "descriptions": {
            "system": "Systemanweisung für den KI-Export nach {format_name}. Sie steuert, wie das Modell Überschriften, Absätze und echte Tabellen erkennt.",
            "user": "Benutzeranweisung für den KI-Export nach {format_name}. Der Platzhalter {{}} für die nummerierten OCR-Zeilen und doppelte JSON-Klammern müssen erhalten bleiben.",
        },
        "system": (
            "Du bist ein präziser Dokumentstruktur-Assistent für historische deutsche Dokumente.\n"
            "Du erhältst nummerierte, bereits transkribierte Zeilen in Lesereihenfolge.\n"
            "Deine Aufgabe ist AUSSCHLIESSLICH die Strukturierung für den Export nach {format_name}. "
            "Du darfst den Zeilentext NICHT verändern, NICHT kürzen, NICHT korrigieren und NICHTS hinzufügen.\n"
            "Erkenne, welche aufeinanderfolgenden Zeilen zusammen eine Tabelle bilden, und zerlege jede Tabellenzeile an den Spaltengrenzen in einzelne Zellen.\n"
            "Zeilen ohne Tabellencharakter werden zu paragraph-Blöcken; kurze Titel-/Kopfzeilen zu heading-Blöcken.\n"
            "Alle Tabellen eines Blocks müssen dieselbe Spaltenzahl haben; fehlende Zellen bleiben leere Strings.\n"
            "Antworte ausschließlich mit gültigem JSON. Kein Markdown. Kein zusätzlicher Text. Keine Kommentare."
        ),
        "user": (
            "Erzeuge die Dokumentstruktur für den Export nach {format_name}.\n"
            "Gib exakt EIN JSON-Objekt zurück und sonst nichts.\n"
            "Format:\n"
            "{{\"blocks\":[{{\"type\":\"heading\",\"text\":\"...\"}},{{\"type\":\"paragraph\",\"text\":\"...\"}},{{\"type\":\"table\",\"header\":[\"…\",\"…\"],\"rows\":[[\"Zelle\",\"Zelle\"]]}}]}}\n"
            "Regeln:\n"
            "- Jede Eingabezeile muss sich vollständig und wortgetreu in genau einem Block wiederfinden.\n"
            "- Zeilennummern mit Präfix 000: und Metadatenpräfixe [TEXT]/[TABLE cols=N] nicht übernehmen.\n"
            "- [TABLE cols=N] legt eine Tabelle mit EXAKT N Spalten verbindlich fest; verschiebe niemals Werte in eine andere Spalte.\n"
            "- Das Zeichen ' | ' trennt die N Tabellenzellen. Auch leere Positionen sind echte Zellen und müssen erhalten bleiben.\n"
            "- Der Marker [[EMPTY]] bedeutet eine leere Zelle und muss im JSON als leerer String ausgegeben werden.\n"
            "- Tabellen als echte rows/Zellen, niemals als Fließtext mit Leerzeichen.\n"
            "- Verwende für gleichartige Registerzeilen ein durchgehendes Spaltensystem; erfinde keine Spaltennamen.\n"
            "- Gleichartige Angaben gehören über alle Zeilen hinweg in dieselbe Spalte; fehlende Werte sind leere Strings.\n"
            "- Die Blöcke müssen der Reihenfolge der Eingabezeilen folgen.\n"
            "- Gib eine Tabelle nur aus, wenn ihre Zeilen mindestens zwei gefüllte Spalten haben.\n"
            "- Keine Ausgabe vor oder nach dem JSON.\n\n"
            "Zeilen:\n{}"
        ),
    },
    "en": {
        "formats": {
            "docx": "Word document (.docx)",
            "xlsx": "Excel workbook (.xlsx)",
            "odt": "LibreOffice Writer document (.odt)",
            "ods": "LibreOffice Calc spreadsheet (.ods)",
        },
        "group": "AI office export (DOCX/XLSX/ODT/ODS)",
        "labels": {"system": "{fmt} – system prompt", "user": "{fmt} – user prompt"},
        "descriptions": {
            "system": "System instruction for AI export to {format_name}. It controls how the model recognizes headings, paragraphs, and real tables.",
            "user": "User instruction for AI export to {format_name}. Keep the {{}} placeholder for numbered OCR lines and doubled JSON braces.",
        },
        "system": (
            "You are a precise document-structure assistant for historical documents.\n"
            "You receive numbered, already transcribed lines in reading order.\n"
            "Your task is EXCLUSIVELY structuring for export to {format_name}. Do not change, shorten, correct, or add to the line text.\n"
            "Detect consecutive table lines and split each table line into cells at column boundaries.\n"
            "Non-table lines become paragraph blocks; short titles become heading blocks.\n"
            "All rows in a table block must have the same number of columns; missing cells remain empty strings.\n"
            "Return valid JSON only. No Markdown, extra text, or comments."
        ),
        "user": (
            "Create the document structure for export to {format_name}.\n"
            "Return exactly ONE JSON object and nothing else.\n"
            "Format:\n"
            "{{\"blocks\":[{{\"type\":\"heading\",\"text\":\"...\"}},{{\"type\":\"paragraph\",\"text\":\"...\"}},{{\"type\":\"table\",\"header\":[\"…\",\"…\"],\"rows\":[[\"cell\",\"cell\"]]}}]}}\n"
            "Rules:\n"
            "- Every input line must appear completely and verbatim in exactly one block.\n"
            "- Do not include line-number prefixes such as 000: or metadata prefixes [TEXT]/[TABLE cols=N].\n"
            "- [TABLE cols=N] binds the row to EXACTLY N columns; never shift a value into another column.\n"
            "- ' | ' separates the N table cells. Empty positions are real cells and must be preserved.\n"
            "- The marker [[EMPTY]] represents an empty cell and must be returned as an empty JSON string.\n"
            "- Use real rows/cells for tables, never running text padded with spaces.\n"
            "- Use one consistent column scheme for similar register lines; do not invent column names.\n"
            "- Keep blocks in input order and use empty strings for missing values.\n"
            "- Output a table only when its rows contain at least two filled columns.\n"
            "- No output before or after the JSON.\n\n"
            "Lines:\n{}"
        ),
    },
    "fr": {
        "formats": {
            "docx": "document Word (.docx)",
            "xlsx": "classeur Excel (.xlsx)",
            "odt": "document LibreOffice Writer (.odt)",
            "ods": "feuille LibreOffice Calc (.ods)",
        },
        "group": "Export bureautique par IA (DOCX/XLSX/ODT/ODS)",
        "labels": {"system": "{fmt} – prompt système", "user": "{fmt} – prompt utilisateur"},
        "descriptions": {
            "system": "Instruction système pour l’export IA vers {format_name}. Elle contrôle la détection des titres, paragraphes et vrais tableaux.",
            "user": "Instruction utilisateur pour l’export IA vers {format_name}. Conserve le paramètre {{}} des lignes OCR numérotées et les doubles accolades JSON.",
        },
        "system": (
            "Tu es un assistant précis de structuration de documents historiques.\n"
            "Tu reçois des lignes numérotées déjà transcrites, dans l’ordre de lecture.\n"
            "Ta tâche est EXCLUSIVEMENT la structuration pour l’export vers {format_name}. Ne modifie, ne raccourcis, ne corrige et n’ajoute rien au texte.\n"
            "Détecte les lignes de tableau consécutives et découpe chaque ligne en cellules aux limites de colonnes.\n"
            "Les autres lignes deviennent des blocs paragraph; les titres courts deviennent des blocs heading.\n"
            "Toutes les lignes d’un bloc table doivent avoir le même nombre de colonnes; les cellules manquantes restent vides.\n"
            "Retourne uniquement du JSON valide, sans Markdown, texte supplémentaire ni commentaire."
        ),
        "user": (
            "Crée la structure du document pour l’export vers {format_name}.\n"
            "Retourne exactement UN objet JSON et rien d’autre.\n"
            "Format:\n"
            "{{\"blocks\":[{{\"type\":\"heading\",\"text\":\"...\"}},{{\"type\":\"paragraph\",\"text\":\"...\"}},{{\"type\":\"table\",\"header\":[\"…\",\"…\"],\"rows\":[[\"cellule\",\"cellule\"]]}}]}}\n"
            "Règles:\n"
            "- Chaque ligne d’entrée doit apparaître intégralement et mot pour mot dans un seul bloc.\n"
            "- Ne reprends ni les préfixes de numéro comme 000:, ni les métadonnées [TEXT]/[TABLE cols=N].\n"
            "- [TABLE cols=N] impose EXACTEMENT N colonnes; ne décale jamais une valeur vers une autre colonne.\n"
            "- ' | ' sépare les N cellules. Les positions vides sont de vraies cellules et doivent être conservées.\n"
            "- Le marqueur [[EMPTY]] représente une cellule vide et doit devenir une chaîne JSON vide.\n"
            "- Utilise de vraies rows/cellules, jamais du texte aligné avec des espaces.\n"
            "- Utilise un schéma de colonnes cohérent et n’invente pas de noms de colonnes.\n"
            "- Garde l’ordre des lignes et utilise des chaînes vides pour les valeurs manquantes.\n"
            "- Ne crée une table que si ses lignes ont au moins deux colonnes remplies.\n"
            "- Aucun texte avant ou après le JSON.\n\n"
            "Lignes:\n{}"
        ),
    },
}


def _bk_lmx_build_prompt_texts():
    result = {}
    for lang, base in _BK_LMX_PROMPT_BASES.items():
        mapping = {"prompt_group_lmx_office_export": base["group"]}
        for fmt, format_name in base["formats"].items():
            fmt_upper = fmt.upper()
            mapping[f"lm_prompt_lmx_{fmt}_system"] = base["labels"]["system"].format(fmt=fmt_upper)
            mapping[f"lm_prompt_lmx_{fmt}_user"] = base["labels"]["user"].format(fmt=fmt_upper)
            mapping[f"prompt_desc_lmx_{fmt}_system"] = base["descriptions"]["system"].format(format_name=format_name)
            mapping[f"prompt_desc_lmx_{fmt}_user"] = base["descriptions"]["user"].format(format_name=format_name)
            mapping[f"ai_prompt_lmx_{fmt}_system"] = base["system"].format(format_name=format_name)
            # Replace only the named format token. The final anonymous {} is intentionally kept
            # for the numbered OCR lines and is filled by lm_structured_export.py at runtime.
            mapping[f"ai_prompt_lmx_{fmt}_user"] = base["user"].replace("{format_name}", format_name)
        result[lang] = mapping
    return result


_BK_LMX_PROMPT_TEXTS = _bk_lmx_build_prompt_texts()


def _bk_prompt_ux_install_texts():
    combined_text_sets = (_BK_PROMPT_UX_EXTRA_TEXTS, _BK_LMX_PROMPT_TEXTS)
    for text_set in combined_text_sets:
        for lang, mapping in text_set.items():
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
            "ai_prompt_lmx_docx_system": "lm_prompt_lmx_docx_system",
            "ai_prompt_lmx_docx_user": "lm_prompt_lmx_docx_user",
            "ai_prompt_lmx_xlsx_system": "lm_prompt_lmx_xlsx_system",
            "ai_prompt_lmx_xlsx_user": "lm_prompt_lmx_xlsx_user",
            "ai_prompt_lmx_odt_system": "lm_prompt_lmx_odt_system",
            "ai_prompt_lmx_odt_user": "lm_prompt_lmx_odt_user",
            "ai_prompt_lmx_ods_system": "lm_prompt_lmx_ods_system",
            "ai_prompt_lmx_ods_user": "lm_prompt_lmx_ods_user",
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
    lang = getattr(window, "current_lang", translation.DEFAULT_LANGUAGE)
    return translation.translate(lang, key, *args)
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
    '_BK_LMX_PROMPT_BASES',
    '_BK_LMX_PROMPT_TEXTS',
    '_BK_PROMPT_UX_ORDER',
    '_bk_lm_show_prompt_settings_dialog',
    '_bk_prompt_ux_install_texts',
    '_bk_prompt_ux_make_group_item',
    '_bk_prompt_ux_ordered_items',
    '_bk_prompt_ux_text',
]
register_globals('bk', globals(), __all__)
