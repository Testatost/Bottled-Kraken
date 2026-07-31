# eScriptorium user interface, native installation, and lifecycle texts.
ESCRIPTORIUM_TEXTS = {'menu_escriptorium': 'eScriptorium',
 'dlg_escriptorium_title': 'Vietinis eScriptorium',
 'escriptorium_dialog_intro': 'Pasirinkite operacinę sistemą. Pirmiausia įdiekite arba atnaujinkite eScriptorium, tada '
                              'paleiskite serverį. Bottled Kraken automatiškai fone atsisiunčia, įdiegia, '
                              'sukonfigūruoja ir valdo visas vietines paslaugas. Docker nereikalingas.',
 'escriptorium_label_status': 'Būsena:',
 'escriptorium_label_install_dir': 'Vietinis aplankas:',
 'escriptorium_label_server_url': 'Serverio adresas:',
 'escriptorium_label_credentials': 'Prisijungimo duomenys:',
 'escriptorium_status_checking': 'Tikrinama būsena…',
 'escriptorium_status_running': 'eScriptorium veikia.',
 'escriptorium_status_stopped': 'Įdiegta, bet nepaleista.',
 'escriptorium_status_not_installed': 'Dar neįdiegta. Pirmiausia naudokite „Įdiegti / atnaujinti eScriptorium“.',
 'escriptorium_btn_refresh': 'Atnaujinti',
 'escriptorium_btn_start': 'Paleisti serverį',
 'escriptorium_btn_stop': 'Sustabdyti serverį',
 'escriptorium_btn_open_browser': 'Atverti naršyklėje',
 'escriptorium_btn_open_folder': 'Atverti aplanką',
 'escriptorium_btn_open_credentials': 'Atverti prisijungimo duomenis',
 'escriptorium_btn_install_help': 'Diegimas / žinynas',
 'escriptorium_credentials_missing': 'Prisijungimo duomenų failas sukuriamas pirmo atsisiuntimo metu.',
 'escriptorium_credentials_header': 'Vietinis eScriptorium administratorius',
 'escriptorium_credentials_user': 'Naudotojas',
 'escriptorium_credentials_password': 'Slaptažodis',
 'escriptorium_credentials_existing': 'runtime.env',
 'escriptorium_progress_placeholder': 'Čia bus rodoma eiga ir techniniai pranešimai.',
 'escriptorium_progress_prepare': 'Ruošiamas vietinis paskirties aplankas',
 'escriptorium_progress_download_source': 'Atsisiunčiamas oficialus eScriptorium šaltinis',
 'escriptorium_progress_extract_source': 'Saugiai išskleidžiamas šaltinio archyvas',
 'escriptorium_progress_wait_server': 'Laukiama vietinio žiniatinklio serverio',
 'escriptorium_progress_done': 'Operacija baigta',
 'escriptorium_task_busy': 'eScriptorium operacija jau vykdoma.',
 'escriptorium_install_success': 'eScriptorium paruošta aplanke {}.',
 'escriptorium_start_success': 'Vietinių eScriptorium paslaugų paleidimas.',
 'escriptorium_stop_success': 'Vietinių eScriptorium paslaugų stabdymas.',
 'escriptorium_error_not_installed': 'eScriptorium dar neįdiegta. Atverkite „Žinynas → eScriptorium“ ir pirmiausia '
                                     'atsisiųskite reikiamus failus.',
 'escriptorium_error_download_failed': 'Atsisiųsti nepavyko:\n{}',
 'escriptorium_error_archive_invalid': 'Atsisiųstas eScriptorium archyvas netinkamas arba nepilnas:\n{}',
 'escriptorium_error_command_failed': 'Nepavyko įvykdyti eScriptorium komandos:\n{}',
 'escriptorium_error_timeout': 'Baigėsi šios operacijos laikas:\n{}',
 'escriptorium_error_server_not_ready': 'eScriptorium žiniatinklio serveris nepasiekiamas:\n{}',
 'escriptorium_error_unexpected': 'Netikėta eScriptorium klaida:\n{}',
 'help_nav_escriptorium': 'eScriptorium',
 'help_html_escriptorium': '<div class="card"><div class="h1">eScriptorium</div><p>Pasirinkite operacinę sistemą ir '
                           'paleiskite eScriptorium. Bottled Kraken automatiškai fone atsisiunčia, įdiegia, '
                           'sukonfigūruoja, paleidžia ir sustabdo visas reikalingas vietines paslaugas. Docker '
                           'nereikalingas.</p></div><div class="card"><div class="h2">Vietinis diegimas</div><p>Docker '
                           'ir Docker Compose nenaudojami. PostgreSQL, Redis, Celery, Django, Kraken ir Python aplinką '
                           'vietoje valdo Bottled Kraken.</p></div><div class="card"><div '
                           'class="h2">Duomenys</div><p>Pasirinkite sistemą, kurioje šiuo metu veikia Bottled Kraken. '
                           'Vienkartinio sistemos komponentų diegimo metu gali būti prašoma administratoriaus teisių. '
                           'Visi eScriptorium duomenys lieka Bottled Kraken naudotojo aplanke.</p></div>',
 'help_escriptorium_target': 'Paskirties aplankas: {}',
 'help_escriptorium_download_button': 'Įdiegti arba atnaujinti eScriptorium',
 'escriptorium_label_platform': 'Operacinė sistema:',
 'escriptorium_platform_fedora': 'Fedora Linux',
 'escriptorium_platform_mint': 'Linux Mint',
 'escriptorium_platform_windows_wsl': 'Windows 10/11 (WSL2)',
 'escriptorium_platform_unknown': 'Nežinoma sistema',
 'escriptorium_platform_help': 'Pasirinkite sistemą, kurioje šiuo metu veikia Bottled Kraken. Vienkartinio sistemos '
                               'komponentų diegimo metu gali būti paprašyta administratoriaus leidimo.',
 'escriptorium_status_platform_mismatch': 'Pasirinkta sistema neatitinka šio kompiuterio.',
 'escriptorium_status_prerequisites_missing': 'Įdiegta, tačiau nėra būtinų sistemos komponentų.',
 'escriptorium_progress_check_prerequisites': 'Būtinų sistemos komponentų tikrinimas',
 'escriptorium_progress_install_system_packages': 'Būtinų sistemos komponentų diegimas',
 'escriptorium_progress_create_runtime': 'Privačios eScriptorium aplinkos kūrimas',
 'escriptorium_progress_install_python': 'Python priklausomybių diegimas',
 'escriptorium_progress_build_frontend': 'eScriptorium žiniatinklio sąsajos kūrimas',
 'escriptorium_progress_initialize_database': 'Vietinių PostgreSQL ir Redis saugyklų paruošimas',
 'escriptorium_progress_migrate_database': 'eScriptorium duomenų bazės naujinimas',
 'escriptorium_progress_install_wsl': 'WSL2 ir Ubuntu diegimas eScriptorium',
 'escriptorium_progress_configure_wsl': 'Privačios WSL2 aplinkos konfigūravimas',
 'escriptorium_progress_copy_source': 'eScriptorium kopijavimas į vietinę aplinką',
 'escriptorium_progress_start_services': 'Vietinių eScriptorium paslaugų paleidimas',
 'escriptorium_progress_stop_services': 'Vietinių eScriptorium paslaugų stabdymas',
 'escriptorium_error_platform_mismatch': 'Pasirinkta sistema neatitinka šio kompiuterio.\n{}',
 'escriptorium_error_privilege_tool_missing': 'Pasirinkite sistemą, kurioje šiuo metu veikia Bottled Kraken. '
                                              'Vienkartinio sistemos komponentų diegimo metu gali būti paprašyta '
                                              'administratoriaus leidimo.\n'
                                              '{}',
 'escriptorium_error_prerequisites_missing': 'Įdiegta, tačiau nėra būtinų sistemos komponentų.\n{}',
 'escriptorium_error_package_install_failed': 'Nepavyko įdiegti reikalingų sistemos komponentų:\n{}',
 'escriptorium_error_python_setup_failed': 'Nepavyko įdiegti „Python“ priklausomybių:\n{}',
 'escriptorium_error_frontend_build_failed': 'Nepavyko sukurti eScriptorium žiniatinklio sąsajos:\n{}',
 'escriptorium_error_database_setup_failed': 'Nepavyko paruošti vietinių PostgreSQL ir Redis duomenų saugyklų:\n{}',
 'escriptorium_error_wsl_missing': 'WSL2 nepasiekiama arba jos nepavyksta paleisti:\n{}',
 'escriptorium_error_wsl_install_failed': 'Nepavyko įdiegti WSL2 ir Ubuntu:\n{}',
 'escriptorium_error_restart_required': 'Norint užbaigti WSL2 diegimą, reikia paleisti Windows iš naujo. Po to '
                                        'pakartokite veiksmą.\n'
                                        '{}',
 'escriptorium_error_folder_open_failed': 'Nepavyko atverti aplanko:\n{}',
 'escriptorium_error_browser_open_failed': 'Nepavyko automatiškai atverti tinklalapio naršyklėje:\\n{}',
 'help_escriptorium_docs_button': 'eScriptorium dokumentacija',
 'escriptorium_status_working': 'eScriptorium diegiama arba paleidžiama fone…',
 'escriptorium_status_cancelling': 'eScriptorium operacija atšaukiama…',
 'escriptorium_error_cancelled': 'eScriptorium veiksmas buvo atšauktas. Jau įdiegti sistemos paketai paliekami; '
                                 'nebaigtas vietinis diegimas bus pataisytas kito diegimo arba atnaujinimo metu.',
 'escriptorium_error_server_not_running': 'eScriptorium dar nepasiekiama. Palaukite, kol bus baigtas diegimas ir '
                                          'serverio paleidimas, tada bandykite dar kartą:\n'
                                          '{}',
 'escriptorium_error_server_start_failed': 'eScriptorium žiniatinklio serveris baigė darbą dar prieš tapdamas '
                                           'pasiekiamas. Techninė išvestis:\n'
                                           '{}'}

__all__ = ["ESCRIPTORIUM_TEXTS"]
