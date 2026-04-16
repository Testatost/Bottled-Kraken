def _bk_blocks_to_text_v10(blocks: List[List[str]]) -> str:
    return '\n\n'.join('\n'.join(block[:3]) for block in blocks if block)

def _bk_build_three_line_context_text_v10(source_text: str) -> str:
    lines = _ptr_source_lines_for_postgres(source_text)
    if not lines:
        return ''
    chunks = []
    for i in range(0, len(lines), 3):
        part = lines[i:i + 3]
        chunks.append(f'[{i + 1:04d}-{i + len(part):04d}]\n' + '\n'.join(part))
    return '\n\n'.join(chunks)

def _bk_lm_collect_current_text_v10(self, task) -> str:
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
    blocks = _bk_source_blocks_for_local_json_v10(recs, page_w=page_w, page_h=page_h)
    if not blocks:
        lines = [_clean_ocr_text(rv.text) for rv in recs if _clean_ocr_text(rv.text)]
        blocks = [lines[i:i + 3] for i in range(0, len(lines), 3)]
    return _bk_blocks_to_text_v10(blocks).strip()

def _ptr_guess_person_name_from_line_v10(line: str) -> Optional[str]:
    txt = _clean_ocr_text(line)
    if not txt:
        return None
    txt = re.sub(r'^[\-–—\s]+', '', txt)
    txt = _BK_NAME_TITLES_PATTERN.sub('', txt).strip(' ,;:|')
    txt = re.sub(r'\s+', ' ', txt)
    if not txt or any(ch.isdigit() for ch in txt[:40]):
        return None
    segments = [_bk_clean_name_fragment(seg) for seg in re.split(r'[;|]', txt) if _bk_clean_name_fragment(seg)]
    primary = segments[0] if segments else txt
    comma_parts = [_bk_clean_name_fragment(seg) for seg in primary.split(',') if _bk_clean_name_fragment(seg)]
    if len(comma_parts) >= 2 and _bk_looks_like_surname(comma_parts[0]):
        given = _bk_prune_given_names(comma_parts[1])
        if given:
            return f"{comma_parts[0]}, {given}"[:140]
        return comma_parts[0][:140]
    primary = re.split(r'[:()]', primary, maxsplit=1)[0].strip()
    tokens = _bk_name_tokens(primary)
    if not tokens:
        return None
    if len(tokens) >= 2:
        maybe_last = tokens[-1]
        maybe_first = ' '.join(tokens[:-1])
        if _bk_looks_like_surname(maybe_last) and _bk_looks_like_given_block(maybe_first):
            return f"{maybe_last}, {_bk_prune_given_names(maybe_first) or maybe_first}"[:140]
    if _bk_is_name_like(primary):
        return primary[:140]
    return None

_ptr_guess_person_name_from_line = _ptr_guess_person_name_from_line_v10

def _ptr_ai_build_postgres_json_local_v10(source_text: str) -> Dict[str, Any]:
    raw_lines = _ptr_source_lines_for_postgres(source_text)
    if not raw_lines:
        return _ptr_normalize_postgres_json(_ptr_postgres_empty_payload(source_text), source_text)
    blocks = [raw_lines[i:i + 3] for i in range(0, len(raw_lines), 3)]
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
    for idx, block in enumerate(blocks, start=1):
        block_text = '\n'.join(_clean_ocr_text(line) for line in block if _clean_ocr_text(line)).strip()
        if not block_text:
            continue
        person_id = None
        person_name = _ptr_guess_person_name_from_line_v10(block_text)
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

_ptr_ai_build_postgres_json_local = _ptr_ai_build_postgres_json_local_v10

