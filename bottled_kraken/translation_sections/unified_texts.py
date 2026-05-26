"""Language-combined dynamic translation section: unified_texts."""

from ..translations.translation_loader import load_named_language_mapping

BK_UNIFIED_TRANSLATIONS = load_named_language_mapping('unified_texts', 'BK_UNIFIED_TRANSLATIONS')

__all__ = ['BK_UNIFIED_TRANSLATIONS']
