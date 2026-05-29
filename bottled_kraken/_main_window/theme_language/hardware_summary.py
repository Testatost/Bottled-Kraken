from bottled_kraken.common import (
    Dict,
    Tuple,
    ctypes,
    html,
    os,
    platform,
    subprocess,
    sys,
    torch,
)
from bottled_kraken.workers import (
    get_external_ocr_backend,
)
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
        def _gpu_capabilities(self, *, refresh: bool = False) -> Dict[str, Tuple[bool, str]]:
            caps: Dict[str, Tuple[bool, str]] = {"cpu": (True, "CPU")}
            cuda_avail = False
            cuda_name = ""
            try:
                cuda_avail = torch.cuda.is_available() and torch.cuda.device_count() > 0
                if cuda_avail:
                    cuda_name = torch.cuda.get_device_name(0)
            except Exception:
                cuda_avail = False
                cuda_name = ""
            hip_ver = getattr(torch.version, "hip", None)
            cuda_ver = getattr(torch.version, "cuda", None)
            rocm_avail = bool(cuda_avail and hip_ver is not None)
            rocm_details = f"{cuda_name} (HIP {hip_ver})" if rocm_avail and cuda_name else (f"HIP {hip_ver}" if rocm_avail else "ROCm")
            cuda_true = bool(cuda_avail and cuda_ver is not None)
            cuda_true_details = f"{cuda_name} (CUDA {cuda_ver})" if cuda_true and cuda_name else (f"CUDA {cuda_ver}" if cuda_true else "CUDA")
            try:
                ext_cuda = get_external_ocr_backend("nvidia-cuda", refresh=refresh)
                if ext_cuda and ext_cuda.ok:
                    cuda_true = True
                    cuda_true_details = ext_cuda.detail or "NVIDIA CUDA Backend"
            except Exception:
                pass
            try:
                ext_rocm = get_external_ocr_backend("amd-rocm", refresh=refresh)
                if ext_rocm and ext_rocm.ok:
                    rocm_avail = True
                    rocm_details = ext_rocm.detail or "AMD ROCm Backend"
            except Exception:
                pass
            caps["cuda"] = (cuda_true, cuda_true_details)
            caps["rocm"] = (rocm_avail, rocm_details)
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
                        ["wmic", "cpu", "get", "name"],
                        text=True,
                        encoding="utf-8",
                        errors="ignore",
                        **_no_console_kwargs(),
                    )
                    lines = [x.strip() for x in out.splitlines() if x.strip() and x.strip().lower() != "name"]
                    if lines:
                        return lines[0], logical
                except Exception:
                    pass
            elif sys.platform == "darwin":
                try:
                    out = subprocess.check_output(
                        ["sysctl", "-n", "machdep.cpu.brand_string"],
                        text=True,
                        encoding="utf-8",
                        errors="ignore",
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
        def _gpu_summary(self, *, refresh_backends: bool = False) -> Dict[str, object]:
            caps = self._gpu_capabilities(refresh=refresh_backends)
            info = {
                "gpu_ok": False,
                "gpu_label": self._tr("help_hw_gpu_none"),
                "gpu_vram_gb": 0.0,
                "gpu_vram_text": self._tr("help_hw_vram_unknown"),
            }
            def _apply_vram_from_bytes(total_memory) -> bool:
                try:
                    total_memory = int(total_memory or 0)
                except Exception:
                    total_memory = 0
                if total_memory <= 0:
                    return False
                vram_gb = round(total_memory / (1024 ** 3), 1)
                info["gpu_vram_gb"] = vram_gb
                info["gpu_vram_text"] = self._tr("help_hw_fmt_gb", vram_gb)
                return True
            def _apply_vram_from_external_backend(kind: str) -> bool:
                try:
                    backend = get_external_ocr_backend(kind, refresh=False)
                    data = getattr(backend, "self_test", None) if backend else None
                    if not isinstance(data, dict):
                        return False
                    total_memory = data.get("cuda_device_total_memory") or data.get("vram_bytes")
                    if _apply_vram_from_bytes(total_memory):
                        return True
                    total_gb = data.get("cuda_device_total_memory_gb") or data.get("vram_gb")
                    try:
                        total_gb = float(total_gb or 0.0)
                    except Exception:
                        total_gb = 0.0
                    if total_gb > 0:
                        info["gpu_vram_gb"] = round(total_gb, 1)
                        info["gpu_vram_text"] = self._tr("help_hw_fmt_gb", info["gpu_vram_gb"])
                        return True
                except Exception:
                    pass
                return False
            for key in ("cuda", "rocm"):
                ok, detail = caps.get(key, (False, ""))
                if not ok:
                    continue
                info["gpu_ok"] = True
                info["gpu_label"] = detail if detail else key.upper()
                if key in ("cuda", "rocm"):
                    got_vram = False
                    try:
                        if torch.cuda.is_available() and torch.cuda.device_count() > 0:
                            props = torch.cuda.get_device_properties(0)
                            got_vram = _apply_vram_from_bytes(getattr(props, "total_memory", 0))
                    except Exception:
                        got_vram = False
                    if not got_vram:
                        backend_kind = "nvidia-cuda" if key == "cuda" else "amd-rocm"
                        got_vram = _apply_vram_from_external_backend(backend_kind)
                    if not got_vram:
                        info["gpu_vram_text"] = self._tr("help_hw_vram_unknown")
                else:
                    info["gpu_vram_text"] = self._tr("help_hw_vram_shared")
                break
            return info
        def _hardware_snapshot(self, *, refresh_backends: bool = False) -> Dict[str, object]:
            cpu_name, cpu_threads = self._cpu_summary()
            ram_gb = self._total_ram_gb()
            gpu = self._gpu_summary(refresh_backends=refresh_backends)
            return {
                "cpu_name": cpu_name,
                "cpu_threads": cpu_threads,
                "ram_gb": ram_gb,
                "gpu_ok": gpu["gpu_ok"],
                "gpu_label": gpu["gpu_label"],
                "gpu_vram_gb": gpu["gpu_vram_gb"],
                "gpu_vram_text": gpu["gpu_vram_text"],
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
