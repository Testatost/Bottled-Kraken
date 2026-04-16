"""Reihenfolge zum Zusammenführen der Übersetzungsblöcke."""

from .additional_translations import ADDITIONAL_TRANSLATIONS
from .bk_lm_dropdown_translations import BK_LM_DROPDOWN_TRANSLATIONS
from .bk_lm_wait_text_translations import BK_LM_WAIT_TEXT_TRANSLATIONS
from .bk_lm_db_json_patch9_translations import BK_LM_DB_JSON_PATCH9_TRANSLATIONS
from .bk_patch10_translations import BK_PATCH10_TRANSLATIONS
from .bk_patch11_translations import BK_PATCH11_TRANSLATIONS
from .bk_patch12_translations import BK_PATCH12_TRANSLATIONS
from .bk_unified_translations import BK_UNIFIED_TRANSLATIONS
from .bk_patch24b_translations import BK_PATCH24B_TRANSLATIONS
from .bk_lm_ocr_translations import BK_LM_OCR_TRANSLATIONS

MERGE_ORDER = (
    ADDITIONAL_TRANSLATIONS,
    BK_LM_DROPDOWN_TRANSLATIONS,
    BK_LM_WAIT_TEXT_TRANSLATIONS,
    BK_LM_DB_JSON_PATCH9_TRANSLATIONS,
    BK_PATCH10_TRANSLATIONS,
    BK_PATCH11_TRANSLATIONS,
    BK_PATCH12_TRANSLATIONS,
    BK_UNIFIED_TRANSLATIONS,
    BK_PATCH24B_TRANSLATIONS,
    BK_LM_OCR_TRANSLATIONS,
)
