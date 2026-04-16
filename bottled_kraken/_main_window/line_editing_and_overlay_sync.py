"""Mixin für MainWindow: line editing and overlay sync."""
from ..shared import *
from ..ui_components import *
from ..workers import *
from ..dialogs import *
from ..image_edit import *

class MainWindowLineEditingAndOverlaySyncMixin:
    def _move_line_to_dialog(self, task: TaskItem, row: int):
        if not task.results:
            return
        _, _, _, recs = task.results
        if not (0 <= row < len(recs)):
            return
        target, ok = QInputDialog.getInt(
            self,
            self._tr("dlg_move_to_title"),
            self._tr("dlg_move_to_label"),
            row + 1,
            1,
            max(1, len(recs)),
            1
        )
        if not ok:
            return
        self._move_line_to(task, row, target - 1)

    def _move_line_to(self, task: TaskItem, from_row: int, to_row: int):
        if not task.results:
            return
        _, _, _, recs = task.results
        if not (0 <= from_row < len(recs)):
            return
        to_row = max(0, min(len(recs) - 1, int(to_row)))
        if from_row == to_row:
            self._sync_ui_after_recs_change(task, keep_row=to_row)
            return
        self._push_undo(task)
        rv = recs.pop(from_row)
        recs.insert(to_row, rv)
        task.edited = True
        self._sync_ui_after_recs_change(task, keep_row=to_row)

    def _delete_line(self, task: TaskItem, row: int):
        if not task.results:
            return
        _, _, _, recs = task.results
        if not (0 <= row < len(recs)):
            return
        self._push_undo(task)
        recs.pop(row)
        task.edited = True
        next_row = min(row, len(recs) - 1) if recs else None
        self._sync_ui_after_recs_change(task, keep_row=next_row)

    def _add_line(self, task: TaskItem, insert_row: int):
        new_text, ok = QInputDialog.getText(self, self._tr("dlg_new_line_title"), self._tr("dlg_new_line_label"))
        if not ok:
            return
        new_text = (new_text or "").strip()
        if not new_text:
            return
        text, kr_records, im, recs = task.results
        insert_row = max(0, min(len(recs), insert_row))
        self._push_undo(task)
        recs.insert(insert_row, RecordView(insert_row, new_text, None))
        task.edited = True
        self._sync_ui_after_recs_change(task, keep_row=insert_row)
        self._pending_new_line_box = False
        self._pending_box_for_row = insert_row
        self.canvas.start_draw_box_mode()

    def on_canvas_select_line(self, idx: int):
        self.on_rect_clicked(idx)

    def _split_text_by_ratio(self, text: str, ratio: float) -> Tuple[str, str]:
        txt = (text or "").strip()
        if not txt:
            return "", ""
        ratio = max(0.05, min(0.95, float(ratio)))
        if " " not in txt:
            cut = max(1, min(len(txt) - 1, int(round(len(txt) * ratio))))
            return txt[:cut].strip(), txt[cut:].strip()
        words = txt.split()
        if len(words) == 1:
            return words[0], ""
        total_chars = len(" ".join(words))
        best_i = 1
        best_diff = 10 ** 9
        current_len = 0
        for i in range(1, len(words)):
            current_len = len(" ".join(words[:i]))
            current_ratio = current_len / max(1, total_chars)
            diff = abs(current_ratio - ratio)
            if diff < best_diff:
                best_diff = diff
                best_i = i
        left = " ".join(words[:best_i]).strip()
        right = " ".join(words[best_i:]).strip()
        return left, right

    def _bbox_intersection(self, a: Optional[BBox], b: Optional[BBox]) -> Tuple[int, int, int]:
        if not a or not b:
            return 0, 0, 0
        ax0, ay0, ax1, ay1 = a
        bx0, by0, bx1, by1 = b
        ix0 = max(ax0, bx0)
        iy0 = max(ay0, by0)
        ix1 = min(ax1, bx1)
        iy1 = min(ay1, by1)
        if ix1 <= ix0 or iy1 <= iy0:
            return 0, 0, 0
        iw = ix1 - ix0
        ih = iy1 - iy0
        return iw * ih, iw, ih

    def _split_text_by_multiple_ratios(self, text: str, ratios: List[float]) -> List[str]:
        txt = (text or "").strip()
        if not txt:
            return [""] * (len(ratios) + 1)
        words = txt.split()
        if len(words) <= 1:
            parts = [""] * (len(ratios) + 1)
            if parts:
                parts[0] = txt
            return parts
        ratios = [max(0.0, min(1.0, float(r))) for r in ratios]
        ratios = sorted(ratios)
        total_words = len(words)
        cut_indices = []
        for r in ratios:
            cut = int(round(total_words * r))
            cut = max(1, min(total_words - 1, cut))
            cut_indices.append(cut)
        # doppelte Schnittstellen bereinigen
        clean_cuts = []
        last = 0
        for cut in cut_indices:
            cut = max(last + 1, cut)
            cut = min(total_words - 1, cut)
            if clean_cuts and cut <= clean_cuts[-1]:
                continue
            clean_cuts.append(cut)
            last = cut
        out = []
        start = 0
        for cut in clean_cuts:
            out.append(" ".join(words[start:cut]).strip())
            start = cut
        out.append(" ".join(words[start:]).strip())
        while len(out) < len(ratios) + 1:
            out.append("")
        return out

    def _reapply_preset_bboxes_to_recs(
            self,
            recs: List[RecordView],
            preset_bboxes: List[Optional[BBox]]
    ) -> List[RecordView]:
        if not preset_bboxes:
            return recs
        # Einfacher Fall: gleiche Anzahl -> nur Boxen ersetzen
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
            # genau ein Ziel -> ganzer Text dorthin
            if len(overlaps) == 1:
                pi = overlaps[0][0]
                target_texts[pi] = (target_texts[pi] + " " + rv.text).strip()
                continue
            # mehrere Zielboxen -> Text proportional aufteilen
            # bevorzugt horizontal (typischer Split links/rechts)
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
        # Falls irgendwo nichts gelandet ist, leeren String behalten
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
        # NEUES VERHALTEN: Eine neue Overlay-Box erzeugt eine NEUE Zeile am Ende.
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
        # Fall A: Neue Zeile am Ende erzeugen (Canvas-Zeichnen)
        if self._pending_new_line_box:
            self._pending_new_line_box = False
            self._pending_box_for_row = None
            # Optional: Text abfragen (optional) – der Nutzer kann ihn später auch in der Liste bearbeiten.
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
        # Fall B: Box für eine bestimmte existierende Zeile zeichnen (Zeilen-Kontextmenü)
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
            im,
            recs
        )
        self._update_task_preset_bboxes(task)
        # Label der Box direkt mitziehen, ohne kompletten Canvas-Neuaufbau
        lab = self.canvas._labels.get(idx)
        if lab and isValid(lab):
            x0, y0, x1, y1 = new_bbox
            lab.setPos(x0, max(0, y0 - 16))

    def _on_overlay_toggled(self, checked):
        self.show_overlay = checked
        self.refresh_preview()

    def on_export_file_started(self, display_name: str, current: int, total: int):
        task = next((i for i in self.queue_items if i.display_name == display_name), None)
        if task:
            task.status = STATUS_EXPORTING
            self._update_queue_row(task.path)

    def export_flow(self, fmt: str):
        checked_tasks = self._checked_queue_tasks()
        selected_tasks = self._selected_queue_tasks()
        # Priorität: Checkmarks vor Auswahl
        target_tasks = checked_tasks if checked_tasks else selected_tasks
        if target_tasks:
            # genau 1 Datei -> normaler "Speichern unter"-Dialog
            if len(target_tasks) == 1:
                it = target_tasks[0]
                if it.status != STATUS_DONE or not it.results:
                    QMessageBox.warning(self, self._tr("warn_title"), self._tr("export_need_done"))
                    return
                self._export_single_interactive(it, fmt)
                return
            # mehrere Dateien -> Batch-Export in Ordner
            items = []
            for it in target_tasks:
                if it.status != STATUS_DONE or not it.results:
                    QMessageBox.warning(self, self._tr("warn_title"), self._tr("export_need_done"))
                    return
                items.append(it)
            self._export_batch(items, fmt)
            return
        if len(self.queue_items) == 0:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_queue_empty"))
            return
        if len(self.queue_items) == 1:
            it = self.queue_items[0]
            if it.status != STATUS_DONE or not it.results:
                QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_select_done"))
                return
            self._export_single_interactive(it, fmt)
            return
        dlg = ExportModeDialog(self._tr, self)
        if dlg.exec() != QDialog.Accepted or dlg.choice is None:
            return
        if dlg.choice == "all":
            items = [it for it in self.queue_items if it.status == STATUS_DONE and it.results]
            if len(items) != len(self.queue_items):
                QMessageBox.warning(self, self._tr("warn_title"), self._tr("export_need_done"))
                return
            self._export_batch(items, fmt)
            return
        sel_dlg = ExportSelectFilesDialog(self._tr, self.queue_items, self)
        if sel_dlg.exec() != QDialog.Accepted:
            return
        paths = sel_dlg.selected_paths
        if not paths:
            QMessageBox.information(self, self._tr("info_title"), self._tr("export_none_selected"))
            return
        items = []
        for p in paths:
            it = next((x for x in self.queue_items if x.path == p), None)
            if not it or it.status != STATUS_DONE or not it.results:
                QMessageBox.warning(self, self._tr("warn_title"), self._tr("export_need_done"))
                return
            items.append(it)
        if len(items) == 1:
            self._export_single_interactive(items[0], fmt)
        else:
            self._export_batch(items, fmt)
