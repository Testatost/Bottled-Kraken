# -*- coding: utf-8 -*-
import os
import sys
import json
import csv
import warnings
import re
from dataclasses import dataclass, field
from typing import Optional, List, Any, Tuple, Dict, Callable

# GUI Framework
from PySide6.QtCore import Qt, QThread, Signal, QRectF, QUrl, QTimer, QSize, QPointF, QPoint
from PySide6.QtGui import (
    QPixmap, QPen, QBrush, QColor, QFont, QDragEnterEvent, QDropEvent, QAction,
    QKeySequence, QActionGroup, QIcon, QPalette
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox,
    QLabel, QPushButton, QProgressBar, QVBoxLayout,
    QListWidget, QListWidgetItem, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QGraphicsSimpleTextItem, QSplitter, QStatusBar,
    QMenu, QTableWidget, QTableWidgetItem, QHeaderView, QToolBar,
    QAbstractItemView, QInputDialog, QDialog, QDialogButtonBox, QRadioButton,
    QListWidget as QListWidget2, QSpinBox, QFormLayout
)

# PySide object validity helper
from shiboken6 import isValid

# Image & PDF
from PIL import Image
from PIL.ImageQt import ImageQt
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader

# Kraken & ML
warnings.filterwarnings("ignore", message="Using legacy polygon extractor*", category=UserWarning)
from kraken import blla, rpred, serialization
from kraken.lib import models, vgsl
import torch


# -----------------------------
# CONSTANTS
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

STATUS_ICONS = {
    STATUS_WAITING: "⏳",
    STATUS_PROCESSING: "⚙️",
    STATUS_DONE: "✅",
    STATUS_ERROR: "❌"
}

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

# -----------------------------
# TRANSLATIONS
# -----------------------------
TRANSLATIONS = {
    "de": {
        "app_title": "Kraken OCR Professional",
        "toolbar_main": "Werkzeugleiste",
        "menu_file": "&Datei",
        "menu_edit": "&Bearbeiten",
        "menu_export": "Exportieren als...",
        "menu_exit": "Beenden",
        "menu_models": "&Modelle",
        "menu_options": "&Optionen",
        "menu_languages": "Sprachen",
        "menu_hw": "CPU/GPU",
        "menu_reading": "Leserichtung",
        "menu_appearance": "Erscheinungsbild",

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

        "act_add_files": "Dateien zum Wartebereich hinzufügen...",
        "act_download_model": "Modell herunterladen...",
        "act_delete": "Löschen",
        "act_rename": "Umbenennen...",
        "act_clear_queue": "Wartebereich löschen",
        "act_start_ocr": "OCR starten",
        "act_stop_ocr": "OCR stoppen",
        "act_re_ocr": "Ergebnis zurücksetzen & OCR wiederholen",
        "act_re_ocr_tip": "Löscht Ergebnisse der aktuellen Datei und startet OCR erneut",
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

        "drop_hint": "Anklicken um Datei hinzuzufügen",
        "queue_drop_hint": "Datei hier ablegen",

        "info_title": "Information",
        "warn_title": "Warnung",
        "err_title": "Fehler",

        "theme_bright": "Hell",
        "theme_dark": "Dunkel",

        "warn_queue_empty": "Wartebereich ist leer oder alle Elemente wurden verarbeitet.",
        "warn_select_done": "Bitte wählen Sie ein fertiges Element zum Exportieren.",
        "warn_need_rec": "Bitte wählen Sie zuerst ein Format-Modell (Recognition) aus.",
        "warn_need_seg": "Bitte wählen Sie zuerst ein Baseline-Modell aus.",

        "msg_stopping": "Breche ab...",
        "msg_finished": "Batch abgeschlossen.",
        "msg_device": "Gerät gesetzt auf: {}",
        "msg_exported": "Exportiert: {}",
        "msg_loaded_rec": "Format-Modell: {}",
        "msg_loaded_seg": "Baseline-Modell: {}",

        "err_load": "Bild kann nicht geladen werden: {}",

        "dlg_title_rename": "Umbenennen",
        "dlg_label_name": "Neuer Dateiname:",
        "dlg_save": "Speichern",
        "dlg_load_img": "Bilder wählen",
        "dlg_filter_img": "Bilder (*.png *.jpg *.jpeg *.tif *.bmp *.webp)",
        "dlg_choose_rec": "Recognition-Modell: ",
        "dlg_choose_seg": "Baseline-Modell: ",
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
    },

    "en": {
        "app_title": "Kraken OCR Professional",
        "toolbar_main": "Toolbar",
        "menu_file": "&File",
        "menu_edit": "&Edit",
        "menu_export": "Export as...",
        "menu_exit": "Exit",
        "menu_models": "&Models",
        "menu_options": "&Options",
        "menu_languages": "Languages",
        "menu_hw": "CPU/GPU",
        "menu_reading": "Reading Direction",
        "menu_appearance": "Appearance",

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

        "act_add_files": "Add files to queue...",
        "act_download_model": "Download model...",
        "act_delete": "Delete",
        "act_rename": "Rename...",
        "act_clear_queue": "Clear queue",
        "act_start_ocr": "Start OCR",
        "act_stop_ocr": "Stop OCR",
        "act_re_ocr": "Reset result & re-run OCR",
        "act_re_ocr_tip": "Clears results of the current file and runs OCR again",
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

        "drop_hint": "Click here to add a file",
        "queue_drop_hint": "Drop file here",

        "info_title": "Information",
        "warn_title": "Warning",
        "err_title": "Error",

        "theme_bright": "Bright",
        "theme_dark": "Dark",

        "warn_queue_empty": "Queue is empty or all items are processed.",
        "warn_select_done": "Please select a completed item to export.",
        "warn_need_rec": "Please select a format model (recognition) first.",
        "warn_need_seg": "Please select a baseline model first.",

        "msg_stopping": "Stopping...",
        "msg_finished": "Batch finished.",
        "msg_device": "Device set to: {}",
        "msg_exported": "Exported: {}",
        "msg_loaded_rec": "Format model: {}",
        "msg_loaded_seg": "Baseline model: {}",

        "err_load": "Cannot load image: {}",

        "dlg_title_rename": "Rename",
        "dlg_label_name": "New filename:",
        "dlg_save": "Save",
        "dlg_load_img": "Choose images",
        "dlg_filter_img": "Images (*.png *.jpg *.jpeg *.tif *.bmp *.webp)",
        "dlg_choose_rec": "recognition model: ",
        "dlg_choose_seg": "baseline model: ",
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
    },

    "fr": {
        "app_title": "Professionnel Kraken OCR",
        "toolbar_main": "Barre d’outils",
        "menu_file": "&Fichier",
        "menu_edit": "&Édition",
        "menu_export": "Exporter en tant que...",
        "menu_exit": "Quitter",
        "menu_models": "&Modèles",
        "menu_options": "&Options",
        "menu_languages": "Langues",
        "menu_hw": "CPU/GPU",
        "menu_reading": "Direction de lecture",
        "menu_appearance": "Apparence",

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

        "act_add_files": "Ajouter des fichiers...",
        "act_download_model": "Télécharger le modèle...",
        "act_delete": "Supprimer",
        "act_rename": "Renommer...",
        "act_clear_queue": "Vider la file d’attente",
        "act_start_ocr": "Démarrer OCR",
        "act_stop_ocr": "Arrêter OCR",
        "act_re_ocr": "Réinitialiser & relancer OCR",
        "act_re_ocr_tip": "Efface les résultats du fichier actuel et relance l’OCR",
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

        "drop_hint": "Cliquez pour ajouter un fichier",
        "queue_drop_hint": "Déposer un fichier ici",

        "info_title": "Information",
        "warn_title": "Avertissement",
        "err_title": "Erreur",

        "theme_bright": "Clair",
        "theme_dark": "Sombre",

        "warn_queue_empty": "La file d’attente est vide ou tous les éléments ont été traités.",
        "warn_select_done": "Veuillez sélectionner un élément terminé à exporter.",
        "warn_need_rec": "Veuillez d’abord sélectionner un modèle de format (reconnaissance).",
        "warn_need_seg": "Veuillez d’abord sélectionner un modèle de baseline.",

        "msg_stopping": "Arrêt...",
        "msg_finished": "Traitement terminé.",
        "msg_device": "Appareil réglé sur: {}",
        "msg_exported": "Exporté: {}",
        "msg_loaded_rec": "Modèle de format: {}",
        "msg_loaded_seg": "Modèle de baseline: {}",

        "err_load": "Impossible de charger l’image: {}",

        "dlg_title_rename": "Renommer",
        "dlg_label_name": "Nouveau nom de fichier:",
        "dlg_save": "Enregistrer",
        "dlg_load_img": "Choisir des images",
        "dlg_filter_img": "Images (*.png *.jpg *.jpeg *.tif *.bmp *.webp)",
        "dlg_choose_rec": "le modèle de reconnaissance: ",
        "dlg_choose_seg": "le modèle de baseline: ",
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
    }
}


