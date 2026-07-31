# eScriptorium user interface, native installation, and lifecycle texts.
ESCRIPTORIUM_TEXTS = {'menu_escriptorium': 'eScriptorium',
 'dlg_escriptorium_title': 'eScriptorium local',
 'escriptorium_dialog_intro': 'Sélectionnez votre système d’exploitation. Installez ou mettez d’abord eScriptorium à '
                              'jour, puis démarrez le serveur. Bottled Kraken télécharge, installe, configure et gère '
                              'automatiquement tous les services locaux en arrière-plan. Docker n’est pas nécessaire.',
 'escriptorium_label_status': 'État :',
 'escriptorium_label_install_dir': 'Dossier local :',
 'escriptorium_label_server_url': 'Adresse du serveur :',
 'escriptorium_label_credentials': 'Identifiants :',
 'escriptorium_status_checking': 'Vérification de l’état…',
 'escriptorium_status_running': 'eScriptorium est en cours d’exécution.',
 'escriptorium_status_stopped': 'Installé, mais arrêté.',
 'escriptorium_status_not_installed': 'Pas encore installé. Utilisez d’abord « Installer / mettre à jour eScriptorium '
                                      '».',
 'escriptorium_btn_refresh': 'Actualiser',
 'escriptorium_btn_start': 'Démarrer le serveur',
 'escriptorium_btn_stop': 'Arrêter le serveur',
 'escriptorium_btn_open_browser': 'Ouvrir dans le navigateur',
 'escriptorium_btn_open_folder': 'Ouvrir le dossier',
 'escriptorium_btn_open_credentials': 'Ouvrir les identifiants',
 'escriptorium_btn_install_help': 'Installation / aide',
 'escriptorium_credentials_missing': 'Le fichier des identifiants est créé lors du premier téléchargement.',
 'escriptorium_credentials_header': 'Administrateur eScriptorium local',
 'escriptorium_credentials_user': 'Utilisateur',
 'escriptorium_credentials_password': 'Mot de passe',
 'escriptorium_credentials_existing': 'eScriptorium utilise les identifiants enregistrés dans le fichier local '
                                      'runtime.env.',
 'escriptorium_progress_placeholder': 'La progression et les messages techniques apparaissent ici.',
 'escriptorium_progress_prepare': 'Préparation du dossier de destination local',
 'escriptorium_progress_download_source': 'Téléchargement du code source officiel d’eScriptorium',
 'escriptorium_progress_extract_source': 'Extraction sécurisée de l’archive source',
 'escriptorium_progress_wait_server': 'Attente du serveur web local',
 'escriptorium_progress_done': 'Opération terminée',
 'escriptorium_task_busy': 'Une opération eScriptorium est déjà en cours.',
 'escriptorium_install_success': 'eScriptorium a été préparé dans {}.',
 'escriptorium_start_success': 'eScriptorium fonctionne. Le navigateur va s’ouvrir.',
 'escriptorium_stop_success': 'eScriptorium a été arrêté. Tous les projets et bases ont été conservés.',
 'escriptorium_error_not_installed': 'eScriptorium n’est pas encore installé. Ouvrez « Aide → eScriptorium » et '
                                     'téléchargez d’abord les fichiers requis.',
 'escriptorium_error_download_failed': 'Le téléchargement a échoué :\n{}',
 'escriptorium_error_archive_invalid': 'L’archive eScriptorium téléchargée est invalide ou incomplète :\n{}',
 'escriptorium_error_command_failed': 'Une commande eScriptorium a échoué :\n{}',
 'escriptorium_error_timeout': 'Délai dépassé pour l’opération suivante :\n{}',
 'escriptorium_error_server_not_ready': 'Les services ont démarré, mais le serveur web ne répond pas à l’adresse :\n{}',
 'escriptorium_error_unexpected': 'Erreur eScriptorium inattendue :\n{}',
 'help_nav_escriptorium': 'eScriptorium',
 'help_html_escriptorium': '<div class="card"><div class="h1">eScriptorium local sans Docker</div><p>Sélectionnez '
                           'Fedora, Linux Mint ou Windows 10/11 avec WSL2. Bottled Kraken automatise en arrière-plan '
                           'le téléchargement, les dépendances, l’environnement Python privé, la construction du '
                           'frontal, la base de données et les services.</p></div><div class="card"><div '
                           'class="h2">Composants installés</div><p>Fedora et Mint utilisent PostgreSQL, Redis, '
                           'Celery, Django, Kraken et un environnement Python privé. Sous Windows, la même pile Linux '
                           's’exécute dans WSL2. Docker et Docker Compose ne sont pas utilisés.</p></div><div '
                           'class="card"><div class="h2">Données et autorisations</div><p>Sources, réglages, '
                           'identifiants, journaux, base, médias et fichiers d’exécution restent dans le dossier de '
                           'données de Bottled Kraken. Une autorisation administrateur peut être demandée pour les '
                           'paquets système ou WSL2.</p></div>',
 'help_escriptorium_target': 'Dossier de destination : {}',
 'help_escriptorium_download_button': 'Installer / mettre à jour eScriptorium',
 'escriptorium_label_platform': 'Système d’exploitation :',
 'escriptorium_platform_fedora': 'Fedora Linux',
 'escriptorium_platform_mint': 'Linux Mint',
 'escriptorium_platform_windows_wsl': 'Windows 10/11 (WSL2)',
 'escriptorium_platform_unknown': 'Système inconnu',
 'escriptorium_platform_help': 'Sélectionnez le système sur lequel Bottled Kraken fonctionne actuellement. Une demande '
                               'd’autorisation administrateur peut apparaître une fois lors de l’installation des '
                               'composants système.',
 'escriptorium_status_platform_mismatch': 'Le système sélectionné ne correspond pas à cet ordinateur.',
 'escriptorium_status_prerequisites_missing': 'Installé, mais des composants système requis sont indisponibles.',
 'escriptorium_progress_check_prerequisites': 'Vérification des composants système requis',
 'escriptorium_progress_install_system_packages': 'Installation des composants système requis',
 'escriptorium_progress_create_runtime': 'Création de l’environnement privé eScriptorium',
 'escriptorium_progress_install_python': 'Installation des dépendances Python',
 'escriptorium_progress_build_frontend': 'Construction de l’interface web eScriptorium',
 'escriptorium_progress_initialize_database': 'Préparation des stockages locaux PostgreSQL et Redis',
 'escriptorium_progress_migrate_database': 'Mise à jour de la base eScriptorium',
 'escriptorium_progress_install_wsl': 'Installation de WSL2 et Ubuntu pour eScriptorium',
 'escriptorium_progress_configure_wsl': 'Configuration de l’environnement WSL2 privé',
 'escriptorium_progress_copy_source': 'Copie d’eScriptorium dans l’environnement local',
 'escriptorium_progress_start_services': 'Démarrage des services eScriptorium locaux',
 'escriptorium_progress_stop_services': 'Arrêt des services eScriptorium locaux',
 'escriptorium_error_platform_mismatch': 'Le système sélectionné ne correspond pas à cet ordinateur. Choisissez '
                                         'Fedora, Linux Mint ou Windows/WSL2 selon le cas.\n'
                                         '{}',
 'escriptorium_error_privilege_tool_missing': 'L’outil graphique d’administration est indisponible. Installez « pkexec '
                                              '»/Polkit puis réessayez.\n'
                                              '{}',
 'escriptorium_error_prerequisites_missing': 'Certains composants système requis n’ont pas pu être installés ou '
                                             'trouvés.\n'
                                             '{}',
 'escriptorium_error_package_install_failed': 'L’installation automatique des composants système requis a échoué.\n{}',
 'escriptorium_error_python_setup_failed': 'L’environnement Python privé d’eScriptorium n’a pas pu être créé.\n{}',
 'escriptorium_error_frontend_build_failed': 'L’interface web eScriptorium n’a pas pu être construite.\n{}',
 'escriptorium_error_database_setup_failed': 'La base locale eScriptorium n’a pas pu être préparée.\n{}',
 'escriptorium_error_wsl_missing': 'WSL est indisponible sur ce système Windows. Bottled Kraken n’a pas pu lancer '
                                   'l’installation automatique de WSL2.\n'
                                   '{}',
 'escriptorium_error_wsl_install_failed': 'L’installation automatique de WSL2/Ubuntu a échoué.\n{}',
 'escriptorium_error_restart_required': 'Windows doit être redémarré pour terminer l’activation de WSL2. Après le '
                                        'redémarrage, cliquez de nouveau sur « Démarrer le serveur ».\n'
                                        '{}',
 'escriptorium_error_folder_open_failed': 'Impossible d’ouvrir automatiquement le dossier ou le fichier :\n{}',
 'escriptorium_error_browser_open_failed': 'Impossible d’ouvrir automatiquement la page web dans le navigateur :\\n{}',
 'help_escriptorium_docs_button': 'Ouvrir la documentation eScriptorium',
 'escriptorium_status_working': 'eScriptorium est installé ou démarré en arrière-plan…',
 'escriptorium_status_cancelling': 'Annulation de l’opération eScriptorium…',
 'escriptorium_error_cancelled': 'L’opération eScriptorium a été annulée. Les paquets système déjà installés sont '
                                 'conservés ; une installation locale incomplète sera réparée lors de la prochaine '
                                 'installation ou mise à jour.',
 'escriptorium_error_server_not_running': 'eScriptorium n’est pas encore accessible. Attendez la fin de l’installation '
                                          'et du démarrage du serveur, puis réessayez :\n'
                                          '{}',
 'escriptorium_error_server_start_failed': 'Le serveur web eScriptorium s’est arrêté avant d’être accessible. Sortie '
                                           'technique :\n'
                                           '{}'}

__all__ = ["ESCRIPTORIUM_TEXTS"]
