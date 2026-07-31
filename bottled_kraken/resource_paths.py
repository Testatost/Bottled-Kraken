from __future__ import annotations

import os
import sys


def resource_path(relative_path: str) -> str:
    """Resolve a bundled or source-tree resource path."""
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


__all__ = ["resource_path"]
