"""Mixin für MainWindow: line editing and overlay sync."""
from ...shared import *
from ...ui_components import *
from ...workers import *
from ...dialogs import *
from ...image_edit import *
from PySide6.QtWidgets import QButtonGroup, QGridLayout, QWidget

class MainWindowOverlayExportFlowMixin:
        def on_export_file_started(self, display_name: str, current: int, total: int):
            task = next((i for i in self.queue_items if i.display_name == display_name), None)
            if task:
                task.status = STATUS_EXPORTING
                self._update_queue_row(task.path)

        def export_flow(self, fmt: str):
            if fmt == "pdf":
                self._export_pdf_flow()
                return

            checked_tasks = self._checked_queue_tasks()
            selected_tasks = self._selected_queue_tasks()
            # Priorität: Checkmarks vor Auswahl
            target_tasks = checked_tasks if checked_tasks else selected_tasks
            if target_tasks:
                # genau 1 Datei -> normaler "Speichern unter"-Dialog
                if len(target_tasks) == 1:
                    it = target_tasks[0]
                    if it.status != STATUS_DONE or not it.results:
                        QMessageBox.warning(self, self._tr("warn_title"), self._tr("export_need_done"))
                        return
                    self._export_single_interactive(it, fmt)
                    return
                # mehrere Dateien -> Batch-Export in Ordner
                items = []
                for it in target_tasks:
                    if it.status != STATUS_DONE or not it.results:
                        QMessageBox.warning(self, self._tr("warn_title"), self._tr("export_need_done"))
                        return
                    items.append(it)
                self._export_batch(items, fmt)
                return
            if len(self.queue_items) == 0:
                QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_queue_empty"))
                return
            if len(self.queue_items) == 1:
                it = self.queue_items[0]
                if it.status != STATUS_DONE or not it.results:
                    QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_select_done"))
                    return
                self._export_single_interactive(it, fmt)
                return
            dlg = ExportModeDialog(self._tr, self)
            if dlg.exec() != QDialog.Accepted or dlg.choice is None:
                return
            if dlg.choice == "all":
                items = [it for it in self.queue_items if it.status == STATUS_DONE and it.results]
                if len(items) != len(self.queue_items):
                    QMessageBox.warning(self, self._tr("warn_title"), self._tr("export_need_done"))
                    return
                self._export_batch(items, fmt)
                return
            sel_dlg = ExportSelectFilesDialog(self._tr, self.queue_items, self)
            if sel_dlg.exec() != QDialog.Accepted:
                return
            paths = sel_dlg.selected_paths
            if not paths:
                QMessageBox.information(self, self._tr("info_title"), self._tr("export_none_selected"))
                return
            items = []
            for p in paths:
                it = next((x for x in self.queue_items if x.path == p), None)
                if not it or it.status != STATUS_DONE or not it.results:
                    QMessageBox.warning(self, self._tr("warn_title"), self._tr("export_need_done"))
                    return
                items.append(it)
            if len(items) == 1:
                self._export_single_interactive(items[0], fmt)
            else:
                self._export_batch(items, fmt)
