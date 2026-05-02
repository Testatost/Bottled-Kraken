"""Worker-Klassen für Bottled Kraken."""
from ..shared import *

class ExportWorker(QThread):
    file_started = Signal(str, int, int)  # display_name, current, total
    file_done = Signal(str, str, int, int)  # display_name, dest_path, current, total
    file_error = Signal(str, str, int, int)
    progress_changed = Signal(int)
    status_changed = Signal(str)
    finished_batch = Signal()

    def __init__(self, render_callback, items: List[TaskItem], fmt: str, folder: str, parent=None):
        super().__init__(parent)
        self.render_callback = render_callback
        self.items = items
        self.fmt = fmt
        self.folder = folder

    def _export_ext(self) -> str:
        if self.fmt in ("txt", "txt_boxes"):
            return "txt"
        return self.fmt

    def _export_stem(self, display_name: str) -> str:
        base_name = os.path.splitext(display_name)[0]
        if self.fmt == "txt_boxes":
            return f"{base_name}_mit_overlay_boxen"
        return base_name

    def run(self):
        total = len(self.items)
        if total <= 0:
            self.finished_batch.emit()
            return
        for i, it in enumerate(self.items, start=1):
            if self.isInterruptionRequested():
                break
            dest_path = os.path.join(self.folder, f"{self._export_stem(it.display_name)}.{self._export_ext()}")
            self.file_started.emit(it.display_name, i, total)
            self.status_changed.emit(f"Exportiere {i}/{total}: {it.display_name}")
            try:
                self.render_callback(dest_path, self.fmt, it)
                self.file_done.emit(it.display_name, dest_path, i, total)
            except Exception as e:
                self.file_error.emit(it.display_name, str(e), i, total)
            self.progress_changed.emit(int((i / total) * 100))
        self.status_changed.emit("Export abgeschlossen.")
        self.finished_batch.emit()


class CombinedPDFExportWorker(QThread):
    page_started = Signal(str, int, int)      # display_name, current, total
    pdf_done = Signal(str, int)               # dest_path, total
    export_error = Signal(str)
    cancelled_export = Signal(str)            # dest_path
    progress_changed = Signal(int)
    status_changed = Signal(str)
    finished_batch = Signal()

    def __init__(self, render_page_callback, items: List[TaskItem], dest_path: str, tr_func=None, parent=None):
        super().__init__(parent)
        self.render_page_callback = render_page_callback
        self.items = list(items or [])
        self.dest_path = dest_path
        self._tr = tr_func or translation.make_tr("de")
        self._cancel_requested = False

    def cancel(self):
        self._cancel_requested = True
        self.requestInterruption()

    def _is_cancelled(self) -> bool:
        return bool(self._cancel_requested or self.isInterruptionRequested())

    def run(self):
        total = len(self.items)
        if total <= 0:
            self.finished_batch.emit()
            return

        c = None
        try:
            self.status_changed.emit(self._tr("pdf_export_status_prepare"))
            self.progress_changed.emit(0)
            c = pdf_canvas.Canvas(self.dest_path, pagesize=(1, 1))

            for i, item in enumerate(self.items, start=1):
                if self._is_cancelled():
                    self.cancelled_export.emit(self.dest_path)
                    return

                display_name = getattr(item, "display_name", os.path.basename(getattr(item, "path", "")))
                self.page_started.emit(display_name, i, total)
                self.status_changed.emit(self._tr("pdf_export_status_page", i, total, display_name))

                if i > 1:
                    c.showPage()

                self.render_page_callback(c, item)
                self.progress_changed.emit(int((i / total) * 95))

            if self._is_cancelled():
                self.cancelled_export.emit(self.dest_path)
                return

            self.status_changed.emit(self._tr("pdf_export_status_saving"))
            self.progress_changed.emit(98)

            try:
                c.save()
            except PermissionError as e:
                raise PermissionError(
                    self._tr("pdf_export_write_blocked", self.dest_path)
                ) from e

            self.progress_changed.emit(100)
            self.status_changed.emit(self._tr("pdf_export_status_done"))
            self.pdf_done.emit(self.dest_path, total)

        except Exception as e:
            self.export_error.emit(str(e))
        finally:
            self.finished_batch.emit()
