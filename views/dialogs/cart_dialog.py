# -*- coding: utf-8 -*-
"""
Modal de Carrito de Compras para DespensAPP.
Permite añadir o editar productos con título, precio unitario y lista asociada.
"""

from kivy.properties import StringProperty
from views.dialogs.base import BaseFormModal
from controllers.validators import validate_cart_form, format_number


class AddCartItemModal(BaseFormModal):
    """
    Modal para ingresar un producto al carrito o, con `item`, para editarlo.
    En modo edición llama a callback_save(item_id, title, price, subtitle).
    """
    title_text = StringProperty("Añadir al Carrito")
    submit_text = StringProperty("Agregar")

    def __init__(self, callback_add=None, item=None, callback_save=None, **kwargs):
        super().__init__(**kwargs)
        self.callback_add = callback_add
        self.callback_save = callback_save
        self.item = item
        if item is not None:
            self.title_text = "Editar producto"
            self.submit_text = "Guardar"
            self.ids.field_title.ids.text_input.text = item.title
            self.ids.field_price.ids.text_input.text = format_money_input(item.price)
            self.ids.field_subtitle.ids.text_input.text = item.subtitle
        self.clear_error_on_input(
            self.ids.field_title.ids.text_input,
            self.ids.field_price.ids.text_input,
            self.ids.field_subtitle.ids.text_input,
        )

    def submit(self):
        """Valida y guarda el artículo, mostrando el error si lo hay."""
        ok, error, data = validate_cart_form(
            title=self.ids.field_title.ids.text_input.text,
            price_str=self.ids.field_price.ids.text_input.text,
            subtitle=self.ids.field_subtitle.ids.text_input.text,
        )
        if not ok:
            self.error_text = error
            return

        if self.item is not None:
            if self.callback_save:
                self.callback_save(self.item.id, data["title"], data["price"], data["subtitle"])
        elif self.callback_add:
            self.callback_add(data["title"], data["price"], data["subtitle"])
        self.dismiss()


def format_money_input(price):
    """Precio editable en formato chileno sin '$' (ej: 1.500); vacío si es 0."""
    if not price:
        return ""
    if price == int(price):
        return f"{int(price):,}".replace(",", ".")
    return format_number(price)
