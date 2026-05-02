"""Integrated GPU backend installer for Bottled Kraken.

The CPU one-file application stays unchanged. This module installs optional
external GPU OCR backends into the user's data directory and writes the backend
metadata that external_backend_ocr.py can discover.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from .external_backend_ocr import (
    EXTERNAL_KRAKEN_WORKER_SOURCE,
    clear_external_ocr_backend_cache,
)


APP_DIR_NAME = "BottledKraken"
APP_VERSION = "3.1"

BACKEND_DEFS: Dict[str, Dict[str, str]] = {
    "nvidia-cuda": {
        "name": "Bottled Kraken NVIDIA CUDA Backend",
        "short_name": "NVIDIA CUDA",
        "dir": "nvidia-cuda",
        "torch_index": "cu128",
        "torch": "2.10.0",
        "torchvision": "0.25.0",
    },
    "amd-rocm": {
        "name": "Bottled Kraken AMD ROCm Backend",
        "short_name": "AMD ROCm",
        "dir": "amd-rocm",
        "torch_index": "rocm7.1",
        "torch": "2.10.0",
        "torchvision": "0.25.0",
    },
}


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
    """Verhindert kurz aufpoppende CMD-Fenster bei subprocess-Aufrufen unter Windows."""
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
            for ver in ("3.13", "3.12", "3.11", "3.10"):
                candidates.append([py_launcher, f"-{ver}"])
            candidates.append([py_launcher, "-3"])
        for exe in ("python", "python3"):
            path = shutil.which(exe)
            if path:
                candidates.append([path])
        return candidates

    candidates = []
    for exe in ("python3.13", "python3.12", "python3.11", "python3.10", "python3"):
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


class BackendInstallerWorker(QThread):
    line = Signal(str)
    finished_ok = Signal(bool, str)

    def __init__(self, kind: str, force: bool = False, parent=None):
        super().__init__(parent)
        self.kind = kind
        self.force = bool(force)
        self._cancel_requested = False

    def cancel(self):
        self._cancel_requested = True

    def _emit(self, text: str):
        self.line.emit(str(text))

    def _run_cmd(self, cmd: List[str], cwd: Optional[Path] = None):
        if self._cancel_requested:
            raise RuntimeError("Cancelled.")

        display = " ".join(f'"{x}"' if " " in str(x) else str(x) for x in cmd)
        self._emit(f"$ {display}")

        env = os.environ.copy()
        env.setdefault("PYTHONUTF8", "1")
        env.setdefault("PYTHONIOENCODING", "utf-8")
        env.setdefault("LANG", "C.UTF-8")
        env.setdefault("LC_ALL", "C.UTF-8")

        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            env=env,
            **_no_console_kwargs(),
        )

        assert proc.stdout is not None
        for raw in proc.stdout:
            if self._cancel_requested:
                try:
                    proc.terminate()
                except Exception:
                    pass
                raise RuntimeError("Cancelled.")
            self._emit(raw.rstrip("\n"))

        rc = proc.wait()
        if rc != 0:
            raise RuntimeError(f"Command failed with exit code {rc}: {display}")

    def _write_worker(self, worker_path: Path):
        worker_path.write_text(EXTERNAL_KRAKEN_WORKER_SOURCE, encoding="utf-8")
        try:
            worker_path.chmod(0o755)
        except Exception:
            pass

    def _write_backend_info(self, target_dir: Path, py: Path, worker: Path, torch_index: str):
        meta = BACKEND_DEFS[self.kind]
        info = {
            "name": meta["name"],
            "app_version": APP_VERSION,
            "backend": self.kind,
            "python": str(py),
            "worker": str(worker),
            "torch": meta["torch"],
            "torchvision": meta["torchvision"],
            "pytorch_index": f"https://download.pytorch.org/whl/{torch_index}",
            "installed_at": datetime.now().astimezone().isoformat(),
            "installed_by": "Bottled Kraken integrated backend installer",
            "platform": detect_platform_id(),
        }
        (target_dir / "backend_info.json").write_text(
            json.dumps(info, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def run(self):
        try:
            if self.kind not in BACKEND_DEFS:
                raise RuntimeError(f"Unknown backend kind: {self.kind}")

            platform_id = detect_platform_id()
            self._emit(f"Platform: {platform_id}")
            self._emit(f"Target backend: {self.kind}")

            if self.kind == "amd-rocm" and not sys.platform.startswith("linux"):
                raise RuntimeError("AMD ROCm backend installation is currently supported only on Linux.")

            meta = BACKEND_DEFS[self.kind]
            target_dir = backend_dir(self.kind)
            venv_dir = target_dir / ".venv"
            py_path = venv_python_path(venv_dir)
            worker_path = target_dir / "worker_kraken_backend.py"

            self._emit(f"Install target: {target_dir}")

            if target_dir.exists() and self.force:
                self._emit("Removing existing backend directory...")
                shutil.rmtree(target_dir, ignore_errors=True)

            target_dir.mkdir(parents=True, exist_ok=True)

            py_cmd, py_ver = choose_python()
            if not py_cmd:
                if sys.platform.startswith("win"):
                    hint = (
                        "No suitable Python interpreter found. Install Python 3.10-3.13 first "
                        "and enable the Python launcher or add Python to PATH."
                    )
                else:
                    hint = (
                        "No suitable Python interpreter found. Install Python 3.10-3.13 first "
                        "(Fedora: sudo dnf install python3 / Linux Mint: sudo apt install python3-venv python3-pip)."
                    )
                raise RuntimeError(hint)

            self._emit(f"Using Python: {' '.join(py_cmd)} ({py_ver})")

            if not py_path.is_file():
                self._emit("Creating virtual environment...")
                self._run_cmd(py_cmd + ["-m", "venv", str(venv_dir)])
            else:
                self._emit("Using existing virtual environment.")

            if not py_path.is_file():
                raise RuntimeError(f"Virtual environment Python was not created: {py_path}")

            pip_cmd = [str(py_path), "-m", "pip"]

            self._emit("Upgrading pip tooling...")
            self._run_cmd(pip_cmd + ["install", "--upgrade", "pip", "setuptools", "wheel"])

            torch_index = meta["torch_index"]
            if self.kind == "nvidia-cuda":
                torch_index = os.environ.get("BK_CUDA_INDEX", torch_index).strip() or torch_index
                if torch_index not in {"cu126", "cu128", "cu130"}:
                    raise RuntimeError(f"Unsupported CUDA wheel index: {torch_index}")
            elif self.kind == "amd-rocm":
                torch_index = os.environ.get("BK_ROCM_INDEX", torch_index).strip() or torch_index
                if not torch_index.startswith("rocm"):
                    raise RuntimeError(f"Unsupported ROCm wheel index: {torch_index}")

            self._emit(f"Installing PyTorch backend wheels from {torch_index}...")
            self._run_cmd(
                pip_cmd + [
                    "install",
                    "--no-cache-dir",
                    "--force-reinstall",
                    f"torch=={meta['torch']}",
                    f"torchvision=={meta['torchvision']}",
                    "--index-url",
                    f"https://download.pytorch.org/whl/{torch_index}",
                ]
            )

            self._emit("Installing Kraken runtime dependencies...")
            deps = ["kraken==7.0.1", "pyarrow", "Pillow", "numpy"]
            # Kraken imports coremltools in its VGSL layer stack on current builds.
            # It is safe on Linux; on Windows it may be unavailable, so try it separately below.
            self._run_cmd(pip_cmd + ["install", "--no-cache-dir", "--upgrade"] + deps)

            self._emit("Installing optional coremltools dependency...")
            try:
                self._run_cmd(pip_cmd + ["install", "--no-cache-dir", "--upgrade", "coremltools"])
            except Exception as exc:
                self._emit(f"[!] coremltools could not be installed: {exc}")
                self._emit("[!] Continuing; the backend self-test will show whether Kraken can import successfully.")

            self._emit("Writing Bottled Kraken backend worker...")
            self._write_worker(worker_path)
            self._write_backend_info(target_dir, py_path, worker_path, torch_index)

            self._emit("Running backend self-test...")
            self._run_cmd([str(py_path), str(worker_path), "--self-test", "--backend-kind", self.kind])

            clear_external_ocr_backend_cache()
            self.finished_ok.emit(True, "ok")
        except Exception as exc:
            clear_external_ocr_backend_cache()
            self._emit(f"[!] {exc}")
            self.finished_ok.emit(False, str(exc))


class BackendInstallDialog(QDialog):
    install_finished = Signal(bool, str)

    def __init__(self, kind: str, tr_func: Optional[Callable[..., str]] = None, parent=None):
        super().__init__(parent)
        self.kind = kind
        self.tr_func = tr_func
        self.worker: Optional[BackendInstallerWorker] = None

        self.setWindowTitle(self._dialog_title())
        self.resize(760, 520)

        self.title_label = QLabel(f"<b>{self._dialog_title()}</b>")
        self.title_label.setTextFormat(Qt.RichText)
        self.info_label = QLabel(self._intro_text())
        self.info_label.setWordWrap(True)
        self.target_label = QLabel(f"{self._tr('backend_install_target')}<br><code>{backend_dir(kind)}</code>")
        self.target_label.setTextFormat(Qt.RichText)
        self.target_label.setWordWrap(True)
        self.warning_label = QLabel(self._tr("backend_install_warning"))
        self.warning_label.setWordWrap(True)

        self.force_checkbox = QCheckBox(self._tr("backend_install_force"))
        self.log_edit = QPlainTextEdit()
        self.log_edit.setReadOnly(True)

        self.buttons = QDialogButtonBox()
        self.start_button = QPushButton(self._tr("backend_install_start"))
        self.close_button = QPushButton(self._tr("backend_install_close"))
        self.buttons.addButton(self.start_button, QDialogButtonBox.ActionRole)
        self.buttons.addButton(self.close_button, QDialogButtonBox.RejectRole)
        self.start_button.clicked.connect(self.start_install)
        self.close_button.clicked.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title_label)
        layout.addWidget(self.info_label)
        layout.addWidget(self.target_label)
        layout.addWidget(self.warning_label)
        layout.addWidget(self.force_checkbox)
        layout.addWidget(QLabel(self._tr("backend_install_log")))
        layout.addWidget(self.log_edit, 1)
        layout.addWidget(self.buttons)

    def _tr(self, key: str, *args) -> str:
        return _call_tr(self.tr_func, key, *args)

    def _dialog_title(self) -> str:
        if self.kind == "amd-rocm":
            return self._tr("backend_install_title_rocm")
        return self._tr("backend_install_title_nvidia")

    def _intro_text(self) -> str:
        if self.kind == "amd-rocm":
            return self._tr("backend_install_intro_rocm")
        return self._tr("backend_install_intro_nvidia")

    def _append(self, text: str):
        self.log_edit.appendPlainText(str(text).rstrip())

    def start_install(self):
        if self.worker is not None and self.worker.isRunning():
            QMessageBox.warning(self, self._tr("backend_install_failed"), self._tr("backend_install_running"))
            return

        self.start_button.setEnabled(False)
        self.force_checkbox.setEnabled(False)
        self.worker = BackendInstallerWorker(self.kind, force=self.force_checkbox.isChecked(), parent=self)
        self.worker.line.connect(self._append)
        self.worker.finished_ok.connect(self._finished)
        self.worker.start()

    def _finished(self, ok: bool, message: str):
        self.start_button.setEnabled(True)
        self.force_checkbox.setEnabled(True)
        self.install_finished.emit(bool(ok), self.kind)
        if ok:
            self._append(self._tr("backend_install_success"))
            QMessageBox.information(self, self._tr("backend_install_finished"), self._tr("backend_install_success"))
        else:
            self._append(self._tr("backend_install_failed"))
            QMessageBox.warning(self, self._tr("backend_install_failed"), message or self._tr("backend_install_failed"))

    def reject(self):
        if self.worker is not None and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                self._tr("backend_install_close"),
                self._tr("backend_install_running"),
            )
            if reply != QMessageBox.Yes:
                return
            self.worker.cancel()
        super().reject()
