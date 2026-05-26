"""Dynamic merge order for legacy translation section imports."""

from .translation_loader import load_translation_sections

MERGE_ORDER = load_translation_sections()

__all__ = ["MERGE_ORDER"]
