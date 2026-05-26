"""Mixin für MainWindow: import lines and ocr batch."""
from ...shared import *
from ...ui_components import *
from ...workers import *
from ...dialogs import *
from ...image_edit import *

class MainWindowLineSelectionAndImportMixin:
        def on_line_selected(self, current, previous=None):
            row = self.list_lines.currentRow()
            task = self._current_task()
            if not task or not task.results:
                return
            _, _, _, recs = task.results
            self._refresh_overlay_display(recs)
            rows = self._selected_line_rows()
            if rows:
                self.canvas.select_indices(rows, center=False)
                return
            if row < 0:
                self.canvas.select_indices([], center=False)
                return
            if 0 <= row < len(recs):
                self.canvas.select_idx(row)

        def on_lines_selection_changed(self):
            task = self._current_task()
            if not task or not task.results:
                return
            _, _, _, recs = task.results
            self._refresh_overlay_display(recs)
            rows = self._selected_line_rows()
            if not rows:
                self.canvas.select_indices([], center=False)
                return
            self.canvas.select_indices(rows, center=False)

        def on_canvas_multi_selected(self, indices: list):
            self.list_lines.blockSignals(True)
            self.list_lines.clearSelection()
            clean = sorted(set(int(i) for i in indices if i is not None))
            first_item = None
            for idx in clean:
                if 0 <= idx < self.list_lines.count():
                    it = self.list_lines.row_item(idx)
                    if it:
                        it.setSelected(True)
                        if first_item is None:
                            first_item = it
            if first_item is not None:
                try:
                    self.list_lines.setCurrentItem(first_item, 0, QItemSelectionModel.NoUpdate)
                except Exception:
                    self.list_lines.setCurrentItem(first_item)
                try:
                    self.list_lines.scrollToItem(first_item, QAbstractItemView.PositionAtCenter)
                except Exception:
                    pass
                self.list_lines.setFocus()
            self.list_lines.blockSignals(False)
            # Canvas-Farben konsistent halten
            self.canvas.select_indices(clean, center=False)

        def on_rect_clicked(self, idx):
            if 0 <= idx < self.list_lines.count():
                self.list_lines.blockSignals(True)
                self.list_lines.clearSelection()
                self.list_lines.setCurrentRow(idx)
                it = self.list_lines.row_item(idx)
                if it:
                    it.setSelected(True)
                self.list_lines.blockSignals(False)
                self.canvas.select_indices([idx], center=False)
                self.list_lines.setFocus()

        @staticmethod
        def _parse_line_item_full(text: str) -> Tuple[Optional[int], str]:
            t = (text or "").rstrip("\n")
            m = re.match(r"^\s*(\d+)\s+(.*)$", t)
            if not m:
                return None, t.strip()
            num = int(m.group(1))
            rest = (m.group(2) or "").strip()
            return num - 1, rest

        def on_line_item_edited(self, item: QTreeWidgetItem, column: int):
            if column != 1:
                return
            task = self._current_task()
            if not task or not task.results or task.status != STATUS_DONE:
                return
            _, _, _, recs = task.results
            row = self.list_lines.row(item)
            if row is None or not (0 <= row < len(recs)):
                return
            new_text = (item.text(1) or "").strip()
            old_text = recs[row].text
            if new_text == old_text:
                self._sync_ui_after_recs_change(task, keep_row=row)
                return
            self._push_undo(task)
            recs[row].text = new_text
            task.edited = True
            self._sync_ui_after_recs_change(task, keep_row=row)

        def _delete_current_line_via_key(self):
            task = self._current_task()
            if not task or not task.results or task.status != STATUS_DONE:
                return
            row = self.list_lines.currentRow()
            if row >= 0:
                self._delete_line(task, row)

        def on_lines_reordered(self, order: list, current_row_after_drop: int):
            task = self._current_task()
            if not task or not task.results or task.status != STATUS_DONE:
                return
            _, _, _, recs = task.results
            if not order or len(order) != len(recs):
                return
            keep_row = max(0, min(len(recs) - 1, int(current_row_after_drop)))
            # Bei manuellem Drag-and-Drop baut _reorder_lines_keep_box_slots()
            # die Zeilenliste neu auf. Dadurch ging die Mehrfachauswahl nach dem
            # Drop verloren, obwohl LinesTreeWidget die verschobenen Quellzeilen
            # bereits kennt. Die Auswahl wird deshalb anhand der alten Quell-IDs
            # nach dem neuen order[]-Mapping wiederhergestellt.
            moved_source_rows = []
            try:
                moved_source_rows = [
                    int(r) for r in getattr(self.list_lines, "_pending_reselect_source_rows", []) or []
                    if 0 <= int(r) < len(recs)
                ]
            except Exception:
                moved_source_rows = []
            self._reorder_lines_keep_box_slots(task, order, keep_row=keep_row)
            if moved_source_rows:
                try:
                    moved_rows = sorted(order.index(src) for src in moved_source_rows if src in order)
                except Exception:
                    moved_rows = []
                if moved_rows:
                    try:
                        self.list_lines.blockSignals(True)
                        self.list_lines.clearSelection()
                        first_item = None
                        for new_row in moved_rows:
                            it = self.list_lines.row_item(new_row)
                            if it is not None:
                                it.setSelected(True)
                                if first_item is None:
                                    first_item = it
                        if first_item is not None:
                            try:
                                self.list_lines.setCurrentItem(first_item, 0, QItemSelectionModel.NoUpdate)
                            except Exception:
                                self.list_lines.setCurrentItem(first_item)
                            try:
                                self.list_lines.scrollToItem(first_item, QAbstractItemView.PositionAtCenter)
                            except Exception:
                                pass
                        self.list_lines.blockSignals(False)
                        if task.results:
                            _, _, _, new_recs = task.results
                            self._refresh_overlay_display(new_recs)
                        self.canvas.select_indices(moved_rows, center=False)
                    except Exception:
                        try:
                            self.list_lines.blockSignals(False)
                        except Exception:
                            pass
            try:
                self.list_lines._pending_reselect_source_rows = []
                self.list_lines._pending_reselect_new_rows = []
            except Exception:
                pass

        def lines_context_menu(self, pos):
            item = self.list_lines.itemAt(pos)
            if item is None:
                return
            row = self.list_lines.row(item)
            menu = QMenu()
            act_swap = menu.addAction(self._tr("line_menu_swap_with"))
            act_move_up = menu.addAction(self._tr("line_menu_move_up_page"))
            act_move_down = menu.addAction(self._tr("line_menu_move_down_page"))
            menu.addSeparator()
            act_del = menu.addAction(self._tr("line_menu_delete"))
            menu.addSeparator()
            act_add_above = menu.addAction(self._tr("line_menu_add_above"))
            act_add_below = menu.addAction(self._tr("line_menu_add_below"))
            menu.addSeparator()
            act_draw = menu.addAction(self._tr("line_menu_draw_box"))
            chosen = menu.exec(self.list_lines.viewport().mapToGlobal(pos))
            if not chosen:
                return
            task = self._current_task()
            if not task or not task.results or task.status != STATUS_DONE:
                return
            if chosen == act_swap:
                self._swap_line_with_dialog(task, row)
            elif chosen == act_move_up:
                rows = self._selected_line_rows() if item.isSelected() else [row]
                self._move_selected_lines(task, rows, -1)
            elif chosen == act_move_down:
                rows = self._selected_line_rows() if item.isSelected() else [row]
                self._move_selected_lines(task, rows, 1)
            elif chosen == act_del:
                self._delete_line(task, row)
            elif chosen == act_add_above:
                self._add_line(task, insert_row=row)
            elif chosen == act_add_below:
                self._add_line(task, insert_row=row + 1)
            elif chosen == act_draw:
                self._pending_new_line_box = False
                self._pending_box_for_row = row
                self.canvas.start_draw_box_mode()

        def _sync_ui_after_recs_change(self, task: TaskItem, keep_row: Optional[int] = None):
            if not task.results:
                return
            text, kr_records, im, recs = task.results
            for i, rv in enumerate(recs):
                rv.idx = i
            new_text = "\n".join([r.text for r in recs]).strip()
            task.results = (new_text, kr_records, im, recs)
            # WICHTIG:
            # Immer den aktuellsten Box-Stand zentral synchron halten.
            self._update_task_preset_bboxes(task)
            self._populate_lines_list(recs, keep_row=keep_row)
            if os.path.exists(task.path):
                preview_im = _load_image_color(task.path)
                self.canvas.load_pil_image(preview_im, preserve_view=True)
                self.canvas.set_overlay_enabled(task.status == STATUS_DONE)
                self._refresh_overlay_display(recs)
            else:
                self.canvas.clear_all()
                self.canvas.set_overlay_enabled(False)

        def _move_line(self, task: TaskItem, row: int, direction: int):
            self._move_selected_lines(task, [row], direction)

        def _move_selected_lines(self, task: TaskItem, rows: list, direction: int):
            if not task.results:
                return
            _, _, _, recs = task.results
            if not recs:
                return
            clean = sorted(set(int(r) for r in (rows or []) if 0 <= int(r) < len(recs)))
            if not clean:
                return
            direction = -1 if int(direction or 0) < 0 else 1
            selected = set(clean)
            if direction < 0:
                if min(selected) <= 0:
                    return
                order = list(range(len(recs)))
                for i in range(1, len(order)):
                    if order[i] in selected and order[i - 1] not in selected:
                        order[i - 1], order[i] = order[i], order[i - 1]
                keep_row = max(0, min(len(recs) - 1, clean[0] - 1))
            else:
                if max(selected) >= len(recs) - 1:
                    return
                order = list(range(len(recs)))
                for i in range(len(order) - 2, -1, -1):
                    if order[i] in selected and order[i + 1] not in selected:
                        order[i], order[i + 1] = order[i + 1], order[i]
                keep_row = max(0, min(len(recs) - 1, clean[-1] + 1))
            if order == list(range(len(recs))):
                return
            self._push_undo(task)
            new_recs = [recs[i] for i in order]
            recs[:] = new_recs
            task.edited = True
            self._sync_ui_after_recs_change(task, keep_row=keep_row)
            try:
                moved_rows = sorted(order.index(r) for r in clean if r in order)
                self.list_lines.blockSignals(True)
                self.list_lines.clearSelection()
                first_item = None
                for new_row in moved_rows:
                    it = self.list_lines.row_item(new_row)
                    if it is not None:
                        it.setSelected(True)
                        if first_item is None:
                            first_item = it
                if first_item is not None:
                    try:
                        self.list_lines.setCurrentItem(first_item, 0, QItemSelectionModel.NoUpdate)
                    except Exception:
                        self.list_lines.setCurrentItem(first_item)
                    try:
                        self.list_lines.scrollToItem(first_item, QAbstractItemView.PositionAtCenter)
                    except Exception:
                        pass
                self.list_lines.blockSignals(False)
                self.canvas.select_indices(moved_rows, center=False)
                try:
                    self._refresh_overlay_display(recs)
                    self.canvas.select_indices(moved_rows, center=False)
                except Exception:
                    pass
            except Exception:
                try:
                    self.list_lines.blockSignals(False)
                except Exception:
                    pass
