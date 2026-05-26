"""Zusatzmodul: Ditto-Zeichen, Tabellen-/Datenexporte, Overlay-Box-Hilfen und UI-Fixes.

Der Patch ist bewusst defensiv: Er hängt sich nur an vorhandene Methoden, wenn sie in der
jeweiligen Bottled-Kraken-Version existieren. Dadurch bleibt die Datei auch mit älteren
Zwischenständen lauffähig.
"""

from .shared import *
from .ui_components import *
from .workers import *
from .dialogs import *
from .image_edit import *
from .main_window import MainWindow

def _bk_fix42_normalize_lm_box_lines(payload) -> List[Dict[str, Any]]:
    lines = _bk_fix41_extract_lm_page_items(payload)
    clean: List[Dict[str, Any]] = []
    for line in lines:
        txt = _bk_fix36_clean_text(line.get("text", ""))
        if not txt or _bk_fix41_is_json_debris_text(txt):
            continue
        # harte Abwehr gegen versehentlich serialisierte dicts/listen als Text
        if txt.startswith("{") or txt.startswith("[") or "'bbox_norm'" in txt or "\"bbox_norm\"" in txt:
            nested = _bk_fix41_extract_lm_page_items(txt)
            if nested and not (len(nested) == 1 and _bk_fix36_clean_text(nested[0].get("text", "")) == txt):
                clean.extend(nested)
            continue
        clean.append({
            "idx": len(clean),
            "text": txt,
            "bbox": line.get("bbox"),
            "bbox_norm": line.get("bbox_norm"),
        })
    return clean

def _bk_fix42_is_ditto_token_text(text: str) -> bool:
    return bool(re.fullmatch(r"\s*(?:[-–—]\s*)?[\"„“”]{1,4}(?:\s*[-–—])?\s*", str(text or "")))

def _bk_fix42_prev_segment_at_char(prev: str, pos: int) -> str:
    s = str(prev or "")
    if not s.strip():
        return ""
    # Prefer a token/span that covers the same character position.
    spans = list(re.finditer(r"\S+(?:\s+\S+){0,2}", s))
    best = ""
    best_dist = 10**9
    for m in re.finditer(r"\S+", s):
        if m.start() <= pos <= m.end():
            return m.group(0).strip(" ,;:")
        dist = min(abs(pos - m.start()), abs(pos - m.end()))
        if dist < best_dist:
            best_dist = dist
            best = m.group(0)
    return best.strip(" ,;:")

def _bk_fix42_resolve_line_ditto_from_prev(prev_line: str, cur_line: str) -> str:
    line = str(cur_line or "")
    if not line.strip() or '"' not in line and "„" not in line and "“" not in line and "”" not in line:
        return line

    # Match only real quotation marks, optionally surrounded by hyphens/dashes.
    quote_re = re.compile(r"(?<![A-Za-zÀ-ÿÄÖÜäöüß0-9.])(?:[-–—]\s*)?[\"„“”]{1,4}(?:\s*[-–—])?(?![A-Za-zÀ-ÿÄÖÜäöüß0-9.])")

    def repl(match):
        before = line[:match.start()]
        after = line[match.end():]
        # If a place/name follows after the quote, this is often a repeated date/year column.
        if re.match(r"\s*[A-ZÄÖÜ][A-Za-zÄÖÜäöüß]", after):
            year = _bk_fix41_extract_prev_year(prev_line)
            if year:
                return year
        # If a trailing number follows or a date stands before the quote, this is often place/residence.
        if re.match(r"\s*\d{1,4}\b", after) or re.search(r"\d{1,2}\.[IVXLCDM0-9]+\.?\s*$", before, flags=re.IGNORECASE):
            place = _bk_fix41_extract_prev_place(prev_line)
            if place:
                return place
        return _bk_fix42_prev_segment_at_char(prev_line, match.start())

    line = quote_re.sub(repl, line)
    line = re.sub(r"\s{2,}", " ", line).strip()
    line = re.sub(r"\s+([.,;:])", r"\1", line)
    return line

