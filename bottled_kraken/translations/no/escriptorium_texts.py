# eScriptorium user interface, native installation, and lifecycle texts.
ESCRIPTORIUM_TEXTS = {'menu_escriptorium': 'eScriptorium',
 'dlg_escriptorium_title': 'Lokal eScriptorium',
 'escriptorium_dialog_intro': 'Velg operativsystemet ditt. Installer eller oppdater eScriptorium først, og start '
                              'deretter serveren. Bottled Kraken laster ned, installerer, konfigurerer og '
                              'administrerer alle lokale tjenester automatisk i bakgrunnen. Docker er ikke nødvendig.',
 'escriptorium_label_status': 'Status:',
 'escriptorium_label_install_dir': 'Lokal mappe:',
 'escriptorium_label_server_url': 'Serveradresse:',
 'escriptorium_label_credentials': 'Påloggingsdata:',
 'escriptorium_status_checking': 'Kontrollerer status…',
 'escriptorium_status_running': 'eScriptorium kjører.',
 'escriptorium_status_stopped': 'Installert, men ikke startet.',
 'escriptorium_status_not_installed': 'Ikke installert ennå. Bruk først «Installer / oppdater eScriptorium».',
 'escriptorium_btn_refresh': 'Oppdater',
 'escriptorium_btn_start': 'Start server',
 'escriptorium_btn_stop': 'Stopp server',
 'escriptorium_btn_open_browser': 'Åpne i nettleser',
 'escriptorium_btn_open_folder': 'Åpne mappe',
 'escriptorium_btn_open_credentials': 'Åpne påloggingsdata',
 'escriptorium_btn_install_help': 'Installasjon / hjelp',
 'escriptorium_credentials_missing': 'Filen med påloggingsdata opprettes ved første nedlasting.',
 'escriptorium_credentials_header': 'Lokal eScriptorium-administrator',
 'escriptorium_credentials_user': 'Bruker',
 'escriptorium_credentials_password': 'Passord',
 'escriptorium_credentials_existing': 'runtime.env',
 'escriptorium_progress_placeholder': 'Fremdrift og tekniske meldinger vises her.',
 'escriptorium_progress_prepare': 'Forbereder lokal målmappe',
 'escriptorium_progress_download_source': 'Laster ned offisiell eScriptorium-kildekode',
 'escriptorium_progress_extract_source': 'Pakker ut kildearkivet sikkert',
 'escriptorium_progress_wait_server': 'Venter på den lokale webserveren',
 'escriptorium_progress_done': 'Handlingen er fullført',
 'escriptorium_task_busy': 'En eScriptorium-handling kjører allerede.',
 'escriptorium_install_success': 'eScriptorium ble klargjort i {}.',
 'escriptorium_start_success': 'Starter lokale eScriptorium-tjenester.',
 'escriptorium_stop_success': 'Stopper lokale eScriptorium-tjenester.',
 'escriptorium_error_not_installed': 'eScriptorium er ikke installert ennå. Åpne “Hjelp → eScriptorium” og last ned de '
                                     'nødvendige filene først.',
 'escriptorium_error_download_failed': 'Nedlastingen mislyktes:\n{}',
 'escriptorium_error_archive_invalid': 'Det nedlastede eScriptorium-arkivet er ugyldig eller ufullstendig:\n{}',
 'escriptorium_error_command_failed': 'eScriptorium-kommandoen mislyktes:\n{}',
 'escriptorium_error_timeout': 'Tidsavbrudd for følgende handling:\n{}',
 'escriptorium_error_server_not_ready': 'eScriptoriums nettserver er ikke tilgjengelig:\n{}',
 'escriptorium_error_unexpected': 'Uventet eScriptorium-feil:\n{}',
 'help_nav_escriptorium': 'eScriptorium',
 'help_html_escriptorium': '<div class="card"><div class="h1">eScriptorium</div><p>Velg operativsystem, og start '
                           'deretter eScriptorium. Bottled Kraken laster ned, installerer, konfigurerer, starter og '
                           'stopper automatisk alle nødvendige lokale tjenester i bakgrunnen. Docker er ikke '
                           'nødvendig.</p></div><div class="card"><div class="h2">Lokal installasjon</div><p>Docker og '
                           'Docker Compose brukes ikke. PostgreSQL, Redis, Celery, Django, Kraken og Python-miljøet '
                           'administreres lokalt av Bottled Kraken.</p></div><div class="card"><div '
                           'class="h2">Data</div><p>Velg systemet som Bottled Kraken kjører på. Det kan bli bedt om '
                           'administratorgodkjenning én gang under installasjonen av systemkomponenter. Alle '
                           'eScriptorium-data blir værende i Bottled Krakens brukermappe.</p></div>',
 'help_escriptorium_target': 'Målmappe: {}',
 'help_escriptorium_download_button': 'Installer eller oppdater eScriptorium',
 'escriptorium_label_platform': 'Operativsystem:',
 'escriptorium_platform_fedora': 'Fedora Linux',
 'escriptorium_platform_mint': 'Linux Mint',
 'escriptorium_platform_windows_wsl': 'Windows 10/11 (WSL2)',
 'escriptorium_platform_unknown': 'Ukjent system',
 'escriptorium_platform_help': 'Velg systemet Bottled Kraken kjører på. Administratorgodkjenning kan bli forespurt én '
                               'gang under installasjonen av systemkomponenter.',
 'escriptorium_status_platform_mismatch': 'Valgt system samsvarer ikke med denne datamaskinen.',
 'escriptorium_status_prerequisites_missing': 'Installert, men nødvendige systemkomponenter er ikke tilgjengelige.',
 'escriptorium_progress_check_prerequisites': 'Kontrollerer nødvendige systemkomponenter',
 'escriptorium_progress_install_system_packages': 'Installerer nødvendige systemkomponenter',
 'escriptorium_progress_create_runtime': 'Oppretter privat eScriptorium-miljø',
 'escriptorium_progress_install_python': 'Installerer Python-avhengigheter',
 'escriptorium_progress_build_frontend': 'Bygger eScriptoriums webgrensesnitt',
 'escriptorium_progress_initialize_database': 'Klargjør lokale PostgreSQL- og Redis-datalagre',
 'escriptorium_progress_migrate_database': 'Oppdaterer eScriptorium-databasen',
 'escriptorium_progress_install_wsl': 'Installerer WSL2 og Ubuntu for eScriptorium',
 'escriptorium_progress_configure_wsl': 'Konfigurerer privat WSL2-miljø',
 'escriptorium_progress_copy_source': 'Kopierer eScriptorium til lokalt miljø',
 'escriptorium_progress_start_services': 'Starter lokale eScriptorium-tjenester',
 'escriptorium_progress_stop_services': 'Stopper lokale eScriptorium-tjenester',
 'escriptorium_error_platform_mismatch': 'Valgt system samsvarer ikke med denne datamaskinen.\n{}',
 'escriptorium_error_privilege_tool_missing': 'Velg systemet Bottled Kraken kjører på. Administratorgodkjenning kan '
                                              'bli forespurt én gang under installasjonen av systemkomponenter.\n'
                                              '{}',
 'escriptorium_error_prerequisites_missing': 'Installert, men nødvendige systemkomponenter er ikke tilgjengelige.\n{}',
 'escriptorium_error_package_install_failed': 'Installasjonen av nødvendige systemkomponenter mislyktes:\n{}',
 'escriptorium_error_python_setup_failed': 'Installasjonen av Python-avhengigheter mislyktes:\n{}',
 'escriptorium_error_frontend_build_failed': 'Byggingen av eScriptoriums nettgrensesnitt mislyktes:\n{}',
 'escriptorium_error_database_setup_failed': 'Klargjøringen av lokale PostgreSQL- og Redis-datalagre mislyktes:\n{}',
 'escriptorium_error_wsl_missing': 'WSL2 er ikke tilgjengelig eller kan ikke startes:\n{}',
 'escriptorium_error_wsl_install_failed': 'Installasjonen av WSL2 og Ubuntu mislyktes:\n{}',
 'escriptorium_error_restart_required': 'Windows må startes på nytt for å fullføre WSL2-installasjonen. Kjør deretter '
                                        'handlingen på nytt.\n'
                                        '{}',
 'escriptorium_error_folder_open_failed': 'Mappen kunne ikke åpnes:\n{}',
 'escriptorium_error_browser_open_failed': 'Nettsiden kunne ikke åpnes automatisk i nettleseren:\\n{}',
 'help_escriptorium_docs_button': 'Dokumentasjon for eScriptorium',
 'escriptorium_status_working': 'eScriptorium installeres eller startes i bakgrunnen…',
 'escriptorium_status_cancelling': 'eScriptorium-operasjonen avbrytes…',
 'escriptorium_error_cancelled': 'eScriptorium-operasjonen ble avbrutt. Systempakker som allerede er installert, '
                                 'beholdes; en ufullstendig lokal installasjon repareres ved neste installasjon eller '
                                 'oppdatering.',
 'escriptorium_error_server_not_running': 'eScriptorium er ikke tilgjengelig ennå. Vent til installasjonen og '
                                          'serveroppstarten er fullført, og prøv igjen:\n'
                                          '{}',
 'escriptorium_error_server_start_failed': 'eScriptorium-webserveren avsluttet før den ble tilgjengelig. Teknisk '
                                           'utdata:\n'
                                           '{}'}

__all__ = ["ESCRIPTORIUM_TEXTS"]
