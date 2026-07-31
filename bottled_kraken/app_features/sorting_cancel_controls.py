from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
def _bk_local_json_worker_cancel_v20(self):
    self._cancelled = True
    self.requestInterruption()
    conn = getattr(self, '_active_conn', None)
    self._active_conn = None
    try:
        sock = getattr(conn, 'sock', None)
    except Exception:
        sock = None
    if sock is not None:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            sock.close()
        except Exception:
            pass
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass
BKLocalStructuredJsonWorker.cancel = _bk_local_json_worker_cancel_v20
def _bk_lm_cancel_local_json_v20(self):
    worker = getattr(self, '_bk_local_json_worker', None)
    context = getattr(self, '_bk_local_json_context', None) or {}
    dialog = getattr(self, '_bk_local_json_dialog', None)
    if worker is None:
        if dialog is not None:
            try:
                dialog.close()
            except Exception:
                pass
            self._bk_local_json_dialog = None
        return
    for signal_name in ('finished_json', 'failed_json', 'status_changed', 'progress_changed'):
        try:
            getattr(worker, signal_name).disconnect()
        except Exception:
            pass
    try:
        worker.cancel()
    except Exception:
        pass
    try:
        # 2 Sekunden kooperativ warten statt 150 ms: terminate() beendet den
        # Thread hart an unkontrollierter Stelle und bleibt nur letzter Ausweg.
        worker.wait(2000)
    except Exception:
        pass
    if worker.isRunning():
        try:
            import sys as _sys
            print("[bottled_kraken] WARNUNG: Worker reagiert nicht auf Abbruch - "
                  "harter terminate() als letzter Ausweg.", file=_sys.stderr)
        except Exception:
            pass
        try:
            worker.terminate()
        except Exception:
            pass
        try:
            worker.wait(300)
        except Exception:
            pass
    try:
        worker.deleteLater()
    except Exception:
        pass
    self._bk_local_json_worker = None
    self._bk_local_json_context = None
    if hasattr(self, 'act_ai_revise') and self.act_ai_revise is not None:
        self.act_ai_revise.setEnabled(True)
    if hasattr(self, 'btn_ai_revise_bottom') and self.btn_ai_revise_bottom is not None:
        self.btn_ai_revise_bottom.setEnabled(True)
    if dialog is not None:
        try:
            dialog.close()
        except Exception:
            pass
    self._bk_local_json_dialog = None
    try:
        self.status_bar.showMessage(self._tr('msg_local_json_cancelled'), 4000)
    except Exception:
        pass
    try:
        if hasattr(self, '_log'):
            path = os.path.basename(str(context.get('path') or ''))
            kind = _bk_json_schema_kind_label(self, str(context.get('schema_kind') or 'postgres'))
            self._log(self._tr_log('log_local_json_failed', path, kind, self._tr('msg_local_json_cancelled')))
    except Exception:
        pass
    try:
        _bk_lm_update_dropdown_state(self)
    except Exception:
        pass
_bk_lm_cancel_local_json = _bk_lm_cancel_local_json_v20
try:
    MainWindow._bk_lm_cancel_local_json = _bk_lm_cancel_local_json_v20
except Exception:
    pass
class BKLocalJsonNoticeDialog(QDialog):
    cancel_requested = Signal()
    def __init__(self, title: str, message: str, tr_func, parent=None):
        super().__init__(parent)
        self._tr = tr_func
        self._base_message = str(message or '')
        self.setWindowTitle(title)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        self.setWindowFlag(Qt.Dialog, True)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        if parent is not None:
            self.setWindowModality(Qt.WindowModal)
        else:
            self.setWindowModality(Qt.ApplicationModal)
        self.setMinimumWidth(420)
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)
        row = QHBoxLayout()
        row.setSpacing(12)
        self.spinner = BusySpinnerWidget(self, diameter=42)
        row.addWidget(self.spinner, 0, Qt.AlignTop)
        self.lbl_status = QLabel(self._base_message)
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setMinimumWidth(320)
        self.lbl_status.setMaximumWidth(520)
        row.addWidget(self.lbl_status, 1)
        root.addLayout(row)
        self.btn_cancel = QPushButton(self._tr('btn_cancel'))
        self.btn_cancel.clicked.connect(self.cancel_requested.emit)
        root.addWidget(self.btn_cancel, 0, Qt.AlignRight)
        self.adjustSize()
    def set_status(self, text: str):
        self.lbl_status.setText(self._base_message)
        self.adjustSize()
    def set_progress(self, value: int):
        return
__all__ = [
    'BKLocalJsonNoticeDialog',
    '_bk_lm_cancel_local_json',
    '_bk_lm_cancel_local_json_v20',
    '_bk_local_json_worker_cancel_v20',
]
register_globals('bk', globals(), __all__)
