from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('shared', globals())
def _theme_color(theme: str, key: str, default: str) -> str:
    try:
        conf = THEMES.get(theme, THEMES.get("bright", {}))
    except Exception:
        conf = {}
    value = conf.get(key, default) if isinstance(conf, dict) else default
    try:
        if hasattr(value, "name"):
            return value.name()
    except Exception:
        pass
    return str(value or default)
def _theme_conf(theme: str) -> Dict[str, str]:
    try:
        conf = THEMES.get(theme, THEMES.get("bright", {}))
    except Exception:
        conf = {}
    return conf if isinstance(conf, dict) else {}
def _theme_is_dark(theme: str) -> bool:
    conf = _theme_conf(theme)
    try:
        if "dark" in conf:
            return bool(conf.get("dark"))
        return QColor(_theme_color(theme, "bg", "#ffffff")).lightness() < 128
    except Exception:
        return str(theme or "").lower() == "dark"
def _theme_adjust(color: str, factor: int) -> str:
    try:
        c = QColor(str(color))
        if not c.isValid():
            return str(color)
        return c.lighter(int(factor)).name() if int(factor) >= 100 else c.darker(int(200 - factor)).name()
    except Exception:
        return str(color)
def _theme_contrast_text(color: str) -> str:
    try:
        return "#000000" if QColor(str(color)).lightness() > 165 else "#ffffff"
    except Exception:
        return "#ffffff"
def _theme_app_qss(theme: str) -> str:
    dark = _theme_is_dark(theme)
    fg = _theme_color(theme, "fg", "#f3f4f6" if dark else "#000000")
    bg = _theme_color(theme, "bg", "#1f232a" if dark else "#f0f0f0")
    surface = _theme_color(theme, "surface", "#2b3038" if dark else "#ffffff")
    control_bg = _theme_color(theme, "control_bg", surface)
    control_hover = _theme_color(theme, "control_hover", _theme_adjust(control_bg, 118 if dark else 96))
    control_pressed = _theme_color(theme, "control_pressed", _theme_adjust(control_bg, 132 if dark else 88))
    border = _theme_color(theme, "border", "#4b5563" if dark else "#b8b8b8")
    selection = _theme_color(theme, "selection", "#2563eb" if dark else "#3399ff")
    selection_text = _theme_color(theme, "selection_text", _theme_contrast_text(selection))
    table_alt = _theme_color(theme, "table_alt", _theme_adjust(surface, 112 if dark else 97))
    menu_bg = _theme_color(theme, "menu_bg", bg)
    disabled_fg = _theme_adjust(fg, 70 if dark else 150)
    disabled_bg = _theme_adjust(control_bg, 86 if dark else 96)
    base = f"""
        QWidget {{
            background: {bg};
            color: {fg};
        }}
        QMainWindow, QDialog, QMessageBox, QInputDialog, QProgressDialog {{
            background: {bg};
            color: {fg};
        }}
        QLabel, QGroupBox {{
            color: {fg};
        }}
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox,
        QComboBox, QListWidget, QTreeWidget, QTableWidget {{
            background: {surface};
            color: {fg};
            border: 1px solid {border};
            selection-background-color: {selection};
            selection-color: {selection_text};
        }}
        QTreeWidget, QTableWidget {{
            alternate-background-color: {table_alt};
        }}
        QPushButton, QToolButton {{
            color: {fg};
            background: {control_bg};
            border: 1px solid {border};
            border-radius: 6px;
            padding: 5px 10px;
        }}
        QPushButton:hover, QToolButton:hover {{
            background: {control_hover};
            border-color: {selection};
        }}
        QPushButton:pressed, QToolButton:pressed {{
            background: {control_pressed};
        }}
        QPushButton:disabled, QToolButton:disabled {{
            color: {disabled_fg};
            background: {disabled_bg};
            border-color: {border};
        }}
        QMenuBar {{
            background: {menu_bg};
            color: {fg};
        }}
        QMenuBar::item:selected {{
            background: {control_hover};
        }}
        QMenu {{
            background: {menu_bg};
            color: {fg};
            border: 1px solid {border};
        }}
        QMenu::item {{
            background: transparent;
            min-height: 22px;
            padding: 4px 30px 4px 28px;
        }}
        QMenu::item:selected {{
            background: {selection};
            color: {selection_text};
        }}
        QMenu::item:disabled {{
            color: {disabled_fg};
        }}
        QMenu::separator {{
            height: 1px;
            background: {border};
            margin: 4px 6px;
        }}
        QMenu::indicator {{
            width: 16px;
            height: 16px;
        }}
        QHeaderView::section {{
            background: {control_bg};
            color: {fg};
            border: 1px solid {border};
            padding: 4px;
        }}
        QScrollBar:vertical, QScrollBar:horizontal {{
            background: {bg};
        }}
    """
    return base + "\n" + _theme_control_qss(theme)
