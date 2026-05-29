from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
from bottled_kraken._main_window.menu_and_queue.menu_behavior import BKStayOpenMenu
"""Batch-Automatisierung für lokale LM-Überarbeitung über den Wartebereich.
Diese Datei überschreibt die LM-Menüpfade spät im bk_features-Ladeprozess.
Batchfähig sind nur:
- "Alle Zeilen überarbeiten"
- "LM OCR"
- Rechtsklick im Wartebereich -> "LM-Überarbeitung" als "Alle Zeilen überarbeiten"
"Aktuelle Zeile überarbeiten" und "Markierte Zeilen überarbeiten" bleiben
bewusst reine Funktionen für die aktuell geladene Vorschauseite.
"""
def _bk_lm_run_queue_batch(self, mode: str, row_indices: Optional[List[int]] = None, *, targets: Optional[List[TaskItem]] = None, allow_selected: bool = False, allow_all_if_empty: bool = False):
    _bk_lm_persist_visible_queue_state(self)
    if _bk_lm_any_job_running(self):
        return False
    if targets is None:
        targets, _source = _bk_lm_queue_targets(self, allow_selected=allow_selected, allow_all_if_empty=allow_all_if_empty)
    if mode == _BK_LM_BATCH_MODE_LM_OCR:
        targets = _bk_lm_unique_tasks([t for t in (targets or []) if getattr(t, "path", None)])
    elif mode == _BK_LM_BATCH_MODE_LM_OCR_BOXES:
        targets = _bk_lm_unique_tasks([t for t in (targets or []) if _bk_lm_task_has_overlay_boxes(t)])
    else:
        targets = _bk_lm_unique_tasks([t for t in (targets or []) if _bk_lm_task_has_results(t)])
    if not targets:
        return False
    model_id = self._resolve_ai_model_id()
    if not model_id:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_ai_model"))
        return True
    script_mode = AI_SCRIPT_PRINT
    if mode not in (_BK_LM_BATCH_MODE_LM_OCR, _BK_LM_BATCH_MODE_LM_OCR_BOXES):
        script_mode = self._choose_ai_script_mode()
        if not script_mode:
            return True
    self.act_ai_revise.setEnabled(False)
    if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
        self.btn_ai_revise_bottom.setEnabled(False)
    title = self._tr("dlg_ai_ocr_boxes_title") if mode == _BK_LM_BATCH_MODE_LM_OCR_BOXES else (self._tr("dlg_ai_ocr_title") if mode == _BK_LM_BATCH_MODE_LM_OCR else self._tr("act_ai_revise"))
    self._bk_lm_queue_batch_mode = mode
    self._bk_lm_queue_batch_dialog = ProgressStatusDialog(title, self._tr, self)
    self._bk_lm_queue_batch_dialog.set_status(self._tr("lm_busy_prepare_status"))
    self._bk_lm_queue_batch_dialog.cancel_requested.connect(lambda: _bk_lm_cancel_queue_batch(self))
    self._bk_lm_queue_batch_dialog.show()
    if mode == _BK_LM_BATCH_MODE_LM_OCR_BOXES:
        max_tokens = self._lm_token_limit("lm_ocr_boxes") if hasattr(self, "_lm_token_limit") else 4500
    elif mode == _BK_LM_BATCH_MODE_LM_OCR:
        max_tokens = self._lm_token_limit("lm_ocr") if hasattr(self, "_lm_token_limit") else 4500
    else:
        max_tokens = self._lm_token_limit("all_lines") if hasattr(self, "_lm_token_limit") else self.ai_max_tokens
    self._bk_lm_queue_batch_worker = BKQueueLMBatchWorker(
        items=targets,
        mode=mode,
        row_indices=row_indices or [],
        lm_model=model_id,
        endpoint=self.ai_endpoint,
        enable_thinking=self.ai_enable_thinking,
        script_mode=script_mode,
        temperature=self.ai_temperature,
        top_p=self.ai_top_p,
        top_k=self.ai_top_k,
        presence_penalty=self.ai_presence_penalty,
        repetition_penalty=self.ai_repetition_penalty,
        min_p=self.ai_min_p,
        max_tokens=max_tokens,
        tr_func=self._tr,
        parent=self,
    )
    w = self._bk_lm_queue_batch_worker
    w.file_started.connect(lambda path, current, total, mode: _bk_lm_on_queue_batch_file_started(self, path, current, total, mode))
    w.file_finished.connect(lambda path, mode, rows, lines, current, total: _bk_lm_on_queue_batch_file_done(self, path, mode, rows, lines, current, total))
    w.file_failed.connect(lambda path, msg, current, total: _bk_lm_on_queue_batch_file_failed(self, path, msg, current, total))
    w.file_skipped.connect(lambda path, reason, current, total: _bk_lm_on_queue_batch_file_skipped(self, path, reason, current, total))
    w.status_changed.connect(self._log)
    w.status_changed.connect(self._bk_lm_queue_batch_dialog.set_status)
    w.progress_changed.connect(self._bk_lm_queue_batch_dialog.set_progress)
    w.finished_batch.connect(lambda: _bk_lm_on_queue_batch_finished(self))
    self._log(f"LM-Batch gestartet: {len(targets)} Datei(en), Modus={mode}")
    w.start()
    return True
