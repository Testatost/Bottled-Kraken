from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
def _bk_source_blocks_for_local_json_v19(recs: List[RecordView], page_w: int = 0, page_h: int = 0) -> List[List[str]]:
    cleaned_recs = [rv for rv in recs if _clean_ocr_text(getattr(rv, 'text', ''))]
    if not cleaned_recs:
        return []
    if any(getattr(rv, 'bbox', None) for rv in cleaned_recs):
        pw = int(page_w or max((rv.bbox[2] for rv in cleaned_recs if rv.bbox), default=0) or 0)
        ph = int(page_h or max((rv.bbox[3] for rv in cleaned_recs if rv.bbox), default=0) or 0)
        if pw > 0 and ph > 0:
            ordered = sort_records_reading_order(cleaned_recs, pw, ph, READING_MODES['TB_LR'])
        else:
            ordered = sorted(cleaned_recs, key=lambda rv: (_bk_record_y0_v10(rv), _bk_record_x0_v10(rv)))
    else:
        ordered = cleaned_recs
    lines = [_clean_ocr_text(rv.text) for rv in ordered if _clean_ocr_text(rv.text)]
    if not lines:
        return []
    blocks = []
    for idx in range(len(lines)):
        prev_line = lines[idx - 1] if idx > 0 else None
        curr_line = lines[idx]
        next_line = lines[idx + 1] if idx + 1 < len(lines) else None
        block = []
        if prev_line:
            block.append(prev_line)
        block.append(curr_line)
        if next_line:
            block.append(next_line)
        blocks.append(block)
    return blocks
_bk_source_blocks_for_local_json_v10 = _bk_source_blocks_for_local_json_v19
def _bk_lm_collect_current_text_v19(self, task) -> str:
    recs = self._current_recs_for_ai(task)
    if not recs:
        return ''
    page_w = 0
    page_h = 0
    try:
        if task and task.results and task.results[2] is not None:
            page_w, page_h = task.results[2].size
    except Exception:
        page_w = 0
        page_h = 0
    blocks = _bk_source_blocks_for_local_json_v19(recs, page_w=page_w, page_h=page_h)
    if not blocks:
        lines = [_clean_ocr_text(rv.text) for rv in recs if _clean_ocr_text(rv.text)]
        blocks = [[line] for line in lines]
    return _bk_blocks_to_text_v10(blocks).strip()
_bk_lm_collect_current_text = _bk_lm_collect_current_text_v19
MainWindow._bk_lm_collect_current_text = _bk_lm_collect_current_text_v19
def _bk_lm_generate_local_json_v19(self, schema_kind: str):
    task = _bk_lm_get_current_done_task(self)
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return
    source_text = _bk_lm_collect_current_text_v19(self, task)
    if not source_text:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_no_text_for_json"))
        return
    model_id = self._resolve_ai_model_id()
    if not model_id:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_ai_model"))
        return
    if _bk_lm_any_job_running(self):
        return
    kind = (schema_kind or "postgres").strip().lower()
    self._bk_local_json_context = {"path": task.path, "schema_kind": kind}
    self.act_ai_revise.setEnabled(False)
    if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
        self.btn_ai_revise_bottom.setEnabled(False)
    if kind == "neo4j":
        self.status_bar.showMessage(self._tr("msg_local_json_started_neo4j"))
        notice_text = self._tr("dlg_local_json_notice_text_neo4j")
    else:
        self.status_bar.showMessage(self._tr("msg_local_json_started_postgres"))
        notice_text = self._tr("dlg_local_json_notice_text_postgres")
    self._log(self._tr_log("log_local_json_started", os.path.basename(task.path), _bk_json_schema_kind_label(self, kind)))
    title_key = "dlg_local_json_title_neo4j" if kind == "neo4j" else "dlg_local_json_title_postgres"
    self._bk_local_json_dialog = BKLocalJsonNoticeDialog(self._tr(title_key), notice_text, self._tr, self)
    self._bk_local_json_dialog.cancel_requested.connect(lambda: _bk_lm_cancel_local_json(self))
    self._bk_local_json_dialog.show()
    self._bk_local_json_worker = BKLocalStructuredJsonWorker(
        path=task.path,
        source_text=source_text,
        schema_kind=kind,
        lm_model=model_id,
        endpoint=self.ai_endpoint,
        enable_thinking=self.ai_enable_thinking,
        temperature=self.ai_temperature,
        top_p=self.ai_top_p,
        top_k=self.ai_top_k,
        presence_penalty=self.ai_presence_penalty,
        repetition_penalty=self.ai_repetition_penalty,
        min_p=self.ai_min_p,
        max_tokens=max(int(getattr(self, "ai_max_tokens", 1200) or 1200), 2200),
        tr_func=self._tr,
        parent=self,
    )
    self._bk_local_json_worker.status_changed.connect(self._log)
    self._bk_local_json_worker.finished_json.connect(lambda path, kind, data: _bk_lm_on_local_json_done(self, path, kind, data))
    self._bk_local_json_worker.failed_json.connect(lambda path, kind, msg: _bk_lm_on_local_json_failed(self, path, kind, msg))
    self._bk_local_json_worker.start()
_bk_lm_generate_local_json = _bk_lm_generate_local_json_v19
__all__ = [
    '_bk_lm_collect_current_text',
    '_bk_lm_collect_current_text_v19',
    '_bk_lm_generate_local_json',
    '_bk_lm_generate_local_json_v19',
    '_bk_source_blocks_for_local_json_v10',
    '_bk_source_blocks_for_local_json_v19',
]
register_globals('bk', globals(), __all__)
