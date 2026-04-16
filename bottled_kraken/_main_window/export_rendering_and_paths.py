"""Mixin für MainWindow: export rendering and paths."""
from ..shared import *
from ..ui_components import *
from ..workers import *
from ..dialogs import *
from ..image_edit import *

class MainWindowExportRenderingAndPathsMixin:
    def _export_single_interactive(self, item: TaskItem, fmt: str):
        base_name = os.path.splitext(item.display_name)[0]
        base_dir = self.current_export_dir or os.path.dirname(item.path)
        filters = {
            "txt": "Text (*.txt)",
            "csv": "CSV (*.csv)",
            "json": "JSON (*.json)",
            "alto": "XML (*.xml)",
            "hocr": "HTML (*.html)",
            "pdf": "PDF (*.pdf)"
        }
        dest_path, _ = QFileDialog.getSaveFileName(
            self,
            self._tr("dlg_save"),
            os.path.join(base_dir, base_name),
            filters.get(fmt, "All (*.*)")
        )
        if not dest_path:
            return
        if not dest_path.lower().endswith(f".{fmt}"):
            dest_path += f".{fmt}"
        try:
            self._render_file(dest_path, fmt, item)
        except PermissionError:
            QMessageBox.warning(
                self,
                self._tr("warn_title"),
                f"Die Datei kann nicht geschrieben werden:\n\n{dest_path}\n\n"
                "Möglicherweise ist sie noch in einem anderen Programm geöffnet."
            )
            return
        except Exception as e:
            QMessageBox.critical(self, self._tr("err_title"), str(e))
            return
        self._log(self._tr_log("log_export_single", item.display_name, dest_path))
        self.status_bar.showMessage(self._tr("msg_exported", os.path.basename(dest_path)))

    def _export_batch(self, items: List[TaskItem], fmt: str):
        folder = QFileDialog.getExistingDirectory(
            self,
            self._tr("export_choose_folder"),
            self.current_export_dir or ""
        )
        if not folder:
            return
        self.current_export_dir = folder
        self._current_export_count = len(items)
        self._current_export_format = fmt
        self.export_dialog = ProgressStatusDialog(f"Export {fmt.upper()}", self)
        self.export_dialog.set_status("Bereite Export vor…")
        self.export_dialog.cancel_requested.connect(self._cancel_export_batch)
        self.export_dialog.show()
        self.export_worker = ExportWorker(
            render_callback=self._render_file,
            items=items,
            fmt=fmt,
            folder=folder,
            parent=self
        )
        self.export_worker.status_changed.connect(self.export_dialog.set_status)
        self.export_worker.progress_changed.connect(self.export_dialog.set_progress)
        self.export_worker.file_done.connect(self.on_export_file_done)
        self.export_worker.file_started.connect(self.on_export_file_started)
        self.export_worker.file_error.connect(self.on_export_file_error)
        self.export_worker.finished_batch.connect(self.on_export_batch_finished)
        self.export_worker.start()

    def _cancel_export_batch(self):
        if self.export_worker and self.export_worker.isRunning():
            self.export_worker.requestInterruption()

    def on_export_file_done(self, display_name: str, dest_path: str, current: int, total: int):
        task = next((i for i in self.queue_items if i.display_name == display_name), None)
        if task:
            task.status = STATUS_DONE
            self._update_queue_row(task.path)
        self._log(self._tr_log("log_export_single", display_name, dest_path))

    def on_export_file_error(self, display_name: str, msg: str, current: int, total: int):
        task = next((i for i in self.queue_items if i.display_name == display_name), None)
        if task:
            task.status = STATUS_ERROR
            self._update_queue_row(task.path)
        self._log(f"Export-Fehler: {display_name} -> {msg}")

    def on_export_batch_finished(self):
        if self.export_dialog:
            self.export_dialog.close()
            self.export_dialog = None
        self.status_bar.showMessage(self._tr("msg_exported", self.current_export_dir))
        self._log(
            self._tr_log(
                "log_export_done",
                getattr(self, "_current_export_count", 0),
                getattr(self, "_current_export_format", "?"),
                self.current_export_dir
            )
        )

    def _build_kraken_segmentation_for_export(
            self,
            image_path: str,
            record_views: List[RecordView]
    ):
        export_lines = []
        for i, rv in enumerate(record_views):
            if not rv.bbox:
                continue
            x0, y0, x1, y1 = rv.bbox
            export_lines.append(
                containers.BBoxLine(
                    id=f"line_{i + 1:04d}",
                    bbox=(int(x0), int(y0), int(x1), int(y1)),
                    text=str(rv.text or ""),
                    base_dir=None,
                    imagename=image_path,
                    regions=None,
                    tags=None,
                    split=None,
                    text_direction="horizontal-lr",
                )
            )
        if not export_lines:
            return None
        return containers.Segmentation(
            type="bbox",
            imagename=image_path,
            text_direction="horizontal-lr",
            script_detection=False,
            lines=export_lines,
            regions=None,
            line_orders=None,
        )

    def _render_hocr_html(self, path: str, item: TaskItem, export_image: Image.Image, record_views: List[RecordView]):
        buf = BytesIO()
        export_image.save(buf, format="PNG")
        img_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        width, height = export_image.size
        page_name = html.escape(os.path.basename(item.path))
        line_blocks = []
        for i, rv in enumerate(record_views):
            if not rv.bbox:
                continue
            x0, y0, x1, y1 = rv.bbox
            w = max(1, x1 - x0)
            h = max(1, y1 - y0)
            txt = html.escape(rv.text or "")
            line_blocks.append(f"""
            <span class="ocr_line"
                  id="line_{i + 1:04d}"
                  title="bbox {x0} {y0} {x1} {y1}"
                  style="left:{x0}px; top:{y0}px; width:{w}px; height:{h}px;">
                <span class="ocrx_word"
                      id="word_{i + 1:04d}"
                      title="bbox {x0} {y0} {x1} {y1}">{txt}</span>
            </span>
            """)
        html_doc = f"""<!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <meta name="ocr-system" content="Bottled Kraken">
    <meta name="ocr-capabilities" content="ocr_page ocr_line ocrx_word">
    <title>{page_name}</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background: #f3f3f3;
            font-family: Arial, sans-serif;
        }}
        .page-wrap {{
            display: inline-block;
            position: relative;
            box-shadow: 0 2px 16px rgba(0,0,0,0.18);
            background: white;
        }}
        .ocr_page {{
            position: relative;
            width: {width}px;
            height: {height}px;
            overflow: hidden;
            background: white;
        }}
        .ocr_page img {{
            position: absolute;
            left: 0;
            top: 0;
            width: {width}px;
            height: {height}px;
            display: block;
        }}
        .ocr_line {{
            position: absolute;
            box-sizing: border-box;
            border: 1px solid rgba(220, 38, 38, 0.45);
            background: rgba(255, 255, 255, 0.10);
            overflow: hidden;
            white-space: nowrap;
        }}
        .ocrx_word {{
            position: absolute;
            left: 0;
            top: 0;
            font-size: 12px;
            line-height: 1.1;
            color: rgba(180, 0, 0, 0.92);
            background: rgba(255, 255, 255, 0.55);
            padding: 0 2px;
        }}
    </style>
    </head>
    <body>
    <div class="page-wrap">
        <div class="ocr_page" title="image {page_name}; bbox 0 0 {width} {height}">
            <img src="data:image/png;base64,{img_b64}" alt="{page_name}">
            {''.join(line_blocks)}
        </div>
    </div>
    </body>
    </html>
    """
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_doc)

    def _line_export_entry(self, rv: RecordView, fallback_idx: int) -> Dict[str, Any]:
        idx = int(getattr(rv, "idx", fallback_idx))
        entry: Dict[str, Any] = {
            "idx": idx,
            "text": str(getattr(rv, "text", "") or ""),
        }
        if rv.bbox:
            x0, y0, x1, y1 = [int(v) for v in rv.bbox]
            entry.update({
                "x": x0,
                "y": y0,
                "width": max(0, x1 - x0),
                "height": max(0, y1 - y0),
                "bbox": [x0, y0, x1, y1],
            })
        else:
            entry.update({"x": None, "y": None, "width": None, "height": None, "bbox": None})
        return entry

    def _write_structured_txt_export(self, path: str, record_views: List[RecordView]):
        with open(path, "w", encoding="utf-8") as f:
            f.write("# Bottled Kraken line export\n")
            f.write("# idx\tx\ty\twidth\theight\ttext\n")
            for i, rv in enumerate(record_views):
                entry = self._line_export_entry(rv, i)
                cols = [
                    str(entry["idx"]),
                    "" if entry["x"] is None else str(entry["x"]),
                    "" if entry["y"] is None else str(entry["y"]),
                    "" if entry["width"] is None else str(entry["width"]),
                    "" if entry["height"] is None else str(entry["height"]),
                    json.dumps(entry["text"], ensure_ascii=False),
                ]
                f.write("\t".join(cols) + "\n")

    def _render_file(self, path: str, fmt: str, item: TaskItem):
        if not item.results:
            return
        text, kr_records, pil_image, record_views = item.results
        export_image = _load_image_color(item.path)
        if fmt == "txt":
            self._write_structured_txt_export(path, record_views)
            return
        grid = table_to_rows(record_views, pil_image.size[0]) if any(rv.bbox for rv in record_views) else [
            [rv.text] for rv in record_views
        ]
        if fmt == "csv":
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerows(grid)
            return
        if fmt == "json":
            payload = {
                "format": "bottled_kraken_lines",
                "version": 2,
                "image": {
                    "file": os.path.basename(item.path),
                    "width": int(pil_image.size[0]),
                    "height": int(pil_image.size[1]),
                },
                "lines": [self._line_export_entry(rv, i) for i, rv in enumerate(record_views)],
                "rows": grid,
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            return
        if fmt == "alto":
            seg_result = self._build_kraken_segmentation_for_export(
                image_path=item.path,
                record_views=record_views
            )
            if seg_result is None:
                raise ValueError("ALTO-Export benötigt Zeilen mit Bounding-Boxen.")
            xml = serialization.serialize(
                seg_result,
                image_size=export_image.size,
                template="alto"
            )
            with open(path, "w", encoding="utf-8") as f:
                f.write(xml)
            return
        if fmt == "hocr":
            self._render_hocr_html(path, item, export_image, record_views)
            return
        if fmt == "pdf":
            width, height = export_image.size
            c = pdf_canvas.Canvas(path, pagesize=(width, height))
            c.drawImage(ImageReader(export_image), 0, 0, width=width, height=height)
            for rv in record_views:
                if not rv.bbox or not rv.text.strip():
                    continue
                x0, y0, x1, y1 = rv.bbox
                t = rv.text
                box_h = max(1, y1 - y0)
                box_w = max(1, x1 - x0)
                font_size = max(6, min(24, box_h * 0.8))
                c.setFont("Helvetica", font_size)
                pdf_y = height - y1
                text_w = c.stringWidth(t, "Helvetica", font_size)
                scale_x = box_w / text_w if text_w > 0 else 1.0
                c.saveState()
                c.translate(x0, pdf_y)
                c.scale(scale_x, 1.0)
                c.setFillAlpha(0)
                c.drawString(0, 0, t)
                c.restoreState()
            try:
                c.save()
            except PermissionError as e:
                raise PermissionError(
                    f"PDF konnte nicht gespeichert werden:\n{path}\n\n"
                    "Die Datei ist wahrscheinlich noch geöffnet oder durch ein anderes Programm gesperrt."
                ) from e
            return

    def _app_base_dir(self) -> str:
        if getattr(sys, "frozen", False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(sys.argv[0]))

    def _default_whisper_base_dir(self) -> str:
        home = os.path.expanduser("~")
        if sys.platform.startswith("win"):
            base = os.path.join(home, "BottledKraken", "whisper")
        elif sys.platform == "darwin":
            base = os.path.join(home, "Library", "Application Support", "BottledKraken", "whisper")
        else:
            base = os.path.join(home, ".local", "share", "BottledKraken", "whisper")
        os.makedirs(base, exist_ok=True)
        return base

    def _default_whisper_model_dir(self) -> str:
        return os.path.join(self._default_whisper_base_dir(), "faster-whisper-large-v3")

    def _system_python_for_venv_cmd(self) -> List[str]:
        """
        Liefert einen echten Python-Interpreter für das Erzeugen der Whisper-venv.
        In der PyInstaller-EXE darf dafür NICHT sys.executable verwendet werden,
        weil das auf Bottled Kraken.exe zeigt.
        """
        if not getattr(sys, "frozen", False):
            return [sys.executable]

        if sys.platform.startswith("win"):
            py_launcher = shutil.which("py")
            if py_launcher:
                return [py_launcher, "-3.11"]

            python_exe = shutil.which("python")
            if python_exe:
                return [python_exe]

            raise RuntimeError(
                "Kein System-Python für die Whisper-Installation gefunden. "
                "Bitte Python 3.11 installieren oder den Python-Launcher 'py.exe' im PATH verfügbar machen."
            )

        python_exe = shutil.which("python3") or shutil.which("python")
        if python_exe:
            return [python_exe]

        raise RuntimeError(
            "Kein Python-Interpreter für die Whisper-Installation gefunden."
        )

    def _hf_cli_executable(self, platform_name: str) -> str:
        """
        Liefert den festen hf-CLI-Pfad in der Whisper-venv.
        Wichtig: Hier NICHT auf os.path.exists() prüfen und NICHT auf "hf" aus dem PATH zurückfallen,
        weil der Pfad schon vor der Installation zusammengesetzt wird.
        """
        name = (platform_name or "").strip().lower()
        venv_dir = self._whisper_venv_dir()

        if name == "windows":
            return os.path.join(venv_dir, "Scripts", "hf.exe")
        return os.path.join(venv_dir, "bin", "hf")

    def _whisper_venv_dir(self) -> str:
        return os.path.join(self._default_whisper_base_dir(), ".venv")

    def _whisper_venv_python_path(self, platform_name: str) -> str:
        name = (platform_name or "").strip().lower()
        venv_dir = self._whisper_venv_dir()
        if name == "windows":
            return os.path.join(venv_dir, "Scripts", "python.exe")
        return os.path.join(venv_dir, "bin", "python3")

    def _whisper_button_commands(self, platform_name: str) -> Tuple[str, str]:
        """
        Nur für die Anzeige im Hinweise-Dialog.
        Zeigt dem Nutzer die Befehle, die dem echten Ablauf entsprechen.
        """
        name = (platform_name or "").strip().lower()
        model_dir = self._default_whisper_model_dir().replace("\\", "/")
        venv_dir = self._whisper_venv_dir().replace("\\", "/")
        venv_python = self._whisper_venv_python_path(platform_name).replace("\\", "/")
        hf_exe = self._hf_cli_executable(platform_name).replace("\\", "/")

        if name == "windows":
            if getattr(sys, "frozen", False):
                bootstrap_cmd = f'py -3.11 -m venv "{venv_dir}"'
            else:
                bootstrap_cmd = f'"{sys.executable}" -m venv "{venv_dir}"'
        else:
            bootstrap_cmd = f'python3 -m venv "{venv_dir}"'

        install_cmd = (
            f'{bootstrap_cmd}\n'
            f'"{venv_python}" -m pip install -U pip setuptools wheel huggingface_hub faster-whisper sounddevice'
        )
        download_cmd = (
            f'"{hf_exe}" download '
            f'Systran/faster-whisper-large-v3 --local-dir "{model_dir}"'
        )
        return install_cmd, download_cmd
