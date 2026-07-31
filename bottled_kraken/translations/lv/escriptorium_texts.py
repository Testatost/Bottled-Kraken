# eScriptorium user interface, native installation, and lifecycle texts.
ESCRIPTORIUM_TEXTS = {'menu_escriptorium': 'eScriptorium',
 'dlg_escriptorium_title': 'Lokāls eScriptorium',
 'escriptorium_dialog_intro': 'Izvēlieties operētājsistēmu. Vispirms instalējiet vai atjauniniet eScriptorium, pēc tam '
                              'palaidiet serveri. Bottled Kraken automātiski fonā lejupielādē, instalē, konfigurē un '
                              'pārvalda visus lokālos pakalpojumus. Docker nav nepieciešams.',
 'escriptorium_label_status': 'Statuss:',
 'escriptorium_label_install_dir': 'Lokālā mape:',
 'escriptorium_label_server_url': 'Servera adrese:',
 'escriptorium_label_credentials': 'Pieteikšanās dati:',
 'escriptorium_status_checking': 'Pārbauda statusu…',
 'escriptorium_status_running': 'eScriptorium darbojas.',
 'escriptorium_status_stopped': 'Instalēts, bet nav palaists.',
 'escriptorium_status_not_installed': 'Vēl nav instalēts. Vispirms izmantojiet “Instalēt / atjaunināt eScriptorium”.',
 'escriptorium_btn_refresh': 'Atjaunināt',
 'escriptorium_btn_start': 'Palaist serveri',
 'escriptorium_btn_stop': 'Apturēt serveri',
 'escriptorium_btn_open_browser': 'Atvērt pārlūkā',
 'escriptorium_btn_open_folder': 'Atvērt mapi',
 'escriptorium_btn_open_credentials': 'Atvērt pieteikšanās datus',
 'escriptorium_btn_install_help': 'Instalēšana / palīdzība',
 'escriptorium_credentials_missing': 'Pieteikšanās datu fails tiek izveidots pirmajā lejupielādē.',
 'escriptorium_credentials_header': 'Lokālais eScriptorium administrators',
 'escriptorium_credentials_user': 'Lietotājs',
 'escriptorium_credentials_password': 'Parole',
 'escriptorium_credentials_existing': 'runtime.env',
 'escriptorium_progress_placeholder': 'Šeit tiks rādīts progress un tehniskie ziņojumi.',
 'escriptorium_progress_prepare': 'Sagatavo lokālo mērķa mapi',
 'escriptorium_progress_download_source': 'Lejupielādē oficiālo eScriptorium pirmkodu',
 'escriptorium_progress_extract_source': 'Droši izpako pirmkoda arhīvu',
 'escriptorium_progress_wait_server': 'Gaida lokālo tīmekļa serveri',
 'escriptorium_progress_done': 'Darbība pabeigta',
 'escriptorium_task_busy': 'eScriptorium darbība jau notiek.',
 'escriptorium_install_success': 'eScriptorium sagatavots mapē {}.',
 'escriptorium_start_success': 'Vietējo eScriptorium pakalpojumu palaišana.',
 'escriptorium_stop_success': 'Vietējo eScriptorium pakalpojumu apturēšana.',
 'escriptorium_error_not_installed': 'eScriptorium vēl nav instalēts. Atveriet “Palīdzība → eScriptorium” un vispirms '
                                     'lejupielādējiet vajadzīgos failus.',
 'escriptorium_error_download_failed': 'Lejupielāde neizdevās:\n{}',
 'escriptorium_error_archive_invalid': 'Lejupielādētais eScriptorium arhīvs ir nederīgs vai nepilnīgs:\n{}',
 'escriptorium_error_command_failed': 'eScriptorium komanda neizdevās:\n{}',
 'escriptorium_error_timeout': 'Beidzās šīs darbības laiks:\n{}',
 'escriptorium_error_server_not_ready': 'eScriptorium tīmekļa serveris nav pieejams:\n{}',
 'escriptorium_error_unexpected': 'Negaidīta eScriptorium kļūda:\n{}',
 'help_nav_escriptorium': 'eScriptorium',
 'help_html_escriptorium': '<div class="card"><div class="h1">eScriptorium</div><p>Izvēlieties operētājsistēmu un pēc '
                           'tam palaidiet eScriptorium. Bottled Kraken fonā automātiski lejupielādē, instalē, '
                           'konfigurē, palaiž un aptur visus nepieciešamos lokālos pakalpojumus. Docker nav '
                           'vajadzīgs.</p></div><div class="card"><div class="h2">Lokāla instalācija</div><p>Docker un '
                           'Docker Compose netiek izmantoti. PostgreSQL, Redis, Celery, Django, Kraken un Python vidi '
                           'lokāli pārvalda Bottled Kraken.</p></div><div class="card"><div '
                           'class="h2">Dati</div><p>Izvēlieties sistēmu, kurā pašlaik darbojas Bottled Kraken. '
                           'Vienreizējās sistēmas komponentu instalēšanas laikā var tikt pieprasītas administratora '
                           'tiesības. Visi eScriptorium dati paliek Bottled Kraken lietotāja mapē.</p></div>',
 'help_escriptorium_target': 'Mērķa mape: {}',
 'help_escriptorium_download_button': 'Instalēt vai atjaunināt eScriptorium',
 'escriptorium_label_platform': 'Operētājsistēma:',
 'escriptorium_platform_fedora': 'Fedora Linux',
 'escriptorium_platform_mint': 'Linux Mint',
 'escriptorium_platform_windows_wsl': 'Windows 10/11 (WSL2)',
 'escriptorium_platform_unknown': 'Nezināma sistēma',
 'escriptorium_platform_help': 'Izvēlieties sistēmu, kurā pašlaik darbojas Bottled Kraken. Vienreizējās sistēmas '
                               'komponentu instalēšanas laikā var tikt pieprasīta administratora atļauja.',
 'escriptorium_status_platform_mismatch': 'Izvēlētā sistēma neatbilst šim datoram.',
 'escriptorium_status_prerequisites_missing': 'Instalēts, bet nepieciešamie sistēmas komponenti nav pieejami.',
 'escriptorium_progress_check_prerequisites': 'Nepieciešamo sistēmas komponentu pārbaude',
 'escriptorium_progress_install_system_packages': 'Nepieciešamo sistēmas komponentu instalēšana',
 'escriptorium_progress_create_runtime': 'Privātas eScriptorium vides izveide',
 'escriptorium_progress_install_python': 'Python atkarību instalēšana',
 'escriptorium_progress_build_frontend': 'eScriptorium tīmekļa saskarnes veidošana',
 'escriptorium_progress_initialize_database': 'Vietējo PostgreSQL un Redis krātuvju sagatavošana',
 'escriptorium_progress_migrate_database': 'eScriptorium datubāzes atjaunināšana',
 'escriptorium_progress_install_wsl': 'WSL2 un Ubuntu instalēšana eScriptorium',
 'escriptorium_progress_configure_wsl': 'Privātās WSL2 vides konfigurēšana',
 'escriptorium_progress_copy_source': 'eScriptorium kopēšana vietējā vidē',
 'escriptorium_progress_start_services': 'Vietējo eScriptorium pakalpojumu palaišana',
 'escriptorium_progress_stop_services': 'Vietējo eScriptorium pakalpojumu apturēšana',
 'escriptorium_error_platform_mismatch': 'Izvēlētā sistēma neatbilst šim datoram.\n{}',
 'escriptorium_error_privilege_tool_missing': 'Izvēlieties sistēmu, kurā pašlaik darbojas Bottled Kraken. Vienreizējās '
                                              'sistēmas komponentu instalēšanas laikā var tikt pieprasīta '
                                              'administratora atļauja.\n'
                                              '{}',
 'escriptorium_error_prerequisites_missing': 'Instalēts, bet nepieciešamie sistēmas komponenti nav pieejami.\n{}',
 'escriptorium_error_package_install_failed': 'Neizdevās instalēt nepieciešamos sistēmas komponentus:\n{}',
 'escriptorium_error_python_setup_failed': 'Neizdevās instalēt Python atkarības:\n{}',
 'escriptorium_error_frontend_build_failed': 'Neizdevās izveidot eScriptorium tīmekļa saskarni:\n{}',
 'escriptorium_error_database_setup_failed': 'Neizdevās sagatavot lokālās PostgreSQL un Redis datu krātuves:\n{}',
 'escriptorium_error_wsl_missing': 'WSL2 nav pieejama vai to nevar palaist:\n{}',
 'escriptorium_error_wsl_install_failed': 'Neizdevās instalēt WSL2 un Ubuntu:\n{}',
 'escriptorium_error_restart_required': 'Lai pabeigtu WSL2 instalēšanu, jārestartē Windows. Pēc tam atkārtojiet '
                                        'darbību.\n'
                                        '{}',
 'escriptorium_error_folder_open_failed': 'Neizdevās atvērt mapi:\n{}',
 'escriptorium_error_browser_open_failed': 'Tīmekļa lapu neizdevās automātiski atvērt pārlūkā:\\n{}',
 'help_escriptorium_docs_button': 'eScriptorium dokumentācija',
 'escriptorium_status_working': 'eScriptorium tiek instalēts vai palaists fonā…',
 'escriptorium_status_cancelling': 'eScriptorium darbība tiek atcelta…',
 'escriptorium_error_cancelled': 'eScriptorium darbība tika atcelta. Jau instalētās sistēmas pakotnes tiek saglabātas; '
                                 'nepabeigta lokālā instalācija tiks salabota nākamās instalēšanas vai atjaunināšanas '
                                 'laikā.',
 'escriptorium_error_server_not_running': 'eScriptorium vēl nav sasniedzams. Uzgaidiet, līdz instalēšana un servera '
                                          'palaišana ir pabeigta, un mēģiniet vēlreiz:\n'
                                          '{}',
 'escriptorium_error_server_start_failed': 'eScriptorium tīmekļa serveris beidza darbu, pirms kļuva sasniedzams. '
                                           'Tehniskā izvade:\n'
                                           '{}'}

__all__ = ["ESCRIPTORIUM_TEXTS"]
