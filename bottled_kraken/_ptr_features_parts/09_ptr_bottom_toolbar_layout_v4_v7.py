def _ptr_rebuild_secondary_button_rows_v4(window):
    # Die zusätzlichen PTR-Buttons werden in dieser Version nicht mehr aufgebaut.
    return

_ptr_prev_mainwindow_init_v4 = MainWindow.__init__

_ptr_prev_mainwindow_retranslate_v4 = MainWindow.retranslate_ui

def _ptr_mainwindow_init_wrapper_v4(self, *args, **kwargs):
    _ptr_prev_mainwindow_init_v4(self, *args, **kwargs)
    _ptr_remove_toolbar_feature_buttons_v4(self)
    _ptr_remove_secondary_feature_buttons_v4(self)

def _ptr_mainwindow_retranslate_ui_wrapper_v4(self, *args, **kwargs):
    _ptr_prev_mainwindow_retranslate_v4(self, *args, **kwargs)
    try:
        self.ptr_update_feature_texts()
    except Exception:
        pass
    _ptr_remove_toolbar_feature_buttons_v4(self)
    _ptr_remove_secondary_feature_buttons_v4(self)

def _ptr_install_feature_actions_v4(self):
    if getattr(self, "_ptr_feature_actions_installed", False):
        return
    self._ptr_feature_actions_installed = True
    self.act_ptr_multi_ocr = QAction(_ptr_ui_tr(self, "ptr_multi_ocr_title"), self)
    self.act_ptr_multi_ocr.triggered.connect(self.ptr_start_multi_ocr)
    self.act_ptr_ai_tools = QAction(_ptr_ui_tr(self, "ptr_ai_tools_title"), self)
    self.act_ptr_ai_tools.triggered.connect(self.ptr_open_ai_tools_for_current_task)
    self.act_ptr_multi_reopen = QAction(_ptr_ui_tr(self, "ptr_ai_reopen"), self)
    self.act_ptr_multi_reopen.triggered.connect(self.ptr_reopen_multi_followup)
    if hasattr(self, "models_menu") and self.models_menu is not None:
        self.models_menu.addSeparator()
        self.models_menu.addAction(self.act_ptr_multi_ocr)
        self.models_menu.addAction(self.act_ptr_multi_reopen)
    if hasattr(self, "revision_models_menu") and self.revision_models_menu is not None:
        self.revision_models_menu.addSeparator()
        self.revision_models_menu.addAction(self.act_ptr_ai_tools)
    self.ptr_update_feature_texts()
    _ptr_remove_toolbar_feature_buttons_v4(self)
    _ptr_remove_secondary_feature_buttons_v4(self)

_ptr_rebuild_secondary_button_rows = _ptr_rebuild_secondary_button_rows_v4

MainWindow.__init__ = _ptr_mainwindow_init_wrapper_v4

MainWindow.retranslate_ui = _ptr_mainwindow_retranslate_ui_wrapper_v4

MainWindow._ptr_install_feature_actions = _ptr_install_feature_actions_v4

def _ptr_remove_bottom_feature_row_container_v7(window):
    for attr in ("_ptr_bottom_feature_row_container_v5", "_ptr_bottom_rows_container_v7"):
        container = getattr(window, attr, None)
        if container is None:
            continue
        try:
            parent = container.parentWidget()
            if parent is not None and parent.layout() is not None:
                parent.layout().removeWidget(container)
        except Exception:
            pass
        try:
            container.hide()
        except Exception:
            pass
        try:
            container.setParent(None)
            container.deleteLater()
        except Exception:
            pass
        try:
            delattr(window, attr)
        except Exception:
            pass
    try:
        window._ptr_bottom_feature_row_built_v5 = False
    except Exception:
        pass
    try:
        window._ptr_bottom_rows_built_v7 = False
    except Exception:
        pass

