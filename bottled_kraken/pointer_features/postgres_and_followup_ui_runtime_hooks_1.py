from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('ptr', globals())
from typing import Any, Dict, List, Optional, Tuple
def _ptr_prompt_owner(config):
    try:
        return getattr(config, "_bk_prompt_owner", None)
    except Exception:
        return None
def _ptr_prompt_text_from_owner(owner, key: str, fallback: str) -> str:
    if owner is not None:
        try:
            if "_bk_lm_prompt_override" in globals():
                override = _bk_lm_prompt_override(owner, key)
                if override:
                    return str(override)
        except Exception:
            pass
        try:
            if hasattr(owner, "_tr"):
                value = owner._tr(key)
                if value and value != key:
                    return str(value)
        except Exception:
            pass
        try:
            lang = getattr(owner, "current_lang", translation.DEFAULT_LANGUAGE)
            value = translation.translate(lang, key)
            if value and value != key:
                return str(value)
        except Exception:
            pass
    return str(fallback or "")
def _ptr_apply_prompt_template(template: str, *, schema_template: str, text: str) -> str:
    try:
        return str(template).format(schema_template=schema_template, ocr_text=text, text=text, merged_text=text)
    except Exception:
        return str(template) + "\n\nText:\n" + str(text or "")
def _ptr_prompt_from_config(config, system_key: str, user_key: str,
                            default_system: str, default_user: str,
                            schema_template: str, text: str) -> Tuple[str, str]:
    owner = _ptr_prompt_owner(config)
    system_prompt = _ptr_prompt_text_from_owner(owner, system_key, default_system)
    user_template = _ptr_prompt_text_from_owner(owner, user_key, default_user)
    user_prompt = _ptr_apply_prompt_template(user_template, schema_template=schema_template, text=text)
    return system_prompt, user_prompt
def _ptr_make_slug(value: str, fallback: str) -> str:
    txt = str(value or "")
    txt = re.sub(r"[^a-zA-Z0-9]+", "-", txt).strip("-").lower()
    return txt or fallback
def _ptr_postgres_empty_payload(source_text: str) -> Dict[str, Any]:
    excerpt = (source_text or "").strip().replace("\r", "")
    excerpt = excerpt[:1000]
    return {
        "document": {
            "id": "document_1",
            "title": None,
            "source_type": "ocr_text",
            "language": None,
            "raw_excerpt": excerpt or None,
        },
        "persons": [],
        "places": [],
        "streets": [],
        "years": [],
        "organizations": [],
        "references": [],
        "sqlite_export": {
            "target": "transcription_helper",
            "tables": {
                "persons": [],
                "documents": [],
                "entries": []
            }
        },
    }
def _ptr_normalize_postgres_json(data: Any, source_text: str) -> Dict[str, Any]:
    payload = _ptr_postgres_empty_payload(source_text)
    if isinstance(data, dict):
        for key in payload.keys():
            if key in data:
                payload[key] = data[key]
    if not isinstance(payload.get("document"), dict):
        payload["document"] = _ptr_postgres_empty_payload(source_text)["document"]
    doc = payload["document"]
    doc.setdefault("id", "document_1")
    doc.setdefault("title", None)
    doc.setdefault("source_type", "ocr_text")
    doc.setdefault("language", None)
    doc.setdefault("raw_excerpt", (source_text or "").strip()[:1000] or None)
    specs = {
        "persons": {
            "defaults": {"id": None, "full_name": None, "first_name": None, "last_name": None, "age": None, "event_date": None, "event_place": None, "occupation": None, "description": None, "source_excerpt": None},
            "label": lambda item: item.get("full_name") or "person",
        },
        "places": {
            "defaults": {"id": None, "name": None, "type": None, "description": None},
            "label": lambda item: item.get("name") or "place",
        },
        "streets": {
            "defaults": {"id": None, "name": None, "place": None, "description": None},
            "label": lambda item: item.get("name") or "street",
        },
        "years": {
            "defaults": {"id": None, "year": None, "context": None},
            "label": lambda item: str(item.get("year") or "year"),
        },
        "organizations": {
            "defaults": {"id": None, "name": None, "type": None, "description": None},
            "label": lambda item: item.get("name") or "organization",
        },
        "references": {
            "defaults": {
                "id": None,
                "source_table": None,
                "source_id": None,
                "relation_type": None,
                "target_table": None,
                "target_id": None,
                "evidence": None,
            },
            "label": lambda item: item.get("relation_type") or "reference",
        },
    }
    for table, spec in specs.items():
        raw_items = payload.get(table)
        if not isinstance(raw_items, list):
            raw_items = []
        normalized = []
        for idx, raw_item in enumerate(raw_items, start=1):
            if isinstance(raw_item, dict):
                item = dict(raw_item)
            elif isinstance(raw_item, str):
                item = {}
                if table == "persons":
                    item["full_name"] = raw_item.strip()
                elif table == "years":
                    item["year"] = raw_item.strip()
                else:
                    item["name"] = raw_item.strip()
            else:
                continue
            for k, v in spec["defaults"].items():
                item.setdefault(k, v)
            label = spec["label"](item)
            if not item.get("id"):
                item["id"] = f"{table[:-1] if table.endswith('s') else table}_{_ptr_make_slug(label, str(idx))}_{idx}"
            if table == "references":
                if item.get("relation_type"):
                    item["relation_type"] = str(item["relation_type"]).upper().replace(" ", "_")
            normalized.append(item)
        payload[table] = normalized
    return payload
