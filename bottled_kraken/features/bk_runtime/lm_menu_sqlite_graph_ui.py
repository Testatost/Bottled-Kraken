"""UI-Fixes für LM-Menü, Overlay-Sichtbarkeit und SQLite-json-Export."""

def _bk_ui_scale_overlay_boxes(self):
    try:
        return self.resize_overlay_boxes_dialog()
    except Exception as exc:
        try:
            QMessageBox.warning(self, self._tr("warn_title"), str(exc))
        except Exception:
            pass

def _bk_ui_overlay_visible_rows_for_mode(self, recs):
    if not getattr(self, "show_overlay", True):
        return []
    mode = str(getattr(self, "overlay_display_mode", "all") or "all").lower()
    if mode in {"none", "off", "hidden"}:
        return []
    max_idx = len(recs) - 1
    if mode == "current":
        row = self.list_lines.currentRow() if hasattr(self, "list_lines") else -1
        if 0 <= row <= max_idx and getattr(recs[row], "bbox", None):
            return [int(getattr(recs[row], "idx", row))]
        return []
    if mode == "selected":
        rows = self._selected_line_rows() if hasattr(self, "_selected_line_rows") else []
        clean = []
        for row in rows:
            try:
                row = int(row)
            except Exception:
                continue
            if 0 <= row <= max_idx and getattr(recs[row], "bbox", None):
                clean.append(int(getattr(recs[row], "idx", row)))
        return sorted(set(clean))
    return [int(getattr(rv, "idx", i)) for i, rv in enumerate(recs or []) if getattr(rv, "bbox", None)]

def _bk_ui_set_overlay_display_mode(self, mode: str):
    mode = str(mode or "all").lower().strip()
    if mode not in {"none", "current", "selected", "all"}:
        mode = "all"
    self.overlay_display_mode = mode
    self.show_overlay = (mode != "none")
    if hasattr(self, "overlay_display_actions"):
        act = self.overlay_display_actions.get(mode)
        if act is not None and not act.isChecked():
            act.setChecked(True)
    try:
        self.settings.setValue("ui/overlay_display_mode", mode)
    except Exception:
        pass
    try:
        self._refresh_overlay_display()
    except Exception:
        pass
    try:
        if mode == "none":
            self.canvas.select_indices([], center=False)
            return
        rows = self._selected_line_rows() if hasattr(self, "_selected_line_rows") else []
        if rows:
            self.canvas.select_indices(rows, center=False)
        else:
            row = self.list_lines.currentRow() if hasattr(self, "list_lines") else -1
            if row >= 0:
                self.canvas.select_idx(row, center=False)
            else:
                self.canvas.select_indices([], center=False)
    except Exception:
        pass

def _bk_ui_rebuild_overlay_menu(self):
    menu = getattr(self, "overlay_menu", None)
    if menu is None:
        return
    try:
        menu.setTitle(self._tr("act_overlay_show"))
    except Exception:
        pass
    # Resize-Aktion aus dem Sichtbarkeitsmenü entfernen; sie liegt jetzt unter Bearbeiten.
    resize_action = getattr(self, "act_overlay_resize_boxes", None)
    if resize_action is not None:
        try:
            menu.removeAction(resize_action)
        except Exception:
            pass
    try:
        menu.clear()
    except Exception:
        pass
    group = QActionGroup(self)
    group.setExclusive(True)
    self.overlay_display_group = group
    self.overlay_display_actions = {}
    for key, mode in [
        ("overlay_mode_none", "none"),
        ("overlay_mode_current", "current"),
        ("overlay_mode_selected", "selected"),
        ("overlay_mode_all", "all"),
    ]:
        act = QAction(self._tr(key), self)
        act.setCheckable(True)
        if mode == str(getattr(self, "overlay_display_mode", "all") or "all").lower():
            act.setChecked(True)
        act.triggered.connect(lambda checked=False, m=mode: self._set_overlay_display_mode(m))
        group.addAction(act)
        menu.addAction(act)
        self.overlay_display_actions[mode] = act
    # Kompatibilitäts-Alias für ältere Runtime-Patches.
    self.act_overlay = menu.menuAction()

def _bk_ui_ensure_overlay_resize_in_edit_menu(self):
    edit_menu = getattr(self, "edit_menu", None)
    if edit_menu is None:
        return
    if not hasattr(self, "act_overlay_resize_boxes") or self.act_overlay_resize_boxes is None:
        self.act_overlay_resize_boxes = QAction(self._tr("overlay_resize_menu"), self)
        self.act_overlay_resize_boxes.triggered.connect(lambda checked=False: _bk_ui_scale_overlay_boxes(self))
    try:
        self.act_overlay_resize_boxes.setText(self._tr("overlay_resize_menu"))
    except Exception:
        pass
    actions = list(edit_menu.actions())
    if self.act_overlay_resize_boxes not in actions:
        edit_menu.addSeparator()
        edit_menu.addAction(self.act_overlay_resize_boxes)

