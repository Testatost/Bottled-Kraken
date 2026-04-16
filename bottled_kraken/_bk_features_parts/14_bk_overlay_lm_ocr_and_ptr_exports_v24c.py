def _ptr_export_ai_postgres_for_current_v24c(self, path: str):
    data = self._ptr_ai_postgres_by_path.get(path)
    default_name = f"{os.path.splitext(os.path.basename(path))[0]}_postgres.json"
    self._ptr_export_json_interactive(data, _ptr_ui_tr(self, 'ptr_export_postgres_json'), default_name)

def _ptr_export_ai_neo4j_for_current_v24c(self, path: str):
    data = self._ptr_ai_neo4j_by_path.get(path)
    default_name = f"{os.path.splitext(os.path.basename(path))[0]}_neo4j.json"
    self._ptr_export_json_interactive(data, _ptr_ui_tr(self, 'ptr_export_neo4j_json'), default_name)

def _ptr_open_multi_followup_for_path_v24c(self, path: str):
    variants = self._ptr_multi_ocr_variants_by_path.get(path, [])
    if not variants:
        QMessageBox.information(self, _ptr_ui_tr(self, 'ptr_multi_ocr_title'), _ptr_ui_tr(self, 'ptr_multi_no_variants'))
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
        self._ptr_open_ai_tools(path, auto_mode='postgres')
        return
    if choice == PtrMultiOCRFollowupDialog.CHOICE_AI_NEO4J:
        self._ptr_open_ai_tools(path, auto_mode='neo4j')
        return
    if choice == PtrMultiOCRFollowupDialog.CHOICE_AI_BOTH:
        self._ptr_open_ai_tools(path, auto_mode='pipeline')
        return

def _ptr_reopen_multi_followup_v24c(self):
    target = getattr(self, '_ptr_last_multi_followup_path', None)
    if not target:
        QMessageBox.information(self, _ptr_ui_tr(self, 'ptr_multi_ocr_title'), _ptr_ui_tr(self, 'ptr_multi_no_followup'))
        return
    self._ptr_open_multi_followup_for_path(target)

MainWindow._ptr_apply_local_merge_to_task = _ptr_apply_local_merge_to_task_v24c

MainWindow._ptr_open_ai_tools = _ptr_open_ai_tools_v24c

MainWindow._ptr_store_ai_merge = _ptr_store_ai_merge_v24c

MainWindow._ptr_store_ai_postgres = _ptr_store_ai_postgres_v24c

MainWindow._ptr_store_ai_neo4j = _ptr_store_ai_neo4j_v24c

MainWindow._ptr_export_ai_merge_for_current = _ptr_export_ai_merge_for_current_v24c

MainWindow._ptr_export_ai_postgres_for_current = _ptr_export_ai_postgres_for_current_v24c

MainWindow._ptr_export_ai_neo4j_for_current = _ptr_export_ai_neo4j_for_current_v24c

MainWindow._ptr_open_multi_followup_for_path = _ptr_open_multi_followup_for_path_v24c

MainWindow._ptr_reopen_multi_followup = _ptr_reopen_multi_followup_v24c

def _bk_is_cancel_message_v10(msg: Any) -> bool:
    txt = str(msg or "").lower()
    return (
        "abgebrochen" in txt
        or "cancelled" in txt
        or "canceled" in txt
        or "annulé" in txt
        or "annule" in txt
        or "annulée" in txt
        or "annulee" in txt
    )

