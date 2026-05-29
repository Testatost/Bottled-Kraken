from bottled_kraken.common import (
    Image,
    List,
    Optional,
    QCursor,
    QPixmap,
    QPointF,
    QRectF,
    QSizePolicy,
    Qt,
    pil_to_qpixmap,
)
from bottled_kraken._image_edit.common import ImageEditSeparator
from PySide6.QtGui import QPolygonF
class ImageEditCanvasLifecycleMixin:
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
            self.crop_rects: List[QRectF] = []
            self.selected_crop_index: int = -1
            self.show_selection = False
            self.selection_rect: Optional[QRectF] = None
            self.selection_polygon: Optional[List[QPointF]] = None
            self.selection_draw_mode = "rect"
            self._selection_point_drag_index = -1
            self._freehand_points: List[QPointF] = []
            self.separator: Optional[ImageEditSeparator] = None
            self.show_erase = False
            self.erase_shape = ""
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
            self._tool_mode = "select"
            self.free_transform_active = False
            self.transform_mode = "scale"
            self.transform_src_rect: Optional[QRectF] = None
            self.transform_src_polygon: Optional[List[QPointF]] = None
            self.transform_quad: Optional[List[QPointF]] = None
            self.transform_source_order: List[int] = [0, 1, 2, 3]
            self.transform_rotate_angle = 0.0
            self.transform_warp_x = 0.0
            self.transform_warp_y = 0.0
            self.transform_warp_grid = None
            self._transform_drag_index = -1
            self._transform_drag_points = None
            self._transform_warp_start_grid = None
            self._transform_warp_free_start = None
            self._transform_warp_free_weights = None
            self._transform_rotate_start_angle = 0.0
            self._transform_rotate_center = QPointF()
            self._transform_rotate_points = None
            self._transform_scale_axis_lock = None
        def set_tool_mode(self, mode: str):
            mode = "pan" if str(mode or "").lower() == "pan" else "select"
            if getattr(self, "_tool_mode", "select") == mode:
                self._update_cursor(self._widget_to_image(self.mapFromGlobal(QCursor.pos())))
                return
            if self.drag_mode == "pan":
                self._pan_active = False
            self.drag_mode = None
            self._tool_mode = mode
            self._update_cursor(self._widget_to_image(self.mapFromGlobal(QCursor.pos())))
            self.update()
        def tool_mode(self) -> str:
            return getattr(self, "_tool_mode", "select")
        def _pan_tool_active(self) -> bool:
            return self.tool_mode() == "pan"
        def _event_requests_pan(self, event) -> bool:
            try:
                if self._pan_tool_active():
                    return True
                return bool(event.modifiers() & Qt.AltModifier)
            except Exception:
                return self._pan_tool_active()
        def set_image(self, img: Optional[Image.Image], reset_zoom: bool = True):
            self.base_image = img
            self._transform_overlay_cache_key = None
            self._transform_overlay_cache = None
            if reset_zoom:
                self.zoom = 1.0
                self._pan_x = 0.0
                self._pan_y = 0.0
            self._update_view_image()
            if self.view_image and self.show_crop and not self.crop_rects:
                self.crop_rect = None
                self.selected_crop_index = -1
            if hasattr(self, "_ensure_separator_inside"):
                self._ensure_separator_inside()
            if hasattr(self, "_ensure_transform_inside"):
                self._ensure_transform_inside()
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
            self._transform_overlay_cache_key = None
            self._transform_overlay_cache = None
            bounds = QRectF(0, 0, nw, nh)
            clamped_crops = []
            for rect in getattr(self, "crop_rects", []) or []:
                try:
                    r = QRectF(rect).intersected(bounds)
                    if r.width() >= 5 and r.height() >= 5:
                        clamped_crops.append(r)
                except Exception:
                    pass
            self.crop_rects = clamped_crops
            if self.crop_rect is not None:
                self.crop_rect = self.crop_rect.intersected(bounds)
            self._store_active_crop()
            self._sync_active_crop()
            if getattr(self, "selection_rect", None) is not None:
                self.selection_rect = self.selection_rect.intersected(bounds)
            if getattr(self, "erase_rect", None) is not None:
                self.erase_rect = self.erase_rect.intersected(bounds)
            self._update_image_offset()
        def create_default_crop(self):
            if not self.view_image:
                return
            w, h = self.view_image.size
            m = 0.05
            rect = QRectF(w * m, h * m, w * (1 - 2 * m), h * (1 - 2 * m))
            if hasattr(self, "add_crop_rect"):
                self.add_crop_rect(rect)
            else:
                self.crop_rect = rect
                self.changed.emit()
        def create_default_selection(self):
            if not self.view_image:
                return
            w, h = self.view_image.size
            self.selection_rect = QRectF(w * 0.25, h * 0.20, w * 0.50, h * 0.35)
            self.show_selection = True
            self.changed.emit()
        def _ensure_separator_inside(self):
            if self.view_image is None or self.separator is None:
                return
            try:
                w, h = self.view_image.size
                self.separator.cx = max(0.0, min(float(w), float(self.separator.cx)))
                self.separator.cy = max(0.0, min(float(h), float(self.separator.cy)))
            except Exception:
                self.separator = None
