from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('ptr', globals())
from bottled_kraken.common import Any, Dict, Image, List, Optional, QAbstractItemView, QCheckBox, QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QSpinBox, QThread, QVBoxLayout, Qt, RecordView, Signal, Tuple, clamp_bbox, dataclass, expand_segmentation_bbox, gc, load_kraken_recognition_model, load_kraken_segmentation_model, os, re, recognize_with_kraken, record_bbox, segment_with_kraken, sort_records_reading_order, torch, translation
from bottled_kraken.main_window import MainWindow
OCR_SOURCE_SEPARATOR = "===== OCR SOURCE ====="
def _ptr_dialog_lang(obj) -> str:
    try:
        parent = obj.parent() if hasattr(obj, "parent") else None
        lang = getattr(parent, "current_lang", None)
        if lang:
            return str(lang)
    except Exception:
        pass
    return translation.DEFAULT_LANGUAGE
def _ptr_dialog_tr(obj, key: str, *args) -> str:
    try:
        lang = _ptr_dialog_lang(obj)
        return translation.translate(lang, key, *args)
    except Exception:
        return key
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
class PtrRemoteAICancelled(RuntimeError):
    pass

class PtrMultiOCRJob:
    def __init__(self, input_paths: List[str], recognition_model_paths: List[str],
                 segmentation_model_path: Optional[str],
                 reading_direction: int, runs: int,
                 image_variants_enabled: bool = False,
                 image_variant_count: int = 1):
        self.input_paths = input_paths or []
        self.recognition_model_paths = recognition_model_paths or []
        self.segmentation_model_path = segmentation_model_path
        self.reading_direction = int(reading_direction)
        self.runs = int(runs)
        self.image_variants_enabled = bool(image_variants_enabled)
        try:
            self.image_variant_count = max(1, min(9, int(image_variant_count)))
        except Exception:
            self.image_variant_count = 1
class PtrMultiOCRWorker(QThread):
    file_started = Signal(str)
    file_done = Signal(str, str, list, object, list, list)
    file_error = Signal(str, str)
    progress = Signal(int)
    finished_batch = Signal()
    failed = Signal(str)
    def __init__(self, job: PtrMultiOCRJob, parent=None):
        super().__init__(parent)
        self.job = job
        self._device = None
        self._seg_model = None
        self._rec_models: Dict[str, Any] = {}
    def _load_rec_model(self, path: str, device):
        return load_kraken_recognition_model(path, device=device)
    def _load_seg_model(self, path: str, device):
        return load_kraken_segmentation_model(path, device=device)
    def _tr(self, key: str, *args):
        try:
            lang = str(getattr(self.job, "language", None) or translation.DEFAULT_LANGUAGE)
            return translation.translate(lang, key, *args)
        except Exception:
            return str(key)

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
            raise ValueError(self._tr("ptr_err_no_rec_models"))
        if runs <= 0:
            raise ValueError(self._tr("ptr_err_runs_min"))
        return [rec_paths[i % len(rec_paths)] for i in range(runs)]
    def _ensure_models_loaded(self):
        if self._device is None:
            self._device = torch.device("cpu")
        if self._seg_model is None:
            if not self.job.segmentation_model_path:
                raise ValueError(self._tr("ptr_err_no_seg_model"))
            self._seg_model = self._load_seg_model(self.job.segmentation_model_path, self._device)
        for p in self._normalize_recognition_paths():
            if p not in self._rec_models:
                self._rec_models[p] = self._load_rec_model(p, self._device)
    def _release_loaded_models(self):
        try:
            self._seg_model = None
            self._rec_models.clear()
        except Exception:
            pass
        try:
            gc.collect()
        except Exception:
            pass
    def _emit_overall_progress(self, file_idx: int, total_files: int, frac: float):
        if total_files <= 0:
            self.progress.emit(0)
            return
        frac = max(0.0, min(1.0, float(frac)))
        overall = (file_idx + frac) / float(total_files)
        self.progress.emit(int(overall * 100))
    def _ocr_one_run(self, im: Image.Image, rec_model: Any) -> Tuple[str, list, List[RecordView]]:
        seg = segment_with_kraken(im, model=self._seg_model, device=self._device)
        kr_records: List[Any] = []
        for rec in recognize_with_kraken(rec_model, im, seg):
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
            bb = expand_segmentation_bbox(record_bbox(r), page_w, page_h)
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
                raise ValueError(self._tr("ptr_err_no_input_files"))
            if not rec_paths:
                raise ValueError(self._tr("ptr_err_no_rec_models"))
            if self.job.runs <= 0:
                raise ValueError(self._tr("ptr_err_runs_min"))
            for p in rec_paths:
                if not os.path.exists(p):
                    raise ValueError(self._tr("ptr_err_rec_model_missing", p))
            if not os.path.exists(self.job.segmentation_model_path or ""):
                raise ValueError(self._tr("ptr_err_baseline_missing"))
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
        finally:
            self._release_loaded_models()
