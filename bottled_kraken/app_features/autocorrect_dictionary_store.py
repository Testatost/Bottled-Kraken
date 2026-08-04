"""SQLite-basierter Wörterbuch-Store für die Offline-Autokorrektur.

Zweistufige Architektur (siehe REFACTORING-BERICHT, Runde 5):
- Kleine Wörterbücher (mitgeliefertes <lang>.json, Nutzerwörterbuch, Common-
  Words) bleiben wie bisher als RAM-Index - sie speisen auch die
  OCR-Worker-Referenzlisten.
- Die grossen erweiterten Wörterbücher (<lang>_erweitert.json, ~2 Mio.
  Begriffe) werden EINMALIG in eine indizierte SQLite-Datenbank überführt
  und zur Laufzeit nur noch per Index abgefragt: exakte Prüfung als
  Primärschlüssel-Lookup, Vorschlags-Kandidaten über (Länge, Präfix)-Indizes.

Dieses Modul ist bewusst frei von Qt- und bottled_kraken-Importen (nur
Standardbibliothek). Die Normalisierungsfunktion wird vom Aufrufer
injiziert, damit exakt dieselbe Norm wie im restlichen Programm gilt.

Kandidaten-Eingrenzung für Vorschläge (statt 2 Mio. linear):
    Q1  prefix2 = norm[:2]  oder vertauscht (Transposition am Wortanfang)
    Q2  c1 = norm[0]        (Fehler ab Position 2)
    Q3  c2 = norm[1]        (Substitution/Verlust des ersten Zeichens)
jeweils mit Längenfenster ±max_dist. Nicht abgedeckt bleibt der seltene
Fall gleichzeitiger Fehler in Position 1 UND 2 - bewusster Kompromiss
zugunsten der Antwortzeit.
"""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import threading
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

_SCHEMA_VERSION = "2"
_BUILD_BATCH = 50_000
_Q_FALLBACK_LIMIT = 2500
_Q_SECOND_LIMIT = 1000


def _stamp_of(paths: Iterable[str]) -> str:
    parts = []
    for p in sorted(paths):
        try:
            st = os.stat(p)
            parts.append(f"{os.path.basename(p)}:{st.st_size}:{int(st.st_mtime)}")
        except OSError:
            parts.append(f"{os.path.basename(p)}:missing")
    return "|".join(parts) + f"|v{_SCHEMA_VERSION}"


def _iter_json_terms(path: str) -> Iterable[str]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception:
        return
    if isinstance(data, dict):
        data = data.get("terms") or data.get("words") or []
    if not isinstance(data, list):
        return
    for item in data:
        if isinstance(item, dict):
            value = item.get("term") or item.get("word") or item.get("text") or item.get("name") or item.get("value")
        else:
            value = item
        value = str(value or "").strip()
        if value:
            yield value