# -----------------------------
# DATA CLASSES
# -----------------------------
@dataclass
class RecordView:
    idx: int
    text: str
    bbox: Optional[Tuple[int, int, int, int]]  # (x0,y0,x1,y1)


UndoSnapshot = Tuple[List[Tuple[str, Optional[Tuple[int, int, int, int]]]], int]  # (recs_state, selected_row)


@dataclass
class TaskItem:
    path: str
    display_name: str
    status: int = STATUS_WAITING
    results: Optional[Tuple[str, list, Image.Image, List[RecordView]]] = None
    edited: bool = False
    undo_stack: List[UndoSnapshot] = field(default_factory=list)
    redo_stack: List[UndoSnapshot] = field(default_factory=list)


@dataclass
class OCRJob:
    input_paths: List[str]
    recognition_model_path: str
    segmentation_model_path: Optional[str]
    device: str
    reading_direction: int
    export_format: str
    export_dir: Optional[str]


# -----------------------------
# GEOMETRY & SORTING
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


def sort_records_reading_order(records, image_width: int, reading_mode: int = READING_MODES["TB_LR"]):
    def q(values, p):
        if not values:
            return None
        vals = sorted(values)
        k = (len(vals) - 1) * p
        f = int(k)
        c = min(f + 1, len(vals) - 1)
        if f == c:
            return vals[f]
        return vals[f] + (vals[c] - vals[f]) * (k - f)

    def bb_center_x(bb):
        return (bb[0] + bb[2]) / 2.0

    def bb_center_y(bb):
        return (bb[1] + bb[3]) / 2.0

    def bb_h(bb):
        return bb[3] - bb[1]

    def bb_w(bb):
        return bb[2] - bb[0]

    def is_fullwidth(bb):
        return bb_w(bb) >= int(image_width * 0.75)

    items = []
    for r in records:
        bb = record_bbox(r)
        if bb:
            items.append((r, bb))

    if not items:
        return list(records)

    MIN_H = 14
    body_candidates = [(r, bb) for (r, bb) in items if bb_h(bb) >= MIN_H and not is_fullwidth(bb)]

    if len(body_candidates) < 6:
        reverse_y = (reading_mode // 2) == 1
        reverse_x = (reading_mode % 2) == 1
        return [r for r, _ in sorted(items, key=lambda x: (x[1][1] if not reverse_y else -x[1][1],
                                                           x[1][0] if not reverse_x else -x[1][0]))]

    xs = [bb_center_x(bb) for _, bb in body_candidates]
    c1 = q(xs, 0.25)
    c2 = q(xs, 0.75)

    if c1 is None or c2 is None:
        return [r for r, _ in sorted(items, key=lambda x: (x[1][1], x[1][0]))]

    for _ in range(8):
        g1, g2 = [], []
        for x in xs:
            (g1 if abs(x - c1) <= abs(x - c2) else g2).append(x)
        c1 = sum(g1) / len(g1) if g1 else c1
        c2 = sum(g2) / len(g2) if g2 else c2

    if c1 > c2:
        c1, c2 = c2, c1

    if abs(c2 - c1) < image_width * 0.18:
        return [r for r, _ in sorted(items, key=lambda x: (x[1][1], x[1][0]))]

    ys_top = [bb[1] for _, bb in body_candidates]
    ys_bot = [bb[3] for _, bb in body_candidates]
    body_top = q(ys_top, 0.08)
    body_bot = q(ys_bot, 0.92)

    if body_top is None or body_bot is None:
        return [r for r, _ in sorted(items, key=lambda x: (x[1][1], x[1][0]))]

    MARGIN_Y = 10
    header, footer, midband = [], [], []

    for r, bb in items:
        if bb_h(bb) < MIN_H:
            midband.append((r, bb))
            continue
        if bb[3] < (body_top - MARGIN_Y):
            header.append((r, bb))
        elif bb[1] > (body_bot + MARGIN_Y):
            footer.append((r, bb))
        else:
            midband.append((r, bb))

    rev_y = (reading_mode == READING_MODES["BT_LR"] or reading_mode == READING_MODES["BT_RL"])
    rev_x = (reading_mode == READING_MODES["TB_RL"] or reading_mode == READING_MODES["BT_RL"])

    def sort_key(item):
        bb = item[1]
        ky = bb_center_y(bb)
        kx = bb[0]
        return (-ky if rev_y else ky, -kx if rev_x else kx)

    header_sorted = sorted(header, key=sort_key)
    footer_sorted = sorted(footer, key=sort_key)

    left_col, right_col = [], []
    for r, bb in midband:
        if is_fullwidth(bb):
            left_col.append((r, bb))
            continue
        x = bb_center_x(bb)
        if abs(x - c1) <= abs(x - c2):
            left_col.append((r, bb))
        else:
            right_col.append((r, bb))

    left_sorted = sorted(left_col, key=sort_key)
    right_sorted = sorted(right_col, key=sort_key)

    if reading_mode == READING_MODES["TB_LR"]:
        ordered = [r for r, _ in header_sorted] + [r for r, _ in left_sorted] + \
                  [r for r, _ in right_sorted] + [r for r, _ in footer_sorted]
    elif reading_mode == READING_MODES["TB_RL"]:
        ordered = [r for r, _ in header_sorted] + [r for r, _ in right_sorted] + \
                  [r for r, _ in left_sorted] + [r for r, _ in footer_sorted]
    elif reading_mode == READING_MODES["BT_LR"]:
        ordered = [r for r, _ in footer_sorted] + [r for r, _ in left_sorted] + \
                  [r for r, _ in right_sorted] + [r for r, _ in header_sorted]
    else:
        ordered = [r for r, _ in footer_sorted] + [r for r, _ in right_sorted] + \
                  [r for r, _ in left_sorted] + [r for r, _ in header_sorted]

    return ordered


def clamp_bbox(bb: Tuple[int, int, int, int], w: int, h: int) -> Optional[Tuple[int, int, int, int]]:
    x0, y0, x1, y1 = bb
    return (max(0, min(w - 1, x0)), max(0, min(h - 1, y0)),
            max(0, min(w, x1)), max(0, min(h, y1)))


def _safe_int(v, default=0):
    try:
        return int(v)
    except Exception:
        return default


# -----------------------------
# TABLE EXPORT HELPERS
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
    if abs(ay0 - by0) > 12:
        return False
    mid = page_width // 2
    if (ax1 < mid and bx0 > mid) or (bx1 < mid and ax0 > mid):
        return False
    return True


def group_rows_by_y(records: List[RecordView], page_width: int):
    rows = []
    sorted_recs = sorted([r for r in records if r.bbox], key=lambda rv: (rv.bbox[1], rv.bbox[0]))
    for r in sorted_recs:
        placed = False
        for row in rows:
            if is_same_visual_row(row[0], r, page_width):
                row.append(r)
                placed = True
                break
        if not placed:
            rows.append([r])
    for row in rows:
        row.sort(key=lambda rv: rv.bbox[0])
    return rows


def table_to_rows(records: List[RecordView], page_width: int) -> List[List[str]]:
    rows = group_rows_by_y(records, page_width)
    cols = cluster_columns(records)
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
# RESIZABLE / MOVABLE RECT ITEM
# -----------------------------
class ResizableRectItem(QGraphicsRectItem):
    """
    Movable + resizable rect.
    Calls on_changed(idx, QRectF(scene coords)) after mouse release.
    """
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
# DROP-ENABLED QUEUE TABLE
# -----------------------------
class DropQueueTable(QTableWidget):
    files_dropped = Signal(list)
    table_resized = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDragDropOverwriteMode(False)
        self.setDragDropMode(QAbstractItemView.DropOnly)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.table_resized.emit()

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
            if p and os.path.exists(p):
                files.append(p)
        if files:
            self.files_dropped.emit(files)
            event.acceptProposedAction()
        else:
            event.ignore()


# -----------------------------
# LINES LIST (Delete + DnD reorder)
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
# OVERLAY BOX EDIT DIALOG
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
# IMAGE CANVAS WITH CONTEXT MENU + DOUBLE CLICK SELECTION
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
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.ScrollHandDrag)

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

        # draw-box mode
        self._draw_mode = False
        self._draw_start = None
        self._draw_rect_item: Optional[QGraphicsRectItem] = None
        self._pen_draw = QPen(QColor("#00ff7f"), 2)
        self._brush_draw = QBrush(QColor(0, 255, 127, 40))

        # enabled only after OCR finished
        self._overlay_enabled = False

        self._show_drop_hint()

    @staticmethod
    def _event_point(event) -> QPoint:
        # Works across PySide6 versions: sometimes event.position() exists, sometimes not.
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

    def dropEvent(self, event: QDropEvent):
        if not event.mimeData().hasUrls():
            event.ignore()
            return
        files = []
        for u in event.mimeData().urls():
            p = u.toLocalFile()
            if p and os.path.exists(p):
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
        self.setDragMode(QGraphicsView.ScrollHandDrag)

    def contextMenuEvent(self, event):
        pos = event.pos()
        item = self.itemAt(pos)

        menu = QMenu(self)
        tr = self.tr_func

        if not self._overlay_enabled:
            disabled = menu.addAction(tr("overlay_only_after_ocr") if tr else "Overlay editing only after OCR.")
            disabled.setEnabled(False)
            menu.exec(event.globalPos())
            return

        if isinstance(item, ResizableRectItem):
            idx = item.idx
            act_sel = menu.addAction(tr("canvas_menu_select_line") if tr else "Select line")
            menu.addSeparator()
            act_edit = menu.addAction(tr("canvas_menu_edit_box") if tr else "Edit overlay box...")
            act_del = menu.addAction(tr("canvas_menu_delete_box") if tr else "Delete overlay box")
            menu.addSeparator()
            act_add_draw = menu.addAction(tr("canvas_menu_add_box_draw") if tr else "Add overlay box (draw)")

            chosen = menu.exec(event.globalPos())
            if not chosen:
                return
            if chosen == act_sel:
                self.overlay_select_requested.emit(idx)
            elif chosen == act_edit:
                self.overlay_edit_requested.emit(idx)
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

        item = self.itemAt(self._event_point(event))
        if isinstance(item, ResizableRectItem):
            self.rect_clicked.emit(item.idx)
            return

        if event.button() == Qt.LeftButton and not self._pixmap_item:
            self.canvas_clicked.emit()

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(self._event_point(event))
        if isinstance(item, ResizableRectItem) and event.button() == Qt.LeftButton:
            self.rect_clicked.emit(item.idx)
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
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

    def _show_drop_hint(self):
        if not self._pixmap_item and not self._drop_text:
            font = QFont("Arial", 20)
            font.setItalic(True)
            txt = self.tr_func("drop_hint") if self.tr_func else "Click to add a file"
            self._drop_text = self.scene.addText(txt, font)
            rect = self._drop_text.boundingRect()
            self._drop_text.setPos(-rect.width() / 2, -rect.height() / 2)
            c = QColor("#aaa") if self._bg_color.lightness() < 128 else QColor("#555")
            self._drop_text.setDefaultTextColor(c)

    def load_pil_image(self, im: Image.Image):
        self.stop_draw_box_mode()
        self.scene.clear()
        self._pixmap_item = None
        self._rects.clear()
        self._labels.clear()
        self._selected_idx = None
        self._drop_text = None
        self.resetTransform()
        self._zoom = 1.0

        qim = ImageQt(im.convert("RGB"))
        pix = QPixmap.fromImage(qim)
        self._pixmap_item = self.scene.addPixmap(pix)
        self._pixmap_item.setZValue(0)
        self.setSceneRect(self.scene.itemsBoundingRect())
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
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


