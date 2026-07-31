"""Zentrale Verwaltung der Seitenausrichtung (Hoch-/Querformat) fuer Exporte.

Der Benutzer waehlt die Ausrichtung im Export-Darstellungsdialog. Die Wahl
wird hier modulweit hinterlegt, zusaetzlich am Hauptfenster gespeichert und
in den QSettings persistiert. Writer, die kein Fensterobjekt erhalten
(z. B. die raeumlichen ODT-/DOCX-Writer in export_layout.py), lesen den
modulweiten Zustand; Writer mit Fensterobjekt bevorzugen dessen Attribut
bzw. dessen QSettings.

Werte: "auto" (bisheriges automatisches Verhalten), "portrait", "landscape".
"""

_BK_EXPORT_ORIENTATION = None  # zuletzt gewaehlte Ausrichtung (Prozess-Laufzeit)

_VALID = {"auto", "portrait", "landscape"}

SETTINGS_KEY = "export/page_orientation"


def bk_normalize_orientation(value) -> str:
    text = str(value or "").strip().lower()
    if text in _VALID:
        return text
    if text in {"hoch", "hochformat", "p"}:
        return "portrait"
    if text in {"quer", "querformat", "l"}:
        return "landscape"
    return "auto"


def bk_set_export_orientation(value, window=None) -> str:
    """Ausrichtung setzen: Laufzeit-Global, Fensterattribut und QSettings."""
    global _BK_EXPORT_ORIENTATION
    normalized = bk_normalize_orientation(value)
    _BK_EXPORT_ORIENTATION = normalized
    if window is not None:
        try:
            window._bk_export_page_orientation = normalized
        except Exception:
            pass
        try:
            settings = getattr(window, "settings", None)
            if settings is not None:
                settings.setValue(SETTINGS_KEY, normalized)
                settings.sync()
        except Exception:
            pass
    return normalized


def bk_get_export_orientation(window=None) -> str:
    """Aktive Ausrichtung ermitteln (Fenster > QSettings > Laufzeit > auto)."""
    global _BK_EXPORT_ORIENTATION
    if window is not None:
        value = getattr(window, "_bk_export_page_orientation", None)
        if value:
            return bk_normalize_orientation(value)
        try:
            settings = getattr(window, "settings", None)
            if settings is not None:
                stored = settings.value(SETTINGS_KEY, "", str)
                if stored:
                    normalized = bk_normalize_orientation(stored)
                    _BK_EXPORT_ORIENTATION = normalized
                    return normalized
        except Exception:
            pass
    if _BK_EXPORT_ORIENTATION:
        return _BK_EXPORT_ORIENTATION
    return "auto"


def bk_resolve_landscape(default_landscape, window=None) -> bool:
    """True, wenn Querformat verwendet werden soll.

    Bei "auto" bleibt das bisherige automatische Verhalten des jeweiligen
    Writers erhalten (default_landscape).
    """
    orientation = bk_get_export_orientation(window)
    if orientation == "landscape":
        return True
    if orientation == "portrait":
        return False
    return bool(default_landscape)


def bk_resolve_portrait(default_portrait, window=None) -> bool:
    return not bk_resolve_landscape(not bool(default_portrait), window)


def bk_page_size_cm(default_landscape, window=None):
    """(Breite, Hoehe) in cm fuer DIN A4 in der aufgeloesten Ausrichtung."""
    if bk_resolve_landscape(default_landscape, window):
        return 29.7, 21.0
    return 21.0, 29.7


def bk_page_size_inches(default_landscape, window=None):
    """(Breite, Hoehe) in Zoll fuer DIN A4 in der aufgeloesten Ausrichtung."""
    if bk_resolve_landscape(default_landscape, window):
        return 11.69, 8.27
    return 8.27, 11.69


def bk_xlsx_page_setup_xml(default_landscape, window=None) -> str:
    orientation = "landscape" if bk_resolve_landscape(default_landscape, window) else "portrait"
    return '<pageSetup paperSize="9" orientation="%s" fitToWidth="1" fitToHeight="0"/>' % orientation


def bk_odf_orientation_name(default_landscape, window=None) -> str:
    return "landscape" if bk_resolve_landscape(default_landscape, window) else "portrait"
