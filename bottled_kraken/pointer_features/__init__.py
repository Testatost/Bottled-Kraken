from bottled_kraken.module_registry import register_globals, seed_from_module, synchronize
from bottled_kraken import common as _common
from bottled_kraken import ui_components as _ui_components
from bottled_kraken import workers as _workers
from bottled_kraken import dialogs as _dialogs
from bottled_kraken import image_edit as _image_edit
for _base_module in (_common, _ui_components, _workers, _dialogs, _image_edit):
    seed_from_module("ptr", _base_module)
def _absorb(module):
    names = [name for name in vars(module) if not name.startswith("__")]
    register_globals("ptr", vars(module), names)
    for name in names:
        globals()[name] = getattr(module, name)
    return names
__all__ = []
from bottled_kraken.pointer_features import dialogs_and_workers as _dialogs_and_workers
__all__.extend(_absorb(_dialogs_and_workers))
from bottled_kraken.pointer_features import ai_tools_dialog as _ai_tools_dialog
__all__.extend(_absorb(_ai_tools_dialog))
from bottled_kraken.pointer_features import merge_and_remote_chat as _merge_and_remote_chat
__all__.extend(_absorb(_merge_and_remote_chat))
from bottled_kraken.pointer_features import ai_generation_and_feature_actions as _ai_generation_and_feature_actions
__all__.extend(_absorb(_ai_generation_and_feature_actions))
from bottled_kraken.pointer_features import batch_hooks_and_mainwindow_wrappers as _batch_hooks_and_mainwindow_wrappers
__all__.extend(_absorb(_batch_hooks_and_mainwindow_wrappers))
from bottled_kraken.pointer_features import postgres_and_followup_ui_runtime_hooks_1 as _postgres_and_followup_ui_runtime_hooks_1
__all__.extend(_absorb(_postgres_and_followup_ui_runtime_hooks_1))
from bottled_kraken.pointer_features import postgres_and_followup_ui_runtime_hooks_2 as _postgres_and_followup_ui_runtime_hooks_2
__all__.extend(_absorb(_postgres_and_followup_ui_runtime_hooks_2))
from bottled_kraken.pointer_features import dialog_runtime_hooks as _dialog_runtime_hooks
__all__.extend(_absorb(_dialog_runtime_hooks))
from bottled_kraken.pointer_features import dialog_window_hooks as _dialog_window_hooks
__all__.extend(_absorb(_dialog_window_hooks))
from bottled_kraken.pointer_features import local_person_parsing_and_postgres as _local_person_parsing_and_postgres
__all__.extend(_absorb(_local_person_parsing_and_postgres))
from bottled_kraken.pointer_features import storage_exports_and_multi_ocr as _storage_exports_and_multi_ocr
__all__.extend(_absorb(_storage_exports_and_multi_ocr))
from bottled_kraken.pointer_features import bottom_toolbar_layout as _bottom_toolbar_layout
__all__.extend(_absorb(_bottom_toolbar_layout))
from bottled_kraken.pointer_features import multi_ocr_result_tabs as _multi_ocr_result_tabs
__all__.extend(_absorb(_multi_ocr_result_tabs))
from bottled_kraken.pointer_features import multi_ocr_dialog_worker_tabs as _multi_ocr_dialog_worker_tabs
__all__.extend(_absorb(_multi_ocr_dialog_worker_tabs))
from bottled_kraken.pointer_features import multi_ocr_variant_help_dialog as _multi_ocr_variant_help_dialog
__all__.extend(_absorb(_multi_ocr_variant_help_dialog))
from bottled_kraken.pointer_features import multi_ocr_start_variants as _multi_ocr_start_variants
__all__.extend(_absorb(_multi_ocr_start_variants))
from bottled_kraken.pointer_features import ocr_variant_storage as _ocr_variant_storage
__all__.extend(_absorb(_ocr_variant_storage))
from bottled_kraken.pointer_features import ocr_variant_state as _ocr_variant_state
__all__.extend(_absorb(_ocr_variant_state))
from bottled_kraken.pointer_features import ocr_tab_state_data as _ocr_tab_state_data
__all__.extend(_absorb(_ocr_tab_state_data))
from bottled_kraken.pointer_features import ocr_tab_state_controller as _ocr_tab_state_controller
__all__.extend(_absorb(_ocr_tab_state_controller))
__all__ = sorted(set(__all__))
synchronize("ptr")
