from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
from bottled_kraken.common import _ai_script_crop_profile, _clean_ocr_text, _crop_block_to_data_url_context, _load_image_color, _page_to_data_url
from bottled_kraken.common import Any, Dict, List, Optional, TaskItem, json, os, re, socket, traceback, urllib
from bottled_kraken.workers import AIRevisionWorker
from bottled_kraken.main_window import MainWindow
import ast as _bk_fix41_ast
def _bk_fix41_normalize_text_value(value) -> str:
    txt = str(value or '').replace('\\n', '\n').replace('\r\n', '\n').replace('\r', '\n').strip()
    txt = re.sub(r"^\s*['\"]?(?:text|line|transcription|ocr_text)['\"]?\s*:\s*", "", txt, flags=re.IGNORECASE).strip()
    txt = txt.strip().strip(',')
    if txt.startswith(('"', "'")) and txt.endswith(('"', "'")) and len(txt) >= 2:
        txt = txt[1:-1]
    return _bk_fix36_clean_text(txt)
def _bk_fix41_is_json_debris_text(txt: str) -> bool:
    s = str(txt or '').strip().strip(',')
    if not s:
        return True
    if re.fullmatch(r'[\{\}\[\],]+', s):
        return True
    if re.fullmatch(r'-?\d+(?:\.\d+)?', s):
        return True
    if re.match(r"^['\"]?(?:lines|rows|entries|items|idx|bbox|bbox_norm|box|textbbox_norm|textbox_norm)['\"]?\s*:?(?:\s*[\[\{,]?)?$", s, flags=re.IGNORECASE):
        return True
    if re.match(r"^['\"]?(?:bbox|bbox_norm|box|textbbox_norm|textbox_norm)['\"]?\s*:", s, flags=re.IGNORECASE):
        return True
    if s in {'None', 'null', 'True', 'False'}:
        return True
    return False
def _bk_fix41_try_parse_obj(raw):
    if isinstance(raw, (dict, list)):
        return raw
    s = _bk_fix40_strip_code_fences(str(raw or '').strip())
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        pass
    try:
        return _bk_fix41_ast.literal_eval(s)
    except Exception:
        pass
    start, end = s.find('{'), s.rfind('}')
    if start >= 0 and end > start:
        frag = s[start:end + 1]
        try:
            return json.loads(frag)
        except Exception:
            try:
                return _bk_fix41_ast.literal_eval(frag)
            except Exception:
                pass
    return None
def _bk_fix41_item_to_line(item, idx: int = 0):
    if isinstance(item, dict):
        text = item.get('text') or item.get('line') or item.get('transcription') or item.get('ocr_text') or ''
        text = _bk_fix41_normalize_text_value(text)
        if _bk_fix41_is_json_debris_text(text):
            return None
        bbox = item.get('bbox') or item.get('box')
        bbox_norm = item.get('bbox_norm') or item.get('normalized_bbox') or item.get('bbox_normalized') or item.get('textbox_norm') or item.get('textbbox_norm')
        return {'idx': int(item.get('idx', idx) or idx), 'text': text, 'bbox': bbox, 'bbox_norm': bbox_norm}
    text = _bk_fix41_normalize_text_value(item)
    if _bk_fix41_is_json_debris_text(text):
        return None
    return {'idx': idx, 'text': text, 'bbox': None, 'bbox_norm': None}
