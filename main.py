# -*- coding: utf-8 -*-
# ========================================================
# DespensAPP - Aplicación de Gestión de Despensa y Compras
# ========================================================

from kivy.config import Config
Config.set("graphics", "height", "780")
Config.set("graphics", "width", "390")
Config.set("graphics", "resizable", "False")

from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager
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
from kivy.graphics import Color, RoundedRectangle, Line, Ellipse


# --------------------------------------------------------
# Widgets Personalizados con Renderizado Canvas Reactivo
# --------------------------------------------------------

class CustomProgressBar(Widget):
    """Barra de progreso moderna con bordes redondeados y colores configurables."""
    value = NumericProperty(0.5)
    track_color = ListProperty([0.792, 0.843, 0.784, 1])
    fill_color = ListProperty([0.192, 0.357, 0.243, 1])

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


class CartItemRow(ButtonBehavior, BoxLayout):
    """Fila de artículo del carrito de compras con checkbox interactivo."""
    item_id = StringProperty("")
    title = StringProperty("")
    subtitle = StringProperty("Lista quincenal")
    price_val = NumericProperty(0)
    price_str = StringProperty("$0")
    checked = BooleanProperty(False)

    def on_release(self):
        self.checked = not self.checked
        app = MDApp.get_running_app()
        if app:
            app.recalcular_total_carrito()


class AddCircleButton(ButtonBehavior, AnchorLayout):
    """Botón circular verde con icono '+' perfectamente centrado."""
    pass


class AvatarCircleButton(ButtonBehavior, AnchorLayout):
    """Botón circular del avatar 'SO' con texto centrado."""
    pass


class ProfileModalView(ModalView):
    """Modal flotante de perfil de usuario sin interferencia de toques cuando está cerrado."""
    pass


# --------------------------------------------------------
# Aplicación Principal
# --------------------------------------------------------

