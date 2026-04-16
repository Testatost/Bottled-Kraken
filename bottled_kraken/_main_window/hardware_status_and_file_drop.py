"""Mixin für MainWindow: hardware status and file drop."""
from ..shared import *
from ..ui_components import *
from ..workers import *
from ..dialogs import *
from ..image_edit import *

class MainWindowHardwareStatusAndFileDropMixin:
    def _build_hardware_requirements_help_html(self) -> str:
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
            f'                                <tr><td><b>GPU</b></td><td>{gpu_label}</td></tr>\n'
            f'                                <tr><td><b>{self._tr("help_hw_label_vram")}</b></td><td>{gpu_vram_text}</td></tr>\n'
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

    def _refresh_hw_menu_availability(self):
        caps = self._gpu_capabilities()
        for dev, act in self.hw_actions.items():
            ok, detail = caps.get(dev, (False, ""))
            if dev == "cpu":
                act.setEnabled(True)
                act.setToolTip(self._tr("msg_device_cpu"))
                continue
            act.setEnabled(ok)
            act.setToolTip(detail if detail else self._tr("msg_not_available"))
        if self.device_str != "cpu":
            ok, _ = caps.get(self.device_str, (False, ""))
            if not ok:
                self.device_str = "cpu"
                if "cpu" in self.hw_actions:
                    self.hw_actions["cpu"].setChecked(True)

    def set_device(self, dev: str):
        caps = self._gpu_capabilities()
        ok, detail = caps.get(dev, (False, ""))
        if not ok:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("msg_hw_not_available"))
            dev = "cpu"
            ok, detail = caps.get("cpu", (True, "CPU"))
        self.device_str = dev
        if dev in self.hw_actions:
            self.hw_actions[dev].setChecked(True)
        if detail:
            self.status_bar.showMessage(self._tr("msg_detected_gpu", detail))
        else:
            label_key = {
                "cpu": "msg_device_cpu",
                "cuda": "msg_device_cuda",
                "rocm": "msg_device_rocm",
                "mps": "msg_device_mps",
            }.get(dev, "msg_device_cpu")
            self.status_bar.showMessage(self._tr("msg_device", self._tr(label_key)))

    def dragEnterEvent(self, event: QDragEnterEvent):
        if not event.mimeData().hasUrls():
            event.ignore()
            return
        for u in event.mimeData().urls():
            p = u.toLocalFile()
            if p and os.path.exists(p) and is_supported_drop_or_paste_file(p):
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        if not event.mimeData().hasUrls():
            event.ignore()
            return
        files = []
        for u in event.mimeData().urls():
            p = u.toLocalFile()
            if p and os.path.exists(p) and is_supported_drop_or_paste_file(p):
                files.append(p)
        if files:
            self.add_files_to_queue(files)
            event.acceptProposedAction()
        else:
            event.ignore()

    def paste_files_from_clipboard(self):
        cb = QApplication.clipboard()
        md = cb.mimeData()
        files = []
        if md:
            # Standardfall: Explorer-Dateien als URLs
            if md.hasUrls():
                for url in md.urls():
                    p = url.toLocalFile()
                    if p and os.path.exists(p) and is_supported_drop_or_paste_file(p):
                        files.append(p)
            # Fallback: Textliste mit Dateipfaden
            if not files and md.hasText():
                raw = md.text().strip()
                if raw:
                    parts = [x.strip().strip('"') for x in raw.splitlines() if x.strip()]
                    for p in parts:
                        if os.path.exists(p) and is_supported_drop_or_paste_file(p):
                            files.append(p)
            # Windows-Fallback: rohe Mime-Formate prüfen
            if not files:
                for fmt in md.formats():
                    try:
                        data = md.data(fmt)
                        if not data:
                            continue
                        txt = bytes(data).decode("utf-8", errors="ignore").strip("\x00").strip()
                        if not txt:
                            continue
                        for candidate in re.split(r'[\r\n]+', txt):
                            candidate = candidate.strip().strip('"')
                            if os.path.exists(candidate) and is_supported_drop_or_paste_file(candidate):
                                files.append(candidate)
                    except Exception:
                        pass
        # doppelte entfernen, Reihenfolge behalten
        unique = []
        seen = set()
        for p in files:
            np = os.path.normpath(p)
            if np not in seen:
                seen.add(np)
                unique.append(p)
        if unique:
            self.add_files_to_queue(unique)
        else:
            QMessageBox.information(
                self,
                self._tr("info_title"),
                "In der Zwischenablage wurden keine unterstützten Bild-, PDF- oder Projektdateien gefunden."
            )

    def choose_files(self):
        file_filter = (
            f"{self._tr('dlg_filter_img')};;"
            f"{self._tr('dlg_filter_project')}"
        )
        files, _ = QFileDialog.getOpenFileNames(
            self,
            self._tr("dlg_load_img"),
            "",
            file_filter
        )
        if files:
            self.add_files_to_queue(files)

    def _start_pdf_render_async(self, pdf_path: str, dpi: int = 300):
        # falls schon ein PDF gerendert wird: optional blockieren oder queue’n
        if self.pdf_worker and self.pdf_worker.isRunning():
            QMessageBox.information(self, self._tr("info_title"),
                                    self._tr("msg_pdf_render_already_running"))
            return
        self._pending_pdf_path = pdf_path
        self._set_progress_busy()
        # Dialog
        dlg = QProgressDialog(self)
        dlg.setWindowTitle(self._tr("pdf_render_title"))
        dlg.setCancelButtonText(self._tr("btn_cancel"))
        dlg.setMinimum(0)
        dlg.setMaximum(0)  # wird gesetzt, sobald wir total kennen
        dlg.setValue(0)
        dlg.setAutoClose(True)
        dlg.setAutoReset(True)
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.canceled.connect(self._cancel_pdf_render)
        dlg.show()
        self.pdf_progress_dlg = dlg
        # Worker
        w = PDFRenderWorker(pdf_path, dpi=dpi, parent=self)
        w.progress.connect(self._on_pdf_render_progress)
        w.finished_pdf.connect(self._on_pdf_render_finished)
        w.failed_pdf.connect(self._on_pdf_render_failed)
        self.pdf_worker = w
        w.start()

    def _cancel_pdf_render(self):
        if self.pdf_worker and self.pdf_worker.isRunning():
            self.pdf_worker.requestInterruption()

    def _on_pdf_render_progress(self, cur: int, total: int, pdf_path: str):
        dlg = self.pdf_progress_dlg
        if dlg:
            if dlg.maximum() != max(1, total):
                dlg.setMaximum(max(1, total))
            try:
                dlg.setLabelText(self._tr("pdf_render_label", cur, total, os.path.basename(pdf_path)))
            except Exception:
                dlg.setLabelText(f"Rendering pages… ({cur}/{total}): {os.path.basename(pdf_path)}")
            dlg.setValue(cur)
        self.progress_bar.setRange(0, max(1, total))
        self.progress_bar.setValue(cur)
        self.status_bar.showMessage(self._tr("pdf_render_label", cur, total, os.path.basename(pdf_path)))

    def _on_pdf_render_finished(self, pdf_path: str, out_paths: list):
        # Dialog schließen
        if self.pdf_progress_dlg:
            self.pdf_progress_dlg.setValue(self.pdf_progress_dlg.maximum())
            self.pdf_progress_dlg.close()
            self.pdf_progress_dlg = None
        self._set_progress_idle(100)
        # Worker cleanup
        self.pdf_worker = None
        if not out_paths:
            return
        # Seiten in Queue einfügen
        added_any = False
        last_added = None
        base_name = os.path.basename(pdf_path)
        for i, img_path in enumerate(out_paths, start=1):
            if any(it.path == img_path for it in self.queue_items):
                continue
            disp = self._tr("pdf_page_display", base_name, i)
            self._add_file_to_queue_single(img_path, display_name=disp, source_kind="pdf_page")
            added_any = True
            last_added = img_path
        if added_any and last_added:
            self.preview_image(last_added)
            self._log(self._tr_log("log_added_files", len(out_paths)))
        if out_paths:
            try:
                self.temp_dirs_created.add(os.path.dirname(out_paths[0]))
            except Exception:
                pass
        self._refresh_queue_numbers()
        self._fit_queue_columns_exact()
        self._update_queue_hint()

    def _on_pdf_render_failed(self, pdf_path: str, msg: str):
        if self.pdf_progress_dlg:
            self.pdf_progress_dlg.close()
            self.pdf_progress_dlg = None
        self.pdf_worker = None
        self._set_progress_idle(0)
        QMessageBox.warning(self, self._tr("warn_title"), f"PDF konnte nicht gerendert werden:\n{msg}")

    def add_files_to_queue(self, paths: List[str]):
        added_any = False
        last_added = None
        added_count = 0
        project_files = []
        normal_files = []
        for p in paths:
            if not p or not os.path.exists(p):
                continue
            if is_project_file(p):
                project_files.append(p)
            elif is_supported_input(p):
                normal_files.append(p)
        # Projektdatei hat Vorrang
        if project_files:
            self.load_project_from_path(project_files[0])
            return
        total = len(normal_files)
        progress = None
        if total > 0:
            progress = QProgressDialog(
                self._tr("queue_load_label", 0, total, ""),
                self._tr("btn_cancel"),
                0,
                total,
                self
            )
            progress.setWindowTitle(self._tr("queue_load_title"))
            progress.setWindowModality(Qt.ApplicationModal)
            progress.setMinimumDuration(0)
            progress.setAutoClose(True)
            progress.setAutoReset(True)
            progress.setValue(0)
        try:
            for idx, p in enumerate(normal_files, start=1):
                base_name = os.path.basename(p)
                if progress is not None:
                    progress.setLabelText(self._tr("queue_load_label", idx, total, base_name))
                    progress.setValue(idx - 1)
                    QCoreApplication.processEvents()
                    if progress.wasCanceled():
                        self.status_bar.showMessage(self._tr("queue_load_cancelled"))
                        break
                ext = os.path.splitext(p)[1].lower()
                if ext == ".pdf":
                    self.status_bar.showMessage(self._tr("queue_load_pdf_started", base_name))
                    self._start_pdf_render_async(p, dpi=300)
                    added_any = True
                    added_count += 1
                else:
                    if any(it.path == p for it in self.queue_items):
                        if progress is not None:
                            progress.setValue(idx)
                        continue
                    self._add_file_to_queue_single(p)
                    added_any = True
                    last_added = p
                    added_count += 1
                if progress is not None:
                    progress.setValue(idx)
                    QCoreApplication.processEvents()
                    if progress.wasCanceled():
                        self.status_bar.showMessage(self._tr("queue_load_cancelled"))
                        break
        finally:
            if progress is not None:
                progress.close()
        if added_any and last_added:
            self.preview_image(last_added)
        if added_any:
            self._log(self._tr_log("log_added_files", added_count))
        self._fit_queue_columns_exact()
        self._update_queue_hint()

    def _add_file_to_queue_single(
            self,
            path: str,
            display_name: Optional[str] = None,
            source_kind: str = "image"
    ):
        item = TaskItem(
            path=path,
            display_name=display_name or os.path.basename(path),
            source_kind=source_kind
        )
        self.queue_items.append(item)
        row = self.queue_table.rowCount()
        self.queue_table.insertRow(row)
        num_item = QTableWidgetItem(str(row + 1))
        num_item.setTextAlignment(Qt.AlignCenter)
        num_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        name_item = QTableWidgetItem(item.display_name)
        name_item.setData(Qt.UserRole, path)
        name_item.setFlags(
            Qt.ItemIsEnabled
            | Qt.ItemIsSelectable
            | Qt.ItemIsEditable
        )
        status_item = QTableWidgetItem(f"{STATUS_ICONS[STATUS_WAITING]} {self._tr('status_waiting')}")
        status_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.queue_table.setItem(row, QUEUE_COL_NUM, num_item)
        self.queue_table.setCellWidget(row, QUEUE_COL_CHECK, self._make_queue_checkbox_widget(False))
        self.queue_table.setItem(row, QUEUE_COL_FILE, name_item)
        self.queue_table.setItem(row, QUEUE_COL_STATUS, status_item)
        self.queue_table.selectRow(row)
        self._refresh_queue_numbers()
        self._update_queue_check_header()

    def on_item_changed(self, item: QTableWidgetItem):
        if item.column() == QUEUE_COL_CHECK:
            self._update_queue_check_header()
            return
        if item.column() == QUEUE_COL_FILE:
            row = item.row()
            path_item = self.queue_table.item(row, QUEUE_COL_FILE)
            if not path_item:
                return
            path = path_item.data(Qt.UserRole)
            task_item = next((t for t in self.queue_items if t.path == path), None)
            if task_item:
                task_item.display_name = item.text()