def _bk_fix41_extract_lm_page_items(payload) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    def add(obj):
        if obj is None:
            return
        if isinstance(obj, dict):
            if any(k in obj for k in ('lines', 'rows', 'entries', 'items')):
                data = obj.get('lines') or obj.get('rows') or obj.get('entries') or obj.get('items') or []
                add(data)
            else:
                line = _bk_fix41_item_to_line(obj, len(items))
                if line:
                    items.append(line)
        elif isinstance(obj, list):
            for element in obj:
                add(element)
        else:
            line = _bk_fix41_item_to_line(obj, len(items))
            if line:
                items.append(line)
    if isinstance(payload, (dict, list)):
        add(payload)
    else:
        raw = str(payload or '')
        obj = _bk_fix41_try_parse_obj(raw)
        if obj is not None:
            add(obj)
        else:
            for block in re.findall(r"\{[^{}]*(?:\[[^\]]*\][^{}]*)?\}", raw, flags=re.DOTALL):
                obj2 = _bk_fix41_try_parse_obj(block)
                if obj2 is not None:
                    add(obj2)
            if not items:
                for ln in raw.splitlines():
                    line = _bk_fix41_normalize_text_value(ln)
                    if not _bk_fix41_is_json_debris_text(line):
                        add(line)
    out: List[Dict[str, Any]] = []
    for item in items:
        text = str(item.get('text') or '').replace('\r\n', '\n').replace('\r', '\n')
        parts = [_bk_fix36_clean_text(p) for p in text.split('\n') if _bk_fix36_clean_text(p)]
        if not parts:
            continue
        bbox = item.get('bbox')
        bbox_norm = item.get('bbox_norm')
        if len(parts) == 1:
            out.append({'idx': len(out), 'text': parts[0], 'bbox': bbox, 'bbox_norm': bbox_norm})
            continue
        for j, part in enumerate(parts):
            nb, nbn = bbox, bbox_norm
            if isinstance(bbox_norm, (list, tuple)) and len(bbox_norm) >= 4:
                try:
                    x0, y0, x1, y1 = [float(v) for v in bbox_norm[:4]]
                    step = (y1 - y0) / max(1, len(parts))
                    nbn = [x0, y0 + j * step, x1, y0 + (j + 1) * step]
                    nb = None
                except Exception:
                    pass
            elif isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
                try:
                    x0, y0, x1, y1 = [float(v) for v in bbox[:4]]
                    step = (y1 - y0) / max(1, len(parts))
                    nb = [x0, y0 + j * step, x1, y0 + (j + 1) * step]
                    nbn = None
                except Exception:
                    pass
            out.append({'idx': len(out), 'text': part, 'bbox': nb, 'bbox_norm': nbn})
    return out
def _bk_fix40_extract_jsonish_lines(payload) -> List[Dict[str, Any]]:
    return _bk_fix41_extract_lm_page_items(payload)
def _bk_fix40_clean_lm_page_text_lines(payload) -> List[str]:
    lines = [_bk_fix36_clean_text(x.get('text', '')) for x in _bk_fix41_extract_lm_page_items(payload)]
    lines = [x for x in lines if x and not _bk_fix41_is_json_debris_text(x)]
    return _bk_fix41_resolve_ditto_marks_in_lines(lines)
def _bk_fix41_extract_prev_year(prev: str) -> str:
    years = re.findall(r'\b(1[5-9]\d{2}|20\d{2})\b', str(prev or ''))
    return years[-1] if years else ''
def _bk_fix41_extract_prev_place(prev: str) -> str:
    s = str(prev or '')
    m = re.search(r'(?:1[5-9]\d{2}|20\d{2})\s*[.,;:]?\s*([^\d]{2,50}?)(?:\s*\d{1,4}\s*[.,;:]?\s*)?$', s)
    if m:
        cand = re.sub(r'["„“”]', '', m.group(1)).strip(' .,;:-')
        if re.search(r'[A-Za-zÄÖÜäöüß]', cand):
            return cand
    s = re.sub(r'\s+\d{1,4}\s*[.,;:]?\s*$', '', s)
    cands = re.findall(r'\b([A-ZÄÖÜ][A-Za-zÄÖÜäöüß.\-]{2,}(?:\s+[A-ZÄÖÜ][A-Za-zÄÖÜäöüß.\-]{2,})?)\b', s)
    return cands[-1].strip(' .,;:-') if cands else ''
