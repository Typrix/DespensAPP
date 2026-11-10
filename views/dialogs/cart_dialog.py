# -*- coding: utf-8 -*-
"""
Modal de Carrito de Compras para DespensAPP.
Permite añadir productos con título, precio unitario y lista asociada.
"""

from views.dialogs.base import BaseFormModal
from controllers.validators import validate_cart_form


class AddCartItemModal(BaseFormModal):
    """Modal para ingresar un nuevo producto al carrito de compras."""

    def __init__(self, callback_add, **kwargs):
        super().__init__(**kwargs)
        self.callback_add = callback_add
        self.clear_error_on_input(
            self.ids.field_title.ids.text_input,
            self.ids.field_price.ids.text_input,
            self.ids.field_subtitle.ids.text_input,
        )

    def submit(self):
        """Valida y añade el artículo al carrito, mostrando el error si lo hay."""
        ok, error, data = validate_cart_form(
            title=self.ids.field_title.ids.text_input.text,
            price_str=self.ids.field_price.ids.text_input.text,
            subtitle=self.ids.field_subtitle.ids.text_input.text,
        )
        if not ok:
            self.error_text = error
            return

        if self.callback_add:
            self.callback_add(data["title"], data["price"], data["subtitle"])
        self.dismiss()
