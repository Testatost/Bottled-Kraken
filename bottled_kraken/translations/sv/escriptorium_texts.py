# eScriptorium user interface, native installation, and lifecycle texts.
ESCRIPTORIUM_TEXTS = {'menu_escriptorium': 'eScriptorium',
 'dlg_escriptorium_title': 'Lokalt eScriptorium',
 'escriptorium_dialog_intro': 'Välj operativsystem. Installera eller uppdatera först eScriptorium och starta sedan '
                              'servern. Bottled Kraken hämtar, installerar, konfigurerar och hanterar alla lokala '
                              'tjänster automatiskt i bakgrunden. Docker behövs inte.',
 'escriptorium_label_status': 'Status:',
 'escriptorium_label_install_dir': 'Lokal mapp:',
 'escriptorium_label_server_url': 'Serveradress:',
 'escriptorium_label_credentials': 'Inloggningsuppgifter:',
 'escriptorium_status_checking': 'Kontrollerar status…',
 'escriptorium_status_running': 'eScriptorium körs.',
 'escriptorium_status_stopped': 'Installerat men inte startat.',
 'escriptorium_status_not_installed': 'Inte installerat ännu. Använd först ”Installera / uppdatera eScriptorium”.',
 'escriptorium_btn_refresh': 'Uppdatera',
 'escriptorium_btn_start': 'Starta server',
 'escriptorium_btn_stop': 'Stoppa server',
 'escriptorium_btn_open_browser': 'Öppna i webbläsare',
 'escriptorium_btn_open_folder': 'Öppna mapp',
 'escriptorium_btn_open_credentials': 'Öppna inloggningsuppgifter',
 'escriptorium_btn_install_help': 'Installation / hjälp',
 'escriptorium_credentials_missing': 'Filen med inloggningsuppgifter skapas vid den första hämtningen.',
 'escriptorium_credentials_header': 'Lokal eScriptorium-administratör',
 'escriptorium_credentials_user': 'Användare',
 'escriptorium_credentials_password': 'Lösenord',
 'escriptorium_credentials_existing': 'runtime.env',
 'escriptorium_progress_placeholder': 'Förlopp och tekniska meddelanden visas här.',
 'escriptorium_progress_prepare': 'Förbereder den lokala målmappen',
 'escriptorium_progress_download_source': 'Hämtar officiell eScriptorium-källkod',
 'escriptorium_progress_extract_source': 'Packar upp källarkivet säkert',
 'escriptorium_progress_wait_server': 'Väntar på den lokala webbservern',
 'escriptorium_progress_done': 'Åtgärden är klar',
 'escriptorium_task_busy': 'En eScriptorium-åtgärd pågår redan.',
 'escriptorium_install_success': 'eScriptorium förbereddes i {}.',
 'escriptorium_start_success': 'Startar lokala eScriptorium-tjänster.',
 'escriptorium_stop_success': 'Stoppar lokala eScriptorium-tjänster.',
 'escriptorium_error_not_installed': 'eScriptorium är inte installerat ännu. Öppna “Hjälp → eScriptorium” och hämta '
                                     'först de filer som krävs.',
 'escriptorium_error_download_failed': 'Hämtningen misslyckades:\n{}',
 'escriptorium_error_archive_invalid': 'Det hämtade eScriptorium-arkivet är ogiltigt eller ofullständigt:\n{}',
 'escriptorium_error_command_failed': 'eScriptorium-kommandot misslyckades:\n{}',
 'escriptorium_error_timeout': 'Tidsgränsen överskreds för:\n{}',
 'escriptorium_error_server_not_ready': 'eScriptoriums webbserver är inte tillgänglig:\n{}',
 'escriptorium_error_unexpected': 'Oväntat eScriptorium-fel:\n{}',
 'help_nav_escriptorium': 'eScriptorium',
 'help_html_escriptorium': '<div class="card"><div class="h1">eScriptorium</div><p>Välj operativsystem och starta '
                           'sedan eScriptorium. Bottled Kraken hämtar, installerar, konfigurerar, startar och stoppar '
                           'automatiskt alla nödvändiga lokala tjänster i bakgrunden. Docker behövs '
                           'inte.</p></div><div class="card"><div class="h2">Lokal installation</div><p>Docker och '
                           'Docker Compose används inte. PostgreSQL, Redis, Celery, Django, Kraken och Python-miljön '
                           'hanteras lokalt av Bottled Kraken.</p></div><div class="card"><div '
                           'class="h2">Data</div><p>Välj systemet som Bottled Kraken körs på. Administratörsbehörighet '
                           'kan begäras en gång när systemkomponenterna installeras. Alla eScriptorium-data stannar i '
                           'Bottled Krakens användarmapp.</p></div>',
 'help_escriptorium_target': 'Målmapp: {}',
 'help_escriptorium_download_button': 'Installera eller uppdatera eScriptorium',
 'escriptorium_label_platform': 'Operativsystem:',
 'escriptorium_platform_fedora': 'Fedora Linux',
 'escriptorium_platform_mint': 'Linux Mint',
 'escriptorium_platform_windows_wsl': 'Windows 10/11 (WSL2)',
 'escriptorium_platform_unknown': 'Okänt system',
 'escriptorium_platform_help': 'Välj systemet som Bottled Kraken körs på. Administratörsbehörighet kan begäras en gång '
                               'när systemkomponenterna installeras.',
 'escriptorium_status_platform_mismatch': 'Det valda systemet matchar inte den här datorn.',
 'escriptorium_status_prerequisites_missing': 'Installerat, men nödvändiga systemkomponenter saknas.',
 'escriptorium_progress_check_prerequisites': 'Kontrollerar nödvändiga systemkomponenter',
 'escriptorium_progress_install_system_packages': 'Installerar nödvändiga systemkomponenter',
 'escriptorium_progress_create_runtime': 'Skapar privat eScriptorium-miljö',
 'escriptorium_progress_install_python': 'Installerar Python-beroenden',
 'escriptorium_progress_build_frontend': 'Bygger eScriptoriums webbgränssnitt',
 'escriptorium_progress_initialize_database': 'Förbereder lokala PostgreSQL- och Redis-datalager',
 'escriptorium_progress_migrate_database': 'Uppdaterar eScriptorium-databasen',
 'escriptorium_progress_install_wsl': 'Installerar WSL2 och Ubuntu för eScriptorium',
 'escriptorium_progress_configure_wsl': 'Konfigurerar privat WSL2-miljö',
 'escriptorium_progress_copy_source': 'Kopierar eScriptorium till lokal miljö',
 'escriptorium_progress_start_services': 'Startar lokala eScriptorium-tjänster',
 'escriptorium_progress_stop_services': 'Stoppar lokala eScriptorium-tjänster',
 'escriptorium_error_platform_mismatch': 'Det valda systemet matchar inte den här datorn.\n{}',
 'escriptorium_error_privilege_tool_missing': 'Välj systemet som Bottled Kraken körs på. Administratörsbehörighet kan '
                                              'begäras en gång när systemkomponenterna installeras.\n'
                                              '{}',
 'escriptorium_error_prerequisites_missing': 'Installerat, men nödvändiga systemkomponenter saknas.\n{}',
 'escriptorium_error_package_install_failed': 'Installationen av nödvändiga systemkomponenter misslyckades:\n{}',
 'escriptorium_error_python_setup_failed': 'Installationen av Python-beroenden misslyckades:\n{}',
 'escriptorium_error_frontend_build_failed': 'Byggandet av eScriptoriums webbgränssnitt misslyckades:\n{}',
 'escriptorium_error_database_setup_failed': 'Förberedelsen av lokala PostgreSQL- och Redis-datalager misslyckades:\n'
                                             '{}',
 'escriptorium_error_wsl_missing': 'WSL2 är inte tillgängligt eller kan inte startas:\n{}',
 'escriptorium_error_wsl_install_failed': 'Installationen av WSL2 och Ubuntu misslyckades:\n{}',
 'escriptorium_error_restart_required': 'Windows måste startas om för att slutföra WSL2-installationen. Kör sedan '
                                        'åtgärden igen.\n'
                                        '{}',
 'escriptorium_error_folder_open_failed': 'Mappen kunde inte öppnas:\n{}',
 'escriptorium_error_browser_open_failed': 'Webbsidan kunde inte öppnas automatiskt i webbläsaren:\\n{}',
 'help_escriptorium_docs_button': 'Dokumentation för eScriptorium',
 'escriptorium_status_working': 'eScriptorium installeras eller startas i bakgrunden…',
 'escriptorium_status_cancelling': 'eScriptorium-åtgärden avbryts…',
 'escriptorium_error_cancelled': 'eScriptorium-åtgärden avbröts. Redan installerade systempaket behålls; en '
                                 'ofullständig lokal installation repareras vid nästa installation eller uppdatering.',
 'escriptorium_error_server_not_running': 'eScriptorium kan ännu inte nås. Vänta tills installationen och '
                                          'serverstarten är klara och försök igen:\n'
                                          '{}',
 'escriptorium_error_server_start_failed': 'eScriptoriums webbserver avslutades innan den kunde nås. Teknisk utdata:\n'
                                           '{}'}

__all__ = ["ESCRIPTORIUM_TEXTS"]
