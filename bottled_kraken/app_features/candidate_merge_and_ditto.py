from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
from bottled_kraken.common import (
    _clean_ocr_text,
    _extract_json_payload,
    _force_text,
)
from bottled_kraken.common import (
    List,
    QTimer,
    RecordView,
    re,
)
from bottled_kraken.workers import (
    AIRevisionWorker,
)
from bottled_kraken.main_window import MainWindow
def _bk_fix43_norm_tokens(text: str) -> List[str]:
    return re.findall(r"[A-Za-zÀ-ÿÄÖÜäöüß0-9]+", str(text or "").lower())
def _bk_fix43_overlap_ratio(base: str, candidate: str) -> float:
    base_tokens = _bk_fix43_norm_tokens(base)
    cand_tokens = set(_bk_fix43_norm_tokens(candidate))
    if not base_tokens or not cand_tokens:
        return 0.0
    hit = sum(1 for t in base_tokens if t in cand_tokens)
    return hit / max(1, len(base_tokens))
def _bk_fix43_info_len(text: str) -> int:
    return len("".join(_bk_fix43_norm_tokens(text)))
def _bk_fix43_choose_final_kraken_first(worker, kraken_text: str, page_text: str, box_text: str, prev_final_text: str = '') -> str:
    kt = _clean_ocr_text(kraken_text or '')
    pt = _clean_ocr_text(page_text or '')
    bt = _clean_ocr_text(box_text or '')
    candidates = [c for c in (kt, pt, bt) if c]
    if not candidates:
        return ""
    def is_suspicious(text: str) -> bool:
        try:
            return bool(worker._looks_like_long_block(text) or worker._is_suspicious_box_result(text))
        except Exception:
            return False
    if kt and not is_suspicious(kt):
        best = kt
        best_len = _bk_fix43_info_len(best)
        for cand in (pt, bt):
            if not cand:
                continue
            cand_len = _bk_fix43_info_len(cand)
            if cand_len < max(4, int(best_len * 0.82)):
                continue
            overlap = _bk_fix43_overlap_ratio(kt, cand)
            if cand_len > best_len * 1.12 and overlap >= 0.55:
                best = cand
                best_len = cand_len
        if prev_final_text and best and worker._normalize_compare_text(best) == worker._normalize_compare_text(prev_final_text):
            for cand in (kt, pt, bt):
                if cand and worker._normalize_compare_text(cand) != worker._normalize_compare_text(prev_final_text):
                    if _bk_fix43_info_len(cand) >= max(4, int(best_len * 0.70)):
                        best = cand
                        break
        return _clean_ocr_text(best)
    best = ""
    for cand in (pt, bt, kt):
        if not cand:
            continue
        if not best or _bk_fix43_info_len(cand) > _bk_fix43_info_len(best):
            best = cand
    return _clean_ocr_text(best)
_bk_fix41_choose_final_kraken_first = _bk_fix43_choose_final_kraken_first
def _bk_fix43_request_block_reread(self, block_data_url: str, start_idx: int, end_idx: int, current_lines: List[str]) -> List[str]:
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
    user_prompt += "\n\n" + self._tr(
        "ai_prompt_block_no_omit_hint",
        "Wichtig: Gib jede der drei Zeilen vollständig zurück. Kürze nichts. Wenn der Ausschnitt rechts/links weitere Wörter, Daten, Orte oder Zahlen enthält, müssen diese erhalten bleiben. Wenn du unsicher bist, behalte die Kraken-Zeile unverändert."
    )
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
        if fallback and txt and _bk_fix43_info_len(txt) < int(_bk_fix43_info_len(fallback) * 0.75):
            txt = fallback
        fixed.append(txt if txt else fallback)
    return fixed
try:
    AIRevisionWorker._request_block_reread = _bk_fix43_request_block_reread
except Exception:
    pass
def _bk_fix43_resolve_line_ditto_from_prev(prev_line: str, cur_line: str) -> str:
    line = str(cur_line or "")
    if not line.strip() or not re.search(r"[\"„“”]", line):
        return line
    quote_re = re.compile(r"(?<![A-Za-zÀ-ÿÄÖÜäöüß0-9.])(?:[-–—]\s*)?[\"„“”]{1,4}(?:\s*[-–—])?(?![A-Za-zÀ-ÿÄÖÜäöüß0-9.])")
    used_positions = []
    def repl(match):
        repl_text = _bk_fix42_prev_segment_at_char(prev_line, match.start())
        if not repl_text or _bk_fix42_is_ditto_token_text(repl_text) or re.fullmatch(r"[.\s]+", repl_text):
            return ""
        left_tokens = _bk_fix43_norm_tokens(line[:match.start()])[-3:]
        right_tokens = _bk_fix43_norm_tokens(line[match.end():])[:2]
        repl_tokens = _bk_fix43_norm_tokens(repl_text)
        if repl_tokens:
            last = repl_tokens[-1]
            if last in left_tokens[-2:] or last in right_tokens:
                return ""
        pos = match.start()
        if any(abs(pos - p) <= 2 for p in used_positions):
            return ""
        used_positions.append(pos)
        return repl_text
    out = quote_re.sub(repl, line)
    out = re.sub(r"\s{2,}", " ", out).strip()
    out = re.sub(r"\s+([.,;:])", r"\1", out)
    return out
