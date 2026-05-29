from bottled_kraken.common import (
    QGraphicsView,
    QPointF,
    QRectF,
    Signal,
)
from bottled_kraken._ui_components.image_canvas_setup import ImageCanvasSetupMixin
from bottled_kraken._ui_components.image_canvas_interaction import ImageCanvasInteractionMixin
from bottled_kraken._ui_components.image_canvas_rendering import ImageCanvasRenderingMixin
class ImageCanvas(
    ImageCanvasRenderingMixin,
    ImageCanvasInteractionMixin,
    ImageCanvasSetupMixin,
    QGraphicsView,
):
    rect_clicked = Signal(int)
    rect_changed = Signal(int, QRectF)
    files_dropped = Signal(list)
    canvas_clicked = Signal()
    box_drawn = Signal(QRectF)
    overlay_add_draw_requested = Signal(QPointF)
    overlay_edit_requested = Signal(int)
    overlay_delete_requested = Signal(int)
    overlay_select_requested = Signal(int)
    box_split_requested = Signal(int, float)
    overlay_multi_selected = Signal(list)
