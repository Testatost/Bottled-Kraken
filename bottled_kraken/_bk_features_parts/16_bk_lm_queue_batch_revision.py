"""Batch-Automatisierung für lokale LM-Überarbeitung über den Wartebereich.

Diese Datei überschreibt die LM-Menüpfade spät im bk_features-Ladeprozess.
Batchfähig sind nur:
- "Alle Zeilen überarbeiten"
- "LM OCR"
- Rechtsklick im Wartebereich -> "LM-Überarbeitung" als "Alle Zeilen überarbeiten"

"Aktuelle Zeile überarbeiten" und "Markierte Zeilen überarbeiten" bleiben
bewusst reine Funktionen für die aktuell geladene Vorschauseite.
"""

_BK_LM_BATCH_MODE_CURRENT_LINE = "current_line"
_BK_LM_BATCH_MODE_SELECTED_LINES = "selected_lines"
_BK_LM_BATCH_MODE_ALL_LINES = "all_lines"
_BK_LM_BATCH_MODE_LM_OCR = "lm_ocr"


def _bk_lm_any_job_running(self) -> bool:
    return bool(
        (getattr(self, "ai_worker", None) and self.ai_worker.isRunning())
        or (getattr(self, "ai_batch_worker", None) and self.ai_batch_worker.isRunning())
        or (getattr(self, "_bk_lm_queue_batch_worker", None) and self._bk_lm_queue_batch_worker.isRunning())
        or (getattr(self, "_bk_local_json_worker", None) and self._bk_local_json_worker.isRunning())
    )


def _bk_lm_task_has_results(task) -> bool:
    if task is None or not getattr(task, "results", None):
        return False
    try:
        _text, _kr_records, _im, recs = task.results
        return bool(recs)
    except Exception:
        return False


def _bk_lm_task_has_overlay_boxes(task) -> bool:
    if not _bk_lm_task_has_results(task):
        return False
    try:
        _text, _kr_records, _im, recs = task.results
        boxes = list(getattr(task, "preset_bboxes", []) or [])
        if len(boxes) != len(recs):
            boxes = [rv.bbox for rv in recs]
        return any(bool(bb) for bb in boxes)
    except Exception:
        return False


def _bk_lm_get_current_done_task(self):
    # Für LM-Nachbearbeitung zählt hier nicht mehr ausschließlich STATUS_DONE.
    # Wenn OCR-Zeilen im Task vorhanden sind, darf auch ein Fehlerstatus weiterverarbeitet werden.
    task = self._current_task()
    try:
        self._persist_live_canvas_bboxes(task)
    except Exception:
        pass
    if not _bk_lm_task_has_results(task):
        return None
    return task


def _bk_lm_unique_tasks(tasks):
    out = []
    seen = set()
    for task in tasks or []:
        path = getattr(task, "path", None)
        if not path or path in seen:
            continue
        seen.add(path)
        out.append(task)
    return out


def _bk_lm_checked_queue_tasks_with_results(self):
    try:
        tasks = self._checked_queue_tasks()
    except Exception:
        tasks = []
    return _bk_lm_unique_tasks([t for t in tasks if _bk_lm_task_has_results(t)])


def _bk_lm_selected_queue_tasks_with_results(self):
    try:
        tasks = self._selected_queue_tasks()
    except Exception:
        tasks = []
    return _bk_lm_unique_tasks([t for t in tasks if _bk_lm_task_has_results(t)])


def _bk_lm_checked_queue_tasks_any(self):
    try:
        tasks = self._checked_queue_tasks()
    except Exception:
        tasks = []
    return _bk_lm_unique_tasks([t for t in tasks if getattr(t, "path", None)])


def _bk_lm_selected_queue_tasks_any(self):
    try:
        tasks = self._selected_queue_tasks()
    except Exception:
        tasks = []
    return _bk_lm_unique_tasks([t for t in tasks if getattr(t, "path", None)])


def _bk_lm_get_current_task_any(self):
    task = None
    try:
        task = self._current_task()
    except Exception:
        task = None
    try:
        self._persist_live_canvas_bboxes(task)
    except Exception:
        pass
    return task if getattr(task, "path", None) else None


