def _bk_name_tokens(value: Any) -> List[str]:
    txt = _bk_clean_name_fragment(value)
    if not txt:
        return []
    return [tok for tok in re.split(r'\s+', txt) if tok]

def _bk_is_name_like(value: Any) -> bool:
    txt = _bk_clean_name_fragment(value)
    if not txt:
        return False
    if any(ch.isdigit() for ch in txt):
        return False
    letters = re.findall(r'[A-Za-zÀ-ÿÄÖÜäöüß]', txt)
    return len(letters) >= 2

def _bk_looks_like_surname(value: Any) -> bool:
    tokens = _bk_name_tokens(value)
    if not tokens or len(tokens) > 4:
        return False
    for tok in tokens:
        base = tok.strip('.,').lower()
        if not base:
            continue
        if base in _BK_PERSON_ROLE_STOPWORDS:
            return False
    return _bk_is_name_like(' '.join(tokens))

def _bk_looks_like_given_block(value: Any) -> bool:
    tokens = _bk_name_tokens(value)
    if not tokens or len(tokens) > 6:
        return False
    if not _bk_is_name_like(' '.join(tokens)):
        return False
    bad = 0
    for tok in tokens:
        base = tok.strip('.,').lower()
        if base in _BK_PERSON_ROLE_STOPWORDS:
            bad += 1
    return bad == 0

def _bk_prune_given_names(value: Any) -> Optional[str]:
    tokens = _bk_name_tokens(value)
    out = []
    for tok in tokens:
        base = tok.strip('.,').lower()
        if not base:
            continue
        if re.search(r'\d', tok):
            break
        if base in _BK_PERSON_ROLE_STOPWORDS:
            break
        out.append(tok.strip(' ,;:'))
    txt = ' '.join(out).strip(' ,;:')
    return txt or None

def _bk_split_person_name_heuristic(full_name: Any, first_name: Any, last_name: Any, description: Any, source_excerpt: Any):
    full = _bk_clean_name_fragment(full_name)
    first = _bk_clean_name_fragment(first_name)
    last = _bk_clean_name_fragment(last_name)
    desc = _bk_clean_name_fragment(description)
    excerpt = _bk_clean_name_fragment(source_excerpt)

    if full and ',' in full:
        left, right = full.split(',', 1)
        left = _bk_clean_name_fragment(left)
        right = _bk_prune_given_names(right)
        if left and not last and _bk_looks_like_surname(left):
            last = left
        if right and not first and _bk_looks_like_given_block(right):
            first = right

    segs = [_bk_clean_name_fragment(seg) for seg in re.split(r'[;,|]', excerpt) if _bk_clean_name_fragment(seg)]
    if segs:
        if not first:
            if full and segs and _bk_clean_name_fragment(segs[0]) == full and _bk_looks_like_given_block(segs[0]):
                first = _bk_prune_given_names(segs[0])
            elif len(segs) >= 1 and _bk_looks_like_given_block(segs[0]):
                first = _bk_prune_given_names(segs[0])
        if not last:
            if len(segs) >= 2 and _bk_looks_like_surname(segs[-1]):
                last = _bk_clean_name_fragment(segs[-1])
            elif desc and _bk_looks_like_surname(desc) and first and _bk_looks_like_given_block(first):
                last = desc

    if not last and desc and _bk_looks_like_surname(desc) and (first or _bk_looks_like_given_block(full)):
        last = desc
    if not first and full and last:
        if full.endswith(last) and full != last:
            maybe_first = _bk_clean_name_fragment(full[:max(0, len(full) - len(last))])
            maybe_first = _bk_prune_given_names(maybe_first)
            if maybe_first:
                first = maybe_first
        elif full.startswith(last + ','):
            maybe_first = _bk_prune_given_names(full[len(last) + 1:])
            if maybe_first:
                first = maybe_first

    if not first and full and not last:
        if ',' in full:
            left, right = full.split(',', 1)
            left = _bk_clean_name_fragment(left)
            right = _bk_prune_given_names(right)
            if left and _bk_looks_like_surname(left):
                last = left
            if right:
                first = right
        else:
            tokens = _bk_name_tokens(full)
            if len(tokens) >= 2:
                maybe_last = tokens[-1]
                maybe_first = ' '.join(tokens[:-1])
                if _bk_looks_like_surname(maybe_last) and _bk_looks_like_given_block(maybe_first):
                    last = _bk_clean_name_fragment(maybe_last)
                    first = _bk_prune_given_names(maybe_first)

    if not full:
        if last and first:
            full = f"{last}, {first}"
        elif last:
            full = last
        elif first:
            full = first
    elif ',' not in full and first and last:
        if full == first or full == last or full == f"{first} {last}":
            full = f"{last}, {first}"

    if first and not _bk_is_name_like(first):
        first = None
    if last and not _bk_looks_like_surname(last):
        last = None
    if full and not _bk_is_name_like(full):
        full = None

    return full or None, first or None, last or None

