from bottled_kraken.common import (
    QHeaderView,
    QKeySequence,
    QTimer,
    QUEUE_COL_CHECK,
    QUEUE_COL_FILE,
    QUEUE_COL_NUM,
    QUEUE_COL_STATUS,
    Qt,
    os,
    subprocess,
    sys,
)
def _no_console_kwargs() -> dict:
    if not sys.platform.startswith("win"):
        return {}
    kwargs = {}
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
        kwargs["startupinfo"] = startupinfo
    except Exception:
        pass
    return kwargs
class MainWindowReadingDirectionAndRetranslateMixin:
        def _apply_localized_menu_shortcut_texts(self):
            if not hasattr(self, "_menu_text_with_shortcut"):
                return
            if hasattr(self, "act_undo"):
                self.act_undo.setText(self._menu_text_with_shortcut(self._tr("act_undo"), "Z"))
                try:
                    self.act_undo.setShortcut(QKeySequence())
                except Exception:
                    pass
            if hasattr(self, "act_redo"):
                self.act_redo.setText(self._menu_text_with_shortcut(self._tr("act_redo"), "Y"))
                try:
                    self.act_redo.setShortcut(QKeySequence())
                except Exception:
                    pass
            if hasattr(self, "act_project_save"):
                self.act_project_save.setText(self._menu_text_with_shortcut(self._tr("menu_project_save"), "S"))
            if hasattr(self, "act_project_save_as"):
                self.act_project_save_as.setText(self._menu_text_with_shortcut(self._tr("menu_project_save_as"), "Shift+S"))
            if hasattr(self, "act_project_load"):
                self.act_project_load.setText(self._menu_text_with_shortcut(self._tr("menu_project_load"), "I"))
            if hasattr(self, "export_menu"):
                self.export_menu.setTitle(self._menu_text_with_shortcut(self._tr("menu_export"), "E"))
            if hasattr(self, "act_exit"):
                self.act_exit.setText(self._menu_text_with_shortcut(self._tr("menu_exit"), "Q"))
        def set_reading_direction(self, mode):
            self.reading_direction = mode
        def retranslate_ui(self):
            self.setWindowTitle(self._tr("app_title"))
            self.file_menu.setTitle(self._tr("menu_file"))
            self.edit_menu.setTitle(self._tr("menu_edit"))
            self.models_menu.setTitle(self._tr("menu_models"))
            self.options_menu.setTitle(self._tr("menu_options"))
            if hasattr(self, "act_appearance"):
                self.act_appearance.setText(self._tr("menu_appearance"))
            self.hw_menu.setTitle(self._tr("menu_hw"))
            if hasattr(self, "_menu_text_with_shortcut"):
                self.export_menu.setTitle(self._menu_text_with_shortcut(self._tr("menu_export"), "E"))
            else:
                self.export_menu.setTitle(self._tr("menu_export"))
            if hasattr(self, "export_format_actions"):
                self.formats = self._export_format_items()
                for name, fmt in self.formats:
                    act = self.export_format_actions.get(fmt)
                    if act is not None:
                        act.setText(name)
            self.reading_menu.setTitle(self._tr("menu_reading"))
            if hasattr(self, "revision_models_menu"):
                self.revision_models_menu.setTitle(self._tr("menu_lm_options"))
            if hasattr(self, "whisper_menu"):
                self.whisper_menu.setTitle(self._tr("menu_whisper_options"))
            self.act_export_log.setText(self._tr("menu_export_log"))
            if hasattr(self, "act_lm_help"):
                self.act_lm_help.setText(self._tr("act_help"))
            if hasattr(self, "act_ai_revise"):
                self.act_ai_revise.setText(self._tr("act_ai_revise"))
                self.act_ai_revise.setToolTip(self._tr("act_ai_revise_tip"))
            if hasattr(self, "btn_ai_model"):
                self._update_ai_model_ui()
            if hasattr(self, "act_ai_revise_all"):
                self.act_ai_revise_all.setText(self._tr("act_ai_revise_all"))
                self.act_ai_revise_all.setToolTip(self._tr("act_ai_revise_all_tip"))
            if hasattr(self, "btn_import_lines"):
                self.btn_import_lines.setText(self._tr("btn_import_lines"))
                self.btn_import_lines.setToolTip(self._tr("btn_import_lines_tip"))
            if hasattr(self, "act_import_lines_current"):
                self.act_import_lines_current.setText(self._tr("act_import_lines_current"))
            if hasattr(self, "act_import_lines_selected"):
                self.act_import_lines_selected.setText(self._tr("act_import_lines_selected"))
            if hasattr(self, "act_import_lines_all"):
                self.act_import_lines_all.setText(self._tr("act_import_lines_all"))
            if hasattr(self, "_apply_localized_menu_shortcut_texts"):
                self._apply_localized_menu_shortcut_texts()
            else:
                if hasattr(self, "act_project_save"):
                    self.act_project_save.setText(self._tr("menu_project_save"))
                if hasattr(self, "act_project_save_as"):
                    self.act_project_save_as.setText(self._tr("menu_project_save_as"))
                if hasattr(self, "act_project_load"):
                    self.act_project_load.setText(self._tr("menu_project_load"))
            if hasattr(self, "act_paste_files_menu"):
                if hasattr(self, "_menu_text_with_shortcut"):
                    self.act_paste_files_menu.setText(self._menu_text_with_shortcut(self._tr("act_paste_clipboard"), "V"))
                else:
                    self.act_paste_files_menu.setText(self._tr("act_paste_clipboard"))
            if hasattr(self, "act_paste_files"):
                self.act_paste_files.setText(self._tr("act_paste_clipboard"))
            if hasattr(self, "btn_voice_fill"):
                self.btn_voice_fill.setText(self._tr("act_voice_fill"))
                self.btn_voice_fill.setToolTip(self._tr("act_voice_fill_tip"))
            if hasattr(self, "btn_ai_revise_bottom"):
                self.btn_ai_revise_bottom.setText(self._tr("act_ai_revise"))
                self.btn_ai_revise_bottom.setToolTip(self._tr("act_ai_revise_tip"))
            if hasattr(self, "btn_autocorrect_settings"):
                self.btn_autocorrect_settings.setText(self._tr("btn_autocorrect_settings"))
                self.btn_autocorrect_settings.setToolTip(self._tr("btn_autocorrect_settings_tooltip"))
            if hasattr(self, "btn_line_search"):
                self.btn_line_search.setText(self._tr("btn_line_search"))
                self.btn_line_search.setToolTip(self._tr("btn_line_search_tooltip"))
            if hasattr(self, "btn_preview_select"):
                self.btn_preview_select.setToolTip(self._tr("preview_tool_select_tip"))
            if hasattr(self, "btn_preview_pan"):
                self.btn_preview_pan.setToolTip(self._tr("preview_tool_pan_tip"))
            if hasattr(self, "line_search_popup_edit"):
                self.line_search_popup_edit.setPlaceholderText(self._tr("line_search_placeholder"))
                self.line_search_popup_edit.setToolTip(self._tr("line_search_tooltip"))
            if hasattr(self, "btn_clear_queue"):
                self.btn_clear_queue.setText(self._tr("act_clear_queue"))
            if hasattr(self, "btn_delete_checked_queue"):
                self.btn_delete_checked_queue.setText(self._tr("act_delete_checked_queue"))
                self.btn_delete_checked_queue.setToolTip(self._tr("act_delete_checked_queue_tip"))
            if hasattr(self, "btn_toggle_log"):
                if self.btn_toggle_log.isChecked():
                    self.btn_toggle_log.setText(self._tr("log_toggle_hide"))
                else:
                    self.btn_toggle_log.setText(self._tr("log_toggle_show"))
            if hasattr(self, "_apply_localized_menu_shortcut_texts"):
                self._apply_localized_menu_shortcut_texts()
            else:
                self.act_undo.setText(self._tr("act_undo"))
                self.act_redo.setText(self._tr("act_redo"))
            self.act_add_files.setText(self._tr("act_add_files"))
            if hasattr(self, "_menu_text_with_shortcut"):
                self.act_exit.setText(self._menu_text_with_shortcut(self._tr("menu_exit"), "Q"))
            else:
                self.act_exit.setText(self._tr("menu_exit"))
            self.act_download.setText(self._tr("act_download_model"))
            if hasattr(self, "overlay_menu"):
                self.overlay_menu.setTitle(self._tr("act_overlay_show"))
            elif hasattr(self, "act_overlay"):
                self.act_overlay.setText(self._tr("act_overlay_show"))
            if hasattr(self, "overlay_display_actions"):
                labels = {
                    "none": "overlay_mode_none",
                    "current": "overlay_mode_current",
                    "selected": "overlay_mode_selected",
                    "all": "overlay_mode_all",
                }
                for mode, key in labels.items():
                    act = self.overlay_display_actions.get(mode)
                    if act is not None:
                        act.setText(self._tr(key))
            if hasattr(self, "act_overlay_resize_boxes"):
                self.act_overlay_resize_boxes.setText(self._tr("overlay_resize_menu"))
            self.act_add.setText(self._tr("act_add_files"))
            self.act_clear.setText(self._tr("act_clear_queue"))
            self.act_play.setText(self._tr("act_start_ocr"))
            self.act_stop.setText(self._tr("act_stop_ocr"))
            if hasattr(self, "act_image_edit"):
                self.act_image_edit.setText(self._tr("act_image_edit"))
            self.act_project_load_toolbar.setText(self._tr("menu_project_load"))
            self.act_project_load_toolbar.setToolTip(self._tr("menu_project_load"))
            self.lbl_queue.setText(self._tr("lbl_queue"))
            self.lbl_lines.setText(self._tr("lbl_lines"))
            self.queue_table.setHorizontalHeaderLabels(["#", "☐", self._tr("col_loaded_files"), self._tr("col_status")])
            self._update_queue_check_header()
            if hasattr(self.list_lines, "setHeaderLabels"):
                self.list_lines.setHeaderLabels(["#", self._tr("lines_tree_header")])
                self.list_lines.header().setDefaultAlignment(Qt.AlignCenter)
            if hasattr(self, "_refresh_ocr_variant_tab_texts"):
                self._refresh_ocr_variant_tab_texts()
            if self.model_path:
                self.btn_rec_model.setText(self._tr("btn_rec_model_value", os.path.basename(self.model_path)))
            else:
                self.btn_rec_model.setText(self._tr("btn_rec_model_empty"))
            if self.seg_model_path:
                self.btn_seg_model.setText(self._tr("btn_seg_model_value", os.path.basename(self.seg_model_path)))
            else:
                self.btn_seg_model.setText(self._tr("btn_seg_model_empty"))
            mapping = {"cpu": "hw_cpu", "cuda": "hw_cuda", "rocm": "hw_rocm"}
            for dev, key in mapping.items():
                if dev in self.hw_actions:
                    self.hw_actions[dev].setText(self._tr(key))
            if hasattr(self, "act_install_cuda_backend"):
                self.act_install_cuda_backend.setText(self._tr("hw_install_cuda_backend"))
            if hasattr(self, "act_install_rocm_backend"):
                self.act_install_rocm_backend.setText(self._tr("hw_install_rocm_backend"))
            read_keys = ["reading_tb_lr", "reading_tb_rl", "reading_bt_lr", "reading_bt_rl"]
            for act, key in zip(self.read_actions, read_keys):
                act.setText(self._tr(key))
            self._retranslate_queue_rows()
            self._update_queue_hint()
            self.canvas._show_drop_hint()
            self._update_models_menu_labels()
            self._update_model_clear_buttons()
            self._update_toolbar_language_theme_ui()
            self._set_primary_toolbar_icons()
            self._set_secondary_button_icons()
            QTimer.singleShot(0, self._normalize_toolbar_button_sizes)
            if hasattr(self, "act_rec"):
                self.act_rec.setText(self._tr("act_load_rec_model"))
            if hasattr(self, "act_seg"):
                self.act_seg.setText(self._tr("act_load_seg_model"))
            if hasattr(self, "act_kraken_auto_revision_settings"):
                self.act_kraken_auto_revision_settings.setText(self._tr("act_kraken_auto_revision_settings"))
            if hasattr(self, "btn_autocorrect_settings"):
                self.btn_autocorrect_settings.setText(self._tr("btn_autocorrect_settings"))
                self.btn_autocorrect_settings.setToolTip(self._tr("btn_autocorrect_settings_tooltip"))
            if hasattr(self, "act_whisper_set_path"):
                self.act_whisper_set_path.setText(self._tr("act_whisper_set_path"))
            if hasattr(self, "act_whisper_set_mic"):
                self.act_whisper_set_mic.setText(self._tr("act_whisper_set_mic"))
            if hasattr(self, "act_whisper_scan"):
                self.act_whisper_scan.setText(self._tr("act_scan_local"))
            if hasattr(self, "act_set_manual_lm_url"):
                self.act_set_manual_lm_url.setText(self._tr("act_set_manual_lm_url"))
            if hasattr(self, "act_clear_manual_lm_url"):
                self.act_clear_manual_lm_url.setText(self._tr("act_clear_manual_lm_url"))
            if hasattr(self, "act_scan_lm"):
                self.act_scan_lm.setText(self._tr("act_scan_local"))
            if hasattr(self, "act_clear_rec"):
                self.act_clear_rec.setText(self._tr("act_clear_rec"))
            if hasattr(self, "act_clear_seg"):
                self.act_clear_seg.setText(self._tr("act_clear_seg"))
            if hasattr(self, "kraken_models_submenu"):
                self.kraken_models_submenu.setTitle(self._tr("submenu_available_kraken_models"))
            if hasattr(self, "ai_models_submenu"):
                self.ai_models_submenu.setTitle(self._tr("submenu_available_ai_models"))
            if hasattr(self, "whisper_models_submenu"):
                self.whisper_models_submenu.setTitle(self._tr("submenu_available_whisper_models"))
            self._update_kraken_menu_status()
            self._rebuild_kraken_models_submenu()
            self.refresh_models_menu_status()
            self._update_whisper_menu_status()
            self._rebuild_whisper_model_submenu()
            if hasattr(self, "btn_rec_clear"):
                self.btn_rec_clear.setToolTip(self._tr("act_clear_rec"))
            if hasattr(self, "btn_seg_clear"):
                self.btn_seg_clear.setToolTip(self._tr("act_clear_seg"))
            header = self.queue_table.horizontalHeader()
            header.setStretchLastSection(False)
            header.setSectionResizeMode(QUEUE_COL_NUM, QHeaderView.Fixed)
            header.setSectionResizeMode(QUEUE_COL_CHECK, QHeaderView.Fixed)
            header.setSectionResizeMode(QUEUE_COL_FILE, QHeaderView.Stretch)
            header.setSectionResizeMode(QUEUE_COL_STATUS, QHeaderView.Interactive)
            header_font = header.font()
            header_font.setBold(False)
            header.setFont(header_font)
        def _retranslate_queue_rows(self):
            for it in self.queue_items:
                self._update_queue_row(it.path)