class BKDictionaryStore:
    """Ein Store pro Sprache. Threadsicher für lesende Zugriffe
    (Verbindung pro Thread), Build atomar über eine Temp-Datei."""

    def __init__(self, lang: str, db_path: str, source_paths: List[str],
                 norm: Callable[[Any], str], weight: float = 100.0):
        self.lang = str(lang)
        self.db_path = str(db_path)
        self.source_paths = [str(p) for p in source_paths if p]
        self._norm = norm
        self._weight = float(weight)
        self._local = threading.local()
        self._build_lock = threading.Lock()
        self.build_error: Optional[str] = None
        self._lookup_cache: Dict[str, Optional[Tuple[str, float]]] = {}

    # ---------------- Verbindungen ----------------

    def _connect(self) -> Optional[sqlite3.Connection]:
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            return conn
        if not os.path.exists(self.db_path):
            return None
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.execute("PRAGMA query_only=ON")
            conn.execute("PRAGMA mmap_size=268435456")
            self._local.conn = conn
            return conn
        except Exception:
            return None

    def close(self) -> None:
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
            self._local.conn = None

    # ---------------- Bau ----------------

    def existing_sources(self) -> List[str]:
        return [p for p in self.source_paths if os.path.isfile(p)]

    def is_ready(self) -> bool:
        sources = self.existing_sources()
        if not sources:
            return False
        conn = self._connect()
        if conn is None:
            return False
        try:
            row = conn.execute("SELECT value FROM meta WHERE key='stamp'").fetchone()
        except Exception:
            return False
        return bool(row) and row[0] == _stamp_of(sources)

    def build(self, progress: Optional[Callable[[int, int], None]] = None) -> bool:
        """Einmaliger Aufbau in eine Temp-Datei mit atomarem Austausch.
        Gibt True zurück, wenn der Store danach benutzbar ist."""
        with self._build_lock:
            if self.is_ready():
                return True
            # is_ready() may have opened a read-only SQLite connection to an
            # outdated database. On Windows an open connection can block
            # os.replace(tmp, self.db_path), so close it before rebuilding.
            self.close()
            self._lookup_cache.clear()
            sources = self.existing_sources()
            if not sources:
                self.build_error = "keine Quelldateien"
                return False
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            fd, tmp = tempfile.mkstemp(prefix=f"bk_dict_{self.lang}_", suffix=".db",
                                       dir=os.path.dirname(self.db_path))
            os.close(fd)
            try:
                conn = sqlite3.connect(tmp)
                conn.execute("PRAGMA journal_mode=OFF")
                conn.execute("PRAGMA synchronous=OFF")
                conn.execute("PRAGMA temp_store=MEMORY")
                conn.execute(
                    "CREATE TABLE terms("
                    " norm TEXT PRIMARY KEY,"
                    " term TEXT NOT NULL,"
                    " weight REAL NOT NULL,"
                    " length INTEGER NOT NULL,"
                    " p2 TEXT NOT NULL,"
                    " c1 TEXT NOT NULL,"
                    " c2 TEXT NOT NULL"
                    ") WITHOUT ROWID")
                conn.execute("CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT)")
                norm_fn = self._norm
                batch: Dict[str, Tuple[str, float, int, str, str, str]] = {}
                total = 0

                def flush() -> None:
                    if not batch:
                        return
                    conn.executemany(
                        "INSERT INTO terms(norm, term, weight, length, p2, c1, c2)"
                        " VALUES(?,?,?,?,?,?,?)"
                        " ON CONFLICT(norm) DO UPDATE SET"
                        "  term=excluded.term, weight=excluded.weight"
                        "  WHERE excluded.weight >= terms.weight",
                        [(n, *v) for n, v in batch.items()])
                    batch.clear()

                for src in sources:
                    for term in _iter_json_terms(src):
                        n = norm_fn(term)
                        if not n or len(n) < 2:
                            continue
                        batch[n] = (term, self._weight, len(n), n[:2], n[0], n[1] if len(n) > 1 else "")
                        total += 1
                        if len(batch) >= _BUILD_BATCH:
                            flush()
                            if progress:
                                progress(total, -1)
                flush()
                # Gleichheitsspalte VOR der Bereichsspalte, sonst Range-Scan über die Länge
                conn.execute("CREATE INDEX idx_p2_len ON terms(p2, length)")
                conn.execute("CREATE INDEX idx_c1_len ON terms(c1, length)")
                conn.execute("CREATE INDEX idx_c2_len ON terms(c2, length)")
                conn.execute("INSERT INTO meta(key, value) VALUES('stamp', ?)",
                             (_stamp_of(sources),))
                conn.execute("INSERT INTO meta(key, value) VALUES('count', ?)",
                             (str(conn.execute('SELECT COUNT(*) FROM terms').fetchone()[0]),))
                conn.commit()
                conn.close()
                os.replace(tmp, self.db_path)
                self.close()
                self._lookup_cache.clear()
                self.build_error = None
                return True
            except Exception as exc:
                self.build_error = f"{type(exc).__name__}: {exc}"
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
                return False

    # ---------------- Abfragen ----------------

    def term_count(self) -> int:
        conn = self._connect()
        if conn is None:
            return 0
        try:
            row = conn.execute("SELECT value FROM meta WHERE key='count'").fetchone()
            return int(row[0]) if row else 0
        except Exception:
            return 0

    def lookup(self, norm: str) -> Optional[Tuple[str, float]]:
        """(Anzeigeform, Gewicht) für eine exakt normalisierte Form, sonst None."""
        norm = str(norm or "")
        if not norm:
            return None
        if norm in self._lookup_cache:
            return self._lookup_cache[norm]
        conn = self._connect()
        result: Optional[Tuple[str, float]] = None
        if conn is not None:
            try:
                row = conn.execute(
                    "SELECT term, weight FROM terms WHERE norm=?", (norm,)).fetchone()
                if row:
                    result = (str(row[0]), float(row[1]))
            except Exception:
                result = None
        if len(self._lookup_cache) > 60_000:
            self._lookup_cache.clear()
        self._lookup_cache[norm] = result
        return result

    def contains(self, norm: str) -> bool:
        return self.lookup(norm) is not None

    def candidates(self, norm: str, max_dist: int) -> List[Tuple[str, str, float]]:
        """Eingegrenzte Vorschlags-Kandidaten als (norm, term, weight)."""
        norm = str(norm or "")
        conn = self._connect()
        if conn is None or len(norm) < 2 or max_dist <= 0:
            return []
        lo, hi = max(2, len(norm) - max_dist), len(norm) + max_dist
        seen: Dict[str, Tuple[str, str, float]] = {}
        try:
            p2 = norm[:2]
            p2_swapped = norm[1] + norm[0]
            for row in conn.execute(
                    "SELECT norm, term, weight FROM terms"
                    " WHERE length BETWEEN ? AND ? AND p2 IN (?, ?)",
                    (lo, hi, p2, p2_swapped)):
                seen[row[0]] = (row[0], row[1], float(row[2]))
            for row in conn.execute(
                    "SELECT norm, term, weight FROM terms"
                    " WHERE length BETWEEN ? AND ? AND c1=? LIMIT ?",
                    (lo, hi, norm[0], _Q_FALLBACK_LIMIT)):
                seen.setdefault(row[0], (row[0], row[1], float(row[2])))
            for row in conn.execute(
                    "SELECT norm, term, weight FROM terms"
                    " WHERE length BETWEEN ? AND ? AND c2=? AND c1<>? LIMIT ?",
                    (lo, hi, norm[1], norm[0], _Q_SECOND_LIMIT)):
                seen.setdefault(row[0], (row[0], row[1], float(row[2])))
        except Exception:
            return list(seen.values())
        seen.pop(norm, None)
        return list(seen.values())


