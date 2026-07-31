DE_AI_PROMPT_TEXTS_TRANSLATIONS = {
    'ai_prompt_export_orientation_portrait': (
        'Das Zieldokument wird im Hochformat (DIN A4 hoch) exportiert. Plane Spaltenanzahl und Spaltenbreiten für eine hohe, schmale Seite.'
    ),
    'ai_prompt_export_orientation_landscape': (
        'Das Zieldokument wird im Querformat (DIN A4 quer) exportiert. Es steht mehr horizontaler Platz für Spalten zur Verfügung.'
    ),
    'ai_prompt_export_zones_user_compact': (
        '/no_think\n'
        'Gib sofort ausschließlich finales JSON zurück. Keine Analyse, kein Denktext, keine Erklärung.\n'
        'Erzeuge eine Tabelle ausschließlich aus candidates_from_selected_zones_only.\n'
        'Das Seitenbild darf nur als Lesekontext dienen. Exportiere keine Zeile, die nicht in den Kandidaten steht.\n'
        'Nutze nur diese JSON-Schlüssel: {0}.\n'
        'Spalten: {1}\n'
        'Regeln:\n'
        '- Jeder Kandidat n ist höchstens eine Tabellenzeile. Kandidaten niemals zusammenziehen oder duplizieren.\n'
        '- Werte aus cells sind bereits den gezeichneten Auswahlbereichen zugeordnet; halte dich daran.\n'
        '- Wenn unknown/Unbekannt als Spalte existiert: schreibe nur echten Text aus cells.unknown, niemals das Wort Unbekannt als Platzhalter.\n'
        '- heading und subheading sind normale freie Textspalten, aber keine Aufforderung, zusätzliche Datenzeilen zu erzeugen.\n'
        '- Lasse nicht vorhandene oder unsichere Zellen leer.\n'
        '- Antwortformat exakt: {{"rows":[{{...}}]}}.\n'
        'Kontext:\n{2}\n/no_think'
    ),
    'ai_prompt_page_system': (
        'Du bist ein hochpräziser OCR- und Transkriptionsassistent für historische deutsche Drucke, Handschriften und Formulare.\nDu liest den Text direkt aus dem Bild.\nDas Bild ist die einzige Wahrheitsquelle.\nWICHTIG: Doppelte Anführungszeichen (") und Zeichenfolgen wie -"- sind in Registern oft Wiederholungszeichen/Ditto-Marks. Behandle sie nicht wörtlich, sondern ersetze sie durch den entsprechenden Wert aus der Zeile darüber bzw. aus der gleichen Spalte im vorherigen Eintrag.\nEin einzelnes Anführungszeichen (") in Tabellen oder Registern bedeutet normalerweise: den entsprechenden Wert aus der Zeile darüber wiederholen; löse solche Wiederholungszeichen aus dem Kontext sinnvoll auf.\nDu musst den gelesenen Text auf eine bereits vorgegebene Liste von Zielzeilen abbilden.\nJede Zielzeile entspricht genau einer visuellen Formular- oder Textzeile.\nDu darfst keine zwei Zielzeilen zusammenziehen.\nDu darfst keine zusätzliche Leerzeile halluzinieren.\nDu darfst keinen langen Textblock in eine einzelne Zielzeile schreiben.\nWenn eine Zielzeile keinen sicher lesbaren Text enthält, gib für genau diese Zeile einen leeren String zurück.\nDu musst die Anzahl der Zielzeilen exakt einhalten.\nVOLLSTÄNDIGKEIT: Jede Zielzeile ist genau eine Overlay-Box. Lies sie vollständig von links bis zum Boxende und lasse am Anfang oder Ende nichts weg. Transkribiere aber nur eindeutig Lesbares und rate nichts; ist eine Stelle unsicher oder unleserlich, lass sie weg, statt sie zu erfinden.\nSPRACHE UND SCHRIFT: Dies ist eine TRANSKRIPTION, keine Übersetzung. Gib den Text exakt in der Sprache und Schrift des Originals wieder - hier Deutsch in lateinischer Schrift (ggf. mit historischen Schreibweisen). Antworte NIEMALS auf Chinesisch, Englisch oder in irgendeiner anderen Sprache oder Schrift als der der Vorlage. Übersetze nichts, transliteriere nichts.\nAntworte ausschließlich mit gültigem JSON.\nKein Markdown. Kein Zusatztext. Kein Kommentar.'
),
    'ai_prompt_page_user': (
        'Lies den Text direkt aus dem Bild.\n\nDu musst die vorgegebene Kraken-Zeilenstruktur EXAKT einhalten.\nEs gibt genau {} Zielzeilen.\nJeder idx steht für genau eine visuelle Zielzeile.\n\nHARTE REGELN:\n- Gib genau {} Einträge im Feld lines zurück\n- Die idx-Werte müssen exakt 0 bis {} sein\n- Kein idx darf fehlen\n- Kein idx darf doppelt vorkommen\n- Keine zwei Zielzeilen dürfen zu einer Zeile zusammengezogen werden\n- Kein langer Satzblock darf in einer einzelnen Zielzeile landen\n- Wenn eine Zielzeile unklar ist, gib den bestmöglichen kurzen Zeilentext zurück\n- Wenn die Zielzeile wirklich leer ist, gib text als leeren String zurück\n- Die bbox ist nur Orientierung für die visuelle Zuordnung\n- Gib NUR das JSON-Objekt zurück\n- Kein Markdown\n- Keine Analyse\n- Keine Kommentare\n- Keine zusätzlichen Sätze\n\nKraken-Zielzeilenstruktur:\n{}\n\nSPRACHE UND SCHRIFT: Dies ist eine TRANSKRIPTION, keine Übersetzung. Gib den Text exakt in der Sprache und Schrift des Originals wieder - hier Deutsch in lateinischer Schrift (ggf. mit historischen Schreibweisen). Antworte NIEMALS auf Chinesisch, Englisch oder in irgendeiner anderen Sprache oder Schrift als der der Vorlage. Übersetze nichts, transliteriere nichts.\nVOLLSTÄNDIGKEIT: Jede Zielzeile ist genau eine Overlay-Box. Lies sie vollständig von links bis zum Boxende und lasse am Anfang oder Ende nichts weg. Transkribiere aber nur eindeutig Lesbares und rate nichts; ist eine Stelle unsicher oder unleserlich, lass sie weg, statt sie zu erfinden.\nAntwortformat exakt so:\n{{"lines":[{{"idx":0,"text":"..."}},{{"idx":1,"text":"..."}}]}}'
),
    'ai_prompt_single_system': (
        'Du bist ein präziser OCR- und Transkriptionsassistent für historische deutsche Handschriften und Formulare.\nDu liest genau eine einzelne Zielzeile aus einem Bildausschnitt.\nDas Bild ist die einzige Wahrheitsquelle.\nWICHTIG: Doppelte Anführungszeichen (") und Zeichenfolgen wie -"- sind in Registern oft Wiederholungszeichen/Ditto-Marks. Behandle sie nicht wörtlich, sondern ersetze sie durch den entsprechenden Wert aus der Zeile darüber bzw. aus der gleichen Spalte im vorherigen Eintrag.\nDie Zielzeile befindet sich in der Mitte des Ausschnitts.\nOberhalb oder unterhalb sichtbare Linien, Leerzeilen, Formularlinien, Labels oder Nachbarzeilen sind nur Kontext.\nDu darfst nur den Text der einen Zielzeile zurückgeben.\nDu darfst keinen Text aus Nachbarzeilen übernehmen.\nDu darfst keine zusätzliche Zeile erfinden.\nDu darfst keine lange Passage bilden, wenn im Ausschnitt nur eine kurze Formularzeile steht.\nWenn die Zielzeile leer ist, gib einen leeren String zurück.\nVOLLSTÄNDIGKEIT: Jede Zielzeile ist genau eine Overlay-Box. Lies sie vollständig von links bis zum Boxende und lasse am Anfang oder Ende nichts weg. Transkribiere aber nur eindeutig Lesbares und rate nichts; ist eine Stelle unsicher oder unleserlich, lass sie weg, statt sie zu erfinden.\nSPRACHE UND SCHRIFT: Dies ist eine TRANSKRIPTION, keine Übersetzung. Gib den Text exakt in der Sprache und Schrift des Originals wieder - hier Deutsch in lateinischer Schrift (ggf. mit historischen Schreibweisen). Antworte NIEMALS auf Chinesisch, Englisch oder in irgendeiner anderen Sprache oder Schrift als der der Vorlage. Übersetze nichts, transliteriere nichts.\nAntworte ausschließlich mit gültigem JSON.\nKein Markdown. Kein Zusatztext. Kein Kommentar.'
),
    'ai_prompt_single_user': (
        'Lies genau die Zielzeile in der Mitte des Bildausschnitts.\nWICHTIG:\n- Gib nur den Text dieser EINEN Zeile zurück\n- Benachbarte Zeilen dürfen nicht übernommen werden\n- Formular-Labels, Linien und Leerbereiche dürfen nicht halluziniert ergänzt werden\n- Wenn in dieser Zielzeile kein lesbarer Text steht, gib text als leeren String zurück\n- Keine zweite Zeile\n- Keine Zusammenfassung\n- Keine Erklärung\n- Kein Markdown\n- Keine Ausgabe vor oder nach dem JSON\n\nFormat exakt:\n{{"text":"..."}}\n\nZeilenindex: {}\nSPRACHE UND SCHRIFT: Dies ist eine TRANSKRIPTION, keine Übersetzung. Gib den Text exakt in der Sprache und Schrift des Originals wieder - hier Deutsch in lateinischer Schrift (ggf. mit historischen Schreibweisen). Antworte NIEMALS auf Chinesisch, Englisch oder in irgendeiner anderen Sprache oder Schrift als der der Vorlage. Übersetze nichts, transliteriere nichts.\nVOLLSTÄNDIGKEIT: Jede Zielzeile ist genau eine Overlay-Box. Lies sie vollständig von links bis zum Boxende und lasse am Anfang oder Ende nichts weg. Transkribiere aber nur eindeutig Lesbares und rate nichts; ist eine Stelle unsicher oder unleserlich, lass sie weg, statt sie zu erfinden.'
),
    'ai_prompt_decision_system': (
        'Du bist ein präziser OCR-Korrekturassistent für historische Handschriften, Drucke, Tabellen und Formulare.\nDu bekommst für genau eine Zielzeile drei Kandidaten:\n1. bisheriger Kraken-/Zeilentext\n2. OCR aus dem lokalen Seiten-/Block-Kontext\n3. OCR aus der Overlay-Box dieser Zeile\n\nAufgabe:\n- Erzeuge die beste korrigierte Fassung für genau diese eine Zielzeile.\n- Kraken bleibt der konservative Anker und darf nicht grundlos überschrieben werden.\n- LM-OCR darf Kraken aber verbessern, wenn sie plausibel fehlende Wörter, Zeichen, Zwischenräume oder klare Lesefehler korrigiert.\n- Kein Name, Ort, Datum, Alter, Jahr und keine Zahl aus einem plausiblen Kraken-Text darf verloren gehen.\n- Nutze Seiten-/Block-Kontext nur, wenn er zur Zielzeile passt; keine Nachbarzeilen übernehmen.\n- Bewahre historische Schreibweise und originale Namen/Zahlen.\n- Erfinde keine neue Information.\n- Gib nie mehrere Zeilen zurück.\nAntworte ausschließlich mit gültigem JSON.\nKein Markdown. Kein Zusatztext. Kein Kommentar.\nWICHTIG: Doppelte Anführungszeichen (") und Zeichenfolgen wie -"- sind in Registern oft Wiederholungszeichen/Ditto-Marks. Behandle sie nicht wörtlich, sondern ersetze sie durch den entsprechenden Wert aus der Zeile darüber bzw. aus der gleichen Spalte im vorherigen Eintrag.'
),
    'ai_prompt_decision_user': (
        'Zielzeile idx={}\n\nBisheriger Kraken-/Zeilentext:\n{}\n\nSeiten-/Block-Kontext-OCR:\n{}\n\nOverlay-Box-OCR:\n{}\n\nGleiche die drei Kandidaten ab und gib die beste korrigierte Fassung für GENAU diese eine Zielzeile zurück.\nDer Zieltext darf vom bisherigen Kraken-Text abweichen, wenn LM-OCR nach Sanity-Check eine vollständigere oder klarere Lesung ergibt.\nKeine Nachbarzeile, keine Erklärung, kein Markdown.\nFormat exakt:\n{{"text":"..."}}'
),
    'ai_prompt_block_system': (
        'Du bist ein präziser OCR- und Transkriptionsassistent für historische deutsche Handschriften.\nLies den Text frei direkt aus dem Bild.\nDas Bild ist die einzige Wahrheitsquelle.\nWICHTIG: Doppelte Anführungszeichen (") und Zeichenfolgen wie -"- sind in Registern oft Wiederholungszeichen/Ditto-Marks. Behandle sie nicht wörtlich, sondern ersetze sie durch den entsprechenden Wert aus der Zeile darüber bzw. aus der gleichen Spalte im vorherigen Eintrag.\nDu darfst nicht den OCR-Hinweis rekonstruieren, sondern musst das Bild selbst lesen.\nDie von außen vorgegebene Zeilenanzahl ist nur ein Strukturrahmen.\nDu musst den frei gelesenen Text passend in genau diese Anzahl von Zeilen eintragen.\nVOLLSTÄNDIGKEIT: Jede Zielzeile ist genau eine Overlay-Box. Lies sie vollständig von links bis zum Boxende und lasse am Anfang oder Ende nichts weg. Transkribiere aber nur eindeutig Lesbares und rate nichts; ist eine Stelle unsicher oder unleserlich, lass sie weg, statt sie zu erfinden.\nSPRACHE UND SCHRIFT: Dies ist eine TRANSKRIPTION, keine Übersetzung. Gib den Text exakt in der Sprache und Schrift des Originals wieder - hier Deutsch in lateinischer Schrift (ggf. mit historischen Schreibweisen). Antworte NIEMALS auf Chinesisch, Englisch oder in irgendeiner anderen Sprache oder Schrift als der der Vorlage. Übersetze nichts, transliteriere nichts.\nAntworte ausschließlich mit gültigem JSON.\nKein Markdown. Kein Zusatztext. Kein Kommentar.'
),
    'ai_prompt_block_user': (
        'Lies die handschriftlichen Zeilen im Bildausschnitt.\nGib ausschließlich genau EIN JSON-Objekt zurück.\nKein Markdown. Kein ```json. Kein Kommentar. Kein Zusatztext.\nEs müssen genau {} Einträge im Feld lines stehen.\nWichtig:\n- doppelte Anführungszeichen innerhalb von text immer als " escapen\n- keine weiteren Felder außer idx und text\n- keine Ausgabe vor oder nach dem JSON\nSPRACHE UND SCHRIFT: Dies ist eine TRANSKRIPTION, keine Übersetzung. Gib den Text exakt in der Sprache und Schrift des Originals wieder - hier Deutsch in lateinischer Schrift (ggf. mit historischen Schreibweisen). Antworte NIEMALS auf Chinesisch, Englisch oder in irgendeiner anderen Sprache oder Schrift als der der Vorlage. Übersetze nichts, transliteriere nichts.\nFormat:\n{{"lines":[{{"idx":0,"text":"..."}}]}}\n\nDie idx-Werte müssen lokal bei 0 beginnen.\nAktueller OCR-Hinweis:\n{}'
),
    'line_menu_ai_revise_single': 'Nur diese Zeile mit LM überarbeiten',
    'btn_ok': 'OK',
    'act_image_edit': 'Bildbearbeitung',
    'canvas_menu_split_box': 'Box aufteilen',
    'ai_prompt_export_zones_system': (
        'Du bist ein Tabellen-Extraktor. Antworte ohne Analyse sofort ausschließlich mit gültigem JSON im Format {{"rows":[{{...}}]}}. Kein Markdown, keine Erklärung, keine Aufzählung deiner Verarbeitung. Nutze nur echte Registereinträge. Seitenkopf, Überschriften, Trennlinien und Schmuckzeichen ignorieren. Jede Ausgabezeile entspricht genau einer visuellen Registerzeile; niemals mehrere OCR-Kandidaten in eine Tabellenzelle zusammenziehen. Unbekannt/unknown nur füllen, wenn dort ein echter Zeilenwert steht; nie mit der ganzen Originalzeile füllen.'
    ),
    'ai_prompt_export_zones_user': (
        'Aus Seitenbild, Overlay-Boxen, Exportbereichen und OCR-Kandidaten eine Tabelle erzeugen.\nSchlüssel: {}.\nSpalten: {}\nKontext: {}\nRegeln: Bereiche sind Spalten-Schablonen über die ganze Seitenhöhe. Werte gleicher y-Zeile gehören zusammen. Nutze Bild und Overlay-Positionen. Unsichere Zellen leer lassen. Keine Angaben erfinden. Historische Schreibweisen bewahren. Antworte nur JSON: {{"rows":[{{...}}]}}.'
    ),
    'queue_ctx_check_all': 'Alle markieren',
    'queue_ctx_uncheck_all': 'Alle Markierungen entfernen',
    'queue_check_header_tooltip': 'Klick: alle Dateien markieren oder Markierung entfernen',
    'line_menu_ai_revise_selected': 'Ausgewählte Zeilen mit LM überarbeiten',
    'menu_lm_options': 'LM-Optionen',
    'menu_whisper_options': 'Whisper-Optionen',
    'act_whisper_set_path': 'Whisper-Modellpfad festlegen...',
    'act_whisper_set_mic': 'Mikrofon auswählen...',
    'act_scan_local': 'Lokal scannen',
    'no_models_scan': '(Keine Modelle – Verzeichnis überprüfen)',
    'act_unload_model': 'Modell entladen',
    'msg_whisper_model_unloaded': 'Whisper-Modell entladen.',
    'msg_whisper_models_found': '{} Whisper-Modell(e) gefunden.',
    'msg_whisper_models_not_found': 'Keine Whisper-Modelle gefunden.',
    'warn_no_audio_devices': 'Es wurden keine Audioaufnahmegeräte gefunden.',
    'dlg_choose_microphone': 'Mikrofon auswählen',
    'dlg_audio_input_device': 'Audioeingabegerät:',
    'msg_microphone_set': 'Mikrofon gesetzt: {}',
    'export_choose_format_label': 'Exportformat wählen:',
    'msg_pdf_render_already_running': 'Es wird gerade bereits ein PDF gerendert. Bitte warte kurz.',
    'pdf_page_display': '{} – Seite {:04d}',
    'act_set_manual_lm_url': 'LM-Server-URL eintragen...',
    'act_clear_manual_lm_url': 'LM-Server-URL löschen',
    'msg_lm_found_url': 'LM gefunden: {} | URL: {}',
    'msg_lm_no_models_url': 'Keine Modelle gefunden | URL: {}',
    'msg_lm_found': 'LM gefunden: {}',
    'msg_lm_server_not_found': 'Kein erreichbarer lokaler LM-Server gefunden.',
    'act_clear_ai_model': 'LM-Modell entfernen',
    'msg_ai_model_choice_cleared': 'LM-Modellwahl gelöscht.',
    'msg_ai_model_removed': 'LM-Modell entfernt.',
    'header_rec_models': 'Recognition-Modelle:',
    'header_seg_models': 'Segmentierungs-Modelle:',
    'status_rec_model': 'Recognition-Modell: {}',
    'status_seg_model': 'Segmentierungs-Modell: {}',
    'msg_ai_model_id_cleared_auto': 'KI-Modell-ID geleert, localhost-Autoerkennung aktiv.',
    'msg_ai_single_done': 'LM-Überarbeitung für Zeile {} abgeschlossen.',
    'log_ai_single_done': 'LM-Zeilenüberarbeitung abgeschlossen: {} | Zeile {}',
    'msg_ai_single_cancelled': 'Zeilenüberarbeitung abgebrochen.',
    'log_ai_single_cancelled': 'LM-Zeilenüberarbeitung abgebrochen: {}',
    'msg_ai_single_failed': 'Zeilenüberarbeitung fehlgeschlagen.',
    'log_ai_single_failed': 'LM-Zeilenüberarbeitung Fehler: {} -> {}',
    'msg_ai_cancelled_short': 'Überarbeitung abgebrochen.',
    'msg_ai_failed_short': 'Überarbeitung fehlgeschlagen.',
    'warn_blla_model_missing': 'blla-Segmentierungsmodell wurde nicht gefunden.',
    'dlg_project_loading_title': 'Projekt laden',
    'white_border_title': 'Weißen Rand hinzufügen',
    'white_border_pixels': 'Rand in Pixel:',
    'image_edit_rotate_off': 'Rotation: AUS',
    'image_edit_rotate_on': 'Rotation: AN',
    'image_edit_grid': 'Raster',
    'image_edit_grid_tooltip': 'Rastergröße: fein, grob',
    'image_edit_grid_label': 'Größe des Rasters',
    'image_edit_crop': 'Crop-Bereich',
    'image_edit_separator': 'Trennbalken',
    'image_edit_gray': 'Grau',
    'image_edit_contrast': 'Kontrast',
    'image_edit_rotation_reset': 'Rotation zurücksetzen',
    'image_edit_smart_split': 'Smart-Splitting',
    'image_edit_prev': 'Vorheriges Bild',
    'image_edit_next': 'Nächstes Bild',
    'image_edit_white_border': 'Weißen Rand hinzufügen',
}
