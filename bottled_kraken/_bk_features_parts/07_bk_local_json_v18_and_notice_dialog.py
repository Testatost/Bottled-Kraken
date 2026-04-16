_ptr_ai_build_postgres_json_local = _ptr_ai_build_postgres_json_local_v18

def _bk_local_json_build_postgres_v18(self) -> Dict[str, Any]:
    three_line_context = _bk_build_three_line_context_text_v18(self.source_text)
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
        "- Always resolve people, organizations, addresses and references with three-line context windows.\n"
        "- A name, occupation or address may span the previous line, the current line and the next line.\n"
        "- Indented continuation lines usually belong to the previous entry unless there is a clearly separate wide column.\n"
        "- Resolve common German given-name abbreviations when the text supports them, for example Frdr.=Friedrich, Joh.=Johann, Gstv.=Gustav, Wilh.=Wilhelm.\n"
        "- Expand abbreviated given names in first_name and full_name when you are confident, but keep the surname exactly as supported by the text.\n"
        "- Split person names carefully. If a surname appears before a comma, put it into last_name and put the following given names or abbreviations into first_name.\n"
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
        "- Deduplicate entities that appear across multiple three-line windows.\n"
        "- references should describe meaningful relations such as LIVES_AT, LOCATED_IN, MEMBER_OF, MENTIONS, or REFERENCED_IN.\n"
        "- If no relations are supported, return an empty references array.\n\n"
        "Three-line context windows:\n" + (three_line_context or self.source_text) + "\n\n"
        "OCR text:\n" + self.source_text
    )
    try:
        data = _bk_local_json_request_payload_v10(self, system_prompt, user_prompt)
        if isinstance(data, dict):
            nested = _bk_extract_nested_json_candidate(data, {'document', 'persons', 'places', 'streets', 'years', 'organizations', 'references'})
            if isinstance(nested, dict):
                data = nested
        if not isinstance(data, dict):
            raise RuntimeError(self._tr('ai_err_invalid_json', 'Top-level JSON object expected.'))
        return _ptr_normalize_postgres_json(data, self.source_text)
    except Exception:
        try:
            self.status_changed.emit(self._tr('status_local_json_generating_fallback'))
        except Exception:
            pass
        return _ptr_ai_build_postgres_json_local(self.source_text)

def _bk_local_json_build_neo4j_v18(self) -> Dict[str, Any]:
    three_line_context = _bk_build_three_line_context_text_v18(self.source_text)
    system_prompt = (
        "You are a graph information extraction assistant for OCR-derived texts.\n\n"
        "Your task is to transform the text into graph-oriented structured JSON.\n"
        "Return valid JSON only.\n\n"
        "Rules:\n"
        "- Return exactly one JSON object.\n"
        "- Do not return an array.\n"
        "- Do not include markdown.\n"
        "- Do not include explanations.\n"
        "- Do not invent unsupported entities or relationships.\n"
        "- Prefer fewer but well-supported relationships over many speculative ones.\n"
        "- Always resolve entities and relations with three-line context windows.\n"
        "- A person, address or organization may span the previous line, current line and next line.\n"
        "- Indented continuation lines usually belong to the previous entry unless there is a clearly separate wide column.\n"
        "- Resolve common German given-name abbreviations when the text supports them, for example Frdr.=Friedrich, Joh.=Johann, Gstv.=Gustav, Wilh.=Wilhelm.\n"
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
        "Important: the top-level value must be an object, not an array and not fenced markdown.\n"
        "Deduplicate repeated entities across the three-line context windows.\n\n"
        "Three-line context windows:\n" + (three_line_context or self.source_text) + "\n\n"
        "OCR text:\n" + self.source_text
    )
    try:
        data = _bk_local_json_request_payload_v10(self, system_prompt, user_prompt)
        graph = _bk_extract_nested_json_candidate(data, {'nodes', 'relationships'})
        if graph is None:
            raise RuntimeError(self._tr('ai_err_invalid_json', 'Top-level JSON object expected.'))
        return _bk_normalize_neo4j_json(graph, self.source_text)
    except Exception:
        try:
            self.status_changed.emit(self._tr('status_local_json_generating_fallback'))
        except Exception:
            pass
        return _bk_build_local_neo4j_json(self.source_text)

BKLocalStructuredJsonWorker._build_postgres_json = _bk_local_json_build_postgres_v18

