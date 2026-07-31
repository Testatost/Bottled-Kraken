from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
import os
import re
def _bk_db_reg_clean(value) -> str:
    txt = str(value or "")
    txt = txt.replace("\r\n", "\n").replace("\r", "\n")
    txt = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", txt)
    txt = re.sub(r"\s+", " ", txt).strip(" \t\n;,.|-")
    return txt
def _bk_db_reg_slug(value, fallback="item") -> str:
    txt = _bk_db_reg_clean(value).lower()
    txt = txt.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    txt = re.sub(r"[^a-z0-9]+", "_", txt)
    txt = re.sub(r"_+", "_", txt).strip("_")
    if not txt:
        txt = fallback
    if txt[0].isdigit():
        txt = "id_" + txt
    return txt
def _bk_db_reg_year_from_date(value: str):
    m = re.search(r"\b(1[5-9]\d{2}|20\d{2})\b", str(value or ""))
    return int(m.group(1)) if m else None
def _bk_db_reg_clean_place(value: str) -> str:
    txt = _bk_db_reg_clean(value)
    txt = re.sub(r"^(?:[IVXLCDM]{1,8}|\d{1,2})\.?\s+", "", txt, flags=re.IGNORECASE)
    txt = re.sub(r"\b(?:Jahre?|Jahr|Monate?|Mon\.?|Tage?|Wochen?|W\.?|Years?|Months?|Days?)\b", "", txt, flags=re.IGNORECASE)
    txt = re.sub(r"\b\d{1,4}\b", "", txt)
    txt = re.sub(r"\s+", " ", txt).strip(" ,.;:-")
    return txt[:120]
def _bk_db_regs_from_text(text: str) -> list:
    regs = []
    try:
        fn = globals().get("_bk_gedcom_registrations_from_text")
        if callable(fn):
            regs = fn(text)
    except Exception:
        regs = []
    if not isinstance(regs, list):
        regs = []
    out = []
    seen = set()
    for idx, reg in enumerate(regs, start=1):
        if not isinstance(reg, dict):
            continue
        person = reg.get("person") if isinstance(reg.get("person"), dict) else {}
        surname = _bk_db_reg_clean(person.get("surname"))
        given = _bk_db_reg_clean(person.get("given_names") or person.get("first_name"))
        name = _bk_db_reg_clean(reg.get("name") or " ".join(x for x in (surname, given) if x))
        if not name:
            continue
        age = _bk_db_reg_clean(reg.get("age"))
        event_date = _bk_db_reg_clean(reg.get("event_date"))
        event_place = _bk_db_reg_clean_place(reg.get("event_place") or reg.get("residence"))
        source_line = _bk_db_reg_clean(reg.get("source_line") or reg.get("notes"))
        if not source_line:
            source_line = name
        key = (name.lower(), age.lower(), event_date.lower(), source_line.lower())
        if key in seen:
            continue
        seen.add(key)
        person_id = f"person_{idx:04d}_{_bk_db_reg_slug(name, 'person')}"
        out.append({
            "id": person_id,
            "entry_id": f"entry_{idx:04d}",
            "full_name": name,
            "first_name": given or None,
            "last_name": surname or None,
            "age": age or None,
            "event_date": event_date or None,
            "event_year": _bk_db_reg_year_from_date(event_date or source_line),
            "event_place": event_place or None,
            "occupation": _bk_db_reg_clean(reg.get("occupation")) or None,
            "source_excerpt": source_line[:1000],
        })
    return out
def _bk_db_text_looks_like_register(text: str, rows: list) -> bool:
    if not isinstance(rows, list) or len(rows) < 2:
        return False
    strong = 0
    for row in rows:
        if row.get("full_name") and (row.get("age") or row.get("event_date") or row.get("event_year")):
            strong += 1
    return strong >= 2
