from bottled_kraken.module_registry import register_globals, synchronize
def _absorb(module):
    names = [name for name in vars(module) if not name.startswith("__")]
    register_globals("shared", vars(module), names)
    for name in names:
        globals()[name] = getattr(module, name)
    return names
__all__ = []
from bottled_kraken.common import imports_constants_and_paths as _imports_constants_and_paths
__all__.extend(_absorb(_imports_constants_and_paths))
from bottled_kraken.common import data_models_and_geometry as _data_models_and_geometry
__all__.extend(_absorb(_data_models_and_geometry))
from bottled_kraken.common import sorting_logging_and_json_tools as _sorting_logging_and_json_tools
__all__.extend(_absorb(_sorting_logging_and_json_tools))
from bottled_kraken.common import table_pdf_and_polygon_utils as _table_pdf_and_polygon_utils
__all__.extend(_absorb(_table_pdf_and_polygon_utils))
from bottled_kraken.common import theme_and_help_styles as _theme_and_help_styles
__all__.extend(_absorb(_theme_and_help_styles))
__all__ = sorted(set(__all__))
synchronize("shared")
