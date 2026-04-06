import os

os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["LANG"] = "C.UTF-8"
os.environ["LC_ALL"] = "C.UTF-8"

import sys
import locale
import platform

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    locale.setlocale(locale.LC_ALL, "")
except Exception:
    pass

try:
    locale.getpreferredencoding = lambda do_setlocale=True: "UTF-8"
except Exception:
    pass

import time
import math
import statistics
import json
import csv
import warnings
import re
import traceback
import gc
import html
from dataclasses import dataclass, field
from typing import Optional, List, Any, Tuple, Dict, Callable
import fitz
import ctypes
import shutil
import subprocess
import urllib.request
import urllib.error
import urllib.parse
import http.client
import base64
import socket
from io import BytesIO
import queue
import wave
import threading
import numpy as np
import sounddevice as sd

try:
    import pyi_splash
except Exception:
    pyi_splash = None

# GUI-Framework
from PySide6.QtCore import (Qt, QThread, Signal, QRectF, QUrl, QTimer,
                            QSize, QPointF, QEvent, QPoint, QDateTime, QLocale,
                            QCoreApplication, QSettings)
from PySide6.QtGui import (
    QPixmap, QPen, QBrush, QColor, QFont, QDragEnterEvent, QDropEvent, QAction,
    QKeySequence, QActionGroup, QIcon, QPalette, QShortcut, QDesktopServices,
    QPainter
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox,
    QLabel, QWidget, QPushButton, QProgressBar, QProgressDialog,
    QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QGraphicsSimpleTextItem, QSplitter, QStatusBar,
    QMenu, QTableWidget, QTableWidgetItem, QHeaderView, QToolBar,
    QAbstractItemView, QInputDialog, QDialog, QDialogButtonBox, QRadioButton,
    QSpinBox, QFormLayout, QPlainTextEdit,
    QToolButton, QLineEdit, QTextEdit,
    QTextBrowser, QScrollArea, QTreeWidget, QTreeWidgetItem, QGraphicsLineItem,
    QSizePolicy, QCheckBox, QSlider, QStyleOptionButton,
    QStyledItemDelegate, QStyleOptionViewItem, QStyle
)

# PySide-Helfer zur Objekt-Validitätsprüfung
from shiboken6 import isValid

# Bild & PDF
from PIL import Image, ImageDraw, ImageOps, ImageEnhance
from PIL.ImageQt import ImageQt
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader

# Kraken & ML (Machine Learning)
warnings.filterwarnings("ignore", message="Using legacy polygon extractor*", category=UserWarning)
from kraken import blla, rpred, serialization, containers
from kraken.lib import models, vgsl
import torch

# -----------------------------
# KONSTANTEN
# -----------------------------
READING_MODES = {
    "TB_LR": 0,
    "TB_RL": 1,
    "BT_LR": 2,
    "BT_RL": 3,
}

STATUS_WAITING = 0
STATUS_PROCESSING = 1
STATUS_DONE = 2
STATUS_ERROR = 3
STATUS_AI_PROCESSING = 4
STATUS_EXPORTING = 5

STATUS_ICONS = {
    STATUS_WAITING: "⏳",
    STATUS_PROCESSING: "⚙️",
    STATUS_DONE: "✅",
    STATUS_ERROR: "❌",
    STATUS_AI_PROCESSING: "🤖",
    STATUS_EXPORTING: "📄"
}

# Queue-Spalten
QUEUE_COL_NUM = 0
QUEUE_COL_CHECK = 1
QUEUE_COL_FILE = 2
QUEUE_COL_STATUS = 3

THEMES = {
    "bright": {
        "bg": "#f0f0f0",
        "fg": "#000000",
        "canvas_bg": "#f2f2f2",
        "table_base": QColor(240, 240, 240),
        "toolbar_text": "#000000",
        "toolbar_border": "#000000",
    },
    "dark": {
        "bg": "#2b2b2b",
        "fg": "#ffffff",
        "canvas_bg": "#1e1e1e",
        "table_base": QColor(43, 43, 43),
        "toolbar_text": "#ffffff",
        "toolbar_border": "#ffffff",
    }
}

ZENODO_URL = "https://zenodo.org/communities/ocr_models/records?q=&l=list&p=1&s=10&sort=mostdownloaded"
SUPPORTED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
SUPPORTED_PDF_EXTS = {".pdf"}

KRAKEN_MODELS_DIR = (
    os.path.dirname(sys.executable)
    if getattr(sys, "frozen", False)
    else os.path.dirname(os.path.abspath(sys.argv[0]))
)

STATUS_VOICE_RECORDING = 6

STATUS_ICONS[STATUS_VOICE_RECORDING] = "🎤"

VOICE_SAMPLE_RATE = 16000
VOICE_CHANNELS = 1
VOICE_BLOCKSIZE = 0

def resource_path(relative_path: str) -> str:
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


def is_supported_input(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    return ext in SUPPORTED_IMAGE_EXTS or ext in SUPPORTED_PDF_EXTS


def is_project_file(path: str) -> bool:
    return os.path.splitext(path)[1].lower() == ".json"


def is_supported_drop_or_paste_file(path: str) -> bool:
    return is_supported_input(path) or is_project_file(path)


def _load_image_gray(path: str) -> Image.Image:
    return Image.open(path).convert("L")


def _load_image_color(path: str) -> Image.Image:
    return Image.open(path).convert("RGB")


def _theme_control_qss(theme: str) -> str:
    if theme == "dark":
        return """
            QCheckBox, QRadioButton {
                spacing: 6px;
                color: #f3f4f6;
            }

            QCheckBox::indicator,
            QRadioButton::indicator,
            QTableWidget::indicator,
            QTreeWidget::indicator,
            QListWidget::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #94a3b8;
                border-radius: 3px;
                background: #2f3540;
            }

            QCheckBox::indicator:hover,
            QRadioButton::indicator:hover,
            QTableWidget::indicator:hover,
            QTreeWidget::indicator:hover,
            QListWidget::indicator:hover {
                border: 1px solid #60a5fa;
                background: #374151;
            }

            QCheckBox::indicator:checked,
            QRadioButton::indicator:checked,
            QTableWidget::indicator:checked,
            QTreeWidget::indicator:checked,
            QListWidget::indicator:checked {
                border: 1px solid #60a5fa;
                background: #2563eb;
            }

            QCheckBox::indicator:checked:hover,
            QRadioButton::indicator:checked:hover,
            QTableWidget::indicator:checked:hover,
            QTreeWidget::indicator:checked:hover,
            QListWidget::indicator:checked:hover {
                border: 1px solid #93c5fd;
                background: #3b82f6;
            }

            QSlider::groove:horizontal {
                height: 8px;
                background: #374151;
                border-radius: 4px;
            }

            QSlider::sub-page:horizontal {
                background: #2563eb;
                border-radius: 4px;
            }

            QSlider::add-page:horizontal {
                background: #374151;
                border-radius: 4px;
            }

            QSlider::handle:horizontal {
                background: #60a5fa;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
                border: 1px solid #93c5fd;
            }

            QSlider::handle:horizontal:hover {
                background: #93c5fd;
            }
        """

    return """
        QCheckBox, QRadioButton {
            spacing: 6px;
            color: #000000;
        }

        QCheckBox::indicator,
        QRadioButton::indicator,
        QTableWidget::indicator,
        QTreeWidget::indicator,
        QListWidget::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid #7c8aa5;
            border-radius: 3px;
            background: #ffffff;
        }

        QCheckBox::indicator:hover,
        QRadioButton::indicator:hover,
        QTableWidget::indicator:hover,
        QTreeWidget::indicator:hover,
        QListWidget::indicator:hover {
            border: 1px solid #3399ff;
            background: #f3f8ff;
        }

        QCheckBox::indicator:checked,
        QRadioButton::indicator:checked,
        QTableWidget::indicator:checked,
        QTreeWidget::indicator:checked,
        QListWidget::indicator:checked {
            border: 1px solid #3399ff;
            background: #3399ff;
        }

        QCheckBox::indicator:checked:hover,
        QRadioButton::indicator:checked:hover,
        QTableWidget::indicator:checked:hover,
        QTreeWidget::indicator:checked:hover,
        QListWidget::indicator:checked:hover {
            border: 1px solid #1d4ed8;
            background: #60a5fa;
        }

        QSlider::groove:horizontal {
            height: 8px;
            background: #d9dee7;
            border-radius: 4px;
        }

        QSlider::sub-page:horizontal {
            background: #3399ff;
            border-radius: 4px;
        }

        QSlider::add-page:horizontal {
            background: #d9dee7;
            border-radius: 4px;
        }

        QSlider::handle:horizontal {
            background: #ffffff;
            width: 18px;
            margin: -5px 0;
            border-radius: 9px;
            border: 1px solid #7aaef7;
        }

        QSlider::handle:horizontal:hover {
            background: #f0f6ff;
            border: 1px solid #3399ff;
        }
    """


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


def _help_pre(text: str) -> str:
    return f"<pre>{html.escape(text)}</pre>"

# -----------------------------
# ÜBERSETZUNGEN
# -----------------------------
TRANSLATIONS = {'de': {'dlg_filter_img': 'Bilder/PDF (*.png *.jpg *.jpeg *.tif *.tiff *.bmp *.webp *.pdf)',
        'pdf_render_title': 'PDF wird vorbereitet',
        'pdf_render_label': 'Seiten werden gerendert… ({}/{}): {}',
        'app_title': 'Bottled Kraken',
        'toolbar_main': 'Werkzeugleiste',
        'toolbar_language': 'Sprache',
        'toolbar_theme_tooltip': 'Zwischen Hell- und Dunkelmodus wechseln',
        'toolbar_language_tooltip': 'Sprache einstellen',
        'menu_file': '&Datei',
        'menu_edit': '&Bearbeiten',
        'menu_export': 'Exportieren als...',
        'menu_exit': 'Beenden',
        'menu_models': '&Kraken-Optionen',
        'menu_options': '&Optionen',
        'menu_languages': 'Sprachen',
        'menu_hw': 'CPU/GPU',
        'menu_reading': 'Leserichtung',
        'menu_appearance': 'Erscheinungsbild',
        'act_clear_rec': 'Recognition-Modell entfernen',
        'act_clear_seg': 'Segmentierungs-Modell entfernen',
        'act_paste_clipboard': 'Aus Zwischenablage einfügen',
        'log_toggle_show': 'Log',
        'log_toggle_hide': 'Log',
        'menu_export_log': 'Log als .txt exportieren...',
        'dlg_save_log': 'Log speichern',
        'dlg_filter_txt': 'Text (*.txt)',
        'log_started': 'Programm gestartet.',
        'log_queue_cleared': 'Queue geleert.',
        'lang_de': 'Deutsch',
        'lang_en': 'English',
        'lang_fr': 'Français',
        'hw_cpu': 'CPU',
        'hw_cuda': 'GPU – CUDA (NVIDIA)',
        'hw_rocm': 'GPU – ROCm (AMD)',
        'hw_mps': 'GPU – MPS (Apple)',
        'act_undo': 'Rückgängig',
        'act_redo': 'Wiederholen',
        'msg_hw_not_available': 'Diese Hardware ist auf diesem System nicht verfügbar. Wechsle zu CPU.',
        'msg_using_device': 'Verwende Gerät: {}',
        'msg_detected_gpu': 'Erkannt: {}',
        'msg_device_cpu': 'CPU',
        'msg_device_cuda': 'CUDA',
        'msg_device_rocm': 'ROCm',
        'msg_device_mps': 'MPS',
        'act_add_files': 'Datei(en) laden...',
        'act_download_model': 'Modell herunterladen (Zenodo)',
        'act_delete': 'Löschen',
        'act_rename': 'Umbenennen...',
        'act_clear_queue': 'Wartebereich leeren',
        'act_start_ocr': 'Starte Kraken OCR',
        'act_stop_ocr': 'Stopp',
        'act_re_ocr': 'Wiederholen',
        'act_re_ocr_tip': 'Ausgewählte Datei(en) erneut verarbeiten',
        'act_overlay_show': 'Overlay-Boxen anzeigen',
        'status_ready': 'Bereit.',
        'status_waiting': 'Wartet',
        'status_processing': 'Verarbeite...',
        'status_done': 'Fertig',
        'status_error': 'Fehler',
        'lbl_queue': 'Wartebereich:',
        'lbl_lines': 'Erkannte Zeilen:',
        'col_file': 'Datei',
        'col_status': 'Status',
        'drop_hint': 'Datei(en) hierher ziehen und ablegen',
        'queue_drop_hint': 'Datei(en) hierher ziehen und ablegen',
        'queue_load_title': 'Dateien werden geladen',
        'queue_load_label': 'Lade Datei {}/{}: {}',
        'queue_load_cancelled': 'Dateiladen abgebrochen.',
        'queue_load_pdf_started': 'PDF wird in den Wartebereich geladen: {}',
        'info_title': 'Information',
        'warn_title': 'Warnung',
        'err_title': 'Fehler',
        'theme_bright': 'Hell',
        'theme_dark': 'Dunkel',
        'warn_queue_empty': 'Wartebereich ist leer oder alle Elemente wurden verarbeitet.',
        'warn_select_done': 'Keine Datei(en) für erneutes OCRn geladen.',
        'warn_need_rec': 'Bitte wählen Sie zuerst ein Format-Modell (Recognition) aus.',
        'warn_need_seg': 'Bitte wählen Sie zuerst ein Segmentierungs-Modell aus.',
        'msg_stopping': 'Breche ab...',
        'msg_finished': 'Batch abgeschlossen.',
        'msg_device': 'Gerät gesetzt auf: {}',
        'msg_exported': 'Exportiert: {}',
        'msg_loaded_rec': 'Format-Modell: {}',
        'msg_loaded_seg': 'Segmentierungs-Modell: {}',
        'err_load': 'Bild kann nicht geladen werden: {}',
        'dlg_title_rename': 'Umbenennen',
        'dlg_label_name': 'Neuer Dateiname:',
        'dlg_save': 'Speichern',
        'dlg_load_img': 'Bilder wählen',
        'dlg_choose_rec': 'Recognition-Modell: ',
        'dlg_choose_seg': 'Segmentierungs-Modell: ',
        'dlg_filter_model': 'Modelle (*.mlmodel)',
        'reading_tb_lr': 'Oben → Unten + Links → Rechts',
        'reading_tb_rl': 'Oben → Unten + Rechts → Links',
        'reading_bt_lr': 'Unten → Oben + Links → Rechts',
        'reading_bt_rl': 'Unten → Oben + Rechts → Links',
        'line_menu_move_up': 'Zeile nach oben',
        'line_menu_move_down': 'Zeile nach unten',
        'line_menu_delete': 'Zeile löschen',
        'line_menu_add_above': 'Zeile darüber hinzufügen',
        'line_menu_add_below': 'Zeile darunter hinzufügen',
        'line_menu_draw_box': 'Overlay-Box zeichnen',
        'line_menu_edit_box': 'Overlay-Box bearbeiten (ziehen/skalieren)',
        'line_menu_move_to': 'Zeile verschieben zu…',
        'dlg_new_line_title': 'Neue Zeile',
        'dlg_new_line_label': 'Text der neuen Zeile:',
        'dlg_move_to_title': 'Zeile verschieben',
        'dlg_move_to_label': 'Ziel-Zeilennummer (1…):',
        'canvas_menu_add_box_draw': 'Overlay-Box hinzufügen (zeichnen)',
        'canvas_menu_delete_box': 'Overlay-Box löschen',
        'canvas_menu_edit_box': 'Overlay-Box bearbeiten…',
        'canvas_menu_select_line': 'Zeile auswählen',
        'dlg_box_title': 'Overlay-Box',
        'dlg_box_left': 'links',
        'dlg_box_top': 'oben',
        'dlg_box_right': 'rechts',
        'dlg_box_bottom': 'unten',
        'dlg_box_apply': 'Anwenden',
        'export_choose_mode_title': 'Export',
        'export_mode_all': 'Alle Dateien exportieren',
        'export_mode_selected': 'Ausgewählte Dateien exportieren',
        'export_select_files_title': 'Datei(en) auswählen',
        'export_select_files_hint': 'Wählen Sie die Datei(en) für den Export:',
        'export_choose_folder': 'Zielordner wählen',
        'export_need_done': 'Mindestens eine ausgewählte Datei ist nicht fertig verarbeitet.',
        'export_none_selected': 'Keine Datei(en) ausgewählt.',
        'undo_nothing': 'Nichts zum Rückgängig machen.',
        'redo_nothing': 'Nichts zum Wiederholen.',
        'overlay_only_after_ocr': 'Overlay-Bearbeitung ist erst nach abgeschlossener OCR möglich.',
        'new_line_from_box_title': 'Neue Zeile',
        'new_line_from_box_label': 'Text für die neue Zeile (optional):',
        'log_added_files': '{} Datei(en) zur Queue hinzugefügt.',
        'log_ocr_started': 'OCR gestartet: {} Datei(en), Device={}, Reading={}',
        'log_stop_requested': 'OCR-Abbruch angefordert.',
        'log_file_started': 'Starte Datei: {}',
        'log_file_done': 'Fertig: {} ({} Zeilen)',
        'log_file_error': 'Fehler: {} -> {}',
        'log_export_done': 'Export abgeschlossen: {} Datei(en) als {} nach {}',
        'log_export_single': 'Export: {} -> {}',
        'log_export_log_done': 'Log exportiert: {}',
        'act_ai_revise': 'LM-Überarbeitung',
        'act_ai_revise_tip': 'OCR-Text mit lokalem LLM überarbeiten',
        'msg_ai_started': 'Überarbeitung gestartet...',
        'msg_ai_done': 'Überarbeitung abgeschlossen.',
        'msg_ai_model_set': 'KI-Modell-ID: {}',
        'msg_ai_disabled': 'Überarbeitung nicht möglich.',
        'warn_lm_url_invalid': 'Es wurde leider keine gültige LM-Server-Adresse eingetragen.\n'
                               'Bitte beachte die Hinweise und versuche eine andere Adresse.',
        'warn_need_done_for_ai': 'Bitte zuerst eine fertig OCR-verarbeitete Datei auswählen.',
        'warn_need_ai_model': 'Kein Modell über die konfigurierte LM-Server-URL gefunden. Bitte einen lokalen '
                              'OpenAI-kompatiblen Server starten oder eine gültige URL bzw. Modell-ID setzen (z. B. LM '
                              'Studio, Ollama, Jan, GPT4All, text-generation-webui, LocalAI oder vLLM).',
        'warn_ai_server': 'Lokaler LM-Server nicht erreichbar. Bitte Modell laden und den OpenAI-kompatiblen Server '
                          'starten.',
        'dlg_choose_ai_model': 'LM-Modell-Identifier',
        'dlg_choose_ai_model_label': 'Optionale Modell-ID. Leer lassen, wenn das laufende Modell des eingetragenen '
                                     'Servers automatisch verwendet werden soll:',
        'log_ai_started': 'Überarbeitung gestartet: {}',
        'log_ai_done': 'Überarbeitung abgeschlossen: {}',
        'log_ai_error': 'Überarbeitung Fehler: {} -> {}',
        'status_ai_processing': 'Überarbeitung...',
        'status_exporting': 'Exportiere...',
        'menu_project_save': 'Projekt speichern',
        'menu_project_save_as': 'Projekt speichern unter...',
        'menu_project_load': 'Projekt laden...',
        'dlg_filter_project': 'Bottled-Kraken Projekt (*.json)',
        'msg_project_saved': 'Projekt gespeichert: {}',
        'msg_project_loaded': 'Projekt geladen: {}',
        'warn_project_load_failed': 'Projekt konnte nicht geladen werden: {}',
        'warn_project_save_failed': 'Projekt konnte nicht gespeichert werden: {}',
        'warn_project_file_missing': 'Datei(en) nicht gefunden: {}',
        'line_menu_swap_with': 'Zeile tauschen mit…',
        'dlg_swap_title': 'Zeile(n) tauschen',
        'dlg_swap_label': 'Mit Zeilennummer tauschen (1…):',
        'act_voice_fill': 'Zeile(n) diktieren',
        'act_voice_fill_tip': 'Zeile(n) per Mikrofon mit faster-whisper überschreiben',
        'act_voice_stop': 'Aufnahme stoppen',
        'msg_voice_started': 'Sprachaufnahme gestartet...',
        'msg_voice_stopped': 'Sprachaufnahme beendet. Transkribiere...',
        'msg_voice_done': 'Sprachimport abgeschlossen.',
        'msg_voice_cancelled': 'Sprachaufnahme abgebrochen.',
        'warn_voice_need_done': 'Bitte zuerst eine fertig OCR-verarbeitete Datei auswählen.',
        'warn_voice_model_missing': 'Faster-Whisper-Modellordner wurde nicht gefunden.',
        'status_voice_recording': 'Spricht ein...',
        'lines_tree_header': 'Erkannte Zeilen und Wörter',
        'col_loaded_files': 'Geladene Datei(en)',
        'btn_rec_model_empty': 'Rec-Modell: -',
        'btn_rec_model_value': 'Rec-Modell: {}',
        'btn_seg_model_empty': 'Seg-Modell: -',
        'btn_seg_model_value': 'Seg-Modell: {}',
        'act_load_rec_model': 'Recognition-Modell laden...',
        'act_load_seg_model': 'Segmentierungs-Modell laden...',
        'submenu_available_kraken_models': 'Verfügbare Kraken-Modelle',
        'submenu_available_ai_models': 'Verfügbare LM-Modelle',
        'submenu_available_whisper_models': 'Verfügbare Whisper-Modelle',
        'btn_cancel': 'Abbrechen',
        'progress_status_ready': 'Bereit',
        'voice_record_title': '🎤 Zeile mit Audio verändern',
        'voice_record_info': 'Steuerung der Audioaufnahme:',
        'voice_record_start': 'Aufnahme starten',
        'voice_record_stop': 'Aufnahme stoppen',
        'voice_record_processing': 'Whisper verarbeitet Audio … bitte kurz warten.',
        'warn_select_line_first': 'Bitte zuerst eine Zeile auswählen.',
        'warn_selected_line_invalid': 'Die ausgewählte Zeile ist ungültig.',
        'warn_whisper_model_not_loaded': "Es ist kein geladenes Whisper-Modell aktiv. Bitte unter 'Whisper-Optionen' "
                                         'ein Modell wählen.',
        'warn_no_microphone_available': 'Es ist kein Mikrofon verfügbar.',
        'log_voice_stopping': 'Sprachaufnahme wird gestoppt...',
        'image_edit_title': 'Bildbearbeitung – {}',
        'image_edit_erase_rect': 'Bereich entfernen (Rechteck)',
        'image_edit_erase_ellipse': 'Bereich entfernen (Kreis)',
        'image_edit_erase_clear': 'Entfernbereich löschen',
        'warn_select_image_or_pdf_page': 'Bitte zuerst ein Bild oder eine PDF-Seite auswählen.',
        'warn_image_load_failed_detail': 'Bild konnte nicht geladen werden:\n{}',
        'info_no_marked_images_found': 'Keine markierten Bilder gefunden.',
        'msg_image_edit_selected_applied': 'Bildbearbeitung für markierte Bilder übernommen.',
        'msg_image_edit_all_applied': 'Bildbearbeitung für alle Bilder übernommen.',
        'log_image_edit_error': 'Bildbearbeitung Fehler: {} -> {}',
        'act_help': 'Hinweise',
        'act_ai_revise_all': 'Alle überarbeiten',
        'act_ai_revise_all_tip': 'Alle fertig erkannten Dateien überarbeiten',
        'warn_select_multiple_lines_first': 'Bitte zuerst mehrere Zeilen auswählen.',
        'msg_ai_selected_lines_started': 'LM-Überarbeitung für {} ausgewählte Zeilen gestartet...',
        'log_ai_multi_started': 'LM-Mehrfachzeilenüberarbeitung gestartet: {} | Zeilen {}',
        'dlg_ai_multi_title': 'KI-Mehrfachzeilenüberarbeitung',
        'dlg_ai_multi_status': 'Überarbeite {} ausgewählte Zeilen …',
        'btn_import_lines': 'Zeile(n) importieren',
        'btn_import_lines_tip': 'Erkannte Zeilen aus TXT/JSON laden',
        'act_import_lines_current': 'Für aktuelles Bild',
        'act_import_lines_selected': 'Für ausgewählte Bilder',
        'act_import_lines_all': 'Für alle Bilder',
        'warn_import_unsupported_format': 'Nicht unterstütztes Importformat: {}',
        'warn_import_no_usable_lines': 'Die Importdatei enthält keine verwertbaren Zeilen.',
        'info_no_current_image_loaded': 'Kein aktuelles Bild geladen.',
        'dlg_import_lines_current': 'Zeile(n) importieren',
        'info_no_images_selected_or_marked': 'Keine Bilder ausgewählt oder markiert.',
        'dlg_import_lines_selected': 'Zeilen-Dateien für ausgewählte Bilder laden',
        'info_no_images_loaded': 'Keine Bilder geladen.',
        'dlg_import_lines_all': 'Zeilen-Dateien für alle Bilder laden',
        'warn_no_matching_import_for_selected': 'Keine Importdatei passt zu den ausgewählten Bildern.\n'
                                                '\n'
                                                'Die Dateinamen müssen über den Basisnamen passen.',
        'warn_no_matching_import_for_loaded': 'Keine Importdatei passt zu den geladenen Bildern.\n'
                                              '\n'
                                              'Die Dateinamen müssen über den Basisnamen passen.',
        'log_import_error': 'Import-Fehler: {} -> {}',
        'log_voice_import_started': 'Sprachimport gestartet: {} | Zeile {} | Mikrofon: {} | Modell: {}',
        'warn_voice_cancelled': 'Aufnahme abgebrochen.',
        'warn_voice_not_finished': 'Aufnahme wurde nicht regulär beendet.',
        'warn_voice_no_audio_data': 'Keine Audiodaten aufgenommen.',
        'voice_status_prepare_wav': 'Audiodatei wird vorbereitet...',
        'voice_status_load_whisper': 'Lade faster-whisper...',
        'voice_status_transcribe_line': 'Transkribiere ausgewählte Zeile lokal ({}/{})...',
        'voice_status_fallback_cpu': 'Initialisierung auf {}/{} fehlgeschlagen. Neuer Versuch mit CPU/int8 …',
        'voice_status_finalize': 'Bereite Text auf...',
        'voice_status_microphone_active': "Mikrofon aktiv … bitte sprechen. Zum Beenden 'Aufnahme stoppen' klicken.",
        'voice_status_input_device': 'Aufnahmegerät: {}',
        'audio_device_default_mic': 'Systemstandard-Mikrofon',
        'audio_device_generic': 'Gerät {}',
        'whisper_status_model': 'Modell: {}',
        'whisper_status_mic': 'Mikrofon: {}',
        'whisper_status_path': 'Pfad: {}',
        'dlg_whisper_model_dir': 'Whisper-Modellordner wählen',
        'msg_whisper_path_set': 'Whisper-Pfad gesetzt: {}',
        'warn_whisper_model_present': 'Das Faster-Whisper large-v3 Modell ist bereits vorhanden.\n'
                                      '\n'
                                      'Pfad:\n'
                                      '{}\n'
                                      '\n'
                                      'Ein erneuter Download ist nicht nötig.',
        'msg_whisper_model_already_present': 'Whisper-Modell bereits vorhanden: {}',
        'warn_whisper_download_start_failed': 'Download des Whisper-Modells konnte nicht gestartet werden:\n{}',
        'msg_whisper_download_start_failed': 'Whisper-Download konnte nicht gestartet werden.',
        'msg_whisper_model_loaded': 'Whisper-Modell geladen: {}',
        'info_whisper_model_downloaded': 'Das Faster-Whisper-Modell wurde erfolgreich heruntergeladen.\n'
                                         '\n'
                                         'Zielordner:\n'
                                         '{}',
        'msg_whisper_download_failed': 'Whisper-Download fehlgeschlagen.',
        'warn_whisper_download_failed': 'Download des Whisper-Modells fehlgeschlagen:\n{}',
        'dlg_help_title': 'Hinweise',
        'help_nav_quick': 'Ablauf',
        'help_nav_kraken': 'Kraken',
        'help_nav_lm_server': 'LM-Server',
        'help_nav_ssh': 'SSH-Tunnel',
        'help_nav_whisper': 'Whisper',
        'help_nav_shortcuts': 'Tastenkürzel',
        'help_nav_data_protection': 'Datenschutz',
        'help_nav_legal': 'Rechtliches',
        'help_whisper_download_label': '<b>Whisper-Modell per Button herunterladen:</b>',
        'help_os_windows': 'Windows',
        'help_os_arch': 'Arch',
        'help_os_debian': 'Debian',
        'help_os_fedora': 'Fedora',
        'help_os_macos': 'macOS',
        'whisper_hint_debian': 'Hinweis für Debian/Ubuntu/Linux Mint:\n'
                               'Die App verwendet hier automatisch eine eigene Python-Umgebung (venv),\n'
                               'damit kein PEP-668-Fehler mit dem System-Python entsteht.\n'
                               '\n'
                               'Falls das Erzeugen der venv scheitert, fehlen meist Systempakete.\n'
                               'Dann bitte einmal im Terminal ausführen:\n'
                               '\n'
                               'sudo apt update\n'
                               'sudo apt install -y python3-venv python3-pip ffmpeg portaudio19-dev',
        'whisper_hint_fedora': 'Optionaler Hinweis für Fedora:\n'
                               'Falls später Probleme mit sounddevice auftreten, können diese Systempakete helfen.\n'
                               '\n'
                               'sudo dnf install -y python3-pip ffmpeg portaudio-devel',
        'whisper_hint_arch': 'Optionaler Hinweis für Arch Linux:\n'
                             'Falls später Probleme mit sounddevice auftreten, können diese Systempakete helfen.\n'
                             '\n'
                             'sudo pacman -S --needed python-pip ffmpeg portaudio',
        'whisper_hint_macos': 'Optionaler Hinweis für macOS:\n'
                              'Falls später Probleme mit sounddevice auftreten, können diese Pakete helfen.\n'
                              '\n'
                              'brew install ffmpeg portaudio',
        'whisper_hint_windows': 'Optionaler Hinweis für Windows:\n'
                                'Normalerweise sind keine zusätzlichen Systempakete nötig.\n'
                                'Falls es später Audioprobleme gibt, liegt das meist eher an Treibern oder '
                                'Mikrofonrechten.',
        'whisper_hint_generic': 'Optionaler Hinweis:\n'
                                'Falls später Probleme mit sounddevice auftreten, können zusätzliche Systempakete '
                                'nötig sein.',
        'whisper_system_hint_dialog': 'Optionaler Systemhinweis:\n'
                                      '\n'
                                      '{}\n'
                                      '\n'
                                      'Der eigentliche Download läuft trotzdem nur über Python (sys.executable -m pip '
                                      '/ Python-API von huggingface_hub).',
        'warn_whisper_download_running': 'Es läuft bereits ein Whisper-Download.',
        'msg_whisper_download_prepare_target': 'Starte Requirement-Installation und Modell-Download nach: {}',
        'dlg_whisper_download_title': 'Whisper-Modell wird geladen',
        'dlg_whisper_download_prepare': 'Starte Whisper-Vorbereitung …',
        'hf_status_waiting_for_lock': 'Warte auf Dateisperre im Zielordner …',
        'hf_status_files_done': 'Dateien fertig: {}/{}',
        'hf_status_current_file': 'Aktuell: {}',
        'hf_status_last_finished': 'Zuletzt fertig: {}',
        'hf_status_download_done': 'Download abgeschlossen.',
        'hf_error_cancelled': 'Download abgebrochen.',
        'hf_error_hf_exit': "'hf download' wurde mit Exit-Code {} beendet.",
        'hf_error_command_exit': 'Befehl wurde mit Exit-Code {} beendet:\n{}',
        'hf_error_python_missing': 'Python oder ein benötigtes Modul wurde nicht gefunden.\n'
                                   '\n'
                                   'Bitte prüfen, ob die Anwendung mit einer funktionsfähigen Python-Umgebung läuft.',
        'hf_error_externally_managed': 'Die Python-Installation des Systems darf nicht direkt verändert werden.\n'
                                       '\n'
                                       'Die App sollte dafür automatisch eine eigene Umgebung benutzen.\n'
                                       'Falls das trotzdem passiert ist, fehlt wahrscheinlich python3-venv.\n'
                                       '\n'
                                       'Bitte einmal ausführen:\n'
                                       'sudo apt update\n'
                                       'sudo apt install -y python3-venv python3-pip',
        'hf_error_no_venv': 'Auf diesem System fehlt die Unterstützung für Python-venv.\n'
                            '\n'
                            'Bitte einmal ausführen:\n'
                            'sudo apt update\n'
                            'sudo apt install -y python3-venv python3-pip',
        'hf_error_python3_missing': 'python3 wurde nicht gefunden.\n\nBitte prüfen, ob Python 3 installiert ist.',
        'warn_invalid_line': 'Ungültige Zeile.',
        'btn_ai_model_value': 'KI: {}',
        'llm_status_value': 'LLM: {}',
        'lm_status_model_value': 'Modell: {}',
        'lm_mode_value': 'Modus: {}',
        'lm_server_value': 'Server: {}',
        'dlg_ai_title': 'KI-Überarbeitung',
        'dlg_ai_connecting': 'Verbinde mit lokalem LM-Server…',
        'dlg_ai_single_title': 'KI-Zeilenüberarbeitung',
        'dlg_ai_single_status': 'Überarbeite nur Zeile {} …',
        'msg_ai_single_started': 'LM-Überarbeitung für Zeile {} gestartet...',
        'log_ai_single_started': 'LM-Zeilenüberarbeitung gestartet: {} | Zeile {}',
        'msg_ai_multi_done': 'LM-Überarbeitung für {} ausgewählte Zeilen abgeschlossen.',
        'log_ai_multi_done': 'LM-Mehrfachzeilenüberarbeitung abgeschlossen: {} | Zeilen {}',
        'msg_ai_multi_cancelled': 'Mehrfachzeilenüberarbeitung abgebrochen.',
        'log_ai_multi_cancelled': 'LM-Mehrfachzeilenüberarbeitung abgebrochen: {}',
        'msg_ai_multi_failed': 'Mehrfachzeilenüberarbeitung fehlgeschlagen.',
        'log_ai_multi_failed': 'LM-Mehrfachzeilenüberarbeitung Fehler: {} -> {}',
        'msg_ai_batch_finished': 'KI-Batch abgeschlossen.',
        'log_ai_batch_debug_return': 'KI Batch Rückgabe für {}: {} Zeilen, OCR hatte {} Zeilen',
        'log_ai_batch_debug_old_first': 'ALT erste Zeile: {}',
        'log_ai_batch_debug_new_first': 'NEU erste Zeile: {}',
        'log_ai_batch_debug_all': 'NEU alle Zeilen: {}',
        'msg_ai_cancelled': 'Überarbeitung abgebrochen.',
        'ai_status_start_free_ocr': 'Starte freie KI-OCR: {}',
        'ai_status_step1_title': '1/3 Zeilenweise Box-OCR: {}',
        'ai_status_step1_line': '1/3 Box-OCR Zeile {}/{}: {}',
        'ai_status_step2_form': '2/3 Block-Kontext-OCR (Formularmodus): {}',
        'ai_status_step2_plain': '2/3 Block-Kontext-OCR: {}',
        'ai_status_step2_chunk': '2/3 Block-Kontext {}/{}: Zeilen {}-{}',
        'ai_status_step3_merge': '3/3 Merge: Box primär, Page nur wenn lokal konsistent: {}',
        'ai_status_done': 'KI-Überarbeitung abgeschlossen: {}',
        'ai_err_bad_scheme': 'Nicht unterstütztes Schema: {}',
        'ai_err_invalid_endpoint': 'Ungültiger Endpoint.',
        'ai_err_timeout': 'Zeitüberschreitung beim Warten auf LM Server.',
        'ai_err_invalid_json': 'Ungültige JSON-Antwort von LM Server: {}',
        'ai_err_http': 'HTTP-Fehler: {}\n{}',
        'ai_err_server_unreachable': 'LM Server nicht erreichbar: {}',
        'ai_err_no_choices': 'LM Server lieferte keine choices. Antwort:\n{}',
        'ai_err_reasoning_truncated': 'Das Modell hat nur reasoning_content geliefert und wurde vor der eigentlichen '
                                      'JSON-Antwort abgeschnitten (finish_reason=length). Erhöhe max_tokens oder '
                                      'verwende ein nicht-thinkendes Modell.',
        'ai_err_reasoning_only': 'Das Modell hat nur reasoning_content geliefert, aber keinen normalen content. '
                                 'Verwende am besten ein nicht-thinkendes Modell oder erzwinge text/json ohne '
                                 'reasoning.',
        'ai_err_no_content': 'LM Server lieferte keinen verwertbaren Antwortinhalt.',
        'ai_err_page_invalid_json': 'Seiten-OCR lieferte kein gültiges JSON-Objekt.\n\nExtrahierter Content:\n{}',
        'ai_err_page_invalid_lines': "Seiten-OCR lieferte kein gültiges Feld 'lines'.\n\nExtrahierter Content:\n{}",
        'ai_err_page_long_blocks': 'Seiten-OCR hat vermutlich mehrere Zielzeilen zu langen Blöcken zusammengezogen.',
        'ai_err_page_no_usable_lines': 'Seiten-OCR lieferte keine verwertbaren Zeilen: {}/{}',
        'ai_err_block_invalid_json': 'Block-OCR lieferte kein gültiges JSON-Objekt.\n\nExtrahierter Content:\n{}',
        'ai_err_block_invalid_lines': "Block-OCR lieferte kein gültiges Feld 'lines'.\n\nExtrahierter Content:\n{}",
        'ai_err_final_merge_count': 'Finale Merge-Ausgabe gab {} statt {} Zeilen zurück.',
        'help_html_quick': '\n'
                           '            <div class="card warn">\n'
                           '                <div class="h1">Ablauf</div>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <ol>\n'
                           '                    <li>Bild oder PDF laden</li>\n'
                           '                    <li>Optional: Bildbearbeitung zur Vorbereitung verwenden</li>\n'
                           '                    <li>Recognition-Modell laden</li>\n'
                           '                    <li>Segmentierungs-Modell laden</li>\n'
                           '                    <li>Kraken-OCR starten</li>\n'
                           '                    <li>Erkannte Zeilen prüfen und bei Bedarf korrigieren</li>\n'
                           '                    <li>Optional: LM-Überarbeitung oder Whisper verwenden</li>\n'
                           '                    <li>Ergebnis als TXT, CSV, JSON, ALTO, hOCR oder PDF exportieren</li>\n'
                           '                </ol>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">Vorbereitung</div>\n'
                           '                <span class="badge">Optional</span>\n'
                           '                <ul>\n'
                           '                    <li>Die Bildbearbeitung kann schon <b>vor</b> dem OCR-Lauf genutzt '
                           'werden, wenn ein Scan schlecht zugeschnitten, kontrastarm oder inhaltlich zu breit '
                           'ist.</li>\n'
                           '                    <li>Besonders praktisch sind dabei <b>Crop-Bereich</b>, '
                           '<b>Trennbalken</b>, <b>Grau</b>, <b>Kontrast</b> und <b>Smart-Splitting</b>.</li>\n'
                           '                    <li>So lassen sich Doppelseiten, Formularhälften, Randbereiche oder '
                           'störende Nachbarinhalte vor dem eigentlichen OCR-Durchlauf gezielt vorbereiten.</li>\n'
                           '                    <li>Das ist vor allem bei Aktenseiten, Formularen, Sammel-Scans und '
                           'unsauber digitalisierten Beständen hilfreich.</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">Nachbearbeitung</div>\n'
                           '                <span class="badge">Optional</span>\n'
                           '                <ul>\n'
                           '                    <li>LM-Modell über LM Studio oder einen anderen kompatiblen LM-Server '
                           'laden</li>\n'
                           '                    <li>OCR-Zeilen mit lokalem Sprachmodell sprachlich oder inhaltlich '
                           'glätten</li>\n'
                           '                    <li>Einzelne Zeilen per Mikrofon mit Faster-Whisper neu '
                           'einsprechen</li>\n'
                           '                    <li>Zeilen aus TXT oder JSON importieren</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">Overlay-Boxen &amp; Zeilen</div>\n'
                           '                <span class="badge">Optional</span>\n'
                           '                <ul>\n'
                           '                    <li>Zeilen und Overlay-Boxen können verschoben, geteilt, ergänzt oder '
                           'gelöscht werden.</li>\n'
                           '                    <li>Damit lässt sich die Zeilenstruktur vor einem erneuten '
                           'OCR-Durchlauf gezielt verbessern.</li>\n'
                           '                    <li>Besonders nützlich bei Formularen, Spaltenlayouts und fehlerhaft '
                           'segmentierten Handschriften.</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">Was macht Bottled Kraken?</div><br>\n'
                           '                Bottled Kraken kombiniert klassische OCR mit vorbereitender '
                           'Bildbearbeitung, manueller Nachbearbeitung und optionaler lokaler KI-Unterstützung.\n'
                           '                So kannst du schwer lesbare historische Drucke, Handschriften oder '
                           'Formularseiten schrittweise verbessern.\n'
                           '            </div>\n'
                           '        ',
        'help_html_kraken': '\n'
                            '            <div class="card">\n'
                            '                <div class="h1">Kraken</div><br>\n'
                            '                Kraken ist die OCR-/ATR-Basis von Bottled Kraken.\n'
                            '                Es handelt sich um ein Open-Source-System für automatische '
                            'Texterkennung,\n'
                            '                das besonders für historische Drucke, Handschriften und nicht-lateinische '
                            'Schriften entwickelt wurde.\n'
                            '            </div>\n'
                            '\n'
                            '            <div class="card">\n'
                            '                <div class="h2">Was ist für Bottled Kraken daran wichtig?</div>\n'
                            '                <ul>\n'
                            '                    <li><b>Segmentierung:</b> Erkennt Layout, Textregionen, Zeilen und '
                            'Lesereihenfolge.</li>\n'
                            '                    <li><b>Recognition:</b> Liest den eigentlichen Text aus den erkannten '
                            'Zeilen.</li>\n'
                            '                    <li><b>Modelle:</b> Segmentierung und Recognition laufen über '
                            'trainierte Modelle, die zum Material passen müssen.</li>\n'
                            '                </ul>\n'
                            '            </div>\n'
                            '\n'
                            '            <div class="card">\n'
                            '                <div class="h2">Typischer Kraken-Ablauf</div>\n'
                            '                <ol>\n'
                            '                    <li>Bild vorbereiten</li>\n'
                            '                    <li>Seite segmentieren (<code>segment</code>)</li>\n'
                            '                    <li>Text erkennen (<code>ocr</code>)</li>\n'
                            '                    <li>Ergebnis strukturieren / exportieren</li>\n'
                            '                </ol>\n'
                            '                In Bottled Kraken sind genau diese Schritte in die Oberfläche '
                            'übertragen:\n'
                            '                zuerst Segmentierungs-Modell, dann Recognition-Modell, danach OCR und '
                            'Export.\n'
                            '            </div>\n'
                            '\n'
                            '            <div class="card">\n'
                            '                <div class="h2">Wichtige Stärken von Kraken</div>\n'
                            '                <ul>\n'
                            '                    <li>trainierbare Layoutanalyse, Lesereihenfolge und '
                            'Zeichenerkennung</li>\n'
                            '                    <li>Unterstützung für Rechts-nach-Links, BiDi und Top-to-Bottom</li>\n'
                            '                    <li>Ausgabe als ALTO, PageXML, abbyyXML und hOCR</li>\n'
                            '                    <li>Wort-Bounding-Boxes und Character-Cuts</li>\n'
                            '                    <li>öffentliche Modellsammlung über HTRMoPo / Zenodo</li>\n'
                            '                </ul>\n'
                            '            </div>\n'
                            '\n'
                            '            <div class="card">\n'
                            '                <div class="h2">Modelle</div><br>\n'
                            '                Kraken arbeitet modellbasiert.\n'
                            '                Gute Ergebnisse hängen stark davon ab, dass das Modell zum Dokumenttyp passt.\n'
                            '                Ein auf historische Drucke trainiertes Modell ist meist deutlich besser für historische Drucke\n'
                            '                als ein allgemeines Modell für modernes Material.\n'
                            '                <br><br>\n'
                            '                <b>Hinweis:</b> Heruntergeladene Kraken-Modelle sollten sich im gleichen Ordner / Verzeichnis\n'
                            '                wie die EXE-Datei befinden, damit Bottled Kraken sie automatisch finden kann.\n'
                            '            </div>\n'
                            '\n'
                            '            <div class="card">\n'
                            '                <div class="h2">Schnittstellen</div><br>\n'
                            '                Kraken bietet zwei Hauptwege:\n'
                            '                <ul>\n'
                            '                    <li><b>CLI:</b> für klassische OCR-Workflows</li>\n'
                            '                    <li><b>Python-API:</b> für eigene Anwendungen und Integrationen</li>\n'
                            '                </ul>\n'
                            '                Bottled Kraken nutzt die Python-Bibliothek direkt im Programmcode.\n'
                            '            </div>\n'
                            '\n'
                            '            <div class="card">\n'
                            '                <div class="h2">Offizielle Quellen</div>\n'
                            '                <ul>\n'
                            '                    <li><a href="https://github.com/mittagessen/kraken">GitHub: '
                            'mittagessen/kraken</a></li>\n'
                            '                    <li><a href="https://kraken.re/7.0/index.html">Kraken Dokumentation '
                            '7.0</a></li>\n'
                            '                    <li><a href="https://kraken.re/7.0/getting_started.html">Getting '
                            'Started</a></li>\n'
                            '                    <li><a href="https://kraken.re/7.0/user_guide/models.html">Model '
                            'Management</a></li>\n'
                            '                </ul>\n'
                            '            </div>\n'
                            '\n'
                            '            <div class="card warn">\n'
                            '                <div class="h2">Hinweis</div>\n'
                            '                <span class="badge">Wichtig</span><br>\n'
                            '                Wenn die Segmentierung nicht sauber ist, wird auch die Recognition '
                            'schlechter.\n'
                            '                Genau deshalb verwendet Bottled Kraken standardmäßig das '
                            '<code>blla.mlmodell</code>\n'
                            '                anstatt des Legacy-Segmentierungs-Modells <code>pageseg</code>.\n'
                            '            </div>\n'
                            '        ',
        'help_html_lm_server': '\n'
                               '            <div class="card">\n'
                               '                <div class="h1">LM-Server / lokale Modellserver</div><br>\n'
                               '                Dieser Bereich ist für die <b>lokale Sprachmodell-Nachbearbeitung</b> '
                               'gedacht.\n'
                               '                Bottled Kraken erwartet dafür eine <b>OpenAI-kompatible Basis-URL</b>, '
                               'typischerweise mit <code>/v1</code>.\n'
                               '            </div>\n'
                               '\n'
                               '            <div class="card">\n'
                               '                <div class="h2">Direkt kompatible Basis-URLs in Bottled Kraken</div>\n'
                               '<pre>LM Studio:              http://localhost:1234/v1\n'
                               'Ollama:                 http://localhost:11434/v1\n'
                               'GPT4All:                http://localhost:4891/v1\n'
                               'text-generation-webui:  http://127.0.0.1:5000/v1\n'
                               'LocalAI:                http://localhost:8080/v1</pre>\n'
                               '                <div class="muted">\n'
                               '                    Wichtig: Bei Ollama trägst du für Bottled Kraken die '
                               '<b>OpenAI-kompatible</b> URL <code>/v1</code> ein, nicht die rohe '
                               '<code>/api</code>-Route.\n'
                               '                </div>\n'
                               '            </div>\n'
                               '\n'
                               '            <div class="card">\n'
                               '                <div class="h2">LM Studio</div>\n'
                               '                <ul>\n'
                               '                    <li>Für viele der bequemste Einstieg, wenn du eine Desktop-App mit '
                               'Modellverwaltung und lokalem Server willst.</li>\n'
                               '                    <li>LM Studio stellt lokale Modelle über REST, OpenAI-kompatible '
                               'und Anthropic-kompatible Endpunkte bereit.</li>\n'
                               '                    <li>Standardfall in Bottled Kraken: '
                               '<code>http://localhost:1234/v1</code></li>\n'
                               '                </ul>\n'
                               '            </div>\n'
                               '\n'
                               '            <div class="card">\n'
                               '                <div class="h2">Ollama</div>\n'
                               '                <ul>\n'
                               '                    <li>Besonders sauber, wenn du vor allem einen lokalen Dienst und '
                               'eine schlanke CLI-/Daemon-Lösung willst.</li>\n'
                               '                    <li>Ollama startet lokal auf <code>http://localhost:11434</code>, '
                               'bietet die eigene <code>/api</code>-Schnittstelle und zusätzlich OpenAI-Kompatibilität '
                               'unter <code>/v1</code>.</li>\n'
                               '                    <li>Für Claude-Code-ähnliche Workflows gibt es außerdem eine '
                               'Anthropic-kompatible Nutzung.</li>\n'
                               '                    <li>In Bottled Kraken deshalb am besten '
                               '<code>http://localhost:11434/v1</code> verwenden.</li>\n'
                               '                </ul>\n'
                               '            </div>\n'
                               '\n'
                               '            <div class="card">\n'
                               '                <div class="h2">Jan</div>\n'
                               '                <ul>\n'
                               '                    <li>Von der Bedienidee oft am nächsten an LM Studio: Desktop-App, '
                               'lokale Modelle, eingebauter OpenAI-kompatibler API-Server.</li>\n'
                               '                    <li>Standardmäßig lauscht Jan auf '
                               '<code>http://127.0.0.1:1337</code> mit API-Prefix <code>/v1</code>; der Default-Host '
                               '<code>127.0.0.1</code> ist bewusst nur lokal erreichbar.</li>\n'
                               '                    <li>Jan verlangt standardmäßig einen API-Key. Für Bottled Kraken '
                               'ist Jan deshalb am praktischsten, wenn die Header-Erwartung angepasst oder ein kleiner '
                               'lokaler Proxy dazwischengeschaltet wird.</li>\n'
                               '                </ul>\n'
                               '            </div>\n'
                               '\n'
                               '            <div class="card">\n'
                               '                <div class="h2">GPT4All</div>\n'
                               '                <ul>\n'
                               '                    <li>Sehr nah an „einfach lokal starten und nutzen“.</li>\n'
                               '                    <li>Der lokale API-Server läuft standardmäßig auf '
                               '<code>http://localhost:4891/v1</code>, ist OpenAI-kompatibel und hört nur auf '
                               '<code>localhost</code>.</li>\n'
                               '                    <li>Zusätzlich bringt GPT4All mit <b>LocalDocs</b> eine einfache '
                               'lokale Dokument-/RAG-Funktion mit.</li>\n'
                               '                    <li>Für Bottled Kraken ist das meist eine der unkompliziertesten '
                               'Alternativen zu LM Studio.</li>\n'
                               '                </ul>\n'
                               '            </div>\n'
                               '\n'
                               '            <div class="card">\n'
                               '                <div class="h2">text-generation-webui (oobabooga)</div>\n'
                               '                <ul>\n'
                               '                    <li>Am interessantesten für Leute, die gern schrauben, Backends '
                               'wechseln und viele Optionen selbst kontrollieren wollen.</li>\n'
                               '                    <li>Das Projekt unterstützt mehrere Backends wie '
                               '<code>llama.cpp</code>, <code>Transformers</code>, <code>ExLlamaV3</code> und '
                               '<code>TensorRT-LLM</code>.</li>\n'
                               '                    <li>Die OpenAI-/Anthropic-kompatible API lässt sich als '
                               'Drop-in-Ersatz verwenden; standardmäßig liegt sie typischerweise auf Port '
                               '<code>5000</code>.</li>\n'
                               '                    <li>Zusätzlich gibt es Tool-Calling, Vision und '
                               'Dateianhänge.</li>\n'
                               '                </ul>\n'
                               '            </div>\n'
                               '\n'
                               '            <div class="card">\n'
                               '                <div class="h2">LocalAI</div>\n'
                               '                <ul>\n'
                               '                    <li>Besonders passend, wenn du eher einen selbst gehosteten '
                               'lokalen AI-Server als eine klassische Desktop-App suchst.</li>\n'
                               '                    <li>LocalAI stellt eine OpenAI-kompatible API bereit; typische '
                               'Nutzung in Bottled Kraken: <code>http://localhost:8080/v1</code>.</li>\n'
                               '                    <li>Darüber hinaus unterstützt LocalAI weitere kompatible '
                               'API-Formate, eine Weboberfläche und Agenten-/MCP-Funktionen.</li>\n'
                               '                    <li>Gut geeignet, wenn du mehrere lokale Dienste oder ein kleines '
                               'internes AI-Setup bündeln willst.</li>\n'
                               '                </ul>\n'
                               '            </div>\n'
                               '\n'
                               '            <div class="card">\n'
                               '                <div class="h2">Praktische Auswahlhilfe</div>\n'
                               '                <ul>\n'
                               '                    <li><b>LM Studio:</b> wenn du GUI + lokales Serving + wenig '
                               'Reibung willst</li>\n'
                               '                    <li><b>Ollama:</b> wenn du einen sauberen lokalen Dienst oder '
                               'CLI-Workflow bevorzugst</li>\n'
                               '                    <li><b>Jan:</b> wenn du LM-Studio-ähnliche Desktop-Bedienung '
                               'willst und mit API-Key/Proxy leben kannst</li>\n'
                               '                    <li><b>GPT4All:</b> wenn du eine einfache Desktop-Lösung plus '
                               'LocalDocs möchtest</li>\n'
                               '                    <li><b>text-generation-webui:</b> wenn du Backends, Vision und '
                               'Tooling fein selbst steuern willst</li>\n'
                               '                    <li><b>LocalAI:</b> wenn du einen stärker selbst gehosteten '
                               'lokalen Server mit breiter API-/Agenten-Ausrichtung suchst</li>\n'
                               '                </ul>\n'
                               '            </div>\n'
                               '\n'
                               '            <div class="card">\n'
                               '                <div class="h2">Offizielle Quellen</div>\n'
                               '                <ul>\n'
                               '                    <li><a href="https://lmstudio.ai/docs/developer/core/server">LM '
                               'Studio Docs – Local LLM API Server</a></li>\n'
                               '                    <li><a href="https://lmstudio.ai/docs/developer/openai-compat">LM '
                               'Studio Docs – OpenAI Compatibility</a></li>\n'
                               '                    <li><a '
                               'href="https://docs.ollama.com/api/openai-compatibility">Ollama Docs – OpenAI '
                               'compatibility</a></li>\n'
                               '                    <li><a '
                               'href="https://docs.ollama.com/integrations/claude-code">Ollama Docs – Claude Code / '
                               'Anthropic-compatible API</a></li>\n'
                               '                    <li><a href="https://www.jan.ai/docs/desktop/api-server">Jan Docs '
                               '– Local API Server</a></li>\n'
                               '                    <li><a '
                               'href="https://docs.gpt4all.io/gpt4all_api_server/home.html">GPT4All Docs – API '
                               'Server</a></li>\n'
                               '                    <li><a '
                               'href="https://github.com/oobabooga/text-generation-webui">text-generation-webui – '
                               'Repository</a></li>\n'
                               '                    <li><a '
                               'href="https://github.com/oobabooga/text-generation-webui/wiki/12-%E2%80%90-OpenAI-API">text-generation-webui '
                               '– OpenAI / Anthropic API Wiki</a></li>\n'
                               '                    <li><a href="https://localai.io/docs/overview/">LocalAI Docs – '
                               'Overview</a></li>\n'
                               '                    <li><a href="https://localai.io/basics/getting_started/">LocalAI '
                               'Docs – Quickstart</a></li>\n'
                               '                </ul>\n'
                               '            </div>\n'
                               '        ',
        'help_html_ssh': '\n'
                         '            <div class="card">\n'
                         '                <div class="h1">Remote-Zugriff per SSH-Tunnel</div><br>\n'
                         '                Ein SSH-Tunnel ist nützlich, wenn dein LM-Server auf einem anderen Rechner '
                         'läuft,\n'
                         '                dort aber nur an <code>127.0.0.1</code> gebunden ist und deshalb nicht '
                         'direkt im Netzwerk erreichbar ist.\n'
                         '            </div>\n'
                         '\n'
                         '            <div class="card">\n'
                         '                <div class="h2">Was passiert dabei?</div><br>\n'
                         '                Der Tunnel leitet einen lokalen Port deines Rechners an einen Port des '
                         'entfernten Rechners weiter.\n'
                         '                Für Bottled Kraken sieht es dann so aus, als würde der LM-Server lokal auf '
                         'deinem eigenen Rechner laufen.\n'
                         '            </div>\n'
                         '\n'
                            '            <div class="card">\n'
                            '                <div class="h2">Beispiel</div><br>\n'
                            '                <b>Auf Rechner A</b><br>\n'
                            '                LM Studio starten<br>\n'
                            '                IP von Rechner A herausfinden, z. B. mit:\n'
                            '                <pre>ipconfig\n'
                            'hostname -I</pre>\n'
                            '                Angenommen, die IP ist:\n'
                            '                <pre>192.168.1.50</pre>\n'
                            '                <b>Auf Rechner B</b><br>\n'
                            '                SSH-Tunnel öffnen:\n'
                            '                <pre>ssh -N -L 1234:127.0.0.1:1234 user@192.168.1.50</pre>\n'
                            '                <b>Auf Rechner B benutzen</b><br>\n'
                            '                Test im Terminal:\n'
                            '                <pre>curl http://127.0.0.1:1234/v1/models</pre>\n'
                            '                In Bottled Kraken eintragen:\n'
                            '                <pre>http://127.0.0.1:1234/v1</pre>\n'
                            '            </div>\n'
                         '\n'
                            '            <div class="card">\n'
                            '                <div class="h2">Typischer Ablauf</div>\n'
                            '                <ol>\n'
                            '                    <li>Auf Rechner A LM Studio starten</li>\n'
                            '                    <li>Auf Rechner A die IP-Adresse herausfinden</li>\n'
                            '                    <li>Auf Rechner B den SSH-Tunnel mit dieser IP öffnen</li>\n'
                            '                    <li>Auf Rechner B testen, ob <code>http://127.0.0.1:1234/v1/models</code> erreichbar ist</li>\n'
                            '                    <li>In Bottled Kraken <code>http://127.0.0.1:1234/v1</code> eintragen</li>\n'
                            '                </ol>\n'
                            '            </div>\n'
                         '\n'
                         '            <div class="card warn">\n'
                         '                <div class="h2">Wichtig</div>\n'
                         '                <ul>\n'
                         '                    <li>In Bottled Kraken trägst du <b>nicht</b> den SSH-Befehl ein.</li>\n'
                         '                    <li>Du trägst immer die resultierende HTTP-URL ein, also zum Beispiel '
                         '<code>http://127.0.0.1:1234/v1</code>.</li>\n'
                         '                    <li>Der SSH-Tunnel muss geöffnet bleiben, solange Bottled Kraken den '
                         'Server nutzen soll.</li>\n'
                         '                </ul>\n'
                         '            </div>\n'
                         '        ',
        'help_html_whisper_intro': '\n'
                                   '            <div class="card">\n'
                                   '                <div class="h1">Faster-Whisper</div>\n'
                                   '                <p>\n'
                                   '                    Faster-Whisper ist eine schnelle lokale '
                                   'Sprach-zu-Text-Erkennung.\n'
                                   '                    In Bottled Kraken kannst du damit einzelne OCR-Zeilen per '
                                   'Mikrofon\n'
                                   '                    neu einsprechen und direkt als Text übernehmen.\n'
                                   '                </p>\n'
                                   '            </div>\n'
                                   '\n'
                                   '            <div class="card">\n'
                                   '                <div class="h2">Wofür ist das nützlich?</div>\n'
                                   '                <ul>\n'
                                   '                    <li>wenn eine OCR-Zeile stark beschädigt oder falsch erkannt '
                                   'wurde</li>\n'
                                   '                    <li>wenn du einzelne Felder oder Namen schneller einsprechen '
                                   'als tippen möchtest</li>\n'
                                   '                    <li>wenn du Korrekturen gezielt zeilenweise durchführen '
                                   'willst</li>\n'
                                   '                </ul>\n'
                                   '            </div>\n'
                                   '\n'
                                   '            <div class="card">\n'
                                   '                <div class="h2">Was wird heruntergeladen?</div>\n'
                                   '                <p>\n'
                                   '                    Es wird das Modell <span '
                                   'class="badge">Systran/faster-whisper-large-v3</span> geladen.\n'
                                   '                </p>\n'
                                   '                <p class="muted">\n'
                                   '                    Vor dem Download installiert Bottled Kraken die benötigten '
                                   'Python-Pakete automatisch.\n'
                                   '                    Der eigentliche Modell-Download läuft über die '
                                   'Hugging-Face-CLI <code>hf download</code>.\n'
                                   '                    Unter Linux und macOS wird dafür automatisch eine eigene '
                                   'venv-Umgebung genutzt.\n'
                                   '                </p>\n'
                                   '            </div>\n'
                                   '\n'
                                   '            <div class="card">\n'
                                   '                <div class="h2">Ablauf in Bottled Kraken</div>\n'
                                   '                <ol>\n'
                                   '                    <li>Whisper-Modell herunterladen oder vorhandenes Modell '
                                   'scannen</li>\n'
                                   '                    <li>Mikrofon auswählen</li>\n'
                                   '                    <li>Eine Zeile markieren</li>\n'
                                   '                    <li>Audioaufnahme starten</li>\n'
                                   '                    <li>Die gesprochene Eingabe wird lokal transkribiert und '
                                   'ersetzt die Zeile</li>\n'
                                   '                </ol>\n'
                                   '            </div>\n'
                                   '        ',
        'help_html_shortcuts': '\n'
                               '            <div class="card">\n'
                               '                <div class="h1">Tastenkürzel</div>\n'
                               '                <table class="table">\n'
                               '                    <tr><td class="section" colspan="2">Projekt</td></tr>\n'
                               '                    <tr><td><span class="kbd">Strg + S</span></td><td>Projekt '
                               'speichern</td></tr>\n'
                               '                    <tr><td><span class="kbd">Strg + Shift + S</span></td><td>Projekt '
                               'speichern unter</td></tr>\n'
                               '                    <tr><td><span class="kbd">Strg + I</span></td><td>Projekt '
                               'laden</td></tr>\n'
                               '                    <tr><td><span class="kbd">Strg + '
                               'E</span></td><td>Export</td></tr>\n'
                               '                    <tr><td><span class="kbd">Strg + Q</span></td><td>Programm '
                               'beenden</td></tr>\n'
                               '\n'
                               '                    <tr><td class="section" colspan="2">OCR &amp; LM</td></tr>\n'
                               '                    <tr><td><span class="kbd">Strg + K</span></td><td>Kraken-OCR '
                               'starten</td></tr>\n'
                               '                    <tr><td><span class="kbd">Strg + P</span></td><td>Kraken-OCR '
                               'stoppen</td></tr>\n'
                               '                    <tr><td><span class="kbd">Strg + L</span></td><td>LM-Überarbeitung '
                               'starten</td></tr>\n'
                               '                    <tr><td><span class="kbd">Strg + M</span></td><td>Faster-Whisper / '
                               'Mikrofon starten</td></tr>\n'
                               '\n'
                               '                    <tr><td class="section" colspan="2">Auswahl</td></tr>\n'
                               '                    <tr><td><span class="kbd">Strg + A</span></td><td>Alles im '
                               'aktuellen Kontext auswählen</td></tr>\n'
                               '                    <tr><td><span class="kbd">Entf</span></td><td>Ausgewählte Zeilen '
                               'oder Boxen löschen</td></tr>\n'
                               '\n'
                               '                    <tr><td class="section" colspan="2">F-Tasten</td></tr>\n'
                               '                    <tr><td><span '
                               'class="kbd">F1</span></td><td>Shortcut-Hilfe</td></tr>\n'
                               '                    <tr><td><span class="kbd">F2</span></td><td>Recognition-Modell '
                               'laden</td></tr>\n'
                               '                    <tr><td><span class="kbd">F3</span></td><td>Segmentierungs-Modell '
                               'laden</td></tr>\n'
                               '                    <tr><td><span class="kbd">F4</span></td><td>LM-Server-URL '
                               'eingeben</td></tr>\n'
                               '                    <tr><td><span class="kbd">F5</span></td><td>LM-Scan '
                               'starten</td></tr>\n'
                               '                    <tr><td><span class="kbd">F6</span></td><td>Whisper-Modelle '
                               'scannen + erstes Mikrofon setzen</td></tr>\n'
                               '                    <tr><td><span class="kbd">F7</span></td><td>Log-Fenster '
                               'ein/aus</td></tr>\n'
                               '                </table>\n'
                               '            </div>\n'
                               '        ',
        'help_html_data_protection': '\n'
                                     '            <div class="card warn">\n'
                                     '                <div class="h1">Datenschutz</div><br>\n'
                                     '                Die folgenden Hinweise fassen den <b>lokalen Standardbetrieb</b> '
                                     'zusammen.\n'
                                     '                Sie ersetzen keine Datenschutzprüfung im Einzelfall.\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">Grundregel</div>\n'
                                     '                <ul>\n'
                                     '                    <li>Lokale Modelle und lokale Server sind grundsätzlich '
                                     'datenschutzfreundlicher, weil Eingaben, Dokumente und Audio nicht automatisch an '
                                     'einen Cloud-Dienst gesendet werden.</li>\n'
                                     '                    <li>Das gilt aber nur, solange du die jeweilige Software '
                                     'wirklich <b>lokal</b> und ohne Cloud- oder Netzwerkrouting nutzt.</li>\n'
                                     '                    <li>Sobald Netzwerkfreigaben, Tunnel, Reverse-Proxys, '
                                     'Remote-Instanzen oder Cloud-Modelle ins Spiel kommen, ändert sich die '
                                     'Datenschutzlage.</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">LM Studio</div>\n'
                                     '                <ul>\n'
                                     '                    <li>Laut offizieller Dokumentation kann LM Studio '
                                     'vollständig offline arbeiten; lokaler Chat, Dokument-Chat und lokaler Server '
                                     'benötigen dafür kein Internet.</li>\n'
                                     '                    <li>Die Privacy Policy sagt außerdem ausdrücklich, dass '
                                     'Nachrichten, Chatverläufe und Dokumente standardmäßig nicht vom System '
                                     'übertragen werden.</li>\n'
                                     '                    <li>Das gilt für die lokale Nutzung. Bei Netzwerkfreigaben '
                                     'oder Remote-Funktionen ist gesondert zu prüfen, wohin Daten fließen.</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">Ollama</div>\n'
                                     '                <ul>\n'
                                     '                    <li>Ollama läuft standardmäßig lokal auf '
                                     '<code>http://localhost:11434</code>; für lokale API-Nutzung ist keine '
                                     'Authentifizierung nötig.</li>\n'
                                     '                    <li>Damit bleibt ein reiner localhost-Betrieb zunächst auf '
                                     'deinem Rechner.</li>\n'
                                     '                    <li>Wichtig: Ollama unterstützt inzwischen auch '
                                     '<b>Cloud-Modelle</b>. Sobald du solche Modelle nutzt, ist der Ablauf nicht mehr '
                                     'rein lokal.</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">Jan</div>\n'
                                     '                <ul>\n'
                                     '                    <li>Jan beschreibt sich als privacy-first und speichert '
                                     'Daten lokal im eigenen Datenordner.</li>\n'
                                     '                    <li>Die lokale API ist standardmäßig auf '
                                     '<code>127.0.0.1</code> beschränkt; das ist für Einzelplatzbetrieb die sicherere '
                                     'Voreinstellung.</li>\n'
                                     '                    <li>Gleichzeitig bietet Jan Analyse-/Tracking-Einstellungen '
                                     'und ausführliche Server-Logs. Vor produktiver Nutzung sollte man deshalb bewusst '
                                     'prüfen, was lokal protokolliert wird und ob Netzwerkzugriff aktiviert '
                                     'wurde.</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">GPT4All</div>\n'
                                     '                <ul>\n'
                                     '                    <li>GPT4All wirbt mit lokaler Ausführung auf eigener '
                                     'Hardware.</li>\n'
                                     '                    <li>Der API-Server hört standardmäßig nur auf '
                                     '<code>localhost</code> und nicht auf fremden Geräten im Netzwerk.</li>\n'
                                     '                    <li>Mit <b>LocalDocs</b> können lokale Dokumente in den '
                                     'Workflow einbezogen werden; auch dabei sollte man Speicherort und Zugriffsschutz '
                                     'des Geräts mitdenken.</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">text-generation-webui &amp; LocalAI</div>\n'
                                     '                <ul>\n'
                                     '                    <li><b>text-generation-webui</b> bezeichnet seine '
                                     'OpenAI-/Anthropic-kompatible API als 100&nbsp;% offline und privat; zusätzlich '
                                     'verweist das Projekt darauf, keine Logs zu erzeugen.</li>\n'
                                     '                    <li><b>LocalAI</b> positioniert sich als lokale, '
                                     'OpenAI-kompatible Komplettlösung und wirbt damit, Daten privat und sicher zu '
                                     'halten.</li>\n'
                                     '                    <li>Bei beiden Projekten gilt trotzdem: Sobald du die API '
                                     'absichtlich im Netzwerk freigibst, einen Reverse-Proxy davorsetzt oder mehrere '
                                     'Nutzer zulässt, musst du Zugriffe, Logs, Backups und Admin-Rechte selbst sauber '
                                     'absichern.</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">faster-whisper</div><br>\n'
                                     '                faster-whisper ist eine lokale Whisper-Implementierung auf Basis '
                                     'von CTranslate2.\n'
                                     '                In Bottled Kraken wird dafür ein lokaler Modellordner geladen '
                                     'und eine lokale WAV-Datei transkribiert.\n'
                                     '                Solange dieser Ablauf lokal bleibt, erfolgt die '
                                     'Audioverarbeitung ebenfalls lokal.\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card warn">\n'
                                     '                <div class="h2">Wichtige Einschränkungen</div>\n'
                                     '                <ul>\n'
                                     '                    <li>Der einmalige Modell-Download benötigt natürlich '
                                     'Internetzugriff.</li>\n'
                                     '                    <li>Auch ein „lokaler“ Server kann personenbezogene Daten '
                                     'preisgeben, wenn das Gerät selbst unzureichend abgesichert ist.</li>\n'
                                     '                    <li>Für Behörden, Archive, Unternehmen oder '
                                     'Forschungseinrichtungen reichen reine Tool-Eigenschaften allein nicht aus; '
                                     'relevant sind zusätzlich Speicherort, Rollenrechte, Logs, Backups, Löschkonzepte '
                                     'und interne Richtlinien.</li>\n'
                                     '                    <li>Die Lizenz oder Privacy Policy einer Software ersetzt '
                                     'keine DSGVO-/Vertrags-/Betriebsprüfung im Einzelfall.</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">Offizielle Quellen</div>\n'
                                     '                <ul>\n'
                                     '                    <li><a href="https://lmstudio.ai/docs/app/offline">LM Studio '
                                     'Docs – Offline Operation</a></li>\n'
                                     '                    <li><a href="https://lmstudio.ai/privacy">LM Studio Desktop '
                                     'App Privacy Policy</a></li>\n'
                                     '                    <li><a '
                                     'href="https://docs.ollama.com/api/authentication">Ollama Docs – '
                                     'Authentication</a></li>\n'
                                     '                    <li><a href="https://docs.ollama.com/cloud">Ollama Docs – '
                                     'Cloud</a></li>\n'
                                     '                    <li><a href="https://ollama.com/privacy">Ollama – Privacy '
                                     'Policy</a></li>\n'
                                     '                    <li><a href="https://www.jan.ai/docs/desktop/privacy">Jan '
                                     'Docs – Privacy</a></li>\n'
                                     '                    <li><a '
                                     'href="https://www.jan.ai/docs/desktop/data-folder">Jan Docs – Data '
                                     'Folder</a></li>\n'
                                     '                    <li><a href="https://www.jan.ai/docs/desktop/api-server">Jan '
                                     'Docs – Local API Server</a></li>\n'
                                     '                    <li><a '
                                     'href="https://docs.gpt4all.io/gpt4all_api_server/home.html">GPT4All Docs – API '
                                     'Server</a></li>\n'
                                     '                    <li><a href="https://github.com/nomic-ai/gpt4all">GPT4All – '
                                     'Repository</a></li>\n'
                                     '                    <li><a '
                                     'href="https://github.com/oobabooga/text-generation-webui/wiki/12-%E2%80%90-OpenAI-API">text-generation-webui '
                                     '– OpenAI / Anthropic API Wiki</a></li>\n'
                                     '                    <li><a href="https://localai.io/docs/overview/">LocalAI Docs '
                                     '– Overview</a></li>\n'
                                     '                    <li><a '
                                     'href="https://github.com/SYSTRAN/faster-whisper">SYSTRAN / '
                                     'faster-whisper</a></li>\n'
                                     '                    <li><a '
                                     'href="https://github.com/opennmt/ctranslate2">CTranslate2</a></li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '        ',
        'help_html_legal': '\n'
                           '            <div class="card warn">\n'
                           '                <div class="h1">Rechtliches</div><br>\n'
                           '                Die folgenden Hinweise sind eine allgemeine Orientierung und ersetzen '
                           'keine Rechtsberatung.\n'
                           '                Für konkrete Nutzungsszenarien sollte die rechtliche Einordnung im '
                           'Einzelfall geprüft werden.\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card ok">\n'
                           '                <div class="h2">Bottled Kraken</div>\n'
                           '                <ul>\n'
                           '                    <li><b>Repository-Lizenz:</b> GPL-3.0.</li>\n'
                           '                    <li><b>Kurz gesagt:</b> Bei Weitergabe, Veröffentlichung veränderter '
                           'Versionen oder Distribution eines darauf aufbauenden Pakets müssen die Bedingungen der '
                           'GPL-3.0 beachtet werden.</li>\n'
                           '                    <li><b>Wichtig:</b> Davon zu unterscheiden sind die Lizenzen der '
                           'eingebundenen Bibliotheken und Modelle.</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">Kraken</div>\n'
                           '                <ul>\n'
                           '                    <li>Kraken ist die OCR-Basis von Bottled Kraken.</li>\n'
                           '                    <li>Das Projekt steht unter der <b>Apache License 2.0</b>.</li>\n'
                           '                    <li>Für Redistribution sind insbesondere Lizenztext, '
                           'Copyright-Hinweise und eventuelle NOTICE-Hinweise relevant.</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">faster-whisper</div>\n'
                           '                <ul>\n'
                           '                    <li>faster-whisper wird in Bottled Kraken für lokale '
                           'Sprach-zu-Text-Funktionen verwendet.</li>\n'
                           '                    <li>Das Projekt steht unter der <b>MIT-Lizenz</b>.</li>\n'
                           '                    <li>Zusätzlich können für Modelle oder weitere Abhängigkeiten '
                           'gesonderte Bedingungen gelten.</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">LM Studio</div>\n'
                           '                <ul>\n'
                           '                    <li>LM Studio wird optional als lokaler oder angebundener '
                           'Sprachmodell-Server genutzt.</li>\n'
                           '                    <li>Maßgeblich sind hier vor allem die offiziellen <b>Terms of '
                           'Service</b> und die <b>Privacy Policy</b>.</li>\n'
                           '                    <li>Für die über LM Studio geladenen Modelle gelten zusätzlich jeweils '
                           'eigene Modelllizenzen.</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">Ollama</div>\n'
                           '                <ul>\n'
                           '                    <li>Die Software im offiziellen Repository steht unter der '
                           '<b>MIT-Lizenz</b>.</li>\n'
                           '                    <li>Für lokale Nutzung ist das meist unkompliziert; bei Weitergabe '
                           'veränderter Software bleiben Lizenz- und Copyright-Hinweise relevant.</li>\n'
                           '                    <li>Davon getrennt zu betrachten sind <b>Cloud-Funktionen</b>, '
                           'Datenschutzregeln und vor allem die Lizenz der jeweils verwendeten Modelle.</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">Jan</div>\n'
                           '                <ul>\n'
                           '                    <li>Das Jan-Repository ist als Open-Source-Projekt ausgewiesen; die '
                           'Repository-Lizenz ist <b>AGPL-3.0</b>.</li>\n'
                           '                    <li>Die AGPL ist besonders relevant, wenn veränderte Versionen über '
                           'ein Netzwerk bereitgestellt werden.</li>\n'
                           '                    <li>Auch hier gelten für eingebundene Modelle und externe '
                           'Cloud-Provider zusätzliche Bedingungen.</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">GPT4All</div>\n'
                           '                <ul>\n'
                           '                    <li>Das offizielle GPT4All-Repository steht unter der '
                           '<b>MIT-Lizenz</b>.</li>\n'
                           '                    <li>Die Softwarelizenz ist permissiv; getrennt davon bleiben '
                           'Modelllizenzen, Markennutzung und etwaige Drittkomponenten zu prüfen.</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">text-generation-webui (oobabooga)</div>\n'
                           '                <ul>\n'
                           '                    <li>Das Projekt steht unter der <b>AGPL-3.0</b>.</li>\n'
                           '                    <li>Das ist rechtlich strenger als MIT oder Apache und vor allem bei '
                           'Änderungen sowie Netzwerkbereitstellung wichtig.</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">LocalAI</div>\n'
                           '                <ul>\n'
                           '                    <li>LocalAI steht laut offiziellem Repository unter der '
                           '<b>MIT-Lizenz</b>.</li>\n'
                           '                    <li>Wie bei den anderen Servern gilt: Modelllizenzen, '
                           'Zusatzkomponenten und organisatorische Nutzungsvorgaben sind davon getrennt zu '
                           'prüfen.</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">PySide6 / Qt for Python</div>\n'
                           '                <ul>\n'
                           '                    <li>Die grafische Oberfläche von Bottled Kraken basiert auf PySide6 / '
                           'Qt for Python.</li>\n'
                           '                    <li>Qt for Python verwendet Lizenzmodelle, die je nach Komponente '
                           '<b>LGPL</b> bzw. kommerzielle Qt-Lizenz einschließen können.</li>\n'
                           '                    <li>Für Redistribution, Packaging und proprietäre Gesamtprodukte '
                           'sollte die Qt-Lizenzsituation gesondert geprüft werden.</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card warn">\n'
                           '                <div class="h2">Zusätzlicher Hinweis zu Modellen und Inhalten</div>\n'
                           '                <ul>\n'
                           '                    <li>Die Software-Lizenz der Anwendung ist immer von der Lizenz der '
                           'geladenen OCR-, Sprach- oder KI-Modelle zu unterscheiden.</li>\n'
                           '                    <li>Auch die Verarbeitung urheberrechtlich geschützter Dokumente, '
                           'personenbezogener Daten oder sensibler Archivbestände ist gesondert rechtlich zu '
                           'bewerten.</li>\n'
                           '                    <li>Dieses Fenster gibt nur einen kompakten Überblick und keine '
                           'verbindliche Einzelfallprüfung.</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">Offizielle Quellen</div>\n'
                           '                <ul>\n'
                           '                    <li><a href="https://github.com/Testatost/Bottled-Kraken">Bottled '
                           'Kraken – Repository</a></li>\n'
                           '                    <li><a href="https://github.com/mittagessen/kraken">Kraken – '
                           'Repository</a></li>\n'
                           '                    <li><a href="https://kraken.re/7.0/index.html">Kraken – '
                           'Dokumentation</a></li>\n'
                           '                    <li><a href="https://github.com/SYSTRAN/faster-whisper">faster-whisper '
                           '– Repository</a></li>\n'
                           '                    <li><a href="https://lmstudio.ai/app-terms">LM Studio – Terms of '
                           'Service</a></li>\n'
                           '                    <li><a href="https://lmstudio.ai/privacy">LM Studio – Privacy '
                           'Policy</a></li>\n'
                           '                    <li><a href="https://github.com/ollama/ollama">Ollama – '
                           'Repository</a></li>\n'
                           '                    <li><a '
                           'href="https://github.com/ollama/ollama/blob/main/LICENSE">Ollama – MIT License</a></li>\n'
                           '                    <li><a href="https://github.com/janhq/jan">Jan – Repository</a></li>\n'
                           '                    <li><a '
                           'href="https://docs.gpt4all.io/gpt4all_api_server/home.html">GPT4All – API Server '
                           'Docs</a></li>\n'
                           '                    <li><a '
                           'href="https://github.com/nomic-ai/gpt4all/blob/main/LICENSE.txt">GPT4All – MIT '
                           'License</a></li>\n'
                           '                    <li><a '
                           'href="https://github.com/oobabooga/text-generation-webui">text-generation-webui – '
                           'Repository</a></li>\n'
                           '                    <li><a '
                           'href="https://github.com/oobabooga/text-generation-webui/blob/main/LICENSE">text-generation-webui '
                           '– AGPL-3.0</a></li>\n'
                           '                    <li><a href="https://localai.io/docs/overview/">LocalAI – '
                           'Overview</a></li>\n'
                           '                    <li><a '
                           'href="https://github.com/mudler/LocalAI/blob/master/LICENSE">LocalAI – MIT '
                           'License</a></li>\n'
                           '                    <li><a href="https://doc.qt.io/qtforpython-6/">Qt for Python – '
                           'Documentation</a></li>\n'
                           '                    <li><a href="https://doc.qt.io/qtforpython-6/licenses.html">Qt for '
                           'Python – Licenses</a></li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '        ',
        'ai_prompt_page_system': 'Du bist ein hochpräziser OCR- und Transkriptionsassistent für historische deutsche '
                                 'Drucke, Handschriften und Formulare.\n'
                                 'Du liest den Text direkt aus dem Bild.\n'
                                 'Das Bild ist die einzige Wahrheitsquelle.\n'
                                 'Du musst den gelesenen Text auf eine bereits vorgegebene Liste von Zielzeilen '
                                 'abbilden.\n'
                                 'Jede Zielzeile entspricht genau einer visuellen Formular- oder Textzeile.\n'
                                 'Du darfst keine zwei Zielzeilen zusammenziehen.\n'
                                 'Du darfst keine zusätzliche Leerzeile halluzinieren.\n'
                                 'Du darfst keinen langen Textblock in eine einzelne Zielzeile schreiben.\n'
                                 'Wenn eine Zielzeile keinen sicher lesbaren Text enthält, gib für genau diese Zeile '
                                 'einen leeren String zurück.\n'
                                 'Du musst die Anzahl der Zielzeilen exakt einhalten.\n'
                                 'Antworte ausschließlich mit gültigem JSON.\n'
                                 'Kein Markdown. Kein Zusatztext. Kein Kommentar.',
        'ai_prompt_page_user': 'Lies den Text direkt aus dem Bild.\n'
                               '\n'
                               'Du musst die vorgegebene Kraken-Zeilenstruktur EXAKT einhalten.\n'
                               'Es gibt genau {} Zielzeilen.\n'
                               'Jeder idx steht für genau eine visuelle Zielzeile.\n'
                               '\n'
                               'HARTE REGELN:\n'
                               '- Gib genau {} Einträge im Feld lines zurück\n'
                               '- Die idx-Werte müssen exakt 0 bis {} sein\n'
                               '- Kein idx darf fehlen\n'
                               '- Kein idx darf doppelt vorkommen\n'
                               '- Keine zwei Zielzeilen dürfen zu einer Zeile zusammengezogen werden\n'
                               '- Kein langer Satzblock darf in einer einzelnen Zielzeile landen\n'
                               '- Wenn eine Zielzeile unklar ist, gib den bestmöglichen kurzen Zeilentext zurück\n'
                               '- Wenn die Zielzeile wirklich leer ist, gib text als leeren String zurück\n'
                               '- Die bbox ist nur Orientierung für die visuelle Zuordnung\n'
                               '- Gib NUR das JSON-Objekt zurück\n'
                               '- Kein Markdown\n'
                               '- Keine Analyse\n'
                               '- Keine Kommentare\n'
                               '- Keine zusätzlichen Sätze\n'
                               '\n'
                               'Kraken-Zielzeilenstruktur:\n'
                               '{}\n'
                               '\n'
                               'Antwortformat exakt so:\n'
                               '{{"lines":[{{"idx":0,"text":"..."}},{{"idx":1,"text":"..."}}]}}',
        'ai_prompt_single_system': 'Du bist ein präziser OCR- und Transkriptionsassistent für historische deutsche '
                                   'Handschriften und Formulare.\n'
                                   'Du liest genau eine einzelne Zielzeile aus einem Bildausschnitt.\n'
                                   'Das Bild ist die einzige Wahrheitsquelle.\n'
                                   'Die Zielzeile befindet sich in der Mitte des Ausschnitts.\n'
                                   'Oberhalb oder unterhalb sichtbare Linien, Leerzeilen, Formularlinien, Labels oder '
                                   'Nachbarzeilen sind nur Kontext.\n'
                                   'Du darfst nur den Text der einen Zielzeile zurückgeben.\n'
                                   'Du darfst keinen Text aus Nachbarzeilen übernehmen.\n'
                                   'Du darfst keine zusätzliche Zeile erfinden.\n'
                                   'Du darfst keine lange Passage bilden, wenn im Ausschnitt nur eine kurze '
                                   'Formularzeile steht.\n'
                                   'Wenn die Zielzeile leer ist, gib einen leeren String zurück.\n'
                                   'Antworte ausschließlich mit gültigem JSON.\n'
                                   'Kein Markdown. Kein Zusatztext. Kein Kommentar.',
        'ai_prompt_single_user': 'Lies genau die Zielzeile in der Mitte des Bildausschnitts.\n'
                                 'WICHTIG:\n'
                                 '- Gib nur den Text dieser EINEN Zeile zurück\n'
                                 '- Benachbarte Zeilen dürfen nicht übernommen werden\n'
                                 '- Formular-Labels, Linien und Leerbereiche dürfen nicht halluziniert ergänzt werden\n'
                                 '- Wenn in dieser Zielzeile kein lesbarer Text steht, gib text als leeren String '
                                 'zurück\n'
                                 '- Keine zweite Zeile\n'
                                 '- Keine Zusammenfassung\n'
                                 '- Keine Erklärung\n'
                                 '- Kein Markdown\n'
                                 '- Keine Ausgabe vor oder nach dem JSON\n'
                                 '\n'
                                 'Format exakt:\n'
                                 '{{"text":"..."}}\n'
                                 '\n'
                                 'Zeilenindex: {}',
        'ai_prompt_decision_system': 'Du bist ein präziser OCR-Korrekturassistent für historische deutsche '
                                     'Handschriften und Formulare.\n'
                                     'Du bekommst für genau eine Zielzeile drei Kandidaten:\n'
                                     '1. Kraken-OCR\n'
                                     '2. OCR aus dem Gesamtseiten-Kontext\n'
                                     '3. OCR aus der Overlay-Box dieser Zeile\n'
                                     '\n'
                                     'WICHTIG:\n'
                                     '- Die Overlay-Box-OCR ist die Primärquelle.\n'
                                     '- Die Seiten-OCR ist NUR Kontext und darf keine fremden Nachbarzeilen in diese '
                                     'Zielzeile hineinziehen.\n'
                                     '- Kraken ist nur schwacher Fallback.\n'
                                     '- Du darfst keine zusätzliche Zeile erfinden.\n'
                                     '- Du darfst keinen Text aus benachbarten Formularzeilen übernehmen.\n'
                                     '- Du darfst keine lange Mehrzeilen-Passage in diese eine Zielzeile packen.\n'
                                     '- Wenn die Box-OCR plausibel ist, übernimm sie.\n'
                                     '- Nur wenn die Box-OCR klar abgeschnitten, leer oder offensichtlich falsch ist, '
                                     'darfst du mit Kraken korrigieren.\n'
                                     '- Die Seiten-OCR darf nur helfen, ein einzelnes unsicheres Wort zu bestätigen, '
                                     'nicht die ganze Zeile zu ersetzen.\n'
                                     '- Bewahre historische Schreibweise.\n'
                                     'Antworte ausschließlich mit gültigem JSON.\n'
                                     'Kein Markdown. Kein Zusatztext. Kein Kommentar.',
        'ai_prompt_decision_user': 'Zielzeile idx={}\n'
                                   '\n'
                                   'Kraken-OCR:\n'
                                   '{}\n'
                                   '\n'
                                   'Seitenkontext-OCR (nur Kontext, nicht Primärquelle):\n'
                                   '{}\n'
                                   '\n'
                                   'Overlay-Box-OCR (Primärquelle):\n'
                                   '{}\n'
                                   '\n'
                                   'Wähle die beste finale Fassung für GENAU diese eine Zeile.\n'
                                   'Bevorzuge die Overlay-Box-OCR.\n'
                                   'Gib nur die finale Textzeile zurück.\n'
                                   'Format exakt:\n'
                                   '{{"text":"..."}}',
        'ai_prompt_block_system': 'Du bist ein präziser OCR- und Transkriptionsassistent für historische deutsche '
                                  'Handschriften.\n'
                                  'Lies den Text frei direkt aus dem Bild.\n'
                                  'Das Bild ist die einzige Wahrheitsquelle.\n'
                                  'Du darfst nicht den OCR-Hinweis rekonstruieren, sondern musst das Bild selbst '
                                  'lesen.\n'
                                  'Die von außen vorgegebene Zeilenanzahl ist nur ein Strukturrahmen.\n'
                                  'Du musst den frei gelesenen Text passend in genau diese Anzahl von Zeilen '
                                  'eintragen.\n'
                                  'Antworte ausschließlich mit gültigem JSON.\n'
                                  'Kein Markdown. Kein Zusatztext. Kein Kommentar.',
        'ai_prompt_block_user': 'Lies die handschriftlichen Zeilen im Bildausschnitt.\n'
                                'Gib ausschließlich genau EIN JSON-Objekt zurück.\n'
                                'Kein Markdown. Kein ```json. Kein Kommentar. Kein Zusatztext.\n'
                                'Es müssen genau {} Einträge im Feld lines stehen.\n'
                                'Wichtig:\n'
                                '- doppelte Anführungszeichen innerhalb von text immer als " escapen\n'
                                '- keine weiteren Felder außer idx und text\n'
                                '- keine Ausgabe vor oder nach dem JSON\n'
                                'Format:\n'
                                '{{"lines":[{{"idx":0,"text":"..."}}]}}\n'
                                '\n'
                                'Die idx-Werte müssen lokal bei 0 beginnen.\n'
                                'Aktueller OCR-Hinweis:\n'
                                '{}',
        'line_menu_ai_revise_single': 'Nur diese Zeile mit LM überarbeiten',
        'btn_ok': 'OK',
        'act_image_edit': 'Bildbearbeitung',
        'canvas_menu_split_box': 'Box aufteilen',
        'queue_ctx_check_all': 'Alle markieren',
        'queue_ctx_uncheck_all': 'Alle Markierungen entfernen',
        'queue_check_header_tooltip': 'Klick: alle Dateien markieren oder Markierung entfernen',
        'line_menu_ai_revise_selected': 'Ausgewählte Zeilen mit LM überarbeiten',
        'menu_lm_options': 'LM-Optionen',
        'menu_whisper_options': 'Whisper-Optionen',
        'act_whisper_set_path': 'Whisper-Modellpfad festlegen...',
        'act_whisper_set_mic': 'Mikrofon auswählen...',
        'act_scan_local': 'Lokal scannen',
        'no_models_scan': '(Keine Modelle – Verzeichnis überprüfen)',
        'act_unload_model': 'Modell entladen',
        'msg_whisper_model_unloaded': 'Whisper-Modell entladen.',
        'msg_whisper_models_found': '{} Whisper-Modell(e) gefunden.',
        'msg_whisper_models_not_found': 'Keine Whisper-Modelle gefunden.',
        'warn_no_audio_devices': 'Es wurden keine Audioaufnahmegeräte gefunden.',
        'dlg_choose_microphone': 'Mikrofon auswählen',
        'dlg_audio_input_device': 'Audioeingabegerät:',
        'msg_microphone_set': 'Mikrofon gesetzt: {}',
        'export_choose_format_label': 'Exportformat wählen:',
        'msg_pdf_render_already_running': 'Es wird gerade bereits ein PDF gerendert. Bitte warte kurz.',
        'pdf_page_display': '{} – Seite {:04d}',
        'act_set_manual_lm_url': 'LM-Server-URL eintragen...',
        'act_clear_manual_lm_url': 'LM-Server-URL löschen',
        'msg_lm_found_url': 'LM gefunden: {} | URL: {}',
        'msg_lm_no_models_url': 'Keine Modelle gefunden | URL: {}',
        'msg_lm_found': 'LM gefunden: {}',
        'msg_lm_server_not_found': 'Kein erreichbarer lokaler LM-Server gefunden.',
        'act_clear_ai_model': 'LM-Modell entfernen',
        'msg_ai_model_choice_cleared': 'LM-Modellwahl gelöscht.',
        'msg_ai_model_removed': 'LM-Modell entfernt.',
        'header_rec_models': 'Recognition-Modelle:',
        'header_seg_models': 'Segmentierungs-Modelle:',
        'status_rec_model': 'Recognition-Modell: {}',
        'status_seg_model': 'Segmentierungs-Modell: {}',
        'msg_ai_model_id_cleared_auto': 'KI-Modell-ID geleert, localhost-Autoerkennung aktiv.',
        'msg_ai_single_done': 'LM-Überarbeitung für Zeile {} abgeschlossen.',
        'log_ai_single_done': 'LM-Zeilenüberarbeitung abgeschlossen: {} | Zeile {}',
        'msg_ai_single_cancelled': 'Zeilenüberarbeitung abgebrochen.',
        'log_ai_single_cancelled': 'LM-Zeilenüberarbeitung abgebrochen: {}',
        'msg_ai_single_failed': 'Zeilenüberarbeitung fehlgeschlagen.',
        'log_ai_single_failed': 'LM-Zeilenüberarbeitung Fehler: {} -> {}',
        'msg_ai_cancelled_short': 'Überarbeitung abgebrochen.',
        'msg_ai_failed_short': 'Überarbeitung fehlgeschlagen.',
        'warn_blla_model_missing': 'blla-Segmentierungsmodell wurde nicht gefunden.',
        'dlg_project_loading_title': 'Projekt laden',
        'white_border_title': 'Weißen Rand hinzufügen',
        'white_border_pixels': 'Rand in Pixel:',
        'image_edit_rotate_off': 'Rotation: AUS',
        'image_edit_rotate_on': 'Rotation: AN',
        'image_edit_grid': 'Raster',
        'image_edit_grid_tooltip': 'Rastergröße: fein, grob',
        'image_edit_grid_label': 'Größe des Rasters',
        'image_edit_crop': 'Crop-Bereich',
        'image_edit_separator': 'Trennbalken',
        'image_edit_gray': 'Grau',
        'image_edit_contrast': 'Kontrast',
        'image_edit_rotation_reset': 'Rotation zurücksetzen',
        'image_edit_smart_split': 'Smart-Splitting',
        'image_edit_prev': 'Vorheriges Bild',
        'image_edit_next': 'Nächstes Bild',
        'image_edit_white_border': 'Weißen Rand hinzufügen',
        'image_edit_white_border_with_px': 'Weißen Rand hinzufügen ({}px)',
        'image_edit_apply_selected': 'Für alle markierten anwenden',
        'image_edit_apply_all': 'Für alle anwenden',
        'image_edit_batch_title': 'Bildbearbeitung läuft',
        'image_edit_batch_label': 'Bearbeite Bild {}/{}: {}',
        'msg_image_edit_batch_cancelled': 'Bildbearbeitung abgebrochen.',
        'image_edit_applied_single_status': 'Bildbearbeitung übernommen. Bearbeitete Bilder wurden im '
                                            'Ursprungsverzeichnis gespeichert und als neue Einträge zur Queue '
                                            'hinzugefügt.',
        'log_image_edit_applied': 'Bildbearbeitung übernommen: {} | {} Ausgabe-Datei(en) im Ursprungsverzeichnis '
                                  'gespeichert',
        'image_edit_no_image_loaded': 'Kein Bild geladen',
        'image_edit_notice_title': 'Hinweis',
        'image_edit_turn_off_rotation_first': 'Rotation ist noch aktiv.\n'
                                              '\n'
                                              "Bitte schalte zuerst 'Rotation: AUS', bevor du den Crop-Bereich oder "
                                              'den Trennbalken bearbeitest.',
        'msg_not_available': 'Nicht verfügbar',
        'help_nav_image_edit': 'Bildbearbeitung',
        'help_nav_lm_alternatives': 'LM-Alternativen',
        'dlg_lm_url_title': 'LM-Server-URL',
        'dlg_lm_url_label':
            """<div class="card">
            <div class="h2"><b>Typische lokale Server</b></div>
            <ul>
                <li><code>http://127.0.0.1:1234/v1</code> - <b>LM Studio<b></li>
                <li><code>http://localhost:11434/v1</code> - <b>Ollama</b></li>
                <li><code>http://127.0.0.1:1337/v1</code> - <b>Jan</b></li>
                <li><code>http://localhost:4891/v1</code> - <b>GPT4All</b></li>
                <li><code>http://127.0.0.1:5000/v1</code> - <b>text-generation-webui</b></li>
                <li><code>http://localhost:8080/v1</code> - <b>LocalAI</b></li>
                <li><code>http://HOST:8000/v1</code> - <b>vLLM</b></li>
            </ul>
        </div>

        <div class="card">
            <div class="h2"><b>Auto-Korrektur</b></div>
            <ul>
                <li>Fehlendes <code>http://</code> wird ergänzt.</li>
                <li><code>/models</code> oder <code>/chat/completions</code> wird automatisch auf die Base-URL gekürzt.</li>
                <li><code>/v1</code> wird bei Bedarf ergänzt.</li>
            </ul>
        </div>

        <div class="card">
            <div class="h2"><b>Wichtig</b></div>
            <ul>
                <li>Keine SSH-Kommandos eintragen.</li>
                <li>Bei SSH-Tunnel bitte die lokale Tunnel-URL verwenden.</li>
                <li>Für Ollama in Bottled Kraken normalerweise die OpenAI-kompatible URL <code>/v1</code> verwenden, nicht die native <code>/api</code>-URL.</li>
            </ul>
        </div>""",
        'dlg_lm_url_placeholder': 'z. B. http://127.0.0.1:1234/v1',
        'help_html_image_edit': '\n'
                                '            <div class="card">\n'
                                '                <div class="h1">Bildbearbeitung</div><br>\n'
                                '                Die Bildbearbeitung dient dazu, Seiten <b>vor der OCR gezielt '
                                'vorzubereiten</b>.\n'
                                '                Das ist besonders nützlich, wenn ein Scan schief, zu dunkel, zu '
                                'kontrastarm,\n'
                                '                zu eng beschnitten oder als Doppelseite gespeichert ist.\n'
                                '            </div>\n'
                                '\n'
                                '            <div class="card">\n'
                                '                <div class="h2">Verfügbare Werkzeuge</div>\n'
                                '                <ul>\n'
                                '                    <li><b>Rotation:</b> Seite begradigen</li>\n'
                                '                    <li><b>Crop-Bereich:</b> störende Ränder gezielt entfernen</li>\n'
                                '                    <li><b>Trennbalken:</b> Doppelseiten oder nebeneinander liegende '
                                'Inhalte sauber teilen</li>\n'
                                '                    <li><b>Grau / Kontrast:</b> Lesbarkeit von Druck und Handschrift '
                                'verbessern</li>\n'
                                '                    <li><b>Weißen Rand hinzufügen:</b> sinnvoll bei zu eng '
                                'beschnittenen Vorlagen</li>\n'
                                '                    <li><b>Smart-Splitting:</b> halbautomatische Aufteilung für '
                                'problematische Vorlagen</li>\n'
                                '                </ul>\n'
                                '            </div>\n'
                                '\n'
                                '            <div class="card">\n'
                                '                <div class="h2">Typischer Einsatz</div>\n'
                                '                <ol>\n'
                                '                    <li>Bild oder PDF-Seite laden</li>\n'
                                '                    <li>Bildbearbeitung öffnen</li>\n'
                                '                    <li>Vorschau anpassen: drehen, beschneiden, Kontrast setzen, ggf. '
                                'teilen</li>\n'
                                '                    <li>Änderung auf das aktuelle Bild, markierte Bilder oder alle '
                                'Bilder anwenden</li>\n'
                                '                    <li>Danach OCR mit Kraken starten</li>\n'
                                '                </ol>\n'
                                '            </div>\n'
                                '\n'
                                '            <div class="card warn">\n'
                                '                <div class="h2">Hinweis</div>\n'
                                '                <span class="badge">Wichtig</span>\n'
                                '                <ul>\n'
                                '                    <li>Wenn Rotation aktiv ist, sollten Crop-Bereich und Trennbalken '
                                'erst nach dem Zurückschalten auf <code>Rotation: AUS</code> fein eingestellt '
                                'werden.</li>\n'
                                '                    <li>Bearbeitete Bilder werden als neue Ausgabe-Dateien '
                                'gespeichert und anschließend wieder in die Queue übernommen.</li>\n'
                                '                </ul>\n'
                                '            </div>\n'
                                '\n'
                                '            <div class="card">\n'
                                '                <div class="h2">Wofür lohnt sich das?</div>\n'
                                '                <ul>\n'
                                '                    <li>schiefe oder verzerrte Scans</li>\n'
                                '                    <li>Doppelseiten aus Büchern oder Akten</li>\n'
                                '                    <li>Formulare mit viel Rand oder störendem Hintergrund</li>\n'
                                '                    <li>blasse historische Drucke oder kontrastarme '
                                'Handschriften</li>\n'
                                '                </ul>\n'
                                '            </div>\n'
                                '        ',
        'help_html_lm_alternatives': '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h1">LM-Studio-Alternativen</div><br>\n'
                                     '                Bottled Kraken ist nicht auf LM Studio beschränkt.\n'
                                     '                Entscheidend ist, dass der laufende Dienst eine '
                                     '<b>OpenAI-kompatible API</b> bereitstellt.\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">Ollama</div>\n'
                                     '                <ul>\n'
                                     '                    <li>für viele der sauberste Ersatz, wenn vor allem ein '
                                     'lokaler Dienst gewünscht ist</li>\n'
                                     '                    <li>native API unter '
                                     '<code>http://localhost:11434/api</code></li>\n'
                                     '                    <li>für Bottled Kraken in der Regel die OpenAI-kompatible '
                                     'URL <code>http://localhost:11434/v1</code> verwenden</li>\n'
                                     '                    <li>zusätzlich gibt es auch Anthropic-Kompatibilität für '
                                     'manche Workflows</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">Jan</div>\n'
                                     '                <ul>\n'
                                     '                    <li>von der Bedienidee her oft am ähnlichsten zu LM '
                                     'Studio</li>\n'
                                     '                    <li>Desktop-App mit lokalen Modellen und eingebautem '
                                     'API-Server</li>\n'
                                     '                    <li>typisch: <code>http://127.0.0.1:1337/v1</code></li>\n'
                                     '                    <li>je nach Konfiguration kann zusätzlich ein API-Key '
                                     'erforderlich sein</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">GPT4All</div>\n'
                                     '                <ul>\n'
                                     '                    <li>ebenfalls sehr nah an „einfach lokal starten und '
                                     'nutzen“</li>\n'
                                     '                    <li>typisch: <code>http://localhost:4891/v1</code></li>\n'
                                     '                    <li>OpenAI-kompatibel</li>\n'
                                     '                    <li>mit LocalDocs auch für einfache lokale '
                                     'Dokument-/RAG-Workflows interessant</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">text-generation-webui</div>\n'
                                     '                <ul>\n'
                                     '                    <li>besonders interessant für Nutzer, die gern tiefer '
                                     'konfigurieren</li>\n'
                                     '                    <li>OpenAI- und Anthropic-kompatible API</li>\n'
                                     '                    <li>typisch: <code>http://127.0.0.1:5000/v1</code></li>\n'
                                     '                    <li>unterstützt je nach Backend auch Vision und '
                                     'Tool-Calling</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">LocalAI</div>\n'
                                     '                <ul>\n'
                                     '                    <li>gut geeignet, wenn eher ein selbst gehosteter lokaler '
                                     'AI-Server als eine Desktop-App gesucht wird</li>\n'
                                     '                    <li>typisch: <code>http://localhost:8080/v1</code></li>\n'
                                     '                    <li>OpenAI-kompatibel, zusätzlich mit Weboberfläche und '
                                     'erweiterten Server-Funktionen</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card warn">\n'
                                     '                <div class="h2">Wichtig</div>\n'
                                     '                <span class="badge">Kompatibilität</span>\n'
                                     '                <ul>\n'
                                     '                    <li>Für Bottled Kraken zählt vor allem die OpenAI-kompatible '
                                     'Base-URL.</li>\n'
                                     '                    <li>Nicht jede Software nutzt dieselben Default-Ports oder '
                                     'dieselbe Authentifizierung.</li>\n'
                                     '                    <li>Wenn eine API-Key-Pflicht aktiv ist, muss Bottled Kraken '
                                     'diesen Header ebenfalls mitsenden.</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '        '},
 'en': {'dlg_filter_img': 'Images/PDF (*.png *.jpg *.jpeg *.tif *.tiff *.bmp *.webp *.pdf)',
        'pdf_render_title': 'Preparing PDF',
        'pdf_render_label': 'Rendering pages… ({}/{}): {}',
        'app_title': 'Bottled Kraken',
        'toolbar_main': 'Toolbar',
        'toolbar_language': 'Language',
        'toolbar_theme_tooltip': 'Switch between light and dark mode',
        'toolbar_language_tooltip': 'Change language',
        'menu_file': '&File',
        'menu_edit': '&Edit',
        'menu_export': 'Export as...',
        'menu_exit': 'Exit',
        'menu_models': '&Kraken Options',
        'menu_options': '&Options',
        'menu_languages': 'Languages',
        'menu_hw': 'CPU/GPU',
        'menu_reading': 'Reading Direction',
        'menu_appearance': 'Appearance',
        'act_clear_rec': 'Clear recognition model',
        'act_clear_seg': 'Clear segmentation model',
        'act_paste_clipboard': 'Paste from clipboard',
        'log_toggle_show': 'Log',
        'log_toggle_hide': 'Log',
        'menu_export_log': 'Export log as .txt...',
        'dlg_save_log': 'Save log',
        'dlg_filter_txt': 'Text (*.txt)',
        'log_started': 'Program started.',
        'log_queue_cleared': 'Queue cleared.',
        'lang_de': 'German',
        'lang_en': 'English',
        'lang_fr': 'French',
        'hw_cpu': 'CPU',
        'hw_cuda': 'GPU – CUDA (NVIDIA)',
        'hw_rocm': 'GPU – ROCm (AMD)',
        'hw_mps': 'GPU – MPS (Apple)',
        'act_undo': 'Undo',
        'act_redo': 'Redo',
        'msg_hw_not_available': 'This hardware is not available on this system. Switching to CPU.',
        'msg_using_device': 'Using device: {}',
        'msg_detected_gpu': 'Detected: {}',
        'msg_device_cpu': 'CPU',
        'msg_device_cuda': 'CUDA',
        'msg_device_rocm': 'ROCm',
        'msg_device_mps': 'MPS',
        'act_add_files': 'Load files...',
        'act_download_model': 'Download model (Zenodo)',
        'act_delete': 'Delete',
        'act_rename': 'Rename...',
        'act_clear_queue': 'Clear queue',
        'act_start_ocr': 'Start Kraken OCR',
        'act_stop_ocr': 'Stop',
        'act_re_ocr': 'Reprocess',
        'act_re_ocr_tip': 'Reprocess selected file(s)',
        'act_overlay_show': 'Show overlay boxes',
        'status_ready': 'Ready.',
        'status_waiting': 'Waiting',
        'status_processing': 'Processing...',
        'status_done': 'Done',
        'status_error': 'Error',
        'lbl_queue': 'Queue:',
        'lbl_lines': 'Recognized lines:',
        'col_file': 'File',
        'col_status': 'Status',
        'drop_hint': 'Drag & drop files here',
        'queue_drop_hint': 'Drag & drop files here',
        'queue_load_title': 'Loading files',
        'queue_load_label': 'Loading file {}/{}: {}',
        'queue_load_cancelled': 'File loading cancelled.',
        'queue_load_pdf_started': 'Loading PDF into queue: {}',
        'info_title': 'Information',
        'warn_title': 'Warning',
        'err_title': 'Error',
        'theme_bright': 'Bright',
        'theme_dark': 'Dark',
        'warn_queue_empty': 'Queue is empty or all items are processed.',
        'warn_select_done': 'No file(s) loaded for re-OCR.',
        'warn_need_rec': 'Please select a format model (recognition) first.',
        'warn_need_seg': 'Please select a segmentation model first.',
        'msg_stopping': 'Stopping...',
        'msg_finished': 'Batch finished.',
        'msg_device': 'Device set to: {}',
        'msg_exported': 'Exported: {}',
        'msg_loaded_rec': 'Format model: {}',
        'msg_loaded_seg': 'Segmentation model: {}',
        'err_load': 'Cannot load image: {}',
        'dlg_title_rename': 'Rename',
        'dlg_label_name': 'New filename:',
        'dlg_save': 'Save',
        'dlg_load_img': 'Choose images',
        'dlg_choose_rec': 'recognition model: ',
        'dlg_choose_seg': 'segmentation model: ',
        'dlg_filter_model': 'Models (*.mlmodel)',
        'reading_tb_lr': 'Top → Bottom + Left → Right',
        'reading_tb_rl': 'Top → Bottom + Right → Left',
        'reading_bt_lr': 'Bottom → Top + Left → Right',
        'reading_bt_rl': 'Bottom → Top + Right → Left',
        'line_menu_move_up': 'Move line up',
        'line_menu_move_down': 'Move line down',
        'line_menu_delete': 'Delete line',
        'line_menu_add_above': 'Add line above',
        'line_menu_add_below': 'Add line below',
        'line_menu_draw_box': 'Draw overlay box',
        'line_menu_edit_box': 'Edit overlay box (move/resize)',
        'line_menu_move_to': 'Move line to…',
        'dlg_new_line_title': 'New line',
        'dlg_new_line_label': 'Text of the new line:',
        'dlg_move_to_title': 'Move line',
        'dlg_move_to_label': 'Target line number (1…):',
        'canvas_menu_add_box_draw': 'Add overlay box (draw)',
        'canvas_menu_delete_box': 'Delete overlay box',
        'canvas_menu_edit_box': 'Edit overlay box…',
        'canvas_menu_select_line': 'Select line',
        'dlg_box_title': 'Overlay box',
        'dlg_box_left': 'left',
        'dlg_box_top': 'top',
        'dlg_box_right': 'right',
        'dlg_box_bottom': 'bottom',
        'dlg_box_apply': 'Apply',
        'export_choose_mode_title': 'Export',
        'export_mode_all': 'Export all files',
        'export_mode_selected': 'Export selected files',
        'export_select_files_title': 'Select files',
        'export_select_files_hint': 'Choose files to export:',
        'export_choose_folder': 'Choose destination folder',
        'export_need_done': 'At least one selected file is not finished.',
        'export_none_selected': 'No files selected.',
        'undo_nothing': 'Nothing to undo.',
        'redo_nothing': 'Nothing to redo.',
        'overlay_only_after_ocr': 'Overlay editing is only available after OCR is finished.',
        'new_line_from_box_title': 'New line',
        'new_line_from_box_label': 'Text for the new line (optional):',
        'log_added_files': '{} file(s) added to the queue.',
        'log_ocr_started': 'OCR started: {} file(s), Device={}, Reading={}',
        'log_stop_requested': 'OCR stop requested.',
        'log_file_started': 'Starting file: {}',
        'log_file_done': 'Done: {} ({} lines)',
        'log_file_error': 'Error: {} -> {}',
        'log_export_done': 'Export finished: {} file(s) as {} to {}',
        'log_export_single': 'Export: {} -> {}',
        'log_export_log_done': 'Log exported: {}',
        'act_ai_revise': 'LM Revision',
        'act_ai_revise_tip': 'Revise OCR text with local LLM',
        'msg_ai_started': 'AI revision started...',
        'msg_ai_done': 'AI revision finished.',
        'msg_ai_model_set': 'AI model ID: {}',
        'msg_ai_disabled': 'AI revision not available.',
        'warn_lm_url_invalid': 'No valid LM server address was entered.\n'
                               'Please check the instructions and try a different address.',
        'warn_need_done_for_ai': 'Please select a finished OCR item first.',
        'warn_need_ai_model': 'No model was found via the configured LM server URL. Please start a local '
                              'OpenAI-compatible server or set a valid URL or model ID (for example LM Studio, Ollama, '
                              'Jan, GPT4All, text-generation-webui, LocalAI, or vLLM).',
        'warn_ai_server': 'Local LM server is not reachable. Please load the model and start the OpenAI-compatible '
                          'server.',
        'dlg_choose_ai_model': 'LM model identifier',
        'dlg_choose_ai_model_label': 'Optional model ID. Leave empty to automatically use the running model from the '
                                     'configured server:',
        'log_ai_started': 'AI revision started: {}',
        'log_ai_done': 'AI revision finished: {}',
        'log_ai_error': 'AI revision error: {} -> {}',
        'status_ai_processing': 'AI revising...',
        'status_exporting': 'Exporting...',
        'menu_project_save': 'Save project',
        'menu_project_save_as': 'Save project as...',
        'menu_project_load': 'Load project...',
        'dlg_filter_project': 'Bottled Kraken Project (*.json)',
        'msg_project_saved': 'Project saved: {}',
        'msg_project_loaded': 'Project loaded: {}',
        'warn_project_load_failed': 'Project could not be loaded: {}',
        'warn_project_save_failed': 'Project could not be saved: {}',
        'warn_project_file_missing': 'File not found: {}',
        'line_menu_swap_with': 'Swap line with…',
        'dlg_swap_title': 'Swap lines',
        'dlg_swap_label': 'Swap with line number (1…):',
        'act_voice_fill': 'Speak lines',
        'act_voice_fill_tip': 'Overwrite lines from microphone with faster-whisper',
        'act_voice_stop': 'Stop recording',
        'msg_voice_started': 'Voice recording started...',
        'msg_voice_stopped': 'Voice recording stopped. Transcribing...',
        'msg_voice_done': 'Voice import finished.',
        'msg_voice_cancelled': 'Voice recording cancelled.',
        'warn_voice_need_done': 'Please select a finished OCR item first.',
        'warn_voice_model_missing': 'Faster-Whisper model directory was not found.',
        'status_voice_recording': 'Recording...',
        'lines_tree_header': 'Recognized lines and words',
        'col_loaded_files': 'Loaded files',
        'btn_rec_model_empty': 'Recognition model: -',
        'btn_rec_model_value': 'Recognition model: {}',
        'btn_seg_model_empty': 'Segmentation model: -',
        'btn_seg_model_value': 'Segmentation model: {}',
        'act_load_rec_model': 'Load recognition model...',
        'act_load_seg_model': 'Load segmentation model...',
        'submenu_available_kraken_models': 'Available Kraken models',
        'submenu_available_ai_models': 'Available LM models',
        'submenu_available_whisper_models': 'Available Whisper models',
        'btn_cancel': 'Cancel',
        'progress_status_ready': 'Ready',
        'voice_record_title': '🎤 Change line with audio',
        'voice_record_info': 'Audio recording controls:',
        'voice_record_start': 'Start recording',
        'voice_record_stop': 'Stop recording',
        'voice_record_processing': 'Whisper is processing audio … please wait a moment.',
        'warn_select_line_first': 'Please select a line first.',
        'warn_selected_line_invalid': 'The selected line is invalid.',
        'warn_whisper_model_not_loaded': "No loaded Whisper model is active. Please choose a model under 'Whisper "
                                         "options'.",
        'warn_no_microphone_available': 'No microphone is available.',
        'log_voice_stopping': 'Stopping voice recording...',
        'image_edit_title': 'Image editing – {}',
        'image_edit_erase_rect': 'Remove area (rectangle)',
        'image_edit_erase_ellipse': 'Remove area (circle)',
        'image_edit_erase_clear': 'Clear removal area',
        'warn_select_image_or_pdf_page': 'Please select an image or a PDF page first.',
        'warn_image_load_failed_detail': 'The image could not be loaded:\n{}',
        'info_no_marked_images_found': 'No marked images found.',
        'msg_image_edit_selected_applied': 'Image editing applied to marked images.',
        'msg_image_edit_all_applied': 'Image editing applied to all images.',
        'log_image_edit_error': 'Image editing error: {} -> {}',
        'act_help': 'Help',
        'act_ai_revise_all': 'Revise all',
        'act_ai_revise_all_tip': 'Revise all fully recognized files',
        'warn_select_multiple_lines_first': 'Please select multiple lines first.',
        'msg_ai_selected_lines_started': 'LM revision started for {} selected lines...',
        'log_ai_multi_started': 'LM multi-line revision started: {} | lines {}',
        'dlg_ai_multi_title': 'AI multi-line revision',
        'dlg_ai_multi_status': 'Revising {} selected lines ...',
        'btn_import_lines': 'Import lines',
        'btn_import_lines_tip': 'Load recognized lines from TXT/JSON',
        'act_import_lines_current': 'For current image',
        'act_import_lines_selected': 'For selected images',
        'act_import_lines_all': 'For all images',
        'warn_import_unsupported_format': 'Unsupported import format: {}',
        'warn_import_no_usable_lines': 'The import file contains no usable lines.',
        'info_no_current_image_loaded': 'No current image loaded.',
        'dlg_import_lines_current': 'Import lines',
        'info_no_images_selected_or_marked': 'No images selected or marked.',
        'dlg_import_lines_selected': 'Load line files for selected images',
        'info_no_images_loaded': 'No images loaded.',
        'dlg_import_lines_all': 'Load line files for all images',
        'warn_no_matching_import_for_selected': 'No import file matches the selected images.\n'
                                                '\n'
                                                'The filenames must match by base name.',
        'warn_no_matching_import_for_loaded': 'No import file matches the loaded images.\n'
                                              '\n'
                                              'The filenames must match by base name.',
        'log_import_error': 'Import error: {} -> {}',
        'log_voice_import_started': 'Sprachimport gestartet: {} | Zeile {} | Mikrofon: {} | Modell: {}',
        'warn_voice_cancelled': 'Aufnahme abgebrochen.',
        'warn_voice_not_finished': 'Aufnahme wurde nicht regulär beendet.',
        'warn_voice_no_audio_data': 'Keine Audiodaten aufgenommen.',
        'voice_status_prepare_wav': 'Audiodatei wird vorbereitet...',
        'voice_status_load_whisper': 'Lade faster-whisper...',
        'voice_status_transcribe_line': 'Transkribiere ausgewählte Zeile lokal ({}/{})...',
        'voice_status_fallback_cpu': 'Initialisierung auf {}/{} fehlgeschlagen. Neuer Versuch mit CPU/int8 …',
        'voice_status_finalize': 'Bereite Text auf...',
        'voice_status_microphone_active': "Mikrofon aktiv … bitte sprechen. Zum Beenden 'Aufnahme stoppen' klicken.",
        'voice_status_input_device': 'Aufnahmegerät: {}',
        'audio_device_default_mic': 'Systemstandard-Mikrofon',
        'audio_device_generic': 'Gerät {}',
        'whisper_status_model': 'Modell: {}',
        'whisper_status_mic': 'Mikrofon: {}',
        'whisper_status_path': 'Pfad: {}',
        'dlg_whisper_model_dir': 'Whisper-Modellordner wählen',
        'msg_whisper_path_set': 'Whisper-Pfad gesetzt: {}',
        'warn_whisper_model_present': 'Das Faster-Whisper large-v3 Modell ist bereits vorhanden.\n'
                                      '\n'
                                      'Pfad:\n'
                                      '{}\n'
                                      '\n'
                                      'Ein erneuter Download ist nicht nötig.',
        'msg_whisper_model_already_present': 'Whisper-Modell bereits vorhanden: {}',
        'warn_whisper_download_start_failed': 'Download des Whisper-Modells konnte nicht gestartet werden:\n{}',
        'msg_whisper_download_start_failed': 'Whisper-Download konnte nicht gestartet werden.',
        'msg_whisper_model_loaded': 'Whisper-Modell geladen: {}',
        'info_whisper_model_downloaded': 'Das Faster-Whisper-Modell wurde erfolgreich heruntergeladen.\n'
                                         '\n'
                                         'Zielordner:\n'
                                         '{}',
        'msg_whisper_download_failed': 'Whisper-Download fehlgeschlagen.',
        'warn_whisper_download_failed': 'Download des Whisper-Modells fehlgeschlagen:\n{}',
        'dlg_help_title': 'Hinweise',
        'help_nav_quick': 'Workflow',
        'help_nav_kraken': 'Kraken',
        'help_nav_lm_server': 'LM server',
        'help_nav_ssh': 'SSH tunnel',
        'help_nav_whisper': 'Whisper',
        'help_nav_shortcuts': 'Shortcuts',
        'help_nav_data_protection': 'Data protection',
        'help_nav_legal': 'Legal',
        'help_whisper_download_label': '<b>Download the Whisper model with a button:</b>',
        'help_os_windows': 'Windows',
        'help_os_arch': 'Arch',
        'help_os_debian': 'Debian',
        'help_os_fedora': 'Fedora',
        'help_os_macos': 'macOS',
        'whisper_hint_debian': 'Note for Debian/Ubuntu/Linux Mint:\n'
                               'The app uses its own Python environment (venv) here to avoid PEP-668 errors with the '
                               'system Python.\n'
                               '\n'
                               'If creating the venv fails, required system packages are usually missing. Run:\n'
                               '\n'
                               'sudo apt update\n'
                               'sudo apt install -y python3-venv python3-pip ffmpeg portaudio19-dev',
        'whisper_hint_fedora': 'Optional note for Fedora:\n'
                               'If sounddevice causes problems later, these system packages may help.\n'
                               '\n'
                               'sudo dnf install -y python3-pip ffmpeg portaudio-devel',
        'whisper_hint_arch': 'Optional note for Arch Linux:\n'
                             'If sounddevice causes problems later, these system packages may help.\n'
                             '\n'
                             'sudo pacman -S --needed python-pip ffmpeg portaudio',
        'whisper_hint_macos': 'Optional note for macOS:\n'
                              'If sounddevice causes problems later, these packages may help.\n'
                              '\n'
                              'brew install ffmpeg portaudio',
        'whisper_hint_windows': 'Optional note for Windows:\n'
                                'Usually no additional system packages are required. If audio problems appear later, '
                                'they are usually related to drivers or microphone permissions.',
        'whisper_hint_generic': 'Optional note:\n'
                                'If sounddevice causes problems later, additional system packages may be required.',
        'whisper_system_hint_dialog': 'Optional system note:\n'
                                      '\n'
                                      '{}\n'
                                      '\n'
                                      'The actual download still runs only through Python (sys.executable -m pip / '
                                      'Python API of huggingface_hub).',
        'warn_whisper_download_running': 'A Whisper download is already running.',
        'msg_whisper_download_prepare_target': 'Starting requirement installation and model download to: {}',
        'dlg_whisper_download_title': 'Loading Whisper model',
        'dlg_whisper_download_prepare': 'Starting Whisper setup ...',
        'hf_status_waiting_for_lock': 'Waiting for file lock in the target folder ...',
        'hf_status_files_done': 'Files finished: {}/{}',
        'hf_status_current_file': 'Current: {}',
        'hf_status_last_finished': 'Last finished: {}',
        'hf_status_download_done': 'Download completed.',
        'hf_error_cancelled': 'Download cancelled.',
        'hf_error_hf_exit': "'hf download' exited with code {}.",
        'hf_error_command_exit': 'Command exited with code {}:\n{}',
        'hf_error_python_missing': 'Python or a required module could not be found.\n'
                                   '\n'
                                   'Please check whether the application is running with a working Python environment.',
        'hf_error_externally_managed': 'The system Python installation must not be modified directly.\n'
                                       '\n'
                                       'The app should automatically use its own environment for this. If this still '
                                       'happened, python3-venv is probably missing.\n'
                                       '\n'
                                       'Please run:\n'
                                       'sudo apt update\n'
                                       'sudo apt install -y python3-venv python3-pip',
        'hf_error_no_venv': 'Python venv support is missing on this system.\n'
                            '\n'
                            'Please run:\n'
                            'sudo apt update\n'
                            'sudo apt install -y python3-venv python3-pip',
        'hf_error_python3_missing': 'python3 was not found.\n\nPlease check whether Python 3 is installed.',
        'warn_invalid_line': 'Invalid line.',
        'btn_ai_model_value': 'KI: {}',
        'llm_status_value': 'LLM: {}',
        'lm_status_model_value': 'Modell: {}',
        'lm_mode_value': 'Modus: {}',
        'lm_server_value': 'Server: {}',
        'dlg_ai_title': 'AI revision',
        'dlg_ai_connecting': 'Connecting to local LM server…',
        'dlg_ai_single_title': 'AI line revision',
        'dlg_ai_single_status': 'Überarbeite nur Zeile {} …',
        'msg_ai_single_started': 'LM-Überarbeitung für Zeile {} gestartet...',
        'log_ai_single_started': 'LM-Zeilenüberarbeitung gestartet: {} | Zeile {}',
        'msg_ai_multi_done': 'LM-Überarbeitung für {} ausgewählte Zeilen abgeschlossen.',
        'log_ai_multi_done': 'LM-Mehrfachzeilenüberarbeitung abgeschlossen: {} | Zeilen {}',
        'msg_ai_multi_cancelled': 'Mehrfachzeilenüberarbeitung abgebrochen.',
        'log_ai_multi_cancelled': 'LM-Mehrfachzeilenüberarbeitung abgebrochen: {}',
        'msg_ai_multi_failed': 'Mehrfachzeilenüberarbeitung fehlgeschlagen.',
        'log_ai_multi_failed': 'LM-Mehrfachzeilenüberarbeitung Fehler: {} -> {}',
        'msg_ai_batch_finished': 'AI batch finished.',
        'log_ai_batch_debug_return': 'KI Batch Rückgabe für {}: {} Zeilen, OCR hatte {} Zeilen',
        'log_ai_batch_debug_old_first': 'ALT erste Zeile: {}',
        'log_ai_batch_debug_new_first': 'NEU erste Zeile: {}',
        'log_ai_batch_debug_all': 'NEU alle Zeilen: {}',
        'msg_ai_cancelled': 'Revision cancelled.',
        'ai_status_start_free_ocr': 'Starte freie KI-OCR: {}',
        'ai_status_step1_title': '1/3 Zeilenweise Box-OCR: {}',
        'ai_status_step1_line': '1/3 Box-OCR Zeile {}/{}: {}',
        'ai_status_step2_form': '2/3 Block-Kontext-OCR (Formularmodus): {}',
        'ai_status_step2_plain': '2/3 Block-Kontext-OCR: {}',
        'ai_status_step2_chunk': '2/3 Block-Kontext {}/{}: Zeilen {}-{}',
        'ai_status_step3_merge': '3/3 Merge: Box primär, Page nur wenn lokal konsistent: {}',
        'ai_status_done': 'KI-Überarbeitung abgeschlossen: {}',
        'ai_err_bad_scheme': 'Unsupported scheme: {}',
        'ai_err_invalid_endpoint': 'Invalid endpoint.',
        'ai_err_timeout': 'Timeout while waiting for LM server.',
        'ai_err_invalid_json': 'Invalid JSON response from LM server: {}',
        'ai_err_http': 'HTTP error: {}\n{}',
        'ai_err_server_unreachable': 'LM server not reachable: {}',
        'ai_err_no_choices': 'LM server lieferte keine choices. Antwort:\n{}',
        'ai_err_reasoning_truncated': 'Das Modell hat nur reasoning_content geliefert und wurde vor der eigentlichen '
                                      'JSON-Antwort abgeschnitten (finish_reason=length). Erhöhe max_tokens oder '
                                      'verwende ein nicht-thinkendes Modell.',
        'ai_err_reasoning_only': 'Das Modell hat nur reasoning_content geliefert, aber keinen normalen content. '
                                 'Verwende am besten ein nicht-thinkendes Modell oder erzwinge text/json ohne '
                                 'reasoning.',
        'ai_err_no_content': 'LM server returned no usable response content.',
        'ai_err_page_invalid_json': 'Seiten-OCR lieferte kein gültiges JSON-Objekt.\n\nExtrahierter Content:\n{}',
        'ai_err_page_invalid_lines': "Seiten-OCR lieferte kein gültiges Feld 'lines'.\n\nExtrahierter Content:\n{}",
        'ai_err_page_long_blocks': 'Seiten-OCR hat vermutlich mehrere Zielzeilen zu langen Blöcken zusammengezogen.',
        'ai_err_page_no_usable_lines': 'Seiten-OCR lieferte keine verwertbaren Zeilen: {}/{}',
        'ai_err_block_invalid_json': 'Block-OCR lieferte kein gültiges JSON-Objekt.\n\nExtrahierter Content:\n{}',
        'ai_err_block_invalid_lines': "Block-OCR lieferte kein gültiges Feld 'lines'.\n\nExtrahierter Content:\n{}",
        'ai_err_final_merge_count': 'Finale Merge-Ausgabe gab {} statt {} Zeilen zurück.',
        'help_html_quick': '\n'
                           '            <div class="card warn">\n'
                           '                <div class="h1">Workflow</div>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <ol>\n'
                           '                    <li>Load an image or PDF</li>\n'
                           '                    <li>Optional: use image editing for preparation</li>\n'
                           '                    <li>Load the recognition model</li>\n'
                           '                    <li>Load the segmentation model</li>\n'
                           '                    <li>Start Kraken OCR</li>\n'
                           '                    <li>Check the recognized lines and correct them if needed</li>\n'
                           '                    <li>Optional: use LM revision or Whisper</li>\n'
                           '                    <li>Export the result as TXT, CSV, JSON, ALTO, hOCR, or PDF</li>\n'
                           '                </ol>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">Preparation</div>\n'
                           '                <span class="badge">Optional</span>\n'
                           '                <ul>\n'
                           '                    <li>Image editing can already be used <b>before</b> OCR if a scan is '
                           'poorly cropped, too low in contrast, or contains too much surrounding content.</li>\n'
                           '                    <li>The most useful tools here are <b>crop area</b>, <b>separator '
                           'bar</b>, <b>gray</b>, <b>contrast</b>, and <b>smart splitting</b>.</li>\n'
                           '                    <li>This makes it easier to prepare double pages, form halves, '
                           'margins, or distracting neighboring content before the actual OCR pass.</li>\n'
                           '                    <li>It is especially helpful for record pages, forms, batch scans, and '
                           'badly digitized archival material.</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">Post-processing</div>\n'
                           '                <span class="badge">Optional</span>\n'
                           '                <ul>\n'
                           '                    <li>Load an LM model via LM Studio or another compatible LM '
                           'server</li>\n'
                           '                    <li>Smooth OCR lines linguistically or semantically with a local '
                           'language model</li>\n'
                           '                    <li>Re-record individual lines with Faster-Whisper through the '
                           'microphone</li>\n'
                           '                    <li>Import lines from TXT or JSON</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">Overlay boxes &amp; lines</div>\n'
                           '                <span class="badge">Optional</span>\n'
                           '                <ul>\n'
                           '                    <li>Lines and overlay boxes can be moved, split, added, or '
                           'deleted.</li>\n'
                           '                    <li>This allows the line structure to be improved in a targeted way '
                           'before running OCR again.</li>\n'
                           '                    <li>Especially useful for forms, column layouts, and badly segmented '
                           'handwriting.</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">What does Bottled Kraken do?</div><br>\n'
                           '                Bottled Kraken combines classic OCR with preparatory image editing, manual '
                           'post-processing, and optional local AI support.\n'
                           '                This lets you improve difficult historical prints, handwriting, or form '
                           'pages step by step.\n'
                           '            </div>\n'
                           '        ',
        'help_html_kraken': '\n'
                            '    <div class="card">\n'
                            '        <div class="h1">Kraken</div><br>\n'
                            '        Kraken is the OCR/ATR foundation of Bottled Kraken.\n'
                            '        It is an open-source system for automatic text recognition,\n'
                            '        developed especially for historical prints, handwriting, and non-Latin scripts.\n'
                            '    </div>\n'
                            '\n'
                            '    <div class="card">\n'
                            '        <div class="h2">What is important about it for Bottled Kraken?</div>\n'
                            '        <ul>\n'
                            '            <li><b>Segmentation:</b> Detects layout, text regions, lines, and reading '
                            'order.</li>\n'
                            '            <li><b>Recognition:</b> Reads the actual text from the detected lines.</li>\n'
                            '            <li><b>Models:</b> Segmentation and recognition run via trained models that '
                            'must match the material.</li>\n'
                            '        </ul>\n'
                            '    </div>\n'
                            '\n'
                            '    <div class="card">\n'
                            '        <div class="h2">Typical Kraken workflow</div>\n'
                            '        <ol>\n'
                            '            <li>Prepare the image</li>\n'
                            '            <li>Segment the page (<code>segment</code>)</li>\n'
                            '            <li>Recognize the text (<code>ocr</code>)</li>\n'
                            '            <li>Structure / export the result</li>\n'
                            '        </ol>\n'
                            '        In Bottled Kraken, these exact steps are transferred into the interface:\n'
                            '        first the segmentation model, then the recognition model, then OCR and export.\n'
                            '    </div>\n'
                            '\n'
                            '    <div class="card">\n'
                            '        <div class="h2">Key strengths of Kraken</div>\n'
                            '        <ul>\n'
                            '            <li>trainable layout analysis, reading order, and character recognition</li>\n'
                            '            <li>support for right-to-left, BiDi, and top-to-bottom</li>\n'
                            '            <li>output as ALTO, PageXML, abbyyXML, and hOCR</li>\n'
                            '            <li>word bounding boxes and character cuts</li>\n'
                            '            <li>public model collection via HTRMoPo / Zenodo</li>\n'
                            '        </ul>\n'
                            '    </div>\n'
                            '\n'
                            '    <div class="card">\n'
                            '        <div class="h2">Models</div><br>\n'
                            '        Kraken works in a model-based way.\n'
                            '        Good results depend heavily on the model matching the document type.\n'
                            '        A model trained on historical prints is usually much better for historical prints\n'
                            '        than a general model for modern material.\n'
                            '        <br><br>\n'
                            '        <b>Note:</b> Downloaded Kraken models should be placed in the same folder / directory\n'
                            '        as the EXE file so that Bottled Kraken can find them automatically.\n'
                            '    </div>\n'
                            '\n'
                            '    <div class="card">\n'
                            '        <div class="h2">Interfaces</div><br>\n'
                            '        Kraken offers two main approaches:\n'
                            '        <ul>\n'
                            '            <li><b>CLI:</b> for classic OCR workflows</li>\n'
                            '            <li><b>Python API:</b> for custom applications and integrations</li>\n'
                            '        </ul>\n'
                            '        Bottled Kraken uses the Python library directly in the program code.\n'
                            '    </div>\n'
                            '\n'
                            '    <div class="card">\n'
                            '        <div class="h2">Official sources</div>\n'
                            '        <ul>\n'
                            '            <li><a href="https://github.com/mittagessen/kraken">GitHub: '
                            'mittagessen/kraken</a></li>\n'
                            '            <li><a href="https://kraken.re/7.0/index.html">Kraken Documentation '
                            '7.0</a></li>\n'
                            '            <li><a href="https://kraken.re/7.0/getting_started.html">Getting '
                            'Started</a></li>\n'
                            '            <li><a href="https://kraken.re/7.0/user_guide/models.html">Model '
                            'Management</a></li>\n'
                            '        </ul>\n'
                            '    </div>\n'
                            '\n'
                            '    <div class="card warn">\n'
                            '        <div class="h2">Note</div>\n'
                            '        <span class="badge">Important</span><br>\n'
                            '        If the segmentation is not clean, recognition will also perform worse.\n'
                            '        That is exactly why Bottled Kraken uses <code>blla.mlmodell</code> by default\n'
                            '        instead of the legacy segmentation model <code>pageseg</code>.\n'
                            '    </div>\n',
        'help_html_lm_server': '\n'
                               '            <div class="card">\n'
                               '                <div class="h1">LM server / local model servers</div><br>\n'
                               '                This section is meant for <b>local language-model '
                               'post-processing</b>.\n'
                               '                For this, Bottled Kraken expects an <b>OpenAI-compatible base URL</b>, '
                               'usually including <code>/v1</code>.\n'
                               '            </div>\n'
                               '\n'
                               '            <div class="card">\n'
                               '                <div class="h2">Base URLs that fit Bottled Kraken directly</div>\n'
                               '                <pre>LM Studio:               http://localhost:1234/v1\n'
                               'Ollama:                  http://localhost:11434/v1\n'
                               'GPT4All:                 http://localhost:4891/v1\n'
                               'text-generation-webui:   http://127.0.0.1:5000/v1\n'
                               'LocalAI:                 http://localhost:8080/v1</pre>\n'
                               '                <div class="muted">\n'
                               '                    Important: with Ollama, enter the <b>OpenAI-compatible</b> '
                               '<code>/v1</code> URL in Bottled Kraken, not the raw <code>/api</code> route.\n'
                               '                </div>\n'
                               '            </div>\n'
                               '\n'
                               '            <div class="card">\n'
                               '                <div class="h2">LM Studio</div>\n'
                               '                <ul>\n'
                               '                    <li>For many users, this is the easiest starting point if you want '
                               'a desktop app with model management and local serving.</li>\n'
                               '                    <li>LM Studio exposes local models through REST, '
                               'OpenAI-compatible, and Anthropic-compatible endpoints.</li>\n'
                               '                    <li>The standard Bottled Kraken case is '
                               '<code>http://localhost:1234/v1</code>.</li>\n'
                               '                </ul>\n'
                               '            </div>\n'
                               '\n'
                               '            <div class="card">\n'
                               '                <div class="h2">Ollama</div>\n'
                               '                <ul>\n'
                               '                    <li>Usually the cleanest choice if you mainly want a local service '
                               'and a lean CLI/daemon workflow.</li>\n'
                               '                    <li>Ollama starts locally on <code>http://localhost:11434</code>, '
                               'offers its own <code>/api</code> interface, and also provides OpenAI compatibility '
                               'under <code>/v1</code>.</li>\n'
                               '                    <li>It also supports Anthropic-compatible usage for workflows such '
                               'as Claude Code.</li>\n'
                               '                    <li>For Bottled Kraken, <code>http://localhost:11434/v1</code> is '
                               'usually the best choice.</li>\n'
                               '                </ul>\n'
                               '            </div>\n'
                               '\n'
                               '            <div class="card">\n'
                               '                <div class="h2">Jan</div>\n'
                               '                <ul>\n'
                               '                    <li>In terms of interaction style, Jan is often the closest '
                               'alternative to LM Studio: desktop app, local models, built-in OpenAI-compatible API '
                               'server.</li>\n'
                               '                    <li>By default, Jan listens on <code>http://127.0.0.1:1337</code> '
                               'with the API prefix <code>/v1</code>; the default host <code>127.0.0.1</code> is '
                               'intentionally local-only.</li>\n'
                               '                    <li>Jan also requires an API key by default. In practice, that '
                               'means Jan is most useful with Bottled Kraken if you adapt the expected header behavior '
                               'or place a small local proxy in between.</li>\n'
                               '                </ul>\n'
                               '            </div>\n'
                               '\n'
                               '            <div class="card">\n'
                               '                <div class="h2">GPT4All</div>\n'
                               '                <ul>\n'
                               '                    <li>Very close to “just start locally and use it”.</li>\n'
                               '                    <li>Its local API server runs by default on '
                               '<code>http://localhost:4891/v1</code>, is OpenAI-compatible, and listens only on '
                               '<code>localhost</code>.</li>\n'
                               '                    <li>On top of that, GPT4All includes <b>LocalDocs</b> for a simple '
                               'local document/RAG workflow.</li>\n'
                               '                    <li>For Bottled Kraken, it is usually one of the most '
                               'straightforward LM Studio alternatives.</li>\n'
                               '                </ul>\n'
                               '            </div>\n'
                               '\n'
                               '            <div class="card">\n'
                               '                <div class="h2">text-generation-webui (oobabooga)</div>\n'
                               '                <ul>\n'
                               '                    <li>Most interesting for people who like to tweak things, switch '
                               'backends, and control many settings themselves.</li>\n'
                               '                    <li>The project supports several backends such as '
                               '<code>llama.cpp</code>, <code>Transformers</code>, <code>ExLlamaV3</code>, and '
                               '<code>TensorRT-LLM</code>.</li>\n'
                               '                    <li>Its OpenAI-/Anthropic-compatible API can be used as a drop-in '
                               'replacement; by default it typically uses port <code>5000</code>.</li>\n'
                               '                    <li>It also includes tool calling, vision, and file '
                               'attachments.</li>\n'
                               '                </ul>\n'
                               '            </div>\n'
                               '\n'
                               '            <div class="card">\n'
                               '                <div class="h2">LocalAI</div>\n'
                               '                <ul>\n'
                               '                    <li>Best suited if you are thinking more in terms of a self-hosted '
                               'local AI server than a classic desktop app.</li>\n'
                               '                    <li>LocalAI exposes an OpenAI-compatible API; the typical Bottled '
                               'Kraken setup is <code>http://localhost:8080/v1</code>.</li>\n'
                               '                    <li>It also supports additional compatible API formats, a web UI, '
                               'and agent/MCP features.</li>\n'
                               '                    <li>A good choice if you want to bundle several local services or '
                               'build a small internal AI stack.</li>\n'
                               '                </ul>\n'
                               '            </div>\n'
                               '\n'
                               '            <div class="card">\n'
                               '                <div class="h2">Practical selection guide</div>\n'
                               '                <ul>\n'
                               '                    <li><b>LM Studio:</b> if you want a GUI, local serving, and low '
                               'friction</li>\n'
                               '                    <li><b>Ollama:</b> if you prefer a clean local service or CLI '
                               'workflow</li>\n'
                               '                    <li><b>Jan:</b> if you want LM-Studio-like desktop handling and '
                               'can live with API-key/proxy setup</li>\n'
                               '                    <li><b>GPT4All:</b> if you want a simple desktop solution plus '
                               'LocalDocs</li>\n'
                               '                    <li><b>text-generation-webui:</b> if you want fine control over '
                               'backends, vision, and tooling</li>\n'
                               '                    <li><b>LocalAI:</b> if you want a more self-hosted local server '
                               'with broader API/agent focus</li>\n'
                               '                </ul>\n'
                               '            </div>\n'
                               '\n'
                               '            <div class="card">\n'
                               '                <div class="h2">Official sources</div>\n'
                               '                <ul>\n'
                               '                    <li><a href="https://lmstudio.ai/docs/developer/core/server">LM '
                               'Studio Docs – Local LLM API Server</a></li>\n'
                               '                    <li><a href="https://lmstudio.ai/docs/developer/openai-compat">LM '
                               'Studio Docs – OpenAI Compatibility</a></li>\n'
                               '                    <li><a '
                               'href="https://docs.ollama.com/api/openai-compatibility">Ollama Docs – OpenAI '
                               'compatibility</a></li>\n'
                               '                    <li><a '
                               'href="https://docs.ollama.com/integrations/claude-code">Ollama Docs – Claude Code / '
                               'Anthropic-compatible API</a></li>\n'
                               '                    <li><a href="https://www.jan.ai/docs/desktop/api-server">Jan Docs '
                               '– Local API Server</a></li>\n'
                               '                    <li><a '
                               'href="https://docs.gpt4all.io/gpt4all_api_server/home.html">GPT4All Docs – API '
                               'Server</a></li>\n'
                               '                    <li><a '
                               'href="https://github.com/oobabooga/text-generation-webui">text-generation-webui – '
                               'Repository</a></li>\n'
                               '                    <li><a '
                               'href="https://github.com/oobabooga/text-generation-webui/wiki/12-%E2%80%90-OpenAI-API">text-generation-webui '
                               '– OpenAI / Anthropic API Wiki</a></li>\n'
                               '                    <li><a href="https://localai.io/docs/overview/">LocalAI Docs – '
                               'Overview</a></li>\n'
                               '                    <li><a href="https://localai.io/basics/getting_started/">LocalAI '
                               'Docs – Quickstart</a></li>\n'
                               '                </ul>\n'
                               '            </div>\n'
                               '        ',
        'help_html_ssh': '\n'
                         '    <div class="card">\n'
                         '        <div class="h1">Remote access via SSH tunnel</div><br>\n'
                         '        An SSH tunnel is useful when your LM server is running on another machine\n'
                         '        but is only bound to <code>127.0.0.1</code> there and is therefore not directly '
                         'reachable on the network.\n'
                         '    </div>\n'
                         '\n'
                         '    <div class="card">\n'
                         '        <div class="h2">What happens here?</div><br>\n'
                         '        The tunnel forwards a local port on your computer to a port on the remote machine.\n'
                         '        For Bottled Kraken, it then looks as if the LM server were running locally on your '
                         'own computer.\n'
                         '    </div>\n'
                         '\n'
                            '            <div class="card">\n'
                            '                <div class="h2">Example</div><br>\n'
                            '                <b>On machine A</b><br>\n'
                            '                Start LM Studio<br>\n'
                            '                Find the IP address of machine A, for example with:\n'
                            '                <pre>ipconfig\n'
                            'hostname -I</pre>\n'
                            '                Assume the IP address is:\n'
                            '                <pre>192.168.1.50</pre>\n'
                            '                <b>On machine B</b><br>\n'
                            '                Open the SSH tunnel:\n'
                            '                <pre>ssh -N -L 1234:127.0.0.1:1234 user@192.168.1.50</pre>\n'
                            '                <b>Use on machine B</b><br>\n'
                            '                Test in the terminal:\n'
                            '                <pre>curl http://127.0.0.1:1234/v1/models</pre>\n'
                            '                Enter this in Bottled Kraken:\n'
                            '                <pre>http://127.0.0.1:1234/v1</pre>\n'
                            '            </div>\n'
                         '\n'
                            '    <div class="card">\n'
                            '        <div class="h2">Typical workflow</div>\n'
                            '        <ol>\n'
                            '            <li>Start LM Studio on machine A</li>\n'
                            '            <li>Find the IP address of machine A</li>\n'
                            '            <li>Open the SSH tunnel on machine B using that IP address</li>\n'
                            '            <li>Test on machine B whether <code>http://127.0.0.1:1234/v1/models</code> is reachable</li>\n'
                            '            <li>Enter <code>http://127.0.0.1:1234/v1</code> in Bottled Kraken</li>\n'
                            '        </ol>\n'
                            '    </div>\n'
                         '\n'
                         '    <div class="card warn">\n'
                         '        <div class="h2">Important</div>\n'
                         '        <ul>\n'
                         '            <li>In Bottled Kraken, you do <b>not</b> enter the SSH command.</li>\n'
                         '            <li>You always enter the resulting HTTP URL, for example '
                         '<code>http://127.0.0.1:1234/v1</code>.</li>\n'
                         '            <li>The SSH tunnel must remain open as long as Bottled Kraken should use the '
                         'server.</li>\n'
                         '        </ul>\n'
                         '    </div>\n',
        'help_html_whisper_intro': '\n'
                                   '    <div class="card">\n'
                                   '        <div class="h1">Faster-Whisper</div>\n'
                                   '        <p>\n'
                                   '            Faster-Whisper is a fast local speech-to-text recognizer.\n'
                                   '            In Bottled Kraken, you can use it to re-dictate individual OCR lines '
                                   'via microphone\n'
                                   '            and insert them directly as text.\n'
                                   '        </p>\n'
                                   '    </div>\n'
                                   '\n'
                                   '    <div class="card">\n'
                                   '        <div class="h2">What is this useful for?</div>\n'
                                   '        <ul>\n'
                                   '            <li>when an OCR line is badly damaged or was recognized '
                                   'incorrectly</li>\n'
                                   '            <li>when you can dictate individual fields or names faster than typing '
                                   'them</li>\n'
                                   '            <li>when you want to make targeted corrections line by line</li>\n'
                                   '        </ul>\n'
                                   '    </div>\n'
                                   '\n'
                                   '    <div class="card">\n'
                                   '        <div class="h2">What gets downloaded?</div>\n'
                                   '        <p>\n'
                                   '            The model <span class="badge">Systran/faster-whisper-large-v3</span> '
                                   'is loaded.\n'
                                   '        </p>\n'
                                   '        <p class="muted">\n'
                                   '            Before the download, Bottled Kraken automatically installs the '
                                   'required Python packages.\n'
                                   '            The actual model download is handled through the Hugging Face CLI via '
                                   '<code>hf download</code>.\n'
                                   '            Under Linux and macOS, a separate venv environment is used '
                                   'automatically for this.\n'
                                   '        </p>\n'
                                   '    </div>\n'
                                   '\n'
                                   '    <div class="card">\n'
                                   '        <div class="h2">Workflow in Bottled Kraken</div>\n'
                                   '        <ol>\n'
                                   '            <li>Download the Whisper model or scan for an existing model</li>\n'
                                   '            <li>Select a microphone</li>\n'
                                   '            <li>Mark a line</li>\n'
                                   '            <li>Start audio recording</li>\n'
                                   '            <li>The spoken input is transcribed locally and replaces the '
                                   'line</li>\n'
                                   '        </ol>\n'
                                   '    </div>\n',
        'help_html_shortcuts': '\n'
                               '    <div class="card">\n'
                               '        <div class="h1">Keyboard Shortcuts</div>\n'
                               '        <table class="table">\n'
                               '            <tr><td class="section" colspan="2">Project</td></tr>\n'
                               '            <tr><td><span class="kbd">Ctrl + S</span></td><td>Save project</td></tr>\n'
                               '            <tr><td><span class="kbd">Ctrl + Shift + S</span></td><td>Save project '
                               'as</td></tr>\n'
                               '            <tr><td><span class="kbd">Ctrl + I</span></td><td>Load project</td></tr>\n'
                               '            <tr><td><span class="kbd">Ctrl + E</span></td><td>Export</td></tr>\n'
                               '            <tr><td><span class="kbd">Ctrl + Q</span></td><td>Quit program</td></tr>\n'
                               '\n'
                               '            <tr><td class="section" colspan="2">OCR &amp; LM</td></tr>\n'
                               '            <tr><td><span class="kbd">Ctrl + K</span></td><td>Start Kraken '
                               'OCR</td></tr>\n'
                               '            <tr><td><span class="kbd">Ctrl + P</span></td><td>Stop Kraken '
                               'OCR</td></tr>\n'
                               '            <tr><td><span class="kbd">Ctrl + L</span></td><td>Start LM '
                               'revision</td></tr>\n'
                               '            <tr><td><span class="kbd">Ctrl + M</span></td><td>Start Faster-Whisper / '
                               'microphone</td></tr>\n'
                               '\n'
                               '            <tr><td class="section" colspan="2">Selection</td></tr>\n'
                               '            <tr><td><span class="kbd">Ctrl + A</span></td><td>Select everything in the '
                               'current context</td></tr>\n'
                               '            <tr><td><span class="kbd">Del</span></td><td>Delete selected lines or '
                               'boxes</td></tr>\n'
                               '\n'
                               '            <tr><td class="section" colspan="2">Function Keys</td></tr>\n'
                               '            <tr><td><span class="kbd">F1</span></td><td>Shortcut help</td></tr>\n'
                               '            <tr><td><span class="kbd">F2</span></td><td>Load recognition '
                               'model</td></tr>\n'
                               '            <tr><td><span class="kbd">F3</span></td><td>Load segmentation '
                               'model</td></tr>\n'
                               '            <tr><td><span class="kbd">F4</span></td><td>Enter LM server URL</td></tr>\n'
                               '            <tr><td><span class="kbd">F5</span></td><td>Start LM scan</td></tr>\n'
                               '            <tr><td><span class="kbd">F6</span></td><td>Scan Whisper models + set '
                               'first microphone</td></tr>\n'
                               '            <tr><td><span class="kbd">F7</span></td><td>Toggle log window</td></tr>\n'
                               '        </table>\n'
                               '    </div>\n',
        'help_html_data_protection': '\n'
                                     '            <div class="card warn">\n'
                                     '                <div class="h1">Data protection</div><br>\n'
                                     '                The following notes summarize the <b>standard local operating '
                                     'mode</b>.\n'
                                     '                They do not replace a case-by-case privacy review.\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">General rule</div>\n'
                                     '                <ul>\n'
                                     '                    <li>Local models and local servers are generally more '
                                     'privacy-friendly because prompts, documents, and audio are not automatically '
                                     'sent to a cloud service.</li>\n'
                                     '                    <li>That is only true as long as the software is actually '
                                     'used <b>locally</b> and without cloud or network routing.</li>\n'
                                     '                    <li>As soon as network exposure, tunnels, reverse proxies, '
                                     'remote instances, or cloud models are involved, the privacy situation '
                                     'changes.</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">LM Studio</div>\n'
                                     '                <ul>\n'
                                     '                    <li>According to the official documentation, LM Studio can '
                                     'operate fully offline; local chat, document chat, and the local server do not '
                                     'require internet access for that.</li>\n'
                                     '                    <li>The privacy policy also states explicitly that messages, '
                                     'chat histories, and documents are not transmitted off the system by '
                                     'default.</li>\n'
                                     '                    <li>That applies to local use. If you enable network serving '
                                     'or remote features, you need to review where data goes.</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">Ollama</div>\n'
                                     '                <ul>\n'
                                     '                    <li>Ollama runs locally by default on '
                                     '<code>http://localhost:11434</code>; no authentication is required for purely '
                                     'local API use.</li>\n'
                                     '                    <li>That keeps a localhost-only setup on your own '
                                     'machine.</li>\n'
                                     '                    <li>Important: Ollama also supports <b>cloud models</b>. As '
                                     'soon as you use them, the workflow is no longer purely local.</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">Jan</div>\n'
                                     '                <ul>\n'
                                     '                    <li>Jan presents itself as privacy-first and stores data '
                                     'locally in its own data folder.</li>\n'
                                     '                    <li>Its local API is restricted to <code>127.0.0.1</code> by '
                                     'default, which is the safer default for single-user use.</li>\n'
                                     '                    <li>At the same time, Jan offers analytics/tracking settings '
                                     'and detailed server logs. Before productive use, it is worth checking '
                                     'consciously what is logged locally and whether network access has been '
                                     'enabled.</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">GPT4All</div>\n'
                                     '                <ul>\n'
                                     '                    <li>GPT4All emphasizes local execution on your own '
                                     'hardware.</li>\n'
                                     '                    <li>Its API server listens on <code>localhost</code> only by '
                                     'default, not to other devices on the network.</li>\n'
                                     '                    <li>With <b>LocalDocs</b>, local documents can be added to '
                                     'the workflow; even then, storage location and device access control still '
                                     'matter.</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">text-generation-webui &amp; LocalAI</div>\n'
                                     '                <ul>\n'
                                     '                    <li><b>text-generation-webui</b> describes its '
                                     'OpenAI-/Anthropic-compatible API as 100% offline and private, and also states '
                                     'that it does not create logs.</li>\n'
                                     '                    <li><b>LocalAI</b> positions itself as a local '
                                     'OpenAI-compatible stack and advertises that it keeps your data private and '
                                     'secure.</li>\n'
                                     '                    <li>For both projects, the same practical rule applies: once '
                                     'you expose the API on the network, put it behind a reverse proxy, or allow '
                                     'multiple users, you need to secure access, logs, backups, and admin permissions '
                                     'yourself.</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">faster-whisper</div><br>\n'
                                     '                faster-whisper is a local Whisper implementation based on '
                                     'CTranslate2.\n'
                                     '                In Bottled Kraken, a local model directory is loaded and a local '
                                     'WAV file is transcribed.\n'
                                     '                As long as this workflow remains local, audio processing also '
                                     'remains local.\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card warn">\n'
                                     '                <div class="h2">Important limitations</div>\n'
                                     '                <ul>\n'
                                     '                    <li>The one-time model download naturally requires internet '
                                     'access.</li>\n'
                                     '                    <li>Even a “local” server can expose personal data if the '
                                     'device itself is not secured properly.</li>\n'
                                     '                    <li>For public institutions, archives, companies, or '
                                     'research organizations, tool properties alone are not enough; storage location, '
                                     'role concepts, logs, backups, deletion rules, and internal policies matter as '
                                     'well.</li>\n'
                                     '                    <li>A software license or privacy policy does not replace a '
                                     'GDPR, contractual, or operational review for a specific deployment.</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">Official sources</div>\n'
                                     '                <ul>\n'
                                     '                    <li><a href="https://lmstudio.ai/docs/app/offline">LM Studio '
                                     'Docs – Offline Operation</a></li>\n'
                                     '                    <li><a href="https://lmstudio.ai/privacy">LM Studio Desktop '
                                     'App Privacy Policy</a></li>\n'
                                     '                    <li><a '
                                     'href="https://docs.ollama.com/api/authentication">Ollama Docs – '
                                     'Authentication</a></li>\n'
                                     '                    <li><a href="https://docs.ollama.com/cloud">Ollama Docs – '
                                     'Cloud</a></li>\n'
                                     '                    <li><a href="https://ollama.com/privacy">Ollama – Privacy '
                                     'Policy</a></li>\n'
                                     '                    <li><a href="https://www.jan.ai/docs/desktop/privacy">Jan '
                                     'Docs – Privacy</a></li>\n'
                                     '                    <li><a '
                                     'href="https://www.jan.ai/docs/desktop/data-folder">Jan Docs – Data '
                                     'Folder</a></li>\n'
                                     '                    <li><a href="https://www.jan.ai/docs/desktop/api-server">Jan '
                                     'Docs – Local API Server</a></li>\n'
                                     '                    <li><a '
                                     'href="https://docs.gpt4all.io/gpt4all_api_server/home.html">GPT4All Docs – API '
                                     'Server</a></li>\n'
                                     '                    <li><a href="https://github.com/nomic-ai/gpt4all">GPT4All – '
                                     'Repository</a></li>\n'
                                     '                    <li><a '
                                     'href="https://github.com/oobabooga/text-generation-webui/wiki/12-%E2%80%90-OpenAI-API">text-generation-webui '
                                     '– OpenAI / Anthropic API Wiki</a></li>\n'
                                     '                    <li><a href="https://localai.io/docs/overview/">LocalAI Docs '
                                     '– Overview</a></li>\n'
                                     '                    <li><a '
                                     'href="https://github.com/SYSTRAN/faster-whisper">SYSTRAN / '
                                     'faster-whisper</a></li>\n'
                                     '                    <li><a '
                                     'href="https://github.com/opennmt/ctranslate2">CTranslate2</a></li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '        ',
        'help_html_legal': '\n'
                           '            <div class="card warn">\n'
                           '                <div class="h1">Legal</div><br>\n'
                           '                The following notes are general guidance and do not replace legal advice.\n'
                           '                For concrete use cases, the legal situation should be reviewed '
                           'individually.\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card ok">\n'
                           '                <div class="h2">Bottled Kraken</div>\n'
                           '                <ul>\n'
                           '                    <li><b>Repository license:</b> GPL-3.0.</li>\n'
                           '                    <li><b>In short:</b> if you redistribute the software, publish '
                           'modified versions, or distribute a package built on top of it, the GPL-3.0 terms must be '
                           'respected.</li>\n'
                           '                    <li><b>Important:</b> this is separate from the licenses of the '
                           'bundled libraries and the model files you use.</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">Kraken</div>\n'
                           '                <ul>\n'
                           '                    <li>Kraken is the OCR foundation of Bottled Kraken.</li>\n'
                           '                    <li>The project is licensed under the <b>Apache License 2.0</b>.</li>\n'
                           '                    <li>For redistribution, the license text, copyright notices, and '
                           'possible NOTICE requirements are especially relevant.</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">faster-whisper</div>\n'
                           '                <ul>\n'
                           '                    <li>faster-whisper is used in Bottled Kraken for local speech-to-text '
                           'features.</li>\n'
                           '                    <li>The project is licensed under the <b>MIT License</b>.</li>\n'
                           '                    <li>Separate conditions may still apply to models and additional '
                           'dependencies.</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">LM Studio</div>\n'
                           '                <ul>\n'
                           '                    <li>LM Studio is used optionally as a local or connected '
                           'language-model server.</li>\n'
                           '                    <li>The main governing documents here are the official <b>Terms of '
                           'Service</b> and <b>Privacy Policy</b>.</li>\n'
                           '                    <li>In addition, every model loaded through LM Studio may have its own '
                           'model license.</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">Ollama</div>\n'
                           '                <ul>\n'
                           '                    <li>The software in the official repository is licensed under the '
                           '<b>MIT License</b>.</li>\n'
                           '                    <li>That is usually straightforward for local use; if you redistribute '
                           'modified software, license and copyright notices still matter.</li>\n'
                           '                    <li>Separate from that are <b>cloud features</b>, privacy rules, and '
                           'above all the license terms of the models you run.</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">Jan</div>\n'
                           '                <ul>\n'
                           '                    <li>The Jan repository is published as an open-source project; its '
                           'repository license is <b>AGPL-3.0</b>.</li>\n'
                           '                    <li>The AGPL is especially relevant when modified versions are made '
                           'available over a network.</li>\n'
                           '                    <li>As with the other tools, additional conditions may apply to '
                           'embedded models and external cloud providers.</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">GPT4All</div>\n'
                           '                <ul>\n'
                           '                    <li>The official GPT4All repository is licensed under the <b>MIT '
                           'License</b>.</li>\n'
                           '                    <li>The software license is permissive; separate checks are still '
                           'needed for model licenses, trademark use, and third-party components.</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">text-generation-webui (oobabooga)</div>\n'
                           '                <ul>\n'
                           '                    <li>The project is licensed under <b>AGPL-3.0</b>.</li>\n'
                           '                    <li>That is legally stricter than MIT or Apache, especially when you '
                           'modify the software or make it available over a network.</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">LocalAI</div>\n'
                           '                <ul>\n'
                           '                    <li>According to the official repository, LocalAI is licensed under '
                           'the <b>MIT License</b>.</li>\n'
                           '                    <li>As with the other servers, model licenses, extra components, and '
                           'organizational usage rules still need separate review.</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">PySide6 / Qt for Python</div>\n'
                           '                <ul>\n'
                           '                    <li>Bottled Kraken’s graphical interface is based on PySide6 / Qt for '
                           'Python.</li>\n'
                           '                    <li>Qt for Python uses license models that can involve <b>LGPL</b> or '
                           'commercial Qt licensing, depending on the component and distribution model.</li>\n'
                           '                    <li>For redistribution, packaging, and proprietary combined products, '
                           'the Qt licensing situation should be checked separately.</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card warn">\n'
                           '                <div class="h2">Additional note on models and content</div>\n'
                           '                <ul>\n'
                           '                    <li>The software license of an application must always be '
                           'distinguished from the license of the OCR, speech, or AI models loaded into it.</li>\n'
                           '                    <li>The processing of copyrighted documents, personal data, or '
                           'sensitive archival materials also requires a separate legal assessment.</li>\n'
                           '                    <li>This window gives only a compact overview, not a binding '
                           'case-specific legal review.</li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '\n'
                           '            <div class="card">\n'
                           '                <div class="h2">Official sources</div>\n'
                           '                <ul>\n'
                           '                    <li><a href="https://github.com/Testatost/Bottled-Kraken">Bottled '
                           'Kraken – Repository</a></li>\n'
                           '                    <li><a href="https://github.com/mittagessen/kraken">Kraken – '
                           'Repository</a></li>\n'
                           '                    <li><a href="https://kraken.re/7.0/index.html">Kraken – '
                           'Documentation</a></li>\n'
                           '                    <li><a href="https://github.com/SYSTRAN/faster-whisper">faster-whisper '
                           '– Repository</a></li>\n'
                           '                    <li><a href="https://lmstudio.ai/app-terms">LM Studio – Terms of '
                           'Service</a></li>\n'
                           '                    <li><a href="https://lmstudio.ai/privacy">LM Studio – Privacy '
                           'Policy</a></li>\n'
                           '                    <li><a href="https://github.com/ollama/ollama">Ollama – '
                           'Repository</a></li>\n'
                           '                    <li><a '
                           'href="https://github.com/ollama/ollama/blob/main/LICENSE">Ollama – MIT License</a></li>\n'
                           '                    <li><a href="https://github.com/janhq/jan">Jan – Repository</a></li>\n'
                           '                    <li><a '
                           'href="https://docs.gpt4all.io/gpt4all_api_server/home.html">GPT4All – API Server '
                           'Docs</a></li>\n'
                           '                    <li><a '
                           'href="https://github.com/nomic-ai/gpt4all/blob/main/LICENSE.txt">GPT4All – MIT '
                           'License</a></li>\n'
                           '                    <li><a '
                           'href="https://github.com/oobabooga/text-generation-webui">text-generation-webui – '
                           'Repository</a></li>\n'
                           '                    <li><a '
                           'href="https://github.com/oobabooga/text-generation-webui/blob/main/LICENSE">text-generation-webui '
                           '– AGPL-3.0</a></li>\n'
                           '                    <li><a href="https://localai.io/docs/overview/">LocalAI – '
                           'Overview</a></li>\n'
                           '                    <li><a '
                           'href="https://github.com/mudler/LocalAI/blob/master/LICENSE">LocalAI – MIT '
                           'License</a></li>\n'
                           '                    <li><a href="https://doc.qt.io/qtforpython-6/">Qt for Python – '
                           'Documentation</a></li>\n'
                           '                    <li><a href="https://doc.qt.io/qtforpython-6/licenses.html">Qt for '
                           'Python – Licenses</a></li>\n'
                           '                </ul>\n'
                           '            </div>\n'
                           '        ',
        'ai_prompt_page_system': 'Du bist ein hochpräziser OCR- und Transkriptionsassistent für historische deutsche '
                                 'Drucke, Handschriften und Formulare.\n'
                                 'Du liest den Text direkt aus dem Bild.\n'
                                 'Das Bild ist die einzige Wahrheitsquelle.\n'
                                 'Du musst den gelesenen Text auf eine bereits vorgegebene Liste von Zielzeilen '
                                 'abbilden.\n'
                                 'Jede Zielzeile entspricht genau einer visuellen Formular- oder Textzeile.\n'
                                 'Du darfst keine zwei Zielzeilen zusammenziehen.\n'
                                 'Du darfst keine zusätzliche Leerzeile halluzinieren.\n'
                                 'Du darfst keinen langen Textblock in eine einzelne Zielzeile schreiben.\n'
                                 'Wenn eine Zielzeile keinen sicher lesbaren Text enthält, gib für genau diese Zeile '
                                 'einen leeren String zurück.\n'
                                 'Du musst die Anzahl der Zielzeilen exakt einhalten.\n'
                                 'Antworte ausschließlich mit gültigem JSON.\n'
                                 'Kein Markdown. Kein Zusatztext. Kein Kommentar.',
        'ai_prompt_page_user': 'Lies den Text direkt aus dem Bild.\n'
                               '\n'
                               'Du musst die vorgegebene Kraken-Zeilenstruktur EXAKT einhalten.\n'
                               'Es gibt genau {} Zielzeilen.\n'
                               'Jeder idx steht für genau eine visuelle Zielzeile.\n'
                               '\n'
                               'HARTE REGELN:\n'
                               '- Gib genau {} Einträge im Feld lines zurück\n'
                               '- Die idx-Werte müssen exakt 0 bis {} sein\n'
                               '- Kein idx darf fehlen\n'
                               '- Kein idx darf doppelt vorkommen\n'
                               '- Keine zwei Zielzeilen dürfen zu einer Zeile zusammengezogen werden\n'
                               '- Kein langer Satzblock darf in einer einzelnen Zielzeile landen\n'
                               '- Wenn eine Zielzeile unklar ist, gib den bestmöglichen kurzen Zeilentext zurück\n'
                               '- Wenn die Zielzeile wirklich leer ist, gib text als leeren String zurück\n'
                               '- Die bbox ist nur Orientierung für die visuelle Zuordnung\n'
                               '- Gib NUR das JSON-Objekt zurück\n'
                               '- Kein Markdown\n'
                               '- Keine Analyse\n'
                               '- Keine Kommentare\n'
                               '- Keine zusätzlichen Sätze\n'
                               '\n'
                               'Kraken-Zielzeilenstruktur:\n'
                               '{}\n'
                               '\n'
                               'Antwortformat exakt so:\n'
                               '{{"lines":[{{"idx":0,"text":"..."}},{{"idx":1,"text":"..."}}]}}',
        'ai_prompt_single_system': 'Du bist ein präziser OCR- und Transkriptionsassistent für historische deutsche '
                                   'Handschriften und Formulare.\n'
                                   'Du liest genau eine einzelne Zielzeile aus einem Bildausschnitt.\n'
                                   'Das Bild ist die einzige Wahrheitsquelle.\n'
                                   'Die Zielzeile befindet sich in der Mitte des Ausschnitts.\n'
                                   'Oberhalb oder unterhalb sichtbare Linien, Leerzeilen, Formularlinien, Labels oder '
                                   'Nachbarzeilen sind nur Kontext.\n'
                                   'Du darfst nur den Text der einen Zielzeile zurückgeben.\n'
                                   'Du darfst keinen Text aus Nachbarzeilen übernehmen.\n'
                                   'Du darfst keine zusätzliche Zeile erfinden.\n'
                                   'Du darfst keine lange Passage bilden, wenn im Ausschnitt nur eine kurze '
                                   'Formularzeile steht.\n'
                                   'Wenn die Zielzeile leer ist, gib einen leeren String zurück.\n'
                                   'Antworte ausschließlich mit gültigem JSON.\n'
                                   'Kein Markdown. Kein Zusatztext. Kein Kommentar.',
        'ai_prompt_single_user': 'Lies genau die Zielzeile in der Mitte des Bildausschnitts.\n'
                                 'WICHTIG:\n'
                                 '- Gib nur den Text dieser EINEN Zeile zurück\n'
                                 '- Benachbarte Zeilen dürfen nicht übernommen werden\n'
                                 '- Formular-Labels, Linien und Leerbereiche dürfen nicht halluziniert ergänzt werden\n'
                                 '- Wenn in dieser Zielzeile kein lesbarer Text steht, gib text als leeren String '
                                 'zurück\n'
                                 '- Keine zweite Zeile\n'
                                 '- Keine Zusammenfassung\n'
                                 '- Keine Erklärung\n'
                                 '- Kein Markdown\n'
                                 '- Keine Ausgabe vor oder nach dem JSON\n'
                                 '\n'
                                 'Format exakt:\n'
                                 '{{"text":"..."}}\n'
                                 '\n'
                                 'Zeilenindex: {}',
        'ai_prompt_decision_system': 'Du bist ein präziser OCR-Korrekturassistent für historische deutsche '
                                     'Handschriften und Formulare.\n'
                                     'Du bekommst für genau eine Zielzeile drei Kandidaten:\n'
                                     '1. Kraken-OCR\n'
                                     '2. OCR aus dem Gesamtseiten-Kontext\n'
                                     '3. OCR aus der Overlay-Box dieser Zeile\n'
                                     '\n'
                                     'WICHTIG:\n'
                                     '- Die Overlay-Box-OCR ist die Primärquelle.\n'
                                     '- Die Seiten-OCR ist NUR Kontext und darf keine fremden Nachbarzeilen in diese '
                                     'Zielzeile hineinziehen.\n'
                                     '- Kraken ist nur schwacher Fallback.\n'
                                     '- Du darfst keine zusätzliche Zeile erfinden.\n'
                                     '- Du darfst keinen Text aus benachbarten Formularzeilen übernehmen.\n'
                                     '- Du darfst keine lange Mehrzeilen-Passage in diese eine Zielzeile packen.\n'
                                     '- Wenn die Box-OCR plausibel ist, übernimm sie.\n'
                                     '- Nur wenn die Box-OCR klar abgeschnitten, leer oder offensichtlich falsch ist, '
                                     'darfst du mit Kraken korrigieren.\n'
                                     '- Die Seiten-OCR darf nur helfen, ein einzelnes unsicheres Wort zu bestätigen, '
                                     'nicht die ganze Zeile zu ersetzen.\n'
                                     '- Bewahre historische Schreibweise.\n'
                                     'Antworte ausschließlich mit gültigem JSON.\n'
                                     'Kein Markdown. Kein Zusatztext. Kein Kommentar.',
        'ai_prompt_decision_user': 'Zielzeile idx={}\n'
                                   '\n'
                                   'Kraken-OCR:\n'
                                   '{}\n'
                                   '\n'
                                   'Seitenkontext-OCR (nur Kontext, nicht Primärquelle):\n'
                                   '{}\n'
                                   '\n'
                                   'Overlay-Box-OCR (Primärquelle):\n'
                                   '{}\n'
                                   '\n'
                                   'Wähle die beste finale Fassung für GENAU diese eine Zeile.\n'
                                   'Bevorzuge die Overlay-Box-OCR.\n'
                                   'Gib nur die finale Textzeile zurück.\n'
                                   'Format exakt:\n'
                                   '{{"text":"..."}}',
        'ai_prompt_block_system': 'Du bist ein präziser OCR- und Transkriptionsassistent für historische deutsche '
                                  'Handschriften.\n'
                                  'Lies den Text frei direkt aus dem Bild.\n'
                                  'Das Bild ist die einzige Wahrheitsquelle.\n'
                                  'Du darfst nicht den OCR-Hinweis rekonstruieren, sondern musst das Bild selbst '
                                  'lesen.\n'
                                  'Die von außen vorgegebene Zeilenanzahl ist nur ein Strukturrahmen.\n'
                                  'Du musst den frei gelesenen Text passend in genau diese Anzahl von Zeilen '
                                  'eintragen.\n'
                                  'Antworte ausschließlich mit gültigem JSON.\n'
                                  'Kein Markdown. Kein Zusatztext. Kein Kommentar.',
        'ai_prompt_block_user': 'Lies die handschriftlichen Zeilen im Bildausschnitt.\n'
                                'Gib ausschließlich genau EIN JSON-Objekt zurück.\n'
                                'Kein Markdown. Kein ```json. Kein Kommentar. Kein Zusatztext.\n'
                                'Es müssen genau {} Einträge im Feld lines stehen.\n'
                                'Wichtig:\n'
                                '- doppelte Anführungszeichen innerhalb von text immer als " escapen\n'
                                '- keine weiteren Felder außer idx und text\n'
                                '- keine Ausgabe vor oder nach dem JSON\n'
                                'Format:\n'
                                '{{"lines":[{{"idx":0,"text":"..."}}]}}\n'
                                '\n'
                                'Die idx-Werte müssen lokal bei 0 beginnen.\n'
                                'Aktueller OCR-Hinweis:\n'
                                '{}',
        'line_menu_ai_revise_single': 'Revise only this line with LM',
        'btn_ok': 'OK',
        'act_image_edit': 'Image editing',
        'canvas_menu_split_box': 'Split box',
        'queue_ctx_check_all': 'Check all',
        'queue_ctx_uncheck_all': 'Clear all checkmarks',
        'queue_check_header_tooltip': 'Click to check all files or clear all checks',
        'line_menu_ai_revise_selected': 'Revise selected lines with LM',
        'menu_lm_options': 'LM options',
        'menu_whisper_options': 'Whisper options',
        'act_whisper_set_path': 'Set Whisper model path...',
        'act_whisper_set_mic': 'Choose microphone...',
        'act_scan_local': 'Scan locally',
        'no_models_scan': 'No models - check directory',
        'act_unload_model': 'Unload model',
        'msg_whisper_model_unloaded': 'Whisper model unloaded.',
        'msg_whisper_models_found': '{} Whisper model(s) found.',
        'msg_whisper_models_not_found': 'No Whisper models found.',
        'warn_no_audio_devices': 'No audio input devices were found.',
        'dlg_choose_microphone': 'Choose microphone',
        'dlg_audio_input_device': 'Audio input device:',
        'msg_microphone_set': 'Microphone set: {}',
        'export_choose_format_label': 'Choose export format:',
        'msg_pdf_render_already_running': 'A PDF is already being rendered. Please wait a moment.',
        'pdf_page_display': '{} – Page {:04d}',
        'act_set_manual_lm_url': 'Set LM server URL...',
        'act_clear_manual_lm_url': 'Clear LM server URL',
        'msg_lm_found_url': 'LM found: {} | URL: {}',
        'msg_lm_no_models_url': 'No models found | URL: {}',
        'msg_lm_found': 'LM found: {}',
        'msg_lm_server_not_found': 'No reachable local LM server found.',
        'act_clear_ai_model': 'Remove LM model',
        'msg_ai_model_choice_cleared': 'LM model selection cleared.',
        'msg_ai_model_removed': 'LM model removed.',
        'header_rec_models': 'Recognition models:',
        'header_seg_models': 'Segmentation models:',
        'status_rec_model': 'Recognition model: {}',
        'status_seg_model': 'Segmentation model: {}',
        'msg_ai_model_id_cleared_auto': 'AI model ID cleared, localhost auto-detection active.',
        'msg_ai_single_done': 'LM revision for line {} completed.',
        'log_ai_single_done': 'LM line revision completed: {} | line {}',
        'msg_ai_single_cancelled': 'Line revision cancelled.',
        'log_ai_single_cancelled': 'LM line revision cancelled: {}',
        'msg_ai_single_failed': 'Line revision failed.',
        'log_ai_single_failed': 'LM line revision error: {} -> {}',
        'msg_ai_cancelled_short': 'Revision cancelled.',
        'msg_ai_failed_short': 'Revision failed.',
        'warn_blla_model_missing': 'The blla segmentation model could not be found.',
        'dlg_project_loading_title': 'Load project',
        'white_border_title': 'Add white border',
        'white_border_pixels': 'Border in pixels:',
        'image_edit_rotate_off': 'Rotation: OFF',
        'image_edit_rotate_on': 'Rotation: ON',
        'image_edit_grid': 'Grid',
        'image_edit_grid_tooltip': 'Grid size: fine to coarse',
        'image_edit_grid_label': 'Grid size',
        'image_edit_crop': 'Crop area',
        'image_edit_separator': 'Separator bar',
        'image_edit_gray': 'Grayscale',
        'image_edit_contrast': 'Contrast',
        'image_edit_rotation_reset': 'Reset rotation',
        'image_edit_smart_split': 'Smart splitting',
        'image_edit_prev': 'Previous image',
        'image_edit_next': 'Next image',
        'image_edit_white_border': 'Add white border',
        'image_edit_white_border_with_px': 'Add white border ({} px)',
        'image_edit_apply_selected': 'Apply to all marked',
        'image_edit_apply_all': 'Apply to all',
        'image_edit_applied_single_status': "Image editing applied. Edited images were saved in the folder 'Bottled "
                                            "Kraken edited Bilder' and added to the queue as new entries.",
        'log_image_edit_applied': "Image editing applied: {} | {} output file(s) saved in the folder 'Bottled Kraken "
                                  "edited Bilder'",
        'image_edit_no_image_loaded': 'No image loaded',
        'image_edit_batch_title': 'Image editing in progress',
        'image_edit_batch_label': 'Processing image {}/{}: {}',
        'msg_image_edit_batch_cancelled': 'Image editing cancelled.',
        'image_edit_notice_title': 'Notice',
        'image_edit_turn_off_rotation_first': 'Rotation is still active.\n'
                                              '\n'
                                              "Please switch to 'Rotation: OFF' before editing the crop area or the "
                                              'separator bar.',
        'msg_not_available': 'Not available',
        'help_nav_image_edit': 'Image editing',
        'help_nav_lm_alternatives': 'LM alternatives',
        'dlg_lm_url_title': 'LM server URL',
        'dlg_lm_url_label': """<div class="card">
        <div class="h2"><b>Typical local servers</b></div>
        <ul>
            <li><code>http://127.0.0.1:1234/v1</code> - <b>LM Studio</b></li>
            <li><code>http://localhost:11434/v1</code> - <b>Ollama</b></li>
            <li><code>http://127.0.0.1:1337/v1</code> - <b>Jan</b></li>
            <li><code>http://localhost:4891/v1</code> - <b>GPT4All</b></li>
            <li><code>http://127.0.0.1:5000/v1</code> - <b>text-generation-webui</b></li>
            <li><code>http://localhost:8080/v1</code> - <b>LocalAI</b></li>
            <li><code>http://HOST:8000/v1</code> - <b>vLLM</b></li>
        </ul>
    </div>

    <div class="card">
        <div class="h2"><b>Auto-correction</b></div>
        <ul>
            <li>A missing <code>http://</code> prefix is added automatically.</li>
            <li><code>/models</code> or <code>/chat/completions</code> is automatically trimmed back to the base URL.</li>
            <li><code>/v1</code> is added if needed.</li>
        </ul>
    </div>

    <div class="card">
        <div class="h2"><b>Important</b></div>
        <ul>
            <li>Do not enter SSH commands.</li>
            <li>For SSH tunnels, use the local tunnel URL.</li>
            <li>For Ollama in Bottled Kraken, normally use the OpenAI-compatible <code>/v1</code> URL, not the native <code>/api</code> URL.</li>
        </ul>
    </div>""",
        'dlg_lm_url_placeholder': 'e.g. http://127.0.0.1:1234/v1',
        'help_html_image_edit': '\n'
                                '            <div class="card">\n'
                                '                <div class="h1">Image editing</div><br>\n'
                                '                Image editing is meant to <b>prepare pages before OCR</b>.\n'
                                '                This is especially useful when a scan is skewed, too dark, '
                                'low-contrast,\n'
                                '                tightly cropped, or stored as a double page.\n'
                                '            </div>\n'
                                '\n'
                                '            <div class="card">\n'
                                '                <div class="h2">Available tools</div>\n'
                                '                <ul>\n'
                                '                    <li><b>Rotation:</b> straighten a page</li>\n'
                                '                    <li><b>Crop area:</b> remove disturbing margins</li>\n'
                                '                    <li><b>Separator bar:</b> split double pages or side-by-side '
                                'content cleanly</li>\n'
                                '                    <li><b>Grayscale / Contrast:</b> improve readability of print and '
                                'handwriting</li>\n'
                                '                    <li><b>Add white border:</b> useful for pages that are cropped '
                                'too tightly</li>\n'
                                '                    <li><b>Smart splitting:</b> semi-automatic splitting for '
                                'difficult source material</li>\n'
                                '                </ul>\n'
                                '            </div>\n'
                                '\n'
                                '            <div class="card">\n'
                                '                <div class="h2">Typical workflow</div>\n'
                                '                <ol>\n'
                                '                    <li>Load an image or PDF page</li>\n'
                                '                    <li>Open image editing</li>\n'
                                '                    <li>Adjust the preview: rotate, crop, change contrast, split if '
                                'needed</li>\n'
                                '                    <li>Apply the result to the current image, marked images, or all '
                                'images</li>\n'
                                '                    <li>Run Kraken OCR afterwards</li>\n'
                                '                </ol>\n'
                                '            </div>\n'
                                '\n'
                                '            <div class="card warn">\n'
                                '                <div class="h2">Note</div>\n'
                                '                <span class="badge">Important</span>\n'
                                '                <ul>\n'
                                '                    <li>If rotation is active, fine-tune the crop area and separator '
                                'bar only after switching back to <code>Rotation: OFF</code>.</li>\n'
                                '                    <li>Edited images are saved as new output files and then added '
                                'back to the queue.</li>\n'
                                '                </ul>\n'
                                '            </div>\n'
                                '\n'
                                '            <div class="card">\n'
                                '                <div class="h2">When is it worth using?</div>\n'
                                '                <ul>\n'
                                '                    <li>skewed or distorted scans</li>\n'
                                '                    <li>double-page book or archival scans</li>\n'
                                '                    <li>forms with too much margin or noisy background</li>\n'
                                '                    <li>faded historical prints or low-contrast handwriting</li>\n'
                                '                </ul>\n'
                                '            </div>\n'
                                '        ',
        'help_html_lm_alternatives': '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h1">LM Studio alternatives</div><br>\n'
                                     '                Bottled Kraken is not limited to LM Studio.\n'
                                     '                What matters is that the running service provides an '
                                     '<b>OpenAI-compatible API</b>.\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">Ollama</div>\n'
                                     '                <ul>\n'
                                     '                    <li>for many users the cleanest replacement when a local '
                                     'service is the main goal</li>\n'
                                     '                    <li>native API at '
                                     '<code>http://localhost:11434/api</code></li>\n'
                                     '                    <li>for Bottled Kraken, usually use the OpenAI-compatible '
                                     'URL <code>http://localhost:11434/v1</code></li>\n'
                                     '                    <li>also offers Anthropic compatibility for some '
                                     'workflows</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">Jan</div>\n'
                                     '                <ul>\n'
                                     '                    <li>often the closest to LM Studio in terms of desktop '
                                     'workflow</li>\n'
                                     '                    <li>desktop app with local models and a built-in API '
                                     'server</li>\n'
                                     '                    <li>typical URL: <code>http://127.0.0.1:1337/v1</code></li>\n'
                                     '                    <li>depending on configuration, an API key may also be '
                                     'required</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">GPT4All</div>\n'
                                     '                <ul>\n'
                                     '                    <li>also very close to “start locally and use it”</li>\n'
                                     '                    <li>typical URL: <code>http://localhost:4891/v1</code></li>\n'
                                     '                    <li>OpenAI-compatible</li>\n'
                                     '                    <li>LocalDocs can also be useful for simple local document / '
                                     'RAG workflows</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">text-generation-webui</div>\n'
                                     '                <ul>\n'
                                     '                    <li>especially useful for users who like more control and '
                                     'configuration</li>\n'
                                     '                    <li>OpenAI- and Anthropic-compatible API</li>\n'
                                     '                    <li>typical URL: <code>http://127.0.0.1:5000/v1</code></li>\n'
                                     '                    <li>depending on the backend, it can also support vision and '
                                     'tool calling</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">LocalAI</div>\n'
                                     '                <ul>\n'
                                     '                    <li>well suited when you want a self-hosted local AI server '
                                     'rather than a classic desktop app</li>\n'
                                     '                    <li>typical URL: <code>http://localhost:8080/v1</code></li>\n'
                                     '                    <li>OpenAI-compatible, plus a web UI and extended server '
                                     'features</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card warn">\n'
                                     '                <div class="h2">Important</div>\n'
                                     '                <span class="badge">Compatibility</span>\n'
                                     '                <ul>\n'
                                     '                    <li>For Bottled Kraken, the main thing is the '
                                     'OpenAI-compatible base URL.</li>\n'
                                     '                    <li>Not every tool uses the same default ports or '
                                     'authentication.</li>\n'
                                     '                    <li>If API key authentication is enabled, Bottled Kraken '
                                     'must send that header as well.</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '        '},
 'fr': {'dlg_filter_img': 'Images/PDF (*.png *.jpg *.jpeg *.tif *.tiff *.bmp *.webp *.pdf)',
        'pdf_render_title': 'Préparation du PDF',
        'pdf_render_label': 'Rendu des pages… ({}/{}): {}',
        'app_title': 'Bottled Kraken',
        'toolbar_main': 'Barre d’outils',
        'toolbar_language': 'Langue',
        'toolbar_theme_tooltip': 'Basculer entre le mode clair et sombre',
        'toolbar_language_tooltip': 'Changer la langue',
        'menu_file': '&Fichier',
        'menu_edit': '&Édition',
        'menu_export': 'Exporter en tant que...',
        'menu_exit': 'Quitter',
        'menu_models': '&Options Kraken',
        'menu_options': '&Options',
        'menu_languages': 'Langues',
        'menu_hw': 'CPU/GPU',
        'menu_reading': 'Direction de lecture',
        'menu_appearance': 'Apparence',
        'act_clear_rec': 'Retirer le modèle de reconnaissance',
        'act_clear_seg': 'Retirer le modèle de segmentation',
        'act_paste_clipboard': 'Coller depuis le presse-papiers',
        'log_toggle_show': 'Log',
        'log_toggle_hide': 'Log',
        'menu_export_log': 'Exporter le log en .txt...',
        'dlg_save_log': 'Enregistrer le log',
        'dlg_filter_txt': 'Texte (*.txt)',
        'log_started': 'Programme démarré.',
        'log_queue_cleared': 'File d’attente vidée.',
        'lang_de': 'Allemand',
        'lang_en': 'Anglais',
        'lang_fr': 'Français',
        'hw_cpu': 'CPU',
        'hw_cuda': 'GPU – CUDA (NVIDIA)',
        'hw_rocm': 'GPU – ROCm (AMD)',
        'hw_mps': 'GPU – MPS (Apple)',
        'act_undo': 'Annuler',
        'act_redo': 'Rétablir',
        'msg_hw_not_available': 'Ce matériel n’est pas disponible sur ce système. Retour au CPU.',
        'msg_using_device': 'Appareil utilisé : {}',
        'msg_detected_gpu': 'Détecté : {}',
        'msg_device_cpu': 'CPU',
        'msg_device_cuda': 'CUDA',
        'msg_device_rocm': 'ROCm',
        'msg_device_mps': 'MPS',
        'act_add_files': 'Charger des fichiers…',
        'act_download_model': 'Télécharger le modèle (Zenodo)',
        'act_delete': 'Supprimer',
        'act_rename': 'Renommer...',
        'act_clear_queue': 'Vider la file d’attente',
        'act_start_ocr': 'Démarrer Kraken OCR',
        'act_stop_ocr': 'Arrêter',
        'act_re_ocr': 'Relancer',
        'act_re_ocr_tip': 'Relancer le traitement du/des fichier(s) sélectionné(s)',
        'act_overlay_show': 'Afficher les boîtes de superposition',
        'status_ready': 'Prêt.',
        'status_waiting': 'En attente',
        'status_processing': 'Traitement...',
        'status_done': 'Terminé',
        'status_error': 'Erreur',
        'lbl_queue': 'File d’attente:',
        'lbl_lines': 'Lignes reconnues:',
        'col_file': 'Fichier',
        'col_status': 'Statut',
        'drop_hint': 'Glissez-déposez des fichiers ici',
        'queue_drop_hint': 'Glissez-déposez des fichiers ici',
        'queue_load_title': 'Chargement des fichiers',
        'queue_load_label': 'Chargement du fichier {}/{} : {}',
        'queue_load_cancelled': 'Chargement des fichiers annulé.',
        'queue_load_pdf_started': 'Chargement du PDF dans la file d’attente : {}',
        'info_title': 'Information',
        'warn_title': 'Avertissement',
        'err_title': 'Erreur',
        'theme_bright': 'Clair',
        'theme_dark': 'Sombre',
        'warn_queue_empty': 'La file d’attente est vide ou tous les éléments ont été traités.',
        'warn_select_done': 'Aucun fichier chargé pour relancer l’OCR.',
        'warn_need_rec': 'Veuillez d’abord sélectionner un modèle de format (reconnaissance).',
        'warn_need_seg': 'Veuillez d’abord sélectionner un modèle de segmentation.',
        'msg_stopping': 'Arrêt...',
        'msg_finished': 'Traitement terminé.',
        'msg_device': 'Appareil réglé sur: {}',
        'msg_exported': 'Exporté: {}',
        'msg_loaded_rec': 'Modèle de format: {}',
        'msg_loaded_seg': 'Modèle de segmentation: {}',
        'err_load': 'Impossible de charger l’image: {}',
        'dlg_title_rename': 'Renommer',
        'dlg_label_name': 'Nouveau nom de fichier:',
        'dlg_save': 'Enregistrer',
        'dlg_load_img': 'Choisir des images',
        'dlg_choose_rec': 'le modèle de reconnaissance: ',
        'dlg_choose_seg': 'le modèle de segmentation: ',
        'dlg_filter_model': 'Modèles (*.mlmodel)',
        'reading_tb_lr': 'Haut → Bas + Gauche → Droite',
        'reading_tb_rl': 'Haut → Bas + Droite → Gauche',
        'reading_bt_lr': 'Bas → Haut + Gauche → Droite',
        'reading_bt_rl': 'Bas → Haut + Droite → Gauche',
        'line_menu_move_up': 'Monter la ligne',
        'line_menu_move_down': 'Descendre la ligne',
        'line_menu_delete': 'Supprimer la ligne',
        'line_menu_add_above': 'Ajouter une ligne au-dessus',
        'line_menu_add_below': 'Ajouter une ligne en dessous',
        'line_menu_draw_box': 'Dessiner la boîte',
        'line_menu_edit_box': 'Modifier la boîte (déplacer/redimensionner)',
        'line_menu_move_to': 'Déplacer la ligne vers…',
        'dlg_new_line_title': 'Nouvelle ligne',
        'dlg_new_line_label': 'Texte de la nouvelle ligne:',
        'dlg_move_to_title': 'Déplacer la ligne',
        'dlg_move_to_label': 'Numéro de ligne cible (1…):',
        'canvas_menu_add_box_draw': 'Ajouter une boîte (dessiner)',
        'canvas_menu_delete_box': 'Supprimer la boîte',
        'canvas_menu_edit_box': 'Modifier la boîte…',
        'canvas_menu_select_line': 'Sélectionner la ligne',
        'dlg_box_title': 'Boîte de superposition',
        'dlg_box_left': 'gauche',
        'dlg_box_top': 'haut',
        'dlg_box_right': 'droite',
        'dlg_box_bottom': 'bas',
        'dlg_box_apply': 'Appliquer',
        'export_choose_mode_title': 'Export',
        'export_mode_all': 'Exporter tous les fichiers',
        'export_mode_selected': 'Exporter les fichiers sélectionnés',
        'export_select_files_title': 'Sélectionner des fichiers',
        'export_select_files_hint': 'Choisissez les fichiers à exporter :',
        'export_choose_folder': 'Choisir le dossier de destination',
        'export_need_done': 'Au moins un fichier sélectionné n’est pas terminé.',
        'export_none_selected': 'Aucun fichier sélectionné.',
        'undo_nothing': 'Rien à annuler.',
        'redo_nothing': 'Rien à rétablir.',
        'overlay_only_after_ocr': 'L’édition des overlays n’est disponible qu’après l’OCR.',
        'new_line_from_box_title': 'Nouvelle ligne',
        'new_line_from_box_label': 'Texte pour la nouvelle ligne (optionnel):',
        'log_added_files': '{} fichier(s) ajouté(s) à la file d’attente.',
        'log_ocr_started': 'OCR démarré : {} fichier(s), Appareil={}, Lecture={}',
        'log_stop_requested': 'Arrêt de l’OCR demandé.',
        'log_file_started': 'Traitement du fichier : {}',
        'log_file_done': 'Terminé : {} ({} lignes)',
        'log_file_error': 'Erreur : {} -> {}',
        'log_export_done': 'Export terminé : {} fichier(s) en {} vers {}',
        'log_export_single': 'Export : {} -> {}',
        'log_export_log_done': 'Log exporté : {}',
        'act_ai_revise': 'Révision LM',
        'act_ai_revise_tip': 'Réviser le texte OCR avec un LLM local',
        'msg_ai_started': 'Révision IA démarrée...',
        'msg_ai_done': 'Révision IA terminée.',
        'msg_ai_model_set': 'ID du modèle IA : {}',
        'msg_ai_disabled': 'Révision IA non disponible.',
        'warn_lm_url_invalid': 'Aucune adresse de serveur LM valide n’a été saisie.\n'
                               'Veuillez consulter les indications et essayer une autre adresse.',
        'warn_need_done_for_ai': "Veuillez d'abord sélectionner un fichier OCR terminé.",
        'warn_need_ai_model': 'Aucun modèle n’a été trouvé via l’URL du serveur LM configurée. Veuillez démarrer un '
                              'serveur local compatible OpenAI ou définir une URL ou un identifiant de modèle valide '
                              '(par exemple LM Studio, Ollama, Jan, GPT4All, text-generation-webui, LocalAI ou vLLM).',
        'warn_ai_server': 'Le serveur LM local est inaccessible. Veuillez charger le modèle et démarrer le serveur '
                          'compatible OpenAI.',
        'dlg_choose_ai_model': 'Identifiant du modèle LM',
        'dlg_choose_ai_model_label': 'Identifiant de modèle facultatif. Laissez vide pour utiliser automatiquement le '
                                     'modèle du serveur configuré :',
        'log_ai_started': 'Révision IA démarrée : {}',
        'log_ai_done': 'Révision IA terminée : {}',
        'log_ai_error': 'Erreur de révision IA : {} -> {}',
        'status_ai_processing': 'Révision IA...',
        'status_exporting': 'Export en cours...',
        'menu_project_save': 'Enregistrer le projet',
        'menu_project_save_as': 'Enregistrer le projet sous...',
        'menu_project_load': 'Charger un projet...',
        'dlg_filter_project': 'Projet Bottled Kraken (*.json)',
        'msg_project_saved': 'Projet enregistré : {}',
        'msg_project_loaded': 'Projet chargé : {}',
        'warn_project_load_failed': 'Impossible de charger le projet : {}',
        'warn_project_save_failed': 'Impossible d’enregistrer le projet : {}',
        'warn_project_file_missing': 'Fichier introuvable : {}',
        'line_menu_swap_with': 'Échanger la ligne avec…',
        'dlg_swap_title': 'Échanger les lignes',
        'dlg_swap_label': 'Échanger avec le numéro de ligne (1…) :',
        'act_voice_fill': 'Dicter les lignes',
        'act_voice_fill_tip': 'Remplacer les lignes reconnues via le microphone avec faster-whisper',
        'act_voice_stop': 'Arrêter l’enregistrement',
        'msg_voice_started': 'Enregistrement vocal démarré...',
        'msg_voice_stopped': 'Enregistrement terminé. Transcription en cours...',
        'msg_voice_done': 'Import vocal terminé.',
        'msg_voice_cancelled': 'Enregistrement vocal annulé.',
        'warn_voice_need_done': "Veuillez d'abord sélectionner un fichier OCR terminé.",
        'warn_voice_model_missing': 'Le dossier du modèle Faster-Whisper est introuvable.',
        'status_voice_recording': 'Enregistrement...',
        'lines_tree_header': 'Lignes et mots reconnus',
        'col_loaded_files': 'Fichiers chargés',
        'btn_rec_model_empty': 'Modèle de reconnaissance : -',
        'btn_rec_model_value': 'Modèle de reconnaissance : {}',
        'btn_seg_model_empty': 'Modèle de segmentation : -',
        'btn_seg_model_value': 'Modèle de segmentation : {}',
        'act_load_rec_model': 'Charger le modèle de reconnaissance...',
        'act_load_seg_model': 'Charger le modèle de segmentation...',
        'submenu_available_kraken_models': 'Modèles Kraken disponibles',
        'submenu_available_ai_models': 'Modèles LM disponibles',
        'submenu_available_whisper_models': 'Modèles Whisper disponibles',
        'btn_cancel': 'Annuler',
        'progress_status_ready': 'Prêt',
        'voice_record_title': '🎤 Modifier la ligne avec l’audio',
        'voice_record_info': 'Contrôle de l’enregistrement audio :',
        'voice_record_start': 'Démarrer l’enregistrement',
        'voice_record_stop': 'Arrêter l’enregistrement',
        'voice_record_processing': 'Whisper verarbeitet Audio … bitte kurz warten.',
        'warn_select_line_first': 'Veuillez d’abord sélectionner une ligne.',
        'warn_selected_line_invalid': 'La ligne sélectionnée est invalide.',
        'warn_whisper_model_not_loaded': 'Aucun modèle Whisper chargé n’est actif. Veuillez choisir un modèle dans '
                                         "'Options Whisper'.",
        'warn_no_microphone_available': 'Aucun microphone n’est disponible.',
        'log_voice_stopping': 'Arrêt de l’enregistrement vocal...',
        'image_edit_title': 'Édition d’image – {}',
        'image_edit_erase_rect': 'Supprimer une zone (rectangle)',
        'image_edit_erase_ellipse': 'Supprimer une zone (cercle)',
        'image_edit_erase_clear': 'Effacer la zone de suppression',
        'warn_select_image_or_pdf_page': 'Veuillez d’abord sélectionner une image ou une page PDF.',
        'warn_image_load_failed_detail': 'Impossible de charger l’image :\n{}',
        'info_no_marked_images_found': 'Aucune image marquée trouvée.',
        'msg_image_edit_selected_applied': 'Édition d’image appliquée aux images marquées.',
        'msg_image_edit_all_applied': 'Édition d’image appliquée à toutes les images.',
        'log_image_edit_error': 'Erreur d’édition d’image : {} -> {}',
        'act_help': 'Aide',
        'act_ai_revise_all': 'Tout réviser',
        'act_ai_revise_all_tip': 'Réviser tous les fichiers entièrement reconnus',
        'warn_select_multiple_lines_first': 'Veuillez d’abord sélectionner plusieurs lignes.',
        'msg_ai_selected_lines_started': 'Révision LM démarrée pour {} lignes sélectionnées...',
        'log_ai_multi_started': 'Révision LM multi-lignes démarrée : {} | lignes {}',
        'dlg_ai_multi_title': 'Révision IA multi-lignes',
        'dlg_ai_multi_status': 'Révision de {} lignes sélectionnées ...',
        'btn_import_lines': 'Importer des lignes',
        'btn_import_lines_tip': 'Charger les lignes reconnues depuis TXT/JSON',
        'act_import_lines_current': 'Pour l’image actuelle',
        'act_import_lines_selected': 'Pour les images sélectionnées',
        'act_import_lines_all': 'Pour toutes les images',
        'warn_import_unsupported_format': 'Format d’import non pris en charge : {}',
        'warn_import_no_usable_lines': 'Le fichier d’import ne contient aucune ligne exploitable.',
        'info_no_current_image_loaded': 'Aucune image actuelle chargée.',
        'dlg_import_lines_current': 'Importer des lignes',
        'info_no_images_selected_or_marked': 'Aucune image sélectionnée ou marquée.',
        'dlg_import_lines_selected': 'Charger les fichiers de lignes pour les images sélectionnées',
        'info_no_images_loaded': 'Aucune image chargée.',
        'dlg_import_lines_all': 'Charger les fichiers de lignes pour toutes les images',
        'warn_no_matching_import_for_selected': 'Aucun fichier d’import ne correspond aux images sélectionnées.\n'
                                                '\n'
                                                'Les noms de fichiers doivent correspondre par le nom de base.',
        'warn_no_matching_import_for_loaded': 'Aucun fichier d’import ne correspond aux images chargées.\n'
                                              '\n'
                                              'Les noms de fichiers doivent correspondre par le nom de base.',
        'log_import_error': 'Erreur d’import : {} -> {}',
        'log_voice_import_started': 'Sprachimport gestartet: {} | Zeile {} | Mikrofon: {} | Modell: {}',
        'warn_voice_cancelled': 'Aufnahme abgebrochen.',
        'warn_voice_not_finished': 'Aufnahme wurde nicht regulär beendet.',
        'warn_voice_no_audio_data': 'Keine Audiodaten aufgenommen.',
        'voice_status_prepare_wav': 'Audiodatei wird vorbereitet...',
        'voice_status_load_whisper': 'Lade faster-whisper...',
        'voice_status_transcribe_line': 'Transkribiere ausgewählte Zeile lokal ({}/{})...',
        'voice_status_fallback_cpu': 'Initialisierung auf {}/{} fehlgeschlagen. Neuer Versuch mit CPU/int8 …',
        'voice_status_finalize': 'Bereite Text auf...',
        'voice_status_microphone_active': "Mikrofon aktiv … bitte sprechen. Zum Beenden 'Aufnahme stoppen' klicken.",
        'voice_status_input_device': 'Aufnahmegerät: {}',
        'audio_device_default_mic': 'Systemstandard-Mikrofon',
        'audio_device_generic': 'Gerät {}',
        'whisper_status_model': 'Modell: {}',
        'whisper_status_mic': 'Mikrofon: {}',
        'whisper_status_path': 'Pfad: {}',
        'dlg_whisper_model_dir': 'Whisper-Modellordner wählen',
        'msg_whisper_path_set': 'Whisper-Pfad gesetzt: {}',
        'warn_whisper_model_present': 'Das Faster-Whisper large-v3 Modell ist bereits vorhanden.\n'
                                      '\n'
                                      'Pfad:\n'
                                      '{}\n'
                                      '\n'
                                      'Ein erneuter Download ist nicht nötig.',
        'msg_whisper_model_already_present': 'Whisper-Modell bereits vorhanden: {}',
        'warn_whisper_download_start_failed': 'Download des Whisper-Modells konnte nicht gestartet werden:\n{}',
        'msg_whisper_download_start_failed': 'Whisper-Download konnte nicht gestartet werden.',
        'msg_whisper_model_loaded': 'Whisper-Modell geladen: {}',
        'info_whisper_model_downloaded': 'Das Faster-Whisper-Modell wurde erfolgreich heruntergeladen.\n'
                                         '\n'
                                         'Zielordner:\n'
                                         '{}',
        'msg_whisper_download_failed': 'Whisper-Download fehlgeschlagen.',
        'warn_whisper_download_failed': 'Download des Whisper-Modells fehlgeschlagen:\n{}',
        'dlg_help_title': 'Hinweise',
        'help_nav_quick': 'Flux',
        'help_nav_kraken': 'Kraken',
        'help_nav_lm_server': 'Serveur LM',
        'help_nav_ssh': 'Tunnel SSH',
        'help_nav_whisper': 'Whisper',
        'help_nav_shortcuts': 'Raccourcis',
        'help_nav_data_protection': 'Protection des données',
        'help_nav_legal': 'Mentions légales',
        'help_whisper_download_label': '<b>Télécharger le modèle Whisper avec un bouton :</b>',
        'help_os_windows': 'Windows',
        'help_os_arch': 'Arch',
        'help_os_debian': 'Debian',
        'help_os_fedora': 'Fedora',
        'help_os_macos': 'macOS',
        'whisper_hint_debian': 'Remarque pour Debian/Ubuntu/Linux Mint :\n'
                               'L’application utilise ici automatiquement son propre environnement Python (venv) pour '
                               'éviter les erreurs PEP-668 avec le Python système.\n'
                               '\n'
                               'Si la création du venv échoue, des paquets système requis manquent probablement. '
                               'Exécutez :\n'
                               '\n'
                               'sudo apt update\n'
                               'sudo apt install -y python3-venv python3-pip ffmpeg portaudio19-dev',
        'whisper_hint_fedora': 'Remarque facultative pour Fedora :\n'
                               'Si sounddevice pose problème plus tard, ces paquets système peuvent aider.\n'
                               '\n'
                               'sudo dnf install -y python3-pip ffmpeg portaudio-devel',
        'whisper_hint_arch': 'Remarque facultative pour Arch Linux :\n'
                             'Si sounddevice pose problème plus tard, ces paquets système peuvent aider.\n'
                             '\n'
                             'sudo pacman -S --needed python-pip ffmpeg portaudio',
        'whisper_hint_macos': 'Remarque facultative pour macOS :\n'
                              'Si sounddevice pose problème plus tard, ces paquets peuvent aider.\n'
                              '\n'
                              'brew install ffmpeg portaudio',
        'whisper_hint_windows': 'Remarque facultative pour Windows :\n'
                                'Normalement, aucun paquet système supplémentaire n’est nécessaire. Si des problèmes '
                                'audio apparaissent plus tard, ils sont généralement liés aux pilotes ou aux '
                                'autorisations du microphone.',
        'whisper_hint_generic': 'Remarque facultative :\n'
                                'Si sounddevice pose problème plus tard, des paquets système supplémentaires peuvent '
                                'être nécessaires.',
        'whisper_system_hint_dialog': 'Remarque système facultative :\n'
                                      '\n'
                                      '{}\n'
                                      '\n'
                                      'Le téléchargement réel passe malgré tout uniquement par Python (sys.executable '
                                      '-m pip / API Python de huggingface_hub).',
        'warn_whisper_download_running': 'Un téléchargement Whisper est déjà en cours.',
        'msg_whisper_download_prepare_target': 'Démarrage de l’installation des dépendances et du téléchargement du '
                                               'modèle vers : {}',
        'dlg_whisper_download_title': 'Chargement du modèle Whisper',
        'dlg_whisper_download_prepare': 'Démarrage de la préparation de Whisper ...',
        'hf_status_waiting_for_lock': 'En attente du verrou de fichier dans le dossier cible ...',
        'hf_status_files_done': 'Fichiers terminés : {}/{}',
        'hf_status_current_file': 'Actuel : {}',
        'hf_status_last_finished': 'Dernier terminé : {}',
        'hf_status_download_done': 'Téléchargement terminé.',
        'hf_error_cancelled': 'Téléchargement annulé.',
        'hf_error_hf_exit': "'hf download' s’est terminé avec le code {}.",
        'hf_error_command_exit': 'La commande s’est terminée avec le code {} :\n{}',
        'hf_error_python_missing': 'Python ou un module requis n’a pas été trouvé.\n'
                                   '\n'
                                   'Veuillez vérifier que l’application fonctionne avec un environnement Python '
                                   'valide.',
        'hf_error_externally_managed': 'L’installation Python du système ne doit pas être modifiée directement.\n'
                                       '\n'
                                       'L’application devrait utiliser automatiquement son propre environnement. Si ce '
                                       'n’est pas le cas, python3-venv manque probablement.\n'
                                       '\n'
                                       'Veuillez exécuter :\n'
                                       'sudo apt update\n'
                                       'sudo apt install -y python3-venv python3-pip',
        'hf_error_no_venv': 'La prise en charge de Python venv manque sur ce système.\n'
                            '\n'
                            'Veuillez exécuter :\n'
                            'sudo apt update\n'
                            'sudo apt install -y python3-venv python3-pip',
        'hf_error_python3_missing': 'python3 est introuvable.\n\nVeuillez vérifier que Python 3 est installé.',
        'warn_invalid_line': 'Ligne invalide.',
        'btn_ai_model_value': 'KI: {}',
        'llm_status_value': 'LLM: {}',
        'lm_status_model_value': 'Modell: {}',
        'lm_mode_value': 'Modus: {}',
        'lm_server_value': 'Server: {}',
        'dlg_ai_title': 'Révision IA',
        'dlg_ai_connecting': 'Connexion au serveur LM local…',
        'dlg_ai_single_title': 'Révision IA de ligne',
        'dlg_ai_single_status': 'Überarbeite nur Zeile {} …',
        'msg_ai_single_started': 'LM-Überarbeitung für Zeile {} gestartet...',
        'log_ai_single_started': 'LM-Zeilenüberarbeitung gestartet: {} | Zeile {}',
        'msg_ai_multi_done': 'LM-Überarbeitung für {} ausgewählte Zeilen abgeschlossen.',
        'log_ai_multi_done': 'LM-Mehrfachzeilenüberarbeitung abgeschlossen: {} | Zeilen {}',
        'msg_ai_multi_cancelled': 'Mehrfachzeilenüberarbeitung abgebrochen.',
        'log_ai_multi_cancelled': 'LM-Mehrfachzeilenüberarbeitung abgebrochen: {}',
        'msg_ai_multi_failed': 'Mehrfachzeilenüberarbeitung fehlgeschlagen.',
        'log_ai_multi_failed': 'LM-Mehrfachzeilenüberarbeitung Fehler: {} -> {}',
        'msg_ai_batch_finished': 'Lot IA terminé.',
        'log_ai_batch_debug_return': 'KI Batch Rückgabe für {}: {} Zeilen, OCR hatte {} Zeilen',
        'log_ai_batch_debug_old_first': 'ALT erste Zeile: {}',
        'log_ai_batch_debug_new_first': 'NEU erste Zeile: {}',
        'log_ai_batch_debug_all': 'NEU alle Zeilen: {}',
        'msg_ai_cancelled': 'Révision annulée.',
        'ai_status_start_free_ocr': 'Starte freie KI-OCR: {}',
        'ai_status_step1_title': '1/3 Zeilenweise Box-OCR: {}',
        'ai_status_step1_line': '1/3 Box-OCR Zeile {}/{}: {}',
        'ai_status_step2_form': '2/3 Block-Kontext-OCR (Formularmodus): {}',
        'ai_status_step2_plain': '2/3 Block-Kontext-OCR: {}',
        'ai_status_step2_chunk': '2/3 Block-Kontext {}/{}: Zeilen {}-{}',
        'ai_status_step3_merge': '3/3 Merge: Box primär, Page nur wenn lokal konsistent: {}',
        'ai_status_done': 'KI-Überarbeitung abgeschlossen: {}',
        'ai_err_bad_scheme': 'Nicht unterstütztes Schema: {}',
        'ai_err_invalid_endpoint': 'Ungültiger Endpoint.',
        'ai_err_timeout': 'Zeitüberschreitung beim Warten auf LM Server.',
        'ai_err_invalid_json': 'Ungültige JSON-Antwort von LM Server: {}',
        'ai_err_http': 'HTTP-Fehler: {}\n{}',
        'ai_err_server_unreachable': 'LM Server nicht erreichbar: {}',
        'ai_err_no_choices': 'LM Server lieferte keine choices. Antwort:\n{}',
        'ai_err_reasoning_truncated': 'Das Modell hat nur reasoning_content geliefert und wurde vor der eigentlichen '
                                      'JSON-Antwort abgeschnitten (finish_reason=length). Erhöhe max_tokens oder '
                                      'verwende ein nicht-thinkendes Modell.',
        'ai_err_reasoning_only': 'Das Modell hat nur reasoning_content geliefert, aber keinen normalen content. '
                                 'Verwende am besten ein nicht-thinkendes Modell oder erzwinge text/json ohne '
                                 'reasoning.',
        'ai_err_no_content': 'LM Server lieferte keinen verwertbaren Antwortinhalt.',
        'ai_err_page_invalid_json': 'Seiten-OCR lieferte kein gültiges JSON-Objekt.\n\nExtrahierter Content:\n{}',
        'ai_err_page_invalid_lines': "Seiten-OCR lieferte kein gültiges Feld 'lines'.\n\nExtrahierter Content:\n{}",
        'ai_err_page_long_blocks': 'Seiten-OCR hat vermutlich mehrere Zielzeilen zu langen Blöcken zusammengezogen.',
        'ai_err_page_no_usable_lines': 'Seiten-OCR lieferte keine verwertbaren Zeilen: {}/{}',
        'ai_err_block_invalid_json': 'Block-OCR lieferte kein gültiges JSON-Objekt.\n\nExtrahierter Content:\n{}',
        'ai_err_block_invalid_lines': "Block-OCR lieferte kein gültiges Feld 'lines'.\n\nExtrahierter Content:\n{}",
        'ai_err_final_merge_count': 'Finale Merge-Ausgabe gab {} statt {} Zeilen zurück.',
        'help_html_quick': '\n'
                           '    <div class="card warn">\n'
                           '        <div class="h1">Déroulement</div>\n'
                           '    </div>\n'
                           '\n'
                           '    <div class="card">\n'
                           '        <ol>\n'
                           '            <li>Charger une image ou un PDF</li>\n'
                           '            <li>Optionnel : utiliser l’édition d’image comme préparation</li>\n'
                           '            <li>Charger le modèle de reconnaissance</li>\n'
                           '            <li>Charger le modèle de segmentation</li>\n'
                           '            <li>Démarrer Kraken OCR</li>\n'
                           '            <li>Vérifier les lignes détectées et les corriger si nécessaire</li>\n'
                           '            <li>Optionnel : utiliser la révision LM ou Whisper</li>\n'
                           '            <li>Exporter le résultat en TXT, CSV, JSON, ALTO, hOCR ou PDF</li>\n'
                           '        </ol>\n'
                           '    </div>\n'
                           '\n'
                           '    <div class="card">\n'
                           '        <div class="h2">Préparation</div>\n'
                           '        <span class="badge">Optionnel</span>\n'
                           '        <ul>\n'
                           '            <li>L’édition d’image peut déjà être utilisée <b>avant</b> l’OCR lorsqu’un '
                           'scan est mal recadré, trop peu contrasté ou contient trop d’éléments autour du contenu '
                           'utile.</li>\n'
                           '            <li>Les outils les plus utiles ici sont la <b>zone de recadrage</b>, la '
                           '<b>barre de séparation</b>, le mode <b>gris</b>, le <b>contraste</b> et le <b>smart '
                           'splitting</b>.</li>\n'
                           '            <li>Cela permet de préparer précisément des doubles pages, des moitiés de '
                           'formulaires, des marges ou du contenu voisin gênant avant le passage OCR proprement '
                           'dit.</li>\n'
                           '            <li>C’est particulièrement utile pour les dossiers, les formulaires, les scans '
                           'groupés et les fonds d’archives mal numérisés.</li>\n'
                           '        </ul>\n'
                           '    </div>\n'
                           '\n'
                           '    <div class="card">\n'
                           '        <div class="h2">Post-traitement</div>\n'
                           '        <span class="badge">Optionnel</span>\n'
                           '        <ul>\n'
                           '            <li>Charger un modèle LM via LM Studio ou un autre serveur LM compatible</li>\n'
                           '            <li>Lisser les lignes OCR sur le plan linguistique ou sémantique avec un '
                           'modèle de langage local</li>\n'
                           '            <li>Réenregistrer des lignes individuelles au microphone avec '
                           'Faster-Whisper</li>\n'
                           '            <li>Importer des lignes depuis TXT ou JSON</li>\n'
                           '        </ul>\n'
                           '    </div>\n'
                           '\n'
                           '    <div class="card">\n'
                           '        <div class="h2">Boîtes d’overlay &amp; lignes</div>\n'
                           '        <span class="badge">Optionnel</span>\n'
                           '        <ul>\n'
                           '            <li>Les lignes et les boîtes d’overlay peuvent être déplacées, divisées, '
                           'ajoutées ou supprimées.</li>\n'
                           '            <li>Cela permet d’améliorer de manière ciblée la structure des lignes avant un '
                           'nouveau passage OCR.</li>\n'
                           '            <li>Particulièrement utile pour les formulaires, les mises en page en colonnes '
                           'et les écritures manuscrites mal segmentées.</li>\n'
                           '        </ul>\n'
                           '    </div>\n'
                           '\n'
                           '    <div class="card">\n'
                           '        <div class="h2">Que fait Bottled Kraken&nbsp;?</div><br>\n'
                           '        Bottled Kraken combine l’OCR classique avec une préparation par édition d’image, '
                           'un post-traitement manuel et une assistance IA locale optionnelle.\n'
                           '        Cela permet d’améliorer pas à pas des imprimés historiques difficiles, des '
                           'manuscrits ou des pages de formulaires.\n'
                           '    </div>\n',
        'help_html_kraken': '\n'
                            '    <div class="card">\n'
                            '        <div class="h1">Kraken</div><br>\n'
                            '        Kraken est la base OCR/ATR de Bottled Kraken.\n'
                            '        Il s’agit d’un système open source de reconnaissance automatique de texte,\n'
                            '        développé spécialement pour les imprimés historiques, les manuscrits et les '
                            'écritures non latines.\n'
                            '    </div>\n'
                            '\n'
                            '    <div class="card">\n'
                            '        <div class="h2">Qu’est-ce qui est important pour Bottled Kraken ?</div>\n'
                            '        <ul>\n'
                            '            <li><b>Segmentation :</b> détecte la mise en page, les zones de texte, les '
                            'lignes et l’ordre de lecture.</li>\n'
                            '            <li><b>Reconnaissance :</b> lit le texte proprement dit à partir des lignes '
                            'détectées.</li>\n'
                            '            <li><b>Modèles :</b> la segmentation et la reconnaissance fonctionnent avec '
                            'des modèles entraînés qui doivent correspondre au type de document.</li>\n'
                            '        </ul>\n'
                            '    </div>\n'
                            '\n'
                            '    <div class="card">\n'
                            '        <div class="h2">Flux de travail typique avec Kraken</div>\n'
                            '        <ol>\n'
                            '            <li>Préparer l’image</li>\n'
                            '            <li>Segmenter la page (<code>segment</code>)</li>\n'
                            '            <li>Reconnaître le texte (<code>ocr</code>)</li>\n'
                            '            <li>Structurer / exporter le résultat</li>\n'
                            '        </ol>\n'
                            '        Dans Bottled Kraken, ces étapes sont reprises directement dans l’interface :\n'
                            '        d’abord le modèle de segmentation, puis le modèle de reconnaissance, ensuite '
                            'l’OCR et l’export.\n'
                            '    </div>\n'
                            '\n'
                            '    <div class="card">\n'
                            '        <div class="h2">Principaux points forts de Kraken</div>\n'
                            '        <ul>\n'
                            '            <li>analyse de mise en page, ordre de lecture et reconnaissance des '
                            'caractères entraînables</li>\n'
                            '            <li>prise en charge de l’écriture de droite à gauche, BiDi et de haut en '
                            'bas</li>\n'
                            '            <li>sortie en ALTO, PageXML, abbyyXML et hOCR</li>\n'
                            '            <li>boîtes englobantes des mots et découpes des caractères</li>\n'
                            '            <li>collection publique de modèles via HTRMoPo / Zenodo</li>\n'
                            '        </ul>\n'
                            '    </div>\n'
                            '\n'
                            '            <div class="card">\n'
                            '                <div class="h2">Modèles</div><br>\n'
                            '                Kraken fonctionne avec des modèles.\n'
                            '                La qualité du résultat dépend fortement de l’adéquation du modèle au type de document.\n'
                            '                Un modèle entraîné sur des imprimés historiques est généralement bien meilleur pour ce type de documents\n'
                            '                qu’un modèle généraliste pour des documents modernes.\n'
                            '                <br><br>\n'
                            '                <b>Remarque :</b> Les modèles Kraken téléchargés doivent se trouver dans le même dossier / répertoire\n'
                            '                que le fichier EXE afin que Bottled Kraken puisse les trouver automatiquement.\n'
                            '            </div>\n'
                            '\n'
                            '    <div class="card">\n'
                            '        <div class="h2">Interfaces</div><br>\n'
                            '        Kraken propose deux approches principales :\n'
                            '        <ul>\n'
                            '            <li><b>CLI :</b> pour les flux de travail OCR classiques</li>\n'
                            '            <li><b>API Python :</b> pour les applications personnalisées et les '
                            'intégrations</li>\n'
                            '        </ul>\n'
                            '        Bottled Kraken utilise directement la bibliothèque Python dans le code du '
                            'programme.\n'
                            '    </div>\n'
                            '\n'
                            '    <div class="card">\n'
                            '        <div class="h2">Sources officielles</div>\n'
                            '        <ul>\n'
                            '            <li><a href="https://github.com/mittagessen/kraken">GitHub : '
                            'mittagessen/kraken</a></li>\n'
                            '            <li><a href="https://kraken.re/7.0/index.html">Documentation Kraken '
                            '7.0</a></li>\n'
                            '            <li><a href="https://kraken.re/7.0/getting_started.html">Prise en '
                            'main</a></li>\n'
                            '            <li><a href="https://kraken.re/7.0/user_guide/models.html">Gestion des '
                            'modèles</a></li>\n'
                            '        </ul>\n'
                            '    </div>\n'
                            '\n'
                            '    <div class="card warn">\n'
                            '        <div class="h2">Remarque</div>\n'
                            '        <span class="badge">Important</span><br>\n'
                            '        Si la segmentation n’est pas propre, la reconnaissance sera également moins '
                            'bonne.\n'
                            '        C’est précisément pour cela que Bottled Kraken utilise par défaut '
                            '<code>blla.mlmodell</code>\n'
                            '        au lieu de l’ancien modèle de segmentation <code>pageseg</code>.\n'
                            '    </div>\n',
        'help_html_lm_server': '\n'
                               '    <div class="card">\n'
                               '        <div class="h1">Serveur LM / serveurs de modèles locaux</div><br>\n'
                               '        Cette section est destinée au <b>post-traitement local par modèle de '
                               'langage</b>.\n'
                               '        Pour cela, Bottled Kraken attend une <b>URL de base compatible OpenAI</b>, '
                               'généralement avec <code>/v1</code>.\n'
                               '    </div>\n'
                               '\n'
                               '    <div class="card">\n'
                               '        <div class="h2">URLs de base directement adaptées à Bottled Kraken</div>\n'
                               '        <pre>LM Studio:              http://localhost:1234/v1\n'
                               'Ollama:                 http://localhost:11434/v1\n'
                               'GPT4All:                http://localhost:4891/v1\n'
                               'text-generation-webui:  http://127.0.0.1:5000/v1\n'
                               'LocalAI:                http://localhost:8080/v1</pre>\n'
                               '        <div class="muted">\n'
                               '            Important : avec Ollama, il faut saisir dans Bottled Kraken l’URL '
                               '<b>compatible OpenAI</b> en <code>/v1</code>, et non la route brute '
                               '<code>/api</code>.\n'
                               '        </div>\n'
                               '    </div>\n'
                               '\n'
                               '    <div class="card">\n'
                               '        <div class="h2">LM Studio</div>\n'
                               '        <ul>\n'
                               '            <li>Pour beaucoup d’utilisateurs, c’est l’option la plus simple si l’on '
                               'veut une application de bureau avec gestion des modèles et serveur local.</li>\n'
                               '            <li>LM Studio expose les modèles locaux via REST ainsi que via des points '
                               'd’accès compatibles OpenAI et Anthropic.</li>\n'
                               '            <li>Le cas standard dans Bottled Kraken est '
                               '<code>http://localhost:1234/v1</code>.</li>\n'
                               '        </ul>\n'
                               '    </div>\n'
                               '\n'
                               '    <div class="card">\n'
                               '        <div class="h2">Ollama</div>\n'
                               '        <ul>\n'
                               '            <li>Souvent le choix le plus propre si l’on veut surtout un service local '
                               'et un flux de travail léger en CLI / daemon.</li>\n'
                               '            <li>Ollama démarre localement sur <code>http://localhost:11434</code>, '
                               'propose sa propre interface <code>/api</code> et fournit aussi une compatibilité '
                               'OpenAI sous <code>/v1</code>.</li>\n'
                               '            <li>Il prend également en charge une utilisation compatible Anthropic pour '
                               'des workflows comme Claude Code.</li>\n'
                               '            <li>Pour Bottled Kraken, le meilleur choix est en général '
                               '<code>http://localhost:11434/v1</code>.</li>\n'
                               '        </ul>\n'
                               '    </div>\n'
                               '\n'
                               '    <div class="card">\n'
                               '        <div class="h2">Jan</div>\n'
                               '        <ul>\n'
                               '            <li>Par sa logique d’utilisation, Jan est souvent l’alternative la plus '
                               'proche de LM Studio : application desktop, modèles locaux, serveur API compatible '
                               'OpenAI intégré.</li>\n'
                               '            <li>Par défaut, Jan écoute sur <code>http://127.0.0.1:1337</code> avec le '
                               'préfixe API <code>/v1</code> ; l’hôte par défaut <code>127.0.0.1</code> est '
                               'volontairement limité à la machine locale.</li>\n'
                               '            <li>Jan impose aussi par défaut une clé API. En pratique, Jan est donc '
                               'surtout utile avec Bottled Kraken si l’on adapte le comportement d’en-tête attendu ou '
                               'si l’on place un petit proxy local entre les deux.</li>\n'
                               '        </ul>\n'
                               '    </div>\n'
                               '\n'
                               '    <div class="card">\n'
                               '        <div class="h2">GPT4All</div>\n'
                               '        <ul>\n'
                               '            <li>Très proche de l’idée «&nbsp;on lance localement et on '
                               'utilise&nbsp;».</li>\n'
                               '            <li>Son serveur API local tourne par défaut sur '
                               '<code>http://localhost:4891/v1</code>, est compatible OpenAI et n’écoute que sur '
                               '<code>localhost</code>.</li>\n'
                               '            <li>En plus, GPT4All propose <b>LocalDocs</b> pour un flux simple de '
                               'documents locaux / RAG local.</li>\n'
                               '            <li>Pour Bottled Kraken, c’est généralement l’une des alternatives les '
                               'plus simples à LM Studio.</li>\n'
                               '        </ul>\n'
                               '    </div>\n'
                               '\n'
                               '    <div class="card">\n'
                               '        <div class="h2">text-generation-webui (oobabooga)</div>\n'
                               '        <ul>\n'
                               '            <li>Particulièrement intéressant pour les personnes qui aiment tout régler '
                               'elles-mêmes, changer de backend et contrôler de nombreux paramètres.</li>\n'
                               '            <li>Le projet prend en charge plusieurs backends comme '
                               '<code>llama.cpp</code>, <code>Transformers</code>, <code>ExLlamaV3</code> et '
                               '<code>TensorRT-LLM</code>.</li>\n'
                               '            <li>Son API compatible OpenAI / Anthropic peut servir de remplacement '
                               'direct ; par défaut elle utilise généralement le port <code>5000</code>.</li>\n'
                               '            <li>On y trouve aussi le tool calling, la vision et les pièces jointes de '
                               'fichiers.</li>\n'
                               '        </ul>\n'
                               '    </div>\n'
                               '\n'
                               '    <div class="card">\n'
                               '        <div class="h2">LocalAI</div>\n'
                               '        <ul>\n'
                               '            <li>Très adapté si l’on pense davantage en termes de serveur IA local '
                               'auto-hébergé qu’en application de bureau classique.</li>\n'
                               '            <li>LocalAI expose une API compatible OpenAI ; dans Bottled Kraken, la '
                               'configuration typique est <code>http://localhost:8080/v1</code>.</li>\n'
                               '            <li>Il prend aussi en charge d’autres formats d’API compatibles, une '
                               'interface web et des fonctions d’agents / MCP.</li>\n'
                               '            <li>C’est un bon choix si l’on veut regrouper plusieurs services locaux ou '
                               'construire une petite pile IA interne.</li>\n'
                               '        </ul>\n'
                               '    </div>\n'
                               '\n'
                               '    <div class="card">\n'
                               '        <div class="h2">Guide pratique de choix</div>\n'
                               '        <ul>\n'
                               '            <li><b>LM Studio :</b> si vous voulez une interface graphique, du serving '
                               'local et peu de friction</li>\n'
                               '            <li><b>Ollama :</b> si vous préférez un service local propre ou un '
                               'workflow CLI</li>\n'
                               '            <li><b>Jan :</b> si vous voulez une ergonomie proche de LM Studio et '
                               'pouvez vivre avec une clé API / un proxy</li>\n'
                               '            <li><b>GPT4All :</b> si vous voulez une solution desktop simple avec '
                               'LocalDocs</li>\n'
                               '            <li><b>text-generation-webui :</b> si vous voulez un contrôle fin des '
                               'backends, de la vision et des outils</li>\n'
                               '            <li><b>LocalAI :</b> si vous voulez un serveur local plus auto-hébergé '
                               'avec une orientation API / agents plus large</li>\n'
                               '        </ul>\n'
                               '    </div>\n'
                               '\n'
                               '    <div class="card">\n'
                               '        <div class="h2">Sources officielles</div>\n'
                               '        <ul>\n'
                               '            <li><a href="https://lmstudio.ai/docs/developer/core/server">LM Studio '
                               'Docs – Local LLM API Server</a></li>\n'
                               '            <li><a href="https://lmstudio.ai/docs/developer/openai-compat">LM Studio '
                               'Docs – OpenAI Compatibility</a></li>\n'
                               '            <li><a href="https://docs.ollama.com/api/openai-compatibility">Ollama Docs '
                               '– OpenAI compatibility</a></li>\n'
                               '            <li><a href="https://docs.ollama.com/integrations/claude-code">Ollama Docs '
                               '– Claude Code / API compatible Anthropic</a></li>\n'
                               '            <li><a href="https://www.jan.ai/docs/desktop/api-server">Jan Docs – Local '
                               'API Server</a></li>\n'
                               '            <li><a href="https://docs.gpt4all.io/gpt4all_api_server/home.html">GPT4All '
                               'Docs – API Server</a></li>\n'
                               '            <li><a '
                               'href="https://github.com/oobabooga/text-generation-webui">text-generation-webui – '
                               'Dépôt</a></li>\n'
                               '            <li><a '
                               'href="https://github.com/oobabooga/text-generation-webui/wiki/12-%E2%80%90-OpenAI-API">text-generation-webui '
                               '– Wiki API OpenAI / Anthropic</a></li>\n'
                               '            <li><a href="https://localai.io/docs/overview/">LocalAI Docs – '
                               'Overview</a></li>\n'
                               '            <li><a href="https://localai.io/basics/getting_started/">LocalAI Docs – '
                               'Quickstart</a></li>\n'
                               '        </ul>\n'
                               '    </div>\n',
        'help_html_ssh': '\n'
                         '    <div class="card">\n'
                         '        <div class="h1">Accès distant via tunnel SSH</div><br>\n'
                         '        Un tunnel SSH est utile lorsque ton serveur LM tourne sur une autre machine,\n'
                         '        mais y est uniquement lié à <code>127.0.0.1</code> et n’est donc pas directement '
                         'accessible sur le réseau.\n'
                         '    </div>\n'
                         '\n'
                         '    <div class="card">\n'
                         '        <div class="h2">Que se passe-t-il alors ?</div><br>\n'
                         '        Le tunnel redirige un port local de ton ordinateur vers un port de la machine '
                         'distante.\n'
                         '        Pour Bottled Kraken, cela donne alors l’impression que le serveur LM fonctionne '
                         'localement sur ton propre ordinateur.\n'
                         '    </div>\n'
                         '\n'
                            '            <div class="card">\n'
                            '                <div class="h2">Exemple</div><br>\n'
                            '                <b>Sur la machine A</b><br>\n'
                            '                Démarrer LM Studio<br>\n'
                            '                Trouver l’adresse IP de la machine A, par exemple avec :\n'
                            '                <pre>ipconfig\n'
                            'hostname -I</pre>\n'
                            '                Supposons que l’adresse IP soit :\n'
                            '                <pre>192.168.1.50</pre>\n'
                            '                <b>Sur la machine B</b><br>\n'
                            '                Ouvrir le tunnel SSH :\n'
                            '                <pre>ssh -N -L 1234:127.0.0.1:1234 user@192.168.1.50</pre>\n'
                            '                <b>À utiliser sur la machine B</b><br>\n'
                            '                Test dans le terminal :\n'
                            '                <pre>curl http://127.0.0.1:1234/v1/models</pre>\n'
                            '                Saisir ceci dans Bottled Kraken :\n'
                            '                <pre>http://127.0.0.1:1234/v1</pre>\n'
                            '            </div>\n'
                         '\n'
                            '    <div class="card">\n'
                            '        <div class="h2">Déroulement typique</div>\n'
                            '        <ol>\n'
                            '            <li>Démarrer LM Studio sur la machine A</li>\n'
                            '            <li>Trouver l’adresse IP de la machine A</li>\n'
                            '            <li>Ouvrir le tunnel SSH sur la machine B avec cette adresse IP</li>\n'
                            '            <li>Tester sur la machine B si <code>http://127.0.0.1:1234/v1/models</code> est accessible</li>\n'
                            '            <li>Saisir <code>http://127.0.0.1:1234/v1</code> dans Bottled Kraken</li>\n'
                            '        </ol>\n'
                            '    </div>\n'
                         '\n'
                         '    <div class="card warn">\n'
                         '        <div class="h2">Important</div>\n'
                         '        <ul>\n'
                         '            <li>Dans Bottled Kraken, tu ne saisis <b>pas</b> la commande SSH.</li>\n'
                         '            <li>Tu saisis toujours l’URL HTTP résultante, par exemple '
                         '<code>http://127.0.0.1:1234/v1</code>.</li>\n'
                         '            <li>Le tunnel SSH doit rester ouvert tant que Bottled Kraken doit utiliser le '
                         'serveur.</li>\n'
                         '        </ul>\n'
                         '    </div>\n',
        'help_html_whisper_intro': '\n'
                                   '    <div class="card">\n'
                                   '        <div class="h1">Faster-Whisper</div>\n'
                                   '        <p>\n'
                                   '            Faster-Whisper est une reconnaissance vocale locale rapide.\n'
                                   '            Dans Bottled Kraken, tu peux l’utiliser pour réenregistrer des lignes '
                                   'OCR individuelles via le microphone\n'
                                   '            et les reprendre directement comme texte.\n'
                                   '        </p>\n'
                                   '    </div>\n'
                                   '\n'
                                   '    <div class="card">\n'
                                   '        <div class="h2">À quoi cela sert-il ?</div>\n'
                                   '        <ul>\n'
                                   '            <li>lorsqu’une ligne OCR est fortement endommagée ou a été mal '
                                   'reconnue</li>\n'
                                   '            <li>lorsque tu peux dicter certains champs ou noms plus rapidement que '
                                   'les taper</li>\n'
                                   '            <li>lorsque tu veux effectuer des corrections ciblées ligne par '
                                   'ligne</li>\n'
                                   '        </ul>\n'
                                   '    </div>\n'
                                   '\n'
                                   '    <div class="card">\n'
                                   '        <div class="h2">Qu’est-ce qui est téléchargé ?</div>\n'
                                   '        <p>\n'
                                   '            Le modèle <span class="badge">Systran/faster-whisper-large-v3</span> '
                                   'est chargé.\n'
                                   '        </p>\n'
                                   '        <p class="muted">\n'
                                   '            Avant le téléchargement, Bottled Kraken installe automatiquement les '
                                   'paquets Python nécessaires.\n'
                                   '            Le téléchargement proprement dit du modèle s’effectue via la CLI '
                                   'Hugging Face avec <code>hf download</code>.\n'
                                   '            Sous Linux et macOS, un environnement venv séparé est automatiquement '
                                   'utilisé pour cela.\n'
                                   '        </p>\n'
                                   '    </div>\n'
                                   '\n'
                                   '    <div class="card">\n'
                                   '        <div class="h2">Déroulement dans Bottled Kraken</div>\n'
                                   '        <ol>\n'
                                   '            <li>Télécharger le modèle Whisper ou rechercher un modèle '
                                   'existant</li>\n'
                                   '            <li>Sélectionner un microphone</li>\n'
                                   '            <li>Marquer une ligne</li>\n'
                                   '            <li>Démarrer l’enregistrement audio</li>\n'
                                   '            <li>La saisie vocale est transcrite localement et remplace la '
                                   'ligne</li>\n'
                                   '        </ol>\n'
                                   '    </div>\n',
        'help_html_shortcuts': '\n'
                       '    <div class="card">\n'
                       '        <div class="h1">Raccourcis clavier</div>\n'
                       '        <table class="table">\n'
                       '            <tr><td class="section" colspan="2">Projet</td></tr>\n'
                       '            <tr><td><span class="kbd">Ctrl + S</span></td><td>Enregistrer le projet</td></tr>\n'
                       '            <tr><td><span class="kbd">Ctrl + Maj + S</span></td><td>Enregistrer le projet sous</td></tr>\n'
                       '            <tr><td><span class="kbd">Ctrl + I</span></td><td>Charger un projet</td></tr>\n'
                       '            <tr><td><span class="kbd">Ctrl + E</span></td><td>Exporter</td></tr>\n'
                       '            <tr><td><span class="kbd">Ctrl + Q</span></td><td>Quitter le programme</td></tr>\n'
                       '\n'
                       '            <tr><td class="section" colspan="2">OCR &amp; LM</td></tr>\n'
                       '            <tr><td><span class="kbd">Ctrl + K</span></td><td>Démarrer l’OCR Kraken</td></tr>\n'
                       '            <tr><td><span class="kbd">Ctrl + P</span></td><td>Arrêter l’OCR Kraken</td></tr>\n'
                       '            <tr><td><span class="kbd">Ctrl + L</span></td><td>Démarrer la révision LM</td></tr>\n'
                       '            <tr><td><span class="kbd">Ctrl + M</span></td><td>Démarrer Faster-Whisper / microphone</td></tr>\n'
                       '\n'
                       '            <tr><td class="section" colspan="2">Sélection</td></tr>\n'
                       '            <tr><td><span class="kbd">Ctrl + A</span></td><td>Tout sélectionner dans le contexte actuel</td></tr>\n'
                       '            <tr><td><span class="kbd">Suppr</span></td><td>Supprimer les lignes ou boîtes sélectionnées</td></tr>\n'
                       '\n'
                       '            <tr><td class="section" colspan="2">Touches de fonction</td></tr>\n'
                       '            <tr><td><span class="kbd">F1</span></td><td>Aide des raccourcis</td></tr>\n'
                       '            <tr><td><span class="kbd">F2</span></td><td>Charger le modèle de reconnaissance</td></tr>\n'
                       '            <tr><td><span class="kbd">F3</span></td><td>Charger le modèle de segmentation</td></tr>\n'
                       '            <tr><td><span class="kbd">F4</span></td><td>Saisir l’URL du serveur LM</td></tr>\n'
                       '            <tr><td><span class="kbd">F5</span></td><td>Lancer la détection LM</td></tr>\n'
                       '            <tr><td><span class="kbd">F6</span></td><td>Scanner les modèles Whisper + définir le premier microphone</td></tr>\n'
                       '            <tr><td><span class="kbd">F7</span></td><td>Afficher / masquer la fenêtre de log</td></tr>\n'
                       '        </table>\n'
                       '    </div>\n',
        'help_html_data_protection': '\n'
                                     '    <div class="card warn">\n'
                                     '        <div class="h1">Protection des données</div><br>\n'
                                     '        Les remarques suivantes résument le <b>mode de fonctionnement local '
                                     'standard</b>.\n'
                                     '        Elles ne remplacent pas une analyse au cas par cas.\n'
                                     '    </div>\n'
                                     '\n'
                                     '    <div class="card">\n'
                                     '        <div class="h2">Règle générale</div>\n'
                                     '        <ul>\n'
                                     '            <li>Les modèles locaux et les serveurs locaux sont en principe plus '
                                     'favorables à la protection des données, car les invites, documents et fichiers '
                                     'audio ne sont pas envoyés automatiquement à un service cloud.</li>\n'
                                     '            <li>Cela n’est vrai que tant que le logiciel est réellement utilisé '
                                     '<b>en local</b>, sans routage cloud ni exposition réseau.</li>\n'
                                     '            <li>Dès qu’il y a exposition sur le réseau, tunnel, reverse proxy, '
                                     'instance distante ou modèle cloud, la situation change.</li>\n'
                                     '        </ul>\n'
                                     '    </div>\n'
                                     '\n'
                                     '    <div class="card">\n'
                                     '        <div class="h2">LM Studio</div>\n'
                                     '        <ul>\n'
                                     '            <li>D’après la documentation officielle, LM Studio peut fonctionner '
                                     'entièrement hors ligne ; le chat local, le chat avec documents et le serveur '
                                     'local n’ont alors pas besoin d’internet.</li>\n'
                                     '            <li>La politique de confidentialité indique aussi explicitement que '
                                     'les messages, historiques de chat et documents ne sont pas transmis hors du '
                                     'système par défaut.</li>\n'
                                     '            <li>Cela vaut pour l’usage local. Si l’on active un accès réseau ou '
                                     'des fonctions distantes, il faut vérifier où partent les données.</li>\n'
                                     '        </ul>\n'
                                     '    </div>\n'
                                     '\n'
                                     '    <div class="card">\n'
                                     '        <div class="h2">Ollama</div>\n'
                                     '        <ul>\n'
                                     '            <li>Ollama fonctionne localement par défaut sur '
                                     '<code>http://localhost:11434</code> ; aucune authentification n’est requise pour '
                                     'l’usage purement local de l’API.</li>\n'
                                     '            <li>Un déploiement limité à <code>localhost</code> reste donc sur '
                                     'votre propre machine.</li>\n'
                                     '            <li>Important : Ollama prend aussi en charge des <b>modèles '
                                     'cloud</b>. Dès qu’ils sont utilisés, le flux de travail n’est plus purement '
                                     'local.</li>\n'
                                     '        </ul>\n'
                                     '    </div>\n'
                                     '\n'
                                     '    <div class="card">\n'
                                     '        <div class="h2">Jan</div>\n'
                                     '        <ul>\n'
                                     '            <li>Jan se présente comme privacy-first et stocke les données '
                                     'localement dans son propre dossier de données.</li>\n'
                                     '            <li>Son API locale est limitée par défaut à <code>127.0.0.1</code>, '
                                     'ce qui constitue la configuration la plus sûre pour un usage individuel.</li>\n'
                                     '            <li>Jan propose aussi des réglages d’analyse / suivi et des journaux '
                                     'serveur détaillés. Avant un usage en production, il est donc utile de vérifier '
                                     'consciemment ce qui est journalisé localement et si un accès réseau a été '
                                     'activé.</li>\n'
                                     '        </ul>\n'
                                     '    </div>\n'
                                     '\n'
                                     '    <div class="card">\n'
                                     '        <div class="h2">GPT4All</div>\n'
                                     '        <ul>\n'
                                     '            <li>GPT4All met en avant l’exécution locale sur votre propre '
                                     'matériel.</li>\n'
                                     '            <li>Son serveur API n’écoute par défaut que sur '
                                     '<code>localhost</code>, et non depuis d’autres appareils du réseau.</li>\n'
                                     '            <li>Avec <b>LocalDocs</b>, des documents locaux peuvent être '
                                     'intégrés au flux de travail ; même dans ce cas, l’emplacement de stockage et le '
                                     'contrôle d’accès à l’appareil restent importants.</li>\n'
                                     '        </ul>\n'
                                     '    </div>\n'
                                     '\n'
                                     '    <div class="card">\n'
                                     '        <div class="h2">text-generation-webui &amp; LocalAI</div>\n'
                                     '        <ul>\n'
                                     '            <li><b>text-generation-webui</b> décrit son API compatible OpenAI / '
                                     'Anthropic comme 100&nbsp;% hors ligne et privée, et précise aussi ne pas créer '
                                     'de logs.</li>\n'
                                     '            <li><b>LocalAI</b> se présente comme une pile locale compatible '
                                     'OpenAI et affirme garder les données privées et sécurisées.</li>\n'
                                     '            <li>Pour les deux projets, la règle pratique reste la même : dès que '
                                     'l’API est exposée sur le réseau, placée derrière un reverse proxy ou ouverte à '
                                     'plusieurs utilisateurs, il faut sécuriser soi-même les accès, les logs, les '
                                     'sauvegardes et les droits d’administration.</li>\n'
                                     '        </ul>\n'
                                     '    </div>\n'
                                     '\n'
                                     '    <div class="card">\n'
                                     '        <div class="h2">faster-whisper</div><br>\n'
                                     '        faster-whisper est une implémentation locale de Whisper basée sur '
                                     'CTranslate2.\n'
                                     '        Dans Bottled Kraken, un dossier de modèle local est chargé et un fichier '
                                     'WAV local est transcrit.\n'
                                     '        Tant que ce flux reste local, le traitement audio reste lui aussi '
                                     'local.\n'
                                     '    </div>\n'
                                     '\n'
                                     '    <div class="card warn">\n'
                                     '        <div class="h2">Limitations importantes</div>\n'
                                     '        <ul>\n'
                                     '            <li>Le téléchargement initial des modèles nécessite naturellement un '
                                     'accès à Internet.</li>\n'
                                     '            <li>Même un serveur «&nbsp;local&nbsp;» peut exposer des données '
                                     'personnelles si l’appareil lui-même n’est pas suffisamment sécurisé.</li>\n'
                                     '            <li>Pour les administrations, archives, entreprises ou organismes de '
                                     'recherche, les seules propriétés d’un outil ne suffisent pas ; il faut aussi '
                                     'prendre en compte l’emplacement de stockage, les rôles, les logs, les '
                                     'sauvegardes, les règles de suppression et les politiques internes.</li>\n'
                                     '            <li>Une licence logicielle ou une politique de confidentialité ne '
                                     'remplace pas une analyse RGPD, contractuelle ou opérationnelle adaptée au '
                                     'déploiement réel.</li>\n'
                                     '        </ul>\n'
                                     '    </div>\n'
                                     '\n'
                                     '    <div class="card">\n'
                                     '        <div class="h2">Sources officielles</div>\n'
                                     '        <ul>\n'
                                     '            <li><a href="https://lmstudio.ai/docs/app/offline">LM Studio Docs – '
                                     'Offline Operation</a></li>\n'
                                     '            <li><a href="https://lmstudio.ai/privacy">LM Studio Desktop App '
                                     'Privacy Policy</a></li>\n'
                                     '            <li><a href="https://docs.ollama.com/api/authentication">Ollama Docs '
                                     '– Authentication</a></li>\n'
                                     '            <li><a href="https://docs.ollama.com/cloud">Ollama Docs – '
                                     'Cloud</a></li>\n'
                                     '            <li><a href="https://ollama.com/privacy">Ollama – Privacy '
                                     'Policy</a></li>\n'
                                     '            <li><a href="https://www.jan.ai/docs/desktop/privacy">Jan Docs – '
                                     'Privacy</a></li>\n'
                                     '            <li><a href="https://www.jan.ai/docs/desktop/data-folder">Jan Docs – '
                                     'Data Folder</a></li>\n'
                                     '            <li><a href="https://www.jan.ai/docs/desktop/api-server">Jan Docs – '
                                     'Local API Server</a></li>\n'
                                     '            <li><a '
                                     'href="https://docs.gpt4all.io/gpt4all_api_server/home.html">GPT4All Docs – API '
                                     'Server</a></li>\n'
                                     '            <li><a href="https://github.com/nomic-ai/gpt4all">GPT4All – '
                                     'Dépôt</a></li>\n'
                                     '            <li><a '
                                     'href="https://github.com/oobabooga/text-generation-webui/wiki/12-%E2%80%90-OpenAI-API">text-generation-webui '
                                     '– Wiki API OpenAI / Anthropic</a></li>\n'
                                     '            <li><a href="https://localai.io/docs/overview/">LocalAI Docs – '
                                     'Overview</a></li>\n'
                                     '            <li><a href="https://github.com/SYSTRAN/faster-whisper">SYSTRAN / '
                                     'faster-whisper</a></li>\n'
                                     '            <li><a '
                                     'href="https://github.com/opennmt/ctranslate2">CTranslate2</a></li>\n'
                                     '        </ul>\n'
                                     '    </div>\n',
        'help_html_legal': '\n'
                           '    <div class="card warn">\n'
                           '        <div class="h1">Mentions légales</div><br>\n'
                           '        Les remarques suivantes constituent une orientation générale et ne remplacent pas '
                           'un conseil juridique.\n'
                           '        Pour tout cas d’usage concret, la situation juridique doit être examinée '
                           'individuellement.\n'
                           '    </div>\n'
                           '\n'
                           '    <div class="card ok">\n'
                           '        <div class="h2">Bottled Kraken</div>\n'
                           '        <ul>\n'
                           '            <li><b>Licence du dépôt :</b> GPL-3.0.</li>\n'
                           '            <li><b>En bref :</b> en cas de redistribution du logiciel, de publication de '
                           'versions modifiées ou de distribution d’un paquet construit à partir de celui-ci, les '
                           'conditions de la GPL-3.0 doivent être respectées.</li>\n'
                           '            <li><b>Important :</b> cela reste distinct des licences des bibliothèques '
                           'intégrées et des modèles utilisés.</li>\n'
                           '        </ul>\n'
                           '    </div>\n'
                           '\n'
                           '    <div class="card">\n'
                           '        <div class="h2">Kraken</div>\n'
                           '        <ul>\n'
                           '            <li>Kraken est la base OCR de Bottled Kraken.</li>\n'
                           '            <li>Le projet est placé sous <b>Apache License 2.0</b>.</li>\n'
                           '            <li>En cas de redistribution, le texte de licence, les mentions de copyright '
                           'et d’éventuelles obligations NOTICE sont particulièrement importants.</li>\n'
                           '        </ul>\n'
                           '    </div>\n'
                           '\n'
                           '    <div class="card">\n'
                           '        <div class="h2">faster-whisper</div>\n'
                           '        <ul>\n'
                           '            <li>faster-whisper est utilisé dans Bottled Kraken pour les fonctions locales '
                           'de transcription vocale.</li>\n'
                           '            <li>Le projet est sous <b>licence MIT</b>.</li>\n'
                           '            <li>Des conditions séparées peuvent toutefois s’appliquer aux modèles et aux '
                           'dépendances additionnelles.</li>\n'
                           '        </ul>\n'
                           '    </div>\n'
                           '\n'
                           '    <div class="card">\n'
                           '        <div class="h2">LM Studio</div>\n'
                           '        <ul>\n'
                           '            <li>LM Studio est utilisé en option comme serveur de modèles local ou '
                           'connecté.</li>\n'
                           '            <li>Les documents de référence sont ici surtout les <b>Terms of Service</b> et '
                           'la <b>Privacy Policy</b> officielles.</li>\n'
                           '            <li>En plus de cela, chaque modèle chargé via LM Studio peut avoir sa propre '
                           'licence.</li>\n'
                           '        </ul>\n'
                           '    </div>\n'
                           '\n'
                           '    <div class="card">\n'
                           '        <div class="h2">Ollama</div>\n'
                           '        <ul>\n'
                           '            <li>Le logiciel du dépôt officiel est placé sous <b>licence MIT</b>.</li>\n'
                           '            <li>Cela reste en général simple pour un usage local ; en cas de '
                           'redistribution d’un logiciel modifié, les mentions de licence et de copyright demeurent '
                           'importantes.</li>\n'
                           '            <li>Il faut distinguer cela des <b>fonctions cloud</b>, des règles de '
                           'confidentialité et surtout des licences propres aux modèles exécutés.</li>\n'
                           '        </ul>\n'
                           '    </div>\n'
                           '\n'
                           '    <div class="card">\n'
                           '        <div class="h2">Jan</div>\n'
                           '        <ul>\n'
                           '            <li>Le dépôt Jan est publié comme projet open source ; sa licence de dépôt est '
                           '<b>AGPL-3.0</b>.</li>\n'
                           '            <li>L’AGPL est particulièrement importante lorsque des versions modifiées sont '
                           'mises à disposition via un réseau.</li>\n'
                           '            <li>Comme pour les autres outils, des conditions supplémentaires peuvent '
                           's’appliquer aux modèles intégrés et aux fournisseurs cloud externes.</li>\n'
                           '        </ul>\n'
                           '    </div>\n'
                           '\n'
                           '    <div class="card">\n'
                           '        <div class="h2">GPT4All</div>\n'
                           '        <ul>\n'
                           '            <li>Le dépôt officiel GPT4All est sous <b>licence MIT</b>.</li>\n'
                           '            <li>La licence logicielle est permissive ; il faut néanmoins vérifier '
                           'séparément les licences des modèles, l’usage de la marque et les composants tiers.</li>\n'
                           '        </ul>\n'
                           '    </div>\n'
                           '\n'
                           '    <div class="card">\n'
                           '        <div class="h2">text-generation-webui (oobabooga)</div>\n'
                           '        <ul>\n'
                           '            <li>Le projet est sous <b>AGPL-3.0</b>.</li>\n'
                           '            <li>Ce cadre est juridiquement plus strict que MIT ou Apache, en particulier '
                           'lorsqu’on modifie le logiciel ou qu’on le met à disposition via un réseau.</li>\n'
                           '        </ul>\n'
                           '    </div>\n'
                           '\n'
                           '    <div class="card">\n'
                           '        <div class="h2">LocalAI</div>\n'
                           '        <ul>\n'
                           '            <li>D’après le dépôt officiel, LocalAI est sous <b>licence MIT</b>.</li>\n'
                           '            <li>Comme pour les autres serveurs, les licences des modèles, les composants '
                           'supplémentaires et les règles d’usage organisationnelles doivent être examinés '
                           'séparément.</li>\n'
                           '        </ul>\n'
                           '    </div>\n'
                           '\n'
                           '    <div class="card">\n'
                           '        <div class="h2">PySide6 / Qt for Python</div>\n'
                           '        <ul>\n'
                           '            <li>L’interface graphique de Bottled Kraken repose sur PySide6 / Qt for '
                           'Python.</li>\n'
                           '            <li>Qt for Python utilise des régimes de licence pouvant impliquer la '
                           '<b>LGPL</b> ou une licence commerciale Qt, selon le composant et le mode de '
                           'distribution.</li>\n'
                           '            <li>Pour la redistribution, le packaging et les produits combinés '
                           'propriétaires, la situation de licence Qt doit être vérifiée séparément.</li>\n'
                           '        </ul>\n'
                           '    </div>\n'
                           '\n'
                           '    <div class="card warn">\n'
                           '        <div class="h2">Remarque supplémentaire sur les modèles et les contenus</div>\n'
                           '        <ul>\n'
                           '            <li>La licence logicielle d’une application doit toujours être distinguée de '
                           'la licence des modèles OCR, vocaux ou IA qui y sont chargés.</li>\n'
                           '            <li>Le traitement de documents protégés par le droit d’auteur, de données '
                           'personnelles ou de fonds d’archives sensibles nécessite aussi une évaluation juridique '
                           'distincte.</li>\n'
                           '            <li>Cette fenêtre ne fournit qu’un aperçu compact, et non une analyse '
                           'juridique contraignante pour un cas particulier.</li>\n'
                           '        </ul>\n'
                           '    </div>\n'
                           '\n'
                           '    <div class="card">\n'
                           '        <div class="h2">Sources officielles</div>\n'
                           '        <ul>\n'
                           '            <li><a href="https://github.com/Testatost/Bottled-Kraken">Bottled Kraken – '
                           'Dépôt</a></li>\n'
                           '            <li><a href="https://github.com/mittagessen/kraken">Kraken – Dépôt</a></li>\n'
                           '            <li><a href="https://kraken.re/7.0/index.html">Kraken – '
                           'Documentation</a></li>\n'
                           '            <li><a href="https://github.com/SYSTRAN/faster-whisper">faster-whisper – '
                           'Dépôt</a></li>\n'
                           '            <li><a href="https://lmstudio.ai/app-terms">LM Studio – Terms of '
                           'Service</a></li>\n'
                           '            <li><a href="https://lmstudio.ai/privacy">LM Studio – Privacy Policy</a></li>\n'
                           '            <li><a href="https://github.com/ollama/ollama">Ollama – Dépôt</a></li>\n'
                           '            <li><a href="https://github.com/ollama/ollama/blob/main/LICENSE">Ollama – '
                           'Licence MIT</a></li>\n'
                           '            <li><a href="https://github.com/janhq/jan">Jan – Dépôt</a></li>\n'
                           '            <li><a href="https://docs.gpt4all.io/gpt4all_api_server/home.html">GPT4All – '
                           'Documentation du serveur API</a></li>\n'
                           '            <li><a '
                           'href="https://github.com/nomic-ai/gpt4all/blob/main/LICENSE.txt">GPT4All – Licence '
                           'MIT</a></li>\n'
                           '            <li><a '
                           'href="https://github.com/oobabooga/text-generation-webui">text-generation-webui – '
                           'Dépôt</a></li>\n'
                           '            <li><a '
                           'href="https://github.com/oobabooga/text-generation-webui/blob/main/LICENSE">text-generation-webui '
                           '– AGPL-3.0</a></li>\n'
                           '            <li><a href="https://localai.io/docs/overview/">LocalAI – Overview</a></li>\n'
                           '            <li><a href="https://github.com/mudler/LocalAI/blob/master/LICENSE">LocalAI – '
                           'Licence MIT</a></li>\n'
                           '            <li><a href="https://doc.qt.io/qtforpython-6/">Qt for Python – '
                           'Documentation</a></li>\n'
                           '            <li><a href="https://doc.qt.io/qtforpython-6/licenses.html">Qt for Python – '
                           'Licences</a></li>\n'
                           '        </ul>\n'
                           '    </div>\n',
        'ai_prompt_page_system': 'Du bist ein hochpräziser OCR- und Transkriptionsassistent für historische deutsche '
                                 'Drucke, Handschriften und Formulare.\n'
                                 'Du liest den Text direkt aus dem Bild.\n'
                                 'Das Bild ist die einzige Wahrheitsquelle.\n'
                                 'Du musst den gelesenen Text auf eine bereits vorgegebene Liste von Zielzeilen '
                                 'abbilden.\n'
                                 'Jede Zielzeile entspricht genau einer visuellen Formular- oder Textzeile.\n'
                                 'Du darfst keine zwei Zielzeilen zusammenziehen.\n'
                                 'Du darfst keine zusätzliche Leerzeile halluzinieren.\n'
                                 'Du darfst keinen langen Textblock in eine einzelne Zielzeile schreiben.\n'
                                 'Wenn eine Zielzeile keinen sicher lesbaren Text enthält, gib für genau diese Zeile '
                                 'einen leeren String zurück.\n'
                                 'Du musst die Anzahl der Zielzeilen exakt einhalten.\n'
                                 'Antworte ausschließlich mit gültigem JSON.\n'
                                 'Kein Markdown. Kein Zusatztext. Kein Kommentar.',
        'ai_prompt_page_user': 'Lies den Text direkt aus dem Bild.\n'
                               '\n'
                               'Du musst die vorgegebene Kraken-Zeilenstruktur EXAKT einhalten.\n'
                               'Es gibt genau {} Zielzeilen.\n'
                               'Jeder idx steht für genau eine visuelle Zielzeile.\n'
                               '\n'
                               'HARTE REGELN:\n'
                               '- Gib genau {} Einträge im Feld lines zurück\n'
                               '- Die idx-Werte müssen exakt 0 bis {} sein\n'
                               '- Kein idx darf fehlen\n'
                               '- Kein idx darf doppelt vorkommen\n'
                               '- Keine zwei Zielzeilen dürfen zu einer Zeile zusammengezogen werden\n'
                               '- Kein langer Satzblock darf in einer einzelnen Zielzeile landen\n'
                               '- Wenn eine Zielzeile unklar ist, gib den bestmöglichen kurzen Zeilentext zurück\n'
                               '- Wenn die Zielzeile wirklich leer ist, gib text als leeren String zurück\n'
                               '- Die bbox ist nur Orientierung für die visuelle Zuordnung\n'
                               '- Gib NUR das JSON-Objekt zurück\n'
                               '- Kein Markdown\n'
                               '- Keine Analyse\n'
                               '- Keine Kommentare\n'
                               '- Keine zusätzlichen Sätze\n'
                               '\n'
                               'Kraken-Zielzeilenstruktur:\n'
                               '{}\n'
                               '\n'
                               'Antwortformat exakt so:\n'
                               '{{"lines":[{{"idx":0,"text":"..."}},{{"idx":1,"text":"..."}}]}}',
        'ai_prompt_single_system': 'Du bist ein präziser OCR- und Transkriptionsassistent für historische deutsche '
                                   'Handschriften und Formulare.\n'
                                   'Du liest genau eine einzelne Zielzeile aus einem Bildausschnitt.\n'
                                   'Das Bild ist die einzige Wahrheitsquelle.\n'
                                   'Die Zielzeile befindet sich in der Mitte des Ausschnitts.\n'
                                   'Oberhalb oder unterhalb sichtbare Linien, Leerzeilen, Formularlinien, Labels oder '
                                   'Nachbarzeilen sind nur Kontext.\n'
                                   'Du darfst nur den Text der einen Zielzeile zurückgeben.\n'
                                   'Du darfst keinen Text aus Nachbarzeilen übernehmen.\n'
                                   'Du darfst keine zusätzliche Zeile erfinden.\n'
                                   'Du darfst keine lange Passage bilden, wenn im Ausschnitt nur eine kurze '
                                   'Formularzeile steht.\n'
                                   'Wenn die Zielzeile leer ist, gib einen leeren String zurück.\n'
                                   'Antworte ausschließlich mit gültigem JSON.\n'
                                   'Kein Markdown. Kein Zusatztext. Kein Kommentar.',
        'ai_prompt_single_user': 'Lies genau die Zielzeile in der Mitte des Bildausschnitts.\n'
                                 'WICHTIG:\n'
                                 '- Gib nur den Text dieser EINEN Zeile zurück\n'
                                 '- Benachbarte Zeilen dürfen nicht übernommen werden\n'
                                 '- Formular-Labels, Linien und Leerbereiche dürfen nicht halluziniert ergänzt werden\n'
                                 '- Wenn in dieser Zielzeile kein lesbarer Text steht, gib text als leeren String '
                                 'zurück\n'
                                 '- Keine zweite Zeile\n'
                                 '- Keine Zusammenfassung\n'
                                 '- Keine Erklärung\n'
                                 '- Kein Markdown\n'
                                 '- Keine Ausgabe vor oder nach dem JSON\n'
                                 '\n'
                                 'Format exakt:\n'
                                 '{{"text":"..."}}\n'
                                 '\n'
                                 'Zeilenindex: {}',
        'ai_prompt_decision_system': 'Du bist ein präziser OCR-Korrekturassistent für historische deutsche '
                                     'Handschriften und Formulare.\n'
                                     'Du bekommst für genau eine Zielzeile drei Kandidaten:\n'
                                     '1. Kraken-OCR\n'
                                     '2. OCR aus dem Gesamtseiten-Kontext\n'
                                     '3. OCR aus der Overlay-Box dieser Zeile\n'
                                     '\n'
                                     'WICHTIG:\n'
                                     '- Die Overlay-Box-OCR ist die Primärquelle.\n'
                                     '- Die Seiten-OCR ist NUR Kontext und darf keine fremden Nachbarzeilen in diese '
                                     'Zielzeile hineinziehen.\n'
                                     '- Kraken ist nur schwacher Fallback.\n'
                                     '- Du darfst keine zusätzliche Zeile erfinden.\n'
                                     '- Du darfst keinen Text aus benachbarten Formularzeilen übernehmen.\n'
                                     '- Du darfst keine lange Mehrzeilen-Passage in diese eine Zielzeile packen.\n'
                                     '- Wenn die Box-OCR plausibel ist, übernimm sie.\n'
                                     '- Nur wenn die Box-OCR klar abgeschnitten, leer oder offensichtlich falsch ist, '
                                     'darfst du mit Kraken korrigieren.\n'
                                     '- Die Seiten-OCR darf nur helfen, ein einzelnes unsicheres Wort zu bestätigen, '
                                     'nicht die ganze Zeile zu ersetzen.\n'
                                     '- Bewahre historische Schreibweise.\n'
                                     'Antworte ausschließlich mit gültigem JSON.\n'
                                     'Kein Markdown. Kein Zusatztext. Kein Kommentar.',
        'ai_prompt_decision_user': 'Zielzeile idx={}\n'
                                   '\n'
                                   'Kraken-OCR:\n'
                                   '{}\n'
                                   '\n'
                                   'Seitenkontext-OCR (nur Kontext, nicht Primärquelle):\n'
                                   '{}\n'
                                   '\n'
                                   'Overlay-Box-OCR (Primärquelle):\n'
                                   '{}\n'
                                   '\n'
                                   'Wähle die beste finale Fassung für GENAU diese eine Zeile.\n'
                                   'Bevorzuge die Overlay-Box-OCR.\n'
                                   'Gib nur die finale Textzeile zurück.\n'
                                   'Format exakt:\n'
                                   '{{"text":"..."}}',
        'ai_prompt_block_system': 'Du bist ein präziser OCR- und Transkriptionsassistent für historische deutsche '
                                  'Handschriften.\n'
                                  'Lies den Text frei direkt aus dem Bild.\n'
                                  'Das Bild ist die einzige Wahrheitsquelle.\n'
                                  'Du darfst nicht den OCR-Hinweis rekonstruieren, sondern musst das Bild selbst '
                                  'lesen.\n'
                                  'Die von außen vorgegebene Zeilenanzahl ist nur ein Strukturrahmen.\n'
                                  'Du musst den frei gelesenen Text passend in genau diese Anzahl von Zeilen '
                                  'eintragen.\n'
                                  'Antworte ausschließlich mit gültigem JSON.\n'
                                  'Kein Markdown. Kein Zusatztext. Kein Kommentar.',
        'ai_prompt_block_user': 'Lies die handschriftlichen Zeilen im Bildausschnitt.\n'
                                'Gib ausschließlich genau EIN JSON-Objekt zurück.\n'
                                'Kein Markdown. Kein ```json. Kein Kommentar. Kein Zusatztext.\n'
                                'Es müssen genau {} Einträge im Feld lines stehen.\n'
                                'Wichtig:\n'
                                '- doppelte Anführungszeichen innerhalb von text immer als " escapen\n'
                                '- keine weiteren Felder außer idx und text\n'
                                '- keine Ausgabe vor oder nach dem JSON\n'
                                'Format:\n'
                                '{{"lines":[{{"idx":0,"text":"..."}}]}}\n'
                                '\n'
                                'Die idx-Werte müssen lokal bei 0 beginnen.\n'
                                'Aktueller OCR-Hinweis:\n'
                                '{}',
        'line_menu_ai_revise_single': 'Réviser uniquement cette ligne avec le LM',
        'btn_ok': 'OK',
        'act_image_edit': 'Édition d’image',
        'canvas_menu_split_box': 'Scinder la boîte',
        'queue_ctx_check_all': 'Tout cocher',
        'queue_ctx_uncheck_all': 'Effacer toutes les coches',
        'queue_check_header_tooltip': 'Cliquer pour cocher tous les fichiers ou retirer toutes les coches',
        'line_menu_ai_revise_selected': 'Réviser les lignes sélectionnées avec le LM',
        'menu_lm_options': 'Options LM',
        'menu_whisper_options': 'Options Whisper',
        'act_whisper_set_path': 'Définir le chemin du modèle Whisper...',
        'act_whisper_set_mic': 'Choisir le microphone...',
        'act_scan_local': 'Scanner localement',
        'no_models_scan': 'Aucun modèle - vérifier le répertoire',
        'act_unload_model': 'Décharger le modèle',
        'msg_whisper_model_unloaded': 'Modèle Whisper déchargé.',
        'msg_whisper_models_found': '{} modèle(s) Whisper trouvé(s).',
        'msg_whisper_models_not_found': 'Aucun modèle Whisper trouvé.',
        'warn_no_audio_devices': 'Aucun périphérique d’entrée audio n’a été trouvé.',
        'dlg_choose_microphone': 'Choisir le microphone',
        'dlg_audio_input_device': 'Périphérique d’entrée audio :',
        'msg_microphone_set': 'Microphone défini : {}',
        'export_choose_format_label': 'Choisir le format d’export :',
        'msg_pdf_render_already_running': 'Un PDF est déjà en cours de rendu. Veuillez patienter un instant.',
        'pdf_page_display': '{} – Page {:04d}',
        'act_set_manual_lm_url': 'Définir l’URL du serveur LM...',
        'act_clear_manual_lm_url': 'Effacer l’URL du serveur LM',
        'msg_lm_found_url': 'LM trouvé : {} | URL : {}',
        'msg_lm_no_models_url': 'Aucun modèle trouvé | URL : {}',
        'msg_lm_found': 'LM trouvé : {}',
        'msg_lm_server_not_found': 'Aucun serveur LM local accessible n’a été trouvé.',
        'act_clear_ai_model': 'Retirer le modèle LM',
        'msg_ai_model_choice_cleared': 'Sélection du modèle LM effacée.',
        'msg_ai_model_removed': 'Modèle LM retiré.',
        'header_rec_models': 'Modèles de reconnaissance:',
        'header_seg_models': 'Modèles de segmentation:',
        'status_rec_model': 'Modèle de reconnaissance : {}',
        'status_seg_model': 'Modèle de segmentation : {}',
        'msg_ai_model_id_cleared_auto': 'Identifiant du modèle IA effacé, auto-détection localhost active.',
        'msg_ai_single_done': 'Révision LM terminée pour la ligne {}.',
        'log_ai_single_done': 'Révision LM de ligne terminée : {} | ligne {}',
        'msg_ai_single_cancelled': 'Révision de ligne annulée.',
        'log_ai_single_cancelled': 'Révision LM de ligne annulée : {}',
        'msg_ai_single_failed': 'Échec de la révision de ligne.',
        'log_ai_single_failed': 'Erreur de révision LM de ligne : {} -> {}',
        'msg_ai_cancelled_short': 'Révision annulée.',
        'msg_ai_failed_short': 'Échec de la révision.',
        'warn_blla_model_missing': 'Le modèle de segmentation blla est introuvable.',
        'dlg_project_loading_title': 'Charger le projet',
        'white_border_title': 'Ajouter une bordure blanche',
        'white_border_pixels': 'Bordure en pixels :',
        'image_edit_rotate_off': 'Rotation : NON',
        'image_edit_rotate_on': 'Rotation : OUI',
        'image_edit_grid': 'Grille',
        'image_edit_grid_tooltip': 'Taille de la grille : fine à grossière',
        'image_edit_grid_label': 'Taille de la grille',
        'image_edit_crop': 'Zone de recadrage',
        'image_edit_separator': 'Barre de séparation',
        'image_edit_gray': 'Niveaux de gris',
        'image_edit_contrast': 'Contraste',
        'image_edit_rotation_reset': 'Réinitialiser la rotation',
        'image_edit_smart_split': 'Découpage intelligent',
        'image_edit_prev': 'Image précédente',
        'image_edit_next': 'Image suivante',
        'image_edit_white_border': 'Ajouter une bordure blanche',
        'image_edit_white_border_with_px': 'Ajouter une bordure blanche ({} px)',
        'image_edit_apply_selected': 'Appliquer à toutes les images marquées',
        'image_edit_apply_all': 'Appliquer à toutes',
        'image_edit_applied_single_status': 'Image editing applied. Edited images were saved in the source directory '
                                            'and added to the queue as new entries.',
        'log_image_edit_applied': 'Image editing applied: {} | {} output file(s) saved in the source directory',
        'image_edit_no_image_loaded': 'Aucune image chargée',
        'image_edit_batch_title': 'Traitement d’image en cours',
        'image_edit_batch_label': 'Traitement de l’image {}/{} : {}',
        'msg_image_edit_batch_cancelled': 'Traitement d’image annulé.',
        'image_edit_notice_title': 'Remarque',
        'image_edit_turn_off_rotation_first': 'La rotation est encore active.\n'
                                              '\n'
                                              "Veuillez d’abord passer à 'Rotation : NON' avant de modifier la zone de "
                                              'recadrage ou la barre de séparation.',
        'msg_not_available': 'Indisponible',
        'help_nav_image_edit': 'Édition d’image',
        'help_nav_lm_alternatives': 'Alternatives à LM Studio',
        'dlg_lm_url_title': 'URL du serveur LM',
        'dlg_lm_url_label': """<div class="card">
        <div class="h2"><b>Serveurs locaux typiques</b></div>
        <ul>
            <li><code>http://127.0.0.1:1234/v1</code> - <b>LM Studio</b></li>
            <li><code>http://localhost:11434/v1</code> - <b>Ollama</b></li>
            <li><code>http://127.0.0.1:1337/v1</code> - <b>Jan</b></li>
            <li><code>http://localhost:4891/v1</code> - <b>GPT4All</b></li>
            <li><code>http://127.0.0.1:5000/v1</code> - <b>text-generation-webui</b></li>
            <li><code>http://localhost:8080/v1</code> - <b>LocalAI</b></li>
            <li><code>http://HOST:8000/v1</code> - <b>vLLM</b></li>
        </ul>
    </div>

    <div class="card">
        <div class="h2"><b>Correction automatique</b></div>
        <ul>
            <li>Le préfixe <code>http://</code> manquant est ajouté automatiquement.</li>
            <li><code>/models</code> ou <code>/chat/completions</code> est automatiquement réduit à l’URL de base.</li>
            <li><code>/v1</code> est ajouté si nécessaire.</li>
        </ul>
    </div>

    <div class="card">
        <div class="h2"><b>Important</b></div>
        <ul>
            <li>N’entrez pas de commandes SSH.</li>
            <li>En cas de tunnel SSH, utilisez l’URL locale du tunnel.</li>
            <li>Pour Ollama dans Bottled Kraken, utilisez normalement l’URL compatible OpenAI en <code>/v1</code>, et non l’URL native en <code>/api</code>.</li>
        </ul>
    </div>""",
        'dlg_lm_url_placeholder': 'ex. http://127.0.0.1:1234/v1',
        'help_html_image_edit': '\n'
                                '            <div class="card">\n'
                                '                <div class="h1">Édition d’image</div><br>\n'
                                '                L’édition d’image sert à <b>préparer les pages avant l’OCR</b>.\n'
                                '                C’est particulièrement utile lorsqu’un scan est incliné, trop sombre, '
                                'peu contrasté,\n'
                                '                trop recadré ou enregistré comme double page.\n'
                                '            </div>\n'
                                '\n'
                                '            <div class="card">\n'
                                '                <div class="h2">Outils disponibles</div>\n'
                                '                <ul>\n'
                                '                    <li><b>Rotation :</b> redresser une page</li>\n'
                                '                    <li><b>Zone de recadrage :</b> supprimer les marges '
                                'gênantes</li>\n'
                                '                    <li><b>Barre de séparation :</b> séparer proprement les doubles '
                                'pages ou les contenus côte à côte</li>\n'
                                '                    <li><b>Niveaux de gris / Contraste :</b> améliorer la lisibilité '
                                'de l’imprimé et de l’écriture manuscrite</li>\n'
                                '                    <li><b>Ajouter une bordure blanche :</b> utile pour les pages '
                                'trop serrées</li>\n'
                                '                    <li><b>Découpage intelligent :</b> séparation semi-automatique '
                                'pour les sources difficiles</li>\n'
                                '                </ul>\n'
                                '            </div>\n'
                                '\n'
                                '            <div class="card">\n'
                                '                <div class="h2">Déroulement typique</div>\n'
                                '                <ol>\n'
                                '                    <li>Charger une image ou une page PDF</li>\n'
                                '                    <li>Ouvrir l’édition d’image</li>\n'
                                '                    <li>Ajuster l’aperçu : rotation, recadrage, contraste, séparation '
                                'si nécessaire</li>\n'
                                '                    <li>Appliquer le résultat à l’image actuelle, aux images marquées '
                                'ou à toutes</li>\n'
                                '                    <li>Lancer ensuite Kraken OCR</li>\n'
                                '                </ol>\n'
                                '            </div>\n'
                                '\n'
                                '            <div class="card warn">\n'
                                '                <div class="h2">Remarque</div>\n'
                                '                <span class="badge">Important</span>\n'
                                '                <ul>\n'
                                '                    <li>Si la rotation est active, il est préférable d’ajuster '
                                'finement la zone de recadrage et la barre de séparation uniquement après être revenu '
                                'à <code>Rotation : NON</code>.</li>\n'
                                '                    <li>Les images modifiées sont enregistrées comme nouveaux '
                                'fichiers de sortie puis réajoutées dans la file d’attente.</li>\n'
                                '                </ul>\n'
                                '            </div>\n'
                                '\n'
                                '            <div class="card">\n'
                                '                <div class="h2">Quand est-ce utile ?</div>\n'
                                '                <ul>\n'
                                '                    <li>scans inclinés ou déformés</li>\n'
                                '                    <li>doubles pages de livres ou d’archives</li>\n'
                                '                    <li>formulaires avec trop de marges ou un fond parasite</li>\n'
                                '                    <li>imprimés historiques pâles ou écritures peu contrastées</li>\n'
                                '                </ul>\n'
                                '            </div>\n'
                                '        ',
        'help_html_lm_alternatives': '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h1">Alternatives à LM Studio</div><br>\n'
                                     '                Bottled Kraken n’est pas limité à LM Studio.\n'
                                     '                L’essentiel est que le service en cours fournisse une <b>API '
                                     'compatible OpenAI</b>.\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">Ollama</div>\n'
                                     '                <ul>\n'
                                     '                    <li>pour beaucoup d’utilisateurs, c’est le remplaçant le '
                                     'plus propre lorsqu’un service local est surtout recherché</li>\n'
                                     '                    <li>API native à '
                                     '<code>http://localhost:11434/api</code></li>\n'
                                     '                    <li>pour Bottled Kraken, utiliser en général l’URL '
                                     'compatible OpenAI <code>http://localhost:11434/v1</code></li>\n'
                                     '                    <li>propose aussi une compatibilité Anthropic pour certains '
                                     'flux de travail</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">Jan</div>\n'
                                     '                <ul>\n'
                                     '                    <li>souvent le plus proche de LM Studio dans l’idée '
                                     'd’utilisation</li>\n'
                                     '                    <li>application de bureau avec modèles locaux et serveur API '
                                     'intégré</li>\n'
                                     '                    <li>URL typique : '
                                     '<code>http://127.0.0.1:1337/v1</code></li>\n'
                                     '                    <li>selon la configuration, une clé API peut aussi être '
                                     'requise</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">GPT4All</div>\n'
                                     '                <ul>\n'
                                     '                    <li>également très proche de « démarrer localement et '
                                     'utiliser »</li>\n'
                                     '                    <li>URL typique : '
                                     '<code>http://localhost:4891/v1</code></li>\n'
                                     '                    <li>compatible OpenAI</li>\n'
                                     '                    <li>LocalDocs peut aussi être utile pour des flux simples de '
                                     'documents / RAG locaux</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">text-generation-webui</div>\n'
                                     '                <ul>\n'
                                     '                    <li>particulièrement intéressant pour les utilisateurs qui '
                                     'aiment configurer davantage</li>\n'
                                     '                    <li>API compatible OpenAI et Anthropic</li>\n'
                                     '                    <li>URL typique : '
                                     '<code>http://127.0.0.1:5000/v1</code></li>\n'
                                     '                    <li>selon le backend, peut aussi prendre en charge la vision '
                                     'et le tool calling</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card">\n'
                                     '                <div class="h2">LocalAI</div>\n'
                                     '                <ul>\n'
                                     '                    <li>bien adapté lorsqu’on cherche plutôt un serveur IA local '
                                     'auto-hébergé qu’une application de bureau classique</li>\n'
                                     '                    <li>URL typique : '
                                     '<code>http://localhost:8080/v1</code></li>\n'
                                     '                    <li>compatible OpenAI, avec en plus une interface web et des '
                                     'fonctions serveur étendues</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '\n'
                                     '            <div class="card warn">\n'
                                     '                <div class="h2">Important</div>\n'
                                     '                <span class="badge">Compatibilité</span>\n'
                                     '                <ul>\n'
                                     '                    <li>Pour Bottled Kraken, l’élément principal est l’URL de '
                                     'base compatible OpenAI.</li>\n'
                                     '                    <li>Tous les outils n’utilisent pas les mêmes ports par '
                                     'défaut ni la même authentification.</li>\n'
                                     '                    <li>Si l’authentification par clé API est activée, Bottled '
                                     'Kraken doit aussi envoyer cet en-tête.</li>\n'
                                     '                </ul>\n'
                                     '            </div>\n'
                                     '        '}}

ADDITIONAL_TRANSLATIONS = {
    "de": {
        "btn_line_search": "Suche",
        "btn_line_search_tooltip": "In den erkannten Zeilen suchen",
        "line_search_placeholder": "Wort oder Text eingeben...",
        "line_search_tooltip": "In den erkannten Zeilen nach Wörtern suchen",
        "help_hw_card_title": "Hardwarevoraussetzungen",
        "help_hw_badge": "System-Check",
        "help_hw_intro": "Schnelle Einschätzung für Kraken, LM-Überarbeitung und Whisper auf diesem Rechner.",
        "help_hw_h2_detected": "Erkannte Hardware",
        "help_hw_h2_usage": "Status: Verwendbarkeit",
        "help_hw_h2_components": "Komponentencheck",
        "help_hw_h2_requirements": "Mindest- und empfohlene Voraussetzungen",

        "help_hw_col_area": "Bereich",
        "help_hw_col_min": "Minimum",
        "help_hw_col_rec": "Empfohlen",

        "help_hw_label_threads": "Threads",
        "help_hw_label_vram": "VRAM",
        "help_hw_label_kraken": "Kraken OCR",
        "help_hw_label_lm": "LM-Überarbeitung",
        "help_hw_label_whisper": "Whisper",
        "help_hw_label_all": "Alles zusammen",

        "help_hw_gpu_none": "Keine nutzbare GPU erkannt",
        "help_hw_unknown": "unbekannt",
        "help_hw_vram_unknown": "nicht verfügbar",
        "help_hw_vram_shared": "geteilt / nicht direkt abgefragt",
        "help_hw_fmt_gb": "{:.1f} GB",

        "help_hw_status_good": "gut nutzbar",
        "help_hw_status_usable_slow": "nutzbar, aber eher langsam",
        "help_hw_status_limited": "nutzbar, aber eingeschränkt",
        "help_hw_status_limited_cpu": "nur eingeschränkt im CPU-Betrieb",
        "help_hw_status_weak": "Hardware eher zu schwach",

        "help_hw_component_ok": "ok",
        "help_hw_component_borderline": "grenzwertig",
        "help_hw_component_not_enough": "nicht ausreichend",

        "help_hw_req_kraken_min": "2+ CPU-Threads, 4+ GB RAM, GPU optional",
        "help_hw_req_kraken_rec": "4+ CPU-Threads, 8+ GB RAM, GPU optional",

        "help_hw_req_lm_min": "4+ CPU-Threads, 8+ GB RAM, 6+ GB VRAM für kleine lokale Modelle",
        "help_hw_req_lm_rec": "6+ CPU-Threads, 16+ GB RAM, 8+ bis 12+ GB VRAM",

        "help_hw_req_whisper_min": "4+ CPU-Threads, 6+ GB RAM, 4+ GB VRAM optional für GPU-Betrieb",
        "help_hw_req_whisper_rec": "6+ CPU-Threads, 8+ GB RAM, 6+ GB VRAM für schnelle GPU-Nutzung",

        "help_hw_req_all_min": "4+ CPU-Threads, 8+ GB RAM, 6+ GB VRAM wenn LM/Whisper auf GPU laufen sollen",
        "help_hw_req_all_rec": "8+ CPU-Threads, 16+ GB RAM, 8+ bis 12+ GB VRAM",

        "help_hw_req_note": "Hinweis: Vor allem die LM-Überarbeitung hängt stark vom geladenen Modell und dessen Quantisierung ab.",
        "help_hw_note": "Die Einschätzung ist eine interne Bottled-Kraken-Heuristik und keine harte technische Sperre."
    },

    "en": {
        "btn_line_search": "Search",
        "btn_line_search_tooltip": "Search in recognized lines",
        "line_search_placeholder": "Enter word or text...",
        "line_search_tooltip": "Search words in recognized lines",
        "help_hw_card_title": "Hardware requirements",
        "help_hw_badge": "System check",
        "help_hw_intro": "Quick estimate for Kraken, LM revision, and Whisper on this computer.",
        "help_hw_h2_detected": "Detected hardware",
        "help_hw_h2_usage": "Status: usability",
        "help_hw_h2_components": "Component check",
        "help_hw_h2_requirements": "Minimum and recommended requirements",

        "help_hw_col_area": "Area",
        "help_hw_col_min": "Minimum",
        "help_hw_col_rec": "Recommended",

        "help_hw_label_threads": "Threads",
        "help_hw_label_vram": "VRAM",
        "help_hw_label_kraken": "Kraken OCR",
        "help_hw_label_lm": "LM revision",
        "help_hw_label_whisper": "Whisper",
        "help_hw_label_all": "Everything together",

        "help_hw_gpu_none": "No usable GPU detected",
        "help_hw_unknown": "unknown",
        "help_hw_vram_unknown": "not available",
        "help_hw_vram_shared": "shared / not queried directly",
        "help_hw_fmt_gb": "{:.1f} GB",

        "help_hw_status_good": "works well",
        "help_hw_status_usable_slow": "usable, but rather slow",
        "help_hw_status_limited": "usable, but limited",
        "help_hw_status_limited_cpu": "only limited in CPU mode",
        "help_hw_status_weak": "hardware is likely too weak",

        "help_hw_component_ok": "ok",
        "help_hw_component_borderline": "borderline",
        "help_hw_component_not_enough": "not sufficient",

        "help_hw_req_kraken_min": "2+ CPU threads, 4+ GB RAM, GPU optional",
        "help_hw_req_kraken_rec": "4+ CPU threads, 8+ GB RAM, GPU optional",

        "help_hw_req_lm_min": "4+ CPU threads, 8+ GB RAM, 6+ GB VRAM for small local models",
        "help_hw_req_lm_rec": "6+ CPU threads, 16+ GB RAM, 8+ to 12+ GB VRAM",

        "help_hw_req_whisper_min": "4+ CPU threads, 6+ GB RAM, 4+ GB VRAM optional for GPU use",
        "help_hw_req_whisper_rec": "6+ CPU threads, 8+ GB RAM, 6+ GB VRAM for fast GPU use",

        "help_hw_req_all_min": "4+ CPU threads, 8+ GB RAM, 6+ GB VRAM if LM/Whisper should run on GPU",
        "help_hw_req_all_rec": "8+ CPU threads, 16+ GB RAM, 8+ to 12+ GB VRAM",

        "help_hw_req_note": "Note: LM revision especially depends heavily on the loaded model and its quantization.",
        "help_hw_note": "This estimate is an internal Bottled Kraken heuristic and not a hard technical lock."
    },

    "fr": {
        "btn_line_search": "Recherche",
        "btn_line_search_tooltip": "Rechercher dans les lignes reconnues",
        "line_search_placeholder": "Saisir un mot ou un texte...",
        "line_search_tooltip": "Rechercher des mots dans les lignes reconnues",
        "help_hw_card_title": "Configuration matérielle",
        "help_hw_badge": "Vérification système",
        "help_hw_intro": "Estimation rapide pour Kraken, la révision LM et Whisper sur cet ordinateur.",
        "help_hw_h2_detected": "Matériel détecté",
        "help_hw_h2_usage": "Statut : utilisabilité",
        "help_hw_h2_components": "Vérification des composants",
        "help_hw_h2_requirements": "Configuration minimale et recommandée",

        "help_hw_col_area": "Domaine",
        "help_hw_col_min": "Minimum",
        "help_hw_col_rec": "Recommandé",

        "help_hw_label_threads": "Threads",
        "help_hw_label_vram": "VRAM",
        "help_hw_label_kraken": "Kraken OCR",
        "help_hw_label_lm": "Révision LM",
        "help_hw_label_whisper": "Whisper",
        "help_hw_label_all": "Ensemble",

        "help_hw_gpu_none": "Aucun GPU exploitable détecté",
        "help_hw_unknown": "inconnu",
        "help_hw_vram_unknown": "non disponible",
        "help_hw_vram_shared": "partagée / non interrogée directement",
        "help_hw_fmt_gb": "{:.1f} GB",

        "help_hw_status_good": "bonne utilisation possible",
        "help_hw_status_usable_slow": "utilisable, mais plutôt lent",
        "help_hw_status_limited": "utilisable, mais limité",
        "help_hw_status_limited_cpu": "seulement limité en mode CPU",
        "help_hw_status_weak": "matériel probablement trop faible",

        "help_hw_component_ok": "ok",
        "help_hw_component_borderline": "limite",
        "help_hw_component_not_enough": "insuffisant",

        "help_hw_req_kraken_min": "2+ threads CPU, 4+ GB RAM, GPU optionnel",
        "help_hw_req_kraken_rec": "4+ threads CPU, 8+ GB RAM, GPU optionnel",

        "help_hw_req_lm_min": "4+ threads CPU, 8+ GB RAM, 6+ GB VRAM pour petits modèles locaux",
        "help_hw_req_lm_rec": "6+ threads CPU, 16+ GB RAM, 8+ à 12+ GB VRAM",

        "help_hw_req_whisper_min": "4+ threads CPU, 6+ GB RAM, 4+ GB VRAM optionnels pour l’usage GPU",
        "help_hw_req_whisper_rec": "6+ threads CPU, 8+ GB RAM, 6+ GB VRAM pour une utilisation GPU rapide",

        "help_hw_req_all_min": "4+ threads CPU, 8+ GB RAM, 6+ GB VRAM si LM/Whisper doivent fonctionner sur GPU",
        "help_hw_req_all_rec": "8+ threads CPU, 16+ GB RAM, 8+ à 12+ GB VRAM",

        "help_hw_req_note": "Remarque : la révision LM dépend fortement du modèle chargé et de sa quantification.",
        "help_hw_note": "Cette estimation est une heuristique interne de Bottled Kraken et non un blocage technique strict."
    },
}

for _lang, _values in ADDITIONAL_TRANSLATIONS.items():
    TRANSLATIONS.setdefault(_lang, {}).update(_values)

# Sicherheitsnetz: fehlende Keys in EN/FR fallen auf DE zurück
for _lang in ("en", "fr"):
    for _k, _v in TRANSLATIONS.get("de", {}).items():
        TRANSLATIONS[_lang].setdefault(_k, _v)

BBox = Tuple[int, int, int, int]
Point = Tuple[float, float]

# -----------------------------
# DATENKLASSEN
# -----------------------------


@dataclass
class RecordView:
    idx: int
    text: str
    bbox: Optional[BBox]

UndoSnapshot = Tuple[List[Tuple[str, Optional[BBox]]], int]

@dataclass
class TaskItem:
    path: str
    display_name: str
    status: int = STATUS_WAITING
    results: Optional[Tuple[str, list, Image.Image, List[RecordView]]] = None
    edited: bool = False
    undo_stack: List[UndoSnapshot] = field(default_factory=list)
    redo_stack: List[UndoSnapshot] = field(default_factory=list)
    source_kind: str = "image"  # "image" oder "pdf_page"
    relative_path: str = ""
    preset_bboxes: List[Optional[BBox]] = field(default_factory=list)
    lm_locked_bboxes: List[Optional[BBox]] = field(default_factory=list)

@dataclass
class OCRJob:
    input_paths: List[str]
    recognition_model_path: str
    segmentation_model_path: Optional[str]
    device: str
    reading_direction: int
    export_format: str
    export_dir: Optional[str]
    preset_bboxes_by_path: Dict[str, List[Optional[BBox]]] = field(default_factory=dict)

# -----------------------------
# GEOMETRIE & SORTIERUNG
# -----------------------------
def _coerce_points(obj: Any) -> List[Point]:
    if obj is None:
        return []
    if isinstance(obj, (list, tuple)):
        if not obj:
            return []
        first = obj[0]
        if isinstance(first, (list, tuple)) and len(first) == 2 and isinstance(first[0], (int, float)):
            try:
                return [(float(x), float(y)) for x, y in obj]
            except Exception:
                return []
        if isinstance(first, (list, tuple)) and first and isinstance(first[0], (list, tuple)) and len(first[0]) == 2:
            pts: List[Point] = []
            for contour in obj:
                pts.extend(_coerce_points(contour))
            return pts
    return []

def _bbox_from_points(points: List[Point], pad: int = 0) -> Optional[Tuple[int, int, int, int]]:
    if not points:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x0 = int(min(xs)) - pad
    y0 = int(min(ys)) - pad
    x1 = int(max(xs)) + pad
    y1 = int(max(ys)) + pad
    if x1 <= x0 or y1 <= y0:
        return None
    return x0, y0, x1, y1

def record_bbox(r: Any) -> Optional[Tuple[int, int, int, int]]:
    bbox = getattr(r, "bbox", None)
    if bbox:
        try:
            x0, y0, x1, y1 = bbox
            x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
            if x1 > x0 and y1 > y0:
                return x0, y0, x1, y1
        except Exception:
            pass

    for attr in ("boundary", "polygon"):
        boundary = getattr(r, attr, None)
        if boundary:
            pts = _coerce_points(boundary)
            bb = _bbox_from_points(pts, pad=2)
            if bb:
                return bb

    baseline = getattr(r, "baseline", None)
    if baseline:
        pts = _coerce_points(baseline)
        bb = _bbox_from_points(pts, pad=2)
        if bb:
            x0, y0, x1, y1 = bb
            vpad = 14
            return x0, y0 - vpad, x1, y1 + vpad
    return None

def baseline_length(bl) -> float:
    pts = _coerce_points(bl)
    if len(pts) < 2:
        return 0.0
    x1, y1 = pts[0]
    x2, y2 = pts[-1]
    return math.hypot(x2 - x1, y2 - y1)

# Vertikale Separator-Records (Spaltentrenner)
VSEP_RE = re.compile(r'^[|│┃¦︱︳]+$')  # | │ ┃ ¦ ︱ ︳

# Horizontale Separator-Records (Zeilentrenner)
HSEP_RE = re.compile(r'^[_\-\u2500\u2501\u2504\u2505]{3,}$')  # _ - ─ ━ etc. (mind. 3)
ONLY_SYMBOL_LINE_RE = re.compile(
    r'^[\(\)\{\}\?\!\/\\\""„“\$\%\&\[\]\=,\.\-—_:;><\|\+\*#\'~`´\^°]+$'
)

NOISE_LINE_RE = re.compile(
    r'^(?:'
    r'a{3,}|e{3,}|i{3,}|o{3,}|u{3,}|'
    r'ä{3,}|ö{3,}|ü{3,}|'
    r'\.{3,}'
    r')$',
    re.IGNORECASE
)

NOISE_REPEAT_RE = re.compile(
    r'^([aäeéiioöuü])(?:[\s\.\,\-_:;]*\1){2,}$',
    re.IGNORECASE
)

DOTS_ONLY_RE = re.compile(r'^(?:\.\s*){3,}$')

def _is_symbol_only_line(text: Any) -> bool:
    txt = _clean_ocr_text(text)
    if not txt:
        return False

    return bool(ONLY_SYMBOL_LINE_RE.fullmatch(txt))

def _is_noise_line(text: Any) -> bool:
    txt = _clean_ocr_text(text)
    if not txt:
        return False

    if NOISE_REPEAT_RE.fullmatch(txt):
        return True

    if DOTS_ONLY_RE.fullmatch(txt):
        return True

    return False

def sort_records_handwriting_simple(records, reading_mode: int = READING_MODES["TB_LR"]):
    """
    Einfache, stabile Sortierung für einspaltige Handschrift:
    zuerst von oben nach unten, innerhalb derselben Zeilenhöhe von links nach rechts.
    """
    raw = []
    for r in records:
        bb = record_bbox(r)
        if bb:
            raw.append((r, bb))

    if not raw:
        return list(records)

    rev_y = reading_mode in (READING_MODES["BT_LR"], READING_MODES["BT_RL"])
    rev_x = reading_mode in (READING_MODES["TB_RL"], READING_MODES["BT_RL"])

    heights = [(bb[3] - bb[1]) for _, bb in raw if (bb[3] - bb[1]) > 0]
    med_h = statistics.median(heights) if heights else 20.0
    y_tol = max(10.0, med_h * 0.6)

    def cx(bb):
        return (bb[0] + bb[2]) / 2.0

    def cy(bb):
        return (bb[1] + bb[3]) / 2.0

    # erst grob nach y sortieren
    raw.sort(key=lambda x: cy(x[1]), reverse=rev_y)

    rows = []
    for r, bb in raw:
        my = cy(bb)
        placed = False

        for row in rows:
            if abs(my - row["cy"]) <= y_tol:
                row["items"].append((r, bb))
                n = len(row["items"])
                row["cy"] = ((row["cy"] * (n - 1)) + my) / n
                placed = True
                break

        if not placed:
            rows.append({
                "cy": my,
                "items": [(r, bb)]
            })

    rows.sort(key=lambda row: row["cy"], reverse=rev_y)

    ordered = []
    for row in rows:
        row["items"].sort(key=lambda x: cx(x[1]), reverse=rev_x)
        ordered.extend([r for r, _ in row["items"]])

    return ordered

def sort_records_reading_order(records, image_width: int, image_height: int,
                               reading_mode: int = READING_MODES["TB_LR"]):
    # ---------- Helfer ----------
    def cx(bb):
        return (bb[0] + bb[2]) / 2.0

    def cy(bb):
        return (bb[1] + bb[3]) / 2.0

    def bw(bb):
        return bb[2] - bb[0]

    def bh(bb):
        return bb[3] - bb[1]

    def quant(vals, p):
        if not vals:
            return None
        vs = sorted(vals)
        k = (len(vs) - 1) * p
        f = int(k)
        c = min(f + 1, len(vs) - 1)
        if f == c:
            return vs[f]
        return vs[f] + (vs[c] - vs[f]) * (k - f)

    # Richtungs-Flags
    rev_y = (reading_mode in (READING_MODES["BT_LR"], READING_MODES["BT_RL"]))  # unten -> oben
    rev_cols = (reading_mode in (READING_MODES["TB_RL"], READING_MODES["BT_RL"]))  # Spalten rechts -> links

    W = max(1, int(image_width))

    # ---------- BBoxes sammeln ----------
    raw = []
    for r in records:
        bb = record_bbox(r)
        if bb:
            raw.append((r, bb))
    if not raw:
        return list(records)

    # ---------- Schräglage (Skew) aus Baselines schätzen (am besten) ----------
    angles = []
    for r, _ in raw:
        bl = getattr(r, "baseline", None)
        pts = _coerce_points(bl)
        if len(pts) >= 2:
            x1, y1 = pts[0]
            x2, y2 = pts[-1]
            dx = (x2 - x1)
            dy = (y2 - y1)
            if abs(dx) > 1.0:
                a = math.atan2(dy, dx)
                # extrem schräge Winkel verwerfen
                if abs(a) < math.radians(20):
                    angles.append(a)

    skew = statistics.median(angles) if angles else 0.0
    # Koordinaten um -skew rotieren (Entzerren / Deskew)
    cs = math.cos(-skew)
    sn = math.sin(-skew)

    Wc = max(1.0, float(image_width)) / 2.0
    Hc = max(1.0, float(image_height)) / 2.0

    def rot(x, y):
        # verschieben -> rotieren -> zurückverschieben
        x -= Wc
        y -= Hc
        xr = x * cs - y * sn
        yr = x * sn + y * cs
        return (xr + Wc, yr + Hc)

    def deskew_bb(bb):
        x0, y0, x1, y1 = bb
        pts = [rot(x0, y0), rot(x1, y0), rot(x1, y1), rot(x0, y1)]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (min(xs), min(ys), max(xs), max(ys))

    items = []
    for r, bb in raw:
        dbb = deskew_bb(bb)
        items.append((r, bb, dbb))

    # ---------- typische Zeilenhöhe (entzerrt / deskewed) ----------
    hs = [(dbb[3] - dbb[1]) for _, _, dbb in items if (dbb[3] - dbb[1]) > 0]
    med_h = sorted(hs)[len(hs) // 2] if hs else 14.0
    MIN_H = max(10.0, 0.6 * med_h)

    def is_fullwidth(dbb):
        return (dbb[2] - dbb[0]) >= 0.82 * W

    # Kandidaten für Haupttext (Body)
    body = [(r, bb, dbb) for (r, bb, dbb) in items if (dbb[3] - dbb[1]) >= MIN_H and not is_fullwidth(dbb)]
    if len(body) < 8:
        # Fallback: nach entzerrtem y, dann x sortieren
        ordered = sorted(items, key=lambda x: (cy(x[2]), cx(x[2])), reverse=rev_y)
        return [r for r, _, _ in ordered]

    # ---------- Header/Footer über y-Quantile bestimmen (entzerrt) ----------
    ys_top = [dbb[1] for _, _, dbb in body]
    ys_bot = [dbb[3] for _, _, dbb in body]
    body_top = quant(ys_top, 0.08)
    body_bot = quant(ys_bot, 0.92)
    if body_top is None or body_bot is None:
        ordered = sorted(items, key=lambda x: (cy(x[2]), cx(x[2])), reverse=rev_y)
        return [r for r, _, _ in ordered]

    MARGIN_Y = max(10.0, 0.8 * med_h)

    def is_real_page_header_or_footer(dbb):
        x0, y0, x1, y1 = dbb
        w = x1 - x0
        x_center = (x0 + x1) / 2.0

        if w >= 0.72 * W:
            return True
        if abs(x_center - (W / 2.0)) <= 0.12 * W and w >= 0.32 * W:
            return True
        return False

    header, footer, midband = [], [], []
    for r, bb, dbb in items:
        if dbb[3] < (body_top - MARGIN_Y) and is_real_page_header_or_footer(dbb):
            header.append((r, bb, dbb))
        elif dbb[1] > (body_bot + MARGIN_Y) and is_real_page_header_or_footer(dbb):
            footer.append((r, bb, dbb))
        else:
            midband.append((r, bb, dbb))

    def sort_y_then_x(lst):
        return sorted(lst, key=lambda x: (cy(x[2]), cx(x[2])), reverse=rev_y)

    def sort_region_by_columns(lst):
        if not lst:
            return []

        # grobe 2-Spalten-Zuordnung über Seitenmitte
        mid = W / 2.0
        gutter = max(20.0, 0.03 * W)

        left = []
        right = []
        spanning = []

        for r, bb, dbb in lst:
            x0, _, x1, _ = dbb
            w = x1 - x0
            x_center = (x0 + x1) / 2.0

            # echte zentrierte / breite Überschrift bleibt oben/unten y-sortiert
            if w >= 0.72 * W or (abs(x_center - mid) <= 0.14 * W and w >= 0.28 * W):
                spanning.append((r, bb, dbb))
                continue

            if x1 <= mid - gutter:
                left.append((r, bb, dbb))
            elif x0 >= mid + gutter:
                right.append((r, bb, dbb))
            else:
                # Grenzfälle über Mittelpunkt
                if x_center < mid:
                    left.append((r, bb, dbb))
                else:
                    right.append((r, bb, dbb))

        spanning = sort_y_then_x(spanning)
        left = sort_y_then_x(left)
        right = sort_y_then_x(right)

        out = []
        out.extend(spanning)

        if rev_cols:
            out.extend(right)
            out.extend(left)
        else:
            out.extend(left)
            out.extend(right)

        return out

    header_sorted = sort_region_by_columns(header)
    footer_sorted = sort_region_by_columns(footer)

    # ---------- Vertikale Separatoren ('|', '│', '┃') als Spaltengassen erkennen ----------
    sep_x = []
    for r, bb, dbb in midband:
        pred = getattr(r, "prediction", "")
        t = str(pred).strip()
        if not t:
            continue
        if VSEP_RE.match(t):
            w_sep = (dbb[2] - dbb[0])
            h_sep = (dbb[3] - dbb[1])
            # etwas weniger streng -> Separator wird eher erkannt
            if w_sep <= 0.05 * W and h_sep >= 1.8 * med_h:
                sep_x.append(cx(dbb))

    sep_x.sort()
    # keep only separators that are reasonably distinct
    filtered = []
    for x in sep_x:
        if not filtered or abs(x - filtered[-1]) > max(10.0, 0.02 * W):
            filtered.append(x)
    sep_x = filtered

    # ---------- Spalten aufbauen ----------
    mid_text = [(r, bb, dbb) for (r, bb, dbb) in midband if (dbb[3] - dbb[1]) >= MIN_H and not is_fullwidth(dbb)]

    # ==========================================================
    # 2-Spalten FALLBACK (wie alter Code) – nur wenn <=2 Spalten
    # ==========================================================
    def _estimate_strong_columns(mid_items):
        # Zählt 'echte' Spalten grob über x0-Cluster.
        # Gibt 1 / 2 / 3 (3 = 3 oder mehr) zurück.
        if not mid_items:
            return 1

        xs = [it[2][0] for it in mid_items]  # dbb x0
        if not xs:
            return 1

        # eher grob -> robust gegen Einrückungen
        x_thr = max(70.0, 0.09 * W)
        clusters = []  # {"x": mean, "n": count}

        for x0 in sorted(xs):
            placed = False
            for c in clusters:
                if abs(c["x"] - x0) <= x_thr:
                    c["n"] += 1
                    c["x"] = (c["x"] * 0.85) + (x0 * 0.15)
                    placed = True
                    break
            if not placed:
                clusters.append({"x": float(x0), "n": 1})

        clusters.sort(key=lambda c: c["x"])

        # "echte" Spalten müssen genug Items haben
        # strong = wirklich dominant
        min_items_strong = max(8, int(0.12 * len(mid_items)))
        # weak = erlaubt auch kürzere Spalten (z.B. rechte Spalte weniger Inhalt)
        min_items_weak = max(4, int(0.05 * len(mid_items)))

        strong = [c for c in clusters if c["n"] >= min_items_strong]
        weak = [c for c in clusters if c["n"] >= min_items_weak]

        # Wenn wir 3 Cluster haben, die wirklich weit genug auseinander liegen -> 3 Spalten.
        if len(weak) >= 3:
            xs = [c["x"] for c in weak]
            xs.sort()
            gaps = [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]
            # mind. zwei deutliche Abstände -> 3 echte Spalten
            big_gaps = sum(1 for g in gaps if g >= max(120.0, 0.18 * W))
            if big_gaps >= 2:
                return 3

        if len(strong) <= 1:
            return 1
        if len(strong) == 2:
            return 2
        return 3

    strong_cols = _estimate_strong_columns(mid_text)

    if strong_cols <= 2 and len(sep_x) < 2:
        mid = W / 2.0

        def is_centered_spanner(dbb):
            w = (dbb[2] - dbb[0])
            x_center = (dbb[0] + dbb[2]) / 2.0

            # wirklich sehr breite Zeilen
            if w >= 0.72 * W:
                return True

            # zentrierte Zwischenüberschrift über beiden Spalten
            if abs(x_center - (W / 2.0)) <= 0.14 * W and w >= 0.28 * W:
                return True

            return False

        def assign_two_col(dbb):
            x0, _, x1, _ = dbb
            gutter = max(20.0, 0.03 * W)

            if x1 <= mid - gutter:
                return 0  # links
            if x0 >= mid + gutter:
                return 1  # rechts

            x_center = (x0 + x1) / 2.0
            return 0 if x_center < mid else 1

        # ------------------------------------------
        # NEU: erst "echten" Beginn der Spalten finden
        # ------------------------------------------
        body_candidates = []
        for r, bb, dbb in midband:
            if is_fullwidth(dbb):
                continue
            if is_centered_spanner(dbb):
                continue

            h = dbb[3] - dbb[1]
            if h >= MIN_H:
                body_candidates.append((r, bb, dbb))

        if body_candidates:
            first_body_y = min(dbb[1] for _, _, dbb in body_candidates)
        else:
            first_body_y = body_top

        Y_PAD = max(10.0, 0.9 * med_h)

        top_mid = []
        left_col = []
        right_col = []

        for r, bb, dbb in midband:
            # Volle Breite immer oben behalten
            if is_fullwidth(dbb):
                top_mid.append((r, bb, dbb))
                continue

            # Zentrierte Spanner nur dann oben behalten,
            # wenn sie wirklich ÜBER dem eigentlichen Spaltenbeginn liegen
            if is_centered_spanner(dbb) and dbb[3] < (first_body_y - Y_PAD):
                top_mid.append((r, bb, dbb))
                continue

            col_idx = assign_two_col(dbb)
            if col_idx == 0:
                left_col.append((r, bb, dbb))
            else:
                right_col.append((r, bb, dbb))

        top_mid_sorted = sort_y_then_x(top_mid)
        left_sorted = sort_y_then_x(left_col)
        right_sorted = sort_y_then_x(right_col)

        core = []
        core.extend(top_mid_sorted)

        if rev_cols:
            core.extend(right_sorted)
            core.extend(left_sorted)
        else:
            core.extend(left_sorted)
            core.extend(right_sorted)

        return [r for r, _, _ in header_sorted] + [r for r, _, _ in core] + [r for r, _, _ in footer_sorted]

    # Wenn explizite Separatoren da sind, nutzen wir sie als Grenzen:
    # Spalten = Anzahl(Separatoren) + 1
    if len(sep_x) >= 1:
        bounds = sep_x[:]  # jede Position ist eine x-Grenze
        ncols = len(bounds) + 1

        GUTTER = max(18.0, 0.01 * W)  # Schutzbereich um die Trennlinie

        def col_index_for(dbb):
            if is_fullwidth(dbb):
                return 0

            x0, _, x1, _ = dbb

            # 1) harte Kantenentscheidung
            for i, b in enumerate(bounds):
                if x1 <= b - GUTTER:
                    return i

            for i, b in enumerate(bounds):
                if x0 < b + GUTTER:
                    break
            else:
                return ncols - 1

            # 2) weicher Fallback nur für Grenzfälle
            x_center = (x0 + x1) / 2.0
            for i, b in enumerate(bounds):
                if x_center < b:
                    return i
            return ncols - 1

        cols = [[] for _ in range(ncols)]
        for r, bb, dbb in midband:
            cols[col_index_for(dbb)].append((r, bb, dbb))

    else:
        # Keine expliziten Separatoren: nach linker Kante x0 (entzerrt) clustern, robust gegen Schräglage/Einrückung
        x_threshold = max(55.0, 0.07 * W)  # etwas größer -> toleranter bei Schräglage
        indent_dx = max(30.0, 0.05 * W)  # Einrückungen aggressiver zusammenführen
        min_items_for_real_col = max(10, int(0.12 * len(mid_text)))  # stärkere Evidenz verlangen

        clusters = []  # {"x": mean_x0, "items":[...]}
        for r, bb, dbb in mid_text:
            x0 = dbb[0]
            placed = False
            for c in clusters:
                if abs(c["x"] - x0) <= x_threshold:
                    c["items"].append((r, bb, dbb))
                    c["x"] = (c["x"] * 0.85) + (x0 * 0.15)
                    placed = True
                    break
            if not placed:
                clusters.append({"x": float(x0), "items": [(r, bb, dbb)]})

        clusters.sort(key=lambda c: c["x"])

        # --- NEU: "Einrückungs-/Zentrier"-Cluster bei starkem horizontalen Überlapp zusammenführen ---
        def q(vals, p):
            if not vals:
                return None
            vs = sorted(vals)
            k = (len(vs) - 1) * p
            f = int(k)
            c = min(f + 1, len(vs) - 1)
            if f == c:
                return vs[f]
            return vs[f] + (vs[c] - vs[f]) * (k - f)

        def span(c):
            lefts = [it[2][0] for it in c["items"]]  # dbb x0
            rights = [it[2][2] for it in c["items"]]  # dbb x1
            l = q(lefts, 0.20) if lefts else c["x"]
            r = q(rights, 0.80) if rights else c["x"]
            if l is None or r is None:
                return (c["x"], c["x"])
            return (float(l), float(r))

        def should_merge(c1, c2):
            l1, r1 = span(c1)
            l2, r2 = span(c2)
            w1 = max(1.0, r1 - l1)
            w2 = max(1.0, r2 - l2)

            # Überlappungsgrad (Einrückung/Zentrierung => hoch, echte Spalten => nahe 0)
            overlap = max(0.0, min(r1, r2) - max(l1, l2))
            overlap_ratio = overlap / max(1.0, min(w1, w2))

            dx = abs(c2["x"] - c1["x"])

            # Wenn in x relativ nah ODER eines im anderen liegt UND starker Überlapp -> zusammenführen
            close = dx <= max(80.0, 0.12 * W)
            inside = (l2 >= l1 - 0.03 * W and r2 <= r1 + 0.03 * W) or (l1 >= l2 - 0.03 * W and r1 <= r2 + 0.03 * W)

            return (overlap_ratio >= 0.55) and (close or inside)

        merged_pass = True
        while merged_pass and len(clusters) > 1:
            merged_pass = False
            new_list = []
            i = 0
            while i < len(clusters):
                if i < len(clusters) - 1 and should_merge(clusters[i], clusters[i + 1]):
                    a = clusters[i]
                    b = clusters[i + 1]
                    a["items"].extend(b["items"])
                    # update mean x0
                    a["x"] = float(sum(it[2][0] for it in a["items"])) / max(1, len(a["items"]))
                    new_list.append(a)
                    i += 2
                    merged_pass = True
                else:
                    new_list.append(clusters[i])
                    i += 1
            clusters = new_list

        clusters.sort(key=lambda c: c["x"])

        # Kleine "Einrückungs"-Cluster in den nächstgelegenen echten Cluster einhängen
        def is_real(c):
            return len(c["items"]) >= min_items_for_real_col

        merged = clusters[:]
        for c in list(merged):
            if is_real(c):
                continue
            # nearest real cluster
            best = None
            best_d = None
            for t in merged:
                if t is c or not is_real(t):
                    continue
                d = abs(t["x"] - c["x"])
                if best_d is None or d < best_d:
                    best, best_d = t, d
            if best is not None and best_d is not None and best_d <= indent_dx:
                best["items"].extend(c["items"])
                merged = [z for z in merged if z is not c]

        merged.sort(key=lambda c: c["x"])

        # Wenn es weiterhin wie "eine Spalte mit Einrückungen" aussieht -> als einspaltig behandeln.
        if len(merged) >= 2:
            sizes = sorted([len(c["items"]) for c in merged], reverse=True)
            biggest = sizes[0]
            ratio = biggest / max(1, sum(sizes))
            # if one cluster dominates strongly -> single column
            if ratio >= 0.70:
                merged = [max(merged, key=lambda c: len(c["items"]))]

        if len(merged) <= 1:
            # Einspaltig -> einfach nach y, dann x sortieren
            core = sort_y_then_x(midband)
            return [r for r, _, _ in header_sorted] + [r for r, _, _ in core] + [r for r, _, _ in footer_sorted]

        # Grenzen zwischen Cluster-Starts berechnen
        col_starts = [c["x"] for c in merged]
        bounds = [(col_starts[i] + col_starts[i + 1]) / 2.0 for i in range(len(col_starts) - 1)]

        def col_index_for(dbb):
            if is_fullwidth(dbb):
                return 0

            x0, _, x1, _ = dbb
            gutter = max(18.0, 0.025 * W)

            # zuerst über echte Box-Ausdehnung entscheiden
            for i, b in enumerate(bounds):
                if x1 <= b - gutter:
                    return i

            # dann Grenzfall über Mittelpunkt
            x_center = (x0 + x1) / 2.0
            for i, b in enumerate(bounds):
                if x_center < b:
                    return i

            return len(col_starts) - 1

        cols = [[] for _ in range(len(col_starts))]
        for r, bb, dbb in midband:
            cols[col_index_for(dbb)].append((r, bb, dbb))

        # ---------- ZWEITER DURCHLAUF: zentrierte Überschriften über Spalten -> Header ----------
        def body_like(dbb):
            h = (dbb[3] - dbb[1])
            w = (dbb[2] - dbb[0])
            if h < MIN_H:
                return False
            if is_fullwidth(dbb):
                return False
            return w >= 0.10 * W

        # oberste "echte" Textzeile in den Spalten finden
        col_tops = []
        for col in cols:
            ys = [it[2][1] for it in col if body_like(it[2])]
            if ys:
                col_tops.append(min(ys))
        first_body_y = min(col_tops) if col_tops else body_top

        def is_centered_heading(dbb):
            w = (dbb[2] - dbb[0])
            if w > 0.85 * W:
                # sehr breit -> eher normaler Absatz; den lassen wir hier in Ruhe
                return False
            x_center = (dbb[0] + dbb[2]) / 2.0
            return abs(x_center - (W / 2.0)) <= 0.18 * W and w >= 0.24 * W

        promote = []
        keep_mid = []
        Y_PAD = max(10.0, 0.9 * med_h)

        for r, bb, dbb in midband:
            # deutlich oberhalb der ersten Spaltenzeile UND zentriert -> header
            if (dbb[3] < (first_body_y - Y_PAD)) and is_centered_heading(dbb):
                promote.append((r, bb, dbb))
            else:
                keep_mid.append((r, bb, dbb))

        if promote:
            # in header aufnehmen
            header_sorted = sort_y_then_x(header + promote)
            midband = keep_mid

            # cols NEU aus midband aufbauen
            cols = [[] for _ in range(len(col_starts))]
            for r, bb, dbb in midband:
                cols[col_index_for(dbb)].append((r, bb, dbb))

    # ---------- innerhalb jeder Spalte sortieren ----------
    def sort_col(col):
        return sorted(col, key=lambda x: cy(x[2]), reverse=rev_y)

    cols = [sort_col(c) for c in cols]

    col_order = list(range(len(cols)))
    if rev_cols:
        col_order = list(reversed(col_order))

    core = []
    for ci in col_order:
        core.extend(cols[ci])

    return [r for r, _, _ in header_sorted] + [r for r, _, _ in core] + [r for r, _, _ in footer_sorted]

def clamp_bbox(bb: Tuple[int, int, int, int], w: int, h: int) -> Optional[Tuple[int, int, int, int]]:
    x0, y0, x1, y1 = bb
    return (max(0, min(w - 1, x0)), max(0, min(h - 1, y0)),
            max(0, min(w, x1)), max(0, min(h, y1)))

def _safe_int(v, default=0):
    try:
        return int(v)
    except Exception:
        return default

def _force_text(value):
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)

def _error_log_path() -> str:
    return os.path.join(os.getcwd(), "bottled_kraken_error.log")

def _cleanup_old_error_log(max_age_days: int = 20):
    log_path = _error_log_path()

    try:
        if not os.path.exists(log_path):
            return

        max_age_seconds = int(max_age_days * 24 * 60 * 60)
        file_age = time.time() - os.path.getmtime(log_path)

        if file_age >= max_age_seconds:
            os.remove(log_path)
    except Exception:
        pass

def _append_error_log_entry(msg: str):
    log_path = _error_log_path()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("\n\n" + "=" * 80 + "\n")
            f.write(f"[{timestamp}] Unbehandelte Ausnahme\n")
            f.write("-" * 80 + "\n")
            f.write(msg.rstrip() + "\n")
    except Exception:
        pass

def _install_exception_hook():
    _cleanup_old_error_log(max_age_days=20)

    def handle_exception(exc_type, exc_value, exc_tb):
        msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        _append_error_log_entry(msg)

        try:
            QMessageBox.critical(None, "Fehler", msg)
        except Exception:
            try:
                print(msg)
            except Exception:
                pass

    sys.excepthook = handle_exception

def _clean_ocr_text(text: Any) -> str:
    if text is None:
        return ""

    if isinstance(text, bytes):
        txt = text.decode("utf-8", errors="replace")
    else:
        txt = str(text)

    txt = txt.replace("\u00a0", " ")
    txt = txt.replace("\u200b", "")
    txt = txt.replace("\ufeff", "")

    txt = txt.replace("ſ", "s")
    txt = txt.replace("⸗", "-")
    txt = txt.replace("±", "+/-")

    txt = re.sub(r"[ \t\r\f\v]+", " ", txt)
    return txt.strip()

def _is_effectively_empty_ocr_text(text: Any) -> bool:
    return _clean_ocr_text(text) == ""

def _extract_json_payload(text: str):
    if not text:
        return None

    raw = _force_text(text).strip()
    raw = re.sub(r"^\s*```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```\s*$", "", raw)

    candidates = [raw]

    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        chunk = raw[start:end + 1]
        candidates.append(chunk)
        candidates.append(re.sub(r",(\s*[}\]])", r"\1", chunk))

    normalized = raw.replace("’", "'").replace("‘", "'")
    normalized = normalized.replace("„", "\"").replace("“", "\"").replace("”", "\"")
    candidates.append(normalized)

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except Exception:
            pass

    return None

def _extract_json_string_lines_object(text: str):
    data = _extract_json_payload(text)
    if isinstance(data, dict) and isinstance(data.get("lines"), list):
        lines = data["lines"]
        if all(isinstance(x, str) for x in lines):
            return lines
    return None

def _pil_to_data_url(
        im: Image.Image,
        max_side: int = 5000,
        image_format: str = "PNG",
        jpeg_quality: int = 85,
) -> str:
    im = im.convert("RGB")
    w, h = im.size

    scale = min(max_side / max(w, h), 1.0)
    if scale < 1.0:
        im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    buf = BytesIO()

    fmt = (image_format or "PNG").upper()
    if fmt == "JPEG":
        im.save(buf, format="JPEG", quality=int(jpeg_quality), optimize=True)
        mime = "image/jpeg"
    else:
        im.save(buf, format="PNG", optimize=True)
        mime = "image/png"

    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:{mime};base64,{b64}"

def _image_to_data_url(path: str) -> str:
    im = _load_image_gray(path)
    return _pil_to_data_url(im)

def _page_to_data_url(
        path: str,
        max_side: int = 5000,
        image_format: str = "PNG",
        jpeg_quality: int = 85,
) -> str:
    im = _load_image_color(path)
    return _pil_to_data_url(
        im,
        max_side=max_side,
        image_format=image_format,
        jpeg_quality=jpeg_quality,
    )

def _page_to_small_png_data_url(
        path: str,
        max_side: int = 1200,
) -> str:
    im = _load_image_color(path)

    w, h = im.size
    longest = max(w, h)
    if longest > max_side:
        scale = max_side / float(longest)
        im = im.resize(
            (max(1, int(w * scale)), max(1, int(h * scale))),
            Image.LANCZOS
        )

    return _pil_to_data_url(
        im,
        max_side=max_side,
        image_format="PNG",
    )

def _crop_block_to_data_url_context(
        path: str,
        recs: List["RecordView"],
        start: int,
        end: int,
        pad_x: int = 40,
        pad_y: int = 35,
) -> str:
    im = _load_image_color(path)
    boxes = [rv.bbox for rv in recs[start:end] if rv.bbox]

    if not boxes:
        return _pil_to_data_url(im, max_side=768)

    x0 = max(0, min(bb[0] for bb in boxes) - pad_x)
    y0 = max(0, min(bb[1] for bb in boxes) - pad_y)
    x1 = min(im.size[0], max(bb[2] for bb in boxes) + pad_x)
    y1 = min(im.size[1], max(bb[3] for bb in boxes) + pad_y)

    crop = im.crop((x0, y0, x1, y1))
    return _pil_to_data_url(crop, max_side=1600)

def _crop_single_line_to_data_url(
        path: str,
        rv: "RecordView",
        pad_x: int = 14,
        pad_y: int = 6,
        extra_context_y: int = 0,
) -> str:
    im = _load_image_color(path)

    if not rv.bbox:
        return _pil_to_data_url(im, max_side=1600)

    x0, y0, x1, y1 = rv.bbox

    x0 = max(0, x0 - pad_x)
    y0 = max(0, y0 - pad_y - extra_context_y)
    x1 = min(im.size[0], x1 + pad_x)
    y1 = min(im.size[1], y1 + pad_y + extra_context_y)

    crop = im.crop((x0, y0, x1, y1))
    return _pil_to_data_url(crop, max_side=1600)

# -----------------------------
# HILFSFUNKTIONEN FÜR TABELLEN-EXPORT
# -----------------------------
def cluster_columns(records: List[RecordView], x_threshold: int = 45):
    cols = []
    for r in records:
        if not r.bbox:
            continue
        x0 = r.bbox[0]
        placed = False
        for c in cols:
            if abs(c["x"] - x0) <= x_threshold:
                c["items"].append(r)
                c["x"] = int((c["x"] * 0.8) + (x0 * 0.2))
                placed = True
                break
        if not placed:
            cols.append({"x": x0, "items": [r]})
    cols.sort(key=lambda c: c["x"])
    return [c["items"] for c in cols]

def is_same_visual_row(a: RecordView, b: RecordView, page_width: int) -> bool:
    if not a.bbox or not b.bbox:
        return False

    ax0, ay0, ax1, ay1 = a.bbox
    bx0, by0, bx1, by1 = b.bbox

    # y-Ähnlichkeit
    if abs(ay0 - by0) > 12:
        return False

    w = max(1, int(page_width))
    mid = w // 2

    aw = ax1 - ax0
    bw = bx1 - bx0

    # Wenn beide Boxen "Textzeilen-breit" sind und in unterschiedlichen Spalten liegen,
    # dann sind das KEINE Tabellenzellen derselben Zeile.
    textish_a = aw >= int(0.30 * w)
    textish_b = bw >= int(0.30 * w)

    a_left = (ax0 < mid and ax1 <= mid + int(0.05 * w))
    b_right = (bx1 > mid and bx0 >= mid - int(0.05 * w))
    b_left = (bx0 < mid and bx1 <= mid + int(0.05 * w))
    a_right = (ax1 > mid and ax0 >= mid - int(0.05 * w))

    if textish_a and textish_b and ((a_left and b_right) or (b_left and a_right)):
        return False

    return True

def group_rows_by_y(records: List[RecordView], page_width: int):
    recs = [r for r in records if r.bbox]
    if not recs:
        return []

    w = max(1, int(page_width))

    # robuste Zeilenhöhe
    hs = sorted([(rv.bbox[3] - rv.bbox[1]) for rv in recs if (rv.bbox[3] - rv.bbox[1]) > 0])
    med_h = hs[len(hs) // 2] if hs else 14

    # enger = "Abstand geringer" (striktere Gruppierung)
    y_tol = max(10, int(0.45 * med_h))

    # Neu: horizontale Separatoren (_ / - / ─) erkennen
    sep_y: List[float] = []
    filtered_recs: List[RecordView] = []
    for rv in recs:
        txt = (rv.text or "").strip()
        x0, y0, x1, y1 = rv.bbox
        bw = (x1 - x0)
        bh = (y1 - y0)

        is_hsep = bool(HSEP_RE.match(txt)) and (bw >= 0.55 * w) and (bh <= 0.7 * med_h)
        if is_hsep:
            sep_y.append((y0 + y1) / 2.0)
        else:
            filtered_recs.append(rv)

    sep_y.sort()
    recs = filtered_recs

    def center_y(rv):
        x0, y0, x1, y1 = rv.bbox
        return (y0 + y1) / 2.0

    sorted_recs = sorted(recs, key=lambda rv: (center_y(rv), rv.bbox[0]))

    rows: List[List[RecordView]] = []
    row_y: List[float] = []
    row_band: List[int] = []

    def band_index(cy: float) -> int:
        # wie viele Separatoren liegen oberhalb? -> Band 0..n
        idx = 0
        for y in sep_y:
            if cy > y:
                idx += 1
            else:
                break
        return idx

    for r in sorted_recs:
        cy = center_y(r)
        b = band_index(cy)
        placed = False

        for i in range(len(rows)):
            if row_band[i] != b:
                continue
            if abs(cy - row_y[i]) <= y_tol:
                rows[i].append(r)
                row_y[i] = row_y[i] * 0.85 + cy * 0.15
                placed = True
                break

        if not placed:
            rows.append([r])
            row_y.append(cy)
            row_band.append(b)

    for row in rows:
        row.sort(key=lambda rv: rv.bbox[0])
    return rows

def table_to_rows_two_columns(records: List[RecordView], page_width: int) -> List[List[str]]:
    #   Erzwingt exakt 2 Spalten anhand Seitenmitte.
    #   Verhindert "3. Spalte" durch Einrückungen/Ausreißer.
    mid = max(1, int(page_width)) // 2
    rows = group_rows_by_y(records, page_width)

    grid: List[List[str]] = []
    for row in rows:
        left_parts = []
        right_parts = []
        for rv in row:
            if not rv.bbox:
                continue
            x0 = rv.bbox[0]
            if x0 < mid:
                left_parts.append(rv.text)
            else:
                right_parts.append(rv.text)

        grid.append([" ".join(left_parts).strip(), " ".join(right_parts).strip()])

    # Optional: kurze Restfragmente an vorige Zeile hängen
    merged: List[List[str]] = []
    for r in grid:
        if merged:
            if (not r[0]) and r[1] and len(r[1]) <= 20 and (not merged[-1][1].endswith(".")):
                merged[-1][1] = (merged[-1][1] + " " + r[1]).strip()
                continue
        merged.append(r)

    return merged

def table_to_rows(records: List[RecordView], page_width: int) -> List[List[str]]:
    # Wenn der Text explizite Trenner enthält, nutze die als "harte" Spalten,
    # statt aus BBox-Positionen eine Tabelle zu raten.
    has_pipes = any(
        (rv.text and (
                any(ch in rv.text for ch in ("|", "│", "┃")) or
                re.search(r"(?:_{2,}|\s_\s)", rv.text)  # "__" oder " _ " als Trenner
        ))
        for rv in records
    )

    if has_pipes:
        rows = group_rows_by_y(records, page_width)
        grid = []
        for row in rows:
            # links->rechts sortieren
            row = [rv for rv in row if rv.bbox]
            row.sort(key=lambda rv: rv.bbox[0] if rv.bbox else 0)

            cells: List[str] = []
            for rv in row:
                txt = (rv.text or "").strip()
                if not txt:
                    continue
                # reine Separator-Records ignorieren
                if re.fullmatch(r"[\|\u2502\u2503]+", txt):
                    continue
                # split an pipes
                if any(ch in txt for ch in ("|", "│", "┃")):
                    parts = re.split(r"\s*(?:[\|\u2502\u2503]+|_{2,}|\s_\s)\s*", txt)
                    parts = [p.strip() for p in parts if p.strip()]
                    if parts:
                        cells.extend(parts)
                else:
                    cells.append(txt)

            grid.append(cells if cells else [""])
        return grid

    # sonst: dein bestehender bbox-basierter Tabellenmodus
    rows = group_rows_by_y(records, page_width)
    cols = cluster_columns(records)

    # Wenn cluster_columns "3 Spalten" liefert, aber wir eigentlich 2-Spalten-Layout haben,
    # erzwinge 2 Spalten wie im alten Code:
    if len(cols) >= 3:
        # Heuristik: wenn zwei größte Cluster dominieren -> 2 Spalten erzwingen
        sizes = sorted([len(c) for c in cols], reverse=True)
        if sizes and (sizes[0] + (sizes[1] if len(sizes) > 1 else 0)) >= 0.80 * sum(sizes):
            return table_to_rows_two_columns(records, page_width)

    col_x = []
    for col in cols:
        xs = [rv.bbox[0] for rv in col if rv.bbox]
        col_x.append(int(sum(xs) / max(1, len(xs))) if xs else 0)

    def nearest_col(x: int) -> int:
        if not col_x:
            return 0
        best_i = 0
        best_d = abs(col_x[0] - x)
        for i in range(1, len(col_x)):
            d = abs(col_x[i] - x)
            if d < best_d:
                best_d = d
                best_i = i
        return best_i

    grid = []
    for row in rows:
        line = [""] * max(1, len(col_x))
        for rv in row:
            if not rv.bbox:
                continue
            c = nearest_col(rv.bbox[0])
            if line[c]:
                line[c] += " " + rv.text
            else:
                line[c] = rv.text
        grid.append(line)
    return grid

# -----------------------------
# Wartebereich
# -----------------------------
class QueueCheckDelegate(QStyledItemDelegate):
    def _checkbox_rect(self, option, widget):
        style = widget.style() if widget else QApplication.style()

        box_opt = QStyleOptionButton()
        indicator = style.subElementRect(QStyle.SE_CheckBoxIndicator, box_opt, widget)

        return QStyle.alignedRect(
            option.direction,
            Qt.AlignCenter,
            indicator.size(),
            option.rect
        )

    def paint(self, painter, option, index):
        value = index.data(Qt.CheckStateRole)
        if value is None:
            super().paint(painter, option, index)
            return

        # Zellenhintergrund / Selektion normal von Qt zeichnen lassen
        view_opt = QStyleOptionViewItem(option)
        self.initStyleOption(view_opt, index)
        view_opt.text = ""
        view_opt.icon = QIcon()
        view_opt.features &= ~QStyleOptionViewItem.HasCheckIndicator
        super().paint(painter, view_opt, index)

        style = option.widget.style() if option.widget else QApplication.style()

        box_opt = QStyleOptionButton()
        box_opt.state |= QStyle.State_Enabled

        if int(value) == str(Qt.Checked):
            box_opt.state |= QStyle.State_On
        else:
            box_opt.state |= QStyle.State_Off

        if option.state & QStyle.State_MouseOver:
            box_opt.state |= QStyle.State_MouseOver

        box_opt.rect = self._checkbox_rect(option, option.widget)

        style.drawPrimitive(QStyle.PE_IndicatorCheckBox, box_opt, painter, option.widget)

    def editorEvent(self, event, model, option, index):
        flags = index.flags()
        if not (flags & Qt.ItemIsUserCheckable) or not (flags & Qt.ItemIsEnabled):
            return False

        # Tastatur
        if event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Space, Qt.Key_Select):
                current = index.data(Qt.CheckStateRole)
                new_state = Qt.Unchecked if int(current) == int(Qt.Checked) else Qt.Checked
                return model.setData(index, new_state, Qt.CheckStateRole)
            return False

        # Doppelklick nicht separat toggeln
        if event.type() == QEvent.MouseButtonDblClick:
            return True

        # Maus nur innerhalb der zentrierten Checkbox
        if event.type() == QEvent.MouseButtonRelease:
            if event.button() != Qt.LeftButton:
                return False

            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            if not self._checkbox_rect(option, option.widget).contains(pos):
                return False

            current = index.data(Qt.CheckStateRole)
            new_state = Qt.Unchecked if int(current) == int(Qt.Checked) else Qt.Checked
            return model.setData(index, new_state, Qt.CheckStateRole)

        return False

# -----------------------------
# SKALIERBARES / VERSCHIEBBARES RECHTECK-ITEM
# -----------------------------
class ResizableRectItem(QGraphicsRectItem):
    HANDLE_PAD = 6.0

    def __init__(
            self,
            rect: QRectF,
            idx: int,
            on_changed: Callable[[int, QRectF], None],
            on_clicked: Optional[Callable[[int], None]] = None,
            on_double_clicked: Optional[Callable[[int], None]] = None
    ):
        super().__init__(rect)
        self.idx = idx
        self._on_changed = on_changed
        self._on_clicked = on_clicked
        self._on_double_clicked = on_double_clicked

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsRectItem.ItemIsMovable, True)

        self._mode = "none"
        self._resize_edges = (False, False, False, False)  # L,T,R,B
        self._press_scene_pos: Optional[QPointF] = None
        self._press_rect: Optional[QRectF] = None
        self._press_item_pos: Optional[QPointF] = None

    def _hit_test_edges(self, pos: QPointF) -> Tuple[bool, bool, bool, bool]:
        r = self.rect()
        x, y = pos.x(), pos.y()
        l = abs(x - r.left()) <= self.HANDLE_PAD
        t = abs(y - r.top()) <= self.HANDLE_PAD
        rr = abs(x - r.right()) <= self.HANDLE_PAD
        b = abs(y - r.bottom()) <= self.HANDLE_PAD
        return l, t, rr, b

    def hoverMoveEvent(self, event):
        l, t, r, b = self._hit_test_edges(event.pos())
        if (l and t) or (r and b):
            self.setCursor(Qt.SizeFDiagCursor)
        elif (r and t) or (l and b):
            self.setCursor(Qt.SizeBDiagCursor)
        elif l or r:
            self.setCursor(Qt.SizeHorCursor)
        elif t or b:
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.OpenHandCursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setSelected(True)

            self._press_scene_pos = event.scenePos()
            self._press_rect = QRectF(self.rect())
            self._press_item_pos = QPointF(self.pos())

            l, t, r, b = self._hit_test_edges(event.pos())
            self._resize_edges = (l, t, r, b)

            if any(self._resize_edges):
                self._mode = "resize"
            else:
                self._mode = "move"

            super().mousePressEvent(event)

            if callable(self._on_clicked):
                self._on_clicked(self.idx)

            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._mode == "resize" and self._press_scene_pos is not None and self._press_rect is not None:
            delta = event.scenePos() - self._press_scene_pos
            rect = QRectF(self._press_rect)

            l, t, r, b = self._resize_edges

            if l:
                rect.setLeft(rect.left() + delta.x())
            if r:
                rect.setRight(rect.right() + delta.x())
            if t:
                rect.setTop(rect.top() + delta.y())
            if b:
                rect.setBottom(rect.bottom() + delta.y())

            min_w = 5.0
            min_h = 5.0

            if rect.width() < min_w:
                if l:
                    rect.setLeft(rect.right() - min_w)
                else:
                    rect.setRight(rect.left() + min_w)

            if rect.height() < min_h:
                if t:
                    rect.setTop(rect.bottom() - min_h)
                else:
                    rect.setBottom(rect.top() + min_h)

            self.setRect(rect.normalized())
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

        if self._mode in ("resize", "move"):
            self._mode = "none"
            if callable(self._on_changed):
                new_scene_rect = self.mapRectToScene(self.rect()).normalized()
                self._on_changed(self.idx, new_scene_rect)
            event.accept()
            return

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            try:
                if callable(self._on_double_clicked):
                    self._on_double_clicked(self.idx)
            except Exception:
                pass
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

# -----------------------------
# WARTEBEREICH-TABELLE MIT DRAG & DROP
# -----------------------------
class DropQueueTable(QTableWidget):
    files_dropped = Signal(list)
    table_resized = Signal()
    delete_pressed = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDragDropOverwriteMode(False)
        self.setDragDropMode(QAbstractItemView.DropOnly)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.table_resized.emit()

    def keyPressEvent(self, event):
        super().keyPressEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if not event.mimeData().hasUrls():
            event.ignore()
            return

        for u in event.mimeData().urls():
            p = u.toLocalFile()
            if p and os.path.exists(p) and is_supported_drop_or_paste_file(p):
                event.acceptProposedAction()
                return

        event.ignore()

    def dragMoveEvent(self, event):
        if not event.mimeData().hasUrls():
            event.ignore()
            return

        for u in event.mimeData().urls():
            p = u.toLocalFile()
            if p and os.path.exists(p) and is_supported_drop_or_paste_file(p):
                event.acceptProposedAction()
                return

        event.ignore()

    def dropEvent(self, event: QDropEvent):
        if not event.mimeData().hasUrls():
            event.ignore()
            return

        files = []
        for u in event.mimeData().urls():
            p = u.toLocalFile()
            if p and os.path.exists(p) and is_supported_drop_or_paste_file(p):
                files.append(p)

        if files:
            self.files_dropped.emit(files)
            event.acceptProposedAction()
        else:
            event.ignore()

# -----------------------------
# ZEILENLISTE (Entf + Drag&Drop zum Umordnen)
# -----------------------------
class LinesTreeWidget(QTreeWidget):
    delete_pressed = Signal()
    reorder_committed = Signal(list, int)  # new_order (old indices), current_row after drop

    def __init__(self, tr_func=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tr_func = tr_func

        self.setColumnCount(2)
        self.setHeaderLabels(["#", self._tr_func("lines_tree_header") if self._tr_func else ""])
        self.setRootIsDecorated(False)
        self.setUniformRowHeights(True)

        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDragDropMode(QAbstractItemView.InternalMove)

        self.header().setStretchLastSection(True)
        self.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.header().setSectionResizeMode(1, QHeaderView.Stretch)

        # NEU:
        self.header().setDefaultAlignment(Qt.AlignCenter)

        # Basisdarstellung wird vom MainWindow-Theme gesetzt
        self.setAlternatingRowColors(True)
        self.setIndentation(0)
        self.setStyleSheet("")

    def edit(self, index, trigger, event):
        # Spalte 0 nie editierbar, nur Inhalt
        if index.isValid() and index.column() == 0:
            return False
        return super().edit(index, trigger, event)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy):
            self.copy_selected_contents()
            event.accept()
            return

        if event.key() == Qt.Key_Delete:
            self.delete_pressed.emit()
            event.accept()
            return

        super().keyPressEvent(event)

    def copy_selected_contents(self):
        rows = self.selected_line_rows()
        if not rows:
            return

        parts = []
        for row in rows:
            it = self.topLevelItem(row)
            if it:
                parts.append(it.text(1))

        QApplication.clipboard().setText("\n".join(parts))

    def selected_line_rows(self) -> List[int]:
        rows = set()
        for idx in self.selectedIndexes():
            rows.add(idx.row())
        return sorted(rows)

    def currentRow(self) -> int:
        it = self.currentItem()
        if it is None:
            return -1
        return self.indexOfTopLevelItem(it)

    def setCurrentRow(self, row: int):
        if 0 <= row < self.topLevelItemCount():
            self.setCurrentItem(self.topLevelItem(row))

    def count(self) -> int:
        return self.topLevelItemCount()

    def row(self, item: QTreeWidgetItem) -> int:
        return self.indexOfTopLevelItem(item)

    def row_item(self, row: int) -> Optional[QTreeWidgetItem]:
        return self.topLevelItem(row)

    def dropEvent(self, event):
        super().dropEvent(event)

        order = []
        for i in range(self.topLevelItemCount()):
            it = self.topLevelItem(i)
            idx = it.data(0, Qt.UserRole)
            if idx is None:
                idx = i
            order.append(int(idx))

        self.reorder_committed.emit(order, self.currentRow())


# -----------------------------
# DIALOG ZUM BEARBEITEN DER OVERLAY-BOX
# -----------------------------
class OverlayBoxDialog(QDialog):
    def __init__(self, tr, img_w: int, img_h: int, bbox: Optional[Tuple[int, int, int, int]] = None, parent=None):
        super().__init__(parent)
        self._tr = tr
        self.setWindowTitle(tr("dlg_box_title"))
        self._img_w = max(1, int(img_w))
        self._img_h = max(1, int(img_h))

        x0, y0, x1, y1 = (0, 0, min(100, self._img_w), min(30, self._img_h))
        if bbox:
            x0, y0, x1, y1 = bbox

        lay = QVBoxLayout(self)
        form = QFormLayout()

        self.sp_x0 = QSpinBox()
        self.sp_y0 = QSpinBox()
        self.sp_x1 = QSpinBox()
        self.sp_y1 = QSpinBox()

        for sp in (self.sp_x0, self.sp_y0, self.sp_x1, self.sp_y1):
            sp.setRange(0, 1000000)

        self.sp_x0.setRange(0, self._img_w)
        self.sp_x1.setRange(0, self._img_w)
        self.sp_y0.setRange(0, self._img_h)
        self.sp_y1.setRange(0, self._img_h)

        self.sp_x0.setValue(max(0, min(self._img_w, int(x0))))
        self.sp_y0.setValue(max(0, min(self._img_h, int(y0))))
        self.sp_x1.setValue(max(0, min(self._img_w, int(x1))))
        self.sp_y1.setValue(max(0, min(self._img_h, int(y1))))

        form.addRow(tr("dlg_box_left"), self.sp_x0)
        form.addRow(tr("dlg_box_top"), self.sp_y0)
        form.addRow(tr("dlg_box_right"), self.sp_x1)
        form.addRow(tr("dlg_box_bottom"), self.sp_y1)

        lay.addLayout(form)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText(tr("dlg_box_apply"))
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def get_bbox(self) -> Tuple[int, int, int, int]:
        x0 = int(self.sp_x0.value())
        y0 = int(self.sp_y0.value())
        x1 = int(self.sp_x1.value())
        y1 = int(self.sp_y1.value())
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        if x1 <= x0:
            x1 = min(self._img_w, x0 + 1)
        if y1 <= y0:
            y1 = min(self._img_h, y0 + 1)
        x0 = max(0, min(self._img_w - 1, x0))
        y0 = max(0, min(self._img_h - 1, y0))
        x1 = max(1, min(self._img_w, x1))
        y1 = max(1, min(self._img_h, y1))
        return (x0, y0, x1, y1)


# -----------------------------
# BILD-CANVAS MIT KONTEXTMENÜ + DOPPELKLICK-AUSWAHL
# -----------------------------
class ImageCanvas(QGraphicsView):
    rect_clicked = Signal(int)
    rect_changed = Signal(int, QRectF)  # idx, new rect in scene coords
    files_dropped = Signal(list)
    canvas_clicked = Signal()
    box_drawn = Signal(QRectF)

    overlay_add_draw_requested = Signal(QPointF)
    overlay_edit_requested = Signal(int)
    overlay_delete_requested = Signal(int)
    overlay_select_requested = Signal(int)
    box_split_requested = Signal(int, float)  # idx, split_x in scene coords

    overlay_multi_selected = Signal(list)  # Liste von idx

    def __init__(self, tr_func=None):
        super().__init__()
        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.NoDrag)
        self._space_panning = False

        # NEU: Maus-Panning (LMB drag)
        self._mouse_panning = False
        self._pan_start = QPoint()
        self._pan_start_h = 0
        self._pan_start_v = 0

        # Drag & Drop
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)

        self._zoom = 1.0
        self._pixmap_item = None

        self._rects: Dict[int, QGraphicsRectItem] = {}
        self._labels: Dict[int, QGraphicsSimpleTextItem] = {}
        self._selected_idx: Optional[int] = None
        self._selected_indices: set[int] = set()
        self._bg_color = QColor("#333")

        self._pen_normal = QPen(QColor("#ff3b30"), 2)
        self._pen_selected = QPen(QColor("#0a84ff"), 3)
        self._brush_fill = QBrush(QColor(255, 59, 48, 30))
        self._brush_selected = QBrush(QColor(10, 132, 255, 60))

        self._drop_text = None
        self.tr_func = tr_func

        # Box-Zeichenmodus
        self._draw_mode = False
        self._draw_start = None
        self._draw_rect_item: Optional[QGraphicsRectItem] = None
        self._pen_draw = QPen(QColor("#00ff7f"), 2)
        self._brush_draw = QBrush(QColor(0, 255, 127, 40))

        # Multi-Selection per Mausziehen
        self._selection_mode = False
        self._selection_start = None
        self._selection_rect_item: Optional[QGraphicsRectItem] = None
        self._pen_selection = QPen(QColor("#0a84ff"), 2, Qt.DashLine)
        self._brush_selection = QBrush(QColor(10, 132, 255, 40))

        # Nur aktiv, nachdem die OCR abgeschlossen ist
        self._overlay_enabled = False

        # Split-Modus für bestehende Boxen
        self._split_mode = False
        self._split_target_idx: Optional[int] = None
        self._split_preview_item: Optional[QGraphicsLineItem] = None
        self._split_pen = QPen(QColor("#ffd60a"), 2, Qt.DashLine)

        self._show_drop_hint()

    def _get_view_state(self):
        # Gibt (Transform, Szenen-Zentrumspunkt, Zoom-Skalar) zurück.
        try:
            t = self.transform()
            center = self.mapToScene(self.viewport().rect().center())
            z = float(t.m11())  # angenommen: gleichmäßige Skalierung
            return t, center, z
        except Exception:
            return None, None, None

    def _restore_view_state(self, t, center, z):
        try:
            if t is not None:
                self.setTransform(t)
            if center is not None:
                self.centerOn(center)
            # internen Zoom synchron halten (wheelEvent nutzt ihn)
            if z is not None:
                self._zoom = float(z)
            else:
                self._zoom = float(self.transform().m11())
        except Exception:
            pass

    @staticmethod
    def _event_point(event) -> QPoint:
        # Funktioniert über verschiedene PySide6-Versionen hinweg: manchmal gibt es event.position(), manchmal nicht.
        try:
            p = event.position()
            return p.toPoint()
        except Exception:
            try:
                return event.pos()
            except Exception:
                return QPoint(0, 0)

    def set_overlay_enabled(self, enabled: bool):
        self._overlay_enabled = bool(enabled)

    def set_theme(self, theme: str):
        if theme == "dark":
            self._bg_color = QColor("#1e1e1e")
            self._pen_normal.setColor(QColor("#ff3b30"))
            self._pen_selected.setColor(QColor("#0a84ff"))
        else:
            self._bg_color = QColor("#f2f2f2")
            self._pen_normal.setColor(QColor("#d00000"))
            self._pen_selected.setColor(QColor("#0000ff"))
        self.setBackgroundBrush(QBrush(self._bg_color))
        if self._pixmap_item and hasattr(self, "_last_recs"):
            self.refresh_overlays()
        else:
            self._show_drop_hint()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if not event.mimeData().hasUrls():
            event.ignore()
            return

        for u in event.mimeData().urls():
            p = u.toLocalFile()
            if p and os.path.exists(p) and is_supported_drop_or_paste_file(p):
                event.acceptProposedAction()
                return

        event.ignore()

    def dragMoveEvent(self, event):
        if not event.mimeData().hasUrls():
            event.ignore()
            return

        for u in event.mimeData().urls():
            p = u.toLocalFile()
            if p and os.path.exists(p) and is_supported_drop_or_paste_file(p):
                event.acceptProposedAction()
                return

        event.ignore()

    def dropEvent(self, event: QDropEvent):
        if not event.mimeData().hasUrls():
            event.ignore()
            return

        files = []
        for u in event.mimeData().urls():
            p = u.toLocalFile()
            if p and os.path.exists(p) and is_supported_drop_or_paste_file(p):
                files.append(p)

        if files:
            self.files_dropped.emit(files)
            event.acceptProposedAction()
        else:
            event.ignore()

    def start_draw_box_mode(self):
        if not self._overlay_enabled:
            return
        self._draw_mode = True
        self._draw_start = None
        self.setDragMode(QGraphicsView.NoDrag)

    def stop_draw_box_mode(self):
        self._draw_mode = False
        self._draw_start = None
        if self._draw_rect_item is not None:
            try:
                if isValid(self._draw_rect_item) and self._draw_rect_item.scene() is self.scene:
                    self.scene.removeItem(self._draw_rect_item)
            except RuntimeError:
                pass
            self._draw_rect_item = None
        self.setDragMode(QGraphicsView.NoDrag)

    def start_split_box_mode(self, idx: int):
        if not self._overlay_enabled:
            return
        if idx not in self._rects:
            return

        self._split_mode = True
        self._split_target_idx = idx
        self.viewport().setCursor(Qt.SplitHCursor)

        if self._split_preview_item is not None:
            try:
                if isValid(self._split_preview_item) and self._split_preview_item.scene() is self.scene:
                    self.scene.removeItem(self._split_preview_item)
            except RuntimeError:
                pass
            self._split_preview_item = None

    def stop_split_box_mode(self):
        self._split_mode = False
        self._split_target_idx = None
        self.viewport().unsetCursor()

        if self._split_preview_item is not None:
            try:
                if isValid(self._split_preview_item) and self._split_preview_item.scene() is self.scene:
                    self.scene.removeItem(self._split_preview_item)
            except RuntimeError:
                pass
            self._split_preview_item = None

    def start_selection_mode(self, scene_pos: QPointF):
        if not self._overlay_enabled:
            return

        self._selection_mode = True
        self._selection_start = scene_pos

        if self._selection_rect_item is not None:
            try:
                if isValid(self._selection_rect_item) and self._selection_rect_item.scene() is self.scene:
                    self.scene.removeItem(self._selection_rect_item)
            except RuntimeError:
                pass
            self._selection_rect_item = None

        self._selection_rect_item = QGraphicsRectItem(QRectF(scene_pos, scene_pos))
        self._selection_rect_item.setPen(self._pen_selection)
        self._selection_rect_item.setBrush(self._brush_selection)
        self._selection_rect_item.setZValue(999)
        self.scene.addItem(self._selection_rect_item)

    def stop_selection_mode(self):
        self._selection_mode = False
        self._selection_start = None
        if self._selection_rect_item is not None:
            try:
                if isValid(self._selection_rect_item) and self._selection_rect_item.scene() is self.scene:
                    self.scene.removeItem(self._selection_rect_item)
            except RuntimeError:
                pass
            self._selection_rect_item = None

    def select_indices(self, indices, center: bool = False):
        try:
            idxs = {int(i) for i in indices if i is not None}
        except Exception:
            idxs = set()

        self._selected_indices = idxs
        self._selected_idx = min(idxs) if idxs else None

        try:
            self.scene.clearSelection()
        except Exception:
            pass

        for idx, rect in self._rects.items():
            if not isValid(rect):
                continue

            is_sel = (idx in idxs)

            rect.setSelected(is_sel)

            if is_sel:
                rect.setPen(self._pen_selected)
                rect.setBrush(self._brush_selected)
                rect.setZValue(20)
            else:
                rect.setPen(self._pen_normal)
                rect.setBrush(self._brush_fill)
                rect.setZValue(10)

            rect.update()

        self.scene.update()
        self.viewport().update()

        if center and idxs:
            first = min(idxs)
            rect = self._rects.get(first)
            if rect and isValid(rect):
                self.centerOn(rect)

    def _finalize_selection_rect(self, additive: bool = False):
        if not self._selection_rect_item or not isValid(self._selection_rect_item):
            self.stop_selection_mode()
            return

        sel_rect = self._selection_rect_item.rect().normalized()

        hit = []
        for idx, rect in self._rects.items():
            if not isValid(rect):
                continue
            scene_rect = rect.mapRectToScene(rect.rect()).normalized()
            center = scene_rect.center()
            if sel_rect.intersects(scene_rect) or sel_rect.contains(center):
                hit.append(idx)

        if additive:
            hit = sorted(set(hit) | self._selected_indices)
        else:
            hit = sorted(set(hit))

        self.select_indices(hit, center=False)
        self.overlay_multi_selected.emit(hit)
        self.stop_selection_mode()

    def contextMenuEvent(self, event):
        pos = event.pos()
        item = self.itemAt(pos)

        menu = QMenu(self)
        tr = self.tr_func

        if not self._overlay_enabled:
            disabled = menu.addAction(
                tr("overlay_only_after_ocr") if tr else "Overlay-Bearbeitung erst nach abgeschlossener OCR möglich.")
            disabled.setEnabled(False)
            menu.exec(event.globalPos())
            return

        if isinstance(item, ResizableRectItem):
            idx = item.idx
            act_split = menu.addAction(tr("canvas_menu_split_box") if tr else "Split box")
            act_del = menu.addAction(tr("canvas_menu_delete_box") if tr else "Delete overlay box")
            menu.addSeparator()
            act_add_draw = menu.addAction(tr("canvas_menu_add_box_draw") if tr else "Add overlay box (draw)")

            chosen = menu.exec(event.globalPos())
            if not chosen:
                return
            elif chosen == act_split:
                self.start_split_box_mode(idx)
            elif chosen == act_del:
                self.overlay_delete_requested.emit(idx)
            elif chosen == act_add_draw:
                self.overlay_add_draw_requested.emit(self.mapToScene(pos))
            return

        act_add_draw = menu.addAction(tr("canvas_menu_add_box_draw") if tr else "Add overlay box (draw)")
        chosen = menu.exec(event.globalPos())
        if not chosen:
            return
        if chosen == act_add_draw:
            self.overlay_add_draw_requested.emit(self.mapToScene(pos))

    def mousePressEvent(self, event):
        if self._split_mode and event.button() == Qt.LeftButton:
            rect_item = self._rects.get(self._split_target_idx)
            if rect_item and isValid(rect_item):
                scene_rect = rect_item.mapRectToScene(rect_item.rect()).normalized()
                sp = self.mapToScene(self._event_point(event))

                if scene_rect.contains(sp):
                    split_x = max(scene_rect.left() + 8.0, min(scene_rect.right() - 8.0, sp.x()))
                    self.box_split_requested.emit(self._split_target_idx, float(split_x))

            self.stop_split_box_mode()
            event.accept()
            return

        if event.button() == Qt.LeftButton:
            it = self.itemAt(self._event_point(event))

            # Klick auf Nummernlabel auf die zugehörige Box umlenken
            if isinstance(it, QGraphicsSimpleTextItem):
                txt = it.text().strip()
                if txt.isdigit():
                    idx = int(txt) - 1
                    rect = self._rects.get(idx)
                    if rect and isValid(rect):
                        it = rect

            # 1) Zeichenmodus hat höchste Priorität
            if self._draw_mode and self._overlay_enabled and self._pixmap_item is not None:
                sp = self.mapToScene(self._event_point(event))
                self._draw_start = sp

                if self._draw_rect_item is not None:
                    try:
                        if isValid(self._draw_rect_item) and self._draw_rect_item.scene() is self.scene:
                            self.scene.removeItem(self._draw_rect_item)
                    except RuntimeError:
                        pass
                    self._draw_rect_item = None

                self._draw_rect_item = QGraphicsRectItem(QRectF(sp, sp))
                self._draw_rect_item.setPen(self._pen_draw)
                self._draw_rect_item.setBrush(self._brush_draw)
                self._draw_rect_item.setZValue(999)
                self.scene.addItem(self._draw_rect_item)

                event.accept()
                return

            # Klick direkt auf eine Overlay-Box
            if isinstance(it, ResizableRectItem):
                ctrl_pressed = bool(event.modifiers() & Qt.ControlModifier)

                if ctrl_pressed:
                    new_selection = set(self._selected_indices)

                    if it.idx in new_selection:
                        new_selection.remove(it.idx)
                    else:
                        new_selection.add(it.idx)

                    new_selection = sorted(new_selection)

                    self.select_indices(new_selection, center=False)
                    self.overlay_multi_selected.emit(new_selection)

                    if new_selection:
                        self._selected_idx = it.idx if it.idx in new_selection else min(new_selection)
                    else:
                        self._selected_idx = None

                    event.accept()
                    return

                # WICHTIG:
                # Nicht hier den Event "schlucken".
                # Die ResizableRectItem muss den Mausklick selbst bekommen,
                # damit Move/Resize funktioniert.
                super().mousePressEvent(event)
                return

            # Panning nur mit Alt + linker Maustaste
            if (
                    self._pixmap_item is not None
                    and self._zoom > (self._fit_zoom * 1.01)
                    and (event.modifiers() & Qt.AltModifier)
            ):
                self._mouse_panning = True
                self._pan_start = self._event_point(event)
                self._pan_start_h = self.horizontalScrollBar().value()
                self._pan_start_v = self.verticalScrollBar().value()
                self.setCursor(Qt.ClosedHandCursor)
                event.accept()
                return

            # Rechteckauswahl nur wenn NICHT im Zeichenmodus
            if (
                    self._overlay_enabled
                    and self._pixmap_item is not None
                    and not self._draw_mode
                    and not (event.modifiers() & Qt.AltModifier)
            ):
                sp = self.mapToScene(self._event_point(event))
                self.start_selection_mode(sp)
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(self._event_point(event))
        if isinstance(item, ResizableRectItem) and event.button() == Qt.LeftButton:
            self.rect_clicked.emit(item.idx)
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        if self._split_mode and self._split_target_idx is not None:
            rect_item = self._rects.get(self._split_target_idx)
            if rect_item and isValid(rect_item):
                scene_rect = rect_item.mapRectToScene(rect_item.rect()).normalized()
                sp = self.mapToScene(self._event_point(event))

                split_x = max(scene_rect.left() + 8.0, min(scene_rect.right() - 8.0, sp.x()))

                if self._split_preview_item is None:
                    self._split_preview_item = QGraphicsLineItem()
                    self._split_preview_item.setPen(self._split_pen)
                    self._split_preview_item.setZValue(999)
                    self.scene.addItem(self._split_preview_item)

                self._split_preview_item.setLine(split_x, scene_rect.top(), split_x, scene_rect.bottom())
                event.accept()
                return

        if self._mouse_panning:
            p = self._event_point(event)
            delta = p - self._pan_start
            self.horizontalScrollBar().setValue(self._pan_start_h - delta.x())
            self.verticalScrollBar().setValue(self._pan_start_v - delta.y())
            event.accept()
            return

        if self._draw_mode and self._draw_start and self._draw_rect_item is not None:
            sp = self.mapToScene(self._event_point(event))
            r = QRectF(self._draw_start, sp).normalized()
            if isValid(self._draw_rect_item):
                self._draw_rect_item.setRect(r)
            return

        if self._selection_mode and self._selection_start and self._selection_rect_item is not None:
            sp = self.mapToScene(self._event_point(event))
            r = QRectF(self._selection_start, sp).normalized()

            if isValid(self._selection_rect_item):
                self._selection_rect_item.setRect(r)

            # Live-Vorschau: alle getroffenen Boxen sofort blau markieren
            hit = []
            for idx, rect in self._rects.items():
                if not isValid(rect):
                    continue
                scene_rect = rect.mapRectToScene(rect.rect()).normalized()
                center = scene_rect.center()
                if r.intersects(scene_rect) or r.contains(center):
                    hit.append(idx)

            self.select_indices(hit, center=False)
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._draw_mode and event.button() == Qt.LeftButton and self._draw_start and self._draw_rect_item is not None:
            rect = None
            if isValid(self._draw_rect_item):
                rect = self._draw_rect_item.rect().normalized()
            self.stop_draw_box_mode()
            if rect and rect.width() >= 5 and rect.height() >= 5:
                self.box_drawn.emit(rect)
            return

        if event.button() == Qt.LeftButton and self._selection_mode:
            self._finalize_selection_rect(additive=False)
            event.accept()
            return

        if event.button() == Qt.LeftButton and self._mouse_panning:
            self._mouse_panning = False
            self.unsetCursor()
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def clear_all(self):
        self.stop_draw_box_mode()
        self.stop_selection_mode()
        self.stop_split_box_mode()
        self.scene.clear()
        self._pixmap_item = None
        self._rects.clear()
        self._labels.clear()
        self._selected_idx = None
        self._selected_indices.clear()
        self._drop_text = None
        self.resetTransform()
        self._zoom = 1.0
        self._fit_zoom = 1.0
        self._show_drop_hint()

    def _center_drop_hint_in_view(self):
        if not self._drop_text or self._pixmap_item:
            return

        # Mittelpunkt des sichtbaren Viewports in Scene-Koordinaten
        center = self.mapToScene(self.viewport().rect().center())

        rect = self._drop_text.boundingRect()
        self._drop_text.setPos(center.x() - rect.width() / 2, center.y() - rect.height() / 2)

        # Szene so setzen, dass der Text sicher enthalten ist (sonst kann Qt komisch scrollen)
        br = self.scene.itemsBoundingRect()
        if br.isValid():
            self.setSceneRect(br.adjusted(-50, -50, 50, 50))

    def _show_drop_hint(self):
        if self._pixmap_item:
            return

        font = QFont("Arial", 20)
        font.setItalic(True)
        txt = self.tr_func("drop_hint") if self.tr_func else ""

        c = QColor("#aaa") if self._bg_color.lightness() < 128 else QColor("#555")

        # Wenn schon vorhanden: nur aktualisieren
        if self._drop_text and isValid(self._drop_text):
            self._drop_text.setFont(font)
            self._drop_text.setPlainText(txt)
            self._drop_text.setDefaultTextColor(c)
            self._center_drop_hint_in_view()
            return

        # Sonst: neu erzeugen
        self._drop_text = self.scene.addText(txt, font)
        self._drop_text.setAcceptedMouseButtons(Qt.NoButton)
        self._drop_text.setDefaultTextColor(c)
        self._center_drop_hint_in_view()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._pixmap_item:
            self._center_drop_hint_in_view()

    def load_pil_image(self, im: Image.Image, preserve_view: bool = False):
        # Aktuellen View-Status VOR dem Leeren speichern
        t = center = z = None
        if preserve_view:
            t, center, z = self._get_view_state()

        self.stop_draw_box_mode()
        self.scene.clear()
        self._pixmap_item = None
        self._rects.clear()
        self._labels.clear()
        self._selected_idx = None
        self._drop_text = None

        # WICHTIG: Nicht immer reset/fitten, wenn wir die Ansicht beibehalten sollen
        if not preserve_view:
            self.resetTransform()
            self._zoom = 1.0

        qim = ImageQt(im.convert("RGB"))
        pix = QPixmap.fromImage(qim)
        self._pixmap_item = self.scene.addPixmap(pix)
        self._pixmap_item.setZValue(0)
        self._pixmap_item.setAcceptedMouseButtons(Qt.NoButton)
        self._pixmap_item.setAcceptHoverEvents(False)
        self.setSceneRect(self.scene.itemsBoundingRect())

        if preserve_view and t is not None:
            self._restore_view_state(t, center, z)
        else:
            self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)

            try:
                self._zoom = float(self.transform().m11())
                self._fit_zoom = self._zoom
            except Exception:
                self._zoom = 1.0
                self._fit_zoom = 1.0

    def refresh_overlays(self):
        if self._pixmap_item and hasattr(self, "_last_recs"):
            for r in list(self._rects.values()):
                try:
                    if isValid(r) and r.scene() is self.scene:
                        self.scene.removeItem(r)
                except RuntimeError:
                    pass
            for l in list(self._labels.values()):
                try:
                    if isValid(l) and l.scene() is self.scene:
                        self.scene.removeItem(l)
                except RuntimeError:
                    pass
            self._rects.clear()
            self._labels.clear()
            self.draw_overlays(self._last_recs)

    def _on_rect_item_changed(self, idx: int, scene_rect: QRectF):
        self.rect_changed.emit(idx, scene_rect)

    def _on_rect_item_clicked(self, idx: int):
        self.rect_clicked.emit(idx)

    def _on_rect_item_double_clicked(self, idx: int):
        self.rect_clicked.emit(idx)

    def draw_overlays(self, recs: List[RecordView]):
        self._last_recs = recs
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)

        for rv in recs:
            if not rv.bbox:
                continue
            x0, y0, x1, y1 = rv.bbox
            rectf = QRectF(x0, y0, x1 - x0, y1 - y0)

            ritem = ResizableRectItem(
                rectf,
                rv.idx,
                self._on_rect_item_changed,
                on_clicked=self._on_rect_item_clicked,
                on_double_clicked=self._on_rect_item_double_clicked
            )
            ritem.setPen(self._pen_normal)
            ritem.setBrush(self._brush_fill)
            ritem.setZValue(10)
            self.scene.addItem(ritem)
            self._rects[rv.idx] = ritem

            lab = QGraphicsSimpleTextItem(str(rv.idx + 1))
            lab.setFont(font)
            c_text = QColor("#fff") if self._bg_color.lightness() < 128 else QColor("#000")
            lab.setBrush(QBrush(c_text))
            lab.setZValue(11)
            lab.setPos(x0, max(0, y0 - 16))
            lab.setAcceptedMouseButtons(Qt.NoButton)
            self.scene.addItem(lab)
            self._labels[rv.idx] = lab

    def select_idx(self, idx: Optional[int], center: bool = True):
        if idx is None:
            self.select_indices([], center=False)
        else:
            self.select_indices([idx], center=center)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self._apply_zoom(1.25)
        else:
            self._apply_zoom(0.8)

    def _apply_zoom(self, factor: float):
        new_zoom = self._zoom * factor
        if 0.05 <= new_zoom <= 20.0:
            self.scale(factor, factor)
            self._zoom = new_zoom

        if not self._draw_mode and not self._mouse_panning:
            self.unsetCursor()


class PDFRenderWorker(QThread):
    progress = Signal(int, int, str)  # current, total, pdf_path
    finished_pdf = Signal(str, list)  # pdf_path, out_paths
    failed_pdf = Signal(str, str)  # pdf_path, error_message

    def __init__(self, pdf_path: str, dpi: int = 300, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.dpi = int(dpi)

    def run(self):
        out_paths: List[str] = []
        try:
            pdf_path = self.pdf_path
            dpi = self.dpi

            base = os.path.splitext(os.path.basename(pdf_path))[0]
            tmp_dir = os.path.join(os.path.dirname(pdf_path), f".kraken_tmp_{base}")
            os.makedirs(tmp_dir, exist_ok=True)

            doc = fitz.open(pdf_path)
            total = int(doc.page_count)

            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)

            try:
                for i in range(total):
                    if self.isInterruptionRequested():
                        break

                    page = doc.load_page(i)
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    out = os.path.join(tmp_dir, f"{base}_p{i + 1:04d}.png")
                    pix.save(out)
                    out_paths.append(out)

                    self.progress.emit(i + 1, total, pdf_path)
            finally:
                doc.close()

            # auch wenn abgebrochen -> "fertig" mit dem was da ist
            self.finished_pdf.emit(pdf_path, out_paths)

        except Exception:
            self.failed_pdf.emit(self.pdf_path, traceback.format_exc())


# -----------------------------
# OCR-WORKER
# -----------------------------
class OCRWorker(QThread):
    file_started = Signal(str)
    file_done = Signal(str, str, list, object, list)
    file_error = Signal(str, str)
    progress = Signal(int)
    finished_batch = Signal()
    failed = Signal(str)
    device_resolved = Signal(str)
    gpu_info = Signal(str)

    def __init__(self, job: OCRJob):
        super().__init__()
        self.job = job
        self._device: Optional[torch.device] = None
        self._rec_model: Any = None
        self._seg_model: Any = None
        self._device_label: str = (job.device or "cpu").lower().strip()

    def _release_torch_resources(self):
        self._rec_model = None
        self._seg_model = None
        self._device = None

        try:
            gc.collect()
        except Exception:
            pass

        try:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

        try:
            if torch.cuda.is_available():
                torch.cuda.ipc_collect()
        except Exception:
            pass

    def _resolve_device(self) -> torch.device:
        dev = (self.job.device or "cpu").lower().strip()
        self._device_label = dev

        if dev in ("cuda", "rocm"):
            # CUDA und ROCm nutzen beide das torch.cuda-Backend; ROCm erkennt man an torch.version.hip
            if torch.cuda.is_available() and torch.cuda.device_count() > 0:
                return torch.device("cuda")

        if dev == "mps" and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")

        self._device_label = "cpu"
        return torch.device("cpu")

    def _emit_gpu_info(self, device: torch.device):
        try:
            if device.type == "cuda":
                name = torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else "GPU"
                hip_ver = getattr(torch.version, "hip", None)
                cuda_ver = getattr(torch.version, "cuda", None)

                # Wenn der Nutzer ROCm gewählt hat oder HIP vorhanden ist -> ROCm/HIP-Info anzeigen, sonst CUDA-Info
                if self._device_label == "rocm" or hip_ver:
                    extra = []
                    if hip_ver:
                        extra.append(f"HIP {hip_ver}")
                    s = name + (f" ({', '.join(extra)})" if extra else " (ROCm)")
                    self.gpu_info.emit(s)
                else:
                    extra = []
                    if cuda_ver:
                        extra.append(f"CUDA {cuda_ver}")
                    s = name + (f" ({', '.join(extra)})" if extra else " (CUDA)")
                    self.gpu_info.emit(s)

            elif device.type == "mps":
                self.gpu_info.emit("Apple MPS")
            else:
                self.gpu_info.emit("CPU")
        except Exception:
            pass

    def _load_rec_model(self, path: str, device: torch.device):
        try:
            return models.load_any(path, device=device)
        except TypeError:
            return models.load_any(path)

    def _load_seg_model(self, path: str, device: torch.device):
        try:
            return vgsl.TorchVGSLModel.load_model(path, device=device)
        except TypeError:
            return vgsl.TorchVGSLModel.load_model(path)

    def _ensure_models_loaded(self):
        if self._device is None:
            self._device = self._resolve_device()
            self.device_resolved.emit(f"{self._device_label} -> {self._device}")
            self._emit_gpu_info(self._device)

        if self._rec_model is None:
            self._rec_model = self._load_rec_model(self.job.recognition_model_path, self._device)

        if self._seg_model is None:
            if not self.job.segmentation_model_path:
                raise ValueError("No blla segmentation model selected.")
            self._seg_model = self._load_seg_model(self.job.segmentation_model_path, self._device)

    @staticmethod
    def _seg_expected_lines(seg: Any) -> Optional[int]:
        for attr in ("lines", "baselines"):
            v = getattr(seg, attr, None)
            if v is not None:
                try:
                    return len(v)
                except Exception:
                    pass
        return None

    def _emit_overall_progress(self, file_idx: int, total_files: int, frac_in_file: float):
        if total_files <= 0:
            self.progress.emit(0)
            return
        frac_in_file = max(0.0, min(1.0, float(frac_in_file)))
        overall = (file_idx + frac_in_file) / float(total_files)
        self.progress.emit(int(overall * 100))

    # -------------------------------------------------------
    # OCRWorker._ocr_one
    # -------------------------------------------------------
    def _filter_short_baselines_in_seg(self, seg):
        try:
            if hasattr(seg, "baselines") and hasattr(seg, "lines") and seg.baselines and seg.lines:
                new_baselines = []
                new_lines = []
                for bl, ln in zip(seg.baselines, seg.lines):
                    if baseline_length(bl) >= 5.0:
                        new_baselines.append(bl)
                        new_lines.append(ln)
                seg.baselines = new_baselines
                seg.lines = new_lines
        except Exception:
            pass
        return seg

    def _ocr_using_preset_bboxes(
            self,
            img_path: str,
            im: Image.Image,
            preset_bboxes: List[Optional[BBox]],
            file_idx: int,
            total_files: int
    ) -> Tuple[str, List[RecordView]]:
        """
        Führt OCR direkt auf den vorhandenen Overlay-/Split-Boxen aus.
        Es wird KEINE neue Seitensegmentierung erzeugt.
        Jede Box ist genau eine Zielzeile.
        """
        page_w, page_h = im.size
        record_views: List[RecordView] = []

        valid_boxes: List[BBox] = []
        for bb in preset_bboxes:
            if not bb:
                continue
            clamped = clamp_bbox(bb, page_w, page_h)
            if not clamped:
                continue
            x0, y0, x1, y1 = clamped
            if x1 > x0 and y1 > y0:
                valid_boxes.append(clamped)

        total_boxes = max(1, len(valid_boxes))

        for box_idx, bb in enumerate(valid_boxes):
            if self.isInterruptionRequested():
                break

            x0, y0, x1, y1 = bb
            crop = im.crop((x0, y0, x1, y1))

            crop_records = []

            try:
                seg = blla.segment(crop, model=self._seg_model)
                seg = self._filter_short_baselines_in_seg(seg)

                for rec in rpred.rpred(self._rec_model, crop, seg):
                    crop_records.append(rec)

            except Exception:
                crop_records = []

            if crop_records:
                rec_model_name = os.path.basename(self.job.recognition_model_path).lower()

                if "handwriting" in rec_model_name:
                    crop_records = sort_records_handwriting_simple(
                        crop_records,
                        self.job.reading_direction
                    )
                else:
                    crop_records = sort_records_reading_order(
                        crop_records,
                        crop.size[0],
                        crop.size[1],
                        self.job.reading_direction
                    )

                parts = []
                for rec in crop_records:
                    pred = getattr(rec, "prediction", None)
                    txt = _clean_ocr_text(pred)
                    if txt and not _is_symbol_only_line(txt) and not _is_noise_line(txt):
                        parts.append(txt)

                final_text = " ".join(parts).strip()
            else:
                final_text = ""

            record_views.append(RecordView(len(record_views), final_text, bb))
            self._emit_overall_progress(file_idx, total_files, (box_idx + 1) / total_boxes)

        text = "\n".join(rv.text for rv in record_views).strip()
        return text, record_views

    def _ocr_one(self, img_path: str, file_idx: int, total_files: int):
        self.file_started.emit(img_path)
        try:
            # --- Bild einmalig laden (Graustufe) ---
            im_orig = _load_image_gray(img_path)
            orig_w, orig_h = im_orig.size

            # NEU: vorhandene Overlay-/Split-Boxen beim Re-OCR direkt verwenden
            preset_bboxes = self.job.preset_bboxes_by_path.get(img_path, []) or []
            if preset_bboxes:
                text, record_views = self._ocr_using_preset_bboxes(
                    img_path=img_path,
                    im=im_orig,
                    preset_bboxes=preset_bboxes,
                    file_idx=file_idx,
                    total_files=total_files
                )

                # kr_records bewusst leer: wir haben direkt auf den Zielboxen gearbeitet
                self.file_done.emit(img_path, text, [], im_orig, record_views)
                return

            im = im_orig
            scale_factor = 1.0

            # --- FIX A: zu kleine Bilder hochskalieren (verhindert Baselines < 5px) ---
            min_dim = min(im.size)
            if min_dim < 1200:
                scale_factor = 2 if min_dim >= 700 else 3
                im = im.resize((im.size[0] * scale_factor, im.size[1] * scale_factor), Image.BICUBIC)

            # --- Segmentierung ---
            seg = blla.segment(im, model=self._seg_model)

            # --- FIX B: winzige/kaputte Baselines entfernen (Baseline length below minimum 5px) ---
            try:
                if hasattr(seg, "baselines") and hasattr(seg, "lines") and seg.baselines and seg.lines:
                    new_baselines = []
                    new_lines = []
                    for bl, ln in zip(seg.baselines, seg.lines):
                        if baseline_length(bl) >= 5.0:
                            new_baselines.append(bl)
                            new_lines.append(ln)
                    seg.baselines = new_baselines
                    seg.lines = new_lines
            except Exception:
                pass

            expected = self._seg_expected_lines(seg)

            def _rescale_bbox(bb, factor):
                if not bb or factor == 1.0:
                    return bb
                x0, y0, x1, y1 = bb
                return (
                    int(round(x0 / factor)),
                    int(round(y0 / factor)),
                    int(round(x1 / factor)),
                    int(round(y1 / factor)),
                )

            # --- Erkennung (Recognition) ---
            kr_records = []
            done = 0

            try:
                for rec in rpred.rpred(self._rec_model, im, seg):
                    kr_records.append(rec)
                    done += 1
                    if expected and expected > 0:
                        self._emit_overall_progress(file_idx, total_files, done / expected)

                    if self.isInterruptionRequested():
                        break
            except Exception:
                self.file_error.emit(img_path, traceback.format_exc())
                return

            if self.isInterruptionRequested():
                return

            rec_model_name = os.path.basename(self.job.recognition_model_path).lower()

            if "handwriting" in rec_model_name:
                kr_sorted = sort_records_handwriting_simple(
                    kr_records,
                    self.job.reading_direction
                )
            else:
                kr_sorted = sort_records_reading_order(
                    kr_records,
                    im.size[0],
                    im.size[1],
                    self.job.reading_direction
                )

            # --- WIDE LINE SPLIT: nur echte 2-Spalten-Zeilen splitten, Header NICHT ---
            def _is_header_like(bb, txt, page_w, page_h):
                x0, y0, x1, y1 = bb
                w = x1 - x0
                cx = (x0 + x1) / 2.0

                if w < 0.72 * page_w:
                    return False
                if abs(cx - (page_w / 2.0)) > 0.20 * page_w:
                    return False
                if y0 > 0.45 * page_h:
                    return False
                if len((txt or "").strip()) > 90:
                    return False
                return True

            two_col_splitter = re.compile(r"\s{4,}")

            record_views: List[RecordView] = []
            lines: List[str] = []
            out_idx = 0
            page_w, page_h = orig_w, orig_h

            for r in kr_sorted:
                pred = getattr(r, "prediction", None)
                if pred is None:
                    continue

                txt = _clean_ocr_text(pred)
                if _is_effectively_empty_ocr_text(txt) or _is_symbol_only_line(txt) or _is_noise_line(txt):
                    continue

                bb = record_bbox(r)
                bb = _rescale_bbox(bb, scale_factor)
                split_done = False

                if bb:
                    x0, y0, x1, y1 = bb
                    w = x1 - x0

                    if w > int(page_w * 0.80) and not _is_header_like(bb, txt, page_w, page_h):
                        parts = two_col_splitter.split(txt, maxsplit=1)

                        if len(parts) == 2:
                            left_txt, right_txt = map(_clean_ocr_text, parts)

                            mid = page_w // 2
                            left_bb = clamp_bbox((0, y0, mid, y1), page_w, page_h)
                            right_bb = clamp_bbox((mid, y0, page_w, y1), page_w, page_h)

                            parts_in_order = []
                            if left_bb and left_txt:
                                parts_in_order.append((left_txt, left_bb))
                            if right_bb and right_txt:
                                parts_in_order.append((right_txt, right_bb))

                            rev_x = self.job.reading_direction in (
                                READING_MODES["TB_RL"],
                                READING_MODES["BT_RL"]
                            )
                            if rev_x:
                                parts_in_order = list(reversed(parts_in_order))

                            if parts_in_order:
                                for txt_part, bb_part in parts_in_order:
                                    record_views.append(RecordView(out_idx, txt_part, bb_part))
                                    lines.append(txt_part)
                                    out_idx += 1
                                split_done = True

                if split_done:
                    continue

                record_views.append(RecordView(out_idx, txt, bb))
                lines.append(txt)
                out_idx += 1

            filtered_record_views: List[RecordView] = []
            filtered_lines: List[str] = []

            for rv in record_views:
                rv.text = _clean_ocr_text(rv.text)
                if _is_effectively_empty_ocr_text(rv.text) or _is_symbol_only_line(rv.text) or _is_noise_line(rv.text):
                    continue

                rv.idx = len(filtered_record_views)
                filtered_record_views.append(rv)
                filtered_lines.append(rv.text)

            record_views = filtered_record_views
            lines = filtered_lines

            self._emit_overall_progress(file_idx, total_files, 1.0)
            text = "\n".join(lines).strip()
            self.file_done.emit(img_path, text, kr_sorted, im, record_views)

        except Exception:
            self.file_error.emit(img_path, traceback.format_exc())

    def run(self):
        try:
            if not os.path.exists(self.job.recognition_model_path):
                raise ValueError("Recognition model not found.")

            if not os.path.exists(self.job.segmentation_model_path or ""):
                raise ValueError("blla segmentation model not found.")

            self._ensure_models_loaded()

            total = len(self.job.input_paths)
            for i, path in enumerate(self.job.input_paths):
                if self.isInterruptionRequested():
                    break
                self._emit_overall_progress(i, total, 0.0)
                self._ocr_one(path, i, total)

            self.progress.emit(100)
            self.finished_batch.emit()
        except Exception:
            self.failed.emit(traceback.format_exc())
        finally:
            self._release_torch_resources()


class AIBatchRevisionWorker(QThread):
    file_started = Signal(str, int, int)  # path, current, total
    file_finished = Signal(str, list, int, int)  # path, revised_lines, current, total
    file_failed = Signal(str, str, int, int)  # path, error, current, total
    progress_changed = Signal(int)  # overall 0..100
    status_changed = Signal(str)
    finished_batch = Signal()

    def __init__(
            self,
            items: List[TaskItem],
            lm_model: str,
            endpoint: str,
            enable_thinking: bool = False,
            temperature: float = 0.2,
            top_p: float = 0.8,
            top_k: int = 10,
            presence_penalty: float = 0.0,
            repetition_penalty: float = 1.0,
            min_p: float = 0.0,
            max_tokens: int = 1200,
            tr_func=None,
            parent=None
    ):
        super().__init__(parent)
        self._tr = tr_func or (lambda key, *args: (TRANSLATIONS["de"].get(key, key).format(*args) if args else TRANSLATIONS["de"].get(key, key)))
        self.items = items
        self.lm_model = lm_model
        self.endpoint = endpoint
        self.enable_thinking = enable_thinking
        self.temperature = float(temperature)
        self.top_p = float(top_p)
        self.top_k = int(top_k)
        self.presence_penalty = float(presence_penalty)
        self.repetition_penalty = float(repetition_penalty)
        self.min_p = float(min_p)
        self.max_tokens = int(max_tokens)
        self._current_worker: Optional[AIRevisionWorker] = None
        self._cancel_requested = False

    def cancel(self):
        self._cancel_requested = True
        self.requestInterruption()

        worker = self._current_worker
        if worker is not None:
            try:
                worker.cancel()
            except Exception:
                pass

    def _revise_one_item(self, item: TaskItem) -> List[str]:
        if self.isInterruptionRequested():
            raise RuntimeError(self._tr("msg_ai_cancelled"))

        if not item.results:
            return []

        _, _, _, recs = item.results

        live_boxes = (
            list(item.preset_bboxes)
            if len(item.preset_bboxes) == len(recs)
            else [rv.bbox for rv in recs]
        )

        recs_for_ai = [
            RecordView(i, recs[i].text, tuple(live_boxes[i]) if live_boxes[i] else None)
            for i in range(len(recs))
        ]

        result_holder: Dict[str, Any] = {}
        error_holder: Dict[str, Any] = {}

        worker = AIRevisionWorker(
            path=item.path,
            recs=recs_for_ai,
            lm_model=self.lm_model,
            endpoint=self.endpoint,
            enable_thinking=self.enable_thinking,
            source_kind=item.source_kind,
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            presence_penalty=self.presence_penalty,
            repetition_penalty=self.repetition_penalty,
            min_p=self.min_p,
            max_tokens=self.max_tokens,
            tr_func=self._tr,
            parent=None
        )

        self._current_worker = worker

        try:
            worker.status_changed.connect(self.status_changed.emit)
            worker.finished_revision.connect(
                lambda path, lines: result_holder.setdefault("lines", lines)
            )
            worker.failed_revision.connect(
                lambda path, msg: error_holder.setdefault("msg", msg)
            )

            # synchron im Batch-Thread
            worker.run()

        finally:
            self._current_worker = None

        if self.isInterruptionRequested():
            raise RuntimeError(self._tr("msg_ai_cancelled"))

        if "msg" in error_holder:
            raise RuntimeError(str(error_holder["msg"]))

        return list(result_holder.get("lines", []))

    def run(self):
        total = len(self.items)

        if total <= 0:
            self.finished_batch.emit()
            return

        for i, item in enumerate(self.items, start=1):
            if self.isInterruptionRequested():
                break

            self.file_started.emit(item.path, i, total)
            self.status_changed.emit(f"KI-Batch {i}/{total}: {os.path.basename(item.path)}")
            self.progress_changed.emit(int(((i - 1) / total) * 100))

            try:
                revised_lines = self._revise_one_item(item)

                if self.isInterruptionRequested():
                    break

                self.file_finished.emit(item.path, revised_lines, i, total)

            except Exception as e:
                msg = str(e)
                self.file_failed.emit(item.path, msg, i, total)

                if "abgebrochen" in msg.lower():
                    break

            self.progress_changed.emit(int((i / total) * 100))

        self.status_changed.emit("KI-Batch abgeschlossen.")
        self.finished_batch.emit()


def _normalize_bbox(bb: Optional[BBox], img_w: int, img_h: int) -> Optional[List[float]]:
    if not bb or img_w <= 0 or img_h <= 0:
        return None
    x0, y0, x1, y1 = bb
    return [
        round(x0 / img_w, 4),
        round(y0 / img_h, 4),
        round(x1 / img_w, 4),
        round(y1 / img_h, 4),
    ]


def _extract_text_lines(text: str) -> List[str]:
    if not text:
        return []
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


class AIRevisionWorker(QThread):
    finished_revision = Signal(str, list)  # path, revised_lines
    failed_revision = Signal(str, str)  # path, error
    progress_changed = Signal(int)  # 0..100
    status_changed = Signal(str)  # live text

    def __init__(
            self,
            path: str,
            recs: List[RecordView],
            lm_model: str,
            endpoint: str = "http://127.0.0.1:1234/v1/chat/completions",
            enable_thinking: bool = False,
            source_kind: str = "image",
            temperature: float = 0.2,
            top_p: float = 0.8,
            top_k: int = 10,
            presence_penalty: float = 0.0,
            repetition_penalty: float = 1.0,
            min_p: float = 0.0,
            max_tokens: int = 1200,
            tr_func=None,
            parent=None
    ):
        super().__init__(parent)
        self._tr = tr_func or (lambda key, *args: (TRANSLATIONS["de"].get(key, key).format(*args) if args else TRANSLATIONS["de"].get(key, key)))
        self.path = path
        self.recs = [
            RecordView(i, rv.text, tuple(rv.bbox) if rv.bbox else None)
            for i, rv in enumerate(recs)
        ]
        self._frozen_bboxes = [tuple(rv.bbox) if rv.bbox else None for rv in self.recs]
        self.lm_model = lm_model
        self.endpoint = endpoint
        self.source_kind = source_kind

        self.enable_thinking = bool(enable_thinking)
        self.temperature = float(temperature)
        self.top_p = float(top_p)
        self.top_k = int(top_k)
        self.presence_penalty = float(presence_penalty)
        self.repetition_penalty = float(repetition_penalty)
        self.min_p = float(min_p)
        self.max_tokens = int(max_tokens)

        self._cancelled = False
        self._active_conn = None

    def cancel(self):
        self._cancelled = True
        self.requestInterruption()

        conn = self._active_conn
        self._active_conn = None

        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

    def _is_image_processing_error(self, exc: Exception) -> bool:
        msg = str(exc).lower()
        return (
                "failed to process image" in msg
                or "image" in msg and "http 400" in msg
        )

    def _looks_like_form_layout(self) -> bool:
        if not self.recs:
            return False

        short_lines = 0
        empty_or_tiny = 0
        with_bbox = 0

        for rv in self.recs:
            txt = (rv.text or "").strip()
            if rv.bbox:
                with_bbox += 1
            if len(txt) <= 25:
                short_lines += 1
            if len(txt) <= 2:
                empty_or_tiny += 1

        ratio_short = short_lines / max(1, len(self.recs))
        ratio_tiny = empty_or_tiny / max(1, len(self.recs))

        return with_bbox >= max(3, len(self.recs) // 2) and ratio_short >= 0.6 and ratio_tiny >= 0.15

    def _normalize_compare_text(self, text: str) -> str:
        txt = _clean_ocr_text(text or "")
        txt = txt.lower()

        # nur sehr leichte Normalisierung
        txt = txt.replace("ſ", "s")
        txt = txt.replace("ß", "ss")

        # Satzzeichen weitgehend raus, Leerraum glätten
        txt = re.sub(r"[^\w\s]", " ", txt, flags=re.UNICODE)
        txt = re.sub(r"\s+", " ", txt).strip()
        return txt

    def _text_similarity_ratio(self, a: str, b: str) -> float:
        import difflib

        aa = self._normalize_compare_text(a)
        bb = self._normalize_compare_text(b)

        if not aa and not bb:
            return 1.0
        if not aa or not bb:
            return 0.0

        return difflib.SequenceMatcher(None, aa, bb).ratio()

    def _token_overlap_ratio(self, a: str, b: str) -> float:
        aa = set(self._normalize_compare_text(a).split())
        bb = set(self._normalize_compare_text(b).split())

        if not aa and not bb:
            return 1.0
        if not aa or not bb:
            return 0.0

        inter = len(aa & bb)
        base = max(1, min(len(aa), len(bb)))
        return inter / base

    def _looks_like_long_block(self, text: str) -> bool:
        txt = _clean_ocr_text(text or "")
        if not txt:
            return False

        # zu lang für eine einzelne Formular-/Kurzzeile
        if len(txt) > 80:
            return True

        # ungewöhnlich viele Wörter -> eher zusammengezogene Nachbarzeilen
        if len(txt.split()) > 12:
            return True

        # explizite Zeilenumbrüche sind hier verdächtig
        if "\n" in txt:
            return True

        return False

    def _is_suspicious_box_result(self, text: str) -> bool:
        txt = _clean_ocr_text(text or "")
        if not txt:
            return True
        if "\n" in txt:
            return True
        if len(txt) <= 2:
            return True

        # typische "komische" OCR-Reste wie KURAVA
        if txt.isupper() and len(txt) >= 5 and " " not in txt:
            return True

        return False

    def _page_text_is_safe_context(
            self,
            kraken_text: str,
            box_text: str,
            page_text: str,
            prev_final_text: str = "",
    ) -> bool:
        pt = _clean_ocr_text(page_text or "")
        bt = _clean_ocr_text(box_text or "")
        kt = _clean_ocr_text(kraken_text or "")
        prev = _clean_ocr_text(prev_final_text or "")

        if not pt:
            return False

        # Niemals lange Blöcke aus Page-OCR übernehmen
        if self._looks_like_long_block(pt):
            return False

        # Niemals Duplikat der vorherigen finalen Zeile erzeugen
        if prev and self._normalize_compare_text(pt) == self._normalize_compare_text(prev):
            return False

        # Page darf nur helfen, wenn es lokal ähnlich genug ist
        sim_box = self._text_similarity_ratio(pt, bt) if bt else 0.0
        sim_kr = self._text_similarity_ratio(pt, kt) if kt else 0.0

        tok_box = self._token_overlap_ratio(pt, bt) if bt else 0.0
        tok_kr = self._token_overlap_ratio(pt, kt) if kt else 0.0

        # sicher nur dann, wenn Page zur lokalen Zeile passt
        if sim_box >= 0.72 or sim_kr >= 0.72:
            return True

        if tok_box >= 0.75 or tok_kr >= 0.75:
            return True

        return False

    def _choose_final_line_text(
            self,
            kraken_text: str,
            box_text: str,
            page_text: str,
            prev_final_text: str = "",
    ) -> str:
        kt = _clean_ocr_text(kraken_text or "")
        bt = _clean_ocr_text(box_text or "")
        pt = _clean_ocr_text(page_text or "")

        # 1) Box ist Primärquelle
        if bt and not self._looks_like_long_block(bt):
            best = bt
        else:
            best = kt

        # 2) Page nur als schwacher Kontext:
        # nur wenn Box leer/fraglich ist UND Page nicht widerspricht
        if self._page_text_is_safe_context(
                kraken_text=kt,
                box_text=bt,
                page_text=pt,
                prev_final_text=prev_final_text,
        ):
            # Nur dann auf Page gehen, wenn Box leer ist
            # oder Box deutlich kürzer/kaputt wirkt als Page,
            # aber Page trotzdem lokal ähnlich genug blieb.
            if not bt:
                best = pt
            else:
                sim_box_kr = self._text_similarity_ratio(bt, kt) if kt else 0.0
                sim_page_kr = self._text_similarity_ratio(pt, kt) if kt else 0.0

                # konservativ: Page nur nehmen, wenn es mindestens so plausibel wie Box wirkt
                if sim_page_kr > sim_box_kr + 0.10 and len(pt) <= len(bt) + 12:
                    best = pt

        # 3) harter Schutz gegen Nachbar-Duplikate
        if prev_final_text:
            if self._normalize_compare_text(best) == self._normalize_compare_text(prev_final_text):
                if kt and self._normalize_compare_text(kt) != self._normalize_compare_text(prev_final_text):
                    best = kt
                elif bt and self._normalize_compare_text(bt) != self._normalize_compare_text(prev_final_text):
                    best = bt

        # 4) niemals leer rausfallen, wenn Kraken was hatte
        if not best:
            best = bt or kt or pt

        return _clean_ocr_text(best)

    def _request_page_ocr_with_fixed_linecount(self, page_data_url: str, recs: List[RecordView]) -> List[str]:
        img_w, img_h = _load_image_color(self.path).size

        line_specs = []
        for rv in recs:
            line_specs.append({
                "idx": int(rv.idx),
                "bbox": _normalize_bbox(rv.bbox, img_w, img_h)
            })

        system_prompt = self._tr("ai_prompt_page_system")

        user_prompt = self._tr(
            "ai_prompt_page_user",
            len(recs),
            len(recs),
            len(recs) - 1,
            json.dumps(line_specs, ensure_ascii=False)
        )

        payload = {
            "model": self.lm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": page_data_url}},
                    ],
                },
            ],
            **self._build_sampling_payload(
                response_format=self._response_format_lines()
            ),
        }

        data = self._post_json(payload)
        try:
            print("RAW FULL LM STUDIO RESPONSE:")
            print(json.dumps(data, ensure_ascii=False, indent=2)[:12000])
        except Exception:
            pass
        content = self._extract_message_content(data)

        # Debug-Log: rohe Modellantwort sichtbar machen
        try:
            print("RAW PAGE OCR RESPONSE:")
            print(content[:4000])
        except Exception:
            pass

        obj = _extract_json_payload(content)

        if not isinstance(obj, dict):
            raise ValueError(
                self._tr("ai_err_page_invalid_json", content[:3000] if content else "<leer>")
            )

        lines = obj.get("lines")
        if not isinstance(lines, list):
            raise ValueError(
                self._tr("ai_err_page_invalid_lines", content[:3000] if content else "<leer>")
            )

        out = [""] * len(recs)

        for item in lines:
            if not isinstance(item, dict):
                continue
            idx = item.get("idx")
            txt = _force_text(item.get("text", "")).strip()
            if isinstance(idx, int) and 0 <= idx < len(recs):
                out[idx] = txt

        # Wenn fast alles leer ist -> kompletter Fehler
        filled = sum(1 for x in out if str(x).strip())

        too_long_blocks = sum(1 for x in out if len(str(x).strip()) > 120)

        if too_long_blocks >= 1:
            raise ValueError(
                self._tr("ai_err_page_long_blocks")
            )

        # Nur komplett unbrauchbare Antworten verwerfen
        if filled == 0:
            raise ValueError(
                self._tr("ai_err_page_no_usable_lines", filled, len(recs))
            )

        for i in range(len(out)):
            if not str(out[i]).strip():
                out[i] = recs[i].text

        return out

    def _request_single_line_reread(
            self,
            line_data_url: str,
            idx: int,
            current_text: str = "",
    ) -> str:
        system_prompt = self._tr("ai_prompt_single_system")

        user_prompt = self._tr("ai_prompt_single_user", idx)

        payload = {
            "model": self.lm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": line_data_url}},
                    ],
                },
            ],
            **self._build_sampling_payload(
                response_format=self._response_format_single_text()
            ),
        }

        data = self._post_json(payload)
        content = self._extract_message_content(data)

        try:
            print("RAW SINGLE LINE RESPONSE:")
            print(content[:2000])
        except Exception:
            pass

        if "```" in content:
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
        content = content.strip()

        obj = None
        try:
            obj = json.loads(content)
        except Exception:
            pass

        if obj is None:
            start = content.find("{")
            end = content.rfind("}")
            if start >= 0 and end > start:
                try:
                    obj = json.loads(content[start:end + 1])
                except Exception:
                    pass

        if isinstance(obj, dict):
            txt = _force_text(obj.get("text", "")).strip()
            if txt or txt == "":
                return txt

        lines = _extract_text_lines(content)
        if lines:
            return lines[0].strip()

        return ""

    def _request_line_decision(
            self,
            idx: int,
            kraken_text: str,
            page_text: str,
            box_text: str,
    ) -> str:
        system_prompt = self._tr("ai_prompt_decision_system")

        user_prompt = self._tr(
            "ai_prompt_decision_user",
            idx,
            kraken_text,
            page_text,
            box_text
        )

        payload = {
            "model": self.lm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            **self._build_sampling_payload(
                response_format=self._response_format_single_text()
            ),
        }

        data = self._post_json(payload)
        content = self._extract_message_content(data)

        try:
            print("RAW LINE DECISION RESPONSE:")
            print(content[:2000])
        except Exception:
            pass

        if "```" in content:
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
        content = content.strip()

        obj = None
        try:
            obj = json.loads(content)
        except Exception:
            pass

        if obj is None:
            start = content.find("{")
            end = content.rfind("}")
            if start >= 0 and end > start:
                try:
                    obj = json.loads(content[start:end + 1])
                except Exception:
                    pass

        if isinstance(obj, dict):
            txt = _force_text(obj.get("text", "")).strip()
            if txt:
                return txt

        lines = _extract_text_lines(content)
        if lines:
            return lines[0].strip()

        # sehr konservativer Fallback:
        # BOX > KRAKEN > PAGE
        if _force_text(box_text).strip():
            return _force_text(box_text).strip()
        if _force_text(kraken_text).strip():
            return _force_text(kraken_text).strip()
        return _force_text(page_text).strip()

    def _build_sampling_payload(self, response_format: Optional[dict] = None) -> dict:
        payload = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
            "max_tokens": self.max_tokens,
            "stream": False,
        }

        if response_format is not None:
            payload["response_format"] = response_format

        if self.top_k > 0:
            payload["top_k"] = self.top_k

        if self.min_p > 0:
            payload["min_p"] = self.min_p

        if self.repetition_penalty != 1.0:
            payload["repetition_penalty"] = self.repetition_penalty

        return payload

    def _response_format_lines(self) -> dict:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "ocr_lines",
                "schema": {
                    "type": "object",
                    "properties": {
                        "lines": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "idx": {"type": "integer"},
                                    "text": {"type": "string"}
                                },
                                "required": ["idx", "text"],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["lines"],
                    "additionalProperties": False
                }
            }
        }

    def _response_format_single_text(self) -> dict:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "ocr_single_line",
                "schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"}
                    },
                    "required": ["text"],
                    "additionalProperties": False
                }
            }
        }

    def _normalize_lines(self, revised: list, original: list) -> list:
        revised = [str(x).strip() for x in revised]

        if len(revised) == len(original):
            return revised

        if len(revised) > len(original):
            return revised[:len(original)]

        fixed = list(revised)
        fixed.extend(original[len(revised):])
        return fixed

    def _post_json(self, payload: dict) -> dict:
        if self._cancelled or self.isInterruptionRequested():
            raise RuntimeError(self._tr("msg_ai_cancelled"))

        body = json.dumps(payload).encode("utf-8")
        parsed = urllib.parse.urlparse(self.endpoint)

        if parsed.scheme not in ("http", "https"):
            raise RuntimeError(self._tr("ai_err_bad_scheme", parsed.scheme))

        host = parsed.hostname
        port = parsed.port
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query

        if not host:
            raise RuntimeError(self._tr("ai_err_invalid_endpoint"))

        conn = None
        try:
            if parsed.scheme == "https":
                conn = http.client.HTTPSConnection(host, port or 443, timeout=600)
            else:
                conn = http.client.HTTPConnection(host, port or 80, timeout=600)

            self._active_conn = conn

            conn.request(
                "POST",
                path,
                body=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer lm-studio"
                }
            )

            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_ai_cancelled"))

            resp = conn.getresponse()
            raw = resp.read().decode("utf-8", errors="replace")

            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_ai_cancelled"))

            if resp.status >= 400:
                raise RuntimeError(f"HTTP {resp.status}: {raw}")

            return json.loads(raw)

        except socket.timeout:
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_ai_cancelled"))
            raise RuntimeError(self._tr("ai_err_timeout"))

        except json.JSONDecodeError as e:
            raise RuntimeError(self._tr("ai_err_invalid_json", e))

        except Exception as e:
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_ai_cancelled"))
            raise

        finally:
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass
            if self._active_conn is conn:
                self._active_conn = None

    def _extract_message_content(self, data: dict) -> str:
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError(
                f"LM Server lieferte keine choices. Antwort:\n{json.dumps(data, ensure_ascii=False)[:3000]}"
            )

        choice0 = choices[0] or {}
        message = choice0.get("message", {}) if isinstance(choice0, dict) else {}

        def flatten(val):
            if val is None:
                return ""
            if isinstance(val, bytes):
                return val.decode("utf-8", errors="replace").strip()
            if isinstance(val, str):
                return val.strip()
            if isinstance(val, list):
                parts = []
                for part in val:
                    if isinstance(part, bytes):
                        txt = part.decode("utf-8", errors="replace").strip()
                        if txt:
                            parts.append(txt)
                    elif isinstance(part, str) and part.strip():
                        parts.append(part.strip())
                    elif isinstance(part, dict):
                        for key in ("text", "content", "output_text"):
                            v = part.get(key)
                            if isinstance(v, bytes):
                                txt = v.decode("utf-8", errors="replace").strip()
                                if txt:
                                    parts.append(txt)
                            elif isinstance(v, str) and v.strip():
                                parts.append(v.strip())
                return "\n".join(parts).strip()
            if isinstance(val, dict):
                for key in ("text", "content", "output_text"):
                    v = val.get(key)
                    if isinstance(v, bytes):
                        txt = v.decode("utf-8", errors="replace").strip()
                        if txt:
                            return txt
                    elif isinstance(v, str) and v.strip():
                        return v.strip()
            return _force_text(val).strip()

        # 1) ZUERST nur echte Ausgabe lesen
        candidates = []
        if isinstance(message, dict):
            candidates.append(message.get("content"))
            candidates.append(message.get("text"))
            candidates.append(message.get("output_text"))

        if isinstance(choice0, dict):
            candidates.append(choice0.get("content"))
            candidates.append(choice0.get("text"))

        for cand in candidates:
            txt = flatten(cand)
            if txt:
                # <think> entfernen, falls ein Modell sowas trotzdem in content schreibt
                txt = re.sub(r"<think>.*?</think>", "", txt, flags=re.DOTALL).strip()
                if txt:
                    return txt

        # 2) reasoning_content NICHT als normale Antwort verwenden
        reasoning = ""
        if isinstance(message, dict):
            rc = message.get("reasoning_content")
            if isinstance(rc, str) and rc.strip():
                reasoning = rc.strip()

        finish_reason = ""
        if isinstance(choice0, dict):
            finish_reason = str(choice0.get("finish_reason", "")).strip()

        if reasoning:
            cleaned = re.sub(r"<think>.*?</think>", "", reasoning, flags=re.DOTALL).strip()

            # Falls reasoning_content selbst schon JSON enthält, nutzen wir es als Notfall-Fallback
            if cleaned:
                if cleaned.startswith("{") or '"lines"' in cleaned or '"text"' in cleaned:
                    return cleaned

            if finish_reason == "length":
                raise RuntimeError(
                    self._tr("ai_err_reasoning_truncated")
                )

            raise RuntimeError(
                self._tr("ai_err_reasoning_only")
            )

        raise RuntimeError(self._tr("ai_err_no_content"))

    def _request_block_reread(
            self,
            block_data_url: str,
            start_idx: int,
            end_idx: int,
            current_lines: List[str],
    ) -> List[str]:
        count = end_idx - start_idx

        system_prompt = self._tr("ai_prompt_block_system")

        joined_hint = "\n".join(
            f"{i}: {txt}" for i, txt in enumerate(current_lines)
        )

        user_prompt = self._tr(
            "ai_prompt_block_user",
            count,
            joined_hint
        )

        payload = {
            "model": self.lm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": block_data_url}},
                    ],
                },
            ],
            **self._build_sampling_payload(
                response_format=self._response_format_lines()
            ),
        }

        data = self._post_json(payload)
        content = self._extract_message_content(data)

        try:
            print("RAW BLOCK RESPONSE:")
            print(content[:3000])
        except Exception:
            pass

        obj = _extract_json_payload(content)
        if not isinstance(obj, dict):
            raise ValueError(
                self._tr("ai_err_block_invalid_json", content[:3000] if content else "<leer>")
            )

        lines = obj.get("lines")
        if not isinstance(lines, list):
            raise ValueError(
                self._tr("ai_err_block_invalid_lines", content[:3000] if content else "<leer>")
            )

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
            txt = out[i].strip()
            fallback = current_lines[i] if i < len(current_lines) else ""
            if txt:
                fixed.append(txt)
            else:
                fixed.append(fallback)

        return fixed

    def _chunk_records(self, recs: List[RecordView], block_size: int = 3) -> List[Tuple[int, int]]:
        chunks: List[Tuple[int, int]] = []
        i = 0
        n = len(recs)
        while i < n:
            j = min(n, i + block_size)
            chunks.append((i, j))
            i = j
        return chunks

    def run(self):
        if self._cancelled or self.isInterruptionRequested():
            self.failed_revision.emit(self.path, self._tr("msg_ai_cancelled"))
            return
        try:
            original_lines = [rv.text for rv in self.recs]

            if not self.recs:
                self.finished_revision.emit(self.path, [])
                return

            self.status_changed.emit(self._tr("ai_status_start_free_ocr", os.path.basename(self.path)))
            self.progress_changed.emit(0)

            # -------------------------------------------------
            # 1/3 BOX-OCR zuerst = Primärquelle
            # -------------------------------------------------
            self.status_changed.emit(self._tr("ai_status_step1_title", os.path.basename(self.path)))

            box_lines: List[str] = []
            total = max(1, len(self.recs))

            for i, rv in enumerate(self.recs):
                if self._cancelled or self.isInterruptionRequested():
                    raise RuntimeError(self._tr("msg_ai_cancelled"))

                self.status_changed.emit(
                    self._tr("ai_status_step1_line", i + 1, total, os.path.basename(self.path))
                )

                try:
                    line_data_url = _crop_single_line_to_data_url(
                        self.path,
                        rv,
                        pad_x=3,
                        pad_y=3,
                        extra_context_y=1,
                    )
                    box_text = self._request_single_line_reread(
                        line_data_url=line_data_url,
                        idx=rv.idx,
                        current_text=""
                    )
                except Exception as e:
                    print(f"BOX OCR ERROR idx={rv.idx}: {e}")
                    box_text = rv.text

                if not str(box_text).strip():
                    box_text = rv.text

                box_lines.append(str(box_text).strip())

                self.progress_changed.emit(int(((i + 1) / total) * 55))

            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_ai_cancelled"))

            is_form_like = self._looks_like_form_layout()

            # -------------------------------------------------
            # 2/3 Block-OCR als Kontext (statt kompletter Seite)
            # -------------------------------------------------
            if is_form_like:
                self.status_changed.emit(
                    self._tr("ai_status_step2_form", os.path.basename(self.path))
                )
            else:
                self.status_changed.emit(
                    self._tr("ai_status_step2_plain", os.path.basename(self.path))
                )

            # Startwert: Kraken-Zeilen als Fallback
            page_lines = [rv.text for rv in self.recs]

            # kleine Blöcke halten den Prompt sicher unter dem Kontextlimit
            chunks = self._chunk_records(self.recs, block_size=3)

            for chunk_idx, (start, end) in enumerate(chunks, start=1):
                if self._cancelled or self.isInterruptionRequested():
                    raise RuntimeError(self._tr("msg_ai_cancelled"))

                self.status_changed.emit(
                    self._tr("ai_status_step2_chunk", chunk_idx, len(chunks), start + 1, end)
                )

                try:
                    block_data_url = _crop_block_to_data_url_context(
                        self.path,
                        self.recs,
                        start,
                        end,
                        pad_x=40,
                        pad_y=35,
                    )

                    reread = self._request_block_reread(
                        block_data_url=block_data_url,
                        start_idx=start,
                        end_idx=end,
                        current_lines=page_lines[start:end],
                    )

                    if isinstance(reread, list) and len(reread) == (end - start):
                        for local_i, txt in enumerate(reread):
                            txt = _clean_ocr_text(txt)
                            if txt:
                                page_lines[start + local_i] = txt

                except Exception as e:
                    print(f"BLOCK OCR ERROR {start}-{end}: {e}")

                # leichter Fortschritt im Kontext-Schritt
                self.progress_changed.emit(55 + int((chunk_idx / max(1, len(chunks))) * 15))

            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_ai_cancelled"))

            # -------------------------------------------------
            # 3/3 Merge: BOX bleibt Primärquelle, PAGE nur schwacher Kontext
            # -------------------------------------------------
            self.status_changed.emit(
                self._tr("ai_status_step3_merge", os.path.basename(self.path))
            )

            final_lines: List[str] = []

            for i, rv in enumerate(self.recs):
                kraken_text = str(rv.text or "").strip()
                box_text = str(box_lines[i] if i < len(box_lines) else "").strip()
                page_text = str(page_lines[i] if i < len(page_lines) else "").strip()
                prev_final = final_lines[i - 1] if i > 0 else ""

                has_locked_bbox = self._frozen_bboxes[i] is not None

                if has_locked_bbox:
                    # Manuell gesetzte Overlay-Box ist die einzige geometrische Wahrheitsquelle.
                    # Kein Block-/Page-Kontext darf diese Zeile überschreiben.
                    best_text = _clean_ocr_text(box_text)

                    if not best_text:
                        best_text = _clean_ocr_text(kraken_text)
                else:
                    need_lm_decision = (
                            self._is_suspicious_box_result(box_text)
                            or (
                                    box_text
                                    and page_text
                                    and self._normalize_compare_text(box_text) != self._normalize_compare_text(
                                page_text)
                            )
                    )

                    if need_lm_decision:
                        best_text = self._request_line_decision(
                            idx=i,
                            kraken_text=kraken_text,
                            page_text=page_text,
                            box_text=box_text,
                        ).strip()

                        if not best_text:
                            best_text = self._choose_final_line_text(
                                kraken_text=kraken_text,
                                box_text=box_text,
                                page_text=page_text,
                                prev_final_text=prev_final,
                            )
                    else:
                        best_text = self._choose_final_line_text(
                            kraken_text=kraken_text,
                            box_text=box_text,
                            page_text=page_text,
                            prev_final_text=prev_final,
                        )

                final_lines.append(best_text)
                self.progress_changed.emit(55 + int(((i + 1) / total) * 45))

            if len(final_lines) != len(self.recs):
                raise ValueError(
                    self._tr("ai_err_final_merge_count", len(final_lines), len(self.recs))
                )

            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_ai_cancelled"))

            self.status_changed.emit(self._tr("ai_status_done", os.path.basename(self.path)))
            self.progress_changed.emit(100)
            self.finished_revision.emit(self.path, final_lines)

        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode("utf-8", errors="replace")
            except Exception:
                body = str(e)
            self.failed_revision.emit(self.path, f"HTTP-Fehler: {e}\n{body}")

        except urllib.error.URLError as e:
            self.failed_revision.emit(self.path, self._tr("ai_err_server_unreachable", e))

        except socket.timeout:
            self.failed_revision.emit(self.path, self._tr("ai_err_timeout"))

        except Exception as e:
            msg = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            self.failed_revision.emit(self.path, msg)


class HFDownloadWorker(QThread):
    progress_changed = Signal(int)
    status_changed = Signal(str)
    finished_download = Signal(str)
    failed_download = Signal(str)

    def __init__(
            self,
            repo_id: str,
            local_dir: str,
            prepare_cmds: List[List[str]],
            install_cmd: List[str],
            download_cmd: List[str],
            tr_func=None,
            parent=None
    ):
        super().__init__(parent)
        self._tr = tr_func or (lambda key, *args: (TRANSLATIONS["de"].get(key, key).format(*args) if args else TRANSLATIONS["de"].get(key, key)))
        self.repo_id = repo_id
        self.local_dir = local_dir
        self.prepare_cmds = prepare_cmds or []
        self.install_cmd = install_cmd
        self.download_cmd = download_cmd
        self._proc = None
        self._cancel_requested = False
        self._last_status_line = ""
        self._current_file = ""
        self._last_finished_file = ""
        self._repo_files: List[Tuple[str, int]] = []  # [(rel_path, size), ...]
        self._last_progress_percent = 0

    def cancel(self):
        self._cancel_requested = True
        self.requestInterruption()
        proc = self._proc
        if proc is not None:
            try:
                proc.terminate()
            except Exception:
                pass

    def _stream_reader_to_queue(self, pipe, output_queue: "queue.Queue[str]"):
        """
        Liest stdout/stderr zeichenweise und splittet sowohl auf \\n als auch auf \\r.
        Dadurch kommen auch tqdm-/hf-Fortschrittsupdates an.
        """
        try:
            if pipe is None:
                return

            buf = ""
            while True:
                ch = pipe.read(1)
                if ch == "":
                    if buf.strip():
                        output_queue.put(buf)
                    break

                if ch in ("\n", "\r"):
                    if buf.strip():
                        output_queue.put(buf)
                    buf = ""
                else:
                    buf += ch
        except Exception:
            pass

    def _run_simple_command(self, cmd: List[str], status_text: str):
        self.status_changed.emit(status_text)

        creationflags = 0
        if sys.platform.startswith("win"):
            creationflags = subprocess.CREATE_NO_WINDOW

        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            universal_newlines=True,
            creationflags=creationflags
        )

        output_queue = queue.Queue()

        reader_thread = threading.Thread(
            target=self._stream_reader_to_queue,
            args=(self._proc.stdout, output_queue),
            daemon=True
        )
        reader_thread.start()

        while True:
            if self._cancel_requested or self.isInterruptionRequested():
                break

            while True:
                try:
                    line = output_queue.get_nowait()
                except queue.Empty:
                    break
                self._consume_output_line(line)

            ret = self._proc.poll()
            if ret is not None:
                break

            self.msleep(100)

        if self._cancel_requested or self.isInterruptionRequested():
            try:
                self._proc.terminate()
            except Exception:
                pass
            raise RuntimeError(self._tr("hf_error_cancelled"))

        ret = self._proc.wait()
        if ret != 0:
            raise RuntimeError(f"Befehl wurde mit Exit-Code {ret} beendet:\n{' '.join(cmd)}")

    def _consume_output_line(self, line: str):
        txt = _force_text(line).strip()
        if not txt:
            return

        self._last_status_line = txt

        current_file = self._extract_current_file_from_output(txt)
        if current_file:
            self._current_file = current_file

        # WICHTIG:
        # KEIN Prozentwert aus der hf-Ausgabe direkt für den ProgressBar übernehmen,
        # weil das meist nur der Fortschritt der aktuellen Datei ist
        # und NICHT des gesamten Modell-Downloads.

        if "still waiting to acquire lock" in txt.lower():
            self.status_changed.emit(self._tr("hf_status_waiting_for_lock"))
        else:
            self.status_changed.emit(txt)

    def _sum_downloaded_bytes(self, folder: str) -> int:
        total = 0
        if not os.path.isdir(folder):
            return 0

        for root, _dirs, files in os.walk(folder):
            for name in files:
                full = os.path.join(root, name)

                # Metadateien ignorieren
                low = name.lower()
                if low.endswith(".lock"):
                    continue
                if low in {".gitattributes", "refs", "snapshots"}:
                    continue

                try:
                    total += os.path.getsize(full)
                except Exception:
                    pass
        return total

    def _fetch_repo_files(self) -> List[Tuple[str, int]]:
        try:
            from huggingface_hub import HfApi

            api = HfApi()
            info = api.model_info(self.repo_id, files_metadata=True)

            out = []
            for sibling in getattr(info, "siblings", []) or []:
                rel = getattr(sibling, "rfilename", None) or getattr(sibling, "path", None)
                size = getattr(sibling, "size", None)

                if not rel or not isinstance(size, int) or size <= 0:
                    continue

                low = str(rel).lower().replace("\\", "/")
                if low.endswith(".lock"):
                    continue

                out.append((str(rel).replace("\\", "/"), int(size)))

            return out
        except Exception:
            return []

    def _repo_total_bytes(self) -> int:
        return sum(size for _rel, size in self._repo_files)

    def _scan_local_progress(self) -> Tuple[int, int, str]:
        """
        Returns:
            downloaded_bytes,
            finished_files_count,
            last_finished_file
        """
        downloaded = 0
        finished = 0
        last_finished = ""

        if not os.path.isdir(self.local_dir):
            return 0, 0, ""

        for rel_path, expected_size in self._repo_files:
            full = os.path.join(self.local_dir, *rel_path.split("/"))
            if not os.path.isfile(full):
                continue

            try:
                size = os.path.getsize(full)
            except Exception:
                continue

            downloaded += size

            if expected_size > 0 and size >= expected_size:
                finished += 1
                last_finished = rel_path

        return downloaded, finished, last_finished

    def _extract_current_file_from_output(self, line: str) -> str:
        txt = (line or "").strip()

        patterns = [
            r"Downloading '([^']+)'",
            r"Download file to .*?[/\\\\]([^/\\\\]+)$",
            r"Fetching (\S+)",
        ]

        for pat in patterns:
            m = re.search(pat, txt, flags=re.IGNORECASE)
            if m:
                return m.group(1).strip()

        return ""

    def run(self):
        try:
            os.makedirs(self.local_dir, exist_ok=True)

            install_cmd = list(self.install_cmd)
            download_cmd = list(self.download_cmd)

            self.progress_changed.emit(0)
            self.status_changed.emit("Ermittle Dateiliste und Gesamtgröße des Modells …")

            self._repo_files = self._fetch_repo_files()
            total_bytes = self._repo_total_bytes()
            total_files = len(self._repo_files)

            start_time = time.time()

            creationflags = 0
            if sys.platform.startswith("win"):
                creationflags = subprocess.CREATE_NO_WINDOW

            # 1) Vorbereitende Befehle (z. B. venv) ausführen
            for cmd in self.prepare_cmds:
                cmd_text = " ".join(cmd).lower()
                if "-m venv" in cmd_text:
                    self._run_simple_command(cmd, "Erzeuge geschützte Python-Umgebung für Whisper …")
                else:
                    self._run_simple_command(cmd, "Bereite Whisper-Umgebung vor …")

            # 2) Requirements installieren
            self._run_simple_command(
                install_cmd,
                "Installiere Python-Requirements für Whisper …"
            )

            # 3) Dateiliste/Gesamtgröße ermitteln
            self.status_changed.emit("Ermittle Dateiliste und Gesamtgröße des Modells …")
            self._repo_files = self._fetch_repo_files()
            total_bytes = self._repo_total_bytes()
            total_files = len(self._repo_files)
            start_time = time.time()

            # 3) Download starten
            self.status_changed.emit("Starte Modell-Download …")
            self._proc = subprocess.Popen(
                download_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                universal_newlines=True,
                creationflags=creationflags
            )

            output_queue = queue.Queue()

            reader_thread = threading.Thread(
                target=self._stream_reader_to_queue,
                args=(self._proc.stdout, output_queue),
                daemon=True
            )
            reader_thread.start()

            last_emit_ts = 0.0

            while True:
                if self._cancel_requested or self.isInterruptionRequested():
                    break

                while True:
                    try:
                        line = output_queue.get_nowait()
                    except queue.Empty:
                        break
                    self._consume_output_line(line)

                ret = self._proc.poll()

                now = time.time()
                if now - last_emit_ts >= 0.25:
                    downloaded, finished_files, last_finished = self._scan_local_progress()
                    elapsed = max(0.0, now - start_time)

                    if last_finished:
                        self._last_finished_file = last_finished

                    if total_files > 0:
                        percent_tenths = int((finished_files / total_files) * 1000)  # 0.1%-Schritte
                    else:
                        percent_tenths = 0

                    percent_tenths = max(0, min(1000, percent_tenths))

                    self._last_progress_percent = percent_tenths
                    self.progress_changed.emit(percent_tenths)

                    lines = [
                        f"{percent_tenths / 10:.1f}%  |  2,9GB (total)  |  {elapsed:.0f}s (ca. 2-5min)"
                    ]

                    if total_files > 0:
                        lines.append(self._tr("hf_status_files_done", finished_files, total_files))

                    if self._current_file:
                        lines.append(self._tr("hf_status_current_file", self._current_file))

                    if self._last_finished_file:
                        lines.append(self._tr("hf_status_last_finished", self._last_finished_file))

                    self.status_changed.emit("\n".join(lines))
                else:
                    downloaded_mb = downloaded / (1024 * 1024)
                    speed = (downloaded_mb / elapsed) if elapsed > 0 else 0.0

                    lines = [
                        f"{downloaded_mb:.1f} MB geladen  |  {elapsed:.0f}s  |  {speed:.1f} MB/s"
                    ]

                    if total_files > 0:
                        lines.append(self._tr("hf_status_files_done", finished_files, total_files))

                    if self._current_file:
                        lines.append(self._tr("hf_status_current_file", self._current_file))

                    if self._last_finished_file:
                        lines.append(self._tr("hf_status_last_finished", self._last_finished_file))

                    self.status_changed.emit("\n".join(lines))

                if ret is not None:
                    break

                self.msleep(100)

            if self._cancel_requested or self.isInterruptionRequested():
                try:
                    self._proc.terminate()
                except Exception:
                    pass
                raise RuntimeError(self._tr("hf_error_cancelled"))

            ret = self._proc.wait()
            if ret != 0:
                raise RuntimeError(self._tr("hf_error_hf_exit", ret))

            self.progress_changed.emit(1000)
            self.status_changed.emit(self._tr("hf_status_download_done"))
            self.finished_download.emit(self.local_dir)


        except FileNotFoundError:
            self.failed_download.emit(self._tr("hf_error_python_missing"))


        except Exception as e:

            msg = str(e)

            low = msg.lower()

            if "externally-managed-environment" in low:
                msg = self._tr("hf_error_externally_managed")
            elif "no module named venv" in low or "ensurepip" in low:
                msg = self._tr("hf_error_no_venv")
            elif "no such file or directory" in low and "python3" in low:
                msg = self._tr("hf_error_python3_missing")

            self.failed_download.emit(msg)
        finally:
            self._proc = None


class VoiceLineFillWorker(QThread):
    finished_line = Signal(str, int, str)  # path, line_index, text
    failed_line = Signal(str, str)  # path, error_message
    progress_changed = Signal(int)  # 0..100
    status_changed = Signal(str)  # status text

    def __init__(
            self,
            path: str,
            line_index: int,
            model_dir: str,
            device: str = "cpu",
            compute_type: str = "int8",
            language: Optional[str] = None,
            input_device=None,
            input_samplerate: Optional[int] = None,
            parent=None
    ):
        super().__init__(parent)
        self.path = path
        self.line_index = int(line_index)
        self.model_dir = model_dir
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.input_device = input_device
        self.input_samplerate = int(input_samplerate) if input_samplerate else None

        self._finish_requested = False
        self._cancel_requested = False
        self._audio_chunks = []
        self._stream = None

    def _tr(self, *args):
        if len(args) == 1:
            return QCoreApplication.translate("VoiceLineFillWorker", args[0])
        return QCoreApplication.translate(*args)

    def stop(self):
        # normales Ende der Aufnahme -> Worker beendet den Stream selbst
        self._finish_requested = True

    def cancel(self):
        # echter Abbruch -> Worker beendet den Stream selbst
        self._cancel_requested = True
        self.requestInterruption()
        self._finish_requested = False

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            # optional für Debug
            try:
                self.status_changed.emit(f"Audio-Status: {status}")
            except Exception:
                pass

        if indata is not None and len(indata):
            self._audio_chunks.append(indata.copy())

        if self._cancel_requested or self._finish_requested:
            raise sd.CallbackStop()

    def _record_until_stop(self):
        self.status_changed.emit(
            f"Aufnahmegerät: {self.input_device} | Samplerate: {self.input_samplerate or 'auto'}"
        )
        self.status_changed.emit("Mikrofon aktiv. Bitte nur die aktuell ausgewählte Zeile diktieren.")
        self.progress_changed.emit(5)

        samplerate = self.input_samplerate
        if not samplerate:
            try:
                dev_info = sd.query_devices(self.input_device, "input")
                samplerate = int(dev_info.get("default_samplerate", VOICE_SAMPLE_RATE))
            except Exception:
                samplerate = VOICE_SAMPLE_RATE

        try:
            sd.check_input_settings(
                device=self.input_device,
                samplerate=samplerate,
                channels=VOICE_CHANNELS,
                dtype="float32",
            )
        except Exception:
            samplerate = VOICE_SAMPLE_RATE

        self._record_samplerate = int(samplerate)
        self._stream = None

        stream = None
        try:
            stream = sd.InputStream(
                device=self.input_device,
                samplerate=self._record_samplerate,
                channels=VOICE_CHANNELS,
                dtype="float32",
                blocksize=VOICE_BLOCKSIZE,
                callback=self._audio_callback
            )
            self._stream = stream
            stream.start()

            while stream.active:
                if self._cancel_requested or self.isInterruptionRequested():
                    try:
                        stream.abort(ignore_errors=True)
                    except Exception:
                        pass
                    break

                if self._finish_requested:
                    try:
                        stream.abort(ignore_errors=True)
                    except Exception:
                        pass
                    break

                self.msleep(20)

        finally:
            try:
                if stream is not None:
                    try:
                        stream.stop()
                    except Exception:
                        pass
                    try:
                        stream.close()
                    except Exception:
                        pass
            finally:
                self._stream = None

    def _safe_ascii_temp_root(self) -> str:
        if sys.platform.startswith("win"):
            base = r"C:\bk_temp"
        else:
            base = "/tmp/bk_temp"

        os.makedirs(base, exist_ok=True)
        return base

    def _write_temp_wav(self) -> str:
        if not self._audio_chunks:
            raise RuntimeError(self._tr("warn_voice_no_audio_data"))

        audio = np.concatenate(self._audio_chunks, axis=0).flatten()

        min_samples = int(0.35 * max(1, getattr(self, "_record_samplerate", VOICE_SAMPLE_RATE)))
        if len(audio) < min_samples:
            raise RuntimeError("Aufnahme zu kurz. Bitte etwas länger sprechen.")

        audio = np.clip(audio, -1.0, 1.0)

        tmp_dir = os.path.join(self._safe_ascii_temp_root(), "voice")
        os.makedirs(tmp_dir, exist_ok=True)

        tmp_path = os.path.join(
            tmp_dir,
            f"voice_{int(time.time() * 1000)}.wav"
        )

        pcm16 = (audio * 32767.0).astype(np.int16)
        samplerate = int(getattr(self, "_record_samplerate", VOICE_SAMPLE_RATE))

        with wave.open(tmp_path, "wb") as wf:
            wf.setnchannels(VOICE_CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(samplerate)
            wf.writeframes(pcm16.tobytes())

        return tmp_path

    def _replace_spoken_punctuation_with_placeholders(self, text: str) -> str:
        txt = (text or "").strip()

        # wichtig: längere Begriffe zuerst
        replacements = [
            (r"\bschräg\s*strich\b[.,;:!?]?", " <<SLASH>> "),
            (r"\bslash\b[.,;:!?]?", " <<SLASH>> "),

            (r"\bdoppel\s*punkt\b[.,;:!?]?", " <<COLON>> "),
            (r"\bsemi\s*kolon\b[.,;:!?]?", " <<SEMICOLON>> "),
            (r"\bfrage\s*zeichen\b[.,;:!?]?", " <<QUESTION>> "),
            (r"\bausrufe\s*zeichen\b[.,;:!?]?", " <<EXCLAMATION>> "),
            (r"\banführungs\s*zeichen\b[.,;:!?]?", " <<QUOTE>> "),
            (r"\bgänse\s*füßchen\b[.,;:!?]?", " <<QUOTE>> "),
            (r"\bgleichheits\s*zeichen\b[.,;:!?]?", " <<EQUALS>> "),
            (r"\bklammer\s+auf\b[.,;:!?]?", " <<LPAREN>> "),
            (r"\bklammer\s+zu\b[.,;:!?]?", " <<RPAREN>> "),
            (r"\bbinde\s*strich\b[.,;:!?]?", " <<HYPHEN>> "),
            (r"\bunter\s*strich\b[.,;:!?]?", " <<UNDERSCORE>> "),

            (r"\bkomma\b[.,;:!?]?", " <<COMMA>> "),
            (r"\bpunkt\b[.,;:!?]?", " <<DOT>> "),
            (r"\bminus\b[.,;:!?]?", " <<HYPHEN>> "),
            (r"\bgleich\b[.,;:!?]?", " <<EQUALS>> "),
            (r"\bprozent\b[.,;:!?]?", " <<PERCENT>> "),
            (r"\beuro\b[.,;:!?]?", " <<EURO>> "),
            (r"\braute\b[.,;:!?]?", " <<HASH>> "),
            (r"\bhashtag\b[.,;:!?]?", " <<HASH>> "),
            (r"\bplus\b[.,;:!?]?", " <<PLUS>> "),
            (r"\bstern\b[.,;:!?]?", " <<ASTERISK>> "),
            (r"\basterisk\b[.,;:!?]?", " <<ASTERISK>> "),
            (r"\bunderscore\b[.,;:!?]?", " <<UNDERSCORE>> "),
        ]

        for pattern, repl in replacements:
            txt = re.sub(pattern, repl, txt, flags=re.IGNORECASE)

        txt = re.sub(r"\s+", " ", txt).strip()
        return txt

    def _restore_punctuation_placeholders(self, text: str) -> str:
        txt = f" {(text or '').strip()} "

        replacements = {
            "<<SLASH>>": "/",
            "<<DOT>>": ".",
            "<<COLON>>": ":",
            "<<HYPHEN>>": "-",
            "<<COMMA>>": ",",
            "<<SEMICOLON>>": ";",
            "<<QUESTION>>": "?",
            "<<EXCLAMATION>>": "!",
            "<<QUOTE>>": "\"",
            "<<EURO>>": "€",
            "<<EQUALS>>": "=",
            "<<PERCENT>>": "%",
            "<<LPAREN>>": "(",
            "<<RPAREN>>": ")",
            "<<HASH>>": "#",
            "<<PLUS>>": "+",
            "<<ASTERISK>>": "*",
            "<<UNDERSCORE>>": "_",
        }

        for placeholder, char in replacements.items():
            txt = txt.replace(placeholder, char)

        # Punkt vor Doppelpunkt automatisch entfernen:
        # "Ort.:" / "Ort. :" / "Ort :" -> "Ort:"
        txt = re.sub(r"\.\s*:", ":", txt)

        # kein Leerzeichen vor klassischen Satzzeichen
        txt = re.sub(r"\s+([.,:;?!%€)\]])", r"\1", txt)

        # kein Leerzeichen nach öffnenden Klammern
        txt = re.sub(r"([(\[\{])\s+", r"\1", txt)

        # keine Leerzeichen um technische Zeichen
        txt = re.sub(r"\s*([/\-=+*_#])\s*", r"\1", txt)

        # Doppelte Spaces glätten
        txt = re.sub(r"\s+", " ", txt).strip()

        return txt

    def _postprocess_transcript(self, text: str) -> str:
        txt = (text or "").strip()

        # gesprochene Satzzeichen zuerst in Platzhalter umwandeln
        txt = self._replace_spoken_punctuation_with_placeholders(txt)

        # automatische Satzendzeichen von Whisper nur entfernen,
        # wenn sie NICHT aus einem Platzhalter entstanden sind
        txt = re.sub(r"[.!?]+$", "", txt).strip()

        # Platzhalter zurückwandeln
        txt = self._restore_punctuation_placeholders(txt)

        return re.sub(r"\s+", " ", txt).strip()

    def run(self):
        tmp_wav = None
        try:
            self._audio_chunks = []
            if not os.path.isdir(self.model_dir):
                raise RuntimeError("Faster-Whisper-Modellordner wurde nicht gefunden.")

            self.progress_changed.emit(0)
            self._record_until_stop()

            if self._cancel_requested or self.isInterruptionRequested():
                raise RuntimeError(self._tr("warn_voice_cancelled"))

            if not self._finish_requested:
                raise RuntimeError(self._tr("warn_voice_not_finished"))

            if not self._audio_chunks:
                raise RuntimeError(self._tr("warn_voice_no_audio_data"))

            self.status_changed.emit(self._tr("voice_status_prepare_wav"))
            self.progress_changed.emit(20)
            tmp_wav = self._write_temp_wav()

            self.status_changed.emit(self._tr("voice_status_load_whisper"))
            self.progress_changed.emit(35)

            from faster_whisper import WhisperModel

            safe_model_dir = os.path.abspath(self.model_dir)
            safe_wav_path = os.path.abspath(tmp_wav)

            kwargs = {
                "beam_size": 5,
                "vad_filter": False,
                "condition_on_previous_text": False,
                "task": "transcribe",
                "language": None,
            }

            active_device = self.device
            active_compute = self.compute_type

            try:
                model = WhisperModel(
                    safe_model_dir,
                    device=active_device,
                    compute_type=active_compute
                )

                self.status_changed.emit(
                    self._tr("voice_status_transcribe_line", active_device, active_compute)
                )
                self.progress_changed.emit(60)

                segments, info = model.transcribe(safe_wav_path, **kwargs)

            except Exception as e:
                msg = str(e).lower()

                if active_device == "cuda" and ("out of memory" in msg or "cuda failed" in msg):
                    try:
                        if torch.cuda.is_available():
                            torch.cuda.empty_cache()
                    except Exception:
                        pass

                    self.status_changed.emit(
                        "CUDA-Speicher voll – Whisper wechselt automatisch auf CPU..."
                    )

                    model = WhisperModel(
                        safe_model_dir,
                        device="cpu",
                        compute_type="int8"
                    )

                    self.status_changed.emit("Transkribiere ausgewählte Zeile lokal (cpu/int8)...")
                    self.progress_changed.emit(60)

                    segments, info = model.transcribe(safe_wav_path, **kwargs)
                else:
                    raise

            try:
                detected_lang = getattr(info, "language", None)
                if detected_lang:
                    self.status_changed.emit(f"Erkannte Sprache: {detected_lang}")
            except Exception:
                pass

            segments = list(segments)

            full_text = " ".join((seg.text or "").strip() for seg in segments).strip()
            full_text = self._postprocess_transcript(full_text)

            if not full_text:
                raise RuntimeError("Es konnte kein verständlicher Text erkannt werden.")

            self.progress_changed.emit(100)
            self.finished_line.emit(self.path, self.line_index, full_text)

        except Exception as e:
            self.failed_line.emit(self.path, str(e))
        finally:
            if tmp_wav and os.path.exists(tmp_wav):
                try:
                    os.remove(tmp_wav)
                except Exception:
                    pass


class ProgressStatusDialog(QDialog):
    cancel_requested = Signal()

    def __init__(self, title: str, tr, parent=None):
        super().__init__(parent)
        self._tr = tr
        self.setWindowTitle(title)

        self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        self.setWindowFlag(Qt.Dialog, True)

        if parent is not None:
            self.setWindowModality(Qt.WindowModal)
        else:
            self.setWindowModality(Qt.ApplicationModal)

        lay = QVBoxLayout(self)

        self.lbl_status = QLabel(self._tr("progress_status_ready"))
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setMinimumWidth(320)
        self.lbl_status.setMaximumWidth(520)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)  # sichtbarer Balken
        self.progress.setValue(0)
        self.progress.setFormat("%p%")

        self.btn_cancel = QPushButton(self._tr("btn_cancel"))
        self.btn_cancel.clicked.connect(self.cancel_requested.emit)

        lay.addWidget(self.lbl_status)
        lay.addWidget(self.progress)
        lay.addWidget(self.btn_cancel)

        self.adjustSize()

    def set_status(self, text: str):
        self.lbl_status.setText(text)
        self.adjustSize()

    def set_progress(self, value: int):
        raw = max(0, int(value))

        if raw <= 100:
            percent = float(raw)
        else:
            percent = raw / 10.0

        percent = max(0.0, min(100.0, percent))

        if self.progress.minimum() != 0 or self.progress.maximum() != 100:
            self.progress.setRange(0, 100)

        self.progress.setValue(int(round(percent)))
        self.progress.setFormat(f"{percent:.1f}%")

class VoiceRecordDialog(QDialog):
    start_requested = Signal()
    stop_requested = Signal()
    cancel_requested = Signal()

    def __init__(self, tr, parent=None):
        super().__init__(parent)
        self._tr = tr
        self._recording = False
        self._processing = False

        self.setWindowTitle(self._tr("voice_record_title"))
        self.setModal(True)

        lay = QVBoxLayout(self)

        self.lbl_info = QLabel(self._tr("voice_record_info"))
        lay.addWidget(self.lbl_info)

        btn_row = QHBoxLayout()

        self.btn_toggle = QPushButton(self._tr("voice_record_start"))
        self.btn_cancel = QPushButton(self._tr("btn_cancel"))

        btn_row.addWidget(self.btn_toggle)
        btn_row.addWidget(self.btn_cancel)

        lay.addLayout(btn_row)

        self.btn_toggle.clicked.connect(self._on_toggle)
        self.btn_cancel.clicked.connect(self._on_cancel)

        # Start-Button soll standardmäßig aktiv sein
        self.btn_toggle.setDefault(True)
        self.btn_toggle.setAutoDefault(True)
        self.btn_cancel.setDefault(False)
        self.btn_cancel.setAutoDefault(False)
        self.btn_toggle.setFocus(Qt.OtherFocusReason)

    def _keep_start_button_primary(self):
        # Start-Button soll optisch/fokusmäßig immer der primäre Button bleiben
        self.btn_toggle.setDefault(True)
        self.btn_toggle.setAutoDefault(True)
        self.btn_cancel.setDefault(False)
        self.btn_cancel.setAutoDefault(False)
        self.btn_toggle.setFocus(Qt.OtherFocusReason)

    def _on_toggle(self):
        # Während Whisper verarbeitet, Klicks auf "Aufnahme starten" ignorieren
        if self._processing:
            return

        if not self._recording:
            self._recording = True
            self._processing = False
            self.btn_toggle.setText(self._tr("voice_record_stop"))
            self.lbl_info.setText(self._tr("voice_record_info"))
            self._keep_start_button_primary()
            self.start_requested.emit()
        else:
            # Aufnahme endet jetzt, ab hier blockieren bis Whisper fertig ist
            self._recording = False
            self._processing = True

            # Button soll optisch wieder "Aufnahme starten" zeigen,
            # aber intern noch gesperrt bleiben
            self.btn_toggle.setText(self._tr("voice_record_start"))
            self.lbl_info.setText(self._tr("voice_record_processing"))
            self._keep_start_button_primary()

            self.stop_requested.emit()

    def _on_cancel(self):
        self.cancel_requested.emit()
        self.reject()

    def set_recording_state(self, recording: bool):
        self._recording = bool(recording)
        self._processing = False

        self.btn_toggle.setEnabled(True)
        self.btn_toggle.setText(self._tr("voice_record_stop") if self._recording else self._tr("voice_record_start"))
        self.lbl_info.setText(self._tr("voice_record_info"))

        self._keep_start_button_primary()

    def closeEvent(self, event):
        super().closeEvent(event)

# -----------------------------
# EXPORT-DIALOGE
# -----------------------------
class ExportWorker(QThread):
    file_started = Signal(str, int, int)  # display_name, current, total
    file_done = Signal(str, str, int, int)  # display_name, dest_path, current, total
    file_error = Signal(str, str, int, int)
    progress_changed = Signal(int)
    status_changed = Signal(str)
    finished_batch = Signal()

    def __init__(self, render_callback, items: List[TaskItem], fmt: str, folder: str, parent=None):
        super().__init__(parent)
        self.render_callback = render_callback
        self.items = items
        self.fmt = fmt
        self.folder = folder

    def run(self):
        total = len(self.items)
        if total <= 0:
            self.finished_batch.emit()
            return

        for i, it in enumerate(self.items, start=1):
            if self.isInterruptionRequested():
                break

            base_name = os.path.splitext(it.display_name)[0]
            dest_path = os.path.join(self.folder, f"{base_name}.{self.fmt}")

            self.file_started.emit(it.display_name, i, total)
            self.status_changed.emit(f"Exportiere {i}/{total}: {it.display_name}")

            try:
                self.render_callback(dest_path, self.fmt, it)
                self.file_done.emit(it.display_name, dest_path, i, total)
            except Exception as e:
                self.file_error.emit(it.display_name, str(e), i, total)

            self.progress_changed.emit(int((i / total) * 100))

        self.status_changed.emit("Export abgeschlossen.")
        self.finished_batch.emit()

# -----------------------------
# EXPORT-DIALOGE
# -----------------------------
class ExportModeDialog(QDialog):
    def __init__(self, tr, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("export_choose_mode_title"))
        self.choice = None

        lay = QVBoxLayout(self)
        self.rb_all = QRadioButton(tr("export_mode_all"))
        self.rb_sel = QRadioButton(tr("export_mode_selected"))
        self.rb_all.setChecked(True)

        lay.addWidget(self.rb_all)
        lay.addWidget(self.rb_sel)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def accept(self):
        self.choice = "all" if self.rb_all.isChecked() else "selected"
        super().accept()

class ExportSelectFilesDialog(QDialog):
    def __init__(self, tr, items: List[TaskItem], parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("export_select_files_title"))
        self.selected_paths: List[str] = []

        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(tr("export_select_files_hint")))

        self.listw = QListWidget()
        self.listw.setSelectionMode(QAbstractItemView.ExtendedSelection)

        for it in items:
            li = QListWidgetItem(it.display_name)
            li.setData(Qt.UserRole, it.path)
            self.listw.addItem(li)

        lay.addWidget(self.listw)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._on_ok)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def _on_ok(self):
        paths = [i.data(Qt.UserRole) for i in self.listw.selectedItems()]
        self.selected_paths = [p for p in paths if p]
        self.accept()

def pil_to_qpixmap(img: Image.Image) -> QPixmap:
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")
    return QPixmap.fromImage(ImageQt(img))

def render_pdf_page_to_pil(pdf_path: str, page_index: int, dpi: int = 300) -> Image.Image:
    doc = fitz.open(pdf_path)
    try:
        page = doc.load_page(page_index)
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    finally:
        doc.close()

@dataclass
class ImageEditSeparator:
    cx: float
    cy: float
    angle: float = 0.0

    HANDLE_R = 8
    ROT_R = 12
    ROT_OFFSET = 30

    def direction_vector(self) -> Tuple[float, float]:
        return math.sin(self.angle), -math.cos(self.angle)

    def clipped_endpoints(self, w: float, h: float) -> Optional[Tuple[float, float, float, float]]:
        if w <= 1 or h <= 1:
            return None

        vx, vy = self.direction_vector()
        eps = 1e-9
        candidates = []

        if abs(vx) > eps:
            for x in (0.0, float(w)):
                t = (x - self.cx) / vx
                y = self.cy + t * vy
                if -1e-6 <= y <= h + 1e-6:
                    candidates.append((t, x, max(0.0, min(float(h), y))))

        if abs(vy) > eps:
            for y in (0.0, float(h)):
                t = (y - self.cy) / vy
                x = self.cx + t * vx
                if -1e-6 <= x <= w + 1e-6:
                    candidates.append((t, max(0.0, min(float(w), x)), y))

        if len(candidates) < 2:
            return None

        unique = []
        for t, x, y in candidates:
            if not any(abs(x - ux) < 1e-4 and abs(y - uy) < 1e-4 for _, ux, uy in unique):
                unique.append((t, x, y))

        if len(unique) < 2:
            return None

        unique.sort(key=lambda item: item[0])
        _, x1, y1 = unique[0]
        _, x2, y2 = unique[-1]
        return x1, y1, x2, y2

    def top_handle(self, w: float, h: float):
        pts = self.clipped_endpoints(w, h)
        if pts is None:
            return self.cx, self.cy
        x1, y1, x2, y2 = pts
        return (x1, y1) if (y1 < y2 or (abs(y1 - y2) < 1e-6 and x1 <= x2)) else (x2, y2)

    def bottom_handle(self, w: float, h: float):
        pts = self.clipped_endpoints(w, h)
        if pts is None:
            return self.cx, self.cy
        x1, y1, x2, y2 = pts
        return (x2, y2) if (y1 < y2 or (abs(y1 - y2) < 1e-6 and x1 <= x2)) else (x1, y1)

    def distance_to_line(self, px: float, py: float, w: float, h: float) -> float:
        pts = self.clipped_endpoints(w, h)
        if pts is None:
            return 1e9

        x1, y1, x2, y2 = pts
        vx = x2 - x1
        vy = y2 - y1
        wx = px - x1
        wy = py - y1
        denom = math.hypot(vx, vy)

        if denom == 0:
            return math.hypot(px - x1, py - y1)

        return abs(vx * wy - vy * wx) / denom

    def set_from_points(self, p1: Tuple[float, float], p2: Tuple[float, float]):
        x1, y1 = p1
        x2, y2 = p2
        self.cx = (x1 + x2) / 2.0
        self.cy = (y1 + y2) / 2.0
        dx = x2 - x1
        dy = y2 - y1
        if abs(dx) >= 1e-9 or abs(dy) >= 1e-9:
            self.angle = math.atan2(dx, -dy)

    def move_by(self, dx: float, dy: float, w: float, h: float):
        self.cx = max(0.0, min(float(w), self.cx + dx))
        self.cy = max(0.0, min(float(h), self.cy + dy))

    def rotation_handle_pos(self):
        px = math.cos(self.angle)
        py = math.sin(self.angle)
        return self.cx + px * self.ROT_OFFSET, self.cy + py * self.ROT_OFFSET

@dataclass
class ImageEditSettings:
    rotation_angle: float = 0.0
    color_mode: str = "RGB"
    contrast_enabled: bool = False
    crop_enabled: bool = False
    crop_orig: Optional[Tuple[int, int, int, int]] = None
    split_enabled: bool = False
    separator_norm: Optional[Tuple[float, float, float]] = None  # cx/w, cy/h, angle
    smart_split_enabled: bool = False
    white_border_px: int = 0

    erase_enabled: bool = False
    erase_shape: str = ""   # "", "rect", "ellipse"
    erase_orig: Optional[Tuple[int, int, int, int]] = None
    erase_actions: List[Tuple[str, Tuple[int, int, int, int]]] = field(default_factory=list)

class WhiteBorderDialog(QDialog):
    def __init__(self, current_px: int = 0, parent=None):
        super().__init__(parent)
        tr = getattr(parent, "_tr", None)
        self._tr = tr if callable(tr) else (lambda key, *args: (TRANSLATIONS["de"].get(key, key).format(*args) if args else TRANSLATIONS["de"].get(key, key)))
        self.setWindowTitle(self._tr("white_border_title"))

        lay = QVBoxLayout(self)
        form = QFormLayout()

        self.sp_px = QSpinBox()
        self.sp_px.setRange(0, 5000)
        self.sp_px.setValue(int(current_px))

        form.addRow(self._tr("white_border_pixels"), self.sp_px)
        lay.addLayout(form)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText(self._tr("dlg_box_apply"))
        bb.button(QDialogButtonBox.Cancel).setText(self._tr("btn_cancel"))
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def get_value(self) -> int:
        return int(self.sp_px.value())

class ImageEditCanvas(QWidget):
    changed = Signal()
    rotation_committed = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setMinimumSize(700, 520)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.base_image: Optional[Image.Image] = None
        self.view_image: Optional[Image.Image] = None
        self.view_pixmap: Optional[QPixmap] = None
        self.zoom = 1.0
        self.fit_scale = 1.0
        self.show_crop = False
        self.show_separator = False
        self.show_grid = False
        self.grid_spacing = 20
        self.rotation_mode = False
        self.crop_rect: Optional[QRectF] = None
        self.separator: Optional[ImageEditSeparator] = None

        self.show_erase = False
        self.erase_shape = ""   # "", "rect", "ellipse"
        self.erase_rect: Optional[QRectF] = None

        self.drag_mode = None
        self.drag_start = QPointF()
        self.rect_before = None
        self.sep_offset = QPointF()
        self.rotation_angle = 0.0
        self.preview_rotation_angle = 0.0
        self.is_preview_rotating = False
        self.rotation_start_angle = 0.0
        self.rotation_start_mouse_angle = 0.0
        self._img_offset_x = 0.0
        self._img_offset_y = 0.0

    def set_image(self, img: Optional[Image.Image], reset_zoom: bool = True):
        self.base_image = img
        if reset_zoom:
            self.zoom = 1.0
        self._update_view_image()
        if self.view_image and self.show_crop and self.crop_rect is None:
            self.create_default_crop()
        self._ensure_separator_inside()
        self.update()
        self.changed.emit()

    def _update_view_image(self):
        if self.base_image is None:
            self.view_image = None
            self.view_pixmap = None
            self._update_image_offset()
            return

        cw = max(10, self.width())
        ch = max(10, self.height())
        iw, ih = self.base_image.size

        self.fit_scale = min(cw / iw, ch / ih)
        scale = self.fit_scale * self.zoom

        nw = max(1, int(iw * scale))
        nh = max(1, int(ih * scale))

        self.view_image = self.base_image.resize((nw, nh), Image.LANCZOS)
        self.view_pixmap = pil_to_qpixmap(self.view_image)

        bounds = QRectF(0, 0, nw, nh)

        if self.crop_rect is not None:
            self.crop_rect = self.crop_rect.intersected(bounds)

        if getattr(self, "erase_rect", None) is not None:
            self.erase_rect = self.erase_rect.intersected(bounds)

        self._update_image_offset()

    def create_default_crop(self):
        if not self.view_image:
            return
        w, h = self.view_image.size
        m = 0.05
        self.crop_rect = QRectF(w * m, h * m, w * (1 - 2 * m), h * (1 - 2 * m))
        self.changed.emit()

    def _ensure_separator_inside(self):
        if self.view_image is None or self.separator is None:
            return
        w, h = self.view_image.size
        self.separator.cx = max(0.0, min(float(w), self.separator.cx))
        self.separator.cy = max(0.0, min(float(h), self.separator.cy))

    def get_crop_orig(self) -> Optional[Tuple[int, int, int, int]]:
        if self.crop_rect is None or self.base_image is None or self.view_image is None:
            return None
        bw, bh = self.base_image.size
        vw, vh = self.view_image.size
        sx = bw / vw
        sy = bh / vh
        x1 = max(0, min(self.crop_rect.left(), vw - 2))
        y1 = max(0, min(self.crop_rect.top(), vh - 2))
        x2 = max(x1 + 2, min(self.crop_rect.right(), vw))
        y2 = max(y1 + 2, min(self.crop_rect.bottom(), vh))
        return (int(round(x1 * sx)), int(round(y1 * sy)), int(round(x2 * sx)), int(round(y2 * sy)))

    def get_erase_orig(self) -> Optional[Tuple[int, int, int, int]]:
        if self.erase_rect is None or self.base_image is None or self.view_image is None:
            return None

        bw, bh = self.base_image.size
        vw, vh = self.view_image.size
        sx = bw / vw
        sy = bh / vh

        x1 = max(0, min(self.erase_rect.left(), vw - 2))
        y1 = max(0, min(self.erase_rect.top(), vh - 2))
        x2 = max(x1 + 2, min(self.erase_rect.right(), vw))
        y2 = max(y1 + 2, min(self.erase_rect.bottom(), vh))

        return (
            int(round(x1 * sx)),
            int(round(y1 * sy)),
            int(round(x2 * sx)),
            int(round(y2 * sy)),
        )

    def set_erase_from_orig(self, erase_orig: Optional[Tuple[int, int, int, int]]):
        if erase_orig is None or self.base_image is None or self.view_image is None:
            self.erase_rect = None
            self.update()
            return

        bw, bh = self.base_image.size
        vw, vh = self.view_image.size
        sx = vw / bw
        sy = vh / bh

        x1, y1, x2, y2 = erase_orig
        self.erase_rect = QRectF(x1 * sx, y1 * sy, (x2 - x1) * sx, (y2 - y1) * sy)
        self.update()

    def set_crop_from_orig(self, crop_orig: Optional[Tuple[int, int, int, int]]):
        if crop_orig is None or self.base_image is None or self.view_image is None:
            self.crop_rect = None
            self.update()
            return
        bw, bh = self.base_image.size
        vw, vh = self.view_image.size
        sx = vw / bw
        sy = vh / bh
        x1, y1, x2, y2 = crop_orig
        self.crop_rect = QRectF(x1 * sx, y1 * sy, (x2 - x1) * sx, (y2 - y1) * sy)
        self.update()

    def _project_to_border(self, x: float, y: float) -> Tuple[float, float]:
        if self.view_image is None:
            return x, y
        w, h = self.view_image.size
        candidates = [
            (0.0, max(0.0, min(float(h), y))),
            (float(w), max(0.0, min(float(h), y))),
            (max(0.0, min(float(w), x)), 0.0),
            (max(0.0, min(float(w), x)), float(h)),
        ]
        return min(candidates, key=lambda c: (x - c[0]) ** 2 + (y - c[1]) ** 2)

    def _mouse_angle_from_center(self, p: QPointF) -> float:
        if self.view_image is None:
            return 0.0
        w, h = self.view_image.size
        cx = w / 2.0
        cy = h / 2.0
        return math.degrees(math.atan2(p.y() - cy, p.x() - cx))

    def _update_image_offset(self):
        if self.view_pixmap is None:
            self._img_offset_x = 0.0
            self._img_offset_y = 0.0
            return
        self._img_offset_x = max(0.0, (self.width() - self.view_pixmap.width()) / 2.0)
        self._img_offset_y = max(0.0, (self.height() - self.view_pixmap.height()) / 2.0)

    def _widget_to_image(self, p: QPointF) -> QPointF:
        return QPointF(p.x() - self._img_offset_x, p.y() - self._img_offset_y)

    def _image_to_widget(self, p: QPointF) -> QPointF:
        return QPointF(p.x() + self._img_offset_x, p.y() + self._img_offset_y)

    def _image_rect_in_widget(self) -> QRectF:
        if self.view_pixmap is None:
            return QRectF()
        return QRectF(
            self._img_offset_x,
            self._img_offset_y,
            float(self.view_pixmap.width()),
            float(self.view_pixmap.height())
        )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#e9e9e9"))

        if self.view_pixmap is None:
            painter.setPen(QColor("#888"))
            tr = getattr(self.parent(), "_tr", None)
            painter.drawText(self.rect(), Qt.AlignCenter, tr("image_edit_no_image_loaded") if callable(tr) else "No image loaded")
            return

        self._update_image_offset()

        draw_x = self._img_offset_x
        draw_y = self._img_offset_y
        w = self.view_pixmap.width()
        h = self.view_pixmap.height()

        angle = self.preview_rotation_angle if self.is_preview_rotating else 0.0

        if abs(angle) > 0.01:
            painter.save()
            painter.translate(draw_x + w / 2.0, draw_y + h / 2.0)
            painter.rotate(angle)
            painter.translate(-w / 2.0, -h / 2.0)
            painter.drawPixmap(0, 0, self.view_pixmap)
            painter.restore()
        else:
            painter.drawPixmap(int(draw_x), int(draw_y), self.view_pixmap)

        painter.save()
        painter.translate(draw_x, draw_y)

        # Raster JETZT über dem Bild zeichnen
        if self.show_grid:
            self._paint_grid(painter)

        if getattr(self, "show_erase", False) and getattr(self, "erase_rect", None) is not None:
            self._paint_erase(painter)

        if self.show_crop and self.crop_rect is not None:
            self._paint_crop(painter)
        if self.show_separator and self.separator is not None:
            self._paint_separator(painter)

        painter.restore()

    def _paint_crop(self, painter: QPainter):
        rect = self.crop_rect
        if rect is None:
            return
        painter.setPen(QPen(QColor("#ff4d4d"), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(rect)
        handle_size = 10
        painter.setPen(QPen(QColor("black"), 1))
        corners = [rect.topLeft(), rect.topRight(), rect.bottomRight(), rect.bottomLeft()]
        mids = [QPointF(rect.center().x(), rect.top()), QPointF(rect.right(), rect.center().y()), QPointF(rect.center().x(), rect.bottom()), QPointF(rect.left(), rect.center().y())]
        painter.setBrush(QColor("#ff4d4d"))
        for p in corners:
            painter.drawRect(QRectF(p.x() - handle_size / 2, p.y() - handle_size / 2, handle_size, handle_size))
        painter.setBrush(QColor("#ffb347"))
        for p in mids:
            painter.drawRect(QRectF(p.x() - handle_size / 2, p.y() - handle_size / 2, handle_size, handle_size))

    def _paint_erase(self, painter: QPainter):
        rect = getattr(self, "erase_rect", None)
        if rect is None:
            return

        painter.setPen(QPen(QColor("#ff4d4d"), 2, Qt.DashLine))
        painter.setBrush(QColor(255, 90, 90, 70))

        shape = getattr(self, "erase_shape", "rect")
        if shape == "ellipse":
            painter.drawEllipse(rect)
        else:
            painter.drawRect(rect)

    def _paint_separator(self, painter: QPainter):
        if self.view_image is None or self.separator is None:
            return
        pts = self.separator.clipped_endpoints(*self.view_image.size)
        if pts is None:
            return
        x1, y1, x2, y2 = pts
        painter.setPen(QPen(QColor("#58d68d"), 3))
        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        painter.setPen(QPen(QColor("black"), 1))
        painter.setBrush(QColor("#ffc107"))
        for hx, hy in (self.separator.top_handle(*self.view_image.size), self.separator.bottom_handle(*self.view_image.size)):
            painter.drawEllipse(QPointF(hx, hy), self.separator.HANDLE_R, self.separator.HANDLE_R)
        rx, ry = self.separator.rotation_handle_pos()
        painter.setBrush(QColor("#ffffff"))
        painter.setPen(QPen(QColor("#555"), 1))
        painter.drawEllipse(QPointF(rx, ry), self.separator.ROT_R, self.separator.ROT_R)
        painter.setPen(QColor("#222"))
        painter.drawText(QRectF(rx - 12, ry - 12, 24, 24), Qt.AlignCenter, "↻")

    def _paint_grid(self, painter: QPainter):
        if self.view_image is None:
            return

        painter.save()

        pen = QPen(QColor(0, 0, 0, 90), 1)
        pen.setCosmetic(True)
        painter.setPen(pen)

        step = max(6, int(self.grid_spacing))
        w, h = self.view_image.size

        x = 0
        while x <= w:
            painter.drawLine(x, 0, x, h)
            x += step

        y = 0
        while y <= h:
            painter.drawLine(0, y, w, y)
            y += step

        painter.restore()

    def _point_in_crop(self, p: QPointF) -> bool:
        return self.crop_rect is not None and self.crop_rect.contains(p)

    def _crop_edge_at(self, p: QPointF):
        if self.crop_rect is None:
            return None
        r = self.crop_rect
        s = 8
        edges = []
        if abs(p.x() - r.left()) <= s and r.top() - s <= p.y() <= r.bottom() + s:
            edges.append("left")
        if abs(p.x() - r.right()) <= s and r.top() - s <= p.y() <= r.bottom() + s:
            edges.append("right")
        if abs(p.y() - r.top()) <= s and r.left() - s <= p.x() <= r.right() + s:
            edges.append("top")
        if abs(p.y() - r.bottom()) <= s and r.left() - s <= p.x() <= r.right() + s:
            edges.append("bottom")
        return "-".join(edges) if edges else None

    def _separator_hit(self, p: QPointF):
        if self.separator is None or self.view_image is None:
            return None
        w, h = self.view_image.size
        rx, ry = self.separator.rotation_handle_pos()
        if (p.x() - rx) ** 2 + (p.y() - ry) ** 2 <= (self.separator.ROT_R + 5) ** 2:
            return "rotate"
        tx, ty = self.separator.top_handle(w, h)
        bx, by = self.separator.bottom_handle(w, h)
        if (p.x() - tx) ** 2 + (p.y() - ty) ** 2 <= (self.separator.HANDLE_R + 4) ** 2:
            return "top"
        if (p.x() - bx) ** 2 + (p.y() - by) ** 2 <= (self.separator.HANDLE_R + 4) ** 2:
            return "bottom"
        if self.separator.distance_to_line(p.x(), p.y(), w, h) < 8:
            return "line"
        return None

    def mousePressEvent(self, event):
        if self.view_image is None:
            return
        wp = event.position()
        p = self._widget_to_image(wp)

        if not self._image_rect_in_widget().contains(wp) and not self.rotation_mode:
            return

        if self.rotation_mode:
            sep_hit = None
            if self.show_separator and self.separator is not None:
                sep_hit = self._separator_hit(p)

            crop_edge = None
            crop_hit = False
            if self.show_crop:
                crop_edge = self._crop_edge_at(p)
                crop_hit = bool(crop_edge) or self._point_in_crop(p)

            # Wenn Crop oder Trennbalken aktiv sind, zuerst Hinweis statt Rotation
            if sep_hit is not None or crop_hit or self.show_crop:
                tr = getattr(self.parent(), "_tr", None)
                QMessageBox.information(
                    self,
                    tr("image_edit_notice_title") if callable(tr) else "Notice",
                    tr("image_edit_turn_off_rotation_first") if callable(tr) else "Rotation is still active."
                )
                return

            self.drag_mode = "img_rotate"
            self.rotation_start_angle = self.rotation_angle
            self.rotation_start_mouse_angle = self._mouse_angle_from_center(p)
            self.preview_rotation_angle = 0.0
            self.is_preview_rotating = True
            self.setCursor(Qt.ClosedHandCursor)
            return
        if self.show_separator and self.separator is not None:
            hit = self._separator_hit(p)
            if hit is not None:
                self.drag_mode = {"top": "sep_top", "bottom": "sep_bottom", "line": "sep_line", "rotate": "sep_rotate"}[hit]
                if hit == "line":
                    self.sep_offset = QPointF(self.separator.cx - p.x(), self.separator.cy - p.y())
                self.drag_start = p
                self.update()
                return
        if self.show_erase:
            edge = self._rect_edge_at(self.erase_rect, p)
            if self.erase_rect is not None and edge:
                self.drag_mode = f"erase_resize:{edge}"
                self.drag_start = p
                self.rect_before = QRectF(self.erase_rect)
                return

            if self.erase_rect is not None and self.erase_rect.contains(p):
                self.drag_mode = "erase_move"
                self.drag_start = p
                self.rect_before = QRectF(self.erase_rect)
                return

            self.drag_mode = "erase_new"
            self.drag_start = p
            self.erase_rect = QRectF(p, p)
            self.update()
            self.changed.emit()
            return

        if self.show_crop:
            edge = self._crop_edge_at(p)
            if self.crop_rect is not None and edge:
                self.drag_mode = f"crop_resize:{edge}"
                self.drag_start = p
                self.rect_before = QRectF(self.crop_rect)
                return
            if self._point_in_crop(p):
                self.drag_mode = "crop_move"
                self.drag_start = p
                self.rect_before = QRectF(self.crop_rect)
                return
            self.drag_mode = "crop_new"
            self.drag_start = p
            self.crop_rect = QRectF(p, p)
            self.update()
            self.changed.emit()

    def mouseMoveEvent(self, event):
        wp = event.position()
        p = self._widget_to_image(wp)
        if self.drag_mode == "img_rotate":
            delta = self._mouse_angle_from_center(p) - self.rotation_start_mouse_angle
            new_angle = self.rotation_start_angle + delta
            if event.modifiers() & Qt.ControlModifier:
                new_angle = round(new_angle)
            self.preview_rotation_angle = new_angle - self.rotation_angle
            self.update()
            return
        if self.drag_mode == "sep_top" and self.separator and self.view_image is not None:
            fixed = self.separator.bottom_handle(*self.view_image.size)
            dragged = self._project_to_border(p.x(), p.y())
            self.separator.set_from_points(dragged, fixed)
            self.update(); self.changed.emit(); return
        if self.drag_mode == "sep_bottom" and self.separator and self.view_image is not None:
            fixed = self.separator.top_handle(*self.view_image.size)
            dragged = self._project_to_border(p.x(), p.y())
            self.separator.set_from_points(fixed, dragged)
            self.update(); self.changed.emit(); return
        if self.drag_mode == "sep_line" and self.separator and self.view_image is not None:
            new_x = p.x() + self.sep_offset.x(); new_y = p.y() + self.sep_offset.y()
            self.separator.move_by(new_x - self.separator.cx, new_y - self.separator.cy, *self.view_image.size)
            self.update(); self.changed.emit(); return
        if self.drag_mode == "sep_rotate" and self.separator:
            dx = p.x() - self.separator.cx; dy = p.y() - self.separator.cy
            if abs(dx) > 1e-6 or abs(dy) > 1e-6:
                raw = math.atan2(dy, dx) - math.pi / 2
                if event.modifiers() & Qt.ControlModifier:
                    step = math.radians(5)
                    raw = round(raw / step) * step
                self.separator.angle = raw
                self.update(); self.changed.emit(); return
        if self.drag_mode == "erase_move" and self.erase_rect and self.rect_before:
            r = QRectF(self.rect_before)
            r.translate(p - self.drag_start)
            self.erase_rect = self._clamp_rect(r)
            self.update()
            self.changed.emit()
            return

        if self.drag_mode and str(self.drag_mode).startswith("erase_resize:") and self.rect_before:
            edge = self.drag_mode.split(":", 1)[1]
            r = QRectF(self.rect_before)

            if "left" in edge:
                r.setLeft(min(p.x(), r.right() - 5))
            if "right" in edge:
                r.setRight(max(p.x(), r.left() + 5))
            if "top" in edge:
                r.setTop(min(p.y(), r.bottom() - 5))
            if "bottom" in edge:
                r.setBottom(max(p.y(), r.top() + 5))

            self.erase_rect = self._clamp_rect(r)
            self.update()
            self.changed.emit()
            return

        if self.drag_mode == "erase_new":
            x1 = min(self.drag_start.x(), p.x())
            y1 = min(self.drag_start.y(), p.y())
            x2 = max(self.drag_start.x(), p.x())
            y2 = max(self.drag_start.y(), p.y())
            self.erase_rect = self._clamp_rect(QRectF(x1, y1, x2 - x1, y2 - y1))
            self.update()
            self.changed.emit()
            return

        if self.drag_mode == "crop_move" and self.crop_rect and self.rect_before:
            r = QRectF(self.rect_before);
            r.translate(p - self.drag_start)
            self.crop_rect = self._clamp_rect(r)
            self.update();
            self.changed.emit();
            return

        if self.drag_mode and str(self.drag_mode).startswith("crop_resize:") and self.rect_before:
            edge = self.drag_mode.split(":", 1)[1]
            r = QRectF(self.rect_before)
            if "left" in edge: r.setLeft(min(p.x(), r.right() - 5))
            if "right" in edge: r.setRight(max(p.x(), r.left() + 5))
            if "top" in edge: r.setTop(min(p.y(), r.bottom() - 5))
            if "bottom" in edge: r.setBottom(max(p.y(), r.top() + 5))
            self.crop_rect = self._clamp_rect(r)
            self.update();
            self.changed.emit();
            return

        if self.drag_mode == "crop_new":
            x1 = min(self.drag_start.x(), p.x());
            y1 = min(self.drag_start.y(), p.y())
            x2 = max(self.drag_start.x(), p.x());
            y2 = max(self.drag_start.y(), p.y())
            self.crop_rect = self._clamp_rect(QRectF(x1, y1, x2 - x1, y2 - y1))
            self.update();
            self.changed.emit();
            return
        self._update_cursor(p)

    def mouseReleaseEvent(self, event):
        if self.drag_mode == "img_rotate":
            self.rotation_angle = (self.rotation_angle + self.preview_rotation_angle) % 360.0
            self.preview_rotation_angle = 0.0
            self.is_preview_rotating = False
            self.rotation_committed.emit(float(self.rotation_angle))

        self.drag_mode = None
        self.rect_before = None
        self.sep_offset = QPointF()

        wp = event.position()
        self._update_cursor(self._widget_to_image(wp))

        self.update()
        self.changed.emit()

    def wheelEvent(self, event):
        if self.base_image is None:
            return

        old_crop = self.get_crop_orig()
        old_erase = self.get_erase_orig() if self.show_erase else None

        self.zoom = max(0.2, min(6.0, self.zoom * (1.1 if event.angleDelta().y() > 0 else 0.9)))
        self._update_view_image()
        self.set_crop_from_orig(old_crop)

        if old_erase:
            self.set_erase_from_orig(old_erase)

        self._ensure_separator_inside()
        self.update()
        self.changed.emit()

    def resizeEvent(self, event):
        old_crop = self.get_crop_orig()
        old_erase = self.get_erase_orig() if self.show_erase else None

        self._update_view_image()
        self.set_crop_from_orig(old_crop)

        if old_erase:
            self.set_erase_from_orig(old_erase)

        self._ensure_separator_inside()
        self._update_image_offset()
        self.update()
        super().resizeEvent(event)

    def _clamp_rect(self, rect: QRectF) -> QRectF:
        if self.view_image is None:
            return rect
        w, h = self.view_image.size
        x1 = max(0, min(rect.left(), w - 5)); y1 = max(0, min(rect.top(), h - 5))
        x2 = max(x1 + 5, min(rect.right(), w)); y2 = max(y1 + 5, min(rect.bottom(), h))
        return QRectF(x1, y1, x2 - x1, y2 - y1)

    def _update_cursor(self, p: QPointF):
        if self.rotation_mode:
            self.setCursor(Qt.OpenHandCursor)
            return

        if self.show_separator and self.separator is not None:
            hit = self._separator_hit(p)
            if hit in ("rotate", "top", "bottom", "line"):
                self.setCursor(Qt.SizeAllCursor)
                return

        if self.show_erase and self.erase_rect is not None:
            edge = self._rect_edge_at(self.erase_rect, p)
            if edge:
                self.setCursor(
                    Qt.SizeHorCursor if edge in ("left", "right")
                    else Qt.SizeVerCursor if edge in ("top", "bottom")
                    else Qt.SizeFDiagCursor
                )
                return
            if self.erase_rect.contains(p):
                self.setCursor(Qt.SizeAllCursor)
                return

        if self.show_crop:
            edge = self._crop_edge_at(p)
            if edge:
                self.setCursor(
                    Qt.SizeHorCursor if edge in ("left", "right")
                    else Qt.SizeVerCursor if edge in ("top", "bottom")
                    else Qt.SizeFDiagCursor
                )
                return
            if self._point_in_crop(p):
                self.setCursor(Qt.SizeAllCursor)
                return

        self.setCursor(Qt.CrossCursor)

    def _rect_edge_at(self, rect: Optional[QRectF], p: QPointF) -> Optional[str]:
        if rect is None:
            return None

        pad = 8.0
        x = p.x()
        y = p.y()

        left = abs(x - rect.left()) <= pad
        right = abs(x - rect.right()) <= pad
        top = abs(y - rect.top()) <= pad
        bottom = abs(y - rect.bottom()) <= pad

        if left and top:
            return "left_top"
        if right and top:
            return "right_top"
        if left and bottom:
            return "left_bottom"
        if right and bottom:
            return "right_bottom"
        if left:
            return "left"
        if right:
            return "right"
        if top:
            return "top"
        if bottom:
            return "bottom"

        return None

def polygon_area(poly: List[Tuple[float, float]]) -> float:
    if not poly or len(poly) < 3:
        return 0.0

    area = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        area += (x1 * y2) - (x2 * y1)

    return abs(area) * 0.5

def clip_polygon_halfplane(
        poly: List[Tuple[float, float]],
        a: float,
        b: float,
        c: float
) -> List[Tuple[float, float]]:
    """
    Behält den Teil des Polygons, für den gilt:
        a*x + b*y + c >= 0
    """
    if not poly:
        return []

    def inside(p: Tuple[float, float]) -> bool:
        x, y = p
        return (a * x + b * y + c) >= 0.0

    def intersection(
            p1: Tuple[float, float],
            p2: Tuple[float, float]
    ) -> Tuple[float, float]:
        x1, y1 = p1
        x2, y2 = p2

        dx = x2 - x1
        dy = y2 - y1

        denom = a * dx + b * dy
        if abs(denom) < 1e-12:
            return p2

        t = -(a * x1 + b * y1 + c) / denom
        return (x1 + t * dx, y1 + t * dy)

    output = []
    prev = poly[-1]
    prev_inside = inside(prev)

    for curr in poly:
        curr_inside = inside(curr)

        if curr_inside:
            if not prev_inside:
                output.append(intersection(prev, curr))
            output.append(curr)
        elif prev_inside:
            output.append(intersection(prev, curr))

        prev = curr
        prev_inside = curr_inside

    return output

class ImageEditDialog(QDialog):
    def __init__(
            self,
            image: Image.Image,
            title: str,
            parent=None,
            on_prev=None,
            on_next=None,
            on_apply_current=None,
            on_apply_selected=None,
            on_apply_all=None,
    ):
        super().__init__(parent)
        self.on_prev = on_prev
        self.on_next = on_next
        self.on_apply_current = on_apply_current
        self.on_apply_selected = on_apply_selected
        self.on_apply_all = on_apply_all
        self.white_border_px = 0
        tr = getattr(parent, "_tr", None)
        self._tr = tr if callable(tr) else (lambda key, *args: (TRANSLATIONS["de"].get(key, key).format(*args) if args else TRANSLATIONS["de"].get(key, key)))

        self.setWindowTitle(self._tr("image_edit_title", title))
        self.resize(1360, 900)

        theme = getattr(parent, "current_theme", "bright")
        self.setStyleSheet(_image_edit_dialog_qss(theme))

        self.original_image = image.convert("RGB")
        self.color_mode = "RGB"
        self.contrast_enabled = False
        self.rotation_angle = 0.0
        self.result_images: List[Image.Image] = []
        self._batch_apply_used = False
        self.erase_actions: List[Tuple[str, Tuple[int, int, int, int]]] = []

        self.canvas = ImageEditCanvas(self)
        self.canvas.setFocusPolicy(Qt.StrongFocus)
        self.canvas.changed.connect(self._sync_from_canvas)
        self.canvas.rotation_committed.connect(self._on_canvas_rotation_committed)

        self.shortcut_prev_left = QShortcut(QKeySequence(Qt.Key_Left), self)
        self.shortcut_prev_left.setContext(Qt.WidgetWithChildrenShortcut)
        self.shortcut_prev_left.activated.connect(self._go_prev)

        self.shortcut_prev_up = QShortcut(QKeySequence(Qt.Key_Up), self)
        self.shortcut_prev_up.setContext(Qt.WidgetWithChildrenShortcut)
        self.shortcut_prev_up.activated.connect(self._go_prev)

        self.shortcut_next_right = QShortcut(QKeySequence(Qt.Key_Right), self)
        self.shortcut_next_right.setContext(Qt.WidgetWithChildrenShortcut)
        self.shortcut_next_right.activated.connect(self._go_next)

        self.shortcut_next_down = QShortcut(QKeySequence(Qt.Key_Down), self)
        self.shortcut_next_down.setContext(Qt.WidgetWithChildrenShortcut)
        self.shortcut_next_down.activated.connect(self._go_next)

        self.shortcut_erase_commit = QShortcut(QKeySequence(Qt.Key_Delete), self)
        self.shortcut_erase_commit.setContext(Qt.WidgetWithChildrenShortcut)
        self.shortcut_erase_commit.activated.connect(self._commit_erase_selection)

        self.shortcut_erase_undo = QShortcut(QKeySequence.Undo, self)
        self.shortcut_erase_undo.setContext(Qt.WidgetWithChildrenShortcut)
        self.shortcut_erase_undo.activated.connect(self._undo_erase_commit)

        self.btn_rotate_mode = QPushButton(self._tr("image_edit_rotate_off"))
        self.btn_rotate_mode.setCheckable(True)
        self.btn_rotate_mode.toggled.connect(self._toggle_rotation_mode)

        self.btn_grid = QPushButton(self._tr("image_edit_grid"))
        self.btn_grid.setCheckable(True)
        self.btn_grid.toggled.connect(self._toggle_grid)

        self.grid_slider = QSlider(Qt.Horizontal)
        self.grid_slider.setRange(0, 100)
        self.grid_slider.setValue(20)
        self.grid_slider.setToolTip(self._tr("image_edit_grid_tooltip"))
        self.grid_slider.valueChanged.connect(self._on_grid_slider_changed)
        self.grid_slider.setMinimumWidth(260)
        self.grid_slider.setMaximumWidth(420)
        self.grid_slider.setFixedHeight(22)
        self.grid_slider.setEnabled(False)

        self.lbl_grid_size = QLabel(self._tr("image_edit_grid_label"))
        self.lbl_grid_size.setMinimumWidth(120)
        self.lbl_grid_size.setEnabled(False)

        self.chk_crop = QCheckBox(self._tr("image_edit_crop"))
        self.chk_crop.toggled.connect(self._toggle_crop)

        self.chk_split = QCheckBox(self._tr("image_edit_separator"))
        self.chk_split.toggled.connect(self._toggle_split)

        self.chk_gray = QCheckBox(self._tr("image_edit_gray"))
        self.chk_gray.toggled.connect(self._toggle_gray)

        self.chk_contrast = QCheckBox(self._tr("image_edit_contrast"))
        self.chk_contrast.toggled.connect(self._toggle_contrast)

        self.btn_erase_rect = QPushButton(self._tr("image_edit_erase_rect"))
        self.btn_erase_rect.setCheckable(True)
        self.btn_erase_rect.toggled.connect(
            lambda checked: self._toggle_erase_mode("rect", checked)
        )

        self.btn_erase_ellipse = QPushButton(self._tr("image_edit_erase_ellipse"))
        self.btn_erase_ellipse.setCheckable(True)
        self.btn_erase_ellipse.toggled.connect(
            lambda checked: self._toggle_erase_mode("ellipse", checked)
        )

        self.btn_erase_clear = QPushButton(self._tr("image_edit_erase_clear"))
        self.btn_erase_clear.clicked.connect(self._clear_erase_area)

        btn_rot_left = QPushButton("↺ 90°")
        btn_rot_left.clicked.connect(lambda: self._rotate_by(-90))

        btn_rot_right = QPushButton("↻ 90°")
        btn_rot_right.clicked.connect(lambda: self._rotate_by(90))

        btn_rot_reset = QPushButton(self._tr("image_edit_rotation_reset"))
        btn_rot_reset.clicked.connect(self._reset_rotation)

        self.chk_smart_split = QCheckBox(self._tr("image_edit_smart_split"))
        self.chk_smart_split.toggled.connect(self._toggle_smart_split)
        self.chk_smart_split.setEnabled(False)

        self.btn_prev = QPushButton(self._tr("image_edit_prev"))
        self.btn_prev.clicked.connect(self._go_prev)

        self.btn_next = QPushButton(self._tr("image_edit_next"))
        self.btn_next.clicked.connect(self._go_next)

        self.btn_border = QPushButton(self._tr("image_edit_white_border"))
        self.btn_border.clicked.connect(self._open_border_dialog)

        self.btn_apply_selected = QPushButton(self._tr("image_edit_apply_selected"))
        self.btn_apply_selected.clicked.connect(self._apply_selected)

        self.btn_apply_all = QPushButton(self._tr("image_edit_apply_all"))
        self.btn_apply_all.clicked.connect(self._apply_all)

        top = QHBoxLayout()
        for widget in (self.btn_grid, self.btn_rotate_mode, btn_rot_left, btn_rot_right, btn_rot_reset):
            top.addWidget(widget)

        top.addSpacing(16)

        for widget in (
                self.chk_crop,
                self.chk_split,
                self.chk_smart_split,
                self.chk_gray,
                self.chk_contrast,
        ):
            top.addWidget(widget)

        top.addStretch(1)
        top.addWidget(self.btn_border, 0, Qt.AlignRight)

        lay = QVBoxLayout(self)
        lay.addLayout(top)

        center = QVBoxLayout()
        center.addWidget(self.canvas, 1)

        grid_row = QHBoxLayout()
        grid_row.addStretch(1)
        grid_row.addWidget(self.lbl_grid_size)
        grid_row.addWidget(self.grid_slider, 0)
        grid_row.addStretch(1)

        erase_row = QHBoxLayout()
        erase_row.addStretch(1)
        erase_row.addWidget(self.btn_erase_rect)
        erase_row.addSpacing(8)
        erase_row.addWidget(self.btn_erase_ellipse)
        erase_row.addSpacing(8)
        erase_row.addWidget(self.btn_erase_clear)
        erase_row.addStretch(1)

        center.addLayout(grid_row)
        center.addLayout(erase_row)
        lay.addLayout(center, 1)

        bottom = QHBoxLayout()
        bottom.addWidget(self.btn_prev)
        bottom.addWidget(self.btn_next)
        bottom.addStretch(1)
        bottom.addWidget(self.btn_apply_selected)
        bottom.addWidget(self.btn_apply_all)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText(self._tr("dlg_box_apply"))
        bb.button(QDialogButtonBox.Cancel).setText(self._tr("btn_cancel"))
        bb.accepted.connect(self._accept_dialog)
        bb.rejected.connect(self.reject)

        lay.addLayout(bottom)
        lay.addWidget(bb)

        self._refresh_preview(reset_zoom=True)
        self.canvas.setFocus()

    def _apply_options(self, img: Image.Image) -> Image.Image:
        out = img.convert("RGB")

        if self.color_mode == "GRAY":
            out = ImageOps.grayscale(out).convert("RGB")

        if self.contrast_enabled:
            out = ImageOps.autocontrast(out, cutoff=1)
            out = ImageEnhance.Contrast(out).enhance(2.2)
            out = ImageEnhance.Sharpness(out).enhance(1.4)

        if abs(self.rotation_angle) > 0.01:
            out = out.rotate(
                -self.rotation_angle,
                expand=True,
                resample=Image.BICUBIC,
                fillcolor="white"
            )

        if self.white_border_px > 0:
            out = ImageOps.expand(out, border=int(self.white_border_px), fill="white")

        draw = ImageDraw.Draw(out)

        for shape, bbox in self.erase_actions:
            x1, y1, x2, y2 = bbox
            if shape == "ellipse":
                draw.ellipse((x1, y1, x2, y2), fill="white")
            else:
                draw.rectangle((x1, y1, x2, y2), fill="white")

        live_action = self._current_erase_action()
        if live_action:
            shape, bbox = live_action
            x1, y1, x2, y2 = bbox
            if shape == "ellipse":
                draw.ellipse((x1, y1, x2, y2), fill="white")
            else:
                draw.rectangle((x1, y1, x2, y2), fill="white")

        return out

    def _refresh_preview(self, reset_zoom: bool = False):
        old_crop = self.canvas.get_crop_orig()
        old_erase = self.canvas.get_erase_orig() if self.canvas.show_erase else None

        preview = self._apply_options(self.original_image)
        self.canvas.rotation_angle = self.rotation_angle
        self.canvas.set_image(preview, reset_zoom=reset_zoom)

        if self.chk_crop.isChecked() and old_crop:
            self.canvas.set_crop_from_orig(old_crop)
        elif self.chk_crop.isChecked() and self.canvas.crop_rect is None:
            self.canvas.create_default_crop()

        if self.canvas.show_erase and old_erase:
            self.canvas.set_erase_from_orig(old_erase)

        if self.chk_split.isChecked() and self.canvas.separator is None and self.canvas.view_image is not None:
            w, h = self.canvas.view_image.size
            self.canvas.separator = ImageEditSeparator(cx=w / 2.0, cy=h / 2.0, angle=0.0)

        self.canvas.update()
        self._update_border_button_text()

    def _sync_from_canvas(self):
        self.rotation_angle = float(self.canvas.rotation_angle)

    def _on_canvas_rotation_committed(self, angle: float):
        self.rotation_angle = float(angle) % 360.0
        self.canvas.rotation_angle = 0.0
        self.canvas.preview_rotation_angle = 0.0
        self.canvas.is_preview_rotating = False

        self.canvas.crop_rect = None
        self.canvas.separator = None

        self._refresh_preview(reset_zoom=False)

    def _toggle_smart_split(self, checked: bool):
        # Smart-Splitting nur erlaubt, wenn Trennbalken aktiv ist
        if checked and not self.chk_split.isChecked():
            self.chk_smart_split.blockSignals(True)
            self.chk_smart_split.setChecked(False)
            self.chk_smart_split.blockSignals(False)
            return

        self.canvas.update()

    def _go_prev(self):
        if callable(self.on_prev):
            self.on_prev(self)

    def _go_next(self):
        if callable(self.on_next):
            self.on_next(self)

    def _current_erase_action(self) -> Optional[Tuple[str, Tuple[int, int, int, int]]]:
        if not self.canvas.show_erase:
            return None

        erase_orig = self.canvas.get_erase_orig()
        if not erase_orig:
            return None

        shape = self.canvas.erase_shape or "rect"
        return shape, erase_orig

    def _commit_erase_selection(self):
        action = self._current_erase_action()
        if action is None:
            return

        shape, bbox = action
        self.erase_actions.append((shape, tuple(bbox)))

        self.canvas.erase_rect = None
        self._refresh_preview(reset_zoom=False)
        self.canvas.setFocus()

    def _undo_erase_commit(self):
        if not self.erase_actions:
            return

        self.erase_actions.pop()
        self.canvas.erase_rect = None
        self._refresh_preview(reset_zoom=False)
        self.canvas.setFocus()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Left, Qt.Key_Up):
            self._go_prev()
            event.accept()
            return

        if event.key() in (Qt.Key_Right, Qt.Key_Down):
            self._go_next()
            event.accept()
            return

        super().keyPressEvent(event)

    def _apply_selected(self):
        if callable(self.on_apply_selected):
            self._batch_apply_used = True
            self.result_images = []
            self.on_apply_selected(self)
            self.accept()

    def _apply_all(self):
        if callable(self.on_apply_all):
            self._batch_apply_used = True
            self.result_images = []
            self.on_apply_all(self)
            self.accept()

    def _update_border_button_text(self):
        if self.white_border_px > 0:
            self.btn_border.setText(self._tr("image_edit_white_border_with_px", self.white_border_px))
        else:
            self.btn_border.setText(self._tr("image_edit_white_border"))

    def _open_border_dialog(self):
        dlg = WhiteBorderDialog(self.white_border_px, self)
        if dlg.exec() == QDialog.Accepted:
            self.white_border_px = dlg.get_value()
            self._update_border_button_text()
            self._refresh_preview(reset_zoom=False)

    def _toggle_rotation_mode(self, checked: bool):
        self.canvas.rotation_mode = checked
        self.btn_rotate_mode.setText(self._tr("image_edit_rotate_on") if checked else self._tr("image_edit_rotate_off"))
        self.canvas.update()

    def _toggle_grid(self, checked: bool):
        self.canvas.show_grid = checked
        self.grid_slider.setEnabled(bool(checked))
        self.lbl_grid_size.setEnabled(bool(checked))
        self.canvas.update()

    def _on_grid_slider_changed(self, value: int):
        # oben fein = kleine Abstände
        # unten grob = große Abstände
        self.canvas.grid_spacing = int(round(6 + (value / 100.0) * 90))
        self.canvas.update()

    def _toggle_crop(self, checked: bool):
        self.canvas.show_crop = checked
        if checked and self.canvas.crop_rect is None and self.canvas.view_image is not None:
            self.canvas.create_default_crop()
        self.canvas.update()

    def _toggle_split(self, checked: bool):
        self.canvas.show_separator = checked
        self.chk_smart_split.setEnabled(checked)

        if checked and self.canvas.separator is None and self.canvas.view_image is not None:
            w, h = self.canvas.view_image.size
            self.canvas.separator = ImageEditSeparator(cx=w / 2.0, cy=h / 2.0, angle=0.0)

        if not checked:
            self.canvas.separator = None

            # Wenn Trennbalken aus ist, muss Smart-Splitting auch aus sein
            if self.chk_smart_split.isChecked():
                self.chk_smart_split.blockSignals(True)
                self.chk_smart_split.setChecked(False)
                self.chk_smart_split.blockSignals(False)

        self.canvas.update()

    def _toggle_erase_mode(self, shape: str, checked: bool):
        if checked:
            if shape == "rect" and self.btn_erase_ellipse.isChecked():
                self.btn_erase_ellipse.blockSignals(True)
                self.btn_erase_ellipse.setChecked(False)
                self.btn_erase_ellipse.blockSignals(False)

            if shape == "ellipse" and self.btn_erase_rect.isChecked():
                self.btn_erase_rect.blockSignals(True)
                self.btn_erase_rect.setChecked(False)
                self.btn_erase_rect.blockSignals(False)

            self.canvas.show_erase = True
            self.canvas.erase_shape = shape

            if self.canvas.erase_rect is None and self.canvas.view_image is not None:
                w, h = self.canvas.view_image.size
                self.canvas.erase_rect = QRectF(w * 0.35, h * 0.20, w * 0.25, h * 0.25)
        else:
            if not self.btn_erase_rect.isChecked() and not self.btn_erase_ellipse.isChecked():
                self.canvas.show_erase = False
                self.canvas.erase_shape = ""

        self.canvas.update()
        self.canvas.changed.emit()

    def _clear_erase_area(self):
        self.canvas.erase_rect = None
        self.canvas.show_erase = False
        self.canvas.erase_shape = ""

        self.btn_erase_rect.blockSignals(True)
        self.btn_erase_rect.setChecked(False)
        self.btn_erase_rect.blockSignals(False)

        self.btn_erase_ellipse.blockSignals(True)
        self.btn_erase_ellipse.setChecked(False)
        self.btn_erase_ellipse.blockSignals(False)

        self.canvas.update()
        self.canvas.changed.emit()

    def _toggle_gray(self, checked: bool):
        self.color_mode = "GRAY" if checked else "RGB"
        self._refresh_preview(reset_zoom=False)

    def _toggle_contrast(self, checked: bool):
        self.contrast_enabled = bool(checked)
        self._refresh_preview(reset_zoom=False)

    def _rotate_by(self, delta: float):
        self.rotation_angle = (self.rotation_angle + delta) % 360.0
        self.canvas.crop_rect = None
        self.canvas.separator = None
        self._refresh_preview(reset_zoom=False)

    def _reset_rotation(self):
        self.rotation_angle = 0.0
        self.canvas.crop_rect = None
        self.canvas.separator = None
        self._refresh_preview(reset_zoom=False)

    def _get_effective_crop_area(self, img: Image.Image) -> Tuple[int, int, int, int]:
        if self.chk_crop.isChecked():
            crop = self.canvas.get_crop_orig()
            if crop is not None:
                return crop
        return (0, 0, img.size[0], img.size[1])

    def _separator_lines_for_processing(self, img: Image.Image):
        if not self.chk_split.isChecked() or self.canvas.separator is None or self.canvas.view_image is None:
            return []
        vw, vh = self.canvas.view_image.size
        bw, bh = img.size
        sx = bw / max(1, vw)
        sy = bh / max(1, vh)
        pts = self.canvas.separator.clipped_endpoints(vw, vh)
        if pts is None:
            return []
        x1d, y1d, x2d, y2d = pts
        return [(x1d * sx, y1d * sy, x2d * sx, y2d * sy)]

    def _compute_segments_for_crop(self, crop_area, line_segments_orig):
        ox1, oy1, ox2, oy2 = crop_area
        rect_poly = [(ox1, oy1), (ox2, oy1), (ox2, oy2), (ox1, oy2)]
        if not line_segments_orig:
            return [rect_poly]
        entries = []
        for x1, y1, x2, y2 in line_segments_orig:
            vx = x2 - x1; vy = y2 - y1
            nx = -vy; ny = vx
            norm = math.hypot(nx, ny)
            if norm < 1e-12:
                continue
            nx /= norm; ny /= norm
            c = -(nx * x1 + ny * y1); d = -c
            entries.append((d, nx, ny, c))
        entries.sort(key=lambda e: e[0])
        if not entries:
            return [rect_poly]
        segments = []
        for i in range(len(entries) + 1):
            poly = rect_poly[:]
            if i == 0:
                a, b, c = entries[0][1], entries[0][2], entries[0][3]
                poly = clip_polygon_halfplane(poly, -a, -b, -c)
            elif i == len(entries):
                a, b, c = entries[-1][1], entries[-1][2], entries[-1][3]
                poly = clip_polygon_halfplane(poly, a, b, c)
            else:
                a1, b1, c1 = entries[i - 1][1], entries[i - 1][2], entries[i - 1][3]
                a2, b2, c2 = entries[i][1], entries[i][2], entries[i][3]
                poly = clip_polygon_halfplane(poly, a1, b1, c1)
                poly = clip_polygon_halfplane(poly, -a2, -b2, -c2)
            if polygon_area(poly) > 1.0:
                segments.append(poly)
        return segments

    def _build_segment_images(self, img: Image.Image, crop_area, segments_polygons):
        ox1, oy1, ox2, oy2 = crop_area
        crop = img.crop((ox1, oy1, ox2, oy2))
        if not segments_polygons:
            return [crop]
        ordered_polys = sorted(segments_polygons, key=lambda poly: sum(x for x, _ in poly) / len(poly))
        out = []
        for poly in ordered_polys:
            if not poly or polygon_area(poly) < 1.0:
                continue
            local = [(x - ox1, y - oy1) for (x, y) in poly]
            full_rgba = Image.new("RGBA", crop.size, (255, 255, 255, 0))
            mask = Image.new("L", crop.size, 0)
            ImageDraw.Draw(mask).polygon(local, fill=255)
            full_rgba.paste(crop.convert("RGBA"), (0, 0), mask)
            min_x = max(0, int(math.floor(min(x for x, _ in local))))
            min_y = max(0, int(math.floor(min(y for _, y in local))))
            max_x = min(crop.size[0], int(math.ceil(max(x for x, _ in local))))
            max_y = min(crop.size[1], int(math.ceil(max(y for _, y in local))))
            if max_x - min_x < 2 or max_y - min_y < 2:
                continue
            segment_img = full_rgba.crop((min_x, min_y, max_x, max_y))
            bg = Image.new("RGB", segment_img.size, (255, 255, 255))
            bg.paste(segment_img, (0, 0), segment_img.split()[-1])
            out.append(bg)
        return out or [crop]

    def _auto_detect_smart_splits(self, img: Image.Image, crop_area, guide_line_orig=None):
        # Smart-Splitting funktioniert nur mit aktivem Trennbalken
        if not guide_line_orig:
            return []

        ox1, oy1, ox2, oy2 = crop_area
        crop = img.crop((ox1, oy1, ox2, oy2)).convert("L")
        w, h = crop.size

        if w < 20 or h < 20:
            return []

        x1, y1, x2, y2 = guide_line_orig[0]
        px = crop.load()

        def expected_x(global_y):
            if abs(y2 - y1) < 1e-6:
                return (x1 + x2) * 0.5
            t = (global_y - y1) / (y2 - y1)
            return x1 + t * (x2 - x1)

        band = max(2, min(6, w // 120))
        search_radius = max(20, min(120, w // 8))
        y_step = max(6, h // 80)

        samples = []

        for local_y in range(6, h - 6, y_step):
            global_y = oy1 + local_y
            ex = int(round(expected_x(global_y) - ox1))

            xmin = max(6, ex - search_radius)
            xmax = min(w - 7, ex + search_radius)
            if xmin >= xmax:
                continue

            best_x = None
            best_score = None

            for x in range(xmin, xmax + 1):
                center_vals = []
                left_vals = []
                right_vals = []

                for yy in range(local_y - 2, local_y + 3):
                    for xx in range(x - band, x + band + 1):
                        center_vals.append(px[xx, yy])

                    for xx in range(max(0, x - 14), max(0, x - 4)):
                        left_vals.append(px[xx, yy])

                    for xx in range(min(w - 1, x + 4), min(w, x + 15)):
                        right_vals.append(px[xx, yy])

                if not center_vals or not left_vals or not right_vals:
                    continue

                center_mean = sum(center_vals) / len(center_vals)
                left_mean = sum(left_vals) / len(left_vals)
                right_mean = sum(right_vals) / len(right_vals)

                contrast = ((left_mean + right_mean) * 0.5) - center_mean
                distance_penalty = abs(x - ex) * 0.15

                score = center_mean - contrast * 1.8 + distance_penalty
                if best_score is None or score < best_score:
                    best_score = score
                    best_x = x

            if best_x is not None:
                samples.append((local_y, best_x))

        if len(samples) < 2:
            return guide_line_orig

        smoothed = []
        for i in range(len(samples)):
            xs = []
            for j in range(max(0, i - 2), min(len(samples), i + 3)):
                xs.append(samples[j][1])
            smoothed.append((samples[i][0], sum(xs) / len(xs)))

        n = len(smoothed)
        sum_y = sum(y for y, _ in smoothed)
        sum_x = sum(x for _, x in smoothed)
        sum_yy = sum(y * y for y, _ in smoothed)
        sum_yx = sum(y * x for y, x in smoothed)

        denom = n * sum_yy - sum_y * sum_y
        if abs(denom) < 1e-9:
            return guide_line_orig

        m = (n * sum_yx - sum_y * sum_x) / denom
        b = (sum_x - m * sum_y) / n

        x_top_local = b
        x_bottom_local = m * (h - 1) + b

        x_top = max(0, min(img.size[0], ox1 + x_top_local))
        x_bottom = max(0, min(img.size[0], ox1 + x_bottom_local))

        return [(
            x_top,
            oy1,
            x_bottom,
            oy2
        )]

    def _accept_dialog(self):
        edited = self._apply_options(self.original_image)
        crop_area = self._get_effective_crop_area(edited)

        lines = self._separator_lines_for_processing(edited)

        if self.chk_split.isChecked() and lines:
            effective_lines = lines

            if self.chk_smart_split.isChecked():
                effective_lines = self._auto_detect_smart_splits(
                    edited,
                    crop_area,
                    guide_line_orig=lines
                ) or lines

            polys = self._compute_segments_for_crop(crop_area, effective_lines)
            self.result_images = self._build_segment_images(edited, crop_area, polys)

        else:
            ox1, oy1, ox2, oy2 = crop_area
            self.result_images = [edited.crop((ox1, oy1, ox2, oy2))]

        self.accept()

    def get_settings(self) -> ImageEditSettings:
        crop_orig = self.canvas.get_crop_orig() if self.chk_crop.isChecked() else None

        separator_norm = None
        if self.chk_split.isChecked() and self.canvas.separator and self.canvas.view_image is not None:
            w, h = self.canvas.view_image.size
            separator_norm = (
                self.canvas.separator.cx / max(1.0, float(w)),
                self.canvas.separator.cy / max(1.0, float(h)),
                float(self.canvas.separator.angle),
            )

        erase_enabled = bool(self.canvas.show_erase and self.canvas.erase_rect is not None)
        erase_shape = self.canvas.erase_shape if erase_enabled else ""
        erase_orig = self.canvas.get_erase_orig() if erase_enabled else None

        return ImageEditSettings(
            rotation_angle=float(self.rotation_angle),
            color_mode=str(self.color_mode),
            contrast_enabled=bool(self.contrast_enabled),
            crop_enabled=bool(self.chk_crop.isChecked()),
            crop_orig=crop_orig,
            split_enabled=bool(self.chk_split.isChecked()),
            separator_norm=separator_norm,
            smart_split_enabled=bool(self.chk_smart_split.isChecked()),
            white_border_px=int(self.white_border_px),
            erase_enabled=erase_enabled,
            erase_shape=erase_shape,
            erase_orig=erase_orig,
            erase_actions=[(shape, tuple(bbox)) for shape, bbox in self.erase_actions],
        )

    def set_settings(self, settings: ImageEditSettings):
        self.rotation_angle = float(settings.rotation_angle)
        self.color_mode = settings.color_mode
        self.contrast_enabled = bool(settings.contrast_enabled)
        self.white_border_px = int(settings.white_border_px)
        self.erase_actions = [(shape, tuple(bbox)) for shape, bbox in (settings.erase_actions or [])]

        self.chk_gray.setChecked(self.color_mode == "GRAY")
        self.chk_contrast.setChecked(self.contrast_enabled)
        self.chk_crop.setChecked(bool(settings.crop_enabled))

        self.chk_erase_rect.blockSignals(True)
        self.chk_erase_ellipse.blockSignals(True)
        self.chk_erase_rect.setChecked(
            bool(settings.erase_enabled and settings.erase_shape == "rect")
        )
        self.chk_erase_ellipse.setChecked(
            bool(settings.erase_enabled and settings.erase_shape == "ellipse")
        )
        self.chk_erase_rect.blockSignals(False)
        self.chk_erase_ellipse.blockSignals(False)

        self.canvas.show_erase = bool(settings.erase_enabled)
        self.canvas.erase_shape = settings.erase_shape if settings.erase_enabled else ""
        self.canvas.erase_rect = None

        self.chk_split.setChecked(bool(settings.split_enabled))
        self.chk_smart_split.setEnabled(bool(settings.split_enabled))

        self.chk_smart_split.setChecked(
            bool(settings.smart_split_enabled) and bool(settings.split_enabled)
        )

        self._refresh_preview(reset_zoom=False)

        if settings.erase_enabled and settings.erase_orig:
            self.canvas.set_erase_from_orig(settings.erase_orig)

        if settings.crop_enabled and settings.crop_orig:
            self.canvas.set_crop_from_orig(settings.crop_orig)

        if (
                settings.split_enabled
                and settings.separator_norm
                and self.canvas.view_image is not None
        ):
            w, h = self.canvas.view_image.size
            cxn, cyn, ang = settings.separator_norm
            self.canvas.separator = ImageEditSeparator(
                cx=float(cxn) * w,
                cy=float(cyn) * h,
                angle=float(ang),
            )
            self.canvas.show_separator = True
            self.canvas.update()

# -----------------------------
# HAUPTFENSTER
# -----------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(1600, 900)
        self.setAcceptDrops(True)

        self.settings = QSettings("BottledKraken", "BottledKrakenApp")

        self.last_rec_model_dir = self.settings.value(
            "paths/last_rec_model_dir",
            KRAKEN_MODELS_DIR,
            str
        )

        self.last_seg_model_dir = self.settings.value(
            "paths/last_seg_model_dir",
            KRAKEN_MODELS_DIR,
            str
        )

        self.current_lang = self.settings.value(
            "ui/language",
            self._detect_system_lang(),
            str
        )
        self.log_lang = self._detect_system_lang()

        self.temp_dirs_created = set()
        QApplication.instance().installEventFilter(self)

        self.ai_worker: Optional[AIRevisionWorker] = None

        # LM / localhost
        self.ai_model_id = ""
        self.ai_endpoint = "http://127.0.0.1:1234/v1/chat/completions"
        self.ai_base_url = None
        self.ai_manual_base_url = ""
        self.ai_available_models: List[str] = []
        self.ai_mode = ""

        self._ai_single_line_context: Optional[dict] = None

        self.project_file_path = ""

        # OCR-Korrektur: konservativ und stabil
        self.ai_enable_thinking = False
        self.ai_temperature = 0.0
        self.ai_top_p = 0.2
        self.ai_top_k = 1
        self.ai_presence_penalty = 0.0
        self.ai_repetition_penalty = 1.0
        self.ai_min_p = 0.0
        self.ai_max_tokens = 8000

        self.ai_model_actions: Dict[str, QAction] = {}
        self.ai_model_group: Optional[QActionGroup] = None

        self.voice_worker: Optional[VoiceLineFillWorker] = None
        self.voice_record_dialog: Optional[VoiceRecordDialog] = None

        saved_whisper_base = self.settings.value("paths/whisper_models_base_dir", "", str)
        self.whisper_models_base_dir = (
            self._normalize_whisper_base_dir(saved_whisper_base)
            if (saved_whisper_base or "").strip()
            else self._default_whisper_base_dir()
        )
        self.whisper_available_models: List[str] = []
        self.whisper_model_path = ""
        self.whisper_model_name = ""
        self.whisper_model_loaded = False
        self.whisper_selected_input_device = None
        self.whisper_selected_input_device_label = ""

        self.reading_direction = READING_MODES["TB_LR"]
        self.device_str = "cpu"
        self.show_overlay = True
        self.model_path = ""
        self.seg_model_path = ""
        self.kraken_rec_models: List[str] = []
        self.kraken_seg_models: List[str] = []
        self.kraken_unknown_models: List[str] = []
        self.current_export_dir = ""
        self.current_theme = self.settings.value("ui/theme", "bright", str)

        # Dynamisches Verhältnis der Queue-Spaltenbreiten
        self.queue_col_ratio = 0.75
        self._resizing_cols = False

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(self._tr("status_ready"))

        self.worker: Optional[OCRWorker] = None
        self.queue_items: List[TaskItem] = []

        self.pdf_worker: Optional[PDFRenderWorker] = None
        self.pdf_progress_dlg: Optional[QProgressDialog] = None
        self._pending_pdf_path: Optional[str] = None

        self.export_worker: Optional[ExportWorker] = None
        self.export_dialog: Optional[ProgressStatusDialog] = None
        self.ai_batch_worker: Optional[AIBatchRevisionWorker] = None
        self.ai_batch_dialog: Optional[ProgressStatusDialog] = None
        self.ai_progress_dialog: Optional[ProgressStatusDialog] = None

        self.hf_download_worker = None
        self.hf_download_dialog = None

        # Canvas (Bildanzeige)
        self.canvas = ImageCanvas(tr_func=self._tr)
        self.canvas.rect_clicked.connect(self.on_rect_clicked)
        self.canvas.rect_changed.connect(self.on_overlay_rect_changed)
        self.canvas.files_dropped.connect(self.add_files_to_queue)
        self.canvas.box_drawn.connect(self.on_box_drawn)

        self.canvas.overlay_add_draw_requested.connect(self.on_canvas_add_box_draw)
        self.canvas.overlay_edit_requested.connect(self.on_canvas_edit_box)
        self.canvas.overlay_delete_requested.connect(self.on_canvas_delete_box)
        self.canvas.overlay_select_requested.connect(self.on_canvas_select_line)
        self.canvas.overlay_multi_selected.connect(self.on_canvas_multi_selected)
        self.canvas.box_split_requested.connect(self.on_canvas_split_box)

        # Wartebereich-Tabelle
        self.queue_table = DropQueueTable()
        self.queue_table.setColumnCount(4)
        self.queue_table.verticalHeader().setVisible(False)
        self.queue_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.queue_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.queue_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.queue_table.itemChanged.connect(self.on_item_changed)
        self.queue_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.queue_table.customContextMenuRequested.connect(self.queue_context_menu)
        self.queue_table.currentCellChanged.connect(self.on_queue_current_cell_changed)
        self.queue_table.cellDoubleClicked.connect(self.on_queue_double_click)
        self.queue_table.delete_pressed.connect(self.delete_current_context)
        self.queue_table.files_dropped.connect(self.add_files_to_queue)
        self.queue_table.table_resized.connect(self._fit_queue_columns_exact)

        header = self.queue_table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setSectionsMovable(False)
        header.setSectionsClickable(True)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.sectionResized.connect(self._on_queue_header_resized)
        header.sectionClicked.connect(self._on_queue_header_clicked)
        self.queue_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Header-Schrift im Wartebereich nicht fett
        header_font = header.font()
        header_font.setBold(False)
        header.setFont(header_font)

        # Hinweis-Overlay für den Wartebereich
        self.queue_hint = QLabel(self._tr("queue_drop_hint"), self.queue_table.viewport())
        self.queue_hint.setAlignment(Qt.AlignCenter)
        self.queue_hint.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.queue_hint.setStyleSheet("color: rgba(180,180,180,180); font-style: italic;")
        self.queue_hint.hide()

        # Zeilenliste
        self.list_lines = LinesTreeWidget(tr_func=self._tr)
        self.list_lines.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_lines.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)

        self.list_lines.currentItemChanged.connect(self.on_line_selected)
        self.list_lines.itemSelectionChanged.connect(self.on_lines_selection_changed)
        self.list_lines.itemChanged.connect(self.on_line_item_edited)
        self.list_lines.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_lines.customContextMenuRequested.connect(self.lines_context_menu)
        self.list_lines.delete_pressed.connect(self.delete_current_context)
        self.list_lines.reorder_committed.connect(self.on_lines_reordered)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)  # idle = normale Prozentanzeige
        self.progress_bar.setValue(0)

        # Log (unter Queue)
        self.log_visible = False
        self.log_edit = QPlainTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setMaximumBlockCount(5000)  # damit es nicht endlos wächst
        self.log_edit.hide()

        self.lbl_queue = QLabel(self._tr("lbl_queue"))
        self.lbl_lines = QLabel(self._tr("lbl_lines"))

        # Toolbar-Aktionen
        self.act_add = QAction(
            self._themed_or_standard_icon("document-open", QStyle.SP_DialogOpenButton),
            self._tr("act_add_files"),
            self,
        )
        self.act_add.triggered.connect(self.choose_files)

        self.act_clear = QAction(
            self._themed_or_standard_icon("edit-clear", QStyle.SP_DialogResetButton),
            self._tr("act_clear_queue"),
            self,
        )
        self.act_clear.triggered.connect(self.clear_queue)

        self.act_play = QAction(
            self._themed_or_standard_icon("media-playback-start", QStyle.SP_MediaPlay),
            self._tr("act_start_ocr"),
            self,
        )
        self.act_play.triggered.connect(self.start_ocr)

        self.act_stop = QAction(
            self._themed_or_standard_icon("media-playback-stop", QStyle.SP_MediaStop),
            self._tr("act_stop_ocr"),
            self,
        )
        self.act_stop.setEnabled(False)
        self.act_stop.triggered.connect(self.stop_ocr)

        self.act_image_edit = QAction(
            self._themed_or_standard_icon("edit-cut", QStyle.SP_FileDialogDetailedView),
            self._tr("act_image_edit"),
            self,
        )
        self.act_image_edit.triggered.connect(self.open_image_edit_dialog)

        self.act_project_load_toolbar = QAction(
            self._themed_or_standard_icon("document-open", QStyle.SP_DialogOpenButton),
            self._tr("menu_project_load"),
            self,
        )
        self.act_project_load_toolbar.triggered.connect(self.load_project)

        self.act_ai_revise = QAction(self._tr("act_ai_revise"), self)
        self.act_ai_revise.setToolTip(self._tr("act_ai_revise_tip"))
        self.act_ai_revise.triggered.connect(self.run_ai_revision)

        self._ai_multi_line_context: Optional[dict] = None

        self._reset_ai_server_cache()
        self._ai_server_cache_ttl = 2.0

        self._update_ai_model_ui()

        self.act_toggle_log = QAction(QIcon.fromTheme("document-preview"), self._tr("log_toggle_show"), self)
        self.act_toggle_log.setCheckable(True)
        self.act_toggle_log.setChecked(False)
        self.act_toggle_log.toggled.connect(self.toggle_log_area)

        # Undo-/Redo-Aktionen
        self.act_undo = QAction(self._tr("act_undo"), self)
        self.act_undo.setShortcut(QKeySequence("Ctrl+Z"))
        self.act_undo.triggered.connect(self.undo)

        self.act_redo = QAction(self._tr("act_redo"), self)
        self.act_redo.setShortcut(QKeySequence("Ctrl+Y"))
        self.act_redo.triggered.connect(self.redo)

        self.addAction(self.act_undo)
        self.addAction(self.act_redo)

        # -----------------------------
        # Globale Shortcuts
        # -----------------------------
        self.act_project_save_sc = QAction(self)
        self.act_project_save_sc.setShortcut(QKeySequence("Ctrl+S"))
        self.act_project_save_sc.triggered.connect(self.save_project)
        self.addAction(self.act_project_save_sc)

        self.act_project_save_as_sc = QAction(self)
        self.act_project_save_as_sc.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.act_project_save_as_sc.triggered.connect(self.save_project_as)
        self.addAction(self.act_project_save_as_sc)

        self.act_project_load_sc = QAction(self)
        self.act_project_load_sc.setShortcut(QKeySequence("Ctrl+I"))
        self.act_project_load_sc.triggered.connect(self.load_project)
        self.addAction(self.act_project_load_sc)

        self.act_export_sc = QAction(self)
        self.act_export_sc.setShortcut(QKeySequence("Ctrl+E"))
        self.act_export_sc.triggered.connect(self.export_default_shortcut)
        self.addAction(self.act_export_sc)

        self.act_quit_sc = QAction(self)
        self.act_quit_sc.setShortcut(QKeySequence("Ctrl+Q"))
        self.act_quit_sc.triggered.connect(self.close)
        self.addAction(self.act_quit_sc)

        self.act_start_ocr_sc = QAction(self)
        self.act_start_ocr_sc.setShortcut(QKeySequence("Ctrl+K"))
        self.act_start_ocr_sc.triggered.connect(self.start_ocr)
        self.addAction(self.act_start_ocr_sc)

        self.act_stop_ocr_sc = QAction(self)
        self.act_stop_ocr_sc.setShortcut(QKeySequence("Ctrl+P"))
        self.act_stop_ocr_sc.triggered.connect(self.stop_ocr)
        self.addAction(self.act_stop_ocr_sc)

        self.act_ai_revise_sc = QAction(self)
        self.act_ai_revise_sc.setShortcut(QKeySequence("Ctrl+L"))
        self.act_ai_revise_sc.triggered.connect(self.run_ai_revision)
        self.addAction(self.act_ai_revise_sc)

        self.act_voice_fill_sc = QAction(self)
        self.act_voice_fill_sc.setShortcut(QKeySequence("Ctrl+M"))
        self.act_voice_fill_sc.triggered.connect(self.run_voice_line_fill)
        self.addAction(self.act_voice_fill_sc)

        self.act_help_shortcuts_sc = QAction(self)
        self.act_help_shortcuts_sc.setShortcut(QKeySequence(Qt.Key_F1))
        self.act_help_shortcuts_sc.triggered.connect(self.show_lm_help_dialog)
        self.addAction(self.act_help_shortcuts_sc)

        self.act_choose_rec_sc = QAction(self)
        self.act_choose_rec_sc.setShortcut(QKeySequence(Qt.Key_F2))
        self.act_choose_rec_sc.triggered.connect(self.choose_rec_model_if_missing)
        self.addAction(self.act_choose_rec_sc)

        self.act_choose_seg_sc = QAction(self)
        self.act_choose_seg_sc.setShortcut(QKeySequence(Qt.Key_F3))
        self.act_choose_seg_sc.triggered.connect(self.choose_seg_model_if_missing)
        self.addAction(self.act_choose_seg_sc)

        self.act_manual_lm_url_sc = QAction(self)
        self.act_manual_lm_url_sc.setShortcut(QKeySequence(Qt.Key_F4))
        self.act_manual_lm_url_sc.triggered.connect(self.set_manual_ai_base_url_dialog)
        self.addAction(self.act_manual_lm_url_sc)

        self.act_scan_lm_sc = QAction(self)
        self.act_scan_lm_sc.setShortcut(QKeySequence(Qt.Key_F5))
        self.act_scan_lm_sc.triggered.connect(self.scan_ai_models_now)
        self.addAction(self.act_scan_lm_sc)

        self.act_scan_whisper_sc = QAction(self)
        self.act_scan_whisper_sc.setShortcut(QKeySequence(Qt.Key_F6))
        self.act_scan_whisper_sc.triggered.connect(self.scan_whisper_and_select_first_mic)
        self.addAction(self.act_scan_whisper_sc)

        self.act_toggle_log_sc = QAction(self)
        self.act_toggle_log_sc.setShortcut(QKeySequence(Qt.Key_F7))
        self.act_toggle_log_sc.triggered.connect(lambda: self.act_toggle_log.toggle())
        self.addAction(self.act_toggle_log_sc)

        self.act_select_all_context_sc = QAction(self)
        self.act_select_all_context_sc.setShortcut(QKeySequence.SelectAll)
        self.act_select_all_context_sc.triggered.connect(self.select_all_current_context)
        self.addAction(self.act_select_all_context_sc)

        self.act_delete_context_sc = QAction(self)
        self.act_delete_context_sc.setShortcut(QKeySequence.Delete)
        self.act_delete_context_sc.triggered.connect(self.delete_current_context)
        self.addAction(self.act_delete_context_sc)

        self.btn_rec_model = QPushButton(self._tr("btn_rec_model_empty"))
        self.btn_rec_model.setIcon(
            self._themed_or_standard_icon("document-open", QStyle.SP_DialogOpenButton)
        )
        self.btn_rec_model.clicked.connect(self.choose_rec_model)

        self.btn_seg_model = QPushButton(self._tr("btn_seg_model_empty"))
        self.btn_seg_model.setIcon(
            self._themed_or_standard_icon("document-open", QStyle.SP_DialogOpenButton)
        )
        self.btn_seg_model.clicked.connect(self.choose_seg_model)

        self.btn_theme_toggle = QToolButton()
        self.btn_theme_toggle.setCheckable(True)
        self.btn_theme_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_theme_toggle.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.btn_theme_toggle.clicked.connect(self.toggle_theme)

        self.btn_lang_menu = QToolButton()
        self.btn_lang_menu.setPopupMode(QToolButton.InstantPopup)
        self.btn_lang_menu.setCursor(Qt.PointingHandCursor)

        self._pending_box_for_row: Optional[int] = None
        self._pending_new_line_box: bool = False

        self._auto_select_best_device()
        self._scan_kraken_models()
        self._load_default_segmentation_model()
        self._init_ui()
        self._init_menu()
        self.apply_theme(self.current_theme)
        self.retranslate_ui()

        QTimer.singleShot(0, self._fit_queue_columns_exact)
        QTimer.singleShot(0, self._update_queue_hint)
        QTimer.singleShot(0, self._refresh_hw_menu_availability)

        self.canvas.set_overlay_enabled(False)
        self._log(self._tr_log("log_started"))

        self._is_closing = False
        self._shutdown_force_timer = QTimer(self)
        self._shutdown_force_timer.setSingleShot(True)
        self._shutdown_force_timer.timeout.connect(self._force_kill_process)

        self._shutdown_poll_timer = QTimer(self)
        self._shutdown_poll_timer.setInterval(100)
        self._shutdown_poll_timer.timeout.connect(self._check_shutdown_complete)

        self._lm_help_dialog_open = False

    def _reset_ai_server_cache(self):
        self._ai_server_cache = {
            "ts": 0.0,
            "base_url": None,
            "model_id": None,
        }

    def _close_ai_progress_dialog(self):
        if hasattr(self, "ai_progress_dialog") and self.ai_progress_dialog:
            self.ai_progress_dialog.close()
            self.ai_progress_dialog = None

    def _scene_rect_to_bbox(self, scene_rect: QRectF, im: Optional[Image.Image]) -> Optional[BBox]:
        if im is None:
            return None

        img_w, img_h = im.size
        r = scene_rect.normalized()

        x0 = max(0, min(img_w - 1, int(round(r.left()))))
        y0 = max(0, min(img_h - 1, int(round(r.top()))))
        x1 = max(1, min(img_w, int(round(r.right()))))
        y1 = max(1, min(img_h, int(round(r.bottom()))))

        if x1 <= x0:
            x1 = min(img_w, x0 + 1)
        if y1 <= y0:
            y1 = min(img_h, y0 + 1)

        return (x0, y0, x1, y1)

    def _persist_live_canvas_bboxes(self, task: Optional[TaskItem]):
        if not task or not task.results:
            return

        text, kr_records, im, recs = task.results
        changed = False

        for idx, rv in enumerate(recs):
            rect_item = self.canvas._rects.get(idx)
            if not rect_item or not isValid(rect_item):
                continue

            scene_rect = rect_item.mapRectToScene(rect_item.rect()).normalized()
            bb = self._scene_rect_to_bbox(scene_rect, im)
            if bb and rv.bbox != bb:
                rv.bbox = bb
                changed = True

        if changed:
            task.results = (
                "\n".join(r.text for r in recs).strip(),
                kr_records,
                im,
                recs
            )

        self._update_task_preset_bboxes(task)

    def _all_workers(self):
        return [
            self.worker,
            self.ai_worker,
            self.ai_batch_worker,
            self.export_worker,
            self.pdf_worker,
            self.hf_download_worker,
            self.voice_worker,
        ]

    def _request_all_workers_stop(self):
        workers = []

        if self.worker and self.worker.isRunning():
            try:
                self.worker.requestInterruption()
                workers.append(self.worker)
            except Exception:
                pass

        if self.ai_worker and self.ai_worker.isRunning():
            try:
                self.ai_worker.cancel()
                workers.append(self.ai_worker)
            except Exception:
                pass

        if self.ai_batch_worker and self.ai_batch_worker.isRunning():
            try:
                self.ai_batch_worker.cancel()
                workers.append(self.ai_batch_worker)
            except Exception:
                pass

        if self.export_worker and self.export_worker.isRunning():
            try:
                self.export_worker.requestInterruption()
                workers.append(self.export_worker)
            except Exception:
                pass

        if self.pdf_worker and self.pdf_worker.isRunning():
            try:
                self.pdf_worker.requestInterruption()
                workers.append(self.pdf_worker)
            except Exception:
                pass

        if self.hf_download_worker and self.hf_download_worker.isRunning():
            try:
                self.hf_download_worker.cancel()
                workers.append(self.hf_download_worker)
            except Exception:
                pass

        if self.voice_worker and self.voice_worker.isRunning():
            try:
                self.voice_worker.cancel()
                workers.append(self.voice_worker)
            except Exception:
                pass

        for w in workers:
            try:
                w.wait(1500)
            except Exception:
                pass

    def _workers_still_running(self) -> bool:
        for w in self._all_workers():
            try:
                if w and w.isRunning():
                    return True
            except Exception:
                pass
        return False

    def _check_shutdown_complete(self):
        if not self._workers_still_running():
            self._shutdown_poll_timer.stop()
            self._shutdown_force_timer.stop()
            self._cleanup_temp_dirs()
            self._final_close()

    def _final_close(self):
        try:
            if self.voice_record_dialog:
                self.voice_record_dialog.close()
                self.voice_record_dialog = None
        except Exception:
            pass

        try:
            if self.ai_progress_dialog:
                self.ai_progress_dialog.close()
                self.ai_progress_dialog = None
        except Exception:
            pass

        try:
            if self.ai_batch_dialog:
                self.ai_batch_dialog.close()
                self.ai_batch_dialog = None
        except Exception:
            pass

        try:
            if self.export_dialog:
                self.export_dialog.close()
                self.export_dialog = None
        except Exception:
            pass

        try:
            if self.pdf_progress_dlg:
                self.pdf_progress_dlg.close()
                self.pdf_progress_dlg = None
        except Exception:
            pass

        try:
            if self.hf_download_dialog:
                self.hf_download_dialog.close()
                self.hf_download_dialog = None
        except Exception:
            pass

        self._shutdown_poll_timer.stop()
        self._shutdown_force_timer.stop()

        # Fenster wirklich schließen, ohne self.close() erneut auszulösen
        super().close()

    def _force_kill_process(self):
        # Kein harter Kill mehr.
        # Nur Diagnose, falls doch noch etwas hängt.
        running = []
        for w in self._all_workers():
            try:
                if w and w.isRunning():
                    running.append(type(w).__name__)
            except Exception:
                pass

        if running:
            print("Shutdown wartet noch auf:", ", ".join(running))

        # Letzter Versuch: regulär quitten
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def _normalize_whisper_base_dir(self, raw: str) -> str:
        return os.path.abspath((raw or "").strip()) if (raw or "").strip() else ""

    def _scan_whisper_models(self) -> List[str]:
        self.whisper_available_models = []

        base = self._normalize_whisper_base_dir(self.whisper_models_base_dir)
        if not base or not os.path.isdir(base):
            return []

        out = []

        # Fall A: Basisordner selbst ist schon ein Modellordner
        if os.path.isfile(os.path.join(base, "model.bin")):
            out.append(base)

        # Fall B: Unterordner enthalten Modelle
        try:
            for name in sorted(os.listdir(base)):
                full = os.path.join(base, name)
                if os.path.isdir(full) and os.path.isfile(os.path.join(full, "model.bin")):
                    out.append(full)
        except Exception:
            pass

        self.whisper_available_models = out
        return out

    def _find_existing_whisper_large_v3_model(self) -> str:
        candidates = []
        seen = set()

        for raw_base in [self.whisper_models_base_dir, self._default_whisper_base_dir()]:
            base = self._normalize_whisper_base_dir(raw_base)
            if not base or base in seen:
                continue
            seen.add(base)
            candidates.append(base)

        for base in candidates:
            if not os.path.isdir(base):
                continue

            # Fall A: Basisordner ist selbst schon das Modell
            if (
                    os.path.basename(base).lower() == "faster-whisper-large-v3"
                    and os.path.isfile(os.path.join(base, "model.bin"))
            ):
                return base

            # Fall B: klassischer Unterordner
            direct = os.path.join(base, "faster-whisper-large-v3")
            if os.path.isdir(direct) and os.path.isfile(os.path.join(direct, "model.bin")):
                return direct

            # Fall C: allgemein Unterordner durchsuchen
            try:
                for name in os.listdir(base):
                    full = os.path.join(base, name)
                    if (
                            os.path.isdir(full)
                            and name.lower() == "faster-whisper-large-v3"
                            and os.path.isfile(os.path.join(full, "model.bin"))
                    ):
                        return full
            except Exception:
                pass

        return ""

    def _set_whisper_model(self, model_path: str):
        model_path = os.path.abspath(model_path) if model_path else ""
        self.whisper_model_path = model_path
        self.whisper_model_name = os.path.basename(model_path) if model_path else ""
        self.whisper_model_loaded = bool(model_path)
        self._rebuild_whisper_model_submenu()
        self._update_whisper_menu_status()

    def _clear_whisper_model(self):
        self.whisper_model_path = ""
        self.whisper_model_name = ""
        self.whisper_model_loaded = False
        self._rebuild_whisper_model_submenu()
        self._update_whisper_menu_status()
        self.status_bar.showMessage(self._tr("msg_whisper_model_unloaded"))

    def _rebuild_whisper_model_submenu(self):
        if not hasattr(self, "whisper_models_submenu"):
            return

        self.whisper_models_submenu.clear()

        if not hasattr(self, "whisper_model_group") or self.whisper_model_group is None:
            self.whisper_model_group = QActionGroup(self)
            self.whisper_model_group.setExclusive(True)

        for act in list(self.whisper_model_group.actions()):
            self.whisper_model_group.removeAction(act)

        if not self.whisper_available_models:
            empty_act = QAction(self._tr("no_models_scan"), self)
            empty_act.setEnabled(False)
            self.whisper_models_submenu.addAction(empty_act)
        else:
            for model_path in self.whisper_available_models:
                name = os.path.basename(model_path)
                act = QAction(name, self)
                act.setCheckable(True)
                act.setChecked(os.path.abspath(model_path) == os.path.abspath(self.whisper_model_path or ""))
                act.triggered.connect(lambda checked, mp=model_path: self._set_whisper_model(mp))
                self.whisper_model_group.addAction(act)
                self.whisper_models_submenu.addAction(act)

        self.whisper_models_submenu.addSeparator()

        self.act_whisper_unload = QAction(self._tr("act_unload_model"), self)
        self.act_whisper_unload.triggered.connect(self._clear_whisper_model)
        self.act_whisper_unload.setEnabled(bool(self.whisper_model_loaded))
        self.whisper_models_submenu.addAction(self.act_whisper_unload)

    def _update_whisper_menu_status(self):
        model_txt = self.whisper_model_name if self.whisper_model_name else "-"
        mic_txt = self.whisper_selected_input_device_label if self.whisper_selected_input_device_label else "-"
        path_txt = self.whisper_models_base_dir if self.whisper_models_base_dir else "-"

        if hasattr(self, "act_whisper_status_model"):
            self.act_whisper_status_model.setText(self._tr("whisper_status_model", model_txt))
        if hasattr(self, "act_whisper_status_mic"):
            self.act_whisper_status_mic.setText(self._tr("whisper_status_mic", mic_txt))
        if hasattr(self, "act_whisper_status_path"):
            self.act_whisper_status_path.setText(self._tr("whisper_status_path", path_txt))
        if hasattr(self, "act_whisper_unload"):
            self.act_whisper_unload.setEnabled(bool(self.whisper_model_loaded))

    def set_whisper_base_dir_dialog(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            self._tr("dlg_whisper_model_dir"),
            self.whisper_models_base_dir or os.getcwd()
        )
        if not folder:
            return

        self.whisper_models_base_dir = self._normalize_whisper_base_dir(folder)
        self.settings.setValue("paths/whisper_models_base_dir", self.whisper_models_base_dir)
        self._scan_whisper_models()

        # falls bisheriges Modell nicht mehr im Pfad liegt -> entladen
        if self.whisper_model_path and not os.path.exists(self.whisper_model_path):
            self._clear_whisper_model()
        else:
            self._rebuild_whisper_model_submenu()
            self._update_whisper_menu_status()

        self.status_bar.showMessage(self._tr("msg_whisper_path_set", self.whisper_models_base_dir))

    def scan_whisper_models_now(self):
        models = self._scan_whisper_models()

        if models:
            if not self.whisper_model_path or self.whisper_model_path not in models:
                self._set_whisper_model(models[0])
            else:
                self._rebuild_whisper_model_submenu()
                self._update_whisper_menu_status()
            self.status_bar.showMessage(self._tr("msg_whisper_models_found", len(models)))
        else:
            self._clear_whisper_model()
            self.status_bar.showMessage(self._tr("msg_whisper_models_not_found"))

    def scan_whisper_and_select_first_mic(self):
        # 1) Whisper-Modelle scannen
        self.scan_whisper_models_now()

        # 2) erstes verfügbares Mikro automatisch setzen
        devices = self._get_input_audio_devices()
        if not devices:
            return

        first = devices[0]
        self.whisper_selected_input_device = first["index"]
        self.whisper_selected_input_device_label = first["label"]

        self._update_whisper_menu_status()
        self.status_bar.showMessage(
            self._tr("msg_microphone_set", self.whisper_selected_input_device_label)
        )

    def choose_whisper_microphone_dialog(self):
        devices = self._get_input_audio_devices()
        if not devices:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_no_audio_devices"))
            return

        labels = [d["label"] for d in devices]
        current_idx = 0
        if self.whisper_selected_input_device_label:
            try:
                current_idx = labels.index(self.whisper_selected_input_device_label)
            except ValueError:
                current_idx = 0

        selected, ok = QInputDialog.getItem(
            self,
            self._tr("dlg_choose_microphone"),
            self._tr("dlg_audio_input_device"),
            labels,
            current_idx,
            False
        )
        if not ok or not selected:
            return

        for dev in devices:
            if dev["label"] == selected:
                self.whisper_selected_input_device = dev["index"]
                self.whisper_selected_input_device_label = dev["label"]
                break

        self._update_whisper_menu_status()
        self.status_bar.showMessage(self._tr("msg_microphone_set", self.whisper_selected_input_device_label))

    def choose_rec_model_if_missing(self):
        if not self.model_path:
            self.choose_rec_model()

    def choose_seg_model_if_missing(self):
        if not self.seg_model_path:
            self.choose_seg_model()

    def export_default_shortcut(self):
        items = [
            ("Text (.txt)", "txt"),
            ("CSV (.csv)", "csv"),
            ("JSON (.json)", "json"),
            ("ALTO (.xml)", "alto"),
            ("hOCR (.html)", "hocr"),
            ("PDF (.pdf)", "pdf"),
        ]
        names = [x[0] for x in items]

        choice, ok = QInputDialog.getItem(
            self,
            "Export",
            self._tr("export_choose_format_label"),
            names,
            0,
            False
        )
        if not ok or not choice:
            return

        fmt = next(fmt for name, fmt in items if name == choice)
        self.export_flow(fmt)

    def _overlay_selected_rows(self) -> List[int]:
        return sorted(set(int(i) for i in getattr(self.canvas, "_selected_indices", set()) if i is not None))

    def _has_overlay_selection(self) -> bool:
        return len(self._overlay_selected_rows()) > 0

    def _has_line_selection(self) -> bool:
        return len(self._selected_line_rows()) > 0

    def delete_current_context(self):
        """
        Entf:
        - wenn Overlay-Box(en) ausgewählt -> Box(en) + zugehörige Zeile(n) löschen
        - sonst wenn Zeile(n) ausgewählt -> Zeile(n) + Box(en) löschen
        - sonst Queue-Löschen wie bisher
        """
        task = self._current_task()

        overlay_rows = self._overlay_selected_rows()
        line_rows = self._selected_line_rows()

        if task and task.results and task.status == STATUS_DONE:
            rows = overlay_rows if overlay_rows else line_rows
            if rows:
                self._delete_multiple_lines(task, rows)
                return

        # Fallback wie bisher
        if self.queue_table.hasFocus():
            self.delete_selected_queue_items(reset_preview=True)

    def select_all_current_context(self):
        """
        Ctrl+A:
        - wenn Zeilenliste oder Canvas aktiv -> alle Zeilen + alle Overlays auswählen
        - sonst normales Queue-Verhalten
        """
        task = self._current_task()
        if not task or not task.results:
            if self.queue_table.rowCount() > 0:
                self.queue_table.selectAll()
            return

        fw = QApplication.focusWidget()

        canvas_has_focus = (fw is self.canvas or fw is self.canvas.viewport())
        lines_has_focus = (fw is self.list_lines or self.list_lines.isAncestorOf(fw))

        if canvas_has_focus or lines_has_focus or self._has_overlay_selection() or self._has_line_selection():
            _, _, _, recs = task.results
            indices = list(range(len(recs)))

            self.list_lines.blockSignals(True)
            self.list_lines.clearSelection()
            for idx in indices:
                if 0 <= idx < self.list_lines.count():
                    it = self.list_lines.row_item(idx)
                    if it:
                        it.setSelected(True)
            if indices:
                self.list_lines.setCurrentRow(indices[0])
            self.list_lines.blockSignals(False)

            self.canvas.select_indices(indices, center=False)
            self.canvas.overlay_multi_selected.emit(indices)
            return

        # Fallback: Queue
        if self.queue_table.rowCount() > 0:
            self.queue_table.selectAll()

    def _delete_multiple_lines(self, task: TaskItem, rows: List[int]):
        if not task.results:
            return

        text, kr_records, im, recs = task.results
        clean_rows = sorted(set(int(r) for r in rows if 0 <= int(r) < len(recs)), reverse=True)
        if not clean_rows:
            return

        self._push_undo(task)

        for row in clean_rows:
            recs.pop(row)

        task.edited = True

        next_row = None
        if recs:
            lowest_removed = min(clean_rows)
            next_row = max(0, min(lowest_removed, len(recs) - 1))

        self._sync_ui_after_recs_change(task, keep_row=next_row)

    def show_shortcuts_dialog(self):
        self.show_lm_help_dialog()

    def _start_voice_line_fill(self):
        task = self._current_task()
        if not task or task.status != STATUS_DONE or not task.results:
            return

        current_row = self.list_lines.currentRow()
        if current_row < 0:
            return

        _, _, _, recs = task.results
        if not (0 <= current_row < len(recs)):
            return

        if self.voice_worker and self.voice_worker.isRunning():
            return

        if not self.whisper_model_path or not os.path.isdir(self.whisper_model_path):
            QMessageBox.warning(
                self,
                self._tr("warn_title"),
                self._tr("warn_whisper_model_not_loaded")
            )
            return

        if self.whisper_selected_input_device is None:
            QMessageBox.warning(
                self,
                self._tr("warn_title"),
                self._tr("warn_no_microphone_available")
            )
            return

        fw_device, fw_compute = self._resolve_faster_whisper_device()

        devices = self._get_input_audio_devices()
        dev_meta = next(
            (d for d in devices if d["index"] == self.whisper_selected_input_device),
            None
        )

        self.voice_worker = VoiceLineFillWorker(
            path=task.path,
            line_index=current_row,
            model_dir=self.whisper_model_path,
            device=fw_device,
            compute_type=fw_compute,
            language=None,
            input_device=self.whisper_selected_input_device,
            input_samplerate=(dev_meta.get("default_samplerate") if dev_meta else None),
            parent=self
        )

        self.voice_worker.finished_line.connect(self.on_voice_line_fill_done)
        self.voice_worker.failed_line.connect(self.on_voice_line_fill_failed)
        self.voice_worker.progress_changed.connect(self.on_voice_progress_changed)
        self.voice_worker.status_changed.connect(self.on_voice_status_changed)

        task.status = STATUS_VOICE_RECORDING
        self._update_queue_row(task.path)
        self.status_bar.showMessage(self._tr("msg_voice_started"))
        self._log(
            self._tr_log("log_voice_import_started", os.path.basename(task.path), current_row + 1, self.whisper_selected_input_device_label, self.whisper_model_name)
        )

        if self.voice_record_dialog:
            self.voice_record_dialog.set_recording_state(True)

        self._set_progress_idle(0)
        self.voice_worker.start()

    def _cancel_voice_record_dialog(self):
        if self.voice_worker and self.voice_worker.isRunning():
            self.voice_worker.cancel()

    def _audio_backend_priority(self, hostapi_name: str) -> int:
        n = (hostapi_name or "").lower()

        # Linux
        if "pipewire" in n:
            return 500
        if "pulse" in n or "pulseaudio" in n:
            return 450
        if "alsa" in n:
            return 350
        if "jack" in n:
            return 250

        # Windows
        if "wasapi" in n:
            return 400
        if "directsound" in n:
            return 300
        if "mme" in n:
            return 200
        if "wdm-ks" in n:
            return 100

        # macOS
        if "core audio" in n:
            return 450

        return 0

    def _normalize_audio_device_name(self, name: str) -> str:
        txt = (name or "").strip()

        # Backend-Suffixe entfernen
        txt = re.sub(
            r"\s+\((MME|Windows DirectSound|Windows WASAPI|Windows WDM-KS)\)\s*$",
            "",
            txt,
            flags=re.IGNORECASE
        )

        # typische Dopplungen säubern
        txt = re.sub(r"\s+", " ", txt).strip()

        # System-Default hübscher anzeigen
        if txt.lower() in ("microsoft soundmapper - input", "primärer soundaufnahmetreiber"):
            return self._tr("audio_device_default_mic")

        return txt

    def _get_input_audio_devices(self) -> List[dict]:
        out = []

        try:
            devices = sd.query_devices()
        except Exception:
            return out

        try:
            default_in = sd.default.device[0]
        except Exception:
            default_in = None

        grouped: Dict[str, dict] = {}

        for i, dev in enumerate(devices):
            try:
                max_in = int(dev.get("max_input_channels", 0))
            except Exception:
                max_in = 0

            if max_in <= 0:
                continue

            raw_name = str(dev.get("name", self._tr("audio_device_generic", i))).strip()
            hostapi_idx = dev.get("hostapi", None)

            hostapi_name = ""
            try:
                if hostapi_idx is not None:
                    hostapi_name = str(sd.query_hostapis(hostapi_idx).get("name", "")).strip()
            except Exception:
                pass

            clean_name = self._normalize_audio_device_name(raw_name)

            score = self._audio_backend_priority(hostapi_name)
            if i == default_in:
                score += 10000

            candidate = {
                "index": i,
                "label": clean_name,
                "hostapi": hostapi_name,
                "score": score,
                "is_default": (i == default_in),
                "default_samplerate": int(float(dev.get("default_samplerate", VOICE_SAMPLE_RATE))),
                "max_input_channels": max_in,
            }

            # pro Hauptgerät nur die beste Variante behalten
            old = grouped.get(clean_name)
            if old is None or candidate["score"] > old["score"]:
                grouped[clean_name] = candidate

        out = list(grouped.values())

        out.sort(
            key=lambda d: (
                0 if d["is_default"] else 1,
                -d["score"],
                d["label"].lower()
            )
        )

        return out

    def _selected_line_rows(self) -> List[int]:
        return self.list_lines.selected_line_rows()

    def run_ai_revision_for_selected_lines(self):
        task = self._current_task()
        self._persist_live_canvas_bboxes(task)
        if not task or task.status != STATUS_DONE or not task.results:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
            return

        text, kr_records, im, recs = task.results
        rows = self._selected_line_rows()

        if not rows:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_select_multiple_lines_first"))
            return

        if len(rows) == 1:
            self.run_ai_revision_for_single_line(rows[0])
            return

        model_id = self._resolve_ai_model_id()
        if not model_id:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_ai_model"))
            return

        if self.ai_worker and self.ai_worker.isRunning():
            return

        live_recs = self._current_recs_for_ai(task)

        selected_recs = [
            RecordView(
                idx=i,
                text=live_recs[row].text,
                bbox=live_recs[row].bbox
            )
            for i, row in enumerate(rows)
        ]

        self._ai_multi_line_context = {
            "path": task.path,
            "rows": rows,
        }

        self.act_ai_revise.setEnabled(False)
        self.status_bar.showMessage(self._tr("msg_ai_selected_lines_started", len(rows)))
        self._log(
            self._tr_log("log_ai_multi_started", os.path.basename(task.path), ", ".join(str(r + 1) for r in rows))
        )

        self.ai_progress_dialog = ProgressStatusDialog(self._tr("dlg_ai_multi_title"), self._tr, self)
        self.ai_progress_dialog.set_status(
            self._tr("dlg_ai_multi_status", len(rows))
        )
        self.ai_progress_dialog.cancel_requested.connect(self._cancel_ai_revision)
        self.ai_progress_dialog.show()

        self.ai_worker = AIRevisionWorker(
            path=task.path,
            recs=selected_recs,
            lm_model=model_id,
            endpoint=self.ai_endpoint,
            enable_thinking=self.ai_enable_thinking,
            source_kind=task.source_kind,
            temperature=self.ai_temperature,
            top_p=self.ai_top_p,
            top_k=self.ai_top_k,
            presence_penalty=self.ai_presence_penalty,
            repetition_penalty=self.ai_repetition_penalty,
            min_p=self.ai_min_p,
            max_tokens=self.ai_max_tokens,
            tr_func=self._tr,
            parent=self
        )

        self.ai_worker.progress_changed.connect(self.ai_progress_dialog.set_progress)
        self.ai_worker.status_changed.connect(self.ai_progress_dialog.set_status)
        self.ai_worker.status_changed.connect(self._log)
        self.ai_worker.finished_revision.connect(self.on_ai_selected_lines_revision_done)
        self.ai_worker.failed_revision.connect(self.on_ai_selected_lines_revision_failed)
        self.ai_worker.start()

    def on_ai_selected_lines_revision_done(self, path: str, revised_lines: list):
        ctx = getattr(self, "_ai_multi_line_context", None) or {}
        self._ai_multi_line_context = None

        task = next((i for i in self.queue_items if i.path == path), None)
        if not task or not task.results:
            self.act_ai_revise.setEnabled(True)
            if self.ai_progress_dialog:
                self.ai_progress_dialog.close()
                self.ai_progress_dialog = None
            return

        rows = list(ctx.get("rows", []))
        text, kr_records, im, recs = task.results

        if not rows:
            self.act_ai_revise.setEnabled(True)
            if self.ai_progress_dialog:
                self.ai_progress_dialog.close()
                self.ai_progress_dialog = None
            return

        revised_lines = [str(x).strip() for x in revised_lines]

        if len(revised_lines) < len(rows):
            for i in range(len(revised_lines), len(rows)):
                revised_lines.append(recs[rows[i]].text)
        elif len(revised_lines) > len(rows):
            revised_lines = revised_lines[:len(rows)]

        self._push_undo(task)

        new_recs = [
            RecordView(i, recs[i].text, recs[i].bbox)
            for i in range(len(recs))
        ]

        for local_idx, row in enumerate(rows):
            if 0 <= row < len(new_recs):
                new_text = revised_lines[local_idx].strip()
                if new_text:
                    new_recs[row].text = new_text

        task.results = (
            "\n".join(rv.text for rv in new_recs).strip(),
            kr_records,
            im,
            new_recs
        )
        task.edited = True

        cur = self._current_task()
        if cur and cur.path == path:
            self._sync_ui_after_recs_change(task, keep_row=rows[0] if rows else 0)

            self.list_lines.blockSignals(True)
            self.list_lines.clearSelection()
            for row in rows:
                if 0 <= row < self.list_lines.count():
                    it = self.list_lines.row_item(row)
                    if it:
                        it.setSelected(True)
            if rows:
                self.list_lines.setCurrentRow(rows[0])
            self.list_lines.blockSignals(False)
        else:
            self._update_queue_row(path)

        self.act_ai_revise.setEnabled(True)
        self.status_bar.showMessage(self._tr("msg_ai_multi_done", len(rows)))
        self._log(
            self._tr_log("log_ai_multi_done", os.path.basename(path), ", ".join(str(r + 1) for r in rows))
        )

        self._close_ai_progress_dialog()

    def on_ai_selected_lines_revision_failed(self, path: str, msg: str):
        self._ai_multi_line_context = None
        self.act_ai_revise.setEnabled(True)

        if "abgebrochen" in str(msg).lower():
            self.status_bar.showMessage(self._tr("msg_ai_multi_cancelled"))
            self._log(self._tr_log("log_ai_multi_cancelled", os.path.basename(path)))
        else:
            self.status_bar.showMessage(self._tr("msg_ai_multi_failed"))
            self._log(self._tr_log("log_ai_multi_failed", os.path.basename(path), msg))
            QMessageBox.warning(self, self._tr("warn_title"), msg)

        self._close_ai_progress_dialog()

    def _cleanup_temp_dirs(self):
        for d in list(self.temp_dirs_created):
            try:
                if os.path.isdir(d):
                    shutil.rmtree(d, ignore_errors=True)
            except Exception:
                pass
        self.temp_dirs_created.clear()

    def eventFilter(self, obj, event):
        if getattr(self, "_is_closing", False):
            return False

        try:
            et = event.type()

            if et in (QEvent.ShortcutOverride, QEvent.KeyPress):
                if event.matches(QKeySequence.Paste):
                    if QApplication.activeWindow() is not self:
                        return super().eventFilter(obj, event)

                    fw = QApplication.focusWidget()

                    if isinstance(fw, (QLineEdit, QPlainTextEdit, QTextEdit)):
                        return super().eventFilter(obj, event)

                    self.paste_files_from_clipboard()
                    event.accept()
                    return True
        except Exception:
            pass

        return super().eventFilter(obj, event)

    def _is_local_port_open(self, host: str, port: int, timeout: float = 0.12) -> bool:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except Exception:
            return False

    def _reorder_lines_keep_box_slots(self, task: TaskItem, order: List[int], keep_row: Optional[int] = None):
        if not task or not task.results:
            return

        text, kr_records, im, recs = task.results
        n = len(recs)

        if len(order) != n:
            return

        try:
            order = [int(i) for i in order]
        except Exception:
            return

        if sorted(order) != list(range(n)):
            return

        self._push_undo(task)

        old_recs = list(recs)

        # GANZE Records verschieben, nicht nur Texte
        new_recs = [
            RecordView(i, old_recs[src_idx].text, old_recs[src_idx].bbox)
            for i, src_idx in enumerate(order)
        ]

        task.edited = True
        task.results = (text, kr_records, im, new_recs)
        self._sync_ui_after_recs_change(task, keep_row=keep_row)

    def _get_active_ai_model_display(self) -> str:
        return (self.ai_model_id or "").strip() or "-"

    def _update_ai_model_ui(self):
        display = self._get_active_ai_model_display()
        mode_label = self._current_ai_mode_label()
        base_url = self.ai_base_url or "-"

        if hasattr(self, "btn_ai_model"):
            self.btn_ai_model.setText(self._tr("btn_ai_model_value", display))

        if hasattr(self, "act_llm_status"):
            self.act_llm_status.setText(self._tr("llm_status_value", display))

        if hasattr(self, "act_lm_status"):
            self.act_lm_status.setText(self._tr("lm_status_model_value", display))

        if hasattr(self, "act_lm_mode"):
            self.act_lm_mode.setText(self._tr("lm_mode_value", mode_label))

        if hasattr(self, "act_lm_base_url"):
            self.act_lm_base_url.setText(self._tr("lm_server_value", base_url))

    def _process_ui(self):
        QCoreApplication.processEvents()

    def _fetch_loaded_llm_models(self, force: bool = False) -> List[str]:
        if self.ai_mode == "manual" and self.ai_manual_base_url:
            base_url = self._normalize_ai_base_url(self.ai_manual_base_url)
            if not base_url:
                self.ai_base_url = None
                self.ai_available_models = []
                return []
            self.ai_base_url = base_url
            self.ai_endpoint = base_url + "/chat/completions"
        else:
            base_url, _ = self._detect_local_openai_server(force=force)
            self.ai_mode = "auto"
            if base_url:
                self.ai_base_url = base_url
                self.ai_endpoint = base_url + "/chat/completions"
            else:
                self.ai_base_url = None

        if not base_url:
            self.ai_available_models = []
            return []

        models, _ = self._fetch_models_from_base_url(base_url, timeout=0.6)
        self.ai_available_models = models
        return models

    def _looks_like_ssh_input(self, raw: str) -> bool:
        txt = (raw or "").strip()

        if not txt:
            return False

        low = txt.lower()

        if low.startswith("ssh "):
            return True

        if low.startswith("ssh://"):
            return True

        # klassisches user@host
        if re.fullmatch(r"[^@\s]+@[^:\s/]+", txt):
            return True

        # host:22 allein soll NICHT automatisch als URL gelten,
        # ist oft ein SSH-Hinweis
        if re.fullmatch(r"[^/\s:]+:\d+", txt):
            try:
                port = int(txt.rsplit(":", 1)[1])
                if port == 22:
                    return True
            except Exception:
                pass

        return False

    def _normalize_ai_base_url(self, raw: str) -> str:
        url = (raw or "").strip()
        if not url:
            return ""

        # Quotes / Whitespace säubern
        url = url.strip().strip('"').strip("'")
        url = re.sub(r"\s+", "", url)

        # SSH-Eingaben hier bewusst NICHT "erraten"
        if self._looks_like_ssh_input(url):
            return ""

        # Fehlendes Schema ergänzen
        if not re.match(r"^https?://", url, flags=re.IGNORECASE):
            url = "http://" + url

        try:
            parsed = urllib.parse.urlparse(url)
        except Exception:
            return ""

        scheme = (parsed.scheme or "http").lower()
        if scheme not in ("http", "https"):
            return ""

        host = parsed.hostname
        if not host:
            return ""

        port = parsed.port
        path = (parsed.path or "").strip()
        path = re.sub(r"/+", "/", path)

        # Häufige Fehlformen auf Base-URL zurückführen
        low_path = path.lower().rstrip("/")

        strip_suffixes = [
            "/v1/chat/completions",
            "/chat/completions",
            "/v1/completions",
            "/completions",
            "/v1/models",
            "/models",
        ]

        for suffix in strip_suffixes:
            if low_path.endswith(suffix):
                path = path[:len(path) - len(suffix)]
                break

        path = path.rstrip("/")

        # Wenn gar kein API-Pfad da ist -> /v1 anhängen
        # Wenn bereits /v1 vorhanden -> so lassen
        # Wenn ein anderer Pfad da ist -> /v1 anhängen
        if not path:
            path = "/v1"
        elif path.lower() != "/v1" and not path.lower().endswith("/v1"):
            path = path + "/v1"

        # Netloc sauber neu aufbauen
        netloc = host
        if port is not None:
            netloc = f"{host}:{port}"

        normalized = urllib.parse.urlunparse((scheme, netloc, path, "", "", ""))
        return normalized

    def set_manual_ai_base_url_dialog(self):
        dlg = QInputDialog(self)
        dlg.setInputMode(QInputDialog.TextInput)
        dlg.setWindowTitle(self._tr("dlg_lm_url_title"))
        dlg.setLabelText(self._tr("dlg_lm_url_label"))
        dlg.setTextValue(self.ai_manual_base_url or "")
        dlg.setOkButtonText(self._tr("btn_ok"))
        dlg.setCancelButtonText(self._tr("btn_cancel"))
        dlg.resize(560, 420)

        line_edit = dlg.findChild(QLineEdit)
        if line_edit is not None:
            line_edit.setPlaceholderText(self._tr("dlg_lm_url_placeholder"))

        if dlg.exec() != QDialog.Accepted:
            return

        raw = (dlg.textValue() or "").strip()

        if self._looks_like_ssh_input(raw):
            QMessageBox.warning(
                self,
                self._tr("warn_title"),
                self._tr("warn_lm_url_no_ssh")
            )
            return

        normalized = self._normalize_ai_base_url(raw)
        if not normalized:
            QMessageBox.warning(
                self,
                self._tr("warn_title"),
                self._tr("warn_lm_url_invalid")
            )
            return

        self.ai_manual_base_url = normalized
        self.ai_mode = "manual"
        self.ai_base_url = normalized
        self.ai_endpoint = normalized + "/chat/completions"

        self._reset_ai_server_cache()

        models, detected_model_id = self._fetch_models_from_base_url(self.ai_base_url, timeout=0.6)
        self.ai_available_models = models

        if models:
            self.ai_model_id = detected_model_id if detected_model_id in models else models[0]
            self.status_bar.showMessage(self._tr("msg_lm_found_url", self.ai_model_id, normalized))
        else:
            self.ai_model_id = ""
            self.status_bar.showMessage(self._tr("msg_lm_no_models_url", normalized))

        self._rebuild_ai_model_submenu()
        self.refresh_models_menu_status()

    def _fetch_server_active_model_id(self, base_url: str, timeout: float = 0.6) -> str:
        _, active = self._fetch_models_from_base_url(base_url, timeout=timeout)
        return active

    def clear_manual_ai_base_url(self):
        self.ai_manual_base_url = ""
        self.ai_mode = "auto"
        self.ai_base_url = None
        self.ai_available_models = []
        self.ai_model_id = ""
        self._reset_ai_server_cache()

        self._rebuild_ai_model_submenu()
        self._update_ai_model_ui()
        self.refresh_models_menu_status()

    def scan_ai_models_now(self):
        self._ai_server_cache = {
            "ts": 0.0,
            "base_url": None,
            "model_id": None,
        }

        models = []
        detected_model_id = ""

        if self.ai_manual_base_url:
            self.ai_mode = "manual"
            self.ai_base_url = self._normalize_ai_base_url(self.ai_manual_base_url)
            self.ai_endpoint = self.ai_base_url + "/chat/completions"
            models, detected_model_id = self._fetch_models_from_base_url(self.ai_base_url, timeout=0.6)
        else:
            self.ai_mode = "auto"
            base_url, detected_model_id = self._detect_local_openai_server(force=True)
            self.ai_base_url = base_url
            if base_url:
                self.ai_endpoint = base_url + "/chat/completions"
                models, active = self._fetch_models_from_base_url(base_url, timeout=0.35)
                if active:
                    detected_model_id = active

        self.ai_available_models = models

        if models:
            if detected_model_id and detected_model_id in models:
                self.ai_model_id = detected_model_id
            else:
                self.ai_model_id = models[0]
            self.status_bar.showMessage(self._tr("msg_lm_found", self.ai_model_id))
        else:
            self.ai_model_id = ""
            if self.ai_mode == "auto":
                self.ai_base_url = None
            self.status_bar.showMessage(self._tr("msg_lm_server_not_found"))

        self._rebuild_ai_model_submenu()
        self.refresh_models_menu_status()

    def _rebuild_ai_model_submenu(self):
        if not hasattr(self, "ai_models_submenu"):
            return

        self.ai_models_submenu.clear()
        self.ai_model_actions = {}

        if self.ai_model_group is None:
            self.ai_model_group = QActionGroup(self)
            self.ai_model_group.setExclusive(True)

        for act in list(self.ai_model_group.actions()):
            self.ai_model_group.removeAction(act)

        if not self.ai_available_models:
            empty_act = QAction(self._tr("no_models_scan"), self)
            empty_act.setEnabled(False)
            self.ai_models_submenu.addAction(empty_act)
        else:
            for model_id in self.ai_available_models:
                act = QAction(model_id, self)
                act.setCheckable(True)
                act.setChecked(model_id == self.ai_model_id)
                act.triggered.connect(lambda checked, mid=model_id: self._set_ai_model(mid))
                self.ai_model_group.addAction(act)
                self.ai_models_submenu.addAction(act)
                self.ai_model_actions[model_id] = act

        self.ai_models_submenu.addSeparator()
        self.act_clear_ai_model = QAction(self._tr("act_clear_ai_model"), self)
        self.act_clear_ai_model.triggered.connect(self.clear_ai_model)
        self.act_clear_ai_model.setEnabled(bool(self.ai_model_id or self.ai_available_models))
        self.ai_models_submenu.addAction(self.act_clear_ai_model)

    def choose_ai_model_dialog(self):
        models = self._fetch_loaded_llm_models(force=True)
        if not models:
            QMessageBox.warning(self, self._tr("warn_title"), "Es wurden keine geladenen LM-Modelle gefunden.")
            return

        current = self.ai_model_id if self.ai_model_id in models else models[0]

        selected, ok = QInputDialog.getItem(
            self,
            "LM-Model ändern",
            "Zu nutzendes LM-Model auswählen:",
            models,
            max(0, models.index(current)),
            False
        )
        if not ok or not selected:
            return

        self._set_ai_model(selected)
        self.refresh_models_menu_status()

    def _current_ai_mode_label(self) -> str:
        if not (self.ai_model_id or "").strip():
            return "-"
        return "Manuell" if self.ai_mode == "manual" else "Auto"

    def _set_ai_model(self, model_id: str):
        self.ai_model_id = (model_id or "").strip()

        for mid, act in self.ai_model_actions.items():
            act.setChecked(mid == self.ai_model_id)

        self._rebuild_ai_model_submenu()
        self._update_ai_model_ui()
        self.refresh_models_menu_status()

        if self.ai_model_id:
            self.status_bar.showMessage(self._tr("msg_ai_model_set", self.ai_model_id))
        else:
            self.status_bar.showMessage(self._tr("msg_ai_model_choice_cleared"))

    def clear_ai_model(self):
        self.ai_model_id = ""
        self.ai_available_models = []

        # alles zurücksetzen
        self.ai_base_url = None
        self.ai_manual_base_url = ""
        self.ai_endpoint = "http://127.0.0.1:1234/v1/chat/completions"
        self.ai_mode = ""

        self._ai_server_cache = {
            "ts": 0.0,
            "base_url": None,
            "model_id": None,
        }

        self._rebuild_ai_model_submenu()
        self._update_ai_model_ui()
        self.refresh_models_menu_status()

        self.status_bar.showMessage(self._tr("msg_ai_model_removed"))

    def _swap_lines(self, task: TaskItem, row_a: int, row_b: int):
        if not task or not task.results:
            return

        _, _, _, recs = task.results
        if not (0 <= row_a < len(recs)) or not (0 <= row_b < len(recs)):
            return

        if row_a == row_b:
            self._sync_ui_after_recs_change(task, keep_row=row_a)
            return

        order = list(range(len(recs)))
        order[row_a], order[row_b] = order[row_b], order[row_a]

        self._reorder_lines_keep_box_slots(task, order, keep_row=row_b)

    def _swap_line_with_dialog(self, task: TaskItem, row: int):
        if not task or not task.results:
            return

        _, _, _, recs = task.results
        if not (0 <= row < len(recs)):
            return

        target, ok = QInputDialog.getInt(
            self,
            self._tr("dlg_swap_title"),
            self._tr("dlg_swap_label"),
            row + 1,  # value
            1,  # minValue
            max(1, len(recs)),  # maxValue
            1  # step
        )
        if not ok:
            return

        self._swap_lines(task, row, target - 1)

    def _project_base_dir(self) -> str:
        if self.project_file_path:
            return os.path.dirname(os.path.abspath(self.project_file_path))
        return os.getcwd()

    def _make_hybrid_paths_for_task(self, task: TaskItem) -> tuple[str, str]:
        abs_path = os.path.abspath(task.path)
        rel_path = ""

        try:
            base_dir = self._project_base_dir()
            rel_candidate = os.path.relpath(abs_path, base_dir)

            # nur sinnvoll, wenn wirklich relativ und nicht auf anderes Laufwerk springt
            if not os.path.isabs(rel_candidate) and not rel_candidate.startswith(".."):
                rel_path = rel_candidate
            else:
                # auch '../...' ist als relativer Pfad technisch gültig,
                # wenn du das erlauben willst, nimm stattdessen einfach:
                # rel_path = rel_candidate
                rel_path = rel_candidate
        except Exception:
            rel_path = os.path.basename(abs_path)

        return abs_path, rel_path

    def _resolve_hybrid_task_path(self, data: dict) -> str:
        absolute_path = str(data.get("absolute_path", "")).strip()
        relative_path = str(data.get("relative_path", "")).strip()
        legacy_path = str(data.get("path", "")).strip()

        # 1) absoluter Pfad
        if absolute_path and os.path.exists(absolute_path):
            return os.path.abspath(absolute_path)

        # 2) relativer Pfad zum Projektordner
        if relative_path:
            candidate = os.path.normpath(os.path.join(self._project_base_dir(), relative_path))
            if os.path.exists(candidate):
                return candidate

        # 3) alter path-Eintrag als Fallback
        if legacy_path and os.path.exists(legacy_path):
            return os.path.abspath(legacy_path)

        # 4) best effort: absoluten Pfad zurückgeben, sonst relativen Kandidaten, sonst legacy
        if absolute_path:
            return os.path.abspath(absolute_path)

        if relative_path:
            return os.path.normpath(os.path.join(self._project_base_dir(), relative_path))

        return legacy_path

    def _recordview_to_dict(self, rv: RecordView) -> dict:
        return {
            "idx": int(rv.idx),
            "text": rv.text,
            "bbox": list(rv.bbox) if rv.bbox else None,
        }

    def _recordview_from_dict(self, data: dict) -> RecordView:
        bbox = data.get("bbox")
        if bbox is not None:
            bbox = tuple(int(x) for x in bbox)
        return RecordView(
            idx=int(data.get("idx", 0)),
            text=str(data.get("text", "")),
            bbox=bbox
        )

    def _task_to_dict(self, task: TaskItem) -> dict:
        abs_path, rel_path = self._make_hybrid_paths_for_task(task)

        payload = {
            "path": abs_path,  # Legacy/Fallback
            "absolute_path": abs_path,  # neu
            "relative_path": rel_path,  # neu: echter relativer Pfad
            "display_name": task.display_name,
            "status": int(task.status),
            "edited": bool(task.edited),
            "source_kind": task.source_kind,
            "undo_stack": [],
            "redo_stack": [],
            "results": None,
        }

        if task.results:
            text, kr_records, im, recs = task.results
            payload["results"] = {"text": text, "records": [self._recordview_to_dict(rv) for rv in recs], }

        return payload

    def _task_from_dict(self, data: dict) -> TaskItem:
        resolved_path = self._resolve_hybrid_task_path(data)

        display_name_default = os.path.basename(resolved_path) if resolved_path else os.path.basename(
            str(data.get("path", "")))
        rel_default = str(data.get("relative_path", "")).strip()

        task = TaskItem(
            path=resolved_path,
            display_name=str(data.get("display_name", display_name_default)),
            status=int(data.get("status", STATUS_WAITING)),
            edited=False,
            source_kind=str(data.get("source_kind", "image")),
            relative_path=rel_default,
        )

        results = data.get("results")
        if results:
            recs = [self._recordview_from_dict(x) for x in results.get("records", [])]
            text = str(results.get("text", "\n".join(rv.text for rv in recs).strip()))

            gray_im = None
            if os.path.exists(task.path):
                try:
                    gray_im = _load_image_gray(task.path)
                except Exception:
                    gray_im = None

            task.results = (text, [], gray_im, recs)

        return task

    def _project_to_dict(self) -> dict:
        current_row = self.queue_table.currentRow()

        return {
            "version": 2,
            "project_base_dir": self._project_base_dir(),
            "settings": {
                "language": self.current_lang,
                "reading_direction": self.reading_direction,
                "device": self.device_str,
                "show_overlay": self.show_overlay,
                "theme": self.current_theme,
                "model_path": self.model_path,
                "seg_model_path": self.seg_model_path,
                "current_export_dir": self.current_export_dir,
                "ai_model_id": self.ai_model_id,
                "current_row": current_row,
                "whisper_models_base_dir": self.whisper_models_base_dir,
                "whisper_model_path": self.whisper_model_path,
                "whisper_selected_input_device": self.whisper_selected_input_device,
                "whisper_selected_input_device_label": self.whisper_selected_input_device_label,
                "last_rec_model_dir": self.last_rec_model_dir,
                "last_seg_model_dir": self.last_seg_model_dir,
            },
            "queue_items": [self._task_to_dict(task) for task in self.queue_items],
        }

    def _remap_missing_project_files(self):
        missing = [t for t in self.queue_items if not os.path.exists(t.path)]
        if not missing:
            return

        answer = QMessageBox.question(
            self,
            self._tr("warn_title"),
            "Einige Originaldateien wurden nicht gefunden.\n\n"
            "Möchten Sie einen neuen Ordner auswählen, damit die Dateien neu zugeordnet werden?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if answer != QMessageBox.Yes:
            return

        new_base_dir = QFileDialog.getExistingDirectory(
            self,
            "Neuen Basisordner für Originaldateien wählen",
            self.current_export_dir or os.getcwd()
        )
        if not new_base_dir:
            return

        unresolved = []

        for task in missing:
            candidates = []

            rel = (task.relative_path or "").strip()
            old_path = (task.path or "").strip()

            # 1) echter relativer Pfad innerhalb des neuen Basisordners
            if rel:
                candidates.append(os.path.normpath(os.path.join(new_base_dir, rel)))

            # 2) nur Dateiname als Fallback
            if old_path:
                candidates.append(os.path.normpath(os.path.join(new_base_dir, os.path.basename(old_path))))

            # doppelte Kandidaten vermeiden
            seen = set()
            final_candidates = []
            for c in candidates:
                norm = os.path.normpath(c)
                if norm not in seen:
                    seen.add(norm)
                    final_candidates.append(norm)

            found = None
            for c in final_candidates:
                if os.path.exists(c):
                    found = c
                    break

            if found:
                task.path = found
                if not task.relative_path:
                    task.relative_path = os.path.basename(found)
            else:
                unresolved.append(task.display_name)

        if unresolved:
            QMessageBox.warning(
                self,
                self._tr("warn_title"),
                "Einige Dateien konnten weiterhin nicht gefunden werden:\n\n" + "\n".join(unresolved[:20])
            )

    def _load_project_dict(self, data: dict):
        progress = QProgressDialog("Projekt wird geladen...", None, 0, 100, self)
        progress.setWindowTitle(self._tr("dlg_project_loading_title"))
        progress.setWindowModality(Qt.ApplicationModal)
        progress.setCancelButton(None)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()
        self._process_ui()

        try:
            self.clear_queue()
            progress.setLabelText("Einstellungen werden wiederhergestellt...")
            progress.setValue(5)
            self._process_ui()

            settings = data.get("settings", {})
            self.current_lang = settings.get("language", self.current_lang)
            self.reading_direction = int(settings.get("reading_direction", self.reading_direction))
            self.device_str = settings.get("device", self.device_str)
            self.show_overlay = bool(settings.get("show_overlay", self.show_overlay))
            self.current_theme = settings.get("theme", self.current_theme)
            self.model_path = settings.get("model_path", self.model_path)
            self.seg_model_path = settings.get("seg_model_path", self.seg_model_path)
            self.current_export_dir = settings.get("current_export_dir", self.current_export_dir)
            self.ai_model_id = settings.get("ai_model_id", self.ai_model_id)
            self.last_rec_model_dir = settings.get("last_rec_model_dir", self.last_rec_model_dir)
            self.last_seg_model_dir = settings.get("last_seg_model_dir", self.last_seg_model_dir)

            self.whisper_models_base_dir = self._default_whisper_base_dir()
            self.whisper_model_path = self._default_whisper_model_dir()
            if not os.path.isfile(os.path.join(self.whisper_model_path, "model.bin")):
                self.whisper_model_path = ""
            self.whisper_model_name = os.path.basename(self.whisper_model_path) if self.whisper_model_path else ""
            self.whisper_model_loaded = bool(self.whisper_model_path)
            self.whisper_selected_input_device = settings.get("whisper_selected_input_device",
                                                              self.whisper_selected_input_device)
            self.whisper_selected_input_device_label = settings.get(
                "whisper_selected_input_device_label",
                self.whisper_selected_input_device_label
            )

            self._scan_whisper_models()
            self._rebuild_whisper_model_submenu()
            self._update_whisper_menu_status()

            queue_data = data.get("queue_items", [])
            self.queue_items = []

            total = max(1, len(queue_data))

            progress.setLabelText("Projektdaten werden eingelesen...")
            progress.setValue(10)
            self._process_ui()

            for idx, task_data in enumerate(queue_data, start=1):
                task = self._task_from_dict(task_data)
                self.queue_items.append(task)

                pct = 10 + int((idx / total) * 35)
                progress.setLabelText(f"Projektobjekte werden eingelesen... ({idx}/{total})")
                progress.setValue(pct)
                self._process_ui()

            progress.setLabelText("Dateipfade werden geprüft...")
            progress.setValue(50)
            self._process_ui()

            self._remap_missing_project_files()

            progress.setLabelText("Wartebereich wird aufgebaut...")
            self._process_ui()

            for idx, task in enumerate(self.queue_items, start=1):
                row = self.queue_table.rowCount()
                self.queue_table.insertRow(row)

                num_item = QTableWidgetItem(str(row + 1))
                num_item.setTextAlignment(Qt.AlignCenter)
                num_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

                name_item = QTableWidgetItem(task.display_name)
                name_item.setData(Qt.UserRole, task.path)
                name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)

                status_item = QTableWidgetItem()
                status_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

                self.queue_table.setItem(row, QUEUE_COL_NUM, num_item)
                self.queue_table.setCellWidget(row, QUEUE_COL_CHECK, self._make_queue_checkbox_widget(False))
                self.queue_table.setItem(row, QUEUE_COL_FILE, name_item)
                self.queue_table.setItem(row, QUEUE_COL_STATUS, status_item)

                self._update_queue_row(task.path)

                pct = 50 + int((idx / total) * 35)
                progress.setLabelText(f"Wartebereich wird aufgebaut... ({idx}/{total})")
                progress.setValue(pct)
                self._process_ui()

            progress.setLabelText("Oberfläche wird aktualisiert...")
            progress.setValue(90)
            self._process_ui()

            self.apply_theme(self.current_theme)
            self.retranslate_ui()

            current_row = int(settings.get("current_row", 0))
            if self.queue_table.rowCount() > 0:
                current_row = max(0, min(self.queue_table.rowCount() - 1, current_row))
                self.queue_table.selectRow(current_row)

                path = self.queue_table.item(current_row, QUEUE_COL_FILE).data(Qt.UserRole)
                task = next((i for i in self.queue_items if i.path == path), None)

                if task:
                    if os.path.exists(path):
                        if task.status == STATUS_DONE and task.results:
                            self.load_results(path)
                        else:
                            self.preview_image(path)
                    else:
                        QMessageBox.warning(
                            self,
                            self._tr("warn_title"),
                            self._tr("warn_project_file_missing", path)
                        )

            self._refresh_queue_numbers()
            self._fit_queue_columns_exact()
            self._update_queue_hint()
            self._update_models_menu_labels()
            self._update_model_clear_buttons()

            progress.setLabelText("Projekt abgeschlossen.")
            progress.setValue(100)
            self._process_ui()

        finally:
            progress.close()

    def save_project_as(self):
        base_dir = self.current_export_dir or os.getcwd()
        path, _ = QFileDialog.getSaveFileName(
            self,
            self._tr("menu_project_save_as"),
            os.path.join(base_dir, "projekt.json"),
            self._tr("dlg_filter_project")
        )
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"

        self.project_file_path = path
        self.save_project()

    def save_project(self):
        if not self.project_file_path:
            self.save_project_as()
            return

        try:
            data = self._project_to_dict()
            with open(self.project_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.status_bar.showMessage(self._tr("msg_project_saved", os.path.basename(self.project_file_path)))

            QMessageBox.information(
                self,
                self._tr("info_title"),
                self._tr("msg_project_saved", os.path.basename(self.project_file_path))
            )

        except Exception as e:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_project_save_failed", str(e)))

    def load_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            self._tr("menu_project_load"),
            self.current_export_dir or os.getcwd(),
            self._tr("dlg_filter_project")
        )
        if not path:
            return

        self.load_project_from_path(path)

    def load_project_from_path(self, path: str):
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.project_file_path = path
            self._load_project_dict(data)
            self.status_bar.showMessage(self._tr("msg_project_loaded", os.path.basename(path)))
        except Exception as e:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_project_load_failed", str(e)))

    def _queue_check_col_width(self) -> int:
        return 34

    def _make_queue_checkbox_widget(self, checked: bool = False) -> QWidget:
        wrap = QWidget()
        lay = QHBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.setAlignment(Qt.AlignCenter)

        cb = QCheckBox(wrap)
        cb.setChecked(bool(checked))
        cb.stateChanged.connect(lambda _state: self._update_queue_check_header())

        lay.addWidget(cb)
        wrap.setStyleSheet("background: transparent;")
        return wrap

    def _queue_checkbox_at_row(self, row: int) -> Optional[QCheckBox]:
        wrap = self.queue_table.cellWidget(row, QUEUE_COL_CHECK)
        if wrap is None:
            return None

        cb = wrap.findChild(QCheckBox)
        return cb

    def _refresh_queue_numbers(self):
        for row in range(self.queue_table.rowCount()):
            item = self.queue_table.item(row, QUEUE_COL_NUM)
            if item is None:
                item = QTableWidgetItem()
                item.setTextAlignment(Qt.AlignCenter)
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.queue_table.setItem(row, QUEUE_COL_NUM, item)
            item.setText(str(row + 1))

    def on_queue_current_cell_changed(self, currentRow, currentColumn, previousRow, previousColumn):
        if currentRow < 0:
            return
        item = self.queue_table.item(currentRow, QUEUE_COL_FILE)
        if not item:
            return
        path = item.data(Qt.UserRole)
        if path:
            self.preview_image(path)

    def _checked_queue_rows(self) -> List[int]:
        rows = []
        for row in range(self.queue_table.rowCount()):
            cb = self._queue_checkbox_at_row(row)
            if cb is not None and cb.isChecked():
                rows.append(row)
        return rows

    def _set_all_queue_checkmarks(self, checked: bool):
        for row in range(self.queue_table.rowCount()):
            cb = self._queue_checkbox_at_row(row)
            if cb is not None:
                cb.blockSignals(True)
                cb.setChecked(bool(checked))
                cb.blockSignals(False)

        self._update_queue_check_header()

    def _toggle_all_queue_checkmarks(self):
        total_rows = self.queue_table.rowCount()
        if total_rows == 0:
            self._update_queue_check_header()
            return

        checked_rows = len(self._checked_queue_rows())
        should_check_all = checked_rows != total_rows
        self._set_all_queue_checkmarks(should_check_all)

    def _checked_queue_tasks(self) -> List[TaskItem]:
        out = []
        for row in self._checked_queue_rows():
            file_item = self.queue_table.item(row, QUEUE_COL_FILE)
            if not file_item:
                continue

            path = file_item.data(Qt.UserRole)
            task = next((t for t in self.queue_items if t.path == path), None)
            if task:
                out.append(task)

        return out

    def _selected_queue_tasks(self) -> List[TaskItem]:
        rows = self.queue_table.selectionModel().selectedRows()
        if not rows:
            return []

        paths = []
        for model_index in rows:
            item = self.queue_table.item(model_index.row(), QUEUE_COL_FILE)
            if item:
                p = item.data(Qt.UserRole)
                if p:
                    paths.append(p)

        out = []
        for p in paths:
            task = next((i for i in self.queue_items if i.path == p), None)
            if task:
                out.append(task)
        return out

    def _normalize_toolbar_button_sizes(self):
        target_height = 34
        clear_width = 28

        # Alle Toolbar-QToolButtons angleichen
        for b in self.toolbar.findChildren(QToolButton):
            b.setMinimumHeight(target_height)
            b.setMaximumHeight(target_height)
            b.setMinimumWidth(0)
            b.setMaximumWidth(16777215)

        # Hauptbuttons angleichen
        for btn_name in (
                "btn_rec_model",
                "btn_seg_model",
                "btn_ai_model",
                "btn_theme_toggle",
                "btn_lang_menu",
        ):
            btn = getattr(self, btn_name, None)
            if btn is not None:
                btn.setMinimumHeight(target_height)
                btn.setMaximumHeight(target_height)
                btn.setMinimumWidth(0)
                btn.setMaximumWidth(16777215)

        if hasattr(self, "btn_theme_toggle"):
            self.btn_theme_toggle.setFixedWidth(target_height + 8)

    def _icon_fg_color(self) -> QColor:
        return QColor("#ffffff") if self.current_theme == "dark" else QColor("#000000")

    def _tinted_theme_or_standard_icon(
            self,
            theme_name: str,
            std_icon,
            size: Optional[QSize] = None
    ):
        icon = QIcon.fromTheme(theme_name)
        if icon.isNull():
            icon = self.style().standardIcon(std_icon)

        if icon.isNull():
            return icon

        if size is None:
            if hasattr(self, "toolbar"):
                size = self.toolbar.iconSize()
            else:
                size = QSize(16, 16)

        src = icon.pixmap(size)
        if src.isNull():
            return icon

        tinted = QPixmap(src.size())
        tinted.fill(Qt.transparent)

        painter = QPainter(tinted)
        painter.drawPixmap(0, 0, src)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(tinted.rect(), self._icon_fg_color())
        painter.end()

        return QIcon(tinted)

    def _themed_or_standard_icon(self, theme_name: str, std_icon):
        icon = QIcon.fromTheme(theme_name)
        if icon.isNull():
            icon = self.style().standardIcon(std_icon)
        return icon

    def _set_primary_toolbar_icons(self):
        if hasattr(self, "act_add"):
            self.act_add.setIcon(
                self._themed_or_standard_icon("document-open", QStyle.SP_DialogOpenButton)
            )

        if hasattr(self, "act_project_load_toolbar"):
            self.act_project_load_toolbar.setIcon(
                self._themed_or_standard_icon("document-open", QStyle.SP_DialogOpenButton)
            )

        if hasattr(self, "act_image_edit"):
            self.act_image_edit.setIcon(
                self._tinted_theme_or_standard_icon("edit-cut", QStyle.SP_FileDialogDetailedView)
            )

        if hasattr(self, "act_play"):
            self.act_play.setIcon(
                self._tinted_theme_or_standard_icon("media-playback-start", QStyle.SP_MediaPlay)
            )

        if hasattr(self, "act_stop"):
            self.act_stop.setIcon(
                self._tinted_theme_or_standard_icon("media-playback-stop", QStyle.SP_MediaStop)
            )

        if hasattr(self, "btn_rec_model"):
            self.btn_rec_model.setIcon(
                self._themed_or_standard_icon("document-open", QStyle.SP_DialogOpenButton)
            )

        if hasattr(self, "btn_seg_model"):
            self.btn_seg_model.setIcon(
                self._themed_or_standard_icon("document-open", QStyle.SP_DialogOpenButton)
            )

    def _set_secondary_button_icons(self):
        def themed_or_standard(theme_name: str, std_icon):
            icon = QIcon.fromTheme(theme_name)
            if icon.isNull():
                icon = self.style().standardIcon(std_icon)
            return icon

        if hasattr(self, "btn_import_lines"):
            self.btn_import_lines.setIcon(
                themed_or_standard("document-import", QStyle.SP_DialogOpenButton)
            )

        if hasattr(self, "btn_voice_fill"):
            self.btn_voice_fill.setIcon(
                self._tinted_theme_or_standard_icon("audio-input-microphone", QStyle.SP_MediaVolume)
            )

        if hasattr(self, "btn_ai_revise_bottom"):
            self.btn_ai_revise_bottom.setIcon(
                themed_or_standard("preferences-system", QStyle.SP_ComputerIcon)
            )

        if hasattr(self, "btn_line_search"):
            self.btn_line_search.setIcon(
                self._tinted_theme_or_standard_icon("system-search", QStyle.SP_FileDialogContentsView)
            )

        if hasattr(self, "btn_clear_queue"):
            self.btn_clear_queue.setIcon(
                self._tinted_theme_or_standard_icon("edit-clear", QStyle.SP_DialogResetButton)
            )

        if hasattr(self, "btn_toggle_log"):
            self.btn_toggle_log.setIcon(
                themed_or_standard("text-x-log", QStyle.SP_FileDialogDetailedView)
            )

    def _scan_kraken_models(self):
        self.kraken_rec_models = []
        self.kraken_seg_models = []
        self.kraken_unknown_models = []

        model_dir = KRAKEN_MODELS_DIR
        if not os.path.isdir(model_dir):
            return

        candidates = []
        seen_names = set()

        for root, _dirs, files in os.walk(model_dir):
            for name in files:
                ext = os.path.splitext(name)[1].lower()

                # nur noch .mlmodel
                if ext != ".mlmodel":
                    continue

                full = os.path.join(root, name)

                # Dubletten über Dateinamen rausfiltern
                key = name.lower()
                if key in seen_names:
                    continue
                seen_names.add(key)

                candidates.append(full)

        for full in sorted(candidates, key=lambda p: os.path.basename(p).lower()):
            kind = self._classify_kraken_model_file(full)

            if kind == "rec":
                self.kraken_rec_models.append(full)
            elif kind == "seg":
                self.kraken_seg_models.append(full)
            else:
                self.kraken_unknown_models.append(full)

    def _load_default_segmentation_model(self):
        if self.seg_model_path and os.path.exists(self.seg_model_path):
            return

        if not self.kraken_seg_models:
            return

        preferred = next(
            (p for p in self.kraken_seg_models if "blla" in os.path.basename(p).lower()),
            self.kraken_seg_models[0]
        )

        self.seg_model_path = preferred

    def _model_type_to_text(self, model_type) -> str:
        if isinstance(model_type, (list, tuple, set)):
            return " ".join(str(x) for x in model_type if x).strip().lower()
        return str(model_type or "").strip().lower()

    def _classify_kraken_model_file(self, model_path: str) -> str:
        """
        Gibt zurück:
            "rec"      -> Recognition-Modell
            "seg"      -> Segmentierungs-Modell
            "unknown"  -> nicht sicher bestimmbar
        """
        # 1) Primär: echtes Kraken-Metadatum lesen
        try:
            nn = vgsl.TorchVGSLModel.load_model(model_path)
            model_type = self._model_type_to_text(getattr(nn, "model_type", ""))

            if "recognition" in model_type:
                return "rec"

            if any(x in model_type for x in ("segmentation", "baseline", "region")):
                return "seg"
        except Exception:
            pass

        # 2) Fallback nur für alte / unklare Modelle
        lname = os.path.basename(model_path).lower()

        if any(x in lname for x in ("blla", "seg", "segment", "baseline", "region")):
            return "seg"

        if any(x in lname for x in ("rec", "recognition", "ocr", "htr", "handwriting", "print")):
            return "rec"

        return "unknown"

    def _set_scanned_rec_model(self, model_path: str):
        if not model_path or not os.path.exists(model_path):
            return

        self.model_path = model_path
        self.last_rec_model_dir = os.path.dirname(model_path)
        self.settings.setValue("paths/last_rec_model_dir", self.last_rec_model_dir)

        self.btn_rec_model.setText(self._tr("btn_rec_model_value", os.path.basename(model_path)))
        self.status_bar.showMessage(self._tr("msg_loaded_rec", os.path.basename(model_path)))

        self._update_models_menu_labels()
        self._update_model_clear_buttons()

    def _set_scanned_seg_model(self, model_path: str):
        if not model_path or not os.path.exists(model_path):
            return

        self.seg_model_path = model_path
        self.last_seg_model_dir = os.path.dirname(model_path)
        self.settings.setValue("paths/last_seg_model_dir", self.last_seg_model_dir)

        self.btn_seg_model.setText(self._tr("btn_seg_model_value", os.path.basename(model_path)))
        self.status_bar.showMessage(self._tr("msg_loaded_seg", os.path.basename(model_path)))

        self._update_models_menu_labels()
        self._update_model_clear_buttons()

    def _rebuild_kraken_models_submenu(self):
        if not hasattr(self, "kraken_models_submenu"):
            return

        self.kraken_models_submenu.clear()

        has_any = False

        if self.kraken_rec_models:
            header_rec = QAction(self._tr("header_rec_models"), self)
            header_rec.setEnabled(False)
            self.kraken_models_submenu.addAction(header_rec)

            for model_path in self.kraken_rec_models:
                name = os.path.basename(model_path)
                act = QAction(name, self)
                act.setCheckable(True)
                act.setChecked(os.path.abspath(model_path) == os.path.abspath(self.model_path or ""))
                act.triggered.connect(lambda checked, mp=model_path: self._set_scanned_rec_model(mp))
                self.kraken_models_submenu.addAction(act)

            has_any = True

        if self.kraken_seg_models:
            if has_any:
                self.kraken_models_submenu.addSeparator()

            header_seg = QAction(self._tr("header_seg_models"), self)
            header_seg.setEnabled(False)
            self.kraken_models_submenu.addAction(header_seg)

            for model_path in self.kraken_seg_models:
                name = os.path.basename(model_path)
                act = QAction(name, self)
                act.setCheckable(True)
                act.setChecked(os.path.abspath(model_path) == os.path.abspath(self.seg_model_path or ""))
                act.triggered.connect(lambda checked, mp=model_path: self._set_scanned_seg_model(mp))
                self.kraken_models_submenu.addAction(act)

            has_any = True

        if not has_any:
            empty_act = QAction(self._tr("no_models_scan"), self)
            empty_act.setEnabled(False)
            self.kraken_models_submenu.addAction(empty_act)

        self.kraken_models_submenu.addSeparator()
        self.kraken_models_submenu.addAction(self.act_clear_rec)
        self.kraken_models_submenu.addAction(self.act_clear_seg)

    def _update_kraken_menu_status(self):
        rec_name = os.path.basename(self.model_path) if self.model_path else "-"
        seg_name = os.path.basename(self.seg_model_path) if self.seg_model_path else "-"

        if hasattr(self, "act_rec_status"):
            self.act_rec_status.setText(self._tr("status_rec_model", rec_name))

        if hasattr(self, "act_seg_status"):
            self.act_seg_status.setText(self._tr("status_seg_model", seg_name))

    def choose_rec_model_from_scanned(self):
        if not getattr(self, "kraken_rec_models", None):
            QMessageBox.warning(self, self._tr("warn_title"), "Keine Recognition-Modelle gefunden.")
            return

        names = [os.path.basename(p) for p in self.kraken_rec_models]
        current_name = os.path.basename(self.model_path) if self.model_path else names[0]

        selected, ok = QInputDialog.getItem(
            self,
            self._tr("dlg_choose_rec"),
            "Recognition-Modell auswählen:",
            names,
            max(0, names.index(current_name)) if current_name in names else 0,
            False
        )
        if not ok or not selected:
            return

        for p in self.kraken_rec_models:
            if os.path.basename(p) == selected:
                self.model_path = p
                break

        self.btn_rec_model.setText(self._tr("btn_rec_model_value", os.path.basename(self.model_path)))
        self._update_models_menu_labels()
        self._update_model_clear_buttons()

    def _detect_local_openai_server(self, force: bool = False) -> Tuple[Optional[str], Optional[str]]:
        now = time.monotonic()

        if not force:
            age = now - float(self._ai_server_cache.get("ts", 0.0))
            if age < self._ai_server_cache_ttl:
                return self._ai_server_cache.get("base_url"), self._ai_server_cache.get("model_id")

        candidates = [
            "http://127.0.0.1:1234/v1",  # LM Studio
            "http://127.0.0.1:8000/v1",  # vLLM
            "http://127.0.0.1:8080/v1",
        ]

        for base_url in candidates:
            models, active = self._fetch_models_from_base_url(base_url, timeout=0.35)
            if models:
                self._ai_server_cache = {
                    "ts": now,
                    "base_url": base_url,
                    "model_id": active or models[0],
                }
                return base_url, (active or models[0])

        self._ai_server_cache = {
            "ts": now,
            "base_url": None,
            "model_id": None,
        }
        return None, None

    def _check_ai_server(self) -> bool:
        base_url, model_id = self._detect_local_openai_server()
        return bool(base_url and model_id)

    def _fetch_loaded_llm_name(self) -> str:
        base_url, model_id = self._detect_local_openai_server()
        return model_id or "-"

    def _refresh_ai_endpoint_from_localhost(self, force: bool = False):
        if self.ai_manual_base_url:
            base_url = self._normalize_ai_base_url(self.ai_manual_base_url)
            if not base_url:
                self.ai_base_url = None
                self.ai_mode = "manual"
                self._update_ai_model_ui()
                return
            self.ai_base_url = base_url
            self.ai_endpoint = base_url + "/chat/completions"
            self.ai_mode = "manual"
            self._update_ai_model_ui()
            return

        base_url, _ = self._detect_local_openai_server(force=force)
        if base_url:
            self.ai_base_url = base_url
            self.ai_endpoint = base_url + "/chat/completions"
        else:
            self.ai_base_url = None

        self.ai_mode = "auto"
        self._update_ai_model_ui()

    def _resolve_ai_model_id(self) -> str:
        self._refresh_ai_endpoint_from_localhost()

        model_id = (self.ai_model_id or "").strip()
        if model_id:
            return model_id

        return ""

    def refresh_models_menu_status(self):
        model_name = self._get_active_ai_model_display()
        mode_label = self._current_ai_mode_label()
        base_url = self.ai_base_url if (self.ai_base_url and self.ai_model_id) else "-"

        if hasattr(self, "act_lm_status"):
            self.act_lm_status.setText(self._tr("lm_status_model_value", model_name))

        if hasattr(self, "act_lm_mode"):
            self.act_lm_mode.setText(self._tr("lm_mode_value", mode_label))

        if hasattr(self, "act_lm_base_url"):
            self.act_lm_base_url.setText(self._tr("lm_server_value", base_url))

        if hasattr(self, "act_clear_manual_lm_url"):
            self.act_clear_manual_lm_url.setEnabled(self.ai_mode == "manual" and bool(self.ai_manual_base_url))

        self._update_ai_model_ui()

    def _fetch_models_from_base_url(self, base_url: str, timeout: float = 0.6) -> Tuple[List[str], str]:
        if not base_url:
            return [], ""

        try:
            req = urllib.request.Request(
                base_url.rstrip("/") + "/models",
                headers={"Authorization": "Bearer local"},
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                data = json.loads(raw)

            models_data = data.get("data", [])
            if not isinstance(models_data, list):
                return [], ""

            out = []
            for m in models_data:
                if not isinstance(m, dict):
                    continue
                mid = str(m.get("id", "")).strip()
                if mid:
                    out.append(mid)

            # Reihenfolge erhalten, Duplikate entfernen
            seen = set()
            uniq = []
            for mid in out:
                if mid not in seen:
                    seen.add(mid)
                    uniq.append(mid)

            active = uniq[0] if uniq else ""
            return uniq, active

        except Exception:
            return [], ""

    # -----------------------------
    # Übersetzung
    # -----------------------------
    def _tr(self, key: str, *args):
        lang = getattr(self, "current_lang", "de")
        txt = TRANSLATIONS.get(lang, TRANSLATIONS["de"]).get(key, key)
        if args:
            return txt.format(*args)
        return txt

    def _detect_system_lang(self) -> str:
        # z. B. "de_DE", "en_US", "fr_FR"
        name = QLocale.system().name().lower()
        if name.startswith("de"):
            return "de"
        if name.startswith("fr"):
            return "fr"
        return "en"

    def _tr_in(self, lang: str, key: str, *args):
        txt = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)
        if args:
            return txt.format(*args)
        return txt

    def _tr_log(self, key: str, *args):
        return self._tr_in(self.log_lang, key, *args)

    def _delete_queue_via_key(self):
        # Löscht selektierte Zeilen und setzt danach die Vorschau zurück
        self.delete_selected_queue_items(reset_preview=True)

    def run_ai_revision_for_selected(self):
        selected = self._selected_queue_tasks()
        if selected:
            items = [it for it in selected if it.status == STATUS_DONE and it.results]
        else:
            items = [it for it in self.queue_items if it.status == STATUS_DONE and it.results]

        if not items:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
            return

        self._run_ai_revision_batch(items)

    def run_ai_revision_for_all(self):
        items = [it for it in self.queue_items if it.status == STATUS_DONE and it.results]
        if not items:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
            return

        self._run_ai_revision_batch(items)

    def on_ai_batch_file_started(self, path: str, current: int, total: int):
        task = next((i for i in self.queue_items if i.path == path), None)
        if task:
            if task.results:
                task.lm_locked_bboxes = [tuple(rv.bbox) if rv.bbox else None for rv in task.results[3]]
            task.status = STATUS_AI_PROCESSING
            self._update_queue_row(path)

    def _cancel_ai_batch_revision(self):
        if hasattr(self, "ai_batch_worker") and self.ai_batch_worker and self.ai_batch_worker.isRunning():
            self.ai_batch_worker.cancel()

    # -----------------------------
    # Undo Helfer (snapshots)
    # -----------------------------
    @staticmethod
    def _snapshot_recs(recs: List[RecordView]) -> List[Tuple[str, Optional[Tuple[int, int, int, int]]]]:
        return [(rv.text, rv.bbox) for rv in recs]

    @staticmethod
    def _restore_recs(snapshot: List[Tuple[str, Optional[Tuple[int, int, int, int]]]]) -> List[RecordView]:
        recs: List[RecordView] = []
        for i, (t, bb) in enumerate(snapshot):
            recs.append(RecordView(i, t, bb))
        return recs

    def _push_undo(self, task: TaskItem):
        if not task.results:
            return
        _, _, _, recs = task.results
        sel = self.list_lines.currentRow()
        snap: UndoSnapshot = (self._snapshot_recs(recs), int(sel) if sel is not None else -1)
        task.undo_stack.append(snap)
        if len(task.undo_stack) > 300:
            task.undo_stack.pop(0)
        task.redo_stack.clear()

    def _apply_snapshot(self, task: TaskItem, snap: UndoSnapshot):
        if not task.results:
            return
        text, kr_records, im, _recs = task.results
        state, sel = snap
        recs = self._restore_recs(state)
        new_text = "\n".join([r.text for r in recs]).strip()
        task.results = (new_text, kr_records, im, recs)
        task.edited = True
        keep_row = sel if sel is not None else -1
        if keep_row < 0:
            keep_row = 0 if recs else None
        self._sync_ui_after_recs_change(task, keep_row=keep_row)

    def undo(self):
        task = self._current_task()
        if not task or task.status != STATUS_DONE or not task.results:
            self.status_bar.showMessage(self._tr("undo_nothing"))
            return
        if not task.undo_stack:
            self.status_bar.showMessage(self._tr("undo_nothing"))
            return

        _, _, _, recs = task.results
        cur_sel = self.list_lines.currentRow()
        task.redo_stack.append((self._snapshot_recs(recs), int(cur_sel) if cur_sel is not None else -1))

        snap = task.undo_stack.pop()
        self._apply_snapshot(task, snap)

    def redo(self):
        task = self._current_task()
        if not task or task.status != STATUS_DONE or not task.results:
            self.status_bar.showMessage(self._tr("redo_nothing"))
            return
        if not task.redo_stack:
            self.status_bar.showMessage(self._tr("redo_nothing"))
            return

        _, _, _, recs = task.results
        cur_sel = self.list_lines.currentRow()
        task.undo_stack.append((self._snapshot_recs(recs), int(cur_sel) if cur_sel is not None else -1))

        snap = task.redo_stack.pop()
        self._apply_snapshot(task, snap)

    def set_ai_model_dialog(self):
        model_id, ok = QInputDialog.getText(
            self,
            self._tr("dlg_choose_ai_model"),
            self._tr("dlg_choose_ai_model_label"),
            text=self.ai_model_id
        )
        if not ok:
            return

        self.ai_model_id = model_id.strip()

        self._update_ai_model_ui()

        if self.ai_model_id:
            self.status_bar.showMessage(self._tr("msg_ai_model_set", self.ai_model_id))
        else:
            self.status_bar.showMessage(self._tr("msg_ai_model_id_cleared_auto"))

    def _resolve_faster_whisper_device(self) -> Tuple[str, str]:
        # Wichtig:
        # Whisper immer auf CPU laufen lassen.
        # Sonst kollidiert es mit Kraken-OCR und/oder LM Studio im VRAM.
        return "cpu", "int8"

    def run_voice_line_fill(self):
        task = self._current_task()
        self._persist_live_canvas_bboxes(task)
        if not task or task.status != STATUS_DONE or not task.results:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_voice_need_done"))
            return

        current_row = self.list_lines.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_select_line_first"))
            return

        _, _, _, recs = task.results
        if not (0 <= current_row < len(recs)):
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_selected_line_invalid"))
            return

        if self.voice_worker and self.voice_worker.isRunning():
            return

        if not self.whisper_model_path or not os.path.isdir(self.whisper_model_path):
            QMessageBox.warning(
                self,
                self._tr("warn_title"),
                self._tr("warn_whisper_model_not_loaded")
            )
            return

        if self.whisper_selected_input_device is None:
            devices = self._get_input_audio_devices()
            if devices:
                self.whisper_selected_input_device = devices[0]["index"]
                self.whisper_selected_input_device_label = devices[0]["label"]
                self._update_whisper_menu_status()
            else:
                QMessageBox.warning(
                    self,
                    self._tr("warn_title"),
                    self._tr("warn_no_microphone_available")
                )
                return

        if self.voice_record_dialog is not None:
            try:
                self.voice_record_dialog.close()
            except Exception:
                pass
            self.voice_record_dialog = None

        self.voice_record_dialog = VoiceRecordDialog(self._tr, self)
        self.voice_record_dialog.start_requested.connect(self._start_voice_line_fill)
        self.voice_record_dialog.stop_requested.connect(self.stop_voice_line_fill)
        self.voice_record_dialog.cancel_requested.connect(self._cancel_voice_record_dialog)
        self.voice_record_dialog.show()

    def on_voice_progress_changed(self, value: int):
        self._set_progress_idle(value)

    def on_voice_status_changed(self, text: str):
        self.status_bar.showMessage(text)
        if text.startswith("Erkannte Sprache:"):
            self._log(text)

    def stop_voice_line_fill(self):
        if self.voice_worker and self.voice_worker.isRunning():
            self.status_bar.showMessage(self._tr("msg_voice_stopped"))
            self._log(self._tr_log("log_voice_stopping"))

            if self.voice_record_dialog:
                self.voice_record_dialog._recording = False
                self.voice_record_dialog._processing = True
                self.voice_record_dialog.btn_toggle.setText(self._tr("voice_record_start"))
                self.voice_record_dialog.lbl_info.setText(self._tr("voice_record_processing"))
                self.voice_record_dialog._keep_start_button_primary()

            self._set_progress_idle(0)
            self.voice_worker.stop()

    def on_voice_line_fill_done(self, path: str, line_index: int, new_text: str):
        task = next((i for i in self.queue_items if i.path == path), None)
        self.voice_worker = None

        if not task or not task.results:
            if self.voice_record_dialog:
                self.voice_record_dialog.close()
                self.voice_record_dialog = None
            return

        text, kr_records, im, recs = task.results

        if not (0 <= line_index < len(recs)):
            if self.voice_record_dialog:
                self.voice_record_dialog.close()
                self.voice_record_dialog = None
            return

        self._push_undo(task)

        new_recs = [
            RecordView(i, recs[i].text, recs[i].bbox)
            for i in range(len(recs))
        ]
        new_recs[line_index].text = str(new_text).strip()

        task.results = (
            "\n".join(rv.text for rv in new_recs).strip(),
            kr_records,
            im,
            new_recs
        )
        task.edited = True
        task.status = STATUS_DONE

        # Nach Whisper-Änderung UI aktualisieren
        self._sync_ui_after_recs_change(task, keep_row=line_index)
        self._update_queue_row(path)

        # Automatisch auf nächste Zeile springen
        next_row = line_index + 1
        if 0 <= next_row < len(new_recs):
            self.list_lines.blockSignals(True)
            self.list_lines.clearSelection()

            self.list_lines.setCurrentRow(next_row)
            next_item = self.list_lines.row_item(next_row)
            if next_item:
                next_item.setSelected(True)

            self.list_lines.blockSignals(False)

            self.canvas.select_indices([next_row], center=True)
            self.list_lines.setFocus()

            # Dialog offen lassen, damit man direkt weiter aufnehmen kann
            if self.voice_record_dialog:
                self.voice_record_dialog.set_recording_state(False)
        else:
            # letzte Zeile erreicht -> Dialog schließen
            if self.voice_record_dialog:
                self.voice_record_dialog.close()
                self.voice_record_dialog = None

        self._set_progress_idle(100)

        self.status_bar.showMessage(self._tr("msg_voice_done"))
        self._log(
            f"Sprachimport abgeschlossen: {os.path.basename(path)} | "
            f"Zeile {line_index + 1} -> {new_text}"
        )

    def on_voice_line_fill_failed(self, path: str, msg: str):
        # Schutz gegen doppelte Ausführung
        if self.voice_worker is None:
            return

        task = next((i for i in self.queue_items if i.path == path), None)
        self.voice_worker = None

        if task:
            task.status = STATUS_DONE if task.results else STATUS_ERROR
            self._update_queue_row(path)

        if self.voice_record_dialog:
            self.voice_record_dialog.close()
            self.voice_record_dialog = None

        self._set_progress_idle(0)

        self.status_bar.showMessage(self._tr("msg_voice_cancelled"))
        self._log(f"Sprachimport Fehler: {os.path.basename(path)} -> {msg}")
        QMessageBox.warning(self, self._tr("warn_title"), msg)

    def run_ai_revision(self):
        checked = self._checked_queue_tasks()
        selected = self._selected_queue_tasks()

        # Priorität: Checkmarks vor Auswahl
        target_tasks = checked if checked else selected

        # Wenn mehrere markiert/selektiert sind -> Batch
        if len(target_tasks) > 1:
            items = [it for it in target_tasks if it.status == STATUS_DONE and it.results]
            if not items:
                QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
                return
            self._run_ai_revision_batch(items)
            return

        # Wenn genau ein markierter/selektierter Eintrag existiert -> diesen nehmen
        if len(target_tasks) == 1:
            task = target_tasks[0]
        else:
            # Fallback: aktuelles Vorschau-Element
            task = self._current_task()
            self._persist_live_canvas_bboxes(task)

        if not task or task.status != STATUS_DONE or not task.results:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
            return

        model_id = self._resolve_ai_model_id()
        if not model_id:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_ai_model"))
            return

        if self.ai_worker and self.ai_worker.isRunning():
            return

        _, _, _, recs = task.results
        if not recs:
            return

        task.lm_locked_bboxes = [tuple(rv.bbox) if rv.bbox else None for rv in recs]

        recs_for_ai = self._current_recs_for_ai(task)
        if not recs_for_ai:
            return

        self.act_ai_revise.setEnabled(True)
        self.status_bar.showMessage(self._tr("msg_ai_started"))
        self._log(self._tr_log("log_ai_started", os.path.basename(task.path)))

        self.ai_progress_dialog = ProgressStatusDialog(self._tr("dlg_ai_title"), self._tr, self)
        self.ai_progress_dialog.set_status(self._tr("dlg_ai_connecting"))
        self.ai_progress_dialog.cancel_requested.connect(self._cancel_ai_revision)
        self.ai_progress_dialog.show()

        self.ai_worker = AIRevisionWorker(
            path=task.path,
            recs=recs_for_ai,
            lm_model=model_id,
            endpoint=self.ai_endpoint,
            enable_thinking=self.ai_enable_thinking,
            source_kind=task.source_kind,
            temperature=self.ai_temperature,
            top_p=self.ai_top_p,
            top_k=self.ai_top_k,
            presence_penalty=self.ai_presence_penalty,
            repetition_penalty=self.ai_repetition_penalty,
            min_p=self.ai_min_p,
            max_tokens=self.ai_max_tokens,
            tr_func=self._tr,
            parent=self
        )

        self.ai_worker.progress_changed.connect(self.ai_progress_dialog.set_progress)
        self.ai_worker.status_changed.connect(self.ai_progress_dialog.set_status)
        self.ai_worker.status_changed.connect(self._log)
        self.ai_worker.finished_revision.connect(self.on_ai_revision_done)
        self.ai_worker.failed_revision.connect(self.on_ai_revision_failed)
        self.ai_worker.start()

    def run_ai_revision_for_single_line(self, row: int):
        task = self._current_task()
        self._persist_live_canvas_bboxes(task)
        if not task or task.status != STATUS_DONE or not task.results:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
            return

        text, kr_records, im, recs = task.results

        if not (0 <= row < len(recs)):
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_invalid_line"))
            return

        model_id = self._resolve_ai_model_id()
        if not model_id:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_ai_model"))
            return

        if self.ai_worker and self.ai_worker.isRunning():
            return

        live_recs = self._current_recs_for_ai(task)

        single_rec = RecordView(
            idx=0,
            text=live_recs[row].text,
            bbox=live_recs[row].bbox
        )

        self._ai_single_line_context = {
            "path": task.path,
            "row": row,
        }

        self.act_ai_revise.setEnabled(False)
        self.status_bar.showMessage(self._tr("msg_ai_single_started", row + 1))
        self._log(self._tr_log("log_ai_single_started", os.path.basename(task.path), row + 1))

        self.ai_progress_dialog = ProgressStatusDialog(self._tr("dlg_ai_single_title"), self._tr, self)
        self.ai_progress_dialog.set_status(self._tr("dlg_ai_single_status", row + 1))
        self.ai_progress_dialog.cancel_requested.connect(self._cancel_ai_revision)
        self.ai_progress_dialog.show()

        self.ai_worker = AIRevisionWorker(
            path=task.path,
            recs=[single_rec],
            lm_model=model_id,
            endpoint=self.ai_endpoint,
            enable_thinking=self.ai_enable_thinking,
            source_kind=task.source_kind,
            temperature=self.ai_temperature,
            top_p=self.ai_top_p,
            top_k=self.ai_top_k,
            presence_penalty=self.ai_presence_penalty,
            repetition_penalty=self.ai_repetition_penalty,
            min_p=self.ai_min_p,
            max_tokens=self.ai_max_tokens,
            tr_func=self._tr,
            parent=self
        )

        self.ai_worker.progress_changed.connect(self.ai_progress_dialog.set_progress)
        self.ai_worker.status_changed.connect(self.ai_progress_dialog.set_status)
        self.ai_worker.status_changed.connect(self._log)
        self.ai_worker.finished_revision.connect(self.on_ai_single_line_revision_done)
        self.ai_worker.failed_revision.connect(self.on_ai_single_line_revision_failed)
        self.ai_worker.start()

    def _run_ai_revision_batch(self, items: List[TaskItem]):
        model_id = self._resolve_ai_model_id()
        if not model_id:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_ai_model"))
            return

        if hasattr(self, "ai_batch_worker") and self.ai_batch_worker and self.ai_batch_worker.isRunning():
            return

        self.act_ai_revise.setEnabled(True)

        self.ai_batch_dialog = ProgressStatusDialog(self._tr("act_ai_revise_all"), self._tr, self)
        self.ai_batch_dialog.set_status(self._tr("dlg_ai_connecting"))
        self.ai_batch_dialog.cancel_requested.connect(self._cancel_ai_batch_revision)
        self.ai_batch_dialog.show()

        self.ai_batch_worker = AIBatchRevisionWorker(
            items=items,
            lm_model=model_id,
            endpoint=self.ai_endpoint,
            enable_thinking=self.ai_enable_thinking,
            temperature=self.ai_temperature,
            top_p=self.ai_top_p,
            top_k=self.ai_top_k,
            presence_penalty=self.ai_presence_penalty,
            repetition_penalty=self.ai_repetition_penalty,
            min_p=self.ai_min_p,
            max_tokens=self.ai_max_tokens,
            tr_func=self._tr,
            parent=self
        )

        self.ai_batch_worker.file_started.connect(self.on_ai_batch_file_started)
        self.ai_batch_worker.status_changed.connect(self.ai_batch_dialog.set_status)
        self.ai_batch_worker.status_changed.connect(self._log)
        self.ai_batch_worker.progress_changed.connect(self.ai_batch_dialog.set_progress)
        self.ai_batch_worker.file_finished.connect(self.on_ai_batch_file_done)
        self.ai_batch_worker.file_failed.connect(self.on_ai_batch_file_failed)
        self.ai_batch_worker.finished_batch.connect(self.on_ai_batch_finished)
        self.ai_batch_worker.start()

    def _cancel_ai_revision(self):
        if self.ai_worker and self.ai_worker.isRunning():
            self.ai_worker.cancel()

    def on_ai_revision_done(self, path: str, revised_lines: list):
        task = next((i for i in self.queue_items if i.path == path), None)
        if not task or not task.results:
            self.act_ai_revise.setEnabled(True)
            if hasattr(self, "ai_progress_dialog") and self.ai_progress_dialog:
                self.ai_progress_dialog.close()
                self.ai_progress_dialog = None
            return

        text, kr_records, im, recs = task.results

        revised_lines = [str(x).strip() for x in revised_lines]

        self._log(
            f"KI Rückgabe für {os.path.basename(path)}: {len(revised_lines)} Zeilen, OCR hatte {len(recs)} Zeilen")

        if len(revised_lines) < len(recs):
            revised_lines.extend([recs[i].text for i in range(len(revised_lines), len(recs))])
        elif len(revised_lines) > len(recs):
            revised_lines = revised_lines[:len(recs)]

        self._log(self._tr_log("log_ai_batch_debug_old_first", recs[0].text if recs else "<leer>"))
        self._log(self._tr_log("log_ai_batch_debug_new_first", revised_lines[0] if revised_lines else "<leer>"))
        self._log(self._tr_log("log_ai_batch_debug_all", revised_lines))

        self._push_undo(task)

        # WICHTIG:
        # Texte ersetzen, aber die AKTUELLEN Boxen aus task.results behalten.
        new_recs = [
            RecordView(i, revised_lines[i], recs[i].bbox)
            for i in range(len(recs))
        ]

        task.results = (
            "\n".join(rv.text for rv in new_recs).strip(),
            kr_records,
            im,
            new_recs
        )
        task.edited = True

        cur = self._current_task()
        if cur and cur.path == path:
            keep_row = self.list_lines.currentRow()
            if keep_row < 0:
                keep_row = 0 if new_recs else None
            self._sync_ui_after_recs_change(task, keep_row=keep_row)
        else:
            self._update_queue_row(path)

        self.act_ai_revise.setEnabled(True)
        self.status_bar.showMessage(self._tr("msg_ai_done"))
        self._log(self._tr_log("log_ai_done", os.path.basename(path)))

        if hasattr(self, "ai_progress_dialog") and self.ai_progress_dialog:
            self.ai_progress_dialog.close()
            self.ai_progress_dialog = None

    def on_ai_single_line_revision_done(self, path: str, revised_lines: list):
        ctx = self._ai_single_line_context or {}
        self._ai_single_line_context = None

        task = next((i for i in self.queue_items if i.path == path), None)
        if not task or not task.results:
            self.act_ai_revise.setEnabled(True)
            if self.ai_progress_dialog:
                self.ai_progress_dialog.close()
                self.ai_progress_dialog = None
            return

        row = int(ctx.get("row", -1))
        text, kr_records, im, recs = task.results

        if not (0 <= row < len(recs)):
            self.act_ai_revise.setEnabled(True)
            if self.ai_progress_dialog:
                self.ai_progress_dialog.close()
                self.ai_progress_dialog = None
            return

        new_text = ""
        if revised_lines:
            new_text = str(revised_lines[0]).strip()

        if not new_text:
            new_text = recs[row].text

        self._push_undo(task)

        new_recs = [
            RecordView(i, recs[i].text, recs[i].bbox)
            for i in range(len(recs))
        ]
        new_recs[row].text = new_text

        task.results = (
            "\n".join(rv.text for rv in new_recs).strip(),
            kr_records,
            im,
            new_recs
        )
        task.edited = True

        cur = self._current_task()
        if cur and cur.path == path:
            self._sync_ui_after_recs_change(task, keep_row=row)
        else:
            self._update_queue_row(path)

        self.act_ai_revise.setEnabled(True)
        self.status_bar.showMessage(self._tr("msg_ai_single_done", row + 1))
        self._log(self._tr_log("log_ai_single_done", os.path.basename(path), row + 1))

        self._close_ai_progress_dialog()

    def on_ai_single_line_revision_failed(self, path: str, msg: str):
        self._ai_single_line_context = None
        self.act_ai_revise.setEnabled(True)

        if "abgebrochen" in str(msg).lower():
            self.status_bar.showMessage(self._tr("msg_ai_single_cancelled"))
            self._log(self._tr_log("log_ai_single_cancelled", os.path.basename(path)))
        else:
            self.status_bar.showMessage(self._tr("msg_ai_single_failed"))
            self._log(self._tr_log("log_ai_single_failed", os.path.basename(path), msg))
            QMessageBox.warning(self, self._tr("warn_title"), msg)

        self._close_ai_progress_dialog()

    def on_ai_revision_failed(self, path: str, msg: str):
        self.act_ai_revise.setEnabled(True)

        if "abgebrochen" in str(msg).lower():
            self.status_bar.showMessage(self._tr("msg_ai_cancelled_short"))
            self._log(f"Überarbeitung abgebrochen: {os.path.basename(path)}")
        else:
            self.status_bar.showMessage(self._tr("msg_ai_failed_short"))
            self._log(self._tr_log("log_ai_error", os.path.basename(path), msg))
            QMessageBox.warning(self, self._tr("warn_title"), msg)

        if hasattr(self, "ai_progress_dialog") and self.ai_progress_dialog:
            self.ai_progress_dialog.close()
            self.ai_progress_dialog = None

    def _auto_select_best_device(self):
        caps = self._gpu_capabilities()

        # Priorität: CUDA (echtes CUDA build) > ROCm/HIP > MPS > CPU
        for dev in ("cuda", "rocm", "mps", "cpu"):
            ok, _ = caps.get(dev, (False, ""))
            if ok:
                self.device_str = dev
                break

    # -----------------------------
    # Benutzeroberfläche (UI)
    # -----------------------------
    def _init_ui(self):
        self.toolbar = QToolBar(self._tr("toolbar_main"))
        self.addToolBar(self.toolbar)
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setIconSize(QSize(20, 20))
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self.toolbar.addAction(self.act_add)
        self.toolbar.addAction(self.act_project_load_toolbar)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.act_image_edit)
        self.toolbar.addAction(self.act_play)
        self.toolbar.addAction(self.act_stop)

        self.toolbar.addSeparator()

        rec_wrap = QWidget()
        rec_lay = QHBoxLayout(rec_wrap)
        rec_lay.setContentsMargins(0, 0, 0, 0)
        rec_lay.setSpacing(2)
        rec_lay.addWidget(self.btn_rec_model)

        self.btn_rec_clear = QToolButton()
        self.btn_rec_clear.setText("×")
        self.btn_rec_clear.setToolTip(self._tr("act_clear_rec"))
        self.btn_rec_clear.setCursor(Qt.PointingHandCursor)
        self.btn_rec_clear.clicked.connect(self.clear_rec_model)
        rec_lay.addWidget(self.btn_rec_clear)

        self.toolbar.addWidget(rec_wrap)

        seg_wrap = QWidget()
        seg_lay = QHBoxLayout(seg_wrap)
        seg_lay.setContentsMargins(0, 0, 0, 0)
        seg_lay.setSpacing(2)
        seg_lay.addWidget(self.btn_seg_model)

        self.btn_seg_clear = QToolButton()
        self.btn_seg_clear.setText("×")
        self.btn_seg_clear.setToolTip(self._tr("act_clear_seg"))
        self.btn_seg_clear.setCursor(Qt.PointingHandCursor)
        self.btn_seg_clear.clicked.connect(self.clear_seg_model)
        seg_lay.addWidget(self.btn_seg_clear)

        self.toolbar.addWidget(seg_wrap)

        toolbar_spacer = QWidget()
        toolbar_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(toolbar_spacer)

        self.toolbar.addWidget(self.btn_theme_toggle)
        self.toolbar.addWidget(self.btn_lang_menu)

        right = QVBoxLayout()

        queue_head = QHBoxLayout()
        queue_head.setContentsMargins(0, 0, 0, 0)
        queue_head.setSpacing(6)

        queue_head.addWidget(self.lbl_queue)
        queue_head.addStretch(1)

        self.btn_clear_queue = QPushButton(self._tr("act_clear_queue"))
        self.btn_clear_queue.clicked.connect(self.clear_queue)
        queue_head.addWidget(self.btn_clear_queue, 0, Qt.AlignRight)

        self.btn_toggle_log = QPushButton(self._tr("log_toggle_show"))
        self.btn_toggle_log.setCheckable(True)
        self.btn_toggle_log.setChecked(False)
        self.btn_toggle_log.toggled.connect(self.toggle_log_area)
        queue_head.addWidget(self.btn_toggle_log, 0, Qt.AlignRight)

        right.addLayout(queue_head)
        right.addWidget(self.queue_table, 2)

        # NEU: Logbereich unter der Queue
        right.addWidget(self.log_edit, 1)

        right.addWidget(self.progress_bar)

        lines_head = QHBoxLayout()
        lines_head.setContentsMargins(0, 0, 0, 0)
        lines_head.setSpacing(6)

        self.btn_import_lines = QToolButton()
        self.btn_import_lines.setText(self._tr("btn_import_lines"))
        self.btn_import_lines.setToolTip(self._tr("btn_import_lines_tip"))
        self.btn_import_lines.setPopupMode(QToolButton.InstantPopup)
        self.btn_import_lines.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self.btn_voice_fill = QToolButton()
        self.btn_voice_fill.setText(self._tr("act_voice_fill"))
        self.btn_voice_fill.setToolTip(self._tr("act_voice_fill_tip"))
        self.btn_voice_fill.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.btn_voice_fill.clicked.connect(self.run_voice_line_fill)

        self.btn_ai_revise_bottom = QToolButton()
        self.btn_ai_revise_bottom.setText(self._tr("act_ai_revise"))
        self.btn_ai_revise_bottom.setToolTip(self._tr("act_ai_revise_tip"))
        self.btn_ai_revise_bottom.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.btn_ai_revise_bottom.clicked.connect(self.run_ai_revision)

        self.btn_line_search = QToolButton()
        self.btn_line_search.setText(self._tr("btn_line_search"))
        self.btn_line_search.setToolTip(self._tr("btn_line_search_tooltip"))
        self.btn_line_search.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.btn_line_search.clicked.connect(self._toggle_line_search_popup)

        import_menu = QMenu(self)

        self.act_import_lines_current = QAction(self._tr("act_import_lines_current"), self)
        self.act_import_lines_selected = QAction(self._tr("act_import_lines_selected"), self)
        self.act_import_lines_all = QAction(self._tr("act_import_lines_all"), self)

        self.act_import_lines_current.triggered.connect(self.import_lines_for_current_image)
        self.act_import_lines_selected.triggered.connect(self.import_lines_for_selected_images)
        self.act_import_lines_all.triggered.connect(self.import_lines_for_all_images)

        import_menu.addAction(self.act_import_lines_current)
        import_menu.addAction(self.act_import_lines_selected)
        import_menu.addAction(self.act_import_lines_all)

        self.btn_import_lines.setMenu(import_menu)

        self.line_search_popup = QDialog(self, Qt.Popup | Qt.FramelessWindowHint)
        self.line_search_popup.setModal(False)
        self.line_search_popup.setObjectName("line_search_popup")

        popup_layout = QVBoxLayout(self.line_search_popup)
        popup_layout.setContentsMargins(6, 6, 6, 6)
        popup_layout.setSpacing(0)

        self.line_search_popup_edit = QLineEdit()
        self.line_search_popup_edit.setClearButtonEnabled(True)
        self.line_search_popup_edit.setPlaceholderText(self._tr("line_search_placeholder"))
        self.line_search_popup_edit.setToolTip(self._tr("line_search_tooltip"))
        self.line_search_popup_edit.setFixedWidth(260)
        self.line_search_popup_edit.textChanged.connect(self._filter_lines_list)

        popup_layout.addWidget(self.line_search_popup_edit)

        lines_head.addWidget(self.btn_import_lines)
        lines_head.addWidget(self.btn_voice_fill)
        lines_head.addWidget(self.btn_ai_revise_bottom)
        lines_head.addWidget(self.btn_line_search)
        lines_head.addStretch(1)

        right.addLayout(lines_head)
        right.addWidget(self.list_lines, 3)

        right_widget = QWidget()
        right_widget.setLayout(right)

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.canvas)
        left_widget = QWidget()
        left_widget.setLayout(left_layout)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(right_widget)
        self.splitter.setSizes([1000, 500])
        self.splitter.splitterMoved.connect(lambda *_: self._fit_queue_columns_exact())
        self.setCentralWidget(self.splitter)

        self._make_toolbar_buttons_pushy()
        self._update_model_clear_buttons()
        self._set_primary_toolbar_icons()
        self._set_secondary_button_icons()

        header = self.queue_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QUEUE_COL_NUM, QHeaderView.Fixed)
        header.setSectionResizeMode(QUEUE_COL_CHECK, QHeaderView.Fixed)
        header.setSectionResizeMode(QUEUE_COL_FILE, QHeaderView.Stretch)
        header.setSectionResizeMode(QUEUE_COL_STATUS, QHeaderView.Interactive)

        QTimer.singleShot(0, self._normalize_toolbar_button_sizes)

    def _filter_lines_list(self, text: str = ""):
        needle = (text or "").strip().casefold()

        first_visible_row = None
        current_row = self.list_lines.currentRow()

        self.list_lines.blockSignals(True)
        try:
            for row in range(self.list_lines.count()):
                it = self.list_lines.row_item(row)
                if it is None:
                    continue

                hay = (it.text(1) or "").casefold()
                visible = (not needle) or (needle in hay)
                it.setHidden(not visible)

                if visible and first_visible_row is None:
                    first_visible_row = row

            if first_visible_row is None:
                self.list_lines.clearSelection()
                self.canvas.select_indices([], center=False)
                return

            cur_item = self.list_lines.row_item(current_row) if current_row >= 0 else None
            if cur_item is None or cur_item.isHidden():
                self.list_lines.setCurrentRow(first_visible_row)
        finally:
            self.list_lines.blockSignals(False)

        visible_selected_rows = []
        for row in self._selected_line_rows():
            it = self.list_lines.row_item(row)
            if it is not None and not it.isHidden():
                visible_selected_rows.append(row)

        if visible_selected_rows:
            self.canvas.select_indices(visible_selected_rows, center=False)
        else:
            row = self.list_lines.currentRow()
            if row >= 0:
                self.canvas.select_idx(row, center=False)
            else:
                self.canvas.select_indices([], center=False)

    def _toggle_line_search_popup(self):
        if not hasattr(self, "line_search_popup") or not hasattr(self, "btn_line_search"):
            return

        if self.line_search_popup.isVisible():
            self.line_search_popup.hide()
            return

        self.line_search_popup.adjustSize()
        popup_w = self.line_search_popup.sizeHint().width()
        popup_h = self.line_search_popup.sizeHint().height()

        btn_bottom_left = self.btn_line_search.mapToGlobal(
            QPoint(0, self.btn_line_search.height() + 2)
        )

        main_top_left = self.mapToGlobal(self.rect().topLeft())
        main_top_right = self.mapToGlobal(self.rect().topRight())
        main_bottom_left = self.mapToGlobal(self.rect().bottomLeft())

        margin = 8

        # Rechts am Hauptfenster ausrichten
        x = main_top_right.x() - popup_w - margin

        # Nicht weiter links als das Hauptfenster
        x = max(main_top_left.x() + margin, x)

        # Standard: unter dem Button
        y = btn_bottom_left.y()

        # Sicherheit: auch am Bildschirm clampen
        screen = self.windowHandle().screen() if self.windowHandle() else QApplication.primaryScreen()
        if screen is not None:
            geo = screen.availableGeometry()

            if x + popup_w > geo.right() - margin:
                x = geo.right() - popup_w - margin
            if x < geo.left() + margin:
                x = geo.left() + margin

            # Falls unten kein Platz mehr ist, oberhalb des Buttons anzeigen
            if y + popup_h > geo.bottom() - margin:
                y = self.btn_line_search.mapToGlobal(QPoint(0, -popup_h - 2)).y()

            if y < geo.top() + margin:
                y = geo.top() + margin

        self.line_search_popup.move(QPoint(x, y))
        self.line_search_popup.show()
        self.line_search_popup.raise_()
        self.line_search_popup.activateWindow()

        if hasattr(self, "line_search_popup_edit"):
            self.line_search_popup_edit.setFocus()
            self.line_search_popup_edit.selectAll()

    def _close_line_search_popup(self):
        if hasattr(self, "line_search_popup") and self.line_search_popup.isVisible():
            self.line_search_popup.hide()

    def on_ai_batch_file_done(self, path: str, revised_lines: list, current: int, total: int):
        task = next((i for i in self.queue_items if i.path == path), None)
        if not task or not task.results:
            return

        task.status = STATUS_DONE
        self._update_queue_row(path)

        text, kr_records, im, recs = task.results

        revised_lines = [str(x).strip() for x in revised_lines]
        self._log(
            self._tr_log("log_ai_batch_debug_return", os.path.basename(path), len(revised_lines), len(recs)))

        if len(revised_lines) < len(recs):
            revised_lines.extend([recs[i].text for i in range(len(revised_lines), len(recs))])
        elif len(revised_lines) > len(recs):
            revised_lines = revised_lines[:len(recs)]

        self._log(self._tr_log("log_ai_batch_debug_old_first", recs[0].text if recs else "<leer>"))
        self._log(self._tr_log("log_ai_batch_debug_new_first", revised_lines[0] if revised_lines else "<leer>"))
        self._log(self._tr_log("log_ai_batch_debug_all", revised_lines))

        self._push_undo(task)

        # WICHTIG:
        # Texte ersetzen, Boxen aber exakt so behalten wie sie aktuell im Task stehen.
        new_recs = [
            RecordView(i, revised_lines[i], recs[i].bbox)
            for i in range(len(recs))
        ]

        task.results = (
            "\n".join(rv.text for rv in new_recs).strip(),
            kr_records,
            im,
            new_recs
        )
        task.edited = True

        cur = self._current_task()
        if cur and cur.path == path:
            keep_row = self.list_lines.currentRow()
            if keep_row < 0:
                keep_row = 0 if new_recs else None
            self._sync_ui_after_recs_change(task, keep_row=keep_row)

        self._update_queue_row(path)

        self._log(self._tr_log("log_ai_done", os.path.basename(path)))

    def on_ai_batch_file_failed(self, path: str, msg: str, current: int, total: int):
        task = next((i for i in self.queue_items if i.path == path), None)
        if task:
            task.status = STATUS_ERROR
            self._update_queue_row(path)
        self._log(self._tr_log("log_ai_error", os.path.basename(path), msg))

    def on_ai_batch_finished(self):

        self.act_ai_revise.setEnabled(True)

        if self.ai_batch_dialog:
            self.ai_batch_dialog.close()
            self.ai_batch_dialog = None

        self.status_bar.showMessage(self._tr("msg_ai_batch_finished"))

    def _make_toolbar_buttons_pushy(self):
        # Alle QToolButtons, die QToolBar für QAction erstellt
        for b in self.toolbar.findChildren(QToolButton):
            b.setAutoRaise(False)  # wichtig: sonst wirkt es oft "flat"
            b.setCursor(Qt.PointingHandCursor)

        # Auch die Modell-Buttons
        self.btn_rec_model.setCursor(Qt.PointingHandCursor)
        self.btn_seg_model.setCursor(Qt.PointingHandCursor)

        if hasattr(self, "btn_import_lines"):
            self.btn_import_lines.setCursor(Qt.PointingHandCursor)

    def _init_menu(self):
        menubar = self.menuBar()

        self.file_menu = menubar.addMenu(self._tr("menu_file"))
        self.edit_menu = menubar.addMenu(self._tr("menu_edit"))
        self.options_menu = menubar.addMenu(self._tr("menu_options"))

        self.edit_menu.addAction(self.act_undo)
        self.edit_menu.addAction(self.act_redo)

        self.edit_menu.addSeparator()
        self.act_export_log = QAction(self._tr("menu_export_log"), self)
        self.act_export_log.triggered.connect(self.export_log_txt)
        self.edit_menu.addAction(self.act_export_log)

        self.act_add_files = QAction(self._tr("act_add_files"), self)
        self.act_add_files.triggered.connect(self.choose_files)
        self.file_menu.addAction(self.act_add_files)

        self.act_paste_files_menu = QAction(self._tr("act_paste_clipboard"), self)
        self.act_paste_files_menu.setShortcut(QKeySequence.Paste)
        self.act_paste_files_menu.triggered.connect(self.paste_files_from_clipboard)
        self.file_menu.addAction(self.act_paste_files_menu)

        self.file_menu.addSeparator()

        self.act_project_save = QAction(self._tr("menu_project_save"), self)
        self.act_project_save.triggered.connect(self.save_project)
        self.file_menu.addAction(self.act_project_save)

        self.act_project_save_as = QAction(self._tr("menu_project_save_as"), self)
        self.act_project_save_as.triggered.connect(self.save_project_as)
        self.file_menu.addAction(self.act_project_save_as)

        self.act_project_load = QAction(self._tr("menu_project_load"), self)
        self.act_project_load.triggered.connect(self.load_project)
        self.file_menu.addAction(self.act_project_load)

        self.file_menu.addSeparator()
        self.export_menu = self.file_menu.addMenu(self._tr("menu_export"))

        self.formats = [
            ("Text (.txt)", "txt"),
            ("CSV (.csv)", "csv"),
            ("JSON (.json)", "json"),
            ("ALTO (.xml)", "alto"),
            ("hOCR (.html)", "hocr"),
            ("PDF (.pdf)", "pdf")
        ]
        for name, fmt in self.formats:
            act = QAction(name, self)
            act.triggered.connect(lambda checked, f=fmt: self.export_flow(f))
            self.export_menu.addAction(act)

        self.file_menu.addSeparator()
        self.act_exit = QAction(self._tr("menu_exit"), self)
        self.act_exit.setShortcut(QKeySequence.Quit)
        self.act_exit.triggered.connect(self.close)
        self.file_menu.addAction(self.act_exit)

        self.models_menu = menubar.addMenu(self._tr("menu_models"))

        self.act_rec = QAction(self._tr("act_load_rec_model"), self)
        self.act_rec.triggered.connect(self.choose_rec_model)
        self.models_menu.addAction(self.act_rec)

        self.act_seg = QAction(self._tr("act_load_seg_model"), self)
        self.act_seg.triggered.connect(self.choose_seg_model)
        self.models_menu.addAction(self.act_seg)

        self.models_menu.addSeparator()

        self.kraken_models_submenu = self.models_menu.addMenu(self._tr("submenu_available_kraken_models"))

        # Diese Aktionen werden nicht mehr direkt ins Hauptmenü gesetzt,
        # sondern im Untermenü eingebaut.
        self.act_clear_rec = QAction(self._tr("act_clear_rec"), self)
        self.act_clear_rec.triggered.connect(self.clear_rec_model)

        self.act_clear_seg = QAction(self._tr("act_clear_seg"), self)
        self.act_clear_seg.triggered.connect(self.clear_seg_model)

        self.act_rec_status = QAction(self._tr("status_rec_model", "-"), self)
        self.act_rec_status.setEnabled(False)

        self.act_seg_status = QAction(self._tr("status_seg_model", "-"), self)
        self.act_seg_status.setEnabled(False)

        self._rebuild_kraken_models_submenu()
        self._update_kraken_menu_status()

        self.models_menu.addSeparator()
        self.models_menu.addAction(self.act_rec_status)
        self.models_menu.addAction(self.act_seg_status)
        self.models_menu.addSeparator()

        self.act_download = QAction(self._tr("act_download_model"), self)
        self.act_download.triggered.connect(self.open_download_link)
        self.models_menu.addAction(self.act_download)

        self.revision_models_menu = menubar.addMenu(self._tr("menu_lm_options"))

        # -----------------------------
        # Whisper-Optionen
        # -----------------------------
        self.whisper_menu = menubar.addMenu(self._tr("menu_whisper_options"))

        self.act_whisper_set_path = QAction(self._tr("act_whisper_set_path"), self)
        self.act_whisper_set_path.triggered.connect(self.set_whisper_base_dir_dialog)
        self.whisper_menu.addAction(self.act_whisper_set_path)

        self.act_whisper_set_mic = QAction(self._tr("act_whisper_set_mic"), self)
        self.act_whisper_set_mic.triggered.connect(self.choose_whisper_microphone_dialog)
        self.whisper_menu.addAction(self.act_whisper_set_mic)

        self.whisper_menu.addSeparator()

        self.act_whisper_scan = QAction(self._tr("act_scan_local"), self)
        self.act_whisper_scan.triggered.connect(self.scan_whisper_models_now)
        self.whisper_menu.addAction(self.act_whisper_scan)

        self.whisper_models_submenu = self.whisper_menu.addMenu(self._tr("submenu_available_whisper_models"))
        self.whisper_model_group = QActionGroup(self)
        self.whisper_model_group.setExclusive(True)

        self.whisper_menu.addSeparator()

        self.act_whisper_status_model = QAction(self._tr("whisper_status_model", "-"), self)
        self.act_whisper_status_model.setEnabled(False)
        self.whisper_menu.addAction(self.act_whisper_status_model)

        self.act_whisper_status_mic = QAction(self._tr("whisper_status_mic", "-"), self)
        self.act_whisper_status_mic.setEnabled(False)
        self.whisper_menu.addAction(self.act_whisper_status_mic)

        self.act_whisper_status_path = QAction(self._tr("whisper_status_path", "-"), self)
        self.act_whisper_status_path.setEnabled(False)
        self.whisper_menu.addAction(self.act_whisper_status_path)

        self._scan_whisper_models()
        self._rebuild_whisper_model_submenu()
        self._update_whisper_menu_status()

        self.act_lm_help = menubar.addAction(self._tr("act_help"))
        self.act_lm_help.triggered.connect(self.show_lm_help_dialog)

        self.act_set_manual_lm_url = QAction(self._tr("act_set_manual_lm_url"), self)
        self.act_set_manual_lm_url.triggered.connect(self.set_manual_ai_base_url_dialog)
        self.revision_models_menu.addAction(self.act_set_manual_lm_url)

        self.act_clear_manual_lm_url = QAction(self._tr("act_clear_manual_lm_url"), self)
        self.act_clear_manual_lm_url.triggered.connect(self.clear_manual_ai_base_url)
        self.revision_models_menu.addAction(self.act_clear_manual_lm_url)

        self.revision_models_menu.addSeparator()

        self.act_scan_lm = QAction(self._tr("act_scan_local"), self)
        self.act_scan_lm.triggered.connect(self.scan_ai_models_now)
        self.revision_models_menu.addAction(self.act_scan_lm)

        self.ai_models_submenu = self.revision_models_menu.addMenu(self._tr("submenu_available_ai_models"))
        self.ai_model_group = QActionGroup(self)
        self.ai_model_group.setExclusive(True)
        self._rebuild_ai_model_submenu()

        self.revision_models_menu.addSeparator()

        self.act_lm_status = QAction(self._tr("lm_status_model_value", "-"), self)
        self.act_lm_status.setEnabled(False)
        self.revision_models_menu.addAction(self.act_lm_status)

        self.act_lm_mode = QAction(self._tr("lm_mode_value", "-"), self)
        self.act_lm_mode.setEnabled(False)
        self.revision_models_menu.addAction(self.act_lm_mode)

        self.act_lm_base_url = QAction(self._tr("lm_server_value", "-"), self)
        self.act_lm_base_url.setEnabled(False)
        self.revision_models_menu.addAction(self.act_lm_base_url)

        # Sprachen
        self._build_toolbar_language_theme_menus()

        # Hardware-Menü
        self.options_menu.addSeparator()
        self.hw_menu = self.options_menu.addMenu(self._tr("menu_hw"))
        hw_group = QActionGroup(self)
        self.hw_actions: Dict[str, QAction] = {}
        for key, dev in [("hw_cpu", "cpu"), ("hw_cuda", "cuda"), ("hw_rocm", "rocm"), ("hw_mps", "mps")]:
            act = QAction(self._tr(key), self)
            act.setCheckable(True)
            if dev == self.device_str:
                act.setChecked(True)
            act.triggered.connect(lambda checked, d=dev: self.set_device(d))
            hw_group.addAction(act)
            self.hw_menu.addAction(act)
            self.hw_actions[dev] = act

        # Leserichtung
        self.options_menu.addSeparator()
        self.reading_menu = self.options_menu.addMenu(self._tr("menu_reading"))
        read_group = QActionGroup(self)
        self.read_actions: List[QAction] = []
        for key, mode in [
            ("reading_tb_lr", READING_MODES["TB_LR"]),
            ("reading_tb_rl", READING_MODES["TB_RL"]),
            ("reading_bt_lr", READING_MODES["BT_LR"]),
            ("reading_bt_rl", READING_MODES["BT_RL"]),
        ]:
            act = QAction(self._tr(key), self)
            act.setCheckable(True)
            if mode == self.reading_direction:
                act.setChecked(True)
            act.triggered.connect(lambda checked, m=mode: self.set_reading_direction(m))
            read_group.addAction(act)
            self.reading_menu.addAction(act)
            self.read_actions.append(act)

        # Overlay (Boxen)
        self.options_menu.addSeparator()
        self.act_overlay = QAction(self._tr("act_overlay_show"), self)
        self.act_overlay.setCheckable(True)
        self.act_overlay.setChecked(True)
        self.act_overlay.toggled.connect(self._on_overlay_toggled)
        self.options_menu.addAction(self.act_overlay)

        if self.device_str in self.hw_actions:
            self.hw_actions[self.device_str].setChecked(True)

    # -----------------------------
    # Queue columns
    # -----------------------------
    def _update_queue_check_header(self):
        header_item = self.queue_table.horizontalHeaderItem(QUEUE_COL_CHECK)
        if header_item is None:
            return

        total_rows = self.queue_table.rowCount()
        checked_rows = len(self._checked_queue_rows())

        if total_rows == 0 or checked_rows == 0:
            symbol = "☐"
        elif checked_rows == total_rows:
            symbol = "☑"
        else:
            symbol = "☒"

        header_item.setText(symbol)
        header_item.setTextAlignment(Qt.AlignCenter)
        header_item.setToolTip(self._tr("queue_check_header_tooltip"))

    def _on_queue_header_clicked(self, logical_index: int):
        if logical_index != QUEUE_COL_CHECK:
            return
        self._toggle_all_queue_checkmarks()

    def _queue_num_col_width(self) -> int:
        count = max(1, self.queue_table.rowCount())
        digits = len(str(count))

        fm = self.queue_table.fontMetrics()
        text_w = fm.horizontalAdvance("9" * digits)
        header_w = fm.horizontalAdvance("#")

        # kleiner Puffer links/rechts
        return max(header_w, text_w) + 10

    def _fit_queue_columns_exact(self):
        if self._resizing_cols:
            return

        self._resizing_cols = True
        try:
            vw = max(1, self.queue_table.viewport().width())

            num_w = self._queue_num_col_width()
            check_w = self._queue_check_col_width()

            remaining = max(0, vw - num_w - check_w)

            current_status_w = self.queue_table.columnWidth(QUEUE_COL_STATUS)
            preferred_status_w = current_status_w if current_status_w > 0 else 120

            min_status_w = 90
            min_file_w = 180

            max_status_w = max(min_status_w, remaining - min_file_w)

            # Wenn sehr wenig Platz da ist, Status zusammendrücken,
            # damit die Tabelle nie breiter als der Viewport wird.
            if remaining <= (min_status_w + min_file_w):
                status_w = max(0, min(preferred_status_w, max(0, remaining // 3)))
            else:
                status_w = max(min_status_w, min(preferred_status_w, max_status_w))

            self.queue_table.setColumnWidth(QUEUE_COL_NUM, num_w)
            self.queue_table.setColumnWidth(QUEUE_COL_CHECK, check_w)
            self.queue_table.setColumnWidth(QUEUE_COL_STATUS, status_w)

            self._update_queue_hint()
        finally:
            self._resizing_cols = False

    def _on_queue_header_resized(self, logicalIndex: int, oldSize: int, newSize: int):
        if self._resizing_cols:
            return

        if logicalIndex in (QUEUE_COL_NUM, QUEUE_COL_CHECK, QUEUE_COL_STATUS):
            self._fit_queue_columns_exact()

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def _update_queue_hint(self):
        empty = (self.queue_table.rowCount() == 0)
        self.queue_hint.setText(self._tr("queue_drop_hint"))
        self.queue_hint.resize(self.queue_table.viewport().size())
        self.queue_hint.move(0, 0)
        self.queue_hint.setVisible(empty)

    # -----------------------------
    # Fortschritts-Helfer
    # -----------------------------
    def _set_progress_busy(self):
        self.progress_bar.setValue(0)
        self.progress_bar.setRange(0, 0)  # busy animation

    def _set_progress_idle(self, value: int = 0):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(max(0, min(100, int(value))))

    def on_progress_update(self, v: int):
        v = max(0, min(100, int(v)))

        # Solange wir in busy (0,0) sind und v noch 0 ist -> Animation bleibt
        if self.progress_bar.minimum() == 0 and self.progress_bar.maximum() == 0:
            if v > 0:
                self.progress_bar.setRange(0, 100)  # sobald >0 -> normale Prozentanzeige
            else:
                return  # busy-mode ignoriert setValue sowieso; Animation bleibt

        self.progress_bar.setValue(v)

    # -----------------------------
    # Theme
    def apply_theme(self, theme: str):
        self.current_theme = theme
        self.settings.setValue("ui/theme", self.current_theme)

        pal = QPalette()
        conf = THEMES[theme]

        fg = QColor(conf["fg"])
        bg = QColor(conf["bg"])
        base = conf["table_base"]
        button = conf["table_base"].lighter(110)

        pal.setColor(QPalette.Window, bg)
        pal.setColor(QPalette.WindowText, fg)
        pal.setColor(QPalette.Base, base)
        pal.setColor(QPalette.AlternateBase, base.lighter(110))
        pal.setColor(QPalette.ToolTipBase, QColor("#ffffff" if theme == "bright" else "#2b3038"))
        pal.setColor(QPalette.ToolTipText, QColor("#000000" if theme == "bright" else "#f3f4f6"))
        pal.setColor(QPalette.Text, fg)
        pal.setColor(QPalette.Button, button)
        pal.setColor(QPalette.ButtonText, fg)
        pal.setColor(QPalette.BrightText, Qt.red)
        pal.setColor(QPalette.Link, QColor(42, 130, 218))
        pal.setColor(QPalette.Highlight, QColor(42, 130, 218))
        pal.setColor(QPalette.HighlightedText, QColor("#ffffff" if theme == "dark" else "#000000"))

        app = QApplication.instance()
        app.setPalette(pal)

        self.canvas.set_theme(theme)
        app.setStyleSheet(_theme_app_qss(theme))

        self._update_toolbar_language_theme_ui()
        self._set_primary_toolbar_icons()
        self._set_secondary_button_icons()

    def toggle_theme(self):
        new_theme = "dark" if self.current_theme == "bright" else "bright"
        self.apply_theme(new_theme)

    # -----------------------------
    # Language / reading
    # -----------------------------
    def set_language(self, lang):
        self.current_lang = lang
        self.settings.setValue("ui/language", self.current_lang)
        self.retranslate_ui()
        self._refresh_hw_menu_availability()
        self._update_toolbar_language_theme_ui()

    def _build_toolbar_language_theme_menus(self):
        # Nur Sprach-Menü
        self.lang_toolbar_menu = QMenu(self)
        self.lang_group = QActionGroup(self)

        self.act_lang_de = QAction(self._tr("lang_de"), self)
        self.act_lang_de.setCheckable(True)
        self.act_lang_de.triggered.connect(lambda: self.set_language("de"))
        self.lang_group.addAction(self.act_lang_de)
        self.lang_toolbar_menu.addAction(self.act_lang_de)

        self.act_lang_en = QAction(self._tr("lang_en"), self)
        self.act_lang_en.setCheckable(True)
        self.act_lang_en.triggered.connect(lambda: self.set_language("en"))
        self.lang_group.addAction(self.act_lang_en)
        self.lang_toolbar_menu.addAction(self.act_lang_en)

        self.act_lang_fr = QAction(self._tr("lang_fr"), self)
        self.act_lang_fr.setCheckable(True)
        self.act_lang_fr.triggered.connect(lambda: self.set_language("fr"))
        self.lang_group.addAction(self.act_lang_fr)
        self.lang_toolbar_menu.addAction(self.act_lang_fr)

        self.btn_lang_menu.setMenu(self.lang_toolbar_menu)

        self._update_toolbar_language_theme_ui()

    def _update_toolbar_language_theme_ui(self):
        if hasattr(self, "btn_theme_toggle"):
            is_dark = self.current_theme == "dark"
            self.btn_theme_toggle.setChecked(is_dark)
            self.btn_theme_toggle.setText("🔅" if is_dark else "💡")
            self.btn_theme_toggle.setIcon(QIcon())
            self.btn_theme_toggle.setToolTip(self._tr("toolbar_theme_tooltip"))

        if hasattr(self, "btn_lang_menu"):
            self.btn_lang_menu.setText(self._tr("toolbar_language"))

            lang_theme_name = "preferences-desktop-locale"
            if QIcon.fromTheme(lang_theme_name).isNull():
                lang_theme_name = "accessories-dictionary"

            self.btn_lang_menu.setIcon(
                self._tinted_theme_or_standard_icon(
                    lang_theme_name,
                    QStyle.SP_FileDialogContentsView
                )
            )
            self.btn_lang_menu.setToolTip(self._tr("toolbar_language_tooltip"))

        if hasattr(self, "act_lang_de"):
            self.act_lang_de.setText(self._tr("lang_de"))
            self.act_lang_de.setChecked(self.current_lang == "de")

        if hasattr(self, "act_lang_en"):
            self.act_lang_en.setText(self._tr("lang_en"))
            self.act_lang_en.setChecked(self.current_lang == "en")

        if hasattr(self, "act_lang_fr"):
            self.act_lang_fr.setText(self._tr("lang_fr"))
            self.act_lang_fr.setChecked(self.current_lang == "fr")

    def _update_models_menu_labels(self):
        if hasattr(self, "act_rec"):
            self.act_rec.setText(self._tr("act_load_rec_model"))
        if hasattr(self, "act_seg"):
            self.act_seg.setText(self._tr("act_load_seg_model"))
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

    def set_reading_direction(self, mode):
        self.reading_direction = mode

    def retranslate_ui(self):
        self.setWindowTitle(self._tr("app_title"))
        self.file_menu.setTitle(self._tr("menu_file"))
        self.edit_menu.setTitle(self._tr("menu_edit"))
        self.models_menu.setTitle(self._tr("menu_models"))
        self.options_menu.setTitle(self._tr("menu_options"))
        self.hw_menu.setTitle(self._tr("menu_hw"))
        self.export_menu.setTitle(self._tr("menu_export"))
        self.reading_menu.setTitle(self._tr("menu_reading"))
        if hasattr(self, "revision_models_menu"):
            self.revision_models_menu.setTitle(self._tr("menu_lm_options"))
        if hasattr(self, "whisper_menu"):
            self.whisper_menu.setTitle(self._tr("menu_whisper_options"))

        self.act_export_log.setText(self._tr("menu_export_log"))

        if hasattr(self, "act_lm_help"):
            self.act_lm_help.setText(self._tr("act_help"))
        if hasattr(self, "act_ai_revise"):
            self.act_ai_revise.setText(self._tr("act_ai_revise"))
            self.act_ai_revise.setToolTip(self._tr("act_ai_revise_tip"))
        if hasattr(self, "btn_ai_model"):
            self._update_ai_model_ui()
        if hasattr(self, "act_ai_revise_all"):
            self.act_ai_revise_all.setText(self._tr("act_ai_revise_all"))
            self.act_ai_revise_all.setToolTip(self._tr("act_ai_revise_all_tip"))
        if hasattr(self, "btn_import_lines"):
            self.btn_import_lines.setText(self._tr("btn_import_lines"))
            self.btn_import_lines.setToolTip(self._tr("btn_import_lines_tip"))
        if hasattr(self, "act_import_lines_current"):
            self.act_import_lines_current.setText(self._tr("act_import_lines_current"))
        if hasattr(self, "act_import_lines_selected"):
            self.act_import_lines_selected.setText(self._tr("act_import_lines_selected"))
        if hasattr(self, "act_import_lines_all"):
            self.act_import_lines_all.setText(self._tr("act_import_lines_all"))
        if hasattr(self, "act_project_save"):
            self.act_project_save.setText(self._tr("menu_project_save"))
        if hasattr(self, "act_project_save_as"):
            self.act_project_save_as.setText(self._tr("menu_project_save_as"))
        if hasattr(self, "act_project_load"):
            self.act_project_load.setText(self._tr("menu_project_load"))
        if hasattr(self, "act_paste_files_menu"):
            self.act_paste_files_menu.setText(self._tr("act_paste_clipboard"))
        if hasattr(self, "act_paste_files"):
            self.act_paste_files.setText(self._tr("act_paste_clipboard"))
        if hasattr(self, "btn_voice_fill"):
            self.btn_voice_fill.setText(self._tr("act_voice_fill"))
            self.btn_voice_fill.setToolTip(self._tr("act_voice_fill_tip"))
        if hasattr(self, "btn_ai_revise_bottom"):
            self.btn_ai_revise_bottom.setText(self._tr("act_ai_revise"))
            self.btn_ai_revise_bottom.setToolTip(self._tr("act_ai_revise_tip"))
        if hasattr(self, "btn_line_search"):
            self.btn_line_search.setText(self._tr("btn_line_search"))
            self.btn_line_search.setToolTip(self._tr("btn_line_search_tooltip"))
        if hasattr(self, "line_search_popup_edit"):
            self.line_search_popup_edit.setPlaceholderText(self._tr("line_search_placeholder"))
            self.line_search_popup_edit.setToolTip(self._tr("line_search_tooltip"))
        if hasattr(self, "btn_clear_queue"):
            self.btn_clear_queue.setText(self._tr("act_clear_queue"))
        if hasattr(self, "btn_toggle_log"):
            if self.btn_toggle_log.isChecked():
                self.btn_toggle_log.setText(self._tr("log_toggle_hide"))
            else:
                self.btn_toggle_log.setText(self._tr("log_toggle_show"))

        self.act_undo.setText(self._tr("act_undo"))
        self.act_redo.setText(self._tr("act_redo"))

        self.act_add_files.setText(self._tr("act_add_files"))
        self.act_exit.setText(self._tr("menu_exit"))
        self.act_download.setText(self._tr("act_download_model"))
        self.act_overlay.setText(self._tr("act_overlay_show"))

        self.act_add.setText(self._tr("act_add_files"))
        self.act_clear.setText(self._tr("act_clear_queue"))
        self.act_play.setText(self._tr("act_start_ocr"))
        self.act_stop.setText(self._tr("act_stop_ocr"))
        if hasattr(self, "act_image_edit"):
            self.act_image_edit.setText(self._tr("act_image_edit"))
        self.act_project_load_toolbar.setText(self._tr("menu_project_load"))
        self.act_project_load_toolbar.setToolTip(self._tr("menu_project_load"))

        self.lbl_queue.setText(self._tr("lbl_queue"))
        self.lbl_lines.setText(self._tr("lbl_lines"))
        self.queue_table.setHorizontalHeaderLabels(["#", "☐", self._tr("col_loaded_files"), self._tr("col_status")])
        self._update_queue_check_header()

        if hasattr(self.list_lines, "setHeaderLabels"):
            self.list_lines.setHeaderLabels(["#", self._tr("lines_tree_header")])
            self.list_lines.header().setDefaultAlignment(Qt.AlignCenter)

        if self.model_path:
            self.btn_rec_model.setText(self._tr("btn_rec_model_value", os.path.basename(self.model_path)))
        else:
            self.btn_rec_model.setText(self._tr("btn_rec_model_empty"))

        if self.seg_model_path:
            self.btn_seg_model.setText(self._tr("btn_seg_model_value", os.path.basename(self.seg_model_path)))
        else:
            self.btn_seg_model.setText(self._tr("btn_seg_model_empty"))

        mapping = {"cpu": "hw_cpu", "cuda": "hw_cuda", "rocm": "hw_rocm", "mps": "hw_mps"}
        for dev, key in mapping.items():
            if dev in self.hw_actions:
                self.hw_actions[dev].setText(self._tr(key))

        read_keys = ["reading_tb_lr", "reading_tb_rl", "reading_bt_lr", "reading_bt_rl"]
        for act, key in zip(self.read_actions, read_keys):
            act.setText(self._tr(key))

        self._retranslate_queue_rows()
        self._update_queue_hint()
        self.canvas._show_drop_hint()
        self._update_models_menu_labels()
        self._update_model_clear_buttons()
        self._update_toolbar_language_theme_ui()
        self._set_primary_toolbar_icons()
        self._set_secondary_button_icons()
        QTimer.singleShot(0, self._normalize_toolbar_button_sizes)

        # Models menu actions
        if hasattr(self, "act_rec"):
            self.act_rec.setText(self._tr("act_load_rec_model"))
        if hasattr(self, "act_seg"):
            self.act_seg.setText(self._tr("act_load_seg_model"))
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

        if hasattr(self, "act_clear_rec"):
            self.act_clear_rec.setText(self._tr("act_clear_rec"))
        if hasattr(self, "act_clear_seg"):
            self.act_clear_seg.setText(self._tr("act_clear_seg"))

        if hasattr(self, "kraken_models_submenu"):
            self.kraken_models_submenu.setTitle(self._tr("submenu_available_kraken_models"))

        if hasattr(self, "ai_models_submenu"):
            self.ai_models_submenu.setTitle(self._tr("submenu_available_ai_models"))

        if hasattr(self, "whisper_models_submenu"):
            self.whisper_models_submenu.setTitle(self._tr("submenu_available_whisper_models"))

        self._update_kraken_menu_status()
        self._rebuild_kraken_models_submenu()
        self.refresh_models_menu_status()
        self._update_whisper_menu_status()
        self._rebuild_whisper_model_submenu()

        if hasattr(self, "btn_rec_clear"):
            self.btn_rec_clear.setToolTip(self._tr("act_clear_rec"))
        if hasattr(self, "btn_seg_clear"):
            self.btn_seg_clear.setToolTip(self._tr("act_clear_seg"))

        header = self.queue_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QUEUE_COL_NUM, QHeaderView.Fixed)
        header.setSectionResizeMode(QUEUE_COL_CHECK, QHeaderView.Fixed)
        header.setSectionResizeMode(QUEUE_COL_FILE, QHeaderView.Stretch)
        header.setSectionResizeMode(QUEUE_COL_STATUS, QHeaderView.Interactive)

        # Header-Schrift im Wartebereich normal halten
        header_font = header.font()
        header_font.setBold(False)
        header.setFont(header_font)

    def _retranslate_queue_rows(self):
        for it in self.queue_items:
            self._update_queue_row(it.path)

    # -----------------------------
    # GPU-Erkennung + Verfügbarkeit
    # -----------------------------
    def _gpu_capabilities(self) -> Dict[str, Tuple[bool, str]]:
        caps: Dict[str, Tuple[bool, str]] = {"cpu": (True, "CPU")}

        cuda_avail = torch.cuda.is_available() and torch.cuda.device_count() > 0
        cuda_name = ""
        if cuda_avail:
            try:
                cuda_name = torch.cuda.get_device_name(0)
            except Exception:
                cuda_name = "GPU"

        hip_ver = getattr(torch.version, "hip", None)
        cuda_ver = getattr(torch.version, "cuda", None)

        # Verfügbarkeit von ROCm (HIP)
        rocm_avail = cuda_avail and (hip_ver is not None)
        rocm_details = ""
        if rocm_avail:
            rocm_details = f"{cuda_name} (HIP {hip_ver})" if cuda_name else f"HIP {hip_ver}"

        # Verfügbarkeit von CUDA (echter CUDA-Build)
        cuda_true = cuda_avail and (cuda_ver is not None)
        cuda_true_details = ""
        if cuda_true:
            cuda_true_details = f"{cuda_name} (CUDA {cuda_ver})" if cuda_name else f"CUDA {cuda_ver}"

        mps_avail = hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
        mps_details = "Apple MPS" if mps_avail else ""

        caps["cuda"] = (cuda_true, cuda_true_details if cuda_true_details else "CUDA")
        caps["rocm"] = (rocm_avail, rocm_details if rocm_details else "ROCm")
        caps["mps"] = (mps_avail, mps_details if mps_details else "MPS")
        return caps

    def _total_ram_bytes(self) -> int:
        try:
            if sys.platform.startswith("win"):
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]

                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                    return int(stat.ullTotalPhys)
        except Exception:
            pass

        try:
            if hasattr(os, "sysconf"):
                pages = os.sysconf("SC_PHYS_PAGES")
                page_size = os.sysconf("SC_PAGE_SIZE")
                if isinstance(pages, int) and isinstance(page_size, int) and pages > 0 and page_size > 0:
                    return int(pages * page_size)
        except Exception:
            pass

        return 0

    def _total_ram_gb(self) -> float:
        ram_bytes = self._total_ram_bytes()
        if ram_bytes <= 0:
            return 0.0
        return round(ram_bytes / (1024 ** 3), 1)

    def _cpu_summary(self) -> Tuple[str, int]:
        logical = os.cpu_count() or 1
        name = ""

        if sys.platform.startswith("win"):
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
                )
                name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
                name = " ".join(str(name).split()).strip()
                if name:
                    return name, logical
            except Exception:
                pass

            try:
                out = subprocess.check_output(
                    ["wmic", "cpu", "get", "name"],
                    text=True,
                    encoding="utf-8",
                    errors="ignore"
                )
                lines = [x.strip() for x in out.splitlines() if x.strip() and x.strip().lower() != "name"]
                if lines:
                    return lines[0], logical
            except Exception:
                pass

        elif sys.platform == "darwin":
            try:
                out = subprocess.check_output(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    text=True,
                    encoding="utf-8",
                    errors="ignore"
                ).strip()
                if out:
                    return out, logical
            except Exception:
                pass

        else:
            try:
                with open("/proc/cpuinfo", "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if ":" in line and line.lower().startswith("model name"):
                            name = line.split(":", 1)[1].strip()
                            if name:
                                return name, logical
            except Exception:
                pass

        try:
            name = (platform.processor() or "").strip()
        except Exception:
            name = ""

        if not name and sys.platform.startswith("win"):
            name = os.environ.get("PROCESSOR_IDENTIFIER", "").strip()

        if not name:
            name = "CPU"

        return name, logical

    def _gpu_summary(self) -> Dict[str, object]:
        caps = self._gpu_capabilities()

        info = {
            "gpu_ok": False,
            "gpu_label": self._tr("help_hw_gpu_none"),
            "gpu_vram_gb": 0.0,
            "gpu_vram_text": self._tr("help_hw_vram_unknown"),
        }

        for key in ("cuda", "rocm", "mps"):
            ok, detail = caps.get(key, (False, ""))
            if not ok:
                continue

            info["gpu_ok"] = True
            info["gpu_label"] = detail if detail else key.upper()

            if key in ("cuda", "rocm"):
                try:
                    props = torch.cuda.get_device_properties(0)
                    total_memory = int(getattr(props, "total_memory", 0) or 0)
                    if total_memory > 0:
                        vram_gb = round(total_memory / (1024 ** 3), 1)
                        info["gpu_vram_gb"] = vram_gb
                        info["gpu_vram_text"] = self._tr("help_hw_fmt_gb", vram_gb)
                    else:
                        info["gpu_vram_text"] = self._tr("help_hw_vram_unknown")
                except Exception:
                    info["gpu_vram_text"] = self._tr("help_hw_vram_unknown")
            else:
                info["gpu_vram_text"] = self._tr("help_hw_vram_shared")

            break

        return info

    def _hardware_snapshot(self) -> Dict[str, object]:
        cpu_name, cpu_threads = self._cpu_summary()
        ram_gb = self._total_ram_gb()
        gpu = self._gpu_summary()

        return {
            "cpu_name": cpu_name,
            "cpu_threads": cpu_threads,
            "ram_gb": ram_gb,
            "gpu_ok": gpu["gpu_ok"],
            "gpu_label": gpu["gpu_label"],
            "gpu_vram_gb": gpu["gpu_vram_gb"],
            "gpu_vram_text": gpu["gpu_vram_text"],
        }

    def _hardware_feature_status(self, hw: Dict[str, object], feature: str) -> Tuple[str, str]:
        cpu_threads = int(hw.get("cpu_threads", 1) or 1)
        ram_gb = float(hw.get("ram_gb", 0.0) or 0.0)
        gpu_ok = bool(hw.get("gpu_ok", False))
        gpu_vram_gb = float(hw.get("gpu_vram_gb", 0.0) or 0.0)

        feature = (feature or "").lower().strip()

        if feature == "kraken":
            if cpu_threads >= 4 and ram_gb >= 8:
                return "green", "help_hw_status_good"
            if cpu_threads >= 2 and ram_gb >= 4:
                return "yellow", "help_hw_status_usable_slow"
            return "red", "help_hw_status_weak"

        if feature == "lm":
            if gpu_ok and gpu_vram_gb >= 8 and cpu_threads >= 6 and ram_gb >= 16:
                return "green", "help_hw_status_good"
            if gpu_ok and gpu_vram_gb >= 6 and cpu_threads >= 4 and ram_gb >= 8:
                return "yellow", "help_hw_status_limited"
            if (not gpu_ok) and cpu_threads >= 8 and ram_gb >= 16:
                return "yellow", "help_hw_status_limited_cpu"
            return "red", "help_hw_status_weak"

        if feature == "whisper":
            if gpu_ok and gpu_vram_gb >= 4 and ram_gb >= 8:
                return "green", "help_hw_status_good"
            if cpu_threads >= 6 and ram_gb >= 8:
                return "green", "help_hw_status_good"
            if cpu_threads >= 4 and ram_gb >= 6:
                return "yellow", "help_hw_status_usable_slow"
            return "red", "help_hw_status_weak"

        return "red", "help_hw_status_weak"

    def _hardware_component_status(self, hw: Dict[str, object], component: str) -> Tuple[str, str]:
        cpu_threads = int(hw.get("cpu_threads", 1) or 1)
        ram_gb = float(hw.get("ram_gb", 0.0) or 0.0)
        gpu_ok = bool(hw.get("gpu_ok", False))
        gpu_vram_gb = float(hw.get("gpu_vram_gb", 0.0) or 0.0)

        component = (component or "").lower().strip()

        if component == "cpu":
            if cpu_threads >= 6:
                return "green", "help_hw_component_ok"
            if cpu_threads >= 4:
                return "yellow", "help_hw_component_borderline"
            return "red", "help_hw_component_not_enough"

        if component == "gpu":
            if gpu_ok and gpu_vram_gb >= 8:
                return "green", "help_hw_component_ok"
            if gpu_ok and (gpu_vram_gb >= 4 or gpu_vram_gb == 0):
                return "yellow", "help_hw_component_borderline"
            return "red", "help_hw_component_not_enough"

        if component == "ram":
            if ram_gb >= 16:
                return "green", "help_hw_component_ok"
            if ram_gb >= 8:
                return "yellow", "help_hw_component_borderline"
            return "red", "help_hw_component_not_enough"

        return "red", "help_hw_component_not_enough"

    def _status_dot_html(self, level: str) -> str:
        colors = {
            "green": "#16a34a",
            "yellow": "#eab308",
            "red": "#dc2626",
        }
        color = colors.get(level, "#6b7280")
        return (
            f'<span style="display:inline-block; width:12px; height:12px; '
            f'border-radius:50%; background:{color}; margin-right:8px; '
            f'vertical-align:middle;"></span>'
        )

    def _status_chip_html(self, level: str, text: str) -> str:
        bg = {
            "green": "#dcfce7",
            "yellow": "#fef3c7",
            "red": "#fee2e2",
        }.get(level, "#e5e7eb")

        fg = {
            "green": "#166534",
            "yellow": "#92400e",
            "red": "#991b1b",
        }.get(level, "#374151")

        return (
            f'<span style="display:inline-block; padding:2px 8px; '
            f'border-radius:999px; background:{bg}; color:{fg}; '
            f'font-weight:700; font-size:11px; white-space:nowrap;">{html.escape(text)}</span>'
        )

    def _build_hardware_requirements_help_html(self) -> str:
        hw = self._hardware_snapshot()

        kraken_level, kraken_key = self._hardware_feature_status(hw, "kraken")
        lm_level, lm_key = self._hardware_feature_status(hw, "lm")
        whisper_level, whisper_key = self._hardware_feature_status(hw, "whisper")

        cpu_level, cpu_key = self._hardware_component_status(hw, "cpu")
        gpu_level, gpu_key = self._hardware_component_status(hw, "gpu")
        ram_level, ram_key = self._hardware_component_status(hw, "ram")

        cpu_name = html.escape(str(hw.get("cpu_name", "CPU")))
        cpu_threads = int(hw.get("cpu_threads", 1) or 1)
        ram_gb = float(hw.get("ram_gb", 0.0) or 0.0)
        gpu_label = html.escape(str(hw.get("gpu_label", self._tr("help_hw_gpu_none"))))
        gpu_vram_text = html.escape(str(hw.get("gpu_vram_text", self._tr("help_hw_vram_unknown"))))

        kraken_text = self._tr(kraken_key)
        lm_text = self._tr(lm_key)
        whisper_text = self._tr(whisper_key)

        cpu_text = self._tr(cpu_key)
        gpu_text = self._tr(gpu_key)
        ram_text = self._tr(ram_key)

        return (
            '            <div class="card">\n'
            f'                <div class="h2">{self._tr("help_hw_card_title")}</div>\n'
            f'                <span class="badge">{self._tr("help_hw_badge")}</span>\n'
            f'                <div class="small">{self._tr("help_hw_intro")}</div>\n'
            '                <br>\n'
            '                <table style="width:100%; border-collapse:separate; border-spacing:14px 0;">\n'
            '                    <tr>\n'
            '                        <td style="width:40%; vertical-align:top;">\n'
            f'                            <div class="h2">{self._tr("help_hw_h2_detected")}</div>\n'
            '                            <table class="table">\n'
            f'                                <tr><td><b>CPU</b></td><td>{cpu_name}</td></tr>\n'
            f'                                <tr><td><b>{self._tr("help_hw_label_threads")}</b></td><td>{cpu_threads}</td></tr>\n'
            f'                                <tr><td><b>RAM</b></td><td>{self._tr("help_hw_fmt_gb", ram_gb)}</td></tr>\n'
            f'                                <tr><td><b>GPU</b></td><td>{gpu_label}</td></tr>\n'
            f'                                <tr><td><b>{self._tr("help_hw_label_vram")}</b></td><td>{gpu_vram_text}</td></tr>\n'
            '                            </table>\n'
            '                        </td>\n'
            '                        <td style="width:30%; vertical-align:top;">\n'
            f'                            <div class="h2">{self._tr("help_hw_h2_usage")}</div>\n'
            '                            <table class="table">\n'
            f'                                <tr><td><b>{self._tr("help_hw_label_kraken")}</b></td><td>{self._status_chip_html(kraken_level, kraken_text)}</td></tr>\n'
            f'                                <tr><td><b>{self._tr("help_hw_label_lm")}</b></td><td>{self._status_chip_html(lm_level, lm_text)}</td></tr>\n'
            f'                                <tr><td><b>{self._tr("help_hw_label_whisper")}</b></td><td>{self._status_chip_html(whisper_level, whisper_text)}</td></tr>\n'
            '                            </table>\n'
            '                        </td>\n'
            '                        <td style="width:30%; vertical-align:top;">\n'
            f'                            <div class="h2">{self._tr("help_hw_h2_components")}</div>\n'
            '                            <table class="table">\n'
            f'                                <tr><td><b>CPU</b></td><td>{self._status_chip_html(cpu_level, cpu_text)}</td></tr>\n'
            f'                                <tr><td><b>GPU</b></td><td>{self._status_chip_html(gpu_level, gpu_text)}</td></tr>\n'
            f'                                <tr><td><b>RAM</b></td><td>{self._status_chip_html(ram_level, ram_text)}</td></tr>\n'
            '                            </table>\n'
            '                        </td>\n'
            '                    </tr>\n'
            '                </table>\n'
            '                <br>\n'
            f'                <div class="h2">{self._tr("help_hw_h2_requirements")}</div>\n'
            '                <table class="table">\n'
            f'                    <tr><td class="section">{self._tr("help_hw_col_area")}</td><td class="section">{self._tr("help_hw_col_min")}</td><td class="section">{self._tr("help_hw_col_rec")}</td></tr>\n'
            f'                    <tr><td><b>{self._tr("help_hw_label_kraken")}</b></td><td>{self._tr("help_hw_req_kraken_min")}</td><td>{self._tr("help_hw_req_kraken_rec")}</td></tr>\n'
            f'                    <tr><td><b>{self._tr("help_hw_label_lm")}</b></td><td>{self._tr("help_hw_req_lm_min")}</td><td>{self._tr("help_hw_req_lm_rec")}</td></tr>\n'
            f'                    <tr><td><b>{self._tr("help_hw_label_whisper")}</b></td><td>{self._tr("help_hw_req_whisper_min")}</td><td>{self._tr("help_hw_req_whisper_rec")}</td></tr>\n'
            f'                    <tr><td><b>{self._tr("help_hw_label_all")}</b></td><td>{self._tr("help_hw_req_all_min")}</td><td>{self._tr("help_hw_req_all_rec")}</td></tr>\n'
            '                </table>\n'
            f'                <div class="small" style="margin-top:8px;">{self._tr("help_hw_req_note")}</div>\n'
            f'                <div class="small" style="margin-top:4px;">{self._tr("help_hw_note")}</div>\n'
            '            </div>\n'
        )

    def _refresh_hw_menu_availability(self):
        caps = self._gpu_capabilities()
        for dev, act in self.hw_actions.items():
            ok, detail = caps.get(dev, (False, ""))
            if dev == "cpu":
                act.setEnabled(True)
                act.setToolTip(self._tr("msg_device_cpu"))
                continue
            act.setEnabled(ok)
            act.setToolTip(detail if detail else self._tr("msg_not_available"))

        if self.device_str != "cpu":
            ok, _ = caps.get(self.device_str, (False, ""))
            if not ok:
                self.device_str = "cpu"
                if "cpu" in self.hw_actions:
                    self.hw_actions["cpu"].setChecked(True)

    def set_device(self, dev: str):
        caps = self._gpu_capabilities()
        ok, detail = caps.get(dev, (False, ""))
        if not ok:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("msg_hw_not_available"))
            dev = "cpu"
            ok, detail = caps.get("cpu", (True, "CPU"))

        self.device_str = dev
        if dev in self.hw_actions:
            self.hw_actions[dev].setChecked(True)

        if detail:
            self.status_bar.showMessage(self._tr("msg_detected_gpu", detail))
        else:
            label_key = {
                "cpu": "msg_device_cpu",
                "cuda": "msg_device_cuda",
                "rocm": "msg_device_rocm",
                "mps": "msg_device_mps",
            }.get(dev, "msg_device_cpu")
            self.status_bar.showMessage(self._tr("msg_device", self._tr(label_key)))

    # -----------------------------
    # Drag & Drop im Hauptfenster
    # -----------------------------
    def dragEnterEvent(self, event: QDragEnterEvent):
        if not event.mimeData().hasUrls():
            event.ignore()
            return

        for u in event.mimeData().urls():
            p = u.toLocalFile()
            if p and os.path.exists(p) and is_supported_drop_or_paste_file(p):
                event.acceptProposedAction()
                return

        event.ignore()

    def dropEvent(self, event: QDropEvent):
        if not event.mimeData().hasUrls():
            event.ignore()
            return

        files = []
        for u in event.mimeData().urls():
            p = u.toLocalFile()
            if p and os.path.exists(p) and is_supported_drop_or_paste_file(p):
                files.append(p)

        if files:
            self.add_files_to_queue(files)
            event.acceptProposedAction()
        else:
            event.ignore()

    # -----------------------------
    # Wartebereich + Vorschau
    # -----------------------------
    def paste_files_from_clipboard(self):
        cb = QApplication.clipboard()
        md = cb.mimeData()

        files = []

        if md:
            # Standardfall: Explorer-Dateien als URLs
            if md.hasUrls():
                for url in md.urls():
                    p = url.toLocalFile()
                    if p and os.path.exists(p) and is_supported_drop_or_paste_file(p):
                        files.append(p)

            # Fallback: Textliste mit Dateipfaden
            if not files and md.hasText():
                raw = md.text().strip()
                if raw:
                    parts = [x.strip().strip('"') for x in raw.splitlines() if x.strip()]
                    for p in parts:
                        if os.path.exists(p) and is_supported_drop_or_paste_file(p):
                            files.append(p)

            # Windows-Fallback: rohe Mime-Formate prüfen
            if not files:
                for fmt in md.formats():
                    try:
                        data = md.data(fmt)
                        if not data:
                            continue
                        txt = bytes(data).decode("utf-8", errors="ignore").strip("\x00").strip()
                        if not txt:
                            continue

                        for candidate in re.split(r'[\r\n]+', txt):
                            candidate = candidate.strip().strip('"')
                            if os.path.exists(candidate) and is_supported_drop_or_paste_file(candidate):
                                files.append(candidate)
                    except Exception:
                        pass

        # doppelte entfernen, Reihenfolge behalten
        unique = []
        seen = set()
        for p in files:
            np = os.path.normpath(p)
            if np not in seen:
                seen.add(np)
                unique.append(p)

        if unique:
            self.add_files_to_queue(unique)
        else:
            QMessageBox.information(
                self,
                self._tr("info_title"),
                "In der Zwischenablage wurden keine unterstützten Bild-, PDF- oder Projektdateien gefunden."
            )

    def choose_files(self):
        file_filter = (
            f"{self._tr('dlg_filter_img')};;"
            f"{self._tr('dlg_filter_project')}"
        )
        files, _ = QFileDialog.getOpenFileNames(
            self,
            self._tr("dlg_load_img"),
            "",
            file_filter
        )
        if files:
            self.add_files_to_queue(files)

    def _start_pdf_render_async(self, pdf_path: str, dpi: int = 300):
        # falls schon ein PDF gerendert wird: optional blockieren oder queue’n
        if self.pdf_worker and self.pdf_worker.isRunning():
            QMessageBox.information(self, self._tr("info_title"),
                                    self._tr("msg_pdf_render_already_running"))
            return

        self._pending_pdf_path = pdf_path
        self._set_progress_busy()

        # Dialog
        dlg = QProgressDialog(self)
        dlg.setWindowTitle(self._tr("pdf_render_title"))
        dlg.setCancelButtonText(self._tr("btn_cancel"))
        dlg.setMinimum(0)
        dlg.setMaximum(0)  # wird gesetzt, sobald wir total kennen
        dlg.setValue(0)
        dlg.setAutoClose(True)
        dlg.setAutoReset(True)
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.canceled.connect(self._cancel_pdf_render)
        dlg.show()

        self.pdf_progress_dlg = dlg

        # Worker
        w = PDFRenderWorker(pdf_path, dpi=dpi, parent=self)
        w.progress.connect(self._on_pdf_render_progress)
        w.finished_pdf.connect(self._on_pdf_render_finished)
        w.failed_pdf.connect(self._on_pdf_render_failed)

        self.pdf_worker = w
        w.start()

    def _cancel_pdf_render(self):
        if self.pdf_worker and self.pdf_worker.isRunning():
            self.pdf_worker.requestInterruption()

    def _on_pdf_render_progress(self, cur: int, total: int, pdf_path: str):
        dlg = self.pdf_progress_dlg
        if dlg:
            if dlg.maximum() != max(1, total):
                dlg.setMaximum(max(1, total))
            try:
                dlg.setLabelText(self._tr("pdf_render_label", cur, total, os.path.basename(pdf_path)))
            except Exception:
                dlg.setLabelText(f"Rendering pages… ({cur}/{total}): {os.path.basename(pdf_path)}")
            dlg.setValue(cur)

        self.progress_bar.setRange(0, max(1, total))
        self.progress_bar.setValue(cur)
        self.status_bar.showMessage(self._tr("pdf_render_label", cur, total, os.path.basename(pdf_path)))

    def _on_pdf_render_finished(self, pdf_path: str, out_paths: list):
        # Dialog schließen
        if self.pdf_progress_dlg:
            self.pdf_progress_dlg.setValue(self.pdf_progress_dlg.maximum())
            self.pdf_progress_dlg.close()
            self.pdf_progress_dlg = None

        self._set_progress_idle(100)

        # Worker cleanup
        self.pdf_worker = None

        if not out_paths:
            return

        # Seiten in Queue einfügen
        added_any = False
        last_added = None
        base_name = os.path.basename(pdf_path)

        for i, img_path in enumerate(out_paths, start=1):
            if any(it.path == img_path for it in self.queue_items):
                continue
            disp = self._tr("pdf_page_display", base_name, i)
            self._add_file_to_queue_single(img_path, display_name=disp, source_kind="pdf_page")
            added_any = True
            last_added = img_path

        if added_any and last_added:
            self.preview_image(last_added)
            self._log(self._tr_log("log_added_files", len(out_paths)))

        if out_paths:
            try:
                self.temp_dirs_created.add(os.path.dirname(out_paths[0]))
            except Exception:
                pass

        self._refresh_queue_numbers()
        self._fit_queue_columns_exact()
        self._update_queue_hint()

    def _on_pdf_render_failed(self, pdf_path: str, msg: str):
        if self.pdf_progress_dlg:
            self.pdf_progress_dlg.close()
            self.pdf_progress_dlg = None

        self.pdf_worker = None
        self._set_progress_idle(0)

        QMessageBox.warning(self, self._tr("warn_title"), f"PDF konnte nicht gerendert werden:\n{msg}")

    def add_files_to_queue(self, paths: List[str]):
        added_any = False
        last_added = None
        added_count = 0

        project_files = []
        normal_files = []

        for p in paths:
            if not p or not os.path.exists(p):
                continue

            if is_project_file(p):
                project_files.append(p)
            elif is_supported_input(p):
                normal_files.append(p)

        # Projektdatei hat Vorrang
        if project_files:
            self.load_project_from_path(project_files[0])
            return

        total = len(normal_files)
        progress = None

        if total > 0:
            progress = QProgressDialog(
                self._tr("queue_load_label", 0, total, ""),
                self._tr("btn_cancel"),
                0,
                total,
                self
            )
            progress.setWindowTitle(self._tr("queue_load_title"))
            progress.setWindowModality(Qt.ApplicationModal)
            progress.setMinimumDuration(0)
            progress.setAutoClose(True)
            progress.setAutoReset(True)
            progress.setValue(0)

        try:
            for idx, p in enumerate(normal_files, start=1):
                base_name = os.path.basename(p)

                if progress is not None:
                    progress.setLabelText(self._tr("queue_load_label", idx, total, base_name))
                    progress.setValue(idx - 1)
                    QCoreApplication.processEvents()

                    if progress.wasCanceled():
                        self.status_bar.showMessage(self._tr("queue_load_cancelled"))
                        break

                ext = os.path.splitext(p)[1].lower()

                if ext == ".pdf":
                    self.status_bar.showMessage(self._tr("queue_load_pdf_started", base_name))
                    self._start_pdf_render_async(p, dpi=300)
                    added_any = True
                    added_count += 1
                else:
                    if any(it.path == p for it in self.queue_items):
                        if progress is not None:
                            progress.setValue(idx)
                        continue

                    self._add_file_to_queue_single(p)
                    added_any = True
                    last_added = p
                    added_count += 1

                if progress is not None:
                    progress.setValue(idx)
                    QCoreApplication.processEvents()

                    if progress.wasCanceled():
                        self.status_bar.showMessage(self._tr("queue_load_cancelled"))
                        break

        finally:
            if progress is not None:
                progress.close()

        if added_any and last_added:
            self.preview_image(last_added)

        if added_any:
            self._log(self._tr_log("log_added_files", added_count))

        self._fit_queue_columns_exact()
        self._update_queue_hint()

    def _add_file_to_queue_single(
            self,
            path: str,
            display_name: Optional[str] = None,
            source_kind: str = "image"
    ):
        item = TaskItem(
            path=path,
            display_name=display_name or os.path.basename(path),
            source_kind=source_kind
        )
        self.queue_items.append(item)

        row = self.queue_table.rowCount()
        self.queue_table.insertRow(row)

        num_item = QTableWidgetItem(str(row + 1))
        num_item.setTextAlignment(Qt.AlignCenter)
        num_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

        name_item = QTableWidgetItem(item.display_name)
        name_item.setData(Qt.UserRole, path)
        name_item.setFlags(
            Qt.ItemIsEnabled
            | Qt.ItemIsSelectable
            | Qt.ItemIsEditable
        )

        status_item = QTableWidgetItem(f"{STATUS_ICONS[STATUS_WAITING]} {self._tr('status_waiting')}")
        status_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

        self.queue_table.setItem(row, QUEUE_COL_NUM, num_item)
        self.queue_table.setCellWidget(row, QUEUE_COL_CHECK, self._make_queue_checkbox_widget(False))
        self.queue_table.setItem(row, QUEUE_COL_FILE, name_item)
        self.queue_table.setItem(row, QUEUE_COL_STATUS, status_item)

        self.queue_table.selectRow(row)
        self._refresh_queue_numbers()
        self._update_queue_check_header()

    def on_item_changed(self, item: QTableWidgetItem):
        if item.column() == QUEUE_COL_CHECK:
            self._update_queue_check_header()
            return

        if item.column() == QUEUE_COL_FILE:
            row = item.row()
            path_item = self.queue_table.item(row, QUEUE_COL_FILE)
            if not path_item:
                return
            path = path_item.data(Qt.UserRole)
            task_item = next((t for t in self.queue_items if t.path == path), None)
            if task_item:
                task_item.display_name = item.text()

    def open_download_link(self):
        from PySide6.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl(ZENODO_URL))

    def queue_context_menu(self, pos):
        menu = QMenu()

        start_ocr_act = menu.addAction(self._tr("act_start_ocr"))
        ai_revise_act = menu.addAction(self._tr("act_ai_revise"))
        menu.addSeparator()

        rename_act = menu.addAction(self._tr("act_rename"))
        delete_act = menu.addAction(self._tr("act_delete"))
        menu.addSeparator()

        check_all_act = menu.addAction(self._tr("queue_ctx_check_all"))
        uncheck_all_act = menu.addAction(self._tr("queue_ctx_uncheck_all"))

        action = menu.exec(self.queue_table.viewport().mapToGlobal(pos))
        if not action:
            return

        if action == start_ocr_act:
            self.start_ocr()
            return

        if action == ai_revise_act:
            self.run_ai_revision()
            return

        if action == check_all_act:
            self.check_all_queue_items()
            return
        if action == uncheck_all_act:
            self.uncheck_all_queue_items()
            return

        item = self.queue_table.itemAt(pos)
        if not item:
            return

        row = item.row()
        path = self.queue_table.item(row, QUEUE_COL_FILE).data(Qt.UserRole)
        task = next((t for t in self.queue_items if t.path == path), None)

        if action == rename_act and task:
            new_name, ok = QInputDialog.getText(
                self,
                self._tr("dlg_title_rename"),
                self._tr("dlg_label_name"),
                text=task.display_name
            )
            if ok:
                task.display_name = new_name
                self.queue_table.item(row, QUEUE_COL_FILE).setText(new_name)

        elif action == delete_act:
            self.delete_selected_queue_items()

    def check_all_queue_items(self):
        self._set_all_queue_checkmarks(True)

    def uncheck_all_queue_items(self):
        self._set_all_queue_checkmarks(False)

    def delete_selected_queue_items(self, reset_preview: bool = False):
        checked_rows = self._checked_queue_rows()

        # Priorität: Checkmarks vor Auswahl
        rows = checked_rows if checked_rows else sorted(
            set(index.row() for index in self.queue_table.selectedIndexes()),
            reverse=True
        )

        if not rows:
            return

        rows = sorted(set(rows), reverse=True)

        current_preview_path = None
        if self.queue_table.currentRow() >= 0:
            current_preview_path = self.queue_table.item(self.queue_table.currentRow(), QUEUE_COL_FILE).data(
                Qt.UserRole)

        removed_paths = []
        for row in rows:
            path = self.queue_table.item(row, QUEUE_COL_FILE).data(Qt.UserRole)
            removed_paths.append(path)
            self.queue_items = [i for i in self.queue_items if i.path != path]
            self.queue_table.removeRow(row)

        if len(self.queue_items) == 0:
            self.canvas.clear_all()
            self.canvas.set_overlay_enabled(False)
            self.list_lines.clear()
            self._set_progress_idle(0)
        else:
            if current_preview_path and current_preview_path in removed_paths:
                self.queue_table.selectRow(0)
                p = self.queue_table.item(0, QUEUE_COL_FILE).data(Qt.UserRole)
                self.preview_image(p)

        self._refresh_queue_numbers()
        self._update_queue_check_header()
        self._fit_queue_columns_exact()
        self._update_queue_hint()

        if reset_preview:
            self.canvas.clear_all()
            self.canvas.set_overlay_enabled(False)
            self.list_lines.clear()
            self._set_progress_idle(0)

    def clear_queue(self):
        self.queue_items.clear()
        self.queue_table.setRowCount(0)
        self._update_queue_check_header()
        self.canvas.clear_all()
        self.canvas.set_overlay_enabled(False)
        self.list_lines.clear()
        self._set_progress_idle(0)
        self._fit_queue_columns_exact()
        self._update_queue_hint()
        self._cleanup_temp_dirs()
        self._log(self._tr_log("log_queue_cleared"))

    def preview_image(self, path: str):
        try:
            im = Image.open(path)
            self.canvas.load_pil_image(im)
            self.list_lines.clear()

            item = next((i for i in self.queue_items if i.path == path), None)
            if item and item.status == STATUS_DONE and item.results:
                self.load_results(path)
            else:
                self.canvas.set_overlay_enabled(False)
        except Exception as e:
            QMessageBox.warning(self, self._tr("err_title"), self._tr("err_load", str(e)))

    def load_results(self, path: str):
        item = next((i for i in self.queue_items if i.path == path), None)
        if not item or not item.results:
            return

        text, kr_records, im, recs = item.results
        preview_im = _load_image_color(path)
        self.canvas.load_pil_image(preview_im)
        self.canvas.set_overlay_enabled(item.status == STATUS_DONE)

        if self.show_overlay:
            self.canvas.draw_overlays(recs)
        self._populate_lines_list(recs)

        rows = self._selected_line_rows()
        if rows:
            self.canvas.select_indices(rows, center=False)

    def _populate_lines_list(self, recs: List[RecordView], keep_row: Optional[int] = None):
        self._close_line_search_popup()
        self.list_lines.blockSignals(True)
        self.list_lines.clear()

        if self.current_theme == "dark":
            even_bg = QColor(43, 43, 43)
            odd_bg = QColor(54, 54, 54)
        else:
            even_bg = QColor(255, 255, 255)
            odd_bg = QColor(245, 245, 245)

        for i, rv in enumerate(recs):
            it = QTreeWidgetItem([f"{i + 1:04d}", rv.text])
            it.setData(0, Qt.UserRole, i)
            it.setFlags(
                Qt.ItemIsEnabled
                | Qt.ItemIsSelectable
                | Qt.ItemIsDragEnabled
                | Qt.ItemIsDropEnabled
                | Qt.ItemIsEditable
            )
            it.setTextAlignment(0, Qt.AlignCenter)

            row_bg = odd_bg if (i % 2) else even_bg
            for col in range(2):
                it.setBackground(col, QBrush(row_bg))

            self.list_lines.addTopLevelItem(it)

        self.list_lines.blockSignals(False)

        if recs:
            if keep_row is None:
                self.list_lines.setCurrentRow(0)
            else:
                self.list_lines.setCurrentRow(max(0, min(self.list_lines.count() - 1, keep_row)))

        if hasattr(self, "line_search_edit"):
            self._filter_lines_list(self.line_search_edit.text())

    def refresh_preview(self):
        if self.queue_table.currentRow() >= 0:
            path = self.queue_table.item(self.queue_table.currentRow(), QUEUE_COL_FILE).data(Qt.UserRole)
            item = next((i for i in self.queue_items if i.path == path), None)
            if item and item.status == STATUS_DONE:
                self.load_results(path)
            else:
                self.preview_image(path)

    def on_queue_double_click(self, row, col):
        path = self.queue_table.item(row, QUEUE_COL_FILE).data(Qt.UserRole)
        self.preview_image(path)

    def choose_rec_model(self):
        start_dir = self.last_rec_model_dir or KRAKEN_MODELS_DIR or os.getcwd()

        p, _ = QFileDialog.getOpenFileName(
            self,
            self._tr("dlg_choose_rec"),
            start_dir,
            self._tr("dlg_filter_model")
        )
        if p:
            self.model_path = p
            self.last_rec_model_dir = os.path.dirname(p)
            self.settings.setValue("paths/last_rec_model_dir", self.last_rec_model_dir)

            name = os.path.basename(p)
            self.btn_rec_model.setText(self._tr("btn_rec_model_value", name))
            self.status_bar.showMessage(self._tr("msg_loaded_rec", name))
            self._update_models_menu_labels()
            self._update_model_clear_buttons()

    def choose_seg_model(self):
        start_dir = self.last_seg_model_dir or KRAKEN_MODELS_DIR or os.getcwd()

        p, _ = QFileDialog.getOpenFileName(
            self,
            self._tr("dlg_choose_seg"),
            start_dir,
            self._tr("dlg_filter_model")
        )
        if p:
            self.seg_model_path = p
            self.last_seg_model_dir = os.path.dirname(p)
            self.settings.setValue("paths/last_seg_model_dir", self.last_seg_model_dir)

            name = os.path.basename(p)
            self.btn_seg_model.setText(self._tr("btn_seg_model_value", name))
            self.status_bar.showMessage(self._tr("msg_loaded_seg", name))
            self._update_models_menu_labels()
            self._update_model_clear_buttons()

    def _update_model_clear_buttons(self):
        has_rec = bool(self.model_path)
        has_seg = bool(self.seg_model_path)

        if hasattr(self, "btn_rec_clear"):
            self.btn_rec_clear.setEnabled(has_rec)
        if hasattr(self, "btn_seg_clear"):
            self.btn_seg_clear.setEnabled(has_seg)

        if hasattr(self, "act_clear_rec"):
            self.act_clear_rec.setEnabled(has_rec)
        if hasattr(self, "act_clear_seg"):
            self.act_clear_seg.setEnabled(has_seg)

    def clear_rec_model(self):
        self.model_path = ""
        self.btn_rec_model.setText(self._tr("btn_rec_model_empty"))
        self.status_bar.showMessage(self._tr("msg_loaded_rec", "-"))
        self._update_models_menu_labels()
        self._update_model_clear_buttons()

    def clear_seg_model(self):
        self.seg_model_path = ""
        self.btn_seg_model.setText(self._tr("btn_seg_model_empty"))
        self.status_bar.showMessage(self._tr("msg_loaded_seg", "-"))
        self._update_models_menu_labels()
        self._update_model_clear_buttons()

    def _log(self, msg: str):
        ts = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        line = f"[{ts}] {msg}"
        try:
            self.log_edit.appendPlainText(line)
        except Exception:
            pass

    def toggle_log_area(self, checked: bool):
        self.log_visible = bool(checked)
        self.log_edit.setVisible(self.log_visible)

        if hasattr(self, "act_toggle_log"):
            self.act_toggle_log.setChecked(checked)
            self.act_toggle_log.setText(
                self._tr("log_toggle_hide") if checked else self._tr("log_toggle_show")
            )
        if hasattr(self, "btn_toggle_log"):
            self.btn_toggle_log.setText(
                self._tr("log_toggle_hide") if checked else self._tr("log_toggle_show")
            )

    def export_log_txt(self):
        base_dir = self.current_export_dir or os.getcwd()
        dest_path, _ = QFileDialog.getSaveFileName(
            self,
            self._tr("dlg_save_log"),
            os.path.join(base_dir, "ocr_log.txt"),
            self._tr("dlg_filter_txt")
        )
        if not dest_path:
            return
        if not dest_path.lower().endswith(".txt"):
            dest_path += ".txt"

        try:
            with open(dest_path, "w", encoding="utf-8") as f:
                f.write(self.log_edit.toPlainText())
            self._log(self._tr_log("log_export_log_done", dest_path))
            self.status_bar.showMessage(self._tr("msg_exported", os.path.basename(dest_path)))
        except Exception as e:
            QMessageBox.critical(self, self._tr("err_title"), str(e))

    def _read_import_lines_file(self, file_path: str) -> List[str]:
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return [ln.strip() for ln in f.read().splitlines() if ln.strip()]

        if ext == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                if all(isinstance(x, str) for x in data):
                    return [str(x).strip() for x in data if str(x).strip()]

            if isinstance(data, dict):
                lines = data.get("lines")
                if isinstance(lines, list) and all(isinstance(x, str) for x in lines):
                    return [str(x).strip() for x in lines if str(x).strip()]

                rows = data.get("rows")
                if isinstance(rows, list):
                    out = []
                    for row in rows:
                        if isinstance(row, list):
                            txt = " ".join(str(x).strip() for x in row if str(x).strip()).strip()
                            if txt:
                                out.append(txt)
                        elif isinstance(row, str):
                            txt = row.strip()
                            if txt:
                                out.append(txt)
                    return out

        raise ValueError(self._tr("warn_import_unsupported_format", file_path))

    def _apply_imported_lines_to_task(self, task: TaskItem, lines: List[str]):
        lines = [str(x).strip() for x in lines if str(x).strip()]
        if not lines:
            raise ValueError(self._tr("warn_import_no_usable_lines"))

        if task.results:
            old_text, old_kr, old_im, old_recs = task.results

            if len(old_recs) == len(lines):
                recs = [RecordView(i, lines[i], old_recs[i].bbox) for i in range(len(lines))]
                im = old_im
                kr = old_kr
            else:
                im = _load_image_gray(task.path)
                kr = []
                recs = [RecordView(i, line, None) for i, line in enumerate(lines)]
        else:
            im = _load_image_gray(task.path)
            kr = []
            recs = [RecordView(i, line, None) for i, line in enumerate(lines)]

        text = "\n".join(lines).strip()
        task.results = (text, kr, im, recs)
        task.status = STATUS_DONE
        task.edited = True

        self._update_queue_row(task.path)

        cur = self._current_task()
        if cur and cur.path == task.path:
            self._sync_ui_after_recs_change(task, keep_row=0)
            if self.list_lines.count() > 0:
                self.list_lines.setCurrentRow(0)
                self.list_lines.setFocus()
                self.canvas.select_idx(0)

    def _match_import_files_to_tasks(self, tasks: List[TaskItem], import_files: List[str]) -> Dict[str, str]:
        file_map = {}
        for fp in import_files:
            stem = os.path.splitext(os.path.basename(fp))[0].lower()
            file_map[stem] = fp

        matches = {}
        for task in tasks:
            path_stem = os.path.splitext(os.path.basename(task.path))[0].lower()
            display_stem = os.path.splitext(task.display_name)[0].lower()

            normalized_display = (
                display_stem
                .replace(" – seite ", "_p")
                .replace(" - seite ", "_p")
                .replace(" seite ", "_p")
            )

            candidates = {
                path_stem,
                display_stem,
                normalized_display,
            }
            for c in candidates:
                if c in file_map:
                    matches[task.path] = file_map[c]
                    break
        return matches

    def import_lines_for_current_image(self):
        task = self._current_task()
        if not task:
            QMessageBox.information(self, self._tr("info_title"), self._tr("info_no_current_image_loaded"))
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self._tr("dlg_import_lines_current"),
            "",
            "Text/JSON (*.txt *.json)"
        )
        if not file_path:
            return

        try:
            lines = self._read_import_lines_file(file_path)
            self._apply_imported_lines_to_task(task, lines)
        except Exception as e:
            QMessageBox.warning(self, self._tr("warn_title"), str(e))

    def import_lines_for_selected_images(self):
        tasks = self._checked_queue_tasks()
        if not tasks:
            tasks = self._selected_queue_tasks()

        if not tasks:
            QMessageBox.information(self, self._tr("info_title"), self._tr("info_no_images_selected_or_marked"))
            return

        files, _ = QFileDialog.getOpenFileNames(
            self,
            self._tr("dlg_import_lines_selected"),
            "",
            "Text/JSON (*.txt *.json)"
        )
        if not files:
            return

        matches = self._match_import_files_to_tasks(tasks, files)

        if not matches:
            QMessageBox.warning(
                self,
                self._tr("warn_title"),
                self._tr("warn_no_matching_import_for_selected")
            )
            return

        for task in tasks:
            fp = matches.get(task.path)
            if not fp:
                continue
            try:
                lines = self._read_import_lines_file(fp)
                self._apply_imported_lines_to_task(task, lines)
            except Exception as e:
                self._log(self._tr_log("log_import_error", task.display_name, e))

    def import_lines_for_all_images(self):
        if not self.queue_items:
            QMessageBox.information(self, self._tr("info_title"), self._tr("info_no_images_loaded"))
            return

        files, _ = QFileDialog.getOpenFileNames(
            self,
            self._tr("dlg_import_lines_all"),
            "",
            "Text/JSON (*.txt *.json)"
        )
        if not files:
            return

        matches = self._match_import_files_to_tasks(self.queue_items, files)

        if not matches:
            QMessageBox.warning(
                self,
                self._tr("warn_title"),
                self._tr("warn_no_matching_import_for_loaded")
            )
            return

        for task in self.queue_items:
            fp = matches.get(task.path)
            if not fp:
                continue
            try:
                lines = self._read_import_lines_file(fp)
                self._apply_imported_lines_to_task(task, lines)
            except Exception as e:
                self._log(self._tr_log("log_import_error", task.display_name, e))

    # -----------------------------
    # OCR-Steuerung
    # -----------------------------
    def start_ocr(self):
        if not self.model_path or not os.path.exists(self.model_path):
            QMessageBox.critical(self, self._tr("err_title"), self._tr("warn_need_rec"))
            return

        if not self.seg_model_path or not os.path.exists(self.seg_model_path):
            QMessageBox.critical(self, self._tr("err_title"), self._tr("warn_blla_model_missing"))
            return

        checked_tasks = self._checked_queue_tasks()
        selected_tasks = self._selected_queue_tasks()

        # Priorität: Checkmarks vor Auswahl
        target_tasks = checked_tasks if checked_tasks else selected_tasks

        # Falls in der Queue nichts markiert/ausgewählt ist:
        # auf die aktuell geladene Datei zurückfallen,
        # damit Re-OCR nach Zeilenbearbeitung trotzdem funktioniert.
        if not target_tasks:
            current_task = self._current_task()
            if current_task and current_task.status in (STATUS_WAITING, STATUS_ERROR, STATUS_DONE):
                target_tasks = [current_task]

        if target_tasks:
            tasks = []
            for it in target_tasks:
                if it.status in (STATUS_WAITING, STATUS_ERROR, STATUS_DONE):
                    # WICHTIG:
                    # Beim normalen "Start Kraken OCR" alte Split-/Overlay-Boxen ignorieren
                    it.preset_bboxes = []

                    if it.status != STATUS_WAITING:
                        it.status = STATUS_WAITING
                        it.results = None
                        it.edited = False
                        it.undo_stack.clear()
                        it.redo_stack.clear()
                        self._update_queue_row(it.path)
                    tasks.append(it)
        else:
            tasks = [i for i in self.queue_items if i.status == STATUS_WAITING]

        if not tasks:
            QMessageBox.information(self, self._tr("info_title"), self._tr("warn_queue_empty"))
            return

        caps = self._gpu_capabilities()
        ok, _ = caps.get(self.device_str, (False, ""))
        if not ok:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("msg_hw_not_available"))
            self.device_str = "cpu"
            if "cpu" in self.hw_actions:
                self.hw_actions["cpu"].setChecked(True)

        self.act_play.setEnabled(False)
        self.act_stop.setEnabled(True)
        self._set_progress_busy()

        paths = [t.path for t in tasks]
        job = OCRJob(
            input_paths=paths,
            recognition_model_path=self.model_path,
            segmentation_model_path=self.seg_model_path,
            device=self.device_str,
            reading_direction=self.reading_direction,
            export_format="pdf",
            export_dir=self.current_export_dir,
            preset_bboxes_by_path={},  # normales Re-OCR ohne alte Split-Boxen
        )

        self.worker = OCRWorker(job)
        self.worker.file_started.connect(self.on_file_started)
        self.worker.file_done.connect(self.on_file_done)
        self.worker.file_error.connect(self.on_file_error)
        self.worker.progress.connect(self.on_progress_update)
        self.worker.finished_batch.connect(self.on_batch_finished)
        self.worker.failed.connect(self.on_failed)
        self.worker.device_resolved.connect(self.on_device_resolved)
        self.worker.gpu_info.connect(self.on_gpu_info)
        self._log(self._tr_log("log_ocr_started", len(paths), self.device_str, self.reading_direction))
        self.worker.start()

    def on_device_resolved(self, dev_str: str):
        self.status_bar.showMessage(self._tr("msg_using_device", dev_str))

    def on_gpu_info(self, info: str):
        self.status_bar.showMessage(self._tr("msg_detected_gpu", info))

    def stop_ocr(self):
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self._log(self._tr_log("log_stop_requested"))
            self.status_bar.showMessage(self._tr("msg_stopping"))

    def on_file_started(self, path):
        item = next((i for i in self.queue_items if i.path == path), None)
        if item:
            item.status = STATUS_PROCESSING
            self._update_queue_row(path)
            self._log(self._tr_log("log_file_started", os.path.basename(path)))

    def on_file_done(self, path, text, kr_records, im, recs):
        item = next((i for i in self.queue_items if i.path == path), None)
        if item:
            # Normales OCR-Ergebnis direkt übernehmen
            text = "\n".join(rv.text for rv in recs).strip()

            item.status = STATUS_DONE
            item.results = (text, kr_records, im, recs)
            item.edited = False
            item.undo_stack.clear()
            item.redo_stack.clear()
            self._update_queue_row(path)

            # nur nach erfolgreichem Anwenden leeren
            item.preset_bboxes = []

            if self.queue_table.currentRow() >= 0:
                cur_path = self.queue_table.item(self.queue_table.currentRow(), QUEUE_COL_FILE).data(Qt.UserRole)
                if cur_path == path:
                    self.load_results(path)
                    if self.list_lines.count() > 0:
                        self.list_lines.setCurrentRow(0)
                        self.list_lines.setFocus()
                        self.canvas.select_idx(0)
            self._log(self._tr_log("log_file_done", os.path.basename(path), len(recs)))

    def on_file_error(self, path, msg):
        item = next((i for i in self.queue_items if i.path == path), None)
        if item:
            item.status = STATUS_ERROR
            self._update_queue_row(path)
            self._log(self._tr_log("log_file_error", os.path.basename(path), msg))

    def on_batch_finished(self):
        self.act_play.setEnabled(True)
        self.act_stop.setEnabled(False)
        self.status_bar.showMessage(self._tr("msg_finished"))
        self.progress_bar.setValue(100)

        if self.worker:
            try:
                self.worker.deleteLater()
            except Exception:
                pass
            self.worker = None

        try:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    def on_failed(self, msg):
        QMessageBox.critical(self, self._tr("err_title"), msg)
        self.act_play.setEnabled(True)
        self.act_stop.setEnabled(False)
        self._set_progress_idle(0)

        if self.worker:
            try:
                self.worker.deleteLater()
            except Exception:
                pass
            self.worker = None

        try:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    def _update_queue_row(self, path):
        for row in range(self.queue_table.rowCount()):
            item0 = self.queue_table.item(row, QUEUE_COL_FILE)
            if item0 and item0.data(Qt.UserRole) == path:
                status_item = self.queue_table.item(row, QUEUE_COL_STATUS)
                task = next((i for i in self.queue_items if i.path == path), None)
                if task and status_item:
                    status_enum = task.status
                    status_icon = STATUS_ICONS[status_enum]
                    status_key = {
                        STATUS_WAITING: "status_waiting",
                        STATUS_PROCESSING: "status_processing",
                        STATUS_DONE: "status_done",
                        STATUS_ERROR: "status_error",
                        STATUS_AI_PROCESSING: "status_ai_processing",
                        STATUS_EXPORTING: "status_exporting",
                        STATUS_VOICE_RECORDING: "status_voice_recording",
                    }[status_enum]
                    status_item.setText(f"{status_icon} {self._tr(status_key)}")

                    if status_enum == STATUS_DONE:
                        status_item.setForeground(QBrush(QColor("green")))
                    elif status_enum == STATUS_VOICE_RECORDING:
                        status_item.setForeground(QBrush(QColor(180, 0, 180)))
                    elif status_enum == STATUS_ERROR:
                        status_item.setForeground(QBrush(QColor("red")))
                    elif status_enum == STATUS_AI_PROCESSING:
                        status_item.setForeground(QBrush(QColor(128, 0, 128)))
                    elif status_enum == STATUS_EXPORTING:
                        status_item.setForeground(QBrush(QColor(180, 120, 0)))
                    else:
                        status_item.setForeground(QBrush(QColor("blue")))

                break

    # -----------------------------
    # Zeilen + Overlays
    # -----------------------------
    def _current_task(self) -> Optional[TaskItem]:
        if self.queue_table.currentRow() < 0:
            return None
        path = self.queue_table.item(self.queue_table.currentRow(), QUEUE_COL_FILE).data(Qt.UserRole)
        return next((i for i in self.queue_items if i.path == path), None)

    def _update_task_preset_bboxes(self, task: TaskItem):
        if not task or not task.results:
            task.preset_bboxes = []
            return

        _, _, _, recs = task.results
        task.preset_bboxes = [rv.bbox for rv in recs]

    def _current_recs_for_ai(self, task: TaskItem) -> List[RecordView]:
        if not task or not task.results:
            return []

        # Sicherheitshalber die aktuell sichtbaren Canvas-Boxen zuerst ins Task-Modell ziehen
        self._persist_live_canvas_bboxes(task)

        _, _, _, recs = task.results

        out = []
        for i, rv in enumerate(recs):
            out.append(
                RecordView(
                    i,
                    rv.text,
                    tuple(rv.bbox) if rv.bbox else None
                )
            )
        return out

    def on_line_selected(self, current, previous=None):
        row = self.list_lines.currentRow()

        task = self._current_task()
        if not task or not task.results:
            return

        rows = self._selected_line_rows()
        if rows:
            self.canvas.select_indices(rows, center=False)
            return

        if row < 0:
            self.canvas.select_indices([], center=False)
            return

        _, _, _, recs = task.results
        if 0 <= row < len(recs):
            self.canvas.select_idx(row)

    def on_lines_selection_changed(self):
        task = self._current_task()
        if not task or not task.results:
            return

        rows = self._selected_line_rows()
        if not rows:
            self.canvas.select_indices([], center=False)
            return

        self.canvas.select_indices(rows, center=False)

    def on_canvas_multi_selected(self, indices: list):
        self.list_lines.blockSignals(True)
        self.list_lines.clearSelection()

        clean = sorted(set(int(i) for i in indices if i is not None))
        first = None

        for idx in clean:
            if 0 <= idx < self.list_lines.count():
                it = self.list_lines.row_item(idx)
                if it:
                    it.setSelected(True)
                    if first is None:
                        first = idx

        if first is not None:
            it = self.list_lines.row_item(first)
            if it:
                self.list_lines.setCurrentItem(it)

        self.list_lines.blockSignals(False)

        # Canvas-Farben konsistent halten
        self.canvas.select_indices(clean, center=False)

    def on_rect_clicked(self, idx):
        if 0 <= idx < self.list_lines.count():
            self.list_lines.blockSignals(True)
            self.list_lines.clearSelection()

            self.list_lines.setCurrentRow(idx)
            it = self.list_lines.row_item(idx)
            if it:
                it.setSelected(True)

            self.list_lines.blockSignals(False)

            self.canvas.select_indices([idx], center=False)
            self.list_lines.setFocus()

    @staticmethod
    def _parse_line_item_full(text: str) -> Tuple[Optional[int], str]:
        t = (text or "").rstrip("\n")
        m = re.match(r"^\s*(\d+)\s+(.*)$", t)
        if not m:
            return None, t.strip()
        num = int(m.group(1))
        rest = (m.group(2) or "").strip()
        return num - 1, rest

    def on_line_item_edited(self, item: QTreeWidgetItem, column: int):
        if column != 1:
            return

        task = self._current_task()
        if not task or not task.results or task.status != STATUS_DONE:
            return

        _, _, _, recs = task.results
        row = self.list_lines.row(item)
        if row is None or not (0 <= row < len(recs)):
            return

        new_text = (item.text(1) or "").strip()
        old_text = recs[row].text

        if new_text == old_text:
            self._sync_ui_after_recs_change(task, keep_row=row)
            return

        self._push_undo(task)
        recs[row].text = new_text
        task.edited = True
        self._sync_ui_after_recs_change(task, keep_row=row)

    def _delete_current_line_via_key(self):
        task = self._current_task()
        if not task or not task.results or task.status != STATUS_DONE:
            return
        row = self.list_lines.currentRow()
        if row >= 0:
            self._delete_line(task, row)

    def on_lines_reordered(self, order: list, current_row_after_drop: int):
        task = self._current_task()
        if not task or not task.results or task.status != STATUS_DONE:
            return

        _, _, _, recs = task.results
        if not order or len(order) != len(recs):
            return

        keep_row = max(0, min(len(recs) - 1, int(current_row_after_drop)))
        self._reorder_lines_keep_box_slots(task, order, keep_row=keep_row)

    def lines_context_menu(self, pos):
        item = self.list_lines.itemAt(pos)
        if item is None:
            return

        selected_rows = self._selected_line_rows()
        row = self.list_lines.row(item)

        menu = QMenu()
        act_swap = menu.addAction(self._tr("line_menu_swap_with"))
        menu.addSeparator()

        act_ai_single = menu.addAction(self._tr("line_menu_ai_revise_single"))
        act_ai_multi = menu.addAction(self._tr("line_menu_ai_revise_selected"))
        if len(selected_rows) < 2:
            act_ai_multi.setEnabled(False)

        menu.addSeparator()
        act_del = menu.addAction(self._tr("line_menu_delete"))
        menu.addSeparator()
        act_add_above = menu.addAction(self._tr("line_menu_add_above"))
        act_add_below = menu.addAction(self._tr("line_menu_add_below"))
        menu.addSeparator()
        act_draw = menu.addAction(self._tr("line_menu_draw_box"))

        chosen = menu.exec(self.list_lines.viewport().mapToGlobal(pos))
        if not chosen:
            return

        task = self._current_task()
        if not task or not task.results or task.status != STATUS_DONE:
            return

        _, _, _, recs = task.results
        if 0 <= row < len(recs):
            if not recs[row].bbox:
                act_ai_single.setEnabled(False)

        if chosen == act_swap:
            self._swap_line_with_dialog(task, row)
        elif chosen == act_ai_single:
            self.run_ai_revision_for_single_line(row)
        elif chosen == act_ai_multi:
            self.run_ai_revision_for_selected_lines()
        elif chosen == act_del:
            self._delete_line(task, row)
        elif chosen == act_add_above:
            self._add_line(task, insert_row=row)
        elif chosen == act_add_below:
            self._add_line(task, insert_row=row + 1)
        elif chosen == act_draw:
            self._pending_new_line_box = False
            self._pending_box_for_row = row
            self.canvas.start_draw_box_mode()

    def _sync_ui_after_recs_change(self, task: TaskItem, keep_row: Optional[int] = None):
        if not task.results:
            return
        text, kr_records, im, recs = task.results

        for i, rv in enumerate(recs):
            rv.idx = i

        new_text = "\n".join([r.text for r in recs]).strip()
        task.results = (new_text, kr_records, im, recs)

        # WICHTIG:
        # Immer den aktuellsten Box-Stand zentral synchron halten.
        self._update_task_preset_bboxes(task)

        self._populate_lines_list(recs, keep_row=keep_row)

        if os.path.exists(task.path):
            preview_im = _load_image_color(task.path)
            self.canvas.load_pil_image(preview_im, preserve_view=True)
            self.canvas.set_overlay_enabled(task.status == STATUS_DONE)
            if self.show_overlay:
                self.canvas.draw_overlays(recs)
        else:
            self.canvas.clear_all()
            self.canvas.set_overlay_enabled(False)

    def _move_line(self, task: TaskItem, row: int, direction: int):
        if not task.results:
            return

        _, _, _, recs = task.results
        new_row = row + direction

        if not (0 <= row < len(recs)) or not (0 <= new_row < len(recs)):
            return

        self._push_undo(task)
        recs[row], recs[new_row] = recs[new_row], recs[row]
        task.edited = True
        self._sync_ui_after_recs_change(task, keep_row=new_row)

    def _move_line_to_dialog(self, task: TaskItem, row: int):
        if not task.results:
            return
        _, _, _, recs = task.results
        if not (0 <= row < len(recs)):
            return

        target, ok = QInputDialog.getInt(
            self,
            self._tr("dlg_move_to_title"),
            self._tr("dlg_move_to_label"),
            row + 1,
            1,
            max(1, len(recs)),
            1
        )
        if not ok:
            return
        self._move_line_to(task, row, target - 1)

    def _move_line_to(self, task: TaskItem, from_row: int, to_row: int):
        if not task.results:
            return

        _, _, _, recs = task.results
        if not (0 <= from_row < len(recs)):
            return

        to_row = max(0, min(len(recs) - 1, int(to_row)))
        if from_row == to_row:
            self._sync_ui_after_recs_change(task, keep_row=to_row)
            return

        self._push_undo(task)
        rv = recs.pop(from_row)
        recs.insert(to_row, rv)
        task.edited = True
        self._sync_ui_after_recs_change(task, keep_row=to_row)

    def _delete_line(self, task: TaskItem, row: int):
        if not task.results:
            return

        _, _, _, recs = task.results
        if not (0 <= row < len(recs)):
            return

        self._push_undo(task)
        recs.pop(row)
        task.edited = True

        next_row = min(row, len(recs) - 1) if recs else None
        self._sync_ui_after_recs_change(task, keep_row=next_row)

    def _add_line(self, task: TaskItem, insert_row: int):
        new_text, ok = QInputDialog.getText(self, self._tr("dlg_new_line_title"), self._tr("dlg_new_line_label"))
        if not ok:
            return
        new_text = (new_text or "").strip()
        if not new_text:
            return
        text, kr_records, im, recs = task.results
        insert_row = max(0, min(len(recs), insert_row))
        self._push_undo(task)
        recs.insert(insert_row, RecordView(insert_row, new_text, None))
        task.edited = True
        self._sync_ui_after_recs_change(task, keep_row=insert_row)

        self._pending_new_line_box = False
        self._pending_box_for_row = insert_row
        self.canvas.start_draw_box_mode()

    # -----------------------------
    # Canvas-Aktionen
    # -----------------------------
    def on_canvas_select_line(self, idx: int):
        self.on_rect_clicked(idx)

    def _split_text_by_ratio(self, text: str, ratio: float) -> Tuple[str, str]:
        txt = (text or "").strip()
        if not txt:
            return "", ""

        ratio = max(0.05, min(0.95, float(ratio)))

        if " " not in txt:
            cut = max(1, min(len(txt) - 1, int(round(len(txt) * ratio))))
            return txt[:cut].strip(), txt[cut:].strip()

        words = txt.split()
        if len(words) == 1:
            return words[0], ""

        total_chars = len(" ".join(words))
        best_i = 1
        best_diff = 10 ** 9
        current_len = 0

        for i in range(1, len(words)):
            current_len = len(" ".join(words[:i]))
            current_ratio = current_len / max(1, total_chars)
            diff = abs(current_ratio - ratio)
            if diff < best_diff:
                best_diff = diff
                best_i = i

        left = " ".join(words[:best_i]).strip()
        right = " ".join(words[best_i:]).strip()
        return left, right

    def _bbox_intersection(self, a: Optional[BBox], b: Optional[BBox]) -> Tuple[int, int, int]:
        if not a or not b:
            return 0, 0, 0

        ax0, ay0, ax1, ay1 = a
        bx0, by0, bx1, by1 = b

        ix0 = max(ax0, bx0)
        iy0 = max(ay0, by0)
        ix1 = min(ax1, bx1)
        iy1 = min(ay1, by1)

        if ix1 <= ix0 or iy1 <= iy0:
            return 0, 0, 0

        iw = ix1 - ix0
        ih = iy1 - iy0
        return iw * ih, iw, ih

    def _split_text_by_multiple_ratios(self, text: str, ratios: List[float]) -> List[str]:
        txt = (text or "").strip()
        if not txt:
            return [""] * (len(ratios) + 1)

        words = txt.split()
        if len(words) <= 1:
            parts = [""] * (len(ratios) + 1)
            if parts:
                parts[0] = txt
            return parts

        ratios = [max(0.0, min(1.0, float(r))) for r in ratios]
        ratios = sorted(ratios)

        total_words = len(words)
        cut_indices = []

        for r in ratios:
            cut = int(round(total_words * r))
            cut = max(1, min(total_words - 1, cut))
            cut_indices.append(cut)

        # doppelte Schnittstellen bereinigen
        clean_cuts = []
        last = 0
        for cut in cut_indices:
            cut = max(last + 1, cut)
            cut = min(total_words - 1, cut)
            if clean_cuts and cut <= clean_cuts[-1]:
                continue
            clean_cuts.append(cut)
            last = cut

        out = []
        start = 0
        for cut in clean_cuts:
            out.append(" ".join(words[start:cut]).strip())
            start = cut
        out.append(" ".join(words[start:]).strip())

        while len(out) < len(ratios) + 1:
            out.append("")

        return out

    def _reapply_preset_bboxes_to_recs(
            self,
            recs: List[RecordView],
            preset_bboxes: List[Optional[BBox]]
    ) -> List[RecordView]:
        if not preset_bboxes:
            return recs

        # Einfacher Fall: gleiche Anzahl -> nur Boxen ersetzen
        if len(preset_bboxes) == len(recs):
            out = []
            for i, rv in enumerate(recs):
                out.append(RecordView(i, rv.text, preset_bboxes[i]))
            return out

        target_texts = [""] * len(preset_bboxes)

        for rv in recs:
            if not rv.bbox:
                continue

            overlaps = []
            for pi, pbb in enumerate(preset_bboxes):
                area, iw, ih = self._bbox_intersection(rv.bbox, pbb)
                if area > 0:
                    overlaps.append((pi, area, iw, ih, pbb))

            if not overlaps:
                continue

            overlaps.sort(key=lambda x: x[0])

            # genau ein Ziel -> ganzer Text dorthin
            if len(overlaps) == 1:
                pi = overlaps[0][0]
                target_texts[pi] = (target_texts[pi] + " " + rv.text).strip()
                continue

            # mehrere Zielboxen -> Text proportional aufteilen
            # bevorzugt horizontal (typischer Split links/rechts)
            total_iw = sum(x[2] for x in overlaps)
            total_ih = sum(x[3] for x in overlaps)

            if total_iw >= total_ih:
                weights = [x[2] for x in overlaps]
            else:
                weights = [x[3] for x in overlaps]

            weight_sum = max(1, sum(weights))
            cum = 0.0
            ratios = []
            for w in weights[:-1]:
                cum += w / weight_sum
                ratios.append(cum)

            parts = self._split_text_by_multiple_ratios(rv.text, ratios)

            for part, ov in zip(parts, overlaps):
                pi = ov[0]
                if part.strip():
                    target_texts[pi] = (target_texts[pi] + " " + part.strip()).strip()

        # Falls irgendwo nichts gelandet ist, leeren String behalten
        out = []
        for i, pbb in enumerate(preset_bboxes):
            out.append(RecordView(i, target_texts[i].strip(), pbb))

        return out

    def _ensure_overlay_possible(self) -> Optional[TaskItem]:
        task = self._current_task()
        if not task or not task.results or task.status != STATUS_DONE:
            QMessageBox.information(self, self._tr("info_title"), self._tr("overlay_only_after_ocr"))
            return None
        return task

    def on_canvas_add_box_draw(self, scene_pos: QPointF):
        # NEUES VERHALTEN: Eine neue Overlay-Box erzeugt eine NEUE Zeile am Ende.
        task = self._ensure_overlay_possible()
        if not task:
            return
        _, _, _, recs = task.results
        if recs is None:
            return

        self._pending_box_for_row = None
        self._pending_new_line_box = True
        self.canvas.start_draw_box_mode()

    def on_canvas_edit_box(self, idx: int):
        task = self._ensure_overlay_possible()
        if not task:
            return
        _, _, im, recs = task.results
        if not im:
            return
        if not (0 <= idx < len(recs)):
            return
        img_w, img_h = im.size
        dlg = OverlayBoxDialog(self._tr, img_w, img_h, bbox=recs[idx].bbox, parent=self)
        if dlg.exec() != QDialog.Accepted:
            return
        self._push_undo(task)
        recs[idx].bbox = dlg.get_bbox()
        task.edited = True
        self._sync_ui_after_recs_change(task, keep_row=idx)

    def on_canvas_delete_box(self, idx: int):
        task = self._ensure_overlay_possible()
        if not task:
            return
        _, _, _, recs = task.results
        if not (0 <= idx < len(recs)):
            return
        self._push_undo(task)
        recs[idx].bbox = None
        task.edited = True
        self._sync_ui_after_recs_change(task, keep_row=idx)
        self._update_task_preset_bboxes(task)

    def on_canvas_split_box(self, idx: int, split_x: float):
        task = self._ensure_overlay_possible()
        if not task:
            return

        _, _, _, recs = task.results
        if not (0 <= idx < len(recs)):
            return

        rv = recs[idx]
        if not rv.bbox:
            return

        x0, y0, x1, y1 = rv.bbox
        split_x = int(round(split_x))
        split_x = max(x0 + 8, min(x1 - 8, split_x))

        if split_x <= x0 or split_x >= x1:
            return

        ratio = (split_x - x0) / max(1, (x1 - x0))
        left_text, right_text = self._split_text_by_ratio(rv.text, ratio)

        left_box = (x0, y0, split_x, y1)
        right_box = (split_x, y0, x1, y1)

        self._push_undo(task)

        rtl = self.reading_direction in (
            READING_MODES["TB_RL"],
            READING_MODES["BT_RL"],
        )

        if rtl:
            new_items = [
                RecordView(idx, right_text, right_box),
                RecordView(idx + 1, left_text, left_box),
            ]
        else:
            new_items = [
                RecordView(idx, left_text, left_box),
                RecordView(idx + 1, right_text, right_box),
            ]

        recs[idx:idx + 1] = new_items
        task.edited = True

        self._sync_ui_after_recs_change(task, keep_row=idx)
        self._update_task_preset_bboxes(task)

    # -----------------------------
    # Box drawing result
    # -----------------------------
    def on_box_drawn(self, rect: QRectF):
        task = self._ensure_overlay_possible()
        if not task:
            return

        text, kr_records, im, recs = task.results

        x0 = _safe_int(rect.left())
        y0 = _safe_int(rect.top())
        x1 = _safe_int(rect.right())
        y1 = _safe_int(rect.bottom())
        x0, y0, x1, y1 = min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)

        if im:
            img_w, img_h = im.size
            x0, y0 = max(0, min(img_w - 1, x0)), max(0, min(img_h - 1, y0))
            x1, y1 = max(1, min(img_w, x1)), max(1, min(img_h, y1))
            if x1 <= x0:
                x1 = min(img_w, x0 + 1)
            if y1 <= y0:
                y1 = min(img_h, y0 + 1)

        # Fall A: Neue Zeile am Ende erzeugen (Canvas-Zeichnen)
        if self._pending_new_line_box:
            self._pending_new_line_box = False
            self._pending_box_for_row = None

            # Optional: Text abfragen (optional) – der Nutzer kann ihn später auch in der Liste bearbeiten.
            new_txt, ok = QInputDialog.getText(self, self._tr("new_line_from_box_title"),
                                               self._tr("new_line_from_box_label"))
            if not ok:
                new_txt = ""
            new_txt = (new_txt or "").strip()

            self._push_undo(task)
            recs.append(RecordView(len(recs), new_txt, (x0, y0, x1, y1)))
            task.edited = True
            self._sync_ui_after_recs_change(task, keep_row=len(recs) - 1)
            self._update_task_preset_bboxes(task)
            self.list_lines.setFocus()
            return

        # Fall B: Box für eine bestimmte existierende Zeile zeichnen (Zeilen-Kontextmenü)
        if self._pending_box_for_row is None:
            return

        row = self._pending_box_for_row
        self._pending_box_for_row = None

        if not (0 <= row < len(recs)):
            return

        self._push_undo(task)
        recs[row].bbox = (x0, y0, x1, y1)
        task.edited = True
        self._sync_ui_after_recs_change(task, keep_row=row)
        self._update_task_preset_bboxes(task)

    def on_overlay_rect_changed(self, idx: int, scene_rect: QRectF):
        task = self._ensure_overlay_possible()
        if not task:
            return

        text, kr_records, im, recs = task.results
        if not (0 <= idx < len(recs)):
            return

        new_bbox = self._scene_rect_to_bbox(scene_rect, im)
        if not new_bbox:
            return

        old_bbox = recs[idx].bbox
        if old_bbox == new_bbox:
            return

        self._push_undo(task)

        recs[idx].bbox = new_bbox
        task.edited = True
        task.results = (
            "\n".join(r.text for r in recs).strip(),
            kr_records,
            im,
            recs
        )

        self._update_task_preset_bboxes(task)

        # Label der Box direkt mitziehen, ohne kompletten Canvas-Neuaufbau
        lab = self.canvas._labels.get(idx)
        if lab and isValid(lab):
            x0, y0, x1, y1 = new_bbox
            lab.setPos(x0, max(0, y0 - 16))

    # -----------------------------
    # Overlay umschalten
    # -----------------------------
    def _on_overlay_toggled(self, checked):
        self.show_overlay = checked
        self.refresh_preview()

    # -----------------------------
    # Export
    # -----------------------------

    def on_export_file_started(self, display_name: str, current: int, total: int):
        task = next((i for i in self.queue_items if i.display_name == display_name), None)
        if task:
            task.status = STATUS_EXPORTING
            self._update_queue_row(task.path)

    def export_flow(self, fmt: str):
        checked_tasks = self._checked_queue_tasks()
        selected_tasks = self._selected_queue_tasks()

        # Priorität: Checkmarks vor Auswahl
        target_tasks = checked_tasks if checked_tasks else selected_tasks

        if target_tasks:
            # genau 1 Datei -> normaler "Speichern unter"-Dialog
            if len(target_tasks) == 1:
                it = target_tasks[0]
                if it.status != STATUS_DONE or not it.results:
                    QMessageBox.warning(self, self._tr("warn_title"), self._tr("export_need_done"))
                    return
                self._export_single_interactive(it, fmt)
                return

            # mehrere Dateien -> Batch-Export in Ordner
            items = []
            for it in target_tasks:
                if it.status != STATUS_DONE or not it.results:
                    QMessageBox.warning(self, self._tr("warn_title"), self._tr("export_need_done"))
                    return
                items.append(it)

            self._export_batch(items, fmt)
            return

        if len(self.queue_items) == 0:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_queue_empty"))
            return

        if len(self.queue_items) == 1:
            it = self.queue_items[0]
            if it.status != STATUS_DONE or not it.results:
                QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_select_done"))
                return
            self._export_single_interactive(it, fmt)
            return

        dlg = ExportModeDialog(self._tr, self)
        if dlg.exec() != QDialog.Accepted or dlg.choice is None:
            return

        if dlg.choice == "all":
            items = [it for it in self.queue_items if it.status == STATUS_DONE and it.results]
            if len(items) != len(self.queue_items):
                QMessageBox.warning(self, self._tr("warn_title"), self._tr("export_need_done"))
                return
            self._export_batch(items, fmt)
            return

        sel_dlg = ExportSelectFilesDialog(self._tr, self.queue_items, self)
        if sel_dlg.exec() != QDialog.Accepted:
            return

        paths = sel_dlg.selected_paths
        if not paths:
            QMessageBox.information(self, self._tr("info_title"), self._tr("export_none_selected"))
            return

        items = []
        for p in paths:
            it = next((x for x in self.queue_items if x.path == p), None)
            if not it or it.status != STATUS_DONE or not it.results:
                QMessageBox.warning(self, self._tr("warn_title"), self._tr("export_need_done"))
                return
            items.append(it)

        if len(items) == 1:
            self._export_single_interactive(items[0], fmt)
        else:
            self._export_batch(items, fmt)

    def _export_single_interactive(self, item: TaskItem, fmt: str):
        base_name = os.path.splitext(item.display_name)[0]
        base_dir = self.current_export_dir or os.path.dirname(item.path)

        filters = {
            "txt": "Text (*.txt)",
            "csv": "CSV (*.csv)",
            "json": "JSON (*.json)",
            "alto": "XML (*.xml)",
            "hocr": "HTML (*.html)",
            "pdf": "PDF (*.pdf)"
        }

        dest_path, _ = QFileDialog.getSaveFileName(
            self,
            self._tr("dlg_save"),
            os.path.join(base_dir, base_name),
            filters.get(fmt, "All (*.*)")
        )
        if not dest_path:
            return
        if not dest_path.lower().endswith(f".{fmt}"):
            dest_path += f".{fmt}"

        try:
            self._render_file(dest_path, fmt, item)
        except PermissionError:
            QMessageBox.warning(
                self,
                self._tr("warn_title"),
                f"Die Datei kann nicht geschrieben werden:\n\n{dest_path}\n\n"
                "Möglicherweise ist sie noch in einem anderen Programm geöffnet."
            )
            return
        except Exception as e:
            QMessageBox.critical(self, self._tr("err_title"), str(e))
            return

        self._log(self._tr_log("log_export_single", item.display_name, dest_path))
        self.status_bar.showMessage(self._tr("msg_exported", os.path.basename(dest_path)))

    def _export_batch(self, items: List[TaskItem], fmt: str):
        folder = QFileDialog.getExistingDirectory(
            self,
            self._tr("export_choose_folder"),
            self.current_export_dir or ""
        )
        if not folder:
            return

        self.current_export_dir = folder

        self._current_export_count = len(items)
        self._current_export_format = fmt

        self.export_dialog = ProgressStatusDialog(f"Export {fmt.upper()}", self)
        self.export_dialog.set_status("Bereite Export vor…")
        self.export_dialog.cancel_requested.connect(self._cancel_export_batch)
        self.export_dialog.show()

        self.export_worker = ExportWorker(
            render_callback=self._render_file,
            items=items,
            fmt=fmt,
            folder=folder,
            parent=self
        )
        self.export_worker.status_changed.connect(self.export_dialog.set_status)
        self.export_worker.progress_changed.connect(self.export_dialog.set_progress)
        self.export_worker.file_done.connect(self.on_export_file_done)
        self.export_worker.file_started.connect(self.on_export_file_started)
        self.export_worker.file_error.connect(self.on_export_file_error)
        self.export_worker.finished_batch.connect(self.on_export_batch_finished)
        self.export_worker.start()

    def _cancel_export_batch(self):
        if self.export_worker and self.export_worker.isRunning():
            self.export_worker.requestInterruption()

    def on_export_file_done(self, display_name: str, dest_path: str, current: int, total: int):
        task = next((i for i in self.queue_items if i.display_name == display_name), None)
        if task:
            task.status = STATUS_DONE
            self._update_queue_row(task.path)

        self._log(self._tr_log("log_export_single", display_name, dest_path))

    def on_export_file_error(self, display_name: str, msg: str, current: int, total: int):
        task = next((i for i in self.queue_items if i.display_name == display_name), None)
        if task:
            task.status = STATUS_ERROR
            self._update_queue_row(task.path)

        self._log(f"Export-Fehler: {display_name} -> {msg}")

    def on_export_batch_finished(self):
        if self.export_dialog:
            self.export_dialog.close()
            self.export_dialog = None

        self.status_bar.showMessage(self._tr("msg_exported", self.current_export_dir))
        self._log(
            self._tr_log(
                "log_export_done",
                getattr(self, "_current_export_count", 0),
                getattr(self, "_current_export_format", "?"),
                self.current_export_dir
            )
        )

    def _build_kraken_segmentation_for_export(
            self,
            image_path: str,
            record_views: List[RecordView]
    ):
        export_lines = []

        for i, rv in enumerate(record_views):
            if not rv.bbox:
                continue

            x0, y0, x1, y1 = rv.bbox

            export_lines.append(
                containers.BBoxLine(
                    id=f"line_{i + 1:04d}",
                    bbox=(int(x0), int(y0), int(x1), int(y1)),
                    text=str(rv.text or ""),
                    base_dir=None,
                    imagename=image_path,
                    regions=None,
                    tags=None,
                    split=None,
                    text_direction="horizontal-lr",
                )
            )

        if not export_lines:
            return None

        return containers.Segmentation(
            type="bbox",
            imagename=image_path,
            text_direction="horizontal-lr",
            script_detection=False,
            lines=export_lines,
            regions=None,
            line_orders=None,
        )

    def _render_hocr_html(self, path: str, item: TaskItem, export_image: Image.Image, record_views: List[RecordView]):
        buf = BytesIO()
        export_image.save(buf, format="PNG")
        img_b64 = base64.b64encode(buf.getvalue()).decode("ascii")

        width, height = export_image.size
        page_name = html.escape(os.path.basename(item.path))

        line_blocks = []

        for i, rv in enumerate(record_views):
            if not rv.bbox:
                continue

            x0, y0, x1, y1 = rv.bbox
            w = max(1, x1 - x0)
            h = max(1, y1 - y0)
            txt = html.escape(rv.text or "")

            line_blocks.append(f"""
            <span class="ocr_line"
                  id="line_{i + 1:04d}"
                  title="bbox {x0} {y0} {x1} {y1}"
                  style="left:{x0}px; top:{y0}px; width:{w}px; height:{h}px;">
                <span class="ocrx_word"
                      id="word_{i + 1:04d}"
                      title="bbox {x0} {y0} {x1} {y1}">{txt}</span>
            </span>
            """)

        html_doc = f"""<!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <meta name="ocr-system" content="Bottled Kraken">
    <meta name="ocr-capabilities" content="ocr_page ocr_line ocrx_word">
    <title>{page_name}</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background: #f3f3f3;
            font-family: Arial, sans-serif;
        }}

        .page-wrap {{
            display: inline-block;
            position: relative;
            box-shadow: 0 2px 16px rgba(0,0,0,0.18);
            background: white;
        }}

        .ocr_page {{
            position: relative;
            width: {width}px;
            height: {height}px;
            overflow: hidden;
            background: white;
        }}

        .ocr_page img {{
            position: absolute;
            left: 0;
            top: 0;
            width: {width}px;
            height: {height}px;
            display: block;
        }}

        .ocr_line {{
            position: absolute;
            box-sizing: border-box;
            border: 1px solid rgba(220, 38, 38, 0.45);
            background: rgba(255, 255, 255, 0.10);
            overflow: hidden;
            white-space: nowrap;
        }}

        .ocrx_word {{
            position: absolute;
            left: 0;
            top: 0;
            font-size: 12px;
            line-height: 1.1;
            color: rgba(180, 0, 0, 0.92);
            background: rgba(255, 255, 255, 0.55);
            padding: 0 2px;
        }}
    </style>
    </head>
    <body>
    <div class="page-wrap">
        <div class="ocr_page" title="image {page_name}; bbox 0 0 {width} {height}">
            <img src="data:image/png;base64,{img_b64}" alt="{page_name}">
            {''.join(line_blocks)}
        </div>
    </div>
    </body>
    </html>
    """

        with open(path, "w", encoding="utf-8") as f:
            f.write(html_doc)

    def _render_file(self, path: str, fmt: str, item: TaskItem):
        if not item.results:
            return

        text, kr_records, pil_image, record_views = item.results
        export_image = _load_image_color(item.path)

        if fmt == "txt":
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join([rv.text for rv in record_views]).strip())
            return

        grid = table_to_rows(record_views, pil_image.size[0]) if any(rv.bbox for rv in record_views) else [
            [rv.text] for rv in record_views
        ]

        if fmt == "csv":
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerows(grid)
            return

        if fmt == "json":
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"rows": grid}, f, indent=2, ensure_ascii=False)
            return

        if fmt == "alto":
            seg_result = self._build_kraken_segmentation_for_export(
                image_path=item.path,
                record_views=record_views
            )

            if seg_result is None:
                raise ValueError("ALTO-Export benötigt Zeilen mit Bounding-Boxen.")

            xml = serialization.serialize(
                seg_result,
                image_size=export_image.size,
                template="alto"
            )

            with open(path, "w", encoding="utf-8") as f:
                f.write(xml)
            return

        if fmt == "hocr":
            self._render_hocr_html(path, item, export_image, record_views)
            return

        if fmt == "pdf":
            width, height = export_image.size
            c = pdf_canvas.Canvas(path, pagesize=(width, height))
            c.drawImage(ImageReader(export_image), 0, 0, width=width, height=height)

            for rv in record_views:
                if not rv.bbox or not rv.text.strip():
                    continue
                x0, y0, x1, y1 = rv.bbox
                t = rv.text
                box_h = max(1, y1 - y0)
                box_w = max(1, x1 - x0)
                font_size = max(6, min(24, box_h * 0.8))
                c.setFont("Helvetica", font_size)
                pdf_y = height - y1
                text_w = c.stringWidth(t, "Helvetica", font_size)
                scale_x = box_w / text_w if text_w > 0 else 1.0
                c.saveState()
                c.translate(x0, pdf_y)
                c.scale(scale_x, 1.0)
                c.setFillAlpha(0)
                c.drawString(0, 0, t)
                c.restoreState()

            try:
                c.save()
            except PermissionError as e:
                raise PermissionError(
                    f"PDF konnte nicht gespeichert werden:\n{path}\n\n"
                    "Die Datei ist wahrscheinlich noch geöffnet oder durch ein anderes Programm gesperrt."
                ) from e
            return

    def _app_base_dir(self) -> str:
        if getattr(sys, "frozen", False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(sys.argv[0]))

    def _default_whisper_base_dir(self) -> str:
        home = os.path.expanduser("~")

        if sys.platform.startswith("win"):
            base = os.path.join(home, "BottledKraken", "whisper")
        elif sys.platform == "darwin":
            base = os.path.join(home, "Library", "Application Support", "BottledKraken", "whisper")
        else:
            base = os.path.join(home, ".local", "share", "BottledKraken", "whisper")

        os.makedirs(base, exist_ok=True)
        return base

    def _default_whisper_model_dir(self) -> str:
        return os.path.join(self._default_whisper_base_dir(), "faster-whisper-large-v3")

    def _hf_cli_executable(self, platform_name: str) -> str:
        """
        Liefert den hf-CLI-Pfad passend zur Python-Umgebung.
        Unter Windows bevorzugt <python>\\Scripts\\hf.exe
        """
        name = (platform_name or "").strip().lower()

        if name == "windows":
            py_dir = os.path.dirname(sys.executable)
            candidates = [
                os.path.join(py_dir, "Scripts", "hf.exe"),
                os.path.join(py_dir, "hf.exe"),
                "hf",
            ]
            for c in candidates:
                if c == "hf" or os.path.exists(c):
                    return c
            return "hf"

        # Linux/macOS: CLI aus der venv
        venv_dir = self._whisper_venv_dir()
        candidates = [
            os.path.join(venv_dir, "bin", "hf"),
            "hf",
        ]
        for c in candidates:
            if c == "hf" or os.path.exists(c):
                return c
        return "hf"

    def _whisper_venv_dir(self) -> str:
        return os.path.join(self._default_whisper_base_dir(), ".venv")

    def _whisper_venv_python_path(self, platform_name: str) -> str:
        name = (platform_name or "").strip().lower()
        venv_dir = self._whisper_venv_dir()

        if name == "windows":
            return os.path.join(venv_dir, "Scripts", "python.exe")

        return os.path.join(venv_dir, "bin", "python3")

    def _whisper_button_commands(self, platform_name: str) -> Tuple[str, str]:
        """
        Nur für die Anzeige im Hinweise-Dialog.
        Zeigt dem Nutzer die Befehle, die dem echten Ablauf entsprechen.
        """
        name = (platform_name or "").strip().lower()
        model_dir = self._default_whisper_model_dir().replace("\\", "/")
        venv_dir = self._whisper_venv_dir().replace("\\", "/")
        venv_python = self._whisper_venv_python_path(platform_name).replace("\\", "/")

        if name == "windows":
            hf_exe = self._hf_cli_executable(platform_name).replace("\\", "/")
            install_cmd = (
                f'"{sys.executable}" -m pip install -U pip setuptools wheel '
                f'huggingface_hub faster-whisper sounddevice'
            )
            download_cmd = (
                f'"{hf_exe}" download Systran/faster-whisper-large-v3 '
                f'--local-dir "{model_dir}"'
            )
            return install_cmd, download_cmd

        # Linux / macOS: immer venv verwenden
        install_cmd = (
            f'python3 -m venv "{venv_dir}"\n'
            f'"{venv_python}" -m pip install -U pip setuptools wheel huggingface_hub faster-whisper sounddevice'
        )
        download_cmd = (
            f'"{venv_python}" -m huggingface_hub download '
            f'Systran/faster-whisper-large-v3 --local-dir "{model_dir}"'
        )
        return install_cmd, download_cmd

    def _whisper_system_hint(self, platform_name: str) -> str:
        name = (platform_name or "").strip().lower()

        if name in ("debian", "ubuntu", "linux mint", "mint"):
            return self._tr("whisper_hint_debian")

        if name == "fedora":
            return self._tr("whisper_hint_fedora")

        if name == "arch":
            return self._tr("whisper_hint_arch")

        if name in ("mac", "macos", "darwin"):
            return self._tr("whisper_hint_macos")

        if name == "windows":
            return self._tr("whisper_hint_windows")

        return self._tr("whisper_hint_generic")

    def download_whisper_model_from_help_dialog(self, platform_name: str, dialog_parent=None):
        # 1) zuerst prüfen, ob large-v3 schon vorhanden ist
        existing_model_dir = self._find_existing_whisper_large_v3_model()
        if existing_model_dir:
            base_dir = os.path.dirname(existing_model_dir)

            self.whisper_models_base_dir = self._normalize_whisper_base_dir(base_dir)
            self.settings.setValue("paths/whisper_models_base_dir", self.whisper_models_base_dir)

            self._scan_whisper_models()
            self._set_whisper_model(existing_model_dir)
            self._update_whisper_menu_status()

            QMessageBox.information(
                dialog_parent or self,
                self._tr("info_title"),
                "Das Faster-Whisper large-v3 Modell ist bereits vorhanden.\n\n"
                f"Pfad:\n{existing_model_dir}\n\n"
                "Ein erneuter Download ist nicht nötig."
            )
            self.status_bar.showMessage(self._tr("msg_whisper_model_already_present", existing_model_dir))
            return

        platform_hint = self._whisper_system_hint(platform_name)

        QMessageBox.information(
            dialog_parent or self,
            self._tr("info_title"),
            "Optionaler Systemhinweis:\n\n"
            f"{platform_hint}\n\n"
            "Der eigentliche Download läuft trotzdem nur über Python "
            "(sys.executable -m pip / Python-API von huggingface_hub)."
        )

        # Prüfen, ob bereits ein Download läuft
        if self.hf_download_worker and self.hf_download_worker.isRunning():
            if self.hf_download_dialog is not None:
                self.hf_download_dialog.show()
                self.hf_download_dialog.raise_()
                self.hf_download_dialog.activateWindow()

            QMessageBox.information(
                dialog_parent or self,
                self._tr("info_title"),
                self._tr("warn_whisper_download_running")
            )
            return

        target_base = self._default_whisper_base_dir()
        target_model_dir = self._default_whisper_model_dir()

        try:
            os.makedirs(target_base, exist_ok=True)

            self.status_bar.showMessage(
                self._tr("msg_whisper_download_prepare_target", target_model_dir)
            )

            self.hf_download_dialog = ProgressStatusDialog(
                self._tr("dlg_whisper_download_title"),
                self._tr,
                dialog_parent or self
            )
            self.hf_download_dialog.set_status(self._tr("dlg_whisper_download_prepare"))
            self.hf_download_dialog.set_progress(0)
            self.hf_download_dialog.show()
            self.hf_download_dialog.raise_()
            self.hf_download_dialog.activateWindow()

            platform_key = (
                "windows" if sys.platform.startswith("win")
                else "mac" if sys.platform == "darwin"
                else "linux"
            )

            venv_dir = self._whisper_venv_dir()
            venv_python = self._whisper_venv_python_path(platform_key)

            if platform_key == "windows":
                # Windows: direkt in der laufenden Python-Umgebung arbeiten
                prepare_cmds = []

                install_cmd = [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "-U",
                    "pip",
                    "setuptools",
                    "wheel",
                    "huggingface_hub",
                    "faster-whisper",
                    "sounddevice",
                ]

                hf_exe = self._hf_cli_executable(platform_key)

                download_cmd = [
                    hf_exe,
                    "download",
                    "Systran/faster-whisper-large-v3",
                    "--local-dir",
                    target_model_dir,
                ]
            else:
                # Linux / macOS: weiter mit venv
                prepare_cmds = [
                    [sys.executable, "-m", "venv", venv_dir],
                ]

                install_cmd = [
                    venv_python,
                    "-m",
                    "pip",
                    "install",
                    "-U",
                    "pip",
                    "setuptools",
                    "wheel",
                    "huggingface_hub",
                    "faster-whisper",
                    "sounddevice",
                ]

                hf_exe = self._hf_cli_executable(platform_key)

                download_cmd = [
                    hf_exe,
                    "download",
                    "Systran/faster-whisper-large-v3",
                    "--local-dir",
                    target_model_dir,
                ]

            self.hf_download_worker = HFDownloadWorker(
                repo_id="Systran/faster-whisper-large-v3",
                local_dir=target_model_dir,
                prepare_cmds=prepare_cmds,
                install_cmd=install_cmd,
                download_cmd=download_cmd,
                tr_func=self._tr,
                parent=self
            )
            self.hf_download_worker.progress_changed.connect(self.hf_download_dialog.set_progress)
            self.hf_download_worker.status_changed.connect(self.hf_download_dialog.set_status)
            self.hf_download_worker.finished_download.connect(self.on_hf_download_finished)
            self.hf_download_worker.failed_download.connect(self.on_hf_download_failed)
            self.hf_download_dialog.cancel_requested.connect(self.hf_download_worker.cancel)
            self.hf_download_worker.start()

        except Exception as e:
            QMessageBox.warning(
                self,
                self._tr("warn_title"),
                f"Download des Whisper-Modells konnte nicht gestartet werden:\n{e}"
            )
            self.status_bar.showMessage(self._tr("msg_whisper_download_start_failed"))

    def on_hf_download_finished(self, local_dir: str):
        self.status_bar.showMessage(self._tr("msg_whisper_model_loaded", local_dir))

        self.whisper_models_base_dir = self._normalize_whisper_base_dir(os.path.dirname(local_dir))
        self._scan_whisper_models()

        if os.path.isfile(os.path.join(local_dir, "model.bin")):
            self._set_whisper_model(local_dir)

        self._update_whisper_menu_status()
        self.settings.setValue("paths/whisper_models_base_dir", self.whisper_models_base_dir)
        if hasattr(self, "hf_download_dialog") and self.hf_download_dialog:
            self.hf_download_dialog.set_progress(100)
            self.hf_download_dialog.hide()
            self.hf_download_dialog.close()
            self.hf_download_dialog = None

        self.hf_download_worker = None

        QMessageBox.information(
            self,
            self._tr("info_title"),
            "Das Faster-Whisper-Modell wurde erfolgreich heruntergeladen.\n\n"
            f"Zielordner:\n{local_dir}"
        )

    def on_hf_download_failed(self, msg: str):
        self.status_bar.showMessage(self._tr("msg_whisper_download_failed"))

        if hasattr(self, "hf_download_dialog") and self.hf_download_dialog:
            self.hf_download_dialog.hide()
            self.hf_download_dialog.close()
            self.hf_download_dialog = None

        self.hf_download_worker = None

        QMessageBox.warning(
            self,
            self._tr("warn_title"),
            f"Download des Whisper-Modells fehlgeschlagen:\n{msg}"
        )
    def show_lm_help_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle(self._tr("dlg_help_title"))
        dlg.resize(1380, 860)
        dlg.setMinimumSize(1240, 760)
        dlg.setStyleSheet(_help_dialog_qss(self.current_theme))

        layout = QVBoxLayout(dlg)

        scroll = QScrollArea(dlg)
        scroll.setWidgetResizable(True)

        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(6, 6, 6, 6)
        content_layout.setSpacing(10)

        default_install_cmd, default_download_cmd = self._whisper_button_commands("Windows")

        def _small_btn(text: str) -> QPushButton:
            button = QPushButton(text)
            button.setFixedHeight(30)
            button.setMinimumWidth(82)
            button.setMaximumWidth(110)
            button.setCursor(Qt.PointingHandCursor)
            return button

        def make_page(content_html: str) -> QTextBrowser:
            browser = QTextBrowser()
            browser.setReadOnly(True)
            browser.setOpenExternalLinks(True)
            browser.setFrameShape(QTextBrowser.NoFrame)
            browser.setOpenLinks(False)
            browser.anchorClicked.connect(QDesktopServices.openUrl)
            browser.setHtml(_help_html(self.current_theme, content_html))
            browser.setMinimumWidth(760)
            browser.document().setDocumentMargin(8)
            return browser

        nav_list = QListWidget()
        nav_list.setFixedWidth(180)
        nav_list.setSpacing(4)

        stack = QStackedWidget()

        quick_html = self._tr("help_html_quick") + self._build_hardware_requirements_help_html()

        kraken_html = self._tr("help_html_kraken")

        lm_server_html = self._tr("help_html_lm_server")

        ssh_html = self._tr("help_html_ssh")

        page_whisper = QWidget()
        page_whisper_layout = QVBoxLayout(page_whisper)
        page_whisper_layout.setContentsMargins(0, 0, 0, 0)
        page_whisper_layout.setSpacing(8)
        page_whisper_layout.setAlignment(Qt.AlignTop)

        whisper_intro_html = self._tr("help_html_whisper_intro")

        browser_whisper_intro = make_page(whisper_intro_html)
        browser_whisper_intro.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        browser_whisper_intro.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        browser_whisper_intro.setMinimumHeight(260)

        page_whisper_layout.addWidget(browser_whisper_intro, 1)

        btn_info = QLabel(self._tr("help_whisper_download_label"))
        page_whisper_layout.addWidget(btn_info, 0)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(6)

        btn_windows = _small_btn(self._tr("help_os_windows"))
        btn_arch = _small_btn(self._tr("help_os_arch"))
        btn_debian = _small_btn(self._tr("help_os_debian"))
        btn_fedora = _small_btn(self._tr("help_os_fedora"))
        btn_mac = _small_btn(self._tr("help_os_macos"))

        hf_cmd_browser = QTextBrowser()
        hf_cmd_browser.setReadOnly(True)
        hf_cmd_browser.setOpenExternalLinks(False)
        hf_cmd_browser.setFrameShape(QTextBrowser.NoFrame)
        hf_cmd_browser.setHtml(_help_pre(f"{default_install_cmd}\n{default_download_cmd}"))
        hf_cmd_browser.setMinimumWidth(760)
        hf_cmd_browser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        hf_cmd_browser.setFixedHeight(96)

        hf_hint_browser = QTextBrowser()
        hf_hint_browser.setReadOnly(True)
        hf_hint_browser.setOpenExternalLinks(False)
        hf_hint_browser.setFrameShape(QTextBrowser.NoFrame)
        hf_hint_browser.setHtml(_help_pre(self._whisper_system_hint("windows")))
        hf_hint_browser.setMinimumWidth(760)
        hf_hint_browser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        hf_hint_browser.setFixedHeight(112)

        def _bind_whisper_button(btn: QPushButton, platform_name: str):
            def _handler():
                install_cmd, download_cmd = self._whisper_button_commands(platform_name)
                system_hint = self._whisper_system_hint(platform_name)

                hf_cmd_browser.setHtml(_help_pre(f"{install_cmd}\n{download_cmd}"))
                hf_hint_browser.setHtml(_help_pre(system_hint))

                self.download_whisper_model_from_help_dialog(platform_name, dlg)

            btn.clicked.connect(_handler)

        _bind_whisper_button(btn_windows, "Windows")
        _bind_whisper_button(btn_arch, "Arch")
        _bind_whisper_button(btn_debian, "Debian")
        _bind_whisper_button(btn_fedora, "Fedora")
        _bind_whisper_button(btn_mac, "Mac")

        btn_row.addWidget(btn_windows)
        btn_row.addWidget(btn_arch)
        btn_row.addWidget(btn_debian)
        btn_row.addWidget(btn_fedora)
        btn_row.addWidget(btn_mac)
        btn_row.addStretch()

        page_whisper_layout.addLayout(btn_row, 0)
        page_whisper_layout.addWidget(hf_cmd_browser, 0)
        page_whisper_layout.addWidget(hf_hint_browser, 0)

        shortcuts_html = self._tr("help_html_shortcuts")

        data_protection_html = self._tr("help_html_data_protection")

        legal_html = self._tr("help_html_legal")

        stack.addWidget(make_page(quick_html))
        stack.addWidget(make_page(kraken_html))
        stack.addWidget(make_page(lm_server_html))
        stack.addWidget(make_page(ssh_html))
        stack.addWidget(page_whisper)
        stack.addWidget(make_page(shortcuts_html))
        stack.addWidget(make_page(data_protection_html))
        stack.addWidget(make_page(legal_html))

        nav_items = [
            self._tr("help_nav_quick"),
            self._tr("help_nav_kraken"),
            self._tr("help_nav_lm_server"),
            self._tr("help_nav_ssh"),
            self._tr("help_nav_whisper"),
            self._tr("help_nav_shortcuts"),
            self._tr("help_nav_data_protection"),
            self._tr("help_nav_legal"),
        ]
        for label in nav_items:
            nav_list.addItem(label)

        nav_list.currentRowChanged.connect(stack.setCurrentIndex)
        nav_list.setCurrentRow(0)

        content_layout.addWidget(nav_list, 0)
        content_layout.addWidget(stack, 1)

        scroll.setWidget(content)
        layout.addWidget(scroll)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.button(QDialogButtonBox.Ok).setText(self._tr("btn_ok"))
        buttons.accepted.connect(dlg.accept)
        layout.addWidget(buttons)

        dlg.exec()

    def _edited_images_output_dir(self, source_task: TaskItem) -> str:
        """
        Sammelordner für bearbeitete Bilder im gleichen Verzeichnis
        wie die Ursprungsdatei.
        """
        src_dir = os.path.dirname(os.path.abspath(source_task.path))
        out_dir = os.path.join(src_dir, "Bottled Kraken - edited pictures")
        os.makedirs(out_dir, exist_ok=True)
        return out_dir

    def _save_edited_image_under_original(
            self,
            source_task: TaskItem,
            pil_image: Image.Image,
            suggested_name: str
    ) -> str:
        edit_dir = self._edited_images_output_dir(source_task)

        src_stem = os.path.splitext(os.path.basename(source_task.path))[0]
        safe_src_stem = re.sub(r'[^A-Za-z0-9._-]+', '_', src_stem).strip('._') or "bild"
        safe_suggested = re.sub(r'[^A-Za-z0-9._-]+', '_', suggested_name).strip('._') or "edit"

        safe_base = f"{safe_src_stem}__{safe_suggested}"
        out_path = os.path.join(edit_dir, f"{safe_base}.png")

        counter = 2
        while os.path.exists(out_path):
            out_path = os.path.join(edit_dir, f"{safe_base}_{counter}.png")
            counter += 1

        pil_image.convert("RGB").save(out_path, format="PNG")
        return out_path

    def _insert_task_row(self, row: int, task: TaskItem):
        row = max(0, min(row, self.queue_table.rowCount()))
        self.queue_items.insert(row, task)
        self.queue_table.insertRow(row)
        num_item = QTableWidgetItem(str(row + 1))
        num_item.setTextAlignment(Qt.AlignCenter)
        num_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        name_item = QTableWidgetItem(task.display_name)
        name_item.setData(Qt.UserRole, task.path)
        name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
        status_item = QTableWidgetItem()
        status_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

        self.queue_table.setItem(row, QUEUE_COL_NUM, num_item)
        self.queue_table.setCellWidget(row, QUEUE_COL_CHECK, self._make_queue_checkbox_widget(False))
        self.queue_table.setItem(row, QUEUE_COL_FILE, name_item)
        self.queue_table.setItem(row, QUEUE_COL_STATUS, status_item)
        self._update_queue_row(task.path)

    def _selected_or_checked_tasks_for_edit(self) -> List[TaskItem]:
        checked = self._checked_queue_tasks()
        if checked:
            return checked
        return self._selected_queue_tasks()

    def _create_edited_tasks_from_images(
            self,
            source_task: TaskItem,
            result_images: List[Image.Image]
    ) -> List[TaskItem]:
        created = []

        original_name = source_task.display_name or os.path.basename(source_task.path)
        original_stem = os.path.splitext(original_name)[0]
        safe_stem = re.sub(r'[^A-Za-z0-9._-]+', '_', original_stem).strip('._') or "bild"

        total = max(1, len(result_images))

        for idx, img in enumerate(result_images, start=1):
            label_name = f"edit_{safe_stem}_{idx}_{total}"

            out_path = self._save_edited_image_under_original(
                source_task=source_task,
                pil_image=img,
                suggested_name=label_name
            )

            new_task = TaskItem(
                path=out_path,
                display_name=os.path.basename(out_path),
                status=STATUS_WAITING,
                edited=False,
                source_kind="image",
                relative_path=""
            )

            # IMMER ans Ende der Queue
            end_row = self.queue_table.rowCount()
            self._insert_task_row(end_row, new_task)
            created.append(new_task)

        return created

    def _apply_image_edit_settings_to_task(self, task: TaskItem, settings: ImageEditSettings) -> List[Image.Image]:
        img = _load_image_color(task.path)
        dlg = ImageEditDialog(img, task.display_name, self)
        dlg.set_settings(settings)
        dlg._accept_dialog()
        return list(dlg.result_images or [])

    def _load_task_into_edit_dialog(self, dlg: ImageEditDialog, task: TaskItem):
        image = _load_image_color(task.path)
        dlg.original_image = image.convert("RGB")
        dlg.setWindowTitle(self._tr("image_edit_title", task.display_name))
        dlg.rotation_angle = 0.0
        dlg.erase_actions = []
        dlg.canvas.crop_rect = None
        dlg.canvas.separator = None
        dlg.canvas.erase_rect = None
        dlg.canvas.show_erase = False
        dlg.canvas.erase_shape = ""

        dlg.chk_crop.blockSignals(True)
        dlg.chk_crop.setChecked(False)
        dlg.chk_crop.blockSignals(False)

        dlg.chk_split.blockSignals(True)
        dlg.chk_split.setChecked(False)
        dlg.chk_split.blockSignals(False)

        dlg.chk_smart_split.blockSignals(True)
        dlg.chk_smart_split.setChecked(False)
        dlg.chk_smart_split.setEnabled(False)
        dlg.chk_smart_split.blockSignals(False)

        dlg.chk_gray.blockSignals(True)
        dlg.chk_gray.setChecked(False)
        dlg.chk_gray.blockSignals(False)

        dlg.chk_contrast.blockSignals(True)
        dlg.chk_contrast.setChecked(False)
        dlg.chk_contrast.blockSignals(False)

        dlg.chk_erase_rect.blockSignals(True)
        dlg.chk_erase_ellipse.blockSignals(True)
        dlg.chk_erase_rect.setChecked(False)
        dlg.chk_erase_ellipse.setChecked(False)
        dlg.chk_erase_rect.blockSignals(False)
        dlg.chk_erase_ellipse.blockSignals(False)

        dlg._refresh_preview(reset_zoom=True)

    def _finalize_image_edit_batch(self, status_message: str):
        self._refresh_queue_numbers()
        self._fit_queue_columns_exact()
        self._update_queue_hint()
        self.status_bar.showMessage(status_message)

    def _apply_image_edit_to_targets(
            self,
            targets: List[TaskItem],
            settings: ImageEditSettings,
            status_message: str
    ):
        if not targets:
            self._finalize_image_edit_batch(status_message)
            return

        total = len(targets)

        progress = QProgressDialog(
            self._tr("image_edit_batch_label", 0, total, ""),
            self._tr("btn_cancel"),
            0,
            total,
            self
        )
        progress.setWindowTitle(self._tr("image_edit_batch_title"))
        progress.setWindowModality(Qt.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.setAutoClose(True)
        progress.setAutoReset(True)
        progress.setValue(0)

        try:
            for idx, tgt in enumerate(targets, start=1):
                progress.setLabelText(
                    self._tr("image_edit_batch_label", idx, total, tgt.display_name)
                )
                progress.setValue(idx - 1)
                QCoreApplication.processEvents()

                if progress.wasCanceled():
                    self._finalize_image_edit_batch(self._tr("msg_image_edit_batch_cancelled"))
                    return

                try:
                    result_images = self._apply_image_edit_settings_to_task(tgt, settings)
                    if result_images:
                        self._create_edited_tasks_from_images(tgt, result_images)
                except Exception as e:
                    self._log(self._tr_log("log_image_edit_error", tgt.display_name, e))

                progress.setValue(idx)
                QCoreApplication.processEvents()

                if progress.wasCanceled():
                    self._finalize_image_edit_batch(self._tr("msg_image_edit_batch_cancelled"))
                    return
        finally:
            progress.close()

        self._finalize_image_edit_batch(status_message)

    def open_image_edit_dialog(self):
        task = self._current_task()
        if not task or not task.path or not os.path.exists(task.path):
            QMessageBox.information(self, self._tr("info_title"),
                                    self._tr("warn_select_image_or_pdf_page"))
            return

        try:
            image = _load_image_color(task.path)
        except Exception as e:
            QMessageBox.warning(self, self._tr("warn_title"), f"Bild konnte nicht geladen werden:\n{e}")
            return

        current_row = self.queue_table.currentRow()
        if current_row < 0:
            current_row = 0

        def _prev(dialog):
            row = self.queue_table.currentRow()
            if row > 0:
                self.queue_table.selectRow(row - 1)
                next_task = self._current_task()
                if next_task and os.path.exists(next_task.path):
                    self._load_task_into_edit_dialog(dialog, next_task)

        def _next(dialog):
            row = self.queue_table.currentRow()
            if row < self.queue_table.rowCount() - 1:
                self.queue_table.selectRow(row + 1)
                next_task = self._current_task()
                if next_task and os.path.exists(next_task.path):
                    self._load_task_into_edit_dialog(dialog, next_task)

        def _apply_selected(dialog):
            settings = dialog.get_settings()
            targets = self._selected_or_checked_tasks_for_edit()
            if not targets:
                QMessageBox.information(self, self._tr("info_title"), self._tr("info_no_marked_images_found"))
                return

            self._apply_image_edit_to_targets(
                targets,
                settings,
                self._tr("msg_image_edit_selected_applied")
            )

        def _apply_all(dialog):
            settings = dialog.get_settings()
            self._apply_image_edit_to_targets(
                list(self.queue_items),
                settings,
                self._tr("msg_image_edit_all_applied")
            )

        dlg = ImageEditDialog(
            image,
            task.display_name or os.path.basename(task.path),
            self,
            on_prev=_prev,
            on_next=_next,
            on_apply_selected=_apply_selected,
            on_apply_all=_apply_all,
        )

        if dlg.exec() != QDialog.Accepted:
            return

        if getattr(dlg, "_batch_apply_used", False):
            return

        result_images = [im for im in getattr(dlg, "result_images", []) if isinstance(im, Image.Image)]
        if not result_images:
            return

        created = self._create_edited_tasks_from_images(task, result_images)

        self._refresh_queue_numbers()
        self._fit_queue_columns_exact()
        self._update_queue_hint()

        if created:
            new_row = next(
                (r for r in range(self.queue_table.rowCount())
                 if self.queue_table.item(r, QUEUE_COL_FILE).data(Qt.UserRole) == created[0].path),
                current_row
            )
            self.queue_table.selectRow(new_row)
            self.preview_image(created[0].path)

        self.status_bar.showMessage(self._tr("image_edit_applied_single_status"))
        self._log(self._tr_log("log_image_edit_applied", task.display_name, len(result_images)))

    def closeEvent(self, event):
        if self._is_closing:
            event.ignore()
            return

        self._is_closing = True
        self.setEnabled(False)

        try:
            self.settings.setValue("ui/language", self.current_lang)
            self.settings.setValue("ui/theme", self.current_theme)
            self.settings.sync()

            self._request_all_workers_stop()

            # Threads kurz sauber auslaufen lassen
            for w in self._all_workers():
                try:
                    if w and w.isRunning():
                        w.wait(1500)
                except Exception:
                    pass

            self._cleanup_temp_dirs()
            event.accept()

        except Exception:
            event.accept()

def main():
    if sys.platform.startswith("win"):
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("bottled.kraken.app")
        except Exception:
            pass

    app = QApplication(sys.argv)
    _install_exception_hook()
    app.setStyle("Fusion")

    icon_path = resource_path("icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    w = MainWindow()
    app.aboutToQuit.connect(w._cleanup_temp_dirs)

    if os.path.exists(icon_path):
        w.setWindowIcon(QIcon(icon_path))

    w.showMaximized()
    QCoreApplication.processEvents()

    try:
        if pyi_splash:
            pyi_splash.close()
    except Exception:
        pass

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
