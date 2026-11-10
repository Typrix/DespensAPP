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
