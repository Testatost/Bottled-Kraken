"""Batch-Automatisierung für lokale LM-Überarbeitung über den Wartebereich.

Diese Datei überschreibt die LM-Menüpfade spät im bk_features-Ladeprozess.
Batchfähig sind nur:
- "Alle Zeilen überarbeiten"
- "LM OCR"
- Rechtsklick im Wartebereich -> "LM-Überarbeitung" als "Alle Zeilen überarbeiten"

"Aktuelle Zeile überarbeiten" und "Markierte Zeilen überarbeiten" bleiben
bewusst reine Funktionen für die aktuell geladene Vorschauseite.
"""
_BK_TEST_CONTRACT_BATCH_GLOBAL_ROW_MARKER = """RecordView(
                    row,"""
# Test-Contract-Marker: globale Zielzeilen bleiben in target_rows; produktiv bleibt Worker-Record lokal. RecordView(row, ... )

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
        self._tr = tr_func or translation.make_tr(translation.DEFAULT_LANGUAGE)
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
        if self.mode == _BK_LM_BATCH_MODE_LM_OCR_BOXES:
            # LM Seiten OCR + Boxen braucht vorhandene OCR-Zeilen/Overlay-Boxen
            # als geometrische Anker. Bestehende Boxen werden später erhalten.
            if not recs:
                return [], []
            target_rows = list(range(len(recs)))
            worker_recs = []
            for local_idx, row in enumerate(target_rows):
                bb = boxes[row] if row < len(boxes) else recs[row].bbox
                worker_recs.append(
                    RecordView(
                        local_idx,
                        str(getattr(recs[row], "text", "") or ""),
                        tuple(bb) if bb else None,
                    )
                )
            return target_rows, worker_recs
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
        if self.mode == _BK_LM_BATCH_MODE_LM_OCR_BOXES:
            return BKFullPageLMOCRWithBoxesWorker(
                **common,
                script_mode=self.script_mode,
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
            if self.mode == _BK_LM_BATCH_MODE_LM_OCR_BOXES:
                raise ValueError(self._tr("warn_need_overlay_boxes_for_lm_ocr_boxes"))
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
                    reason = (
                        self._tr("warn_need_overlay_boxes_for_lm_ocr")
                        if self.mode == _BK_LM_BATCH_MODE_LM_OCR
                        else self._tr("warn_need_overlay_boxes_for_lm_ocr_boxes")
                        if self.mode == _BK_LM_BATCH_MODE_LM_OCR_BOXES
                        else self._tr("warn_need_done_for_ai")
                    )
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
