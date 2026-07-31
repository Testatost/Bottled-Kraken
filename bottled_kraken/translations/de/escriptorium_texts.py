# eScriptorium user interface, native installation, and lifecycle texts.
ESCRIPTORIUM_TEXTS = {'menu_escriptorium': 'eScriptorium',
 'dlg_escriptorium_title': 'Lokales eScriptorium',
 'escriptorium_dialog_intro': 'Wähle dein Betriebssystem aus. Installiere oder aktualisiere eScriptorium zuerst und '
                              'starte danach den Server. Bottled Kraken erledigt Download, Installation, Konfiguration '
                              'und Verwaltung aller lokalen Dienste automatisch im Hintergrund. Docker wird nicht '
                              'benötigt.',
 'escriptorium_label_status': 'Status:',
 'escriptorium_label_install_dir': 'Lokaler Ordner:',
 'escriptorium_label_server_url': 'Server-Adresse:',
 'escriptorium_label_credentials': 'Anmeldedaten:',
 'escriptorium_status_checking': 'Status wird geprüft …',
 'escriptorium_status_running': 'eScriptorium läuft.',
 'escriptorium_status_stopped': 'Installiert, aber nicht gestartet.',
 'escriptorium_status_not_installed': 'Noch nicht installiert. Verwende zuerst „eScriptorium installieren / '
                                      'aktualisieren“.',
 'escriptorium_btn_refresh': 'Aktualisieren',
 'escriptorium_btn_start': 'Server starten',
 'escriptorium_btn_stop': 'Server stoppen',
 'escriptorium_btn_open_browser': 'Im Browser öffnen',
 'escriptorium_btn_open_folder': 'Ordner öffnen',
 'escriptorium_btn_open_credentials': 'Anmeldedaten öffnen',
 'escriptorium_btn_install_help': 'Installation / Hilfe',
 'escriptorium_credentials_missing': 'Die Datei mit den Anmeldedaten wird beim ersten Download erzeugt.',
 'escriptorium_credentials_header': 'Lokaler eScriptorium-Administrator',
 'escriptorium_credentials_user': 'Benutzer',
 'escriptorium_credentials_password': 'Passwort',
 'escriptorium_credentials_existing': 'eScriptorium verwendet die Zugangsdaten aus der lokalen Datei runtime.env.',
 'escriptorium_progress_placeholder': 'Fortschritt und technische Meldungen erscheinen hier.',
 'escriptorium_progress_prepare': 'Lokalen Zielordner vorbereiten',
 'escriptorium_progress_download_source': 'Offiziellen eScriptorium-Quellstand herunterladen',
 'escriptorium_progress_extract_source': 'Quellarchiv sicher entpacken',
 'escriptorium_progress_wait_server': 'Auf den lokalen Webserver warten',
 'escriptorium_progress_done': 'Vorgang abgeschlossen',
 'escriptorium_task_busy': 'Es läuft bereits ein eScriptorium-Vorgang.',
 'escriptorium_install_success': 'eScriptorium wurde unter {} vorbereitet.',
 'escriptorium_start_success': 'eScriptorium läuft. Der Browser wird geöffnet.',
 'escriptorium_stop_success': 'eScriptorium wurde beendet. Alle Projekte und Datenbanken bleiben erhalten.',
 'escriptorium_error_not_installed': 'eScriptorium ist noch nicht installiert. Öffne „Hinweise → eScriptorium“ und '
                                     'lade zuerst die benötigten Dateien herunter.',
 'escriptorium_error_download_failed': 'Der Download ist fehlgeschlagen:\n{}',
 'escriptorium_error_archive_invalid': 'Das heruntergeladene eScriptorium-Archiv ist ungültig oder unvollständig:\n{}',
 'escriptorium_error_command_failed': 'Ein eScriptorium-Befehl ist fehlgeschlagen:\n{}',
 'escriptorium_error_timeout': 'Zeitüberschreitung bei folgendem Vorgang:\n{}',
 'escriptorium_error_server_not_ready': 'Die Dienste wurden gestartet, aber der Webserver antwortet nicht unter:\n{}',
 'escriptorium_error_unexpected': 'Unerwarteter eScriptorium-Fehler:\n{}',
 'help_nav_escriptorium': 'eScriptorium',
 'help_html_escriptorium': '<div class="card"><div class="h1">Lokales eScriptorium ohne Docker</div><p>Wähle Fedora, '
                           'Linux Mint oder Windows 10/11 mit WSL2 aus. Bottled Kraken erledigt Download, Installation '
                           'der Abhängigkeiten, private Python-Umgebung, Frontend-Build, Datenbankvorbereitung und '
                           'Dienststeuerung automatisch im Hintergrund.</p></div><div class="card"><div '
                           'class="h2">Installierte Komponenten</div><p>Fedora und Mint verwenden lokales PostgreSQL, '
                           'Redis, Celery, Django, Kraken und eine private Python-Umgebung. Unter Windows läuft '
                           'derselbe Linux-Stack in WSL2. Docker und Docker Compose werden nicht '
                           'verwendet.</p></div><div class="card"><div class="h2">Daten und '
                           'Berechtigungen</div><p>Quellcode, Einstellungen, Zugangsdaten, Protokolle, Datenbankdaten, '
                           'Medien und Laufzeitdateien liegen unterhalb des Bottled-Kraken-Benutzerdatenordners. Bei '
                           'der Installation von Betriebssystempaketen oder WSL2 kann eine Administratorabfrage '
                           'erscheinen.</p></div>',
 'help_escriptorium_target': 'Zielordner: {}',
 'help_escriptorium_download_button': 'eScriptorium installieren / aktualisieren',
 'escriptorium_label_platform': 'Betriebssystem:',
 'escriptorium_platform_fedora': 'Fedora Linux',
 'escriptorium_platform_mint': 'Linux Mint',
 'escriptorium_platform_windows_wsl': 'Windows 10/11 (WSL2)',
 'escriptorium_platform_unknown': 'Unbekanntes System',
 'escriptorium_platform_help': 'Wähle das Betriebssystem aus, auf dem Bottled Kraken gerade läuft. Während der '
                               'einmaligen Installation von Systemkomponenten kann eine Administratorabfrage '
                               'erscheinen.',
 'escriptorium_status_platform_mismatch': 'Das ausgewählte Betriebssystem passt nicht zu diesem Computer.',
 'escriptorium_status_prerequisites_missing': 'Installiert, aber benötigte Systemkomponenten sind nicht verfügbar.',
 'escriptorium_progress_check_prerequisites': 'Benötigte Systemkomponenten werden geprüft',
 'escriptorium_progress_install_system_packages': 'Benötigte Systemkomponenten werden installiert',
 'escriptorium_progress_create_runtime': 'Private eScriptorium-Laufzeitumgebung wird erstellt',
 'escriptorium_progress_install_python': 'Python-Abhängigkeiten werden installiert',
 'escriptorium_progress_build_frontend': 'eScriptorium-Weboberfläche wird erstellt',
 'escriptorium_progress_initialize_database': 'Lokale PostgreSQL- und Redis-Datenspeicher werden vorbereitet',
 'escriptorium_progress_migrate_database': 'eScriptorium-Datenbank wird aktualisiert',
 'escriptorium_progress_install_wsl': 'WSL2 und Ubuntu für eScriptorium werden installiert',
 'escriptorium_progress_configure_wsl': 'Private WSL2-Umgebung wird konfiguriert',
 'escriptorium_progress_copy_source': 'eScriptorium wird in die lokale Laufzeitumgebung kopiert',
 'escriptorium_progress_start_services': 'Lokale eScriptorium-Dienste werden gestartet',
 'escriptorium_progress_stop_services': 'Lokale eScriptorium-Dienste werden beendet',
 'escriptorium_error_platform_mismatch': 'Das ausgewählte Betriebssystem passt nicht zu diesem Computer. Wähle '
                                         'entsprechend Fedora, Linux Mint oder Windows/WSL2 aus.\n'
                                         '{}',
 'escriptorium_error_privilege_tool_missing': 'Das grafische Administratorwerkzeug ist nicht verfügbar. Installiere '
                                              '„pkexec“/Polkit und versuche es erneut.\n'
                                              '{}',
 'escriptorium_error_prerequisites_missing': 'Einige benötigte Systemkomponenten konnten nicht installiert oder '
                                             'gefunden werden.\n'
                                             '{}',
 'escriptorium_error_package_install_failed': 'Die automatische Installation der benötigten Systemkomponenten ist '
                                              'fehlgeschlagen.\n'
                                              '{}',
 'escriptorium_error_python_setup_failed': 'Die private Python-Umgebung für eScriptorium konnte nicht erstellt '
                                           'werden.\n'
                                           '{}',
 'escriptorium_error_frontend_build_failed': 'Die eScriptorium-Weboberfläche konnte nicht erstellt werden.\n{}',
 'escriptorium_error_database_setup_failed': 'Die lokale eScriptorium-Datenbank konnte nicht vorbereitet werden.\n{}',
 'escriptorium_error_wsl_missing': 'WSL ist auf diesem Windows-System nicht verfügbar. Bottled Kraken konnte die '
                                   'automatische WSL2-Installation nicht starten.\n'
                                   '{}',
 'escriptorium_error_wsl_install_failed': 'Die automatische Installation von WSL2/Ubuntu ist fehlgeschlagen.\n{}',
 'escriptorium_error_restart_required': 'Windows muss neu gestartet werden, um WSL2 vollständig zu aktivieren. Drücke '
                                        'nach dem Neustart erneut „Server starten“.\n'
                                        '{}',
 'escriptorium_error_folder_open_failed': 'Der Ordner oder die Datei konnte nicht automatisch geöffnet werden:\n{}',
 'escriptorium_error_browser_open_failed': 'Die Webseite konnte nicht automatisch im Browser geöffnet werden:\\n{}',
 'help_escriptorium_docs_button': 'eScriptorium-Dokumentation öffnen',
 'escriptorium_status_working': 'eScriptorium wird im Hintergrund eingerichtet oder gestartet …',
 'escriptorium_status_cancelling': 'Der eScriptorium-Vorgang wird abgebrochen …',
 'escriptorium_error_cancelled': 'Der eScriptorium-Vorgang wurde abgebrochen. Bereits installierte Systempakete '
                                 'bleiben erhalten; eine unvollständige lokale Installation wird beim nächsten '
                                 'Installations- oder Aktualisierungslauf repariert.',
 'escriptorium_error_server_not_running': 'eScriptorium ist noch nicht erreichbar. Warte, bis Installation und '
                                          'Serverstart abgeschlossen sind, und versuche es erneut:\n'
                                          '{}',
 'escriptorium_error_server_start_failed': 'Der eScriptorium-Webserver wurde beendet, bevor er erreichbar war. Die '
                                           'technische Ausgabe lautet:\n'
                                           '{}'}

__all__ = ["ESCRIPTORIUM_TEXTS"]