class MainApp(MDApp):
    # Control de Pantalla y Estado
    current_screen_name = StringProperty("stats")
    screen_header_tag = StringProperty("ESTADÍSTICAS")
    modo_oscuro = BooleanProperty(False)

    # Total dinámico del carrito
    total_carrito_str = StringProperty("$8.800")

    # Referencia al modal de perfil
    profile_modal = None

    # Paleta de Colores Modo Claro (Predeterminado)
    COLOR_LIGHT = {
        "bg": [0.965, 0.969, 0.949, 1],                # #F6F7F2
        "sage_container": [0.875, 0.910, 0.867, 1],    # #DFE8DD
        "card_white": [1.0, 1.0, 1.0, 1],              # #FFFFFF
        "text_primary": [0.118, 0.227, 0.145, 1],      # #1E3A25
        "text_secondary": [0.416, 0.498, 0.439, 1],    # #6A7F70
        "category_tag": [0.353, 0.478, 0.392, 1],      # #5A7A64
        "accent_green": [0.192, 0.357, 0.243, 1],      # #315B3E
        "active_pill": [0.835, 0.898, 0.824, 1],       # #D5E5D2
        "divider": [0.792, 0.843, 0.784, 1],           # #CAD7C8
        "leaf_badge_bg": [0.847, 0.910, 0.839, 1],     # #D8E8D6
        "avatar_border": [0.192, 0.357, 0.243, 1],     # #315B3E
        "chart_card_dark": [0.192, 0.357, 0.243, 1],   # #315B3E
        "chart_card_text_dim": [0.718, 0.843, 0.749, 1], # #B7D7BF
        "progress_track": [0.792, 0.843, 0.784, 1],    # #CAD7C8
        "icon_badge_pink": [0.969, 0.867, 0.847, 1],   # #F7DDD8
        "icon_badge_amber": [0.961, 0.910, 0.816, 1],  # #F5E8D0
    }

    # Paleta de Colores Modo Oscuro
    COLOR_DARK = {
        "bg": [0.082, 0.106, 0.090, 1],                # #151B17
        "sage_container": [0.133, 0.176, 0.145, 1],    # #222D25
        "card_white": [0.173, 0.227, 0.188, 1],        # #2C3A30
        "text_primary": [0.910, 0.945, 0.918, 1],      # #E8F1EA
        "text_secondary": [0.616, 0.690, 0.631, 1],    # #9DB0A1
        "category_tag": [0.518, 0.671, 0.549, 1],      # #84AB8C
        "accent_green": [0.380, 0.675, 0.455, 1],      # #61AC74
        "active_pill": [0.184, 0.259, 0.200, 1],       # #2F4233
        "divider": [0.204, 0.267, 0.220, 1],           # #344438
        "leaf_badge_bg": [0.184, 0.259, 0.200, 1],     # #2F4233
        "avatar_border": [0.380, 0.675, 0.455, 1],     # #61AC74
        "chart_card_dark": [0.114, 0.157, 0.125, 1],   # #1D2820
        "chart_card_text_dim": [0.616, 0.690, 0.631, 1],
        "progress_track": [0.235, 0.306, 0.251, 1],    # #3C4E40
        "icon_badge_pink": [0.306, 0.204, 0.204, 1],
        "icon_badge_amber": [0.306, 0.267, 0.184, 1],
    }

    # Propiedades reactivas de color expuestas a KV
    bg_color = ListProperty([0.965, 0.969, 0.949, 1])
    sage_container_color = ListProperty([0.875, 0.910, 0.867, 1])
    card_white_color = ListProperty([1.0, 1.0, 1.0, 1])
    text_primary_color = ListProperty([0.118, 0.227, 0.145, 1])
    text_secondary_color = ListProperty([0.416, 0.498, 0.439, 1])
    category_tag_color = ListProperty([0.353, 0.478, 0.392, 1])
    accent_green_color = ListProperty([0.192, 0.357, 0.243, 1])
    active_pill_color = ListProperty([0.835, 0.898, 0.824, 1])
    divider_color = ListProperty([0.792, 0.843, 0.784, 1])
    leaf_badge_bg_color = ListProperty([0.847, 0.910, 0.839, 1])
    avatar_border_color = ListProperty([0.192, 0.357, 0.243, 1])
    chart_card_dark_color = ListProperty([0.192, 0.357, 0.243, 1])
    chart_card_text_dim_color = ListProperty([0.718, 0.843, 0.749, 1])
    progress_track_color = ListProperty([0.792, 0.843, 0.784, 1])
    icon_badge_pink_color = ListProperty([0.969, 0.867, 0.847, 1])
    icon_badge_amber_color = ListProperty([0.961, 0.910, 0.816, 1])

    TAGS_MAP = {
        "home": "INICIO",
        "cart": "COMPRAS",
        "cupboard": "DESPENSA",
        "lists": "LISTAS",
        "stats": "ESTADÍSTICAS",
    }

    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Green"
        self._aplicar_tema(False)
        return None

    def on_start(self):
        self.cambiar_pantalla(self.current_screen_name)

    def cambiar_pantalla(self, name_option):
        """Cambia suavemente a la pantalla seleccionada y actualiza encabezados."""
        self.current_screen_name = name_option
        self.screen_header_tag = self.TAGS_MAP.get(name_option, "DESPENSAPP")
        
        sm = self.root.ids.get("screen_manager") if self.root else None
        if sm:
            sm.current = name_option

    def toggle_menu_perfil(self):
        """Abre o cierra el modal flotante de perfil de usuario."""
        if self.profile_modal is None:
            self.profile_modal = ProfileModalView()
        
        if self.profile_modal.get_parent_window() is not None:
            self.profile_modal.dismiss()
        else:
            self.profile_modal.open()

    def cerrar_menu_perfil(self):
        """Cierra el menú de perfil."""
        if self.profile_modal and self.profile_modal.get_parent_window() is not None:
            self.profile_modal.dismiss()

    def cambiar_tema(self, valor_activo):
        """Alterna entre Tema Claro y Tema Oscuro de manera fluida."""
        self.modo_oscuro = bool(valor_activo)
        self.theme_cls.theme_style = "Dark" if self.modo_oscuro else "Light"
        self._aplicar_tema(self.modo_oscuro)

    def _aplicar_tema(self, dark):
        paleta = self.COLOR_DARK if dark else self.COLOR_LIGHT
        self.bg_color = paleta["bg"]
        self.sage_container_color = paleta["sage_container"]
        self.card_white_color = paleta["card_white"]
        self.text_primary_color = paleta["text_primary"]
        self.text_secondary_color = paleta["text_secondary"]
        self.category_tag_color = paleta["category_tag"]
        self.accent_green_color = paleta["accent_green"]
        self.active_pill_color = paleta["active_pill"]
        self.divider_color = paleta["divider"]
        self.leaf_badge_bg_color = paleta["leaf_badge_bg"]
        self.avatar_border_color = paleta["avatar_border"]
        self.chart_card_dark_color = paleta["chart_card_dark"]
        self.chart_card_text_dim_color = paleta["chart_card_text_dim"]
        self.progress_track_color = paleta["progress_track"]
        self.icon_badge_pink_color = paleta["icon_badge_pink"]
        self.icon_badge_amber_color = paleta["icon_badge_amber"]

    def recalcular_total_carrito(self):
        """Calcula el total sumando los productos que no han sido tachados (o todos)."""
        total = 8800
        self.total_carrito_str = f"${total:,.0f}".replace(",", ".")

    def accion_agregar(self):
        """Acción al pulsar el botón '+' de cada pantalla."""
        print(f"Agregar nuevo elemento en pantalla: {self.current_screen_name}")


if __name__ == '__main__':
    MainApp().run()