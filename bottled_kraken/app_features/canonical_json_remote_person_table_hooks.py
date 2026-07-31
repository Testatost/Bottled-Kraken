from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
from bottled_kraken.common import _force_text
from bottled_kraken.pointer_features import (
    PtrAIToolsDialog,
    PtrOpenRouterWaitDialog,
    PtrRemoteAICancelled,
    _ptr_extract_content_from_chat_response,
    _ptr_extract_json_object,
    _ptr_remote_chat_completion,
    _ptr_ui_tr,
)
from bottled_kraken.common import (
    QApplication,
    QFileDialog,
    QThread,
    QTimer,
    Qt,
    Signal,
    threading,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    Tuple,
    json,
    os,
    translation,
)
from bottled_kraken.main_window import MainWindow
from PySide6.QtGui import QPainterPath
from PySide6.QtWidgets import (
    QComboBox,
    QGraphicsEllipseItem,
    QGraphicsTextItem,
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsPathItem,
    QGraphicsLineItem,
    QGroupBox,
    QSlider,
    QCheckBox,
    QLineEdit,
)
def _bk_owner_for_prompt_settings(obj):
    cur = obj
    for _ in range(8):
        if cur is None:
            break
        if hasattr(cur, "settings") and hasattr(cur, "current_lang"):
            return cur
        try:
            cur = cur.parent()
        except Exception:
            break
    return obj
def _bk_canonical_prompt_text(owner, key: str, fallback: str = "") -> str:
    try:
        if "_bk_lm_prompt_override" in globals():
            override = _bk_lm_prompt_override(owner, key)
            if override:
                return str(override)
    except Exception:
        pass
    try:
        if hasattr(owner, "_tr"):
            value = owner._tr(key)
            if value and value != key:
                return str(value)
    except Exception:
        pass
    try:
        lang = getattr(owner, "current_lang", translation.DEFAULT_LANGUAGE)
        value = translation.translate(lang, key)
        if value and value != key:
            return str(value)
    except Exception:
        pass
    return fallback
def _bk_canonical_token_limit(owner, default: int = 12000) -> int:
    try:
        if "_lm_token_limit" in globals():
            return max(9000, int(_lm_token_limit(owner, "canonical")))
    except Exception:
        pass
    return max(9000, int(default))
def _bk_remote_canonical_prompt(source_text: str, tr_func=None, owner=None) -> Tuple[str, str]:
    owner = _bk_owner_for_prompt_settings(owner) if owner is not None else owner
    system_prompt = _bk_canonical_prompt_text(owner, "ai_prompt_canonical_system") if owner is not None else ""
    user_template = _bk_canonical_prompt_text(owner, "ai_prompt_canonical_user") if owner is not None else ""
    if not system_prompt and callable(tr_func):
        try:
            system_prompt = tr_func("ai_prompt_canonical_system")
            user_template = user_template or tr_func("ai_prompt_canonical_user")
        except Exception:
            pass
    system_prompt = system_prompt if system_prompt and system_prompt != "ai_prompt_canonical_system" else (
        "You are a JSON-only extraction engine for OCR-derived genealogical and historical records. "
        "Return exactly one valid JSON object, no markdown, no explanations, no code fences. "
        "The JSON must contain document, entities, relations and metadata."
    )
    schema_template = (
        "{\n"
        '  "document": {"id":"document_1","title":null,"source_type":"ocr_text","language":null},\n'
        '  "entities": [{"id":"entity_1","type":"PERSON|PLACE|YEAR|EVENT|DOCUMENT|ENTITY","label":"...","attributes":{},"evidence":"..."}],\n'
        '  "relations": [{"id":"rel_1","source":"entity_1","target":"entity_2","type":"RELATED_TO|LOCATED_IN|DURING|PART_OF|ASSOCIATED_WITH","attributes":{"strength":0.0},"evidence":"..."}],\n'
        '  "metadata": {"schema":"canonical_graph","version":1}\n'
        "}"
    )
    if user_template and user_template != "ai_prompt_canonical_user":
        try:
            user_prompt = user_template.format(schema_template=schema_template, ocr_text=_force_text(source_text)[:60000])
        except Exception:
            user_prompt = user_template + "\n\nOCR_TEXT_START\n" + _force_text(source_text)[:60000] + "\nOCR_TEXT_END"
    else:
        user_prompt = (
            "Create canonical_graph JSON from this OCR text.\n"
            "Schema:\n"
            f"{schema_template}\n"
            "Rules: use only information supported by OCR text; use null for unknown values; strength 0.0 to 1.0; arrays may be empty.\n\n"
            "OCR_TEXT_START\n" + _force_text(source_text)[:60000] + "\nOCR_TEXT_END"
        )
    return system_prompt, user_prompt
