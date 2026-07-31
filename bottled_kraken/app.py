import os
import sys
import traceback
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox
from PySide6.QtGui import QIcon, QPixmap, QPainter, QImage
from PySide6.QtCore import QCoreApplication, Qt, QTimer, QEventLoop, QRect
from bottled_kraken.translation import translation
from bottled_kraken.user_storage import bottled_kraken_user_path
from bottled_kraken.resource_paths import resource_path
from bottled_kraken.runtime_logging import (
    configure_logging,
    get_logger,
    install_exception_hooks,
)
try:
    import pyi_splash as _pyi_splash
except Exception:
    _pyi_splash = None
_CRASH_LOG_FILE = None
def _app_log_dir() -> str:
    base = os.environ.get("BOTTLED_KRAKEN_LOG_DIR")
    if not base:
        base = str(bottled_kraken_user_path("logs"))
    try:
        os.makedirs(base, exist_ok=True)
    except Exception:
        base = os.getcwd()
    return base
def _install_crash_log() -> None:
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
        get_logger("startup").exception("Could not initialize faulthandler crash log")
def _pick_existing_resource(*names: str) -> str:
    for name in names:
        path = resource_path(name)
        if os.path.exists(path):
            return path
    return ""
def _active_exception_dialog_context():
    parent = None
    lang = _startup_language() if "_startup_language" in globals() else translation.DEFAULT_LANGUAGE
    try:
        app = QApplication.instance()
        if app is not None:
            parent = app.activeWindow()
        if parent is not None:
            lang = getattr(parent, "current_lang", lang)
    except Exception:
        get_logger("exceptions").debug("Could not resolve active UI language", exc_info=True)
    return parent, translation.normalize_language_code(lang)

def _show_unhandled_exception_dialog(exc_type, exc_value, error_id: str, path: str) -> None:
    parent, lang = _active_exception_dialog_context()
    detail = f"{getattr(exc_type, '__name__', 'Exception')}: {exc_value}".strip()
    if len(detail) > 600:
        detail = detail[:597] + "…"
    message = "\n\n".join((
        translation.translate(lang, "error_unexpected_summary"),
        translation.translate(lang, "error_detail", detail),
        translation.translate(lang, "error_reference", error_id),
        translation.translate(lang, "error_log_saved_to", path),
    ))
    QMessageBox.critical(parent, translation.translate(lang, "error_title"), message)

def _install_early_exception_hook() -> None:
    install_exception_hooks(_show_unhandled_exception_dialog)

class _SplashWidget(QWidget):
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
    def paintEvent(self, event) -> None:
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


def _startup_language() -> str:
    """Resolve the UI language before the main window and its settings exist."""
    try:
        from PySide6.QtCore import QLocale, QSettings
        settings_file = str(bottled_kraken_user_path("settings") / "settings.ini")
        settings = QSettings(settings_file, QSettings.IniFormat)
        configured = str(settings.value("ui/language", "") or "").strip()
        detected = configured or QLocale.system().name()
    except Exception:
        detected = translation.DEFAULT_LANGUAGE
    return translation.normalize_language_code(detected)


def _startup_text(language: str, key: str) -> str:
    """Translate a startup status with the normal English fallback policy."""
    return translation.translate(language, key)