def _bk_fix41_resolve_ditto_marks_in_lines(lines: List[str]) -> List[str]:
    out: List[str] = []
    prev_line = ''
    quote_re = re.compile(r'(?<![A-Za-zÀ-ÿÄÖÜäöüß0-9.])(?:[-–—]\s*)?["„“”]{1,4}(?:\s*[-–—])?(?![A-Za-zÀ-ÿÄÖÜäöüß0-9.])')
    attached_re = re.compile(r'(?<![A-Za-zÀ-ÿÄÖÜäöüß0-9.])(?:[-–—]\s*)?["„“”]{1,4}(?:\s*[-–—])?(?=[A-Za-zÀ-ÿÄÖÜäöüß])')
    for raw in lines or []:
        line = str(raw or '')
        if not line.strip():
            out.append(line)
            continue
        def repl_attached(match):
            after = line[match.end():]
            year = _bk_fix41_extract_prev_year(prev_line)
            return (year + ' ') if year else ''
        line2 = attached_re.sub(repl_attached, line)
        def repl(match):
            after = line2[match.end():]
            before = line2[:match.start()]
            if re.match(r'\s*[A-ZÄÖÜ][A-Za-zÄÖÜäöüß]', after):
                v = _bk_fix41_extract_prev_year(prev_line)
                if v:
                    return v
            if re.match(r'\s*\d{1,4}\b', after) or re.search(r'\b\d{1,2}\.[IVXLCDM0-9]+\.\s*(?:1[5-9]\d{2}|20\d{2})?\s*$', before, flags=re.IGNORECASE):
                v = _bk_fix41_extract_prev_place(prev_line)
                if v:
                    return v
            return _bk_fix37_prev_word_at_column(prev_line, match.start()) or ''
        line2 = quote_re.sub(repl, line2)
        line2 = re.sub(r'\s{2,}', ' ', line2).strip()
        line2 = re.sub(r'\s+([.,;:])', r'\1', line2)
        out.append(line2)
        if line2:
            prev_line = line2
    return out
def _bk_fix41_resolve_ditto_marks_in_recs(recs):
    try:
        recs = list(recs or [])
        if not recs:
            return recs
        with_boxes = [rv for rv in recs if getattr(rv, 'bbox', None)]
        if not with_boxes:
            texts = _bk_fix41_resolve_ditto_marks_in_lines([getattr(rv, 'text', '') for rv in recs])
            for rv, txt in zip(recs, texts):
                rv.text = txt
            return recs
        rows = _bk_fix36_group_recs_into_table_rows(recs)
        prev_row = []
        for row in rows:
            row = sorted(row, key=lambda r: r.bbox[0] if getattr(r, 'bbox', None) else 0)
            for rv in row:
                txt = str(getattr(rv, 'text', '') or '')
                if not txt:
                    continue
                if re.fullmatch(r'\s*(?:[-–—]\s*)?["„“”]{1,4}(?:\s*[-–—])?\s*', txt):
                    if prev_row and getattr(rv, 'bbox', None):
                        cx = (rv.bbox[0] + rv.bbox[2]) / 2.0
                        candidates = [p for p in prev_row if getattr(p, 'bbox', None) and _bk_fix36_clean_text(getattr(p, 'text', ''))]
                        if candidates:
                            best = min(candidates, key=lambda p: abs(((p.bbox[0] + p.bbox[2]) / 2.0) - cx))
                            rv.text = str(getattr(best, 'text', '') or '')
                    continue
                rv.text = _bk_fix41_resolve_ditto_marks_in_lines([txt])[0]
            if row:
                prev_row = [x for x in row if _bk_fix36_clean_text(getattr(x, 'text', ''))]
    except Exception:
        pass
    return recs
_bk_fix40_resolve_ditto_marks_in_lines = _bk_fix41_resolve_ditto_marks_in_lines
_bk_fix36_resolve_ditto_marks_in_lines = _bk_fix41_resolve_ditto_marks_in_lines
_bk_fix37_resolve_ditto_marks_in_lines = _bk_fix41_resolve_ditto_marks_in_lines
_bk_fix38_resolve_ditto_marks_in_lines = _bk_fix41_resolve_ditto_marks_in_lines
_bk_fix40_resolve_ditto_marks_in_recs = _bk_fix41_resolve_ditto_marks_in_recs
_bk_fix36_resolve_ditto_marks_in_recs = _bk_fix41_resolve_ditto_marks_in_recs
_bk_fix37_expand_ditto_text = lambda text: '\n'.join(_bk_fix41_resolve_ditto_marks_in_lines(str(text or '').splitlines()))
_bk_fix38_expand_ditto_text = _bk_fix37_expand_ditto_text
try:
    _BK_FIX41_PREV_APPLY_BATCH_RESULT = _bk_lm_apply_queue_batch_result
