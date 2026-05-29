from __future__ import annotations
import copy
import importlib
import pkgutil
from typing import Dict, Iterable, List, Mapping
from bottled_kraken.translations.language_registry import available_language_codes
LANGUAGE_MODULE_ORDER = [
    "common_actions_and_buttons",
    "ai_prompt_texts",
    "ai_revision_and_dialog_texts",
    "core_ui_texts",
    "help_privacy_and_legal_texts",
    "image_edit_texts",
    "image_edit_and_navigation_texts",
    "legal_and_ai_prompt_tail",
    "lm_help_and_ssh_texts",
    "voice_swap_and_batch_texts",
    "additional_translations",
    "lm_wait_texts",
    "lm_dropdown_texts",
    "lm_db_json_texts",
    "local_json_progress_texts",
    "local_json_wait_texts",
    "local_json_notice_texts",
    "unified_texts",
    "person_table_ai_notice_texts",
    "lm_ocr_texts",
    "lm_options_texts",
    "gedcom_texts",
    "runtime_ui_texts",
]
PATCH_MODULE_OUTPUTS = {
    "additional_translations": ["ADDITIONAL_TRANSLATIONS"],
    "lm_wait_texts": ["BK_LM_WAIT_TEXT_TRANSLATIONS"],
    "lm_dropdown_texts": ["BK_LM_DROPDOWN_TRANSLATIONS"],
    "lm_db_json_texts": ["BK_LM_DB_JSON_PATCH9_TRANSLATIONS"],
    "local_json_progress_texts": ["BK_PATCH10_TRANSLATIONS"],
    "local_json_wait_texts": ["BK_PATCH11_TRANSLATIONS"],
    "local_json_notice_texts": ["BK_PATCH12_TRANSLATIONS"],
    "unified_texts": ["BK_UNIFIED_TRANSLATIONS"],
    "person_table_ai_notice_texts": ["BK_PATCH24B_TRANSLATIONS"],
    "lm_ocr_texts": ["BK_LM_OCR_TRANSLATIONS"],
    "lm_options_texts": ["BK_LM_OPTIONS_TRANSLATIONS"],
    "gedcom_texts": [
        "BK_GEDCOM_PROMPT_DEFAULTS",
        "BK_GEDCOM_VISION_TEXTS",
        "BK_GEDCOM_SAVE_FIX_TEXTS",
        "BK_GEDCOM_ROBUST_TEXTS",
        "BK_GEDCOM_STRUCTURED_TEXTS",
        "BK_GEDCOM_REVIEW_TEXTS",
        "BK_PROMPT_UX_EXTRA_TEXTS",
        "BK_GEDCOM_TRANSLATIONS",
    ],
}
def _package_name() -> str:
    return __package__ or "bottled_kraken.translations"
def _is_flat_translation_dict(value: object) -> bool:
    return isinstance(value, dict) and all(
        isinstance(key, str) and not isinstance(item, dict)
        for key, item in value.items()
    )
def _language_module_names(language: str) -> List[str]:
    try:
        package = importlib.import_module(f"{_package_name()}.{language}")
    except Exception:
        return []
    discovered: list[str] = []
    try:
        package_path = getattr(package, "__path__", None)
        if package_path is not None:
            discovered = [
                item.name for item in pkgutil.iter_modules(package_path)
                if not item.name.startswith("_") and item.name != "language_info"
            ]
    except Exception:
        discovered = []
    if not discovered:
        discovered = list(LANGUAGE_MODULE_ORDER)
    order_index = {name: index for index, name in enumerate(LANGUAGE_MODULE_ORDER)}
    return sorted(dict.fromkeys(discovered), key=lambda name: (order_index.get(name, 10_000), name))
def _dicts_from_module(module: object) -> Iterable[dict]:
    for name, value in vars(module).items():
        if name.isupper() and _is_flat_translation_dict(value):
            yield value
def load_language_translations(language: str) -> Dict[str, str]:
    data: Dict[str, str] = {}
    for module_name in _language_module_names(language):
        try:
            module = importlib.import_module(f"{_package_name()}.{language}.{module_name}")
        except Exception:
            continue
        for mapping in _dicts_from_module(module):
            data.update(copy.deepcopy(mapping))
    return data
def load_all_language_translations() -> Dict[str, Dict[str, str]]:
    return {code: load_language_translations(code) for code in available_language_codes()}
def _matches_named_mapping(name: str, logical_name: str, language: str) -> bool:
    suffix = "_" + language.upper()
    if name == logical_name:
        return True
    if name == logical_name + suffix:
        return True
    return name.endswith(suffix) and name[:-len(suffix)] == logical_name
def load_named_language_mapping(module_name: str, logical_name: str) -> Dict[str, Dict[str, str]]:
    combined: Dict[str, Dict[str, str]] = {}
    for language in available_language_codes():
        try:
            module = importlib.import_module(f"{_package_name()}.{language}.{module_name}")
        except Exception:
            continue
        merged: Dict[str, str] = {}
        for name, value in vars(module).items():
            if name.isupper() and _matches_named_mapping(name, logical_name, language):
                if _is_flat_translation_dict(value):
                    merged.update(copy.deepcopy(value))
        if merged:
            combined[language] = merged
    return combined
def load_translation_sections() -> List[Dict[str, Dict[str, str]]]:
    sections: list[Dict[str, Dict[str, str]]] = []
    for module_name in LANGUAGE_MODULE_ORDER:
        for logical_name in PATCH_MODULE_OUTPUTS.get(module_name, []):
            section = load_named_language_mapping(module_name, logical_name)
            if section:
                sections.append(section)
    return sections
load_patch_sections = load_translation_sections
__all__ = [
    "LANGUAGE_MODULE_ORDER",
    "PATCH_MODULE_OUTPUTS",
    "load_language_translations",
    "load_all_language_translations",
    "load_named_language_mapping",
    "load_translation_sections",
    "load_patch_sections",
]
