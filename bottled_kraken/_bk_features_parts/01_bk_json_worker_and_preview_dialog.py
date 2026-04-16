"""BK-Erweiterungen und späte Patches für lokale LM-Workflows."""

from .shared import *

from .ui_components import *

from .workers import *

from .dialogs import *

from .image_edit import *

from .main_window import MainWindow

from .ptr_features import *

def _bk_json_schema_kind_label(window, schema_kind: str) -> str:
    if str(schema_kind).strip().lower() == "neo4j":
        return "Neo4j"
    return "PostgreSQL"

def _bk_normalize_neo4j_json(data: Any, source_text: str) -> Dict[str, Any]:
    payload = data if isinstance(data, dict) else {}
    raw_nodes = payload.get("nodes")
    raw_relationships = payload.get("relationships")
    if not isinstance(raw_nodes, list):
        raw_nodes = []
    if not isinstance(raw_relationships, list):
        raw_relationships = []
    nodes: List[Dict[str, Any]] = []
    seen_ids = set()
    for idx, raw_node in enumerate(raw_nodes, start=1):
        if isinstance(raw_node, dict):
            node = dict(raw_node)
        elif isinstance(raw_node, str):
            node = {"label": raw_node.strip(), "type": "Entity", "properties": {"source_excerpt": (source_text or "")[:400] or None}}
        else:
            continue
        node_id = str(node.get("id") or f"node_{idx}").strip() or f"node_{idx}"
        if node_id in seen_ids:
            node_id = f"{node_id}_{idx}"
        seen_ids.add(node_id)
        label = node.get("label")
        node_type = node.get("type")
        props = node.get("properties")
        if not isinstance(props, dict):
            props = {}
        nodes.append({
            "id": node_id,
            "label": (str(label).strip() if label is not None else None),
            "type": (str(node_type).strip() if node_type is not None else None),
            "properties": props,
        })
    valid_ids = {node["id"] for node in nodes}
    relationships: List[Dict[str, Any]] = []
    for idx, raw_rel in enumerate(raw_relationships, start=1):
        if not isinstance(raw_rel, dict):
            continue
        source = str(raw_rel.get("source") or "").strip()
        target = str(raw_rel.get("target") or "").strip()
        rel_type = str(raw_rel.get("type") or "").strip().upper().replace(" ", "_")
        props = raw_rel.get("properties")
        if not isinstance(props, dict):
            props = {}
        if not source or not target or not rel_type:
            continue
        if valid_ids and (source not in valid_ids or target not in valid_ids):
            continue
        relationships.append({
            "source": source,
            "target": target,
            "type": rel_type,
            "properties": props,
        })
    return {
        "nodes": nodes,
        "relationships": relationships,
    }

