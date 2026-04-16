_DOTENV_LINE_RE_V23 = re.compile(r'^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$')

def _ptr_read_dotenv_file_v23(path: str) -> Dict[str, str]:
    data: Dict[str, str] = {}
    try:
        if not path or not os.path.exists(path) or not os.path.isfile(path):
            return data
        with open(path, 'r', encoding='utf-8') as fh:
            for raw_line in fh:
                line = raw_line.strip()
                if not line or line.startswith('#'):
                    continue
                m = _DOTENV_LINE_RE_V23.match(raw_line)
                if not m:
                    continue
                key = str(m.group(1) or '').strip()
                value = str(m.group(2) or '').strip()
                if not key:
                    continue
                if len(value) >= 2 and ((value[0] == value[-1] == '"') or (value[0] == value[-1] == "'")):
                    value = value[1:-1]
                value = value.strip()
                if value:
                    data[key] = value
    except Exception:
        return {}
    return data

def _ptr_candidate_api_env_names_v23(provider_name: str, base_url: str = '') -> List[str]:
    provider = str(provider_name or '').strip().lower()
    url = str(base_url or '').strip().lower()
    names: List[str] = []
    if provider:
        env_base = re.sub(r'[^a-z0-9]+', '_', provider).strip('_').upper()
        if env_base:
            names.extend([
                f'{env_base}_API_KEY',
                f'BOTTLED_KRAKEN_{env_base}_API_KEY',
                f'PTR_{env_base}_API_KEY',
            ])
    if provider == 'openrouter' or 'openrouter.ai' in url:
        names = [
            'OPENROUTER_API_KEY',
            'BOTTLED_KRAKEN_OPENROUTER_API_KEY',
            'PTR_OPENROUTER_API_KEY',
        ] + names
    names.extend([
        'BOTTLED_KRAKEN_REMOTE_AI_API_KEY',
        'PTR_REMOTE_AI_API_KEY',
    ])
    return _ptr_unique_keep_order_v23(names)

def _ptr_lookup_api_key_from_env_v23(provider_name: str, base_url: str = '') -> Tuple[str, str]:
    names = _ptr_candidate_api_env_names_v23(provider_name, base_url)
    for env_name in names:
        try:
            value = str(os.environ.get(env_name, '') or '').strip()
        except Exception:
            value = ''
        if value:
            return value, f'env:{env_name}'
    for dotenv_path in _ptr_default_secret_search_paths_v23():
        mapping = _ptr_read_dotenv_file_v23(dotenv_path)
        if not mapping:
            continue
        for env_name in names:
            value = str(mapping.get(env_name, '') or '').strip()
            if value:
                return value, f'file:{dotenv_path}:{env_name}'
    return '', ''

def _ptr_resolve_remote_api_key_v23(config: PtrRemoteAIConfig) -> Tuple[str, str]:
    direct = str(getattr(config, 'api_key', '') or '').strip()
    if direct:
        return direct, 'dialog'
    return _ptr_lookup_api_key_from_env_v23(
        getattr(config, 'provider_name', ''),
        getattr(config, 'base_url', ''),
    )

def _ptr_mask_sensitive_text_v23(text: str, secrets: Optional[List[str]] = None) -> str:
    masked = str(text or '')
    if not masked:
        return ''
    masked = re.sub(
        r'(?i)(Authorization\s*[:=]\s*Bearer\s+)([^\s,;"\']+)',
        lambda m: m.group(1) + _ptr_mask_secret_value_v23(m.group(2)),
        masked,
    )
    masked = re.sub(
        r'(?i)("api[_-]?key"\s*:\s*")([^"]+)(")',
        lambda m: m.group(1) + _ptr_mask_secret_value_v23(m.group(2)) + m.group(3),
        masked,
    )
    for secret in secrets or []:
        value = str(secret or '').strip()
        if value:
            masked = masked.replace(value, _ptr_mask_secret_value_v23(value))
    return masked

def _ptr_remote_ai_config_repr_v23(self):
    return (
        'PtrRemoteAIConfig('
        f'provider_name={self.provider_name!r}, '
        'api_key=<hidden>, '
        f'base_url={self.base_url!r}, '
        f'model={self.model!r}, '
        f'timeout_seconds={self.timeout_seconds!r}, '
        f'temperature={self.temperature!r}, '
        f'app_name={self.app_name!r}, '
        f'app_url={self.app_url!r}'
        ')'
    )

