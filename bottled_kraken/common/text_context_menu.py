from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('shared', globals())

from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QLineEdit, QPlainTextEdit, QTextEdit

from bottled_kraken.translation import translation
from bottled_kraken.common.light_mode_button_icons import _bk_auto_tint_icon_for_widget


_TEXT_CONTEXT_ACTIONS = (
    ("text_context_undo", "text_context_shortcut_undo"),
    ("text_context_redo", "text_context_shortcut_redo"),
    ("text_context_cut", "text_context_shortcut_cut"),
    ("text_context_copy", "text_context_shortcut_copy"),
    ("text_context_paste", "text_context_shortcut_paste"),
    ("text_context_delete", "text_context_shortcut_delete"),
    ("text_context_select_all", "text_context_shortcut_select_all"),
)


def _bk_text_context_language(widget) -> str:
    current = widget
    while current is not None:
        try:
            lang = getattr(current, "current_lang", None)
            if lang:
                return translation.normalize_language_code(lang)
        except Exception:
            pass
        current = current.parentWidget() if hasattr(current, "parentWidget") else None
    return translation.DEFAULT_LANGUAGE


def _bk_is_standard_text_editor(widget) -> bool:
    return isinstance(widget, (QLineEdit, QTextEdit, QPlainTextEdit))


def _bk_handle_text_redo_shortcut(widget, event) -> bool:
    """Macht Ctrl+Y/Strg+Y in allen Standard-Textfeldern zu Redo.

    Qt verwendet unter Linux je nach Desktop-/Qt-Konfiguration oft
    Ctrl+Shift+Z als Standardfolge. Bottled Kraken zeigt bewusst Ctrl+Y an,
    daher muss diese Folge auch tatsaechlich funktionieren.
    """
    if not _bk_is_standard_text_editor(widget):
        return False
    try:
        if event.type() not in (QEvent.ShortcutOverride, QEvent.KeyPress):
            return False
        if event.key() != Qt.Key_Y:
            return False
        modifiers = event.modifiers()
        if not (modifiers & Qt.ControlModifier):
            return False
        if modifiers & (Qt.ShiftModifier | Qt.AltModifier | Qt.MetaModifier):
            return False
        if event.type() == QEvent.ShortcutOverride:
            event.accept()
            return True
        widget.redo()
        event.accept()
        return True
    except Exception:
        return False


def _bk_decorate_standard_text_context_menu(widget, menu) -> None:
    lang = _bk_text_context_language(widget)
    actions = [action for action in menu.actions() if not action.isSeparator()]
    # Qts Standardmenue beginnt bei QLineEdit, QTextEdit und QPlainTextEdit
    # stabil mit Undo, Redo, Cut, Copy, Paste, Delete und Select All. Etwaige
    # Plattform-Zusatzaktionen folgen danach und bleiben bewusst unveraendert.
    for index, (key, shortcut_key) in enumerate(_TEXT_CONTEXT_ACTIONS):
        if index >= len(actions):
            break
        action = actions[index]
        label = translation.translate(lang, key)
        shortcut_text = translation.translate(lang, shortcut_key)
        # Der Text hinter dem Tabulator wird von QMenu in der rechten
        # Shortcut-Spalte dargestellt. So folgt die Anzeige der gewaehlten
        # App-Sprache statt der Desktop-Sprache. Ctrl+Y fuer Redo wird
        # zusaetzlich zentral im Event-Filter verarbeitet.
        action.setShortcut(QKeySequence())
        action.setText(f"{label}\t{shortcut_text}")
        try:
            icon = action.icon()
            if icon is not None and not icon.isNull():
                fixed = _bk_auto_tint_icon_for_widget(icon, widget)
                if fixed is not None and not fixed.isNull():
                    action.setIcon(fixed)
        except Exception:
            pass


def _bk_show_standard_text_context_menu(widget, event) -> bool:
    if not _bk_is_standard_text_editor(widget):
        return False
    try:
        if widget.contextMenuPolicy() != Qt.DefaultContextMenu:
            return False
    except Exception:
        pass
    try:
        menu = widget.createStandardContextMenu()
    except Exception:
        return False
    if menu is None:
        return False
    try:
        _bk_decorate_standard_text_context_menu(widget, menu)
        try:
            global_pos = event.globalPos()
        except Exception:
            global_pos = QPoint()
        if global_pos.isNull():
            try:
                global_pos = widget.mapToGlobal(widget.rect().center())
            except Exception:
                pass
        menu.exec(global_pos)
        event.accept()
        return True
    finally:
        try:
            menu.deleteLater()
        except Exception:
            pass


__all__ = [
    "_bk_decorate_standard_text_context_menu",
    "_bk_handle_text_redo_shortcut",
    "_bk_is_standard_text_editor",
    "_bk_show_standard_text_context_menu",
]

register_globals('shared', globals(), __all__)
