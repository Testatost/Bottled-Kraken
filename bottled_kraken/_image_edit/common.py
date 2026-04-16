"""Kleine Bildbearbeitungs-Hilfsklassen."""
from ..shared import *
from ..dialogs import *

@dataclass
class ImageEditSeparator:
    cx: float
    cy: float
    angle: float = 0.0
    HANDLE_R = 8
    ROT_R = 12
    ROT_OFFSET = 30
    def direction_vector(self) -> Tuple[float, float]:
        return math.sin(self.angle), -math.cos(self.angle)
    def clipped_endpoints(self, w: float, h: float) -> Optional[Tuple[float, float, float, float]]:
        if w <= 1 or h <= 1:
            return None
        vx, vy = self.direction_vector()
        eps = 1e-9
        candidates = []
        if abs(vx) > eps:
            for x in (0.0, float(w)):
                t = (x - self.cx) / vx
                y = self.cy + t * vy
                if -1e-6 <= y <= h + 1e-6:
                    candidates.append((t, x, max(0.0, min(float(h), y))))
        if abs(vy) > eps:
            for y in (0.0, float(h)):
                t = (y - self.cy) / vy
                x = self.cx + t * vx
                if -1e-6 <= x <= w + 1e-6:
                    candidates.append((t, max(0.0, min(float(w), x)), y))
        if len(candidates) < 2:
            return None
        unique = []
        for t, x, y in candidates:
            if not any(abs(x - ux) < 1e-4 and abs(y - uy) < 1e-4 for _, ux, uy in unique):
                unique.append((t, x, y))
        if len(unique) < 2:
            return None
        unique.sort(key=lambda item: item[0])
        _, x1, y1 = unique[0]
        _, x2, y2 = unique[-1]
        return x1, y1, x2, y2
    def top_handle(self, w: float, h: float):
        pts = self.clipped_endpoints(w, h)
        if pts is None:
            return self.cx, self.cy
        x1, y1, x2, y2 = pts
        return (x1, y1) if (y1 < y2 or (abs(y1 - y2) < 1e-6 and x1 <= x2)) else (x2, y2)
    def bottom_handle(self, w: float, h: float):
        pts = self.clipped_endpoints(w, h)
        if pts is None:
            return self.cx, self.cy
        x1, y1, x2, y2 = pts
        return (x2, y2) if (y1 < y2 or (abs(y1 - y2) < 1e-6 and x1 <= x2)) else (x1, y1)
    def distance_to_line(self, px: float, py: float, w: float, h: float) -> float:
        pts = self.clipped_endpoints(w, h)
        if pts is None:
            return 1e9
        x1, y1, x2, y2 = pts
        vx = x2 - x1
        vy = y2 - y1
        wx = px - x1
        wy = py - y1
        denom = math.hypot(vx, vy)
        if denom == 0:
            return math.hypot(px - x1, py - y1)
        return abs(vx * wy - vy * wx) / denom
    def set_from_points(self, p1: Tuple[float, float], p2: Tuple[float, float]):
        x1, y1 = p1
        x2, y2 = p2
        self.cx = (x1 + x2) / 2.0
        self.cy = (y1 + y2) / 2.0
        dx = x2 - x1
        dy = y2 - y1
        if abs(dx) >= 1e-9 or abs(dy) >= 1e-9:
            self.angle = math.atan2(dx, -dy)
    def move_by(self, dx: float, dy: float, w: float, h: float):
        self.cx = max(0.0, min(float(w), self.cx + dx))
        self.cy = max(0.0, min(float(h), self.cy + dy))
    def rotation_handle_pos(self):
        px = math.cos(self.angle)
        py = math.sin(self.angle)
        return self.cx + px * self.ROT_OFFSET, self.cy + py * self.ROT_OFFSET

@dataclass
class ImageEditSettings:
    rotation_angle: float = 0.0
    color_mode: str = "RGB"
    contrast_enabled: bool = False
    crop_enabled: bool = False
    crop_orig: Optional[Tuple[int, int, int, int]] = None
    split_enabled: bool = False
    separator_norm: Optional[Tuple[float, float, float]] = None  # cx/w, cy/h, angle
    smart_split_enabled: bool = False
    white_border_px: int = 0
    erase_enabled: bool = False
    erase_shape: str = ""   # "", "rect", "ellipse"
    erase_orig: Optional[Tuple[int, int, int, int]] = None
    erase_actions: List[Tuple[str, Tuple[int, int, int, int]]] = field(default_factory=list)

class WhiteBorderDialog(QDialog):
    def __init__(self, current_px: int = 0, parent=None):
        super().__init__(parent)
        tr = getattr(parent, "_tr", None)
        self._tr = tr if callable(tr) else translation.make_tr("de")
        self.setWindowTitle(self._tr("white_border_title"))
        lay = QVBoxLayout(self)
        form = QFormLayout()
        self.sp_px = QSpinBox()
        self.sp_px.setRange(0, 5000)
        self.sp_px.setValue(int(current_px))
        form.addRow(self._tr("white_border_pixels"), self.sp_px)
        lay.addLayout(form)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText(self._tr("dlg_box_apply"))
        bb.button(QDialogButtonBox.Cancel).setText(self._tr("btn_cancel"))
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)
    def get_value(self) -> int:
        return int(self.sp_px.value())
