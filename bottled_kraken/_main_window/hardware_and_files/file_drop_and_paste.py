from bottled_kraken.common import (
    QApplication,
    QDragEnterEvent,
    QDropEvent,
    QFileDialog,
    QMessageBox,
    QThread,
    Signal,
    is_supported_drop_or_paste_file,
    os,
    re,
)
from bottled_kraken.workers import (
    clear_external_ocr_backend_cache,
)
class HardwareSnapshotWorker(QThread):
    done = Signal(dict)
    failed = Signal(str)
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
    def run(self):
        try:
            try:
                clear_external_ocr_backend_cache()
            except Exception:
                pass
            snapshot = self.owner._hardware_snapshot(refresh_backends=True)
            self.done.emit(snapshot)
        except Exception as exc:
            self.failed.emit(repr(exc))
class MainWindowFileDropAndPasteMixin:
        def dragEnterEvent(self, event: QDragEnterEvent):
            if not event.mimeData().hasUrls():
                event.ignore()
                return
            for u in event.mimeData().urls():
                p = u.toLocalFile()
                if p and os.path.exists(p) and is_supported_drop_or_paste_file(p):
                    event.acceptProposedAction()
                    return
            event.ignore()
        def dropEvent(self, event: QDropEvent):
            if not event.mimeData().hasUrls():
                event.ignore()
                return
            files = []
            for u in event.mimeData().urls():
                p = u.toLocalFile()
                if p and os.path.exists(p) and is_supported_drop_or_paste_file(p):
                    files.append(p)
            if files:
                self.add_files_to_queue(files)
                event.acceptProposedAction()
            else:
                event.ignore()
        def paste_files_from_clipboard(self):
            cb = QApplication.clipboard()
            md = cb.mimeData()
            files = []
            if md:
                if md.hasUrls():
                    for url in md.urls():
                        p = url.toLocalFile()
                        if p and os.path.exists(p) and is_supported_drop_or_paste_file(p):
                            files.append(p)
                if not files and md.hasText():
                    raw = md.text().strip()
                    if raw:
                        parts = [x.strip().strip('"') for x in raw.splitlines() if x.strip()]
                        for p in parts:
                            if os.path.exists(p) and is_supported_drop_or_paste_file(p):
                                files.append(p)
                if not files:
                    for fmt in md.formats():
                        try:
                            data = md.data(fmt)
                            if not data:
                                continue
                            txt = bytes(data).decode("utf-8", errors="ignore").strip("\x00").strip()
                            if not txt:
                                continue
                            for candidate in re.split(r'[\r\n]+', txt):
                                candidate = candidate.strip().strip('"')
                                if os.path.exists(candidate) and is_supported_drop_or_paste_file(candidate):
                                    files.append(candidate)
                        except Exception:
                            pass
            unique = []
            seen = set()
            for p in files:
                np = os.path.normpath(p)
                if np not in seen:
                    seen.add(np)
                    unique.append(p)
            if unique:
                self.add_files_to_queue(unique)
            else:
                QMessageBox.information(
                    self,
                    self._tr("info_title"),
                    self._tr("msg_clipboard_no_supported_files")
                )
        def choose_files(self):
            file_filter = (
                f"{self._tr('dlg_filter_img')};;"
                f"{self._tr('dlg_filter_project')}"
            )
            files, _ = QFileDialog.getOpenFileNames(
                self,
                self._tr("dlg_load_img"),
                "",
                file_filter
            )
            if files:
                self.add_files_to_queue(files)
