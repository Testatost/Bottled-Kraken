"""Hilfsfunktionen zum Laden ausgelagerter Modulgruppen.

Der Loader unterstuetzt zwei Laufzeitformen:
1. Quellcode/onedir: Split-Parts liegen als echte .py-Dateien neben dem Wrapper.
2. PyInstaller-OneFile: Split-Parts liegen nur als importierbare Module im PYZ-Archiv.

In beiden Faellen werden die Parts im Namespace des oeffentlichen Wrapper-Moduls
exec()'t. Das ist wichtig, weil die historische v3.2-Splitstruktur darauf
beruht, dass spaetere Parts Namen aus frueheren Parts direkt im selben globalen
Namespace sehen koennen.
"""

from __future__ import annotations

import importlib
import importlib.util
import pkgutil
from pathlib import Path
from typing import Any, MutableMapping


def _read_manifest(parts_dir: Path) -> list[Path] | None:
    manifest = parts_dir / "_parts_order.py"
    if not manifest.is_file():
        return None
    namespace: dict[str, Any] = {}
    exec(compile(manifest.read_text(encoding="utf-8"), str(manifest), "exec"), namespace)
    names = namespace.get("PARTS")
    if not isinstance(names, (list, tuple)):
        raise ImportError(f"Ungueltige PARTS-Liste in {manifest}")
    files = [parts_dir / str(name) for name in names]
    missing = [str(path) for path in files if not path.is_file()]
    if missing:
        raise ImportError("In _parts_order.py referenzierte Dateien fehlen: " + ", ".join(missing))
    return files


def _package_from_module_file(module_file: str, parts_dir_name: str, module_globals: MutableMapping[str, Any]) -> str:
    """Bestimmt das Part-Package auch fuer verschachtelte Split-Loader.

    Beispiele:
      bottled_kraken/shared.py + _shared_parts
        -> bottled_kraken._shared_parts
      bottled_kraken/_bk_features_parts/canonical_graph_dialog.py + canonical_graph_dialog_parts
        -> bottled_kraken._bk_features_parts.canonical_graph_dialog_parts
    """
    try:
        p = Path(str(module_file)).resolve()
        parts = list(p.parts)
        if "bottled_kraken" in parts:
            i = len(parts) - 1 - parts[::-1].index("bottled_kraken")
            parent_pkg_parts = parts[i:-1]
            return ".".join(parent_pkg_parts + [parts_dir_name])
    except Exception:
        pass

    package_name = str(module_globals.get("__package__") or "").strip()
    if not package_name:
        module_name = str(module_globals.get("__name__") or "")
        package_name = module_name.rsplit(".", 1)[0] if "." in module_name else module_name
    if not package_name:
        raise ImportError(f"Split-Modul-Paket fuer {parts_dir_name!r} konnte nicht bestimmt werden.")
    return f"{package_name}.{parts_dir_name}"


def _part_module_names(parts_package: str) -> list[str]:
    try:
        manifest = importlib.import_module(f"{parts_package}._parts_order")
        names = getattr(manifest, "PARTS")
        if isinstance(names, (list, tuple)):
            return [str(name).removesuffix(".py") for name in names]
    except Exception:
        pass

    package = importlib.import_module(parts_package)
    if not hasattr(package, "__path__"):
        raise ImportError(f"Split-Modul-Paket ist nicht iterierbar: {parts_package}")
    names: list[str] = []
    for info in pkgutil.iter_modules(package.__path__):
        name = info.name
        if name not in {"__init__", "_parts_order"} and not name.startswith("."):
            names.append(name)
    return sorted(names)


def _exec_part_module(fullname: str, module_globals: MutableMapping[str, Any]) -> None:
    spec = importlib.util.find_spec(fullname)
    if spec is None or spec.loader is None:
        # letzte Rueckfallebene: normal importieren und oeffentliche Namen spiegeln
        module = importlib.import_module(fullname)
        exported = getattr(module, "__all__", None)
        names = [str(n) for n in exported] if isinstance(exported, (list, tuple, set)) else [n for n in vars(module) if not n.startswith("__")]
        for name in names:
            if hasattr(module, name):
                module_globals[name] = getattr(module, name)
        return

    get_code = getattr(spec.loader, "get_code", None)
    code = get_code(fullname) if callable(get_code) else None
    if code is None:
        get_source = getattr(spec.loader, "get_source", None)
        source = get_source(fullname) if callable(get_source) else None
        if source is None:
            module = importlib.import_module(fullname)
            exported = getattr(module, "__all__", None)
            names = [str(n) for n in exported] if isinstance(exported, (list, tuple, set)) else [n for n in vars(module) if not n.startswith("__")]
            for name in names:
                if hasattr(module, name):
                    module_globals[name] = getattr(module, name)
            return
        code = compile(source, spec.origin or fullname, "exec")

    old_file = module_globals.get("__file__")
    old_name = module_globals.get("__name__")
    old_package = module_globals.get("__package__")
    try:
        module_globals["__file__"] = spec.origin or fullname
        # Der Wrapper bleibt das aktive Modul; __package__ muss fuer relative Imports wie .shared erhalten bleiben.
        exec(code, module_globals)
    finally:
        if old_file is not None:
            module_globals["__file__"] = old_file
        elif "__file__" in module_globals:
            module_globals.pop("__file__", None)
        if old_name is not None:
            module_globals["__name__"] = old_name
        if old_package is not None:
            module_globals["__package__"] = old_package


def _load_split_module_by_import(module_file: str, module_globals: MutableMapping[str, Any], parts_dir_name: str) -> None:
    parts_package = _package_from_module_file(module_file, parts_dir_name, module_globals)
    for part_name in _part_module_names(parts_package):
        _exec_part_module(f"{parts_package}.{part_name}", module_globals)


def load_split_module(module_file: str, module_globals: MutableMapping[str, Any], parts_dir_name: str) -> None:
    """Laedt ausgelagerte Moduldateien in ``module_globals``."""
    base_dir = Path(module_file).resolve().parent
    parts_dir = base_dir / parts_dir_name

    if not parts_dir.is_dir():
        _load_split_module_by_import(module_file, module_globals, parts_dir_name)
        return

    part_files = _read_manifest(parts_dir)
    if part_files is None:
        part_files = sorted(
            p for p in parts_dir.glob("*.py")
            if p.name not in {"__init__.py", "_parts_order.py"} and not p.name.startswith(".")
        )

    old_file = module_globals.get("__file__")
    old_name = module_globals.get("__name__")
    old_package = module_globals.get("__package__")
    for part_file in part_files:
        source = part_file.read_text(encoding="utf-8")
        code = compile(source, str(part_file), "exec")
        module_globals["__file__"] = str(part_file)
        exec(code, module_globals)

    if old_file is not None:
        module_globals["__file__"] = old_file
    if old_name is not None:
        module_globals["__name__"] = old_name
    if old_package is not None:
        module_globals["__package__"] = old_package
