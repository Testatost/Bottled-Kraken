import json
from uuid import uuid4

from bottled_kraken.common import _theme_app_qss
from bottled_kraken.common import (
    QAction,
    QActionGroup,
    QApplication,
    QColor,
    QPalette,
    QToolButton,
    Qt,
    QKeySequence,
    QShortcut,
    THEMES,
    translation,
)
from bottled_kraken.common.theme_and_help_styles import _theme_is_dark
from bottled_kraken.workers import (
    BackendInstallDialog,
    clear_external_ocr_backend_cache,
)
from PySide6.QtWidgets import (
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QMenu,
    QInputDialog,
)
from PySide6.QtCore import Signal, QTimer

from bottled_kraken._main_window.menu_and_queue.menu_behavior import BKStayOpenMenu

_APPEARANCE_PRESET_ORDER = [
    "original", "light", "midnight", "paper", "cyberpunk", "retrowave",
    "forest", "ocean", "sakura", "copper", "terminal", "organs",
    "lavender", "gpt", "claude", "cute", "bright", "dark",
]
_APPEARANCE_BUILTIN_THEME_KEYS = tuple(_APPEARANCE_PRESET_ORDER)
_APPEARANCE_DEFAULT_THEME_NAMES = {key: str(THEMES.get(key, {}).get("name") or key) for key in _APPEARANCE_BUILTIN_THEME_KEYS}
_APPEARANCE_USER_THEME_PREFIX = "user_"
_APPEARANCE_COLOR_KEYS = [
    ("fg", "appearance_color_text"),
    ("surface", "appearance_color_surface"),
    ("bg", "appearance_color_background"),
    ("selection", "appearance_color_selection"),
    ("overlay_frame", "appearance_color_overlay_frame"),
    ("overlay_split", "appearance_color_overlay_split"),
]
_APPEARANCE_SETTINGS_USER_THEMES = "ui/appearance/user_themes"
_APPEARANCE_SETTINGS_HIDDEN_BUILTINS = "ui/appearance/hidden_builtin_themes"
_APPEARANCE_SETTINGS_RENAMED_BUILTINS = "ui/appearance/renamed_builtin_themes"

def _qcolor_name(value, default="#000000") -> str:
    try:
        if hasattr(value, "name"):
            return value.name()
        c = QColor(str(value or default))
        return c.name() if c.isValid() else str(default)
    except Exception:
        return str(default)

def _contrast_text(color: str) -> str:
    try:
        return "#000000" if QColor(str(color)).lightness() > 165 else "#ffffff"
    except Exception:
        return "#ffffff"

def _adjust(color: str, factor: int) -> str:
    try:
        c = QColor(str(color))
        if not c.isValid():
            return str(color)
        return c.lighter(factor).name() if factor >= 100 else c.darker(200 - factor).name()
    except Exception:
        return str(color)

def _theme_label(key: str, tr_func=None) -> str:
    try:
        if key in _APPEARANCE_BUILTIN_THEME_KEYS and tr_func is not None:
            translated = tr_func(f"theme_{key}")
            if translated and translated != f"theme_{key}":
                return str(translated)
    except Exception:
        pass
    conf = THEMES.get(key, {})
    return str(conf.get("name") or key).strip() or key


class _AppearanceThemeButton(QPushButton):
    doubleClicked = Signal(str)

    def __init__(self, theme_key: str, label: str, parent=None):
        super().__init__(label, parent)
        self.theme_key = str(theme_key)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.doubleClicked.emit(self.theme_key)
            event.accept()
            return
        super().mouseDoubleClickEvent(event)


