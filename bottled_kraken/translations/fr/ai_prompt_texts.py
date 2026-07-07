FR_AI_PROMPT_TEXTS_TRANSLATIONS = {
    'ai_prompt_page_system': (
        'Du bist ein hochpräziser OCR- und Transkriptionsassistent für historische deutsche Drucke, Handschriften und Formulare.\nDu liest den Text direkt aus dem Bild.\nDas Bild ist die einzige Wahrheitsquelle.\nIMPORTANT : les guillemets doubles (") et les séquences comme -"- dans les registres sont souvent des marques de répétition. Ne les traite pas littéralement ; remplace-les par la valeur correspondante de la ligne précédente ou de la même colonne dans l’entrée précédente.\nUn guillemet simple (") dans des tableaux ou registres signifie généralement : répéter la valeur correspondante de la ligne précédente ; résous ces marques de répétition à partir du contexte.\nDu musst den gelesenen Text auf eine bereits vorgegebene Liste von Zielzeilen abbilden.\nJede Zielzeile entspricht genau einer visuellen Formular- oder Textzeile.\nDu darfst keine zwei Zielzeilen zusammenziehen.\nDu darfst keine zusätzliche Leerzeile halluzinieren.\nDu darfst keinen langen Textblock in eine einzelne Zielzeile schreiben.\nWenn eine Zielzeile keinen sicher lesbaren Text enthält, gib für genau diese Zeile einen leeren String zurück.\nDu musst die Anzahl der Zielzeilen exakt einhalten.\nAntworte ausschließlich mit gültigem JSON.\nKein Markdown. Kein Zusatztext. Kein Kommentar.'
),
    'ai_prompt_page_user': (
        'Lies den Text direkt aus dem Bild.\n\nDu musst die vorgegebene Kraken-Zeilenstruktur EXAKT einhalten.\nEs gibt genau {} Zielzeilen.\nJeder idx steht für genau eine visuelle Zielzeile.\n\nHARTE REGELN:\n- Gib genau {} Einträge im Feld lines zurück\n- Die idx-Werte müssen exakt 0 bis {} sein\n- Kein idx darf fehlen\n- Kein idx darf doppelt vorkommen\n- Keine zwei Zielzeilen dürfen zu einer Zeile zusammengezogen werden\n- Kein langer Satzblock darf in einer einzelnen Zielzeile landen\n- Wenn eine Zielzeile unklar ist, gib den bestmöglichen kurzen Zeilentext zurück\n- Wenn die Zielzeile wirklich leer ist, gib text als leeren String zurück\n- Die bbox ist nur Orientierung für die visuelle Zuordnung\n- Gib NUR das JSON-Objekt zurück\n- Kein Markdown\n- Keine Analyse\n- Keine Kommentare\n- Keine zusätzlichen Sätze\n\nKraken-Zielzeilenstruktur:\n{}\n\nAntwortformat exakt so:\n{{"lines":[{{"idx":0,"text":"..."}},{{"idx":1,"text":"..."}}]}}'
),
    'ai_prompt_single_system': (
        'Du bist ein präziser OCR- und Transkriptionsassistent für historische deutsche Handschriften und Formulare.\nDu liest genau eine einzelne Zielzeile aus einem Bildausschnitt.\nDas Bild ist die einzige Wahrheitsquelle.\nIMPORTANT : les guillemets doubles (") et les séquences comme -"- dans les registres sont souvent des marques de répétition. Ne les traite pas littéralement ; remplace-les par la valeur correspondante de la ligne précédente ou de la même colonne dans l’entrée précédente.\nUn guillemet simple (") dans des tableaux ou registres signifie généralement : répéter la valeur correspondante de la ligne précédente ; résous ces marques de répétition à partir du contexte.\nDie Zielzeile befindet sich in der Mitte des Ausschnitts.\nOberhalb oder unterhalb sichtbare Linien, Leerzeilen, Formularlinien, Labels oder Nachbarzeilen sind nur Kontext.\nDu darfst nur den Text der einen Zielzeile zurückgeben.\nDu darfst keinen Text aus Nachbarzeilen übernehmen.\nDu darfst keine zusätzliche Zeile erfinden.\nDu darfst keine lange Passage bilden, wenn im Ausschnitt nur eine kurze Formularzeile steht.\nWenn die Zielzeile leer ist, gib einen leeren String zurück.\nAntworte ausschließlich mit gültigem JSON.\nKein Markdown. Kein Zusatztext. Kein Kommentar.'
),
    'ai_prompt_single_user': (
        'Lies genau die Zielzeile in der Mitte des Bildausschnitts.\nWICHTIG:\n- Gib nur den Text dieser EINEN Zeile zurück\n- Benachbarte Zeilen dürfen nicht übernommen werden\n- Formular-Labels, Linien und Leerbereiche dürfen nicht halluziniert ergänzt werden\n- Wenn in dieser Zielzeile kein lesbarer Text steht, gib text als leeren String zurück\n- Keine zweite Zeile\n- Keine Zusammenfassung\n- Keine Erklärung\n- Kein Markdown\n- Keine Ausgabe vor oder nach dem JSON\n\nFormat exakt:\n{{"text":"..."}}\n\nZeilenindex: {}'
),
    'ai_prompt_decision_system': (
        'Tu es un assistant précis de correction OCR pour écritures historiques, textes imprimés, tableaux et formulaires.\nTu reçois trois candidats pour exactement une ligne cible :\n1. le texte Kraken/de ligne précédent\n2. l’OCR du contexte local de page/bloc\n3. l’OCR de la boîte de superposition de cette ligne\n\nTâche :\n- Produis la meilleure version corrigée pour exactement cette ligne cible.\n- Kraken reste l’ancre conservatrice et ne doit pas être remplacé sans raison.\n- L’OCR LM peut améliorer Kraken si elle ajoute de manière plausible des mots, caractères ou espaces manquants, ou corrige des lectures clairement fausses.\n- Aucun nom, lieu, date, âge, année ou nombre d’un texte Kraken plausible ne doit disparaître.\n- Utilise le contexte de page/bloc seulement s’il correspond à la ligne cible ; ne copie jamais les lignes voisines.\n- Conserve l’orthographe historique ainsi que les noms et nombres originaux.\n- N’invente aucune information.\n- Ne retourne jamais plus d’une ligne.\nRéponds uniquement avec du JSON valide.\nPas de Markdown. Pas de texte supplémentaire. Pas de commentaire.\nIMPORTANT : Les guillemets doubles (") et les séquences comme -"- sont souvent des marques de répétition dans les registres. Ne les rends pas littéralement ; remplace-les par la valeur correspondante de la ligne précédente ou de la même colonne dans l’entrée précédente.'
),
    'ai_prompt_decision_user': (
        'Ligne cible idx={}\n\nTexte Kraken/de ligne précédent :\n{}\n\nOCR du contexte page/bloc :\n{}\n\nOCR de la boîte de superposition :\n{}\n\nCompare les trois candidats et retourne la meilleure version corrigée pour EXACTEMENT cette ligne cible.\nLe texte cible peut différer du texte Kraken précédent si l’OCR LM passe le contrôle de cohérence et donne une lecture plus complète ou plus claire.\nPas de ligne voisine, pas d’explication, pas de Markdown.\nFormat exact :\n{{"text":"..."}}'
),
    'ai_prompt_block_system': (
        'Du bist ein präziser OCR- und Transkriptionsassistent für historische deutsche Handschriften.\nLies den Text frei direkt aus dem Bild.\nDas Bild ist die einzige Wahrheitsquelle.\nIMPORTANT : les guillemets doubles (") et les séquences comme -"- dans les registres sont souvent des marques de répétition. Ne les traite pas littéralement ; remplace-les par la valeur correspondante de la ligne précédente ou de la même colonne dans l’entrée précédente.\nUn guillemet simple (") dans des tableaux ou registres signifie généralement : répéter la valeur correspondante de la ligne précédente ; résous ces marques de répétition à partir du contexte.\nDu darfst nicht den OCR-Hinweis rekonstruieren, sondern musst das Bild selbst lesen.\nDie von außen vorgegebene Zeilenanzahl ist nur ein Strukturrahmen.\nDu musst den frei gelesenen Text passend in genau diese Anzahl von Zeilen eintragen.\nAntworte ausschließlich mit gültigem JSON.\nKein Markdown. Kein Zusatztext. Kein Kommentar.'
),
    'ai_prompt_block_user': (
        'Lies die handschriftlichen Zeilen im Bildausschnitt.\nGib ausschließlich genau EIN JSON-Objekt zurück.\nKein Markdown. Kein ```json. Kein Kommentar. Kein Zusatztext.\nEs müssen genau {} Einträge im Feld lines stehen.\nWichtig:\n- doppelte Anführungszeichen innerhalb von text immer als " escapen\n- keine weiteren Felder außer idx und text\n- keine Ausgabe vor oder nach dem JSON\nFormat:\n{{"lines":[{{"idx":0,"text":"..."}}]}}\n\nDie idx-Werte müssen lokal bei 0 beginnen.\nAktueller OCR-Hinweis:\n{}'
),
    'line_menu_ai_revise_single': 'Réviser uniquement cette ligne avec le LM',
    'btn_ok': 'OK',
    'act_image_edit': 'Édition d’image',
    'canvas_menu_split_box': 'Scinder la boîte',
    'ai_prompt_export_zones_system': (
        'Tu es un extracteur de tableaux. Sans analyse, retourne immédiatement uniquement du JSON valide au format {{"rows":[{{...}}]}}. Pas de Markdown, pas d’explication, pas de notes de traitement. Utilise uniquement de vraies entrées de registre. Ignore les en-têtes, titres, séparateurs et ornements. Chaque ligne de sortie correspond exactement à une ligne visuelle du registre ; ne fusionne jamais plusieurs candidats OCR dans une cellule. Ne remplis unknown que s’il existe une vraie valeur dans cette colonne ; ne l’utilise jamais pour toute la ligne originale.'
    ),
    'ai_prompt_export_zones_user': (
        'Créer un tableau à partir de l’image de page, des boîtes overlay, des zones d’export et des candidats OCR.\nClés : {}.\nColonnes : {}\nContexte : {}\nRègles : les zones sont des modèles de colonnes sur toute la hauteur de page. Les valeurs de la même ligne y vont ensemble. Utilise l’image et les positions overlay. Laisse les cellules incertaines vides. N’invente aucune donnée. Conserve les graphies historiques. Retourne seulement JSON : {{"rows":[{{...}}]}}.'
    ),
    'queue_ctx_check_all': 'Tout cocher',
    'queue_ctx_uncheck_all': 'Effacer toutes les coches',
    'queue_check_header_tooltip': 'Cliquer pour cocher tous les fichiers ou retirer toutes les coches',
    'line_menu_ai_revise_selected': 'Réviser les lignes sélectionnées avec le LM',
    'menu_lm_options': 'Options LM',
    'menu_whisper_options': 'Options Whisper',
    'act_whisper_set_path': 'Définir le chemin du modèle Whisper...',
    'act_whisper_set_mic': 'Choisir le microphone...',
    'act_scan_local': 'Scanner localement',
    'no_models_scan': 'Aucun modèle - vérifier le répertoire',
    'act_unload_model': 'Décharger le modèle',
    'msg_whisper_model_unloaded': 'Modèle Whisper déchargé.',
    'msg_whisper_models_found': '{} modèle(s) Whisper trouvé(s).',
    'msg_whisper_models_not_found': 'Aucun modèle Whisper trouvé.',
    'warn_no_audio_devices': 'Aucun périphérique d’entrée audio n’a été trouvé.',
    'dlg_choose_microphone': 'Choisir le microphone',
    'dlg_audio_input_device': 'Périphérique d’entrée audio :',
    'msg_microphone_set': 'Microphone défini : {}',
    'export_choose_format_label': 'Choisir le format d’export :',
    'msg_pdf_render_already_running': 'Un PDF est déjà en cours de rendu. Veuillez patienter un instant.',
    'pdf_page_display': '{} – Page {:04d}',
    'act_set_manual_lm_url': 'Définir l’URL du serveur LM...',
    'act_clear_manual_lm_url': 'Effacer l’URL du serveur LM',
    'msg_lm_found_url': 'LM trouvé : {} | URL : {}',
    'msg_lm_no_models_url': 'Aucun modèle trouvé | URL : {}',
    'msg_lm_found': 'LM trouvé : {}',
    'msg_lm_server_not_found': 'Aucun serveur LM local accessible n’a été trouvé.',
    'act_clear_ai_model': 'Retirer le modèle LM',
    'msg_ai_model_choice_cleared': 'Sélection du modèle LM effacée.',
    'msg_ai_model_removed': 'Modèle LM retiré.',
    'header_rec_models': 'Modèles de reconnaissance:',
    'header_seg_models': 'Modèles de segmentation:',
    'status_rec_model': 'Modèle de reconnaissance : {}',
    'status_seg_model': 'Modèle de segmentation : {}',
    'msg_ai_model_id_cleared_auto': 'Identifiant du modèle IA effacé, auto-détection localhost active.',
    'msg_ai_single_done': 'Révision LM terminée pour la ligne {}.',
    'log_ai_single_done': 'Révision LM de ligne terminée : {} | ligne {}',
    'msg_ai_single_cancelled': 'Révision de ligne annulée.',
    'log_ai_single_cancelled': 'Révision LM de ligne annulée : {}',
    'msg_ai_single_failed': 'Échec de la révision de ligne.',
    'log_ai_single_failed': 'Erreur de révision LM de ligne : {} -> {}',
    'msg_ai_cancelled_short': 'Révision annulée.',
    'msg_ai_failed_short': 'Échec de la révision.',
    'warn_blla_model_missing': 'Le modèle de segmentation blla est introuvable.',
    'dlg_project_loading_title': 'Charger le projet',
    'white_border_title': 'Ajouter une bordure blanche',
    'white_border_pixels': 'Bordure en pixels :',
    'image_edit_rotate_off': 'Rotation : NON',
    'image_edit_rotate_on': 'Rotation : OUI',
    'image_edit_grid': 'Grille',
    'image_edit_grid_tooltip': 'Taille de la grille : fine à grossière',
    'image_edit_grid_label': 'Taille de la grille',
    'image_edit_crop': 'Zone de recadrage',
    'image_edit_separator': 'Barre de séparation',
    'image_edit_gray': 'Niveaux de gris',
    'image_edit_contrast': 'Contraste',
    'image_edit_rotation_reset': 'Réinitialiser la rotation',
    'image_edit_smart_split': 'Découpage intelligent',
    'image_edit_prev': 'Image précédente',
    'image_edit_next': 'Image suivante',
    'image_edit_white_border': 'Ajouter une bordure blanche',
    'image_edit_white_border_with_px': 'Ajouter une bordure blanche ({} px)',
    'image_edit_apply_selected': 'Appliquer à toutes les images marquées',
    'image_edit_apply_all': 'Appliquer à toutes',
    'image_edit_applied_single_status': 'Image editing applied. Edited images were saved in the source directory and added to the queue as new entries.',
    'log_image_edit_applied': 'Image editing applied: {} | {} output file(s) saved in the source directory',
    'image_edit_no_image_loaded': 'Aucune image chargée',
    'image_edit_batch_title': 'Traitement d’image en cours',
    'image_edit_batch_label': 'Traitement de l’image {}/{} : {}',
    'msg_image_edit_batch_cancelled': 'Traitement d’image annulé.',
    'image_edit_notice_title': 'Remarque',
    'image_edit_turn_off_rotation_first': (
        "La rotation est encore active.\n\nVeuillez d’abord passer à 'Rotation : NON' avant de modifier la zone de recadrage ou la barre de séparation."
),
    'msg_not_available': 'Indisponible',
    'help_nav_image_edit': 'Édition d’image',
    'help_nav_lm_alternatives': 'Alternatives à LM Studio',
}
