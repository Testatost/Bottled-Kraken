"""Hauptfenster der Anwendung."""

from .shared import *
from .ui_components import *
from .workers import *
from .dialogs import *
from .image_edit import *

from ._main_window.initialization_and_shutdown import MainWindowInitializationAndShutdownMixin
from ._main_window.whisper_setup_and_model_selection import MainWindowWhisperSetupAndModelSelectionMixin
from ._main_window.voice_input_selection_and_ai_selected_lines import MainWindowVoiceInputSelectionAndAiSelectedLinesMixin
from ._main_window.ai_server_urls_and_model_selection import MainWindowAiServerUrlsAndModelSelectionMixin
from ._main_window.project_persistence_and_queue_selection import MainWindowProjectPersistenceAndQueueSelectionMixin
from ._main_window.toolbar_icons_and_local_server_models import MainWindowToolbarIconsAndLocalServerModelsMixin
from ._main_window.undo_voice_fill_and_ai_revision import MainWindowUndoVoiceFillAndAiRevisionMixin
from ._main_window.ui_build import MainWindowUiBuildMixin
from ._main_window.ai_batch_callbacks import MainWindowAiBatchCallbacksMixin
from ._main_window.menu_setup_and_queue_headers import MainWindowMenuSetupAndQueueHeadersMixin
from ._main_window.theme_language_and_reading_direction import MainWindowThemeLanguageAndReadingDirectionMixin
from ._main_window.hardware_status_and_file_drop import MainWindowHardwareStatusAndFileDropMixin
from ._main_window.queue_context_preview_and_model_loading import MainWindowQueueContextPreviewAndModelLoadingMixin
from ._main_window.import_lines_and_ocr_batch import MainWindowImportLinesAndOcrBatchMixin
from ._main_window.line_editing_and_overlay_sync import MainWindowLineEditingAndOverlaySyncMixin
from ._main_window.export_rendering_and_paths import MainWindowExportRenderingAndPathsMixin
from ._main_window.whisper_download_help_and_image_edit_queue import MainWindowWhisperDownloadHelpAndImageEditQueueMixin
from ._main_window.image_edit_application_and_close import MainWindowImageEditApplicationAndCloseMixin


class MainWindow(
    MainWindowInitializationAndShutdownMixin,
    MainWindowWhisperSetupAndModelSelectionMixin,
    MainWindowVoiceInputSelectionAndAiSelectedLinesMixin,
    MainWindowAiServerUrlsAndModelSelectionMixin,
    MainWindowProjectPersistenceAndQueueSelectionMixin,
    MainWindowToolbarIconsAndLocalServerModelsMixin,
    MainWindowUndoVoiceFillAndAiRevisionMixin,
    MainWindowUiBuildMixin,
    MainWindowAiBatchCallbacksMixin,
    MainWindowMenuSetupAndQueueHeadersMixin,
    MainWindowThemeLanguageAndReadingDirectionMixin,
    MainWindowHardwareStatusAndFileDropMixin,
    MainWindowQueueContextPreviewAndModelLoadingMixin,
    MainWindowImportLinesAndOcrBatchMixin,
    MainWindowLineEditingAndOverlaySyncMixin,
    MainWindowExportRenderingAndPathsMixin,
    MainWindowWhisperDownloadHelpAndImageEditQueueMixin,
    MainWindowImageEditApplicationAndCloseMixin,
    QMainWindow,
):
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
        # Harte Obergrenze für die normale LM-Überarbeitung.
        # Lokale JSON-Erzeugung und LM OCR setzen weiterhin eigene Mindestwerte.
        self.ai_max_tokens = 1200
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