BKLocalStructuredJsonWorker._build_neo4j_json = _bk_local_json_build_neo4j_v18

def _bk_lm_generate_local_json_v18(self, schema_kind: str):
    task = _bk_lm_get_current_done_task(self)
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return
    source_text = _bk_lm_collect_current_text_v18(self, task)
    if not source_text:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_no_text_for_json"))
        return
    model_id = self._resolve_ai_model_id()
    if not model_id:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_ai_model"))
        return
    if _bk_lm_any_job_running(self):
        return

    kind = (schema_kind or "postgres").strip().lower()
    self._bk_local_json_context = {"path": task.path, "schema_kind": kind}
    self.act_ai_revise.setEnabled(False)
    if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
        self.btn_ai_revise_bottom.setEnabled(False)
    if kind == "neo4j":
        self.status_bar.showMessage(self._tr("msg_local_json_started_neo4j"))
        wait_text = self._tr("dlg_local_json_wait_text_neo4j")
    else:
        self.status_bar.showMessage(self._tr("msg_local_json_started_postgres"))
        wait_text = self._tr("dlg_local_json_wait_text_postgres")
    self._log(self._tr_log("log_local_json_started", os.path.basename(task.path), _bk_json_schema_kind_label(self, kind)))
    title_key = "dlg_local_json_title_neo4j" if kind == "neo4j" else "dlg_local_json_title_postgres"
    self._bk_local_json_dialog = BKLocalJsonWaitDialog(self._tr(title_key), wait_text, self._tr, self)
    self._bk_local_json_dialog.cancel_requested.connect(lambda: _bk_lm_cancel_local_json(self))
    self._bk_local_json_dialog.show()
    self._bk_local_json_worker = BKLocalStructuredJsonWorker(
        path=task.path,
        source_text=source_text,
        schema_kind=kind,
        lm_model=model_id,
        endpoint=self.ai_endpoint,
        enable_thinking=self.ai_enable_thinking,
        temperature=self.ai_temperature,
        top_p=self.ai_top_p,
        top_k=self.ai_top_k,
        presence_penalty=self.ai_presence_penalty,
        repetition_penalty=self.ai_repetition_penalty,
        min_p=self.ai_min_p,
        max_tokens=max(int(getattr(self, "ai_max_tokens", 1200) or 1200), 2200),
        tr_func=self._tr,
        parent=self,
    )
    self._bk_local_json_worker.status_changed.connect(self._log)
    self._bk_local_json_worker.finished_json.connect(lambda path, kind, data: _bk_lm_on_local_json_done(self, path, kind, data))
    self._bk_local_json_worker.failed_json.connect(lambda path, kind, msg: _bk_lm_on_local_json_failed(self, path, kind, msg))
    self._bk_local_json_worker.start()

_bk_lm_generate_local_json = _bk_lm_generate_local_json_v18

class BKLocalJsonNoticeDialog(QDialog):
    cancel_requested = Signal()

    def __init__(self, title: str, message: str, tr_func, parent=None):
        super().__init__(parent)
        self._tr = tr_func
        self.setWindowTitle(title)
        self.setModal(False)
        self.setMinimumWidth(380)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)
        self.lbl_status = QLabel(message)
        self.lbl_status.setWordWrap(True)
        root.addWidget(self.lbl_status)
        self.btn_cancel = QPushButton(self._tr("btn_cancel"))
        self.btn_cancel.clicked.connect(self.cancel_requested)
        root.addWidget(self.btn_cancel)

    def set_status(self, text: str):
        if text:
            self.lbl_status.setText(str(text))

def _bk_cluster_columns_original_v19(records: List[RecordView], x_threshold: int = 45):
    cols = []
    for r in records:
        bb = getattr(r, 'bbox', None)
        if not bb:
            continue
        x0 = bb[0]
        placed = False
        for c in cols:
            if abs(c["x"] - x0) <= x_threshold:
                c["items"].append(r)
                c["x"] = int((c["x"] * 0.8) + (x0 * 0.2))
                placed = True
                break
        if not placed:
            cols.append({"x": x0, "items": [r]})
    cols.sort(key=lambda c: c["x"])
    return [c["items"] for c in cols]

cluster_columns = _bk_cluster_columns_original_v19

