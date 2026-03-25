import os
import sys
import time
import math
import statistics
import json
import csv
import warnings
import re
from dataclasses import dataclass, field
from typing import Optional, List, Any, Tuple, Dict, Callable
import fitz
import ctypes
import shutil
import urllib.request
import urllib.error
import urllib.parse
import http.client
import base64
import mimetypes
import socket
from io import BytesIO

# GUI-Framework
from PySide6.QtCore import (Qt, QThread, Signal, QRectF, QUrl, QTimer,
                            QSize, QPointF, QEvent, QPoint, QDateTime, QLocale,
                            QCoreApplication)
from PySide6.QtGui import (
    QPixmap, QPen, QBrush, QColor, QFont, QDragEnterEvent, QDropEvent, QAction,
    QKeySequence, QActionGroup, QIcon, QPalette, QShortcut
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox,
    QLabel, QWidget, QPushButton, QProgressBar, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QGraphicsSimpleTextItem, QSplitter, QStatusBar,
    QMenu, QTableWidget, QTableWidgetItem, QHeaderView, QToolBar,
    QAbstractItemView, QInputDialog, QDialog, QDialogButtonBox, QRadioButton,
    QListWidget as QListWidget2, QSpinBox, QFormLayout, QPlainTextEdit,
    QToolButton, QProgressDialog, QLineEdit, QTextEdit
)

# PySide-Helfer zur Objekt-Validitätsprüfung
from shiboken6 import isValid

# Bild & PDF
from PIL import Image
from PIL.ImageQt import ImageQt
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader

# Kraken & ML (Machine Learning)
warnings.filterwarnings("ignore", message="Using legacy polygon extractor*", category=UserWarning)
from kraken import blla, rpred, serialization, pageseg, binarization
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
        "canvas_bg": "#ffffff",
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

KRAKEN_MODELS_DIR = r"C:\Users\Entertainment\PycharmProjects\Bottled Kraken + vLLM\Kraken-Modelle"

def resource_path(relative_path: str) -> str:
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)

