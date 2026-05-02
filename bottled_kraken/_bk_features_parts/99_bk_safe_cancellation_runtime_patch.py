"""Konservativer Runtime-Patch für stabilere Abbruchlogik.

Version 2: Der erste Patch war zu breit und hat einige vorhandene
Abbrechen-Buttons übersteuert. Diese Variante lässt die bestehenden Worker-
Abläufe weitgehend unverändert und patcht nur die gefährlichen/fehlenden
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


def _bk_cancel_lang_text(window, de: str, en: str, fr: str) -> str:
    try:
        lang = str(getattr(window, "current_lang", "de") or "de").lower()
        if lang == "en":
            return en
        if lang == "fr":
            return fr
    except Exception:
        pass
    return de


def _bk_cancel_pending_text(window) -> str:
    return _bk_cancel_lang_text(
        window,
        "Abbruch wird angefordert … Der aktuelle Schritt wird noch sicher beendet.",
        "Cancellation requested … The current step will finish safely first.",
        "Annulation demandée … L’étape en cours va d’abord se terminer en toute sécurité.",
    )


def _bk_cancel_done_text(window, subject: str = "Aktion") -> str:
    if subject == "pdf":
        return _bk_cancel_lang_text(window, "PDF-Verarbeitung abgebrochen.", "PDF processing cancelled.", "Traitement du PDF annulé.")
    if subject == "export":
        return _bk_cancel_lang_text(window, "Export abgebrochen.", "Export cancelled.", "Export annulé.")
    if subject == "ocr":
        return _bk_cancel_lang_text(window, "OCR abgebrochen.", "OCR cancelled.", "OCR annulée.")
    if subject == "lm":
        return _bk_cancel_lang_text(window, "LM-Batch abgebrochen.", "LM batch cancelled.", "Lot LM annulé.")
    return _bk_cancel_lang_text(window, "Aktion abgebrochen.", "Action cancelled.", "Action annulée.")


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
            btn.setText(_bk_cancel_lang_text(window, "Abbruch läuft …", "Cancelling …", "Annulation …"))
            btn.setEnabled(False)
    except Exception:
        pass
    try:
        window.status_bar.showMessage(text)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Lokale JSON-/KI-Erzeugung: gefährliches terminate() ersetzen.
# ---------------------------------------------------------------------------

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
        _bk_cancel_lang_text(
            self,
            "Lokale KI-Erzeugung wird abgebrochen …",
            "Cancelling local AI generation …",
            "Annulation de la génération IA locale …",
        ),
    )

    # Nicht terminate() verwenden. Der Worker schließt seine HTTP-Verbindung in
    # cancel() selbst und meldet danach failed_json mit Abbruchtext.


try:
    MainWindow._bk_lm_cancel_local_json = _bk_lm_cancel_local_json
except Exception:
    pass


# ---------------------------------------------------------------------------
# Einzelne LM-Überarbeitung / KI-Fortschrittsdialog.
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Batch-LM / AI-Batch: nur Cancel-Einstieg reparieren, Worker-Run nicht ersetzen.
# ---------------------------------------------------------------------------
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


# Wenn der Queue-LM-Batch abgebrochen wurde, nicht als normal abgeschlossen melden.
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


# ---------------------------------------------------------------------------
# PDF-Rendering: echter Abbruch zwischen den Seiten, kein Teilimport.
# ---------------------------------------------------------------------------
_BK_PREV_CANCEL_PDF_RENDER = getattr(MainWindow, "_cancel_pdf_render", None)
_BK_PREV_ON_PDF_RENDER_FINISHED = getattr(MainWindow, "_on_pdf_render_finished", None)
_BK_PREV_ON_PDF_RENDER_FAILED = getattr(MainWindow, "_on_pdf_render_failed", None)
_BK_PREV_PDF_RENDER_RUN = getattr(PDFRenderWorker, "run", None)


class _BKPdfRenderCancelled(Exception):
    pass


def _bk_pdf_render_cancel_text() -> str:
    # Worker hat keine sichere Referenz auf MainWindow/current_lang.
    return "PDF-Verarbeitung abgebrochen."


def _bk_pdf_remove_partial_outputs(out_paths):
    for p in list(out_paths or []):
        try:
            if p and os.path.exists(p):
                os.remove(p)
        except Exception:
            pass
    try:
        if out_paths:
            tmp_dir = os.path.dirname(out_paths[0])
            if tmp_dir and os.path.isdir(tmp_dir) and not os.listdir(tmp_dir):
                os.rmdir(tmp_dir)
    except Exception:
        pass


def _bk_pdf_worker_cancel(self):
    _bk_mark_worker_cancelled(self)
    try:
        self.requestInterruption()
    except Exception:
        pass


def _bk_pdf_worker_cancel_requested(self) -> bool:
    try:
        if bool(getattr(self, "_bk_cancelled_by_user", False)):
            return True
    except Exception:
        pass
    try:
        if self.isInterruptionRequested():
            return True
    except Exception:
        pass
    return False


def _bk_pdf_render_worker_run_cancellable(self):
    """Cancellable PDF renderer.

    Der alte Worker prüfte den Abbruch nur am Schleifenanfang und emittierte
    danach trotzdem finished_pdf(...). Dadurch wurden halb gerenderte PDFs in
    den Wartebereich übernommen. Diese Variante meldet Abbruch über failed_pdf
    und löscht Teilbilder. Ein gerade laufender MuPDF-get_pixmap()-Aufruf kann
    technisch nicht mitten im nativen Aufruf beendet werden, aber direkt danach
    wird abgebrochen, bevor die nächste Seite startet.
    """
    out_paths = []
    doc = None
    try:
        pdf_path = self.pdf_path
        dpi = int(getattr(self, "dpi", 300) or 300)
        base = os.path.splitext(os.path.basename(pdf_path))[0]
        tmp_dir = os.path.join(os.path.dirname(pdf_path), f".kraken_tmp_{base}")
        os.makedirs(tmp_dir, exist_ok=True)

        doc = fitz.open(pdf_path)
        total = int(doc.page_count)
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)

        for i in range(total):
            if _bk_pdf_worker_cancel_requested(self):
                raise _BKPdfRenderCancelled()

            page = None
            pix = None
            out = os.path.join(tmp_dir, f"{base}_p{i + 1:04d}.png")
            try:
                page = doc.load_page(i)
                if _bk_pdf_worker_cancel_requested(self):
                    raise _BKPdfRenderCancelled()

                pix = page.get_pixmap(matrix=mat, alpha=False)
                if _bk_pdf_worker_cancel_requested(self):
                    raise _BKPdfRenderCancelled()

                pix.save(out)
                if _bk_pdf_worker_cancel_requested(self):
                    try:
                        if os.path.exists(out):
                            os.remove(out)
                    except Exception:
                        pass
                    raise _BKPdfRenderCancelled()

                out_paths.append(out)
                self.progress.emit(i + 1, total, pdf_path)
            finally:
                pix = None
                page = None
                if (i + 1) % 5 == 0:
                    try:
                        gc.collect()
                    except Exception:
                        pass

        self.finished_pdf.emit(pdf_path, out_paths)

    except _BKPdfRenderCancelled:
        _bk_mark_worker_cancelled(self)
        _bk_pdf_remove_partial_outputs(out_paths)
        self.failed_pdf.emit(getattr(self, "pdf_path", ""), _bk_pdf_render_cancel_text())
    except Exception:
        _bk_pdf_remove_partial_outputs(out_paths)
        self.failed_pdf.emit(getattr(self, "pdf_path", ""), traceback.format_exc())
    finally:
        try:
            if doc is not None:
                doc.close()
        except Exception:
            pass
        try:
            gc.collect()
        except Exception:
            pass


try:
    PDFRenderWorker.cancel = _bk_pdf_worker_cancel
    PDFRenderWorker.run = _bk_pdf_render_worker_run_cancellable
except Exception:
    pass


def _bk_cancel_pdf_render_safe(self):
    worker = getattr(self, "pdf_worker", None)
    if worker is not None and worker.isRunning():
        _bk_mark_worker_cancelled(worker)
        try:
            if hasattr(worker, "cancel"):
                worker.cancel()
            else:
                worker.requestInterruption()
        except Exception:
            try:
                worker.requestInterruption()
            except Exception:
                pass
        _bk_dialog_cancel_feedback(
            self,
            getattr(self, "pdf_progress_dlg", None),
            _bk_cancel_lang_text(
                self,
                "PDF-Verarbeitung wird abgebrochen … Die aktuelle Seite wird noch sicher beendet.",
                "Cancelling PDF processing … The current page will finish safely first.",
                "Annulation du traitement du PDF … La page en cours va d’abord se terminer en toute sécurité.",
            ),
        )
        return
    if callable(_BK_PREV_CANCEL_PDF_RENDER):
        return _BK_PREV_CANCEL_PDF_RENDER(self)


def _bk_pdf_cleanup_dialog_and_worker(self):
    if getattr(self, "pdf_progress_dlg", None):
        try:
            self.pdf_progress_dlg.close()
        except Exception:
            pass
        self.pdf_progress_dlg = None
    self.pdf_worker = None
    try:
        self._set_progress_idle(0)
    except Exception:
        pass


def _bk_on_pdf_render_finished_safe(self, pdf_path: str, out_paths: list):
    worker = getattr(self, "pdf_worker", None)
    cancelled = bool(getattr(worker, "_bk_cancelled_by_user", False)) or bool(
        worker is not None and worker.isInterruptionRequested()
    )
    if cancelled:
        _bk_pdf_cleanup_dialog_and_worker(self)
        _bk_pdf_remove_partial_outputs(out_paths)
        try:
            self.status_bar.showMessage(_bk_cancel_done_text(self, "pdf"))
            self._log(_bk_cancel_done_text(self, "pdf") + " " + os.path.basename(str(pdf_path)))
        except Exception:
            pass
        return
    if callable(_BK_PREV_ON_PDF_RENDER_FINISHED):
        return _BK_PREV_ON_PDF_RENDER_FINISHED(self, pdf_path, out_paths)


def _bk_on_pdf_render_failed_safe(self, pdf_path: str, msg: str):
    worker = getattr(self, "pdf_worker", None)
    cancelled = bool(getattr(worker, "_bk_cancelled_by_user", False)) or _bk_is_cancel_message(msg)
    if cancelled:
        _bk_pdf_cleanup_dialog_and_worker(self)
        try:
            self.status_bar.showMessage(_bk_cancel_done_text(self, "pdf"))
            self._log(_bk_cancel_done_text(self, "pdf") + " " + os.path.basename(str(pdf_path)))
        except Exception:
            pass
        return
    if callable(_BK_PREV_ON_PDF_RENDER_FAILED):
        return _BK_PREV_ON_PDF_RENDER_FAILED(self, pdf_path, msg)


MainWindow._cancel_pdf_render = _bk_cancel_pdf_render_safe
MainWindow._on_pdf_render_finished = _bk_on_pdf_render_finished_safe
MainWindow._on_pdf_render_failed = _bk_on_pdf_render_failed_safe


# ---------------------------------------------------------------------------
# Export-Batch: Cancel-Button bleibt funktionsfähig, Status korrekt setzen.
# ---------------------------------------------------------------------------
_BK_PREV_CANCEL_EXPORT_BATCH = getattr(MainWindow, "_cancel_export_batch", None)
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
            _bk_cancel_lang_text(self, "Export wird abgebrochen …", "Cancelling export …", "Annulation de l’export …"),
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


# ---------------------------------------------------------------------------
# OCR-Stop: ursprünglichen Stop nicht ersetzen, nur sicherer erweitern.
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Sicheres Schließen: nur anfragen, nicht hart terminieren.
# ---------------------------------------------------------------------------
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
        if not getattr(self, "_is_closing", False):
            self._is_closing = True
            try:
                self.status_bar.showMessage(
                    _bk_cancel_lang_text(
                        self,
                        "Laufende Aktionen werden beendet …",
                        "Stopping running actions …",
                        "Arrêt des actions en cours …",
                    )
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
        event.ignore()
        return

    if callable(_BK_PREV_CLOSE_EVENT):
        return _BK_PREV_CLOSE_EVENT(self, event)
    event.accept()


MainWindow._all_running_workers = _bk_all_running_workers
MainWindow._request_all_running_workers_cancel = _bk_request_all_running_workers_cancel
MainWindow.closeEvent = _bk_close_event_safe
