from bottled_kraken.common import (
    BBox,
    List,
    Optional,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QRadioButton,
    QSlider,
    QVBoxLayout,
    Qt,
    RecordView,
)
from PySide6.QtWidgets import QButtonGroup, QGridLayout, QWidget
class MainWindowOverlayDisplayMixin:
        def _overlay_visible_rows_for_mode(self, recs: List[RecordView]) -> List[int]:
            if not getattr(self, "show_overlay", True):
                return []
            mode = getattr(self, "overlay_display_mode", "all")
            max_idx = len(recs) - 1
            if mode == "all":
                return [int(rv.idx) for rv in recs if rv.bbox]
            if mode == "current":
                row = self.list_lines.currentRow() if hasattr(self, "list_lines") else -1
                if 0 <= row <= max_idx:
                    return [int(recs[row].idx)]
                return []
            if mode == "selected":
                rows = self._selected_line_rows() if hasattr(self, "_selected_line_rows") else []
                clean = []
                for row in rows:
                    if 0 <= row <= max_idx:
                        clean.append(int(recs[row].idx))
                return sorted(set(clean))
            return [int(rv.idx) for rv in recs if rv.bbox]
        def _refresh_overlay_display(self, recs: Optional[List[RecordView]] = None):
            if recs is None:
                task = self._current_task() if hasattr(self, "_current_task") else None
                if not task or not task.results:
                    return
                _, _, _, recs = task.results
            if not hasattr(self, "canvas"):
                return
            rows = self._overlay_visible_rows_for_mode(recs)
            self.canvas.draw_overlays(recs, visible_indices=rows)
        def _set_overlay_display_mode(self, mode: str):
            mode = str(mode or "all").lower()
            if mode not in {"current", "selected", "all"}:
                mode = "all"
            self.overlay_display_mode = mode
            self.show_overlay = True
            if hasattr(self, "overlay_display_actions"):
                act = self.overlay_display_actions.get(mode)
                if act is not None and not act.isChecked():
                    act.setChecked(True)
            try:
                self.settings.setValue("ui/overlay_display_mode", mode)
            except Exception:
                pass
            self._refresh_overlay_display()
            rows = self._selected_line_rows() if hasattr(self, "_selected_line_rows") else []
            if rows:
                self.canvas.select_indices(rows, center=False)
            else:
                row = self.list_lines.currentRow() if hasattr(self, "list_lines") else -1
                if row >= 0:
                    self.canvas.select_idx(row, center=False)
                else:
                    self.canvas.select_indices([], center=False)
        def _on_overlay_toggled(self, checked):
            self.show_overlay = bool(checked)
            self._refresh_overlay_display()
        def _overlay_box_resize_rows_for_scope(self, recs: List[RecordView], scope: str) -> List[int]:
            scope = str(scope or "current").lower()
            max_row = len(recs) - 1
            if scope == "all":
                return [i for i, rv in enumerate(recs) if rv.bbox]
            if scope == "selected":
                rows = self._selected_line_rows() if hasattr(self, "_selected_line_rows") else []
                clean = [int(r) for r in rows if 0 <= int(r) <= max_row and recs[int(r)].bbox]
                if clean:
                    return sorted(set(clean))
            row = self.list_lines.currentRow() if hasattr(self, "list_lines") else -1
            if 0 <= row <= max_row and recs[row].bbox:
                return [row]
            return []
        def _scale_overlay_bbox(
                self,
                bbox: BBox,
                sx: float,
                sy: float,
                img_w: int,
                img_h: int,
                side: str = "center",
        ) -> BBox:
            x0, y0, x1, y1 = [int(v) for v in bbox]
            side = str(side or "center").lower()
            old_w = max(2.0, float(x1 - x0))
            old_h = max(2.0, float(y1 - y0))
            new_w = max(2.0, old_w * max(0.10, float(sx)))
            new_h = max(2.0, old_h * max(0.10, float(sy)))
            if side == "left":
                nx1 = x1
                nx0 = int(round(nx1 - new_w))
                cy = (y0 + y1) / 2.0
                ny0 = int(round(cy - new_h / 2.0))
                ny1 = int(round(cy + new_h / 2.0))
            elif side == "right":
                nx0 = x0
                nx1 = int(round(nx0 + new_w))
                cy = (y0 + y1) / 2.0
                ny0 = int(round(cy - new_h / 2.0))
                ny1 = int(round(cy + new_h / 2.0))
            elif side == "top":
                ny1 = y1
                ny0 = int(round(ny1 - new_h))
                cx = (x0 + x1) / 2.0
                nx0 = int(round(cx - new_w / 2.0))
                nx1 = int(round(cx + new_w / 2.0))
            elif side == "bottom":
                ny0 = y0
                ny1 = int(round(ny0 + new_h))
                cx = (x0 + x1) / 2.0
                nx0 = int(round(cx - new_w / 2.0))
                nx1 = int(round(cx + new_w / 2.0))
            else:
                cx = (x0 + x1) / 2.0
                cy = (y0 + y1) / 2.0
                nx0 = int(round(cx - new_w / 2.0))
                nx1 = int(round(cx + new_w / 2.0))
                ny0 = int(round(cy - new_h / 2.0))
                ny1 = int(round(cy + new_h / 2.0))
            if nx0 < 0:
                nx1 -= nx0
                nx0 = 0
            if ny0 < 0:
                ny1 -= ny0
                ny0 = 0
            if nx1 > img_w:
                shift = nx1 - img_w
                nx0 = max(0, nx0 - shift)
                nx1 = img_w
            if ny1 > img_h:
                shift = ny1 - img_h
                ny0 = max(0, ny0 - shift)
                ny1 = img_h
            nx1 = max(nx0 + 2, min(nx1, img_w))
            ny1 = max(ny0 + 2, min(ny1, img_h))
            return nx0, ny0, nx1, ny1
        def resize_overlay_boxes_dialog(self):
            task = self._ensure_overlay_possible()
            if not task or not task.results:
                return
            text, kr_records, im, recs = task.results
            if im is None:
                im = self._task_geometry_image(task)
            if im is None:
                return
            dlg = QDialog(self)
            dlg.setWindowTitle(self._tr("overlay_resize_title"))
            layout = QVBoxLayout(dlg)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(10)
            scope_label = QLabel(self._tr("overlay_resize_scope"), dlg)
            layout.addWidget(scope_label)
            scope_box = QWidget(dlg)
            scope_layout = QVBoxLayout(scope_box)
            scope_layout.setContentsMargins(0, 0, 0, 0)
            scope_layout.setSpacing(4)
            scope_group = QButtonGroup(scope_box)
            scope_group.setExclusive(True)
            rb_current = QRadioButton(self._tr("overlay_resize_scope_current"), scope_box)
            rb_selected = QRadioButton(self._tr("overlay_resize_scope_selected"), scope_box)
            rb_all = QRadioButton(self._tr("overlay_resize_scope_all"), scope_box)
            for rb in (rb_current, rb_selected, rb_all):
                scope_group.addButton(rb)
                scope_layout.addWidget(rb)
            rb_current.setChecked(True)
            layout.addWidget(scope_box)
            side_label = QLabel(self._tr("overlay_resize_side"), dlg)
            layout.addWidget(side_label)
            side_box = QWidget(dlg)
            side_grid = QGridLayout(side_box)
            side_grid.setContentsMargins(0, 0, 0, 0)
            side_grid.setSpacing(4)
            side_group = QButtonGroup(side_box)
            side_group.setExclusive(True)
            side_rows = [
                ("center", self._tr("overlay_resize_side_center")),
                ("left", self._tr("overlay_resize_side_left")),
                ("right", self._tr("overlay_resize_side_right")),
                ("top", self._tr("overlay_resize_side_top")),
                ("bottom", self._tr("overlay_resize_side_bottom")),
            ]
            side_buttons = {}
            for idx, (key, label) in enumerate(side_rows):
                rb = QRadioButton(label, side_box)
                rb.setProperty("resize_side", key)
                side_group.addButton(rb)
                side_buttons[key] = rb
                side_grid.addWidget(rb, idx // 2, idx % 2)
            side_buttons["center"].setChecked(True)
            layout.addWidget(side_box)
            def make_slider(label_key: str):
                row = QHBoxLayout()
                lbl = QLabel(self._tr(label_key, 0), dlg)
                lbl.setMinimumWidth(220)
                sl = QSlider(Qt.Horizontal, dlg)
                sl.setRange(-50, 100)
                sl.setValue(0)
                sl.setTickInterval(10)
                sl.setMinimumWidth(340)
                row.addWidget(lbl)
                row.addWidget(sl, 1)
                layout.addLayout(row)
                return lbl, sl
            lbl_w, sl_w = make_slider("overlay_resize_width")
            lbl_h, sl_h = make_slider("overlay_resize_height")
            hint = QLabel(self._tr("overlay_resize_hint"), dlg)
            hint.setWordWrap(True)
            layout.addWidget(hint)
            original_bboxes = {
                idx: tuple(rv.bbox) if rv.bbox else None
                for idx, rv in enumerate(recs)
            }
            img_w, img_h = im.size
            preview_guard = {"active": False}
            def selected_side() -> str:
                checked = side_group.checkedButton()
                return str(checked.property("resize_side") if checked else "center")
            def current_scope() -> str:
                if rb_all.isChecked():
                    return "all"
                if rb_selected.isChecked():
                    return "selected"
                return "current"
            def rows_for_preview():
                return self._overlay_box_resize_rows_for_scope(recs, current_scope())
            def restore_original_bboxes():
                for idx, bb in original_bboxes.items():
                    recs[idx].bbox = tuple(bb) if bb else None
            def update_labels():
                lbl_w.setText(self._tr("overlay_resize_width", int(sl_w.value())))
                lbl_h.setText(self._tr("overlay_resize_height", int(sl_h.value())))
            def refresh_overlay_only():
                try:
                    task.results = ("\n".join(r.text for r in recs).strip(), kr_records, None, recs)
                except Exception:
                    pass
                if hasattr(self, "_refresh_overlay_display"):
                    self._refresh_overlay_display(recs)
                elif hasattr(self, "canvas"):
                    try:
                        self.canvas.draw_overlays(recs)
                    except Exception:
                        pass
            def apply_preview():
                if preview_guard["active"]:
                    return
                preview_guard["active"] = True
                try:
                    update_labels()
                    restore_original_bboxes()
                    rows = rows_for_preview()
                    sx = 1.0 + (int(sl_w.value()) / 100.0)
                    sy = 1.0 + (int(sl_h.value()) / 100.0)
                    side = selected_side()
                    if rows and (abs(sx - 1.0) >= 1e-6 or abs(sy - 1.0) >= 1e-6):
                        for row in rows:
                            bb = original_bboxes.get(row)
                            if bb:
                                recs[row].bbox = self._scale_overlay_bbox(bb, sx, sy, img_w, img_h, side)
                    refresh_overlay_only()
                finally:
                    preview_guard["active"] = False
            sl_w.valueChanged.connect(lambda _v: apply_preview())
            sl_h.valueChanged.connect(lambda _v: apply_preview())
            for rb in (rb_current, rb_selected, rb_all):
                rb.toggled.connect(lambda _checked: apply_preview())
            for rb in side_buttons.values():
                rb.toggled.connect(lambda _checked: apply_preview())
            update_labels()
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dlg)
            buttons.button(QDialogButtonBox.Ok).setText(self._tr("dlg_box_apply"))
            buttons.button(QDialogButtonBox.Cancel).setText(self._tr("btn_cancel"))
            buttons.accepted.connect(dlg.accept)
            buttons.rejected.connect(dlg.reject)
            layout.addWidget(buttons)
            apply_preview()
            accepted = dlg.exec() == QDialog.Accepted
            rows = rows_for_preview()
            sx = 1.0 + (int(sl_w.value()) / 100.0)
            sy = 1.0 + (int(sl_h.value()) / 100.0)
            side = selected_side()
            restore_original_bboxes()
            refresh_overlay_only()
            if not accepted:
                return
            if not rows:
                QMessageBox.information(self, self._tr("info_title"), self._tr("overlay_resize_no_boxes"))
                return
            if abs(sx - 1.0) < 1e-6 and abs(sy - 1.0) < 1e-6:
                return
            self._push_undo(task)
            for row in rows:
                bb = original_bboxes.get(row)
                if bb:
                    recs[row].bbox = self._scale_overlay_bbox(bb, sx, sy, img_w, img_h, side)
            task.edited = True
            task.results = ("\n".join(r.text for r in recs).strip(), kr_records, None, recs)
            self._update_task_preset_bboxes(task)
            keep_row = rows[0] if rows else None
            self._sync_ui_after_recs_change(task, keep_row=keep_row)
            self.status_bar.showMessage(self._tr("overlay_resize_done", len(rows)))
