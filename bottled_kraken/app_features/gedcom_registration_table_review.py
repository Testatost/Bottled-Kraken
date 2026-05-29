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
def _bk_gedcom_reg_clean(value) -> str:
    txt = str(value or "")
    txt = txt.replace("\r\n", "\n").replace("\r", "\n")
    txt = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", txt)
    txt = re.sub(r"\s+", " ", txt).strip(" \t\n;,.|")
    return txt
def _bk_gedcom_reg_split_name(full_name: str):
    name = _bk_gedcom_reg_clean(full_name)
    name = re.sub(r"\([^)]*\)", " ", name)
    name = re.sub(r"\s+", " ", name).strip(" ,.;")
    if not name:
        return "", ""
    parts = name.split()
    if len(parts) == 1:
        return parts[0], ""
    return " ".join(parts[1:]), parts[0]
def _bk_gedcom_reg_name_from_registration(reg: dict) -> str:
    if not isinstance(reg, dict):
        return ""
    person = reg.get("person") if isinstance(reg.get("person"), dict) else {}
    full = _bk_gedcom_reg_clean(reg.get("name") or person.get("full_name") or person.get("label"))
    if full:
        return full
    given = _bk_gedcom_reg_clean(person.get("given_names") or person.get("first_name"))
    surname = _bk_gedcom_reg_clean(person.get("surname") or person.get("last_name"))
    if given or surname:
        return f"{surname} {given}".strip()
    return ""
def _bk_gedcom_reg_extract_from_source_line(line: str) -> dict:
    raw = _bk_gedcom_reg_clean(line)
    if not raw:
        return {}
    if re.fullmatch(r"(seite|page)\s*[-–]?\s*\d+", raw, flags=re.IGNORECASE):
        return {}
    if len(raw) < 4:
        return {}
    age = ""
    m_age = re.search(r"\b(\d{1,3}\s*(?:Jahre?|Jahr|J\.|Monate?|Mon\.?|Tage?|Wochen?|Years?|Months?|Days?))\b", raw, flags=re.IGNORECASE)
    if m_age:
        age = m_age.group(1).strip()
    date = ""
    m_date = re.search(r"\b(\d{1,2}\.\s*(?:[IVXLCDM]{1,8}|\d{1,2})\.?\s*(?:1[5-9]\d{2}|20\d{2})?|1[5-9]\d{2}|20\d{2})\b", raw, flags=re.IGNORECASE)
    if m_date:
        date = m_date.group(1).strip(" .,")
    cut = len(raw)
    for m in (m_age, m_date):
        if m:
            cut = min(cut, m.start())
    name_part = raw[:cut].strip(" ,.;:-")
    name_part = re.sub(r"^\d+\s*", "", name_part)
    name_part = name_part[:90].strip(" ,.;")
    if not re.search(r"[A-Za-zÄÖÜäöüß]", name_part):
        return {}
    given, surname = _bk_gedcom_reg_split_name(name_part)
    rest_start = max((m.end() for m in (m_age, m_date) if m), default=0)
    rest = raw[rest_start:].strip(" ,.;:-")
    place = ""
    place_candidates = re.findall(r"\b([A-ZÄÖÜ][A-Za-zÄÖÜäöüß.\-]{2,}(?:\s+[A-ZÄÖÜ][A-Za-zÄÖÜäöüß.\-]{2,})?)\b", rest)
    if place_candidates:
        place = place_candidates[-1].strip(" .,")
    return {
        "selected": True,
        "source_line": raw,
        "name": name_part,
        "person": {"given_names": given, "surname": surname},
        "age": age,
        "event_date": date,
        "event_place": place,
        "residence": place,
        "occupation": "",
        "notes": raw,
        "uncertainty": False,
    }
def _bk_gedcom_registrations_from_text(text: str) -> list:
    txt = str(text or "")
    lines = []
    for raw in txt.splitlines():
        line = raw.strip()
        m = re.match(r"^\d+\s+CONT\s+(.+)$", line, flags=re.IGNORECASE)
        if m:
            line = m.group(1).strip()
        elif re.match(r"^\d+\s+\w+\b", line):
            continue
        if line:
            lines.append(line)
    regs = []
    seen = set()
    for line in lines[:800]:
        reg = _bk_gedcom_reg_extract_from_source_line(line)
        if not reg:
            continue
        key = (_bk_gedcom_reg_clean(reg.get("name")).lower(), _bk_gedcom_reg_clean(reg.get("event_date")).lower(), _bk_gedcom_reg_clean(reg.get("age")).lower())
        if not key[0] or key in seen:
            continue
        seen.add(key)
        regs.append(reg)
    return regs
