from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('ptr', globals())
def _ptr_multi_default_variant_keys():
    return ["original", "autocontrast", "contrast", "sharp", "gray_autocontrast"]
def _ptr_multi_variant_specs():
    return [
        ("original", "multi_ocr_variant_original", True),
        ("autocontrast", "multi_ocr_variant_autocontrast", True),
        ("contrast", "multi_ocr_variant_contrast", True),
        ("sharp", "multi_ocr_variant_sharp", True),
        ("gray_autocontrast", "multi_ocr_variant_gray_autocontrast", True),
        ("binary_otsu", "multi_ocr_variant_binary_otsu", False),
        ("contrast_sharp", "multi_ocr_variant_contrast_sharp", False),
        ("equalize", "multi_ocr_variant_equalize", False),
        ("slightly_bright", "multi_ocr_variant_slightly_bright", False),
    ]
def _ptr_multi_valid_variant_keys():
    return {key for key, _label_key, _default_checked in _ptr_multi_variant_specs()}
def _ptr_multi_clean_variant_keys(keys):
    valid = _ptr_multi_valid_variant_keys()
    selected = []
    seen = set()
    for key in list(keys or []):
        text = str(key or "").strip()
        if text and text in valid and text not in seen:
            selected.append(text)
            seen.add(text)
    return selected or ["original"]
def _ptr_multi_variant_keys_from_count(count: int):
    try:
        count = max(1, min(len(_ptr_multi_variant_specs()), int(count or 1)))
    except Exception:
        count = len(_ptr_multi_default_variant_keys())
    return [key for key, _label_key, _default_checked in _ptr_multi_variant_specs()[:count]]
def _ptr_multi_selected_variant_keys_from_job(job):
    keys = _ptr_multi_clean_variant_keys(getattr(job, "image_variant_keys", None))
    if keys:
        return keys
    if bool(getattr(job, "image_variants_enabled", False)):
        return _ptr_multi_variant_keys_from_count(getattr(job, "image_variant_count", 1))
    return ["original"]
def _ptr_multi_translate_job(job, key: str, *args):
    try:
        lang = str(getattr(job, "language", None) or translation.DEFAULT_LANGUAGE)
        return translation.translate(lang, key, *args)
    except Exception:
        return str(key)
def _ptr_multi_normalize_page_image(im):
    try:
        if im.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", im.size, (255, 255, 255))
            converted = im.convert("RGBA")
            background.paste(converted, mask=converted.getchannel("A"))
            return background
        if im.mode != "RGB":
            return im.convert("RGB")
    except Exception:
        pass
    return im.copy()
def _ptr_multi_otsu_threshold(gray):
    try:
        hist = gray.histogram()
        total = sum(hist)
        if total <= 0:
            return 127
        sum_total = sum(i * hist[i] for i in range(256))
        sum_b = 0.0
        weight_b = 0
        best_threshold = 127
        best_variance = -1.0
        for threshold in range(256):
            weight_b += hist[threshold]
            if weight_b <= 0:
                continue
            weight_f = total - weight_b
            if weight_f <= 0:
                break
            sum_b += threshold * hist[threshold]
            mean_b = sum_b / float(weight_b)
            mean_f = (sum_total - sum_b) / float(weight_f)
            variance = weight_b * weight_f * ((mean_b - mean_f) ** 2)
            if variance > best_variance:
                best_variance = variance
                best_threshold = threshold
        return int(best_threshold)
    except Exception:
        return 127
def _ptr_multi_binary_variant(base):
    gray = ImageOps.grayscale(base)
    threshold = _ptr_multi_otsu_threshold(gray)
    return gray.point(lambda px: 255 if px > threshold else 0).convert("RGB")
