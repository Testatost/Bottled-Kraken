# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(os.path.abspath(globals().get("SPECPATH", "."))).resolve()

# Wichtig für lokale Projektpakete und collect_submodules() bei der refaktorierten Struktur
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyInstaller.utils.hooks import (
    collect_all,
    collect_dynamic_libs,
    collect_submodules,
    copy_metadata,
)
from PyInstaller.utils.win32.versioninfo import (
    VSVersionInfo,
    FixedFileInfo,
    StringFileInfo,
    StringTable,
    StringStruct,
    VarFileInfo,
    VarStruct,
)

block_cipher = None

APP_NAME = "Bottled Kraken"
APP_EXE_NAME = "Bottled Kraken"
APP_VERSION = "3.0"

version_info = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(3, 0, 0, 0),
        prodvers=(3, 0, 0, 0),
        mask=0x3F,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0),
    ),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    "040704B0",
                    [
                        StringStruct("CompanyName", "Privat"),
                        StringStruct(
                            "FileDescription",
                            "Bottled Kraken v3 - Sebastian S. (Testatost) & Benedikt E. - Universität Leipzig",
                        ),
                        StringStruct("FileVersion", APP_VERSION),
                        StringStruct("InternalName", APP_NAME),
                        StringStruct("OriginalFilename", f"{APP_EXE_NAME}.exe"),
                        StringStruct("ProductName", APP_NAME),
                        StringStruct("ProductVersion", APP_VERSION),
                    ],
                )
            ]
        ),
        VarFileInfo([VarStruct("Translation", [1031, 1200])]),
    ],
)


def safe_collect_all(package_name):
    try:
        return collect_all(package_name)
    except Exception:
        return [], [], []



def safe_collect_submodules(package_name):
    try:
        return collect_submodules(package_name)
    except Exception:
        return []



def safe_collect_dynamic_libs(package_name):
    try:
        return collect_dynamic_libs(package_name)
    except Exception:
        return []



def safe_copy_metadata(package_name):
    try:
        return copy_metadata(package_name)
    except Exception:
        return []



def dedupe_toc(items):
    seen = set()
    out = []
    for item in items:
        key = tuple(item) if isinstance(item, (list, tuple)) else item
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out



datas = []
binaries = []
hiddenimports = []



def add_data_file(rel_path, dest="."):
    src = PROJECT_ROOT / rel_path
    if src.exists():
        datas.append((str(src), dest))



def add_data_dir(rel_dir, dest=None, pattern="*"):
    src_dir = PROJECT_ROOT / rel_dir
    if src_dir.exists():
        datas.append((str(src_dir / pattern), dest or rel_dir.replace("\\", "/")))



def add_package(package_name, add_dynamic_libs=False, add_metadata=True):
    global datas, binaries, hiddenimports

    d, b, h = safe_collect_all(package_name)
    datas += d
    binaries += b
    hiddenimports += h

    hiddenimports += safe_collect_submodules(package_name)

    if add_metadata:
        datas += safe_copy_metadata(package_name)

    if add_dynamic_libs:
        binaries += safe_collect_dynamic_libs(package_name)


# -------------------------------------------------
# Statische Dateien
# -------------------------------------------------
add_data_file("icon.ico", ".")
add_data_file("splash.png", ".")

# -------------------------------------------------
# Split-Loader-Ordner als echte Dateien mitgeben
# -------------------------------------------------
# Diese Ordner werden zur Laufzeit von bottled_kraken/_module_loader.py
# physisch vom Dateisystem gelesen. hiddenimports allein reichen dafür nicht.
for rel_dir in (
    "bottled_kraken/_shared_parts",
    "bottled_kraken/_bk_features_parts",
    "bottled_kraken/_ptr_features_parts",
    "bottled_kraken/_translation_data",
):
    add_data_dir(rel_dir, rel_dir, pattern="*.py")

# -------------------------------------------------
# Lokales Projektpaket
# -------------------------------------------------
for pkg in (
    "bottled_kraken",
    "bottled_kraken._shared_parts",
    "bottled_kraken._workers",
    "bottled_kraken._ui_components",
    "bottled_kraken._image_edit",
    "bottled_kraken._main_window",
    "bottled_kraken._ptr_features_parts",
    "bottled_kraken._bk_features_parts",
    "bottled_kraken._translation_data",
):
    hiddenimports += safe_collect_submodules(pkg)

hiddenimports += [
    "bottled_kraken",
    "bottled_kraken.app",
    "bottled_kraken.shared",
    "bottled_kraken.translation",
    "bottled_kraken.ui_components",
    "bottled_kraken.dialogs",
    "bottled_kraken.image_edit",
    "bottled_kraken.workers",
    "bottled_kraken.main_window",
    "bottled_kraken.ptr_features",
    "bottled_kraken.bk_features",
    "PIL.ImageQt",
]

# -------------------------------------------------
# Externe Pakete
# -------------------------------------------------
for pkg in (
    "PySide6",
    "shiboken6",
    "PIL",
    "numpy",
    "sounddevice",
    "kraken",
    "reportlab",
    "fitz",
    "torch",
    "ctranslate2",
    "faster_whisper",
    "huggingface_hub",
):
    add_package(
        pkg,
        add_dynamic_libs=pkg in {
            "PySide6",
            "shiboken6",
            "torch",
            "ctranslate2",
            "sounddevice",
            "fitz",
        },
    )

# PyMuPDF-Metadaten separat absichern
# (das Importmodul heißt fitz, die Paket-Metadaten PyMuPDF)
datas += safe_copy_metadata("PyMuPDF")

datas = dedupe_toc(datas)
binaries = dedupe_toc(binaries)
hiddenimports = sorted(set(hiddenimports))

a = Analysis(
    [str(PROJECT_ROOT / "main.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PyQt5",
        "PyQt6",
        "PySide2",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

splash = Splash(
    str(PROJECT_ROOT / "splash.png"),
    binaries=a.binaries,
    datas=a.datas,
    always_on_top=False,
)

exe = EXE(
    pyz,
    a.scripts,
    splash,
    splash.binaries,
    a.binaries,
    a.datas,
    [],
    name=APP_EXE_NAME,
    version=version_info,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(PROJECT_ROOT / "icon.ico"),
)
