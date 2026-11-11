# -*- coding: utf-8 -*-
"""
Widgets de Mi Despensa para DespensAPP.
- PantryItemRow: fila con ícono del producto (color según categoría), estado, vencimiento y ajuste rápido -/+.
- PantryFilterChip: chip de filtro (Todos, Por vencer, Por agotarse, categorías).
- PantrySectionHeader: encabezado de sección por urgencia con su conteo.
"""

from kivymd.app import MDApp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.properties import StringProperty, NumericProperty, ListProperty

from controllers.pantry_organizer import category_of, category_tint
from controllers.product_icons import item_icon
from controllers.validators import format_number, step_for_unit


class PantryItemRow(ButtonBehavior, BoxLayout):
    """Fila de inventario: tocar abre el detalle; -/+ ajusta el stock sin abrirlo."""
    item_id = NumericProperty(0)
    name = StringProperty("")
    quantity_str = StringProperty("")
    status_str = StringProperty("Suficiente")
    status_color = ListProperty([0.18, 0.44, 0.25, 1.0])
    expiration_str = StringProperty("Sin vencimiento")
    expiration_color = ListProperty([0.5, 0.5, 0.5, 1.0])
    raw_expiration = StringProperty("")
    quantity_val = NumericProperty(0)
    unit = StringProperty("un.")
    icon = StringProperty("leaf")
    tint_light = ListProperty(category_tint("General"))
    tint_dark = ListProperty(category_tint("General", dark=True))
    step_label = StringProperty("1")

    def __init__(self, item=None, **kwargs):
        super().__init__(**kwargs)
        self.item = None
        if item is not None:
            self.set_item(item)

    def set_item(self, item):
        """Muestra los datos del producto (se usa también tras un ajuste rápido)."""
        self.item = item
        self.item_id = item.id
        self.name = item.name
        self.quantity_val = item.quantity
        self.unit = item.unit or "un."
        self.quantity_str = item.formatted_quantity
        self.status_str = item.status
        self.status_color = item.status_text_color
        self.expiration_str = item.expiration_status if item.expiration_date else ""
        self.expiration_color = item.expiration_text_color
        self.raw_expiration = item.expiration_date or ""
        category = category_of(item)
        self.icon = item_icon(item)
        self.tint_light = category_tint(category)
        self.tint_dark = category_tint(category, dark=True)
        self.step_label = format_number(step_for_unit(self.unit))

    def open_detail(self):
        """Abre la ventana modal de detalle para ajustar stock, caducidad o reponer."""
        app = MDApp.get_running_app()
        if app:
            app.abrir_detalle_despensa(self.item_id)

    def quick_adjust(self, direction):
        """Suma o resta un paso según la unidad (1 un., 100 g, 0,5 kg)."""
        app = MDApp.get_running_app()
        if app and self.item is not None:
            app.ajuste_rapido_despensa(self, direction)


class PantryFilterChip(ButtonBehavior, Label):
    """Chip de filtro; se marca activo según app.pantry_filter."""
    filter_key = StringProperty("all")

    def on_release(self):
        app = MDApp.get_running_app()
        if app:
            app.filtrar_despensa(self.filter_key)


class PantrySectionHeader(BoxLayout):
    """Encabezado de sección: punto de color, título y conteo."""
    title = StringProperty("")
    count = NumericProperty(0)
    dot_color = ListProperty([0.5, 0.5, 0.5, 1.0])
