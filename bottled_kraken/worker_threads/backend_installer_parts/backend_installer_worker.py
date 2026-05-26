from .backend_installer_helpers import *
from .backend_installer_helpers import _no_console_kwargs, _run_capture
from ...translation import translation

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

        if self.kind == "nvidia-cuda":
            # Kraken 7.0.2 akzeptiert maximal torch 2.10.x.
            # Der CUDA-Index liefert ohne Pinning automatisch die neueste Version
            # und kann dadurch torch 2.11.x installieren, was Kraken ablehnt.
            torch_ver = meta.get("torch") or "2.10.0"
            torchvision_ver = meta.get("torchvision") or "0.25.0"
            suffix = f"+{torch_index}" if torch_index.startswith("cu") else ""
            return f"torch=={torch_ver}{suffix}", f"torchvision=={torchvision_ver}{suffix}"

        torch_pkg = f"torch=={meta['torch']}" if meta.get("torch") else "torch"
        torchvision_pkg = f"torchvision=={meta['torchvision']}" if meta.get("torchvision") else "torchvision"
        return torch_pkg, torchvision_pkg

    def _install_pytorch_backend_wheels(self, pip_cmd: List[str], torch_index: str, *, repair: bool = False):
        torch_pkg, torchvision_pkg = self._torch_packages(torch_index)
        if repair:
            self._emit(f"Repairing PyTorch backend wheels from {torch_index} after dependency installation...")
        else:
            self._emit(f"Installing PyTorch backend wheels from {torch_index}...")

        self._emit(f"PyTorch packages: {torch_pkg} {torchvision_pkg}")

        # Wichtig: Beim NVIDIA-Backend darf am Ende keine CPU-Wheel von torch übrig bleiben.
        # Kraken/Pip kann sonst unter Windows später wieder torch==...+cpu aus PyPI einziehen.
        # Darum installieren wir die CUDA/ROCm-Wheels explizit aus dem PyTorch-Index und prüfen sie danach.
        self._run_cmd(
            pip_cmd + [
                "install",
                "--no-cache-dir",
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

            torch_index = meta["torch_index"]
            if self.kind == "nvidia-cuda":
                torch_index = os.environ.get("BK_CUDA_INDEX", torch_index).strip() or torch_index
                if torch_index not in {"cu121", "cu124", "cu126", "cu128", "cu130"}:
                    raise RuntimeError(translation.translate(translation.DEFAULT_LANGUAGE, "backend_install_unsupported_cuda_index", torch_index))
            elif self.kind == "amd-rocm":
                torch_index = os.environ.get("BK_ROCM_INDEX", torch_index).strip() or torch_index
                if not torch_index.startswith("rocm"):
                    raise RuntimeError(translation.translate(translation.DEFAULT_LANGUAGE, "backend_install_unsupported_rocm_index", torch_index))

            self._install_pytorch_backend_wheels(pip_cmd, torch_index)

            self._emit("Installing Kraken runtime dependencies...")
            deps = [KRAKEN_REQUIREMENT, PYTHON_BIDI_REQUIREMENT, "pyarrow", "Pillow", "numpy"]
            # Kein --upgrade: Die GPU-Wheel von PyTorch soll nicht unnötig ersetzt werden.
            self._run_cmd(pip_cmd + ["install", "--no-cache-dir", "--prefer-binary"] + deps)

            if self.kind == "nvidia-cuda":
                # Schutz gegen Windows/Pip-Fall: Kraken oder dessen Abhängigkeiten können
                # nachträglich torch==...+cpu aus PyPI installieren. Deshalb wird am Ende
                # CUDA-PyTorch erneut aus dem PyTorch-CUDA-Index installiert und geprüft.
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
