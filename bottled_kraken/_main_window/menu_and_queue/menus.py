"""Mixin für MainWindow: menu setup and queue headers."""
from ...shared import *
from ...ui_components import *
from ...workers import *
from ...dialogs import *
from ...image_edit import *
import math

from .menu_behavior import BKStayOpenMenu

class MainWindowMenuConstructionMixin:

        def set_kraken_auto_revision_enabled(self, checked: bool):
            self.kraken_auto_revision_enabled = bool(checked)
            try:
                self.settings.setValue("ocr/auto_revision_enabled", "true" if self.kraken_auto_revision_enabled else "false")
            except Exception:
                pass

        def _kraken_auto_revision_default_text(self) -> str:
            try:
                return _serialize_ocr_auto_revision_replacements()
            except Exception:
                return "ſ=s\n⸗=-\n±=+/-"

        def _open_kraken_auto_revision_settings(self):
            dialog = QDialog(self)
            dialog.setWindowTitle(self._tr("kraken_revision_settings_title"))
            dialog.setMinimumSize(560, 420)
            try:
                dialog.resize(620, 480)
            except Exception:
                pass
            layout = QVBoxLayout(dialog)
            info = QLabel(self._tr("kraken_revision_settings_intro"))
            info.setWordWrap(True)
            layout.addWidget(info)
            editor = QPlainTextEdit(dialog)
            editor.setPlaceholderText(self._tr("kraken_revision_replacements_placeholder"))
            editor.setMinimumHeight(170)
            editor.setPlainText(str(getattr(self, "kraken_auto_revision_replacements", "") or self._kraken_auto_revision_default_text()))
            layout.addWidget(editor, 1)
            hint = QLabel(self._tr("kraken_revision_replacements_hint"))
            hint.setWordWrap(True)
            layout.addWidget(hint)
            check = QCheckBox(self._tr("kraken_revision_enable_checkbox"), dialog)
            check.setChecked(bool(getattr(self, "kraken_auto_revision_enabled", False)))
            layout.addWidget(check)
            buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, dialog)
            if buttons.button(QDialogButtonBox.Save):
                buttons.button(QDialogButtonBox.Save).setText(self._tr("btn_save"))
            if buttons.button(QDialogButtonBox.Cancel):
                buttons.button(QDialogButtonBox.Cancel).setText(self._tr("btn_cancel"))
            reset_btn = buttons.addButton(self._tr("kraken_revision_reset_defaults"), QDialogButtonBox.ResetRole)
            reset_btn.clicked.connect(lambda: editor.setPlainText(self._kraken_auto_revision_default_text()))
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            if dialog.exec() == QDialog.Accepted:
                text = editor.toPlainText().strip() or self._kraken_auto_revision_default_text()
                self.kraken_auto_revision_replacements = text
                self.kraken_auto_revision_enabled = bool(check.isChecked())
                try:
                    self.settings.setValue("ocr/auto_revision_replacements", text)
                    self.settings.setValue("ocr/auto_revision_enabled", "true" if self.kraken_auto_revision_enabled else "false")
                except Exception:
                    pass

        def _place_kraken_auto_revision_action_at_bottom(self):
            if not hasattr(self, "models_menu"):
                return
            if not hasattr(self, "act_kraken_auto_revision_settings"):
                self.act_kraken_auto_revision_settings = QAction(self._tr("act_kraken_auto_revision_settings"), self)
                self.act_kraken_auto_revision_settings.triggered.connect(self._open_kraken_auto_revision_settings)
            sep = getattr(self, "_kraken_auto_revision_separator", None)
            for action in (sep, self.act_kraken_auto_revision_settings):
                if action is not None:
                    try:
                        self.models_menu.removeAction(action)
                    except Exception:
                        pass
            self._kraken_auto_revision_separator = self.models_menu.addSeparator()
            self.models_menu.addAction(self.act_kraken_auto_revision_settings)

        def _shortcut_ctrl_label(self, suffix: str) -> str:
            lang = str(getattr(self, "current_lang", "") or "").lower()
            prefix = "Strg" if lang.startswith("de") else "Ctrl"
            return f"{prefix}+{str(suffix).lstrip('+')}"

        def _menu_text_with_shortcut(self, text: str, suffix: str) -> str:
            # Tab trennt in Qt-Menüs den Beschriftungstext von der Shortcut-Spalte.
            return f"{str(text)}\t{self._shortcut_ctrl_label(suffix)}"

        def _init_menu(self):
            menubar = self.menuBar()
            self.file_menu = BKStayOpenMenu(self._tr("menu_file"), self)
            self.edit_menu = BKStayOpenMenu(self._tr("menu_edit"), self)
            self.options_menu = BKStayOpenMenu(self._tr("menu_options"), self)
            menubar.addMenu(self.file_menu)
            menubar.addMenu(self.edit_menu)
            menubar.addMenu(self.options_menu)
            if hasattr(self, "_apply_localized_menu_shortcut_texts"):
                self._apply_localized_menu_shortcut_texts()
            self.edit_menu.addAction(self.act_undo)
            self.edit_menu.addAction(self.act_redo)
            self.edit_menu.addSeparator()
            self.act_export_log = QAction(self._tr("menu_export_log"), self)
            self.act_export_log.triggered.connect(self.export_log_txt)
            self.edit_menu.addAction(self.act_export_log)
            self.act_add_files = QAction(self._tr("act_add_files"), self)
            self.act_add_files.triggered.connect(self.choose_files)
            self.file_menu.addAction(self.act_add_files)
            self.act_paste_files_menu = QAction(self._menu_text_with_shortcut(self._tr("act_paste_clipboard"), "V"), self)
            self.act_paste_files_menu.triggered.connect(self.paste_files_from_clipboard)
            self.file_menu.addAction(self.act_paste_files_menu)
            self.act_paste_files_menu_sc = QAction(self)
            self.act_paste_files_menu_sc.setShortcut(QKeySequence.Paste)
            self.act_paste_files_menu_sc.triggered.connect(self.paste_files_from_clipboard)
            self.addAction(self.act_paste_files_menu_sc)
            self.file_menu.addSeparator()
            self.act_project_save = QAction(self._menu_text_with_shortcut(self._tr("menu_project_save"), "S"), self)
            self.act_project_save.triggered.connect(self.save_project)
            self.file_menu.addAction(self.act_project_save)
            self.act_project_save_as = QAction(self._menu_text_with_shortcut(self._tr("menu_project_save_as"), "Shift+S"), self)
            self.act_project_save_as.triggered.connect(self.save_project_as)
            self.file_menu.addAction(self.act_project_save_as)
            self.act_project_load = QAction(self._menu_text_with_shortcut(self._tr("menu_project_load"), "I"), self)
            self.act_project_load.triggered.connect(self.load_project)
            self.file_menu.addAction(self.act_project_load)
            self.file_menu.addSeparator()
            self.export_menu = BKStayOpenMenu(self._menu_text_with_shortcut(self._tr("menu_export"), "E"), self.file_menu)
            self.file_menu.addMenu(self.export_menu)
            self.formats = self._export_format_items()
            self.export_format_actions = {}
            for name, fmt in self.formats:
                act = QAction(name, self)
                act.triggered.connect(lambda checked, f=fmt: self.export_flow(f))
                self.export_format_actions[fmt] = act
                self.export_menu.addAction(act)
            self.file_menu.addSeparator()
            self.act_exit = QAction(self._menu_text_with_shortcut(self._tr("menu_exit"), "Q"), self)
            self.act_exit.triggered.connect(self.close)
            self.file_menu.addAction(self.act_exit)
            self.models_menu = BKStayOpenMenu(self._tr("menu_models"), self); menubar.addMenu(self.models_menu)
            self.act_rec = QAction(self._tr("act_load_rec_model"), self)
            self.act_rec.triggered.connect(self.choose_rec_model)
            self.models_menu.addAction(self.act_rec)
            self.act_seg = QAction(self._tr("act_load_seg_model"), self)
            self.act_seg.triggered.connect(self.choose_seg_model)
            self.models_menu.addAction(self.act_seg)
            self.models_menu.addSeparator()
            self.kraken_models_submenu = BKStayOpenMenu(self._tr("submenu_available_kraken_models"), self.models_menu); self.models_menu.addMenu(self.kraken_models_submenu)
            # Diese Aktionen werden nicht mehr direkt ins Hauptmenü gesetzt,
            # sondern im Untermenü eingebaut.
            self.act_clear_rec = QAction(self._tr("act_clear_rec"), self)
            self.act_clear_rec.triggered.connect(self.clear_rec_model)
            self.act_clear_seg = QAction(self._tr("act_clear_seg"), self)
            self.act_clear_seg.triggered.connect(self.clear_seg_model)
            self.act_rec_status = QAction(self._tr("status_rec_model", "-"), self)
            self.act_rec_status.setEnabled(False)
            self.act_seg_status = QAction(self._tr("status_seg_model", "-"), self)
            self.act_seg_status.setEnabled(False)
            self._rebuild_kraken_models_submenu()
            self._update_kraken_menu_status()
            self.models_menu.addSeparator()
            self.models_menu.addAction(self.act_rec_status)
            self.models_menu.addAction(self.act_seg_status)
            self.models_menu.addSeparator()
            self.act_download = QAction(self._tr("act_download_model"), self)
            self.act_download.triggered.connect(self.open_download_link)
            self.models_menu.addAction(self.act_download)
            self._place_kraken_auto_revision_action_at_bottom()
            self.revision_models_menu = BKStayOpenMenu(self._tr("menu_lm_options"), self); menubar.addMenu(self.revision_models_menu)
            # -----------------------------
            # Whisper-Optionen
            # -----------------------------
            self.whisper_menu = BKStayOpenMenu(self._tr("menu_whisper_options"), self); menubar.addMenu(self.whisper_menu)
            self.act_whisper_set_path = QAction(self._tr("act_whisper_set_path"), self)
            self.act_whisper_set_path.triggered.connect(self.set_whisper_base_dir_dialog)
            self.whisper_menu.addAction(self.act_whisper_set_path)
            self.act_whisper_set_mic = QAction(self._tr("act_whisper_set_mic"), self)
            self.act_whisper_set_mic.triggered.connect(self.choose_whisper_microphone_dialog)
            self.whisper_menu.addAction(self.act_whisper_set_mic)
            self.whisper_menu.addSeparator()
            self.act_whisper_scan = QAction(self._tr("act_scan_local"), self)
            self.act_whisper_scan.triggered.connect(self.scan_whisper_models_now)
            self.whisper_menu.addAction(self.act_whisper_scan)
            self.whisper_models_submenu = BKStayOpenMenu(self._tr("submenu_available_whisper_models"), self.whisper_menu); self.whisper_menu.addMenu(self.whisper_models_submenu)
            self.whisper_model_group = QActionGroup(self)
            self.whisper_model_group.setExclusive(True)
            self.whisper_menu.addSeparator()
            self.act_whisper_status_model = QAction(self._tr("whisper_status_model", "-"), self)
            self.act_whisper_status_model.setEnabled(False)
            self.whisper_menu.addAction(self.act_whisper_status_model)
            self.act_whisper_status_mic = QAction(self._tr("whisper_status_mic", "-"), self)
            self.act_whisper_status_mic.setEnabled(False)
            self.whisper_menu.addAction(self.act_whisper_status_mic)
            self.act_whisper_status_path = QAction(self._tr("whisper_status_path", "-"), self)
            self.act_whisper_status_path.setEnabled(False)
            self.whisper_menu.addAction(self.act_whisper_status_path)
            self._scan_whisper_models()
            self._rebuild_whisper_model_submenu()
            self._update_whisper_menu_status()
            self.act_lm_help = menubar.addAction(self._tr("act_help"))
            self.act_lm_help.triggered.connect(self.show_lm_help_dialog)
            self.act_set_manual_lm_url = QAction(self._tr("act_set_manual_lm_url"), self)
            self.act_set_manual_lm_url.triggered.connect(self.set_manual_ai_base_url_dialog)
            self.revision_models_menu.addAction(self.act_set_manual_lm_url)
            self.act_clear_manual_lm_url = QAction(self._tr("act_clear_manual_lm_url"), self)
            self.act_clear_manual_lm_url.triggered.connect(self.clear_manual_ai_base_url)
            self.revision_models_menu.addAction(self.act_clear_manual_lm_url)
            self.revision_models_menu.addSeparator()
            self.act_scan_lm = QAction(self._tr("act_scan_local"), self)
            self.act_scan_lm.triggered.connect(self.scan_ai_models_now)
            self.revision_models_menu.addAction(self.act_scan_lm)
            self.ai_models_submenu = BKStayOpenMenu(self._tr("submenu_available_ai_models"), self.revision_models_menu); self.revision_models_menu.addMenu(self.ai_models_submenu)
            self.ai_model_group = QActionGroup(self)
            self.ai_model_group.setExclusive(True)
            self._rebuild_ai_model_submenu()
            self.revision_models_menu.addSeparator()
            self.act_lm_status = QAction(self._tr("lm_status_model_value", "-"), self)
            self.act_lm_status.setEnabled(False)
            self.revision_models_menu.addAction(self.act_lm_status)
            self.act_lm_mode = QAction(self._tr("lm_mode_value", "-"), self)
            self.act_lm_mode.setEnabled(False)
            self.revision_models_menu.addAction(self.act_lm_mode)
            self.act_lm_base_url = QAction(self._tr("lm_server_value", "-"), self)
            self.act_lm_base_url.setEnabled(False)
            self.revision_models_menu.addAction(self.act_lm_base_url)
            # Sprachen
            self._build_toolbar_language_theme_menus()
            # Hardware-Menü
            self.options_menu.addSeparator()
            self.hw_menu = BKStayOpenMenu(self._tr("menu_hw"), self.options_menu); self.options_menu.addMenu(self.hw_menu)
            hw_group = QActionGroup(self)
            self.hw_actions: Dict[str, QAction] = {}
            for key, dev in [("hw_cpu", "cpu"), ("hw_cuda", "cuda"), ("hw_rocm", "rocm"), ("hw_mps", "mps")]:
                act = QAction(self._tr(key), self)
                act.setCheckable(True)
                if dev == self.device_str:
                    act.setChecked(True)
                act.triggered.connect(lambda checked, d=dev: self.set_device(d))
                hw_group.addAction(act)
                self.hw_menu.addAction(act)
                self.hw_actions[dev] = act

                if dev == "cuda":
                    self.act_install_cuda_backend = QAction(self._tr("hw_install_cuda_backend"), self)
                    self.act_install_cuda_backend.triggered.connect(
                        lambda checked=False: self.open_integrated_backend_installer("nvidia-cuda")
                    )
                    self.hw_menu.addAction(self.act_install_cuda_backend)
                elif dev == "rocm":
                    self.act_install_rocm_backend = QAction(self._tr("hw_install_rocm_backend"), self)
                    self.act_install_rocm_backend.triggered.connect(
                        lambda checked=False: self.open_integrated_backend_installer("amd-rocm")
                    )
                    self.hw_menu.addAction(self.act_install_rocm_backend)
            # Leserichtung
            self.options_menu.addSeparator()
            self.reading_menu = BKStayOpenMenu(self._tr("menu_reading"), self.options_menu); self.options_menu.addMenu(self.reading_menu)
            read_group = QActionGroup(self)
            self.read_actions: List[QAction] = []
            for key, mode in [
                ("reading_tb_lr", READING_MODES["TB_LR"]),
                ("reading_tb_rl", READING_MODES["TB_RL"]),
                ("reading_bt_lr", READING_MODES["BT_LR"]),
                ("reading_bt_rl", READING_MODES["BT_RL"]),
            ]:
                act = QAction(self._tr(key), self)
                act.setCheckable(True)
                if mode == self.reading_direction:
                    act.setChecked(True)
                act.triggered.connect(lambda checked, m=mode: self.set_reading_direction(m))
                read_group.addAction(act)
                self.reading_menu.addAction(act)
                self.read_actions.append(act)
            # Overlay (Boxen)
            self.options_menu.addSeparator()
            self.overlay_menu = BKStayOpenMenu(self._tr("act_overlay_show"), self.options_menu); self.options_menu.addMenu(self.overlay_menu)
            self.overlay_display_group = QActionGroup(self)
            self.overlay_display_group.setExclusive(True)
            self.overlay_display_actions: Dict[str, QAction] = {}

            for key, mode in [
                ("overlay_mode_none", "none"),
                ("overlay_mode_current", "current"),
                ("overlay_mode_selected", "selected"),
                ("overlay_mode_all", "all"),
            ]:
                act = QAction(self._tr(key), self)
                act.setCheckable(True)
                if mode == getattr(self, "overlay_display_mode", "all"):
                    act.setChecked(True)
                act.triggered.connect(lambda checked=False, m=mode: self._set_overlay_display_mode(m))
                self.overlay_display_group.addAction(act)
                self.overlay_menu.addAction(act)
                self.overlay_display_actions[mode] = act

            self.act_overlay_resize_boxes = QAction(self._tr("overlay_resize_menu"), self)
            self.act_overlay_resize_boxes.triggered.connect(self.resize_overlay_boxes_dialog)

            # Kompatibilitäts-Alias für ältere Runtime-Patches, die noch self.act_overlay erwarten.
            self.act_overlay = self.overlay_menu.menuAction()
            if self.device_str in self.hw_actions:
                self.hw_actions[self.device_str].setChecked(True)
