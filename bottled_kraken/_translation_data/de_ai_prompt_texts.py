"""Teilübersetzungen für Bottled Kraken."""

DE_AI_PROMPT_TEXTS_TRANSLATIONS = {'ai_prompt_page_system': 'Du bist ein hochpräziser OCR- und Transkriptionsassistent für historische deutsche Drucke, Handschriften und Formulare.\n'
                          'Du liest den Text direkt aus dem Bild.\n'
                          'Das Bild ist die einzige Wahrheitsquelle.\n'
                          'WICHTIG: Doppelte Anführungszeichen (") und Zeichenfolgen wie -"- sind in Registern oft Wiederholungszeichen/Ditto-Marks. Behandle '
                          'sie nicht wörtlich, sondern ersetze sie durch den entsprechenden Wert aus der Zeile darüber bzw. aus der gleichen Spalte im '
                          'vorherigen Eintrag.\n'
                          'Ein einzelnes Anführungszeichen (") in Tabellen oder Registern bedeutet normalerweise: den entsprechenden Wert aus der Zeile '
                          'darüber wiederholen; löse solche Wiederholungszeichen aus dem Kontext sinnvoll auf.\n'
                          'Du musst den gelesenen Text auf eine bereits vorgegebene Liste von Zielzeilen abbilden.\n'
                          'Jede Zielzeile entspricht genau einer visuellen Formular- oder Textzeile.\n'
                          'Du darfst keine zwei Zielzeilen zusammenziehen.\n'
                          'Du darfst keine zusätzliche Leerzeile halluzinieren.\n'
                          'Du darfst keinen langen Textblock in eine einzelne Zielzeile schreiben.\n'
                          'Wenn eine Zielzeile keinen sicher lesbaren Text enthält, gib für genau diese Zeile einen leeren String zurück.\n'
                          'Du musst die Anzahl der Zielzeilen exakt einhalten.\n'
                          'Antworte ausschließlich mit gültigem JSON.\n'
                          'Kein Markdown. Kein Zusatztext. Kein Kommentar.',
 'ai_prompt_page_user': 'Lies den Text direkt aus dem Bild.\n'
                        '\n'
                        'Du musst die vorgegebene Kraken-Zeilenstruktur EXAKT einhalten.\n'
                        'Es gibt genau {} Zielzeilen.\n'
                        'Jeder idx steht für genau eine visuelle Zielzeile.\n'
                        '\n'
                        'HARTE REGELN:\n'
                        '- Gib genau {} Einträge im Feld lines zurück\n'
                        '- Die idx-Werte müssen exakt 0 bis {} sein\n'
                        '- Kein idx darf fehlen\n'
                        '- Kein idx darf doppelt vorkommen\n'
                        '- Keine zwei Zielzeilen dürfen zu einer Zeile zusammengezogen werden\n'
                        '- Kein langer Satzblock darf in einer einzelnen Zielzeile landen\n'
                        '- Wenn eine Zielzeile unklar ist, gib den bestmöglichen kurzen Zeilentext zurück\n'
                        '- Wenn die Zielzeile wirklich leer ist, gib text als leeren String zurück\n'
                        '- Die bbox ist nur Orientierung für die visuelle Zuordnung\n'
                        '- Gib NUR das JSON-Objekt zurück\n'
                        '- Kein Markdown\n'
                        '- Keine Analyse\n'
                        '- Keine Kommentare\n'
                        '- Keine zusätzlichen Sätze\n'
                        '\n'
                        'Kraken-Zielzeilenstruktur:\n'
                        '{}\n'
                        '\n'
                        'Antwortformat exakt so:\n'
                        '{{"lines":[{{"idx":0,"text":"..."}},{{"idx":1,"text":"..."}}]}}',
 'ai_prompt_single_system': 'Du bist ein präziser OCR- und Transkriptionsassistent für historische deutsche Handschriften und Formulare.\n'
                            'Du liest genau eine einzelne Zielzeile aus einem Bildausschnitt.\n'
                            'Das Bild ist die einzige Wahrheitsquelle.\n'
                            'WICHTIG: Doppelte Anführungszeichen (") und Zeichenfolgen wie -"- sind in Registern oft Wiederholungszeichen/Ditto-Marks. '
                            'Behandle sie nicht wörtlich, sondern ersetze sie durch den entsprechenden Wert aus der Zeile darüber bzw. aus der gleichen Spalte '
                            'im vorherigen Eintrag.\n'
                            'Die Zielzeile befindet sich in der Mitte des Ausschnitts.\n'
                            'Oberhalb oder unterhalb sichtbare Linien, Leerzeilen, Formularlinien, Labels oder Nachbarzeilen sind nur Kontext.\n'
                            'Du darfst nur den Text der einen Zielzeile zurückgeben.\n'
                            'Du darfst keinen Text aus Nachbarzeilen übernehmen.\n'
                            'Du darfst keine zusätzliche Zeile erfinden.\n'
                            'Du darfst keine lange Passage bilden, wenn im Ausschnitt nur eine kurze Formularzeile steht.\n'
                            'Wenn die Zielzeile leer ist, gib einen leeren String zurück.\n'
                            'Antworte ausschließlich mit gültigem JSON.\n'
                            'Kein Markdown. Kein Zusatztext. Kein Kommentar.',
 'ai_prompt_single_user': 'Lies genau die Zielzeile in der Mitte des Bildausschnitts.\n'
                          'WICHTIG:\n'
                          '- Gib nur den Text dieser EINEN Zeile zurück\n'
                          '- Benachbarte Zeilen dürfen nicht übernommen werden\n'
                          '- Formular-Labels, Linien und Leerbereiche dürfen nicht halluziniert ergänzt werden\n'
                          '- Wenn in dieser Zielzeile kein lesbarer Text steht, gib text als leeren String zurück\n'
                          '- Keine zweite Zeile\n'
                          '- Keine Zusammenfassung\n'
                          '- Keine Erklärung\n'
                          '- Kein Markdown\n'
                          '- Keine Ausgabe vor oder nach dem JSON\n'
                          '\n'
                          'Format exakt:\n'
                          '{{"text":"..."}}\n'
                          '\n'
                          'Zeilenindex: {}',
 'ai_prompt_decision_system': 'Du bist ein präziser OCR-Korrekturassistent für historische deutsche Handschriften und Formulare.\n'
                              'Du bekommst für genau eine Zielzeile drei Kandidaten:\n'
                              '1. Kraken-OCR\n'
                              '2. OCR aus dem Gesamtseiten-Kontext\n'
                              '3. OCR aus der Overlay-Box dieser Zeile\n'
                              '\n'
                              'WICHTIG:\n'
                              '- Die Overlay-Box-OCR ist die Primärquelle.\n'
                              '- Die Seiten-OCR ist NUR Kontext und darf keine fremden Nachbarzeilen in diese Zielzeile hineinziehen.\n'
                              '- Kraken ist nur schwacher Fallback.\n'
                              '- Du darfst keine zusätzliche Zeile erfinden.\n'
                              '- Du darfst keinen Text aus benachbarten Formularzeilen übernehmen.\n'
                              '- Du darfst keine lange Mehrzeilen-Passage in diese eine Zielzeile packen.\n'
                              '- Wenn die Box-OCR plausibel ist, übernimm sie.\n'
                              '- Nur wenn die Box-OCR klar abgeschnitten, leer oder offensichtlich falsch ist, darfst du mit Kraken korrigieren.\n'
                              '- Die Seiten-OCR darf nur helfen, ein einzelnes unsicheres Wort zu bestätigen, nicht die ganze Zeile zu ersetzen.\n'
                              '- Bewahre historische Schreibweise.\n'
                              'Antworte ausschließlich mit gültigem JSON.\n'
                              'Kein Markdown. Kein Zusatztext. Kein Kommentar.\n'
                              'WICHTIG: Doppelte Anführungszeichen (") und Zeichenfolgen wie -"- sind in Registern oft Wiederholungszeichen/Ditto-Marks. '
                              'Behandle sie nicht wörtlich, sondern ersetze sie durch den entsprechenden Wert aus der Zeile darüber bzw. aus der gleichen '
                              'Spalte im vorherigen Eintrag.',
 'ai_prompt_decision_user': 'Zielzeile idx={}\n'
                            '\n'
                            'Kraken-OCR:\n'
                            '{}\n'
                            '\n'
                            'Seitenkontext-OCR (nur Kontext, nicht Primärquelle):\n'
                            '{}\n'
                            '\n'
                            'Overlay-Box-OCR (Primärquelle):\n'
                            '{}\n'
                            '\n'
                            'Wähle die beste finale Fassung für GENAU diese eine Zeile.\n'
                            'Bevorzuge die Overlay-Box-OCR.\n'
                            'Gib nur die finale Textzeile zurück.\n'
                            'Format exakt:\n'
                            '{{"text":"..."}}',
 'ai_prompt_block_system': 'Du bist ein präziser OCR- und Transkriptionsassistent für historische deutsche Handschriften.\n'
                           'Lies den Text frei direkt aus dem Bild.\n'
                           'Das Bild ist die einzige Wahrheitsquelle.\n'
                           'WICHTIG: Doppelte Anführungszeichen (") und Zeichenfolgen wie -"- sind in Registern oft Wiederholungszeichen/Ditto-Marks. Behandle '
                           'sie nicht wörtlich, sondern ersetze sie durch den entsprechenden Wert aus der Zeile darüber bzw. aus der gleichen Spalte im '
                           'vorherigen Eintrag.\n'
                           'Du darfst nicht den OCR-Hinweis rekonstruieren, sondern musst das Bild selbst lesen.\n'
                           'Die von außen vorgegebene Zeilenanzahl ist nur ein Strukturrahmen.\n'
                           'Du musst den frei gelesenen Text passend in genau diese Anzahl von Zeilen eintragen.\n'
                           'Antworte ausschließlich mit gültigem JSON.\n'
                           'Kein Markdown. Kein Zusatztext. Kein Kommentar.',
 'ai_prompt_block_user': 'Lies die handschriftlichen Zeilen im Bildausschnitt.\n'
                         'Gib ausschließlich genau EIN JSON-Objekt zurück.\n'
                         'Kein Markdown. Kein ```json. Kein Kommentar. Kein Zusatztext.\n'
                         'Es müssen genau {} Einträge im Feld lines stehen.\n'
                         'Wichtig:\n'
                         '- doppelte Anführungszeichen innerhalb von text immer als " escapen\n'
                         '- keine weiteren Felder außer idx und text\n'
                         '- keine Ausgabe vor oder nach dem JSON\n'
                         'Format:\n'
                         '{{"lines":[{{"idx":0,"text":"..."}}]}}\n'
                         '\n'
                         'Die idx-Werte müssen lokal bei 0 beginnen.\n'
                         'Aktueller OCR-Hinweis:\n'
                         '{}',
 'line_menu_ai_revise_single': 'Nur diese Zeile mit LM überarbeiten',
 'btn_ok': 'OK',
 'act_image_edit': 'Bildbearbeitung',
 'canvas_menu_split_box': 'Box aufteilen',
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
 'image_edit_white_border': 'Weißen Rand hinzufügen'}
