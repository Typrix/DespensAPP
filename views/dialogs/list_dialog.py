# -*- coding: utf-8 -*-
"""
Modales de Listas de Compras para DespensAPP.
Gestiona la creación de listas de supermercado, paleta de colores y anotación interactiva de productos.
"""

from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.properties import BooleanProperty, StringProperty, NumericProperty, ListProperty
from kivy.graphics import Color, Ellipse, Line

from views.dialogs.base import BaseFormModal, EditItemModal
from controllers.validators import validate_list_form, validate_cart_form, format_number
from controllers.purchase_controller import summarize_items, format_money
from controllers.list_controller import DEFAULT_SUPERMARKET, SUPERMARKET_OPTIONS
from views.widgets.empty_state import EmptyState
from controllers.product_icons import name_visual
from controllers.pantry_organizer import category_tint


class ColorChipButton(Button):
    """Botón circular interactivo para seleccionar color de icono."""
    color_hex = StringProperty("#286ED3")
    is_selected = BooleanProperty(False)

    def __init__(self, color_hex, on_select, **kwargs):
        super().__init__(**kwargs)
        self.color_hex = color_hex
        self.on_select = on_select
        self.size_hint = (None, None)
        self.size = ("34dp", "34dp")
        self.background_color = [0, 0, 0, 0]
        self.bind(pos=self._update_canvas, size=self._update_canvas, is_selected=self._update_canvas)

    def _update_canvas(self, *args):
        self.canvas.before.clear()
        rgba = self._hex_to_rgba(self.color_hex)
        with self.canvas.before:
            Color(rgba=rgba)
            Ellipse(pos=self.pos, size=self.size)
            if self.is_selected:
                Color(rgba=[1, 1, 1, 1])
                Line(circle=(self.center_x, self.center_y, 14), width=1.8)
                Color(rgba=rgba)
                Line(circle=(self.center_x, self.center_y, 16), width=1.5)

    def on_release(self):
        if self.on_select:
            self.on_select(self.color_hex)

    @staticmethod
    def _hex_to_rgba(hex_str):
        h = hex_str.lstrip("#")
        return [int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0, 1.0]


class AddShoppingListModal(BaseFormModal):
    """Modal para crear una nueva lista de compras con supermercado y color."""
    COLOR_PALETTE = ["#286ED3", "#10B981", "#E05A6D", "#F59E0B", "#8B5CF6", "#06B6D4"]
    selected_supermarket = StringProperty(DEFAULT_SUPERMARKET)

    def __init__(self, callback_add, **kwargs):
        super().__init__(**kwargs)
        self.callback_add = callback_add
        self.selected_color = self.COLOR_PALETTE[0]
        self.selected_supermarket = DEFAULT_SUPERMARKET
        self.supermarket_menu = None
        self.chip_widgets = []
        self._build_color_chips()
        self.clear_error_on_input(
            self.ids.field_name.ids.text_input,
        )

    def _build_color_chips(self):
        container = self.ids.color_chips_box
        container.clear_widgets()
        for color_hex in self.COLOR_PALETTE:
            chip = ColorChipButton(
                color_hex=color_hex,
                on_select=self.set_color,
                is_selected=(color_hex == self.selected_color)
            )
            self.chip_widgets.append(chip)
            container.add_widget(chip)

    def set_color(self, color_hex):
        self.selected_color = color_hex
        for chip in self.chip_widgets:
            chip.is_selected = (chip.color_hex == color_hex)

    def open_supermarket_menu(self, caller):
        """Despliega el menú con los supermercados disponibles."""
        if self.supermarket_menu is None:
            self.supermarket_menu = MDDropdownMenu(
                caller=caller,
                items=[
                    {
                        "text": market,
                        "leading_icon": "storefront-outline",
                        "on_release": lambda m=market: self.set_supermarket(m),
                    }
                    for market in SUPERMARKET_OPTIONS
                ],
                position="bottom",
                width=max(caller.width, dp(220)),
                max_height=dp(260),
            )
        self.supermarket_menu.open()

    def set_supermarket(self, supermarket: str):
        """Asigna el supermercado seleccionado y cierra el menú desplegable."""
        self.selected_supermarket = supermarket
        if self.supermarket_menu:
            self.supermarket_menu.dismiss()

    def on_dismiss(self):
        """Cierra el menú desplegable de supermercado si quedó abierto."""
        if self.supermarket_menu:
            self.supermarket_menu.dismiss()

    def submit(self):
        """Valida y crea la lista, mostrando el error si lo hay."""
        ok, error, data = validate_list_form(
            name=self.ids.field_name.ids.text_input.text,
        )
        if not ok:
            self.error_text = error
            return
        market = "" if self.selected_supermarket == DEFAULT_SUPERMARKET else self.selected_supermarket
        if self.callback_add:
            self.callback_add(data["name"], self.selected_color, "", market)
        self.dismiss()


