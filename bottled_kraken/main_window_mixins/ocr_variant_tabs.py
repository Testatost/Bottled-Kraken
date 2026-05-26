"""OCR variant tab helpers for the main window."""
try:
    from PySide6.QtCore import QEvent, QTimer, Qt
    from PySide6.QtWidgets import QInputDialog, QLineEdit, QMenu, QTabBar, QToolButton
except Exception:  # pragma: no cover
    QEvent = None
    QTimer = None
    Qt = None
    QInputDialog = None
    QLineEdit = None
    QMenu = None
    QToolButton = None
    QTabBar = object
try:
    from .ocr_tab_close_widget import OCRTabCloseWidget
    from .ocr_tab_name_utils import plain_ocr_tab_text
except Exception:  # pragma: no cover
    OCRTabCloseWidget = None
    def plain_ocr_tab_text(text: str) -> str:
        value = str(text or "").strip()
        return value[:-1].rstrip() if value.endswith("×") else value
OCR_TAB_CLOSE_MARK = "×"
def ocr_variant_tab_label(window, index: int) -> str:
    try:
        return window._tr("multi_ocr_variant_tab", int(index) + 1)
    except Exception:
        return f"Tab ({int(index) + 1})"
def current_ocr_variant_path(window) -> str:
    try:
        task = window._current_task() if hasattr(window, "_current_task") else None
        path = str(getattr(task, "path", "") or "") if task is not None else ""
        if path:
            return path
    except Exception:
        pass
    return str(getattr(window, "_loaded_preview_path", "") or "")
def ocr_variant_tab_plain_text(text: str) -> str:
    return plain_ocr_tab_text(text)
def ocr_variant_tab_display_text(label: str) -> str:
    return plain_ocr_tab_text(label) or "+"
def _ocr_variant_next_generated_label(window, tabs) -> str:
    max_number = 0
    real_count = 0
    try:
        for i in range(max(0, tabs.count() - 1)):
            real_count += 1
            text = plain_ocr_tab_text(tabs.tabText(i))
            try:
                max_number = max(max_number, int(text.rsplit("(", 1)[1].split(")", 1)[0].strip()))
            except Exception:
                pass
    except Exception:
        pass
    return ocr_variant_tab_label(window, max(max_number, real_count))
def _is_plus_tab(tabs, index: int) -> bool:
    try:
        return tabs is not None and index >= 0 and (
            plain_ocr_tab_text(tabs.tabText(index)) == "+" or index == tabs.count() - 1
        )
    except Exception:
        return False
def _hide_tab_close_button(tabs, index: int) -> None:
    try:
        tabs.setTabButton(index, QTabBar.RightSide, None)
        tabs.setTabButton(index, QTabBar.LeftSide, None)
    except Exception:
        pass
def _install_tab_close_button(window, tabs, index: int) -> None:
    if tabs is None or _is_plus_tab(tabs, index) or OCRTabCloseWidget is None:
        return
    try:
        old = tabs.tabButton(index, QTabBar.RightSide)
        if isinstance(old, OCRTabCloseWidget):
            return
    except Exception:
        pass
    try:
        tooltip = window._tr("multi_ocr_variant_delete_tab")
    except Exception:
        tooltip = "Delete OCR tab"
    try:
        button = OCRTabCloseWidget(tabs, lambda idx: delete_ocr_variant_tab(window, idx), tooltip, tabs)
        tabs.setTabButton(index, QTabBar.RightSide, button)
    except Exception:
        pass
def set_ocr_variant_tab_text(tabs, index: int, label: str) -> None:
    try:
        tabs.setTabText(index, ocr_variant_tab_display_text(label))
        tabs.setTabToolTip(index, str(label or "").strip())
    except Exception:
        pass
def _set_plus_tab_text(window, tabs) -> None:
    try:
        plus = tabs.count() - 1
        if plus < 0:
            return
        tabs.setTabText(plus, "+")
        try:
            tabs.setTabToolTip(plus, window._tr("multi_ocr_variant_add_tooltip"))
        except Exception:
            tabs.setTabToolTip(plus, "+")
        _hide_tab_close_button(tabs, plus)
    except Exception:
        pass
