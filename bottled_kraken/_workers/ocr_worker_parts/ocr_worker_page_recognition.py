from bottled_kraken.runtime_logging import get_logger

from bottled_kraken.common import (
    _clean_ocr_text_for_kraken_display,
    _is_effectively_empty_ocr_text,
    _is_noise_line,
    _is_symbol_only_line,
    _load_image_gray,
)
from bottled_kraken.common import (
    Image,
    List,
    READING_MODES,
    RecordView,
    baseline_length,
    clamp_bbox,
    expand_segmentation_bbox,
    os,
    re,
    recognize_with_kraken,
    record_bbox,
    segment_with_kraken,
    sort_records_handwriting_simple,
    sort_records_reading_order,
    torch,
    traceback,
)
MAX_KRAKEN_OCR_LINES = 500
class OCRWorkerPageRecognitionMixin:
        def _ocr_one(self, img_path: str, file_idx: int, total_files: int):
            self.file_started.emit(img_path)
            im_orig = None
            im = None
            seg = None
            kr_records = []
            kr_sorted = []
            try:
                im_orig = _load_image_gray(img_path)
                orig_w, orig_h = im_orig.size
                preset_bboxes = self.job.preset_bboxes_by_path.get(img_path, []) or []
                if preset_bboxes:
                    text, record_views = self._ocr_using_preset_bboxes(
                        img_path=img_path,
                        im=im_orig,
                        preset_bboxes=preset_bboxes,
                        file_idx=file_idx,
                        total_files=total_files
                    )
                    self.file_done.emit(img_path, text, [], None, record_views)
                    return
                im = im_orig
                scale_factor = 1.0
                min_dim = min(im.size)
                if min_dim < 1200:
                    scale_factor = 2 if min_dim >= 700 else 3
                    im = im.resize((im.size[0] * scale_factor, im.size[1] * scale_factor), Image.BICUBIC)
                with torch.no_grad():
                    seg = segment_with_kraken(im, model=self._seg_model, device=self._device)
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
                kr_records = []
                done = 0
                try:
                    with torch.no_grad():
                        for rec in recognize_with_kraken(self._rec_model, im, seg):
                            kr_records.append(rec)
                            done += 1
                            if expected and expected > 0:
                                self._emit_overall_progress(file_idx, total_files, done / expected)
                            if self.isInterruptionRequested():
                                break
                except Exception:
                    get_logger("workers.ocr").exception(
                        "Kraken recognition failed for %s", img_path
                    )
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
                    txt = _clean_ocr_text_for_kraken_display(pred, getattr(self.job, "auto_revision_enabled", False), getattr(self.job, "auto_revision_replacements", None))
                    if _is_effectively_empty_ocr_text(txt) or _is_symbol_only_line(txt) or _is_noise_line(txt):
                        continue
                    bb = record_bbox(r)
                    bb = _rescale_bbox(bb, scale_factor)
                    bb = expand_segmentation_bbox(bb, page_w, page_h)
                    split_done = False
                    if bb:
                        x0, y0, x1, y1 = bb
                        w = x1 - x0
                        if w > int(page_w * 0.80) and not _is_header_like(bb, txt, page_w, page_h):
                            parts = two_col_splitter.split(txt, maxsplit=1)
                            if len(parts) == 2:
                                left_txt, right_txt = [_clean_ocr_text_for_kraken_display(part, getattr(self.job, "auto_revision_enabled", False), getattr(self.job, "auto_revision_replacements", None)) for part in parts]
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
                    rv.text = _clean_ocr_text_for_kraken_display(rv.text, getattr(self.job, "auto_revision_enabled", False), getattr(self.job, "auto_revision_replacements", None))
                    if _is_effectively_empty_ocr_text(rv.text) or _is_symbol_only_line(rv.text) or _is_noise_line(rv.text):
                        continue
                    rv.idx = len(filtered_record_views)
                    filtered_record_views.append(rv)
                    filtered_lines.append(rv.text)
                record_views = filtered_record_views
                lines = filtered_lines
                if len(record_views) >= 190:
                    tiled = self._ocr_one_tiled_lines(img_path, im_orig, file_idx, total_files)
                    if tiled:
                        tiled_text, tiled_views = tiled
                        if len(tiled_views) > len(record_views):
                            text = tiled_text
                            record_views = tiled_views
                            lines = [rv.text for rv in record_views]
                        else:
                            text = "\n".join(lines).strip()
                    else:
                        text = "\n".join(lines).strip()
                else:
                    text = "\n".join(lines).strip()
                self._emit_overall_progress(file_idx, total_files, 1.0)
                self.file_done.emit(img_path, text, [], None, record_views)
            except Exception:
                get_logger("workers.ocr").exception("OCR failed for %s", img_path)
                self.file_error.emit(img_path, traceback.format_exc())
            finally:
                try:
                    if im is not None and im is not im_orig:
                        im.close()
                except Exception:
                    pass
                try:
                    if im_orig is not None:
                        im_orig.close()
                except Exception:
                    pass
                seg = None
                kr_records = []
                kr_sorted = []
                self._soft_page_cleanup()
        def run(self):
            err = None
            ok = False
            try:
                if not os.path.exists(self.job.recognition_model_path):
                    raise ValueError(self._tr("ptr_err_rec_model_missing_generic"))
                if not os.path.exists(self.job.segmentation_model_path or ""):
                    raise ValueError(self._tr("ptr_err_baseline_missing"))
                self._ensure_models_loaded()
                total = len(self.job.input_paths)
                reset_every = self._ocr_reset_every()
                for i, path in enumerate(self.job.input_paths):
                    if self.isInterruptionRequested():
                        break
                    self._emit_overall_progress(i, total, 0.0)
                    self._ocr_one(path, i, total)
                    self._soft_page_cleanup()
                    if reset_every > 0 and (i + 1) < total and ((i + 1) % reset_every) == 0:
                        self.status_info.emit(self._tr("ocr_status_memory_reloaded", i + 1))
                        self._release_torch_resources()
                        if self.isInterruptionRequested():
                            break
                        self._ensure_models_loaded()
                self.progress.emit(100)
                ok = True
            except Exception:
                get_logger("workers.ocr").exception("OCR batch worker failed")
                err = traceback.format_exc()
            finally:
                self._release_torch_resources()
            if err:
                self.failed.emit(err)
            elif ok:
                self.finished_batch.emit()
