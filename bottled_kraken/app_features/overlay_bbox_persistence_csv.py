from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
from bottled_kraken.common import _load_image_color
from bottled_kraken.common import (
    List,
    QApplication,
    QCursor,
    QMenu,
    RecordView,
    TaskItem,
    csv,
    os,
    re,
)
from bottled_kraken.dialogs import (
    BusyStatusDialog,
    ProgressStatusDialog,
)
from bottled_kraken.main_window import MainWindow
try:
    from bottled_kraken._main_window.menu_and_queue.menu_behavior import BKStayOpenMenu as _BKStayOpenMenu52
    def _bk_fix52_fit_menu(menu):
        try:
            fm = menu.fontMetrics(); max_w = 0
            for act in menu.actions():
                if act.isSeparator():
                    continue
                max_w = max(max_w, fm.horizontalAdvance(act.text().replace('&', '')) + (36 if act.menu() else 0))
            if max_w:
                menu.setMinimumWidth(min(max_w + 64, _bk_fix52_screen_max_width(menu)))
        except Exception:
            pass
    _orig_popup = getattr(_BKStayOpenMenu52, 'popup', None)
    if callable(_orig_popup) and not getattr(_orig_popup, '_bk_fix52_popup', False):
        def _popup(self, pos, action=None):
            _bk_fix52_fit_menu(self)
            return _orig_popup(self, pos, action)
        _popup._bk_fix52_popup = True
        _BKStayOpenMenu52.popup = _popup
except Exception:
    pass
def _bk_fix53_clean_text(value) -> str:
    try:
        return re.sub(r"\s+", " ", str(value or "")).strip()
    except Exception:
        return str(value or "").strip()
def _bk_fix53_image_size_from_task(task):
    try:
        if task and getattr(task, 'results', None):
            _t, _k, im, _r = task.results
            if im is not None and getattr(im, 'size', None):
                return im.size
    except Exception:
        pass
    try:
        if task and getattr(task, 'path', None):
            return _load_image_color(task.path).size
    except Exception:
        pass
    return None
def _bk_fix53_adjust_recs_once(task, *, force: bool = False):
    try:
        if not task or not getattr(task, 'results', None):
            return False
        if not force and not bool(getattr(task, '_bk_fresh_kraken_ocr_result', False)):
            return False
        if getattr(task, '_bk_fix53_default_box_scale_applied', False) and not force:
            return False
        text, kr_records, im, recs = task.results
        image_size = _bk_fix53_image_size_from_task(task)
        changed = False
        for rv in recs or []:
            bb = getattr(rv, 'bbox', None)
            if bb:
                nbb = _bk_fix52_adjust_bbox(bb, image_size) if callable(globals().get('_bk_fix52_adjust_bbox')) else bb
                if nbb != bb:
                    rv.bbox = nbb
                    changed = True
        task.results = (text, kr_records, im, recs)
        task.preset_bboxes = [getattr(rv, 'bbox', None) for rv in (recs or [])]
        task._bk_fix53_default_box_scale_applied = True
        task._bk_fix52_default_box_scale_applied = True
        task._bk_fresh_kraken_ocr_result = False
        return changed
    except Exception:
        return False
try:
    _BK_FIX53_PREV_UPDATE_PRESET = MainWindow._update_task_preset_bboxes
except Exception:
    _BK_FIX53_PREV_UPDATE_PRESET = None
def _bk_fix53_update_task_preset_bboxes(self, task: TaskItem):
    try:
        if task is not None and getattr(task, 'results', None):
            _bk_fix53_adjust_recs_once(task)
    except Exception:
        pass
    if callable(_BK_FIX53_PREV_UPDATE_PRESET):
        return _BK_FIX53_PREV_UPDATE_PRESET(self, task)
    try:
        if not task or not task.results:
            task.preset_bboxes = []
            return
        _t, _k, _im, recs = task.results
        task.preset_bboxes = [getattr(rv, 'bbox', None) for rv in recs]
    except Exception:
        pass
try:
    MainWindow._update_task_preset_bboxes = _bk_fix53_update_task_preset_bboxes
except Exception:
    pass
