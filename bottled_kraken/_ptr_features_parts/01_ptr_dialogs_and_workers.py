"""PTR-Erweiterungen: Multi-OCR, Remote-AI und Folge-Patches."""

from .shared import *

from .ui_components import *

from .workers import *

from .dialogs import *

from .image_edit import *

from .main_window import MainWindow

OCR_SOURCE_SEPARATOR = "===== OCR SOURCE ====="

@dataclass
class PtrRemoteAIConfig:
    provider_name: str = "openrouter"
    api_key: str = ""
    base_url: str = "https://openrouter.ai/api/v1"
    model: str = "openrouter/free"
    timeout_seconds: int = 90
    temperature: float = 0.2
    app_name: str = "Bottled Kraken"
    app_url: str = ""

class PtrMultiOCRJob:
    def __init__(self, input_paths: List[str], recognition_model_paths: List[str],
                 segmentation_model_path: Optional[str], device: str,
                 reading_direction: int, runs: int):
        self.input_paths = input_paths or []
        self.recognition_model_paths = recognition_model_paths or []
        self.segmentation_model_path = segmentation_model_path
        self.device = device
        self.reading_direction = int(reading_direction)
        self.runs = int(runs)

class PtrMultiOCRWorker(QThread):
    file_started = Signal(str)
    file_done = Signal(str, str, list, object, list, list)
    file_error = Signal(str, str)
    progress = Signal(int)
    finished_batch = Signal()
    failed = Signal(str)
    device_resolved = Signal(str)
    gpu_info = Signal(str)
    def __init__(self, job: PtrMultiOCRJob, parent=None):
        super().__init__(parent)
        self.job = job
        self._device = None
        self._device_label = (job.device or "cpu").lower().strip()
        self._seg_model = None
        self._rec_models: Dict[str, Any] = {}
    def _resolve_device(self):
        dev = (self.job.device or "cpu").lower().strip()
        self._device_label = dev
        if dev in ("cuda", "rocm") and torch.cuda.is_available() and torch.cuda.device_count() > 0:
            return torch.device("cuda")
        if dev == "mps" and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        self._device_label = "cpu"
        return torch.device("cpu")
    def _emit_gpu_info(self, device):
        try:
            if device.type == "cuda":
                name = torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else "GPU"
                hip_ver = getattr(torch.version, "hip", None)
                cuda_ver = getattr(torch.version, "cuda", None)
                if self._device_label == "rocm" or hip_ver:
                    self.gpu_info.emit(f"{name} (ROCm/HIP {hip_ver})" if hip_ver else f"{name} (ROCm)")
                else:
                    self.gpu_info.emit(f"{name} (CUDA {cuda_ver})" if cuda_ver else f"{name} (CUDA)")
            elif device.type == "mps":
                self.gpu_info.emit("Apple MPS")
            else:
                self.gpu_info.emit("CPU")
        except Exception:
            pass
    def _load_rec_model(self, path: str, device):
        try:
            return models.load_any(path, device=device)
        except TypeError:
            return models.load_any(path)
    def _load_seg_model(self, path: str, device):
        try:
            return vgsl.TorchVGSLModel.load_model(path, device=device)
        except TypeError:
            return vgsl.TorchVGSLModel.load_model(path)
    def _normalize_recognition_paths(self) -> List[str]:
        cleaned = []
        seen = set()
        for p in self.job.recognition_model_paths:
            norm = (p or "").strip()
            if not norm or norm in seen:
                continue
            cleaned.append(norm)
            seen.add(norm)
        return cleaned
    def _build_run_plan(self, rec_paths: List[str], runs: int) -> List[str]:
        if not rec_paths:
            raise ValueError("No recognition models selected.")
        if runs <= 0:
            raise ValueError("Runs must be >= 1.")
        return [rec_paths[i % len(rec_paths)] for i in range(runs)]
    def _ensure_models_loaded(self):
        if self._device is None:
            self._device = self._resolve_device()
            self.device_resolved.emit(f"{self._device_label} -> {self._device}")
            self._emit_gpu_info(self._device)
        if self._seg_model is None:
            if not self.job.segmentation_model_path:
                raise ValueError("No segmentation/baseline model selected.")
            self._seg_model = self._load_seg_model(self.job.segmentation_model_path, self._device)
        for p in self._normalize_recognition_paths():
            if p not in self._rec_models:
                self._rec_models[p] = self._load_rec_model(p, self._device)
    def _emit_overall_progress(self, file_idx: int, total_files: int, frac: float):
        if total_files <= 0:
            self.progress.emit(0)
            return
        frac = max(0.0, min(1.0, float(frac)))
        overall = (file_idx + frac) / float(total_files)
        self.progress.emit(int(overall * 100))
    def _ocr_one_run(self, im: Image.Image, rec_model: Any) -> Tuple[str, list, List[RecordView]]:
        seg = blla.segment(im, model=self._seg_model)
        kr_records: List[Any] = []
        for rec in rpred.rpred(rec_model, im, seg):
            kr_records.append(rec)
            if self.isInterruptionRequested():
                break
        if self.isInterruptionRequested():
            return ("", [], [])
        kr_sorted = sort_records_reading_order(kr_records, im.size[0], im.size[1], self.job.reading_direction)
        wide_line_splitter = re.compile(r"\s{2,}")
        record_views: List[RecordView] = []
        lines: List[str] = []
        out_idx = 0
        page_w, page_h = im.size
        for r in kr_sorted:
            pred = getattr(r, "prediction", None)
            if pred is None:
                continue
            txt = str(pred)
            bb = record_bbox(r)
            if bb:
                x0, y0, x1, y1 = bb
                w = x1 - x0
                if w > int(page_w * 0.80):
                    parts = wide_line_splitter.split(txt, maxsplit=1)
                    if len(parts) == 2:
                        left_txt, right_txt = map(str.strip, parts)
                        mid = page_w // 2
                        left_bb = clamp_bbox((0, y0, mid, y1), page_w, page_h)
                        right_bb = clamp_bbox((mid, y0, page_w, y1), page_w, page_h)
                        if left_bb:
                            record_views.append(RecordView(out_idx, left_txt, left_bb))
                            lines.append(left_txt)
                            out_idx += 1
                        if right_bb:
                            record_views.append(RecordView(out_idx, right_txt, right_bb))
                            lines.append(right_txt)
                            out_idx += 1
                        continue
            record_views.append(RecordView(out_idx, txt, bb))
            lines.append(txt)
            out_idx += 1
        return ("\n".join(lines).strip(), kr_sorted, record_views)
    def _ocr_multi_for_file(self, img_path: str, file_idx: int, total_files: int):
        self.file_started.emit(img_path)
        with Image.open(img_path) as im:
            im = im.copy()
        texts: List[str] = []
        last_sorted: list = []
        last_views: List[RecordView] = []
        rec_paths = self._normalize_recognition_paths()
        run_plan = self._build_run_plan(rec_paths, self.job.runs)
        for run_i, rec_path in enumerate(run_plan):
            if self.isInterruptionRequested():
                return
            rec_model = self._rec_models[rec_path]
            t, kr_sorted, rvs = self._ocr_one_run(im, rec_model)
            texts.append(t)
            last_sorted = kr_sorted
            last_views = rvs
            self._emit_overall_progress(file_idx, total_files, (run_i + 1) / float(len(run_plan)))
        merged = _ptr_merge_ocr_texts_local(texts)
        self.file_done.emit(img_path, merged, last_sorted, im, last_views, texts)
    def run(self):
        try:
            rec_paths = self._normalize_recognition_paths()
            if not self.job.input_paths:
                raise ValueError("No input files selected.")
            if not rec_paths:
                raise ValueError("No recognition models selected.")
            if self.job.runs <= 0:
                raise ValueError("Runs must be >= 1.")
            for p in rec_paths:
                if not os.path.exists(p):
                    raise ValueError(f"Recognition model not found: {p}")
            if not os.path.exists(self.job.segmentation_model_path or ""):
                raise ValueError("Baseline model not found.")
            self._ensure_models_loaded()
            total = len(self.job.input_paths)
            for i, path in enumerate(self.job.input_paths):
                if self.isInterruptionRequested():
                    break
                self._emit_overall_progress(i, total, 0.0)
                try:
                    self._ocr_multi_for_file(path, i, total)
                except Exception as exc:
                    self.file_error.emit(path, str(exc))
            self.progress.emit(100)
            self.finished_batch.emit()
        except Exception as exc:
            self.failed.emit(str(exc))

