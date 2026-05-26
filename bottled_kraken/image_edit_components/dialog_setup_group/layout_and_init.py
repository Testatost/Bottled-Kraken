"""Mixin-Methoden für den Bildbearbeitungsdialog."""
from ...shared import *
from ...dialogs import *
from ..common import ImageEditSeparator, ImageEditSettings, WhiteBorderDialog
from ..canvas import ImageEditCanvas
from PySide6.QtGui import QPainterPath

class ImageEditDialogLayoutAndInitMixin:
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
            self._tr = tr if callable(tr) else translation.make_tr(translation.DEFAULT_LANGUAGE)
            self.setWindowTitle(self._tr("image_edit_title", title))
            self.resize(1500, 960)
            self.setWindowState(self.windowState() | Qt.WindowMaximized)
            theme = getattr(parent, "current_theme", "bright")
            self._preview_tool_theme = theme
            self.setStyleSheet(_image_edit_dialog_qss(theme))
            self.original_image = image.convert("RGB")
            self.color_mode = "RGB"
            self.contrast_enabled = False
            self.contrast_level = 2.2
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
            self.shortcut_erase_commit.activated.connect(self._delete_selected_crop_or_erase)
            self.shortcut_erase_undo = QShortcut(QKeySequence("Ctrl+Alt+Z"), self)
            self.shortcut_erase_undo.setContext(Qt.WidgetWithChildrenShortcut)
            self.shortcut_erase_undo.activated.connect(self._undo_erase_commit)
            self.shortcut_transform_ctrl_t = QShortcut(QKeySequence("Ctrl+T"), self)
            self.shortcut_transform_ctrl_t.setContext(Qt.WidgetWithChildrenShortcut)
            self.shortcut_transform_ctrl_t.activated.connect(lambda: self._toggle_free_transform(True))
            self.shortcut_transform_apply_enter = QShortcut(QKeySequence(Qt.Key_Return), self)
            self.shortcut_transform_apply_enter.setContext(Qt.WidgetWithChildrenShortcut)
            self.shortcut_transform_apply_enter.activated.connect(self._enter_transform_or_apply)
            self.shortcut_transform_apply_enter2 = QShortcut(QKeySequence(Qt.Key_Enter), self)
            self.shortcut_transform_apply_enter2.setContext(Qt.WidgetWithChildrenShortcut)
            self.shortcut_transform_apply_enter2.activated.connect(self._enter_transform_or_apply)
            self.shortcut_transform_cancel_esc = QShortcut(QKeySequence(Qt.Key_Escape), self)
            self.shortcut_transform_cancel_esc.setContext(Qt.WidgetWithChildrenShortcut)
            self.shortcut_transform_cancel_esc.activated.connect(self._clear_selection)
            self.shortcut_tf_scale = QShortcut(QKeySequence("Ctrl+S"), self)
            self.shortcut_tf_scale.setContext(Qt.WidgetWithChildrenShortcut)
            self.shortcut_tf_scale.activated.connect(lambda: self._activate_or_start_transform_mode("scale"))
            self.shortcut_tf_rotate = QShortcut(QKeySequence("Ctrl+D"), self)
            self.shortcut_tf_rotate.setContext(Qt.WidgetWithChildrenShortcut)
            self.shortcut_tf_rotate.activated.connect(lambda: self._activate_or_start_transform_mode("rotate"))
            self.shortcut_tf_skew = QShortcut(QKeySequence("Ctrl+N"), self)
            self.shortcut_tf_skew.setContext(Qt.WidgetWithChildrenShortcut)
            self.shortcut_tf_skew.activated.connect(lambda: self._activate_or_start_transform_mode("skew"))
            self.shortcut_tf_persp = QShortcut(QKeySequence("Ctrl+P"), self)
            self.shortcut_tf_persp.setContext(Qt.WidgetWithChildrenShortcut)
            self.shortcut_tf_persp.activated.connect(lambda: self._activate_or_start_transform_mode("perspective"))
            self.shortcut_tf_warp = QShortcut(QKeySequence("Ctrl+V"), self)
            self.shortcut_tf_warp.setContext(Qt.WidgetWithChildrenShortcut)
            self.shortcut_tf_warp.activated.connect(lambda: self._activate_or_start_transform_mode("warp"))
            self.shortcut_undo = QShortcut(QKeySequence("Ctrl+Z"), self)
            self.shortcut_undo.setContext(Qt.ApplicationShortcut)
            self.shortcut_undo.activated.connect(self._undo_action)
            self.shortcut_redo = QShortcut(QKeySequence("Ctrl+Y"), self)
            self.shortcut_redo.setContext(Qt.ApplicationShortcut)
            self.shortcut_redo.activated.connect(self._redo_action)

            self.btn_preview_select = self._make_preview_tool_button("select", "image_edit_preview_tool_select_tip")
            self.btn_preview_pan = self._make_preview_tool_button("pan", "image_edit_preview_tool_pan_tip")
            self.btn_preview_select.clicked.connect(lambda: self._set_preview_tool_mode("select"))
            self.btn_preview_pan.clicked.connect(lambda: self._set_preview_tool_mode("pan"))
            self._set_preview_tool_mode("select")

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
            self.grid_slider.setMinimumWidth(220)
            self.grid_slider.setMaximumWidth(360)
            self.grid_slider.setFixedHeight(22)
            self.grid_slider.setEnabled(False)
            self.grid_slider.setVisible(False)
            self.lbl_grid_size = QLabel(self._tr("image_edit_grid_label"))
            self.lbl_grid_size.setMinimumWidth(120)
            self.lbl_grid_size.setEnabled(False)
            self.lbl_grid_size.setVisible(False)

            self.chk_crop = QPushButton(self._tr("image_edit_crop"))
            self.chk_crop.setCheckable(True)
            self.chk_crop.toggled.connect(self._toggle_crop)
            self.chk_crop.clicked.connect(self._on_crop_button_clicked)
            self.chk_selection = QCheckBox(self._tr("image_edit_selection_area"))
            self.chk_selection.toggled.connect(self._toggle_selection)
            self.chk_split = QPushButton(self._tr("image_edit_separator"))
            self.chk_split.setCheckable(True)
            self.chk_split.toggled.connect(self._toggle_split)
            self.chk_gray = QPushButton(self._tr("image_edit_gray"))
            self.chk_gray.setCheckable(True)
            self.chk_gray.clicked.connect(self._on_gray_button_clicked)
            self.chk_contrast = QPushButton(self._tr("image_edit_contrast"))
            self.chk_contrast.setCheckable(True)
            self.chk_contrast.clicked.connect(self._on_contrast_button_clicked)

            self.contrast_controls_widget = QWidget()
            contrast_controls_layout = QHBoxLayout(self.contrast_controls_widget)
            contrast_controls_layout.setContentsMargins(0, 0, 0, 0)
            contrast_controls_layout.setSpacing(8)
            self.lbl_contrast_strength = QLabel()
            self.lbl_contrast_strength.setMinimumWidth(150)
            self.contrast_slider = QSlider(Qt.Horizontal)
            self.contrast_slider.setRange(0, 100)
            self.contrast_slider.setValue(40)
            self.contrast_slider.setMinimumWidth(240)
            self.contrast_slider.setMaximumWidth(460)
            self.contrast_slider.setFixedHeight(22)
            self.contrast_slider.valueChanged.connect(self._on_contrast_slider_changed)
            self.contrast_slider.sliderPressed.connect(self._on_contrast_slider_pressed)
            self.contrast_slider.sliderReleased.connect(self._on_contrast_slider_released)
            self._contrast_preview_pending = False
            self._contrast_preview_timer = QTimer(self)
            self._contrast_preview_timer.setSingleShot(True)
            self._contrast_preview_timer.setInterval(140)
            self._contrast_preview_timer.timeout.connect(self._apply_pending_contrast_preview)
            contrast_controls_layout.addStretch(1)
            contrast_controls_layout.addWidget(self.lbl_contrast_strength)
            contrast_controls_layout.addWidget(self.contrast_slider, 0)
            contrast_controls_layout.addStretch(1)
            self.contrast_controls_widget.setVisible(False)

            self.btn_erase_rect = QPushButton(self._tr("image_edit_erase_rect"))
            self.btn_erase_rect.setCheckable(True)
            self.btn_erase_rect.toggled.connect(lambda checked: self._toggle_erase_mode("rect", checked))
            self.btn_erase_ellipse = QPushButton(self._tr("image_edit_erase_ellipse"))
            self.btn_erase_ellipse.setCheckable(True)
            self.btn_erase_ellipse.toggled.connect(lambda checked: self._toggle_erase_mode("ellipse", checked))
            self.btn_erase_clear = QPushButton(self._tr("image_edit_erase_clear"))
            self.btn_erase_clear.clicked.connect(self._commit_erase_selection)

            btn_rot_left = QPushButton("↺ 90°")
            btn_rot_left.clicked.connect(lambda: self._rotate_by(-90))
            btn_rot_right = QPushButton("↻ 90°")
            btn_rot_right.clicked.connect(lambda: self._rotate_by(90))
            btn_flip_h = QPushButton(self._tr("image_edit_flip_horizontal"))
            btn_flip_h.clicked.connect(self._flip_horizontal)
            btn_flip_v = QPushButton(self._tr("image_edit_flip_vertical"))
            btn_flip_v.clicked.connect(self._flip_vertical)
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
            self.btn_rect_selection = QPushButton(self._tr("image_edit_selection_rect"))
            self.btn_rect_selection.setCheckable(True)
            self.btn_rect_selection.setChecked(True)
            self.btn_rect_selection.clicked.connect(lambda checked: self._set_selection_draw_mode("rect"))
            self.btn_ellipse_selection = QPushButton(self._tr("image_edit_selection_ellipse"))
            self.btn_ellipse_selection.setCheckable(True)
            self.btn_ellipse_selection.clicked.connect(lambda checked: self._set_selection_draw_mode("ellipse" if checked else "rect"))
            self.btn_freehand_selection = QPushButton(self._tr("image_edit_selection_freehand"))
            self.btn_freehand_selection.setCheckable(True)
            self.btn_freehand_selection.clicked.connect(lambda checked: self._set_selection_draw_mode("freehand" if checked else "rect"))
            self.btn_polygon_selection = QPushButton(self._tr("image_edit_selection_polygon"))
            self.btn_polygon_selection.setCheckable(True)
            self.btn_polygon_selection.clicked.connect(lambda checked: self._set_selection_draw_mode("polygon" if checked else "rect"))
            self.btn_apply_selected = QPushButton(self._tr("image_edit_apply_selected"))
            self.btn_apply_selected.clicked.connect(self._apply_selected)
            self.btn_apply_all = QPushButton(self._tr("image_edit_apply_all"))
            self.btn_apply_all.clicked.connect(self._apply_all)

            self.btn_crop_tool = self._make_sidebar_button("crop", self._tr("image_edit_crop"))
            self.btn_crop_tool.clicked.connect(lambda: self.chk_crop.setChecked(not self.chk_crop.isChecked()))
            self.btn_transform = QPushButton(self._tr("image_edit_menu_free_transform"))
            self.btn_transform.setCheckable(True)
            self.btn_transform.clicked.connect(self._toggle_free_transform)
            self.btn_split_tool = self._make_sidebar_button("split", self._tr("image_edit_separator"))
            self.btn_split_tool.clicked.connect(lambda: self.chk_split.setChecked(not self.chk_split.isChecked()))
            self.btn_erase_tool = self._make_sidebar_button("erase", self._tr("image_edit_erase_rect"))
            self.btn_erase_tool.clicked.connect(lambda: self.btn_erase_rect.setChecked(not self.btn_erase_rect.isChecked()))
            self.btn_hand_tool = self._make_sidebar_button("pan", self._tr("image_edit_preview_tool_pan_tip"))
            self.btn_hand_tool.clicked.connect(lambda: self._set_preview_tool_mode("pan"))
            self.btn_select_tool = self._make_sidebar_button("select", self._tr("image_edit_preview_tool_select_tip"))
            self.btn_select_tool.clicked.connect(lambda: self._set_preview_tool_mode("select"))

            self.btn_tf_scale = QPushButton(self._tr("image_edit_transform_mode_scale"))
            self.btn_tf_scale.setCheckable(True)
            self.btn_tf_scale.clicked.connect(lambda: self._set_transform_mode("scale"))
            self.btn_tf_rotate = QPushButton(self._tr("image_edit_transform_mode_rotate"))
            self.btn_tf_rotate.setCheckable(True)
            self.btn_tf_rotate.clicked.connect(lambda: self._set_transform_mode("rotate"))
            self.btn_tf_skew = QPushButton(self._tr("image_edit_transform_mode_skew"))
            self.btn_tf_skew.setCheckable(True)
            self.btn_tf_skew.clicked.connect(lambda: self._set_transform_mode("skew"))
            self.btn_tf_persp = QPushButton(self._tr("image_edit_transform_mode_perspective"))
            self.btn_tf_persp.setCheckable(True)
            self.btn_tf_persp.clicked.connect(lambda: self._set_transform_mode("perspective"))
            self.btn_tf_warp = QPushButton(self._tr("image_edit_transform_mode_warp"))
            self.btn_tf_warp.setCheckable(True)
            self.btn_tf_warp.clicked.connect(lambda: self._set_transform_mode("warp"))
            self.btn_transform_apply = QPushButton(self._tr("image_edit_menu_transform_apply"))
            self.btn_transform_apply.clicked.connect(self._apply_transform)
            self.btn_transform_cancel = QPushButton(self._tr("image_edit_menu_transform_cancel"))
            self.btn_transform_cancel.clicked.connect(self._cancel_transform)
            self.lbl_transform_mode = QLabel(self._tr("image_edit_transform_inactive"))

            root = QVBoxLayout(self)
            root.setContentsMargins(8, 8, 8, 8)
            root.setSpacing(6)

            options_row = QHBoxLayout()
            for widget in (self.btn_preview_select, self.btn_preview_pan, self.btn_grid, self.btn_rotate_mode, btn_rot_left, btn_rot_right, btn_rot_reset, btn_flip_h, btn_flip_v):
                options_row.addWidget(widget)
            options_row.addSpacing(12)
            for widget in (self.chk_crop, self.chk_split, self.chk_smart_split, self.chk_gray, self.chk_contrast):
                options_row.addWidget(widget)
            options_row.addStretch(1)
            options_row.addWidget(self.btn_border, 0, Qt.AlignRight)
            root.addLayout(options_row)

            transform_row = QHBoxLayout()
            transform_row.addWidget(self.btn_transform)
            for widget in (self.btn_tf_scale, self.btn_tf_rotate, self.btn_tf_skew, self.btn_tf_persp, self.btn_tf_warp):
                transform_row.addWidget(widget)
            transform_row.addSpacing(10)
            transform_row.addWidget(self.btn_transform_apply)
            transform_row.addWidget(self.btn_transform_cancel)
            transform_row.addStretch(1)
            transform_row.addWidget(self.btn_rect_selection, 0, Qt.AlignRight)
            transform_row.addWidget(self.btn_ellipse_selection, 0, Qt.AlignRight)
            transform_row.addWidget(self.btn_freehand_selection, 0, Qt.AlignRight)
            transform_row.addWidget(self.btn_polygon_selection, 0, Qt.AlignRight)
            root.addLayout(transform_row)

            body = QHBoxLayout()
            body.setSpacing(8)
            # Keine linke Photoshop-Symbolleiste mehr: die Werkzeuge liegen oben in
            # der Options-/Transformationsleiste. Die folgenden Buttons bleiben als
            # Attribute erhalten, werden aber nicht ins Layout eingefügt.
            for _btn in (
                self.btn_select_tool,
                self.btn_hand_tool,
                self.btn_crop_tool,
                self.btn_split_tool,
                self.btn_erase_tool,
            ):
                _btn.hide()

            center = QVBoxLayout()
            center.addWidget(self.canvas, 1)
            for _erase_btn in (self.btn_erase_rect, self.btn_erase_ellipse, self.btn_erase_clear):
                _erase_btn.hide()
            body.addLayout(center, 1)
            root.addLayout(body, 1)

            bottom = QHBoxLayout()
            bottom.addWidget(self.btn_prev)
            bottom.addWidget(self.btn_next)
            bottom.addStretch(1)
            bottom.addWidget(self.lbl_grid_size, 0, Qt.AlignCenter)
            bottom.addWidget(self.grid_slider, 0, Qt.AlignCenter)
            bottom.addStretch(1)
            bottom.addWidget(self.btn_apply_selected)
            bottom.addWidget(self.btn_apply_all)
            bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            bb.button(QDialogButtonBox.Ok).setText(self._tr("dlg_box_apply"))
            bb.button(QDialogButtonBox.Cancel).setText(self._tr("btn_cancel"))
            bb.accepted.connect(self._accept_dialog)
            bb.rejected.connect(self.reject)
            root.addLayout(bottom)
            root.addWidget(bb)

            self.gray_level = 0.0
            self.gray_enabled = False
            self._history_undo = []
            self._history_redo = []
            self._history_restoring = False
            self.chk_selection.setChecked(True)
            self.chk_selection.hide()
            self.canvas.show_selection = True
            self.canvas.selection_rect = None
            self._refresh_preview(reset_zoom=True)
            self.canvas.selection_rect = None
            self.canvas.show_selection = True
            self._sync_transform_mode_buttons()
            self._history_push()
            self.canvas.setFocus()
            QTimer.singleShot(0, self.showMaximized)
