def _bk_prepare_sort_items_v21(records, image_width: int = 0, image_height: int = 0, *, deskew: bool = True):
    raw = []
    for r in records:
        bb = record_bbox(r)
        if bb:
            raw.append((r, bb))
    if not raw:
        return [], 20.0, 0.0, 0.0

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
                    a = math.atan2(dy, dx)
                    if abs(a) <= math.radians(15.0):
                        angles.append(a)
        if angles:
            med = statistics.median(angles)
            mad = statistics.median([abs(a - med) for a in angles]) if len(angles) > 1 else 0.0
            if math.radians(0.20) <= abs(med) <= math.radians(12.0) and mad <= math.radians(3.0):
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
        w = max(1.0, right - left)
        heights.append(h)
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
            'w': w,
        })
    med_h = statistics.median(heights) if heights else 20.0
    return items, med_h, page_w, page_h

def _bk_group_rows_v21(items, med_h: float):
    if not items:
        return []
    top_tol = max(6.0, med_h * 0.52)
    cy_tol = max(7.0, med_h * 0.58)
    row_gap_break = max(6.0, med_h * 0.48)
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
                overlap_ratio >= 0.12
                or abs(item['cy'] - row['cy']) <= cy_tol
                or abs(item['top'] - row['top_anchor']) <= top_tol
            )
            if not same_row:
                continue
            score = (
                abs(item['cy'] - row['cy']) * 1.0
                + abs(item['top'] - row['top_anchor']) * 0.8
                + abs(item['left'] - row['left_anchor']) * 0.01
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

def _bk_sort_single_flow_v21(items, reading_mode: int, med_h: float):
    if not items:
        return []
    rev_y = reading_mode in (READING_MODES['BT_LR'], READING_MODES['BT_RL'])
    rev_x = reading_mode in (READING_MODES['TB_RL'], READING_MODES['BT_RL'])
    rows = _bk_group_rows_v21(items, med_h)
    rows.sort(key=lambda row: (row['top_anchor'], row['top']), reverse=rev_y)
    ordered = []
    for row in rows:
        row['items'].sort(key=lambda item: (item['left'], item['cx'], item['top'], item['cy']), reverse=rev_x)
        ordered.extend(item['record'] for item in row['items'])
    return ordered

def _bk_detect_columns_v21(items, med_h: float, image_width: int = 0):
    # Spalten nur erkennen, wenn es wirklich deutliche Gassen gibt.
    # Leichte Einrückungen sollen ausdrücklich NICHT als neue Spalte gelten.
    if len(items) < 6:
        return []

    page_w = float(image_width or max((item['right'] for item in items), default=0.0) or 0.0)
    left_edge = min(item['left'] for item in items)
    right_edge = max(item['right'] for item in items)
    span = max(1.0, right_edge - left_edge)

    anchor_tol = max(28.0, med_h * 1.85)
    same_col_pad = max(10.0, med_h * 0.45)
    gutter_threshold = max(68.0, med_h * 3.2, span * 0.09, page_w * 0.07 if page_w > 0 else 0.0)
    min_items_per_col = max(3, int(round(len(items) * 0.18)))

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
            abs(item['left'] - prev['anchor']) <= anchor_tol
            or item['left'] <= prev['right'] + same_col_pad
            or gap < gutter_threshold * 1.15
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

    if len(cols) < 2:
        return []

    merged = []
    for col in cols:
        if not merged:
            merged.append(col)
            continue
        prev = merged[-1]
        gap = col['left'] - prev['right']
        weak_col = len(col['items']) < min_items_per_col
        if weak_col or gap < gutter_threshold * 1.25:
            prev['items'].extend(col['items'])
            prev['left'] = min(prev['left'], col['left'])
            prev['right'] = max(prev['right'], col['right'])
            prev['anchor'] = ((prev['anchor'] * 0.75) + (col['anchor'] * 0.25))
        else:
            merged.append(col)
    cols = merged

    usable = [col for col in cols if len(col['items']) >= min_items_per_col]
    if len(usable) < 2:
        return []

    # Nur echte Spalten behalten: zwischen den Spalten muss eine klare Gasse liegen,
    # und es dürfen kaum Linien diese Gasse überqueren.
    final_cols = []
    for idx, col in enumerate(usable):
        if idx > 0:
            prev = usable[idx - 1]
            gap = col['left'] - prev['right']
            if gap < gutter_threshold:
                return []
            split_x = (prev['right'] + col['left']) / 2.0
            crossing = sum(1 for item in items if item['left'] < split_x < item['right'])
            if crossing > max(1, int(len(items) * 0.04)):
                return []
        final_cols.append(col['items'])

    return final_cols if len(final_cols) >= 2 else []

def _bk_sort_records_strict_v21(records, image_width: int = 0, image_height: int = 0,
                                reading_mode: int = READING_MODES['TB_LR'], *, deskew: bool = True):
    items, med_h, page_w, page_h = _bk_prepare_sort_items_v21(records, image_width, image_height, deskew=deskew)
    if not items:
        return list(records)

    columns = _bk_detect_columns_v21(items, med_h, image_width=page_w)
    if not columns:
        ordered = _bk_sort_single_flow_v21(items, reading_mode, med_h)
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
            ordered.extend(_bk_sort_single_flow_v21(col['items'], reading_mode, med_h))

    ordered_ids = {id(r) for r in ordered}
    for r in records:
        if id(r) not in ordered_ids:
            ordered.append(r)
    return ordered

def _bk_sort_records_reading_order_v21(records, image_width: int, image_height: int,
                                       reading_mode: int = READING_MODES['TB_LR']):
    return _bk_sort_records_strict_v21(records, image_width, image_height, reading_mode, deskew=True)

def _bk_sort_records_handwriting_simple_v21(records, reading_mode: int = READING_MODES['TB_LR']):
    boxes = [record_bbox(r) for r in records if record_bbox(r)]
    if boxes:
        image_width = int(max(bb[2] for bb in boxes)) + 1
        image_height = int(max(bb[3] for bb in boxes)) + 1
    else:
        image_width = 0
        image_height = 0
    return _bk_sort_records_strict_v21(records, image_width, image_height, reading_mode, deskew=False)

sort_records_reading_order = _bk_sort_records_reading_order_v21

sort_records_handwriting_simple = _bk_sort_records_handwriting_simple_v21

def _bk_local_json_post_json_v21(self, payload: dict) -> dict:
    if self._cancelled or self.isInterruptionRequested():
        raise RuntimeError(self._tr('msg_local_json_cancelled'))

    body = json.dumps(payload).encode('utf-8')
    parsed = urllib.parse.urlparse(self.endpoint)
    if parsed.scheme not in ('http', 'https'):
        raise RuntimeError(self._tr('ai_err_bad_scheme', parsed.scheme))
    host = parsed.hostname
    port = parsed.port
    path = parsed.path or '/'
    if parsed.query:
        path += '?' + parsed.query
    if not host:
        raise RuntimeError(self._tr('ai_err_invalid_endpoint'))

    conn = None
    resp = None
    self._active_conn = None
    self._active_response = None
    self._active_socket = None

    def _refresh_active_socket(c, r=None):
        sock = None
        try:
            sock = getattr(c, 'sock', None)
        except Exception:
            sock = None
        if sock is None and r is not None:
            for attr_chain in (
                ('fp', 'raw', '_sock'),
                ('fp', 'raw', 'sock'),
                ('fp', 'fp', 'raw', '_sock'),
            ):
                try:
                    obj = r
                    for part in attr_chain:
                        obj = getattr(obj, part)
                    if obj is not None:
                        sock = obj
                        break
                except Exception:
                    continue
        self._active_socket = sock
        try:
            if sock is not None:
                sock.settimeout(0.5)
        except Exception:
            pass

    try:
        if parsed.scheme == 'https':
            conn = http.client.HTTPSConnection(host, port or 443, timeout=5)
        else:
            conn = http.client.HTTPConnection(host, port or 80, timeout=5)
        self._active_conn = conn
        conn.connect()
        _refresh_active_socket(conn)
        conn.putrequest('POST', path)
        conn.putheader('Content-Type', 'application/json')
        conn.putheader('Authorization', 'Bearer lm-studio')
        conn.putheader('Connection', 'close')
        conn.putheader('Content-Length', str(len(body)))
        conn.endheaders(body)

        while True:
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr('msg_local_json_cancelled'))
            try:
                resp = conn.getresponse()
                self._active_response = resp
                _refresh_active_socket(conn, resp)
                break
            except socket.timeout:
                continue

        chunks = []
        while True:
            if self._cancelled or self.isInterruptionRequested():
                raise RuntimeError(self._tr('msg_local_json_cancelled'))
            try:
                chunk = resp.read(65536)
            except socket.timeout:
                continue
            if not chunk:
                break
            chunks.append(chunk)

        raw = b''.join(chunks).decode('utf-8', errors='replace')
        if self._cancelled or self.isInterruptionRequested():
            raise RuntimeError(self._tr('msg_local_json_cancelled'))
        if resp.status >= 400:
            raise RuntimeError(self._tr('ai_err_http', resp.status, raw))
        return json.loads(raw)
    except socket.timeout:
        if self._cancelled or self.isInterruptionRequested():
            raise RuntimeError(self._tr('msg_local_json_cancelled'))
        raise RuntimeError(self._tr('ai_err_timeout'))
    except json.JSONDecodeError as e:
        raise RuntimeError(self._tr('ai_err_invalid_json', e))
    finally:
        try:
            if resp is not None:
                resp.close()
        except Exception:
            pass
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass
        self._active_conn = None
        self._active_response = None
        self._active_socket = None