class PtrMultiOcrDialog(QDialog):
    def __init__(self, rec_models: List[Tuple[str, str]], default_selected_paths: Optional[List[str]] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_ptr_dialog_tr(self, "multi_ocr_title"))
        self.setMinimumWidth(560)
        self._rec_models = rec_models
        self._default_selected = set(default_selected_paths or [])
        root = QVBoxLayout(self)
        root.addWidget(QLabel(_ptr_dialog_tr(self, "multi_ocr_runs_label")))
        self.spin_runs = QSpinBox()
        self.spin_runs.setRange(1, 99)
        self.spin_runs.setSingleStep(1)
        self.spin_runs.setValue(3)
        root.addWidget(self.spin_runs)
        root.addSpacing(8)
        root.addWidget(QLabel(_ptr_dialog_tr(self, "multi_ocr_rec_models_label")))
        self.list_models = QListWidget()
        self.list_models.setSelectionMode(QAbstractItemView.NoSelection)
        for name, path in self._rec_models:
            it = QListWidgetItem(name)
            it.setData(Qt.UserRole, path)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            checked = path in self._default_selected
            it.setCheckState(Qt.Checked if checked else Qt.Unchecked)
            self.list_models.addItem(it)
        if self.list_models.count() > 0 and not self.selected_recognition_paths():
            self.list_models.item(0).setCheckState(Qt.Checked)
        root.addWidget(self.list_models)
        self.chk_use_seg = QCheckBox(_ptr_dialog_tr(self, "multi_ocr_use_seg"))
        self.chk_use_seg.setChecked(True)
        root.addWidget(self.chk_use_seg)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        try:
            bb.button(QDialogButtonBox.Ok).setText(_ptr_dialog_tr(self, "btn_ok"))
            bb.button(QDialogButtonBox.Cancel).setText(_ptr_dialog_tr(self, "btn_cancel"))
        except Exception:
            pass
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        root.addWidget(bb)
    def runs(self) -> int:
        return int(self.spin_runs.value())
    def selected_recognition_paths(self) -> List[str]:
        out = []
        for i in range(self.list_models.count()):
            it = self.list_models.item(i)
            if it is not None and it.checkState() == Qt.Checked:
                p = it.data(Qt.UserRole)
                if p:
                    out.append(str(p))
        return out
    def use_segmentation(self) -> bool:
        return bool(self.chk_use_seg.isChecked())
def _ptr_dialog_translate(obj, key: str, *args) -> str:
    try:
        parent = obj.parent() if hasattr(obj, "parent") else None
        lang = getattr(parent, "current_lang", translation.DEFAULT_LANGUAGE)
        return translation.translate(lang, key, *args)
    except Exception:
        return key
