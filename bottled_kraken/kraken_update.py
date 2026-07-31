from __future__ import annotations

import importlib.abc
import importlib.metadata
import importlib.machinery
import json
import os
import queue
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import threading
import time
import urllib.request
from urllib.parse import quote
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Callable, Sequence

from bottled_kraken.runtime_cli import application_cli_command, hidden_process_kwargs
from bottled_kraken.user_storage import bottled_kraken_runtime_path

KRAKEN_REPOSITORY = "mittagessen/kraken"
KRAKEN_DEFAULT_BRANCH = "main"
_STATE_FILE = "bottled-kraken-kraken-state.json"
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_MAX_ARCHIVE_BYTES = 1024 * 1024 * 1024
_OVERLAY_FINDER = None


class KrakenUpdateError(RuntimeError):
    pass


@dataclass(frozen=True)
class KrakenCommit:
    sha: str
    message: str
    html_url: str


@dataclass(frozen=True)
class KrakenRelease:
    sha: str
    version: str
    tag_name: str
    name: str
    html_url: str


@dataclass(frozen=True)
class KrakenUpdateResult:
    sha: str
    version: str
    changed: bool
    overlay_dir: str


def kraken_update_root() -> Path:
    return bottled_kraken_runtime_path("kraken-update")


def kraken_overlay_dir() -> Path:
    return kraken_update_root() / "current"


def kraken_overlay_state_path(base: Path | None = None) -> Path:
    return (kraken_overlay_dir() if base is None else Path(base)) / _STATE_FILE


def _read_state(base: Path | None = None) -> dict:
    path = kraken_overlay_state_path(base)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


class _KrakenOverlayFinder(importlib.abc.MetaPathFinder):
    """Resolve only ``kraken`` from the validated external update directory."""

    def __init__(self, overlay: Path):
        self.overlay = Path(overlay).resolve()

    def find_spec(self, fullname, path=None, target=None):
        if fullname == "kraken":
            return importlib.machinery.PathFinder.find_spec(fullname, [str(self.overlay)])
        if fullname.startswith("kraken."):
            return importlib.machinery.PathFinder.find_spec(fullname, path)
        return None


def _install_overlay_finder(overlay: Path) -> _KrakenOverlayFinder:
    global _OVERLAY_FINDER
    resolved = Path(overlay).resolve()
    if isinstance(_OVERLAY_FINDER, _KrakenOverlayFinder):
        if _OVERLAY_FINDER.overlay == resolved and _OVERLAY_FINDER in sys.meta_path:
            return _OVERLAY_FINDER
        try:
            sys.meta_path.remove(_OVERLAY_FINDER)
        except ValueError:
            pass
    finder = _KrakenOverlayFinder(resolved)
    sys.meta_path.insert(0, finder)
    _OVERLAY_FINDER = finder
    return finder


def activate_kraken_overlay() -> str | None:
    """Activate a validated Kraken source overlay ahead of bundled modules."""
    if str(os.environ.get("BOTTLED_KRAKEN_DISABLE_KRAKEN_OVERLAY", "")).strip() == "1":
        return None
    overlay = kraken_overlay_dir()
    state = _read_state(overlay)
    package = overlay / "kraken" / "__init__.py"
    if not package.is_file() or not _SHA_RE.match(str(state.get("sha", ""))):
        return None
    value = str(overlay.resolve())
    if value not in sys.path:
        sys.path.insert(0, value)
    _install_overlay_finder(overlay)
    os.environ["BOTTLED_KRAKEN_ACTIVE_KRAKEN_OVERLAY"] = value
    return value


def current_kraken_summary() -> dict:
    state = _read_state()
    overlay_present = kraken_overlay_dir().joinpath("kraken", "__init__.py").is_file()
    if state and overlay_present:
        version = str(state.get("version") or "unknown")
    else:
        try:
            version = importlib.metadata.version("kraken")
        except importlib.metadata.PackageNotFoundError:
            version = "unknown"
    return {
        "version": version,
        "sha": str(state.get("sha", "")),
        "overlay_active": bool(os.environ.get("BOTTLED_KRAKEN_ACTIVE_KRAKEN_OVERLAY")),
        "overlay_pending": bool(state and overlay_present),
    }


def _github_request(url: str) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "Bottled-Kraken-Kraken-Updater",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )


