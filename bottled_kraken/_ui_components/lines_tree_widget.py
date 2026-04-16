"""Zeilenliste für erkannte OCR-Zeilen."""
from ..shared import *

class LinesTreeWidget(QTreeWidget):
    delete_pressed = Signal()
    reorder_committed = Signal(list, int)  # new_order (old indices), current_row after drop
    _DRAG_MIME = "application/x-bottled-kraken-lines-reorder"
    _PLACEHOLDER_ROLE = Qt.UserRole + 100
    def __init__(self, tr_func=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tr_func = tr_func
        self.setColumnCount(2)
        self.setHeaderLabels(["#", self._tr_func("lines_tree_header") if self._tr_func else ""])
        self.setRootIsDecorated(False)
        self.setUniformRowHeights(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(False)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDragDropOverwriteMode(False)
        self.header().setStretchLastSection(True)
        self.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.header().setDefaultAlignment(Qt.AlignCenter)
        self.setAlternatingRowColors(True)
        self.setIndentation(0)
        self.setStyleSheet("")
        self._drag_ids_snapshot: List[int] = []
        self._drag_active = False
        self._placeholder_row = -1
        self._placeholder_item: Optional[QTreeWidgetItem] = None
    def edit(self, index, trigger, event):
        if index.isValid() and index.column() == 0:
            return False
        return super().edit(index, trigger, event)
    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy):
            self.copy_selected_contents()
            event.accept()
            return
        if event.key() == Qt.Key_Delete:
            self.delete_pressed.emit()
            event.accept()
            return
        super().keyPressEvent(event)
    def copy_selected_contents(self):
        rows = self.selected_line_rows()
        if not rows:
            return
        parts = []
        for row in rows:
            it = self.topLevelItem(row)
            if it and not self._is_placeholder_item(it):
                parts.append(it.text(1))
        QApplication.clipboard().setText("\n".join(parts))
    def selected_line_rows(self) -> List[int]:
        rows = set()
        for idx in self.selectedIndexes():
            item = self.itemFromIndex(idx)
            if item is None or self._is_placeholder_item(item):
                continue
            rows.add(self.indexOfTopLevelItem(item))
        return sorted(row for row in rows if row >= 0)
    def currentRow(self) -> int:
        it = self.currentItem()
        if it is None or self._is_placeholder_item(it):
            return -1
        return self.indexOfTopLevelItem(it)
    def setCurrentRow(self, row: int):
        if 0 <= row < self.topLevelItemCount():
            item = self.topLevelItem(row)
            if item is not None and not self._is_placeholder_item(item):
                self.setCurrentItem(item)
    def count(self) -> int:
        return self.topLevelItemCount()
    def row(self, item: QTreeWidgetItem) -> int:
        return self.indexOfTopLevelItem(item)
    def row_item(self, row: int) -> Optional[QTreeWidgetItem]:
        return self.topLevelItem(row)
    def _event_pos(self, event) -> QPoint:
        pos_attr = getattr(event, "position", None)
        if callable(pos_attr):
            return pos_attr().toPoint()
        return event.pos()
    def _is_placeholder_item(self, item: Optional[QTreeWidgetItem]) -> bool:
        return bool(item is not None and item.data(0, self._PLACEHOLDER_ROLE))
    def _make_placeholder_item(self) -> QTreeWidgetItem:
        it = QTreeWidgetItem(["", " "])
        it.setData(0, self._PLACEHOLDER_ROLE, True)
        it.setFlags(Qt.ItemIsEnabled)
        it.setTextAlignment(0, Qt.AlignCenter)
        placeholder_bg = self.palette().highlight().color().lighter(150)
        placeholder_fg = self.palette().highlightedText().color()
        for col in range(2):
            it.setBackground(col, QBrush(placeholder_bg))
            it.setForeground(col, QBrush(placeholder_fg))
        it.setSizeHint(0, QSize(0, max(22, self.fontMetrics().height() + 8)))
        it.setSizeHint(1, QSize(0, max(22, self.fontMetrics().height() + 8)))
        return it
    def _remove_placeholder(self):
        if self._placeholder_item is None:
            self._placeholder_row = -1
            return
        row = self.indexOfTopLevelItem(self._placeholder_item)
        if row >= 0:
            self.takeTopLevelItem(row)
        self._placeholder_item = None
        self._placeholder_row = -1
    def _count_real_items(self) -> int:
        count = 0
        for i in range(self.topLevelItemCount()):
            if not self._is_placeholder_item(self.topLevelItem(i)):
                count += 1
        return count
    def _iter_real_items(self):
        logical_row = 0
        for visual_row in range(self.topLevelItemCount()):
            item = self.topLevelItem(visual_row)
            if item is None or self._is_placeholder_item(item):
                continue
            yield logical_row, visual_row, item
            logical_row += 1
    def _drop_insert_row_from_pos(self, pos: QPoint) -> int:
        count = self._count_real_items()
        if count <= 0:
            return 0
        for logical_row, _visual_row, item in self._iter_real_items():
            rect = self.visualItemRect(item)
            if not rect.isValid():
                continue
            if pos.y() < rect.center().y():
                return logical_row
            if rect.top() <= pos.y() <= rect.bottom():
                return logical_row + 1
        return count
    def _show_placeholder_at(self, insert_row: int):
        insert_row = max(0, min(self._count_real_items(), int(insert_row)))
        if self._placeholder_item is not None and self._placeholder_row == insert_row:
            return
        self._remove_placeholder()
        self._placeholder_item = self._make_placeholder_item()
        visual_insert_row = self.topLevelItemCount()
        logical_row = 0
        for visual_row in range(self.topLevelItemCount()):
            item = self.topLevelItem(visual_row)
            if item is None or self._is_placeholder_item(item):
                continue
            if logical_row >= insert_row:
                visual_insert_row = visual_row
                break
            logical_row += 1
        self.insertTopLevelItem(visual_insert_row, self._placeholder_item)
        self._placeholder_row = insert_row
    def _emit_current_visual_order(self):
        order = []
        for i in range(self.topLevelItemCount()):
            it = self.topLevelItem(i)
            if it is None or self._is_placeholder_item(it):
                continue
            idx = it.data(0, Qt.UserRole)
            if idx is None:
                idx = i
            order.append(int(idx))
        self.reorder_committed.emit(order, self.currentRow())
    def startDrag(self, supportedActions):
        rows = self.selected_line_rows()
        if not rows:
            return
        drag_ids = []
        for row in rows:
            item = self.topLevelItem(row)
            if item is None or self._is_placeholder_item(item):
                continue
            item_id = item.data(0, Qt.UserRole)
            if item_id is None:
                continue
            drag_ids.append(int(item_id))
        if not drag_ids:
            return
        self._drag_ids_snapshot = drag_ids
        self._drag_active = True
        self._remove_placeholder()
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(self._DRAG_MIME, b"move")
        drag.setMimeData(mime)
        current = self.currentItem()
        if current is not None and not self._is_placeholder_item(current):
            rect = self.visualItemRect(current)
            if rect.isValid():
                drag.setPixmap(self.viewport().grab(rect))
                drag.setHotSpot(QPoint(12, min(12, max(0, rect.height() // 2))))
        try:
            drag.exec(Qt.MoveAction)
        finally:
            self._remove_placeholder()
            self._drag_active = False
            self._drag_ids_snapshot = []
    def dragEnterEvent(self, event):
        if event.source() is self and event.mimeData().hasFormat(self._DRAG_MIME):
            event.setDropAction(Qt.MoveAction)
            event.accept()
            return
        event.ignore()
    def dragMoveEvent(self, event):
        if event.source() is not self or not event.mimeData().hasFormat(self._DRAG_MIME):
            event.ignore()
            return
        insert_row = self._drop_insert_row_from_pos(self._event_pos(event))
        self._show_placeholder_at(insert_row)
        event.setDropAction(Qt.MoveAction)
        event.accept()
    def dragLeaveEvent(self, event):
        self._remove_placeholder()
        event.accept()
    def dropEvent(self, event):
        if event.source() is not self or not event.mimeData().hasFormat(self._DRAG_MIME):
            event.ignore()
            return
        if not self._drag_ids_snapshot:
            self._remove_placeholder()
            event.ignore()
            return
        insert_row = self._placeholder_row
        if insert_row < 0:
            insert_row = self._drop_insert_row_from_pos(self._event_pos(event))
        self._remove_placeholder()
        id_to_row = {}
        id_to_item = {}
        for row in range(self.topLevelItemCount()):
            item = self.topLevelItem(row)
            if item is None or self._is_placeholder_item(item):
                continue
            item_id = item.data(0, Qt.UserRole)
            if item_id is None:
                continue
            item_id = int(item_id)
            if item_id in self._drag_ids_snapshot:
                id_to_row[item_id] = row
                id_to_item[item_id] = item
        moving_ids = [item_id for item_id in self._drag_ids_snapshot if item_id in id_to_item]
        if not moving_ids:
            event.ignore()
            return
        rows_to_take = sorted((id_to_row[item_id] for item_id in moving_ids), reverse=True)
        taken_items = {}
        for row in rows_to_take:
            item = self.takeTopLevelItem(row)
            if item is None:
                continue
            item_id = item.data(0, Qt.UserRole)
            if item_id is not None:
                taken_items[int(item_id)] = item
        removed_before_insert = sum(1 for row in rows_to_take if row < insert_row)
        insert_row = max(0, min(self.topLevelItemCount(), insert_row - removed_before_insert))
        inserted_items = []
        for offset, item_id in enumerate(moving_ids):
            item = taken_items.get(item_id)
            if item is None:
                continue
            self.insertTopLevelItem(insert_row + offset, item)
            inserted_items.append(item)
        self.clearSelection()
        first_item = inserted_items[0] if inserted_items else None
        for item in inserted_items:
            item.setSelected(True)
        if first_item is not None:
            self.setCurrentItem(first_item)
            self.scrollToItem(first_item, QAbstractItemView.PositionAtCenter)
        self._emit_current_visual_order()
        event.setDropAction(Qt.MoveAction)
        event.accept()