def _bk_gedcom_reg_note(level: int, text: str, out: list):
    text = _bk_gedcom_reg_clean(text)
    if not text:
        return
    chunks = [text[i:i+220] for i in range(0, len(text), 220)] or [text]
    out.append(f"{level} NOTE {chunks[0]}")
    for chunk in chunks[1:]:
        out.append(f"{level + 1} CONT {chunk}")
def _bk_gedcom_build_from_registrations(worker, data: dict) -> str:
    regs = data.get("registrations") if isinstance(data, dict) else []
    if not isinstance(regs, list):
        regs = []
    selected = [r for r in regs if isinstance(r, dict) and bool(r.get("selected", True))]
    if not selected:
        selected = [r for r in regs if isinstance(r, dict)]
    if not selected:
        raise RuntimeError(_bk_gedcom_review_text(self.window, "err_no_selected_registrations"))
    source_title = _bk_gedcom_reg_clean(data.get("source_title") or os.path.basename(getattr(worker, "path", "") or ""))
    out = [
        "0 HEAD",
        "1 SOUR BottledKraken",
        "1 GEDC",
        "2 VERS 5.5.1",
        "2 FORM LINEAGE-LINKED",
        "1 CHAR UTF-8",
    ]
    for idx, reg in enumerate(selected, start=1):
        person = reg.get("person") if isinstance(reg.get("person"), dict) else {}
        name = _bk_gedcom_reg_name_from_registration(reg)
        given = _bk_gedcom_reg_clean(person.get("given_names") or person.get("first_name"))
        surname = _bk_gedcom_reg_clean(person.get("surname") or person.get("last_name"))
        if not (given or surname):
            given, surname = _bk_gedcom_reg_split_name(name)
        if not (given or surname):
            given = "Unbekannt"
        out.append(f"0 @I{idx}@ INDI")
        out.append(f"1 NAME {given or 'Unbekannt'} /{surname}/")
        age = _bk_gedcom_reg_clean(reg.get("age") or person.get("age"))
        if age:
            _bk_gedcom_reg_note(1, f"Alter: {age}", out)
        occu = _bk_gedcom_reg_clean(reg.get("occupation") or person.get("occupation"))
        if occu:
            out.append(f"1 OCCU {occu}")
        residence = _bk_gedcom_reg_clean(reg.get("residence") or reg.get("event_place") or person.get("residence"))
        if residence:
            out.append("1 RESI")
            out.append(f"2 PLAC {residence}")
        event_date = _bk_gedcom_reg_clean(reg.get("event_date") or reg.get("year"))
        event_place = _bk_gedcom_reg_clean(reg.get("event_place") or residence)
        if event_date or event_place:
            out.append("1 EVEN")
            out.append("2 TYPE Registereintrag")
            if event_date:
                out.append(f"2 DATE {event_date}")
            if event_place:
                out.append(f"2 PLAC {event_place}")
        note = _bk_gedcom_reg_clean(reg.get("notes") or reg.get("source_line"))
        if note:
            _bk_gedcom_reg_note(1, note, out)
        if source_title:
            out.append("1 SOUR @S1@")
    if source_title:
        out.extend(["0 @S1@ SOUR", f"1 TITL {source_title}"])
    out.append("0 TRLR")
    return "\n".join(out).strip() + "\n"
def _bk_gedcom_build_from_structured(worker, data: dict) -> str:
    try:
        if isinstance(data, dict) and isinstance(data.get("registrations"), list) and data.get("registrations"):
            try:
                setattr(worker, "_bk_gedcom_structured_data", _bk_gedcom_review_deepcopy(data))
                setattr(worker, "_bk_gedcom_used_structured", True)
            except Exception:
                pass
            return _bk_gedcom_build_from_registrations(worker, data)
    except Exception:
        pass
    if _BK_GEDCOM_REG_PREV_BUILD_FROM_STRUCTURED is None:
        raise RuntimeError(_bk_gedcom_review_text(self.window, "err_structured_gedcom_builder_missing"))
    return _BK_GEDCOM_REG_PREV_BUILD_FROM_STRUCTURED(worker, data)
def _bk_gedcom_review_prepare_structured(gedcom_text: str, structured_data):
    data = _bk_gedcom_review_deepcopy(structured_data) if isinstance(structured_data, dict) else {}
    regs = data.get("registrations") if isinstance(data, dict) else None
    if not isinstance(regs, list) or not regs:
        regs = _bk_gedcom_registrations_from_text(gedcom_text)
        if regs:
            data["registrations"] = regs
            data.setdefault("source_title", "OCR register page")
    return data if isinstance(data, dict) and data.get("registrations") else structured_data
