def _bk_sort_records_reading_order_v19(records, image_width: int, image_height: int,
                                       reading_mode: int = READING_MODES["TB_LR"]):
    return _bk_sort_records_strict_v19(records, image_width, image_height, reading_mode, deskew=True)

def _bk_sort_records_handwriting_simple_v19(records, reading_mode: int = READING_MODES["TB_LR"]):
    raw = []
    for r in records:
        bb = record_bbox(r)
        if bb:
            raw.append(bb)
    if raw:
        image_width = int(max(bb[2] for bb in raw)) + 1
        image_height = int(max(bb[3] for bb in raw)) + 1
    else:
        image_width = image_height = 0
    return _bk_sort_records_strict_v19(records, image_width, image_height, reading_mode, deskew=False)

sort_records_reading_order = _bk_sort_records_reading_order_v19

sort_records_handwriting_simple = _bk_sort_records_handwriting_simple_v19

def _bk_source_blocks_for_local_json_v19(recs: List[RecordView], page_w: int = 0, page_h: int = 0) -> List[List[str]]:
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
    lines = [_clean_ocr_text(rv.text) for rv in ordered if _clean_ocr_text(rv.text)]
    if not lines:
        return []
    blocks = []
    for idx in range(len(lines)):
        prev_line = lines[idx - 1] if idx > 0 else None
        curr_line = lines[idx]
        next_line = lines[idx + 1] if idx + 1 < len(lines) else None
        block = []
        if prev_line:
            block.append(prev_line)
        block.append(curr_line)
        if next_line:
            block.append(next_line)
        blocks.append(block)
    return blocks

_bk_source_blocks_for_local_json_v10 = _bk_source_blocks_for_local_json_v19

def _bk_lm_collect_current_text_v19(self, task) -> str:
    recs = self._current_recs_for_ai(task)
    if not recs:
        return ''
    page_w = 0
    page_h = 0
    try:
        if task and task.results and task.results[2] is not None:
            page_w, page_h = task.results[2].size
    except Exception:
        page_w = 0
        page_h = 0
    blocks = _bk_source_blocks_for_local_json_v19(recs, page_w=page_w, page_h=page_h)
    if not blocks:
        lines = [_clean_ocr_text(rv.text) for rv in recs if _clean_ocr_text(rv.text)]
        blocks = [[line] for line in lines]
    return _bk_blocks_to_text_v10(blocks).strip()

_bk_lm_collect_current_text = _bk_lm_collect_current_text_v19

MainWindow._bk_lm_collect_current_text = _bk_lm_collect_current_text_v19

def _bk_lm_generate_local_json_v19(self, schema_kind: str):
    task = _bk_lm_get_current_done_task(self)
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return
    source_text = _bk_lm_collect_current_text_v19(self, task)
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
        notice_text = self._tr("dlg_local_json_notice_text_neo4j")
    else:
        self.status_bar.showMessage(self._tr("msg_local_json_started_postgres"))
        notice_text = self._tr("dlg_local_json_notice_text_postgres")
    self._log(self._tr_log("log_local_json_started", os.path.basename(task.path), _bk_json_schema_kind_label(self, kind)))
    title_key = "dlg_local_json_title_neo4j" if kind == "neo4j" else "dlg_local_json_title_postgres"
    self._bk_local_json_dialog = BKLocalJsonNoticeDialog(self._tr(title_key), notice_text, self._tr, self)
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

_bk_lm_generate_local_json = _bk_lm_generate_local_json_v19

def _bk_prepare_sort_items_v20(records, image_width: int = 0, image_height: int = 0, *, deskew: bool = True):
    raw = []
    for r in records:
        bb = record_bbox(r)
        if bb:
            raw.append((r, bb))
    if not raw:
        return [], 20.0

    angles = []
    if deskew:
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
        cx = (left + right) / 2.0
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
            'cx': cx,
            'cy': cy,
            'h': h,
        })
    med_h = statistics.median(heights) if heights else 20.0
    return items, med_h

def _bk_sort_items_row_major_v20(items, reading_mode: int, med_h: float):
    if not items:
        return []
    rev_y = reading_mode in (READING_MODES['BT_LR'], READING_MODES['BT_RL'])
    rev_x = reading_mode in (READING_MODES['TB_RL'], READING_MODES['BT_RL'])
    top_tol = max(4.0, med_h * 0.34)
    cy_tol = max(6.0, med_h * 0.42)

    ordered_seed = sorted(items, key=lambda item: (item['top'], item['left'], item['cy']), reverse=rev_y)
    rows = []
    for item in ordered_seed:
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

