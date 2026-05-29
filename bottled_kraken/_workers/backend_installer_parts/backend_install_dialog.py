from typing import Callable, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)
from bottled_kraken._workers.backend_installer_parts.backend_installer_helpers import (
    backend_dir,
)
from bottled_kraken._workers.backend_installer_parts.backend_installer_helpers import _call_tr
from bottled_kraken._workers.backend_installer_parts.backend_installer_worker import BackendInstallerWorker
class BackendInstallDialog(QDialog):
    install_finished = Signal(bool, str)
    def __init__(self, kind: str, tr_func: Optional[Callable[..., str]] = None, parent=None):
        super().__init__(parent)
        self.kind = kind
        self.tr_func = tr_func
        self.worker: Optional[BackendInstallerWorker] = None
        self.setWindowTitle(self._dialog_title())
        self.resize(760, 520)
        self.title_label = QLabel(f"<b>{self._dialog_title()}</b>")
        self.title_label.setTextFormat(Qt.RichText)
        self.info_label = QLabel(self._intro_text())
        self.info_label.setWordWrap(True)
        self.target_label = QLabel(f"{self._tr('backend_install_target')}<br><code>{backend_dir(kind)}</code>")
        self.target_label.setTextFormat(Qt.RichText)
        self.target_label.setWordWrap(True)
        self.warning_label = QLabel(self._tr("backend_install_warning"))
        self.warning_label.setWordWrap(True)
        self.force_checkbox = QCheckBox(self._tr("backend_install_force"))
        self.log_edit = QPlainTextEdit()
        self.log_edit.setReadOnly(True)
        self.buttons = QDialogButtonBox()
        self.start_button = QPushButton(self._tr("backend_install_start"))
        self.close_button = QPushButton(self._tr("backend_install_close"))
        self.buttons.addButton(self.start_button, QDialogButtonBox.ActionRole)
        self.buttons.addButton(self.close_button, QDialogButtonBox.RejectRole)
        self.start_button.clicked.connect(self.start_install)
        self.close_button.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.title_label)
        layout.addWidget(self.info_label)
        layout.addWidget(self.target_label)
        layout.addWidget(self.warning_label)
        layout.addWidget(self.force_checkbox)
        layout.addWidget(QLabel(self._tr("backend_install_log")))
        layout.addWidget(self.log_edit, 1)
        layout.addWidget(self.buttons)
    def _tr(self, key: str, *args) -> str:
        return _call_tr(self.tr_func, key, *args)
    def _dialog_title(self) -> str:
        if self.kind == "amd-rocm":
            return self._tr("backend_install_title_rocm")
        return self._tr("backend_install_title_nvidia")
    def _intro_text(self) -> str:
        if self.kind == "amd-rocm":
            return self._tr("backend_install_intro_rocm")
        return self._tr("backend_install_intro_nvidia")
    def _append(self, text: str):
        self.log_edit.appendPlainText(str(text).rstrip())
    def start_install(self):
        if self.worker is not None and self.worker.isRunning():
            QMessageBox.warning(self, self._tr("backend_install_failed"), self._tr("backend_install_running"))
            return
        self.start_button.setEnabled(False)
        self.force_checkbox.setEnabled(False)
        self.worker = BackendInstallerWorker(self.kind, force=self.force_checkbox.isChecked(), parent=self)
        self.worker.line.connect(self._append)
        self.worker.finished_ok.connect(self._finished)
        self.worker.start()
    def _finished(self, ok: bool, message: str):
        self.start_button.setEnabled(True)
        self.force_checkbox.setEnabled(True)
        self.install_finished.emit(bool(ok), self.kind)
        if ok:
            self._append(self._tr("backend_install_success"))
            QMessageBox.information(self, self._tr("backend_install_finished"), self._tr("backend_install_success"))
        else:
            self._append(self._tr("backend_install_failed"))
            QMessageBox.warning(self, self._tr("backend_install_failed"), message or self._tr("backend_install_failed"))
    def reject(self):
        if self.worker is not None and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                self._tr("backend_install_close"),
                self._tr("backend_install_running"),
            )
            if reply != QMessageBox.Yes:
                return
            self.worker.cancel()
        super().reject()
