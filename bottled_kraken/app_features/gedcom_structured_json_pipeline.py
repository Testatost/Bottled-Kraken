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
def _bk_gedcom_structured_install_translations():
    for lang, mapping in _BK_GEDCOM_STRUCTURED_TEXTS.items():
        try:
            translation.TRANSLATIONS.setdefault(lang, {}).update(mapping)
        except Exception:
            try:
                TRANSLATIONS.setdefault(lang, {}).update(mapping)
            except Exception:
                pass
        try:
            if "_BK_GEDCOM_PROMPT_DEFAULTS" in globals():
                _BK_GEDCOM_PROMPT_DEFAULTS.setdefault(lang, {}).update(mapping)
        except Exception:
            pass
        try:
            if "_BK_LM_OPTIONS_TEXTS" in globals():
                _BK_LM_OPTIONS_TEXTS.setdefault(lang, {}).update({
                    "lm_prompt_gedcom_extract_system": mapping["lm_prompt_gedcom_extract_system"],
                    "lm_prompt_gedcom_extract_user": mapping["lm_prompt_gedcom_extract_user"],
                })
        except Exception:
            pass
    try:
        existing = [k for k, _label in _BK_LM_PROMPT_KEYS]
        extra = []
        if "ai_prompt_gedcom_extract_system" not in existing:
            extra.append(("ai_prompt_gedcom_extract_system", "lm_prompt_gedcom_extract_system"))
        if "ai_prompt_gedcom_extract_user" not in existing:
            extra.append(("ai_prompt_gedcom_extract_user", "lm_prompt_gedcom_extract_user"))
        if extra:
            globals()["_BK_LM_PROMPT_KEYS"] = tuple(_BK_LM_PROMPT_KEYS) + tuple(extra)
    except Exception:
        pass
def _bk_gedcom_structured_tr(worker, key: str, *args) -> str:
    lang = getattr(worker, "current_lang", translation.DEFAULT_LANGUAGE)
    return translation.translate(lang, key, *args)
def _bk_gedcom_safe_text(value) -> str:
    txt = str(value or "")
    txt = txt.replace("\r\n", "\n").replace("\r", "\n")
    txt = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", txt)
    txt = re.sub(r"[ \t]+", " ", txt)
    return txt.strip(" \t\n;,.|")
def _bk_gedcom_json_from_model_text(text: str):
    raw = str(text or "").strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE).strip()
    raw = re.sub(r"\s*```$", "", raw).strip()
    try:
        return json.loads(raw)
    except Exception:
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(raw[start:end + 1])
        except Exception:
            return None
    return None
def _bk_gedcom_person_has_data(person) -> bool:
    if not isinstance(person, dict):
        return False
    for key in ("given_names", "surname", "maiden_surname", "occupation", "residence", "religion", "note"):
        if _bk_gedcom_safe_text(person.get(key)):
            return True
    return False
def _bk_gedcom_person_name(given: str, surname: str, fallback_given: str = "Unbekannt") -> str:
    given = _bk_gedcom_safe_text(given)
    surname = _bk_gedcom_safe_text(surname)
    if not given and not surname:
        given = fallback_given
    if surname:
        return f"{given} /{surname}/".strip()
    return f"{given} //".strip()
def _bk_gedcom_note_lines(level: int, tag: str, value: str, out: list, max_chars: int = 12000):
    txt = _bk_gedcom_safe_text(value)
    if not txt:
        return
    txt = txt[:max_chars]
    parts = txt.split("\n")
    first = True
    for part in parts:
        part = _bk_gedcom_safe_text(part)
        if not part:
            continue
        while len(part) > 230:
            chunk = part[:230].rstrip()
            part = part[230:].lstrip()
            if first:
                out.append(f"{level} {tag} {chunk}")
                first = False
            else:
                out.append(f"{level + 1} CONT {chunk}")
        if first:
            out.append(f"{level} {tag} {part}")
            first = False
        else:
            out.append(f"{level + 1} CONT {part}")
