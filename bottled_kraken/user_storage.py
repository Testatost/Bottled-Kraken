from __future__ import annotations

import os
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Union

try:
    from bottled_kraken.version_config import APP_DIR_NAME
except Exception:  # pragma: no cover
    APP_DIR_NAME = "BottledKraken"

PathLikePart = Union[str, os.PathLike]

_WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


def _default_user_root(
    *,
    os_name: str | None = None,
    platform_name: str | None = None,
    home: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> Path:
    """Return the platform-standard per-user application data directory."""
    current_os_name = os.name if os_name is None else os_name
    current_platform = sys.platform if platform_name is None else platform_name
    current_home = Path.home() if home is None else Path(home)
    current_environ = os.environ if environ is None else environ
    if current_os_name == "nt":
        base = current_environ.get("LOCALAPPDATA") or current_environ.get("APPDATA")
        return (Path(base).expanduser() if base else current_home / "AppData" / "Local") / APP_DIR_NAME
    if current_platform == "darwin":
        return current_home / "Library" / "Application Support" / APP_DIR_NAME
    xdg_data_home = str(current_environ.get("XDG_DATA_HOME", "") or "").strip()
    base = Path(xdg_data_home).expanduser() if xdg_data_home else current_home / ".local" / "share"
    return base / APP_DIR_NAME


def _legacy_user_root(home: Path | None = None) -> Path:
    """Return the pre-3.4 application-data location used by beta builds."""
    return (Path.home() if home is None else Path(home)) / APP_DIR_NAME


def _select_compatible_user_root(default_root: Path, legacy_root: Path) -> Path:
    """Keep an existing beta data directory usable without copying user data."""
    try:
        if default_root.resolve(strict=False) == legacy_root.resolve(strict=False):
            return default_root
    except OSError:
        pass
    if not default_root.exists() and legacy_root.is_dir():
        return legacy_root
    return default_root


def bottled_kraken_user_root() -> Path:
    """Return the central writable root for generated application data.

    Fresh installations follow platform conventions. Existing beta data under
    ``~/BottledKraken`` remains usable until it is migrated manually.
    ``BOTTLED_KRAKEN_USER_DIR`` and the legacy
    ``BOTTLED_KRAKEN_DATA_DIR`` override both locations.
    """
    override = (
        os.environ.get("BOTTLED_KRAKEN_USER_DIR")
        or os.environ.get("BOTTLED_KRAKEN_DATA_DIR")
        or ""
    ).strip()
    if override:
        root = Path(override).expanduser()
    else:
        root = _select_compatible_user_root(_default_user_root(), _legacy_user_root())
    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return root


def _safe_relative_parts(parts: tuple[PathLikePart, ...]) -> list[str]:
    """Validate that application subpaths cannot escape the user-data root."""
    result: list[str] = []
    for part in parts:
        raw = str(part or "").strip()
        if not raw:
            continue
        candidate = Path(raw)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError(f"Unsafe Bottled Kraken storage path component: {raw!r}")
        result.append(raw)
    return result


def bottled_kraken_user_path(*parts: PathLikePart, create: bool = True) -> Path:
    """Return a path below the platform-standard Bottled Kraken data root."""
    path = bottled_kraken_user_root().joinpath(*_safe_relative_parts(parts))
    if create:
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
    return path


def bottled_kraken_runtime_path(*parts: PathLikePart, create: bool = True) -> Path:
    """Return a path below the application's runtime-data directory."""
    return bottled_kraken_user_path("runtime", *parts, create=create)


def _is_windows_reserved_name(value: str) -> bool:
    stem = str(value or "").split(".", 1)[0].rstrip(" .").upper()
    return stem in _WINDOWS_RESERVED_NAMES


def safe_storage_name(value: str, fallback: str = "item", max_length: int = 80) -> str:
    """Convert arbitrary OCR/user text into a portable filename component.

    The result avoids control characters, path separators, trailing dots and
    spaces, and Windows device names such as ``CON`` or ``LPT1``.
    """
    max_length = max(1, int(max_length or 1))

    def clean(raw: object) -> str:
        text = str(raw or "").strip()
        text = re.sub(r'[\\/:*?"<>|\x00-\x1f]+', '_', text)
        return re.sub(r"\s+", "_", text).strip("._- ")

    text = clean(value) or clean(fallback) or "item"
    if _is_windows_reserved_name(text):
        text = f"_{text}"
    text = text[:max_length].rstrip(". ")
    if not text:
        text = "_" if max_length == 1 else (clean(fallback) or "item")[:max_length].rstrip(". ")
    if _is_windows_reserved_name(text):
        text = "_" if max_length == 1 else ("_" + text)[:max_length].rstrip(". ")
    return text[:max_length] or "_"


__all__ = [
    "bottled_kraken_user_root",
    "bottled_kraken_user_path",
    "bottled_kraken_runtime_path",
    "safe_storage_name",
]
