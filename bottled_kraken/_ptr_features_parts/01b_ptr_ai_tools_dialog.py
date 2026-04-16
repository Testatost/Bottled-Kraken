class PtrAIToolsDialog(QDialog):
    merge_completed = Signal(str)
    postgres_completed = Signal(dict)
    neo4j_completed = Signal(dict)
    pipeline_completed = Signal(str, object, object)
    def __init__(self, parent=None, config: Optional[PtrRemoteAIConfig] = None):
        super().__init__(parent)
        self.setWindowTitle("AI Tools")
        self.resize(1150, 760)
        self._worker: Optional[PtrRemoteAITaskWorker] = None
        self._ocr_inputs: List[str] = []
        self._merged_text: str = ""
        self._existing_result_data = None
        self._build_ui()
        self.set_config(config or PtrRemoteAIConfig())
    def _build_ui(self):
        root = QVBoxLayout(self)
        cfg_wrap = QWidget()
        cfg_form = QFormLayout(cfg_wrap)
        self.provider_edit = QLineEdit("openrouter")
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.model_edit = QLineEdit("openrouter/free")
        self.base_url_edit = QLineEdit("https://openrouter.ai/api/v1")
        self.temp_edit = QLineEdit("0.2")
        self.timeout_edit = QLineEdit("90")
        self.app_name_edit = QLineEdit("Bottled Kraken")
        self.app_url_edit = QLineEdit("")
        cfg_form.addRow("Provider:", self.provider_edit)
        cfg_form.addRow("API key:", self.api_key_edit)
        cfg_form.addRow("Model:", self.model_edit)
        cfg_form.addRow("Base URL:", self.base_url_edit)
        cfg_form.addRow("Temperature:", self.temp_edit)
        cfg_form.addRow("Timeout (s):", self.timeout_edit)
        cfg_form.addRow("App name:", self.app_name_edit)
        cfg_form.addRow("App URL:", self.app_url_edit)
        root.addWidget(cfg_wrap)
        splitter = QSplitter(Qt.Horizontal)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("OCR input variants"))
        self.input_edit = QPlainTextEdit()
        self.input_edit.setPlaceholderText("Mehrere OCR-Varianten werden mit '===== OCR SOURCE =====' getrennt.")
        left_layout.addWidget(self.input_edit)
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(QLabel("Merged text"))
        self.merged_edit = QPlainTextEdit()
        right_layout.addWidget(self.merged_edit)
        right_layout.addWidget(QLabel("Structured JSON / result"))
        self.result_output_edit = QPlainTextEdit()
        right_layout.addWidget(self.result_output_edit)
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([500, 600])
        root.addWidget(splitter, 1)
        row1 = QHBoxLayout()
        self.merge_btn = QPushButton("OCR Merge")
        self.postgres_btn = QPushButton("Generate PostgreSQL JSON")
        self.neo4j_btn = QPushButton("Generate Neo4j JSON")
        self.pipeline_btn = QPushButton("Run Full Pipeline")
        row1.addWidget(self.merge_btn)
        row1.addWidget(self.postgres_btn)
        row1.addWidget(self.neo4j_btn)
        row1.addWidget(self.pipeline_btn)
        root.addLayout(row1)
        row2 = QHBoxLayout()
        self.save_merged_btn = QPushButton("Save merged text")
        self.save_result_btn = QPushButton("Save result")
        self.clear_btn = QPushButton("Clear outputs")
        self.close_btn = QPushButton("Close")
        row2.addWidget(self.save_merged_btn)
        row2.addWidget(self.save_result_btn)
        row2.addWidget(self.clear_btn)
        row2.addStretch(1)
        row2.addWidget(self.close_btn)
        root.addLayout(row2)
        self.merge_btn.clicked.connect(self._on_merge)
        self.postgres_btn.clicked.connect(self._on_postgres)
        self.neo4j_btn.clicked.connect(self._on_neo4j)
        self.pipeline_btn.clicked.connect(self._on_pipeline)
        self.save_merged_btn.clicked.connect(self._save_merged)
        self.save_result_btn.clicked.connect(self._save_result)
        self.clear_btn.clicked.connect(self._clear_outputs)
        self.close_btn.clicked.connect(self.accept)
    def set_config(self, config: PtrRemoteAIConfig):
        self.provider_edit.setText(config.provider_name or "openrouter")
        self.api_key_edit.setText(config.api_key or "")
        self.model_edit.setText(config.model or "openrouter/free")
        self.base_url_edit.setText(config.base_url or "https://openrouter.ai/api/v1")
        self.temp_edit.setText(str(config.temperature))
        self.timeout_edit.setText(str(config.timeout_seconds))
        self.app_name_edit.setText(config.app_name or "Bottled Kraken")
        self.app_url_edit.setText(config.app_url or "")
    def get_config(self) -> PtrRemoteAIConfig:
        def _float(text: str, default: float) -> float:
            try:
                return float(str(text).strip().replace(",", "."))
            except Exception:
                return default
        def _int(text: str, default: int) -> int:
            try:
                return int(float(str(text).strip().replace(",", ".")))
            except Exception:
                return default
        return PtrRemoteAIConfig(
            provider_name=(self.provider_edit.text().strip() or "openrouter"),
            api_key=self.api_key_edit.text().strip(),
            base_url=(self.base_url_edit.text().strip() or "https://openrouter.ai/api/v1"),
            model=(self.model_edit.text().strip() or "openrouter/free"),
            timeout_seconds=_int(self.timeout_edit.text(), 90),
            temperature=_float(self.temp_edit.text(), 0.2),
            app_name=(self.app_name_edit.text().strip() or "Bottled Kraken"),
            app_url=self.app_url_edit.text().strip(),
        )
    def set_ocr_inputs(self, texts: List[str]):
        self._ocr_inputs = [str(t).strip() for t in (texts or []) if str(t).strip()]
        self.input_edit.setPlainText(_ptr_build_merge_input_text(self._ocr_inputs))
    def set_existing_merged_text(self, text: str):
        self._merged_text = (text or "").strip()
        if self._merged_text:
            self.merged_edit.setPlainText(self._merged_text)
    def auto_run(self, mode: str):
        mode = (mode or "").strip().lower()
        if mode == "merge":
            QTimer.singleShot(0, self._on_merge)
        elif mode == "postgres":
            QTimer.singleShot(0, self._on_postgres)
        elif mode == "neo4j":
            QTimer.singleShot(0, self._on_neo4j)
        elif mode in ("both", "pipeline"):
            QTimer.singleShot(0, self._on_pipeline)
    def _collect_ocr_inputs(self) -> List[str]:
        raw = self.input_edit.toPlainText().strip()
        if raw:
            parts = [p.strip() for p in raw.split(OCR_SOURCE_SEPARATOR) if p.strip()]
            if parts:
                return parts
        if self._ocr_inputs:
            return list(self._ocr_inputs)
        merged = self.merged_edit.toPlainText().strip()
        if merged:
            return [merged]
        raise ValueError("No OCR text input available.")
    def _collect_merged_text(self) -> str:
        txt = self.merged_edit.toPlainText().strip() or self._merged_text
        return (txt or "").strip()
    def _set_busy(self, busy: bool):
        for w in [self.merge_btn, self.postgres_btn, self.neo4j_btn, self.pipeline_btn,
                  self.save_merged_btn, self.save_result_btn, self.clear_btn]:
            w.setEnabled(not busy)
        self.setCursor(Qt.WaitCursor if busy else Qt.ArrowCursor)
    def _start_worker(self, mode: str, *, include_postgres: bool = True, include_neo4j: bool = True):
        if self._worker and self._worker.isRunning():
            return
        cfg = self.get_config()
        texts = self._collect_ocr_inputs()
        merged = self._collect_merged_text()
        if mode == "merge":
            merged = ""
        elif mode in ("postgres", "neo4j") and not merged:
            merged = ""
        self._worker = PtrRemoteAITaskWorker(
            mode=mode,
            config=cfg,
            ocr_texts=texts,
            merged_text=merged,
            include_postgres=include_postgres,
            include_neo4j=include_neo4j,
            parent=self,
        )
        self._worker.result_ready.connect(self._on_worker_result)
        self._worker.failed.connect(self._on_worker_failed)
        self._worker.finished.connect(lambda: self._set_busy(False))
        self._set_busy(True)
        self._worker.start()
    def _on_merge(self):
        self._start_worker("merge")
    def _on_postgres(self):
        self._start_worker("postgres")
    def _on_neo4j(self):
        self._start_worker("neo4j")
    def _on_pipeline(self):
        self._start_worker("pipeline", include_postgres=True, include_neo4j=True)
    def _on_worker_result(self, payload):
        mode = str((payload or {}).get("mode", ""))
        merged = str((payload or {}).get("merged_text", "") or "").strip()
        if merged:
            self._merged_text = merged
            self.merged_edit.setPlainText(merged)
        if mode == "merge":
            self.result_output_edit.clear()
            self.merge_completed.emit(merged)
            return
        if mode == "postgres":
            data = payload.get("postgres")
            self._existing_result_data = data
            self.result_output_edit.setPlainText(json.dumps(data, ensure_ascii=False, indent=2))
            if merged:
                self.merge_completed.emit(merged)
            if isinstance(data, dict):
                self.postgres_completed.emit(data)
            return
        if mode == "neo4j":
            data = payload.get("neo4j")
            self._existing_result_data = data
            self.result_output_edit.setPlainText(json.dumps(data, ensure_ascii=False, indent=2))
            if merged:
                self.merge_completed.emit(merged)
            if isinstance(data, dict):
                self.neo4j_completed.emit(data)
            return
        if mode == "pipeline":
            pg = payload.get("postgres")
            neo = payload.get("neo4j")
            shown = neo if isinstance(neo, dict) else pg
            if shown is not None:
                self._existing_result_data = shown
                self.result_output_edit.setPlainText(json.dumps(shown, ensure_ascii=False, indent=2))
            if merged:
                self.merge_completed.emit(merged)
            if isinstance(pg, dict):
                self.postgres_completed.emit(pg)
            if isinstance(neo, dict):
                self.neo4j_completed.emit(neo)
            self.pipeline_completed.emit(merged, pg, neo)
    def _on_worker_failed(self, message: str):
        QMessageBox.critical(self, "AI Tools", str(message))
    def _clear_outputs(self):
        self._merged_text = ""
        self._existing_result_data = None
        self.merged_edit.clear()
        self.result_output_edit.clear()
    def _save_merged(self):
        text = self.merged_edit.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "AI Tools", "No merged text available.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save merged text", "ai_merged.txt", "Text Files (*.txt)")
        if not path:
            return
        if not path.lower().endswith(".txt"):
            path += ".txt"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
    def _save_result(self):
        data = self._existing_result_data
        if data is None:
            txt = self.result_output_edit.toPlainText().strip()
            if txt:
                data = txt
        if data is None:
            QMessageBox.information(self, "AI Tools", "No result available.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save result", "ai_result.json", "JSON Files (*.json);;Text Files (*.txt)")
        if not path:
            return
        if isinstance(data, dict):
            if not path.lower().endswith(".json"):
                path += ".json"
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
        else:
            if not path.lower().endswith(".txt"):
                path += ".txt"
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(str(data))
