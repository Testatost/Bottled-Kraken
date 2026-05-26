from .menu_behavior import BKStayOpenMenu
from .queue_headers import MainWindowQueueHeadersMixin
from .theme_toolbar import MainWindowThemeToolbarMixin
from .menus import MainWindowMenuConstructionMixin

class MainWindowMenuSetupAndQueueHeadersMixin(MainWindowQueueHeadersMixin, MainWindowThemeToolbarMixin, MainWindowMenuConstructionMixin):
    pass

__all__ = ['MainWindowMenuSetupAndQueueHeadersMixin', 'MainWindowQueueHeadersMixin', 'MainWindowThemeToolbarMixin', 'MainWindowMenuConstructionMixin', 'BKStayOpenMenu']
