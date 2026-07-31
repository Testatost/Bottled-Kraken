from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
from bottled_kraken.common import (
    QThread,
    STATUS_DONE,
    STATUS_PROCESSING,
    STATUS_WAITING,
    translation,
)
from bottled_kraken.main_window import MainWindow
def _bk_fix54_is_main_qthread(obj) -> bool:
    try:
        return obj is QThread.currentThread()
    except Exception:
        return False
def _bk_fix54_is_running_qthread(obj) -> bool:
    try:
        return bool(obj is not None and hasattr(obj, "isRunning") and obj.isRunning())
    except Exception:
        return False
def _bk_fix54_request_worker_cancel(worker) -> bool:
    if worker is None:
        return False
    try:
        worker._bk_cancelled_by_user = True
    except Exception:
        pass

    did = False
    # Important for LM workers: their cancel() closes the active HTTP connection.
    # requestInterruption() alone only flips a flag and cannot wake a blocking
    # getresponse()/read() call.
    try:
        cancel = getattr(worker, "cancel", None)
        if callable(cancel):
            cancel()
            did = True
    except Exception:
        pass

    try:
        req = getattr(worker, "requestInterruption", None)
        if callable(req) and not _bk_fix54_is_main_qthread(worker):
            req()
            did = True
    except Exception:
        pass
    return did
def _bk_fix54_disconnect_ocr_worker_signals(window, worker):
    if worker is None:
        return
    pairs = (
        ("file_started", "on_file_started"),
        ("file_done", "on_file_done"),
        ("file_error", "on_file_error"),
        ("progress", "on_progress_update"),
        ("finished_batch", "on_batch_finished"),
        ("failed", "on_failed"),
        ("status_info", "on_ocr_status_info"),
    )
    for sig_name, slot_name in pairs:
        try:
            sig = getattr(worker, sig_name, None)
            slot = getattr(window, slot_name, None)
            if sig is not None and slot is not None:
                try:
                    sig.disconnect(slot)
                except Exception:
                    pass
        except Exception:
            pass
def _bk_fix54_forget_abandoned_worker(window, worker):
    try:
        lst = getattr(window, "_bk_abandoned_ocr_workers", [])
        if worker in lst:
            lst.remove(worker)
        window._bk_abandoned_ocr_workers = lst
    except Exception:
        pass
    try:
        worker.deleteLater()
    except Exception:
        pass
def _bk_fix54_reset_ocr_ui(window, message=None):
    try:
        for flag in ("_ocr_cancel_requested", "_ocr_stop_requested", "_stop_requested", "_cancel_requested"):
            try:
                setattr(window, flag, False)
            except Exception:
                pass
        for task in list(getattr(window, "queue_items", []) or []):
            try:
                if getattr(task, "status", None) == STATUS_PROCESSING:
                    task.status = STATUS_WAITING if not getattr(task, "results", None) else STATUS_DONE
                    window._update_queue_row(task.path)
            except Exception:
                pass
        try:
            window.act_play.setEnabled(True)
        except Exception:
            pass
        try:
            window.act_stop.setEnabled(False)
        except Exception:
            pass
        try:
            window._set_progress_idle(0)
        except Exception:
            try:
                window.progress_bar.setRange(0, 100)
                window.progress_bar.setValue(0)
            except Exception:
                pass
        try:
            if message:
                window.status_bar.showMessage(message, 5000)
        except Exception:
            pass
        try:
            window._update_actions_enabled()
        except Exception:
            pass
    except Exception:
        pass
def _bk_fix54_stop_ocr_safe(window, *args, **kwargs):
    worker_attrs = (
        "worker",
        "ai_worker",
        "ai_batch_worker",
        "_bk_lm_queue_batch_worker",
        "_ptr_multi_ocr_worker",
    )
    running_workers = []
    for attr in worker_attrs:
        worker = getattr(window, attr, None)
        if _bk_fix54_is_running_qthread(worker):
            running_workers.append((attr, worker))

    if running_workers:
        try:
            window._ocr_cancel_requested = True
            window._ocr_stop_requested = True
        except Exception:
            pass

        for attr, worker in running_workers:
            _bk_fix54_request_worker_cancel(worker)

            # The normal OCR worker is managed by the queue/overlay callbacks.
            # Disconnect it exactly as before so late signals cannot mutate UI.
            if attr == "worker":
                _bk_fix54_disconnect_ocr_worker_signals(window, worker)
                try:
                    abandoned = list(getattr(window, "_bk_abandoned_ocr_workers", []) or [])
                    if worker not in abandoned:
                        abandoned.append(worker)
                    window._bk_abandoned_ocr_workers = abandoned
                    try:
                        worker.finished.connect(lambda w=worker, win=window: _bk_fix54_forget_abandoned_worker(win, w))
                    except Exception:
                        pass
                except Exception:
                    pass
                try:
                    window.worker = None
                except Exception:
                    pass

        try:
            window._log(window._tr_log("log_stop_requested"))
        except Exception:
            pass

        # Keep the LM progress dialogs alive until their worker emits finished;
        # their own completion handlers close and clean them up safely.
        has_lm = any(attr in {"ai_worker", "ai_batch_worker", "_bk_lm_queue_batch_worker"} for attr, _ in running_workers)
        try:
            if has_lm:
                msg = _bk_cancel_pending_text(window) if callable(globals().get("_bk_cancel_pending_text")) else translation.translate(translation.DEFAULT_LANGUAGE, "cancel_pending_text")
                window.status_bar.showMessage(msg, 5000)
            else:
                msg = _bk_cancel_done_text(window, "ocr") if callable(globals().get("_bk_cancel_done_text")) else translation.translate(translation.DEFAULT_LANGUAGE, "cancel_done_ocr")
                _bk_fix54_reset_ocr_ui(window, msg)
        except Exception:
            pass
        return None

    _bk_fix54_reset_ocr_ui(
        window,
        _bk_cancel_done_text(window, "ocr") if callable(globals().get("_bk_cancel_done_text")) else translation.translate(translation.DEFAULT_LANGUAGE, "cancel_done_ocr"),
    )
    return None
def _bk_fix54_stop_everything_now(window):
    return _bk_fix54_stop_ocr_safe(window)
globals()["_bk_fix43_stop_everything_now"] = _bk_fix54_stop_everything_now
globals()["_bk_request_worker_cancel"] = _bk_fix54_request_worker_cancel
MainWindow.stop_ocr = _bk_fix54_stop_ocr_safe
__all__ = [
    '_bk_fix54_disconnect_ocr_worker_signals',
    '_bk_fix54_forget_abandoned_worker',
    '_bk_fix54_is_main_qthread',
    '_bk_fix54_is_running_qthread',
    '_bk_fix54_request_worker_cancel',
    '_bk_fix54_reset_ocr_ui',
    '_bk_fix54_stop_everything_now',
    '_bk_fix54_stop_ocr_safe',
]
register_globals('bk', globals(), __all__)
