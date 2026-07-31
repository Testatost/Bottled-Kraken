from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
from bottled_kraken.common import (
    _clean_ocr_text,
    _extract_json_payload,
    _force_text,
    _normalize_ai_script_mode,
)
from bottled_kraken.common import (
    AI_SCRIPT_PRINT,
    List,
    QApplication,
    QCursor,
    QDialog,
    QKeySequence,
    QRectF,
    QShortcut,
    QTimer,
    Qt,
    isValid,
    re,
)
from bottled_kraken.workers import (
    AIRevisionWorker,
)
from bottled_kraken.dialogs import (
    BusyStatusDialog,
    ProgressStatusDialog,
)
from bottled_kraken.main_window import MainWindow
def _bk_fix45_screen_geometry(widget=None):
    try:
        screen = None
        if widget is not None and hasattr(widget, "windowHandle") and widget.windowHandle():
            screen = widget.windowHandle().screen()
        if screen is None:
            screen = QApplication.screenAt(QCursor.pos())
        if screen is None:
            screen = QApplication.primaryScreen()
        if screen is not None:
            return screen.availableGeometry()
    except Exception:
        pass
    return QApplication.primaryScreen().availableGeometry() if QApplication.primaryScreen() else QRectF(0, 0, 1280, 720).toRect()
def _bk_fix45_prepare_dialog_size(dialog):
    try:
        geo = _bk_fix45_screen_geometry(dialog)
        max_w = max(360, int(geo.width() - 80))
        for label_name in ("lbl_status", "label", "lbl_info"):
            label = getattr(dialog, label_name, None)
            if label is not None:
                try:
                    label.setWordWrap(True)
                    label.setMinimumWidth(min(320, max_w))
                    label.setMaximumWidth(max_w)
                except Exception:
                    pass
    except Exception:
        pass
def _bk_fix45_center_dialog(dialog):
    try:
        if dialog is None or not isValid(dialog):
            return
        _bk_fix45_prepare_dialog_size(dialog)
        geo = _bk_fix45_screen_geometry(dialog)
        frame = dialog.frameGeometry()
        x = geo.left() + max(0, int((geo.width() - frame.width()) / 2))
        y = geo.top() + max(0, int((geo.height() - frame.height()) / 2))
        dialog.move(x, y)
    except Exception:
        pass
def _bk_fix45_patch_status_dialog_class(cls):
    if cls is None or getattr(cls, "_bk_fix45_center_patched", False):
        return
    old_set_status = getattr(cls, "set_status", None)
    old_show_event = getattr(cls, "showEvent", None)
    old_resize_event = getattr(cls, "resizeEvent", None)
    def set_status(self, text: str):
        try:
            if callable(old_set_status):
                old_set_status(self, text)
            elif hasattr(self, "lbl_status"):
                self.lbl_status.setText(str(text or ""))
        except Exception:
            try:
                if hasattr(self, "lbl_status"):
                    self.lbl_status.setText(str(text or ""))
            except Exception:
                pass
        try:
            _bk_fix45_prepare_dialog_size(self)
            QDialog.adjustSize(self)
        except Exception:
            try:
                self.adjustSize()
            except Exception:
                pass
        try:
            QTimer.singleShot(0, lambda d=self: _bk_fix45_center_dialog(d))
        except Exception:
            _bk_fix45_center_dialog(self)
    def showEvent(self, event):
        try:
            if callable(old_show_event):
                old_show_event(self, event)
            else:
                QDialog.showEvent(self, event)
        except Exception:
            pass
        try:
            _bk_fix45_prepare_dialog_size(self)
            QTimer.singleShot(0, lambda d=self: _bk_fix45_center_dialog(d))
        except Exception:
            pass
    def resizeEvent(self, event):
        try:
            if callable(old_resize_event):
                old_resize_event(self, event)
            else:
                QDialog.resizeEvent(self, event)
        except Exception:
            pass
        try:
            QTimer.singleShot(0, lambda d=self: _bk_fix45_center_dialog(d))
        except Exception:
            pass
    cls.set_status = set_status
    cls.showEvent = showEvent
    cls.resizeEvent = resizeEvent
    cls._bk_fix45_center_patched = True
try:
    _bk_fix45_patch_status_dialog_class(BusyStatusDialog)
    _bk_fix45_patch_status_dialog_class(ProgressStatusDialog)
except Exception:
    pass
try:
    _BK_FIX45_PREV_CROP_PROFILE = _ai_script_crop_profile
except Exception:
    _BK_FIX45_PREV_CROP_PROFILE = None
