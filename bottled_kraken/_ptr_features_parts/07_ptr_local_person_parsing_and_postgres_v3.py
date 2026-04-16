def _ptr_extract_year_candidates(source_text: str) -> List[Dict[str, Any]]:
    years = []
    seen = set()
    for match in re.finditer(r'(?<!\d)(1[0-9]{3}|20[0-9]{2})(?!\d)', str(source_text or '')):
        year = match.group(1)
        if year in seen:
            continue
        seen.add(year)
        years.append({
            'year': year,
            'context': (str(source_text or '')[max(0, match.start()-40):match.end()+40].strip() or None),
        })
    return years

def _ptr_extract_street_candidates_from_line(line: str) -> List[Dict[str, Any]]:
    txt = str(line or '')
    pattern = re.compile(
        r'([A-ZÄÖÜ][A-Za-zÄÖÜäöüß\-\. ]{1,80}?(?:straße|str\.?|gasse|weg|platz|allee|ring|markt|ufer|chaussee|hof))'
        r'(?:\s*(\d+[A-Za-z]?))?',
        flags=re.IGNORECASE,
    )
    out = []
    for match in pattern.finditer(txt):
        name = re.sub(r'\s+', ' ', match.group(1)).strip(' ,;:.')
        number = (match.group(2) or '').strip()
        desc = number or None
        out.append({'name': name, 'place': None, 'description': desc})
    return out

def _ptr_extract_org_candidates_from_line(line: str) -> List[Dict[str, Any]]:
    txt = str(line or '')
    hits = []
    patterns = [
        r'(Firma\s+[A-ZÄÖÜ][^,;:.]{1,90})',
        r'([A-ZÄÖÜ][A-Za-zÄÖÜäöüß&\- ]{2,80}\s+(?:AG|GmbH|KG|OHG|GbR|e\.V\.|S\.A\.|SARL|Inc\.?|Ltd\.?))',
        r'([A-ZÄÖÜ][A-Za-zÄÖÜäöüß&\- ]{2,80}\s+(?:Compagnie|Company|Werk|Werke|Manufaktur|Verlag|Bank))',
    ]
    for pat in patterns:
        for match in re.finditer(pat, txt, flags=re.IGNORECASE):
            name = re.sub(r'\s+', ' ', match.group(1)).strip(' ,;:.')
            hits.append({'name': name, 'type': 'organization', 'description': None})
    return hits

def _ptr_extract_place_candidates(source_text: str) -> List[Dict[str, Any]]:
    txt = str(source_text or '')
    hits = []
    for match in re.finditer(r'\b(?:in|aus|bei)\s+([A-ZÄÖÜ][A-Za-zÄÖÜäöüß\-]{2,60})', txt):
        hits.append(match.group(1).strip())
    hits = _ptr_unique_keep_order(hits)
    return [{'name': h, 'type': 'place', 'description': None} for h in hits]

