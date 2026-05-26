"""Mixin für MainWindow: whisper download help and image edit queue."""
from ...shared import *
from ...ui_components import *
from ...workers import *
from ...dialogs import *
from ...image_edit import *

class MainWindowImageEditQueueMixin:
        def _edited_images_output_dir(self, source_task: TaskItem) -> str:
            """
            Sammelordner für bearbeitete Bilder im gleichen Verzeichnis
            wie die Ursprungsdatei.
            """
            src_dir = os.path.dirname(os.path.abspath(source_task.path))
            out_dir = os.path.join(src_dir, "Bottled Kraken - edited pictures")
            os.makedirs(out_dir, exist_ok=True)
            return out_dir

        def _normalized_edited_image_base_name(self, source_task: TaskItem) -> str:
            """
            Liefert den stabilen Basisnamen für bearbeitete Bilder.

            Zielschema:
                originalname_edit_X_Y.png

            Dabei ist X die Bearbeitungs-/Versionsnummer für dieselbe Ursprungsdatei
            und Y die laufende Nummer innerhalb derselben Bearbeitungsrunde.
            """
            stem = os.path.splitext(os.path.basename(source_task.path))[0]
            # Neues Schema: originalname_edit_2_1 -> originalname
            stem = re.sub(r'_edit_\d+_\d+$', '', stem)
            # Altes Schema: original__edit_irgendwas -> original
            stem = re.sub(r'__edit_.*$', '', stem)
            return re.sub(r'[^A-Za-z0-9._-]+', '_', stem).strip('._') or "bild"

        def _next_edited_image_version(self, source_task: TaskItem) -> int:
            """
            Ermittelt die nächste freie Versionsnummer X für Dateien nach dem Schema
            originalname_edit_X_Y.png im Bearbeitungsordner.
            """
            edit_dir = self._edited_images_output_dir(source_task)
            base_name = self._normalized_edited_image_base_name(source_task)
            pattern = re.compile(rf'^{re.escape(base_name)}_edit_(\d+)_(\d+)\.png$', re.IGNORECASE)
            max_version = 0
            try:
                for entry in os.listdir(edit_dir):
                    match = pattern.match(entry)
                    if not match:
                        continue
                    try:
                        max_version = max(max_version, int(match.group(1)))
                    except Exception:
                        pass
            except Exception:
                pass
            return max_version + 1

        def _save_edited_image_under_original(
                self,
                source_task: TaskItem,
                pil_image: Image.Image,
                file_stem: str
        ) -> str:
            edit_dir = self._edited_images_output_dir(source_task)
            safe_stem = re.sub(r'[^A-Za-z0-9._-]+', '_', file_stem).strip('._') or "bild_edit_1_1"
            out_path = os.path.join(edit_dir, f"{safe_stem}.png")
            pil_image.convert("RGB").save(out_path, format="PNG")
            return out_path

        def _insert_task_row(self, row: int, task: TaskItem):
            row = max(0, min(row, self.queue_table.rowCount()))
            self.queue_items.insert(row, task)
            self.queue_table.insertRow(row)
            num_item = QTableWidgetItem(str(row + 1))
            num_item.setTextAlignment(Qt.AlignCenter)
            num_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            name_item = QTableWidgetItem(task.display_name)
            name_item.setData(Qt.UserRole, task.path)
            name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
            status_item = QTableWidgetItem()
            status_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.queue_table.setItem(row, QUEUE_COL_NUM, num_item)
            self.queue_table.setCellWidget(row, QUEUE_COL_CHECK, self._make_queue_checkbox_widget(False))
            self.queue_table.setItem(row, QUEUE_COL_FILE, name_item)
            self.queue_table.setItem(row, QUEUE_COL_STATUS, status_item)
            self._update_queue_row(task.path)

        def _selected_or_checked_tasks_for_edit(self) -> List[TaskItem]:
            checked = self._checked_queue_tasks()
            if checked:
                return checked
            return self._selected_queue_tasks()

        def _create_edited_tasks_from_images(
                self,
                source_task: TaskItem,
                result_images: List[Image.Image]
        ) -> List[TaskItem]:
            created = []
            total = max(1, len(result_images))
            base_name = self._normalized_edited_image_base_name(source_task)
            version = self._next_edited_image_version(source_task)
            edit_dir = self._edited_images_output_dir(source_task)
            while True:
                candidate_paths = [
                    os.path.join(edit_dir, f"{base_name}_edit_{version}_{idx}.png")
                    for idx in range(1, total + 1)
                ]
                if not any(os.path.exists(p) for p in candidate_paths):
                    break
                version += 1
            for idx, img in enumerate(result_images, start=1):
                file_stem = f"{base_name}_edit_{version}_{idx}"
                out_path = self._save_edited_image_under_original(
                    source_task=source_task,
                    pil_image=img,
                    file_stem=file_stem
                )
                new_task = TaskItem(
                    path=out_path,
                    display_name=os.path.basename(out_path),
                    status=STATUS_WAITING,
                    edited=False,
                    source_kind="image",
                    relative_path=""
                )
                # IMMER ans Ende der Queue
                end_row = self.queue_table.rowCount()
                self._insert_task_row(end_row, new_task)
                created.append(new_task)
            return created

        def _apply_image_edit_settings_to_task(self, task: TaskItem, settings: ImageEditSettings) -> List[Image.Image]:
            img = _load_image_color(task.path)
            dlg = ImageEditDialog(img, task.display_name, self)
            dlg.set_settings(settings)
            dlg._accept_dialog()
            return list(dlg.result_images or [])