def _bk_fix45_ai_script_crop_profile(script_mode=None):
    try:
        prof = dict(_BK_FIX45_PREV_CROP_PROFILE(script_mode)) if callable(_BK_FIX45_PREV_CROP_PROFILE) else {}
    except Exception:
        prof = {}
    try:
        mode = _normalize_ai_script_mode(script_mode)
    except Exception:
        mode = AI_SCRIPT_PRINT
    if mode == AI_SCRIPT_PRINT:
        prof["single_pad_x"] = 0
        prof["single_pad_y"] = 0
        prof["single_extra_context_y"] = 0
        prof["block_pad_x"] = 0
        prof["block_pad_y"] = 0
        return prof
    prof["single_pad_x"] = max(int(prof.get("single_pad_x", 0) or 0), 28)
    prof["single_pad_y"] = max(int(prof.get("single_pad_y", 0) or 0), 10)
    prof["single_extra_context_y"] = max(int(prof.get("single_extra_context_y", 0) or 0), 10)
    prof["block_pad_x"] = max(int(prof.get("block_pad_x", 0) or 0), 150)
    prof["block_pad_y"] = max(int(prof.get("block_pad_y", 0) or 0), 70)
    return prof
try:
    _ai_script_crop_profile = _bk_fix45_ai_script_crop_profile
except Exception:
    pass
def _bk_fix45_token_set(text: str) -> set:
    return set(re.findall(r"[A-Za-zÀ-ÿÄÖÜäöüß0-9]+", str(text or "").casefold()))
def _bk_fix45_number_set(text: str) -> set:
    return set(re.findall(r"\b\d+(?:[./]\d+)*\b", str(text or "")))
def _bk_fix45_missing_ratio(reference: str, candidate: str) -> float:
    ref = _bk_fix45_token_set(reference)
    if not ref:
        return 0.0
    cand = _bk_fix45_token_set(candidate)
    if not cand:
        return 1.0
    return len(ref - cand) / max(1, len(ref))
def _bk_fix45_is_bad_candidate(worker, text: str) -> bool:
    t = _clean_ocr_text(text or "")
    if not t:
        return True
    if t.startswith("{") or t.startswith("[") or "bbox_norm" in t:
        return True
    try:
        if worker._looks_like_long_block(t) or worker._is_suspicious_box_result(t):
            return True
    except Exception:
        pass
    return False
def _bk_fix45_candidate_score(worker, cand: str, kraken: str, page: str, box: str) -> float:
    c = _clean_ocr_text(cand or "")
    if _bk_fix45_is_bad_candidate(worker, c):
        return -999999.0
    info = float(_bk_fix43_info_len(c))
    score = info
    for ref, weight in ((kraken, 34.0), (page, 34.0), (box, 12.0)):
        r = _clean_ocr_text(ref or "")
        if not r:
            continue
        miss = _bk_fix45_missing_ratio(r, c)
        score += weight * (1.0 - miss)
        nums = _bk_fix45_number_set(r)
        if nums:
            missing_nums = nums - _bk_fix45_number_set(c)
            score -= 18.0 * len(missing_nums)
    max_ref_len = max(_bk_fix43_info_len(kraken), _bk_fix43_info_len(page), 1)
    if _bk_fix43_info_len(c) < max(5, int(max_ref_len * 0.72)):
        score -= 80.0
    return score
def _bk_fix45_merge_candidates(worker, kraken_text: str, page_text: str, box_text: str, prev_final_text: str = "") -> str:
    kt = _clean_ocr_text(kraken_text or "")
    pt = _clean_ocr_text(page_text or "")
    bt = _clean_ocr_text(box_text or "")
    candidates = []
    for label, val in (("kraken", kt), ("page", pt), ("box", bt)):
        if val and not _bk_fix45_is_bad_candidate(worker, val):
            candidates.append((label, val, _bk_fix45_candidate_score(worker, val, kt, pt, bt)))
    if not candidates:
        return kt or pt or bt or ""
    candidates.sort(key=lambda x: x[2], reverse=True)
    best_label, best, best_score = candidates[0]
    try:
        if prev_final_text and best and worker._normalize_compare_text(best) == worker._normalize_compare_text(prev_final_text):
            for _label, cand, _score in candidates[1:]:
                if worker._normalize_compare_text(cand) != worker._normalize_compare_text(prev_final_text):
                    best = cand
                    break
    except Exception:
        pass
    return _clean_ocr_text(best)
