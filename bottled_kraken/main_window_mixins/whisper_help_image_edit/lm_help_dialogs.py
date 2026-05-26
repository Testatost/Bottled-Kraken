"""Mixin für MainWindow: whisper download help and image edit queue."""
from ...shared import *
from ...ui_components import *
from ...workers import *
from ...dialogs import *
from ...image_edit import *

class MainWindowLmHelpDialogsMixin:
        def show_lm_help_dialog(self):
            dlg = QDialog(self)
            dlg.setWindowTitle(self._tr("dlg_help_title"))
            dlg.resize(1380, 860)
            dlg.setMinimumSize(1240, 760)
            dlg.setStyleSheet(_help_dialog_qss(self.current_theme))
            layout = QVBoxLayout(dlg)
            scroll = QScrollArea(dlg)
            scroll.setWidgetResizable(True)
            content = QWidget()
            content_layout = QHBoxLayout(content)
            content_layout.setContentsMargins(6, 6, 6, 6)
            content_layout.setSpacing(10)
            default_install_cmd, default_download_cmd = self._whisper_button_commands("Windows")
            def _small_btn(text: str) -> QPushButton:
                button = QPushButton(text)
                button.setFixedHeight(30)
                button.setMinimumWidth(82)
                button.setMaximumWidth(110)
                button.setCursor(Qt.PointingHandCursor)
                return button
            def make_page(content_html: str) -> QTextBrowser:
                browser = QTextBrowser()
                browser.setReadOnly(True)
                browser.setOpenExternalLinks(True)
                browser.setFrameShape(QTextBrowser.NoFrame)
                browser.setOpenLinks(False)
                browser.anchorClicked.connect(QDesktopServices.openUrl)
                browser.setHtml(_help_html(self.current_theme, content_html))
                browser.setMinimumWidth(760)
                browser.document().setDocumentMargin(8)
                return browser
            nav_panel = QWidget()
            nav_panel.setFixedWidth(250)
            nav_panel_layout = QVBoxLayout(nav_panel)
            nav_panel_layout.setContentsMargins(0, 0, 0, 0)
            nav_panel_layout.setSpacing(8)

            nav_list = QListWidget()
            nav_list.setSpacing(4)
            nav_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            nav_list.setTextElideMode(Qt.ElideNone)

            nav_bottom = QListWidget()
            nav_bottom.setSpacing(4)
            nav_bottom.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            nav_bottom.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            nav_bottom.setTextElideMode(Qt.ElideNone)
            nav_bottom.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            # Der untere Sonderreiter braucht unter Windows/Linux wegen Theme-Padding
            # etwas mehr Höhe, sonst wird der Text abgeschnitten.
            nav_bottom.setMinimumHeight(74)
            nav_bottom.setFixedHeight(74)

            stack = QStackedWidget()
            quick_html = self._tr("help_html_quick") + self._build_hardware_requirements_loading_html()
            kraken_html = self._tr("help_html_kraken")
            lm_server_html = self._tr("help_html_lm_server")
            ssh_html = self._tr("help_html_ssh")
            openrouter_html = self._tr("help_html_openrouter")
            page_whisper = QWidget()
            page_whisper_layout = QVBoxLayout(page_whisper)
            page_whisper_layout.setContentsMargins(0, 0, 0, 0)
            page_whisper_layout.setSpacing(8)
            page_whisper_layout.setAlignment(Qt.AlignTop)
            whisper_intro_html = self._tr("help_html_whisper_intro")
            browser_whisper_intro = make_page(whisper_intro_html)
            browser_whisper_intro.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            browser_whisper_intro.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            browser_whisper_intro.setMinimumHeight(260)
            page_whisper_layout.addWidget(browser_whisper_intro, 1)
            btn_info = QLabel(self._tr("help_whisper_download_label"))
            page_whisper_layout.addWidget(btn_info, 0)
            btn_row = QHBoxLayout()
            btn_row.setContentsMargins(0, 0, 0, 0)
            btn_row.setSpacing(6)
            btn_windows = _small_btn(self._tr("help_os_windows"))
            btn_arch = _small_btn(self._tr("help_os_arch"))
            btn_debian = _small_btn(self._tr("help_os_debian"))
            btn_fedora = _small_btn(self._tr("help_os_fedora"))
            btn_mac = _small_btn(self._tr("help_os_macos"))
            hf_cmd_browser = QTextBrowser()
            hf_cmd_browser.setReadOnly(True)
            hf_cmd_browser.setOpenExternalLinks(False)
            hf_cmd_browser.setFrameShape(QTextBrowser.NoFrame)
            hf_cmd_browser.setHtml(_help_pre(f"{default_install_cmd}\n{default_download_cmd}"))
            hf_cmd_browser.setMinimumWidth(760)
            hf_cmd_browser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            hf_cmd_browser.setFixedHeight(96)
            hf_hint_browser = QTextBrowser()
            hf_hint_browser.setReadOnly(True)
            hf_hint_browser.setOpenExternalLinks(False)
            hf_hint_browser.setFrameShape(QTextBrowser.NoFrame)
            hf_hint_browser.setHtml(_help_pre(self._whisper_system_hint("windows")))
            hf_hint_browser.setMinimumWidth(760)
            hf_hint_browser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            hf_hint_browser.setFixedHeight(112)
            def _bind_whisper_button(btn: QPushButton, platform_name: str):
                def _handler():
                    install_cmd, download_cmd = self._whisper_button_commands(platform_name)
                    system_hint = self._whisper_system_hint(platform_name)
                    hf_cmd_browser.setHtml(_help_pre(f"{install_cmd}\n{download_cmd}"))
                    hf_hint_browser.setHtml(_help_pre(system_hint))
                    self.download_whisper_model_from_help_dialog(platform_name, dlg)
                btn.clicked.connect(_handler)
            _bind_whisper_button(btn_windows, "Windows")
            _bind_whisper_button(btn_arch, "Arch")
            _bind_whisper_button(btn_debian, "Debian")
            _bind_whisper_button(btn_fedora, "Fedora")
            _bind_whisper_button(btn_mac, "Mac")
            btn_row.addWidget(btn_windows)
            btn_row.addWidget(btn_arch)
            btn_row.addWidget(btn_debian)
            btn_row.addWidget(btn_fedora)
            btn_row.addWidget(btn_mac)
            btn_row.addStretch()
            page_whisper_layout.addLayout(btn_row, 0)
            page_whisper_layout.addWidget(hf_cmd_browser, 0)
            page_whisper_layout.addWidget(hf_hint_browser, 0)
            shortcuts_html = self._tr("help_html_shortcuts")
            data_protection_html = self._tr("help_html_data_protection")
            legal_html = self._tr("help_html_legal")
            quick_browser = make_page(quick_html)
            stack.addWidget(quick_browser)
            stack.addWidget(make_page(kraken_html))
            stack.addWidget(make_page(lm_server_html))
            stack.addWidget(make_page(ssh_html))
            stack.addWidget(make_page(openrouter_html))
            stack.addWidget(page_whisper)
            stack.addWidget(make_page(shortcuts_html))
            stack.addWidget(make_page(data_protection_html))
            stack.addWidget(make_page(legal_html))
            stack.addWidget(self._make_uninstall_delete_page(dlg))
            nav_items = [
                self._tr("help_nav_quick"),
                self._tr("help_nav_kraken"),
                self._tr("help_nav_lm_server"),
                self._tr("help_nav_ssh"),
                self._tr("help_nav_openrouter"),
                self._tr("help_nav_whisper"),
                self._tr("help_nav_shortcuts"),
                self._tr("help_nav_data_protection"),
                self._tr("help_nav_legal"),
            ]
            for label in nav_items:
                nav_list.addItem(label)
            nav_bottom.addItem(self._tr("help_nav_uninstall_delete"))
            bottom_item = nav_bottom.item(0)
            if bottom_item is not None:
                bottom_item.setSizeHint(QSize(220, 44))

            def _select_top(row: int):
                if row < 0:
                    return
                try:
                    nav_bottom.blockSignals(True)
                    nav_bottom.clearSelection()
                    nav_bottom.setCurrentRow(-1)
                finally:
                    nav_bottom.blockSignals(False)
                stack.setCurrentIndex(row)

            def _select_bottom(row: int):
                if row < 0:
                    return
                try:
                    nav_list.blockSignals(True)
                    nav_list.clearSelection()
                    nav_list.setCurrentRow(-1)
                finally:
                    nav_list.blockSignals(False)
                stack.setCurrentIndex(9)

            nav_list.currentRowChanged.connect(_select_top)
            nav_bottom.currentRowChanged.connect(_select_bottom)
            nav_list.setCurrentRow(0)
            nav_panel_layout.addWidget(nav_list, 1)
            nav_panel_layout.addWidget(nav_bottom, 0)
            content_layout.addWidget(nav_panel, 0)
            content_layout.addWidget(stack, 1)
            scroll.setWidget(content)
            layout.addWidget(scroll)
            buttons = QDialogButtonBox(QDialogButtonBox.Ok)
            buttons.button(QDialogButtonBox.Ok).setText(self._tr("btn_ok"))
            buttons.accepted.connect(dlg.accept)
            layout.addWidget(buttons)
            self._start_help_hardware_refresh(quick_browser)
            dlg.exec()
