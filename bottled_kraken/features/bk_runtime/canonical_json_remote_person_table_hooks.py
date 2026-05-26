"""Canonical-JSON- und Graph-Ansicht für lokale LM-Workflows.

Diese Erweiterung integriert den Canonical-JSON/Graph-View-Ansatz aus dem
Kraken-OCR-Tool in Bottled Kraken, ohne externe Graph-Datenbank vorauszusetzen.
"""

from .shared import *

from .ui_components import *
from .workers import *
from .dialogs import *
from .image_edit import *
from .main_window import MainWindow
from .ptr_features import *

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

def _bk_ptr_dialog_generate_remote_canonical(self):
    try:
        source_text = _bk_ptr_dialog_collect_source_for_canonical(self)
        if not source_text:
            QMessageBox.warning(self, _ptr_ui_tr(self, "warn_title"), _ptr_ui_tr(self, "ptr_canonical_no_text"))
            return False
        cfg = self.get_config()
        self._set_busy(True)
        self.progress_label.setText(_ptr_ui_tr(self, "ptr_ai_running_canonical"))
        self.progress_bar.setRange(0, 0)
        QApplication.processEvents()
        owner = _bk_owner_for_prompt_settings(self)
        system_prompt, user_prompt = _bk_remote_canonical_prompt(source_text, lambda k, *a: _ptr_ui_tr(self, k, *a), owner=owner)
        max_tokens = _bk_canonical_token_limit(owner, 12000)
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        try:
            raw = _ptr_remote_chat_completion(
                cfg,
                messages,
                expect_json=True,
                max_tokens=max_tokens,
            )
            content = _ptr_extract_content_from_chat_response(raw)
        except Exception:
            # Some OpenRouter/free models reject response_format=json_object or return a non-standard
            # payload without choices. Retry without response_format and with a shorter JSON-only prompt.
            retry_messages = [
                {"role": "system", "content": "Return JSON only. The response must be one parseable JSON object."},
                {"role": "user", "content": user_prompt[:22000]},
            ]
            try:
                raw = _ptr_remote_chat_completion(
                    cfg,
                    retry_messages,
                    expect_json=False,
                    max_tokens=max_tokens,
                )
                content = _ptr_extract_content_from_chat_response(raw)
            except Exception as retry_exc:
                raise RuntimeError(_ptr_ui_tr(self, "ptr_canonical_remote_failed", retry_exc)) from retry_exc
        try:
            data = _ptr_extract_json_object(content)
            canonical = _bk_prepare_canonical_json(data, source_text)
        except Exception as parse_exc:
            raise RuntimeError(_ptr_ui_tr(self, "ptr_canonical_remote_invalid_json", parse_exc)) from parse_exc
        self._bk_remote_canonical_json = canonical
        self.result_output_edit.setPlainText(json.dumps(canonical, ensure_ascii=False, indent=2))
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_label.setText(_ptr_ui_tr(self, "ptr_ai_canonical_ready"))
        return True
    except Exception as exc:
        QMessageBox.warning(self, _ptr_ui_tr(self, "warn_title"), str(exc))
        return False
    finally:
        try:
            self._set_busy(False)
        except Exception:
            pass

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
        dlg.exec()
    except Exception as exc:
        QMessageBox.warning(self, _ptr_ui_tr(self, "warn_title"), str(exc))

_BK_CANONICAL_PREV_PTR_INIT = PtrAIToolsDialog.__init__ if "PtrAIToolsDialog" in globals() else None

_BK_CANONICAL_PREV_PTR_SET_BUSY = PtrAIToolsDialog._set_busy if "PtrAIToolsDialog" in globals() and hasattr(PtrAIToolsDialog, "_set_busy") else None

def _bk_ptr_dialog_generate_and_show_remote_canonical(self):
    if _bk_ptr_dialog_generate_remote_canonical(self):
        try:
            _bk_ptr_dialog_show_remote_canonical_graph(self)
        except Exception as exc:
            QMessageBox.warning(self, _ptr_ui_tr(self, "warn_title"), str(exc))

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
    except Exception:
        pass

def _bk_ptr_dialog_set_busy_with_canonical(self, busy: bool):
    if _BK_CANONICAL_PREV_PTR_SET_BUSY is not None:
        _BK_CANONICAL_PREV_PTR_SET_BUSY(self, busy)
    for _attr in ("graph_display_btn", "canonical_json_btn", "canonical_graph_btn"):
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
    if _BK_CANONICAL_PREV_PTR_SET_BUSY is not None:
        PtrAIToolsDialog._set_busy = _bk_ptr_dialog_set_busy_with_canonical