def _ptr_ai_dialog_apply_key_hints_v23(self):
    lang = _ptr_ui_lang(self)
    if lang == 'de':
        placeholder = 'leer lassen = OPENROUTER_API_KEY / .env verwenden'
        tooltip = (
            'API-Key optional direkt hier eingeben. '            'Sicherer ist es, den Key über OPENROUTER_API_KEY '            'oder BOTTLED_KRAKEN_OPENROUTER_API_KEY in einer .env/.env.local zu laden.'
        )
    elif lang == 'fr':
        placeholder = 'laisser vide = utiliser OPENROUTER_API_KEY / .env'
        tooltip = (
            "Vous pouvez saisir la clé ici, mais il est plus sûr de la charger via "
            "OPENROUTER_API_KEY ou BOTTLED_KRAKEN_OPENROUTER_API_KEY dans .env/.env.local."
        )
    else:
        placeholder = 'leave empty = use OPENROUTER_API_KEY / .env'
        tooltip = (
            'You can enter the API key here, but it is safer to load it via '            'OPENROUTER_API_KEY or BOTTLED_KRAKEN_OPENROUTER_API_KEY from .env/.env.local.'
        )
    try:
        self.api_key_edit.setPlaceholderText(placeholder)
        self.api_key_edit.setToolTip(tooltip)
    except Exception:
        pass
    try:
        self.save_api_key_cb.setToolTip(tooltip)
    except Exception:
        pass

def _ptr_ai_dialog_build_ui_v3(self):
    _ptr_ai_dialog_build_ui_v2(self)
    _ptr_ai_dialog_apply_key_hints_v23(self)

def _ptr_ai_dialog_set_config_v3(self, config: PtrRemoteAIConfig):
    _ptr_ai_dialog_set_config_v2(self, config)
    _ptr_ai_dialog_apply_key_hints_v23(self)

def _ptr_remote_chat_completion_v3(config: PtrRemoteAIConfig, messages: List[Dict[str, str]],
                                   *, expect_json: bool = False,
                                   max_tokens: Optional[int] = None) -> Dict[str, Any]:
    provider_name = (config.provider_name or '').strip().lower()
    base_url = _ptr_normalize_remote_base_url(config.base_url or '', provider_name)
    if not base_url:
        raise ValueError('Base URL must not be empty.')
    if not re.match(r'^https?://', base_url, flags=re.IGNORECASE):
        raise ValueError('Base URL must start with http:// or https://')
    url = base_url.rstrip('/')
    if not url.endswith('/chat/completions'):
        url += '/chat/completions'
    payload: Dict[str, Any] = {
        'model': (config.model or '').strip(),
        'messages': messages,
        'temperature': float(config.temperature),
    }
    if not payload['model']:
        raise ValueError('Model must not be empty.')
    if max_tokens is not None:
        payload['max_tokens'] = int(max_tokens)
    if expect_json:
        payload['response_format'] = {'type': 'json_object'}
    headers = {'Content-Type': 'application/json'}
    resolved_api_key, api_key_source = _ptr_resolve_remote_api_key_v23(config)
    if resolved_api_key:
        headers['Authorization'] = f'Bearer {resolved_api_key}'
    is_openrouter = provider_name == 'openrouter' or 'openrouter.ai' in url.lower()
    if is_openrouter:
        if not resolved_api_key:
            raise RuntimeError(
                'OpenRouter requires a valid API key. '                'Leave the field empty only if OPENROUTER_API_KEY or '                'BOTTLED_KRAKEN_OPENROUTER_API_KEY is available in the environment or in a local .env file.'
            )
        if (config.app_url or '').strip():
            headers['HTTP-Referer'] = config.app_url.strip()
        if (config.app_name or '').strip():
            headers['X-Title'] = config.app_name.strip()
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=max(5, int(config.timeout_seconds))) as response:
            raw = response.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode('utf-8', errors='replace')
        except Exception:
            body = str(exc)
        body_clean = _ptr_mask_sensitive_text_v23(body.strip(), [resolved_api_key])
        if exc.code == 401 and is_openrouter:
            source_hint = ''
            if api_key_source and api_key_source != 'dialog':
                source_hint = f' Key source: {api_key_source}.'
            raise RuntimeError(
                'HTTP 401: OpenRouter authentication failed. Please check the API key and the base URL '
                '(expected usually: https://openrouter.ai/api/v1).' + source_hint + ' Server response: ' + body_clean
            ) from exc
        raise RuntimeError(f'HTTP {exc.code}: {body_clean}') from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(_ptr_mask_sensitive_text_v23(f'Remote AI request failed: {exc}', [resolved_api_key])) from exc
    except socket.timeout as exc:
        raise RuntimeError('Remote AI request timed out.') from exc
    try:
        data = json.loads(raw)
    except Exception as exc:
        raise RuntimeError('Remote AI returned invalid JSON.') from exc
    if not isinstance(data, dict):
        raise RuntimeError('Remote AI returned an unexpected response format.')
    return data

