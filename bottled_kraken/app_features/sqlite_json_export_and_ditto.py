from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
from bottled_kraken.common import (
    Any,
    Dict,
    List,
    QAction,
    QFileDialog,
    QMessageBox,
    os,
    re,
)
from bottled_kraken.main_window import MainWindow
def _bk_fix37_prev_word_at_column(prev_line: str, pos: int) -> str:
    prev_line = str(prev_line or "")
    words = []
    for m in re.finditer(r"[A-Za-zÀ-ÿÄÖÜäöüß0-9][A-Za-zÀ-ÿÄÖÜäöüß0-9./,'()\-]*", prev_line):
        token = m.group(0).strip(" ,;:")
        if not token:
            continue
        words.append((m.start(), m.end(), token))
    if not words:
        return ""
    covering = [w for w in words if w[0] - 2 <= pos <= w[1] + 2]
    if covering:
        return covering[-1][2]
    nearest = min(words, key=lambda w: min(abs(pos - w[0]), abs(pos - w[1])))
    if min(abs(pos - nearest[0]), abs(pos - nearest[1])) <= 14:
        return nearest[2]
    return ""
def _bk_fix37_resolve_ditto_marks_in_lines(lines: List[str]) -> List[str]:
    out: List[str] = []
    prev_line = ""
    ditto_re = re.compile(r'(?<![A-Za-zÀ-ÿÄÖÜäöüß0-9])(?:-["„“”]-|["„“”])(?=\s|[.,;:)\]]|$)')
    attached_re = re.compile(r'(?<![A-Za-zÀ-ÿÄÖÜäöüß0-9])["„“”](?=[A-Za-zÀ-ÿÄÖÜäöüß])')
    for raw in lines or []:
        line = str(raw or "")
        if not line.strip():
            out.append(line)
            continue
        def repl(match):
            copied = _bk_fix37_prev_word_at_column(prev_line, match.start())
            return copied if copied else ""
        line2 = ditto_re.sub(repl, line)
        line2 = attached_re.sub("", line2)
        line2 = re.sub(r'\s*[-–—]\s*["„“”]\s*[-–—]\s*', lambda m: " " + (_bk_fix37_prev_word_at_column(prev_line, m.start()) or "") + " ", line2)
        line2 = re.sub(r"\s{2,}", " ", line2).strip()
        out.append(line2)
        if line2:
            prev_line = line2
    return out
_bk_fix36_resolve_ditto_marks_in_lines = _bk_fix37_resolve_ditto_marks_in_lines
def _bk_fix37_expand_ditto_text(text: str) -> str:
    return "\n".join(_bk_fix37_resolve_ditto_marks_in_lines(str(text or "").splitlines()))
try:
    _BK_FIX37_PREV_COLLECT_CURRENT_TEXT = _bk_lm_collect_current_text
except Exception:
    _BK_FIX37_PREV_COLLECT_CURRENT_TEXT = None
def _bk_lm_collect_current_text(self, task):
    if callable(_BK_FIX37_PREV_COLLECT_CURRENT_TEXT):
        txt = _BK_FIX37_PREV_COLLECT_CURRENT_TEXT(self, task)
    else:
        txt = ""
        try:
            if task is not None and getattr(task, "results", None):
                _t, _kr, _im, recs = task.results
                txt = "\n".join(str(getattr(r, "text", "") or "") for r in recs)
        except Exception:
            pass
    return _bk_fix37_expand_ditto_text(txt)
def _bk_fix37_wrap_source_text_worker(cls_name: str):
    cls = globals().get(cls_name)
    if cls is None:
        return
    old_init = getattr(cls, "__init__", None)
    if not callable(old_init) or getattr(old_init, "_bk_fix37_ditto_wrapped", False):
        return
    def __init__(self, *args, **kwargs):
        if "source_text" in kwargs:
            kwargs["source_text"] = _bk_fix37_expand_ditto_text(kwargs.get("source_text", ""))
        old_init(self, *args, **kwargs)
        try:
            self.source_text = _bk_fix37_expand_ditto_text(getattr(self, "source_text", ""))
        except Exception:
            pass
    __init__._bk_fix37_ditto_wrapped = True
    cls.__init__ = __init__
