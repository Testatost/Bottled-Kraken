"""Kompatibilitätsmodul für LM-Sanity-Testflächen.

Dieses Runtime-Modul wird absichtlich nach ``single_line_revision_context.py``
geladen, ersetzt aber keine produktive Worker-Run- oder Zeilen-Dispatch-Logik.
Die eigentlichen Merge-/Sanity-Hilfsfunktionen liegen in
``lm_revision_sanity_check_parts/`` und werden von den statischen/isolierten
Tests direkt ausgeführt. Dadurch bleiben die funktionierende LM-Zeilenauswahl
und das Zurückschreiben aus dem bestehenden Code unverändert.
"""

BK_LM_SANITY_COMPAT_ONLY = True
