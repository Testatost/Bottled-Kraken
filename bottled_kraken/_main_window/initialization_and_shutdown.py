"""Mixin für MainWindow: initialization and shutdown."""
from ..shared import *
from ..ui_components import *
from ..workers import *
from ..dialogs import *
from ..image_edit import *

class MainWindowInitializationAndShutdownMixin:
    def _reset_ai_server_cache(self):
        self._ai_server_cache = {
            "ts": 0.0,
            "base_url": None,
            "model_id": None,
        }

    def _close_ai_progress_dialog(self):
        if hasattr(self, "ai_progress_dialog") and self.ai_progress_dialog:
            self.ai_progress_dialog.close()
            self.ai_progress_dialog = None

    def _scene_rect_to_bbox(self, scene_rect: QRectF, im: Optional[Image.Image]) -> Optional[BBox]:
        if im is None:
            return None
        img_w, img_h = im.size
        r = scene_rect.normalized()
        x0 = max(0, min(img_w - 1, int(round(r.left()))))
        y0 = max(0, min(img_h - 1, int(round(r.top()))))
        x1 = max(1, min(img_w, int(round(r.right()))))
        y1 = max(1, min(img_h, int(round(r.bottom()))))
        if x1 <= x0:
            x1 = min(img_w, x0 + 1)
        if y1 <= y0:
            y1 = min(img_h, y0 + 1)
        return (x0, y0, x1, y1)

    def _persist_live_canvas_bboxes(self, task: Optional[TaskItem]):
        if not task or not task.results:
            return
        text, kr_records, im, recs = task.results
        changed = False
        for idx, rv in enumerate(recs):
            rect_item = self.canvas._rects.get(idx)
            if not rect_item or not isValid(rect_item):
                continue
            scene_rect = rect_item.mapRectToScene(rect_item.rect()).normalized()
            bb = self._scene_rect_to_bbox(scene_rect, im)
            if bb and rv.bbox != bb:
                rv.bbox = bb
                changed = True
        if changed:
            task.results = (
                "\n".join(r.text for r in recs).strip(),
                kr_records,
                im,
                recs
            )
        self._update_task_preset_bboxes(task)

    def _all_workers(self):
        return [
            self.worker,
            self.ai_worker,
            self.ai_batch_worker,
            self.export_worker,
            self.pdf_worker,
            self.hf_download_worker,
            self.voice_worker,
        ]

    def _request_all_workers_stop(self):
        workers = []
        if self.worker and self.worker.isRunning():
            try:
                self.worker.requestInterruption()
                workers.append(self.worker)
            except Exception:
                pass
        if self.ai_worker and self.ai_worker.isRunning():
            try:
                self.ai_worker.cancel()
                workers.append(self.ai_worker)
            except Exception:
                pass
        if self.ai_batch_worker and self.ai_batch_worker.isRunning():
            try:
                self.ai_batch_worker.cancel()
                workers.append(self.ai_batch_worker)
            except Exception:
                pass
        if self.export_worker and self.export_worker.isRunning():
            try:
                self.export_worker.requestInterruption()
                workers.append(self.export_worker)
            except Exception:
                pass
        if self.pdf_worker and self.pdf_worker.isRunning():
            try:
                self.pdf_worker.requestInterruption()
                workers.append(self.pdf_worker)
            except Exception:
                pass
        if self.hf_download_worker and self.hf_download_worker.isRunning():
            try:
                self.hf_download_worker.cancel()
                workers.append(self.hf_download_worker)
            except Exception:
                pass
        if self.voice_worker and self.voice_worker.isRunning():
            try:
                self.voice_worker.cancel()
                workers.append(self.voice_worker)
            except Exception:
                pass
        for w in workers:
            try:
                w.wait(1500)
            except Exception:
                pass
