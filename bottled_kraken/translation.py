from __future__ import annotations
import copy
from typing import Dict, List
from bottled_kraken.translations.language_registry import (
    DEFAULT_LANGUAGE,
    FALLBACK_LANGUAGES,
    available_language_codes,
    language_info,
    normalize_language_code,
)
from bottled_kraken.translations.translation_loader import (
    load_all_language_translations,
    load_named_language_mapping,
    load_translation_sections,
)
class translation:
    DEFAULT_LANGUAGE = DEFAULT_LANGUAGE
    FALLBACK_LANGUAGES = FALLBACK_LANGUAGES
    BASE_TRANSLATIONS = load_all_language_translations()
    ADDITIONAL_TRANSLATIONS = load_named_language_mapping("additional_translations", "ADDITIONAL_TRANSLATIONS")
    BK_LM_WAIT_TEXT_TRANSLATIONS = load_named_language_mapping("lm_wait_texts", "BK_LM_WAIT_TEXT_TRANSLATIONS")
    BK_LM_DROPDOWN_TRANSLATIONS = load_named_language_mapping("lm_dropdown_texts", "BK_LM_DROPDOWN_TRANSLATIONS")
    BK_LM_DB_JSON_PATCH9_TRANSLATIONS = load_named_language_mapping("lm_db_json_texts", "BK_LM_DB_JSON_PATCH9_TRANSLATIONS")
    BK_PATCH10_TRANSLATIONS = load_named_language_mapping("local_json_progress_texts", "BK_PATCH10_TRANSLATIONS")
    BK_PATCH11_TRANSLATIONS = load_named_language_mapping("local_json_wait_texts", "BK_PATCH11_TRANSLATIONS")
    BK_PATCH12_TRANSLATIONS = load_named_language_mapping("local_json_notice_texts", "BK_PATCH12_TRANSLATIONS")
    BK_UNIFIED_TRANSLATIONS = load_named_language_mapping("unified_texts", "BK_UNIFIED_TRANSLATIONS")
    BK_PATCH24B_TRANSLATIONS = load_named_language_mapping("person_table_ai_notice_texts", "BK_PATCH24B_TRANSLATIONS")
    BK_LM_OCR_TRANSLATIONS = load_named_language_mapping("lm_ocr_texts", "BK_LM_OCR_TRANSLATIONS")
    BK_LM_OPTIONS_TRANSLATIONS = load_named_language_mapping("lm_options_texts", "BK_LM_OPTIONS_TRANSLATIONS")
    BK_GEDCOM_TRANSLATIONS = load_named_language_mapping("gedcom_texts", "BK_GEDCOM_TRANSLATIONS")
    MERGE_ORDER = load_translation_sections()
    @classmethod
    def available_languages(cls) -> List[str]:
        return available_language_codes()
    @classmethod
    def normalize_language_code(cls, lang: object) -> str:
        return normalize_language_code(lang, cls.DEFAULT_LANGUAGE)
    @classmethod
    def build_translations(cls) -> Dict[str, Dict[str, str]]:
        data = copy.deepcopy(load_all_language_translations())
        fallback_chain = [code for code in cls.FALLBACK_LANGUAGES if code in data]
        for lang, values in list(data.items()):
            for fallback_lang in fallback_chain:
                if fallback_lang == lang:
                    continue
                for key, value in data.get(fallback_lang, {}).items():
                    values.setdefault(key, value)
        return data
    @classmethod
    def translate(cls, lang: str, key: str, *args):
        lang = cls.normalize_language_code(lang)
        txt = cls.TRANSLATIONS.get(lang, {}).get(key)
        if txt is None:
            for fallback_lang in cls.FALLBACK_LANGUAGES:
                txt = cls.TRANSLATIONS.get(fallback_lang, {}).get(key)
                if txt is not None:
                    break
        if txt is None:
            txt = key
        return txt.format(*args) if args else txt
    @classmethod
    def language_display_name(cls, code: str, ui_lang: str | None = None) -> str:
        code = cls.normalize_language_code(code)
        ui_lang = cls.normalize_language_code(ui_lang or code)
        key = f"lang_{code}"
        label = cls.TRANSLATIONS.get(ui_lang, {}).get(key)
        if label and label != key:
            return label
        label = cls.TRANSLATIONS.get(code, {}).get(key)
        if label and label != key:
            return label
        return language_info(code).get("native_name", code)
    @classmethod
    def make_tr(cls, lang: str):
        normalized = cls.normalize_language_code(lang)
        return lambda key, *args: cls.translate(normalized, key, *args)
translation.TRANSLATIONS = translation.build_translations()
TRANSLATIONS = translation.TRANSLATIONS
Translation = translation
__all__ = ["translation", "Translation", "TRANSLATIONS"]
