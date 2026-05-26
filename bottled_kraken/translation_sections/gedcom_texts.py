"""Language-combined dynamic translation section: gedcom_texts."""

from ..translations.translation_loader import load_named_language_mapping

BK_GEDCOM_PROMPT_DEFAULTS = load_named_language_mapping("gedcom_texts", 'BK_GEDCOM_PROMPT_DEFAULTS')
BK_GEDCOM_VISION_TEXTS = load_named_language_mapping("gedcom_texts", 'BK_GEDCOM_VISION_TEXTS')
BK_GEDCOM_SAVE_FIX_TEXTS = load_named_language_mapping("gedcom_texts", 'BK_GEDCOM_SAVE_FIX_TEXTS')
BK_GEDCOM_ROBUST_TEXTS = load_named_language_mapping("gedcom_texts", 'BK_GEDCOM_ROBUST_TEXTS')
BK_GEDCOM_STRUCTURED_TEXTS = load_named_language_mapping("gedcom_texts", 'BK_GEDCOM_STRUCTURED_TEXTS')
BK_GEDCOM_REVIEW_TEXTS = load_named_language_mapping("gedcom_texts", 'BK_GEDCOM_REVIEW_TEXTS')
BK_PROMPT_UX_EXTRA_TEXTS = load_named_language_mapping("gedcom_texts", 'BK_PROMPT_UX_EXTRA_TEXTS')
BK_GEDCOM_TRANSLATIONS = load_named_language_mapping("gedcom_texts", 'BK_GEDCOM_TRANSLATIONS')

__all__ = ['BK_GEDCOM_PROMPT_DEFAULTS', 'BK_GEDCOM_VISION_TEXTS', 'BK_GEDCOM_SAVE_FIX_TEXTS', 'BK_GEDCOM_ROBUST_TEXTS', 'BK_GEDCOM_STRUCTURED_TEXTS', 'BK_GEDCOM_REVIEW_TEXTS', 'BK_PROMPT_UX_EXTRA_TEXTS', 'BK_GEDCOM_TRANSLATIONS']
