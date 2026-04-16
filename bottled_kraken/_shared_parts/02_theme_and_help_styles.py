def _theme_app_qss(theme: str) -> str:
    if theme == "dark":
        base = """
            QWidget {
                background: #2b2b2b;
                color: #f3f4f6;
            }
            QMainWindow, QDialog, QMessageBox, QInputDialog, QProgressDialog {
                background: #1f232a;
                color: #f3f4f6;
            }
            QLabel, QGroupBox {
                color: #f3f4f6;
            }
            QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox,
            QComboBox, QListWidget, QTreeWidget, QTableWidget {
                background: #2b3038;
                color: #f3f4f6;
                border: 1px solid #4b5563;
                selection-background-color: #2563eb;
                selection-color: white;
            }
            QPushButton, QToolButton {
                color: #f3f4f6;
                background: #2b3038;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 5px 10px;
            }
            QPushButton:hover, QToolButton:hover {
                background: #343a44;
                border-color: #60a5fa;
            }
            QPushButton:pressed, QToolButton:pressed {
                background: #3f4652;
            }
            QPushButton:disabled, QToolButton:disabled {
                color: #9ca3af;
                background: #252a31;
                border-color: #3f4652;
            }
            QMenuBar {
                background: #20242b;
                color: #f3f4f6;
            }
            QMenuBar::item:selected {
                background: #2f3540;
            }
            QMenu {
                background: #1f232a;
                color: #f3f4f6;
                border: 1px solid #4b5563;
            }
            QMenu::item:selected {
                background: #2563eb;
                color: white;
            }
            QHeaderView::section {
                background: #313844;
                color: #f3f4f6;
                border: 1px solid #4b5563;
                padding: 4px;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: #232830;
            }
        """
    else:
        base = """
            QWidget {
                background: #f0f0f0;
                color: #000000;
            }
            QMainWindow, QDialog, QMessageBox, QInputDialog, QProgressDialog {
                background: #efefef;
                color: #000000;
            }
            QLabel, QGroupBox {
                color: #000000;
            }
            QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox,
            QComboBox, QListWidget, QTreeWidget, QTableWidget {
                background: #ffffff;
                color: #000000;
                border: 1px solid #b8b8b8;
                selection-background-color: #3399ff;
                selection-color: #ffffff;
            }
            QPushButton, QToolButton {
                color: #000000;
                background: #f7f7f7;
                border: 1px solid #b8b8b8;
                border-radius: 6px;
                padding: 5px 10px;
            }
            QPushButton:hover, QToolButton:hover {
                background: #ececec;
                border-color: #7aaef7;
            }
            QPushButton:pressed, QToolButton:pressed {
                background: #dddddd;
            }
            QPushButton:disabled, QToolButton:disabled {
                color: #8a8a8a;
                background: #f0f0f0;
                border-color: #cfcfcf;
            }
            QMenuBar {
                background: #efefef;
                color: #000000;
            }
            QMenuBar::item:selected {
                background: #dcdcdc;
            }
            QMenu {
                background: #ffffff;
                color: #000000;
                border: 1px solid #b8b8b8;
            }
            QMenu::item:selected {
                background: #3399ff;
                color: #ffffff;
            }
            QHeaderView::section {
                background: #e8e8e8;
                color: #000000;
                border: 1px solid #c8c8c8;
                padding: 4px;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: #efefef;
            }
        """
    return base + "\n" + _theme_control_qss(theme)

def _image_edit_dialog_qss(theme: str) -> str:
    if theme == "dark":
        base = """
            QDialog {
                background: #1f232a;
                color: #f3f4f6;
            }
            QLabel, QPushButton {
                color: #f3f4f6;
                font-size: 13px;
            }
            QPushButton {
                background: #2b3038;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 6px 10px;
            }
            QPushButton:hover {
                background: #343a44;
                border-color: #60a5fa;
            }
            QPushButton:pressed {
                background: #3f4652;
            }
            QPushButton:checked {
                background: #1d4ed8;
                border-color: #60a5fa;
                color: white;
            }
        """
    else:
        base = """
            QDialog {
                background: #f6f7fb;
                color: #1f2937;
            }
            QLabel, QPushButton {
                color: #1f2937;
                font-size: 13px;
            }
            QPushButton {
                background: #ffffff;
                border: 1px solid #cfd5df;
                border-radius: 6px;
                padding: 6px 10px;
            }
            QPushButton:hover {
                background: #f0f4ff;
                border-color: #7aaef7;
            }
            QPushButton:pressed {
                background: #e5edff;
            }
            QPushButton:checked {
                background: #3399ff;
                border-color: #7aaef7;
                color: white;
            }
        """
    return base + "\n" + _theme_control_qss(theme)

def _help_theme_values(theme: str) -> Dict[str, str]:
    if theme == "dark":
        return {
            "html_bg": "#1f232a",
            "html_fg": "#f3f4f6",
            "card_bg": "#2b3038",
            "card_border": "#4b5563",
            "accent": "#60a5fa",
            "muted": "#cbd5e1",
            "badge_bg": "#1d4ed8",
            "badge_fg": "#ffffff",
            "warn_bg": "#3b2b00",
            "warn_border": "#f59e0b",
            "ok_bg": "#0f2d1f",
            "ok_border": "#34d399",
            "code_bg": "#20242b",
            "nav_bg": "#2b3038",
            "nav_border": "#4b5563",
            "nav_hover": "#374151",
            "nav_selected_bg": "#1d4ed8",
            "nav_selected_border": "#60a5fa",
            "button_bg": "#2b3038",
            "button_hover": "#343a44",
            "button_border": "#4b5563",
            "dialog_bg": "#1f232a",
            "browser_bg": "#2b3038",
            "browser_border": "#4b5563",
        }
    return {
        "html_bg": "#f6f7fb",
        "html_fg": "#1f2937",
        "card_bg": "#ffffff",
        "card_border": "#e3e7ef",
        "accent": "#1d4ed8",
        "muted": "#6b7280",
        "badge_bg": "#dbeafe",
        "badge_fg": "#1d4ed8",
        "warn_bg": "#fff7e6",
        "warn_border": "#f59e0b",
        "ok_bg": "#eefbf3",
        "ok_border": "#34d399",
        "code_bg": "#f3f6fb",
        "nav_bg": "#ffffff",
        "nav_border": "#d9dce3",
        "nav_hover": "#f3f6fb",
        "nav_selected_bg": "#dbeafe",
        "nav_selected_border": "#93c5fd",
        "button_bg": "#ffffff",
        "button_hover": "#f0f4ff",
        "button_border": "#cfd5df",
        "dialog_bg": "#f6f7fb",
        "browser_bg": "#ffffff",
        "browser_border": "#d9dce3",
    }

def _help_dialog_qss(theme: str) -> str:
    colors = _help_theme_values(theme)
    selected_fg = "#ffffff" if theme == "dark" else "#1e3a8a"
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
