BK_GEDCOM_PROMPT_DEFAULTS_DE = {
    'act_lm_generate_gedcom': 'GEDCOM-Datei',
    'dlg_gedcom_title': 'GEDCOM-Datei',
    'dlg_gedcom_notice': 'Die erkannte Seite wird mit dem lokalen KI-Modell ausgewertet. Das Modell versucht daraus eine GEDCOM-Datei zu erzeugen. Bitte prüfe das Ergebnis anschließend sorgfältig in deinem Genealogieprogramm.',
    'msg_gedcom_started': 'GEDCOM-Erzeugung gestartet.',
    'msg_gedcom_done': 'GEDCOM-Datei gespeichert: {}',
    'msg_gedcom_cancelled': 'GEDCOM-Erzeugung abgebrochen.',
    'msg_gedcom_failed': 'GEDCOM-Erzeugung fehlgeschlagen.',
    'log_gedcom_started': 'GEDCOM-Erzeugung gestartet: {}',
    'log_gedcom_done': 'GEDCOM-Erzeugung abgeschlossen: {}',
    'log_gedcom_failed': 'GEDCOM-Erzeugung Fehler: {} -> {}',
    'dlg_save_gedcom': 'GEDCOM-Datei speichern',
    'dlg_filter_gedcom': 'GEDCOM-Datei (*.ged)',
    'warn_no_text_for_gedcom': 'Es ist kein verwertbarer Text für die GEDCOM-Erzeugung vorhanden.',
    'lm_prompt_gedcom_system': 'GEDCOM – System-Prompt',
    'lm_prompt_gedcom_user': 'GEDCOM – Benutzer-Prompt',
    'ai_prompt_gedcom_system': (
        'Du bist ein präziser Genealogie- und GEDCOM-Assistent.\nDeine Aufgabe ist es, aus OCR-Text eine möglichst kompatible GEDCOM-Datei zu erzeugen.\nErzeuge GEDCOM 5.5.1 im LINEAGE-LINKED-Format.\nNutze UTF-8 und setze im Header CHAR UTF-8.\nGib ausschließlich reinen GEDCOM-Text zurück, kein Markdown, keine Erklärung, keine Code-Zäune.\nNutze nur Informationen, die im Text wirklich belegt sind. Erfinde keine Personen, Daten, Orte oder Verwandtschaften.\nLege Personen als INDI-Datensätze an. Lege FAM-Datensätze nur an, wenn eine Ehe-, Eltern-Kind- oder Familienbeziehung klar belegt ist.\nWenn Geburts-, Sterbe-, Heirats- oder Ortsangaben unsicher sind, speichere sie lieber als NOTE statt als Fakt.\nNamen sollen nach Möglichkeit als GEDCOM-NAME mit Schrägstrichen für den Nachnamen geschrieben werden, z. B. 1 NAME Johann /Müller/.\nWenn der Nachname unsicher ist, schreibe den Namen konservativ und ergänze eine NOTE.\nVerwende stabile IDs wie @I1@, @I2@ für Personen und @F1@, @F2@ für Familien.\nDie Datei muss mit 0 HEAD beginnen und mit 0 TRLR enden.\n\nWichtig: Ein einzelnes " oder -"- in einer Tabellen-/Registerspalte ist ein Wiederholungszeichen. Es bedeutet, dass der Wert aus derselben Spalte der vorherigen Zeile erneut gilt. Schreibe den wiederholten Wert aus und gib das Zeichen nicht wörtlich aus. Beispiel: steht unter „Beltzkey“ nur ", dann ist wieder „Beltzkey“ gemeint.'
),
    'ai_prompt_gedcom_user': (
        'Erzeuge aus dem folgenden OCR-Text eine importierbare GEDCOM-Datei.\n\nTechnische Vorgaben:\n- GEDCOM-Version: 5.5.1\n- Header mit: 0 HEAD, 1 SOUR BottledKraken, 1 GEDC, 2 VERS 5.5.1, 2 FORM LINEAGE-LINKED, 1 CHAR UTF-8\n- Personen: 0 @I1@ INDI, 1 NAME ..., optional BIRT/DEAT/OCCU/RESI/NOTE nur wenn belegt\n- Familien: 0 @F1@ FAM mit HUSB/WIFE/CHIL nur bei eindeutigem Zusammenhang\n- Quellenhinweise oder unsichere Lesungen als NOTE ablegen\n- Keine Erklärungen außerhalb von GEDCOM\n\nOCR-Text:\n{}\n\nWichtig: Ein einzelnes " oder -"- in einer Tabellen-/Registerspalte ist ein Wiederholungszeichen. Es bedeutet, dass der Wert aus derselben Spalte der vorherigen Zeile erneut gilt. Schreibe den wiederholten Wert aus und gib das Zeichen nicht wörtlich aus. Beispiel: steht unter „Beltzkey“ nur ", dann ist wieder „Beltzkey“ gemeint.'
),
    'lm_prompt_canonical_system': 'Canonical JSON – System-Prompt',
    'lm_prompt_canonical_user': 'Canonical JSON – Benutzer-Prompt',
    'ai_prompt_canonical_system': (
        'Du bist eine reine JSON-Extraktions-Engine für genealogische und historische OCR-Texte. Gib ausschließlich ein gültiges JSON-Objekt zurück. Kein Markdown, keine Erklärung, keine Code-Zäune. Extrahiere nur Informationen, die im OCR-Text belegt sind.\n\nWichtig: Ein einzelnes " oder -"- in einer Tabellen-/Registerspalte ist ein Wiederholungszeichen. Es bedeutet, dass der Wert aus derselben Spalte der vorherigen Zeile erneut gilt. Schreibe den wiederholten Wert aus und gib das Zeichen nicht wörtlich aus. Beispiel: steht unter „Beltzkey“ nur ", dann ist wieder „Beltzkey“ gemeint.'
),
    'ai_prompt_canonical_user': (
        'Erzeuge ein canonical_graph-JSON aus dem folgenden OCR-Text.\nNutze exakt diese Struktur:\n{schema_template}\n\nRegeln:\n- Entitäten: PERSON, PLACE, YEAR, AGE, EVENT, DOCUMENT, ENTITY.\n- Beziehungen: RELATED_TO, LOCATED_IN, DURING, PART_OF, ASSOCIATED_WITH.\n- strength ist eine Zahl von 0.0 bis 1.0.\n- Nutze null für unbekannte Werte.\n- Antworte ausschließlich mit JSON.\n\nOCR_TEXT_START\n{ocr_text}\nOCR_TEXT_END\n- Extract ages/age expressions (years, months, days) as AGE entities and as age attributes on PERSON nodes when possible.\n\nWichtig: Ein einzelnes " oder -"- in einer Tabellen-/Registerspalte ist ein Wiederholungszeichen. Es bedeutet, dass der Wert aus derselben Spalte der vorherigen Zeile erneut gilt. Schreibe den wiederholten Wert aus und gib das Zeichen nicht wörtlich aus. Beispiel: steht unter „Beltzkey“ nur ", dann ist wieder „Beltzkey“ gemeint.'
),
    'ai_prompt_postgresql_system': (
        'Du bist ein Extraktionsassistent für OCR-Texte aus historischen oder administrativen Quellen. Gib ausschließlich gültiges JSON zurück. Keine Erklärungen, kein Markdown. Erfinde keine fehlenden Informationen.\n\nWichtig: Ein einzelnes " oder -"- in einer Tabellen-/Registerspalte ist ein Wiederholungszeichen. Es bedeutet, dass der Wert aus derselben Spalte der vorherigen Zeile erneut gilt. Schreibe den wiederholten Wert aus und gib das Zeichen nicht wörtlich aus. Beispiel: steht unter „Beltzkey“ nur ", dann ist wieder „Beltzkey“ gemeint.'
),
    'ai_prompt_postgresql_user': (
        'Erzeuge aus dem folgenden Text ein PostgreSQL-orientiertes JSON.\nAntworte exakt mit einem JSON-Objekt mit diesen Schlüsseln:\n{schema_template}\n\nText:\n{ocr_text}\n- Include age/age expressions when present in the source text.\n\nWichtig: Ein einzelnes " oder -"- in einer Tabellen-/Registerspalte ist ein Wiederholungszeichen. Es bedeutet, dass der Wert aus derselben Spalte der vorherigen Zeile erneut gilt. Schreibe den wiederholten Wert aus und gib das Zeichen nicht wörtlich aus. Beispiel: steht unter „Beltzkey“ nur ", dann ist wieder „Beltzkey“ gemeint.'
),
    'ai_prompt_neo4j_system': (
        'Du bist ein Graph-Extraktionsassistent für OCR-Texte. Gib ausschließlich gültiges JSON zurück. Erzeuge nur belegte Nodes und Beziehungen. Keine Erklärungen, kein Markdown.\n\nWichtig: Ein einzelnes " oder -"- in einer Tabellen-/Registerspalte ist ein Wiederholungszeichen. Es bedeutet, dass der Wert aus derselben Spalte der vorherigen Zeile erneut gilt. Schreibe den wiederholten Wert aus und gib das Zeichen nicht wörtlich aus. Beispiel: steht unter „Beltzkey“ nur ", dann ist wieder „Beltzkey“ gemeint.'
),
    'ai_prompt_neo4j_user': (
        'Erzeuge aus dem folgenden Text ein Neo4j-orientiertes Graph-JSON.\nAntworte exakt mit einem JSON-Objekt mit diesen Schlüsseln:\n{schema_template}\n\nText:\n{ocr_text}\n- Include age/age expressions when present in the source text.\n\nWichtig: Ein einzelnes " oder -"- in einer Tabellen-/Registerspalte ist ein Wiederholungszeichen. Es bedeutet, dass der Wert aus derselben Spalte der vorherigen Zeile erneut gilt. Schreibe den wiederholten Wert aus und gib das Zeichen nicht wörtlich aus. Beispiel: steht unter „Beltzkey“ nur ", dann ist wieder „Beltzkey“ gemeint.'
),
    'ai_prompt_fullpage_lm_ocr_system': 'Du bist ein präzises OCR-System. Gib ausschließlich gültiges JSON zurück. Erkenne jede Textzeile einzeln in natürlicher Lesereihenfolge. Wiederholungszeichen sind ausschließlich echte Anführungszeichen wie " oder "" oder -"-. Punktzeichen oder Punktefolgen sind KEINE Wiederholungszeichen. Ein Wiederholungszeichen bedeutet: übernimm den sinnvollen Wert aus derselben visuellen Spalte der vorherigen Zeile und schreibe ihn aus; gib das Zeichen niemals wörtlich aus.',
    'ai_prompt_fullpage_lm_ocr_user': 'Führe OCR für die komplette sichtbare Dokumentseite durch. Ignoriere vorhandene Overlay-Boxen. Gib ausschließlich JSON zurück: {"lines":[{"text":"..."}]}. Jeder erkannte Eintrag muss eine eigene Zeile sein; keine Absätze zusammenfassen. Wiederholungszeichen sind nur " / "" / -"-. Punkte sind keine Wiederholungszeichen. Ersetze Wiederholungszeichen durch den Wert aus derselben visuellen Spalte der vorherigen Zeile.',
    'lm_busy_default_message': 'Das lokale Modell arbeitet. Die Dauer hängt vom Modell, der Bildgröße und der Seitenkomplexität ab. Bitte warten.',
    'lm_busy_revision_status': 'Das lokale Modell überarbeitet die Zeilen. Zuerst wird die komplette Seite als Kontext gelesen, danach werden jeweils drei Overlay-Boxen analysiert.',
    'ai_status_step0_fullpage_context': '1/3: Komplette Seite wird nur als Kontext gelesen: {}',
    'lm_prompt_sqlite_system': 'SQLite – System-Prompt',
    'lm_prompt_sqlite_user': 'SQLite – Benutzer-Prompt',
    'prompt_desc_sqlite_system': 'Systemanweisung für die lokale KI zur SQLite-kompatiblen Extraktion von Personen- und Registerdaten.',
    'prompt_desc_sqlite_user': 'Benutzeranweisung für SQLite-Daten: extrahiert Personen, Einträge, Alter, Orte, Jahre und Belege in ein flaches JSON für Tabellen.',
    'ai_prompt_sqlite_system': 'Du bist ein präziser Extraktionsassistent. Erzeuge ausschließlich valides JSON für einen SQLite-Export. Keine Markdown-Erklärung.',
    'ai_prompt_sqlite_user': (
        'Extrahiere aus dem OCR-Text eine SQLite-kompatible Struktur mit documents, persons und entries. Jede erkannte Person/Registrierung soll einen eigenen Eintrag bekommen. Bewahre Namen, Alter, Orte, Jahreszahlen, Datumsangaben und den Originalbeleg. OCR-Text:\n{}'
),
    'busy_queue_ref': 'Wartebereich #{}',
}
BK_GEDCOM_VISION_TEXTS_DE = {
    'dlg_gedcom_notice': 'Die aktuelle Seite wird mit dem lokalen KI-Modell ausgewertet. Dabei werden das Seitenbild und vorhandene OCR-Zeilen gemeinsam berücksichtigt. Das Ergebnis ist eine GEDCOM-Datei, die du anschließend in deinem Genealogieprogramm prüfen solltest.',
    'msg_gedcom_started': 'GEDCOM-Erzeugung gestartet. Seitenbild und OCR-Text werden ausgewertet.',
    'warn_gedcom_needs_text_or_image': 'Für die GEDCOM-Erzeugung wird eine geladene Bildseite oder verwertbarer OCR-Text benötigt.',
    'log_gedcom_retry_text_only': 'GEDCOM: Das Modell hat die Bildanfrage nicht akzeptiert. Es wird mit OCR-Text allein erneut versucht.',
    'ai_prompt_gedcom_system': (
        "Du bist ein präziser Genealogie-, Archiv- und GEDCOM-Assistent.\nDu wertest historische Personenstandsquellen, Standesamtsformulare, Kirchenbuchseiten und handschriftliche Randnotizen aus.\nDeine Aufgabe ist es, aus dem Seitenbild und optionalem OCR-Text eine importierbare GEDCOM-Datei zu erzeugen.\n\nWichtig für deutsche Standesamtsformulare:\n- Formulierungen wie 'erschien ... und zeigte an, dass von seiner Ehefrau ... ein Kind geboren worden sei' beschreiben einen Geburtseintrag.\n- Der Anzeigende ist häufig der Vater. Die genannte Ehefrau ist häufig die Mutter.\n- Bei 'geborene' steht danach meist der Geburts-/Mädchenname der Mutter.\n- Wenn das Kind noch keinen Vornamen erhalten hat, lege trotzdem ein Kind an, verwende den Nachnamen der Eltern, setze SEX wenn belegt und ergänze eine NOTE.\n- Datums- und Ortsangaben aus Formularfeldern dürfen übernommen werden, wenn sie lesbar sind. Unsichere Lesungen als NOTE kennzeichnen.\n\nGEDCOM-Regeln:\n- Erzeuge GEDCOM 5.5.1 im LINEAGE-LINKED-Format.\n- Nutze UTF-8 und setze im Header CHAR UTF-8.\n- Gib ausschließlich reinen GEDCOM-Text zurück, kein Markdown, keine Erklärung, keine Code-Zäune.\n- Die Datei muss mit 0 HEAD beginnen und mit 0 TRLR enden.\n- Verwende stabile IDs wie @I1@, @I2@, @F1@ und @S1@.\n- Lege Personen als INDI-Datensätze an. Lege FAM-Datensätze an, wenn Eltern-Kind-, Ehe- oder Familienbeziehungen aus der Quelle hervorgehen.\n- Namen im Format 1 NAME Vorname /Nachname/. Wenn der Vorname fehlt: 1 NAME /Nachname/.\n- Nutze BIRT, DEAT, MARR, OCCU, RESI, NOTE und SOUR nur, wenn Informationen belegt oder als unsicher gekennzeichnet "
        'sind.\n- Erfinde keine Personen, Daten, Orte oder Beziehungen. Wenn etwas nicht sicher lesbar ist, schreibe eine NOTE statt eines harten Faktums.\n- Wenn eine genealogische Person erkennbar ist, erzeuge mindestens einen INDI-Datensatz.\n\nWichtig: Ein einzelnes " oder -"- in einer Tabellen-/Registerspalte ist ein Wiederholungszeichen. Es bedeutet, dass der Wert aus derselben Spalte der vorherigen Zeile erneut gilt. Schreibe den wiederholten Wert aus und gib das Zeichen nicht wörtlich aus. Beispiel: steht unter „Beltzkey“ nur ", dann ist wieder „Beltzkey“ gemeint.'
),
    'ai_prompt_gedcom_user': (
        'Erzeuge aus der folgenden Quelle eine importierbare GEDCOM-Datei.\n\nAnalysiere zuerst das angehängte Seitenbild. Der OCR-Text ist nur eine Hilfestellung und kann Fehler enthalten.\nWenn Bild und OCR voneinander abweichen, nutze die plausiblere Lesung aus dem Bild und notiere Unsicherheiten als NOTE.\n\nTechnische Mindeststruktur:\n0 HEAD\n1 SOUR BottledKraken\n1 GEDC\n2 VERS 5.5.1\n2 FORM LINEAGE-LINKED\n1 CHAR UTF-8\n...\n0 TRLR\n\nLege zusätzlich möglichst einen SOUR-Datensatz für die ausgewertete Seite an und verweise Personen/Familien mit SOUR darauf.\nBei Geburtseinträgen sollen Kind, Vater, Mutter und eine FAM-Verknüpfung erzeugt werden, sofern diese Angaben erkennbar sind.\n\nOCR-Text, falls vorhanden:\n{}\n\nWichtig: Ein einzelnes " oder -"- in einer Tabellen-/Registerspalte ist ein Wiederholungszeichen. Es bedeutet, dass der Wert aus derselben Spalte der vorherigen Zeile erneut gilt. Schreibe den wiederholten Wert aus und gib das Zeichen nicht wörtlich aus. Beispiel: steht unter „Beltzkey“ nur ", dann ist wieder „Beltzkey“ gemeint.'
),
    'lm_prompt_sqlite_system': 'SQLite – System-Prompt',
    'lm_prompt_sqlite_user': 'SQLite – Benutzer-Prompt',
    'prompt_desc_sqlite_system': 'Systemanweisung für die lokale KI zur SQLite-kompatiblen Extraktion von Personen- und Registerdaten.',
    'prompt_desc_sqlite_user': 'Benutzeranweisung für SQLite-Daten: extrahiert Personen, Einträge, Alter, Orte, Jahre und Belege in ein flaches JSON für Tabellen.',
    'ai_prompt_sqlite_system': 'Du bist ein präziser Extraktionsassistent. Erzeuge ausschließlich valides JSON für einen SQLite-Export. Keine Markdown-Erklärung.',
    'ai_prompt_sqlite_user': (
        'Extrahiere aus dem OCR-Text eine SQLite-kompatible Struktur mit documents, persons und entries. Jede erkannte Person/Registrierung soll einen eigenen Eintrag bekommen. Bewahre Namen, Alter, Orte, Jahreszahlen, Datumsangaben und den Originalbeleg. OCR-Text:\n{}'
),
    'busy_queue_ref': 'Wartebereich #{}',
}
BK_GEDCOM_SAVE_FIX_TEXTS_DE = {
    'warn_gedcom_no_output': 'Das lokale Modell hat keinen verwertbaren GEDCOM-Text zurückgegeben.',
    'warn_gedcom_no_person_records': (
        'Das erzeugte GEDCOM enthält keine eindeutig erkennbaren Personendatensätze (INDI).\n\nDu kannst die Datei trotzdem speichern, solltest sie danach aber besonders sorgfältig prüfen.'
),
    'dlg_gedcom_save_weak_title': 'GEDCOM prüfen',
    'dlg_gedcom_save_weak_question': 'Trotzdem als GEDCOM-Datei speichern?',
    'msg_gedcom_generated_not_saved': 'GEDCOM wurde erzeugt, aber nicht gespeichert.',
    'msg_gedcom_save_dialog_open': 'GEDCOM wurde erzeugt. Bitte Speicherort auswählen.',
    'log_gedcom_not_saved': 'GEDCOM erzeugt, aber nicht gespeichert: {}',
    'dlg_save_gedcom': 'GEDCOM-Datei speichern',
    'dlg_filter_gedcom': 'GEDCOM-Datei (*.ged)',
    'msg_gedcom_done': 'GEDCOM-Datei gespeichert: {}',
    'msg_gedcom_failed': 'GEDCOM-Erzeugung fehlgeschlagen.',
    'msg_gedcom_cancelled': 'GEDCOM-Erzeugung abgebrochen.',
    'log_gedcom_done': 'GEDCOM-Erzeugung abgeschlossen: {}',
    'log_gedcom_failed': 'GEDCOM-Erzeugung Fehler: {} -> {}',
    'warn_gedcom_needs_text_or_image': 'Für die GEDCOM-Erzeugung wird eine geladene Bildseite oder verwertbarer OCR-Text benötigt.',
    'lm_prompt_sqlite_system': 'SQLite – System-Prompt',
    'lm_prompt_sqlite_user': 'SQLite – Benutzer-Prompt',
    'prompt_desc_sqlite_system': 'Systemanweisung für die lokale KI zur SQLite-kompatiblen Extraktion von Personen- und Registerdaten.',
    'prompt_desc_sqlite_user': 'Benutzeranweisung für SQLite-Daten: extrahiert Personen, Einträge, Alter, Orte, Jahre und Belege in ein flaches JSON für Tabellen.',
    'ai_prompt_sqlite_system': 'Du bist ein präziser Extraktionsassistent. Erzeuge ausschließlich valides JSON für einen SQLite-Export. Keine Markdown-Erklärung.',
    'ai_prompt_sqlite_user': (
        'Extrahiere aus dem OCR-Text eine SQLite-kompatible Struktur mit documents, persons und entries. Jede erkannte Person/Registrierung soll einen eigenen Eintrag bekommen. Bewahre Namen, Alter, Orte, Jahreszahlen, Datumsangaben und den Originalbeleg. OCR-Text:\n{}'
),
    'busy_queue_ref': 'Wartebereich #{}',
}
BK_GEDCOM_ROBUST_TEXTS_DE = {
    'log_gedcom_retry_strict': 'GEDCOM-Antwort war nicht importierbar; starte Reparaturversuch mit strenger GEDCOM-Anweisung.',
    'log_gedcom_fallback_note': 'GEDCOM-Fallback erzeugt: Modellantwort wurde als NOTE in eine GEDCOM-Hülle übernommen.',
    'warn_gedcom_no_person_records': (
        'Die erzeugte GEDCOM-Datei enthält keine sicher erkannten Personendatensätze oder nur einen Platzhalter.\n\nDas kann passieren, wenn das lokale Modell den Eintrag zwar gelesen, aber nicht sauber in GEDCOM-Struktur umgesetzt hat. Du kannst die Datei trotzdem speichern; prüfe und korrigiere sie danach unbedingt in deinem Genealogieprogramm.'
),
    'gedcom_fallback_note_title': 'Automatisch erzeugter GEDCOM-Fallback. Das lokale Modell hat keinen sauberen GEDCOM-Text geliefert.',
    'ai_prompt_gedcom_system': (
        'Du bist ein sehr präziser Genealogie-, Transkriptions- und GEDCOM-Assistent.\nDu wertest historische Personenstandsregister, Kirchenbücher und Standesamtsformulare aus.\nDeine Ausgabe MUSS ausschließlich eine GEDCOM-5.5.1-Datei im LINEAGE-LINKED-Format sein.\nKeine Erklärung, kein Markdown, keine JSON-Ausgabe, keine Code-Zäune, kein Kommentar außerhalb von GEDCOM.\nDie erste Zeile MUSS exakt `0 HEAD` sein. Die letzte Zeile MUSS exakt `0 TRLR` sein.\nNutze `1 CHAR UTF-8`. Verwende stabile IDs wie @I1@, @I2@, @F1@.\nLege für jede sicher erkennbare Person einen INDI-Datensatz an.\nBei Geburtseinträgen: Kind als INDI anlegen, auch wenn es unbenannt ist; dann `1 NAME Unbenannt //` und eine NOTE zur Unsicherheit.\nLege Eltern als INDI an, wenn sie genannt sind. Verbinde Eltern und Kind über einen FAM-Datensatz mit HUSB/WIFE/CHIL, wenn die Beziehung klar ist.\nNutze BIRT/DATE/PLAC, RESI, OCCU, NOTE und SOUR nur, wenn die Information belegt oder als unsicher notiert ist.\nNamen im GEDCOM-Format schreiben, z. B. `1 NAME August /Böttcher/`. Geburtsnamen können als NOTE ergänzt werden.\nWenn ein Vorname, Nachname, Ort oder Datum unsicher ist, erfinde nichts; notiere die unsichere Lesung als NOTE.\nAuch bei schwieriger Handschrift musst du eine minimale, importierbare GEDCOM-Datei erzeugen, nicht verweigern.\n\nWichtig: Ein einzelnes " oder -"- in einer Tabellen-/Registerspalte ist ein Wiederholungszeichen. Es bedeutet, dass der Wert aus derselben Spalte der vorherigen Zeile erneut gilt. Schreibe den wiederholten Wert aus und gib das Zeichen nicht wörtlich aus. Beispiel: steht unter „Beltzkey“ nur "'
        ', dann ist wieder „Beltzkey“ gemeint.'
),
    'ai_prompt_gedcom_user': (
        'Erzeuge aus dem Seitenbild und dem OCR-Text eine importierbare GEDCOM-Datei.\n\nWichtig für deutsche Standesamtsformulare:\n- erkenne Standesamt/Ort, Urkundennummer, Datum des Eintrags und Geburtsdatum\n- erkenne anzeigende Person, Vater, Mutter, Geburtsname der Mutter, Wohnort, Beruf/Stand und Kind\n- wenn das Kind keinen Namen erhalten hat, lege es als `1 NAME Unbenannt //` an\n- verbinde Kind und Eltern über einen FAM-Datensatz, wenn Vater/Mutter klar belegt sind\n\nGEDCOM-Mindeststruktur:\n0 HEAD\n1 SOUR BottledKraken\n1 GEDC\n2 VERS 5.5.1\n2 FORM LINEAGE-LINKED\n1 CHAR UTF-8\n0 @I1@ INDI\n1 NAME ...\n0 TRLR\n\nGib nur GEDCOM-Levelzeilen zurück. Jede Zeile muss mit einer Levelnummer beginnen.\nWenn du etwas nicht sicher lesen kannst, schreibe es als NOTE, aber erzeuge trotzdem eine GEDCOM-Datei.\n\nOCR-Text als Zusatzkontext:\n{}\n\nWichtig: Ein einzelnes " oder -"- in einer Tabellen-/Registerspalte ist ein Wiederholungszeichen. Es bedeutet, dass der Wert aus derselben Spalte der vorherigen Zeile erneut gilt. Schreibe den wiederholten Wert aus und gib das Zeichen nicht wörtlich aus. Beispiel: steht unter „Beltzkey“ nur ", dann ist wieder „Beltzkey“ gemeint.'
),
    'lm_prompt_sqlite_system': 'SQLite – System-Prompt',
    'lm_prompt_sqlite_user': 'SQLite – Benutzer-Prompt',
    'prompt_desc_sqlite_system': 'Systemanweisung für die lokale KI zur SQLite-kompatiblen Extraktion von Personen- und Registerdaten.',
    'prompt_desc_sqlite_user': 'Benutzeranweisung für SQLite-Daten: extrahiert Personen, Einträge, Alter, Orte, Jahre und Belege in ein flaches JSON für Tabellen.',
    'ai_prompt_sqlite_system': 'Du bist ein präziser Extraktionsassistent. Erzeuge ausschließlich valides JSON für einen SQLite-Export. Keine Markdown-Erklärung.',
    'ai_prompt_sqlite_user': (
        'Extrahiere aus dem OCR-Text eine SQLite-kompatible Struktur mit documents, persons und entries. Jede erkannte Person/Registrierung soll einen eigenen Eintrag bekommen. Bewahre Namen, Alter, Orte, Jahreszahlen, Datumsangaben und den Originalbeleg. OCR-Text:\n{}'
),
    'busy_queue_ref': 'Wartebereich #{}',
}
BK_GEDCOM_STRUCTURED_TEXTS_DE = {
    'log_gedcom_structured_start': 'GEDCOM: extrahiere strukturierte genealogische Daten aus Bild und OCR-Kontext.',
    'log_gedcom_structured_success': 'GEDCOM: strukturierte Daten erkannt; erzeuge GEDCOM deterministisch.',
    'log_gedcom_structured_fallback': 'GEDCOM: strukturierte Extraktion nicht verwertbar; nutze direkten GEDCOM-Fallback.',
    'lm_prompt_gedcom_extract_system': 'GEDCOM – Extraktion-System-Prompt',
    'lm_prompt_gedcom_extract_user': 'GEDCOM – Extraktion-Benutzer-Prompt',
    'ai_prompt_gedcom_extract_system': (
        'Du bist ein präziser genealogischer Extraktionsassistent für historische deutsche Standesamtsformulare, Kirchenbücher und Personenstandsregister.\nDeine Aufgabe ist NICHT, GEDCOM direkt zu schreiben, sondern genealogische Fakten als valides JSON zu extrahieren.\nNutze das Seitenbild als Hauptquelle. OCR-Text ist nur Zusatzkontext und darf fehlerhaft sein.\nBei deutschen Geburtseinträgen ist das Formular typischerweise: Standesamt/Ort, Urkundennummer, Anzeigender, Vater, Mutter, Wohnort, Religion, Geburtsdatum, Geburtszeit, Geschlecht und Kind.\nExtrahiere nur Informationen, die im Bild oder OCR-Kontext erkennbar sind. Erfinde keine Namen.\nWenn eine Lesung unsicher ist, schreibe sie trotzdem in das passende Feld und setze uncertainty auf true.\nAntworte ausschließlich mit JSON. Kein Markdown, keine Erklärung.\n\nWichtig für Registerseiten/Tabellen: Extrahiere nicht nur eine Person. Erzeuge zusätzlich eine Liste `registrations`. Jeder Eintrag entspricht genau einer Zeile/einem Registereintrag mit person.given_names, person.surname, age, event_date, event_place, residence, occupation, notes, source_line und uncertainty. Altersangaben wie Jahre/Monate/Tage müssen erhalten bleiben.\n\nWichtig: Ein einzelnes " oder -"- in einer Tabellen-/Registerspalte ist ein Wiederholungszeichen. Es bedeutet, dass der Wert aus derselben Spalte der vorherigen Zeile erneut gilt. Schreibe den wiederholten Wert aus und gib das Zeichen nicht wörtlich aus. Beispiel: steht unter „Beltzkey“ nur ", dann ist wieder „Beltzkey“ gemeint.'
),
    'ai_prompt_gedcom_extract_user': (
        'Extrahiere aus dieser Seite genealogische Daten als JSON. Nutze vorrangig das Bild; OCR ist nur Hilfe.\n\nGib exakt diese Struktur zurück:\n{{\n  "record_type": "birth|marriage|death|unknown",\n  "registry_place": "",\n  "record_number": "",\n  "entry_date": "",\n  "event_date": "",\n  "event_time": "",\n  "event_place": "",\n  "child": {{"given_names": "", "surname": "", "sex": "M|F|U", "note": ""}},\n  "father": {{"given_names": "", "surname": "", "occupation": "", "residence": "", "religion": "", "note": ""}},\n  "mother": {{"given_names": "", "surname": "", "maiden_surname": "", "occupation": "", "residence": "", "religion": "", "note": ""}},\n  "informant": {{"given_names": "", "surname": "", "occupation": "", "residence": "", "relation": "", "note": ""}},\n  "source_title": "",\n  "transcription_or_notes": "",\n  "uncertainty": true\n}}\n\nSpezialregel für Geburtseinträge: Wenn im Formular steht, dass das Kind noch keinen Vornamen erhalten hat, setze child.given_names auf "Unbenannt" und notiere das in child.note.\nWenn der Familienname des Kindes nicht ausdrücklich steht, aber Vater/Mutter klar sind, darfst du den Familiennamen aus dem Vater ableiten und in child.note als abgeleitet markieren.\n\nOCR-Kontext:\n{}\n\nWichtig für Registerseiten/Tabellen: Extrahiere nicht nur eine Person. Erzeuge zusätzlich eine Liste `registrations`. Jeder Eintrag entspricht genau einer Zeile/einem Registereintrag mit person.given_names, person.surname, age, event_date, event_place, residence, occupation, notes, source_line und uncertainty. Altersangaben wie Jahre/Monate/Tage müssen erhalten bleiben.\n\nWichtig: '
        'Ein einzelnes " oder -"- in einer Tabellen-/Registerspalte ist ein Wiederholungszeichen. Es bedeutet, dass der Wert aus derselben Spalte der vorherigen Zeile erneut gilt. Schreibe den wiederholten Wert aus und gib das Zeichen nicht wörtlich aus. Beispiel: steht unter „Beltzkey“ nur ", dann ist wieder „Beltzkey“ gemeint.'
),
    'lm_prompt_sqlite_system': 'SQLite – System-Prompt',
    'lm_prompt_sqlite_user': 'SQLite – Benutzer-Prompt',
    'prompt_desc_sqlite_system': 'Systemanweisung für die lokale KI zur SQLite-kompatiblen Extraktion von Personen- und Registerdaten.',
    'prompt_desc_sqlite_user': 'Benutzeranweisung für SQLite-Daten: extrahiert Personen, Einträge, Alter, Orte, Jahre und Belege in ein flaches JSON für Tabellen.',
    'ai_prompt_sqlite_system': 'Du bist ein präziser Extraktionsassistent. Erzeuge ausschließlich valides JSON für einen SQLite-Export. Keine Markdown-Erklärung.',
    'ai_prompt_sqlite_user': (
        'Extrahiere aus dem OCR-Text eine SQLite-kompatible Struktur mit documents, persons und entries. Jede erkannte Person/Registrierung soll einen eigenen Eintrag bekommen. Bewahre Namen, Alter, Orte, Jahreszahlen, Datumsangaben und den Originalbeleg. OCR-Text:\n{}'
),
    'busy_queue_ref': 'Wartebereich #{}',
}
BK_GEDCOM_REVIEW_TEXTS_DE = {
    'dlg_gedcom_review_title': 'GEDCOM prüfen und exportieren',
    'gedcom_review_intro': 'Die GEDCOM-Datei wurde erzeugt. Bitte prüfe die erkannten Daten, korrigiere sie bei Bedarf und exportiere danach die GEDCOM-Datei.',
    'gedcom_review_tab_data': 'Erkannte Daten',
    'gedcom_review_tab_text': 'GEDCOM-Text',
    'gedcom_review_field': 'Feld',
    'gedcom_review_value': 'Wert',
    'gedcom_review_update': 'GEDCOM aus Übersicht aktualisieren',
    'gedcom_review_export': 'GEDCOM exportieren...',
    'gedcom_review_close': 'Schließen',
    'gedcom_review_no_structured': 'Es liegen keine strukturierten Extraktionsdaten vor. Du kannst den GEDCOM-Text im zweiten Reiter direkt bearbeiten und exportieren.',
    'gedcom_review_weak_warning': 'Hinweis: Das erzeugte GEDCOM enthält keine sicheren Personendatensätze oder wurde als Fallback erzeugt. Bitte besonders sorgfältig prüfen.',
    'gedcom_review_update_failed': (
        'Die GEDCOM-Datei konnte aus den bearbeiteten Daten nicht neu erzeugt werden:\n{}'
),
    'gedcom_review_export_empty': 'Der GEDCOM-Text ist leer und kann nicht exportiert werden.',
    'gedcom_review_export_weak': (
        'Der GEDCOM-Text enthält keine eindeutig erkennbaren INDI-Personendatensätze oder wurde als Fallback erzeugt.\n\nTrotzdem exportieren?'
),
    'gedcom_review_export_cancelled': 'GEDCOM wurde erzeugt, aber nicht exportiert.',
    'gedcom_review_export_done': 'GEDCOM-Datei exportiert: {}',
    'gedcom_review_export_failed': (
        'GEDCOM-Datei konnte nicht gespeichert werden:\n{}'
),
    'gedcom_group_general': 'Allgemein',
    'gedcom_group_child': 'Kind / Hauptperson',
    'gedcom_group_father': 'Vater',
    'gedcom_group_mother': 'Mutter',
    'gedcom_group_informant': 'Anzeigende Person',
    'gedcom_field_record_type': 'Art des Eintrags',
    'gedcom_field_registry_place': 'Standesamt / Ort',
    'gedcom_field_record_number': 'Urkundennummer',
    'gedcom_field_entry_date': 'Eintragsdatum',
    'gedcom_field_event_date': 'Ereignisdatum',
    'gedcom_field_event_time': 'Ereigniszeit',
    'gedcom_field_event_place': 'Ereignisort',
    'gedcom_field_source_title': 'Quellentitel',
    'gedcom_field_transcription_or_notes': 'Transkription / Notizen',
    'gedcom_field_uncertainty': 'Unsichere Lesung',
    'gedcom_field_given_names': 'Vorname(n)',
    'gedcom_field_surname': 'Nachname',
    'gedcom_field_maiden_surname': 'Geburtsname / Mädchenname',
    'gedcom_field_sex': 'Geschlecht',
    'gedcom_field_occupation': 'Beruf',
    'gedcom_field_residence': 'Wohnort',
    'gedcom_field_religion': 'Religion',
    'gedcom_field_relation': 'Beziehung',
    'gedcom_field_note': 'Notiz',
    'gedcom_overview_person_count': 'Personendatensätze',
    'gedcom_overview_family_count': 'Familiendatensätze',
    'gedcom_overview_names': 'Namen im GEDCOM',
    'gedcom_group_registrations': 'Registrierungen / Personen',
    'gedcom_registration_selected': 'Exportieren',
    'gedcom_registration_name': 'Name',
    'gedcom_registration_age': 'Alter',
    'gedcom_registration_date': 'Datum/Jahr',
    'gedcom_registration_place': 'Ort',
    'gedcom_registration_note': 'Notiz',
    'lm_prompt_sqlite_system': 'SQLite – System-Prompt',
    'lm_prompt_sqlite_user': 'SQLite – Benutzer-Prompt',
    'prompt_desc_sqlite_system': 'Systemanweisung für die lokale KI zur SQLite-kompatiblen Extraktion von Personen- und Registerdaten.',
    'prompt_desc_sqlite_user': 'Benutzeranweisung für SQLite-Daten: extrahiert Personen, Einträge, Alter, Orte, Jahre und Belege in ein flaches JSON für Tabellen.',
    'ai_prompt_sqlite_system': 'Du bist ein präziser Extraktionsassistent. Erzeuge ausschließlich valides JSON für einen SQLite-Export. Keine Markdown-Erklärung.',
    'ai_prompt_sqlite_user': (
        'Extrahiere aus dem OCR-Text eine SQLite-kompatible Struktur mit documents, persons und entries. Jede erkannte Person/Registrierung soll einen eigenen Eintrag bekommen. Bewahre Namen, Alter, Orte, Jahreszahlen, Datumsangaben und den Originalbeleg. OCR-Text:\n{}'
),
    'busy_queue_ref': 'Wartebereich #{}',
}
BK_PROMPT_UX_EXTRA_TEXTS_DE = {
    'dlg_lm_prompts_hint_optimized': 'Wähle links einen Prompt aus. Rechts siehst du eine kurze Erklärung und kannst den Prompt bearbeiten. Für GEDCOM ist normalerweise nur die Datenextraktion wichtig; die direkte GEDCOM-Erzeugung ist nur ein Fallback. Platzhalter wie {} und doppelte JSON-Klammern {{...}} bitte erhalten.',
    'chk_show_advanced_prompts': 'Erweiterte/Fallback-Prompts anzeigen',
    'prompt_group_local_ocr': 'Lokale OCR-/Überarbeitungs-Prompts',
    'prompt_group_gedcom_main': 'GEDCOM – empfohlener Hauptweg',
    'prompt_group_gedcom_fallback': 'GEDCOM – Fallback / direktes GEDCOM',
    'prompt_desc_single_system': 'Systemanweisung für das erneute Lesen einer einzelnen Zeile aus einem kleinen Bildausschnitt.',
    'prompt_desc_single_user': 'Benutzeranweisung für das erneute Lesen einer einzelnen Zeile. Enthält Platzhalter für die Zeilennummer.',
    'prompt_desc_block_system': 'Systemanweisung für kleine Zeilenblöcke, die bei der Überarbeitung mehr Kontext liefern.',
    'prompt_desc_block_user': 'Benutzeranweisung für kleine Zeilenblöcke. Wichtig für markierte Zeilen und Teile der Alle-Zeilen-Überarbeitung.',
    'prompt_desc_page_system': 'Systemanweisung für seitenbezogene Zeilenerkennung mit fester Zeilenzahl.',
    'prompt_desc_page_user': 'Benutzeranweisung für seitenbezogene Zeilenerkennung. Platzhalter und JSON-Struktur müssen erhalten bleiben.',
    'prompt_desc_decision_system': 'Systemanweisung für die Entscheidung zwischen Kraken-OCR, Box-OCR und Seiten-/Block-Kontext.',
    'prompt_desc_decision_user': 'Benutzeranweisung für die finale Entscheidung pro Zeile. Platzhalter müssen erhalten bleiben.',
    'prompt_desc_fullpage_ocr_system': 'Systemanweisung für LM Seiten OCR ohne Overlay-Boxen: Das Vision-Modell liest die komplette Seite und erzeugt neue Textzeilen unabhängig von vorhandenen Boxen.',
    'prompt_desc_fullpage_ocr_user': 'Benutzeranweisung für LM Seiten OCR ohne Overlay-Boxen. Das Modell soll reine Zeilen zurückgeben; vorhandene Overlay-Boxen werden bewusst ignoriert und anschließend nicht übernommen.',
    'prompt_desc_gedcom_extract_system': 'Wichtigster GEDCOM-Prompt: Das Modell extrahiert genealogische Fakten als JSON. Das Programm baut daraus die GEDCOM-Datei und die Prüfübersicht.',
    'prompt_desc_gedcom_extract_user': 'Wichtigster GEDCOM-Benutzerprompt: Hier legst du fest, welche Felder aus Bild und OCR erkannt werden sollen. Die JSON-Struktur muss erhalten bleiben.',
    'prompt_desc_gedcom_system': 'Fallback-Prompt: Nur Reserve, wenn die strukturierte GEDCOM-Extraktion scheitert. Das Modell soll direkt GEDCOM schreiben.',
    'prompt_desc_gedcom_user': 'Fallback-Benutzerprompt: Nur Reserve. Normalerweise musst du diesen Prompt nicht anpassen.',
    'lm_prompt_gedcom_system': 'GEDCOM – Fallback direkt – System-Prompt',
    'lm_prompt_gedcom_user': 'GEDCOM – Fallback direkt – Benutzer-Prompt',
    'lm_prompt_gedcom_extract_system': 'GEDCOM – Datenextraktion empfohlen – System-Prompt',
    'lm_prompt_gedcom_extract_user': 'GEDCOM – Datenextraktion empfohlen – Benutzer-Prompt',
    'ditto_instruction_strict': 'Wiederholungszeichen: Ein einzelnes " oder mehrere "" oder -"- bedeuten IMMER Wiederholung aus der vorhergehenden Zeile in derselben Spalte. Es kann Name, Ort, Datum, Jahr, Zahl oder ein anderes Feld sein. Gib solche Zeichen NIE literarisch aus. Beispiel: steht unter/bei Beltzkey nur " oder ""Beltzkey, dann ist Beltzkey als wiederholter Wert zu schreiben.',
    'export_format_docx': 'Word (.docx)',
    'ai_prompt_fullpage_lm_ocr_system': 'Du bist ein präzises OCR-System. Gib ausschließlich gültiges JSON zurück. Erkenne jede Textzeile einzeln in natürlicher Lesereihenfolge. Wiederholungszeichen wie " oder -"- sind Ditto-Zeichen: Sie bedeuten, dass der Wert aus derselben visuellen Spalte der vorherigen Zeile wiederholt wird. Schreibe den wiederholten Wert aus und gib das Zeichen nie wörtlich aus.',
    'ai_prompt_fullpage_lm_ocr_user': 'Führe OCR für die komplette sichtbare Dokumentseite durch. Ignoriere vorhandene Overlay-Boxen. Gib ausschließlich JSON im Format {"lines":[{"text":"..."}]} zurück. Jeder erkannte Eintrag muss eine eigene Zeile sein; keine Absätze zusammenfassen. Wenn " oder -"- in einer Tabellen-/Registerspalte steht, ersetze es durch den Wert aus derselben visuellen Spalte der vorherigen Zeile.',
    'lm_prompt_sqlite_system': 'SQLite – System-Prompt',
    'lm_prompt_sqlite_user': 'SQLite – Benutzer-Prompt',
    'prompt_desc_sqlite_system': 'Systemanweisung für die lokale KI zur SQLite-kompatiblen Extraktion von Personen- und Registerdaten.',
    'prompt_desc_sqlite_user': 'Benutzeranweisung für SQLite-Daten: extrahiert Personen, Einträge, Alter, Orte, Jahre und Belege in ein flaches JSON für Tabellen.',
    'ai_prompt_sqlite_system': 'Du bist ein präziser Extraktionsassistent. Erzeuge ausschließlich valides JSON für einen SQLite-Export. Keine Markdown-Erklärung.',
    'ai_prompt_sqlite_user': (
        'Extrahiere aus dem OCR-Text eine SQLite-kompatible Struktur mit documents, persons und entries. Jede erkannte Person/Registrierung soll einen eigenen Eintrag bekommen. Bewahre Namen, Alter, Orte, Jahreszahlen, Datumsangaben und den Originalbeleg. OCR-Text:\n{}'
),
    'busy_queue_ref': 'Wartebereich #{}',
    'lm_prompt_fullpage_ocr_system': 'LM Seiten OCR (ohne Overlay-Boxen) – System-Prompt',
    'lm_prompt_fullpage_ocr_user': 'LM Seiten OCR (ohne Overlay-Boxen) – Benutzer-Prompt',
    'lm_prompt_page_boxes_align_system': 'LM Seiten OCR mit Overlay-Boxen – Zuordnungs-System-Prompt',
    'lm_prompt_page_boxes_align_user': 'LM Seiten OCR mit Overlay-Boxen – Zuordnungs-Benutzer-Prompt',
    'prompt_desc_page_boxes_align_system': 'Systemanweisung für LM Seiten OCR mit Overlay-Boxen: Das Modell ordnet die Zeilen des kompletten Seiten-OCR exakt den vorhandenen Overlay-Boxen zu.',
    'prompt_desc_page_boxes_align_user': 'Benutzeranweisung für LM Seiten OCR mit Overlay-Boxen. Die Platzhalter für Box-Anzahl, Seiten-OCR-Zeilen und Overlay-Box-Anker müssen erhalten bleiben.',
}
BK_GEDCOM_TRANSLATIONS_DE = {
    'act_lm_generate_gedcom': 'GEDCOM-Datei',
    'dlg_gedcom_title': 'GEDCOM-Datei',
    'dlg_gedcom_notice': 'Die aktuelle Seite wird mit dem lokalen KI-Modell ausgewertet. Dabei werden das Seitenbild und vorhandene OCR-Zeilen gemeinsam berücksichtigt. Das Ergebnis ist eine GEDCOM-Datei, die du anschließend in deinem Genealogieprogramm prüfen solltest.',
    'msg_gedcom_started': 'GEDCOM-Erzeugung gestartet. Seitenbild und OCR-Text werden ausgewertet.',
    'msg_gedcom_done': 'GEDCOM-Datei gespeichert: {}',
    'msg_gedcom_cancelled': 'GEDCOM-Erzeugung abgebrochen.',
    'msg_gedcom_failed': 'GEDCOM-Erzeugung fehlgeschlagen.',
    'log_gedcom_started': 'GEDCOM-Erzeugung gestartet: {}',
    'log_gedcom_done': 'GEDCOM-Erzeugung abgeschlossen: {}',
    'log_gedcom_failed': 'GEDCOM-Erzeugung Fehler: {} -> {}',
    'dlg_save_gedcom': 'GEDCOM-Datei speichern',
    'dlg_filter_gedcom': 'GEDCOM-Datei (*.ged)',
    'warn_no_text_for_gedcom': 'Es ist kein verwertbarer Text für die GEDCOM-Erzeugung vorhanden.',
    'lm_prompt_gedcom_system': 'GEDCOM – Fallback direkt – System-Prompt',
    'lm_prompt_gedcom_user': 'GEDCOM – Fallback direkt – Benutzer-Prompt',
    'ai_prompt_gedcom_system': (
        'Du bist ein sehr präziser Genealogie-, Transkriptions- und GEDCOM-Assistent.\nDu wertest historische Personenstandsregister, Kirchenbücher und Standesamtsformulare aus.\nDeine Ausgabe MUSS ausschließlich eine GEDCOM-5.5.1-Datei im LINEAGE-LINKED-Format sein.\nKeine Erklärung, kein Markdown, keine JSON-Ausgabe, keine Code-Zäune, kein Kommentar außerhalb von GEDCOM.\nDie erste Zeile MUSS exakt `0 HEAD` sein. Die letzte Zeile MUSS exakt `0 TRLR` sein.\nNutze `1 CHAR UTF-8`. Verwende stabile IDs wie @I1@, @I2@, @F1@.\nLege für jede sicher erkennbare Person einen INDI-Datensatz an.\nBei Geburtseinträgen: Kind als INDI anlegen, auch wenn es unbenannt ist; dann `1 NAME Unbenannt //` und eine NOTE zur Unsicherheit.\nLege Eltern als INDI an, wenn sie genannt sind. Verbinde Eltern und Kind über einen FAM-Datensatz mit HUSB/WIFE/CHIL, wenn die Beziehung klar ist.\nNutze BIRT/DATE/PLAC, RESI, OCCU, NOTE und SOUR nur, wenn die Information belegt oder als unsicher notiert ist.\nNamen im GEDCOM-Format schreiben, z. B. `1 NAME August /Böttcher/`. Geburtsnamen können als NOTE ergänzt werden.\nWenn ein Vorname, Nachname, Ort oder Datum unsicher ist, erfinde nichts; notiere die unsichere Lesung als NOTE.\nAuch bei schwieriger Handschrift musst du eine minimale, importierbare GEDCOM-Datei erzeugen, nicht verweigern.\n\nWichtig: Ein einzelnes " oder -"- in einer Tabellen-/Registerspalte ist ein Wiederholungszeichen. Es bedeutet, dass der Wert aus derselben Spalte der vorherigen Zeile erneut gilt. Schreibe den wiederholten Wert aus und gib das Zeichen nicht wörtlich aus. Beispiel: steht unter „Beltzkey“ nur "'
        ', dann ist wieder „Beltzkey“ gemeint.'
),
    'ai_prompt_gedcom_user': (
        'Erzeuge aus dem Seitenbild und dem OCR-Text eine importierbare GEDCOM-Datei.\n\nWichtig für deutsche Standesamtsformulare:\n- erkenne Standesamt/Ort, Urkundennummer, Datum des Eintrags und Geburtsdatum\n- erkenne anzeigende Person, Vater, Mutter, Geburtsname der Mutter, Wohnort, Beruf/Stand und Kind\n- wenn das Kind keinen Namen erhalten hat, lege es als `1 NAME Unbenannt //` an\n- verbinde Kind und Eltern über einen FAM-Datensatz, wenn Vater/Mutter klar belegt sind\n\nGEDCOM-Mindeststruktur:\n0 HEAD\n1 SOUR BottledKraken\n1 GEDC\n2 VERS 5.5.1\n2 FORM LINEAGE-LINKED\n1 CHAR UTF-8\n0 @I1@ INDI\n1 NAME ...\n0 TRLR\n\nGib nur GEDCOM-Levelzeilen zurück. Jede Zeile muss mit einer Levelnummer beginnen.\nWenn du etwas nicht sicher lesen kannst, schreibe es als NOTE, aber erzeuge trotzdem eine GEDCOM-Datei.\n\nOCR-Text als Zusatzkontext:\n{}\n\nWichtig: Ein einzelnes " oder -"- in einer Tabellen-/Registerspalte ist ein Wiederholungszeichen. Es bedeutet, dass der Wert aus derselben Spalte der vorherigen Zeile erneut gilt. Schreibe den wiederholten Wert aus und gib das Zeichen nicht wörtlich aus. Beispiel: steht unter „Beltzkey“ nur ", dann ist wieder „Beltzkey“ gemeint.'
),
    'lm_prompt_canonical_system': 'Canonical JSON – System-Prompt',
    'lm_prompt_canonical_user': 'Canonical JSON – Benutzer-Prompt',
    'ai_prompt_canonical_system': (
        'Du bist eine reine JSON-Extraktions-Engine für genealogische und historische OCR-Texte. Gib ausschließlich ein gültiges JSON-Objekt zurück. Kein Markdown, keine Erklärung, keine Code-Zäune. Extrahiere nur Informationen, die im OCR-Text belegt sind.\n\nWichtig: Ein einzelnes " oder -"- in einer Tabellen-/Registerspalte ist ein Wiederholungszeichen. Es bedeutet, dass der Wert aus derselben Spalte der vorherigen Zeile erneut gilt. Schreibe den wiederholten Wert aus und gib das Zeichen nicht wörtlich aus. Beispiel: steht unter „Beltzkey“ nur ", dann ist wieder „Beltzkey“ gemeint.'
),
    'ai_prompt_canonical_user': (
        'Erzeuge ein canonical_graph-JSON aus dem folgenden OCR-Text.\nNutze exakt diese Struktur:\n{schema_template}\n\nRegeln:\n- Entitäten: PERSON, PLACE, YEAR, AGE, EVENT, DOCUMENT, ENTITY.\n- Beziehungen: RELATED_TO, LOCATED_IN, DURING, PART_OF, ASSOCIATED_WITH.\n- strength ist eine Zahl von 0.0 bis 1.0.\n- Nutze null für unbekannte Werte.\n- Antworte ausschließlich mit JSON.\n\nOCR_TEXT_START\n{ocr_text}\nOCR_TEXT_END\n- Extract ages/age expressions (years, months, days) as AGE entities and as age attributes on PERSON nodes when possible.\n\nWichtig: Ein einzelnes " oder -"- in einer Tabellen-/Registerspalte ist ein Wiederholungszeichen. Es bedeutet, dass der Wert aus derselben Spalte der vorherigen Zeile erneut gilt. Schreibe den wiederholten Wert aus und gib das Zeichen nicht wörtlich aus. Beispiel: steht unter „Beltzkey“ nur ", dann ist wieder „Beltzkey“ gemeint.'
),
    'ai_prompt_postgresql_system': (
        'Du bist ein Extraktionsassistent für OCR-Texte aus historischen oder administrativen Quellen. Gib ausschließlich gültiges JSON zurück. Keine Erklärungen, kein Markdown. Erfinde keine fehlenden Informationen.\n\nWichtig: Ein einzelnes " oder -"- in einer Tabellen-/Registerspalte ist ein Wiederholungszeichen. Es bedeutet, dass der Wert aus derselben Spalte der vorherigen Zeile erneut gilt. Schreibe den wiederholten Wert aus und gib das Zeichen nicht wörtlich aus. Beispiel: steht unter „Beltzkey“ nur ", dann ist wieder „Beltzkey“ gemeint.'
),
    'ai_prompt_postgresql_user': (
        'Erzeuge aus dem folgenden Text ein PostgreSQL-orientiertes JSON.\nAntworte exakt mit einem JSON-Objekt mit diesen Schlüsseln:\n{schema_template}\n\nText:\n{ocr_text}\n- Include age/age expressions when present in the source text.\n\nWichtig: Ein einzelnes " oder -"- in einer Tabellen-/Registerspalte ist ein Wiederholungszeichen. Es bedeutet, dass der Wert aus derselben Spalte der vorherigen Zeile erneut gilt. Schreibe den wiederholten Wert aus und gib das Zeichen nicht wörtlich aus. Beispiel: steht unter „Beltzkey“ nur ", dann ist wieder „Beltzkey“ gemeint.'
),
    'ai_prompt_neo4j_system': (
        'Du bist ein Graph-Extraktionsassistent für OCR-Texte. Gib ausschließlich gültiges JSON zurück. Erzeuge nur belegte Nodes und Beziehungen. Keine Erklärungen, kein Markdown.\n\nWichtig: Ein einzelnes " oder -"- in einer Tabellen-/Registerspalte ist ein Wiederholungszeichen. Es bedeutet, dass der Wert aus derselben Spalte der vorherigen Zeile erneut gilt. Schreibe den wiederholten Wert aus und gib das Zeichen nicht wörtlich aus. Beispiel: steht unter „Beltzkey“ nur ", dann ist wieder „Beltzkey“ gemeint.'
),
    'ai_prompt_neo4j_user': (
        'Erzeuge aus dem folgenden Text ein Neo4j-orientiertes Graph-JSON.\nAntworte exakt mit einem JSON-Objekt mit diesen Schlüsseln:\n{schema_template}\n\nText:\n{ocr_text}\n- Include age/age expressions when present in the source text.\n\nWichtig: Ein einzelnes " oder -"- in einer Tabellen-/Registerspalte ist ein Wiederholungszeichen. Es bedeutet, dass der Wert aus derselben Spalte der vorherigen Zeile erneut gilt. Schreibe den wiederholten Wert aus und gib das Zeichen nicht wörtlich aus. Beispiel: steht unter „Beltzkey“ nur ", dann ist wieder „Beltzkey“ gemeint.'
),
    'ai_prompt_fullpage_lm_ocr_system': 'Du bist ein präzises OCR-System. Gib ausschließlich gültiges JSON zurück. Erkenne jede Textzeile einzeln in natürlicher Lesereihenfolge. Wiederholungszeichen wie " oder -"- sind Ditto-Zeichen: Sie bedeuten, dass der Wert aus derselben visuellen Spalte der vorherigen Zeile wiederholt wird. Schreibe den wiederholten Wert aus und gib das Zeichen nie wörtlich aus.',
    'ai_prompt_fullpage_lm_ocr_user': 'Führe OCR für die komplette sichtbare Dokumentseite durch. Ignoriere vorhandene Overlay-Boxen. Gib ausschließlich JSON im Format {"lines":[{"text":"..."}]} zurück. Jeder erkannte Eintrag muss eine eigene Zeile sein; keine Absätze zusammenfassen. Wenn " oder -"- in einer Tabellen-/Registerspalte steht, ersetze es durch den Wert aus derselben visuellen Spalte der vorherigen Zeile.',
    'lm_busy_default_message': 'Das lokale Modell arbeitet. Die Dauer hängt vom Modell, der Bildgröße und der Seitenkomplexität ab. Bitte warten.',
    'lm_busy_revision_status': 'Das lokale Modell überarbeitet die Zeilen. Zuerst wird die komplette Seite als Kontext gelesen, danach werden jeweils drei Overlay-Boxen analysiert.',
    'ai_status_step0_fullpage_context': '1/3: Komplette Seite wird nur als Kontext gelesen: {}',
    'lm_prompt_sqlite_system': 'SQLite – System-Prompt',
    'lm_prompt_sqlite_user': 'SQLite – Benutzer-Prompt',
    'prompt_desc_sqlite_system': 'Systemanweisung für die lokale KI zur SQLite-kompatiblen Extraktion von Personen- und Registerdaten.',
    'prompt_desc_sqlite_user': 'Benutzeranweisung für SQLite-Daten: extrahiert Personen, Einträge, Alter, Orte, Jahre und Belege in ein flaches JSON für Tabellen.',
    'ai_prompt_sqlite_system': 'Du bist ein präziser Extraktionsassistent. Erzeuge ausschließlich valides JSON für einen SQLite-Export. Keine Markdown-Erklärung.',
    'ai_prompt_sqlite_user': (
        'Extrahiere aus dem OCR-Text eine SQLite-kompatible Struktur mit documents, persons und entries. Jede erkannte Person/Registrierung soll einen eigenen Eintrag bekommen. Bewahre Namen, Alter, Orte, Jahreszahlen, Datumsangaben und den Originalbeleg. OCR-Text:\n{}'
),
    'busy_queue_ref': 'Wartebereich #{}',
    'warn_gedcom_needs_text_or_image': 'Für die GEDCOM-Erzeugung wird eine geladene Bildseite oder verwertbarer OCR-Text benötigt.',
    'log_gedcom_retry_text_only': 'GEDCOM: Das Modell hat die Bildanfrage nicht akzeptiert. Es wird mit OCR-Text allein erneut versucht.',
    'warn_gedcom_no_output': 'Das lokale Modell hat keinen verwertbaren GEDCOM-Text zurückgegeben.',
    'warn_gedcom_no_person_records': (
        'Die erzeugte GEDCOM-Datei enthält keine sicher erkannten Personendatensätze oder nur einen Platzhalter.\n\nDas kann passieren, wenn das lokale Modell den Eintrag zwar gelesen, aber nicht sauber in GEDCOM-Struktur umgesetzt hat. Du kannst die Datei trotzdem speichern; prüfe und korrigiere sie danach unbedingt in deinem Genealogieprogramm.'
),
    'dlg_gedcom_save_weak_title': 'GEDCOM prüfen',
    'dlg_gedcom_save_weak_question': 'Trotzdem als GEDCOM-Datei speichern?',
    'msg_gedcom_generated_not_saved': 'GEDCOM wurde erzeugt, aber nicht gespeichert.',
    'msg_gedcom_save_dialog_open': 'GEDCOM wurde erzeugt. Bitte Speicherort auswählen.',
    'log_gedcom_not_saved': 'GEDCOM erzeugt, aber nicht gespeichert: {}',
    'log_gedcom_retry_strict': 'GEDCOM-Antwort war nicht importierbar; starte Reparaturversuch mit strenger GEDCOM-Anweisung.',
    'log_gedcom_fallback_note': 'GEDCOM-Fallback erzeugt: Modellantwort wurde als NOTE in eine GEDCOM-Hülle übernommen.',
    'gedcom_fallback_note_title': 'Automatisch erzeugter GEDCOM-Fallback. Das lokale Modell hat keinen sauberen GEDCOM-Text geliefert.',
    'log_gedcom_structured_start': 'GEDCOM: extrahiere strukturierte genealogische Daten aus Bild und OCR-Kontext.',
    'log_gedcom_structured_success': 'GEDCOM: strukturierte Daten erkannt; erzeuge GEDCOM deterministisch.',
    'log_gedcom_structured_fallback': 'GEDCOM: strukturierte Extraktion nicht verwertbar; nutze direkten GEDCOM-Fallback.',
    'lm_prompt_gedcom_extract_system': 'GEDCOM – Datenextraktion empfohlen – System-Prompt',
    'lm_prompt_gedcom_extract_user': 'GEDCOM – Datenextraktion empfohlen – Benutzer-Prompt',
    'ai_prompt_gedcom_extract_system': (
        'Du bist ein präziser genealogischer Extraktionsassistent für historische deutsche Standesamtsformulare, Kirchenbücher und Personenstandsregister.\nDeine Aufgabe ist NICHT, GEDCOM direkt zu schreiben, sondern genealogische Fakten als valides JSON zu extrahieren.\nNutze das Seitenbild als Hauptquelle. OCR-Text ist nur Zusatzkontext und darf fehlerhaft sein.\nBei deutschen Geburtseinträgen ist das Formular typischerweise: Standesamt/Ort, Urkundennummer, Anzeigender, Vater, Mutter, Wohnort, Religion, Geburtsdatum, Geburtszeit, Geschlecht und Kind.\nExtrahiere nur Informationen, die im Bild oder OCR-Kontext erkennbar sind. Erfinde keine Namen.\nWenn eine Lesung unsicher ist, schreibe sie trotzdem in das passende Feld und setze uncertainty auf true.\nAntworte ausschließlich mit JSON. Kein Markdown, keine Erklärung.\n\nWichtig für Registerseiten/Tabellen: Extrahiere nicht nur eine Person. Erzeuge zusätzlich eine Liste `registrations`. Jeder Eintrag entspricht genau einer Zeile/einem Registereintrag mit person.given_names, person.surname, age, event_date, event_place, residence, occupation, notes, source_line und uncertainty. Altersangaben wie Jahre/Monate/Tage müssen erhalten bleiben.\n\nWichtig: Ein einzelnes " oder -"- in einer Tabellen-/Registerspalte ist ein Wiederholungszeichen. Es bedeutet, dass der Wert aus derselben Spalte der vorherigen Zeile erneut gilt. Schreibe den wiederholten Wert aus und gib das Zeichen nicht wörtlich aus. Beispiel: steht unter „Beltzkey“ nur ", dann ist wieder „Beltzkey“ gemeint.'
),
    'ai_prompt_gedcom_extract_user': (
        'Extrahiere aus dieser Seite genealogische Daten als JSON. Nutze vorrangig das Bild; OCR ist nur Hilfe.\n\nGib exakt diese Struktur zurück:\n{{\n  "record_type": "birth|marriage|death|unknown",\n  "registry_place": "",\n  "record_number": "",\n  "entry_date": "",\n  "event_date": "",\n  "event_time": "",\n  "event_place": "",\n  "child": {{"given_names": "", "surname": "", "sex": "M|F|U", "note": ""}},\n  "father": {{"given_names": "", "surname": "", "occupation": "", "residence": "", "religion": "", "note": ""}},\n  "mother": {{"given_names": "", "surname": "", "maiden_surname": "", "occupation": "", "residence": "", "religion": "", "note": ""}},\n  "informant": {{"given_names": "", "surname": "", "occupation": "", "residence": "", "relation": "", "note": ""}},\n  "source_title": "",\n  "transcription_or_notes": "",\n  "uncertainty": true\n}}\n\nSpezialregel für Geburtseinträge: Wenn im Formular steht, dass das Kind noch keinen Vornamen erhalten hat, setze child.given_names auf "Unbenannt" und notiere das in child.note.\nWenn der Familienname des Kindes nicht ausdrücklich steht, aber Vater/Mutter klar sind, darfst du den Familiennamen aus dem Vater ableiten und in child.note als abgeleitet markieren.\n\nOCR-Kontext:\n{}\n\nWichtig für Registerseiten/Tabellen: Extrahiere nicht nur eine Person. Erzeuge zusätzlich eine Liste `registrations`. Jeder Eintrag entspricht genau einer Zeile/einem Registereintrag mit person.given_names, person.surname, age, event_date, event_place, residence, occupation, notes, source_line und uncertainty. Altersangaben wie Jahre/Monate/Tage müssen erhalten bleiben.\n\nWichtig: '
        'Ein einzelnes " oder -"- in einer Tabellen-/Registerspalte ist ein Wiederholungszeichen. Es bedeutet, dass der Wert aus derselben Spalte der vorherigen Zeile erneut gilt. Schreibe den wiederholten Wert aus und gib das Zeichen nicht wörtlich aus. Beispiel: steht unter „Beltzkey“ nur ", dann ist wieder „Beltzkey“ gemeint.'
),
    'dlg_gedcom_review_title': 'GEDCOM prüfen und exportieren',
    'gedcom_review_intro': 'Die GEDCOM-Datei wurde erzeugt. Bitte prüfe die erkannten Daten, korrigiere sie bei Bedarf und exportiere danach die GEDCOM-Datei.',
    'gedcom_review_tab_data': 'Erkannte Daten',
    'gedcom_review_tab_text': 'GEDCOM-Text',
    'gedcom_review_field': 'Feld',
    'gedcom_review_value': 'Wert',
    'gedcom_review_update': 'GEDCOM aus Übersicht aktualisieren',
    'gedcom_review_export': 'GEDCOM exportieren...',
    'gedcom_review_close': 'Schließen',
    'gedcom_review_no_structured': 'Es liegen keine strukturierten Extraktionsdaten vor. Du kannst den GEDCOM-Text im zweiten Reiter direkt bearbeiten und exportieren.',
    'gedcom_review_weak_warning': 'Hinweis: Das erzeugte GEDCOM enthält keine sicheren Personendatensätze oder wurde als Fallback erzeugt. Bitte besonders sorgfältig prüfen.',
    'gedcom_review_update_failed': (
        'Die GEDCOM-Datei konnte aus den bearbeiteten Daten nicht neu erzeugt werden:\n{}'
),
    'gedcom_review_export_empty': 'Der GEDCOM-Text ist leer und kann nicht exportiert werden.',
    'gedcom_review_export_weak': (
        'Der GEDCOM-Text enthält keine eindeutig erkennbaren INDI-Personendatensätze oder wurde als Fallback erzeugt.\n\nTrotzdem exportieren?'
),
    'gedcom_review_export_cancelled': 'GEDCOM wurde erzeugt, aber nicht exportiert.',
    'gedcom_review_export_done': 'GEDCOM-Datei exportiert: {}',
    'gedcom_review_export_failed': (
        'GEDCOM-Datei konnte nicht gespeichert werden:\n{}'
),
    'gedcom_group_general': 'Allgemein',
    'gedcom_group_child': 'Kind / Hauptperson',
    'gedcom_group_father': 'Vater',
    'gedcom_group_mother': 'Mutter',
    'gedcom_group_informant': 'Anzeigende Person',
    'gedcom_field_record_type': 'Art des Eintrags',
    'gedcom_field_registry_place': 'Standesamt / Ort',
    'gedcom_field_record_number': 'Urkundennummer',
    'gedcom_field_entry_date': 'Eintragsdatum',
    'gedcom_field_event_date': 'Ereignisdatum',
    'gedcom_field_event_time': 'Ereigniszeit',
    'gedcom_field_event_place': 'Ereignisort',
    'gedcom_field_source_title': 'Quellentitel',
    'gedcom_field_transcription_or_notes': 'Transkription / Notizen',
    'gedcom_field_uncertainty': 'Unsichere Lesung',
    'gedcom_field_given_names': 'Vorname(n)',
    'gedcom_field_surname': 'Nachname',
    'gedcom_field_maiden_surname': 'Geburtsname / Mädchenname',
    'gedcom_field_sex': 'Geschlecht',
    'gedcom_field_occupation': 'Beruf',
    'gedcom_field_residence': 'Wohnort',
    'gedcom_field_religion': 'Religion',
    'gedcom_field_relation': 'Beziehung',
    'gedcom_field_note': 'Notiz',
    'gedcom_overview_person_count': 'Personendatensätze',
    'gedcom_overview_family_count': 'Familiendatensätze',
    'gedcom_overview_names': 'Namen im GEDCOM',
    'gedcom_group_registrations': 'Registrierungen / Personen',
    'gedcom_registration_selected': 'Exportieren',
    'gedcom_registration_name': 'Name',
    'gedcom_registration_age': 'Alter',
    'gedcom_registration_date': 'Datum/Jahr',
    'gedcom_registration_place': 'Ort',
    'gedcom_registration_note': 'Notiz',
    'dlg_lm_prompts_hint_optimized': 'Wähle links einen Prompt aus. Rechts siehst du eine kurze Erklärung und kannst den Prompt bearbeiten. Für GEDCOM ist normalerweise nur die Datenextraktion wichtig; die direkte GEDCOM-Erzeugung ist nur ein Fallback. Platzhalter wie {} und doppelte JSON-Klammern {{...}} bitte erhalten.',
    'chk_show_advanced_prompts': 'Erweiterte/Fallback-Prompts anzeigen',
    'prompt_group_local_ocr': 'Lokale OCR-/Überarbeitungs-Prompts',
    'prompt_group_gedcom_main': 'GEDCOM – empfohlener Hauptweg',
    'prompt_group_gedcom_fallback': 'GEDCOM – Fallback / direktes GEDCOM',
    'prompt_desc_single_system': 'Systemanweisung für das erneute Lesen einer einzelnen Zeile aus einem kleinen Bildausschnitt.',
    'prompt_desc_single_user': 'Benutzeranweisung für das erneute Lesen einer einzelnen Zeile. Enthält Platzhalter für die Zeilennummer.',
    'prompt_desc_block_system': 'Systemanweisung für kleine Zeilenblöcke, die bei der Überarbeitung mehr Kontext liefern.',
    'prompt_desc_block_user': 'Benutzeranweisung für kleine Zeilenblöcke. Wichtig für markierte Zeilen und Teile der Alle-Zeilen-Überarbeitung.',
    'prompt_desc_page_system': 'Systemanweisung für seitenbezogene Zeilenerkennung mit fester Zeilenzahl.',
    'prompt_desc_page_user': 'Benutzeranweisung für seitenbezogene Zeilenerkennung. Platzhalter und JSON-Struktur müssen erhalten bleiben.',
    'prompt_desc_decision_system': 'Systemanweisung für die Entscheidung zwischen Kraken-OCR, Box-OCR und Seiten-/Block-Kontext.',
    'prompt_desc_decision_user': 'Benutzeranweisung für die finale Entscheidung pro Zeile. Platzhalter müssen erhalten bleiben.',
    'prompt_desc_fullpage_ocr_system': 'Systemanweisung für LM Seiten OCR: Das Vision-Modell liest die komplette Seite ohne vorhandene Overlay-Boxen.',
    'prompt_desc_fullpage_ocr_user': 'Benutzeranweisung für LM Seiten OCR. Das Modell soll reine Zeilen zurückgeben; Overlay-Boxen werden danach bewusst nicht übernommen.',
    'prompt_desc_gedcom_extract_system': 'Wichtigster GEDCOM-Prompt: Das Modell extrahiert genealogische Fakten als JSON. Das Programm baut daraus die GEDCOM-Datei und die Prüfübersicht.',
    'prompt_desc_gedcom_extract_user': 'Wichtigster GEDCOM-Benutzerprompt: Hier legst du fest, welche Felder aus Bild und OCR erkannt werden sollen. Die JSON-Struktur muss erhalten bleiben.',
    'prompt_desc_gedcom_system': 'Fallback-Prompt: Nur Reserve, wenn die strukturierte GEDCOM-Extraktion scheitert. Das Modell soll direkt GEDCOM schreiben.',
    'prompt_desc_gedcom_user': 'Fallback-Benutzerprompt: Nur Reserve. Normalerweise musst du diesen Prompt nicht anpassen.',
    'ditto_instruction_strict': 'Wiederholungszeichen: Ein einzelnes " oder mehrere "" oder -"- bedeuten IMMER Wiederholung aus der vorhergehenden Zeile in derselben Spalte. Es kann Name, Ort, Datum, Jahr, Zahl oder ein anderes Feld sein. Gib solche Zeichen NIE literarisch aus. Beispiel: steht unter/bei Beltzkey nur " oder ""Beltzkey, dann ist Beltzkey als wiederholter Wert zu schreiben.',
    'export_format_docx': 'Word (.docx)',
}
