from bottled_kraken.common import (
    _clean_ocr_text_for_kraken_display,
    _is_effectively_empty_ocr_text,
    _is_noise_line,
    _is_symbol_only_line,
)
from bottled_kraken.common import (
    Image,
    List,
    RecordView,
    expand_segmentation_bbox,
    os,
    recognize_with_kraken,
    record_bbox,
    segment_with_kraken,
    sort_records_handwriting_simple,
    sort_records_reading_order,
    torch,
)
MAX_KRAKEN_OCR_LINES = 500
class OCRWorkerTiledLinesMixin:
        def _ocr_one_tiled_lines(self, img_path: str, im_orig, file_idx: int, total_files: int):
            try:
                orig_w, orig_h = im_orig.size
                if orig_w < 200 or orig_h < 200:
                    return None
                overlap_x = max(16, int(orig_w * 0.025))
                overlap_y = max(16, int(orig_h * 0.025))
                tiles = []
                if orig_w >= orig_h * 1.15:
                    mid_x = orig_w // 2
                    mid_y = orig_h // 2
                    x_parts = [
                        (0, min(orig_w, mid_x + overlap_x), 0, mid_x),
                        (max(0, mid_x - overlap_x), orig_w, mid_x, orig_w),
                    ]
                    y_parts = [
                        (0, min(orig_h, mid_y + overlap_y), 0, mid_y),
                        (max(0, mid_y - overlap_y), orig_h, mid_y, orig_h),
                    ]
                    for x0, x1, cx0, cx1 in x_parts:
                        for y0, y1, cy0, cy1 in y_parts:
                            tiles.append((x0, y0, x1, y1, cx0, cy0, cx1, cy1))
                else:
                    mid_y = orig_h // 2
                    tiles = [
                        (0, 0, orig_w, min(orig_h, mid_y + overlap_y), 0, 0, orig_w, mid_y),
                        (0, max(0, mid_y - overlap_y), orig_w, orig_h, 0, mid_y, orig_w, orig_h),
                    ]
                rec_model_name = os.path.basename(self.job.recognition_model_path).lower()
                all_views: List[RecordView] = []
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
                for tile_idx, (x0, y0, x1, y1, cx0, cy0, cx1, cy1) in enumerate(tiles):
                    if self.isInterruptionRequested():
                        break
                    crop_orig = im_orig.crop((x0, y0, x1, y1))
                    crop = crop_orig
                    scale_factor = 1.0
                    try:
                        min_dim = min(crop.size)
                        if min_dim < 1200:
                            scale_factor = 2 if min_dim >= 700 else 3
                            crop = crop.resize((crop.size[0] * scale_factor, crop.size[1] * scale_factor), Image.BICUBIC)
                        with torch.no_grad():
                            seg = segment_with_kraken(crop, model=self._seg_model, device=self._device)
                        seg = self._filter_short_baselines_in_seg(seg)
                        expected = self._seg_expected_lines(seg)
                        tile_records = []
                        done = 0
                        with torch.no_grad():
                            for rec in recognize_with_kraken(self._rec_model, crop, seg):
                                tile_records.append(rec)
                                done += 1
                                if expected and expected > 0:
                                    frac_tile = min(1.0, done / max(1, expected))
                                    frac_all = (tile_idx + frac_tile) / max(1, len(tiles))
                                    self._emit_overall_progress(file_idx, total_files, frac_all)
                                if self.isInterruptionRequested():
                                    break
                        if "handwriting" in rec_model_name:
                            tile_sorted = sort_records_handwriting_simple(tile_records, self.job.reading_direction)
                        else:
                            tile_sorted = sort_records_reading_order(tile_records, crop.size[0], crop.size[1], self.job.reading_direction)
                        for rec in tile_sorted:
                            pred = getattr(rec, "prediction", None)
                            if pred is None:
                                continue
                            txt = _clean_ocr_text_for_kraken_display(pred, getattr(self.job, "auto_revision_enabled", False), getattr(self.job, "auto_revision_replacements", None))
                            if _is_effectively_empty_ocr_text(txt) or _is_symbol_only_line(txt) or _is_noise_line(txt):
                                continue
                            bb = record_bbox(rec)
                            bb = _rescale_bbox(bb, scale_factor)
                            if not bb:
                                continue
                            tx0, ty0, tx1, ty1 = bb
                            page_bb = (tx0 + x0, ty0 + y0, tx1 + x0, ty1 + y0)
                            page_bb = expand_segmentation_bbox(page_bb, orig_w, orig_h)
                            if not page_bb:
                                continue
                            pcx = (page_bb[0] + page_bb[2]) / 2.0
                            pcy = (page_bb[1] + page_bb[3]) / 2.0
                            if not (cx0 <= pcx < cx1 and cy0 <= pcy < cy1):
                                continue
                            all_views.append(RecordView(len(all_views), txt, page_bb))
                    finally:
                        try:
                            if crop is not crop_orig:
                                crop.close()
                        except Exception:
                            pass
                        try:
                            crop_orig.close()
                        except Exception:
                            pass
                if not all_views:
                    return None
                filtered: List[RecordView] = []
                seen = set()
                for rv in all_views:
                    key = (rv.text.strip().lower(), tuple(int(v // 5) for v in (rv.bbox or (0, 0, 0, 0))))
                    if key in seen:
                        continue
                    seen.add(key)
                    rv.idx = len(filtered)
                    filtered.append(rv)
                    if len(filtered) >= MAX_KRAKEN_OCR_LINES:
                        break
                lines = [rv.text for rv in filtered]
                return "\n".join(lines).strip(), filtered
            except Exception:
                return None