_bk_prev_ptr_normalize_postgres_json_v9 = _ptr_normalize_postgres_json

def _ptr_normalize_postgres_json_v9(data: Any, source_text: str) -> Dict[str, Any]:
    payload = _bk_prev_ptr_normalize_postgres_json_v9(data, source_text)
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

_ptr_normalize_postgres_json = _ptr_normalize_postgres_json_v9

def _bk_extract_token_usage(data: Any) -> Dict[str, Optional[int]]:
    usage = data.get('usage') if isinstance(data, dict) else None
    if not isinstance(usage, dict):
        usage = {}

    def _first_int(*values):
        for value in values:
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)):
                return int(value)
            if isinstance(value, str):
                value = value.strip()
                if value.isdigit():
                    return int(value)
        return None

    prompt = _first_int(usage.get('prompt_tokens'), usage.get('input_tokens'))
    completion = _first_int(usage.get('completion_tokens'), usage.get('output_tokens'))
    total = _first_int(usage.get('total_tokens'))
    if total is None and (prompt is not None or completion is not None):
        total = int(prompt or 0) + int(completion or 0)
    return {
        'prompt_tokens': prompt,
        'completion_tokens': completion,
        'total_tokens': total,
    }

def _bk_emit_usage_progress(worker, data: Any):
    usage = _bk_extract_token_usage(data)
    worker._bk_last_usage = usage
    used_tokens = usage.get('completion_tokens')
    if used_tokens is None:
        used_tokens = usage.get('total_tokens')
    if used_tokens is None:
        return
    max_tokens = max(int(getattr(worker, 'max_tokens', 0) or 0), 1)
    percent = max(1, min(99, int(round((float(used_tokens) / float(max_tokens)) * 100.0))))
    try:
        worker.progress_changed.emit(int(percent * 10))
    except Exception:
        pass
    try:
        worker.status_changed.emit(worker._tr('status_local_json_generating_tokens', int(used_tokens), int(max_tokens), int(percent)))
    except Exception:
        pass

def _bk_extract_nested_json_candidate(obj: Any, required_keys: set, depth: int = 0):
    if depth > 4:
        return None
    if isinstance(obj, dict):
        if required_keys.issubset(set(obj.keys())):
            return obj
        for key in ('graph', 'result', 'data', 'payload', 'json', 'output', 'response', 'neo4j', 'postgres', 'postgresql'):
            if key in obj:
                nested = _bk_extract_nested_json_candidate(obj.get(key), required_keys, depth + 1)
                if nested is not None:
                    return nested
        for value in obj.values():
            if isinstance(value, (dict, list)):
                nested = _bk_extract_nested_json_candidate(value, required_keys, depth + 1)
                if nested is not None:
                    return nested
    elif isinstance(obj, list):
        if required_keys == {'nodes', 'relationships'}:
            nodes = []
            relationships = []
            for item in obj:
                if isinstance(item, dict):
                    if 'source' in item and 'target' in item:
                        relationships.append(item)
                    elif any(k in item for k in ('label', 'properties', 'id', 'type', 'name')):
                        nodes.append(item)
                    else:
                        nested = _bk_extract_nested_json_candidate(item, required_keys, depth + 1)
                        if isinstance(nested, dict):
                            nodes.extend(nested.get('nodes') or [])
                            relationships.extend(nested.get('relationships') or [])
            if nodes or relationships:
                return {'nodes': nodes, 'relationships': relationships}
    return None

