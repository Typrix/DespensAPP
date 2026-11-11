# -*- coding: utf-8 -*-
"""
Widgets del historial de compras para DespensAPP.
- PurchaseHistoryRow: producto comprado, fecha/cantidad y precio pagado.
- PurchaseGroupCard: una compra finalizada (lista, fecha, subtotal y sus productos).
"""

from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import BooleanProperty, StringProperty

from controllers.validators import format_number


class PurchaseHistoryRow(BoxLayout):
    """Fila de solo lectura de una compra finalizada."""
    title = StringProperty("")
    detail = StringProperty("")
    price_str = StringProperty("$0")


class PurchaseGroupCard(ButtonBehavior, BoxLayout):
    """Tarjeta de una compra: encabezado con subtotal y sus productos comprados."""
    name = StringProperty("")
    info = StringProperty("")
    subtotal_str = StringProperty("$0")
    tappable = BooleanProperty(False)  # en Estadísticas, tocarla abre el historial completo
    in_modal = BooleanProperty(False)  # dentro de un modal blanco usa un fondo que contraste

    def add_row(self, row):
        self.ids.rows_box.add_widget(row)


def build_purchase_card(group, max_rows=None, **kwargs):
    """
    Crea la tarjeta de un grupo de PurchaseController.group_by_purchase.
    max_rows limita los productos visibles; el resto se resume en "y N producto(s) más".
    """
    count = group["count"]
    card = PurchaseGroupCard(
        name=group["name"],
        info=f"{group['date_str']} · {count} {'producto' if count == 1 else 'productos'}",
        subtotal_str=group["subtotal_str"],
        **kwargs,
    )
    records = group["records"] if max_rows is None else group["records"][:max_rows]
    for rec in records:
        card.add_row(PurchaseHistoryRow(
            title=rec.title,
            detail=f"{format_number(rec.quantity)} {rec.unit}",
            price_str=rec.formatted_price if rec.price > 0 else "Sin precio",
        ))
    hidden = count - len(records)
    if hidden > 0:
        card.add_row(PurchaseHistoryRow(title=f"y {hidden} producto(s) más", detail="", price_str=""))
    return card