def _bk_fix42_resolve_ditto_marks_with_recs(recs, texts: List[str]) -> List[str]:
    texts = [str(x or "") for x in (texts or [])]
    if not texts:
        return []
    if recs:
        try:
            tmp = []
            for i, txt in enumerate(texts):
                rv = recs[i] if i < len(recs) else None
                bbox = getattr(rv, "bbox", None) if rv is not None else None
                tmp.append(RecordView(i, txt, bbox))
            tmp = _bk_fix42_resolve_ditto_marks_in_recs(tmp)
            return [getattr(rv, "text", "") for rv in tmp]
        except Exception:
            pass
    out = []
    prev = ""
    for line in texts:
        resolved = _bk_fix42_resolve_line_ditto_from_prev(prev, line)
        out.append(resolved)
        if _bk_fix36_clean_text(resolved):
            prev = resolved
    return out

def _bk_fix42_resolve_ditto_marks_in_recs(recs):
    try:
        recs = list(recs or [])
        if not recs:
            return recs
        if not any(getattr(rv, "bbox", None) for rv in recs):
            texts = _bk_fix42_resolve_ditto_marks_with_recs(None, [getattr(rv, "text", "") for rv in recs])
            for rv, text in zip(recs, texts):
                rv.text = text
            return recs

        rows = _bk_fix36_group_recs_into_table_rows(recs)
        prev_row = []
        for row in rows:
            row = sorted(row, key=lambda r: r.bbox[0] if getattr(r, "bbox", None) else 0)
            prev_line_text = " ".join(_bk_fix36_clean_text(getattr(r, "text", "")) for r in prev_row if _bk_fix36_clean_text(getattr(r, "text", "")))
            for rv in row:
                txt = str(getattr(rv, "text", "") or "")
                if not txt:
                    continue
                if _bk_fix42_is_ditto_token_text(txt) and prev_row and getattr(rv, "bbox", None):
                    cx = (rv.bbox[0] + rv.bbox[2]) / 2.0
                    candidates = [p for p in prev_row if getattr(p, "bbox", None) and _bk_fix36_clean_text(getattr(p, "text", ""))]
                    if candidates:
                        best = min(candidates, key=lambda p: abs(((p.bbox[0] + p.bbox[2]) / 2.0) - cx))
                        rv.text = str(getattr(best, "text", "") or "")
                    continue
                rv.text = _bk_fix42_resolve_line_ditto_from_prev(prev_line_text, txt)
            if row:
                prev_row = [x for x in row if _bk_fix36_clean_text(getattr(x, "text", ""))]
    except Exception:
        pass
    return recs

_bk_fix41_resolve_ditto_marks_in_lines = lambda lines: _bk_fix42_resolve_ditto_marks_with_recs(None, list(lines or []))

_bk_fix40_resolve_ditto_marks_in_lines = _bk_fix41_resolve_ditto_marks_in_lines

_bk_fix36_resolve_ditto_marks_in_lines = _bk_fix41_resolve_ditto_marks_in_lines

_bk_fix37_resolve_ditto_marks_in_lines = _bk_fix41_resolve_ditto_marks_in_lines

_bk_fix41_resolve_ditto_marks_in_recs = _bk_fix42_resolve_ditto_marks_in_recs

_bk_fix40_resolve_ditto_marks_in_recs = _bk_fix42_resolve_ditto_marks_in_recs

_bk_fix36_resolve_ditto_marks_in_recs = _bk_fix42_resolve_ditto_marks_in_recs

_bk_fix37_expand_ditto_text = lambda text: "\n".join(_bk_fix42_resolve_ditto_marks_with_recs(None, str(text or "").splitlines()))

_bk_fix38_expand_ditto_text = _bk_fix37_expand_ditto_text

try:
    _BK_FIX42_PREV_APPLY_QUEUE_BATCH_RESULT = _bk_lm_apply_queue_batch_result
except Exception:
    _BK_FIX42_PREV_APPLY_QUEUE_BATCH_RESULT = None

