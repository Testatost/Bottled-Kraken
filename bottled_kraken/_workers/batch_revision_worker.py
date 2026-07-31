from bottled_kraken.common import _normalize_ai_script_mode
from bottled_kraken._workers.ai_revision_worker import AIRevisionWorker
from bottled_kraken.cancellation import operation_was_cancelled
from bottled_kraken.runtime_logging import get_logger

from bottled_kraken.common import (
    AI_SCRIPT_PRINT,
    Any,
    Dict,
    List,
    Optional,
    QThread,
    RecordView,
    Signal,
    TaskItem,
    os,
    translation,
)
class AIBatchRevisionWorker(QThread):
    file_started = Signal(str, int, int)
    file_finished = Signal(str, list, int, int)
    file_failed = Signal(str, str, int, int)
    progress_changed = Signal(int)
    status_changed = Signal(str)
    finished_batch = Signal()
    def __init__(
            self,
            items: List[TaskItem],
            lm_model: str,
            endpoint: str,
            enable_thinking: bool = False,
            script_mode: str = AI_SCRIPT_PRINT,
            temperature: float = 0.2,
            top_p: float = 0.8,
            top_k: int = 10,
            presence_penalty: float = 0.0,
            repetition_penalty: float = 1.0,
            min_p: float = 0.0,
            max_tokens: int = 1200,
            tr_func=None,
            parent=None
    ):
        super().__init__(parent)
        self._tr = tr_func or translation.make_tr(translation.DEFAULT_LANGUAGE)
        self.items = items
        self.lm_model = lm_model
        self.endpoint = endpoint
        self.enable_thinking = enable_thinking
        self.script_mode = _normalize_ai_script_mode(script_mode)
        self.temperature = float(temperature)
        self.top_p = float(top_p)
        self.top_k = int(top_k)
        self.presence_penalty = float(presence_penalty)
        self.repetition_penalty = float(repetition_penalty)
        self.min_p = float(min_p)
        self.max_tokens = int(max_tokens)
        self._current_worker: Optional[AIRevisionWorker] = None
        self._cancel_requested = False
    def cancel(self):
        self._cancel_requested = True
        self.requestInterruption()
        worker = self._current_worker
        if worker is not None:
            try:
                worker.cancel()
            except Exception:
                pass
    def _revise_one_item(self, item: TaskItem) -> List[str]:
        if self.isInterruptionRequested():
            raise RuntimeError(self._tr("msg_ai_cancelled"))
        if not item.results:
            return []
        _, _, _, recs = item.results
        live_boxes = (
            list(item.preset_bboxes)
            if len(item.preset_bboxes) == len(recs)
            else [rv.bbox for rv in recs]
        )
        recs_for_ai = [
            RecordView(i, recs[i].text, tuple(live_boxes[i]) if live_boxes[i] else None)
            for i in range(len(recs))
        ]
        result_holder: Dict[str, Any] = {}
        error_holder: Dict[str, Any] = {}
        worker = AIRevisionWorker(
            path=item.path,
            recs=recs_for_ai,
            lm_model=self.lm_model,
            endpoint=self.endpoint,
            enable_thinking=self.enable_thinking,
            source_kind=item.source_kind,
            script_mode=self.script_mode,
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            presence_penalty=self.presence_penalty,
            repetition_penalty=self.repetition_penalty,
            min_p=self.min_p,
            max_tokens=self.max_tokens,
            tr_func=self._tr,
            parent=None
        )
        self._current_worker = worker
        try:
            worker.status_changed.connect(self.status_changed.emit)
            worker.finished_revision.connect(
                lambda path, lines: result_holder.setdefault("lines", lines)
            )
            worker.failed_revision.connect(
                lambda path, msg: error_holder.setdefault("msg", msg)
            )
            worker.run()
        finally:
            self._current_worker = None
        if self.isInterruptionRequested():
            raise RuntimeError(self._tr("msg_ai_cancelled"))
        if "msg" in error_holder:
            raise RuntimeError(str(error_holder["msg"]))
        return list(result_holder.get("lines", []))
    def run(self):
        total = len(self.items)
        if total <= 0:
            self.finished_batch.emit()
            return
        for i, item in enumerate(self.items, start=1):
            if self.isInterruptionRequested():
                break
            self.file_started.emit(item.path, i, total)
            self.status_changed.emit(self._tr("status_ai_batch_file", i, total, os.path.basename(item.path)))
            self.progress_changed.emit(int(((i - 1) / total) * 100))
            try:
                revised_lines = self._revise_one_item(item)
                if self.isInterruptionRequested():
                    break
                self.file_finished.emit(item.path, revised_lines, i, total)
            except Exception as e:
                msg = str(e)
                if not operation_was_cancelled(worker=self, message=msg):
                    get_logger("workers.ai_revision").exception(
                        "AI batch revision failed for %s", item.path
                    )
                self.file_failed.emit(item.path, msg, i, total)
                if self.isInterruptionRequested() or self._cancel_requested:
                    break
            self.progress_changed.emit(int((i / total) * 100))
        self.status_changed.emit(self._tr("status_ai_batch_done"))
        self.finished_batch.emit()
