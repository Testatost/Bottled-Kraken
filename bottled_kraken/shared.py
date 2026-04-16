from ._module_loader import load_split_module as __load_split_module

__load_split_module(__file__, globals(), "_shared_parts")
del __load_split_module
