def _bk_local_json_build_neo4j_v9(self) -> Dict[str, Any]:
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
        "Important: the top-level value must be an object, not an array and not fenced markdown.\n\n"
        "Text:\n" + self.source_text
    )
    try:
        data = _bk_local_json_request_payload(self, system_prompt, user_prompt)
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

def _bk_local_json_worker_run_v9(self):
    try:
        if self._cancelled or self.isInterruptionRequested():
            raise RuntimeError(self._tr('msg_local_json_cancelled'))
        self.progress_changed.emit(3)
        self.status_changed.emit(self._tr('dlg_local_json_connecting'))
        if self.schema_kind == 'neo4j':
            self.progress_changed.emit(8)
            self.status_changed.emit(self._tr('status_local_json_generating'))
            data = self._build_neo4j_json()
        else:
            self.progress_changed.emit(8)
            self.status_changed.emit(self._tr('status_local_json_generating'))
            data = self._build_postgres_json()
        if self._cancelled or self.isInterruptionRequested():
            raise RuntimeError(self._tr('msg_local_json_cancelled'))
        usage = getattr(self, '_bk_last_usage', None) or {}
        used_tokens = usage.get('completion_tokens')
        if used_tokens is None:
            used_tokens = usage.get('total_tokens')
        if used_tokens is not None:
            max_tokens = max(int(getattr(self, 'max_tokens', 0) or 0), 1)
            percent = max(1, min(99, int(round((float(used_tokens) / float(max_tokens)) * 100.0))))
            self.progress_changed.emit(int(percent * 10))
        self.progress_changed.emit(100)
        self.finished_json.emit(self.path, self.schema_kind, data)
    except Exception as exc:
        self.failed_json.emit(self.path, self.schema_kind, str(exc))

BKLocalStructuredJsonWorker._bk_last_usage = None

BKLocalStructuredJsonWorker._request_json_payload = _bk_local_json_request_payload

BKLocalStructuredJsonWorker._request_json_object = _bk_local_json_request_object

BKLocalStructuredJsonWorker._build_postgres_json = _bk_local_json_build_postgres_v9

BKLocalStructuredJsonWorker._build_neo4j_json = _bk_local_json_build_neo4j_v9

BKLocalStructuredJsonWorker.run = _bk_local_json_worker_run_v9

def _bk_estimate_token_count_v10(text: Any) -> int:
    txt = _force_text(text or '').strip()
    if not txt:
        return 0
    chars = len(txt)
    words = len(re.findall(r'\S+', txt))
    est_chars = chars / 4.0
    est_words = words * 1.2
    return max(1, int(round(max(est_chars, est_words))))

def _bk_progress_from_tokens_v10(used_tokens: Any, max_tokens: Any, *, clamp_max: float = 99.0) -> Tuple[int, int, int]:
    try:
        used = int(float(used_tokens or 0))
    except Exception:
        used = 0
    try:
        max_tok = int(float(max_tokens or 0))
    except Exception:
        max_tok = 0
    max_tok = max(1, max_tok)
    percent = max(0.0, min(float(clamp_max), (float(used) / float(max_tok)) * 100.0))
    return used, max_tok, int(round(percent))

def _bk_emit_token_progress_v10(worker, used_tokens: Any, *, estimated: bool = False):
    used, max_tok, percent = _bk_progress_from_tokens_v10(used_tokens, getattr(worker, 'max_tokens', 0) or 0)
    try:
        worker.progress_changed.emit(int(percent * 10))
    except Exception:
        pass
    try:
        key = 'status_local_json_generating_estimated' if estimated else 'status_local_json_generating_tokens'
        worker.status_changed.emit(worker._tr(key, used, max_tok, percent))
    except Exception:
        pass

def _bk_emit_estimated_request_progress_v10(worker, system_prompt: str, user_prompt: str):
    prompt_est = _bk_estimate_token_count_v10(system_prompt) + _bk_estimate_token_count_v10(user_prompt)
    worker._bk_prompt_token_estimate = prompt_est
    _bk_emit_token_progress_v10(worker, prompt_est, estimated=True)
    try:
        worker.status_changed.emit(worker._tr('status_local_json_waiting_response'))
    except Exception:
        pass

def _bk_extract_token_usage_v10(data: Any, content: Any = None) -> Dict[str, Optional[int]]:
    usage = _bk_extract_token_usage(data)
    prompt = usage.get('prompt_tokens')
    completion = usage.get('completion_tokens')
    total = usage.get('total_tokens')
    if completion is None and content:
        completion = _bk_estimate_token_count_v10(content)
    if total is None and (prompt is not None or completion is not None):
        total = int(prompt or 0) + int(completion or 0)
    return {
        'prompt_tokens': prompt,
        'completion_tokens': completion,
        'total_tokens': total,
    }

