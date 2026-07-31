from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable


def application_cli_command(arguments: Iterable[str]) -> list[str]:
    """Return a command that starts Bottled Kraken in an internal CLI mode."""
    args = [str(item) for item in arguments]
    if getattr(sys, "frozen", False):
        return [sys.executable, *args]
    main_script = Path(__file__).resolve().parent.parent / "main.py"
    return [sys.executable, str(main_script), *args]


def hidden_process_kwargs() -> dict:
    """Return platform-specific subprocess flags that avoid console windows."""
    kwargs: dict = {}
    if os.name == "nt":
        creationflags = int(getattr(__import__("subprocess"), "CREATE_NO_WINDOW", 0))
        if creationflags:
            kwargs["creationflags"] = creationflags
    return kwargs


__all__ = ["application_cli_command", "hidden_process_kwargs"]
