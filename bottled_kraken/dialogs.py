"""Allgemeine Dialoge und Statusfenster."""

from .shared import *


def _resolve_tr_and_parent(tr, parent=None):
    """Erlaubt sowohl (title, tr, parent) als auch (title, parent)."""
    if parent is None and tr is not None and not callable(tr):
        candidate_parent = tr
        tr = getattr(candidate_parent, "_tr", None)
        parent = candidate_parent
    if not callable(tr):
        tr = (lambda key, *args: key)
    return tr, parent


class ProgressStatusDialog(QDialog):
    cancel_requested = Signal()
    def __init__(self, title: str, tr, parent=None):
        tr, parent = _resolve_tr_and_parent(tr, parent)
        super().__init__(parent)
        self._tr = tr
        self.setWindowTitle(title)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        self.setWindowFlag(Qt.Dialog, True)
        if parent is not None:
            self.setWindowModality(Qt.WindowModal)
        else:
            self.setWindowModality(Qt.ApplicationModal)
        lay = QVBoxLayout(self)
        self.lbl_status = QLabel(self._tr("progress_status_ready"))
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setMinimumWidth(320)
        self.lbl_status.setMaximumWidth(520)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)  # sichtbarer Balken
        self.progress.setValue(0)
        self.progress.setFormat("%p%")
        self.btn_cancel = QPushButton(self._tr("btn_cancel"))
        self.btn_cancel.clicked.connect(self.cancel_requested.emit)
        lay.addWidget(self.lbl_status)
        lay.addWidget(self.progress)
        lay.addWidget(self.btn_cancel)
        self.adjustSize()
    def set_status(self, text: str):
        self.lbl_status.setText(text)
        self.adjustSize()
    def set_progress(self, value: int):
        raw = max(0, int(value))
        if raw <= 100:
            percent = float(raw)
        else:
            percent = raw / 10.0
        percent = max(0.0, min(100.0, percent))
        if self.progress.minimum() != 0 or self.progress.maximum() != 100:
            self.progress.setRange(0, 100)
        self.progress.setValue(int(round(percent)))
        self.progress.setFormat(f"{percent:.1f}%")


class BusySpinnerWidget(QWidget):
    def __init__(self, parent=None, diameter: int = 42):
        super().__init__(parent)
        self._diameter = max(24, int(diameter))
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance)
        self._timer.start(90)
        self.setMinimumSize(self.sizeHint())

    def sizeHint(self):
        return QSize(self._diameter, self._diameter)

    def _advance(self):
        self._angle = (self._angle + 30) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect().adjusted(4, 4, -4, -4)
        pen_bg = QPen(QColor(180, 180, 180, 90), 4)
        pen_bg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_bg)
        painter.drawEllipse(rect)
        pen_fg = QPen(QColor(48, 127, 226), 4)
        pen_fg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_fg)
        start = int((-self._angle + 90) * 16)
        span = int(-110 * 16)
        painter.drawArc(rect, start, span)


class BusyStatusDialog(QDialog):
    cancel_requested = Signal()

    def __init__(self, title: str, message: str, tr, parent=None):
        tr, parent = _resolve_tr_and_parent(tr, parent)
        super().__init__(parent)
        self._tr = tr
        self._base_message = str(message or "")
        self.setWindowTitle(title)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        self.setWindowFlag(Qt.Dialog, True)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        if parent is not None:
            self.setWindowModality(Qt.WindowModal)
        else:
            self.setWindowModality(Qt.ApplicationModal)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)
        row = QHBoxLayout()
        row.setSpacing(12)
        self.spinner = BusySpinnerWidget(self, diameter=42)
        row.addWidget(self.spinner, 0, Qt.AlignTop)
        self.lbl_status = QLabel(self._base_message)
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setMinimumWidth(320)
        self.lbl_status.setMaximumWidth(520)
        row.addWidget(self.lbl_status, 1)
        lay.addLayout(row)
        self.btn_cancel = QPushButton(self._tr("btn_cancel"))
        self.btn_cancel.clicked.connect(self.cancel_requested.emit)
        lay.addWidget(self.btn_cancel, 0, Qt.AlignRight)
        self.adjustSize()

    def set_status(self, text: str):
        # Absichtlich keine Fortschrittszahlen oder Prozentwerte im Dialog anzeigen.
        self.lbl_status.setText(self._base_message)
        self.adjustSize()

    def set_progress(self, value: int):
        return


