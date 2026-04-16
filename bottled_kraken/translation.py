"""Zentrale Übersetzungen und Sprachhilfen für Bottled Kraken."""

from __future__ import annotations
import copy
from typing import Dict

from ._translation_data.de_ai_prompt_texts import DE_AI_PROMPT_TEXTS_TRANSLATIONS
from ._translation_data.de_ai_revision_and_dialog_texts import DE_AI_REVISION_AND_DIALOG_TEXTS_TRANSLATIONS
from ._translation_data.de_core_ui_texts import DE_CORE_UI_TEXTS_TRANSLATIONS
from ._translation_data.de_help_privacy_and_legal_texts import DE_HELP_PRIVACY_AND_LEGAL_TEXTS_TRANSLATIONS
from ._translation_data.de_image_edit_texts import DE_IMAGE_EDIT_TEXTS_TRANSLATIONS
from ._translation_data.fr_ai_prompt_texts import FR_AI_PROMPT_TEXTS_TRANSLATIONS
from ._translation_data.fr_ai_revision_and_dialog_texts import FR_AI_REVISION_AND_DIALOG_TEXTS_TRANSLATIONS
from ._translation_data.fr_core_ui_texts import FR_CORE_UI_TEXTS_TRANSLATIONS
from ._translation_data.fr_help_privacy_and_legal_texts import FR_HELP_PRIVACY_AND_LEGAL_TEXTS_TRANSLATIONS
from ._translation_data.fr_image_edit_and_navigation_texts import FR_IMAGE_EDIT_AND_NAVIGATION_TEXTS_TRANSLATIONS
from ._translation_data.en_common_actions_and_buttons import EN_COMMON_ACTIONS_AND_BUTTONS_TRANSLATIONS
from ._translation_data.en_image_edit_texts import EN_IMAGE_EDIT_TEXTS_TRANSLATIONS
from ._translation_data.en_legal_and_ai_prompt_tail import EN_LEGAL_AND_AI_PROMPT_TAIL_TRANSLATIONS
from ._translation_data.en_lm_help_and_ssh_texts import EN_LM_HELP_AND_SSH_TEXTS_TRANSLATIONS
from ._translation_data.en_voice_swap_and_batch_texts import EN_VOICE_SWAP_AND_BATCH_TEXTS_TRANSLATIONS
from ._translation_data.additional_translations import ADDITIONAL_TRANSLATIONS
from ._translation_data.bk_lm_wait_text_translations import BK_LM_WAIT_TEXT_TRANSLATIONS
from ._translation_data.bk_lm_dropdown_translations import BK_LM_DROPDOWN_TRANSLATIONS
from ._translation_data.bk_lm_db_json_patch9_translations import BK_LM_DB_JSON_PATCH9_TRANSLATIONS
from ._translation_data.bk_patch10_translations import BK_PATCH10_TRANSLATIONS
from ._translation_data.bk_patch11_translations import BK_PATCH11_TRANSLATIONS
from ._translation_data.bk_patch12_translations import BK_PATCH12_TRANSLATIONS
from ._translation_data.bk_unified_translations import BK_UNIFIED_TRANSLATIONS
from ._translation_data.bk_patch24b_translations import BK_PATCH24B_TRANSLATIONS
from ._translation_data.bk_lm_ocr_translations import BK_LM_OCR_TRANSLATIONS
from ._translation_data.merge_order import MERGE_ORDER


class translation:
    """Zentrale Sammlung aller Übersetzungen des Projekts."""

    _DE_BASE_PARTS = [
        DE_AI_PROMPT_TEXTS_TRANSLATIONS,
        DE_AI_REVISION_AND_DIALOG_TEXTS_TRANSLATIONS,
        DE_CORE_UI_TEXTS_TRANSLATIONS,
        DE_HELP_PRIVACY_AND_LEGAL_TEXTS_TRANSLATIONS,
        DE_IMAGE_EDIT_TEXTS_TRANSLATIONS,
    ]
    _FR_BASE_PARTS = [
        FR_AI_PROMPT_TEXTS_TRANSLATIONS,
        FR_AI_REVISION_AND_DIALOG_TEXTS_TRANSLATIONS,
        FR_CORE_UI_TEXTS_TRANSLATIONS,
        FR_HELP_PRIVACY_AND_LEGAL_TEXTS_TRANSLATIONS,
        FR_IMAGE_EDIT_AND_NAVIGATION_TEXTS_TRANSLATIONS,
    ]
    _EN_BASE_PARTS = [
        EN_COMMON_ACTIONS_AND_BUTTONS_TRANSLATIONS,
        EN_IMAGE_EDIT_TEXTS_TRANSLATIONS,
        EN_LEGAL_AND_AI_PROMPT_TAIL_TRANSLATIONS,
        EN_LM_HELP_AND_SSH_TEXTS_TRANSLATIONS,
        EN_VOICE_SWAP_AND_BATCH_TEXTS_TRANSLATIONS,
    ]

    BASE_TRANSLATIONS = {
        "de": {key: value for part in _DE_BASE_PARTS for key, value in part.items()},
        "fr": {key: value for part in _FR_BASE_PARTS for key, value in part.items()},
        "en": {key: value for part in _EN_BASE_PARTS for key, value in part.items()},
    }

    ADDITIONAL_TRANSLATIONS = ADDITIONAL_TRANSLATIONS
    BK_LM_WAIT_TEXT_TRANSLATIONS = BK_LM_WAIT_TEXT_TRANSLATIONS
    BK_LM_DROPDOWN_TRANSLATIONS = BK_LM_DROPDOWN_TRANSLATIONS
    BK_LM_DB_JSON_PATCH9_TRANSLATIONS = BK_LM_DB_JSON_PATCH9_TRANSLATIONS
    BK_PATCH10_TRANSLATIONS = BK_PATCH10_TRANSLATIONS
    BK_PATCH11_TRANSLATIONS = BK_PATCH11_TRANSLATIONS
    BK_PATCH12_TRANSLATIONS = BK_PATCH12_TRANSLATIONS
    BK_UNIFIED_TRANSLATIONS = BK_UNIFIED_TRANSLATIONS
    BK_PATCH24B_TRANSLATIONS = BK_PATCH24B_TRANSLATIONS
    BK_LM_OCR_TRANSLATIONS = BK_LM_OCR_TRANSLATIONS
    MERGE_ORDER = MERGE_ORDER

    @classmethod
    def build_translations(cls) -> Dict[str, Dict[str, str]]:
        data = copy.deepcopy(cls.BASE_TRANSLATIONS)
        for section in cls.MERGE_ORDER:
            for lang, values in section.items():
                data.setdefault(lang, {}).update(copy.deepcopy(values))
        for lang in ("en", "fr"):
            data.setdefault(lang, {})
            for key, value in data.get("de", {}).items():
                data[lang].setdefault(key, value)
        return data

    @classmethod
    def translate(cls, lang: str, key: str, *args):
        txt = cls.TRANSLATIONS.get(lang, cls.TRANSLATIONS.get("de", {})).get(
            key,
            cls.TRANSLATIONS.get("en", {}).get(key, key),
        )
        return txt.format(*args) if args else txt

    @classmethod
    def make_tr(cls, lang: str):
        return lambda key, *args: cls.translate(lang, key, *args)

translation.TRANSLATIONS = translation.build_translations()
TRANSLATIONS = translation.TRANSLATIONS
Translation = translation
__all__ = ["translation", "Translation", "TRANSLATIONS"]
