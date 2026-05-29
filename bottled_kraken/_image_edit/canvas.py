from bottled_kraken.common import (
    QWidget,
    Signal,
)
from bottled_kraken._image_edit.common import ImageEditSeparator
from bottled_kraken._image_edit.canvas_setup_and_geometry import ImageEditCanvasSetupMixin
from bottled_kraken._image_edit.canvas_interaction_and_painting import ImageEditCanvasInteractionMixin
class ImageEditCanvas(
    ImageEditCanvasInteractionMixin,
    ImageEditCanvasSetupMixin,
    QWidget,
):
    changed = Signal()
    rotation_committed = Signal(float)
    local_rotation_requested = Signal(tuple, float)
    local_skew_requested = Signal(tuple, str, float)