def _ptr_multi_variant_builder_map():
    return {
        "original": ("multi_ocr_variant_original", lambda src: src.copy()),
        "autocontrast": ("multi_ocr_variant_autocontrast", lambda src: ImageOps.autocontrast(src)),
        "contrast": ("multi_ocr_variant_contrast", lambda src: ImageEnhance.Contrast(src).enhance(1.25)),
        "sharp": ("multi_ocr_variant_sharp", lambda src: ImageEnhance.Sharpness(src).enhance(1.60)),
        "gray_autocontrast": (
            "multi_ocr_variant_gray_autocontrast",
            lambda src: ImageOps.autocontrast(ImageOps.grayscale(src)).convert("RGB"),
        ),
        "binary_otsu": ("multi_ocr_variant_binary_otsu", lambda src: _ptr_multi_binary_variant(src)),
        "contrast_sharp": (
            "multi_ocr_variant_contrast_sharp",
            lambda src: ImageEnhance.Sharpness(ImageEnhance.Contrast(src).enhance(1.18)).enhance(1.40),
        ),
        "equalize": ("multi_ocr_variant_equalize", lambda src: ImageOps.equalize(src)),
        "slightly_bright": (
            "multi_ocr_variant_slightly_bright",
            lambda src: ImageEnhance.Brightness(src).enhance(1.05),
        ),
    }
def _ptr_multi_build_selected_image_variants(im, variant_keys, job=None):
    base = _ptr_multi_normalize_page_image(im)
    builders = _ptr_multi_variant_builder_map()
    variants = []
    for key in _ptr_multi_clean_variant_keys(variant_keys):
        label_key, builder = builders.get(key, builders["original"])
        try:
            candidate = builder(base)
            if candidate.size != base.size:
                candidate = candidate.resize(base.size)
            if candidate.mode != "RGB":
                candidate = candidate.convert("RGB")
        except Exception:
            candidate = base.copy()
        label = _ptr_multi_translate_job(job, label_key) if job is not None else str(label_key)
        variants.append((key, label, candidate))
    return variants or [("original", _ptr_multi_translate_job(job, "multi_ocr_variant_original"), base.copy())]
def _ptr_build_model_variant_run_plan(self, rec_paths, runs):
    if not rec_paths:
        raise ValueError("No recognition models selected.")
    try:
        count = max(1, int(runs))
    except Exception:
        count = 1
    plan = []
    for _repeat in range(count):
        for rec_path in rec_paths:
            plan.append(rec_path)
    return plan
def _ptr_multi_ocr_job_init_v9(self, input_paths, recognition_model_paths, segmentation_model_path,
                               device, reading_direction, runs, image_variants_enabled=False,
                               image_variant_count=1, image_variant_keys=None, language=None):
    self.input_paths = input_paths or []
    self.recognition_model_paths = recognition_model_paths or []
    self.segmentation_model_path = segmentation_model_path
    self.device = device
    self.reading_direction = int(reading_direction)
    self.runs = int(runs)
    if image_variant_keys is None:
        if image_variants_enabled:
            image_variant_keys = _ptr_multi_variant_keys_from_count(image_variant_count)
        else:
            image_variant_keys = ["original"]
    self.image_variant_keys = _ptr_multi_clean_variant_keys(image_variant_keys)
    self.image_variants_enabled = bool(self.image_variant_keys)
    self.image_variant_count = len(self.image_variant_keys)
    self.language = language or translation.DEFAULT_LANGUAGE