def _bk_sqlite_json_payload_from_rows(self, task, rows):
    try:
        source_path = str(getattr(task, "path", "") or "")
        title = os.path.basename(source_path)
    except Exception:
        source_path = ""
        title = ""
    persons = []
    entries = []
    for row in rows or []:
        rid = str(row.get("id") or f"entry_{len(entries)+1}")
        persons.append({
            "id": rid,
            "full_name": row.get("full_name", ""),
            "first_name": row.get("first_name", ""),
            "last_name": row.get("last_name", ""),
        })
        entries.append({
            "id": rid,
            "person_id": rid,
            "age": row.get("age", ""),
            "event_date": row.get("event_date", ""),
            "event_place": row.get("event_place", ""),
            "source_excerpt": row.get("source_excerpt", ""),
        })
    return {
        "schema": "bottled_kraken.sqlite_json.v1",
        "database_hint": "sqlite",
        "tables": {
            "documents": [
                {"id": 1, "source_path": source_path, "title": title}
            ],
            "persons": persons,
            "entries": entries,
        },
    }

def _bk_export_sqlite_json(self):
    task = _bk_fix36_current_task(self) if "_bk_fix36_current_task" in globals() else None
    if not task or not getattr(task, "results", None):
        QMessageBox.information(self, _bk_fix36_tr(self, "info_title"), _bk_fix36_tr(self, "warn_no_ocr_results"))
        return
    try:
        _txt, _kr, _im, recs = task.results
        source_text = "\n".join(str(getattr(r, "text", "") or "") for r in recs)
    except Exception:
        source_text = ""
    rows = _bk_fix37_sqlite_rows_from_current_text(source_text) if "_bk_fix37_sqlite_rows_from_current_text" in globals() else []
    if not rows:
        QMessageBox.information(self, _bk_fix36_tr(self, "info_title"), _bk_fix36_tr(self, "warn_no_exportable_person_entries"))
        return
    payload = _bk_sqlite_json_payload_from_rows(self, task, rows)
    start_dir = getattr(self, "current_export_dir", "") or os.path.dirname(getattr(task, "path", "") or "") or os.getcwd()
    default_name = os.path.splitext(os.path.basename(getattr(task, "path", "bottled_kraken")))[0] + "_sqlite.json"
    path, _ = QFileDialog.getSaveFileName(
        self,
        _bk_fix36_tr(self, "dlg_sqlite_json_title", "SQLite-json speichern"),
        os.path.join(start_dir, default_name),
        _bk_fix36_tr(self, "filter_json_files", "JSON (*.json);;All Files (*)"),
    )
    if not path:
        return
    if not path.lower().endswith(".json"):
        path += ".json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    try:
        self.current_export_dir = os.path.dirname(path)
        self.status_bar.showMessage(_bk_fix36_tr(self, "msg_sqlite_export_done", "SQLite-json exportiert: {}").format(os.path.basename(path)), 5000)
    except Exception:
        pass

def _bk_ui_connect_action_once(action, slot):
    try:
        action.triggered.disconnect()
    except Exception:
        pass
    action.triggered.connect(lambda checked=False: slot())

