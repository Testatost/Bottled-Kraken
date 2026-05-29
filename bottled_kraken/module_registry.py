_REGISTRIES = {}
def _registry(name):
    return _REGISTRIES.setdefault(name, {"symbols": {}, "modules": []})
def seed_globals(group, namespace):
    namespace.update(_registry(group)["symbols"])
def register_globals(group, namespace, names):
    reg = _registry(group)
    symbols = reg["symbols"]
    for name in names:
        if name in namespace:
            symbols[name] = namespace[name]
    reg["modules"].append(namespace)
def seed_from_module(group, module):
    symbols = _registry(group)["symbols"]
    names = getattr(module, "__all__", None)
    if names is None:
        names = [name for name in vars(module) if not name.startswith("__")]
    for name in names:
        if hasattr(module, name):
            symbols[name] = getattr(module, name)
def synchronize(group):
    reg = _registry(group)
    symbols = reg["symbols"]
    for namespace in reg["modules"]:
        namespace.update(symbols)
