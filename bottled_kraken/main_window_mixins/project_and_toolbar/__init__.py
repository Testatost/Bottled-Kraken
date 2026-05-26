from .project_files import MainWindowProjectFilesMixin
from .queue_selection import MainWindowQueueSelectionMixin
from .toolbar_icons import MainWindowToolbarIconFactoryMixin

class MainWindowProjectPersistenceAndQueueSelectionMixin(MainWindowProjectFilesMixin, MainWindowQueueSelectionMixin, MainWindowToolbarIconFactoryMixin):
    pass

__all__ = ['MainWindowProjectPersistenceAndQueueSelectionMixin', 'MainWindowProjectFilesMixin', 'MainWindowQueueSelectionMixin', 'MainWindowToolbarIconFactoryMixin']
