"""Mixin für MainWindow: undo voice fill and ai revision."""
from ...shared import *
from ...ui_components import *
from ...workers import *
from ...dialogs import *
from ...image_edit import *

class MainWindowAiRevisionTargetsMixin:
        def _ai_revision_task_has_revisable_results(self, task: Optional[TaskItem]) -> bool:
            """True, wenn ein Queue-Task verwertbare OCR-Zeilen besitzt."""
            if not task or not getattr(task, "results", None):
                return False
            try:
                _text, _kr_records, _im, recs = task.results
            except Exception:
                return False
            return bool(recs)

        def _ai_revision_unique_tasks(self, tasks: List[TaskItem]) -> List[TaskItem]:
            out: List[TaskItem] = []
            seen = set()
            for task in tasks or []:
                path = getattr(task, "path", None)
                if not path or path in seen:
                    continue
                seen.add(path)
                out.append(task)
            return out

        def _ai_revision_queue_targets(self) -> List[TaskItem]:
            checked = self._checked_queue_tasks()
            selected = self._selected_queue_tasks()
            # Priorität: Haken im Wartebereich vor normaler Tabellen-Auswahl.
            return self._ai_revision_unique_tasks(checked if checked else selected)

        def _ai_revision_ready_tasks(self, tasks: List[TaskItem]) -> List[TaskItem]:
            return [task for task in self._ai_revision_unique_tasks(tasks) if self._ai_revision_task_has_revisable_results(task)]

        def _prepare_task_for_ai_revision(self, task: TaskItem) -> None:
            if not self._ai_revision_task_has_revisable_results(task):
                return
            try:
                # Nur bei der tatsächlich sichtbaren Seite die aktuell verschobenen Overlay-Boxen sichern.
                if getattr(self, "_loaded_preview_path", None) == getattr(task, "path", None):
                    self._persist_live_canvas_bboxes(task)
            except Exception:
                pass
            try:
                _text, _kr_records, _im, recs = task.results
                boxes = [tuple(rv.bbox) if rv.bbox else None for rv in recs]
                task.preset_bboxes = list(boxes)
                task.lm_locked_bboxes = list(boxes)
            except Exception:
                pass