def _ptr_rebuild_secondary_feature_rows_v7(window):
    if getattr(window, "_ptr_bottom_rows_built_v7", False):
        try:
            _ptr_update_feature_texts_v2(window)
        except Exception:
            pass
        try:
            _ptr_apply_new_button_icons(window)
        except Exception:
            pass
        try:
            _ptr_remove_toolbar_feature_buttons_v4(window)
        except Exception:
            pass
        return
    if not hasattr(window, "splitter") or window.splitter.count() < 2:
        return
    right_widget = window.splitter.widget(1)
    right_layout = right_widget.layout() if right_widget is not None else None
    if right_layout is None:
        return
    _ptr_remove_toolbar_feature_buttons_v4(window)
    _ptr_remove_bottom_feature_row_container_v7(window)
    if not hasattr(window, "btn_ptr_multi_ocr_bottom"):
        window.btn_ptr_multi_ocr_bottom = QToolButton()
        window.btn_ptr_multi_ocr_bottom.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        window.btn_ptr_multi_ocr_bottom.clicked.connect(window.ptr_start_multi_ocr)
    if not hasattr(window, "btn_ptr_openrouter_ai_bottom"):
        window.btn_ptr_openrouter_ai_bottom = QToolButton()
        window.btn_ptr_openrouter_ai_bottom.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        window.btn_ptr_openrouter_ai_bottom.clicked.connect(window.ptr_open_ai_tools_for_current_task)
    old_lines_layout = None
    old_index = None
    existing_buttons = [
        getattr(window, "btn_import_lines", None),
        getattr(window, "btn_voice_fill", None),
        getattr(window, "btn_ai_revise_bottom", None),
        getattr(window, "btn_line_search", None),
    ]
    for i in range(right_layout.count()):
        item = right_layout.itemAt(i)
        lay = item.layout() if item is not None else None
        if lay is None:
            continue
        try:
            if any(btn is not None and lay.indexOf(btn) != -1 for btn in existing_buttons):
                old_lines_layout = lay
                old_index = i
                break
        except Exception:
            continue
    container = QWidget(right_widget)
    outer = QVBoxLayout(container)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(6)
    row1 = QHBoxLayout()
    row1.setContentsMargins(0, 0, 0, 0)
    row1.setSpacing(6)
    row2 = QHBoxLayout()
    row2.setContentsMargins(0, 0, 0, 0)
    row2.setSpacing(6)
    row1.addWidget(window.btn_ptr_multi_ocr_bottom)
    row1.addWidget(window.btn_ai_revise_bottom)
    row1.addWidget(window.btn_ptr_openrouter_ai_bottom)
    row1.addStretch(1)
    row2.addWidget(window.btn_import_lines)
    row2.addWidget(window.btn_voice_fill)
    row2.addWidget(window.btn_line_search)
    row2.addStretch(1)
    outer.addLayout(row1)
    outer.addLayout(row2)
    if old_lines_layout is not None:
        try:
            old_lines_layout.setContentsMargins(0, 0, 0, 0)
            old_lines_layout.setSpacing(0)
        except Exception:
            pass
        insert_index = old_index if isinstance(old_index, int) else max(0, right_layout.count() - 1)
        right_layout.insertWidget(insert_index, container)
    else:
        right_layout.addWidget(container)
    window._ptr_bottom_rows_built_v7 = True
    window._ptr_bottom_rows_container_v7 = container
    try:
        _ptr_update_feature_texts_v2(window)
    except Exception:
        pass
    try:
        _ptr_apply_new_button_icons(window)
    except Exception:
        pass

def _ptr_mainwindow_init_wrapper_v7(self, *args, **kwargs):
    _ptr_prev_mainwindow_init_v4(self, *args, **kwargs)
    _ptr_remove_toolbar_feature_buttons_v4(self)
    _ptr_rebuild_secondary_feature_rows_v7(self)

def _ptr_mainwindow_retranslate_ui_wrapper_v7(self, *args, **kwargs):
    _ptr_prev_mainwindow_retranslate_v4(self, *args, **kwargs)
    try:
        self.ptr_update_feature_texts()
    except Exception:
        pass
    _ptr_remove_toolbar_feature_buttons_v4(self)
    _ptr_rebuild_secondary_feature_rows_v7(self)

def _ptr_install_feature_actions_v7(self):
    if getattr(self, "_ptr_feature_actions_installed", False):
        return
    self._ptr_feature_actions_installed = True
    self.act_ptr_multi_ocr = QAction(_ptr_ui_tr(self, "ptr_multi_ocr_title"), self)
    self.act_ptr_multi_ocr.triggered.connect(self.ptr_start_multi_ocr)
    self.act_ptr_ai_tools = QAction(_ptr_ui_tr(self, "ptr_ai_tools_title"), self)
    self.act_ptr_ai_tools.triggered.connect(self.ptr_open_ai_tools_for_current_task)
    self.act_ptr_multi_reopen = QAction(_ptr_ui_tr(self, "ptr_ai_reopen"), self)
    self.act_ptr_multi_reopen.triggered.connect(self.ptr_reopen_multi_followup)
    if hasattr(self, "models_menu") and self.models_menu is not None:
        self.models_menu.addSeparator()
        self.models_menu.addAction(self.act_ptr_multi_ocr)
        self.models_menu.addAction(self.act_ptr_multi_reopen)
    if hasattr(self, "revision_models_menu") and self.revision_models_menu is not None:
        self.revision_models_menu.addSeparator()
        self.revision_models_menu.addAction(self.act_ptr_ai_tools)
    self.ptr_update_feature_texts()
    _ptr_remove_toolbar_feature_buttons_v4(self)
    _ptr_rebuild_secondary_feature_rows_v7(self)

MainWindow.__init__ = _ptr_mainwindow_init_wrapper_v7

MainWindow.retranslate_ui = _ptr_mainwindow_retranslate_ui_wrapper_v7

MainWindow._ptr_install_feature_actions = _ptr_install_feature_actions_v7

__all__ = [name for name in globals() if not name.startswith("__")]
