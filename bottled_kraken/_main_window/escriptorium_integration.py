from __future__ import annotations

from bottled_kraken.common import (
    QComboBox,
    QDesktopServices,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QTextBrowser,
    QThread,
    QUrl,
    QVBoxLayout,
    QWidget,
    Signal,
    Qt,
    isValid,
    _help_html,
)
from bottled_kraken.escriptorium import (
    ESCRIPTORIUM_DOCUMENTATION_URL,
    ESCRIPTORIUM_PLATFORM_FEDORA,
    ESCRIPTORIUM_PLATFORM_MINT,
    ESCRIPTORIUM_PLATFORM_WINDOWS_WSL,
    EScriptoriumError,
    EScriptoriumManager,
    EScriptoriumStatus,
)
from bottled_kraken.dialogs import BusySpinnerWidget
from bottled_kraken.runtime_logging import get_logger


class EScriptoriumTaskThread(QThread):
    """Run native installation and service work outside the Qt GUI thread."""

    progress = Signal(str, int, str)
    completed = Signal(str, object)
    failed = Signal(str, str, str)

    def __init__(
        self,
        manager: EScriptoriumManager,
        action: str,
        *,
        credentials_labels=None,
        parent=None,
    ):
        super().__init__(parent)
        self.manager = manager
        self.action = action
        self.credentials_labels = dict(credentials_labels or {})

    def run(self):
        try:
            callback = lambda stage, percent, detail: self.progress.emit(stage, percent, detail)
            cancelled = self.isInterruptionRequested
            if self.action == "install":
                result = self.manager.install(
                    callback,
                    self.credentials_labels,
                    cancel_requested=cancelled,
                )
            elif self.action == "start":
                result = self.manager.start(
                    callback,
                    self.credentials_labels,
                    auto_install=False,
                    cancel_requested=cancelled,
                )
            elif self.action == "stop":
                result = self.manager.stop(callback, cancel_requested=cancelled)
            elif self.action == "status":
                result = self.manager.status()
            else:
                raise EScriptoriumError("unexpected", self.action)
            self.completed.emit(self.action, result)
        except EScriptoriumError as exc:
            self.failed.emit(self.action, exc.code, exc.detail)
        except Exception as exc:
            get_logger("escriptorium.ui").exception(
                "Unexpected eScriptorium task failure during %s", self.action
            )
            self.failed.emit(self.action, "unexpected", repr(exc))

    def cancel(self) -> None:
        """Request cancellation; active child commands are terminated safely."""
        self.requestInterruption()


