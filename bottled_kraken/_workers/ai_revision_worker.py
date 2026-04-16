"""Zusammengesetzter AI-Revision-Worker."""
from ..shared import *
from .ai_revision_analysis import AIRevisionAnalysisMixin
from .ai_revision_requests import AIRevisionRequestsMixin
from .ai_revision_runtime import AIRevisionRuntimeMixin
from .ai_revision_response_parsing import AIRevisionResponseParsingMixin

class AIRevisionWorker(
    AIRevisionRuntimeMixin,
    AIRevisionResponseParsingMixin,
    AIRevisionRequestsMixin,
    AIRevisionAnalysisMixin,
    QThread,
):
    finished_revision = Signal(str, list)  # path, revised_lines

    failed_revision = Signal(str, str)  # path, error

    progress_changed = Signal(int)  # 0..100

    status_changed = Signal(str)  # live text