class PtrMultiOcrDialog(QDialog):
    def __init__(self, rec_models: List[Tuple[str, str]], default_selected_paths: Optional[List[str]] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Multi-OCR")
        self.setMinimumWidth(520)
        self._rec_models = rec_models
        self._default_selected = set(default_selected_paths or [])
        root = QVBoxLayout(self)
        root.addWidget(QLabel("Wie oft OCR durchführen?"))
        self.spin_runs = QSpinBox()
        self.spin_runs.setRange(1, 99)
        self.spin_runs.setSingleStep(1)
        self.spin_runs.setValue(3)
        root.addWidget(self.spin_runs)
        root.addSpacing(8)
        root.addWidget(QLabel("Welche Recognition-Modelle verwenden? (Mehrfachauswahl)"))
        self.list_models = QListWidget()
        self.list_models.setSelectionMode(QAbstractItemView.MultiSelection)
        for name, path in self._rec_models:
            it = QListWidgetItem(name)
            it.setData(Qt.UserRole, path)
            self.list_models.addItem(it)
            if path in self._default_selected:
                it.setSelected(True)
        if self.list_models.count() > 0 and not self.list_models.selectedItems():
            self.list_models.item(0).setSelected(True)
        root.addWidget(self.list_models)
        self.chk_use_seg = QCheckBox("Segmentation-/Baseline-Modell verwenden")
        self.chk_use_seg.setChecked(True)
        root.addWidget(self.chk_use_seg)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        root.addWidget(bb)
    def runs(self) -> int:
        return int(self.spin_runs.value())
    def selected_recognition_paths(self) -> List[str]:
        out = []
        for it in self.list_models.selectedItems():
            p = it.data(Qt.UserRole)
            if p:
                out.append(str(p))
        return out
    def use_segmentation(self) -> bool:
        return bool(self.chk_use_seg.isChecked())

class PtrMultiOCRFollowupDialog(QDialog):
    CHOICE_LOCAL = "local"
    CHOICE_AI = "ai"
    CHOICE_AI_POSTGRES = "ai_postgres"
    CHOICE_AI_NEO4J = "ai_neo4j"
    CHOICE_AI_BOTH = "ai_both"
    CHOICE_CANCEL = "cancel"
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Multi-OCR fertig")
        self.resize(560, 220)
        self.choice = self.CHOICE_CANCEL
        root = QVBoxLayout(self)
        lbl = QLabel(
            "Multi-OCR wurde abgeschlossen.\n\n"
            "Wie möchtest du mit dem Ergebnis weiterarbeiten?"
        )
        lbl.setWordWrap(True)
        root.addWidget(lbl)
        row1 = QHBoxLayout()
        row2 = QHBoxLayout()
        self.local_btn = QPushButton("Lokalen Merge verwenden")
        self.ai_btn = QPushButton("AI Tools öffnen")
        self.ai_pg_btn = QPushButton("AI + PostgreSQL")
        self.ai_neo_btn = QPushButton("AI + Neo4j")
        self.ai_both_btn = QPushButton("AI + Beide")
        self.cancel_btn = QPushButton("Abbrechen")
        row1.addWidget(self.local_btn)
        row1.addWidget(self.ai_btn)
        row1.addWidget(self.cancel_btn)
        row2.addWidget(self.ai_pg_btn)
        row2.addWidget(self.ai_neo_btn)
        row2.addWidget(self.ai_both_btn)
        root.addLayout(row1)
        root.addLayout(row2)
        self.local_btn.clicked.connect(lambda: self._choose(self.CHOICE_LOCAL))
        self.ai_btn.clicked.connect(lambda: self._choose(self.CHOICE_AI))
        self.ai_pg_btn.clicked.connect(lambda: self._choose(self.CHOICE_AI_POSTGRES))
        self.ai_neo_btn.clicked.connect(lambda: self._choose(self.CHOICE_AI_NEO4J))
        self.ai_both_btn.clicked.connect(lambda: self._choose(self.CHOICE_AI_BOTH))
        self.cancel_btn.clicked.connect(self.reject)
    def _choose(self, choice: str):
        self.choice = choice
        self.accept()
    @classmethod
    def get_choice(cls, parent=None) -> str:
        dlg = cls(parent=parent)
        if dlg.exec() == QDialog.Accepted:
            return dlg.choice
        return cls.CHOICE_CANCEL

class PtrRemoteAITaskWorker(QThread):
    result_ready = Signal(object)
    failed = Signal(str)
    def __init__(self, mode: str, config: PtrRemoteAIConfig,
                 ocr_texts: Optional[List[str]] = None,
                 merged_text: str = "",
                 include_postgres: bool = True,
                 include_neo4j: bool = True,
                 parent=None):
        super().__init__(parent)
        self.mode = (mode or "").strip().lower()
        self.config = config
        self.ocr_texts = list(ocr_texts or [])
        self.merged_text = merged_text or ""
        self.include_postgres = bool(include_postgres)
        self.include_neo4j = bool(include_neo4j)
    def run(self):
        try:
            if self.mode == "merge":
                merged = _ptr_ai_merge_ocr_texts(self.config, self.ocr_texts)
                self.result_ready.emit({"mode": "merge", "merged_text": merged})
                return
            if self.mode == "postgres":
                merged = (self.merged_text or "").strip()
                if not merged:
                    merged = _ptr_ai_merge_ocr_texts(self.config, self.ocr_texts)
                pg = _ptr_ai_build_postgres_json(self.config, merged)
                self.result_ready.emit({"mode": "postgres", "merged_text": merged, "postgres": pg})
                return
            if self.mode == "neo4j":
                merged = (self.merged_text or "").strip()
                if not merged:
                    merged = _ptr_ai_merge_ocr_texts(self.config, self.ocr_texts)
                neo = _ptr_ai_build_neo4j_json(self.config, merged)
                self.result_ready.emit({"mode": "neo4j", "merged_text": merged, "neo4j": neo})
                return
            if self.mode == "pipeline":
                merged = _ptr_ai_merge_ocr_texts(self.config, self.ocr_texts)
                pg = _ptr_ai_build_postgres_json(self.config, merged) if self.include_postgres else None
                neo = _ptr_ai_build_neo4j_json(self.config, merged) if self.include_neo4j else None
                self.result_ready.emit({
                    "mode": "pipeline",
                    "merged_text": merged,
                    "postgres": pg,
                    "neo4j": neo,
                })
                return
            raise ValueError(f"Unknown remote AI mode: {self.mode}")
        except Exception as exc:
            self.failed.emit(str(exc))