class MainWindowEScriptoriumMixin:
    def _get_escriptorium_manager(self) -> EScriptoriumManager:
        manager = getattr(self, "_escriptorium_manager_instance", None)
        if manager is None:
            manager = EScriptoriumManager()
            self._escriptorium_manager_instance = manager
        return manager

    def _escriptorium_widget_alive(self, widget) -> bool:
        try:
            return bool(widget is not None and isValid(widget))
        except Exception:
            return False

    def _escriptorium_platform_label(self, platform_id: str) -> str:
        keys = {
            ESCRIPTORIUM_PLATFORM_FEDORA: "escriptorium_platform_fedora",
            ESCRIPTORIUM_PLATFORM_MINT: "escriptorium_platform_mint",
            ESCRIPTORIUM_PLATFORM_WINDOWS_WSL: "escriptorium_platform_windows_wsl",
        }
        return self._tr(keys.get(platform_id, "escriptorium_platform_unknown"))

    def _build_escriptorium_platform_combo(self, parent=None) -> QComboBox:
        manager = self._get_escriptorium_manager()
        combo = QComboBox(parent)
        for platform_id in (
            ESCRIPTORIUM_PLATFORM_FEDORA,
            ESCRIPTORIUM_PLATFORM_MINT,
            ESCRIPTORIUM_PLATFORM_WINDOWS_WSL,
        ):
            combo.addItem(self._escriptorium_platform_label(platform_id), platform_id)
        index = combo.findData(manager.platform_id)
        combo.setCurrentIndex(max(0, index))
        combo.setToolTip(self._tr("escriptorium_platform_help"))
        return combo

    def _escriptorium_status_text(self, status: EScriptoriumStatus) -> str:
        if not status.platform_compatible:
            return self._tr("escriptorium_status_platform_mismatch")
        if status.running:
            return self._tr("escriptorium_status_running")
        if not status.installed:
            return self._tr("escriptorium_status_not_installed")
        if not status.prerequisites_available:
            return self._tr("escriptorium_status_prerequisites_missing")
        return self._tr("escriptorium_status_stopped")

    def _escriptorium_error_text(self, code: str, detail: str = "") -> str:
        key = f"escriptorium_error_{code}"
        template = self._tr(key)
        if template == key:
            template = self._tr("escriptorium_error_unexpected")
        clean_detail = str(detail or "").strip()
        if len(clean_detail) > 4000:
            clean_detail = clean_detail[:1200] + "\n\n…\n\n" + clean_detail[-2600:]
        if "{}" in template:
            return template.format(clean_detail or "-")
        if clean_detail:
            return f"{template}\n\n{clean_detail}"
        return template

    def _append_escriptorium_progress(
        self,
        progress_box: QPlainTextEdit | None,
        stage: str,
        percent: int,
        detail: str,
    ) -> None:
        self._escriptorium_last_progress = (str(stage), int(percent), str(detail or ""))
        if not self._escriptorium_widget_alive(progress_box):
            return
        key = f"escriptorium_progress_{stage}"
        text = self._tr(key)
        if text == key:
            text = stage
        suffix = f" — {detail}" if detail else ""
        progress_box.appendPlainText(f"[{percent:3d}%] {text}{suffix}")
        progress_box.verticalScrollBar().setValue(progress_box.verticalScrollBar().maximum())

    def _set_escriptorium_buttons_enabled(self, buttons, enabled: bool) -> None:
        for button in buttons or ():
            if self._escriptorium_widget_alive(button):
                button.setEnabled(bool(enabled))

    def _set_escriptorium_busy_ui(
        self,
        busy_widget,
        cancel_button: QPushButton | None,
        busy: bool,
    ) -> None:
        if self._escriptorium_widget_alive(busy_widget):
            busy_widget.setVisible(bool(busy))
        if self._escriptorium_widget_alive(cancel_button):
            cancel_button.setVisible(bool(busy))
            cancel_button.setEnabled(bool(busy))

    def _cancel_active_escriptorium_task(
        self,
        status_label: QLabel | None = None,
        cancel_button: QPushButton | None = None,
    ) -> None:
        active = getattr(self, "_escriptorium_active_thread", None)
        if active is None or not active.isRunning():
            return
        active.cancel()
        if self._escriptorium_widget_alive(status_label):
            status_label.setText(self._tr("escriptorium_status_cancelling"))
        if self._escriptorium_widget_alive(cancel_button):
            cancel_button.setEnabled(False)

    def _refresh_escriptorium_status_label(self, status_label: QLabel | None) -> EScriptoriumStatus:
        status = self._get_escriptorium_manager().status()
        if self._escriptorium_widget_alive(status_label):
            status_label.setText(self._escriptorium_status_text(status))
        return status

    def _attach_escriptorium_active_task_view(
        self,
        *,
        status_label: QLabel | None,
        progress_box: QPlainTextEdit | None,
        buttons=(),
        busy_widget=None,
        cancel_button: QPushButton | None = None,
    ) -> bool:
        active = getattr(self, "_escriptorium_active_thread", None)
        if active is None or not active.isRunning():
            return False
        self._set_escriptorium_buttons_enabled(buttons, False)
        self._set_escriptorium_busy_ui(busy_widget, cancel_button, True)
        if self._escriptorium_widget_alive(status_label):
            status_label.setText(self._tr("escriptorium_status_working"))
        last = getattr(self, "_escriptorium_last_progress", None)
        if last and self._escriptorium_widget_alive(progress_box):
            self._append_escriptorium_progress(progress_box, *last)
        active.progress.connect(
            lambda stage, percent, detail: self._append_escriptorium_progress(
                progress_box, stage, percent, detail
            )
        )

        def _finished_view():
            self._set_escriptorium_buttons_enabled(buttons, True)
            self._set_escriptorium_busy_ui(busy_widget, cancel_button, False)
            if self._escriptorium_widget_alive(status_label):
                self._refresh_escriptorium_status_label(status_label)

        active.finished.connect(_finished_view)
        return True

    def _run_escriptorium_task(
        self,
        action: str,
        *,
        parent_dialog=None,
        status_label: QLabel | None = None,
        progress_box: QPlainTextEdit | None = None,
        buttons=(),
        busy_widget=None,
        cancel_button: QPushButton | None = None,
        on_success=None,
    ) -> None:
        if self._attach_escriptorium_active_task_view(
            status_label=status_label,
            progress_box=progress_box,
            buttons=buttons,
            busy_widget=busy_widget,
            cancel_button=cancel_button,
        ):
            return

        manager = self._get_escriptorium_manager()
        credentials_labels = {
            "header": self._tr("escriptorium_credentials_header"),
            "user": self._tr("escriptorium_credentials_user"),
            "password": self._tr("escriptorium_credentials_password"),
        }
        thread = EScriptoriumTaskThread(
            manager,
            action,
            credentials_labels=credentials_labels,
            parent=self,
        )
        self._escriptorium_active_thread = thread
        self._escriptorium_last_progress = None
        self._set_escriptorium_buttons_enabled(buttons, False)
        self._set_escriptorium_busy_ui(busy_widget, cancel_button, True)
        if self._escriptorium_widget_alive(status_label):
            status_label.setText(self._tr("escriptorium_status_working"))
        if self._escriptorium_widget_alive(progress_box):
            progress_box.clear()

        thread.progress.connect(
            lambda stage, percent, detail: self._append_escriptorium_progress(
                progress_box, stage, percent, detail
            )
        )

        cleaned = {"value": False}

        def _cleanup_ui():
            if cleaned["value"]:
                return
            cleaned["value"] = True
            self._set_escriptorium_buttons_enabled(buttons, True)
            self._set_escriptorium_busy_ui(busy_widget, cancel_button, False)

        def _completed(done_action: str, status: EScriptoriumStatus):
            _cleanup_ui()
            if self._escriptorium_widget_alive(status_label):
                status_label.setText(self._escriptorium_status_text(status))
            if done_action == "install":
                message = self._tr("escriptorium_install_success", status.install_dir)
            elif done_action == "start":
                message = self._tr("escriptorium_start_success")
            elif done_action == "stop":
                message = self._tr("escriptorium_stop_success")
            else:
                message = ""
            if message and self._escriptorium_widget_alive(progress_box):
                progress_box.appendPlainText(message)
            if callable(on_success):
                on_success(done_action, status)

        def _failed(failed_action: str, code: str, detail: str):
            _cleanup_ui()
            if self._escriptorium_widget_alive(status_label):
                self._refresh_escriptorium_status_label(status_label)
            message = self._escriptorium_error_text(code, detail)
            if code == "cancelled":
                QMessageBox.information(
                    parent_dialog or self,
                    self._tr("dlg_escriptorium_title"),
                    message,
                )
            else:
                QMessageBox.critical(
                    parent_dialog or self,
                    self._tr("dlg_escriptorium_title"),
                    message,
                )
            get_logger("escriptorium.ui").error(
                "eScriptorium task %s failed: %s (%s)",
                failed_action,
                code,
                detail,
            )

        def _finished():
            _cleanup_ui()
            if getattr(self, "_escriptorium_active_thread", None) is thread:
                self._escriptorium_active_thread = None
            thread.deleteLater()

        thread.completed.connect(_completed)
        thread.failed.connect(_failed)
        thread.finished.connect(_finished)
        thread.start()

    def _open_escriptorium_browser(
        self,
        parent=None,
        *,
        allow_finishing_start_task: bool = False,
    ) -> None:
        manager = self._get_escriptorium_manager()
        active = getattr(self, "_escriptorium_active_thread", None)
        task_blocks_open = (
            active is not None
            and active.isRunning()
            and not allow_finishing_start_task
        )
        if task_blocks_open or not manager.server_is_ready(timeout=1.5):
            QMessageBox.information(
                parent or self,
                self._tr("dlg_escriptorium_title"),
                self._tr("escriptorium_error_server_not_running", manager.server_url),
            )
            return
        if manager.open_browser():
            return
        # Final Qt fallback for desktop environments without a native launcher.
        if QDesktopServices.openUrl(QUrl(manager.server_url)):
            return
        QMessageBox.warning(
            parent or self,
            self._tr("dlg_escriptorium_title"),
            self._tr("escriptorium_error_browser_open_failed", manager.server_url),
        )

    def _open_escriptorium_folder(self, parent=None) -> None:
        manager = self._get_escriptorium_manager()
        if manager.open_folder():
            return
        # Last Qt fallback for uncommon desktop environments.
        if QDesktopServices.openUrl(QUrl.fromLocalFile(str(manager.paths.profile))):
            return
        QMessageBox.warning(
            parent or self,
            self._tr("dlg_escriptorium_title"),
            self._tr("escriptorium_error_folder_open_failed", str(manager.paths.profile)),
        )

    def _open_escriptorium_credentials(self, parent=None) -> None:
        manager = self._get_escriptorium_manager()
        if not manager.paths.credentials.is_file():
            QMessageBox.information(
                parent or self,
                self._tr("dlg_escriptorium_title"),
                self._tr("escriptorium_credentials_missing"),
            )
            return
        if manager.open_credentials():
            return
        if QDesktopServices.openUrl(QUrl.fromLocalFile(str(manager.paths.credentials))):
            return
        QMessageBox.warning(
            parent or self,
            self._tr("dlg_escriptorium_title"),
            self._tr("escriptorium_error_folder_open_failed", str(manager.paths.credentials)),
        )

    def _connect_escriptorium_platform_combo(
        self,
        combo: QComboBox,
        *,
        status_label: QLabel,
        install_field: QLineEdit | None = None,
        credentials_field: QLineEdit | None = None,
        target_label: QLabel | None = None,
    ) -> None:
        def _changed(_index: int):
            platform_id = str(combo.currentData() or "")
            manager = self._get_escriptorium_manager()
            try:
                manager.set_platform(platform_id)
            except ValueError:
                return
            if self._escriptorium_widget_alive(install_field):
                install_field.setText(str(manager.paths.profile))
            if self._escriptorium_widget_alive(credentials_field):
                credentials_field.setText(str(manager.paths.credentials))
            if self._escriptorium_widget_alive(target_label):
                target_label.setText(self._tr("help_escriptorium_target", str(manager.paths.profile)))
            self._refresh_escriptorium_status_label(status_label)

        combo.currentIndexChanged.connect(_changed)

    def show_escriptorium_dialog(self):
        manager = self._get_escriptorium_manager()
        dlg = QDialog(self)
        dlg.setWindowTitle(self._tr("dlg_escriptorium_title"))
        dlg.resize(800, 500)
        dlg.setMinimumSize(700, 450)
        layout = QVBoxLayout(dlg)

        title = QLabel(self._tr("escriptorium_dialog_intro"))
        title.setWordWrap(True)
        layout.addWidget(title)

        platform_row = QHBoxLayout()
        platform_label = QLabel(self._tr("escriptorium_label_platform"))
        platform_label.setMinimumWidth(150)
        platform_combo = self._build_escriptorium_platform_combo(dlg)
        platform_row.addWidget(platform_label)
        platform_row.addWidget(platform_combo, 1)
        layout.addLayout(platform_row)

        platform_help = QLabel(self._tr("escriptorium_platform_help"))
        platform_help.setWordWrap(True)
        layout.addWidget(platform_help)

        status_row = QHBoxLayout()
        status_row.addWidget(QLabel(self._tr("escriptorium_label_status")))
        busy_spinner = BusySpinnerWidget(dlg, diameter=26)
        busy_spinner.hide()
        status_row.addWidget(busy_spinner)
        status_label = QLabel(self._tr("escriptorium_status_checking"))
        status_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        status_row.addWidget(status_label, 1)
        refresh_button = QPushButton(self._tr("escriptorium_btn_refresh"))
        status_row.addWidget(refresh_button)
        layout.addLayout(status_row)

        fields = {}
        for label_key, name, value in (
            ("escriptorium_label_install_dir", "install", str(manager.paths.profile)),
            ("escriptorium_label_server_url", "server", manager.server_url),
            ("escriptorium_label_credentials", "credentials", str(manager.paths.credentials)),
        ):
            row = QHBoxLayout()
            label = QLabel(self._tr(label_key))
            label.setMinimumWidth(150)
            field = QLineEdit(value)
            field.setReadOnly(True)
            fields[name] = field
            row.addWidget(label)
            row.addWidget(field, 1)
            layout.addLayout(row)

        progress_box = QPlainTextEdit()
        progress_box.setReadOnly(True)
        progress_box.setPlaceholderText(self._tr("escriptorium_progress_placeholder"))
        progress_box.setMaximumBlockCount(2000)
        progress_box.setFixedHeight(135)
        layout.addWidget(progress_box)

        primary_actions = QHBoxLayout()
        secondary_actions = QHBoxLayout()
        install_button = QPushButton(self._tr("help_escriptorium_download_button"))
        start_button = QPushButton(self._tr("escriptorium_btn_start"))
        stop_button = QPushButton(self._tr("escriptorium_btn_stop"))
        browser_button = QPushButton(self._tr("escriptorium_btn_open_browser"))
        folder_button = QPushButton(self._tr("escriptorium_btn_open_folder"))
        credentials_button = QPushButton(self._tr("escriptorium_btn_open_credentials"))
        help_button = QPushButton(self._tr("escriptorium_btn_install_help"))
        cancel_button = QPushButton(self._tr("btn_cancel"))
        cancel_button.hide()
        for button in (install_button, start_button, stop_button, browser_button):
            primary_actions.addWidget(button)
        primary_actions.addWidget(cancel_button)
        primary_actions.addStretch()
        for button in (folder_button, credentials_button, help_button):
            secondary_actions.addWidget(button)
        secondary_actions.addStretch()
        layout.addLayout(primary_actions)
        layout.addLayout(secondary_actions)

        all_task_buttons = (
            install_button,
            start_button,
            stop_button,
            browser_button,
            refresh_button,
            platform_combo,
        )

        def _after_start(done_action: str, _status: EScriptoriumStatus):
            if done_action == "start":
                # ``completed`` is emitted immediately before QThread finishes.
                # Readiness has already been confirmed by manager.start(), so
                # allow this final start callback through the active-task guard.
                self._open_escriptorium_browser(
                    dlg,
                    allow_finishing_start_task=True,
                )

        install_button.clicked.connect(
            lambda: self._run_escriptorium_task(
                "install",
                parent_dialog=dlg,
                status_label=status_label,
                progress_box=progress_box,
                buttons=all_task_buttons,
                busy_widget=busy_spinner,
                cancel_button=cancel_button,
            )
        )
        start_button.clicked.connect(
            lambda: self._run_escriptorium_task(
                "start",
                parent_dialog=dlg,
                status_label=status_label,
                progress_box=progress_box,
                buttons=all_task_buttons,
                busy_widget=busy_spinner,
                cancel_button=cancel_button,
                on_success=_after_start,
            )
        )
        stop_button.clicked.connect(
            lambda: self._run_escriptorium_task(
                "stop",
                parent_dialog=dlg,
                status_label=status_label,
                progress_box=progress_box,
                buttons=all_task_buttons,
                busy_widget=busy_spinner,
                cancel_button=cancel_button,
            )
        )
        cancel_button.clicked.connect(
            lambda: self._cancel_active_escriptorium_task(status_label, cancel_button)
        )
        refresh_button.clicked.connect(lambda: self._refresh_escriptorium_status_label(status_label))
        browser_button.clicked.connect(lambda: self._open_escriptorium_browser(dlg))
        folder_button.clicked.connect(lambda: self._open_escriptorium_folder(dlg))
        credentials_button.clicked.connect(lambda: self._open_escriptorium_credentials(dlg))
        help_button.clicked.connect(lambda: self.show_lm_help_dialog("escriptorium"))
        self._connect_escriptorium_platform_combo(
            platform_combo,
            status_label=status_label,
            install_field=fields["install"],
            credentials_field=fields["credentials"],
        )

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.button(QDialogButtonBox.Close).setText(self._tr("btn_close"))
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        self._refresh_escriptorium_status_label(status_label)
        self._attach_escriptorium_active_task_view(
            status_label=status_label,
            progress_box=progress_box,
            buttons=all_task_buttons,
            busy_widget=busy_spinner,
            cancel_button=cancel_button,
        )
        dlg.exec()

    def _make_escriptorium_help_page(self, parent_dialog: QDialog) -> QWidget:
        manager = self._get_escriptorium_manager()
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        browser = QTextBrowser()
        browser.setReadOnly(True)
        browser.setOpenExternalLinks(True)
        browser.setFrameShape(QTextBrowser.NoFrame)
        browser.setHtml(_help_html(self.current_theme, self._tr("help_html_escriptorium")))
        browser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        browser.setMinimumHeight(280)
        layout.addWidget(browser, 1)

        platform_row = QHBoxLayout()
        platform_row.addWidget(QLabel(self._tr("escriptorium_label_platform")))
        platform_combo = self._build_escriptorium_platform_combo(page)
        platform_row.addWidget(platform_combo, 1)
        layout.addLayout(platform_row)

        status_row = QHBoxLayout()
        status_row.addWidget(QLabel(self._tr("escriptorium_label_status")))
        busy_spinner = BusySpinnerWidget(page, diameter=24)
        busy_spinner.hide()
        status_row.addWidget(busy_spinner)
        status_label = QLabel(self._tr("escriptorium_status_checking"))
        status_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        status_row.addWidget(status_label, 1)
        layout.addLayout(status_row)

        path_label = QLabel(self._tr("help_escriptorium_target", str(manager.paths.profile)))
        path_label.setWordWrap(True)
        path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(path_label)

        progress_box = QPlainTextEdit()
        progress_box.setReadOnly(True)
        progress_box.setPlaceholderText(self._tr("escriptorium_progress_placeholder"))
        progress_box.setMaximumBlockCount(2000)
        progress_box.setFixedHeight(125)
        layout.addWidget(progress_box)

        button_row = QHBoxLayout()
        download_button = QPushButton(self._tr("help_escriptorium_download_button"))
        docs_button = QPushButton(self._tr("help_escriptorium_docs_button"))
        folder_button = QPushButton(self._tr("escriptorium_btn_open_folder"))
        credentials_button = QPushButton(self._tr("escriptorium_btn_open_credentials"))
        cancel_button = QPushButton(self._tr("btn_cancel"))
        cancel_button.hide()
        button_row.addWidget(download_button)
        button_row.addWidget(docs_button)
        button_row.addWidget(folder_button)
        button_row.addWidget(credentials_button)
        button_row.addWidget(cancel_button)
        button_row.addStretch()
        layout.addLayout(button_row)

        task_buttons = (download_button, platform_combo)
        download_button.clicked.connect(
            lambda: self._run_escriptorium_task(
                "install",
                parent_dialog=parent_dialog,
                status_label=status_label,
                progress_box=progress_box,
                buttons=task_buttons,
                busy_widget=busy_spinner,
                cancel_button=cancel_button,
            )
        )
        cancel_button.clicked.connect(
            lambda: self._cancel_active_escriptorium_task(status_label, cancel_button)
        )
        docs_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(ESCRIPTORIUM_DOCUMENTATION_URL))
        )
        folder_button.clicked.connect(lambda: self._open_escriptorium_folder(parent_dialog))
        credentials_button.clicked.connect(lambda: self._open_escriptorium_credentials(parent_dialog))
        self._connect_escriptorium_platform_combo(
            platform_combo,
            status_label=status_label,
            target_label=path_label,
        )
        self._refresh_escriptorium_status_label(status_label)
        self._attach_escriptorium_active_task_view(
            status_label=status_label,
            progress_box=progress_box,
            buttons=task_buttons,
            busy_widget=busy_spinner,
            cancel_button=cancel_button,
        )
        return page


__all__ = ["EScriptoriumTaskThread", "MainWindowEScriptoriumMixin"]
