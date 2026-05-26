"""LM-OCR and page-box translations."""

BK_LM_OCR_TRANSLATIONS = {'de': {'btn_ai_revise_menu_tip': 'Lokales LM: Zeilen überarbeiten, LM Seiten OCR ausführen oder Datenbank-JSON '
                                  'erzeugen',
        'lm_menu_lm_ocr': 'LM Seiten OCR',
        'dlg_ai_ocr_title': 'LM Seiten OCR',
        'dlg_ai_ocr_status': 'Es wird gerade ein kompletter Seiten-OCR mit einem lokalen Modell durchgeführt. '
                             'Vorhandene Overlay-Boxen werden dabei ignoriert. Bitte warten.',
        'msg_ai_ocr_started': 'LM Seiten OCR gestartet...',
        'msg_ai_ocr_done': 'LM Seiten OCR abgeschlossen.',
        'msg_ai_ocr_cancelled': 'LM Seiten OCR abgebrochen.',
        'msg_ai_ocr_failed': 'LM Seiten OCR fehlgeschlagen.',
        'log_ai_ocr_started': 'LM Seiten OCR gestartet: {}',
        'log_ai_ocr_done': 'LM Seiten OCR abgeschlossen: {}',
        'log_ai_ocr_failed': 'LM Seiten OCR Fehler: {} -> {}',
        'warn_need_overlay_boxes_for_lm_ocr': 'Für LM Seiten OCR wird keine Overlay-Box benötigt. Bitte lade oder '
                                              'markiere mindestens eine Bildseite.',
        'ai_status_page_overlay_scan': 'LM Seiten OCR: kompletter Seiten-Scan ohne Overlay-Boxen: {}',
        'ai_status_page_overlay_done': 'LM Seiten OCR abgeschlossen: {}',
        'info_lm_ocr_manual_boxes_hint': 'LM Seiten OCR wurde abgeschlossen. Vorhandene Overlay-Boxen wurden dabei '
                                         'bewusst entfernt. Falls du Zeilenboxen benötigst, kannst du sie per '
                                         'Rechtsklick auf die jeweilige Zeile manuell neu zeichnen.',
        'ai_prompt_fullpage_lm_ocr_system': 'Du bist ein präzises OCR-System. Gib ausschließlich gültiges JSON zurück. '
                                            'Erkenne jede sichtbare Textzeile einzeln in natürlicher Lesereihenfolge. '
                                            'Fasse keine mehreren Zeilen zusammen. Wiederholungszeichen sind '
                                            'ausschließlich echte Anführungszeichen wie " oder "" oder -"-. '
                                            'Punktzeichen, Punktreihen, Auslassungspunkte und Tabellen-Füllpunkte sind '
                                            'NIEMALS Wiederholungszeichen. Ein Wiederholungszeichen bedeutet: Schaue '
                                            'an exakt derselben horizontalen Bildposition eine Zeile darüber und '
                                            'übernimm dort den sinnvollen Wert. Gib das Wiederholungszeichen nie '
                                            'wörtlich aus.',
        'ai_prompt_fullpage_lm_ocr_user': 'Führe OCR für die komplette sichtbare Dokumentseite durch. Ignoriere '
                                          'vorhandene Overlay-Boxen. Gib ausschließlich JSON zurück: '
                                          '{"lines":[{"text":"..."}]}. Jeder sichtbare Eintrag muss eine eigene Zeile '
                                          'sein; keine Absätze zusammenfassen. Wiederholungszeichen sind nur " / "" / '
                                          '-"-. Punkte sind keine Wiederholungszeichen. Ersetze ein '
                                          'Wiederholungszeichen nur durch den Wert, der direkt vertikal darüber in '
                                          'derselben visuellen Spalte steht.',
        'lm_busy_default_message': 'Das lokale Modell arbeitet. Die Dauer hängt vom Modell, der Bildgröße und der '
                                   'Seitenkomplexität ab. Bitte warten.',
        'lm_busy_revision_status': 'Das lokale Modell überarbeitet die Zeilen. Zuerst wird die komplette Seite als '
                                   'Kontext gelesen, danach werden jeweils drei Overlay-Boxen analysiert.',
        'ai_status_step0_fullpage_context': '1/3: Komplette Seite wird nur als Kontext gelesen: {}',
        'ai_prompt_block_page_context_header': 'Kompletter LM-Seiten-OCR als Kontext (nicht als Hauptquelle):',
        'ai_prompt_block_weighting_hint': 'Gewichtung beim Zusammenführen: Kraken-OCR und kompletter LM-Seiten-OCR '
                                          'sind gleichwertige Quellen. Der kleine Overlay-Box-Ausschnitt dient als '
                                          'visuelle Kontrolle. Übernimm den Text, der nach Sanity-Check am '
                                          'vollständigsten ist und keine Namen, Orte, Daten, Altersangaben oder Zahlen '
                                          'verliert.',
        'ai_prompt_block_no_omit_hint': 'Wichtig: Gib jede Zeile vollständig zurück. Kürze nichts. Kein Name, Ort, '
                                        'Datum, Alter, Jahr und keine Zahl darf verschwinden. Kraken-OCR und '
                                        'kompletter LM-Seiten-OCR sind gleichwertige Quellen; entscheide mit '
                                        'Sanity-Check, welcher Text vollständig und plausibel ist.',
        'msg_ocr_cancelled': 'OCR abgebrochen. Das Programm ist wieder bereit.',
        'ai_status_fix46_fullpage_context': '1/3: Kompletter LM-Seiten-OCR wird nur als Kontext gelesen: {}',
        'ai_status_fix46_overlay_line': '2/3: Overlay-Box {}/{} wird mit Kraken-OCR an das lokale Modell gesendet: {}',
        'ai_prompt_overlay_compare_system': 'Du bist ein präziser OCR- und Korrekturassistent. Du erhältst genau einen '
                                            'Bildausschnitt: die Overlay-Box einer einzelnen ausgewählten Zeile. Lies '
                                            'ausschließlich diesen Ausschnitt neu. Vergleiche dein eigenes '
                                            'OCR-Ergebnis mit der vorhandenen Kraken-OCR-Zeile. Kraken-OCR und dein '
                                            'Box-OCR sind gleichwertige Quellen. Ergänze nur fehlende Informationen an '
                                            'der richtigen Position. Kürze niemals Namen, Orte, Daten, Altersangaben '
                                            'oder Zahlen. Gib ausschließlich gültiges JSON zurück: {"text":"..."}.',
        'ai_prompt_overlay_compare_user': 'Zeilen-ID: {}\n'
                                          '\n'
                                          'Vorhandene Kraken-OCR-Zeile:\n'
                                          '{}\n'
                                          '\n'
                                          'Kompletter LM-Seiten-OCR nur als Kontext, nicht als Ersatz:\n'
                                          '{}\n'
                                          '\n'
                                          'Aufgabe:\n'
                                          '1. Lies die übermittelte Overlay-Box selbst neu.\n'
                                          '2. Vergleiche dein Box-OCR mit der Kraken-OCR-Zeile.\n'
                                          '3. Wenn in Kraken etwas fehlt, ergänze es an der passenden Stelle.\n'
                                          '4. Wenn dein Box-OCR unsicher oder kürzer ist, behalte die Kraken-Zeile.\n'
                                          '5. Gib genau eine vollständige Zeile zurück, keine Erklärung, kein '
                                          'Markdown.\n'
                                          '\n'
                                          'Wichtig: Wiederholungszeichen sind nur echte Anführungszeichen wie " oder '
                                          '"" oder -"-. Punkte oder Punktreihen sind keine Wiederholungszeichen. Ein '
                                          'Wiederholungszeichen bedeutet: Wert vertikal darüber an derselben '
                                          'Bildposition übernehmen.',
        'ai_status_fix48_mandatory_page_ocr': '1/6 Pflichtschritt: kompletter LM-Seiten-OCR als Kontext für {0}',
        'export_format_odt': 'LibreOffice Writer (.odt)',
        'msg_odt_export_done': 'ODT exportiert: {}',
        'lm_prompt_sqlite_system': 'SQLite – System-Prompt',
        'lm_prompt_sqlite_user': 'SQLite – Benutzer-Prompt',
        'prompt_desc_sqlite_system': 'Systemanweisung für die lokale KI zur SQLite-kompatiblen Extraktion von '
                                     'Personen- und Registerdaten.',
        'prompt_desc_sqlite_user': 'Benutzeranweisung für SQLite-Daten: extrahiert Personen, Einträge, Alter, Orte, '
                                   'Jahre und Belege in ein flaches JSON für Tabellen.',
        'ai_prompt_sqlite_system': 'Du bist ein präziser Extraktionsassistent. Erzeuge ausschließlich valides JSON für '
                                   'einen SQLite-Export. Keine Markdown-Erklärung.',
        'ai_prompt_sqlite_user': 'Extrahiere aus dem OCR-Text eine SQLite-kompatible Struktur mit documents, persons '
                                 'und entries. Jede erkannte Person/Registrierung soll einen eigenen Eintrag bekommen. '
                                 'Bewahre Namen, Alter, Orte, Jahreszahlen, Datumsangaben und den Originalbeleg. '
                                 'OCR-Text:\n'
                                 '{}',
        'busy_queue_ref': 'Wartebereich #{}'},
 'en': {'btn_ai_revise_menu_tip': 'Local LM: revise lines, run LM Page OCR, or generate database JSON',
        'lm_menu_lm_ocr': 'LM Page OCR',
        'dlg_ai_ocr_title': 'LM Page OCR',
        'dlg_ai_ocr_status': 'A full-page OCR with a local model is currently being performed. Existing overlay boxes '
                             'are ignored. Please wait.',
        'msg_ai_ocr_started': 'LM Page OCR started...',
        'msg_ai_ocr_done': 'LM Page OCR finished.',
        'msg_ai_ocr_cancelled': 'LM Page OCR cancelled.',
        'msg_ai_ocr_failed': 'LM Page OCR failed.',
        'log_ai_ocr_started': 'LM Page OCR started: {}',
        'log_ai_ocr_done': 'LM Page OCR finished: {}',
        'log_ai_ocr_failed': 'LM Page OCR error: {} -> {}',
        'warn_need_overlay_boxes_for_lm_ocr': 'LM Page OCR does not require overlay boxes. Please load or select at '
                                              'least one image page.',
        'ai_status_page_overlay_scan': 'LM Page OCR: full-page scan without overlay boxes: {}',
        'ai_status_page_overlay_done': 'LM Page OCR finished: {}',
        'info_lm_ocr_manual_boxes_hint': 'LM Page OCR has finished. Existing overlay boxes were deliberately removed. '
                                         'If you need line boxes, you can redraw them manually for each line by '
                                         'right-clicking the respective line.',
        'ai_prompt_fullpage_lm_ocr_system': 'You are a precise OCR system. Return valid JSON only. Detect every '
                                            'visible text line separately in natural reading order. Do not merge '
                                            'multiple lines. Ditto marks are only real quotation marks such as " or "" '
                                            'or -"-. Periods, dotted leaders, ellipses and table filler dots are NEVER '
                                            'ditto marks. A ditto mark means: look at exactly the same horizontal '
                                            'image position one line above and copy the meaningful value from there. '
                                            'Never output the ditto mark literally.',
        'ai_prompt_fullpage_lm_ocr_user': 'Run OCR for the complete visible document page. Ignore existing overlay '
                                          'boxes. Return JSON only: {"lines":[{"text":"..."}]}. Every visible entry '
                                          'must be its own line; do not merge entries into paragraphs. Ditto marks are '
                                          'only " / "" / -"-. Periods are not ditto marks. Replace a ditto mark only '
                                          'with the value directly above it in the same visual column.',
        'lm_busy_default_message': 'The local model is working. Duration depends on the model, image size and page '
                                   'complexity. Please wait.',
        'lm_busy_revision_status': 'The local model is revising the lines. First the complete page is read as context, '
                                   'then three overlay boxes at a time are analyzed.',
        'ai_status_step0_fullpage_context': '1/3: Reading the complete page only as context: {}',
        'ai_prompt_block_page_context_header': 'Complete LM page OCR as context only, not as the primary source:',
        'ai_prompt_block_weighting_hint': 'Merge weighting: Kraken OCR and full-page LM OCR are equal sources. The '
                                          'small overlay-box crop is visual evidence. Use the text that wins a sanity '
                                          'check for completeness and does not lose names, places, dates, ages or '
                                          'numbers.',
        'ai_prompt_block_no_omit_hint': 'Important: return every line completely. Do not shorten anything. No name, '
                                        'place, date, age, year or number may disappear. Kraken OCR and full-page LM '
                                        'OCR are equal sources; use a sanity check to decide which text is complete '
                                        'and plausible.',
        'msg_ocr_cancelled': 'OCR cancelled. The program is ready again.',
        'ai_status_fix46_fullpage_context': '1/3: Full-page LM OCR is read as context only: {}',
        'ai_status_fix46_overlay_line': '2/3: Overlay box {}/{} is sent to the local model together with Kraken OCR: '
                                        '{}',
        'ai_prompt_overlay_compare_system': 'You are a precise OCR and correction assistant. You receive exactly one '
                                            'image crop: the overlay box of one selected line. Re-read only this crop. '
                                            'Compare your own OCR result with the existing Kraken OCR line. Kraken OCR '
                                            'and your box OCR are equal sources. Only add missing information at the '
                                            'correct position. Never shorten names, places, dates, ages or numbers. '
                                            'Return valid JSON only: {"text":"..."}.',
        'ai_prompt_overlay_compare_user': 'Line ID: {}\n'
                                          '\n'
                                          'Existing Kraken OCR line:\n'
                                          '{}\n'
                                          '\n'
                                          'Full-page LM OCR as context only, not as replacement:\n'
                                          '{}\n'
                                          '\n'
                                          'Task:\n'
                                          '1. Re-read the transmitted overlay box yourself.\n'
                                          '2. Compare your box OCR with the Kraken OCR line.\n'
                                          '3. If Kraken is missing information, insert it at the correct position.\n'
                                          '4. If your box OCR is uncertain or shorter, keep the Kraken line.\n'
                                          '5. Return exactly one complete line, no explanation, no Markdown.\n'
                                          '\n'
                                          'Important: ditto marks are only real quotation marks such as " or "" or '
                                          '-"-. Dots or dotted runs are not ditto marks. A ditto mark means: copy the '
                                          'value vertically above at the same image position.',
        'ai_status_fix48_mandatory_page_ocr': '1/6 Required step: complete LM page OCR as context for {0}',
        'export_format_odt': 'LibreOffice Writer (.odt)',
        'msg_odt_export_done': 'ODT exported: {}',
        'lm_prompt_sqlite_system': 'SQLite – system prompt',
        'lm_prompt_sqlite_user': 'SQLite – user prompt',
        'prompt_desc_sqlite_system': 'System instruction for local AI extraction of SQLite-compatible person and '
                                     'register data.',
        'prompt_desc_sqlite_user': 'User instruction for SQLite data: extracts persons, entries, ages, places, years '
                                   'and evidence into flat JSON tables.',
        'ai_prompt_sqlite_system': 'You are a precise extraction assistant. Return only valid JSON for an SQLite '
                                   'export. No Markdown explanation.',
        'ai_prompt_sqlite_user': 'Extract an SQLite-compatible structure from the OCR text with documents, persons and '
                                 'entries. Each detected person/registration should get its own record. Preserve '
                                 'names, ages, places, years, dates and original evidence. OCR text:\n'
                                 '{}',
        'busy_queue_ref': 'Queue #{}'},
 'fr': {'btn_ai_revise_menu_tip': 'LM local : réviser les lignes, lancer l’OCR de page LM ou générer un JSON de base '
                                  'de données',
        'lm_menu_lm_ocr': 'OCR de page LM',
        'dlg_ai_ocr_title': 'OCR de page LM',
        'dlg_ai_ocr_status': 'Une OCR complète de la page avec un modèle local est en cours. Les boîtes de '
                             'superposition existantes sont ignorées. Veuillez patienter.',
        'msg_ai_ocr_started': 'OCR de page LM démarré...',
        'msg_ai_ocr_done': 'OCR de page LM terminé.',
        'msg_ai_ocr_cancelled': 'OCR de page LM annulé.',
        'msg_ai_ocr_failed': 'Échec de l’OCR de page LM.',
        'log_ai_ocr_started': 'OCR de page LM démarré : {}',
        'log_ai_ocr_done': 'OCR de page LM terminé : {}',
        'log_ai_ocr_failed': 'Erreur OCR de page LM : {} -> {}',
        'warn_need_overlay_boxes_for_lm_ocr': 'L’OCR de page LM ne nécessite pas de boîtes de superposition. Veuillez '
                                              'charger ou sélectionner au moins une page d’image.',
        'ai_status_page_overlay_scan': 'OCR de page LM : scan complet de la page sans boîtes de superposition : {}',
        'ai_status_page_overlay_done': 'OCR de page LM terminé : {}',
        'info_lm_ocr_manual_boxes_hint': 'L’OCR de page LM est terminé. Les boîtes de superposition existantes ont été '
                                         'volontairement supprimées. Si vous avez besoin de boîtes de lignes, vous '
                                         'pouvez les redessiner manuellement pour chaque ligne par clic droit sur la '
                                         'ligne concernée.',
        'ai_prompt_fullpage_lm_ocr_system': 'Tu es un système OCR précis. Retourne uniquement du JSON valide. Détecte '
                                            'chaque ligne de texte visible séparément dans l’ordre naturel de lecture. '
                                            'Ne fusionne pas plusieurs lignes. Les marques de répétition sont '
                                            'uniquement de vrais guillemets comme " ou "" ou -"-. Les points, lignes '
                                            'pointillées, ellipses et points de remplissage de tableau ne sont JAMAIS '
                                            'des marques de répétition. Une marque de répétition signifie : regarde '
                                            'exactement à la même position horizontale de l’image une ligne au-dessus '
                                            'et copie la valeur pertinente.',
        'ai_prompt_fullpage_lm_ocr_user': 'Effectue l’OCR de toute la page visible. Ignore les boîtes de superposition '
                                          'existantes. Retourne uniquement du JSON : {"lines":[{"text":"..."}]}. '
                                          'Chaque entrée visible doit être une ligne distincte ; ne regroupe pas les '
                                          'entrées en paragraphes. Les marques de répétition sont seulement " / "" / '
                                          '-"-. Les points ne sont pas des marques de répétition. Remplace une marque '
                                          'de répétition uniquement par la valeur située directement au-dessus dans la '
                                          'même colonne visuelle.',
        'lm_busy_default_message': 'Le modèle local travaille. La durée dépend du modèle, de la taille de l’image et '
                                   'de la complexité de la page. Veuillez patienter.',
        'lm_busy_revision_status': 'Le modèle local révise les lignes. La page complète est d’abord lue comme '
                                   'contexte, puis trois boîtes de superposition sont analysées à la fois.',
        'ai_status_step0_fullpage_context': '1/3 : lecture de la page complète uniquement comme contexte : {}',
        'ai_prompt_block_page_context_header': 'OCR de page LM complète utilisée uniquement comme contexte, pas comme '
                                               'source principale :',
        'ai_prompt_block_weighting_hint': 'Pondération de fusion : l’OCR Kraken et l’OCR LM pleine page sont des '
                                          'sources équivalentes. Le petit extrait de boîte de superposition sert de '
                                          'contrôle visuel. Utilise le texte qui réussit le mieux le contrôle de '
                                          'cohérence et ne perd aucun nom, lieu, date, âge ou nombre.',
        'ai_prompt_block_no_omit_hint': 'Important : renvoie chaque ligne entièrement. Ne raccourcis rien. Aucun nom, '
                                        'lieu, date, âge, année ou nombre ne doit disparaître. L’OCR Kraken et l’OCR '
                                        'LM pleine page sont des sources équivalentes ; décide avec un contrôle de '
                                        'cohérence quel texte est complet et plausible.',
        'msg_ocr_cancelled': 'OCR annulé. Le programme est de nouveau prêt.',
        'ai_status_fix46_fullpage_context': '1/3 : l’OCR LM de page complète est lue uniquement comme contexte : {}',
        'ai_status_fix46_overlay_line': '2/3 : la boîte de superposition {}/{} est envoyée au modèle local avec l’OCR '
                                        'Kraken : {}',
        'ai_prompt_overlay_compare_system': 'Tu es un assistant précis d’OCR et de correction. Tu reçois exactement un '
                                            'extrait d’image : la boîte de superposition d’une seule ligne '
                                            'sélectionnée. Relis uniquement cet extrait. Compare ton propre résultat '
                                            'OCR avec la ligne OCR Kraken existante. L’OCR Kraken et ton OCR de boîte '
                                            'sont des sources équivalentes. Ajoute uniquement les informations '
                                            'manquantes à la bonne position. Ne raccourcis jamais les noms, lieux, '
                                            'dates, âges ou nombres. Retourne uniquement du JSON valide : '
                                            '{"text":"..."}.',
        'ai_prompt_overlay_compare_user': 'ID de ligne : {}\n'
                                          '\n'
                                          'Ligne OCR Kraken existante :\n'
                                          '{}\n'
                                          '\n'
                                          'OCR LM de page complète uniquement comme contexte, pas comme remplacement '
                                          ':\n'
                                          '{}\n'
                                          '\n'
                                          'Tâche :\n'
                                          '1. Relis toi-même la boîte de superposition transmise.\n'
                                          '2. Compare ton OCR de boîte avec la ligne OCR Kraken.\n'
                                          '3. Si Kraken manque des informations, insère-les à la bonne position.\n'
                                          '4. Si ton OCR de boîte est incertain ou plus court, conserve la ligne '
                                          'Kraken.\n'
                                          '5. Retourne exactement une ligne complète, sans explication ni Markdown.\n'
                                          '\n'
                                          'Important : les marques de répétition sont uniquement de vrais guillemets '
                                          'comme " ou "" ou -"-. Les points ou suites de points ne sont pas des '
                                          'marques de répétition. Une marque de répétition signifie : copier la valeur '
                                          'située verticalement au-dessus à la même position dans l’image.',
        'ai_status_fix48_mandatory_page_ocr': '1/6 Étape obligatoire : OCR LM complet de la page comme contexte pour '
                                              '{0}',
        'export_format_odt': 'LibreOffice Writer (.odt)',
        'msg_odt_export_done': 'ODT exporté : {}',
        'lm_prompt_sqlite_system': 'SQLite – prompt système',
        'lm_prompt_sqlite_user': 'SQLite – prompt utilisateur',
        'prompt_desc_sqlite_system': 'Instruction système pour l’extraction locale par IA de données de personnes et '
                                     'de registres compatibles SQLite.',
        'prompt_desc_sqlite_user': 'Instruction utilisateur pour SQLite : extrait personnes, entrées, âges, lieux, '
                                   'années et preuves dans des tables JSON plates.',
        'ai_prompt_sqlite_system': 'Tu es un assistant d’extraction précis. Retourne uniquement du JSON valide pour un '
                                   'export SQLite. Aucune explication Markdown.',
        'ai_prompt_sqlite_user': 'Extrais du texte OCR une structure compatible SQLite avec documents, persons et '
                                 'entries. Chaque personne/inscription détectée doit avoir son propre enregistrement. '
                                 'Conserve les noms, âges, lieux, années, dates et le justificatif original. Texte OCR '
                                 ':\n'
                                 '{}',
        'busy_queue_ref': 'File d’attente #{}'}}