def _bk_db_postgres_from_register_rows(source_text: str, rows: list) -> dict:
    payload = _ptr_postgres_empty_payload(source_text) if callable(globals().get("_ptr_postgres_empty_payload")) else {
        "document": {"id": "document_1", "title": None, "source_type": "ocr_text", "language": None, "raw_excerpt": str(source_text or "")[:1000] or None},
        "persons": [], "places": [], "streets": [], "years": [], "organizations": [], "references": [], "sqlite_export": {"tables": {"persons": [], "documents": [], "entries": []}},
    }
    persons = []
    places = []
    years = []
    refs = []
    place_ids = {}
    year_ids = {}
    sqlite_persons = []
    sqlite_entries = []
    for row in rows:
        person_id = row["id"]
        persons.append({
            "id": person_id,
            "full_name": row.get("full_name"),
            "first_name": row.get("first_name"),
            "last_name": row.get("last_name"),
            "age": row.get("age"),
            "event_date": row.get("event_date"),
            "event_place": row.get("event_place"),
            "occupation": row.get("occupation"),
            "description": None,
            "source_excerpt": row.get("source_excerpt"),
        })
        sqlite_persons.append({
            "id": person_id,
            "full_name": row.get("full_name"),
            "first_name": row.get("first_name"),
            "last_name": row.get("last_name"),
        })
        sqlite_entries.append({
            "id": row.get("entry_id"),
            "person_id": person_id,
            "age": row.get("age"),
            "event_date": row.get("event_date"),
            "event_place": row.get("event_place"),
            "source_excerpt": row.get("source_excerpt"),
        })
        place = row.get("event_place")
        if place:
            pkey = place.lower()
            place_id = place_ids.get(pkey)
            if not place_id:
                place_id = f"place_{len(place_ids)+1:04d}_{_bk_db_reg_slug(place, 'place')}"
                place_ids[pkey] = place_id
                places.append({"id": place_id, "name": place, "type": "event_place", "description": None})
            refs.append({"id": f"reference_{len(refs)+1}", "source_table": "persons", "source_id": person_id, "relation_type": "EVENT_PLACE", "target_table": "places", "target_id": place_id, "evidence": row.get("source_excerpt")})
        year = row.get("event_year")
        if year:
            ykey = str(year)
            year_id = year_ids.get(ykey)
            if not year_id:
                year_id = f"year_{ykey}"
                year_ids[ykey] = year_id
                years.append({"id": year_id, "year": year, "context": "event_date"})
            refs.append({"id": f"reference_{len(refs)+1}", "source_table": "persons", "source_id": person_id, "relation_type": "EVENT_YEAR", "target_table": "years", "target_id": year_id, "evidence": row.get("source_excerpt")})
    payload["persons"] = persons
    payload["places"] = places
    payload["years"] = years
    payload["references"] = refs
    payload["sqlite_export"] = {
        "target": "transcription_helper",
        "tables": {
            "documents": [{"id": 1, "source_path": None, "title": payload.get("document", {}).get("title") if isinstance(payload.get("document"), dict) else None}],
            "persons": sqlite_persons,
            "entries": sqlite_entries,
            "places": places,
            "years": years,
        },
    }
    norm = globals().get("_ptr_normalize_postgres_json")
    return norm(payload, source_text) if callable(norm) else payload
def _bk_db_neo4j_from_register_rows(source_text: str, rows: list) -> dict:
    pg = _bk_db_postgres_from_register_rows(source_text, rows)
    build_graph = globals().get("_bk_build_local_neo4j_json")
    if callable(build_graph):
        try:
            return build_graph(source_text)
        except Exception:
            pass
    nodes = [{"id": "document_1", "label": "Document", "type": "Document", "properties": {"raw_excerpt": str(source_text or "")[:1000] or None}}]
    rels = []
    for person in pg.get("persons") or []:
        pid = person.get("id")
        if not pid:
            continue
        nodes.append({"id": pid, "label": person.get("full_name"), "type": "Person", "properties": dict(person)})
        rels.append({"source": "document_1", "target": pid, "type": "MENTIONS", "properties": {}})
    for table, typ, label_key in (("places", "Place", "name"), ("years", "Year", "year")):
        for item in pg.get(table) or []:
            iid = item.get("id")
            if iid:
                nodes.append({"id": iid, "label": str(item.get(label_key) or iid), "type": typ, "properties": dict(item)})
    for ref in pg.get("references") or []:
        if ref.get("source_id") and ref.get("target_id"):
            rels.append({"source": ref.get("source_id"), "target": ref.get("target_id"), "type": ref.get("relation_type") or "RELATED_TO", "properties": {"evidence": ref.get("evidence")}})
    norm = globals().get("_bk_normalize_neo4j_json")
    return norm({"nodes": nodes, "relationships": rels}, source_text) if callable(norm) else {"nodes": nodes, "relationships": rels}
