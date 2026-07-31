# eScriptorium user interface, native installation, and lifecycle texts.
ESCRIPTORIUM_TEXTS = {'menu_escriptorium': 'eScriptorium',
 'dlg_escriptorium_title': 'Lokalne eScriptorium',
 'escriptorium_dialog_intro': 'Wybierz system operacyjny. Najpierw zainstaluj lub zaktualizuj eScriptorium, a '
                              'następnie uruchom serwer. Bottled Kraken automatycznie pobiera, instaluje, konfiguruje '
                              'i zarządza wszystkimi usługami lokalnymi w tle. Docker nie jest wymagany.',
 'escriptorium_label_status': 'Stan:',
 'escriptorium_label_install_dir': 'Folder lokalny:',
 'escriptorium_label_server_url': 'Adres serwera:',
 'escriptorium_label_credentials': 'Dane logowania:',
 'escriptorium_status_checking': 'Sprawdzanie stanu…',
 'escriptorium_status_running': 'eScriptorium działa.',
 'escriptorium_status_stopped': 'Zainstalowane, ale nieuruchomione.',
 'escriptorium_status_not_installed': 'Jeszcze nie zainstalowano. Najpierw użyj „Zainstaluj / zaktualizuj '
                                      'eScriptorium”.',
 'escriptorium_btn_refresh': 'Odśwież',
 'escriptorium_btn_start': 'Uruchom serwer',
 'escriptorium_btn_stop': 'Zatrzymaj serwer',
 'escriptorium_btn_open_browser': 'Otwórz w przeglądarce',
 'escriptorium_btn_open_folder': 'Otwórz folder',
 'escriptorium_btn_open_credentials': 'Otwórz dane logowania',
 'escriptorium_btn_install_help': 'Instalacja / pomoc',
 'escriptorium_credentials_missing': 'Plik z danymi logowania jest tworzony podczas pierwszego pobierania.',
 'escriptorium_credentials_header': 'Lokalny administrator eScriptorium',
 'escriptorium_credentials_user': 'Użytkownik',
 'escriptorium_credentials_password': 'Hasło',
 'escriptorium_credentials_existing': 'runtime.env',
 'escriptorium_progress_placeholder': 'Tutaj pojawi się postęp i komunikaty techniczne.',
 'escriptorium_progress_prepare': 'Przygotowywanie lokalnego folderu docelowego',
 'escriptorium_progress_download_source': 'Pobieranie oficjalnego kodu źródłowego eScriptorium',
 'escriptorium_progress_extract_source': 'Bezpieczne rozpakowywanie archiwum źródłowego',
 'escriptorium_progress_wait_server': 'Oczekiwanie na lokalny serwer WWW',
 'escriptorium_progress_done': 'Operacja zakończona',
 'escriptorium_task_busy': 'Operacja eScriptorium jest już wykonywana.',
 'escriptorium_install_success': 'eScriptorium przygotowano w {}.',
 'escriptorium_start_success': 'Uruchamianie lokalnych usług eScriptorium.',
 'escriptorium_stop_success': 'Zatrzymywanie lokalnych usług eScriptorium.',
 'escriptorium_error_not_installed': 'eScriptorium nie jest jeszcze zainstalowane. Otwórz „Pomoc → eScriptorium” i '
                                     'najpierw pobierz wymagane pliki.',
 'escriptorium_error_download_failed': 'Pobieranie nie powiodło się:\n{}',
 'escriptorium_error_archive_invalid': 'Pobrane archiwum eScriptorium jest nieprawidłowe lub niekompletne:\n{}',
 'escriptorium_error_command_failed': 'Polecenie eScriptorium zakończyło się niepowodzeniem:\n{}',
 'escriptorium_error_timeout': 'Przekroczono limit czasu operacji:\n{}',
 'escriptorium_error_server_not_ready': 'Serwer internetowy eScriptorium jest niedostępny:\n{}',
 'escriptorium_error_unexpected': 'Nieoczekiwany błąd eScriptorium:\n{}',
 'help_nav_escriptorium': 'eScriptorium',
 'help_html_escriptorium': '<div class="card"><div class="h1">eScriptorium</div><p>Wybierz system operacyjny, a '
                           'następnie uruchom eScriptorium. Bottled Kraken automatycznie w tle pobiera, instaluje, '
                           'konfiguruje, uruchamia i zatrzymuje wszystkie wymagane usługi lokalne. Docker nie jest '
                           'potrzebny.</p></div><div class="card"><div class="h2">Instalacja lokalna</div><p>Docker '
                           'ani Docker Compose nie są używane. PostgreSQL, Redis, Celery, Django, Kraken i środowisko '
                           'Pythona są lokalnie zarządzane przez Bottled Kraken.</p></div><div class="card"><div '
                           'class="h2">Dane</div><p>Wybierz system, na którym działa Bottled Kraken. Podczas '
                           'jednorazowej instalacji składników systemowych może pojawić się prośba o uprawnienia '
                           'administratora. Wszystkie dane eScriptorium pozostają w folderze użytkownika Bottled '
                           'Kraken.</p></div>',
 'help_escriptorium_target': 'Folder docelowy: {}',
 'help_escriptorium_download_button': 'Zainstaluj lub zaktualizuj eScriptorium',
 'escriptorium_label_platform': 'System operacyjny:',
 'escriptorium_platform_fedora': 'Fedora Linux',
 'escriptorium_platform_mint': 'Linux Mint',
 'escriptorium_platform_windows_wsl': 'Windows 10/11 (WSL2)',
 'escriptorium_platform_unknown': 'Nieznany system',
 'escriptorium_platform_help': 'Wybierz system, na którym działa Bottled Kraken. Podczas jednorazowej instalacji '
                               'składników systemowych może pojawić się prośba o uprawnienia administratora.',
 'escriptorium_status_platform_mismatch': 'Wybrany system nie odpowiada temu komputerowi.',
 'escriptorium_status_prerequisites_missing': 'Zainstalowano, ale wymagane składniki systemowe są niedostępne.',
 'escriptorium_progress_check_prerequisites': 'Sprawdzanie wymaganych składników systemowych',
 'escriptorium_progress_install_system_packages': 'Instalowanie wymaganych składników systemowych',
 'escriptorium_progress_create_runtime': 'Tworzenie prywatnego środowiska eScriptorium',
 'escriptorium_progress_install_python': 'Instalowanie zależności Pythona',
 'escriptorium_progress_build_frontend': 'Budowanie interfejsu internetowego eScriptorium',
 'escriptorium_progress_initialize_database': 'Przygotowywanie lokalnych magazynów PostgreSQL i Redis',
 'escriptorium_progress_migrate_database': 'Aktualizowanie bazy eScriptorium',
 'escriptorium_progress_install_wsl': 'Instalowanie WSL2 i Ubuntu dla eScriptorium',
 'escriptorium_progress_configure_wsl': 'Konfigurowanie prywatnego środowiska WSL2',
 'escriptorium_progress_copy_source': 'Kopiowanie eScriptorium do lokalnego środowiska',
 'escriptorium_progress_start_services': 'Uruchamianie lokalnych usług eScriptorium',
 'escriptorium_progress_stop_services': 'Zatrzymywanie lokalnych usług eScriptorium',
 'escriptorium_error_platform_mismatch': 'Wybrany system nie odpowiada temu komputerowi.\n{}',
 'escriptorium_error_privilege_tool_missing': 'Wybierz system, na którym działa Bottled Kraken. Podczas jednorazowej '
                                              'instalacji składników systemowych może pojawić się prośba o uprawnienia '
                                              'administratora.\n'
                                              '{}',
 'escriptorium_error_prerequisites_missing': 'Zainstalowano, ale wymagane składniki systemowe są niedostępne.\n{}',
 'escriptorium_error_package_install_failed': 'Nie udało się zainstalować wymaganych składników systemowych:\n{}',
 'escriptorium_error_python_setup_failed': 'Nie udało się zainstalować zależności Pythona:\n{}',
 'escriptorium_error_frontend_build_failed': 'Nie udało się zbudować interfejsu internetowego eScriptorium:\n{}',
 'escriptorium_error_database_setup_failed': 'Nie udało się przygotować lokalnych magazynów danych PostgreSQL i '
                                             'Redis:\n'
                                             '{}',
 'escriptorium_error_wsl_missing': 'WSL2 jest niedostępne albo nie można go uruchomić:\n{}',
 'escriptorium_error_wsl_install_failed': 'Nie udało się zainstalować WSL2 i Ubuntu:\n{}',
 'escriptorium_error_restart_required': 'Aby dokończyć instalację WSL2, należy ponownie uruchomić Windows. Następnie '
                                        'wykonaj tę operację ponownie.\n'
                                        '{}',
 'escriptorium_error_folder_open_failed': 'Nie udało się otworzyć folderu:\n{}',
 'escriptorium_error_browser_open_failed': 'Nie udało się automatycznie otworzyć strony w przeglądarce:\\n{}',
 'help_escriptorium_docs_button': 'Dokumentacja eScriptorium',
 'escriptorium_status_working': 'eScriptorium jest instalowane lub uruchamiane w tle…',
 'escriptorium_status_cancelling': 'Anulowanie operacji eScriptorium…',
 'escriptorium_error_cancelled': 'Operacja eScriptorium została anulowana. Już zainstalowane pakiety systemowe '
                                 'pozostają; niepełna instalacja lokalna zostanie naprawiona podczas następnej '
                                 'instalacji lub aktualizacji.',
 'escriptorium_error_server_not_running': 'eScriptorium nie jest jeszcze dostępne. Poczekaj na zakończenie instalacji '
                                          'i uruchamiania serwera, a następnie spróbuj ponownie:\n'
                                          '{}',
 'escriptorium_error_server_start_failed': 'Serwer WWW eScriptorium zakończył działanie, zanim stał się dostępny. Dane '
                                           'techniczne:\n'
                                           '{}'}

__all__ = ["ESCRIPTORIUM_TEXTS"]
