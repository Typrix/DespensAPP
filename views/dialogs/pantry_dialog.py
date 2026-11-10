# -*- coding: utf-8 -*-
"""
Modales de Despensa para DespensAPP.
Controla adición de alimentos, umbrales mínimos, control de caducidad y detalle.
"""

from dataclasses import replace

from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty, StringProperty, NumericProperty
from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.pickers import MDModalDatePicker
from views.dialogs.base import BaseFormModal
from controllers.validators import (
    PANTRY_UNITS,
    NAME_MAX_LENGTH,
    QUANTITY_MAX,
    validate_pantry_form,
    validate_pantry_details,
    validate_quantity,
    expiration_warning,
    format_number,
    step_for_unit,
)

# Re-exportado para compatibilidad con código que lo importaba desde este módulo
__all__ = [
    "PANTRY_UNITS", "NAME_MAX_LENGTH", "QUANTITY_MAX", "validate_pantry_form",
    "AddPantryItemModal", "PantryItemDetailModal",
]


def _open_date_picker(on_date):
    """Abre el calendario de KivyMD y entrega la fecha elegida (AAAA-MM-DD) al callback."""
    date_picker = MDModalDatePicker()

    def on_ok(picker_instance):
        selected_dates = picker_instance.get_date()
        picker_instance.dismiss()
        if selected_dates:
            on_date(selected_dates[0].strftime("%Y-%m-%d"))

    def on_cancel(picker_instance):
        picker_instance.dismiss()

    date_picker.bind(on_ok=on_ok, on_cancel=on_cancel)
    date_picker.open()


class AddPantryItemModal(BaseFormModal):
    """Modal para ingresar un producto a la despensa con umbral numérico y fecha de vencimiento."""
    has_no_expiration = BooleanProperty(False)
    expiration_date_str = StringProperty("")
    selected_unit = StringProperty(PANTRY_UNITS[0])
    warning_text = StringProperty("")

    def __init__(self, callback_add, **kwargs):
        super().__init__(**kwargs)
        self.callback_add = callback_add
        self.unit_menu = None
        self.clear_error_on_input(
            self.ids.field_name.ids.text_input,
            self.ids.field_quantity.ids.text_input,
            self.ids.field_threshold.ids.text_input,
            self.ids.field_expiration_input,
        )
        # Avisa en vivo si la fecha escrita o elegida ya pasó
        self.ids.field_expiration_input.bind(
            text=lambda inst, val: setattr(self, "warning_text", expiration_warning(val))
        )

    def open_unit_menu(self, caller):
        """Despliega el menú con las unidades predefinidas bajo el campo de unidad."""
        if self.unit_menu is None:
            items = [
                {"text": unit, "on_release": lambda u=unit: self.set_unit(u)}
                for unit in PANTRY_UNITS
            ]
            # El menú se alinea con el recuadro completo del campo (texto + flecha)
            field_box = caller.parent
            self.unit_menu = MDDropdownMenu(
                caller=field_box,
                items=items,
                position="bottom",
                width=field_box.width,
                max_height=dp(240),
            )
        self.unit_menu.open()

    def set_unit(self, unit):
        """Asigna la unidad seleccionada en el menú desplegable."""
        self.selected_unit = unit
        self.error_text = ""
        if self.unit_menu:
            self.unit_menu.dismiss()

    def open_date_picker(self):
        """Abre el selector interactivo de fecha mediante calendario visual (MDModalDatePicker)."""
        if self.has_no_expiration:
            return

        def set_date(formatted_date):
            self.expiration_date_str = formatted_date
            self.ids.field_expiration_input.text = formatted_date

        _open_date_picker(set_date)

    def toggle_no_expiration(self):
        """Alterna entre producto con fecha de vencimiento y producto no perecible."""
        self.has_no_expiration = not self.has_no_expiration
        self.error_text = ""
        if self.has_no_expiration:
            self.expiration_date_str = ""
            self.ids.field_expiration_input.text = ""

    def submit(self):
        """Valida y registra el alimento en el inventario."""
        ok, error, data = validate_pantry_form(
            name=self.ids.field_name.ids.text_input.text,
            quantity_str=self.ids.field_quantity.ids.text_input.text,
            unit=self.selected_unit,
            threshold_str=self.ids.field_threshold.ids.text_input.text,
            expiration_str=self.ids.field_expiration_input.text,
            has_no_expiration=self.has_no_expiration,
        )
        if not ok:
            self.error_text = error
            return

        self.error_text = ""
        if self.callback_add:
            self.callback_add(data["name"], data["quantity"], data["unit"], data["threshold"], data["expiration_date"])
        self.dismiss()