_BK_DB_PREV_PG_LOCAL = globals().get("_ptr_ai_build_postgres_json_local")
def _ptr_ai_build_postgres_json_local_db_register(source_text: str) -> dict:
    rows = _bk_db_regs_from_text(source_text)
    if _bk_db_text_looks_like_register(source_text, rows):
        return _bk_db_postgres_from_register_rows(source_text, rows)
    if callable(_BK_DB_PREV_PG_LOCAL):
        return _BK_DB_PREV_PG_LOCAL(source_text)
    return _bk_db_postgres_from_register_rows(source_text, rows)
_ptr_ai_build_postgres_json_local = _ptr_ai_build_postgres_json_local_db_register
_BK_DB_PREV_WORKER_BUILD_PG = getattr(BKLocalStructuredJsonWorker, "_build_postgres_json", None) if "BKLocalStructuredJsonWorker" in globals() else None
_BK_DB_PREV_WORKER_BUILD_NEO = getattr(BKLocalStructuredJsonWorker, "_build_neo4j_json", None) if "BKLocalStructuredJsonWorker" in globals() else None
def _bk_db_worker_build_postgres(self) -> dict:
    rows = _bk_db_regs_from_text(getattr(self, "source_text", ""))
    if _bk_db_text_looks_like_register(getattr(self, "source_text", ""), rows):
        try:
            self.status_changed.emit(self._tr("status_local_json_generating_fallback"))
        except Exception:
            pass
        return _bk_db_postgres_from_register_rows(getattr(self, "source_text", ""), rows)
    if callable(_BK_DB_PREV_WORKER_BUILD_PG):
        return _BK_DB_PREV_WORKER_BUILD_PG(self)
    return _bk_db_postgres_from_register_rows(getattr(self, "source_text", ""), rows)
def _bk_db_worker_build_neo4j(self) -> dict:
    rows = _bk_db_regs_from_text(getattr(self, "source_text", ""))
    if _bk_db_text_looks_like_register(getattr(self, "source_text", ""), rows):
        try:
            self.status_changed.emit(self._tr("status_local_json_generating_fallback"))
        except Exception:
            pass
        return _bk_db_neo4j_from_register_rows(getattr(self, "source_text", ""), rows)
    if callable(_BK_DB_PREV_WORKER_BUILD_NEO):
        return _BK_DB_PREV_WORKER_BUILD_NEO(self)
    return _bk_db_neo4j_from_register_rows(getattr(self, "source_text", ""), rows)
try:
    BKLocalStructuredJsonWorker._build_postgres_json = _bk_db_worker_build_postgres
    BKLocalStructuredJsonWorker._build_neo4j_json = _bk_db_worker_build_neo4j
except Exception:
    pass
_BK_DB_PREV_SQLITE_ROWS = globals().get("_bk_fix37_sqlite_rows_from_current_text")
def _bk_fix37_sqlite_rows_from_current_text_db_register(text: str) -> list:
    rows = _bk_db_regs_from_text(text)
    if _bk_db_text_looks_like_register(text, rows):
        return rows
    if callable(_BK_DB_PREV_SQLITE_ROWS):
        return _BK_DB_PREV_SQLITE_ROWS(text)
    return rows
_bk_fix37_sqlite_rows_from_current_text = _bk_fix37_sqlite_rows_from_current_text_db_register
_BK_DB_PREV_SQLITE_JSON_PAYLOAD = globals().get("_bk_sqlite_json_payload_from_rows")
__all__ = [
    '_BK_DB_PREV_PG_LOCAL',
    '_BK_DB_PREV_SQLITE_JSON_PAYLOAD',
    '_BK_DB_PREV_SQLITE_ROWS',
    '_BK_DB_PREV_WORKER_BUILD_NEO',
    '_BK_DB_PREV_WORKER_BUILD_PG',
    '_bk_db_neo4j_from_register_rows',
    '_bk_db_postgres_from_register_rows',
    '_bk_db_reg_clean',
    '_bk_db_reg_clean_place',
    '_bk_db_reg_slug',
    '_bk_db_reg_year_from_date',
    '_bk_db_regs_from_text',
    '_bk_db_text_looks_like_register',
    '_bk_db_worker_build_neo4j',
    '_bk_db_worker_build_postgres',
    '_bk_fix37_sqlite_rows_from_current_text',
    '_bk_fix37_sqlite_rows_from_current_text_db_register',
    '_ptr_ai_build_postgres_json_local',
    '_ptr_ai_build_postgres_json_local_db_register',
]
register_globals('bk', globals(), __all__)