def _bk_lm_queue_targets(self, *, allow_selected: bool = False, allow_all_if_empty: bool = False):
    checked = _bk_lm_checked_queue_tasks_with_results(self)
    if checked:
        return checked, "checked"
    if allow_selected:
        selected = _bk_lm_selected_queue_tasks_with_results(self)
        if selected:
            return selected, "selected"
    if allow_all_if_empty:
        all_items = [t for t in getattr(self, "queue_items", []) if _bk_lm_task_has_results(t)]
        if all_items:
            return _bk_lm_unique_tasks(all_items), "all"
    return [], ""


def _bk_lm_persist_visible_queue_state(self):
    try:
        self._persist_live_canvas_bboxes(self._current_task())
    except Exception:
        pass
    try:
        self._persist_loaded_preview_bboxes()
    except Exception:
        pass


class BKFullPageLMOCRWorker(AIRevisionWorker):
    """LM OCR über die komplette Seite, ohne vorhandene Overlay-Boxen zu verwenden."""

    def _response_format_full_page_lines(self) -> dict:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "lm_full_page_ocr_lines",
                "schema": {
                    "type": "object",
                    "properties": {
                        "lines": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "text": {"type": "string"},
                                },
                                "required": ["text"],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "required": ["lines"],
                    "additionalProperties": False,
                },
            },
        }

    def _extract_full_page_lines(self, content: str) -> List[str]:
        obj = _extract_json_payload(content)
        out: List[str] = []
        if isinstance(obj, dict):
            lines = obj.get("lines")
            if isinstance(lines, list):
                for item in lines:
                    if isinstance(item, dict):
                        txt = _clean_ocr_text(_force_text(item.get("text", "")))
                    else:
                        txt = _clean_ocr_text(_force_text(item))
                    if txt:
                        out.append(txt)
            elif isinstance(obj.get("text"), str):
                out.extend(_extract_text_lines(obj.get("text", "")))
        if not out:
            out = [_clean_ocr_text(x) for x in _extract_text_lines(content or "")]
            out = [x for x in out if x]
        return out

    def _request_full_page_ocr(self, page_data_url: str) -> List[str]:
        system_prompt = self._tr("ai_prompt_fullpage_lm_ocr_system")
        user_prompt = self._tr("ai_prompt_fullpage_lm_ocr_user")
        payload = {
            "model": self.lm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": page_data_url}},
                    ],
                },
            ],
            **self._build_sampling_payload(
                response_format=self._response_format_full_page_lines(),
                override_max_tokens=max(1, int(getattr(self, "max_tokens", 4500) or 4500)),
            ),
        }
        data = self._post_json(payload)
        content = self._extract_message_content(data)
        lines = self._extract_full_page_lines(content)
        if not lines:
            raise ValueError(self._tr("ai_err_page_no_usable_lines", 0, 0))
        return lines

    def run(self):
        if self._cancelled or self.isInterruptionRequested():
            self.failed_revision.emit(self.path, self._tr("msg_ai_ocr_cancelled"))
            return
        try:
            self.status_changed.emit(self._tr("ai_status_page_overlay_scan", os.path.basename(self.path)))
            self.progress_changed.emit(5)
            page_data_url = _page_to_data_url(self.path)
            self.progress_changed.emit(25)
            final_lines = self._request_full_page_ocr(page_data_url)
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_ai_ocr_cancelled"))
            final_lines = [_clean_ocr_text(x) for x in final_lines if _clean_ocr_text(x)]
            self.progress_changed.emit(100)
            self.status_changed.emit(self._tr("ai_status_page_overlay_done", os.path.basename(self.path)))
            self.finished_revision.emit(self.path, final_lines)
        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode("utf-8", errors="replace")
            except Exception:
                body = str(e)
            self.failed_revision.emit(self.path, f"HTTP-Fehler: {e}\n{body}")
        except urllib.error.URLError as e:
            self.failed_revision.emit(self.path, self._tr("ai_err_server_unreachable", e))
        except socket.timeout:
            self.failed_revision.emit(self.path, self._tr("ai_err_timeout"))
        except RuntimeError as e:
            self.failed_revision.emit(self.path, str(e))
        except Exception as e:
            msg = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            self.failed_revision.emit(self.path, msg)


