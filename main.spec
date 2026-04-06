# -*- mode: python ; coding: utf-8 -*-

import os
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

# -----------------------------
# Windows-Dateiversion der EXE
# -----------------------------
version_info = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(2, 9, 0, 0),
        prodvers=(2, 9, 0, 0),
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
                    "040904B0",
                    [
                        StringStruct("CompanyName", "Sebastian - Universität Leipzig"),
                        StringStruct("FileDescription", "Bottled Kraken - Sebastian (Testatost) - Universität Leipzig"),
                        StringStruct("FileVersion", "2.9"),
                        StringStruct("InternalName", "Bottled Kraken"),
                        StringStruct("OriginalFilename", "Bottled Kraken.exe"),
                        StringStruct("ProductName", "Bottled Kraken"),
                        StringStruct("ProductVersion", "2.9"),
                    ],
                )
            ]
        ),
        VarFileInfo([VarStruct("Translation", [1033, 1200])]),
    ],
)


def safe_collect_all(package_name):
    try:
        return collect_all(package_name)
    except Exception:
        return [], [], []


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


datas = [
    ("icon.ico", "."),
    ("splash.png", "."),
]

binaries = []
hiddenimports = []

for pkg in (
    "faster_whisper",
    "sounddevice",
    "kraken",
    "reportlab",
    "fitz",
):
    d, b, h = safe_collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

for pkg in (
    "ctranslate2",
    "torch",
):
    binaries += safe_collect_dynamic_libs(pkg)

for pkg in (
    "faster_whisper",
    "ctranslate2",
    "kraken",
    "reportlab",
    "fitz",
    "torch",
):
    datas += safe_copy_metadata(pkg)

try:
    hiddenimports += collect_submodules("faster_whisper")
except Exception:
    pass

try:
    hiddenimports += collect_submodules("kraken")
except Exception:
    pass

try:
    hiddenimports += collect_submodules("ctranslate2")
except Exception:
    pass

datas = dedupe_toc(datas)
binaries = dedupe_toc(binaries)
hiddenimports = sorted(set(hiddenimports))

a = Analysis(
    ["main.py"],
    pathex=[os.path.abspath(".")],
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
    "splash.png",
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
    name="Bottled Kraken",
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
    icon="icon.ico",
)