def _ptr_multi_ocr_worker_ocr_multi_for_file_with_meta(self, img_path: str, file_idx: int, total_files: int):
    self.file_started.emit(img_path)
    with Image.open(img_path) as im:
        im = im.copy()
    display_image = _ptr_multi_normalize_page_image(im)
    variant_entries = []
    plain_texts = []
    last_sorted = []
    last_views = []
    rec_paths = self._normalize_recognition_paths()
    run_plan = self._build_run_plan(rec_paths, self.job.runs)
    selected_keys = _ptr_multi_selected_variant_keys_from_job(self.job)
    page_variants = _ptr_multi_build_selected_image_variants(display_image, selected_keys, self.job)
    total_runs = max(1, len(run_plan) * len(page_variants))
    done_runs = 0
    for _run_i, rec_path in enumerate(run_plan):
        if self.isInterruptionRequested():
            return
        rec_model = self._rec_models[rec_path]
        for variant_key, variant_label, variant_image in page_variants:
            if self.isInterruptionRequested():
                return
            text, kr_sorted, record_views = self._ocr_one_run(variant_image, rec_model)
            safe_views = _ptr_clone_record_views(record_views)
            variant_text = "\n".join(rv.text for rv in safe_views).strip() or text
            plain_texts.append(variant_text)
            base_model_name = _ptr_model_display_name(rec_path)
            model_name = base_model_name if len(page_variants) == 1 else f"{base_model_name} — {variant_label}"
            variant_entries.append({
                "run_index": len(variant_entries) + 1,
                "model_path": rec_path,
                "model_name": model_name,
                "image_variant": variant_key,
                "image_variant_name": variant_label,
                "text": variant_text,
                "kr_sorted": kr_sorted or [],
                "record_views": safe_views,
            })
            last_sorted = kr_sorted
            last_views = safe_views
            done_runs += 1
            self._emit_overall_progress(file_idx, total_files, done_runs / float(total_runs))
    merged = _ptr_merge_ocr_texts_local(plain_texts)
    self.file_done.emit(img_path, merged, last_sorted, display_image, last_views, variant_entries)
def _ptr_multi_model_label(name, path):
    try:
        return str(name or os.path.basename(str(path or "")) or path or "")
    except Exception:
        return str(name or path or "")
def _ptr_multi_dialog_init_checklist(self, rec_models, default_selected_paths=None, parent=None):
    QDialog.__init__(self, parent)
    self.setWindowTitle(_ptr_dialog_tr(self, "multi_ocr_title"))
    self.setMinimumWidth(620)
    self.resize(620, 520)
    self._rec_models = list(rec_models or [])
    self._default_selected = set(str(p) for p in (default_selected_paths or []) if p)
    root = QVBoxLayout(self)
    root.setContentsMargins(12, 12, 12, 12)
    root.setSpacing(8)
    root.addWidget(QLabel(_ptr_dialog_tr(self, "multi_ocr_models_section"), self))
    label = QLabel(_ptr_dialog_tr(self, "multi_ocr_rec_models_label"), self)
    label.setWordWrap(True)
    root.addWidget(label)
    self.list_models = QListWidget(self)
    self.list_models.setAlternatingRowColors(True)
    self.list_models.setSelectionMode(QAbstractItemView.NoSelection)
    self.list_models.setMinimumHeight(120)
    self.list_models.setStyleSheet("QListWidget::item { padding: 5px 6px; } QListWidget::indicator { width: 18px; height: 18px; }")
    default_all = not bool(self._default_selected)
    for name, path in self._rec_models:
        path = str(path or "")
        item = QListWidgetItem(_ptr_multi_model_label(name, path))
        item.setToolTip(path or item.text())
        item.setData(Qt.UserRole, path)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        item.setCheckState(Qt.Checked if (default_all or path in self._default_selected) else Qt.Unchecked)
        self.list_models.addItem(item)
    if self.list_models.count() > 0 and not self.selected_recognition_paths():
        self.list_models.item(0).setCheckState(Qt.Checked)
    root.addWidget(self.list_models, 1)
    variants_header = QHBoxLayout()
    variants_header.addWidget(QLabel(_ptr_dialog_tr(self, "multi_ocr_variants_section"), self))
    self.btn_image_variants_help = QToolButton(self)
    self.btn_image_variants_help.setText("?")
    self.btn_image_variants_help.setFixedSize(32, 24)
    self.btn_image_variants_help.setToolTip(_ptr_dialog_tr(self, "multi_ocr_variants_help_button_tooltip"))
    self.btn_image_variants_help.clicked.connect(lambda: _ptr_multi_show_variant_help(self))
    variants_header.addWidget(self.btn_image_variants_help)
    variants_header.addStretch(1)
    root.addLayout(variants_header)
    variants_label = QLabel(_ptr_dialog_tr(self, "multi_ocr_variants_label"), self)
    variants_label.setWordWrap(True)
    root.addWidget(variants_label)
    self.list_image_variants = QListWidget(self)
    self.list_image_variants.setAlternatingRowColors(True)
    self.list_image_variants.setSelectionMode(QAbstractItemView.NoSelection)
    self.list_image_variants.setMinimumHeight(135)
    self.list_image_variants.setStyleSheet("QListWidget::item { padding: 4px 6px; } QListWidget::indicator { width: 18px; height: 18px; }")
    for key, label_key, default_checked in _ptr_multi_variant_specs():
        item = QListWidgetItem(_ptr_dialog_tr(self, label_key))
        item.setData(Qt.UserRole, key)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        item.setCheckState(Qt.Checked if default_checked else Qt.Unchecked)
        self.list_image_variants.addItem(item)
    root.addWidget(self.list_image_variants, 1)
    root.addWidget(QLabel(_ptr_dialog_tr(self, "multi_ocr_runs_section"), self))
    runs_row = QHBoxLayout()
    runs_label = QLabel(_ptr_dialog_tr(self, "multi_ocr_runs_label"), self)
    runs_label.setWordWrap(True)
    runs_row.addWidget(runs_label)
    self.spin_runs = QSpinBox(self)
    self.spin_runs.setRange(1, 99)
    self.spin_runs.setSingleStep(1)
    self.spin_runs.setValue(1)
    self.spin_runs.setFixedWidth(82)
    runs_row.addWidget(self.spin_runs)
    runs_row.addStretch(1)
    root.addLayout(runs_row)
    seg_note = QLabel(_ptr_dialog_tr(self, "multi_ocr_seg_model_fixed"), self)
    seg_note.setWordWrap(True)
    root.addWidget(seg_note)
    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
    try:
        buttons.button(QDialogButtonBox.Ok).setText(_ptr_dialog_tr(self, "btn_ok"))
        buttons.button(QDialogButtonBox.Cancel).setText(_ptr_dialog_tr(self, "btn_cancel"))
    except Exception:
        pass
    buttons.accepted.connect(self.accept)
    buttons.rejected.connect(self.reject)
    root.addWidget(buttons)