def _image_edit_dialog_qss(theme: str) -> str:
    dark = _theme_is_dark(theme)
    fg = _theme_color(theme, "fg", "#f3f4f6" if dark else "#1f2937")
    bg = _theme_color(theme, "bg", "#1f232a" if dark else "#f6f7fb")
    surface = _theme_color(theme, "surface", "#2b3038" if dark else "#ffffff")
    border = _theme_color(theme, "border", "#4b5563" if dark else "#cfd5df")
    selection = _theme_color(theme, "selection", "#1d4ed8" if dark else "#3399ff")
    selection_text = _theme_color(theme, "selection_text", _theme_contrast_text(selection))
    hover = _theme_color(theme, "control_hover", _theme_adjust(surface, 118 if dark else 96))
    pressed = _theme_color(theme, "control_pressed", _theme_adjust(surface, 132 if dark else 88))
    base = f"""
        QDialog {{
            background: {bg};
            color: {fg};
        }}
        QLabel, QPushButton {{
            color: {fg};
            font-size: 13px;
        }}
        QPushButton {{
            background: {surface};
            border: 1px solid {border};
            border-radius: 6px;
            padding: 6px 10px;
        }}
        QPushButton:hover {{
            background: {hover};
            border-color: {selection};
        }}
        QPushButton:pressed {{
            background: {pressed};
        }}
        QPushButton:checked {{
            background: {selection};
            border-color: {selection};
            color: {selection_text};
        }}
    """
    return base + "\n" + _theme_control_qss(theme)
def _theme_control_qss(theme: str) -> str:
    dark = _theme_is_dark(theme)
    fg = _theme_color(theme, "fg", "#f3f4f6" if dark else "#000000")
    surface = _theme_color(theme, "surface", "#2b3038" if dark else "#ffffff")
    border = _theme_color(theme, "border", "#94a3b8" if dark else "#7c8aa5")
    selection = _theme_color(theme, "selection", "#2563eb" if dark else "#3399ff")
    hover = _theme_color(theme, "control_hover", _theme_adjust(surface, 118 if dark else 96))
    rail = _theme_adjust(surface, 125 if dark else 92)
    handle = _theme_adjust(selection, 128 if dark else 150)
    return f"""
        QCheckBox, QRadioButton {{
            spacing: 6px;
            color: {fg};
        }}
        QCheckBox::indicator,
        QRadioButton::indicator,
        QTableWidget::indicator,
        QTreeWidget::indicator,
        QListWidget::indicator {{
            width: 16px;
            height: 16px;
            border: 1px solid {border};
            border-radius: 3px;
            background: {surface};
        }}
        QCheckBox::indicator:hover,
        QRadioButton::indicator:hover,
        QTableWidget::indicator:hover,
        QTreeWidget::indicator:hover,
        QListWidget::indicator:hover {{
            border: 1px solid {selection};
            background: {hover};
        }}
        QCheckBox::indicator:checked,
        QRadioButton::indicator:checked,
        QTableWidget::indicator:checked,
        QTreeWidget::indicator:checked,
        QListWidget::indicator:checked {{
            border: 1px solid {selection};
            background: {selection};
        }}
        QCheckBox::indicator:checked:hover,
        QRadioButton::indicator:checked:hover,
        QTableWidget::indicator:checked:hover,
        QListWidget::indicator:checked:hover {{
            border: 1px solid {handle};
            background: {handle};
        }}
        QSlider::groove:horizontal {{
            height: 8px;
            background: {rail};
            border-radius: 4px;
        }}
        QSlider::sub-page:horizontal {{
            background: {selection};
            border-radius: 4px;
        }}
        QSlider::add-page:horizontal {{
            background: {rail};
            border-radius: 4px;
        }}
        QSlider::handle:horizontal {{
            background: {handle};
            width: 18px;
            margin: -5px 0;
            border-radius: 9px;
            border: 1px solid {selection};
        }}
        QSlider::handle:horizontal:hover {{
            background: {selection};
        }}
    """
