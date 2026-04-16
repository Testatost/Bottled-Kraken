"""Mixin-Methoden für den Bildbearbeitungsdialog."""
from ..shared import *
from ..dialogs import *
from .common import ImageEditSettings, WhiteBorderDialog
from .canvas import ImageEditCanvas

class ImageEditDialogSetupMixin:
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
        self._tr = tr if callable(tr) else translation.make_tr("de")
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
        self.btn_erase_clear.clicked.connect(self._commit_erase_selection)
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
