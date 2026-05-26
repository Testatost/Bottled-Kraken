"""Übersetzungen für lokale LM-Token- und Prompt-Optionen."""

BK_LM_OPTIONS_TRANSLATIONS = {'de': {'act_lm_token_settings': 'Token-Anzahl für lokale Modelle einstellen',
        'act_lm_prompt_settings': 'Prompts für lokale KI bearbeiten',
        'dlg_lm_token_title': 'Lokale LM-Token einstellen',
        'dlg_lm_token_hint': 'Diese Werte steuern die maximale Antwortlänge der lokalen KI für die jeweiligen '
                             'LM-Funktionen.',
        'lm_token_current_line': 'Aktuelle Zeile überarbeiten',
        'lm_token_selected_lines': 'Markierte Zeilen überarbeiten',
        'lm_token_all_lines': 'Alle Zeilen überarbeiten',
        'lm_token_lm_ocr': 'LM Seiten OCR',
        'lm_token_gedcom': 'GEDCOM erzeugen',
        'btn_restore_defaults': 'Standardwerte',
        'msg_lm_tokens_saved': 'Lokale LM-Token gespeichert.',
        'dlg_lm_prompts_title': 'Prompts für lokale KI bearbeiten',
        'dlg_lm_prompts_hint': 'Wähle links einen Prompt aus, bearbeite ihn rechts und speichere die Änderungen. '
                               'Platzhalter wie {} und doppelte JSON-Klammern {{...}} bitte erhalten.',
        'lm_prompt_single_system': 'Aktuelle Zeile – System-Prompt',
        'lm_prompt_single_user': 'Aktuelle Zeile – Benutzer-Prompt',
        'lm_prompt_block_system': 'Markierte/Alle Zeilen – Block-System-Prompt',
        'lm_prompt_block_user': 'Markierte/Alle Zeilen – Block-Benutzer-Prompt',
        'lm_prompt_page_system': 'Alle Zeilen – Seiten-System-Prompt',
        'lm_prompt_page_user': 'Alle Zeilen – Seiten-Benutzer-Prompt',
        'lm_prompt_decision_system': 'Alle Zeilen – Entscheidungs-System-Prompt',
        'lm_prompt_decision_user': 'Alle Zeilen – Entscheidungs-Benutzer-Prompt',
        'lm_prompt_fullpage_ocr_system': 'LM Seiten OCR – System-Prompt',
        'lm_prompt_fullpage_ocr_user': 'LM Seiten OCR – Benutzer-Prompt',
        'lm_prompt_gedcom_system': 'GEDCOM – System-Prompt',
        'lm_prompt_gedcom_user': 'GEDCOM – Benutzer-Prompt',
        'btn_save': 'Speichern',
        'btn_close': 'Schließen',
        'btn_reset_selected_prompt': 'Ausgewählten Prompt zurücksetzen',
        'btn_reset_all_prompts': 'Alle Prompts zurücksetzen',
        'msg_lm_prompts_saved': 'Lokale KI-Prompts gespeichert.',
        'msg_lm_prompt_reset': 'Prompt wurde auf den Ausgangsprompt zurückgesetzt.',
        'msg_lm_prompts_reset_all': 'Alle lokalen KI-Prompts wurden auf die Ausgangsprompts zurückgesetzt.',
        'help_nav_overview': 'Übersicht',
        'help_h1_overview': 'Übersicht',
        'act_lm_custom_context': 'Vorgaben / Listen / Kontext',
        'dlg_lm_custom_context_title': 'Vorgaben / Listen / Kontext',
        'dlg_lm_custom_context_hint': 'Hier können optionale Referenzlisten und Vorgaben hinterlegt werden, z. B. '
                                      'Familiennamen, Ortsnamen, typische Berufsbezeichnungen oder Abkürzungen. Diese '
                                      'Angaben werden automatisch an die Benutzer-Prompts der lokalen KI angehängt.',
        'dlg_lm_custom_context_placeholder': 'Beispiel:\n'
                                             'Familiennamen: Müller, Schmidt, Hoffmann\n'
                                             'Orte: Leipzig, Markranstädt, Taucha\n'
                                             'Hinweise: lange s-Schreibung beachten; lateinische Monatsnamen möglich',
        'btn_clear': 'Leeren',
        'msg_lm_custom_context_saved': 'KI-Vorgaben gespeichert.',
        'msg_lm_custom_context_cleared': 'KI-Vorgaben geleert.',
        'lm_custom_context_appendix': 'Zusätzliche Vorgaben/Referenzlisten:\n'
                                      '{}\n'
                                      '\n'
                                      'Nutze diese Angaben nur als Entscheidungshilfe für unsichere Lesungen von '
                                      'Namen, Orten und wiederkehrenden Begriffen. Erfinde keine Angaben, die nicht im '
                                      'Bild erkennbar sind.',
        'lm_token_canonical': 'Canonical JSON erzeugen',
        'lm_prompt_canonical_system': 'Canonical JSON – System-Prompt',
        'lm_prompt_canonical_user': 'Canonical JSON – Benutzer-Prompt',
        'section_local_ocr_prompts': 'Lokale OCR-/Überarbeitungs-Prompts',
        'section_gedcom_prompts': 'GEDCOM – empfohlener Hauptweg',
        'section_canonical_prompts': 'Canonical JSON / Graph – Prompts',
        'section_structured_json_prompts': 'Strukturierte JSON-/Graph-Prompts',
        'lm_prompt_postgresql_system': 'PostgreSQL-JSON – System-Prompt',
        'lm_prompt_postgresql_user': 'PostgreSQL-JSON – Benutzer-Prompt',
        'lm_prompt_neo4j_system': 'Neo4j-JSON – System-Prompt',
        'lm_prompt_neo4j_user': 'Neo4j-JSON – Benutzer-Prompt',
        'prompt_group_structured_json': 'Strukturierte JSON-/Graph-Prompts',
        'prompt_desc_canonical_system': 'Systemanweisung für Canonical JSON. Das Modell extrahiert eine einheitliche, '
                                        'überprüfbare Graph-Struktur aus OCR-Text.',
        'prompt_desc_canonical_user': 'Benutzeranweisung für Canonical JSON. Platzhalter {schema_template} und '
                                      '{ocr_text} bitte erhalten.',
        'prompt_desc_postgresql_system': 'Systemanweisung für PostgreSQL-JSON. Das Modell erzeugt relationale '
                                         'JSON-Tabellen für Personen, Orte, Jahre und Beziehungen.',
        'prompt_desc_postgresql_user': 'Benutzeranweisung für PostgreSQL-JSON. Platzhalter {schema_template} und '
                                       '{ocr_text} bitte erhalten.',
        'prompt_desc_neo4j_system': 'Systemanweisung für Neo4j-JSON. Das Modell erzeugt Nodes und Relationships für '
                                    'eine Graphdatenbank.',
        'prompt_desc_neo4j_user': 'Benutzeranweisung für Neo4j-JSON. Platzhalter {schema_template} und {ocr_text} '
                                  'bitte erhalten.',
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
                                 '{}'},
 'en': {'act_lm_token_settings': 'Set token limits for local models',
        'act_lm_prompt_settings': 'Edit prompts for local AI',
        'dlg_lm_token_title': 'Local LM token limits',
        'dlg_lm_token_hint': 'These values control the maximum response length of the local AI for each LM function.',
        'lm_token_current_line': 'Revise current line',
        'lm_token_selected_lines': 'Revise selected lines',
        'lm_token_all_lines': 'Revise all lines',
        'lm_token_lm_ocr': 'LM Page OCR',
        'lm_token_gedcom': 'Generate GEDCOM',
        'btn_restore_defaults': 'Defaults',
        'msg_lm_tokens_saved': 'Local LM token limits saved.',
        'dlg_lm_prompts_title': 'Edit local AI prompts',
        'dlg_lm_prompts_hint': 'Select a prompt on the left, edit it on the right, and save the changes. Keep '
                               'placeholders such as {} and doubled JSON braces {{...}} intact.',
        'lm_prompt_single_system': 'Current line – system prompt',
        'lm_prompt_single_user': 'Current line – user prompt',
        'lm_prompt_block_system': 'Selected/all lines – block system prompt',
        'lm_prompt_block_user': 'Selected/all lines – block user prompt',
        'lm_prompt_page_system': 'All lines – page system prompt',
        'lm_prompt_page_user': 'All lines – page user prompt',
        'lm_prompt_decision_system': 'All lines – decision system prompt',
        'lm_prompt_decision_user': 'All lines – decision user prompt',
        'lm_prompt_fullpage_ocr_system': 'LM Page OCR – system prompt',
        'lm_prompt_fullpage_ocr_user': 'LM Page OCR – user prompt',
        'lm_prompt_gedcom_system': 'GEDCOM – system prompt',
        'lm_prompt_gedcom_user': 'GEDCOM – user prompt',
        'btn_save': 'Save',
        'btn_close': 'Close',
        'btn_reset_selected_prompt': 'Reset selected prompt',
        'btn_reset_all_prompts': 'Reset all prompts',
        'msg_lm_prompts_saved': 'Local AI prompts saved.',
        'msg_lm_prompt_reset': 'Prompt was reset to the default prompt.',
        'msg_lm_prompts_reset_all': 'All local AI prompts were reset to their defaults.',
        'help_nav_overview': 'Overview',
        'help_h1_overview': 'Overview',
        'act_lm_custom_context': 'Defaults / lists / context',
        'dlg_lm_custom_context_title': 'Defaults / lists / context',
        'dlg_lm_custom_context_hint': 'Optional reference lists and instructions can be stored here, for example '
                                      'family names, place names, common occupations or abbreviations. These hints are '
                                      'appended automatically to the local AI user prompts.',
        'dlg_lm_custom_context_placeholder': 'Example:\n'
                                             'Family names: Miller, Smith, Hoffmann\n'
                                             'Places: Leipzig, Markranstädt, Taucha\n'
                                             'Notes: watch long-s spelling; Latin month names may occur',
        'btn_clear': 'Clear',
        'msg_lm_custom_context_saved': 'AI hints saved.',
        'msg_lm_custom_context_cleared': 'AI hints cleared.',
        'lm_custom_context_appendix': 'Additional hints/reference lists:\n'
                                      '{}\n'
                                      '\n'
                                      'Use these details only as decision support for uncertain readings of names, '
                                      'places and recurring terms. Do not invent information that is not visible in '
                                      'the image.',
        'lm_token_canonical': 'Generate Canonical JSON',
        'lm_prompt_canonical_system': 'Canonical JSON – system prompt',
        'lm_prompt_canonical_user': 'Canonical JSON – user prompt',
        'section_local_ocr_prompts': 'Local OCR/revision prompts',
        'section_gedcom_prompts': 'GEDCOM – recommended main workflow',
        'section_canonical_prompts': 'Canonical JSON / graph – prompts',
        'section_structured_json_prompts': 'Structured JSON / graph prompts',
        'lm_prompt_postgresql_system': 'PostgreSQL JSON – system prompt',
        'lm_prompt_postgresql_user': 'PostgreSQL JSON – user prompt',
        'lm_prompt_neo4j_system': 'Neo4j JSON – system prompt',
        'lm_prompt_neo4j_user': 'Neo4j JSON – user prompt',
        'prompt_group_structured_json': 'Structured JSON / graph prompts',
        'prompt_desc_canonical_system': 'System instruction for Canonical JSON. The model extracts a unified, '
                                        'verifiable graph structure from OCR text.',
        'prompt_desc_canonical_user': 'User instruction for Canonical JSON. Keep the placeholders {schema_template} '
                                      'and {ocr_text}.',
        'prompt_desc_postgresql_system': 'System instruction for PostgreSQL JSON. The model creates relational JSON '
                                         'tables for persons, places, years and relations.',
        'prompt_desc_postgresql_user': 'User instruction for PostgreSQL JSON. Keep the placeholders {schema_template} '
                                       'and {ocr_text}.',
        'prompt_desc_neo4j_system': 'System instruction for Neo4j JSON. The model creates nodes and relationships for '
                                    'a graph database.',
        'prompt_desc_neo4j_user': 'User instruction for Neo4j JSON. Keep the placeholders {schema_template} and '
                                  '{ocr_text}.',
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
                                 '{}'},
 'fr': {'act_lm_token_settings': 'Définir les limites de tokens des modèles locaux',
        'act_lm_prompt_settings': 'Modifier les prompts pour l’IA locale',
        'dlg_lm_token_title': 'Limites de tokens LM locales',
        'dlg_lm_token_hint': 'Ces valeurs définissent la longueur maximale de réponse de l’IA locale pour chaque '
                             'fonction LM.',
        'lm_token_current_line': 'Réviser la ligne actuelle',
        'lm_token_selected_lines': 'Réviser les lignes sélectionnées',
        'lm_token_all_lines': 'Réviser toutes les lignes',
        'lm_token_lm_ocr': 'OCR de page LM',
        'lm_token_gedcom': 'Générer GEDCOM',
        'btn_restore_defaults': 'Valeurs par défaut',
        'msg_lm_tokens_saved': 'Limites de tokens LM locales enregistrées.',
        'dlg_lm_prompts_title': 'Modifier les prompts de l’IA locale',
        'dlg_lm_prompts_hint': 'Sélectionnez un prompt à gauche, modifiez-le à droite puis enregistrez. Conservez les '
                               'espaces réservés comme {} et les accolades JSON doublées {{...}}.',
        'lm_prompt_single_system': 'Ligne actuelle – prompt système',
        'lm_prompt_single_user': 'Ligne actuelle – prompt utilisateur',
        'lm_prompt_block_system': 'Lignes sélectionnées/toutes les lignes – prompt système de bloc',
        'lm_prompt_block_user': 'Lignes sélectionnées/toutes les lignes – prompt utilisateur de bloc',
        'lm_prompt_page_system': 'Toutes les lignes – prompt système de page',
        'lm_prompt_page_user': 'Toutes les lignes – prompt utilisateur de page',
        'lm_prompt_decision_system': 'Toutes les lignes – prompt système de décision',
        'lm_prompt_decision_user': 'Toutes les lignes – prompt utilisateur de décision',
        'lm_prompt_fullpage_ocr_system': 'OCR de page LM – prompt système',
        'lm_prompt_fullpage_ocr_user': 'OCR de page LM – prompt utilisateur',
        'lm_prompt_gedcom_system': 'GEDCOM – prompt système',
        'lm_prompt_gedcom_user': 'GEDCOM – prompt utilisateur',
        'btn_save': 'Enregistrer',
        'btn_close': 'Fermer',
        'btn_reset_selected_prompt': 'Réinitialiser le prompt sélectionné',
        'btn_reset_all_prompts': 'Réinitialiser tous les prompts',
        'msg_lm_prompts_saved': 'Prompts de l’IA locale enregistrés.',
        'msg_lm_prompt_reset': 'Le prompt a été réinitialisé au prompt par défaut.',
        'msg_lm_prompts_reset_all': 'Tous les prompts de l’IA locale ont été réinitialisés.',
        'help_nav_overview': 'Vue d’ensemble',
        'help_h1_overview': 'Vue d’ensemble',
        'act_lm_custom_context': 'Consignes / listes / contexte',
        'dlg_lm_custom_context_title': 'Consignes / listes / contexte',
        'dlg_lm_custom_context_hint': 'Des listes de référence et consignes optionnelles peuvent être enregistrées '
                                      'ici, par exemple des noms de famille, lieux, métiers fréquents ou abréviations. '
                                      'Ces indications sont ajoutées automatiquement aux prompts utilisateur de l’IA '
                                      'locale.',
        'dlg_lm_custom_context_placeholder': 'Exemple :\n'
                                             'Noms de famille : Müller, Schmidt, Hoffmann\n'
                                             'Lieux : Leipzig, Markranstädt, Taucha\n'
                                             'Remarques : tenir compte du s long ; noms de mois latins possibles',
        'btn_clear': 'Vider',
        'msg_lm_custom_context_saved': 'Consignes IA enregistrées.',
        'msg_lm_custom_context_cleared': 'Consignes IA vidées.',
        'lm_custom_context_appendix': 'Consignes/listes de référence supplémentaires :\n'
                                      '{}\n'
                                      '\n'
                                      'Utilise ces indications uniquement comme aide à la décision pour les lectures '
                                      'incertaines de noms, lieux et termes récurrents. N’invente pas d’informations '
                                      'qui ne sont pas visibles dans l’image.',
        'lm_token_canonical': 'Générer le JSON canonique',
        'lm_prompt_canonical_system': 'JSON canonique – prompt système',
        'lm_prompt_canonical_user': 'JSON canonique – prompt utilisateur',
        'section_local_ocr_prompts': 'Prompts locaux OCR/révision',
        'section_gedcom_prompts': 'GEDCOM – méthode principale recommandée',
        'section_canonical_prompts': 'JSON canonique / graphe – prompts',
        'section_structured_json_prompts': 'Prompts JSON structuré / graphe',
        'lm_prompt_postgresql_system': 'JSON PostgreSQL – prompt système',
        'lm_prompt_postgresql_user': 'JSON PostgreSQL – prompt utilisateur',
        'lm_prompt_neo4j_system': 'JSON Neo4j – prompt système',
        'lm_prompt_neo4j_user': 'JSON Neo4j – prompt utilisateur',
        'prompt_group_structured_json': 'Prompts JSON structuré / graphe',
        'prompt_desc_canonical_system': 'Consigne système pour le JSON canonique. Le modèle extrait une structure de '
                                        'graphe unifiée et vérifiable à partir du texte OCR.',
        'prompt_desc_canonical_user': 'Consigne utilisateur pour le JSON canonique. Conserver les espaces réservés '
                                      '{schema_template} et {ocr_text}.',
        'prompt_desc_postgresql_system': 'Consigne système pour le JSON PostgreSQL. Le modèle crée des tables JSON '
                                         'relationnelles pour les personnes, lieux, années et relations.',
        'prompt_desc_postgresql_user': 'Consigne utilisateur pour le JSON PostgreSQL. Conserver les espaces réservés '
                                       '{schema_template} et {ocr_text}.',
        'prompt_desc_neo4j_system': 'Consigne système pour le JSON Neo4j. Le modèle crée des nœuds et relations pour '
                                    'une base de données graphe.',
        'prompt_desc_neo4j_user': 'Consigne utilisateur pour le JSON Neo4j. Conserver les espaces réservés '
                                  '{schema_template} et {ocr_text}.',
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
                                 '{}'}}
