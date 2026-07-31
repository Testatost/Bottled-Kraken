# eScriptorium user interface, native installation, and lifecycle texts.
ESCRIPTORIUM_TEXTS = {'menu_escriptorium': 'eScriptorium',
 'dlg_escriptorium_title': 'Local eScriptorium',
 'escriptorium_dialog_intro': 'Choose your operating system. Install or update eScriptorium first, then start the '
                              'server. Bottled Kraken automatically downloads, installs, configures, and manages all '
                              'local services in the background. Docker is not required.',
 'escriptorium_label_status': 'Status:',
 'escriptorium_label_install_dir': 'Local folder:',
 'escriptorium_label_server_url': 'Server address:',
 'escriptorium_label_credentials': 'Credentials:',
 'escriptorium_status_checking': 'Checking status…',
 'escriptorium_status_running': 'eScriptorium is running.',
 'escriptorium_status_stopped': 'Installed, but not running.',
 'escriptorium_status_not_installed': 'Not installed yet. Use “Install / update eScriptorium” first.',
 'escriptorium_btn_refresh': 'Refresh',
 'escriptorium_btn_start': 'Start server',
 'escriptorium_btn_stop': 'Stop server',
 'escriptorium_btn_open_browser': 'Open in browser',
 'escriptorium_btn_open_folder': 'Open folder',
 'escriptorium_btn_open_credentials': 'Open credentials',
 'escriptorium_btn_install_help': 'Installation / help',
 'escriptorium_credentials_missing': 'The credentials file is created during the first download.',
 'escriptorium_credentials_header': 'Local eScriptorium administrator',
 'escriptorium_credentials_user': 'User',
 'escriptorium_credentials_password': 'Password',
 'escriptorium_credentials_existing': 'eScriptorium uses the credentials stored in the local runtime.env file.',
 'escriptorium_progress_placeholder': 'Progress and technical messages appear here.',
 'escriptorium_progress_prepare': 'Preparing the local destination',
 'escriptorium_progress_download_source': 'Downloading the official eScriptorium source',
 'escriptorium_progress_extract_source': 'Safely extracting the source archive',
 'escriptorium_progress_wait_server': 'Waiting for the local web server',
 'escriptorium_progress_done': 'Operation completed',
 'escriptorium_task_busy': 'An eScriptorium operation is already running.',
 'escriptorium_install_success': 'eScriptorium was prepared in {}.',
 'escriptorium_start_success': 'eScriptorium is running. The browser will open.',
 'escriptorium_stop_success': 'eScriptorium was stopped. All projects and databases were preserved.',
 'escriptorium_error_not_installed': 'eScriptorium is not installed yet. Open “Help → eScriptorium” and download the '
                                     'required files first.',
 'escriptorium_error_download_failed': 'The download failed:\n{}',
 'escriptorium_error_archive_invalid': 'The downloaded eScriptorium archive is invalid or incomplete:\n{}',
 'escriptorium_error_command_failed': 'An eScriptorium command failed:\n{}',
 'escriptorium_error_timeout': 'The following operation timed out:\n{}',
 'escriptorium_error_server_not_ready': 'The services started, but the web server is not responding at:\n{}',
 'escriptorium_error_unexpected': 'Unexpected eScriptorium error:\n{}',
 'help_nav_escriptorium': 'eScriptorium',
 'help_html_escriptorium': '<div class="card"><div class="h1">Local eScriptorium without Docker</div><p>Select Fedora, '
                           'Linux Mint, or Windows 10/11 with WSL2. Bottled Kraken performs the download, dependency '
                           'installation, private Python setup, frontend build, database preparation, and service '
                           'control automatically in the background.</p></div><div class="card"><div class="h2">What '
                           'is installed</div><p>Fedora and Mint use local PostgreSQL, Redis, Celery, Django, Kraken, '
                           'and a private Python environment. On Windows, the same Linux stack runs inside WSL2. '
                           'Docker and Docker Compose are not used.</p></div><div class="card"><div class="h2">Data '
                           'and permissions</div><p>eScriptorium source, settings, credentials, logs, database data, '
                           'media, and runtime files are kept below the Bottled Kraken user-data folder. A system '
                           'administrator prompt may appear while operating-system packages or WSL2 are '
                           'installed.</p></div>',
 'help_escriptorium_target': 'Destination folder: {}',
 'help_escriptorium_download_button': 'Install / update eScriptorium',
 'escriptorium_label_platform': 'Operating system:',
 'escriptorium_platform_fedora': 'Fedora Linux',
 'escriptorium_platform_mint': 'Linux Mint',
 'escriptorium_platform_windows_wsl': 'Windows 10/11 (WSL2)',
 'escriptorium_platform_unknown': 'Unknown system',
 'escriptorium_platform_help': 'Select the operating system on which Bottled Kraken is currently running. '
                               'Administrator authentication may be requested once while system components are '
                               'installed.',
 'escriptorium_status_platform_mismatch': 'The selected operating system does not match this computer.',
 'escriptorium_status_prerequisites_missing': 'Installed, but required system components are unavailable.',
 'escriptorium_progress_check_prerequisites': 'Checking required system components',
 'escriptorium_progress_install_system_packages': 'Installing required system components',
 'escriptorium_progress_create_runtime': 'Creating the private eScriptorium runtime',
 'escriptorium_progress_install_python': 'Installing Python dependencies',
 'escriptorium_progress_build_frontend': 'Building the eScriptorium web interface',
 'escriptorium_progress_initialize_database': 'Preparing the local PostgreSQL and Redis data stores',
 'escriptorium_progress_migrate_database': 'Updating the eScriptorium database',
 'escriptorium_progress_install_wsl': 'Installing WSL2 and Ubuntu for eScriptorium',
 'escriptorium_progress_configure_wsl': 'Configuring the private WSL2 environment',
 'escriptorium_progress_copy_source': 'Copying eScriptorium into the local runtime',
 'escriptorium_progress_start_services': 'Starting local eScriptorium services',
 'escriptorium_progress_stop_services': 'Stopping local eScriptorium services',
 'escriptorium_error_platform_mismatch': 'The selected operating system does not match this computer. Select Fedora, '
                                         'Linux Mint, or Windows/WSL2 as appropriate.\n'
                                         '{}',
 'escriptorium_error_privilege_tool_missing': 'The graphical administrator tool is unavailable. Install '
                                              '“pkexec”/Polkit and try again.\n'
                                              '{}',
 'escriptorium_error_prerequisites_missing': 'Some required system components could not be installed or found.\n{}',
 'escriptorium_error_package_install_failed': 'Automatic installation of required system components failed.\n{}',
 'escriptorium_error_python_setup_failed': 'The private Python environment for eScriptorium could not be created.\n{}',
 'escriptorium_error_frontend_build_failed': 'The eScriptorium web interface could not be built.\n{}',
 'escriptorium_error_database_setup_failed': 'The local eScriptorium database could not be prepared.\n{}',
 'escriptorium_error_wsl_missing': 'WSL is unavailable on this Windows system. Bottled Kraken could not start the '
                                   'automatic WSL2 installation.\n'
                                   '{}',
 'escriptorium_error_wsl_install_failed': 'The automatic WSL2/Ubuntu installation failed.\n{}',
 'escriptorium_error_restart_required': 'Windows must be restarted to finish enabling WSL2. After the restart, press '
                                        '“Start server” again.\n'
                                        '{}',
 'escriptorium_error_folder_open_failed': 'The folder or file could not be opened automatically:\n{}',
 'escriptorium_error_browser_open_failed': 'The web page could not be opened automatically in a browser:\\n{}',
 'help_escriptorium_docs_button': 'Open eScriptorium documentation',
 'escriptorium_status_working': 'eScriptorium is being installed or started in the background…',
 'escriptorium_status_cancelling': 'Cancelling the eScriptorium operation…',
 'escriptorium_error_cancelled': 'The eScriptorium operation was cancelled. System packages already installed are '
                                 'kept; an incomplete local installation is repaired during the next install or update '
                                 'run.',
 'escriptorium_error_server_not_running': 'eScriptorium is not reachable yet. Wait until installation and server '
                                          'startup have finished, then try again:\n'
                                          '{}',
 'escriptorium_error_server_start_failed': 'The eScriptorium web server exited before it became reachable. Technical '
                                           'output:\n'
                                           '{}'}

__all__ = ["ESCRIPTORIUM_TEXTS"]
