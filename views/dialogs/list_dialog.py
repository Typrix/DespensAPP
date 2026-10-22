# -*- coding: utf-8 -*-
"""
Modales de Listas de Compras para DespensAPP.
Gestiona la creación de listas de supermercado, paleta de colores y anotación interactiva de productos.
"""

from kivymd.app import MDApp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.properties import BooleanProperty, StringProperty, NumericProperty, ListProperty
from kivy.graphics import Color, Ellipse, Line

from views.dialogs.base import BaseFormModal, EditItemModal


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
    """Modal para crear una nueva lista de compras con color y productos iniciales opcionales."""
    COLOR_PALETTE = ["#286ED3", "#10B981", "#E05A6D", "#F59E0B", "#8B5CF6", "#06B6D4"]

    def __init__(self, callback_add, **kwargs):
        super().__init__(**kwargs)
        self.callback_add = callback_add
        self.selected_color = self.COLOR_PALETTE[0]
        self.chip_widgets = []
        self._build_color_chips()

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

    def submit(self):
        name = self.ids.field_name.ids.text_input.text.strip()
        initial_items = self.ids.field_initial_items.ids.text_input.text.strip()
        if not name:
            return
        if self.callback_add:
            self.callback_add(name, self.selected_color, initial_items)
        self.dismiss()


class ShoppingListItemRow(BoxLayout):
    """Fila de producto individual dentro de una lista de compras de supermercado."""
    item_id = NumericProperty(0)
    name = StringProperty("")
    is_checked = BooleanProperty(False)

    def __init__(self, item_id, name, is_checked, callback_toggle, callback_edit, callback_delete, **kwargs):
        super().__init__(**kwargs)
        self.item_id = item_id
        self.name = name
        self.is_checked = is_checked
        self.callback_toggle = callback_toggle
        self.callback_edit = callback_edit
        self.callback_delete = callback_delete

    def toggle(self):
        if self.callback_toggle:
            self.callback_toggle(self.item_id, not self.is_checked)

    def edit(self):
        if self.callback_edit:
            self.callback_edit(self.item_id, self.name)

    def delete(self):
        if self.callback_delete:
            self.callback_delete(self.item_id)


class ShoppingListDetailModal(BaseFormModal):
    """Modal de detalle de lista estilo supermercado en papel (productos anotados, tachado y edición)."""
    list_id = NumericProperty(0)
    list_name = StringProperty("")
    icon_color_rgba = ListProperty([0.157, 0.431, 0.831, 1.0])
    subtitle_info = StringProperty("0 productos")

    def __init__(self, list_id, list_name, icon_color_rgba, **kwargs):
        super().__init__(**kwargs)
        self.list_id = list_id
        self.list_name = list_name
        self.icon_color_rgba = icon_color_rgba
        self.load_items()

    def load_items(self):
        """Carga y renderiza todos los productos anotados en la lista."""
        app = MDApp.get_running_app()
        if not app or not getattr(app, "db", None):
            return
        items = app.db.get_shopping_list_items(self.list_id)
        container = self.ids.items_list_box
        container.clear_widgets()

        checked_count = sum(1 for it in items if it.is_checked)
        self.subtitle_info = f"{len(items)} productos anotados · {checked_count} tachados"

        if not items:
            from kivy.uix.label import Label
            empty_lbl = Label(
                text="Lista vacía.\nAñade los productos que vas a comprar arriba.",
                font_size="13sp",
                color=app.text_secondary_color,
                halign="center",
                size_hint_y=None,
                height="80dp"
            )
            container.add_widget(empty_lbl)
            return

        for it in items:
            row = ShoppingListItemRow(
                item_id=it.id,
                name=it.name,
                is_checked=it.is_checked,
                callback_toggle=self.toggle_item,
                callback_edit=self.open_edit_item,
                callback_delete=self.delete_item
            )
            container.add_widget(row)

    def add_item(self):
        """Añade un nuevo producto a la lista (sin precios, como en papel)."""
        name = self.ids.new_item_input.text.strip()
        if not name:
            return
        app = MDApp.get_running_app()
        if app and getattr(app, "db", None):
            app.db.add_shopping_list_item(self.list_id, name)
            if hasattr(app, "analytics") and app.analytics:
                app.analytics.track_event("add_shopping_list_item", metadata={"list_id": self.list_id, "name": name})
            self.ids.new_item_input.text = ""
            self.load_items()
            app.cargar_listas()

    def toggle_item(self, item_id, is_checked):
        """Tacha o desmarca un producto al comprarlo."""
        app = MDApp.get_running_app()
        if app and getattr(app, "db", None):
            app.db.toggle_shopping_list_item(item_id, is_checked)
            self.load_items()
            app.cargar_listas()

    def open_edit_item(self, item_id, current_name):
        """Abre modal para corregir el nombre del producto."""
        def save_edit(new_name):
            app = MDApp.get_running_app()
            if app and getattr(app, "db", None):
                app.db.update_shopping_list_item_name(item_id, new_name)
                self.load_items()
                app.cargar_listas()

        modal = EditItemModal(
            title_text="Editar Producto",
            initial_value=current_name,
            callback_save=save_edit
        )
        modal.open()

    def delete_item(self, item_id):
        """Elimina un producto individual de la lista."""
        app = MDApp.get_running_app()
        if app and getattr(app, "db", None):
            app.db.delete_shopping_list_item(item_id)
            self.load_items()
            app.cargar_listas()

    def edit_list_name(self):
        """Abre modal para renombrar la lista."""
        def save_list_name(new_name):
            app = MDApp.get_running_app()
            if app and getattr(app, "db", None):
                app.db.update_shopping_list_name(self.list_id, new_name)
                self.list_name = new_name
                app.cargar_listas()

        modal = EditItemModal(
            title_text="Editar Nombre de Lista",
            initial_value=self.list_name,
            callback_save=save_list_name
        )
        modal.open()

    def delete_this_list(self):
        """Elimina la lista completa."""
        app = MDApp.get_running_app()
        if app:
            app.eliminar_lista_compras(self.list_id)
            self.dismiss()
