from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('ptr', globals())
from typing import Any, Dict, List, Optional, Tuple
def _ptr_make_multi_ocr_icon(window, size: int = 16) -> QIcon:
    color = QColor("#ffffff") if _ptr_is_dark_theme(window) else QColor("#000000")
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing, True)
    pen = QPen(color, max(1, int(round(size * 0.11))), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    painter.drawRoundedRect(QRectF(size * 0.12, size * 0.16, size * 0.34, size * 0.22), 1.5, 1.5)
    painter.drawRoundedRect(QRectF(size * 0.52, size * 0.39, size * 0.34, size * 0.22), 1.5, 1.5)
    painter.drawRoundedRect(QRectF(size * 0.12, size * 0.66, size * 0.34, size * 0.22), 1.5, 1.5)
    painter.setBrush(color)
    painter.setPen(Qt.NoPen)
    r = max(1.1, size * 0.08)
    painter.drawEllipse(QPointF(size * 0.50, size * 0.27), r, r)
    painter.drawEllipse(QPointF(size * 0.49, size * 0.77), r, r)
    painter.end()
    icon = QIcon()
    for mode in (QIcon.Normal, QIcon.Active, QIcon.Selected, QIcon.Disabled):
        icon.addPixmap(pix, mode, QIcon.Off)
        icon.addPixmap(pix, mode, QIcon.On)
    return icon
def _ptr_apply_new_button_icons(window):
    try:
        if hasattr(window, "btn_ptr_multi_ocr_bottom"):
            window.btn_ptr_multi_ocr_bottom.setIcon(_ptr_make_multi_ocr_icon(window, 16))
        if hasattr(window, "btn_ptr_openrouter_ai_bottom"):
            window.btn_ptr_openrouter_ai_bottom.setIcon(
                _ptr_plain_theme_or_standard_icon(window, "preferences-system", QStyle.SP_ComputerIcon)
            )
    except Exception:
        pass
def _ptr_rebuild_secondary_button_rows(window):
    if getattr(window, "_ptr_bottom_rows_built", False):
        return
    if not hasattr(window, "splitter") or window.splitter.count() < 2:
        return
    right_widget = window.splitter.widget(1)
    right_layout = right_widget.layout() if right_widget is not None else None
    if right_layout is None:
        return
    window._ptr_bottom_rows_built = True
    if not hasattr(window, "btn_ptr_multi_ocr_bottom"):
        window.btn_ptr_multi_ocr_bottom = QToolButton()
        window.btn_ptr_multi_ocr_bottom.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        window.btn_ptr_multi_ocr_bottom.clicked.connect(window.ptr_start_multi_ocr)
    if not hasattr(window, "btn_ptr_openrouter_ai_bottom"):
        window.btn_ptr_openrouter_ai_bottom = QToolButton()
        window.btn_ptr_openrouter_ai_bottom.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        window.btn_ptr_openrouter_ai_bottom.clicked.connect(window.ptr_open_ai_tools_for_current_task)
    old_lines_layout = None
    old_index = None
    existing_buttons = [
        getattr(window, "btn_import_lines", None),
        getattr(window, "btn_voice_fill", None),
        getattr(window, "btn_ai_revise_bottom", None),
        getattr(window, "btn_line_search", None),
        getattr(window, "line_search_button_panel", None),
        getattr(window, "line_search_inline_panel", None),
    ]
    for i in range(right_layout.count()):
        item = right_layout.itemAt(i)
        lay = item.layout() if item is not None else None
        if lay is None:
            continue
        try:
            if any(btn is not None and lay.indexOf(btn) != -1 for btn in existing_buttons):
                old_lines_layout = lay
                old_index = i
                break
        except Exception:
            continue
    container = QWidget(right_widget)
    outer = QVBoxLayout(container)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(6)
    row1 = QHBoxLayout()
    row1.setContentsMargins(0, 0, 0, 0)
    row1.setSpacing(6)
    row2 = QHBoxLayout()
    row2.setContentsMargins(0, 0, 0, 0)
    row2.setSpacing(6)
    row1.addWidget(window.btn_import_lines)
    row1.addWidget(window.btn_voice_fill)
    search_widget = getattr(window, "line_search_button_panel", window.btn_line_search)
    row1.addWidget(search_widget, 0, Qt.AlignTop)
    row1.addStretch(1)
    row2.addWidget(window.btn_ai_revise_bottom)
    row2.addWidget(window.btn_ptr_multi_ocr_bottom)
    row2.addWidget(window.btn_ptr_openrouter_ai_bottom)
    row2.addStretch(1)
    outer.addLayout(row1)
    outer.addLayout(row2)
    search_inline_panel = getattr(window, "line_search_inline_panel", None)
    if search_inline_panel is not None:
        outer.addWidget(search_inline_panel)
    if old_lines_layout is not None:
        try:
            old_lines_layout.setContentsMargins(0, 0, 0, 0)
            old_lines_layout.setSpacing(0)
        except Exception:
            pass
        insert_index = old_index if isinstance(old_index, int) else max(0, right_layout.count() - 1)
        right_layout.insertWidget(insert_index, container)
    else:
        right_layout.addWidget(container)
    _ptr_update_feature_texts_v2(window)
    _ptr_apply_new_button_icons(window)
try:
    _PTR_PREV_APPLY_THEME_MULTI_OCR_ICON_V2
except NameError:
    _PTR_PREV_APPLY_THEME_MULTI_OCR_ICON_V2 = MainWindow.apply_theme
    def _ptr_apply_theme_multi_ocr_icon_wrapper_v2(self, theme: str):
        result = _PTR_PREV_APPLY_THEME_MULTI_OCR_ICON_V2(self, theme)
        try:
            _ptr_apply_new_button_icons(self)
        except Exception:
            pass
        return result
    MainWindow.apply_theme = _ptr_apply_theme_multi_ocr_icon_wrapper_v2
__all__ = [
    '_ptr_apply_new_button_icons',
    '_ptr_make_multi_ocr_icon',
    '_ptr_rebuild_secondary_button_rows',
]
register_globals('ptr', globals(), __all__)
