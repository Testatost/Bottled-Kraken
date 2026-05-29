from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
BK_LM_SANITY_COMPAT_ONLY = True
__all__ = [
    'BK_LM_SANITY_COMPAT_ONLY',
]
register_globals('bk', globals(), __all__)
