"""Mixin für MainWindow: hardware status and file drop."""
from ...shared import *
from ...ui_components import *
from ...workers import *
from ...dialogs import *
from ...image_edit import *

class HardwareSnapshotWorker(QThread):
    done = Signal(dict)
    failed = Signal(str)

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner

    def run(self):
        try:
            try:
                clear_external_ocr_backend_cache()
            except Exception:
                pass
            snapshot = self.owner._hardware_snapshot(refresh_backends=True)
            self.done.emit(snapshot)
        except Exception as exc:
            self.failed.emit(repr(exc))

class MainWindowPdfRenderQueueMixin:
        def _start_pdf_render_async(self, pdf_path: str, dpi: int = 300):
            # falls schon ein PDF gerendert wird: optional blockieren oder queue’n
            if self.pdf_worker and self.pdf_worker.isRunning():
                QMessageBox.information(self, self._tr("info_title"),
                                        self._tr("msg_pdf_render_already_running"))
                return
            self._pending_pdf_path = pdf_path
            self._set_progress_busy()
            base_name = os.path.basename(pdf_path)
            # Freundlicher Warte-Dialog mit animiertem Kreis statt statischem ProgressDialog.
            # Die eigentlichen Seitenfortschritte bleiben zusätzlich in Statusleiste und Haupt-Fortschrittsbalken sichtbar.
            dlg = BusyStatusDialog(
                self._tr("pdf_render_title"),
                self._tr("pdf_render_busy_message", base_name),
                self._tr,
                self,
            )
            dlg.cancel_requested.connect(self._cancel_pdf_render)
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
            base_name = os.path.basename(pdf_path)
            if dlg:
                # Kompatibel zu altem QProgressDialog und neuem BusyStatusDialog.
                if hasattr(dlg, "setMaximum") and hasattr(dlg, "maximum"):
                    try:
                        if dlg.maximum() != max(1, total):
                            dlg.setMaximum(max(1, total))
                    except Exception:
                        pass
                try:
                    status_text = self._tr("pdf_render_label", cur, total, base_name)
                except Exception:
                    status_text = f"Rendering pages… ({cur}/{total}): {base_name}"
                if hasattr(dlg, "setLabelText"):
                    try:
                        dlg.setLabelText(status_text)
                    except Exception:
                        pass
                elif hasattr(dlg, "set_status"):
                    try:
                        dlg.set_status(status_text)
                    except Exception:
                        pass
                if hasattr(dlg, "setValue"):
                    try:
                        dlg.setValue(cur)
                    except Exception:
                        pass
            self.progress_bar.setRange(0, max(1, total))
            self.progress_bar.setValue(cur)
            self.status_bar.showMessage(self._tr("pdf_render_label", cur, total, base_name))

        def _on_pdf_render_finished(self, pdf_path: str, out_paths: list):
            # Dialog schließen
            if self.pdf_progress_dlg:
                try:
                    if hasattr(self.pdf_progress_dlg, "setValue") and hasattr(self.pdf_progress_dlg, "maximum"):
                        self.pdf_progress_dlg.setValue(self.pdf_progress_dlg.maximum())
                except Exception:
                    pass
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
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_pdf_render_failed", msg))

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
