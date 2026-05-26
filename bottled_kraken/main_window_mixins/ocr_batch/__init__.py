from .ocr_start_stop import MainWindowOcrStartStopMixin
from .ocr_results import MainWindowOcrResultsMixin
from .line_selection_and_import import MainWindowLineSelectionAndImportMixin

class MainWindowImportLinesAndOcrBatchMixin(MainWindowOcrStartStopMixin, MainWindowOcrResultsMixin, MainWindowLineSelectionAndImportMixin):
    pass

__all__ = ['MainWindowImportLinesAndOcrBatchMixin', 'MainWindowOcrStartStopMixin', 'MainWindowOcrResultsMixin', 'MainWindowLineSelectionAndImportMixin']