def _bk_ptr_dialog_collect_source_for_canonical(dialog) -> str:
    merged = ""
    try:
        merged = dialog._collect_merged_text()
    except Exception:
        merged = ""
    if not merged:
        try:
            parts = dialog._collect_ocr_inputs()
            merged = "\n".join(str(p) for p in parts if str(p).strip())
        except Exception:
            merged = ""
    result_text = ""
    try:
        result_text = dialog.result_output_edit.toPlainText().strip()
    except Exception:
        result_text = ""
    return (merged or result_text or "").strip()
def _bk_ptr_dialog_show_remote_canonical_graph(self):
    try:
        canonical = getattr(self, "_bk_remote_canonical_json", None)
        if not isinstance(canonical, dict):
            text = self.result_output_edit.toPlainText().strip()
            if text:
                canonical = _bk_prepare_canonical_json(_ptr_extract_json_object(text), text)
        if not isinstance(canonical, dict):
            QMessageBox.warning(self, _ptr_ui_tr(self, "warn_title"), _ptr_ui_tr(self, "ptr_canonical_no_json"))
            return
        dlg = BKCanonicalGraphDialog(self, lambda k, *a: _ptr_ui_tr(self, k, *a), canonical, "openrouter_canonical.json")
        try:
            dlg.setWindowState(dlg.windowState() | Qt.WindowMaximized)
        except Exception:
            pass
        try:
            dlg.showMaximized()
            QApplication.processEvents()
        except Exception:
            pass
        dlg.exec()
    except Exception as exc:
        QMessageBox.warning(self, _ptr_ui_tr(self, "warn_title"), str(exc))
_BK_CANONICAL_PREV_PTR_INIT = PtrAIToolsDialog.__init__ if "PtrAIToolsDialog" in globals() else None
_BK_CANONICAL_PREV_PTR_SET_BUSY = PtrAIToolsDialog._set_busy if "PtrAIToolsDialog" in globals() and hasattr(PtrAIToolsDialog, "_set_busy") else None

def _bk_ptr_dialog_init_with_canonical(self, *args, **kwargs):
    if _BK_CANONICAL_PREV_PTR_INIT is not None:
        _BK_CANONICAL_PREV_PTR_INIT(self, *args, **kwargs)
    if getattr(self, "_bk_canonical_buttons_installed", False):
        return
    self._bk_canonical_buttons_installed = True
    self._bk_remote_canonical_json = None
    try:
        self.canonical_json_btn = None
        self.canonical_graph_btn = None
        btn = getattr(self, "graph_display_btn", None)
        if btn is None:
            row = QHBoxLayout()
            btn = QPushButton(_ptr_ui_tr(self, "ptr_ai_btn_graph_display"))
            btn.setMinimumWidth(230)
            row.addStretch(1)
            row.addWidget(btn, 1)
            self.layout().insertLayout(max(0, self.layout().count() - 1), row)
            self.graph_display_btn = btn
        btn.setText(_ptr_ui_tr(self, "ptr_ai_btn_graph_display"))
        if not getattr(self, "_bk_graph_display_connected", False):
            btn.clicked.connect(lambda: _bk_ptr_dialog_generate_and_show_remote_canonical(self))
            self._bk_graph_display_connected = True
        load_btn = getattr(self, "graph_load_btn", None)
        if load_btn is not None:
            load_btn.setText(_ptr_ui_tr(self, "ptr_ai_btn_graph_load"))
            if not getattr(self, "_bk_graph_load_connected", False):
                load_btn.clicked.connect(lambda: _bk_ptr_dialog_load_canonical_json_and_show_graph(self))
                self._bk_graph_load_connected = True
    except Exception:
        pass

