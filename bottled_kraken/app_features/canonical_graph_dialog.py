from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('bk', globals())
class BKCanonicalGraphDialog(
    BKCanonicalGraphDialogSetupMixin,
    BKCanonicalGraphDialogUiTablesMixin,
    BKCanonicalGraphDialogLayoutRenderMixin,
    BKCanonicalGraphDialogSelectionSaveMixin,
    QDialog,
):
    pass
try:
    del BKCanonicalGraphDialogSetupMixin
    del BKCanonicalGraphDialogUiTablesMixin
    del BKCanonicalGraphDialogLayoutRenderMixin
    del BKCanonicalGraphDialogSelectionSaveMixin
except NameError:
    pass
__all__ = [
    'BKCanonicalGraphDialog',
]
register_globals('bk', globals(), __all__)
