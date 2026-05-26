"""Mixin-Methoden für den Bildbearbeitungsdialog."""
from ...shared import *
from ...dialogs import *
from ..common import ImageEditSeparator, ImageEditSettings, WhiteBorderDialog, LiveValueDialog
from ..canvas import ImageEditCanvas

class ImageEditDialogFiltersRotationTransformMixin:
        def _toggle_gray(self, checked: bool):
            self.color_mode = "GRAY" if checked else "RGB"
            self._refresh_preview(reset_zoom=False)

        def _contrast_level_from_slider(self, value: int) -> float:
            return 1.0 + (max(0, min(100, int(value))) / 100.0) * 3.0

        def _set_contrast_slider_from_level(self, level: float):
            value = int(round(((max(1.0, min(4.0, float(level))) - 1.0) / 3.0) * 100.0))
            if hasattr(self, "contrast_slider"):
                self.contrast_slider.blockSignals(True)
                self.contrast_slider.setValue(max(0, min(100, value)))
                self.contrast_slider.blockSignals(False)

        def _update_contrast_slider_ui(self):
            level = max(1.0, min(4.0, float(getattr(self, "contrast_level", 2.2))))
            if hasattr(self, "lbl_contrast_strength"):
                self.lbl_contrast_strength.setText(f"{self._tr('image_edit_contrast')}: {level:.2f}×")
                self.lbl_contrast_strength.setEnabled(bool(getattr(self, "contrast_enabled", False)))
            if hasattr(self, "contrast_slider"):
                self.contrast_slider.setEnabled(bool(getattr(self, "contrast_enabled", False)))
                self.contrast_slider.setToolTip(f"{self._tr('image_edit_contrast')}: {level:.2f}×")
            if hasattr(self, "contrast_controls_widget"):
                self.contrast_controls_widget.setVisible(bool(getattr(self, "contrast_enabled", False)))

        def _on_contrast_slider_pressed(self):
            self._contrast_preview_pending = False

        def _schedule_contrast_preview(self):
            if not self.contrast_enabled:
                return
            self._contrast_preview_pending = True
            timer = getattr(self, "_contrast_preview_timer", None)
            if timer is not None:
                timer.start()
            else:
                self._apply_pending_contrast_preview()

        def _apply_pending_contrast_preview(self):
            if not getattr(self, "_contrast_preview_pending", False):
                return
            self._contrast_preview_pending = False
            if self.contrast_enabled:
                self._refresh_preview(reset_zoom=False)

        def _on_contrast_slider_released(self):
            timer = getattr(self, "_contrast_preview_timer", None)
            if timer is not None:
                timer.stop()
            self._contrast_preview_pending = True
            self._apply_pending_contrast_preview()

        def _on_contrast_slider_changed(self, value: int):
            self.contrast_level = self._contrast_level_from_slider(value)
            self._update_contrast_slider_ui()
            if self.contrast_enabled:
                self._schedule_contrast_preview()

        def _toggle_contrast(self, checked: bool):
            self.contrast_enabled = bool(checked)
            if self.contrast_enabled and hasattr(self, "contrast_slider"):
                self.contrast_level = self._contrast_level_from_slider(self.contrast_slider.value())
            timer = getattr(self, "_contrast_preview_timer", None)
            if timer is not None:
                timer.stop()
            self._contrast_preview_pending = False
            self._update_contrast_slider_ui()
            self._refresh_preview(reset_zoom=False)

        def _rotate_by(self, delta: float):
            self.rotation_angle = (self.rotation_angle + delta) % 360.0
            self.canvas.rotation_angle = float(self.rotation_angle)
            self.canvas.crop_rect = None
            self.canvas.separator = None
            self.canvas.cancel_free_transform()
            self.canvas.selection_rect = None
            self._refresh_preview(reset_zoom=False)
            self._history_push()

        def _reset_rotation(self):
            self.rotation_angle = 0.0
            self.canvas.rotation_angle = 0.0
            self.canvas.crop_rect = None
            self.canvas.separator = None
            self.canvas.cancel_free_transform()
            self.canvas.selection_rect = None
            self._refresh_preview(reset_zoom=False)
            self._history_push()

        def _flip_horizontal(self):
            self.canvas.cancel_free_transform()
            self.canvas.selection_rect = None
            self.flip_horizontal = not bool(getattr(self, "flip_horizontal", False))
            self._refresh_preview(reset_zoom=False)
            self._history_push()

        def _flip_vertical(self):
            self.canvas.cancel_free_transform()
            self.canvas.selection_rect = None
            self.flip_vertical = not bool(getattr(self, "flip_vertical", False))
            self._refresh_preview(reset_zoom=False)
            self._history_push()

        def _set_transform_mode(self, mode: str):
            mode = str(mode or "scale").lower()
            if mode not in ("scale", "rotate", "skew", "perspective", "warp"):
                mode = "scale"
            old_mode = str(getattr(self.canvas, "transform_mode", "scale") or "scale")

            # Alle freien Transformationsmodi arbeiten auf derselben aktuellen
            # Vierpunkt-Geometrie. Drehen wird nicht mehr als separater PIL-Rotate-
            # Zwischenzustand behandelt, sondern direkt in transform_quad geführt.
            # Dadurch bleiben Inhalt UND Auswahlrahmen beim Wechsel zwischen
            # Skalieren/Drehen/Neigen/Perspektive/Verkrümmen erhalten.
            if old_mode == "rotate" and mode != "rotate":
                self.canvas.transform_rotate_angle = 0.0

            if mode == "rotate":
                self.canvas.transform_rotate_angle = 0.0
                self.canvas._rotate_base_source_order = list(getattr(self.canvas, "transform_source_order", [0, 1, 2, 3]) or [0, 1, 2, 3])
                if old_mode == "warp" and hasattr(self.canvas, "_warp_grid_tuples"):
                    self.canvas._rotate_base_warp_grid = list(self.canvas._warp_grid_tuples())
                else:
                    self.canvas._rotate_base_warp_grid = None
            else:
                self.canvas._rotate_base_warp_grid = None
                self.canvas._rotate_base_source_order = None

            self.canvas.transform_mode = mode
            if mode == "warp" and self.canvas.transform_src_rect is not None:
                grid = getattr(self.canvas, "transform_warp_grid", None)
                if not grid or len(grid) not in (9, 25):
                    if hasattr(self.canvas, "_warp_grid_points_from_quad"):
                        self.canvas.transform_warp_grid = self.canvas._warp_grid_points_from_quad()
                    else:
                        self.canvas._warp_grid_points()
                elif len(grid) == 9 and hasattr(self.canvas, "_warp_grid_points"):
                    self.canvas._warp_grid_points()
            if mode != "warp":
                self.canvas.transform_warp_x = 0.0
                self.canvas.transform_warp_y = 0.0
            if hasattr(self, "lbl_transform_mode"):
                self.lbl_transform_mode.setText(self._tr(f"image_edit_transform_mode_{mode}"))
            self._sync_transform_mode_buttons()
            self.canvas.update()

        def _sync_transform_mode_buttons(self):
            active_transform = self.canvas.has_active_transform()
            if hasattr(self, "btn_transform"):
                self.btn_transform.blockSignals(True)
                self.btn_transform.setChecked(active_transform)
                self.btn_transform.blockSignals(False)
            if hasattr(self, "btn_crop_tool"):
                self.btn_crop_tool.blockSignals(True)
                self.btn_crop_tool.setChecked(bool(self.chk_crop.isChecked()))
                self.btn_crop_tool.blockSignals(False)
            if hasattr(self, "chk_selection"):
                self.chk_selection.blockSignals(True)
                self.chk_selection.setChecked(bool(getattr(self.canvas, "show_selection", False)))
                self.chk_selection.blockSignals(False)
            for attr, mode in (
                ("btn_tf_scale", "scale"),
                ("btn_tf_rotate", "rotate"),
                ("btn_tf_skew", "skew"),
                ("btn_tf_persp", "perspective"),
                ("btn_tf_warp", "warp"),
            ):
                btn = getattr(self, attr, None)
                if btn is not None:
                    btn.setEnabled(active_transform)
                    btn.blockSignals(True)
                    btn.setChecked(active_transform and self.canvas.transform_mode == mode)
                    btn.blockSignals(False)
            if hasattr(self, "btn_transform_apply"):
                self.btn_transform_apply.setEnabled(active_transform)
            if hasattr(self, "btn_transform_cancel"):
                self.btn_transform_cancel.setEnabled(active_transform)
            if hasattr(self, "lbl_transform_mode"):
                if active_transform:
                    self.lbl_transform_mode.setText(self._tr(f"image_edit_transform_mode_{self.canvas.transform_mode}"))
                else:
                    self.lbl_transform_mode.setText(self._tr("image_edit_transform_inactive"))

        def _toggle_free_transform(self, checked: bool):
            if checked:
                self.canvas.show_selection = True
                if self.canvas.selection_rect is None:
                    if hasattr(self, "btn_transform"):
                        self.btn_transform.blockSignals(True)
                        self.btn_transform.setChecked(False)
                        self.btn_transform.blockSignals(False)
                    self.canvas.setFocus()
                    return
                if self.canvas.start_free_transform():
                    self._set_transform_mode(self.canvas.transform_mode or "scale")
            else:
                self._cancel_transform()
                return
            self._sync_transform_mode_buttons()
            self.canvas.setFocus()

        def _apply_transform(self):
            if not self.canvas.has_active_transform():
                return

            # Sauberen Vorher-Zustand sichern:
            # ohne aktive Transformations-Overlay-Vorschau, aber mit unverändertem Bild.
            before_settings = self.get_settings()
            before_settings.free_transform_enabled = False
            before_settings.transform_src_norm = None
            before_settings.transform_dest_norm = None
            before_settings.transform_source_order = (0, 1, 2, 3)
            before_settings.transform_rotate_angle = 0.0
            before_settings.transform_warp_x = 0.0
            before_settings.transform_warp_y = 0.0
            before_settings.transform_warp_grid_norm = None
            before_settings.selection_enabled = False
            before_settings.selection_orig = None
            undo = getattr(self, "_history_undo", None)
            if undo is None:
                self._history_undo = []
                undo = self._history_undo
            undo.append({
                "settings": before_settings,
                "image": self.original_image.copy() if getattr(self, "original_image", None) is not None else None,
            })
            if len(undo) > 100:
                del undo[:-100]
            self._history_redo = []

            transformed_poly = self.canvas.transformed_selection_polygon()
            try:
                self.original_image = self._apply_free_transform_to_image(self.original_image.convert("RGB")).convert("RGB")
            except Exception:
                pass
            self.canvas.cancel_free_transform()
            if transformed_poly:
                self.canvas.selection_polygon = [QPointF(p) for p in transformed_poly]
                self.canvas.selection_rect = self.canvas._selection_rect_from_points(self.canvas.selection_polygon)
                # Preserve original drawn/created lines instead of collapsing to a rectangle.
                if len(self.canvas.selection_polygon) > 4:
                    self.canvas.selection_draw_mode = "freehand" if getattr(self.canvas, "_selection_polygon_before_transform", None) else self.canvas.selection_draw_mode
            else:
                self.canvas.selection_rect = None
                self.canvas.selection_polygon = None
            self.canvas.show_selection = True
            self._refresh_preview(reset_zoom=False)
            self._sync_transform_mode_buttons()

            # Nachher-Zustand sichern.
            self._history_push()
            self.canvas.setFocus()

        def _cancel_transform(self):
            previous = getattr(self.canvas, "_selection_before_transform", None)
            previous_poly = getattr(self.canvas, "_selection_polygon_before_transform", None)
            self.canvas.cancel_free_transform()
            if previous is not None:
                self.canvas.selection_rect = QRectF(previous)
                self.canvas.selection_polygon = [QPointF(p) for p in (previous_poly or [])] if previous_poly else None
                self.canvas.show_selection = True
                self.canvas._selection_before_transform = None
                self.canvas._selection_polygon_before_transform = None
            else:
                self.canvas.selection_rect = None
                self.canvas.selection_polygon = None
                self.canvas.show_selection = True
            self._sync_transform_mode_buttons()
            self.canvas.update()
            self.canvas.setFocus()

        def _clear_selection(self):
            self.canvas.cancel_free_transform()
            self.canvas.selection_rect = None
            self.canvas.selection_polygon = None
            self.canvas.show_selection = True
            if hasattr(self, "chk_selection"):
                self.chk_selection.blockSignals(True)
                self.chk_selection.setChecked(True)
                self.chk_selection.blockSignals(False)
            self._set_selection_draw_mode("rect")
            self._sync_transform_mode_buttons()
            self.canvas.update()
            self._history_push()

        def _transform_rotate_local(self, degrees: float):
            if not self.canvas.has_active_transform() or not self.canvas.transform_quad:
                return
            center = self.canvas._quad_center()
            rad = math.radians(float(degrees))
            cos_a = math.cos(rad)
            sin_a = math.sin(rad)
            rotated = []
            for pt in self.canvas.transform_quad:
                x = pt.x() - center.x()
                y = pt.y() - center.y()
                rotated.append(QPointF(center.x() + x * cos_a - y * sin_a, center.y() + x * sin_a + y * cos_a))
            self.canvas.transform_quad = rotated
            order = list(self.canvas.transform_source_order or [0, 1, 2, 3])
            steps = int(round(degrees / 90.0)) % 4
            if steps > 0:
                for _ in range(steps):
                    order = [order[3], order[0], order[1], order[2]]
            elif steps < 0:
                for _ in range(abs(steps)):
                    order = [order[1], order[2], order[3], order[0]]
            self.canvas.transform_source_order = order
            self.canvas._ensure_transform_inside()
            self.canvas.update(); self.canvas.changed.emit()

        def _transform_flip_local(self, axis: str):
            if not self.canvas.has_active_transform() or not self.canvas.transform_quad:
                return
            center = self.canvas._quad_center()
            flipped = []
            for pt in self.canvas.transform_quad:
                if axis == "h":
                    flipped.append(QPointF(2 * center.x() - pt.x(), pt.y()))
                else:
                    flipped.append(QPointF(pt.x(), 2 * center.y() - pt.y()))
            self.canvas.transform_quad = flipped
            order = list(self.canvas.transform_source_order or [0, 1, 2, 3])
            if axis == "h":
                order = [order[1], order[0], order[3], order[2]]
            else:
                order = [order[3], order[2], order[1], order[0]]
            self.canvas.transform_source_order = order
            self.canvas._ensure_transform_inside()
            self.canvas.update(); self.canvas.changed.emit()

        def _show_selection_context_menu(self, global_pos):
            menu = QMenu(self)
            act_transform = menu.addAction(self._tr("image_edit_menu_free_transform"))
            act_clear = menu.addAction(self._tr("image_edit_menu_deselect"))
            chosen = menu.exec(global_pos)
            if chosen == act_clear:
                self._clear_selection()
            elif chosen == act_transform:
                self._toggle_free_transform(True)

        def _show_crop_context_menu(self, global_pos):
            menu = QMenu(self)
            act_delete = menu.addAction(self._tr("image_edit_menu_deselect"))
            act_delete.setText(self._tr("image_edit_context_delete_crop_area"))
            chosen = menu.exec(global_pos)
            if chosen == act_delete:
                if self.canvas.delete_selected_crop():
                    self._history_push()

        def _show_transform_context_menu(self, global_pos):
            menu = QMenu(self)
            act_apply = menu.addAction(self._tr("image_edit_menu_transform_apply"))
            act_cancel = menu.addAction(self._tr("image_edit_menu_transform_cancel"))
            menu.addSeparator()
            act_scale = menu.addAction(self._tr("image_edit_transform_mode_scale"))
            act_rotate = menu.addAction(self._tr("image_edit_transform_mode_rotate"))
            act_skew = menu.addAction(self._tr("image_edit_transform_mode_skew"))
            act_persp = menu.addAction(self._tr("image_edit_transform_mode_perspective"))
            act_warp = menu.addAction(self._tr("image_edit_transform_mode_warp"))
            menu.addSeparator()
            act_rot_l = menu.addAction(self._tr("image_edit_menu_rotate_left"))
            act_rot_r = menu.addAction(self._tr("image_edit_menu_rotate_right"))
            act_flip_h = menu.addAction(self._tr("image_edit_menu_flip_h"))
            act_flip_v = menu.addAction(self._tr("image_edit_menu_flip_v"))
            chosen = menu.exec(global_pos)
            if chosen == act_apply:
                self._apply_transform()
            elif chosen == act_cancel:
                self._cancel_transform()
            elif chosen == act_scale:
                self._set_transform_mode("scale")
            elif chosen == act_rotate:
                self._set_transform_mode("rotate")
            elif chosen == act_skew:
                self._set_transform_mode("skew")
            elif chosen == act_persp:
                self._set_transform_mode("perspective")
            elif chosen == act_warp:
                self._set_transform_mode("warp")
            elif chosen == act_rot_l:
                self._transform_rotate_local(-90)
            elif chosen == act_rot_r:
                self._transform_rotate_local(90)
            elif chosen == act_flip_h:
                self._transform_flip_local("h")
            elif chosen == act_flip_v:
                self._transform_flip_local("v")
