from ._module_loader import load_split_module as __load_split_module

__load_split_module(__file__, globals(), "_bk_features_parts")
del __load_split_module
