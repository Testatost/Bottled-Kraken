from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
"""GEDCOM-Erzeugung über lokales LM.
Ergänzt im LM-Überarbeitungsmenü den Eintrag "GEDCOM erzeugen" unterhalb
von "Neo4j-JSON erzeugen" und bindet die GEDCOM-Prompts in den bestehenden
Prompt-Editor ein.
"""
from bottled_kraken.translations.translation_loader import load_named_language_mapping as _load_translation_mapping
_BK_GEDCOM_PROMPT_DEFAULTS = _load_translation_mapping("gedcom_texts", "BK_GEDCOM_PROMPT_DEFAULTS")
_BK_GEDCOM_VISION_TEXTS = _load_translation_mapping("gedcom_texts", "BK_GEDCOM_VISION_TEXTS")
_BK_GEDCOM_SAVE_FIX_TEXTS = _load_translation_mapping("gedcom_texts", "BK_GEDCOM_SAVE_FIX_TEXTS")
_BK_GEDCOM_ROBUST_TEXTS = _load_translation_mapping("gedcom_texts", "BK_GEDCOM_ROBUST_TEXTS")
_BK_GEDCOM_STRUCTURED_TEXTS = _load_translation_mapping("gedcom_texts", "BK_GEDCOM_STRUCTURED_TEXTS")
_BK_GEDCOM_REVIEW_TEXTS = _load_translation_mapping("gedcom_texts", "BK_GEDCOM_REVIEW_TEXTS")
_BK_PROMPT_UX_EXTRA_TEXTS = _load_translation_mapping("gedcom_texts", "BK_PROMPT_UX_EXTRA_TEXTS")
def _bk_gedcom_install_translations():
    for lang, mapping in _BK_GEDCOM_PROMPT_DEFAULTS.items():
        try:
            translation.TRANSLATIONS.setdefault(lang, {}).update(mapping)
        except Exception:
            try:
                TRANSLATIONS.setdefault(lang, {}).update(mapping)
            except Exception:
                pass
    try:
        existing_prompt_keys = [k for k, _label in _BK_LM_PROMPT_KEYS]
        extra = []
        if "ai_prompt_gedcom_system" not in existing_prompt_keys:
            extra.append(("ai_prompt_gedcom_system", "lm_prompt_gedcom_system"))
        if "ai_prompt_gedcom_user" not in existing_prompt_keys:
            extra.append(("ai_prompt_gedcom_user", "lm_prompt_gedcom_user"))
        if extra:
            globals()["_BK_LM_PROMPT_KEYS"] = tuple(_BK_LM_PROMPT_KEYS) + tuple(extra)
    except Exception:
        pass
    try:
        existing_token_keys = [k for k, _label in _BK_LM_TOKEN_KEYS]
        if "gedcom" not in existing_token_keys:
            globals()["_BK_LM_TOKEN_KEYS"] = tuple(_BK_LM_TOKEN_KEYS) + (("gedcom", "lm_token_gedcom"),)
    except Exception:
        pass
    try:
        _BK_LM_TOKEN_DEFAULTS.setdefault("gedcom", 4500)
    except Exception:
        pass
    try:
        for lang, mapping in _BK_GEDCOM_PROMPT_DEFAULTS.items():
            if "_BK_LM_OPTIONS_TEXTS" in globals():
                _BK_LM_OPTIONS_TEXTS.setdefault(lang, {}).update({
                    "lm_token_gedcom": mapping["act_lm_generate_gedcom"],
                    "lm_prompt_gedcom_system": mapping["lm_prompt_gedcom_system"],
                    "lm_prompt_gedcom_user": mapping["lm_prompt_gedcom_user"],
                })
    except Exception:
        pass
def _bk_gedcom_text(self, key: str, *args) -> str:
    lang = getattr(self, "current_lang", translation.DEFAULT_LANGUAGE)
    return translation.translate(lang, key, *args)
__all__ = [
    '_BK_GEDCOM_PROMPT_DEFAULTS',
    '_BK_GEDCOM_REVIEW_TEXTS',
    '_BK_GEDCOM_ROBUST_TEXTS',
    '_BK_GEDCOM_SAVE_FIX_TEXTS',
    '_BK_GEDCOM_STRUCTURED_TEXTS',
    '_BK_GEDCOM_VISION_TEXTS',
    '_BK_PROMPT_UX_EXTRA_TEXTS',
    '_bk_gedcom_install_translations',
    '_bk_gedcom_text',
]
register_globals('bk', globals(), __all__)