def _github_json(url: str, *, timeout: float) -> dict:
    try:
        with urllib.request.urlopen(_github_request(url), timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8", errors="strict"))
    except Exception as exc:
        raise KrakenUpdateError(f"GitHub request failed: {exc}") from exc
    if not isinstance(payload, dict):
        raise KrakenUpdateError("GitHub returned an invalid response.")
    return payload


def _release_version_from_tag(tag_name: str) -> str:
    value = str(tag_name or "").strip()
    value = re.sub(r"^(?:kraken[-_ ]*)?v", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^kraken[-_ ]*", "", value, flags=re.IGNORECASE)
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,3}(?:[A-Za-z0-9.+-]*)?", value):
        raise KrakenUpdateError(f"GitHub returned an invalid Kraken release tag: {tag_name!r}")
    return value


def fetch_latest_kraken_commit(timeout: float = 20.0) -> KrakenCommit:
    url = f"https://api.github.com/repos/{KRAKEN_REPOSITORY}/commits/{KRAKEN_DEFAULT_BRANCH}"
    payload = _github_json(url, timeout=timeout)
    sha = str(payload.get("sha", "")).lower()
    if not _SHA_RE.match(sha):
        raise KrakenUpdateError("GitHub returned no valid Kraken commit ID.")
    commit = payload.get("commit") if isinstance(payload.get("commit"), dict) else {}
    return KrakenCommit(
        sha=sha,
        message=str(commit.get("message", "")).splitlines()[0].strip(),
        html_url=str(payload.get("html_url", "")),
    )


def fetch_latest_kraken_release(timeout: float = 20.0) -> KrakenRelease:
    """Return the newest published, non-prerelease Kraken release.

    Updating from a release tag gives the UI a real package version and avoids
    presenting an opaque ``main@<commit>`` development identifier as a version.
    """
    release_url = f"https://api.github.com/repos/{KRAKEN_REPOSITORY}/releases/latest"
    payload = _github_json(release_url, timeout=timeout)
    if payload.get("draft") or payload.get("prerelease"):
        raise KrakenUpdateError("GitHub returned no stable Kraken release.")
    tag_name = str(payload.get("tag_name", "")).strip()
    version = _release_version_from_tag(tag_name)
    commit_url = (
        f"https://api.github.com/repos/{KRAKEN_REPOSITORY}/commits/"
        f"{quote(tag_name, safe='')}"
    )
    commit_payload = _github_json(commit_url, timeout=timeout)
    sha = str(commit_payload.get("sha", "")).lower()
    if not _SHA_RE.match(sha):
        raise KrakenUpdateError("GitHub returned no valid commit for the latest Kraken release.")
    return KrakenRelease(
        sha=sha,
        version=version,
        tag_name=tag_name,
        name=str(payload.get("name") or tag_name).strip(),
        html_url=str(payload.get("html_url", "")),
    )


def kraken_archive_url(sha: str) -> str:
    value = str(sha).lower()
    if not _SHA_RE.match(value):
        raise KrakenUpdateError("Invalid Kraken commit ID.")
    return f"https://api.github.com/repos/{KRAKEN_REPOSITORY}/tarball/{value}"


def _download_kraken_archive(
    sha: str,
    destination: Path,
    *,
    on_progress: Callable[[int, str], None],
    cancel_event: threading.Event,
    timeout: float = 60.0,
) -> None:
    request = _github_request(kraken_archive_url(sha))
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response, destination.open("wb") as out:
            try:
                expected = int(response.headers.get("Content-Length") or 0)
            except (TypeError, ValueError):
                expected = 0
            written = 0
            while True:
                if cancel_event.is_set():
                    raise KrakenUpdateError("cancelled")
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > _MAX_ARCHIVE_BYTES:
                    raise KrakenUpdateError("The Kraken source archive is unexpectedly large.")
                out.write(chunk)
                if expected > 0:
                    percent = 15 + min(45, int((written / expected) * 45))
                    on_progress(percent, f"GitHub: {written // 1024 // 1024} MiB downloaded …")
            if written == 0:
                raise KrakenUpdateError("GitHub returned an empty Kraken source archive.")
    except KrakenUpdateError:
        raise
    except Exception as exc:
        raise KrakenUpdateError(f"Kraken source download failed: {exc}") from exc


def _safe_extract_kraken_package(
    archive_path: Path,
    target: Path,
    *,
    cancel_event: threading.Event,
) -> None:
    """Extract only the repository's ``kraken/`` package without links."""
    target = Path(target).resolve()
    target.mkdir(parents=True, exist_ok=True)
    extracted_bytes = 0
    found_package = False
    try:
        archive = tarfile.open(archive_path, mode="r:*")
    except (OSError, tarfile.TarError) as exc:
        raise KrakenUpdateError(f"The Kraken source archive is invalid: {exc}") from exc
    with archive:
        for member in archive:
            if cancel_event.is_set():
                raise KrakenUpdateError("cancelled")
            parts = PurePosixPath(member.name).parts
            if len(parts) < 2 or parts[1] != "kraken":
                continue
            relative_parts = parts[1:]
            if any(part in {"", ".", ".."} for part in relative_parts):
                raise KrakenUpdateError("Unsafe path in Kraken source archive.")
            relative = Path(*relative_parts)
            destination = (target / relative).resolve()
            try:
                destination.relative_to(target)
            except ValueError as exc:
                raise KrakenUpdateError("Unsafe path in Kraken source archive.") from exc
            if member.issym() or member.islnk():
                raise KrakenUpdateError("Links are not allowed in the Kraken source archive.")
            if member.isdir():
                destination.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile():
                continue
            extracted_bytes += max(0, int(member.size))
            if extracted_bytes > _MAX_ARCHIVE_BYTES:
                raise KrakenUpdateError("The extracted Kraken package is unexpectedly large.")
            source = archive.extractfile(member)
            if source is None:
                raise KrakenUpdateError(f"Could not read {member.name} from the Kraken archive.")
            destination.parent.mkdir(parents=True, exist_ok=True)
            with source, destination.open("wb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)
            found_package = True
    if not found_package or not (target / "kraken" / "__init__.py").is_file():
        raise KrakenUpdateError("The GitHub archive contains no usable Kraken package.")


def kraken_validation_command(target: Path) -> list[str]:
    return application_cli_command(["--bk-validate-kraken-overlay", str(Path(target).resolve())])


def _terminate(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    try:
        if os.name == "nt":
            process.terminate()
        else:
            os.killpg(process.pid, signal.SIGTERM)
    except Exception:
        try:
            process.terminate()
        except Exception:
            return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            if os.name == "nt":
                process.kill()
            else:
                os.killpg(process.pid, signal.SIGKILL)
        except Exception:
            process.kill()


def _run_streaming(
    command: Sequence[str],
    *,
    on_detail: Callable[[str], None],
    cancel_event: threading.Event,
    env: dict[str, str] | None = None,
) -> str:
    kwargs = hidden_process_kwargs()
    if os.name != "nt":
        kwargs["start_new_session"] = True
    process = subprocess.Popen(
        list(command),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        bufsize=1,
        **kwargs,
    )
    lines: list[str] = []
    output_queue: queue.Queue[str | None] = queue.Queue()
    assert process.stdout is not None

    def _read_output() -> None:
        try:
            for line in process.stdout:
                output_queue.put(line)
        finally:
            output_queue.put(None)

    reader = threading.Thread(target=_read_output, name="kraken-update-output", daemon=True)
    reader.start()
    finished = False
    while not finished:
        if cancel_event.is_set():
            _terminate(process)
            reader.join(timeout=1)
            raise KrakenUpdateError("cancelled")
        try:
            item = output_queue.get(timeout=0.1)
        except queue.Empty:
            if process.poll() is not None and not reader.is_alive():
                break
            continue
        if item is None:
            finished = True
            continue
        clean = item.rstrip()
        lines.append(clean)
        on_detail(clean)
    reader.join(timeout=1)
    returncode = int(process.wait())
    output = "\n".join(lines)
    if returncode != 0:
        tail = "\n".join(lines[-30:]).strip()
        raise KrakenUpdateError(tail or f"Command failed ({returncode}).")
    return output


def validate_kraken_overlay_cli(path: str) -> int:
    target = Path(path).resolve()
    try:
        from bottled_kraken.windows_coremltools_stub import install_windows_coremltools_stub
        install_windows_coremltools_stub()
        sys.path.insert(0, str(target))
        _install_overlay_finder(target)
        from kraken import blla, containers, rpred, serialization  # noqa: F401
        from kraken.lib import models, vgsl  # noqa: F401
        import kraken

        origin = Path(kraken.__file__).resolve()
        if target not in origin.parents:
            raise RuntimeError(f"Kraken was not loaded from the update directory: {origin}")
        print(json.dumps({"ok": True, "origin": str(origin)}, ensure_ascii=True))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=True))
        return 2


def install_latest_kraken(
    *,
    on_progress: Callable[[int, str], None],
    cancel_event: threading.Event,
) -> KrakenUpdateResult:
    on_progress(5, "GitHub: checking the latest published Kraken release …")
    release = fetch_latest_kraken_release()
    state = _read_state()
    if state.get("sha") == release.sha and kraken_overlay_dir().is_dir():
        if str(state.get("version") or "") != release.version:
            state.update(
                {
                    "version": release.version,
                    "release_tag": release.tag_name,
                    "release_name": release.name,
                    "release_url": release.html_url,
                }
            )
            kraken_overlay_state_path().write_text(
                json.dumps(state, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        return KrakenUpdateResult(
            sha=release.sha,
            version=release.version,
            changed=False,
            overlay_dir=str(kraken_overlay_dir()),
        )
    if cancel_event.is_set():
        raise KrakenUpdateError("cancelled")

    root = kraken_update_root()
    root.mkdir(parents=True, exist_ok=True)
    archive_path = root / f"source-{uuid.uuid4().hex}.tar.gz"
    staging = root / f"staging-{uuid.uuid4().hex}"
    staging.mkdir(parents=True, exist_ok=False)
    try:
        on_progress(15, f"Kraken {release.version} is being downloaded from GitHub …")
        _download_kraken_archive(
            release.sha,
            archive_path,
            on_progress=on_progress,
            cancel_event=cancel_event,
        )
        on_progress(65, "The Kraken source package is being prepared …")
        _safe_extract_kraken_package(archive_path, staging, cancel_event=cancel_event)

        on_progress(80, "The new Kraken version is being validated against Bottled Kraken …")
        validation_output = _run_streaming(
            kraken_validation_command(staging),
            on_detail=lambda line: on_progress(85, line),
            cancel_event=cancel_event,
            env=dict(
                os.environ,
                BOTTLED_KRAKEN_DISABLE_KRAKEN_OVERLAY="1",
                PYTHONUTF8="1",
                PYTHONIOENCODING="utf-8",
            ),
        )
        payload = None
        for line in reversed(validation_output.splitlines()):
            try:
                candidate = json.loads(line)
            except ValueError:
                continue
            if isinstance(candidate, dict) and "ok" in candidate:
                payload = candidate
                break
        if not payload or not payload.get("ok"):
            raise KrakenUpdateError(
                str((payload or {}).get("error") or "Kraken compatibility validation failed.")
            )

        version = release.version
        state_payload = {
            "repository": KRAKEN_REPOSITORY,
            "release_tag": release.tag_name,
            "release_name": release.name,
            "release_url": release.html_url,
            "sha": release.sha,
            "version": version,
            "installed_at": datetime.now(timezone.utc).isoformat(),
            "python": f"{sys.version_info.major}.{sys.version_info.minor}",
        }
        kraken_overlay_state_path(staging).write_text(
            json.dumps(state_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        current = kraken_overlay_dir()
        backup = root / f"backup-{uuid.uuid4().hex}"
        if current.exists():
            current.rename(backup)
        try:
            staging.rename(current)
        except Exception:
            if backup.exists() and not current.exists():
                backup.rename(current)
            raise
        shutil.rmtree(backup, ignore_errors=True)
        on_progress(100, "Kraken was updated. Restart required.")
        return KrakenUpdateResult(release.sha, version, True, str(current))
    finally:
        try:
            archive_path.unlink()
        except OSError:
            pass
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


__all__ = [
    "KRAKEN_DEFAULT_BRANCH",
    "KRAKEN_REPOSITORY",
    "KrakenCommit",
    "KrakenRelease",
    "KrakenUpdateError",
    "KrakenUpdateResult",
    "activate_kraken_overlay",
    "current_kraken_summary",
    "fetch_latest_kraken_commit",
    "fetch_latest_kraken_release",
    "install_latest_kraken",
    "kraken_archive_url",
    "kraken_overlay_dir",
    "kraken_validation_command",
    "validate_kraken_overlay_cli",
]
