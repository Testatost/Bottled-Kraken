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

_BK_PREV_STOP_OCR = getattr(MainWindow, "stop_ocr", None)

_BK_PREV_ON_BATCH_FINISHED = getattr(MainWindow, "on_batch_finished", None)

def _bk_stop_ocr_safe(self):
    did_cancel_extra = False

    # Erst das originale Verhalten ausführen, damit der normale Kraken-OCR-
    # Abbruch exakt so bleibt wie vorher.
    if callable(_BK_PREV_STOP_OCR):
        try:
            result = _BK_PREV_STOP_OCR(self)
        except Exception:
            result = None
    else:
        result = None

    # Zusätzlich neuere Worker berücksichtigen, die der alte Stop-Button nicht
    # kannte. Keine Buttons entfernen, keine Threads hart beenden.
    for attr in ("_ptr_multi_ocr_worker", "_bk_lm_queue_batch_worker"):
        try:
            worker = getattr(self, attr, None)
            if worker is not None and worker.isRunning():
                did_cancel_extra = _bk_request_worker_cancel(worker) or did_cancel_extra
        except Exception:
            pass

    if did_cancel_extra:
        try:
            self.status_bar.showMessage(_bk_cancel_pending_text(self))
        except Exception:
            pass
    return result

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

MainWindow.stop_ocr = _bk_stop_ocr_safe

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
        # Nicht _is_closing setzen, solange Threads noch laufen.
        # Das ursprüngliche closeEvent ignoriert spätere Close-Versuche, wenn
        # _is_closing bereits True ist. Genau dadurch konnte das Fenster nach
        # einem laufenden/gerade beendeten Multi-OCR im Shutdown hängen bleiben.
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