for _cls_name in ("BKLocalStructuredJsonWorker", "BKLocalGedcomWorker"):
    _bk_fix37_wrap_source_text_worker(_cls_name)
def _bk_fix37_sqlite_rows_from_current_text(text: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for i, line in enumerate(_bk_fix37_expand_ditto_text(text).splitlines(), start=1):
        line = _bk_fix36_clean_text(line)
        if not line or len(line) < 4:
            continue
        if re.fullmatch(r"(seite|page)\s*[-–]?\s*\d+", line, flags=re.IGNORECASE):
            continue
        m_age = re.search(r"\b(\d{1,3}\s*(?:Jahre?|Jahr|J\.|Monate?|Mon\.?|Tage?|Wochen?|Years?|Months?|Days?))\b", line, flags=re.IGNORECASE)
        m_date = re.search(r"\b(\d{1,2}\.\s*(?:[IVXLCDM]{1,8}|\d{1,2})\.?\s*(?:1[5-9]\d{2}|20\d{2})?|1[5-9]\d{2}|20\d{2})\b", line, flags=re.IGNORECASE)
        cut_positions = [m.start() for m in (m_age, m_date) if m]
        cut = min(cut_positions) if cut_positions else min(len(line), 80)
        name = re.sub(r"^\d+\s*", "", line[:cut]).strip(" ,.;:-")
        if not re.search(r"[A-Za-zÄÖÜäöüß]", name):
            continue
        parts = re.sub(r"\([^)]*\)", " ", name).split()
        if len(parts) >= 2:
            last_name = parts[0]
            first_name = " ".join(parts[1:])
        else:
            last_name = ""
            first_name = parts[0] if parts else ""
        rows.append({
            "id": f"entry_{len(rows)+1}",
            "full_name": name,
            "first_name": first_name,
            "last_name": last_name,
            "age": m_age.group(1) if m_age else "",
            "event_date": m_date.group(1).strip(" .,") if m_date else "",
            "event_place": "",
            "source_excerpt": line,
        })
    return rows
def _bk_fix37_export_sqlite(self):
    try:
        import sqlite3
    except Exception as exc:
        QMessageBox.warning(self, _bk_fix36_tr(self, "warn_title"), str(exc))
        return
    task = _bk_fix36_current_task(self)
    if not task or not getattr(task, "results", None):
        QMessageBox.information(self, _bk_fix36_tr(self, "info_title"), _bk_fix36_tr(self, "warn_no_ocr_results"))
        return
    try:
        _txt, _kr, _im, recs = task.results
        source_text = "\n".join(str(getattr(r, "text", "") or "") for r in recs)
    except Exception:
        source_text = ""
    rows = _bk_fix37_sqlite_rows_from_current_text(source_text)
    if not rows:
        QMessageBox.information(self, _bk_fix36_tr(self, "info_title"), _bk_fix36_tr(self, "warn_no_exportable_person_entries"))
        return
    default_name = os.path.splitext(os.path.basename(getattr(task, "path", "bottled_kraken")))[0] + "_persons.sqlite"
    start_dir = getattr(self, "current_export_dir", "") or os.path.dirname(getattr(task, "path", "") or "") or os.getcwd()
    path, _ = QFileDialog.getSaveFileName(self, _bk_fix36_tr(self, "lm_menu_generate_sqlite"), os.path.join(start_dir, default_name), _bk_fix36_tr(self, "filter_sqlite_all_files"))
    if not path:
        return
    if not path.lower().endswith((".sqlite", ".db")):
        path += ".sqlite"
    conn = sqlite3.connect(path)
    try:
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY, source_path TEXT, title TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS persons (id TEXT PRIMARY KEY, full_name TEXT, first_name TEXT, last_name TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS entries (id TEXT PRIMARY KEY, person_id TEXT, age TEXT, event_date TEXT, event_place TEXT, source_excerpt TEXT)")
        cur.execute("DELETE FROM documents")
        cur.execute("DELETE FROM entries")
        cur.execute("DELETE FROM persons")
        cur.execute("INSERT INTO documents (id, source_path, title) VALUES (1, ?, ?)", (getattr(task, "path", ""), os.path.basename(getattr(task, "path", "") or "")))
        for row in rows:
            pid = str(row["id"])
            cur.execute("INSERT OR REPLACE INTO persons (id, full_name, first_name, last_name) VALUES (?, ?, ?, ?)", (pid, row.get("full_name", ""), row.get("first_name", ""), row.get("last_name", "")))
            cur.execute("INSERT OR REPLACE INTO entries (id, person_id, age, event_date, event_place, source_excerpt) VALUES (?, ?, ?, ?, ?, ?)", (pid, pid, row.get("age", ""), row.get("event_date", ""), row.get("event_place", ""), row.get("source_excerpt", "")))
        conn.commit()
    finally:
        conn.close()
    try:
        self.current_export_dir = os.path.dirname(path)
        self.status_bar.showMessage(_bk_fix36_tr(self, "msg_sqlite_export_done").format(os.path.basename(path)), 5000)
    except Exception:
        pass
def _bk_fix37_ensure_sqlite_menu_action(self):
    if not hasattr(self, "btn_ai_revise_menu") or self.btn_ai_revise_menu is None:
        return
    if not hasattr(self, "act_ai_menu_sqlite_export"):
        self.act_ai_menu_sqlite_export = QAction(_bk_fix36_tr(self, "lm_menu_generate_sqlite"), self)
        self.act_ai_menu_sqlite_export.triggered.connect(lambda: _bk_fix37_export_sqlite(self))
    self.act_ai_menu_sqlite_export.setText(_bk_fix36_tr(self, "lm_menu_generate_sqlite"))
    actions = list(self.btn_ai_revise_menu.actions())
    if self.act_ai_menu_sqlite_export in actions:
        return
    insert_before = None
    for idx, action in enumerate(actions):
        if "PostgreSQL" in str(action.text()):
            if idx + 1 < len(actions):
                insert_before = actions[idx + 1]
            break
    if insert_before is not None:
        self.btn_ai_revise_menu.insertAction(insert_before, self.act_ai_menu_sqlite_export)
    else:
        self.btn_ai_revise_menu.addAction(self.act_ai_menu_sqlite_export)
def _bk_fix37_mainwindow_init(self, *args, **kwargs):
    try:
        _bk_fix37_ensure_sqlite_menu_action(self)
    except Exception:
        pass
def _bk_fix37_retranslate_ui(self, *args, **kwargs):
    try:
        _bk_fix37_ensure_sqlite_menu_action(self)
    except Exception:
        pass
from bottled_kraken.common.chain_consolidation import register_init_delta, register_retranslate_delta
register_init_delta(_bk_fix37_mainwindow_init)
register_retranslate_delta(_bk_fix37_retranslate_ui)
MainWindow.bk_export_sqlite_persons = _bk_fix37_export_sqlite
__all__ = [
    '_bk_fix36_resolve_ditto_marks_in_lines',
    '_bk_fix37_ensure_sqlite_menu_action',
    '_bk_fix37_expand_ditto_text',
    '_bk_fix37_export_sqlite',
    '_bk_fix37_mainwindow_init',
    '_bk_fix37_prev_word_at_column',
    '_bk_fix37_resolve_ditto_marks_in_lines',
    '_bk_fix37_retranslate_ui',
    '_bk_fix37_sqlite_rows_from_current_text',
    '_bk_fix37_wrap_source_text_worker',
    '_bk_lm_collect_current_text',
    '_cls_name',
]
register_globals('bk', globals(), __all__)
