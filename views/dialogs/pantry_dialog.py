# -*- coding: utf-8 -*-
"""
Modales de Despensa para DespensAPP.
Controla adición de alimentos, umbrales mínimos, control de caducidad y detalle.
"""

from kivy.metrics import dp
from kivy.properties import BooleanProperty, StringProperty, NumericProperty
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.pickers import MDModalDatePicker
from views.dialogs.base import BaseFormModal
from controllers.validators import (
    PANTRY_UNITS,
    NAME_MAX_LENGTH,
    QUANTITY_MAX,
    validate_pantry_form,
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
    Modal para ajustar stock, fecha de caducidad o eliminar un producto.
    Los ajustes de cantidad no cierran el modal: el stock se actualiza en vivo
    y la lista de la despensa se refresca una sola vez al cerrar.
    """
    item_id = NumericProperty(0)
    item_name = StringProperty("")
    quantity_val = NumericProperty(0)
    unit = StringProperty("un.")
    step = NumericProperty(1)
    qty_display = StringProperty("")
    step_display = StringProperty("1")
    expiration_str = StringProperty("Sin vencimiento")
    raw_expiration = StringProperty("")

    def __init__(self, item_id, item_name, quantity_val, unit, expiration_str="", raw_expiration="",
                 callback_set_qty=None, callback_finish=None, callback_delete=None,
                 callback_update_exp=None, **kwargs):
        super().__init__(**kwargs)
        self.item_id = item_id
        self.item_name = item_name
        self.unit = unit or "un."
        self.step = step_for_unit(self.unit)
        self.step_display = format_number(self.step)
        self.quantity_val = float(quantity_val)
        self.on_quantity_val(self, self.quantity_val)  # también cubre el caso cantidad = 0
        self.expiration_str = expiration_str or "Sin vencimiento"
        self.raw_expiration = raw_expiration or ""
        self.callback_set_qty = callback_set_qty
        self.callback_finish = callback_finish
        self.callback_delete = callback_delete
        self.callback_update_exp = callback_update_exp
        self._qty_changed = False
        self.clear_error_on_input(self.ids.exact_qty_input)

    def on_quantity_val(self, instance, value):
        self.qty_display = f"{format_number(value)} {self.unit}"

    def _apply_quantity(self, new_qty):
        """Guarda la nueva cantidad sin cerrar el modal."""
        new_qty = max(0.0, min(float(QUANTITY_MAX), round(new_qty, 3)))
        if new_qty == self.quantity_val:
            return
        self.quantity_val = new_qty
        self._qty_changed = True
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
        if self._qty_changed and self.callback_finish:
            self.callback_finish(self.item_id)
        self._qty_changed = False

    def edit_expiration(self):
        """Abre el selector de calendario interactivo para actualizar la fecha de caducidad."""
        def set_date(formatted_date):
            if self.callback_update_exp:
                self.callback_update_exp(self.item_id, formatted_date)
            self.dismiss()

        _open_date_picker(set_date)

    def clear_expiration(self):
        """Elimina la fecha de vencimiento marcando el producto como no perecible."""
        if self.callback_update_exp:
            self.callback_update_exp(self.item_id, None)
        self.dismiss()

    def delete_item(self):
        """Elimina el producto de la despensa (con opción de deshacer)."""
        self._qty_changed = False
        self.dismiss()
        if self.callback_delete:
            self.callback_delete(self.item_id, self.item_name)
