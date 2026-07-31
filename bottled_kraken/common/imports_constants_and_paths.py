from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('shared', globals())
from bottled_kraken.resource_paths import resource_path
import os
import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning, module=r"coremltools(\.|$)")
warnings.filterwarnings("ignore", message=r"invalid escape sequence.*\\_", category=SyntaxWarning)
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"
import sys
import locale
import platform
from bottled_kraken.windows_coremltools_stub import install_windows_coremltools_stub
install_windows_coremltools_stub()
import torch
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
try:
    locale.setlocale(locale.LC_ALL, "")
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
from bottled_kraken.translation import TRANSLATIONS, translation, Translation
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
    QPainter, QDrag, QFontMetricsF, QCursor, QPolygonF
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
    QStyledItemDelegate, QStyleOptionViewItem, QStyle, QComboBox
)
from shiboken6 import isValid
from PIL import Image, ImageDraw, ImageOps, ImageEnhance
try:
    _BK_PIL_MAX_IMAGE_PIXELS = int(os.environ.get("BOTTLED_KRAKEN_PIL_MAX_IMAGE_PIXELS", "250000000"))
except Exception:
    _BK_PIL_MAX_IMAGE_PIXELS = 250_000_000
try:
    Image.MAX_IMAGE_PIXELS = max(int(Image.MAX_IMAGE_PIXELS or 0), _BK_PIL_MAX_IMAGE_PIXELS)
except Exception:
    Image.MAX_IMAGE_PIXELS = _BK_PIL_MAX_IMAGE_PIXELS
from PIL.ImageQt import ImageQt
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader
warnings.filterwarnings("ignore", message="Using legacy polygon extractor*", category=UserWarning)
warnings.filterwarnings("ignore", message=r"`blla\.segment\(\)` is deprecated.*", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=r"`rpred\..*` is deprecated.*", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=r"`TorchVGSLModel\.load_model` is deprecated.*", category=DeprecationWarning)
install_windows_coremltools_stub()
from kraken import blla, rpred, serialization, containers
from kraken.lib import models, vgsl
import torch
from bottled_kraken.version_config import KRAKEN_VERSION
KRAKEN_TARGET_VERSION = KRAKEN_VERSION
def _kraken_device_arg(device: Any = None) -> str:
    if device is None:
        return "cpu"
    try:
        if isinstance(device, torch.device):
            if device.index is not None:
                return f"{device.type}:{device.index}"
            return str(device.type or "cpu")
    except Exception:
        pass
    text = str(device or "cpu").strip()
    return text or "cpu"
def load_kraken_recognition_model(path: str, device: Any = None):
    device_arg = _kraken_device_arg(device)
    try:
        return models.load_any(path, device=device_arg)
    except TypeError:
        return models.load_any(path)
def load_kraken_segmentation_model(path: str, device: Any = None):
    try:
        return vgsl.TorchVGSLModel.load_model(path)
    except TypeError:
        return vgsl.TorchVGSLModel.load_model(path)
def segment_with_kraken(im: Image.Image, model: Any, device: Any = None,
                        text_direction: str = "horizontal-lr"):
    device_arg = _kraken_device_arg(device)
    try:
        return blla.segment(im, model=model, device=device_arg, text_direction=text_direction)
    except TypeError:
        try:
            return blla.segment(im, model=model, device=device_arg)
        except TypeError:
            return blla.segment(im, model=model)
