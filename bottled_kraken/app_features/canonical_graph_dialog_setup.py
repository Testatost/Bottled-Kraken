from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
from bottled_kraken.common import (
    Any,
    Dict,
    List,
    QGraphicsScene,
    QTimer,
    Qt,
    Tuple,
    re,
    translation,
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
class BKCanonicalGraphDialogSetupMixin:
        def __init__(self, parent, tr_func, canonical_data: Dict[str, Any], task_path: str = ""):
            super().__init__(parent)
            self._tr = tr_func or translation.make_tr(translation.DEFAULT_LANGUAGE)
            self.canonical = _bk_prepare_canonical_json(canonical_data if isinstance(canonical_data, dict) else {})
            self.task_path = task_path or "canonical.json"
            self.nodes: List[Dict[str, Any]] = []
            self.edges: List[Dict[str, Any]] = []
            self.node_by_id: Dict[str, Dict[str, Any]] = {}
            self.graph_node_items: Dict[str, Any] = {}
            self.graph_edge_refs: List[Dict[str, Any]] = []
            self.graph_cluster_refs: Dict[str, Dict[str, Any]] = {}
            self._graph_cluster_node_ids: Dict[str, List[str]] = {}
            self._graph_cluster_manual_offsets: Dict[str, Tuple[float, float]] = {}
            self._selected_graph_node_id = ""
            self._graph_filter_text = ""
            self._graph_show_arrows = True
            self._graph_show_labels = False
            self._graph_node_scale = 100
            self._graph_edge_scale = 100
            self._graph_link_distance = 120
            self._graph_center_force = 18
            self._graph_repel_force = 5200
            self._graph_link_force = 20
            self._graph_render_pending_fit = False
            self._graph_render_timer = QTimer(self)
            self._graph_render_timer.setSingleShot(True)
            self._graph_render_timer.timeout.connect(self._perform_scheduled_graph_render)
            self.scene = QGraphicsScene(self)
            self._normalize_for_view()
            self.setWindowTitle(self._tr("dlg_canonical_graph_title"))
            self.resize(1280, 820)
            try:
                self.setMinimumSize(1100, 760)
                self.setWindowState(self.windowState() | Qt.WindowMaximized)
            except Exception:
                pass
            self._build_ui()
            self._populate_tables()
            self._schedule_graph_render(fit=True, delay_ms=1)
            QTimer.singleShot(0, self._fit_graph)
            QTimer.singleShot(0, self.showMaximized)
        def showEvent(self, event):
            try:
                super().showEvent(event)
            except Exception:
                pass
            try:
                if not getattr(self, "_bk_initial_maximize_done", False):
                    self._bk_initial_maximize_done = True
                    self.setWindowState(self.windowState() | Qt.WindowMaximized)
                    QTimer.singleShot(0, self.showMaximized)
                    QTimer.singleShot(80, self.showMaximized)
                    QTimer.singleShot(120, self._fit_graph)
            except Exception:
                pass

        def _tr2(self, key: str, *args) -> str:
            return self._tr(key, *args)
        def _node_attr(self, node: Dict[str, Any], *keys: str) -> str:
            attrs = node.get("attributes") if isinstance(node.get("attributes"), dict) else {}
            for key in keys:
                val = attrs.get(key)
                if val not in (None, "", [], {}):
                    if isinstance(val, list):
                        return ", ".join(str(v) for v in val if v not in (None, ""))
                    return str(val)
            return ""
        def _infer_first_last(self, label: str, attrs: Dict[str, Any]) -> Tuple[str, str]:
            first = attrs.get("first_name") or attrs.get("vorname") or attrs.get("given_name") or ""
            last = attrs.get("last_name") or attrs.get("nachname") or attrs.get("surname") or attrs.get("family_name") or ""
            if (not first or not last) and label:
                parts = label.replace(",", " ").split()
                if len(parts) >= 2:
                    first = first or parts[0]
                    last = last or parts[-1]
            return str(first or ""), str(last or "")
        def _infer_year(self, node: Dict[str, Any]) -> str:
            attrs = node.get("attributes") if isinstance(node.get("attributes"), dict) else {}
            for key in ("year", "jahr", "date", "datum"):
                if attrs.get(key) not in (None, "", [], {}):
                    return str(attrs.get(key))
            text = " ".join([str(node.get("label") or ""), str(attrs)])
            m = re.search(r"\b(1[5-9]\d{2}|20\d{2})\b", text)
            return m.group(1) if m else ""
        def _infer_age(self, node: Dict[str, Any]) -> str:
            attrs = node.get("attributes") if isinstance(node.get("attributes"), dict) else {}
            for key in ("age", "alter", "age_years", "years_old", "jahr_alt", "jahre", "months_old", "tage", "days_old"):
                if attrs.get(key) not in (None, "", [], {}):
                    return str(attrs.get(key))
            text = " ".join([str(node.get("label") or ""), str(attrs), str(node.get("evidence") or "")])
            m = re.search(r"\b(\d{1,3})\s*(?:jahre?|jahr|j\.|years?|yrs?)\b", text, flags=re.IGNORECASE)
            if m:
                return f"{m.group(1)} Jahre"
            m = re.search(r"\b(\d{1,2})\s*(?:monate?|mon\.?|months?)\b", text, flags=re.IGNORECASE)
            if m:
                return f"{m.group(1)} Monate"
            m = re.search(r"\b(\d{1,2})\s*(?:tage?|days?)\b", text, flags=re.IGNORECASE)
            if m:
                return f"{m.group(1)} Tage"
            if str(node.get("type") or "").upper() == "AGE":
                return str(node.get("label") or "")
            return ""
        def _infer_place(self, node: Dict[str, Any]) -> str:
            attrs = node.get("attributes") if isinstance(node.get("attributes"), dict) else {}
            for key in ("place", "ort", "location", "place_name", "city", "village"):
                if attrs.get(key) not in (None, "", [], {}):
                    return str(attrs.get(key))
            if str(node.get("type") or "").upper() == "PLACE":
                return str(node.get("label") or "")
            return ""
        def _normalize_for_view(self):
            entities = self.canonical.get("entities") if isinstance(self.canonical.get("entities"), list) else []
            relations = self.canonical.get("relations") if isinstance(self.canonical.get("relations"), list) else []
            degree = {}
            for rel in relations:
                if not isinstance(rel, dict):
                    continue
                degree[str(rel.get("source") or "")] = degree.get(str(rel.get("source") or ""), 0) + 1
                degree[str(rel.get("target") or "")] = degree.get(str(rel.get("target") or ""), 0) + 1
            self.nodes = []
            for ent in entities:
                if not isinstance(ent, dict):
                    continue
                node_id = str(ent.get("id") or "").strip()
                if not node_id:
                    continue
                attrs = ent.get("attributes") if isinstance(ent.get("attributes"), dict) else {}
                label = str(ent.get("label") or node_id)
                first, last = self._infer_first_last(label, attrs)
                node_type = str(ent.get("type") or "ENTITY").upper()
                if node_type == "DOCUMENT":
                    continue
                node = {
                    "id": node_id,
                    "type": node_type,
                    "label": label,
                    "first_name": first,
                    "last_name": last,
                    "place": self._infer_place(ent),
                    "year": self._infer_year(ent),
                    "age": self._infer_age(ent),
                    "related_places": [],
                    "related_years": [],
                    "related_ages": [],
                    "degree": int(degree.get(node_id, 0)),
                    "attributes": attrs,
                    "raw": ent,
                }
                self.nodes.append(node)
            self.node_by_id = {n["id"]: n for n in self.nodes}
            self.edges = []
            for rel in relations:
                if not isinstance(rel, dict):
                    continue
                source = str(rel.get("source") or "")
                target = str(rel.get("target") or "")
                if source not in self.node_by_id or target not in self.node_by_id:
                    continue
                attrs = rel.get("attributes") if isinstance(rel.get("attributes"), dict) else {}
                self.edges.append({
                    "id": str(rel.get("id") or f"{source}_{target}"),
                    "source": source,
                    "target": target,
                    "type": str(rel.get("type") or "RELATED_TO"),
                    "strength": _bk_extract_strength(attrs),
                    "evidence": str(rel.get("evidence") or attrs.get("evidence") or ""),
                    "attributes": attrs,
                    "raw": rel,
                })
            for edge in self.edges:
                src = self.node_by_id.get(edge.get("source"))
                tgt = self.node_by_id.get(edge.get("target"))
                if not src or not tgt:
                    continue
                pair = ((src, tgt), (tgt, src))
                for person, other in pair:
                    if str(person.get("type")).upper() != "PERSON":
                        continue
                    typ = str(other.get("type")).upper()
                    label = str(other.get("label") or "")
                    if typ == "PLACE" and label and label not in person["related_places"]:
                        person["related_places"].append(label)
                    elif typ == "YEAR" and label and label not in person["related_years"]:
                        person["related_years"].append(label)
                    elif typ == "AGE" and label and label not in person["related_ages"]:
                        person["related_ages"].append(label)
            for node in self.nodes:
                if not node.get("place") and node.get("related_places"):
                    node["place"] = node["related_places"][0]
                if not node.get("year") and node.get("related_years"):
                    node["year"] = node["related_years"][0]
                if not node.get("age") and node.get("related_ages"):
                    node["age"] = node["related_ages"][0]
__all__ = [
    'BKCanonicalGraphDialogSetupMixin',
]
register_globals('bk', globals(), __all__)
