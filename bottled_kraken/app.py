"""Anwendungsstart."""

import os
import sys
import traceback

from PySide6.QtWidgets import QApplication, QWidget, QMessageBox
from PySide6.QtGui import QIcon, QPixmap, QPainter, QImage
from PySide6.QtCore import QCoreApplication, Qt, QTimer, QEventLoop, QRect

try:
    import pyi_splash as _pyi_splash  # type: ignore[import]
except Exception:
    _pyi_splash = None


_CRASH_LOG_FILE = None


def _app_log_dir() -> str:
    """Writable log directory, also in PyInstaller builds."""
    base = os.environ.get("BOTTLED_KRAKEN_LOG_DIR")
    if not base:
        base = os.path.join(os.path.expanduser("~"), ".bottled_kraken")
    try:
        os.makedirs(base, exist_ok=True)
    except Exception:
        base = os.getcwd()
    return base


def _install_crash_log() -> None:
    """
    Aktiviert faulthandler für native Abstürze/Segfaults.
    Harte Crashes landen hier: ~/.bottled_kraken/bottled_kraken_crash.log
    """
    global _CRASH_LOG_FILE
    try:
        import faulthandler
        import time
        import platform

        log_path = os.path.join(_app_log_dir(), "bottled_kraken_crash.log")
        _CRASH_LOG_FILE = open(log_path, "a", encoding="utf-8", buffering=1)
        _CRASH_LOG_FILE.write("\n" + "=" * 80 + "\n")
        _CRASH_LOG_FILE.write(time.strftime("[%Y-%m-%d %H:%M:%S] Bottled Kraken start\n"))
        _CRASH_LOG_FILE.write(f"Python: {sys.version}\n")
        _CRASH_LOG_FILE.write(f"Platform: {platform.platform()}\n")
        _CRASH_LOG_FILE.write("-" * 80 + "\n")
        faulthandler.enable(file=_CRASH_LOG_FILE, all_threads=True)
    except Exception:
        # Logging darf den Programmstart niemals verhindern.
        pass

def resource_path(relative_path: str) -> str:
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


def _pick_existing_resource(*names: str) -> str:
    for name in names:
        path = resource_path(name)
        if os.path.exists(path):
            return path
    return ""


def _install_early_exception_hook() -> None:
    def handle_exception(exc_type, exc_value, exc_tb):
        msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        try:
            QMessageBox.critical(None, "Fehler", msg)
        except Exception:
            try:
                print(msg, file=sys.stderr)
            except Exception:
                pass

    sys.excepthook = handle_exception


class _SplashWidget(QWidget):
    """Ein leichtgewichtiges Splash-Fenster für Wayland/KDE."""

    def __init__(self, pixmap: QPixmap) -> None:
        super().__init__(
            None,
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool,
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WA_NoSystemBackground, False)
        self._pixmap = pixmap
        self.setFixedSize(pixmap.width(), pixmap.height())

        screen = QApplication.primaryScreen()
        if screen is not None:
            screen_geom: QRect = screen.geometry()
            self.move(
                screen_geom.x() + (screen_geom.width() - pixmap.width()) // 2,
                screen_geom.y() + (screen_geom.height() - pixmap.height()) // 2,
            )

    def paintEvent(self, event) -> None:  # noqa: ANN001
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._pixmap)



def _load_pixmap(path: str) -> "QPixmap | None":
    try:
        from PIL import Image

        img = Image.open(path).convert("RGBA")
        w, h = img.size
        raw = img.tobytes("raw", "RGBA")
        qimg = QImage(raw, w, h, w * 4, QImage.Format.Format_RGBA8888)
        owned = qimg.copy()
        del raw, qimg
        pix = QPixmap.fromImage(owned)
        return pix if not pix.isNull() else None
    except Exception:
        pix = QPixmap(path)
        return pix if not pix.isNull() else None



def _compositor_sync(ms: int = 220) -> None:
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()



def _flush_gui(rounds: int = 3) -> None:
    for _ in range(rounds):
        QCoreApplication.processEvents()



def main():
    _install_crash_log()
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("bottled.kraken.app")
        except Exception:
            pass

    app = QApplication(sys.argv)
    _install_early_exception_hook()
    app.setStyle("Fusion")

    if sys.platform.startswith("linux"):
        icon_path = _pick_existing_resource("icon.png", "icon.ico")
    else:
        icon_path = _pick_existing_resource("icon.ico", "icon.png")

    if icon_path:
        app.setWindowIcon(QIcon(icon_path))

    # Eigenes Qt-Splash so früh wie möglich zeigen.
    splash = None
    splash_path = _pick_existing_resource(
        "splash.png",
        "splash_boot.png",
        "Bottled Kraken Screenshot.png",
    )
    if splash_path:
        pix = _load_pixmap(splash_path)
        if pix is not None:
            splash = _SplashWidget(pix)
            splash.show()
            splash.raise_()
            splash.update()
            _flush_gui(4)
            _compositor_sync(220)

    # Bootloader-Splash erst schließen, wenn unser Qt-Splash sichtbar ist.
    if _pyi_splash is not None:
        try:
            _pyi_splash.update_text("Lade Module ...")
        except Exception:
            pass

    from .shared import _install_exception_hook
    _install_exception_hook()

    from .main_window import MainWindow
    from . import ptr_features as _ptr_features  # noqa: F401
    from . import bk_features as _bk_features  # noqa: F401

    if _pyi_splash is not None:
        try:
            _pyi_splash.update_text("Erzeuge Hauptfenster ...")
        except Exception:
            pass

    window = MainWindow()

    if _pyi_splash is not None:
        try:
            _pyi_splash.update_text("Zeige Oberfläche ...")
        except Exception:
            pass

    window.showMaximized()
    _flush_gui(6)
    _compositor_sync(220)

    if splash is not None:
        splash.close()
        splash.deleteLater()
        splash = None
        _flush_gui(2)

    if _pyi_splash is not None:
        try:
            _pyi_splash.close()
        except Exception:
            pass

    sys.exit(app.exec())