class _PtrHTTPResponseError(RuntimeError):
    def __init__(self, code: int, body: str):
        super().__init__(str(code))
        self.code = int(code)
        self.body = body or ""

def _ptr_raise_if_remote_cancelled(config):
    checker = getattr(config, "_bk_cancel_checker", None)
    if callable(checker):
        checker()

def _ptr_cancellable_http_post_json(config, url: str, payload: Dict[str, Any], headers: Dict[str, str], timeout_seconds: int) -> str:
    parsed = urllib.parse.urlparse(url)
    scheme = (parsed.scheme or "").lower()
    if scheme not in ("http", "https"):
        raise ValueError("Base URL must start with http:// or https://")
    if not parsed.hostname:
        raise ValueError("Base URL host must not be empty.")
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    body = json.dumps(payload).encode("utf-8")
    request_headers = dict(headers or {})
    request_headers.setdefault("Content-Type", "application/json")
    request_headers.setdefault("Content-Length", str(len(body)))
    connection_cls = http.client.HTTPSConnection if scheme == "https" else http.client.HTTPConnection
    connection = connection_cls(parsed.hostname, port=parsed.port, timeout=max(5, int(timeout_seconds)))
    owner = getattr(config, "_bk_connection_owner", None)
    try:
        if owner is not None and hasattr(owner, "_set_active_connection"):
            owner._set_active_connection(connection)
        _ptr_raise_if_remote_cancelled(config)
        connection.request("POST", path, body=body, headers=request_headers)
        _ptr_raise_if_remote_cancelled(config)
        response = connection.getresponse()
        raw = response.read().decode("utf-8", errors="replace")
        _ptr_raise_if_remote_cancelled(config)
        if int(getattr(response, "status", 0) or 0) >= 400:
            raise _PtrHTTPResponseError(int(response.status), raw)
        return raw
    finally:
        if owner is not None and hasattr(owner, "_clear_active_connection"):
            try:
                owner._clear_active_connection(connection)
            except Exception:
                pass
        try:
            connection.close()
        except Exception:
            pass

