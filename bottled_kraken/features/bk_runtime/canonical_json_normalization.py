"""Canonical-JSON- und Graph-Ansicht für lokale LM-Workflows.

Diese Erweiterung integriert den Canonical-JSON/Graph-View-Ansatz aus dem
Kraken-OCR-Tool in Bottled Kraken, ohne externe Graph-Datenbank vorauszusetzen.
"""

from .shared import *

from .ui_components import *
from .workers import *
from .dialogs import *
from .image_edit import *
from .main_window import MainWindow
from .ptr_features import *

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

_BK_CANONICAL_SCHEMA_KIND = "canonical"

_ENTITY_TYPE_ALIASES = {
    "PERSONEN": "PERSON", "PERSON_NAME": "PERSON", "NAME": "PERSON", "HUMAN": "PERSON",
    "ORT": "PLACE", "ORTSNAME": "PLACE", "LOCATION": "PLACE", "LOC": "PLACE",
    "CITY": "PLACE", "TOWN": "PLACE", "VILLAGE": "PLACE",
    "STRASSE": "STREET", "STRAßE": "STREET", "ROAD": "STREET", "STREET_NAME": "STREET",
    "JAHR": "YEAR", "DATE": "YEAR", "YEAR_VALUE": "YEAR",
    "ALTER": "AGE", "AGE_VALUE": "AGE", "YEARS_OLD": "AGE", "AGE": "AGE",
    "ORG": "ORGANIZATION", "ORGANISATION": "ORGANIZATION", "INSTITUTION": "ORGANIZATION",
    "DOC": "DOCUMENT", "SOURCE": "DOCUMENT", "EREIGNIS": "EVENT", "EVENT": "EVENT",
}

_RELATION_TYPE_ALIASES = {
    "RELATED": "RELATED_TO", "RELATES_TO": "RELATED_TO", "ASSOCIATED": "ASSOCIATED_WITH",
    "IN": "LOCATED_IN", "AT": "LOCATED_IN", "LOCATED_AT": "LOCATED_IN",
    "DURING_YEAR": "DURING", "YEAR_OF": "DURING",
    "PARTOF": "PART_OF", "BELONGS_TO": "PART_OF",
    "PARTICIPATED": "PARTICIPATED_IN", "PARTICIPANT_OF": "PARTICIPATED_IN",
}

