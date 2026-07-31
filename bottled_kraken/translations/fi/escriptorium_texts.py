# eScriptorium user interface, native installation, and lifecycle texts.
ESCRIPTORIUM_TEXTS = {'menu_escriptorium': 'eScriptorium',
 'dlg_escriptorium_title': 'Paikallinen eScriptorium',
 'escriptorium_dialog_intro': 'Valitse käyttöjärjestelmä. Asenna tai päivitä eScriptorium ensin ja käynnistä palvelin '
                              'sen jälkeen. Bottled Kraken lataa, asentaa, määrittää ja hallitsee kaikki paikalliset '
                              'palvelut automaattisesti taustalla. Dockeria ei tarvita.',
 'escriptorium_label_status': 'Tila:',
 'escriptorium_label_install_dir': 'Paikallinen kansio:',
 'escriptorium_label_server_url': 'Palvelimen osoite:',
 'escriptorium_label_credentials': 'Kirjautumistiedot:',
 'escriptorium_status_checking': 'Tarkistetaan tilaa…',
 'escriptorium_status_running': 'eScriptorium on käynnissä.',
 'escriptorium_status_stopped': 'Asennettu, mutta ei käynnissä.',
 'escriptorium_status_not_installed': 'Ei ole vielä asennettu. Käytä ensin toimintoa ”Asenna / päivitä eScriptorium”.',
 'escriptorium_btn_refresh': 'Päivitä',
 'escriptorium_btn_start': 'Käynnistä palvelin',
 'escriptorium_btn_stop': 'Pysäytä palvelin',
 'escriptorium_btn_open_browser': 'Avaa selaimessa',
 'escriptorium_btn_open_folder': 'Avaa kansio',
 'escriptorium_btn_open_credentials': 'Avaa kirjautumistiedot',
 'escriptorium_btn_install_help': 'Asennus / ohje',
 'escriptorium_credentials_missing': 'Kirjautumistiedosto luodaan ensimmäisen latauksen yhteydessä.',
 'escriptorium_credentials_header': 'Paikallinen eScriptorium-järjestelmänvalvoja',
 'escriptorium_credentials_user': 'Käyttäjä',
 'escriptorium_credentials_password': 'Salasana',
 'escriptorium_credentials_existing': 'runtime.env',
 'escriptorium_progress_placeholder': 'Edistyminen ja tekniset viestit näkyvät tässä.',
 'escriptorium_progress_prepare': 'Valmistellaan paikallista kohdekansiota',
 'escriptorium_progress_download_source': 'Ladataan virallista eScriptorium-lähdekoodia',
 'escriptorium_progress_extract_source': 'Puretaan lähdearkisto turvallisesti',
 'escriptorium_progress_wait_server': 'Odotetaan paikallista verkkopalvelinta',
 'escriptorium_progress_done': 'Toiminto valmis',
 'escriptorium_task_busy': 'eScriptorium-toiminto on jo käynnissä.',
 'escriptorium_install_success': 'eScriptorium valmisteltiin kansioon {}.',
 'escriptorium_start_success': 'Paikallisten eScriptorium-palvelujen käynnistys.',
 'escriptorium_stop_success': 'Paikallisten eScriptorium-palvelujen pysäytys.',
 'escriptorium_error_not_installed': 'eScriptoriumia ei ole vielä asennettu. Avaa “Ohje → eScriptorium” ja lataa ensin '
                                     'tarvittavat tiedostot.',
 'escriptorium_error_download_failed': 'Lataus epäonnistui:\n{}',
 'escriptorium_error_archive_invalid': 'Ladattu eScriptorium-arkisto on virheellinen tai puutteellinen:\n{}',
 'escriptorium_error_command_failed': 'eScriptorium-komento epäonnistui:\n{}',
 'escriptorium_error_timeout': 'Seuraava toiminto aikakatkaistiin:\n{}',
 'escriptorium_error_server_not_ready': 'eScriptoriumin verkkopalvelin ei ole käytettävissä:\n{}',
 'escriptorium_error_unexpected': 'Odottamaton eScriptorium-virhe:\n{}',
 'help_nav_escriptorium': 'eScriptorium',
 'help_html_escriptorium': '<div class="card"><div class="h1">eScriptorium</div><p>Valitse käyttöjärjestelmä ja '
                           'käynnistä sitten eScriptorium. Bottled Kraken lataa, asentaa, määrittää, käynnistää ja '
                           'pysäyttää automaattisesti kaikki tarvittavat paikalliset palvelut taustalla. Dockeria ei '
                           'tarvita.</p></div><div class="card"><div class="h2">Paikallinen asennus</div><p>Dockeria '
                           'tai Docker Composea ei käytetä. Bottled Kraken hallitsee PostgreSQL-, Redis-, Celery-, '
                           'Django-, Kraken- ja Python-ympäristöä paikallisesti.</p></div><div class="card"><div '
                           'class="h2">Tiedot</div><p>Valitse järjestelmä, jossa Bottled Kraken on käynnissä. '
                           'Järjestelmäosien kertaluonteinen asennus voi pyytää järjestelmänvalvojan oikeuksia. Kaikki '
                           'eScriptorium-tiedot säilyvät Bottled Krakenin käyttäjäkansiossa.</p></div>',
 'help_escriptorium_target': 'Kohdekansio: {}',
 'help_escriptorium_download_button': 'Asenna tai päivitä eScriptorium',
 'escriptorium_label_platform': 'Käyttöjärjestelmä:',
 'escriptorium_platform_fedora': 'Fedora Linux',
 'escriptorium_platform_mint': 'Linux Mint',
 'escriptorium_platform_windows_wsl': 'Windows 10/11 (WSL2)',
 'escriptorium_platform_unknown': 'Tuntematon järjestelmä',
 'escriptorium_platform_help': 'Valitse järjestelmä, jossa Bottled Kraken on käynnissä. Järjestelmäosien '
                               'kertaluonteisen asennuksen aikana voidaan pyytää järjestelmänvalvojan oikeuksia.',
 'escriptorium_status_platform_mismatch': 'Valittu järjestelmä ei vastaa tätä tietokonetta.',
 'escriptorium_status_prerequisites_missing': 'Asennettu, mutta vaadittuja järjestelmäosia ei ole saatavilla.',
 'escriptorium_progress_check_prerequisites': 'Vaadittujen järjestelmäosien tarkistus',
 'escriptorium_progress_install_system_packages': 'Vaadittujen järjestelmäosien asennus',
 'escriptorium_progress_create_runtime': 'Yksityisen eScriptorium-ympäristön luonti',
 'escriptorium_progress_install_python': 'Python-riippuvuuksien asennus',
 'escriptorium_progress_build_frontend': 'eScriptorium-verkkokäyttöliittymän rakentaminen',
 'escriptorium_progress_initialize_database': 'Paikallisten PostgreSQL- ja Redis-tietovarastojen valmistelu',
 'escriptorium_progress_migrate_database': 'eScriptorium-tietokannan päivitys',
 'escriptorium_progress_install_wsl': 'WSL2:n ja Ubuntun asennus eScriptoriumille',
 'escriptorium_progress_configure_wsl': 'Yksityisen WSL2-ympäristön määritys',
 'escriptorium_progress_copy_source': 'eScriptoriumin kopiointi paikalliseen ympäristöön',
 'escriptorium_progress_start_services': 'Paikallisten eScriptorium-palvelujen käynnistys',
 'escriptorium_progress_stop_services': 'Paikallisten eScriptorium-palvelujen pysäytys',
 'escriptorium_error_platform_mismatch': 'Valittu järjestelmä ei vastaa tätä tietokonetta.\n{}',
 'escriptorium_error_privilege_tool_missing': 'Valitse järjestelmä, jossa Bottled Kraken on käynnissä. '
                                              'Järjestelmäosien kertaluonteisen asennuksen aikana voidaan pyytää '
                                              'järjestelmänvalvojan oikeuksia.\n'
                                              '{}',
 'escriptorium_error_prerequisites_missing': 'Asennettu, mutta vaadittuja järjestelmäosia ei ole saatavilla.\n{}',
 'escriptorium_error_package_install_failed': 'Tarvittavien järjestelmäosien asennus epäonnistui:\n{}',
 'escriptorium_error_python_setup_failed': 'Python-riippuvuuksien asennus epäonnistui:\n{}',
 'escriptorium_error_frontend_build_failed': 'eScriptoriumin verkkokäyttöliittymän koostaminen epäonnistui:\n{}',
 'escriptorium_error_database_setup_failed': 'Paikallisten PostgreSQL- ja Redis-tietovarastojen valmistelu '
                                             'epäonnistui:\n'
                                             '{}',
 'escriptorium_error_wsl_missing': 'WSL2 ei ole käytettävissä tai sitä ei voida käynnistää:\n{}',
 'escriptorium_error_wsl_install_failed': 'WSL2:n ja Ubuntun asennus epäonnistui:\n{}',
 'escriptorium_error_restart_required': 'Windows on käynnistettävä uudelleen WSL2-asennuksen viimeistelemiseksi. '
                                        'Suorita toiminto sen jälkeen uudelleen.\n'
                                        '{}',
 'escriptorium_error_folder_open_failed': 'Kansiota ei voitu avata:\n{}',
 'escriptorium_error_browser_open_failed': 'Verkkosivua ei voitu avata selaimessa automaattisesti:\\n{}',
 'help_escriptorium_docs_button': 'eScriptoriumin dokumentaatio',
 'escriptorium_status_working': 'eScriptoriumia asennetaan tai käynnistetään taustalla…',
 'escriptorium_status_cancelling': 'eScriptorium-toimintoa peruutetaan…',
 'escriptorium_error_cancelled': 'eScriptorium-toiminto peruutettiin. Jo asennetut järjestelmäpaketit säilytetään; '
                                 'keskeneräinen paikallinen asennus korjataan seuraavan asennuksen tai päivityksen '
                                 'yhteydessä.',
 'escriptorium_error_server_not_running': 'eScriptorium ei ole vielä tavoitettavissa. Odota asennuksen ja palvelimen '
                                          'käynnistyksen valmistumista ja yritä uudelleen:\n'
                                          '{}',
 'escriptorium_error_server_start_failed': 'eScriptorium-verkkopalvelin päättyi ennen kuin se tuli tavoitettavaksi. '
                                           'Tekninen tuloste:\n'
                                           '{}'}

__all__ = ["ESCRIPTORIUM_TEXTS"]
