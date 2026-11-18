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
from controllers.validators import PANTRY_UNITS, format_number, validate_quantity
from views.dialogs.base import BaseFormModal


class CheckoutRow(BoxLayout):
    """Fila de resumen y confirmación: producto, detalle de precio/stock, cantidad, medida y subtotal."""
    title = StringProperty("")
    unit = StringProperty("un.")
    is_new = BooleanProperty(False)
    detail_str = StringProperty("")
    subtotal_str = StringProperty("$0")

    def __init__(self, ref, title, price, unit, is_new, initial_quantity=1.0, on_change=None, **kwargs):
        super().__init__(**kwargs)
        self.ref = ref          # producto de la lista que se compra
        self.price = float(price or 0.0)
        self.title = title
        self.unit = unit or "un."
        self.is_new = is_new
        self._menu = None
        self._on_change_cb = on_change
        raw_qty = initial_quantity if initial_quantity else getattr(ref, "quantity", 1.0)
        self.initial_quantity = max(0.01, float(raw_qty or 1.0))
        self.ids.qty_input.text = format_number(self.initial_quantity)
        self._refresh_summary()
        self.ids.qty_input.bind(text=self._handle_change)

    def _handle_change(self, *args):
        self._refresh_summary()
        if self._on_change_cb:
            self._on_change_cb()

    def _refresh_summary(self):
        stock_txt = "Nuevo en despensa" if self.is_new else "Suma al stock"
        unit_price_txt = f"{format_money(self.price)} c/u" if self.price > 0 else "Sin precio"
        self.detail_str = f"{unit_price_txt} · {stock_txt}"
        self.subtotal_str = format_money(self.subtotal)

    def open_unit_menu(self, caller):
        """Despliega las unidades disponibles."""
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
        self._refresh_summary()
        if self._on_change_cb:
            self._on_change_cb()
        if self._menu:
            self._menu.dismiss()

    @property
    def quantity_text(self):
        return self.ids.qty_input.text

    @property
    def subtotal(self) -> float:
        """Calcula el precio multiplicado por la cantidad ingresada (si es válida)."""
        value, error = validate_quantity(self.quantity_text, "La cantidad")
        if error or value is None or value <= 0:
            return 0.0
        return float(self.price or 0.0) * float(value)


class CheckoutModal(BaseFormModal):
    """Muestra el resumen completo y confirma la compra de los productos tachados de una lista."""
    row_count = NumericProperty(0)
    total_str = StringProperty("$0")
    summary_subtitle = StringProperty("")

    def __init__(self, checkout_rows, callback_confirm, **kwargs):
        """
        checkout_rows: salida de PurchaseController.build_checkout.
        callback_confirm(entries): recibe [{ref, quantity, unit}].
        """
        super().__init__(**kwargs)
        self.callback_confirm = callback_confirm
        self.rows = []
        for data in checkout_rows:
            row = CheckoutRow(
                data["ref"],
                data["title"],
                data["price"],
                data["unit"],
                data["is_new"],
                initial_quantity=data.get("quantity", getattr(data["ref"], "quantity", 1.0)),
                on_change=self._update_total,
            )
            self.rows.append(row)
            self.ids.rows_box.add_widget(row)
        self.row_count = len(self.rows)
        self._update_total()

    def _update_total(self):
        self.error_text = ""
        total = 0.0
        new_count = 0
        restock_count = 0
        for row in self.rows:
            total += row.subtotal
            if row.is_new:
                new_count += 1
            else:
                restock_count += 1
        self.total_str = format_money(total)
        parts = [f"{len(self.rows)} {'producto' if len(self.rows) == 1 else 'productos'}"]
        if new_count:
            parts.append(f"{new_count} {'nuevo' if new_count == 1 else 'nuevos'}")
        if restock_count:
            parts.append(f"{restock_count} por sumar al stock")
        self.summary_subtitle = " · ".join(parts)

    def submit(self):
        """Valida que cada cantidad sea mayor a 0 y confirma la compra."""
        entries = []
        total = 0.0
        for row in self.rows:
            value, error = validate_quantity(row.quantity_text, "La cantidad")
            if error or value <= 0:
                self.error_text = f"{row.title}: {error or 'la cantidad debe ser mayor a 0.'}"
                return
            entries.append({"ref": row.ref, "quantity": value, "unit": row.unit})
            total += row.price * value
        self.total_str = format_money(total)
        self.dismiss()
        if self.callback_confirm:
            self.callback_confirm(entries)