# -----------------------------
# OCR WORKER
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
            # Both CUDA and ROCm use torch.cuda backend; ROCm is indicated by torch.version.hip
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

                # If user selected ROCm or HIP is present -> show ROCm/HIP info; otherwise CUDA info
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
            # show chosen backend label (cuda/rocm/mps/cpu) + actual torch device
            self.device_resolved.emit(f"{self._device_label} -> {self._device}")
            self._emit_gpu_info(self._device)
        if self._rec_model is None:
            self._rec_model = self._load_rec_model(self.job.recognition_model_path, self._device)
        if self._seg_model is None:
            if not self.job.segmentation_model_path:
                raise ValueError("No baseline model selected.")
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

    def _ocr_one(self, img_path: str, file_idx: int, total_files: int):
        self.file_started.emit(img_path)
        try:
            im = Image.open(img_path)

            seg = blla.segment(im, model=self._seg_model)
            expected = self._seg_expected_lines(seg)

            kr_records = []
            done = 0
            for rec in rpred.rpred(self._rec_model, im, seg):
                kr_records.append(rec)
                done += 1
                if expected and expected > 0:
                    self._emit_overall_progress(file_idx, total_files, done / expected)

                if self.isInterruptionRequested():
                    break

            if self.isInterruptionRequested():
                return

            kr_sorted = sort_records_reading_order(kr_records, im.size[0], self.job.reading_direction)

            wide_line_splitter = re.compile(r"\s{2,}")
            record_views: List[RecordView] = []
            lines: List[str] = []
            out_idx = 0
            page_w, page_h = im.size

            for r in kr_sorted:
                pred = getattr(r, "prediction", None)
                if pred is None:
                    continue
                txt = str(pred)
                bb = record_bbox(r)

                if bb:
                    x0, y0, x1, y1 = bb
                    w = x1 - x0
                    if w > int(page_w * 0.80):
                        parts = wide_line_splitter.split(txt, maxsplit=1)
                        if len(parts) == 2:
                            left_txt, right_txt = map(str.strip, parts)
                            mid = page_w // 2
                            left_bb = clamp_bbox((0, y0, mid, y1), page_w, page_h)
                            right_bb = clamp_bbox((mid, y0, page_w, y1), page_w, page_h)

                            if left_bb:
                                record_views.append(RecordView(out_idx, left_txt, left_bb))
                                lines.append(left_txt)
                                out_idx += 1
                            if right_bb:
                                record_views.append(RecordView(out_idx, right_txt, right_bb))
                                lines.append(right_txt)
                                out_idx += 1
                            continue

                record_views.append(RecordView(out_idx, txt, bb))
                lines.append(txt)
                out_idx += 1

            self._emit_overall_progress(file_idx, total_files, 1.0)
            text = "\n".join(lines).strip()
            self.file_done.emit(img_path, text, kr_sorted, im, record_views)

        except Exception as e:
            self.file_error.emit(img_path, str(e))

    def run(self):
        try:
            if not os.path.exists(self.job.recognition_model_path):
                raise ValueError("Recognition model not found.")
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