def _bk_install_qt_base_translator(app, lang: str = None) -> None:
    """Laedt Qts eigene Basisuebersetzungen (qtbase_<lang>.qm).

    Ohne diese bleiben Qts EINGEBAUTE Oberflaechen englisch - z. B. das
    Rechtsklick-Menue von Textfeldern (Undo/Redo/Cut/Copy/Paste/Select All),
    Standard-Dialogknoepfe und Dateidialog-Texte. Das sind keine App-
    Uebersetzungsschluessel; die eigenen Uebersetzungstests konnten das daher
    prinzipiell nicht erkennen. Wird beim Start und bei jedem Sprachwechsel
    (retranslate_ui) mit der jeweils aktiven Sprache aufgerufen."""
    try:
        from PySide6.QtCore import QTranslator, QLibraryInfo, QLocale, QSettings
        if lang is None:
            try:
                settings = QSettings("BottledKraken", "OCRApp")
                lang = str(settings.value("ui/language", "") or "") or QLocale.system().name()[:2]
            except Exception:
                lang = QLocale.system().name()[:2]
        lang = str(lang or "de")[:2].lower()
        old = getattr(app, "_bk_qt_base_translator", None)
        if old is not None:
            try:
                app.removeTranslator(old)
            except Exception:
                pass
        translator = QTranslator(app)
        path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
        if translator.load(f"qtbase_{lang}", path):
            app.installTranslator(translator)
            app._bk_qt_base_translator = translator
        else:
            app._bk_qt_base_translator = None
    except Exception:
        pass
def _bk_linux_display_preflight() -> None:
    """Startabstuerze unter Linux abfangen, bevor QApplication erzeugt wird.

    Hintergrund: PySide6/Qt >= 6.5 benoetigt fuer das xcb-Plugin die
    Systembibliothek libxcb-cursor. Auf Linux Mint (Cinnamon/MATE/Xfce,
    Ubuntu-Basis) ist libxcb-cursor0 nicht immer vorinstalliert. Fehlt sie
    und wurde sie nicht mitgebundelt, bricht Qt beim Laden des xcb-Plugins
    hart ab ("could not load the Qt platform plugin xcb") - fuer den Nutzer
    sieht das wie ein Absturz direkt nach dem Start aus, oft ohne jede
    Meldung. Linux Mint 22.x benötigt dafür das Paket libxcb-cursor0.

    Gegenmassnahmen:
    1. In einer Wayland-Sitzung wird das native wayland-Plugin immer vor xcb
       gewaehlt, auch wenn XWayland zusaetzlich DISPLAY gesetzt hat. Damit
       startet auch eine optionale Cinnamon-Wayland-Sitzung nativ und bleibt
       bei fraktionaler Skalierung scharf. xcb bleibt nur der Fallback.
    2. Fehlt libxcb-cursor auf einem primaeren X11-Start und liegt auch keine
       Kopie im PyInstaller-Bundle, wird ein klarer Hinweis in Protokoll,
       Crash-Log und stderr geschrieben (inkl. Installationsbefehl fuer
       Mint/Ubuntu und Fedora), statt kommentarlos abzubrechen.
    """
    if not sys.platform.startswith("linux"):
        return
    try:
        has_x11 = bool(os.environ.get("DISPLAY"))
        has_wayland = bool(os.environ.get("WAYLAND_DISPLAY"))
        if not os.environ.get("QT_QPA_PLATFORM"):
            if has_wayland:
                # Under a native Wayland session DISPLAY is commonly present
                # because XWayland is available. WAYLAND_DISPLAY must therefore
                # take precedence; xcb remains a fallback only.
                os.environ["QT_QPA_PLATFORM"] = "wayland;xcb"
            elif has_x11:
                os.environ["QT_QPA_PLATFORM"] = "xcb"
        platform_order = os.environ.get("QT_QPA_PLATFORM", "")
        xcb_is_primary = platform_order.split(";", 1)[0].strip() == "xcb"
        if has_x11 and xcb_is_primary:
            found = None
            try:
                import ctypes.util
                found = ctypes.util.find_library("xcb-cursor")
            except Exception:
                found = None
            if not found:
                bundle_dir = str(getattr(sys, "_MEIPASS", "") or "")
                bundled = False
                if bundle_dir:
                    try:
                        for name in os.listdir(bundle_dir):
                            if name.startswith("libxcb-cursor"):
                                bundled = True
                                break
                    except Exception:
                        bundled = False
                if not bundled:
                    # Text aus den Sprachdateien; die Paketbefehle selbst sind
                    # sprachneutral und bleiben als technische Angabe stehen.
                    try:
                        message = translation.translate(translation.DEFAULT_LANGUAGE, "startup_hint_missing_xcb_cursor")
                        if not message or message == "startup_hint_missing_xcb_cursor":
                            message = "libxcb-cursor: not found"
                    except Exception:
                        message = "libxcb-cursor: not found"
                    hint = (
                        "[bottled_kraken] " + message + "\n"
                        "  Linux Mint / Ubuntu / Debian:  sudo apt install libxcb-cursor0\n"
                        "  Fedora:                        sudo dnf install xcb-util-cursor\n"
                    )
                    get_logger("startup").warning("%s", hint.rstrip())
                    try:
                        print(hint, file=sys.stderr)
                    except Exception:
                        get_logger("startup").debug("Could not write xcb hint to stderr", exc_info=True)
                    try:
                        if _CRASH_LOG_FILE is not None:
                            _CRASH_LOG_FILE.write(hint)
                    except Exception:
                        pass
    except Exception:
        # Der Preflight darf den Start niemals selbst verhindern.
        get_logger("startup").exception("Linux display preflight failed")


