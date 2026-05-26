"""Konservativer Runtime-Patch für stabilere Abbruchlogik.

Version 2: Der erste Patch war zu breit und hat einige vorhandene
Abbrechen-Buttons übersteuert. Diese Variante lässt die bestehenden Worker-
Abläufe weitgehend unverändert und ergänzt nur die gefährlichen/fehlenden
Abbruch-Einstiegspunkte.

Ziele:
- keine harten QThread.terminate()-Abbrüche bei lokaler JSON-/KI-Erzeugung
- bestehende Abbrechen-Buttons bleiben anklickbar und lösen wieder die
  ursprünglichen Abbruchmethoden aus
- PDF-/Export-/LM-Dialoge geben sichtbares Feedback nach dem Klick auf
  Abbrechen
- abgebrochene PDF-Teilrender werden nicht versehentlich importiert
"""

from .shared import *
from .workers import *
from .dialogs import *
from .main_window import MainWindow

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
    # QThread-Objekte nie rekursiv über worker.thread() abbrechen: die Affinity
    # eines QThread-Objekts ist meist der GUI/Main-Thread.
    try:
        if isinstance(worker, QThread):
            if not _bk_fix54_is_main_qthread(worker):
                try:
                    worker.requestInterruption()
                    did = True
                except Exception:
                    pass
            return did
    except Exception:
        pass
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
        ("device_resolved", "on_device_resolved"),
        ("gpu_info", "on_gpu_info"),
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
    worker = getattr(window, "worker", None)
    running = _bk_fix54_is_running_qthread(worker)
    if running:
        try:
            window._ocr_cancel_requested = True
            window._ocr_stop_requested = True
        except Exception:
            pass
        _bk_fix54_request_worker_cancel(worker)
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
        # Wichtig: GUI sofort wieder freigeben. Der Worker darf im Hintergrund
        # seinen aktuellen nativen Kraken-Schritt sicher beenden; seine Signale
        # sind getrennt und ändern die UI nicht mehr.
        try:
            window.worker = None
        except Exception:
            pass
        try:
            window._log(window._tr_log("log_stop_requested"))
        except Exception:
            pass
        _bk_fix54_reset_ocr_ui(window, _bk_cancel_done_text(window, "ocr") if callable(globals().get("_bk_cancel_done_text")) else translation.translate(translation.DEFAULT_LANGUAGE, "cancel_done_ocr"))
        return None
    _bk_fix54_reset_ocr_ui(window, _bk_cancel_done_text(window, "ocr") if callable(globals().get("_bk_cancel_done_text")) else translation.translate(translation.DEFAULT_LANGUAGE, "cancel_done_ocr"))
    return None

def _bk_fix54_stop_everything_now(window):
    return _bk_fix54_stop_ocr_safe(window)

globals()["_bk_fix43_stop_everything_now"] = _bk_fix54_stop_everything_now

globals()["_bk_request_worker_cancel"] = _bk_fix54_request_worker_cancel

MainWindow.stop_ocr = _bk_fix54_stop_ocr_safe
