from PySide6.QtCore import QPoint, QRect, QTimer
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication, QMenu
class BKStayOpenMenu(QMenu):
    _BK_CLOSE_INTERVAL_MS = 120
    _BK_CLOSE_GRACE_TICKS = 2
    _BK_HIT_PADDING = 5
    _BK_BRIDGE_PADDING = 10
    _BK_MIN_WIDTH = 140
    _BK_SCREEN_MARGIN = 80
    _BK_TEXT_PADDING = 56
    _BK_MENU_STYLE = """
        QMenu {
            padding: 2px 2px 2px 2px;
        }
        QMenu::item {
            padding: 5px 28px 5px 22px;
        }
        QMenu::item:selected {
            padding: 5px 28px 5px 22px;
        }
        QMenu::indicator {
            width: 12px;
            height: 12px;
            left: 5px;
        }
        QMenu::right-arrow {
            width: 8px;
            height: 8px;
            right: 8px;
        }
        QMenu::separator {
            height: 1px;
            margin: 4px 7px 4px 7px;
        }
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bk_hover_close_timer = QTimer(self)
        self._bk_hover_close_timer.setInterval(self._BK_CLOSE_INTERVAL_MS)
        self._bk_hover_close_timer.timeout.connect(self._bk_check_hover_close)
        self._bk_outside_ticks = 0
        self._bk_last_popup_pos = None
        self._bk_apply_compact_style()
        try:
            self.setSeparatorsCollapsible(True)
            self.setToolTipsVisible(True)
        except Exception:
            pass
    def _bk_apply_compact_style(self) -> None:
        try:
            existing = self.styleSheet().strip()
            compact = self._BK_MENU_STYLE.strip()
            if compact not in existing:
                self.setStyleSheet((existing + "\n" + compact).strip())
        except Exception:
            pass
    @staticmethod
    def _dedupe_menus(menus):
        result = []
        seen = set()
        for menu in menus or []:
            if not isinstance(menu, QMenu):
                continue
            key = id(menu)
            if key in seen:
                continue
            seen.add(key)
            result.append(menu)
        return result
    @staticmethod
    def _parent_menu(menu):
        try:
            parent = menu.parentWidget()
            return parent if isinstance(parent, QMenu) else None
        except Exception:
            return None
    def _ancestor_chain(self):
        chain = []
        menu = self
        while isinstance(menu, QMenu):
            chain.append(menu)
            menu = BKStayOpenMenu._parent_menu(menu)
        return BKStayOpenMenu._dedupe_menus(reversed(chain))
    @staticmethod
    def _visible_child_menus(menu):
        children = []
        try:
            for action in menu.actions():
                child = action.menu()
                if isinstance(child, QMenu) and child.isVisible():
                    children.append(child)
                    children.extend(BKStayOpenMenu._visible_child_menus(child))
        except Exception:
            pass
        return BKStayOpenMenu._dedupe_menus(children)
    def _menu_family(self):
        family = []
        for menu in self._ancestor_chain():
            family.append(menu)
            family.extend(BKStayOpenMenu._visible_child_menus(menu))
        return BKStayOpenMenu._dedupe_menus(family)
    @staticmethod
    def _remember_family_positions(family):
        for menu in family or []:
            try:
                menu._bk_last_popup_pos = menu.pos()
            except Exception:
                pass
        return family
    @staticmethod
    def _reopen_menu_family(family):
        for menu in family or []:
            try:
                pos = getattr(menu, "_bk_last_popup_pos", None)
                if pos is not None:
                    menu.popup(pos)
            except Exception:
                pass
    def _fit_to_contents(self) -> None:
        try:
            self._bk_apply_compact_style()
            self.ensurePolished()
            self.setMinimumWidth(0)
            self.setMaximumWidth(16777215)
        except Exception:
            pass
        try:
            fm = self.fontMetrics()
            text_width = 0
            for action in self.actions():
                if action.isSeparator():
                    continue
                label = action.text().replace("&", "")
                width = fm.horizontalAdvance(label)
                shortcut = action.shortcut()
                if shortcut and not shortcut.isEmpty():
                    width += fm.horizontalAdvance(shortcut.toString()) + 32
                if action.menu() is not None:
                    width += 18
                text_width = max(text_width, width)
            hint_width = max(self.sizeHint().width(), text_width + self._BK_TEXT_PADDING)
            screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
            if screen is not None:
                max_width = max(self._BK_MIN_WIDTH, screen.availableGeometry().width() - self._BK_SCREEN_MARGIN)
                hint_width = min(hint_width, max_width)
            self.setMinimumWidth(max(self._BK_MIN_WIDTH, int(hint_width)))
            self.updateGeometry()
            self.adjustSize()
        except Exception:
            pass
    @staticmethod
    def _global_widget_rect(widget):
        try:
            top_left = widget.mapToGlobal(QPoint(0, 0))
            return QRect(top_left, widget.size())
        except Exception:
            return None
    @staticmethod
    def _cursor_inside_menu_window(menu, global_pos):
        try:
            if isinstance(menu, QMenu) and menu.isVisible():
                pad = BKStayOpenMenu._BK_HIT_PADDING
                return menu.geometry().adjusted(-pad, -pad, pad, pad).contains(global_pos)
        except Exception:
            pass
        return False
    @staticmethod
    def _action_rect_in_widget(action, widget):
        try:
            if widget is None or not hasattr(widget, "actionGeometry"):
                return None
            rect = widget.actionGeometry(action)
            if not rect.isValid():
                return None
            return QRect(widget.mapToGlobal(rect.topLeft()), rect.size())
        except Exception:
            return None
    @staticmethod
    def _cursor_on_qmenubar_action(menu, widget, global_pos):
        try:
            rect = BKStayOpenMenu._action_rect_in_widget(menu.menuAction(), widget)
            if rect is None:
                return False
            pad = BKStayOpenMenu._BK_HIT_PADDING
            return rect.adjusted(-pad, -pad, pad, pad).contains(global_pos)
        except Exception:
            return False
    @staticmethod
    def _cursor_on_qtoolbutton_menu(menu, widget, global_pos):
        try:
            if widget is None or not hasattr(widget, "menu"):
                return False
            if widget.menu() is not menu:
                return False
            rect = BKStayOpenMenu._global_widget_rect(widget)
            if rect is None:
                return False
            pad = BKStayOpenMenu._BK_HIT_PADDING
            return rect.adjusted(-pad, -pad, pad, pad).contains(global_pos)
        except Exception:
            return False
    @staticmethod
    def _cursor_on_parent_menu_action(menu, global_pos):
        try:
            parent = BKStayOpenMenu._parent_menu(menu)
            if not isinstance(parent, QMenu):
                return False
            rect = BKStayOpenMenu._action_rect_in_widget(menu.menuAction(), parent)
            if rect is None:
                return False
            pad = BKStayOpenMenu._BK_HIT_PADDING
            return rect.adjusted(-pad, -pad, pad, pad).contains(global_pos)
        except Exception:
            return False
    @staticmethod
    def _cursor_between_parent_action_and_submenu(menu, global_pos):
        try:
            parent = BKStayOpenMenu._parent_menu(menu)
            if not isinstance(parent, QMenu) or not menu.isVisible():
                return False
            action_rect = BKStayOpenMenu._action_rect_in_widget(menu.menuAction(), parent)
            menu_rect = menu.geometry()
            if action_rect is None or not menu_rect.isValid():
                return False
            left = min(action_rect.left(), menu_rect.left())
            top = min(action_rect.top(), menu_rect.top())
            right = max(action_rect.right(), menu_rect.right())
            bottom = max(action_rect.bottom(), menu_rect.bottom())
            pad = BKStayOpenMenu._BK_BRIDGE_PADDING
            bridge = QRect(QPoint(left, top), QPoint(right, bottom)).adjusted(-pad, -pad, pad, pad)
            return bridge.contains(global_pos)
        except Exception:
            return False
    @staticmethod
    def _associated_widgets(action):
        try:
            widgets = action.associatedObjects()
            if isinstance(widgets, (list, tuple)):
                return widgets
            return list(widgets)
        except Exception:
            return []
    @staticmethod
    def _cursor_on_known_trigger(menu, global_pos):
        try:
            action = menu.menuAction()
        except Exception:
            return False
        if BKStayOpenMenu._cursor_on_parent_menu_action(menu, global_pos):
            return True
        if BKStayOpenMenu._cursor_between_parent_action_and_submenu(menu, global_pos):
            return True
        for widget in BKStayOpenMenu._associated_widgets(action):
            if BKStayOpenMenu._cursor_on_qmenubar_action(menu, widget, global_pos):
                return True
            if BKStayOpenMenu._cursor_on_qtoolbutton_menu(menu, widget, global_pos):
                return True
        try:
            widget = QApplication.widgetAt(global_pos)
        except Exception:
            widget = None
        while widget is not None:
            if BKStayOpenMenu._cursor_on_qmenubar_action(menu, widget, global_pos):
                return True
            if BKStayOpenMenu._cursor_on_qtoolbutton_menu(menu, widget, global_pos):
                return True
            try:
                widget = widget.parentWidget()
            except Exception:
                break
        return False
    @staticmethod
    def _cursor_inside_any_menu(family):
        try:
            global_pos = QCursor.pos()
            for menu in family or []:
                if BKStayOpenMenu._cursor_inside_menu_window(menu, global_pos):
                    return True
                if BKStayOpenMenu._cursor_on_known_trigger(menu, global_pos):
                    return True
        except Exception:
            pass
        return False
    @staticmethod
    def _close_family_if_cursor_outside(family, force=False):
        try:
            family = BKStayOpenMenu._dedupe_menus(family)
            if not force and BKStayOpenMenu._cursor_inside_any_menu(family):
                return False
            for menu in reversed(family):
                if isinstance(menu, QMenu):
                    menu.close()
            return True
        except Exception:
            return False
    def _bk_check_hover_close(self) -> None:
        family = self._menu_family()
        if BKStayOpenMenu._cursor_inside_any_menu(family):
            self._bk_outside_ticks = 0
            return
        self._bk_outside_ticks += 1
        if self._bk_outside_ticks >= self._BK_CLOSE_GRACE_TICKS:
            BKStayOpenMenu._close_family_if_cursor_outside(family, force=True)
    def leaveEvent(self, event):
        try:
            family = self._menu_family()
            QTimer.singleShot(
                self._BK_CLOSE_INTERVAL_MS,
                lambda fam=family: BKStayOpenMenu._close_family_if_cursor_outside(fam),
            )
        except Exception:
            pass
        return super().leaveEvent(event)
    def showEvent(self, event):
        try:
            self._bk_last_popup_pos = self.pos()
            self._bk_outside_ticks = 0
            self._fit_to_contents()
            if not self._bk_hover_close_timer.isActive():
                self._bk_hover_close_timer.start()
        except Exception:
            pass
        super().showEvent(event)
    def hideEvent(self, event):
        try:
            self._bk_hover_close_timer.stop()
            self._bk_outside_ticks = 0
        except Exception:
            pass
        super().hideEvent(event)
    def popup(self, pos, action=None):
        try:
            self._bk_last_popup_pos = pos
            self._bk_outside_ticks = 0
            self._fit_to_contents()
        except Exception:
            pass
        return super().popup(pos, action)
    def mouseReleaseEvent(self, event):
        action = self.activeAction()
        if action is None or not action.isEnabled() or action.isSeparator():
            return super().mouseReleaseEvent(event)
        if action.menu() is not None:
            return super().mouseReleaseEvent(event)
        family = BKStayOpenMenu._remember_family_positions(self._menu_family())
        try:
            action.trigger()
            event.accept()
            for delay in (0, 25, 90):
                QTimer.singleShot(delay, lambda fam=family: BKStayOpenMenu._reopen_menu_family(fam))
            return
        except Exception:
            return super().mouseReleaseEvent(event)