def _bk_fix43_resolve_ditto_marks_with_recs(recs, texts: List[str]) -> List[str]:
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
            tmp = _bk_fix43_resolve_ditto_marks_in_recs(tmp)
            return [getattr(rv, "text", "") for rv in tmp]
        except Exception:
            pass
    out = []
    prev = ""
    for line in texts:
        resolved = _bk_fix43_resolve_line_ditto_from_prev(prev, line)
        out.append(resolved)
        if _bk_fix36_clean_text(resolved):
            prev = resolved
    return out
def _bk_fix43_resolve_ditto_marks_in_recs(recs):
    try:
        recs = list(recs or [])
        if not recs:
            return recs
        if not any(getattr(rv, "bbox", None) for rv in recs):
            texts = _bk_fix43_resolve_ditto_marks_with_recs(None, [getattr(rv, "text", "") for rv in recs])
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
                        value = str(getattr(best, "text", "") or "")
                        if not _bk_fix42_is_ditto_token_text(value) and not re.fullmatch(r"[.\s]+", value):
                            rv.text = value
                        else:
                            rv.text = ""
                    continue
                rv.text = _bk_fix43_resolve_line_ditto_from_prev(prev_line_text, txt)
            if row:
                prev_row = [x for x in row if _bk_fix36_clean_text(getattr(x, "text", ""))]
    except Exception:
        pass
    return recs
def _bk_fix43_resolve_ditto_marks_in_lines(lines):
    return _bk_fix43_resolve_ditto_marks_with_recs(None, list(lines or []))
_bk_fix42_resolve_line_ditto_from_prev = _bk_fix43_resolve_line_ditto_from_prev
_bk_fix42_resolve_ditto_marks_with_recs = _bk_fix43_resolve_ditto_marks_with_recs
_bk_fix42_resolve_ditto_marks_in_recs = _bk_fix43_resolve_ditto_marks_in_recs
_bk_fix41_resolve_ditto_marks_in_lines = _bk_fix43_resolve_ditto_marks_in_lines
_bk_fix40_resolve_ditto_marks_in_lines = _bk_fix41_resolve_ditto_marks_in_lines
_bk_fix36_resolve_ditto_marks_in_lines = _bk_fix41_resolve_ditto_marks_in_lines
_bk_fix37_resolve_ditto_marks_in_lines = _bk_fix41_resolve_ditto_marks_in_lines
_bk_fix41_resolve_ditto_marks_in_recs = _bk_fix43_resolve_ditto_marks_in_recs
_bk_fix40_resolve_ditto_marks_in_recs = _bk_fix43_resolve_ditto_marks_in_recs
_bk_fix36_resolve_ditto_marks_in_recs = _bk_fix43_resolve_ditto_marks_in_recs
_bk_fix37_expand_ditto_text = lambda text: "\n".join(_bk_fix43_resolve_ditto_marks_with_recs(None, str(text or "").splitlines()))
_bk_fix38_expand_ditto_text = _bk_fix37_expand_ditto_text
try:
    MainWindow.bk_resolve_ditto_marks_in_recs = lambda self, recs: _bk_fix43_resolve_ditto_marks_in_recs(recs)
except Exception:
    pass
def _bk_fix43_connect_stop_buttons(self):
    try:
        for attr in list(vars(self).keys()):
            low = attr.lower()
            if "stop" not in low and "cancel" not in low:
                continue
            try:
                obj = getattr(self, attr)
            except Exception:
                continue
            try:
                signal = getattr(obj, "clicked", None) or getattr(obj, "triggered", None)
                if signal is not None and not getattr(obj, "_bk_fix43_stop_connected", False):
                    signal.connect(lambda *args, w=self: _bk_fix43_stop_everything_now(w))
                    setattr(obj, "_bk_fix43_stop_connected", True)
            except Exception:
                pass
    except Exception:
        pass
def _bk_fix43_mainwindow_init(self, *args, **kwargs):
    try:
        QTimer.singleShot(0, lambda: _bk_fix43_connect_stop_buttons(self))
    except Exception:
        _bk_fix43_connect_stop_buttons(self)
from bottled_kraken.common.chain_consolidation import register_init_delta
register_init_delta(_bk_fix43_mainwindow_init)
__all__ = [
    '_bk_fix36_resolve_ditto_marks_in_lines',
    '_bk_fix36_resolve_ditto_marks_in_recs',
    '_bk_fix37_expand_ditto_text',
    '_bk_fix37_resolve_ditto_marks_in_lines',
    '_bk_fix38_expand_ditto_text',
    '_bk_fix40_resolve_ditto_marks_in_lines',
    '_bk_fix40_resolve_ditto_marks_in_recs',
    '_bk_fix41_choose_final_kraken_first',
    '_bk_fix41_resolve_ditto_marks_in_lines',
    '_bk_fix41_resolve_ditto_marks_in_recs',
    '_bk_fix42_resolve_ditto_marks_in_recs',
    '_bk_fix42_resolve_ditto_marks_with_recs',
    '_bk_fix42_resolve_line_ditto_from_prev',
    '_bk_fix43_choose_final_kraken_first',
    '_bk_fix43_connect_stop_buttons',
    '_bk_fix43_info_len',
    '_bk_fix43_norm_tokens',
    '_bk_fix43_overlap_ratio',
    '_bk_fix43_request_block_reread',
    '_bk_fix43_resolve_ditto_marks_in_lines',
    '_bk_fix43_resolve_ditto_marks_in_recs',
    '_bk_fix43_resolve_ditto_marks_with_recs',
    '_bk_fix43_resolve_line_ditto_from_prev',
]
register_globals('bk', globals(), __all__)
