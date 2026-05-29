from bottled_kraken.common import (
    Image,
    ImageDraw,
    List,
    Optional,
    QPointF,
    QRectF,
    Tuple,
    math,
)
from bottled_kraken._image_edit.common import ImageEditSeparator
from PySide6.QtGui import QPolygonF
class ImageEditCanvasCropEraseSelectionStateMixin:
        def _store_active_crop(self):
            if not hasattr(self, "crop_rects"):
                self.crop_rects = []
            if not hasattr(self, "selected_crop_index"):
                self.selected_crop_index = -1
            if self.crop_rect is None:
                return
            if 0 <= self.selected_crop_index < len(self.crop_rects):
                self.crop_rects[self.selected_crop_index] = QRectF(self.crop_rect)
            else:
                self.crop_rects.append(QRectF(self.crop_rect))
                self.selected_crop_index = len(self.crop_rects) - 1
        def _sync_active_crop(self):
            if not hasattr(self, "crop_rects"):
                self.crop_rects = []
            if not self.crop_rects:
                self.selected_crop_index = -1
                self.crop_rect = None
                return
            if self.selected_crop_index < 0 or self.selected_crop_index >= len(self.crop_rects):
                self.selected_crop_index = len(self.crop_rects) - 1
            self.crop_rect = QRectF(self.crop_rects[self.selected_crop_index])
        def add_crop_rect(self, rect: QRectF):
            if not hasattr(self, "crop_rects"):
                self.crop_rects = []
            self._store_active_crop()
            rect = self._clamp_rect(QRectF(rect))
            self.crop_rects.append(rect)
            self.selected_crop_index = len(self.crop_rects) - 1
            self.crop_rect = QRectF(rect)
            self.show_crop = True
            self.update()
            self.changed.emit()
        def select_crop_index(self, idx: int) -> bool:
            if not hasattr(self, "crop_rects"):
                self.crop_rects = []
            self._store_active_crop()
            idx = int(idx)
            if 0 <= idx < len(self.crop_rects):
                self.selected_crop_index = idx
                self.crop_rect = QRectF(self.crop_rects[idx])
                self.update()
                return True
            self.selected_crop_index = -1
            self.crop_rect = None
            self.update()
            return False
        def delete_selected_crop(self) -> bool:
            if not hasattr(self, "crop_rects"):
                self.crop_rects = []
            idx = int(getattr(self, "selected_crop_index", -1))
            if 0 <= idx < len(self.crop_rects):
                self.crop_rects.pop(idx)
                if self.crop_rects:
                    self.selected_crop_index = min(idx, len(self.crop_rects) - 1)
                    self.crop_rect = QRectF(self.crop_rects[self.selected_crop_index])
                else:
                    self.selected_crop_index = -1
                    self.crop_rect = None
                self.update()
                self.changed.emit()
                return True
            return False
        def _crop_hit_index(self, p: QPointF) -> Optional[int]:
            if not hasattr(self, "crop_rects"):
                self.crop_rects = []
            self._store_active_crop()
            for idx in range(len(self.crop_rects) - 1, -1, -1):
                rect = self.crop_rects[idx]
                if rect is not None and (rect.contains(p) or self._rect_edge_at(rect, p)):
                    return idx
            return None
        def get_all_crops_orig(self) -> List[Tuple[int, int, int, int]]:
            if self.base_image is None or self.view_image is None:
                return []
            if not hasattr(self, "crop_rects"):
                self.crop_rects = []
            self._store_active_crop()
            bw, bh = self.base_image.size
            vw, vh = self.view_image.size
            sx = bw / max(1, vw)
            sy = bh / max(1, vh)
            out = []
            for rect in self.crop_rects:
                if rect is None:
                    continue
                x1 = max(0, min(rect.left(), vw - 2))
                y1 = max(0, min(rect.top(), vh - 2))
                x2 = max(x1 + 2, min(rect.right(), vw))
                y2 = max(y1 + 2, min(rect.bottom(), vh))
                out.append((
                    int(round(x1 * sx)),
                    int(round(y1 * sy)),
                    int(round(x2 * sx)),
                    int(round(y2 * sy)),
                ))
            return out
        def set_crops_from_orig(self, crop_list: Optional[List[Tuple[int, int, int, int]]], active_index: int = -1):
            self.crop_rects = []
            self.crop_rect = None
            self.selected_crop_index = -1
            if not crop_list or self.base_image is None or self.view_image is None:
                self.update()
                return
            bw, bh = self.base_image.size
            vw, vh = self.view_image.size
            sx = vw / max(1, bw)
            sy = vh / max(1, bh)
            for crop_orig in crop_list:
                if crop_orig is None:
                    continue
                x1, y1, x2, y2 = crop_orig
                rect = QRectF(x1 * sx, y1 * sy, (x2 - x1) * sx, (y2 - y1) * sy)
                self.crop_rects.append(self._clamp_rect(rect))
            if self.crop_rects:
                active_index = int(active_index)
                if active_index < 0 or active_index >= len(self.crop_rects):
                    active_index = len(self.crop_rects) - 1
                self.selected_crop_index = active_index
                self.crop_rect = QRectF(self.crop_rects[self.selected_crop_index])
            self.update()
        def get_crop_orig(self) -> Optional[Tuple[int, int, int, int]]:
            crops = self.get_all_crops_orig()
            if not crops:
                return None
            idx = getattr(self, "selected_crop_index", -1)
            if idx < 0 or idx >= len(crops):
                idx = len(crops) - 1
            return crops[idx]
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
            self.set_crops_from_orig([crop_orig] if crop_orig else [], 0)
        def set_selection_draw_mode(self, mode: str):
            mode = str(mode or "rect").lower()
            if mode not in ("rect", "ellipse", "polygon", "freehand"):
                mode = "rect"
            self.selection_draw_mode = mode
            self.show_selection = True
            self.update()
        def _selection_rect_from_points(self, points: List[QPointF]) -> Optional[QRectF]:
            pts = [p for p in (points or []) if p is not None]
            if not pts:
                return None
            min_x = min(p.x() for p in pts)
            min_y = min(p.y() for p in pts)
            max_x = max(p.x() for p in pts)
            max_y = max(p.y() for p in pts)
            if max_x - min_x < 2 or max_y - min_y < 2:
                return None
            return self._clamp_rect(QRectF(min_x, min_y, max_x - min_x, max_y - min_y))
        def _set_selection_polygon(self, points: List[QPointF]):
            pts = []
            for p in points or []:
                pts.append(QPointF(
                    max(0.0, min(float(self.view_image.size[0] if self.view_image else 0), float(p.x()))),
                    max(0.0, min(float(self.view_image.size[1] if self.view_image else 0), float(p.y()))),
                ))
            self.selection_polygon = pts if len(pts) >= 3 else None
            self.selection_rect = self._selection_rect_from_points(pts) if len(pts) >= 3 else None
            self.show_selection = True
            self.update()
            self.changed.emit()
        def _selection_point_hit(self, p: QPointF) -> int:
            pts = list(self.selection_polygon or [])
            if not pts and self.selection_rect is not None:
                pts = [
                    self.selection_rect.topLeft(),
                    self.selection_rect.topRight(),
                    self.selection_rect.bottomRight(),
                    self.selection_rect.bottomLeft(),
                ]
            best_idx = -1
            best_dist = 999999.0
            for idx, pt in enumerate(pts):
                dx = pt.x() - p.x()
                dy = pt.y() - p.y()
                dist = (dx * dx + dy * dy) ** 0.5
                if dist < best_dist and dist <= 12.0:
                    best_idx = idx
                    best_dist = dist
            return best_idx
        def _ensure_selection_polygon_from_rect(self):
            if self.selection_polygon or self.selection_rect is None:
                return
            r = self.selection_rect
            self.selection_polygon = [
                QPointF(r.left(), r.top()),
                QPointF(r.right(), r.top()),
                QPointF(r.right(), r.bottom()),
                QPointF(r.left(), r.bottom()),
            ]
        def _ellipse_points_for_rect(self, rect: QRectF, steps: int = 48) -> List[QPointF]:
            if rect is None:
                return []
            cx = rect.center().x()
            cy = rect.center().y()
            rx = max(1.0, rect.width() / 2.0)
            ry = max(1.0, rect.height() / 2.0)
            pts = []
            steps = max(12, int(steps))
            for i in range(steps):
                a = (2.0 * math.pi * i) / float(steps)
                pts.append(QPointF(cx + math.cos(a) * rx, cy + math.sin(a) * ry))
            return pts
        def _simplify_selection_points(self, points: List[QPointF], min_dist: float = 10.0) -> List[QPointF]:
            pts = [QPointF(p) for p in (points or [])]
            if len(pts) <= 3:
                return pts
            simplified = [pts[0]]
            min_dist2 = float(min_dist) * float(min_dist)
            for p in pts[1:]:
                dx = p.x() - simplified[-1].x()
                dy = p.y() - simplified[-1].y()
                if dx * dx + dy * dy >= min_dist2:
                    simplified.append(p)
            if len(simplified) >= 2:
                dx = simplified[0].x() - simplified[-1].x()
                dy = simplified[0].y() - simplified[-1].y()
                if dx * dx + dy * dy < min_dist2:
                    simplified[-1] = simplified[0]
            if len(simplified) > 120:
                step = max(1, int(math.ceil(len(simplified) / 120.0)))
                simplified = simplified[::step]
            return simplified
        def _selection_mask_for_rect(self, src_rect: QRectF, size: Tuple[int, int]) -> Image.Image:
            w, h = int(size[0]), int(size[1])
            mask = Image.new("L", (max(1, w), max(1, h)), 0)
            pts = list(getattr(self, "transform_src_polygon", None) or self.selection_polygon or [])
            if len(pts) >= 3:
                rel = [(float(p.x() - src_rect.left()), float(p.y() - src_rect.top())) for p in pts]
                ImageDraw.Draw(mask).polygon(rel, fill=255)
            else:
                ImageDraw.Draw(mask).rectangle((0, 0, max(0, w - 1), max(0, h - 1)), fill=255)
            return mask
        def get_selection_state_orig(self) -> Optional[dict]:
            if self.selection_rect is None or self.base_image is None or self.view_image is None:
                return None
            bw, bh = self.base_image.size
            vw, vh = self.view_image.size
            sx = bw / max(1.0, float(vw))
            sy = bh / max(1.0, float(vh))
            rect = self.selection_rect
            rect_orig = (
                int(round(max(0.0, min(rect.left(), vw - 2)) * sx)),
                int(round(max(0.0, min(rect.top(), vh - 2)) * sy)),
                int(round(max(2.0, min(rect.right(), vw)) * sx)),
                int(round(max(2.0, min(rect.bottom(), vh)) * sy)),
            )
            polygon_orig = []
            for p in (getattr(self, "selection_polygon", None) or []):
                polygon_orig.append((
                    int(round(max(0.0, min(float(p.x()), float(vw))) * sx)),
                    int(round(max(0.0, min(float(p.y()), float(vh))) * sy)),
                ))
            return {
                "rect": rect_orig,
                "polygon": polygon_orig,
                "mode": str(getattr(self, "selection_draw_mode", "rect") or "rect"),
                "show": bool(getattr(self, "show_selection", False)),
            }
        def set_selection_state_from_orig(self, state: Optional[dict]):
            if not state or self.base_image is None or self.view_image is None:
                self.selection_rect = None
                self.selection_polygon = None
                self.update()
                return
            bw, bh = self.base_image.size
            vw, vh = self.view_image.size
            sx = float(vw) / max(1.0, float(bw))
            sy = float(vh) / max(1.0, float(bh))
            rect_orig = state.get("rect")
            if rect_orig:
                x1, y1, x2, y2 = rect_orig
                self.selection_rect = QRectF(x1 * sx, y1 * sy, (x2 - x1) * sx, (y2 - y1) * sy)
            else:
                self.selection_rect = None
            polygon = []
            for x, y in (state.get("polygon") or []):
                polygon.append(QPointF(float(x) * sx, float(y) * sy))
            self.selection_polygon = polygon if polygon else None
            if self.selection_polygon and len(self.selection_polygon) >= 3:
                rect = self._selection_rect_from_points(self.selection_polygon)
                if rect is not None:
                    self.selection_rect = rect
            mode = str(state.get("mode") or "rect")
            if mode in ("rect", "ellipse", "polygon", "freehand"):
                self.selection_draw_mode = mode
            self.show_selection = bool(state.get("show", True))
            self.update()
        def get_selection_orig(self) -> Optional[Tuple[int, int, int, int]]:
            if self.selection_rect is None or self.base_image is None or self.view_image is None:
                return None
            bw, bh = self.base_image.size
            vw, vh = self.view_image.size
            sx = bw / vw
            sy = bh / vh
            x1 = max(0, min(self.selection_rect.left(), vw - 2))
            y1 = max(0, min(self.selection_rect.top(), vh - 2))
            x2 = max(x1 + 2, min(self.selection_rect.right(), vw))
            y2 = max(y1 + 2, min(self.selection_rect.bottom(), vh))
            return (int(round(x1 * sx)), int(round(y1 * sy)), int(round(x2 * sx)), int(round(y2 * sy)))
        def set_selection_from_orig(self, selection_orig: Optional[Tuple[int, int, int, int]]):
            if selection_orig is None or self.base_image is None or self.view_image is None:
                self.selection_rect = None
                self.selection_polygon = None
                self.update()
                return
            bw, bh = self.base_image.size
            vw, vh = self.view_image.size
            sx = vw / bw
            sy = vh / bh
            x1, y1, x2, y2 = selection_orig
            self.selection_rect = QRectF(x1 * sx, y1 * sy, (x2 - x1) * sx, (y2 - y1) * sy)
            self.show_selection = True
            self.update()