def recognize_with_kraken(recognition_model: Any, im: Image.Image, segmentation: Any):
    return rpred.rpred(recognition_model, im, segmentation)
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
def _theme_entry(
        *,
        name: str,
        bg: str,
        fg: str,
        surface: str,
        canvas_bg: str,
        selection: str,
        overlay_frame: str,
        overlay_split: str,
        border: str | None = None,
        control_bg: str | None = None,
        control_hover: str | None = None,
        control_pressed: str | None = None,
        table_alt: str | None = None,
        selection_text: str | None = None,
        dark: bool | None = None,
):
    base_color = QColor(surface)
    bg_color = QColor(bg)
    is_dark = bool(dark) if dark is not None else bg_color.lightness() < 128
    border_color = border or (QColor(surface).lighter(150).name() if is_dark else QColor(surface).darker(130).name())
    hover = control_hover or (QColor(control_bg or surface).lighter(118).name() if is_dark else QColor(control_bg or surface).darker(104).name())
    pressed = control_pressed or (QColor(control_bg or surface).lighter(132).name() if is_dark else QColor(control_bg or surface).darker(112).name())
    alt = table_alt or (base_color.lighter(112).name() if is_dark else base_color.darker(103).name())
    sel_text = selection_text
    if not sel_text:
        sel_text = "#000000" if QColor(selection).lightness() > 165 else "#ffffff"
    return {
        "name": name,
        "dark": is_dark,
        "bg": bg,
        "fg": fg,
        "surface": surface,
        "canvas_bg": canvas_bg,
        "table_base": base_color,
        "table_alt": alt,
        "control_bg": control_bg or surface,
        "control_hover": hover,
        "control_pressed": pressed,
        "border": border_color,
        "selection": selection,
        "selection_text": sel_text,
        "toolbar_text": fg,
        "toolbar_border": border_color,
        "overlay_frame": overlay_frame,
        "overlay_selected": selection,
        "overlay_split": overlay_split,
        "overlay_fill_alpha": 34,
        "overlay_selected_alpha": 64,
    }
