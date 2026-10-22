# -*- coding: utf-8 -*-
"""
Widget ShoppingListCard para DespensAPP.
Tarjeta interactiva de lista de compras estilo supermercado.
"""

from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, NumericProperty, ListProperty


class ShoppingListCard(ButtonBehavior, BoxLayout):
    """Tarjeta interactiva de lista de compras estilo supermercado."""
    list_id = NumericProperty(0)
    list_name = StringProperty("")
    icon_name = StringProperty("clipboard-text-outline")
    icon_color_rgba = ListProperty([0.157, 0.431, 0.831, 1.0])
    badge_bg_color = ListProperty([0.157, 0.431, 0.831, 0.15])
    info_subtitle = StringProperty("")

    def open_detail(self):
        """Abre el detalle y los productos de la lista de compras."""
        from views.dialogs.list_dialog import ShoppingListDetailModal
        modal = ShoppingListDetailModal(
            list_id=self.list_id,
            list_name=self.list_name,
            icon_color_rgba=self.icon_color_rgba
        )
        modal.open()