def _bk_lm_apply_queue_batch_result(self, path: str, mode: str, target_rows: List[int], revised_lines: List[Any]):
    if mode in (_BK_LM_BATCH_MODE_LM_OCR, _BK_LM_BATCH_MODE_LM_OCR_BOXES):
        parsed = _bk_fix42_normalize_lm_box_lines(revised_lines)
        revised_lines = [x.get("text", "") for x in parsed]
        revised_lines = [x for x in _bk_fix42_resolve_ditto_marks_with_recs(None, revised_lines) if _bk_fix36_clean_text(x)]
    if callable(_BK_FIX42_PREV_APPLY_QUEUE_BATCH_RESULT):
        return _BK_FIX42_PREV_APPLY_QUEUE_BATCH_RESULT(self, path, mode, target_rows, revised_lines)
    return None

try:
    _BK_FIX42_PREV_BLOCK_REREAD = AIRevisionWorker._request_block_reread
except Exception:
    _BK_FIX42_PREV_BLOCK_REREAD = None

def _bk_fix42_request_block_reread(self, block_data_url: str, start_idx: int, end_idx: int, current_lines: List[str]) -> List[str]:
    count = end_idx - start_idx
    system_prompt = self._tr("ai_prompt_block_system")
    page_context_lines = getattr(self, "_bk_fix42_page_context_lines", None) or []
    context_slice = []
    try:
        lo = max(0, start_idx - 2)
        hi = min(len(page_context_lines), end_idx + 2)
        context_slice = [f"{i}: {page_context_lines[i]}" for i in range(lo, hi) if _bk_fix36_clean_text(page_context_lines[i])]
    except Exception:
        context_slice = []
    joined_hint = "\n".join(f"{i}: {txt}" for i, txt in enumerate(current_lines))
    user_prompt = self._tr("ai_prompt_block_user", count, joined_hint)
    if context_slice:
        user_prompt += "\n\n" + self._tr("ai_prompt_block_page_context_header") + "\n" + "\n".join(context_slice)
        user_prompt += "\n\n" + self._tr("ai_prompt_block_weighting_hint")
    payload = {
        "model": self.lm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": block_data_url}},
            ]},
        ],
        **self._build_sampling_payload(response_format=self._response_format_lines(), override_max_tokens=self._effective_revision_max_tokens("block", count)),
    }
    data = self._post_json(payload)
    content = self._extract_message_content(data)
    obj = _extract_json_payload(content)
    if not isinstance(obj, dict):
        raise ValueError(self._tr("ai_err_block_invalid_json", content[:3000] if content else "<leer>"))
    lines = obj.get("lines")
    if not isinstance(lines, list):
        raise ValueError(self._tr("ai_err_block_invalid_lines", content[:3000] if content else "<leer>"))
    out = [""] * count
    for item in lines:
        if not isinstance(item, dict):
            continue
        idx = item.get("idx")
        txt = _force_text(item.get("text", "")).strip()
        if isinstance(idx, int) and 0 <= idx < count:
            out[idx] = txt
    fixed = []
    for i in range(count):
        txt = out[i].strip()
        fallback = current_lines[i] if i < len(current_lines) else ""
        fixed.append(txt if txt else fallback)
    return fixed

try:
    AIRevisionWorker._request_block_reread = _bk_fix42_request_block_reread
except Exception:
    pass

try:
    _BK_FIX42_PREV_AI_RUN = AIRevisionWorker.run
except Exception:
    _BK_FIX42_PREV_AI_RUN = None