def _bk_detect_column_splits_v20(items, med_h: float, image_width: int = 0):
    if len(items) < 4:
        return []
    left_edge = min(item['left'] for item in items)
    right_edge = max(item['right'] for item in items)
    span = max(1.0, right_edge - left_edge)
    page_w = float(image_width or 0)

    intervals = sorted((item['left'], item['right']) for item in items)
    merged = []
    merge_pad = max(2.0, med_h * 0.20)
    for left, right in intervals:
        if not merged:
            merged.append([left, right])
            continue
        prev = merged[-1]
        if left <= prev[1] + merge_pad:
            prev[1] = max(prev[1], right)
        else:
            merged.append([left, right])

    min_gap = max(40.0, med_h * 2.2, span * 0.05, page_w * 0.04 if page_w > 0 else 0.0)
    splits = []
    for i in range(len(merged) - 1):
        gap_left = merged[i][1]
        gap_right = merged[i + 1][0]
        gap = gap_right - gap_left
        if gap < min_gap:
            continue
        split_x = (gap_left + gap_right) / 2.0
        left_items = [item for item in items if item['cx'] < split_x]
        right_items = [item for item in items if item['cx'] >= split_x]
        crossing = sum(1 for item in items if item['left'] < split_x < item['right'])
        if len(left_items) < 2 or len(right_items) < 2:
            continue
        if crossing > max(1, int(len(items) * 0.08)):
            continue
        splits.append(split_x)
    return splits

def _bk_sort_records_strict_v20(records, image_width: int = 0, image_height: int = 0,
                                reading_mode: int = READING_MODES['TB_LR'], *, deskew: bool = True):
    items, med_h = _bk_prepare_sort_items_v20(records, image_width, image_height, deskew=deskew)
    if not items:
        return list(records)

    splits = _bk_detect_column_splits_v20(items, med_h, image_width=image_width)
    if not splits:
        return _bk_sort_items_row_major_v20(items, reading_mode, med_h)

    rev_x = reading_mode in (READING_MODES['TB_RL'], READING_MODES['BT_RL'])
    columns = {}
    for item in items:
        col_idx = 0
        while col_idx < len(splits) and item['cx'] >= splits[col_idx]:
            col_idx += 1
        columns.setdefault(col_idx, []).append(item)

    ordered = []
    column_indices = sorted(columns.keys(), reverse=rev_x)
    for col_idx in column_indices:
        col_items = columns.get(col_idx) or []
        if not col_items:
            continue
        ordered.extend(_bk_sort_items_row_major_v20(col_items, reading_mode, med_h))
    return ordered

sort_records_reading_order = lambda records, image_width, image_height, reading_mode=READING_MODES['TB_LR']: _bk_sort_records_strict_v20(records, image_width, image_height, reading_mode, deskew=True)

sort_records_handwriting_simple = lambda records, reading_mode=READING_MODES['TB_LR']: _bk_sort_records_strict_v20(
    records,
    int(max((record_bbox(r)[2] for r in records if record_bbox(r)), default=0)) + 1,
    int(max((record_bbox(r)[3] for r in records if record_bbox(r)), default=0)) + 1,
    reading_mode,
    deskew=False,
)

def _bk_prepare_sort_items_v20_final(records, image_width: int = 0, image_height: int = 0, *, deskew: bool = True):
    raw = []
    for r in records:
        bb = record_bbox(r)
        if bb:
            raw.append((r, bb))
    if not raw:
        return [], 20.0

    page_w = max(1.0, float(image_width or max(bb[2] for _, bb in raw)))
    page_h = max(1.0, float(image_height or max(bb[3] for _, bb in raw)))

    skew = 0.0
    if deskew:
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
                    angle = math.atan2(dy, dx)
                    if abs(angle) <= math.radians(15.0):
                        angles.append(angle)
        if angles:
            med = statistics.median(angles)
            mad = statistics.median([abs(a - med) for a in angles]) if len(angles) > 1 else 0.0
            if abs(med) >= math.radians(0.20) and abs(med) <= math.radians(12.0) and mad <= math.radians(3.0):
                skew = med

    wc = page_w / 2.0
    hc = page_h / 2.0
    cs = math.cos(-skew)
    sn = math.sin(-skew)

    def _rot(x: float, y: float):
        x -= wc
        y -= hc
        xr = x * cs - y * sn
        yr = x * sn + y * cs
        return xr + wc, yr + hc

    def _deskew_bb(bb):
        if abs(skew) < 1e-6:
            return tuple(float(v) for v in bb)
        x0, y0, x1, y1 = bb
        pts = [_rot(x0, y0), _rot(x1, y0), _rot(x1, y1), _rot(x0, y1)]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (min(xs), min(ys), max(xs), max(ys))

    items = []
    heights = []
    for r, bb in raw:
        dbb = _deskew_bb(bb)
        left = float(dbb[0])
        top = float(dbb[1])
        right = float(dbb[2])
        bottom = float(dbb[3])
        h = max(1.0, bottom - top)
        items.append({
            'record': r,
            'bbox': bb,
            'dbb': dbb,
            'left': left,
            'top': top,
            'right': right,
            'bottom': bottom,
            'cx': (left + right) / 2.0,
            'cy': (top + bottom) / 2.0,
            'h': h,
            'w': max(1.0, right - left),
        })
        heights.append(h)
    med_h = statistics.median(heights) if heights else 20.0
    return items, med_h