except Exception:
    _BK_FIX41_PREV_APPLY_BATCH_RESULT = None
def _bk_lm_apply_queue_batch_result(self, path: str, mode: str, target_rows: List[int], revised_lines: List[Any]):
    if mode == _BK_LM_BATCH_MODE_LM_OCR:
        parsed = _bk_fix41_extract_lm_page_items(revised_lines)
        if parsed:
            revised_lines = [x.get('text', '') for x in parsed]
        else:
            clean: List[str] = []
            for x in revised_lines or []:
                clean.extend(_bk_fix40_clean_lm_page_text_lines(x))
            revised_lines = clean
        revised_lines = [x for x in _bk_fix41_resolve_ditto_marks_in_lines([str(v) for v in revised_lines]) if _bk_fix36_clean_text(x)]
    if callable(_BK_FIX41_PREV_APPLY_BATCH_RESULT):
        return _BK_FIX41_PREV_APPLY_BATCH_RESULT(self, path, mode, target_rows, revised_lines)
    return None
try:
    _BK_FIX41_PREV_RUN_QUEUE_BATCH = _bk_lm_run_queue_batch
except Exception:
    _BK_FIX41_PREV_RUN_QUEUE_BATCH = None
def _bk_lm_run_queue_batch(self, mode: str, row_indices: Optional[List[int]] = None, *, targets: Optional[List[TaskItem]] = None, allow_selected: bool = False, allow_all_if_empty: bool = False):
    result = False
    if callable(_BK_FIX41_PREV_RUN_QUEUE_BATCH):
        result = _BK_FIX41_PREV_RUN_QUEUE_BATCH(self, mode, row_indices, targets=targets, allow_selected=allow_selected, allow_all_if_empty=allow_all_if_empty)
    try:
        dlg = getattr(self, '_bk_lm_queue_batch_dialog', None)
        if dlg:
            if mode == _BK_LM_BATCH_MODE_LM_OCR:
                dlg.set_status(_bk_fix36_tr(self, 'dlg_ai_ocr_status', 'Es wird gerade ein kompletter Seiten-OCR mit einem lokalen Modell durchgeführt. Bitte warten.'))
            elif globals().get('_BK_LM_BATCH_MODE_LM_OCR_BOXES') is not None and mode == _BK_LM_BATCH_MODE_LM_OCR_BOXES:
                dlg.set_status(_bk_fix36_tr(self, 'ai_status_page_boxes_scan', 'LM Seiten OCR + Boxen wird vorbereitet: {}', os.path.basename(getattr((targets or [None])[0], 'path', '') if targets else '')))
            else:
                dlg.set_status(_bk_fix36_tr(self, 'lm_busy_revision_status', 'Das lokale Modell überarbeitet die Zeilen. Die Dauer hängt vom Modell und der Seitenkomplexität ab.'))
    except Exception:
        pass
    return result
try:
    _BK_FIX41_PREV_AI_RUN = AIRevisionWorker.run
except Exception:
    _BK_FIX41_PREV_AI_RUN = None
def _bk_fix41_choose_final_kraken_first(worker, kraken_text: str, page_text: str, box_text: str, prev_final_text: str = '') -> str:
    kt = _clean_ocr_text(kraken_text or '')
    pt = _clean_ocr_text(page_text or '')
    bt = _clean_ocr_text(box_text or '')
    if kt and not worker._looks_like_long_block(kt):
        best = kt
    elif pt and worker._page_text_is_safe_context(kraken_text=kt, box_text=bt, page_text=pt, prev_final_text=prev_final_text):
        best = pt
    else:
        best = bt or kt or pt
    if prev_final_text and best and worker._normalize_compare_text(best) == worker._normalize_compare_text(prev_final_text):
        for cand in (kt, pt, bt):
            if cand and worker._normalize_compare_text(cand) != worker._normalize_compare_text(prev_final_text):
                best = cand
                break
    return _clean_ocr_text(best)
