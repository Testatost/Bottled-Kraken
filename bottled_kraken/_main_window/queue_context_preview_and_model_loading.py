"""Mixin für MainWindow: queue context preview and model loading."""
from ..shared import *
from ..ui_components import *
from ..workers import *
from ..dialogs import *
from ..image_edit import *

class MainWindowQueueContextPreviewAndModelLoadingMixin:
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
        # Priorität: Checkmarks vor Auswahl
        rows = checked_rows if checked_rows else sorted(
            set(index.row() for index in self.queue_table.selectedIndexes()),
            reverse=True
        )
        if not rows:
            return
        rows = sorted(set(rows), reverse=True)
        current_preview_path = None
        if self.queue_table.currentRow() >= 0:
            current_preview_path = self.queue_table.item(self.queue_table.currentRow(), QUEUE_COL_FILE).data(
                Qt.UserRole)
        removed_paths = []
        for row in rows:
            path = self.queue_table.item(row, QUEUE_COL_FILE).data(Qt.UserRole)
            removed_paths.append(path)
            self.queue_items = [i for i in self.queue_items if i.path != path]
            self.queue_table.removeRow(row)
        if len(self.queue_items) == 0:
            self.canvas.clear_all()
            self.canvas.set_overlay_enabled(False)
            self.list_lines.clear()
            self._set_progress_idle(0)
        else:
            if current_preview_path and current_preview_path in removed_paths:
                self.queue_table.selectRow(0)
                p = self.queue_table.item(0, QUEUE_COL_FILE).data(Qt.UserRole)
                self.preview_image(p)
        self._refresh_queue_numbers()
        self._update_queue_check_header()
        self._fit_queue_columns_exact()
        self._update_queue_hint()
        if reset_preview:
            self.canvas.clear_all()
            self.canvas.set_overlay_enabled(False)
            self.list_lines.clear()
            self._set_progress_idle(0)

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

    def preview_image(self, path: str):
        try:
            im = Image.open(path)
            self.canvas.load_pil_image(im)
            self.list_lines.clear()
            item = next((i for i in self.queue_items if i.path == path), None)
            if item and item.status == STATUS_DONE and item.results:
                self.load_results(path)
            else:
                self.canvas.set_overlay_enabled(False)
        except Exception as e:
            QMessageBox.warning(self, self._tr("err_title"), self._tr("err_load", str(e)))

    def load_results(self, path: str):
        item = next((i for i in self.queue_items if i.path == path), None)
        if not item or not item.results:
            return
        text, kr_records, im, recs = item.results
        preview_im = _load_image_color(path)
        self.canvas.load_pil_image(preview_im)
        self.canvas.set_overlay_enabled(item.status == STATUS_DONE)
        if self.show_overlay:
            self.canvas.draw_overlays(recs)
        self._populate_lines_list(recs)
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
            if item and item.status == STATUS_DONE:
                self.load_results(path)
            else:
                self.preview_image(path)

    def on_queue_double_click(self, row, col):
        path = self.queue_table.item(row, QUEUE_COL_FILE).data(Qt.UserRole)
        self.preview_image(path)

    def choose_rec_model(self):
        start_dir = self.last_rec_model_dir or KRAKEN_MODELS_DIR or os.getcwd()
        p, _ = QFileDialog.getOpenFileName(
            self,
            self._tr("dlg_choose_rec"),
            start_dir,
            self._tr("dlg_filter_model")
        )
        if p:
            self.model_path = p
            self.last_rec_model_dir = os.path.dirname(p)
            self.settings.setValue("paths/last_rec_model_dir", self.last_rec_model_dir)
            name = os.path.basename(p)
            self.btn_rec_model.setText(self._tr("btn_rec_model_value", name))
            self.status_bar.showMessage(self._tr("msg_loaded_rec", name))
            self._update_models_menu_labels()
            self._update_model_clear_buttons()

    def choose_seg_model(self):
        start_dir = self.last_seg_model_dir or KRAKEN_MODELS_DIR or os.getcwd()
        p, _ = QFileDialog.getOpenFileName(
            self,
            self._tr("dlg_choose_seg"),
            start_dir,
            self._tr("dlg_filter_model")
        )
        if p:
            self.seg_model_path = p
            self.last_seg_model_dir = os.path.dirname(p)
            self.settings.setValue("paths/last_seg_model_dir", self.last_seg_model_dir)
            name = os.path.basename(p)
            self.btn_seg_model.setText(self._tr("btn_seg_model_value", name))
            self.status_bar.showMessage(self._tr("msg_loaded_seg", name))
            self._update_models_menu_labels()
            self._update_model_clear_buttons()

    def _update_model_clear_buttons(self):
        has_rec = bool(self.model_path)
        has_seg = bool(self.seg_model_path)
        if hasattr(self, "btn_rec_clear"):
            self.btn_rec_clear.setEnabled(has_rec)
        if hasattr(self, "btn_seg_clear"):
            self.btn_seg_clear.setEnabled(has_seg)
        if hasattr(self, "act_clear_rec"):
            self.act_clear_rec.setEnabled(has_rec)
        if hasattr(self, "act_clear_seg"):
            self.act_clear_seg.setEnabled(has_seg)

    def clear_rec_model(self):
        self.model_path = ""
        self.btn_rec_model.setText(self._tr("btn_rec_model_empty"))
        self.status_bar.showMessage(self._tr("msg_loaded_rec", "-"))
        self._update_models_menu_labels()
        self._update_model_clear_buttons()

    def clear_seg_model(self):
        self.seg_model_path = ""
        self.btn_seg_model.setText(self._tr("btn_seg_model_empty"))
        self.status_bar.showMessage(self._tr("msg_loaded_seg", "-"))
        self._update_models_menu_labels()
        self._update_model_clear_buttons()

    def _log(self, msg: str):
        ts = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        line = f"[{ts}] {msg}"
        try:
            self.log_edit.appendPlainText(line)
        except Exception:
            pass

    def toggle_log_area(self, checked: bool):
        self.log_visible = bool(checked)
        self.log_edit.setVisible(self.log_visible)
        if hasattr(self, "act_toggle_log"):
            self.act_toggle_log.setChecked(checked)
            self.act_toggle_log.setText(
                self._tr("log_toggle_hide") if checked else self._tr("log_toggle_show")
            )
        if hasattr(self, "btn_toggle_log"):
            self.btn_toggle_log.setText(
                self._tr("log_toggle_hide") if checked else self._tr("log_toggle_show")
            )

    def export_log_txt(self):
        base_dir = self.current_export_dir or os.getcwd()
        dest_path, _ = QFileDialog.getSaveFileName(
            self,
            self._tr("dlg_save_log"),
            os.path.join(base_dir, "ocr_log.txt"),
            self._tr("dlg_filter_txt")
        )
        if not dest_path:
            return
        if not dest_path.lower().endswith(".txt"):
            dest_path += ".txt"
        try:
            with open(dest_path, "w", encoding="utf-8") as f:
                f.write(self.log_edit.toPlainText())
            self._log(self._tr_log("log_export_log_done", dest_path))
            self.status_bar.showMessage(self._tr("msg_exported", os.path.basename(dest_path)))
        except Exception as e:
            QMessageBox.critical(self, self._tr("err_title"), str(e))
    def _read_import_lines_file(self, file_path: str) -> List[Any]:
        def _coerce_import_bbox(obj: Any) -> Optional[Tuple[int, int, int, int]]:
            bbox = obj.get("bbox") if isinstance(obj, dict) else None
            if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
                try:
                    x0, y0, x1, y1 = [int(round(float(v))) for v in bbox]
                    if x1 > x0 and y1 > y0:
                        return x0, y0, x1, y1
                except Exception:
                    pass
            try:
                x = obj.get("x")
                y = obj.get("y")
                w = obj.get("width")
                h = obj.get("height")
                if None not in (x, y, w, h):
                    x, y, w, h = [int(round(float(v))) for v in (x, y, w, h)]
                    if w > 0 and h > 0:
                        return x, y, x + w, y + h
            except Exception:
                pass
            return None

        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                raw_lines = f.read().splitlines()
            structured = []
            for ln in raw_lines:
                s = ln.strip()
                if not s or s.startswith("#"):
                    continue
                parts = ln.split("	", 5)
                if len(parts) >= 6:
                    try:
                        text_value = json.loads(parts[5])
                    except Exception:
                        text_value = parts[5]
                    txt = str(text_value).strip()
                    if not txt:
                        continue
                    entry = {
                        "idx": int(parts[0]) if parts[0].strip().lstrip("-").isdigit() else None,
                        "text": txt,
                        "x": parts[1].strip() or None,
                        "y": parts[2].strip() or None,
                        "width": parts[3].strip() or None,
                        "height": parts[4].strip() or None,
                    }
                    structured.append({"text": txt, "bbox": _coerce_import_bbox(entry)})
            if structured:
                return structured
            return [ln.strip() for ln in raw_lines if ln.strip()]
        if ext == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and all(isinstance(x, str) for x in data):
                return [str(x).strip() for x in data if str(x).strip()]
            if isinstance(data, dict):
                lines = data.get("lines")
                if isinstance(lines, list):
                    out = []
                    for item in lines:
                        if isinstance(item, dict):
                            txt = str(item.get("text", "") or "").strip()
                            if txt:
                                out.append({"text": txt, "bbox": _coerce_import_bbox(item)})
                        elif isinstance(item, str):
                            txt = item.strip()
                            if txt:
                                out.append(txt)
                    if out:
                        return out
                rows = data.get("rows")
                if isinstance(rows, list):
                    out = []
                    for row in rows:
                        if isinstance(row, list):
                            txt = " ".join(str(x).strip() for x in row if str(x).strip()).strip()
                            if txt:
                                out.append(txt)
                        elif isinstance(row, str):
                            txt = row.strip()
                            if txt:
                                out.append(txt)
                    return out
        raise ValueError(self._tr("warn_import_unsupported_format", file_path))
    def _apply_imported_lines_to_task(self, task: TaskItem, lines: List[Any]):
        entries = []
        for line in lines:
            if isinstance(line, dict):
                txt = str(line.get("text", "") or "").strip()
                if txt:
                    entries.append({"text": txt, "bbox": line.get("bbox")})
            else:
                txt = str(line).strip()
                if txt:
                    entries.append({"text": txt, "bbox": None})
        if not entries:
            raise ValueError(self._tr("warn_import_no_usable_lines"))
        if task.results:
            old_text, old_kr, old_im, old_recs = task.results
            if len(old_recs) == len(entries):
                recs = [
                    RecordView(i, entry["text"], entry["bbox"] if entry["bbox"] else old_recs[i].bbox)
                    for i, entry in enumerate(entries)
                ]
                im = old_im
                kr = old_kr
            else:
                im = _load_image_gray(task.path)
                kr = []
                recs = [RecordView(i, entry["text"], entry["bbox"]) for i, entry in enumerate(entries)]
        else:
            im = _load_image_gray(task.path)
            kr = []
            recs = [RecordView(i, entry["text"], entry["bbox"]) for i, entry in enumerate(entries)]
        text = "\n".join(entry["text"] for entry in entries).strip()
        task.results = (text, kr, im, recs)
        task.preset_bboxes = [rv.bbox for rv in recs]
        task.status = STATUS_DONE
        task.edited = True
        self._update_queue_row(task.path)
        cur = self._current_task()
        if cur and cur.path == task.path:
            self._sync_ui_after_recs_change(task, keep_row=0)
            if self.list_lines.count() > 0:
                self.list_lines.setCurrentRow(0)
                self.list_lines.setFocus()
                self.canvas.select_idx(0)

    def _match_import_files_to_tasks(self, tasks: List[TaskItem], import_files: List[str]) -> Dict[str, str]:
        file_map = {}
        for fp in import_files:
            stem = os.path.splitext(os.path.basename(fp))[0].lower()
            file_map[stem] = fp
        matches = {}
        for task in tasks:
            path_stem = os.path.splitext(os.path.basename(task.path))[0].lower()
            display_stem = os.path.splitext(task.display_name)[0].lower()
            normalized_display = (
                display_stem
                .replace(" – seite ", "_p")
                .replace(" - seite ", "_p")
                .replace(" seite ", "_p")
            )
            candidates = {
                path_stem,
                display_stem,
                normalized_display,
            }
            for c in candidates:
                if c in file_map:
                    matches[task.path] = file_map[c]
                    break
        return matches

    def import_lines_for_current_image(self):
        task = self._current_task()
        if not task:
            QMessageBox.information(self, self._tr("info_title"), self._tr("info_no_current_image_loaded"))
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self._tr("dlg_import_lines_current"),
            "",
            "Text/JSON (*.txt *.json)"
        )
        if not file_path:
            return
        try:
            lines = self._read_import_lines_file(file_path)
            self._apply_imported_lines_to_task(task, lines)
        except Exception as e:
            QMessageBox.warning(self, self._tr("warn_title"), str(e))

    def import_lines_for_selected_images(self):
        tasks = self._checked_queue_tasks()
        if not tasks:
            tasks = self._selected_queue_tasks()
        if not tasks:
            QMessageBox.information(self, self._tr("info_title"), self._tr("info_no_images_selected_or_marked"))
            return
        files, _ = QFileDialog.getOpenFileNames(
            self,
            self._tr("dlg_import_lines_selected"),
            "",
            "Text/JSON (*.txt *.json)"
        )
        if not files:
            return
        matches = self._match_import_files_to_tasks(tasks, files)
        if not matches:
            QMessageBox.warning(
                self,
                self._tr("warn_title"),
                self._tr("warn_no_matching_import_for_selected")
            )
            return
        for task in tasks:
            fp = matches.get(task.path)
            if not fp:
                continue
            try:
                lines = self._read_import_lines_file(fp)
                self._apply_imported_lines_to_task(task, lines)
            except Exception as e:
                self._log(self._tr_log("log_import_error", task.display_name, e))