class BKLocalStructuredJsonWorker(QThread):
    finished_json = Signal(str, str, dict)
    failed_json = Signal(str, str, str)
    progress_changed = Signal(int)
    status_changed = Signal(str)

    def __init__(
        self,
        *,
        path: str,
        source_text: str,
        schema_kind: str,
        lm_model: str,
        endpoint: str,
        enable_thinking: bool = False,
        temperature: float = 0.2,
        top_p: float = 0.8,
        top_k: int = 10,
        presence_penalty: float = 0.0,
        repetition_penalty: float = 1.0,
        min_p: float = 0.0,
        max_tokens: int = 2400,
        tr_func=None,
        parent=None,
    ):
        super().__init__(parent)
        self._tr = tr_func or translation.make_tr("de")
        self.path = path
        self.source_text = (source_text or "").strip()
        self.schema_kind = (schema_kind or "postgres").strip().lower()
        self.lm_model = lm_model
        self.endpoint = endpoint
        self.enable_thinking = bool(enable_thinking)
        self.temperature = float(temperature)
        self.top_p = float(top_p)
        self.top_k = int(top_k)
        self.presence_penalty = float(presence_penalty)
        self.repetition_penalty = float(repetition_penalty)
        self.min_p = float(min_p)
        self.max_tokens = int(max_tokens)
        self._cancelled = False
        self._active_conn = None

    def cancel(self):
        self._cancelled = True
        self.requestInterruption()
        conn = self._active_conn
        self._active_conn = None
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

    def _build_sampling_payload(self, *, use_response_format: bool) -> dict:
        payload = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
            "max_tokens": self.max_tokens,
        }
        if use_response_format:
            payload["response_format"] = {"type": "json_object"}
        if self.enable_thinking:
            payload["reasoning"] = {"effort": "medium"}
        if self.top_k > 0:
            payload["top_k"] = self.top_k
        if self.min_p > 0:
            payload["min_p"] = self.min_p
        if self.repetition_penalty != 1.0:
            payload["repetition_penalty"] = self.repetition_penalty
        return payload

    def _post_json(self, payload: dict) -> dict:
        if self._cancelled or self.isInterruptionRequested():
            raise RuntimeError(self._tr("msg_local_json_cancelled"))
        body = json.dumps(payload).encode("utf-8")
        parsed = urllib.parse.urlparse(self.endpoint)
        if parsed.scheme not in ("http", "https"):
            raise RuntimeError(self._tr("ai_err_bad_scheme", parsed.scheme))
        host = parsed.hostname
        port = parsed.port
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query
        if not host:
            raise RuntimeError(self._tr("ai_err_invalid_endpoint"))
        conn = None
        try:
            if parsed.scheme == "https":
                conn = http.client.HTTPSConnection(host, port or 443, timeout=600)
            else:
                conn = http.client.HTTPConnection(host, port or 80, timeout=600)
            self._active_conn = conn
            conn.request(
                "POST",
                path,
                body=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer lm-studio",
                },
            )
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_local_json_cancelled"))
            resp = conn.getresponse()
            raw = resp.read().decode("utf-8", errors="replace")
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_local_json_cancelled"))
            if resp.status >= 400:
                raise RuntimeError(self._tr("ai_err_http", resp.status, raw))
            return json.loads(raw)
        except socket.timeout:
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_local_json_cancelled"))
            raise RuntimeError(self._tr("ai_err_timeout"))
        except json.JSONDecodeError as e:
            raise RuntimeError(self._tr("ai_err_invalid_json", e))
        finally:
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass
            if self._active_conn is conn:
                self._active_conn = None

    def _extract_message_content(self, data: dict) -> str:
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError(self._tr("ai_err_no_choices", json.dumps(data, ensure_ascii=False)[:3000]))
        choice0 = choices[0] or {}
        message = choice0.get("message", {}) if isinstance(choice0, dict) else {}

        def flatten(val):
            if val is None:
                return ""
            if isinstance(val, bytes):
                return val.decode("utf-8", errors="replace").strip()
            if isinstance(val, str):
                return val.strip()
            if isinstance(val, list):
                parts = []
                for part in val:
                    if isinstance(part, bytes):
                        txt = part.decode("utf-8", errors="replace").strip()
                        if txt:
                            parts.append(txt)
                    elif isinstance(part, str) and part.strip():
                        parts.append(part.strip())
                    elif isinstance(part, dict):
                        for key in ("text", "content", "output_text"):
                            v = part.get(key)
                            if isinstance(v, bytes):
                                txt = v.decode("utf-8", errors="replace").strip()
                                if txt:
                                    parts.append(txt)
                            elif isinstance(v, str) and v.strip():
                                parts.append(v.strip())
                return "\n".join(parts).strip()
            if isinstance(val, dict):
                for key in ("text", "content", "output_text"):
                    v = val.get(key)
                    if isinstance(v, bytes):
                        txt = v.decode("utf-8", errors="replace").strip()
                        if txt:
                            return txt
                    elif isinstance(v, str) and v.strip():
                        return v.strip()
            return _force_text(val).strip()

        candidates = []
        if isinstance(message, dict):
            candidates.append(message.get("content"))
            candidates.append(message.get("text"))
            candidates.append(message.get("output_text"))
        if isinstance(choice0, dict):
            candidates.append(choice0.get("content"))
            candidates.append(choice0.get("text"))
        for cand in candidates:
            txt = flatten(cand)
            if txt:
                txt = re.sub(r"<think>.*?</think>", "", txt, flags=re.DOTALL).strip()
                if txt:
                    return txt
        reasoning = ""
        if isinstance(message, dict):
            rc = message.get("reasoning_content")
            if isinstance(rc, str) and rc.strip():
                reasoning = rc.strip()
        finish_reason = ""
        if isinstance(choice0, dict):
            finish_reason = str(choice0.get("finish_reason", "")).strip()
        if reasoning:
            cleaned = re.sub(r"<think>.*?</think>", "", reasoning, flags=re.DOTALL).strip()
            if cleaned:
                if cleaned.startswith("{") or '"nodes"' in cleaned or '"lines"' in cleaned or '"document"' in cleaned:
                    return cleaned
            if finish_reason == "length":
                raise RuntimeError(self._tr("ai_err_reasoning_truncated"))
            raise RuntimeError(self._tr("ai_err_reasoning_only"))
        raise RuntimeError(self._tr("ai_err_no_content"))

    def _request_json_object(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        last_error = None
        for use_response_format in (True, False):
            payload = {
                "model": self.lm_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                **self._build_sampling_payload(use_response_format=use_response_format),
            }
            try:
                data = self._post_json(payload)
                content = self._extract_message_content(data)
                obj = _extract_json_payload(content)
                if not isinstance(obj, dict):
                    raise RuntimeError(self._tr("ai_err_invalid_json", "Top-level JSON object expected."))
                return obj
            except Exception as exc:
                last_error = exc
                if self._cancelled or self.isInterruptionRequested():
                    break
        if last_error is None:
            raise RuntimeError(self._tr("msg_local_json_failed"))
        raise last_error

    def _build_postgres_json(self) -> Dict[str, Any]:
        system_prompt = (
            "You are an information extraction assistant for OCR-derived historical or administrative texts.\n\n"
            "Your task is to extract structured relational data and return valid JSON only.\n\n"
            "Rules:\n"
            "- Return JSON only.\n"
            "- Do not include markdown.\n"
            "- Do not include explanations.\n"
            "- Do not invent missing information.\n"
            "- If a value is unknown or uncertain, use null.\n"
            "- Extract entities only when they are supported by the text.\n"
            "- Keep output compact but schema-consistent.\n"
            "- The JSON must be usable as a PostgreSQL import/interchange payload.\n"
            "- Create lightweight stable ids when possible.\n"
            "- References must describe relational links between extracted entities.\n"
        )
        user_prompt = (
            "Create a PostgreSQL-oriented JSON payload from the following text.\n\n"
            "Return exactly one JSON object with this top-level structure:\n"
            "{\n"
            '  "document": {"id": "document_1", "title": null, "source_type": "ocr_text", "language": null, "raw_excerpt": null},\n'
            '  "persons": [{"id": "...", "full_name": null, "first_name": null, "last_name": null, "description": null, "source_excerpt": null}],\n'
            '  "places": [{"id": "...", "name": null, "type": null, "description": null}],\n'
            '  "streets": [{"id": "...", "name": null, "place": null, "description": null}],\n'
            '  "years": [{"id": "...", "year": null, "context": null}],\n'
            '  "organizations": [{"id": "...", "name": null, "type": null, "description": null}],\n'
            '  "references": [{"id": "...", "source_table": null, "source_id": null, "relation_type": null, "target_table": null, "target_id": null, "evidence": null}]\n'
            "}\n\n"
            "Guidance:\n"
            "- Use arrays even when only one entry exists.\n"
            "- Keep unconfirmed values as null.\n"
            "- references should describe meaningful relations such as LIVES_AT, LOCATED_IN, MEMBER_OF, MENTIONS, or REFERENCED_IN.\n"
            "- If no relations are supported, return an empty references array.\n\n"
            "Text:\n" + self.source_text
        )
        data = self._request_json_object(system_prompt, user_prompt)
        return _ptr_normalize_postgres_json(data, self.source_text)

    def _build_neo4j_json(self) -> Dict[str, Any]:
        system_prompt = (
            "You are a graph information extraction assistant for OCR-derived texts.\n\n"
            "Your task is to transform the text into graph-oriented structured JSON.\n"
            "Return valid JSON only.\n\n"
            "Rules:\n"
            "- Return JSON only.\n"
            "- Do not include markdown.\n"
            "- Do not include explanations.\n"
            "- Do not invent unsupported entities or relationships.\n"
            "- Prefer fewer but well-supported relationships over many speculative ones.\n"
            "- Create nodes for meaningful entities such as persons, places, streets, years, organizations, and documents.\n"
            "- Create relationships only when the text supports them.\n"
            "- Use concise relationship types in uppercase with underscores.\n"
        )
        user_prompt = (
            "Create a Neo4j-oriented graph JSON payload from the following text.\n\n"
            "Return exactly one JSON object with this top-level structure:\n"
            "{\n"
            '  "nodes": [...],\n'
            '  "relationships": [...]\n'
            "}\n\n"
            "Node structure:\n"
            '{ "id": "...", "label": "...", "type": "...", "properties": { ... } }\n\n'
            "Relationship structure:\n"
            '{ "source": "...", "target": "...", "type": "...", "properties": { ... } }\n\n'
            "Text:\n" + self.source_text
        )
        data = self._request_json_object(system_prompt, user_prompt)
        return _bk_normalize_neo4j_json(data, self.source_text)

    def run(self):
        try:
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_local_json_cancelled"))
            self.progress_changed.emit(5)
            self.status_changed.emit(self._tr("dlg_local_json_connecting"))
            if self.schema_kind == "neo4j":
                self.progress_changed.emit(45)
                self.status_changed.emit(self._tr("status_local_json_generating"))
                data = self._build_neo4j_json()
            else:
                self.progress_changed.emit(45)
                self.status_changed.emit(self._tr("status_local_json_generating"))
                data = self._build_postgres_json()
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr("msg_local_json_cancelled"))
            self.progress_changed.emit(100)
            self.finished_json.emit(self.path, self.schema_kind, data)
        except Exception as exc:
            self.failed_json.emit(self.path, self.schema_kind, str(exc))