def _bk_gedcom_date(value: str) -> str:
    txt = _bk_gedcom_safe_text(value)
    if not txt:
        return ""
    return txt
def _bk_gedcom_setdefault_person_dict(obj: dict, key: str) -> dict:
    val = obj.get(key)
    if isinstance(val, dict):
        return val
    return {}
def _bk_gedcom_build_from_structured(worker, data: dict) -> str:
    if not isinstance(data, dict):
        raise RuntimeError(self._tr("err_structured_gedcom_no_object"))
    record_type = _bk_gedcom_safe_text(data.get("record_type")).lower() or "unknown"
    registry_place = _bk_gedcom_safe_text(data.get("registry_place"))
    record_number = _bk_gedcom_safe_text(data.get("record_number"))
    entry_date = _bk_gedcom_date(data.get("entry_date"))
    event_date = _bk_gedcom_date(data.get("event_date"))
    event_time = _bk_gedcom_safe_text(data.get("event_time"))
    event_place = _bk_gedcom_safe_text(data.get("event_place")) or registry_place
    source_title = _bk_gedcom_safe_text(data.get("source_title"))
    transcription = _bk_gedcom_safe_text(data.get("transcription_or_notes"))
    uncertainty = bool(data.get("uncertainty", True))
    child = _bk_gedcom_setdefault_person_dict(data, "child")
    father = _bk_gedcom_setdefault_person_dict(data, "father")
    mother = _bk_gedcom_setdefault_person_dict(data, "mother")
    informant = _bk_gedcom_setdefault_person_dict(data, "informant")
    father_has = _bk_gedcom_person_has_data(father)
    mother_has = _bk_gedcom_person_has_data(mother)
    child_has = _bk_gedcom_person_has_data(child) or record_type == "birth" or event_date or father_has or mother_has
    informant_has = _bk_gedcom_person_has_data(informant)
    if not (child_has or father_has or mother_has or informant_has):
        raise RuntimeError(self._tr("err_no_usable_genealogical_person_data"))
    father_surname = _bk_gedcom_safe_text(father.get("surname"))
    child_given = _bk_gedcom_safe_text(child.get("given_names"))
    child_surname = _bk_gedcom_safe_text(child.get("surname"))
    if child_has and not child_given:
        child_given = "Unbenannt" if record_type == "birth" else "Unbekannt"
    if child_has and not child_surname and father_surname:
        child_surname = father_surname
        note = _bk_gedcom_safe_text(child.get("note"))
        derived = "Familienname aus dem Vater abgeleitet; bitte prüfen."
        child["note"] = f"{note} {derived}".strip()
    out = [
        "0 HEAD",
        "1 SOUR BottledKraken",
        "1 GEDC",
        "2 VERS 5.5.1",
        "2 FORM LINEAGE-LINKED",
        "1 CHAR UTF-8",
    ]
    id_counter = 1
    ids = {}
    def next_id(prefix="I"):
        nonlocal id_counter
        ident = f"@{prefix}{id_counter}@"
        id_counter += 1
        return ident
    child_id = next_id("I") if child_has else ""
    father_id = next_id("I") if father_has else ""
    mother_id = next_id("I") if mother_has else ""
    def add_person(pid: str, person: dict, role_label: str, *, is_child=False):
        given = child_given if is_child else _bk_gedcom_safe_text(person.get("given_names"))
        surname = child_surname if is_child else _bk_gedcom_safe_text(person.get("surname"))
        out.append(f"0 {pid} INDI")
        out.append("1 NAME " + _bk_gedcom_person_name(given, surname, "Unbekannt"))
        sex = _bk_gedcom_safe_text(person.get("sex")).upper()
        if is_child:
            if sex in ("M", "F"):
                out.append(f"1 SEX {sex}")
            elif sex in ("MALE", "MÄNNLICH", "MANN", "HOMME", "MASCULIN"):
                out.append("1 SEX M")
            elif sex in ("FEMALE", "WEIBLICH", "FRAU", "FEMME", "FÉMININ"):
                out.append("1 SEX F")
            else:
                out.append("1 SEX U")
        maiden = _bk_gedcom_safe_text(person.get("maiden_surname"))
        if maiden:
            _bk_gedcom_note_lines(1, "NOTE", f"Geburtsname/Mädchenname: {maiden}", out)
        occu = _bk_gedcom_safe_text(person.get("occupation"))
        if occu:
            out.append(f"1 OCCU {occu}")
        resi = _bk_gedcom_safe_text(person.get("residence"))
        if resi:
            out.append("1 RESI")
            out.append(f"2 PLAC {resi}")
        religion = _bk_gedcom_safe_text(person.get("religion"))
        if religion:
            _bk_gedcom_note_lines(1, "NOTE", f"Religion: {religion}", out)
        if is_child and record_type == "birth":
            out.append("1 BIRT")
            if event_date:
                out.append(f"2 DATE {event_date}")
            if event_place:
                out.append(f"2 PLAC {event_place}")
            if event_time:
                _bk_gedcom_note_lines(2, "NOTE", f"Geburtszeit: {event_time}", out)
        note = _bk_gedcom_safe_text(person.get("note"))
        role_note = f"Rolle im Dokument: {role_label}."
        if note:
            role_note += f" {note}"
        _bk_gedcom_note_lines(1, "NOTE", role_note, out)
        if source_title or registry_place or record_number or entry_date:
            out.append("1 SOUR @S1@")
    if child_has:
        add_person(child_id, child, "Kind", is_child=True)
    if father_has:
        add_person(father_id, father, "Vater")
    if mother_has:
        add_person(mother_id, mother, "Mutter")
    informant_id = ""
    if informant_has:
        inf_name = (_bk_gedcom_safe_text(informant.get("given_names")), _bk_gedcom_safe_text(informant.get("surname")))
        father_name = (_bk_gedcom_safe_text(father.get("given_names")), _bk_gedcom_safe_text(father.get("surname")))
        mother_name = (_bk_gedcom_safe_text(mother.get("given_names")), _bk_gedcom_safe_text(mother.get("surname")))
        if inf_name != father_name and inf_name != mother_name:
            informant_id = next_id("I")
            add_person(informant_id, informant, "Anzeigende Person")
        else:
            pass
    if child_has and (father_has or mother_has):
        out.append("0 @F1@ FAM")
        if father_has:
            out.append(f"1 HUSB {father_id}")
        if mother_has:
            out.append(f"1 WIFE {mother_id}")
        out.append(f"1 CHIL {child_id}")
        if child_has:
            pass
    title_parts = []
    if source_title:
        title_parts.append(source_title)
    if registry_place:
        title_parts.append(f"Standesamt/Ort: {registry_place}")
    if record_number:
        title_parts.append(f"Nr. {record_number}")
    if entry_date:
        title_parts.append(f"Eintrag: {entry_date}")
    if not title_parts:
        title_parts.append(os.path.basename(getattr(worker, "path", "")) or "Quelle")
    out.append("0 @S1@ SOUR")
    out.append("1 TITL " + " | ".join(title_parts))
    if uncertainty:
        _bk_gedcom_note_lines(1, "NOTE", "Automatisch aus Bild/OCR erzeugt; unsichere Lesungen bitte prüfen.", out)
    if transcription:
        _bk_gedcom_note_lines(1, "NOTE", transcription, out)
    out.append("0 TRLR")
    text = "\n".join(out).strip() + "\n"
    if not re.search(r"(?m)^0\s+@I\d+@\s+INDI\b", text):
        raise RuntimeError(self._tr("err_structured_data_no_indi"))
    return text
