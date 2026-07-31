# eScriptorium user interface, native installation, and lifecycle texts.
ESCRIPTORIUM_TEXTS = {'menu_escriptorium': 'eScriptorium',
 'dlg_escriptorium_title': 'Kohalik eScriptorium',
 'escriptorium_dialog_intro': 'Vali oma operatsioonisüsteem. Esmalt installi või uuenda eScriptorium ja seejärel '
                              'käivita server. Bottled Kraken laadib alla, installib, seadistab ja haldab kõiki '
                              'kohalikke teenuseid automaatselt taustal. Dockerit ei ole vaja.',
 'escriptorium_label_status': 'Olek:',
 'escriptorium_label_install_dir': 'Kohalik kaust:',
 'escriptorium_label_server_url': 'Serveri aadress:',
 'escriptorium_label_credentials': 'Sisselogimisandmed:',
 'escriptorium_status_checking': 'Oleku kontrollimine…',
 'escriptorium_status_running': 'eScriptorium töötab.',
 'escriptorium_status_stopped': 'Paigaldatud, kuid ei tööta.',
 'escriptorium_status_not_installed': 'Pole veel installitud. Kasuta esmalt nuppu „Installi / uuenda eScriptorium“.',
 'escriptorium_btn_refresh': 'Värskenda',
 'escriptorium_btn_start': 'Käivita server',
 'escriptorium_btn_stop': 'Peata server',
 'escriptorium_btn_open_browser': 'Ava brauseris',
 'escriptorium_btn_open_folder': 'Ava kaust',
 'escriptorium_btn_open_credentials': 'Ava sisselogimisandmed',
 'escriptorium_btn_install_help': 'Installimine / abi',
 'escriptorium_credentials_missing': 'Sisselogimisandmete fail luuakse esimesel allalaadimisel.',
 'escriptorium_credentials_header': 'Kohalik eScriptoriumi administraator',
 'escriptorium_credentials_user': 'Kasutaja',
 'escriptorium_credentials_password': 'Parool',
 'escriptorium_credentials_existing': 'runtime.env',
 'escriptorium_progress_placeholder': 'Edenemine ja tehnilised teated kuvatakse siin.',
 'escriptorium_progress_prepare': 'Kohaliku sihtkausta ettevalmistamine',
 'escriptorium_progress_download_source': 'Ametliku eScriptoriumi lähtekoodi allalaadimine',
 'escriptorium_progress_extract_source': 'Lähtearhiivi turvaline lahtipakkimine',
 'escriptorium_progress_wait_server': 'Kohaliku veebiserveri ootamine',
 'escriptorium_progress_done': 'Toiming lõpetatud',
 'escriptorium_task_busy': 'eScriptoriumi toiming juba töötab.',
 'escriptorium_install_success': 'eScriptorium valmistati ette kaustas {}.',
 'escriptorium_start_success': 'Kohalike eScriptoriumi teenuste käivitamine.',
 'escriptorium_stop_success': 'Kohalike eScriptoriumi teenuste peatamine.',
 'escriptorium_error_not_installed': 'eScriptorium pole veel paigaldatud. Ava “Abi → eScriptorium” ja laadi esmalt '
                                     'vajalikud failid alla.',
 'escriptorium_error_download_failed': 'Allalaadimine nurjus:\n{}',
 'escriptorium_error_archive_invalid': 'Allalaaditud eScriptoriumi arhiiv on vigane või puudulik:\n{}',
 'escriptorium_error_command_failed': 'eScriptoriumi käsk nurjus:\n{}',
 'escriptorium_error_timeout': 'Järgmine toiming aegus:\n{}',
 'escriptorium_error_server_not_ready': 'eScriptoriumi veebiserver pole saadaval:\n{}',
 'escriptorium_error_unexpected': 'Ootamatu eScriptoriumi viga:\n{}',
 'help_nav_escriptorium': 'eScriptorium',
 'help_html_escriptorium': '<div class="card"><div class="h1">eScriptorium</div><p>Valige operatsioonisüsteem ja '
                           'käivitage seejärel eScriptorium. Bottled Kraken laadib kõik vajalikud kohalikud teenused '
                           'taustal automaatselt alla, installib, seadistab, käivitab ja peatab. Dockerit pole '
                           'vaja.</p></div><div class="card"><div class="h2">Kohalik install</div><p>Dockerit ega '
                           'Docker Compose’i ei kasutata. PostgreSQL-i, Redist, Celeryt, Djangot, Krakenit ja Pythoni '
                           'keskkonda haldab Bottled Kraken kohapeal.</p></div><div class="card"><div '
                           'class="h2">Andmed</div><p>Valige süsteem, kus Bottled Kraken praegu töötab. '
                           'Süsteemikomponentide ühekordsel installimisel võidakse küsida administraatori luba. Kõik '
                           'eScriptoriumi andmed jäävad Bottled Krakeni kasutajakausta.</p></div>',
 'help_escriptorium_target': 'Sihtkaust: {}',
 'help_escriptorium_download_button': 'Installi või uuenda eScriptorium',
 'escriptorium_label_platform': 'Operatsioonisüsteem:',
 'escriptorium_platform_fedora': 'Fedora Linux',
 'escriptorium_platform_mint': 'Linux Mint',
 'escriptorium_platform_windows_wsl': 'Windows 10/11 (WSL2)',
 'escriptorium_platform_unknown': 'Tundmatu süsteem',
 'escriptorium_platform_help': 'Valige süsteem, kus Bottled Kraken praegu töötab. Süsteemikomponentide ühekordsel '
                               'installimisel võidakse küsida administraatori luba.',
 'escriptorium_status_platform_mismatch': 'Valitud süsteem ei vasta sellele arvutile.',
 'escriptorium_status_prerequisites_missing': 'Installitud, kuid vajalikud süsteemikomponendid pole saadaval.',
 'escriptorium_progress_check_prerequisites': 'Vajalike süsteemikomponentide kontrollimine',
 'escriptorium_progress_install_system_packages': 'Vajalike süsteemikomponentide installimine',
 'escriptorium_progress_create_runtime': 'Privaatse eScriptoriumi keskkonna loomine',
 'escriptorium_progress_install_python': 'Pythoni sõltuvuste installimine',
 'escriptorium_progress_build_frontend': 'eScriptoriumi veebiliidese koostamine',
 'escriptorium_progress_initialize_database': 'Kohalike PostgreSQL-i ja Redise andmehoidlate ettevalmistamine',
 'escriptorium_progress_migrate_database': 'eScriptoriumi andmebaasi uuendamine',
 'escriptorium_progress_install_wsl': 'WSL2 ja Ubuntu installimine eScriptoriumi jaoks',
 'escriptorium_progress_configure_wsl': 'Privaatse WSL2 keskkonna seadistamine',
 'escriptorium_progress_copy_source': 'eScriptoriumi kopeerimine kohalikku keskkonda',
 'escriptorium_progress_start_services': 'Kohalike eScriptoriumi teenuste käivitamine',
 'escriptorium_progress_stop_services': 'Kohalike eScriptoriumi teenuste peatamine',
 'escriptorium_error_platform_mismatch': 'Valitud süsteem ei vasta sellele arvutile.\n{}',
 'escriptorium_error_privilege_tool_missing': 'Valige süsteem, kus Bottled Kraken praegu töötab. Süsteemikomponentide '
                                              'ühekordsel installimisel võidakse küsida administraatori luba.\n'
                                              '{}',
 'escriptorium_error_prerequisites_missing': 'Installitud, kuid vajalikud süsteemikomponendid pole saadaval.\n{}',
 'escriptorium_error_package_install_failed': 'Nõutavate süsteemikomponentide installimine nurjus:\n{}',
 'escriptorium_error_python_setup_failed': 'Pythoni sõltuvuste installimine nurjus:\n{}',
 'escriptorium_error_frontend_build_failed': 'eScriptoriumi veebiliidese koostamine nurjus:\n{}',
 'escriptorium_error_database_setup_failed': 'Kohalike PostgreSQL-i ja Redise andmehoidlate ettevalmistamine nurjus:\n'
                                             '{}',
 'escriptorium_error_wsl_missing': 'WSL2 pole saadaval või seda ei saa käivitada:\n{}',
 'escriptorium_error_wsl_install_failed': 'WSL2 ja Ubuntu installimine nurjus:\n{}',
 'escriptorium_error_restart_required': 'WSL2 installimise lõpetamiseks tuleb Windows taaskäivitada. Seejärel '
                                        'käivitage toiming uuesti.\n'
                                        '{}',
 'escriptorium_error_folder_open_failed': 'Kausta ei saanud avada:\n{}',
 'escriptorium_error_browser_open_failed': 'Veebilehte ei saanud brauseris automaatselt avada:\\n{}',
 'help_escriptorium_docs_button': 'eScriptoriumi dokumentatsioon',
 'escriptorium_status_working': 'eScriptoriumit installitakse või käivitatakse taustal…',
 'escriptorium_status_cancelling': 'eScriptoriumi toimingut katkestatakse…',
 'escriptorium_error_cancelled': 'eScriptoriumi toiming katkestati. Juba installitud süsteemipaketid säilivad; pooleli '
                                 'jäänud kohalik install parandatakse järgmisel installimisel või uuendamisel.',
 'escriptorium_error_server_not_running': 'eScriptorium pole veel kättesaadav. Oota paigalduse ja serveri käivitamise '
                                          'lõppu ning proovi uuesti:\n'
                                          '{}',
 'escriptorium_error_server_start_failed': 'eScriptoriumi veebiserver lõpetas töö enne kättesaadavaks muutumist. '
                                           'Tehniline väljund:\n'
                                           '{}'}

__all__ = ["ESCRIPTORIUM_TEXTS"]
