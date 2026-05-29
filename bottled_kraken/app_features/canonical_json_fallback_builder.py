from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
from bottled_kraken.common import _force_text
from bottled_kraken.common import (
    Any,
    Dict,
    List,
    Optional,
    re,
)
from bottled_kraken.main_window import MainWindow
from PySide6.QtGui import QPainterPath
from PySide6.QtWidgets import (
    QComboBox,
    QGraphicsEllipseItem,
    QGraphicsTextItem,
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsPathItem,
    QGraphicsLineItem,
    QGroupBox,
    QSlider,
    QCheckBox,
    QLineEdit,
)
def _bk_canonical_line_candidates(source_text: str) -> List[str]:
    lines = []
    for raw in _force_text(source_text).splitlines():
        line = _bk_clean_string(raw)
        if not line:
            continue
        low = line.lower()
        if low in {"-", "--", "—"}:
            continue
        if len(line) < 3:
            continue
        lines.append(line)
    return lines
def _bk_canonical_extract_years(line: str) -> List[str]:
    years = []
    for y in re.findall(r"\b(1[5-9]\d{2}|20\d{2})\b", line):
        if y not in years:
            years.append(y)
    return years
def _bk_canonical_extract_dates(line: str) -> List[str]:
    dates: List[str] = []
    for m in re.finditer(r"\b([0-3]?\d\.\s*(?:I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII)\.?\s*(?:1[5-9]\d{2}|20\d{2})?)\b", line, flags=re.IGNORECASE):
        cand = _bk_clean_string(m.group(1))
        if cand and cand not in dates:
            dates.append(cand)
    return dates[:3]
def _bk_canonical_extract_family_context(line: str) -> Optional[str]:
    m = re.search(r"\(([^)]{2,90})\)", _force_text(line))
    if not m:
        return None
    cand = _bk_clean_string(m.group(1))
    return cand or None
def _bk_canonical_extract_place_candidates(line: str) -> List[str]:
    places = []
    for m in re.finditer(r"(?:1[5-9]\d{2}|20\d{2})[.,;:\s]*([A-ZÄÖÜ][A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß\-.]{1,}(?:\s+[A-ZÄÖÜ][A-Za-zÄÖÜäöüß\-.]{2,}){0,2})", line):
        cand = _bk_clean_string(m.group(1))
        cand = re.sub(r"\b(Jahr|Jahre|Monat|Monate|Woche|Wochen|Tag|Tage|ann|geb|gest|den)\b.*$", "", cand, flags=re.IGNORECASE).strip()
        cand = cand.strip(" .,:;")
        if 2 <= len(cand) <= 60 and not re.match(r"^\d+$", cand) and cand not in places:
            places.append(cand)
    m = re.search(r"([A-ZÄÖÜ][A-Za-zÄÖÜäöüß\-.]{2,})(?:[.,;:\s]+(?:\d{1,4}|[IVXLC]+))?\s*$", line)
    if m:
        cand = _bk_clean_string(m.group(1))
        if cand and cand.lower() not in {"jahre", "jahr", "wochen", "woche", "monate", "monat", "tage", "tag"} and cand not in places:
            places.append(cand)
    return places[:3]
def _bk_canonical_extract_person_candidate(line: str) -> Optional[Dict[str, Any]]:
    if not line:
        return None
    low = line.lower()
    if "seite" in low and len(line) < 40:
        return None
    if low.startswith(("unter ", "oben ", "fortsetzung", "weiter", "register", "index")):
        return None
    part = re.split(r"\b\d{1,3}\s*(?:Jahr|Jahre|Monat|Monate|Woche|Wochen|Tag|Tage)\b|\b[0-3]?\d\.\s*(?:I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII)\.|\b1[5-9]\d{2}\b", line, maxsplit=1, flags=re.IGNORECASE)[0]
    part = re.split(r"[,;:]", part, maxsplit=1)[0]
    part = _bk_clean_string(part)
    part = re.sub(r"^[\d#\-\s.]+", "", part)
    part = re.sub(r"\s+", " ", part).strip()
    tokens = [t for t in re.split(r"\s+", part) if t]
    tokens = [t.strip(".,;:()[]{}") for t in tokens]
    tokens = [t for t in tokens if re.search(r"[A-Za-zÄÖÜäöüß]", t)]
    if len(tokens) < 2:
        return None
    tokens = tokens[:4]
    label = _bk_clean_string(" ".join(tokens))
    if len(label) < 5 or len(label) > 80:
        return None
    if not re.match(r"^[A-ZÄÖÜ]", label):
        return None
    last_name = tokens[0]
    first_name = " ".join(tokens[1:]) if len(tokens) > 1 else None
    return {
        "label": label,
        "first_name": first_name,
        "last_name": last_name,
    }