class BKQueueLMBatchWorker(QThread):
    file_started = Signal(str, int, int, str)          # path, current, total, mode
    file_finished = Signal(str, str, object, object, int, int)  # path, mode, target_rows, revised_lines, current, total
    file_failed = Signal(str, str, int, int)           # path, error, current, total
    file_skipped = Signal(str, str, int, int)          # path, reason, current, total
    progress_changed = Signal(int)
    status_changed = Signal(str)
    finished_batch = Signal()

    def __init__(
        self,
        items: List[TaskItem],
        mode: str,
        row_indices: Optional[List[int]],
        lm_model: str,
        endpoint: str,
        enable_thinking: bool = False,
        script_mode: str = AI_SCRIPT_PRINT,
        temperature: float = 0.2,
        top_p: float = 0.8,
        top_k: int = 10,
        presence_penalty: float = 0.0,
        repetition_penalty: float = 1.0,
        min_p: float = 0.0,
        max_tokens: int = 1200,
        tr_func=None,
        parent=None,
    ):
        super().__init__(parent)
        self._tr = tr_func or translation.make_tr("de")
        self.items = list(items or [])
        self.mode = str(mode or _BK_LM_BATCH_MODE_ALL_LINES)
        self.row_indices = [int(r) for r in (row_indices or [])]
        self.lm_model = lm_model
        self.endpoint = endpoint
        self.enable_thinking = enable_thinking
        self.script_mode = _normalize_ai_script_mode(script_mode)
        self.temperature = float(temperature)
        self.top_p = float(top_p)
        self.top_k = int(top_k)
        self.presence_penalty = float(presence_penalty)
        self.repetition_penalty = float(repetition_penalty)
        self.min_p = float(min_p)
        self.max_tokens = int(max_tokens)
        self._current_worker = None
        self._cancel_requested = False

    def cancel(self):
        self._cancel_requested = True
        self.requestInterruption()
        worker = self._current_worker
        if worker is not None:
            try:
                worker.cancel()
            except Exception:
                pass

    def _item_recs_and_boxes(self, item: TaskItem):
        if not item or not item.results:
            return [], []
        _text, _kr_records, _im, recs = item.results
        recs = list(recs or [])
        boxes = list(getattr(item, "preset_bboxes", []) or [])
        if len(boxes) != len(recs):
            boxes = [rv.bbox for rv in recs]
        return recs, boxes

    def _target_rows_for_item(self, item: TaskItem):
        recs, boxes = self._item_recs_and_boxes(item)
        if self.mode == _BK_LM_BATCH_MODE_LM_OCR:
            # Fullpage-LM-OCR arbeitet direkt auf dem Bildpfad und braucht
            # weder vorhandene OCR-Zeilen noch Overlay-Boxen.
            return [], [RecordView(0, "", None)]
        if not recs:
            return [], []
        if self.mode == _BK_LM_BATCH_MODE_ALL_LINES:
            target_rows = list(range(len(recs)))
        elif self.mode in (_BK_LM_BATCH_MODE_CURRENT_LINE, _BK_LM_BATCH_MODE_SELECTED_LINES):
            target_rows = []
            seen = set()
            for row in self.row_indices:
                try:
                    row = int(row)
                except Exception:
                    continue
                if 0 <= row < len(recs) and row not in seen:
                    seen.add(row)
                    target_rows.append(row)
        else:
            target_rows = list(range(len(recs)))
        worker_recs = []
        for local_idx, row in enumerate(target_rows):
            bb = boxes[row] if row < len(boxes) else recs[row].bbox
            txt = recs[row].text
            worker_recs.append(
                RecordView(
                    local_idx,
                    str(txt or ""),
                    tuple(bb) if bb else None,
                )
            )
        return target_rows, worker_recs

    def _make_worker(self, item: TaskItem, worker_recs: List[RecordView]):
        common = dict(
            path=item.path,
            recs=worker_recs,
            lm_model=self.lm_model,
            endpoint=self.endpoint,
            enable_thinking=self.enable_thinking,
            source_kind=item.source_kind,
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            presence_penalty=self.presence_penalty,
            repetition_penalty=self.repetition_penalty,
            min_p=self.min_p,
            tr_func=self._tr,
            parent=None,
        )
        if self.mode == _BK_LM_BATCH_MODE_LM_OCR:
            return BKFullPageLMOCRWorker(
                **common,
                max_tokens=self.max_tokens,
            )
        return AIRevisionWorker(
            **common,
            script_mode=self.script_mode,
            max_tokens=self.max_tokens,
        )

    def _revise_one_item(self, item: TaskItem, current: int, total: int):
        if self.isInterruptionRequested() or self._cancel_requested:
            raise RuntimeError(self._tr("msg_ai_cancelled"))
        target_rows, worker_recs = self._target_rows_for_item(item)
        if not worker_recs:
            if self.mode == _BK_LM_BATCH_MODE_LM_OCR:
                raise ValueError(self._tr("warn_need_overlay_boxes_for_lm_ocr"))
            raise ValueError(self._tr("warn_need_done_for_ai"))
        result_holder: Dict[str, Any] = {}
        error_holder: Dict[str, Any] = {}
        worker = self._make_worker(item, worker_recs)
        self._current_worker = worker
        try:
            worker.status_changed.connect(self.status_changed.emit)
            worker.progress_changed.connect(
                lambda value, c=current, t=total: self.progress_changed.emit(
                    max(0, min(100, int((((c - 1) + (int(value) / 100.0)) / max(1, t)) * 100)))
                )
            )
            worker.finished_revision.connect(lambda path, lines: result_holder.setdefault("lines", list(lines or [])))
            worker.failed_revision.connect(lambda path, msg: error_holder.setdefault("msg", msg))
            worker.run()
        finally:
            self._current_worker = None
        if self.isInterruptionRequested() or self._cancel_requested:
            raise RuntimeError(self._tr("msg_ai_cancelled"))
        if "msg" in error_holder:
            raise RuntimeError(str(error_holder["msg"]))
        return target_rows, list(result_holder.get("lines", []))

    def run(self):
        total = len(self.items)
        if total <= 0:
            self.finished_batch.emit()
            return
        for i, item in enumerate(self.items, start=1):
            if self.isInterruptionRequested() or self._cancel_requested:
                break
            try:
                target_rows, worker_recs = self._target_rows_for_item(item)
                if not worker_recs:
                    reason = self._tr("warn_need_overlay_boxes_for_lm_ocr") if self.mode == _BK_LM_BATCH_MODE_LM_OCR else self._tr("warn_need_done_for_ai")
                    self.file_skipped.emit(item.path, reason, i, total)
                    self.progress_changed.emit(int((i / total) * 100))
                    continue
            except Exception as e:
                self.file_skipped.emit(item.path, str(e), i, total)
                self.progress_changed.emit(int((i / total) * 100))
                continue
            self.file_started.emit(item.path, i, total, self.mode)
            self.status_changed.emit(f"LM-Batch {i}/{total}: {os.path.basename(item.path)}")
            self.progress_changed.emit(int(((i - 1) / total) * 100))
            try:
                target_rows, revised_lines = self._revise_one_item(item, i, total)
                if self.isInterruptionRequested() or self._cancel_requested:
                    break
                self.file_finished.emit(item.path, self.mode, target_rows, revised_lines, i, total)
            except Exception as e:
                msg = str(e)
                self.file_failed.emit(item.path, msg, i, total)
                if _bk_is_cancel_message_v10(msg):
                    break
            self.progress_changed.emit(int((i / total) * 100))
        self.status_changed.emit("LM-Batch abgeschlossen.")
        self.finished_batch.emit()