_BK_GEDCOM_REG_PREV_DIALOG_INIT = BKGedcomReviewDialog.__init__
def _bk_gedcom_review_dialog_init_registrations(self, window, path: str, gedcom_text: str, structured_data=None, parent=None):
    structured_data = _bk_gedcom_review_prepare_structured(gedcom_text, structured_data)
    _BK_GEDCOM_REG_PREV_DIALOG_INIT(self, window, path, gedcom_text, structured_data, parent)
def _bk_gedcom_review_populate_overview_registrations(self):
    if isinstance(self.structured_data, dict) and isinstance(self.structured_data.get("registrations"), list) and self.structured_data.get("registrations"):
        self.tree.clear()
        group = self._make_group("gedcom_group_registrations")
        for idx, reg in enumerate(self.structured_data.get("registrations") or []):
            if not isinstance(reg, dict):
                continue
            name = _bk_gedcom_reg_name_from_registration(reg) or f"Person {idx + 1}"
            summary_bits = [name]
            for key in ("age", "event_date", "event_place"):
                val = _bk_gedcom_reg_clean(reg.get(key))
                if val:
                    summary_bits.append(val)
            item = QTreeWidgetItem([_bk_gedcom_review_text(self.window, "gedcom_registration_selected"), " | ".join(summary_bits)])
            item.setData(0, Qt.UserRole, f"registrations.{idx}.selected")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Checked if bool(reg.get("selected", True)) else Qt.Unchecked)
            group.addChild(item)
            person = reg.get("person") if isinstance(reg.get("person"), dict) else {}
            flat = {
                "name": _bk_gedcom_reg_name_from_registration(reg),
                "person.given_names": person.get("given_names") or person.get("first_name") or "",
                "person.surname": person.get("surname") or person.get("last_name") or "",
                "age": reg.get("age", ""),
                "event_date": reg.get("event_date", ""),
                "event_place": reg.get("event_place", ""),
                "residence": reg.get("residence", ""),
                "occupation": reg.get("occupation", ""),
                "notes": reg.get("notes") or reg.get("source_line") or "",
            }
            label_map = {
                "name": "gedcom_registration_name",
                "person.given_names": "gedcom_field_given_names",
                "person.surname": "gedcom_field_surname",
                "age": "gedcom_registration_age",
                "event_date": "gedcom_registration_date",
                "event_place": "gedcom_registration_place",
                "residence": "gedcom_field_residence",
                "occupation": "gedcom_field_occupation",
                "notes": "gedcom_registration_note",
            }
            for field, value in flat.items():
                child = QTreeWidgetItem([_bk_gedcom_review_text(self.window, label_map.get(field, field)), str(value or "")])
                child.setData(0, Qt.UserRole, f"registrations.{idx}.{field}")
                child.setFlags(child.flags() | Qt.ItemIsEditable)
                item.addChild(child)
        self.tree.collapseAll()
        self.update_btn.setEnabled(True)
        self.warning_label.setVisible(False)
        return
    return _BK_GEDCOM_REG_PREV_POPULATE(self)
_BK_GEDCOM_REG_PREV_POPULATE = BKGedcomReviewDialog._populate_overview
def _bk_gedcom_review_tree_to_structured_data_registrations(self) -> dict:
    data = _bk_gedcom_review_deepcopy(self.structured_data) if isinstance(self.structured_data, dict) else {}
    if isinstance(data.get("registrations"), list):
        for i in range(self.tree.topLevelItemCount()):
            group = self.tree.topLevelItem(i)
            for j in range(group.childCount()):
                item = group.child(j)
                key_path = item.data(0, Qt.UserRole)
                if not key_path or not str(key_path).startswith("registrations."):
                    continue
                parts = str(key_path).split(".")
                if len(parts) < 3:
                    continue
                try:
                    idx = int(parts[1])
                except Exception:
                    continue
                if idx < 0 or idx >= len(data["registrations"]):
                    continue
                field = ".".join(parts[2:])
                reg = data["registrations"][idx]
                if field == "selected":
                    reg["selected"] = item.checkState(0) == Qt.Checked
                for k in range(item.childCount()):
                    child = item.child(k)
                    cpath = str(child.data(0, Qt.UserRole) or "")
                    cparts = cpath.split(".")
                    if len(cparts) < 3:
                        continue
                    cfield = ".".join(cparts[2:])
                    value = child.text(1).strip()
                    if cfield.startswith("person."):
                        person = reg.setdefault("person", {})
                        person[cfield.split(".", 1)[1]] = value
                    else:
                        reg[cfield] = value
        return data
    return _BK_GEDCOM_REG_PREV_TREE_TO_STRUCTURED(self)
