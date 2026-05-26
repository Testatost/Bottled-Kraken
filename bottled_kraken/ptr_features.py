from ._module_loader import load_split_module as __load_split_module

__load_split_module(__file__, globals(), '_ptr_features_parts')
__all__ = [name for name in globals() if not name.startswith('__')]
del __load_split_module
