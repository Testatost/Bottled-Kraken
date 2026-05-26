"""Mixin für MainWindow: queue context preview and model loading."""
from ...shared import *
from ...ui_components import *
from ...workers import *
from ...dialogs import *
from ...image_edit import *

class MainWindowPreviewAndResultsMixin:
        def preview_image(self, path: str, persist_current: bool = False):
            try:
                if persist_current:
                    self._persist_loaded_preview_bboxes()
                im = Image.open(path)
                self.canvas.load_pil_image(im)
                self._loaded_preview_path = path
                self.list_lines.clear()
                item = next((i for i in self.queue_items if i.path == path), None)
                if item and item.results:
                    self.load_results(path, persist_current=False)
                else:
                    self.canvas.set_overlay_enabled(False)
            except Exception as e:
                QMessageBox.warning(self, self._tr("err_title"), self._tr("err_load", str(e)))

        def load_results(self, path: str, persist_current: bool = False):
            if persist_current:
                self._persist_loaded_preview_bboxes()
            item = next((i for i in self.queue_items if i.path == path), None)
            if not item or not item.results:
                return
            text, kr_records, im, recs = item.results
            preview_im = _load_image_color(path)
            self.canvas.load_pil_image(preview_im)
            self._loaded_preview_path = path
            self.canvas.set_overlay_enabled(bool(item.results))
            self._populate_lines_list(recs)
            self._refresh_overlay_display(recs)
            rows = self._selected_line_rows()
            if rows:
                self.canvas.select_indices(rows, center=False)

        def _populate_lines_list(self, recs: List[RecordView], keep_row: Optional[int] = None):
            self._close_line_search_popup()
            self.list_lines.blockSignals(True)
            self.list_lines.clear()
            if self.current_theme == "dark":
                even_bg = QColor(43, 43, 43)
                odd_bg = QColor(54, 54, 54)
            else:
                even_bg = QColor(255, 255, 255)
                odd_bg = QColor(245, 245, 245)
            for i, rv in enumerate(recs):
                it = QTreeWidgetItem([f"{i + 1:04d}", rv.text])
                it.setData(0, Qt.UserRole, i)
                it.setFlags(
                    Qt.ItemIsEnabled
                    | Qt.ItemIsSelectable
                    | Qt.ItemIsDragEnabled
                    | Qt.ItemIsEditable
                )
                it.setTextAlignment(0, Qt.AlignCenter)
                row_bg = odd_bg if (i % 2) else even_bg
                for col in range(2):
                    it.setBackground(col, QBrush(row_bg))
                self.list_lines.addTopLevelItem(it)
            self.list_lines.blockSignals(False)
            if recs:
                if keep_row is None:
                    self.list_lines.setCurrentRow(0)
                else:
                    self.list_lines.setCurrentRow(max(0, min(self.list_lines.count() - 1, keep_row)))
            if hasattr(self, "line_search_edit"):
                self._filter_lines_list(self.line_search_edit.text())

        def refresh_preview(self):
            if self.queue_table.currentRow() >= 0:
                path = self.queue_table.item(self.queue_table.currentRow(), QUEUE_COL_FILE).data(Qt.UserRole)
                item = next((i for i in self.queue_items if i.path == path), None)
                # refresh_preview lädt dieselbe sichtbare Seite neu (z. B. Overlay an/aus).
                # Deshalb vor dem Neuaufbau die aktuellen Canvas-Boxen sichern.
                if item and item.results:
                    self.load_results(path, persist_current=True)
                else:
                    self.preview_image(path, persist_current=True)

        def on_queue_double_click(self, row, col):
            path = self.queue_table.item(row, QUEUE_COL_FILE).data(Qt.UserRole)
            self.preview_image(path)
