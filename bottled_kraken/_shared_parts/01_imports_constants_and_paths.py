"""Gemeinsame Grundlagen, Konstanten und Hilfsfunktionen für Bottled Kraken."""

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

from .translation import TRANSLATIONS, translation, Translation

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

from PySide6.QtCore import (Qt, QThread, Signal, QRectF, QUrl, QTimer,
                            QSize, QPointF, QEvent, QPoint, QDateTime, QLocale,
                            QCoreApplication, QSettings, QItemSelectionModel, QMimeData)

from PySide6.QtGui import (
    QPixmap, QPen, QBrush, QColor, QFont, QDragEnterEvent, QDropEvent, QAction,
    QKeySequence, QActionGroup, QIcon, QPalette, QShortcut, QDesktopServices,
    QPainter, QDrag, QFontMetricsF
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

from shiboken6 import isValid

from PIL import Image, ImageDraw, ImageOps, ImageEnhance

from PIL.ImageQt import ImageQt

from reportlab.pdfgen import canvas as pdf_canvas

from reportlab.lib.utils import ImageReader

warnings.filterwarnings("ignore", message="Using legacy polygon extractor*", category=UserWarning)

from kraken import blla, rpred, serialization, containers

from kraken.lib import models, vgsl

import torch

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
