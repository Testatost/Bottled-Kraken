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

def _bk_cancel_lang_text(window, key_or_de: str, en: str | None = None, fr: str | None = None) -> str:
    try:
        lang = getattr(window, "current_lang", translation.DEFAULT_LANGUAGE)
        if en is None and fr is None:
            return translation.translate(lang, key_or_de)
        lang = translation.normalize_language_code(lang)
        if lang == "en" and en is not None:
            return en
        if lang == "fr" and fr is not None:
            return fr
    except Exception:
        pass
    return key_or_de

def _bk_cancel_pending_text(window) -> str:
    return _bk_cancel_lang_text(window, "cancel_pending_text")

def _bk_cancel_done_text(window, subject: str = "action") -> str:
    key_by_subject = {
        "pdf": "cancel_done_pdf",
        "export": "cancel_done_export",
        "ocr": "cancel_done_ocr",
        "lm": "cancel_done_lm",
    }
    return _bk_cancel_lang_text(window, key_by_subject.get(subject, "cancel_done_action"))

def _bk_is_cancel_message(msg) -> bool:
    txt = str(msg or "").lower()
    return any(token in txt for token in (
        "abgebrochen", "abbruch", "cancelled", "canceled", "cancel",
        "annulé", "annule", "annulée", "annulee",
    ))

def _bk_mark_worker_cancelled(worker):
    if worker is None:
        return
    try:
        worker._bk_cancelled_by_user = True
    except Exception:
        pass

def _bk_request_worker_cancel(worker):
    if worker is None:
        return False
    _bk_mark_worker_cancelled(worker)
    try:
        if hasattr(worker, "cancel"):
            worker.cancel()
        else:
            worker.requestInterruption()
        return True
    except Exception:
        try:
            worker.requestInterruption()
            return True
        except Exception:
            return False

def _bk_dialog_cancel_feedback(window, dialog=None, text: str = None):
    """Nur Status/Button-Text ändern, aber keine Signalverbindungen entfernen.

    Wichtig: Der alte Patch hat teilweise Cancel-Buttons entfernt/deaktiviert.
    Das wirkte so, als seien sie kaputt. Hier bleibt der Button vorhanden; er
    wird nur kurz deaktiviert, damit kein Doppelklick zwei Abbrüche auslöst.
    """
    text = text or _bk_cancel_pending_text(window)
    try:
        if dialog is not None and hasattr(dialog, "set_status"):
            dialog.set_status(text)
        elif dialog is not None and hasattr(dialog, "setLabelText"):
            dialog.setLabelText(text)
    except Exception:
        pass
    try:
        btn = getattr(dialog, "btn_cancel", None)
        if btn is not None:
            btn.setText(_bk_cancel_lang_text(window, "cancel_button_running_text"))
            btn.setEnabled(False)
    except Exception:
        pass
    try:
        window.status_bar.showMessage(text)
    except Exception:
        pass

def _bk_lm_cancel_local_json(self):
    worker = getattr(self, "_bk_local_json_worker", None)
    dialog = getattr(self, "_bk_local_json_dialog", None)

    if worker is None:
        if dialog is not None:
            try:
                dialog.close()
            except Exception:
                pass
            self._bk_local_json_dialog = None
        return

    _bk_request_worker_cancel(worker)
    _bk_dialog_cancel_feedback(
        self,
        dialog,
        translation.translate(getattr(self, "current_lang", translation.DEFAULT_LANGUAGE), "cancel_local_ai_in_progress_text"),
    )

try:
    MainWindow._bk_lm_cancel_local_json = _bk_lm_cancel_local_json
except Exception:
    pass

_BK_PREV_CANCEL_AI_REVISION = getattr(MainWindow, "_cancel_ai_revision", None)

def _bk_cancel_ai_revision_safe(self):
    worker = getattr(self, "ai_worker", None)
    if worker is not None and worker.isRunning():
        _bk_request_worker_cancel(worker)
        _bk_dialog_cancel_feedback(self, getattr(self, "ai_progress_dialog", None))
        return
    if callable(_BK_PREV_CANCEL_AI_REVISION):
        return _BK_PREV_CANCEL_AI_REVISION(self)