def _ptr_dialog_selected_recognition_paths(self):
    paths = []
    seen = set()
    for i in range(self.list_models.count()):
        item = self.list_models.item(i)
        if item is None or item.checkState() != Qt.Checked:
            continue
        path = str(item.data(Qt.UserRole) or "")
        if path and path not in seen:
            paths.append(path)
            seen.add(path)
    return paths
def _ptr_dialog_selected_image_variant_keys(self):
    keys = []
    seen = set()
    view = getattr(self, "list_image_variants", None)
    if view is not None:
        for i in range(view.count()):
            item = view.item(i)
            if item is None or item.checkState() != Qt.Checked:
                continue
            key = str(item.data(Qt.UserRole) or "")
            if key and key not in seen:
                keys.append(key)
                seen.add(key)
    keys = _ptr_multi_clean_variant_keys(keys)
    if view is not None and not keys:
        for i in range(view.count()):
            item = view.item(i)
            if item is not None and str(item.data(Qt.UserRole) or "") == "original":
                item.setCheckState(Qt.Checked)
                return ["original"]
    return keys
def _ptr_dialog_image_variants_enabled(self) -> bool:
    return bool(_ptr_dialog_selected_image_variant_keys(self))
def _ptr_dialog_image_variant_count(self) -> int:
    return len(_ptr_dialog_selected_image_variant_keys(self))
def _ptr_dialog_use_segmentation(self) -> bool:
    return True
try:
    PtrMultiOCRJob.__init__ = _ptr_multi_ocr_job_init_v9
    PtrMultiOCRWorker._build_run_plan = _ptr_build_model_variant_run_plan
    PtrMultiOCRWorker._ocr_multi_for_file = _ptr_multi_ocr_worker_ocr_multi_for_file_with_meta
    PtrMultiOcrDialog.__init__ = _ptr_multi_dialog_init_checklist
    PtrMultiOcrDialog.selected_recognition_paths = _ptr_dialog_selected_recognition_paths
    PtrMultiOcrDialog.selected_image_variant_keys = _ptr_dialog_selected_image_variant_keys
    PtrMultiOcrDialog.use_segmentation = _ptr_dialog_use_segmentation
    PtrMultiOcrDialog.image_variants_enabled = _ptr_dialog_image_variants_enabled
    PtrMultiOcrDialog.image_variant_count = _ptr_dialog_image_variant_count
