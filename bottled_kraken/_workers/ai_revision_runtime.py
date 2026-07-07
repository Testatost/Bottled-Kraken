from bottled_kraken.common import (
    _ai_script_crop_profile,
    _clean_ocr_text,
    _crop_block_to_data_url_context,
    _crop_single_line_to_data_url,
)
from bottled_kraken.common import (
    List,
    os,
    socket,
    traceback,
    urllib,
)
class AIRevisionRuntimeMixin:
    def run(self):
        if self._cancelled or self.isInterruptionRequested():
            self.failed_revision.emit(self.path, self._tr("msg_ai_cancelled"))
            return
        try:
            original_lines = [rv.text for rv in self.recs]
            if not self.recs:
                self.finished_revision.emit(self.path, [])
                return
            self.status_changed.emit(self._tr("ai_status_start_free_ocr", os.path.basename(self.path)))
            self.progress_changed.emit(0)
            crop_profile = _ai_script_crop_profile(self.script_mode)
            self.status_changed.emit(self._tr("ai_status_step1_title", os.path.basename(self.path)))
            box_lines: List[str] = []
            total = max(1, len(self.recs))
            for i, rv in enumerate(self.recs):
                if self._cancelled or self.isInterruptionRequested():
                    raise RuntimeError(self._tr("msg_ai_cancelled"))
                self.status_changed.emit(
                    self._tr("ai_status_step1_line", i + 1, total, os.path.basename(self.path))
                )
                try:
                    line_data_url = _crop_single_line_to_data_url(
                        self.path,
                        rv,
                        pad_x=crop_profile["single_pad_x"],
                        pad_y=crop_profile["single_pad_y"],
                        extra_context_y=crop_profile["single_extra_context_y"],
                    )
                    box_text = self._request_single_line_reread(
                        line_data_url=line_data_url,
                        idx=rv.idx,
                        current_text=str(rv.text or "")
                    )
                except Exception as e:
                    print(f"BOX OCR ERROR idx={rv.idx}: {e}")
                    box_text = "" if self._looks_like_manual_placeholder(str(rv.text or "")) else rv.text
                if not str(box_text).strip():
                    box_text = "" if self._looks_like_manual_placeholder(str(rv.text or "")) else rv.text
                box_lines.append(str(box_text).strip())
                self.progress_changed.emit(int(((i + 1) / total) * 55))
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_ai_cancelled"))
            is_form_like = self._looks_like_form_layout()
            if is_form_like:
                self.status_changed.emit(
                    self._tr("ai_status_step2_form", os.path.basename(self.path))
                )
            else:
                self.status_changed.emit(
                    self._tr("ai_status_step2_plain", os.path.basename(self.path))
                )
            page_lines = [rv.text for rv in self.recs]
            chunks = self._chunk_records(self.recs, block_size=3)
            for chunk_idx, (start, end) in enumerate(chunks, start=1):
                if self._cancelled or self.isInterruptionRequested():
                    raise RuntimeError(self._tr("msg_ai_cancelled"))
                self.status_changed.emit(
                    self._tr("ai_status_step2_chunk", chunk_idx, len(chunks), start + 1, end)
                )
                try:
                    block_data_url = _crop_block_to_data_url_context(
                        self.path,
                        self.recs,
                        start,
                        end,
                        pad_x=crop_profile["block_pad_x"],
                        pad_y=crop_profile["block_pad_y"],
                    )
                    reread = self._request_block_reread(
                        block_data_url=block_data_url,
                        start_idx=start,
                        end_idx=end,
                        current_lines=page_lines[start:end],
                    )
                    if isinstance(reread, list) and len(reread) == (end - start):
                        for local_i, txt in enumerate(reread):
                            txt = _clean_ocr_text(txt)
                            if txt:
                                page_lines[start + local_i] = txt
                except Exception as e:
                    print(f"BLOCK OCR ERROR {start}-{end}: {e}")
                self.progress_changed.emit(55 + int((chunk_idx / max(1, len(chunks))) * 15))
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_ai_cancelled"))
            self.status_changed.emit(
                self._tr("ai_status_step3_merge", os.path.basename(self.path))
            )
            final_lines: List[str] = []
            for i, rv in enumerate(self.recs):
                kraken_text = str(rv.text or "").strip()
                box_text = str(box_lines[i] if i < len(box_lines) else "").strip()
                page_text = str(page_lines[i] if i < len(page_lines) else "").strip()
                prev_final = final_lines[i - 1] if i > 0 else ""
                if self._looks_like_manual_placeholder(kraken_text):
                    if self._is_usable_image_line_result(box_text):
                        best_text = box_text
                    elif self._is_usable_image_line_result(page_text):
                        best_text = page_text
                    else:
                        best_text = ""
                else:
                    best_text = self._request_line_decision(
                        idx=i,
                        kraken_text=kraken_text,
                        page_text=page_text,
                        box_text=box_text,
                    ).strip()
                    if self._looks_like_manual_placeholder(best_text) and self._is_usable_image_line_result(box_text):
                        best_text = box_text
                if not best_text:
                    best_text = self._choose_final_line_text(
                        kraken_text=kraken_text,
                        box_text=box_text,
                        page_text=page_text,
                        prev_final_text=prev_final,
                    )
                if not best_text:
                    best_text = _clean_ocr_text(box_text or kraken_text or page_text)
                final_lines.append(_clean_ocr_text(best_text))
                self.progress_changed.emit(55 + int(((i + 1) / total) * 45))
            if len(final_lines) != len(self.recs):
                raise ValueError(
                    self._tr("ai_err_final_merge_count", len(final_lines), len(self.recs))
                )
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_ai_cancelled"))
            self.status_changed.emit(self._tr("ai_status_done", os.path.basename(self.path)))
            self.progress_changed.emit(100)
            self.finished_revision.emit(self.path, final_lines)
        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode("utf-8", errors="replace")
            except Exception:
                body = str(e)
            self.failed_revision.emit(self.path, self._tr("err_http_with_body", e, body))
        except urllib.error.URLError as e:
            self.failed_revision.emit(self.path, self._tr("ai_err_server_unreachable", e))
        except socket.timeout:
            self.failed_revision.emit(self.path, self._tr("ai_err_timeout"))
        except Exception as e:
            msg = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            self.failed_revision.emit(self.path, msg)
