"""Worker-Klassen für Bottled Kraken."""
from ..shared import *

class PDFRenderWorker(QThread):
    progress = Signal(int, int, str)  # current, total, pdf_path
    finished_pdf = Signal(str, list)  # pdf_path, out_paths
    failed_pdf = Signal(str, str)  # pdf_path, error_message
    def __init__(self, pdf_path: str, dpi: int = 300, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.dpi = int(dpi)
    def run(self):
        out_paths: List[str] = []
        try:
            pdf_path = self.pdf_path
            dpi = self.dpi
            base = os.path.splitext(os.path.basename(pdf_path))[0]
            tmp_dir = os.path.join(os.path.dirname(pdf_path), f".kraken_tmp_{base}")
            os.makedirs(tmp_dir, exist_ok=True)
            doc = fitz.open(pdf_path)
            total = int(doc.page_count)
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            try:
                for i in range(total):
                    if self.isInterruptionRequested():
                        break
                    page = doc.load_page(i)
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    out = os.path.join(tmp_dir, f"{base}_p{i + 1:04d}.png")
                    pix.save(out)
                    out_paths.append(out)
                    self.progress.emit(i + 1, total, pdf_path)
            finally:
                doc.close()
            # auch wenn abgebrochen -> "fertig" mit dem was da ist
            self.finished_pdf.emit(pdf_path, out_paths)
        except Exception:
            self.failed_pdf.emit(self.pdf_path, traceback.format_exc())

class OCRWorker(QThread):
    file_started = Signal(str)
    file_done = Signal(str, str, list, object, list)
    file_error = Signal(str, str)
    progress = Signal(int)
    finished_batch = Signal()
    failed = Signal(str)
    device_resolved = Signal(str)
    gpu_info = Signal(str)
    def __init__(self, job: OCRJob):
        super().__init__()
        self.job = job
        self._device: Optional[torch.device] = None
        self._rec_model: Any = None
        self._seg_model: Any = None
        self._device_label: str = (job.device or "cpu").lower().strip()
    def _release_torch_resources(self):
        self._rec_model = None
        self._seg_model = None
        self._device = None
        try:
            gc.collect()
        except Exception:
            pass
        try:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
        try:
            if torch.cuda.is_available():
                torch.cuda.ipc_collect()
        except Exception:
            pass
    def _resolve_device(self) -> torch.device:
        dev = (self.job.device or "cpu").lower().strip()
        self._device_label = dev
        if dev in ("cuda", "rocm"):
            # CUDA und ROCm nutzen beide das torch.cuda-Backend; ROCm erkennt man an torch.version.hip
            if torch.cuda.is_available() and torch.cuda.device_count() > 0:
                return torch.device("cuda")
        if dev == "mps" and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        self._device_label = "cpu"
        return torch.device("cpu")
    def _emit_gpu_info(self, device: torch.device):
        try:
            if device.type == "cuda":
                name = torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else "GPU"
                hip_ver = getattr(torch.version, "hip", None)
                cuda_ver = getattr(torch.version, "cuda", None)
                # Wenn der Nutzer ROCm gewählt hat oder HIP vorhanden ist -> ROCm/HIP-Info anzeigen, sonst CUDA-Info
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
            elif device.type == "mps":
                self.gpu_info.emit("Apple MPS")
            else:
                self.gpu_info.emit("CPU")
        except Exception:
            pass
    def _load_rec_model(self, path: str, device: torch.device):
        try:
            return models.load_any(path, device=device)
        except TypeError:
            return models.load_any(path)
    def _load_seg_model(self, path: str, device: torch.device):
        try:
            return vgsl.TorchVGSLModel.load_model(path, device=device)
        except TypeError:
            return vgsl.TorchVGSLModel.load_model(path)
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
    # -------------------------------------------------------
    # OCRWorker._ocr_one
    # -------------------------------------------------------
    def _filter_short_baselines_in_seg(self, seg):
        try:
            if hasattr(seg, "baselines") and hasattr(seg, "lines") and seg.baselines and seg.lines:
                new_baselines = []
                new_lines = []
                for bl, ln in zip(seg.baselines, seg.lines):
                    if baseline_length(bl) >= 5.0:
                        new_baselines.append(bl)
                        new_lines.append(ln)
                seg.baselines = new_baselines
                seg.lines = new_lines
        except Exception:
            pass
        return seg
    def _ocr_using_preset_bboxes(
            self,
            img_path: str,
            im: Image.Image,
            preset_bboxes: List[Optional[BBox]],
            file_idx: int,
            total_files: int
    ) -> Tuple[str, List[RecordView]]:
        """
        Führt OCR direkt auf den vorhandenen Overlay-/Split-Boxen aus.
        Es wird KEINE neue Seitensegmentierung erzeugt.
        Jede Box ist genau eine Zielzeile.
        """
        page_w, page_h = im.size
        record_views: List[RecordView] = []
        valid_boxes: List[BBox] = []
        for bb in preset_bboxes:
            if not bb:
                continue
            clamped = clamp_bbox(bb, page_w, page_h)
            if not clamped:
                continue
            x0, y0, x1, y1 = clamped
            if x1 > x0 and y1 > y0:
                valid_boxes.append(clamped)
        total_boxes = max(1, len(valid_boxes))
        for box_idx, bb in enumerate(valid_boxes):
            if self.isInterruptionRequested():
                break
            x0, y0, x1, y1 = bb
            crop = im.crop((x0, y0, x1, y1))
            crop_records = []
            try:
                seg = blla.segment(crop, model=self._seg_model)
                seg = self._filter_short_baselines_in_seg(seg)
                for rec in rpred.rpred(self._rec_model, crop, seg):
                    crop_records.append(rec)
            except Exception:
                crop_records = []
            if crop_records:
                rec_model_name = os.path.basename(self.job.recognition_model_path).lower()
                if "handwriting" in rec_model_name:
                    crop_records = sort_records_handwriting_simple(
                        crop_records,
                        self.job.reading_direction
                    )
                else:
                    crop_records = sort_records_reading_order(
                        crop_records,
                        crop.size[0],
                        crop.size[1],
                        self.job.reading_direction
                    )
                parts = []
                for rec in crop_records:
                    pred = getattr(rec, "prediction", None)
                    txt = _clean_ocr_text(pred)
                    if txt and not _is_symbol_only_line(txt) and not _is_noise_line(txt):
                        parts.append(txt)
                final_text = " ".join(parts).strip()
            else:
                final_text = ""
            record_views.append(RecordView(len(record_views), final_text, bb))
            self._emit_overall_progress(file_idx, total_files, (box_idx + 1) / total_boxes)
        text = "\n".join(rv.text for rv in record_views).strip()
        return text, record_views
    def _ocr_one(self, img_path: str, file_idx: int, total_files: int):
        self.file_started.emit(img_path)
        try:
            # --- Bild einmalig laden (Graustufe) ---
            im_orig = _load_image_gray(img_path)
            orig_w, orig_h = im_orig.size
            # NEU: vorhandene Overlay-/Split-Boxen beim Re-OCR direkt verwenden
            preset_bboxes = self.job.preset_bboxes_by_path.get(img_path, []) or []
            if preset_bboxes:
                text, record_views = self._ocr_using_preset_bboxes(
                    img_path=img_path,
                    im=im_orig,
                    preset_bboxes=preset_bboxes,
                    file_idx=file_idx,
                    total_files=total_files
                )
                # kr_records bewusst leer: wir haben direkt auf den Zielboxen gearbeitet
                self.file_done.emit(img_path, text, [], im_orig, record_views)
                return
            im = im_orig
            scale_factor = 1.0
            # --- FIX A: zu kleine Bilder hochskalieren (verhindert Baselines < 5px) ---
            min_dim = min(im.size)
            if min_dim < 1200:
                scale_factor = 2 if min_dim >= 700 else 3
                im = im.resize((im.size[0] * scale_factor, im.size[1] * scale_factor), Image.BICUBIC)
            # --- Segmentierung ---
            seg = blla.segment(im, model=self._seg_model)
            # --- FIX B: winzige/kaputte Baselines entfernen (Baseline length below minimum 5px) ---
            try:
                if hasattr(seg, "baselines") and hasattr(seg, "lines") and seg.baselines and seg.lines:
                    new_baselines = []
                    new_lines = []
                    for bl, ln in zip(seg.baselines, seg.lines):
                        if baseline_length(bl) >= 5.0:
                            new_baselines.append(bl)
                            new_lines.append(ln)
                    seg.baselines = new_baselines
                    seg.lines = new_lines
            except Exception:
                pass
            expected = self._seg_expected_lines(seg)
            def _rescale_bbox(bb, factor):
                if not bb or factor == 1.0:
                    return bb
                x0, y0, x1, y1 = bb
                return (
                    int(round(x0 / factor)),
                    int(round(y0 / factor)),
                    int(round(x1 / factor)),
                    int(round(y1 / factor)),
                )
            # --- Erkennung (Recognition) ---
            kr_records = []
            done = 0
            try:
                for rec in rpred.rpred(self._rec_model, im, seg):
                    kr_records.append(rec)
                    done += 1
                    if expected and expected > 0:
                        self._emit_overall_progress(file_idx, total_files, done / expected)
                    if self.isInterruptionRequested():
                        break
            except Exception:
                self.file_error.emit(img_path, traceback.format_exc())
                return
            if self.isInterruptionRequested():
                return
            rec_model_name = os.path.basename(self.job.recognition_model_path).lower()
            if "handwriting" in rec_model_name:
                kr_sorted = sort_records_handwriting_simple(
                    kr_records,
                    self.job.reading_direction
                )
            else:
                kr_sorted = sort_records_reading_order(
                    kr_records,
                    im.size[0],
                    im.size[1],
                    self.job.reading_direction
                )
            # --- WIDE LINE SPLIT: nur echte 2-Spalten-Zeilen splitten, Header NICHT ---
            def _is_header_like(bb, txt, page_w, page_h):
                x0, y0, x1, y1 = bb
                w = x1 - x0
                cx = (x0 + x1) / 2.0
                if w < 0.72 * page_w:
                    return False
                if abs(cx - (page_w / 2.0)) > 0.20 * page_w:
                    return False
                if y0 > 0.45 * page_h:
                    return False
                if len((txt or "").strip()) > 90:
                    return False
                return True
            two_col_splitter = re.compile(r"\s{4,}")
            record_views: List[RecordView] = []
            lines: List[str] = []
            out_idx = 0
            page_w, page_h = orig_w, orig_h
            for r in kr_sorted:
                pred = getattr(r, "prediction", None)
                if pred is None:
                    continue
                txt = _clean_ocr_text(pred)
                if _is_effectively_empty_ocr_text(txt) or _is_symbol_only_line(txt) or _is_noise_line(txt):
                    continue
                bb = record_bbox(r)
                bb = _rescale_bbox(bb, scale_factor)
                split_done = False
                if bb:
                    x0, y0, x1, y1 = bb
                    w = x1 - x0
                    if w > int(page_w * 0.80) and not _is_header_like(bb, txt, page_w, page_h):
                        parts = two_col_splitter.split(txt, maxsplit=1)
                        if len(parts) == 2:
                            left_txt, right_txt = map(_clean_ocr_text, parts)
                            mid = page_w // 2
                            left_bb = clamp_bbox((0, y0, mid, y1), page_w, page_h)
                            right_bb = clamp_bbox((mid, y0, page_w, y1), page_w, page_h)
                            parts_in_order = []
                            if left_bb and left_txt:
                                parts_in_order.append((left_txt, left_bb))
                            if right_bb and right_txt:
                                parts_in_order.append((right_txt, right_bb))
                            rev_x = self.job.reading_direction in (
                                READING_MODES["TB_RL"],
                                READING_MODES["BT_RL"]
                            )
                            if rev_x:
                                parts_in_order = list(reversed(parts_in_order))
                            if parts_in_order:
                                for txt_part, bb_part in parts_in_order:
                                    record_views.append(RecordView(out_idx, txt_part, bb_part))
                                    lines.append(txt_part)
                                    out_idx += 1
                                split_done = True
                if split_done:
                    continue
                record_views.append(RecordView(out_idx, txt, bb))
                lines.append(txt)
                out_idx += 1
            filtered_record_views: List[RecordView] = []
            filtered_lines: List[str] = []
            for rv in record_views:
                rv.text = _clean_ocr_text(rv.text)
                if _is_effectively_empty_ocr_text(rv.text) or _is_symbol_only_line(rv.text) or _is_noise_line(rv.text):
                    continue
                rv.idx = len(filtered_record_views)
                filtered_record_views.append(rv)
                filtered_lines.append(rv.text)
            record_views = filtered_record_views
            lines = filtered_lines
            self._emit_overall_progress(file_idx, total_files, 1.0)
            text = "\n".join(lines).strip()
            self.file_done.emit(img_path, text, kr_sorted, im, record_views)
        except Exception:
            self.file_error.emit(img_path, traceback.format_exc())
    def run(self):
        try:
            if not os.path.exists(self.job.recognition_model_path):
                raise ValueError("Recognition model not found.")
            if not os.path.exists(self.job.segmentation_model_path or ""):
                raise ValueError("blla segmentation model not found.")
            self._ensure_models_loaded()
            total = len(self.job.input_paths)
            for i, path in enumerate(self.job.input_paths):
                if self.isInterruptionRequested():
                    break
                self._emit_overall_progress(i, total, 0.0)
                self._ocr_one(path, i, total)
            self.progress.emit(100)
            self.finished_batch.emit()
        except Exception:
            self.failed.emit(traceback.format_exc())
        finally:
            self._release_torch_resources()
