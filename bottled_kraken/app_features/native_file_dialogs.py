from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
import os
import shutil
import subprocess
import time
from PySide6.QtWidgets import QFileDialog
_BK_NATIVE_QFILEDIALOG_GET_OPEN_FILE_NAME = QFileDialog.getOpenFileName
_BK_NATIVE_QFILEDIALOG_GET_OPEN_FILE_NAMES = QFileDialog.getOpenFileNames
_BK_NATIVE_QFILEDIALOG_GET_SAVE_FILE_NAME = QFileDialog.getSaveFileName
_BK_NATIVE_QFILEDIALOG_GET_EXISTING_DIRECTORY = QFileDialog.getExistingDirectory
def _bk_native_desktop() -> str:
    return (
        os.environ.get("XDG_CURRENT_DESKTOP")
        or os.environ.get("KDE_FULL_SESSION")
        or os.environ.get("DESKTOP_SESSION")
        or ""
    ).lower()
def _bk_native_tool() -> str:
    # zenity/kdialog sind reine Linux-Helfer. Unter Windows und macOS werden
    # immer die Qt-eigenen (nativen) Dialoge verwendet.
    if not sys.platform.startswith("linux"):
        return ""
    desk = _bk_native_desktop()
    if "kde" in desk or "plasma" in desk:
        if shutil.which("kdialog"):
            return "kdialog"
    if shutil.which("zenity"):
        return "zenity"
    if shutil.which("kdialog"):
        return "kdialog"
    return ""


_BK_ZENITY_MAJOR = None


def _bk_zenity_major_version() -> int:
    """Hauptversion von zenity ermitteln (einmalig, mit Timeout).

    zenity 4.x (GTK4-Rewrite, u. a. Linux Mint 22 / Ubuntu 24.04) hat
    einzelne Optionen wie --confirm-overwrite entfernt. Damit der
    Speichern-Dialog auf allen Mint-Versionen funktioniert, wird die Option
    nur bei zenity 3.x uebergeben.
    """
    global _BK_ZENITY_MAJOR
    if _BK_ZENITY_MAJOR is not None:
        return _BK_ZENITY_MAJOR
    major = 0
    try:
        proc = subprocess.run(
            ["zenity", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            text=True,
            timeout=3.0,
            check=False,
            env=_bk_native_subprocess_env(),
        )
        text = (proc.stdout or "").strip()
        if text:
            major = int(text.split(".", 1)[0])
    except Exception:
        major = 0
    _BK_ZENITY_MAJOR = major
    return major


def _bk_zenity_save_args() -> list:
    args = ["zenity", "--file-selection", "--save"]
    if _bk_zenity_major_version() < 4:
        args.append("--confirm-overwrite")
    return args
def _bk_native_start_path(path: str) -> str:
    path = str(path or "").strip()
    if not path:
        return os.getcwd()
    return os.path.expanduser(path)
def _bk_native_subprocess_env() -> dict:
    # Gemeinsame, gruendlich bereinigte Umgebung (inkl. GTK-Variablen) aus
    # bottled_kraken.subprocess_env. zenity ist eine GTK-Anwendung; zeigen
    # GTK-/GIO-Variablen in das PyInstaller-Bundle, kann zenity ohne Fenster
    # haengen bleiben.
    try:
        from bottled_kraken.subprocess_env import bk_clean_child_env
        return bk_clean_child_env()
    except Exception:
        env = dict(os.environ)
        original_ld = env.get("LD_LIBRARY_PATH_ORIG")
        if original_ld is not None:
            env["LD_LIBRARY_PATH"] = original_ld
        else:
            env.pop("LD_LIBRARY_PATH", None)
        for key in (
            "LD_LIBRARY_PATH_ORIG",
            "PYTHONHOME",
            "PYTHONPATH",
            "QT_PLUGIN_PATH",
            "QT_QPA_PLATFORM_PLUGIN_PATH",
            "QML2_IMPORT_PATH",
            "PYSIDE_DESIGNER_PLUGINS",
        ):
            env.pop(key, None)
        for key, value in list(env.items()):
            if isinstance(value, str) and "_MEI" in value and ("QT" in key or "PYTHON" in key):
                env.pop(key, None)
        return env
def _bk_native_run(cmd) -> str | None:
    """Externen Dialog (zenity/kdialog) starten, ohne die Qt-Event-Loop
    einzufrieren.

    Frueher blockierte hier subprocess.run auf dem Qt-Hauptthread. Solange
    der Dialog offen war (oder zenity haengen blieb), stand die komplette
    Oberflaeche still - unter Linux Mint Cinnamon meldete der Desktop das
    Hauptfenster als "reagiert nicht" und die App wirkte aufgehaengt.
    Jetzt laeuft der Dialog ueber Popen, waehrenddessen werden Qt-Events
    weiter verarbeitet.
    """
    try:
        started = time.monotonic()
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            text=True,
            env=_bk_native_subprocess_env(),
        )
    except Exception:
        return None
    app = None
    try:
        from PySide6.QtWidgets import QApplication as _BKApp
        app = _BKApp.instance()
    except Exception:
        app = None
    try:
        while proc.poll() is None:
            if app is not None:
                try:
                    app.processEvents()
                except Exception:
                    pass
            time.sleep(0.02)
        out, _err = proc.communicate()
        elapsed = time.monotonic() - started
        if proc.returncode == 0:
            return (out or "").strip()
        # Schneller Fehlschlag (< 1 s): Werkzeug defekt/nicht nutzbar ->
        # None fuehrt zum Qt-Fallbackdialog. Spaeterer Nicht-Null-Exit ist
        # in aller Regel "Abbrechen" durch den Nutzer.
        if elapsed < 1.0:
            return None
        return ""
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
        return None
