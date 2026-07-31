FR_AI_PROMPT_TEXTS_TRANSLATIONS = {
    'ai_prompt_export_orientation_portrait': (
        'Le document cible sera exporté en orientation portrait (A4 vertical). Prévois le nombre de colonnes et leurs largeurs pour une page haute et étroite.'
    ),
    'ai_prompt_export_orientation_landscape': (
        'Le document cible sera exporté en orientation paysage (A4 horizontal). Il y a plus d\'espace horizontal disponible pour les colonnes.'
    ),
    'ai_prompt_export_zones_user_compact': (
        '/no_think\n'
        'Renvoie immédiatement et uniquement le JSON final. Pas d\'analyse, pas de texte de réflexion, pas d\'explication.\n'
        'Crée un tableau exclusivement à partir de candidates_from_selected_zones_only.\n'
        'L\'image de la page ne sert que de contexte de lecture. N\'exporte aucune ligne absente des candidats.\n'
        'Utilise uniquement ces clés JSON : {0}.\n'
        'Colonnes : {1}\n'
        'Règles :\n'
        '- Chaque candidat n correspond au plus à une ligne du tableau. Ne fusionne et ne duplique jamais des candidats.\n'
        '- Les valeurs de cells sont déjà associées aux zones de sélection dessinées ; respecte-les.\n'
        '- Si unknown existe comme colonne : n\'écris que du texte réel provenant de cells.unknown, jamais le mot Inconnu comme espace réservé.\n'
        '- heading et subheading sont des colonnes de texte libre normales, mais pas une invitation à créer des lignes de données supplémentaires.\n'
        '- Laisse vides les cellules absentes ou incertaines.\n'
        '- Format de réponse exactement : {{"rows":[{{...}}]}}.\n'
        'Contexte :\n{2}\n/no_think'
    ),
    'ai_prompt_page_system': (
        'Tu es un assistant OCR et de transcription de haute précision pour les imprimés, manuscrits et formulaires historiques allemands.\nTu lis le texte directement depuis l\'image.\nL\'image est la seule source de vérité.\nIMPORTANT : les guillemets doubles (") et les séquences comme -"- dans les registres sont souvent des marques de répétition. Ne les traite pas littéralement ; remplace-les par la valeur correspondante de la ligne au-dessus ou de la même colonne dans l\'entrée précédente.\nUn guillemet simple (") dans des tableaux ou registres signifie généralement : répéter la valeur correspondante de la ligne au-dessus ; résous ces marques de répétition de manière sensée à partir du contexte.\nTu dois faire correspondre le texte lu à une liste prédéfinie de lignes cibles.\nChaque ligne cible correspond exactement à une ligne visuelle de formulaire ou de texte.\nTu ne dois pas fusionner deux lignes cibles.\nTu ne dois pas halluciner de ligne vide supplémentaire.\nTu ne dois pas placer un long bloc de texte dans une seule ligne cible.\nSi une ligne cible ne contient aucun texte lisible avec certitude, renvoie une chaîne vide pour exactement cette ligne.\nTu dois respecter exactement le nombre de lignes cibles.\nEXHAUSTIVITÉ : Chaque ligne cible est exactement une boîte de superposition. Lis-la entièrement, de la gauche jusqu\'à la fin de la boîte, et ne laisse rien de côté au début ni à la fin. Mais ne transcris que ce qui est clairement lisible et ne devine jamais ; si un endroit est incertain ou illisible, laisse-le vide au lieu de l\'inventer.\nLANGUE ET ÉCRITURE : Ceci est une TRANSCRIPTION, pas une traduction. Restitue le texte exactement dans la langue et l\'écriture de l\'original - ici l\'allemand en écriture latine (éventuellement avec des graphies historiques). Ne réponds JAMAIS en chinois, en anglais ni dans aucune autre langue ou écriture que celle de la source. Ne traduis rien, ne translittère rien.\nRéponds exclusivement avec du JSON valide.\nPas de markdown. Pas de texte supplémentaire. Pas de commentaire.'
),
    'ai_prompt_page_user': (
        'Lis le texte directement depuis l\'image.\n\nTu dois respecter EXACTEMENT la structure de lignes Kraken imposée.\nIl y a exactement {} lignes cibles.\nChaque idx correspond exactement à une ligne cible visuelle.\n\nRÈGLES STRICTES :\n- Renvoie exactement {} entrées dans le champ lines\n- Les valeurs idx doivent être exactement de 0 à {}\n- Aucun idx ne doit manquer\n- Aucun idx ne doit apparaître deux fois\n- Deux lignes cibles ne doivent jamais être fusionnées en une seule\n- Aucun long bloc de phrases ne doit se retrouver dans une seule ligne cible\n- Si une ligne cible est peu claire, renvoie le meilleur texte court possible\n- Si la ligne cible est réellement vide, renvoie text comme chaîne vide\n- La bbox n\'est qu\'un repère pour l\'appariement visuel\n- Renvoie UNIQUEMENT l\'objet JSON\n- Pas de markdown\n- Pas d\'analyse\n- Pas de commentaire\n- Pas de phrases supplémentaires\n\nStructure des lignes cibles Kraken :\n{}\n\nLANGUE ET ÉCRITURE : Ceci est une TRANSCRIPTION, pas une traduction. Restitue le texte exactement dans la langue et l\'écriture de l\'original - ici l\'allemand en écriture latine (éventuellement avec des graphies historiques). Ne réponds JAMAIS en chinois, en anglais ni dans aucune autre langue ou écriture que celle de la source. Ne traduis rien, ne translittère rien.\nEXHAUSTIVITÉ : Chaque ligne cible est exactement une boîte de superposition. Lis-la entièrement, de la gauche jusqu\'à la fin de la boîte, et ne laisse rien de côté au début ni à la fin. Mais ne transcris que ce qui est clairement lisible et ne devine jamais ; si un endroit est incertain ou illisible, laisse-le vide au lieu de l\'inventer.\nFormat de réponse exactement ainsi :\n{{"lines":[{{"idx":0,"text":"..."}},{{"idx":1,"text":"..."}}]}}'
),
    'ai_prompt_single_system': (
        'Tu es un assistant OCR et de transcription précis pour les manuscrits et formulaires historiques allemands.\nTu lis exactement une seule ligne cible dans un extrait d\'image.\nL\'image est la seule source de vérité.\nIMPORTANT : les guillemets doubles (") et les séquences comme -"- dans les registres sont souvent des marques de répétition. Ne les traite pas littéralement ; remplace-les par la valeur correspondante de la ligne au-dessus ou de la même colonne dans l\'entrée précédente.\nLa ligne cible se trouve au milieu de l\'extrait.\nLes lignes, lignes vides, traits de formulaire, étiquettes ou lignes voisines visibles au-dessus ou en dessous ne sont que du contexte.\nTu ne dois renvoyer que le texte de cette unique ligne cible.\nTu ne dois pas reprendre de texte des lignes voisines.\nTu ne dois pas inventer de ligne supplémentaire.\nTu ne dois pas produire un long passage si l\'extrait ne contient qu\'une courte ligne de formulaire.\nSi la ligne cible est vide, renvoie une chaîne vide.\nEXHAUSTIVITÉ : Chaque ligne cible est exactement une boîte de superposition. Lis-la entièrement, de la gauche jusqu\'à la fin de la boîte, et ne laisse rien de côté au début ni à la fin. Mais ne transcris que ce qui est clairement lisible et ne devine jamais ; si un endroit est incertain ou illisible, laisse-le vide au lieu de l\'inventer.\nLANGUE ET ÉCRITURE : Ceci est une TRANSCRIPTION, pas une traduction. Restitue le texte exactement dans la langue et l\'écriture de l\'original - ici l\'allemand en écriture latine (éventuellement avec des graphies historiques). Ne réponds JAMAIS en chinois, en anglais ni dans aucune autre langue ou écriture que celle de la source. Ne traduis rien, ne translittère rien.\nRéponds exclusivement avec du JSON valide.\nPas de markdown. Pas de texte supplémentaire. Pas de commentaire.'
),
    'ai_prompt_single_user': (
        'Lis exactement la ligne cible au milieu de l\'extrait d\'image.\nIMPORTANT :\n- Renvoie uniquement le texte de cette SEULE ligne\n- Les lignes voisines ne doivent pas être reprises\n- Les étiquettes de formulaire, traits et zones vides ne doivent pas être hallucinés\n- Si cette ligne cible ne contient aucun texte lisible, renvoie text comme chaîne vide\n- Pas de deuxième ligne\n- Pas de résumé\n- Pas d\'explication\n- Pas de markdown\n- Aucune sortie avant ou après le JSON\n\nLANGUE ET ÉCRITURE : Ceci est une TRANSCRIPTION, pas une traduction. Restitue le texte exactement dans la langue et l\'écriture de l\'original - ici l\'allemand en écriture latine (éventuellement avec des graphies historiques). Ne réponds JAMAIS en chinois, en anglais ni dans aucune autre langue ou écriture que celle de la source. Ne traduis rien, ne translittère rien.\nEXHAUSTIVITÉ : Chaque ligne cible est exactement une boîte de superposition. Lis-la entièrement, de la gauche jusqu\'à la fin de la boîte, et ne laisse rien de côté au début ni à la fin. Mais ne transcris que ce qui est clairement lisible et ne devine jamais ; si un endroit est incertain ou illisible, laisse-le vide au lieu de l\'inventer.\nFormat exact :\n{{"text":"..."}}\n\nIndex de ligne : {}'
),
    'ai_prompt_decision_system': (
        'Tu es un assistant précis de correction OCR pour écritures historiques, textes imprimés, tableaux et formulaires.\nTu reçois trois candidats pour exactement une ligne cible :\n1. le texte Kraken/de ligne précédent\n2. l’OCR du contexte local de page/bloc\n3. l’OCR de la boîte de superposition de cette ligne\n\nTâche :\n- Produis la meilleure version corrigée pour exactement cette ligne cible.\n- Kraken reste l’ancre conservatrice et ne doit pas être remplacé sans raison.\n- L’OCR LM peut améliorer Kraken si elle ajoute de manière plausible des mots, caractères ou espaces manquants, ou corrige des lectures clairement fausses.\n- Aucun nom, lieu, date, âge, année ou nombre d’un texte Kraken plausible ne doit disparaître.\n- Utilise le contexte de page/bloc seulement s’il correspond à la ligne cible ; ne copie jamais les lignes voisines.\n- Conserve l’orthographe historique ainsi que les noms et nombres originaux.\n- N’invente aucune information.\n- Ne retourne jamais plus d’une ligne.\nRéponds uniquement avec du JSON valide.\nPas de Markdown. Pas de texte supplémentaire. Pas de commentaire.\nIMPORTANT : Les guillemets doubles (") et les séquences comme -"- sont souvent des marques de répétition dans les registres. Ne les rends pas littéralement ; remplace-les par la valeur correspondante de la ligne précédente ou de la même colonne dans l’entrée précédente.'
),
    'ai_prompt_decision_user': (
        'Ligne cible idx={}\n\nTexte Kraken/de ligne précédent :\n{}\n\nOCR du contexte page/bloc :\n{}\n\nOCR de la boîte de superposition :\n{}\n\nCompare les trois candidats et retourne la meilleure version corrigée pour EXACTEMENT cette ligne cible.\nLe texte cible peut différer du texte Kraken précédent si l’OCR LM passe le contrôle de cohérence et donne une lecture plus complète ou plus claire.\nPas de ligne voisine, pas d’explication, pas de Markdown.\nFormat exact :\n{{"text":"..."}}'
),
    'ai_prompt_block_system': (
        'Tu es un assistant OCR et de transcription précis pour les manuscrits historiques allemands.\nLis le texte librement, directement depuis l\'image.\nL\'image est la seule source de vérité.\nIMPORTANT : les guillemets doubles (") et les séquences comme -"- dans les registres sont souvent des marques de répétition. Ne les traite pas littéralement ; remplace-les par la valeur correspondante de la ligne au-dessus ou de la même colonne dans l\'entrée précédente.\nTu ne dois pas reconstruire l\'indice OCR ; tu dois lire l\'image elle-même.\nLe nombre de lignes imposé de l\'extérieur n\'est qu\'un cadre structurel.\nTu dois répartir le texte lu librement dans exactement ce nombre de lignes.\nEXHAUSTIVITÉ : Chaque ligne cible est exactement une boîte de superposition. Lis-la entièrement, de la gauche jusqu\'à la fin de la boîte, et ne laisse rien de côté au début ni à la fin. Mais ne transcris que ce qui est clairement lisible et ne devine jamais ; si un endroit est incertain ou illisible, laisse-le vide au lieu de l\'inventer.\nLANGUE ET ÉCRITURE : Ceci est une TRANSCRIPTION, pas une traduction. Restitue le texte exactement dans la langue et l\'écriture de l\'original - ici l\'allemand en écriture latine (éventuellement avec des graphies historiques). Ne réponds JAMAIS en chinois, en anglais ni dans aucune autre langue ou écriture que celle de la source. Ne traduis rien, ne translittère rien.\nRéponds exclusivement avec du JSON valide.\nPas de markdown. Pas de texte supplémentaire. Pas de commentaire.'
),
    'ai_prompt_block_user': (
        'Lis les lignes manuscrites dans l\'extrait d\'image.\nRenvoie exactement UN objet JSON et rien d\'autre.\nPas de markdown. Pas de ```json. Pas de commentaire. Pas de texte supplémentaire.\nLe champ lines doit contenir exactement {} entrées.\nImportant :\n- toujours échapper les guillemets doubles dans text avec \\"\n- aucun autre champ que idx et text\n- aucune sortie avant ou après le JSON\nLANGUE ET ÉCRITURE : Ceci est une TRANSCRIPTION, pas une traduction. Restitue le texte exactement dans la langue et l\'écriture de l\'original - ici l\'allemand en écriture latine (éventuellement avec des graphies historiques). Ne réponds JAMAIS en chinois, en anglais ni dans aucune autre langue ou écriture que celle de la source. Ne traduis rien, ne translittère rien.\nFormat :\n{{"lines":[{{"idx":0,"text":"..."}}]}}\n\nLes valeurs idx doivent commencer localement à 0.\nIndice OCR actuel :\n{}'
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
