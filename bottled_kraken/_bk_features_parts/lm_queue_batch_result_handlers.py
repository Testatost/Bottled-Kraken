"""Batch-Automatisierung für lokale LM-Überarbeitung über den Wartebereich.

Diese Datei überschreibt die LM-Menüpfade spät im bk_features-Ladeprozess.
Batchfähig sind nur:
- "Alle Zeilen überarbeiten"
- "LM OCR"
- Rechtsklick im Wartebereich -> "LM-Überarbeitung" als "Alle Zeilen überarbeiten"

"Aktuelle Zeile überarbeiten" und "Markierte Zeilen überarbeiten" bleiben
bewusst reine Funktionen für die aktuell geladene Vorschauseite.
"""

def _bk_lm_apply_queue_batch_result(self, path: str, mode: str, target_rows: List[int], revised_lines: List[str]):
    task = next((i for i in getattr(self, "queue_items", []) if i.path == path), None)
    if not task:
        return
    revised_lines = [_clean_ocr_text(str(x).strip()) for x in (revised_lines or [])]

    if mode == _BK_LM_BATCH_MODE_LM_OCR_BOXES:
        # LM Seiten OCR + Boxen: Anzahl und Geometrie der vorhandenen Overlay-Boxen
        # bleiben strikt erhalten. Es wird genau ein Text pro vorhandener Box ersetzt;
        # es werden keine neuen Zeilen angefügt und keine alten Zeilen gelöscht.
        if not task.results:
            return
        text, kr_records, im, recs = task.results
        recs = list(recs or [])
        if not recs:
            return
        try:
            self._push_undo(task)
        except Exception:
            pass
        old_boxes = list(getattr(task, "preset_bboxes", []) or [])
        if len(old_boxes) != len(recs):
            old_boxes = [tuple(rv.bbox) if getattr(rv, "bbox", None) else None for rv in recs]
        strict_lines = [_clean_ocr_text(x) for x in (revised_lines or [])]
        if len(strict_lines) < len(recs):
            strict_lines.extend([""] * (len(recs) - len(strict_lines)))
        elif len(strict_lines) > len(recs):
            strict_lines = strict_lines[:len(recs)]
        new_recs = []
        for i, rv in enumerate(recs):
            bb = old_boxes[i] if i < len(old_boxes) else getattr(rv, "bbox", None)
            new_text = strict_lines[i] if i < len(strict_lines) and _clean_ocr_text(strict_lines[i]) else getattr(rv, "text", "")
            new_recs.append(RecordView(i, _clean_ocr_text(new_text), tuple(bb) if bb else None))
        task.results = (
            "\n".join(rv.text for rv in new_recs).strip(),
            kr_records,
            im,
            new_recs,
        )
        task.preset_bboxes = [tuple(rv.bbox) if getattr(rv, "bbox", None) else None for rv in new_recs]
        task.lm_locked_bboxes = []
        task.edited = True
        task.status = STATUS_DONE
        cur = self._current_task()
        if cur and cur.path == path:
            self._sync_ui_after_recs_change(task, keep_row=0 if new_recs else None)
        else:
            self._update_queue_row(path)
        self._update_queue_row(path)
        return

    if mode == _BK_LM_BATCH_MODE_LM_OCR:
        # Fullpage-LM-OCR ersetzt die bisherige Zeilenstruktur vollständig.
        # Overlay-Boxen werden bewusst verworfen; der Nutzer kann sie danach
        # bei Bedarf pro Zeile per Rechtsklick neu zeichnen.
        if task.results:
            _old_text, _old_kr_records, old_im, _old_recs = task.results
            im = old_im
        else:
            im = _load_image_gray(task.path)
        try:
            self._push_undo(task)
        except Exception:
            pass
        new_recs = [
            RecordView(i, line, None)
            for i, line in enumerate(revised_lines)
            if str(line or "").strip()
        ]
        task.results = (
            "\n".join(rv.text for rv in new_recs).strip(),
            [],
            im,
            new_recs,
        )
        task.preset_bboxes = [None for _ in new_recs]
        task.lm_locked_bboxes = []
        task.edited = True
        task.status = STATUS_DONE
        cur = self._current_task()
        if cur and cur.path == path:
            self._sync_ui_after_recs_change(task, keep_row=0 if new_recs else None)
        else:
            self._update_queue_row(path)
        self._update_queue_row(path)
        return

    if not task.results:
        return
    text, kr_records, im, recs = task.results
    recs = list(recs or [])
    target_rows = [int(r) for r in (target_rows or []) if 0 <= int(r) < len(recs)]
    if mode == _BK_LM_BATCH_MODE_ALL_LINES:
        target_rows = list(range(len(recs)))
        if len(revised_lines) < len(recs):
            revised_lines.extend([recs[i].text for i in range(len(revised_lines), len(recs))])
        elif len(revised_lines) > len(recs):
            revised_lines = revised_lines[:len(recs)]
    else:
        if len(revised_lines) < len(target_rows):
            pad = [recs[target_rows[i]].text for i in range(len(revised_lines), len(target_rows))]
            if mode == _BK_LM_BATCH_MODE_LM_OCR:
                pad = [""] * (len(target_rows) - len(revised_lines))
            revised_lines.extend(pad)
        elif len(revised_lines) > len(target_rows):
            revised_lines = revised_lines[:len(target_rows)]
    try:
        self._push_undo(task)
    except Exception:
        pass
    new_recs = [RecordView(i, recs[i].text, recs[i].bbox) for i in range(len(recs))]
    for local_idx, row in enumerate(target_rows):
        if not (0 <= row < len(new_recs)):
            continue
        new_text = revised_lines[local_idx] if local_idx < len(revised_lines) else ""
        if mode in (_BK_LM_BATCH_MODE_CURRENT_LINE, _BK_LM_BATCH_MODE_SELECTED_LINES):
            if new_text:
                new_recs[row].text = new_text
        else:
            # All-Lines und LM OCR ersetzen den jeweiligen Zielbereich vollständig.
            new_recs[row].text = new_text
    task.results = (
        "\n".join(rv.text for rv in new_recs).strip(),
        kr_records,
        im,
        new_recs,
    )
    task.edited = True
    task.status = STATUS_DONE
    try:
        self._update_task_preset_bboxes(task)
    except Exception:
        pass
    cur = self._current_task()
    if cur and cur.path == path:
        keep_row = target_rows[0] if target_rows else self.list_lines.currentRow()
        if keep_row is None or keep_row < 0:
            keep_row = 0 if new_recs else None
        self._sync_ui_after_recs_change(task, keep_row=keep_row)
        if mode == _BK_LM_BATCH_MODE_SELECTED_LINES and target_rows:
            try:
                self.list_lines.blockSignals(True)
                self.list_lines.clearSelection()
                for row in target_rows:
                    item = self.list_lines.row_item(row)
                    if item:
                        item.setSelected(True)
                self.list_lines.setCurrentRow(target_rows[0])
                self.list_lines.blockSignals(False)
            except Exception:
                try:
                    self.list_lines.blockSignals(False)
                except Exception:
                    pass
    self._update_queue_row(path)

