"""Mixin für MainWindow: whisper download help and image edit queue."""
from ..shared import *
from ..ui_components import *
from ..workers import *
from ..dialogs import *
from ..image_edit import *

class MainWindowWhisperDownloadHelpAndImageEditQueueMixin:
    def _whisper_system_hint(self, platform_name: str) -> str:
        name = (platform_name or "").strip().lower()
        if name in ("debian", "ubuntu", "linux mint", "mint"):
            return self._tr("whisper_hint_debian")
        if name == "fedora":
            return self._tr("whisper_hint_fedora")
        if name == "arch":
            return self._tr("whisper_hint_arch")
        if name in ("mac", "macos", "darwin"):
            return self._tr("whisper_hint_macos")
        if name == "windows":
            return self._tr("whisper_hint_windows")
        return self._tr("whisper_hint_generic")

    def download_whisper_model_from_help_dialog(self, platform_name: str, dialog_parent=None):
        # 1) zuerst prüfen, ob large-v3 schon vorhanden ist
        existing_model_dir = self._find_existing_whisper_large_v3_model()
        if existing_model_dir:
            base_dir = os.path.dirname(existing_model_dir)
            self.whisper_models_base_dir = self._normalize_whisper_base_dir(base_dir)
            self.settings.setValue("paths/whisper_models_base_dir", self.whisper_models_base_dir)
            self._scan_whisper_models()
            self._set_whisper_model(existing_model_dir)
            self._update_whisper_menu_status()
            QMessageBox.information(
                dialog_parent or self,
                self._tr("info_title"),
                "Das Faster-Whisper large-v3 Modell ist bereits vorhanden.\n\n"
                f"Pfad:\n{existing_model_dir}\n\n"
                "Ein erneuter Download ist nicht nötig."
            )
            self.status_bar.showMessage(self._tr("msg_whisper_model_already_present", existing_model_dir))
            return
        platform_hint = self._whisper_system_hint(platform_name)
        QMessageBox.information(
            dialog_parent or self,
            self._tr("info_title"),
            "Optionaler Systemhinweis:\n\n"
            f"{platform_hint}\n\n"
            "Der eigentliche Download läuft trotzdem nur über eine eigene "
            "Python-Umgebung (.venv) und die Python-API von huggingface_hub."
        )
        # Prüfen, ob bereits ein Download läuft
        if self.hf_download_worker and self.hf_download_worker.isRunning():
            if self.hf_download_dialog is not None:
                self.hf_download_dialog.show()
                self.hf_download_dialog.raise_()
                self.hf_download_dialog.activateWindow()
            QMessageBox.information(
                dialog_parent or self,
                self._tr("info_title"),
                self._tr("warn_whisper_download_running")
            )
            return
        target_base = self._default_whisper_base_dir()
        target_model_dir = self._default_whisper_model_dir()
        try:
            os.makedirs(target_base, exist_ok=True)
            self.status_bar.showMessage(
                self._tr("msg_whisper_download_prepare_target", target_model_dir)
            )
            self.hf_download_dialog = ProgressStatusDialog(
                self._tr("dlg_whisper_download_title"),
                self._tr,
                dialog_parent or self
            )
            self.hf_download_dialog.set_status(self._tr("dlg_whisper_download_prepare"))
            self.hf_download_dialog.set_progress(0)
            self.hf_download_dialog.show()
            self.hf_download_dialog.raise_()
            self.hf_download_dialog.activateWindow()
            platform_key = (
                "windows" if sys.platform.startswith("win")
                else "mac" if sys.platform == "darwin"
                else "linux"
            )
            venv_dir = self._whisper_venv_dir()
            venv_python = self._whisper_venv_python_path(platform_key)
            prepare_cmds = [
                self._system_python_for_venv_cmd() + ["-m", "venv", venv_dir],
            ]

            install_cmd = [
                venv_python,
                "-m",
                "pip",
                "install",
                "-U",
                "pip",
                "setuptools",
                "wheel",
                "huggingface_hub",
                "faster-whisper",
                "sounddevice",
            ]

            hf_exe = self._hf_cli_executable(platform_key)
            download_cmd = [
                hf_exe,
                "download",
                "Systran/faster-whisper-large-v3",
                "--local-dir",
                target_model_dir,
            ]
            self.hf_download_worker = HFDownloadWorker(
                repo_id="Systran/faster-whisper-large-v3",
                local_dir=target_model_dir,
                prepare_cmds=prepare_cmds,
                install_cmd=install_cmd,
                download_cmd=download_cmd,
                tr_func=self._tr,
                parent=self
            )
            self.hf_download_worker.progress_changed.connect(self.hf_download_dialog.set_progress)
            self.hf_download_worker.status_changed.connect(self.hf_download_dialog.set_status)
            self.hf_download_worker.finished_download.connect(self.on_hf_download_finished)
            self.hf_download_worker.failed_download.connect(self.on_hf_download_failed)
            self.hf_download_dialog.cancel_requested.connect(self.hf_download_worker.cancel)
            self.hf_download_worker.start()
        except Exception as e:
            QMessageBox.warning(
                self,
                self._tr("warn_title"),
                f"Download des Whisper-Modells konnte nicht gestartet werden:\n{e}"
            )
            self.status_bar.showMessage(self._tr("msg_whisper_download_start_failed"))

    def on_hf_download_finished(self, local_dir: str):
        self.status_bar.showMessage(self._tr("msg_whisper_model_loaded", local_dir))
        self.whisper_models_base_dir = self._normalize_whisper_base_dir(os.path.dirname(local_dir))
        self._scan_whisper_models()
        if os.path.isfile(os.path.join(local_dir, "model.bin")):
            self._set_whisper_model(local_dir)
        self._update_whisper_menu_status()
        self.settings.setValue("paths/whisper_models_base_dir", self.whisper_models_base_dir)
        if hasattr(self, "hf_download_dialog") and self.hf_download_dialog:
            self.hf_download_dialog.set_progress(100)
            self.hf_download_dialog.hide()
            self.hf_download_dialog.close()
            self.hf_download_dialog = None
        self.hf_download_worker = None
        QMessageBox.information(
            self,
            self._tr("info_title"),
            "Das Faster-Whisper-Modell wurde erfolgreich heruntergeladen.\n\n"
            f"Zielordner:\n{local_dir}"
        )

    def on_hf_download_failed(self, msg: str):
        self.status_bar.showMessage(self._tr("msg_whisper_download_failed"))
        if hasattr(self, "hf_download_dialog") and self.hf_download_dialog:
            self.hf_download_dialog.hide()
            self.hf_download_dialog.close()
            self.hf_download_dialog = None
        self.hf_download_worker = None
        QMessageBox.warning(
            self,
            self._tr("warn_title"),
            f"Download des Whisper-Modells fehlgeschlagen:\n{msg}"
        )

    def _build_uninstall_delete_help_html(self) -> str:
        return (
            '            <div class="card warn">\n'
            f'                <div class="h1">{self._tr("uninstall_delete_title")}</div>\n'
            f'                <p>{self._tr("uninstall_delete_intro")}</p>\n'
            f'                <p><b>{self._tr("uninstall_delete_scope_title")}</b></p>\n'
            '                <ul>\n'
            f'                    <li>{self._tr("uninstall_delete_scope_backends")}</li>\n'
            f'                    <li>{self._tr("uninstall_delete_scope_whisper")}</li>\n'
            f'                    <li>{self._tr("uninstall_delete_scope_settings")}</li>\n'
            f'                    <li>{self._tr("uninstall_delete_scope_cache")}</li>\n'
            '                </ul>\n'
            f'                <p><b>{self._tr("uninstall_delete_warning_title")}</b></p>\n'
            '                <ul>\n'
            f'                    <li>{self._tr("uninstall_delete_warning_irreversible")}</li>\n'
            f'                    <li>{self._tr("uninstall_delete_warning_user_files")}</li>\n'
            f'                    <li>{self._tr("uninstall_delete_warning_running_app")}</li>\n'
            '                </ul>\n'
            f'                <p>{self._tr("uninstall_delete_click_hint")}</p>\n'
            '            </div>\n'
        )

    def _make_uninstall_delete_page(self, parent_dialog: QDialog) -> QWidget:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(10)

        browser = QTextBrowser()
        browser.setReadOnly(True)
        browser.setOpenExternalLinks(True)
        browser.setFrameShape(QTextBrowser.NoFrame)
        browser.setOpenLinks(False)
        browser.anchorClicked.connect(QDesktopServices.openUrl)
        browser.setHtml(_help_html(self.current_theme, self._build_uninstall_delete_help_html()))
        browser.setMinimumWidth(760)
        browser.document().setDocumentMargin(8)
        page_layout.addWidget(browser, 1)

        row = QHBoxLayout()
        row.addStretch(1)
        btn = QPushButton(self._tr("btn_uninstall_delete"))
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumHeight(38)
        btn.setMinimumWidth(230)
        btn.setStyleSheet(
            "QPushButton {"
            "background:#b91c1c; color:white; border:1px solid #7f1d1d;"
            "border-radius:8px; padding:8px 14px; font-weight:700;"
            "}"
            "QPushButton:hover { background:#dc2626; }"
            "QPushButton:pressed { background:#7f1d1d; }"
            "QPushButton:disabled { background:#7f7f7f; color:#dddddd; }"
        )
        btn.clicked.connect(lambda: self._run_uninstall_delete_from_help(parent_dialog))
        row.addWidget(btn, 0)
        page_layout.addLayout(row, 0)
        return page

    def _release_bottled_kraken_runtime_files(self):
        """Gibt offene Log-/Crashdateien frei, damit der Datenordner gelöscht werden kann."""
        try:
            import faulthandler
            if faulthandler.is_enabled():
                faulthandler.disable()
        except Exception:
            pass
        try:
            import bottled_kraken.app as _bk_app
            log_file = getattr(_bk_app, "_CRASH_LOG_FILE", None)
            if log_file:
                try:
                    log_file.flush()
                except Exception:
                    pass
                try:
                    log_file.close()
                except Exception:
                    pass
                try:
                    _bk_app._CRASH_LOG_FILE = None
                except Exception:
                    pass
        except Exception:
            pass


    def _candidate_bottled_kraken_delete_paths(self) -> List[str]:
        paths: List[str] = []
        home = os.path.expanduser("~")

        def add(path: str):
            if not path:
                return
            try:
                norm = os.path.abspath(os.path.expanduser(path))
            except Exception:
                return
            if norm and norm not in paths:
                paths.append(norm)

        # Historische und aktuelle Bottled-Kraken-Pfade im Benutzerprofil.
        # .bottled_kraken enthält u. a. Crash-/Fehlerlogs aus älteren und aktuellen Builds.
        add(os.path.join(home, ".bottled_kraken"))
        add(os.path.join(home, ".bottled_kraken.env"))
        add(os.path.join(home, ".kraken_ocr_tool_settings"))

        if sys.platform.startswith("win"):
            add(os.path.join(os.environ.get("LOCALAPPDATA", ""), "BottledKraken"))
            add(os.path.join(os.environ.get("APPDATA", ""), "BottledKraken"))
            add(os.path.join(home, "BottledKraken"))
        elif sys.platform == "darwin":
            add(os.path.join(home, "Library", "Application Support", "BottledKraken"))
            add(os.path.join(home, "Library", "Caches", "BottledKraken"))
            add(os.path.join(home, "Library", "Preferences", "BottledKraken"))
            add(os.path.join(home, "Library", "Preferences", "com.BottledKraken.BottledKrakenApp.plist"))
        else:
            xdg_data = os.environ.get("XDG_DATA_HOME") or os.path.join(home, ".local", "share")
            xdg_cache = os.environ.get("XDG_CACHE_HOME") or os.path.join(home, ".cache")
            xdg_config = os.environ.get("XDG_CONFIG_HOME") or os.path.join(home, ".config")
            add(os.path.join(xdg_data, "BottledKraken"))
            add(os.path.join(xdg_cache, "BottledKraken"))
            add(os.path.join(xdg_config, "BottledKraken"))

        # Falls der Whisper-Basisordner durch den Nutzer umgestellt wurde, nur dann löschen,
        # wenn der Pfad eindeutig zu BottledKraken gehört. So werden fremde Modellordner nicht versehentlich entfernt.
        try:
            whisper_base = self._normalize_whisper_base_dir(getattr(self, "whisper_models_base_dir", ""))
            if whisper_base and "BottledKraken" in os.path.abspath(whisper_base).split(os.sep):
                add(whisper_base)
        except Exception:
            pass

        # Optional konfigurierter externer Backend-Ordner.
        custom_backend_root = os.environ.get("BOTTLED_KRAKEN_BACKENDS_DIR", "").strip()
        if custom_backend_root and "BottledKraken" in os.path.abspath(os.path.expanduser(custom_backend_root)).split(os.sep):
            add(custom_backend_root)

        return self._dedupe_parent_delete_paths(paths)

    def _dedupe_parent_delete_paths(self, paths: List[str]) -> List[str]:
        existing = []
        for path in paths:
            try:
                norm = os.path.abspath(path)
            except Exception:
                continue
            if os.path.exists(norm) or os.path.islink(norm):
                existing.append(norm)

        existing = sorted(set(existing), key=len)
        result: List[str] = []
        for path in existing:
            try:
                if any(os.path.commonpath([path, parent]) == parent for parent in result):
                    continue
            except Exception:
                pass
            result.append(path)
        return result

    def _is_safe_bottled_kraken_delete_path(self, path: str) -> bool:
        try:
            norm = os.path.abspath(path)
            home = os.path.abspath(os.path.expanduser("~"))
            app_dir = os.path.abspath(self._app_base_dir()) if hasattr(self, "_app_base_dir") else ""
        except Exception:
            return False

        if not norm or norm in (os.path.abspath(os.sep), home):
            return False

        # Nie den Ordner löschen, aus dem das laufende Programm gerade gestartet wurde.
        if app_dir:
            try:
                if norm == app_dir or os.path.commonpath([app_dir, norm]) == norm:
                    return False
            except Exception:
                pass

        parts = [part.lower() for part in norm.split(os.sep) if part]
        filename = os.path.basename(norm).lower()

        if filename in {".bottled_kraken", ".bottled_kraken.env", ".kraken_ocr_tool_settings"}:
            return True

        if "bottledkraken" in parts or filename.startswith("com.bottledkraken."):
            return True

        return False

    def _delete_bottled_kraken_path(self, path: str) -> Tuple[bool, str]:
        if not self._is_safe_bottled_kraken_delete_path(path):
            return False, self._tr("uninstall_delete_skipped_unsafe", path)
        try:
            if os.path.islink(path) or os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
            else:
                return True, self._tr("uninstall_delete_skipped_missing", path)
            return True, self._tr("uninstall_delete_deleted_path", path)
        except Exception as exc:
            return False, self._tr("uninstall_delete_failed_path", path, repr(exc))

    def _run_uninstall_delete_from_help(self, parent_dialog: QDialog):
        title = self._tr("uninstall_delete_confirm_title")
        first = QMessageBox.warning(
            parent_dialog or self,
            title,
            self._tr("uninstall_delete_confirm_text"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if first != QMessageBox.Yes:
            return

        phrase = self._tr("uninstall_delete_confirm_phrase")
        typed, ok = QInputDialog.getText(
            parent_dialog or self,
            title,
            self._tr("uninstall_delete_confirm_prompt", phrase),
        )
        if not ok or typed.strip() != phrase:
            QMessageBox.information(
                parent_dialog or self,
                self._tr("info_title"),
                self._tr("uninstall_delete_cancelled"),
            )
            return

        # Laufende optionale Worker möglichst sauber anhalten, bevor Dateien entfernt werden.
        for attr in ("hf_download_worker", "worker", "ai_worker", "voice_worker", "ai_batch_worker", "pdf_worker", "export_worker"):
            obj = getattr(self, attr, None)
            try:
                if obj and hasattr(obj, "cancel"):
                    obj.cancel()
            except Exception:
                pass

        self._release_bottled_kraken_runtime_files()

        paths = self._candidate_bottled_kraken_delete_paths()
        messages: List[str] = []
        ok_count = 0
        fail_count = 0

        try:
            self.settings.clear()
            self.settings.sync()
            ok_count += 1
            messages.append(self._tr("uninstall_delete_settings_cleared"))
        except Exception as exc:
            fail_count += 1
            messages.append(self._tr("uninstall_delete_settings_failed", repr(exc)))

        for path in paths:
            ok_deleted, msg = self._delete_bottled_kraken_path(path)
            messages.append(msg)
            if ok_deleted:
                ok_count += 1
            else:
                fail_count += 1

        summary = self._tr("uninstall_delete_summary", ok_count, fail_count)
        detail = "\n".join(messages[-18:])
        if len(messages) > 18:
            detail = "...\n" + detail

        QMessageBox.information(
            parent_dialog or self,
            self._tr("uninstall_delete_done_title"),
            f"{summary}\n\n{detail}\n\n{self._tr('uninstall_delete_restart_note')}",
        )

        try:
            if parent_dialog:
                parent_dialog.accept()
        except Exception:
            pass
        QTimer.singleShot(250, QApplication.quit)

    def show_lm_help_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle(self._tr("dlg_help_title"))
        dlg.resize(1380, 860)
        dlg.setMinimumSize(1240, 760)
        dlg.setStyleSheet(_help_dialog_qss(self.current_theme))
        layout = QVBoxLayout(dlg)
        scroll = QScrollArea(dlg)
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(6, 6, 6, 6)
        content_layout.setSpacing(10)
        default_install_cmd, default_download_cmd = self._whisper_button_commands("Windows")
        def _small_btn(text: str) -> QPushButton:
            button = QPushButton(text)
            button.setFixedHeight(30)
            button.setMinimumWidth(82)
            button.setMaximumWidth(110)
            button.setCursor(Qt.PointingHandCursor)
            return button
        def make_page(content_html: str) -> QTextBrowser:
            browser = QTextBrowser()
            browser.setReadOnly(True)
            browser.setOpenExternalLinks(True)
            browser.setFrameShape(QTextBrowser.NoFrame)
            browser.setOpenLinks(False)
            browser.anchorClicked.connect(QDesktopServices.openUrl)
            browser.setHtml(_help_html(self.current_theme, content_html))
            browser.setMinimumWidth(760)
            browser.document().setDocumentMargin(8)
            return browser
        nav_panel = QWidget()
        nav_panel.setFixedWidth(250)
        nav_panel_layout = QVBoxLayout(nav_panel)
        nav_panel_layout.setContentsMargins(0, 0, 0, 0)
        nav_panel_layout.setSpacing(8)

        nav_list = QListWidget()
        nav_list.setSpacing(4)
        nav_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        nav_list.setTextElideMode(Qt.ElideNone)

        nav_bottom = QListWidget()
        nav_bottom.setSpacing(4)
        nav_bottom.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        nav_bottom.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        nav_bottom.setTextElideMode(Qt.ElideNone)
        nav_bottom.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # Der untere Sonderreiter braucht unter Windows/Linux wegen Theme-Padding
        # etwas mehr Höhe, sonst wird der Text abgeschnitten.
        nav_bottom.setMinimumHeight(74)
        nav_bottom.setFixedHeight(74)

        stack = QStackedWidget()
        quick_html = self._tr("help_html_quick") + self._build_hardware_requirements_loading_html()
        kraken_html = self._tr("help_html_kraken")
        lm_server_html = self._tr("help_html_lm_server")
        ssh_html = self._tr("help_html_ssh")
        openrouter_html = self._tr("help_html_openrouter")
        page_whisper = QWidget()
        page_whisper_layout = QVBoxLayout(page_whisper)
        page_whisper_layout.setContentsMargins(0, 0, 0, 0)
        page_whisper_layout.setSpacing(8)
        page_whisper_layout.setAlignment(Qt.AlignTop)
        whisper_intro_html = self._tr("help_html_whisper_intro")
        browser_whisper_intro = make_page(whisper_intro_html)
        browser_whisper_intro.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        browser_whisper_intro.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        browser_whisper_intro.setMinimumHeight(260)
        page_whisper_layout.addWidget(browser_whisper_intro, 1)
        btn_info = QLabel(self._tr("help_whisper_download_label"))
        page_whisper_layout.addWidget(btn_info, 0)
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(6)
        btn_windows = _small_btn(self._tr("help_os_windows"))
        btn_arch = _small_btn(self._tr("help_os_arch"))
        btn_debian = _small_btn(self._tr("help_os_debian"))
        btn_fedora = _small_btn(self._tr("help_os_fedora"))
        btn_mac = _small_btn(self._tr("help_os_macos"))
        hf_cmd_browser = QTextBrowser()
        hf_cmd_browser.setReadOnly(True)
        hf_cmd_browser.setOpenExternalLinks(False)
        hf_cmd_browser.setFrameShape(QTextBrowser.NoFrame)
        hf_cmd_browser.setHtml(_help_pre(f"{default_install_cmd}\n{default_download_cmd}"))
        hf_cmd_browser.setMinimumWidth(760)
        hf_cmd_browser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        hf_cmd_browser.setFixedHeight(96)
        hf_hint_browser = QTextBrowser()
        hf_hint_browser.setReadOnly(True)
        hf_hint_browser.setOpenExternalLinks(False)
        hf_hint_browser.setFrameShape(QTextBrowser.NoFrame)
        hf_hint_browser.setHtml(_help_pre(self._whisper_system_hint("windows")))
        hf_hint_browser.setMinimumWidth(760)
        hf_hint_browser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        hf_hint_browser.setFixedHeight(112)
        def _bind_whisper_button(btn: QPushButton, platform_name: str):
            def _handler():
                install_cmd, download_cmd = self._whisper_button_commands(platform_name)
                system_hint = self._whisper_system_hint(platform_name)
                hf_cmd_browser.setHtml(_help_pre(f"{install_cmd}\n{download_cmd}"))
                hf_hint_browser.setHtml(_help_pre(system_hint))
                self.download_whisper_model_from_help_dialog(platform_name, dlg)
            btn.clicked.connect(_handler)
        _bind_whisper_button(btn_windows, "Windows")
        _bind_whisper_button(btn_arch, "Arch")
        _bind_whisper_button(btn_debian, "Debian")
        _bind_whisper_button(btn_fedora, "Fedora")
        _bind_whisper_button(btn_mac, "Mac")
        btn_row.addWidget(btn_windows)
        btn_row.addWidget(btn_arch)
        btn_row.addWidget(btn_debian)
        btn_row.addWidget(btn_fedora)
        btn_row.addWidget(btn_mac)
        btn_row.addStretch()
        page_whisper_layout.addLayout(btn_row, 0)
        page_whisper_layout.addWidget(hf_cmd_browser, 0)
        page_whisper_layout.addWidget(hf_hint_browser, 0)
        shortcuts_html = self._tr("help_html_shortcuts")
        data_protection_html = self._tr("help_html_data_protection")
        legal_html = self._tr("help_html_legal")
        quick_browser = make_page(quick_html)
        stack.addWidget(quick_browser)
        stack.addWidget(make_page(kraken_html))
        stack.addWidget(make_page(lm_server_html))
        stack.addWidget(make_page(ssh_html))
        stack.addWidget(make_page(openrouter_html))
        stack.addWidget(page_whisper)
        stack.addWidget(make_page(shortcuts_html))
        stack.addWidget(make_page(data_protection_html))
        stack.addWidget(make_page(legal_html))
        stack.addWidget(self._make_uninstall_delete_page(dlg))
        nav_items = [
            self._tr("help_nav_quick"),
            self._tr("help_nav_kraken"),
            self._tr("help_nav_lm_server"),
            self._tr("help_nav_ssh"),
            self._tr("help_nav_openrouter"),
            self._tr("help_nav_whisper"),
            self._tr("help_nav_shortcuts"),
            self._tr("help_nav_data_protection"),
            self._tr("help_nav_legal"),
        ]
        for label in nav_items:
            nav_list.addItem(label)
        nav_bottom.addItem(self._tr("help_nav_uninstall_delete"))
        bottom_item = nav_bottom.item(0)
        if bottom_item is not None:
            bottom_item.setSizeHint(QSize(220, 44))

        def _select_top(row: int):
            if row < 0:
                return
            try:
                nav_bottom.blockSignals(True)
                nav_bottom.clearSelection()
                nav_bottom.setCurrentRow(-1)
            finally:
                nav_bottom.blockSignals(False)
            stack.setCurrentIndex(row)

        def _select_bottom(row: int):
            if row < 0:
                return
            try:
                nav_list.blockSignals(True)
                nav_list.clearSelection()
                nav_list.setCurrentRow(-1)
            finally:
                nav_list.blockSignals(False)
            stack.setCurrentIndex(9)

        nav_list.currentRowChanged.connect(_select_top)
        nav_bottom.currentRowChanged.connect(_select_bottom)
        nav_list.setCurrentRow(0)
        nav_panel_layout.addWidget(nav_list, 1)
        nav_panel_layout.addWidget(nav_bottom, 0)
        content_layout.addWidget(nav_panel, 0)
        content_layout.addWidget(stack, 1)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.button(QDialogButtonBox.Ok).setText(self._tr("btn_ok"))
        buttons.accepted.connect(dlg.accept)
        layout.addWidget(buttons)
        self._start_help_hardware_refresh(quick_browser)
        dlg.exec()

    def _edited_images_output_dir(self, source_task: TaskItem) -> str:
        """
        Sammelordner für bearbeitete Bilder im gleichen Verzeichnis
        wie die Ursprungsdatei.
        """
        src_dir = os.path.dirname(os.path.abspath(source_task.path))
        out_dir = os.path.join(src_dir, "Bottled Kraken - edited pictures")
        os.makedirs(out_dir, exist_ok=True)
        return out_dir

    def _normalized_edited_image_base_name(self, source_task: TaskItem) -> str:
        """
        Liefert den stabilen Basisnamen für bearbeitete Bilder.

        Zielschema:
            originalname_edit_X_Y.png

        Dabei ist X die Bearbeitungs-/Versionsnummer für dieselbe Ursprungsdatei
        und Y die laufende Nummer innerhalb derselben Bearbeitungsrunde.
        """
        stem = os.path.splitext(os.path.basename(source_task.path))[0]
        # Neues Schema: originalname_edit_2_1 -> originalname
        stem = re.sub(r'_edit_\d+_\d+$', '', stem)
        # Altes Schema: original__edit_irgendwas -> original
        stem = re.sub(r'__edit_.*$', '', stem)
        return re.sub(r'[^A-Za-z0-9._-]+', '_', stem).strip('._') or "bild"

    def _next_edited_image_version(self, source_task: TaskItem) -> int:
        """
        Ermittelt die nächste freie Versionsnummer X für Dateien nach dem Schema
        originalname_edit_X_Y.png im Bearbeitungsordner.
        """
        edit_dir = self._edited_images_output_dir(source_task)
        base_name = self._normalized_edited_image_base_name(source_task)
        pattern = re.compile(rf'^{re.escape(base_name)}_edit_(\d+)_(\d+)\.png$', re.IGNORECASE)
        max_version = 0
        try:
            for entry in os.listdir(edit_dir):
                match = pattern.match(entry)
                if not match:
                    continue
                try:
                    max_version = max(max_version, int(match.group(1)))
                except Exception:
                    pass
        except Exception:
            pass
        return max_version + 1

    def _save_edited_image_under_original(
            self,
            source_task: TaskItem,
            pil_image: Image.Image,
            file_stem: str
    ) -> str:
        edit_dir = self._edited_images_output_dir(source_task)
        safe_stem = re.sub(r'[^A-Za-z0-9._-]+', '_', file_stem).strip('._') or "bild_edit_1_1"
        out_path = os.path.join(edit_dir, f"{safe_stem}.png")
        pil_image.convert("RGB").save(out_path, format="PNG")
        return out_path

    def _insert_task_row(self, row: int, task: TaskItem):
        row = max(0, min(row, self.queue_table.rowCount()))
        self.queue_items.insert(row, task)
        self.queue_table.insertRow(row)
        num_item = QTableWidgetItem(str(row + 1))
        num_item.setTextAlignment(Qt.AlignCenter)
        num_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        name_item = QTableWidgetItem(task.display_name)
        name_item.setData(Qt.UserRole, task.path)
        name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
        status_item = QTableWidgetItem()
        status_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.queue_table.setItem(row, QUEUE_COL_NUM, num_item)
        self.queue_table.setCellWidget(row, QUEUE_COL_CHECK, self._make_queue_checkbox_widget(False))
        self.queue_table.setItem(row, QUEUE_COL_FILE, name_item)
        self.queue_table.setItem(row, QUEUE_COL_STATUS, status_item)
        self._update_queue_row(task.path)

    def _selected_or_checked_tasks_for_edit(self) -> List[TaskItem]:
        checked = self._checked_queue_tasks()
        if checked:
            return checked
        return self._selected_queue_tasks()

    def _create_edited_tasks_from_images(
            self,
            source_task: TaskItem,
            result_images: List[Image.Image]
    ) -> List[TaskItem]:
        created = []
        total = max(1, len(result_images))
        base_name = self._normalized_edited_image_base_name(source_task)
        version = self._next_edited_image_version(source_task)
        edit_dir = self._edited_images_output_dir(source_task)
        while True:
            candidate_paths = [
                os.path.join(edit_dir, f"{base_name}_edit_{version}_{idx}.png")
                for idx in range(1, total + 1)
            ]
            if not any(os.path.exists(p) for p in candidate_paths):
                break
            version += 1
        for idx, img in enumerate(result_images, start=1):
            file_stem = f"{base_name}_edit_{version}_{idx}"
            out_path = self._save_edited_image_under_original(
                source_task=source_task,
                pil_image=img,
                file_stem=file_stem
            )
            new_task = TaskItem(
                path=out_path,
                display_name=os.path.basename(out_path),
                status=STATUS_WAITING,
                edited=False,
                source_kind="image",
                relative_path=""
            )
            # IMMER ans Ende der Queue
            end_row = self.queue_table.rowCount()
            self._insert_task_row(end_row, new_task)
            created.append(new_task)
        return created

    def _apply_image_edit_settings_to_task(self, task: TaskItem, settings: ImageEditSettings) -> List[Image.Image]:
        img = _load_image_color(task.path)
        dlg = ImageEditDialog(img, task.display_name, self)
        dlg.set_settings(settings)
        dlg._accept_dialog()
        return list(dlg.result_images or [])