def _bk_local_json_request_payload_v10(self, system_prompt: str, user_prompt: str):
    last_error = None
    for use_response_format in (True, False):
        payload = {
            'model': self.lm_model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            **self._build_sampling_payload(use_response_format=use_response_format),
        }
        try:
            _bk_emit_estimated_request_progress_v10(self, system_prompt, user_prompt)
            data = self._post_json(payload)
            _bk_emit_usage_progress_v10(self, data)
            content = self._extract_message_content(data)
            obj = _extract_json_payload(content)
            if obj is not None:
                return obj
            last_error = RuntimeError(self._tr('ai_err_invalid_json', content[:500] if isinstance(content, str) else 'empty'))
        except Exception as exc:
            last_error = exc
            if self._cancelled or self.isInterruptionRequested():
                break
    if last_error is None:
        raise RuntimeError(self._tr('msg_local_json_failed'))
    raise last_error

def _bk_local_json_build_postgres_v10(self) -> Dict[str, Any]:
    three_line_context = _bk_build_three_line_context_text_v10(self.source_text)
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
        "- Always resolve people, organizations, addresses and references with three-line context blocks.\n"
        "- A name, occupation or address may span the previous line, the current line and the next line.\n"
        "- Indented continuation lines usually belong to the previous line unless there is a clearly separate wide column.\n"
        "- Split person names carefully. If a surname appears before a comma, put it into last_name and put the following given names or abbreviations into first_name.\n"
        "- If a line looks like 'Frdr. Aug., profession, Kramer', infer first_name='Frdr. Aug.' and last_name='Kramer' when the text supports it.\n"
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
        "- Deduplicate entities that appear across multiple three-line blocks.\n"
        "- references should describe meaningful relations such as LIVES_AT, LOCATED_IN, MEMBER_OF, MENTIONS, or REFERENCED_IN.\n"
        "- If no relations are supported, return an empty references array.\n\n"
        "Three-line context blocks:\n" + (three_line_context or self.source_text) + "\n\n"
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

def _bk_local_json_build_neo4j_v10(self) -> Dict[str, Any]:
    three_line_context = _bk_build_three_line_context_text_v10(self.source_text)
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
        "- Always resolve entities and relations with three-line context blocks.\n"
        "- A person, address or organization may span the previous line, current line and next line.\n"
        "- Indented continuation lines usually belong to the previous line unless there is a clearly separate wide column.\n"
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
        "Deduplicate repeated entities across the three-line context blocks.\n\n"
        "Three-line context blocks:\n" + (three_line_context or self.source_text) + "\n\n"
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

def _bk_local_json_worker_run_v10(self):
    try:
        if self._cancelled or self.isInterruptionRequested():
            raise RuntimeError(self._tr('msg_local_json_cancelled'))
        self.progress_changed.emit(0)
        self.status_changed.emit(self._tr('dlg_local_json_connecting'))
        if self.schema_kind == 'neo4j':
            data = self._build_neo4j_json()
        else:
            data = self._build_postgres_json()
        if self._cancelled or self.isInterruptionRequested():
            raise RuntimeError(self._tr('msg_local_json_cancelled'))
        usage = getattr(self, '_bk_last_usage', None) or {}
        used_tokens = usage.get('total_tokens') or usage.get('completion_tokens') or usage.get('prompt_tokens') or getattr(self, '_bk_prompt_token_estimate', None)
        if used_tokens is not None:
            _bk_emit_token_progress_v10(self, used_tokens, estimated=False)
        self.progress_changed.emit(1000)
        self.finished_json.emit(self.path, self.schema_kind, data)
    except Exception as exc:
        self.failed_json.emit(self.path, self.schema_kind, str(exc))

BKLocalStructuredJsonWorker._bk_last_usage = None

BKLocalStructuredJsonWorker._bk_prompt_token_estimate = None

BKLocalStructuredJsonWorker._request_json_payload = _bk_local_json_request_payload_v10

BKLocalStructuredJsonWorker._build_postgres_json = _bk_local_json_build_postgres_v10

BKLocalStructuredJsonWorker._build_neo4j_json = _bk_local_json_build_neo4j_v10

BKLocalStructuredJsonWorker.run = _bk_local_json_worker_run_v10

_bk_lm_collect_current_text = _bk_lm_collect_current_text_v10

MainWindow._bk_lm_collect_current_text = _bk_lm_collect_current_text_v10