class BKOverlayLMOCRWorker(AIRevisionWorker):
    def _request_page_ocr_with_fixed_linecount(self, page_data_url: str, recs: List[RecordView]) -> List[str]:
        img_w, img_h = _load_image_color(self.path).size
        line_specs = []
        for rv in recs:
            line_specs.append({
                "idx": int(rv.idx),
                "bbox": _normalize_bbox(rv.bbox, img_w, img_h)
            })
        system_prompt = self._tr("ai_prompt_page_system")
        user_prompt = self._tr(
            "ai_prompt_page_user",
            len(recs),
            len(recs),
            len(recs) - 1,
            json.dumps(line_specs, ensure_ascii=False)
        )

        def _extract_out_lines(content: str):
            obj = _extract_json_payload(content)
            if not isinstance(obj, dict):
                return None
            lines = obj.get("lines")
            if not isinstance(lines, list):
                return None
            out = [""] * len(recs)
            for item in lines:
                if not isinstance(item, dict):
                    continue
                idx = item.get("idx")
                txt = _force_text(item.get("text", "")).strip()
                if isinstance(idx, int) and 0 <= idx < len(recs):
                    out[idx] = _clean_ocr_text(txt)
            return out

        max_tokens_candidates = []
        primary_tokens = self._effective_revision_max_tokens("page", len(recs))
        max_tokens_candidates.append(primary_tokens)
        retry_tokens = min(12000, max(primary_tokens * 2, 2400, 180 * len(recs) + 600))
        if retry_tokens not in max_tokens_candidates:
            max_tokens_candidates.append(retry_tokens)

        last_content = ""
        last_data = None
        for attempt_no, max_tokens in enumerate(max_tokens_candidates, start=1):
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
                    response_format=self._response_format_lines(),
                    override_max_tokens=max_tokens,
                ),
            }
            data = self._post_json(payload)
            last_data = data
            content = self._extract_message_content(data)
            last_content = content
            out = _extract_out_lines(content)
            if out is not None:
                filled = sum(1 for x in out if str(x).strip())
                too_long_blocks = sum(1 for x in out if len(str(x).strip()) > 120)
                if too_long_blocks >= 1:
                    raise ValueError(self._tr("ai_err_page_long_blocks"))
                if filled == 0:
                    raise ValueError(self._tr("ai_err_page_no_usable_lines", filled, len(recs)))
                return out
            finish_reason = ""
            try:
                choices = data.get("choices") if isinstance(data, dict) else None
                if isinstance(choices, list) and choices and isinstance(choices[0], dict):
                    finish_reason = str(choices[0].get("finish_reason", "")).strip().lower()
            except Exception:
                finish_reason = ""
            looks_truncated = (
                finish_reason == "length"
                or (content or "").count("{") > (content or "").count("}")
                or '"lines"' in (content or "")
            )
            if attempt_no >= len(max_tokens_candidates) or not looks_truncated:
                break

        if isinstance(last_data, dict):
            try:
                choices = last_data.get("choices")
                if isinstance(choices, list) and choices and isinstance(choices[0], dict):
                    finish_reason = str(choices[0].get("finish_reason", "")).strip().lower()
                    if finish_reason == "length":
                        raise ValueError(
                            self._tr("ai_err_page_invalid_json", (last_content[:2600] + "\n\n[Hinweis: Modellantwort wurde wahrscheinlich wegen max_tokens abgeschnitten.]") if last_content else "<leer>")
                        )
            except ValueError:
                raise
            except Exception:
                pass
        raise ValueError(
            self._tr("ai_err_page_invalid_json", last_content[:3000] if last_content else "<leer>")
        )

    def run(self):
        if self._cancelled or self.isInterruptionRequested():
            self.failed_revision.emit(self.path, self._tr("msg_ai_ocr_cancelled"))
            return
        try:
            if not self.recs:
                self.finished_revision.emit(self.path, [])
                return
            self.status_changed.emit(self._tr("ai_status_page_overlay_scan", os.path.basename(self.path)))
            self.progress_changed.emit(5)
            page_data_url = _page_to_data_url(self.path)
            final_lines = self._request_page_ocr_with_fixed_linecount(page_data_url, self.recs)
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_ai_ocr_cancelled"))
            final_lines = [_clean_ocr_text(x) for x in final_lines]
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

