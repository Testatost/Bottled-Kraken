from bottled_kraken.common import (
    Optional,
    QApplication,
    QPointF,
    QRectF,
    Qt,
)
from bottled_kraken._image_edit.common import ImageEditSeparator
class ImageEditCanvasCursorAndRectHelpersMixin:
        def _clamp_rect(self, rect: QRectF) -> QRectF:
            if self.view_image is None:
                return rect
            w, h = self.view_image.size
            x1 = max(0, min(rect.left(), w - 5)); y1 = max(0, min(rect.top(), h - 5))
            x2 = max(x1 + 5, min(rect.right(), w)); y2 = max(y1 + 5, min(rect.bottom(), h))
            return QRectF(x1, y1, x2 - x1, y2 - y1)
        def _update_cursor(self, p: QPointF):
            if self.rotation_mode:
                self.setCursor(Qt.OpenHandCursor)
                return
            if self._pan_active:
                self.setCursor(Qt.ClosedHandCursor)
                return
            if self._pan_tool_active() or (self._can_pan_with_alt() and (QApplication.keyboardModifiers() & Qt.AltModifier)):
                self.setCursor(Qt.OpenHandCursor)
                return
            if self.has_active_transform():
                hit = self._transform_hit(p)
                if hit is not None:
                    hit_type, _ = hit
                    if hit_type == "rotate" or str(self.transform_mode or "") == "rotate":
                        self.setCursor(Qt.OpenHandCursor)
                        return
                    if hit_type == "inside":
                        self.setCursor(Qt.SizeAllCursor)
                        return
                    if hit_type == "edge":
                        self.setCursor(Qt.SizeAllCursor if str(self.transform_mode or "") in ("skew", "perspective", "warp") else Qt.SizeHorCursor)
                        return
                    if hit_type == "corner":
                        self.setCursor(Qt.SizeFDiagCursor)
                        return
            if self.show_separator and self.separator is not None:
                hit = self._separator_hit(p)
                if hit in ("rotate", "top", "bottom", "line"):
                    self.setCursor(Qt.SizeAllCursor)
                    return
            if self.show_erase and self.erase_rect is not None:
                edge = self._rect_edge_at(self.erase_rect, p)
                if edge:
                    self.setCursor(
                        Qt.SizeHorCursor if edge in ("left", "right")
                        else Qt.SizeVerCursor if edge in ("top", "bottom")
                        else Qt.SizeFDiagCursor
                    )
                    return
                if self.erase_rect.contains(p):
                    self.setCursor(Qt.SizeAllCursor)
                    return
            if self.show_crop:
                edge = self._crop_edge_at(p)
                if edge:
                    self.setCursor(
                        Qt.SizeHorCursor if edge in ("left", "right")
                        else Qt.SizeVerCursor if edge in ("top", "bottom")
                        else Qt.SizeFDiagCursor
                    )
                    return
                if self._point_in_crop(p):
                    self.setCursor(Qt.SizeAllCursor)
                    return
            self.setCursor(Qt.CrossCursor)
        def _rect_edge_at(self, rect: Optional[QRectF], p: QPointF) -> Optional[str]:
            if rect is None:
                return None
            pad = 8.0
            x = p.x()
            y = p.y()
            left = abs(x - rect.left()) <= pad
            right = abs(x - rect.right()) <= pad
            top = abs(y - rect.top()) <= pad
            bottom = abs(y - rect.bottom()) <= pad
            if left and top:
                return "left_top"
            if right and top:
                return "right_top"
            if left and bottom:
                return "left_bottom"
            if right and bottom:
                return "right_bottom"
            if left:
                return "left"
            if right:
                return "right"
            if top:
                return "top"
            if bottom:
                return "bottom"
            return None
