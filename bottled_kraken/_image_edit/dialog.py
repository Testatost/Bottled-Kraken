from bottled_kraken.common import (
    QDialog,
)
from bottled_kraken._image_edit.common import ImageEditSettings, WhiteBorderDialog
from bottled_kraken._image_edit.canvas import ImageEditCanvas
from bottled_kraken._image_edit.dialog_setup import ImageEditDialogSetupMixin
from bottled_kraken._image_edit.dialog_actions import ImageEditDialogActionsMixin
from bottled_kraken._image_edit.dialog_processing import ImageEditDialogProcessingMixin
class ImageEditDialog(
    ImageEditDialogProcessingMixin,
    ImageEditDialogActionsMixin,
    ImageEditDialogSetupMixin,
    QDialog,
):
    pass
