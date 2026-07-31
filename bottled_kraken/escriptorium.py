"""Native local eScriptorium lifecycle management for Bottled Kraken.

The user selects Fedora, Linux Mint, or Windows. Bottled Kraken then performs
all long-running setup and lifecycle work in a background Qt thread. Fedora
and Mint use a private Python virtual environment plus user-owned PostgreSQL
and Redis data directories. Windows imports an official Ubuntu 24.04 WSL2
root file system as a dedicated distribution stored below the Bottled Kraken
data directory.

No Docker or Docker Compose command is used by this integration.
"""
from __future__ import annotations

from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import platform as platform_module
import queue
import re
import secrets
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import tarfile
import threading
import time
from typing import Callable, Iterable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
import zipfile

from bottled_kraken.runtime_logging import get_logger
from bottled_kraken.subprocess_env import bk_clean_child_env
from bottled_kraken.user_storage import bottled_kraken_user_path

ESCRIPTORIUM_REPOSITORY_URL = "https://gitlab.com/scripta/escriptorium.git"
ESCRIPTORIUM_ARCHIVE_URL = (
    "https://gitlab.com/scripta/escriptorium/-/archive/{ref}/"
    "escriptorium-{ref}.zip"
)
ESCRIPTORIUM_DEFAULT_REF = "26.04.1"
ESCRIPTORIUM_SERVER_URL = "http://127.0.0.1:8000/"
ESCRIPTORIUM_DOCUMENTATION_URL = "https://escriptorium.readthedocs.io/en/latest/"

ESCRIPTORIUM_PLATFORM_FEDORA = "fedora"
ESCRIPTORIUM_PLATFORM_MINT = "mint"
ESCRIPTORIUM_PLATFORM_WINDOWS_WSL = "windows_wsl"
ESCRIPTORIUM_SUPPORTED_PLATFORMS = (
    ESCRIPTORIUM_PLATFORM_FEDORA,
    ESCRIPTORIUM_PLATFORM_MINT,
    ESCRIPTORIUM_PLATFORM_WINDOWS_WSL,
)
ESCRIPTORIUM_WSL_DISTRIBUTION = "BottledKraken-eScriptorium"
UBUNTU_WSL_IMAGE_BASE_URL = "https://cloud-images.ubuntu.com/wsl/releases/24.04/current"

ESCRIPTORIUM_PYVIPS_VERSION = "3.1.1"
ESCRIPTORIUM_PYVIPS_SDIST_URL = (
    "https://files.pythonhosted.org/packages/2d/6a/"
    "282936de9faac6addf6bc8792c18e006489d0023ffd8856b8643f54d0558/"
    "pyvips-3.1.1.tar.gz"
)
ESCRIPTORIUM_PYVIPS_SDIST_SHA256 = (
    "84fe744d023b1084ac2516bb17064cacd41c7f8aabf8e524dd383534941b9301"
)
ESCRIPTORIUM_TORCH_CPU_INDEX_URL = "https://download.pytorch.org/whl/cpu"
# eScriptorium 26.04.1 resolves Kraken 7.0.x, whose metadata caps torch at
# ``<=2.12``.  PyTorch 2.12.1 is therefore outside the accepted range even
# though it is a patch release.  Keep the matching official torchvision
# release pinned as one tested CPU pair.
ESCRIPTORIUM_TORCH_VERSION = "2.12.0"
ESCRIPTORIUM_TORCHVISION_VERSION = "0.27.0"

POSTGRES_PORT = 54329
REDIS_PORT = 6389
POSTGRES_UNIX_SOCKET_MAX_BYTES = 107


def _postgres_socket_path_length(socket_dir: Path, port: int = POSTGRES_PORT) -> int:
    """Return the encoded Unix-socket pathname length used by PostgreSQL."""
    socket_path = Path(socket_dir) / f".s.PGSQL.{int(port)}"
    return len(os.fsencode(str(socket_path)))


def _short_postgres_socket_dir(
    platform_id: str,
    *,
    environ: Mapping[str, str] | None = None,
    temp_dir: str | os.PathLike[str] | None = None,
    uid: int | str | None = None,
) -> Path:
    """Choose a short per-user runtime directory for PostgreSQL sockets.

    ``sockaddr_un.sun_path`` is limited to 107 usable bytes on Linux.  The
    normal Bottled Kraken data path can exceed that limit before PostgreSQL
    appends ``/.s.PGSQL.<port>``.  Prefer ``XDG_RUNTIME_DIR`` and fall back to
    a UID-scoped directory below the system temporary directory.
    """
    env = os.environ if environ is None else environ
    selected = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(platform_id or "linux"))[:24] or "linux"
    runtime_value = str(env.get("XDG_RUNTIME_DIR", "") or "").strip()
    try:
        user_id = os.getuid() if uid is None else uid
    except AttributeError:  # pragma: no cover - Windows does not use this backend
        user_id = "user" if uid is None else uid
    temp_base = Path(tempfile.gettempdir() if temp_dir is None else temp_dir)
    candidates = []
    if runtime_value:
        candidates.append(Path(runtime_value) / "bottled-kraken" / selected / "pg")
    candidates.extend(
        (
            temp_base / f"bk-pg-{user_id}" / selected,
            Path("/tmp") / f"bkpg-{user_id}" / selected,
        )
    )
    for candidate in candidates:
        if _postgres_socket_path_length(candidate) <= POSTGRES_UNIX_SOCKET_MAX_BYTES:
            return candidate
    raise EScriptoriumError(
        "database_setup_failed",
        "No sufficiently short directory is available for the PostgreSQL Unix socket.",
    )


ProgressCallback = Callable[[str, int, str], None]
CancelCallback = Callable[[], bool]


