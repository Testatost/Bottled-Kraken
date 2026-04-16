"""Kleinere Queue- und Overlay-Widgets."""
from ..shared import *

class QueueCheckDelegate(QStyledItemDelegate):
    def _checkbox_rect(self, option, widget):
        style = widget.style() if widget else QApplication.style()
        box_opt = QStyleOptionButton()
        indicator = style.subElementRect(QStyle.SE_CheckBoxIndicator, box_opt, widget)
        return QStyle.alignedRect(
            option.direction,
            Qt.AlignCenter,
            indicator.size(),
            option.rect
        )
    def paint(self, painter, option, index):
        value = index.data(Qt.CheckStateRole)
        if value is None:
            super().paint(painter, option, index)
            return
        # Zellenhintergrund / Selektion normal von Qt zeichnen lassen
        view_opt = QStyleOptionViewItem(option)
        self.initStyleOption(view_opt, index)
        view_opt.text = ""
        view_opt.icon = QIcon()
        view_opt.features &= ~QStyleOptionViewItem.HasCheckIndicator
        super().paint(painter, view_opt, index)
        style = option.widget.style() if option.widget else QApplication.style()
        box_opt = QStyleOptionButton()
        box_opt.state |= QStyle.State_Enabled
        if int(value) == str(Qt.Checked):
            box_opt.state |= QStyle.State_On
        else:
            box_opt.state |= QStyle.State_Off
        if option.state & QStyle.State_MouseOver:
            box_opt.state |= QStyle.State_MouseOver
        box_opt.rect = self._checkbox_rect(option, option.widget)
        style.drawPrimitive(QStyle.PE_IndicatorCheckBox, box_opt, painter, option.widget)
    def editorEvent(self, event, model, option, index):
        flags = index.flags()
        if not (flags & Qt.ItemIsUserCheckable) or not (flags & Qt.ItemIsEnabled):
            return False
        # Tastatur
        if event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Space, Qt.Key_Select):
                current = index.data(Qt.CheckStateRole)
                new_state = Qt.Unchecked if int(current) == int(Qt.Checked) else Qt.Checked
                return model.setData(index, new_state, Qt.CheckStateRole)
            return False
        # Doppelklick nicht separat toggeln
        if event.type() == QEvent.MouseButtonDblClick:
            return True
        # Maus nur innerhalb der zentrierten Checkbox
        if event.type() == QEvent.MouseButtonRelease:
            if event.button() != Qt.LeftButton:
                return False
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            if not self._checkbox_rect(option, option.widget).contains(pos):
                return False
            current = index.data(Qt.CheckStateRole)
            new_state = Qt.Unchecked if int(current) == int(Qt.Checked) else Qt.Checked
            return model.setData(index, new_state, Qt.CheckStateRole)
        return False

class OutlinedSimpleTextItem(QGraphicsSimpleTextItem):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._fill_color = QColor("#000000")
        self._outline_color = QColor("#ffffff")
        self._outline_width = 1.0

    def set_text_style(self, fill: QColor, outline: QColor, outline_width: float = 1.0):
        self._fill_color = QColor(fill)
        self._outline_color = QColor(outline)
        self._outline_width = max(0.5, float(outline_width))
        self.update()

    def boundingRect(self):
        br = super().boundingRect()
        pad = self._outline_width + 1.0
        return br.adjusted(-pad, -pad, pad, pad)

    def paint(self, painter, option, widget=None):
        text = self.text()
        if not text:
            return
        painter.save()
        painter.setFont(self.font())
        fm = QFontMetricsF(self.font())
        ascent = fm.ascent()
        pen = QPen(self._outline_color, self._outline_width)
        pen.setCosmetic(True)
        painter.setPen(pen)
        offsets = [
            (-1.0, 0.0), (1.0, 0.0), (0.0, -1.0), (0.0, 1.0),
            (-1.0, -1.0), (1.0, -1.0), (-1.0, 1.0), (1.0, 1.0),
        ]
        for dx, dy in offsets:
            painter.drawText(QPointF(dx, ascent + dy), text)
        painter.setPen(QPen(self._fill_color, 1.0))
        painter.drawText(QPointF(0.0, ascent), text)
        painter.restore()

