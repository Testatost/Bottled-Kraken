BKLocalStructuredJsonWorker._post_json = _bk_local_json_post_json_v21

def _bk_local_json_worker_cancel_v21(self):
    self._cancelled = True
    self.requestInterruption()

    resp = getattr(self, '_active_response', None)
    conn = getattr(self, '_active_conn', None)
    sock = getattr(self, '_active_socket', None)

    self._active_response = None
    self._active_conn = None
    self._active_socket = None

    for obj in (resp,):
        if obj is not None:
            try:
                obj.close()
            except Exception:
                pass

    if sock is not None:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            sock.close()
        except Exception:
            pass

    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass

BKLocalStructuredJsonWorker.cancel = _bk_local_json_worker_cancel_v21

def _bk_lm_cancel_local_json_v21(self):
    worker = getattr(self, '_bk_local_json_worker', None)
    context = getattr(self, '_bk_local_json_context', None) or {}
    dialog = getattr(self, '_bk_local_json_dialog', None)

    if worker is None:
        if dialog is not None:
            try:
                dialog.close()
            except Exception:
                pass
            self._bk_local_json_dialog = None
        return

    try:
        worker.cancel()
    except Exception:
        pass

    try:
        worker.wait(50)
    except Exception:
        pass

    if worker.isRunning():
        try:
            worker.terminate()
        except Exception:
            pass
        try:
            worker.wait(150)
        except Exception:
            pass

    for signal_name in ('finished_json', 'failed_json', 'status_changed', 'progress_changed'):
        try:
            getattr(worker, signal_name).disconnect()
        except Exception:
            pass

    try:
        worker.deleteLater()
    except Exception:
        pass

    self._bk_local_json_worker = None
    self._bk_local_json_context = None

    if hasattr(self, 'act_ai_revise') and self.act_ai_revise is not None:
        self.act_ai_revise.setEnabled(True)
    if hasattr(self, 'btn_ai_revise_bottom') and self.btn_ai_revise_bottom is not None:
        self.btn_ai_revise_bottom.setEnabled(True)

    if dialog is not None:
        try:
            dialog.close()
        except Exception:
            pass
    self._bk_local_json_dialog = None

    try:
        self.status_bar.showMessage(self._tr('msg_local_json_cancelled'), 4000)
    except Exception:
        pass
    try:
        if hasattr(self, '_log'):
            path = os.path.basename(str(context.get('path') or ''))
            kind = _bk_json_schema_kind_label(self, str(context.get('schema_kind') or 'postgres'))
            self._log(self._tr_log('log_local_json_failed', path, kind, self._tr('msg_local_json_cancelled')))
    except Exception:
        pass
    try:
        _bk_lm_update_dropdown_state(self)
    except Exception:
        pass

_bk_lm_cancel_local_json = _bk_lm_cancel_local_json_v21

try:
    MainWindow._bk_lm_cancel_local_json = _bk_lm_cancel_local_json_v21
except Exception:
    pass

def _bk_lm_generate_local_json_v21(self, schema_kind: str):
    task = _bk_lm_get_current_done_task(self)
    if not task:
        QMessageBox.warning(self, self._tr('warn_title'), self._tr('warn_need_done_for_ai'))
        return
    source_text = self._bk_lm_collect_current_text(task) if hasattr(self, '_bk_lm_collect_current_text') else _bk_lm_collect_current_text(self, task)
    if not source_text:
        QMessageBox.warning(self, self._tr('warn_title'), self._tr('warn_no_text_for_json'))
        return
    model_id = self._resolve_ai_model_id()
    if not model_id:
        QMessageBox.warning(self, self._tr('warn_title'), self._tr('warn_need_ai_model'))
        return
    if _bk_lm_any_job_running(self):
        return

    kind = (schema_kind or 'postgres').strip().lower()
    self._bk_local_json_context = {'path': task.path, 'schema_kind': kind}
    self.act_ai_revise.setEnabled(False)
    if hasattr(self, 'btn_ai_revise_bottom') and self.btn_ai_revise_bottom is not None:
        self.btn_ai_revise_bottom.setEnabled(False)

    if kind == 'neo4j':
        self.status_bar.showMessage(self._tr('msg_local_json_started_neo4j'))
        notice_text = self._tr('dlg_local_json_notice_text_neo4j')
    else:
        self.status_bar.showMessage(self._tr('msg_local_json_started_postgres'))
        notice_text = self._tr('dlg_local_json_notice_text_postgres')

    self._log(self._tr_log('log_local_json_started', os.path.basename(task.path), _bk_json_schema_kind_label(self, kind)))
    title_key = 'dlg_local_json_title_neo4j' if kind == 'neo4j' else 'dlg_local_json_title_postgres'
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
        max_tokens=max(int(getattr(self, 'ai_max_tokens', 1200) or 1200), 2200),
        tr_func=self._tr,
        parent=self,
    )
    self._bk_local_json_worker.status_changed.connect(self._log)
    self._bk_local_json_worker.finished_json.connect(lambda path, kind, data: _bk_lm_on_local_json_done(self, path, kind, data))
    self._bk_local_json_worker.failed_json.connect(lambda path, kind, msg: _bk_lm_on_local_json_failed(self, path, kind, msg))
    self._bk_local_json_worker.start()

_bk_lm_generate_local_json = _bk_lm_generate_local_json_v21

try:
    MainWindow._bk_lm_generate_local_json = _bk_lm_generate_local_json_v21
except Exception:
    pass