def _bk_fix42_ai_revision_run(self):
    if isinstance(self, BKFullPageLMOCRWorker):
        if callable(_BK_FIX42_PREV_AI_RUN):
            return _BK_FIX42_PREV_AI_RUN(self)
    if self._cancelled or self.isInterruptionRequested():
        self.failed_revision.emit(self.path, self._tr('msg_ai_cancelled'))
        return
    try:
        if not self.recs:
            self.finished_revision.emit(self.path, [])
            return
        total = max(1, len(self.recs))
        crop_profile = _ai_script_crop_profile(self.script_mode)
        original_lines = [rv.text for rv in self.recs]

        # 1) Full page OCR as context for current line, selected lines and all lines.
        self.status_changed.emit(self._tr('ai_status_step0_fullpage_context', os.path.basename(self.path)))
        self.progress_changed.emit(0)
        page_lines = list(original_lines)
        try:
            page_data_url = _page_to_data_url(self.path)
            page_guess = self._request_page_ocr_with_fixed_linecount(page_data_url, self.recs)
            if isinstance(page_guess, list) and page_guess:
                for i, txt in enumerate(page_guess[:len(page_lines)]):
                    txt = _clean_ocr_text(txt)
                    if txt:
                        page_lines[i] = txt
        except Exception as e:
            print(f'FULL PAGE CONTEXT OCR ERROR: {e}')
        self._bk_fix42_page_context_lines = page_lines

        # 2) Send exactly 3 overlay boxes at a time, with page context in the text prompt.
        self.status_changed.emit(self._tr('ai_status_step2_plain', os.path.basename(self.path)))
        box_lines = [''] * len(self.recs)
        chunks = self._chunk_records(self.recs, block_size=3)
        for chunk_idx, (start, end) in enumerate(chunks, start=1):
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr('msg_ai_cancelled'))
            self.status_changed.emit(self._tr('ai_status_step2_chunk', chunk_idx, len(chunks), start + 1, end))
            try:
                block_data_url = _crop_block_to_data_url_context(
                    self.path, self.recs, start, end,
                    pad_x=crop_profile['block_pad_x'], pad_y=crop_profile['block_pad_y'],
                )
                reread = self._request_block_reread(block_data_url=block_data_url, start_idx=start, end_idx=end, current_lines=original_lines[start:end])
                if isinstance(reread, list):
                    for local_i, txt in enumerate(reread[:end-start]):
                        box_lines[start + local_i] = _clean_ocr_text(txt)
            except Exception as e:
                print(f'3-BOX OCR ERROR {start}-{end}: {e}')
            self.progress_changed.emit(int((chunk_idx / max(1, len(chunks))) * 70))

        # 3) Conservative merge: Kraken > page context > overlay-box reread.
        self.status_changed.emit(self._tr('ai_status_step3_merge', os.path.basename(self.path)))
        final_lines: List[str] = []
        for i, rv in enumerate(self.recs):
            kraken_text = str(original_lines[i] if i < len(original_lines) else '').strip()
            page_text = str(page_lines[i] if i < len(page_lines) else '').strip()
            box_text = str(box_lines[i] if i < len(box_lines) else '').strip()
            prev_final = final_lines[i - 1] if i > 0 else ''
            if (not kraken_text) or self._is_suspicious_box_result(kraken_text):
                try:
                    decision = self._request_line_decision(i, kraken_text, page_text, box_text).strip()
                except Exception:
                    decision = ''
                best = decision or _bk_fix41_choose_final_kraken_first(self, kraken_text, page_text, box_text, prev_final)
            else:
                best = _bk_fix41_choose_final_kraken_first(self, kraken_text, page_text, box_text, prev_final)
            final_lines.append(best)
            self.progress_changed.emit(70 + int(((i + 1) / total) * 30))
        final_lines = _bk_fix42_resolve_ditto_marks_with_recs(self.recs, final_lines)
        if len(final_lines) != len(self.recs):
            raise ValueError(self._tr('ai_err_final_merge_count', len(final_lines), len(self.recs)))
        self.status_changed.emit(self._tr('ai_status_done', os.path.basename(self.path)))
        self.progress_changed.emit(100)
        self.finished_revision.emit(self.path, final_lines)
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode('utf-8', errors='replace')
        except Exception:
            body = str(e)
        self.failed_revision.emit(self.path, self._tr('err_http_with_body', e, body))
    except urllib.error.URLError as e:
        self.failed_revision.emit(self.path, self._tr('ai_err_server_unreachable', e))
    except socket.timeout:
        self.failed_revision.emit(self.path, self._tr('ai_err_timeout'))
    except Exception as e:
        self.failed_revision.emit(self.path, ''.join(traceback.format_exception(type(e), e, e.__traceback__)))

try:
    AIRevisionWorker.run = _bk_fix42_ai_revision_run
except Exception:
    pass
