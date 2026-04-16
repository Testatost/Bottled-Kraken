"""Mixin für MainWindow: toolbar icons and local server models."""
from ..shared import *
from ..ui_components import *
from ..workers import *
from ..dialogs import *
from ..image_edit import *

class MainWindowToolbarIconsAndLocalServerModelsMixin:
    def _set_secondary_button_icons(self):
        def themed_or_standard(theme_name: str, std_icon):
            icon = QIcon.fromTheme(theme_name)
            if icon.isNull():
                icon = self.style().standardIcon(std_icon)
            return icon
        if hasattr(self, "btn_import_lines"):
            self.btn_import_lines.setIcon(
                themed_or_standard("document-import", QStyle.SP_DialogOpenButton)
            )
        if hasattr(self, "btn_voice_fill"):
            self.btn_voice_fill.setIcon(
                self._tinted_theme_or_standard_icon("audio-input-microphone", QStyle.SP_MediaVolume)
            )
        if hasattr(self, "btn_ai_revise_bottom"):
            self.btn_ai_revise_bottom.setIcon(
                themed_or_standard("preferences-system", QStyle.SP_ComputerIcon)
            )
        if hasattr(self, "btn_line_search"):
            self.btn_line_search.setIcon(
                self._tinted_theme_or_standard_icon("system-search", QStyle.SP_FileDialogContentsView)
            )
        if hasattr(self, "btn_clear_queue"):
            self.btn_clear_queue.setIcon(
                self._tinted_theme_or_standard_icon("edit-clear", QStyle.SP_DialogResetButton)
            )
        if hasattr(self, "btn_toggle_log"):
            self.btn_toggle_log.setIcon(
                themed_or_standard("text-x-log", QStyle.SP_FileDialogDetailedView)
            )

    def _scan_kraken_models(self):
        self.kraken_rec_models = []
        self.kraken_seg_models = []
        self.kraken_unknown_models = []
        model_dir = KRAKEN_MODELS_DIR
        if not os.path.isdir(model_dir):
            return
        candidates = []
        seen_names = set()
        for root, _dirs, files in os.walk(model_dir):
            for name in files:
                ext = os.path.splitext(name)[1].lower()
                # nur noch .mlmodel
                if ext != ".mlmodel":
                    continue
                full = os.path.join(root, name)
                # Dubletten über Dateinamen rausfiltern
                key = name.lower()
                if key in seen_names:
                    continue
                seen_names.add(key)
                candidates.append(full)
        for full in sorted(candidates, key=lambda p: os.path.basename(p).lower()):
            kind = self._classify_kraken_model_file(full)
            if kind == "rec":
                self.kraken_rec_models.append(full)
            elif kind == "seg":
                self.kraken_seg_models.append(full)
            else:
                self.kraken_unknown_models.append(full)

    def _load_default_segmentation_model(self):
        if self.seg_model_path and os.path.exists(self.seg_model_path):
            return
        if not self.kraken_seg_models:
            return
        preferred = next(
            (p for p in self.kraken_seg_models if "blla" in os.path.basename(p).lower()),
            self.kraken_seg_models[0]
        )
        self.seg_model_path = preferred

    def _model_type_to_text(self, model_type) -> str:
        if isinstance(model_type, (list, tuple, set)):
            return " ".join(str(x) for x in model_type if x).strip().lower()
        return str(model_type or "").strip().lower()

    def _classify_kraken_model_file(self, model_path: str) -> str:
        """
        Gibt zurück:
            "rec"      -> Recognition-Modell
            "seg"      -> Segmentierungs-Modell
            "unknown"  -> nicht sicher bestimmbar
        """
        # 1) Primär: echtes Kraken-Metadatum lesen
        try:
            nn = vgsl.TorchVGSLModel.load_model(model_path)
            model_type = self._model_type_to_text(getattr(nn, "model_type", ""))
            if "recognition" in model_type:
                return "rec"
            if any(x in model_type for x in ("segmentation", "baseline", "region")):
                return "seg"
        except Exception:
            pass
        # 2) Fallback nur für alte / unklare Modelle
        lname = os.path.basename(model_path).lower()
        if any(x in lname for x in ("blla", "seg", "segment", "baseline", "region")):
            return "seg"
        if any(x in lname for x in ("rec", "recognition", "ocr", "htr", "handwriting", "print")):
            return "rec"
        return "unknown"

    def _set_scanned_rec_model(self, model_path: str):
        if not model_path or not os.path.exists(model_path):
            return
        self.model_path = model_path
        self.last_rec_model_dir = os.path.dirname(model_path)
        self.settings.setValue("paths/last_rec_model_dir", self.last_rec_model_dir)
        self.btn_rec_model.setText(self._tr("btn_rec_model_value", os.path.basename(model_path)))
        self.status_bar.showMessage(self._tr("msg_loaded_rec", os.path.basename(model_path)))
        self._update_models_menu_labels()
        self._update_model_clear_buttons()

    def _set_scanned_seg_model(self, model_path: str):
        if not model_path or not os.path.exists(model_path):
            return
        self.seg_model_path = model_path
        self.last_seg_model_dir = os.path.dirname(model_path)
        self.settings.setValue("paths/last_seg_model_dir", self.last_seg_model_dir)
        self.btn_seg_model.setText(self._tr("btn_seg_model_value", os.path.basename(model_path)))
        self.status_bar.showMessage(self._tr("msg_loaded_seg", os.path.basename(model_path)))
        self._update_models_menu_labels()
        self._update_model_clear_buttons()

    def _rebuild_kraken_models_submenu(self):
        if not hasattr(self, "kraken_models_submenu"):
            return
        self.kraken_models_submenu.clear()
        has_any = False
        if self.kraken_rec_models:
            header_rec = QAction(self._tr("header_rec_models"), self)
            header_rec.setEnabled(False)
            self.kraken_models_submenu.addAction(header_rec)
            for model_path in self.kraken_rec_models:
                name = os.path.basename(model_path)
                act = QAction(name, self)
                act.setCheckable(True)
                act.setChecked(os.path.abspath(model_path) == os.path.abspath(self.model_path or ""))
                act.triggered.connect(lambda checked, mp=model_path: self._set_scanned_rec_model(mp))
                self.kraken_models_submenu.addAction(act)
            has_any = True
        if self.kraken_seg_models:
            if has_any:
                self.kraken_models_submenu.addSeparator()
            header_seg = QAction(self._tr("header_seg_models"), self)
            header_seg.setEnabled(False)
            self.kraken_models_submenu.addAction(header_seg)
            for model_path in self.kraken_seg_models:
                name = os.path.basename(model_path)
                act = QAction(name, self)
                act.setCheckable(True)
                act.setChecked(os.path.abspath(model_path) == os.path.abspath(self.seg_model_path or ""))
                act.triggered.connect(lambda checked, mp=model_path: self._set_scanned_seg_model(mp))
                self.kraken_models_submenu.addAction(act)
            has_any = True
        if not has_any:
            empty_act = QAction(self._tr("no_models_scan"), self)
            empty_act.setEnabled(False)
            self.kraken_models_submenu.addAction(empty_act)
        self.kraken_models_submenu.addSeparator()
        self.kraken_models_submenu.addAction(self.act_clear_rec)
        self.kraken_models_submenu.addAction(self.act_clear_seg)

    def _update_kraken_menu_status(self):
        rec_name = os.path.basename(self.model_path) if self.model_path else "-"
        seg_name = os.path.basename(self.seg_model_path) if self.seg_model_path else "-"
        if hasattr(self, "act_rec_status"):
            self.act_rec_status.setText(self._tr("status_rec_model", rec_name))
        if hasattr(self, "act_seg_status"):
            self.act_seg_status.setText(self._tr("status_seg_model", seg_name))

    def choose_rec_model_from_scanned(self):
        if not getattr(self, "kraken_rec_models", None):
            QMessageBox.warning(self, self._tr("warn_title"), "Keine Recognition-Modelle gefunden.")
            return
        names = [os.path.basename(p) for p in self.kraken_rec_models]
        current_name = os.path.basename(self.model_path) if self.model_path else names[0]
        selected, ok = QInputDialog.getItem(
            self,
            self._tr("dlg_choose_rec"),
            "Recognition-Modell auswählen:",
            names,
            max(0, names.index(current_name)) if current_name in names else 0,
            False
        )
        if not ok or not selected:
            return
        for p in self.kraken_rec_models:
            if os.path.basename(p) == selected:
                self.model_path = p
                break
        self.btn_rec_model.setText(self._tr("btn_rec_model_value", os.path.basename(self.model_path)))
        self._update_models_menu_labels()
        self._update_model_clear_buttons()

    def _detect_local_openai_server(self, force: bool = False) -> Tuple[Optional[str], Optional[str]]:
        now = time.monotonic()
        if not force:
            age = now - float(self._ai_server_cache.get("ts", 0.0))
            if age < self._ai_server_cache_ttl:
                return self._ai_server_cache.get("base_url"), self._ai_server_cache.get("model_id")
        candidates = [
            "http://127.0.0.1:1234/v1",  # LM Studio
            "http://127.0.0.1:8000/v1",  # vLLM
            "http://127.0.0.1:8080/v1",
        ]
        for base_url in candidates:
            models, active = self._fetch_models_from_base_url(base_url, timeout=0.35)
            if models:
                self._ai_server_cache = {
                    "ts": now,
                    "base_url": base_url,
                    "model_id": active or models[0],
                }
                return base_url, (active or models[0])
        self._ai_server_cache = {
            "ts": now,
            "base_url": None,
            "model_id": None,
        }
        return None, None

    def _check_ai_server(self) -> bool:
        base_url, model_id = self._detect_local_openai_server()
        return bool(base_url and model_id)

    def _fetch_loaded_llm_name(self) -> str:
        base_url, model_id = self._detect_local_openai_server()
        return model_id or "-"

    def _refresh_ai_endpoint_from_localhost(self, force: bool = False):
        if self.ai_manual_base_url:
            base_url = self._normalize_ai_base_url(self.ai_manual_base_url)
            if not base_url:
                self.ai_base_url = None
                self.ai_mode = "manual"
                self._update_ai_model_ui()
                return
            self.ai_base_url = base_url
            self.ai_endpoint = base_url + "/chat/completions"
            self.ai_mode = "manual"
            self._update_ai_model_ui()
            return
        base_url, _ = self._detect_local_openai_server(force=force)
        if base_url:
            self.ai_base_url = base_url
            self.ai_endpoint = base_url + "/chat/completions"
        else:
            self.ai_base_url = None
        self.ai_mode = "auto"
        self._update_ai_model_ui()

    def _resolve_ai_model_id(self) -> str:
        self._refresh_ai_endpoint_from_localhost()
        model_id = (self.ai_model_id or "").strip()
        if model_id:
            return model_id
        return ""

    def refresh_models_menu_status(self):
        model_name = self._get_active_ai_model_display()
        mode_label = self._current_ai_mode_label()
        base_url = self.ai_base_url if (self.ai_base_url and self.ai_model_id) else "-"
        if hasattr(self, "act_lm_status"):
            self.act_lm_status.setText(self._tr("lm_status_model_value", model_name))
        if hasattr(self, "act_lm_mode"):
            self.act_lm_mode.setText(self._tr("lm_mode_value", mode_label))
        if hasattr(self, "act_lm_base_url"):
            self.act_lm_base_url.setText(self._tr("lm_server_value", base_url))
        if hasattr(self, "act_clear_manual_lm_url"):
            self.act_clear_manual_lm_url.setEnabled(self.ai_mode == "manual" and bool(self.ai_manual_base_url))
        self._update_ai_model_ui()

    def _fetch_models_from_base_url(self, base_url: str, timeout: float = 0.6) -> Tuple[List[str], str]:
        if not base_url:
            return [], ""
        try:
            req = urllib.request.Request(
                base_url.rstrip("/") + "/models",
                headers={"Authorization": "Bearer local"},
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                data = json.loads(raw)
            models_data = data.get("data", [])
            if not isinstance(models_data, list):
                return [], ""
            out = []
            for m in models_data:
                if not isinstance(m, dict):
                    continue
                mid = str(m.get("id", "")).strip()
                if mid:
                    out.append(mid)
            # Reihenfolge erhalten, Duplikate entfernen
            seen = set()
            uniq = []
            for mid in out:
                if mid not in seen:
                    seen.add(mid)
                    uniq.append(mid)
            active = uniq[0] if uniq else ""
            return uniq, active
        except Exception:
            return [], ""

    def _tr(self, key: str, *args):
        lang = getattr(self, "current_lang", "de")
        return translation.translate(lang, key, *args)

    def _detect_system_lang(self) -> str:
        # z. B. "de_DE", "en_US", "fr_FR"
        name = QLocale.system().name().lower()
        if name.startswith("de"):
            return "de"
        if name.startswith("fr"):
            return "fr"
        return "en"

    def _tr_in(self, lang: str, key: str, *args):
        return translation.translate(lang, key, *args)

    def _tr_log(self, key: str, *args):
        return self._tr_in(self.log_lang, key, *args)

    def _delete_queue_via_key(self):
        # Löscht selektierte Zeilen und setzt danach die Vorschau zurück
        self.delete_selected_queue_items(reset_preview=True)

    def run_ai_revision_for_selected(self):
        selected = self._selected_queue_tasks()
        if selected:
            items = [it for it in selected if it.status == STATUS_DONE and it.results]
        else:
            items = [it for it in self.queue_items if it.status == STATUS_DONE and it.results]
        if not items:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
            return
        self._run_ai_revision_batch(items)

    def run_ai_revision_for_all(self):
        items = [it for it in self.queue_items if it.status == STATUS_DONE and it.results]
        if not items:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
            return
        self._run_ai_revision_batch(items)

    def on_ai_batch_file_started(self, path: str, current: int, total: int):
        task = next((i for i in self.queue_items if i.path == path), None)
        if task:
            if task.results:
                task.lm_locked_bboxes = [tuple(rv.bbox) if rv.bbox else None for rv in task.results[3]]
            task.status = STATUS_AI_PROCESSING
            self._update_queue_row(path)

    def _cancel_ai_batch_revision(self):
        if hasattr(self, "ai_batch_worker") and self.ai_batch_worker and self.ai_batch_worker.isRunning():
            self.ai_batch_worker.cancel()

    @staticmethod
    def _snapshot_recs(recs: List[RecordView]) -> List[Tuple[str, Optional[Tuple[int, int, int, int]]]]:
        return [(rv.text, rv.bbox) for rv in recs]

    @staticmethod
    def _restore_recs(snapshot: List[Tuple[str, Optional[Tuple[int, int, int, int]]]]) -> List[RecordView]:
        recs: List[RecordView] = []
        for i, (t, bb) in enumerate(snapshot):
            recs.append(RecordView(i, t, bb))
        return recs

    def _push_undo(self, task: TaskItem):
        if not task.results:
            return
        _, _, _, recs = task.results
        sel = self.list_lines.currentRow()
        snap: UndoSnapshot = (self._snapshot_recs(recs), int(sel) if sel is not None else -1)
        task.undo_stack.append(snap)
        if len(task.undo_stack) > 300:
            task.undo_stack.pop(0)
        task.redo_stack.clear()

    def _apply_snapshot(self, task: TaskItem, snap: UndoSnapshot):
        if not task.results:
            return
        text, kr_records, im, _recs = task.results
        state, sel = snap
        recs = self._restore_recs(state)
        new_text = "\n".join([r.text for r in recs]).strip()
        task.results = (new_text, kr_records, im, recs)
        task.edited = True
        keep_row = sel if sel is not None else -1
        if keep_row < 0:
            keep_row = 0 if recs else None
        self._sync_ui_after_recs_change(task, keep_row=keep_row)

    def undo(self):
        task = self._current_task()
        if not task or task.status != STATUS_DONE or not task.results:
            self.status_bar.showMessage(self._tr("undo_nothing"))
            return
        if not task.undo_stack:
            self.status_bar.showMessage(self._tr("undo_nothing"))
            return
        _, _, _, recs = task.results
        cur_sel = self.list_lines.currentRow()
        task.redo_stack.append((self._snapshot_recs(recs), int(cur_sel) if cur_sel is not None else -1))
        snap = task.undo_stack.pop()
        self._apply_snapshot(task, snap)

    def redo(self):
        task = self._current_task()
        if not task or task.status != STATUS_DONE or not task.results:
            self.status_bar.showMessage(self._tr("redo_nothing"))
            return
        if not task.redo_stack:
            self.status_bar.showMessage(self._tr("redo_nothing"))
            return
        _, _, _, recs = task.results
        cur_sel = self.list_lines.currentRow()
        task.undo_stack.append((self._snapshot_recs(recs), int(cur_sel) if cur_sel is not None else -1))
        snap = task.redo_stack.pop()
        self._apply_snapshot(task, snap)
