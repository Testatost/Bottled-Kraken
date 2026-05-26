"""Language-combined dynamic translation section: additional_translations."""

from ..translations.translation_loader import load_named_language_mapping

ADDITIONAL_TRANSLATIONS = load_named_language_mapping('additional_translations', 'ADDITIONAL_TRANSLATIONS')

__all__ = ['ADDITIONAL_TRANSLATIONS']
