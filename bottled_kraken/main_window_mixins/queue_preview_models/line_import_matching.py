"""Mixin für MainWindow: queue context preview and model loading."""
from ...shared import *
from ...ui_components import *
from ...workers import *
from ...dialogs import *
from ...image_edit import *

class MainWindowLineImportMatchingMixin:
        def _read_import_lines_file(self, file_path: str) -> List[Any]:
            def _coerce_import_bbox(obj: Any) -> Optional[Tuple[int, int, int, int]]:
                bbox = obj.get("bbox") if isinstance(obj, dict) else None
                if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
                    try:
                        x0, y0, x1, y1 = [int(round(float(v))) for v in bbox]
                        if x1 > x0 and y1 > y0:
                            return x0, y0, x1, y1
                    except Exception:
                        pass
                try:
                    x = obj.get("x")
                    y = obj.get("y")
                    w = obj.get("width")
                    h = obj.get("height")
                    if None not in (x, y, w, h):
                        x, y, w, h = [int(round(float(v))) for v in (x, y, w, h)]
                        if w > 0 and h > 0:
                            return x, y, x + w, y + h
                except Exception:
                    pass
                return None

            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    raw_lines = f.read().splitlines()
                structured = []
                for ln in raw_lines:
                    s = ln.strip()
                    if not s or s.startswith("#"):
                        continue
                    parts = ln.split("	", 5)
                    if len(parts) >= 6:
                        try:
                            text_value = json.loads(parts[5])
                        except Exception:
                            text_value = parts[5]
                        txt = str(text_value).strip()
                        if not txt:
                            continue
                        entry = {
                            "idx": int(parts[0]) if parts[0].strip().lstrip("-").isdigit() else None,
                            "text": txt,
                            "x": parts[1].strip() or None,
                            "y": parts[2].strip() or None,
                            "width": parts[3].strip() or None,
                            "height": parts[4].strip() or None,
                        }
                        structured.append({"text": txt, "bbox": _coerce_import_bbox(entry)})
                if structured:
                    return structured
                return [ln.strip() for ln in raw_lines if ln.strip()]
            if ext == ".json":
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list) and all(isinstance(x, str) for x in data):
                    return [str(x).strip() for x in data if str(x).strip()]
                if isinstance(data, dict):
                    lines = data.get("lines")
                    if isinstance(lines, list):
                        out = []
                        for item in lines:
                            if isinstance(item, dict):
                                txt = str(item.get("text", "") or "").strip()
                                if txt:
                                    out.append({"text": txt, "bbox": _coerce_import_bbox(item)})
                            elif isinstance(item, str):
                                txt = item.strip()
                                if txt:
                                    out.append(txt)
                        if out:
                            return out
                    rows = data.get("rows")
                    if isinstance(rows, list):
                        out = []
                        for row in rows:
                            if isinstance(row, list):
                                txt = " ".join(str(x).strip() for x in row if str(x).strip()).strip()
                                if txt:
                                    out.append(txt)
                            elif isinstance(row, str):
                                txt = row.strip()
                                if txt:
                                    out.append(txt)
                        return out
            raise ValueError(self._tr("warn_import_unsupported_format", file_path))

        def _apply_imported_lines_to_task(self, task: TaskItem, lines: List[Any]):
            entries = []
            for line in lines:
                if isinstance(line, dict):
                    txt = str(line.get("text", "") or "").strip()
                    if txt:
                        entries.append({"text": txt, "bbox": line.get("bbox")})
                else:
                    txt = str(line).strip()
                    if txt:
                        entries.append({"text": txt, "bbox": None})
            if not entries:
                raise ValueError(self._tr("warn_import_no_usable_lines"))
            if task.results:
                old_text, old_kr, old_im, old_recs = task.results
                if len(old_recs) == len(entries):
                    recs = [
                        RecordView(i, entry["text"], entry["bbox"] if entry["bbox"] else old_recs[i].bbox)
                        for i, entry in enumerate(entries)
                    ]
                    im = old_im
                    kr = old_kr
                else:
                    im = None
                    kr = []
                    recs = [RecordView(i, entry["text"], entry["bbox"]) for i, entry in enumerate(entries)]
            else:
                im = None
                kr = []
                recs = [RecordView(i, entry["text"], entry["bbox"]) for i, entry in enumerate(entries)]
            text = "\n".join(entry["text"] for entry in entries).strip()
            task.results = (text, kr, im, recs)
            task.preset_bboxes = [rv.bbox for rv in recs]
            task.status = STATUS_DONE
            task.edited = True
            self._update_queue_row(task.path)
            cur = self._current_task()
            if cur and cur.path == task.path:
                self._sync_ui_after_recs_change(task, keep_row=0)
                if self.list_lines.count() > 0:
                    self.list_lines.setCurrentRow(0)
                    self.list_lines.setFocus()
                    self.canvas.select_idx(0)

        def _match_import_files_to_tasks(self, tasks: List[TaskItem], import_files: List[str]) -> Dict[str, str]:
            file_map = {}
            for fp in import_files:
                stem = os.path.splitext(os.path.basename(fp))[0].lower()
                file_map[stem] = fp
            matches = {}
            for task in tasks:
                path_stem = os.path.splitext(os.path.basename(task.path))[0].lower()
                display_stem = os.path.splitext(task.display_name)[0].lower()
                normalized_display = (
                    display_stem
                    .replace(" – seite ", "_p")
                    .replace(" - seite ", "_p")
                    .replace(" seite ", "_p")
                )
                candidates = {
                    path_stem,
                    display_stem,
                    normalized_display,
                }
                for c in candidates:
                    if c in file_map:
                        matches[task.path] = file_map[c]
                        break
            return matches

        def import_lines_for_current_image(self):
            task = self._current_task()
            if not task:
                QMessageBox.information(self, self._tr("info_title"), self._tr("info_no_current_image_loaded"))
                return
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                self._tr("dlg_import_lines_current"),
                "",
                self._tr("dlg_import_lines_filter")
            )
            if not file_path:
                return
            try:
                lines = self._read_import_lines_file(file_path)
                self._apply_imported_lines_to_task(task, lines)
            except Exception as e:
                QMessageBox.warning(self, self._tr("warn_title"), str(e))

        def import_lines_for_selected_images(self):
            tasks = self._checked_queue_tasks()
            if not tasks:
                tasks = self._selected_queue_tasks()
            if not tasks:
                QMessageBox.information(self, self._tr("info_title"), self._tr("info_no_images_selected_or_marked"))
                return
            files, _ = QFileDialog.getOpenFileNames(
                self,
                self._tr("dlg_import_lines_selected"),
                "",
                self._tr("dlg_import_lines_filter")
            )
            if not files:
                return
            matches = self._match_import_files_to_tasks(tasks, files)
            if not matches:
                QMessageBox.warning(
                    self,
                    self._tr("warn_title"),
                    self._tr("warn_no_matching_import_for_selected")
                )
                return
            for task in tasks:
                fp = matches.get(task.path)
                if not fp:
                    continue
                try:
                    lines = self._read_import_lines_file(fp)
                    self._apply_imported_lines_to_task(task, lines)
                except Exception as e:
                    self._log(self._tr_log("log_import_error", task.display_name, e))