def _bk_build_canonical_json_fallback_from_text(source_text: str, reason: Any = None) -> Dict[str, Any]:
    source_text = _force_text(source_text or "")
    lines = _bk_canonical_line_candidates(source_text)
    entities = [{
        "id": "document_1",
        "type": "DOCUMENT",
        "label": "OCR document",
        "attributes": {"source_type": "ocr_text"},
        "evidence": None,
    }]
    relations = []
    entity_by_key = {("DOCUMENT", "ocr document"): "document_1"}
    def ensure_entity(entity_type: str, label: str, attributes: Optional[Dict[str, Any]] = None, evidence: Optional[str] = None) -> str:
        entity_type = _bk_normalize_entity_type(entity_type)
        label = _bk_clean_string(label)
        identity_probe = {
            "id": "",
            "type": entity_type,
            "label": label,
            "attributes": attributes or {},
            "evidence": evidence,
        }
        key = _bk_canonical_entity_identity_key(identity_probe, len(entities))
        if key in entity_by_key:
            ent_id = entity_by_key[key]
            for ent in entities:
                if ent.get("id") == ent_id:
                    ent["attributes"] = _bk_merge_attributes(ent.get("attributes", {}), attributes or {})
                    if evidence:
                        ent["evidence"] = _bk_merge_text(ent.get("evidence"), evidence)
                    break
            return ent_id
        base = _bk_normalize_id(f"{entity_type.lower()}_{label}", f"{entity_type.lower()}_{len(entities)+1}")
        used = {e.get("id") for e in entities}
        ent_id = base
        counter = 2
        while ent_id in used:
            ent_id = f"{base}_{counter}"
            counter += 1
        entity_by_key[key] = ent_id
        entities.append({
            "id": ent_id,
            "type": entity_type,
            "label": label,
            "attributes": attributes or {},
            "evidence": evidence,
        })
        return ent_id
    def add_relation(source: str, target: str, rel_type: str, strength: float, evidence: str):
        if not source or not target or source == target:
            return
        rel_type = _bk_normalize_relation_type(rel_type)
        rel_id = _bk_normalize_id(f"rel_{source}_{rel_type}_{target}", f"rel_{len(relations)+1}")
        key = (source, rel_type, target)
        for rel in relations:
            if (rel.get("source"), rel.get("type"), rel.get("target")) == key:
                attrs = rel.setdefault("attributes", {})
                try:
                    attrs["strength"] = max(float(attrs.get("strength", 0.0)), float(strength))
                except Exception:
                    attrs["strength"] = strength
                rel["evidence"] = _bk_merge_text(rel.get("evidence"), evidence)
                return
        relations.append({
            "id": rel_id,
            "source": source,
            "target": target,
            "type": rel_type,
            "attributes": {"strength": max(0.0, min(1.0, float(strength)))},
            "evidence": evidence[:300] if evidence else None,
        })
    for line_idx, line in enumerate(lines[:500], start=1):
        person = _bk_canonical_extract_person_candidate(line)
        years = _bk_canonical_extract_years(line)
        dates = _bk_canonical_extract_dates(line)
        places = _bk_canonical_extract_place_candidates(line)
        ages = re.findall(r"\b\d{1,3}\s*(?:Jahre?|Jahr|J\.|Monate?|Mon\.?|Wochen?|Woch\.?|Tage?|Years?|Months?|Weeks?|Days?)\b", line, flags=re.IGNORECASE)
        family_context = _bk_canonical_extract_family_context(line)
        person_id = None
        if person:
            attrs = {
                "first_name": person.get("first_name"),
                "last_name": person.get("last_name"),
                "line_index": line_idx,
            }
            if years:
                attrs["year"] = years[0]
            if dates:
                attrs["event_date"] = dates[0]
            if places:
                attrs["place"] = places[0]
            if ages:
                attrs["age"] = ages[0]
            if family_context:
                attrs["family_context"] = family_context
            person_id = ensure_entity("PERSON", person["label"], attrs, line)
            add_relation("document_1", person_id, "PART_OF", 0.35, line)
        year_ids = []
        for year in years[:3]:
            yid = ensure_entity("YEAR", year, {"year": year, "line_index": line_idx}, line)
            year_ids.append(yid)
            if person_id:
                add_relation(person_id, yid, "DURING", 0.75, line)
        place_ids = []
        for place in places[:3]:
            pid = ensure_entity("PLACE", place, {"place": place, "line_index": line_idx}, line)
            place_ids.append(pid)
            if person_id:
                add_relation(person_id, pid, "LOCATED_IN", 0.80, line)
        age_ids = []
        for age in ages[:2]:
            aid = ensure_entity("AGE", age, {"age": age, "line_index": line_idx}, line)
            age_ids.append(aid)
            if person_id:
                add_relation(person_id, aid, "HAS_AGE", 0.72, line)
        if not person_id:
            for pid in place_ids:
                add_relation("document_1", pid, "PART_OF", 0.25, line)
            for yid in year_ids:
                add_relation("document_1", yid, "PART_OF", 0.20, line)
            for aid in age_ids:
                add_relation("document_1", aid, "PART_OF", 0.20, line)
    fallback_reason = _bk_clean_string(reason)[:500] if reason else None
    data = {
        "document": {
            "id": "document_1",
            "title": None,
            "source_type": "ocr_text",
            "language": None,
        },
        "entities": entities,
        "relations": relations,
        "metadata": {
            "schema": "canonical_graph",
            "version": 1,
            "fallback_used": True,
            "fallback_reason": fallback_reason,
            "fallback_method": "local_line_heuristics",
        },
    }
    return _bk_prepare_canonical_json(data, source_text)
