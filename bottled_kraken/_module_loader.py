"""Hilfsfunktionen zum Laden ausgelagerter Modul-Teile.

Dieses Projekt legt sehr große Module in nummerierte Dateien unterhalb von
z. B. ``_shared_parts`` oder ``_bk_features_parts`` ab. ``load_split_module``
führt diese Dateien der Reihe nach im Namespace des aufrufenden Moduls aus.
Dadurch funktionieren relative Imports wie ``from .shared import *`` weiterhin
so, als stünde der Code direkt in ``shared.py``/``bk_features.py``.
"""

from __future__ import annotations

import os
from pathlib import Path
from types import ModuleType
from typing import MutableMapping, Any


def load_split_module(module_file: str, module_globals: MutableMapping[str, Any], parts_dir_name: str) -> None:
    """Lädt alle ``*.py``-Dateien eines Split-Ordners sortiert in ``module_globals``.

    Args:
        module_file: ``__file__`` des Wrapper-Moduls, z. B. ``shared.py``.
        module_globals: ``globals()`` des Wrapper-Moduls.
        parts_dir_name: Name des Unterordners mit den Teilmodulen.
    """
    base_dir = Path(module_file).resolve().parent
    parts_dir = base_dir / parts_dir_name

    if not parts_dir.is_dir():
        raise ImportError(f"Split-Modul-Ordner nicht gefunden: {parts_dir}")

    part_files = sorted(
        p for p in parts_dir.glob("*.py")
        if p.name != "__init__.py" and not p.name.startswith(".")
    )

    old_file = module_globals.get("__file__")
    module_globals.setdefault("__package__", __package__)

    for part_file in part_files:
        source = part_file.read_text(encoding="utf-8")
        code = compile(source, str(part_file), "exec")
        module_globals["__file__"] = str(part_file)
        exec(code, module_globals)

    if old_file is not None:
        module_globals["__file__"] = old_file