def _bk_gedcom_build_structured_payload(worker, image_data_url: str = "") -> dict:
    ocr_text = getattr(worker, "source_text", "") or "[Kein OCR-Text vorhanden. Bitte primär das Seitenbild auswerten.]"
    system_prompt = worker._tr("ai_prompt_gedcom_extract_system")
    user_prompt = worker._tr("ai_prompt_gedcom_extract_user", ocr_text)
    if image_data_url:
        user_content = [
            {"type": "text", "text": user_prompt},
            {"type": "image_url", "image_url": {"url": image_data_url}},
        ]
    else:
        user_content = user_prompt
    payload = {
        "model": worker.lm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        **worker._build_sampling_payload(),
    }
    payload["response_format"] = _bk_gedcom_response_format_structured()
    payload["max_tokens"] = max(int(getattr(worker, "max_tokens", 6000) or 6000), 2500)
    return payload
_BK_GEDCOM_V22_PREV_RUN = BKLocalGedcomWorker.run
def _bk_gedcom_worker_run_structured(self):
    try:
        if self._cancelled or self.isInterruptionRequested():
            raise RuntimeError(self._tr("msg_gedcom_cancelled"))
        image_data_url = self._page_image_data_url()
        if not getattr(self, "source_text", "") and not image_data_url:
            raise RuntimeError(self._tr("warn_gedcom_needs_text_or_image"))
        self.progress_changed.emit(5)
        self.status_changed.emit(_bk_gedcom_structured_tr(self, "log_gedcom_structured_start"))
        try:
            self.progress_changed.emit(18)
            data = self._post_json(_bk_gedcom_build_structured_payload(self, image_data_url=image_data_url))
            content = self._extract_message_content(data)
            obj = _bk_gedcom_json_from_model_text(content)
            gedcom_text = _bk_gedcom_build_from_structured(self, obj)
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_gedcom_cancelled"))
            self.progress_changed.emit(100)
            self.status_changed.emit(_bk_gedcom_structured_tr(self, "log_gedcom_structured_success"))
            self.finished_gedcom.emit(self.path, gedcom_text)
            return
        except Exception as structured_exc:
            if self._cancelled or self.isInterruptionRequested():
                raise
            self.status_changed.emit(_bk_gedcom_structured_tr(self, "log_gedcom_structured_fallback"))
            try:
                self.status_changed.emit(self._tr("status_gedcom_structured_extraction_failed", str(structured_exc)[:500]))
            except Exception:
                pass
        return _BK_GEDCOM_V22_PREV_RUN(self)
    except Exception as exc:
        self.failed_gedcom.emit(self.path, str(exc))
