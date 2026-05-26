"""Mixin-Methoden für den Bildbearbeitungsdialog."""
from ...shared import *
from ...dialogs import *
from ..common import ImageEditSeparator, ImageEditSettings, WhiteBorderDialog
from ..canvas import ImageEditCanvas
from PySide6.QtGui import QPainterPath

class ImageEditDialogToolButtonsMixin:
        def _enter_transform_or_apply(self):
            if hasattr(self, "canvas") and self.canvas.has_active_transform():
                self._apply_transform()
                return
            if hasattr(self, "canvas") and self.canvas.selection_rect is not None:
                self._toggle_free_transform(True)

        def _set_preview_tool_mode(self, mode: str):
            mode = "pan" if str(mode or "").lower() == "pan" else "select"
            if hasattr(self, "canvas"):
                self.canvas.set_tool_mode(mode)
            if hasattr(self, "btn_preview_select"):
                self.btn_preview_select.setChecked(mode == "select")
            if hasattr(self, "btn_preview_pan"):
                self.btn_preview_pan.setChecked(mode == "pan")
            if hasattr(self, "btn_select_tool"):
                self.btn_select_tool.setChecked(mode == "select")
            if hasattr(self, "btn_hand_tool"):
                self.btn_hand_tool.setChecked(mode == "pan")

        def _preview_tool_icon_color(self) -> QColor:
            return QColor("#f8fafc" if getattr(self, "_preview_tool_theme", "bright") == "dark" else "#111827")

        def _build_preview_tool_icon(self, tool: str) -> QIcon:
            ink = self._preview_tool_icon_color()
            pix = QPixmap(24, 24)
            pix.fill(Qt.transparent)

            painter = QPainter(pix)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setPen(QPen(ink, 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

            if tool == "pan":
                hand = QPainterPath()
                hand.moveTo(7.2, 16.2)
                hand.lineTo(6.2, 14.9)
                hand.cubicTo(5.4, 13.8, 6.7, 12.8, 7.8, 13.8)
                hand.lineTo(9.0, 15.0)
                hand.lineTo(9.0, 7.1)
                hand.cubicTo(9.0, 5.6, 11.0, 5.6, 11.0, 7.1)
                hand.lineTo(11.0, 12.0)
                hand.lineTo(11.0, 6.1)
                hand.cubicTo(11.0, 4.7, 13.0, 4.7, 13.0, 6.1)
                hand.lineTo(13.0, 12.1)
                hand.lineTo(13.0, 7.0)
                hand.cubicTo(13.0, 5.7, 15.0, 5.7, 15.0, 7.0)
                hand.lineTo(15.0, 12.3)
                hand.lineTo(15.0, 8.7)
                hand.cubicTo(15.0, 7.5, 16.9, 7.5, 16.9, 8.7)
                hand.lineTo(16.9, 14.0)
                hand.cubicTo(16.9, 18.3, 14.4, 20.5, 11.4, 20.5)
                hand.cubicTo(9.4, 20.5, 8.2, 18.3, 7.2, 16.2)
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(hand)
            elif tool == "transform":
                painter.drawRect(QRectF(5, 5, 14, 14))
                for px, py in ((5, 5), (19, 5), (19, 19), (5, 19)):
                    painter.fillRect(QRectF(px - 2, py - 2, 4, 4), ink)
            elif tool == "crop":
                painter.drawLine(7, 5, 7, 17)
                painter.drawLine(7, 17, 19, 17)
                painter.drawLine(11, 7, 19, 7)
                painter.drawLine(19, 7, 19, 19)
            elif tool == "erase":
                painter.drawLine(6, 16, 18, 8)
                painter.drawRect(QRectF(8, 8, 8, 8))
            elif tool == "split":
                painter.drawLine(12, 4, 12, 20)
                painter.drawLine(9, 6, 12, 3)
                painter.drawLine(15, 18, 12, 21)
            else:
                cursor = QPainterPath()
                cursor.moveTo(5.4, 3.4)
                cursor.lineTo(5.4, 19.1)
                cursor.lineTo(9.4, 14.8)
                cursor.lineTo(12.3, 21.0)
                cursor.lineTo(15.2, 19.7)
                cursor.lineTo(12.3, 13.6)
                cursor.lineTo(18.6, 13.6)
                cursor.closeSubpath()
                painter.setBrush(QBrush(ink))
                painter.drawPath(cursor)

            painter.end()
            icon = QIcon()
            icon.addPixmap(pix, QIcon.Normal, QIcon.Off)
            icon.addPixmap(pix, QIcon.Normal, QIcon.On)
            return icon

        def _preview_tool_button_qss(self) -> str:
            return """
                QToolButton {
                    border: 1px solid transparent;
                    border-radius: 6px;
                    padding: 2px;
                    background: transparent;
                }
                QToolButton:hover {
                    background: rgba(59, 130, 246, 0.16);
                    border: 1px solid rgba(59, 130, 246, 0.35);
                }
                QToolButton:checked {
                    background: rgba(59, 130, 246, 0.34);
                    border: 1px solid rgba(59, 130, 246, 0.95);
                }
                QToolButton:pressed {
                    background: rgba(59, 130, 246, 0.44);
                }
            """

        def _make_preview_tool_button(self, tool: str, tooltip_key: str) -> QToolButton:
            btn = QToolButton(self)
            btn.setText("")
            btn.setIcon(self._build_preview_tool_icon(tool))
            btn.setIconSize(QSize(22, 22))
            btn.setToolTip(self._tr(tooltip_key))
            btn.setCheckable(True)
            btn.setAutoRaise(False)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
            btn.setFixedSize(30, 28)
            btn.setStyleSheet(self._preview_tool_button_qss())
            return btn

        def _make_sidebar_button(self, tool: str, tooltip_text: str, checkable: bool = True) -> QToolButton:
            btn = QToolButton(self)
            btn.setCheckable(checkable)
            btn.setIcon(self._build_preview_tool_icon(tool))
            btn.setIconSize(QSize(24, 24))
            btn.setFixedSize(40, 40)
            btn.setToolTip(tooltip_text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
            btn.setStyleSheet(self._preview_tool_button_qss())
            return btn