def _bk_ptr_dialog_load_canonical_json_and_show_graph(self):
    """Load an existing canonical JSON and open the graph view without a new OpenRouter request."""
    try:
        start_dir = ""
        try:
            parent = self.parent()
            if parent is not None and hasattr(parent, "current_file_path"):
                current = str(getattr(parent, "current_file_path", "") or "")
                if current:
                    start_dir = os.path.dirname(current)
        except Exception:
            start_dir = ""
        path, _ = QFileDialog.getOpenFileName(
            self,
            _ptr_ui_tr(self, "ptr_ai_btn_graph_load"),
            start_dir or "",
            _ptr_ui_tr(self, "dlg_filter_json"),
        )
        if not path:
            return False
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            raise RuntimeError(_ptr_ui_tr(self, "ptr_graph_load_invalid_json"))
        canonical = _bk_prepare_canonical_json(data, path)
        self._bk_remote_canonical_json = canonical
        try:
            self.result_output_edit.setPlainText(json.dumps(canonical, ensure_ascii=False, indent=2))
        except Exception:
            pass
        try:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            self.progress_label.setText(_ptr_ui_tr(self, "ptr_graph_load_ready"))
        except Exception:
            pass
        dlg = BKCanonicalGraphDialog(self, lambda k, *a: _ptr_ui_tr(self, k, *a), canonical, path)
        try:
            dlg.setWindowState(dlg.windowState() | Qt.WindowMaximized)
        except Exception:
            pass
        try:
            dlg.showMaximized()
            QApplication.processEvents()
        except Exception:
            pass
        dlg.exec()
        return True
    except Exception as exc:
        QMessageBox.warning(self, _ptr_ui_tr(self, "warn_title"), str(exc))
        return False

class BKRemoteCanonicalGraphWorker(QThread):
    graph_ready = Signal(object)
    failed = Signal(str)
    canceled = Signal(str)

    def __init__(self, config, source_text: str, owner=None, parent=None):
        super().__init__(parent)
        self.config = config
        self.source_text = str(source_text or "")
        self.owner = owner
        self._cancel_requested = False
        self._active_connection = None
        self._active_connection_lock = threading.Lock()

    def _tr(self, key: str, *args):
        owner = self.owner
        try:
            lang = getattr(owner, "current_lang", None) or getattr(owner, "_lang", lambda: None)()
            if not lang and hasattr(owner, "parent"):
                lang = getattr(owner.parent(), "current_lang", None)
            return translation.translate(lang or translation.DEFAULT_LANGUAGE, key, *args)
        except Exception:
            try:
                return translation.translate(translation.DEFAULT_LANGUAGE, key, *args)
            except Exception:
                return key

    def _raise_if_cancelled(self):
        if self._cancel_requested or self.isInterruptionRequested():
            raise PtrRemoteAICancelled(self._tr("ptr_graph_wait_cancelled_status"))

    def _set_active_connection(self, connection):
        with self._active_connection_lock:
            self._active_connection = connection

    def _close_active_connection(self):
        with self._active_connection_lock:
            connection = self._active_connection
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass

    def cancel(self):
        self._cancel_requested = True
        try:
            self.requestInterruption()
        except Exception:
            pass
        self._close_active_connection()

    def _install_cancel_hooks(self):
        try:
            setattr(self.config, "_bk_cancel_checker", self._raise_if_cancelled)
            setattr(self.config, "_bk_connection_owner", self)
        except Exception:
            pass

    def _remove_cancel_hooks(self):
        for name in ("_bk_cancel_checker", "_bk_connection_owner"):
            try:
                if hasattr(self.config, name):
                    delattr(self.config, name)
            except Exception:
                pass

    def run(self):
        self._install_cancel_hooks()
        try:
            self._raise_if_cancelled()
            owner = _bk_owner_for_prompt_settings(self.owner)
            system_prompt, user_prompt = _bk_remote_canonical_prompt(
                self.source_text,
                lambda k, *a: self._tr(k, *a),
                owner=owner,
            )
            max_tokens = _bk_canonical_token_limit(owner, 12000)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            try:
                raw = _ptr_remote_chat_completion(
                    self.config,
                    messages,
                    expect_json=True,
                    max_tokens=max_tokens,
                )
                content = _ptr_extract_content_from_chat_response(raw)
            except Exception:
                retry_messages = [
                    {"role": "system", "content": "Return JSON only. The response must be one parseable JSON object."},
                    {"role": "user", "content": user_prompt[:22000]},
                ]
                try:
                    raw = _ptr_remote_chat_completion(
                        self.config,
                        retry_messages,
                        expect_json=False,
                        max_tokens=max_tokens,
                    )
                    content = _ptr_extract_content_from_chat_response(raw)
                except Exception as retry_exc:
                    raise RuntimeError(self._tr("ptr_canonical_remote_failed", retry_exc)) from retry_exc
            self._raise_if_cancelled()
            try:
                data = _ptr_extract_json_object(content)
                canonical = _bk_prepare_canonical_json(data, self.source_text)
            except Exception as parse_exc:
                raise RuntimeError(self._tr("ptr_canonical_remote_invalid_json", parse_exc)) from parse_exc
            self._raise_if_cancelled()
            self.graph_ready.emit(canonical)
        except PtrRemoteAICancelled as exc:
            self.canceled.emit(str(exc))
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self._remove_cancel_hooks()

