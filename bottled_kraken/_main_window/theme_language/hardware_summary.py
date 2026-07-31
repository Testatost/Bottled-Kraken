from bottled_kraken.common import (
    Dict,
    Tuple,
    ctypes,
    html,
    os,
    platform,
    subprocess,
    sys,
)
from bottled_kraken.system_gpu_detection import detect_system_gpus
def _no_console_kwargs() -> dict:
    if not sys.platform.startswith("win"):
        return {}
    kwargs = {}
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
        kwargs["startupinfo"] = startupinfo
    except Exception:
        pass
    return kwargs
class MainWindowHardwareSummaryMixin:
        def _gpu_capabilities(self) -> Dict[str, Tuple[bool, str]]:
            """Kompatibilitaetsansicht fuer vorhandene Aufrufer.

            Die Erkennung basiert auf den installierten Systemtreibern und nicht
            auf der CUDA-/ROCm-Unterstuetzung der eingebauten Torch-Version.
            """
            devices = detect_system_gpus()
            caps: Dict[str, Tuple[bool, str]] = {"cpu": (True, "CPU")}
            for vendor, key, label in (("nvidia", "cuda", "CUDA"), ("amd", "rocm", "ROCm")):
                matches = [d for d in devices if str(d.get("vendor", "")).lower() == vendor]
                usable = [d for d in matches if bool(d.get("driver_loaded", False))]
                names = ", ".join(str(d.get("name", "")).strip() for d in usable if str(d.get("name", "")).strip())
                caps[key] = (bool(usable), names or label)
            return caps
        def _total_ram_bytes(self) -> int:
            try:
                if sys.platform.startswith("win"):
                    class MEMORYSTATUSEX(ctypes.Structure):
                        _fields_ = [
                            ("dwLength", ctypes.c_ulong),
                            ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong),
                            ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong),
                            ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong),
                            ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                        ]
                    stat = MEMORYSTATUSEX()
                    stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                    if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                        return int(stat.ullTotalPhys)
            except Exception:
                pass
            try:
                if hasattr(os, "sysconf"):
                    pages = os.sysconf("SC_PHYS_PAGES")
                    page_size = os.sysconf("SC_PAGE_SIZE")
                    if isinstance(pages, int) and isinstance(page_size, int) and pages > 0 and page_size > 0:
                        return int(pages * page_size)
            except Exception:
                pass
            return 0
        def _total_ram_gb(self) -> float:
            ram_bytes = self._total_ram_bytes()
            if ram_bytes <= 0:
                return 0.0
            return round(ram_bytes / (1024 ** 3), 1)
        def _cpu_summary(self) -> Tuple[str, int]:
            logical = os.cpu_count() or 1
            name = ""
            if sys.platform.startswith("win"):
                try:
                    import winreg
                    key = winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
                    )
                    name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
                    name = " ".join(str(name).split()).strip()
                    if name:
                        return name, logical
                except Exception:
                    pass
                try:
                    out = subprocess.check_output(
                        [
                            "powershell.exe",
                            "-NoLogo",
                            "-NoProfile",
                            "-NonInteractive",
                            "-Command",
                            "(Get-CimInstance -ClassName Win32_Processor | Select-Object -First 1 -ExpandProperty Name)",
                        ],
                        text=True,
                        encoding="utf-8",
                        errors="ignore",
                        timeout=3,
                        **_no_console_kwargs(),
                    ).strip()
                    if out:
                        return " ".join(out.split()), logical
                except (OSError, subprocess.SubprocessError):
                    pass
            elif sys.platform == "darwin":
                try:
                    out = subprocess.check_output(
                        ["sysctl", "-n", "machdep.cpu.brand_string"],
                        text=True,
                        encoding="utf-8",
                        errors="ignore",
                        timeout=3,
                        **_no_console_kwargs(),
                    ).strip()
                    if out:
                        return out, logical
                except Exception:
                    pass
            else:
                try:
                    with open("/proc/cpuinfo", "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            if ":" in line and line.lower().startswith("model name"):
                                name = line.split(":", 1)[1].strip()
                                if name:
                                    return name, logical
                except Exception:
                    pass
            try:
                name = (platform.processor() or "").strip()
            except Exception:
                name = ""
            if not name and sys.platform.startswith("win"):
                name = os.environ.get("PROCESSOR_IDENTIFIER", "").strip()
            if not name:
                name = "CPU"
            return name, logical
        def _gpu_summary(self) -> Dict[str, object]:
            devices = detect_system_gpus()
            visible_devices = [d for d in devices if str(d.get("name", "")).strip()]
            usable_devices = [d for d in visible_devices if bool(d.get("driver_loaded", False))]

            max_vram_bytes = 0
            for device in usable_devices:
                try:
                    max_vram_bytes = max(max_vram_bytes, int(device.get("vram_bytes", 0) or 0))
                except Exception:
                    pass

            max_vram_gb = round(max_vram_bytes / (1024 ** 3), 1) if max_vram_bytes > 0 else 0.0
            labels = [str(d.get("name", "")).strip() for d in visible_devices]
            return {
                "gpu_ok": bool(usable_devices),
                "gpu_label": "; ".join(label for label in labels if label) or self._tr("help_hw_gpu_none"),
                "gpu_vram_gb": max_vram_gb,
                "gpu_vram_text": (
                    self._tr("help_hw_fmt_gb", max_vram_gb)
                    if max_vram_gb > 0
                    else self._tr("help_hw_vram_unknown")
                ),
                "gpu_devices": visible_devices,
            }
        def _hardware_snapshot(self) -> Dict[str, object]:
            cpu_name, cpu_threads = self._cpu_summary()
            ram_gb = self._total_ram_gb()
            gpu = self._gpu_summary()
            return {
                "cpu_name": cpu_name,
                "cpu_threads": cpu_threads,
                "ram_gb": ram_gb,
                "gpu_ok": gpu["gpu_ok"],
                "gpu_label": gpu["gpu_label"],
                "gpu_vram_gb": gpu["gpu_vram_gb"],
                "gpu_vram_text": gpu["gpu_vram_text"],
                "gpu_devices": gpu.get("gpu_devices", []),
            }
        def _hardware_feature_status(self, hw: Dict[str, object], feature: str) -> Tuple[str, str]:
            cpu_threads = int(hw.get("cpu_threads", 1) or 1)
            ram_gb = float(hw.get("ram_gb", 0.0) or 0.0)
            gpu_ok = bool(hw.get("gpu_ok", False))
            gpu_vram_gb = float(hw.get("gpu_vram_gb", 0.0) or 0.0)
            feature = (feature or "").lower().strip()
            if feature == "kraken":
                if cpu_threads >= 4 and ram_gb >= 8:
                    return "green", "help_hw_status_good"
                if cpu_threads >= 2 and ram_gb >= 4:
                    return "yellow", "help_hw_status_usable_slow"
                return "red", "help_hw_status_weak"
            if feature == "lm":
                if gpu_ok and gpu_vram_gb >= 8 and cpu_threads >= 6 and ram_gb >= 16:
                    return "green", "help_hw_status_good"
                if gpu_ok and gpu_vram_gb >= 6 and cpu_threads >= 4 and ram_gb >= 8:
                    return "yellow", "help_hw_status_limited"
                if (not gpu_ok) and cpu_threads >= 8 and ram_gb >= 16:
                    return "yellow", "help_hw_status_limited_cpu"
                return "red", "help_hw_status_weak"
            if feature == "whisper":
                if gpu_ok and gpu_vram_gb >= 4 and ram_gb >= 8:
                    return "green", "help_hw_status_good"
                if cpu_threads >= 6 and ram_gb >= 8:
                    return "green", "help_hw_status_good"
                if cpu_threads >= 4 and ram_gb >= 6:
                    return "yellow", "help_hw_status_usable_slow"
                return "red", "help_hw_status_weak"
            return "red", "help_hw_status_weak"
        def _hardware_component_status(self, hw: Dict[str, object], component: str) -> Tuple[str, str]:
            cpu_threads = int(hw.get("cpu_threads", 1) or 1)
            ram_gb = float(hw.get("ram_gb", 0.0) or 0.0)
            gpu_ok = bool(hw.get("gpu_ok", False))
            gpu_vram_gb = float(hw.get("gpu_vram_gb", 0.0) or 0.0)
            component = (component or "").lower().strip()
            if component == "cpu":
                if cpu_threads >= 6:
                    return "green", "help_hw_component_ok"
                if cpu_threads >= 4:
                    return "yellow", "help_hw_component_borderline"
                return "red", "help_hw_component_not_enough"
            if component == "gpu":
                if gpu_ok and gpu_vram_gb >= 8:
                    return "green", "help_hw_component_ok"
                if gpu_ok and (gpu_vram_gb >= 4 or gpu_vram_gb == 0):
                    return "yellow", "help_hw_component_borderline"
                return "red", "help_hw_component_not_enough"
            if component == "ram":
                if ram_gb >= 16:
                    return "green", "help_hw_component_ok"
                if ram_gb >= 8:
                    return "yellow", "help_hw_component_borderline"
                return "red", "help_hw_component_not_enough"
            return "red", "help_hw_component_not_enough"
        def _status_dot_html(self, level: str) -> str:
            colors = {
                "green": "#16a34a",
                "yellow": "#eab308",
                "red": "#dc2626",
            }
            color = colors.get(level, "#6b7280")
            return (
                f'<span style="display:inline-block; width:12px; height:12px; '
                f'border-radius:50%; background:{color}; margin-right:8px; '
                f'vertical-align:middle;"></span>'
            )
        def _status_chip_html(self, level: str, text: str) -> str:
            bg = {
                "green": "#dcfce7",
                "yellow": "#fef3c7",
                "red": "#fee2e2",
            }.get(level, "#e5e7eb")
            fg = {
                "green": "#166534",
                "yellow": "#92400e",
                "red": "#991b1b",
            }.get(level, "#374151")
            return (
                f'<span style="display:inline-block; padding:2px 8px; '
                f'border-radius:999px; background:{bg}; color:{fg}; '
                f'font-weight:700; font-size:11px; white-space:nowrap;">{html.escape(text)}</span>'
            )
