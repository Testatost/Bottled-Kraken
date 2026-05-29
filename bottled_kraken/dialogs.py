from bottled_kraken.common import (
    List,
    QAbstractItemView,
    QApplication,
    QColor,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPainter,
    QPen,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSize,
    QTimer,
    QVBoxLayout,
    QWidget,
    Qt,
    Signal,
    TaskItem,
    re,
)
def _resolve_tr_and_parent(tr, parent=None):
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
        self.progress.setRange(0, 100)
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
        self.btn_toggle.setDefault(True)
        self.btn_toggle.setAutoDefault(True)
        self.btn_cancel.setDefault(False)
        self.btn_cancel.setAutoDefault(False)
        self.btn_toggle.setFocus(Qt.OtherFocusReason)
    def _keep_start_button_primary(self):
        self.btn_toggle.setDefault(True)
        self.btn_toggle.setAutoDefault(True)
        self.btn_cancel.setDefault(False)
        self.btn_cancel.setAutoDefault(False)
        self.btn_toggle.setFocus(Qt.OtherFocusReason)
    def _on_toggle(self):
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
            self._recording = False
            self._processing = True
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
        try:
            bb.button(QDialogButtonBox.Ok).setText(tr("btn_ok"))
            bb.button(QDialogButtonBox.Cancel).setText(tr("btn_cancel"))
        except Exception:
            pass
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
        try:
            bb.button(QDialogButtonBox.Ok).setText(tr("btn_ok"))
            bb.button(QDialogButtonBox.Cancel).setText(tr("btn_cancel"))
        except Exception:
            pass
        bb.accepted.connect(self._on_ok)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)
    def _on_ok(self):
        paths = [i.data(Qt.UserRole) for i in self.listw.selectedItems()]
        self.selected_paths = [p for p in paths if p]
        self.accept()
__all__ = [name for name in globals() if not name.startswith("__")]
_BK_FIX41_ORIG_PROGRESS_INIT = ProgressStatusDialog.__init__
def _bk_fix41_progress_status_init(self, title: str, tr, parent=None):
    tr, parent = _resolve_tr_and_parent(tr, parent)
    QDialog.__init__(self, parent)
    self._tr = tr
    self.setWindowTitle(title)
    self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
    self.setWindowFlag(Qt.Dialog, True)
    self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
    if parent is not None:
        self.setWindowModality(Qt.WindowModal)
    else:
        self.setWindowModality(Qt.ApplicationModal)
    lay = QVBoxLayout(self)
    lay.setContentsMargins(18, 18, 18, 18)
    lay.setSpacing(12)
    row = QHBoxLayout()
    row.setSpacing(14)
    self.spinner = BusySpinnerWidget(self, diameter=44)
    row.addWidget(self.spinner, 0, Qt.AlignTop)
    self.lbl_status = QLabel(self._tr('lm_busy_default_message'))
    self.lbl_status.setWordWrap(True)
    self.lbl_status.setMinimumWidth(380)
    self.lbl_status.setMaximumWidth(620)
    row.addWidget(self.lbl_status, 1)
    lay.addLayout(row)
    self.progress = QProgressBar(self)
    self.progress.hide()
    self.btn_cancel = QPushButton(self._tr('btn_cancel'))
    self.btn_cancel.clicked.connect(self.cancel_requested.emit)
    lay.addWidget(self.btn_cancel, 0, Qt.AlignRight)
    self.adjustSize()
def _bk_fix41_progress_status_set_status(self, text: str):
    txt = str(text or '').strip()
    if not txt:
        txt = self._tr('lm_busy_default_message')
    self.lbl_status.setText(txt)
    self.adjustSize()
def _bk_fix41_progress_status_set_progress(self, value: int):
    return
