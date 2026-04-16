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
    def run(self):
        total = len(self.items)
        if total <= 0:
            self.finished_batch.emit()
            return
        for i, it in enumerate(self.items, start=1):
            if self.isInterruptionRequested():
                break
            base_name = os.path.splitext(it.display_name)[0]
            dest_path = os.path.join(self.folder, f"{base_name}.{self.fmt}")
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
