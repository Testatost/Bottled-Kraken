from __future__ import annotations

import ast as _ast
import json as _json
import os as _os
import sys as _sys
from datetime import datetime as _datetime, timezone as _timezone
from pathlib import Path as _Path
from typing import Any

_DEBUG_COLLISIONS = str(_os.environ.get("BK_DEBUG_REGISTRY", "")).strip().lower() in {"1", "true", "yes", "on"}

_REGISTRIES: dict[str, dict[str, Any]] = {}


def _registry(name: str) -> dict[str, Any]:
    """Return the mutable compatibility registry for one injection group."""
    return _REGISTRIES.setdefault(
        name,
        {"symbols": {}, "modules": [], "owners": {}, "collisions": []},
    )


def seed_globals(group: str, namespace: dict[str, Any]) -> None:
    """Seed a legacy module namespace with the group's current symbol snapshot."""
    namespace.update(_registry(group)["symbols"])


def _record_symbol(group: str, namespace: dict[str, Any], name: str, value: Any) -> None:
    reg = _registry(group)
    symbols = reg["symbols"]
    owners = reg["owners"]
    owner = str(namespace.get("__name__", "?") or "?")
    if name in symbols and symbols[name] is value:
        # Re-exporting an injected symbol must not steal ownership from the
        # module that actually defined it.
        return
    if name in symbols:
        previous_owner = owners.get(name, "?")
        reg["collisions"].append((name, previous_owner, owner))
        if _DEBUG_COLLISIONS:
            print(
                f"[bk-registry] '{group}:{name}' überschrieben: "
                f"{previous_owner} -> {owner}",
                file=_sys.stderr,
            )
    symbols[name] = value
    owners[name] = owner


def register_globals(group: str, namespace: dict[str, Any], names) -> None:
    """Register selected names and retain their source-module lineage."""
    reg = _registry(group)
    for name in names:
        if name in namespace:
            _record_symbol(group, namespace, name, namespace[name])
    if not any(existing is namespace for existing in reg["modules"]):
        reg["modules"].append(namespace)


def seed_from_module(group: str, module: Any) -> None:
    """Register a module's explicit exports as initial symbols for a group."""
    names = getattr(module, "__all__", None)
    if names is None:
        names = [name for name in vars(module) if not name.startswith("__")]
    namespace = vars(module)
    for name in names:
        if hasattr(module, name):
            _record_symbol(group, namespace, name, getattr(module, name))


def synchronize(group: str) -> None:
    """Update all registered legacy namespaces with the final symbol mapping."""
    reg = _registry(group)
    symbols = reg["symbols"]
    for namespace in reg["modules"]:
        namespace.update(symbols)


def registry_collisions(group: str | None = None) -> tuple[tuple[str, str, str, str], ...]:
    """Return immutable collision records for diagnostics and release audits."""
    groups = (group,) if group is not None else tuple(sorted(_REGISTRIES))
    rows: list[tuple[str, str, str, str]] = []
    for group_name in groups:
        for name, previous_owner, owner in _registry(group_name)["collisions"]:
            rows.append((group_name, name, previous_owner, owner))
    return tuple(rows)



def mainwindow_binding_writes(main_window_cls: Any) -> tuple[dict[str, Any], ...]:
    """Inspect loaded feature modules for ``MainWindow.<name> = ...`` writes.

    The scan uses the modules that were actually absorbed into a compatibility
    registry during this process.  The source location is static metadata, but
    the right-hand side and the active-binding flag are resolved against the
    live module namespaces and the live ``MainWindow`` class.  This makes the
    result suitable for one-shot runtime audits without changing the Qt class
    metaclass or wrapping every historical assignment.
    """
    seen_files: set[str] = set()
    rows: list[dict[str, Any]] = []
    missing = object()
    for registry in _REGISTRIES.values():
        for namespace in registry.get("modules", ()):  # pragma: no branch - tiny loop
            source_path = str(namespace.get("__file__", "") or "")
            module_name = str(namespace.get("__name__", "?") or "?")
            if not source_path or source_path in seen_files:
                continue
            seen_files.add(source_path)
            try:
                source = _Path(source_path).read_text(encoding="utf-8")
                tree = _ast.parse(source, filename=source_path)
            except Exception:
                continue
            for node in _ast.walk(tree):
                if not isinstance(node, (_ast.Assign, _ast.AnnAssign)):
                    continue
                targets = node.targets if isinstance(node, _ast.Assign) else [node.target]
                value_node = node.value
                for target in targets:
                    if not (
                        isinstance(target, _ast.Attribute)
                        and isinstance(target.value, _ast.Name)
                        and target.value.id == "MainWindow"
                    ):
                        continue
                    rhs = _ast.unparse(value_node) if value_node is not None else ""
                    value = missing
                    if isinstance(value_node, _ast.Name):
                        value = namespace.get(value_node.id, missing)
                    active_value = getattr(main_window_cls, target.attr, missing)
                    rows.append(
                        {
                            "attribute": target.attr,
                            "module": module_name,
                            "source": source_path,
                            "line": int(getattr(node, "lineno", 0) or 0),
                            "rhs": rhs,
                            "active": value is not missing and active_value is value,
                        }
                    )
    rows.sort(key=lambda row: (row["attribute"], row["source"], row["line"]))
    return tuple(rows)


def write_registry_diagnostics(path: str | _os.PathLike[str], main_window_cls: Any) -> str:
    """Write collision and repeated-``MainWindow`` binding data as JSON."""
    destination = _Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    bindings = mainwindow_binding_writes(main_window_cls)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in bindings:
        grouped.setdefault(str(row["attribute"]), []).append(row)
    repeated = {
        name: rows
        for name, rows in sorted(grouped.items())
        if len(rows) > 1
    }
    payload = {
        "generated_at_utc": _datetime.now(_timezone.utc).isoformat(),
        "registry_collisions": [
            {
                "group": group,
                "symbol": symbol,
                "previous_owner": previous_owner,
                "owner": owner,
            }
            for group, symbol, previous_owner, owner in registry_collisions()
        ],
        "multiple_mainwindow_bindings": repeated,
    }
    destination.write_text(
        _json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return str(destination)

def registry_symbol_source(group: str, name: str) -> str | None:
    """Return the module that currently owns a registered symbol."""
    return _registry(group)["owners"].get(name)


__all__ = [
    "mainwindow_binding_writes",
    "register_globals",
    "registry_collisions",
    "registry_symbol_source",
    "seed_from_module",
    "seed_globals",
    "synchronize",
    "write_registry_diagnostics",
]
