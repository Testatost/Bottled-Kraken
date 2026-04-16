"""Mixin für MainWindow: UI-Aufbau."""
from ..shared import *
from ..ui_components import *
from ..workers import *
from ..dialogs import *
from ..image_edit import *

class MainWindowUiBuildMixin:
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