PtrRemoteAIConfig.__repr__ = _ptr_remote_ai_config_repr_v23

PtrRemoteAIConfig.__str__ = _ptr_remote_ai_config_repr_v23

PtrAIToolsDialog._build_ui = _ptr_ai_dialog_build_ui_v3

PtrAIToolsDialog.set_config = _ptr_ai_dialog_set_config_v3

_ptr_remote_chat_completion = _ptr_remote_chat_completion_v3

_bk_patch24_prev_help_theme_values = _help_theme_values

def _help_theme_values_v24(theme: str) -> Dict[str, str]:
    colors = dict(_bk_patch24_prev_help_theme_values(theme))
    colors["warn_bg"] = colors.get("card_bg", colors.get("warn_bg", "#ffffff"))
    colors["ok_bg"] = colors.get("card_bg", colors.get("ok_bg", "#ffffff"))
    colors["warn_border"] = colors.get("card_border", colors.get("warn_border", "#d9dce3"))
    colors["ok_border"] = colors.get("card_border", colors.get("ok_border", "#d9dce3"))
    return colors

_help_theme_values = _help_theme_values_v24

def _bk_patch24_lang(obj) -> str:
    try:
        lang = getattr(obj, "current_lang", None)
        if lang:
            return str(lang)
    except Exception:
        pass
    try:
        lang = getattr(obj, "ui_lang", None)
        if lang:
            return str(lang)
    except Exception:
        pass
    try:
        parent = obj.parent() if hasattr(obj, "parent") else None
        if parent is not None and parent is not obj:
            return _bk_patch24_lang(parent)
    except Exception:
        pass
    return "de"

def _bk_patch24_tr(obj, key: str, *args) -> str:
    lang = _bk_patch24_lang(obj)
    try:
        return translation.translate(lang, key, *args)
    except Exception:
        return key

_BK_PATCH24_EXACT_ERROR_KEYS = {
    "Base URL must not be empty.": "ptr_err_base_url_empty",
    "Base URL must start with http:// or https://": "ptr_err_base_url_scheme",
    "Base URL must start with http:// or https://.": "ptr_err_base_url_scheme",
    "Model must not be empty.": "ptr_err_model_empty",
    "AI JSON response must be a top-level object.": "ptr_err_json_top_level",
    "Failed to parse JSON object from AI response.": "ptr_err_parse_json",
    "Remote AI response contains no choices.": "ptr_err_no_choices",
    "Remote AI choice format is invalid.": "ptr_err_choice_invalid",
    "Remote AI message format is invalid.": "ptr_err_message_invalid",
    "The model returned only reasoning_content and was truncated before the final answer. Increase max_tokens or use a non-reasoning model.": "ptr_err_reasoning_truncated",
    "The model returned only reasoning_content and no usable content.": "ptr_err_reasoning_only",
    "Remote AI response content is empty or unsupported.": "ptr_err_response_empty",
    "AI response content is empty.": "ptr_err_response_empty",
    "ocr_texts must contain at least one non-empty text entry.": "ptr_err_ocr_inputs_empty",
    "No OCR text input available.": "ptr_err_ocr_inputs_empty",
    "Merge task returned empty text.": "ptr_err_merge_empty",
    "merged_text must not be empty.": "ptr_err_merged_text_empty",
    "Baseline model not found.": "ptr_err_baseline_missing",
    "No input files selected.": "ptr_err_no_input_files",
    "No recognition models selected.": "ptr_err_no_rec_models",
    "No segmentation/baseline model selected.": "ptr_err_no_seg_model",
    "Recognition model not found.": "ptr_err_rec_model_missing_generic",
    "blla segmentation model not found.": "ptr_err_baseline_missing",
    "No blla segmentation model selected.": "ptr_err_no_seg_model",
    "Runs must be >= 1.": "ptr_err_runs_min",
}

