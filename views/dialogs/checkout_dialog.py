# -*- coding: utf-8 -*-
"""
Modal de Finalizar Compra para DespensAPP.
Muestra una fila por producto tachado de la lista para indicar la cantidad comprada
(y la unidad si es un producto nuevo en la despensa) antes de registrar la compra.
"""

from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout

from controllers.purchase_controller import format_money
from controllers.unit_selector import format_amount
from views.dialogs.base import BaseFormModal
from views.dialogs.quantity_sheet import QuantitySheet


class CheckoutRow(BoxLayout):
    """Fila de un producto comprado: nombre y una píldora con la cantidad que abre la hoja compacta."""
    title = StringProperty("")
    unit = StringProperty("un.")
    is_new = BooleanProperty(False)
    quantity = NumericProperty(1)
    amount_str = StringProperty("1 un.")

    def __init__(self, ref, title, price, unit, is_new, on_change=None, **kwargs):
        super().__init__(**kwargs)
        self.ref = ref          # producto de la lista que se compra
        self.price = price
        self.title = title
        self.unit = unit
        self.is_new = is_new
        self._on_change = on_change
        self.initial_quantity = max(1, int(getattr(ref, "quantity", 1)))
        self.quantity = self.initial_quantity
        self._refresh_amount()

    def _refresh_amount(self):
        self.amount_str = format_amount(self.quantity, self.unit)

    def open_quantity(self):
        """Hoja para indicar cuánto se compró; la medida solo se elige si el producto es nuevo."""
        def save(quantity, unit):
            self.quantity = quantity
            self.unit = unit
            self._refresh_amount()
            if self._on_change:
                self._on_change()

        QuantitySheet(
            title=self.title,
            subtitle="Nuevo en la despensa" if self.is_new else "Se suma a tu stock",
            quantity=self.quantity,
            unit=self.unit,
            show_units=self.is_new,
            on_save=save,
        ).open()

    @property
    def subtotal(self) -> float:
        """Precio multiplicado por la cantidad comprada."""
        return float(self.price or 0.0) * float(self.quantity)


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
                              on_change=self._update_total)
            self.rows.append(row)
            self.ids.rows_box.add_widget(row)
        self.row_count = len(self.rows)
        self.total_str = format_money(sum(r.price * r.initial_quantity for r in self.rows))

    def _update_total(self):
        self.error_text = ""
        self.total_str = format_money(sum(row.subtotal for row in self.rows))

    def submit(self):
        """Valida que cada cantidad sea mayor a 0 y confirma la compra."""
        entries = []
        total = 0.0
        for row in self.rows:
            if row.quantity <= 0:
                self.error_text = f"{row.title}: la cantidad debe ser mayor a 0."
                return
            entries.append({"ref": row.ref, "quantity": row.quantity, "unit": row.unit})
            total += row.subtotal
        self.total_str = format_money(total)
        self.dismiss()
        if self.callback_confirm:
            self.callback_confirm(entries)
