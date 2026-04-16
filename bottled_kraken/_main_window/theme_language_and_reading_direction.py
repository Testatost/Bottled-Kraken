"""Mixin für MainWindow: theme language and reading direction."""
from ..shared import *
from ..ui_components import *
from ..workers import *
from ..dialogs import *
from ..image_edit import *

class MainWindowThemeLanguageAndReadingDirectionMixin:
    def set_reading_direction(self, mode):
        self.reading_direction = mode

    def retranslate_ui(self):
        self.setWindowTitle(self._tr("app_title"))
        self.file_menu.setTitle(self._tr("menu_file"))
        self.edit_menu.setTitle(self._tr("menu_edit"))
        self.models_menu.setTitle(self._tr("menu_models"))
        self.options_menu.setTitle(self._tr("menu_options"))
        self.hw_menu.setTitle(self._tr("menu_hw"))
        self.export_menu.setTitle(self._tr("menu_export"))
        self.reading_menu.setTitle(self._tr("menu_reading"))
        if hasattr(self, "revision_models_menu"):
            self.revision_models_menu.setTitle(self._tr("menu_lm_options"))
        if hasattr(self, "whisper_menu"):
            self.whisper_menu.setTitle(self._tr("menu_whisper_options"))
        self.act_export_log.setText(self._tr("menu_export_log"))
        if hasattr(self, "act_lm_help"):
            self.act_lm_help.setText(self._tr("act_help"))
        if hasattr(self, "act_ai_revise"):
            self.act_ai_revise.setText(self._tr("act_ai_revise"))
            self.act_ai_revise.setToolTip(self._tr("act_ai_revise_tip"))
        if hasattr(self, "btn_ai_model"):
            self._update_ai_model_ui()
        if hasattr(self, "act_ai_revise_all"):
            self.act_ai_revise_all.setText(self._tr("act_ai_revise_all"))
            self.act_ai_revise_all.setToolTip(self._tr("act_ai_revise_all_tip"))
        if hasattr(self, "btn_import_lines"):
            self.btn_import_lines.setText(self._tr("btn_import_lines"))
            self.btn_import_lines.setToolTip(self._tr("btn_import_lines_tip"))
        if hasattr(self, "act_import_lines_current"):
            self.act_import_lines_current.setText(self._tr("act_import_lines_current"))
        if hasattr(self, "act_import_lines_selected"):
            self.act_import_lines_selected.setText(self._tr("act_import_lines_selected"))
        if hasattr(self, "act_import_lines_all"):
            self.act_import_lines_all.setText(self._tr("act_import_lines_all"))
        if hasattr(self, "act_project_save"):
            self.act_project_save.setText(self._tr("menu_project_save"))
        if hasattr(self, "act_project_save_as"):
            self.act_project_save_as.setText(self._tr("menu_project_save_as"))
        if hasattr(self, "act_project_load"):
            self.act_project_load.setText(self._tr("menu_project_load"))
        if hasattr(self, "act_paste_files_menu"):
            self.act_paste_files_menu.setText(self._tr("act_paste_clipboard"))
        if hasattr(self, "act_paste_files"):
            self.act_paste_files.setText(self._tr("act_paste_clipboard"))
        if hasattr(self, "btn_voice_fill"):
            self.btn_voice_fill.setText(self._tr("act_voice_fill"))
            self.btn_voice_fill.setToolTip(self._tr("act_voice_fill_tip"))
        if hasattr(self, "btn_ai_revise_bottom"):
            self.btn_ai_revise_bottom.setText(self._tr("act_ai_revise"))
            self.btn_ai_revise_bottom.setToolTip(self._tr("act_ai_revise_tip"))
        if hasattr(self, "btn_line_search"):
            self.btn_line_search.setText(self._tr("btn_line_search"))
            self.btn_line_search.setToolTip(self._tr("btn_line_search_tooltip"))
        if hasattr(self, "line_search_popup_edit"):
            self.line_search_popup_edit.setPlaceholderText(self._tr("line_search_placeholder"))
            self.line_search_popup_edit.setToolTip(self._tr("line_search_tooltip"))
        if hasattr(self, "btn_clear_queue"):
            self.btn_clear_queue.setText(self._tr("act_clear_queue"))
        if hasattr(self, "btn_toggle_log"):
            if self.btn_toggle_log.isChecked():
                self.btn_toggle_log.setText(self._tr("log_toggle_hide"))
            else:
                self.btn_toggle_log.setText(self._tr("log_toggle_show"))
        self.act_undo.setText(self._tr("act_undo"))
        self.act_redo.setText(self._tr("act_redo"))
        self.act_add_files.setText(self._tr("act_add_files"))
        self.act_exit.setText(self._tr("menu_exit"))
        self.act_download.setText(self._tr("act_download_model"))
        self.act_overlay.setText(self._tr("act_overlay_show"))
        self.act_add.setText(self._tr("act_add_files"))
        self.act_clear.setText(self._tr("act_clear_queue"))
        self.act_play.setText(self._tr("act_start_ocr"))
        self.act_stop.setText(self._tr("act_stop_ocr"))
        if hasattr(self, "act_image_edit"):
            self.act_image_edit.setText(self._tr("act_image_edit"))
        self.act_project_load_toolbar.setText(self._tr("menu_project_load"))
        self.act_project_load_toolbar.setToolTip(self._tr("menu_project_load"))
        self.lbl_queue.setText(self._tr("lbl_queue"))
        self.lbl_lines.setText(self._tr("lbl_lines"))
        self.queue_table.setHorizontalHeaderLabels(["#", "☐", self._tr("col_loaded_files"), self._tr("col_status")])
        self._update_queue_check_header()
        if hasattr(self.list_lines, "setHeaderLabels"):
            self.list_lines.setHeaderLabels(["#", self._tr("lines_tree_header")])
            self.list_lines.header().setDefaultAlignment(Qt.AlignCenter)
        if self.model_path:
            self.btn_rec_model.setText(self._tr("btn_rec_model_value", os.path.basename(self.model_path)))
        else:
            self.btn_rec_model.setText(self._tr("btn_rec_model_empty"))
        if self.seg_model_path:
            self.btn_seg_model.setText(self._tr("btn_seg_model_value", os.path.basename(self.seg_model_path)))
        else:
            self.btn_seg_model.setText(self._tr("btn_seg_model_empty"))
        mapping = {"cpu": "hw_cpu", "cuda": "hw_cuda", "rocm": "hw_rocm", "mps": "hw_mps"}
        for dev, key in mapping.items():
            if dev in self.hw_actions:
                self.hw_actions[dev].setText(self._tr(key))
        read_keys = ["reading_tb_lr", "reading_tb_rl", "reading_bt_lr", "reading_bt_rl"]
        for act, key in zip(self.read_actions, read_keys):
            act.setText(self._tr(key))
        self._retranslate_queue_rows()
        self._update_queue_hint()
        self.canvas._show_drop_hint()
        self._update_models_menu_labels()
        self._update_model_clear_buttons()
        self._update_toolbar_language_theme_ui()
        self._set_primary_toolbar_icons()
        self._set_secondary_button_icons()
        QTimer.singleShot(0, self._normalize_toolbar_button_sizes)
        # Models menu actions
        if hasattr(self, "act_rec"):
            self.act_rec.setText(self._tr("act_load_rec_model"))
        if hasattr(self, "act_seg"):
            self.act_seg.setText(self._tr("act_load_seg_model"))
        if hasattr(self, "act_whisper_set_path"):
            self.act_whisper_set_path.setText(self._tr("act_whisper_set_path"))
        if hasattr(self, "act_whisper_set_mic"):
            self.act_whisper_set_mic.setText(self._tr("act_whisper_set_mic"))
        if hasattr(self, "act_whisper_scan"):
            self.act_whisper_scan.setText(self._tr("act_scan_local"))
        if hasattr(self, "act_set_manual_lm_url"):
            self.act_set_manual_lm_url.setText(self._tr("act_set_manual_lm_url"))
        if hasattr(self, "act_clear_manual_lm_url"):
            self.act_clear_manual_lm_url.setText(self._tr("act_clear_manual_lm_url"))
        if hasattr(self, "act_scan_lm"):
            self.act_scan_lm.setText(self._tr("act_scan_local"))
        if hasattr(self, "act_clear_rec"):
            self.act_clear_rec.setText(self._tr("act_clear_rec"))
        if hasattr(self, "act_clear_seg"):
            self.act_clear_seg.setText(self._tr("act_clear_seg"))
        if hasattr(self, "kraken_models_submenu"):
            self.kraken_models_submenu.setTitle(self._tr("submenu_available_kraken_models"))
        if hasattr(self, "ai_models_submenu"):
            self.ai_models_submenu.setTitle(self._tr("submenu_available_ai_models"))
        if hasattr(self, "whisper_models_submenu"):
            self.whisper_models_submenu.setTitle(self._tr("submenu_available_whisper_models"))
        self._update_kraken_menu_status()
        self._rebuild_kraken_models_submenu()
        self.refresh_models_menu_status()
        self._update_whisper_menu_status()
        self._rebuild_whisper_model_submenu()
        if hasattr(self, "btn_rec_clear"):
            self.btn_rec_clear.setToolTip(self._tr("act_clear_rec"))
        if hasattr(self, "btn_seg_clear"):
            self.btn_seg_clear.setToolTip(self._tr("act_clear_seg"))
        header = self.queue_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QUEUE_COL_NUM, QHeaderView.Fixed)
        header.setSectionResizeMode(QUEUE_COL_CHECK, QHeaderView.Fixed)
        header.setSectionResizeMode(QUEUE_COL_FILE, QHeaderView.Stretch)
        header.setSectionResizeMode(QUEUE_COL_STATUS, QHeaderView.Interactive)
        # Header-Schrift im Wartebereich normal halten
        header_font = header.font()
        header_font.setBold(False)
        header.setFont(header_font)

    def _retranslate_queue_rows(self):
        for it in self.queue_items:
            self._update_queue_row(it.path)

    def _gpu_capabilities(self) -> Dict[str, Tuple[bool, str]]:
        caps: Dict[str, Tuple[bool, str]] = {"cpu": (True, "CPU")}
        cuda_avail = torch.cuda.is_available() and torch.cuda.device_count() > 0
        cuda_name = ""
        if cuda_avail:
            try:
                cuda_name = torch.cuda.get_device_name(0)
            except Exception:
                cuda_name = "GPU"
        hip_ver = getattr(torch.version, "hip", None)
        cuda_ver = getattr(torch.version, "cuda", None)
        # Verfügbarkeit von ROCm (HIP)
        rocm_avail = cuda_avail and (hip_ver is not None)
        rocm_details = ""
        if rocm_avail:
            rocm_details = f"{cuda_name} (HIP {hip_ver})" if cuda_name else f"HIP {hip_ver}"
        # Verfügbarkeit von CUDA (echter CUDA-Build)
        cuda_true = cuda_avail and (cuda_ver is not None)
        cuda_true_details = ""
        if cuda_true:
            cuda_true_details = f"{cuda_name} (CUDA {cuda_ver})" if cuda_name else f"CUDA {cuda_ver}"
        mps_avail = hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
        mps_details = "Apple MPS" if mps_avail else ""
        caps["cuda"] = (cuda_true, cuda_true_details if cuda_true_details else "CUDA")
        caps["rocm"] = (rocm_avail, rocm_details if rocm_details else "ROCm")
        caps["mps"] = (mps_avail, mps_details if mps_details else "MPS")
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
                    errors="ignore"
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
                    errors="ignore"
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
        caps = self._gpu_capabilities()
        info = {
            "gpu_ok": False,
            "gpu_label": self._tr("help_hw_gpu_none"),
            "gpu_vram_gb": 0.0,
            "gpu_vram_text": self._tr("help_hw_vram_unknown"),
        }
        for key in ("cuda", "rocm", "mps"):
            ok, detail = caps.get(key, (False, ""))
            if not ok:
                continue
            info["gpu_ok"] = True
            info["gpu_label"] = detail if detail else key.upper()
            if key in ("cuda", "rocm"):
                try:
                    props = torch.cuda.get_device_properties(0)
                    total_memory = int(getattr(props, "total_memory", 0) or 0)
                    if total_memory > 0:
                        vram_gb = round(total_memory / (1024 ** 3), 1)
                        info["gpu_vram_gb"] = vram_gb
                        info["gpu_vram_text"] = self._tr("help_hw_fmt_gb", vram_gb)
                    else:
                        info["gpu_vram_text"] = self._tr("help_hw_vram_unknown")
                except Exception:
                    info["gpu_vram_text"] = self._tr("help_hw_vram_unknown")
            else:
                info["gpu_vram_text"] = self._tr("help_hw_vram_shared")
            break
        return info

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