_STORES: Dict[Tuple[str, str], BKDictionaryStore] = {}
_STORES_LOCK = threading.Lock()


# Norm-Zeichenraum des Programms: [a-zäöüßà-ÿ] (à-ÿ = U+00E0..U+00FF ohne ÷)
BK_NORM_ALPHABET = "abcdefghijklmnopqrstuvwxyzß" + "".join(
    chr(c) for c in range(0x00E0, 0x0100) if c != 0x00F7)


def edits1(norm: str, alphabet: str = BK_NORM_ALPHABET) -> Iterable[str]:
    """Alle Normformen mit Editierdistanz 1 (Norvig-Schema).

    Statt zehntausende Kandidaten aus der Datenbank zu lesen und zu scoren,
    werden die ~n*|Alphabet| Distanz-1-Varianten GENERIERT und per
    Primärschlüssel nachgeschlagen (~1-2 µs pro Lookup)."""
    splits = [(norm[:i], norm[i:]) for i in range(len(norm) + 1)]
    for left, right in splits:
        if right:
            yield left + right[1:]                      # Löschung
        if len(right) > 1:
            yield left + right[1] + right[0] + right[2:]  # Transposition
        for ch in alphabet:
            if right:
                if ch != right[0]:
                    yield left + ch + right[1:]         # Ersetzung
            yield left + ch + right                     # Einfügung


