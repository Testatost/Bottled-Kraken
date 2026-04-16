"""Mixin für MainWindow: project persistence and queue selection."""
from ..shared import *
from ..ui_components import *
from ..workers import *
from ..dialogs import *
from ..image_edit import *

class MainWindowProjectPersistenceAndQueueSelectionMixin:
    def _remap_missing_project_files(self):
        missing = [t for t in self.queue_items if not os.path.exists(t.path)]
        if not missing:
            return
        answer = QMessageBox.question(
            self,
            self._tr("warn_title"),
            "Einige Originaldateien wurden nicht gefunden.\n\n"
            "Möchten Sie einen neuen Ordner auswählen, damit die Dateien neu zugeordnet werden?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if answer != QMessageBox.Yes:
            return
        new_base_dir = QFileDialog.getExistingDirectory(
            self,
            "Neuen Basisordner für Originaldateien wählen",
            self.current_export_dir or os.getcwd()
        )
        if not new_base_dir:
            return
        unresolved = []
        for task in missing:
            candidates = []
            rel = (task.relative_path or "").strip()
            old_path = (task.path or "").strip()
            # 1) echter relativer Pfad innerhalb des neuen Basisordners
            if rel:
                candidates.append(os.path.normpath(os.path.join(new_base_dir, rel)))
            # 2) nur Dateiname als Fallback
            if old_path:
                candidates.append(os.path.normpath(os.path.join(new_base_dir, os.path.basename(old_path))))
            # doppelte Kandidaten vermeiden
            seen = set()
            final_candidates = []
            for c in candidates:
                norm = os.path.normpath(c)
                if norm not in seen:
                    seen.add(norm)
                    final_candidates.append(norm)
            found = None
            for c in final_candidates:
                if os.path.exists(c):
                    found = c
                    break
            if found:
                task.path = found
                if not task.relative_path:
                    task.relative_path = os.path.basename(found)
            else:
                unresolved.append(task.display_name)
        if unresolved:
            QMessageBox.warning(
                self,
                self._tr("warn_title"),
                "Einige Dateien konnten weiterhin nicht gefunden werden:\n\n" + "\n".join(unresolved[:20])
            )

    def _load_project_dict(self, data: dict):
        progress = QProgressDialog("Projekt wird geladen...", None, 0, 100, self)
        progress.setWindowTitle(self._tr("dlg_project_loading_title"))
        progress.setWindowModality(Qt.ApplicationModal)
        progress.setCancelButton(None)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()
        self._process_ui()
        try:
            self.clear_queue()
            progress.setLabelText("Einstellungen werden wiederhergestellt...")
            progress.setValue(5)
            self._process_ui()
            settings = data.get("settings", {})
            self.current_lang = settings.get("language", self.current_lang)
            self.reading_direction = int(settings.get("reading_direction", self.reading_direction))
            self.device_str = settings.get("device", self.device_str)
            self.show_overlay = bool(settings.get("show_overlay", self.show_overlay))
            self.current_theme = settings.get("theme", self.current_theme)
            self.model_path = settings.get("model_path", self.model_path)
            self.seg_model_path = settings.get("seg_model_path", self.seg_model_path)
            self.current_export_dir = settings.get("current_export_dir", self.current_export_dir)
            self.ai_model_id = settings.get("ai_model_id", self.ai_model_id)
            self.last_rec_model_dir = settings.get("last_rec_model_dir", self.last_rec_model_dir)
            self.last_seg_model_dir = settings.get("last_seg_model_dir", self.last_seg_model_dir)
            self.whisper_models_base_dir = self._default_whisper_base_dir()
            self.whisper_model_path = self._default_whisper_model_dir()
            if not os.path.isfile(os.path.join(self.whisper_model_path, "model.bin")):
                self.whisper_model_path = ""
            self.whisper_model_name = os.path.basename(self.whisper_model_path) if self.whisper_model_path else ""
            self.whisper_model_loaded = bool(self.whisper_model_path)
            self.whisper_selected_input_device = settings.get("whisper_selected_input_device",
                                                              self.whisper_selected_input_device)
            self.whisper_selected_input_device_label = settings.get(
                "whisper_selected_input_device_label",
                self.whisper_selected_input_device_label
            )
            self._scan_whisper_models()
            self._rebuild_whisper_model_submenu()
            self._update_whisper_menu_status()
            queue_data = data.get("queue_items", [])
            self.queue_items = []
            total = max(1, len(queue_data))
            progress.setLabelText("Projektdaten werden eingelesen...")
            progress.setValue(10)
            self._process_ui()
            for idx, task_data in enumerate(queue_data, start=1):
                task = self._task_from_dict(task_data)
                self.queue_items.append(task)
                pct = 10 + int((idx / total) * 35)
                progress.setLabelText(f"Projektobjekte werden eingelesen... ({idx}/{total})")
                progress.setValue(pct)
                self._process_ui()
            progress.setLabelText("Dateipfade werden geprüft...")
            progress.setValue(50)
            self._process_ui()
            self._remap_missing_project_files()
            progress.setLabelText("Wartebereich wird aufgebaut...")
            self._process_ui()
            for idx, task in enumerate(self.queue_items, start=1):
                row = self.queue_table.rowCount()
                self.queue_table.insertRow(row)
                num_item = QTableWidgetItem(str(row + 1))
                num_item.setTextAlignment(Qt.AlignCenter)
                num_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                name_item = QTableWidgetItem(task.display_name)
                name_item.setData(Qt.UserRole, task.path)
                name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
                status_item = QTableWidgetItem()
                status_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.queue_table.setItem(row, QUEUE_COL_NUM, num_item)
                self.queue_table.setCellWidget(row, QUEUE_COL_CHECK, self._make_queue_checkbox_widget(False))
                self.queue_table.setItem(row, QUEUE_COL_FILE, name_item)
                self.queue_table.setItem(row, QUEUE_COL_STATUS, status_item)
                self._update_queue_row(task.path)
                pct = 50 + int((idx / total) * 35)
                progress.setLabelText(f"Wartebereich wird aufgebaut... ({idx}/{total})")
                progress.setValue(pct)
                self._process_ui()
            progress.setLabelText("Oberfläche wird aktualisiert...")
            progress.setValue(90)
            self._process_ui()
            self.apply_theme(self.current_theme)
            self.retranslate_ui()
            current_row = int(settings.get("current_row", 0))
            if self.queue_table.rowCount() > 0:
                current_row = max(0, min(self.queue_table.rowCount() - 1, current_row))
                self.queue_table.selectRow(current_row)
                path = self.queue_table.item(current_row, QUEUE_COL_FILE).data(Qt.UserRole)
                task = next((i for i in self.queue_items if i.path == path), None)
                if task:
                    if os.path.exists(path):
                        if task.status == STATUS_DONE and task.results:
                            self.load_results(path)
                        else:
                            self.preview_image(path)
                    else:
                        QMessageBox.warning(
                            self,
                            self._tr("warn_title"),
                            self._tr("warn_project_file_missing", path)
                        )
            self._refresh_queue_numbers()
            self._fit_queue_columns_exact()
            self._update_queue_hint()
            self._update_models_menu_labels()
            self._update_model_clear_buttons()
            progress.setLabelText("Projekt abgeschlossen.")
            progress.setValue(100)
            self._process_ui()
        finally:
            progress.close()

    def save_project_as(self):
        base_dir = self.current_export_dir or os.getcwd()
        path, _ = QFileDialog.getSaveFileName(
            self,
            self._tr("menu_project_save_as"),
            os.path.join(base_dir, "projekt.json"),
            self._tr("dlg_filter_project")
        )
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        self.project_file_path = path
        self.save_project()

    def save_project(self):
        if not self.project_file_path:
            self.save_project_as()
            return
        try:
            data = self._project_to_dict()
            with open(self.project_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.status_bar.showMessage(self._tr("msg_project_saved", os.path.basename(self.project_file_path)))
            QMessageBox.information(
                self,
                self._tr("info_title"),
                self._tr("msg_project_saved", os.path.basename(self.project_file_path))
            )
        except Exception as e:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_project_save_failed", str(e)))

    def load_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            self._tr("menu_project_load"),
            self.current_export_dir or os.getcwd(),
            self._tr("dlg_filter_project")
        )
        if not path:
            return
        self.load_project_from_path(path)

    def load_project_from_path(self, path: str):
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.project_file_path = path
            self._load_project_dict(data)
            self.status_bar.showMessage(self._tr("msg_project_loaded", os.path.basename(path)))
        except Exception as e:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_project_load_failed", str(e)))

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
        if currentRow < 0:
            return
        item = self.queue_table.item(currentRow, QUEUE_COL_FILE)
        if not item:
            return
        path = item.data(Qt.UserRole)
        if path:
            self.preview_image(path)

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

    def _normalize_toolbar_button_sizes(self):
        target_height = 34
        clear_width = 28
        # Alle Toolbar-QToolButtons angleichen
        for b in self.toolbar.findChildren(QToolButton):
            b.setMinimumHeight(target_height)
            b.setMaximumHeight(target_height)
            b.setMinimumWidth(0)
            b.setMaximumWidth(16777215)
        # Hauptbuttons angleichen
        for btn_name in (
                "btn_rec_model",
                "btn_seg_model",
                "btn_ai_model",
                "btn_theme_toggle",
                "btn_lang_menu",
        ):
            btn = getattr(self, btn_name, None)
            if btn is not None:
                btn.setMinimumHeight(target_height)
                btn.setMaximumHeight(target_height)
                btn.setMinimumWidth(0)
                btn.setMaximumWidth(16777215)
        if hasattr(self, "btn_theme_toggle"):
            self.btn_theme_toggle.setFixedWidth(target_height + 8)

    def _icon_fg_color(self) -> QColor:
        return QColor("#ffffff") if self.current_theme == "dark" else QColor("#000000")

    def _tinted_theme_or_standard_icon(
            self,
            theme_name: str,
            std_icon,
            size: Optional[QSize] = None
    ):
        icon = QIcon.fromTheme(theme_name)
        if icon.isNull():
            icon = self.style().standardIcon(std_icon)
        if icon.isNull():
            return icon
        if size is None:
            if hasattr(self, "toolbar"):
                size = self.toolbar.iconSize()
            else:
                size = QSize(16, 16)
        src = icon.pixmap(size)
        if src.isNull():
            return icon
        tinted = QPixmap(src.size())
        tinted.fill(Qt.transparent)
        painter = QPainter(tinted)
        painter.drawPixmap(0, 0, src)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(tinted.rect(), self._icon_fg_color())
        painter.end()
        return QIcon(tinted)

    def _themed_or_standard_icon(self, theme_name: str, std_icon):
        icon = QIcon.fromTheme(theme_name)
        if icon.isNull():
            icon = self.style().standardIcon(std_icon)
        return icon

    def _set_primary_toolbar_icons(self):
        if hasattr(self, "act_add"):
            self.act_add.setIcon(
                self._themed_or_standard_icon("document-open", QStyle.SP_DialogOpenButton)
            )
        if hasattr(self, "act_project_load_toolbar"):
            self.act_project_load_toolbar.setIcon(
                self._themed_or_standard_icon("document-open", QStyle.SP_DialogOpenButton)
            )
        if hasattr(self, "act_image_edit"):
            self.act_image_edit.setIcon(
                self._tinted_theme_or_standard_icon("edit-cut", QStyle.SP_FileDialogDetailedView)
            )
        if hasattr(self, "act_play"):
            self.act_play.setIcon(
                self._tinted_theme_or_standard_icon("media-playback-start", QStyle.SP_MediaPlay)
            )
        if hasattr(self, "act_stop"):
            self.act_stop.setIcon(
                self._tinted_theme_or_standard_icon("media-playback-stop", QStyle.SP_MediaStop)
            )
        if hasattr(self, "btn_rec_model"):
            self.btn_rec_model.setIcon(
                self._themed_or_standard_icon("document-open", QStyle.SP_DialogOpenButton)
            )
        if hasattr(self, "btn_seg_model"):
            self.btn_seg_model.setIcon(
                self._themed_or_standard_icon("document-open", QStyle.SP_DialogOpenButton)
            )