def _bk_lm_run_overlay_lm_ocr_current_task(self):
    task = _bk_lm_get_current_done_task(self)
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return
    if getattr(self, "ai_worker", None) and self.ai_worker.isRunning():
        return
    model_id = self._resolve_ai_model_id()
    if not model_id:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_ai_model"))
        return
    recs_for_ai = self._current_recs_for_ai(task)
    if not recs_for_ai:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return
    boxed_pairs = [
        (i, rv) for i, rv in enumerate(recs_for_ai)
        if getattr(rv, "bbox", None)
    ]
    if not boxed_pairs:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_overlay_boxes_for_lm_ocr"))
        return
    target_indices = [i for i, _ in boxed_pairs]
    boxed_recs = [rv for _, rv in boxed_pairs]
    task._bk_lm_ocr_target_indices = list(target_indices)
    blank_recs = [
        RecordView(i, "", tuple(rv.bbox) if rv.bbox else None)
        for i, rv in enumerate(boxed_recs)
    ]
    self.act_ai_revise.setEnabled(False)
    try:
        if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
            self.btn_ai_revise_bottom.setEnabled(False)
    except Exception:
        pass
    self.status_bar.showMessage(self._tr("msg_ai_ocr_started"))
    self._log(self._tr("log_ai_ocr_started", os.path.basename(task.path)))
    self.ai_progress_dialog = BKLocalJsonNoticeDialog(self._tr("dlg_ai_ocr_title"), self._tr("dlg_ai_ocr_status"), self._tr, self)
    self.ai_progress_dialog.set_status(self._tr("dlg_ai_ocr_status"))
    self.ai_progress_dialog.cancel_requested.connect(self._cancel_ai_revision)
    self.ai_progress_dialog.show()
    self.ai_worker = BKOverlayLMOCRWorker(
        path=task.path,
        recs=blank_recs,
        lm_model=model_id,
        endpoint=self.ai_endpoint,
        enable_thinking=self.ai_enable_thinking,
        source_kind=task.source_kind,
        temperature=self.ai_temperature,
        top_p=self.ai_top_p,
        top_k=self.ai_top_k,
        presence_penalty=self.ai_presence_penalty,
        repetition_penalty=self.ai_repetition_penalty,
        min_p=self.ai_min_p,
        max_tokens=max(int(getattr(self, "ai_max_tokens", 1200) or 1200), 1400),
        tr_func=self._tr,
        parent=self,
    )
    self.ai_worker.progress_changed.connect(self.ai_progress_dialog.set_progress)
    self.ai_worker.status_changed.connect(self.ai_progress_dialog.set_status)
    self.ai_worker.status_changed.connect(self._log)
    self.ai_worker.finished_revision.connect(self.on_ai_overlay_lm_ocr_done)
    self.ai_worker.failed_revision.connect(self.on_ai_overlay_lm_ocr_failed)
    self.ai_worker.start()

def _bk_on_ai_overlay_lm_ocr_done(self, path: str, revised_lines: list):
    task = next((i for i in self.queue_items if i.path == path), None)
    if not task or not task.results:
        if task is not None:
            try:
                delattr(task, "_bk_lm_ocr_target_indices")
            except Exception:
                pass
        self.act_ai_revise.setEnabled(True)
        try:
            if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
                self.btn_ai_revise_bottom.setEnabled(True)
        except Exception:
            pass
        self._close_ai_progress_dialog()
        return
    text, kr_records, im, recs = task.results
    revised_lines = [_clean_ocr_text(str(x).strip()) for x in (revised_lines or [])]
    target_indices = list(getattr(task, "_bk_lm_ocr_target_indices", []) or [])
    self._push_undo(task)
    if target_indices:
        if len(revised_lines) < len(target_indices):
            revised_lines.extend([""] * (len(target_indices) - len(revised_lines)))
        elif len(revised_lines) > len(target_indices):
            revised_lines = revised_lines[:len(target_indices)]
        revised_map = {target_indices[i]: revised_lines[i] for i in range(len(target_indices))}
        new_recs = [
            RecordView(i, revised_map.get(i, recs[i].text), recs[i].bbox)
            for i in range(len(recs))
        ]
    else:
        if len(revised_lines) < len(recs):
            revised_lines.extend([""] * (len(recs) - len(revised_lines)))
        elif len(revised_lines) > len(recs):
            revised_lines = revised_lines[:len(recs)]
        new_recs = [
            RecordView(i, revised_lines[i], recs[i].bbox)
            for i in range(len(recs))
        ]
    try:
        delattr(task, "_bk_lm_ocr_target_indices")
    except Exception:
        pass
    task.results = (
        "\n".join(rv.text for rv in new_recs).strip(),
        kr_records,
        im,
        new_recs,
    )
    task.edited = True
    cur = self._current_task()
    if cur and cur.path == path:
        keep_row = self.list_lines.currentRow()
        if keep_row < 0:
            keep_row = 0 if new_recs else None
        self._sync_ui_after_recs_change(task, keep_row=keep_row)
    else:
        self._update_queue_row(path)
    self.act_ai_revise.setEnabled(True)
    try:
        if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
            self.btn_ai_revise_bottom.setEnabled(True)
    except Exception:
        pass
    self.status_bar.showMessage(self._tr("msg_ai_ocr_done"))
    self._log(self._tr("log_ai_ocr_done", os.path.basename(path)))
    self._close_ai_progress_dialog()