def _bk_lm_on_queue_batch_file_started(self, path: str, current: int, total: int, mode: str):
    task = next((i for i in getattr(self, "queue_items", []) if i.path == path), None)
    if task:
        if task.results:
            try:
                task.lm_locked_bboxes = [tuple(rv.bbox) if rv.bbox else None for rv in task.results[3]]
            except Exception:
                task.lm_locked_bboxes = []
        task.status = STATUS_AI_PROCESSING
        self._update_queue_row(path)
    self.status_bar.showMessage(f"LM-Batch {current}/{total}: {os.path.basename(path)}")

def _bk_lm_on_queue_batch_file_done(self, path: str, mode: str, target_rows, revised_lines, current: int, total: int):
    _bk_lm_apply_queue_batch_result(self, path, mode, list(target_rows or []), list(revised_lines or []))
    self._log(f"LM-Batch {current}/{total} abgeschlossen: {os.path.basename(path)}")

def _bk_lm_on_queue_batch_file_failed(self, path: str, msg: str, current: int, total: int):
    task = next((i for i in getattr(self, "queue_items", []) if i.path == path), None)
    if task:
        task.status = STATUS_ERROR
        self._update_queue_row(path)
    self._log(f"LM-Batch {current}/{total} Fehler: {os.path.basename(path)} -> {msg}")

def _bk_lm_on_queue_batch_file_skipped(self, path: str, reason: str, current: int, total: int):
    self._log(f"LM-Batch {current}/{total} übersprungen: {os.path.basename(path)} -> {reason}")

def _bk_lm_on_queue_batch_finished(self):
    finished_mode = getattr(self, "_bk_lm_queue_batch_mode", "")
    self.act_ai_revise.setEnabled(True)
    if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
        self.btn_ai_revise_bottom.setEnabled(True)
    dlg = getattr(self, "_bk_lm_queue_batch_dialog", None)
    if dlg:
        try:
            dlg.close()
        except Exception:
            pass
    self._bk_lm_queue_batch_dialog = None
    worker = getattr(self, "_bk_lm_queue_batch_worker", None)
    if worker is not None:
        try:
            worker.deleteLater()
        except Exception:
            pass
    self._bk_lm_queue_batch_worker = None
    self._bk_lm_queue_batch_mode = ""
    self.status_bar.showMessage("LM-Batch abgeschlossen.")
    if finished_mode == _BK_LM_BATCH_MODE_LM_OCR:
        try:
            QMessageBox.information(
                self,
                self._tr("dlg_ai_ocr_title"),
                self._tr("info_lm_ocr_manual_boxes_hint"),
            )
        except Exception:
            pass
    elif finished_mode == _BK_LM_BATCH_MODE_LM_OCR_BOXES:
        try:
            QMessageBox.information(
                self,
                self._tr("dlg_ai_ocr_boxes_title"),
                self._tr("info_lm_ocr_boxes_done_hint"),
            )
        except Exception:
            pass

def _bk_lm_cancel_queue_batch(self):
    worker = getattr(self, "_bk_lm_queue_batch_worker", None)
    if worker is not None and worker.isRunning():
        worker.cancel()