def _bk_clean_string(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\x00", " ").strip()
    text = re.sub(r"\s+", " ", text)
    return text.strip(" \t\n\r.,;:!?()[]{}<>\"'`´“”„’")

def _bk_clean_key(value: Any) -> str:
    key = _bk_clean_string(value).lower()
    key = key.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    key = re.sub(r"[^a-z0-9_]+", "_", key)
    key = re.sub(r"_+", "_", key).strip("_")
    return key

def _bk_normalize_id(value: Any, fallback: str = "entity") -> str:
    raw = _bk_clean_string(value)
    if not raw:
        raw = fallback
    raw = raw.lower()
    raw = raw.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    raw = re.sub(r"[^a-z0-9_]+", "_", raw)
    raw = re.sub(r"_+", "_", raw).strip("_")
    if not raw:
        raw = fallback
    if raw and raw[0].isdigit():
        raw = f"id_{raw}"
    return raw

def _bk_canonical_match_key(label: Any, entity_type: Any = "") -> str:
    text = _bk_clean_string(label).lower()
    text = text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    text = re.sub(r"\b(stadt|dorf|gemeinde|herr|frau|mr|mrs|miss)\b", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def _bk_normalize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = _bk_clean_string(value)
        return cleaned if cleaned else None
    if isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, list):
        out = []
        for item in value:
            normalized = _bk_normalize_value(item)
            if normalized is not None:
                out.append(normalized)
        return out if out else None
    if isinstance(value, dict):
        out = {}
        for key, val in value.items():
            k = _bk_clean_key(key)
            normalized = _bk_normalize_value(val)
            if k and normalized is not None:
                out[k] = normalized
        return out if out else None
    return _bk_clean_string(value) or None

def _bk_normalize_mapping(data: Any) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    out = {}
    for key, val in data.items():
        k = _bk_clean_key(key)
        normalized = _bk_normalize_value(val)
        if k and normalized is not None:
            out[k] = normalized
    return out

def _bk_normalize_entity_type(value: Any) -> str:
    text = _bk_clean_string(value or "ENTITY").upper().replace(" ", "_")
    text = _ENTITY_TYPE_ALIASES.get(text, text)
    text = re.sub(r"[^A-Z0-9_]+", "_", text).strip("_") or "ENTITY"
    return text

def _bk_normalize_relation_type(value: Any) -> str:
    text = _bk_clean_string(value or "RELATED_TO").upper().replace(" ", "_")
    text = _RELATION_TYPE_ALIASES.get(text, text)
    text = re.sub(r"[^A-Z0-9_]+", "_", text).strip("_") or "RELATED_TO"
    return text

def _bk_extract_strength(attributes: Any) -> float:
    attrs = attributes if isinstance(attributes, dict) else {}
    for key in ("strength", "confidence", "weight", "score", "probability", "staerke", "stärke"):
        val = attrs.get(key)
        try:
            f = float(val)
            if f > 1.0:
                f = f / 100.0 if f <= 100.0 else 1.0
            return max(0.0, min(1.0, f))
        except Exception:
            continue
    return 1.0

def _bk_canonical_from_graph_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    raw_nodes = data.get("nodes") if isinstance(data, dict) else []
    raw_rels = data.get("relationships") if isinstance(data, dict) else []
    if not isinstance(raw_nodes, list):
        raw_nodes = []
    if not isinstance(raw_rels, list):
        raw_rels = []
    entities = []
    for idx, node in enumerate(raw_nodes, start=1):
        if not isinstance(node, dict):
            continue
        props = node.get("properties") if isinstance(node.get("properties"), dict) else {}
        label = node.get("label") or props.get("label") or node.get("name") or f"Entity {idx}"
        typ = node.get("type") or props.get("entity_type") or node.get("labels") or "ENTITY"
        if isinstance(typ, list):
            typ = next((x for x in typ if x not in ("CanonicalEntity", "Entity")), "ENTITY")
        entities.append({
            "id": node.get("id") or props.get("canonical_id") or f"entity_{idx}",
            "type": typ,
            "label": label,
            "attributes": props,
            "evidence": node.get("evidence") or props.get("evidence"),
        })
    relations = []
    for idx, rel in enumerate(raw_rels, start=1):
        if not isinstance(rel, dict):
            continue
        props = rel.get("properties") if isinstance(rel.get("properties"), dict) else {}
        relations.append({
            "id": rel.get("id") or props.get("canonical_id") or f"rel_{idx}",
            "source": rel.get("source") or rel.get("from"),
            "target": rel.get("target") or rel.get("to"),
            "type": rel.get("type") or "RELATED_TO",
            "attributes": props,
            "evidence": rel.get("evidence") or props.get("evidence"),
        })
    return {"document": data.get("document", {}) if isinstance(data, dict) else {}, "entities": entities, "relations": relations, "metadata": data.get("metadata", {}) if isinstance(data, dict) else {}}

def _bk_normalize_entity(entity: Any, index: int) -> Dict[str, Any]:
    if not isinstance(entity, dict):
        return {}
    attrs = entity.get("attributes") if isinstance(entity.get("attributes"), dict) else {}
    # Accept flat AI outputs too.
    for key, val in entity.items():
        if key not in {"id", "type", "label", "attributes", "evidence", "description"} and key not in attrs:
            attrs[key] = val
    typ = _bk_normalize_entity_type(entity.get("type") or attrs.get("type") or "ENTITY")
    label = _bk_clean_string(entity.get("label") or attrs.get("label") or attrs.get("name") or entity.get("name") or entity.get("id") or f"Entity {index + 1}")
    if not label:
        return {}
    ent_id = _bk_normalize_id(entity.get("id") or f"{typ.lower()}_{label}", f"entity_{index + 1}")
    out = {"id": ent_id, "type": typ, "label": label, "attributes": _bk_normalize_mapping(attrs)}
    evidence = _bk_clean_string(entity.get("evidence"))
    if evidence:
        out["evidence"] = evidence
    description = _bk_clean_string(entity.get("description"))
    if description:
        out["description"] = description
    return out

def _bk_normalize_relation(relation: Any, index: int) -> Dict[str, Any]:
    if not isinstance(relation, dict):
        return {}
    attrs = relation.get("attributes") if isinstance(relation.get("attributes"), dict) else {}
    for key, val in relation.items():
        if key not in {"id", "source", "target", "from", "to", "type", "attributes", "evidence", "description"} and key not in attrs:
            attrs[key] = val
    source = _bk_normalize_id(relation.get("source") or relation.get("from"), "")
    target = _bk_normalize_id(relation.get("target") or relation.get("to"), "")
    typ = _bk_normalize_relation_type(relation.get("type") or "RELATED_TO")
    rel_id = _bk_normalize_id(relation.get("id") or f"rel_{source}_{typ}_{target}", f"rel_{index + 1}")
    out = {"id": rel_id, "source": source, "target": target, "type": typ, "attributes": _bk_normalize_mapping(attrs)}
    evidence = _bk_clean_string(relation.get("evidence"))
    if evidence:
        out["evidence"] = evidence
    description = _bk_clean_string(relation.get("description"))
    if description:
        out["description"] = description
    return out

def _bk_merge_text(left: Any, right: Any) -> str:
    a = _bk_clean_string(left)
    b = _bk_clean_string(right)
    if not a:
        return b
    if not b or b == a:
        return a
    return f"{a} | {b}"

def _bk_merge_attributes(left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(left or {})
    for key, val in (right or {}).items():
        if key not in out or out.get(key) in (None, "", [], {}):
            out[key] = val
        elif out.get(key) != val:
            if isinstance(out.get(key), list):
                if val not in out[key]:
                    out[key].append(val)
            else:
                out[key] = [out[key], val] if val != out[key] else out[key]
    return out

_BK_CANONICAL_NOISE_LABELS = {
    "", "-", "--", "—", "_", "seite", "page", "unter", "oben", "weiter", "weitersuchen",
    "fortsetzung", "index", "register", "ocr", "document", "dokument", "unknown", "unbekannt",
    "jahr", "jahre", "monat", "monate", "woche", "wochen", "tag", "tage",
}

def _bk_entity_is_meaningful(entity: Dict[str, Any]) -> bool:
    if not isinstance(entity, dict):
        return False
    typ = _bk_normalize_entity_type(entity.get("type"))
    label = _bk_clean_string(entity.get("label") or entity.get("id") or "")
    label_key = _bk_canonical_match_key(label, typ)
    if typ == "DOCUMENT":
        return True
    if typ == "YEAR":
        return bool(re.search(r"\b(1[5-9]\d{2}|20\d{2})\b", label + " " + str(entity.get("attributes") or "")))
    if not label or label.lower() in _BK_CANONICAL_NOISE_LABELS or label_key in _BK_CANONICAL_NOISE_LABELS:
        return False
    if len(label_key) < 2:
        return False
    if re.fullmatch(r"[ivxlcdm]+", label_key, flags=re.IGNORECASE):
        return False
    if re.fullmatch(r"\d+", label_key):
        return False
    if typ == "PERSON":
        # Person entities should contain at least one plausible letter pair, not only OCR punctuation or date fragments.
        if not re.search(r"[A-Za-zÄÖÜäöüß]{2,}", label):
            return False
        if len(label.split()) == 1 and len(label) <= 3:
            return False
    if typ == "PLACE":
        if label.lower() in {"jahre", "jahr", "wochen", "woche", "monate", "monat", "tage", "tag"}:
            return False
    return True

def _bk_sanity_check_canonical_json(canonical: Dict[str, Any]) -> Dict[str, Any]:
    """Filter obvious OCR/LM noise before graph display and JSON saving.

    The check is deliberately conservative: it removes empty/noise nodes,
    invalid dangling edges, self loops, very weak edges and excessive document
    hub edges that otherwise create unreadable star graphs.
    """
    if not isinstance(canonical, dict):
        canonical = {}
    entities_in = canonical.get("entities") if isinstance(canonical.get("entities"), list) else []
    relations_in = canonical.get("relations") if isinstance(canonical.get("relations"), list) else []

    entities = []
    seen = set()
    for ent in entities_in:
        if not isinstance(ent, dict):
            continue
        ent = dict(ent)
        ent["type"] = _bk_normalize_entity_type(ent.get("type"))
        ent["label"] = _bk_clean_string(ent.get("label") or ent.get("id") or "")
        if not _bk_entity_is_meaningful(ent):
            continue
        key = _bk_canonical_entity_identity_key(ent, len(entities))
        if key in seen:
            continue
        seen.add(key)
        entities.append(ent)

    valid_ids = {str(e.get("id")) for e in entities if e.get("id")}
    doc_ids = {str(e.get("id")) for e in entities if str(e.get("type") or "").upper() == "DOCUMENT"}

    relations = []
    seen_rel = set()
    weak_doc_hub = []
    for rel in relations_in:
        if not isinstance(rel, dict):
            continue
        rel = dict(rel)
        src = str(rel.get("source") or "")
        tgt = str(rel.get("target") or "")
        if not src or not tgt or src == tgt:
            continue
        if src not in valid_ids or tgt not in valid_ids:
            continue
        rel_type = _bk_normalize_relation_type(rel.get("type"))
        attrs = rel.get("attributes") if isinstance(rel.get("attributes"), dict) else {}
        strength = _bk_extract_strength(attrs)
        if strength < 0.10:
            continue
        key = (src, rel_type, tgt)
        if key in seen_rel:
            continue
        seen_rel.add(key)
        attrs = dict(attrs)
        attrs["strength"] = strength
        rel["type"] = rel_type
        rel["attributes"] = attrs
        if (src in doc_ids or tgt in doc_ids) and rel_type in {"PART_OF", "RELATED_TO"} and strength <= 0.35:
            weak_doc_hub.append(rel)
        else:
            relations.append(rel)

    # Star-shaped document->everything fallback edges are useful as metadata,
    # but unreadable in a graph. Keep them only when they are not excessive.
    if len(weak_doc_hub) <= 60:
        relations.extend(weak_doc_hub)

    metadata = canonical.get("metadata") if isinstance(canonical.get("metadata"), dict) else {}
    metadata = dict(metadata)
    metadata["sanity_check"] = {
        "enabled": True,
        "person_identity_split": True,
        "entities_before": len(entities_in),
        "entities_after": len(entities),
        "relations_before": len(relations_in),
        "relations_after": len(relations),
        "weak_document_edges_removed": max(0, len(weak_doc_hub) - (len(weak_doc_hub) if len(weak_doc_hub) <= 60 else 0)),
    }

    return {
        "document": canonical.get("document") if isinstance(canonical.get("document"), dict) else {},
        "entities": entities,
        "relations": relations,
        "metadata": metadata,
    }

def _bk_prepare_canonical_json(data: Dict[str, Any], source_text: str = "") -> Dict[str, Any]:
    if not isinstance(data, dict):
        data = {}
    if isinstance(data.get("canonical_json"), dict):
        data = data["canonical_json"]
    if isinstance(data.get("nodes"), list) and not isinstance(data.get("entities"), list):
        data = _bk_canonical_from_graph_payload(data)

    raw_entities = data.get("entities") if isinstance(data.get("entities"), list) else []
    raw_relations = data.get("relations") if isinstance(data.get("relations"), list) else []
    if not raw_relations and isinstance(data.get("relationships"), list):
        raw_relations = data.get("relationships")

    before_entities = len(raw_entities)
    before_relations = len(raw_relations)

    entities_by_key: Dict[Tuple[str, ...], Dict[str, Any]] = {}
    key_order: List[Tuple[str, ...]] = []
    id_map: Dict[str, str] = {}
    used_ids = set()
    for idx, raw in enumerate(raw_entities):
        ent = _bk_normalize_entity(raw, idx)
        if not ent:
            continue
        old_id = _bk_normalize_id(raw.get("id") if isinstance(raw, dict) else ent.get("id"), ent["id"])
        key = _bk_canonical_entity_identity_key(ent, idx)
        if key not in entities_by_key:
            base_id = ent["id"]
            cand = base_id
            counter = 2
            while cand in used_ids:
                cand = f"{base_id}_{counter}"
                counter += 1
            ent["id"] = cand
            used_ids.add(cand)
            entities_by_key[key] = ent
            key_order.append(key)
        else:
            base = entities_by_key[key]
            base["attributes"] = _bk_merge_attributes(base.get("attributes", {}), ent.get("attributes", {}))
            if ent.get("evidence"):
                base["evidence"] = _bk_merge_text(base.get("evidence"), ent.get("evidence"))
            if ent.get("description"):
                base["description"] = _bk_merge_text(base.get("description"), ent.get("description"))
        if old_id:
            id_map[old_id] = entities_by_key[key]["id"]

    entities = [entities_by_key[k] for k in key_order]
    entity_ids = {e["id"] for e in entities}

    relations_by_key: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    relation_order: List[Tuple[str, str, str]] = []
    used_rel_ids = set()
    for idx, raw in enumerate(raw_relations):
        rel = _bk_normalize_relation(raw, idx)
        if not rel:
            continue
        rel["source"] = id_map.get(rel["source"], rel["source"])
        rel["target"] = id_map.get(rel["target"], rel["target"])
        if not rel["source"] or not rel["target"] or rel["source"] == rel["target"]:
            continue
        if rel["source"] not in entity_ids or rel["target"] not in entity_ids:
            continue
        attrs = rel.get("attributes", {})
        attrs["strength"] = _bk_extract_strength(attrs)
        rel["attributes"] = attrs
        key = (rel["source"], rel["type"], rel["target"])
        if key not in relations_by_key:
            base_id = rel["id"]
            cand = base_id
            counter = 2
            while cand in used_rel_ids:
                cand = f"{base_id}_{counter}"
                counter += 1
            rel["id"] = cand
            used_rel_ids.add(cand)
            relations_by_key[key] = rel
            relation_order.append(key)
        else:
            base = relations_by_key[key]
            base["attributes"] = _bk_merge_attributes(base.get("attributes", {}), rel.get("attributes", {}))
            try:
                base["attributes"]["strength"] = max(float(base["attributes"].get("strength", 0.0)), float(rel["attributes"].get("strength", 0.0)))
            except Exception:
                base["attributes"]["strength"] = _bk_extract_strength(base.get("attributes", {}))
            if rel.get("evidence"):
                base["evidence"] = _bk_merge_text(base.get("evidence"), rel.get("evidence"))

    metadata = _bk_normalize_mapping(data.get("metadata", {}))
    metadata["canonical_pipeline"] = {
        "version": 2,
        "entity_count_before": before_entities,
        "entity_count_after": len(entities),
        "relation_count_before": before_relations,
        "relation_count_after": len(relations_by_key),
        "deduplicated": True,
        "person_identity_split": True,
    }
    if source_text:
        metadata.setdefault("source_excerpt", source_text[:500])

    canonical = {
        "document": _bk_normalize_mapping(data.get("document", {})),
        "entities": entities,
        "relations": [relations_by_key[k] for k in relation_order],
        "metadata": metadata,
    }
    return _bk_sanity_check_canonical_json(canonical)
