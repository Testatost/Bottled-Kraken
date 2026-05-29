try:
    from PySide6.QtCore import QSize, QTimer, Qt
    from PySide6.QtWidgets import QMenu, QTabBar, QToolButton
except Exception:
    QSize = None
    QTimer = None
    Qt = None
    QMenu = None
    QToolButton = None
    QTabBar = object
try:
    from bottled_kraken._main_window.ocr_tab_name_utils import plain_ocr_tab_text
except Exception:
    def plain_ocr_tab_text(text: str) -> str:
        value = str(text or "").strip()
        return value[:-1].rstrip() if value.endswith("×") else value
class OCRVariantTabBar(QTabBar):
    _CTRL_W = 108
    def __init__(self, owner=None, parent=None):
        super().__init__(parent)
        self._ocr_variant_owner = owner
        self._manual_scroll_buttons_ready = False
        self._overflow_first_visible = 0
        self._overflow_last_visible = -1
        self._overflow_syncing = False
        self._overflow_hidden_indices = set()
        self._overflow_layout_dirty = False
        try:
            self.setContextMenuPolicy(Qt.CustomContextMenu if Qt is not None else 3)
            self.customContextMenuRequested.connect(self._show_context_menu)
            self.setTabsClosable(False)
            self.setUsesScrollButtons(False)
            self.setElideMode(Qt.ElideNone)
            self.setExpanding(False)
            self.setSelectionBehaviorOnRemove(QTabBar.SelectPreviousTab)
        except Exception:
            pass
        self._ensure_manual_scroll_buttons()
    def _actions(self):
        from bottled_kraken._main_window import ocr_variant_tabs
        return ocr_variant_tabs
    def _is_plus_index(self, index: int) -> bool:
        try:
            return index >= 0 and (index == self.count() - 1 or plain_ocr_tab_text(self.tabText(index)) == "+")
        except Exception:
            return False
    def _ensure_manual_scroll_buttons(self):
        if self._manual_scroll_buttons_ready or QToolButton is None:
            return
        try:
            self._manual_plus_btn = QToolButton(self)
            self._overflow_more_btn = QToolButton(self)
            self._scroll_left_btn = QToolButton(self)
            self._scroll_right_btn = QToolButton(self)
            spec = ((self._manual_plus_btn, "+", 30), (self._overflow_more_btn, "[...]", 38), (self._scroll_left_btn, "←", 20), (self._scroll_right_btn, "→", 20))
            for button, text, width in spec:
                button.setText(text)
                button.setToolTip(text)
                button.setAutoRaise(False)
                button.setFixedSize(width, 22)
                button.setFocusPolicy(Qt.NoFocus if Qt is not None else 0)
                try:
                    button.setToolButtonStyle(Qt.ToolButtonTextOnly)
                except Exception:
                    pass
                button.setStyleSheet("QToolButton{padding:0;margin:0;font-weight:bold;} QToolButton:focus{outline:0;}")
                button.hide()
            self._overflow_more_btn.setEnabled(True)
            self._manual_plus_btn.clicked.connect(self._add_tab_from_button)
            self._overflow_more_btn.clicked.connect(self._show_overflow_tab_menu)
            self._scroll_left_btn.clicked.connect(lambda: self._scroll_visible_window(-1))
            self._scroll_right_btn.clicked.connect(lambda: self._scroll_visible_window(1))
            self.setStyleSheet((self.styleSheet() or "") + "\nQTabBar::scroller{width:0px;height:0px;}")
            self._manual_scroll_buttons_ready = True
        except Exception:
            self._manual_scroll_buttons_ready = False
    def _add_tab_from_button(self):
        owner = self._ocr_variant_owner
        if owner is None:
            return
        try:
            self._actions().add_ocr_variant_tab(owner)
        except Exception:
            pass
    def _base_tab_size_hint(self, index: int):
        try:
            return super().tabSizeHint(index)
        except Exception:
            if QSize is not None:
                return QSize(1, 22)
            raise
    def tabSizeHint(self, index):
        try:
            if int(index) in self._overflow_hidden_indices and QSize is not None:
                base = self._base_tab_size_hint(index)
                height = max(20, int(base.height()))
                return QSize(0, height)
        except Exception:
            pass
        return self._base_tab_size_hint(index)
    def minimumTabSizeHint(self, index):
        try:
            if int(index) in self._overflow_hidden_indices and QSize is not None:
                base = self._base_tab_size_hint(index)
                height = max(20, int(base.height()))
                return QSize(0, height)
        except Exception:
            pass
        try:
            return super().minimumTabSizeHint(index)
        except Exception:
            return self._base_tab_size_hint(index)
    def _natural_tab_width(self, index: int) -> int:
        width = 1
        try:
            width = max(width, int(self._base_tab_size_hint(index).width()))
        except Exception:
            pass
        try:
            width = max(width, int(self.fontMetrics().horizontalAdvance(self.tabText(index))) + 34)
        except Exception:
            pass
        return max(1, width)
    def _set_tab_visible_safe(self, index: int, visible: bool) -> None:
        try:
            index = int(index)
        except Exception:
            return
        try:
            before = set(self._overflow_hidden_indices)
            if visible:
                self._overflow_hidden_indices.discard(index)
            else:
                self._overflow_hidden_indices.add(index)
            self._overflow_layout_dirty = self._overflow_layout_dirty or before != self._overflow_hidden_indices
            for side in (QTabBar.LeftSide, QTabBar.RightSide):
                try:
                    button = self.tabButton(index, side)
                    if button is not None:
                        button.setVisible(bool(visible))
                except Exception:
                    pass
        except Exception:
            pass
    def _force_overflow_layout_refresh(self) -> None:
        if not getattr(self, "_overflow_layout_dirty", False):
            try:
                self.updateGeometry()
                self.update()
            except Exception:
                pass
            return
        self._overflow_layout_dirty = False
        try:
            self.updateGeometry()
            self.update()
        except Exception:
            pass
        try:
            self.tabLayoutChange()
        except Exception:
            pass
        try:
            mode = self.elideMode()
            if Qt is not None:
                self.setElideMode(Qt.ElideRight)
            self.setElideMode(mode)
        except Exception:
            pass
        try:
            text_index = self._overflow_first_visible
            if 0 <= text_index < self.count():
                text = self.tabText(text_index)
                self.setTabText(text_index, text + "\u200b")
                self.setTabText(text_index, text)
        except Exception:
            pass
        try:
            self.repaint()
        except Exception:
            pass
        if QTimer is not None:
            try:
                QTimer.singleShot(0, self.updateGeometry)
                QTimer.singleShot(0, self.update)
            except Exception:
                pass
    def _tabs_overflow(self) -> bool:
        try:
            total = sum(self._natural_tab_width(i) for i in range(self.count()))
            return total > max(1, self.width() - 2)
        except Exception:
            return False
    def _available_tab_width(self) -> int:
        try:
            return max(1, int(self.width()) - self._CTRL_W - 2)
        except Exception:
            return 1
    def _fit_end(self, start: int, real_count: int, available: int) -> int:
        if real_count <= 0:
            return -1
        start = max(0, min(int(start or 0), real_count - 1))
        used = 0
        end = start
        for i in range(start, real_count):
            width = self._natural_tab_width(i)
            if i > start and used + width > available:
                break
            used += width
            end = i
            if used >= available:
                break
        return max(start, min(end, real_count - 1))
    def _best_start_for_end(self, end: int, real_count: int, available: int) -> int:
        if real_count <= 0:
            return 0
        end = max(0, min(int(end or 0), real_count - 1))
        used = 0
        start = end
        for i in range(end, -1, -1):
            width = self._natural_tab_width(i)
            if i < end and used + width > available:
                break
            used += width
            start = i
            if used >= available:
                break
        return max(0, min(start, end))
    def _max_scroll_start(self, real_count: int, available: int) -> int:
        if real_count <= 0:
            return 0
        return self._best_start_for_end(real_count - 1, real_count, available)
    def _clamped_overflow_start(self, start: int, real_count: int, available: int) -> int:
        max_start = self._max_scroll_start(real_count, available)
        try:
            start = int(start or 0)
        except Exception:
            start = 0
        return max(0, min(start, max_start))
    def _sync_visible_overflow_tabs(self, overflow: bool, ensure_current: bool = True) -> None:
        if self._overflow_syncing:
            return
        self._overflow_syncing = True
        try:
            plus = self.count() - 1
            real_count = max(0, plus)
            if not overflow or real_count <= 0:
                for i in range(self.count()):
                    self._set_tab_visible_safe(i, True)
                self._overflow_first_visible = 0
                self._overflow_last_visible = real_count - 1
                self._force_overflow_layout_refresh()
                return
            available = self._available_tab_width()
            start = self._clamped_overflow_start(self._overflow_first_visible, real_count, available)
            if ensure_current:
                current = self.currentIndex()
                if current < 0 or current >= real_count:
                    current = start
                current = max(0, min(int(current or 0), real_count - 1))
                end = self._fit_end(start, real_count, available)
                if current < start:
                    start = current
                elif current > end:
                    start = self._best_start_for_end(current, real_count, available)
                start = self._clamped_overflow_start(start, real_count, available)
            end = self._fit_end(start, real_count, available)
            for i in range(real_count):
                self._set_tab_visible_safe(i, start <= i <= end)
            self._set_tab_visible_safe(plus, False)
            self._overflow_first_visible = start
            self._overflow_last_visible = end
            self._force_overflow_layout_refresh()
        finally:
            self._overflow_syncing = False
    def _hide_native_scroll_buttons(self):
        manual = {getattr(self, name, None) for name in ("_manual_plus_btn", "_overflow_more_btn", "_scroll_left_btn", "_scroll_right_btn")}
        try:
            buttons = [b for b in self.findChildren(QToolButton) if b not in manual]
        except Exception:
            buttons = []
        for button in buttons:
            try:
                button.setVisible(False)
                button.setEnabled(False)
                button.resize(0, 0)
            except Exception:
                pass
    def _show_manual_scroll_buttons(self, show: bool) -> None:
        if not self._manual_scroll_buttons_ready:
            return
        try:
            height = max(20, min(24, self.height() - 2))
            y = max(0, (self.height() - height) // 2)
            x = max(1, self.width() - self._CTRL_W)
            widths = (30, 38, 20, 20)
            buttons = (self._manual_plus_btn, self._overflow_more_btn, self._scroll_left_btn, self._scroll_right_btn)
            for button, width in zip(buttons, widths):
                button.setFixedSize(width, height)
                button.move(x, y)
                button.setVisible(bool(show))
                button.raise_()
                x += width
        except Exception:
            pass
    def _update_scroll_arrow_buttons(self, ensure_current: bool = True) -> None:
        self._ensure_manual_scroll_buttons()
        self._hide_native_scroll_buttons()
        overflow = self._tabs_overflow()
        self._sync_visible_overflow_tabs(overflow, ensure_current=ensure_current)
        self._show_manual_scroll_buttons(overflow)
        try:
            last_real = max(0, self.count() - 2)
            self._scroll_left_btn.setEnabled(overflow and self._overflow_first_visible > 0)
            self._scroll_right_btn.setEnabled(overflow and self._overflow_last_visible < last_real)
            self._force_overflow_layout_refresh()
        except Exception:
            pass
    def _show_overflow_tab_menu(self):
        if self._ocr_variant_owner is None or QMenu is None:
            return
        menu = QMenu(self)
        real_count = max(0, self.count() - 1)
        if real_count <= 0: return
        for index in range(real_count):
            action = menu.addAction(plain_ocr_tab_text(self.tabText(index)) or str(index + 1))
            action.setCheckable(True); action.setChecked(index == self.currentIndex()); action.setData(index)
        chosen = menu.exec(self._overflow_more_btn.mapToGlobal(self._overflow_more_btn.rect().bottomLeft()))
        if chosen is None: return
        index = int(chosen.data())
        if not (0 <= index < real_count): return
        available = self._available_tab_width()
        start = self._overflow_first_visible
        end = self._fit_end(start, real_count, available)
        if index < start: start = index
        elif index > end: start = self._best_start_for_end(index, real_count, available)
        self._overflow_first_visible = self._clamped_overflow_start(start, real_count, available)
        self.setCurrentIndex(index); self._update_scroll_arrow_buttons(ensure_current=True)
    def _scroll_visible_window(self, step: int) -> None:
        try:
            real_count = max(0, self.count() - 1)
            if real_count <= 0:
                return
            available = self._available_tab_width()
            start = self._clamped_overflow_start(self._overflow_first_visible + int(step or 0), real_count, available)
            self._overflow_first_visible = start
        except Exception:
            pass
        self._update_scroll_arrow_buttons(ensure_current=False)
    def _show_context_menu(self, pos):
        owner = self._ocr_variant_owner
        if owner is None or QMenu is None:
            return
        try:
            index = self.tabAt(pos)
        except Exception:
            index = -1
        if index < 0 or self._is_plus_index(index):
            return
        menu = QMenu(self)
        try:
            rename_text = owner._tr("multi_ocr_variant_rename_action")
            delete_text = owner._tr("multi_ocr_variant_delete_tab")
        except Exception:
            rename_text = "Rename OCR tab"
            delete_text = "Delete OCR tab"
        rename_action = menu.addAction(rename_text)
        delete_action = menu.addAction(delete_text)
        chosen = menu.exec(self.mapToGlobal(pos))
        if chosen == rename_action:
            self._actions().rename_ocr_variant_tab(owner, index)
        elif chosen == delete_action:
            self._actions().delete_ocr_variant_tab(owner, index)
    def _handle_plus_at_pos(self, pos) -> bool:
        try:
            index = self.tabAt(pos)
        except Exception:
            index = -1
        if self._ocr_variant_owner is not None and self._is_plus_index(index):
            self._actions().add_ocr_variant_tab(self._ocr_variant_owner)
            return True
        return False
    def _is_right_button(self, event) -> bool:
        try:
            return Qt is not None and event.button() == Qt.RightButton
        except Exception:
            return False
    def mousePressEvent(self, event):
        if self._is_right_button(event):
            try:
                self._show_context_menu(event.pos())
                event.accept()
            except Exception:
                pass
            return
        super().mousePressEvent(event)
    def mouseReleaseEvent(self, event):
        if self._is_right_button(event):
            try:
                event.accept()
            except Exception:
                pass
            return
        if self._handle_plus_at_pos(event.pos()):
            try:
                event.accept()
            except Exception:
                pass
            return
        super().mouseReleaseEvent(event)
        self._update_scroll_arrow_buttons(ensure_current=True)
    def mouseDoubleClickEvent(self, event):
        try:
            index = self.tabAt(event.pos())
        except Exception:
            index = -1
        if self._ocr_variant_owner is not None and index >= 0 and not self._is_plus_index(index):
            self._actions().rename_ocr_variant_tab(self._ocr_variant_owner, index)
            try:
                event.accept()
            except Exception:
                pass
            return
        super().mouseDoubleClickEvent(event)
    def keyPressEvent(self, event):
        try:
            if Qt is not None and event.key() == Qt.Key_F2 and self._ocr_variant_owner is not None:
                index = self.currentIndex()
                if index >= 0 and not self._is_plus_index(index):
                    self._actions().rename_ocr_variant_tab(self._ocr_variant_owner, index)
                    event.accept()
                    return
        except Exception:
            pass
        super().keyPressEvent(event)
    def tabInserted(self, index):
        try:
            super().tabInserted(index)
        except Exception:
            pass
        self._overflow_first_visible = max(0, min(self._overflow_first_visible, max(0, self.count() - 2)))
        owner = self._ocr_variant_owner
        if owner is not None:
            QTimer.singleShot(0, lambda: self._actions().configure_ocr_variant_tab_buttons(owner)) if QTimer is not None else self._actions().configure_ocr_variant_tab_buttons(owner)
    def tabRemoved(self, index):
        try:
            super().tabRemoved(index)
        except Exception:
            pass
        self._overflow_first_visible = max(0, min(self._overflow_first_visible, max(0, self.count() - 2)))
        owner = self._ocr_variant_owner
        if owner is not None:
            QTimer.singleShot(0, lambda: self._actions().configure_ocr_variant_tab_buttons(owner)) if QTimer is not None else self._actions().configure_ocr_variant_tab_buttons(owner)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scroll_arrow_buttons()
    def showEvent(self, event):
        super().showEvent(event)
        self._update_scroll_arrow_buttons()