def engine_suggestions(token: str, ram_buckets: dict, ram_exact: dict,
                       ram_weights: dict, store: Optional[BKDictionaryStore],
                       helpers: Dict[str, Any], limit: int = 5,
                       cache: Optional[Dict[str, List[str]]] = None) -> List[str]:
    """Vorschlagsliste über RAM-Index UND SQLite-Store.

    Semantik folgt _bk_ac_suggestion_list: fused-initial zuerst, dann die
    stärksten Kandidaten (Distanz 1 per Generierung, Distanz 2 nur als
    Fallback über die eingegrenzte Kandidaten-Query)."""
    norm_fn = helpers["norm"]
    norm = norm_fn(token)
    if not norm or len(norm) < 2:
        return []
    if norm in ram_exact or (store is not None and store.contains(norm)):
        return []
    if helpers["is_common_norm"](norm) or norm in helpers["skip_norms"]:
        return []
    if cache is not None and norm in cache:
        return list(cache[norm])[:limit]

    max_dist = int(helpers["max_distance"](norm))
    is_strong = helpers["is_strong"]
    restore_case = helpers["restore_case"]
    rank_fn = helpers["similarity_rank"]

    def weight_of(n: str) -> float:
        if n in ram_weights:
            return float(ram_weights.get(n, 1.0))
        if store is not None:
            hit = store.lookup(n)
            if hit is not None:
                return float(hit[1])
        return 1.0

    weights_view = _WeightsView(ram_weights, store)

    out: List[str] = []
    fused = helpers.get("fused_initial")
    if callable(fused):
        f = fused(token, _ExactView(ram_exact, store))
        if f:
            out.append(f)

    # Distanz 1: generieren + nachschlagen
    scored: List[Tuple[int, float, str, str]] = []
    seen_norms = set()
    if max_dist >= 1:
        for cand in edits1(norm):
            if cand == norm or cand in seen_norms or len(cand) < 2:
                continue
            seen_norms.add(cand)
            term = ram_exact.get(cand)
            if term is None and store is not None:
                hit = store.lookup(cand)
                term = hit[0] if hit else None
            if term is None:
                continue
            if not is_strong(norm, cand, 1, weights_view):
                continue
            scored.append((rank_fn(norm, cand), weight_of(cand), cand, term))
    scored.sort(key=lambda x: (-x[0], -x[1], x[2]))
    for _rank, _w, _cand, term in scored:
        restored = restore_case(token, term)
        if restored not in out:
            out.append(restored)
        if len(out) >= limit:
            break

    # Distanz 2 nur, wenn nötig und erlaubt
    if len(out) < limit and max_dist >= 2:
        distance = helpers["distance"]
        pool: List[Tuple[str, str, float]] = []
        for ln in range(max(1, len(norm) - 2), len(norm) + 3):
            for cand_norm, cand_term in (ram_buckets.get(ln) or []):
                pool.append((cand_norm, cand_term, float(ram_weights.get(cand_norm, 1.0))))
        if store is not None:
            pool.extend(store.candidates(norm, 2))
        scored2: List[Tuple[int, float, str, str]] = []
        for cand_norm, cand_term, w in pool:
            if cand_norm == norm or cand_norm in seen_norms:
                continue
            d = distance(norm, cand_norm, 2)
            if d > 2:
                continue
            if not is_strong(norm, cand_norm, d, weights_view):
                continue
            scored2.append((rank_fn(norm, cand_norm), w, cand_norm, cand_term))
        scored2.sort(key=lambda x: (-x[0], -x[1], x[2]))
        for _rank, _w, _cand, term in scored2:
            restored = restore_case(token, term)
            if restored not in out:
                out.append(restored)
            if len(out) >= limit:
                break

    if cache is not None:
        if len(cache) > 20_000:
            cache.clear()
        cache[norm] = list(out)
    return out[:limit]


def make_weights_view(ram_weights: dict, store: Optional[BKDictionaryStore]) -> "_WeightsView":
    """Öffentliche Fabrik: kombinierte Gewichts-Sicht (RAM + Store) für die
    bestehenden should_mark-/is_strong-Prüfungen."""
    return _WeightsView(ram_weights, store)


class _WeightsView:
    """dict-artige Sicht für die bestehenden Strength-/Mark-Prüfungen:
    RAM-Gewichte plus Store-Treffer (Store-Mitgliedschaft zählt als Gewicht)."""

    def __init__(self, ram_weights: dict, store: Optional[BKDictionaryStore]):
        self._ram = ram_weights or {}
        self._store = store

    def __contains__(self, norm: str) -> bool:
        if norm in self._ram:
            return True
        return self._store is not None and self._store.contains(norm)

    def get(self, norm: str, default: float = 0.0) -> float:
        if norm in self._ram:
            return float(self._ram.get(norm, default))
        if self._store is not None:
            hit = self._store.lookup(norm)
            if hit is not None:
                return float(hit[1])
        return default


class _ExactView:
    """dict-artige Sicht (nur Lesen) über RAM-exact + Store für fused-initial."""

    def __init__(self, ram_exact: dict, store: Optional[BKDictionaryStore]):
        self._ram = ram_exact or {}
        self._store = store

    def __contains__(self, norm: str) -> bool:
        if norm in self._ram:
            return True
        return self._store is not None and self._store.contains(norm)

    def get(self, norm: str, default=None):
        if norm in self._ram:
            return self._ram.get(norm, default)
        if self._store is not None:
            hit = self._store.lookup(norm)
            if hit is not None:
                return hit[0]
        return default


def get_dictionary_store(lang: str, db_dir: str, source_paths: List[str],
                         norm: Callable[[Any], str]) -> BKDictionaryStore:
    key = (str(lang), os.path.abspath(db_dir))
    with _STORES_LOCK:
        store = _STORES.get(key)
        if store is None:
            store = BKDictionaryStore(
                lang=lang,
                db_path=os.path.join(db_dir, f"{lang}.db"),
                source_paths=source_paths,
                norm=norm)
            _STORES[key] = store
        else:
            store.source_paths = [str(p) for p in source_paths if p]
        return store
