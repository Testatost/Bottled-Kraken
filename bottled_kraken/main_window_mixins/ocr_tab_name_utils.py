"""Name helpers for OCR variant tabs."""

import re

_LEGACY_CLOSE_MARK = "×"
_GENERATED_LABEL_RE = re.compile(r"^(tab|reiter|onglet|ocr)\s*\(\s*\d+\s*\)$", re.IGNORECASE)

def plain_ocr_tab_text(text: str) -> str:
    value = str(text or "").strip()
    if value.endswith(_LEGACY_CLOSE_MARK):
        value = value[:-1].rstrip()
    return value

def is_generated_ocr_tab_label(window, text: str) -> bool:
    value = plain_ocr_tab_text(text)
    if not value or value == "+":
        return False
    if _GENERATED_LABEL_RE.match(value):
        return True
    for index in range(1, 1000):
        try:
            if value == str(window._tr("multi_ocr_variant_tab", index)):
                return True
        except Exception:
            break
    return False

def persistent_ocr_tab_name(window, text: str, fallback: str = "") -> str:
    value = plain_ocr_tab_text(text)
    if value and value != "+" and not is_generated_ocr_tab_label(window, value):
        return value
    old = plain_ocr_tab_text(fallback)
    if old and old != "+" and not is_generated_ocr_tab_label(window, old):
        return old
    return ""
