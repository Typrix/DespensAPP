# -*- coding: utf-8 -*-
"""
Widgets y Componentes Visuales Personalizados para DespensAPP.
Contiene elementos interactivos de la interfaz: botones de navegación, filas de
carrito, tarjetas de listas, barras de progreso y modal flotante de perfil.
"""

from kivymd.app import MDApp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.widget import Widget
from kivy.uix.modalview import ModalView
from kivy.properties import (
    BooleanProperty,
    StringProperty,
    NumericProperty,
    ListProperty,
)
from kivy.graphics import Color, RoundedRectangle

from dialogs import PantryItemDetailModal, ShoppingListDetailModal


class CustomProgressBar(Widget):
    """Barra de progreso moderna con bordes redondeados y colores configurables."""
    value = NumericProperty(0.5)
    track_color = ListProperty([0.890, 0.914, 0.945, 1])
    fill_color = ListProperty([0.157, 0.431, 0.831, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pos=self._update_canvas,
            size=self._update_canvas,
            value=self._update_canvas,
            track_color=self._update_canvas,
            fill_color=self._update_canvas,
        )

    def _update_canvas(self, *args):
        self.canvas.clear()
        with self.canvas:
            Color(rgba=self.track_color)
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[self.height / 2.0]
            )
            clamped_val = max(0.0, min(1.0, self.value))
            fill_width = self.width * clamped_val
            if fill_width > 0:
                Color(rgba=self.fill_color)
                RoundedRectangle(
                    pos=self.pos,
                    size=(fill_width, self.height),
                    radius=[self.height / 2.0]
                )


class BottomNavButton(ButtonBehavior, BoxLayout):
    """Botón de la barra de navegación inferior con píldora activa redondeada."""
    icon_name = StringProperty("home-outline")
    label_text = StringProperty("Inicio")
    screen_target = StringProperty("home")
    is_active = BooleanProperty(False)


class CartItemRow(BoxLayout):
    """Fila interactiva de artículo del carrito de compras."""
    item_id = NumericProperty(0)
    title = StringProperty("")
    subtitle = StringProperty("Lista quincenal")
    price_val = NumericProperty(0)
    price_str = StringProperty("$0")
    checked = BooleanProperty(False)

    def toggle_check(self):
        self.checked = not self.checked
        app = MDApp.get_running_app()
        if app:
            app.toggle_item_carrito(self.item_id, self.checked)

    def delete_self(self):
        app = MDApp.get_running_app()
        if app:
            app.eliminar_item_carrito(self.item_id)


class PantryItemRow(ButtonBehavior, BoxLayout):
    """Fila de inventario de la despensa con alerta cromática y estado de vencimiento."""
    item_id = NumericProperty(0)
    name = StringProperty("")
    quantity_str = StringProperty("")
    status_str = StringProperty("Suficiente")
    status_color = ListProperty([0.18, 0.44, 0.25, 1.0])
    expiration_str = StringProperty("Sin vencimiento")
    expiration_color = ListProperty([0.5, 0.5, 0.5, 1.0])
    raw_expiration = StringProperty("")

    def open_detail(self):
        app = MDApp.get_running_app()
        if app:
            modal = PantryItemDetailModal(
                item_id=self.item_id,
                item_name=self.name,
                item_qty_str=self.quantity_str,
                expiration_str=self.expiration_str,
                raw_expiration=self.raw_expiration,
                callback_change=app.cambiar_cantidad_despensa,
                callback_delete=app.eliminar_item_despensa,
                callback_update_exp=getattr(app, "actualizar_vencimiento_despensa", None)
            )
            modal.open()


class ShoppingListCard(ButtonBehavior, BoxLayout):
    """Tarjeta interactiva de lista de compras estilo supermercado."""
    list_id = NumericProperty(0)
    list_name = StringProperty("")
    icon_name = StringProperty("clipboard-text-outline")
    icon_color_rgba = ListProperty([0.157, 0.431, 0.831, 1.0])
    badge_bg_color = ListProperty([0.157, 0.431, 0.831, 0.15])
    info_subtitle = StringProperty("")

    def open_detail(self):
        modal = ShoppingListDetailModal(
            list_id=self.list_id,
            list_name=self.list_name,
            icon_color_rgba=self.icon_color_rgba
        )
        modal.open()


class AddCircleButton(ButtonBehavior, AnchorLayout):
    """Botón circular con icono '+' perfectamente centrado."""
    pass


class AvatarCircleButton(ButtonBehavior, AnchorLayout):
    """Botón circular del avatar con texto centrado dinámico."""
    pass


class ProfileModalView(ModalView):
    """Modal flotante de perfil de usuario sin interferencia de toques cuando está cerrado."""
    pass
