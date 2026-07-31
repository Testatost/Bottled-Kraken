# -*- mode: python ; coding: utf-8 -*-

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
    copy_metadata,
)

# Diese Spec ist für Windows 10/11 x64 gedacht.
# Sie muss unter Windows ausgeführt werden; PyInstaller ist kein Cross-Compiler.
IS_WINDOWS = sys.platform.startswith("win")
if IS_WINDOWS:
    from PyInstaller.utils.win32.versioninfo import (
        FixedFileInfo,
        StringFileInfo,
        StringStruct,
        StringTable,
        VarFileInfo,
        VarStruct,
        VSVersionInfo,
    )

block_cipher = None

PROJECT_ROOT = Path(os.path.abspath(globals().get("SPECPATH", "."))).resolve()
PACKAGE_ROOT = PROJECT_ROOT / "bottled_kraken"
TRANSLATIONS_ROOT = PACKAGE_ROOT / "translations"
DICTIONARIES_ROOT = PACKAGE_ROOT / "dictionaries"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bottled_kraken.version_config import APP_NAME, APP_VERSION

APP_EXE_NAME = APP_NAME
APP_AUTHOR = "Sebastian S. (Testatost) & Benedikt E. - Universität Leipzig"
APP_PLATFORM = "Windows 10/11 x64"
APP_DESCRIPTION = f"{APP_NAME} v{APP_VERSION} - {APP_AUTHOR} - {APP_PLATFORM}"

def _numeric_version_tuple(version):
    parts = [int(part) for part in __import__("re").findall(r"\d+", str(version))[:4]]
    return tuple((parts + [0, 0, 0, 0])[:4])

APP_VERSION_TUPLE = _numeric_version_tuple(APP_VERSION)

