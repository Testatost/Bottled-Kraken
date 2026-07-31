from __future__ import annotations

import threading

from PySide6.QtCore import QThread, Signal

from bottled_kraken.kraken_update import install_latest_kraken


class KrakenUpdateWorker(QThread):
    progress = Signal(int, str)
    completed = Signal(str, str, bool)
    failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cancel_event = threading.Event()

    def cancel(self) -> None:
        self._cancel_event.set()

    def run(self) -> None:
        try:
            result = install_latest_kraken(
                on_progress=lambda percent, detail: self.progress.emit(int(percent), str(detail)),
                cancel_event=self._cancel_event,
            )
            self.completed.emit(result.version, result.sha, result.changed)
        except Exception as exc:
            self.failed.emit(str(exc))


__all__ = ["KrakenUpdateWorker"]
