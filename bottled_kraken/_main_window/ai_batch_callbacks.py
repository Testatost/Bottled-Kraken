"""Mixin für MainWindow: AI-Batch-Callbacks."""
from ..shared import *
from ..ui_components import *
from ..workers import *
from ..dialogs import *
from ..image_edit import *

class MainWindowAiBatchCallbacksMixin:
    def on_ai_batch_file_done(self, path: str, revised_lines: list, current: int, total: int):
        task = next((i for i in self.queue_items if i.path == path), None)
        if not task or not task.results:
            return
        task.status = STATUS_DONE
        self._update_queue_row(path)
        text, kr_records, im, recs = task.results
        revised_lines = [str(x).strip() for x in revised_lines]
        self._log(
            self._tr_log("log_ai_batch_debug_return", os.path.basename(path), len(revised_lines), len(recs)))
        if len(revised_lines) < len(recs):
            revised_lines.extend([recs[i].text for i in range(len(revised_lines), len(recs))])
        elif len(revised_lines) > len(recs):
            revised_lines = revised_lines[:len(recs)]
        self._log(self._tr_log("log_ai_batch_debug_old_first", recs[0].text if recs else "<leer>"))
        self._log(self._tr_log("log_ai_batch_debug_new_first", revised_lines[0] if revised_lines else "<leer>"))
        self._log(self._tr_log("log_ai_batch_debug_all", revised_lines))
        self._push_undo(task)
        # WICHTIG:
        # Texte ersetzen, Boxen aber exakt so behalten wie sie aktuell im Task stehen.
        new_recs = [
            RecordView(i, revised_lines[i], recs[i].bbox)
            for i in range(len(recs))
        ]
        task.results = (
            "\n".join(rv.text for rv in new_recs).strip(),
            kr_records,
            im,
            new_recs
        )
        task.edited = True
        cur = self._current_task()
        if cur and cur.path == path:
            keep_row = self.list_lines.currentRow()
            if keep_row < 0:
                keep_row = 0 if new_recs else None
            self._sync_ui_after_recs_change(task, keep_row=keep_row)
        self._update_queue_row(path)
        self._log(self._tr_log("log_ai_done", os.path.basename(path)))

    def on_ai_batch_file_failed(self, path: str, msg: str, current: int, total: int):
        task = next((i for i in self.queue_items if i.path == path), None)
        if task:
            task.status = STATUS_ERROR
            self._update_queue_row(path)
        self._log(self._tr_log("log_ai_error", os.path.basename(path), msg))

    def on_ai_batch_finished(self):
        self.act_ai_revise.setEnabled(True)
        if self.ai_batch_dialog:
            self.ai_batch_dialog.close()
            self.ai_batch_dialog = None
        self.status_bar.showMessage(self._tr("msg_ai_batch_finished"))