_bk_fix41_choose_final_kraken_first = _bk_fix45_merge_candidates
_bk_fix43_choose_final_kraken_first = _bk_fix45_merge_candidates
def _bk_fix45_request_block_reread(self, block_data_url: str, start_idx: int, end_idx: int, current_lines: List[str]) -> List[str]:
    count = end_idx - start_idx
    system_prompt = self._tr("ai_prompt_block_system")
    page_context_lines = getattr(self, "_bk_fix42_page_context_lines", None) or []
    context_slice = []
    try:
        lo = max(0, start_idx - 3)
        hi = min(len(page_context_lines), end_idx + 3)
        context_slice = [f"{i}: {page_context_lines[i]}" for i in range(lo, hi) if _bk_fix36_clean_text(page_context_lines[i])]
    except Exception:
        context_slice = []
    joined_hint = "\n".join(f"{i}: {txt}" for i, txt in enumerate(current_lines))
    user_prompt = self._tr("ai_prompt_block_user", count, joined_hint)
    user_prompt += "\n\n" + self._tr(
        "ai_prompt_block_no_omit_hint",
        "Wichtig: Gib jede der drei Zeilen vollständig zurück. Kürze nichts. Kein Name, Ort, Datum, Alter, Jahr und keine Zahl darf verschwinden. Kraken-OCR und kompletter LM-Seiten-OCR sind gleichwertige Quellen; entscheide mit Sanity-Check, welcher Text vollständig und plausibel ist."
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
        txt = _clean_ocr_text(out[i])
        fallback = _clean_ocr_text(current_lines[i] if i < len(current_lines) else "")
        page_line = _clean_ocr_text(page_context_lines[start_idx + i] if start_idx + i < len(page_context_lines) else "")
        if txt:
            refs = [r for r in (fallback, page_line) if r]
            for ref in refs:
                if _bk_fix43_info_len(txt) < int(_bk_fix43_info_len(ref) * 0.78):
                    txt = ""
                    break
                missing_nums = _bk_fix45_number_set(ref) - _bk_fix45_number_set(txt)
                if len(missing_nums) >= 2:
                    txt = ""
                    break
        fixed.append(txt if txt else (page_line if page_line and _bk_fix43_info_len(page_line) > _bk_fix43_info_len(fallback) * 1.15 else fallback))
    return fixed
try:
    AIRevisionWorker._request_block_reread = _bk_fix45_request_block_reread
except Exception:
    pass
def _bk_fix45_begin_draw_box_for_current_line(self):
    try:
        task = self._ensure_overlay_possible()
        if not task or not getattr(task, "results", None):
            return
        row = -1
        try:
            rows = self._selected_line_rows()
            if rows:
                row = int(rows[0])
        except Exception:
            pass
        if row < 0 and hasattr(self, "list_lines"):
            try:
                row = int(self.list_lines.currentRow())
            except Exception:
                row = -1
        _, _, _, recs = task.results
        if not (0 <= row < len(recs)):
            return
        self._pending_new_line_box = False
        self._pending_box_for_row = row
        try:
            self.canvas.set_overlay_enabled(True)
            self.canvas.setFocus(Qt.ShortcutFocusReason)
        except Exception:
            pass
        self.canvas.start_draw_box_mode()
        try:
            self.status_bar.showMessage(self._tr("canvas_menu_add_box_draw"), 3000)
        except Exception:
            pass
    except Exception as exc:
        try:
            print(f"FIX8.45 preview B shortcut failed: {exc}")
        except Exception:
            pass
def _bk_fix45_connect_preview_shortcut(self):
    try:
        if getattr(self, "_bk_fix45_b_shortcut_connected", False):
            return
        if not hasattr(self, "canvas"):
            return
        try:
            self.canvas.setFocusPolicy(Qt.StrongFocus)
            self.canvas.viewport().setFocusPolicy(Qt.StrongFocus)
        except Exception:
            pass
        sc = QShortcut(QKeySequence("B"), self.canvas)
        sc.setContext(Qt.WidgetWithChildrenShortcut)
        sc.activated.connect(lambda w=self: _bk_fix45_begin_draw_box_for_current_line(w))
        self._bk_fix45_b_shortcut = sc
        sc2 = QShortcut(QKeySequence("B"), self.canvas.viewport())
        sc2.setContext(Qt.WidgetShortcut)
        sc2.activated.connect(lambda w=self: _bk_fix45_begin_draw_box_for_current_line(w))
        self._bk_fix45_b_shortcut_viewport = sc2
        self._bk_fix45_b_shortcut_connected = True
    except Exception as exc:
        try:
            print(f"FIX8.45 shortcut connect failed: {exc}")
        except Exception:
            pass
def _bk_fix45_mainwindow_init(self, *args, **kwargs):
    try:
        QTimer.singleShot(0, lambda w=self: _bk_fix45_connect_preview_shortcut(w))
    except Exception:
        _bk_fix45_connect_preview_shortcut(self)
from bottled_kraken.common.chain_consolidation import register_init_delta
register_init_delta(_bk_fix45_mainwindow_init)
try:
    MainWindow.bk_draw_box_for_current_line_shortcut = _bk_fix45_begin_draw_box_for_current_line
except Exception:
    pass
__all__ = [
    '_bk_fix41_choose_final_kraken_first',
    '_bk_fix43_choose_final_kraken_first',
    '_bk_fix45_ai_script_crop_profile',
    '_bk_fix45_begin_draw_box_for_current_line',
    '_bk_fix45_candidate_score',
    '_bk_fix45_center_dialog',
    '_bk_fix45_connect_preview_shortcut',
    '_bk_fix45_is_bad_candidate',
    '_bk_fix45_merge_candidates',
    '_bk_fix45_missing_ratio',
    '_bk_fix45_number_set',
    '_bk_fix45_patch_status_dialog_class',
    '_bk_fix45_prepare_dialog_size',
    '_bk_fix45_request_block_reread',
    '_bk_fix45_screen_geometry',
    '_bk_fix45_token_set',
]
register_globals('bk', globals(), __all__)
