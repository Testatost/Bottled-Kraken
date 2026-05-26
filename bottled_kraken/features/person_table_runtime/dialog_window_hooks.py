def _ptr_sqlite_person_rows(data, fallback_text: str = "") -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if isinstance(data, dict):
        # Prefer an explicit sqlite_export section when an external model returned one.
        sqlite_export = data.get("sqlite_export") if isinstance(data.get("sqlite_export"), dict) else {}
        tables = sqlite_export.get("tables") if isinstance(sqlite_export.get("tables"), dict) else {}
        for key in ("persons", "entries", "registrations"):
            raw = tables.get(key)
            if isinstance(raw, list):
                for item in raw:
                    if isinstance(item, dict):
                        rows.append(dict(item))
        for key in ("persons", "registrations", "entries"):
            raw = data.get(key)
            if isinstance(raw, list):
                for item in raw:
                    if isinstance(item, dict):
                        rows.append(dict(item))
    if not rows:
        # Conservative fallback from OCR lines.
        for i, line in enumerate(str(fallback_text or "").splitlines(), start=1):
            line = _ptr_sqlite_clean(line)
            if not line or len(line) < 4:
                continue
            m_age = re.search(r"\b(\d{1,3}\s*(?:Jahre?|Jahr|J\.|Monate?|Mon\.?|Tage?|Wochen?|Years?|Months?|Days?))\b", line, flags=re.IGNORECASE)
            m_date = re.search(r"\b(\d{1,2}\.\s*(?:[IVXLCDM]{1,8}|\d{1,2})\.?\s*(?:1[5-9]\d{2}|20\d{2})?|1[5-9]\d{2}|20\d{2})\b", line, flags=re.IGNORECASE)
            cut = min([m.start() for m in (m_age, m_date) if m] or [min(len(line), 90)])
            full_name = re.sub(r"^\d+\s*", "", line[:cut]).strip(" ,.;:-")
            if not re.search(r"[A-Za-zÄÖÜäöüß]", full_name):
                continue
            first, last = _ptr_sqlite_split_name(full_name)
            rows.append({
                "id": f"person_{i}",
                "full_name": full_name,
                "first_name": first,
                "last_name": last,
                "age": m_age.group(1) if m_age else None,
                "event_date": m_date.group(1).strip(" .,") if m_date else None,
                "event_place": None,
                "occupation": None,
                "source_excerpt": line,
            })
    # Normalize/deduplicate.
    out = []
    seen = set()
    for i, row in enumerate(rows, start=1):
        person = row.get("person") if isinstance(row.get("person"), dict) else {}
        full_name = _ptr_sqlite_clean(row.get("full_name") or row.get("name") or row.get("label") or person.get("full_name"))
        first = _ptr_sqlite_clean(row.get("first_name") or person.get("first_name") or person.get("given_names"))
        last = _ptr_sqlite_clean(row.get("last_name") or person.get("last_name") or person.get("surname"))
        if not full_name and (first or last):
            full_name = (last + " " + first).strip()
        if not (first or last) and full_name:
            first, last = _ptr_sqlite_split_name(full_name)
        key = (full_name.lower(), _ptr_sqlite_clean(row.get("event_date") or row.get("year")).lower(), _ptr_sqlite_clean(row.get("age")).lower())
        if not key[0] or key in seen:
            continue
        seen.add(key)
        out.append({
            "id": _ptr_sqlite_clean(row.get("id") or f"person_{len(out)+1}"),
            "full_name": full_name,
            "first_name": first,
            "last_name": last,
            "age": _ptr_sqlite_clean(row.get("age") or person.get("age")),
            "event_date": _ptr_sqlite_clean(row.get("event_date") or row.get("date") or row.get("year")),
            "event_place": _ptr_sqlite_clean(row.get("event_place") or row.get("place") or row.get("residence")),
            "occupation": _ptr_sqlite_clean(row.get("occupation") or person.get("occupation")),
            "notes": _ptr_sqlite_clean(row.get("notes") or row.get("description")),
            "source_line": _ptr_sqlite_clean(row.get("source_excerpt") or row.get("source_line") or row.get("evidence")),
        })
    return out

