from ._module_loader import load_split_module as __load_canonical_graph_dialog_parts

__load_canonical_graph_dialog_parts(__file__, globals(), 'canonical_graph_dialog_parts')
del __load_canonical_graph_dialog_parts

class BKCanonicalGraphDialog(
    BKCanonicalGraphDialogSetupMixin,
    BKCanonicalGraphDialogUiTablesMixin,
    BKCanonicalGraphDialogLayoutRenderMixin,
    BKCanonicalGraphDialogSelectionSaveMixin,
    QDialog,
):
    """Dialogklasse aus semantisch getrennten Graph-View-Mixins."""
    pass

try:
    del BKCanonicalGraphDialogSetupMixin
    del BKCanonicalGraphDialogUiTablesMixin
    del BKCanonicalGraphDialogLayoutRenderMixin
    del BKCanonicalGraphDialogSelectionSaveMixin
except NameError:
    pass