class ResizableRectItem(QGraphicsRectItem):
    HANDLE_PAD = 6.0
    def __init__(
            self,
            rect: QRectF,
            idx: int,
            on_changed: Callable[[int, QRectF], None],
            on_clicked: Optional[Callable[[int], None]] = None,
            on_double_clicked: Optional[Callable[[int], None]] = None
    ):
        super().__init__(rect)
        self.idx = idx
        self._on_changed = on_changed
        self._on_clicked = on_clicked
        self._on_double_clicked = on_double_clicked
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsRectItem.ItemIsMovable, True)
        self._mode = "none"
        self._resize_edges = (False, False, False, False)  # L,T,R,B
        self._press_scene_pos: Optional[QPointF] = None
        self._press_rect: Optional[QRectF] = None
        self._press_item_pos: Optional[QPointF] = None
    def _hit_test_edges(self, pos: QPointF) -> Tuple[bool, bool, bool, bool]:
        r = self.rect()
        x, y = pos.x(), pos.y()
        l = abs(x - r.left()) <= self.HANDLE_PAD
        t = abs(y - r.top()) <= self.HANDLE_PAD
        rr = abs(x - r.right()) <= self.HANDLE_PAD
        b = abs(y - r.bottom()) <= self.HANDLE_PAD
        return l, t, rr, b
    def hoverMoveEvent(self, event):
        l, t, r, b = self._hit_test_edges(event.pos())
        if (l and t) or (r and b):
            self.setCursor(Qt.SizeFDiagCursor)
        elif (r and t) or (l and b):
            self.setCursor(Qt.SizeBDiagCursor)
        elif l or r:
            self.setCursor(Qt.SizeHorCursor)
        elif t or b:
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.OpenHandCursor)
        super().hoverMoveEvent(event)
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setSelected(True)
            self._press_scene_pos = event.scenePos()
            self._press_rect = QRectF(self.rect())
            self._press_item_pos = QPointF(self.pos())
            l, t, r, b = self._hit_test_edges(event.pos())
            self._resize_edges = (l, t, r, b)
            if any(self._resize_edges):
                self._mode = "resize"
            else:
                self._mode = "move"
            super().mousePressEvent(event)
            if callable(self._on_clicked):
                self._on_clicked(self.idx)
            event.accept()
            return
        super().mousePressEvent(event)
    def mouseMoveEvent(self, event):
        if self._mode == "resize" and self._press_scene_pos is not None and self._press_rect is not None:
            delta = event.scenePos() - self._press_scene_pos
            rect = QRectF(self._press_rect)
            l, t, r, b = self._resize_edges
            if l:
                rect.setLeft(rect.left() + delta.x())
            if r:
                rect.setRight(rect.right() + delta.x())
            if t:
                rect.setTop(rect.top() + delta.y())
            if b:
                rect.setBottom(rect.bottom() + delta.y())
            min_w = 5.0
            min_h = 5.0
            if rect.width() < min_w:
                if l:
                    rect.setLeft(rect.right() - min_w)
                else:
                    rect.setRight(rect.left() + min_w)
            if rect.height() < min_h:
                if t:
                    rect.setTop(rect.bottom() - min_h)
                else:
                    rect.setBottom(rect.top() + min_h)
            self.setRect(rect.normalized())
            event.accept()
            return
        super().mouseMoveEvent(event)
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self._mode in ("resize", "move"):
            self._mode = "none"
            if callable(self._on_changed):
                new_scene_rect = self.mapRectToScene(self.rect()).normalized()
                self._on_changed(self.idx, new_scene_rect)
            event.accept()
            return
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            try:
                if callable(self._on_double_clicked):
                    self._on_double_clicked(self.idx)
            except Exception:
                pass
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

class DropQueueTable(QTableWidget):
    files_dropped = Signal(list)
    table_resized = Signal()
    delete_pressed = Signal()
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDragDropOverwriteMode(False)
        self.setDragDropMode(QAbstractItemView.DropOnly)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.table_resized.emit()
    def keyPressEvent(self, event):
        super().keyPressEvent(event)
    def dragEnterEvent(self, event: QDragEnterEvent):
        if not event.mimeData().hasUrls():
            event.ignore()
            return
        for u in event.mimeData().urls():
            p = u.toLocalFile()
            if p and os.path.exists(p) and is_supported_drop_or_paste_file(p):
                event.acceptProposedAction()
                return
        event.ignore()
    def dragMoveEvent(self, event):
        if not event.mimeData().hasUrls():
            event.ignore()
            return
        for u in event.mimeData().urls():
            p = u.toLocalFile()
            if p and os.path.exists(p) and is_supported_drop_or_paste_file(p):
                event.acceptProposedAction()
                return
        event.ignore()
    def dropEvent(self, event: QDropEvent):
        if not event.mimeData().hasUrls():
            event.ignore()
            return
        files = []
        for u in event.mimeData().urls():
            p = u.toLocalFile()
            if p and os.path.exists(p) and is_supported_drop_or_paste_file(p):
                files.append(p)
        if files:
            self.files_dropped.emit(files)
            event.acceptProposedAction()
        else:
            event.ignore()