MainWindow._cancel_ai_revision = _bk_cancel_ai_revision_safe

_BK_PREV_CANCEL_AI_BATCH = getattr(MainWindow, "_cancel_ai_batch_revision", None)

def _bk_cancel_ai_batch_revision_safe(self):
    cancelled = False

    worker = getattr(self, "ai_batch_worker", None)
    if worker is not None and worker.isRunning():
        cancelled = _bk_request_worker_cancel(worker) or cancelled
        _bk_dialog_cancel_feedback(self, getattr(self, "ai_batch_dialog", None))

    worker = getattr(self, "_bk_lm_queue_batch_worker", None)
    if worker is not None and worker.isRunning():
        cancelled = _bk_request_worker_cancel(worker) or cancelled
        _bk_dialog_cancel_feedback(self, getattr(self, "_bk_lm_queue_batch_dialog", None))

    if cancelled:
        return

    if callable(_BK_PREV_CANCEL_AI_BATCH):
        return _BK_PREV_CANCEL_AI_BATCH(self)

MainWindow._cancel_ai_batch_revision = _bk_cancel_ai_batch_revision_safe

try:
    _BK_PREV_LM_CANCEL_QUEUE_BATCH = _bk_lm_cancel_queue_batch
except Exception:
    _BK_PREV_LM_CANCEL_QUEUE_BATCH = None

def _bk_lm_cancel_queue_batch(self):
    worker = getattr(self, "_bk_lm_queue_batch_worker", None)
    if worker is not None and worker.isRunning():
        _bk_request_worker_cancel(worker)
        _bk_dialog_cancel_feedback(self, getattr(self, "_bk_lm_queue_batch_dialog", None))
        return
    if callable(_BK_PREV_LM_CANCEL_QUEUE_BATCH):
        return _BK_PREV_LM_CANCEL_QUEUE_BATCH(self)

try:
    MainWindow._bk_lm_cancel_queue_batch = _bk_lm_cancel_queue_batch
except Exception:
    pass

try:
    _BK_PREV_LM_ON_QUEUE_BATCH_FINISHED = _bk_lm_on_queue_batch_finished
except Exception:
    _BK_PREV_LM_ON_QUEUE_BATCH_FINISHED = None

def _bk_lm_on_queue_batch_finished(self):
    worker = getattr(self, "_bk_lm_queue_batch_worker", None)
    cancelled = bool(getattr(worker, "_bk_cancelled_by_user", False)) or bool(
        worker is not None and worker.isInterruptionRequested()
    ) or bool(getattr(worker, "_cancel_requested", False))

    if cancelled:
        try:
            self.act_ai_revise.setEnabled(True)
            if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
                self.btn_ai_revise_bottom.setEnabled(True)
        except Exception:
            pass
        dlg = getattr(self, "_bk_lm_queue_batch_dialog", None)
        if dlg:
            try:
                dlg.close()
            except Exception:
                pass
        self._bk_lm_queue_batch_dialog = None
        if worker is not None:
            try:
                worker.deleteLater()
            except Exception:
                pass
        self._bk_lm_queue_batch_worker = None
        try:
            self.status_bar.showMessage(_bk_cancel_done_text(self, "lm"))
            self._log(_bk_cancel_done_text(self, "lm"))
        except Exception:
            pass
        return

    if callable(_BK_PREV_LM_ON_QUEUE_BATCH_FINISHED):
        return _BK_PREV_LM_ON_QUEUE_BATCH_FINISHED(self)

_BK_PREV_CANCEL_PDF_RENDER = getattr(MainWindow, "_cancel_pdf_render", None)

_BK_PREV_ON_PDF_RENDER_FINISHED = getattr(MainWindow, "_on_pdf_render_finished", None)

_BK_PREV_ON_PDF_RENDER_FAILED = getattr(MainWindow, "_on_pdf_render_failed", None)

_BK_PREV_PDF_RENDER_RUN = getattr(PDFRenderWorker, "run", None)
