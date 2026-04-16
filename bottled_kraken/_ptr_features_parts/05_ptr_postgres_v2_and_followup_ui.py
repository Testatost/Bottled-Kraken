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
            "defaults": {"id": None, "full_name": None, "first_name": None, "last_name": None, "description": None, "source_excerpt": None},
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

def _ptr_ai_build_postgres_json_v2(config: PtrRemoteAIConfig, merged_text: str) -> Dict[str, Any]:
    cleaned_text = (merged_text or "").strip()
    if not cleaned_text:
        raise ValueError("merged_text must not be empty.")
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
        "Text:\n" + cleaned_text
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
            raise RuntimeError("OpenRouter requires a valid API key.")
        if (config.app_url or "").strip():
            headers["HTTP-Referer"] = config.app_url.strip()
        if (config.app_name or "").strip():
            headers["X-Title"] = config.app_name.strip()
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=max(5, int(config.timeout_seconds))) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            body = str(exc)
        body_clean = body.strip()
        if exc.code == 401 and (provider_name == "openrouter" or "openrouter.ai" in url.lower()):
            raise RuntimeError(
                "HTTP 401: OpenRouter authentication failed. Please check the API key and the base URL "
                "(expected usually: https://openrouter.ai/api/v1). Server response: " + body_clean
            ) from exc
        raise RuntimeError(f"HTTP {exc.code}: {body_clean}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Remote AI request failed: {exc}") from exc
    except socket.timeout as exc:
        raise RuntimeError("Remote AI request timed out.") from exc
    try:
        data = json.loads(raw)
    except Exception as exc:
        raise RuntimeError("Remote AI returned invalid JSON.") from exc
    if not isinstance(data, dict):
        raise RuntimeError("Remote AI returned an unexpected response format.")
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
    self.ai_pg_btn = QPushButton("AI + PostgreSQL")
    self.ai_neo_btn = QPushButton("AI + Neo4j")
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
    if hasattr(self, "revision_models_menu") and self.revision_models_menu is not None:
        self.revision_models_menu.addSeparator()
        self.revision_models_menu.addAction(self.act_ptr_ai_tools)
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

def _ptr_apply_new_button_icons(window):
    try:
        if hasattr(window, "btn_ptr_multi_ocr_bottom"):
            window.btn_ptr_multi_ocr_bottom.setIcon(
                window._themed_or_standard_icon("view-list-tree", QStyle.SP_FileDialogListView)
            )
        if hasattr(window, "btn_ptr_openrouter_ai_bottom"):
            window.btn_ptr_openrouter_ai_bottom.setIcon(
                window._themed_or_standard_icon("preferences-system", QStyle.SP_ComputerIcon)
            )
    except Exception:
        pass

def _ptr_rebuild_secondary_button_rows(window):
    if getattr(window, "_ptr_bottom_rows_built", False):
        return
    if not hasattr(window, "splitter") or window.splitter.count() < 2:
        return
    right_widget = window.splitter.widget(1)
    right_layout = right_widget.layout() if right_widget is not None else None
    if right_layout is None:
        return
    window._ptr_bottom_rows_built = True
    if not hasattr(window, "btn_ptr_multi_ocr_bottom"):
        window.btn_ptr_multi_ocr_bottom = QToolButton()
        window.btn_ptr_multi_ocr_bottom.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        window.btn_ptr_multi_ocr_bottom.clicked.connect(window.ptr_start_multi_ocr)
    if not hasattr(window, "btn_ptr_openrouter_ai_bottom"):
        window.btn_ptr_openrouter_ai_bottom = QToolButton()
        window.btn_ptr_openrouter_ai_bottom.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        window.btn_ptr_openrouter_ai_bottom.clicked.connect(window.ptr_open_ai_tools_for_current_task)
    old_lines_layout = None
    old_index = None
    existing_buttons = [
        getattr(window, "btn_import_lines", None),
        getattr(window, "btn_voice_fill", None),
        getattr(window, "btn_ai_revise_bottom", None),
        getattr(window, "btn_line_search", None),
    ]
    for i in range(right_layout.count()):
        item = right_layout.itemAt(i)
        lay = item.layout() if item is not None else None
        if lay is None:
            continue
        try:
            if any(btn is not None and lay.indexOf(btn) != -1 for btn in existing_buttons):
                old_lines_layout = lay
                old_index = i
                break
        except Exception:
            continue
    container = QWidget(right_widget)
    outer = QVBoxLayout(container)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(6)
    row1 = QHBoxLayout()
    row1.setContentsMargins(0, 0, 0, 0)
    row1.setSpacing(6)
    row2 = QHBoxLayout()
    row2.setContentsMargins(0, 0, 0, 0)
    row2.setSpacing(6)
    row1.addWidget(window.btn_import_lines)
    row1.addWidget(window.btn_voice_fill)
    row1.addWidget(window.btn_line_search)
    row1.addStretch(1)
    row2.addWidget(window.btn_ptr_multi_ocr_bottom)
    row2.addWidget(window.btn_ai_revise_bottom)
    row2.addWidget(window.btn_ptr_openrouter_ai_bottom)
    row2.addStretch(1)
    outer.addLayout(row1)
    outer.addLayout(row2)
    if old_lines_layout is not None:
        try:
            old_lines_layout.setContentsMargins(0, 0, 0, 0)
            old_lines_layout.setSpacing(0)
        except Exception:
            pass
        insert_index = old_index if isinstance(old_index, int) else max(0, right_layout.count() - 1)
        right_layout.insertWidget(insert_index, container)
    else:
        right_layout.addWidget(container)
    _ptr_update_feature_texts_v2(window)
    _ptr_apply_new_button_icons(window)
