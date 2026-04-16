class BKLocalJsonWaitDialog(QDialog):
    cancel_requested = Signal()

    def __init__(self, title: str, message: str, tr_func, parent=None):
        super().__init__(parent)
        self._tr = tr_func
        self.setWindowTitle(title)
        self.setModal(False)
        self.setMinimumWidth(360)
        lay = QVBoxLayout(self)
        self.lbl_status = QLabel(message)
        self.lbl_status.setWordWrap(True)
        lay.addWidget(self.lbl_status)
        self.btn_cancel = QPushButton(self._tr("btn_cancel"))
        self.btn_cancel.clicked.connect(self.cancel_requested)
        lay.addWidget(self.btn_cancel)

    def set_status(self, text: str):
        if text:
            self.lbl_status.setText(str(text))

def _bk_sort_records_reading_order_v18(records, image_width: int, image_height: int,
                                       reading_mode: int = READING_MODES["TB_LR"]):
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
        return xr + wc, yr + hc

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
    return ordered

def _bk_sort_records_handwriting_simple_v18(records, reading_mode: int = READING_MODES["TB_LR"]):
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
            rows.append({"cy": my, "items": [(r, bb)]})

    rows.sort(key=lambda row: row["cy"], reverse=rev_y)
    ordered = []
    for row in rows:
        row["items"].sort(key=lambda x: cx(x[1]), reverse=rev_x)
        ordered.extend([r for r, _ in row["items"]])
    return ordered

sort_records_reading_order = _bk_sort_records_reading_order_v18

sort_records_handwriting_simple = _bk_sort_records_handwriting_simple_v18

_BK_GERMAN_NAME_ABBREVIATIONS_V18 = {
    'fr': 'Franz',
    'frz': 'Franz',
    'frdr': 'Friedrich',
    'frd': 'Friedrich',
    'fridr': 'Friedrich',
    'frdrd': 'Friedrich',
    'fredr': 'Friedrich',
    'fred': 'Friedrich',
    'aug': 'August',
    'ad': 'Adolf',
    'adph': 'Adolph',
    'adol': 'Adolf',
    'adolf': 'Adolf',
    'adr': 'Andreas',
    'andr': 'Andreas',
    'ant': 'Anton',
    'anth': 'Anton',
    'bernh': 'Bernhard',
    'ber': 'Bernhard',
    'bern': 'Bernhard',
    'brnh': 'Bernhard',
    'chr': 'Christian',
    'chrd': 'Konrad',
    'chstph': 'Christoph',
    'christph': 'Christoph',
    'gstv': 'Gustav',
    'gust': 'Gustav',
    'hein': 'Heinrich',
    'heinr': 'Heinrich',
    'hnr': 'Heinrich',
    'joh': 'Johann',
    'johs': 'Johannes',
    'jul': 'Julius',
    'theod': 'Theodor',
    'thdr': 'Theodor',
    'traug': 'Traugott',
    'siegm': 'Siegmund',
    'sieg': 'Siegmund',
    'wilh': 'Wilhelm',
    'wlhm': 'Wilhelm',
    'wlhm': 'Wilhelm',
    'wilhm': 'Wilhelm',
    'gfrd': 'Gottfried',
    'gustv': 'Gustav',
    'ferd': 'Ferdinand',
    'herm': 'Hermann',
    'ludw': 'Ludwig',
    'rud': 'Rudolf',
}

def _bk_expand_name_abbreviation_token_v18(token: str) -> str:
    raw = _clean_ocr_text(token)
    if not raw:
        return raw
    prefix = ''
    suffix = ''
    while raw and not raw[0].isalnum():
        prefix += raw[0]
        raw = raw[1:]
    while raw and not raw[-1].isalnum():
        suffix = raw[-1] + suffix
        raw = raw[:-1]
    key = re.sub(r'[^A-Za-zÄÖÜäöüß]', '', raw).casefold()
    if not key:
        return token
    expanded = _BK_GERMAN_NAME_ABBREVIATIONS_V18.get(key)
    if not expanded:
        return token
    return prefix + expanded + suffix