class ShoppingListItemRow(BoxLayout):
    """Producto de una lista: tachar = ya está en el carro; tocar el nombre o el lápiz = editar."""
    item_id = NumericProperty(0)
    name = StringProperty("")
    price = NumericProperty(0)
    price_str = StringProperty("")
    quantity = NumericProperty(1)
    is_checked = BooleanProperty(False)
    icon = StringProperty("leaf")
    tint_light = ListProperty(category_tint("General"))
    tint_dark = ListProperty(category_tint("General", dark=True))

    def __init__(self, item, callback_toggle, callback_edit, callback_delete, **kwargs):
        super().__init__(**kwargs)
        self.item = item
        self.item_id = item.id
        self.name = item.name
        self.icon, category = name_visual(item.name)
        self.tint_light = category_tint(category)
        self.tint_dark = category_tint(category, dark=True)
        self.price = item.price
        self.quantity = item.quantity
        self.price_str = item.formatted_price if item.price > 0 else ""
        self.is_checked = item.is_checked
        self.callback_toggle = callback_toggle
        self.callback_edit = callback_edit
        self.callback_delete = callback_delete
        self.callback_quantity = None

    def toggle(self):
        if self.callback_toggle:
            self.callback_toggle(self.item_id, not self.is_checked)

    def edit(self):
        if self.callback_edit:
            self.callback_edit(self.item)

    def delete(self):
        if self.callback_delete:
            self.callback_delete(self.item_id)

    def adjust_quantity(self, delta):
        if self.callback_quantity:
            self.callback_quantity(self.item, max(1, self.quantity + delta))


class EditListItemModal(BaseFormModal):
    """Corrige el nombre y el precio de un producto de la lista."""

    def __init__(self, item, callback_save, **kwargs):
        super().__init__(**kwargs)
        self.item = item
        self.callback_save = callback_save
        self.ids.field_name.ids.text_input.text = item.name
        self.ids.field_price.ids.text_input.text = format_price_input(item.price)
        self.clear_error_on_input(self.ids.field_name.ids.text_input, self.ids.field_price.ids.text_input)

    def submit(self):
        ok, error, data = validate_cart_form(
            title=self.ids.field_name.ids.text_input.text,
            price_str=self.ids.field_price.ids.text_input.text,
            subtitle="",
        )
        if not ok:
            self.error_text = error
            return
        if self.callback_save:
            self.callback_save(self.item.id, data["title"], data["price"])
        self.dismiss()


def format_price_input(price):
    """Precio editable en formato chileno sin '$' (ej: 1.500); vacío si es 0."""
    if not price:
        return ""
    if price == int(price):
        return f"{int(price):,}".replace(",", ".")
    return format_number(price)


