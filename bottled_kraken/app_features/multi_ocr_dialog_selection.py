from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
try:
    PtrMultiOcrDialog.__init__ = _ptr_multi_dialog_init_checklist
    PtrMultiOcrDialog.selected_recognition_paths = _ptr_dialog_selected_recognition_paths
    PtrMultiOcrDialog.selected_image_variant_keys = _ptr_dialog_selected_image_variant_keys
    PtrMultiOcrDialog.use_segmentation = _ptr_dialog_use_segmentation
    PtrMultiOcrDialog.image_variants_enabled = _ptr_dialog_image_variants_enabled
    PtrMultiOcrDialog.image_variant_count = _ptr_dialog_image_variant_count
except Exception:
    pass
def _bk_final_followup_label(obj, key: str, fallback: str, *, trim_run_suffix: bool = False) -> str:
    text = fallback
    try:
        text = _ptr_ui_tr(obj, key)
    except Exception:
        text = fallback
    if trim_run_suffix:
        for suffix in (" ausführen", " exécuter", " lancer"):
            if text.endswith(suffix):
                text = text[: -len(suffix)]
        if text.casefold().startswith("run full "):
            text = text[4:]
    return str(text or fallback).strip() or fallback
def _ptr_multi_followup_init_final_v17(self, parent=None):
    QDialog.__init__(self, parent)
    self.setWindowTitle(_bk_final_followup_label(self, "ptr_multi_followup_open_title", "Multi-OCR"))
    self.resize(760, 220)
    self.choice = self.CHOICE_CANCEL
    root = QVBoxLayout(self)
    lbl = QLabel(_bk_final_followup_label(self, "ptr_ai_multi_done_text", "Multi-OCR"))
    lbl.setWordWrap(True)
    root.addWidget(lbl)
    hint = QLabel(_bk_final_followup_label(self, "ptr_multi_followup_openrouter_hint", "Remote AI post-processing only"))
    hint.setWordWrap(True)
    root.addWidget(hint)
    row1 = QHBoxLayout()
    row2 = QHBoxLayout()
    self.local_btn = QPushButton(_bk_final_followup_label(self, "ptr_multi_followup_btn_ocr_merge", "OCR Merge"))
    self.ai_pg_btn = QPushButton(_bk_final_followup_label(self, "ptr_multi_followup_btn_postgres", "PostgreSQL"))
    self.ai_neo_btn = QPushButton(_bk_final_followup_label(self, "ptr_multi_followup_btn_neo4j", "Neo4j"))
    self.sqlite_btn = QPushButton(_bk_final_followup_label(self, "ptr_multi_followup_btn_sqlite", "SQLite"))
    self.ai_both_btn = QPushButton(_bk_final_followup_label(self, "ptr_multi_followup_btn_pipeline", "Full Pipeline", trim_run_suffix=True))
    self.ai_graph_btn = QPushButton(_bk_final_followup_label(self, "ptr_multi_followup_btn_graph", "Graph view"))
    self.ai_btn = QPushButton(_bk_final_followup_label(self, "ptr_multi_followup_btn_openrouter", "OpenRouter"))
    self.cancel_btn = QPushButton(_bk_final_followup_label(self, "btn_cancel", "Cancel"))
    for btn in (self.local_btn, self.ai_pg_btn, self.ai_neo_btn, self.sqlite_btn):
        row1.addWidget(btn, 1)
    for btn in (self.ai_both_btn, self.ai_graph_btn, self.ai_btn, self.cancel_btn):
        row2.addWidget(btn, 1)
    root.addLayout(row1)
    root.addLayout(row2)
    self.local_btn.clicked.connect(lambda: self._choose(self.CHOICE_LOCAL))
    self.ai_pg_btn.clicked.connect(lambda: self._choose(self.CHOICE_AI_POSTGRES))
    self.ai_neo_btn.clicked.connect(lambda: self._choose(self.CHOICE_AI_NEO4J))
    self.sqlite_btn.clicked.connect(lambda: self._choose(self.CHOICE_SQLITE))
    self.ai_both_btn.clicked.connect(lambda: self._choose(self.CHOICE_AI_BOTH))
    self.ai_graph_btn.clicked.connect(lambda: self._choose(self.CHOICE_AI_GRAPH))
    self.ai_btn.clicked.connect(lambda: self._choose(self.CHOICE_AI))
    self.cancel_btn.clicked.connect(self.reject)
