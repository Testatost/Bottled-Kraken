from bottled_kraken.common import (
    QThread,
    Signal,
)
MAX_KRAKEN_OCR_LINES = 500
from bottled_kraken._workers.pdf_render_worker import PDFRenderWorker
from bottled_kraken._workers.ocr_worker_parts import (
    OCRWorkerSetupMixin,
    OCRWorkerPresetBoxesMixin,
    OCRWorkerTiledLinesMixin,
    OCRWorkerPageRecognitionMixin,
)
class OCRWorker(
    OCRWorkerPageRecognitionMixin,
    OCRWorkerTiledLinesMixin,
    OCRWorkerPresetBoxesMixin,
    OCRWorkerSetupMixin,
    QThread,
):
        file_started = Signal(str)
        file_done = Signal(str, str, list, object, list)
        file_error = Signal(str, str)
        progress = Signal(int)
        finished_batch = Signal()
        failed = Signal(str)
        device_resolved = Signal(str)
        gpu_info = Signal(str)
__all__ = ["PDFRenderWorker", "OCRWorker"]
