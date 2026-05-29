from bottled_kraken.common import (
    BBox,
    List,
    Optional,
    QInputDialog,
    RecordView,
    TaskItem,
    Tuple,
)
from PySide6.QtWidgets import QButtonGroup, QGridLayout, QWidget
class MainWindowLineActionsMixin:
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
