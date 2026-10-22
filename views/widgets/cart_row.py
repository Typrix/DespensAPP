# -*- coding: utf-8 -*-
"""
Widget CartItemRow para DespensAPP.
Fila interactiva de artículo del carrito de compras con casillas de verificación.
"""

from kivymd.app import MDApp
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import BooleanProperty, StringProperty, NumericProperty


class CartItemRow(BoxLayout):
    """Fila interactiva de artículo del carrito de compras."""
    item_id = NumericProperty(0)
    title = StringProperty("")
    subtitle = StringProperty("Lista quincenal")
    price_val = NumericProperty(0)
    price_str = StringProperty("$0")
    checked = BooleanProperty(False)

    def toggle_check(self):
        """Alterna el estado completado/pendiente del artículo."""
        self.checked = not self.checked
        app = MDApp.get_running_app()
        if app:
            app.toggle_item_carrito(self.item_id, self.checked)

    def delete_self(self):
        """Elimina el artículo del carrito."""
        app = MDApp.get_running_app()
        if app:
            app.eliminar_item_carrito(self.item_id)