class EScriptoriumError(RuntimeError):
    """Structured failure that can be localized by the GUI layer."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = str(code or "unexpected")
        self.detail = str(detail or "").strip()
        super().__init__(f"{self.code}: {self.detail}" if self.detail else self.code)


@dataclass(frozen=True)
class EScriptoriumPaths:
    root: Path
    profile: Path
    source: Path
    downloads: Path
    data: Path
    runtime: Path
    config: Path
    logs: Path
    credentials: Path
    env_file: Path
    local_settings_file: Path
    venv: Path
    pid_dir: Path
    install_marker: Path
    platform_file: Path
    scripts: Path
    wsl_location: Path


@dataclass(frozen=True)
class EScriptoriumStatus:
    installed: bool
    running: bool
    platform_id: str
    platform_compatible: bool
    prerequisites_available: bool
    server_url: str
    install_dir: str
    credentials_file: str
    detail: str = ""


@dataclass(frozen=True)
class _PlatformInfo:
    platform_id: str
    compatible: bool
    detail: str = ""


def _read_os_release(path: Path = Path("/etc/os-release")) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" not in line or line.lstrip().startswith("#"):
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"\'')
    except OSError:
        pass
    return values


def detect_escriptorium_platform(
    *,
    os_name: str | None = None,
    platform_name: str | None = None,
    os_release: Mapping[str, str] | None = None,
) -> str:
    """Return the most suitable supported backend for the current host."""
    current_os = os.name if os_name is None else os_name
    current_platform = sys.platform if platform_name is None else platform_name
    if current_os == "nt" or current_platform.startswith("win"):
        return ESCRIPTORIUM_PLATFORM_WINDOWS_WSL
    if current_platform.startswith("linux"):
        release = dict(_read_os_release() if os_release is None else os_release)
        tokens = " ".join(
            str(release.get(key, "")) for key in ("ID", "ID_LIKE", "NAME")
        ).casefold()
        if any(token in tokens for token in ("fedora", "rhel", "centos")):
            return ESCRIPTORIUM_PLATFORM_FEDORA
        if any(token in tokens for token in ("linuxmint", "mint", "ubuntu", "debian")):
            return ESCRIPTORIUM_PLATFORM_MINT
    return ESCRIPTORIUM_PLATFORM_MINT


def platform_compatibility(platform_id: str) -> _PlatformInfo:
    selected = str(platform_id or "").strip()
    if selected not in ESCRIPTORIUM_SUPPORTED_PLATFORMS:
        return _PlatformInfo(selected, False, "unsupported")
    if selected == ESCRIPTORIUM_PLATFORM_WINDOWS_WSL:
        compatible = os.name == "nt" or sys.platform.startswith("win")
        return _PlatformInfo(selected, compatible, "windows_required" if not compatible else "")
    compatible = sys.platform.startswith("linux") and os.name != "nt"
    if not compatible:
        return _PlatformInfo(selected, False, "linux_required")
    detected = detect_escriptorium_platform()
    if selected == ESCRIPTORIUM_PLATFORM_FEDORA and detected != ESCRIPTORIUM_PLATFORM_FEDORA:
        return _PlatformInfo(selected, False, "fedora_required")
    if selected == ESCRIPTORIUM_PLATFORM_MINT and detected == ESCRIPTORIUM_PLATFORM_FEDORA:
        return _PlatformInfo(selected, False, "mint_required")
    return _PlatformInfo(selected, True, "")


def _subprocess_flags() -> int:
    return int(getattr(subprocess, "CREATE_NO_WINDOW", 0)) if os.name == "nt" else 0


def _clean_output(value: object) -> str:
    return str(value or "").replace("\x00", "").strip()


def open_external_url(url: str) -> bool:
    """Open an HTTP(S) URL with the native desktop browser.

    PyInstaller bundles can leak bundled Qt/GTK libraries into ``xdg-open``
    and KDE/GIO launchers.  Start those tools with the same cleaned child
    environment used for external file managers, then let the UI use
    ``QDesktopServices`` only as a final fallback.
    """
    target = str(url or "").strip()
    parsed = urlparse(target)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return False

    try:
        if os.name == "nt" or sys.platform.startswith("win"):
            os.startfile(target)  # type: ignore[attr-defined]
            return True
    except Exception:
        pass

    if sys.platform == "darwin":
        commands = [["open", target]]
    else:
        commands = [
            # Cinnamon/GNOME first: these respect Linux Mint's default-app
            # settings and work reliably from a PyInstaller child process.
            ["gio", "open", target],
            ["xdg-open", target],
            ["sensible-browser", target],
            ["x-www-browser", target],
            ["kioclient6", "exec", target],
            ["kioclient5", "exec", target],
            ["kioclient", "exec", target],
        ]

    env = bk_clean_child_env()
    search_path = env.get("PATH")
    for command in commands:
        executable = shutil.which(command[0], path=search_path)
        if not executable:
            continue
        command = [executable, *command[1:]]
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                start_new_session=os.name != "nt",
                env=env,
                creationflags=_subprocess_flags(),
            )
            try:
                if process.wait(timeout=1.0) == 0:
                    return True
                continue
            except subprocess.TimeoutExpired:
                # Some browser launchers remain attached until the browser has
                # accepted the URL.  A still-running launcher means the handoff
                # was started successfully.
                return True
        except OSError:
            continue
    return False


def open_local_path(path: str | os.PathLike[str]) -> bool:
    """Open a local file or directory with the native desktop application.

    PyInstaller one-file builds must not leak their bundled Qt/GTK library
    paths into external file managers. The function therefore uses a cleaned
    child environment and tries platform-native launchers before the Qt GUI
    layer falls back to ``QDesktopServices``.
    """
    target = Path(path).expanduser().resolve(strict=False)
    if not target.exists():
        try:
            if target.suffix:
                target.parent.mkdir(parents=True, exist_ok=True)
            else:
                target.mkdir(parents=True, exist_ok=True)
        except OSError:
            return False
    try:
        if os.name == "nt" or sys.platform.startswith("win"):
            os.startfile(str(target))  # type: ignore[attr-defined]
            return True
    except Exception:
        pass

    url = target.as_uri()
    commands: list[list[str]]
    if sys.platform == "darwin":
        commands = [["open", str(target)]]
    else:
        commands = [
            ["gio", "open", str(target)],
            ["xdg-open", str(target)],
        ]
        if target.is_dir():
            commands.append(["nemo", str(target)])
        commands.extend([
            ["kioclient6", "exec", url],
            ["kioclient5", "exec", url],
            ["kioclient", "exec", url],
        ])
    env = bk_clean_child_env()
    search_path = env.get("PATH")
    for command in commands:
        executable = shutil.which(command[0], path=search_path)
        if not executable:
            continue
        command = [executable, *command[1:]]
        try:
            subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                start_new_session=True,
                env=env,
                creationflags=_subprocess_flags(),
            )
            return True
        except OSError:
            continue
    return False


class EScriptoriumManager:
    """Install and operate a local eScriptorium instance without containers."""

    def __init__(
        self,
        root: str | os.PathLike[str] | None = None,
        *,
        platform_id: str | None = None,
        ref: str | None = None,
        server_url: str | None = None,
    ) -> None:
        base = Path(root).expanduser() if root else bottled_kraken_user_path("escriptorium")
        self.root = base.resolve(strict=False)
        self.root.mkdir(parents=True, exist_ok=True)
        self.ref = (
            ref
            or os.environ.get("BOTTLED_KRAKEN_ESCRIPTORIUM_REF")
            or ESCRIPTORIUM_DEFAULT_REF
        ).strip()
        self.server_url = (
            server_url
            or os.environ.get("BOTTLED_KRAKEN_ESCRIPTORIUM_URL")
            or ESCRIPTORIUM_SERVER_URL
        ).strip()
        if not self.server_url.endswith("/"):
            self.server_url += "/"
        saved = self._load_saved_platform()
        selected = platform_id or saved or detect_escriptorium_platform()
        self.platform_id = self._normalize_platform(selected)
        self.logger = get_logger("escriptorium")
        self._active_progress_callback: ProgressCallback | None = None
        self._active_cancel_requested: CancelCallback | None = None
        self._active_stage = "prepare"
        self._active_percent = 0

    @staticmethod
    def _normalize_platform(value: str) -> str:
        selected = str(value or "").strip().casefold()
        aliases = {
            "windows": ESCRIPTORIUM_PLATFORM_WINDOWS_WSL,
            "wsl": ESCRIPTORIUM_PLATFORM_WINDOWS_WSL,
            "windows-wsl": ESCRIPTORIUM_PLATFORM_WINDOWS_WSL,
            "linux_mint": ESCRIPTORIUM_PLATFORM_MINT,
            "linux-mint": ESCRIPTORIUM_PLATFORM_MINT,
        }
        selected = aliases.get(selected, selected)
        if selected not in ESCRIPTORIUM_SUPPORTED_PLATFORMS:
            raise ValueError(f"Unsupported eScriptorium platform: {value!r}")
        return selected

    def _load_saved_platform(self) -> str | None:
        config = self.root / "platform.json"
        try:
            value = json.loads(config.read_text(encoding="utf-8")).get("platform")
            if value:
                return self._normalize_platform(str(value))
        except Exception:
            pass
        return None

    def set_platform(self, platform_id: str, *, persist: bool = True) -> None:
        self.platform_id = self._normalize_platform(platform_id)
        if persist:
            config = self.root / "platform.json"
            config.parent.mkdir(parents=True, exist_ok=True)
            temp = config.with_suffix(".tmp")
            temp.write_text(
                json.dumps({"platform": self.platform_id}, indent=2) + "\n",
                encoding="utf-8",
            )
            temp.replace(config)

    @property
    def paths(self) -> EScriptoriumPaths:
        profile = self.root / "platforms" / self.platform_id
        source = profile / "source"
        runtime = profile / "runtime"
        config = profile / "config"
        return EScriptoriumPaths(
            root=self.root,
            profile=profile,
            source=source,
            downloads=self.root / "downloads",
            data=profile / "data",
            runtime=runtime,
            config=config,
            logs=profile / "logs",
            credentials=profile / "credentials.txt",
            env_file=config / "runtime.env",
            local_settings_file=source / "app" / "escriptorium" / "local_settings.py",
            venv=runtime / "venv",
            pid_dir=runtime / "pids",
            install_marker=config / "installed.json",
            platform_file=self.root / "platform.json",
            scripts=profile / "scripts",
            wsl_location=profile / "wsl",
        )

    @contextmanager
    def _operation_context(
        self,
        progress: ProgressCallback | None,
        cancel_requested: CancelCallback | None,
    ):
        previous = (
            self._active_progress_callback,
            self._active_cancel_requested,
            self._active_stage,
            self._active_percent,
        )
        self._active_progress_callback = progress
        self._active_cancel_requested = cancel_requested
        try:
            yield
        finally:
            (
                self._active_progress_callback,
                self._active_cancel_requested,
                self._active_stage,
                self._active_percent,
            ) = previous

    def _cancel_is_requested(self) -> bool:
        callback = self._active_cancel_requested
        if callback is None:
            return False
        try:
            return bool(callback())
        except Exception:
            self.logger.exception("eScriptorium cancellation callback failed")
            return False

    def _raise_if_cancelled(self) -> None:
        if self._cancel_is_requested():
            raise EScriptoriumError("cancelled")

    def _progress(
        self,
        callback: ProgressCallback | None,
        stage: str,
        percent: int,
        detail: str = "",
    ) -> None:
        self._raise_if_cancelled()
        normalized_percent = max(0, min(100, int(percent)))
        self._active_stage = str(stage or self._active_stage or "prepare")
        self._active_percent = normalized_percent
        target = callback or self._active_progress_callback
        if target is not None:
            target(self._active_stage, normalized_percent, str(detail or ""))

    @staticmethod
    def _command_text(command: Iterable[object]) -> str:
        return " ".join(shlex.quote(str(part)) for part in command)

    @staticmethod
    def _terminate_process(process: subprocess.Popen[str]) -> None:
        if process.poll() is not None:
            return
        try:
            if os.name != "nt":
                os.killpg(process.pid, signal.SIGTERM)
            else:
                process.terminate()
        except OSError:
            try:
                process.terminate()
            except OSError:
                pass
        try:
            process.wait(timeout=8)
            return
        except subprocess.TimeoutExpired:
            pass
        try:
            if os.name != "nt":
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
        except OSError:
            try:
                process.kill()
            except OSError:
                pass

    @staticmethod
    def _clean_progress_line(value: str) -> str:
        line = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", str(value or ""))
        line = line.replace("\r", " ").replace("\x00", "").strip()
        return line[-600:]

    def _run(
        self,
        command: list[str],
        *,
        cwd: Path | None = None,
        timeout: int = 120,
        check: bool = True,
        env: Mapping[str, str] | None = None,
        code: str = "command_failed",
    ) -> subprocess.CompletedProcess[str]:
        """Run a command with live output, cancellation, and timeout handling.

        During an active GUI operation output is consumed continuously instead
        of being buffered by ``subprocess.run``. This keeps long package and
        Python dependency installations visibly alive and prevents pipe buffers
        from stalling child processes. Only recent output is retained for
        diagnostics.
        """
        self._raise_if_cancelled()
        command_text = self._command_text(command)
        self.logger.info("Running eScriptorium command: %s", command_text)
        child_env = bk_clean_child_env()
        if env:
            child_env.update({str(key): str(value) for key, value in env.items()})

        creationflags = _subprocess_flags()
        if os.name == "nt":
            creationflags |= int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
        try:
            process = subprocess.Popen(
                command,
                cwd=str(cwd) if cwd else None,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                env=child_env,
                creationflags=creationflags,
                start_new_session=(os.name != "nt"),
            )
        except OSError as exc:
            raise EScriptoriumError(code, str(exc)) from exc

        output_queue: queue.Queue[str | None] = queue.Queue()
        output_lines: deque[str] = deque(maxlen=600)
        recent_context: deque[str] = deque(maxlen=8)
        diagnostic_lines: deque[str] = deque(maxlen=240)
        diagnostic_followup = 0

        def _reader() -> None:
            stream = process.stdout
            try:
                if stream is not None:
                    for raw_line in iter(stream.readline, ""):
                        output_queue.put(raw_line)
            finally:
                try:
                    if stream is not None:
                        stream.close()
                except OSError:
                    pass
                output_queue.put(None)

        reader = threading.Thread(
            target=_reader,
            name="bk-escriptorium-command-output",
            daemon=True,
        )
        reader.start()
        started = time.monotonic()
        deadline = started + max(1, int(timeout))
        last_emit = started
        emitted_real_output = False
        last_detail = ""
        reader_done = False

        try:
            while True:
                while True:
                    try:
                        item = output_queue.get_nowait()
                    except queue.Empty:
                        break
                    if item is None:
                        reader_done = True
                        continue
                    cleaned = self._clean_progress_line(item)
                    if not cleaned:
                        continue
                    output_lines.append(cleaned)
                    last_detail = cleaned
                    lowered = cleaned.casefold()
                    critical = any(
                        token in lowered
                        for token in (
                            "error", "failed", "failure", "exception",
                            "traceback", "fatal", "cannot", "could not",
                        )
                    )
                    if critical:
                        for context_line in recent_context:
                            if not diagnostic_lines or diagnostic_lines[-1] != context_line:
                                diagnostic_lines.append(context_line)
                        diagnostic_lines.append(cleaned)
                        diagnostic_followup = 12
                    elif diagnostic_followup > 0:
                        diagnostic_lines.append(cleaned)
                        diagnostic_followup -= 1
                    recent_context.append(cleaned)
                    self.logger.debug("eScriptorium command output: %s", cleaned)
                    now_for_output = time.monotonic()
                    if (
                        self._active_progress_callback is not None
                        and (
                            not emitted_real_output
                            or now_for_output - last_emit >= 0.15
                        )
                    ):
                        self._progress(
                            self._active_progress_callback,
                            self._active_stage,
                            self._active_percent,
                            cleaned,
                        )
                        last_emit = now_for_output
                        emitted_real_output = True

                now = time.monotonic()
                if self._cancel_is_requested():
                    self._terminate_process(process)
                    raise EScriptoriumError("cancelled")
                if now >= deadline and process.poll() is None:
                    self._terminate_process(process)
                    raise EScriptoriumError("timeout", command_text)

                if self._active_progress_callback is not None and now - last_emit >= 5.0:
                    elapsed = max(0, int(now - started))
                    elapsed_text = f"{elapsed // 60:02d}:{elapsed % 60:02d}"
                    heartbeat = (
                        f"{elapsed_text} — {last_detail}" if last_detail else elapsed_text
                    )
                    self._progress(
                        self._active_progress_callback,
                        self._active_stage,
                        self._active_percent,
                        heartbeat,
                    )
                    last_emit = now

                returncode = process.poll()
                if returncode is not None and reader_done and output_queue.empty():
                    break
                time.sleep(0.1)
        except Exception:
            if process.poll() is None:
                self._terminate_process(process)
            raise
        finally:
            reader.join(timeout=2)

        while True:
            try:
                item = output_queue.get_nowait()
            except queue.Empty:
                break
            if item is None:
                continue
            cleaned = self._clean_progress_line(item)
            if cleaned:
                output_lines.append(cleaned)
                lowered = cleaned.casefold()
                if any(token in lowered for token in ("error", "failed", "exception", "traceback", "fatal")):
                    diagnostic_lines.append(cleaned)

        stdout = "\n".join(output_lines)
        result = subprocess.CompletedProcess(command, int(process.returncode or 0), stdout, "")
        if check and result.returncode != 0:
            tail = _clean_output(result.stdout)
            diagnostics = _clean_output("\n".join(diagnostic_lines))
            if diagnostics and diagnostics not in tail:
                detail = f"{diagnostics}\n\n--- last output ---\n{tail}"
            else:
                detail = tail
            detail = detail[-24000:]
            self.logger.error(
                "eScriptorium command failed (%s): %s",
                result.returncode,
                detail,
            )
            raise EScriptoriumError(code, detail or command_text)
        return result

    def _archive_url(self) -> str:
        safe_ref = quote(self.ref, safe="-._")
        return ESCRIPTORIUM_ARCHIVE_URL.format(ref=safe_ref)

    def _download_archive(self, callback: ProgressCallback | None) -> Path:
        paths = self.paths
        paths.downloads.mkdir(parents=True, exist_ok=True)
        final_path = paths.downloads / f"escriptorium-{self.ref.replace('/', '-')}.zip"
        temp_path = final_path.with_suffix(".zip.part")
        request = Request(self._archive_url(), headers={"User-Agent": "BottledKraken/3.4"})
        self._progress(callback, "download_source", 3, self.ref)
        try:
            with urlopen(request, timeout=60) as response, temp_path.open("wb") as handle:
                total = int(response.headers.get("Content-Length") or 0)
                downloaded = 0
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    handle.write(chunk)
                    downloaded += len(chunk)
                    percent = 3 + int((downloaded / total) * 27) if total > 0 else 12
                    self._progress(
                        callback,
                        "download_source",
                        min(percent, 30),
                        f"{downloaded / (1024 * 1024):.1f} MiB",
                    )
            temp_path.replace(final_path)
            return final_path
        except Exception as exc:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise EScriptoriumError("download_failed", str(exc)) from exc

    @staticmethod
    def _safe_extract(archive: Path, destination: Path) -> None:
        destination = destination.resolve(strict=False)
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.infolist():
                target = (destination / member.filename).resolve(strict=False)
                if destination != target and destination not in target.parents:
                    raise EScriptoriumError("archive_invalid", member.filename)
            bundle.extractall(destination)

    @staticmethod
    def _find_source_root(extracted: Path) -> Path:
        candidates = [
            path.parent.parent
            for path in extracted.rglob("app/manage.py")
            if path.is_file() and (path.parent.parent / "front" / "package.json").is_file()
        ]
        if not candidates:
            raise EScriptoriumError("archive_invalid", "app/manage.py")
        return min(candidates, key=lambda path: len(path.parts))

    @staticmethod
    def _copy_if_present(source_root: Path, target_root: Path, relative: str) -> None:
        source = source_root / relative
        target = target_root / relative
        if not source.exists():
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)

    def _replace_source(self, extracted_source: Path) -> None:
        source = self.paths.source
        backup = self.paths.profile / ".source-backup"
        preserve = ("app/escriptorium/local_settings.py",)
        if backup.exists():
            shutil.rmtree(backup, ignore_errors=True)
        try:
            source.parent.mkdir(parents=True, exist_ok=True)
            if source.exists():
                source.replace(backup)
            extracted_source.replace(source)
            if backup.exists():
                for relative in preserve:
                    self._copy_if_present(backup, source, relative)
                shutil.rmtree(backup, ignore_errors=True)
        except Exception:
            if source.exists():
                shutil.rmtree(source, ignore_errors=True)
            if backup.exists():
                backup.replace(source)
            raise

    def _prepare_source(self, callback: ProgressCallback | None) -> None:
        self.paths.profile.mkdir(parents=True, exist_ok=True)
        archive = self._download_archive(callback)
        extraction_parent = Path(
            tempfile.mkdtemp(prefix="escriptorium-", dir=str(self.paths.profile))
        )
        try:
            self._progress(callback, "extract_source", 32, archive.name)
            self._safe_extract(archive, extraction_parent)
            self._replace_source(self._find_source_root(extraction_parent))
        except EScriptoriumError:
            raise
        except Exception as exc:
            raise EScriptoriumError("archive_invalid", str(exc)) from exc
        finally:
            shutil.rmtree(extraction_parent, ignore_errors=True)

    @staticmethod
    def _parse_env(path: Path) -> dict[str, str]:
        values: dict[str, str] = {}
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return values
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            values[key.strip()] = value.strip()
        return values

    def _ensure_secrets(
        self,
        credentials_labels: Mapping[str, str] | None = None,
    ) -> dict[str, str]:
        paths = self.paths
        for directory in (
            paths.config,
            paths.data / "postgres",
            paths.data / "redis",
            paths.data / "media",
            paths.data / "static",
            paths.data / "emails",
            paths.logs,
            paths.runtime,
            paths.pid_dir,
            paths.scripts,
        ):
            directory.mkdir(parents=True, exist_ok=True)
        values = self._parse_env(paths.env_file)
        defaults = {
            "SECRET_KEY": secrets.token_urlsafe(48),
            "POSTGRES_DB": "escriptorium",
            "POSTGRES_USER": "bk_escriptorium",
            "POSTGRES_PASSWORD": secrets.token_urlsafe(24),
            "SQL_HOST": "127.0.0.1",
            "SQL_PORT": str(POSTGRES_PORT),
            "REDIS_HOST": "127.0.0.1",
            "REDIS_PORT": str(REDIS_PORT),
            "DJANGO_SU_NAME": "admin",
            "DJANGO_SU_EMAIL": "admin@localhost",
            "DJANGO_SU_PASSWORD": secrets.token_urlsafe(18),
            "CSRF_TRUSTED_ORIGINS": self.server_url.rstrip("/"),
            "DISABLE_ELASTICSEARCH": "True",
            "KRAKEN_TRAINING_DEVICE": "cpu",
            "DJANGO_SETTINGS_MODULE": "escriptorium.local_settings",
            "PYTHONUNBUFFERED": "1",
        }
        values = {**defaults, **values}
        for key, value in tuple(values.items()):
            values[key] = str(value).strip()

        # runtime.env is sourced by Bash inside WSL.  On Windows the default
        # text-mode newline conversion would write CRLF and leave a hidden
        # carriage return in every exported value (for example ``admin\r``).
        # Always rewrite the file with LF, including existing installations.
        with paths.env_file.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(
                "\n".join(f"{key}={value}" for key, value in values.items()) + "\n"
            )
        try:
            paths.env_file.chmod(0o600)
        except OSError:
            pass

        labels = {
            "header": "eScriptorium local administrator",
            "user": "User",
            "password": "Password",
        }
        if credentials_labels:
            for key in labels:
                value = str(credentials_labels.get(key, "") or "").strip()
                if value:
                    labels[key] = value
        with paths.credentials.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(
                f"{labels['header']}\n"
                f"URL: {self.server_url}\n"
                f"{labels['user']}: {values.get('DJANGO_SU_NAME', 'admin')}\n"
                f"{labels['password']}: {values.get('DJANGO_SU_PASSWORD', '')}\n"
            )
        try:
            paths.credentials.chmod(0o600)
        except OSError:
            pass
        return values

    def _write_native_local_settings(self) -> None:
        paths = self.paths
        settings = f'''# Generated by Bottled Kraken. Manual edits may be overwritten.\nimport os\nfrom .settings import *  # noqa: F401,F403\n\n\ndef _bk_env(name, default=""):\n    value = os.getenv(name)\n    if value is None:\n        return default\n    value = value.strip()\n    for _ in range(3):\n        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):\n            value = value[1:-1].strip()\n            continue\n        if len(value) >= 4 and value.startswith("\\\\\\\"") and value.endswith("\\\\\\\""):\n            value = value[2:-2].strip()\n            continue\n        break\n    return value or default\n\n\nDEBUG = True\nMEDIA_ROOT = {str(paths.data / "media")!r}\nSTATIC_ROOT = {str(paths.data / "static")!r}\nEMAIL_FILE_PATH = {str(paths.data / "emails")!r}\nDISABLE_ELASTICSEARCH = True\nDATABASES["default"].update({{\n    "HOST": _bk_env("SQL_HOST", "127.0.0.1"),\n    "PORT": _bk_env("SQL_PORT", "{POSTGRES_PORT}"),\n    "NAME": _bk_env("POSTGRES_DB", "escriptorium"),\n    "USER": _bk_env("POSTGRES_USER", "bk_escriptorium"),\n    "PASSWORD": _bk_env("POSTGRES_PASSWORD", ""),\n}})\n'''
        paths.local_settings_file.parent.mkdir(parents=True, exist_ok=True)
        # Upstream's base settings open app/escriptorium/logs/error.log while
        # Django imports the settings module. Git archives do not preserve an
        # empty directory, so create it before any manage.py/Celery command.
        (paths.local_settings_file.parent / "logs").mkdir(parents=True, exist_ok=True)
        paths.local_settings_file.write_text(settings, encoding="utf-8")

    def _runtime_env(self) -> dict[str, str]:
        values = self._parse_env(self.paths.env_file)
        env = bk_clean_child_env()
        env.update(values)
        bin_dir = self.paths.venv / ("Scripts" if os.name == "nt" else "bin")
        env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
        env["DJANGO_SETTINGS_MODULE"] = "escriptorium.local_settings"
        env["FRONTEND_DIR"] = str(self.paths.source / "front" / "dist")
        return env

    def _backend(self):
        if self.platform_id == ESCRIPTORIUM_PLATFORM_WINDOWS_WSL:
            return _WindowsWslBackend(self)
        return _NativeLinuxBackend(self, self.platform_id)

    def source_is_installed(self) -> bool:
        return self._backend().is_installed()

    def server_is_ready(self, timeout: float = 2.0) -> bool:
        request = Request(self.server_url, headers={"User-Agent": "BottledKraken/3.4"})
        try:
            with urlopen(request, timeout=max(0.2, float(timeout))) as response:
                return 100 <= int(getattr(response, "status", 200)) < 500
        except HTTPError as exc:
            return 100 <= int(exc.code) < 500
        except (URLError, TimeoutError, OSError, ValueError):
            return False

    def status(self) -> EScriptoriumStatus:
        compatibility = platform_compatibility(self.platform_id)
        if not compatibility.compatible:
            return EScriptoriumStatus(
                installed=False,
                running=False,
                platform_id=self.platform_id,
                platform_compatible=False,
                prerequisites_available=False,
                server_url=self.server_url,
                install_dir=str(self.paths.profile),
                credentials_file=str(self.paths.credentials),
                detail=compatibility.detail,
            )
        return self._backend().status()

    def install(
        self,
        progress: ProgressCallback | None = None,
        credentials_labels: Mapping[str, str] | None = None,
        *,
        cancel_requested: CancelCallback | None = None,
    ) -> EScriptoriumStatus:
        with self._operation_context(progress, cancel_requested):
            compatibility = platform_compatibility(self.platform_id)
            if not compatibility.compatible:
                raise EScriptoriumError("platform_mismatch", compatibility.detail)
            self._progress(progress, "prepare", 0, str(self.paths.profile))
            self._prepare_source(progress)
            values = self._ensure_secrets(credentials_labels)
            if self.platform_id != ESCRIPTORIUM_PLATFORM_WINDOWS_WSL:
                self._write_native_local_settings()
            self._backend().install(progress, values)
            marker = {
                "platform": self.platform_id,
                "ref": self.ref,
                "installed_at": time.time(),
            }
            self.paths.install_marker.parent.mkdir(parents=True, exist_ok=True)
            self.paths.install_marker.write_text(
                json.dumps(marker, indent=2) + "\n",
                encoding="utf-8",
            )
            self._progress(progress, "done", 100, str(self.paths.profile))
            return self.status()

    def start(
        self,
        progress: ProgressCallback | None = None,
        credentials_labels: Mapping[str, str] | None = None,
        *,
        auto_install: bool = False,
        cancel_requested: CancelCallback | None = None,
    ) -> EScriptoriumStatus:
        """Start an already installed eScriptorium instance.

        Installation is deliberately a separate user action.  This prevents a
        server-start click from unexpectedly downloading gigabytes, requesting
        administrator privileges, or modifying the local runtime.
        """
        with self._operation_context(progress, cancel_requested):
            if not self.source_is_installed():
                if not auto_install:
                    raise EScriptoriumError("not_installed")
                self.install(
                    progress,
                    credentials_labels,
                    cancel_requested=cancel_requested,
                )
            backend = self._backend()
            try:
                backend.start(progress)
                deadline = time.monotonic() + 240
                while time.monotonic() < deadline:
                    self._raise_if_cancelled()
                    if self.server_is_ready(timeout=2):
                        self._progress(progress, "done", 100, self.server_url)
                        return self.status()
                    diagnostics = getattr(backend, "startup_failure_detail", lambda: "")()
                    if diagnostics:
                        raise EScriptoriumError("server_start_failed", diagnostics)
                    elapsed = 240 - max(0, int(deadline - time.monotonic()))
                    self._progress(
                        progress,
                        "wait_server",
                        min(98, 55 + int((elapsed / 240) * 43)),
                        self.server_url,
                    )
                    time.sleep(2)
            except Exception:
                try:
                    backend.stop(None)
                except Exception:
                    self.logger.exception("Failed to clean up eScriptorium after start failure")
                raise
            diagnostics = getattr(backend, "diagnostic_tail", lambda: "")()
            detail = self.server_url
            if diagnostics:
                detail += "\n\n" + diagnostics
            raise EScriptoriumError("server_not_ready", detail)

    def stop(
        self,
        progress: ProgressCallback | None = None,
        *,
        cancel_requested: CancelCallback | None = None,
    ) -> EScriptoriumStatus:
        with self._operation_context(progress, cancel_requested):
            if not self.source_is_installed():
                raise EScriptoriumError("not_installed")
            self._backend().stop(progress)
            self._progress(progress, "done", 100, "")
            return self.status()

    def open_browser(self) -> bool:
        """Open the configured local server with a bundle-safe launcher."""
        return open_external_url(self.server_url)

    def open_folder(self) -> bool:
        """Open the selected platform profile in the native file manager."""
        self.paths.profile.mkdir(parents=True, exist_ok=True)
        return open_local_path(self.paths.profile)

    def open_credentials(self) -> bool:
        return self.paths.credentials.is_file() and open_local_path(self.paths.credentials)


class _NativeLinuxBackend:
    """Fedora and Linux Mint backend using user-owned local services."""

    FEDORA_PACKAGES = (
        "postgresql-server", "postgresql-contrib", "redis", "git", "curl",
        "gettext", "vips", "vips-devel", "vips-tools", "nodejs", "npm", "python3.12", "python3.12-devel",
        # Fedora retires individual OpenJDK streams over time.  Use the
        # stable virtual capability instead of pinning a release-specific
        # package such as java-17-openjdk-devel.  DNF resolves java-devel to
        # the supported JDK of the current Fedora release and pulls the JRE.
        "java-devel", "ant",
        "gcc", "gcc-c++", "make", "libpq-devel",
        "pkgconf-pkg-config", "glib2-devel", "expat-devel",
        "libjpeg-turbo-devel", "zlib-devel", "libtiff-devel",
        "libxml2-devel", "libxslt-devel", "openjpeg2-devel",
        "libffi-devel", "jpegoptim", "pngcrush",
    )
    # Linux Mint 22.x is based on Ubuntu 24.04 (Noble) and ships Python 3.12.
    # Keep the interpreter explicit so a later point release cannot silently
    # rebuild the private eScriptorium environment with a different Python.
    MINT_PACKAGES = (
        "postgresql", "postgresql-client", "postgresql-contrib",
        "redis-server", "redis-tools",
        "git", "curl", "ca-certificates", "gettext",
        "libvips-dev", "libvips-tools",
        "nodejs", "npm",
        "python3.12", "python3.12-venv", "python3.12-dev", "python3-pip",
        "build-essential", "default-jre-headless", "default-jdk-headless", "ant",
        "libpq-dev", "pkg-config", "libglib2.0-dev", "libexpat1-dev",
        "libjpeg-dev", "zlib1g-dev", "libtiff-dev", "libxml2-dev",
        "libxslt1-dev", "libopenjp2-7-dev", "libffi-dev",
        "jpegoptim", "pngcrush", "netcat-openbsd",
    )

    def __init__(self, manager: EScriptoriumManager, platform_id: str) -> None:
        self.manager = manager
        self.platform_id = platform_id
        self.paths = manager.paths

    @property
    def python(self) -> Path:
        return self.paths.venv / "bin" / "python"

    @property
    def celery(self) -> Path:
        return self.paths.venv / "bin" / "celery"

    def is_installed(self) -> bool:
        return (
            self.paths.install_marker.is_file()
            and self.python.is_file()
            and (self.paths.source / "app" / "manage.py").is_file()
            and (self.paths.data / "postgres" / "PG_VERSION").is_file()
        )

    def _system_python_command(self) -> str:
        """Return the interpreter used to create eScriptorium's private venv.

        Fedora 44 and Linux Mint 22.x both use a dedicated CPython 3.12
        environment for eScriptorium.  Pinning the executable name prevents a
        future distribution upgrade from silently changing the venv ABI.
        """
        return "python3.12"

    def _missing_prerequisites(self) -> list[str]:
        """Return native build/runtime prerequisites that are still missing.

        Merely finding PostgreSQL, Redis, npm, and Python is not enough.  A
        workstation can have all of those while lacking the libvips headers
        needed by eScriptorium's pinned ``pyvips`` release.  Verify libvips via
        pkg-config rather than requiring the optional ``vips`` command-line
        tool: Fedora and Debian-family systems package that executable
        separately as ``vips-tools``/``libvips-tools``.  The CLI packages are
        still installed for diagnostics, but their absence must not turn an
        otherwise usable libvips development installation into a false error.
        """
        required_commands = (
            self._system_python_command(),
            "npm",
            "node",
            "redis-server",
            "redis-cli",
            "pg_config",
            "git",
            "java",
            "javac",
            "cc",
            "make",
            "pkg-config",
        )
        missing = [command for command in required_commands if not shutil.which(command)]
        pkg_config = shutil.which("pkg-config")
        if pkg_config:
            result = self.manager._run(
                [pkg_config, "--exists", "vips"],
                timeout=20,
                check=False,
            )
            if result.returncode != 0:
                missing.append("libvips development files (pkg-config: vips)")
        return missing

    def _required_commands_available(self) -> bool:
        return not self._missing_prerequisites()

    def status(self) -> EScriptoriumStatus:
        return EScriptoriumStatus(
            installed=self.is_installed(),
            running=self.manager.server_is_ready(timeout=0.25),
            platform_id=self.platform_id,
            platform_compatible=True,
            prerequisites_available=self._required_commands_available(),
            server_url=self.manager.server_url,
            install_dir=str(self.paths.profile),
            credentials_file=str(self.paths.credentials),
        )

    @staticmethod
    def _compact_package_error(detail: str) -> str:
        """Return the actionable part of package-manager diagnostics.

        Package managers can print hundreds of lines for packages that are
        already installed before reporting the one unavailable argument that
        aborted the transaction.  Keep the failure lines and a small amount of
        surrounding context so the GUI error remains readable while the full
        command output is still preserved in the application log.
        """
        lines = [line.strip() for line in str(detail or "").splitlines() if line.strip()]
        if not lines:
            return ""
        markers = (
            "no match",
            "keine übereinstimmung",
            "unable to locate",
            "couldn't find",
            "nicht verfügbar",
            "not available",
            "failed",
            "fehlgeschlagen",
            "error:",
            "fehler:",
            "problem:",
        )
        indexes: set[int] = set()
        for index, line in enumerate(lines):
            lowered = line.casefold()
            if any(marker in lowered for marker in markers):
                for candidate in range(max(0, index - 2), min(len(lines), index + 3)):
                    indexes.add(candidate)
        if indexes:
            selected = [line for index, line in enumerate(lines) if index in indexes]
        else:
            selected = lines[-30:]
        compact = "\n".join(selected)
        return compact[-4000:]

    def _install_system_packages(self, progress: ProgressCallback | None) -> None:
        self.manager._progress(progress, "check_prerequisites", 36, self.platform_id)
        if self._required_commands_available():
            return
        pkexec = shutil.which("pkexec")
        if not pkexec:
            raise EScriptoriumError("privilege_tool_missing", "pkexec")
        self.manager._progress(progress, "install_system_packages", 38, self.platform_id)
        if self.platform_id == ESCRIPTORIUM_PLATFORM_FEDORA:
            dnf = shutil.which("dnf")
            if not dnf:
                raise EScriptoriumError("platform_mismatch", "dnf")
            try:
                self.manager._run(
                    [pkexec, dnf, "install", "-y", *self.FEDORA_PACKAGES],
                    timeout=3600,
                    code="package_install_failed",
                )
            except EScriptoriumError as exc:
                if exc.code != "package_install_failed":
                    raise
                raise EScriptoriumError(
                    "package_install_failed",
                    self._compact_package_error(exc.detail),
                ) from exc
        else:
            apt = shutil.which("apt-get")
            if not apt:
                raise EScriptoriumError("platform_mismatch", "apt-get")
            env_command = shutil.which("env") or "/usr/bin/env"
            self.manager._run(
                [pkexec, env_command, "DEBIAN_FRONTEND=noninteractive", apt, "update"],
                timeout=1800,
                code="package_install_failed",
            )
            self.manager._run(
                [
                    pkexec,
                    env_command,
                    "DEBIAN_FRONTEND=noninteractive",
                    apt,
                    "install",
                    "-y",
                    *self.MINT_PACKAGES,
                ],
                timeout=3600,
                code="package_install_failed",
            )
        missing = self._missing_prerequisites()
        if missing:
            raise EScriptoriumError(
                "prerequisites_missing",
                f"{self.platform_id}: " + ", ".join(missing),
            )

    @staticmethod
    def _requirement_name(line: str) -> str:
        """Return a normalized package name for a simple requirement line.

        eScriptorium's release requirements use one PEP 508 requirement per
        line.  The generated compatibility file keeps the official file
        untouched and removes only dependencies that Bottled Kraken installs
        in a platform-aware way.
        """
        value = str(line or "").strip()
        if not value or value.startswith(("#", "-")):
            return ""
        match = re.match(r"([A-Za-z0-9][A-Za-z0-9_.-]*)", value)
        if not match:
            return ""
        return re.sub(r"[-_.]+", "-", match.group(1)).casefold()

    def _write_compat_requirements(self, requirements: Path) -> Path:
        """Create a local requirements copy without platform-sensitive pins.

        eScriptorium 26.04.1 pins ``pyvips`` to the old 2.1 series. That
        series generates a CFFI extension against the installed libvips
        headers and is incompatible with current distro APIs, including
        Linux Mint 22.x's libvips 8.15 and Fedora 44's libvips 8.18.
        Torch is also handled separately so the resolver cannot replace a
        CPU-only wheel with multi-gigabyte CUDA packages from PyPI.
        """
        excluded = {"pyvips", "torch", "torchvision", "torchaudio"}
        lines = requirements.read_text(encoding="utf-8").splitlines()
        kept = [line for line in lines if self._requirement_name(line) not in excluded]
        target = self.paths.runtime / "requirements-bottled-kraken.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        header = [
            "# Generated by Bottled Kraken from eScriptorium's official app/requirements.txt.",
            "# pyvips and PyTorch are installed separately for platform compatibility.",
        ]
        target.write_text("\n".join(header + kept).rstrip() + "\n", encoding="utf-8")
        return target

    def _write_torch_constraints(self) -> Path:
        """Validate and pin the tested CPU torch pair for the main resolver.

        Kraken 7.0.x declares ``torch>=2.4.0,<=2.12``.  PEP 440 therefore
        accepts ``2.12.0+cpu`` but rejects ``2.12.1+cpu``.  The validation is
        deliberate: selecting the newest 2.12 patch silently reintroduces a
        resolver conflict even though torch itself has already been installed.
        """
        probe = self.manager._run(
            [
                str(self.python), "-c",
                (
                    "import importlib.metadata as m; import torch, torchvision; "
                    "tv=m.version('torch'); vv=m.version('torchvision'); "
                    f"assert tv.split('+', 1)[0] == '{ESCRIPTORIUM_TORCH_VERSION}', tv; "
                    f"assert vv.split('+', 1)[0] == '{ESCRIPTORIUM_TORCHVISION_VERSION}', vv; "
                    "assert tuple(int(x) for x in tv.split('+', 1)[0].split('.')[:3]) <= (2, 12, 0), tv; "
                    "print('torch==' + tv); print('torchvision==' + vv)"
                ),
            ],
            timeout=120,
            code="python_setup_failed",
        )
        pins = [
            line.strip()
            for line in str(probe.stdout or "").splitlines()
            if line.strip().startswith(("torch==", "torchvision=="))
        ]
        if len(pins) != 2:
            raise EScriptoriumError("python_setup_failed", "CPU PyTorch version could not be determined.")
        target = self.paths.runtime / "constraints-bottled-kraken.txt"
        target.write_text("\n".join(pins) + "\n", encoding="utf-8")
        return target

    @staticmethod
    def _compact_python_error(detail: str) -> str:
        """Reduce pip/compiler output to the actionable failure summary."""
        lines = [line.strip() for line in str(detail or "").splitlines() if line.strip()]
        if not lines:
            return ""
        markers = (
            "error:", "failed", "could not", "cannot", "no matching distribution",
            "resolutionimpossible", "modulenotfounderror", "importerror",
            "subprocess-exited-with-error", "failed-wheel-build-for-install",
        )
        selected: list[str] = []
        for index, line in enumerate(lines):
            lowered = line.casefold()
            if any(marker in lowered for marker in markers):
                start = max(0, index - 1)
                end = min(len(lines), index + 3)
                for candidate in lines[start:end]:
                    if candidate not in selected:
                        selected.append(candidate)
        if not selected:
            selected = lines[-24:]
        return "\n".join(selected[-40:])[-6000:]

    @staticmethod
    def _safe_extract_tar(archive: Path, destination: Path) -> None:
        """Extract a trusted package archive while rejecting path traversal."""
        destination.mkdir(parents=True, exist_ok=True)
        root = destination.resolve()
        with tarfile.open(archive, "r:*") as bundle:
            for member in bundle.getmembers():
                target = (destination / member.name).resolve()
                if target != root and root not in target.parents:
                    raise EScriptoriumError("python_setup_failed", f"Unsafe pyvips archive entry: {member.name}")
                if member.issym() or member.islnk():
                    raise EScriptoriumError("python_setup_failed", f"Unsupported pyvips archive link: {member.name}")
            try:
                bundle.extractall(destination, filter="data")
            except TypeError:  # Python 3.10 compatibility
                bundle.extractall(destination)

    def _install_pyvips_abi_fallback(self) -> None:
        """Install pyvips in pure-Python ABI mode after an API build failure.

        Modern pyvips normally compiles cleanly.  If a distribution ships a
        newer libvips header API than the binding knows, this fallback patches
        only the downloaded pyvips build script to skip the optional CFFI
        extension.  The resulting package dynamically loads the system
        libvips library and preserves all distro-provided codecs.
        """
        cache = self.paths.runtime / "pyvips-abi"
        cache.mkdir(parents=True, exist_ok=True)
        archive = cache / f"pyvips-{ESCRIPTORIUM_PYVIPS_VERSION}.tar.gz"
        if archive.is_file():
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            if digest != ESCRIPTORIUM_PYVIPS_SDIST_SHA256:
                archive.unlink(missing_ok=True)
        if not archive.is_file():
            temporary = archive.with_suffix(archive.suffix + ".part")
            temporary.unlink(missing_ok=True)
            digest = hashlib.sha256()
            try:
                request = Request(
                    ESCRIPTORIUM_PYVIPS_SDIST_URL,
                    headers={"User-Agent": "BottledKraken/3.4"},
                )
                with urlopen(request, timeout=60) as response, temporary.open("wb") as handle:
                    while True:
                        self.manager._raise_if_cancelled()
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        handle.write(chunk)
                        digest.update(chunk)
            except EScriptoriumError:
                temporary.unlink(missing_ok=True)
                raise
            except Exception as exc:
                temporary.unlink(missing_ok=True)
                raise EScriptoriumError("python_setup_failed", f"pyvips download: {exc}") from exc
            if digest.hexdigest() != ESCRIPTORIUM_PYVIPS_SDIST_SHA256:
                temporary.unlink(missing_ok=True)
                raise EScriptoriumError("python_setup_failed", "The pyvips source archive checksum is invalid.")
            temporary.replace(archive)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        if digest != ESCRIPTORIUM_PYVIPS_SDIST_SHA256:
            raise EScriptoriumError("python_setup_failed", "The pyvips source archive checksum is invalid.")

        source_root = cache / "source"
        shutil.rmtree(source_root, ignore_errors=True)
        self._safe_extract_tar(archive, source_root)
        setup_files = [candidate for candidate in source_root.rglob("setup.py") if candidate.parent.joinpath("pyproject.toml").is_file()]
        if len(setup_files) != 1:
            raise EScriptoriumError("python_setup_failed", "The pyvips source archive layout is invalid.")
        setup_file = setup_files[0]
        setup_file.write_text(
            "# Bottled Kraken: force pyvips ABI mode for distro libvips compatibility.\n"
            "from setuptools import setup\n"
            "setup()\n",
            encoding="utf-8",
        )
        self.manager._run(
            [
                str(self.python), "-m", "pip", "install", "--no-input",
                "--no-build-isolation", "--no-deps", str(setup_file.parent),
            ],
            timeout=1800,
            code="python_setup_failed",
        )

    def _install_modern_pyvips(self) -> None:
        """Install a Python-3.12 and modern distro-libvips compatible binding."""
        try:
            self.manager._run(
                [
                    str(self.python), "-m", "pip", "install", "--no-input",
                    "--no-build-isolation", "--no-deps",
                    f"pyvips=={ESCRIPTORIUM_PYVIPS_VERSION}",
                ],
                timeout=1800,
                code="python_setup_failed",
            )
        except EScriptoriumError as exc:
            self.manager.logger.warning(
                "Standard pyvips %s build failed; retrying in ABI mode: %s",
                ESCRIPTORIUM_PYVIPS_VERSION,
                self._compact_python_error(exc.detail),
            )
            self._install_pyvips_abi_fallback()

    def _create_venv(self, progress: ProgressCallback | None) -> None:
        self.manager._progress(progress, "create_runtime", 48, str(self.paths.runtime))
        if not self.python.is_file():
            python_command = self._system_python_command()
            self.manager._run(
                [shutil.which(python_command) or python_command, "-m", "venv", str(self.paths.venv)],
                timeout=600,
                code="python_setup_failed",
            )
        requirements = self.paths.source / "app" / "requirements.txt"
        if not requirements.is_file():
            raise EScriptoriumError("archive_invalid", str(requirements))
        compat_requirements = self._write_compat_requirements(requirements)
        self.manager._progress(progress, "install_python", 52, str(compat_requirements))
        try:
            self.manager._run(
                [
                    str(self.python), "-m", "pip", "install", "--no-input",
                    "--upgrade", "pip", "setuptools<82", "wheel", "cffi", "pkgconfig",
                ],
                timeout=1200,
                code="python_setup_failed",
            )

            # Install a matching CPU-only torch/torchvision pair first.  The
            # exact installed versions are then constrained during the main
            # dependency resolution so PyPI cannot replace them with CUDA
            # wheels merely because a newer generic torch release exists.
            torch_index = os.environ.get(
                "BOTTLED_KRAKEN_ESCRIPTORIUM_TORCH_INDEX_URL",
                ESCRIPTORIUM_TORCH_CPU_INDEX_URL,
            ).strip()
            if not torch_index:
                torch_index = ESCRIPTORIUM_TORCH_CPU_INDEX_URL
            self.manager._run(
                [
                    str(self.python), "-m", "pip", "install", "--no-input",
                    "--index-url", torch_index,
                    f"torch=={ESCRIPTORIUM_TORCH_VERSION}",
                    f"torchvision=={ESCRIPTORIUM_TORCHVISION_VERSION}",
                ],
                timeout=14400,
                code="python_setup_failed",
            )
            constraints = self._write_torch_constraints()

            self.manager._run(
                [
                    str(self.python), "-m", "pip", "install", "--no-input",
                    "--no-build-isolation", "--extra-index-url", torch_index,
                    "--constraint", str(constraints), "-r", str(compat_requirements),
                ],
                timeout=14400,
                code="python_setup_failed",
            )
            self._install_modern_pyvips()
            self.manager._run(
                [
                    str(self.python), "-c",
                    (
                        "import importlib.metadata as m; import pyvips; "
                        f"assert m.version('pyvips') == '{ESCRIPTORIUM_PYVIPS_VERSION}'; "
                        "assert pyvips.Image.black(1, 1).width == 1"
                    ),
                ],
                timeout=120,
                env=self.manager._runtime_env(),
                code="python_setup_failed",
            )
        except EScriptoriumError as exc:
            if exc.code != "python_setup_failed":
                raise
            raise EScriptoriumError(
                "python_setup_failed",
                self._compact_python_error(exc.detail),
            ) from exc

    def _build_frontend(self, progress: ProgressCallback | None) -> None:
        front = self.paths.source / "front"
        self.manager._progress(progress, "build_frontend", 68, str(front))
        npm = shutil.which("npm") or "npm"
        install_command = [npm, "ci"] if (front / "package-lock.json").is_file() else [npm, "install"]
        node_env = {"NODE_OPTIONS": "--openssl-legacy-provider"}
        self.manager._run(
            install_command,
            cwd=front,
            timeout=3600,
            env=node_env,
            code="frontend_build_failed",
        )
        self.manager._run(
            [npm, "run", "production"],
            cwd=front,
            timeout=3600,
            env=node_env,
            code="frontend_build_failed",
        )

    def _pg_bin(self, command: str) -> str:
        result = self.manager._run(
            [shutil.which("pg_config") or "pg_config", "--bindir"],
            timeout=30,
            code="database_setup_failed",
        )
        bindir = Path(_clean_output(result.stdout))
        executable = bindir / command
        return str(executable if executable.is_file() else command)

    def _postgres_running(self) -> bool:
        data = self.paths.data / "postgres"
        if not (data / "PG_VERSION").is_file():
            return False
        result = self.manager._run(
            [self._pg_bin("pg_ctl"), "-D", str(data), "status"],
            timeout=20,
            check=False,
        )
        return result.returncode == 0

    def _postgres_socket_dir(self) -> Path:
        """Return a short, private and user-writable Unix-socket directory.

        Fedora's system socket directory is not writable by a desktop user,
        while the full Bottled Kraken data path can exceed Linux' 107-byte
        Unix-socket limit.  Runtime sockets therefore live below
        ``XDG_RUNTIME_DIR`` (or a UID-scoped temporary fallback), not below
        the persistent application data directory.
        """
        socket_dir = _short_postgres_socket_dir(self.platform_id)
        socket_dir.mkdir(parents=True, exist_ok=True)
        try:
            socket_dir.chmod(0o700)
        except OSError:
            pass
        return socket_dir

    @staticmethod
    def _read_text_tail(path: Path, *, max_chars: int = 12000) -> str:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""
        return text[-max(1, int(max_chars)):].strip()

    def _read_postgres_diagnostics(
        self,
        pg_ctl_log: Path,
        *,
        started_at: float | None = None,
        max_chars: int = 12000,
    ) -> str:
        """Read pg_ctl output and the newest PostgreSQL collector log.

        With ``logging_collector`` enabled, ``pg_ctl -l`` often contains only
        a redirect notice.  The actionable startup failure is written to
        ``PGDATA/log/postgresql-*.log`` instead.
        """
        sections: list[str] = []
        primary = self._read_text_tail(pg_ctl_log, max_chars=max_chars)
        if primary:
            sections.append(f"--- postgres.log ---\n{primary}")

        collector_dir = self.paths.data / "postgres" / "log"
        try:
            candidates = [path for path in collector_dir.glob("postgresql-*.log") if path.is_file()]
            if not candidates:
                candidates = [path for path in collector_dir.glob("*.log") if path.is_file()]
            newest = max(candidates, key=lambda path: path.stat().st_mtime) if candidates else None
        except OSError:
            newest = None
        if newest is not None:
            try:
                recent_enough = started_at is None or newest.stat().st_mtime >= float(started_at) - 10.0
            except OSError:
                recent_enough = False
            collector = self._read_text_tail(newest, max_chars=max_chars) if recent_enough else ""
            if collector and collector not in primary:
                sections.append(f"--- {newest.name} ---\n{collector}")
        return "\n\n".join(sections).strip()

    def _start_postgres(self) -> None:
        if self._postgres_running():
            return
        data = self.paths.data / "postgres"
        self.paths.logs.mkdir(parents=True, exist_ok=True)
        log = self.paths.logs / "postgres.log"
        socket_dir = self._postgres_socket_dir()
        options = (
            f"-p {POSTGRES_PORT} -h 127.0.0.1 "
            f"-k {shlex.quote(str(socket_dir))}"
        )
        started_at = time.time()
        try:
            self.manager._run(
                [
                    self._pg_bin("pg_ctl"), "-D", str(data), "-l", str(log),
                    "-o", options, "start", "-w",
                ],
                timeout=180,
                code="database_setup_failed",
            )
        except EScriptoriumError as exc:
            postgres_detail = self._read_postgres_diagnostics(log, started_at=started_at)
            detail = exc.detail
            if postgres_detail:
                detail = f"{detail}\n\n{postgres_detail}" if detail else postgres_detail
            raise EScriptoriumError("database_setup_failed", detail) from exc

    def _stop_postgres(self) -> None:
        if not self._postgres_running():
            return
        self.manager._run(
            [self._pg_bin("pg_ctl"), "-D", str(self.paths.data / "postgres"), "stop", "-m", "fast", "-w"],
            timeout=120,
            check=False,
        )

    def _redis_running(self) -> bool:
        cli = shutil.which("redis-cli") or "redis-cli"
        result = self.manager._run(
            [cli, "-h", "127.0.0.1", "-p", str(REDIS_PORT), "ping"],
            timeout=10,
            check=False,
        )
        return result.returncode == 0 and "PONG" in _clean_output(result.stdout).upper()

    def _start_redis(self) -> None:
        if self._redis_running():
            return
        data = self.paths.data / "redis"
        data.mkdir(parents=True, exist_ok=True)
        config = self.paths.config / "redis.conf"
        config.write_text(
            "\n".join((
                "bind 127.0.0.1",
                "protected-mode yes",
                f"port {REDIS_PORT}",
                f"dir {data}",
                "dbfilename dump.rdb",
                f"pidfile {self.paths.pid_dir / 'redis.pid'}",
                f"logfile {self.paths.logs / 'redis.log'}",
                "daemonize yes",
                "save 900 1",
                "save 300 10",
                "",
            )),
            encoding="utf-8",
        )
        self.manager._run(
            [shutil.which("redis-server") or "redis-server", str(config)],
            timeout=60,
            code="database_setup_failed",
        )

    def _stop_redis(self) -> None:
        if not self._redis_running():
            return
        self.manager._run(
            [shutil.which("redis-cli") or "redis-cli", "-h", "127.0.0.1", "-p", str(REDIS_PORT), "shutdown", "save"],
            timeout=30,
            check=False,
        )

    def _initialize_database(self, progress: ProgressCallback | None) -> None:
        data = self.paths.data / "postgres"
        self.manager._progress(progress, "initialize_database", 76, str(data))
        if not (data / "PG_VERSION").is_file():
            data.mkdir(parents=True, exist_ok=True)
            self.manager._run(
                [
                    self._pg_bin("initdb"), "-D", str(data), "-U", "bk_escriptorium",
                    "--auth-local=trust", "--auth-host=trust", "--encoding=UTF8",
                ],
                timeout=300,
                code="database_setup_failed",
            )
        self._start_postgres()
        self._start_redis()
        createdb = self._pg_bin("createdb")
        check = self.manager._run(
            [
                self._pg_bin("psql"), "-h", "127.0.0.1", "-p", str(POSTGRES_PORT),
                "-U", "bk_escriptorium", "-d", "postgres", "-tAc",
                "SELECT 1 FROM pg_database WHERE datname='escriptorium'",
            ],
            timeout=30,
            code="database_setup_failed",
        )
        if _clean_output(check.stdout) != "1":
            self.manager._run(
                [createdb, "-h", "127.0.0.1", "-p", str(POSTGRES_PORT), "-U", "bk_escriptorium", "escriptorium"],
                timeout=60,
                code="database_setup_failed",
            )

    def _django(self, args: list[str], *, timeout: int = 1800) -> None:
        self.manager._run(
            [str(self.python), "manage.py", *args],
            cwd=self.paths.source / "app",
            timeout=timeout,
            env=self.manager._runtime_env(),
            code="database_setup_failed",
        )

    def _migrate(self, progress: ProgressCallback | None) -> None:
        self.manager._progress(progress, "migrate_database", 84, "")
        self._django(["migrate", "--noinput"], timeout=3600)
        self._django(["collectstatic", "--noinput"], timeout=1800)
        env = self.manager._parse_env(self.paths.env_file)
        username = env.get("DJANGO_SU_NAME", "admin").strip() or "admin"
        email = env.get("DJANGO_SU_EMAIL", "admin@localhost").strip() or "admin@localhost"
        password = env.get("DJANGO_SU_PASSWORD", "").strip()
        if not password:
            raise EScriptoriumError("database_setup_failed", "Missing administrator password")
        code = (
            "from django.contrib.auth import get_user_model;"
            "U=get_user_model();"
            f"n={username!r};e={email!r};p={password!r};"
            "u=U.objects.filter(username=n).first();"
            "legacy=U.objects.filter(username=n+'\r').first();"
            "u=u or legacy or U(username=n);"
            "u.username=n;u.email=e;u.is_active=True;u.is_staff=True;u.is_superuser=True;"
            "u.set_password(p);u.save();assert u.check_password(p)"
        )
        self._django(["shell", "-c", code], timeout=300)

    def install(self, progress: ProgressCallback | None, _values: Mapping[str, str]) -> None:
        self._install_system_packages(progress)
        self.manager._write_native_local_settings()
        self._create_venv(progress)
        self._build_frontend(progress)
        try:
            self._initialize_database(progress)
            self._migrate(progress)
        finally:
            self._stop_redis()
            self._stop_postgres()

    @staticmethod
    def _pid_alive(pid: int) -> bool:
        if pid <= 0:
            return False
        # ``kill(pid, 0)`` also succeeds for zombie processes on Linux. A
        # crashed Django or Celery child would then look alive until the PID is
        # reaped or reused, hiding the actual startup failure.
        stat_path = Path(f"/proc/{pid}/stat")
        try:
            fields = stat_path.read_text(encoding="utf-8", errors="replace").split()
            if len(fields) >= 3 and fields[2] in {"Z", "X"}:
                return False
        except OSError:
            pass
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def _read_pid(self, name: str) -> int:
        try:
            return int((self.paths.pid_dir / f"{name}.pid").read_text(encoding="utf-8").strip())
        except Exception:
            return 0

    def _log_tail(self, name: str, lines: int = 60) -> str:
        path = self.paths.logs / f"{name}.log"
        try:
            content = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return ""
        return "\n".join(content[-max(1, int(lines)):]).strip()

    def startup_failure_detail(self) -> str:
        for name in ("web", "celery"):
            pid = self._read_pid(name)
            if pid and not self._pid_alive(pid):
                detail = self._log_tail(name)
                return detail or f"{name} process exited before startup completed"
        return ""

    def diagnostic_tail(self) -> str:
        parts = []
        for name in ("web", "celery", "postgres", "redis"):
            tail = self._log_tail(name, 30)
            if tail:
                parts.append(f"[{name}]\n{tail}")
        return "\n\n".join(parts)[-12000:]

    def _start_process(self, name: str, command: list[str]) -> None:
        self.paths.pid_dir.mkdir(parents=True, exist_ok=True)
        self.paths.logs.mkdir(parents=True, exist_ok=True)
        pidfile = self.paths.pid_dir / f"{name}.pid"
        try:
            old_pid = int(pidfile.read_text(encoding="utf-8").strip())
        except Exception:
            old_pid = 0
        if self._pid_alive(old_pid):
            return
        log_path = self.paths.logs / f"{name}.log"
        log_handle = log_path.open("a", encoding="utf-8")
        try:
            process = subprocess.Popen(
                command,
                cwd=str(self.paths.source / "app"),
                stdin=subprocess.DEVNULL,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                env=self.manager._runtime_env(),
                start_new_session=True,
                close_fds=True,
            )
        except Exception as exc:
            raise EScriptoriumError("command_failed", str(exc)) from exc
        finally:
            log_handle.close()
        pidfile.write_text(str(process.pid), encoding="utf-8")
        time.sleep(0.8)
        if process.poll() is not None:
            pidfile.unlink(missing_ok=True)
            detail = self._log_tail(name)
            raise EScriptoriumError(
                "server_start_failed",
                detail or f"{name} exited with code {process.returncode}",
            )

    def _stop_process(self, name: str) -> None:
        pidfile = self.paths.pid_dir / f"{name}.pid"
        try:
            pid = int(pidfile.read_text(encoding="utf-8").strip())
        except Exception:
            pidfile.unlink(missing_ok=True)
            return
        if self._pid_alive(pid):
            try:
                os.killpg(pid, signal.SIGTERM)
            except OSError:
                try:
                    os.kill(pid, signal.SIGTERM)
                except OSError:
                    pass
            deadline = time.monotonic() + 12
            while time.monotonic() < deadline and self._pid_alive(pid):
                time.sleep(0.2)
            if self._pid_alive(pid):
                try:
                    os.killpg(pid, signal.SIGKILL)
                except OSError:
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except OSError:
                        pass
        pidfile.unlink(missing_ok=True)

    def start(self, progress: ProgressCallback | None) -> None:
        self.manager._progress(progress, "start_services", 42, "PostgreSQL / Redis")
        self._start_postgres()
        self._start_redis()
        self.manager._progress(progress, "start_services", 50, "Celery")
        self._start_process(
            "celery",
            [
                str(self.celery), "-A", "escriptorium", "worker", "-l", "INFO",
                "-E", "-Ofair", "--prefetch-multiplier", "1",
            ],
        )
        self.manager._progress(progress, "start_services", 54, "Django")
        self._start_process(
            "web",
            [str(self.python), "manage.py", "runserver", "127.0.0.1:8000", "--noreload"],
        )

    def stop(self, progress: ProgressCallback | None) -> None:
        self.manager._progress(progress, "stop_services", 25, "Django / Celery")
        self._stop_process("web")
        self._stop_process("celery")
        self.manager._progress(progress, "stop_services", 65, "Redis / PostgreSQL")
        self._stop_redis()
        self._stop_postgres()


class _WindowsWslBackend:
    """Windows backend using a private Ubuntu 24.04 WSL2 installation."""

    LINUX_ROOT = "/opt/bottled-kraken-escriptorium"
    LINUX_USER = "bk-escriptorium"

    def __init__(self, manager: EScriptoriumManager) -> None:
        self.manager = manager
        self.paths = manager.paths
        self.distro = os.environ.get(
            "BOTTLED_KRAKEN_ESCRIPTORIUM_WSL_DISTRO",
            ESCRIPTORIUM_WSL_DISTRIBUTION,
        ).strip() or ESCRIPTORIUM_WSL_DISTRIBUTION
        self._keepalive_process: subprocess.Popen[str] | None = None

    @staticmethod
    def _wsl_executable() -> str | None:
        if os.name != "nt" and not sys.platform.startswith("win"):
            return None
        system_root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
        candidates = [system_root / "System32" / "wsl.exe", system_root / "Sysnative" / "wsl.exe"]
        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)
        return shutil.which("wsl.exe") or shutil.which("wsl")

    def _wsl(self, args: list[str], *, timeout: int = 600, check: bool = True, code: str = "wsl_install_failed"):
        executable = self._wsl_executable()
        if not executable:
            raise EScriptoriumError("wsl_missing")
        return self.manager._run([executable, *args], timeout=timeout, check=check, code=code)

    def _installed_distros(self) -> set[str]:
        executable = self._wsl_executable()
        if not executable:
            return set()
        result = self.manager._run([executable, "--list", "--quiet"], timeout=30, check=False)
        return {line.strip() for line in _clean_output(result.stdout).splitlines() if line.strip()}

    @staticmethod
    def _wsl_missing_disk_detail(text: str) -> bool:
        normalized = _clean_output(text).casefold()
        return any(
            marker in normalized
            for marker in (
                "error_path_not_found",
                "0x80070003",
                "system cannot find the path",
                "system kann den angegebenen pfad nicht finden",
                "kann den angegebenen pfad nicht finden",
                "mountdisk",
                "createinstance/mountdisk",
                "ext4.vhdx",
            )
        )

    def _registered_wsl_distribution_is_usable(self) -> bool:
        result = self._wsl(
            ["--distribution", self.distro, "--user", "root", "--", "true"],
            timeout=60,
            check=False,
            code="wsl_install_failed",
        )
        if result.returncode == 0:
            return True

        detail = "\n".join(
            part for part in (_clean_output(result.stderr), _clean_output(result.stdout)) if part
        )
        if self._wsl_missing_disk_detail(detail):
            return False

        vhdx = self.paths.wsl_location / "ext4.vhdx"
        if not vhdx.is_file():
            return False

        raise EScriptoriumError("wsl_install_failed", detail or str(result.returncode))

    def _unregister_broken_wsl_distribution(self, progress: ProgressCallback | None, detail: str = "") -> None:
        self.manager._progress(progress, "install_wsl", 35, f"{self.distro} neu anlegen")
        result = self._wsl(
            ["--unregister", self.distro],
            timeout=600,
            check=False,
            code="wsl_install_failed",
        )
        if result.returncode != 0 and self.distro in self._installed_distros():
            message = _clean_output(result.stderr) or _clean_output(result.stdout) or detail or str(result.returncode)
            raise EScriptoriumError("wsl_install_failed", message)
        shutil.rmtree(self.paths.wsl_location, ignore_errors=True)

    @staticmethod
    def _wsl_image_architecture() -> str:
        machine = (
            os.environ.get("PROCESSOR_ARCHITEW6432")
            or os.environ.get("PROCESSOR_ARCHITECTURE")
            or platform_module.machine()
            or "amd64"
        ).casefold()
        return "arm64" if machine in {"arm64", "aarch64"} else "amd64"

    def _ensure_wsl_feature(self) -> None:
        executable = self._wsl_executable()
        if not executable:
            raise EScriptoriumError("wsl_missing")
        status = self.manager._run(
            [executable, "--status"], timeout=60, check=False, code="wsl_install_failed"
        )
        if status.returncode == 0:
            # A current Store WSL is required for reliable systemd support.
            # Updating is best-effort here: an already functional installation
            # must remain usable when Windows Update or the network is offline.
            self.manager._run(
                [executable, "--update", "--web-download"],
                timeout=3600,
                check=False,
                code="wsl_install_failed",
            )
            return
        script = self.paths.scripts / "enable_wsl.ps1"
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text(
            "$ErrorActionPreference = 'Stop'\n"
            "$args = @('--install','--no-distribution','--web-download')\n"
            "$p = Start-Process -FilePath 'wsl.exe' -ArgumentList $args -Verb RunAs -Wait -PassThru\n"
            "exit $p.ExitCode\n",
            encoding="utf-8-sig",
        )
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if not powershell:
            raise EScriptoriumError("wsl_missing", "PowerShell")
        result = self.manager._run(
            [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
            timeout=3600,
            check=False,
            code="wsl_install_failed",
        )
        if result.returncode in (3010, 1641):
            raise EScriptoriumError("restart_required", self.distro)
        if result.returncode != 0:
            detail = _clean_output(result.stderr) or _clean_output(result.stdout)
            raise EScriptoriumError("wsl_install_failed", detail or str(result.returncode))
        status = self.manager._run(
            [executable, "--status"], timeout=60, check=False, code="wsl_install_failed"
        )
        if status.returncode != 0:
            raise EScriptoriumError("restart_required", self.distro)

    def _download_wsl_rootfs(self, progress: ProgressCallback | None) -> Path:
        architecture = self._wsl_image_architecture()
        filename = f"ubuntu-noble-wsl-{architecture}-24.04lts.rootfs.tar.gz"
        url = f"{UBUNTU_WSL_IMAGE_BASE_URL}/{filename}"
        checksum_url = f"{UBUNTU_WSL_IMAGE_BASE_URL}/SHA256SUMS"
        self.paths.downloads.mkdir(parents=True, exist_ok=True)
        target = self.paths.downloads / filename
        try:
            with urlopen(Request(checksum_url, headers={"User-Agent": "BottledKraken/3.4"}), timeout=60) as response:
                sums = response.read().decode("utf-8", errors="replace")
        except Exception as exc:
            raise EScriptoriumError("wsl_install_failed", f"SHA256SUMS: {exc}") from exc
        expected = ""
        for line in sums.splitlines():
            parts = line.strip().split()
            if len(parts) >= 2 and parts[-1].lstrip("*") == filename:
                expected = parts[0].casefold()
                break
        if not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise EScriptoriumError("wsl_install_failed", f"SHA256SUMS: {filename}")

        def valid(path: Path) -> bool:
            if not path.is_file():
                return False
            digest = hashlib.sha256()
            try:
                with path.open("rb") as handle:
                    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                        digest.update(chunk)
            except OSError:
                return False
            return digest.hexdigest().casefold() == expected

        if valid(target):
            return target
        target.unlink(missing_ok=True)
        temporary = target.with_suffix(target.suffix + ".part")
        temporary.unlink(missing_ok=True)
        try:
            with urlopen(Request(url, headers={"User-Agent": "BottledKraken/3.4"}), timeout=90) as response, temporary.open("wb") as handle:
                total = int(response.headers.get("Content-Length") or 0)
                downloaded = 0
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    handle.write(chunk)
                    downloaded += len(chunk)
                    ratio = downloaded / total if total else 0.0
                    self.manager._progress(
                        progress,
                        "install_wsl",
                        min(46, 38 + int(ratio * 8)),
                        f"Ubuntu 24.04: {downloaded / (1024 * 1024):.1f} MiB",
                    )
            temporary.replace(target)
        except Exception as exc:
            temporary.unlink(missing_ok=True)
            raise EScriptoriumError("wsl_install_failed", str(exc)) from exc
        if not valid(target):
            target.unlink(missing_ok=True)
            raise EScriptoriumError("wsl_install_failed", f"SHA-256: {filename}")
        return target

    def _install_wsl_distribution(self, progress: ProgressCallback | None) -> None:
        if self.distro in self._installed_distros():
            if self._registered_wsl_distribution_is_usable():
                return
            self._unregister_broken_wsl_distribution(progress)
        self.manager._progress(progress, "install_wsl", 36, self.distro)
        self._ensure_wsl_feature()
        archive = self._download_wsl_rootfs(progress)
        self.paths.wsl_location.parent.mkdir(parents=True, exist_ok=True)
        if self.paths.wsl_location.exists():
            shutil.rmtree(self.paths.wsl_location, ignore_errors=True)
        self.paths.wsl_location.mkdir(parents=True, exist_ok=True)
        result = self._wsl(
            [
                "--import",
                self.distro,
                str(self.paths.wsl_location),
                str(archive),
                "--version",
                "2",
            ],
            timeout=3600,
            check=False,
            code="wsl_install_failed",
        )
        if result.returncode != 0:
            detail = _clean_output(result.stderr) or _clean_output(result.stdout)
            shutil.rmtree(self.paths.wsl_location, ignore_errors=True)
            raise EScriptoriumError("wsl_install_failed", detail or str(result.returncode))
        if self.distro not in self._installed_distros():
            raise EScriptoriumError("restart_required", self.distro)

    @staticmethod
    def _windows_path_to_wsl_mount_path(path: Path | str) -> str:
        """Convert a local Windows path to the default WSL automount path.

        Calling ``wslpath`` from ``wsl.exe -- wslpath C:\\...`` is fragile:
        the Windows backslashes can be consumed before they reach WSL, producing
        paths such as ``C:Users...``.  Bottled Kraken only passes local files it
        has just created below ``%LOCALAPPDATA%``, so the deterministic WSL2
        automount mapping is sufficient and avoids an extra dependency on
        ``wslu``/``wslpath``.
        """
        raw = str(path).strip()
        if raw.startswith("\\\\?\\UNC\\"):
            raise EScriptoriumError("wsl_install_failed", raw)
        if raw.startswith("\\\\?\\"):
            raw = raw[4:]

        win_path = PureWindowsPath(raw)
        drive = (win_path.drive or "").rstrip(":").lower()
        if not re.fullmatch(r"[a-z]", drive):
            raise EScriptoriumError("wsl_install_failed", raw)

        parts = [part for part in win_path.parts[1:] if part not in {"", "\\", "/"}]
        return "/".join(["", "mnt", drive, *parts]).replace("\\", "/")

    def _windows_to_wsl_path(self, path: Path) -> str:
        return self._windows_path_to_wsl_mount_path(path)

    def _write_wsl_script(self) -> Path:
        script = self.paths.scripts / "escriptorium_wsl.sh"
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text(_WSL_SCRIPT, encoding="utf-8", newline="\n")
        return script

    def _run_action(self, action: str, *, timeout: int = 7200) -> subprocess.CompletedProcess[str]:
        script = self._write_wsl_script()
        script_path = self._windows_to_wsl_path(script)
        source_path = self._windows_to_wsl_path(self.paths.source)
        config_path = self._windows_to_wsl_path(self.paths.config)
        credentials_path = self._windows_to_wsl_path(self.paths.credentials)
        return self._wsl(
            [
                "--distribution", self.distro, "--user", "root", "--",
                "bash", script_path, action, source_path, config_path, credentials_path,
            ],
            timeout=timeout,
            code="wsl_install_failed" if action == "install" else "command_failed",
        )

    def _start_wsl_keepalive(self) -> None:
        """Keep the private WSL2 distribution alive while services are running.

        On Windows, systemd services inside WSL do not reliably keep an imported
        distribution alive once the last foreground ``wsl.exe`` invocation has
        exited.  A long-running Windows-side ``wsl.exe`` process prevents WSL
        from tearing down the instance moments after Bottled Kraken has opened
        the browser.  The helper exits by itself when the web and Celery
        services are stopped.
        """
        if self._keepalive_process and self._keepalive_process.poll() is None:
            return
        executable = self._wsl_executable()
        if not executable:
            raise EScriptoriumError("wsl_missing")
        self.paths.logs.mkdir(parents=True, exist_ok=True)
        log_path = self.paths.logs / "wsl-keepalive.log"
        command = [
            executable,
            "--distribution",
            self.distro,
            "--user",
            "root",
            "--",
            "bash",
            "-lc",
            (
                "deadline=$((SECONDS+240)); "
                "while [ $SECONDS -lt $deadline ]; do "
                "if systemctl is-active --quiet bk-escriptorium-web.service "
                "&& systemctl is-active --quiet bk-escriptorium-celery.service; then break; fi; "
                "if systemctl is-failed --quiet bk-escriptorium-web.service "
                "|| systemctl is-failed --quiet bk-escriptorium-celery.service; then exit 0; fi; "
                "sleep 1; "
                "done; "
                "while systemctl is-active --quiet bk-escriptorium-web.service "
                "|| systemctl is-active --quiet bk-escriptorium-celery.service; do sleep 15; done"
            ),
        ]
        self.manager.logger.info("Starting WSL keepalive command: %s", self.manager._command_text(command))
        log_handle = log_path.open("a", encoding="utf-8")
        try:
            creationflags = _subprocess_flags()
            if os.name == "nt":
                creationflags |= int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
            self._keepalive_process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=bk_clean_child_env(),
                creationflags=creationflags,
            )
        except Exception as exc:
            raise EScriptoriumError("command_failed", str(exc)) from exc
        finally:
            log_handle.close()

    def _stop_wsl_keepalive(self) -> None:
        process = self._keepalive_process
        self._keepalive_process = None
        if process is not None:
            EScriptoriumManager._terminate_process(process)

    def is_installed(self) -> bool:
        if self.distro not in self._installed_distros():
            return False
        try:
            result = self._wsl(
                ["--distribution", self.distro, "--user", "root", "--", "test", "-f", f"{self.LINUX_ROOT}/config/installed.json"],
                timeout=30,
                check=False,
            )
            return result.returncode == 0 and self.paths.install_marker.is_file()
        except EScriptoriumError:
            return False

    def status(self) -> EScriptoriumStatus:
        available = bool(self._wsl_executable())
        installed = self.is_installed() if available else False
        return EScriptoriumStatus(
            installed=installed,
            running=installed and self.manager.server_is_ready(timeout=0.25),
            platform_id=ESCRIPTORIUM_PLATFORM_WINDOWS_WSL,
            platform_compatible=True,
            prerequisites_available=available,
            server_url=self.manager.server_url,
            install_dir=str(self.paths.profile),
            credentials_file=str(self.paths.credentials),
            detail=self.distro,
        )

    def install(self, progress: ProgressCallback | None, _values: Mapping[str, str]) -> None:
        self._install_wsl_distribution(progress)
        self.manager._progress(progress, "configure_wsl", 44, self.distro)
        # Ensure systemd is enabled. Ubuntu installed by current WSL versions
        # uses it by default; the explicit file keeps older supported systems
        # deterministic.
        check = self._wsl(
            ["--distribution", self.distro, "--user", "root", "--", "bash", "-lc", "test \"$(ps -p 1 -o comm= | tr -d '[:space:]')\" = systemd"],
            timeout=60,
            check=False,
        )
        if check.returncode != 0:
            self._wsl(
                [
                    "--distribution", self.distro, "--user", "root", "--", "bash", "-lc",
                    "printf '[boot]\\nsystemd=true\\n' > /etc/wsl.conf",
                ],
                timeout=60,
            )
            executable = self._wsl_executable()
            if executable:
                self.manager._run([executable, "--terminate", self.distro], timeout=120, check=False)
            time.sleep(2)
        self.manager._progress(progress, "copy_source", 48, self.distro)
        self._run_action("install", timeout=10800)
        marker = self.paths.profile / "WINDOWS_WSL_RUNTIME.txt"
        marker.write_text(
            "eScriptorium runs inside the dedicated WSL distribution.\n"
            f"Distribution: {self.distro}\n"
            f"WSL storage: {self.paths.wsl_location}\n"
            f"Linux path: {self.LINUX_ROOT}\n"
            f"Windows access: \\\\wsl.localhost\\{self.distro}\\opt\\bottled-kraken-escriptorium\n",
            encoding="utf-8",
        )

    def start(self, progress: ProgressCallback | None) -> None:
        self.manager._progress(progress, "start_services", 45, self.distro)
        self._run_action("start", timeout=900)
        self._start_wsl_keepalive()

    def stop(self, progress: ProgressCallback | None) -> None:
        self.manager._progress(progress, "stop_services", 30, self.distro)
        try:
            self._run_action("stop", timeout=600)
        finally:
            self._stop_wsl_keepalive()

    def diagnostic_tail(self) -> str:
        if self.distro not in self._installed_distros():
            return ""
        result = self._wsl(
            [
                "--distribution", self.distro, "--user", "root", "--",
                "journalctl", "--no-pager", "-n", "80",
                "-u", "bk-escriptorium-web.service",
                "-u", "bk-escriptorium-celery.service",
            ],
            timeout=60,
            check=False,
        )
        return _clean_output(result.stdout)[-12000:]

    def startup_failure_detail(self) -> str:
        if self.distro not in self._installed_distros():
            return ""
        result = self._wsl(
            [
                "--distribution", self.distro, "--user", "root", "--",
                "systemctl", "is-failed",
                "bk-escriptorium-web.service",
                "bk-escriptorium-celery.service",
            ],
            timeout=30,
            check=False,
        )
        if result.returncode == 0:
            return self.diagnostic_tail() or "WSL eScriptorium service failed"
        return ""


_WSL_SCRIPT = r'''#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-}"
SOURCE_INPUT="${2:-}"
CONFIG_INPUT="${3:-}"
CREDENTIALS_INPUT="${4:-}"
ROOT="/opt/bottled-kraken-escriptorium"
USER_NAME="bk-escriptorium"
APP="$ROOT/source/app"
VENV="$ROOT/runtime/venv"
DATA="$ROOT/data"
CONFIG="$ROOT/config"
LOGS="$ROOT/logs"
PG_PORT="54329"
REDIS_PORT="6389"

as_user() {
    runuser -u "$USER_NAME" -- env HOME="$ROOT/home" "$@"
}

sync_runtime_files() {
    mkdir -p "$ROOT" "$CONFIG"
    cp -f "$CONFIG_INPUT/runtime.env" "$CONFIG/runtime.env"
    cp -f "$CREDENTIALS_INPUT" "$ROOT/credentials.txt"
    # Files created by the Windows host can use CRLF.  Bash would otherwise
    # export values such as admin\r and set an unusable Django password.
    sed -i 's/\r$//' "$CONFIG/runtime.env" "$ROOT/credentials.txt"
    chmod 0600 "$CONFIG/runtime.env" "$ROOT/credentials.txt"
    if id "$USER_NAME" >/dev/null 2>&1; then
        chown "$USER_NAME:$USER_NAME" "$CONFIG/runtime.env" "$ROOT/credentials.txt"
    fi
}

wait_for_postgres() {
    for _ in $(seq 1 60); do
        if "$(pg_config --bindir)/pg_isready" -h 127.0.0.1 -p "$PG_PORT" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done
    echo "PostgreSQL did not become ready on port $PG_PORT" >&2
    return 1
}

ensure_admin_user() {
    as_user "$ROOT/runtime/run-env.sh" "$VENV/bin/python" "$APP/manage.py" shell -c "from django.contrib.auth import get_user_model; import os; U=get_user_model(); n=(os.environ.get('DJANGO_SU_NAME') or 'admin').strip(); e=(os.environ.get('DJANGO_SU_EMAIL') or 'admin@localhost').strip(); p=(os.environ.get('DJANGO_SU_PASSWORD') or '').strip(); assert n and p, 'Missing eScriptorium administrator credentials'; u=U.objects.filter(username=n).first(); legacy=U.objects.filter(username=n+'\r').first(); u=u or legacy or U(username=n); u.username=n; u.email=e; u.is_active=True; u.is_staff=True; u.is_superuser=True; u.set_password(p); u.save(); assert u.check_password(p)"
}

start_all() {
    sync_runtime_files
    write_env_wrapper
    systemctl start bk-escriptorium-postgres.service bk-escriptorium-redis.service
    wait_for_postgres
    ensure_admin_user
    systemctl start bk-escriptorium.target
}

write_local_settings() {
    cat > "$APP/escriptorium/local_settings.py" <<PYSETTINGS
# Generated by Bottled Kraken. Manual edits may be overwritten.
import os
from .settings import *  # noqa: F401,F403


def _bk_env(name, default=''):
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip()
    for _ in range(3):
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1].strip()
            continue
        if len(value) >= 4 and value.startswith('\\"') and value.endswith('\\"'):
            value = value[2:-2].strip()
            continue
        break
    return value or default


DEBUG = True
MEDIA_ROOT = '$DATA/media'
STATIC_ROOT = '$DATA/static'
EMAIL_FILE_PATH = '$DATA/emails'
DISABLE_ELASTICSEARCH = True
DATABASES['default'].update({
    'HOST': _bk_env('SQL_HOST', '127.0.0.1'),
    'PORT': _bk_env('SQL_PORT', '$PG_PORT'),
    'NAME': _bk_env('POSTGRES_DB', 'escriptorium'),
    'USER': _bk_env('POSTGRES_USER', 'bk_escriptorium'),
    'PASSWORD': _bk_env('POSTGRES_PASSWORD', ''),
})
PYSETTINGS
}

write_env_wrapper() {
    cat > "$ROOT/runtime/run-env.sh" <<'SHENV'
#!/usr/bin/env bash
set -a
source /opt/bottled-kraken-escriptorium/config/runtime.env
set +a
export DJANGO_SETTINGS_MODULE=escriptorium.local_settings
export FRONTEND_DIR=/opt/bottled-kraken-escriptorium/source/front/dist
export PATH=/opt/bottled-kraken-escriptorium/runtime/venv/bin:$PATH
exec "$@"
SHENV
    chmod 0755 "$ROOT/runtime/run-env.sh"
}

install_units() {
    PG_BINDIR="$(pg_config --bindir)"
    cat > /etc/systemd/system/bk-escriptorium-postgres.service <<UNIT
[Unit]
Description=Bottled Kraken eScriptorium PostgreSQL
After=network.target
[Service]
Type=simple
User=$USER_NAME
Environment=HOME=$ROOT/home
RuntimeDirectory=bk-escriptorium-postgres
RuntimeDirectoryMode=0700
ExecStart=$PG_BINDIR/postgres -D $DATA/postgres -p $PG_PORT -h 127.0.0.1 -k /run/bk-escriptorium-postgres
ExecStop=$PG_BINDIR/pg_ctl -D $DATA/postgres stop -m fast
Restart=on-failure
[Install]
WantedBy=bk-escriptorium.target
UNIT
    cat > /etc/systemd/system/bk-escriptorium-redis.service <<UNIT
[Unit]
Description=Bottled Kraken eScriptorium Redis
After=network.target
[Service]
Type=simple
User=$USER_NAME
ExecStart=/usr/bin/redis-server $CONFIG/redis.conf --daemonize no
Restart=on-failure
[Install]
WantedBy=bk-escriptorium.target
UNIT
    cat > /etc/systemd/system/bk-escriptorium-celery.service <<UNIT
[Unit]
Description=Bottled Kraken eScriptorium Celery
After=bk-escriptorium-postgres.service bk-escriptorium-redis.service
Requires=bk-escriptorium-postgres.service bk-escriptorium-redis.service
[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$APP
Environment=HOME=$ROOT/home
ExecStart=$ROOT/runtime/run-env.sh $VENV/bin/celery -A escriptorium worker -l INFO -E -Ofair --prefetch-multiplier 1
Restart=on-failure
[Install]
WantedBy=bk-escriptorium.target
UNIT
    cat > /etc/systemd/system/bk-escriptorium-web.service <<UNIT
[Unit]
Description=Bottled Kraken eScriptorium web server
After=bk-escriptorium-postgres.service bk-escriptorium-redis.service
Requires=bk-escriptorium-postgres.service bk-escriptorium-redis.service
[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$APP
Environment=HOME=$ROOT/home
ExecStart=$ROOT/runtime/run-env.sh $VENV/bin/python manage.py runserver 0.0.0.0:8000 --noreload
Restart=on-failure
[Install]
WantedBy=bk-escriptorium.target
UNIT
    cat > /etc/systemd/system/bk-escriptorium.target <<UNIT
[Unit]
Description=Bottled Kraken eScriptorium services
Requires=bk-escriptorium-postgres.service bk-escriptorium-redis.service bk-escriptorium-celery.service bk-escriptorium-web.service
After=bk-escriptorium-postgres.service bk-escriptorium-redis.service
[Install]
WantedBy=multi-user.target
UNIT
    systemctl daemon-reload
}

install_all() {
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get upgrade -y
    apt-get install -y postgresql postgresql-client postgresql-contrib redis-server git curl gettext libvips-dev libvips-tools nodejs npm python3 python3-venv python3-dev python3-pip build-essential default-jre default-jdk ant libpq-dev pkg-config libglib2.0-dev libexpat1-dev libjpeg-dev zlib1g-dev libtiff-dev libxml2-dev libxslt1-dev libopenjp2-7-dev libffi-dev jpegoptim pngcrush netcat-openbsd
    if ! id "$USER_NAME" >/dev/null 2>&1; then
        useradd --system --home-dir "$ROOT/home" --create-home --shell /bin/bash "$USER_NAME"
    fi
    mkdir -p "$ROOT" "$ROOT/runtime" "$DATA/postgres" "$DATA/redis" "$DATA/media" "$DATA/static" "$DATA/emails" "$CONFIG" "$LOGS"
    rm -rf "$ROOT/source.new"
    mkdir -p "$ROOT/source.new"
    cp -a "$SOURCE_INPUT"/. "$ROOT/source.new"/
    rm -rf "$ROOT/source"
    mv "$ROOT/source.new" "$ROOT/source"
    mkdir -p "$APP/escriptorium/logs"
    sync_runtime_files
    write_local_settings
    chown -R "$USER_NAME:$USER_NAME" "$ROOT"
    if [ ! -x "$VENV/bin/python" ]; then
        as_user python3 -m venv "$VENV"
    fi
    as_user "$VENV/bin/python" -m pip install --no-input --upgrade pip 'setuptools<82' wheel cffi pkgconfig
    COMPAT_REQUIREMENTS="$ROOT/runtime/requirements-bottled-kraken.txt"
    TORCH_CONSTRAINTS="$ROOT/runtime/constraints-bottled-kraken.txt"
    as_user "$VENV/bin/python" - "$APP/requirements.txt" "$COMPAT_REQUIREMENTS" <<'PYREQ'
from pathlib import Path
import re
import sys
source = Path(sys.argv[1])
target = Path(sys.argv[2])
excluded = {"pyvips", "torch", "torchvision", "torchaudio"}
kept = []
for line in source.read_text(encoding="utf-8").splitlines():
    stripped = line.strip()
    match = re.match(r"([A-Za-z0-9][A-Za-z0-9_.-]*)", stripped) if stripped and not stripped.startswith(("#", "-")) else None
    name = re.sub(r"[-_.]+", "-", match.group(1)).casefold() if match else ""
    if name not in excluded:
        kept.append(line)
target.write_text(
    "# Generated by Bottled Kraken from eScriptorium app/requirements.txt.\n"
    "# pyvips and PyTorch are installed separately for compatibility.\n"
    + "\n".join(kept).rstrip() + "\n",
    encoding="utf-8",
)
PYREQ
    TORCH_INDEX="${BOTTLED_KRAKEN_ESCRIPTORIUM_TORCH_INDEX_URL:-https://download.pytorch.org/whl/cpu}"
    TORCH_VERSION="2.12.0"
    TORCHVISION_VERSION="0.27.0"
    as_user "$VENV/bin/python" -m pip install --no-input --index-url "$TORCH_INDEX" "torch==$TORCH_VERSION" "torchvision==$TORCHVISION_VERSION"
    as_user "$VENV/bin/python" - "$TORCH_CONSTRAINTS" <<'PYTORCH'
from pathlib import Path
import importlib.metadata as metadata
import sys
torch_version = metadata.version("torch")
torchvision_version = metadata.version("torchvision")
assert torch_version.split("+", 1)[0] == "2.12.0", torch_version
assert torchvision_version.split("+", 1)[0] == "0.27.0", torchvision_version
Path(sys.argv[1]).write_text(
    f"torch=={torch_version}\ntorchvision=={torchvision_version}\n",
    encoding="utf-8",
)
PYTORCH
    as_user "$VENV/bin/python" -m pip install --no-input --no-build-isolation --extra-index-url "$TORCH_INDEX" --constraint "$TORCH_CONSTRAINTS" -r "$COMPAT_REQUIREMENTS"
    as_user "$VENV/bin/python" -m pip install --no-input --no-build-isolation --no-deps 'pyvips==3.1.1'
    as_user "$VENV/bin/python" -c "import importlib.metadata as m; import pyvips; assert m.version('pyvips') == '3.1.1'; assert pyvips.Image.black(1, 1).width == 1"
    if [ -f "$ROOT/source/front/package-lock.json" ]; then
        as_user env NODE_OPTIONS=--openssl-legacy-provider npm --prefix "$ROOT/source/front" ci
    else
        as_user env NODE_OPTIONS=--openssl-legacy-provider npm --prefix "$ROOT/source/front" install
    fi
    as_user env NODE_OPTIONS=--openssl-legacy-provider npm --prefix "$ROOT/source/front" run production
    if [ ! -f "$DATA/postgres/PG_VERSION" ]; then
        PG_BINDIR="$(pg_config --bindir)"
        as_user "$PG_BINDIR/initdb" -D "$DATA/postgres" -U bk_escriptorium --auth-local=trust --auth-host=trust --encoding=UTF8
    fi
    cat > "$CONFIG/redis.conf" <<REDIS
bind 127.0.0.1
protected-mode yes
port $REDIS_PORT
dir $DATA/redis
dbfilename dump.rdb
logfile $LOGS/redis.log
daemonize no
save 900 1
save 300 10
REDIS
    write_env_wrapper
    chown -R "$USER_NAME:$USER_NAME" "$ROOT"
    install_units
    systemctl start bk-escriptorium-postgres.service bk-escriptorium-redis.service
    wait_for_postgres
    if ! as_user "$(pg_config --bindir)/psql" -h 127.0.0.1 -p "$PG_PORT" -U bk_escriptorium -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='escriptorium'" | grep -q 1; then
        as_user "$(pg_config --bindir)/createdb" -h 127.0.0.1 -p "$PG_PORT" -U bk_escriptorium escriptorium
    fi
    as_user "$ROOT/runtime/run-env.sh" "$VENV/bin/python" "$APP/manage.py" migrate --noinput
    as_user "$ROOT/runtime/run-env.sh" "$VENV/bin/python" "$APP/manage.py" collectstatic --noinput
    ensure_admin_user
    systemctl stop bk-escriptorium-redis.service bk-escriptorium-postgres.service
    printf '{"installed": true}\n' > "$CONFIG/installed.json"
    chown "$USER_NAME:$USER_NAME" "$CONFIG/installed.json"
}

case "$ACTION" in
    install) install_all ;;
    start) start_all ;;
    stop) systemctl stop bk-escriptorium-web.service bk-escriptorium-celery.service bk-escriptorium-redis.service bk-escriptorium-postgres.service bk-escriptorium.target || true ;;
    status) systemctl is-active --quiet bk-escriptorium-web.service ;;
    *) echo "Unknown action: $ACTION" >&2; exit 2 ;;
esac
'''


__all__ = [
    "ESCRIPTORIUM_ARCHIVE_URL",
    "ESCRIPTORIUM_DEFAULT_REF",
    "ESCRIPTORIUM_DOCUMENTATION_URL",
    "ESCRIPTORIUM_PLATFORM_FEDORA",
    "ESCRIPTORIUM_PLATFORM_MINT",
    "ESCRIPTORIUM_PLATFORM_WINDOWS_WSL",
    "ESCRIPTORIUM_PYVIPS_VERSION",
    "ESCRIPTORIUM_PYVIPS_SDIST_URL",
    "ESCRIPTORIUM_TORCH_CPU_INDEX_URL",
    "ESCRIPTORIUM_REPOSITORY_URL",
    "ESCRIPTORIUM_SERVER_URL",
    "ESCRIPTORIUM_SUPPORTED_PLATFORMS",
    "ESCRIPTORIUM_WSL_DISTRIBUTION",
    "UBUNTU_WSL_IMAGE_BASE_URL",
    "EScriptoriumError",
    "EScriptoriumManager",
    "EScriptoriumPaths",
    "EScriptoriumStatus",
    "detect_escriptorium_platform",
    "open_external_url",
    "open_local_path",
    "platform_compatibility",
]
