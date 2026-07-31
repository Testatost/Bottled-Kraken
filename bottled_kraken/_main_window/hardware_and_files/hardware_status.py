from bottled_kraken.common import _help_html
from bottled_kraken.common import (
    Dict,
    Optional,
    QTextBrowser,
    QThread,
    QTimer,
    Signal,
    html,
    isValid,
)
class HardwareSnapshotWorker(QThread):
    done = Signal(dict)
    failed = Signal(str)
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
    def run(self):
        try:
            snapshot = self.owner._hardware_snapshot()
            self.done.emit(snapshot)
        except Exception as exc:
            self.failed.emit(repr(exc))
class MainWindowHardwareStatusMixin:
        def _build_hardware_requirements_loading_html(self) -> str:
            return (
                '            <div class="card">\n'
                f'                <div class="h2">{self._tr("help_hw_card_title")}</div>\n'
                f'                <span class="badge">{self._tr("help_hw_badge")}</span>\n'
                f'                <div class="small">{self._tr("help_hw_check_running")}</div>\n'
                '                <br>\n'
                '                <table class="table">\n'
                f'                    <tr><td><b>CPU</b></td><td>{self._tr("help_hw_check_wait")}</td></tr>\n'
                f'                    <tr><td><b>GPU</b></td><td>{self._tr("help_hw_check_wait")}</td></tr>\n'
                f'                    <tr><td><b>RAM</b></td><td>{self._tr("help_hw_check_wait")}</td></tr>\n'
                '                </table>\n'
                f'                <div class="small" style="margin-top:8px;">{self._tr("help_hw_check_background")}</div>\n'
                '            </div>\n'
            )
        def _build_hardware_requirements_help_html(self, hw: Optional[Dict[str, object]] = None) -> str:
            if hw is None:
                hw = self._hardware_snapshot()
            kraken_level, kraken_key = self._hardware_feature_status(hw, "kraken")
            lm_level, lm_key = self._hardware_feature_status(hw, "lm")
            whisper_level, whisper_key = self._hardware_feature_status(hw, "whisper")
            cpu_level, cpu_key = self._hardware_component_status(hw, "cpu")
            gpu_level, gpu_key = self._hardware_component_status(hw, "gpu")
            ram_level, ram_key = self._hardware_component_status(hw, "ram")
            cpu_name = html.escape(str(hw.get("cpu_name", "CPU")))
            cpu_threads = int(hw.get("cpu_threads", 1) or 1)
            ram_gb = float(hw.get("ram_gb", 0.0) or 0.0)
            gpu_label = html.escape(str(hw.get("gpu_label", self._tr("help_hw_gpu_none"))))
            gpu_vram_text = html.escape(str(hw.get("gpu_vram_text", self._tr("help_hw_vram_unknown"))))
            gpu_devices = hw.get("gpu_devices", [])
            gpu_rows = ""
            if isinstance(gpu_devices, list) and gpu_devices:
                rows = []
                for index, device in enumerate(gpu_devices, 1):
                    if not isinstance(device, dict):
                        continue
                    name = html.escape(str(device.get("name", "") or self._tr("help_hw_unknown")))
                    driver_name = str(device.get("driver_name", "") or "").strip()
                    driver_version = str(device.get("driver_version", "") or "").strip()
                    driver_parts = [part for part in (driver_name, driver_version) if part]
                    if bool(device.get("driver_loaded", False)):
                        driver_text = " ".join(driver_parts) or self._tr("help_hw_unknown")
                    else:
                        driver_text = self._tr("help_hw_driver_missing")
                    try:
                        vram_bytes = int(device.get("vram_bytes", 0) or 0)
                    except Exception:
                        vram_bytes = 0
                    vram_text = (
                        self._tr("help_hw_fmt_gb", round(vram_bytes / (1024 ** 3), 1))
                        if vram_bytes > 0
                        else self._tr("help_hw_vram_unknown")
                    )
                    details = (
                        f'{html.escape(self._tr("help_hw_label_driver"))}: {html.escape(driver_text)}'
                        f' · {html.escape(self._tr("help_hw_label_vram"))}: {html.escape(vram_text)}'
                    )
                    rows.append(
                        f'<tr><td><b>GPU {index}</b></td><td>{name}'
                        f'<br><span class="small">{details}</span></td></tr>'
                    )
                gpu_rows = "".join(rows)
            if not gpu_rows:
                gpu_rows = (
                    f'<tr><td><b>GPU</b></td><td>{gpu_label}</td></tr>'
                    f'<tr><td><b>{self._tr("help_hw_label_vram")}</b></td><td>{gpu_vram_text}</td></tr>'
                )
            kraken_text = self._tr(kraken_key)
            lm_text = self._tr(lm_key)
            whisper_text = self._tr(whisper_key)
            cpu_text = self._tr(cpu_key)
            gpu_text = self._tr(gpu_key)
            ram_text = self._tr(ram_key)
            return (
                '            <div class="card">\n'
                f'                <div class="h2">{self._tr("help_hw_card_title")}</div>\n'
                f'                <span class="badge">{self._tr("help_hw_badge")}</span>\n'
                f'                <div class="small">{self._tr("help_hw_intro")}</div>\n'
                '                <br>\n'
                '                <table style="width:100%; border-collapse:separate; border-spacing:14px 0;">\n'
                '                    <tr>\n'
                '                        <td style="width:40%; vertical-align:top;">\n'
                f'                            <div class="h2">{self._tr("help_hw_h2_detected")}</div>\n'
                '                            <table class="table">\n'
                f'                                <tr><td><b>CPU</b></td><td>{cpu_name}</td></tr>\n'
                f'                                <tr><td><b>{self._tr("help_hw_label_threads")}</b></td><td>{cpu_threads}</td></tr>\n'
                f'                                <tr><td><b>RAM</b></td><td>{self._tr("help_hw_fmt_gb", ram_gb)}</td></tr>\n'
                f'                                {gpu_rows}\n'
                '                            </table>\n'
                '                        </td>\n'
                '                        <td style="width:30%; vertical-align:top;">\n'
                f'                            <div class="h2">{self._tr("help_hw_h2_usage")}</div>\n'
                '                            <table class="table">\n'
                f'                                <tr><td><b>{self._tr("help_hw_label_kraken")}</b></td><td>{self._status_chip_html(kraken_level, kraken_text)}</td></tr>\n'
                f'                                <tr><td><b>{self._tr("help_hw_label_lm")}</b></td><td>{self._status_chip_html(lm_level, lm_text)}</td></tr>\n'
                f'                                <tr><td><b>{self._tr("help_hw_label_whisper")}</b></td><td>{self._status_chip_html(whisper_level, whisper_text)}</td></tr>\n'
                '                            </table>\n'
                '                        </td>\n'
                '                        <td style="width:30%; vertical-align:top;">\n'
                f'                            <div class="h2">{self._tr("help_hw_h2_components")}</div>\n'
                '                            <table class="table">\n'
                f'                                <tr><td><b>CPU</b></td><td>{self._status_chip_html(cpu_level, cpu_text)}</td></tr>\n'
                f'                                <tr><td><b>GPU</b></td><td>{self._status_chip_html(gpu_level, gpu_text)}</td></tr>\n'
                f'                                <tr><td><b>RAM</b></td><td>{self._status_chip_html(ram_level, ram_text)}</td></tr>\n'
                '                            </table>\n'
                '                        </td>\n'
                '                    </tr>\n'
                '                </table>\n'
                '                <br>\n'
                f'                <div class="h2">{self._tr("help_hw_h2_requirements")}</div>\n'
                '                <table class="table">\n'
                f'                    <tr><td class="section">{self._tr("help_hw_col_area")}</td><td class="section">{self._tr("help_hw_col_min")}</td><td class="section">{self._tr("help_hw_col_rec")}</td></tr>\n'
                f'                    <tr><td><b>{self._tr("help_hw_label_kraken")}</b></td><td>{self._tr("help_hw_req_kraken_min")}</td><td>{self._tr("help_hw_req_kraken_rec")}</td></tr>\n'
                f'                    <tr><td><b>{self._tr("help_hw_label_lm")}</b></td><td>{self._tr("help_hw_req_lm_min")}</td><td>{self._tr("help_hw_req_lm_rec")}</td></tr>\n'
                f'                    <tr><td><b>{self._tr("help_hw_label_whisper")}</b></td><td>{self._tr("help_hw_req_whisper_min")}</td><td>{self._tr("help_hw_req_whisper_rec")}</td></tr>\n'
                f'                    <tr><td><b>{self._tr("help_hw_label_all")}</b></td><td>{self._tr("help_hw_req_all_min")}</td><td>{self._tr("help_hw_req_all_rec")}</td></tr>\n'
                '                </table>\n'
                f'                <div class="small" style="margin-top:8px;">{self._tr("help_hw_req_note")}</div>\n'
                f'                <div class="small" style="margin-top:4px;">{self._tr("help_hw_note")}</div>\n'
                '            </div>\n'
            )
        def _start_help_hardware_refresh(self, quick_browser: QTextBrowser):
            worker = HardwareSnapshotWorker(self)
            self._help_hardware_worker = worker
            def _browser_alive() -> bool:
                try:
                    return bool(quick_browser is not None and isValid(quick_browser))
                except Exception:
                    return False
            def _cleanup():
                try:
                    worker.deleteLater()
                except Exception:
                    pass
                if getattr(self, "_help_hardware_worker", None) is worker:
                    self._help_hardware_worker = None
            def _finish(hw: Dict[str, object]):
                try:
                    if _browser_alive():
                        html_text = self._tr("help_html_quick") + self._build_hardware_requirements_help_html(hw)
                        quick_browser.setHtml(_help_html(self.current_theme, html_text))
                except Exception:
                    pass
                _cleanup()
            def _failed(_msg: str):
                try:
                    if _browser_alive():
                        html_text = self._tr("help_html_quick") + self._build_hardware_requirements_help_html()
                        quick_browser.setHtml(_help_html(self.current_theme, html_text))
                except Exception:
                    pass
                _cleanup()
            worker.done.connect(_finish)
            worker.failed.connect(_failed)
            QTimer.singleShot(120, worker.start)
