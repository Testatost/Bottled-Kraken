from bottled_kraken.common import (
    QInputDialog,
    Tuple,
)
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
            return "cpu", "int8"
