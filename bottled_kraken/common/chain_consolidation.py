"""
BK-OPT: Consolidated MainWindow hook chain.

Historically, ~20 files across `app_features` and `pointer_features` each
independently monkey-patched `MainWindow.__init__` and `MainWindow.retranslate_ui`
by saving the previous implementation, calling it, then adding their own logic,
and finally reassigning the class attribute to the new wrapper. Loaded in import
order, this built a 22-deep (resp. 17-deep) chain of nested closures.

This module replaces *only the wiring*, not the logic: every file's own delta
code is unchanged and still runs in exactly the same order as before (import
order = registration order). Instead of each file re-wrapping the previous
wrapper, each file now appends its delta function to an ordered list here, and
`install_consolidated_hooks()` builds ONE flat function per hook that calls the
true base implementation once, followed by every registered delta in order.

Behavioral guarantee: for any MainWindow instance, the sequence of code that
executes for `MainWindow()` / `window.retranslate_ui()` is byte-for-byte the
same sequence of statements as before this change - only the call stack is now
1 frame deep per hook instead of up to 22.
"""

_bk_init_deltas = []
_bk_retranslate_deltas = []
_bk_render_handlers = []

_bk_base_init = None
_bk_base_retranslate_ui = None
_bk_base_render_file = None

# Sentinel returned by a render handler to signal "format not handled here,
# try the next (older) handler". Replaces the legacy pattern of tail-calling
# a captured previous implementation (`return _BK_X_PREV_RENDER_FILE(...)`).
RENDER_NOT_HANDLED = object()


def capture_base_hooks(main_window_cls):
    """Must be called exactly once, immediately after MainWindow is defined in
    main_window.py and before any feature module has had a chance to patch it."""
    global _bk_base_init, _bk_base_retranslate_ui, _bk_base_render_file
    _bk_base_init = main_window_cls.__init__
    _bk_base_retranslate_ui = main_window_cls.retranslate_ui
    _bk_base_render_file = main_window_cls._render_file


def register_render_handler(fn):
    """Called by a feature module in place of the old
    `MainWindow._render_file = wrapper` line. Registration order equals the
    old assignment order; the dispatcher tries handlers newest-first, exactly
    mirroring the legacy chain (statically verified: the live legacy chain
    visited handlers in strictly decreasing assignment order)."""
    _bk_render_handlers.append(fn)
    return fn


def register_init_delta(fn):
    """Called by a feature module in place of the old
    `MainWindow.__init__ = wrapper` line. `fn` is the exact same delta code as
    before, just without the now-centralized call to the previous __init__."""
    _bk_init_deltas.append(fn)
    return fn


def register_retranslate_delta(fn):
    """Same as register_init_delta, for MainWindow.retranslate_ui."""
    _bk_retranslate_deltas.append(fn)
    return fn


def install_consolidated_hooks(main_window_cls):
    """Must be called exactly once, after all app_features/pointer_features
    modules have been imported (and have therefore finished registering their
    deltas). Installs the final, flattened __init__ / retranslate_ui onto
    MainWindow."""
    if _bk_base_init is None or _bk_base_retranslate_ui is None or _bk_base_render_file is None:
        raise RuntimeError(
            "capture_base_hooks() must run before install_consolidated_hooks()."
        )
    base_init = _bk_base_init
    base_retranslate_ui = _bk_base_retranslate_ui
    base_render_file = _bk_base_render_file
    init_deltas = tuple(_bk_init_deltas)
    retranslate_deltas = tuple(_bk_retranslate_deltas)
    render_handlers_newest_first = tuple(reversed(_bk_render_handlers))

    def _bk_consolidated_init(self, *args, **kwargs):
        base_init(self, *args, **kwargs)
        for delta in init_deltas:
            delta(self, *args, **kwargs)

    def _bk_consolidated_retranslate_ui(self, *args, **kwargs):
        base_retranslate_ui(self, *args, **kwargs)
        for delta in retranslate_deltas:
            delta(self, *args, **kwargs)

    def _bk_consolidated_render_file(self, path, fmt, item):
        for handler in render_handlers_newest_first:
            result = handler(self, path, fmt, item)
            if result is not RENDER_NOT_HANDLED:
                return result
        return base_render_file(self, path, fmt, item)

    main_window_cls.__init__ = _bk_consolidated_init
    main_window_cls.retranslate_ui = _bk_consolidated_retranslate_ui
    main_window_cls._render_file = _bk_consolidated_render_file
