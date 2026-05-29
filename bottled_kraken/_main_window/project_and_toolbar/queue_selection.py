from bottled_kraken.common import (
    List,
    Optional,
    QCheckBox,
    QHBoxLayout,
    QTableWidgetItem,
    QUEUE_COL_CHECK,
    QUEUE_COL_FILE,
    QUEUE_COL_NUM,
    QWidget,
    Qt,
    TaskItem,
)
import math
class MainWindowQueueSelectionMixin:
        def _queue_check_col_width(self) -> int:
            return 34
        def _make_queue_checkbox_widget(self, checked: bool = False) -> QWidget:
            wrap = QWidget()
            lay = QHBoxLayout(wrap)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.setSpacing(0)
            lay.setAlignment(Qt.AlignCenter)
            cb = QCheckBox(wrap)
            cb.setChecked(bool(checked))
            cb.stateChanged.connect(lambda _state: self._update_queue_check_header())
            lay.addWidget(cb)
            wrap.setStyleSheet("background: transparent;")
            return wrap
        def _queue_checkbox_at_row(self, row: int) -> Optional[QCheckBox]:
            wrap = self.queue_table.cellWidget(row, QUEUE_COL_CHECK)
            if wrap is None:
                return None
            cb = wrap.findChild(QCheckBox)
            return cb
        def _refresh_queue_numbers(self):
            for row in range(self.queue_table.rowCount()):
                item = self.queue_table.item(row, QUEUE_COL_NUM)
                if item is None:
                    item = QTableWidgetItem()
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                    self.queue_table.setItem(row, QUEUE_COL_NUM, item)
                item.setText(str(row + 1))
        def on_queue_current_cell_changed(self, currentRow, currentColumn, previousRow, previousColumn):
            try:
                self._persist_loaded_preview_bboxes()
            except Exception:
                pass
            if currentRow < 0:
                return
            item = self.queue_table.item(currentRow, QUEUE_COL_FILE)
            if not item:
                return
            path = item.data(Qt.UserRole)
            if path:
                self.preview_image(path, persist_current=False)
        def _checked_queue_rows(self) -> List[int]:
            rows = []
            for row in range(self.queue_table.rowCount()):
                cb = self._queue_checkbox_at_row(row)
                if cb is not None and cb.isChecked():
                    rows.append(row)
            return rows
        def _set_all_queue_checkmarks(self, checked: bool):
            for row in range(self.queue_table.rowCount()):
                cb = self._queue_checkbox_at_row(row)
                if cb is not None:
                    cb.blockSignals(True)
                    cb.setChecked(bool(checked))
                    cb.blockSignals(False)
            self._update_queue_check_header()
        def _toggle_all_queue_checkmarks(self):
            total_rows = self.queue_table.rowCount()
            if total_rows == 0:
                self._update_queue_check_header()
                return
            checked_rows = len(self._checked_queue_rows())
            should_check_all = checked_rows != total_rows
            self._set_all_queue_checkmarks(should_check_all)
        def _checked_queue_tasks(self) -> List[TaskItem]:
            out = []
            for row in self._checked_queue_rows():
                file_item = self.queue_table.item(row, QUEUE_COL_FILE)
                if not file_item:
                    continue
                path = file_item.data(Qt.UserRole)
                task = next((t for t in self.queue_items if t.path == path), None)
                if task:
                    out.append(task)
            return out
        def _selected_queue_tasks(self) -> List[TaskItem]:
            rows = self.queue_table.selectionModel().selectedRows()
            if not rows:
                return []
            paths = []
            for model_index in rows:
                item = self.queue_table.item(model_index.row(), QUEUE_COL_FILE)
                if item:
                    p = item.data(Qt.UserRole)
                    if p:
                        paths.append(p)
            out = []
            for p in paths:
                task = next((i for i in self.queue_items if i.path == p), None)
                if task:
                    out.append(task)
            return out