def _bk_ui_ensure_lm_menu_order(self):
    if not hasattr(self, "btn_ai_revise_menu") or self.btn_ai_revise_menu is None:
        return
    menu = self.btn_ai_revise_menu
    # Fehlende Aktionen defensiv anlegen.
    if not hasattr(self, "act_ai_menu_sqlite_export"):
        self.act_ai_menu_sqlite_export = QAction(self._tr("lm_menu_generate_sqlite"), self)
    _bk_ui_connect_action_once(self.act_ai_menu_sqlite_export, lambda: _bk_export_sqlite_json(self))
    if not hasattr(self, "act_ai_menu_canonical"):
        self.act_ai_menu_canonical = QAction(self._tr("lm_menu_show_canonical_graph"), self)
    _bk_ui_connect_action_once(self.act_ai_menu_canonical, lambda: _bk_lm_generate_canonical_json(self))
    # Der frühere Nur-Anzeigen-Menüpunkt wird entfernt; Graph-Darstellung erzeugt jetzt neu und zeigt danach an.
    if hasattr(self, "act_ai_menu_canonical_graph"):
        try:
            menu.removeAction(self.act_ai_menu_canonical_graph)
        except Exception:
            pass
    label_pairs = [
        ("act_ai_menu_current_line", "lm_menu_current_line"),
        ("act_ai_menu_selected_lines", "lm_menu_selected_lines"),
        ("act_ai_menu_all_lines", "lm_menu_all_lines"),
        ("act_ai_menu_lm_ocr", "lm_menu_lm_ocr"),
        ("act_ai_menu_lm_ocr_boxes", "lm_menu_lm_ocr_boxes"),
        ("act_ai_menu_postgres", "lm_menu_generate_postgres"),
        ("act_ai_menu_neo4j", "lm_menu_generate_neo4j"),
        ("act_ai_menu_sqlite_export", "lm_menu_generate_sqlite"),
        ("act_ai_menu_canonical", "lm_menu_show_canonical_graph"),
        ("act_ai_menu_gedcom", "act_lm_generate_gedcom"),
    ]
    for attr, key in label_pairs:
        act = getattr(self, attr, None)
        if act is not None:
            try:
                act.setText(self._tr(key))
            except Exception:
                pass
    # Vorhandene Aktionen aus Menü entfernen und sauber neu sortieren.
    known = [getattr(self, attr, None) for attr, _key in label_pairs]
    known += [getattr(self, "act_ai_menu_canonical_graph", None)]
    for act in list(menu.actions()):
        if act in known or (act is not None and act.isSeparator()):
            try:
                menu.removeAction(act)
            except Exception:
                pass
    def _add(attr):
        act = getattr(self, attr, None)
        if act is not None:
            menu.addAction(act)
    _add("act_ai_menu_current_line")
    _add("act_ai_menu_selected_lines")
    _add("act_ai_menu_all_lines")
    menu.addSeparator()
    _add("act_ai_menu_lm_ocr")
    _add("act_ai_menu_lm_ocr_boxes")
    menu.addSeparator()
    _add("act_ai_menu_postgres")
    _add("act_ai_menu_neo4j")
    _add("act_ai_menu_sqlite_export")
    _add("act_ai_menu_canonical")
    _add("act_ai_menu_gedcom")
    try:
        _bk_lm_update_dropdown_state(self)
    except Exception:
        pass

_BK_UI_PREV_UPDATE_DROPDOWN_STATE = _bk_lm_update_dropdown_state if "_bk_lm_update_dropdown_state" in globals() else None

def _bk_lm_update_dropdown_state(self):
    if _BK_UI_PREV_UPDATE_DROPDOWN_STATE is not None:
        try:
            _BK_UI_PREV_UPDATE_DROPDOWN_STATE(self)
        except Exception:
            pass
    busy = _bk_lm_any_job_running(self) if "_bk_lm_any_job_running" in globals() else False
    task = _bk_lm_get_current_done_task(self) if "_bk_lm_get_current_done_task" in globals() else None
    if hasattr(self, "act_ai_menu_sqlite_export"):
        self.act_ai_menu_sqlite_export.setEnabled(bool(task) and not busy)
    if hasattr(self, "act_ai_menu_canonical"):
        self.act_ai_menu_canonical.setEnabled(bool(task) and not busy)

_BK_UI_PREV_MAINWINDOW_INIT = MainWindow.__init__

def _bk_ui_mainwindow_init(self, *args, **kwargs):
    _BK_UI_PREV_MAINWINDOW_INIT(self, *args, **kwargs)
    try:
        if str(getattr(self, "overlay_display_mode", "all") or "all").lower() not in {"none", "current", "selected", "all"}:
            self.overlay_display_mode = "all"
    except Exception:
        pass
    try:
        _bk_ui_rebuild_overlay_menu(self)
        _bk_ui_ensure_overlay_resize_in_edit_menu(self)
        _bk_ui_ensure_lm_menu_order(self)
    except Exception:
        pass

_BK_UI_PREV_RETRANSLATE = MainWindow.retranslate_ui

def _bk_ui_retranslate_ui(self, *args, **kwargs):
    _BK_UI_PREV_RETRANSLATE(self, *args, **kwargs)
    try:
        _bk_ui_rebuild_overlay_menu(self)
        _bk_ui_ensure_overlay_resize_in_edit_menu(self)
        _bk_ui_ensure_lm_menu_order(self)
    except Exception:
        pass

try:
    MainWindow._overlay_visible_rows_for_mode = _bk_ui_overlay_visible_rows_for_mode
    MainWindow._set_overlay_display_mode = _bk_ui_set_overlay_display_mode
    MainWindow._bk_export_sqlite_json = _bk_export_sqlite_json
    MainWindow.bk_export_sqlite_persons = _bk_export_sqlite_json
    MainWindow.__init__ = _bk_ui_mainwindow_init
    MainWindow.retranslate_ui = _bk_ui_retranslate_ui
except Exception:
    pass