def _ptr_open_multi_followup_for_path_final_v17(self, path: str):
    variants = self._ptr_multi_ocr_variants_by_path.get(path, [])
    if not variants:
        QMessageBox.information(self, _ptr_ui_tr(self, "ptr_multi_ocr_title"), _ptr_ui_tr(self, "ptr_multi_no_variants"))
        return
    self._ptr_last_multi_followup_path = path
    choice = PtrMultiOCRFollowupDialog.get_choice(self)
    if choice == PtrMultiOCRFollowupDialog.CHOICE_CANCEL:
        return
    if choice == PtrMultiOCRFollowupDialog.CHOICE_LOCAL:
        self._ptr_apply_local_merge_to_task(path)
        return
    if choice == PtrMultiOCRFollowupDialog.CHOICE_AI:
        self._ptr_open_ai_tools(path, auto_mode=None)
        return
    if choice == PtrMultiOCRFollowupDialog.CHOICE_AI_POSTGRES:
        self._ptr_open_ai_tools(path, auto_mode="postgres")
        return
    if choice == PtrMultiOCRFollowupDialog.CHOICE_AI_NEO4J:
        self._ptr_open_ai_tools(path, auto_mode="neo4j")
        return
    if choice == PtrMultiOCRFollowupDialog.CHOICE_SQLITE:
        self._ptr_open_ai_tools(path, auto_mode=None)
        return
    if choice == PtrMultiOCRFollowupDialog.CHOICE_AI_BOTH:
        self._ptr_open_ai_tools(path, auto_mode="pipeline")
        return
    if choice == PtrMultiOCRFollowupDialog.CHOICE_AI_GRAPH:
        self._ptr_open_ai_tools(path, auto_mode=None)
        try:
            dlg = getattr(self, "_ptr_last_ai_dialog", None)
            if dlg is not None and hasattr(dlg, "_bk_generate_remote_canonical_and_show_graph"):
                QTimer.singleShot(0, dlg._bk_generate_remote_canonical_and_show_graph)
        except Exception:
            pass
        return
try:
    PtrMultiOCRFollowupDialog.CHOICE_SQLITE = getattr(PtrMultiOCRFollowupDialog, "CHOICE_SQLITE", "sqlite")
    PtrMultiOCRFollowupDialog.CHOICE_AI_GRAPH = getattr(PtrMultiOCRFollowupDialog, "CHOICE_AI_GRAPH", "ai_graph")
    PtrMultiOCRFollowupDialog.__init__ = _ptr_multi_followup_init_final_v17
    MainWindow._ptr_open_multi_followup_for_path = _ptr_open_multi_followup_for_path_final_v17
except Exception:
    pass
try:
    _BK_FINAL_PREV_SELECTED_LINE_ROWS_V17 = MainWindow._selected_line_rows
except Exception:
    _BK_FINAL_PREV_SELECTED_LINE_ROWS_V17 = None
def _bk_final_selected_line_rows_v17(self):
    override = getattr(self, "_bk_lm_strict_selected_rows_override", None)
    if override is not None:
        return list(override)
    if callable(_BK_FINAL_PREV_SELECTED_LINE_ROWS_V17):
        return _BK_FINAL_PREV_SELECTED_LINE_ROWS_V17(self)
    try:
        return self.list_lines.selected_line_rows()
    except Exception:
        return []
def _bk_final_task_and_row_count_v17(self):
    try:
        task = _bk_lm_get_current_done_task(self)
    except Exception:
        try:
            task = self._current_task()
        except Exception:
            task = None
    if not task or not getattr(task, "results", None):
        return None, 0
    try:
        _text, _kr_records, _im, recs = task.results
        return task, len(recs or [])
    except Exception:
        return task, 0
def _bk_final_clean_rows_v17(rows, row_count: int):
    out = []
    seen = set()
    for row in rows or []:
        try:
            row = int(row)
        except Exception:
            continue
        if 0 <= row < row_count and row not in seen:
            seen.add(row)
            out.append(row)
    return out
def _bk_final_current_row_v17(self, row_count: int):
    try:
        row = self.list_lines.currentRow()
    except Exception:
        row = -1
    rows = _bk_final_clean_rows_v17([row], row_count)
    return rows[0] if rows else -1
def _bk_final_selected_rows_v17(self, row_count: int):
    try:
        rows = self._selected_line_rows()
    except Exception:
        rows = []
    return _bk_final_clean_rows_v17(rows, row_count)
