"""Kompatibilitaetsalias fuer alte/neue Split-Loader-Pfade.

Einige v3.3-Shared-Core-Module importieren die Translation-Helfer relativ
als ``bottled_kraken.shared_core.translation``. In der v3.2-kompatiblen
PyInstaller-Struktur liegt die zentrale Implementierung weiterhin unter
``bottled_kraken.translation``. Dieses Modul stellt die erwarteten Namen
bereit, ohne die eigentliche Translation-Logik zu duplizieren.
"""

from bottled_kraken.translation import TRANSLATIONS, Translation, translation

__all__ = ["TRANSLATIONS", "Translation", "translation"]
