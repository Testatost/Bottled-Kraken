"""Zusammengesetzter Bildbearbeitungsdialog."""
from ..shared import *
from ..dialogs import *
from .common import ImageEditSettings, WhiteBorderDialog
from .canvas import ImageEditCanvas
from .dialog_setup import ImageEditDialogSetupMixin
from .dialog_actions import ImageEditDialogActionsMixin
from .dialog_processing import ImageEditDialogProcessingMixin

class ImageEditDialog(
    ImageEditDialogProcessingMixin,
    ImageEditDialogActionsMixin,
    ImageEditDialogSetupMixin,
    QDialog,
):
    pass
