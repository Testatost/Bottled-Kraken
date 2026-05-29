from bottled_kraken.common import (
    QThread,
    Signal,
)
from bottled_kraken._workers.ai_revision_analysis import AIRevisionAnalysisMixin
from bottled_kraken._workers.ai_revision_requests import AIRevisionRequestsMixin
from bottled_kraken._workers.ai_revision_runtime import AIRevisionRuntimeMixin
from bottled_kraken._workers.ai_revision_response_parsing import AIRevisionResponseParsingMixin
class AIRevisionWorker(
    AIRevisionRuntimeMixin,
    AIRevisionResponseParsingMixin,
    AIRevisionRequestsMixin,
    AIRevisionAnalysisMixin,
    QThread,
):
    finished_revision = Signal(str, list)
    failed_revision = Signal(str, str)
    progress_changed = Signal(int)
    status_changed = Signal(str)