version_info = None
if IS_WINDOWS:
    version_info = VSVersionInfo(
        ffi=FixedFileInfo(
            filevers=APP_VERSION_TUPLE,
            prodvers=APP_VERSION_TUPLE,
            mask=0x3F,
            flags=0x0,
            OS=0x40004,
            fileType=0x1,
            subtype=0x0,
            date=(0, 0),
        ),
        kids=[
            StringFileInfo([
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
            ]),
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
        if path.suffix in {".pyc", ".pyo"}:
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


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def add_dictionary_bundle():
    """Packt alle Wörterbücher plus einen stabilen Inhaltsmanifest ein.

    PyInstaller-Onefile entpackt Ressourcen bei jedem Start mit neuen mtimes.
    Ohne Manifest würde die Anwendung die drei großen JSON-Dateien jedes Mal
    erneut in den Benutzerordner kopieren und den SQLite-Index invalidieren.
    """
    if not DICTIONARIES_ROOT.is_dir():
        raise RuntimeError(
            f"Wörterbuchordner fehlt: {DICTIONARIES_ROOT}"
        )

    dictionary_files = sorted(
        path for path in DICTIONARIES_ROOT.glob("*.json")
        if path.is_file() and path.name != "dictionary_manifest.json"
    )
    if not dictionary_files:
        raise RuntimeError(
            "Keine eingebetteten Wörterbuch-JSONs unter "
            "bottled_kraken/dictionaries gefunden."
        )

    manifest_files = {}
    for path in dictionary_files:
        size = int(path.stat().st_size)
        if size <= 0:
            raise RuntimeError(f"Leere Wörterbuchdatei erkannt: {path}")
        manifest_files[path.name] = {
            "size": size,
            "sha256": sha256_file(path),
        }
        datas.append((str(path), "bottled_kraken/dictionaries"))

    readme = DICTIONARIES_ROOT / "README.md"
    if readme.is_file():
        datas.append((str(readme), "bottled_kraken/dictionaries"))

    generated_dir = PROJECT_ROOT / "build" / "pyinstaller_generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = generated_dir / "dictionary_manifest.json"
    manifest_text = json.dumps(
        {"schema": 1, "files": manifest_files},
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    if not manifest_path.is_file() or manifest_path.read_text(encoding="utf-8") != manifest_text:
        manifest_path.write_text(manifest_text, encoding="utf-8")
    datas.append((str(manifest_path), "bottled_kraken/dictionaries"))

    total_size = sum(item["size"] for item in manifest_files.values())
    print(
        f"[main.spec] Wörterbücher geprüft: {len(dictionary_files)} JSON-Dateien, "
        f"{total_size / (1024 * 1024):.1f} MiB, SHA-256-Manifest erzeugt."
    )


def module_name_from_source(path, package_root=PACKAGE_ROOT, package_name="bottled_kraken"):
    """Leitet einen Importnamen direkt aus einer Python-Datei im Quellbaum ab."""
    path = Path(path)
    rel = path.relative_to(package_root)
    parts = list(rel.parts)
    if not parts or parts[-1].startswith("."):
        return ""
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    elif parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]
    else:
        return ""
    return ".".join([package_name, *parts]) if parts else package_name


def add_source_tree_hiddenimports(package_root=PACKAGE_ROOT):
    """Nimmt auch dynamisch geladene Bottled-Kraken-Module sicher in den Build auf."""
    if not package_root.is_dir():
        raise RuntimeError(f"Bottled-Kraken-Paketordner fehlt: {package_root}")
    for path in package_root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        module_name = module_name_from_source(path, package_root)
        if module_name:
            hiddenimports.append(module_name)


def discover_language_codes():
    """Ermittelt Sprachen ausschließlich aus den Sprachpaketen, ohne feste Codeliste."""
    if not TRANSLATIONS_ROOT.is_dir():
        raise RuntimeError(f"Übersetzungsordner fehlt: {TRANSLATIONS_ROOT}")
    codes = []
    for path in sorted(TRANSLATIONS_ROOT.iterdir()):
        if not path.is_dir() or path.name.startswith("_"):
            continue
        if (path / "__init__.py").is_file() and (path / "language_info.py").is_file():
            codes.append(path.name)
    if not codes:
        raise RuntimeError("Keine gültigen Sprachpakete unter bottled_kraken/translations gefunden.")
    return codes


def validate_i18n_sources():
    """Verhindert Builds mit fehlenden Sprachpaketen oder abweichenden Schlüsseln."""
    language_codes = discover_language_codes()
    try:
        from bottled_kraken.translations.language_registry import default_language_code
        from bottled_kraken.translations.translation_loader import load_all_language_translations

        translations = load_all_language_translations()
        reference_code = default_language_code()
        if reference_code not in translations:
            reference_code = language_codes[0]
        reference_keys = set(translations.get(reference_code, {}))
        if not reference_keys:
            raise RuntimeError(f"Referenzsprache '{reference_code}' enthält keine Übersetzungen.")

        problems = []
        for code in language_codes:
            mapping = translations.get(code, {})
            keys = set(mapping)
            missing = sorted(reference_keys - keys)
            extra = sorted(keys - reference_keys)
            if missing or extra:
                problems.append(
                    f"{code}: {len(missing)} fehlend, {len(extra)} zusätzlich"
                )
        if problems:
            raise RuntimeError(
                "Unvollständige Übersetzungen erkannt: " + "; ".join(problems)
            )
        print(
            f"[main.spec] i18n geprüft: {len(language_codes)} Sprachen, "
            f"je {len(reference_keys)} Schlüssel."
        )
    except Exception as exc:
        raise RuntimeError(f"i18n-Validierung für den PyInstaller-Build fehlgeschlagen: {exc}") from exc


# Früh und unabhängig von PyInstallers Importanalyse prüfen.
validate_i18n_sources()
add_source_tree_hiddenimports()

hiddenimports.extend([
    "bottled_kraken.windows_coremltools_stub",
    "coremltools",
    "coremltools.proto",
    "coremltools.proto.NeuralNetwork_pb2",
    "coremltools.proto.Model_pb2",
    "coremltools.proto.FeatureTypes_pb2",
    "coremltools.models",
    "coremltools.models.neural_network",
    "coremltools.models.neural_network.builder",
    "coremltools.models.neural_network.datatypes",
    "backports",
    "backports.tarfile",
    "setuptools._vendor.jaraco.context",
    "setuptools._vendor.backports",
    "setuptools._vendor.backports.tarfile",
])



# Projektdateien, die in der Windows-10/11-Ausgabe mitgeliefert werden sollen.
for file in (
    "icon.ico",
    "icon.png",
    "splash.png",
    "logo.png",
    "Bottled Kraken Programm v3.4.png",
    "README.md",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
    "Kurzhinweise - Bottled Kraken.txt",
    "WINDOWS_10_11_HINWEISE.txt",
    "ESCRIPTORIUM_NATIVE_INSTALLATION.md",
    "requirements.txt",
    "requirements-lock-windows.txt",
    "build_windows_10_11.ps1",
    "check_windows_10_11_build_environment.ps1",
):
    add_file(file, ".")

# Refactorisierte Bottled-Kraken-Struktur. Die Windows-kompatiblen
# Dialog- und Button-Ressourcen werden nur eingesammelt und nicht überschrieben.
for folder in (
    "bottled_kraken/_image_edit",
    "bottled_kraken/_main_window",
    "bottled_kraken/_ui_components",
    "bottled_kraken/_workers",
    "bottled_kraken/common",
    "bottled_kraken/pointer_features",
    "bottled_kraken/app_features",
    "bottled_kraken/tools",
    "bottled_kraken/translations",
):
    # Die .py-Dateien der Übersetzungen werden absichtlich zusätzlich als Daten
    # abgelegt. Dadurch kann pkgutil.iter_modules() die dynamisch erkannten
    # Sprach- und Abschnittsmodule auch im Onefile-Build zuverlässig auflisten.
    add_dir(folder, folder, "*.py", recursive=True)

# Dokumentation der Sprachpakete und alle eingebetteten Offline-Wörterbücher.
add_file("bottled_kraken/translations/README.md", "bottled_kraken/translations")
add_dictionary_bundle()

# Optionale Modell-/Resource-Ordner, falls sie im Projektordner vorhanden sind.
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

hiddenimports.extend([
    "bottled_kraken",
    "bottled_kraken.app",
    "bottled_kraken.version_config",
    "bottled_kraken.common",
    "bottled_kraken.translation",
    "bottled_kraken.ui_components",
    "bottled_kraken.dialogs",
    "bottled_kraken.image_edit",
    "bottled_kraken.workers",
    "bottled_kraken.main_window",
    "bottled_kraken.pointer_features",
    "bottled_kraken.app_features",
    "bottled_kraken._workers.backend_installer",
    "bottled_kraken._workers.external_backend_ocr",
    "bottled_kraken._workers.kraken_update_worker",
    "bottled_kraken.kraken_update",
    "bottled_kraken.runtime_cli",
    "bottled_kraken.whisper_runtime",
    "pyi_splash",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtSvg",
    "PySide6.QtNetwork",
    "PySide6.QtPrintSupport",
    "PIL.Image",
    "PIL.ImageQt",
    "PIL.ImageOps",
    "PIL.ImageEnhance",
    "PIL.PngImagePlugin",
    "PIL.JpegImagePlugin",
    "PIL.TiffImagePlugin",
    "PIL.WebPImagePlugin",
    "fitz",
    "pymupdf",
    "docx",
    "docx.document",
    "docx.oxml",
    "lxml",
    "lxml.etree",
    "lxml._elementpath",
    "kraken",
    "kraken.blla",
    "kraken.rpred",
    "kraken.serialization",
    "kraken.containers",
    "kraken.lib.models",
    "kraken.lib.vgsl",
    "kraken.lib.dataset",
    "kraken.lib.dataset.recognition",
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
    "ctranslate2",
    "faster_whisper",
    "faster_whisper.assets",
    "huggingface_hub",
    "transformers",
    "safetensors",
    "tokenizers",
])

# Viele Module werden in Bottled Kraken dynamisch über Runtime-Hooks/Registries
# aktiviert. Deshalb werden die aktuellen Submodule breit eingesammelt.
for _bk_pkg in (
    "bottled_kraken",
    "bottled_kraken.translations",
    "bottled_kraken._workers",
    "bottled_kraken.common",
    "bottled_kraken.pointer_features",
    "bottled_kraken.app_features",
    "bottled_kraken._main_window",
    "bottled_kraken._image_edit",
    "bottled_kraken._ui_components",
    "bottled_kraken.tools",
):
    hiddenimports.extend(safe_submodules(_bk_pkg))

add_pkg("PySide6", metadata="PySide6", data=False, libs=False)
add_pkg("shiboken6", metadata="shiboken6", data=False, libs=False)
add_pkg("PIL", metadata="Pillow", data=True)
add_pkg("numpy", metadata="numpy", libs=True)
add_pkg("fitz", metadata="PyMuPDF", data=True, libs=True)
add_pkg("pymupdf", metadata="PyMuPDF", data=True, libs=True)
add_pkg("pyarrow", metadata="pyarrow", data=True, libs=True)
add_pkg("docx", metadata="python-docx", data=True, submodules=True)
add_pkg("lxml", metadata="lxml", data=True, libs=True, submodules=True)
if not IS_WINDOWS:
    hiddenimports.extend([
        "coremltools",
        "coremltools.converters",
        "coremltools.models",
        "coremltools.proto",
        "coremltools.optimize",
    ])
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

for module, metadata, with_libs, with_submodules in (
    ("accelerate", "accelerate", False, False),
    ("whisper", "openai-whisper", False, False),
    ("tiktoken", "tiktoken", True, False),
    ("sounddevice", "sounddevice", False, False),
    ("cffi", "cffi", False, False),
    ("scipy", "scipy", True, False),
    ("skimage", "scikit-image", True, False),
    ("sklearn", "scikit-learn", True, False),
    ("shapely", "shapely", True, False),
    ("iso639", "iso639-lang", False, False),
    ("lightning", "lightning", False, False),
    ("pytorch_lightning", "pytorch-lightning", False, False),
):
    add_pkg(module, metadata=metadata, data=True, libs=with_libs, submodules=with_submodules)

if has_module("tiktoken_ext"):
    hiddenimports.extend(safe_submodules("tiktoken_ext"))

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
DROP_CONTAINS = (".tests.", ".test_", ".conftest")


def keep_hidden(name):
    if any(name == p or name.startswith(p + ".") for p in DROP_PREFIXES):
        return False
    if any(x in name for x in DROP_CONTAINS):
        return False
    return True


hiddenimports = sorted({h for h in hiddenimports if h and keep_hidden(h)})
datas = dedupe(datas)
binaries = dedupe(binaries)

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
        "AppKit",
        "Foundation",
        "objc",
        "pytest",
        "IPython",
        "jupyter",
        "notebook",
        "matplotlib",
        "tkinter",
        "tensorflow",
        "keras",
        "jax",
        "jaxlib",
        "flax",
        "paddle",
        "onnx",
        "cupy",
        "nvidia",
        "cuda_bindings",
        "triton",
        "torchaudio",
        "tensorboard",
        "torch.utils.tensorboard",
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
exe_args.extend([a.binaries, a.datas, []])

exe_kwargs = dict(
    name=APP_EXE_NAME,
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

if IS_WINDOWS and version_info is not None:
    exe_kwargs["version"] = version_info
    icon_path = PROJECT_ROOT / "icon.ico"
    if icon_path.is_file():
        exe_kwargs["icon"] = str(icon_path)

exe = EXE(*exe_args, **exe_kwargs)