def _bk_expand_name_block_v18(value: Any) -> Optional[str]:
    txt = _bk_clean_name_fragment(value)
    if not txt:
        return None
    parts = re.split(r'(\s+)', txt)
    expanded = []
    changed = False
    for part in parts:
        if not part or part.isspace():
            expanded.append(part)
            continue
        new_part = _bk_expand_name_abbreviation_token_v18(part)
        if new_part != part:
            changed = True
        expanded.append(new_part)
    out = ''.join(expanded).strip()
    return out if (changed and out) else txt

_bk_prev_split_person_name_heuristic_v18 = _bk_split_person_name_heuristic

def _bk_split_person_name_heuristic_v18(full_name: Any, first_name: Any, last_name: Any, description: Any, source_excerpt: Any):
    full, first, last = _bk_prev_split_person_name_heuristic_v18(full_name, first_name, last_name, description, source_excerpt)
    first = _bk_expand_name_block_v18(first)
    full = _bk_expand_name_block_v18(full)
    if full and last and ',' in full:
        left, right = full.split(',', 1)
        right = _bk_expand_name_block_v18(right)
        full = f"{_bk_clean_name_fragment(left)}, {_bk_clean_name_fragment(right)}" if right else _bk_clean_name_fragment(left)
    elif full and first and last:
        full = f"{last}, {first}"
    return full or None, first or None, last or None

_bk_split_person_name_heuristic = _bk_split_person_name_heuristic_v18

_bk_prev_ptr_normalize_postgres_json_v18 = _ptr_normalize_postgres_json

def _ptr_normalize_postgres_json_v18(data: Any, source_text: str) -> Dict[str, Any]:
    payload = _bk_prev_ptr_normalize_postgres_json_v18(data, source_text)
    persons = payload.get('persons')
    if isinstance(persons, list):
        for item in persons:
            if not isinstance(item, dict):
                continue
            full, first, last = _bk_split_person_name_heuristic(
                item.get('full_name'),
                item.get('first_name'),
                item.get('last_name'),
                item.get('description'),
                item.get('source_excerpt'),
            )
            if full is not None:
                item['full_name'] = full
            item['first_name'] = first
            item['last_name'] = last
    return payload

_ptr_normalize_postgres_json = _ptr_normalize_postgres_json_v18

def _bk_build_three_line_context_text_v18(source_text: str) -> str:
    lines = _ptr_source_lines_for_postgres(source_text)
    if not lines:
        return ''
    windows = []
    total = len(lines)
    for idx in range(total):
        prev_line = lines[idx - 1] if idx > 0 else ''
        cur_line = lines[idx]
        next_line = lines[idx + 1] if idx + 1 < total else ''
        windows.append(
            f"[{idx + 1:04d}/{total:04d}]\n"
            f"previous: {prev_line}\n"
            f"current: {cur_line}\n"
            f"next: {next_line}"
        )
    return '\n\n'.join(windows)

_bk_build_three_line_context_text_v10 = _bk_build_three_line_context_text_v18

def _bk_lm_collect_current_text_v18(self, task) -> str:
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
    cleaned_recs = [rv for rv in recs if _clean_ocr_text(getattr(rv, 'text', ''))]
    if not cleaned_recs:
        return ''
    if any(getattr(rv, 'bbox', None) for rv in cleaned_recs):
        pw = int(page_w or max((rv.bbox[2] for rv in cleaned_recs if rv.bbox), default=0) or 0)
        ph = int(page_h or max((rv.bbox[3] for rv in cleaned_recs if rv.bbox), default=0) or 0)
        if pw > 0 and ph > 0:
            ordered = sort_records_reading_order(cleaned_recs, pw, ph, READING_MODES['TB_LR'])
        else:
            ordered = sorted(cleaned_recs, key=lambda rv: (_bk_record_y0_v10(rv), _bk_record_x0_v10(rv)))
    else:
        ordered = cleaned_recs
    return "\n".join(_clean_ocr_text(rv.text) for rv in ordered if _clean_ocr_text(rv.text)).strip()

_bk_lm_collect_current_text = _bk_lm_collect_current_text_v18

_bk_lm_collect_current_text_v10 = _bk_lm_collect_current_text_v18