def _bk_emit_usage_progress_v10(worker, data: Any):
    content = None
    try:
        content = worker._extract_message_content(data)
    except Exception:
        content = None
    usage = _bk_extract_token_usage_v10(data, content)
    worker._bk_last_usage = usage
    used_tokens = usage.get('total_tokens')
    if used_tokens is None:
        used_tokens = usage.get('completion_tokens')
    if used_tokens is None:
        used_tokens = usage.get('prompt_tokens')
    if used_tokens is None:
        used_tokens = getattr(worker, '_bk_prompt_token_estimate', None)
    if used_tokens is not None:
        _bk_emit_token_progress_v10(worker, used_tokens, estimated=False)

def _bk_record_x0_v10(rv: Any) -> float:
    try:
        if getattr(rv, 'bbox', None):
            return float(rv.bbox[0])
    except Exception:
        pass
    return 0.0

def _bk_record_y0_v10(rv: Any) -> float:
    try:
        if getattr(rv, 'bbox', None):
            return float(rv.bbox[1])
    except Exception:
        pass
    return 0.0

def _bk_sort_records_core_v10(records, image_width: int, image_height: int, reading_mode: int, *, simple: bool = False):
    raw = []
    for r in records:
        bb = record_bbox(r)
        if bb:
            raw.append((r, bb))
    if not raw:
        return list(records)

    rev_y = reading_mode in (READING_MODES['BT_LR'], READING_MODES['BT_RL'])
    rev_x = reading_mode in (READING_MODES['TB_RL'], READING_MODES['BT_RL'])

    def cx(bb):
        return (bb[0] + bb[2]) / 2.0

    def cy(bb):
        return (bb[1] + bb[3]) / 2.0

    deskew_items = []
    if simple:
        for r, bb in raw:
            deskew_items.append((r, bb, bb))
    else:
        angles = []
        for r, _ in raw:
            bl = getattr(r, 'baseline', None)
            pts = _coerce_points(bl)
            if len(pts) >= 2:
                x1, y1 = pts[0]
                x2, y2 = pts[-1]
                dx = x2 - x1
                dy = y2 - y1
                if abs(dx) > 1.0:
                    a = math.atan2(dy, dx)
                    if abs(a) < math.radians(20):
                        angles.append(a)
        skew = statistics.median(angles) if angles else 0.0
        cs = math.cos(-skew)
        sn = math.sin(-skew)
        wc = max(1.0, float(image_width)) / 2.0
        hc = max(1.0, float(image_height)) / 2.0

        def rot(x, y):
            x -= wc
            y -= hc
            xr = x * cs - y * sn
            yr = x * sn + y * cs
            return xr + wc, yr + hc

        def deskew_bb(bb):
            x0, y0, x1, y1 = bb
            pts = [rot(x0, y0), rot(x1, y0), rot(x1, y1), rot(x0, y1)]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            return (min(xs), min(ys), max(xs), max(ys))

        for r, bb in raw:
            deskew_items.append((r, bb, deskew_bb(bb)))

    heights = [(dbb[3] - dbb[1]) for _, _, dbb in deskew_items if (dbb[3] - dbb[1]) > 0]
    med_h = statistics.median(heights) if heights else 20.0
    y_tol = max(12.0, med_h * (0.85 if simple else 0.75))

    items = []
    for r, bb, dbb in deskew_items:
        items.append({
            'record': r,
            'bb': bb,
            'dbb': dbb,
            'top': float(dbb[1]),
            'bottom': float(dbb[3]),
            'left': float(dbb[0]),
            'right': float(dbb[2]),
            'cy': cy(dbb),
            'cx': cx(dbb),
        })

    items.sort(key=lambda item: (item['top'], item['left']))
    rows = []
    for item in items:
        placed = False
        for row in rows:
            overlap = min(item['bottom'], row['bottom']) - max(item['top'], row['top'])
            same_visual_row = overlap >= -max(2.0, med_h * 0.12) or abs(item['cy'] - row['cy']) <= y_tol
            if same_visual_row:
                row['items'].append(item)
                row['top'] = min(row['top'], item['top'])
                row['bottom'] = max(row['bottom'], item['bottom'])
                row['cy'] = (row['cy'] * (len(row['items']) - 1) + item['cy']) / len(row['items'])
                placed = True
                break
        if not placed:
            rows.append({
                'top': item['top'],
                'bottom': item['bottom'],
                'cy': item['cy'],
                'items': [item],
            })

    rows.sort(key=lambda row: (row['cy'], row['top']), reverse=rev_y)
    ordered = []
    for row in rows:
        row['items'].sort(key=lambda item: (item['left'], item['cx']), reverse=rev_x)
        ordered.extend(item['record'] for item in row['items'])
    return ordered

def sort_records_handwriting_simple(records, reading_mode: int = READING_MODES['TB_LR']):
    raw = []
    for r in records:
        bb = record_bbox(r)
        if bb:
            raw.append((r, bb))
    if not raw:
        return list(records)
    max_x = max(bb[2] for _, bb in raw)
    max_y = max(bb[3] for _, bb in raw)
    return _bk_sort_records_core_v10(records, int(max_x) + 1, int(max_y) + 1, reading_mode, simple=True)

def sort_records_reading_order(records, image_width: int, image_height: int, reading_mode: int = READING_MODES['TB_LR']):
    return _bk_sort_records_core_v10(records, image_width, image_height, reading_mode, simple=False)

