# -*- coding: utf-8 -*-
"""
Widget PurchaseHistoryRow para DespensAPP.
Fila del historial de compras: producto, fecha/cantidad y precio pagado.
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty


class PurchaseHistoryRow(BoxLayout):
    """Fila de solo lectura de una compra finalizada."""
    title = StringProperty("")
    detail = StringProperty("")
    price_str = StringProperty("$0")


class PurchaseGroupCard(BoxLayout):
    """Tarjeta de una lista en el historial: encabezado con subtotal y sus productos comprados."""
    name = StringProperty("")
    info = StringProperty("")
    subtotal_str = StringProperty("$0")

    def add_row(self, row):
        self.ids.rows_box.add_widget(row)