def _bk_patch24_translate_error_message(obj, message: str) -> str:
    msg = str(message or "")
    key = _BK_PATCH24_EXACT_ERROR_KEYS.get(msg)
    if key:
        return _bk_patch24_tr(obj, key)

    patterns = [
        (r'^Recognition model not found: (.+)$', lambda m: _bk_patch24_tr(obj, 'ptr_err_rec_model_missing', m.group(1))),
        (r'^Unknown remote AI mode: (.+)$', lambda m: _bk_patch24_tr(obj, 'ptr_err_unknown_remote_mode', m.group(1))),
        (r'^HTTP (\d+):\s*(.*)$', lambda m: _bk_patch24_tr(obj, 'ptr_err_http_generic', m.group(1), m.group(2))),
        (r'^Remote AI request failed: (.+)$', lambda m: _bk_patch24_tr(obj, 'ptr_err_request_failed', m.group(1))),
        (r'^Remote AI request timed out\.?$', lambda m: _bk_patch24_tr(obj, 'ptr_err_request_timeout')),
        (r'^Remote AI returned invalid JSON\.?$', lambda m: _bk_patch24_tr(obj, 'ptr_err_invalid_json_response')),
        (r'^Remote AI returned an unexpected response format\.?$', lambda m: _bk_patch24_tr(obj, 'ptr_err_unexpected_response')),
        (r'^OpenRouter requires a valid API key\..*$', lambda m: _bk_patch24_tr(obj, 'ptr_err_openrouter_key_required')),
        (r'^HTTP 401: OpenRouter authentication failed\. Please check the API key and the base URL \(expected usually: https://openrouter\.ai/api/v1\)\.(?: Key source: ([^.]+)\.)? Server response: (.*)$',
         lambda m: _bk_patch24_tr(obj, 'ptr_err_http_401_openrouter',
                                  _bk_patch24_tr(obj, 'ptr_err_http_401_source_hint', m.group(1)) if m.group(1) else '',
                                  m.group(2))),
        (r'^PostgreSQL JSON is missing keys: (.+)$', lambda m: _bk_patch24_tr(obj, 'ptr_err_pg_missing_keys', m.group(1))),
        (r'^PostgreSQL JSON key "(.+)" must be a list\.$', lambda m: _bk_patch24_tr(obj, 'ptr_err_pg_key_list', m.group(1))),
        (r'^PostgreSQL JSON key "document" must be an object\.$', lambda m: _bk_patch24_tr(obj, 'ptr_err_pg_document_object')),
        (r'^Neo4j JSON is missing keys: (.+)$', lambda m: _bk_patch24_tr(obj, 'ptr_err_neo_missing_keys', m.group(1))),
        (r'^Neo4j JSON key "nodes" must be a list\.$', lambda m: _bk_patch24_tr(obj, 'ptr_err_neo_nodes_list')),
        (r'^Neo4j JSON key "relationships" must be a list\.$', lambda m: _bk_patch24_tr(obj, 'ptr_err_neo_rels_list')),
    ]
    for pat, fn in patterns:
        m = re.match(pat, msg, flags=re.S)
        if m:
            try:
                return fn(m)
            except Exception:
                break
    return msg

def _ptr_ai_dialog_start_worker_v24(self, mode: str, *, include_postgres: bool = True, include_neo4j: bool = True):
    if self._worker and self._worker.isRunning():
        return
    cfg = self.get_config()
    try:
        setattr(cfg, 'ui_lang', _bk_patch24_lang(self))
    except Exception:
        pass
    texts = self._collect_ocr_inputs()
    merged = self._collect_merged_text()
    if mode == 'merge':
        merged = ''
        self.progress_label.setText(_ptr_ui_tr(self, 'ptr_ai_running_merge'))
    elif mode == 'postgres':
        self.progress_label.setText(_ptr_ui_tr(self, 'ptr_ai_running_postgres'))
    elif mode == 'neo4j':
        self.progress_label.setText(_ptr_ui_tr(self, 'ptr_ai_running_neo4j'))
    else:
        self.progress_label.setText(_ptr_ui_tr(self, 'ptr_ai_running_pipeline'))
    self._worker = PtrRemoteAITaskWorker(
        mode=mode,
        config=cfg,
        ocr_texts=texts,
        merged_text=merged,
        include_postgres=include_postgres,
        include_neo4j=include_neo4j,
        parent=self,
    )
    try:
        setattr(self._worker, 'ui_lang', _bk_patch24_lang(self))
    except Exception:
        pass
    self._worker.result_ready.connect(self._on_worker_result)
    self._worker.failed.connect(self._on_worker_failed)
    self._worker.finished.connect(lambda: self._set_busy(False))
    self._set_busy(True)
    self._worker.start()
