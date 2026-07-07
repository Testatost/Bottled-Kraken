from bottled_kraken.common import (
    QFileDialog,
    QMessageBox,
    QProgressDialog,
    QTableWidgetItem,
    QUEUE_COL_CHECK,
    QUEUE_COL_FILE,
    QUEUE_COL_NUM,
    QUEUE_COL_STATUS,
    Qt,
    STATUS_DONE,
    json,
    os,
    translation,
)
import math
class MainWindowProjectFilesMixin:
        def _remap_missing_project_files(self):
            missing = [t for t in self.queue_items if not os.path.exists(t.path)]
            if not missing:
                return
            answer = QMessageBox.question(
                self,
                self._tr("warn_title"),
                self._tr("project_missing_files_prompt"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if answer != QMessageBox.Yes:
                return
            new_base_dir = QFileDialog.getExistingDirectory(
                self,
                self._tr("project_choose_new_base_dir"),
                self.current_export_dir or os.getcwd()
            )
            if not new_base_dir:
                return
            unresolved = []
            for task in missing:
                candidates = []
                rel = (task.relative_path or "").strip()
                old_path = (task.path or "").strip()
                if rel:
                    candidates.append(os.path.normpath(os.path.join(new_base_dir, rel)))
                if old_path:
                    candidates.append(os.path.normpath(os.path.join(new_base_dir, os.path.basename(old_path))))
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
                    self._tr("project_files_still_missing", "\n".join(unresolved[:20]))
                )
        def _load_project_dict(self, data: dict):
            progress = QProgressDialog(self._tr("project_loading_progress"), None, 0, 100, self)
            progress.setWindowTitle(self._tr("dlg_project_loading_title"))
            progress.setWindowModality(Qt.ApplicationModal)
            progress.setCancelButton(None)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            progress.show()
            self._process_ui()
            try:
                self.clear_queue()
                for _name in (
                    "_ocr_variants_by_path",
                    "_ocr_active_variant_by_path",
                    "_ptr_multi_ocr_variant_meta_by_path",
                    "_ptr_multi_ocr_variants_by_path",
                    "_ptr_multi_ocr_active_index_by_path",
                ):
                    try:
                        setattr(self, _name, {})
                    except Exception:
                        pass
                progress.setLabelText(self._tr("project_restore_settings"))
                progress.setValue(5)
                self._process_ui()
                settings = data.get("settings", {})
                self.current_lang = translation.normalize_language_code(settings.get("language", self.current_lang))
                self.log_lang = self.current_lang
                self.reading_direction = int(settings.get("reading_direction", self.reading_direction))
                self.device_str = settings.get("device", self.device_str)
                self.show_overlay = bool(settings.get("show_overlay", self.show_overlay))
                self.current_theme = settings.get("theme", self.current_theme)
                custom_theme_colors = settings.get("custom_theme_colors", None)
                if isinstance(custom_theme_colors, dict) and hasattr(self, "_save_custom_theme_colors"):
                    try:
                        self._save_custom_theme_colors(custom_theme_colors)
                        self._register_custom_theme(custom_theme_colors)
                    except Exception:
                        pass
                appearance_user_themes = settings.get("appearance_user_themes", None)
                if isinstance(appearance_user_themes, list) and hasattr(self, "_appearance_save_user_themes"):
                    try:
                        self._appearance_save_user_themes(appearance_user_themes)
                        self._ensure_appearance_themes_loaded()
                    except Exception:
                        pass
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
                progress.setLabelText(self._tr("project_read_data"))
                progress.setValue(10)
                self._process_ui()
                for idx, task_data in enumerate(queue_data, start=1):
                    task = self._task_from_dict(task_data)
                    self.queue_items.append(task)
                    pct = 10 + int((idx / total) * 35)
                    progress.setLabelText(self._tr("project_read_objects", idx, total))
                    progress.setValue(pct)
                    self._process_ui()
                progress.setLabelText(self._tr("project_check_paths"))
                progress.setValue(50)
                self._process_ui()
                self._remap_missing_project_files()
                progress.setLabelText(self._tr("project_build_queue"))
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
                    progress.setLabelText(self._tr("project_build_queue_progress", idx, total))
                    progress.setValue(pct)
                    self._process_ui()
                progress.setLabelText(self._tr("project_update_ui"))
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
                                try:
                                    refresh_tabs = getattr(self, "_ptr_refresh_ocr_variant_tabs_now", None)
                                    if callable(refresh_tabs):
                                        refresh_tabs()
                                except Exception:
                                    pass
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
                progress.setLabelText(self._tr("project_done"))
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
