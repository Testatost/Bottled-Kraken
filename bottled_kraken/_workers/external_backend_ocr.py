from __future__ import annotations
import json
import os
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from bottled_kraken.user_storage import bottled_kraken_runtime_path
from bottled_kraken.common import QThread, Signal, OCRJob, RecordView, BBox
from bottled_kraken.translation import translation
BACKEND_APP_DIR_NAME = "BottledKraken"
BACKEND_CACHE_TTL_SECONDS = 20.0
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
@dataclass
class ExternalOCRBackend:
    kind: str
    name: str
    base_dir: str
    python: str
    worker: str
    info_path: str
    ok: bool = False
    detail: str = ""
    raw_info: Optional[Dict[str, Any]] = None
    self_test: Optional[Dict[str, Any]] = None
_BACKEND_CACHE: Dict[str, Tuple[float, Optional[ExternalOCRBackend]]] = {}
def _default_backend_root() -> Path:
    custom = os.environ.get("BOTTLED_KRAKEN_BACKENDS_DIR", "").strip()
    if custom:
        return Path(custom).expanduser()
    return bottled_kraken_runtime_path("backends")
def _backend_dir_for_kind(kind: str) -> Path:
    return _default_backend_root() / kind
def _safe_read_backend_info(kind: str) -> Optional[Dict[str, Any]]:
    info_path = _backend_dir_for_kind(kind) / "backend_info.json"
    if not info_path.is_file():
        return None
    try:
        data = json.loads(info_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None
        return data
    except Exception:
        return None
def _backend_info_to_obj(kind: str, data: Dict[str, Any]) -> Optional[ExternalOCRBackend]:
    base = _backend_dir_for_kind(kind)
    py = str(data.get("python") or "").strip()
    worker = str(data.get("worker") or "").strip()
    if not py:
        py = str(base / ".venv" / "bin" / "python")
    if not worker:
        worker = str(base / "worker_kraken_backend.py")
    if not Path(py).is_file() or not Path(worker).is_file():
        return None
    return ExternalOCRBackend(
        kind=kind,
        name=str(data.get("name") or kind),
        base_dir=str(base),
        python=py,
        worker=worker,
        info_path=str(base / "backend_info.json"),
        raw_info=data,
    )
def _run_backend_self_test(backend: ExternalOCRBackend, timeout: int = 40) -> ExternalOCRBackend:
    def _probe_backend_vram() -> Dict[str, Any]:
        code = (
            "import json, torch\n"
            "out = {}\n"
            "try:\n"
            "    ok = bool(torch.cuda.is_available() and torch.cuda.device_count() > 0)\n"
            "    out['cuda_available'] = ok\n"
            "    out['cuda_device_count'] = int(torch.cuda.device_count()) if hasattr(torch, 'cuda') else 0\n"
            "    if ok:\n"
            "        props = torch.cuda.get_device_properties(0)\n"
            "        total = int(getattr(props, 'total_memory', 0) or 0)\n"
            "        out['device_name'] = torch.cuda.get_device_name(0)\n"
            "        out['cuda_device_total_memory'] = total\n"
            "        out['cuda_device_total_memory_gb'] = round(total / (1024 ** 3), 1) if total else 0.0\n"
            "except Exception as exc:\n"
            "    out['vram_probe_error'] = repr(exc)\n"
            "print(json.dumps(out, ensure_ascii=False), flush=True)\n"
        )
        try:
            env = os.environ.copy()
            env.setdefault("PYTHONUTF8", "1")
            env.setdefault("PYTHONIOENCODING", "utf-8")
            p2 = subprocess.run(
                [backend.python, "-c", code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=20,
                env=env,
                **_no_console_kwargs(),
            )
            raw = (p2.stdout or "").strip()
            if raw:
                start = raw.find("{")
                end = raw.rfind("}")
                if start >= 0 and end >= start:
                    data2 = json.loads(raw[start:end + 1])
                    return data2 if isinstance(data2, dict) else {}
        except Exception:
            pass
        return {}
    try:
        cmd = [backend.python, backend.worker, "--self-test", "--backend-kind", backend.kind]
        env = os.environ.copy()
        env.setdefault("PYTHONUTF8", "1")
        env.setdefault("PYTHONIOENCODING", "utf-8")
        p = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
            **_no_console_kwargs(),
        )
        text = (p.stdout or "").strip()
        data = None
        if text:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end >= start:
                data = json.loads(text[start:end + 1])
        if not isinstance(data, dict):
            data = {
                "ok": False,
                "error": (p.stderr or p.stdout or "No JSON self-test output").strip(),
            }
        if data.get("ok") or data.get("cuda_available"):
            if not data.get("cuda_device_total_memory") and not data.get("cuda_device_total_memory_gb"):
                probe = _probe_backend_vram()
                for key, value in probe.items():
                    data.setdefault(key, value)
        backend.self_test = data
        backend.ok = bool(data.get("ok") or data.get("cuda_available"))
        if backend.ok:
            dev = str(data.get("device_name") or data.get("backend_kind") or backend.kind)
            if backend.kind == "nvidia-cuda":
                cuda = data.get("cuda_version")
                backend.detail = f"{dev} (CUDA {cuda})" if cuda else f"{dev} (CUDA)"
            elif backend.kind == "amd-rocm":
                hip = data.get("hip_version")
                backend.detail = f"{dev} (HIP {hip})" if hip else f"{dev} (ROCm)"
            else:
                backend.detail = dev
        else:
            backend.detail = str(data.get("error") or p.stderr or "Backend self-test failed").strip()
    except Exception as exc:
        backend.ok = False
        backend.detail = repr(exc)
        backend.self_test = {"ok": False, "error": repr(exc)}
    return backend
def get_external_ocr_backend(kind: str, *, refresh: bool = False) -> Optional[ExternalOCRBackend]:
    kind = str(kind or "").strip().lower()
    if kind not in ("nvidia-cuda", "amd-rocm"):
        return None
    now = time.time()
    if not refresh:
        cached = _BACKEND_CACHE.get(kind)
        if cached and (now - cached[0]) <= BACKEND_CACHE_TTL_SECONDS:
            return cached[1]
    data = _safe_read_backend_info(kind)
    backend = _backend_info_to_obj(kind, data) if data else None
    if backend is not None:
        backend = _run_backend_self_test(backend)
    _BACKEND_CACHE[kind] = (now, backend)
    return backend
def get_external_ocr_backends(*, refresh: bool = False) -> Dict[str, ExternalOCRBackend]:
    out: Dict[str, ExternalOCRBackend] = {}
    for kind in ("nvidia-cuda", "amd-rocm"):
        b = get_external_ocr_backend(kind, refresh=refresh)
        if b is not None:
            out[kind] = b
    return out
def clear_external_ocr_backend_cache():
    _BACKEND_CACHE.clear()
from bottled_kraken._workers.external_backend_worker_source import EXTERNAL_KRAKEN_WORKER_SOURCE
def ensure_external_worker_script(backend: ExternalOCRBackend) -> bool:
    try:
        worker_path = Path(backend.worker)
        worker_path.parent.mkdir(parents=True, exist_ok=True)
        current = worker_path.read_text(encoding="utf-8") if worker_path.is_file() else ""
        if "--job-json" not in current or "Bottled Kraken external Kraken OCR worker" not in current:
            worker_path.write_text(EXTERNAL_KRAKEN_WORKER_SOURCE, encoding="utf-8")
            try:
                worker_path.chmod(0o755)
            except Exception:
                pass
        return True
    except Exception:
        return False
class ExternalBackendOCRWorker(QThread):
    file_started = Signal(str)
    file_done = Signal(str, str, list, object, list)
    file_error = Signal(str, str)
    progress = Signal(int)
    finished_batch = Signal()
    failed = Signal(str)
    device_resolved = Signal(str)
    gpu_info = Signal(str)
    def __init__(self, job: OCRJob, backend: ExternalOCRBackend):
        super().__init__()
        self.job = job
        self.backend = backend
        self._proc: Optional[subprocess.Popen] = None
        self._job_file: Optional[Path] = None
    def requestInterruption(self):
        super().requestInterruption()
        proc = self._proc
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass
    def _write_job_file(self) -> Path:
        payload = {
            "input_paths": list(self.job.input_paths or []),
            "recognition_model_path": self.job.recognition_model_path,
            "segmentation_model_path": self.job.segmentation_model_path,
            "device": self.job.device,
            "reading_direction": self.job.reading_direction,
            "preset_bboxes_by_path": self.job.preset_bboxes_by_path or {},
            "auto_revision_enabled": bool(getattr(self.job, "auto_revision_enabled", False)),
            "auto_revision_replacements": str(getattr(self.job, "auto_revision_replacements", "") or ""),
        }
        job_dir = bottled_kraken_runtime_path("backend_jobs")
        path = job_dir / f"bk_backend_job_{int(time.time() * 1000)}_{uuid.uuid4().hex}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        self._job_file = Path(path)
        return self._job_file
    def _handle_event(self, data: Dict[str, Any]):
        event = data.get("event")
        if event == "file_started":
            self.file_started.emit(str(data.get("path") or ""))
        elif event == "file_done":
            path = str(data.get("path") or "")
            text = str(data.get("text") or "")
            records = []
            for idx, item in enumerate(data.get("records") or []):
                if not isinstance(item, dict):
                    continue
                raw_bb = item.get("bbox")
                bbox: Optional[BBox] = None
                if isinstance(raw_bb, (list, tuple)) and len(raw_bb) == 4:
                    try:
                        bbox = tuple(int(v) for v in raw_bb)
                    except Exception:
                        bbox = None
                records.append(RecordView(len(records), str(item.get("text") or ""), bbox))
            self.file_done.emit(path, text, [], None, records)
        elif event == "file_error":
            self.file_error.emit(str(data.get("path") or ""), str(data.get("message") or ""))
        elif event == "progress":
            try:
                self.progress.emit(max(0, min(100, int(data.get("value") or 0))))
            except Exception:
                pass
        elif event == "device_resolved":
            self.device_resolved.emit(str(data.get("value") or ""))
        elif event == "gpu_info":
            self.gpu_info.emit(str(data.get("value") or ""))
        elif event == "failed":
            self.failed.emit(str(data.get("message") or translation.translate(translation.DEFAULT_LANGUAGE, "err_external_backend_failed")))
    def run(self):
        try:
            if not ensure_external_worker_script(self.backend):
                raise RuntimeError(translation.translate(translation.DEFAULT_LANGUAGE, "err_external_backend_write_failed"))
            job_file = self._write_job_file()
            cmd = [
                self.backend.python,
                self.backend.worker,
                "--backend-kind",
                self.backend.kind,
                "--job-json",
                str(job_file),
            ]
            env = os.environ.copy()
            env.setdefault("PYTHONUTF8", "1")
            env.setdefault("PYTHONIOENCODING", "utf-8")
            self._proc = subprocess.Popen(
                cmd,
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
            assert self._proc.stdout is not None
            for line in self._proc.stdout:
                if self.isInterruptionRequested():
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except Exception:
                    continue
                if isinstance(data, dict):
                    self._handle_event(data)
            if self.isInterruptionRequested():
                try:
                    if self._proc and self._proc.poll() is None:
                        self._proc.terminate()
                except Exception:
                    pass
                return
            rc = self._proc.wait(timeout=10) if self._proc else 1
            if rc != 0:
                self.failed.emit(translation.translate(translation.DEFAULT_LANGUAGE, "err_external_backend_exit_code", rc))
                return
            self.progress.emit(100)
            self.finished_batch.emit()
        except Exception as exc:
            import traceback
            self.failed.emit(traceback.format_exc() if os.environ.get("BOTTLED_KRAKEN_DEBUG") else str(exc))
        finally:
            try:
                if self._job_file and self._job_file.exists():
                    self._job_file.unlink()
            except Exception:
                pass
