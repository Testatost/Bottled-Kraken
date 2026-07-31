# eScriptorium user interface, native installation, and lifecycle texts.
ESCRIPTORIUM_TEXTS = {'menu_escriptorium': 'eScriptorium',
 'dlg_escriptorium_title': 'eScriptorium local',
 'escriptorium_dialog_intro': 'Selecciona tu sistema operativo. Primero instala o actualiza eScriptorium y después '
                              'inicia el servidor. Bottled Kraken descarga, instala, configura y administra '
                              'automáticamente todos los servicios locales en segundo plano. No se necesita Docker.',
 'escriptorium_label_status': 'Estado:',
 'escriptorium_label_install_dir': 'Carpeta local:',
 'escriptorium_label_server_url': 'Dirección del servidor:',
 'escriptorium_label_credentials': 'Credenciales:',
 'escriptorium_status_checking': 'Comprobando el estado…',
 'escriptorium_status_running': 'eScriptorium está en ejecución.',
 'escriptorium_status_stopped': 'Instalado, pero detenido.',
 'escriptorium_status_not_installed': 'Aún no está instalado. Usa primero «Instalar / actualizar eScriptorium».',
 'escriptorium_btn_refresh': 'Actualizar',
 'escriptorium_btn_start': 'Iniciar servidor',
 'escriptorium_btn_stop': 'Detener servidor',
 'escriptorium_btn_open_browser': 'Abrir en el navegador',
 'escriptorium_btn_open_folder': 'Abrir carpeta',
 'escriptorium_btn_open_credentials': 'Abrir credenciales',
 'escriptorium_btn_install_help': 'Instalación / ayuda',
 'escriptorium_credentials_missing': 'El archivo de credenciales se crea durante la primera descarga.',
 'escriptorium_credentials_header': 'Administrador local de eScriptorium',
 'escriptorium_credentials_user': 'Usuario',
 'escriptorium_credentials_password': 'Contraseña',
 'escriptorium_credentials_existing': 'eScriptorium usa las credenciales guardadas en el archivo local runtime.env.',
 'escriptorium_progress_placeholder': 'El progreso y los mensajes técnicos aparecen aquí.',
 'escriptorium_progress_prepare': 'Preparando la carpeta de destino local',
 'escriptorium_progress_download_source': 'Descargando el código oficial de eScriptorium',
 'escriptorium_progress_extract_source': 'Extrayendo de forma segura el archivo fuente',
 'escriptorium_progress_wait_server': 'Esperando al servidor web local',
 'escriptorium_progress_done': 'Operación completada',
 'escriptorium_task_busy': 'Ya hay una operación de eScriptorium en curso.',
 'escriptorium_install_success': 'eScriptorium se preparó en {}.',
 'escriptorium_start_success': 'eScriptorium está funcionando. Se abrirá el navegador.',
 'escriptorium_stop_success': 'eScriptorium se detuvo. Se conservaron todos los proyectos y bases de datos.',
 'escriptorium_error_not_installed': 'eScriptorium aún no está instalado. Abre «Ayuda → eScriptorium» y descarga '
                                     'primero los archivos necesarios.',
 'escriptorium_error_download_failed': 'La descarga falló:\n{}',
 'escriptorium_error_archive_invalid': 'El archivo de eScriptorium descargado no es válido o está incompleto:\n{}',
 'escriptorium_error_command_failed': 'Falló un comando de eScriptorium:\n{}',
 'escriptorium_error_timeout': 'Se agotó el tiempo de la operación siguiente:\n{}',
 'escriptorium_error_server_not_ready': 'Los servicios se iniciaron, pero el servidor web no responde en:\n{}',
 'escriptorium_error_unexpected': 'Error inesperado de eScriptorium:\n{}',
 'help_nav_escriptorium': 'eScriptorium',
 'help_html_escriptorium': '<div class="card"><div class="h1">eScriptorium local sin Docker</div><p>Seleccione Fedora, '
                           'Linux Mint o Windows 10/11 con WSL2. Bottled Kraken automatiza en segundo plano la '
                           'descarga, dependencias, entorno Python privado, construcción web, base de datos y '
                           'servicios.</p></div><div class="card"><div class="h2">Componentes '
                           'instalados</div><p>Fedora y Mint usan PostgreSQL, Redis, Celery, Django, Kraken y un '
                           'entorno Python privado. En Windows, la misma pila Linux se ejecuta en WSL2. No se usan '
                           'Docker ni Docker Compose.</p></div><div class="card"><div class="h2">Datos y '
                           'permisos</div><p>El código, ajustes, credenciales, registros, base de datos, medios y '
                           'archivos de ejecución permanecen dentro de la carpeta de datos de Bottled Kraken. Puede '
                           'solicitarse autorización de administrador para paquetes del sistema o WSL2.</p></div>',
 'help_escriptorium_target': 'Carpeta de destino: {}',
 'help_escriptorium_download_button': 'Instalar / actualizar eScriptorium',
 'escriptorium_label_platform': 'Sistema operativo:',
 'escriptorium_platform_fedora': 'Fedora Linux',
 'escriptorium_platform_mint': 'Linux Mint',
 'escriptorium_platform_windows_wsl': 'Windows 10/11 (WSL2)',
 'escriptorium_platform_unknown': 'Sistema desconocido',
 'escriptorium_platform_help': 'Seleccione el sistema en el que se está ejecutando Bottled Kraken. Puede aparecer una '
                               'solicitud de administrador una vez durante la instalación de componentes del sistema.',
 'escriptorium_status_platform_mismatch': 'El sistema seleccionado no coincide con este equipo.',
 'escriptorium_status_prerequisites_missing': 'Instalado, pero faltan componentes del sistema necesarios.',
 'escriptorium_progress_check_prerequisites': 'Comprobando los componentes necesarios',
 'escriptorium_progress_install_system_packages': 'Instalando los componentes necesarios',
 'escriptorium_progress_create_runtime': 'Creando el entorno privado de eScriptorium',
 'escriptorium_progress_install_python': 'Instalando dependencias de Python',
 'escriptorium_progress_build_frontend': 'Construyendo la interfaz web de eScriptorium',
 'escriptorium_progress_initialize_database': 'Preparando PostgreSQL y Redis locales',
 'escriptorium_progress_migrate_database': 'Actualizando la base de datos de eScriptorium',
 'escriptorium_progress_install_wsl': 'Instalando WSL2 y Ubuntu para eScriptorium',
 'escriptorium_progress_configure_wsl': 'Configurando el entorno privado WSL2',
 'escriptorium_progress_copy_source': 'Copiando eScriptorium al entorno local',
 'escriptorium_progress_start_services': 'Iniciando los servicios locales de eScriptorium',
 'escriptorium_progress_stop_services': 'Deteniendo los servicios locales de eScriptorium',
 'escriptorium_error_platform_mismatch': 'El sistema seleccionado no coincide con este equipo. Elija Fedora, Linux '
                                         'Mint o Windows/WSL2 según corresponda.\n'
                                         '{}',
 'escriptorium_error_privilege_tool_missing': 'La herramienta gráfica de administración no está disponible. Instale '
                                              '«pkexec»/Polkit e inténtelo de nuevo.\n'
                                              '{}',
 'escriptorium_error_prerequisites_missing': 'No se pudieron instalar o encontrar algunos componentes necesarios.\n{}',
 'escriptorium_error_package_install_failed': 'Falló la instalación automática de los componentes necesarios.\n{}',
 'escriptorium_error_python_setup_failed': 'No se pudo crear el entorno privado de Python para eScriptorium.\n{}',
 'escriptorium_error_frontend_build_failed': 'No se pudo construir la interfaz web de eScriptorium.\n{}',
 'escriptorium_error_database_setup_failed': 'No se pudo preparar la base de datos local de eScriptorium.\n{}',
 'escriptorium_error_wsl_missing': 'WSL no está disponible en este sistema Windows. Bottled Kraken no pudo iniciar la '
                                   'instalación automática de WSL2.\n'
                                   '{}',
 'escriptorium_error_wsl_install_failed': 'Falló la instalación automática de WSL2/Ubuntu.\n{}',
 'escriptorium_error_restart_required': 'Windows debe reiniciarse para terminar de habilitar WSL2. Después del '
                                        'reinicio, pulse de nuevo «Iniciar servidor».\n'
                                        '{}',
 'escriptorium_error_folder_open_failed': 'No se pudo abrir automáticamente la carpeta o el archivo:\n{}',
 'escriptorium_error_browser_open_failed': 'No se pudo abrir automáticamente la página web en el navegador:\\n{}',
 'help_escriptorium_docs_button': 'Abrir la documentación de eScriptorium',
 'escriptorium_status_working': 'eScriptorium se está instalando o iniciando en segundo plano…',
 'escriptorium_status_cancelling': 'Se está cancelando la operación de eScriptorium…',
 'escriptorium_error_cancelled': 'La operación de eScriptorium se canceló. Los paquetes del sistema ya instalados se '
                                 'conservan; una instalación local incompleta se reparará en la siguiente instalación '
                                 'o actualización.',
 'escriptorium_error_server_not_running': 'eScriptorium todavía no está disponible. Espera a que terminen la '
                                          'instalación y el inicio del servidor y vuelve a intentarlo:\n'
                                          '{}',
 'escriptorium_error_server_start_failed': 'El servidor web de eScriptorium terminó antes de estar disponible. Salida '
                                           'técnica:\n'
                                           '{}'}

__all__ = ["ESCRIPTORIUM_TEXTS"]
