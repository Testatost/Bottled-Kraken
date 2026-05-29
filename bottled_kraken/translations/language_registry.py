from __future__ import annotations
import pkgutil
from importlib import import_module
from typing import Dict, List
DEFAULT_LANGUAGE = "de"
FALLBACK_LANGUAGES = (DEFAULT_LANGUAGE, "en")
KNOWN_LANGUAGE_CODES = ("de", "en", "fr")
_RESERVED_PACKAGES = {"patches", "__pycache__"}
def available_language_codes() -> List[str]:
    codes: list[str] = []
    package_name = __package__ or "bottled_kraken.translations"
    try:
        package = import_module(package_name)
        package_path = getattr(package, "__path__", None)
        if package_path is not None:
            for item in pkgutil.iter_modules(package_path):
                name = item.name
                if item.ispkg and not name.startswith("_") and name not in _RESERVED_PACKAGES:
                    codes.append(name)
    except Exception:
        codes = []
    if not codes:
        for code in KNOWN_LANGUAGE_CODES:
            try:
                import_module(f"{package_name}.{code}")
            except Exception:
                continue
            codes.append(code)
    codes = sorted(dict.fromkeys(codes))
    if DEFAULT_LANGUAGE in codes:
        codes.remove(DEFAULT_LANGUAGE)
        codes.insert(0, DEFAULT_LANGUAGE)
    return codes
def normalize_language_code(code: object, default: str = DEFAULT_LANGUAGE) -> str:
    available = available_language_codes()
    if not available:
        return default
    raw = str(code or "").strip().lower().replace("-", "_")
    if raw in available:
        return raw
    short = raw.split("_", 1)[0]
    if short in available:
        return short
    for candidate in available:
        if raw.startswith(candidate.lower() + "_"):
            return candidate
    return default if default in available else available[0]
def language_info(code: str) -> Dict[str, str]:
    code = normalize_language_code(code, default=str(code or DEFAULT_LANGUAGE))
    info = {"code": code, "native_name": code, "english_name": code}
    try:
        module = import_module(f"{__package__}.{code}.language_info")
    except Exception:
        return info
    native_name = getattr(module, "NATIVE_NAME", None)
    english_name = getattr(module, "ENGLISH_NAME", None)
    if native_name:
        info["native_name"] = str(native_name)
    if english_name:
        info["english_name"] = str(english_name)
    return info
__all__ = [
    "DEFAULT_LANGUAGE",
    "FALLBACK_LANGUAGES",
    "KNOWN_LANGUAGE_CODES",
    "available_language_codes",
    "normalize_language_code",
    "language_info",
]
