"""Zeilenliste für erkannte OCR-Zeilen."""
from ..shared import *
from PySide6.QtGui import QCursor

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
        self.setDragEnabled(False)
        self.setAcceptDrops(False)
        self.setDropIndicatorShown(False)
        self.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.setDragDropOverwriteMode(False)
        self.header().setStretchLastSection(True)
        self.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.header().setDefaultAlignment(Qt.AlignCenter)
        self.setAlternatingRowColors(True)
        self.setIndentation(0)
        self.setStyleSheet("")
        self._drag_ids_snapshot: List[int] = []
        self._drag_rows_snapshot: List[int] = []
        self._drag_seed_rows: List[int] = []
        self._drag_active = False
        self._placeholder_row = -1
        self._placeholder_item: Optional[QTreeWidgetItem] = None
        self._drag_wheel_scroll_step = max(24, self.fontMetrics().height() + 8)
        self._drag_press_pos: Optional[QPoint] = None
        self._drag_last_pos: QPoint = QPoint()
        self._pending_reselect_source_rows: List[int] = []
        self._pending_reselect_new_rows: List[int] = []
    def edit(self, index, trigger, event):
        if index.isValid() and index.column() == 0:
            return False
        return super().edit(index, trigger, event)
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
    def _selected_drag_ids(self) -> List[int]:
        drag_ids = []
        for row in self.selected_line_rows():
            item = self.topLevelItem(row)
            if item is None or self._is_placeholder_item(item):
                continue
            item_id = item.data(0, Qt.UserRole)
            if item_id is None:
                continue
            drag_ids.append(int(item_id))
        return drag_ids
    def _begin_manual_drag(self, pos: QPoint) -> bool:
        drag_rows = self._drag_seed_rows if self._drag_seed_rows else self.selected_line_rows()
        drag_ids = self._selected_drag_ids()
        if not drag_rows:
            self._drag_active = False
            return False
        self._drag_rows_snapshot = drag_rows
        self._drag_ids_snapshot = drag_ids
        self._drag_active = True
        self._drag_last_pos = QPoint(pos)
        insert_row = self._drop_insert_row_from_pos(pos)
        self._show_placeholder_at(insert_row)
        self.viewport().setCursor(Qt.ClosedHandCursor)
        self.viewport().update()
        return True
    def _finish_manual_drag(self, commit: bool):
        if not self._drag_active:
            self._remove_placeholder()
            self._drag_rows_snapshot = []
            self._drag_ids_snapshot = []
            self._drag_seed_rows = []
            self._pending_reselect_source_rows = []
            self._pending_reselect_new_rows = []
            self.viewport().unsetCursor()
            return
        if not commit:
            self._remove_placeholder()
            self._drag_active = False
            self._drag_rows_snapshot = []
            self._drag_ids_snapshot = []
            self._drag_seed_rows = []
            self._pending_reselect_source_rows = []
            self._pending_reselect_new_rows = []
            self.viewport().unsetCursor()
            return
        insert_row = self._placeholder_row
        if insert_row < 0:
            insert_row = self._drop_insert_row_from_pos(self._drag_last_pos)
        self._remove_placeholder()
        moving_rows = sorted(set(
            row for row in self._drag_rows_snapshot
            if 0 <= row < self.topLevelItemCount()
        ))
        if not moving_rows:
            self._drag_active = False
            self._drag_rows_snapshot = []
            self._drag_ids_snapshot = []
            self._drag_seed_rows = []
            self._pending_reselect_source_rows = []
            self._pending_reselect_new_rows = []
            self.viewport().unsetCursor()
            return
        rows_to_take = sorted(moving_rows, reverse=True)
        taken_items_by_row = {}
        for row in rows_to_take:
            item = self.takeTopLevelItem(row)
            if item is None:
                continue
            taken_items_by_row[row] = item
        removed_before_insert = sum(1 for row in rows_to_take if row < insert_row)
        insert_row = max(0, min(self.topLevelItemCount(), insert_row - removed_before_insert))
        inserted_items = []
        inserted_rows = []
        for offset, row in enumerate(moving_rows):
            item = taken_items_by_row.get(row)
            if item is None:
                continue
            new_row = insert_row + offset
            self.insertTopLevelItem(new_row, item)
            inserted_items.append(item)
            inserted_rows.append(new_row)
        self._pending_reselect_new_rows = inserted_rows
        selected_set = set(inserted_rows)
        for row in range(self.topLevelItemCount()):
            item = self.topLevelItem(row)
            if item is None or self._is_placeholder_item(item):
                continue
            item.setSelected(row in selected_set)
        first_item = inserted_items[0] if inserted_items else None
        if first_item is not None:
            try:
                self.setCurrentItem(first_item, 0, QItemSelectionModel.NoUpdate)
            except Exception:
                self.setCurrentItem(first_item)
            self.scrollToItem(first_item, QAbstractItemView.PositionAtCenter)
        selected_sources = []
        for item in inserted_items:
            src_idx = item.data(0, Qt.UserRole)
            if src_idx is None:
                continue
            selected_sources.append(int(src_idx))
        self._pending_reselect_source_rows = selected_sources
        self._emit_current_visual_order()
        self._drag_active = False
        self._drag_rows_snapshot = []
        self._drag_ids_snapshot = []
        self._drag_seed_rows = []
        self.viewport().unsetCursor()
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = self._event_pos(event)
            self._drag_press_pos = pos
            selected_rows = self.selected_line_rows()
            self._drag_seed_rows = []
            clicked_item = self.itemAt(pos)
            if (
                clicked_item is not None
                and clicked_item.isSelected()
                and QApplication.keyboardModifiers() == Qt.NoModifier
            ):
                if selected_rows:
                    self._drag_seed_rows = selected_rows
                event.accept()
                return
        super().mousePressEvent(event)
    def mouseMoveEvent(self, event):
        pos = self._event_pos(event)
        if self._drag_active:
            self._drag_last_pos = QPoint(pos)
            self._show_placeholder_at(self._drop_insert_row_from_pos(pos))
            event.accept()
            return
        if (event.buttons() & Qt.LeftButton) and self._drag_press_pos is not None:
            if (pos - self._drag_press_pos).manhattanLength() >= QApplication.startDragDistance():
                if self._begin_manual_drag(pos):
                    event.accept()
                    return
            # Während LMB-Drag keine native Bereichsauswahl laufen lassen,
            # sonst markiert Qt zwischen Anker und Mausposition zusätzliche Zeilen.
            event.accept()
            return
        super().mouseMoveEvent(event)
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_press_pos = None
            self._drag_seed_rows = []
            if self._drag_active:
                self._drag_last_pos = self._event_pos(event)
                self._finish_manual_drag(commit=True)
                event.accept()
                return
        super().mouseReleaseEvent(event)
    def wheelEvent(self, event):
        super().wheelEvent(event)
        if not self._drag_active:
            return
        global_pos_attr = getattr(event, "globalPosition", None)
        if callable(global_pos_attr):
            global_pos = global_pos_attr().toPoint()
        else:
            global_pos = QCursor.pos()
        local_pos = self.viewport().mapFromGlobal(global_pos)
        self._drag_last_pos = QPoint(local_pos)
        self._show_placeholder_at(self._drop_insert_row_from_pos(local_pos))
    def keyPressEvent(self, event):
        if self._drag_active and event.key() == Qt.Key_Escape:
            self._finish_manual_drag(commit=False)
            event.accept()
            return
        if event.matches(QKeySequence.Copy):
            self.copy_selected_contents()
            event.accept()
            return
        if event.key() == Qt.Key_Delete:
            self.delete_pressed.emit()
            event.accept()
            return
        super().keyPressEvent(event)
