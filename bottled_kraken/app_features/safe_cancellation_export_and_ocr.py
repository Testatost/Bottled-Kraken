from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
from bottled_kraken.common import (
    STATUS_DONE,
    STATUS_PROCESSING,
    STATUS_WAITING,
    translation,
)
from bottled_kraken.main_window import MainWindow
_BK_PREV_ON_EXPORT_BATCH_FINISHED = getattr(MainWindow, "on_export_batch_finished", None)
def _bk_cancel_export_batch_safe(self):
    worker = getattr(self, "export_worker", None)
    if worker is not None and worker.isRunning():
        _bk_mark_worker_cancelled(worker)
        try:
            worker.requestInterruption()
        except Exception:
            pass
        _bk_dialog_cancel_feedback(
            self,
            getattr(self, "export_dialog", None),
            translation.translate(getattr(self, "current_lang", translation.DEFAULT_LANGUAGE), "cancel_export_in_progress_text"),
        )
        return
    if callable(_BK_PREV_CANCEL_EXPORT_BATCH):
        return _BK_PREV_CANCEL_EXPORT_BATCH(self)
def _bk_on_export_batch_finished_safe(self):
    worker = getattr(self, "export_worker", None)
    cancelled = bool(getattr(worker, "_bk_cancelled_by_user", False)) or bool(
        worker is not None and worker.isInterruptionRequested()
    )
    if cancelled:
        if getattr(self, "export_dialog", None):
            try:
                self.export_dialog.close()
            except Exception:
                pass
            self.export_dialog = None
        self.export_worker = None
        try:
            self._set_progress_idle(0)
            self.status_bar.showMessage(_bk_cancel_done_text(self, "export"))
            self._log(_bk_cancel_done_text(self, "export"))
        except Exception:
            pass
        return
    if callable(_BK_PREV_ON_EXPORT_BATCH_FINISHED):
        return _BK_PREV_ON_EXPORT_BATCH_FINISHED(self)
MainWindow._cancel_export_batch = _bk_cancel_export_batch_safe
MainWindow.on_export_batch_finished = _bk_on_export_batch_finished_safe
_BK_PREV_ON_BATCH_FINISHED = getattr(MainWindow, "on_batch_finished", None)
def _bk_on_batch_finished_safe(self):
    worker = getattr(self, "worker", None)
    cancelled = bool(getattr(worker, "_bk_cancelled_by_user", False)) or bool(
        worker is not None and worker.isInterruptionRequested()
    )
    if cancelled:
        try:
            self.act_play.setEnabled(True)
            self.act_stop.setEnabled(False)
            self._set_progress_idle(0)
            self.status_bar.showMessage(_bk_cancel_done_text(self, "ocr"))
            self._log(_bk_cancel_done_text(self, "ocr"))
        except Exception:
            pass
        try:
            for task in getattr(self, "queue_items", []):
                if getattr(task, "status", None) == STATUS_PROCESSING:
                    task.status = STATUS_WAITING if not getattr(task, "results", None) else STATUS_DONE
                    self._update_queue_row(task.path)
        except Exception:
            pass
        try:
            if worker is not None:
                worker.deleteLater()
        except Exception:
            pass
        self.worker = None
        return
    if callable(_BK_PREV_ON_BATCH_FINISHED):
        return _BK_PREV_ON_BATCH_FINISHED(self)
MainWindow.on_batch_finished = _bk_on_batch_finished_safe
_BK_PREV_CLOSE_EVENT = getattr(MainWindow, "closeEvent", None)
def _bk_all_running_workers(self):
    workers = []
    for attr in (
        "worker", "ai_worker", "ai_batch_worker", "export_worker", "pdf_worker",
        "hf_download_worker", "voice_worker", "_bk_lm_queue_batch_worker",
        "_bk_local_json_worker", "_ptr_multi_ocr_worker",
    ):
        try:
            worker = getattr(self, attr, None)
            if worker is not None and worker.isRunning() and worker not in workers:
                workers.append(worker)
        except Exception:
            pass
    return workers
def _bk_request_all_running_workers_cancel(self):
    for worker in _bk_all_running_workers(self):
        _bk_request_worker_cancel(worker)
def _bk_close_event_safe(self, event):
    running = _bk_all_running_workers(self)
    if running:
        if not getattr(self, "_bk_shutdown_requested", False):
            self._bk_shutdown_requested = True
            try:
                self.setEnabled(False)
            except Exception:
                pass
            try:
                self.status_bar.showMessage(
                    _bk_cancel_lang_text(self, "cancel_running_actions_text")
                )
            except Exception:
                pass
            _bk_request_all_running_workers_cancel(self)
            try:
                if hasattr(self, "_shutdown_poll_timer"):
                    self._shutdown_poll_timer.start()
                if hasattr(self, "_shutdown_force_timer"):
                    self._shutdown_force_timer.start(12000)
            except Exception:
                pass
        else:
            _bk_request_all_running_workers_cancel(self)
        event.ignore()
        return
    try:
        self._bk_shutdown_requested = False
    except Exception:
        pass
    try:
        if hasattr(self, "_shutdown_poll_timer"):
            self._shutdown_poll_timer.stop()
        if hasattr(self, "_shutdown_force_timer"):
            self._shutdown_force_timer.stop()
    except Exception:
        pass
    try:
        self.setEnabled(True)
    except Exception:
        pass
    if callable(_BK_PREV_CLOSE_EVENT):
        return _BK_PREV_CLOSE_EVENT(self, event)
    event.accept()
MainWindow._all_running_workers = _bk_all_running_workers
MainWindow._request_all_running_workers_cancel = _bk_request_all_running_workers_cancel
MainWindow.closeEvent = _bk_close_event_safe
__all__ = [
    '_BK_PREV_CLOSE_EVENT',
    '_BK_PREV_ON_BATCH_FINISHED',
    '_BK_PREV_ON_EXPORT_BATCH_FINISHED',
    '_bk_all_running_workers',
    '_bk_cancel_export_batch_safe',
    '_bk_close_event_safe',
    '_bk_on_batch_finished_safe',
    '_bk_on_export_batch_finished_safe',
    '_bk_request_all_running_workers_cancel',
]
register_globals('bk', globals(), __all__)