def _bk_build_local_neo4j_json(source_text: str) -> Dict[str, Any]:
    pg = _ptr_ai_build_postgres_json_local(source_text)
    nodes = []
    relationships = []
    node_map = {}

    def add_node(node_id: str, label: Any, node_type: str, props: Dict[str, Any]):
        if not node_id:
            return
        if node_id in node_map:
            return
        node = {
            'id': str(node_id),
            'label': _clean_ocr_text(label) or None,
            'type': node_type,
            'properties': dict(props or {}),
        }
        node_map[node_id] = node
        nodes.append(node)

    doc = pg.get('document') if isinstance(pg, dict) else {}
    if isinstance(doc, dict):
        doc_id = str(doc.get('id') or 'document_1')
        add_node(doc_id, doc.get('title') or 'Document', 'Document', {
            'source_type': doc.get('source_type'),
            'language': doc.get('language'),
            'raw_excerpt': doc.get('raw_excerpt'),
        })
    else:
        doc_id = 'document_1'
        add_node(doc_id, 'Document', 'Document', {'raw_excerpt': (source_text or '')[:1000] or None})

    table_specs = {
        'persons': ('Person', lambda item: item.get('full_name') or 'Person', {'full_name', 'first_name', 'last_name', 'description', 'source_excerpt'}),
        'places': ('Place', lambda item: item.get('name') or 'Place', {'name', 'type', 'description'}),
        'streets': ('Street', lambda item: item.get('name') or 'Street', {'name', 'place', 'description'}),
        'years': ('Year', lambda item: item.get('year') or 'Year', {'year', 'context'}),
        'organizations': ('Organization', lambda item: item.get('name') or 'Organization', {'name', 'type', 'description'}),
    }
    for table, (node_type, label_fn, prop_keys) in table_specs.items():
        raw_items = pg.get(table)
        if not isinstance(raw_items, list):
            continue
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            node_id = str(item.get('id') or '').strip()
            if not node_id:
                continue
            props = {k: item.get(k) for k in prop_keys if k in item}
            add_node(node_id, label_fn(item), node_type, props)
            relationships.append({
                'source': doc_id,
                'target': node_id,
                'type': 'MENTIONS',
                'properties': {},
            })

    raw_refs = pg.get('references')
    if isinstance(raw_refs, list):
        for item in raw_refs:
            if not isinstance(item, dict):
                continue
            src = _clean_ocr_text(item.get('source_id'))
            tgt = _clean_ocr_text(item.get('target_id'))
            rel_type = _clean_ocr_text(item.get('relation_type')).upper().replace(' ', '_') if item.get('relation_type') else 'RELATED_TO'
            if not src or not tgt:
                continue
            relationships.append({
                'source': src,
                'target': tgt,
                'type': rel_type or 'RELATED_TO',
                'properties': {'evidence': item.get('evidence')},
            })

    return _bk_normalize_neo4j_json({'nodes': nodes, 'relationships': relationships}, source_text)

def _bk_local_json_request_payload(self, system_prompt: str, user_prompt: str):
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
            data = self._post_json(payload)
            _bk_emit_usage_progress(self, data)
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

def _bk_local_json_request_object(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    obj = _bk_local_json_request_payload(self, system_prompt, user_prompt)
    if isinstance(obj, dict):
        return obj
    raise RuntimeError(self._tr('ai_err_invalid_json', 'Top-level JSON object expected.'))

def _bk_local_json_build_postgres_v9(self) -> Dict[str, Any]:
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
        "- references should describe meaningful relations such as LIVES_AT, LOCATED_IN, MEMBER_OF, MENTIONS, or REFERENCED_IN.\n"
        "- If no relations are supported, return an empty references array.\n\n"
        "Text:\n" + self.source_text
    )
    try:
        data = _bk_local_json_request_payload(self, system_prompt, user_prompt)
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