def _configure_tab_bar_basics(tabs) -> None:
    try:
        tabs.setTabsClosable(False)
        tabs.setUsesScrollButtons(False)
        tabs.setElideMode(Qt.ElideNone)
        tabs.setExpanding(False)
    except Exception:
        pass
    try:
        tabs.setSelectionBehaviorOnRemove(QTabBar.SelectPreviousTab)
    except Exception:
        pass
def configure_ocr_variant_tab_buttons(window) -> None:
    tabs = getattr(window, "ocr_variant_tabs", None)
    if tabs is None:
        return
    try:
        _configure_tab_bar_basics(tabs)
        for index in range(tabs.count()):
            if _is_plus_tab(tabs, index):
                _hide_tab_close_button(tabs, index)
            else:
                try:
                    tabs.setTabButton(index, QTabBar.LeftSide, None)
                except Exception:
                    pass
                _install_tab_close_button(window, tabs, index)
        tabs.updateGeometry()
        tabs.update()
    except Exception:
        pass
    try:
        if hasattr(tabs, "_update_scroll_arrow_buttons"):
            tabs._update_scroll_arrow_buttons()
    except Exception:
        pass
def refresh_ocr_variant_tab_texts(window) -> None:
    tabs = getattr(window, "ocr_variant_tabs", None)
    if tabs is None:
        return
    refresh = getattr(window, "_ptr_show_multi_ocr_variant_tabs", None)
    if callable(refresh) and not getattr(window, "_ocr_variant_core_refreshing", False):
        try:
            window._ocr_variant_core_refreshing = True
            refresh(current_ocr_variant_path(window))
            configure_ocr_variant_tab_buttons(window)
            return
        except Exception:
            pass
        finally:
            window._ocr_variant_core_refreshing = False
    try:
        if tabs.count() <= 0:
            first = tabs.addTab(ocr_variant_tab_label(window, 0))
            tabs.setTabToolTip(first, ocr_variant_tab_label(window, 0))
            tabs.addTab("+")
        elif plain_ocr_tab_text(tabs.tabText(tabs.count() - 1)) != "+":
            tabs.addTab("+")
        for index in range(max(0, tabs.count() - 1)):
            set_ocr_variant_tab_text(tabs, index, ocr_variant_tab_label(window, index))
        _set_plus_tab_text(window, tabs)
        configure_ocr_variant_tab_buttons(window)
    except Exception:
        pass
def _current_real_tab_index(tabs, preferred: int) -> int:
    try:
        last = tabs.count() - 2
        return max(0, min(int(preferred), last))
    except Exception:
        return 0
def delete_ocr_variant_tab(window, index: int) -> None:
    tabs = getattr(window, "ocr_variant_tabs", None)
    if tabs is None or index < 0 or _is_plus_tab(tabs, index):
        return
    delete_variant = getattr(window, "_ptr_delete_ocr_variant_tab", None)
    if callable(delete_variant):
        try:
            if delete_variant(int(index)) is True:
                configure_ocr_variant_tab_buttons(window)
                try:
                    tabs.setCurrentIndex(_current_real_tab_index(tabs, tabs.currentIndex()))
                except Exception:
                    pass
                return
        except Exception:
            pass
    try:
        if tabs.count() <= 2:
            label = ocr_variant_tab_label(window, 0)
            set_ocr_variant_tab_text(tabs, 0, label)
            tabs.setCurrentIndex(0)
        else:
            tabs.removeTab(index)
            if tabs.count() <= 0 or plain_ocr_tab_text(tabs.tabText(tabs.count() - 1)) != "+":
                tabs.addTab("+")
            for tab_index in range(max(0, tabs.count() - 1)):
                set_ocr_variant_tab_text(tabs, tab_index, ocr_variant_tab_label(window, tab_index))
            _set_plus_tab_text(window, tabs)
            tabs.setCurrentIndex(_current_real_tab_index(tabs, index))
        configure_ocr_variant_tab_buttons(window)
    except Exception:
        pass
