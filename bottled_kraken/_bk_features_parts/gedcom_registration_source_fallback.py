"""Deterministische GEDCOM-Erzeugung für Register-/Tabellenseiten.

Diese Runtime-Schicht greift nur bei OCR-Texten, die wie eine Liste mehrerer
Personen-/Registereinträge aussehen. Sie verändert keine LM-Zeilenüberarbeitung.
"""

import os
import re


def _bk_gedcom_reg_source_clean(value) -> str:
    txt = str(value or "")
    txt = txt.replace("\r\n", "\n").replace("\r", "\n")
    txt = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", txt)
    txt = re.sub(r"[ \t]+", " ", txt)
    return txt.strip(" \t\n;,.|")


def _bk_gedcom_reg_source_line_text(line: str) -> str:
    raw = _bk_gedcom_reg_source_clean(line)
    raw = re.sub(r"^\s*\d{1,5}\s+", "", raw).strip()
    return raw


def _bk_gedcom_reg_source_is_heading(line: str) -> bool:
    txt = _bk_gedcom_reg_source_line_text(line).lower()
    if not txt:
        return True
    if len(txt) < 5:
        return True
    heading_patterns = (
        r"^seite\s*[-–]?\s*\d+",
        r"^page\s*[-–]?\s*\d+",
        r"^[-–—]+\s*[ivxlcdm]+\s*[-–—]+$",
        r"^name\b",
        r"^person\b",
        r"^tabelle\b",
        r"^register\b",
        r"^geburts[- ]?register\b",
        r"^sterbe[- ]?register\b",
    )
    return any(re.search(pat, txt, flags=re.IGNORECASE) for pat in heading_patterns)


def _bk_gedcom_reg_source_age_match(raw: str):
    return re.search(
        r"\b(\d{1,3}\s*(?:Jahre?|Jahr|J\.?|Monate?|Mon\.?|Tage?|Tag|Wochen?|W\.?|Years?|Months?|Days?))\b",
        raw,
        flags=re.IGNORECASE,
    )


def _bk_gedcom_reg_source_date_match(raw: str):
    return re.search(
        r"\b(\d{1,2}\.\s*(?:[IVXLCDM]{1,8}|\d{1,2})\.?\s*(?:1[5-9]\d{2}|20\d{2})|\d{1,2}\.\s*(?:[IVXLCDM]{1,8}|\d{1,2})\.?|(?:1[5-9]\d{2}|20\d{2}))\b",
        raw,
        flags=re.IGNORECASE,
    )


def _bk_gedcom_reg_source_split_name(full_name: str):
    name = _bk_gedcom_reg_source_clean(full_name)
    name = re.sub(r"\([^)]*\)", " ", name)
    name = re.sub(r"\[[^]]*\]", " ", name)
    name = re.sub(r"\s+", " ", name).strip(" ,.;:-")
    if not name:
        return "", ""
    parts = name.split()
    if len(parts) == 1:
        return parts[0], ""
    # Historische Register sind hier meist: Nachname Vorname(n).
    return " ".join(parts[1:]), parts[0]


def _bk_gedcom_reg_extract_from_source_line(line: str) -> dict:
    raw = _bk_gedcom_reg_source_line_text(line)
    if _bk_gedcom_reg_source_is_heading(raw):
        return {}

    m_age = _bk_gedcom_reg_source_age_match(raw)
    m_date = _bk_gedcom_reg_source_date_match(raw)
    # Für Register-Tabellen nur Zeilen akzeptieren, die mindestens Alter oder Datum/Jahr enthalten.
    if not (m_age or m_date):
        return {}

    cut = len(raw)
    for match in (m_age, m_date):
        if match:
            cut = min(cut, match.start())
    name_area = raw[:cut].strip(" ,.;:-")
    if "," in name_area:
        name_part = name_area.split(",", 1)[0].strip(" ,.;:-")
    else:
        name_part = name_area
    name_part = re.sub(r"\b(?:geb\.?|gest\.?|verh\.?|ledig|witwe|wwe\.)\b.*$", "", name_part, flags=re.IGNORECASE).strip()
    name_part = re.sub(r"\s+", " ", name_part).strip(" ,.;:-")[:100]
    if not re.search(r"[A-Za-zÄÖÜäöüß]", name_part):
        return {}
    if len(name_part.split()) < 2 and "," not in name_area:
        return {}

    given, surname = _bk_gedcom_reg_source_split_name(name_part)
    if not (given or surname):
        return {}

    age = m_age.group(1).strip() if m_age else ""
    date = m_date.group(1).strip(" .,;") if m_date else ""

    rest_start = max((m.end() for m in (m_age, m_date) if m), default=0)
    rest = raw[rest_start:].strip(" ,.;:-")
    rest = re.sub(r"^\d{1,4}\.?\s*", "", rest).strip(" ,.;:-")
    place = ""
    place_candidates = re.findall(
        r"\b([A-ZÄÖÜ][A-Za-zÄÖÜäöüß.\-]{2,}(?:\s+[A-ZÄÖÜ][A-Za-zÄÖÜäöüß.\-]{2,})?)\b",
        rest,
    )
    if place_candidates:
        place = place_candidates[-1].strip(" .,;")

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
    lines = []
    for raw in str(text or "").replace("\r\n", "\n").replace("\r", "\n").splitlines():
        line = raw.strip()
        # GEDCOM-Fallback-NOTEs wieder in normalen Quelltext zurückverwandeln.
        m_cont = re.match(r"^\d+\s+CONT\s+(.+)$", line, flags=re.IGNORECASE)
        m_note = re.match(r"^\d+\s+NOTE\s+(.+)$", line, flags=re.IGNORECASE)
        if m_cont:
            line = m_cont.group(1).strip()
        elif m_note:
            line = m_note.group(1).strip()
        elif re.match(r"^\d+\s+(HEAD|SOUR|GEDC|VERS|FORM|CHAR|TRLR|INDI|NAME|_BK_FALLBACK)\b", line, flags=re.IGNORECASE):
            continue
        if line:
            lines.append(line)

    regs = []
    seen = set()
    for line in lines[:1200]:
        reg = _bk_gedcom_reg_extract_from_source_line(line)
        if not reg:
            continue
        key = (
            _bk_gedcom_reg_source_clean(reg.get("name")).lower(),
            _bk_gedcom_reg_source_clean(reg.get("event_date")).lower(),
            _bk_gedcom_reg_source_clean(reg.get("age")).lower(),
        )
        if not key[0] or key in seen:
            continue
        seen.add(key)
        regs.append(reg)
    return regs