_BK_GEDCOM_REG_PREV_TREE_TO_STRUCTURED = BKGedcomReviewDialog._tree_to_structured_data
def _bk_gedcom_review_update_from_overview_registrations(self):
    if isinstance(self.structured_data, dict) and isinstance(self.structured_data.get("registrations"), list):
        data = self._tree_to_structured_data()
        fake_worker = type("BKGedcomReviewBuildContext", (), {})()
        fake_worker.path = self.path
        try:
            gedcom_text = _bk_gedcom_build_from_registrations(fake_worker, data)
            gedcom_text = _bk_gedcom_review_finalize_text(gedcom_text)
        except Exception as exc:
            QMessageBox.warning(self, _bk_gedcom_review_text(self.window, "warn_title"), _bk_gedcom_review_text(self.window, "gedcom_review_update_failed", exc))
            return
        self.structured_data = data
        self.text_edit.setPlainText(gedcom_text)
        self._update_warning()
        return
    return _BK_GEDCOM_REG_PREV_UPDATE(self)
_BK_GEDCOM_REG_PREV_UPDATE = BKGedcomReviewDialog.update_gedcom_from_overview
def _bk_gedcom_review_export_gedcom_registrations(self):
    if isinstance(self.structured_data, dict) and isinstance(self.structured_data.get("registrations"), list):
        data = self._tree_to_structured_data()
        fake_worker = type("BKGedcomReviewBuildContext", (), {})()
        fake_worker.path = self.path
        try:
            self.structured_data = data
            self.text_edit.setPlainText(_bk_gedcom_review_finalize_text(_bk_gedcom_build_from_registrations(fake_worker, data)))
        except Exception:
            pass
    return _BK_GEDCOM_REG_PREV_EXPORT(self)
_BK_GEDCOM_REG_PREV_EXPORT = BKGedcomReviewDialog.export_gedcom
BKGedcomReviewDialog.__init__ = _bk_gedcom_review_dialog_init_registrations
BKGedcomReviewDialog._populate_overview = _bk_gedcom_review_populate_overview_registrations
BKGedcomReviewDialog._tree_to_structured_data = _bk_gedcom_review_tree_to_structured_data_registrations
BKGedcomReviewDialog.update_gedcom_from_overview = _bk_gedcom_review_update_from_overview_registrations
BKGedcomReviewDialog.export_gedcom = _bk_gedcom_review_export_gedcom_registrations
__all__ = [
    '_BK_GEDCOM_PROMPT_DEFAULTS',
    '_BK_GEDCOM_REG_PREV_DIALOG_INIT',
    '_BK_GEDCOM_REG_PREV_EXPORT',
    '_BK_GEDCOM_REG_PREV_POPULATE',
    '_BK_GEDCOM_REG_PREV_TREE_TO_STRUCTURED',
    '_BK_GEDCOM_REG_PREV_UPDATE',
    '_BK_GEDCOM_REVIEW_TEXTS',
    '_BK_GEDCOM_ROBUST_TEXTS',
    '_BK_GEDCOM_SAVE_FIX_TEXTS',
    '_BK_GEDCOM_STRUCTURED_TEXTS',
    '_BK_GEDCOM_VISION_TEXTS',
    '_BK_PROMPT_UX_EXTRA_TEXTS',
    '_bk_gedcom_build_from_registrations',
    '_bk_gedcom_build_from_structured',
    '_bk_gedcom_reg_clean',
    '_bk_gedcom_reg_extract_from_source_line',
    '_bk_gedcom_reg_name_from_registration',
    '_bk_gedcom_reg_note',
    '_bk_gedcom_reg_split_name',
    '_bk_gedcom_registrations_from_text',
    '_bk_gedcom_review_dialog_init_registrations',
    '_bk_gedcom_review_export_gedcom_registrations',
    '_bk_gedcom_review_populate_overview_registrations',
    '_bk_gedcom_review_prepare_structured',
    '_bk_gedcom_review_tree_to_structured_data_registrations',
    '_bk_gedcom_review_update_from_overview_registrations',
]
register_globals('bk', globals(), __all__)