def _bk_lm_apply_queue_batch_result(self, path: str, mode: str, target_rows: List[int], revised_lines: List[str]):
    task = next((i for i in getattr(self, "queue_items", []) if i.path == path), None)
    if not task:
        return
    revised_lines = [_clean_ocr_text(str(x).strip()) for x in (revised_lines or [])]

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


def _bk_lm_cancel_queue_batch(self):
    worker = getattr(self, "_bk_lm_queue_batch_worker", None)
    if worker is not None and worker.isRunning():
        worker.cancel()


def _bk_lm_run_queue_batch(self, mode: str, row_indices: Optional[List[int]] = None, *, targets: Optional[List[TaskItem]] = None, allow_selected: bool = False, allow_all_if_empty: bool = False):
    _bk_lm_persist_visible_queue_state(self)
    if _bk_lm_any_job_running(self):
        return False
    if targets is None:
        targets, _source = _bk_lm_queue_targets(self, allow_selected=allow_selected, allow_all_if_empty=allow_all_if_empty)
    if mode == _BK_LM_BATCH_MODE_LM_OCR:
        targets = _bk_lm_unique_tasks([t for t in (targets or []) if getattr(t, "path", None)])
    else:
        targets = _bk_lm_unique_tasks([t for t in (targets or []) if _bk_lm_task_has_results(t)])
    if not targets:
        return False
    model_id = self._resolve_ai_model_id()
    if not model_id:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_ai_model"))
        return True
    script_mode = AI_SCRIPT_PRINT
    if mode != _BK_LM_BATCH_MODE_LM_OCR:
        script_mode = self._choose_ai_script_mode()
        if not script_mode:
            return True
    self.act_ai_revise.setEnabled(False)
    if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
        self.btn_ai_revise_bottom.setEnabled(False)
    title = self._tr("dlg_ai_ocr_title") if mode == _BK_LM_BATCH_MODE_LM_OCR else self._tr("act_ai_revise")
    self._bk_lm_queue_batch_mode = mode
    self._bk_lm_queue_batch_dialog = ProgressStatusDialog(title, self._tr, self)
    self._bk_lm_queue_batch_dialog.set_status("LM-Batch wird vorbereitet ...")
    self._bk_lm_queue_batch_dialog.cancel_requested.connect(lambda: _bk_lm_cancel_queue_batch(self))
    self._bk_lm_queue_batch_dialog.show()
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
        max_tokens=(self._lm_token_limit("lm_ocr") if mode == _BK_LM_BATCH_MODE_LM_OCR and hasattr(self, "_lm_token_limit") else (4500 if mode == _BK_LM_BATCH_MODE_LM_OCR else (self._lm_token_limit("all_lines") if hasattr(self, "_lm_token_limit") else self.ai_max_tokens))),
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
    # Kein Queue-Batch mehr: Diese Funktion bearbeitet bewusst nur die aktuell
    # geladene Vorschauseite und dort nur die aktuelle Zeile.
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
    # Kein Queue-Batch mehr: Diese Funktion bearbeitet bewusst nur die aktuell
    # geladene Vorschauseite und dort nur die markierten Zeilen.
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
    # Wenn keine Checkbox aktiv ist, bleibt das alte Verhalten erhalten: aktuelle Vorschau-Seite.
    task = _bk_lm_get_current_done_task(self)
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return
    _bk_lm_run_queue_batch(self, _BK_LM_BATCH_MODE_ALL_LINES, targets=[task])