def cluster_columns(records: List[RecordView], x_threshold: int = 45):
    items = [r for r in records if getattr(r, 'bbox', None)]
    if not items:
        return []
    xs0 = [float(r.bbox[0]) for r in items]
    xs1 = [float(r.bbox[2]) for r in items]
    hs = [max(1.0, float(r.bbox[3] - r.bbox[1])) for r in items]
    span = max(xs1) - min(xs0) if xs0 and xs1 else 0.0
    med_h = statistics.median(hs) if hs else 20.0
    base_tol = max(float(x_threshold), med_h * 1.5)
    column_gap = max(140.0, span * 0.22, med_h * 6.0)
    raw = sorted(items, key=lambda r: (float(r.bbox[0]), float(r.bbox[1])))
    cols: List[Dict[str, Any]] = []
    for rv in raw:
        x0 = float(rv.bbox[0])
        if not cols:
            cols.append({'anchor': x0, 'max_x': float(rv.bbox[2]), 'items': [rv]})
            continue
        prev = cols[-1]
        gap_from_prev = x0 - prev['max_x']
        same_column = abs(x0 - prev['anchor']) <= base_tol or gap_from_prev < column_gap
        if same_column:
            prev['items'].append(rv)
            prev['anchor'] = (prev['anchor'] * 0.8) + (x0 * 0.2)
            prev['max_x'] = max(prev['max_x'], float(rv.bbox[2]))
        else:
            cols.append({'anchor': x0, 'max_x': float(rv.bbox[2]), 'items': [rv]})
    merged: List[Dict[str, Any]] = []
    for col in cols:
        if merged and len(col['items']) <= 2:
            gap = col['anchor'] - merged[-1]['max_x']
            if gap < column_gap * 0.75:
                merged[-1]['items'].extend(col['items'])
                merged[-1]['max_x'] = max(merged[-1]['max_x'], col['max_x'])
                continue
        merged.append(col)
    merged.sort(key=lambda c: c['anchor'])
    return [c['items'] for c in merged]

def _bk_source_blocks_for_local_json_v10(recs: List[RecordView], page_w: int = 0, page_h: int = 0) -> List[List[str]]:
    cleaned_recs = [rv for rv in recs if _clean_ocr_text(getattr(rv, 'text', ''))]
    if not cleaned_recs:
        return []
    if any(getattr(rv, 'bbox', None) for rv in cleaned_recs):
        pw = int(page_w or max((rv.bbox[2] for rv in cleaned_recs if rv.bbox), default=0) or 0)
        ph = int(page_h or max((rv.bbox[3] for rv in cleaned_recs if rv.bbox), default=0) or 0)
        if pw > 0 and ph > 0:
            ordered = sort_records_reading_order(cleaned_recs, pw, ph, READING_MODES['TB_LR'])
        else:
            ordered = sorted(cleaned_recs, key=lambda rv: (_bk_record_y0_v10(rv), _bk_record_x0_v10(rv)))
    else:
        ordered = cleaned_recs
    boxes = [rv.bbox for rv in ordered if getattr(rv, 'bbox', None)]
    hs = [max(1.0, float(bb[3] - bb[1])) for bb in boxes]
    med_h = statistics.median(hs) if hs else 20.0
    min_x = min((float(bb[0]) for bb in boxes), default=0.0)
    estimated_page_w = float(page_w or max((bb[2] for bb in boxes), default=0) or 0.0)
    indent_threshold = max(20.0, med_h * 1.25)
    column_gap_threshold = max(140.0, estimated_page_w * 0.22, med_h * 6.0)
    blocks: List[List[str]] = []
    current: List[str] = []
    prev_bbox = None
    base_x = None
    for rv in ordered:
        txt = _clean_ocr_text(rv.text)
        if not txt:
            continue
        bb = getattr(rv, 'bbox', None)
        if not current:
            current = [txt]
            prev_bbox = bb
            base_x = float(bb[0]) if bb else None
            continue
        continuation = False
        if bb and prev_bbox and base_x is not None:
            y_gap = max(0.0, float(bb[1]) - float(prev_bbox[3]))
            x_shift = float(bb[0]) - float(base_x)
            clear_new_column = (float(bb[0]) - min_x) >= column_gap_threshold
            if (not clear_new_column) and len(current) < 3 and y_gap <= med_h * 1.8:
                if x_shift >= indent_threshold:
                    continuation = True
                elif x_shift >= indent_threshold * 0.55 and len(txt) <= 100:
                    continuation = True
        elif len(current) < 3:
            continuation = True
        if continuation:
            current.append(txt)
            prev_bbox = bb or prev_bbox
        else:
            blocks.append(current)
            current = [txt]
            prev_bbox = bb
            base_x = float(bb[0]) if bb else None
    if current:
        blocks.append(current)
    normalized = []
    for block in blocks:
        block = [_clean_ocr_text(x) for x in block if _clean_ocr_text(x)]
        if block:
            normalized.append(block[:3])
    return normalized
