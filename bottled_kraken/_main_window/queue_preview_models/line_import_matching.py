from bottled_kraken.common import (
    Any,
    Dict,
    List,
    Optional,
    QFileDialog,
    QMessageBox,
    RecordView,
    STATUS_DONE,
    TaskItem,
    Tuple,
    csv,
    json,
    os,
    re,
)
class MainWindowLineImportMatchingMixin:
        def _clean_import_text_value(self, value: Any) -> str:
            if value is None:
                return ""
            if isinstance(value, (dict, list, tuple)):
                return ""
            text = str(value).replace("\r\n", " ").replace("\r", " ").replace("\n", " ").strip()
            if not text:
                return ""
            labeled = re.search(
                r"(?:^|[\s,;|])(?:text|txt|zeile|line)\s*[:=]\s*(.+)$",
                text,
                flags=re.IGNORECASE,
            )
            if labeled:
                text = labeled.group(1).strip()
            text = re.sub(
                r"^\s*(?:idx|index|line|line_no|zeile|nr)\s*[:=]\s*-?\d+\s*[,;|\t ]+",
                "",
                text,
                flags=re.IGNORECASE,
            ).strip()
            text = re.sub(
                r"^\s*(?:(?:x|y|w|h|width|height|breite|hoehe|höhe)\s*[:=]\s*-?\d+(?:\.\d+)?\s*[,;|\t ]*){2,5}",
                "",
                text,
                flags=re.IGNORECASE,
            ).strip()
            numeric_prefix = re.match(
                r"^\s*-?\d+\s+[+-]?\d+(?:\.\d+)?\s+[+-]?\d+(?:\.\d+)?\s+[+-]?\d+(?:\.\d+)?\s+[+-]?\d+(?:\.\d+)?\s+(.+)$",
                text,
            )
            if numeric_prefix:
                text = numeric_prefix.group(1).strip()
            return text.strip(' \t,;|')
        def _coerce_import_bbox(self, obj: Any) -> Optional[Tuple[int, int, int, int]]:
            if not isinstance(obj, dict):
                return None
            bbox = obj.get("bbox")
            if isinstance(bbox, str):
                try:
                    bbox = json.loads(bbox)
                except Exception:
                    parts = re.findall(r"-?\d+(?:\.\d+)?", bbox)
                    bbox = parts[:4] if len(parts) >= 4 else None
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
                w = obj.get("width", obj.get("w"))
                h = obj.get("height", obj.get("h"))
                if None not in (x, y, w, h):
                    x, y, w, h = [int(round(float(v))) for v in (x, y, w, h)]
                    if w > 0 and h > 0:
                        return x, y, x + w, y + h
            except Exception:
                pass
            return None
        def _entry_from_import_object(self, obj: Any) -> Optional[Dict[str, Any]]:
            if isinstance(obj, dict):
                text_value = obj.get("text", obj.get("txt", obj.get("line", obj.get("zeile", ""))))
                text = self._clean_import_text_value(text_value)
                if text:
                    return {"text": text, "bbox": self._coerce_import_bbox(obj)}
                return None
            text = self._clean_import_text_value(obj)
            if text:
                return {"text": text, "bbox": None}
            return None
        def _entry_from_delimited_import_line(self, line: str) -> Optional[Dict[str, Any]]:
            candidates = []
            if "\t" in line:
                candidates.append(line.split("\t"))
            for delimiter in (",", ";"):
                if delimiter in line:
                    try:
                        candidates.extend(list(csv.reader([line], delimiter=delimiter)))
                    except Exception:
                        pass
            for parts in candidates:
                parts = [str(part).strip() for part in parts]
                if len(parts) < 6:
                    continue
                if any(p.lower() in {"idx", "x", "y", "width", "height", "text"} for p in parts[:6]):
                    continue
                first_five = parts[:5]
                if not all(part == "" or re.fullmatch(r"-?\d+(?:\.\d+)?", part) for part in first_five):
                    continue
                text_part = parts[-1] if len(parts) > 6 else parts[5]
                try:
                    text_value = json.loads(text_part)
                except Exception:
                    text_value = text_part
                text = self._clean_import_text_value(text_value)
                if not text:
                    continue
                entry = {
                    "idx": first_five[0] or None,
                    "x": first_five[1] or None,
                    "y": first_five[2] or None,
                    "width": first_five[3] or None,
                    "height": first_five[4] or None,
                    "text": text,
                }
                return {"text": text, "bbox": self._coerce_import_bbox(entry)}
            return None
        def _read_import_lines_file(self, file_path: str) -> List[Any]:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    raw_lines = f.read().splitlines()
                structured = []
                plain = []
                for line in raw_lines:
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#"):
                        continue
                    entry = self._entry_from_delimited_import_line(line)
                    if entry:
                        structured.append(entry)
                        continue
                    if stripped.startswith("{") and stripped.endswith("}"):
                        try:
                            entry = self._entry_from_import_object(json.loads(stripped))
                            if entry:
                                structured.append(entry)
                                continue
                        except Exception:
                            pass
                    entry = self._entry_from_import_object(stripped)
                    if entry:
                        plain.append(entry["text"])
                if structured:
                    return structured
                return plain
            if ext == ".json":
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    out = []
                    for item in data:
                        entry = self._entry_from_import_object(item)
                        if entry:
                            out.append(entry if entry.get("bbox") else entry["text"])
                    if out:
                        return out
                if isinstance(data, dict):
                    for key in ("lines", "records", "items"):
                        lines = data.get(key)
                        if isinstance(lines, list):
                            out = []
                            for item in lines:
                                entry = self._entry_from_import_object(item)
                                if entry:
                                    out.append(entry if entry.get("bbox") else entry["text"])
                            if out:
                                return out
                    rows = data.get("rows")
                    if isinstance(rows, list):
                        out = []
                        for row in rows:
                            if isinstance(row, dict):
                                entry = self._entry_from_import_object(row)
                                if entry:
                                    out.append(entry if entry.get("bbox") else entry["text"])
                            elif isinstance(row, list):
                                text = " ".join(self._clean_import_text_value(x) for x in row if self._clean_import_text_value(x)).strip()
                                if text:
                                    out.append(text)
                            else:
                                entry = self._entry_from_import_object(row)
                                if entry:
                                    out.append(entry["text"])
                        if out:
                            return out
            raise ValueError(self._tr("warn_import_unsupported_format", file_path))
        def _apply_imported_lines_to_task(self, task: TaskItem, lines: List[Any]):
            entries = []
            for line in lines:
                if isinstance(line, dict):
                    txt = self._clean_import_text_value(line.get("text", ""))
                    if txt:
                        entries.append({"text": txt, "bbox": self._coerce_import_bbox(line) or line.get("bbox")})
                else:
                    txt = self._clean_import_text_value(line)
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
                    im = old_im
                    kr = old_kr
                    recs = [
                        RecordView(i, entry["text"], entry["bbox"] or (old_recs[i].bbox if i < len(old_recs) else None))
                        for i, entry in enumerate(entries)
                    ]
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