def _bk_sort_records_handwriting_simple_v22_from_v15(records, reading_mode: int = READING_MODES["TB_LR"]):
    """
    Wiederhergestellte einfache, stabile Sortierung aus v15 für einspaltige Handschrift:
    zuerst in der eingestellten vertikalen Richtung, innerhalb derselben Zeilenhöhe
    in der eingestellten horizontalen Richtung.
    """
    raw = []
    for r in records:
        bb = record_bbox(r)
        if bb:
            raw.append((r, bb))
    if not raw:
        return list(records)

    rev_y = reading_mode in (READING_MODES["BT_LR"], READING_MODES["BT_RL"])
    rev_x = reading_mode in (READING_MODES["TB_RL"], READING_MODES["BT_RL"])

    heights = [(bb[3] - bb[1]) for _, bb in raw if (bb[3] - bb[1]) > 0]
    med_h = statistics.median(heights) if heights else 20.0
    y_tol = max(10.0, med_h * 0.6)

    def cx(bb):
        return (bb[0] + bb[2]) / 2.0

    def cy(bb):
        return (bb[1] + bb[3]) / 2.0

    raw.sort(key=lambda x: cy(x[1]), reverse=rev_y)
    rows = []
    for r, bb in raw:
        my = cy(bb)
        placed = False
        for row in rows:
            if abs(my - row["cy"]) <= y_tol:
                row["items"].append((r, bb))
                n = len(row["items"])
                row["cy"] = ((row["cy"] * (n - 1)) + my) / n
                placed = True
                break
        if not placed:
            rows.append({
                "cy": my,
                "items": [(r, bb)],
            })

    rows.sort(key=lambda row: row["cy"], reverse=rev_y)
    ordered = []
    for row in rows:
        row["items"].sort(key=lambda x: cx(x[1]), reverse=rev_x)
        ordered.extend([r for r, _ in row["items"]])

    ordered_ids = {id(r) for r in ordered}
    for r in records:
        if id(r) not in ordered_ids:
            ordered.append(r)
    return ordered

def _bk_sort_records_reading_order_v22_from_v15(records, image_width: int, image_height: int,
                                                reading_mode: int = READING_MODES["TB_LR"]):
    """
    Wiederhergestellte stabile visuelle Sortierung aus v15.
    Die Reihenfolge folgt strikt der eingestellten Leserichtung:
    vertikal zuerst, innerhalb derselben Zeilenhöhe horizontal.
    Leichte Schräglagen werden über die Baselines herausgerechnet.
    """
    def cx(bb):
        return (bb[0] + bb[2]) / 2.0

    def cy(bb):
        return (bb[1] + bb[3]) / 2.0

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
        return (xr + wc, yr + hc)

    def deskew_bb(bb):
        x0, y0, x1, y1 = bb
        pts = [rot(x0, y0), rot(x1, y0), rot(x1, y1), rot(x0, y1)]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (min(xs), min(ys), max(xs), max(ys))

    items = []
    heights = []
    for r, bb in raw:
        dbb = deskew_bb(bb)
        items.append((r, bb, dbb))
        h = dbb[3] - dbb[1]
        if h > 0:
            heights.append(h)

    med_h = statistics.median(heights) if heights else 20.0
    y_tol = max(10.0, med_h * 0.75)

    items.sort(key=lambda x: cy(x[2]), reverse=rev_y)
    rows = []
    for r, bb, dbb in items:
        my = cy(dbb)
        placed = False
        for row in rows:
            if abs(my - row["cy"]) <= y_tol:
                row["items"].append((r, bb, dbb))
                n = len(row["items"])
                row["cy"] = ((row["cy"] * (n - 1)) + my) / n
                placed = True
                break
        if not placed:
            rows.append({"cy": my, "items": [(r, bb, dbb)]})

    rows.sort(key=lambda row: row["cy"], reverse=rev_y)
    ordered = []
    for row in rows:
        row["items"].sort(key=lambda x: cx(x[2]), reverse=rev_x)
        ordered.extend([r for r, _, _ in row["items"]])

    ordered_ids = {id(r) for r in ordered}
    for r in records:
        if id(r) not in ordered_ids:
            ordered.append(r)
    return ordered

sort_records_reading_order = _bk_sort_records_reading_order_v22_from_v15

sort_records_handwriting_simple = _bk_sort_records_handwriting_simple_v22_from_v15

def _ptr_unique_keep_order_v23(items: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in items or []:
        val = str(item or '').strip()
        if not val:
            continue
        key = val.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(val)
    return out

def _ptr_mask_secret_value_v23(value: str, keep_start: int = 4, keep_end: int = 2) -> str:
    secret = str(value or '')
    if not secret:
        return ''
    if len(secret) <= max(keep_start + keep_end, 6):
        return '*' * len(secret)
    return secret[:keep_start] + ('*' * max(6, len(secret) - keep_start - keep_end)) + secret[-keep_end:]

_DEF_PTR_DOTENV_PATHS_V23 = None

def _ptr_default_secret_search_paths_v23() -> List[str]:
    global _DEF_PTR_DOTENV_PATHS_V23
    if _DEF_PTR_DOTENV_PATHS_V23 is not None:
        return list(_DEF_PTR_DOTENV_PATHS_V23)
    app_dir = KRAKEN_MODELS_DIR or os.path.dirname(os.path.abspath(sys.argv[0]))
    home_dir = os.path.expanduser('~')
    candidates = [
        os.path.join(app_dir, '.env.local'),
        os.path.join(app_dir, '.env'),
        os.path.join(app_dir, '.secrets.env'),
        os.path.join(home_dir, '.bottled_kraken.env'),
        os.path.join(home_dir, '.config', 'bottled_kraken', '.env'),
    ]
    _DEF_PTR_DOTENV_PATHS_V23 = _ptr_unique_keep_order_v23(candidates)
    return list(_DEF_PTR_DOTENV_PATHS_V23)