def _bk_lm_run_current_line(self):
    task = _bk_lm_get_current_done_task(self)
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return
    row = self.list_lines.currentRow()
    if row < 0:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_select_line_first"))
        return
    self.run_ai_revision_for_single_line(row)
def _bk_lm_run_selected_lines(self):
    task = _bk_lm_get_current_done_task(self)
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return
    rows = self._selected_line_rows()
    if not rows:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_select_multiple_lines_first"))
        return
    self.run_ai_revision_for_selected_lines()
def _bk_lm_run_all_lines_current_task(self):
    checked_targets = _bk_lm_checked_queue_tasks_with_results(self)
    if checked_targets:
        _bk_lm_run_queue_batch(self, _BK_LM_BATCH_MODE_ALL_LINES, targets=checked_targets)
        return
    task = _bk_lm_get_current_done_task(self)
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return
    _bk_lm_run_queue_batch(self, _BK_LM_BATCH_MODE_ALL_LINES, targets=[task])
def _bk_lm_run_overlay_lm_ocr_current_task(self):
    checked_targets = _bk_lm_checked_queue_tasks_any(self)
    if checked_targets:
        _bk_lm_run_queue_batch(self, _BK_LM_BATCH_MODE_LM_OCR, targets=checked_targets)
        return
    task = _bk_lm_get_current_task_any(self)
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return
    _bk_lm_run_queue_batch(self, _BK_LM_BATCH_MODE_LM_OCR, targets=[task])
def _bk_lm_run_overlay_lm_ocr_boxes_current_task(self):
    checked_targets = [t for t in _bk_lm_checked_queue_tasks_with_results(self) if _bk_lm_task_has_overlay_boxes(t)]
    if checked_targets:
        _bk_lm_run_queue_batch(self, _BK_LM_BATCH_MODE_LM_OCR_BOXES, targets=checked_targets)
        return
    task = _bk_lm_get_current_done_task(self)
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return
    if not _bk_lm_task_has_overlay_boxes(task):
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_overlay_boxes_for_lm_ocr_boxes"))
        return
    _bk_lm_run_queue_batch(self, _BK_LM_BATCH_MODE_LM_OCR_BOXES, targets=[task])
def _bk_lm_run_revision_from_queue_context(self):
    if _bk_lm_run_queue_batch(self, _BK_LM_BATCH_MODE_ALL_LINES, allow_selected=True):
        return
    task = _bk_lm_get_current_done_task(self)
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return
    _bk_lm_run_queue_batch(self, _BK_LM_BATCH_MODE_ALL_LINES, targets=[task])
def _bk_lm_run_ai_revision_patched(self):
    if _bk_lm_run_queue_batch(self, _BK_LM_BATCH_MODE_ALL_LINES, allow_selected=True):
        return
    task = _bk_lm_get_current_done_task(self)
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return
    _bk_lm_run_queue_batch(self, _BK_LM_BATCH_MODE_ALL_LINES, targets=[task])