def _ptr_ai_build_postgres_json_v2(config: PtrRemoteAIConfig, merged_text: str) -> Dict[str, Any]:
    cleaned_text = (merged_text or "").strip()
    if not cleaned_text:
        raise ValueError("merged_text must not be empty.")
    schema_template = (
        "{\n"
        '  "document": {"id": "document_1", "title": null, "source_type": "ocr_text", "language": null, "raw_excerpt": null},\n'
        '  "persons": [{"id": "...", "full_name": null, "first_name": null, "last_name": null, "age": null, "event_date": null, "event_place": null, "occupation": null, "description": null, "source_excerpt": null}],\n'
        '  "places": [{"id": "...", "name": null, "type": null, "description": null}],\n'
        '  "streets": [{"id": "...", "name": null, "place": null, "description": null}],\n'
        '  "years": [{"id": "...", "year": null, "context": null}],\n'
        '  "organizations": [{"id": "...", "name": null, "type": null, "description": null}],\n'
        '  "references": [{"id": "...", "source_table": null, "source_id": null, "relation_type": null, "target_table": null, "target_id": null, "evidence": null}],\n'
        '  "sqlite_export": {"target": "transcription_helper", "tables": {"persons": [], "documents": [], "entries": []}}\n'
        "}"
    )
    default_system = (
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
        "- Also include enough person/entry fields for a SQLite export usable by transcription-helper style apps.\n"
        "- Extract age expressions, event dates, places and source lines for persons when present.\n"
        "- Create lightweight stable ids when possible.\n"
        "- References must describe relational links between extracted entities.\n"
    )
    default_user = (
        "Create a PostgreSQL-oriented JSON payload from the following text.\n\n"
        "Return exactly one JSON object with this top-level structure:\n"
        "{schema_template}\n\n"
        "Guidance:\n"
        "- Use arrays even when only one entry exists.\n"
        "- Keep unconfirmed values as null.\n"
        "- references should describe meaningful relations such as LIVES_AT, LOCATED_IN, MEMBER_OF, MENTIONS, or REFERENCED_IN.\n"
        "- For register pages, persons should include age, event_date, event_place, occupation and source_excerpt when available.\n"
        "- sqlite_export.tables.persons and sqlite_export.tables.entries may mirror the extracted persons in a flat SQLite-friendly structure.\n"
        "- If no relations are supported, return an empty references array.\n\n"
        "Text:\n{ocr_text}"
    )
    system_prompt, user_prompt = _ptr_prompt_from_config(
        config,
        "ai_prompt_postgresql_system",
        "ai_prompt_postgresql_user",
        default_system,
        default_user,
        schema_template,
        cleaned_text,
    )
    raw = _ptr_remote_chat_completion(config, [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ], expect_json=True)
    data = _ptr_extract_json_object(_ptr_extract_content_from_chat_response(raw))
    return _ptr_normalize_postgres_json(data, cleaned_text)