try:
    _BK_FIX53_PREV_REFRESH_OVERLAY = MainWindow._refresh_overlay_display
except Exception:
    _BK_FIX53_PREV_REFRESH_OVERLAY = None
def _bk_fix53_refresh_overlay_display(self, recs=None):
    try:
        task = self._current_task() if hasattr(self, '_current_task') else None
        if task is not None and getattr(task, 'results', None):
            if _bk_fix53_adjust_recs_once(task):
                _t, _k, _im, recs2 = task.results
                if recs is None or recs is recs2:
                    recs = recs2
    except Exception:
        pass
    if callable(_BK_FIX53_PREV_REFRESH_OVERLAY):
        return _BK_FIX53_PREV_REFRESH_OVERLAY(self, recs)
try:
    MainWindow._refresh_overlay_display = _bk_fix53_refresh_overlay_display
except Exception:
    pass
def _bk_fix53_tr_queue_ref(parent, number: int) -> str:
    try:
        return _bk_fix36_tr(parent, 'busy_queue_ref').format(int(number))
    except Exception:
        return f'Wartebereich #{int(number)}'
def _bk_fix53_queue_index_for_text(parent, text: str):
    try:
        s = str(text or '')
        for idx, task in enumerate(getattr(parent, 'queue_items', []) or [], start=1):
            vals = []
            for attr in ('path', 'display_name'):
                v = getattr(task, attr, '')
                if v:
                    vals.append(str(v))
                    vals.append(os.path.basename(str(v)))
            for v in vals:
                if v and len(v) > 2 and v in s:
                    return idx
        if hasattr(parent, 'queue_table'):
            r = int(parent.queue_table.currentRow())
            if r >= 0:
                return r + 1
    except Exception:
        pass
    return None
def _bk_fix53_sanitize_wait_text(parent, text: str) -> str:
    raw = str(text or '')
    idx = _bk_fix53_queue_index_for_text(parent, raw)
    out = raw
    try:
        for task in getattr(parent, 'queue_items', []) or []:
            vals = []
            for attr in ('path', 'display_name'):
                v = getattr(task, attr, '')
                if v:
                    vals.extend([str(v), os.path.basename(str(v))])
            for v in sorted(set(vals), key=len, reverse=True):
                if v:
                    out = out.replace(v, '')
        out = re.sub(r'[:\-–—,;\s]+$', '', out.strip())
        out = re.sub(r'\n\s*\n+', '\n', out)
        if idx is not None:
            ref = _bk_fix53_tr_queue_ref(parent, idx)
            if ref not in out:
                out = (out.strip() + '\n' + ref).strip()
    except Exception:
        pass
    return out.strip() or raw.strip()
try:
    _BK_FIX53_PREV_BUSY_INIT = BusyStatusDialog.__init__
except Exception:
    _BK_FIX53_PREV_BUSY_INIT = None
if callable(_BK_FIX53_PREV_BUSY_INIT) and not getattr(BusyStatusDialog.__init__, '_bk_fix53_wrapped', False):
    def _bk_fix53_busy_init(self, title: str, message: str, tr, parent=None):
        _BK_FIX53_PREV_BUSY_INIT(self, title, message, tr, parent)
        try:
            clean = _bk_fix53_sanitize_wait_text(parent or self.parent(), getattr(self, '_base_message', message))
            self._base_message = clean
            self.lbl_status.setText(clean)
            self.setMaximumWidth(max(360, _bk_fix52_screen_max_width(self) + 120 if callable(globals().get('_bk_fix52_screen_max_width')) else 1600))
            self.adjustSize()
            try:
                screen = (self.screen() or QApplication.primaryScreen()).availableGeometry()
                self.move(screen.center() - self.rect().center())
            except Exception:
                pass
        except Exception:
            pass
    _bk_fix53_busy_init._bk_fix53_wrapped = True
    BusyStatusDialog.__init__ = _bk_fix53_busy_init