def main():
    logger = configure_logging()
    _install_early_exception_hook()
    logger.info("Starting Bottled Kraken")
    _install_crash_log()
    _bk_linux_display_preflight()
    logger.info("Qt platform preference: %s", os.environ.get("QT_QPA_PLATFORM", "auto"))
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("bottled.kraken.app")
        except Exception:
            pass
    try:
        app = QApplication(sys.argv)
    except Exception:
        # Wenn schon die QApplication scheitert (fehlende Plattform-Plugins,
        # fehlende Systembibliotheken), landet der Traceback im Crash-Log
        # statt in einem stummen Abbruch.
        msg = traceback.format_exc()
        logger.critical("QApplication creation failed", exc_info=True)
        try:
            print(msg, file=sys.stderr)
            if _CRASH_LOG_FILE is not None:
                _CRASH_LOG_FILE.write(msg + "\n")
        except Exception:
            logger.debug("Could not mirror QApplication failure to crash log", exc_info=True)
        raise
    startup_language = _startup_language()
    _bk_install_qt_base_translator(app, startup_language)
    app.setStyle("Fusion")
    if sys.platform.startswith("linux"):
        icon_path = _pick_existing_resource("icon.png", "icon.ico")
    else:
        icon_path = _pick_existing_resource("icon.ico", "icon.png")
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))
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
    if _pyi_splash is not None:
        try:
            _pyi_splash.update_text(_startup_text(startup_language, "startup_loading_modules"))
        except Exception:
            pass
    from bottled_kraken.main_window import MainWindow
    from bottled_kraken.common.chain_consolidation import (
        capture_base_hooks,
        install_consolidated_hooks,
    )
    capture_base_hooks(MainWindow)  # BK-OPT: must run before any feature import
    from bottled_kraken import pointer_features as _ptr_features
    from bottled_kraken import app_features as _bk_features
    install_consolidated_hooks(MainWindow)  # BK-OPT: replaces the 22x/17x monkey-patch chain
    if str(os.environ.get("BOTTLED_KRAKEN_WRITE_REGISTRY_DIAGNOSTICS", "")).strip().lower() in {"1", "true", "yes", "on"}:
        try:
            from bottled_kraken.module_registry import write_registry_diagnostics
            diagnostic_path = write_registry_diagnostics(
                bottled_kraken_user_path("logs") / "registry_diagnostics.json",
                MainWindow,
            )
            logger.info("Registry diagnostics written to %s", diagnostic_path)
        except Exception:
            logger.exception("Could not write registry diagnostics")
    if _pyi_splash is not None:
        try:
            _pyi_splash.update_text(_startup_text(startup_language, "startup_creating_main_window"))
        except Exception:
            pass
    window = MainWindow()
    if _pyi_splash is not None:
        try:
            _pyi_splash.update_text(_startup_text(startup_language, "startup_showing_ui"))
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
    exit_code = app.exec()
    logger.info("Bottled Kraken stopped with exit code %s", exit_code)
    sys.exit(exit_code)
