"""Mixin für MainWindow: whisper download help and image edit queue."""
from ...shared import *
from ...ui_components import *
from ...workers import *
from ...dialogs import *
from ...image_edit import *

class MainWindowWhisperDownloadsMixin:
        def _whisper_system_hint(self, platform_name: str) -> str:
            name = (platform_name or "").strip().lower()
            if name in ("debian", "ubuntu", "linux mint", "mint"):
                return self._tr("whisper_hint_debian")
            if name == "fedora":
                return self._tr("whisper_hint_fedora")
            if name == "arch":
                return self._tr("whisper_hint_arch")
            if name in ("mac", "macos", "darwin"):
                return self._tr("whisper_hint_macos")
            if name == "windows":
                return self._tr("whisper_hint_windows")
            return self._tr("whisper_hint_generic")

        def download_whisper_model_from_help_dialog(self, platform_name: str, dialog_parent=None):
            # 1) zuerst prüfen, ob large-v3 schon vorhanden ist
            existing_model_dir = self._find_existing_whisper_large_v3_model()
            if existing_model_dir:
                base_dir = os.path.dirname(existing_model_dir)
                self.whisper_models_base_dir = self._normalize_whisper_base_dir(base_dir)
                self.settings.setValue("paths/whisper_models_base_dir", self.whisper_models_base_dir)
                self._scan_whisper_models()
                self._set_whisper_model(existing_model_dir)
                self._update_whisper_menu_status()
                QMessageBox.information(
                    dialog_parent or self,
                    self._tr("info_title"),
                    self._tr("msg_whisper_model_already_present") + "\n\n"
                    f"Pfad:\n{existing_model_dir}\n\n"
                    "Ein erneuter Download ist nicht nötig."
                )
                self.status_bar.showMessage(self._tr("msg_whisper_model_already_present", existing_model_dir))
                return
            platform_hint = self._whisper_system_hint(platform_name)
            QMessageBox.information(
                dialog_parent or self,
                self._tr("info_title"),
                "Optionaler Systemhinweis:\n\n"
                f"{platform_hint}\n\n"
                "Der eigentliche Download läuft trotzdem nur über eine eigene "
                "Python-Umgebung (.venv) und die Python-API von huggingface_hub."
            )
            # Prüfen, ob bereits ein Download läuft
            if self.hf_download_worker and self.hf_download_worker.isRunning():
                if self.hf_download_dialog is not None:
                    self.hf_download_dialog.show()
                    self.hf_download_dialog.raise_()
                    self.hf_download_dialog.activateWindow()
                QMessageBox.information(
                    dialog_parent or self,
                    self._tr("info_title"),
                    self._tr("warn_whisper_download_running")
                )
                return
            target_base = self._default_whisper_base_dir()
            target_model_dir = self._default_whisper_model_dir()
            try:
                os.makedirs(target_base, exist_ok=True)
                self.status_bar.showMessage(
                    self._tr("msg_whisper_download_prepare_target", target_model_dir)
                )
                self.hf_download_dialog = ProgressStatusDialog(
                    self._tr("dlg_whisper_download_title"),
                    self._tr,
                    dialog_parent or self
                )
                self.hf_download_dialog.set_status(self._tr("dlg_whisper_download_prepare"))
                self.hf_download_dialog.set_progress(0)
                self.hf_download_dialog.show()
                self.hf_download_dialog.raise_()
                self.hf_download_dialog.activateWindow()
                platform_key = (
                    "windows" if sys.platform.startswith("win")
                    else "mac" if sys.platform == "darwin"
                    else "linux"
                )
                venv_dir = self._whisper_venv_dir()
                venv_python = self._whisper_venv_python_path(platform_key)
                prepare_cmds = [
                    self._system_python_for_venv_cmd() + ["-m", "venv", venv_dir],
                ]

                install_cmd = [
                    venv_python,
                    "-m",
                    "pip",
                    "install",
                    "-U",
                    "pip",
                    "setuptools",
                    "wheel",
                    "huggingface_hub",
                    "faster-whisper",
                    "sounddevice",
                ]

                hf_exe = self._hf_cli_executable(platform_key)
                download_cmd = [
                    hf_exe,
                    "download",
                    "Systran/faster-whisper-large-v3",
                    "--local-dir",
                    target_model_dir,
                ]
                self.hf_download_worker = HFDownloadWorker(
                    repo_id="Systran/faster-whisper-large-v3",
                    local_dir=target_model_dir,
                    prepare_cmds=prepare_cmds,
                    install_cmd=install_cmd,
                    download_cmd=download_cmd,
                    tr_func=self._tr,
                    parent=self
                )
                self.hf_download_worker.progress_changed.connect(self.hf_download_dialog.set_progress)
                self.hf_download_worker.status_changed.connect(self.hf_download_dialog.set_status)
                self.hf_download_worker.finished_download.connect(self.on_hf_download_finished)
                self.hf_download_worker.failed_download.connect(self.on_hf_download_failed)
                self.hf_download_dialog.cancel_requested.connect(self.hf_download_worker.cancel)
                self.hf_download_worker.start()
            except Exception as e:
                QMessageBox.warning(
                    self,
                    self._tr("warn_title"),
                    self._tr("msg_whisper_download_start_failed", e)
                )
                self.status_bar.showMessage(self._tr("msg_whisper_download_start_failed"))

        def on_hf_download_finished(self, local_dir: str):
            self.status_bar.showMessage(self._tr("msg_whisper_model_loaded", local_dir))
            self.whisper_models_base_dir = self._normalize_whisper_base_dir(os.path.dirname(local_dir))
            self._scan_whisper_models()
            if os.path.isfile(os.path.join(local_dir, "model.bin")):
                self._set_whisper_model(local_dir)
            self._update_whisper_menu_status()
            self.settings.setValue("paths/whisper_models_base_dir", self.whisper_models_base_dir)
            if hasattr(self, "hf_download_dialog") and self.hf_download_dialog:
                self.hf_download_dialog.set_progress(100)
                self.hf_download_dialog.hide()
                self.hf_download_dialog.close()
                self.hf_download_dialog = None
            self.hf_download_worker = None
            QMessageBox.information(
                self,
                self._tr("info_title"),
                self._tr("info_whisper_model_downloaded") + "\n\n"
                f"Zielordner:\n{local_dir}"
            )

        def on_hf_download_failed(self, msg: str):
            self.status_bar.showMessage(self._tr("msg_whisper_download_failed"))
            if hasattr(self, "hf_download_dialog") and self.hf_download_dialog:
                self.hf_download_dialog.hide()
                self.hf_download_dialog.close()
                self.hf_download_dialog = None
            self.hf_download_worker = None
            QMessageBox.warning(
                self,
                self._tr("warn_title"),
                self._tr("warn_whisper_download_failed", msg)
            )
