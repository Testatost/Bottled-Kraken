from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
from bottled_kraken.common import (
    Dict,
    List,
    QBrush,
    QColor,
    QFileDialog,
    QFont,
    QPen,
    QTableWidget,
    Qt,
    json,
    os,
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
class BKCanonicalGraphDialogSelectionSaveMixin:
        def _render_graph(self):
            self.scene.clear()
            self.graph_node_items = {}
            self.graph_edge_refs = []
            if not self.nodes:
                self.scene.addText(self._tr("dlg_canonical_graph_empty"))
                return
            positions, boxes = self._clustered_positions()
            self._add_cluster_backgrounds(boxes)
            node_items: Dict[str, BKCanonicalGraphNodeItem] = {}
            edge_refs = []
            for edge in self._visible_edges():
                if edge["source"] not in positions or edge["target"] not in positions:
                    continue
                x1, y1 = positions[edge["source"]]
                x2, y2 = positions[edge["target"]]
                strength = max(0.0, min(1.0, float(edge.get("strength") or 0.0)))
                alpha = int(42 + 150 * strength)
                width = max(0.7, 0.7 + 3.9 * strength) * (float(getattr(self, "_graph_edge_scale", 100) or 100) / 100.0)
                pen = QPen(QColor(70, 70, 70, alpha), width)
                line = BKCanonicalGraphEdgeItem(edge, owner=self)
                line.setLine(x1, y1, x2, y2)
                line.setPen(pen)
                line.setZValue(-5)
                line.setToolTip(f"{edge.get('type')} | {strength:.2f}")
                self.scene.addItem(line)
                arrow_items = self._graph_add_arrow(x1, y1, x2, y2, QColor(70, 70, 70, alpha), width)
                mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
                font = QFont("Sans Serif", 8)
                label_items = BKCanonicalOutlinedText.add(
                    self.scene,
                    f"{edge.get('type')} {strength:.2f}",
                    0,
                    0,
                    font,
                    width=190,
                )
                for label_item in label_items:
                    label_item.setPos(mx, my)
                    label_item.setZValue(9)
                    label_item.setVisible(bool(getattr(self, "_graph_show_labels", False)))
                ref = {"edge": edge, "line": line, "label_items": label_items, "arrow_items": arrow_items, "normal_pen": pen}
                edge_refs.append(ref)
            for node in self._visible_nodes():
                if node["id"] not in positions:
                    continue
                x, y = positions[node["id"]]
                deg = max(1, int(node.get("degree") or 1))
                size = min(96.0, 30.0 + deg * 4.8) * (float(getattr(self, "_graph_node_scale", 100) or 100) / 100.0)
                item = BKCanonicalGraphNodeItem(str(node["id"]), node, size, self._node_color(node.get("type")), owner=self)
                item.setPos(x, y)
                item.setToolTip(f"{node.get('type')} | {node.get('label')}\n{node.get('place')} {node.get('year')}")
                self.scene.addItem(item)
                node_items[str(node["id"])] = item
                label = str(node.get("label") or node.get("id"))
                font = QFont("Sans Serif", max(4, min(7, int(size / 14.0))))
                font.setBold(False)
                label_width = max(18.0, size * 0.88)
                BKCanonicalOutlinedText.add(
                    self.scene,
                    label,
                    -label_width / 2.0,
                    -5.0,
                    font,
                    parent_item=item,
                    width=label_width,
                )
            for ref in edge_refs:
                edge = ref.get("edge") or {}
                source_item = node_items.get(str(edge.get("source")))
                target_item = node_items.get(str(edge.get("target")))
                if source_item is None or target_item is None:
                    continue
                ref["source_item"] = source_item
                ref["target_item"] = target_item
                source_item.edge_refs.append(ref)
                target_item.edge_refs.append(ref)
            self.graph_node_items = node_items
            self.graph_edge_refs = edge_refs
            self._add_legend()
            self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-120, -120, 120, 120))
        def _clear_table_highlights(self):
            clear_brush = QBrush()
            for table in (self.tbl_nodes, self.tbl_edges):
                for row in range(table.rowCount()):
                    for col in range(table.columnCount()):
                        item = table.item(row, col)
                        if item is not None:
                            item.setBackground(clear_brush)
        def _highlight_table_row(self, table: QTableWidget, row: int, color: QColor):
            if row < 0:
                return
            brush = QBrush(color)
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item is not None:
                    item.setBackground(brush)
        def _row_for_node_id(self, node_id: str) -> int:
            for row in range(self.tbl_nodes.rowCount()):
                item = self.tbl_nodes.item(row, 0)
                if item is not None and str(item.data(Qt.UserRole) or "") == str(node_id):
                    return row
            return -1
        def _rows_for_edge_ids(self, edge_ids: set) -> List[int]:
            rows = []
            for row in range(self.tbl_edges.rowCount()):
                item = self.tbl_edges.item(row, 0)
                if item is not None and str(item.data(Qt.UserRole) or "") in edge_ids:
                    rows.append(row)
            return rows
        def _reset_graph_edge_visuals(self):
            for ref in getattr(self, "graph_edge_refs", []):
                line = ref.get("line")
                if line is not None:
                    line.setPen(ref.get("normal_pen") or QPen(QColor(70, 70, 70, 140), 1))
                    line.setZValue(-5)
                    try:
                        line.setSelected(False)
                    except Exception:
                        pass
                for label_item in (ref.get("label_items") or []):
                    try:
                        label_item.setVisible(bool(getattr(self, "_graph_show_labels", False)))
                    except Exception:
                        pass
        def _select_graph_node(self, node_id: str, center_on_node: bool = False):
            node_id = str(node_id or "")
            if not node_id:
                return
            self._selected_graph_node_id = node_id
            connected_node_ids = {node_id}
            connected_edge_ids = set()
            self._reset_graph_edge_visuals()
            for ref in getattr(self, "graph_edge_refs", []):
                edge = ref.get("edge") or {}
                connected = edge.get("source") == node_id or edge.get("target") == node_id
                line = ref.get("line")
                if connected:
                    connected_edge_ids.add(str(edge.get("id")))
                    if edge.get("source"):
                        connected_node_ids.add(str(edge.get("source")))
                    if edge.get("target"):
                        connected_node_ids.add(str(edge.get("target")))
                    if line is not None:
                        line.setPen(QPen(QColor("#ff7a00"), 5.2))
                        line.setZValue(12)
                    for label_item in (ref.get("label_items") or []):
                        try:
                            label_item.setVisible(True)
                        except Exception:
                            pass
            for nid, item in getattr(self, "graph_node_items", {}).items():
                try:
                    item.set_highlighted(nid in connected_node_ids)
                except Exception:
                    pass
            self._clear_table_highlights()
            self.tbl_nodes.blockSignals(True)
            self.tbl_nodes.clearSelection()
            for nid in connected_node_ids:
                row = self._row_for_node_id(nid)
                if row >= 0:
                    self._highlight_table_row(self.tbl_nodes, row, QColor("#ffe0b2" if nid == node_id else "#fff3cd"))
            node_row = self._row_for_node_id(node_id)
            if node_row >= 0:
                self.tbl_nodes.selectRow(node_row)
                self.tbl_nodes.scrollToItem(self.tbl_nodes.item(node_row, 0))
            self.tbl_nodes.blockSignals(False)
            edge_rows = self._rows_for_edge_ids(connected_edge_ids)
            self.tbl_edges.blockSignals(True)
            self.tbl_edges.clearSelection()
            for row in edge_rows:
                self._highlight_table_row(self.tbl_edges, row, QColor("#fff3cd"))
            if edge_rows:
                self.tbl_edges.selectRow(edge_rows[0])
                self.tbl_edges.scrollToItem(self.tbl_edges.item(edge_rows[0], 0))
            self.tbl_edges.blockSignals(False)
            if center_on_node and node_id in getattr(self, "graph_node_items", {}):
                try:
                    self.graph_view.centerOn(self.graph_node_items[node_id])
                except Exception:
                    pass
        def _select_graph_edge(self, edge_id: str, center_on_edge: bool = False):
            edge_id = str(edge_id or "")
            if not edge_id:
                return
            edge = next((e for e in self.edges if str(e.get("id")) == edge_id), None)
            if not edge:
                return
            src = str(edge.get("source") or "")
            tgt = str(edge.get("target") or "")
            self._selected_graph_node_id = src
            for nid, item in getattr(self, "graph_node_items", {}).items():
                try:
                    item.set_highlighted(nid in {src, tgt})
                except Exception:
                    pass
            self._reset_graph_edge_visuals()
            selected_line = None
            for ref in getattr(self, "graph_edge_refs", []):
                ref_edge = ref.get("edge") or {}
                if str(ref_edge.get("id")) == edge_id:
                    line = ref.get("line")
                    if line is not None:
                        line.setPen(QPen(QColor("#d00000"), 5.5))
                        line.setZValue(7)
                        selected_line = line
                    for label_item in (ref.get("label_items") or []):
                        label_item.setVisible(True)
            self._clear_table_highlights()
            for nid in (src, tgt):
                row = self._row_for_node_id(nid)
                if row >= 0:
                    self._highlight_table_row(self.tbl_nodes, row, QColor("#ffe0b2"))
            edge_rows = self._rows_for_edge_ids({edge_id})
            self.tbl_edges.blockSignals(True)
            self.tbl_edges.clearSelection()
            for row in edge_rows:
                self._highlight_table_row(self.tbl_edges, row, QColor("#ffccbc"))
            if edge_rows:
                self.tbl_edges.selectRow(edge_rows[0])
                self.tbl_edges.scrollToItem(self.tbl_edges.item(edge_rows[0], 0))
            self.tbl_edges.blockSignals(False)
            if center_on_edge:
                try:
                    if selected_line is not None:
                        self.graph_view.centerOn(selected_line.line().pointAt(0.5))
                except Exception:
                    pass
        def _node_table_selection_changed(self):
            items = self.tbl_nodes.selectedItems()
            if not items:
                return
            node_id = str(items[0].data(Qt.UserRole) or "")
            if node_id:
                self._select_graph_node(node_id, center_on_node=True)
        def _edge_table_selection_changed(self):
            items = self.tbl_edges.selectedItems()
            if not items:
                return
            edge_id = str(items[0].data(Qt.UserRole) or "")
            if edge_id:
                self._select_graph_edge(edge_id, center_on_edge=True)
        def _fit_graph(self):
            try:
                self.graph_view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
            except Exception:
                pass
        def _save_json(self):
            parent = self.parentWidget()
            start_dir = getattr(parent, "current_export_dir", "") or os.getcwd()
            default = os.path.splitext(os.path.basename(self.task_path or "canonical"))[0] + "_canonical.json"
            path, _ = QFileDialog.getSaveFileName(self, self._tr("dlg_canonical_graph_save_json"), os.path.join(start_dir, default), self._tr("dlg_filter_json"))
            if not path:
                return
            if not path.lower().endswith(".json"):
                path += ".json"
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(self.canonical, fh, ensure_ascii=False, indent=2)
            if parent is not None:
                try:
                    parent.current_export_dir = os.path.dirname(path)
                    parent.status_bar.showMessage(self._tr("msg_local_json_saved", os.path.basename(path)), 4000)
                except Exception:
                    pass
__all__ = [
    'BKCanonicalGraphDialogSelectionSaveMixin',
]
register_globals('bk', globals(), __all__)