class ShoppingListDetailModal(BaseFormModal):
    """
    Lista de compras que funciona como carrito: se anotan productos (con precio opcional),
    se tachan al echarlos al carro y se finaliza la compra desde aquí.
    """
    list_id = NumericProperty(0)
    list_name = StringProperty("")
    supermarket = StringProperty("")
    icon_color_rgba = ListProperty([0.157, 0.431, 0.831, 1.0])
    subtitle_info = StringProperty("0 productos")
    checked_count = NumericProperty(0)
    in_cart_str = StringProperty("$0")
    progress_str = StringProperty("")

    def __init__(self, list_id, list_name, icon_color_rgba, supermarket="", **kwargs):
        super().__init__(**kwargs)
        self.list_id = list_id
        self.list_name = list_name
        self.supermarket = (supermarket or "").strip()
        self.icon_color_rgba = icon_color_rgba
        self.clear_error_on_input(self.ids.new_item_input, self.ids.new_item_price)
        self.load_items()

    def load_items(self):
        """Carga los productos (orden fijo) y recalcula el total que va en el carro."""
        app = MDApp.get_running_app()
        if not app or not getattr(app, "db", None):
            return
        items = [
            it for it in app.db.get_shopping_list_items(self.list_id)
            if not app.is_pending_delete("list_item", it.id)
        ]
        summary = summarize_items(items)
        self.checked_count = summary["checked"]
        self.in_cart_str = format_money(summary["in_cart"])
        self.progress_str = (
            f"de {format_money(summary['estimated'])} estimado · {summary['checked']} de {summary['total_items']}"
            if items else ""
        )
        base_sub = (
            f"{summary['pending']} por comprar · {summary['checked']} en el carro" if items else "Lista vacía"
        )
        self.subtitle_info = f"{self.supermarket} · {base_sub}" if self.supermarket else base_sub

        container = self.ids.items_list_box
        container.clear_widgets()
        if not items:
            container.add_widget(EmptyState(
                icon="clipboard-text-outline",
                title="Lista vacía",
                message="Anota arriba el producto y su precio para comparar y controlar tu gasto.",
            ))
            return
        for it in items:
            row = ShoppingListItemRow(
                item=it,
                callback_toggle=self.toggle_item,
                callback_edit=self.open_edit_item,
                callback_delete=self.delete_item,
            )
            row.callback_quantity = self.update_item_quantity
            container.add_widget(row)

    def add_item(self):
        """Anota un producto con su precio obligatorio y verifica si existe más barato en otro supermercado."""
        ok, error, data = validate_cart_form(
            title=self.ids.new_item_input.text,
            price_str=self.ids.new_item_price.text,
            subtitle="",
        )
        if not ok:
            self.error_text = error
            return
        self.error_text = ""
        app = MDApp.get_running_app()
        if app and getattr(app, "db", None):
            new_id = app.db.add_shopping_list_item(self.list_id, data["title"], price=data["price"])
            if hasattr(app, "analytics") and app.analytics:
                app.analytics.track_event("add_shopping_list_item", metadata={"list_id": self.list_id})
            offer = app.db.find_cheaper_supermarket_offer(data["title"], data["price"], self.supermarket)
            if offer and hasattr(app, "notificar_oferta_supermercado"):
                offer["item_id"] = new_id or 0
                app.notificar_oferta_supermercado(offer, force=True)
            self.ids.new_item_input.text = ""
            self.ids.new_item_price.text = ""
            self.ids.new_item_input.focus = True
            self.load_items()
            app.cargar_listas()
            if hasattr(app, "actualizar_inicio"):
                app.actualizar_inicio()

    def toggle_item(self, item_id, is_checked):
        """Tachar = el producto ya está en el carro."""
        app = MDApp.get_running_app()
        if app and getattr(app, "db", None):
            app.db.toggle_shopping_list_item(item_id, is_checked)
            self.load_items()
            app.cargar_listas()

    def update_item_quantity(self, item, quantity):
        """Ajusta la cantidad del producto sin permitir que baje de una unidad."""
        app = MDApp.get_running_app()
        if app and getattr(app, "db", None):
            app.db.update_shopping_list_item(item.id, item.name, item.price, quantity)
            self.load_items()
            app.cargar_listas()
            if hasattr(app, "actualizar_inicio"):
                app.actualizar_inicio()

    def open_edit_item(self, item):
        """Abre el modal para corregir nombre y precio."""
        def save_edit(item_id, name, price):
            app = MDApp.get_running_app()
            if app and getattr(app, "db", None):
                app.db.update_shopping_list_item(item_id, name, price, item.quantity)
                offer = app.db.find_cheaper_supermarket_offer(name, price, self.supermarket)
                if offer and hasattr(app, "notificar_oferta_supermercado"):
                    offer["item_id"] = item_id
                    app.notificar_oferta_supermercado(offer, force=True)
                self.load_items()
                app.cargar_listas()
                if hasattr(app, "actualizar_inicio"):
                    app.actualizar_inicio()

        EditListItemModal(item=item, callback_save=save_edit).open()

    def delete_item(self, item_id):
        """Elimina un producto individual de la lista (con opción de deshacer)."""
        app = MDApp.get_running_app()
        if not app:
            return
        name = next((row.name for row in self.ids.items_list_box.children
                     if isinstance(row, ShoppingListItemRow) and row.item_id == item_id), "Producto")

        def refresh():
            self.load_items()
            app.cargar_listas()

        app.programar_borrado("list_item", item_id, f"'{name}' eliminado", refresh)

    def edit_list_name(self):
        """Abre modal para renombrar la lista."""
        def save_list_name(new_name):
            app = MDApp.get_running_app()
            if app and getattr(app, "db", None):
                app.db.update_shopping_list_name(self.list_id, new_name)
                self.list_name = new_name
                app.cargar_listas()

        EditItemModal(
            title_text="Editar nombre de la lista",
            initial_value=self.list_name,
            callback_save=save_list_name,
        ).open()

    def finalize(self):
        """Finaliza la compra de lo tachado en esta lista."""
        app = MDApp.get_running_app()
        if app:
            app.abrir_finalizar_compra(self.list_id, self.list_name, on_done=self.load_items)

    def delete_this_list(self):
        """Elimina la lista completa (con opción de deshacer)."""
        app = MDApp.get_running_app()
        self.dismiss()
        if app:
            app.eliminar_lista_compras(self.list_id, self.list_name)
