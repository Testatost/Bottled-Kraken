"""Compatibility alias for PyInstaller/v3.2-style package layout."""
from importlib import import_module as _import_module

_target = _import_module('bottled_kraken.main_window')
for _name, _value in vars(_target).items():
    if not _name.startswith("_"):
        globals()[_name] = _value
__all__ = [name for name in globals() if not name.startswith("_")]