def _ptr_remote_chat_completion_v2(config: PtrRemoteAIConfig, messages: List[Dict[str, str]],
                                   *, expect_json: bool = False,
                                   max_tokens: Optional[int] = None) -> Dict[str, Any]:
    provider_name = (config.provider_name or "").strip().lower()
    base_url = _ptr_normalize_remote_base_url(config.base_url or "", provider_name)
    if not base_url:
        raise ValueError("Base URL must not be empty.")
    if not re.match(r"^https?://", base_url, flags=re.IGNORECASE):
        raise ValueError("Base URL must start with http:// or https://")
    url = base_url.rstrip("/")
    if not url.endswith("/chat/completions"):
        url += "/chat/completions"
    payload: Dict[str, Any] = {
        "model": (config.model or "").strip(),
        "messages": messages,
        "temperature": float(config.temperature),
    }
    if not payload["model"]:
        raise ValueError("Model must not be empty.")
    if max_tokens is not None:
        payload["max_tokens"] = int(max_tokens)
    if expect_json:
        payload["response_format"] = {"type": "json_object"}
    headers = {"Content-Type": "application/json"}
    api_key = (config.api_key or "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if provider_name == "openrouter" or "openrouter.ai" in url.lower():
        if not api_key:
            raise RuntimeError(translation.translate(translation.DEFAULT_LANGUAGE, "ptr_err_openrouter_key_required"))
        if (config.app_url or "").strip():
            headers["HTTP-Referer"] = config.app_url.strip()
        if (config.app_name or "").strip():
            headers["X-Title"] = config.app_name.strip()
    try:
        raw = _ptr_cancellable_http_post_json(config, url, payload, headers, max(5, int(config.timeout_seconds)))
    except PtrRemoteAICancelled:
        raise
    except _PtrHTTPResponseError as exc:
        body_clean = (exc.body or "").strip()
        if exc.code == 401 and (provider_name == "openrouter" or "openrouter.ai" in url.lower()):
            raise RuntimeError(translation.translate(translation.DEFAULT_LANGUAGE, "ptr_err_http_401_openrouter", "", body_clean)) from exc
        raise RuntimeError(translation.translate(translation.DEFAULT_LANGUAGE, "ptr_err_http_generic", exc.code, body_clean)) from exc
    except TimeoutError as exc:
        raise RuntimeError(translation.translate(translation.DEFAULT_LANGUAGE, "ptr_err_request_timeout")) from exc
    except socket.timeout as exc:
        raise RuntimeError(translation.translate(translation.DEFAULT_LANGUAGE, "ptr_err_request_timeout")) from exc
    except OSError as exc:
        _ptr_raise_if_remote_cancelled(config)
        raise RuntimeError(translation.translate(translation.DEFAULT_LANGUAGE, "ptr_err_request_failed", exc)) from exc
    try:
        data = json.loads(raw)
    except Exception as exc:
        raise RuntimeError(translation.translate(translation.DEFAULT_LANGUAGE, "ptr_err_invalid_json_response")) from exc
    if not isinstance(data, dict):
        raise RuntimeError(translation.translate(translation.DEFAULT_LANGUAGE, "ptr_err_unexpected_response"))
    return data
def _ptr_feature_config_from_window_v2(window) -> PtrRemoteAIConfig:
    settings = getattr(window, "settings", None)
    getv = (lambda key, default, t=None: settings.value(key, default, t) if settings is not None else default)
    save_api_key = bool(getv("ptr_remote_ai/save_api_key", False, bool))
    api_key = getv("ptr_remote_ai/api_key", "", str) if save_api_key else ""
    cfg = PtrRemoteAIConfig(
        provider_name=getv("ptr_remote_ai/provider", "openrouter", str),
        api_key=api_key,
        base_url=getv("ptr_remote_ai/base_url", "https://openrouter.ai/api/v1", str),
        model=getv("ptr_remote_ai/model", "openrouter/free", str),
        timeout_seconds=int(getv("ptr_remote_ai/timeout", 90, int)),
        temperature=float(getv("ptr_remote_ai/temperature", 0.2, float)),
        app_name=getv("ptr_remote_ai/app_name", "Bottled Kraken", str),
        app_url=getv("ptr_remote_ai/app_url", "", str),
    )
    setattr(cfg, "save_api_key", save_api_key)
    return cfg
def _ptr_save_feature_config_to_window_v2(window, config: PtrRemoteAIConfig):
    save_api_key = bool(getattr(config, "save_api_key", False))
    api_key = (config.api_key or "").strip()
    window.ptr_remote_ai_api_key = api_key if save_api_key else ""
    if hasattr(window, "settings") and window.settings is not None:
        window.settings.setValue("ptr_remote_ai/provider", config.provider_name)
        window.settings.setValue("ptr_remote_ai/base_url", _ptr_normalize_remote_base_url(config.base_url, config.provider_name))
        window.settings.setValue("ptr_remote_ai/model", config.model)
        window.settings.setValue("ptr_remote_ai/timeout", int(config.timeout_seconds))
        window.settings.setValue("ptr_remote_ai/temperature", float(config.temperature))
        window.settings.setValue("ptr_remote_ai/app_name", config.app_name)
        window.settings.setValue("ptr_remote_ai/app_url", config.app_url)
        window.settings.setValue("ptr_remote_ai/save_api_key", save_api_key)
        if save_api_key and api_key:
            window.settings.setValue("ptr_remote_ai/api_key", api_key)
        else:
            window.settings.remove("ptr_remote_ai/api_key")
def _ptr_followup_init_v2(self, parent=None):
    QDialog.__init__(self, parent)
    self.setWindowTitle(_ptr_ui_tr(self, "ptr_ai_multi_done_title"))
    self.resize(560, 220)
    self.choice = self.CHOICE_CANCEL
    root = QVBoxLayout(self)
    lbl = QLabel(_ptr_ui_tr(self, "ptr_ai_multi_done_text"))
    lbl.setWordWrap(True)
    root.addWidget(lbl)
    row1 = QHBoxLayout()
    row2 = QHBoxLayout()
    self.local_btn = QPushButton(_ptr_ui_tr(self, "ptr_ai_local_merge"))
    self.ai_btn = QPushButton(_ptr_ui_tr(self, "ptr_ai_open_tools"))
    self.ai_pg_btn = QPushButton(_ptr_ui_tr(self, "ptr_ai_followup_postgres"))
    self.ai_neo_btn = QPushButton(_ptr_ui_tr(self, "ptr_ai_followup_neo4j"))
    self.ai_both_btn = QPushButton(_ptr_ui_tr(self, "ptr_ai_both"))
    self.cancel_btn = QPushButton(_ptr_ui_tr(self, "btn_cancel"))
    row1.addWidget(self.local_btn)
    row1.addWidget(self.ai_btn)
    row1.addWidget(self.cancel_btn)
    row2.addWidget(self.ai_pg_btn)
    row2.addWidget(self.ai_neo_btn)
    row2.addWidget(self.ai_both_btn)
    root.addLayout(row1)
    root.addLayout(row2)
    self.local_btn.clicked.connect(lambda: self._choose(self.CHOICE_LOCAL))
    self.ai_btn.clicked.connect(lambda: self._choose(self.CHOICE_AI))
    self.ai_pg_btn.clicked.connect(lambda: self._choose(self.CHOICE_AI_POSTGRES))
    self.ai_neo_btn.clicked.connect(lambda: self._choose(self.CHOICE_AI_NEO4J))
    self.ai_both_btn.clicked.connect(lambda: self._choose(self.CHOICE_AI_BOTH))
    self.cancel_btn.clicked.connect(self.reject)
def _ptr_install_feature_actions_v2(self):
    if getattr(self, "_ptr_feature_actions_installed", False):
        return
    self._ptr_feature_actions_installed = True
    self.act_ptr_multi_ocr = QAction(_ptr_ui_tr(self, "ptr_multi_ocr_btn"), self)
    self.act_ptr_multi_ocr.triggered.connect(self.ptr_start_multi_ocr)
    self.act_ptr_ai_tools = QAction(_ptr_ui_tr(self, "ptr_ai_tools_title"), self)
    self.act_ptr_ai_tools.triggered.connect(self.ptr_open_ai_tools_for_current_task)
    self.act_ptr_multi_reopen = QAction(_ptr_ui_tr(self, "ptr_ai_reopen"), self)
    self.act_ptr_multi_reopen.triggered.connect(self.ptr_reopen_multi_followup)
    if hasattr(self, "toolbar") and self.toolbar is not None:
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.act_ptr_multi_ocr)
        self.toolbar.addAction(self.act_ptr_ai_tools)
    if hasattr(self, "models_menu") and self.models_menu is not None:
        self.models_menu.addSeparator()
        self.models_menu.addAction(self.act_ptr_multi_ocr)
        self.models_menu.addAction(self.act_ptr_multi_reopen)
        if hasattr(self, "_place_kraken_auto_revision_action_at_bottom"):
            self._place_kraken_auto_revision_action_at_bottom()
    self.ptr_update_feature_texts()
