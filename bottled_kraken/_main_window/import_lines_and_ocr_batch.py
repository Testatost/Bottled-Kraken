"""Mixin für MainWindow: import lines and ocr batch."""
from ..shared import *
from ..ui_components import *
from ..workers import *
from ..dialogs import *
from ..image_edit import *

class MainWindowImportLinesAndOcrBatchMixin:
    def import_lines_for_all_images(self):
        if not self.queue_items:
            QMessageBox.information(self, self._tr("info_title"), self._tr("info_no_images_loaded"))
            return
        files, _ = QFileDialog.getOpenFileNames(
            self,
            self._tr("dlg_import_lines_all"),
            "",
            "Text/JSON (*.txt *.json)"
        )
        if not files:
            return
        matches = self._match_import_files_to_tasks(self.queue_items, files)
        if not matches:
            QMessageBox.warning(
                self,
                self._tr("warn_title"),
                self._tr("warn_no_matching_import_for_loaded")
            )
            return
        for task in self.queue_items:
            fp = matches.get(task.path)
            if not fp:
                continue
            try:
                lines = self._read_import_lines_file(fp)
                self._apply_imported_lines_to_task(task, lines)
            except Exception as e:
                self._log(self._tr_log("log_import_error", task.display_name, e))

    def start_ocr(self):
        if not self.model_path or not os.path.exists(self.model_path):
            QMessageBox.critical(self, self._tr("err_title"), self._tr("warn_need_rec"))
            return
        if not self.seg_model_path or not os.path.exists(self.seg_model_path):
            QMessageBox.critical(self, self._tr("err_title"), self._tr("warn_blla_model_missing"))
            return
        checked_tasks = self._checked_queue_tasks()
        selected_tasks = self._selected_queue_tasks()
        # Priorität: Checkmarks vor Auswahl
        target_tasks = checked_tasks if checked_tasks else selected_tasks
        # Falls in der Queue nichts markiert/ausgewählt ist:
        # auf die aktuell geladene Datei zurückfallen,
        # damit Re-OCR nach Zeilenbearbeitung trotzdem funktioniert.
        if not target_tasks:
            current_task = self._current_task()
            if current_task and current_task.status in (STATUS_WAITING, STATUS_ERROR, STATUS_DONE):
                target_tasks = [current_task]
        if target_tasks:
            tasks = []
            for it in target_tasks:
                if it.status in (STATUS_WAITING, STATUS_ERROR, STATUS_DONE):
                    # WICHTIG:
                    # Beim normalen "Start Kraken OCR" alte Split-/Overlay-Boxen ignorieren
                    it.preset_bboxes = []
                    if it.status != STATUS_WAITING:
                        it.status = STATUS_WAITING
                        it.results = None
                        it.edited = False
                        it.undo_stack.clear()
                        it.redo_stack.clear()
                        self._update_queue_row(it.path)
                    tasks.append(it)
        else:
            tasks = [i for i in self.queue_items if i.status == STATUS_WAITING]
        if not tasks:
            QMessageBox.information(self, self._tr("info_title"), self._tr("warn_queue_empty"))
            return
        caps = self._gpu_capabilities()
        ok, _ = caps.get(self.device_str, (False, ""))
        if not ok:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("msg_hw_not_available"))
            self.device_str = "cpu"
            if "cpu" in self.hw_actions:
                self.hw_actions["cpu"].setChecked(True)
        self.act_play.setEnabled(False)
        self.act_stop.setEnabled(True)
        self._set_progress_busy()
        paths = [t.path for t in tasks]
        job = OCRJob(
            input_paths=paths,
            recognition_model_path=self.model_path,
            segmentation_model_path=self.seg_model_path,
            device=self.device_str,
            reading_direction=self.reading_direction,
            export_format="pdf",
            export_dir=self.current_export_dir,
            preset_bboxes_by_path={},  # normales Re-OCR ohne alte Split-Boxen
        )
        self.worker = OCRWorker(job)
        self.worker.file_started.connect(self.on_file_started)
        self.worker.file_done.connect(self.on_file_done)
        self.worker.file_error.connect(self.on_file_error)
        self.worker.progress.connect(self.on_progress_update)
        self.worker.finished_batch.connect(self.on_batch_finished)
        self.worker.failed.connect(self.on_failed)
        self.worker.device_resolved.connect(self.on_device_resolved)
        self.worker.gpu_info.connect(self.on_gpu_info)
        self._log(self._tr_log("log_ocr_started", len(paths), self.device_str, self.reading_direction))
        self.worker.start()

    def on_device_resolved(self, dev_str: str):
        self.status_bar.showMessage(self._tr("msg_using_device", dev_str))

    def on_gpu_info(self, info: str):
        self.status_bar.showMessage(self._tr("msg_detected_gpu", info))

    def stop_ocr(self):
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self._log(self._tr_log("log_stop_requested"))
            self.status_bar.showMessage(self._tr("msg_stopping"))

    def on_file_started(self, path):
        item = next((i for i in self.queue_items if i.path == path), None)
        if item:
            item.status = STATUS_PROCESSING
            self._update_queue_row(path)
            self._log(self._tr_log("log_file_started", os.path.basename(path)))

    def on_file_done(self, path, text, kr_records, im, recs):
        item = next((i for i in self.queue_items if i.path == path), None)
        if item:
            # Normales OCR-Ergebnis direkt übernehmen
            text = "\n".join(rv.text for rv in recs).strip()
            item.status = STATUS_DONE
            item.results = (text, kr_records, im, recs)
            item.edited = False
            item.undo_stack.clear()
            item.redo_stack.clear()
            self._update_queue_row(path)
            # nur nach erfolgreichem Anwenden leeren
            item.preset_bboxes = []
            if self.queue_table.currentRow() >= 0:
                cur_path = self.queue_table.item(self.queue_table.currentRow(), QUEUE_COL_FILE).data(Qt.UserRole)
                if cur_path == path:
                    self.load_results(path)
                    if self.list_lines.count() > 0:
                        self.list_lines.setCurrentRow(0)
                        self.list_lines.setFocus()
                        self.canvas.select_idx(0)
            self._log(self._tr_log("log_file_done", os.path.basename(path), len(recs)))

    def on_file_error(self, path, msg):
        item = next((i for i in self.queue_items if i.path == path), None)
        if item:
            item.status = STATUS_ERROR
            self._update_queue_row(path)
            self._log(self._tr_log("log_file_error", os.path.basename(path), msg))

    def on_batch_finished(self):
        self.act_play.setEnabled(True)
        self.act_stop.setEnabled(False)
        self.status_bar.showMessage(self._tr("msg_finished"))
        self.progress_bar.setValue(100)
        if self.worker:
            try:
                self.worker.deleteLater()
            except Exception:
                pass
            self.worker = None
        try:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    def on_failed(self, msg):
        QMessageBox.critical(self, self._tr("err_title"), msg)
        self.act_play.setEnabled(True)
        self.act_stop.setEnabled(False)
        self._set_progress_idle(0)
        if self.worker:
            try:
                self.worker.deleteLater()
            except Exception:
                pass
            self.worker = None
        try:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    def _update_queue_row(self, path):
        for row in range(self.queue_table.rowCount()):
            item0 = self.queue_table.item(row, QUEUE_COL_FILE)
            if item0 and item0.data(Qt.UserRole) == path:
                status_item = self.queue_table.item(row, QUEUE_COL_STATUS)
                task = next((i for i in self.queue_items if i.path == path), None)
                if task and status_item:
                    status_enum = task.status
                    status_icon = STATUS_ICONS[status_enum]
                    status_key = {
                        STATUS_WAITING: "status_waiting",
                        STATUS_PROCESSING: "status_processing",
                        STATUS_DONE: "status_done",
                        STATUS_ERROR: "status_error",
                        STATUS_AI_PROCESSING: "status_ai_processing",
                        STATUS_EXPORTING: "status_exporting",
                        STATUS_VOICE_RECORDING: "status_voice_recording",
                    }[status_enum]
                    status_item.setText(f"{status_icon} {self._tr(status_key)}")
                    if status_enum == STATUS_DONE:
                        status_item.setForeground(QBrush(QColor("green")))
                    elif status_enum == STATUS_VOICE_RECORDING:
                        status_item.setForeground(QBrush(QColor(180, 0, 180)))
                    elif status_enum == STATUS_ERROR:
                        status_item.setForeground(QBrush(QColor("red")))
                    elif status_enum == STATUS_AI_PROCESSING:
                        status_item.setForeground(QBrush(QColor(128, 0, 128)))
                    elif status_enum == STATUS_EXPORTING:
                        status_item.setForeground(QBrush(QColor(180, 120, 0)))
                    else:
                        status_item.setForeground(QBrush(QColor("blue")))
                break

    def _current_task(self) -> Optional[TaskItem]:
        if self.queue_table.currentRow() < 0:
            return None
        path = self.queue_table.item(self.queue_table.currentRow(), QUEUE_COL_FILE).data(Qt.UserRole)
        return next((i for i in self.queue_items if i.path == path), None)

    def _update_task_preset_bboxes(self, task: TaskItem):
        if not task or not task.results:
            task.preset_bboxes = []
            return
        _, _, _, recs = task.results
        task.preset_bboxes = [rv.bbox for rv in recs]

    def _current_recs_for_ai(self, task: TaskItem) -> List[RecordView]:
        if not task or not task.results:
            return []
        # Sicherheitshalber die aktuell sichtbaren Canvas-Boxen zuerst ins Task-Modell ziehen
        self._persist_live_canvas_bboxes(task)
        _, _, _, recs = task.results
        out = []
        for i, rv in enumerate(recs):
            out.append(
                RecordView(
                    i,
                    rv.text,
                    tuple(rv.bbox) if rv.bbox else None
                )
            )
        return out

    def on_line_selected(self, current, previous=None):
        row = self.list_lines.currentRow()
        task = self._current_task()
        if not task or not task.results:
            return
        rows = self._selected_line_rows()
        if rows:
            self.canvas.select_indices(rows, center=False)
            return
        if row < 0:
            self.canvas.select_indices([], center=False)
            return
        _, _, _, recs = task.results
        if 0 <= row < len(recs):
            self.canvas.select_idx(row)

    def on_lines_selection_changed(self):
        task = self._current_task()
        if not task or not task.results:
            return
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
        pending_new_rows = list(getattr(self.list_lines, "_pending_reselect_new_rows", []))
        selected_sources = list(getattr(self.list_lines, "_pending_reselect_source_rows", []))
        keep_row = max(0, min(len(recs) - 1, int(current_row_after_drop)))
        self._reorder_lines_keep_box_slots(task, order, keep_row=keep_row)
        if pending_new_rows:
            new_rows = [r for r in pending_new_rows if 0 <= r < len(recs)]
        elif selected_sources:
            source_set = set(int(i) for i in selected_sources)
            new_rows = [new_row for new_row, old_row in enumerate(order) if old_row in source_set]
        else:
            self.list_lines._pending_reselect_source_rows = []
            self.list_lines._pending_reselect_new_rows = []
            return
        if not new_rows:
            self.list_lines._pending_reselect_source_rows = []
            self.list_lines._pending_reselect_new_rows = []
            return
        def _reselect_rows():
            self.list_lines.blockSignals(True)
            try:
                selected_set = set(new_rows)
                for row in range(self.list_lines.count()):
                    item = self.list_lines.row_item(row)
                    if item is not None:
                        item.setSelected(row in selected_set)
                first_item = self.list_lines.row_item(new_rows[0])
                if first_item is not None:
                    try:
                        self.list_lines.setCurrentItem(first_item, 0, QItemSelectionModel.NoUpdate)
                    except Exception:
                        self.list_lines.setCurrentItem(first_item)
                    self.list_lines.scrollToItem(first_item, QAbstractItemView.PositionAtCenter)
                self.list_lines.setFocus()
            finally:
                self.list_lines.blockSignals(False)
        _reselect_rows()
        QTimer.singleShot(0, _reselect_rows)
        self.list_lines._pending_reselect_source_rows = []
        self.list_lines._pending_reselect_new_rows = []
        self.on_lines_selection_changed()

    def lines_context_menu(self, pos):
        item = self.list_lines.itemAt(pos)
        if item is None:
            return
        row = self.list_lines.row(item)
        menu = QMenu()
        act_swap = menu.addAction(self._tr("line_menu_swap_with"))
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
            if self.show_overlay:
                self.canvas.draw_overlays(recs)
        else:
            self.canvas.clear_all()
            self.canvas.set_overlay_enabled(False)

    def _move_line(self, task: TaskItem, row: int, direction: int):
        if not task.results:
            return
        _, _, _, recs = task.results
        new_row = row + direction
        if not (0 <= row < len(recs)) or not (0 <= new_row < len(recs)):
            return
        self._push_undo(task)
        recs[row], recs[new_row] = recs[new_row], recs[row]
        task.edited = True
        self._sync_ui_after_recs_change(task, keep_row=new_row)"""Mixin für MainWindow: import lines and ocr batch."""
