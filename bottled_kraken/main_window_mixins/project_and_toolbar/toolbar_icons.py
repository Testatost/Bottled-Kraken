"""Mixin für MainWindow: project persistence and queue selection."""
from ...shared import *
from ...ui_components import *
from ...workers import *
from ...dialogs import *
from ...image_edit import *
import math

class MainWindowToolbarIconFactoryMixin:
        def _normalize_toolbar_button_sizes(self):
            target_height = 34
            clear_width = 28
            # Alle Toolbar-QToolButtons angleichen; die zwei Vorschau-Werkzeugbuttons bleiben bewusst kompakt.
            for b in self.toolbar.findChildren(QToolButton):
                if b.objectName() in ("btn_preview_select", "btn_preview_pan"):
                    b.setFixedSize(target_height, target_height)
                    continue
                b.setMinimumHeight(target_height)
                b.setMaximumHeight(target_height)
                b.setMinimumWidth(0)
                b.setMaximumWidth(16777215)
            # Hauptbuttons angleichen
            for btn_name in (
                    "btn_rec_model",
                    "btn_seg_model",
                    "btn_ai_model",
                    "btn_theme_toggle",
                    "btn_lang_menu",
            ):
                btn = getattr(self, btn_name, None)
                if btn is not None:
                    btn.setMinimumHeight(target_height)
                    btn.setMaximumHeight(target_height)
                    btn.setMinimumWidth(0)
                    btn.setMaximumWidth(16777215)
            if hasattr(self, "btn_theme_toggle"):
                self.btn_theme_toggle.setFixedWidth(target_height + 10)
            if hasattr(self, "btn_lang_menu"):
                self.btn_lang_menu.setFixedWidth(target_height + 18)

        def _toolbar_custom_symbol_icon(self, kind: str, size: Optional[QSize] = None) -> QIcon:
            if size is None:
                if hasattr(self, "toolbar"):
                    size = self.toolbar.iconSize()
                else:
                    size = QSize(20, 20)

            px = max(16, int(size.width()))
            py = max(16, int(size.height()))

            pix = QPixmap(px, py)
            pix.fill(Qt.transparent)

            painter = QPainter(pix)
            painter.setRenderHint(QPainter.Antialiasing, True)

            if kind == "moon":
                painter.setPen(Qt.NoPen)

                moon_rect = QRectF(px * 0.10, py * 0.10, px * 0.80, py * 0.80)

                painter.setBrush(QColor("#808995"))
                painter.drawEllipse(moon_rect)

                painter.setBrush(QColor("#c3c8cf"))
                painter.drawEllipse(QRectF(px * 0.12, py * 0.11, px * 0.76, py * 0.76))

                painter.setBrush(QColor("#8d949f"))
                painter.drawEllipse(QRectF(px * 0.22, py * 0.20, px * 0.21, py * 0.16))
                painter.drawEllipse(QRectF(px * 0.47, py * 0.28, px * 0.17, py * 0.13))
                painter.drawEllipse(QRectF(px * 0.33, py * 0.48, px * 0.18, py * 0.12))
                painter.drawEllipse(QRectF(px * 0.57, py * 0.54, px * 0.09, py * 0.08))

                painter.setBrush(QColor("#a7afb9"))
                painter.drawEllipse(QRectF(px * 0.27, py * 0.27, px * 0.10, py * 0.08))
                painter.drawEllipse(QRectF(px * 0.53, py * 0.37, px * 0.08, py * 0.06))
                painter.drawEllipse(QRectF(px * 0.40, py * 0.58, px * 0.06, py * 0.05))

                painter.setBrush(QColor(255, 255, 255, 36))
                painter.drawEllipse(QRectF(px * 0.23, py * 0.18, px * 0.23, py * 0.10))
                painter.drawEllipse(QRectF(px * 0.50, py * 0.27, px * 0.11, py * 0.05))

            elif kind == "sun":
                center = QPointF(px / 2.0, py / 2.0)
                ray_pen = QPen(QColor("#d97706"), max(1.4, px * 0.07), Qt.SolidLine, Qt.RoundCap)
                painter.setPen(ray_pen)

                inner = px * 0.23
                outer = px * 0.40
                for i in range(8):
                    angle = math.radians(i * 45)
                    p1 = QPointF(center.x() + math.cos(angle) * inner, center.y() + math.sin(angle) * inner)
                    p2 = QPointF(center.x() + math.cos(angle) * outer, center.y() + math.sin(angle) * outer)
                    painter.drawLine(p1, p2)

                painter.setPen(QPen(QColor("#d97706"), max(1.1, px * 0.05)))
                painter.setBrush(QColor("#facc15"))
                painter.drawEllipse(QRectF(px * 0.25, py * 0.25, px * 0.50, py * 0.50))



            elif kind == "translate":

                is_bright = self.current_theme == "bright"

                outline = QColor("#000000") if is_bright else QColor("#f8fafc")

                accent = QColor("#000000") if is_bright else QColor("#93c5fd")

                front_fill = QColor("#ffffff") if is_bright else QColor("#0f172a")

                back_fill = QColor("#f3f4f6") if is_bright else QColor("#1e293b")

                card_front = QRectF(px * 0.12, py * 0.20, px * 0.46, py * 0.50)

                card_back = QRectF(px * 0.40, py * 0.30, px * 0.40, py * 0.42)

                radius = max(2.5, px * 0.08)

                pen = QPen(outline, max(1.1, px * 0.05))

                painter.setPen(pen)

                painter.setBrush(front_fill)

                painter.drawRoundedRect(card_front, radius, radius)

                painter.setPen(pen)

                painter.setBrush(back_fill)

                painter.drawRoundedRect(card_back, radius, radius)

                font_a = QFont()

                font_a.setBold(True)

                font_a.setPointSizeF(max(6.5, px * 0.30))

                painter.setFont(font_a)

                painter.setPen(outline)

                painter.drawText(card_front, Qt.AlignCenter, "A")

                font_b = QFont()

                font_b.setBold(True)

                font_b.setPointSizeF(max(5.5, px * 0.24))

                painter.setFont(font_b)

                painter.setPen(accent)

                painter.drawText(card_back, Qt.AlignCenter, "文")

                arrow_pen = QPen(outline, max(1.2, px * 0.055), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)

                painter.setPen(arrow_pen)

                y = py * 0.83

                x1 = px * 0.22

                x2 = px * 0.78

                painter.drawLine(QPointF(x1, y), QPointF(x2, y))

                head = px * 0.08

                painter.drawLine(QPointF(x2, y), QPointF(x2 - head, y - head * 0.6))

                painter.drawLine(QPointF(x2, y), QPointF(x2 - head, y + head * 0.6))

                painter.drawLine(QPointF(x1, y), QPointF(x1 + head, y - head * 0.6))

                painter.drawLine(QPointF(x1, y), QPointF(x1 + head, y + head * 0.6))

            else:
                painter.end()
                return QIcon()

            painter.end()
            return QIcon(pix)

        def _icon_fg_color(self) -> QColor:
            return QColor("#ffffff") if self.current_theme == "dark" else QColor("#000000")

        def _tinted_theme_or_standard_icon(
                self,
                theme_name: str,
                std_icon,
                size: Optional[QSize] = None
        ):
            icon = QIcon.fromTheme(theme_name)
            if icon.isNull():
                icon = self.style().standardIcon(std_icon)
            if icon.isNull():
                return icon
            if size is None:
                if hasattr(self, "toolbar"):
                    size = self.toolbar.iconSize()
                else:
                    size = QSize(16, 16)
            src = icon.pixmap(size)
            if src.isNull():
                return icon
            tinted = QPixmap(src.size())
            tinted.fill(Qt.transparent)
            painter = QPainter(tinted)
            painter.drawPixmap(0, 0, src)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(tinted.rect(), self._icon_fg_color())
            painter.end()
            return QIcon(tinted)

        def _themed_or_standard_icon(self, theme_name: str, std_icon):
            # Reine Button-Symbole themeabhängig einfärben:
            # Dunkelmodus = weiß, Hellmodus = schwarz.
            # Bildhafte Sondericons wie Sonne/Mond/Sprache laufen bewusst nicht hierüber,
            # sondern über _theme_toggle_icon() und _language_menu_icon().
            return self._tinted_theme_or_standard_icon(theme_name, std_icon)

        def _first_theme_icon(self, *theme_names: str) -> QIcon:
            for name in theme_names:
                if not name:
                    continue
                icon = QIcon.fromTheme(name)
                if not icon.isNull():
                    return icon
            return QIcon()

        def _theme_toggle_icon(self) -> QIcon:
            # Sonne soll genau so bleiben wie jetzt
            if self.current_theme == "dark":
                return self._toolbar_custom_symbol_icon("sun")

            # Im Hellmodus zuerst ein System-Mondsymbol von Fedora/KDE probieren
            icon = self._first_theme_icon(
                "weather-clear-night",
                "night-light",
                "moon",
                "weather-night"
            )
            if not icon.isNull():
                return icon

            # Fallback auf dein eigenes Mondsymbol
            return self._toolbar_custom_symbol_icon("moon")

        def _language_menu_icon(self) -> QIcon:
            return self._toolbar_custom_symbol_icon("translate")

        def _set_primary_toolbar_icons(self):
            if hasattr(self, "act_add"):
                self.act_add.setIcon(
                    self._themed_or_standard_icon("document-open", QStyle.SP_DialogOpenButton)
                )
            if hasattr(self, "act_project_load_toolbar"):
                self.act_project_load_toolbar.setIcon(
                    self._themed_or_standard_icon("document-open", QStyle.SP_DialogOpenButton)
                )
            if hasattr(self, "act_image_edit"):
                self.act_image_edit.setIcon(
                    self._tinted_theme_or_standard_icon("edit-cut", QStyle.SP_FileDialogDetailedView)
                )
            if hasattr(self, "act_play"):
                self.act_play.setIcon(
                    self._tinted_theme_or_standard_icon("media-playback-start", QStyle.SP_MediaPlay)
                )
            if hasattr(self, "act_stop"):
                self.act_stop.setIcon(
                    self._tinted_theme_or_standard_icon("media-playback-stop", QStyle.SP_MediaStop)
                )
            if hasattr(self, "btn_rec_model"):
                self.btn_rec_model.setIcon(
                    self._themed_or_standard_icon("document-open", QStyle.SP_DialogOpenButton)
                )
            if hasattr(self, "btn_seg_model"):
                self.btn_seg_model.setIcon(
                    self._themed_or_standard_icon("document-open", QStyle.SP_DialogOpenButton)
                )
