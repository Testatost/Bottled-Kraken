from typing import Any, Dict, List, Optional, Tuple

def _ptr_prompt_owner(config):
    try:
        owner = getattr(config, "_bk_prompt_owner", None)
        return owner
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

def _ptr_ai_merge_ocr_texts(config: PtrRemoteAIConfig, ocr_texts: List[str]) -> str:
    cleaned_sources = [text.strip() for text in ocr_texts if text and text.strip()]
    if not cleaned_sources:
        raise ValueError("ocr_texts must contain at least one non-empty text entry.")
    joined_sources = "\n\n===== OCR SOURCE =====\n\n".join(cleaned_sources)
    system_prompt = (
        "You are an OCR text merge assistant.\n\n"
        "Your task is to merge multiple OCR outputs that come from the same original source.\n"
        "Create one best-effort corrected plain text version.\n\n"
        "Rules:\n"
        "- Return plain text only.\n"
        "- Do not return JSON.\n"
        "- Do not add explanations.\n"
        "- Do not summarize.\n"
        "- Do not invent missing facts.\n"
        "- Preserve names, dates, places, streets, numbers, and document structure whenever possible.\n"
        "- If OCR versions disagree, prefer the reading that is most consistent and plausible.\n"
        "- Preserve paragraph breaks where possible.\n"
        "- Remove obvious OCR garbage if it is clearly meaningless.\n"
    )
    user_prompt = "Merge the following OCR outputs into one corrected plain text version.\n\n" + joined_sources
    raw = _ptr_remote_chat_completion(config, [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ])
    content = _ptr_extract_content_from_chat_response(raw).strip()
    if not content:
        raise RuntimeError(self._tr("ptr_err_merge_empty"))
    return content

