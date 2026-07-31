from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Tuple

from PySide6.QtCore import Qt, QRect, QUrl
from PySide6.QtGui import QAction, QColor, QDesktopServices, QFontMetrics, QPen, QPainter
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QStyle,
    QStyleOptionViewItem,
    QStyledItemDelegate,
    QTabWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QCheckBox,
)

from bottled_kraken.user_storage import bottled_kraken_user_path
from bottled_kraken.translation import translation

from bottled_kraken.common import (
    _bk_autocorrect_best_term,
    _bk_autocorrect_norm,
    _bk_autocorrect_payload_entry,
    _bk_autocorrect_restore_case,
    _apply_ocr_auto_revision_replacements,
    STATUS_DONE,
    QUEUE_COL_FILE,
)

try:
    from bottled_kraken.main_window import MainWindow
except Exception:  # pragma: no cover
    MainWindow = None

try:
    from bottled_kraken.app_features.autocorrect_dictionary_store import (
        get_dictionary_store as _bk_ac_get_store,
        engine_suggestions as _bk_ac_engine_suggestions_impl,
        make_weights_view as _bk_ac_make_weights_view,
    )
except Exception:  # pragma: no cover - z. B. Alt-Test-Loader
    _bk_ac_get_store = None
    _bk_ac_engine_suggestions_impl = None
    _bk_ac_make_weights_view = None

BK_AUTOCORRECT_ERRORS_ROLE = Qt.UserRole + 831
BK_AUTOCORRECT_TEXT_ROLE = Qt.UserRole + 832
def _bk_ac_available_langs() -> List[str]:
    try:
        langs = list(translation.available_languages())
        if langs:
            return langs
    except Exception:
        pass
    langs: List[str] = []
    try:
        pkg_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "translations"))
        for name in sorted(os.listdir(pkg_dir)):
            if name.startswith("_"):
                continue
            if os.path.isdir(os.path.join(pkg_dir, name)):
                langs.append(name)
    except Exception:
        pass
    return langs or ([translation.DEFAULT_LANGUAGE] if translation.DEFAULT_LANGUAGE else [])


def _bk_ac_display_language_name(code: str, ui_lang: str = "") -> str:
    code = str(code or "").strip()
    try:
        return str(translation.language_display_name(code, ui_lang or code))
    except Exception:
        pass
    return code
BK_AUTOCORRECT_WORD_CHARS = r"A-Za-zÄÖÜäöüßÀ-ÿ"
BK_AUTOCORRECT_WORD_RE = re.compile(
    rf"(?<![{BK_AUTOCORRECT_WORD_CHARS}])[{BK_AUTOCORRECT_WORD_CHARS}][{BK_AUTOCORRECT_WORD_CHARS}'’\-]{{2,}}(?![{BK_AUTOCORRECT_WORD_CHARS}])"
)
BK_AUTOCORRECT_SKIP_NORMS = {
    "und", "oder", "der", "die", "das", "den", "dem", "des", "ein", "eine", "einer", "eines", "im", "in", "am", "an", "auf", "von", "vom", "zu", "zur", "zum", "mit", "ohne", "bei", "für", "ist", "war",
    "and", "or", "the", "a", "an", "of", "to", "in", "on", "for", "from", "with", "without", "is", "was",
    "et", "ou", "le", "la", "les", "un", "une", "des", "du", "de", "à", "au", "aux", "en", "sur", "pour", "avec", "sans", "est",
}

BK_AUTOCORRECT_COMMON_WORDS = {
    "de": {
        "kind", "kinder", "tage", "tag", "jahr", "jahre", "monat", "monate", "woche", "wochen", "alt", "alter",
        "geboren", "geb", "geborene", "getauft", "taufe", "gestorben", "starb", "beerdigt", "begraben",
        "vater", "mutter", "eltern", "sohn", "tochter", "ehefrau", "ehemann", "frau", "mann", "witwe", "witwer",
        "ledig", "verheiratet", "ehelich", "unehelich", "wohnhaft", "wohnort", "ort", "dorf", "stadt", "haus", "nr",
        "tage", "tagen", "jahr", "jahren", "monat", "monaten", "stunden", "uhr", "nachmittag", "vormittag",
        "den", "dem", "der", "die", "das", "des", "ein", "eine", "einer", "eines", "sein", "seine", "ihre", "ihr",
        "und", "oder", "von", "vom", "aus", "zu", "zur", "zum", "in", "im", "am", "an", "auf", "bei", "mit", "ohne",
        "herr", "frau", "fräulein", "frl", "familie", "zeugen", "zeuge", "zeugin", "pfarrer", "pastor", "kirche", "gemeinde",
        "januar", "februar", "märz", "maerz", "april", "mai", "juni", "juli", "august", "september", "oktober", "november", "dezember",
    },
    "en": {
        "child", "children", "day", "days", "year", "years", "month", "months", "born", "baptized", "married",
        "died", "buried", "father", "mother", "son", "daughter", "wife", "husband", "widow", "widower",
        "and", "or", "of", "from", "in", "at", "on", "with", "without", "the", "a", "an",
    },
    "fr": {
        "enfant", "enfants", "jour", "jours", "an", "ans", "mois", "né", "née", "baptisé", "baptisée",
        "marié", "mariée", "décédé", "décédée", "père", "mère", "fils", "fille", "épouse", "époux",
        "et", "ou", "de", "du", "des", "à", "au", "aux", "en", "avec", "sans", "le", "la", "les",
    },
}


BK_AUTOCORRECT_COMMON_WORDS.setdefault("de", set()).update({
    "unter", "über", "ueber", "ober", "neben", "zwischen", "vor", "hinter", "nach", "aus", "bis", "durch", "gegen", "um", "wegen", "wider",
    "als", "also", "auch", "noch", "nur", "nicht", "kein", "keine", "keinen", "keinem", "keiner", "keines", "mehr", "sehr", "schon", "wieder", "heute", "gestern", "morgen",
    "hier", "dort", "da", "daher", "darum", "dann", "wenn", "weil", "wie", "wer", "was", "wo", "wann", "welche", "welcher", "welches", "welchen", "welchem",
    "dieser", "diese", "dieses", "diesen", "diesem", "jener", "jene", "jenes", "jeden", "jede", "jedes", "alle", "alles", "allen", "aller", "beide", "beiden",
    "ist", "sind", "war", "waren", "wurde", "wurden", "hat", "hatte", "hatten", "haben", "sein", "gewesen", "wird", "werden", "worden", "kann", "konnte", "soll", "sollte",
    "muss", "musste", "darf", "durfte", "mag", "mochte", "will", "wollte", "geht", "ging", "kam", "kommt", "bleibt", "blieb", "steht", "stand", "liegt", "lag",
    "klein", "groß", "gross", "jung", "alt", "älter", "aelter", "erwachsen", "tot", "lebend", "verstorben", "krank", "gesund", "arm", "reich", "eigen", "fremd",
    "er", "sie", "es", "wir", "ihr", "mich", "dich", "sich", "uns", "euch", "ihn", "ihm", "ihnen", "mein", "meine", "meiner", "meines", "dein", "deine", "ihrer",
    "buch", "seite", "seiten", "zeile", "zeilen", "eintrag", "einträge", "eintraege", "register", "liste", "spalte", "reihe", "nummer", "nr", "no", "akten", "akte",
    "geburt", "geburtsort", "geburtsdatum", "taufort", "tauftag", "sterbeort", "sterbetag", "tod", "hochzeit", "heirat", "trauung", "ehe", "bräutigam", "braeutigam", "braut",
    "pate", "patin", "paten", "taufpate", "taufpatin", "zeugen", "zeuge", "zeugin", "nachbar", "nachbarn", "bürger", "buerger", "bauer", "knecht", "magd", "arbeiter",
    "meister", "geselle", "schneider", "weber", "müller", "mueller", "schuster", "wirt", "wirth", "lehrer", "schreiber", "richter", "gericht", "amt", "pfarramt",
    "ehefrau", "ehemann", "gattin", "gatte", "witwe", "witwer", "weib", "tochter", "sohn", "kind", "kinder", "vater", "mutter", "eltern", "bruder", "schwester",
    "großvater", "grossvater", "großmutter", "grossmutter", "enkel", "enkelin", "onkel", "tante", "vetter", "base", "schwager", "schwägerin", "schwaegerin",
    "jahr", "jahre", "jahren", "jährig", "jaehrig", "monat", "monate", "monaten", "woche", "wochen", "tag", "tage", "tagen", "stunde", "stunden", "minute", "minuten",
    "januar", "februar", "märz", "maerz", "april", "mai", "juni", "juli", "august", "september", "oktober", "november", "dezember",
    "ledig", "verheiratet", "verwitwet", "geschieden", "ehelich", "unehelich", "geboren", "geb", "geborene", "getauft", "gestorben", "beerdigt", "begraben", "konfirmiert",
    "katholisch", "evangelisch", "lutherisch", "reformiert", "israelitisch", "jüdisch", "juedisch", "kirche", "pfarre", "pfarrer", "pastor", "kaplan", "vikar",
    "ort", "orte", "dorf", "stadt", "gemeinde", "kreis", "bezirk", "land", "hof", "haus", "straße", "strasse", "gasse", "platz", "mühle", "muehle", "schloss", "kolonie",
})
BK_AUTOCORRECT_COMMON_WORDS.setdefault("en", set()).update({
    "under", "over", "after", "before", "between", "beside", "near", "also", "not", "no", "yes", "this", "that", "these", "those", "page", "line", "entry", "number",
})
BK_AUTOCORRECT_COMMON_WORDS.setdefault("fr", set()).update({
    "sous", "sur", "après", "apres", "avant", "entre", "aussi", "non", "oui", "ce", "cette", "ces", "page", "ligne", "entrée", "entree", "numéro", "numero",
})

