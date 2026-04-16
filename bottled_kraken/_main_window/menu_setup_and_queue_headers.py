"""Mixin für MainWindow: menu setup and queue headers."""
from ..shared import *
from ..ui_components import *
from ..workers import *
from ..dialogs import *
from ..image_edit import *

class MainWindowMenuSetupAndQueueHeadersMixin:
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
        # kleiner Puffer links/rechts
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
            # Wenn sehr wenig Platz da ist, Status zusammendrücken,
            # damit die Tabelle nie breiter als der Viewport wird.
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
        self.progress_bar.setRange(0, 0)  # busy animation

    def _set_progress_idle(self, value: int = 0):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(max(0, min(100, int(value))))

    def on_progress_update(self, v: int):
        v = max(0, min(100, int(v)))
        # Solange wir in busy (0,0) sind und v noch 0 ist -> Animation bleibt
        if self.progress_bar.minimum() == 0 and self.progress_bar.maximum() == 0:
            if v > 0:
                self.progress_bar.setRange(0, 100)  # sobald >0 -> normale Prozentanzeige
            else:
                return  # busy-mode ignoriert setValue sowieso; Animation bleibt
        self.progress_bar.setValue(v)

    def apply_theme(self, theme: str):
        self.current_theme = theme
        self.settings.setValue("ui/theme", self.current_theme)
        pal = QPalette()
        conf = THEMES[theme]
        fg = QColor(conf["fg"])
        bg = QColor(conf["bg"])
        base = conf["table_base"]
        button = conf["table_base"].lighter(110)
        pal.setColor(QPalette.Window, bg)
        pal.setColor(QPalette.WindowText, fg)
        pal.setColor(QPalette.Base, base)
        pal.setColor(QPalette.AlternateBase, base.lighter(110))
        pal.setColor(QPalette.ToolTipBase, QColor("#ffffff" if theme == "bright" else "#2b3038"))
        pal.setColor(QPalette.ToolTipText, QColor("#000000" if theme == "bright" else "#f3f4f6"))
        pal.setColor(QPalette.Text, fg)
        pal.setColor(QPalette.Button, button)
        pal.setColor(QPalette.ButtonText, fg)
        pal.setColor(QPalette.BrightText, Qt.red)
        pal.setColor(QPalette.Link, QColor(42, 130, 218))
        pal.setColor(QPalette.Highlight, QColor(42, 130, 218))
        pal.setColor(QPalette.HighlightedText, QColor("#ffffff" if theme == "dark" else "#000000"))
        app = QApplication.instance()
        app.setPalette(pal)
        self.canvas.set_theme(theme)
        app.setStyleSheet(_theme_app_qss(theme))
        self._update_toolbar_language_theme_ui()
        self._set_primary_toolbar_icons()
        self._set_secondary_button_icons()
        self._apply_lines_tree_theme()

    def toggle_theme(self):
        new_theme = "dark" if self.current_theme == "bright" else "bright"
        self.apply_theme(new_theme)

    def _apply_lines_tree_theme(self):
        if not hasattr(self, "list_lines") or self.list_lines is None:
            return
        if self.current_theme == "dark":
            qss = """
                QTreeWidget {
                    background: #1f2630;
                    alternate-background-color: #27303b;
                    color: #f3f4f6;
                    border: 1px solid #4b5563;
                    selection-background-color: #2563eb;
                    selection-color: #ffffff;
                }
                QTreeWidget::item {
                    background: #1f2630;
                    color: #f3f4f6;
                    padding: 2px 4px;
                }
                QTreeWidget::item:alternate {
                    background: #27303b;
                    color: #f3f4f6;
                }
                QTreeWidget::item:hover {
                    background: #334155;
                    color: #ffffff;
                }
                QTreeWidget::item:selected,
                QTreeWidget::item:selected:active,
                QTreeWidget::item:selected:!active {
                    background: #2563eb;
                    color: #ffffff;
                }
                QHeaderView::section {
                    background: #313844;
                    color: #f3f4f6;
                    border: 1px solid #4b5563;
                    padding: 4px;
                    font-weight: 600;
                }
            """
        else:
            qss = """
                QTreeWidget {
                    background: #ffffff;
                    alternate-background-color: #f3f6fb;
                    color: #111827;
                    border: 1px solid #c8c8c8;
                    selection-background-color: #3399ff;
                    selection-color: #ffffff;
                }
                QTreeWidget::item {
                    background: #ffffff;
                    color: #111827;
                    padding: 2px 4px;
                }
                QTreeWidget::item:alternate {
                    background: #f3f6fb;
                    color: #111827;
                }
                QTreeWidget::item:hover {
                    background: #e8f1ff;
                    color: #111827;
                }
                QTreeWidget::item:selected,
                QTreeWidget::item:selected:active,
                QTreeWidget::item:selected:!active {
                    background: #3399ff;
                    color: #ffffff;
                }
                QHeaderView::section {
                    background: #e8e8e8;
                    color: #000000;
                    border: 1px solid #c8c8c8;
                    padding: 4px;
                    font-weight: 600;
                }
            """
        self.list_lines.setAlternatingRowColors(True)
        self.list_lines.setStyleSheet(qss)
        self.list_lines.viewport().update()

    def set_language(self, lang):
        self.current_lang = lang
        self.settings.setValue("ui/language", self.current_lang)
        self.retranslate_ui()
        self._refresh_hw_menu_availability()
        self._update_toolbar_language_theme_ui()

    def _build_toolbar_language_theme_menus(self):
        # Nur Sprach-Menü
        self.lang_toolbar_menu = QMenu(self)
        self.lang_group = QActionGroup(self)
        self.act_lang_de = QAction(self._tr("lang_de"), self)
        self.act_lang_de.setCheckable(True)
        self.act_lang_de.triggered.connect(lambda: self.set_language("de"))
        self.lang_group.addAction(self.act_lang_de)
        self.lang_toolbar_menu.addAction(self.act_lang_de)
        self.act_lang_en = QAction(self._tr("lang_en"), self)
        self.act_lang_en.setCheckable(True)
        self.act_lang_en.triggered.connect(lambda: self.set_language("en"))
        self.lang_group.addAction(self.act_lang_en)
        self.lang_toolbar_menu.addAction(self.act_lang_en)
        self.act_lang_fr = QAction(self._tr("lang_fr"), self)
        self.act_lang_fr.setCheckable(True)
        self.act_lang_fr.triggered.connect(lambda: self.set_language("fr"))
        self.lang_group.addAction(self.act_lang_fr)
        self.lang_toolbar_menu.addAction(self.act_lang_fr)
        self.btn_lang_menu.setMenu(self.lang_toolbar_menu)
        self._update_toolbar_language_theme_ui()

    def _update_toolbar_language_theme_ui(self):
        if hasattr(self, "btn_theme_toggle"):
            is_dark = self.current_theme == "dark"
            self.btn_theme_toggle.setChecked(is_dark)
            self.btn_theme_toggle.setText("🔅" if is_dark else "💡")
            self.btn_theme_toggle.setIcon(QIcon())
            self.btn_theme_toggle.setToolTip(self._tr("toolbar_theme_tooltip"))
        if hasattr(self, "btn_lang_menu"):
            self.btn_lang_menu.setText(self._tr("toolbar_language"))
            lang_theme_name = "preferences-desktop-locale"
            if QIcon.fromTheme(lang_theme_name).isNull():
                lang_theme_name = "accessories-dictionary"
            self.btn_lang_menu.setIcon(
                self._tinted_theme_or_standard_icon(
                    lang_theme_name,
                    QStyle.SP_FileDialogContentsView
                )
            )
            self.btn_lang_menu.setToolTip(self._tr("toolbar_language_tooltip"))
        if hasattr(self, "act_lang_de"):
            self.act_lang_de.setText(self._tr("lang_de"))
            self.act_lang_de.setChecked(self.current_lang == "de")
        if hasattr(self, "act_lang_en"):
            self.act_lang_en.setText(self._tr("lang_en"))
            self.act_lang_en.setChecked(self.current_lang == "en")
        if hasattr(self, "act_lang_fr"):
            self.act_lang_fr.setText(self._tr("lang_fr"))
            self.act_lang_fr.setChecked(self.current_lang == "fr")

    def _update_models_menu_labels(self):
        if hasattr(self, "act_rec"):
            self.act_rec.setText(self._tr("act_load_rec_model"))
        if hasattr(self, "act_seg"):
            self.act_seg.setText(self._tr("act_load_seg_model"))
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
        self._update_kraken_menu_status()
        if hasattr(self, "kraken_models_submenu"):
            self._rebuild_kraken_models_submenu()

    def _make_toolbar_buttons_pushy(self):
        # Alle QToolButtons, die QToolBar für QAction erstellt
        for b in self.toolbar.findChildren(QToolButton):
            b.setAutoRaise(False)  # wichtig: sonst wirkt es oft "flat"
            b.setCursor(Qt.PointingHandCursor)
        # Auch die Modell-Buttons
        self.btn_rec_model.setCursor(Qt.PointingHandCursor)
        self.btn_seg_model.setCursor(Qt.PointingHandCursor)
        if hasattr(self, "btn_import_lines"):
            self.btn_import_lines.setCursor(Qt.PointingHandCursor)

    def _init_menu(self):
        menubar = self.menuBar()
        self.file_menu = menubar.addMenu(self._tr("menu_file"))
        self.edit_menu = menubar.addMenu(self._tr("menu_edit"))
        self.options_menu = menubar.addMenu(self._tr("menu_options"))
        self.edit_menu.addAction(self.act_undo)
        self.edit_menu.addAction(self.act_redo)
        self.edit_menu.addSeparator()
        self.act_export_log = QAction(self._tr("menu_export_log"), self)
        self.act_export_log.triggered.connect(self.export_log_txt)
        self.edit_menu.addAction(self.act_export_log)
        self.act_add_files = QAction(self._tr("act_add_files"), self)
        self.act_add_files.triggered.connect(self.choose_files)
        self.file_menu.addAction(self.act_add_files)
        self.act_paste_files_menu = QAction(self._tr("act_paste_clipboard"), self)
        self.act_paste_files_menu.setShortcut(QKeySequence.Paste)
        self.act_paste_files_menu.triggered.connect(self.paste_files_from_clipboard)
        self.file_menu.addAction(self.act_paste_files_menu)
        self.file_menu.addSeparator()
        self.act_project_save = QAction(self._tr("menu_project_save"), self)
        self.act_project_save.triggered.connect(self.save_project)
        self.file_menu.addAction(self.act_project_save)
        self.act_project_save_as = QAction(self._tr("menu_project_save_as"), self)
        self.act_project_save_as.triggered.connect(self.save_project_as)
        self.file_menu.addAction(self.act_project_save_as)
        self.act_project_load = QAction(self._tr("menu_project_load"), self)
        self.act_project_load.triggered.connect(self.load_project)
        self.file_menu.addAction(self.act_project_load)
        self.file_menu.addSeparator()
        self.export_menu = self.file_menu.addMenu(self._tr("menu_export"))
        self.formats = [
            ("Text (.txt)", "txt"),
            ("CSV (.csv)", "csv"),
            ("JSON (.json)", "json"),
            ("ALTO (.xml)", "alto"),
            ("hOCR (.html)", "hocr"),
            ("PDF (.pdf)", "pdf")
        ]
        for name, fmt in self.formats:
            act = QAction(name, self)
            act.triggered.connect(lambda checked, f=fmt: self.export_flow(f))
            self.export_menu.addAction(act)
        self.file_menu.addSeparator()
        self.act_exit = QAction(self._tr("menu_exit"), self)
        self.act_exit.setShortcut(QKeySequence.Quit)
        self.act_exit.triggered.connect(self.close)
        self.file_menu.addAction(self.act_exit)
        self.models_menu = menubar.addMenu(self._tr("menu_models"))
        self.act_rec = QAction(self._tr("act_load_rec_model"), self)
        self.act_rec.triggered.connect(self.choose_rec_model)
        self.models_menu.addAction(self.act_rec)
        self.act_seg = QAction(self._tr("act_load_seg_model"), self)
        self.act_seg.triggered.connect(self.choose_seg_model)
        self.models_menu.addAction(self.act_seg)
        self.models_menu.addSeparator()
        self.kraken_models_submenu = self.models_menu.addMenu(self._tr("submenu_available_kraken_models"))
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
        self.revision_models_menu = menubar.addMenu(self._tr("menu_lm_options"))
        # -----------------------------
        # Whisper-Optionen
        # -----------------------------
        self.whisper_menu = menubar.addMenu(self._tr("menu_whisper_options"))
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
        self.whisper_models_submenu = self.whisper_menu.addMenu(self._tr("submenu_available_whisper_models"))
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
        self.ai_models_submenu = self.revision_models_menu.addMenu(self._tr("submenu_available_ai_models"))
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
        self.hw_menu = self.options_menu.addMenu(self._tr("menu_hw"))
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
        # Leserichtung
        self.options_menu.addSeparator()
        self.reading_menu = self.options_menu.addMenu(self._tr("menu_reading"))
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
        self.act_overlay = QAction(self._tr("act_overlay_show"), self)
        self.act_overlay.setCheckable(True)
        self.act_overlay.setChecked(True)
        self.act_overlay.toggled.connect(self._on_overlay_toggled)
        self.options_menu.addAction(self.act_overlay)
        if self.device_str in self.hw_actions:
            self.hw_actions[self.device_str].setChecked(True)
