from bottled_kraken.common import _safe_int
from bottled_kraken.common import (
    BBox,
    List,
    Optional,
    QDialog,
    QInputDialog,
    QMessageBox,
    QPointF,
    QRectF,
    READING_MODES,
    RecordView,
    STATUS_DONE,
    TaskItem,
    isValid,
)
from bottled_kraken.ui_components import (
    OverlayBoxDialog,
)
from PySide6.QtWidgets import QButtonGroup, QGridLayout, QWidget
class MainWindowOverlayBoxEditingMixin:
        def _reapply_preset_bboxes_to_recs(
                self,
                recs: List[RecordView],
                preset_bboxes: List[Optional[BBox]]
        ) -> List[RecordView]:
            if not preset_bboxes:
                return recs
            if len(preset_bboxes) == len(recs):
                out = []
                for i, rv in enumerate(recs):
                    out.append(RecordView(i, rv.text, preset_bboxes[i]))
                return out
            target_texts = [""] * len(preset_bboxes)
            for rv in recs:
                if not rv.bbox:
                    continue
                overlaps = []
                for pi, pbb in enumerate(preset_bboxes):
                    area, iw, ih = self._bbox_intersection(rv.bbox, pbb)
                    if area > 0:
                        overlaps.append((pi, area, iw, ih, pbb))
                if not overlaps:
                    continue
                overlaps.sort(key=lambda x: x[0])
                if len(overlaps) == 1:
                    pi = overlaps[0][0]
                    target_texts[pi] = (target_texts[pi] + " " + rv.text).strip()
                    continue
                total_iw = sum(x[2] for x in overlaps)
                total_ih = sum(x[3] for x in overlaps)
                if total_iw >= total_ih:
                    weights = [x[2] for x in overlaps]
                else:
                    weights = [x[3] for x in overlaps]
                weight_sum = max(1, sum(weights))
                cum = 0.0
                ratios = []
                for w in weights[:-1]:
                    cum += w / weight_sum
                    ratios.append(cum)
                parts = self._split_text_by_multiple_ratios(rv.text, ratios)
                for part, ov in zip(parts, overlaps):
                    pi = ov[0]
                    if part.strip():
                        target_texts[pi] = (target_texts[pi] + " " + part.strip()).strip()
            out = []
            for i, pbb in enumerate(preset_bboxes):
                out.append(RecordView(i, target_texts[i].strip(), pbb))
            return out
        def _ensure_overlay_possible(self) -> Optional[TaskItem]:
            task = self._current_task()
            if not task or not task.results or task.status != STATUS_DONE:
                QMessageBox.information(self, self._tr("info_title"), self._tr("overlay_only_after_ocr"))
                return None
            return task
        def on_canvas_add_box_draw(self, scene_pos: QPointF):
            task = self._ensure_overlay_possible()
            if not task:
                return
            _, _, _, recs = task.results
            if recs is None:
                return
            self._pending_box_for_row = None
            self._pending_new_line_box = True
            self.canvas.start_draw_box_mode()
        def on_canvas_edit_box(self, idx: int):
            task = self._ensure_overlay_possible()
            if not task:
                return
            _, _, im, recs = task.results
            if im is None:
                im = self._task_geometry_image(task)
            if not im:
                return
            if not (0 <= idx < len(recs)):
                return
            img_w, img_h = im.size
            dlg = OverlayBoxDialog(self._tr, img_w, img_h, bbox=recs[idx].bbox, parent=self)
            if dlg.exec() != QDialog.Accepted:
                return
            self._push_undo(task)
            recs[idx].bbox = dlg.get_bbox()
            task.edited = True
            self._sync_ui_after_recs_change(task, keep_row=idx)
        def on_canvas_delete_box(self, idx: int):
            task = self._ensure_overlay_possible()
            if not task:
                return
            _, _, _, recs = task.results
            if not (0 <= idx < len(recs)):
                return
            self._push_undo(task)
            recs[idx].bbox = None
            task.edited = True
            self._sync_ui_after_recs_change(task, keep_row=idx)
            self._update_task_preset_bboxes(task)
        def on_canvas_split_box(self, idx: int, split_x: float):
            task = self._ensure_overlay_possible()
            if not task:
                return
            _, _, _, recs = task.results
            if not (0 <= idx < len(recs)):
                return
            rv = recs[idx]
            if not rv.bbox:
                return
            x0, y0, x1, y1 = rv.bbox
            split_x = int(round(split_x))
            split_x = max(x0 + 8, min(x1 - 8, split_x))
            if split_x <= x0 or split_x >= x1:
                return
            ratio = (split_x - x0) / max(1, (x1 - x0))
            left_text, right_text = self._split_text_by_ratio(rv.text, ratio)
            left_box = (x0, y0, split_x, y1)
            right_box = (split_x, y0, x1, y1)
            self._push_undo(task)
            rtl = self.reading_direction in (
                READING_MODES["TB_RL"],
                READING_MODES["BT_RL"],
            )
            if rtl:
                new_items = [
                    RecordView(idx, right_text, right_box),
                    RecordView(idx + 1, left_text, left_box),
                ]
            else:
                new_items = [
                    RecordView(idx, left_text, left_box),
                    RecordView(idx + 1, right_text, right_box),
                ]
            recs[idx:idx + 1] = new_items
            task.edited = True
            self._sync_ui_after_recs_change(task, keep_row=idx)
            self._update_task_preset_bboxes(task)
        def on_box_drawn(self, rect: QRectF):
            task = self._ensure_overlay_possible()
            if not task:
                return
            text, kr_records, im, recs = task.results
            if im is None:
                im = self._task_geometry_image(task)
            x0 = _safe_int(rect.left())
            y0 = _safe_int(rect.top())
            x1 = _safe_int(rect.right())
            y1 = _safe_int(rect.bottom())
            x0, y0, x1, y1 = min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)
            if im:
                img_w, img_h = im.size
                x0, y0 = max(0, min(img_w - 1, x0)), max(0, min(img_h - 1, y0))
                x1, y1 = max(1, min(img_w, x1)), max(1, min(img_h, y1))
                if x1 <= x0:
                    x1 = min(img_w, x0 + 1)
                if y1 <= y0:
                    y1 = min(img_h, y0 + 1)
            if self._pending_new_line_box:
                self._pending_new_line_box = False
                self._pending_box_for_row = None
                new_txt, ok = QInputDialog.getText(self, self._tr("new_line_from_box_title"),
                                                   self._tr("new_line_from_box_label"))
                if not ok:
                    new_txt = ""
                new_txt = (new_txt or "").strip()
                self._push_undo(task)
                recs.append(RecordView(len(recs), new_txt, (x0, y0, x1, y1)))
                task.edited = True
                self._sync_ui_after_recs_change(task, keep_row=len(recs) - 1)
                self._update_task_preset_bboxes(task)
                self.list_lines.setFocus()
                return
            if self._pending_box_for_row is None:
                return
            row = self._pending_box_for_row
            self._pending_box_for_row = None
            if not (0 <= row < len(recs)):
                return
            self._push_undo(task)
            recs[row].bbox = (x0, y0, x1, y1)
            task.edited = True
            self._sync_ui_after_recs_change(task, keep_row=row)
            self._update_task_preset_bboxes(task)
        def on_overlay_rect_changed(self, idx: int, scene_rect: QRectF):
            task = self._ensure_overlay_possible()
            if not task:
                return
            text, kr_records, im, recs = task.results
            if im is None:
                im = self._task_geometry_image(task)
            if not (0 <= idx < len(recs)):
                return
            new_bbox = self._scene_rect_to_bbox(scene_rect, im)
            if not new_bbox:
                return
            old_bbox = recs[idx].bbox
            if old_bbox == new_bbox:
                return
            self._push_undo(task)
            recs[idx].bbox = new_bbox
            task.edited = True
            task.results = (
                "\n".join(r.text for r in recs).strip(),
                kr_records,
                None,
                recs
            )
            self._update_task_preset_bboxes(task)
            lab = self.canvas._labels.get(idx)
            if lab and isValid(lab):
                x0, y0, x1, y1 = new_bbox
                lab.setPos(x0, max(0, y0 - 16))
