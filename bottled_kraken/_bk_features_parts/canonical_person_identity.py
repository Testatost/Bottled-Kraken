"""Personen-Identitätslogik für Canonical JSON.

Gleichnamige Personen in historischen Registerseiten werden nicht mehr nur nach
Name dedupliziert. Alter, Datum, Jahr, Ort, Eltern-/Familienkontext und
Zeilen-/Belegkontext bilden eine separate Identität.
"""

from .shared import *

def _bk_first_scalar(value: Any) -> str:
    """Return a compact scalar value from flat/list/dict attributes for identity checks."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        for item in value:
            got = _bk_first_scalar(item)
            if got:
                return got
        return ""
    if isinstance(value, dict):
        for key in ("label", "name", "value", "text", "id"):
            got = _bk_first_scalar(value.get(key))
            if got:
                return got
        for item in value.values():
            got = _bk_first_scalar(item)
            if got:
                return got
        return ""
    return _bk_clean_string(value)

_BK_PERSON_CONTEXT_ATTR_KEYS = (
    "line_index", "line", "row", "row_index", "record_index", "record_no", "record_number",
    "age", "alter", "birth_date", "birthdate", "geburtsdatum", "birthday", "date_of_birth",
    "event_date", "date", "datum", "death_date", "deathdate", "year", "jahr",
    "place", "ort", "location", "located_in", "residence", "origin",
    "father", "vater", "mother", "mutter", "parent", "parents", "spouse", "ehepartner",
    "husband", "wife", "context", "family_context", "person_instance", "identity_key",
)

_BK_PERSON_GENERIC_ID_RE = re.compile(r"^(?:person|personen|entity|entitaet|entität|name|human)(?:_?\d+)?$", re.IGNORECASE)

def _bk_context_fragment(prefix: str, value: Any) -> str:
    text = _bk_first_scalar(value)
    if not text:
        return ""
    key = _bk_canonical_match_key(text)
    if not key:
        return ""
    return f"{prefix}:{key[:80]}"

def _bk_extract_person_context_from_evidence(evidence: Any) -> List[str]:
    text = _bk_clean_string(evidence)
    if not text:
        return []
    parts: List[str] = []
    # Age is a strong discriminator in historical registers.
    m = re.search(r"\b(\d{1,3})\s*(Jahre?|Jahr|J\.|Monate?|Mon\.?|Wochen?|Woch\.?|Tage?|Tag|Years?|Months?|Weeks?|Days?)\b", text, flags=re.IGNORECASE)
    if m:
        parts.append(_bk_context_fragment("age", " ".join(m.groups())))
    # Numeric/roman dates such as 21.V.1765 or 21. V. 1765 often represent birth/death/event dates.
    m = re.search(r"\b([0-3]?\d\.\s*(?:I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII)\.?\s*(?:1[5-9]\d{2}|20\d{2})?)\b", text, flags=re.IGNORECASE)
    if m:
        parts.append(_bk_context_fragment("date", m.group(1)))
    m = re.search(r"\b(1[5-9]\d{2}|20\d{2})\b", text)
    if m:
        parts.append(_bk_context_fragment("year", m.group(1)))
    # Parent/spouse notes in parentheses, e.g. (S.d.Andreas), are useful for names repeated on the same page.
    m = re.search(r"\(([^)]{2,90})\)", text)
    if m:
        parts.append(_bk_context_fragment("ctx", m.group(1)))
    # A final place/page fragment helps separate same names when age/date are missing.
    m = re.search(r"(?:1[5-9]\d{2}|20\d{2})[.,;:\s]*([A-ZÄÖÜ][A-Za-zÄÖÜäöüß.-]{2,}(?:\s+[A-ZÄÖÜ][A-Za-zÄÖÜäöüß.-]{2,}){0,2})", text)
    if m:
        parts.append(_bk_context_fragment("place", m.group(1)))
    return [p for p in parts if p]

def _bk_person_identity_parts(entity: Dict[str, Any], index: int = 0) -> List[str]:
    attrs = entity.get("attributes") if isinstance(entity.get("attributes"), dict) else {}
    parts: List[str] = []
    for key in _BK_PERSON_CONTEXT_ATTR_KEYS:
        if key in attrs:
            frag = _bk_context_fragment(key, attrs.get(key))
            if frag and frag not in parts:
                parts.append(frag)
    for frag in _bk_extract_person_context_from_evidence(entity.get("evidence")):
        if frag and frag not in parts:
            parts.append(frag)
    if parts:
        return parts

    # If a model explicitly created different person IDs with the same label, keep them separate.
    raw_id = _bk_normalize_id(entity.get("id"), "")
    label_id = _bk_normalize_id(entity.get("label"), "")
    if raw_id and raw_id != label_id and not _BK_PERSON_GENERIC_ID_RE.match(raw_id):
        return [f"id:{raw_id}"]

    evidence_key = _bk_canonical_match_key(entity.get("evidence"))
    if evidence_key:
        return [f"evidence:{evidence_key[:120]}"]
    return [f"instance:{index + 1}"]

def _bk_canonical_entity_identity_key(entity: Dict[str, Any], index: int = 0) -> Tuple[str, ...]:
    typ = _bk_normalize_entity_type(entity.get("type"))
    label_key = _bk_canonical_match_key(entity.get("label") or entity.get("id"), typ) or _bk_normalize_id(entity.get("id"), "entity")
    if typ != "PERSON":
        return (typ, label_key)
    parts = _bk_person_identity_parts(entity, index)
    return (typ, label_key, "|".join(parts))