def _ptr_guess_person_name_from_line_v18(line: str) -> Optional[str]:
    guessed = _ptr_guess_person_name_from_line_v10(line)
    if not guessed:
        return None
    full, first, last = _bk_split_person_name_heuristic(guessed, None, None, None, line)
    if first and last:
        return f"{last}, {first}"[:140]
    return full or guessed

_ptr_guess_person_name_from_line = _ptr_guess_person_name_from_line_v18

def _ptr_ai_build_postgres_json_local_v18(source_text: str) -> Dict[str, Any]:
    raw_lines = _ptr_source_lines_for_postgres(source_text)
    if not raw_lines:
        return _ptr_normalize_postgres_json(_ptr_postgres_empty_payload(source_text), source_text)
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
        pid = f"place_{_ptr_make_slug(place.get('name') or 'place', 'place')}_{len(place_index) + 1}"
        place['id'] = pid
        place_index[(place.get('name') or '').strip().lower()] = pid

    windows = []
    total = len(raw_lines)
    for i in range(total):
        part = [raw_lines[j] for j in (i - 1, i, i + 1) if 0 <= j < total and _clean_ocr_text(raw_lines[j])]
        block_text = '\n'.join(_clean_ocr_text(x) for x in part if _clean_ocr_text(x)).strip()
        if block_text:
            windows.append((i + 1, block_text))

    for idx, block_text in windows:
        person_id = None
        person_name = _ptr_guess_person_name_from_line_v18(block_text)
        if person_name:
            key = person_name.lower()
            person_id = person_index.get(key)
            if not person_id:
                person_id = f"person_{_ptr_make_slug(person_name, str(idx))}_{len(person_index) + 1}"
                person_index[key] = person_id
                full_name, first_name, last_name = _bk_split_person_name_heuristic(person_name, None, None, None, block_text)
                persons.append({
                    'id': person_id,
                    'full_name': full_name or person_name,
                    'first_name': first_name,
                    'last_name': last_name,
                    'description': None,
                    'source_excerpt': block_text[:500],
                })
        for street in _ptr_extract_street_candidates_from_line(block_text):
            skey = (street.get('name') or '').strip().lower()
            if not skey:
                continue
            street_id = street_index.get(skey)
            if not street_id:
                street_id = f"street_{_ptr_make_slug(street.get('name') or 'street', str(idx))}_{len(street_index) + 1}"
                street_index[skey] = street_id
                street['id'] = street_id
                streets.append(street)
            else:
                street['id'] = street_id
            if person_id:
                references.append({
                    'id': f'reference_{len(references) + 1}',
                    'source_table': 'persons',
                    'source_id': person_id,
                    'relation_type': 'LIVES_AT',
                    'target_table': 'streets',
                    'target_id': street['id'],
                    'evidence': block_text[:500],
                })
        for org in _ptr_extract_org_candidates_from_line(block_text):
            okey = (org.get('name') or '').strip().lower()
            if not okey:
                continue
            org_id = org_index.get(okey)
            if not org_id:
                org_id = f"organization_{_ptr_make_slug(org.get('name') or 'organization', str(idx))}_{len(org_index) + 1}"
                org_index[okey] = org_id
                org['id'] = org_id
                organizations.append(org)
            else:
                org['id'] = org_id
            if person_id:
                references.append({
                    'id': f'reference_{len(references) + 1}',
                    'source_table': 'persons',
                    'source_id': person_id,
                    'relation_type': 'ASSOCIATED_WITH',
                    'target_table': 'organizations',
                    'target_id': org['id'],
                    'evidence': block_text[:500],
                })
        for place_name, place_id in place_index.items():
            if re.search(rf'\b{re.escape(place_name)}\b', block_text, flags=re.IGNORECASE):
                if person_id:
                    references.append({
                        'id': f'reference_{len(references) + 1}',
                        'source_table': 'persons',
                        'source_id': person_id,
                        'relation_type': 'LOCATED_IN',
                        'target_table': 'places',
                        'target_id': place_id,
                        'evidence': block_text[:500],
                    })
    payload['persons'] = persons
    payload['places'] = places
    payload['streets'] = streets
    payload['years'] = years
    payload['organizations'] = organizations
    payload['references'] = references
    return _ptr_normalize_postgres_json(payload, source_text)