def _ptr_ai_build_postgres_json_local(source_text: str) -> Dict[str, Any]:
    lines = _ptr_source_lines_for_postgres(source_text)
    payload = _ptr_postgres_empty_payload(source_text)
    persons = []
    streets = []
    organizations = []
    places = _ptr_extract_place_candidates(source_text)
    years = _ptr_extract_year_candidates(source_text)
    references = []
    person_index = {}
    street_index = {}
    org_index = {}
    place_index = {}
    for place in places:
        pid = f"place_{_ptr_make_slug(place.get('name') or 'place', 'place')}_{len(place_index)+1}"
        place['id'] = pid
        place_index[(place.get('name') or '').strip().lower()] = pid
    for idx, line in enumerate(lines, start=1):
        person_id = None
        person_name = _ptr_guess_person_name_from_line(line)
        if person_name:
            key = person_name.lower()
            person_id = person_index.get(key)
            if not person_id:
                person_id = f"person_{_ptr_make_slug(person_name, str(idx))}_{len(person_index)+1}"
                person_index[key] = person_id
                first_name = None
                last_name = None
                tokens = [t for t in re.split(r'\s+', person_name) if t]
                if len(tokens) >= 2:
                    first_name = tokens[0]
                    last_name = tokens[-1]
                persons.append({
                    'id': person_id,
                    'full_name': person_name,
                    'first_name': first_name,
                    'last_name': last_name,
                    'description': None,
                    'source_excerpt': line[:500],
                })
        for street in _ptr_extract_street_candidates_from_line(line):
            skey = (street.get('name') or '').strip().lower()
            if not skey:
                continue
            street_id = street_index.get(skey)
            if not street_id:
                street_id = f"street_{_ptr_make_slug(street.get('name') or 'street', str(idx))}_{len(street_index)+1}"
                street_index[skey] = street_id
                street['id'] = street_id
                streets.append(street)
            else:
                street['id'] = street_id
            if person_id:
                references.append({
                    'id': f'reference_{len(references)+1}',
                    'source_table': 'persons',
                    'source_id': person_id,
                    'relation_type': 'LIVES_AT',
                    'target_table': 'streets',
                    'target_id': street['id'],
                    'evidence': line[:500],
                })
        for org in _ptr_extract_org_candidates_from_line(line):
            okey = (org.get('name') or '').strip().lower()
            if not okey:
                continue
            org_id = org_index.get(okey)
            if not org_id:
                org_id = f"organization_{_ptr_make_slug(org.get('name') or 'organization', str(idx))}_{len(org_index)+1}"
                org_index[okey] = org_id
                org['id'] = org_id
                organizations.append(org)
            else:
                org['id'] = org_id
            if person_id:
                references.append({
                    'id': f'reference_{len(references)+1}',
                    'source_table': 'persons',
                    'source_id': person_id,
                    'relation_type': 'ASSOCIATED_WITH',
                    'target_table': 'organizations',
                    'target_id': org['id'],
                    'evidence': line[:500],
                })
        for place_name, place_id in place_index.items():
            if re.search(rf'\b{re.escape(place_name)}\b', line, flags=re.IGNORECASE):
                if person_id:
                    references.append({
                        'id': f'reference_{len(references)+1}',
                        'source_table': 'persons',
                        'source_id': person_id,
                        'relation_type': 'LOCATED_IN',
                        'target_table': 'places',
                        'target_id': place_id,
                        'evidence': line[:500],
                    })
    payload['persons'] = persons
    payload['places'] = places
    payload['streets'] = streets
    payload['years'] = years
    payload['organizations'] = organizations
    payload['references'] = references
    return _ptr_normalize_postgres_json(payload, source_text)

def _ptr_ai_build_postgres_json_v3(config: PtrRemoteAIConfig, merged_text: str) -> Dict[str, Any]:
    cleaned_text = (merged_text or '').strip()
    if not cleaned_text:
        raise ValueError('merged_text must not be empty.')
    try:
        return _ptr_ai_build_postgres_json_v2(config, cleaned_text)
    except Exception:
        return _ptr_ai_build_postgres_json_local(cleaned_text)

_ptr_ai_build_postgres_json = _ptr_ai_build_postgres_json_v3

def _ptr_multi_dialog_init_v3(self, rec_models: List[Tuple[str, str]], default_selected_paths: Optional[List[str]] = None, parent=None):
    QDialog.__init__(self, parent)
    self.setWindowTitle(_ptr_ui_tr(self, "ptr_multi_ocr_title"))
    self.setMinimumWidth(520)
    self._rec_models = rec_models
    self._default_selected = set(default_selected_paths or [])
    root = QVBoxLayout(self)
    root.addWidget(QLabel(_ptr_ui_tr(self, "ptr_multi_ocr_runs_label")))
    self.spin_runs = QSpinBox()
    self.spin_runs.setRange(1, 99)
    self.spin_runs.setSingleStep(1)
    self.spin_runs.setValue(3)
    root.addWidget(self.spin_runs)
    root.addSpacing(8)
    root.addWidget(QLabel(_ptr_ui_tr(self, "ptr_multi_ocr_models_label")))
    self.list_models = QListWidget()
    self.list_models.setSelectionMode(QAbstractItemView.MultiSelection)
    for name, path in self._rec_models:
        it = QListWidgetItem(name)
        it.setData(Qt.UserRole, path)
        self.list_models.addItem(it)
        if path in self._default_selected:
            it.setSelected(True)
    if self.list_models.count() > 0 and not self.list_models.selectedItems():
        self.list_models.item(0).setSelected(True)
    root.addWidget(self.list_models)
    self.chk_use_seg = QCheckBox(_ptr_ui_tr(self, "ptr_multi_ocr_use_seg"))
    self.chk_use_seg.setChecked(True)
    root.addWidget(self.chk_use_seg)
    bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    bb.accepted.connect(self.accept)
    bb.rejected.connect(self.reject)
    root.addWidget(bb)

def _ptr_followup_init_v3(self, parent=None):
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

