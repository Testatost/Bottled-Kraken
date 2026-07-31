from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
from bottled_kraken.common import (
    QTimer,
)
from bottled_kraken.main_window import MainWindow
def _bk_fix43_call_if_exists(obj, names, *args, **kwargs):
    for name in names:
        try:
            fn = getattr(obj, name, None)
            if callable(fn):
                try:
                    return fn(*args, **kwargs)
                except TypeError:
                    return fn()
        except Exception:
            pass
    return None
def _bk_fix43_reset_mainwindow_after_cancel(self):
    try:
        for flag in ("_ocr_running", "_is_ocr_running", "_busy", "_processing", "_cancel_requested", "_stop_requested"):
            try:
                setattr(self, flag, False)
            except Exception:
                pass
        for name in ("stop_button", "btn_stop", "btn_stop_ocr", "button_stop", "act_stop", "stop_action"):
            obj = getattr(self, name, None)
            if obj is not None:
                try:
                    obj.setEnabled(False)
                except Exception:
                    pass
        for name in ("start_button", "btn_start", "btn_start_ocr", "btn_ocr", "button_start_ocr", "act_start_ocr", "start_ocr_action"):
            obj = getattr(self, name, None)
            if obj is not None:
                try:
                    obj.setEnabled(True)
                except Exception:
                    pass
        for name in ("progress_bar", "progress", "queue_progress", "ocr_progress"):
            obj = getattr(self, name, None)
            if obj is not None:
                try:
                    obj.setRange(0, 100)
                    obj.setValue(0)
                except Exception:
                    pass
        try:
            self.status_bar.showMessage(_bk_fix36_tr(self, "msg_ocr_cancelled"), 5000)
        except Exception:
            pass
        try:
            self._update_actions_enabled()
        except Exception:
            pass
        try:
            self._update_ui_state()
        except Exception:
            pass
    except Exception:
        pass
def _bk_fix43_request_cancel_on_object(obj):
    if obj is None:
        return
    for flag in ("_cancelled", "cancelled", "_canceled", "canceled", "_stop_requested", "stop_requested", "_abort", "abort"):
        try:
            setattr(obj, flag, True)
        except Exception:
            pass
    _bk_fix43_call_if_exists(obj, ("cancel", "stop", "abort", "request_cancel", "request_stop", "requestInterruption"))
    try:
        if hasattr(obj, "thread") and callable(obj.thread):
            th = obj.thread()
            if th is not None and th is not obj:
                _bk_fix43_request_cancel_on_object(th)
    except Exception:
        pass
def _bk_fix43_force_finish_thread(obj):
    try:
        if obj is None:
            return
        running = False
        for name in ("isRunning", "is_running"):
            fn = getattr(obj, name, None)
            if callable(fn):
                try:
                    running = bool(fn())
                except Exception:
                    running = False
                break
        if running:
            _bk_fix43_call_if_exists(obj, ("quit",))
            _bk_fix43_call_if_exists(obj, ("wait",), 180)
            still = False
            try:
                still = bool(obj.isRunning())
            except Exception:
                still = False
            if still:
                _bk_fix43_call_if_exists(obj, ("terminate",))
                _bk_fix43_call_if_exists(obj, ("wait",), 180)
    except Exception:
        pass
def _bk_fix43_stop_everything_now(self):
    try:
        for flag in ("_cancel_requested", "_stop_requested", "_ocr_cancel_requested", "_ocr_stop_requested"):
            try:
                setattr(self, flag, True)
            except Exception:
                pass
        for attr in list(vars(self).keys()):
            low = attr.lower()
            if not any(part in low for part in ("worker", "thread", "ocr")):
                continue
            try:
                obj = getattr(self, attr)
            except Exception:
                continue
            if obj is None:
                continue
            if isinstance(obj, (str, int, float, bool, list, tuple, dict, set)):
                continue
            _bk_fix43_request_cancel_on_object(obj)
            try:
                QTimer.singleShot(1200, lambda o=obj: _bk_fix43_force_finish_thread(o))
            except Exception:
                pass
        try:
            QTimer.singleShot(80, lambda: _bk_fix43_reset_mainwindow_after_cancel(self))
            QTimer.singleShot(1600, lambda: _bk_fix43_reset_mainwindow_after_cancel(self))
        except Exception:
            _bk_fix43_reset_mainwindow_after_cancel(self)
    except Exception:
        _bk_fix43_reset_mainwindow_after_cancel(self)
def _bk_fix43_wrap_stop_method(method_name: str):
    old = getattr(MainWindow, method_name, None)
    if not callable(old) or getattr(old, "_bk_fix43_wrapped", False):
        return
    def wrapper(self, *args, **kwargs):
        _bk_fix43_stop_everything_now(self)
        result = None
        try:
            result = old(self, *args, **kwargs)
        except Exception as exc:
            try:
                print(f"FIX8.43 stop wrapper swallowed stop exception in {method_name}: {exc}")
            except Exception:
                pass
        _bk_fix43_stop_everything_now(self)
        return result
    wrapper._bk_fix43_wrapped = True
    setattr(MainWindow, method_name, wrapper)
for _bk_fix43_stop_name in (
    "stop_ocr", "_stop_ocr", "cancel_ocr", "_cancel_ocr", "stop_processing",
    "_stop_processing", "on_stop_clicked", "_on_stop_clicked", "request_stop",
    "_request_stop", "stop_current_worker", "_stop_current_worker",
):
    _bk_fix43_wrap_stop_method(_bk_fix43_stop_name)
__all__ = [
    '_bk_fix43_call_if_exists',
    '_bk_fix43_force_finish_thread',
    '_bk_fix43_request_cancel_on_object',
    '_bk_fix43_reset_mainwindow_after_cancel',
    '_bk_fix43_stop_everything_now',
    '_bk_fix43_stop_name',
    '_bk_fix43_wrap_stop_method',
]
register_globals('bk', globals(), __all__)
