# -*- coding: utf-8 -*-
"""
Modales de Despensa para DespensAPP.
Controla adición de alimentos, umbrales mínimos, control de caducidad y detalle.
"""

from kivy.properties import BooleanProperty, StringProperty, NumericProperty
from views.dialogs.base import BaseFormModal, EditItemModal


class AddPantryItemModal(BaseFormModal):
    """Modal para ingresar un producto a la despensa con umbral numérico y fecha de vencimiento."""
    has_no_expiration = BooleanProperty(False)

    def __init__(self, callback_add, **kwargs):
        super().__init__(**kwargs)
        self.callback_add = callback_add

    def toggle_no_expiration(self):
        """Alterna entre producto con fecha de vencimiento y producto no perecible."""
        self.has_no_expiration = not self.has_no_expiration
        if self.has_no_expiration:
            self.ids.field_expiration.input_text = ""
            self.ids.field_expiration.ids.text_input.text = ""
            self.ids.field_expiration.ids.text_input.disabled = True
            self.ids.field_expiration.hint_text = "No vence (producto no perecible)"
        else:
            self.ids.field_expiration.ids.text_input.disabled = False
            self.ids.field_expiration.hint_text = "AAAA-MM-DD (ej: 2026-11-20)"

    def submit(self):
        """Valida y registra el alimento en el inventario."""
        name = self.ids.field_name.ids.text_input.text.strip()
        quantity_str = self.ids.field_quantity.ids.text_input.text.strip()
        unit = self.ids.field_unit.ids.text_input.text.strip() or "un."
        thresh_str = self.ids.field_threshold.ids.text_input.text.strip()
        exp_date = None if self.has_no_expiration else self.ids.field_expiration.ids.text_input.text.strip()

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
        """Abre modal secundario para actualizar la fecha de vencimiento."""
        def save_exp(new_date):
            clean_date = new_date.strip()
            if clean_date.lower() in ("no vence", "sin vencimiento", "", "none"):
                clean_date = None
            if self.callback_update_exp:
                self.callback_update_exp(self.item_id, clean_date)
            self.dismiss()

        init_val = self.raw_expiration if self.raw_expiration else ""
        modal = EditItemModal(
            title_text="Fecha de Vencimiento (AAAA-MM-DD o 'No vence')",
            initial_value=init_val,
            callback_save=save_exp
        )
        modal.open()

    def delete_item(self):
        """Elimina el producto de la despensa."""
        if self.callback_delete:
            self.callback_delete(self.item_id)
        self.dismiss()