def _bk_final_set_strict_result_rows_v17(self, task, rows):
    try:
        self._bk_lm_strict_result_rows_context = {
            "path": getattr(task, "path", None),
            "rows": list(rows or []),
        }
    except Exception:
        pass
def _bk_final_clear_strict_result_rows_v17(self):
    try:
        self._bk_lm_strict_result_rows_context = None
    except Exception:
        pass
def _bk_final_run_exact_rows_v17(self, rows, *, require_selected: bool = False):
    task, row_count = _bk_final_task_and_row_count_v17(self)
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return True
    clean_rows = _bk_final_clean_rows_v17(rows, row_count)
    if require_selected and not clean_rows:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_select_multiple_lines_first"))
        return True
    if not clean_rows:
        return False
    _bk_final_set_strict_result_rows_v17(self, task, clean_rows)
    if len(clean_rows) == 1:
        self.run_ai_revision_for_single_line(clean_rows[0])
        return True
    old = getattr(self, "_bk_lm_strict_selected_rows_override", None)
    self._bk_lm_strict_selected_rows_override = list(clean_rows)
    try:
        self.run_ai_revision_for_selected_lines()
    finally:
        if old is None:
            try:
                delattr(self, "_bk_lm_strict_selected_rows_override")
            except Exception:
                pass
        else:
            self._bk_lm_strict_selected_rows_override = old
    return True
def _bk_final_lm_run_current_line_v17(self):
    task, row_count = _bk_final_task_and_row_count_v17(self)
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return
    row = _bk_final_current_row_v17(self, row_count)
    if row < 0:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_select_line_first"))
        return
    _bk_final_run_exact_rows_v17(self, [row])
def _bk_final_lm_run_selected_lines_v17(self):
    task, row_count = _bk_final_task_and_row_count_v17(self)
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return
    rows = _bk_final_selected_rows_v17(self, row_count)
    _bk_final_run_exact_rows_v17(self, rows, require_selected=True)
def _bk_final_lm_queue_has_focus_v17(self):
    try:
        return _bk_lm_queue_has_keyboard_focus(self)
    except Exception:
        try:
            return _bk_lm_widget_contains(getattr(self, "queue_table", None), QApplication.focusWidget())
        except Exception:
            return False
def _bk_final_run_ai_revision_v17(self):
    try:
        if _bk_lm_any_job_running(self):
            return
    except Exception:
        pass
    force_queue_context = bool(getattr(self, "_bk_lm_force_queue_revision_context", False))
    if force_queue_context:
        _bk_final_clear_strict_result_rows_v17(self)
        if _bk_lm_run_queue_batch(self, _BK_LM_BATCH_MODE_ALL_LINES, allow_selected=True):
            return
    task, row_count = _bk_final_task_and_row_count_v17(self)
    if task and not force_queue_context:
        rows = _bk_final_selected_rows_v17(self, row_count)
        if rows:
            _bk_final_run_exact_rows_v17(self, rows)
            return
        row = _bk_final_current_row_v17(self, row_count)
        if row >= 0:
            _bk_final_run_exact_rows_v17(self, [row])
            return
    checked_targets = _bk_lm_checked_queue_tasks_with_results(self)
    if checked_targets:
        _bk_final_clear_strict_result_rows_v17(self)
        _bk_lm_run_queue_batch(self, _BK_LM_BATCH_MODE_ALL_LINES, targets=checked_targets)
        return
    if _bk_final_lm_queue_has_focus_v17(self):
        _bk_final_clear_strict_result_rows_v17(self)
        if _bk_lm_run_queue_batch(self, _BK_LM_BATCH_MODE_ALL_LINES, allow_selected=True):
            return
    if task:
        _bk_final_clear_strict_result_rows_v17(self)
        _bk_lm_run_queue_batch(self, _BK_LM_BATCH_MODE_ALL_LINES, targets=[task])
        return
    QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
try:
    _BK_FINAL_PREV_ON_AI_REVISION_DONE_V17 = MainWindow.on_ai_revision_done
except Exception:
    _BK_FINAL_PREV_ON_AI_REVISION_DONE_V17 = None
try:
    _BK_FINAL_PREV_ON_AI_SINGLE_LINE_REVISION_DONE_V17 = MainWindow.on_ai_single_line_revision_done
except Exception:
    _BK_FINAL_PREV_ON_AI_SINGLE_LINE_REVISION_DONE_V17 = None
try:
    _BK_FINAL_PREV_ON_AI_SELECTED_LINES_REVISION_DONE_V17 = MainWindow.on_ai_selected_lines_revision_done
