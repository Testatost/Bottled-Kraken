from bottled_kraken.common import (
    _help_dialog_qss,
    _help_html,
    _help_pre,
)
from bottled_kraken.common import (
    QDesktopServices,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QProgressDialog,
    QScrollArea,
    QSize,
    QSizePolicy,
    QStackedWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
    Qt,
)
from bottled_kraken.kraken_update import current_kraken_summary
from bottled_kraken._workers.kraken_update_worker import KrakenUpdateWorker


class MainWindowLmHelpDialogsMixin:
        def show_lm_help_dialog(self, initial_page=None):
            if isinstance(initial_page, bool):
                initial_page = None
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
            nav_bottom.setMinimumHeight(74)
            nav_bottom.setFixedHeight(74)
            stack = QStackedWidget()
            quick_html = self._tr("help_html_quick") + self._build_hardware_requirements_loading_html()
            kraken_html = self._tr("help_html_kraken")
            lm_server_html = self._tr("help_html_lm_server")
            ssh_html = self._tr("help_html_ssh")
            openrouter_html = self._tr("help_html_openrouter")

            page_kraken = QWidget()
            page_kraken_layout = QVBoxLayout(page_kraken)
            page_kraken_layout.setContentsMargins(0, 0, 0, 0)
            page_kraken_layout.setSpacing(8)
            browser_kraken = make_page(kraken_html)
            page_kraken_layout.addWidget(browser_kraken, 1)
            kraken_summary = current_kraken_summary()
            kraken_status = QLabel(
                self._tr(
                    "kraken_update_current_version",
                    kraken_summary.get("version", "-"),
                )
            )
            kraken_status.setWordWrap(True)
            page_kraken_layout.addWidget(kraken_status, 0)
            kraken_update_row = QHBoxLayout()
            kraken_update_row.setContentsMargins(0, 0, 0, 0)
            kraken_update_button = QPushButton(self._tr("kraken_update_button"))
            kraken_update_button.setMinimumHeight(34)
            kraken_update_button.setToolTip(self._tr("kraken_update_button_tip"))
            kraken_update_row.addWidget(kraken_update_button, 0)
            kraken_source = QLabel(self._tr("kraken_update_source"))
            kraken_source.setWordWrap(True)
            kraken_update_row.addWidget(kraken_source, 1)
            page_kraken_layout.addLayout(kraken_update_row, 0)

            def _start_kraken_update():
                existing = getattr(self, "_kraken_update_worker", None)
                if existing is not None and existing.isRunning():
                    QMessageBox.information(
                        self,
                        self._tr("info_title"),
                        self._tr("kraken_update_already_running"),
                    )
                    return
                answer = QMessageBox.question(
                    self,
                    self._tr("kraken_update_confirm_title"),
                    self._tr("kraken_update_confirm_text"),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if answer != QMessageBox.Yes:
                    return
                progress_dialog = QProgressDialog(
                    self._tr("kraken_update_checking"),
                    self._tr("btn_cancel"),
                    0,
                    100,
                    self,
                )
                progress_dialog.setWindowTitle(self._tr("kraken_update_dialog_title"))
                progress_dialog.setMinimumDuration(0)
                progress_dialog.setAutoClose(False)
                progress_dialog.setAutoReset(False)
                progress_dialog.setValue(0)
                worker = KrakenUpdateWorker(self)
                self._kraken_update_worker = worker
                self._kraken_update_progress_dialog = progress_dialog
                kraken_update_button.setEnabled(False)

                def _on_progress(percent: int, detail: str):
                    progress_dialog.setValue(max(0, min(100, int(percent))))
                    progress_dialog.setLabelText(str(detail))
                    kraken_status.setText(str(detail))

                def _finish_common():
                    kraken_update_button.setEnabled(True)
                    progress_dialog.close()
                    self._kraken_update_worker = None
                    self._kraken_update_progress_dialog = None

                def _on_completed(version: str, sha: str, changed: bool):
                    _finish_common()
                    if changed:
                        kraken_status.setText(
                            self._tr("kraken_update_pending_restart", version, sha[:12])
                        )
                        QMessageBox.information(
                            self,
                            self._tr("info_title"),
                            self._tr("kraken_update_success", version, sha[:12]),
                        )
                    else:
                        kraken_status.setText(self._tr("kraken_update_up_to_date", version))
                        QMessageBox.information(
                            self,
                            self._tr("info_title"),
                            self._tr("kraken_update_up_to_date", version),
                        )

                def _on_failed(message: str):
                    _finish_common()
                    if str(message).strip().lower() == "cancelled":
                        kraken_status.setText(self._tr("kraken_update_cancelled"))
                        return
                    kraken_status.setText(self._tr("kraken_update_failed", message))
                    QMessageBox.warning(
                        self,
                        self._tr("warn_title"),
                        self._tr("kraken_update_failed", message),
                    )

                worker.progress.connect(_on_progress)
                worker.completed.connect(_on_completed)
                worker.failed.connect(_on_failed)
                worker.finished.connect(worker.deleteLater)
                progress_dialog.canceled.connect(worker.cancel)
                progress_dialog.show()
                worker.start()

            kraken_update_button.clicked.connect(_start_kraken_update)

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
            stack.addWidget(page_kraken)
            stack.addWidget(make_page(lm_server_html))
            stack.addWidget(make_page(ssh_html))
            stack.addWidget(make_page(openrouter_html))
            stack.addWidget(page_whisper)
            stack.addWidget(self._make_escriptorium_help_page(dlg))
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
                self._tr("help_nav_escriptorium"),
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
                stack.setCurrentIndex(10)
            nav_list.currentRowChanged.connect(_select_top)
            nav_bottom.currentRowChanged.connect(_select_bottom)
            initial_rows = {"escriptorium": 6}
            nav_list.setCurrentRow(initial_rows.get(str(initial_page or "").strip().lower(), 0))
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