def _ptr_install_feature_actions_v3(self):
    if getattr(self, "_ptr_feature_actions_installed", False):
        return
    self._ptr_feature_actions_installed = True
    self.act_ptr_multi_ocr = QAction(_ptr_ui_tr(self, "ptr_multi_ocr_btn"), self)
    self.act_ptr_multi_ocr.triggered.connect(self.ptr_start_multi_ocr)
    self.act_ptr_ai_tools = QAction(_ptr_ui_tr(self, "ptr_ai_tools_title"), self)
    self.act_ptr_ai_tools.triggered.connect(self.ptr_open_ai_tools_for_current_task)
    self.act_ptr_multi_reopen = QAction(_ptr_ui_tr(self, "ptr_ai_reopen"), self)
    self.act_ptr_multi_reopen.triggered.connect(self.ptr_reopen_multi_followup)
    # Keine zusätzlichen Toolbar-Buttons neben dem Sprach-Menü:
    # Multi-OCR und OpenRouter-KI bleiben nur in Menüs und in der unteren Button-Zeile.
    if hasattr(self, "toolbar") and self.toolbar is not None:
        try:
            self.toolbar.removeAction(self.act_ptr_multi_ocr)
        except Exception:
            pass
        try:
            self.toolbar.removeAction(self.act_ptr_ai_tools)
        except Exception:
            pass
    if hasattr(self, "models_menu") and self.models_menu is not None:
        self.models_menu.addSeparator()
        self.models_menu.addAction(self.act_ptr_multi_ocr)
        self.models_menu.addAction(self.act_ptr_multi_reopen)
    if hasattr(self, "revision_models_menu") and self.revision_models_menu is not None:
        self.revision_models_menu.addSeparator()
        self.revision_models_menu.addAction(self.act_ptr_ai_tools)
    self.ptr_update_feature_texts()

def _ptr_ai_dialog_save_merged_v3(self):
    text = self.merged_edit.toPlainText().strip()
    if not text:
        QMessageBox.information(self, _ptr_ui_tr(self, "ptr_ai_tools_title"), _ptr_ui_tr(self, "ptr_ai_no_merged"))
        return
    path, _ = QFileDialog.getSaveFileName(
        self,
        _ptr_ui_tr(self, "ptr_ai_btn_save_merged"),
        "ai_merged.txt",
        _ptr_ui_tr(self, "ptr_filter_text_files"),
    )
    if not path:
        return
    if not path.lower().endswith(".txt"):
        path += ".txt"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)

def _ptr_ai_dialog_save_result_v3(self):
    data = self._existing_result_data
    if data is None:
        txt = self.result_output_edit.toPlainText().strip()
        if txt:
            data = txt
    if data is None:
        QMessageBox.information(self, _ptr_ui_tr(self, "ptr_ai_tools_title"), _ptr_ui_tr(self, "ptr_ai_no_result"))
        return
    path, _ = QFileDialog.getSaveFileName(
        self,
        _ptr_ui_tr(self, "ptr_ai_btn_save_result"),
        "ai_result.json",
        _ptr_ui_tr(self, "ptr_filter_json_text_files"),
    )
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

def _ptr_apply_local_merge_to_task_v3(self, path: str):
    variants = list((getattr(self, "_ptr_multi_ocr_variants_by_path", {}) or {}).get(path, []))
    if not variants:
        QMessageBox.information(self, _ptr_ui_tr(self, "ptr_multi_ocr_title"), _ptr_ui_tr(self, "ptr_multi_no_variants"))
        return
    merged_text = _ptr_merge_ocr_texts_local(variants)
    if not merged_text.strip():
        QMessageBox.information(self, _ptr_ui_tr(self, "ptr_multi_ocr_title"), _ptr_ui_tr(self, "ptr_multi_local_merge_empty"))
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
    self.status_bar.showMessage(_ptr_ui_tr(self, "ptr_multi_local_merge_done", os.path.basename(path)), 3000)

def _ptr_open_ai_tools_v3(self, target_path: Optional[str] = None, auto_mode: Optional[str] = None):
    if not target_path:
        task = self._current_task()
        if not task:
            QMessageBox.warning(self, self._tr("warn_title"), _ptr_ui_tr(self, "ptr_select_file_first"))
            return
        target_path = task.path
    task = _ptr_find_task(self, target_path)
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), _ptr_ui_tr(self, "ptr_selected_file_missing"))
        return
    texts = list(self._ptr_multi_ocr_variants_by_path.get(target_path, []))
    if not texts and task.results:
        texts = [task.results[0]] if task.results[0] else []
    if not texts:
        QMessageBox.warning(self, self._tr("warn_title"), _ptr_ui_tr(self, "ptr_no_ocr_texts"))
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
    dlg.show()
    self._ptr_last_ai_dialog = dlg
    if auto_mode:
        dlg.auto_run(auto_mode)

def _ptr_store_ai_merge_v3(self, path: str, merged_text: str):
    merged_text = (merged_text or "").strip()
    if not merged_text:
        return
    self._ptr_ai_merged_by_path[path] = merged_text
    self.status_bar.showMessage(_ptr_ui_tr(self, "ptr_ai_merge_done", os.path.basename(path)), 3000)