BK_AUTOCORRECT_COMMON_NORMS = set(BK_AUTOCORRECT_SKIP_NORMS)
for _words in BK_AUTOCORRECT_COMMON_WORDS.values():
    for _word in _words:
        BK_AUTOCORRECT_COMMON_NORMS.add(_bk_autocorrect_norm(_word))


def _bk_ac_is_common_norm(norm: str) -> bool:
    return str(norm or "") in BK_AUTOCORRECT_COMMON_NORMS


def _bk_ac_language_common_terms(lang: str) -> List[str]:
    lang = _bk_ac_norm_lang(lang)
    words = set(BK_AUTOCORRECT_COMMON_WORDS.get(lang, set()))
    words.update(BK_AUTOCORRECT_COMMON_WORDS.get("de", set()) if lang != "de" else set())
    return sorted(words, key=lambda value: (len(value), value.casefold()))


def _bk_ac_packaged_dictionary_dir() -> str:
    candidates: List[str] = []
    base = getattr(sys, "_MEIPASS", None)
    if base:
        candidates.append(os.path.join(base, "bottled_kraken", "dictionaries"))
        candidates.append(os.path.join(base, "dictionaries"))
    candidates.append(os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "dictionaries")))
    for candidate in candidates:
        try:
            if os.path.isdir(candidate) and any(name.lower().endswith(".json") for name in os.listdir(candidate)):
                return candidate
        except Exception:
            continue
    return candidates[-1]


def _bk_ac_runtime_dictionary_root() -> str:
    # Mirrored and user dictionaries stay in the platform-specific application
    # data directory unless BOTTLED_KRAKEN_USER_DIR is set explicitly.
    path = str(bottled_kraken_user_path("dictionaries"))
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass
    return path


_BK_AC_SYNC_LOCK = threading.Lock()
_BK_AC_PACKAGED_MANIFEST = "dictionary_manifest.json"
_BK_AC_LOCAL_MANIFEST = ".packaged_dictionary_manifest.json"


def _bk_ac_sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _bk_ac_read_manifest(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict) and isinstance(data.get("files"), dict):
            return data
    except Exception:
        pass
    return {"schema": 1, "files": {}}


