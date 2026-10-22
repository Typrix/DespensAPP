# -*- coding: utf-8 -*-
"""
Modal de Carrito de Compras para DespensAPP.
Permite añadir productos con título, precio unitario y lista asociada.
"""

from views.dialogs.base import BaseFormModal


class AddCartItemModal(BaseFormModal):
    """Modal para ingresar un nuevo producto al carrito de compras."""

    def __init__(self, callback_add, **kwargs):
        super().__init__(**kwargs)
        self.callback_add = callback_add

    def submit(self):
        """Valida y añade el artículo al carrito."""
        title = self.ids.field_title.ids.text_input.text.strip()
        price_str = self.ids.field_price.ids.text_input.text.strip()
        subtitle = self.ids.field_subtitle.ids.text_input.text.strip() or "General"

        if not title:
            return

        try:
            price = float(price_str) if price_str else 0.0
        except ValueError:
            price = 0.0

        if self.callback_add:
            self.callback_add(title, price, subtitle)
        self.dismiss()
