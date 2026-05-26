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

class _BKPdfRenderCancelled(Exception):
    pass

def _bk_pdf_render_cancel_text() -> str:
    # Worker hat keine sichere Referenz auf MainWindow/current_lang.
    return translation.translate(translation.DEFAULT_LANGUAGE, "cancel_pdf_processing_text")

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
            translation.translate(getattr(self, "current_lang", translation.DEFAULT_LANGUAGE), "cancel_pdf_in_progress_text"),
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

_BK_PREV_CANCEL_EXPORT_BATCH = getattr(MainWindow, "_cancel_export_batch", None)