def _bk_ac_write_manifest(path: str, data: Dict[str, Any]) -> None:
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    temp_path = f"{path}.tmp-{os.getpid()}-{threading.get_ident()}"
    try:
        with open(temp_path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.flush()
            try:
                os.fsync(handle.fileno())
            except OSError:
                pass
        os.replace(temp_path, path)
    finally:
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except OSError:
            pass


def _bk_ac_atomic_copy(source: str, destination: str) -> None:
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    temp_path = f"{destination}.tmp-{os.getpid()}-{threading.get_ident()}"
    try:
        shutil.copy2(source, temp_path)
        os.replace(temp_path, destination)
    finally:
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except OSError:
            pass


def _bk_ac_manifest_entry(path: str) -> Dict[str, Any]:
    return {"size": int(os.path.getsize(path)), "sha256": _bk_ac_sha256(path)}


def _bk_ac_dictionary_file_is_current(
    source: str,
    destination: str,
    packaged_entry: Optional[Dict[str, Any]],
    local_entry: Optional[Dict[str, Any]],
) -> bool:
    if not os.path.isfile(destination):
        return False
    try:
        source_size = int(os.path.getsize(source))
        destination_size = int(os.path.getsize(destination))
    except OSError:
        return False
    if source_size != destination_size:
        return False

    # Onefile-Dateien werden bei jedem Start neu nach _MEIPASS entpackt und
    # erhalten dabei wechselnde Zeitstempel. Der Build-Manifestvergleich ist
    # deshalb die schnelle, stabile Quelle der Wahrheit.
    if isinstance(packaged_entry, dict) and packaged_entry.get("sha256"):
        expected = {
            "size": int(packaged_entry.get("size", source_size)),
            "sha256": str(packaged_entry.get("sha256")),
        }
        if isinstance(local_entry, dict):
            known = {
                "size": int(local_entry.get("size", -1)),
                "sha256": str(local_entry.get("sha256", "")),
            }
            if known == expected and destination_size == expected["size"]:
                return True
        try:
            return _bk_ac_sha256(destination) == expected["sha256"]
        except Exception:
            return False

    # Rückwärtskompatibilität für Builds ohne Manifest. Bei identischen
    # Zeitstempeln genügt der Größenvergleich; andernfalls wird einmalig der
    # Inhalt verglichen, statt die 35-MB-Dateien bei jedem Start neu zu kopieren.
    try:
        if int(os.path.getmtime(source)) <= int(os.path.getmtime(destination)):
            return True
    except OSError:
        pass
    try:
        return _bk_ac_sha256(source) == _bk_ac_sha256(destination)
    except Exception:
        return False


def _bk_ac_sync_runtime_dictionaries() -> str:
    # Serialisiert Hintergrund-Sync beim Start und spaetere On-Demand-Aufrufe,
    # damit nicht zwei Threads gleichzeitig dieselben ~35-MB-Dateien kopieren.
    with _BK_AC_SYNC_LOCK:
        return _bk_ac_sync_runtime_dictionaries_locked()


def _bk_ac_sync_runtime_dictionaries_locked() -> str:
    root = _bk_ac_runtime_dictionary_root()
    embedded = os.path.join(root, "embedded")
    try:
        os.makedirs(embedded, exist_ok=True)
    except Exception:
        pass

    src = _bk_ac_packaged_dictionary_dir()
    packaged_manifest = _bk_ac_read_manifest(os.path.join(src, _BK_AC_PACKAGED_MANIFEST))
    packaged_files = packaged_manifest.get("files", {}) if isinstance(packaged_manifest, dict) else {}
    local_manifest_path = os.path.join(embedded, _BK_AC_LOCAL_MANIFEST)
    local_manifest = _bk_ac_read_manifest(local_manifest_path)
    local_files = local_manifest.get("files", {}) if isinstance(local_manifest, dict) else {}
    next_local_files: Dict[str, Any] = {}

    try:
        if os.path.isdir(src):
            for name in sorted(os.listdir(src)):
                if not name.lower().endswith(".json") or name == _BK_AC_PACKAGED_MANIFEST:
                    continue
                sp = os.path.join(src, name)
                if not os.path.isfile(sp):
                    continue
                dp = os.path.join(embedded, name)
                packaged_entry = packaged_files.get(name) if isinstance(packaged_files, dict) else None
                local_entry = local_files.get(name) if isinstance(local_files, dict) else None
                try:
                    current = _bk_ac_dictionary_file_is_current(
                        sp, dp, packaged_entry, local_entry
                    )
                    if not current:
                        _bk_ac_atomic_copy(sp, dp)
                    if isinstance(packaged_entry, dict) and packaged_entry.get("sha256"):
                        next_local_files[name] = {
                            "size": int(packaged_entry.get("size", os.path.getsize(dp))),
                            "sha256": str(packaged_entry.get("sha256")),
                        }
                    else:
                        next_local_files[name] = _bk_ac_manifest_entry(dp)
                except Exception:
                    # Eine bereits vollständige ältere Spiegeldatei bleibt nutzbar;
                    # unvollständige Kopien werden wegen des atomaren Austauschs nie
                    # als fertige Zieldatei sichtbar.
                    if os.path.isfile(dp):
                        try:
                            next_local_files[name] = _bk_ac_manifest_entry(dp)
                        except Exception:
                            pass
    except Exception:
        pass

    if next_local_files:
        try:
            _bk_ac_write_manifest(
                local_manifest_path,
                {"schema": 1, "files": next_local_files},
            )
        except Exception:
            pass

    for code in _bk_ac_available_langs():
        path = os.path.join(embedded, f"{_bk_ac_norm_lang(code)}.json")
        if not os.path.exists(path):
            try:
                with open(path, "w", encoding="utf-8") as handle:
                    json.dump({"language": _bk_ac_norm_lang(code), "terms": []}, handle, ensure_ascii=False, indent=2)
            except Exception:
                pass
    return embedded


def _bk_ac_resource_dir() -> str:
    # Runtime dictionaries are mirrored into the BottledKraken user folder so a
    # compiled one-file build still has physical dictionary files.
    return _bk_ac_sync_runtime_dictionaries()


def _bk_ac_user_dir() -> str:
    base = os.environ.get("BOTTLED_KRAKEN_CONFIG_DIR")
    if base:
        path = os.path.join(base, "dictionaries")
    else:
        path = os.path.join(_bk_ac_runtime_dictionary_root(), "user")
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass
    return path


def _bk_ac_norm_lang(lang: str) -> str:
    available = _bk_ac_available_langs()
    fallback = "de" if "de" in available else (available[0] if available else "de")
    raw = str(lang or fallback).strip().lower().replace("-", "_")
    if raw in available:
        return raw
    short = raw.split("_", 1)[0]
    if short in available:
        return short
    try:
        return str(translation.normalize_language_code(raw))
    except Exception:
        pass
    return fallback


def _bk_ac_read_json_terms(path: str) -> List[str]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception:
        return []
    if isinstance(data, dict):
        data = data.get("terms") or data.get("words") or []
    out: List[str] = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                value = item.get("term") or item.get("word") or item.get("text") or item.get("name") or item.get("value")
            else:
                value = item
            value = str(value or "").strip()
            if value:
                out.append(value)
    return out


def _bk_ac_user_path(lang: str) -> str:
    return os.path.join(_bk_ac_user_dir(), f"{_bk_ac_norm_lang(lang)}.json")


def _bk_ac_load_builtin_terms(lang: str) -> List[str]:
    lang = _bk_ac_norm_lang(lang)
    path = os.path.join(_bk_ac_resource_dir(), f"{lang}.json")
    terms = _bk_ac_read_json_terms(path)
    if lang != "de":
        terms.extend(_bk_ac_read_json_terms(os.path.join(_bk_ac_resource_dir(), "de.json"))[:40])
    return terms


def _bk_ac_load_user_terms(lang: str) -> List[str]:
    return _bk_ac_read_json_terms(_bk_ac_user_path(lang))


def _bk_ac_dedupe_terms(terms: Iterable[Any]) -> Tuple[List[str], Dict[str, List[str]]]:
    by_norm: Dict[str, str] = {}
    duplicates: Dict[str, List[str]] = {}
    for item in terms or []:
        term = str(item or "").strip()
        if not term:
            continue
        norm = _bk_autocorrect_norm(term)
        if len(norm) < 2:
            continue
        if norm in by_norm:
            duplicates.setdefault(norm, [by_norm[norm]]).append(term)
            continue
        by_norm[norm] = term
    return list(by_norm.values()), duplicates


def _bk_ac_write_user_terms(lang: str, terms: Iterable[Any]) -> bool:
    clean, _dups = _bk_ac_dedupe_terms(terms)
    try:
        os.makedirs(_bk_ac_user_dir(), exist_ok=True)
        with open(_bk_ac_user_path(lang), "w", encoding="utf-8") as handle:
            json.dump({"language": _bk_ac_norm_lang(lang), "terms": clean}, handle, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def _bk_ac_open_directory(path: str) -> bool:
    directory = os.path.abspath(os.path.expanduser(str(path or "")))
    try:
        os.makedirs(directory, exist_ok=True)
    except Exception:
        return False

    # Externe Desktop-Programme dürfen im PyInstaller-Onefile-Build nicht die
    # gebündelten Qt-/GTK-Bibliothekspfade erben. Genau das verhindert unter
    # Linux häufig, dass xdg-open bzw. Dolphin überhaupt startet.
    try:
        from bottled_kraken.subprocess_env import bk_clean_child_env
        child_env = bk_clean_child_env()
    except Exception:
        child_env = dict(os.environ)

    try:
        if sys.platform.startswith("win"):
            os.startfile(directory)  # type: ignore[attr-defined]
            return True
        commands: List[List[str]] = []
        if sys.platform == "darwin":
            commands.append(["open", directory])
        else:
            commands.extend([
                ["xdg-open", directory],
                ["gio", "open", directory],
                ["kioclient6", "exec", QUrl.fromLocalFile(directory).toString()],
                ["kioclient5", "exec", QUrl.fromLocalFile(directory).toString()],
                ["kioclient", "exec", QUrl.fromLocalFile(directory).toString()],
            ])
        for command in commands:
            if not shutil.which(command[0]):
                continue
            try:
                subprocess.Popen(
                    command,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    close_fds=True,
                    start_new_session=True,
                    env=child_env,
                )
                return True
            except Exception:
                continue
    except Exception:
        pass

    try:
        return bool(QDesktopServices.openUrl(QUrl.fromLocalFile(directory)))
    except Exception:
        return False


def _bk_ac_current_lang(window) -> str:
    return _bk_ac_norm_lang(getattr(window, "current_lang", "de"))


def _bk_ac_reference_terms_with_weights(terms: Iterable[Any]) -> List[Dict[str, Any]]:
    out_by_norm: Dict[str, Dict[str, Any]] = {}
    for item in terms or []:
        term, weight = _bk_autocorrect_payload_entry(item)
        term = str(term or "").strip()
        norm = _bk_autocorrect_norm(term)
        if not norm or len(norm) < 2:
            continue
        entry = out_by_norm.get(norm)
        if entry is None:
            out_by_norm[norm] = {"term": term, "weight": float(weight), "best_weight": float(weight)}
        else:
            entry["weight"] = float(entry.get("weight", 1.0)) + float(weight)
            if float(weight) > float(entry.get("best_weight", 0.0)):
                entry["term"] = term
                entry["best_weight"] = float(weight)
    return [{"term": entry["term"], "weight": float(entry.get("weight", 1.0))} for entry in out_by_norm.values()]


def _bk_ac_build_index(terms: Iterable[Any]) -> Tuple[Dict[int, List[Tuple[str, str]]], Dict[str, str], Dict[str, float]]:
    exact: Dict[str, str] = {}
    weights: Dict[str, float] = {}
    display_weight: Dict[str, float] = {}
    for item in terms or []:
        term, weight = _bk_autocorrect_payload_entry(item)
        term = str(term or "").strip()
        norm = _bk_autocorrect_norm(term)
        if not norm or len(norm) < 2:
            continue
        weights[norm] = float(weights.get(norm, 0.0)) + float(weight)
        if norm not in exact or float(weight) >= float(display_weight.get(norm, 0.0)):
            exact[norm] = term
            display_weight[norm] = float(weight)
    buckets: Dict[int, List[Tuple[str, str]]] = {}
    for norm, term in exact.items():
        buckets.setdefault(len(norm), []).append((norm, term))
    return buckets, exact, weights


def _bk_ac_fused_initial_suggestion(token: str, exact: dict) -> Optional[str]:
    raw = str(token or "").strip()
    match = re.fullmatch(r"([A-ZÄÖÜÀ-Ý][A-Za-zÄÖÜäöüßÀ-ÿ]{2,})([A-ZÄÖÜÀ-Ý])", raw)
    if not match:
        return None
    prefix, initial = match.group(1), match.group(2)
    norm = _bk_autocorrect_norm(prefix)
    if norm in exact and not _bk_ac_is_common_norm(norm):
        return f"{_bk_autocorrect_restore_case(prefix, exact[norm])} {initial}"
    return None


def _bk_ac_suggestion_is_strong(token_norm: str, cand_norm: str, dist: int, weights: dict) -> bool:
    if not token_norm or not cand_norm or dist <= 0:
        return False
    if _bk_ac_is_common_norm(token_norm):
        return False
    rank = 0
    try:
        from bottled_kraken.common import _bk_autocorrect_similarity_rank
        rank = _bk_autocorrect_similarity_rank(token_norm, cand_norm)
    except Exception:
        rank = 0
    weight = float((weights or {}).get(cand_norm, 1.0))
    if len(token_norm) <= 4:
        return dist == 1 and rank >= 7 and weight >= 20.0
    if len(token_norm) <= 6:
        return dist <= 1 or (dist == 2 and rank >= 10 and weight >= 50.0)
    return dist <= 2 and rank >= 8


def _bk_ac_suggestion_list(token: str, buckets: dict, exact: dict, weights: dict, limit: int = 5) -> List[str]:
    norm = _bk_autocorrect_norm(token)
    if not norm or norm in exact or norm in BK_AUTOCORRECT_SKIP_NORMS or _bk_ac_is_common_norm(norm):
        return []
    fused = _bk_ac_fused_initial_suggestion(token, exact)
    out: List[str] = []
    if fused:
        out.append(fused)
    first, dist, first_norm = _bk_autocorrect_best_term(norm, buckets, exact, weights)
    if first and _bk_ac_suggestion_is_strong(norm, first_norm, dist, weights):
        restored_first = _bk_autocorrect_restore_case(token, first)
        if restored_first not in out:
            out.append(restored_first)
    for ln in range(max(1, len(norm) - 2), len(norm) + 3):
        for cand_norm, cand_term in buckets.get(ln, []):
            if cand_norm == norm:
                continue
            term, d, resolved_norm = _bk_autocorrect_best_term(norm, {ln: [(cand_norm, cand_term)]}, {cand_norm: cand_term}, weights)
            if term and _bk_ac_suggestion_is_strong(norm, resolved_norm or cand_norm, d, weights):
                restored = _bk_autocorrect_restore_case(token, cand_term)
                if restored not in out:
                    out.append(restored)
            if len(out) >= limit:
                return out
    return out[:limit]


def _bk_ac_token_looks_ocr_suspicious(token: str) -> bool:
    raw = str(token or "")
    if re.search(r"[0-9|\[\]{}<>]", raw):
        return True
    if re.search(r"[a-zäöüßà-ÿ][A-ZÄÖÜÀ-Ý]", raw):
        return True
    if re.search(r"[A-ZÄÖÜÀ-Ý]{2,}[a-zäöüßà-ÿ]", raw):
        return True
    if re.search(r"(.)\1\1", _bk_autocorrect_norm(raw)):
        return True
    return False


def _bk_ac_should_mark_suggestion(token: str, suggestions: List[str], weights: dict) -> bool:
    if not suggestions:
        return False
    token_norm = _bk_autocorrect_norm(token)
    first_norm = _bk_autocorrect_norm(suggestions[0])
    if not first_norm:
        return False
    # Common dictionary words are mainly used to suppress false positives.
    # Unknown words are not marked just because they resemble a common word, unless
    # the OCR token itself has a clearly suspicious shape.
    if _bk_ac_is_common_norm(first_norm) and not _bk_ac_token_looks_ocr_suspicious(token):
        return False
    if len(token_norm) <= 4 and first_norm not in weights and not _bk_ac_token_looks_ocr_suspicious(token):
        return False
    return True


def _bk_ac_find_errors(text: str, terms: Iterable[Any]) -> List[Dict[str, Any]]:
    buckets, exact, weights = _bk_ac_build_index(terms)
    if not exact:
        return []
    errors: List[Dict[str, Any]] = []
    for match in BK_AUTOCORRECT_WORD_RE.finditer(str(text or "")):
        token = match.group(0)
        norm = _bk_autocorrect_norm(token)
        if len(norm) < 3 or norm in exact or norm in BK_AUTOCORRECT_SKIP_NORMS or _bk_ac_is_common_norm(norm):
            continue
        suggestions = _bk_ac_suggestion_list(token, buckets, exact, weights, limit=5)
        if suggestions and _bk_ac_should_mark_suggestion(token, suggestions, weights):
            errors.append({
                "start": int(match.start()),
                "end": int(match.end()),
                "token": token,
                "suggestions": suggestions,
            })
    return errors


class BKAutocorrectUnderlineDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        if index.column() != 1:
            return
        errors = index.data(BK_AUTOCORRECT_ERRORS_ROLE) or []
        text = index.data(BK_AUTOCORRECT_TEXT_ROLE) or index.data(Qt.DisplayRole) or ""
        if not errors or not text:
            return
        widget = option.widget
        opt = QStyleOptionViewItem(option)
        try:
            self.initStyleOption(opt, index)
            text_rect_sub = getattr(QStyle, "SE_ItemViewItemText", getattr(QStyle.SubElement, "SE_ItemViewItemText"))
            text_rect = widget.style().subElementRect(text_rect_sub, opt, widget)
        except Exception:
            text_rect = QRect(option.rect).adjusted(4, 0, -4, 0)
        metrics = QFontMetrics(opt.font if hasattr(opt, "font") else option.font)
        y = min(option.rect.bottom() - 3, text_rect.bottom() - 2)
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.setPen(QPen(QColor(210, 0, 0), 2, Qt.SolidLine))
        for err in errors:
            try:
                start = int(err.get("start", 0))
                end = int(err.get("end", start))
            except Exception:
                continue
            prefix = str(text)[:start]
            word = str(text)[start:end]
            # Fine-tuned visual correction: only nudge the underline slightly to the right,
            # not by a full character width.
            x_shift = 2
            x0 = text_rect.left() + metrics.horizontalAdvance(prefix) + x_shift
            x1 = x0 + max(8, metrics.horizontalAdvance(word))
            painter.drawLine(x0, y, min(x1, text_rect.right()), y)
        painter.restore()


def _bk_ac_dictionary_terms(self) -> List[Dict[str, Any]]:
    lang = _bk_ac_current_lang(self)
    terms = []
    for term in _bk_ac_language_common_terms(lang):
        terms.append({"term": term, "weight": 90.0})
    for term in _bk_ac_load_builtin_terms(lang):
        terms.append({"term": term, "weight": 100.0})
    for term in _bk_ac_load_user_terms(lang):
        terms.append({"term": term, "weight": 180.0})
    return _bk_ac_reference_terms_with_weights(terms)


def _bk_ac_install_delegate(self):
    try:
        if hasattr(self, "list_lines") and not getattr(self.list_lines, "_bk_autocorrect_delegate", None):
            delegate = BKAutocorrectUnderlineDelegate(self.list_lines)
            self.list_lines.setItemDelegateForColumn(1, delegate)
            self.list_lines._bk_autocorrect_delegate = delegate
    except Exception:
        pass


def _bk_ac_all_terms(self) -> List[Dict[str, Any]]:
    if not bool(getattr(self, "kraken_autocorrect_enabled", False)):
        return []
    terms = []
    try:
        terms.extend(_bk_ac_dictionary_terms(self))
    except Exception:
        pass
    try:
        original = getattr(self, "_bk_original_kraken_autocorrect_reference_terms", None)
        if callable(original):
            for item in original():
                term, weight = _bk_autocorrect_payload_entry(item)
                terms.append({"term": term, "weight": max(1.0, float(weight))})
    except Exception:
        pass
    return _bk_ac_reference_terms_with_weights(terms)


# ---------------------------------------------------------------------------
# Zweistufige Wörterbuch-Engine (RAM-Kleinwörterbuch + SQLite-Store für die
# grossen <lang>_erweitert.json-Listen). Siehe autocorrect_dictionary_store.py.
# ---------------------------------------------------------------------------

_BK_AC_ENGINE_CACHE: Dict[Tuple[str, float, bool], Dict[str, Any]] = {}


def _bk_ac_store_for(lang: str):
    if _bk_ac_get_store is None:
        return None
    lang = _bk_ac_norm_lang(lang)
    root = _bk_ac_runtime_dictionary_root()
    source = os.path.join(root, "embedded", f"{lang}_erweitert.json")
    try:
        return _bk_ac_get_store(lang, os.path.join(root, "index"), [source], _bk_autocorrect_norm)
    except Exception:
        return None


def _bk_ac_ensure_store_ready(self, store):
    """Liefert den Store nur, wenn seine Datenbank aktuell ist; stösst sonst
    einen einmaligen Hintergrund-Aufbau an (UI bleibt derweil im RAM-Modus)."""
    if store is None:
        return None
    try:
        if store.is_ready():
            return store
        if not store.existing_sources():
            return None
    except Exception:
        return None
    if getattr(store, "_bk_build_thread", None) is None:
        if int(getattr(store, "_bk_build_attempts", 0)) >= 2:
            return None  # zweimal gescheitert - nicht endlos erneut versuchen
        store._bk_build_attempts = int(getattr(store, "_bk_build_attempts", 0)) + 1
        try:
            self.status_bar.showMessage(_bk_ac_text(
                self, "autocorrect_index_building"), 8000)
        except Exception:
            pass
        import threading as _threading

        def _run():
            ok = store.build()
            store._bk_build_done = bool(ok)
            store._bk_build_finished = True

        thread = _threading.Thread(target=_run, name=f"bk-dict-index-{store.lang}", daemon=True)
        store._bk_build_thread = thread
        store._bk_build_finished = False
        thread.start()

        # GUI-seitiger Poller: sobald der Build fertig ist, Engine-Cache
        # verwerfen und die Zeilenmarkierungen automatisch neu berechnen.
        # (Ohne diesen Schritt blieben nach einem Projekt-Laden waehrend des
        # ersten Index-Aufbaus dauerhaft nur die RAM-Markierungen sichtbar.)
        try:
            from PySide6.QtCore import QTimer

            timer = QTimer(self)
            timer.setInterval(500)

            def _poll():
                if not getattr(store, "_bk_build_finished", False):
                    return
                timer.stop()
                timer.deleteLater()
                store._bk_build_thread = None
                _BK_AC_ENGINE_CACHE.clear()
                if getattr(store, "_bk_build_done", False):
                    try:
                        self._bk_autocorrect_refresh_line_marks()
                    except Exception:
                        pass
                else:
                    try:
                        self.status_bar.showMessage(_bk_ac_text(
                            self, "autocorrect_index_failed").format(
                                getattr(store, "build_error", "?")), 9000)
                    except Exception:
                        pass

            timer.timeout.connect(_poll)
            timer.start()
        except Exception:
            pass
    return None


def _bk_ac_engine_helpers() -> Dict[str, Any]:
    g = globals()
    return {
        "norm": _bk_autocorrect_norm,
        "distance": g.get("_bk_autocorrect_distance"),
        "max_distance": g.get("_bk_autocorrect_max_distance"),
        "similarity_rank": g.get("_bk_autocorrect_similarity_rank"),
        "restore_case": _bk_autocorrect_restore_case,
        "is_strong": _bk_ac_suggestion_is_strong,
        "is_common_norm": _bk_ac_is_common_norm,
        "skip_norms": BK_AUTOCORRECT_SKIP_NORMS,
        "fused_initial": _bk_ac_fused_initial_suggestion,
    }


def _bk_ac_engine(self) -> Dict[str, Any]:
    lang = _bk_ac_current_lang(self)
    user_mtime = 0.0
    try:
        user_mtime = os.path.getmtime(_bk_ac_user_path(lang))
    except OSError:
        pass
    store = _bk_ac_store_for(lang)
    ready = _bk_ac_ensure_store_ready(self, store)
    key = (lang, user_mtime, ready is not None)
    engine = _BK_AC_ENGINE_CACHE.get(key)
    if engine is None:
        buckets, exact, weights = _bk_ac_build_index(_bk_ac_dictionary_terms(self))
        engine = {"lang": lang, "buckets": buckets, "exact": exact,
                  "weights": weights, "store": ready, "sugcache": {}}
        _BK_AC_ENGINE_CACHE.clear()
        _BK_AC_ENGINE_CACHE[key] = engine
        if ready is not None and getattr(store, "_bk_build_done", False):
            store._bk_build_done = False
            try:
                self.status_bar.showMessage(_bk_ac_text(
                    self, "autocorrect_index_ready").format(ready.term_count()), 5000)
            except Exception:
                pass
    return engine


def _bk_ac_engine_contains(engine: Dict[str, Any], norm: str) -> bool:
    if norm in engine["exact"]:
        return True
    store = engine.get("store")
    return store is not None and store.contains(norm)


def _bk_ac_find_errors_engine(self, text: str) -> List[Dict[str, Any]]:
    """Wie _bk_ac_find_errors, aber über die zweistufige Engine: exakte
    Prüfung als Index-Lookup, Vorschläge per Distanz-1-Generierung mit
    Distanz-2-Fallback. Ohne Store-Modul identisches Legacy-Verhalten."""
    engine = _bk_ac_engine(self)
    if not engine["exact"] and engine.get("store") is None:
        return []
    helpers = _bk_ac_engine_helpers()
    weights_view = engine["weights"]
    if engine.get("store") is not None and _bk_ac_make_weights_view is not None:
        weights_view = _bk_ac_make_weights_view(engine["weights"], engine["store"])
    errors: List[Dict[str, Any]] = []
    for match in BK_AUTOCORRECT_WORD_RE.finditer(str(text or "")):
        token = match.group(0)
        norm = _bk_autocorrect_norm(token)
        if (len(norm) < 3 or norm in BK_AUTOCORRECT_SKIP_NORMS
                or _bk_ac_is_common_norm(norm) or _bk_ac_engine_contains(engine, norm)):
            continue
        if _bk_ac_engine_suggestions_impl is not None:
            suggestions = _bk_ac_engine_suggestions_impl(
                token, engine["buckets"], engine["exact"], engine["weights"],
                engine.get("store"), helpers, limit=5, cache=engine["sugcache"])
        else:
            suggestions = _bk_ac_suggestion_list(
                token, engine["buckets"], engine["exact"], engine["weights"], limit=5)
        if suggestions and _bk_ac_should_mark_suggestion(token, suggestions, weights_view):
            errors.append({
                "start": int(match.start()),
                "end": int(match.end()),
                "token": token,
                "suggestions": suggestions,
            })
    return errors


def _bk_ac_refresh_line_marks(self):
    try:
        self._bk_autocorrect_install_delegate()
    except Exception:
        pass
    tree = getattr(self, "list_lines", None)
    if tree is None:
        return
    try:
        tree.blockSignals(True)
        for row in range(tree.count()):
            item = tree.row_item(row)
            if item is None:
                continue
            text = item.text(1) or ""
            errors = _bk_ac_find_errors_engine(self, text)
            item.setData(1, BK_AUTOCORRECT_ERRORS_ROLE, errors)
            item.setData(1, BK_AUTOCORRECT_TEXT_ROLE, text)
            if errors:
                item.setToolTip(1, _bk_ac_text(self, "autocorrect_tooltip_errors").format(", ".join(f"{e.get('token')} → {', '.join(e.get('suggestions', [])[:3])}" for e in errors[:4])))
            else:
                item.setToolTip(1, "")
    finally:
        try:
            tree.blockSignals(False)
            tree.viewport().update()
        except Exception:
            pass



def _bk_ac_sync_keep_exact_row(self, task, row: int):
    tree = getattr(self, "list_lines", None)
    scroll_value = None
    try:
        scroll_value = tree.verticalScrollBar().value() if tree is not None else None
    except Exception:
        scroll_value = None
    if hasattr(self, "_sync_ui_after_recs_change"):
        self._sync_ui_after_recs_change(task, keep_row=row)
    try:
        if tree is not None and 0 <= row < tree.count():
            tree.setCurrentRow(row)
            if scroll_value is not None:
                tree.verticalScrollBar().setValue(scroll_value)
            item = tree.row_item(row)
            if item is not None:
                tree.scrollToItem(item, tree.EnsureVisible)
    except Exception:
        pass
    try:
        self._bk_autocorrect_refresh_line_marks()
    except Exception:
        pass

def _bk_ac_replace_token_once(text: str, start: int, end: int, replacement: str) -> str:
    return str(text or "")[:start] + str(replacement or "") + str(text or "")[end:]


def _bk_ac_apply_suggestion(self, row: int, err: dict, replacement: str):
    task = self._current_task() if hasattr(self, "_current_task") else None
    if not task or not task.results:
        return
    _text, _kr_records, _im, recs = task.results
    if not (0 <= row < len(recs)):
        return
    old = str(recs[row].text or "")
    start = int(err.get("start", 0))
    end = int(err.get("end", start))
    if start < 0 or end > len(old) or end <= start:
        return
    new = _bk_ac_replace_token_once(old, start, end, replacement).strip()
    new = re.sub(r"(?<=\b[A-ZÄÖÜÀ-Ý])\.(?=[A-ZÄÖÜÀ-Ý][a-zäöüßà-ÿ])", ". ", new)
    new = re.sub(r"([A-ZÄÖÜÀ-Ý])\.\.(?=\s|[A-ZÄÖÜÀ-Ý]|$)", r"\1.", new)
    if new == old:
        return
    try:
        self._push_undo(task)
    except Exception:
        pass
    recs[row].text = new
    task.edited = True
    _bk_ac_sync_keep_exact_row(self, task, row)


def _bk_ac_apply_all_current_line(self, row: int):
    task = self._current_task() if hasattr(self, "_current_task") else None
    if not task or not task.results:
        return
    _text, _kr_records, _im, recs = task.results
    if not (0 <= row < len(recs)):
        return
    new = _bk_ac_correct_text_with_terms(self, recs[row].text, _bk_ac_extract_document_terms(recs))
    if new and new != recs[row].text:
        try:
            self._push_undo(task)
        except Exception:
            pass
        recs[row].text = new
        task.edited = True
        _bk_ac_sync_keep_exact_row(self, task, row)


def _bk_ac_apply_all_visible(self):
    task = self._current_task() if hasattr(self, "_current_task") else None
    if not task or not task.results:
        return
    _text, _kr_records, _im, recs = task.results
    document_terms = _bk_ac_extract_document_terms(recs)
    changed = False
    try:
        self._push_undo(task)
    except Exception:
        pass
    for rv in recs:
        new = _bk_ac_correct_text_with_terms(self, rv.text, document_terms)
        if new and new != rv.text:
            rv.text = new
            changed = True
    if changed:
        task.edited = True
        keep = self.list_lines.currentRow() if hasattr(self, "list_lines") else 0
        _bk_ac_sync_keep_exact_row(self, task, keep)


def _bk_ac_extract_document_terms(recs: Iterable[Any]) -> List[Dict[str, Any]]:
    counter: Counter[str] = Counter()
    display: Dict[str, str] = {}
    for rv in recs or []:
        text = str(getattr(rv, "text", rv) or "")
        for match in BK_AUTOCORRECT_WORD_RE.finditer(text):
            token = match.group(0).strip(" \t\r\n.,;:()[]{}<>\"'`´")
            if not token or len(token) < 3:
                continue
            if re.search(r"[a-zäöüßà-ÿ][A-ZÄÖÜÀ-Ý]", token):
                continue
            norm = _bk_autocorrect_norm(token)
            if len(norm) < 3 or _bk_ac_is_common_norm(norm):
                continue
            letters = "".join(ch for ch in token if ch.isalpha())
            if not letters:
                continue
            if not (letters[0].isupper() or "-" in token):
                continue
            counter[norm] += 1
            if norm not in display or token[0].isupper():
                display[norm] = token
    out: List[Dict[str, Any]] = []
    for norm, count in counter.items():
        term = display.get(norm, norm)
        # Dokumentinterne Treffer bekommen nur mittleres Gewicht: genug für echte Namenswiederholungen,
        # aber schwächer als Benutzerwörterbuch und Referenzdateien.
        out.append({"term": term, "weight": 20.0 + min(80.0, float(count) * 10.0)})
    return out


def _bk_ac_replacements_with_extra_terms(self, extra_terms: Iterable[Any] = ()) -> str:
    text = str(getattr(self, "kraken_auto_revision_replacements", "") or "")
    if not text and hasattr(self, "_kraken_auto_revision_default_text"):
        text = self._kraken_auto_revision_default_text()
    terms: List[Dict[str, Any]] = []
    for item in extra_terms or []:
        term, weight = _bk_autocorrect_payload_entry(item)
        norm = _bk_autocorrect_norm(term)
        # Normal dictionary words are acceptance words. They prevent false positives,
        # but they are not automatic replacement targets.
        if term and norm and not _bk_ac_is_common_norm(norm):
            terms.append({"term": term, "weight": float(weight)})
    if terms:
        try:
            text += "\n#BK_AUTOCORRECT_TERMS_JSON=" + json.dumps(_bk_ac_reference_terms_with_weights(terms), ensure_ascii=False)
        except Exception:
            pass
    return text


def _bk_ac_fix_fused_name_initials_text(text: str, terms: Iterable[Any]) -> str:
    _buckets, exact, _weights = _bk_ac_build_index(terms)
    if not exact:
        return str(text or "")

    def repl(match):
        prefix = match.group(1)
        initial = match.group(2)
        norm = _bk_autocorrect_norm(prefix)
        if norm in exact and not _bk_ac_is_common_norm(norm):
            return f"{_bk_autocorrect_restore_case(prefix, exact[norm])} {initial}"
        return match.group(0)

    txt = re.sub(r"\b([A-ZÄÖÜÀ-Ý][a-zäöüßà-ÿ]{2,})([A-ZÄÖÜÀ-Ý])(?=\.)", repl, str(text or ""))
    txt = re.sub(r"\b([A-ZÄÖÜÀ-Ý][a-zäöüßà-ÿ]{2,})([A-ZÄÖÜÀ-Ý])(?=\s|,|;|:|$)", repl, txt)
    txt = re.sub(r"(?<=\b[A-ZÄÖÜÀ-Ý])\.(?=[A-ZÄÖÜÀ-Ý][a-zäöüßà-ÿ])", ". ", txt)
    return txt


def _bk_ac_correct_text_with_terms(self, text: str, extra_terms: Iterable[Any] = ()) -> str:
    terms = []
    try:
        terms.extend(self._kraken_autocorrect_reference_terms())
    except Exception:
        pass
    terms.extend(list(extra_terms or []))
    replacements = _bk_ac_replacements_with_extra_terms(self, terms)
    new = _apply_ocr_auto_revision_replacements(text, replacements)
    new = _bk_ac_fix_fused_name_initials_text(new, terms)
    return re.sub(r"[ \t\r\f\v]+", " ", str(new or "")).strip()


def _bk_ac_apply_document_autocorrect_to_recs(self, recs: Iterable[Any]) -> bool:
    if not bool(getattr(self, "kraken_autocorrect_enabled", False)):
        return False
    recs = list(recs or [])
    if not recs:
        return False
    document_terms = _bk_ac_extract_document_terms(recs)
    changed = False
    for rv in recs:
        old = str(getattr(rv, "text", "") or "")
        new = _bk_ac_correct_text_with_terms(self, old, document_terms)
        if new and new != old:
            try:
                rv.text = new
                changed = True
            except Exception:
                pass
    return changed


def _bk_ac_add_word_to_dictionary(self, word: str, lang: Optional[str] = None):
    word = str(word or "").strip(" \t\r\n.,;:()[]{}<>\"'`´")
    if not word:
        return
    lang = _bk_ac_norm_lang(lang or _bk_ac_current_lang(self))
    existing = _bk_ac_load_user_terms(lang)
    norms = {_bk_autocorrect_norm(w): w for w in existing}
    norm = _bk_autocorrect_norm(word)
    if norm in norms:
        result = QMessageBox.question(
            self,
            self._tr("autocorrect_duplicate_title"),
            self._tr("autocorrect_duplicate_question", word, norms[norm]),
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.No,
        )
        if result == QMessageBox.Cancel:
            return
        if result == QMessageBox.No:
            return
        existing = [w for w in existing if _bk_autocorrect_norm(w) != norm]
    existing.append(word)
    if _bk_ac_write_user_terms(lang, existing):
        try:
            self.status_bar.showMessage(_bk_ac_text(self, "autocorrect_word_added").format(word), 4000)
        except Exception:
            pass
        self._bk_autocorrect_refresh_line_marks()


def _bk_ac_lines_context_menu(self, pos):
    item = self.list_lines.itemAt(pos)
    if item is None:
        return
    row = self.list_lines.row(item)
    errors = item.data(1, BK_AUTOCORRECT_ERRORS_ROLE) or []
    menu = QMenu()
    suggestion_actions: Dict[QAction, Tuple[dict, str]] = {}
    add_word_actions: Dict[QAction, str] = {}
    if errors:
        for err in errors[:5]:
            token = str(err.get("token") or "")
            suggestions = err.get("suggestions") or []
            for suggestion in suggestions[:3]:
                act = menu.addAction(_bk_ac_text(self, "autocorrect_suggestion_entry").format(token, suggestion))
                suggestion_actions[act] = (err, suggestion)
            add_act = menu.addAction(_bk_ac_text(self, "autocorrect_add_word_to_dictionary").format(token))
            add_word_actions[add_act] = token
        menu.addSeparator()
        act_apply_line = menu.addAction(_bk_ac_text(self, "autocorrect_apply_line_suggestions"))
        act_apply_all = menu.addAction(_bk_ac_text(self, "autocorrect_apply_all_lines"))
        menu.addSeparator()
    else:
        act_apply_line = None
        act_apply_all = None
    act_swap = menu.addAction(self._tr("line_menu_swap_with"))
    act_move_up = menu.addAction(self._tr("line_menu_move_up_page"))
    act_move_down = menu.addAction(self._tr("line_menu_move_down_page"))
    menu.addSeparator()
    act_del = menu.addAction(self._tr("line_menu_delete"))
    menu.addSeparator()
    act_add_above = menu.addAction(self._tr("line_menu_add_above"))
    act_add_below = menu.addAction(self._tr("line_menu_add_below"))
    menu.addSeparator()
    act_draw = menu.addAction(self._tr("line_menu_draw_box"))
    chosen = menu.exec(self.list_lines.viewport().mapToGlobal(pos))
    if not chosen:
        return
    if chosen in suggestion_actions:
        err, replacement = suggestion_actions[chosen]
        self._bk_autocorrect_apply_suggestion(row, err, replacement)
        return
    if chosen in add_word_actions:
        self._bk_autocorrect_add_word_to_dictionary(add_word_actions[chosen])
        return
    if act_apply_line is not None and chosen == act_apply_line:
        self._bk_autocorrect_apply_all_current_line(row)
        return
    if act_apply_all is not None and chosen == act_apply_all:
        self._bk_autocorrect_apply_all_visible()
        return
    task = self._current_task()
    if not task or not task.results or task.status != STATUS_DONE:
        return
    if chosen == act_swap:
        self._swap_line_with_dialog(task, row)
    elif chosen == act_move_up:
        rows = self._selected_line_rows() if item.isSelected() else [row]
        self._move_selected_lines(task, rows, -1)
    elif chosen == act_move_down:
        rows = self._selected_line_rows() if item.isSelected() else [row]
        self._move_selected_lines(task, rows, 1)
    elif chosen == act_del:
        self._delete_line(task, row)
    elif chosen == act_add_above:
        self._add_line(task, insert_row=row)
    elif chosen == act_add_below:
        self._add_line(task, insert_row=row + 1)
    elif chosen == act_draw:
        self._pending_new_line_box = False
        self._pending_box_for_row = row
        self.canvas.start_draw_box_mode()


def _bk_ac_duplicates_dialog(parent, duplicates: Dict[str, List[str]]) -> str:
    if not duplicates:
        return "overwrite"
    sample = []
    for values in list(duplicates.values())[:12]:
        sample.append(" / ".join(values[:4]))
    msg = _bk_ac_text(parent, "autocorrect_duplicates_msg").format("\n".join(sample))
    box = QMessageBox(parent)
    box.setWindowTitle(_bk_ac_text(parent, "autocorrect_duplicates_title"))
    box.setText(msg)
    overwrite = box.addButton(_bk_ac_text(parent, "autocorrect_btn_overwrite"), QMessageBox.AcceptRole)
    ignore = box.addButton(_bk_ac_text(parent, "autocorrect_btn_ignore"), QMessageBox.DestructiveRole)
    cancel = box.addButton(_bk_ac_text(parent, "btn_cancel"), QMessageBox.RejectRole)
    box.exec()
    clicked = box.clickedButton()
    if clicked == overwrite:
        return "overwrite"
    if clicked == ignore:
        return "ignore"
    return "cancel"



def _bk_ac_text(owner, key: str, *args) -> str:
    lang = getattr(owner, "current_lang", translation.DEFAULT_LANGUAGE)
    return translation.translate(lang, key, *args)

def _bk_ac_open_revision_settings(self):
    dialog = QDialog(self)
    dialog.setWindowTitle(self._tr("kraken_revision_settings_title"))
    dialog.setMinimumSize(760, 620)
    layout = QVBoxLayout(dialog)
    tabs = QTabWidget(dialog)
    layout.addWidget(tabs, 1)

    revision_tab = QWidget(dialog)
    revision_layout = QVBoxLayout(revision_tab)
    info = QLabel(_bk_ac_text(self, "autocorrect_revision_intro"), revision_tab)
    info.setWordWrap(True)
    revision_layout.addWidget(info)
    editor = QPlainTextEdit(revision_tab)
    editor.setPlaceholderText(self._tr("kraken_revision_replacements_placeholder"))
    editor.setMinimumHeight(160)
    editor.setPlainText(str(getattr(self, "kraken_auto_revision_replacements", "") or self._kraken_auto_revision_default_text()))
    revision_layout.addWidget(editor, 1)
    check = QCheckBox(self._tr("kraken_revision_enable_checkbox"), revision_tab)
    check.setChecked(bool(getattr(self, "kraken_auto_revision_enabled", False)))
    revision_layout.addWidget(check)
    autocorrect_check = QCheckBox(_bk_ac_text(self, "autocorrect_enable_offline_dictionary"), revision_tab)
    autocorrect_check.setChecked(bool(getattr(self, "kraken_autocorrect_enabled", False)))
    revision_layout.addWidget(autocorrect_check)

    ref_state = {
        "dir": str(getattr(self, "kraken_autocorrect_reference_dir", "") or ""),
        "file": str(getattr(self, "kraken_autocorrect_reference_file", "") or ""),
    }
    ref_row = QHBoxLayout()
    ref_label = QLabel(self._tr("kraken_autocorrect_reference_label"), revision_tab)
    ref_file_btn = QPushButton(self._tr("kraken_autocorrect_reference_file_choose"), revision_tab)
    ref_dir_btn = QPushButton(self._tr("kraken_autocorrect_reference_dir_choose"), revision_tab)
    ref_status = QLabel("", revision_tab)
    ref_status.setWordWrap(True)

    def update_reference_status():
        has_file = bool(ref_state.get("file") and os.path.isfile(ref_state.get("file")))
        has_dir = bool(ref_state.get("dir") and os.path.isdir(ref_state.get("dir")))
        if has_file:
            text = self._tr("kraken_autocorrect_reference_selected_file") + " " + os.path.basename(ref_state.get("file"))
        elif has_dir:
            text = self._tr("kraken_autocorrect_reference_selected_dir") + " " + ref_state.get("dir")
        else:
            text = self._tr("kraken_autocorrect_reference_selected_none")
        ref_status.setText(text)

    def choose_reference_file():
        start_dir = os.path.expanduser("~")
        if ref_state.get("file") and os.path.isfile(ref_state.get("file")):
            start_dir = os.path.dirname(ref_state.get("file"))
        chosen, _flt = QFileDialog.getOpenFileName(dialog, self._tr("kraken_autocorrect_reference_file_title"), start_dir, self._tr("kraken_autocorrect_reference_file_filter"))
        if chosen:
            ref_state["file"] = chosen
            ref_state["dir"] = ""
            update_reference_status()

    def choose_reference_dir():
        start_dir = ref_state.get("dir") if ref_state.get("dir") and os.path.isdir(ref_state.get("dir")) else os.path.expanduser("~")
        chosen = QFileDialog.getExistingDirectory(dialog, self._tr("kraken_autocorrect_reference_dir_title"), start_dir)
        if chosen:
            ref_state["dir"] = chosen
            ref_state["file"] = ""
            update_reference_status()

    ref_file_btn.clicked.connect(choose_reference_file)
    ref_dir_btn.clicked.connect(choose_reference_dir)
    ref_row.addWidget(ref_label)
    ref_row.addWidget(ref_file_btn)
    ref_row.addWidget(ref_dir_btn)
    ref_row.addStretch(1)
    revision_layout.addLayout(ref_row)
    update_reference_status()
    revision_layout.addWidget(ref_status)
    ref_hint = QLabel(self._tr("kraken_autocorrect_reference_dir_hint"), revision_tab)
    ref_hint.setWordWrap(True)
    revision_layout.addWidget(ref_hint)
    tabs.addTab(revision_tab, _bk_ac_text(self, "btn_autocorrect_settings"))

    dict_tab = QWidget(dialog)
    dict_layout = QVBoxLayout(dict_tab)
    dict_intro = QLabel(_bk_ac_text(self, "autocorrect_dictionary_intro"), dict_tab)
    dict_intro.setWordWrap(True)
    dict_layout.addWidget(dict_intro)
    lang_row = QHBoxLayout()
    lang_combo = QComboBox(dict_tab)
    current_lang = _bk_ac_current_lang(self)
    for code in _bk_ac_available_langs():
        lang_combo.addItem(_bk_ac_display_language_name(code, current_lang), code)
    try:
        lang_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        longest = max([lang_combo.itemText(i) for i in range(lang_combo.count())] or [""])
        lang_combo.setMinimumWidth(lang_combo.fontMetrics().horizontalAdvance(longest + "  ") + 36)
    except Exception:
        pass
    for idx in range(lang_combo.count()):
        if lang_combo.itemData(idx) == current_lang:
            lang_combo.setCurrentIndex(idx)
            break
    user_editor = QPlainTextEdit(dict_tab)
    user_editor.setPlaceholderText(_bk_ac_text(self, "autocorrect_user_dictionary_placeholder"))
    builtin_view = QPlainTextEdit(dict_tab)
    builtin_view.setReadOnly(True)
    builtin_view.setMinimumHeight(140)
    path_label = QLabel("", dict_tab)
    path_label.setWordWrap(True)
    open_dictionary_folder_btn = QPushButton(_bk_ac_text(self, "autocorrect_open_dictionary_folder"), dict_tab)
    def open_dictionary_folder():
        _bk_ac_open_directory(_bk_ac_user_dir())
    open_dictionary_folder_btn.clicked.connect(open_dictionary_folder)
    staged_user_terms: Dict[str, str] = {}
    active_lang = {"value": _bk_ac_norm_lang(lang_combo.currentData())}

    def normalize_editor_text(raw: str) -> Tuple[List[str], Dict[str, List[str]]]:
        parts = [p.strip(" \t\r\n.,;:()[]{}<>\"'`´") for p in re.split(r"[\s,;_]+", raw or "")]
        parts = [p for p in parts if p and re.search(r"[A-Za-zÄÖÜäöüßÀ-ÿ]", p)]
        return _bk_ac_dedupe_terms(parts)

    def snapshot_active_lang() -> bool:
        lang = _bk_ac_norm_lang(active_lang.get("value"))
        clean, duplicates = normalize_editor_text(user_editor.toPlainText())
        if duplicates:
            choice = _bk_ac_duplicates_dialog(dialog, duplicates)
            if choice == "cancel":
                return False
            if choice == "ignore":
                return True
        staged_user_terms[lang] = "\n".join(clean)
        if user_editor.toPlainText().strip() != staged_user_terms[lang].strip():
            user_editor.setPlainText(staged_user_terms[lang])
        return True

    def load_lang_fields():
        lang = _bk_ac_norm_lang(lang_combo.currentData())
        active_lang["value"] = lang
        if lang not in staged_user_terms:
            staged_user_terms[lang] = "\n".join(_bk_ac_load_user_terms(lang))
        user_editor.setPlainText(staged_user_terms.get(lang, ""))
        builtin_terms = _bk_ac_load_builtin_terms(lang)
        store = _bk_ac_store_for(lang)
        ready_store = _bk_ac_ensure_store_ready(self, store)
        extended = ready_store.term_count() if ready_store is not None else 0
        preview = builtin_terms[:5000]
        stats = _bk_ac_text(self, "autocorrect_dictionary_stats").format(len(builtin_terms), extended)
        builtin_view.setPlainText(stats + "\n" + ("-" * 60) + "\n" + "\n".join(preview))
        path_label.setText(_bk_ac_text(self, "autocorrect_user_dictionary_file") + " " + _bk_ac_user_path(lang))

    def on_lang_changed(_idx: int):
        old_lang = _bk_ac_norm_lang(active_lang.get("value"))
        clean, duplicates = normalize_editor_text(user_editor.toPlainText())
        if duplicates:
            choice = _bk_ac_duplicates_dialog(dialog, duplicates)
            if choice == "cancel":
                for idx in range(lang_combo.count()):
                    if lang_combo.itemData(idx) == old_lang:
                        try:
                            lang_combo.blockSignals(True)
                            lang_combo.setCurrentIndex(idx)
                        finally:
                            lang_combo.blockSignals(False)
                        return
            elif choice == "ignore":
                clean = [line.strip() for line in user_editor.toPlainText().splitlines() if line.strip()]
        staged_user_terms[old_lang] = "\n".join(clean)
        load_lang_fields()

    lang_combo.currentIndexChanged.connect(on_lang_changed)
    lang_row.addWidget(QLabel(_bk_ac_text(self, "label_language")+"", dict_tab))
    lang_row.addWidget(lang_combo)
    lang_row.addStretch(1)
    dict_layout.addLayout(lang_row)
    dict_layout.addWidget(QLabel(_bk_ac_text(self, "autocorrect_user_dictionary_label"), dict_tab))
    dict_layout.addWidget(user_editor, 2)
    path_row = QHBoxLayout()
    path_row.addWidget(path_label, 1)
    path_row.addWidget(open_dictionary_folder_btn, 0)
    dict_layout.addLayout(path_row)
    dict_layout.addWidget(QLabel(_bk_ac_text(self, "autocorrect_embedded_dictionary_label"), dict_tab))
    dict_layout.addWidget(builtin_view, 1)
    load_lang_fields()

    # Während des einmaligen SQLite-Aufbaus bleibt der Dialog bedienbar. Sobald
    # der Index fertig ist, wird die angezeigte Zahl automatisch von 0 auf den
    # tatsächlichen Bestand aktualisiert, ohne dass der Dialog neu geöffnet
    # werden muss.
    try:
        from PySide6.QtCore import QTimer

        stats_state = {"lang": "", "count": -1}
        dictionary_stats_timer = QTimer(dialog)
        dictionary_stats_timer.setInterval(500)

        def _poll_dictionary_stats():
            lang = _bk_ac_norm_lang(lang_combo.currentData())
            store = _bk_ac_store_for(lang)
            if store is None:
                return
            ready_store = _bk_ac_ensure_store_ready(self, store)
            if ready_store is None:
                return
            count = ready_store.term_count()
            if stats_state.get("lang") == lang and stats_state.get("count") == count:
                return
            stats_state["lang"] = lang
            stats_state["count"] = count
            lines = builtin_view.toPlainText().splitlines()
            builtin_count = len(_bk_ac_load_builtin_terms(lang))
            stats = _bk_ac_text(self, "autocorrect_dictionary_stats").format(
                builtin_count, count
            )
            if lines:
                lines[0] = stats
                builtin_view.setPlainText("\n".join(lines))
            else:
                builtin_view.setPlainText(stats)

        dictionary_stats_timer.timeout.connect(_poll_dictionary_stats)
        dictionary_stats_timer.start()
        dialog._bk_dictionary_stats_timer = dictionary_stats_timer
    except Exception:
        pass

    tabs.addTab(dict_tab, _bk_ac_text(self, "autocorrect_dictionary_tab"))

    buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, dialog)
    try:
        save_btn = buttons.button(QDialogButtonBox.Save)
        cancel_btn = buttons.button(QDialogButtonBox.Cancel)
        if save_btn is not None:
            save_btn.setText(_bk_ac_text(self, "btn_save"))
            if hasattr(self, "_tinted_theme_or_standard_icon"):
                save_btn.setIcon(self._tinted_theme_or_standard_icon("document-save", QStyle.SP_DialogSaveButton))
        if cancel_btn is not None:
            cancel_btn.setText(_bk_ac_text(self, "btn_cancel"))
            if hasattr(self, "_tinted_theme_or_standard_icon"):
                cancel_btn.setIcon(self._tinted_theme_or_standard_icon("dialog-cancel", QStyle.SP_DialogCancelButton))
    except Exception:
        pass
    reset_btn = buttons.addButton(self._tr("kraken_revision_reset_defaults"), QDialogButtonBox.ResetRole)
    reset_btn.clicked.connect(lambda: editor.setPlainText(self._kraken_auto_revision_default_text()))
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    if dialog.exec() != QDialog.Accepted:
        return
    if not snapshot_active_lang():
        return
    for lang_key, raw_text in list(staged_user_terms.items()):
        clean_terms, duplicates = normalize_editor_text(raw_text)
        if duplicates:
            choice = _bk_ac_duplicates_dialog(self, duplicates)
            if choice == "cancel":
                return
            if choice == "ignore":
                continue
        _bk_ac_write_user_terms(lang_key, clean_terms)
    text = editor.toPlainText().strip() or self._kraken_auto_revision_default_text()
    self.kraken_auto_revision_replacements = text
    self.kraken_auto_revision_enabled = bool(check.isChecked())
    self.kraken_autocorrect_enabled = bool(autocorrect_check.isChecked())
    selected_file = str(ref_state.get("file") or "").strip()
    selected_dir = str(ref_state.get("dir") or "").strip()
    if selected_file and os.path.isfile(selected_file):
        selected_dir = ""
    self.kraken_autocorrect_reference_dir = selected_dir
    self.kraken_autocorrect_reference_file = selected_file
    try:
        self.settings.setValue("ocr/auto_revision_replacements", text)
        self.settings.setValue("ocr/auto_revision_enabled", "true" if self.kraken_auto_revision_enabled else "false")
        self.settings.setValue("ocr/autocorrect_enabled", "true" if self.kraken_autocorrect_enabled else "false")
        self.settings.setValue("ocr/autocorrect_reference_dir", self.kraken_autocorrect_reference_dir)
        self.settings.setValue("ocr/autocorrect_reference_file", self.kraken_autocorrect_reference_file)
    except Exception:
        pass
    try:
        task = self._current_task() if hasattr(self, "_current_task") else None
        if bool(getattr(self, "kraken_autocorrect_enabled", False)) and task and task.results:
            _text, _kr_records, _im, recs = task.results
            if _bk_ac_apply_document_autocorrect_to_recs(self, recs):
                task.results = ("\n".join(rv.text for rv in recs).strip(), _kr_records, _im, recs)
                task.edited = True
                if hasattr(self, "_sync_ui_after_recs_change"):
                    self._sync_ui_after_recs_change(task, keep_row=getattr(self.list_lines, "currentRow", lambda: 0)())
    except Exception:
        pass
    try:
        self._bk_autocorrect_refresh_line_marks()
    except Exception:
        pass


def _install_autocorrect_feature():
    if MainWindow is None or getattr(MainWindow, "_bk_autocorrect_offline_installed", False):
        return
    MainWindow._bk_autocorrect_offline_installed = True
    MainWindow._bk_autocorrect_install_delegate = _bk_ac_install_delegate
    MainWindow._bk_autocorrect_refresh_line_marks = _bk_ac_refresh_line_marks
    MainWindow._bk_autocorrect_apply_suggestion = _bk_ac_apply_suggestion
    MainWindow._bk_autocorrect_apply_all_current_line = _bk_ac_apply_all_current_line
    MainWindow._bk_autocorrect_apply_all_visible = _bk_ac_apply_all_visible
    MainWindow._bk_autocorrect_add_word_to_dictionary = _bk_ac_add_word_to_dictionary
    MainWindow._bk_autocorrect_apply_document_to_recs = _bk_ac_apply_document_autocorrect_to_recs
    original_reference_terms = getattr(MainWindow, "_kraken_autocorrect_reference_terms", None)
    if original_reference_terms is not None:
        MainWindow._bk_original_kraken_autocorrect_reference_terms = original_reference_terms
    MainWindow._kraken_autocorrect_reference_terms = _bk_ac_all_terms
    MainWindow._open_kraken_auto_revision_settings = _bk_ac_open_revision_settings
    MainWindow.lines_context_menu = _bk_ac_lines_context_menu

    def patched_init(self, *args, **kwargs):
        # Die Woerterbuch-Spiegelung (bis ~105 MB beim Erststart) laeuft im
        # Hintergrund-Thread statt auf dem GUI-Thread - der Programmstart
        # blockiert dadurch nicht mehr sichtbar. Spaetere On-Demand-Zugriffe
        # rufen den Sync ohnehin erneut auf (manifest-geprüft, dann billig)
        # und werden ueber _BK_AC_SYNC_LOCK sauber serialisiert.
        sync_state = {"finished": False}

        def _sync_worker():
            try:
                _bk_ac_sync_runtime_dictionaries()
            finally:
                sync_state["finished"] = True

        try:
            sync_thread = threading.Thread(
                target=_sync_worker, name="bk-dict-sync", daemon=True
            )
            self._bk_autocorrect_dictionary_sync_thread = sync_thread
            sync_thread.start()
        except Exception:
            sync_state["finished"] = True

        try:
            self._bk_autocorrect_install_delegate()
        except Exception:
            pass

        # Nach dem erstmaligen Spiegeln der Onefile-Ressourcen muss die Engine
        # erneut angestoßen werden. Früher blieb sie bis zu einer anderen UI-
        # Aktion im 476-Wörter-RAM-Modus, weil beim ersten Refresh die große
        # JSON-Datei noch nicht im persistenten Benutzerordner lag.
        try:
            from PySide6.QtCore import QTimer

            sync_timer = QTimer(self)
            sync_timer.setInterval(400)

            def _poll_dictionary_sync():
                if not sync_state.get("finished", False):
                    return
                sync_timer.stop()
                sync_timer.deleteLater()
                _BK_AC_ENGINE_CACHE.clear()
                try:
                    self._bk_autocorrect_refresh_line_marks()
                except Exception:
                    pass

            sync_timer.timeout.connect(_poll_dictionary_sync)
            sync_timer.start()
            self._bk_autocorrect_dictionary_sync_timer = sync_timer
        except Exception:
            pass
    from bottled_kraken.common.chain_consolidation import register_init_delta
    register_init_delta(patched_init)


    original_on_file_done = getattr(MainWindow, "on_file_done", None)
    if original_on_file_done is not None:
        def patched_on_file_done(self, path, text, kr_records, im, recs):
            result = original_on_file_done(self, path, text, kr_records, im, recs)
            try:
                item = next((i for i in getattr(self, "queue_items", []) if i.path == path), None)
                if item and item.results and bool(getattr(self, "kraken_autocorrect_enabled", False)):
                    _text, _kr_records, _im, current_recs = item.results
                    if _bk_ac_apply_document_autocorrect_to_recs(self, current_recs):
                        item.results = ("\n".join(rv.text for rv in current_recs).strip(), _kr_records, _im, current_recs)
                        try:
                            cur_path = self.queue_table.item(self.queue_table.currentRow(), QUEUE_COL_FILE).data(Qt.UserRole) if self.queue_table.currentRow() >= 0 else None
                        except Exception:
                            cur_path = None
                        if cur_path == path and hasattr(self, "load_results"):
                            self.load_results(path)
                        try:
                            self._bk_autocorrect_refresh_line_marks()
                        except Exception:
                            pass
            except Exception:
                pass
            return result
        MainWindow.on_file_done = patched_on_file_done

    original_populate = getattr(MainWindow, "_populate_lines_list", None)
    if original_populate is not None:
        def patched_populate(self, *args, **kwargs):
            result = original_populate(self, *args, **kwargs)
            try:
                self._bk_autocorrect_refresh_line_marks()
            except Exception:
                pass
            return result
        MainWindow._populate_lines_list = patched_populate


_install_autocorrect_feature()

__all__ = [
    "BK_AUTOCORRECT_ERRORS_ROLE",
    "BK_AUTOCORRECT_TEXT_ROLE",
    "BKAutocorrectUnderlineDelegate",
]