def _bk_ptr_dialog_show_graph_wait_dialog(self):
    dlg = getattr(self, "_bk_graph_wait_dialog", None)
    if dlg is None:
        dlg = PtrOpenRouterWaitDialog(self, lambda k, *a: _ptr_ui_tr(self, k, *a), key_prefix="ptr_graph_wait")
        dlg.cancel_requested.connect(lambda: _bk_ptr_dialog_cancel_graph_worker(self))
        self._bk_graph_wait_dialog = dlg
    try:
        dlg.show()
        if hasattr(dlg, "spinner"):
            dlg.spinner.start()
        QApplication.processEvents()
    except Exception:
        pass

def _bk_ptr_dialog_hide_graph_wait_dialog(self):
    dlg = getattr(self, "_bk_graph_wait_dialog", None)
    if dlg is None:
        return
    try:
        dlg.mark_finished()
        dlg.hide()
        dlg.deleteLater()
    except Exception:
        pass
    self._bk_graph_wait_dialog = None

def _bk_ptr_dialog_force_release_graph_worker(self, worker):
    if worker is None or worker is not getattr(self, "_bk_graph_worker", None) or not worker.isRunning():
        return
    for signal_name, handler_name in (("graph_ready", "_bk_on_graph_worker_ready"), ("failed", "_bk_on_graph_worker_failed"), ("canceled", "_bk_on_graph_worker_canceled")):
        try:
            getattr(worker, signal_name).disconnect(getattr(self, handler_name))
        except Exception:
            pass
    abandoned = getattr(self, "_bk_abandoned_graph_workers", None)
    if abandoned is None:
        abandoned = []
        self._bk_abandoned_graph_workers = abandoned
    abandoned.append(worker)
    try:
        worker.finished.connect(lambda: abandoned.remove(worker) if worker in abandoned else None)
    except Exception:
        pass
    self._bk_graph_worker = None
    _bk_ptr_dialog_hide_graph_wait_dialog(self)
    try:
        self._set_busy(False)
    except Exception:
        pass
    try:
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_label.setText(_ptr_ui_tr(self, "ptr_graph_wait_cancelled_status"))
    except Exception:
        pass

def _bk_ptr_dialog_cancel_graph_worker(self):
    worker = getattr(self, "_bk_graph_worker", None)
    if worker is None or not worker.isRunning():
        _bk_ptr_dialog_hide_graph_wait_dialog(self)
        try:
            self._set_busy(False)
        except Exception:
            pass
        return
    try:
        worker.cancel()
    except Exception:
        try:
            worker.requestInterruption()
        except Exception:
            pass
    QTimer.singleShot(1500, lambda w=worker: _bk_ptr_dialog_force_release_graph_worker(self, w))

def _bk_ptr_dialog_on_graph_worker_ready(self, canonical):
    self._bk_remote_canonical_json = canonical
    try:
        self.result_output_edit.setPlainText(json.dumps(canonical, ensure_ascii=False, indent=2))
    except Exception:
        pass
    _bk_ptr_dialog_hide_graph_wait_dialog(self)
    try:
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_label.setText(_ptr_ui_tr(self, "ptr_ai_canonical_ready"))
    except Exception:
        pass
    try:
        self._set_busy(False)
    except Exception:
        pass
    self._bk_graph_worker = None
    QTimer.singleShot(0, lambda: _bk_ptr_dialog_show_remote_canonical_graph(self))

def _bk_ptr_dialog_on_graph_worker_failed(self, message: str):
    _bk_ptr_dialog_hide_graph_wait_dialog(self)
    try:
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_label.setText(_ptr_ui_tr(self, "ptr_ai_progress_idle"))
    except Exception:
        pass
    try:
        self._set_busy(False)
    except Exception:
        pass
    self._bk_graph_worker = None
    QMessageBox.warning(self, _ptr_ui_tr(self, "warn_title"), str(message))

def _bk_ptr_dialog_on_graph_worker_canceled(self, message: str):
    _bk_ptr_dialog_hide_graph_wait_dialog(self)
    try:
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_label.setText(_ptr_ui_tr(self, "ptr_graph_wait_cancelled_status"))
    except Exception:
        pass
    try:
        self._set_busy(False)
    except Exception:
        pass
    self._bk_graph_worker = None

