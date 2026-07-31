# eScriptorium user interface, native installation, and lifecycle texts.
ESCRIPTORIUM_TEXTS = {'menu_escriptorium': 'eScriptorium',
 'dlg_escriptorium_title': 'Lokal eScriptorium',
 'escriptorium_dialog_intro': 'Vælg dit operativsystem. Installer eller opdater først eScriptorium, og start derefter '
                              'serveren. Bottled Kraken henter, installerer, konfigurerer og styrer automatisk alle '
                              'lokale tjenester i baggrunden. Docker er ikke nødvendigt.',
 'escriptorium_label_status': 'Status:',
 'escriptorium_label_install_dir': 'Lokal mappe:',
 'escriptorium_label_server_url': 'Serveradresse:',
 'escriptorium_label_credentials': 'Loginoplysninger:',
 'escriptorium_status_checking': 'Kontrollerer status…',
 'escriptorium_status_running': 'eScriptorium kører.',
 'escriptorium_status_stopped': 'Installeret, men ikke startet.',
 'escriptorium_status_not_installed': 'Ikke installeret endnu. Brug først “Installer / opdater eScriptorium”.',
 'escriptorium_btn_refresh': 'Opdater',
 'escriptorium_btn_start': 'Start server',
 'escriptorium_btn_stop': 'Stop server',
 'escriptorium_btn_open_browser': 'Åbn i browser',
 'escriptorium_btn_open_folder': 'Åbn mappe',
 'escriptorium_btn_open_credentials': 'Åbn loginoplysninger',
 'escriptorium_btn_install_help': 'Installation / hjælp',
 'escriptorium_credentials_missing': 'Filen med loginoplysninger oprettes ved den første download.',
 'escriptorium_credentials_header': 'Lokal eScriptorium-administrator',
 'escriptorium_credentials_user': 'Bruger',
 'escriptorium_credentials_password': 'Adgangskode',
 'escriptorium_credentials_existing': 'runtime.env',
 'escriptorium_progress_placeholder': 'Fremdrift og tekniske meddelelser vises her.',
 'escriptorium_progress_prepare': 'Forbereder den lokale målmappe',
 'escriptorium_progress_download_source': 'Downloader den officielle eScriptorium-kildekode',
 'escriptorium_progress_extract_source': 'Pakker kildearkivet sikkert ud',
 'escriptorium_progress_wait_server': 'Venter på den lokale webserver',
 'escriptorium_progress_done': 'Handlingen er fuldført',
 'escriptorium_task_busy': 'En eScriptorium-handling kører allerede.',
 'escriptorium_install_success': 'eScriptorium blev forberedt i {}.',
 'escriptorium_start_success': 'Starter lokale eScriptorium-tjenester.',
 'escriptorium_stop_success': 'Stopper lokale eScriptorium-tjenester.',
 'escriptorium_error_not_installed': 'eScriptorium er endnu ikke installeret. Åbn “Hjælp → eScriptorium”, og download '
                                     'først de nødvendige filer.',
 'escriptorium_error_download_failed': 'Download mislykkedes:\n{}',
 'escriptorium_error_archive_invalid': 'Det downloadede eScriptorium-arkiv er ugyldigt eller ufuldstændigt:\n{}',
 'escriptorium_error_command_failed': 'eScriptorium-kommandoen mislykkedes:\n{}',
 'escriptorium_error_timeout': 'Tidsgrænsen blev overskredet for:\n{}',
 'escriptorium_error_server_not_ready': 'eScriptoriums webserver er ikke tilgængelig:\n{}',
 'escriptorium_error_unexpected': 'Uventet eScriptorium-fejl:\n{}',
 'help_nav_escriptorium': 'eScriptorium',
 'help_html_escriptorium': '<div class="card"><div class="h1">eScriptorium</div><p>Vælg dit operativsystem, og start '
                           'derefter eScriptorium. Bottled Kraken downloader, installerer, konfigurerer, starter og '
                           'stopper automatisk alle nødvendige lokale tjenester i baggrunden. Docker er ikke '
                           'nødvendigt.</p></div><div class="card"><div class="h2">Lokal installation</div><p>Docker '
                           'og Docker Compose anvendes ikke. PostgreSQL, Redis, Celery, Django, Kraken og '
                           'Python-miljøet administreres lokalt af Bottled Kraken.</p></div><div class="card"><div '
                           'class="h2">Data</div><p>Vælg det system, som Bottled Kraken kører på. Der kan blive bedt '
                           'om administratorgodkendelse én gang under installationen af systemkomponenter. Alle '
                           'eScriptorium-data bliver i Bottled Krakens brugermappe.</p></div>',
 'help_escriptorium_target': 'Målmappe: {}',
 'help_escriptorium_download_button': 'Installer eller opdater eScriptorium',
 'escriptorium_label_platform': 'Operativsystem:',
 'escriptorium_platform_fedora': 'Fedora Linux',
 'escriptorium_platform_mint': 'Linux Mint',
 'escriptorium_platform_windows_wsl': 'Windows 10/11 (WSL2)',
 'escriptorium_platform_unknown': 'Ukendt system',
 'escriptorium_platform_help': 'Vælg det system, som Bottled Kraken kører på. Der kan blive bedt om '
                               'administratorgodkendelse én gang under installationen af systemkomponenter.',
 'escriptorium_status_platform_mismatch': 'Det valgte system passer ikke til denne computer.',
 'escriptorium_status_prerequisites_missing': 'Installeret, men nødvendige systemkomponenter er ikke tilgængelige.',
 'escriptorium_progress_check_prerequisites': 'Kontrollerer nødvendige systemkomponenter',
 'escriptorium_progress_install_system_packages': 'Installerer nødvendige systemkomponenter',
 'escriptorium_progress_create_runtime': 'Opretter privat eScriptorium-miljø',
 'escriptorium_progress_install_python': 'Installerer Python-afhængigheder',
 'escriptorium_progress_build_frontend': 'Bygger eScriptoriums webgrænseflade',
 'escriptorium_progress_initialize_database': 'Forbereder lokale PostgreSQL- og Redis-datalagre',
 'escriptorium_progress_migrate_database': 'Opdaterer eScriptorium-databasen',
 'escriptorium_progress_install_wsl': 'Installerer WSL2 og Ubuntu til eScriptorium',
 'escriptorium_progress_configure_wsl': 'Konfigurerer privat WSL2-miljø',
 'escriptorium_progress_copy_source': 'Kopierer eScriptorium til det lokale miljø',
 'escriptorium_progress_start_services': 'Starter lokale eScriptorium-tjenester',
 'escriptorium_progress_stop_services': 'Stopper lokale eScriptorium-tjenester',
 'escriptorium_error_platform_mismatch': 'Det valgte system passer ikke til denne computer.\n{}',
 'escriptorium_error_privilege_tool_missing': 'Vælg det system, som Bottled Kraken kører på. Der kan blive bedt om '
                                              'administratorgodkendelse én gang under installationen af '
                                              'systemkomponenter.\n'
                                              '{}',
 'escriptorium_error_prerequisites_missing': 'Installeret, men nødvendige systemkomponenter er ikke tilgængelige.\n{}',
 'escriptorium_error_package_install_failed': 'Installationen af de nødvendige systemkomponenter mislykkedes:\n{}',
 'escriptorium_error_python_setup_failed': 'Installationen af Python-afhængigheder mislykkedes:\n{}',
 'escriptorium_error_frontend_build_failed': 'Opbygningen af eScriptoriums webgrænseflade mislykkedes:\n{}',
 'escriptorium_error_database_setup_failed': 'Forberedelsen af de lokale PostgreSQL- og Redis-datalagre mislykkedes:\n'
                                             '{}',
 'escriptorium_error_wsl_missing': 'WSL2 er ikke tilgængelig eller kan ikke startes:\n{}',
 'escriptorium_error_wsl_install_failed': 'Installationen af WSL2 og Ubuntu mislykkedes:\n{}',
 'escriptorium_error_restart_required': 'Windows skal genstartes for at fuldføre WSL2-installationen. Kør derefter '
                                        'handlingen igen.\n'
                                        '{}',
 'escriptorium_error_folder_open_failed': 'Mappen kunne ikke åbnes:\n{}',
 'escriptorium_error_browser_open_failed': 'Websiden kunne ikke åbnes automatisk:\\n{}',
 'help_escriptorium_docs_button': 'Dokumentation til eScriptorium',
 'escriptorium_status_working': 'eScriptorium installeres eller startes i baggrunden…',
 'escriptorium_status_cancelling': 'eScriptorium-handlingen annulleres…',
 'escriptorium_error_cancelled': 'eScriptorium-handlingen blev annulleret. Allerede installerede systempakker bevares; '
                                 'en ufuldstændig lokal installation repareres ved næste installation eller '
                                 'opdatering.',
 'escriptorium_error_server_not_running': 'eScriptorium kan endnu ikke nås. Vent, til installationen og serverstarten '
                                          'er færdige, og prøv igen:\n'
                                          '{}',
 'escriptorium_error_server_start_failed': 'eScriptorium-webserveren stoppede, før den kunne nås. Teknisk output:\n{}'}

__all__ = ["ESCRIPTORIUM_TEXTS"]
