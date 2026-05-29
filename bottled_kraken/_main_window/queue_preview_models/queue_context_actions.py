from bottled_kraken.common import (
    Optional,
    QInputDialog,
    QMenu,
    QUEUE_COL_FILE,
    QUrl,
    Qt,
    TaskItem,
    ZENODO_URL,
)
class MainWindowQueueContextActionsMixin:
        def open_download_link(self):
            from PySide6.QtGui import QDesktopServices
            QDesktopServices.openUrl(QUrl(ZENODO_URL))
        def queue_context_menu(self, pos):
            menu = QMenu()
            start_ocr_act = menu.addAction(self._tr("act_start_ocr"))
            ai_revise_act = menu.addAction(self._tr("act_ai_revise"))
            menu.addSeparator()
            rename_act = menu.addAction(self._tr("act_rename"))
            delete_act = menu.addAction(self._tr("act_delete"))
            menu.addSeparator()
            check_all_act = menu.addAction(self._tr("queue_ctx_check_all"))
            uncheck_all_act = menu.addAction(self._tr("queue_ctx_uncheck_all"))
            action = menu.exec(self.queue_table.viewport().mapToGlobal(pos))
            if not action:
                return
            if action == start_ocr_act:
                self.start_ocr()
                return
            if action == ai_revise_act:
                self.run_ai_revision()
                return
            if action == check_all_act:
                self.check_all_queue_items()
                return
            if action == uncheck_all_act:
                self.uncheck_all_queue_items()
                return
            item = self.queue_table.itemAt(pos)
            if not item:
                return
            row = item.row()
            path = self.queue_table.item(row, QUEUE_COL_FILE).data(Qt.UserRole)
            task = next((t for t in self.queue_items if t.path == path), None)
            if action == rename_act and task:
                new_name, ok = QInputDialog.getText(
                    self,
                    self._tr("dlg_title_rename"),
                    self._tr("dlg_label_name"),
                    text=task.display_name
                )
                if ok:
                    task.display_name = new_name
                    self.queue_table.item(row, QUEUE_COL_FILE).setText(new_name)
            elif action == delete_act:
                self.delete_selected_queue_items()
        def check_all_queue_items(self):
            self._set_all_queue_checkmarks(True)
        def uncheck_all_queue_items(self):
            self._set_all_queue_checkmarks(False)
        def delete_selected_queue_items(self, reset_preview: bool = False):
            checked_rows = self._checked_queue_rows()
            rows = checked_rows if checked_rows else sorted(
                set(index.row() for index in self.queue_table.selectedIndexes()),
                reverse=True
            )
            if not rows:
                return
            rows = sorted(set(rows), reverse=True)
            first_removed_row = min(rows)
            current_preview_path = getattr(self, "_loaded_preview_path", None)
            if self.queue_table.currentRow() >= 0:
                item = self.queue_table.item(self.queue_table.currentRow(), QUEUE_COL_FILE)
                if item is not None:
                    current_preview_path = item.data(Qt.UserRole)
            removed_paths = []
            for row in rows:
                item = self.queue_table.item(row, QUEUE_COL_FILE)
                if item is None:
                    continue
                path = item.data(Qt.UserRole)
                removed_paths.append(path)
                self.queue_items = [i for i in self.queue_items if i.path != path]
                self.queue_table.removeRow(row)
            self._refresh_queue_numbers()
            self._update_queue_check_header()
            self._fit_queue_columns_exact()
            self._update_queue_hint()
            if len(self.queue_items) == 0:
                self.canvas.clear_all()
                self.canvas.set_overlay_enabled(False)
                self.list_lines.clear()
                self._loaded_preview_path = None
                self._set_progress_idle(0)
                return
            target_row = min(first_removed_row, self.queue_table.rowCount() - 1)
            if current_preview_path and current_preview_path not in removed_paths:
                for row in range(self.queue_table.rowCount()):
                    item = self.queue_table.item(row, QUEUE_COL_FILE)
                    if item is not None and item.data(Qt.UserRole) == current_preview_path:
                        target_row = row
                        break
            target_item = self.queue_table.item(target_row, QUEUE_COL_FILE)
            if target_item is None:
                return
            target_path = target_item.data(Qt.UserRole)
            self.queue_table.setCurrentCell(target_row, QUEUE_COL_FILE)
            self.queue_table.selectRow(target_row)
            if target_path:
                self.preview_image(target_path, persist_current=False)
        def clear_queue(self):
            self.queue_items.clear()
            self.queue_table.setRowCount(0)
            self._update_queue_check_header()
            self.canvas.clear_all()
            self.canvas.set_overlay_enabled(False)
            self.list_lines.clear()
            self._set_progress_idle(0)
            self._fit_queue_columns_exact()
            self._update_queue_hint()
            self._cleanup_temp_dirs()
            self._log(self._tr_log("log_queue_cleared"))
        def _task_by_path(self, path: Optional[str]) -> Optional[TaskItem]:
            if not path:
                return None
            return next((i for i in self.queue_items if i.path == path), None)
        def _loaded_preview_task(self) -> Optional[TaskItem]:
            return self._task_by_path(getattr(self, "_loaded_preview_path", None))
        def _persist_loaded_preview_bboxes(self):
            task = self._loaded_preview_task()
            if task and task.results:
                self._persist_live_canvas_bboxes(task)
