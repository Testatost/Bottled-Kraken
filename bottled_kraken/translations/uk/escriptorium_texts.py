# eScriptorium user interface, native installation, and lifecycle texts.
ESCRIPTORIUM_TEXTS = {'menu_escriptorium': 'eScriptorium',
 'dlg_escriptorium_title': 'Локальний eScriptorium',
 'escriptorium_dialog_intro': 'Виберіть операційну систему. Спочатку встановіть або оновіть eScriptorium, а потім '
                              'запустіть сервер. Bottled Kraken автоматично у фоновому режимі завантажує, встановлює, '
                              'налаштовує та керує всіма локальними службами. Docker не потрібен.',
 'escriptorium_label_status': 'Стан:',
 'escriptorium_label_install_dir': 'Локальна папка:',
 'escriptorium_label_server_url': 'Адреса сервера:',
 'escriptorium_label_credentials': 'Облікові дані:',
 'escriptorium_status_checking': 'Перевірка стану…',
 'escriptorium_status_running': 'eScriptorium працює.',
 'escriptorium_status_stopped': 'Встановлено, але не запущено.',
 'escriptorium_status_not_installed': 'Ще не встановлено. Спочатку скористайтеся «Встановити / оновити eScriptorium».',
 'escriptorium_btn_refresh': 'Оновити',
 'escriptorium_btn_start': 'Запустити сервер',
 'escriptorium_btn_stop': 'Зупинити сервер',
 'escriptorium_btn_open_browser': 'Відкрити у браузері',
 'escriptorium_btn_open_folder': 'Відкрити папку',
 'escriptorium_btn_open_credentials': 'Відкрити облікові дані',
 'escriptorium_btn_install_help': 'Встановлення / довідка',
 'escriptorium_credentials_missing': 'Файл облікових даних створюється під час першого завантаження.',
 'escriptorium_credentials_header': 'Локальний адміністратор eScriptorium',
 'escriptorium_credentials_user': 'Користувач',
 'escriptorium_credentials_password': 'Пароль',
 'escriptorium_credentials_existing': 'runtime.env',
 'escriptorium_progress_placeholder': 'Тут відображатимуться перебіг і технічні повідомлення.',
 'escriptorium_progress_prepare': 'Підготовка локальної цільової папки',
 'escriptorium_progress_download_source': 'Завантаження офіційного коду eScriptorium',
 'escriptorium_progress_extract_source': 'Безпечне розпакування архіву коду',
 'escriptorium_progress_wait_server': 'Очікування локального вебсервера',
 'escriptorium_progress_done': 'Операцію завершено',
 'escriptorium_task_busy': 'Операція eScriptorium уже виконується.',
 'escriptorium_install_success': 'eScriptorium підготовлено в {}.',
 'escriptorium_start_success': 'Запуск локальних служб eScriptorium.',
 'escriptorium_stop_success': 'Зупинення локальних служб eScriptorium.',
 'escriptorium_error_not_installed': 'eScriptorium ще не встановлено. Відкрийте «Довідка → eScriptorium» і спочатку '
                                     'завантажте потрібні файли.',
 'escriptorium_error_download_failed': 'Не вдалося завантажити:\n{}',
 'escriptorium_error_archive_invalid': 'Завантажений архів eScriptorium пошкоджений або неповний:\n{}',
 'escriptorium_error_command_failed': 'Не вдалося виконати команду eScriptorium:\n{}',
 'escriptorium_error_timeout': 'Перевищено час очікування операції:\n{}',
 'escriptorium_error_server_not_ready': 'Вебсервер eScriptorium недоступний:\n{}',
 'escriptorium_error_unexpected': 'Неочікувана помилка eScriptorium:\n{}',
 'help_nav_escriptorium': 'eScriptorium',
 'help_html_escriptorium': '<div class="card"><div class="h1">eScriptorium</div><p>Виберіть операційну систему, а '
                           'потім запустіть eScriptorium. Bottled Kraken автоматично у фоновому режимі завантажує, '
                           'встановлює, налаштовує, запускає та зупиняє всі потрібні локальні служби. Docker не '
                           'потрібен.</p></div><div class="card"><div class="h2">Локальне встановлення</div><p>Docker '
                           'і Docker Compose не використовуються. PostgreSQL, Redis, Celery, Django, Kraken і '
                           'середовище Python локально керуються Bottled Kraken.</p></div><div class="card"><div '
                           'class="h2">Дані</div><p>Виберіть систему, у якій зараз працює Bottled Kraken. Під час '
                           'одноразового встановлення системних компонентів може з’явитися запит прав адміністратора. '
                           'Усі дані eScriptorium залишаються в папці користувача Bottled Kraken.</p></div>',
 'help_escriptorium_target': 'Цільова папка: {}',
 'help_escriptorium_download_button': 'Встановити або оновити eScriptorium',
 'escriptorium_label_platform': 'Операційна система:',
 'escriptorium_platform_fedora': 'Fedora Linux',
 'escriptorium_platform_mint': 'Linux Mint',
 'escriptorium_platform_windows_wsl': 'Windows 10/11 (WSL2)',
 'escriptorium_platform_unknown': 'Невідома система',
 'escriptorium_platform_help': 'Виберіть систему, у якій зараз працює Bottled Kraken. Під час одноразового '
                               'встановлення системних компонентів може з’явитися запит прав адміністратора.',
 'escriptorium_status_platform_mismatch': 'Вибрана система не відповідає цьому комп’ютеру.',
 'escriptorium_status_prerequisites_missing': 'Встановлено, але потрібні системні компоненти недоступні.',
 'escriptorium_progress_check_prerequisites': 'Перевірка потрібних системних компонентів',
 'escriptorium_progress_install_system_packages': 'Встановлення потрібних системних компонентів',
 'escriptorium_progress_create_runtime': 'Створення приватного середовища eScriptorium',
 'escriptorium_progress_install_python': 'Встановлення залежностей Python',
 'escriptorium_progress_build_frontend': 'Збирання вебінтерфейсу eScriptorium',
 'escriptorium_progress_initialize_database': 'Підготовка локальних сховищ PostgreSQL і Redis',
 'escriptorium_progress_migrate_database': 'Оновлення бази даних eScriptorium',
 'escriptorium_progress_install_wsl': 'Встановлення WSL2 та Ubuntu для eScriptorium',
 'escriptorium_progress_configure_wsl': 'Налаштування приватного середовища WSL2',
 'escriptorium_progress_copy_source': 'Копіювання eScriptorium до локального середовища',
 'escriptorium_progress_start_services': 'Запуск локальних служб eScriptorium',
 'escriptorium_progress_stop_services': 'Зупинення локальних служб eScriptorium',
 'escriptorium_error_platform_mismatch': 'Вибрана система не відповідає цьому комп’ютеру.\n{}',
 'escriptorium_error_privilege_tool_missing': 'Виберіть систему, у якій зараз працює Bottled Kraken. Під час '
                                              'одноразового встановлення системних компонентів може з’явитися запит '
                                              'прав адміністратора.\n'
                                              '{}',
 'escriptorium_error_prerequisites_missing': 'Встановлено, але потрібні системні компоненти недоступні.\n{}',
 'escriptorium_error_package_install_failed': 'Не вдалося встановити потрібні системні компоненти:\n{}',
 'escriptorium_error_python_setup_failed': 'Не вдалося встановити залежності Python:\n{}',
 'escriptorium_error_frontend_build_failed': 'Не вдалося зібрати вебінтерфейс eScriptorium:\n{}',
 'escriptorium_error_database_setup_failed': 'Не вдалося підготувати локальні сховища PostgreSQL і Redis:\n{}',
 'escriptorium_error_wsl_missing': 'WSL2 недоступна або її не вдається запустити:\n{}',
 'escriptorium_error_wsl_install_failed': 'Не вдалося встановити WSL2 та Ubuntu:\n{}',
 'escriptorium_error_restart_required': 'Щоб завершити встановлення WSL2, потрібно перезапустити Windows. Після цього '
                                        'повторіть дію.\n'
                                        '{}',
 'escriptorium_error_folder_open_failed': 'Не вдалося відкрити папку:\n{}',
 'escriptorium_error_browser_open_failed': 'Не вдалося автоматично відкрити вебсторінку у браузері:\\n{}',
 'help_escriptorium_docs_button': 'Документація eScriptorium',
 'escriptorium_status_working': 'eScriptorium встановлюється або запускається у фоновому режимі…',
 'escriptorium_status_cancelling': 'Операцію eScriptorium скасовують…',
 'escriptorium_error_cancelled': 'Операцію eScriptorium скасовано. Уже встановлені системні пакети зберігаються; '
                                 'незавершене локальне встановлення буде виправлено під час наступного встановлення '
                                 'або оновлення.',
 'escriptorium_error_server_not_running': 'eScriptorium ще недоступний. Дочекайтеся завершення встановлення та запуску '
                                          'сервера й повторіть спробу:\n'
                                          '{}',
 'escriptorium_error_server_start_failed': 'Вебсервер eScriptorium завершив роботу до того, як став доступним. '
                                           'Технічний вивід:\n'
                                           '{}'}

__all__ = ["ESCRIPTORIUM_TEXTS"]
