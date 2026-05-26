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

class BKCanonicalGraphDialogUiTablesMixin:
        def _show_graph_help(self):
            dlg = QDialog(self)
            dlg.setWindowTitle(self._tr2("dlg_canonical_graph_help_title", "Graph-Erklärung"))
            dlg.resize(720, 520)
            layout = QVBoxLayout(dlg)
            title = QLabel(f"<h2>{self._tr2('dlg_canonical_graph_help_title', 'Graph-Erklärung')}</h2>")
            title.setTextFormat(Qt.RichText)
            layout.addWidget(title)

            text = QTextBrowser()
            text.setOpenExternalLinks(True)
            html = self._tr2("dlg_canonical_graph_help_html", "")
            if not html or html == "dlg_canonical_graph_help_html":
                html = (
                    "<div style='font-size:10pt;'>"
                    "<h3>Was zeigt der Graph?</h3>"
                    "<p>Jeder Kreis ist ein erkannter Node, zum Beispiel Person, Ort, Jahr oder Alter. "
                    "Linien sind Beziehungen zwischen diesen Nodes.</p>"
                    "<h3>Wie entsteht die Kantenstärke?</h3>"
                    "<ul>"
                    "<li><b>0.80</b>: direkt belegte Beziehung, etwa Person–Ort.</li>"
                    "<li><b>0.75</b>: Zeit-/Jahr-Beziehung.</li>"
                    "<li><b>0.72</b>: Altersangabe.</li>"
                    "<li><b>0.35</b>: schwächere Dokument-/Teil-von-Beziehung.</li>"
                    "</ul>"
                    "<h3>Was machen die Regler?</h3>"
                    "<p>Node-Größe, Kantenstärke, Kantenabstand, Zentrierung, Abstoßung, "
                    "Kantenkraft und Cluster-Bubbles ändern nur die Darstellung. Die Daten werden dadurch nicht verändert.</p>"
                    "<h3>Interaktion</h3>"
                    "<p>Beim Klick auf einen Node werden der Node, direkt verbundene Nodes und verbundene Kanten hervorgehoben. "
                    "Die Tabellen rechts springen zur passenden Auswahl.</p>"
                    "<p>Cluster-Bubbles können über ihre Überschrift, zum Beispiel einen Nachnamen, "
                    "gezogen werden. Dabei werden alle Nodes dieser Bubble gemeinsam verschoben.</p>"
                    "</div>"
                )
            text.setHtml(html)
            layout.addWidget(text, 1)

            buttons = QDialogButtonBox(QDialogButtonBox.Ok)
            buttons.accepted.connect(dlg.accept)
            layout.addWidget(buttons)
            dlg.exec()

        def _build_ui(self):
            root = QVBoxLayout(self)
            top = QHBoxLayout()
            top.addWidget(QLabel(self._tr("dlg_canonical_graph_sort")))
            self.cmb_sort = QComboBox()
            for key, label in (
                ("name", self._tr("dlg_canonical_graph_sort_name")),
                ("last_name", self._tr("dlg_canonical_graph_sort_lastname")),
                ("place", self._tr("dlg_canonical_graph_sort_place")),
                ("year", self._tr("dlg_canonical_graph_sort_year")),
                ("age", self._tr("dlg_canonical_graph_sort_age")),
                ("type", self._tr("dlg_canonical_graph_sort_type")),
                ("strength", self._tr("dlg_canonical_graph_sort_strength")),
            ):
                self.cmb_sort.addItem(label, key)
            self.cmb_sort.setSizeAdjustPolicy(QComboBox.AdjustToContents)
            try:
                fm = self.cmb_sort.fontMetrics()
                longest_px = max(fm.horizontalAdvance(self.cmb_sort.itemText(i)) for i in range(self.cmb_sort.count()))
                dynamic_w = max(230, longest_px + 84)
                self.cmb_sort.setMinimumWidth(dynamic_w)
                self.cmb_sort.setMinimumContentsLength(max(16, max(len(self.cmb_sort.itemText(i)) for i in range(self.cmb_sort.count())) + 3))
                self.cmb_sort.view().setMinimumWidth(dynamic_w + 40)
            except Exception:
                self.cmb_sort.setMinimumWidth(240)
                try:
                    self.cmb_sort.view().setMinimumWidth(280)
                except Exception:
                    pass
            self.cmb_sort.currentIndexChanged.connect(self._sort_changed)
            top.addWidget(self.cmb_sort)
            self.graph_legend_label = QLabel(self._legend_text())
            self.graph_legend_label.setTextFormat(Qt.RichText)
            self.graph_legend_label.setStyleSheet("padding-left: 14px;")
            top.addWidget(self.graph_legend_label)
            self.btn_graph_help = QPushButton("?")
            self.btn_graph_help.setFixedWidth(32)
            self.btn_graph_help.setToolTip(self._tr2("dlg_canonical_graph_help_title", "Graph-Erklärung"))
            self.btn_graph_help.clicked.connect(self._show_graph_help)
            top.addWidget(self.btn_graph_help)
            top.addStretch(1)
            # Der separate Button "Graph einpassen" wurde entfernt.
            # Die Ansicht wird beim Öffnen und nach Neuordnung weiterhin automatisch eingepasst.
            self.btn_save = QPushButton(self._tr("dlg_canonical_graph_save_json"))
            self.btn_close = QPushButton(self._tr("btn_close"))
            top.addWidget(self.btn_save)
            top.addWidget(self.btn_close)
            root.addLayout(top)

            splitter = QSplitter(Qt.Horizontal)
            self.graph_view = BKCanonicalGraphView(self.scene, self)
            splitter.addWidget(self.graph_view)

            right = QWidget()
            right_layout = QVBoxLayout(right)
            settings_box = QGroupBox(self._tr("dlg_canonical_graph_settings"))
            settings_layout = QVBoxLayout(settings_box)
            # No free-text filter in this view: clustering is driven by the sort mode.
            self.graph_filter_edit = QLineEdit()
            self.graph_filter_edit.hide()
            self.chk_graph_arrows = QCheckBox(self._tr("dlg_canonical_graph_arrows"))
            self.chk_graph_arrows.setChecked(True)
            self.chk_graph_arrows.toggled.connect(self._graph_settings_changed)
            self.chk_graph_labels = QCheckBox(self._tr("dlg_canonical_graph_show_edge_labels"))
            self.chk_graph_labels.setChecked(False)
            self.chk_graph_labels.toggled.connect(self._graph_settings_changed)
            settings_layout.addWidget(self.chk_graph_arrows)
            settings_layout.addWidget(self.chk_graph_labels)
            self._graph_sliders = {}
            for key, label_key in (
                ("node", "dlg_canonical_graph_node_size"),
                ("edge", "dlg_canonical_graph_link_thickness"),
                ("distance", "dlg_canonical_graph_link_distance"),
                ("center", "dlg_canonical_graph_center_force"),
                ("repel", "dlg_canonical_graph_repel_force"),
                ("link", "dlg_canonical_graph_link_force"),
                ("bubble", "dlg_canonical_graph_cluster_bubble_size"),
            ):
                row = QHBoxLayout()
                lbl = QLabel(self._tr(label_key))
                lbl.setMinimumWidth(130)
                slider = QSlider(Qt.Horizontal)
                slider.setRange(-100, 100)
                slider.setValue(0)
                slider.setTickPosition(QSlider.TicksBelow)
                slider.setTickInterval(50)
                slider.valueChanged.connect(self._graph_settings_changed)
                row.addWidget(lbl)
                row.addWidget(slider, 1)
                settings_layout.addLayout(row)
                self._graph_sliders[key] = slider
            self.btn_graph_relayout = QPushButton(self._tr("dlg_canonical_graph_relayout"))
            self.btn_graph_relayout.clicked.connect(self._graph_relayout)
            settings_layout.addWidget(self.btn_graph_relayout)
            right_layout.addWidget(settings_box)
            right_layout.addWidget(QLabel(self._tr("dlg_canonical_graph_nodes")))
            self.tbl_nodes = QTableWidget(0, 8)
            self.tbl_nodes.setHorizontalHeaderLabels([
                self._tr("dlg_canonical_graph_col_type"),
                self._tr("dlg_canonical_graph_col_label"),
                self._tr("dlg_canonical_graph_col_first_name"),
                self._tr("dlg_canonical_graph_col_last_name"),
                self._tr("dlg_canonical_graph_col_place"),
                self._tr("dlg_canonical_graph_col_year"),
                self._tr("dlg_canonical_graph_col_age"),
                self._tr("dlg_canonical_graph_col_degree"),
            ])
            self.tbl_nodes.setSortingEnabled(True)
            self.tbl_nodes.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.tbl_nodes.itemSelectionChanged.connect(self._node_table_selection_changed)
            self.tbl_nodes.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            self.tbl_nodes.horizontalHeader().setStretchLastSection(True)
            right_layout.addWidget(self.tbl_nodes, 2)

            right_layout.addWidget(QLabel(self._tr("dlg_canonical_graph_edges")))
            self.tbl_edges = QTableWidget(0, 5)
            self.tbl_edges.setHorizontalHeaderLabels([
                self._tr("dlg_canonical_graph_col_source"),
                self._tr("dlg_canonical_graph_col_relation"),
                self._tr("dlg_canonical_graph_col_target"),
                self._tr("dlg_canonical_graph_col_strength"),
                self._tr("dlg_canonical_graph_col_evidence"),
            ])
            self.tbl_edges.setSortingEnabled(True)
            self.tbl_edges.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.tbl_edges.itemSelectionChanged.connect(self._edge_table_selection_changed)
            self.tbl_edges.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            self.tbl_edges.horizontalHeader().setStretchLastSection(True)
            right_layout.addWidget(self.tbl_edges, 2)
            splitter.addWidget(right)
            splitter.setSizes([760, 520])
            root.addWidget(splitter, 1)

            self.btn_save.clicked.connect(self._save_json)
            self.btn_close.clicked.connect(self.accept)

        def _sort_key(self, node: Dict[str, Any], mode: str):
            if mode == "name":
                return str(node.get("label") or "").lower()
            if mode == "last_name":
                return str(node.get("last_name") or "").lower()
            if mode == "place":
                return str(node.get("place") or "").lower()
            if mode == "year":
                m = re.search(r"\d+", str(node.get("year") or ""))
                return int(m.group(0)) if m else 999999
            if mode == "age":
                text = str(node.get("age") or node.get("label") or "")
                m = re.search(r"\d+", text)
                return int(m.group(0)) if m else 999999
            if mode == "type":
                return str(node.get("type") or "").lower()
            if mode == "strength":
                max_strength = 0.0
                nid = node.get("id")
                for edge in self.edges:
                    if edge.get("source") == nid or edge.get("target") == nid:
                        max_strength = max(max_strength, float(edge.get("strength") or 0.0))
                return -max_strength
            return str(node.get("label") or "").lower()

        def _sort_changed(self):
            mode = str(self.cmb_sort.currentData() or "name")
            self.nodes.sort(key=lambda n: self._sort_key(n, mode))
            if mode == "strength":
                self.edges.sort(key=lambda e: -float(e.get("strength") or 0.0))
            self._populate_tables()
            self._schedule_graph_render(fit=True, delay_ms=1)

        def _populate_tables(self):
            self.tbl_nodes.setSortingEnabled(False)
            self.tbl_nodes.setRowCount(len(self.nodes))
            for row, node in enumerate(self.nodes):
                values = [node.get("type"), node.get("label"), node.get("first_name"), node.get("last_name"), node.get("place"), node.get("year"), node.get("age"), node.get("degree")]
                for col, value in enumerate(values):
                    item = QTableWidgetItem(str(value if value is not None else ""))
                    item.setData(Qt.UserRole, node.get("id"))
                    if col == 7:
                        try:
                            item.setData(Qt.EditRole, int(value))
                        except Exception:
                            pass
                    self.tbl_nodes.setItem(row, col, item)
            self.tbl_nodes.setSortingEnabled(True)

            self.tbl_edges.setSortingEnabled(False)
            self.tbl_edges.setRowCount(len(self.edges))
            for row, edge in enumerate(self.edges):
                src = self.node_by_id.get(edge.get("source"), {}).get("label", edge.get("source"))
                tgt = self.node_by_id.get(edge.get("target"), {}).get("label", edge.get("target"))
                values = [src, edge.get("type"), tgt, round(float(edge.get("strength") or 0.0), 3), edge.get("evidence")]
                for col, value in enumerate(values):
                    item = QTableWidgetItem(str(value if value is not None else ""))
                    item.setData(Qt.UserRole, edge.get("id"))
                    if col == 3:
                        item.setData(Qt.EditRole, float(edge.get("strength") or 0.0))
                    self.tbl_edges.setItem(row, col, item)
            self.tbl_edges.setSortingEnabled(True)

        def _node_color(self, node_type: str) -> QColor:
            t = (node_type or "").upper()
            if t == "PERSON":
                return QColor("#5aa3ff")
            if t == "PLACE":
                return QColor("#7bd88f")
            if t == "YEAR":
                return QColor("#ffd166")
            if t == "AGE":
                return QColor("#f48fb1")
            if t in ("STREET", "ORGANIZATION"):
                return QColor("#c792ea")
            if t == "EVENT":
                return QColor("#ff9f6e")
            if t == "DOCUMENT":
                return QColor("#90a4ae")
            return QColor("#b0bec5")

        def _cluster_mode(self) -> str:
            try:
                return str(self.cmb_sort.currentData() or "name")
            except Exception:
                return "name"

        def _clean_cluster_value(self, value: str, fallback: str = "") -> str:
            value = _bk_clean_string(value)
            if not value or value.startswith("dlg_"):
                return fallback
            return value

        def _cluster_key(self, node: Dict[str, Any]) -> str:
            t = str(node.get("type") or "ENTITY").upper()
            mode = self._cluster_mode()
            if mode == "type":
                return f"TYPE:{t}"
            if t == "PERSON":
                if mode == "place":
                    place = self._clean_cluster_value(str(node.get("place") or (node.get("related_places") or [""])[0] or ""))
                    return f"PLACE:{place}" if place else "PERSON_OTHER"
                if mode == "year":
                    year = self._clean_cluster_value(str(node.get("year") or (node.get("related_years") or [""])[0] or ""))
                    return f"YEAR:{year}" if year else "PERSON_OTHER"
                if mode == "age":
                    age = self._clean_cluster_value(str(node.get("age") or (node.get("related_ages") or [""])[0] or ""))
                    return f"AGE:{age}" if age else "PERSON_OTHER"
                last = self._clean_cluster_value(str(node.get("last_name") or ""))
                if mode in ("last_name", "name") and last:
                    return f"SURNAME:{last}"
                return "PERSON_OTHER"
            if t == "PLACE":
                label = self._clean_cluster_value(str(node.get("label") or node.get("place") or ""))
                return f"PLACE:{label}" if mode == "place" and label else "PLACE_NODES"
            if t == "YEAR":
                label = self._clean_cluster_value(str(node.get("label") or node.get("year") or ""))
                return f"YEAR:{label}" if mode == "year" and label else "YEAR_NODES"
            if t == "AGE":
                label = self._clean_cluster_value(str(node.get("label") or node.get("age") or ""))
                return f"AGE:{label}" if mode == "age" and label else "AGE_NODES"
            if t == "DOCUMENT":
                return "DOCUMENT"
            if t == "EVENT":
                return "EVENT"
            if t in ("STREET", "ORGANIZATION"):
                return "CONTEXT"
            return "OTHER"
