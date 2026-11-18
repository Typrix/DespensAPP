# -*- coding: utf-8 -*-
"""
Modal de Finalizar Compra para DespensAPP.
Resumen de solo lectura de los productos tachados de una lista: cantidad y medida
anotadas, subtotal de cada uno y total. Para corregir algo se edita en la lista.
"""

from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout

from controllers.purchase_controller import format_money
from controllers.unit_selector import format_amount
from views.dialogs.base import BaseFormModal


class CheckoutRow(BoxLayout):
    """Fila de resumen: producto, precio y destino en la despensa, cantidad anotada y subtotal."""
    title = StringProperty("")
    unit = StringProperty("un.")
    is_new = BooleanProperty(False)
    quantity = NumericProperty(1)
    amount_str = StringProperty("1 un.")
    detail_str = StringProperty("")
    subtotal_str = StringProperty("$0")

    def __init__(self, data, **kwargs):
        super().__init__(**kwargs)
        self.ref = data["ref"]          # producto de la lista que se compra
        self.price = float(data.get("price") or 0.0)
        self.title = data["title"]
        self.unit = data.get("unit") or "un."
        self.is_new = bool(data.get("is_new"))
        self.quantity = max(0.01, float(data.get("quantity") or 1.0))
        self.stock_unit = data.get("stock_unit") or self.unit
        self.stock_quantity = float(data.get("stock_quantity", self.quantity))
        self.amount_str = format_amount(self.quantity, self.unit)
        unit_price_txt = f"{format_money(self.price)} c/u" if self.price > 0 else "Sin precio"
        if self.is_new:
            stock_txt = "Nuevo en despensa"
        elif self.stock_unit != self.unit:
            stock_txt = f"Suma {format_amount(self.stock_quantity, self.stock_unit)} al stock"
        else:
            stock_txt = "Suma al stock"
        self.detail_str = f"{unit_price_txt} · {stock_txt}"
        self.subtotal_str = format_money(self.subtotal)

    @property
    def subtotal(self) -> float:
        """Precio por la cantidad anotada en la lista."""
        return self.price * float(self.quantity)

    def entry(self) -> dict:
        """Lo que recibe PurchaseController.finalize_purchase."""
        return {"ref": self.ref, "quantity": self.quantity, "unit": self.unit,
                "stock_quantity": self.stock_quantity}


class CheckoutModal(BaseFormModal):
    """Muestra el resumen y el total de los productos tachados y confirma la compra."""
    row_count = NumericProperty(0)
    total_str = StringProperty("$0")
    summary_subtitle = StringProperty("")

    def __init__(self, checkout_rows, callback_confirm, **kwargs):
        """
        checkout_rows: salida de PurchaseController.build_checkout.
        callback_confirm(entries): recibe [{ref, quantity, unit, stock_quantity}].
        """
        super().__init__(**kwargs)
        self.callback_confirm = callback_confirm
        self.rows = [CheckoutRow(data) for data in checkout_rows]
        for row in self.rows:
            self.ids.rows_box.add_widget(row)
        self.row_count = len(self.rows)
        self.total_str = format_money(sum(row.subtotal for row in self.rows))
        new_count = sum(1 for row in self.rows if row.is_new)
        restock_count = len(self.rows) - new_count
        parts = [f"{len(self.rows)} {'producto' if len(self.rows) == 1 else 'productos'}"]
        if new_count:
            parts.append(f"{new_count} {'nuevo' if new_count == 1 else 'nuevos'}")
        if restock_count:
            parts.append(f"{restock_count} por sumar al stock")
        self.summary_subtitle = " · ".join(parts)

    def submit(self):
        """Confirma la compra con las cantidades anotadas en la lista."""
        entries = [row.entry() for row in self.rows]
        self.dismiss()
        if self.callback_confirm:
            self.callback_confirm(entries)