def _ptr_update_feature_texts_v2(self):
    if hasattr(self, "act_ptr_multi_ocr"):
        self.act_ptr_multi_ocr.setText(_ptr_ui_tr(self, "ptr_multi_ocr_btn"))
    if hasattr(self, "act_ptr_ai_tools"):
        self.act_ptr_ai_tools.setText(_ptr_ui_tr(self, "ptr_ai_tools_title"))
    if hasattr(self, "act_ptr_multi_reopen"):
        self.act_ptr_multi_reopen.setText(_ptr_ui_tr(self, "ptr_ai_reopen"))
    if hasattr(self, "btn_ptr_multi_ocr_bottom"):
        self.btn_ptr_multi_ocr_bottom.setText(_ptr_ui_tr(self, "ptr_multi_ocr_btn"))
        self.btn_ptr_multi_ocr_bottom.setToolTip(_ptr_ui_tr(self, "ptr_multi_ocr_btn_tip"))
    if hasattr(self, "btn_ptr_openrouter_ai_bottom"):
        self.btn_ptr_openrouter_ai_bottom.setText(_ptr_ui_tr(self, "ptr_openrouter_btn"))
        self.btn_ptr_openrouter_ai_bottom.setToolTip(_ptr_ui_tr(self, "ptr_openrouter_btn_tip"))
def _ptr_plain_theme_or_standard_icon(window, theme_name: str, std_icon):
    icon = QIcon.fromTheme(theme_name)
    if icon.isNull():
        icon = window.style().standardIcon(std_icon)
    return icon
def _ptr_is_dark_theme(window) -> bool:
    theme = str(getattr(window, "current_theme", "") or "").strip().lower()
    if theme in ("dark", "dunkel"):
        return True
    if theme in ("bright", "light", "hell"):
        return False
    try:
        return window.palette().color(QPalette.Window).lightness() < 128
    except Exception:
        return False
__all__ = [
    '_PtrHTTPResponseError',
    '_ptr_ai_build_postgres_json_v2',
    '_ptr_cancellable_http_post_json',
    '_ptr_raise_if_remote_cancelled',
    '_ptr_apply_prompt_template',
    '_ptr_feature_config_from_window_v2',
    '_ptr_followup_init_v2',
    '_ptr_install_feature_actions_v2',
    '_ptr_is_dark_theme',
    '_ptr_make_slug',
    '_ptr_normalize_postgres_json',
    '_ptr_plain_theme_or_standard_icon',
    '_ptr_postgres_empty_payload',
    '_ptr_prompt_from_config',
    '_ptr_prompt_owner',
    '_ptr_prompt_text_from_owner',
    '_ptr_remote_chat_completion_v2',
    '_ptr_save_feature_config_to_window_v2',
    '_ptr_update_feature_texts_v2',
]
register_globals('ptr', globals(), __all__)