class MainWindowThemeToolbarMixin:
    def _theme_conf(self, theme: str | None = None) -> dict:
        theme = str(theme or getattr(self, "current_theme", "bright") or "bright")
        return THEMES.get(theme, THEMES.get("bright", {}))

    def _theme_dark(self, theme: str | None = None) -> bool:
        theme = str(theme or getattr(self, "current_theme", "bright") or "bright")
        try:
            return _theme_is_dark(theme)
        except Exception:
            conf = self._theme_conf(theme)
            try:
                return bool(conf.get("dark", QColor(_qcolor_name(conf.get("bg"), "#ffffff")).lightness() < 128))
            except Exception:
                return theme == "dark"

    def _dialog_theme_colors(self, theme: str) -> dict:
        conf = THEMES.get(theme, THEMES.get("bright", {}))
        return {
            "fg": _qcolor_name(conf.get("fg"), "#000000"),
            "surface": _qcolor_name(conf.get("surface", conf.get("table_base")), "#ffffff"),
            "bg": _qcolor_name(conf.get("bg"), "#f0f0f0"),
            "selection": _qcolor_name(conf.get("selection"), "#3399ff"),
            "overlay_frame": _qcolor_name(conf.get("overlay_frame"), "#d00000"),
            "overlay_split": _qcolor_name(conf.get("overlay_split"), "#ffd60a"),
        }

    def _load_custom_theme_colors(self) -> dict:
        defaults = self._dialog_theme_colors("custom")
        colors = {}
        for key in defaults:
            try:
                colors[key] = _qcolor_name(self.settings.value(f"ui/custom_theme/{key}", defaults[key], str), defaults[key])
            except Exception:
                colors[key] = defaults[key]
        return colors

    def _save_custom_theme_colors(self, colors: dict):
        for key, value in (colors or {}).items():
            if key in {item[0] for item in _APPEARANCE_COLOR_KEYS}:
                try:
                    self.settings.setValue(f"ui/custom_theme/{key}", _qcolor_name(value, "#000000"))
                except Exception:
                    pass

    def _make_appearance_theme_entry(self, name: str, colors: dict | None = None) -> dict:
        colors = dict(colors or {})
        fg = _qcolor_name(colors.get("fg"), "#00ff66")
        surface = _qcolor_name(colors.get("surface"), "#050805")
        bg = _qcolor_name(colors.get("bg"), "#000000")
        selection = _qcolor_name(colors.get("selection"), "#00ff66")
        overlay_frame = _qcolor_name(colors.get("overlay_frame"), selection)
        overlay_split = _qcolor_name(colors.get("overlay_split"), "#ffff00")
        is_dark = QColor(bg).lightness() < 128
        border = _adjust(selection, 62 if is_dark else 128)
        return {
            "name": str(name or "").strip() or (self._tr("appearance_custom_theme_name") if hasattr(self, "_tr") else "Benutzerdefiniert"),
            "dark": is_dark,
            "bg": bg,
            "fg": fg,
            "surface": surface,
            "canvas_bg": bg,
            "table_base": QColor(surface),
            "table_alt": _adjust(surface, 112 if is_dark else 96),
            "control_bg": surface,
            "control_hover": _adjust(surface, 122 if is_dark else 94),
            "control_pressed": _adjust(surface, 136 if is_dark else 88),
            "border": border,
            "selection": selection,
            "selection_text": _contrast_text(selection),
            "toolbar_text": fg,
            "toolbar_border": border,
            "overlay_frame": overlay_frame,
            "overlay_selected": selection,
            "overlay_split": overlay_split,
            "overlay_fill_alpha": 34,
            "overlay_selected_alpha": 64,
        }

    def _register_custom_theme(self, colors: dict | None = None):
        colors = dict(colors or self._load_custom_theme_colors())
        THEMES["custom"] = self._make_appearance_theme_entry(
            self._tr("appearance_custom_theme_name") if hasattr(self, "_tr") else "Benutzerdefiniert",
            colors,
        )

    def apply_theme(self, theme: str):
        if hasattr(self, "_ensure_appearance_themes_loaded"):
            self._ensure_appearance_themes_loaded()
        theme = str(theme or "bright").strip().lower()
        if theme == "custom":
            self._register_custom_theme()
        if theme not in THEMES:
            theme = "bright"
        self.current_theme = theme
        self.settings.setValue("ui/theme", self.current_theme)
        conf = self._theme_conf(theme)
        is_dark = self._theme_dark(theme)
        self._current_theme_is_dark = is_dark
        fg = QColor(_qcolor_name(conf.get("fg"), "#ffffff" if is_dark else "#000000"))
        bg = QColor(_qcolor_name(conf.get("bg"), "#2b2b2b" if is_dark else "#f0f0f0"))
        base = conf.get("table_base") if hasattr(conf.get("table_base"), "lighter") else QColor(_qcolor_name(conf.get("surface"), "#ffffff"))
        button = QColor(_qcolor_name(conf.get("control_bg"), base.name()))
        selection = QColor(_qcolor_name(conf.get("selection"), "#2563eb" if is_dark else "#3399ff"))
        pal = QPalette()
        pal.setColor(QPalette.Window, bg)
        pal.setColor(QPalette.WindowText, fg)
        pal.setColor(QPalette.Base, QColor(_qcolor_name(conf.get("surface"), base.name())))
        pal.setColor(QPalette.AlternateBase, QColor(_qcolor_name(conf.get("table_alt"), base.lighter(110).name())))
        pal.setColor(QPalette.ToolTipBase, QColor(_qcolor_name(conf.get("surface"), "#2b3038" if is_dark else "#ffffff")))
        pal.setColor(QPalette.ToolTipText, fg)
        pal.setColor(QPalette.Text, fg)
        pal.setColor(QPalette.Button, button)
        pal.setColor(QPalette.ButtonText, fg)
        pal.setColor(QPalette.BrightText, Qt.red)
        pal.setColor(QPalette.Link, selection)
        pal.setColor(QPalette.Highlight, selection)
        pal.setColor(QPalette.HighlightedText, QColor(_qcolor_name(conf.get("selection_text"), _contrast_text(selection.name()))))
        app = QApplication.instance()
        if app is not None:
            app.setPalette(pal)
            app.setStyleSheet(_theme_app_qss(theme))
        if hasattr(self, "canvas"):
            self.canvas.set_theme(theme, conf)
        self._update_toolbar_language_theme_ui()
        if hasattr(self, "_refresh_preview_tool_button_icons"):
            self._refresh_preview_tool_button_icons()
        self._set_primary_toolbar_icons()
        self._set_secondary_button_icons()
        self._apply_lines_tree_theme()

    def toggle_theme(self):
        new_theme = "dark" if not self._theme_dark() else "bright"
        self.apply_theme(new_theme)

    def _apply_lines_tree_theme(self):
        if not hasattr(self, "list_lines") or self.list_lines is None:
            return
        conf = self._theme_conf()
        is_dark = self._theme_dark()
        fg = _qcolor_name(conf.get("fg"), "#f3f4f6" if is_dark else "#111827")
        surface = _qcolor_name(conf.get("surface"), "#1f2630" if is_dark else "#ffffff")
        alt = _qcolor_name(conf.get("table_alt"), _adjust(surface, 112 if is_dark else 96))
        border = _qcolor_name(conf.get("border"), "#4b5563" if is_dark else "#c8c8c8")
        selection = _qcolor_name(conf.get("selection"), "#2563eb" if is_dark else "#3399ff")
        selection_text = _qcolor_name(conf.get("selection_text"), _contrast_text(selection))
        hover = _qcolor_name(conf.get("control_hover"), _adjust(surface, 122 if is_dark else 94))
        header = _qcolor_name(conf.get("control_bg"), surface)
        qss = f"""
            QTreeWidget {{
                background: {surface};
                alternate-background-color: {alt};
                color: {fg};
                border: 1px solid {border};
                selection-background-color: {selection};
                selection-color: {selection_text};
            }}
            QTreeWidget::item {{
                background: {surface};
                color: {fg};
                padding: 2px 4px;
            }}
            QTreeWidget::item:alternate {{
                background: {alt};
                color: {fg};
            }}
            QTreeWidget::item:hover {{
                background: {hover};
                color: {fg};
            }}
            QTreeWidget::item:selected,
            QTreeWidget::item:selected:active,
            QTreeWidget::item:selected:!active {{
                background: {selection};
                color: {selection_text};
            }}
            QHeaderView::section {{
                background: {header};
                color: {fg};
                border: 1px solid {border};
                padding: 4px;
                font-weight: 600;
            }}
        """
        self.list_lines.setAlternatingRowColors(True)
        self.list_lines.setStyleSheet(qss)
        self.list_lines.viewport().update()

    def _appearance_preset_button_style(self, theme_key: str) -> str:
        conf = THEMES.get(theme_key, THEMES.get("bright", {}))
        fg = _qcolor_name(conf.get("fg"), "#000000")
        surface = _qcolor_name(conf.get("surface"), "#ffffff")
        border = _qcolor_name(conf.get("border"), "#808080")
        selection = _qcolor_name(conf.get("selection"), "#3399ff")
        return f"""
            QPushButton {{
                background: {surface};
                color: {fg};
                border: 2px solid {border};
                border-radius: 8px;
                padding: 8px 10px;
                min-width: 118px;
                min-height: 44px;
                text-align: center;
            }}
            QPushButton:hover {{
                border-color: {selection};
            }}
            QPushButton:checked {{
                border-color: {selection};
                background: {_adjust(surface, 118 if self._theme_dark(theme_key) else 94)};
            }}
        """

    def _color_button_style(self, color: str) -> str:
        color = _qcolor_name(color, "#000000")
        return f"background: {color}; color: {_contrast_text(color)}; border: 1px solid #555; border-radius: 6px; padding: 5px 10px;"

    def _appearance_json_setting(self, key: str, default):
        try:
            raw = self.settings.value(key, "", str)
        except Exception:
            raw = ""
        if isinstance(raw, (list, dict)):
            return raw
        if raw is None or str(raw).strip() == "":
            return default
        try:
            value = json.loads(str(raw))
            return value
        except Exception:
            return default

    def _appearance_set_json_setting(self, key: str, value):
        try:
            self.settings.setValue(key, json.dumps(value, ensure_ascii=False))
        except Exception:
            pass

    def _appearance_hidden_builtin_keys(self) -> set[str]:
        value = self._appearance_json_setting(_APPEARANCE_SETTINGS_HIDDEN_BUILTINS, [])
        if not isinstance(value, list):
            return set()
        return {str(item) for item in value if str(item) in _APPEARANCE_BUILTIN_THEME_KEYS}

    def _appearance_builtin_name_overrides(self) -> dict:
        value = self._appearance_json_setting(_APPEARANCE_SETTINGS_RENAMED_BUILTINS, {})
        if not isinstance(value, dict):
            return {}
        return {
            str(key): str(label).strip()
            for key, label in value.items()
            if str(key) in _APPEARANCE_BUILTIN_THEME_KEYS and str(label).strip()
        }

    def _appearance_user_themes(self) -> list[dict]:
        raw = self._appearance_json_setting(_APPEARANCE_SETTINGS_USER_THEMES, [])
        if not isinstance(raw, list):
            return []
        themes = []
        seen = set()
        for item in raw:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key", "")).strip().lower()
            if not key.startswith(_APPEARANCE_USER_THEME_PREFIX):
                continue
            if key in seen:
                continue
            name = str(item.get("name", "")).strip() or self._tr("appearance_custom_theme_name")
            colors = item.get("colors", {})
            if not isinstance(colors, dict):
                colors = {}
            normalized = {}
            for ckey, _label_key in _APPEARANCE_COLOR_KEYS:
                normalized[ckey] = _qcolor_name(colors.get(ckey), self._dialog_theme_colors("bright").get(ckey, "#000000"))
            themes.append({"key": key, "name": name, "colors": normalized})
            seen.add(key)
        return themes

    def _appearance_save_user_themes(self, user_themes: list[dict]):
        cleaned = []
        seen = set()
        for item in user_themes or []:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key", "")).strip().lower()
            if not key.startswith(_APPEARANCE_USER_THEME_PREFIX) or key in seen:
                continue
            colors = item.get("colors", {}) if isinstance(item.get("colors", {}), dict) else {}
            cleaned.append({
                "key": key,
                "name": str(item.get("name", "")).strip() or self._tr("appearance_custom_theme_name"),
                "colors": {ckey: _qcolor_name(colors.get(ckey), "#000000") for ckey, _label_key in _APPEARANCE_COLOR_KEYS},
            })
            seen.add(key)
        self._appearance_set_json_setting(_APPEARANCE_SETTINGS_USER_THEMES, cleaned)

    def _ensure_appearance_themes_loaded(self):
        for key in _APPEARANCE_BUILTIN_THEME_KEYS:
            if key in THEMES and key in _APPEARANCE_DEFAULT_THEME_NAMES:
                try:
                    THEMES[key]["name"] = _APPEARANCE_DEFAULT_THEME_NAMES[key]
                except Exception:
                    pass
        for key, label in self._appearance_builtin_name_overrides().items():
            if key in THEMES:
                try:
                    THEMES[key]["name"] = label
                except Exception:
                    pass
        existing_user_keys = [key for key in list(THEMES.keys()) if str(key).startswith(_APPEARANCE_USER_THEME_PREFIX)]
        for key in existing_user_keys:
            THEMES.pop(key, None)
        for item in self._appearance_user_themes():
            THEMES[item["key"]] = self._make_appearance_theme_entry(item["name"], item["colors"])

    def _appearance_visible_theme_keys(self) -> list[str]:
        self._ensure_appearance_themes_loaded()
        hidden = self._appearance_hidden_builtin_keys()
        keys = [key for key in _APPEARANCE_PRESET_ORDER if key in THEMES and key not in hidden]
        for item in self._appearance_user_themes():
            key = item.get("key")
            if key in THEMES and key not in keys:
                keys.append(key)
        return keys

    def _appearance_is_builtin_theme(self, key: str) -> bool:
        return str(key) in _APPEARANCE_BUILTIN_THEME_KEYS

    def _appearance_theme_label(self, key: str) -> str:
        if self._appearance_is_builtin_theme(key):
            overrides = self._appearance_builtin_name_overrides()
            if key in overrides:
                return overrides[key]
        return _theme_label(key, self._tr if hasattr(self, "_tr") else None)

    def _appearance_new_user_theme_key(self) -> str:
        return f"{_APPEARANCE_USER_THEME_PREFIX}{uuid4().hex[:12]}"

    def _appearance_default_custom_theme_name(self) -> str:
        base = self._tr("appearance_custom_theme_name") if hasattr(self, "_tr") else "Benutzerdefiniert"
        used = {str(item.get("name", "")).strip() for item in self._appearance_user_themes()}
        if base not in used:
            return base
        idx = 2
        while f"{base} {idx}" in used:
            idx += 1
        return f"{base} {idx}"

    def _appearance_store_or_update_user_theme(self, theme_key: str | None, name: str, colors: dict) -> str:
        self._ensure_appearance_themes_loaded()
        user_themes = self._appearance_user_themes()
        target_key = str(theme_key or "").strip().lower()
        if not target_key.startswith(_APPEARANCE_USER_THEME_PREFIX):
            target_key = self._appearance_new_user_theme_key()
        name = str(name or "").strip() or self._appearance_default_custom_theme_name()
        normalized_colors = {ckey: _qcolor_name(colors.get(ckey), "#000000") for ckey, _label_key in _APPEARANCE_COLOR_KEYS}
        updated = False
        for item in user_themes:
            if item.get("key") == target_key:
                item["name"] = name
                item["colors"] = normalized_colors
                updated = True
                break
        if not updated:
            user_themes.append({"key": target_key, "name": name, "colors": normalized_colors})
        self._appearance_save_user_themes(user_themes)
        THEMES[target_key] = self._make_appearance_theme_entry(name, normalized_colors)
        return target_key

    def _appearance_rename_theme(self, theme_key: str, parent=None) -> bool:
        self._ensure_appearance_themes_loaded()
        if theme_key not in THEMES:
            return False
        current_label = self._appearance_theme_label(theme_key)
        new_label, ok = QInputDialog.getText(
            parent or self,
            self._tr("appearance_rename_theme"),
            self._tr("appearance_theme_name_prompt"),
            text=current_label,
        )
        if not ok:
            return False
        new_label = str(new_label or "").strip()
        if not new_label:
            return False
        if self._appearance_is_builtin_theme(theme_key):
            overrides = self._appearance_builtin_name_overrides()
            default_name = _APPEARANCE_DEFAULT_THEME_NAMES.get(theme_key, theme_key)
            if new_label == default_name:
                overrides.pop(theme_key, None)
            else:
                overrides[theme_key] = new_label
            self._appearance_set_json_setting(_APPEARANCE_SETTINGS_RENAMED_BUILTINS, overrides)
            if theme_key in THEMES:
                THEMES[theme_key]["name"] = new_label
            return True
        user_themes = self._appearance_user_themes()
        for item in user_themes:
            if item.get("key") == theme_key:
                item["name"] = new_label
                break
        self._appearance_save_user_themes(user_themes)
        if theme_key in THEMES:
            THEMES[theme_key]["name"] = new_label
        return True

    def _appearance_delete_theme(self, theme_key: str) -> bool:
        self._ensure_appearance_themes_loaded()
        if theme_key not in THEMES:
            return False
        if self._appearance_is_builtin_theme(theme_key):
            hidden = self._appearance_hidden_builtin_keys()
            hidden.add(theme_key)
            self._appearance_set_json_setting(_APPEARANCE_SETTINGS_HIDDEN_BUILTINS, sorted(hidden))
        else:
            user_themes = [item for item in self._appearance_user_themes() if item.get("key") != theme_key]
            self._appearance_save_user_themes(user_themes)
            THEMES.pop(theme_key, None)
        if getattr(self, "current_theme", "") == theme_key:
            self.current_theme = "bright"
            try:
                self.settings.setValue("ui/theme", "bright")
            except Exception:
                pass
        return True

    def _appearance_reset_theme_library(self):
        self._appearance_set_json_setting(_APPEARANCE_SETTINGS_USER_THEMES, [])
        self._appearance_set_json_setting(_APPEARANCE_SETTINGS_HIDDEN_BUILTINS, [])
        self._appearance_set_json_setting(_APPEARANCE_SETTINGS_RENAMED_BUILTINS, {})
        for key in list(THEMES.keys()):
            if str(key).startswith(_APPEARANCE_USER_THEME_PREFIX):
                THEMES.pop(key, None)
        for key, name in _APPEARANCE_DEFAULT_THEME_NAMES.items():
            if key in THEMES:
                try:
                    THEMES[key]["name"] = name
                except Exception:
                    pass
        if getattr(self, "current_theme", "bright") not in THEMES or str(getattr(self, "current_theme", "")).startswith(_APPEARANCE_USER_THEME_PREFIX):
            self.current_theme = "bright"
            try:
                self.settings.setValue("ui/theme", "bright")
            except Exception:
                pass

    def _appearance_translate_color_dialog_widgets(self, color_dialog: QColorDialog):
        mapping = {
            "Basic colors": self._tr("color_dialog_basic_colors"),
            "Custom colors": self._tr("color_dialog_custom_colors"),
            "Pick Screen Color": self._tr("color_dialog_pick_screen_color"),
            "Add to Custom Colors": self._tr("color_dialog_add_to_custom_colors"),
            "Hue": self._tr("color_dialog_hue"),
            "Sat": self._tr("color_dialog_sat"),
            "Val": self._tr("color_dialog_val"),
            "Red": self._tr("color_dialog_red"),
            "Green": self._tr("color_dialog_green"),
            "Blue": self._tr("color_dialog_blue"),
            "HTML": self._tr("color_dialog_html"),
            "OK": self._tr("color_dialog_ok"),
            "Cancel": self._tr("color_dialog_cancel"),
        }
        def translated(text: str) -> str | None:
            raw = str(text or "")
            normalized = raw.replace("&", "").strip()
            had_colon = normalized.endswith(":")
            key = normalized[:-1].strip() if had_colon else normalized
            value = mapping.get(key)
            if not value:
                return None
            return f"{value}:" if had_colon and not str(value).endswith(":") else str(value)
        for widget_type in (QLabel, QPushButton):
            for widget in color_dialog.findChildren(widget_type):
                try:
                    value = translated(widget.text())
                    if value:
                        widget.setText(value)
                except Exception:
                    pass
        for box in color_dialog.findChildren(QDialogButtonBox):
            try:
                ok_button = box.button(QDialogButtonBox.Ok)
                if ok_button is not None:
                    ok_button.setText(self._tr("color_dialog_ok"))
                cancel_button = box.button(QDialogButtonBox.Cancel)
                if cancel_button is not None:
                    cancel_button.setText(self._tr("color_dialog_cancel"))
            except Exception:
                pass

    def _appearance_choose_color(self, initial: QColor, parent) -> QColor:
        dialog = QColorDialog(initial, parent)
        option = getattr(QColorDialog, "DontUseNativeDialog", None)
        if option is None:
            option = getattr(getattr(QColorDialog, "ColorDialogOption", None), "DontUseNativeDialog", None)
        if option is not None:
            dialog.setOption(option, True)
        dialog.setWindowTitle(self._tr("appearance_choose_color"))
        try:
            dialog.setStyleSheet(_theme_app_qss(getattr(self, "current_theme", "bright")))
        except Exception:
            pass
        self._appearance_translate_color_dialog_widgets(dialog)
        QTimer.singleShot(0, lambda: self._appearance_translate_color_dialog_widgets(dialog))
        result = dialog.exec()
        if result == QDialog.Accepted:
            color = dialog.selectedColor()
            if color.isValid():
                return color
        return QColor()

    def open_appearance_dialog(self):
        self._ensure_appearance_themes_loaded()
        self._register_custom_theme()
        dialog = QDialog(self)
        dialog.setWindowTitle(self._tr("appearance_title"))
        dialog.setMinimumSize(800, 600)
        dialog.setStyleSheet(_theme_app_qss(self.current_theme))
        visible_keys = self._appearance_visible_theme_keys()
        start_theme = self.current_theme if self.current_theme in visible_keys else ("bright" if "bright" in visible_keys else (visible_keys[0] if visible_keys else "bright"))
        state = {
            "theme": start_theme,
            "colors": self._dialog_theme_colors(start_theme),
            "customized": False,
            "source_theme": start_theme,
        }
        root = QVBoxLayout(dialog)
        intro = QLabel(self._tr("appearance_intro"), dialog)
        intro.setWordWrap(True)
        root.addWidget(intro)
        presets_box = QGroupBox(self._tr("appearance_presets"), dialog)
        presets_layout = QGridLayout(presets_box)
        presets_layout.setSpacing(8)
        preset_buttons = {}
        root.addWidget(presets_box)
        colors_box = QGroupBox(self._tr("appearance_custom_colors"), dialog)
        colors_layout = QGridLayout(colors_box)
        colors_layout.setColumnStretch(1, 1)
        color_buttons = {}
        color_labels = {}
        preview = QFrame(colors_box)
        preview.setFrameShape(QFrame.StyledPanel)
        preview.setMinimumHeight(72)
        preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        preview_label = QLabel(self._tr("appearance_preview_text"), preview)
        preview_label.setAlignment(Qt.AlignCenter)
        preview_lay = QVBoxLayout(preview)
        preview_lay.setContentsMargins(12, 12, 12, 12)
        preview_lay.addWidget(preview_label)

        def clear_layout(layout):
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                child_layout = item.layout()
                if widget is not None:
                    widget.deleteLater()
                elif child_layout is not None:
                    clear_layout(child_layout)

        def refresh_preview():
            colors = state["colors"]
            fg = colors.get("fg", "#000000")
            surface = colors.get("surface", "#ffffff")
            bg = colors.get("bg", "#f0f0f0")
            selection = colors.get("selection", "#3399ff")
            border = colors.get("overlay_frame", selection)
            split = colors.get("overlay_split", "#ffd60a")
            preview.setStyleSheet(
                f"QFrame{{background:{bg}; border:1px solid {border}; border-radius:8px;}} "
                f"QLabel{{background:{surface}; color:{fg}; border-left:8px solid {selection}; border-right:8px solid {split}; padding:12px;}}"
            )
            for ckey, _label_key in _APPEARANCE_COLOR_KEYS:
                val = _qcolor_name(colors.get(ckey), "#000000")
                color_buttons[ckey].setText(val)
                color_buttons[ckey].setStyleSheet(self._color_button_style(val))
            for key, btn in preset_buttons.items():
                btn.setChecked((not state.get("customized")) and state.get("theme") == key)

        def set_from_theme(key: str):
            self._ensure_appearance_themes_loaded()
            if key not in THEMES:
                visible = self._appearance_visible_theme_keys()
                key = "bright" if "bright" in visible else (visible[0] if visible else "bright")
            state["theme"] = key
            state["source_theme"] = key
            state["colors"] = self._dialog_theme_colors(key)
            state["customized"] = False
            refresh_preview()

        def rebuild_preset_buttons():
            self._ensure_appearance_themes_loaded()
            clear_layout(presets_layout)
            preset_buttons.clear()
            for pos, key in enumerate(self._appearance_visible_theme_keys()):
                if key not in THEMES:
                    continue
                btn = _AppearanceThemeButton(key, self._appearance_theme_label(key), presets_box)
                btn.setCheckable(True)
                btn.setCursor(Qt.PointingHandCursor)
                btn.setContextMenuPolicy(Qt.CustomContextMenu)
                btn.setStyleSheet(self._appearance_preset_button_style(key))
                btn.clicked.connect(lambda checked=False, k=key: set_from_theme(k))
                btn.doubleClicked.connect(lambda k: rename_theme(k))
                btn.customContextMenuRequested.connect(lambda pos, b=btn, k=key: open_theme_menu(k, b.mapToGlobal(pos)))
                preset_buttons[key] = btn
                presets_layout.addWidget(btn, pos // 6, pos % 6)
            refresh_preview()

        def rename_theme(key: str):
            if self._appearance_rename_theme(key, dialog):
                rebuild_preset_buttons()
                if state.get("theme") == key:
                    state["source_theme"] = key
                refresh_preview()

        def delete_theme(key: str):
            if not self._appearance_delete_theme(key):
                return
            visible = self._appearance_visible_theme_keys()
            if state.get("theme") == key or key not in visible:
                fallback = "bright" if "bright" in visible else (visible[0] if visible else "bright")
                state["theme"] = fallback
                state["source_theme"] = fallback
                state["colors"] = self._dialog_theme_colors(fallback)
                state["customized"] = False
            rebuild_preset_buttons()

        def open_theme_menu(key: str, global_pos):
            menu = QMenu(dialog)
            rename_action = menu.addAction(self._tr("appearance_rename_theme"))
            delete_action = menu.addAction(self._tr("appearance_delete_theme"))
            chosen = menu.exec(global_pos)
            if chosen == rename_action:
                rename_theme(key)
            elif chosen == delete_action:
                delete_theme(key)

        def choose_color(ckey: str):
            old = QColor(state["colors"].get(ckey, "#000000"))
            color = self._appearance_choose_color(old, dialog)
            if not color.isValid():
                return
            state["colors"][ckey] = color.name()
            state["customized"] = True
            refresh_preview()

        def delete_selected_theme():
            key = state.get("theme")
            if key and key in preset_buttons:
                delete_theme(key)

        def reset_theme_library():
            self._appearance_reset_theme_library()
            state["theme"] = "bright"
            state["source_theme"] = "bright"
            state["colors"] = self._dialog_theme_colors("bright")
            state["customized"] = False
            rebuild_preset_buttons()

        QShortcut(QKeySequence.Delete, dialog).activated.connect(delete_selected_theme)
        for row, (ckey, label_key) in enumerate(_APPEARANCE_COLOR_KEYS):
            label = QLabel(self._tr(label_key), colors_box)
            btn = QPushButton(colors_box)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, k=ckey: choose_color(k))
            color_labels[ckey] = label
            color_buttons[ckey] = btn
            colors_layout.addWidget(label, row, 0)
            colors_layout.addWidget(btn, row, 1)
        colors_layout.addWidget(preview, 0, 2, len(_APPEARANCE_COLOR_KEYS), 1)
        root.addWidget(colors_box, 1)
        buttons_row = QHBoxLayout()
        themes_reset_btn = QPushButton(self._tr("appearance_reset_themes"), dialog)
        themes_reset_btn.clicked.connect(reset_theme_library)
        buttons_row.addWidget(themes_reset_btn)
        reset_btn = QPushButton(self._tr("appearance_reset"), dialog)
        reset_btn.clicked.connect(lambda: set_from_theme("bright"))
        buttons_row.addWidget(reset_btn)
        buttons_row.addStretch(1)
        save_btn = QPushButton(self._tr("btn_save"), dialog)
        cancel_btn = QPushButton(self._tr("btn_cancel"), dialog)
        save_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        buttons_row.addWidget(save_btn)
        buttons_row.addWidget(cancel_btn)
        root.addLayout(buttons_row)
        rebuild_preset_buttons()
        if dialog.exec() == QDialog.Accepted:
            theme_to_apply = state.get("theme") or "bright"
            if state.get("customized"):
                colors = dict(state.get("colors") or {})
                self._save_custom_theme_colors(colors)
                if str(theme_to_apply).startswith(_APPEARANCE_USER_THEME_PREFIX):
                    current_name = self._appearance_theme_label(theme_to_apply)
                    theme_to_apply = self._appearance_store_or_update_user_theme(theme_to_apply, current_name, colors)
                else:
                    default_name = self._appearance_default_custom_theme_name()
                    new_name, ok = QInputDialog.getText(
                        dialog,
                        self._tr("appearance_save_custom_theme_title"),
                        self._tr("appearance_theme_name_prompt"),
                        text=default_name,
                    )
                    if ok:
                        name = str(new_name or "").strip() or default_name
                    else:
                        name = default_name
                    theme_to_apply = self._appearance_store_or_update_user_theme(None, name, colors)
            self._ensure_appearance_themes_loaded()
            self.apply_theme(theme_to_apply if theme_to_apply in THEMES else "bright")

    def set_language(self, lang):
        self.current_lang = translation.normalize_language_code(lang)
        self.log_lang = self.current_lang
        self.settings.setValue("ui/language", self.current_lang)
        self.retranslate_ui()
        self._refresh_hw_menu_availability()
        self._update_toolbar_language_theme_ui()

    def _build_toolbar_language_theme_menus(self):
        self.lang_toolbar_menu = BKStayOpenMenu(self)
        self.lang_group = QActionGroup(self)
        self.lang_group.setExclusive(True)
        self.lang_actions = {}
        for lang_code in translation.available_languages():
            label = translation.language_display_name(lang_code, getattr(self, "current_lang", None))
            action = QAction(label, self)
            action.setCheckable(True)
            action.triggered.connect(lambda checked=False, code=lang_code: self.set_language(code))
            self.lang_group.addAction(action)
            self.lang_toolbar_menu.addAction(action)
            self.lang_actions[lang_code] = action
            if lang_code.isidentifier():
                setattr(self, f"act_lang_{lang_code}", action)
        self.btn_lang_menu.setMenu(self.lang_toolbar_menu)
        self._update_toolbar_language_theme_ui()

    def _update_toolbar_language_theme_ui(self):
        if hasattr(self, "btn_theme_toggle"):
            self.btn_theme_toggle.setChecked(self._theme_dark())
            self.btn_theme_toggle.setText("")
            self.btn_theme_toggle.setIcon(self._theme_toggle_icon())
            self.btn_theme_toggle.setToolButtonStyle(Qt.ToolButtonIconOnly)
            self.btn_theme_toggle.setToolTip(self._tr("toolbar_theme_tooltip"))
        if hasattr(self, "btn_lang_menu"):
            self.btn_lang_menu.setText("")
            self.btn_lang_menu.setIcon(self._language_menu_icon())
            self.btn_lang_menu.setToolButtonStyle(Qt.ToolButtonIconOnly)
            self.btn_lang_menu.setToolTip(self._tr("toolbar_language_tooltip"))
        for lang_code, action in getattr(self, "lang_actions", {}).items():
            action.setText(translation.language_display_name(lang_code, self.current_lang))
            action.setChecked(self.current_lang == lang_code)

    def _update_models_menu_labels(self):
        if hasattr(self, "act_rec"):
            self.act_rec.setText(self._tr("act_load_rec_model"))
        if hasattr(self, "act_seg"):
            self.act_seg.setText(self._tr("act_load_seg_model"))
        if hasattr(self, "act_kraken_auto_revision_settings"):
            self.act_kraken_auto_revision_settings.setText(self._tr("act_kraken_auto_revision_settings"))
        if hasattr(self, "act_whisper_set_path"):
            self.act_whisper_set_path.setText(self._tr("act_whisper_set_path"))
        if hasattr(self, "act_whisper_set_mic"):
            self.act_whisper_set_mic.setText(self._tr("act_whisper_set_mic"))
        if hasattr(self, "act_whisper_scan"):
            self.act_whisper_scan.setText(self._tr("act_scan_local"))
        if hasattr(self, "act_set_manual_lm_url"):
            self.act_set_manual_lm_url.setText(self._tr("act_set_manual_lm_url"))
        if hasattr(self, "act_clear_manual_lm_url"):
            self.act_clear_manual_lm_url.setText(self._tr("act_clear_manual_lm_url"))
        if hasattr(self, "act_scan_lm"):
            self.act_scan_lm.setText(self._tr("act_scan_local"))
        self._update_kraken_menu_status()
        if hasattr(self, "kraken_models_submenu"):
            self._rebuild_kraken_models_submenu()

    def _make_toolbar_buttons_pushy(self):
        for b in self.toolbar.findChildren(QToolButton):
            b.setAutoRaise(False)
            b.setCursor(Qt.PointingHandCursor)
        self.btn_rec_model.setCursor(Qt.PointingHandCursor)
        self.btn_seg_model.setCursor(Qt.PointingHandCursor)
        if hasattr(self, "btn_import_lines"):
            self.btn_import_lines.setCursor(Qt.PointingHandCursor)

    def open_integrated_backend_installer(self, backend_kind: str):
        dlg = BackendInstallDialog(backend_kind, tr_func=self._tr, parent=self)
        dlg.install_finished.connect(self._on_integrated_backend_install_finished)
        dlg.exec()

    def _on_integrated_backend_install_finished(self, ok: bool, backend_kind: str):
        try:
            clear_external_ocr_backend_cache()
        except Exception:
            pass
        try:
            self._refresh_hw_menu_availability()
        except Exception:
            pass
        if ok:
            try:
                self._log(self._tr("backend_install_success"))
            except Exception:
                pass
