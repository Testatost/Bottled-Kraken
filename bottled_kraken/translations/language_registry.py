from __future__ import annotations

import pkgutil
from functools import lru_cache
from importlib import import_module
from typing import Any, Dict, List

_RESERVED_PACKAGES = {"patches", "__pycache__"}


def _package_name() -> str:
    return __package__ or "bottled_kraken.translations"


@lru_cache(maxsize=1)
def _discovered_language_info() -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    package_name = _package_name()
    try:
        package = import_module(package_name)
        package_path = getattr(package, "__path__", None)
        candidates = (
            item.name
            for item in pkgutil.iter_modules(package_path or [])
            if item.ispkg
            and not item.name.startswith("_")
            and item.name not in _RESERVED_PACKAGES
        )
    except Exception:
        candidates = ()

    for code in sorted(set(candidates)):
        try:
            module = import_module(f"{package_name}.{code}.language_info")
        except Exception:
            continue
        metadata = {
            "code": str(getattr(module, "LANGUAGE_CODE", code)).strip() or code,
            "native_name": str(getattr(module, "NATIVE_NAME", code)),
            "english_name": str(getattr(module, "ENGLISH_NAME", code)),
            "qt_locale": str(getattr(module, "QT_LOCALE", code)),
            "is_default": bool(getattr(module, "IS_DEFAULT", False)),
        }
        # The directory name is the import key. LANGUAGE_CODE is descriptive metadata.
        metadata["code"] = code
        result[code] = metadata
    return result


def available_language_codes() -> List[str]:
    data = _discovered_language_info()
    codes = sorted(data)
    default = default_language_code()
    if default in codes:
        codes.remove(default)
        codes.insert(0, default)
    return codes


def default_language_code() -> str:
    data = _discovered_language_info()
    marked = [code for code, info in data.items() if info.get("is_default")]
    if marked:
        return sorted(marked)[0]
    return sorted(data)[0] if data else ""


def normalize_language_code(code: object, default: str | None = None) -> str:
    available = available_language_codes()
    if not available:
        return ""
    fallback = default if default in available else default_language_code()
    raw = str(code or "").strip().lower().replace("-", "_")
    if raw in available:
        return raw
    short = raw.split("_", 1)[0]
    if short in available:
        return short
    for candidate in available:
        if raw.startswith(candidate.lower() + "_"):
            return candidate
    return fallback if fallback in available else available[0]


def language_info(code: str) -> Dict[str, Any]:
    data = _discovered_language_info()
    normalized = normalize_language_code(code)
    return dict(data.get(normalized, {
        "code": normalized,
        "native_name": normalized,
        "english_name": normalized,
        "qt_locale": normalized,
        "is_default": False,
    }))


DEFAULT_LANGUAGE = default_language_code()
# English is the stable UI fallback for newly introduced translation keys.
FALLBACK_LANGUAGES: tuple[str, ...] = ("en",) if "en" in available_language_codes() else ()

__all__ = [
    "DEFAULT_LANGUAGE",
    "FALLBACK_LANGUAGES",
    "available_language_codes",
    "default_language_code",
    "normalize_language_code",
    "language_info",
]
