"""Language-independent cancellation detection.

Cancellation is primarily a state, not an error-message keyword.  This module
therefore checks worker state first and only falls back to exact comparisons
against every translated cancellation message shipped with the application.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Iterable, Sequence
import unicodedata

from bottled_kraken.translation import translation

DEFAULT_CANCELLATION_KEYS: tuple[str, ...] = (
    "msg_ai_cancelled",
    "msg_ai_cancelled_short",
    "msg_ai_single_cancelled",
    "msg_ai_multi_cancelled",
    "msg_ai_ocr_cancelled",
    "msg_local_json_cancelled",
    "msg_ocr_cancelled",
)

_WORKER_CANCEL_FLAGS: tuple[str, ...] = (
    "_bk_cancelled_by_user",
    "_cancelled",
    "cancelled",
    "_canceled",
    "canceled",
    "_cancel_requested",
    "cancel_requested",
    "_ocr_cancel_requested",
    "_stop_requested",
    "stop_requested",
    "_abort",
    "abort",
)


def _normalize_message(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or ""))
    return " ".join(text.strip().casefold().split())


def worker_was_cancelled(worker: object | None) -> bool:
    """Return ``True`` when a worker exposes an active cancellation state."""
    if worker is None:
        return False

    for name in _WORKER_CANCEL_FLAGS:
        try:
            if bool(getattr(worker, name, False)):
                return True
        except Exception:
            continue

    for method_name in ("isInterruptionRequested", "is_cancelled", "isCancelled"):
        try:
            method = getattr(worker, method_name, None)
            if callable(method) and bool(method()):
                return True
        except Exception:
            continue
    return False


@lru_cache(maxsize=64)
def translated_cancellation_messages(keys: tuple[str, ...]) -> frozenset[str]:
    """Return normalized cancellation strings for all installed UI languages."""
    messages: set[str] = set()
    for lang in translation.available_languages():
        for key in keys:
            try:
                candidate = _normalize_message(translation.translate(lang, key))
            except Exception:
                candidate = ""
            if candidate and candidate != _normalize_message(key):
                messages.add(candidate)
    return frozenset(messages)


def message_is_cancellation(
    message: object,
    keys: Sequence[str] = DEFAULT_CANCELLATION_KEYS,
) -> bool:
    """Match exactly against cancellation translations in all languages.

    Normalization is limited to Unicode compatibility, case folding and
    whitespace.  Prefixes, suffixes and wrapped context are intentionally not
    accepted.  Callers that decorate an exception message must therefore keep
    the structural worker-state check or pass the original cancellation text.
    """
    normalized = _normalize_message(message)
    if not normalized:
        return False
    normalized_keys = tuple(dict.fromkeys(str(key) for key in keys if key))
    return normalized in translated_cancellation_messages(normalized_keys)


def operation_was_cancelled(
    *,
    worker: object | None = None,
    workers: Iterable[object | None] = (),
    message: object = "",
    keys: Sequence[str] = DEFAULT_CANCELLATION_KEYS,
) -> bool:
    """Detect cancellation from worker state, then from translated messages."""
    if worker_was_cancelled(worker):
        return True
    for candidate in workers:
        if worker_was_cancelled(candidate):
            return True
    return message_is_cancellation(message, keys)


__all__ = [
    "DEFAULT_CANCELLATION_KEYS",
    "message_is_cancellation",
    "operation_was_cancelled",
    "translated_cancellation_messages",
    "worker_was_cancelled",
]