def _bk_fix53_patch_status_method(cls):
    try:
        prev = cls.set_status
    except Exception:
        return
    if getattr(prev, '_bk_fix53_wrapped', False):
        return
    def _set_status(self, text: str):
        parent = self.parent()
        clean = _bk_fix53_sanitize_wait_text(parent, text)
        try:
            return prev(self, clean)
        finally:
            try:
                self.lbl_status.setText(_bk_fix53_sanitize_wait_text(parent, getattr(self, '_base_message', clean)))
                self.adjustSize()
                screen = (self.screen() or QApplication.primaryScreen()).availableGeometry()
                self.move(screen.center() - self.rect().center())
            except Exception:
                pass
    _set_status._bk_fix53_wrapped = True
    cls.set_status = _set_status
try:
    _bk_fix53_patch_status_method(BusyStatusDialog)
    _bk_fix53_patch_status_method(ProgressStatusDialog)
except Exception:
    pass
def _bk_fix53_grid_from_table_block(block) -> List[List[str]]:
    rows = block.get('rows') or []
    out = []
    for row in rows:
        out.append([_bk_fix53_clean_text(cell) for cell in (row or [])])
    return out
def _bk_fix53_write_csv(path: str, record_views: List[RecordView], image_size=None):
    page_w = int(image_size[0]) if image_size else 0
    blocks = _bk_fix51_split_blocks(list(record_views or []), page_w) if callable(globals().get('_bk_fix51_split_blocks')) else []
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not blocks:
            for rv in record_views or []:
                writer.writerow([_bk_fix53_clean_text(getattr(rv, 'text', ''))])
            return
        for bi, block in enumerate(blocks):
            if bi:
                writer.writerow([])
            if block.get('type') == 'table':
                for row in _bk_fix53_grid_from_table_block(block):
                    writer.writerow(row)
            else:
                text = _bk_fix53_clean_text(block.get('text', ''))
                if text:
                    writer.writerow([text])
try:
    from PySide6.QtWidgets import QMenuBar
    from bottled_kraken._main_window.menu_and_queue.menu_behavior import BKStayOpenMenu as _BKStayOpenMenu53
    def _bk_fix53_cursor_inside_chain_or_menubar(chain):
        try:
            gp = QCursor.pos()
            for m in chain or []:
                if isinstance(m, QMenu) and m.isVisible() and m.geometry().adjusted(-4, -4, 4, 4).contains(gp):
                    return True
                parent = m.parentWidget() if hasattr(m, 'parentWidget') else None
                while parent is not None:
                    if isinstance(parent, QMenuBar) and parent.geometry().adjusted(-6, -6, 6, 6).contains(parent.mapFromGlobal(gp)):
                        return True
                    if isinstance(parent, QMenu) and parent.isVisible() and parent.geometry().adjusted(-4, -4, 4, 4).contains(gp):
                        return True
                    parent = parent.parentWidget() if hasattr(parent, 'parentWidget') else None
            for widget in QApplication.topLevelWidgets():
                try:
                    mb = widget.menuBar() if hasattr(widget, 'menuBar') else None
                    if isinstance(mb, QMenuBar) and mb.geometry().adjusted(-6, -6, 6, 6).contains(mb.mapFromGlobal(gp)):
                        return True
                except Exception:
                    pass
        except Exception:
            pass
        return False
    if not (
        hasattr(_BKStayOpenMenu53, '_cursor_on_known_trigger')
        and hasattr(_BKStayOpenMenu53, '_visible_child_menus')
    ):
        _BKStayOpenMenu53._cursor_inside_any_menu = staticmethod(_bk_fix53_cursor_inside_chain_or_menubar)
except Exception:
    pass
__all__ = [
    '_bk_fix53_adjust_recs_once',
    '_bk_fix53_clean_text',
    '_bk_fix53_grid_from_table_block',
    '_bk_fix53_image_size_from_task',
    '_bk_fix53_patch_status_method',
    '_bk_fix53_queue_index_for_text',
    '_bk_fix53_refresh_overlay_display',
    '_bk_fix53_sanitize_wait_text',
    '_bk_fix53_tr_queue_ref',
    '_bk_fix53_update_task_preset_bboxes',
    '_bk_fix53_write_csv',
]
register_globals('bk', globals(), __all__)
