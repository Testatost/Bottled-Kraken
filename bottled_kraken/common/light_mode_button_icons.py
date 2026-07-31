from bottled_kraken.module_registry import register_globals, seed_globals
seed_globals('shared', globals())

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QAbstractButton, QDialogButtonBox, QWidget


def _bk_widget_theme_is_dark(widget) -> bool:
    current = widget
    while current is not None:
        try:
            fn = getattr(current, "_is_current_theme_dark", None)
            if callable(fn):
                return bool(fn())
        except Exception:
            pass
        try:
            value = getattr(current, "_current_theme_is_dark", None)
            if value is not None:
                return bool(value)
        except Exception:
            pass
        try:
            theme = getattr(current, "current_theme", None)
            if theme is not None:
                return str(theme).strip().lower() == "dark"
        except Exception:
            pass
        current = current.parentWidget() if hasattr(current, "parentWidget") else None
    try:
        pal = widget.palette()
        return pal.color(pal.Window).lightness() < 128
    except Exception:
        return False


def _bk_target_icon_color(widget) -> QColor:
    return QColor("#ffffff") if _bk_widget_theme_is_dark(widget) else QColor("#000000")


def _bk_icon_analysis(icon: QIcon, size: QSize):
    pix = icon.pixmap(size)
    if pix.isNull():
        return {
            "coverage": 0.0,
            "mean_lum": 0.0,
            "colorfulness": 0.0,
            "pixmap": pix,
        }
    img = pix.toImage()
    w, h = img.width(), img.height()
    if w <= 0 or h <= 0:
        return {
            "coverage": 0.0,
            "mean_lum": 0.0,
            "colorfulness": 0.0,
            "pixmap": pix,
        }
    opaque = 0
    lum_sum = 0.0
    color_sum = 0.0
    samples = 0
    step = max(1, min(w, h) // 24)
    for y in range(0, h, step):
        for x in range(0, w, step):
            samples += 1
            c = img.pixelColor(x, y)
            if c.alpha() <= 40:
                continue
            opaque += 1
            lum_sum += (0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()) / 255.0
            color_sum += (abs(c.red() - c.green()) + abs(c.green() - c.blue()) + abs(c.blue() - c.red())) / (3.0 * 255.0)
    if samples == 0 or opaque == 0:
        return {
            "coverage": 0.0,
            "mean_lum": 0.0,
            "colorfulness": 0.0,
            "pixmap": pix,
        }
    return {
        "coverage": opaque / samples,
        "mean_lum": lum_sum / opaque,
        "colorfulness": color_sum / opaque,
        "pixmap": pix,
    }


def _bk_tint_icon_pixmap(src: QPixmap, color: QColor) -> QIcon:
    if src.isNull():
        return QIcon()
    tinted = QPixmap(src.size())
    tinted.fill(Qt.transparent)
    painter = QPainter(tinted)
    painter.drawPixmap(0, 0, src)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(tinted.rect(), color)
    painter.end()
    return QIcon(tinted)


def _bk_auto_tint_icon_for_widget(icon: QIcon, widget, size: QSize | None = None) -> QIcon:
    if icon is None or icon.isNull() or widget is None:
        return icon
    if size is None or not size.isValid() or size.isEmpty():
        try:
            size = widget.iconSize()
        except Exception:
            size = QSize(20, 20)
    if not size.isValid() or size.isEmpty():
        size = QSize(20, 20)
    stats = _bk_icon_analysis(icon, size)
    coverage = stats["coverage"]
    mean_lum = stats["mean_lum"]
    colorfulness = stats["colorfulness"]
    if coverage < 0.02:
        return icon
    # Bunte / individuell gestaltete Symbole beibehalten.
    if colorfulness > 0.10:
        return icon
    # Fast vollflaechige Kacheln / Piktogrammplatten nicht zwangsweise toenen,
    # sonst koennen schwarze Quadrate entstehen.
    if coverage > 0.92:
        return icon
    is_dark = _bk_widget_theme_is_dark(widget)
    mismatched = (mean_lum > 0.72 and not is_dark) or (mean_lum < 0.28 and is_dark)
    if not mismatched:
        return icon
    return _bk_tint_icon_pixmap(stats["pixmap"], _bk_target_icon_color(widget))


def _bk_refresh_widget_button_icons(widget, include_actions: bool = False) -> None:
    if widget is None or not hasattr(widget, "findChildren"):
        return
    try:
        buttons = widget.findChildren(QAbstractButton)
    except Exception:
        buttons = []
    for button in buttons:
        try:
            icon = button.icon()
            if icon is None or icon.isNull():
                continue
            size = button.iconSize() if hasattr(button, "iconSize") else QSize(20, 20)
            fixed = _bk_auto_tint_icon_for_widget(icon, button, size)
            if fixed is not None and not fixed.isNull():
                button.setIcon(fixed)
        except Exception:
            pass
    if include_actions:
        try:
            actions = widget.findChildren(QAction)
        except Exception:
            actions = []
        for action in actions:
            try:
                icon = action.icon()
                if icon is None or icon.isNull():
                    continue
                fixed = _bk_auto_tint_icon_for_widget(icon, widget, QSize(20, 20))
                if fixed is not None and not fixed.isNull():
                    action.setIcon(fixed)
            except Exception:
                pass


def _bk_refresh_dialog_button_box_icons(button_box: QDialogButtonBox) -> None:
    _bk_refresh_widget_button_icons(button_box, include_actions=False)


__all__ = [
    "_bk_auto_tint_icon_for_widget",
    "_bk_refresh_dialog_button_box_icons",
    "_bk_refresh_widget_button_icons",
    "_bk_target_icon_color",
    "_bk_widget_theme_is_dark",
]

register_globals('shared', globals(), __all__)
