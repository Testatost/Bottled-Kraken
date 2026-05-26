"""Help dialog for Multi-OCR image preprocessing variants."""

def _ptr_multi_variant_help_detail_key(label_key: str) -> str:
    return str(label_key or "") + "_help"

def _ptr_multi_variant_help_html(obj) -> str:
    parts = [
        "<html><body>",
        "<p>" + html.escape(_ptr_dialog_tr(obj, "multi_ocr_variants_help_intro")) + "</p>",
        "<table cellspacing='0' cellpadding='6' width='100%'>",
    ]
    for _variant_key, label_key, _default_checked in _ptr_multi_variant_specs():
        label = html.escape(_ptr_dialog_tr(obj, label_key))
        detail = html.escape(_ptr_dialog_tr(obj, _ptr_multi_variant_help_detail_key(label_key)))
        parts.append("<tr><td valign='top'><b>" + label + "</b></td><td valign='top'>" + detail + "</td></tr>")
    parts.extend([
        "</table>",
        "<p>" + html.escape(_ptr_dialog_tr(obj, "multi_ocr_variants_help_footer")) + "</p>",
        "</body></html>",
    ])
    return "".join(parts)

def _ptr_multi_show_variant_help(obj) -> None:
    dlg = QDialog(obj)
    dlg.setWindowTitle(_ptr_dialog_tr(obj, "multi_ocr_variants_help_title"))
    dlg.resize(720, 520)
    layout = QVBoxLayout(dlg)
    browser = QTextBrowser(dlg)
    browser.setOpenExternalLinks(False)
    browser.setHtml(_ptr_multi_variant_help_html(obj))
    layout.addWidget(browser, 1)
    buttons = QDialogButtonBox(QDialogButtonBox.Close, dlg)
    try:
        buttons.button(QDialogButtonBox.Close).setText(_ptr_dialog_tr(obj, "btn_close"))
    except Exception:
        pass
    buttons.rejected.connect(dlg.reject)
    buttons.accepted.connect(dlg.accept)
    layout.addWidget(buttons)
    dlg.exec()