def _bk_fix41_ai_revision_run(self):
    if isinstance(self, BKFullPageLMOCRWorker):
        if callable(_BK_FIX41_PREV_AI_RUN):
            return _BK_FIX41_PREV_AI_RUN(self)
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
                reread = self._request_block_reread(
                    block_data_url=block_data_url,
                    start_idx=start,
                    end_idx=end,
                    current_lines=original_lines[start:end],
                )
                if isinstance(reread, list):
                    for local_i, txt in enumerate(reread[:end-start]):
                        box_lines[start + local_i] = _clean_ocr_text(txt)
            except Exception as e:
                print(f'3-BOX OCR ERROR {start}-{end}: {e}')
            self.progress_changed.emit(int((chunk_idx / max(1, len(chunks))) * 70))
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
        final_lines = _bk_fix41_resolve_ditto_marks_in_lines(final_lines)
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
        self.failed_revision.emit(self.path, f'HTTP-Fehler: {e}\n{body}')
    except urllib.error.URLError as e:
        self.failed_revision.emit(self.path, self._tr('ai_err_server_unreachable', e))
    except socket.timeout:
        self.failed_revision.emit(self.path, self._tr('ai_err_timeout'))
    except Exception as e:
        self.failed_revision.emit(self.path, ''.join(traceback.format_exception(type(e), e, e.__traceback__)))
try:
    AIRevisionWorker.run = _bk_fix41_ai_revision_run
except Exception:
    pass
try:
    _BK_FIX41_PREV_RENDER_FILE = MainWindow._render_file
except Exception:
    _BK_FIX41_PREV_RENDER_FILE = None
def _bk_fix41_render_file(self, path: str, fmt: str, item: TaskItem):
    if not item.results:
        return
    text, kr_records, pil_image, record_views = item.results
    export_image = _load_image_color(item.path)
    fmt_l = str(fmt or '').lower()
    if fmt_l == 'txt':
        _bk_fix41_resolve_ditto_marks_in_recs(record_views)
        out_text = _bk_fix38_spatial_text_from_recs(record_views)
        if not _bk_fix36_clean_text(out_text):
            out_text = '\n'.join(_bk_fix36_clean_text(getattr(rv, 'text', '')) for rv in (record_views or []) if _bk_fix36_clean_text(getattr(rv, 'text', '')))
        with open(path, 'w', encoding='utf-8') as f:
            f.write(out_text.rstrip() + '\n')
        return
    if fmt_l == 'txt_boxes':
        return _bk_fix40_write_structured_txt_export(path, record_views, export_image.size)
    if fmt_l == 'docx':
        return _bk_fix40_write_docx_export(path, item, export_image, record_views)
    if callable(_BK_FIX41_PREV_RENDER_FILE):
        return _BK_FIX41_PREV_RENDER_FILE(self, path, fmt, item)
    return None
try:
    MainWindow._render_file = _bk_fix41_render_file
except Exception:
    pass
__all__ = [
    '_bk_fix36_resolve_ditto_marks_in_lines',
    '_bk_fix36_resolve_ditto_marks_in_recs',
    '_bk_fix37_expand_ditto_text',
    '_bk_fix37_resolve_ditto_marks_in_lines',
    '_bk_fix38_expand_ditto_text',
    '_bk_fix38_resolve_ditto_marks_in_lines',
    '_bk_fix40_clean_lm_page_text_lines',
    '_bk_fix40_extract_jsonish_lines',
    '_bk_fix40_resolve_ditto_marks_in_lines',
    '_bk_fix40_resolve_ditto_marks_in_recs',
    '_bk_fix41_ai_revision_run',
    '_bk_fix41_choose_final_kraken_first',
    '_bk_fix41_extract_lm_page_items',
    '_bk_fix41_extract_prev_place',
    '_bk_fix41_extract_prev_year',
    '_bk_fix41_is_json_debris_text',
    '_bk_fix41_item_to_line',
    '_bk_fix41_normalize_text_value',
    '_bk_fix41_render_file',
    '_bk_fix41_resolve_ditto_marks_in_lines',
    '_bk_fix41_resolve_ditto_marks_in_recs',
    '_bk_fix41_try_parse_obj',
    '_bk_lm_apply_queue_batch_result',
    '_bk_lm_run_queue_batch',
]
register_globals('bk', globals(), __all__)
