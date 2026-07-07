from bottled_kraken.user_storage import bottled_kraken_user_path

from bottled_kraken.common import (
    List,
    Tuple,
    os,
    shutil,
    sys,
)
class MainWindowWhisperPathHelpersMixin:
        def _app_base_dir(self) -> str:
            if getattr(sys, "frozen", False):
                return os.path.dirname(sys.executable)
            return os.path.dirname(os.path.abspath(sys.argv[0]))
        def _default_whisper_base_dir(self) -> str:
            base = str(bottled_kraken_user_path("whisper"))
            os.makedirs(base, exist_ok=True)
            return base
        def _default_whisper_model_dir(self) -> str:
            return os.path.join(self._default_whisper_base_dir(), "faster-whisper-large-v3")
        def _system_python_for_venv_cmd(self) -> List[str]:
            if not getattr(sys, "frozen", False):
                return [sys.executable]
            if sys.platform.startswith("win"):
                py_launcher = shutil.which("py")
                if py_launcher:
                    return [py_launcher, "-3.11"]
                python_exe = shutil.which("python")
                if python_exe:
                    return [python_exe]
                raise RuntimeError(self._tr("err_whisper_no_system_python_win"))
            python_exe = shutil.which("python3") or shutil.which("python")
            if python_exe:
                return [python_exe]
            raise RuntimeError(self._tr("err_whisper_no_python"))
        def _hf_cli_executable(self, platform_name: str) -> str:
            name = (platform_name or "").strip().lower()
            venv_dir = self._whisper_venv_dir()
            if name == "windows":
                return os.path.join(venv_dir, "Scripts", "hf.exe")
            return os.path.join(venv_dir, "bin", "hf")
        def _whisper_venv_dir(self) -> str:
            return os.path.join(self._default_whisper_base_dir(), ".venv")
        def _whisper_venv_python_path(self, platform_name: str) -> str:
            name = (platform_name or "").strip().lower()
            venv_dir = self._whisper_venv_dir()
            if name == "windows":
                return os.path.join(venv_dir, "Scripts", "python.exe")
            return os.path.join(venv_dir, "bin", "python3")
        def _whisper_button_commands(self, platform_name: str) -> Tuple[str, str]:
            name = (platform_name or "").strip().lower()
            model_dir = self._default_whisper_model_dir().replace("\\", "/")
            venv_dir = self._whisper_venv_dir().replace("\\", "/")
            venv_python = self._whisper_venv_python_path(platform_name).replace("\\", "/")
            hf_exe = self._hf_cli_executable(platform_name).replace("\\", "/")
            if name == "windows":
                if getattr(sys, "frozen", False):
                    bootstrap_cmd = f'py -3.11 -m venv "{venv_dir}"'
                else:
                    bootstrap_cmd = f'"{sys.executable}" -m venv "{venv_dir}"'
            else:
                bootstrap_cmd = f'python3 -m venv "{venv_dir}"'
            install_cmd = (
                f'{bootstrap_cmd}\n'
                f'"{venv_python}" -m pip install -U pip setuptools wheel huggingface_hub faster-whisper sounddevice'
            )
            download_cmd = (
                f'"{hf_exe}" download '
                f'Systran/faster-whisper-large-v3 --local-dir "{model_dir}"'
            )
            return install_cmd, download_cmd
