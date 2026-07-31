# eScriptorium user interface, native installation, and lifecycle texts.
ESCRIPTORIUM_TEXTS = {'menu_escriptorium': 'eScriptorium',
 'dlg_escriptorium_title': 'eScriptorium locale',
 'escriptorium_dialog_intro': 'Seleziona il sistema operativo. Prima installa o aggiorna eScriptorium, quindi avvia il '
                              'server. Bottled Kraken scarica, installa, configura e gestisce automaticamente tutti i '
                              'servizi locali in background. Docker non è necessario.',
 'escriptorium_label_status': 'Stato:',
 'escriptorium_label_install_dir': 'Cartella locale:',
 'escriptorium_label_server_url': 'Indirizzo del server:',
 'escriptorium_label_credentials': 'Credenziali:',
 'escriptorium_status_checking': 'Verifica dello stato…',
 'escriptorium_status_running': 'eScriptorium è in esecuzione.',
 'escriptorium_status_stopped': 'Installato, ma non in esecuzione.',
 'escriptorium_status_not_installed': 'Non ancora installato. Usa prima «Installa / aggiorna eScriptorium».',
 'escriptorium_btn_refresh': 'Aggiorna',
 'escriptorium_btn_start': 'Avvia server',
 'escriptorium_btn_stop': 'Arresta server',
 'escriptorium_btn_open_browser': 'Apri nel browser',
 'escriptorium_btn_open_folder': 'Apri cartella',
 'escriptorium_btn_open_credentials': 'Apri credenziali',
 'escriptorium_btn_install_help': 'Installazione / guida',
 'escriptorium_credentials_missing': 'Il file delle credenziali viene creato durante il primo download.',
 'escriptorium_credentials_header': 'Amministratore eScriptorium locale',
 'escriptorium_credentials_user': 'Utente',
 'escriptorium_credentials_password': 'Password',
 'escriptorium_credentials_existing': 'eScriptorium usa le credenziali salvate nel file locale runtime.env.',
 'escriptorium_progress_placeholder': 'Qui vengono mostrati avanzamento e messaggi tecnici.',
 'escriptorium_progress_prepare': 'Preparazione della cartella locale',
 'escriptorium_progress_download_source': 'Download del sorgente ufficiale di eScriptorium',
 'escriptorium_progress_extract_source': 'Estrazione sicura dell’archivio sorgente',
 'escriptorium_progress_wait_server': 'Attesa del server web locale',
 'escriptorium_progress_done': 'Operazione completata',
 'escriptorium_task_busy': 'È già in corso un’operazione eScriptorium.',
 'escriptorium_install_success': 'eScriptorium è stato preparato in {}.',
 'escriptorium_start_success': 'eScriptorium è in esecuzione. Il browser verrà aperto.',
 'escriptorium_stop_success': 'eScriptorium è stato arrestato. Tutti i progetti e i database sono stati conservati.',
 'escriptorium_error_not_installed': 'eScriptorium non è ancora installato. Apri «Guida → eScriptorium» e scarica '
                                     'prima i file necessari.',
 'escriptorium_error_download_failed': 'Download non riuscito:\n{}',
 'escriptorium_error_archive_invalid': 'L’archivio eScriptorium scaricato non è valido o è incompleto:\n{}',
 'escriptorium_error_command_failed': 'Un comando di eScriptorium è fallito:\n{}',
 'escriptorium_error_timeout': 'Tempo scaduto per l’operazione seguente:\n{}',
 'escriptorium_error_server_not_ready': 'I servizi sono stati avviati, ma il server web non risponde su:\n{}',
 'escriptorium_error_unexpected': 'Errore eScriptorium imprevisto:\n{}',
 'help_nav_escriptorium': 'eScriptorium',
 'help_html_escriptorium': '<div class="card"><div class="h1">eScriptorium locale senza Docker</div><p>Seleziona '
                           'Fedora, Linux Mint o Windows 10/11 con WSL2. Bottled Kraken automatizza download, '
                           'dipendenze, ambiente Python privato, compilazione web, database e servizi in '
                           'background.</p></div><div class="card"><div class="h2">Componenti '
                           'installati</div><p>Fedora e Mint usano PostgreSQL, Redis, Celery, Django, Kraken e un '
                           'ambiente Python privato. In Windows lo stesso stack Linux gira in WSL2. Docker e Docker '
                           'Compose non sono usati.</p></div><div class="card"><div class="h2">Dati e '
                           'permessi</div><p>Sorgenti, impostazioni, credenziali, log, database, media e file runtime '
                           'restano nella cartella dati di Bottled Kraken. Può essere richiesta l’autorizzazione '
                           'amministratore per i pacchetti di sistema o WSL2.</p></div>',
 'help_escriptorium_target': 'Cartella di destinazione: {}',
 'help_escriptorium_download_button': 'Installa / aggiorna eScriptorium',
 'escriptorium_label_platform': 'Sistema operativo:',
 'escriptorium_platform_fedora': 'Fedora Linux',
 'escriptorium_platform_mint': 'Linux Mint',
 'escriptorium_platform_windows_wsl': 'Windows 10/11 (WSL2)',
 'escriptorium_platform_unknown': 'Sistema sconosciuto',
 'escriptorium_platform_help': 'Seleziona il sistema su cui è in esecuzione Bottled Kraken. Durante l’installazione '
                               'iniziale dei componenti di sistema può comparire una richiesta di amministratore.',
 'escriptorium_status_platform_mismatch': 'Il sistema selezionato non corrisponde a questo computer.',
 'escriptorium_status_prerequisites_missing': 'Installato, ma alcuni componenti di sistema necessari non sono '
                                              'disponibili.',
 'escriptorium_progress_check_prerequisites': 'Verifica dei componenti di sistema necessari',
 'escriptorium_progress_install_system_packages': 'Installazione dei componenti di sistema necessari',
 'escriptorium_progress_create_runtime': 'Creazione dell’ambiente privato di eScriptorium',
 'escriptorium_progress_install_python': 'Installazione delle dipendenze Python',
 'escriptorium_progress_build_frontend': 'Creazione dell’interfaccia web di eScriptorium',
 'escriptorium_progress_initialize_database': 'Preparazione degli archivi locali PostgreSQL e Redis',
 'escriptorium_progress_migrate_database': 'Aggiornamento del database di eScriptorium',
 'escriptorium_progress_install_wsl': 'Installazione di WSL2 e Ubuntu per eScriptorium',
 'escriptorium_progress_configure_wsl': 'Configurazione dell’ambiente WSL2 privato',
 'escriptorium_progress_copy_source': 'Copia di eScriptorium nell’ambiente locale',
 'escriptorium_progress_start_services': 'Avvio dei servizi locali di eScriptorium',
 'escriptorium_progress_stop_services': 'Arresto dei servizi locali di eScriptorium',
 'escriptorium_error_platform_mismatch': 'Il sistema selezionato non corrisponde a questo computer. Scegli Fedora, '
                                         'Linux Mint o Windows/WSL2.\n'
                                         '{}',
 'escriptorium_error_privilege_tool_missing': 'Lo strumento grafico di amministrazione non è disponibile. Installa '
                                              '“pkexec”/Polkit e riprova.\n'
                                              '{}',
 'escriptorium_error_prerequisites_missing': 'Alcuni componenti di sistema necessari non sono stati installati o '
                                             'trovati.\n'
                                             '{}',
 'escriptorium_error_package_install_failed': 'L’installazione automatica dei componenti di sistema è fallita.\n{}',
 'escriptorium_error_python_setup_failed': 'Impossibile creare l’ambiente Python privato per eScriptorium.\n{}',
 'escriptorium_error_frontend_build_failed': 'Impossibile creare l’interfaccia web di eScriptorium.\n{}',
 'escriptorium_error_database_setup_failed': 'Impossibile preparare il database locale di eScriptorium.\n{}',
 'escriptorium_error_wsl_missing': 'WSL non è disponibile in questo sistema Windows. Bottled Kraken non ha potuto '
                                   'avviare l’installazione automatica di WSL2.\n'
                                   '{}',
 'escriptorium_error_wsl_install_failed': 'L’installazione automatica di WSL2/Ubuntu è fallita.\n{}',
 'escriptorium_error_restart_required': 'È necessario riavviare Windows per completare l’attivazione di WSL2. Dopo il '
                                        'riavvio premi di nuovo “Avvia server”.\n'
                                        '{}',
 'escriptorium_error_folder_open_failed': 'Impossibile aprire automaticamente la cartella o il file:\n{}',
 'escriptorium_error_browser_open_failed': 'Impossibile aprire automaticamente la pagina web nel browser:\\n{}',
 'help_escriptorium_docs_button': 'Apri la documentazione di eScriptorium',
 'escriptorium_status_working': 'eScriptorium viene installato o avviato in background…',
 'escriptorium_status_cancelling': 'Annullamento dell’operazione eScriptorium…',
 'escriptorium_error_cancelled': 'L’operazione eScriptorium è stata annullata. I pacchetti di sistema già installati '
                                 'vengono conservati; un’installazione locale incompleta sarà riparata alla successiva '
                                 'installazione o aggiornamento.',
 'escriptorium_error_server_not_running': 'eScriptorium non è ancora raggiungibile. Attendi il completamento '
                                          'dell’installazione e dell’avvio del server, quindi riprova:\n'
                                          '{}',
 'escriptorium_error_server_start_failed': 'Il server web eScriptorium si è arrestato prima di diventare '
                                           'raggiungibile. Output tecnico:\n'
                                           '{}'}

__all__ = ["ESCRIPTORIUM_TEXTS"]
