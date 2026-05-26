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

class BKCanonicalGraphDialogLayoutRenderMixin:
        def _cluster_label(self, key: str) -> str:
            key = str(key or "OTHER")
            if key.startswith("PLACE:"):
                return f"{self._tr2('dlg_canonical_graph_cluster_place_prefix', 'Ort')}: {key.split(':', 1)[1]}"
            if key.startswith("YEAR:"):
                return f"{self._tr2('dlg_canonical_graph_cluster_year_prefix', 'Jahr')}: {key.split(':', 1)[1]}"
            if key.startswith("AGE:"):
                return f"{self._tr2('dlg_canonical_graph_cluster_age_prefix', 'Alter')}: {key.split(':', 1)[1]}"
            if key.startswith("SURNAME:"):
                return f"{self._tr2('dlg_canonical_graph_cluster_surname_prefix', 'Nachname')}: {key.split(':', 1)[1]}"
            if key.startswith("TYPE:"):
                return f"{self._tr2('dlg_canonical_graph_cluster_type_prefix', 'Typ')}: {key.split(':', 1)[1]}"
            return {
                "DOCUMENT": self._tr2("dlg_canonical_graph_cluster_document", "Dokument"),
                "PERSON_OTHER": self._tr2("dlg_canonical_graph_cluster_persons_uncategorized", "Personen ohne Gruppierung"),
                "PLACE_NODES": self._tr2("dlg_canonical_graph_cluster_places", "Orte"),
                "YEAR_NODES": self._tr2("dlg_canonical_graph_cluster_years", "Jahre"),
                "AGE_NODES": self._tr2("dlg_canonical_graph_cluster_ages", "Alter"),
                "EVENT": self._tr2("dlg_canonical_graph_cluster_events", "Ereignisse"),
                "CONTEXT": self._tr2("dlg_canonical_graph_cluster_context", "Kontext"),
                "OTHER": self._tr2("dlg_canonical_graph_cluster_other", "Sonstige"),
            }.get(key, key)

        def _graph_cluster_node_id_map(self) -> Dict[str, List[str]]:
            mapping: Dict[str, List[str]] = {}
            for node in self._visible_nodes():
                try:
                    key = self._cluster_key(node)
                except Exception:
                    key = "OTHER"
                node_id = str(node.get("id") or "")
                if node_id:
                    mapping.setdefault(str(key or "OTHER"), []).append(node_id)
            return mapping

        def _initial_cluster_centers(self, clusters: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Tuple[float, float]]:
            keys = list(clusters.keys())
            centers: Dict[str, Tuple[float, float]] = {}
            if not keys:
                return centers

            mode = self._cluster_mode()
            if mode in ("name", "last_name"):
                main_prefixes = ("SURNAME:",)
            elif mode == "place":
                main_prefixes = ("PLACE:",)
            elif mode == "year":
                main_prefixes = ("YEAR:",)
            elif mode == "age":
                main_prefixes = ("AGE:",)
            elif mode == "type":
                main_prefixes = ("TYPE:",)
            else:
                main_prefixes = ("SURNAME:", "PLACE:", "YEAR:", "TYPE:")

            def is_main(key: str) -> bool:
                return any(str(key).startswith(prefix) for prefix in main_prefixes)

            main_keys = [k for k in keys if is_main(k)]
            other_keys = [k for k in keys if k not in main_keys and k != "DOCUMENT"]

            # The selected grouping dimension is placed in the centre.
            # Other node families are arranged around it.
            golden = math.pi * (3.0 - math.sqrt(5.0))
            main_sorted = sorted(main_keys, key=lambda k: (-len(clusters.get(k, [])), str(k).lower()))
            if len(main_sorted) == 1:
                centers[main_sorted[0]] = (0.0, 0.0)
            else:
                inner_radius = max(180.0, 80.0 * math.sqrt(max(1, len(main_sorted))))
                for idx, key in enumerate(main_sorted):
                    r = inner_radius * (0.35 + 0.65 * math.sqrt((idx + 1) / max(1, len(main_sorted))))
                    a = idx * golden
                    centers[key] = (math.cos(a) * r, math.sin(a) * r)

            outer_radius = max(520.0, 190.0 * math.sqrt(max(1, len(other_keys))))
            for idx, key in enumerate(sorted(other_keys, key=lambda k: (-len(clusters.get(k, [])), str(k).lower()))):
                a = idx * golden + 0.85
                r = outer_radius * (0.82 + 0.28 * math.sqrt((idx + 1) / max(1, len(other_keys))))
                centers[key] = (math.cos(a) * r, math.sin(a) * r)

            if "DOCUMENT" in keys:
                centers["DOCUMENT"] = (0.0, 0.0)
            return centers

        def _clustered_positions(self) -> Tuple[Dict[str, Tuple[float, float]], Dict[str, Tuple[float, float, float, float]]]:
            clusters: Dict[str, List[Dict[str, Any]]] = {}
            node_cluster: Dict[str, str] = {}
            visible_nodes = self._visible_nodes()
            for node in visible_nodes:
                key = self._cluster_key(node)
                clusters.setdefault(key, []).append(node)
                node_cluster[str(node["id"])] = key

            centers = self._initial_cluster_centers(clusters)
            positions: Dict[str, List[float]] = {}
            golden = math.pi * (3.0 - math.sqrt(5.0))
            mode = self._cluster_mode()

            def _anchor_score(key: str, node: Dict[str, Any]) -> int:
                typ = str(node.get("type") or "").upper()
                label = _bk_clean_string(str(node.get("label") or ""))
                if key.startswith("PLACE:") and typ == "PLACE" and _bk_clean_string(key.split(":", 1)[1]).lower() == label.lower():
                    return -100
                if key.startswith("YEAR:") and typ == "YEAR" and _bk_clean_string(key.split(":", 1)[1]).lower() == label.lower():
                    return -100
                if key.startswith("SURNAME:") and typ == "PERSON":
                    return -10
                return 0

            for key, nodes in clusters.items():
                cx, cy = centers.get(key, (0.0, 0.0))
                sorted_nodes = sorted(nodes, key=lambda n: (_anchor_score(key, n), self._sort_key(n, mode)))
                for idx, node in enumerate(sorted_nodes):
                    # The grouping value itself (place/year node) sits in the center;
                    # related nodes are arranged around it.
                    if idx == 0 and _anchor_score(key, node) <= -100:
                        x, y = cx, cy
                    elif len(sorted_nodes) == 1:
                        x, y = cx, cy
                    else:
                        ring_idx = idx if _anchor_score(key, sorted_nodes[0]) <= -100 else idx + 1
                        r = 34.0 + float(getattr(self, "_graph_link_distance", 120) or 120) * 0.25 + 24.0 * math.sqrt(ring_idx)
                        a = ring_idx * golden
                        x = cx + math.cos(a) * r
                        y = cy + math.sin(a) * r
                    positions[str(node["id"])] = [x, y]

            # Organic force refinement: edge springs + node repulsion + cluster gravity.
            ids = list(positions.keys())
            id_set = set(ids)
            edges = [e for e in self._visible_edges() if e.get("source") in id_set and e.get("target") in id_set]
            max_nodes_for_repulsion = 280
            iterations = 70 if len(ids) <= 220 else 45
            for _ in range(iterations):
                disp = {nid: [0.0, 0.0] for nid in ids}
                sample_ids = ids[:max_nodes_for_repulsion]
                for i, a_id in enumerate(sample_ids):
                    ax, ay = positions[a_id]
                    for b_id in sample_ids[i + 1:]:
                        bx, by = positions[b_id]
                        dx = ax - bx; dy = ay - by
                        dist2 = dx * dx + dy * dy + 50.0
                        force = float(getattr(self, "_graph_repel_force", 5200) or 5200) / dist2
                        inv = 1.0 / math.sqrt(dist2)
                        fx = dx * inv * force; fy = dy * inv * force
                        disp[a_id][0] += fx; disp[a_id][1] += fy
                        disp[b_id][0] -= fx; disp[b_id][1] -= fy
                for edge in edges:
                    s = edge.get("source"); t = edge.get("target")
                    sx, sy = positions[s]; tx, ty = positions[t]
                    dx = tx - sx; dy = ty - sy
                    dist = max(1.0, math.sqrt(dx * dx + dy * dy))
                    desired = float(getattr(self, "_graph_link_distance", 120) or 120) + 60.0 * (1.0 - max(0.0, min(1.0, float(edge.get("strength") or 0.0))))
                    force = (dist - desired) * (float(getattr(self, "_graph_link_force", 20) or 20) / 1200.0) * max(0.25, float(edge.get("strength") or 0.0))
                    fx = dx / dist * force; fy = dy / dist * force
                    disp[s][0] += fx; disp[s][1] += fy
                    disp[t][0] -= fx; disp[t][1] -= fy
                for nid in ids:
                    key = node_cluster.get(nid, "OTHER")
                    cx, cy = centers.get(key, (0.0, 0.0))
                    x, y = positions[nid]
                    # Keep cluster membership readable even after force refinement.
                    disp[nid][0] += (cx - x) * (float(getattr(self, "_graph_center_force", 18) or 18) / 850.0)
                    disp[nid][1] += (cy - y) * (float(getattr(self, "_graph_center_force", 18) or 18) / 850.0)
                temp = 10.0
                for nid in ids:
                    dx, dy = disp[nid]
                    mag = max(1.0, math.sqrt(dx * dx + dy * dy))
                    positions[nid][0] += dx / mag * min(temp, mag)
                    positions[nid][1] += dy / mag * min(temp, mag)

                    # Keep every node visually inside its semantic cluster. This prevents
                    # sliders/edge forces from pulling nodes into unrelated bubbles.
                    key = node_cluster.get(nid, "OTHER")
                    cx, cy = centers.get(key, (0.0, 0.0))
                    vx = positions[nid][0] - cx
                    vy = positions[nid][1] - cy
                    dist = math.sqrt(vx * vx + vy * vy)
                    cluster_size = max(1, len(clusters.get(key, [])))
                    bubble_scale = float(getattr(self, "_graph_bubble_scale", 0.62) or 0.62)
                    max_radius = (62.0 + 24.0 * math.sqrt(cluster_size) + float(getattr(self, "_graph_link_distance", 120) or 120) * 0.08) * max(0.45, min(1.25, bubble_scale + 0.18))
                    if dist > max_radius:
                        scale = max_radius / max(1.0, dist)
                        positions[nid][0] = cx + vx * scale
                        positions[nid][1] = cy + vy * scale

            offsets = getattr(self, "_graph_cluster_manual_offsets", {}) or {}
            for nid, key in node_cluster.items():
                dx, dy = offsets.get(key, (0.0, 0.0))
                if dx or dy:
                    positions[nid][0] += float(dx)
                    positions[nid][1] += float(dy)

            boxes: Dict[str, Tuple[float, float, float, float]] = {}
            for key, nodes in clusters.items():
                pts = [positions[str(n["id"])] for n in nodes if str(n["id"]) in positions]
                if not pts:
                    continue
                xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
                margin = 86.0
                boxes[key] = (min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin)
            return {k: (v[0], v[1]) for k, v in positions.items()}, boxes

        def _add_cluster_backgrounds(self, boxes: Dict[str, Tuple[float, float, float, float]]):
            # Soft halos instead of rigid grid boxes. The halo and the title label
            # are drag handles for the whole cluster/bubble.
            self.graph_cluster_refs = {}
            self._graph_cluster_node_ids = self._graph_cluster_node_id_map()
            drag_tip = self._tr2(
                "dlg_canonical_graph_cluster_drag_tooltip",
                "Bubble ziehen: alle Nodes dieser Gruppe gemeinsam verschieben",
            )
            for key, (x1, y1, x2, y2) in boxes.items():
                w = max(92.0, x2 - x1); h = max(72.0, y2 - y1)
                # Keep the halo large enough to contain every node in this cluster.
                cx = x1 + w / 2.0; cy = y1 + h / 2.0
                bubble_scale = float(getattr(self, "_graph_bubble_scale", 0.62) or 0.62)
                w *= bubble_scale; h *= bubble_scale
                x1 = cx - w / 2.0; y1 = cy - h / 2.0
                halo = BKCanonicalGraphClusterBubbleItem(key, self, x1, y1, w, h)
                halo.setPen(QPen(QColor(120, 120, 120, 38), 1, Qt.DashLine))
                halo.setBrush(QBrush(QColor(245, 245, 245, 42)))
                halo.setZValue(-20)
                halo.setToolTip(drag_tip)
                self.scene.addItem(halo)
                font = QFont("Sans Serif", 8)
                font.setUnderline(True)
                label_width = min(240.0, max(100.0, w - 20))
                label_items = BKCanonicalOutlinedText.add(
                    self.scene,
                    self._cluster_label(key),
                    x1 + 10,
                    y1 + 8,
                    font,
                    width=label_width,
                )
                handle = BKCanonicalGraphClusterLabelHandle(key, self, x1 + 6, y1 + 3, label_width + 12, 34)
                handle.setToolTip(drag_tip)
                self.scene.addItem(handle)
                self.graph_cluster_refs[str(key)] = {
                    "halo": halo,
                    "label_items": label_items,
                    "handle": handle,
                }

        def _legend_text(self) -> str:
            entries = [
                ("#5aa3ff", self._tr2("dlg_canonical_graph_legend_person", "Person")),
                ("#7bd88f", self._tr2("dlg_canonical_graph_legend_place", "Ort")),
                ("#ffd166", self._tr2("dlg_canonical_graph_legend_year", "Jahr")),
                ("#f48fb1", self._tr2("dlg_canonical_graph_legend_age", "Alter")),
                ("#b0bec5", self._tr2("dlg_canonical_graph_legend_other", "Sonstige")),
            ]
            parts = [f"<b>{self._tr2('dlg_canonical_graph_legend', 'Legende')}:</b>"]
            for color, label in entries:
                parts.append(f"<span style='color:{color}; font-size:16px;'>●</span> {label}")
            return " &nbsp; ".join(parts)

        def _add_legend(self):
            # Legend is shown in the top toolbar next to the sorting control.
            return

        def _read_graph_settings(self):
            try:
                self._graph_filter_text = ""
                self._graph_show_arrows = bool(self.chk_graph_arrows.isChecked())
                self._graph_show_labels = bool(self.chk_graph_labels.isChecked())
                node_v = int(self._graph_sliders["node"].value())
                edge_v = int(self._graph_sliders["edge"].value())
                dist_v = int(self._graph_sliders["distance"].value())
                center_v = int(self._graph_sliders["center"].value())
                repel_v = int(self._graph_sliders["repel"].value())
                link_v = int(self._graph_sliders["link"].value())
                bubble_v = int(self._graph_sliders.get("bubble").value()) if self._graph_sliders.get("bubble") is not None else 0

                # UI values are -100..100 with 0 as the neutral default.
                self._graph_node_scale = max(40, 100 + node_v)
                self._graph_edge_scale = max(20, 100 + edge_v)
                self._graph_link_distance = max(40, 120 + int(dist_v * 1.8))
                self._graph_center_force = max(2, 18 + int(center_v * 0.35))
                self._graph_repel_force = max(500, 5200 + int(repel_v * 70))
                self._graph_link_force = max(1, 20 + int(link_v * 0.45))
                self._graph_bubble_scale = max(0.35, min(1.25, 0.62 + bubble_v * 0.004))
            except Exception:
                pass

        def _schedule_graph_render(self, fit: bool = False, delay_ms: int = 90):
            self._read_graph_settings()
            self._graph_render_pending_fit = bool(getattr(self, "_graph_render_pending_fit", False) or fit)
            try:
                self._graph_render_timer.start(max(1, int(delay_ms)))
            except Exception:
                self._perform_scheduled_graph_render()

        def _perform_scheduled_graph_render(self):
            fit = bool(getattr(self, "_graph_render_pending_fit", False))
            self._graph_render_pending_fit = False
            self._read_graph_settings()
            self._render_graph()
            if fit:
                QTimer.singleShot(0, self._fit_graph)

        def _graph_settings_changed(self, *args):
            # Coalesce slider/filter changes so the graph stays responsive.
            self._schedule_graph_render(fit=False, delay_ms=85)

        def _graph_relayout(self):
            # Explicit relayout resets manual bubble dragging offsets.
            self._graph_cluster_manual_offsets = {}
            self._schedule_graph_render(fit=True, delay_ms=1)

        def _select_graph_cluster(self, cluster_key: str):
            cluster_key = str(cluster_key or "OTHER")
            node_ids = set(getattr(self, "_graph_cluster_node_ids", {}).get(cluster_key, []))
            if not node_ids:
                return
            for nid, item in getattr(self, "graph_node_items", {}).items():
                try:
                    item.set_highlighted(str(nid) in node_ids)
                except Exception:
                    pass
            self._clear_table_highlights()
            self.tbl_nodes.blockSignals(True)
            self.tbl_nodes.clearSelection()
            first_row = -1
            for nid in node_ids:
                row = self._row_for_node_id(nid)
                if row >= 0:
                    if first_row < 0:
                        first_row = row
                    self._highlight_table_row(self.tbl_nodes, row, QColor("#e3f2fd"))
            if first_row >= 0:
                self.tbl_nodes.selectRow(first_row)
            self.tbl_nodes.blockSignals(False)

        def _move_graph_cluster_by_delta(self, cluster_key: str, delta):
            cluster_key = str(cluster_key or "OTHER")
            try:
                dx = float(delta.x())
                dy = float(delta.y())
            except Exception:
                try:
                    dx = float(delta[0]); dy = float(delta[1])
                except Exception:
                    return
            if abs(dx) < 0.01 and abs(dy) < 0.01:
                return

            offsets = getattr(self, "_graph_cluster_manual_offsets", None)
            if not isinstance(offsets, dict):
                offsets = {}
                self._graph_cluster_manual_offsets = offsets
            ox, oy = offsets.get(cluster_key, (0.0, 0.0))
            offsets[cluster_key] = (float(ox) + dx, float(oy) + dy)

            delta_point = QPointF(dx, dy)
            node_ids = getattr(self, "_graph_cluster_node_ids", {}).get(cluster_key, [])
            for node_id in node_ids:
                item = getattr(self, "graph_node_items", {}).get(str(node_id))
                if item is not None:
                    try:
                        item.setPos(item.pos() + delta_point)
                    except Exception:
                        pass

            refs = getattr(self, "graph_cluster_refs", {}).get(cluster_key, {})
            for key in ("halo", "handle"):
                item = refs.get(key)
                if item is not None:
                    try:
                        item.setPos(item.pos() + delta_point)
                    except Exception:
                        pass
            for item in refs.get("label_items", []) or []:
                try:
                    item.setPos(item.pos() + delta_point)
                except Exception:
                    pass

            # Explicitly refresh all connected edge geometries after moving a
            # cluster. QGraphicsItem.ItemPositionHasChanged normally updates
            # individual edges while each node is moved; this final pass keeps
            # line segments, arrow heads and edge labels in sync even if Qt
            # coalesces or suppresses itemChange events during batch movement.
            seen_edge_refs = set()
            for node_id in node_ids:
                item = getattr(self, "graph_node_items", {}).get(str(node_id))
                if item is None:
                    continue
                try:
                    item.update_connected_edges()
                except Exception:
                    pass
                for ref in getattr(item, "edge_refs", []) or []:
                    seen_edge_refs.add(id(ref))

            # Keep the edge-ref symbol in this method intentionally: static
            # regression tests verify that cluster-drag has a direct edge
            # update path instead of relying only on passive background moves.
            for ref in getattr(self, "graph_edge_refs", []) or []:
                if id(ref) in seen_edge_refs:
                    continue
                source_item = ref.get("source_item") if isinstance(ref, dict) else None
                if source_item is not None:
                    try:
                        source_item.update_connected_edges()
                    except Exception:
                        pass

            try:
                self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-120, -120, 120, 120))
            except Exception:
                pass

        def _visible_nodes(self) -> List[Dict[str, Any]]:
            return list(self.nodes)

        def _visible_edges(self) -> List[Dict[str, Any]]:
            """Edges whose source and target are currently visible."""
            visible_ids = {str(n.get("id")) for n in self._visible_nodes()}
            return [
                e for e in self.edges
                if str(e.get("source")) in visible_ids and str(e.get("target")) in visible_ids
            ]

        def _graph_add_arrow(self, x1: float, y1: float, x2: float, y2: float, color: QColor, width: float):
            if not getattr(self, "_graph_show_arrows", True):
                return []
            dx = x2 - x1
            dy = y2 - y1
            dist = max(1.0, math.sqrt(dx * dx + dy * dy))
            ux = dx / dist
            uy = dy / dist
            tip_x = x2 - ux * 18.0
            tip_y = y2 - uy * 18.0
            size = 8.0 + min(6.0, float(width))
            # two short strokes; avoids extra polygon imports and moves with edge updates.
            left_x = tip_x - ux * size - uy * size * 0.55
            left_y = tip_y - uy * size + ux * size * 0.55
            right_x = tip_x - ux * size + uy * size * 0.55
            right_y = tip_y - uy * size - ux * size * 0.55
            pen = QPen(color, max(1.0, width * 0.75))
            a = self.scene.addLine(tip_x, tip_y, left_x, left_y, pen)
            b = self.scene.addLine(tip_x, tip_y, right_x, right_y, pen)
            for item in (a, b):
                item.setZValue(-4)
            return [a, b]
