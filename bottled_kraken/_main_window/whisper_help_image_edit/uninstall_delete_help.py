from bottled_kraken.user_storage import bottled_kraken_user_root
from bottled_kraken.common import _help_html
from bottled_kraken.common import (
    List,
    QApplication,
    QDesktopServices,
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QTimer,
    QVBoxLayout,
    QWidget,
    Qt,
    Tuple,
    os,
    shutil,
    sys,
)
class MainWindowUninstallDeleteHelpMixin:
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
            add(str(bottled_kraken_user_root()))
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
            try:
                whisper_base = self._normalize_whisper_base_dir(getattr(self, "whisper_models_base_dir", ""))
                if whisper_base and "BottledKraken" in os.path.abspath(whisper_base).split(os.sep):
                    add(whisper_base)
            except Exception:
                pass
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
