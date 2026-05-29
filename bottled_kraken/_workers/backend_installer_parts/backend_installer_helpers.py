from __future__ import annotations
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple
from bottled_kraken.version_config import (
    APP_DIR_NAME,
    APP_VERSION,
    BACKEND_DEFS,
    KRAKEN_REQUIREMENT,
    PYTHON_BIDI_REQUIREMENT,
)
def _fallback_tr(key: str, *args) -> str:
    fallback = {
        "backend_install_title_nvidia": "Install NVIDIA CUDA backend",
        "backend_install_title_rocm": "Install AMD ROCm backend",
        "backend_install_intro_nvidia": (
            "This installs a separate NVIDIA CUDA backend with its own Python environment. "
            "The Bottled Kraken CPU one-file application is not modified."
        ),
        "backend_install_intro_rocm": (
            "This installs a separate AMD ROCm backend with its own Python environment. "
            "The Bottled Kraken CPU one-file application is not modified."
        ),
        "backend_install_target": "Installation target:",
        "backend_install_warning": "Several gigabytes may be downloaded. An internet connection is required.",
        "backend_install_force": "Remove existing backend first and reinstall",
        "backend_install_start": "Start installation",
        "backend_install_close": "Close",
        "backend_install_log": "Installation log:",
        "backend_install_running": "Installation is already running.",
        "backend_install_success": "Backend installation completed successfully.",
        "backend_install_failed": "Backend installation failed.",
        "backend_install_finished": "Installation finished.",
        "backend_install_choose_python_failed": "No suitable Python interpreter was found.",
        "backend_install_platform": "Detected platform:",
        "backend_install_unsupported": "This backend is not supported on this operating system yet.",
    }
    text = fallback.get(key, key)
    if args:
        try:
            return text.format(*args)
        except Exception:
            return text
    return text
def _call_tr(tr_func: Optional[Callable[..., str]], key: str, *args) -> str:
    if tr_func is None:
        return _fallback_tr(key, *args)
    try:
        return tr_func(key, *args)
    except Exception:
        return _fallback_tr(key, *args)
def backend_root() -> Path:
    custom = os.environ.get("BOTTLED_KRAKEN_BACKENDS_DIR", "").strip()
    if custom:
        return Path(custom).expanduser()
    if sys.platform.startswith("win"):
        base = os.environ.get("LOCALAPPDATA", "").strip()
        if base:
            return Path(base) / APP_DIR_NAME / "backends"
        return Path.home() / "AppData" / "Local" / APP_DIR_NAME / "backends"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_DIR_NAME / "backends"
    xdg = os.environ.get("XDG_DATA_HOME", "").strip()
    if xdg:
        return Path(xdg).expanduser() / APP_DIR_NAME / "backends"
    return Path.home() / ".local" / "share" / APP_DIR_NAME / "backends"
def backend_dir(kind: str) -> Path:
    meta = BACKEND_DEFS.get(kind, BACKEND_DEFS["nvidia-cuda"])
    return backend_root() / meta["dir"]
def detect_linux_distro() -> str:
    os_release = Path("/etc/os-release")
    data: Dict[str, str] = {}
    if os_release.is_file():
        try:
            for raw in os_release.read_text(encoding="utf-8", errors="ignore").splitlines():
                if "=" not in raw:
                    continue
                key, value = raw.split("=", 1)
                data[key.strip()] = value.strip().strip('"')
        except Exception:
            pass
    distro_id = (data.get("ID") or "").lower()
    like = (data.get("ID_LIKE") or "").lower()
    if "fedora" in distro_id or "fedora" in like:
        return "linux-fedora"
    if "linuxmint" in distro_id or "ubuntu" in distro_id or "debian" in distro_id:
        return "linux-mint-debian"
    if "ubuntu" in like or "debian" in like:
        return "linux-mint-debian"
    return "linux"
def detect_platform_id() -> str:
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    if sys.platform.startswith("linux"):
        return detect_linux_distro()
    return sys.platform
def _no_console_kwargs() -> Dict[str, object]:
    if not sys.platform.startswith("win"):
        return {}
    kwargs: Dict[str, object] = {}
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
        kwargs["startupinfo"] = startupinfo
    except Exception:
        pass
    return kwargs
def _run_capture(cmd: List[str], timeout: int = 15) -> Tuple[int, str]:
    try:
        p = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            **_no_console_kwargs(),
        )
        return p.returncode, p.stdout.strip()
    except Exception as exc:
        return 1, repr(exc)
def _python_candidates() -> List[List[str]]:
    forced = os.environ.get("BK_BACKEND_PYTHON", "").strip()
    if forced:
        return [[forced]]
    if sys.platform.startswith("win"):
        candidates: List[List[str]] = []
        py_launcher = shutil.which("py")
        if py_launcher:
            for ver in ("3.12", "3.11", "3.10", "3.13"):
                candidates.append([py_launcher, f"-{ver}"])
            candidates.append([py_launcher, "-3"])
        for exe in ("python", "python3"):
            path = shutil.which(exe)
            if path:
                candidates.append([path])
        return candidates
    candidates = []
    for exe in ("python3.12", "python3.11", "python3.10", "python3.13", "python3"):
        path = shutil.which(exe)
        if path:
            candidates.append([path])
    return candidates
def _check_python(cmd: List[str]) -> Optional[str]:
    code = (
        "import sys; "
        "v=sys.version_info[:2]; "
        "raise SystemExit(0 if (3,10) <= v < (3,14) else 1)"
    )
    rc, _ = _run_capture(cmd + ["-c", code], timeout=10)
    if rc != 0:
        return None
    rc, out = _run_capture(cmd + ["-c", "import sys; print('.'.join(map(str, sys.version_info[:3])))"], timeout=10)
    if rc == 0 and out:
        return out.strip()
    return "python"
def choose_python() -> Tuple[Optional[List[str]], str]:
    for cmd in _python_candidates():
        ver = _check_python(cmd)
        if ver:
            return cmd, ver
    return None, ""
def venv_python_path(venv_dir: Path) -> Path:
    if sys.platform.startswith("win"):
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"
