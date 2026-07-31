from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
from bottled_kraken.common import _crop_overlay_box_to_data_url_strict
class BKFullPageLMOCRWithBoxesWorker(BKFullPageLMOCRWorker):
    def _safe_page_line_for_idx(self, page_lines: List[str], idx: int) -> str:
        if 0 <= int(idx) < len(page_lines):
            return _clean_ocr_text(page_lines[int(idx)])
        return ""
    def _response_format_box_aligned_lines(self) -> dict:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "lm_page_ocr_box_aligned_lines",
                "schema": {
                    "type": "object",
                    "properties": {
                        "lines": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "idx": {"type": "integer"},
                                    "text": {"type": "string"},
                                },
                                "required": ["idx", "text"],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "required": ["lines"],
                    "additionalProperties": False,
                },
            },
        }
    def _fallback_merge_line(self, kraken_text: str, page_text: str, box_text: str, prev_final: str = "") -> str:
        page_text = _clean_ocr_text(page_text or "")
        box_text = _clean_ocr_text(box_text or "")
        kraken_text = _clean_ocr_text(kraken_text or "")
        return page_text or box_text or kraken_text
    def _read_overlay_boxes(self) -> List[str]:
        box_lines: List[str] = []
        total = max(1, len(self.recs))
        try:
            crop_profile = _ai_script_crop_profile(getattr(self, "script_mode", AI_SCRIPT_PRINT))
        except Exception:
            crop_profile = {
                "single_pad_x": 20,
                "single_pad_y": 8,
                "single_extra_context_y": 0,
            }
        for i, rv in enumerate(self.recs):
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_ai_cancelled"))
            self.status_changed.emit(
                self._tr(
                    "ai_status_page_boxes_box_scan",
                    i + 1,
                    total,
                    os.path.basename(self.path),
                )
            )
            box_text = ""
            if getattr(rv, "bbox", None):
                try:
                    line_data_url = _crop_overlay_box_to_data_url_strict(
                        self.path,
                        rv,
                        pad_x=crop_profile.get("single_pad_x", 20),
                        pad_y=crop_profile.get("single_pad_y", 8),
                        extra_context_y=crop_profile.get("single_extra_context_y", 0),
                    )
                    self._bk_strict_overlay_transcription_active = True
                    self._bk_active_overlay_crop_data_url = line_data_url
                    try:
                        box_text = self._request_single_line_reread(
                            line_data_url=line_data_url,
                            idx=getattr(rv, "idx", i),
                            current_text=getattr(rv, "text", "") or "",
                        )
                    finally:
                        self._bk_active_overlay_crop_data_url = None
                except Exception as exc:
                    try:
                        print(f"LM PAGE+BOXES BOX OCR ERROR idx={getattr(rv, 'idx', i)}: {exc}")
                    except Exception:
                        pass
                    box_text = getattr(rv, "text", "") or ""
            if not _clean_ocr_text(box_text):
                box_text = getattr(rv, "text", "") or ""
            box_lines.append(_clean_ocr_text(box_text))
            self.progress_changed.emit(35 + int(((i + 1) / total) * 35))
        return box_lines
    def _deterministic_align_page_lines_to_boxes(self, page_lines: List[str], box_lines: List[str]) -> List[str]:
        page_lines = [_clean_ocr_text(x) for x in (page_lines or [])]
        page_lines = [x for x in page_lines if x]
        out: List[str] = []
        used = set()
        n = len(self.recs)
        for i, rv in enumerate(self.recs):
            kraken_text = _clean_ocr_text(getattr(rv, "text", "") or "")
            box_text = _clean_ocr_text(box_lines[i] if i < len(box_lines) else "")
            anchor = box_text or kraken_text
            best_idx = None
            best_score = -1.0
            for j, candidate in enumerate(page_lines):
                if j in used:
                    continue
                if anchor:
                    score = max(
                        self._text_similarity_ratio(anchor, candidate),
                        self._token_overlap_ratio(anchor, candidate),
                    )
                else:
                    score = 0.25
                score += max(0.0, 0.20 - (abs(j - i) * 0.025))
                if j == i:
                    score += 0.08
                if score > best_score:
                    best_score = score
                    best_idx = j
            if best_idx is not None and (best_score > 0.05 or not anchor):
                used.add(best_idx)
                out.append(_clean_ocr_text(page_lines[best_idx]))
            elif i < len(page_lines):
                out.append(_clean_ocr_text(page_lines[i]))
            else:
                out.append(self._fallback_merge_line(kraken_text, "", box_text, out[-1] if out else ""))
        if len(out) < n:
            out.extend([""] * (n - len(out)))
        return out[:n]
    def _request_page_box_alignment(self, page_lines: List[str], box_lines: List[str]) -> List[str]:
        n = len(self.recs)
        fallback = self._deterministic_align_page_lines_to_boxes(page_lines, box_lines)
        box_specs = []
        for i, rv in enumerate(self.recs):
            box_specs.append({
                "idx": i,
                "existing_text": _clean_ocr_text(getattr(rv, "text", "") or ""),
                "box_ocr_text": _clean_ocr_text(box_lines[i] if i < len(box_lines) else ""),
            })
        system_prompt = self._tr("ai_prompt_page_boxes_align_system")
        user_prompt = self._tr(
            "ai_prompt_page_boxes_align_user",
            n,
            max(0, n - 1),
            json.dumps([_clean_ocr_text(x) for x in (page_lines or []) if _clean_ocr_text(x)], ensure_ascii=False, indent=2),
            json.dumps(box_specs, ensure_ascii=False, indent=2),
        )
        alignment_max_tokens = max(1, int(getattr(self, "max_tokens", 4500) or 4500))
        payload = {
            "model": self.lm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            **self._build_sampling_payload(
                response_format=self._response_format_box_aligned_lines(),
                override_max_tokens=alignment_max_tokens,
            ),
        }
        try:
            data = self._post_json(payload)
            content = self._extract_message_content(data)
            try:
                print("RAW PAGE+BOX ALIGNMENT RESPONSE:")
                print(content[:4000])
            except Exception:
                pass
            obj = _extract_json_payload(content)
            if not isinstance(obj, dict):
                return fallback
            lines = obj.get("lines")
            if not isinstance(lines, list):
                return fallback
            out = [""] * n
            for item in lines:
                if not isinstance(item, dict):
                    continue
                idx = item.get("idx")
                try:
                    idx = int(idx)
                except Exception:
                    continue
                if 0 <= idx < n:
                    out[idx] = _clean_ocr_text(_force_text(item.get("text", "")))
            for i in range(n):
                if not out[i]:
                    out[i] = fallback[i] if i < len(fallback) else ""
            return out[:n]
        except Exception as exc:
            try:
                print(f"LM PAGE+BOXES ALIGNMENT ERROR: {exc}")
            except Exception:
                pass
            return fallback
    def _merge_page_and_boxes(self, page_lines: List[str], box_lines: List[str]) -> List[str]:
        self.status_changed.emit(self._tr("ai_status_page_boxes_merge", os.path.basename(self.path)))
        final_lines = self._request_page_box_alignment(page_lines, box_lines)
        final_lines = [_clean_ocr_text(x) for x in (final_lines or [])]
        n = len(self.recs)
        if len(final_lines) < n:
            final_lines.extend([""] * (n - len(final_lines)))
        elif len(final_lines) > n:
            final_lines = final_lines[:n]
        for i, rv in enumerate(self.recs):
            if not final_lines[i]:
                final_lines[i] = _clean_ocr_text(
                    self._fallback_merge_line(
                        getattr(rv, "text", "") or "",
                        self._safe_page_line_for_idx(page_lines, i),
                        box_lines[i] if i < len(box_lines) else "",
                        final_lines[i - 1] if i > 0 else "",
                    )
                )
            self.progress_changed.emit(70 + int(((i + 1) / max(1, n)) * 25))
        return final_lines[:n]
    def run(self):
        if self._cancelled or self.isInterruptionRequested():
            self.failed_revision.emit(self.path, self._tr("msg_ai_cancelled"))
            return
        try:
            if not self.recs:
                raise ValueError(self._tr("warn_need_overlay_boxes_for_lm_ocr_boxes"))
            if not any(getattr(rv, "bbox", None) for rv in self.recs):
                raise ValueError(self._tr("warn_need_overlay_boxes_for_lm_ocr_boxes"))
            self.status_changed.emit(self._tr("ai_status_page_boxes_scan", os.path.basename(self.path)))
            self.progress_changed.emit(3)
            self._bk_strict_overlay_transcription_active = True
            self._bk_active_overlay_crop_data_url = None
            page_data_url = _page_to_data_url(self.path)
            self._bk_full_page_context_image_url = page_data_url
            self.progress_changed.emit(10)
            self._bk_full_page_context_request_active = True
            try:
                page_lines = self._request_full_page_ocr(page_data_url)
            finally:
                self._bk_full_page_context_request_active = False
            page_lines = [_clean_ocr_text(x) for x in (page_lines or []) if _clean_ocr_text(x)]
            if not page_lines:
                raise ValueError(self._tr("ai_err_page_no_usable_lines", 0, 0))
            self.progress_changed.emit(35)
            box_lines = self._read_overlay_boxes()
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_ai_cancelled"))
            final_lines = self._merge_page_and_boxes(page_lines, box_lines)
            final_lines = [_clean_ocr_text(x) for x in (final_lines or [])]
            if len(final_lines) < len(self.recs):
                final_lines.extend([""] * (len(self.recs) - len(final_lines)))
            elif len(final_lines) > len(self.recs):
                final_lines = final_lines[:len(self.recs)]
            if not any(_clean_ocr_text(x) for x in final_lines):
                raise ValueError(self._tr("ai_err_page_no_usable_lines", 0, len(self.recs)))
            self.status_changed.emit(self._tr("ai_status_page_boxes_done", os.path.basename(self.path)))
            self.progress_changed.emit(100)
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
__all__ = [
    'BKFullPageLMOCRWithBoxesWorker',
]
register_globals('bk', globals(), __all__)