def is_supported_input(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    return ext in SUPPORTED_IMAGE_EXTS or ext in SUPPORTED_PDF_EXTS

def _load_image_gray(path: str) -> Image.Image:
    return Image.open(path).convert("L")

def _load_image_color(path: str) -> Image.Image:
    return Image.open(path).convert("RGB")

# -----------------------------
# ÜBERSETZUNGEN
# -----------------------------
TRANSLATIONS = {
    "de": {
        "dlg_filter_img": "Bilder/PDF (*.png *.jpg *.jpeg *.tif *.tiff *.bmp *.webp *.pdf)",
        "pdf_render_title": "PDF wird vorbereitet",
        "pdf_render_label": "Seiten werden gerendert… ({}/{}): {}",
        "app_title": "Bottled Kraken",
        "toolbar_main": "Werkzeugleiste",
        "menu_file": "&Datei",
        "menu_edit": "&Bearbeiten",
        "menu_export": "Exportieren als...",
        "menu_exit": "Beenden",
        "menu_models": "&Kraken-Modelle",
        "menu_options": "&Optionen",
        "menu_languages": "Sprachen",
        "menu_hw": "CPU/GPU",
        "menu_reading": "Leserichtung",
        "menu_appearance": "Erscheinungsbild",
        "act_clear_rec": "Recognition-Modell entfernen",
        "act_clear_seg": "Segmentierungs-Modell entfernen",
        "act_paste_clipboard": "Aus Zwischenablage einfügen",

        "log_toggle_show": "Log",
        "log_toggle_hide": "Log",
        "menu_export_log": "Log als .txt exportieren...",
        "dlg_save_log": "Log speichern",
        "dlg_filter_txt": "Text (*.txt)",
        "log_started": "Programm gestartet.",
        "log_queue_cleared": "Queue geleert.",

        "lang_de": "Deutsch",
        "lang_en": "English",
        "lang_fr": "Français",

        "hw_cpu": "CPU",
        "hw_cuda": "GPU – CUDA (NVIDIA)",
        "hw_rocm": "GPU – ROCm (AMD)",
        "hw_mps": "GPU – MPS (Apple)",

        "act_undo": "Rückgängig",
        "act_redo": "Wiederholen",

        "msg_hw_not_available": "Diese Hardware ist auf diesem System nicht verfügbar. Wechsle zu CPU.",
        "msg_using_device": "Verwende Gerät: {}",
        "msg_detected_gpu": "Erkannt: {}",
        "msg_device_cpu": "CPU",
        "msg_device_cuda": "CUDA",
        "msg_device_rocm": "ROCm",
        "msg_device_mps": "MPS",

        "act_add_files": "Dateien laden...",
        "act_download_model": "Modell herunterladen (Zenodo)",
        "act_delete": "Löschen",
        "act_rename": "Umbenennen...",
        "act_clear_queue": "Wartebereich leeren",
        "act_start_ocr": "Start Kraken OCR",
        "act_stop_ocr": "Stopp",
        "act_re_ocr": "Wiederholen",
        "act_re_ocr_tip": "Ausgewählte Datei(en) erneut verarbeiten",
        "act_overlay_show": "Overlay-Boxen anzeigen",

        "status_ready": "Bereit.",
        "status_waiting": "Wartet",
        "status_processing": "Verarbeite...",
        "status_done": "Fertig",
        "status_error": "Fehler",

        "lbl_queue": "Wartebereich:",
        "lbl_lines": "Erkannte Zeilen:",
        "col_file": "Datei",
        "col_status": "Status",

        "drop_hint": "Datei(en) hierher ziehen und ablegen",
        "queue_drop_hint": "Datei(en) hierher ziehen und ablegen",

        "info_title": "Information",
        "warn_title": "Warnung",
        "err_title": "Fehler",

        "theme_bright": "Hell",
        "theme_dark": "Dunkel",

        "warn_queue_empty": "Wartebereich ist leer oder alle Elemente wurden verarbeitet.",
        "warn_select_done": "Keine Datei(en) für erneutes OCRn geladen.",
        "warn_need_rec": "Bitte wählen Sie zuerst ein Format-Modell (Recognition) aus.",
        "warn_need_seg": "Bitte wählen Sie zuerst ein Segmentierungs-Modell aus.",

        "msg_stopping": "Breche ab...",
        "msg_finished": "Batch abgeschlossen.",
        "msg_device": "Gerät gesetzt auf: {}",
        "msg_exported": "Exportiert: {}",
        "msg_loaded_rec": "Format-Modell: {}",
        "msg_loaded_seg": "Segmentierungs-Modell: {}",

        "err_load": "Bild kann nicht geladen werden: {}",

        "dlg_title_rename": "Umbenennen",
        "dlg_label_name": "Neuer Dateiname:",
        "dlg_save": "Speichern",
        "dlg_load_img": "Bilder wählen",
        "dlg_choose_rec": "Recognition-Modell: ",
        "dlg_choose_seg": "Segmentierungs-Modell: ",
        "dlg_filter_model": "Modelle (*.mlmodel *.pt)",

        "reading_tb_lr": "Oben → Unten + Links → Rechts",
        "reading_tb_rl": "Oben → Unten + Rechts → Links",
        "reading_bt_lr": "Unten → Oben + Links → Rechts",
        "reading_bt_rl": "Unten → Oben + Rechts → Links",

        "line_menu_move_up": "Zeile nach oben",
        "line_menu_move_down": "Zeile nach unten",
        "line_menu_delete": "Zeile löschen",
        "line_menu_add_above": "Zeile darüber hinzufügen",
        "line_menu_add_below": "Zeile darunter hinzufügen",
        "line_menu_draw_box": "Overlay-Box zeichnen",
        "line_menu_edit_box": "Overlay-Box bearbeiten (ziehen/skalieren)",
        "line_menu_move_to": "Zeile verschieben zu…",

        "dlg_new_line_title": "Neue Zeile",
        "dlg_new_line_label": "Text der neuen Zeile:",

        "dlg_move_to_title": "Zeile verschieben",
        "dlg_move_to_label": "Ziel-Zeilennummer (1…):",

        "canvas_menu_add_box_draw": "Overlay-Box hinzufügen (zeichnen)",
        "canvas_menu_delete_box": "Overlay-Box löschen",
        "canvas_menu_edit_box": "Overlay-Box bearbeiten…",
        "canvas_menu_select_line": "Zeile auswählen",

        "dlg_box_title": "Overlay-Box",
        "dlg_box_left": "links",
        "dlg_box_top": "oben",
        "dlg_box_right": "rechts",
        "dlg_box_bottom": "unten",
        "dlg_box_apply": "Anwenden",

        "export_choose_mode_title": "Export",
        "export_mode_all": "Alle Dateien exportieren",
        "export_mode_selected": "Ausgewählte Dateien exportieren",
        "export_select_files_title": "Dateien auswählen",
        "export_select_files_hint": "Wählen Sie die Dateien für den Export:",
        "export_choose_folder": "Zielordner wählen",
        "export_need_done": "Mindestens eine ausgewählte Datei ist nicht fertig verarbeitet.",
        "export_none_selected": "Keine Dateien ausgewählt.",

        "undo_nothing": "Nichts zum Rückgängig machen.",
        "redo_nothing": "Nichts zum Wiederholen.",
        "overlay_only_after_ocr": "Overlay-Bearbeitung ist erst nach abgeschlossener OCR möglich.",

        "new_line_from_box_title": "Neue Zeile",
        "new_line_from_box_label": "Text für die neue Zeile (optional):",

        "log_added_files": "{} Datei(en) zur Queue hinzugefügt.",
        "log_ocr_started": "OCR gestartet: {} Datei(en), Device={}, Reading={}",
        "log_stop_requested": "OCR-Abbruch angefordert.",
        "log_file_started": "Starte Datei: {}",
        "log_file_done": "Fertig: {} ({} Zeilen)",
        "log_file_error": "Fehler: {} -> {}",
        "log_export_done": "Export abgeschlossen: {} Datei(en) als {} nach {}",
        "log_export_single": "Export: {} -> {}",
        "log_export_log_done": "Log exportiert: {}",
        "act_ai_revise": "LM-Überarbeitung",
        "act_ai_revise_tip": "OCR-Text mit lokalem LLM überarbeiten",
        "msg_ai_started": "Überarbeitung gestartet...",
        "msg_ai_done": "Überarbeitung abgeschlossen.",
        "msg_ai_model_set": "KI-Modell-ID: {}",
        "msg_ai_disabled": "Überarbeitung nicht möglich.",
        "warn_need_done_for_ai": "Bitte zuerst eine fertig OCR-verarbeitete Datei auswählen.",
        "warn_need_ai_model": "Kein Modell über localhost gefunden. Bitte vLLM/LM Studio starten oder eine Modell-ID setzen.",
        "warn_ai_server": "LM Studio Server nicht erreichbar. Bitte Modell laden und lokalen Server starten.",
        "dlg_choose_ai_model": "LM-Studio Modell-Identifier",
        "dlg_choose_ai_model_label": "Optionale Modell-ID. Leer lassen, wenn das laufende localhost-Modell automatisch verwendet werden soll:",
        "log_ai_started": "Überarbeitung gestartet: {}",
        "log_ai_done": "Überarbeitung abgeschlossen: {}",
        "log_ai_error": "Überarbeitung Fehler: {} -> {}",
        "status_ai_processing": "Überarbeitung...",
        "status_exporting": "Exportiere...",

        "menu_project_save": "Projekt speichern",
        "menu_project_save_as": "Projekt speichern unter...",
        "menu_project_load": "Projekt laden...",
        "dlg_filter_project": "Bottled-Kraken Projekt (*.json)",
        "msg_project_saved": "Projekt gespeichert: {}",
        "msg_project_loaded": "Projekt geladen: {}",
        "warn_project_load_failed": "Projekt konnte nicht geladen werden: {}",
        "warn_project_save_failed": "Projekt konnte nicht gespeichert werden: {}",
        "warn_project_file_missing": "Datei nicht gefunden: {}",
        "line_menu_swap_with": "Zeile tauschen mit…",
        "dlg_swap_title": "Zeilen tauschen",
        "dlg_swap_label": "Mit Zeilennummer tauschen (1…):",
    },

    "en": {
        "dlg_filter_img": "Images/PDF (*.png *.jpg *.jpeg *.tif *.tiff *.bmp *.webp *.pdf)",
        "pdf_render_title": "Preparing PDF",
        "pdf_render_label": "Rendering pages… ({}/{}): {}",
        "app_title": "Bottled Kraken",
        "toolbar_main": "Toolbar",
        "menu_file": "&File",
        "menu_edit": "&Edit",
        "menu_export": "Export as...",
        "menu_exit": "Exit",
        "menu_models": "&Kraken Models",
        "menu_options": "&Options",
        "menu_languages": "Languages",
        "menu_hw": "CPU/GPU",
        "menu_reading": "Reading Direction",
        "menu_appearance": "Appearance",
        "act_clear_rec": "Clear recognition model",
        "act_clear_seg": "Clear segmentation model",
        "act_paste_clipboard": "Paste from clipboard",

        "log_toggle_show": "Log",
        "log_toggle_hide": "Log",
        "menu_export_log": "Export log as .txt...",
        "dlg_save_log": "Save log",
        "dlg_filter_txt": "Text (*.txt)",
        "log_started": "Program started.",
        "log_queue_cleared": "Queue cleared.",

        "lang_de": "German",
        "lang_en": "English",
        "lang_fr": "French",

        "hw_cpu": "CPU",
        "hw_cuda": "GPU – CUDA (NVIDIA)",
        "hw_rocm": "GPU – ROCm (AMD)",
        "hw_mps": "GPU – MPS (Apple)",

        "act_undo": "Undo",
        "act_redo": "Redo",

        "msg_hw_not_available": "This hardware is not available on this system. Switching to CPU.",
        "msg_using_device": "Using device: {}",
        "msg_detected_gpu": "Detected: {}",
        "msg_device_cpu": "CPU",
        "msg_device_cuda": "CUDA",
        "msg_device_rocm": "ROCm",
        "msg_device_mps": "MPS",

        "act_add_files": "Load files...",
        "act_download_model": "Download model (Zenodo)",
        "act_delete": "Delete",
        "act_rename": "Rename...",
        "act_clear_queue": "Clear queue",
        "act_start_ocr": "Start Kraken OCR",
        "act_stop_ocr": "Stop",
        "act_re_ocr": "Reprocess",
        "act_re_ocr_tip": "Reprocess selected file(s)",
        "act_overlay_show": "Show overlay boxes",

        "status_ready": "Ready.",
        "status_waiting": "Waiting",
        "status_processing": "Processing...",
        "status_done": "Done",
        "status_error": "Error",

        "lbl_queue": "Queue:",
        "lbl_lines": "Recognized lines:",
        "col_file": "File",
        "col_status": "Status",

        "drop_hint": "Drag & drop files here",
        "queue_drop_hint": "Drag & drop files here",

        "info_title": "Information",
        "warn_title": "Warning",
        "err_title": "Error",

        "theme_bright": "Bright",
        "theme_dark": "Dark",

        "warn_queue_empty": "Queue is empty or all items are processed.",
        "warn_select_done": "No file(s) loaded for re-OCR.",
        "warn_need_rec": "Please select a format model (recognition) first.",
        "warn_need_seg": "Please select a segmentation model first.",

        "msg_stopping": "Stopping...",
        "msg_finished": "Batch finished.",
        "msg_device": "Device set to: {}",
        "msg_exported": "Exported: {}",
        "msg_loaded_rec": "Format model: {}",
        "msg_loaded_seg": "Segmentation model: {}",

        "err_load": "Cannot load image: {}",

        "dlg_title_rename": "Rename",
        "dlg_label_name": "New filename:",
        "dlg_save": "Save",
        "dlg_load_img": "Choose images",
        "dlg_choose_rec": "recognition model: ",
        "dlg_choose_seg": "segmentation model: ",
        "dlg_filter_model": "Models (*.mlmodel *.pt)",

        "reading_tb_lr": "Top → Bottom + Left → Right",
        "reading_tb_rl": "Top → Bottom + Right → Left",
        "reading_bt_lr": "Bottom → Top + Left → Right",
        "reading_bt_rl": "Bottom → Top + Right → Left",

        "line_menu_move_up": "Move line up",
        "line_menu_move_down": "Move line down",
        "line_menu_delete": "Delete line",
        "line_menu_add_above": "Add line above",
        "line_menu_add_below": "Add line below",
        "line_menu_draw_box": "Draw overlay box",
        "line_menu_edit_box": "Edit overlay box (move/resize)",
        "line_menu_move_to": "Move line to…",

        "dlg_new_line_title": "New line",
        "dlg_new_line_label": "Text of the new line:",

        "dlg_move_to_title": "Move line",
        "dlg_move_to_label": "Target line number (1…):",

        "canvas_menu_add_box_draw": "Add overlay box (draw)",
        "canvas_menu_delete_box": "Delete overlay box",
        "canvas_menu_edit_box": "Edit overlay box…",
        "canvas_menu_select_line": "Select line",

        "dlg_box_title": "Overlay box",
        "dlg_box_left": "left",
        "dlg_box_top": "top",
        "dlg_box_right": "right",
        "dlg_box_bottom": "bottom",
        "dlg_box_apply": "Apply",

        "export_choose_mode_title": "Export",
        "export_mode_all": "Export all files",
        "export_mode_selected": "Export selected files",
        "export_select_files_title": "Select files",
        "export_select_files_hint": "Choose files to export:",
        "export_choose_folder": "Choose destination folder",
        "export_need_done": "At least one selected file is not finished.",
        "export_none_selected": "No files selected.",

        "undo_nothing": "Nothing to undo.",
        "redo_nothing": "Nothing to redo.",
        "overlay_only_after_ocr": "Overlay editing is only available after OCR is finished.",

        "new_line_from_box_title": "New line",
        "new_line_from_box_label": "Text for the new line (optional):",

        "log_added_files": "{} file(s) added to the queue.",
        "log_ocr_started": "OCR started: {} file(s), Device={}, Reading={}",
        "log_stop_requested": "OCR stop requested.",
        "log_file_started": "Starting file: {}",
        "log_file_done": "Done: {} ({} lines)",
        "log_file_error": "Error: {} -> {}",
        "log_export_done": "Export finished: {} file(s) as {} to {}",
        "log_export_single": "Export: {} -> {}",
        "log_export_log_done": "Log exported: {}",
        "act_ai_revise": "LM Revision",
        "act_ai_revise_tip": "Revise OCR text with local LLM",
        "msg_ai_started": "AI revision started...",
        "msg_ai_done": "AI revision finished.",
        "msg_ai_model_set": "AI model ID: {}",
        "msg_ai_disabled": "AI revision not available.",
        "warn_need_done_for_ai": "Please select a finished OCR item first.",
        "warn_need_ai_model": "No model was found via localhost. Please start vLLM/LM Studio or set a model ID.",
        "warn_ai_server": "LM Studio server is not reachable. Please load the model and start the local server.",
        "dlg_choose_ai_model": "LM Studio model identifier",
        "dlg_choose_ai_model_label": "Optional model ID. Leave empty to automatically use the running localhost model:",
        "log_ai_started": "AI revision started: {}",
        "log_ai_done": "AI revision finished: {}",
        "log_ai_error": "AI revision error: {} -> {}",
        "status_ai_processing": "AI revising...",
        "status_exporting": "Exporting...",

        "menu_project_save": "Save project",
        "menu_project_save_as": "Save project as...",
        "menu_project_load": "Load project...",
        "dlg_filter_project": "Bottled Kraken Project (*.json)",
        "msg_project_saved": "Project saved: {}",
        "msg_project_loaded": "Project loaded: {}",
        "warn_project_load_failed": "Project could not be loaded: {}",
        "warn_project_save_failed": "Project could not be saved: {}",
        "warn_project_file_missing": "File not found: {}",
        "line_menu_swap_with": "Swap line with…",
        "dlg_swap_title": "Swap lines",
        "dlg_swap_label": "Swap with line number (1…):",
    },

    "fr": {
        "dlg_filter_img": "Images/PDF (*.png *.jpg *.jpeg *.tif *.tiff *.bmp *.webp *.pdf)",
        "pdf_render_title": "Préparation du PDF",
        "pdf_render_label": "Rendu des pages… ({}/{}): {}",
        "app_title": "Bottled Kraken",
        "toolbar_main": "Barre d’outils",
        "menu_file": "&Fichier",
        "menu_edit": "&Édition",
        "menu_export": "Exporter en tant que...",
        "menu_exit": "Quitter",
        "menu_models": "&Modèles Kraken",
        "menu_options": "&Options",
        "menu_languages": "Langues",
        "menu_hw": "CPU/GPU",
        "menu_reading": "Direction de lecture",
        "menu_appearance": "Apparence",
        "act_clear_rec": "Retirer le modèle de reconnaissance",
        "act_clear_seg": "Retirer le modèle de segmentation",
        "act_paste_clipboard": "Coller depuis le presse-papiers",

        "log_toggle_show": "Log",
        "log_toggle_hide": "Log",
        "menu_export_log": "Exporter le log en .txt...",
        "dlg_save_log": "Enregistrer le log",
        "dlg_filter_txt": "Texte (*.txt)",
        "log_started": "Programme démarré.",
        "log_queue_cleared": "File d’attente vidée.",

        "lang_de": "Allemand",
        "lang_en": "Anglais",
        "lang_fr": "Français",

        "hw_cpu": "CPU",
        "hw_cuda": "GPU – CUDA (NVIDIA)",
        "hw_rocm": "GPU – ROCm (AMD)",
        "hw_mps": "GPU – MPS (Apple)",

        "act_undo": "Annuler",
        "act_redo": "Rétablir",

        "msg_hw_not_available": "Ce matériel n’est pas disponible sur ce système. Retour au CPU.",
        "msg_using_device": "Appareil utilisé : {}",
        "msg_detected_gpu": "Détecté : {}",
        "msg_device_cpu": "CPU",
        "msg_device_cuda": "CUDA",
        "msg_device_rocm": "ROCm",
        "msg_device_mps": "MPS",

        "act_add_files": "Charger des fichiers…",
        "act_download_model": "Télécharger le modèle (Zenodo)",
        "act_delete": "Supprimer",
        "act_rename": "Renommer...",
        "act_clear_queue": "Vider la file d’attente",
        "act_start_ocr": "Démarrer Kraken OCR",
        "act_stop_ocr": "Arrêter",
        "act_re_ocr": "Relancer",
        "act_re_ocr_tip": "Relancer le traitement du/des fichier(s) sélectionné(s)",
        "act_overlay_show": "Afficher les boîtes de superposition",

        "status_ready": "Prêt.",
        "status_waiting": "En attente",
        "status_processing": "Traitement...",
        "status_done": "Terminé",
        "status_error": "Erreur",

        "lbl_queue": "File d’attente:",
        "lbl_lines": "Lignes reconnues:",
        "col_file": "Fichier",
        "col_status": "Statut",

        "drop_hint": "Glissez-déposez des fichiers ici",
        "queue_drop_hint": "Glissez-déposez des fichiers ici",

        "info_title": "Information",
        "warn_title": "Avertissement",
        "err_title": "Erreur",

        "theme_bright": "Clair",
        "theme_dark": "Sombre",

        "warn_queue_empty": "La file d’attente est vide ou tous les éléments ont été traités.",
        "warn_select_done": "Aucun fichier chargé pour relancer l’OCR.",
        "warn_need_rec": "Veuillez d’abord sélectionner un modèle de format (reconnaissance).",
        "warn_need_seg": "Veuillez d’abord sélectionner un modèle de segmentation.",

        "msg_stopping": "Arrêt...",
        "msg_finished": "Traitement terminé.",
        "msg_device": "Appareil réglé sur: {}",
        "msg_exported": "Exporté: {}",
        "msg_loaded_rec": "Modèle de format: {}",
        "msg_loaded_seg": "Modèle de segmentation: {}",

        "err_load": "Impossible de charger l’image: {}",

        "dlg_title_rename": "Renommer",
        "dlg_label_name": "Nouveau nom de fichier:",
        "dlg_save": "Enregistrer",
        "dlg_load_img": "Choisir des images",
        "dlg_choose_rec": "le modèle de reconnaissance: ",
        "dlg_choose_seg": "le modèle de segmentation: ",
        "dlg_filter_model": "Modèles (*.mlmodel *.pt)",

        "reading_tb_lr": "Haut → Bas + Gauche → Droite",
        "reading_tb_rl": "Haut → Bas + Droite → Gauche",
        "reading_bt_lr": "Bas → Haut + Gauche → Droite",
        "reading_bt_rl": "Bas → Haut + Droite → Gauche",

        "line_menu_move_up": "Monter la ligne",
        "line_menu_move_down": "Descendre la ligne",
        "line_menu_delete": "Supprimer la ligne",
        "line_menu_add_above": "Ajouter une ligne au-dessus",
        "line_menu_add_below": "Ajouter une ligne en dessous",
        "line_menu_draw_box": "Dessiner la boîte",
        "line_menu_edit_box": "Modifier la boîte (déplacer/redimensionner)",
        "line_menu_move_to": "Déplacer la ligne vers…",

        "dlg_new_line_title": "Nouvelle ligne",
        "dlg_new_line_label": "Texte de la nouvelle ligne:",

        "dlg_move_to_title": "Déplacer la ligne",
        "dlg_move_to_label": "Numéro de ligne cible (1…):",

        "canvas_menu_add_box_draw": "Ajouter une boîte (dessiner)",
        "canvas_menu_delete_box": "Supprimer la boîte",
        "canvas_menu_edit_box": "Modifier la boîte…",
        "canvas_menu_select_line": "Sélectionner la ligne",

        "dlg_box_title": "Boîte de superposition",
        "dlg_box_left": "gauche",
        "dlg_box_top": "haut",
        "dlg_box_right": "droite",
        "dlg_box_bottom": "bas",
        "dlg_box_apply": "Appliquer",

        "export_choose_mode_title": "Export",
        "export_mode_all": "Exporter tous les fichiers",
        "export_mode_selected": "Exporter les fichiers sélectionnés",
        "export_select_files_title": "Sélectionner des fichiers",
        "export_select_files_hint": "Choisissez les fichiers à exporter :",
        "export_choose_folder": "Choisir le dossier de destination",
        "export_need_done": "Au moins un fichier sélectionné n’est pas terminé.",
        "export_none_selected": "Aucun fichier sélectionné.",

        "undo_nothing": "Rien à annuler.",
        "redo_nothing": "Rien à rétablir.",
        "overlay_only_after_ocr": "L’édition des overlays n’est disponible qu’après l’OCR.",

        "new_line_from_box_title": "Nouvelle ligne",
        "new_line_from_box_label": "Texte pour la nouvelle ligne (optionnel):",

        "log_added_files": "{} fichier(s) ajouté(s) à la file d’attente.",
        "log_ocr_started": "OCR démarré : {} fichier(s), Appareil={}, Lecture={}",
        "log_stop_requested": "Arrêt de l’OCR demandé.",
        "log_file_started": "Traitement du fichier : {}",
        "log_file_done": "Terminé : {} ({} lignes)",
        "log_file_error": "Erreur : {} -> {}",
        "log_export_done": "Export terminé : {} fichier(s) en {} vers {}",
        "log_export_single": "Export : {} -> {}",
        "log_export_log_done": "Log exporté : {}",
        "act_ai_revise": "Révision LM",
        "act_ai_revise_tip": "Réviser le texte OCR avec un LLM local",
        "msg_ai_started": "Révision IA démarrée...",
        "msg_ai_done": "Révision IA terminée.",
        "msg_ai_model_set": "ID du modèle IA : {}",
        "msg_ai_disabled": "Révision IA non disponible.",
        "warn_need_done_for_ai": "Veuillez d'abord sélectionner un fichier OCR terminé.",
        "warn_need_ai_model": "Aucun modèle trouvé via localhost. Veuillez démarrer vLLM/LM Studio ou définir un identifiant de modèle.",
        "warn_ai_server": "Serveur LM Studio inaccessible. Veuillez charger le modèle et démarrer le serveur local.",
        "dlg_choose_ai_model": "Identifiant du modèle LM Studio",
        "dlg_choose_ai_model_label": "Identifiant de modèle facultatif. Laissez vide pour utiliser automatiquement le modèle localhost en cours d'exécution :",
        "log_ai_started": "Révision IA démarrée : {}",
        "log_ai_done": "Révision IA terminée : {}",
        "log_ai_error": "Erreur de révision IA : {} -> {}",
        "status_ai_processing": "Révision IA...",
        "status_exporting": "Export en cours...",

        "menu_project_save": "Enregistrer le projet",
        "menu_project_save_as": "Enregistrer le projet sous...",
        "menu_project_load": "Charger un projet...",
        "dlg_filter_project": "Projet Bottled Kraken (*.json)",
        "msg_project_saved": "Projet enregistré : {}",
        "msg_project_loaded": "Projet chargé : {}",
        "warn_project_load_failed": "Impossible de charger le projet : {}",
        "warn_project_save_failed": "Impossible d’enregistrer le projet : {}",
        "warn_project_file_missing": "Fichier introuvable : {}",
        "line_menu_swap_with": "Échanger la ligne avec…",
        "dlg_swap_title": "Échanger les lignes",
        "dlg_swap_label": "Échanger avec le numéro de ligne (1…) :",
    }
}

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
    source_kind: str = "image"   # "image" oder "pdf_page"
    relative_path: str = ""

@dataclass
class OCRJob:
    input_paths: List[str]
    recognition_model_path: str
    segmentation_model_path: Optional[str]
    device: str
    reading_direction: int
    export_format: str
    export_dir: Optional[str]
    segmenter_mode: str = "blla"

# -----------------------------
# GEOMETRIE & SORTIERUNG
# -----------------------------
Point = Tuple[float, float]

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
ONLY_SYMBOL_LINE_RE = re.compile(r'^[\.\,\:\;\-–—_\/\\\|\(\)\[\]\{\}\'"`~^*+=<>!?·•…]+$')

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

    header, footer, midband = [], [], []
    for r, bb, dbb in items:
        if dbb[3] < (body_top - MARGIN_Y):
            header.append((r, bb, dbb))
        elif dbb[1] > (body_bot + MARGIN_Y):
            footer.append((r, bb, dbb))
        else:
            midband.append((r, bb, dbb))

    def sort_y_then_x(lst):
        return sorted(lst, key=lambda x: (cy(x[2]), cx(x[2])), reverse=rev_y)

    header_sorted = sort_y_then_x(header)
    footer_sorted = sort_y_then_x(footer)

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

        # wie alter Code: finde ab welcher y es wirklich "zweispaltig" wird
        ys = [it[2][1] for it in mid_text]  # dbb y0
        if ys:
            y_min, y_max = min(ys), max(ys)
        else:
            y_min, y_max = 0.0, float(image_height)

        step = int(max(60.0, 4.0 * med_h))
        threshold_y = y_max + 1.0  # fallback: alles "oben"

        # "links/rechts aktiv" in einem Band?
        for y0 in range(int(y_min), int(y_max), step):
            y1 = y0 + step
            left = 0
            right = 0
            for _, _, dbb in mid_text:
                if y0 <= dbb[1] < y1:
                    x_center = (dbb[0] + dbb[2]) / 2.0
                    if x_center < mid:
                        left += 1
                    else:
                        right += 1
            if left >= 2 and right >= 2:
                threshold_y = float(y0)
                break

        # Split: "top" (Einleitung/Überschrift) + Spaltenbereich
        top_mid = []
        left_col = []
        right_col = []

        for r, bb, dbb in midband:
            if is_fullwidth(dbb):
                # volle Breite -> gehört ins "top" bzw. bleibt im Flow oben
                top_mid.append((r, bb, dbb))
                continue

            if dbb[1] < threshold_y:
                top_mid.append((r, bb, dbb))
            else:
                x_center = (dbb[0] + dbb[2]) / 2.0
                if x_center < mid:
                    left_col.append((r, bb, dbb))
                else:
                    right_col.append((r, bb, dbb))

        # sortieren: wie vorher (rev_y berücksichtigt)
        top_mid_sorted = sort_y_then_x(top_mid)
        left_sorted = sort_y_then_x(left_col)
        right_sorted = sort_y_then_x(right_col)

        # Leserichtung: RL -> rechte Spalte zuerst
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
            # Fullwidth immer in "erste Spalte" (Header/Spanner behandeln wir später separat)
            if is_fullwidth(dbb):
                return 0
            # Wenn eine Box komplett links von der Trennlinie liegt -> links
            # (wichtig für rechtsbündige kurze Zeilen wie "w. Koehler.")
            for i, b in enumerate(bounds):
                if dbb[2] <= b - GUTTER:  # right edge klar links
                    return i

            # Wenn komplett rechts -> rechts
            for i, b in enumerate(bounds):
                if dbb[0] >= b + GUTTER:  # left edge klar rechts
                    continue
                # überlappt GUTTER -> entscheide über Center
                break

            x_center = (dbb[0] + dbb[2]) / 2.0
            i = 0
            for b in bounds:
                if x_center < b:
                    return i
                i += 1
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
            x = dbb[0]
            if is_fullwidth(dbb):
                return 0
            for i, b in enumerate(bounds):
                if x < b:
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
            return abs(x_center - (W / 2.0)) <= 0.18 * W  # "zentriert genug"

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
        return sorted(col, key=lambda x: (cy(x[2]), cx(x[2])), reverse=rev_y)

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

def _clean_ocr_text(text: Any) -> str:
    if text is None:
        return ""
    txt = str(text)

    # unsichtbare / störende Zeichen entfernen
    txt = txt.replace("\u00a0", " ")   # NBSP
    txt = txt.replace("\u200b", "")    # zero-width space
    txt = txt.replace("\ufeff", "")    # BOM

    # Leerraum normalisieren
    txt = re.sub(r"[ \t\r\f\v]+", " ", txt)
    return txt.strip()


def _is_effectively_empty_ocr_text(text: Any) -> bool:
    return _clean_ocr_text(text) == ""

def _is_symbol_only_line(text: Any) -> bool:
    txt = _clean_ocr_text(text)
    if not txt:
        return False

    # nur Symbol-/Trennzeichen
    if not ONLY_SYMBOL_LINE_RE.fullmatch(txt):
        return False

    # wirklich "ganze Zeile nur Zeichen"
    # ein einzelner Punkt, Doppelpunkt, Slash etc. soll weg
    return True

def _extract_json_string_lines_object(text: str):
    if not text:
        return None

    raw = str(text).strip()

    # fences entfernen
    raw = re.sub(r"^\s*```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```\s*$", "", raw)

    # 1) direktes JSON
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and isinstance(data.get("lines"), list):
            lines = data["lines"]
            if all(isinstance(x, str) for x in lines):
                return lines
    except Exception:
        pass

    # 2) erstes JSON-Objekt extrahieren
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        chunk = raw[start:end + 1]

        try:
            data = json.loads(chunk)
            if isinstance(data, dict) and isinstance(data.get("lines"), list):
                lines = data["lines"]
                if all(isinstance(x, str) for x in lines):
                    return lines
        except Exception:
            pass

        repaired = re.sub(r",(\s*[}\]])", r"\1", chunk)
        try:
            data = json.loads(repaired)
            if isinstance(data, dict) and isinstance(data.get("lines"), list):
                lines = data["lines"]
                if all(isinstance(x, str) for x in lines):
                    return lines
        except Exception:
            pass

    # 3) typografische Quotes als letzter Fallback
    normalized = raw
    normalized = normalized.replace("’", "'").replace("‘", "'")
    normalized = normalized.replace("„", "\"").replace("“", "\"").replace("”", "\"")

    try:
        data = json.loads(normalized)
        if isinstance(data, dict) and isinstance(data.get("lines"), list):
            lines = data["lines"]
            if all(isinstance(x, str) for x in lines):
                return lines
    except Exception:
        pass

    return None

def _extract_json_lines_object(text: str):
    if not text:
        return None

    raw = str(text).strip()

    # fences entfernen
    raw = re.sub(r"^\s*```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```\s*$", "", raw)

    # 1) ZUERST IMMER das rohe JSON versuchen
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and isinstance(data.get("lines"), list):
            return data["lines"]
        if isinstance(data, list):
            return data
    except Exception:
        pass

    # 2) Erstes JSON-Objekt isolieren und roh parsen
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        chunk = raw[start:end + 1]

        try:
            data = json.loads(chunk)
            if isinstance(data, dict) and isinstance(data.get("lines"), list):
                return data["lines"]
            if isinstance(data, list):
                return data
        except Exception:
            pass

        # 3) nur sehr konservative Reparatur: trailing commas
        repaired = re.sub(r",(\s*[}\]])", r"\1", chunk)
        try:
            data = json.loads(repaired)
            if isinstance(data, dict) and isinstance(data.get("lines"), list):
                return data["lines"]
            if isinstance(data, list):
                return data
        except Exception:
            pass

    # 4) LETZTER FALLBACK:
    # nur wenn das Modell kein sauberes JSON geliefert hat, typografische Quotes glätten
    normalized = raw
    normalized = normalized.replace("’", "'").replace("‘", "'")

    # WICHTIG:
    # „ “ nur hier ganz am Ende als Notfall-Fallback,
    # niemals vor dem ersten json.loads()
    normalized = normalized.replace("„", "\"").replace("“", "\"").replace("”", "\"")

    try:
        data = json.loads(normalized)
        if isinstance(data, dict) and isinstance(data.get("lines"), list):
            return data["lines"]
        if isinstance(data, list):
            return data
    except Exception:
        pass

    # 5) lines-array direkt extrahieren
    m = re.search(r'"lines"\s*:\s*(\[[\s\S]*\])', raw)
    if m:
        arr_txt = m.group(1)
        arr_txt = re.sub(r",(\s*[}\]])", r"\1", arr_txt)
        try:
            arr = json.loads(arr_txt)
            if isinstance(arr, list):
                return arr
        except Exception:
            pass

    return None

def _pil_to_data_url(
    im: Image.Image,
    max_side: int = 5000,
    image_format: str = "JPEG",
    jpeg_quality: int = 85,
) -> str:
    im = im.convert("RGB")
    w, h = im.size

    scale = min(max_side / max(w, h), 1.0)
    if scale < 1.0:
        im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    buf = BytesIO()

    fmt = (image_format or "JPEG").upper()
    if fmt == "JPEG":
        im.save(buf, format="JPEG", quality=int(jpeg_quality), optimize=True)
        mime = "image/jpeg"
    else:
        im.save(buf, format="PNG")
        mime = "image/png"

    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:{mime};base64,{b64}"

def _image_to_data_url(path: str) -> str:
    im = _load_image_gray(path)
    return _pil_to_data_url(im)

def _page_to_data_url(
    path: str,
    max_side: int = 5000,
    image_format: str = "JPEG",
    jpeg_quality: int = 85,
) -> str:
    im = _load_image_color(path)
    return _pil_to_data_url(
        im,
        max_side=max_side,
        image_format=image_format,
        jpeg_quality=jpeg_quality,
    )

def _page_to_small_jpeg_data_url(
    path: str,
    max_side: int = 1200,
    jpeg_quality: int = 65,
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
        image_format="JPEG",
        jpeg_quality=jpeg_quality,
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
    pad_x: int = 80,
    pad_y: int = 30,
    extra_context_y: int = 20,
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
# SKALIERBARES / VERSCHIEBBARES RECHTECK-ITEM
# -----------------------------
class ResizableRectItem(QGraphicsRectItem):
    #    Verschiebbares + skalierbares Rechteck.
    #    Ruft on_changed(idx, QRectF(Szenenkoordinaten)) nach dem Loslassen der Maus auf.

    HANDLE_PAD = 6.0

    def __init__(self, rect: QRectF, idx: int, on_changed: Callable[[int, QRectF], None],
                 on_double_clicked: Optional[Callable[[int], None]] = None):
        super().__init__(rect)
        self.idx = idx
        self._on_changed = on_changed
        self._on_double_clicked = on_double_clicked

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsRectItem.ItemIsMovable, True)

        self._mode = "none"
        self._resize_edges = (False, False, False, False)  # L,T,R,B
        self._press_item_pos: Optional[QPointF] = None
        self._press_rect: Optional[QRectF] = None

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
            l, t, r, b = self._hit_test_edges(event.pos())
            if l or t or r or b:
                self._mode = "resize"
                self._resize_edges = (l, t, r, b)
                self._press_item_pos = QPointF(event.pos())
                self._press_rect = QRectF(self.rect())
                self.setFlag(QGraphicsRectItem.ItemIsMovable, False)
                event.accept()
                return
            else:
                self._mode = "move"
                self.setFlag(QGraphicsRectItem.ItemIsMovable, True)
                self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._mode == "resize" and self._press_item_pos is not None and self._press_rect is not None:
            delta = event.pos() - self._press_item_pos
            r = QRectF(self._press_rect)

            l, t, rr, b = self._resize_edges
            if l:
                r.setLeft(r.left() + delta.x())
            if rr:
                r.setRight(r.right() + delta.x())
            if t:
                r.setTop(r.top() + delta.y())
            if b:
                r.setBottom(r.bottom() + delta.y())

            r = r.normalized()
            if r.width() < 5:
                r.setWidth(5)
            if r.height() < 5:
                r.setHeight(5)

            self.setRect(r)
            event.accept()
            return
        super().mouseMoveEvent(event)

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

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.setCursor(Qt.OpenHandCursor)

        was_resize_or_move = (self._mode in ("resize", "move"))
        self._mode = "none"
        self._press_item_pos = None
        self._press_rect = None

        self.setFlag(QGraphicsRectItem.ItemIsMovable, True)

        if was_resize_or_move:
            try:
                if callable(self._on_changed):
                    scene_rect = self.mapRectToScene(self.rect()).normalized()
                    self._on_changed(self.idx, scene_rect)
            except Exception:
                pass

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
        if event.key() == Qt.Key_Delete:
            self.delete_pressed.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if not event.mimeData().hasUrls():
            event.ignore()
            return
        files = []
        for u in event.mimeData().urls():
            p = u.toLocalFile()
            if p and os.path.exists(p) and is_supported_input(p):
                files.append(p)
        if files:
            self.files_dropped.emit(files)
            event.acceptProposedAction()
        else:
            event.ignore()

# -----------------------------
# ZEILENLISTE (Entf + Drag&Drop zum Umordnen)
# -----------------------------
class LinesListWidget(QListWidget):
    delete_pressed = Signal()
    reorder_committed = Signal(list, int)  # new_order (list of old indices), current_row after drop

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDragDropMode(QAbstractItemView.InternalMove)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.delete_pressed.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def dropEvent(self, event):
        super().dropEvent(event)
        order = []
        for i in range(self.count()):
            it = self.item(i)
            idx = it.data(Qt.UserRole)
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

        # Nur aktiv, nachdem die OCR abgeschlossen ist
        self._overlay_enabled = False

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
            self._bg_color = QColor("#ffffff")
            self._pen_normal.setColor(QColor("#d00000"))
            self._pen_selected.setColor(QColor("#0000ff"))
        self.setBackgroundBrush(QBrush(self._bg_color))
        if self._pixmap_item and hasattr(self, "_last_recs"):
            self.refresh_overlays()
        else:
            self._show_drop_hint()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if not event.mimeData().hasUrls():
            event.ignore()
            return
        files = []
        for u in event.mimeData().urls():
            p = u.toLocalFile()
            if p and os.path.exists(p) and is_supported_input(p):
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

    def contextMenuEvent(self, event):
        pos = event.pos()
        item = self.itemAt(pos)

        menu = QMenu(self)
        tr = self.tr_func

        if not self._overlay_enabled:
            disabled = menu.addAction(tr("overlay_only_after_ocr") if tr else "Overlay-Bearbeitung erst nach abgeschlossener OCR möglich.")
            disabled.setEnabled(False)
            menu.exec(event.globalPos())
            return

        if isinstance(item, ResizableRectItem):
            idx = item.idx
            act_edit = menu.addAction(tr("canvas_menu_edit_box") if tr else "Edit overlay box...")
            act_del = menu.addAction(tr("canvas_menu_delete_box") if tr else "Delete overlay box")
            menu.addSeparator()
            act_add_draw = menu.addAction(tr("canvas_menu_add_box_draw") if tr else "Add overlay box (draw)")

            chosen = menu.exec(event.globalPos())
            if not chosen:
                return
            elif chosen == act_edit:
                self.rect_clicked.emit(idx)
                self.select_idx(idx, center=True)
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
        if self._draw_mode and event.button() == Qt.LeftButton:
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
            self._draw_rect_item.setZValue(1000)
            self.scene.addItem(self._draw_rect_item)
            return

        if (not self._draw_mode) and event.button() == Qt.LeftButton:
            it = self.itemAt(self._event_point(event))

            # Wenn gezoomt und NICHT auf Overlay-Box: direkt per Maus pannen (LMB gedrückt halten)
            if self._zoom > 1.01 and not isinstance(it, ResizableRectItem):
                self._mouse_panning = True
                self._pan_start = self._event_point(event)  # viewport coords
                self._pan_start_h = self.horizontalScrollBar().value()
                self._pan_start_v = self.verticalScrollBar().value()
                self.setCursor(Qt.ClosedHandCursor)
                event.accept()
                return

        item = self.itemAt(self._event_point(event))
        if isinstance(item, ResizableRectItem):
            self.rect_clicked.emit(item.idx)
            # WICHTIG: nicht return -> Item muss Maus-Events bekommen für Move/Resize
            super().mousePressEvent(event)
            return

        if event.button() == Qt.LeftButton and not self._pixmap_item:
            self.canvas_clicked.emit()

        item = self.itemAt(self._event_point(event))
        if isinstance(item, ResizableRectItem):
            self.rect_clicked.emit(item.idx)
            return

        # Klick auf Bild/Leere Fläche: keine Drag/Pan-Aktion starten
        if event.button() == Qt.LeftButton:
            it = self.itemAt(self._event_point(event))

            # falls Pixmap oder Leere Fläche geklickt -> nur deselect + accept
            if (it is None) or (self._pixmap_item is not None and it == self._pixmap_item):
                self.select_idx(None, center=False)
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
        # NEU: Maus-Panning
        if self._mouse_panning:
            p = self._event_point(event)
            delta = p - self._pan_start
            self.horizontalScrollBar().setValue(self._pan_start_h - delta.x())
            self.verticalScrollBar().setValue(self._pan_start_v - delta.y())
            event.accept()
            return

        # Box-Zeichnen wie gehabt
        if self._draw_mode and self._draw_start and self._draw_rect_item is not None:
            sp = self.mapToScene(self._event_point(event))
            r = QRectF(self._draw_start, sp).normalized()
            if isValid(self._draw_rect_item):
                self._draw_rect_item.setRect(r)
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

        if event.button() == Qt.LeftButton and self._mouse_panning:
            self._mouse_panning = False
            if self._zoom > 1.01 and not self._draw_mode:
                self.setCursor(Qt.OpenHandCursor)
            else:
                self.unsetCursor()
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def clear_all(self):
        self.stop_draw_box_mode()
        self.scene.clear()
        self._pixmap_item = None
        self._rects.clear()
        self._labels.clear()
        self._selected_idx = None
        self._drop_text = None
        self.resetTransform()
        self._zoom = 1.0
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
        txt = self.tr_func("drop_hint") if self.tr_func else "Datei(en) hierher ziehen und ablegen"

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
            # Zoom aus der tatsächlichen Transformationsmatrix synchronisieren
            try:
                self._zoom = float(self.transform().m11())
            except Exception:
                self._zoom = 1.0

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
            self.scene.addItem(lab)
            self._labels[rv.idx] = lab

    def select_idx(self, idx: Optional[int], center: bool = True):
        for rect in self._rects.values():
            if isValid(rect):
                rect.setPen(self._pen_normal)
                rect.setBrush(self._brush_fill)
        self._selected_idx = idx
        if idx is not None and idx in self._rects:
            rect = self._rects[idx]
            if isValid(rect):
                rect.setPen(self._pen_selected)
                rect.setBrush(self._brush_selected)
                if center:
                    self.centerOn(rect)

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
        if self._zoom > 1.01 and not self._draw_mode:
            self.setCursor(Qt.OpenHandCursor)
        elif not self._draw_mode:
            self.unsetCursor()

class PDFRenderWorker(QThread):
    progress = Signal(int, int, str)          # current, total, pdf_path
    finished_pdf = Signal(str, list)          # pdf_path, out_paths
    failed_pdf = Signal(str, str)             # pdf_path, error_message

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

        except Exception as e:
            self.failed_pdf.emit(self.pdf_path, str(e))

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
            # Gewähltes Backend-Label (cuda/rocm/mps/cpu) + tatsächliches torch-Device anzeigen
            self.device_resolved.emit(f"{self._device_label} -> {self._device}")
            self._emit_gpu_info(self._device)
        if self._rec_model is None:
            self._rec_model = self._load_rec_model(self.job.recognition_model_path, self._device)
        mode = getattr(self.job, "segmenter_mode", "blla")
        if mode == "blla":
            if self._seg_model is None:
                if not self.job.segmentation_model_path:
                    raise ValueError("No baseline model selected.")
                self._seg_model = self._load_seg_model(self.job.segmentation_model_path, self._device)
        else:
            self._seg_model = None

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
    def _ocr_one(self, img_path: str, file_idx: int, total_files: int):
        self.file_started.emit(img_path)
        try:
            # --- Bild einmalig laden (Graustufe) ---
            im = _load_image_gray(img_path)

            # --- FIX A: zu kleine Bilder hochskalieren (verhindert Baselines < 5px) ---
            min_dim = min(im.size)
            if min_dim < 1200:
                scale = 2 if min_dim >= 700 else 3
                im = im.resize((im.size[0] * scale, im.size[1] * scale), Image.BICUBIC)

            # --- Segmentierung ---
            if getattr(self.job, "segmenter_mode", "blla") == "pageseg":
                # pageseg braucht ein bi-level Bild (Mode "1")
                bw = binarization.nlbin(im)  # empfohlen für legacy pageseg
                if getattr(bw, "mode", None) != "1":
                    bw = bw.convert("1")
                seg = pageseg.segment(bw)
            else:
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
            except Exception as e:
                self.file_error.emit(img_path, str(e))
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
            page_w, page_h = im.size

            for r in kr_sorted:
                pred = getattr(r, "prediction", None)
                if pred is None:
                    continue

                txt = _clean_ocr_text(pred)
                if _is_effectively_empty_ocr_text(txt) or _is_symbol_only_line(txt):
                    continue

                bb = record_bbox(r)
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
                if _is_effectively_empty_ocr_text(rv.text) or _is_symbol_only_line(rv.text):
                    continue

                rv.idx = len(filtered_record_views)
                filtered_record_views.append(rv)
                filtered_lines.append(rv.text)

            record_views = filtered_record_views
            lines = filtered_lines

            self._emit_overall_progress(file_idx, total_files, 1.0)
            text = "\n".join(lines).strip()
            self.file_done.emit(img_path, text, kr_sorted, im, record_views)

        except Exception as e:
            self.file_error.emit(img_path, str(e))

    def run(self):
        try:
            if not os.path.exists(self.job.recognition_model_path):
                raise ValueError("Recognition model not found.")
            mode = getattr(self.job, "segmenter_mode", "blla")
            if mode == "blla":
                if not os.path.exists(self.job.segmentation_model_path or ""):
                    raise ValueError("Baseline model not found.")

            self._ensure_models_loaded()

            total = len(self.job.input_paths)
            for i, path in enumerate(self.job.input_paths):
                if self.isInterruptionRequested():
                    break
                self._emit_overall_progress(i, total, 0.0)
                self._ocr_one(path, i, total)

            self.progress.emit(100)
            self.finished_batch.emit()
        except Exception as e:
            self.failed.emit(str(e))

class AIBatchRevisionWorker(QThread):
    file_started = Signal(str, int, int)          # path, current, total
    file_finished = Signal(str, list, int, int)   # path, revised_lines, current, total
    file_failed = Signal(str, str, int, int)      # path, error, current, total
    progress_changed = Signal(int)                # overall 0..100
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
            parent=None
    ):
        super().__init__(parent)
        self.items = items
        self.lm_model = lm_model
        self.endpoint = endpoint
        self.enable_thinking = enable_thinking
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.presence_penalty = presence_penalty
        self.repetition_penalty = repetition_penalty
        self.min_p = min_p
        self.max_tokens = max_tokens
        self._current_worker = None

    def cancel(self):
        self.requestInterruption()

        w = self._current_worker
        if w is not None:
            try:
                w.cancel()
            except Exception:
                pass

    def run(self):
        total = len(self.items)
        if total <= 0:
            self.finished_batch.emit()
            return

        for i, task in enumerate(self.items, start=1):
            if self.isInterruptionRequested():
                break

            self.file_started.emit(task.path, i, total)
            self.status_changed.emit(f"KI-Datei {i}/{total}: {os.path.basename(task.path)}")

            try:
                _, _, _, recs = task.results
                worker = AIRevisionWorker(
                    path=task.path,
                    recs=recs,
                    lm_model=self.lm_model,
                    endpoint=self.endpoint,
                    enable_thinking=self.enable_thinking,
                    source_kind=task.source_kind,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    top_k=self.top_k,
                    presence_penalty=self.presence_penalty,
                    repetition_penalty=self.repetition_penalty,
                    min_p=self.min_p,
                    max_tokens=self.max_tokens,
                )
                self._current_worker = worker
                revised_holder = {"lines": None, "error": None}

                def _done(path, lines):
                    revised_holder["lines"] = lines

                def _fail(path, msg):
                    revised_holder["error"] = msg

                worker.finished_revision.connect(_done)
                worker.failed_revision.connect(_fail)

                worker.run()  # absichtlich synchron innerhalb des Batch-Threads
                self._current_worker = None

                if revised_holder["error"] is not None:
                    self.file_failed.emit(task.path, revised_holder["error"], i, total)
                else:
                    self.file_finished.emit(task.path, revised_holder["lines"], i, total)

            except Exception as e:
                self.file_failed.emit(task.path, str(e), i, total)

            percent = int((i / total) * 100)
            self.progress_changed.emit(percent)

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
    finished_revision = Signal(str, list)   # path, revised_lines
    failed_revision = Signal(str, str)      # path, error
    progress_changed = Signal(int)          # 0..100
    status_changed = Signal(str)            # live text

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
            parent=None
    ):
        super().__init__(parent)
        self.path = path
        self.recs = recs
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

    def _request_page_ocr_with_fixed_linecount(self, page_data_url: str, recs: List[RecordView]) -> List[str]:
        img_w, img_h = _load_image_color(self.path).size

        line_specs = []
        for rv in recs:
            line_specs.append({
                "idx": int(rv.idx),
                "bbox": _normalize_bbox(rv.bbox, img_w, img_h)
            })

        system_prompt = (
            "Du bist ein hochpräziser OCR- und Transkriptionsassistent für historische deutsche Drucke und Handschriften. "
            "Du bist spezialisiert auf Fraktur, Sütterlin, Kurrent und verwandte ältere deutsche Schriftformen. "
            "Lies den Text frei direkt aus dem Bild. "
            "Das Bild ist die einzige Wahrheitsquelle. "
            "Du darfst den OCR-Hinweis nicht rekonstruieren, sondern musst den Text wirklich aus dem Bild lesen. "
            "Bewahre historische Schreibweisen, Eigennamen, Abkürzungen und alte Orthographie so genau wie möglich. "
            "Modernisiere oder normalisiere nichts. "
            "Wenn einzelne Zeichen unsicher sind, nutze den visuellen und sprachlichen Kontext historischer deutscher Texte. "
            "Die vorgegebene Zeilenanzahl ist nur ein Strukturrahmen. "
            "Du musst den frei gelesenen Text passend in genau diese Anzahl von Zeilen eintragen. "
            "Antworte ausschließlich mit gültigem JSON. "
            "Kein Markdown. Kein Zusatztext. Kein Kommentar."
        )

        user_prompt = (
            "Lies den Text direkt aus dem Bild.\n\n"
            "Du musst dich exakt an die vorgegebene Kraken-Zeilenstruktur halten.\n"
            f"Es gibt genau {len(recs)} Zielzeilen.\n"
            "Für jede Zielzeile gibt es einen festen idx.\n"
            "Gib für jeden idx genau den Text der zugehörigen handschriftlichen Zeile zurück.\n"
            "Verschiebe keinen Text zwischen den idx-Werten.\n"
            "Lasse keinen idx aus.\n"
            "Die bbox dient nur als Orientierung, welche visuelle Zeile gemeint ist.\n\n"
            "Wichtig:\n"
            f"- Gib genau {len(recs)} Einträge im Feld lines zurück\n"
            f"- Die idx-Werte müssen exakt 0 bis {len(recs) - 1} sein\n"
            "- Gib NUR ein JSON-Objekt zurück\n"
            "- Kein Markdown\n"
            "- Keine Analyse\n"
            "- Keine zusätzlichen Sätze\n"
            "- Keine Kommentare\n"
            "- Wenn eine Zeile unklar ist, gib den bestmöglichen Text zurück\n"
            "- Wenn eine Zielzeile wirklich leer wäre, gib für diese Zeile text als leeren String zurück\n\n"
            "Kraken-Zielzeilenstruktur:\n"
            f"{json.dumps(line_specs, ensure_ascii=False)}\n\n"
            "Antwortformat exakt so:\n"
            "{\"lines\":[{\"idx\":0,\"text\":\"...\"},{\"idx\":1,\"text\":\"...\"}]}"
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

        lines = _extract_json_lines_object(content)

        if not isinstance(lines, list):
            raise ValueError(
                "Seiten-OCR lieferte kein gültiges JSON-Objekt.\n\n"
                f"Extrahierter Content:\n{content[:3000] if content else '<leer>'}"
            )

        out = [""] * len(recs)

        for item in lines:
            if not isinstance(item, dict):
                continue
            idx = item.get("idx")
            txt = str(item.get("text", "")).strip()
            if isinstance(idx, int) and 0 <= idx < len(recs):
                out[idx] = txt

        # Wenn fast alles leer ist -> kompletter Fehler
        filled = sum(1 for x in out if str(x).strip())
        if filled < max(1, int(len(recs) * 0.6)):
            raise ValueError(
                f"Seiten-OCR lieferte zu wenig verwertbare Zeilen: {filled}/{len(recs)}"
            )

        # Leere Einzelzeilen gezielt mit Kraken-Original auffüllen,
        # damit die Zeilenstruktur exakt erhalten bleibt
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
        system_prompt = (
            "Du bist ein präziser OCR- und Transkriptionsassistent für historische deutsche Handschriften. "
            "Lies den Text frei direkt aus dem Bild. "
            "Das Bild ist die einzige Wahrheitsquelle. "
            "Du darfst nicht den OCR-Hinweis rekonstruieren, sondern musst das Bild selbst lesen. "
            "Die von außen vorgegebene Zeilenanzahl ist nur ein Strukturrahmen. "
            "Du musst den frei gelesenen Text passend in genau diese Anzahl von Zeilen eintragen. "
            "Antworte ausschließlich mit gültigem JSON. "
            "Kein Markdown. Kein Zusatztext. Kein Kommentar."
        )

        user_prompt = (
            "Lies genau die zentrale handschriftliche Zeile aus dem Bildausschnitt.\n"
            "Gib ausschließlich genau EIN JSON-Objekt zurück.\n"
            "Kein Markdown. Kein ```json. Kein Kommentar. Kein Zusatztext.\n"
            "Wichtig:\n"
            "- doppelte Anführungszeichen innerhalb von text immer als \\\" escapen\n"
            "- keine Ausgabe vor oder nach dem JSON\n"
            "Format:\n"
            "{\"text\":\"...\"}\n\n"
            f"Zeilenindex: {idx}\n"
            f"Aktueller OCR-Text als schwacher Hinweis:\n{current_text}"
        )

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
            txt = str(obj.get("text", "")).strip()
            if txt or txt == "":
                return txt

        lines = _extract_text_lines(content)
        if lines:
            return lines[0].strip()

        return current_text

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
            raise RuntimeError("Überarbeitung abgebrochen.")

        body = json.dumps(payload).encode("utf-8")
        parsed = urllib.parse.urlparse(self.endpoint)

        if parsed.scheme not in ("http", "https"):
            raise RuntimeError(f"Nicht unterstütztes Schema: {parsed.scheme}")

        host = parsed.hostname
        port = parsed.port
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query

        if not host:
            raise RuntimeError("Ungültiger Endpoint.")

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
                raise RuntimeError("Überarbeitung abgebrochen.")

            resp = conn.getresponse()
            raw = resp.read().decode("utf-8", errors="replace")

            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError("Überarbeitung abgebrochen.")

            if resp.status >= 400:
                raise RuntimeError(f"HTTP {resp.status}: {raw}")

            return json.loads(raw)

        except socket.timeout:
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError("Überarbeitung abgebrochen.")
            raise RuntimeError("Zeitüberschreitung bei LM Studio")

        except json.JSONDecodeError as e:
            raise RuntimeError(f"Ungültige JSON-Antwort von LM Studio: {e}")

        except Exception as e:
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError("Überarbeitung abgebrochen.")
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
                f"LM Studio lieferte keine choices. Antwort:\n{json.dumps(data, ensure_ascii=False)[:3000]}"
            )

        choice0 = choices[0] or {}
        message = choice0.get("message", {}) if isinstance(choice0, dict) else {}

        def flatten(val):
            if val is None:
                return ""
            if isinstance(val, str):
                return val.strip()
            if isinstance(val, list):
                parts = []
                for part in val:
                    if isinstance(part, str) and part.strip():
                        parts.append(part.strip())
                    elif isinstance(part, dict):
                        # NUR echte Antwortfelder, KEIN reasoning_content
                        for key in ("text", "content", "output_text"):
                            v = part.get(key)
                            if isinstance(v, str) and v.strip():
                                parts.append(v.strip())
                return "\n".join(parts).strip()
            if isinstance(val, dict):
                for key in ("text", "content", "output_text"):
                    v = val.get(key)
                    if isinstance(v, str) and v.strip():
                        return v.strip()
            return str(val).strip()

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
                    "Das Modell hat nur reasoning_content geliefert und wurde vor der eigentlichen JSON-Antwort abgeschnitten "
                    "(finish_reason=length). Erhöhe max_tokens oder verwende ein nicht-thinkendes Modell."
                )

            raise RuntimeError(
                "Das Modell hat nur reasoning_content geliefert, aber keinen normalen content. "
                "Verwende am besten ein nicht-thinkendes Modell oder erzwinge text/json ohne reasoning."
            )

        raise RuntimeError("LM Studio lieferte keinen verwertbaren Antwortinhalt.")

    def _request_block_reread(
            self,
            block_data_url: str,
            start_idx: int,
            end_idx: int,
            current_lines: List[str],
    ) -> List[str]:
        count = end_idx - start_idx

        system_prompt = (
            "Du bist ein präziser OCR- und Transkriptionsassistent für historische deutsche Handschriften. "
            "Lies den Text frei direkt aus dem Bild. "
            "Das Bild ist die einzige Wahrheitsquelle. "
            "Du darfst nicht den OCR-Hinweis rekonstruieren, sondern musst das Bild selbst lesen. "
            "Die von außen vorgegebene Zeilenanzahl ist nur ein Strukturrahmen. "
            "Du musst den frei gelesenen Text passend in genau diese Anzahl von Zeilen eintragen. "
            "Antworte ausschließlich mit gültigem JSON. "
            "Kein Markdown. Kein Zusatztext. Kein Kommentar."
        )

        joined_hint = "\n".join(
            f"{start_idx + i}: {txt}" for i, txt in enumerate(current_lines)
        )

        user_prompt = (
            "Lies die handschriftlichen Zeilen im Bildausschnitt.\n"
            "Gib ausschließlich genau EIN JSON-Objekt zurück.\n"
            "Kein Markdown. Kein ```json. Kein Kommentar. Kein Zusatztext.\n"
            f"Es müssen genau {count} Einträge im Feld lines stehen.\n"
            "Wichtig:\n"
            "- doppelte Anführungszeichen innerhalb von text immer als \\\" escapen\n"
            "- keine weiteren Felder außer idx und text\n"
            "- keine Ausgabe vor oder nach dem JSON\n"
            "Format:\n"
            "{\"lines\":[{\"idx\":0,\"text\":\"...\"}]}\n\n"
            "Die idx-Werte müssen lokal bei 0 beginnen.\n"
            "Aktueller OCR-Hinweis:\n"
            f"{joined_hint}"
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

        lines = _extract_json_lines_object(content)
        if not isinstance(lines, list):
            return current_lines

        out = [""] * count
        for item in lines:
            if not isinstance(item, dict):
                continue
            idx = item.get("idx")
            txt = str(item.get("text", "")).strip()
            if isinstance(idx, int) and 0 <= idx < count:
                out[idx] = txt

        fixed = []
        for i in range(count):
            txt = out[i].strip()
            if txt:
                fixed.append(txt)
            else:
                fixed.append(current_lines[i])

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
            self.failed_revision.emit(self.path, "Überarbeitung abgebrochen.")
            return
        try:
            original_lines = [rv.text for rv in self.recs]

            if not self.recs:
                self.finished_revision.emit(self.path, [])
                return

            self.status_changed.emit(f"Starte freie KI-OCR: {os.path.basename(self.path)}")
            self.progress_changed.emit(0)

            self.status_changed.emit(
                f"Freies Seiten-OCR mit fixer Zeilenanzahl: {os.path.basename(self.path)}"
            )

            revised_all = None
            last_err = None

            retry_configs = [
                {"max_side": 2000, "image_format": "JPEG", "jpeg_quality": 100},
                {"max_side": 1500, "image_format": "JPEG", "jpeg_quality": 85},
                {"max_side": 1000, "image_format": "JPEG", "jpeg_quality": 70},
            ]

            for cfg in retry_configs:
                if self._cancelled or self.isInterruptionRequested():
                    raise RuntimeError("Überarbeitung abgebrochen.")

                try:
                    self.status_changed.emit(
                        f"Vision-OCR Versuch: {cfg['max_side']}px {cfg['image_format']}"
                    )
                    page_data_url = _page_to_data_url(
                        self.path,
                        max_side=cfg["max_side"],
                        image_format=cfg["image_format"],
                        jpeg_quality=cfg["jpeg_quality"],
                    )

                    if self._cancelled or self.isInterruptionRequested():
                        raise RuntimeError("Überarbeitung abgebrochen.")

                    revised_all = self._request_page_ocr_with_fixed_linecount(page_data_url, self.recs)
                    break
                except Exception as e:
                    last_err = e
                    if self._is_image_processing_error(e):
                        continue
                    raise

            if revised_all is None:
                # Spezial-Fallback nur für PDF-Seiten:
                # nochmal als stark verkleinertes JPEG versuchen
                if self.source_kind == "pdf_page":
                    try:
                        self.status_changed.emit("PDF-Fallback: stark verkleinertes JPEG wird versucht")
                        page_data_url = _page_to_small_jpeg_data_url(
                            self.path,
                            max_side=1200,
                            jpeg_quality=65,
                        )
                        revised_all = self._request_page_ocr_with_fixed_linecount(page_data_url, self.recs)
                    except Exception as pdf_fallback_err:
                        last_err = pdf_fallback_err

                if revised_all is None:
                    raise RuntimeError(f"Bild konnte vom Vision-Modell nicht verarbeitet werden: {last_err}")

            if len(revised_all) != len(original_lines):
                raise ValueError(
                    f"Seiten-OCR gab {len(revised_all)} statt {len(original_lines)} Zeilen zurück."
                )

            if len(revised_all) != len(self.recs):
                raise ValueError(
                    f"LLM gab {len(revised_all)} Zeilen zurück, erwartet wurden {len(self.recs)}."
                )

            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError("Überarbeitung abgebrochen.")

            self.status_changed.emit(f"Freie KI-OCR abgeschlossen: {os.path.basename(self.path)}")
            self.progress_changed.emit(100)
            self.finished_revision.emit(self.path, revised_all)

        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode("utf-8", errors="replace")
            except Exception:
                body = str(e)
            self.failed_revision.emit(self.path, f"HTTP-Fehler: {e}\n{body}")

        except urllib.error.URLError as e:
            self.failed_revision.emit(self.path, f"LM Studio nicht erreichbar: {e}")

        except socket.timeout:
            self.failed_revision.emit(self.path, "Zeitüberschreitung beim Warten auf LM Studio.")

        except Exception as e:
            self.failed_revision.emit(self.path, str(e))

class ProgressStatusDialog(QDialog):
    cancel_requested = Signal()

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)

        lay = QVBoxLayout(self)

        self.lbl_status = QLabel("Bereit")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setMinimumWidth(320)
        self.lbl_status.setMaximumWidth(520)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_cancel.clicked.connect(self.cancel_requested.emit)

        lay.addWidget(self.lbl_status)
        lay.addWidget(self.progress)
        lay.addWidget(self.btn_cancel)

        self.adjustSize()

    def set_status(self, text: str):
        self.lbl_status.setText(text)
        self.adjustSize()

    def set_progress(self, value: int):
        self.progress.setValue(max(0, min(100, int(value))))