_bk_gedcom_structured_install_translations()
BKLocalGedcomWorker.run = _bk_gedcom_worker_run_structured
"""GEDCOM-Vorschau-/Bearbeitungsdialog vor dem Export.
Ersetzt den direkten Speichern-Dialog nach der GEDCOM-Erzeugung durch eine
prüfbare Übersicht mit bearbeitbaren erkannten Daten, editierbarem GEDCOM-Text
und anschließendem Export.
"""
try:
    from PySide6.QtWidgets import QTabWidget
except Exception:
    QTabWidget = None
__all__ = [
    '_BK_GEDCOM_PROMPT_DEFAULTS',
    '_BK_GEDCOM_REVIEW_TEXTS',
    '_BK_GEDCOM_ROBUST_TEXTS',
    '_BK_GEDCOM_SAVE_FIX_TEXTS',
    '_BK_GEDCOM_STRUCTURED_TEXTS',
    '_BK_GEDCOM_V22_PREV_RUN',
    '_BK_GEDCOM_VISION_TEXTS',
    '_BK_PROMPT_UX_EXTRA_TEXTS',
    '_bk_gedcom_build_from_structured',
    '_bk_gedcom_build_structured_payload',
    '_bk_gedcom_date',
    '_bk_gedcom_json_from_model_text',
    '_bk_gedcom_note_lines',
    '_bk_gedcom_person_has_data',
    '_bk_gedcom_person_name',
    '_bk_gedcom_safe_text',
    '_bk_gedcom_setdefault_person_dict',
    '_bk_gedcom_structured_install_translations',
    '_bk_gedcom_structured_tr',
    '_bk_gedcom_worker_run_structured',
]
register_globals('bk', globals(), __all__)