def _bk_lm_run_overlay_lm_ocr_current_task(self):
    # LM OCR arbeitet jetzt als kompletter Seiten-OCR ohne Overlay-Boxen.
    # Checkboxen im Wartebereich haben Priorität; sonst wird nur die aktuelle
    # Vorschauseite verarbeitet.
    checked_targets = _bk_lm_checked_queue_tasks_any(self)
    if checked_targets:
        _bk_lm_run_queue_batch(self, _BK_LM_BATCH_MODE_LM_OCR, targets=checked_targets)
        return
    task = _bk_lm_get_current_task_any(self)
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return
    _bk_lm_run_queue_batch(self, _BK_LM_BATCH_MODE_LM_OCR, targets=[task])


def _bk_lm_run_revision_from_queue_context(self):
    # Rechtsklick im Wartebereich: Checkboxen haben Priorität, sonst selektierte/angeklickte Zeile.
    if _bk_lm_run_queue_batch(self, _BK_LM_BATCH_MODE_ALL_LINES, allow_selected=True):
        return
    task = _bk_lm_get_current_done_task(self)
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return
    _bk_lm_run_queue_batch(self, _BK_LM_BATCH_MODE_ALL_LINES, targets=[task])


def _bk_lm_run_ai_revision_patched(self):
    # Ctrl+L / alte Action / Queue-Kontext: als Batch für Checkbox-Auswahl ausführen.
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

    # Aktuelle/markierte Zeilen bleiben auf die aktuell geladene Vorschauseite begrenzt.
    self.act_ai_menu_current_line.setEnabled(has_current_task and row >= 0 and not busy)
    self.act_ai_menu_selected_lines.setEnabled(has_current_task and len(selected_rows) > 0 and not busy)

    # Batch gibt es nur für "Alle Zeilen" und "LM OCR".
    has_all_lines_target = has_checked or has_current_task
    has_lm_ocr_target = has_checked_any or has_current_any_task
    self.act_ai_menu_all_lines.setEnabled(has_all_lines_target and not busy)
    if hasattr(self, "act_ai_menu_lm_ocr"):
        self.act_ai_menu_lm_ocr.setEnabled(has_lm_ocr_target and not busy)
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
    self.act_ai_menu_postgres = QAction(self._tr("lm_menu_generate_postgres"), self)
    self.act_ai_menu_neo4j = QAction(self._tr("lm_menu_generate_neo4j"), self)
    self.act_ai_menu_current_line.triggered.connect(lambda: _bk_lm_run_current_line(self))
    self.act_ai_menu_selected_lines.triggered.connect(lambda: _bk_lm_run_selected_lines(self))
    self.act_ai_menu_all_lines.triggered.connect(lambda: _bk_lm_run_all_lines_current_task(self))
    self.act_ai_menu_lm_ocr.triggered.connect(lambda: _bk_lm_run_overlay_lm_ocr_current_task(self))
    self.act_ai_menu_postgres.triggered.connect(lambda: _bk_lm_generate_local_json(self, "postgres"))
    self.act_ai_menu_neo4j.triggered.connect(lambda: _bk_lm_generate_local_json(self, "neo4j"))
    self.btn_ai_revise_menu = QMenu(self)
    self.btn_ai_revise_menu.aboutToShow.connect(lambda: _bk_lm_update_dropdown_state(self))
    self.btn_ai_revise_menu.addAction(self.act_ai_menu_current_line)
    self.btn_ai_revise_menu.addAction(self.act_ai_menu_selected_lines)
    self.btn_ai_revise_menu.addAction(self.act_ai_menu_all_lines)
    self.btn_ai_revise_menu.addSeparator()
    self.btn_ai_revise_menu.addAction(self.act_ai_menu_lm_ocr)
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
    self.act_ai_menu_postgres.setText(self._tr("lm_menu_generate_postgres"))
    self.act_ai_menu_neo4j.setText(self._tr("lm_menu_generate_neo4j"))
    if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
        self.btn_ai_revise_bottom.setToolTip(self._tr("btn_ai_revise_menu_tip"))
    _bk_lm_update_dropdown_state(self)


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