def _help_theme_values(theme: str) -> Dict[str, str]:
    dark = _theme_is_dark(theme)
    fg = _theme_color(theme, "fg", "#f3f4f6" if dark else "#1f2937")
    bg = _theme_color(theme, "bg", "#1f232a" if dark else "#f6f7fb")
    surface = _theme_color(theme, "surface", "#2b3038" if dark else "#ffffff")
    border = _theme_color(theme, "border", "#4b5563" if dark else "#e3e7ef")
    accent = _theme_color(theme, "selection", "#60a5fa" if dark else "#1d4ed8")
    return {
        "html_bg": bg,
        "html_fg": fg,
        "card_bg": surface,
        "card_border": border,
        "accent": accent,
        "muted": _theme_adjust(fg, 76 if dark else 138),
        "badge_bg": accent,
        "badge_fg": _theme_contrast_text(accent),
        "warn_bg": "#3b2b00" if dark else "#fff7e6",
        "warn_border": "#f59e0b",
        "ok_bg": "#0f2d1f" if dark else "#eefbf3",
        "ok_border": "#34d399",
        "code_bg": _theme_color(theme, "control_bg", surface),
        "nav_bg": surface,
        "nav_border": border,
        "nav_hover": _theme_color(theme, "control_hover", _theme_adjust(surface, 118 if dark else 96)),
        "nav_selected_bg": accent,
        "nav_selected_border": _theme_adjust(accent, 126 if dark else 82),
        "button_bg": _theme_color(theme, "control_bg", surface),
        "button_hover": _theme_color(theme, "control_hover", _theme_adjust(surface, 118 if dark else 96)),
        "button_border": border,
        "dialog_bg": bg,
        "browser_bg": surface,
        "browser_border": border,
    }
def _help_dialog_qss(theme: str) -> str:
    colors = _help_theme_values(theme)
    selected_fg = _theme_color(theme, "selection_text", _theme_contrast_text(colors["nav_selected_bg"]))
    return f"""
        QDialog {{
            background: {colors["dialog_bg"]};
            color: {colors["html_fg"]};
        }}
        QTextBrowser {{
            background: {colors["browser_bg"]};
            color: {colors["html_fg"]};
            border: 1px solid {colors["browser_border"]};
            border-radius: 10px;
            padding: 8px;
        }}
        QLabel {{
            color: {colors["html_fg"]};
            font-size: 13px;
            font-weight: 600;
        }}
        QPushButton {{
            color: {colors["html_fg"]};
            background: {colors["button_bg"]};
            border: 1px solid {colors["button_border"]};
            border-radius: 8px;
            padding: 6px 12px;
            min-height: 28px;
        }}
        QPushButton:hover {{
            background: {colors["button_hover"]};
            border-color: {colors["accent"]};
        }}
        QPushButton:pressed {{
            background: {colors["button_hover"]};
        }}
        QListWidget {{
            background: {colors["nav_bg"]};
            color: {colors["html_fg"]};
            border: 1px solid {colors["nav_border"]};
            border-radius: 12px;
            padding: 8px;
            font-size: 14px;
        }}
        QListWidget::item {{
            min-height: 34px;
            padding: 8px 12px;
            margin: 2px 0;
            border-radius: 8px;
        }}
        QListWidget::item:selected {{
            background: {colors["nav_selected_bg"]};
            color: {selected_fg};
            border: 1px solid {colors["nav_selected_border"]};
            font-weight: 700;
        }}
        QListWidget::item:hover {{
            background: {colors["nav_hover"]};
        }}
        QScrollArea {{
            border: none;
            background: transparent;
        }}
    """