def _bk_lm_run_ai_revision_for_selected_patched(self):
    targets, _source = _bk_lm_queue_targets(self, allow_selected=True, allow_all_if_empty=False)
    if not targets:
        targets = [t for t in getattr(self, "queue_items", []) if _bk_lm_task_has_results(t)]
    if not targets:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return
    _bk_lm_run_queue_batch(self, _BK_LM_BATCH_MODE_ALL_LINES, targets=targets)
def _bk_lm_run_ai_revision_for_all_patched(self):
    targets = [t for t in getattr(self, "queue_items", []) if _bk_lm_task_has_results(t)]
    if not targets:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return
    _bk_lm_run_queue_batch(self, _BK_LM_BATCH_MODE_ALL_LINES, targets=targets)
def _bk_lm_update_dropdown_state(self):
    if not hasattr(self, "act_ai_menu_current_line"):
        return
    busy = _bk_lm_any_job_running(self)
    checked_targets = _bk_lm_checked_queue_tasks_with_results(self)
    checked_any_targets = _bk_lm_checked_queue_tasks_any(self)
    has_checked = bool(checked_targets)
    has_checked_any = bool(checked_any_targets)
    task = _bk_lm_get_current_done_task(self)
    current_any_task = _bk_lm_get_current_task_any(self)
    has_current_task = bool(task)
    has_current_any_task = bool(current_any_task)
    row = self.list_lines.currentRow() if hasattr(self, "list_lines") else -1
    selected_rows = self._selected_line_rows() if hasattr(self, "_selected_line_rows") else []
    self.act_ai_menu_current_line.setEnabled(has_current_task and row >= 0 and not busy)
    self.act_ai_menu_selected_lines.setEnabled(has_current_task and len(selected_rows) > 0 and not busy)
    has_all_lines_target = has_checked or has_current_task
    has_lm_ocr_target = has_checked_any or has_current_any_task
    checked_box_targets = [t for t in checked_targets if _bk_lm_task_has_overlay_boxes(t)]
    has_lm_ocr_boxes_target = bool(checked_box_targets) or bool(task and _bk_lm_task_has_overlay_boxes(task))
    self.act_ai_menu_all_lines.setEnabled(has_all_lines_target and not busy)
    if hasattr(self, "act_ai_menu_lm_ocr"):
        self.act_ai_menu_lm_ocr.setEnabled(has_lm_ocr_target and not busy)
    if hasattr(self, "act_ai_menu_lm_ocr_boxes"):
        self.act_ai_menu_lm_ocr_boxes.setEnabled(has_lm_ocr_boxes_target and not busy)
    if hasattr(self, "act_ai_menu_postgres"):
        self.act_ai_menu_postgres.setEnabled(has_current_task and not busy)
    if hasattr(self, "act_ai_menu_neo4j"):
        self.act_ai_menu_neo4j.setEnabled(has_current_task and not busy)