from ..shared import *
from ..ui_components import *
from ..workers import *
from ..dialogs import *
from ..image_edit import *

class MainWindowImportLinesAndOcrBatchMixin:
    def import_lines_for_all_images(self):
        if not self.queue_items:
            QMessageBox.information(self, self._tr("info_title"), self._tr("info_no_images_loaded"))
            return
        files, _ = QFileDialog.getOpenFileNames(
            self,
            self._tr("dlg_import_lines_all"),
            "",
            "Text/JSON (*.txt *.json)"
        )
        if not files:
            return
        matches = self._match_import_files_to_tasks(self.queue_items, files)
        if not matches:
            QMessageBox.warning(
                self,
                self._tr("warn_title"),
                self._tr("warn_no_matching_import_for_loaded")
            )
            return
        for task in self.queue_items:
            fp = matches.get(task.path)
            if not fp:
                continue
            try:
                lines = self._read_import_lines_file(fp)
                self._apply_imported_lines_to_task(task, lines)
            except Exception as e:
                self._log(self._tr_log("log_import_error", task.display_name, e))

    def start_ocr(self):
        if not self.model_path or not os.path.exists(self.model_path):
            QMessageBox.critical(self, self._tr("err_title"), self._tr("warn_need_rec"))
            return
        if not self.seg_model_path or not os.path.exists(self.seg_model_path):
            QMessageBox.critical(self, self._tr("err_title"), self._tr("warn_blla_model_missing"))
            return
        checked_tasks = self._checked_queue_tasks()
        selected_tasks = self._selected_queue_tasks()
        # Priorität: Checkmarks vor Auswahl
        target_tasks = checked_tasks if checked_tasks else selected_tasks
        # Falls in der Queue nichts markiert/ausgewählt ist:
        # auf die aktuell geladene Datei zurückfallen,
        # damit Re-OCR nach Zeilenbearbeitung trotzdem funktioniert.
        if not target_tasks:
            current_task = self._current_task()
            if current_task and current_task.status in (STATUS_WAITING, STATUS_ERROR, STATUS_DONE):
                target_tasks = [current_task]
        if target_tasks:
            tasks = []
            for it in target_tasks:
                if it.status in (STATUS_WAITING, STATUS_ERROR, STATUS_DONE):
                    # WICHTIG:
                    # Beim normalen "Start Kraken OCR" alte Split-/Overlay-Boxen ignorieren
                    it.preset_bboxes = []
                    if it.status != STATUS_WAITING:
                        it.status = STATUS_WAITING
                        it.results = None
                        it.edited = False
                        it.undo_stack.clear()
                        it.redo_stack.clear()
                        self._update_queue_row(it.path)
                    tasks.append(it)
        else:
            tasks = [i for i in self.queue_items if i.status == STATUS_WAITING]
        if not tasks:
            QMessageBox.information(self, self._tr("info_title"), self._tr("warn_queue_empty"))
            return
        caps = self._gpu_capabilities()
        ok, _ = caps.get(self.device_str, (False, ""))
        if not ok:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("msg_hw_not_available"))
            self.device_str = "cpu"
            if "cpu" in self.hw_actions:
                self.hw_actions["cpu"].setChecked(True)
        self.act_play.setEnabled(False)
        self.act_stop.setEnabled(True)
        self._set_progress_busy()
        paths = [t.path for t in tasks]
        job = OCRJob(
            input_paths=paths,
            recognition_model_path=self.model_path,
            segmentation_model_path=self.seg_model_path,
            device=self.device_str,
            reading_direction=self.reading_direction,
            export_format="pdf",
            export_dir=self.current_export_dir,
            preset_bboxes_by_path={},  # normales Re-OCR ohne alte Split-Boxen
        )
        self.worker = OCRWorker(job)
        self.worker.file_started.connect(self.on_file_started)
        self.worker.file_done.connect(self.on_file_done)
        self.worker.file_error.connect(self.on_file_error)
        self.worker.progress.connect(self.on_progress_update)
        self.worker.finished_batch.connect(self.on_batch_finished)
        self.worker.failed.connect(self.on_failed)
        self.worker.device_resolved.connect(self.on_device_resolved)
        self.worker.gpu_info.connect(self.on_gpu_info)
        self._log(self._tr_log("log_ocr_started", len(paths), self.device_str, self.reading_direction))
        self.worker.start()

    def on_device_resolved(self, dev_str: str):
        self.status_bar.showMessage(self._tr("msg_using_device", dev_str))

    def on_gpu_info(self, info: str):
        self.status_bar.showMessage(self._tr("msg_detected_gpu", info))

    def stop_ocr(self):
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self._log(self._tr_log("log_stop_requested"))
            self.status_bar.showMessage(self._tr("msg_stopping"))

    def on_file_started(self, path):
        item = next((i for i in self.queue_items if i.path == path), None)
        if item:
            item.status = STATUS_PROCESSING
            self._update_queue_row(path)
            self._log(self._tr_log("log_file_started", os.path.basename(path)))

    def on_file_done(self, path, text, kr_records, im, recs):
        item = next((i for i in self.queue_items if i.path == path), None)
        if item:
            # Normales OCR-Ergebnis direkt übernehmen
            text = "\n".join(rv.text for rv in recs).strip()
            item.status = STATUS_DONE
            item.results = (text, kr_records, im, recs)
            item.edited = False
            item.undo_stack.clear()
            item.redo_stack.clear()
            self._update_queue_row(path)
            # nur nach erfolgreichem Anwenden leeren
            item.preset_bboxes = []
            if self.queue_table.currentRow() >= 0:
                cur_path = self.queue_table.item(self.queue_table.currentRow(), QUEUE_COL_FILE).data(Qt.UserRole)
                if cur_path == path:
                    self.load_results(path)
                    if self.list_lines.count() > 0:
                        self.list_lines.setCurrentRow(0)
                        self.list_lines.setFocus()
                        self.canvas.select_idx(0)
            self._log(self._tr_log("log_file_done", os.path.basename(path), len(recs)))

    def on_file_error(self, path, msg):
        item = next((i for i in self.queue_items if i.path == path), None)
        if item:
            item.status = STATUS_ERROR
            self._update_queue_row(path)
            self._log(self._tr_log("log_file_error", os.path.basename(path), msg))

    def on_batch_finished(self):
        self.act_play.setEnabled(True)
        self.act_stop.setEnabled(False)
        self.status_bar.showMessage(self._tr("msg_finished"))
        self.progress_bar.setValue(100)
        if self.worker:
            try:
                self.worker.deleteLater()
            except Exception:
                pass
            self.worker = None
        try:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    def on_failed(self, msg):
        QMessageBox.critical(self, self._tr("err_title"), msg)
        self.act_play.setEnabled(True)
        self.act_stop.setEnabled(False)
        self._set_progress_idle(0)
        if self.worker:
            try:
                self.worker.deleteLater()
            except Exception:
                pass
            self.worker = None
        try:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    def _update_queue_row(self, path):
        for row in range(self.queue_table.rowCount()):
            item0 = self.queue_table.item(row, QUEUE_COL_FILE)
            if item0 and item0.data(Qt.UserRole) == path:
                status_item = self.queue_table.item(row, QUEUE_COL_STATUS)
                task = next((i for i in self.queue_items if i.path == path), None)
                if task and status_item:
                    status_enum = task.status
                    status_icon = STATUS_ICONS[status_enum]
                    status_key = {
                        STATUS_WAITING: "status_waiting",
                        STATUS_PROCESSING: "status_processing",
                        STATUS_DONE: "status_done",
                        STATUS_ERROR: "status_error",
                        STATUS_AI_PROCESSING: "status_ai_processing",
                        STATUS_EXPORTING: "status_exporting",
                        STATUS_VOICE_RECORDING: "status_voice_recording",
                    }[status_enum]
                    status_item.setText(f"{status_icon} {self._tr(status_key)}")
                    if status_enum == STATUS_DONE:
                        status_item.setForeground(QBrush(QColor("green")))
                    elif status_enum == STATUS_VOICE_RECORDING:
                        status_item.setForeground(QBrush(QColor(180, 0, 180)))
                    elif status_enum == STATUS_ERROR:
                        status_item.setForeground(QBrush(QColor("red")))
                    elif status_enum == STATUS_AI_PROCESSING:
                        status_item.setForeground(QBrush(QColor(128, 0, 128)))
                    elif status_enum == STATUS_EXPORTING:
                        status_item.setForeground(QBrush(QColor(180, 120, 0)))
                    else:
                        status_item.setForeground(QBrush(QColor("blue")))
                break

    def _current_task(self) -> Optional[TaskItem]:
        if self.queue_table.currentRow() < 0:
            return None
        path = self.queue_table.item(self.queue_table.currentRow(), QUEUE_COL_FILE).data(Qt.UserRole)
        return next((i for i in self.queue_items if i.path == path), None)

    def _update_task_preset_bboxes(self, task: TaskItem):
        if not task or not task.results:
            task.preset_bboxes = []
            return
        _, _, _, recs = task.results
        task.preset_bboxes = [rv.bbox for rv in recs]

    def _current_recs_for_ai(self, task: TaskItem) -> List[RecordView]:
        if not task or not task.results:
            return []
        # Sicherheitshalber die aktuell sichtbaren Canvas-Boxen zuerst ins Task-Modell ziehen
        self._persist_live_canvas_bboxes(task)
        _, _, _, recs = task.results
        out = []
        for i, rv in enumerate(recs):
            out.append(
                RecordView(
                    i,
                    rv.text,
                    tuple(rv.bbox) if rv.bbox else None
                )
            )
        return out

    def on_line_selected(self, current, previous=None):
        row = self.list_lines.currentRow()
        task = self._current_task()
        if not task or not task.results:
            return
        rows = self._selected_line_rows()
        if rows:
            self.canvas.select_indices(rows, center=False)
            return
        if row < 0:
            self.canvas.select_indices([], center=False)
            return
        _, _, _, recs = task.results
        if 0 <= row < len(recs):
            self.canvas.select_idx(row)

    def on_lines_selection_changed(self):
        task = self._current_task()
        if not task or not task.results:
            return
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
        self._reorder_lines_keep_box_slots(task, order, keep_row=keep_row)

    def lines_context_menu(self, pos):
        item = self.list_lines.itemAt(pos)
        if item is None:
            return
        row = self.list_lines.row(item)
        menu = QMenu()
        act_swap = menu.addAction(self._tr("line_menu_swap_with"))
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
            if self.show_overlay:
                self.canvas.draw_overlays(recs)
        else:
            self.canvas.clear_all()
            self.canvas.set_overlay_enabled(False)

    def _move_line(self, task: TaskItem, row: int, direction: int):
        if not task.results:
            return
        _, _, _, recs = task.results
        new_row = row + direction
        if not (0 <= row < len(recs)) or not (0 <= new_row < len(recs)):
            return
        self._push_undo(task)
        recs[row], recs[new_row] = recs[new_row], recs[row]
        task.edited = True
        self._sync_ui_after_recs_change(task, keep_row=new_row)