# Klasse final überschreiben. Dadurch funktionieren auch bereits früher definierte Wrapper,
# weil sie die globalen Funktionsnamen dieses Moduls erst zur Laufzeit auflösen.
MainWindow._bk_lm_install_dropdown_menu = _bk_lm_install_dropdown_menu
MainWindow._bk_lm_retranslate_dropdown = _bk_lm_retranslate_dropdown
MainWindow._bk_lm_run_all_lines_current_task = _bk_lm_run_all_lines_current_task
MainWindow._bk_lm_run_overlay_lm_ocr_current_task = _bk_lm_run_overlay_lm_ocr_current_task
MainWindow.run_ai_revision = _bk_lm_run_ai_revision_patched
MainWindow.run_ai_revision_for_selected = _bk_lm_run_ai_revision_for_selected_patched
MainWindow.run_ai_revision_for_all = _bk_lm_run_ai_revision_for_all_patched
MainWindow.queue_context_menu = _bk_lm_queue_context_menu_patched
MainWindow.preview_image = _bk_lm_preview_image_patched
MainWindow.load_results = _bk_lm_load_results_patched
MainWindow.refresh_preview = _bk_lm_refresh_preview_patched
MainWindow._persist_loaded_preview_bboxes = _bk_lm_persist_loaded_preview_bboxes_patched
MainWindow._cancel_ai_batch_revision = _bk_lm_cancel_ai_batch_revision_patched