class PantryItemDetailModal(BaseFormModal):
    """
    Detalle de un producto de la despensa.
    - Vista: estado, stock con +/- (sin cerrar), cantidad exacta, aviso de mínimo,
      vencimiento claro, reponer al carrito y eliminar.
    - Edición (lápiz): nombre, unidad y mínimo de alerta en el mismo modal.
    La lista de la despensa se refresca una sola vez al cerrar.
    """
    item_id = NumericProperty(0)
    item_name = StringProperty("")
    quantity_val = NumericProperty(0)
    unit = StringProperty("un.")
    min_threshold = NumericProperty(0)
    step = NumericProperty(1)
    qty_display = StringProperty("")
    step_display = StringProperty("1")
    threshold_hint = StringProperty("")
    status_str = StringProperty("Suficiente")
    status_color = ListProperty([0.18, 0.44, 0.25, 1.0])
    status_text_color = ListProperty([0.18, 0.44, 0.25, 1.0])
    exp_title = StringProperty("")
    exp_desc = StringProperty("")
    exp_color = ListProperty([0.5, 0.5, 0.5, 1.0])
    has_expiration = BooleanProperty(False)
    needs_restock = BooleanProperty(False)
    restock_text = StringProperty("Añadir al carrito")
    is_editing = BooleanProperty(False)
    edit_unit = StringProperty("un.")

    def __init__(self, item, callback_set_qty=None, callback_finish=None, callback_delete=None,
                 callback_update_exp=None, callback_add_to_cart=None, callback_update_details=None,
                 **kwargs):
        super().__init__(**kwargs)
        self.callback_set_qty = callback_set_qty
        self.callback_finish = callback_finish
        self.callback_delete = callback_delete
        self.callback_update_exp = callback_update_exp
        self.callback_add_to_cart = callback_add_to_cart
        self.callback_update_details = callback_update_details
        self._changed = False
        self._unit_menu = None
        # Contenedores de vista y edición: se intercambian dentro de 'body'
        self._view_box = self.ids.view_box
        self._edit_box = self.ids.edit_box
        self.ids.body.remove_widget(self._edit_box)
        self.clear_error_on_input(
            self.ids.exact_qty_input,
            self.ids.edit_name.ids.text_input,
            self.ids.edit_threshold.ids.text_input,
        )
        self._load(item)

    # ------------------------------------------------------------------
    # Estado mostrado
    # ------------------------------------------------------------------
    def _load(self, item):
        """Carga los datos del producto en el modal."""
        self.item = item
        self.item_id = item.id
        self.item_name = item.name
        self.unit = item.unit or "un."
        self.min_threshold = float(item.min_threshold)
        self.step = step_for_unit(self.unit)
        self.step_display = format_number(self.step)
        self.quantity_val = float(item.quantity)
        self._refresh_status()
        self._refresh_expiration(item)

    def _refresh_status(self):
        """Recalcula estado, color, aviso de mínimo y botón de reponer según la cantidad actual."""
        current = replace(self.item, quantity=self.quantity_val, unit=self.unit, min_threshold=self.min_threshold)
        self.qty_display = f"{format_number(self.quantity_val)} {self.unit}"
        self.status_str = current.status
        self.status_color = current.status_text_color
        # En modo oscuro se aclara el texto de la píldora para mantener el contraste
        app = MDApp.get_running_app()
        if app and getattr(app, "modo_oscuro", False):
            self.status_text_color = [min(1.0, c * 0.5 + 0.5) for c in self.status_color[:3]] + [1.0]
        else:
            self.status_text_color = list(self.status_color)
        self.threshold_hint = f"Te avisamos cuando baje de {format_number(self.min_threshold)} {self.unit}"
        self.needs_restock = current.status in ("Reponer", "Por agotarse") and self.callback_add_to_cart is not None

    def _refresh_expiration(self, item):
        """Arma el título y la descripción del vencimiento con su color."""
        days = item.days_until_expiration
        self.has_expiration = days is not None
        if days is None:
            self.exp_title = "Sin fecha de vencimiento"
            self.exp_desc = "Producto no perecible"
            self.exp_color = [0.45, 0.50, 0.58, 1.0]
            return
        self.exp_title = f"Vence el {item.formatted_expiration_date}"
        if days < 0:
            self.exp_desc = f"Venció hace {abs(days)} día(s)"
            self.exp_color = [0.85, 0.20, 0.25, 1.0]
        elif days == 0:
            self.exp_desc = "Vence hoy"
            self.exp_color = [0.85, 0.20, 0.25, 1.0]
        elif days <= 3:
            self.exp_desc = "Vence mañana" if days == 1 else f"Vence en {days} días"
            self.exp_color = [0.82, 0.48, 0.12, 1.0]
        else:
            self.exp_desc = f"Faltan {days} días"
            self.exp_color = [0.18, 0.55, 0.32, 1.0]

    # ------------------------------------------------------------------
    # Stock
    # ------------------------------------------------------------------
    def _apply_quantity(self, new_qty):
        """Guarda la nueva cantidad sin cerrar el modal."""
        new_qty = max(0.0, min(float(QUANTITY_MAX), round(new_qty, 3)))
        if new_qty == self.quantity_val:
            return
        self.quantity_val = new_qty
        self._changed = True
        self._refresh_status()
        if self.callback_set_qty:
            self.callback_set_qty(self.item_id, new_qty)

    def change_qty(self, direction):
        """Suma o resta un paso (según la unidad) a la cantidad actual."""
        self._apply_quantity(self.quantity_val + direction * self.step)

    def set_exact_qty(self):
        """Fija la cantidad escrita por el usuario (acepta 1,5 / 500 / 1.500)."""
        value, error = validate_quantity(self.ids.exact_qty_input.text, "La cantidad")
        if error:
            self.error_text = error
            return
        self.error_text = ""
        self.ids.exact_qty_input.text = ""
        self._apply_quantity(value)

    def on_dismiss(self):
        """Al cerrar, refresca la despensa y evalúa alertas una sola vez."""
        if self._changed and self.callback_finish:
            self.callback_finish(self.item_id)
        self._changed = False

    # ------------------------------------------------------------------
    # Edición de nombre, unidad y mínimo
    # ------------------------------------------------------------------
    def start_edit(self):
        """Pasa al modo edición con los datos actuales."""
        self.error_text = ""
        self.ids.edit_name.ids.text_input.text = self.item_name
        self.ids.edit_threshold.ids.text_input.text = format_number(self.min_threshold)
        self.edit_unit = self.unit
        self.ids.body.remove_widget(self._view_box)
        self.ids.body.add_widget(self._edit_box)
        self.is_editing = True

    def cancel_edit(self):
        """Vuelve a la vista sin guardar."""
        self.error_text = ""
        self.ids.body.remove_widget(self._edit_box)
        self.ids.body.add_widget(self._view_box)
        self.is_editing = False

    def open_edit_unit_menu(self, caller):
        if self._unit_menu is None:
            self._unit_menu = MDDropdownMenu(
                caller=caller,
                items=[{"text": u, "on_release": lambda u=u: self._set_edit_unit(u)} for u in PANTRY_UNITS],
                position="bottom",
                width=dp(140),
                max_height=dp(240),
            )
        self._unit_menu.open()

    def _set_edit_unit(self, unit):
        self.edit_unit = unit
        self.error_text = ""
        if self._unit_menu:
            self._unit_menu.dismiss()

    def save_edit(self):
        """Valida y guarda nombre, unidad y mínimo; recarga el modal con los datos nuevos."""
        ok, error, data = validate_pantry_details(
            self.ids.edit_name.ids.text_input.text,
            self.edit_unit,
            self.ids.edit_threshold.ids.text_input.text,
        )
        if not ok:
            self.error_text = error
            return
        updated = None
        if self.callback_update_details:
            updated = self.callback_update_details(self.item_id, data["name"], data["unit"], data["threshold"])
        if updated is not None:
            self._load(updated)
        self._changed = True
        self.cancel_edit()

    # ------------------------------------------------------------------
    # Vencimiento, reponer y eliminar
    # ------------------------------------------------------------------
    def add_to_cart(self):
        """Agrega el producto al carrito para reponerlo (sin cerrar el modal)."""
        if not self.callback_add_to_cart:
            return
        added = self.callback_add_to_cart(self.item_id)
        self.restock_text = "Agregado al carrito" if added else "Ya está en el carrito"

    def edit_expiration(self):
        """Abre el calendario para elegir o cambiar la fecha de vencimiento."""
        def set_date(formatted_date):
            if self.callback_update_exp:
                self.callback_update_exp(self.item_id, formatted_date)
            self._refresh_expiration(replace(self.item, expiration_date=formatted_date))
            self.item = replace(self.item, expiration_date=formatted_date)

        _open_date_picker(set_date)

    def clear_expiration(self):
        """Marca el producto como no perecible (sin fecha)."""
        if self.callback_update_exp:
            self.callback_update_exp(self.item_id, None)
        self.item = replace(self.item, expiration_date=None)
        self._refresh_expiration(self.item)

    def delete_item(self):
        """Elimina el producto de la despensa (con opción de deshacer)."""
        self._changed = False
        self.dismiss()
        if self.callback_delete:
            self.callback_delete(self.item_id, self.item_name)