def _bk_sort_records_strict_v19(records, image_width: int = 0, image_height: int = 0,
                                reading_mode: int = READING_MODES["TB_LR"], *, deskew: bool = True):
    rev_y = reading_mode in (READING_MODES["BT_LR"], READING_MODES["BT_RL"])
    rev_x = reading_mode in (READING_MODES["TB_RL"], READING_MODES["BT_RL"])
    raw = []
    for r in records:
        bb = record_bbox(r)
        if bb:
            raw.append((r, bb))
    if not raw:
        return list(records)

    angles = []
    if deskew:
        for r, _ in raw:
            bl = getattr(r, "baseline", None)
            pts = _coerce_points(bl)
            if len(pts) >= 2:
                x1, y1 = pts[0]
                x2, y2 = pts[-1]
                dx = x2 - x1
                dy = y2 - y1
                if abs(dx) > 1.0:
                    a = math.atan2(dy, dx)
                    if abs(a) < math.radians(18):
                        angles.append(a)
    skew = statistics.median(angles) if angles else 0.0
    cs = math.cos(-skew)
    sn = math.sin(-skew)
    wc = max(1.0, float(image_width or max(bb[2] for _, bb in raw))) / 2.0
    hc = max(1.0, float(image_height or max(bb[3] for _, bb in raw))) / 2.0

    def rot(x, y):
        x -= wc
        y -= hc
        xr = x * cs - y * sn
        yr = x * sn + y * cs
        return xr + wc, yr + hc

    def norm_bb(bb):
        if not deskew or abs(skew) < 1e-6:
            return tuple(float(v) for v in bb)
        x0, y0, x1, y1 = bb
        pts = [rot(x0, y0), rot(x1, y0), rot(x1, y1), rot(x0, y1)]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (min(xs), min(ys), max(xs), max(ys))

    items = []
    heights = []
    for r, bb in raw:
        dbb = norm_bb(bb)
        top = float(dbb[1])
        bottom = float(dbb[3])
        left = float(dbb[0])
        right = float(dbb[2])
        cy = (top + bottom) / 2.0
        h = max(1.0, bottom - top)
        heights.append(h)
        items.append({
            'record': r,
            'bbox': bb,
            'dbb': dbb,
            'top': top,
            'bottom': bottom,
            'left': left,
            'right': right,
            'cy': cy,
            'h': h,
        })
    med_h = statistics.median(heights) if heights else 20.0
    top_tol = max(4.0, med_h * 0.34)
    cy_tol = max(6.0, med_h * 0.42)

    items.sort(key=lambda item: (item['top'], item['left'], item['cy']), reverse=rev_y)
    rows = []
    for item in items:
        chosen = None
        chosen_score = None
        for row in rows:
            overlap = min(item['bottom'], row['bottom']) - max(item['top'], row['top'])
            min_h = max(1.0, min(item['h'], row['med_h']))
            overlap_ratio = overlap / min_h
            close_top = abs(item['top'] - row['top_anchor']) <= top_tol
            close_cy = abs(item['cy'] - row['cy']) <= cy_tol
            if not (close_top or (close_cy and overlap_ratio >= -0.10)):
                continue
            score = abs(item['top'] - row['top_anchor']) + (abs(item['cy'] - row['cy']) * 0.35)
            if chosen is None or score < chosen_score:
                chosen = row
                chosen_score = score
        if chosen is None:
            rows.append({
                'top_anchor': item['top'],
                'top': item['top'],
                'bottom': item['bottom'],
                'cy': item['cy'],
                'med_h': item['h'],
                'items': [item],
            })
        else:
            chosen['items'].append(item)
            n = len(chosen['items'])
            chosen['top_anchor'] = ((chosen['top_anchor'] * (n - 1)) + item['top']) / n
            chosen['top'] = min(chosen['top'], item['top'])
            chosen['bottom'] = max(chosen['bottom'], item['bottom'])
            chosen['cy'] = ((chosen['cy'] * (n - 1)) + item['cy']) / n
            chosen['med_h'] = ((chosen['med_h'] * (n - 1)) + item['h']) / n

    rows.sort(key=lambda row: (row['top_anchor'], row['top']), reverse=rev_y)
    ordered = []
    for row in rows:
        row['items'].sort(key=lambda item: (item['left'], item['top'], item['cy']), reverse=rev_x)
        ordered.extend(item['record'] for item in row['items'])
    return ordered
