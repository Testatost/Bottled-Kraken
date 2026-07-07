from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Union

try:
    from bottled_kraken.version_config import APP_DIR_NAME
except Exception:  # pragma: no cover
    APP_DIR_NAME = "BottledKraken"

PathLikePart = Union[str, os.PathLike]


def bottled_kraken_user_root() -> Path:
    """Central writable root for all Bottled Kraken generated data.

    Default on Windows and Linux: <user home>/BottledKraken.
    Override with BOTTLED_KRAKEN_USER_DIR when a portable/custom location is required.
    """
    override = (
        os.environ.get("BOTTLED_KRAKEN_USER_DIR")
        or os.environ.get("BOTTLED_KRAKEN_DATA_DIR")
        or ""
    ).strip()
    root = Path(override).expanduser() if override else Path.home() / APP_DIR_NAME
    try:
        root.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return root


def bottled_kraken_user_path(*parts: PathLikePart, create: bool = True) -> Path:
    path = bottled_kraken_user_root().joinpath(*(str(part) for part in parts if str(part or "")))
    if create:
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
    return path


def bottled_kraken_runtime_path(*parts: PathLikePart, create: bool = True) -> Path:
    return bottled_kraken_user_path("runtime", *parts, create=create)


def safe_storage_name(value: str, fallback: str = "item", max_length: int = 80) -> str:
    text = str(value or "").strip()
    text = re.sub(r"[\\/:*?\"<>|\x00-\x1f]+", "_", text)
    text = re.sub(r"\s+", "_", text).strip("._-")
    if not text:
        text = fallback
    if len(text) > max_length:
        text = text[:max_length].rstrip("._-") or fallback
    return text


__all__ = [
    "bottled_kraken_user_root",
    "bottled_kraken_user_path",
    "bottled_kraken_runtime_path",
    "safe_storage_name",
]