class PtrMultiOCRFollowupDialog(QDialog):
    CHOICE_LOCAL = "local"
    CHOICE_AI = "ai"
    CHOICE_AI_POSTGRES = "ai_postgres"
    CHOICE_AI_NEO4J = "ai_neo4j"
    CHOICE_AI_BOTH = "ai_both"
    CHOICE_CANCEL = "cancel"
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_ptr_dialog_translate(self, "ptr_multi_followup_title"))
        self.resize(560, 220)
        self.choice = self.CHOICE_CANCEL
        root = QVBoxLayout(self)
        lbl = QLabel(_ptr_dialog_translate(self, "ptr_multi_followup_text"))
        lbl.setWordWrap(True)
        root.addWidget(lbl)
        row1 = QHBoxLayout()
        row2 = QHBoxLayout()
        self.local_btn = QPushButton(_ptr_dialog_translate(self, "ptr_multi_followup_local_merge"))
        self.ai_btn = QPushButton(_ptr_dialog_translate(self, "ptr_multi_followup_ai_tools"))
        self.ai_pg_btn = QPushButton(_ptr_dialog_translate(self, "ptr_multi_followup_ai_postgres"))
        self.ai_neo_btn = QPushButton(_ptr_dialog_translate(self, "ptr_multi_followup_ai_neo4j"))
        self.ai_both_btn = QPushButton(_ptr_dialog_translate(self, "ptr_multi_followup_ai_both"))
        self.cancel_btn = QPushButton(_ptr_dialog_translate(self, "ptr_multi_followup_cancel"))
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
    canceled = Signal(str)
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
        self._cancel_requested = False
        self._active_connection = None
        self._active_connection_lock = threading.Lock()
    def _tr(self, key: str, *args):
        try:
            owner = getattr(self.config, "_bk_prompt_owner", None)
            lang = getattr(owner, "current_lang", None) or getattr(owner, "_lang", lambda: None)()
            if not lang and hasattr(owner, "parent"):
                lang = getattr(owner.parent(), "current_lang", None)
            return translation.translate(lang or translation.DEFAULT_LANGUAGE, key, *args)
        except Exception:
            try:
                return translation.translate(translation.DEFAULT_LANGUAGE, key, *args)
            except Exception:
                return key
    def _raise_if_cancelled(self):
        if self._cancel_requested or self.isInterruptionRequested():
            raise PtrRemoteAICancelled(self._tr("ptr_ai_request_cancelled"))
    def _set_active_connection(self, connection):
        with self._active_connection_lock:
            self._active_connection = connection
    def _clear_active_connection(self, connection=None):
        with self._active_connection_lock:
            if connection is None or connection is self._active_connection:
                self._active_connection = None
    def _close_active_connection(self):
        with self._active_connection_lock:
            connection = self._active_connection
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass
    def cancel(self):
        self._cancel_requested = True
        try:
            self.requestInterruption()
        except Exception:
            pass
        self._close_active_connection()
    def _install_cancel_hooks(self):
        try:
            setattr(self.config, "_bk_cancel_checker", self._raise_if_cancelled)
            setattr(self.config, "_bk_connection_owner", self)
        except Exception:
            pass
    def _remove_cancel_hooks(self):
        for name in ("_bk_cancel_checker", "_bk_connection_owner"):
            try:
                if hasattr(self.config, name):
                    delattr(self.config, name)
            except Exception:
                pass
    def run(self):
        self._install_cancel_hooks()
        try:
            self._raise_if_cancelled()
            if self.mode == "merge":
                merged = _ptr_ai_merge_ocr_texts(self.config, self.ocr_texts)
                self._raise_if_cancelled()
                self.result_ready.emit({"mode": "merge", "merged_text": merged})
                return
            if self.mode == "postgres":
                merged = (self.merged_text or "").strip()
                if not merged:
                    merged = _ptr_ai_merge_ocr_texts(self.config, self.ocr_texts)
                    self._raise_if_cancelled()
                pg = _ptr_ai_build_postgres_json(self.config, merged)
                self._raise_if_cancelled()
                self.result_ready.emit({"mode": "postgres", "merged_text": merged, "postgres": pg})
                return
            if self.mode == "neo4j":
                merged = (self.merged_text or "").strip()
                if not merged:
                    merged = _ptr_ai_merge_ocr_texts(self.config, self.ocr_texts)
                    self._raise_if_cancelled()
                neo = _ptr_ai_build_neo4j_json(self.config, merged)
                self._raise_if_cancelled()
                self.result_ready.emit({"mode": "neo4j", "merged_text": merged, "neo4j": neo})
                return
            if self.mode == "pipeline":
                merged = _ptr_ai_merge_ocr_texts(self.config, self.ocr_texts)
                self._raise_if_cancelled()
                pg = _ptr_ai_build_postgres_json(self.config, merged) if self.include_postgres else None
                self._raise_if_cancelled()
                neo = _ptr_ai_build_neo4j_json(self.config, merged) if self.include_neo4j else None
                self._raise_if_cancelled()
                self.result_ready.emit({
                    "mode": "pipeline",
                    "merged_text": merged,
                    "postgres": pg,
                    "neo4j": neo,
                })
                return
            raise ValueError(self._tr("ptr_err_unknown_remote_mode", self.mode))
        except PtrRemoteAICancelled as exc:
            self.canceled.emit(str(exc) or self._tr("ptr_ai_request_cancelled"))
        except Exception as exc:
            if self._cancel_requested or self.isInterruptionRequested():
                self.canceled.emit(self._tr("ptr_ai_request_cancelled"))
            else:
                self.failed.emit(str(exc))
        finally:
            self._remove_cancel_hooks()
            self._close_active_connection()
__all__ = [
    'OCR_SOURCE_SEPARATOR',
    'PtrMultiOCRFollowupDialog',
    'PtrRemoteAICancelled',
    'PtrMultiOCRJob',
    'PtrMultiOCRWorker',
    'PtrMultiOcrDialog',
    'PtrRemoteAIConfig',
    'PtrRemoteAITaskWorker',
    '_ptr_dialog_lang',
    '_ptr_dialog_tr',
    '_ptr_dialog_translate',
]
register_globals('ptr', globals(), __all__)