def _bk_ptr_dialog_generate_remote_canonical(self):
    source_text = _bk_ptr_dialog_collect_source_for_canonical(self)
    if not source_text:
        _bk_ptr_dialog_hide_graph_wait_dialog(self)
        QMessageBox.warning(self, _ptr_ui_tr(self, "warn_title"), _ptr_ui_tr(self, "ptr_canonical_no_text"))
        return False
    cfg = self.get_config()
    try:
        cfg._bk_prompt_owner = _bk_owner_for_prompt_settings(self)
    except Exception:
        pass
    worker = getattr(self, "_bk_graph_worker", None)
    if worker is not None:
        try:
            if worker.isRunning():
                _bk_ptr_dialog_show_graph_wait_dialog(self)
                return True
        except Exception:
            pass
    self._set_busy(True)
    self.progress_label.setText(_ptr_ui_tr(self, "ptr_ai_running_canonical"))
    self.progress_bar.setRange(0, 0)
    _bk_ptr_dialog_show_graph_wait_dialog(self)
    QApplication.processEvents()
    worker = BKRemoteCanonicalGraphWorker(cfg, source_text, owner=self, parent=self)
    self._bk_graph_worker = worker
    self._bk_on_graph_worker_ready = lambda canonical: _bk_ptr_dialog_on_graph_worker_ready(self, canonical)
    self._bk_on_graph_worker_failed = lambda message: _bk_ptr_dialog_on_graph_worker_failed(self, message)
    self._bk_on_graph_worker_canceled = lambda message: _bk_ptr_dialog_on_graph_worker_canceled(self, message)
    worker.graph_ready.connect(self._bk_on_graph_worker_ready)
    worker.failed.connect(self._bk_on_graph_worker_failed)
    worker.canceled.connect(self._bk_on_graph_worker_canceled)
    worker.finished.connect(worker.deleteLater)
    worker.start()
    return True

def _bk_ptr_dialog_generate_and_show_remote_canonical(self):
    try:
        return _bk_ptr_dialog_generate_remote_canonical(self)
    except Exception as exc:
        _bk_ptr_dialog_hide_graph_wait_dialog(self)
        try:
            self._set_busy(False)
        except Exception:
            pass
        QMessageBox.warning(self, _ptr_ui_tr(self, "warn_title"), str(exc))
        return False

def _bk_ptr_dialog_set_busy_with_canonical(self, busy: bool):
    if _BK_CANONICAL_PREV_PTR_SET_BUSY is not None:
        _BK_CANONICAL_PREV_PTR_SET_BUSY(self, busy)
    for _attr in ("graph_display_btn", "graph_load_btn", "canonical_json_btn", "canonical_graph_btn"):
        try:
            widget = getattr(self, _attr, None)
            if widget is not None:
                widget.setEnabled(not bool(busy))
        except Exception:
            pass
if _BK_CANONICAL_PREV_PTR_INIT is not None:
    PtrAIToolsDialog.__init__ = _bk_ptr_dialog_init_with_canonical
    PtrAIToolsDialog._bk_generate_remote_canonical_json = _bk_ptr_dialog_generate_remote_canonical
    PtrAIToolsDialog._bk_show_remote_canonical_graph = _bk_ptr_dialog_show_remote_canonical_graph
    PtrAIToolsDialog._bk_generate_remote_canonical_and_show_graph = _bk_ptr_dialog_generate_and_show_remote_canonical
    PtrAIToolsDialog._bk_load_canonical_json_and_show_graph = _bk_ptr_dialog_load_canonical_json_and_show_graph
    if _BK_CANONICAL_PREV_PTR_SET_BUSY is not None:
        PtrAIToolsDialog._set_busy = _bk_ptr_dialog_set_busy_with_canonical
__all__ = [
    '_BK_CANONICAL_PREV_PTR_INIT',
    '_BK_CANONICAL_PREV_PTR_SET_BUSY',
    '_bk_canonical_prompt_text',
    '_bk_canonical_token_limit',
    '_bk_owner_for_prompt_settings',
    '_bk_ptr_dialog_collect_source_for_canonical',
    '_bk_ptr_dialog_generate_and_show_remote_canonical',
    '_bk_ptr_dialog_generate_remote_canonical',
    '_bk_ptr_dialog_load_canonical_json_and_show_graph',
    'BKRemoteCanonicalGraphWorker',
    '_bk_ptr_dialog_show_graph_wait_dialog',
    '_bk_ptr_dialog_hide_graph_wait_dialog',
    '_bk_ptr_dialog_force_release_graph_worker',
    '_bk_ptr_dialog_cancel_graph_worker',
    '_bk_ptr_dialog_on_graph_worker_ready',
    '_bk_ptr_dialog_on_graph_worker_failed',
    '_bk_ptr_dialog_on_graph_worker_canceled',
    '_bk_ptr_dialog_init_with_canonical',
    '_bk_ptr_dialog_set_busy_with_canonical',
    '_bk_ptr_dialog_show_remote_canonical_graph',
    '_bk_remote_canonical_prompt',
]
register_globals('bk', globals(), __all__)
