# -*- coding: utf-8 -*-
"""
Modal de Finalizar Compra para DespensAPP.
Muestra una fila por producto tachado de la lista para indicar la cantidad comprada
(y la unidad si es un producto nuevo en la despensa) antes de registrar la compra.
"""

from kivy.metrics import dp
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.menu import MDDropdownMenu

from controllers.purchase_controller import format_money
from controllers.validators import PANTRY_UNITS, validate_quantity
from views.dialogs.base import BaseFormModal


class CheckoutRow(BoxLayout):
    """Fila editable: producto, cantidad comprada y unidad."""
    title = StringProperty("")
    unit = StringProperty("un.")
    is_new = BooleanProperty(False)

    def __init__(self, ref, title, price, unit, is_new, on_change=None, **kwargs):
        super().__init__(**kwargs)
        self.ref = ref          # producto de la lista que se compra
        self.price = price
        self.title = title
        self.unit = unit
        self.is_new = is_new
        self._menu = None
        if on_change:
            self.ids.qty_input.bind(text=lambda *a: on_change())

    def open_unit_menu(self, caller):
        """Despliega las unidades disponibles (solo productos nuevos)."""
        if not self.is_new:
            return
        if self._menu is None:
            self._menu = MDDropdownMenu(
                caller=caller,
                items=[{"text": u, "on_release": lambda u=u: self._set_unit(u)} for u in PANTRY_UNITS],
                position="bottom",
                width=dp(120),
                max_height=dp(240),
            )
        self._menu.open()

    def _set_unit(self, unit):
        self.unit = unit
        if self._menu:
            self._menu.dismiss()

    @property
    def quantity_text(self):
        return self.ids.qty_input.text


class CheckoutModal(BaseFormModal):
    """Confirma la compra de los productos tachados de una lista."""
    row_count = NumericProperty(0)
    total_str = StringProperty("$0")

    def __init__(self, checkout_rows, callback_confirm, **kwargs):
        """
        checkout_rows: salida de PurchaseController.build_checkout.
        callback_confirm(entries): recibe [{ref, quantity, unit}].
        """
        super().__init__(**kwargs)
        self.callback_confirm = callback_confirm
        self.rows = []
        for data in checkout_rows:
            row = CheckoutRow(data["ref"], data["title"], data["price"], data["unit"], data["is_new"],
                              on_change=self._clear_error)
            self.rows.append(row)
            self.ids.rows_box.add_widget(row)
        self.row_count = len(self.rows)
        self.total_str = format_money(sum(r.price for r in self.rows))

    def submit(self):
        """Valida que cada cantidad sea mayor a 0 y confirma la compra."""
        entries = []
        for row in self.rows:
            value, error = validate_quantity(row.quantity_text, "La cantidad")
            if error or value <= 0:
                self.error_text = f"{row.title}: {error or 'la cantidad debe ser mayor a 0.'}"
                return
            entries.append({"ref": row.ref, "quantity": value, "unit": row.unit})
        self.dismiss()
        if self.callback_confirm:
            self.callback_confirm(entries)
