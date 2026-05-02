
"""Öffentliche Worker-Schnittstelle."""

from ._workers.pdf_ocr_workers import PDFRenderWorker, OCRWorker
from ._workers.external_backend_ocr import (
    ExternalBackendOCRWorker,
    get_external_ocr_backend,
    get_external_ocr_backends,
    clear_external_ocr_backend_cache,
)
from ._workers.backend_installer import (
    BackendInstallerWorker,
    BackendInstallDialog,
    backend_root,
    backend_dir,
    detect_platform_id,
)
from ._workers.batch_revision_worker import AIBatchRevisionWorker
from ._workers.ai_revision_worker import AIRevisionWorker
from ._workers.huggingface_download_worker import HFDownloadWorker
from ._workers.voice_line_fill_worker import VoiceLineFillWorker
from ._workers.export_worker import ExportWorker, CombinedPDFExportWorker

__all__ = [
    "PDFRenderWorker",
    "OCRWorker",
    "ExternalBackendOCRWorker",
    "get_external_ocr_backend",
    "get_external_ocr_backends",
    "clear_external_ocr_backend_cache",
    "BackendInstallerWorker",
    "BackendInstallDialog",
    "backend_root",
    "backend_dir",
    "detect_platform_id",
    "AIBatchRevisionWorker",
    "AIRevisionWorker",
    "HFDownloadWorker",
    "VoiceLineFillWorker",
    "ExportWorker",
    "CombinedPDFExportWorker",
]