def _bk_native_qt_options(options):
    try:
        opts = QFileDialog.Options(options)
    except Exception:
        opts = QFileDialog.Options()
    try:
        opts &= ~QFileDialog.Option.DontUseNativeDialog
    except Exception:
        pass
    return opts
def _bk_native_file_filter_for_kdialog(file_filter: str) -> str:
    txt = str(file_filter or "").strip()
    if not txt:
        return "*"
    first = txt.split(";;", 1)[0].strip()
    return first or "*"
def _bk_native_first_line(raw: str | None) -> str:
    if raw is None:
        return ""
    for line in str(raw).splitlines():
        line = line.strip()
        if line:
            return line
    return ""
def _bk_native_get_open_file_name(parent=None, caption="", dir="", filter="", selectedFilter="", options=QFileDialog.Options()):
    tool = _bk_native_tool()
    start = _bk_native_start_path(dir)
    if tool == "kdialog":
        raw = _bk_native_run(["kdialog", "--title", str(caption or ""), "--getopenfilename", start, _bk_native_file_filter_for_kdialog(filter)])
        if raw is not None:
            return _bk_native_first_line(raw), selectedFilter or filter
    elif tool == "zenity":
        raw = _bk_native_run(["zenity", "--file-selection", "--title", str(caption or ""), "--filename", start])
        if raw is not None:
            return _bk_native_first_line(raw), selectedFilter or filter
    return _BK_NATIVE_QFILEDIALOG_GET_OPEN_FILE_NAME(parent, caption, dir, filter, selectedFilter, _bk_native_qt_options(options))
def _bk_native_get_open_file_names(parent=None, caption="", dir="", filter="", selectedFilter="", options=QFileDialog.Options()):
    tool = _bk_native_tool()
    start = _bk_native_start_path(dir)
    if tool == "kdialog":
        raw = _bk_native_run(["kdialog", "--title", str(caption or ""), "--multiple", "--separate-output", "--getopenfilename", start, _bk_native_file_filter_for_kdialog(filter)])
        if raw is not None:
            return [p.strip() for p in raw.splitlines() if p.strip()], selectedFilter or filter
    elif tool == "zenity":
        raw = _bk_native_run(["zenity", "--file-selection", "--multiple", "--separator=\n", "--title", str(caption or ""), "--filename", start])
        if raw is not None:
            return [p.strip() for p in raw.splitlines() if p.strip()], selectedFilter or filter
    return _BK_NATIVE_QFILEDIALOG_GET_OPEN_FILE_NAMES(parent, caption, dir, filter, selectedFilter, _bk_native_qt_options(options))
def _bk_native_get_save_file_name(parent=None, caption="", dir="", filter="", selectedFilter="", options=QFileDialog.Options()):
    tool = _bk_native_tool()
    start = _bk_native_start_path(dir)
    if tool == "kdialog":
        raw = _bk_native_run(["kdialog", "--title", str(caption or ""), "--getsavefilename", start, _bk_native_file_filter_for_kdialog(filter)])
        if raw is not None:
            return _bk_native_first_line(raw), selectedFilter or filter
    elif tool == "zenity":
        raw = _bk_native_run(_bk_zenity_save_args() + ["--title", str(caption or ""), "--filename", start])
        if raw is not None:
            return _bk_native_first_line(raw), selectedFilter or filter
    return _BK_NATIVE_QFILEDIALOG_GET_SAVE_FILE_NAME(parent, caption, dir, filter, selectedFilter, _bk_native_qt_options(options))
def _bk_native_get_existing_directory(parent=None, caption="", dir="", options=QFileDialog.Options()):
    tool = _bk_native_tool()
    start = _bk_native_start_path(dir)
    if tool == "kdialog":
        raw = _bk_native_run(["kdialog", "--title", str(caption or ""), "--getexistingdirectory", start])
        if raw is not None:
            return _bk_native_first_line(raw)
    elif tool == "zenity":
        raw = _bk_native_run(["zenity", "--file-selection", "--directory", "--title", str(caption or ""), "--filename", start])
        if raw is not None:
            return _bk_native_first_line(raw)
    return _BK_NATIVE_QFILEDIALOG_GET_EXISTING_DIRECTORY(parent, caption, dir, _bk_native_qt_options(options))
QFileDialog.getOpenFileName = staticmethod(_bk_native_get_open_file_name)
QFileDialog.getOpenFileNames = staticmethod(_bk_native_get_open_file_names)
QFileDialog.getSaveFileName = staticmethod(_bk_native_get_save_file_name)
QFileDialog.getExistingDirectory = staticmethod(_bk_native_get_existing_directory)
__all__ = [
    '_BK_NATIVE_QFILEDIALOG_GET_EXISTING_DIRECTORY',
    '_BK_NATIVE_QFILEDIALOG_GET_OPEN_FILE_NAME',
    '_BK_NATIVE_QFILEDIALOG_GET_OPEN_FILE_NAMES',
    '_BK_NATIVE_QFILEDIALOG_GET_SAVE_FILE_NAME',
    '_bk_native_desktop',
    '_bk_native_file_filter_for_kdialog',
    '_bk_native_first_line',
    '_bk_native_get_existing_directory',
    '_bk_native_get_open_file_name',
    '_bk_native_get_open_file_names',
    '_bk_native_get_save_file_name',
    '_bk_native_qt_options',
    '_bk_native_run',
    '_bk_native_start_path',
    '_bk_native_subprocess_env',
    '_bk_native_tool',
    '_bk_zenity_major_version',
    '_bk_zenity_save_args',
]
register_globals('bk', globals(), __all__)
