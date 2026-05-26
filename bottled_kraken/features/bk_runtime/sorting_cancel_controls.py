def _bk_group_rows_v20_final(items, med_h: float):
    if not items:
        return []
    top_tol = max(5.0, med_h * 0.42)
    cy_tol = max(6.0, med_h * 0.50)
    row_gap_break = max(5.0, med_h * 0.40)
    ordered_seed = sorted(items, key=lambda item: (item['top'], item['left'], item['cy'], item['cx']))
    rows = []
    for item in ordered_seed:
        chosen = None
        chosen_score = None
        for row in reversed(rows):
            if item['top'] > row['bottom'] + row_gap_break:
                break
            overlap = min(item['bottom'], row['bottom']) - max(item['top'], row['top'])
            min_h = max(1.0, min(item['h'], row['med_h']))
            overlap_ratio = overlap / min_h
            same_row = (
                overlap_ratio >= 0.16
                or abs(item['cy'] - row['cy']) <= cy_tol
                or abs(item['top'] - row['top_anchor']) <= top_tol
            )
            if not same_row:
                continue
            score = (
                abs(item['cy'] - row['cy']) * 1.0
                + abs(item['top'] - row['top_anchor']) * 0.7
                + abs(item['left'] - row['left_anchor']) * 0.02
            )
            if chosen is None or score < chosen_score:
                chosen = row
                chosen_score = score
        if chosen is None:
            rows.append({
                'top_anchor': item['top'],
                'left_anchor': item['left'],
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
            chosen['left_anchor'] = min(chosen['left_anchor'], item['left'])
            chosen['top'] = min(chosen['top'], item['top'])
            chosen['bottom'] = max(chosen['bottom'], item['bottom'])
            chosen['cy'] = ((chosen['cy'] * (n - 1)) + item['cy']) / n
            chosen['med_h'] = ((chosen['med_h'] * (n - 1)) + item['h']) / n
    return rows

def _bk_sort_single_flow_v20_final(items, reading_mode: int, med_h: float):
    if not items:
        return []
    rev_y = reading_mode in (READING_MODES['BT_LR'], READING_MODES['BT_RL'])
    rev_x = reading_mode in (READING_MODES['TB_RL'], READING_MODES['BT_RL'])
    rows = _bk_group_rows_v20_final(items, med_h)
    rows.sort(key=lambda row: (row['top_anchor'], row['top']), reverse=rev_y)
    ordered = []
    for row in rows:
        row['items'].sort(key=lambda item: (item['left'], item['cx'], item['top'], item['cy']), reverse=rev_x)
        ordered.extend(item['record'] for item in row['items'])
    return ordered

def _bk_detect_columns_v20_final(items, med_h: float, image_width: int = 0):
    if len(items) < 4:
        return []
    page_w = float(image_width or max((item['right'] for item in items), default=0.0) or 0.0)
    left_edge = min(item['left'] for item in items)
    right_edge = max(item['right'] for item in items)
    span = max(1.0, right_edge - left_edge)

    anchor_tol = max(18.0, med_h * 1.20)
    same_col_pad = max(6.0, med_h * 0.30)
    gutter_threshold = max(42.0, med_h * 2.4, span * 0.06, page_w * 0.05 if page_w > 0 else 0.0)

    by_left = sorted(items, key=lambda item: (item['left'], item['cx'], item['top']))
    cols = []
    for item in by_left:
        if not cols:
            cols.append({
                'anchor': item['left'],
                'left': item['left'],
                'right': item['right'],
                'items': [item],
            })
            continue
        prev = cols[-1]
        gap = item['left'] - prev['right']
        same_col = (
            item['left'] <= prev['right'] + same_col_pad
            or abs(item['left'] - prev['anchor']) <= anchor_tol
            or gap < gutter_threshold
        )
        if same_col:
            prev['items'].append(item)
            n = len(prev['items'])
            prev['anchor'] = ((prev['anchor'] * (n - 1)) + item['left']) / n
            prev['left'] = min(prev['left'], item['left'])
            prev['right'] = max(prev['right'], item['right'])
        else:
            cols.append({
                'anchor': item['left'],
                'left': item['left'],
                'right': item['right'],
                'items': [item],
            })

    merged = []
    for col in cols:
        if merged:
            prev = merged[-1]
            gap = col['left'] - prev['right']
            if len(col['items']) <= 2 and gap < gutter_threshold * 0.9:
                prev['items'].extend(col['items'])
                prev['right'] = max(prev['right'], col['right'])
                prev['anchor'] = ((prev['anchor'] * 0.8) + (col['anchor'] * 0.2))
                continue
        merged.append(col)
    cols = merged

    if len(cols) < 2:
        return []

    strong_gaps = []
    for i in range(len(cols) - 1):
        left_col = cols[i]
        right_col = cols[i + 1]
        gap = right_col['left'] - left_col['right']
        if gap < gutter_threshold:
            return []
        split_x = (left_col['right'] + right_col['left']) / 2.0
        crossing = sum(1 for item in items if item['left'] < split_x < item['right'])
        if crossing > max(1, int(len(items) * 0.06)):
            return []
        strong_gaps.append(gap)

    if not strong_gaps:
        return []

    min_items_per_col = 2 if len(items) >= 6 else 1
    usable_cols = [col for col in cols if len(col['items']) >= min_items_per_col]
    if len(usable_cols) < 2:
        return []

    return [col['items'] for col in usable_cols]

def _bk_sort_records_strict_v20_final(records, image_width: int = 0, image_height: int = 0,
                                      reading_mode: int = READING_MODES['TB_LR'], *, deskew: bool = True):
    items, med_h = _bk_prepare_sort_items_v20_final(records, image_width, image_height, deskew=deskew)
    if not items:
        return list(records)

    columns = _bk_detect_columns_v20_final(items, med_h, image_width=image_width)
    if not columns:
        ordered = _bk_sort_single_flow_v20_final(items, reading_mode, med_h)
    else:
        rev_x = reading_mode in (READING_MODES['TB_RL'], READING_MODES['BT_RL'])
        col_wrappers = []
        for col_items in columns:
            if not col_items:
                continue
            col_wrappers.append({
                'anchor': min(item['left'] for item in col_items),
                'items': col_items,
            })
        col_wrappers.sort(key=lambda col: col['anchor'], reverse=rev_x)
        ordered = []
        for col in col_wrappers:
            ordered.extend(_bk_sort_single_flow_v20_final(col['items'], reading_mode, med_h))

    ordered_ids = {id(r) for r in ordered}
    for r in records:
        if id(r) not in ordered_ids:
            ordered.append(r)
    return ordered

def _bk_sort_records_reading_order_v20_final(records, image_width: int, image_height: int,
                                             reading_mode: int = READING_MODES['TB_LR']):
    return _bk_sort_records_strict_v20_final(records, image_width, image_height, reading_mode, deskew=True)

def _bk_sort_records_handwriting_simple_v20_final(records, reading_mode: int = READING_MODES['TB_LR']):
    boxes = [record_bbox(r) for r in records if record_bbox(r)]
    if boxes:
        image_width = int(max(bb[2] for bb in boxes)) + 1
        image_height = int(max(bb[3] for bb in boxes)) + 1
    else:
        image_width = 0
        image_height = 0
    return _bk_sort_records_strict_v20_final(records, image_width, image_height, reading_mode, deskew=False)

sort_records_reading_order = _bk_sort_records_reading_order_v20_final

sort_records_handwriting_simple = _bk_sort_records_handwriting_simple_v20_final

def _bk_local_json_worker_cancel_v20(self):
    self._cancelled = True
    self.requestInterruption()
    conn = getattr(self, '_active_conn', None)
    self._active_conn = None
    try:
        sock = getattr(conn, 'sock', None)
    except Exception:
        sock = None
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

BKLocalStructuredJsonWorker.cancel = _bk_local_json_worker_cancel_v20

def _bk_lm_cancel_local_json_v20(self):
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

    for signal_name in ('finished_json', 'failed_json', 'status_changed', 'progress_changed'):
        try:
            getattr(worker, signal_name).disconnect()
        except Exception:
            pass

    try:
        worker.cancel()
    except Exception:
        pass

    try:
        worker.wait(150)
    except Exception:
        pass

    if worker.isRunning():
        try:
            worker.terminate()
        except Exception:
            pass
        try:
            worker.wait(300)
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

_bk_lm_cancel_local_json = _bk_lm_cancel_local_json_v20

try:
    MainWindow._bk_lm_cancel_local_json = _bk_lm_cancel_local_json_v20
except Exception:
    pass

class BKLocalJsonNoticeDialog(QDialog):
    cancel_requested = Signal()

    def __init__(self, title: str, message: str, tr_func, parent=None):
        super().__init__(parent)
        self._tr = tr_func
        self._base_message = str(message or '')
        self.setWindowTitle(title)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        self.setWindowFlag(Qt.Dialog, True)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        if parent is not None:
            self.setWindowModality(Qt.WindowModal)
        else:
            self.setWindowModality(Qt.ApplicationModal)
        self.setMinimumWidth(420)
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)
        row = QHBoxLayout()
        row.setSpacing(12)
        self.spinner = BusySpinnerWidget(self, diameter=42)
        row.addWidget(self.spinner, 0, Qt.AlignTop)
        self.lbl_status = QLabel(self._base_message)
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setMinimumWidth(320)
        self.lbl_status.setMaximumWidth(520)
        row.addWidget(self.lbl_status, 1)
        root.addLayout(row)
        self.btn_cancel = QPushButton(self._tr('btn_cancel'))
        self.btn_cancel.clicked.connect(self.cancel_requested.emit)
        root.addWidget(self.btn_cancel, 0, Qt.AlignRight)
        self.adjustSize()

    def set_status(self, text: str):
        # absichtlich keine wechselnden Fortschrittszahlen im Dialog
        self.lbl_status.setText(self._base_message)
        self.adjustSize()

    def set_progress(self, value: int):
        return