def _help_html(theme: str, content: str) -> str:
    colors = _help_theme_values(theme)
    return f"""
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                color: {colors["html_fg"]};
                background: {colors["html_bg"]};
                line-height: 1.55;
                margin: 0;
            }}
            a {{
                color: {colors["accent"]};
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
            .card {{
                border: 1px solid {colors["card_border"]};
                border-radius: 12px;
                padding: 14px 16px;
                margin-bottom: 12px;
                background: {colors["card_bg"]};
            }}
            .warn {{
                background: {colors["warn_bg"]};
                border-color: {colors["warn_border"]};
            }}
            .ok {{
                background: {colors["ok_bg"]};
                border-color: {colors["ok_border"]};
            }}
            .h1 {{
                font-size: 20px;
                font-weight: 700;
                margin: 0 0 8px 0;
                color: {colors["html_fg"]};
            }}
            .h2 {{
                font-size: 15px;
                font-weight: 700;
                margin: 0 0 8px 0;
                color: {colors["accent"]};
            }}
            .muted {{
                color: {colors["muted"]};
            }}
            .badge {{
                display: inline-block;
                padding: 2px 8px;
                border-radius: 999px;
                font-size: 11px;
                font-weight: 700;
                background: {colors["badge_bg"]};
                color: {colors["badge_fg"]};
                margin-bottom: 8px;
            }}
            .small {{
                font-size: 12px;
                color: {colors["muted"]};
            }}
            code {{
                font-family: 'Cascadia Code', 'Consolas', monospace;
                background: {colors["code_bg"]};
                padding: 2px 6px;
                border-radius: 6px;
            }}
            pre {{
                font-family: 'Cascadia Code', 'Consolas', monospace;
                background: {colors["code_bg"]};
                padding: 10px 12px;
                border-radius: 8px;
                white-space: pre-wrap;
                border: 1px solid {colors["card_border"]};
                overflow-wrap: anywhere;
            }}
            ul, ol {{
                margin-top: 6px;
                margin-bottom: 0;
                padding-left: 22px;
            }}
            li {{
                margin-bottom: 4px;
            }}
            .table {{
                width: 100%;
                border-collapse: collapse;
            }}
            .table td {{
                padding: 7px 8px;
                border-bottom: 1px solid {colors["card_border"]};
                vertical-align: top;
            }}
            .table .section {{
                font-weight: 700;
                color: {colors["accent"]};
                background: {colors["code_bg"]};
            }}
            .kbd {{
                display: inline-block;
                min-width: 70px;
                padding: 2px 8px;
                border-radius: 6px;
                border: 1px solid {colors["card_border"]};
                background: {colors["code_bg"]};
                font-family: 'Cascadia Code', 'Consolas', monospace;
                font-size: 12px;
                text-align: center;
            }}
        </style>
        {content}
    """
__all__ = [
    '_help_dialog_qss',
    '_help_html',
    '_help_theme_values',
    '_image_edit_dialog_qss',
    '_theme_app_qss',
    '_theme_control_qss',
    '_theme_is_dark',
]
register_globals('shared', globals(), __all__)
