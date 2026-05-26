"""Optionen für lokale LM-Token und lokale KI-Prompts.

Diese späte Patch-Datei ergänzt unter "Optionen" zwei Dialoge:
- Token-Anzahl für lokale LM-Funktionen
- Prompt-Editor für lokale KI-Prompts

Außerdem wird im Hinweise-Dialog der erste Bereich von "Ablauf" zu
"Übersicht" umbenannt.
"""

_BK_LM_TOKEN_DEFAULTS = {
    "current_line": 1200,
    "selected_lines": 1200,
    "all_lines": 1200,
    "lm_ocr": 4500,
    "lm_ocr_boxes": 4500,
    "postgresql_json": 9000,
    "neo4j_json": 9000,
    "sqlite_json": 9000,
    "gedcom": 6000,
    "canonical": 9000,
}

_BK_LM_TOKEN_KEYS = (
    ("current_line", "lm_token_current_line"),
    ("selected_lines", "lm_token_selected_lines"),
    ("all_lines", "lm_token_all_lines"),
    ("lm_ocr", "lm_token_lm_ocr"),
    ("lm_ocr_boxes", "lm_token_lm_ocr_boxes"),
    ("postgresql_json", "lm_token_postgresql_json"),
    ("neo4j_json", "lm_token_neo4j_json"),
    ("sqlite_json", "lm_token_sqlite_json"),
    ("gedcom", "lm_token_gedcom"),
    ("canonical", "lm_token_canonical"),
)

_BK_LM_PROMPT_KEYS = (
    ("ai_prompt_single_system", "lm_prompt_single_system"),
    ("ai_prompt_single_user", "lm_prompt_single_user"),
    ("ai_prompt_block_system", "lm_prompt_block_system"),
    ("ai_prompt_block_user", "lm_prompt_block_user"),
    ("ai_prompt_page_system", "lm_prompt_page_system"),
    ("ai_prompt_page_user", "lm_prompt_page_user"),
    ("ai_prompt_decision_system", "lm_prompt_decision_system"),
    ("ai_prompt_decision_user", "lm_prompt_decision_user"),
    ("ai_prompt_fullpage_lm_ocr_system", "lm_prompt_fullpage_ocr_system"),
    ("ai_prompt_fullpage_lm_ocr_user", "lm_prompt_fullpage_ocr_user"),
    ("ai_prompt_page_boxes_align_system", "lm_prompt_page_boxes_align_system"),
    ("ai_prompt_page_boxes_align_user", "lm_prompt_page_boxes_align_user"),
    ("ai_prompt_gedcom_system", "lm_prompt_gedcom_system"),
    ("ai_prompt_gedcom_user", "lm_prompt_gedcom_user"),
    ("ai_prompt_canonical_system", "lm_prompt_canonical_system"),
    ("ai_prompt_canonical_user", "lm_prompt_canonical_user"),
    ("ai_prompt_postgresql_system", "lm_prompt_postgresql_system"),
    ("ai_prompt_postgresql_user", "lm_prompt_postgresql_user"),
    ("ai_prompt_neo4j_system", "lm_prompt_neo4j_system"),
    ("ai_prompt_neo4j_user", "lm_prompt_neo4j_user"),
    ("ai_prompt_sqlite_system", "lm_prompt_sqlite_system"),
    ("ai_prompt_sqlite_user", "lm_prompt_sqlite_user"),
)

from .translation_sections.lm_options_texts import BK_LM_OPTIONS_TRANSLATIONS as _BK_LM_OPTIONS_TEXTS

def _bk_lm_opt_text(self, key: str, *args) -> str:
    lang = getattr(self, "current_lang", translation.DEFAULT_LANGUAGE)
    data = _BK_LM_OPTIONS_TEXTS.get(lang) or _BK_LM_OPTIONS_TEXTS["de"]
    txt = data.get(key, _BK_LM_OPTIONS_TEXTS["de"].get(key, key))
    try:
        return txt.format(*args) if args else txt
    except Exception:
        return txt

def _bk_lm_token_settings_key(kind: str) -> str:
    return f"lm_tokens/{kind}"

