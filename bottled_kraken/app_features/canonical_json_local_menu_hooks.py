from bottled_kraken.module_registry import register_globals, seed_globals
from bottled_kraken.common.chain_consolidation import register_init_delta, register_retranslate_delta
seed_globals('bk', globals())
from bottled_kraken.common import (
    Any,
    Dict,
    QAction,
    QFileDialog,
    QMessageBox,
    os,
    json,
)
from bottled_kraken.dialogs import (
    BusyStatusDialog,
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
BKLocalStructuredJsonWorker._build_canonical_json = _bk_build_canonical_json
_BK_CANONICAL_PREV_WORKER_RUN = BKLocalStructuredJsonWorker.run
def _bk_canonical_worker_run(self):
    if (getattr(self, "schema_kind", "") or "").strip().lower() != _BK_CANONICAL_SCHEMA_KIND:
        return _BK_CANONICAL_PREV_WORKER_RUN(self)
    try:
        if self._cancelled or self.isInterruptionRequested():
            raise RuntimeError(self._tr("msg_local_json_cancelled"))
        self.progress_changed.emit(5)
        self.status_changed.emit(self._tr("dlg_local_json_connecting"))
        self.progress_changed.emit(45)
        self.status_changed.emit(self._tr("status_local_json_generating_canonical"))
        data = self._build_canonical_json()
        if self._cancelled or self.isInterruptionRequested():
            raise RuntimeError(self._tr("msg_local_json_cancelled"))
        self.progress_changed.emit(100)
        self.finished_json.emit(self.path, _BK_CANONICAL_SCHEMA_KIND, data)
    except Exception as exc:
        self.failed_json.emit(self.path, _BK_CANONICAL_SCHEMA_KIND, str(exc))
BKLocalStructuredJsonWorker.run = _bk_canonical_worker_run
def _bk_ensure_structured_json_prompt_keys():
    try:
        existing = [k for k, _label in _BK_LM_PROMPT_KEYS]
        extra = []
        for item in (
            ("ai_prompt_canonical_system", "lm_prompt_canonical_system"),
            ("ai_prompt_canonical_user", "lm_prompt_canonical_user"),
            ("ai_prompt_postgresql_system", "lm_prompt_postgresql_system"),
            ("ai_prompt_postgresql_user", "lm_prompt_postgresql_user"),
            ("ai_prompt_neo4j_system", "lm_prompt_neo4j_system"),
            ("ai_prompt_neo4j_user", "lm_prompt_neo4j_user"),
            ("ai_prompt_sqlite_system", "lm_prompt_sqlite_system"),
            ("ai_prompt_sqlite_user", "lm_prompt_sqlite_user"),
        ):
            if item[0] not in existing:
                extra.append(item)
        if extra:
            globals()["_BK_LM_PROMPT_KEYS"] = tuple(_BK_LM_PROMPT_KEYS) + tuple(extra)
    except Exception:
        pass
_bk_ensure_structured_json_prompt_keys()
_BK_CANONICAL_PREV_SCHEMA_LABEL = _bk_json_schema_kind_label if "_bk_json_schema_kind_label" in globals() else None
def _bk_json_schema_kind_label(window, schema_kind: str) -> str:
    kind = str(schema_kind or "").strip().lower()
    if kind == _BK_CANONICAL_SCHEMA_KIND:
        try:
            return window._tr("canonical_json_label")
        except Exception:
            return "Canonical JSON"
    if _BK_CANONICAL_PREV_SCHEMA_LABEL is not None:
        return _BK_CANONICAL_PREV_SCHEMA_LABEL(window, schema_kind)
    return str(schema_kind or "JSON")
def _bk_lm_show_canonical_graph_dialog(self, data: Dict[str, Any], task_path: str = ""):
    canonical = _bk_prepare_canonical_json(data if isinstance(data, dict) else {})
    dlg = BKCanonicalGraphDialog(self, self._tr, canonical, task_path=task_path)
    self._bk_last_canonical_graph_dialog = dlg
    dlg.exec()

def _bk_lm_load_canonical_graph_json(self):
    task = _bk_lm_get_current_done_task(self) if "_bk_lm_get_current_done_task" in globals() else None
    start_dir = getattr(self, "current_export_dir", "") or ""
    if not start_dir and task is not None:
        try:
            start_dir = os.path.dirname(getattr(task, "path", "") or "")
        except Exception:
            start_dir = ""
    if not start_dir:
        try:
            start_dir = os.getcwd()
        except Exception:
            start_dir = ""
    path, _ = QFileDialog.getOpenFileName(
        self,
        self._tr("dlg_load_canonical_json_title"),
        start_dir,
        self._tr("filter_json_files"),
    )
    if not path:
        return
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            raise ValueError(self._tr("warn_canonical_json_invalid"))
        canonical = _bk_prepare_canonical_json(data)
        if not isinstance(canonical, dict):
            raise ValueError(self._tr("warn_canonical_json_invalid"))
        if not hasattr(self, "_bk_canonical_by_path") or not isinstance(getattr(self, "_bk_canonical_by_path", None), dict):
            self._bk_canonical_by_path = {}
        self._bk_canonical_by_path[path] = canonical
        self._bk_last_canonical_json = canonical
        self._bk_last_canonical_path = path
        try:
            self.current_export_dir = os.path.dirname(path)
        except Exception:
            pass
        try:
            self.status_bar.showMessage(self._tr("msg_canonical_json_loaded").format(os.path.basename(path)), 5000)
        except Exception:
            pass
        try:
            _bk_lm_update_dropdown_state(self)
        except Exception:
            pass
        _bk_lm_show_canonical_graph_dialog(self, canonical, task_path=path)
    except Exception as exc:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_canonical_json_load_failed").format(exc))
def _bk_lm_show_current_canonical_graph(self):
    task = _bk_lm_get_current_done_task(self)
    path = getattr(task, "path", "") if task else ""
    data = None
    if path:
        data = getattr(self, "_bk_canonical_by_path", {}).get(path)
    if not isinstance(data, dict):
        data = getattr(self, "_bk_last_canonical_json", None)
        path = path or getattr(self, "_bk_last_canonical_path", "")
    if not isinstance(data, dict):
        QMessageBox.information(self, self._tr("info_title"), self._tr("warn_no_canonical_json"))
        return
    _bk_lm_show_canonical_graph_dialog(self, data, task_path=path)
_BK_CANONICAL_PREV_DONE = _bk_lm_on_local_json_done if "_bk_lm_on_local_json_done" in globals() else None
def _bk_lm_on_local_json_done(self, path: str, schema_kind: str, data: dict):
    kind = (schema_kind or "").strip().lower()
    if kind != _BK_CANONICAL_SCHEMA_KIND:
        if _BK_CANONICAL_PREV_DONE is not None:
            return _BK_CANONICAL_PREV_DONE(self, path, schema_kind, data)
        return
    worker = getattr(self, "_bk_local_json_worker", None)
    if worker is not None:
        try:
            worker.deleteLater()
        except Exception:
            pass
    self._bk_local_json_worker = None
    self._bk_local_json_context = None
    self.act_ai_revise.setEnabled(True)
    if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
        self.btn_ai_revise_bottom.setEnabled(True)
    if hasattr(self, "_bk_local_json_dialog") and self._bk_local_json_dialog:
        try:
            self._bk_local_json_dialog.close()
        except Exception:
            pass
        self._bk_local_json_dialog = None
    canonical = _bk_prepare_canonical_json(data if isinstance(data, dict) else {})
    self._bk_canonical_by_path[path] = canonical
    self._bk_last_canonical_json = canonical
    self._bk_last_canonical_path = path
    self.status_bar.showMessage(self._tr("msg_local_json_done_canonical"), 4000)
    self._log(self._tr_log("log_local_json_done", os.path.basename(path), _bk_json_schema_kind_label(self, kind)))
    try:
        _bk_lm_update_dropdown_state(self)
    except Exception:
        pass
    _bk_lm_show_canonical_graph_dialog(self, canonical, task_path=path)
def _bk_lm_generate_canonical_json(self):
    task = _bk_lm_get_current_done_task(self)
    if not task:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_done_for_ai"))
        return
    source_text = _bk_lm_collect_current_text(self, task)
    if not source_text:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_no_text_for_json"))
        return
    model_id = self._resolve_ai_model_id()
    if not model_id:
        QMessageBox.warning(self, self._tr("warn_title"), self._tr("warn_need_ai_model"))
        return
    if _bk_lm_any_job_running(self):
        return
    self._bk_local_json_context = {"path": task.path, "schema_kind": _BK_CANONICAL_SCHEMA_KIND}
    self.act_ai_revise.setEnabled(False)
    if hasattr(self, "btn_ai_revise_bottom") and self.btn_ai_revise_bottom is not None:
        self.btn_ai_revise_bottom.setEnabled(False)
    self.status_bar.showMessage(self._tr("msg_local_json_started_canonical"))
    self._log(self._tr_log("log_local_json_started", os.path.basename(task.path), _bk_json_schema_kind_label(self, _BK_CANONICAL_SCHEMA_KIND)))
    self._bk_local_json_dialog = BusyStatusDialog(self._tr("dlg_local_json_title_canonical"), self._tr("dlg_local_json_wait_text_canonical"), self._tr, self)
    self._bk_local_json_dialog.cancel_requested.connect(lambda: _bk_lm_cancel_local_json(self))
    self._bk_local_json_dialog.show()
    self._bk_local_json_worker = BKLocalStructuredJsonWorker(
        path=task.path,
        source_text=source_text,
        schema_kind=_BK_CANONICAL_SCHEMA_KIND,
        lm_model=model_id,
        endpoint=self.ai_endpoint,
        enable_thinking=self.ai_enable_thinking,
        temperature=self.ai_temperature,
        top_p=self.ai_top_p,
        top_k=self.ai_top_k,
        presence_penalty=self.ai_presence_penalty,
        repetition_penalty=self.ai_repetition_penalty,
        min_p=self.ai_min_p,
        max_tokens=max(_lm_token_limit(self, "canonical") if "_lm_token_limit" in globals() else int(getattr(self, "ai_max_tokens", 9000) or 9000), 9000),
        tr_func=self._tr,
        parent=self,
    )
    try:
        self._bk_local_json_worker.canonical_system_prompt = (
            _bk_lm_prompt_override(self, "ai_prompt_canonical_system")
            if "_bk_lm_prompt_override" in globals() else ""
        ) or self._tr("ai_prompt_canonical_system")
        self._bk_local_json_worker.canonical_user_prompt = (
            _bk_lm_prompt_override(self, "ai_prompt_canonical_user")
            if "_bk_lm_prompt_override" in globals() else ""
        ) or self._tr("ai_prompt_canonical_user")
    except Exception:
        pass
    self._bk_local_json_worker.status_changed.connect(self._log)
    try:
        self._bk_local_json_worker.progress_changed.connect(self._bk_local_json_dialog.set_progress)
        self._bk_local_json_worker.status_changed.connect(self._bk_local_json_dialog.set_status)
    except Exception:
        pass
    self._bk_local_json_worker.finished_json.connect(lambda path, kind, data: _bk_lm_on_local_json_done(self, path, kind, data))
    self._bk_local_json_worker.failed_json.connect(lambda path, kind, msg: _bk_lm_on_local_json_failed(self, path, kind, msg))
    self._bk_local_json_worker.start()
_BK_CANONICAL_PREV_UPDATE_DROPDOWN_STATE = _bk_lm_update_dropdown_state if "_bk_lm_update_dropdown_state" in globals() else None
def _bk_lm_update_dropdown_state(self):
    if _BK_CANONICAL_PREV_UPDATE_DROPDOWN_STATE is not None:
        try:
            _BK_CANONICAL_PREV_UPDATE_DROPDOWN_STATE(self)
        except Exception:
            pass
    busy = _bk_lm_any_job_running(self)
    task = _bk_lm_get_current_done_task(self)
    if hasattr(self, "act_ai_menu_canonical"):
        self.act_ai_menu_canonical.setEnabled(bool(task) and not busy)
    if hasattr(self, "act_ai_menu_canonical_graph"):
        path = getattr(task, "path", "") if task else ""
        has_data = bool(path and isinstance(getattr(self, "_bk_canonical_by_path", {}).get(path), dict)) or isinstance(getattr(self, "_bk_last_canonical_json", None), dict)
        self.act_ai_menu_canonical_graph.setEnabled(has_data and not busy)
    if hasattr(self, "act_ai_menu_canonical_load"):
        self.act_ai_menu_canonical_load.setEnabled(not busy)
_BK_CANONICAL_PREV_INSTALL_DROPDOWN = _bk_lm_install_dropdown_menu if "_bk_lm_install_dropdown_menu" in globals() else None
def _bk_lm_install_dropdown_menu(self):
    if _BK_CANONICAL_PREV_INSTALL_DROPDOWN is not None:
        _BK_CANONICAL_PREV_INSTALL_DROPDOWN(self)
    if not hasattr(self, "btn_ai_revise_menu") or self.btn_ai_revise_menu is None:
        return
    if not hasattr(self, "_bk_canonical_by_path"):
        self._bk_canonical_by_path = {}
        self._bk_last_canonical_json = None
        self._bk_last_canonical_path = ""
    if not hasattr(self, "act_ai_menu_canonical"):
        self.act_ai_menu_canonical = QAction(self._tr("lm_menu_generate_canonical"), self)
        self.act_ai_menu_canonical.triggered.connect(lambda: _bk_lm_generate_canonical_json(self))
    if not hasattr(self, "act_ai_menu_canonical_graph"):
        self.act_ai_menu_canonical_graph = QAction(self._tr("lm_menu_show_canonical_graph"), self)
        self.act_ai_menu_canonical_graph.triggered.connect(lambda: _bk_lm_show_current_canonical_graph(self))
    if not hasattr(self, "act_ai_menu_canonical_load"):
        self.act_ai_menu_canonical_load = QAction(self._tr("lm_menu_load_canonical_graph"), self)
        self.act_ai_menu_canonical_load.triggered.connect(lambda: _bk_lm_load_canonical_graph_json(self))
    actions = list(self.btn_ai_revise_menu.actions())
    if self.act_ai_menu_canonical not in actions:
        self.btn_ai_revise_menu.addSeparator()
        self.btn_ai_revise_menu.addAction(self.act_ai_menu_canonical)
    actions = list(self.btn_ai_revise_menu.actions())
    if self.act_ai_menu_canonical_graph not in actions:
        self.btn_ai_revise_menu.addAction(self.act_ai_menu_canonical_graph)
    actions = list(self.btn_ai_revise_menu.actions())
    if self.act_ai_menu_canonical_load not in actions:
        self.btn_ai_revise_menu.addAction(self.act_ai_menu_canonical_load)
    self.act_ai_menu_canonical.setText(self._tr("lm_menu_generate_canonical"))
    self.act_ai_menu_canonical_graph.setText(self._tr("lm_menu_show_canonical_graph"))
    self.act_ai_menu_canonical_load.setText(self._tr("lm_menu_load_canonical_graph"))
    try:
        _bk_lm_update_dropdown_state(self)
    except Exception:
        pass
_BK_CANONICAL_PREV_RETRANSLATE_DROPDOWN = _bk_lm_retranslate_dropdown if "_bk_lm_retranslate_dropdown" in globals() else None
def _bk_lm_retranslate_dropdown(self):
    if _BK_CANONICAL_PREV_RETRANSLATE_DROPDOWN is not None:
        try:
            _BK_CANONICAL_PREV_RETRANSLATE_DROPDOWN(self)
        except Exception:
            pass
    try:
        _bk_lm_install_dropdown_menu(self)
    except Exception:
        pass
    if hasattr(self, "act_ai_menu_canonical"):
        self.act_ai_menu_canonical.setText(self._tr("lm_menu_generate_canonical"))
    if hasattr(self, "act_ai_menu_canonical_graph"):
        self.act_ai_menu_canonical_graph.setText(self._tr("lm_menu_show_canonical_graph"))
    if hasattr(self, "act_ai_menu_canonical_load"):
        self.act_ai_menu_canonical_load.setText(self._tr("lm_menu_load_canonical_graph"))
def _bk_canonical_init(self, *args, **kwargs):
    self._bk_canonical_by_path = getattr(self, "_bk_canonical_by_path", {}) or {}
    self._bk_last_canonical_json = getattr(self, "_bk_last_canonical_json", None)
    self._bk_last_canonical_path = getattr(self, "_bk_last_canonical_path", "")
    self._bk_last_canonical_graph_dialog = None
    try:
        _bk_lm_install_dropdown_menu(self)
    except Exception:
        pass
def _bk_canonical_retranslate(self, *args, **kwargs):
    try:
        _bk_lm_retranslate_dropdown(self)
    except Exception:
        pass
register_init_delta(_bk_canonical_init)
register_retranslate_delta(_bk_canonical_retranslate)
MainWindow._bk_lm_generate_canonical_json = _bk_lm_generate_canonical_json
MainWindow._bk_lm_show_current_canonical_graph = _bk_lm_show_current_canonical_graph
MainWindow._bk_lm_load_canonical_graph_json = _bk_lm_load_canonical_graph_json
MainWindow._bk_lm_show_canonical_graph_dialog = _bk_lm_show_canonical_graph_dialog
__all__ = [
    '_BK_CANONICAL_PREV_DONE',
    '_BK_CANONICAL_PREV_INSTALL_DROPDOWN',
    '_BK_CANONICAL_PREV_RETRANSLATE_DROPDOWN',
    '_BK_CANONICAL_PREV_SCHEMA_LABEL',
    '_BK_CANONICAL_PREV_UPDATE_DROPDOWN_STATE',
    '_BK_CANONICAL_PREV_WORKER_RUN',
    '_bk_canonical_init',
    '_bk_canonical_retranslate',
    '_bk_canonical_worker_run',
    '_bk_ensure_structured_json_prompt_keys',
    '_bk_json_schema_kind_label',
    '_bk_lm_generate_canonical_json',
    '_bk_lm_load_canonical_graph_json',
    '_bk_lm_install_dropdown_menu',
    '_bk_lm_on_local_json_done',
    '_bk_lm_retranslate_dropdown',
    '_bk_lm_show_canonical_graph_dialog',
    '_bk_lm_show_current_canonical_graph',
    '_bk_lm_update_dropdown_state',
]
register_globals('bk', globals(), __all__)
