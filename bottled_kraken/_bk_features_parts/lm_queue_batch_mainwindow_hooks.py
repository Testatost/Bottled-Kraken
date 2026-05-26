"""Batch-Automatisierung für lokale LM-Überarbeitung über den Wartebereich.

Diese Datei überschreibt die LM-Menüpfade spät im bk_features-Ladeprozess.
Batchfähig sind nur:
- "Alle Zeilen überarbeiten"
- "LM OCR"
- Rechtsklick im Wartebereich -> "LM-Überarbeitung" als "Alle Zeilen überarbeiten"

"Aktuelle Zeile überarbeiten" und "Markierte Zeilen überarbeiten" bleiben
bewusst reine Funktionen für die aktuell geladene Vorschauseite.
"""

_BK_PREV_QUEUE_CONTEXT_MENU_V16 = MainWindow.queue_context_menu

def _bk_lm_queue_context_menu_patched(self, pos):
    # Rechtsklick soll ohne vorheriges Linksklicken auf die angeklickte Datei wirken,
    # solange keine Checkbox-Auswahl aktiv ist.
    try:
        if not _bk_lm_checked_queue_tasks_with_results(self):
            item = self.queue_table.itemAt(pos)
            if item is not None:
                row = item.row()
                selected_rows = [idx.row() for idx in self.queue_table.selectionModel().selectedRows()]
                if row not in selected_rows:
                    self.queue_table.selectRow(row)
    except Exception:
        pass
    return _BK_PREV_QUEUE_CONTEXT_MENU_V16(self, pos)

_BK_PREV_PREVIEW_IMAGE_V16 = MainWindow.preview_image

_BK_PREV_LOAD_RESULTS_V16 = MainWindow.load_results

_BK_PREV_REFRESH_PREVIEW_V16 = MainWindow.refresh_preview

_BK_PREV_PERSIST_LOADED_PREVIEW_BBOXES_V16 = MainWindow._persist_loaded_preview_bboxes

_BK_PREV_CANCEL_AI_BATCH_REVISION_V16 = MainWindow._cancel_ai_batch_revision

def _bk_lm_persist_loaded_preview_bboxes_patched(self):
    task = self._loaded_preview_task()
    if task and task.results:
        self._persist_live_canvas_bboxes(task)

def _bk_lm_preview_image_patched(self, path: str, persist_current: bool = False):
    try:
        if persist_current:
            self._persist_loaded_preview_bboxes()
        im = Image.open(path)
        self.canvas.load_pil_image(im)
        self._loaded_preview_path = path
        self.list_lines.clear()
        item = next((i for i in self.queue_items if i.path == path), None)
        if item and item.results:
            self.load_results(path, persist_current=False)
        else:
            self.canvas.set_overlay_enabled(False)
    except Exception as e:
        QMessageBox.warning(self, self._tr("err_title"), self._tr("err_load", str(e)))

def _bk_lm_load_results_patched(self, path: str, persist_current: bool = False):
    if persist_current:
        self._persist_loaded_preview_bboxes()
    item = next((i for i in self.queue_items if i.path == path), None)
    if not item or not item.results:
        return
    text, kr_records, im, recs = item.results
    preview_im = _load_image_color(path)
    self.canvas.load_pil_image(preview_im)
    self._loaded_preview_path = path
    # Overlay-Boxen auch bei STATUS_ERROR anzeigen, wenn echte OCR-/Import-Ergebnisse vorhanden sind.
    self.canvas.set_overlay_enabled(True)
    self._refresh_overlay_display(recs)
    self._populate_lines_list(recs)
    rows = self._selected_line_rows()
    if rows:
        self.canvas.select_indices(rows, center=False)

def _bk_lm_refresh_preview_patched(self):
    if self.queue_table.currentRow() >= 0:
        path = self.queue_table.item(self.queue_table.currentRow(), QUEUE_COL_FILE).data(Qt.UserRole)
        item = next((i for i in self.queue_items if i.path == path), None)
        if item and item.results:
            self.load_results(path, persist_current=True)
        else:
            self.preview_image(path, persist_current=True)

def _bk_lm_cancel_ai_batch_revision_patched(self):
    worker = getattr(self, "_bk_lm_queue_batch_worker", None)
    if worker is not None and worker.isRunning():
        worker.cancel()
        return
    try:
        return _BK_PREV_CANCEL_AI_BATCH_REVISION_V16(self)
    except Exception:
        pass

MainWindow._bk_lm_install_dropdown_menu = _bk_lm_install_dropdown_menu

MainWindow._bk_lm_retranslate_dropdown = _bk_lm_retranslate_dropdown

MainWindow._bk_lm_run_all_lines_current_task = _bk_lm_run_all_lines_current_task

MainWindow._bk_lm_run_overlay_lm_ocr_current_task = _bk_lm_run_overlay_lm_ocr_current_task

MainWindow._bk_lm_run_overlay_lm_ocr_boxes_current_task = _bk_lm_run_overlay_lm_ocr_boxes_current_task

MainWindow.run_ai_revision = _bk_lm_run_ai_revision_patched

MainWindow.run_ai_revision_for_selected = _bk_lm_run_ai_revision_for_selected_patched

MainWindow.run_ai_revision_for_all = _bk_lm_run_ai_revision_for_all_patched

MainWindow.queue_context_menu = _bk_lm_queue_context_menu_patched

MainWindow.preview_image = _bk_lm_preview_image_patched

MainWindow.load_results = _bk_lm_load_results_patched

MainWindow.refresh_preview = _bk_lm_refresh_preview_patched

MainWindow._persist_loaded_preview_bboxes = _bk_lm_persist_loaded_preview_bboxes_patched

MainWindow._cancel_ai_batch_revision = _bk_lm_cancel_ai_batch_revision_patched
