"""Mixin für MainWindow: undo voice fill and ai revision."""
from ...shared import *
from ...ui_components import *
from ...workers import *
from ...dialogs import *
from ...image_edit import *

class MainWindowVoiceModelAndDeviceMixin:
        def set_ai_model_dialog(self):
            model_id, ok = QInputDialog.getText(
                self,
                self._tr("dlg_choose_ai_model"),
                self._tr("dlg_choose_ai_model_label"),
                text=self.ai_model_id
            )
            if not ok:
                return
            self.ai_model_id = model_id.strip()
            self._update_ai_model_ui()
            if self.ai_model_id:
                self.status_bar.showMessage(self._tr("msg_ai_model_set", self.ai_model_id))
            else:
                self.status_bar.showMessage(self._tr("msg_ai_model_id_cleared_auto"))

        def _resolve_faster_whisper_device(self) -> Tuple[str, str]:
            # Wichtig:
            # Whisper immer auf CPU laufen lassen.
            # Sonst kollidiert es mit Kraken-OCR und/oder LM Studio im VRAM.
            return "cpu", "int8"

        def _auto_select_best_device(self):
            caps = self._gpu_capabilities()
            # Priorität: CUDA (echtes CUDA build) > ROCm/HIP > MPS > CPU
            for dev in ("cuda", "rocm", "mps", "cpu"):
                ok, _ = caps.get(dev, (False, ""))
                if ok:
                    self.device_str = dev
                    break