except Exception:
    _BK_FINAL_PREV_ON_AI_SELECTED_LINES_REVISION_DONE_V17 = None
def _bk_final_on_ai_revision_done_v17(self, path: str, revised_lines: list):
    ctx = getattr(self, "_bk_lm_strict_result_rows_context", None) or {}
    rows = list(ctx.get("rows", []) or [])
    ctx_path = ctx.get("path")
    if not rows or ctx_path != path:
        if callable(_BK_FINAL_PREV_ON_AI_REVISION_DONE_V17):
            return _BK_FINAL_PREV_ON_AI_REVISION_DONE_V17(self, path, revised_lines)
        return None
    _bk_final_clear_strict_result_rows_v17(self)
    task = next((i for i in getattr(self, "queue_items", []) if getattr(i, "path", None) == path), None)
    if not task or not getattr(task, "results", None):
        if callable(_BK_FINAL_PREV_ON_AI_REVISION_DONE_V17):
            return _BK_FINAL_PREV_ON_AI_REVISION_DONE_V17(self, path, revised_lines)
        return None
    try:
        text, kr_records, im, recs = task.results
    except Exception:
        if callable(_BK_FINAL_PREV_ON_AI_REVISION_DONE_V17):
            return _BK_FINAL_PREV_ON_AI_REVISION_DONE_V17(self, path, revised_lines)
        return None
    rows = _bk_final_clean_rows_v17(rows, len(recs or []))
    if not rows:
        if callable(_BK_FINAL_PREV_ON_AI_REVISION_DONE_V17):
            return _BK_FINAL_PREV_ON_AI_REVISION_DONE_V17(self, path, revised_lines)
        return None
    revised_lines = [str(x).strip() for x in (revised_lines or [])]
    self._push_undo(task)
    new_recs = [
        RecordView(i, recs[i].text, recs[i].bbox)
        for i in range(len(recs))
    ]
    full_page_result = len(revised_lines) >= len(new_recs)
    for local_idx, row in enumerate(rows):
        if not (0 <= row < len(new_recs)):
            continue
        if full_page_result:
            new_text = revised_lines[row] if row < len(revised_lines) else ""
        else:
            new_text = revised_lines[local_idx] if local_idx < len(revised_lines) else ""
        new_text = str(new_text).strip()
        if new_text:
            new_recs[row].text = new_text
    task.results = (
        "\n".join(rv.text for rv in new_recs).strip(),
        kr_records,
        im,
        new_recs,
    )
    task.status = STATUS_DONE
    task.edited = True
    try:
        cur = self._current_task()
    except Exception:
        cur = None
    if cur and getattr(cur, "path", None) == path:
        self._sync_ui_after_recs_change(task, keep_row=rows[0])
        try:
            self.list_lines.blockSignals(True)
            self.list_lines.clearSelection()
            for row in rows:
                if 0 <= row < self.list_lines.count():
                    it = self.list_lines.row_item(row)
                    if it:
                        it.setSelected(True)
            self.list_lines.setCurrentRow(rows[0])
            self.list_lines.blockSignals(False)
            self.canvas.select_indices(rows, center=False)
        except Exception:
            try:
                self.list_lines.blockSignals(False)
            except Exception:
                pass
    self._refresh_queue_row_for_path(path)
    self.act_ai_revise.setEnabled(True)
    try:
        if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
            self.btn_ai_revise_bottom.setEnabled(True)
    except Exception:
        pass
    if getattr(self, "ai_progress_dialog", None):
        self.ai_progress_dialog.close()
        self.ai_progress_dialog = None
    try:
        self.status_bar.showMessage(self._tr("msg_ai_selected_lines_done", len(rows)))
    except Exception:
        pass
def _bk_final_on_ai_single_line_revision_done_v17(self, path: str, revised_lines: list):
    _bk_final_clear_strict_result_rows_v17(self)
    if callable(_BK_FINAL_PREV_ON_AI_SINGLE_LINE_REVISION_DONE_V17):
        return _BK_FINAL_PREV_ON_AI_SINGLE_LINE_REVISION_DONE_V17(self, path, revised_lines)
    return None
def _bk_final_on_ai_selected_lines_revision_done_v17(self, path: str, revised_lines: list):
    _bk_final_clear_strict_result_rows_v17(self)
    if callable(_BK_FINAL_PREV_ON_AI_SELECTED_LINES_REVISION_DONE_V17):
        return _BK_FINAL_PREV_ON_AI_SELECTED_LINES_REVISION_DONE_V17(self, path, revised_lines)
    return None
