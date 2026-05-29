try:
    from PySide6.QtCore import Qt, QSize, QTimer
    from PySide6.QtGui import QColor, QPainter, QPen
    from PySide6.QtWidgets import QWidget, QTabBar
except Exception:
    Qt = None
    QSize = None
    QTimer = None
    QColor = None
    QPainter = None
    QPen = None
    QWidget = object
    QTabBar = None
class OCRTabCloseWidget(QWidget):
    def __init__(self, tab_bar, on_delete, tooltip="", parent=None):
        super().__init__(parent or tab_bar)
        self._tab_bar = tab_bar
        self._on_delete = on_delete
        self._pressed = False
        self._hover = False
        try:
            self.setFixedSize(16, 16)
            self.setToolTip(str(tooltip or "Delete OCR tab"))
            self.setCursor(Qt.PointingHandCursor)
            self.setAttribute(Qt.WA_Hover, True)
            self.setFocusPolicy(Qt.NoFocus)
        except Exception:
            pass
    def sizeHint(self):
        return QSize(16, 16) if QSize is not None else super().sizeHint()
    def tab_index(self) -> int:
        try:
            for index in range(self._tab_bar.count()):
                if self._tab_bar.tabButton(index, QTabBar.RightSide) is self:
                    return index
        except Exception:
            pass
        try:
            index = self._tab_bar.tabAt(self.mapTo(self._tab_bar, self.rect().center()))
            if index >= 0:
                return index
        except Exception:
            pass
        return -1
    def enterEvent(self, event):
        self._hover = True
        self.update()
        try:
            super().enterEvent(event)
        except Exception:
            pass
    def leaveEvent(self, event):
        self._hover = False
        self._pressed = False
        self.update()
        try:
            super().leaveEvent(event)
        except Exception:
            pass
    def mousePressEvent(self, event):
        try:
            if Qt is None or event.button() == Qt.LeftButton:
                self._pressed = True
                self.update()
                event.accept()
                return
        except Exception:
            pass
        try:
            super().mousePressEvent(event)
        except Exception:
            pass
    def mouseReleaseEvent(self, event):
        was_pressed = self._pressed
        self._pressed = False
        self.update()
        try:
            inside = self.rect().contains(event.pos())
        except Exception:
            inside = True
        if was_pressed and inside:
            index = self.tab_index()
            try:
                if QTimer is not None:
                    QTimer.singleShot(0, lambda: self._on_delete(index))
                else:
                    self._on_delete(index)
            except Exception:
                pass
            try:
                event.accept()
            except Exception:
                pass
            return
        try:
            super().mouseReleaseEvent(event)
        except Exception:
            pass
    def paintEvent(self, event):
        if QPainter is None or QPen is None:
            return
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing, True)
            rect = self.rect().adjusted(2, 2, -2, -2)
            if self._pressed:
                painter.setBrush(QColor(185, 185, 185, 150))
            elif self._hover:
                painter.setBrush(QColor(215, 215, 215, 130))
            else:
                painter.setBrush(QColor(245, 245, 245, 80))
            painter.setPen(QPen(QColor(145, 145, 145), 1))
            painter.drawEllipse(rect)
            pen = QPen(QColor(25, 25, 25), 1.7)
            if Qt is not None:
                pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            pad = 5
            painter.drawLine(pad, pad, self.width() - pad - 1, self.height() - pad - 1)
            painter.drawLine(self.width() - pad - 1, pad, pad, self.height() - pad - 1)
        finally:
            painter.end()