def _bk_build_canonical_json(self) -> Dict[str, Any]:
    system_prompt = str(getattr(self, "canonical_system_prompt", "") or "").strip() or (
        "You are a JSON-only extraction engine. You must output exactly one valid JSON object.\n"
        "The first character of your answer must be { and the last character must be }.\n"
        "No markdown, no prose, no explanation, no comments, no code fences.\n"
        "Extract only information supported by the OCR text. Use null for unknown values.\n"
    )
    schema_template = (
        '{'
        '"document":{"id":"document_1","title":null,"source_type":"ocr_text","language":null},'
        '"entities":['
        '{"id":"entity_1","type":"PERSON","label":"Example","attributes":{"first_name":null,"last_name":null,"place":null,"year":null,"age":null},"evidence":null}'
        '],'
        '"relations":['
        '{"id":"rel_1","source":"entity_1","target":"document_1","type":"PART_OF","attributes":{"strength":0.5},"evidence":null}'
        '],'
        '"metadata":{"schema":"canonical_graph","version":1}'
        '}'
    )
    default_user_prompt = (
        "Return only one JSON object matching this structure exactly. Do not repeat these instructions.\n\n"
        "Allowed entity types: PERSON, PLACE, STREET, YEAR, ORGANIZATION, EVENT, DOCUMENT, ENTITY.\n"
        "Allowed relation types: RELATED_TO, LOCATED_IN, DURING, PART_OF, PARTICIPATED_IN, ASSOCIATED_WITH.\n"
        "Relation strength must be a number from 0.0 to 1.0.\n"
        "Use arrays even when empty. If nothing is extractable, return empty entities and relations arrays.\n"
        "The output must be parseable by json.loads.\n\n"
        "Required JSON skeleton:\n"
        f"{schema_template}\n\n"
        "OCR_TEXT_START\n"
        + _force_text(self.source_text or "")[:60000] +
        "\nOCR_TEXT_END"
    )
    template = str(getattr(self, "canonical_user_prompt", "") or "").strip()
    if template:
        try:
            user_prompt = template.format(schema_template=schema_template, ocr_text=_force_text(self.source_text or "")[:60000])
        except Exception:
            user_prompt = template + "\n\nOCR_TEXT_START\n" + _force_text(self.source_text or "")[:60000] + "\nOCR_TEXT_END"
    else:
        user_prompt = default_user_prompt
    last_error = None
    try:
        data = self._request_json_object(system_prompt, user_prompt)
        return _bk_prepare_canonical_json(data, self.source_text)
    except Exception as exc:
        last_error = exc
    retry_prompt = (
        "Return JSON only. No prose. Start with { and end with }.\n"
        "Create a canonical_graph JSON object with document, entities, relations, metadata.\n"
        "Use PERSON, PLACE, YEAR and PART_OF/LOCATED_IN/DURING relations when supported.\n"
        "OCR text follows:\n"
        + _force_text(self.source_text or "")[:18000]
    )
    try:
        data = self._request_json_object(system_prompt, retry_prompt)
        canonical = _bk_prepare_canonical_json(data, self.source_text)
        canonical.setdefault("metadata", {})["lm_retry_used"] = True
        return canonical
    except Exception as exc:
        last_error = exc
    return _bk_build_canonical_json_fallback_from_text(self.source_text, reason=last_error)
__all__ = [
    '_bk_build_canonical_json',
    '_bk_build_canonical_json_fallback_from_text',
    '_bk_canonical_extract_dates',
    '_bk_canonical_extract_family_context',
    '_bk_canonical_extract_person_candidate',
    '_bk_canonical_extract_place_candidates',
    '_bk_canonical_extract_years',
    '_bk_canonical_line_candidates',
]
register_globals('bk', globals(), __all__)
