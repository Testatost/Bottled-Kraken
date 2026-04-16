"""Zusammengesetzte Canvas für die Bildbearbeitung."""
from ..shared import *
from .common import ImageEditSeparator
from .canvas_setup_and_geometry import ImageEditCanvasSetupMixin
from .canvas_interaction_and_painting import ImageEditCanvasInteractionMixin

class ImageEditCanvas(
    ImageEditCanvasInteractionMixin,
    ImageEditCanvasSetupMixin,
    QWidget,
):
    changed = Signal()

    rotation_committed = Signal(float)
