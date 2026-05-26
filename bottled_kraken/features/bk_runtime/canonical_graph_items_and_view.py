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

class BKCanonicalOutlinedText:
    @staticmethod
    def _text_path(text: str, font: QFont, x: float, y: float) -> QPainterPath:
        path = QPainterPath()
        # draw text at baseline. +font.pointSizeF() gives stable visual placement.
        baseline = y + max(10.0, float(font.pointSizeF() if font.pointSizeF() > 0 else font.pointSize()))
        path.addText(float(x), float(baseline), font, str(text or ""))
        return path

    @staticmethod
    def _wrap_lines(text: str, font: QFont, width: float, max_lines: int = 5) -> List[str]:
        text = str(text or "").strip()
        if not text:
            return [""]
        size = float(font.pointSizeF() if font.pointSizeF() > 0 else font.pointSize() or 8)
        max_chars = max(5, int(float(width or 120.0) / max(3.2, size * 0.48)))
        words = text.split()
        if not words:
            return [text]
        lines: List[str] = []
        cur = ""
        for word in words:
            if not cur:
                cur = word
            elif len(cur) + 1 + len(word) <= max_chars:
                cur += " " + word
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        # If a single long token exceeds the width, soft-split it.
        fixed: List[str] = []
        for line in lines:
            if len(line) <= max_chars:
                fixed.append(line)
            else:
                for i in range(0, len(line), max_chars):
                    fixed.append(line[i:i + max_chars])
        return fixed[:max_lines] if fixed else [""]

    @staticmethod
    def add(scene: QGraphicsScene, text: str, x: float, y: float, font: QFont, parent_item=None, width: float = 180.0):
        """Adds centered black text with a precise 1px white outline.

        Long labels are wrapped instead of shortened so node names stay readable.
        """
        lines = BKCanonicalOutlinedText._wrap_lines(str(text or ""), font, width, max_lines=5)
        size = float(font.pointSizeF() if font.pointSizeF() > 0 else font.pointSize() or 8)
        line_h = max(6.0, size * 1.22)
        total_h = line_h * len(lines)
        items = []
        for idx, line in enumerate(lines):
            # approximate text width; good enough for centering path text inside graph nodes
            approx_w = min(float(width or 180.0), max(1.0, len(line) * size * 0.52))
            xx = float(x) + (float(width or approx_w) - approx_w) / 2.0
            yy = float(y) - total_h / 2.0 + idx * line_h
            path = BKCanonicalOutlinedText._text_path(line, font, xx, yy)

            outline = QGraphicsPathItem(path, parent_item)
            outline.setPen(QPen(QColor("white"), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            outline.setBrush(QBrush(QColor("black")))
            outline.setZValue(20)
            if parent_item is None:
                scene.addItem(outline)

            fill = QGraphicsPathItem(path, parent_item)
            fill.setPen(QPen(QColor("black"), 0.25))
            fill.setBrush(QBrush(QColor("black")))
            fill.setZValue(21)
            if parent_item is None:
                scene.addItem(fill)
            items.extend([outline, fill])
        return items

class BKCanonicalGraphClusterBubbleItem(QGraphicsEllipseItem):
    """Draggable cluster bubble background.

    Dragging the bubble moves all nodes that belong to the same semantic
    cluster, for example all persons inside a surname bubble.
    """
    def __init__(self, cluster_key: str, owner, x: float, y: float, w: float, h: float):
        super().__init__(float(x), float(y), float(w), float(h))
        self.cluster_key = str(cluster_key or "OTHER")
        self.owner = owner
        self._dragging = False
        self._last_scene_pos = None
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.OpenHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._last_scene_pos = event.scenePos()
            self.setCursor(Qt.ClosedHandCursor)
            if self.owner is not None:
                try:
                    self.owner._select_graph_cluster(self.cluster_key)
                except Exception:
                    pass
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and self._last_scene_pos is not None:
            current = event.scenePos()
            delta = current - self._last_scene_pos
            self._last_scene_pos = current
            if self.owner is not None:
                try:
                    self.owner._move_graph_cluster_by_delta(self.cluster_key, delta)
                except Exception:
                    pass
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._dragging:
            self._dragging = False
            self._last_scene_pos = None
            self.setCursor(Qt.OpenHandCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def hoverEnterEvent(self, event):
        self.setCursor(Qt.OpenHandCursor)
        super().hoverEnterEvent(event)

class BKCanonicalGraphClusterLabelHandle(QGraphicsRectItem):
    """Transparent drag handle above a cluster title label."""
    def __init__(self, cluster_key: str, owner, x: float, y: float, w: float, h: float):
        super().__init__(float(x), float(y), float(w), float(h))
        self.cluster_key = str(cluster_key or "OTHER")
        self.owner = owner
        self._dragging = False
        self._last_scene_pos = None
        self.setPen(QPen(Qt.NoPen))
        self.setBrush(QBrush(QColor(255, 255, 255, 1)))
        self.setZValue(28)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.OpenHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._last_scene_pos = event.scenePos()
            self.setCursor(Qt.ClosedHandCursor)
            if self.owner is not None:
                try:
                    self.owner._select_graph_cluster(self.cluster_key)
                except Exception:
                    pass
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and self._last_scene_pos is not None:
            current = event.scenePos()
            delta = current - self._last_scene_pos
            self._last_scene_pos = current
            if self.owner is not None:
                try:
                    self.owner._move_graph_cluster_by_delta(self.cluster_key, delta)
                except Exception:
                    pass
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._dragging:
            self._dragging = False
            self._last_scene_pos = None
            self.setCursor(Qt.OpenHandCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def hoverEnterEvent(self, event):
        self.setCursor(Qt.OpenHandCursor)
        super().hoverEnterEvent(event)

class BKCanonicalGraphNodeItem(QGraphicsEllipseItem):
    def __init__(self, node_id: str, node_data: Dict[str, Any], size: float, color: QColor, owner=None):
        super().__init__(-size / 2.0, -size / 2.0, size, size)
        self.node_id = node_id
        self.node_data = node_data
        self.owner = owner
        self.edge_refs: List[Dict[str, Any]] = []
        self._normal_pen = QPen(QColor("#263238"), 2)
        self._selected_pen = QPen(QColor("#ff7a00"), 5)
        self.setBrush(QBrush(color))
        self.setPen(self._normal_pen)
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setZValue(10)
        self.setCursor(Qt.OpenHandCursor)

    def center_scene_pos(self) -> QPointF:
        return self.scenePos()

    def set_highlighted(self, active: bool):
        self.setPen(self._selected_pen if active else self._normal_pen)
        self.setZValue(30 if active else 10)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.update_connected_edges()
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        self.setCursor(Qt.ClosedHandCursor)
        if self.owner is not None:
            try:
                self.owner._select_graph_node(self.node_id, center_on_node=False)
            except Exception:
                pass
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.OpenHandCursor)
        super().mouseReleaseEvent(event)

    def update_connected_edges(self):
        for ref in list(self.edge_refs):
            try:
                source_item = ref.get("source_item")
                target_item = ref.get("target_item")
                line_item = ref.get("line")
                label_items = ref.get("label_items") or []
                if source_item is None or target_item is None or line_item is None:
                    continue
                sp = source_item.center_scene_pos()
                tp = target_item.center_scene_pos()
                line_item.setLine(sp.x(), sp.y(), tp.x(), tp.y())
                mx, my = (sp.x() + tp.x()) / 2.0, (sp.y() + tp.y()) / 2.0
                for item in label_items:
                    item.setPos(mx, my)
                arrows = ref.get("arrow_items") or []
                if arrows:
                    dx = tp.x() - sp.x(); dy = tp.y() - sp.y()
                    dist = max(1.0, math.sqrt(dx * dx + dy * dy))
                    ux = dx / dist; uy = dy / dist
                    tip_x = tp.x() - ux * 18.0; tip_y = tp.y() - uy * 18.0
                    size = 10.0
                    left_x = tip_x - ux * size - uy * size * 0.55
                    left_y = tip_y - uy * size + ux * size * 0.55
                    right_x = tip_x - ux * size + uy * size * 0.55
                    right_y = tip_y - uy * size - ux * size * 0.55
                    if len(arrows) >= 2:
                        arrows[0].setLine(tip_x, tip_y, left_x, left_y)
                        arrows[1].setLine(tip_x, tip_y, right_x, right_y)
            except Exception:
                pass

class BKCanonicalGraphEdgeItem(QGraphicsLineItem):
    def __init__(self, edge_data: Dict[str, Any], owner=None):
        super().__init__()
        self.edge_data = edge_data or {}
        self.owner = owner
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if self.owner is not None:
            try:
                self.owner._select_graph_edge(str(self.edge_data.get("id") or ""), center_on_edge=False)
            except Exception:
                pass
        super().mousePressEvent(event)

    def hoverEnterEvent(self, event):
        try:
            self.setZValue(5)
        except Exception:
            pass
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        try:
            if not self.isSelected():
                self.setZValue(-5)
        except Exception:
            pass
        super().hoverLeaveEvent(event)

class BKCanonicalGraphView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self._panning = False
        self._last_pos = None
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setBackgroundBrush(QBrush(QColor("#f7f7f7")))

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta == 0:
            delta = event.angleDelta().x()
        if delta == 0 and hasattr(event, "pixelDelta"):
            delta = event.pixelDelta().y() or event.pixelDelta().x()
        if delta == 0:
            event.accept()
            return
        factor = 1.15 if delta > 0 else 1 / 1.15
        self.scale(factor, factor)
        event.accept()

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if event.button() == Qt.LeftButton and item is None:
            self._panning = True
            self._last_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning and self._last_pos is not None:
            delta = event.pos() - self._last_pos
            self._last_pos = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._panning:
            self._panning = False
            self._last_pos = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)
