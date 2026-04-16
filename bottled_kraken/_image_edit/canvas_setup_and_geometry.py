"""Mixin-Methoden für die Bildbearbeitungs-Canvas."""
from ..shared import *
from .common import ImageEditSeparator

class ImageEditCanvasSetupMixin:
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
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._pan_active = False
        self._pan_start_widget = QPointF()
        self._pan_start_x = 0.0
        self._pan_start_y = 0.0

    def set_image(self, img: Optional[Image.Image], reset_zoom: bool = True):
        self.base_image = img
        if reset_zoom:
            self.zoom = 1.0
            self._pan_x = 0.0
            self._pan_y = 0.0
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

    def _pan_limits(self) -> Tuple[float, float]:
        if self.view_pixmap is None:
            return 0.0, 0.0
        max_x = max(0.0, (float(self.view_pixmap.width()) - float(self.width())) / 2.0)
        max_y = max(0.0, (float(self.view_pixmap.height()) - float(self.height())) / 2.0)
        return max_x, max_y

    def _clamp_pan(self):
        if self.view_pixmap is None or self.zoom <= 1.001:
            self._pan_x = 0.0
            self._pan_y = 0.0
            return
        max_x, max_y = self._pan_limits()
        self._pan_x = max(-max_x, min(max_x, float(self._pan_x)))
        self._pan_y = max(-max_y, min(max_y, float(self._pan_y)))

    def _can_pan_with_alt(self) -> bool:
        return self.view_pixmap is not None and self.zoom > 1.001

    def _update_image_offset(self):
        if self.view_pixmap is None:
            self._img_offset_x = 0.0
            self._img_offset_y = 0.0
            return
        self._clamp_pan()
        base_x = max(0.0, (self.width() - self.view_pixmap.width()) / 2.0)
        base_y = max(0.0, (self.height() - self.view_pixmap.height()) / 2.0)
        self._img_offset_x = base_x + self._pan_x
        self._img_offset_y = base_y + self._pan_y

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