except Exception:
    pass
def _ptr_on_multi_file_done(self, path: str, merged_text: str, last_sorted: list, im: object, last_views: list, variants: list):
    entries = _ptr_variant_entries_from_raw(variants)
    if not entries:
        safe_views = _ptr_clone_record_views(last_views or [])
        text = "\n".join(rv.text for rv in safe_views).strip() or str(merged_text or "")
        entries = [{
            "run_index": 1,
            "model_path": "",
            "model_name": "",
            "text": text,
            "kr_sorted": last_sorted or [],
            "record_views": safe_views or _ptr_recs_from_text(text),
        }]
    task = _ptr_get_task(self, path)
    if task:
        task.status = STATUS_DONE
        task.results = _ptr_entry_to_results(entries[0], im)
        task.edited = False
        try:
            task.undo_stack.clear()
            task.redo_stack.clear()
        except Exception:
            pass
        self._update_queue_row(path)
    if not hasattr(self, "_ptr_multi_ocr_variant_meta_by_path"):
        self._ptr_multi_ocr_variant_meta_by_path = {}
    if not hasattr(self, "_ptr_multi_ocr_variants_by_path"):
        self._ptr_multi_ocr_variants_by_path = {}
    if not hasattr(self, "_ptr_multi_ocr_active_index_by_path"):
        self._ptr_multi_ocr_active_index_by_path = {}
    self._ptr_multi_ocr_variant_meta_by_path[path] = entries
    self._ptr_multi_ocr_variants_by_path[path] = [entry.get("text", "") for entry in entries]
    self._ptr_multi_ocr_active_index_by_path[path] = 0
    if (merged_text or "").strip():
        self._ptr_ai_merged_by_path[path] = merged_text.strip()
    self._ptr_last_multi_followup_path = path
    if not hasattr(self, "_ptr_multi_processed_paths"):
        self._ptr_multi_processed_paths = []
    self._ptr_multi_processed_paths.append(path)
    current = self._current_task() if hasattr(self, "_current_task") else None
    if current is not None and getattr(current, "path", "") == path:
        _ptr_apply_variant(self, path, 0, save_current=False)
    else:
        _ptr_refresh_tabs(self, _ptr_current_path(self))
_PTR_PREV_LOAD_RESULTS = getattr(MainWindow, "load_results", None)
def _ptr_load_results_with_variant_tabs(self, path: str, *args, **kwargs):
    if not getattr(self, "_ptr_variant_loading", False):
        old_path = str(getattr(self, "_ptr_active_multi_ocr_path", "") or "")
        if old_path:
            _ptr_save_active_variant(self)
    result = _PTR_PREV_LOAD_RESULTS(self, path, *args, **kwargs) if callable(_PTR_PREV_LOAD_RESULTS) else None
    try:
        path = str(path or _ptr_current_path(self) or "")
        entries = _ptr_entries_for_path(self, path, create=True) if path else []
        active_map = getattr(self, "_ptr_multi_ocr_active_index_by_path", {}) or {}
        index = int(active_map.get(path, 0) or 0) if entries else 0
        self._ptr_active_multi_ocr_path = path
        self._ptr_active_multi_ocr_index = max(0, min(index, max(0, len(entries) - 1)))
        _ptr_refresh_tabs(self, path)
    except Exception:
        pass
    return result
_PTR_PREV_PREVIEW_IMAGE = getattr(MainWindow, "preview_image", None)
def _ptr_preview_image_with_variant_tabs(self, path: str, *args, **kwargs):
    if not getattr(self, "_ptr_variant_loading", False):
        _ptr_save_active_variant(self)
    result = _PTR_PREV_PREVIEW_IMAGE(self, path, *args, **kwargs) if callable(_PTR_PREV_PREVIEW_IMAGE) else None
    try:
        _ptr_refresh_tabs(self, path)
    except Exception:
        pass
    return result