def rename_ocr_variant_tab(window, index: int) -> None:
    tabs = getattr(window, "ocr_variant_tabs", None)
    if tabs is None or index < 0 or _is_plus_tab(tabs, index) or QInputDialog is None:
        return
    current = plain_ocr_tab_text(tabs.tabText(index))
    try:
        title = window._tr("multi_ocr_variant_rename_title")
        label = window._tr("multi_ocr_variant_rename_label")
    except Exception:
        title = "Rename OCR tab"
        label = "New tab name:"
    try:
        mode = QLineEdit.Normal if QLineEdit is not None else 0
        text, ok = QInputDialog.getText(window, title, label, mode, current)
    except Exception:
        return
    new_name = str(text or "").strip() if ok else ""
    if not new_name:
        return
    rename_variant = getattr(window, "_ptr_rename_ocr_variant_tab", None)
    if callable(rename_variant):
        try:
            if rename_variant(index, new_name) is True:
                configure_ocr_variant_tab_buttons(window)
                return
        except Exception:
            pass
    try:
        set_ocr_variant_tab_text(tabs, index, new_name)
        configure_ocr_variant_tab_buttons(window)
    except Exception:
        pass
def add_ocr_variant_tab(window) -> None:
    tabs = getattr(window, "ocr_variant_tabs", None)
    if tabs is None or getattr(window, "_ocr_variant_plus_handling", False):
        return
    window._ocr_variant_plus_handling = True
    try:
        path = current_ocr_variant_path(window)
        before = tabs.count()
        add_variant = getattr(window, "_ptr_add_ocr_variant_tab", None)
        if callable(add_variant) and path:
            try:
                if add_variant(path) is True or tabs.count() > before:
                    configure_ocr_variant_tab_buttons(window)
                    return
            except Exception:
                pass
        if tabs.count() <= 0:
            tabs.addTab(ocr_variant_tab_label(window, 0))
            tabs.addTab("+")
        elif plain_ocr_tab_text(tabs.tabText(tabs.count() - 1)) != "+":
            tabs.addTab("+")
        insert_at = max(0, tabs.count() - 1)
        label = _ocr_variant_next_generated_label(window, tabs)
        new_index = tabs.insertTab(insert_at, label)
        tabs.setTabToolTip(new_index, label)
        _set_plus_tab_text(window, tabs)
        tabs.setCurrentIndex(insert_at)
        configure_ocr_variant_tab_buttons(window)
    finally:
        def unlock():
            try:
                window._ocr_variant_plus_handling = False
            except Exception:
                pass
        QTimer.singleShot(0, unlock) if QTimer is not None else unlock()
def on_ocr_variant_tab_clicked(window, index: int) -> None:
    tabs = getattr(window, "ocr_variant_tabs", None)
    if tabs is not None and index >= 0 and _is_plus_tab(tabs, index):
        add_ocr_variant_tab(window)
def on_ocr_variant_current_changed(window, index: int) -> None:
    tabs = getattr(window, "ocr_variant_tabs", None)
    if tabs is None or index < 0 or getattr(window, "_ocr_variant_plus_handling", False):
        return
    if _is_plus_tab(tabs, index):
        add_ocr_variant_tab(window)
        return
    apply_variant = getattr(window, "_ptr_apply_multi_ocr_variant", None)
    if callable(apply_variant):
        try:
            apply_variant(current_ocr_variant_path(window), index, save_current=True)
        except TypeError:
            try:
                apply_variant(current_ocr_variant_path(window), index)
            except Exception:
                pass
        except Exception:
            pass

try:
    from .ocr_variant_tab_bar import OCRVariantTabBar
except Exception:  # pragma: no cover
    class OCRVariantTabBar(QTabBar):
        pass
