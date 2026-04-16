"""Anwendungsstart."""

from .shared import *
from .main_window import MainWindow
from . import ptr_features as _ptr_features  # noqa: F401
from . import bk_features as _bk_features  # noqa: F401

def main():
    if sys.platform.startswith("win"):
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("bottled.kraken.app")
        except Exception:
            pass
    app = QApplication(sys.argv)
    _install_exception_hook()
    app.setStyle("Fusion")
    icon_path = resource_path("icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    w = MainWindow()
    app.aboutToQuit.connect(w._cleanup_temp_dirs)
    if os.path.exists(icon_path):
        w.setWindowIcon(QIcon(icon_path))
    w.showMaximized()
    QCoreApplication.processEvents()
    try:
        if pyi_splash:
            pyi_splash.close()
    except Exception:
        pass
    sys.exit(app.exec())