def _bk_gedcom_source_text_looks_like_register(text: str, regs: list) -> bool:
    if not isinstance(regs, list) or len(regs) < 2:
        return False
    source_lines = [ln for ln in str(text or "").splitlines() if _bk_gedcom_reg_source_line_text(ln)]
    if len(source_lines) < 2:
        return False
    strong = 0
    for reg in regs:
        if not isinstance(reg, dict):
            continue
        if reg.get("age") or reg.get("event_date"):
            strong += 1
    return strong >= 2


def _bk_gedcom_response_format_structured() -> dict:
    """Schema mit expliziter registrations-Liste, damit lokale Server diese nicht verwerfen."""
    person_schema = {
        "type": "object",
        "properties": {
            "given_names": {"type": "string"},
            "surname": {"type": "string"},
            "full_name": {"type": "string"},
            "sex": {"type": "string"},
            "age": {"type": "string"},
            "occupation": {"type": "string"},
            "residence": {"type": "string"},
            "religion": {"type": "string"},
            "note": {"type": "string"},
        },
        "additionalProperties": True,
    }
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "gedcom_extraction",
            "schema": {
                "type": "object",
                "properties": {
                    "record_type": {"type": "string"},
                    "registry_place": {"type": "string"},
                    "record_number": {"type": "string"},
                    "entry_date": {"type": "string"},
                    "event_date": {"type": "string"},
                    "event_time": {"type": "string"},
                    "event_place": {"type": "string"},
                    "child": person_schema,
                    "father": person_schema,
                    "mother": person_schema,
                    "informant": person_schema,
                    "registrations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "selected": {"type": "boolean"},
                                "name": {"type": "string"},
                                "person": person_schema,
                                "age": {"type": "string"},
                                "event_date": {"type": "string"},
                                "event_place": {"type": "string"},
                                "residence": {"type": "string"},
                                "occupation": {"type": "string"},
                                "notes": {"type": "string"},
                                "source_line": {"type": "string"},
                                "uncertainty": {"type": "boolean"},
                            },
                            "additionalProperties": True,
                        },
                    },
                    "source_title": {"type": "string"},
                    "transcription_or_notes": {"type": "string"},
                    "uncertainty": {"type": "boolean"},
                },
                "required": ["record_type", "child", "father", "mother", "informant", "uncertainty"],
                "additionalProperties": True,
            },
        },
    }


_BK_GEDCOM_REG_SOURCE_PREV_RUN = BKLocalGedcomWorker.run


def _bk_gedcom_worker_run_registration_source(self):
    try:
        source_text = getattr(self, "source_text", "") or ""
        regs = _bk_gedcom_registrations_from_text(source_text)
        if _bk_gedcom_source_text_looks_like_register(source_text, regs):
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_gedcom_cancelled"))
            try:
                self.progress_changed.emit(10)
                self.status_changed.emit("GEDCOM: Register-/Tabellenseite erkannt; erzeuge Personendatensätze direkt aus OCR-Zeilen.")
            except Exception:
                pass
            data = {
                "record_type": "register",
                "source_title": os.path.basename(getattr(self, "path", "") or "OCR register page"),
                "registrations": regs,
                "transcription_or_notes": source_text,
                "uncertainty": False,
            }
            setattr(self, "_bk_gedcom_structured_data", data)
            setattr(self, "_bk_gedcom_used_structured", True)
            gedcom_text = _bk_gedcom_build_from_registrations(self, data)
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_gedcom_cancelled"))
            try:
                self.progress_changed.emit(100)
            except Exception:
                pass
            self.finished_gedcom.emit(self.path, gedcom_text)
            return
    except Exception:
        # Bei unklaren Fällen den bisherigen LM-/Vision-Pfad nicht blockieren.
        pass
    return _BK_GEDCOM_REG_SOURCE_PREV_RUN(self)


try:
    BKLocalGedcomWorker.run = _bk_gedcom_worker_run_registration_source
except Exception:
    pass