ProgressStatusDialog.__init__ = _bk_fix41_progress_status_init
ProgressStatusDialog.set_status = _bk_fix41_progress_status_set_status
ProgressStatusDialog.set_progress = _bk_fix41_progress_status_set_progress
def _bk_fix42_dialog_text_width(label: QLabel, text: str, minimum: int = 220, maximum: int = 500) -> int:
    try:
        metrics = label.fontMetrics()
        plain = re.sub(r"<[^>]+>", " ", str(text or ""))
        longest = max([line.strip() for line in plain.splitlines()] or [plain], key=len)
        width = metrics.horizontalAdvance(longest) + 28
        return max(minimum, min(maximum, int(width)))
    except Exception:
        return maximum
def _bk_fix42_apply_dynamic_label_width(dlg, text: str):
    try:
        width = _bk_fix42_dialog_text_width(dlg.lbl_status, text, 220, 500)
        dlg.lbl_status.setMinimumWidth(width)
        dlg.lbl_status.setMaximumWidth(500)
        dlg.lbl_status.setWordWrap(True)
        dlg.setMaximumWidth(560)
        dlg.adjustSize()
    except Exception:
        pass
def _bk_fix42_progress_status_set_status(self, text: str):
    txt = str(text or '').strip() or self._tr('lm_busy_default_message')
    self.lbl_status.setText(txt)
    _bk_fix42_apply_dynamic_label_width(self, txt)
def _bk_fix42_busy_status_set_status(self, text: str):
    txt = str(text or '').strip() or str(getattr(self, '_base_message', '') or self._tr('lm_busy_default_message'))
    self._base_message = txt
    self.lbl_status.setText(txt)
    _bk_fix42_apply_dynamic_label_width(self, txt)
ProgressStatusDialog.set_status = _bk_fix42_progress_status_set_status
try:
    BusyStatusDialog.set_status = _bk_fix42_busy_status_set_status
except Exception:
    pass
def _bk_fix43_screen_max_dialog_width(dlg=None) -> int:
    try:
        try:
            _QApplication = QApplication
        except Exception:
            from PySide6.QtWidgets import QApplication as _QApplication
        app = _QApplication.instance()
        screen = None
        if dlg is not None and getattr(dlg, "windowHandle", None) is not None and dlg.windowHandle():
            screen = dlg.windowHandle().screen()
        if screen is None and app is not None:
            screen = app.primaryScreen()
        if screen is not None:
            return max(360, int(screen.availableGeometry().width()) - 96)
    except Exception:
        pass
    return 1200
def _bk_fix43_dialog_text_width(label: QLabel, text: str, minimum: int = 260) -> int:
    try:
        max_width = _bk_fix43_screen_max_dialog_width(label.window() if label is not None else None)
        metrics = label.fontMetrics()
        plain = re.sub(r"<[^>]+>", " ", str(text or ""))
        longest = max([line.strip() for line in plain.splitlines()] or [plain], key=len)
        width = metrics.horizontalAdvance(longest) + 36
        return max(minimum, min(max_width, int(width)))
    except Exception:
        return 900
def _bk_fix43_apply_dynamic_label_width(dlg, text: str):
    try:
        max_width = _bk_fix43_screen_max_dialog_width(dlg)
        width = _bk_fix43_dialog_text_width(dlg.lbl_status, text, 260)
        dlg.lbl_status.setMinimumWidth(width)
        dlg.lbl_status.setMaximumWidth(max_width)
        dlg.lbl_status.setWordWrap(True)
        dlg.setMaximumWidth(max_width + 80)
        dlg.adjustSize()
    except Exception:
        pass
def _bk_fix43_progress_status_set_status(self, text: str):
    txt = str(text or '').strip() or self._tr('lm_busy_default_message')
    self.lbl_status.setText(txt)
    _bk_fix43_apply_dynamic_label_width(self, txt)
def _bk_fix43_busy_status_set_status(self, text: str):
    txt = str(text or '').strip() or str(getattr(self, '_base_message', '') or self._tr('lm_busy_default_message'))
    self._base_message = txt
    self.lbl_status.setText(txt)
    _bk_fix43_apply_dynamic_label_width(self, txt)
ProgressStatusDialog.set_status = _bk_fix43_progress_status_set_status
try:
    BusyStatusDialog.set_status = _bk_fix43_busy_status_set_status
except Exception:
    pass