def _bk_final_connect_action_v17(action, callback):
    if action is None:
        return
    try:
        action.triggered.disconnect()
    except Exception:
        pass
    action.triggered.connect(lambda checked=False: callback())
def _bk_final_rewire_lm_dropdown_v17(self):
    _bk_final_connect_action_v17(getattr(self, "act_ai_menu_current_line", None), lambda: _bk_final_lm_run_current_line_v17(self))
    _bk_final_connect_action_v17(getattr(self, "act_ai_menu_selected_lines", None), lambda: _bk_final_lm_run_selected_lines_v17(self))
    _bk_final_connect_action_v17(getattr(self, "act_ai_menu_all_lines", None), lambda: _bk_lm_run_all_lines_current_task(self))
    _bk_final_connect_action_v17(getattr(self, "act_ai_menu_lm_ocr", None), lambda: _bk_lm_run_overlay_lm_ocr_current_task(self))
    _bk_final_connect_action_v17(getattr(self, "act_ai_menu_lm_ocr_boxes", None), lambda: _bk_lm_run_overlay_lm_ocr_boxes_current_task(self))
    _bk_final_connect_action_v17(getattr(self, "act_ai_menu_postgres", None), lambda: _bk_lm_generate_local_json(self, "postgres"))
    _bk_final_connect_action_v17(getattr(self, "act_ai_menu_neo4j", None), lambda: _bk_lm_generate_local_json(self, "neo4j"))
    try:
        _bk_lm_update_dropdown_state(self)
    except Exception:
        pass
try:
    def _bk_final_mainwindow_init_v17(self, *args, **kwargs):
        try:
            _bk_final_rewire_lm_dropdown_v17(self)
        except Exception:
            pass
    from bottled_kraken.common.chain_consolidation import register_init_delta, register_retranslate_delta
    register_init_delta(_bk_final_mainwindow_init_v17)
except Exception:
    pass
try:
    def _bk_final_retranslate_ui_v17(self, *args, **kwargs):
        try:
            _bk_final_rewire_lm_dropdown_v17(self)
        except Exception:
            pass
    register_retranslate_delta(_bk_final_retranslate_ui_v17)
except Exception:
    pass
try:
    MainWindow._selected_line_rows = _bk_final_selected_line_rows_v17
    MainWindow.run_ai_revision = _bk_final_run_ai_revision_v17
    MainWindow.on_ai_revision_done = _bk_final_on_ai_revision_done_v17
    MainWindow.on_ai_single_line_revision_done = _bk_final_on_ai_single_line_revision_done_v17
    MainWindow.on_ai_selected_lines_revision_done = _bk_final_on_ai_selected_lines_revision_done_v17
    MainWindow._bk_lm_run_current_line = _bk_final_lm_run_current_line_v17
    MainWindow._bk_lm_run_selected_lines = _bk_final_lm_run_selected_lines_v17
    _bk_lm_run_current_line = _bk_final_lm_run_current_line_v17
    _bk_lm_run_selected_lines = _bk_final_lm_run_selected_lines_v17
except Exception:
    pass
__all__ = [name for name in globals() if not name.startswith("__")]
from bottled_kraken.export_layout import install_export_layout as _install_bottled_kraken_export_layout
_install_bottled_kraken_export_layout(MainWindow)
del _install_bottled_kraken_export_layout
__all__ = [
    '_bk_final_clean_rows_v17',
    '_bk_final_clear_strict_result_rows_v17',
    '_bk_final_connect_action_v17',
    '_bk_final_current_row_v17',
    '_bk_final_followup_label',
    '_bk_final_lm_queue_has_focus_v17',
    '_bk_final_lm_run_current_line_v17',
    '_bk_final_lm_run_selected_lines_v17',
    '_bk_final_on_ai_revision_done_v17',
    '_bk_final_on_ai_selected_lines_revision_done_v17',
    '_bk_final_on_ai_single_line_revision_done_v17',
    '_bk_final_rewire_lm_dropdown_v17',
    '_bk_final_run_ai_revision_v17',
    '_bk_final_run_exact_rows_v17',
    '_bk_final_selected_line_rows_v17',
    '_bk_final_selected_rows_v17',
    '_bk_final_set_strict_result_rows_v17',
    '_bk_final_task_and_row_count_v17',
    '_ptr_multi_followup_init_final_v17',
    '_ptr_open_multi_followup_for_path_final_v17',
]
register_globals('bk', globals(), __all__)
