from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
from bottled_kraken.common import (
    Any,
    Dict,
    List,
    json,
    re,
)
from bottled_kraken.main_window import MainWindow
def _bk_fix40_strip_code_fences(raw: str) -> str:
    raw = str(raw or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE).strip()
        raw = re.sub(r"\s*```$", "", raw).strip()
    return raw
def _bk_fix40_extract_jsonish_lines(payload) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        data = payload
    elif isinstance(payload, dict):
        data = payload.get("lines") or payload.get("rows") or payload.get("entries") or payload.get("items") or []
    else:
        raw = _bk_fix40_strip_code_fences(str(payload or ""))
        data = None
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                data = parsed.get("lines") or parsed.get("rows") or parsed.get("entries") or parsed.get("items") or []
            elif isinstance(parsed, list):
                data = parsed
        except Exception:
            data = None
        if data is None:
            blocks = re.findall(r"\{[^{}]*(?:\[[^\]]*\][^{}]*)?\}", raw, flags=re.DOTALL)
            items = []
            if not blocks:
                blocks = [raw]
            for block in blocks:
                text_match = re.search(
                    r"""(?ix)
                    \b(?:text|line|transcription|ocr_text)\b\s*:\s*
                    (?:
                        "([^"]*)" |
                        '([^']*)' |
                        ([^\n\r,\]}]+)
                    )
                    """,
                    block,
                )
                if not text_match:
                    continue
                text = next((g for g in text_match.groups() if g is not None), "")
                text = str(text or "").strip().strip(",")
                if not text or text in {"{", "}", "[", "]"}:
                    continue
                bbox_vals = None
                bbox_match = re.search(
                    r"""(?ix)
                    \b(?:bbox_norm|normalized_bbox|bbox_normalized|bbox|box|textbox_norm|textbbox_norm)\w*\b
                    \s*:\s*\[([^\]]+)\]
                    """,
                    block,
                )
                if bbox_match:
                    nums = re.findall(r"-?\d+(?:\.\d+)?", bbox_match.group(1))
                    if len(nums) >= 4:
                        bbox_vals = [float(n) for n in nums[:4]]
                items.append({"text": text, "bbox_norm": bbox_vals})
            if items:
                data = items
            else:
                lines = []
                for ln in raw.splitlines():
                    line = ln.strip().strip(",")
                    if not line:
                        continue
                    if re.fullmatch(r'[\{\}\[\],]+', line):
                        continue
                    if re.match(r'^(lines|rows|entries|idx|bbox|bbox_norm|textbox_norm|textbbox_norm)\b\s*:?', line, flags=re.IGNORECASE):
                        continue
                    if re.fullmatch(r'-?\d+(?:\.\d+)?', line):
                        continue
                    if line.startswith('"') and line.endswith('"'):
                        line = line[1:-1]
                    lines.append({"text": line})
                data = lines
    out: List[Dict[str, Any]] = []
    for idx, item in enumerate(data or []):
        if isinstance(item, str):
            text = item
            bbox = None
            bbox_norm = None
        elif isinstance(item, dict):
            text = item.get("text") or item.get("line") or item.get("transcription") or item.get("ocr_text") or ""
            bbox = item.get("bbox") or item.get("box")
            bbox_norm = item.get("bbox_norm") or item.get("normalized_bbox") or item.get("bbox_normalized")
        else:
            continue
        parts = [p.strip() for p in str(text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n") if p.strip()]
        if not parts:
            continue
        if len(parts) > 1:
            for j, part in enumerate(parts):
                new_bbox_norm = None
                new_bbox = None
                if isinstance(bbox_norm, (list, tuple)) and len(bbox_norm) >= 4:
                    try:
                        x0, y0, x1, y1 = [float(x) for x in bbox_norm[:4]]
                        step = (y1 - y0) / max(1, len(parts))
                        new_bbox_norm = [x0, y0 + j * step, x1, y0 + (j + 1) * step]
                    except Exception:
                        new_bbox_norm = bbox_norm
                elif isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
                    try:
                        x0, y0, x1, y1 = [float(x) for x in bbox[:4]]
                        step = (y1 - y0) / max(1, len(parts))
                        new_bbox = [x0, y0 + j * step, x1, y0 + (j + 1) * step]
                    except Exception:
                        new_bbox = bbox
                out.append({"idx": len(out), "text": part, "bbox": new_bbox, "bbox_norm": new_bbox_norm})
        else:
            out.append({"idx": len(out), "text": parts[0], "bbox": bbox, "bbox_norm": bbox_norm})
    return out
def _bk_fix40_clean_lm_page_text_lines(payload) -> List[str]:
    lines = []
    for item in _bk_fix40_extract_jsonish_lines(payload):
        txt = _bk_fix36_clean_text(item.get("text", ""))
        if txt and not re.match(r"^(lines|rows|entries|idx|bbox|bbox_norm)\b\s*:?", txt, flags=re.IGNORECASE):
            lines.append(txt)
    return _bk_fix40_resolve_ditto_marks_in_lines(lines)
try:
    _BK_FIX40_PREV_FULLPAGE_RESPONSE_FORMAT = BKFullPageLMOCRWorker._response_format_full_page_lines
except Exception:
    _BK_FIX40_PREV_FULLPAGE_RESPONSE_FORMAT = None
def _bk_fix40_response_format_full_page_lines(self):
    if callable(_BK_FIX40_PREV_FULLPAGE_RESPONSE_FORMAT):
        return _BK_FIX40_PREV_FULLPAGE_RESPONSE_FORMAT(self)
    return {"type": "json_object"}
try:
    BKFullPageLMOCRWorker._response_format_full_page_lines = _bk_fix40_response_format_full_page_lines
except Exception:
    pass
    pass
try:
    _BK_FIX40_PREV_EXTRACT_FULLPAGE_LINES = BKFullPageLMOCRWorker._extract_full_page_lines
except Exception:
    _BK_FIX40_PREV_EXTRACT_FULLPAGE_LINES = None
def _bk_fix40_extract_full_page_lines(self, content: str):
    lines = _bk_fix40_clean_lm_page_text_lines(content)
    if lines:
        return lines
    parsed = _bk_fix40_extract_jsonish_lines(content)
    if parsed:
        return [str(item.get("text", "") or "").strip() for item in parsed if isinstance(item, dict) and str(item.get("text", "") or "").strip()]
    if callable(_BK_FIX40_PREV_EXTRACT_FULLPAGE_LINES):
        return _BK_FIX40_PREV_EXTRACT_FULLPAGE_LINES(self, content)
    return []
try:
    BKFullPageLMOCRWorker._extract_full_page_lines = _bk_fix40_extract_full_page_lines
except Exception:
    pass
try:
    _BK_FIX40_PREV_REQUEST_FULLPAGE_OCR = BKFullPageLMOCRWorker._request_full_page_ocr
except Exception:
    _BK_FIX40_PREV_REQUEST_FULLPAGE_OCR = None
def _bk_fix40_request_full_page_ocr(self, page_data_url: str):
    if callable(_BK_FIX40_PREV_REQUEST_FULLPAGE_OCR):
        return _BK_FIX40_PREV_REQUEST_FULLPAGE_OCR(self, page_data_url)
    return []
try:
    BKFullPageLMOCRWorker._request_full_page_ocr = _bk_fix40_request_full_page_ocr
except Exception:
    pass
try:
    _BK_FIX40_PREV_APPLY_QUEUE_BATCH_RESULT = _bk_lm_apply_queue_batch_result
except Exception:
    _BK_FIX40_PREV_APPLY_QUEUE_BATCH_RESULT = None
def _bk_lm_apply_queue_batch_result(self, path: str, mode: str, target_rows: List[int], revised_lines: List[Any]):
    if mode in (_BK_LM_BATCH_MODE_LM_OCR, _BK_LM_BATCH_MODE_LM_OCR_BOXES):
        clean_lines: List[str] = []
        for x in revised_lines or []:
            if isinstance(x, dict):
                clean_lines.extend(_bk_fix40_clean_lm_page_text_lines({"lines": [x]}))
            else:
                parsed = _bk_fix40_clean_lm_page_text_lines(x)
                clean_lines.extend(parsed if parsed else [str(x)])
        revised_lines = [x for x in _bk_fix40_resolve_ditto_marks_in_lines(clean_lines) if _bk_fix36_clean_text(x)]
    if callable(_BK_FIX40_PREV_APPLY_QUEUE_BATCH_RESULT):
        return _BK_FIX40_PREV_APPLY_QUEUE_BATCH_RESULT(self, path, mode, target_rows, revised_lines)
    return None
def _bk_fix40_resolve_ditto_marks_in_lines(lines: List[str]) -> List[str]:
    out: List[str] = []
    prev_line = ""
    mark_re = re.compile(r'(?<![A-Za-zÀ-ÿÄÖÜäöüß0-9])(?:[-–—]\s*)?["„“”]{1,4}(?:\s*[-–—])?(?![A-Za-zÀ-ÿÄÖÜäöüß0-9])')
    attached_re = re.compile(r'(?<![A-Za-zÀ-ÿÄÖÜäöüß0-9])(?:[-–—]\s*)?["„“”]{1,4}(?:\s*[-–—])?(?=[A-Za-zÀ-ÿÄÖÜäöüß])')
    for raw in lines or []:
        line = str(raw or "")
        if not line.strip():
            out.append(line)
            continue
        line2 = attached_re.sub("", line)
        def repl(match):
            after = line2[match.end():]
            if re.match(r"\s*[A-Za-zÀ-ÿÄÖÜäöüß]", after):
                return ""
            return _bk_fix37_prev_word_at_column(prev_line, match.start()) or ""
        line2 = mark_re.sub(repl, line2)
        line2 = re.sub(r"\s{2,}", " ", line2).strip()
        line2 = re.sub(r"\s+([.,;:])", r"\1", line2)
        out.append(line2)
        if line2:
            prev_line = line2
    return out
def _bk_fix40_resolve_ditto_marks_in_recs(recs):
    try:
        recs = list(recs or [])
        if not recs:
            return recs
        with_boxes = [rv for rv in recs if getattr(rv, "bbox", None)]
        if not with_boxes:
            texts = _bk_fix40_resolve_ditto_marks_in_lines([getattr(rv, "text", "") for rv in recs])
            for rv, txt in zip(recs, texts):
                rv.text = txt
            return recs
        rows = _bk_fix36_group_recs_into_table_rows(recs)
        prev_row = []
        for row in rows:
            row = sorted(row, key=lambda r: r.bbox[0] if getattr(r, "bbox", None) else 0)
            for rv in row:
                txt = str(getattr(rv, "text", "") or "")
                if not txt:
                    continue
                if _bk_fix36_is_ditto(txt) or re.fullmatch(r'\s*(?:[-–—]\s*)?["„“”]{1,4}(?:\s*[-–—])?\s*', txt):
                    if prev_row and getattr(rv, "bbox", None):
                        cx = (rv.bbox[0] + rv.bbox[2]) / 2.0
                        candidates = [p for p in prev_row if getattr(p, "bbox", None) and _bk_fix36_clean_text(getattr(p, "text", ""))]
                        if candidates:
                            best = min(candidates, key=lambda p: abs(((p.bbox[0] + p.bbox[2]) / 2.0) - cx))
                            rv.text = str(getattr(best, "text", "") or "")
                    continue
                resolved = _bk_fix40_resolve_ditto_marks_in_lines([txt])[0]
                rv.text = resolved
            if row:
                prev_row = [x for x in row if _bk_fix36_clean_text(getattr(x, "text", ""))]
    except Exception:
        pass
    return recs
_bk_fix36_resolve_ditto_marks_in_lines = _bk_fix40_resolve_ditto_marks_in_lines
_bk_fix37_resolve_ditto_marks_in_lines = _bk_fix40_resolve_ditto_marks_in_lines
_bk_fix38_resolve_ditto_marks_in_lines = _bk_fix40_resolve_ditto_marks_in_lines
_bk_fix36_resolve_ditto_marks_in_recs = _bk_fix40_resolve_ditto_marks_in_recs
_bk_fix38_expand_ditto_text = lambda text: "\n".join(_bk_fix40_resolve_ditto_marks_in_lines(str(text or "").splitlines()))
_bk_fix37_expand_ditto_text = _bk_fix38_expand_ditto_text
__all__ = [
    '_bk_fix36_resolve_ditto_marks_in_lines',
    '_bk_fix36_resolve_ditto_marks_in_recs',
    '_bk_fix37_expand_ditto_text',
    '_bk_fix37_resolve_ditto_marks_in_lines',
    '_bk_fix38_expand_ditto_text',
    '_bk_fix38_resolve_ditto_marks_in_lines',
    '_bk_fix40_clean_lm_page_text_lines',
    '_bk_fix40_extract_full_page_lines',
    '_bk_fix40_extract_jsonish_lines',
    '_bk_fix40_request_full_page_ocr',
    '_bk_fix40_resolve_ditto_marks_in_lines',
    '_bk_fix40_resolve_ditto_marks_in_recs',
    '_bk_fix40_response_format_full_page_lines',
    '_bk_fix40_strip_code_fences',
    '_bk_lm_apply_queue_batch_result',
]
register_globals('bk', globals(), __all__)
