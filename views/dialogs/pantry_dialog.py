# -*- coding: utf-8 -*-
"""
Modales de Despensa para DespensAPP.
Controla adición de alimentos, umbrales mínimos, control de caducidad y detalle.
"""

from datetime import datetime, date
from kivy.metrics import dp
from kivy.properties import BooleanProperty, StringProperty, NumericProperty
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.pickers import MDModalDatePicker
from views.dialogs.base import BaseFormModal, EditItemModal

# Unidades predefinidas disponibles en el menú desplegable
PANTRY_UNITS = ["un.", "kg", "g", "L", "ml", "paquete", "caja", "lata", "botella"]
NAME_MAX_LENGTH = 50
QUANTITY_MAX = 100000


def validate_pantry_form(name, quantity_str, unit, threshold_str, expiration_str, has_no_expiration):
    """
    Valida los campos del formulario de despensa.
    Retorna (True, "", datos_limpios) si es válido, o (False, mensaje_error, None).
    """
    name = (name or "").strip()
    if not name:
        return False, "Ingresa el nombre del producto.", None
    if len(name) < 2:
        return False, "El nombre debe tener al menos 2 caracteres.", None
    if len(name) > NAME_MAX_LENGTH:
        return False, f"El nombre no puede superar {NAME_MAX_LENGTH} caracteres.", None

    quantity_str = (quantity_str or "").strip()
    if not quantity_str:
        return False, "Ingresa la cantidad actual.", None
    try:
        quantity = float(quantity_str)
    except ValueError:
        return False, "La cantidad debe ser un número válido.", None
    if quantity < 0 or quantity > QUANTITY_MAX:
        return False, f"La cantidad debe estar entre 0 y {QUANTITY_MAX}.", None

    if unit not in PANTRY_UNITS:
        return False, "Selecciona una unidad de la lista.", None

    threshold_str = (threshold_str or "").strip()
    if not threshold_str:
        return False, "Ingresa la cantidad mínima para la alerta.", None
    try:
        threshold = float(threshold_str)
    except ValueError:
        return False, "La cantidad mínima debe ser un número válido.", None
    if threshold < 0 or threshold > QUANTITY_MAX:
        return False, f"La cantidad mínima debe estar entre 0 y {QUANTITY_MAX}.", None

    if has_no_expiration:
        exp_date = None
    else:
        expiration_str = (expiration_str or "").strip()
        if not expiration_str:
            return False, "Elige la fecha de vencimiento o marca 'no perecible'.", None
        try:
            parsed = datetime.strptime(expiration_str, "%Y-%m-%d").date()
        except ValueError:
            return False, "La fecha debe tener el formato AAAA-MM-DD.", None
        if parsed < date.today():
            return False, "La fecha de vencimiento no puede ser anterior a hoy.", None
        exp_date = parsed.strftime("%Y-%m-%d")

    return True, "", {
        "name": name,
        "quantity": quantity,
        "unit": unit,
        "threshold": threshold,
        "expiration_date": exp_date,
    }


class AddPantryItemModal(BaseFormModal):
    """Modal para ingresar un producto a la despensa con umbral numérico y fecha de vencimiento."""
    has_no_expiration = BooleanProperty(False)
    expiration_date_str = StringProperty("")
    selected_unit = StringProperty(PANTRY_UNITS[0])
    error_text = StringProperty("")

    def __init__(self, callback_add, **kwargs):
        super().__init__(**kwargs)
        self.callback_add = callback_add
        self.unit_menu = None

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
        if self.unit_menu:
            self.unit_menu.dismiss()

    def open_date_picker(self):
        """Abre el selector interactivo de fecha mediante calendario visual (MDModalDatePicker)."""
        if self.has_no_expiration:
            return

        date_picker = MDModalDatePicker()

        def on_ok(picker_instance):
            selected_dates = picker_instance.get_date()
            if selected_dates:
                chosen_date = selected_dates[0]
                formatted_date = chosen_date.strftime("%Y-%m-%d")
                self.expiration_date_str = formatted_date
                if "field_expiration_input" in self.ids:
                    self.ids.field_expiration_input.text = formatted_date
            picker_instance.dismiss()

        def on_cancel(picker_instance):
            picker_instance.dismiss()

        date_picker.bind(on_ok=on_ok, on_cancel=on_cancel)
        date_picker.open()

    def toggle_no_expiration(self):
        """Alterna entre producto con fecha de vencimiento y producto no perecible."""
        self.has_no_expiration = not self.has_no_expiration
        if self.has_no_expiration:
            self.expiration_date_str = ""
            if "field_expiration_input" in self.ids:
                self.ids.field_expiration_input.text = ""

    def submit(self):
        """Valida y registra el alimento en el inventario."""
        raw_expiration = self.ids.field_expiration_input.text if "field_expiration_input" in self.ids else self.expiration_date_str

        ok, error, data = validate_pantry_form(
            name=self.ids.field_name.ids.text_input.text,
            quantity_str=self.ids.field_quantity.ids.text_input.text,
            unit=self.selected_unit,
            threshold_str=self.ids.field_threshold.ids.text_input.text,
            expiration_str=raw_expiration,
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
    """Modal flotante para ajustar stock numérico, fecha de caducidad o eliminar producto."""
    item_id = NumericProperty(0)
    item_name = StringProperty("")
    item_qty_str = StringProperty("")
    expiration_str = StringProperty("Sin vencimiento")
    raw_expiration = StringProperty("")

    def __init__(self, item_id, item_name, item_qty_str, expiration_str="", raw_expiration="",
                 callback_change=None, callback_delete=None, callback_update_exp=None, **kwargs):
        super().__init__(**kwargs)
        self.item_id = item_id
        self.item_name = item_name
        self.item_qty_str = item_qty_str
        self.expiration_str = expiration_str or "Sin vencimiento"
        self.raw_expiration = raw_expiration or ""
        self.callback_change = callback_change
        self.callback_delete = callback_delete
        self.callback_update_exp = callback_update_exp

    def change_qty(self, delta):
        """Aumenta o disminuye la cantidad del producto."""
        if self.callback_change:
            self.callback_change(self.item_id, delta)
        self.dismiss()

    def edit_expiration(self):
        """Abre el selector de calendario interactivo para actualizar la fecha de caducidad."""
        date_picker = MDModalDatePicker()

        def on_ok(picker_instance):
            selected_dates = picker_instance.get_date()
            if selected_dates and self.callback_update_exp:
                chosen_date = selected_dates[0]
                formatted_date = chosen_date.strftime("%Y-%m-%d")
                self.callback_update_exp(self.item_id, formatted_date)
            picker_instance.dismiss()
            self.dismiss()

        def on_cancel(picker_instance):
            picker_instance.dismiss()

        date_picker.bind(on_ok=on_ok, on_cancel=on_cancel)
        date_picker.open()

    def clear_expiration(self):
        """Elimina la fecha de vencimiento marcando el producto como no perecible."""
        if self.callback_update_exp:
            self.callback_update_exp(self.item_id, None)
        self.dismiss()

    def delete_item(self):
        """Elimina el producto de la despensa."""
        if self.callback_delete:
            self.callback_delete(self.item_id)
        self.dismiss()
