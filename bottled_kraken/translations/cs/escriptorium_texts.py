# eScriptorium user interface, native installation, and lifecycle texts.
ESCRIPTORIUM_TEXTS = {'menu_escriptorium': 'eScriptorium',
 'dlg_escriptorium_title': 'Místní eScriptorium',
 'escriptorium_dialog_intro': 'Vyberte svůj operační systém. Nejprve eScriptorium nainstalujte nebo aktualizujte a '
                              'potom spusťte server. Bottled Kraken provede stahování, instalaci, konfiguraci a správu '
                              'všech místních služeb automaticky na pozadí. Docker není potřeba.',
 'escriptorium_label_status': 'Stav:',
 'escriptorium_label_install_dir': 'Místní složka:',
 'escriptorium_label_server_url': 'Adresa serveru:',
 'escriptorium_label_credentials': 'Přihlašovací údaje:',
 'escriptorium_status_checking': 'Kontrola stavu…',
 'escriptorium_status_running': 'eScriptorium je spuštěno.',
 'escriptorium_status_stopped': 'Nainstalováno, ale neběží.',
 'escriptorium_status_not_installed': 'Dosud není nainstalováno. Nejprve použijte „Nainstalovat / aktualizovat '
                                      'eScriptorium“.',
 'escriptorium_btn_refresh': 'Aktualizovat',
 'escriptorium_btn_start': 'Spustit server',
 'escriptorium_btn_stop': 'Zastavit server',
 'escriptorium_btn_open_browser': 'Otevřít v prohlížeči',
 'escriptorium_btn_open_folder': 'Otevřít složku',
 'escriptorium_btn_open_credentials': 'Otevřít přihlašovací údaje',
 'escriptorium_btn_install_help': 'Instalace / nápověda',
 'escriptorium_credentials_missing': 'Soubor s přihlašovacími údaji se vytvoří při prvním stažení.',
 'escriptorium_credentials_header': 'Místní správce eScriptorium',
 'escriptorium_credentials_user': 'Uživatel',
 'escriptorium_credentials_password': 'Heslo',
 'escriptorium_credentials_existing': 'runtime.env',
 'escriptorium_progress_placeholder': 'Zde se zobrazí průběh a technické zprávy.',
 'escriptorium_progress_prepare': 'Příprava místní cílové složky',
 'escriptorium_progress_download_source': 'Stahování oficiálního zdrojového kódu eScriptorium',
 'escriptorium_progress_extract_source': 'Bezpečné rozbalení zdrojového archivu',
 'escriptorium_progress_wait_server': 'Čekání na místní webový server',
 'escriptorium_progress_done': 'Operace dokončena',
 'escriptorium_task_busy': 'Již probíhá operace eScriptorium.',
 'escriptorium_install_success': 'eScriptorium bylo připraveno v {}.',
 'escriptorium_start_success': 'Spouštění místních služeb eScriptorium.',
 'escriptorium_stop_success': 'Zastavování místních služeb eScriptorium.',
 'escriptorium_error_not_installed': 'eScriptorium ještě není nainstalováno. Otevřete „Nápověda → eScriptorium“ a '
                                     'nejprve stáhněte potřebné soubory.',
 'escriptorium_error_download_failed': 'Stažení se nezdařilo:\n{}',
 'escriptorium_error_archive_invalid': 'Stažený archiv eScriptorium je neplatný nebo neúplný:\n{}',
 'escriptorium_error_command_failed': 'Příkaz eScriptorium se nezdařil:\n{}',
 'escriptorium_error_timeout': 'Vypršel časový limit operace:\n{}',
 'escriptorium_error_server_not_ready': 'Webový server eScriptorium není dostupný:\n{}',
 'escriptorium_error_unexpected': 'Neočekávaná chyba eScriptorium:\n{}',
 'help_nav_escriptorium': 'eScriptorium',
 'help_html_escriptorium': '<div class="card"><div class="h1">eScriptorium</div><p>Vyberte operační systém a poté '
                           'spusťte eScriptorium. Bottled Kraken automaticky na pozadí stáhne, nainstaluje, nastaví, '
                           'spustí a zastaví všechny potřebné místní služby. Docker není potřeba.</p></div><div '
                           'class="card"><div class="h2">Místní instalace</div><p>Docker ani Docker Compose se '
                           'nepoužívají. PostgreSQL, Redis, Celery, Django, Kraken a prostředí Pythonu spravuje '
                           'Bottled Kraken místně.</p></div><div class="card"><div class="h2">Data</div><p>Vyberte '
                           'systém, na kterém právě běží Bottled Kraken. Při jednorázové instalaci systémových '
                           'součástí může být vyžadováno oprávnění správce. Všechna data eScriptorium zůstávají v '
                           'uživatelském adresáři Bottled Kraken.</p></div>',
 'help_escriptorium_target': 'Cílová složka: {}',
 'help_escriptorium_download_button': 'Nainstalovat nebo aktualizovat eScriptorium',
 'escriptorium_label_platform': 'Operační systém:',
 'escriptorium_platform_fedora': 'Fedora Linux',
 'escriptorium_platform_mint': 'Linux Mint',
 'escriptorium_platform_windows_wsl': 'Windows 10/11 (WSL2)',
 'escriptorium_platform_unknown': 'Neznámý systém',
 'escriptorium_platform_help': 'Vyberte systém, na kterém právě běží Bottled Kraken. Při jednorázové instalaci '
                               'systémových součástí může být vyžadováno oprávnění správce.',
 'escriptorium_status_platform_mismatch': 'Vybraný systém neodpovídá tomuto počítači.',
 'escriptorium_status_prerequisites_missing': 'Nainstalováno, ale požadované systémové součásti nejsou dostupné.',
 'escriptorium_progress_check_prerequisites': 'Kontrola požadovaných systémových součástí',
 'escriptorium_progress_install_system_packages': 'Instalace požadovaných systémových součástí',
 'escriptorium_progress_create_runtime': 'Vytváření soukromého prostředí eScriptorium',
 'escriptorium_progress_install_python': 'Instalace závislostí Pythonu',
 'escriptorium_progress_build_frontend': 'Sestavování webového rozhraní eScriptorium',
 'escriptorium_progress_initialize_database': 'Příprava místních úložišť PostgreSQL a Redis',
 'escriptorium_progress_migrate_database': 'Aktualizace databáze eScriptorium',
 'escriptorium_progress_install_wsl': 'Instalace WSL2 a Ubuntu pro eScriptorium',
 'escriptorium_progress_configure_wsl': 'Konfigurace soukromého prostředí WSL2',
 'escriptorium_progress_copy_source': 'Kopírování eScriptoria do místního prostředí',
 'escriptorium_progress_start_services': 'Spouštění místních služeb eScriptorium',
 'escriptorium_progress_stop_services': 'Zastavování místních služeb eScriptorium',
 'escriptorium_error_platform_mismatch': 'Vybraný systém neodpovídá tomuto počítači.\n{}',
 'escriptorium_error_privilege_tool_missing': 'Vyberte systém, na kterém právě běží Bottled Kraken. Při jednorázové '
                                              'instalaci systémových součástí může být vyžadováno oprávnění správce.\n'
                                              '{}',
 'escriptorium_error_prerequisites_missing': 'Nainstalováno, ale požadované systémové součásti nejsou dostupné.\n{}',
 'escriptorium_error_package_install_failed': 'Instalace požadovaných systémových součástí se nezdařila:\n{}',
 'escriptorium_error_python_setup_failed': 'Instalace závislostí Pythonu se nezdařila:\n{}',
 'escriptorium_error_frontend_build_failed': 'Sestavení webového rozhraní eScriptorium se nezdařilo:\n{}',
 'escriptorium_error_database_setup_failed': 'Příprava místních úložišť PostgreSQL a Redis se nezdařila:\n{}',
 'escriptorium_error_wsl_missing': 'WSL2 není k dispozici nebo jej nelze spustit:\n{}',
 'escriptorium_error_wsl_install_failed': 'Instalace WSL2 a Ubuntu se nezdařila:\n{}',
 'escriptorium_error_restart_required': 'Pro dokončení instalace WSL2 je nutné restartovat Windows. Poté spusťte akci '
                                        'znovu.\n'
                                        '{}',
 'escriptorium_error_folder_open_failed': 'Složku nelze otevřít:\n{}',
 'escriptorium_error_browser_open_failed': 'Webovou stránku nelze automaticky otevřít:\\n{}',
 'help_escriptorium_docs_button': 'Dokumentace eScriptorium',
 'escriptorium_status_working': 'eScriptorium se instaluje nebo spouští na pozadí…',
 'escriptorium_status_cancelling': 'Operace eScriptorium se ruší…',
 'escriptorium_error_cancelled': 'Operace eScriptorium byla zrušena. Již nainstalované systémové balíčky zůstanou '
                                 'zachovány; neúplná místní instalace bude opravena při příštím spuštění instalace '
                                 'nebo aktualizace.',
 'escriptorium_error_server_not_running': 'eScriptorium zatím není dostupné. Počkejte na dokončení instalace a '
                                          'spuštění serveru a zkuste to znovu:\n'
                                          '{}',
 'escriptorium_error_server_start_failed': 'Webový server eScriptorium skončil dříve, než byl dostupný. Technický '
                                           'výstup:\n'
                                           '{}'}

__all__ = ["ESCRIPTORIUM_TEXTS"]
