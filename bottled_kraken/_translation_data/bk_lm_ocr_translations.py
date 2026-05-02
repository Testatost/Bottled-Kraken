"""Ausgelagerte Übersetzungen für LM-Seiten-OCR."""

BK_LM_OCR_TRANSLATIONS = {'de': {'btn_ai_revise_menu_tip': 'Lokales LM: Zeilen überarbeiten, LM Seiten OCR ausführen oder '
                                  'Datenbank-JSON erzeugen',
        'lm_menu_lm_ocr': 'LM Seiten OCR',
        'dlg_ai_ocr_title': 'LM Seiten OCR',
        'dlg_ai_ocr_status': 'Es wird gerade ein kompletter Seiten-OCR mit einem lokalen Modell '
                             'durchgeführt. Vorhandene Overlay-Boxen werden dabei ignoriert. Bitte '
                             'warten.',
        'msg_ai_ocr_started': 'LM Seiten OCR gestartet...',
        'msg_ai_ocr_done': 'LM Seiten OCR abgeschlossen.',
        'msg_ai_ocr_cancelled': 'LM Seiten OCR abgebrochen.',
        'msg_ai_ocr_failed': 'LM Seiten OCR fehlgeschlagen.',
        'log_ai_ocr_started': 'LM Seiten OCR gestartet: {}',
        'log_ai_ocr_done': 'LM Seiten OCR abgeschlossen: {}',
        'log_ai_ocr_failed': 'LM Seiten OCR Fehler: {} -> {}',
        'warn_need_overlay_boxes_for_lm_ocr': 'Für LM Seiten OCR wird keine Overlay-Box benötigt. '
                                              'Bitte lade oder markiere mindestens eine Bildseite.',
        'ai_status_page_overlay_scan': 'LM Seiten OCR: kompletter Seiten-Scan ohne Overlay-Boxen: '
                                       '{}',
        'ai_status_page_overlay_done': 'LM Seiten OCR abgeschlossen: {}',
        'info_lm_ocr_manual_boxes_hint': 'LM Seiten OCR wurde abgeschlossen. Vorhandene '
                                         'Overlay-Boxen wurden dabei bewusst entfernt. Falls du '
                                         'Zeilenboxen benötigst, kannst du sie per Rechtsklick '
                                         'auf die jeweilige Zeile manuell neu zeichnen.',
        'ai_prompt_fullpage_lm_ocr_system': 'Du bist ein präzises OCR-System für historische und '
                                            'moderne Dokumentseiten. Erkenne Textzeilen in '
                                            'natürlicher Lesereihenfolge. Gib ausschließlich '
                                            'gültiges JSON zurück.',
        'ai_prompt_fullpage_lm_ocr_user': 'Führe OCR für die komplette sichtbare Dokumentseite '
                                          'durch. Ignoriere vorhandene Overlay-Boxen oder '
                                          'Segmentierungen vollständig. Lege die Textzeilen selbst '
                                          'fest und gib sie in natürlicher Lesereihenfolge zurück. '
                                          'Gib ausschließlich JSON im Format '
                                          '{"lines":[{"text":"..."}]} zurück. Keine Koordinaten, '
                                          'keine Boxen, keine Erklärungen, kein Markdown.'},
 'en': {'btn_ai_revise_menu_tip': 'Local LM: revise lines, run LM Page OCR, or generate database '
                                  'JSON',
        'lm_menu_lm_ocr': 'LM Page OCR',
        'dlg_ai_ocr_title': 'LM Page OCR',
        'dlg_ai_ocr_status': 'A full-page OCR with a local model is currently being performed. '
                             'Existing overlay boxes are ignored. Please wait.',
        'msg_ai_ocr_started': 'LM Page OCR started...',
        'msg_ai_ocr_done': 'LM Page OCR finished.',
        'msg_ai_ocr_cancelled': 'LM Page OCR cancelled.',
        'msg_ai_ocr_failed': 'LM Page OCR failed.',
        'log_ai_ocr_started': 'LM Page OCR started: {}',
        'log_ai_ocr_done': 'LM Page OCR finished: {}',
        'log_ai_ocr_failed': 'LM Page OCR error: {} -> {}',
        'warn_need_overlay_boxes_for_lm_ocr': 'LM Page OCR does not require overlay boxes. Please '
                                              'load or select at least one image page.',
        'ai_status_page_overlay_scan': 'LM Page OCR: full-page scan without overlay boxes: {}',
        'ai_status_page_overlay_done': 'LM Page OCR finished: {}',
        'info_lm_ocr_manual_boxes_hint': 'LM Page OCR has finished. Existing overlay boxes were '
                                         'deliberately removed. If you need line boxes, you can '
                                         'redraw them manually for each line by right-clicking '
                                         'the respective line.',
        'ai_prompt_fullpage_lm_ocr_system': 'You are a precise OCR system for historical and '
                                            'modern document pages. Detect text lines in natural '
                                            'reading order. Return valid JSON only.',
        'ai_prompt_fullpage_lm_ocr_user': 'Perform OCR on the complete visible document page. '
                                          'Ignore existing overlay boxes or segmentations '
                                          'completely. Determine the text lines yourself and '
                                          'return them in natural reading order. Return only JSON '
                                          'in the format {"lines":[{"text":"..."}]}. No '
                                          'coordinates, no boxes, no explanations, no Markdown.'},
 'fr': {'btn_ai_revise_menu_tip': 'LM local : réviser les lignes, lancer l’OCR de page LM ou '
                                  'générer un JSON de base de données',
        'lm_menu_lm_ocr': 'OCR de page LM',
        'dlg_ai_ocr_title': 'OCR de page LM',
        'dlg_ai_ocr_status': 'Une OCR complète de la page avec un modèle local est en cours. Les '
                             'boîtes de superposition existantes sont ignorées. Veuillez '
                             'patienter.',
        'msg_ai_ocr_started': 'OCR de page LM démarré...',
        'msg_ai_ocr_done': 'OCR de page LM terminé.',
        'msg_ai_ocr_cancelled': 'OCR de page LM annulé.',
        'msg_ai_ocr_failed': 'Échec de l’OCR de page LM.',
        'log_ai_ocr_started': 'OCR de page LM démarré : {}',
        'log_ai_ocr_done': 'OCR de page LM terminé : {}',
        'log_ai_ocr_failed': 'Erreur OCR de page LM : {} -> {}',
        'warn_need_overlay_boxes_for_lm_ocr': 'L’OCR de page LM ne nécessite pas de boîtes de '
                                              'superposition. Veuillez charger ou sélectionner au '
                                              'moins une page d’image.',
        'ai_status_page_overlay_scan': 'OCR de page LM : scan complet de la page sans boîtes de '
                                       'superposition : {}',
        'ai_status_page_overlay_done': 'OCR de page LM terminé : {}',
        'info_lm_ocr_manual_boxes_hint': 'L’OCR de page LM est terminé. Les boîtes de '
                                         'superposition existantes ont été volontairement '
                                         'supprimées. Si vous avez besoin de boîtes de lignes, '
                                         'vous pouvez les redessiner manuellement pour chaque '
                                         'ligne par clic droit sur la ligne concernée.',
        'ai_prompt_fullpage_lm_ocr_system': 'Vous êtes un système OCR précis pour des pages de '
                                            'documents historiques et modernes. Détectez les '
                                            'lignes de texte dans l’ordre naturel de lecture. '
                                            'Répondez uniquement avec du JSON valide.',
        'ai_prompt_fullpage_lm_ocr_user': 'Effectuez l’OCR de toute la page de document visible. '
                                          'Ignorez complètement les boîtes de superposition ou '
                                          'segmentations existantes. Déterminez vous-même les '
                                          'lignes de texte et renvoyez-les dans l’ordre naturel de '
                                          'lecture. Répondez uniquement au format JSON '
                                          '{"lines":[{"text":"..."}]}. Pas de coordonnées, pas de '
                                          'boîtes, pas d’explications, pas de Markdown.'}}
