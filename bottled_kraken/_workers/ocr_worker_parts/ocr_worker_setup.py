from bottled_kraken.translation import translation
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


        def _tr(self, key: str, *args) -> str:
            return translation.translate(getattr(self.job, "ui_language", "de"), key, *args)

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

        def _release_torch_resources(self):
            self._rec_model = None
            self._seg_model = None
            self._device = None
            self._soft_page_cleanup()

        def _load_rec_model(self, path: str, device: torch.device):
            return load_kraken_recognition_model(path, device=device)

        def _load_seg_model(self, path: str, device: torch.device):
            return load_kraken_segmentation_model(path, device=device)

        def _ensure_models_loaded(self):
            if self._device is None:
                self._device = torch.device("cpu")
            if self._rec_model is None:
                self._rec_model = self._load_rec_model(self.job.recognition_model_path, self._device)
            if self._seg_model is None:
                if not self.job.segmentation_model_path:
                    raise ValueError(self._tr("ptr_err_no_seg_model"))
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
