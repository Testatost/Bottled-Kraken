# -*- mode: python ; coding: utf-8 -*-

import importlib.util
import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import (
    collect_data_files,
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

PROJECT_ROOT = Path(os.path.abspath(globals().get("SPECPATH", "."))).resolve()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

APP_NAME = "Bottled Kraken"
APP_EXE_NAME = "Bottled Kraken"
APP_VERSION = "3.2"
APP_AUTHOR = "Sebastian S. (Testatost) & Benedikt E. - Universität Leipzig"
APP_PLATFORM = "Windows 10 / Windows 11"
APP_DESCRIPTION = f"{APP_NAME} v{APP_VERSION} - {APP_AUTHOR} - {APP_PLATFORM}"

version_info = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(3, 2, 0, 0),
        prodvers=(3, 2, 0, 0),
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
                        StringStruct("FileDescription", APP_DESCRIPTION),
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

datas = []
binaries = []
hiddenimports = []


def has_module(name):
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def safe_data(name):
    try:
        return collect_data_files(name) if has_module(name) else []
    except Exception:
        return []


def safe_libs(name):
    try:
        return collect_dynamic_libs(name) if has_module(name) else []
    except Exception:
        return []


def safe_submodules(name):
    try:
        return collect_submodules(name) if has_module(name) else []
    except Exception:
        return []


def safe_metadata(name):
    try:
        return copy_metadata(name)
    except Exception:
        return []


def dedupe(items):
    seen = set()
    out = []
    for item in items:
        key = tuple(item) if isinstance(item, (list, tuple)) else item
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def add_file(rel_path, dest="."):
    src = PROJECT_ROOT / rel_path
    if src.is_file():
        datas.append((str(src), dest))


def add_dir(rel_dir, dest=None, pattern="*", recursive=True):
    src_dir = PROJECT_ROOT / rel_dir
    if not src_dir.is_dir():
        return
    dest_root = (dest or rel_dir).replace("\\", "/")
    iterator = src_dir.rglob if recursive else src_dir.glob
    for path in iterator(pattern):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts:
            continue
        rel_parent = path.parent.relative_to(src_dir).as_posix()
        target = dest_root if rel_parent == "." else f"{dest_root}/{rel_parent}"
        datas.append((str(path), target))


def add_pkg(module, metadata=None, data=False, libs=False, submodules=False):
    if not has_module(module):
        return
    hiddenimports.append(module)
    if data:
        datas.extend(safe_data(module))
    if libs:
        binaries.extend(safe_libs(module))
    if submodules:
        hiddenimports.extend(safe_submodules(module))
    datas.extend(safe_metadata(metadata or module))


# -------------------------------------------------
# Statische Dateien
# -------------------------------------------------
for file in (
    "icon.ico",
    "icon.png",
    "splash.png",
    "logo.png",
):
    add_file(file, ".")


# -------------------------------------------------
# Split-Loader-Ordner als echte Dateien mitgeben
# -------------------------------------------------
for folder in (
    "bottled_kraken/_shared_parts",
    "bottled_kraken/_bk_features_parts",
    "bottled_kraken/_ptr_features_parts",
    "bottled_kraken/_translation_data",
):
    add_dir(folder, folder, "*.py", recursive=False)


# -------------------------------------------------
# Optionale lokale Ressourcen / Modelle
# -------------------------------------------------
for folder in (
    "models",
    "kraken_models",
    "Kraken-Modelle",
    "resources",
    "bottled_kraken/models",
    "bottled_kraken/kraken_models",
    "bottled_kraken/resources",
):
    add_dir(folder, folder, "*", recursive=True)


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
    hiddenimports.extend(safe_submodules(pkg))

hiddenimports.extend([
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
    "bottled_kraken._workers.backend_installer",
    "bottled_kraken._workers.external_backend_ocr",
    "pyi_splash",

    # PySide6 / Qt
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtSvg",
    "PySide6.QtNetwork",
    "PySide6.QtPrintSupport",

    # Pillow
    "PIL.Image",
    "PIL.ImageQt",
    "PIL.ImageOps",
    "PIL.ImageEnhance",
    "PIL.PngImagePlugin",
    "PIL.JpegImagePlugin",
    "PIL.TiffImagePlugin",
    "PIL.WebPImagePlugin",

    # PyMuPDF
    "fitz",
    "pymupdf",

    # Kraken / OCR
    "kraken",
    "kraken.blla",
    "kraken.rpred",
    "kraken.serialization",
    "kraken.containers",
    "kraken.lib.models",
    "kraken.lib.vgsl",
    "kraken.lib.dataset",
    "kraken.lib.dataset.recognition",

    # Kraken-Abhängigkeiten
    "torch",
    "torch.testing",
    "torch.testing._comparison",
    "torch.testing._creation",
    "torchvision",
    "torchvision.transforms",
    "torchvision.transforms.functional",
    "torchvision.io",
    "pyarrow",
    "pyarrow.lib",
    "pyarrow.dataset",
    "pyarrow.parquet",
    "pyarrow.ipc",

    # Optional durch Kraken-Importpfade; wird nur gesammelt, wenn installiert.
    "coremltools",
    "coremltools.converters",
    "coremltools.models",
    "coremltools.proto",
    "coremltools.optimize",

    # LM / Whisper / HuggingFace
    "ctranslate2",
    "faster_whisper",
    "faster_whisper.assets",
    "huggingface_hub",
    "transformers",
    "safetensors",
    "tokenizers",
])


# -------------------------------------------------
# Externe Pakete
# -------------------------------------------------
# PyInstaller-Hooks sammeln die nötigen Qt-Bibliotheken bereits.
# collect_dynamic_libs("PySide6") würde zu viele Qt-Plugins mitnehmen.
add_pkg("PySide6", metadata="PySide6", data=False, libs=False)
add_pkg("shiboken6", metadata="shiboken6", data=False, libs=False)

add_pkg("PIL", metadata="Pillow", data=True)
add_pkg("numpy", metadata="numpy", libs=True)

add_pkg("fitz", metadata="PyMuPDF", data=True, libs=True)
add_pkg("pymupdf", metadata="PyMuPDF", data=True, libs=True)

add_pkg("pyarrow", metadata="pyarrow", data=True, libs=True)
add_pkg("coremltools", metadata="coremltools", data=True, libs=True, submodules=False)

add_pkg("kraken", metadata="kraken", data=True, submodules=True)
add_pkg("reportlab", metadata="reportlab", data=True, submodules=True)

add_pkg("torch", metadata="torch", data=True, libs=True)
add_pkg("torchvision", metadata="torchvision", data=True, libs=True)

add_pkg("ctranslate2", metadata="ctranslate2", data=True, libs=True)
add_pkg("faster_whisper", metadata="faster-whisper", data=True, submodules=True)

add_pkg("huggingface_hub", metadata="huggingface_hub", data=True)
add_pkg("transformers", metadata="transformers", data=True)
add_pkg("safetensors", metadata="safetensors", data=True, libs=True)
add_pkg("tokenizers", metadata="tokenizers", data=True, libs=True)

for module, metadata, with_libs in (
    ("accelerate", "accelerate", False),
    ("whisper", "openai-whisper", False),
    ("tiktoken", "tiktoken", True),
    ("sounddevice", "sounddevice", False),
):
    add_pkg(module, metadata=metadata, data=True, libs=with_libs)

if has_module("tiktoken_ext"):
    hiddenimports.extend(safe_submodules("tiktoken_ext"))


# -------------------------------------------------
# Aufräumen
# -------------------------------------------------
DROP_PREFIXES = (
    "PySide6.scripts",
    "PySide6.examples",
    "PySide6.QtDesigner",
    "PySide6.QtWebEngine",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuickWidgets",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "numpy.tests",
    "numpy.f2py.tests",
    "pyarrow.tests",
    "torch._dynamo.test",
    "torch.fx.passes.tests",
    "reportlab.graphics.samples",
    "reportlab.graphics.testdrawings",
)

DROP_CONTAINS = (
    ".tests.",
    ".test_",
    ".conftest",
)


def keep_hidden(name):
    if any(name == p or name.startswith(p + ".") for p in DROP_PREFIXES):
        return False
    if any(x in name for x in DROP_CONTAINS):
        return False
    return True


hiddenimports = sorted({h for h in hiddenimports if h and keep_hidden(h)})
datas = dedupe(datas)
binaries = dedupe(binaries)


# -------------------------------------------------
# Build: OneFile / Windows CPU-Release
# -------------------------------------------------
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
        # Nur PySide6 verwenden.
        "PyQt5",
        "PyQt6",
        "PySide2",

        # Nicht benötigte macOS-/Linux-spezifische Module.
        "AppKit",
        "Foundation",
        "objc",

        # Dev-/Notebook-/Testumgebungen.
        "pytest",
        "IPython",
        "jupyter",
        "notebook",
        "matplotlib",
        "tkinter",

        # Nicht benötigte ML-Backends für den Windows-CPU-Release.
        "tensorflow",
        "keras",
        "jax",
        "jaxlib",
        "flax",
        "paddle",
        "onnx",
        "onnxruntime",
        "cupy",

        # CPU-Release: kein CUDA/Triton im Hauptprogramm.
        "nvidia",
        "cuda_bindings",
        "triton",
        "torchaudio",

        # Nur relevant, wenn man TensorBoard aktiv nutzt.
        "tensorboard",
        "torch.utils.tensorboard",

        # Tests.
        "numpy.tests",
        "pyarrow.tests",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

splash = None
splash_path = PROJECT_ROOT / "splash.png"

if splash_path.is_file():
    splash = Splash(
        str(splash_path),
        binaries=a.binaries,
        datas=a.datas,
        text_pos=None,
        text_size=12,
        minify_script=True,
        always_on_top=False,
    )

exe_args = [pyz, a.scripts]

if splash is not None:
    exe_args.extend([splash, splash.binaries])

exe_args.extend([
    a.binaries,
    a.datas,
    [],
])

exe_kwargs = dict(
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
)

icon_path = PROJECT_ROOT / "icon.ico"
if icon_path.is_file():
    exe_kwargs["icon"] = str(icon_path)

exe = EXE(
    *exe_args,
    **exe_kwargs,
)