# -----------------------------
# EXPORT DIALOGS
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

        self.listw = QListWidget2()
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
# MAIN WINDOW
# -----------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(1600, 900)
        self.setAcceptDrops(True)

        self.current_lang = "de"
        self.reading_direction = READING_MODES["TB_LR"]
        self.device_str = "cpu"
        self.show_overlay = True
        self.model_path = ""
        self.seg_model_path = ""
        self.current_export_dir = ""
        self.current_theme = "bright"

        # queue columns dynamic ratio
        self.queue_col_ratio = 0.75
        self._resizing_cols = False

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(self._tr("status_ready"))

        self.worker: Optional[OCRWorker] = None
        self.queue_items: List[TaskItem] = []

        # Canvas
        self.canvas = ImageCanvas(tr_func=self._tr)
        self.canvas.rect_clicked.connect(self.on_rect_clicked)
        self.canvas.rect_changed.connect(self.on_overlay_rect_changed)
        self.canvas.files_dropped.connect(self.add_files_to_queue)
        self.canvas.canvas_clicked.connect(self.on_canvas_click)
        self.canvas.box_drawn.connect(self.on_box_drawn)

        self.canvas.overlay_add_draw_requested.connect(self.on_canvas_add_box_draw)
        self.canvas.overlay_edit_requested.connect(self.on_canvas_edit_box)
        self.canvas.overlay_delete_requested.connect(self.on_canvas_delete_box)
        self.canvas.overlay_select_requested.connect(self.on_canvas_select_line)

        # Queue Table
        self.queue_table = DropQueueTable()
        self.queue_table.setColumnCount(2)
        self.queue_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.queue_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.queue_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.queue_table.itemChanged.connect(self.on_item_changed)
        self.queue_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.queue_table.customContextMenuRequested.connect(self.queue_context_menu)
        self.queue_table.cellDoubleClicked.connect(self.on_queue_double_click)
        self.queue_table.files_dropped.connect(self.add_files_to_queue)
        self.queue_table.table_resized.connect(self._fit_queue_columns_exact)

        header = self.queue_table.horizontalHeader()
        header.setSectionsMovable(False)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.sectionResized.connect(self._on_queue_header_resized)
        self.queue_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Queue hint overlay
        self.queue_hint = QLabel(self._tr("queue_drop_hint"), self.queue_table.viewport())
        self.queue_hint.setAlignment(Qt.AlignCenter)
        self.queue_hint.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.queue_hint.setStyleSheet("color: rgba(180,180,180,180); font-style: italic;")
        self.queue_hint.hide()

        # Lines list
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
        self.progress_bar.setValue(0)

        self.lbl_queue = QLabel(self._tr("lbl_queue"))
        self.lbl_lines = QLabel(self._tr("lbl_lines"))

        # Toolbar Actions
        self.act_add = QAction(QIcon.fromTheme("document-open"), self._tr("act_add_files"), self)
        self.act_add.triggered.connect(self.choose_files)

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

        # Undo / Redo actions
        self.act_undo = QAction(self._tr("act_undo"), self)
        self.act_undo.setShortcut(QKeySequence("Ctrl+Z"))
        self.act_undo.triggered.connect(self.undo)

        self.act_redo = QAction(self._tr("act_redo"), self)
        self.act_redo.setShortcut(QKeySequence("Ctrl+Y"))
        self.act_redo.triggered.connect(self.redo)

        self.addAction(self.act_undo)
        self.addAction(self.act_redo)

        self.btn_rec_model = QPushButton(self._tr("dlg_choose_rec") + " -")
        self.btn_rec_model.setIcon(QIcon.fromTheme("document-open"))
        self.btn_rec_model.clicked.connect(self.choose_rec_model)

        self.btn_seg_model = QPushButton(self._tr("dlg_choose_seg") + " -")
        self.btn_seg_model.setIcon(QIcon.fromTheme("document-open"))
        self.btn_seg_model.clicked.connect(self.choose_seg_model)

        self._pending_box_for_row: Optional[int] = None
        self._pending_new_line_box: bool = False

        self._init_ui()
        self._init_menu()
        self.apply_theme("bright")
        self.retranslate_ui()

        QTimer.singleShot(0, self._fit_queue_columns_exact)
        QTimer.singleShot(0, self._update_queue_hint)
        QTimer.singleShot(0, self._refresh_hw_menu_availability)

        self.canvas.set_overlay_enabled(False)

    # -----------------------------
    # Translation
    # -----------------------------
    def _tr(self, key: str, *args):
        txt = TRANSLATIONS.get(self.current_lang, TRANSLATIONS["de"]).get(key, key)
        if args:
            return txt.format(*args)
        return txt

    # -----------------------------
    # Undo helpers (snapshots)
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

    # -----------------------------
    # UI
    # -----------------------------
    def _init_ui(self):
        self.toolbar = QToolBar(self._tr("toolbar_main"))
        self.addToolBar(self.toolbar)
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setIconSize(QSize(20, 20))

        self.toolbar.addAction(self.act_add)
        self.toolbar.addAction(self.act_clear)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.act_play)
        self.toolbar.addAction(self.act_stop)
        self.toolbar.addAction(self.act_re_ocr)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.btn_rec_model)
        self.toolbar.addWidget(self.btn_seg_model)

        right = QVBoxLayout()
        right.addWidget(self.lbl_queue)
        right.addWidget(self.queue_table, 2)
        right.addWidget(self.progress_bar)
        right.addWidget(self.lbl_lines)
        right.addWidget(self.list_lines, 3)

        right_widget = QLabel()
        right_widget.setLayout(right)

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.canvas)
        left_widget = QLabel()
        left_widget.setLayout(left_layout)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(right_widget)
        self.splitter.setSizes([1000, 500])
        self.splitter.splitterMoved.connect(lambda *_: self._fit_queue_columns_exact())
        self.setCentralWidget(self.splitter)

    def _init_menu(self):
        menubar = self.menuBar()

        self.file_menu = menubar.addMenu(self._tr("menu_file"))
        self.edit_menu = menubar.addMenu(self._tr("menu_edit"))

        self.edit_menu.addAction(self.act_undo)
        self.edit_menu.addAction(self.act_redo)

        self.act_add_files = QAction(self._tr("act_add_files"), self)
        self.act_add_files.triggered.connect(self.choose_files)
        self.file_menu.addAction(self.act_add_files)

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
        self.act_rec = QAction(self._tr("dlg_choose_rec"), self)
        self.act_rec.triggered.connect(self.choose_rec_model)
        self.models_menu.addAction(self.act_rec)

        self.act_seg = QAction(self._tr("dlg_choose_seg"), self)
        self.act_seg.triggered.connect(self.choose_seg_model)
        self.models_menu.addAction(self.act_seg)

        self.models_menu.addSeparator()
        self.act_download = QAction(self._tr("act_download_model"), self)
        self.act_download.triggered.connect(self.open_download_link)
        self.models_menu.addAction(self.act_download)

        self.options_menu = menubar.addMenu(self._tr("menu_options"))

        # Languages
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

        # HW menu
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

        # Reading direction
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

        # Overlay
        self.options_menu.addSeparator()
        self.act_overlay = QAction(self._tr("act_overlay_show"), self)
        self.act_overlay.setCheckable(True)
        self.act_overlay.setChecked(True)
        self.act_overlay.toggled.connect(self._on_overlay_toggled)
        self.options_menu.addAction(self.act_overlay)

        # Theme
        self.options_menu.addSeparator()
        self.theme_menu = self.options_menu.addMenu(self._tr("menu_appearance"))
        self.act_theme_bright = QAction(self._tr("theme_bright"), self)
        self.act_theme_bright.triggered.connect(lambda: self.apply_theme("bright"))
        self.theme_menu.addAction(self.act_theme_bright)
        self.act_theme_dark = QAction(self._tr("theme_dark"), self)
        self.act_theme_dark.triggered.connect(lambda: self.apply_theme("dark"))
        self.theme_menu.addAction(self.act_theme_dark)

    # -----------------------------
    # Queue columns
    # -----------------------------
    def _fit_queue_columns_exact(self):
        if self._resizing_cols:
            return
        self._resizing_cols = True
        try:
            vw = max(1, self.queue_table.viewport().width())
            w0 = int(vw * float(self.queue_col_ratio))
            w1 = vw - w0

            min0, min1 = 80, 60
            if w0 < min0:
                w0 = min0
                w1 = max(min1, vw - w0)
            if w1 < min1:
                w1 = min1
                w0 = max(min0, vw - w1)

            if w0 + w1 != vw:
                w1 = max(min1, vw - w0)

            self.queue_table.setColumnWidth(0, w0)
            self.queue_table.setColumnWidth(1, w1)

            if vw > 0:
                self.queue_col_ratio = max(0.1, min(0.9, w0 / float(vw)))

            self._update_queue_hint()
        finally:
            self._resizing_cols = False

    def _on_queue_header_resized(self, logicalIndex: int, oldSize: int, newSize: int):
        if self._resizing_cols:
            return
        w0 = self.queue_table.columnWidth(0)
        w1 = self.queue_table.columnWidth(1)
        total = max(1, w0 + w1)
        self.queue_col_ratio = max(0.1, min(0.9, w0 / float(total)))
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
                QToolButton {{
                    color: {txt};
                    border: 1px solid {border};
                    border-radius: 6px;
                    padding: 4px 6px;
                    background: transparent;
                }}
                QPushButton {{
                    color: {txt};
                    border: 1px solid {border};
                    border-radius: 6px;
                    padding: 4px 8px;
                    background: transparent;
                }}
                """
            )
        else:
            self.toolbar.setStyleSheet(
                """
                QToolButton { border: none; padding: 4px 6px; }
                QPushButton { border: 1px solid rgba(0,0,0,0.25); border-radius: 6px; padding: 4px 8px; }
                """
            )

    # -----------------------------
    # Language / reading
    # -----------------------------
    def set_language(self, lang):
        self.current_lang = lang
        self.retranslate_ui()
        self._refresh_hw_menu_availability()

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

        self.act_undo.setText(self._tr("act_undo"))
        self.act_redo.setText(self._tr("act_redo"))

        self.act_add_files.setText(self._tr("act_add_files"))
        self.act_exit.setText(self._tr("menu_exit"))
        self.act_download.setText(self._tr("act_download_model"))
        self.act_rec.setText(self._tr("dlg_choose_rec"))
        self.act_seg.setText(self._tr("dlg_choose_seg"))
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
        self.queue_table.setHorizontalHeaderLabels([self._tr("col_file"), self._tr("col_status")])

        if self.model_path:
            self.btn_rec_model.setText(f"{self._tr('dlg_choose_rec')}{os.path.basename(self.model_path)}")
        else:
            self.btn_rec_model.setText(f"{self._tr('dlg_choose_rec')}-")

        if self.seg_model_path:
            self.btn_seg_model.setText(f"{self._tr('dlg_choose_seg')}{os.path.basename(self.seg_model_path)}")
        else:
            self.btn_seg_model.setText(f"{self._tr('dlg_choose_seg')}-")

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

    def _retranslate_queue_rows(self):
        for it in self.queue_items:
            self._update_queue_row(it.path)

    # -----------------------------
    # GPU detection + availability
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

        # ROCm (HIP) availability
        rocm_avail = cuda_avail and (hip_ver is not None)
        rocm_details = ""
        if rocm_avail:
            rocm_details = f"{cuda_name} (HIP {hip_ver})" if cuda_name else f"HIP {hip_ver}"

        # CUDA availability (real CUDA build)
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
    # Drag & Drop on MainWindow
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
            if p and os.path.exists(p):
                files.append(p)
        if files:
            self.add_files_to_queue(files)
            event.acceptProposedAction()
        else:
            event.ignore()

    # -----------------------------
    # Queue + preview
    # -----------------------------
    def choose_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, self._tr("dlg_load_img"), "", self._tr("dlg_filter_img"))
        if files:
            self.add_files_to_queue(files)

    def on_canvas_click(self):
        self.choose_files()

    def add_files_to_queue(self, paths: List[str]):
        added_any = False
        last_added = None
        for p in paths:
            if not p or not os.path.exists(p):
                continue
            if any(it.path == p for it in self.queue_items):
                continue
            self._add_file_to_queue_single(p)
            added_any = True
            last_added = p

        if added_any and last_added:
            self.preview_image(last_added)

        self._fit_queue_columns_exact()
        self._update_queue_hint()

    def _add_file_to_queue_single(self, path: str):
        item = TaskItem(path=path, display_name=os.path.basename(path))
        self.queue_items.append(item)

        row = self.queue_table.rowCount()
        self.queue_table.insertRow(row)

        name_item = QTableWidgetItem(item.display_name)
        name_item.setData(Qt.UserRole, path)
        name_item.setFlags(name_item.flags() | Qt.ItemIsEditable)

        status_item = QTableWidgetItem(f"{STATUS_ICONS[STATUS_WAITING]} {self._tr('status_waiting')}")
        status_item.setFlags(status_item.flags() ^ Qt.ItemIsEditable)

        self.queue_table.setItem(row, 0, name_item)
        self.queue_table.setItem(row, 1, status_item)
        self.queue_table.selectRow(row)

    def on_item_changed(self, item: QTableWidgetItem):
        if item.column() == 0:
            row = item.row()
            path_item = self.queue_table.item(row, 0)
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
        rename_act = menu.addAction(self._tr("act_rename"))
        delete_act = menu.addAction(self._tr("act_delete"))

        action = menu.exec(self.queue_table.viewport().mapToGlobal(pos))
        if not action:
            return

        item = self.queue_table.itemAt(pos)
        if not item:
            return

        row = item.row()
        path = self.queue_table.item(row, 0).data(Qt.UserRole)
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
                self.queue_table.item(row, 0).setText(new_name)

        elif action == delete_act:
            self.delete_selected_queue_items()

    def delete_selected_queue_items(self):
        rows = sorted(set(index.row() for index in self.queue_table.selectedIndexes()), reverse=True)
        if not rows:
            return

        current_preview_path = None
        if self.queue_table.currentRow() >= 0:
            current_preview_path = self.queue_table.item(self.queue_table.currentRow(), 0).data(Qt.UserRole)

        removed_paths = []
        for row in rows:
            path = self.queue_table.item(row, 0).data(Qt.UserRole)
            removed_paths.append(path)
            self.queue_items = [i for i in self.queue_items if i.path != path]
            self.queue_table.removeRow(row)

        if len(self.queue_items) == 0:
            self.canvas.clear_all()
            self.canvas.set_overlay_enabled(False)
            self.list_lines.clear()
            self.progress_bar.setValue(0)
        else:
            if current_preview_path and current_preview_path in removed_paths:
                self.queue_table.selectRow(0)
                p = self.queue_table.item(0, 0).data(Qt.UserRole)
                self.preview_image(p)

        self._fit_queue_columns_exact()
        self._update_queue_hint()

    def clear_queue(self):
        self.queue_items.clear()
        self.queue_table.setRowCount(0)
        self.canvas.clear_all()
        self.canvas.set_overlay_enabled(False)
        self.list_lines.clear()
        self.progress_bar.setValue(0)
        self._fit_queue_columns_exact()
        self._update_queue_hint()

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
        self.canvas.load_pil_image(im)
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
            path = self.queue_table.item(self.queue_table.currentRow(), 0).data(Qt.UserRole)
            item = next((i for i in self.queue_items if i.path == path), None)
            if item and item.status == STATUS_DONE:
                self.load_results(path)
            else:
                self.preview_image(path)

    def on_queue_double_click(self, row, col):
        path = self.queue_table.item(row, 0).data(Qt.UserRole)
        self.preview_image(path)

    def choose_rec_model(self):
        p, _ = QFileDialog.getOpenFileName(self, self._tr("dlg_choose_rec"), "", self._tr("dlg_filter_model"))
        if p:
            self.model_path = p
            name = os.path.basename(p)
            self.btn_rec_model.setText(f"{self._tr('dlg_choose_rec')}{name}")
            self.status_bar.showMessage(self._tr("msg_loaded_rec", name))

    def choose_seg_model(self):
        p, _ = QFileDialog.getOpenFileName(self, self._tr("dlg_choose_seg"), "", self._tr("dlg_filter_model"))
        if p:
            self.seg_model_path = p
            name = os.path.basename(p)
            self.btn_seg_model.setText(f"{self._tr('dlg_choose_seg')}{name}")
            self.status_bar.showMessage(self._tr("msg_loaded_seg", name))

    # -----------------------------
    # OCR controls
    # -----------------------------
    def start_ocr(self):
        if not self.model_path or not os.path.exists(self.model_path):
            QMessageBox.critical(self, self._tr("err_title"), self._tr("warn_need_rec"))
            return
        if not self.seg_model_path or not os.path.exists(self.seg_model_path):
            QMessageBox.critical(self, self._tr("err_title"), self._tr("warn_need_seg"))
            return

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
        self.progress_bar.setValue(0)

        paths = [t.path for t in tasks]
        job = OCRJob(
            input_paths=paths,
            recognition_model_path=self.model_path,
            segmentation_model_path=self.seg_model_path,
            device=self.device_str,
            reading_direction=self.reading_direction,
            export_format="pdf",
            export_dir=self.current_export_dir
        )

        self.worker = OCRWorker(job)
        self.worker.file_started.connect(self.on_file_started)
        self.worker.file_done.connect(self.on_file_done)
        self.worker.file_error.connect(self.on_file_error)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished_batch.connect(self.on_batch_finished)
        self.worker.failed.connect(self.on_failed)
        self.worker.device_resolved.connect(self.on_device_resolved)
        self.worker.gpu_info.connect(self.on_gpu_info)
        self.worker.start()

    def on_device_resolved(self, dev_str: str):
        self.status_bar.showMessage(self._tr("msg_using_device", dev_str))

    def on_gpu_info(self, info: str):
        self.status_bar.showMessage(self._tr("msg_detected_gpu", info))

    def reprocess_selected(self):
        if self.queue_table.currentRow() < 0:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_select_done"))
            return

        path = self.queue_table.item(self.queue_table.currentRow(), 0).data(Qt.UserRole)
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
            self.progress_bar.setValue(0)
            self.start_ocr()

    def stop_ocr(self):
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.status_bar.showMessage(self._tr("msg_stopping"))

    def on_file_started(self, path):
        item = next((i for i in self.queue_items if i.path == path), None)
        if item:
            item.status = STATUS_PROCESSING
            self._update_queue_row(path)

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
                cur_path = self.queue_table.item(self.queue_table.currentRow(), 0).data(Qt.UserRole)
                if cur_path == path:
                    self.load_results(path)

    def on_file_error(self, path, msg):
        item = next((i for i in self.queue_items if i.path == path), None)
        if item:
            item.status = STATUS_ERROR
            self._update_queue_row(path)

    def on_batch_finished(self):
        self.act_play.setEnabled(True)
        self.act_stop.setEnabled(False)
        self.status_bar.showMessage(self._tr("msg_finished"))

    def on_failed(self, msg):
        QMessageBox.critical(self, self._tr("err_title"), msg)
        self.act_play.setEnabled(True)
        self.act_stop.setEnabled(False)

    def _update_queue_row(self, path):
        for row in range(self.queue_table.rowCount()):
            item0 = self.queue_table.item(row, 0)
            if item0 and item0.data(Qt.UserRole) == path:
                status_item = self.queue_table.item(row, 1)
                task = next((i for i in self.queue_items if i.path == path), None)
                if task and status_item:
                    status_enum = task.status
                    status_icon = STATUS_ICONS[status_enum]
                    status_key = {
                        STATUS_WAITING: "status_waiting",
                        STATUS_PROCESSING: "status_processing",
                        STATUS_DONE: "status_done",
                        STATUS_ERROR: "status_error",
                    }[status_enum]
                    status_item.setText(f"{status_icon} {self._tr(status_key)}")

                    if status_enum == STATUS_DONE:
                        status_item.setForeground(QBrush(QColor("green")))
                    elif status_enum == STATUS_ERROR:
                        status_item.setForeground(QBrush(QColor("red")))
                    else:
                        status_item.setForeground(QBrush(QColor("blue")))
                break

    # -----------------------------
    # Lines + overlays
    # -----------------------------
    def _current_task(self) -> Optional[TaskItem]:
        if self.queue_table.currentRow() < 0:
            return None
        path = self.queue_table.item(self.queue_table.currentRow(), 0).data(Qt.UserRole)
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
            rv = recs.pop(row)
            rv.text = new_text
            recs.insert(target_idx, rv)
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
        text, kr_records, im, recs = task.results

        if not order or len(order) != len(recs):
            return

        try:
            new_recs = [recs[int(i)] for i in order]
        except Exception:
            return

        self._push_undo(task)
        task.edited = True
        task.results = (text, kr_records, im, new_recs)
        self._sync_ui_after_recs_change(task, keep_row=max(0, min(len(new_recs) - 1, int(current_row_after_drop))))

    def lines_context_menu(self, pos):
        item = self.list_lines.itemAt(pos)
        if item is None:
            return
        row = self.list_lines.row(item)

        menu = QMenu()
        act_up = menu.addAction(self._tr("line_menu_move_up"))
        act_down = menu.addAction(self._tr("line_menu_move_down"))
        menu.addSeparator()
        act_move_to = menu.addAction(self._tr("line_menu_move_to"))
        menu.addSeparator()
        act_del = menu.addAction(self._tr("line_menu_delete"))
        menu.addSeparator()
        act_add_above = menu.addAction(self._tr("line_menu_add_above"))
        act_add_below = menu.addAction(self._tr("line_menu_add_below"))
        menu.addSeparator()
        act_draw = menu.addAction(self._tr("line_menu_draw_box"))
        menu.addSeparator()
        act_edit_box = menu.addAction(self._tr("line_menu_edit_box"))

        chosen = menu.exec(self.list_lines.viewport().mapToGlobal(pos))
        if not chosen:
            return

        task = self._current_task()
        if not task or not task.results or task.status != STATUS_DONE:
            return

        if chosen == act_up:
            self._move_line(task, row, -1)
        elif chosen == act_down:
            self._move_line(task, row, +1)
        elif chosen == act_move_to:
            self._move_line_to_dialog(task, row)
        elif chosen == act_del:
            self._delete_line(task, row)
        elif chosen == act_add_above:
            self._add_line(task, insert_row=row)
        elif chosen == act_add_below:
            self._add_line(task, insert_row=row + 1)
        elif chosen == act_draw:
            # Draw box FOR THIS LINE (kept as-is)
            self._pending_new_line_box = False
            self._pending_box_for_row = row
            self.canvas.start_draw_box_mode()
        elif chosen == act_edit_box:
            self.show_overlay = True
            self.act_overlay.setChecked(True)
            self.refresh_preview()

    def _sync_ui_after_recs_change(self, task: TaskItem, keep_row: Optional[int] = None):
        if not task.results:
            return
        text, kr_records, im, recs = task.results

        for i, rv in enumerate(recs):
            rv.idx = i

        new_text = "\n".join([r.text for r in recs]).strip()
        task.results = (new_text, kr_records, im, recs)

        self.canvas.load_pil_image(im)
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
            value=row + 1,
            min=1,
            max=max(1, len(recs)),
            step=1
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
    # Canvas actions
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
        # NEW BEHAVIOR: drawing a new overlay box creates a NEW line at the end.
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

        # Case A: create new line at end (canvas draw)
        if self._pending_new_line_box:
            self._pending_new_line_box = False
            self._pending_box_for_row = None

            # Optional: ask for text (optional) – user can also just edit in list afterwards.
            new_txt, ok = QInputDialog.getText(self, self._tr("new_line_from_box_title"), self._tr("new_line_from_box_label"))
            if not ok:
                new_txt = ""
            new_txt = (new_txt or "").strip()

            self._push_undo(task)
            recs.append(RecordView(len(recs), new_txt, (x0, y0, x1, y1)))
            task.edited = True
            self._sync_ui_after_recs_change(task, keep_row=len(recs) - 1)
            self.list_lines.setFocus()
            return

        # Case B: draw box for a specific existing row (line context menu)
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
    # Overlay toggle
    # -----------------------------
    def _on_overlay_toggled(self, checked):
        self.show_overlay = checked
        self.refresh_preview()

    # -----------------------------
    # Export
    # -----------------------------
    def export_flow(self, fmt: str):
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

        self._export_batch(items, fmt)

    def _export_single_interactive(self, item: TaskItem, fmt: str):
        base_name = os.path.splitext(item.display_name)[0]
        base_dir = self.current_export_dir or os.path.dirname(item.path)

        filters = {"txt": "Text (*.txt)", "csv": "CSV (*.csv)", "json": "JSON (*.json)",
                   "alto": "XML (*.xml)", "hocr": "HTML (*.html)", "pdf": "PDF (*.pdf)"}

        dest_path, _ = QFileDialog.getSaveFileName(
            self, self._tr("dlg_save"),
            os.path.join(base_dir, base_name),
            filters.get(fmt, "All (*.*)")
        )
        if not dest_path:
            return
        if not dest_path.lower().endswith(f".{fmt}"):
            dest_path += f".{fmt}"

        self._render_file(dest_path, fmt, item)
        self.status_bar.showMessage(self._tr("msg_exported", os.path.basename(dest_path)))

    def _export_batch(self, items: List[TaskItem], fmt: str):
        folder = QFileDialog.getExistingDirectory(self, self._tr("export_choose_folder"), self.current_export_dir or "")
        if not folder:
            return
        self.current_export_dir = folder

        for it in items:
            base_name = os.path.splitext(it.display_name)[0]
            dest_path = os.path.join(folder, f"{base_name}.{fmt}")
            self._render_file(dest_path, fmt, it)

        self.status_bar.showMessage(self._tr("msg_exported", folder))

    def _render_file(self, path: str, fmt: str, item: TaskItem):
        if not item.results:
            return

        text, kr_records, pil_image, record_views = item.results

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
            xml = serialization.serialize(kr_records, image_name=img_name, image_size=pil_image.size, template=fmt)
            with open(path, "w", encoding="utf-8") as f:
                f.write(xml)
            return

        if fmt == "pdf":
            width, height = pil_image.size
            c = pdf_canvas.Canvas(path, pagesize=(width, height))
            c.drawImage(ImageReader(pil_image), 0, 0, width=width, height=height)

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

            c.save()
            return

    # -----------------------------
    # Keyboard focus handling
    # -----------------------------
    def keyPressEvent(self, event):
        if self.focusWidget() is self.list_lines and event.key() == Qt.Key_Delete:
            self._delete_current_line_via_key()
            event.accept()
            return

        if event.key() == Qt.Key_Delete and self.focusWidget() is self.queue_table:
            self.delete_selected_queue_items()
            event.accept()
            return

        super().keyPressEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()