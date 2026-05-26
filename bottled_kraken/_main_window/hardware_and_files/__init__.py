from .hardware_status import MainWindowHardwareStatusMixin
from .file_drop_and_paste import MainWindowFileDropAndPasteMixin
from .pdf_render_queue import MainWindowPdfRenderQueueMixin

class MainWindowHardwareStatusAndFileDropMixin(MainWindowHardwareStatusMixin, MainWindowFileDropAndPasteMixin, MainWindowPdfRenderQueueMixin):
    pass

__all__ = ['MainWindowHardwareStatusAndFileDropMixin', 'MainWindowHardwareStatusMixin', 'MainWindowFileDropAndPasteMixin', 'MainWindowPdfRenderQueueMixin', 'HardwareSnapshotWorker']