class BKJsonPreviewDialog(QDialog):
    def __init__(self, parent, tr_func, title: str, hint: str, data: Dict[str, Any], default_name: str):
        super().__init__(parent)
        self._tr = tr_func
        self._data = data if isinstance(data, dict) else {}
        self._default_name = default_name or "result.json"
        self.setWindowTitle(title)
        self.resize(860, 640)
        root = QVBoxLayout(self)
        self.lbl_hint = QLabel(hint)
        self.lbl_hint.setWordWrap(True)
        root.addWidget(self.lbl_hint)
        self.edit = QPlainTextEdit()
        self.edit.setReadOnly(True)
        self.edit.setPlainText(json.dumps(self._data, ensure_ascii=False, indent=2))
        root.addWidget(self.edit, 1)
        row = QHBoxLayout()
        row.addStretch(1)
        self.btn_save = QPushButton(self._tr("dlg_save"))
        self.btn_close = QPushButton(self._tr("btn_close"))
        row.addWidget(self.btn_save)
        row.addWidget(self.btn_close)
        root.addLayout(row)
        self.btn_save.clicked.connect(self._save_as)
        self.btn_close.clicked.connect(self.accept)

    def _save_as(self):
        parent = self.parentWidget()
        start_dir = getattr(parent, "current_export_dir", "") or os.getcwd()
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.windowTitle(),
            os.path.join(start_dir, self._default_name),
            self._tr("dlg_filter_json"),
        )
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, ensure_ascii=False, indent=2)
        if parent is not None:
            try:
                parent.current_export_dir = os.path.dirname(path)
            except Exception:
                pass
            try:
                parent.status_bar.showMessage(self._tr("msg_local_json_saved", os.path.basename(path)), 4000)
            except Exception:
                pass
        self.accept()
