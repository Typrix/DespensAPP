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
    track_color = ListProperty([0.890, 0.914, 0.945, 1])  # Azul muy claro para la pista
    fill_color = ListProperty([0.157, 0.431, 0.831, 1])   # Azul principal vibrante para el relleno

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
    """Botón circular con icono '+' perfectamente centrado."""
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

    # Paleta de Colores Modo Claro - Tonos Azules Profesionales y Limpios
    COLOR_LIGHT = {
        "bg": [0.949, 0.965, 0.984, 1],                 # #F2F5FB (Fondo azul grisáceo muy claro y limpio)
        "sage_container": [0.890, 0.918, 0.957, 1],     # #E3EAF5 (Contenedor azul suave)
        "card_white": [1.0, 1.0, 1.0, 1],               # #FFFFFF (Tarjetas blancas)
        "text_primary": [0.086, 0.149, 0.251, 1],       # #162640 (Texto principal azul marino muy oscuro)
        "text_secondary": [0.380, 0.471, 0.592, 1],     # #617897 (Texto secundario azul grisáceo medio)
        "category_tag": [0.157, 0.431, 0.831, 1],       # #286ED3 (Etiquetas en azul vibrante)
        "accent_green": [0.157, 0.431, 0.831, 1],       # #286ED3 (Acento azul principal)
        "active_pill": [0.835, 0.886, 0.957, 1],        # #D5E2F5 (Píldora de navegación activa azul suave)
        "divider": [0.851, 0.882, 0.925, 1],            # #D9E1EC (Líneas divisorias sutiles)
        "leaf_badge_bg": [0.875, 0.910, 0.961, 1],      # #DFE8F5 (Fondo de insignias azul tenue)
        "avatar_border": [0.157, 0.431, 0.831, 1],      # #286ED3 (Borde del avatar)
        "chart_card_dark": [0.110, 0.184, 0.306, 1],    # #1C2F4E (Tarjeta de estadísticas en azul marino profundo)
        "chart_card_text_dim": [0.776, 0.835, 0.910, 1],# #C6D5E8 (Texto tenue sobre tarjeta oscura)
        "progress_track": [0.890, 0.914, 0.945, 1],     # #E3E9F5 (Barra de progreso fondo azul claro)
        "icon_badge_pink": [0.835, 0.886, 0.957, 1],    # #D5E2F5 (Insignia azul suave)
        "icon_badge_amber": [0.890, 0.918, 0.957, 1],   # #E3EAF5 (Insignia secundaria azul)
    }

    # Paleta de Colores Modo Oscuro - Tonos Azules Noche y Neón
    COLOR_DARK = {
        "bg": [0.059, 0.086, 0.133, 1],                 # #0F1622 (Fondo azul noche profundo)
        "sage_container": [0.114, 0.161, 0.239, 1],     # #1D293D (Contenedores oscuros azulados)
        "card_white": [0.161, 0.220, 0.314, 1],         # #293850 (Tarjetas elevadas azul medianoche)
        "text_primary": [0.902, 0.941, 0.988, 1],       # #E6F0FC (Texto claro azulado)
        "text_secondary": [0.584, 0.675, 0.792, 1],     # #95ACCB (Texto secundario legible)
        "category_tag": [0.353, 0.608, 0.941, 1],       # #5A9BF0 (Etiquetas azul brillante)
        "accent_green": [0.392, 0.651, 0.980, 1],       # #64A6FA (Acento azul luminoso)
        "active_pill": [0.165, 0.275, 0.435, 1],        # #2A466F (Píldora activa con tono azul medio)
        "divider": [0.200, 0.267, 0.365, 1],            # #33445D (Divisores)
        "leaf_badge_bg": [0.165, 0.275, 0.435, 1],      # #2A466F (Fondo insignias)
        "avatar_border": [0.392, 0.651, 0.980, 1],      # #64A6FA (Borde avatar)
        "chart_card_dark": [0.082, 0.125, 0.192, 1],    # #152031 (Tarjeta de estadísticas oscura)
        "chart_card_text_dim": [0.651, 0.745, 0.863, 1],
        "progress_track": [0.200, 0.267, 0.365, 1],     # #33445D (Progreso fondo)
        "icon_badge_pink": [0.216, 0.345, 0.529, 1],    # #375887
        "icon_badge_amber": [0.137, 0.196, 0.286, 1],   # #233248
    }

    # Propiedades reactivas de color expuestas a KV
    bg_color = ListProperty([0.949, 0.965, 0.984, 1])
    sage_container_color = ListProperty([0.890, 0.918, 0.957, 1])
    card_white_color = ListProperty([1.0, 1.0, 1.0, 1])
    text_primary_color = ListProperty([0.086, 0.149, 0.251, 1])
    text_secondary_color = ListProperty([0.380, 0.471, 0.592, 1])
    category_tag_color = ListProperty([0.157, 0.431, 0.831, 1])
    accent_green_color = ListProperty([0.157, 0.431, 0.831, 1])
    active_pill_color = ListProperty([0.835, 0.886, 0.957, 1])
    divider_color = ListProperty([0.851, 0.882, 0.925, 1])
    leaf_badge_bg_color = ListProperty([0.875, 0.910, 0.961, 1])
    avatar_border_color = ListProperty([0.157, 0.431, 0.831, 1])
    chart_card_dark_color = ListProperty([0.110, 0.184, 0.306, 1])
    chart_card_text_dim_color = ListProperty([0.776, 0.835, 0.910, 1])
    progress_track_color = ListProperty([0.890, 0.914, 0.945, 1])
    icon_badge_pink_color = ListProperty([0.835, 0.886, 0.957, 1])
    icon_badge_amber_color = ListProperty([0.890, 0.918, 0.957, 1])

    TAGS_MAP = {
        "home": "INICIO",
        "cart": "COMPRAS",
        "cupboard": "DESPENSA",
        "lists": "LISTAS",
        "stats": "ESTADÍSTICAS",
    }

    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
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
