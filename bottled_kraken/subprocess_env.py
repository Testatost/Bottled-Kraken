"""Bereinigte Umgebungsvariablen fuer externe Subprozesse.

In PyInstaller-Bundles zeigen LD_LIBRARY_PATH, Qt- und Python-Variablen in
das Bundle-Verzeichnis (_MEI...). Externe Programme wie zenity, kdialog,
lspci oder nvidia-smi laden damit unter Umstaenden falsche Bibliotheken und
stuerzen ab oder haengen. Diese Funktion stellt eine saubere System-Umgebung
fuer Kindprozesse her und wird von den nativen Dateidialogen und der
GPU-Erkennung gemeinsam verwendet.
"""

import os
import sys

# Variablen, die PyInstaller/Qt setzen und die externe Programme stoeren.
_BK_CHILD_ENV_DROP = (
    "LD_LIBRARY_PATH_ORIG",
    "PYTHONHOME",
    "PYTHONPATH",
    "QT_PLUGIN_PATH",
    "QT_QPA_PLATFORM_PLUGIN_PATH",
    "QT_QPA_PLATFORM",
    "QT_QPA_PLATFORMTHEME",
    "QT_STYLE_OVERRIDE",
    "QT_SCALE_FACTOR",
    "QT_AUTO_SCREEN_SCALE_FACTOR",
    "QML2_IMPORT_PATH",
    "PYSIDE_DESIGNER_PLUGINS",
    # GTK-relevante Variablen: zenity ist eine GTK-Anwendung. Zeigen diese
    # Variablen in das Bundle (oder auf fremde Prefixe), kann zenity ohne
    # sichtbares Fenster haengen bleiben - genau das sah unter Linux Mint
    # Cinnamon wie ein Einfrieren der ganzen App aus.
    "GTK_PATH",
    "GTK_EXE_PREFIX",
    "GTK_DATA_PREFIX",
    "GTK_MODULES",
    "GIO_MODULE_DIR",
    "GIO_EXTRA_MODULES",
    "GDK_PIXBUF_MODULE_FILE",
    "GDK_PIXBUF_MODULEDIR",
    "GDK_BACKEND",
    "GST_PLUGIN_PATH",
    "GST_PLUGIN_SYSTEM_PATH",
    "FONTCONFIG_FILE",
    "FONTCONFIG_PATH",
)


def bk_clean_child_env() -> dict:
    """Kopie von os.environ, in der Bundle-spezifische Pfade entfernt sind."""
    env = dict(os.environ)
    original_ld = env.get("LD_LIBRARY_PATH_ORIG")
    if original_ld is not None:
        env["LD_LIBRARY_PATH"] = original_ld
    else:
        env.pop("LD_LIBRARY_PATH", None)
    for key in _BK_CHILD_ENV_DROP:
        env.pop(key, None)
    # Alles entfernen, was noch auf das entpackte PyInstaller-Verzeichnis zeigt.
    meipass = str(getattr(sys, "_MEIPASS", "") or "")
    for key, value in list(env.items()):
        if not isinstance(value, str):
            continue
        if "_MEI" in value or (meipass and meipass in value):
            upper = key.upper()
            if "QT" in upper or "PYTHON" in upper or "GTK" in upper or "GDK" in upper or "GIO" in upper or "XDG_DATA_DIRS" == upper:
                env.pop(key, None)
    return env
