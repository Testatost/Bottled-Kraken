from __future__ import annotations
from importlib import resources
def _load_external_kraken_worker_source() -> str:
    try:
        return (
            resources.files(__package__)
            .joinpath("external_backend_worker_runtime.py")
            .read_text(encoding="utf-8")
        )
    except Exception:
        return (
            "#!/usr/bin/env python3\n"
            "# -*- coding: utf-8 -*-\n"
            "import json, sys\n"
            "print(json.dumps({"
            "'ok': False, 'error': 'external_backend_worker_runtime.py fehlt'"
            "}, ensure_ascii=False), flush=True)\n"
            "sys.exit(2)\n"
        )
EXTERNAL_KRAKEN_WORKER_SOURCE = _load_external_kraken_worker_source()
