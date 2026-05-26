"""Mixin für MainWindow: menu setup and queue headers."""
from ...shared import *
from ...ui_components import *
from ...workers import *
from ...dialogs import *
from ...image_edit import *
import math

from .menu_behavior import BKStayOpenMenu

class MainWindowThemeToolbarMixin:
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
            if hasattr(self, "_refresh_preview_tool_button_icons"):
                self._refresh_preview_tool_button_icons()
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
            self.current_lang = translation.normalize_language_code(lang)
            # Das Log folgt ab sofort der aktuell gewählten UI-Sprache.
            self.log_lang = self.current_lang
            self.settings.setValue("ui/language", self.current_lang)
            self.retranslate_ui()
            self._refresh_hw_menu_availability()
            self._update_toolbar_language_theme_ui()

        def _build_toolbar_language_theme_menus(self):
            self.lang_toolbar_menu = BKStayOpenMenu(self)
            self.lang_group = QActionGroup(self)
            self.lang_group.setExclusive(True)
            self.lang_actions = {}
            for lang_code in translation.available_languages():
                label = translation.language_display_name(lang_code, getattr(self, "current_lang", None))
                action = QAction(label, self)
                action.setCheckable(True)
                action.triggered.connect(lambda checked=False, code=lang_code: self.set_language(code))
                self.lang_group.addAction(action)
                self.lang_toolbar_menu.addAction(action)
                self.lang_actions[lang_code] = action
                if lang_code.isidentifier():
                    setattr(self, f"act_lang_{lang_code}", action)
            self.btn_lang_menu.setMenu(self.lang_toolbar_menu)
            self._update_toolbar_language_theme_ui()

        def _update_toolbar_language_theme_ui(self):
            if hasattr(self, "btn_theme_toggle"):
                self.btn_theme_toggle.setChecked(self.current_theme == "dark")
                self.btn_theme_toggle.setText("")
                self.btn_theme_toggle.setIcon(self._theme_toggle_icon())
                self.btn_theme_toggle.setToolButtonStyle(Qt.ToolButtonIconOnly)
                self.btn_theme_toggle.setToolTip(self._tr("toolbar_theme_tooltip"))

            if hasattr(self, "btn_lang_menu"):
                self.btn_lang_menu.setText("")
                self.btn_lang_menu.setIcon(self._language_menu_icon())
                self.btn_lang_menu.setToolButtonStyle(Qt.ToolButtonIconOnly)
                self.btn_lang_menu.setToolTip(self._tr("toolbar_language_tooltip"))

            for lang_code, action in getattr(self, "lang_actions", {}).items():
                action.setText(translation.language_display_name(lang_code, self.current_lang))
                action.setChecked(self.current_lang == lang_code)

        def _update_models_menu_labels(self):
            if hasattr(self, "act_rec"):
                self.act_rec.setText(self._tr("act_load_rec_model"))
            if hasattr(self, "act_seg"):
                self.act_seg.setText(self._tr("act_load_seg_model"))
            if hasattr(self, "act_kraken_auto_revision_settings"):
                self.act_kraken_auto_revision_settings.setText(self._tr("act_kraken_auto_revision_settings"))
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

        def open_integrated_backend_installer(self, backend_kind: str):
            dlg = BackendInstallDialog(backend_kind, tr_func=self._tr, parent=self)
            dlg.install_finished.connect(self._on_integrated_backend_install_finished)
            dlg.exec()

        def _on_integrated_backend_install_finished(self, ok: bool, backend_kind: str):
            try:
                clear_external_ocr_backend_cache()
            except Exception:
                pass
            try:
                self._refresh_hw_menu_availability()
            except Exception:
                pass
            if ok:
                try:
                    self._log(self._tr("backend_install_success"))
                except Exception:
                    pass
