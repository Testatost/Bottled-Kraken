"""Language-combined dynamic translation section: lm_ocr_texts."""

from ..translations.translation_loader import load_named_language_mapping

BK_LM_OCR_TRANSLATIONS = load_named_language_mapping('lm_ocr_texts', 'BK_LM_OCR_TRANSLATIONS')

__all__ = ['BK_LM_OCR_TRANSLATIONS']