# -----------------------------
# EXPORT-DIALOGE
# -----------------------------

class ExportWorker(QThread):
    file_started = Signal(str, int, int)   # display_name, current, total
    file_done = Signal(str, str, int, int) # display_name, dest_path, current, total
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

# -----------------------------
# HAUPTFENSTER
# -----------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(1600, 900)
        self.setAcceptDrops(True)

        self.temp_dirs_created = set()
        QApplication.instance().installEventFilter(self)

        self.ai_worker: Optional[AIRevisionWorker] = None
        self.ai_model_id = ""
        self.ai_endpoint = "http://127.0.0.1:1234/v1/chat/completions"
        self.ai_base_url = None

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

        self.ai_available_models: List[str] = []
        self.ai_model_actions: Dict[str, QAction] = {}
        self.ai_model_group: Optional[QActionGroup] = None

        self.current_lang = "de"
        self.log_lang = self._detect_system_lang()
        self.reading_direction = READING_MODES["TB_LR"]
        self.device_str = "cpu"
        self.show_overlay = True
        self.model_path = ""
        self.seg_model_path = ""
        self.rec_model_candidates = []
        self.default_seg_model = ""
        self.current_export_dir = ""
        self.current_theme = "bright"
        self.current_segmenter_mode = "blla"

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
        self.queue_table.delete_pressed.connect(self._delete_queue_via_key)
        self.queue_table.files_dropped.connect(self.add_files_to_queue)
        self.queue_table.table_resized.connect(self._fit_queue_columns_exact)

        header = self.queue_table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setSectionsMovable(False)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.sectionResized.connect(self._on_queue_header_resized)
        self.queue_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        header.sectionClicked.connect(self._on_queue_header_clicked)

        # Hinweis-Overlay für den Wartebereich
        self.queue_hint = QLabel(self._tr("queue_drop_hint"), self.queue_table.viewport())
        self.queue_hint.setAlignment(Qt.AlignCenter)
        self.queue_hint.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.queue_hint.setStyleSheet("color: rgba(180,180,180,180); font-style: italic;")
        self.queue_hint.hide()

        # Zeilenliste
        self.list_lines = LinesListWidget()
        self.list_lines.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_lines.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.list_lines.currentRowChanged.connect(self.on_line_selected)
        self.list_lines.itemChanged.connect(self.on_line_item_edited)
        self.list_lines.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_lines.customContextMenuRequested.connect(self.lines_context_menu)
        self.list_lines.delete_pressed.connect(self._delete_current_line_via_key)
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
        self.act_add = QAction(QIcon.fromTheme("document-open"), self._tr("act_add_files"), self)
        self.act_add.triggered.connect(self.choose_files)

        self.act_paste_files = QAction("Aus Zwischenablage einfügen", self)
        self.act_paste_files.setShortcut(QKeySequence.Paste)
        self.act_paste_files.triggered.connect(self.paste_files_from_clipboard)
        self.addAction(self.act_paste_files)

        self.shortcut_paste_files_main = QShortcut(QKeySequence.Paste, self)
        self.shortcut_paste_files_main.setContext(Qt.WindowShortcut)
        self.shortcut_paste_files_main.activated.connect(self.paste_files_from_clipboard)

        self.act_clear = QAction(QIcon.fromTheme("edit-clear"), self._tr("act_clear_queue"), self)
        self.act_clear.triggered.connect(self.clear_queue)

        self.act_play = QAction(QIcon.fromTheme("media-playback-start"), self._tr("act_start_ocr"), self)
        self.act_play.triggered.connect(self.start_ocr)

        self.act_stop = QAction(QIcon.fromTheme("media-playback-stop"), self._tr("act_stop_ocr"), self)
        self.act_stop.setEnabled(False)
        self.act_stop.triggered.connect(self.stop_ocr)

        self.act_re_ocr = QAction(QIcon.fromTheme("view-refresh"), self._tr("act_re_ocr"), self)
        self.act_re_ocr.setToolTip(self._tr("act_re_ocr_tip"))
        self.act_re_ocr.triggered.connect(self.reprocess_selected)

        self.act_ai_revise = QAction(self._tr("act_ai_revise"), self)
        self.act_ai_revise.setToolTip(self._tr("act_ai_revise_tip"))
        self.act_ai_revise.triggered.connect(self.run_ai_revision)

        self._ai_server_cache = {
            "ts": 0.0,
            "base_url": None,
            "model_id": None,
        }
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

        self.btn_rec_model = QPushButton("Rec-Modell: -")
        self.btn_rec_model.setIcon(QIcon.fromTheme("document-open"))
        self.btn_rec_model.clicked.connect(self.choose_rec_model)

        self.btn_seg_model = QPushButton(self._tr("dlg_choose_seg") + " -")
        self.btn_seg_model.setIcon(QIcon.fromTheme("document-open"))
        self.btn_seg_model.clicked.connect(self.choose_seg_model)

        self._pending_box_for_row: Optional[int] = None
        self._pending_new_line_box: bool = False

        self._auto_select_best_device()
        self._scan_kraken_models()
        self._load_default_segmentation_model()
        self._init_ui()
        self._init_menu()
        self.apply_theme("bright")
        self.retranslate_ui()

        QTimer.singleShot(0, self._fit_queue_columns_exact)
        QTimer.singleShot(0, self._update_queue_hint)
        QTimer.singleShot(0, self._refresh_hw_menu_availability)

        self.canvas.set_overlay_enabled(False)
        self._log(self._tr_log("log_started"))

    def _cleanup_temp_dirs(self):
        for d in list(self.temp_dirs_created):
            try:
                if os.path.isdir(d):
                    shutil.rmtree(d, ignore_errors=True)
            except Exception:
                pass
        self.temp_dirs_created.clear()

    def eventFilter(self, obj, event):
        try:
            et = event.type()

            if et in (QEvent.ShortcutOverride, QEvent.KeyPress):
                if event.matches(QKeySequence.Paste):
                    # Nur reagieren, wenn dieses Fenster wirklich aktiv ist
                    if QApplication.activeWindow() is not self:
                        return super().eventFilter(obj, event)

                    fw = QApplication.focusWidget()

                    # In Texteingaben normales Einfügen erlauben
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
        explicit = (self.ai_model_id or "").strip()
        if explicit:
            return explicit

        models = self._fetch_loaded_llm_models()
        if models:
            return f"AUTO → {models[0]}"

        return "AUTO → -"

    def _update_ai_model_ui(self):
        display = self._get_active_ai_model_display()

        if hasattr(self, "btn_ai_model"):
            self.btn_ai_model.setText(f"KI: {display}")

        if hasattr(self, "act_llm_status"):
            self.act_llm_status.setText(f"LLM: {display}")

    def _process_ui(self):
        QCoreApplication.processEvents()

    def _fetch_loaded_llm_models(self) -> List[str]:
        base_url, _ = self._detect_local_openai_server()
        if not base_url:
            return []

        url = base_url + "/models"
        try:
            req = urllib.request.Request(
                url,
                headers={"Authorization": "Bearer local"},
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                data = json.loads(raw)

            models_data = data.get("data", [])
            out = []
            if isinstance(models_data, list):
                for m in models_data:
                    if not isinstance(m, dict):
                        continue
                    mid = str(m.get("id", "")).strip()
                    if mid:
                        out.append(mid)

            # doppelte raus, Reihenfolge behalten
            seen = set()
            uniq = []
            for mid in out:
                if mid not in seen:
                    seen.add(mid)
                    uniq.append(mid)
            return uniq

        except Exception:
            return []

    def _set_ai_model_from_menu(self, model_id: str):
        self.ai_model_id = (model_id or "").strip()
        self._update_ai_model_ui()

        if self.ai_model_id:
            self.status_bar.showMessage(self._tr("msg_ai_model_set", self.ai_model_id))
        else:
            self.status_bar.showMessage("KI-Modell-ID geleert, localhost-Autoerkennung aktiv.")

    def _refresh_ai_models_menu(self):
        if not hasattr(self, "ai_models_menu"):
            return

        self.ai_models_menu.clear()
        self.ai_available_models = self._fetch_loaded_llm_models()

        self.ai_model_group = QActionGroup(self)
        self.ai_model_group.setExclusive(True)
        self.ai_model_actions = {}

        if not self.ai_available_models:
            act = QAction("Keine localhost-Modelle gefunden", self)
            act.setEnabled(False)
            self.ai_models_menu.addAction(act)
            return

        for mid in self.ai_available_models:
            act = QAction(mid, self)
            act.setCheckable(True)
            act.setChecked(mid == self.ai_model_id)
            act.triggered.connect(lambda checked, m=mid: self._set_ai_model_from_menu(m))
            self.ai_model_group.addAction(act)
            self.ai_models_menu.addAction(act)
            self.ai_model_actions[mid] = act

        self.ai_models_menu.addSeparator()

        act_auto = QAction("AUTO (erstes verfügbares Modell)", self)
        act_auto.setCheckable(True)
        act_auto.setChecked(not bool(self.ai_model_id))
        act_auto.triggered.connect(lambda checked: self._set_ai_model_from_menu(""))
        self.ai_model_group.addAction(act_auto)
        self.ai_models_menu.addAction(act_auto)

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
        payload = {
            "path": task.path,
            "display_name": task.display_name,
            "status": int(task.status),
            "edited": bool(task.edited),
            "source_kind": task.source_kind,
            "relative_path": os.path.basename(task.path),
            "undo_stack": [],
            "redo_stack": [],
            "results": None,
        }

        if task.results:
            text, kr_records, im, recs = task.results
            payload["results"] = {"text": text, "records": [self._recordview_to_dict(rv) for rv in recs], }

        return payload

    def _task_from_dict(self, data: dict) -> TaskItem:
        task = TaskItem(
            path=str(data.get("path", "")),
            display_name=str(data.get("display_name", os.path.basename(str(data.get("path", ""))))),
            status=int(data.get("status", STATUS_WAITING)),
            edited=bool(data.get("edited", False)),
            source_kind=str(data.get("source_kind", "image")),
            relative_path=str(data.get("relative_path", os.path.basename(str(data.get("path", ""))))),
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
            "version": 1,
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

            if rel:
                candidates.append(os.path.join(new_base_dir, rel))

            if old_path:
                candidates.append(os.path.join(new_base_dir, os.path.basename(old_path)))

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
        progress.setWindowTitle("Projekt laden")
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

                check_item = QTableWidgetItem()
                check_item.setTextAlignment(Qt.AlignCenter)
                check_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)
                check_item.setCheckState(Qt.Unchecked)

                name_item = QTableWidgetItem(task.display_name)
                name_item.setData(Qt.UserRole, task.path)
                name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)

                status_item = QTableWidgetItem()
                status_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

                self.queue_table.setItem(row, QUEUE_COL_NUM, num_item)
                self.queue_table.setItem(row, QUEUE_COL_CHECK, check_item)
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

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.project_file_path = path
            self._load_project_dict(data)
            self.status_bar.showMessage(self._tr("msg_project_loaded", os.path.basename(path)))
        except Exception as e:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_project_load_failed", str(e)))

    def _queue_check_col_width(self) -> int:
        style = self.queue_table.style()
        indicator_w = style.pixelMetric(style.PixelMetric.PM_IndicatorWidth)
        return max(18, indicator_w + 6)  # 3 px links + 3 px rechts

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

    def _checked_queue_tasks(self) -> List[TaskItem]:
        out = []
        for row in range(self.queue_table.rowCount()):
            check_item = self.queue_table.item(row, QUEUE_COL_CHECK)
            file_item = self.queue_table.item(row, QUEUE_COL_FILE)
            if not check_item or not file_item:
                continue
            if check_item.checkState() == Qt.Checked:
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
        for btn_name in ("btn_rec_model", "btn_seg_model", "btn_ai_model"):
            btn = getattr(self, btn_name, None)
            if btn is not None:
                btn.setMinimumHeight(target_height)
                btn.setMaximumHeight(target_height)
                btn.setMinimumWidth(0)
                btn.setMaximumWidth(16777215)

        # kleine X-Buttons
        for btn_name in ("btn_rec_clear", "btn_seg_clear"):
            btn = getattr(self, btn_name, None)
            if btn is not None:
                btn.setMinimumHeight(target_height)
                btn.setMaximumHeight(target_height)
                btn.setFixedWidth(clear_width)

    def _scan_kraken_models(self):
        self.rec_model_candidates = []
        self.default_seg_model = ""

        model_dir = KRAKEN_MODELS_DIR
        if not os.path.isdir(model_dir):
            return

        for name in sorted(os.listdir(model_dir)):
            full = os.path.join(model_dir, name)
            if not os.path.isfile(full):
                continue
            ext = os.path.splitext(name)[1].lower()
            if ext not in (".mlmodel", ".pt"):
                continue

            lname = name.lower()

            # Standard-Segmentierung: blla
            if "blla" in lname:
                if not self.default_seg_model:
                    self.default_seg_model = full
                continue

            # Alles andere als Recognition behandeln
            self.rec_model_candidates.append(full)

    def _load_default_segmentation_model(self):
        if self.default_seg_model and os.path.exists(self.default_seg_model):
            self.seg_model_path = self.default_seg_model
            self.current_segmenter_mode = "blla"

    def choose_rec_model_from_scanned(self):
        if not getattr(self, "rec_model_candidates", None):
            QMessageBox.warning(self, self._tr("warn_title"), "Keine Recognition-Modelle gefunden.")
            return

        names = [os.path.basename(p) for p in self.rec_model_candidates]
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

        for p in self.rec_model_candidates:
            if os.path.basename(p) == selected:
                self.model_path = p
                break

        self.btn_rec_model.setText(f"Rec-Modell: {os.path.basename(self.model_path)}")
        self._update_models_menu_labels()
        self._update_model_clear_buttons()

    def _detect_local_openai_server(self, force: bool = False) -> Tuple[Optional[str], Optional[str]]:
        now = time.monotonic()

        if not force:
            age = now - float(self._ai_server_cache.get("ts", 0.0))
            if age < self._ai_server_cache_ttl:
                return self._ai_server_cache.get("base_url"), self._ai_server_cache.get("model_id")

        candidates = [
            ("127.0.0.1", 1234),  # LM Studio
            ("localhost", 1234),
            ("127.0.0.1", 8000),  # vLLM
            ("localhost", 8000),
            ("127.0.0.1", 8080),
            ("localhost", 8080),
            ("127.0.0.1", 3000),
            ("localhost", 3000),
        ]

        # 1) Erst ultraschnell prüfen, ob überhaupt ein Port offen ist
        open_candidates = []
        for host, port in candidates:
            if self._is_local_port_open(host, port, timeout=0.12):
                open_candidates.append((host, port))

        if not open_candidates:
            self._ai_server_cache = {
                "ts": now,
                "base_url": None,
                "model_id": None,
            }
            return None, None

        # 2) Nur für offene Ports /v1/models abfragen
        for host, port in open_candidates:
            url = f"http://{host}:{port}/v1/models"
            try:
                req = urllib.request.Request(
                    url,
                    headers={"Authorization": "Bearer local"},
                    method="GET"
                )
                with urllib.request.urlopen(req, timeout=0.35) as resp:
                    raw = resp.read().decode("utf-8", errors="replace")
                    data = json.loads(raw)

                models_data = data.get("data", [])
                if isinstance(models_data, list) and models_data:
                    first = models_data[0]
                    model_id = str(first.get("id", "")).strip() or "-"
                    base_url = url.rsplit("/models", 1)[0]

                    self._ai_server_cache = {
                        "ts": now,
                        "base_url": base_url,
                        "model_id": model_id,
                    }
                    return base_url, model_id

            except Exception:
                continue

        self._ai_server_cache = {
            "ts": now,
            "base_url": None,
            "model_id": None,
        }
        return None, None

    def _check_lm_studio_server(self) -> bool:
        base_url, model_id = self._detect_local_openai_server()
        return bool(base_url and model_id)

    def _fetch_loaded_llm_name(self) -> str:
        base_url, model_id = self._detect_local_openai_server()
        return model_id or "-"

    def _refresh_ai_endpoint_from_localhost(self):
        base_url, _ = self._detect_local_openai_server()
        if base_url:
            self.ai_base_url = base_url
            self.ai_endpoint = base_url + "/chat/completions"
        self._update_ai_model_ui()

    def _resolve_ai_model_id(self) -> str:
        self._refresh_ai_endpoint_from_localhost()

        # 1) explizit ausgewähltes Modell hat Vorrang
        model_id = (self.ai_model_id or "").strip()
        if model_id:
            return model_id

        # 2) sonst erstes geladenes localhost-Modell
        models = self._fetch_loaded_llm_models()
        if models:
            return models[0]

        return ""

    def refresh_models_menu_status(self):
        base_url, _ = self._detect_local_openai_server()
        server_on = bool(base_url)

        if server_on:
            self.ai_base_url = base_url
            self.ai_endpoint = base_url + "/chat/completions"

        self._update_ai_model_ui()

        self.act_server_status.setText(
            f"Localhost-Server: {'ON' if server_on else 'OFF'}"
            + (f" ({base_url})" if server_on else "")
        )

    # -----------------------------
    # Übersetzung
    # -----------------------------
    def _tr(self, key: str, *args):
        txt = TRANSLATIONS.get(self.current_lang, TRANSLATIONS["de"]).get(key, key)
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

        model_id = self._resolve_ai_model_id()
        if not model_id:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_ai_model"))
            return

        if hasattr(self, "ai_batch_worker") and self.ai_batch_worker and self.ai_batch_worker.isRunning():
            return

        self.act_ai_revise.setEnabled(False)
        self.act_ai_revise_all.setEnabled(False)

        self.ai_batch_dialog = ProgressStatusDialog("KI-Batch-Überarbeitung", self)
        self.ai_batch_dialog.set_status("Initialisiere KI-Batch…")
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

    def run_ai_revision_for_all(self):
        items = [it for it in self.queue_items if it.status == STATUS_DONE and it.results]
        if not items:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
            return

        model_id = self._resolve_ai_model_id()
        if not model_id:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_ai_model"))
            return

        if hasattr(self, "ai_batch_worker") and self.ai_batch_worker and self.ai_batch_worker.isRunning():
            return

        self.act_ai_revise.setEnabled(False)
        self.act_ai_revise_all.setEnabled(False)

        self.ai_batch_dialog = ProgressStatusDialog("KI-Batch-Überarbeitung", self)
        self.ai_batch_dialog.set_status("Initialisiere KI-Batch…")
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

    def on_ai_batch_file_started(self, path: str, current: int, total: int):
        task = next((i for i in self.queue_items if i.path == path), None)
        if task:
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
            self.status_bar.showMessage("KI-Modell-ID geleert, localhost-Autoerkennung aktiv.")

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

        self.act_ai_revise.setEnabled(False)
        self.act_ai_revise_all.setEnabled(False)
        self.status_bar.showMessage(self._tr("msg_ai_started"))
        self._log(self._tr_log("log_ai_started", os.path.basename(task.path)))

        self.ai_progress_dialog = ProgressStatusDialog("KI-Überarbeitung", self)
        self.ai_progress_dialog.set_status("Verbinde mit LM Studio…")
        self.ai_progress_dialog.cancel_requested.connect(self._cancel_ai_revision)
        self.ai_progress_dialog.show()

        self.ai_worker = AIRevisionWorker(
            path=task.path,
            recs=recs,
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
            parent=self
        )

        self.ai_worker.progress_changed.connect(self.ai_progress_dialog.set_progress)
        self.ai_worker.status_changed.connect(self.ai_progress_dialog.set_status)
        self.ai_worker.status_changed.connect(self._log)
        self.ai_worker.finished_revision.connect(self.on_ai_revision_done)
        self.ai_worker.failed_revision.connect(self.on_ai_revision_failed)
        self.ai_worker.start()

    def _run_ai_revision_batch(self, items: List[TaskItem]):
        model_id = self._resolve_ai_model_id()
        if not model_id:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_ai_model"))
            return

        if hasattr(self, "ai_batch_worker") and self.ai_batch_worker and self.ai_batch_worker.isRunning():
            return

        self.act_ai_revise.setEnabled(False)
        self.act_ai_revise_all.setEnabled(False)

        self.ai_batch_dialog = ProgressStatusDialog("KI-Batch-Überarbeitung", self)
        self.ai_batch_dialog.set_status("Initialisiere KI-Batch…")
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
            self.act_ai_revise_all.setEnabled(True)
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

        self._log(f"ALT erste Zeile: {recs[0].text if recs else '<leer>'}")
        self._log(f"NEU erste Zeile: {revised_lines[0] if revised_lines else '<leer>'}")
        self._log(f"NEU alle Zeilen: {revised_lines}")

        self._push_undo(task)

        # WICHTIG: neue RecordView-Liste bauen, nicht in-place mutieren
        new_recs = [
            RecordView(i, revised_lines[i], recs[i].bbox)
            for i in range(len(recs))
        ]

        new_text = "\n".join(rv.text for rv in new_recs).strip()
        task.results = (new_text, kr_records, im, new_recs)
        task.edited = True

        cur = self._current_task()
        if cur and cur.path == path:
            self._sync_ui_after_recs_change(task, keep_row=self.list_lines.currentRow())
        else:
            self._update_queue_row(path)

        self.act_ai_revise.setEnabled(True)
        self.act_ai_revise_all.setEnabled(True)
        self.status_bar.showMessage(self._tr("msg_ai_done"))
        self._log(self._tr_log("log_ai_done", os.path.basename(path)))

        if hasattr(self, "ai_progress_dialog") and self.ai_progress_dialog:
            self.ai_progress_dialog.close()
            self.ai_progress_dialog = None

    def on_ai_revision_failed(self, path: str, msg: str):
        self.act_ai_revise.setEnabled(True)
        self.act_ai_revise_all.setEnabled(True)

        if "abgebrochen" in str(msg).lower():
            self.status_bar.showMessage("Überarbeitung abgebrochen.")
            self._log(f"Überarbeitung abgebrochen: {os.path.basename(path)}")
        else:
            self.status_bar.showMessage("Überarbeitung fehlgeschlagen.")
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
        self.toolbar.addAction(self.act_clear)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.act_play)
        self.toolbar.addAction(self.act_stop)
        self.toolbar.addAction(self.act_re_ocr)
        self.toolbar.addAction(self.act_ai_revise)
        self.toolbar.addAction(self.act_toggle_log)

        # Nur Recognition-Modell in der Toolbar
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

        self._make_toolbar_buttons_pushy()
        self._update_model_clear_buttons()

        right = QVBoxLayout()
        right.addWidget(self.lbl_queue)
        right.addWidget(self.queue_table, 2)

        # NEU: Logbereich unter der Queue
        right.addWidget(self.log_edit, 1)

        right.addWidget(self.progress_bar)

        lines_head = QHBoxLayout()
        lines_head.addWidget(self.lbl_lines)

        self.btn_import_lines = QToolButton()
        self.btn_import_lines.setText("Import")
        self.btn_import_lines.setToolTip("Erkannte Zeilen aus TXT/JSON laden")
        self.btn_import_lines.setPopupMode(QToolButton.InstantPopup)

        import_menu = QMenu(self)

        self.act_import_lines_current = QAction("Für aktuelles Bild", self)
        self.act_import_lines_selected = QAction("Für ausgewählte Bilder", self)
        self.act_import_lines_all = QAction("Für alle Bilder", self)

        self.act_import_lines_current.triggered.connect(self.import_lines_for_current_image)
        self.act_import_lines_selected.triggered.connect(self.import_lines_for_selected_images)
        self.act_import_lines_all.triggered.connect(self.import_lines_for_all_images)

        import_menu.addAction(self.act_import_lines_current)
        import_menu.addAction(self.act_import_lines_selected)
        import_menu.addAction(self.act_import_lines_all)

        self.btn_import_lines.setMenu(import_menu)

        lines_head.addWidget(self.btn_import_lines)
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
        QTimer.singleShot(0, self._normalize_toolbar_button_sizes)

    def on_ai_batch_file_done(self, path: str, revised_lines: list, current: int, total: int):
        task = next((i for i in self.queue_items if i.path == path), None)
        if not task or not task.results:
            return

        task.status = STATUS_DONE
        self._update_queue_row(path)

        text, kr_records, im, recs = task.results

        revised_lines = [str(x).strip() for x in revised_lines]
        self._log(
            f"KI Batch Rückgabe für {os.path.basename(path)}: {len(revised_lines)} Zeilen, OCR hatte {len(recs)} Zeilen")

        if len(revised_lines) < len(recs):
            revised_lines.extend([recs[i].text for i in range(len(revised_lines), len(recs))])
        elif len(revised_lines) > len(recs):
            revised_lines = revised_lines[:len(recs)]

            self._log(f"ALT erste Zeile: {recs[0].text if recs else '<leer>'}")
            self._log(f"NEU erste Zeile: {revised_lines[0] if revised_lines else '<leer>'}")
            self._log(f"NEU alle Zeilen: {revised_lines}")

        self._push_undo(task)

        # WICHTIG: neue Liste statt Mutation der alten
        new_recs = [
            RecordView(i, revised_lines[i], recs[i].bbox)
            for i in range(len(recs))
        ]

        new_text = "\n".join(rv.text for rv in new_recs).strip()
        task.results = (new_text, kr_records, im, new_recs)
        task.edited = True

        keep_row = self.list_lines.currentRow() if self._current_task() and self._current_task().path == path else 0
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
        self.act_ai_revise_all.setEnabled(True)

        if self.ai_batch_dialog:
            self.ai_batch_dialog.close()
            self.ai_batch_dialog = None

        self.status_bar.showMessage("KI-Batch abgeschlossen.")

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
        lang_group = QActionGroup(self)
        lang_group.setExclusive(True)

        hw_group = QActionGroup(self)
        hw_group.setExclusive(True)

        read_group = QActionGroup(self)
        read_group.setExclusive(True)

        menubar = self.menuBar()

        self.file_menu = menubar.addMenu(self._tr("menu_file"))
        self.edit_menu = menubar.addMenu(self._tr("menu_edit"))

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

        self.revision_models_menu = menubar.addMenu("Modelle - Überarbeitung")

        # Menüeinträge zeigen immer den aktuell geladenen Namen
        self.act_rec = QAction("Recognition-Modell laden...", self)
        self.act_rec.triggered.connect(self.choose_rec_model)
        self.models_menu.addAction(self.act_rec)

        self.act_seg = QAction("Segmentierungs-Modell laden...", self)
        self.act_seg.triggered.connect(self.choose_seg_model)
        self.models_menu.addAction(self.act_seg)

        self.models_menu.addSeparator()

        # --- Clear actions in Models menu ---
        self.act_clear_rec = QAction(self._tr("act_clear_rec"), self)
        self.act_clear_rec.setToolTip(self._tr("act_clear_rec"))
        self.act_clear_rec.triggered.connect(self.clear_rec_model)
        self.models_menu.addAction(self.act_clear_rec)

        self.act_clear_seg = QAction(self._tr("act_clear_seg"), self)
        self.act_clear_seg.setToolTip(self._tr("act_clear_seg"))
        self.act_clear_seg.triggered.connect(self.clear_seg_model)
        self.models_menu.addAction(self.act_clear_seg)

        self.models_menu.addSeparator()
        self.act_download = QAction(self._tr("act_download_model"), self)
        self.act_download.triggered.connect(self.open_download_link)
        self.models_menu.addAction(self.act_download)

        self.ai_models_menu = self.revision_models_menu.addMenu("KI-Modell für Überarbeitung")
        self.revision_models_menu.aboutToShow.connect(self._refresh_ai_models_menu)

        self.revision_models_menu.addSeparator()

        self.act_server_status = QAction("Localhost-Server: OFF", self)
        self.act_server_status.setEnabled(False)
        self.revision_models_menu.addAction(self.act_server_status)

        self.revision_models_menu.aboutToShow.connect(self.refresh_models_menu_status)

        self.options_menu = menubar.addMenu(self._tr("menu_options"))

        # Sprachen
        self.lang_menu = self.options_menu.addMenu(self._tr("menu_languages"))
        lang_group = QActionGroup(self)
        for key, code in [("lang_de", "de"), ("lang_en", "en"), ("lang_fr", "fr")]:
            act = QAction(self._tr(key), self)
            act.setCheckable(True)
            if code == self.current_lang:
                act.setChecked(True)
            act.triggered.connect(lambda checked, c=code: self.set_language(c))
            lang_group.addAction(act)
            self.lang_menu.addAction(act)

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

        # Theme / Erscheinungsbild
        self.options_menu.addSeparator()
        self.theme_menu = self.options_menu.addMenu(self._tr("menu_appearance"))
        self.act_theme_bright = QAction(self._tr("theme_bright"), self)
        self.act_theme_bright.triggered.connect(lambda: self.apply_theme("bright"))
        self.theme_menu.addAction(self.act_theme_bright)
        self.act_theme_dark = QAction(self._tr("theme_dark"), self)
        self.act_theme_dark.triggered.connect(lambda: self.apply_theme("dark"))
        self.theme_menu.addAction(self.act_theme_dark)

        if self.device_str in self.hw_actions:
            self.hw_actions[self.device_str].setChecked(True)

    # -----------------------------
    # Queue columns
    # -----------------------------

    def _on_queue_header_clicked(self, logical_index: int):
        if logical_index != QUEUE_COL_CHECK:
            return

        states = []
        for row in range(self.queue_table.rowCount()):
            item = self.queue_table.item(row, QUEUE_COL_CHECK)
            if item:
                states.append(item.checkState() == Qt.Checked)

        if not states:
            return

        set_checked = not all(states)

        for row in range(self.queue_table.rowCount()):
            item = self.queue_table.item(row, QUEUE_COL_CHECK)
            if item:
                item.setCheckState(Qt.Checked if set_checked else Qt.Unchecked)

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
            status_w = 120

            file_w = max(120, vw - num_w - check_w - status_w)

            self.queue_table.setColumnWidth(QUEUE_COL_NUM, num_w)
            self.queue_table.setColumnWidth(QUEUE_COL_CHECK, check_w)
            self.queue_table.setColumnWidth(QUEUE_COL_FILE, file_w)
            self.queue_table.setColumnWidth(QUEUE_COL_STATUS, status_w)

            self._update_queue_hint()
        finally:
            self._resizing_cols = False

    def _on_queue_header_resized(self, logicalIndex: int, oldSize: int, newSize: int):
        if self._resizing_cols:
            return
        self._fit_queue_columns_exact()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_queue_columns_exact()

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
    # -----------------------------
    def apply_theme(self, theme: str):
        self.current_theme = theme
        pal = QPalette()
        conf = THEMES[theme]

        pal.setColor(QPalette.Window, QColor(conf["bg"]))
        pal.setColor(QPalette.WindowText, QColor(conf["fg"]))
        pal.setColor(QPalette.Base, conf["table_base"])
        pal.setColor(QPalette.AlternateBase, conf["table_base"].lighter(110))
        pal.setColor(QPalette.ToolTipBase, Qt.white)
        pal.setColor(QPalette.ToolTipText, Qt.white)
        pal.setColor(QPalette.Text, QColor(conf["fg"]))
        pal.setColor(QPalette.Button, conf["table_base"].lighter(110))
        pal.setColor(QPalette.ButtonText, QColor(conf["fg"]))
        pal.setColor(QPalette.BrightText, Qt.red)
        pal.setColor(QPalette.Link, QColor(42, 130, 218))
        pal.setColor(QPalette.Highlight, QColor(42, 130, 218))
        pal.setColor(QPalette.HighlightedText, Qt.black)
        QApplication.instance().setPalette(pal)

        self.canvas.set_theme(theme)

        txt = conf["toolbar_text"]
        border = conf["toolbar_border"]
        if theme == "dark":
            self.toolbar.setStyleSheet(
                f"""
                QToolBar {{
                    background: {conf["bg"]};
                    spacing: 6px;
                }}

                QToolButton {{
                    color: #000;
                    border: 1px solid rgba(255,255,255,0.85);
                    border-radius: 6px;
                    padding: 4px 8px;
                    background: rgba(255,255,255,0.92);
                }}
                QToolButton:hover {{
                    background: rgba(255,255,255,0.98);
                    border-color: rgba(255,255,255,0.98);
                }}
                QToolButton:pressed {{
                    background: rgba(235,235,235,1.0);
                }}

                QToolButton:checked {{
                    background: rgba(200,230,255,1.0);
                    border-color: rgba(120,190,255,1.0);
                }}

                QPushButton {{
                    color: #000;
                    border: 1px solid rgba(255,255,255,0.85);
                    border-radius: 6px;
                    padding: 4px 8px;
                    background: rgba(255,255,255,0.92);
                }}
                QPushButton:hover {{
                    background: rgba(255,255,255,0.98);
                    border-color: rgba(255,255,255,0.98);
                }}
                QPushButton:pressed {{
                    background: rgba(235,235,235,1.0);
                }}
                """
            )
        else:
            self.toolbar.setStyleSheet(
                """
                QToolBar {
                    spacing: 6px;
                }

                QToolButton, QPushButton {
                    border: 1px solid rgba(0,0,0,0.25);
                    border-radius: 6px;
                    padding: 4px 8px;
                    background: rgba(255,255,255,0.90);
                }

                QToolButton:hover, QPushButton:hover {
                    background: rgba(255,255,255,1.0);
                    border-color: rgba(0,0,0,0.35);
                }

                /* Push/Release Feedback */
                QToolButton:pressed, QPushButton:pressed {
                    background: rgba(230,230,230,1.0);
                    border-color: rgba(0,0,0,0.45);
                    padding-left: 9px;   /* “depressed” effect */
                    padding-top: 5px;
                }

                QToolButton:checked {
                    background: rgba(42,130,218,0.20);
                    border-color: rgba(42,130,218,0.45);
                }
                """
            )

    # -----------------------------
    # Language / reading
    # -----------------------------
    def set_language(self, lang):
        self.current_lang = lang
        self.retranslate_ui()
        self._refresh_hw_menu_availability()

    def _update_models_menu_labels(self):
        rec_name = os.path.basename(self.model_path) if self.model_path else "-"
        seg_name = os.path.basename(self.seg_model_path) if self.seg_model_path else "-"

        # Reiter "Modelle" (Menü) aktualisieren
        self.act_rec.setText(f"{self._tr('dlg_choose_rec')}{rec_name}")
        self.act_seg.setText(f"{self._tr('dlg_choose_seg')}{seg_name}")

    def set_reading_direction(self, mode):
        self.reading_direction = mode

    def retranslate_ui(self):
        self.setWindowTitle(self._tr("app_title"))
        self.file_menu.setTitle(self._tr("menu_file"))
        self.edit_menu.setTitle(self._tr("menu_edit"))
        self.models_menu.setTitle(self._tr("menu_models"))
        self.options_menu.setTitle(self._tr("menu_options"))
        self.lang_menu.setTitle(self._tr("menu_languages"))
        self.hw_menu.setTitle(self._tr("menu_hw"))
        self.theme_menu.setTitle(self._tr("menu_appearance"))
        self.export_menu.setTitle(self._tr("menu_export"))
        self.reading_menu.setTitle(self._tr("menu_reading"))

        self.act_export_log.setText(self._tr("menu_export_log"))

        if hasattr(self, "act_ai_revise"):
            self.act_ai_revise.setText(self._tr("act_ai_revise"))
            self.act_ai_revise.setToolTip(self._tr("act_ai_revise_tip"))
        if hasattr(self, "btn_ai_model"):
            self._update_ai_model_ui()
        if hasattr(self, "act_ai_revise_all"):
            self.act_ai_revise_all.setText("Alle Überarbeiten")
            self.act_ai_revise_all.setToolTip("Alle fertig erkannten Dateien überarbeiten")
        if hasattr(self, "btn_import_lines"):
            self.btn_import_lines.setToolTip("Erkannte Zeilen aus TXT/JSON laden")
        if hasattr(self, "act_import_lines_current"):
            self.act_import_lines_current.setText("Für aktuelles Bild")
        if hasattr(self, "act_import_lines_selected"):
            self.act_import_lines_selected.setText("Für ausgewählte Bilder")
        if hasattr(self, "act_import_lines_all"):
            self.act_import_lines_all.setText("Für alle Bilder")
        if hasattr(self, "act_project_save"):
            self.act_project_save.setText(self._tr("menu_project_save"))
        if hasattr(self, "act_project_save_as"):
            self.act_project_save_as.setText(self._tr("menu_project_save_as"))
        if hasattr(self, "act_project_load"):
            self.act_project_load.setText(self._tr("menu_project_load"))
        if hasattr(self, "act_paste_files_menu"):
            self.act_paste_files_menu.setText(self._tr("act_paste_clipboard"))

        self.act_undo.setText(self._tr("act_undo"))
        self.act_redo.setText(self._tr("act_redo"))

        self.act_add_files.setText(self._tr("act_add_files"))
        self.act_exit.setText(self._tr("menu_exit"))
        self.act_download.setText(self._tr("act_download_model"))
        self.act_overlay.setText(self._tr("act_overlay_show"))
        self.act_theme_bright.setText(self._tr("theme_bright"))
        self.act_theme_dark.setText(self._tr("theme_dark"))

        self.act_add.setText(self._tr("act_add_files"))
        self.act_clear.setText(self._tr("act_clear_queue"))
        self.act_play.setText(self._tr("act_start_ocr"))
        self.act_stop.setText(self._tr("act_stop_ocr"))
        self.act_re_ocr.setText(self._tr("act_re_ocr"))
        self.act_re_ocr.setToolTip(self._tr("act_re_ocr_tip"))

        self.lbl_queue.setText(self._tr("lbl_queue"))
        self.lbl_lines.setText(self._tr("lbl_lines"))
        self.queue_table.setHorizontalHeaderLabels(["#", "☐", self._tr("col_file"), self._tr("col_status")])

        if self.model_path:
            self.btn_rec_model.setText(f"Rec-Modell: {os.path.basename(self.model_path)}")
        else:
            self.btn_rec_model.setText("Rec-Modell: -")

        if self.seg_model_path:
            self.btn_seg_model.setText(f"Seg-Modell: {os.path.basename(self.seg_model_path)}")
        else:
            self.btn_seg_model.setText("Seg-Modell: -")

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
        QTimer.singleShot(0, self._normalize_toolbar_button_sizes)

        # Models menu actions
        self.act_rec.setText(
            f"{self._tr('dlg_choose_rec')}{os.path.basename(self.model_path) if self.model_path else '-'}")
        self.act_seg.setText(
            f"{self._tr('dlg_choose_seg')}{os.path.basename(self.seg_model_path) if self.seg_model_path else '-'}")

        if hasattr(self, "act_clear_rec"):
            self.act_clear_rec.setText(self._tr("act_clear_rec"))
            self.act_clear_rec.setToolTip(self._tr("act_clear_rec"))
        if hasattr(self, "act_clear_seg"):
            self.act_clear_seg.setText(self._tr("act_clear_seg"))
            self.act_clear_seg.setToolTip(self._tr("act_clear_seg"))

        if hasattr(self, "btn_rec_clear"):
            self.btn_rec_clear.setToolTip(self._tr("act_clear_rec"))
        if hasattr(self, "btn_seg_clear"):
            self.btn_seg_clear.setToolTip(self._tr("act_clear_seg"))

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

    def _refresh_hw_menu_availability(self):
        caps = self._gpu_capabilities()
        for dev, act in self.hw_actions.items():
            ok, detail = caps.get(dev, (False, ""))
            if dev == "cpu":
                act.setEnabled(True)
                act.setToolTip("CPU")
                continue
            act.setEnabled(ok)
            act.setToolTip(detail if detail else ("Not available" if self.current_lang == "en" else "Nicht verfügbar"))

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
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if not event.mimeData().hasUrls():
            event.ignore()
            return
        files = []
        for u in event.mimeData().urls():
            p = u.toLocalFile()
            if p and os.path.exists(p) and is_supported_input(p):
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
                    if p and os.path.exists(p) and is_supported_input(p):
                        files.append(p)

            # Fallback: Textliste mit Dateipfaden
            if not files and md.hasText():
                raw = md.text().strip()
                if raw:
                    parts = [x.strip().strip('"') for x in raw.splitlines() if x.strip()]
                    for p in parts:
                        if os.path.exists(p) and is_supported_input(p):
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
                            if os.path.exists(candidate) and is_supported_input(candidate):
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
                "In der Zwischenablage wurden keine unterstützten Dateien gefunden."
            )

    def choose_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, self._tr("dlg_load_img"), "", self._tr("dlg_filter_img"))
        if files:
            self.add_files_to_queue(files)

    def _start_pdf_render_async(self, pdf_path: str, dpi: int = 300):
        # falls schon ein PDF gerendert wird: optional blockieren oder queue’n
        if self.pdf_worker and self.pdf_worker.isRunning():
            QMessageBox.information(self, self._tr("info_title"),
                                    "Es wird gerade bereits ein PDF gerendert. Bitte warte kurz.")
            return

        self._pending_pdf_path = pdf_path

        # Dialog
        dlg = QProgressDialog(self)
        dlg.setWindowTitle(self._tr("pdf_render_title"))
        dlg.setCancelButtonText(
            "Abbrechen" if self.current_lang == "de" else ("Cancel" if self.current_lang == "en" else "Annuler")
        )
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

    def _on_pdf_render_finished(self, pdf_path: str, out_paths: list):
        # Dialog schließen
        if self.pdf_progress_dlg:
            self.pdf_progress_dlg.setValue(self.pdf_progress_dlg.maximum())
            self.pdf_progress_dlg.close()
            self.pdf_progress_dlg = None

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
            disp = f"{base_name} – Seite {i:04d}"
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

        QMessageBox.warning(self, self._tr("warn_title"), f"PDF konnte nicht gerendert werden:\n{msg}")

    def add_files_to_queue(self, paths: List[str]):
        added_any = False
        last_added = None
        added_count = 0

        for p in paths:
            if not p or not os.path.exists(p):
                continue
            if not is_supported_input(p):
                continue

            ext = os.path.splitext(p)[1].lower()

            if ext == ".pdf":
                self._start_pdf_render_async(p, dpi=300)
                added_any = True  # damit dein Log/Hint-Update unten nicht „vergisst“
                continue

            # normale Bilder
            if any(it.path == p for it in self.queue_items):
                continue
            self._add_file_to_queue_single(p)
            added_any = True
            last_added = p
            added_count += 1

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

        check_item = QTableWidgetItem()
        check_item.setTextAlignment(Qt.AlignCenter)
        check_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)
        check_item.setCheckState(Qt.Unchecked)

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
        self.queue_table.setItem(row, QUEUE_COL_CHECK, check_item)
        self.queue_table.setItem(row, QUEUE_COL_FILE, name_item)
        self.queue_table.setItem(row, QUEUE_COL_STATUS, status_item)

        self.queue_table.selectRow(row)
        self._refresh_queue_numbers()

    def on_item_changed(self, item: QTableWidgetItem):
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

        check_all_act = menu.addAction("Alle markieren")
        uncheck_all_act = menu.addAction("Alle Markierungen entfernen")

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
        for row in range(self.queue_table.rowCount()):
            item = self.queue_table.item(row, QUEUE_COL_CHECK)
            if item:
                item.setCheckState(Qt.Checked)

    def uncheck_all_queue_items(self):
        for row in range(self.queue_table.rowCount()):
            item = self.queue_table.item(row, QUEUE_COL_CHECK)
            if item:
                item.setCheckState(Qt.Unchecked)

    def delete_selected_queue_items(self, reset_preview: bool = False):
        checked_rows = []
        for row in range(self.queue_table.rowCount()):
            item = self.queue_table.item(row, QUEUE_COL_CHECK)
            if item and item.checkState() == Qt.Checked:
                checked_rows.append(row)

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

    def _populate_lines_list(self, recs: List[RecordView], keep_row: Optional[int] = None):
        self.list_lines.blockSignals(True)
        self.list_lines.clear()
        for i, rv in enumerate(recs):
            li = QListWidgetItem(f"{i + 1:04d}  {rv.text}")
            li.setData(Qt.UserRole, i)
            li.setFlags(li.flags() | Qt.ItemIsEditable)
            self.list_lines.addItem(li)
        self.list_lines.blockSignals(False)

        if recs:
            if keep_row is None:
                self.list_lines.setCurrentRow(0)
            else:
                self.list_lines.setCurrentRow(max(0, min(self.list_lines.count() - 1, keep_row)))

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
        p, _ = QFileDialog.getOpenFileName(self, self._tr("dlg_choose_rec"), "", self._tr("dlg_filter_model"))
        if p:
            self.model_path = p
            name = os.path.basename(p)
            self.btn_rec_model.setText(f"Rec-Modell: {name}")
            self.status_bar.showMessage(self._tr("msg_loaded_rec", name))
            self._update_models_menu_labels()
            self._update_model_clear_buttons()

    def choose_seg_model(self):
        p, _ = QFileDialog.getOpenFileName(self, self._tr("dlg_choose_seg"), "", self._tr("dlg_filter_model"))
        if p:
            self.seg_model_path = p
            name = os.path.basename(p)
            self.btn_seg_model.setText(f"Seg-Modell: {name}")
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
        self.btn_rec_model.setText("Rec-Modell: -")
        self.status_bar.showMessage(self._tr("msg_loaded_rec", "-"))
        self._update_models_menu_labels()
        self._update_model_clear_buttons()

    def clear_seg_model(self):
        self.seg_model_path = ""
        self.btn_seg_model.setText("Seg-Modell: -")
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

        # Button-Text umschalten
        if self.act_toggle_log.isChecked():
            self.act_toggle_log.setText(self._tr("log_toggle_hide"))
        else:
            self.act_toggle_log.setText(self._tr("log_toggle_show"))

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

        raise ValueError(f"Nicht unterstütztes Importformat: {file_path}")

    def _apply_imported_lines_to_task(self, task: TaskItem, lines: List[str]):
        lines = [str(x).strip() for x in lines if str(x).strip()]
        if not lines:
            raise ValueError("Die Importdatei enthält keine verwertbaren Zeilen.")

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
            QMessageBox.information(self, self._tr("info_title"), "Kein aktuelles Bild geladen.")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Zeilen importieren",
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
            QMessageBox.information(self, self._tr("info_title"), "Keine Bilder ausgewählt oder markiert.")
            return

        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Zeilen-Dateien für ausgewählte Bilder laden",
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
                "Keine Importdatei passt zu den ausgewählten Bildern.\n\nDie Dateinamen müssen über den Basisnamen passen."
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
                self._log(f"Import-Fehler: {task.display_name} -> {e}")

    def import_lines_for_all_images(self):
        if not self.queue_items:
            QMessageBox.information(self, self._tr("info_title"), "Keine Bilder geladen.")
            return

        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Zeilen-Dateien für alle Bilder laden",
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
                "Keine Importdatei passt zu den geladenen Bildern.\n\nDie Dateinamen müssen über den Basisnamen passen."
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
                self._log(f"Import-Fehler: {task.display_name} -> {e}")

    # -----------------------------
    # OCR-Steuerung
    # -----------------------------
    def start_ocr(self):
        if not self.model_path or not os.path.exists(self.model_path):
            QMessageBox.critical(self, self._tr("err_title"), self._tr("warn_need_rec"))
            return
        use_pageseg = False

        if not self.seg_model_path or not os.path.exists(self.seg_model_path):
            QMessageBox.critical(self, self._tr("err_title"), "blla-Segmentierungsmodell wurde nicht gefunden.")
            return

        segmenter_mode = "pageseg" if use_pageseg else "blla"
        self.current_segmenter_mode = segmenter_mode

        checked_tasks = self._checked_queue_tasks()
        selected_tasks = self._selected_queue_tasks()

        # Priorität: Checkmarks vor Auswahl
        target_tasks = checked_tasks if checked_tasks else selected_tasks

        if target_tasks:
            tasks = []
            for it in target_tasks:
                if it.status in (STATUS_WAITING, STATUS_ERROR, STATUS_DONE):
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
            segmentation_model_path=None if use_pageseg else self.seg_model_path,
            device=self.device_str,
            reading_direction=self.reading_direction,
            export_format="pdf",
            export_dir=self.current_export_dir,
            segmenter_mode=segmenter_mode,
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
        self._log(self._tr_log("log_ocr_started", len(paths), self.device_str,
                               self.reading_direction) + f", Seg={segmenter_mode}")
        self.worker.start()

    def on_device_resolved(self, dev_str: str):
        self.status_bar.showMessage(self._tr("msg_using_device", dev_str) + f" | Seg={self.current_segmenter_mode}")

    def on_gpu_info(self, info: str):
        self.status_bar.showMessage(self._tr("msg_detected_gpu", info) + f" | Seg={self.current_segmenter_mode}")

    def reprocess_selected(self):
        if self.queue_table.currentRow() < 0:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_select_done"))
            return

        path = self.queue_table.item(self.queue_table.currentRow(), QUEUE_COL_FILE).data(Qt.UserRole)
        item = next((i for i in self.queue_items if i.path == path), None)

        if item:
            item.status = STATUS_WAITING
            item.results = None
            item.edited = False
            item.undo_stack.clear()
            item.redo_stack.clear()
            self._update_queue_row(path)
            self.list_lines.clear()
            self.canvas.set_overlay_enabled(False)
            self._set_progress_idle(0)
            self.start_ocr()

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
            item.status = STATUS_DONE
            item.results = (text, kr_records, im, recs)
            item.edited = False
            item.undo_stack.clear()
            item.redo_stack.clear()
            self._update_queue_row(path)

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

    def on_failed(self, msg):
        QMessageBox.critical(self, self._tr("err_title"), msg)
        self.act_play.setEnabled(True)
        self.act_stop.setEnabled(False)
        self._set_progress_idle(0)

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
                    }[status_enum]
                    status_item.setText(f"{status_icon} {self._tr(status_key)}")

                    if status_enum == STATUS_DONE:
                        status_item.setForeground(QBrush(QColor("green")))
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

    def on_line_selected(self, row):
        task = self._current_task()
        if not task or not task.results or row < 0:
            return
        _, _, _, recs = task.results
        if 0 <= row < len(recs):
            self.canvas.select_idx(row)

    def on_rect_clicked(self, idx):
        if 0 <= idx < self.list_lines.count():
            self.list_lines.setCurrentRow(idx)
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

    def on_line_item_edited(self, item: QListWidgetItem):
        task = self._current_task()
        if not task or not task.results or task.status != STATUS_DONE:
            return

        text, kr_records, im, recs = task.results
        row = self.list_lines.row(item)
        if row is None or not (0 <= row < len(recs)):
            return

        target_idx, new_text = self._parse_line_item_full(item.text())
        new_text = (new_text or "").strip()

        if target_idx is None:
            target_idx = row

        target_idx = max(0, min(len(recs) - 1, int(target_idx)))

        def normalize_display(selected_row: int):
            self.list_lines.blockSignals(True)
            for i, rv in enumerate(recs):
                it = self.list_lines.item(i)
                if it:
                    it.setText(f"{i + 1:04d}  {rv.text}")
                    it.setData(Qt.UserRole, i)
            self.list_lines.blockSignals(False)
            self.list_lines.setCurrentRow(max(0, min(self.list_lines.count() - 1, selected_row)))

        if target_idx == row and new_text == recs[row].text:
            normalize_display(row)
            return

        self._push_undo(task)

        if target_idx != row:
            self._push_undo(task)

            moved = RecordView(
                recs[row].idx,
                new_text,
                recs[row].bbox
            )

            recs.pop(row)
            recs.insert(target_idx, moved)

            task.edited = True
            self._sync_ui_after_recs_change(task, keep_row=target_idx)
            return

        # Nur Text ändern, BBox unverändert lassen
        recs[row].text = new_text
        task.edited = True
        self._sync_ui_after_recs_change(task, keep_row=row)

        def normalize_display(selected_row: int):
            self.list_lines.blockSignals(True)
            for i, rv in enumerate(recs):
                it = self.list_lines.item(i)
                if it:
                    it.setText(f"{i + 1:04d}  {rv.text}")
                    it.setData(Qt.UserRole, i)
            self.list_lines.blockSignals(False)
            self.list_lines.setCurrentRow(max(0, min(self.list_lines.count() - 1, selected_row)))

        if target_idx == row and new_text == recs[row].text:
            normalize_display(row)
            return

        self._push_undo(task)

        if target_idx != row:

            recs[row].text = new_text
            recs[row], recs[target_idx] = recs[target_idx], recs[row]

            task.edited = True
            self._sync_ui_after_recs_change(task, keep_row=target_idx)
            return

        old_text = recs[row].text
        recs[row].text = new_text
        task.edited = True

        if recs[row].bbox and im:
            x0, y0, x1, y1 = recs[row].bbox
            old_len = max(1, len(old_text))
            new_len = max(1, len(new_text))
            w = max(10, x1 - x0)
            avg_char = w / float(old_len)
            new_w = int(max(10, avg_char * new_len))
            img_w, img_h = im.size
            new_x1 = min(img_w, x0 + new_w)
            recs[row].bbox = (x0, y0, new_x1, y1)

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

        row = self.list_lines.row(item)

        menu = QMenu()
        act_swap = menu.addAction(self._tr("line_menu_swap_with"))
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

        if chosen == act_swap:
            self._swap_line_with_dialog(task, row)
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

        preview_im = _load_image_color(task.path)
        self.canvas.load_pil_image(preview_im, preserve_view=True)
        self.canvas.set_overlay_enabled(task.status == STATUS_DONE)
        if self.show_overlay:
            self.canvas.draw_overlays(recs)

        self._populate_lines_list(recs, keep_row=keep_row)

    def _move_line(self, task: TaskItem, row: int, direction: int):
        text, kr_records, im, recs = task.results
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
        text, kr_records, im, recs = task.results
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
        text, kr_records, im, recs = task.results
        if not (0 <= row < len(recs)):
            return
        self._push_undo(task)
        recs.pop(row)
        task.edited = True
        next_row = min(row, max(0, len(recs) - 1)) if recs else None
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

    def on_overlay_rect_changed(self, idx: int, scene_rect: QRectF):
        task = self._ensure_overlay_possible()
        if not task:
            return

        text, kr_records, im, recs = task.results
        if not (0 <= idx < len(recs)):
            return

        if im:
            img_w, img_h = im.size
            r = scene_rect.normalized()
            x0 = max(0, min(img_w - 1, _safe_int(r.left())))
            y0 = max(0, min(img_h - 1, _safe_int(r.top())))
            x1 = max(1, min(img_w, _safe_int(r.right())))
            y1 = max(1, min(img_h, _safe_int(r.bottom())))

            if x1 <= x0:
                x1 = min(img_w, x0 + 1)
            if y1 <= y0:
                y1 = min(img_h, y0 + 1)

            old = recs[idx].bbox
            new = (x0, y0, x1, y1)
            if old != new:
                self._push_undo(task)
                recs[idx].bbox = new
                task.edited = True

                keep = self.list_lines.currentRow() if self.list_lines.currentRow() >= 0 else idx
                self._sync_ui_after_recs_change(task, keep_row=keep)

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

        if fmt in ("alto", "hocr"):
            try:
                for i, rv in enumerate(record_views):
                    if i < len(kr_records) and hasattr(kr_records[i], "prediction"):
                        try:
                            kr_records[i].prediction = rv.text
                        except Exception:
                            pass
            except Exception:
                pass

            img_name = os.path.basename(path)
            xml = serialization.serialize(kr_records, image_name=img_name, image_size=export_image.size, template=fmt)
            with open(path, "w", encoding="utf-8") as f:
                f.write(xml)
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

    def closeEvent(self, event):
        try:
            if self.worker and self.worker.isRunning():
                self.worker.requestInterruption()
                self.worker.wait(2000)

            if self.ai_worker and self.ai_worker.isRunning():
                self.ai_worker.cancel()
                self.ai_worker.wait(2000)

            if self.ai_batch_worker and self.ai_batch_worker.isRunning():
                self.ai_batch_worker.cancel()
                self.ai_batch_worker.wait(2000)

            if self.export_worker and self.export_worker.isRunning():
                self.export_worker.requestInterruption()
                self.export_worker.wait(2000)

            if self.pdf_worker and self.pdf_worker.isRunning():
                self.pdf_worker.requestInterruption()
                self.pdf_worker.wait(2000)

            self._cleanup_temp_dirs()
        except Exception:
            pass

        super().closeEvent(event)

def main():
    # Windows: sorgt dafür, dass Taskleisten-Icon korrekt zugeordnet wird
    if sys.platform.startswith("win"):
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("bottled.kraken.app")
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    icon_path = resource_path("icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    splash = QProgressDialog("Programm startet, bitte kurz warten…", None, 0, 0)
    splash.setWindowTitle("Bottled Kraken")
    splash.setWindowModality(Qt.ApplicationModal)
    splash.setCancelButton(None)
    splash.setMinimumDuration(0)
    splash.setAutoClose(False)
    splash.setAutoReset(False)
    if os.path.exists(icon_path):
        splash.setWindowIcon(QIcon(icon_path))
    splash.show()
    QCoreApplication.processEvents()

    w = MainWindow()
    app.aboutToQuit.connect(w._cleanup_temp_dirs)

    if os.path.exists(icon_path):
        w.setWindowIcon(QIcon(icon_path))

    splash.close()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()