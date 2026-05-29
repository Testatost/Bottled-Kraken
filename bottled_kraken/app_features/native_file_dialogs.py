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
    desk = _bk_native_desktop()
    if "kde" in desk or "plasma" in desk:
        if shutil.which("kdialog"):
            return "kdialog"
    if shutil.which("zenity"):
        return "zenity"
    if shutil.which("kdialog"):
        return "kdialog"
    return ""
def _bk_native_start_path(path: str) -> str:
    path = str(path or "").strip()
    if not path:
        return os.getcwd()
    return os.path.expanduser(path)
def _bk_native_subprocess_env() -> dict:
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
    try:
        started = time.monotonic()
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            env=_bk_native_subprocess_env(),
        )
        elapsed = time.monotonic() - started
        if proc.returncode == 0:
            return (proc.stdout or "").strip()
        if elapsed < 1.0:
            return None
        return ""
    except Exception:
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
        raw = _bk_native_run(["zenity", "--file-selection", "--save", "--confirm-overwrite", "--title", str(caption or ""), "--filename", start])
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
]
register_globals('bk', globals(), __all__)