_PTR_TABS_PREV_MAINWINDOW_INIT = MainWindow.__init__
def _ptr_mainwindow_init_with_variant_tabs(self, *args, **kwargs):
    _PTR_TABS_PREV_MAINWINDOW_INIT(self, *args, **kwargs)
    self._ptr_multi_ocr_variant_meta_by_path = getattr(self, "_ptr_multi_ocr_variant_meta_by_path", {}) or {}
    self._ptr_multi_ocr_active_index_by_path = getattr(self, "_ptr_multi_ocr_active_index_by_path", {}) or {}
    self._ptr_multi_ocr_variants_by_path = getattr(self, "_ptr_multi_ocr_variants_by_path", {}) or {}
    self._ptr_active_multi_ocr_path = ""
    self._ptr_active_multi_ocr_index = -1
    try:
        _ptr_ensure_tabs(self)
        _ptr_refresh_tabs(self, _ptr_current_path(self))
    except Exception:
        pass
_PTR_TABS_PREV_RETRANSLATE = MainWindow.retranslate_ui
def _ptr_retranslate_with_variant_tabs(self, *args, **kwargs):
    _PTR_TABS_PREV_RETRANSLATE(self, *args, **kwargs)
    try:
        _ptr_refresh_tabs(self, _ptr_current_path(self))
    except Exception:
        pass
try:
    MainWindow.__init__ = _ptr_mainwindow_init_with_variant_tabs
    MainWindow.retranslate_ui = _ptr_retranslate_with_variant_tabs
    MainWindow.load_results = _ptr_load_results_with_variant_tabs
    MainWindow.preview_image = _ptr_preview_image_with_variant_tabs
    MainWindow._ptr_on_multi_file_done = _ptr_on_multi_file_done
    MainWindow._ptr_ensure_multi_ocr_tabs = _ptr_ensure_tabs
    MainWindow._ptr_show_multi_ocr_variant_tabs = _ptr_refresh_tabs
    MainWindow._ptr_apply_multi_ocr_variant = _ptr_apply_variant
    MainWindow._ptr_sync_active_multi_variant = _ptr_save_active_variant
    MainWindow._ptr_add_ocr_variant_tab = _ptr_add_variant
except Exception:
    pass
__all__ = [
    '_PTR_PREV_LOAD_RESULTS',
    '_PTR_PREV_PREVIEW_IMAGE',
    '_PTR_TABS_PREV_MAINWINDOW_INIT',
    '_PTR_TABS_PREV_RETRANSLATE',
    '_ptr_build_model_variant_run_plan',
    '_ptr_dialog_image_variant_count',
    '_ptr_dialog_image_variants_enabled',
    '_ptr_dialog_selected_image_variant_keys',
    '_ptr_dialog_selected_recognition_paths',
    '_ptr_dialog_use_segmentation',
    '_ptr_load_results_with_variant_tabs',
    '_ptr_mainwindow_init_with_variant_tabs',
    '_ptr_multi_binary_variant',
    '_ptr_multi_build_selected_image_variants',
    '_ptr_multi_clean_variant_keys',
    '_ptr_multi_default_variant_keys',
    '_ptr_multi_dialog_init_checklist',
    '_ptr_multi_model_label',
    '_ptr_multi_normalize_page_image',
    '_ptr_multi_ocr_job_init_v9',
    '_ptr_multi_ocr_worker_ocr_multi_for_file_with_meta',
    '_ptr_multi_otsu_threshold',
    '_ptr_multi_selected_variant_keys_from_job',
    '_ptr_multi_translate_job',
    '_ptr_multi_valid_variant_keys',
    '_ptr_multi_variant_builder_map',
    '_ptr_multi_variant_keys_from_count',
    '_ptr_multi_variant_specs',
    '_ptr_on_multi_file_done',
    '_ptr_preview_image_with_variant_tabs',
    '_ptr_retranslate_with_variant_tabs',
]
register_globals('ptr', globals(), __all__)
