"""Static source-quality guardrails for Bottled Kraken.

The project still contains legacy modules with ``from ... import *``.  New modules
should not add more of those imports.  Tests compare the current legacy baseline
against these policy values and fail on newly introduced wildcard imports.
"""

from __future__ import annotations

LEGACY_STAR_IMPORT_BASELINE_MAX = 265

VISIBLE_TEXT_TRANSLATION_REQUIRED = True

EXTERNAL_WORKER_RUNTIME_MODULE = "bottled_kraken/worker_threads/external_backend_worker_runtime.py"

LM_SANITY_DOMAIN_PARTS = (
    "ditto_guard.py",
    "lm_revision_merge_modes.py",
)
