"""Mixin für MainWindow: ai server urls and model selection."""
from ..shared import *
from ..ui_components import *
from ..workers import *
from ..dialogs import *
from ..image_edit import *

class MainWindowAiServerUrlsAndModelSelectionMixin:
    def _looks_like_ssh_input(self, raw: str) -> bool:
        txt = (raw or "").strip()
        if not txt:
            return False
        low = txt.lower()
        if low.startswith("ssh "):
            return True
        if low.startswith("ssh://"):
            return True
        # klassisches user@host
        if re.fullmatch(r"[^@\s]+@[^:\s/]+", txt):
            return True
        # host:22 allein soll NICHT automatisch als URL gelten,
        # ist oft ein SSH-Hinweis
        if re.fullmatch(r"[^/\s:]+:\d+", txt):
            try:
                port = int(txt.rsplit(":", 1)[1])
                if port == 22:
                    return True
            except Exception:
                pass
        return False

    def _normalize_ai_base_url(self, raw: str) -> str:
        url = (raw or "").strip()
        if not url:
            return ""
        # Quotes / Whitespace säubern
        url = url.strip().strip('"').strip("'")
        url = re.sub(r"\s+", "", url)
        # SSH-Eingaben hier bewusst NICHT "erraten"
        if self._looks_like_ssh_input(url):
            return ""
        # Fehlendes Schema ergänzen
        if not re.match(r"^https?://", url, flags=re.IGNORECASE):
            url = "http://" + url
        try:
            parsed = urllib.parse.urlparse(url)
        except Exception:
            return ""
        scheme = (parsed.scheme or "http").lower()
        if scheme not in ("http", "https"):
            return ""
        host = parsed.hostname
        if not host:
            return ""
        port = parsed.port
        path = (parsed.path or "").strip()
        path = re.sub(r"/+", "/", path)
        # Häufige Fehlformen auf Base-URL zurückführen
        low_path = path.lower().rstrip("/")
        strip_suffixes = [
            "/v1/chat/completions",
            "/chat/completions",
            "/v1/completions",
            "/completions",
            "/v1/models",
            "/models",
        ]
        for suffix in strip_suffixes:
            if low_path.endswith(suffix):
                path = path[:len(path) - len(suffix)]
                break
        path = path.rstrip("/")
        # Wenn gar kein API-Pfad da ist -> /v1 anhängen
        # Wenn bereits /v1 vorhanden -> so lassen
        # Wenn ein anderer Pfad da ist -> /v1 anhängen
        if not path:
            path = "/v1"
        elif path.lower() != "/v1" and not path.lower().endswith("/v1"):
            path = path + "/v1"
        # Netloc sauber neu aufbauen
        netloc = host
        if port is not None:
            netloc = f"{host}:{port}"
        normalized = urllib.parse.urlunparse((scheme, netloc, path, "", "", ""))
        return normalized

    def set_manual_ai_base_url_dialog(self):
        dlg = QInputDialog(self)
        dlg.setInputMode(QInputDialog.TextInput)
        dlg.setWindowTitle(self._tr("dlg_lm_url_title"))
        dlg.setLabelText(self._tr("dlg_lm_url_label"))
        dlg.setTextValue(self.ai_manual_base_url or "")
        dlg.setOkButtonText(self._tr("btn_ok"))
        dlg.setCancelButtonText(self._tr("btn_cancel"))
        dlg.resize(560, 420)
        line_edit = dlg.findChild(QLineEdit)
        if line_edit is not None:
            line_edit.setPlaceholderText(self._tr("dlg_lm_url_placeholder"))
        if dlg.exec() != QDialog.Accepted:
            return
        raw = (dlg.textValue() or "").strip()
        if self._looks_like_ssh_input(raw):
            QMessageBox.warning(
                self,
                self._tr("warn_title"),
                self._tr("warn_lm_url_no_ssh")
            )
            return
        normalized = self._normalize_ai_base_url(raw)
        if not normalized:
            QMessageBox.warning(
                self,
                self._tr("warn_title"),
                self._tr("warn_lm_url_invalid")
            )
            return
        self.ai_manual_base_url = normalized
        self.ai_mode = "manual"
        self.ai_base_url = normalized
        self.ai_endpoint = normalized + "/chat/completions"
        self._reset_ai_server_cache()
        models, detected_model_id = self._fetch_models_from_base_url(self.ai_base_url, timeout=0.6)
        self.ai_available_models = models
        if models:
            self.ai_model_id = detected_model_id if detected_model_id in models else models[0]
            self.status_bar.showMessage(self._tr("msg_lm_found_url", self.ai_model_id, normalized))
        else:
            self.ai_model_id = ""
            self.status_bar.showMessage(self._tr("msg_lm_no_models_url", normalized))
        self._rebuild_ai_model_submenu()
        self.refresh_models_menu_status()

    def _fetch_server_active_model_id(self, base_url: str, timeout: float = 0.6) -> str:
        _, active = self._fetch_models_from_base_url(base_url, timeout=timeout)
        return active

    def clear_manual_ai_base_url(self):
        self.ai_manual_base_url = ""
        self.ai_mode = "auto"
        self.ai_base_url = None
        self.ai_available_models = []
        self.ai_model_id = ""
        self._reset_ai_server_cache()
        self._rebuild_ai_model_submenu()
        self._update_ai_model_ui()
        self.refresh_models_menu_status()

    def scan_ai_models_now(self):
        self._ai_server_cache = {
            "ts": 0.0,
            "base_url": None,
            "model_id": None,
        }
        models = []
        detected_model_id = ""
        if self.ai_manual_base_url:
            self.ai_mode = "manual"
            self.ai_base_url = self._normalize_ai_base_url(self.ai_manual_base_url)
            self.ai_endpoint = self.ai_base_url + "/chat/completions"
            models, detected_model_id = self._fetch_models_from_base_url(self.ai_base_url, timeout=0.6)
        else:
            self.ai_mode = "auto"
            base_url, detected_model_id = self._detect_local_openai_server(force=True)
            self.ai_base_url = base_url
            if base_url:
                self.ai_endpoint = base_url + "/chat/completions"
                models, active = self._fetch_models_from_base_url(base_url, timeout=0.35)
                if active:
                    detected_model_id = active
        self.ai_available_models = models
        if models:
            if detected_model_id and detected_model_id in models:
                self.ai_model_id = detected_model_id
            else:
                self.ai_model_id = models[0]
            self.status_bar.showMessage(self._tr("msg_lm_found", self.ai_model_id))
        else:
            self.ai_model_id = ""
            if self.ai_mode == "auto":
                self.ai_base_url = None
            self.status_bar.showMessage(self._tr("msg_lm_server_not_found"))
        self._rebuild_ai_model_submenu()
        self.refresh_models_menu_status()

    def _rebuild_ai_model_submenu(self):
        if not hasattr(self, "ai_models_submenu"):
            return
        self.ai_models_submenu.clear()
        self.ai_model_actions = {}
        if self.ai_model_group is None:
            self.ai_model_group = QActionGroup(self)
            self.ai_model_group.setExclusive(True)
        for act in list(self.ai_model_group.actions()):
            self.ai_model_group.removeAction(act)
        if not self.ai_available_models:
            empty_act = QAction(self._tr("no_models_scan"), self)
            empty_act.setEnabled(False)
            self.ai_models_submenu.addAction(empty_act)
        else:
            for model_id in self.ai_available_models:
                act = QAction(model_id, self)
                act.setCheckable(True)
                act.setChecked(model_id == self.ai_model_id)
                act.triggered.connect(lambda checked, mid=model_id: self._set_ai_model(mid))
                self.ai_model_group.addAction(act)
                self.ai_models_submenu.addAction(act)
                self.ai_model_actions[model_id] = act
        self.ai_models_submenu.addSeparator()
        self.act_clear_ai_model = QAction(self._tr("act_clear_ai_model"), self)
        self.act_clear_ai_model.triggered.connect(self.clear_ai_model)
        self.act_clear_ai_model.setEnabled(bool(self.ai_model_id or self.ai_available_models))
        self.ai_models_submenu.addAction(self.act_clear_ai_model)

    def choose_ai_model_dialog(self):
        models = self._fetch_loaded_llm_models(force=True)
        if not models:
            QMessageBox.warning(self, self._tr("warn_title"), "Es wurden keine geladenen LM-Modelle gefunden.")
            return
        current = self.ai_model_id if self.ai_model_id in models else models[0]
        selected, ok = QInputDialog.getItem(
            self,
            "LM-Model ändern",
            "Zu nutzendes LM-Model auswählen:",
            models,
            max(0, models.index(current)),
            False
        )
        if not ok or not selected:
            return
        self._set_ai_model(selected)
        self.refresh_models_menu_status()

    def _current_ai_mode_label(self) -> str:
        if not (self.ai_model_id or "").strip():
            return "-"
        return "Manuell" if self.ai_mode == "manual" else "Auto"

    def _set_ai_model(self, model_id: str):
        self.ai_model_id = (model_id or "").strip()
        for mid, act in self.ai_model_actions.items():
            act.setChecked(mid == self.ai_model_id)
        self._rebuild_ai_model_submenu()
        self._update_ai_model_ui()
        self.refresh_models_menu_status()
        if self.ai_model_id:
            self.status_bar.showMessage(self._tr("msg_ai_model_set", self.ai_model_id))
        else:
            self.status_bar.showMessage(self._tr("msg_ai_model_choice_cleared"))

    def clear_ai_model(self):
        self.ai_model_id = ""
        self.ai_available_models = []
        # alles zurücksetzen
        self.ai_base_url = None
        self.ai_manual_base_url = ""
        self.ai_endpoint = "http://127.0.0.1:1234/v1/chat/completions"
        self.ai_mode = ""
        self._ai_server_cache = {
            "ts": 0.0,
            "base_url": None,
            "model_id": None,
        }
        self._rebuild_ai_model_submenu()
        self._update_ai_model_ui()
        self.refresh_models_menu_status()
        self.status_bar.showMessage(self._tr("msg_ai_model_removed"))

    def _swap_lines(self, task: TaskItem, row_a: int, row_b: int):
        if not task or not task.results:
            return
        _, _, _, recs = task.results
        if not (0 <= row_a < len(recs)) or not (0 <= row_b < len(recs)):
            return
        if row_a == row_b:
            self._sync_ui_after_recs_change(task, keep_row=row_a)
            return
        order = list(range(len(recs)))
        order[row_a], order[row_b] = order[row_b], order[row_a]
        self._reorder_lines_keep_box_slots(task, order, keep_row=row_b)

    def _swap_line_with_dialog(self, task: TaskItem, row: int):
        if not task or not task.results:
            return
        _, _, _, recs = task.results
        if not (0 <= row < len(recs)):
            return
        target, ok = QInputDialog.getInt(
            self,
            self._tr("dlg_swap_title"),
            self._tr("dlg_swap_label"),
            row + 1,  # value
            1,  # minValue
            max(1, len(recs)),  # maxValue
            1  # step
        )
        if not ok:
            return
        self._swap_lines(task, row, target - 1)

    def _project_base_dir(self) -> str:
        if self.project_file_path:
            return os.path.dirname(os.path.abspath(self.project_file_path))
        return os.getcwd()

    def _make_hybrid_paths_for_task(self, task: TaskItem) -> tuple[str, str]:
        abs_path = os.path.abspath(task.path)
        rel_path = ""
        try:
            base_dir = self._project_base_dir()
            rel_candidate = os.path.relpath(abs_path, base_dir)
            # nur sinnvoll, wenn wirklich relativ und nicht auf anderes Laufwerk springt
            if not os.path.isabs(rel_candidate) and not rel_candidate.startswith(".."):
                rel_path = rel_candidate
            else:
                # auch '../...' ist als relativer Pfad technisch gültig,
                # wenn du das erlauben willst, nimm stattdessen einfach:
                # rel_path = rel_candidate
                rel_path = rel_candidate
        except Exception:
            rel_path = os.path.basename(abs_path)
        return abs_path, rel_path

    def _resolve_hybrid_task_path(self, data: dict) -> str:
        absolute_path = str(data.get("absolute_path", "")).strip()
        relative_path = str(data.get("relative_path", "")).strip()
        legacy_path = str(data.get("path", "")).strip()
        # 1) absoluter Pfad
        if absolute_path and os.path.exists(absolute_path):
            return os.path.abspath(absolute_path)
        # 2) relativer Pfad zum Projektordner
        if relative_path:
            candidate = os.path.normpath(os.path.join(self._project_base_dir(), relative_path))
            if os.path.exists(candidate):
                return candidate
        # 3) alter path-Eintrag als Fallback
        if legacy_path and os.path.exists(legacy_path):
            return os.path.abspath(legacy_path)
        # 4) best effort: absoluten Pfad zurückgeben, sonst relativen Kandidaten, sonst legacy
        if absolute_path:
            return os.path.abspath(absolute_path)
        if relative_path:
            return os.path.normpath(os.path.join(self._project_base_dir(), relative_path))
        return legacy_path

    def _recordview_to_dict(self, rv: RecordView) -> dict:
        return {
            "idx": int(rv.idx),
            "text": rv.text,
            "bbox": list(rv.bbox) if rv.bbox else None,
        }

    def _recordview_from_dict(self, data: dict) -> RecordView:
        bbox = data.get("bbox")
        if bbox is not None:
            bbox = tuple(int(x) for x in bbox)
        return RecordView(
            idx=int(data.get("idx", 0)),
            text=str(data.get("text", "")),
            bbox=bbox
        )

    def _task_to_dict(self, task: TaskItem) -> dict:
        abs_path, rel_path = self._make_hybrid_paths_for_task(task)
        payload = {
            "path": abs_path,  # Legacy/Fallback
            "absolute_path": abs_path,  # neu
            "relative_path": rel_path,  # neu: echter relativer Pfad
            "display_name": task.display_name,
            "status": int(task.status),
            "edited": bool(task.edited),
            "source_kind": task.source_kind,
            "undo_stack": [],
            "redo_stack": [],
            "results": None,
        }
        if task.results:
            text, kr_records, im, recs = task.results
            payload["results"] = {"text": text, "records": [self._recordview_to_dict(rv) for rv in recs], }
        return payload

    def _task_from_dict(self, data: dict) -> TaskItem:
        resolved_path = self._resolve_hybrid_task_path(data)
        display_name_default = os.path.basename(resolved_path) if resolved_path else os.path.basename(
            str(data.get("path", "")))
        rel_default = str(data.get("relative_path", "")).strip()
        task = TaskItem(
            path=resolved_path,
            display_name=str(data.get("display_name", display_name_default)),
            status=int(data.get("status", STATUS_WAITING)),
            edited=False,
            source_kind=str(data.get("source_kind", "image")),
            relative_path=rel_default,
        )
        results = data.get("results")
        if results:
            recs = [self._recordview_from_dict(x) for x in results.get("records", [])]
            text = str(results.get("text", "\n".join(rv.text for rv in recs).strip()))
            gray_im = None
            if os.path.exists(task.path):
                try:
                    gray_im = _load_image_gray(task.path)
                except Exception:
                    gray_im = None
            task.results = (text, [], gray_im, recs)
        return task

    def _project_to_dict(self) -> dict:
        current_row = self.queue_table.currentRow()
        return {
            "version": 2,
            "project_base_dir": self._project_base_dir(),
            "settings": {
                "language": self.current_lang,
                "reading_direction": self.reading_direction,
                "device": self.device_str,
                "show_overlay": self.show_overlay,
                "theme": self.current_theme,
                "model_path": self.model_path,
                "seg_model_path": self.seg_model_path,
                "current_export_dir": self.current_export_dir,
                "ai_model_id": self.ai_model_id,
                "current_row": current_row,
                "whisper_models_base_dir": self.whisper_models_base_dir,
                "whisper_model_path": self.whisper_model_path,
                "whisper_selected_input_device": self.whisper_selected_input_device,
                "whisper_selected_input_device_label": self.whisper_selected_input_device_label,
                "last_rec_model_dir": self.last_rec_model_dir,
                "last_seg_model_dir": self.last_seg_model_dir,
            },
            "queue_items": [self._task_to_dict(task) for task in self.queue_items],
        }
