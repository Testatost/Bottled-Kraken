import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from PySide6.QtCore import QThread, Signal
from bottled_kraken._workers.external_backend_ocr import EXTERNAL_KRAKEN_WORKER_SOURCE, clear_external_ocr_backend_cache
from bottled_kraken._workers.backend_installer_parts.backend_installer_helpers import (
    APP_VERSION,
    BACKEND_DEFS,
    KRAKEN_REQUIREMENT,
    PYTHON_BIDI_REQUIREMENT,
    backend_dir,
    choose_python,
    detect_platform_id,
    venv_python_path,
)
from bottled_kraken._workers.backend_installer_parts.backend_installer_helpers import _no_console_kwargs, _run_capture
from bottled_kraken.version_config import (
    NVIDIA_TORCH_VERSION,
    NVIDIA_TORCHVISION_VERSION,
)
from bottled_kraken.translation import translation
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
            raise RuntimeError(translation.translate(translation.DEFAULT_LANGUAGE, "backend_install_cancelled_short"))
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
                raise RuntimeError(translation.translate(translation.DEFAULT_LANGUAGE, "backend_install_cancelled_short"))
            self._emit(raw.rstrip("\n"))
        rc = proc.wait()
        if rc != 0:
            raise RuntimeError(translation.translate(translation.DEFAULT_LANGUAGE, "backend_install_command_failed", rc, display))
    def _write_worker(self, worker_path: Path):
        worker_path.write_text(EXTERNAL_KRAKEN_WORKER_SOURCE, encoding="utf-8")
        try:
            worker_path.chmod(0o755)
        except Exception:
            pass

    def _pytorch_index_sort_key(self, token: str):
        token = str(token or "").strip().lower()
        if token.startswith("cu"):
            return (1, int(re.sub(r"\D", "", token) or "0"))
        if token.startswith("rocm"):
            nums = [int(x) for x in re.findall(r"\d+", token)]
            return (2, nums)
        return (0, token)

    def _fetch_available_pytorch_indexes(self, prefix: str) -> List[str]:
        url = "https://download.pytorch.org/whl/"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": f"BottledKraken/{APP_VERSION} backend-installer"},
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            html = response.read().decode("utf-8", "replace")
        prefix = str(prefix or "").lower()
        if prefix == "cu":
            pattern = r"(?<![a-z0-9])cu\d{3,4}(?![a-z0-9])"
        elif prefix == "rocm":
            pattern = r"(?<![a-z0-9])rocm\d+(?:\.\d+)+(?![a-z0-9])"
        else:
            return []
        return sorted(set(m.group(0).lower() for m in re.finditer(pattern, html, re.I)), key=self._pytorch_index_sort_key)

    def _resolve_torch_index(self, default_index: str) -> str:
        if self.kind == "nvidia-cuda":
            env_name = "BK_CUDA_INDEX"
            prefix = "cu"
            label = "CUDA"
            env_value = os.environ.get(env_name, "").strip().lower()
            if env_value:
                if not re.fullmatch(r"cu\d{3,4}", env_value):
                    raise RuntimeError(translation.translate(translation.DEFAULT_LANGUAGE, "backend_install_unsupported_cuda_index", env_value))
                self._emit(f"Using {label} wheel index from {env_name}: {env_value}")
                return env_value
        elif self.kind == "amd-rocm":
            env_name = "BK_ROCM_INDEX"
            prefix = "rocm"
            label = "ROCm"
            env_value = os.environ.get(env_name, "").strip().lower()
            if env_value:
                if not re.fullmatch(r"rocm\d+(?:\.\d+)+", env_value):
                    raise RuntimeError(translation.translate(translation.DEFAULT_LANGUAGE, "backend_install_unsupported_rocm_index", env_value))
                self._emit(f"Using {label} wheel index from {env_name}: {env_value}")
                return env_value
        else:
            return str(default_index or "").strip()
        fallback = str(default_index or "").strip().lower()
        self._emit(f"Resolving newest PyTorch {label} wheel index online...")
        try:
            indexes = self._fetch_available_pytorch_indexes(prefix)
            if indexes:
                chosen = indexes[-1]
                self._emit(f"Newest PyTorch {label} wheel index found: {chosen}")
                return chosen
            self._emit(f"[!] No PyTorch {label} wheel index found online; using fallback {fallback}.")
        except Exception as exc:
            self._emit(f"[!] Could not resolve newest PyTorch {label} wheel index online: {exc}")
            self._emit(f"[!] Using fallback PyTorch {label} wheel index: {fallback}")
        return fallback
    def _write_backend_info(self, target_dir: Path, py: Path, worker: Path, torch_index: str):
        meta = BACKEND_DEFS[self.kind]
        info = {
            "name": meta["name"],
            "app_version": APP_VERSION,
            "backend": self.kind,
            "python": str(py),
            "worker": str(worker),
            "torch": meta.get("torch") or "auto",
            "torchvision": meta.get("torchvision") or "auto",
            "pytorch_index": f"https://download.pytorch.org/whl/{torch_index}",
            "installed_at": datetime.now().astimezone().isoformat(),
            "installed_by": "Bottled Kraken integrated backend installer",
            "platform": detect_platform_id(),
        }
        (target_dir / "backend_info.json").write_text(
            json.dumps(info, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    def _torch_packages(self, torch_index: str):
        meta = BACKEND_DEFS[self.kind]
        torch_ver = os.environ.get("BK_TORCH_VERSION", "").strip() or meta.get("torch") or NVIDIA_TORCH_VERSION
        torchvision_ver = os.environ.get("BK_TORCHVISION_VERSION", "").strip() or meta.get("torchvision") or NVIDIA_TORCHVISION_VERSION
        if torch_ver and torchvision_ver:
            suffix = f"+{torch_index}" if self.kind == "nvidia-cuda" and torch_index.startswith("cu") else ""
            return f"torch=={torch_ver}{suffix}", f"torchvision=={torchvision_ver}{suffix}"
        if torch_ver:
            suffix = f"+{torch_index}" if self.kind == "nvidia-cuda" and torch_index.startswith("cu") else ""
            return f"torch=={torch_ver}{suffix}", "torchvision"
        if torchvision_ver:
            suffix = f"+{torch_index}" if self.kind == "nvidia-cuda" and torch_index.startswith("cu") else ""
            return "torch", f"torchvision=={torchvision_ver}{suffix}"
        return "torch", "torchvision"
    def _install_pytorch_backend_wheels(self, pip_cmd: List[str], torch_index: str, *, repair: bool = False):
        torch_pkg, torchvision_pkg = self._torch_packages(torch_index)
        if repair:
            self._emit(f"Repairing PyTorch backend wheels from {torch_index} after dependency installation...")
        else:
            self._emit(f"Installing PyTorch backend wheels from {torch_index}...")
        self._emit(f"PyTorch packages: {torch_pkg} {torchvision_pkg}")
        self._run_cmd(
            pip_cmd + [
                "install",
                "--no-cache-dir",
                "--upgrade",
                "--force-reinstall",
                torch_pkg,
                torchvision_pkg,
                "--index-url",
                f"https://download.pytorch.org/whl/{torch_index}",
            ]
        )
    def _verify_pytorch_backend(self, py_path: Path):
        if self.kind == "nvidia-cuda":
            code = (
                "import json, torch; "
                "out={"
                "'torch': torch.__version__, "
                "'cuda_version': getattr(torch.version, 'cuda', None), "
                "'cuda_available': bool(torch.cuda.is_available()), "
                "'cuda_device_count': int(torch.cuda.device_count()) if hasattr(torch, 'cuda') else 0"
                "}; "
                "print(json.dumps(out)); "
                "raise SystemExit(0 if out['cuda_available'] and out['cuda_device_count'] > 0 and out['cuda_version'] else 42)"
            )
            rc, out = _run_capture([str(py_path), "-c", code], timeout=30)
            self._emit(f"PyTorch CUDA check: {out}")
            if rc != 0:
                raise RuntimeError(
                    "NVIDIA-CUDA-PyTorch wurde nicht korrekt installiert. "
                    "Im Backend liegt wahrscheinlich noch eine CPU-Wheel von torch oder eine nicht passende Python/PyTorch-Kombination. "
                    "Aktiviere im Installer 'Vorhandenes Backend vorher löschen und neu installieren' und starte die Installation erneut."
                )
    def run(self):
        try:
            if self.kind not in BACKEND_DEFS:
                raise RuntimeError(translation.translate(translation.DEFAULT_LANGUAGE, "backend_install_unknown_backend", self.kind))
            platform_id = detect_platform_id()
            self._emit(f"Platform: {platform_id}")
            self._emit(f"Target backend: {self.kind}")
            if self.kind == "amd-rocm" and not sys.platform.startswith("linux"):
                raise RuntimeError(translation.translate(translation.DEFAULT_LANGUAGE, "backend_install_rocm_linux_only"))
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
            self._emit("Installing binary wheel prerequisite: python-bidi...")
            try:
                self._run_cmd(
                    pip_cmd + [
                        "install",
                        "--no-cache-dir",
                        "--prefer-binary",
                        "--only-binary=:all:",
                        PYTHON_BIDI_REQUIREMENT,
                    ]
                )
            except Exception as exc:
                raise RuntimeError(
                    "python-bidi could not be installed as a prebuilt wheel. "
                    "Please use Python 3.10-3.13 64-bit and upgrade pip first. "
                    "The backend installer intentionally does not build python-bidi from source, "
                    "because that would require Rust/MSVC build tools on Windows.\n\n"
                    f"Original error: {exc}"
                ) from exc
            torch_index = self._resolve_torch_index(meta["torch_index"])
            self._install_pytorch_backend_wheels(pip_cmd, torch_index)
            self._emit("Installing Kraken runtime dependencies...")
            deps = [KRAKEN_REQUIREMENT, PYTHON_BIDI_REQUIREMENT, "pyarrow", "Pillow", "numpy"]
            self._run_cmd(pip_cmd + ["install", "--no-cache-dir", "--prefer-binary"] + deps)
            if self.kind == "nvidia-cuda":
                self._install_pytorch_backend_wheels(pip_cmd, torch_index, repair=True)
                self._verify_pytorch_backend(py_path)
            self._emit("Installing optional coremltools dependency...")
            try:
                self._run_cmd(pip_cmd + ["install", "--no-cache-dir", "--prefer-binary", "coremltools"])
            except Exception as exc:
                self._emit(f"[!] coremltools could not be installed: {exc}")
                self._emit("[!] Continuing; the backend self-test will show whether Kraken can import successfully.")
            self._emit("Writing Bottled Kraken backend worker...")
            self._write_worker(worker_path)
            self._write_backend_info(target_dir, py_path, worker_path, torch_index)
            self._emit("Running backend self-test...")
            self._run_cmd([str(py_path), str(worker_path), "--self-test", "--backend-kind", self.kind])
            clear_external_ocr_backend_cache()
            self.finished_ok.emit(True, translation.translate(translation.DEFAULT_LANGUAGE, "backend_install_ok"))
        except Exception as exc:
            clear_external_ocr_backend_cache()
            self._emit(f"[!] {exc}")
            self.finished_ok.emit(False, str(exc))
