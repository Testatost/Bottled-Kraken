# Sprachdateien hinzufügen

Neue Sprachen werden automatisch erkannt.

1. Neuen Ordner anlegen, z. B. `bottled_kraken/translations/es/`.
2. Darin eine leere `__init__.py` anlegen.
3. Optional `language_info.py` anlegen:

```python
NATIVE_NAME = "Español"
ENGLISH_NAME = "Spanish"
```

4. Eine oder mehrere Python-Dateien mit Translation-Dictionaries anlegen, z. B. `core_ui_texts.py`:

```python
ES_CORE_UI_TEXTS_TRANSLATIONS = {
    "lang_es": "Español",
    "toolbar_language_tooltip": "Idioma",
}
```

Alle flachen Dictionaries mit String-Keys werden automatisch geladen. Fehlende Keys werden aus den Fallback-Sprachen übernommen.
