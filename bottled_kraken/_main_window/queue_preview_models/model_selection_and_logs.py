from bottled_kraken.common import (
    KRAKEN_MODELS_DIR,
    QDateTime,
    QFileDialog,
    QMessageBox,
    os,
)
class MainWindowModelSelectionAndLogsMixin:
        def choose_rec_model(self):
            start_dir = self.last_rec_model_dir or KRAKEN_MODELS_DIR or os.getcwd()
            p, _ = QFileDialog.getOpenFileName(
                self,
                self._tr("dlg_choose_rec"),
                start_dir,
                self._tr("dlg_filter_model")
            )
            if p:
                self.model_path = p
                self.last_rec_model_dir = os.path.dirname(p)
                self.settings.setValue("paths/last_rec_model_dir", self.last_rec_model_dir)
                name = os.path.basename(p)
                self.btn_rec_model.setText(self._tr("btn_rec_model_value", name))
                self.status_bar.showMessage(self._tr("msg_loaded_rec", name))
                self._update_models_menu_labels()
                self._update_model_clear_buttons()
        def choose_seg_model(self):
            start_dir = self.last_seg_model_dir or KRAKEN_MODELS_DIR or os.getcwd()
            p, _ = QFileDialog.getOpenFileName(
                self,
                self._tr("dlg_choose_seg"),
                start_dir,
                self._tr("dlg_filter_model")
            )
            if p:
                self.seg_model_path = p
                self.last_seg_model_dir = os.path.dirname(p)
                self.settings.setValue("paths/last_seg_model_dir", self.last_seg_model_dir)
                name = os.path.basename(p)
                self.btn_seg_model.setText(self._tr("btn_seg_model_value", name))
                self.status_bar.showMessage(self._tr("msg_loaded_seg", name))
                self._update_models_menu_labels()
                self._update_model_clear_buttons()
        def _update_model_clear_buttons(self):
            has_rec = bool(self.model_path)
            has_seg = bool(self.seg_model_path)
            if hasattr(self, "btn_rec_clear"):
                self.btn_rec_clear.setEnabled(has_rec)
            if hasattr(self, "btn_seg_clear"):
                self.btn_seg_clear.setEnabled(has_seg)
            if hasattr(self, "act_clear_rec"):
                self.act_clear_rec.setEnabled(has_rec)
            if hasattr(self, "act_clear_seg"):
                self.act_clear_seg.setEnabled(has_seg)
        def clear_rec_model(self):
            self.model_path = ""
            self.btn_rec_model.setText(self._tr("btn_rec_model_empty"))
            self.status_bar.showMessage(self._tr("msg_loaded_rec", "-"))
            self._update_models_menu_labels()
            self._update_model_clear_buttons()
        def clear_seg_model(self):
            self.seg_model_path = ""
            self.btn_seg_model.setText(self._tr("btn_seg_model_empty"))
            self.status_bar.showMessage(self._tr("msg_loaded_seg", "-"))
            self._update_models_menu_labels()
            self._update_model_clear_buttons()
        def _log(self, msg: str):
            ts = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
            line = f"[{ts}] {msg}"
            try:
                self.log_edit.appendPlainText(line)
            except Exception:
                pass
        def toggle_log_area(self, checked: bool):
            self.log_visible = bool(checked)
            self.log_edit.setVisible(self.log_visible)
            if hasattr(self, "act_toggle_log"):
                self.act_toggle_log.setChecked(checked)
                self.act_toggle_log.setText(
                    self._tr("log_toggle_hide") if checked else self._tr("log_toggle_show")
                )
            if hasattr(self, "btn_toggle_log"):
                self.btn_toggle_log.setText(
                    self._tr("log_toggle_hide") if checked else self._tr("log_toggle_show")
                )
        def export_log_txt(self):
            base_dir = self.current_export_dir or os.getcwd()
            dest_path, _ = QFileDialog.getSaveFileName(
                self,
                self._tr("dlg_save_log"),
                os.path.join(base_dir, "ocr_log.txt"),
                self._tr("dlg_filter_txt")
            )
            if not dest_path:
                return
            if not dest_path.lower().endswith(".txt"):
                dest_path += ".txt"
            try:
                with open(dest_path, "w", encoding="utf-8") as f:
                    f.write(self.log_edit.toPlainText())
                self._log(self._tr_log("log_export_log_done", dest_path))
                self.status_bar.showMessage(self._tr("msg_exported", os.path.basename(dest_path)))
            except Exception as e:
                QMessageBox.critical(self, self._tr("err_title"), str(e))