def _bk_on_ai_overlay_lm_ocr_failed(self, path: str, msg: str):
    task = next((i for i in self.queue_items if i.path == path), None)
    if task is not None:
        try:
            delattr(task, "_bk_lm_ocr_target_indices")
        except Exception:
            pass
    self.act_ai_revise.setEnabled(True)
    try:
        if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
            self.btn_ai_revise_bottom.setEnabled(True)
    except Exception:
        pass
    if _bk_is_cancel_message_v10(msg):
        self.status_bar.showMessage(self._tr("msg_ai_ocr_cancelled"))
        self._log(self._tr("msg_ai_ocr_cancelled"))
    else:
        self.status_bar.showMessage(self._tr("msg_ai_ocr_failed"))
        self._log(self._tr("log_ai_ocr_failed", os.path.basename(path), msg))
        QMessageBox.warning(self, self._tr("warn_title"), msg)
    self._close_ai_progress_dialog()

_bk_prev_lm_update_dropdown_state_v10 = _bk_lm_update_dropdown_state

_bk_prev_lm_install_dropdown_menu_v10 = _bk_lm_install_dropdown_menu

_bk_prev_lm_retranslate_dropdown_v10 = _bk_lm_retranslate_dropdown

def _bk_lm_update_dropdown_state(self):
    _bk_prev_lm_update_dropdown_state_v10(self)
    if not hasattr(self, "act_ai_menu_lm_ocr"):
        return
    task = _bk_lm_get_current_done_task(self)
    has_task = bool(task)
    has_boxes = False
    try:
        if task is not None:
            has_boxes = any(rv.bbox for rv in self._current_recs_for_ai(task))
    except Exception:
        has_boxes = False
    busy = _bk_lm_any_job_running(self)
    self.act_ai_menu_lm_ocr.setEnabled(has_task and has_boxes and not busy)

def _bk_lm_install_dropdown_menu(self):
    _bk_prev_lm_install_dropdown_menu_v10(self)
    if not hasattr(self, "act_ai_menu_lm_ocr"):
        self.act_ai_menu_lm_ocr = QAction(self._tr("lm_menu_lm_ocr"), self)
        self.act_ai_menu_lm_ocr.triggered.connect(lambda: _bk_lm_run_overlay_lm_ocr_current_task(self))
    if hasattr(self, "btn_ai_revise_menu") and self.btn_ai_revise_menu is not None:
        existing = list(self.btn_ai_revise_menu.actions())
        if self.act_ai_menu_lm_ocr not in existing:
            before = getattr(self, "act_ai_menu_postgres", None)
            if before is not None:
                self.btn_ai_revise_menu.insertAction(before, self.act_ai_menu_lm_ocr)
            else:
                self.btn_ai_revise_menu.addAction(self.act_ai_menu_lm_ocr)
    try:
        if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
            self.btn_ai_revise_bottom.setToolTip(self._tr("btn_ai_revise_menu_tip"))
    except Exception:
        pass
    _bk_lm_update_dropdown_state(self)

def _bk_lm_retranslate_dropdown(self):
    _bk_prev_lm_retranslate_dropdown_v10(self)
    if hasattr(self, "act_ai_menu_lm_ocr"):
        self.act_ai_menu_lm_ocr.setText(self._tr("lm_menu_lm_ocr"))
    try:
        if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
            self.btn_ai_revise_bottom.setToolTip(self._tr("btn_ai_revise_menu_tip"))
    except Exception:
        pass
    _bk_lm_update_dropdown_state(self)