def _bk_lm_prompt_settings_key(lang: str, key: str) -> str:
    return f"lm_prompts/{lang}/{key}"

def _bk_lm_custom_context_settings_key() -> str:
    return "lm_prompts/custom_context"

def _bk_lm_default_prompt(lang: str, key: str) -> str:
    lang = translation.normalize_language_code(lang)
    if key in translation.TRANSLATIONS.get(lang, {}):
        return str(translation.TRANSLATIONS[lang].get(key, ""))
    return str(translation.TRANSLATIONS.get(translation.DEFAULT_LANGUAGE, {}).get(key, key))

def _bk_lm_prompt_override(self, key: str) -> str:
    if key not in {k for k, _label in _BK_LM_PROMPT_KEYS}:
        return ""
    settings = getattr(self, "settings", None)
    if settings is None:
        return ""
    lang = getattr(self, "current_lang", translation.DEFAULT_LANGUAGE)
    try:
        value = settings.value(_bk_lm_prompt_settings_key(lang, key), "", str)
    except Exception:
        value = ""
    return str(value or "")

def _bk_lm_load_custom_context(self):
    settings = getattr(self, "settings", None)
    value = ""
    if settings is not None:
        try:
            value = settings.value(_bk_lm_custom_context_settings_key(), "", str)
        except Exception:
            value = ""
    self.lm_custom_context = str(value or "")

def _bk_lm_custom_context(self) -> str:
    if not hasattr(self, "lm_custom_context"):
        _bk_lm_load_custom_context(self)
    return str(getattr(self, "lm_custom_context", "") or "")

def _bk_lm_apply_custom_context(self, key: str, text: str) -> str:
    if key not in {k for k, _label in _BK_LM_PROMPT_KEYS}:
        return text
    if not str(key).endswith("_user"):
        return text
    ctx = _bk_lm_custom_context(self).strip()
    if not ctx:
        return text
    appendix = _bk_lm_opt_text(self, "lm_custom_context_appendix", ctx)
    return f"{str(text).rstrip()}\n\n{appendix}"

def _bk_lm_load_token_settings(self):
    defaults = dict(_BK_LM_TOKEN_DEFAULTS)
    try:
        base = int(getattr(self, "ai_max_tokens", 1200) or 1200)
    except Exception:
        base = 1200
    defaults["current_line"] = base
    defaults["selected_lines"] = base
    defaults["all_lines"] = base
    defaults["lm_ocr"] = 4500
    defaults["lm_ocr_boxes"] = 4500
    defaults["postgresql_json"] = 9000
    defaults["neo4j_json"] = 9000
    defaults["sqlite_json"] = 9000
    defaults["gedcom"] = 6000
    defaults["canonical"] = 9000

    self.lm_token_limits = {}
    settings = getattr(self, "settings", None)
    for kind, default in defaults.items():
        value = default
        if settings is not None:
            try:
                value = int(settings.value(_bk_lm_token_settings_key(kind), default, int))
            except Exception:
                value = default
        self.lm_token_limits[kind] = max(1, int(value))

def _lm_token_limit(self, kind: str) -> int:
    if not hasattr(self, "lm_token_limits"):
        _bk_lm_load_token_settings(self)
    kind = str(kind or "all_lines")
    if kind not in self.lm_token_limits:
        kind = "all_lines"
    try:
        return max(1, int(self.lm_token_limits.get(kind) or _BK_LM_TOKEN_DEFAULTS.get(kind, 1200)))
    except Exception:
        return int(_BK_LM_TOKEN_DEFAULTS.get(kind, 1200))


def _bk_lm_token_kind_for_json(schema_kind: str) -> str:
    kind = str(schema_kind or "postgres").strip().lower()
    if kind == "neo4j":
        return "neo4j_json"
    if kind == "sqlite":
        return "sqlite_json"
    return "postgresql_json"


def _bk_lm_token_limit_for_json(self, schema_kind: str) -> int:
    return _lm_token_limit(self, _bk_lm_token_kind_for_json(schema_kind))