def _ptr_write_transcription_helper_sqlite(path: str, data, source_text: str = "") -> int:
    import sqlite3
    rows = _ptr_sqlite_person_rows(data, source_text)
    conn = sqlite3.connect(path)
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA user_version = 1")
        cur.execute("CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, source_type TEXT, raw_text TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS persons (id INTEGER PRIMARY KEY AUTOINCREMENT, external_id TEXT, full_name TEXT, first_name TEXT, last_name TEXT, age TEXT, event_date TEXT, event_place TEXT, occupation TEXT, notes TEXT, source_line TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS entries (id INTEGER PRIMARY KEY AUTOINCREMENT, person_id INTEGER, field_name TEXT, field_value TEXT, confidence REAL, source_line TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT)")
        title = None
        if isinstance(data, dict) and isinstance(data.get("document"), dict):
            title = data["document"].get("title") or data["document"].get("id")
        cur.execute("INSERT INTO documents(title, source_type, raw_text) VALUES (?, ?, ?)", (title or "Bottled Kraken OCR", "ocr_text", source_text or ""))
        doc_id = cur.lastrowid
        for row in rows:
            cur.execute(
                "INSERT INTO persons(external_id, full_name, first_name, last_name, age, event_date, event_place, occupation, notes, source_line) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (row["id"], row["full_name"], row["first_name"], row["last_name"], row["age"], row["event_date"], row["event_place"], row["occupation"], row["notes"], row["source_line"]),
            )
            pid = cur.lastrowid
            for field in ("full_name", "first_name", "last_name", "age", "event_date", "event_place", "occupation", "notes"):
                value = row.get(field)
                if value:
                    cur.execute("INSERT INTO entries(person_id, field_name, field_value, confidence, source_line) VALUES (?, ?, ?, ?, ?)", (pid, field, value, 1.0, row.get("source_line") or ""))
        cur.execute("INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)", ("creator", "Bottled Kraken"))
        cur.execute("INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)", ("schema", "transcription_helper_flat_v1"))
        cur.execute("INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)", ("document_id", str(doc_id)))
        conn.commit()
        return len(rows)
    finally:
        conn.close()

def _ptr_ai_dialog_save_sqlite_v2(self):
    data = getattr(self, "_existing_result_data", None)
    text = self.merged_edit.toPlainText().strip() or self.input_edit.toPlainText().strip()
    if data is None:
        raw = self.result_output_edit.toPlainText().strip()
        if raw:
            try:
                data = json.loads(raw)
            except Exception:
                data = None
    if data is None and not text:
        QMessageBox.information(self, _ptr_ui_tr(self, "ptr_ai_tools_title"), _ptr_ui_tr(self, "ptr_ai_no_result"))
        return
    path, _ = QFileDialog.getSaveFileName(self, _ptr_ui_tr(self, "ptr_ai_btn_save_sqlite"), "bottled_kraken_persons.sqlite", _ptr_ui_tr(self, "filter_sqlite_files"))
    if not path:
        return
    if not (path.lower().endswith(".sqlite") or path.lower().endswith(".db")):
        path += ".sqlite"
    try:
        count = _ptr_write_transcription_helper_sqlite(path, data or {}, text)
        QMessageBox.information(self, _ptr_ui_tr(self, "ptr_ai_tools_title"), _ptr_ui_tr(self, "ptr_ai_sqlite_done", count))
    except Exception as exc:
        QMessageBox.warning(self, _ptr_ui_tr(self, "ptr_ai_tools_title"), str(exc))

PtrAIToolsDialog._save_sqlite = _ptr_ai_dialog_save_sqlite_v2