def _bk_lm_install_dropdown_menu(self):
    if getattr(self, "_bk_lm_dropdown_installed", False):
        _bk_lm_update_dropdown_state(self)
        return
    self._bk_lm_dropdown_installed = True
    self.act_ai_menu_current_line = QAction(self._tr("lm_menu_current_line"), self)
    self.act_ai_menu_selected_lines = QAction(self._tr("lm_menu_selected_lines"), self)
    self.act_ai_menu_all_lines = QAction(self._tr("lm_menu_all_lines"), self)
    self.act_ai_menu_lm_ocr = QAction(self._tr("lm_menu_lm_ocr"), self)
    self.act_ai_menu_lm_ocr_boxes = QAction(self._tr("lm_menu_lm_ocr_boxes"), self)
    self.act_ai_menu_postgres = QAction(self._tr("lm_menu_generate_postgres"), self)
    self.act_ai_menu_neo4j = QAction(self._tr("lm_menu_generate_neo4j"), self)
    self.act_ai_menu_current_line.triggered.connect(lambda: _bk_lm_run_current_line(self))
    self.act_ai_menu_selected_lines.triggered.connect(lambda: _bk_lm_run_selected_lines(self))
    self.act_ai_menu_all_lines.triggered.connect(lambda: _bk_lm_run_all_lines_current_task(self))
    self.act_ai_menu_lm_ocr.triggered.connect(lambda: _bk_lm_run_overlay_lm_ocr_current_task(self))
    self.act_ai_menu_lm_ocr_boxes.triggered.connect(lambda: _bk_lm_run_overlay_lm_ocr_boxes_current_task(self))
    self.act_ai_menu_postgres.triggered.connect(lambda: _bk_lm_generate_local_json(self, "postgres"))
    self.act_ai_menu_neo4j.triggered.connect(lambda: _bk_lm_generate_local_json(self, "neo4j"))
    self.btn_ai_revise_menu = BKStayOpenMenu(self)
    self.btn_ai_revise_menu.aboutToShow.connect(lambda: _bk_lm_update_dropdown_state(self))
    self.btn_ai_revise_menu.addAction(self.act_ai_menu_current_line)
    self.btn_ai_revise_menu.addAction(self.act_ai_menu_selected_lines)
    self.btn_ai_revise_menu.addAction(self.act_ai_menu_all_lines)
    self.btn_ai_revise_menu.addSeparator()
    self.btn_ai_revise_menu.addAction(self.act_ai_menu_lm_ocr)
    self.btn_ai_revise_menu.addAction(self.act_ai_menu_lm_ocr_boxes)
    self.btn_ai_revise_menu.addSeparator()
    self.btn_ai_revise_menu.addAction(self.act_ai_menu_postgres)
    self.btn_ai_revise_menu.addAction(self.act_ai_menu_neo4j)
    try:
        self.btn_ai_revise_bottom.clicked.disconnect()
    except Exception:
        pass
    self.btn_ai_revise_bottom.setMenu(self.btn_ai_revise_menu)
    self.btn_ai_revise_bottom.setPopupMode(QToolButton.InstantPopup)
    self.btn_ai_revise_bottom.setToolTip(self._tr("btn_ai_revise_menu_tip"))
    _bk_lm_update_dropdown_state(self)
def _bk_lm_retranslate_dropdown(self):
    if not getattr(self, "_bk_lm_dropdown_installed", False):
        return
    self.act_ai_menu_current_line.setText(self._tr("lm_menu_current_line"))
    self.act_ai_menu_selected_lines.setText(self._tr("lm_menu_selected_lines"))
    self.act_ai_menu_all_lines.setText(self._tr("lm_menu_all_lines"))
    if hasattr(self, "act_ai_menu_lm_ocr"):
        self.act_ai_menu_lm_ocr.setText(self._tr("lm_menu_lm_ocr"))
    if hasattr(self, "act_ai_menu_lm_ocr_boxes"):
        self.act_ai_menu_lm_ocr_boxes.setText(self._tr("lm_menu_lm_ocr_boxes"))
    self.act_ai_menu_postgres.setText(self._tr("lm_menu_generate_postgres"))
    self.act_ai_menu_neo4j.setText(self._tr("lm_menu_generate_neo4j"))
    if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
        self.btn_ai_revise_bottom.setToolTip(self._tr("btn_ai_revise_menu_tip"))
    _bk_lm_update_dropdown_state(self)
__all__ = [
    '_bk_lm_install_dropdown_menu',
    '_bk_lm_retranslate_dropdown',
    '_bk_lm_run_ai_revision_for_all_patched',
    '_bk_lm_run_ai_revision_for_selected_patched',
    '_bk_lm_run_ai_revision_patched',
    '_bk_lm_run_all_lines_current_task',
    '_bk_lm_run_current_line',
    '_bk_lm_run_overlay_lm_ocr_boxes_current_task',
    '_bk_lm_run_overlay_lm_ocr_current_task',
    '_bk_lm_run_queue_batch',
    '_bk_lm_run_revision_from_queue_context',
    '_bk_lm_run_selected_lines',
    '_bk_lm_update_dropdown_state',
]
register_globals('bk', globals(), __all__)