def _ptr_ai_build_postgres_json(config: PtrRemoteAIConfig, merged_text: str) -> Dict[str, Any]:
    cleaned_text = (merged_text or "").strip()
    if not cleaned_text:
        raise ValueError("merged_text must not be empty.")
    schema_template = (
        "{\n"
        '  "document": {...},\n'
        '  "persons": [...],\n'
        '  "places": [...],\n'
        '  "streets": [...],\n'
        '  "years": [...],\n'
        '  "organizations": [...],\n'
        '  "references": [...]\n'
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
        "- Split personal names into first_name and last_name when possible.\n"
        "- Normalize obvious entity categories such as person, place, street, year, organization, and document reference.\n"
    )
    default_user = (
        "Create a PostgreSQL-oriented JSON payload from the following text.\n\n"
        "Return exactly one JSON object with the following top-level keys:\n"
        "{schema_template}\n\n"
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
    required = {"document", "persons", "places", "streets", "years", "organizations", "references"}
    missing = required.difference(data.keys())
    if missing:
        raise RuntimeError(self._tr("ptr_err_pg_missing_keys", ", ".join(sorted(missing))))
    for key in ["persons", "places", "streets", "years", "organizations", "references"]:
        if not isinstance(data.get(key), list):
            raise RuntimeError(self._tr("ptr_err_pg_key_list", key))
    if not isinstance(data.get("document"), dict):
        raise RuntimeError(self._tr("ptr_err_pg_document_object"))
    return data

def _ptr_ai_build_neo4j_json(config: PtrRemoteAIConfig, merged_text: str) -> Dict[str, Any]:
    cleaned_text = (merged_text or "").strip()
    if not cleaned_text:
        raise ValueError("merged_text must not be empty.")
    schema_template = (
        "{\n"
        '  "nodes": [...],\n'
        '  "relationships": [...]\n'
        "}\n\n"
        'Node: { "id": "...", "label": "...", "type": "...", "properties": { ... } }\n'
        'Relationship: { "source": "...", "target": "...", "type": "...", "properties": { ... } }'
    )
    default_system = (
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
    default_user = (
        "Create a Neo4j-oriented graph JSON payload from the following text.\n\n"
        "Return exactly one JSON object with this top-level structure:\n"
        "{schema_template}\n\n"
        "Text:\n{ocr_text}"
    )
    system_prompt, user_prompt = _ptr_prompt_from_config(
        config,
        "ai_prompt_neo4j_system",
        "ai_prompt_neo4j_user",
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
    required = {"nodes", "relationships"}
    missing = required.difference(data.keys())
    if missing:
        raise RuntimeError(self._tr("ptr_err_neo_missing_keys", ", ".join(sorted(missing))))
    if not isinstance(data.get("nodes"), list):
        raise RuntimeError(self._tr("ptr_err_neo_nodes_list"))
    if not isinstance(data.get("relationships"), list):
        raise RuntimeError(self._tr("ptr_err_neo_rels_list"))
    return data

def _ptr_feature_config_from_window(window) -> PtrRemoteAIConfig:
    settings = getattr(window, "settings", None)
    getv = (lambda key, default: settings.value(key, default, type(default)) if settings is not None else default)
    return PtrRemoteAIConfig(
        provider_name=getv("ptr_remote_ai/provider", "openrouter"),
        api_key=getattr(window, "ptr_remote_ai_api_key", "") or "",
        base_url=getv("ptr_remote_ai/base_url", "https://openrouter.ai/api/v1"),
        model=getv("ptr_remote_ai/model", "openrouter/free"),
        timeout_seconds=int(getv("ptr_remote_ai/timeout", 90)),
        temperature=float(getv("ptr_remote_ai/temperature", 0.2)),
        app_name=getv("ptr_remote_ai/app_name", "Bottled Kraken"),
        app_url=getv("ptr_remote_ai/app_url", ""),
    )

def _ptr_save_feature_config_to_window(window, config: PtrRemoteAIConfig):
    window.ptr_remote_ai_api_key = config.api_key or ""
    if hasattr(window, "settings") and window.settings is not None:
        window.settings.setValue("ptr_remote_ai/provider", config.provider_name)
        window.settings.setValue("ptr_remote_ai/base_url", config.base_url)
        window.settings.setValue("ptr_remote_ai/model", config.model)
        window.settings.setValue("ptr_remote_ai/timeout", int(config.timeout_seconds))
        window.settings.setValue("ptr_remote_ai/temperature", float(config.temperature))
        window.settings.setValue("ptr_remote_ai/app_name", config.app_name)
        window.settings.setValue("ptr_remote_ai/app_url", config.app_url)

def _ptr_find_task(window, path: str) -> Optional[TaskItem]:
    return next((t for t in window.queue_items if t.path == path), None)

def _ptr_current_or_selected_target_tasks(window) -> List[TaskItem]:
    checked = window._checked_queue_tasks() if hasattr(window, "_checked_queue_tasks") else []
    selected = window._selected_queue_tasks() if hasattr(window, "_selected_queue_tasks") else []
    tasks = checked if checked else selected
    if not tasks:
        current = window._current_task() if hasattr(window, "_current_task") else None
        if current:
            tasks = [current]
    return [t for t in tasks if t is not None]

def _ptr_multi_default_rec_models(window) -> List[Tuple[str, str]]:
    models_found = []
    for path in list(getattr(window, "kraken_rec_models", []) or []):
        if path and os.path.exists(path):
            models_found.append((os.path.basename(path), path))
    if getattr(window, "model_path", "") and os.path.exists(window.model_path):
        if all(os.path.abspath(window.model_path) != os.path.abspath(p) for _, p in models_found):
            models_found.insert(0, (os.path.basename(window.model_path), window.model_path))
    return models_found

def _ptr_install_feature_actions(self):
    if getattr(self, "_ptr_feature_actions_installed", False):
        return
    self._ptr_feature_actions_installed = True
    self.act_ptr_multi_ocr = QAction(_ptr_lang_text(self, "Multi-OCR", "Multi-OCR"), self)
    self.act_ptr_multi_ocr.triggered.connect(self.ptr_start_multi_ocr)
    self.act_ptr_ai_tools = QAction(self._tr("ptr_ai_tools_title"), self)
    self.act_ptr_ai_tools.triggered.connect(self.ptr_open_ai_tools_for_current_task)
    self.act_ptr_multi_reopen = QAction(self._tr("ptr_multi_reopen_followup"), self)
    self.act_ptr_multi_reopen.triggered.connect(self.ptr_reopen_multi_followup)
    # Keine zusätzlichen Toolbar-Buttons für PTR-Features hier,
    # weil Multi-OCR und AI/OpenRouter bereits in der unteren Button-Zeile verfügbar sind.
    self.ptr_update_feature_texts()

def _ptr_update_feature_texts(self):
    if hasattr(self, "act_ptr_multi_ocr"):
        self.act_ptr_multi_ocr.setText(self._tr("ptr_multi_ocr_action"))
    if hasattr(self, "act_ptr_ai_tools"):
        self.act_ptr_ai_tools.setText(self._tr("ptr_ai_tools_title"))
    if hasattr(self, "act_ptr_multi_reopen"):
        self.act_ptr_multi_reopen.setText(self._tr("ptr_multi_reopen_followup"))

def _ptr_export_text_interactive(self, text: str, title: str, default_name: str):
    if not (text or "").strip():
        QMessageBox.information(self, self._tr("dlg_export_title"), self._tr("ptr_export_no_text"))
        return
    start_dir = getattr(self, "current_export_dir", "") or os.getcwd()
    path, _ = QFileDialog.getSaveFileName(self, title, os.path.join(start_dir, default_name), self._tr("filter_text_files"))
    if not path:
        return
    if not path.lower().endswith(".txt"):
        path += ".txt"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    self.current_export_dir = os.path.dirname(path)
    self.status_bar.showMessage(self._tr("ptr_status_exported", os.path.basename(path)), 3000)

def _ptr_export_json_interactive(self, data: dict, title: str, default_name: str):
    if not isinstance(data, dict):
        QMessageBox.information(self, self._tr("dlg_export_title"), self._tr("ptr_export_no_json"))
        return
    start_dir = getattr(self, "current_export_dir", "") or os.getcwd()
    path, _ = QFileDialog.getSaveFileName(self, title, os.path.join(start_dir, default_name), self._tr("filter_json_files"))
    if not path:
        return
    if not path.lower().endswith(".json"):
        path += ".json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    self.current_export_dir = os.path.dirname(path)
    self.status_bar.showMessage(self._tr("ptr_status_exported", os.path.basename(path)), 3000)

def _ptr_apply_local_merge_to_task(self, path: str):
    variants = list((getattr(self, "_ptr_multi_ocr_variants_by_path", {}) or {}).get(path, []))
    if not variants:
        QMessageBox.information(self, self._tr("ptr_multi_followup_title"), self._tr("ptr_msg_no_multi_ocr_variants"))
        return
    merged_text = _ptr_merge_ocr_texts_local(variants)
    if not merged_text.strip():
        QMessageBox.information(self, self._tr("ptr_multi_followup_title"), self._tr("ptr_msg_local_merge_no_text"))
        return
    self._ptr_ai_merged_by_path[path] = merged_text
    task = _ptr_find_task(self, path)
    if task and task.results:
        text, kr_records, im, recs = task.results
        merged_lines = [ln for ln in merged_text.splitlines()]
        if merged_lines and len(merged_lines) == len(recs):
            new_recs = [RecordView(i, merged_lines[i], recs[i].bbox) for i in range(len(merged_lines))]
            task.results = ("\n".join(merged_lines).strip(), kr_records, im, new_recs)
            if self._current_task() and self._current_task().path == path:
                self.load_results(path)
        self._update_queue_row(path)
    self.status_bar.showMessage(self._tr("ptr_status_local_merge_done", os.path.basename(path)), 3000)

def _ptr_open_ai_tools(self, target_path: Optional[str] = None, auto_mode: Optional[str] = None):
    if not target_path:
        task = self._current_task()
        if not task:
            QMessageBox.warning(self, self._tr("warn_title"), self._tr("ptr_warn_select_file_first"))
            return
        target_path = task.path
    task = _ptr_find_task(self, target_path)
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("ptr_warn_selected_file_missing"))
        return
    texts = list(self._ptr_multi_ocr_variants_by_path.get(target_path, []))
    if not texts and task.results:
        texts = [task.results[0]] if task.results[0] else []
    if not texts:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("ptr_warn_no_ocr_texts"))
        return
    dlg = PtrAIToolsDialog(self, config=_ptr_feature_config_from_window(self))
    dlg.setAttribute(Qt.WA_DeleteOnClose, True)
    dlg.set_ocr_inputs(texts)
    dlg.set_existing_merged_text(self._ptr_ai_merged_by_path.get(target_path, ""))
    def _remember():
        try:
            _ptr_save_feature_config_to_window(self, dlg.get_config())
        except Exception:
            pass
    dlg.finished.connect(_remember)
    dlg.merge_completed.connect(lambda text, p=target_path: self._ptr_store_ai_merge(p, text))
    dlg.postgres_completed.connect(lambda data, p=target_path: self._ptr_store_ai_postgres(p, data))
    dlg.neo4j_completed.connect(lambda data, p=target_path: self._ptr_store_ai_neo4j(p, data))
    dlg.pipeline_completed.connect(lambda merged, pg, neo, p=target_path: self._ptr_store_ai_pipeline(p, merged, pg, neo))
    try:
        dlg.showMaximized()
    except Exception:
        dlg.show()
    self._ptr_last_ai_dialog = dlg
    if auto_mode:
        dlg.auto_run(auto_mode)

def _ptr_store_ai_merge(self, path: str, merged_text: str):
    merged_text = (merged_text or "").strip()
    if not merged_text:
        return
    self._ptr_ai_merged_by_path[path] = merged_text
    self.status_bar.showMessage(self._tr("ptr_status_ai_merge_done", os.path.basename(path)), 3000)

def _ptr_store_ai_postgres(self, path: str, data: dict):
    if not isinstance(data, dict):
        return
    self._ptr_ai_postgres_by_path[path] = data
    self.status_bar.showMessage(self._tr("ptr_status_postgres_json_done", os.path.basename(path)), 3000)

def _ptr_store_ai_neo4j(self, path: str, data: dict):
    if not isinstance(data, dict):
        return
    self._ptr_ai_neo4j_by_path[path] = data
    self.status_bar.showMessage(self._tr("ptr_status_neo4j_json_done", os.path.basename(path)), 3000)

def _ptr_store_ai_pipeline(self, path: str, merged_text: str, postgres_data, neo4j_data):
    self._ptr_store_ai_merge(path, merged_text)
    if isinstance(postgres_data, dict):
        self._ptr_store_ai_postgres(path, postgres_data)
    if isinstance(neo4j_data, dict):
        self._ptr_store_ai_neo4j(path, neo4j_data)

def _ptr_export_ai_merge_for_current(self, path: str):
    text = self._ptr_ai_merged_by_path.get(path, "")
    default_name = f"{os.path.splitext(os.path.basename(path))[0]}_ai_merge.txt"
    self._ptr_export_text_interactive(text, self._tr("ptr_save_merged_title"), default_name)

def _ptr_export_ai_postgres_for_current(self, path: str):
    data = self._ptr_ai_postgres_by_path.get(path)
    default_name = f"{os.path.splitext(os.path.basename(path))[0]}_postgres.json"
    self._ptr_export_json_interactive(data, self._tr("ptr_btn_generate_postgres_json"), default_name)

def _ptr_export_ai_neo4j_for_current(self, path: str):
    data = self._ptr_ai_neo4j_by_path.get(path)
    default_name = f"{os.path.splitext(os.path.basename(path))[0]}_neo4j.json"
    self._ptr_export_json_interactive(data, self._tr("ptr_btn_generate_neo4j_json"), default_name)

def _ptr_open_multi_followup_for_path(self, path: str):
    variants = self._ptr_multi_ocr_variants_by_path.get(path, [])
    if not variants:
        QMessageBox.information(self, self._tr("ptr_multi_followup_title"), self._tr("ptr_msg_no_multi_ocr_variants"))
        return
    self._ptr_last_multi_followup_path = path
    choice = PtrMultiOCRFollowupDialog.get_choice(self)
    if choice == PtrMultiOCRFollowupDialog.CHOICE_CANCEL:
        return
    if choice == PtrMultiOCRFollowupDialog.CHOICE_LOCAL:
        self._ptr_apply_local_merge_to_task(path)
        return
    if choice == PtrMultiOCRFollowupDialog.CHOICE_AI:
        self._ptr_open_ai_tools(path, auto_mode=None)
        return
    if choice == PtrMultiOCRFollowupDialog.CHOICE_AI_POSTGRES:
        self._ptr_open_ai_tools(path, auto_mode="postgres")
        return
    if choice == PtrMultiOCRFollowupDialog.CHOICE_AI_NEO4J:
        self._ptr_open_ai_tools(path, auto_mode="neo4j")
        return
    if choice == PtrMultiOCRFollowupDialog.CHOICE_AI_BOTH:
        self._ptr_open_ai_tools(path, auto_mode="pipeline")
        return

def _ptr_reopen_multi_followup(self):
    target = getattr(self, "_ptr_last_multi_followup_path", None)
    if not target:
        QMessageBox.information(self, self._tr("ptr_multi_followup_title"), self._tr("ptr_msg_no_multi_followup"))
        return
    self._ptr_open_multi_followup_for_path(target)

def _ptr_start_multi_ocr(self):
    if not getattr(self, "queue_items", None):
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_queue_empty"))
        return
    try:
        self._scan_kraken_models()
    except Exception:
        pass
    rec_models = _ptr_multi_default_rec_models(self)
    if not rec_models:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("ptr_warn_no_recognition_models"))
        return
    default_selected = [self.model_path] if getattr(self, "model_path", "") else [rec_models[0][1]]
    dlg = PtrMultiOcrDialog(rec_models=rec_models, default_selected_paths=default_selected, parent=self)
    if dlg.exec() != QDialog.Accepted:
        return
    rec_paths = []
    seen = set()
    for p in dlg.selected_recognition_paths():
        if p and p not in seen:
            rec_paths.append(p)
            seen.add(p)
    if not rec_paths:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("ptr_warn_select_recognition_model"))
        return
    seg_path = self.seg_model_path if dlg.use_segmentation() else None
    if not seg_path or not os.path.exists(seg_path):
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("ptr_warn_select_segmentation_model"))
        return
    tasks = _ptr_current_or_selected_target_tasks(self)
    tasks = [t for t in tasks if t.path and os.path.exists(t.path)]
    if not tasks:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_queue_empty"))
        return
    job = PtrMultiOCRJob(
        input_paths=[t.path for t in tasks],
        recognition_model_paths=rec_paths,
        segmentation_model_path=seg_path,
        device=self.device_str,
        reading_direction=self.reading_direction,
        runs=dlg.runs(),
    )
    self._ptr_multi_processed_paths = []
    self._ptr_multi_ocr_worker = PtrMultiOCRWorker(job, parent=self)
    self._ptr_multi_ocr_worker.file_started.connect(self._ptr_on_multi_file_started)
    self._ptr_multi_ocr_worker.file_done.connect(self._ptr_on_multi_file_done)
    self._ptr_multi_ocr_worker.file_error.connect(self._ptr_on_multi_file_error)
    self._ptr_multi_ocr_worker.progress.connect(self.on_progress_update)
    self._ptr_multi_ocr_worker.finished_batch.connect(self._ptr_on_multi_batch_finished)
    self._ptr_multi_ocr_worker.failed.connect(self._ptr_on_multi_failed)
    self._ptr_multi_ocr_worker.device_resolved.connect(self.on_device_resolved)
    self._ptr_multi_ocr_worker.gpu_info.connect(self.on_gpu_info)
    self.act_play.setEnabled(False)
    self.act_stop.setEnabled(True)
    if hasattr(self, "act_ptr_multi_ocr"):
        self.act_ptr_multi_ocr.setEnabled(False)
    self._set_progress_busy()
    self._ptr_multi_ocr_worker.start()
