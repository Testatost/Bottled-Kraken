"""Persistent application logging and process-wide exception hooks."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sys
import tempfile
import threading
import traceback
import uuid
from typing import Callable

from bottled_kraken.user_storage import bottled_kraken_user_path

LOGGER_NAME = "bottled_kraken"
LOG_FILE_NAME = "bottled_kraken.log"
MAX_LOG_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 5

_configure_lock = threading.RLock()
_configured_path: Path | None = None
_dialog_callback: Callable[[type[BaseException], BaseException, str, str], None] | None = None
_hooks_installed = False
_handling_exception = threading.local()


def _resolve_log_dir() -> Path:
    override = os.environ.get("BOTTLED_KRAKEN_LOG_DIR", "").strip()
    target = Path(override).expanduser() if override else bottled_kraken_user_path("logs")
    try:
        target.mkdir(parents=True, exist_ok=True)
        return target
    except Exception:
        fallback = Path.cwd() / "BottledKraken-logs"
        try:
            fallback.mkdir(parents=True, exist_ok=True)
            return fallback
        except Exception:
            final_fallback = Path(tempfile.gettempdir()) / "BottledKraken-logs"
            final_fallback.mkdir(parents=True, exist_ok=True)
            return final_fallback


def configure_logging(level: int | str | None = None) -> logging.Logger:
    """Configure one rotating UTF-8 log file and return the app logger."""
    global _configured_path
    with _configure_lock:
        logger = logging.getLogger(LOGGER_NAME)
        resolved_level = level or os.environ.get("BOTTLED_KRAKEN_LOG_LEVEL", "INFO")
        try:
            logger.setLevel(resolved_level)
        except (TypeError, ValueError):
            logger.setLevel(logging.INFO)
        logger.propagate = False

        log_path = (_resolve_log_dir() / LOG_FILE_NAME).resolve()
        existing = next(
            (
                handler
                for handler in logger.handlers
                if isinstance(handler, RotatingFileHandler)
                and Path(getattr(handler, "baseFilename", "")) == log_path
            ),
            None,
        )
        if existing is None:
            handler = RotatingFileHandler(
                log_path,
                maxBytes=MAX_LOG_BYTES,
                backupCount=LOG_BACKUP_COUNT,
                encoding="utf-8",
                delay=True,
            )
            handler.setLevel(logging.DEBUG)
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s | %(levelname)-8s | %(threadName)s | "
                    "%(name)s | %(message)s"
                )
            )
            handler._bottled_kraken_handler = True  # type: ignore[attr-defined]
            logger.addHandler(handler)

        if os.environ.get("BOTTLED_KRAKEN_CONSOLE_LOG", "").strip() == "1":
            if not any(getattr(h, "_bottled_kraken_console", False) for h in logger.handlers):
                console = logging.StreamHandler(sys.stderr)
                console.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
                console._bottled_kraken_console = True  # type: ignore[attr-defined]
                logger.addHandler(console)

        _configured_path = log_path
        return logger


def get_logger(component: str | None = None) -> logging.Logger:
    configure_logging()
    if component:
        return logging.getLogger(f"{LOGGER_NAME}.{component}")
    return logging.getLogger(LOGGER_NAME)


def log_file_path() -> str:
    configure_logging()
    return str(_configured_path or (_resolve_log_dir() / LOG_FILE_NAME).resolve())


def log_suppressed_exception(context: str, *, level: int = logging.WARNING) -> None:
    """Record an exception that is intentionally swallowed by compatibility code."""
    get_logger("suppressed").log(level, "Suppressed exception in %s", context, exc_info=True)


def _new_error_id() -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{uuid.uuid4().hex[:8]}"


def _report_exception(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_tb,
    *,
    origin: str,
) -> None:
    if exc_type is KeyboardInterrupt or issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return

    if getattr(_handling_exception, "active", False):
        traceback.print_exception(exc_type, exc_value, exc_tb, file=sys.stderr)
        return

    _handling_exception.active = True
    try:
        error_id = _new_error_id()
        get_logger("exceptions").critical(
            "Unhandled exception [%s] in %s",
            error_id,
            origin,
            exc_info=(exc_type, exc_value, exc_tb),
        )
        callback = _dialog_callback
        # GUI dialogs may only be created on the main thread. Exceptions from
        # Python worker threads are still fully recorded by threading.excepthook.
        if callback is not None and threading.current_thread() is threading.main_thread():
            try:
                callback(exc_type, exc_value, error_id, log_file_path())
                return
            except Exception:
                get_logger("exceptions").exception(
                    "Could not display the exception dialog for error %s", error_id
                )
        print(
            f"Bottled Kraken error {error_id}: {exc_type.__name__}: {exc_value}\n"
            f"Log: {log_file_path()}",
            file=sys.stderr,
        )
    finally:
        _handling_exception.active = False


def install_exception_hooks(
    dialog_callback: Callable[[type[BaseException], BaseException, str, str], None] | None = None,
) -> None:
    """Install hooks for main-thread, Python-thread and unraisable exceptions."""
    global _dialog_callback, _hooks_installed
    configure_logging()
    if dialog_callback is not None:
        _dialog_callback = dialog_callback
    if _hooks_installed:
        return

    def sys_hook(exc_type, exc_value, exc_tb):
        _report_exception(exc_type, exc_value, exc_tb, origin="main thread")

    def thread_hook(args: threading.ExceptHookArgs):
        thread_name = getattr(args.thread, "name", "unknown thread")
        _report_exception(
            args.exc_type,
            args.exc_value,
            args.exc_traceback,
            origin=f"thread {thread_name}",
        )

    def unraisable_hook(args):
        exc_type = args.exc_type or RuntimeError
        exc_value = args.exc_value or RuntimeError(str(args.err_msg or "unraisable exception"))
        _report_exception(
            exc_type,
            exc_value,
            args.exc_traceback,
            origin=f"unraisable object {args.object!r}",
        )

    sys.excepthook = sys_hook
    threading.excepthook = thread_hook
    sys.unraisablehook = unraisable_hook
    _hooks_installed = True


__all__ = [
    "LOGGER_NAME",
    "configure_logging",
    "get_logger",
    "install_exception_hooks",
    "log_file_path",
    "log_suppressed_exception",
]
