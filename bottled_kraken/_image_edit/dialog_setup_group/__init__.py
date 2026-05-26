from .tool_buttons import ImageEditDialogToolButtonsMixin
from .layout_and_init import ImageEditDialogLayoutAndInitMixin
from .options_and_navigation import ImageEditDialogOptionsAndNavigationMixin

class ImageEditDialogSetupMixin(ImageEditDialogToolButtonsMixin, ImageEditDialogLayoutAndInitMixin, ImageEditDialogOptionsAndNavigationMixin):
    pass

__all__ = ['ImageEditDialogSetupMixin', 'ImageEditDialogToolButtonsMixin', 'ImageEditDialogLayoutAndInitMixin', 'ImageEditDialogOptionsAndNavigationMixin']
