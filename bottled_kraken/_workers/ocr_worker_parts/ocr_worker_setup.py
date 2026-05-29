from bottled_kraken.common import (
    Any,
    OCRJob,
    Optional,
    baseline_length,
    gc,
    load_kraken_recognition_model,
    load_kraken_segmentation_model,
    os,
    torch,
)
MAX_KRAKEN_OCR_LINES = 500
class OCRWorkerSetupMixin:
        def __init__(self, job: OCRJob):
            super().__init__()
            self.job = job
            self._device: Optional[torch.device] = None
            self._rec_model: Any = None
            self._seg_model: Any = None
            self._device_label: str = (job.device or "cpu").lower().strip()
        @staticmethod
        def _ocr_reset_every() -> int:
            raw = os.environ.get("BOTTLED_KRAKEN_OCR_RESET_EVERY", "25")
            try:
                return max(0, int(raw))
            except Exception:
                return 25
        def _soft_page_cleanup(self):
            try:
                gc.collect()
            except Exception:
                pass
            try:
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass
        def _release_torch_resources(self):
            try:
                if torch.cuda.is_available():
                    torch.cuda.synchronize()
            except Exception:
                pass
            self._rec_model = None
            self._seg_model = None
            self._device = None
            self._soft_page_cleanup()
        def _resolve_device(self) -> torch.device:
            dev = (self.job.device or "cpu").lower().strip()
            self._device_label = dev
            if dev in ("cuda", "rocm"):
                if torch.cuda.is_available() and torch.cuda.device_count() > 0:
                    return torch.device("cuda")
            self._device_label = "cpu"
            return torch.device("cpu")
        def _emit_gpu_info(self, device: torch.device):
            try:
                if device.type == "cuda":
                    name = torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else "GPU"
                    hip_ver = getattr(torch.version, "hip", None)
                    cuda_ver = getattr(torch.version, "cuda", None)
                    if self._device_label == "rocm" or hip_ver:
                        extra = []
                        if hip_ver:
                            extra.append(f"HIP {hip_ver}")
                        s = name + (f" ({', '.join(extra)})" if extra else " (ROCm)")
                        self.gpu_info.emit(s)
                    else:
                        extra = []
                        if cuda_ver:
                            extra.append(f"CUDA {cuda_ver}")
                        s = name + (f" ({', '.join(extra)})" if extra else " (CUDA)")
                        self.gpu_info.emit(s)
                else:
                    self.gpu_info.emit("CPU")
            except Exception:
                pass
        def _load_rec_model(self, path: str, device: torch.device):
            return load_kraken_recognition_model(path, device=device)
        def _load_seg_model(self, path: str, device: torch.device):
            return load_kraken_segmentation_model(path, device=device)
        def _ensure_models_loaded(self):
            if self._device is None:
                self._device = self._resolve_device()
                self.device_resolved.emit(f"{self._device_label} -> {self._device}")
                self._emit_gpu_info(self._device)
            if self._rec_model is None:
                self._rec_model = self._load_rec_model(self.job.recognition_model_path, self._device)
            if self._seg_model is None:
                if not self.job.segmentation_model_path:
                    raise ValueError("No blla segmentation model selected.")
                self._seg_model = self._load_seg_model(self.job.segmentation_model_path, self._device)
        @staticmethod
        def _seg_expected_lines(seg: Any) -> Optional[int]:
            for attr in ("lines", "baselines"):
                v = getattr(seg, attr, None)
                if v is not None:
                    try:
                        return len(v)
                    except Exception:
                        pass
            return None
        def _emit_overall_progress(self, file_idx: int, total_files: int, frac_in_file: float):
            if total_files <= 0:
                self.progress.emit(0)
                return
            frac_in_file = max(0.0, min(1.0, float(frac_in_file)))
            overall = (file_idx + frac_in_file) / float(total_files)
            self.progress.emit(int(overall * 100))
        def _filter_short_baselines_in_seg(self, seg):
            try:
                if hasattr(seg, "baselines") and hasattr(seg, "lines") and seg.baselines and seg.lines:
                    new_baselines = []
                    new_lines = []
                    for bl, ln in zip(seg.baselines, seg.lines):
                        if baseline_length(bl) >= 5.0:
                            new_baselines.append(bl)
                            new_lines.append(ln)
                    seg.baselines = new_baselines[:MAX_KRAKEN_OCR_LINES]
                    seg.lines = new_lines[:MAX_KRAKEN_OCR_LINES]
            except Exception:
                pass
            return seg
