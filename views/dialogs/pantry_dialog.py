# -*- coding: utf-8 -*-
"""
Modales de Despensa para DespensAPP.
Controla adición de alimentos, umbrales mínimos, control de caducidad y detalle.
"""

from datetime import datetime, date
from kivy.properties import BooleanProperty, StringProperty, NumericProperty
from kivymd.uix.pickers import MDModalDatePicker
from views.dialogs.base import BaseFormModal, EditItemModal


class AddPantryItemModal(BaseFormModal):
    """Modal para ingresar un producto a la despensa con umbral numérico y fecha de vencimiento."""
    has_no_expiration = BooleanProperty(False)
    expiration_date_str = StringProperty("")

    def __init__(self, callback_add, **kwargs):
        super().__init__(**kwargs)
        self.callback_add = callback_add

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
        name = self.ids.field_name.ids.text_input.text.strip()
        quantity_str = self.ids.field_quantity.ids.text_input.text.strip()
        unit = self.ids.field_unit.ids.text_input.text.strip() or "un."
        thresh_str = self.ids.field_threshold.ids.text_input.text.strip()

        if self.has_no_expiration:
            exp_date = None
        else:
            raw_input = self.ids.field_expiration_input.text.strip() if "field_expiration_input" in self.ids else self.expiration_date_str.strip()
            exp_date = raw_input if raw_input and raw_input.lower() not in ("no vence", "sin vencimiento", "none", "null") else None

        if not name:
            return

        try:
            quantity = float(quantity_str) if quantity_str else 1.0
        except ValueError:
            quantity = 1.0

        try:
            threshold = float(thresh_str) if thresh_str else 2.0
        except ValueError:
            threshold = 2.0

        if self.callback_add:
            self.callback_add(name, quantity, unit, threshold, exp_date)
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
