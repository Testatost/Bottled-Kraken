"""Worker-Klassen für Bottled Kraken."""
from ...shared import *

MAX_KRAKEN_OCR_LINES = 500

class OCRWorkerPresetBoxesMixin:
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
                crop_size = crop.size
                crop_records = []
                seg = None
                try:
                    with torch.no_grad():
                        seg = segment_with_kraken(crop, model=self._seg_model, device=self._device)
                        seg = self._filter_short_baselines_in_seg(seg)
                        for rec in recognize_with_kraken(self._rec_model, crop, seg):
                            crop_records.append(rec)
                except Exception:
                    crop_records = []
                finally:
                    try:
                        crop.close()
                    except Exception:
                        pass
                    seg = None
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
                            crop_size[0],
                            crop_size[1],
                            self.job.reading_direction
                        )
                    parts = []
                    for rec in crop_records:
                        pred = getattr(rec, "prediction", None)
                        txt = _clean_ocr_text_for_kraken_display(pred, getattr(self.job, "auto_revision_enabled", False), getattr(self.job, "auto_revision_replacements", None))
                        if txt and not _is_symbol_only_line(txt) and not _is_noise_line(txt):
                            parts.append(txt)
                    final_text = " ".join(parts).strip()
                else:
                    final_text = ""
                record_views.append(RecordView(len(record_views), final_text, bb))
                self._emit_overall_progress(file_idx, total_files, (box_idx + 1) / total_boxes)
            text = "\n".join(rv.text for rv in record_views).strip()
            return text, record_views