class VoiceRecordDialog(QDialog):
    start_requested = Signal()
    stop_requested = Signal()
    cancel_requested = Signal()
    def __init__(self, tr, parent=None):
        super().__init__(parent)
        self._tr = tr
        self._recording = False
        self._processing = False
        self.setWindowTitle(self._tr("voice_record_title"))
        self.setModal(True)
        lay = QVBoxLayout(self)
        self.lbl_info = QLabel(self._tr("voice_record_info"))
        lay.addWidget(self.lbl_info)
        btn_row = QHBoxLayout()
        self.btn_toggle = QPushButton(self._tr("voice_record_start"))
        self.btn_cancel = QPushButton(self._tr("btn_cancel"))
        btn_row.addWidget(self.btn_toggle)
        btn_row.addWidget(self.btn_cancel)
        lay.addLayout(btn_row)
        self.btn_toggle.clicked.connect(self._on_toggle)
        self.btn_cancel.clicked.connect(self._on_cancel)
        # Start-Button soll standardmäßig aktiv sein
        self.btn_toggle.setDefault(True)
        self.btn_toggle.setAutoDefault(True)
        self.btn_cancel.setDefault(False)
        self.btn_cancel.setAutoDefault(False)
        self.btn_toggle.setFocus(Qt.OtherFocusReason)
    def _keep_start_button_primary(self):
        # Start-Button soll optisch/fokusmäßig immer der primäre Button bleiben
        self.btn_toggle.setDefault(True)
        self.btn_toggle.setAutoDefault(True)
        self.btn_cancel.setDefault(False)
        self.btn_cancel.setAutoDefault(False)
        self.btn_toggle.setFocus(Qt.OtherFocusReason)
    def _on_toggle(self):
        # Während Whisper verarbeitet, Klicks auf "Aufnahme starten" ignorieren
        if self._processing:
            return
        if not self._recording:
            self._recording = True
            self._processing = False
            self.btn_toggle.setText(self._tr("voice_record_stop"))
            self.lbl_info.setText(self._tr("voice_record_info"))
            self._keep_start_button_primary()
            self.start_requested.emit()
        else:
            # Aufnahme endet jetzt, ab hier blockieren bis Whisper fertig ist
            self._recording = False
            self._processing = True
            # Button soll optisch wieder "Aufnahme starten" zeigen,
            # aber intern noch gesperrt bleiben
            self.btn_toggle.setText(self._tr("voice_record_start"))
            self.lbl_info.setText(self._tr("voice_record_processing"))
            self._keep_start_button_primary()
            self.stop_requested.emit()
    def _on_cancel(self):
        self.cancel_requested.emit()
        self.reject()
    def set_recording_state(self, recording: bool):
        self._recording = bool(recording)
        self._processing = False
        self.btn_toggle.setEnabled(True)
        self.btn_toggle.setText(self._tr("voice_record_stop") if self._recording else self._tr("voice_record_start"))
        self.lbl_info.setText(self._tr("voice_record_info"))
        self._keep_start_button_primary()
    def closeEvent(self, event):
        super().closeEvent(event)


class ExportModeDialog(QDialog):
    def __init__(self, tr, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("export_choose_mode_title"))
        self.choice = None
        lay = QVBoxLayout(self)
        self.rb_all = QRadioButton(tr("export_mode_all"))
        self.rb_sel = QRadioButton(tr("export_mode_selected"))
        self.rb_all.setChecked(True)
        lay.addWidget(self.rb_all)
        lay.addWidget(self.rb_sel)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)
    def accept(self):
        self.choice = "all" if self.rb_all.isChecked() else "selected"
        super().accept()


class ExportSelectFilesDialog(QDialog):
    def __init__(self, tr, items: List[TaskItem], parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("export_select_files_title"))
        self.selected_paths: List[str] = []
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(tr("export_select_files_hint")))
        self.listw = QListWidget()
        self.listw.setSelectionMode(QAbstractItemView.ExtendedSelection)
        for it in items:
            li = QListWidgetItem(it.display_name)
            li.setData(Qt.UserRole, it.path)
            self.listw.addItem(li)
        lay.addWidget(self.listw)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._on_ok)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)
    def _on_ok(self):
        paths = [i.data(Qt.UserRole) for i in self.listw.selectedItems()]
        self.selected_paths = [p for p in paths if p]
        self.accept()

__all__ = [name for name in globals() if not name.startswith("__")]
