# eScriptorium user interface, native installation, and lifecycle texts.
ESCRIPTORIUM_TEXTS = {'menu_escriptorium': 'eScriptorium',
 'dlg_escriptorium_title': 'Lokale eScriptorium',
 'escriptorium_dialog_intro': 'Kies je besturingssysteem. Installeer of werk eScriptorium eerst bij en start daarna de '
                              'server. Bottled Kraken downloadt, installeert, configureert en beheert alle lokale '
                              'diensten automatisch op de achtergrond. Docker is niet nodig.',
 'escriptorium_label_status': 'Status:',
 'escriptorium_label_install_dir': 'Lokale map:',
 'escriptorium_label_server_url': 'Serveradres:',
 'escriptorium_label_credentials': 'Aanmeldgegevens:',
 'escriptorium_status_checking': 'Status controleren…',
 'escriptorium_status_running': 'eScriptorium wordt uitgevoerd.',
 'escriptorium_status_stopped': 'Geïnstalleerd, maar niet actief.',
 'escriptorium_status_not_installed': 'Nog niet geïnstalleerd. Gebruik eerst “eScriptorium installeren / bijwerken”.',
 'escriptorium_btn_refresh': 'Vernieuwen',
 'escriptorium_btn_start': 'Server starten',
 'escriptorium_btn_stop': 'Server stoppen',
 'escriptorium_btn_open_browser': 'Openen in browser',
 'escriptorium_btn_open_folder': 'Map openen',
 'escriptorium_btn_open_credentials': 'Aanmeldgegevens openen',
 'escriptorium_btn_install_help': 'Installatie / hulp',
 'escriptorium_credentials_missing': 'Het bestand met aanmeldgegevens wordt bij de eerste download gemaakt.',
 'escriptorium_credentials_header': 'Lokale eScriptorium-beheerder',
 'escriptorium_credentials_user': 'Gebruiker',
 'escriptorium_credentials_password': 'Wachtwoord',
 'escriptorium_credentials_existing': 'eScriptorium gebruikt de aanmeldgegevens uit het lokale bestand runtime.env.',
 'escriptorium_progress_placeholder': 'Voortgang en technische meldingen verschijnen hier.',
 'escriptorium_progress_prepare': 'Lokale doelmap voorbereiden',
 'escriptorium_progress_download_source': 'Officiële eScriptorium-broncode downloaden',
 'escriptorium_progress_extract_source': 'Bronarchief veilig uitpakken',
 'escriptorium_progress_wait_server': 'Wachten op de lokale webserver',
 'escriptorium_progress_done': 'Bewerking voltooid',
 'escriptorium_task_busy': 'Er wordt al een eScriptorium-bewerking uitgevoerd.',
 'escriptorium_install_success': 'eScriptorium is voorbereid in {}.',
 'escriptorium_start_success': 'eScriptorium draait. De browser wordt geopend.',
 'escriptorium_stop_success': 'eScriptorium is gestopt. Alle projecten en databases zijn behouden.',
 'escriptorium_error_not_installed': 'eScriptorium is nog niet geïnstalleerd. Open “Hulp → eScriptorium” en download '
                                     'eerst de vereiste bestanden.',
 'escriptorium_error_download_failed': 'De download is mislukt:\n{}',
 'escriptorium_error_archive_invalid': 'Het gedownloade eScriptorium-archief is ongeldig of onvolledig:\n{}',
 'escriptorium_error_command_failed': 'Een eScriptorium-opdracht is mislukt:\n{}',
 'escriptorium_error_timeout': 'Time-out bij de volgende bewerking:\n{}',
 'escriptorium_error_server_not_ready': 'De diensten zijn gestart, maar de webserver reageert niet op:\n{}',
 'escriptorium_error_unexpected': 'Onverwachte eScriptorium-fout:\n{}',
 'help_nav_escriptorium': 'eScriptorium',
 'help_html_escriptorium': '<div class="card"><div class="h1">Lokaal eScriptorium zonder Docker</div><p>Selecteer '
                           'Fedora, Linux Mint of Windows 10/11 met WSL2. Bottled Kraken automatiseert download, '
                           'afhankelijkheden, privé Python-omgeving, webbouw, database en diensten op de '
                           'achtergrond.</p></div><div class="card"><div class="h2">Geïnstalleerde '
                           'onderdelen</div><p>Fedora en Mint gebruiken PostgreSQL, Redis, Celery, Django, Kraken en '
                           'een privé Python-omgeving. Op Windows draait dezelfde Linux-stack in WSL2. Docker en '
                           'Docker Compose worden niet gebruikt.</p></div><div class="card"><div class="h2">Gegevens '
                           'en rechten</div><p>Broncode, instellingen, aanmeldgegevens, logboeken, database, media en '
                           'runtimebestanden blijven in de gegevensmap van Bottled Kraken. Voor systeempakketten of '
                           'WSL2 kan beheerdersautorisatie nodig zijn.</p></div>',
 'help_escriptorium_target': 'Doelmap: {}',
 'help_escriptorium_download_button': 'eScriptorium installeren / bijwerken',
 'escriptorium_label_platform': 'Besturingssysteem:',
 'escriptorium_platform_fedora': 'Fedora Linux',
 'escriptorium_platform_mint': 'Linux Mint',
 'escriptorium_platform_windows_wsl': 'Windows 10/11 (WSL2)',
 'escriptorium_platform_unknown': 'Onbekend systeem',
 'escriptorium_platform_help': 'Selecteer het systeem waarop Bottled Kraken nu draait. Tijdens de eenmalige '
                               'installatie van systeemonderdelen kan om beheerdersrechten worden gevraagd.',
 'escriptorium_status_platform_mismatch': 'Het geselecteerde systeem komt niet overeen met deze computer.',
 'escriptorium_status_prerequisites_missing': 'Geïnstalleerd, maar vereiste systeemonderdelen zijn niet beschikbaar.',
 'escriptorium_progress_check_prerequisites': 'Vereiste systeemonderdelen controleren',
 'escriptorium_progress_install_system_packages': 'Vereiste systeemonderdelen installeren',
 'escriptorium_progress_create_runtime': 'Privé eScriptorium-omgeving maken',
 'escriptorium_progress_install_python': 'Python-afhankelijkheden installeren',
 'escriptorium_progress_build_frontend': 'eScriptorium-webinterface bouwen',
 'escriptorium_progress_initialize_database': 'Lokale PostgreSQL- en Redis-opslag voorbereiden',
 'escriptorium_progress_migrate_database': 'eScriptorium-database bijwerken',
 'escriptorium_progress_install_wsl': 'WSL2 en Ubuntu voor eScriptorium installeren',
 'escriptorium_progress_configure_wsl': 'Privé WSL2-omgeving configureren',
 'escriptorium_progress_copy_source': 'eScriptorium naar de lokale omgeving kopiëren',
 'escriptorium_progress_start_services': 'Lokale eScriptorium-diensten starten',
 'escriptorium_progress_stop_services': 'Lokale eScriptorium-diensten stoppen',
 'escriptorium_error_platform_mismatch': 'Het geselecteerde systeem komt niet overeen met deze computer. Kies Fedora, '
                                         'Linux Mint of Windows/WSL2.\n'
                                         '{}',
 'escriptorium_error_privilege_tool_missing': 'Het grafische beheerdershulpmiddel is niet beschikbaar. Installeer '
                                              '“pkexec”/Polkit en probeer opnieuw.\n'
                                              '{}',
 'escriptorium_error_prerequisites_missing': 'Sommige vereiste systeemonderdelen konden niet worden geïnstalleerd of '
                                             'gevonden.\n'
                                             '{}',
 'escriptorium_error_package_install_failed': 'De automatische installatie van vereiste systeemonderdelen is mislukt.\n'
                                              '{}',
 'escriptorium_error_python_setup_failed': 'De privé Python-omgeving voor eScriptorium kon niet worden gemaakt.\n{}',
 'escriptorium_error_frontend_build_failed': 'De eScriptorium-webinterface kon niet worden gebouwd.\n{}',
 'escriptorium_error_database_setup_failed': 'De lokale eScriptorium-database kon niet worden voorbereid.\n{}',
 'escriptorium_error_wsl_missing': 'WSL is niet beschikbaar op dit Windows-systeem. Bottled Kraken kon de automatische '
                                   'WSL2-installatie niet starten.\n'
                                   '{}',
 'escriptorium_error_wsl_install_failed': 'De automatische installatie van WSL2/Ubuntu is mislukt.\n{}',
 'escriptorium_error_restart_required': 'Windows moet opnieuw worden gestart om WSL2 te activeren. Druk na de herstart '
                                        'opnieuw op “Server starten”.\n'
                                        '{}',
 'escriptorium_error_folder_open_failed': 'De map of het bestand kon niet automatisch worden geopend:\n{}',
 'escriptorium_error_browser_open_failed': 'De webpagina kon niet automatisch in de browser worden geopend:\\n{}',
 'help_escriptorium_docs_button': 'eScriptorium-documentatie openen',
 'escriptorium_status_working': 'eScriptorium wordt op de achtergrond geïnstalleerd of gestart…',
 'escriptorium_status_cancelling': 'De eScriptorium-bewerking wordt geannuleerd…',
 'escriptorium_error_cancelled': 'De eScriptorium-bewerking is geannuleerd. Reeds geïnstalleerde systeempakketten '
                                 'blijven behouden; een onvolledige lokale installatie wordt bij de volgende '
                                 'installatie of update hersteld.',
 'escriptorium_error_server_not_running': 'eScriptorium is nog niet bereikbaar. Wacht tot de installatie en het '
                                          'starten van de server zijn voltooid en probeer het opnieuw:\n'
                                          '{}',
 'escriptorium_error_server_start_failed': 'De eScriptorium-webserver is afgesloten voordat deze bereikbaar was. '
                                           'Technische uitvoer:\n'
                                           '{}'}

__all__ = ["ESCRIPTORIUM_TEXTS"]
