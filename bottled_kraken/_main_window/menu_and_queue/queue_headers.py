from bottled_kraken.common import (
    QUEUE_COL_CHECK,
    QUEUE_COL_NUM,
    QUEUE_COL_STATUS,
    Qt,
)
import math
from bottled_kraken._main_window.menu_and_queue.menu_behavior import BKStayOpenMenu
class MainWindowQueueHeadersMixin:
        def _update_queue_check_header(self):
            header_item = self.queue_table.horizontalHeaderItem(QUEUE_COL_CHECK)
            if header_item is None:
                return
            total_rows = self.queue_table.rowCount()
            checked_rows = len(self._checked_queue_rows())
            if total_rows == 0 or checked_rows == 0:
                symbol = "☐"
            elif checked_rows == total_rows:
                symbol = "☑"
            else:
                symbol = "☒"
            header_item.setText(symbol)
            header_item.setTextAlignment(Qt.AlignCenter)
            header_item.setToolTip(self._tr("queue_check_header_tooltip"))
        def _on_queue_header_clicked(self, logical_index: int):
            if logical_index != QUEUE_COL_CHECK:
                return
            self._toggle_all_queue_checkmarks()
        def _queue_num_col_width(self) -> int:
            count = max(1, self.queue_table.rowCount())
            digits = len(str(count))
            fm = self.queue_table.fontMetrics()
            text_w = fm.horizontalAdvance("9" * digits)
            header_w = fm.horizontalAdvance("#")
            return max(header_w, text_w) + 10
        def _fit_queue_columns_exact(self):
            if self._resizing_cols:
                return
            self._resizing_cols = True
            try:
                vw = max(1, self.queue_table.viewport().width())
                num_w = self._queue_num_col_width()
                check_w = self._queue_check_col_width()
                remaining = max(0, vw - num_w - check_w)
                current_status_w = self.queue_table.columnWidth(QUEUE_COL_STATUS)
                preferred_status_w = current_status_w if current_status_w > 0 else 120
                min_status_w = 90
                min_file_w = 180
                max_status_w = max(min_status_w, remaining - min_file_w)
                if remaining <= (min_status_w + min_file_w):
                    status_w = max(0, min(preferred_status_w, max(0, remaining // 3)))
                else:
                    status_w = max(min_status_w, min(preferred_status_w, max_status_w))
                self.queue_table.setColumnWidth(QUEUE_COL_NUM, num_w)
                self.queue_table.setColumnWidth(QUEUE_COL_CHECK, check_w)
                self.queue_table.setColumnWidth(QUEUE_COL_STATUS, status_w)
                self._update_queue_hint()
            finally:
                self._resizing_cols = False
        def _on_queue_header_resized(self, logicalIndex: int, oldSize: int, newSize: int):
            if self._resizing_cols:
                return
            if logicalIndex in (QUEUE_COL_NUM, QUEUE_COL_CHECK, QUEUE_COL_STATUS):
                self._fit_queue_columns_exact()
        def resizeEvent(self, event):
            super().resizeEvent(event)
        def _update_queue_hint(self):
            empty = (self.queue_table.rowCount() == 0)
            self.queue_hint.setText(self._tr("queue_drop_hint"))
            self.queue_hint.resize(self.queue_table.viewport().size())
            self.queue_hint.move(0, 0)
            self.queue_hint.setVisible(empty)
        def _set_progress_busy(self):
            self.progress_bar.setValue(0)
            self.progress_bar.setRange(0, 0)
        def _set_progress_idle(self, value: int = 0):
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(max(0, min(100, int(value))))
        def on_progress_update(self, v: int):
            v = max(0, min(100, int(v)))
            if self.progress_bar.minimum() == 0 and self.progress_bar.maximum() == 0:
                if v > 0:
                    self.progress_bar.setRange(0, 100)
                else:
                    return
            self.progress_bar.setValue(v)