THEMES = {
    "bright": _theme_entry(
        name="Hell",
        bg="#f0f0f0",
        fg="#000000",
        surface="#ffffff",
        canvas_bg="#f2f2f2",
        selection="#3399ff",
        overlay_frame="#d00000",
        overlay_split="#ffd60a",
        border="#b8b8b8",
        control_bg="#f7f7f7",
        control_hover="#ececec",
        control_pressed="#dddddd",
        table_alt="#f3f6fb",
        dark=False,
    ),
    "dark": _theme_entry(
        name="Dunkel",
        bg="#2b2b2b",
        fg="#ffffff",
        surface="#2b3038",
        canvas_bg="#1e1e1e",
        selection="#2563eb",
        overlay_frame="#ff3b30",
        overlay_split="#ffd60a",
        border="#4b5563",
        control_bg="#2b3038",
        control_hover="#343a44",
        control_pressed="#3f4652",
        table_alt="#27303b",
        dark=True,
    ),
    "original": _theme_entry(name="Original", bg="#f0f0f0", fg="#000000", surface="#ffffff", canvas_bg="#f2f2f2", selection="#3399ff", overlay_frame="#d00000", overlay_split="#ffd60a", border="#b8b8b8", control_bg="#f7f7f7", dark=False),
    "light": _theme_entry(name="Light", bg="#f7f4ed", fg="#1f2933", surface="#fffaf0", canvas_bg="#fbf7ee", selection="#c49a6c", overlay_frame="#7c4f2c", overlay_split="#d08b5b", border="#d9c8aa", dark=False),
    "midnight": _theme_entry(name="Midnight", bg="#0b1020", fg="#dbeafe", surface="#111827", canvas_bg="#050816", selection="#60a5fa", overlay_frame="#ff5757", overlay_split="#f59e0b", border="#334155", dark=True),
    "paper": _theme_entry(name="Paper", bg="#f8f3df", fg="#262626", surface="#fff8dc", canvas_bg="#f7efd4", selection="#b59b4a", overlay_frame="#7a5c16", overlay_split="#a16207", border="#d6c896", dark=False),
    "cyberpunk": _theme_entry(name="Cyberpunk", bg="#070712", fg="#e0fbff", surface="#101022", canvas_bg="#050510", selection="#00e5ff", overlay_frame="#d946ef", overlay_split="#facc15", border="#26264a", dark=True),
    "retrowave": _theme_entry(name="Retrowave", bg="#190b2d", fg="#fff1f8", surface="#24113f", canvas_bg="#110720", selection="#ff4d8d", overlay_frame="#ff2d55", overlay_split="#00d4ff", border="#5b2c83", dark=True),
    "forest": _theme_entry(name="Forest", bg="#102017", fg="#e7f5e8", surface="#1d3325", canvas_bg="#0c1a12", selection="#7cc47f", overlay_frame="#9bdc9c", overlay_split="#d6a84f", border="#335c40", dark=True),
    "ocean": _theme_entry(name="Ocean", bg="#071b2c", fg="#e0f2fe", surface="#0f2a44", canvas_bg="#061525", selection="#38bdf8", overlay_frame="#67e8f9", overlay_split="#f59e0b", border="#235277", dark=True),
    "sakura": _theme_entry(name="Sakura", bg="#fdf2f8", fg="#3b2233", surface="#fff7fb", canvas_bg="#fff1f6", selection="#f9a8d4", overlay_frame="#e879a6", overlay_split="#a78bfa", border="#f3c6d9", selection_text="#3b2233", dark=False),
    "copper": _theme_entry(name="Copper", bg="#211814", fg="#ffe8d6", surface="#35231c", canvas_bg="#180f0c", selection="#f4b183", overlay_frame="#e27d60", overlay_split="#f7c56f", border="#6b4636", dark=True),
    "terminal": _theme_entry(name="Terminal", bg="#000000", fg="#1cff68", surface="#050805", canvas_bg="#000000", selection="#00ff55", overlay_frame="#00ff55", overlay_split="#eaff00", border="#0a7f32", selection_text="#001a08", dark=True),
    "organs": _theme_entry(name="Organs", bg="#150608", fg="#ffe4e6", surface="#250b10", canvas_bg="#100305", selection="#f4f1de", overlay_frame="#be3144", overlay_split="#f59e0b", border="#5a1721", dark=True),
    "lavender": _theme_entry(name="Lavender", bg="#f3efff", fg="#2f2358", surface="#faf8ff", canvas_bg="#f0eafd", selection="#8b5cf6", overlay_frame="#7c3aed", overlay_split="#ec4899", border="#d6c9ff", dark=False),
    "gpt": _theme_entry(name="GPT", bg="#101513", fg="#ececec", surface="#1f2723", canvas_bg="#0b0f0e", selection="#10a37f", overlay_frame="#d1d5db", overlay_split="#fbbf24", border="#3f4f48", dark=True),
    "claude": _theme_entry(name="Claude", bg="#f7efe7", fg="#2c221c", surface="#fffaf3", canvas_bg="#f5eadf", selection="#d97745", overlay_frame="#cc785c", overlay_split="#4b5563", border="#dcc7b5", dark=False),
    "cute": _theme_entry(name="Cute", bg="#fff1f5", fg="#4a1d2f", surface="#fff7fb", canvas_bg="#ffeaf2", selection="#fb7185", overlay_frame="#ec4899", overlay_split="#facc15", border="#fecdd3", dark=False),
    "custom": _theme_entry(name="Benutzerdefiniert", bg="#101010", fg="#00ff66", surface="#050805", canvas_bg="#000000", selection="#00ff66", overlay_frame="#00ff66", overlay_split="#ffff00", border="#0a7f32", selection_text="#001a08", dark=True),
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
__all__ = [
    'KRAKEN_MODELS_DIR',
    'KRAKEN_TARGET_VERSION',
    'QUEUE_COL_CHECK',
    'QUEUE_COL_FILE',
    'QUEUE_COL_NUM',
    'QUEUE_COL_STATUS',
    'READING_MODES',
    'STATUS_AI_PROCESSING',
    'STATUS_DONE',
    'STATUS_ERROR',
    'STATUS_EXPORTING',
    'STATUS_ICONS',
    'STATUS_PROCESSING',
    'STATUS_VOICE_RECORDING',
    'STATUS_WAITING',
    'SUPPORTED_IMAGE_EXTS',
    'SUPPORTED_PDF_EXTS',
    'THEMES',
    'VOICE_BLOCKSIZE',
    'VOICE_CHANNELS',
    'VOICE_SAMPLE_RATE',
    'ZENODO_URL',
    '_kraken_device_arg',
    '_load_image_color',
    '_load_image_gray',
    '_theme_control_qss',
    'is_project_file',
    'is_supported_drop_or_paste_file',
    'is_supported_input',
    'load_kraken_recognition_model',
    'load_kraken_segmentation_model',
    'recognize_with_kraken',
    'resource_path',
    'segment_with_kraken',
]
register_globals('shared', globals(), __all__)
