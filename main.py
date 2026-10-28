# -*- coding: utf-8 -*-
# ========================================================
# DespensAPP - Aplicación de Gestión de Despensa y Compras
# ========================================================

from kivy.config import Config
Config.set("graphics", "height", "780")
Config.set("graphics", "width", "390")
Config.set("graphics", "resizable", "False")

from kivymd.app import MDApp
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.widget import Widget
from kivy.properties import (
    BooleanProperty,
    StringProperty,
    NumericProperty,
    ListProperty,
)
from kivy.graphics import Color, Rectangle

from models import DatabaseManager
from controllers import (
    MainController,
    AuthController,
    AnalyticsController,
    SyncController,
    NotificationController,
)
from views import (
    COLOR_LIGHT,
    COLOR_DARK,
    TAGS_MAP,
    CustomProgressBar,
    BottomNavButton,
    CartItemRow,
    PantryItemRow,
    ShoppingListCard,
    AddCircleButton,
    AvatarCircleButton,
    ProfileModalView,
    RemoteConfigBanner,
    AddCartItemModal,
    AddPantryItemModal,
    PantryItemDetailModal,
    AddShoppingListModal,
    AuthModal,
)


class MainApp(MDApp):
    """Aplicación principal de DespensAPP con arquitectura desacoplada y reactiva."""

    # Control de Pantalla y Estado
    current_screen_name = StringProperty("home")
    screen_header_tag = StringProperty("INICIO")
    modo_oscuro = BooleanProperty(False)

    # Estado de la Pantalla de Carga (Splash Screen)
    splash_progress = NumericProperty(0.0)
    splash_status_text = StringProperty("Iniciando DespensAPP...")

    # Datos Dinámicos del Usuario
    user_name_str = StringProperty("Sofía Martínez")
    user_email_str = StringProperty("sofia@despensapp.com")
    user_initials_str = StringProperty("SO")
    user_greeting_str = StringProperty("Bienvenida, Sofía")

    # Datos Dinámicos del Carrito
    total_carrito_str = StringProperty("$0")

    # Datos Dinámicos de la Pantalla de Inicio
    home_spent_str = StringProperty("$0")
    home_alert_title_str = StringProperty("Despensa")
    home_alert_desc_str = StringProperty("Sin productos")
    home_recipe_str = StringProperty("Añade alimentos para sugerir recetas")

    # Datos Dinámicos de Estadísticas
    stats_spent_str = StringProperty("$0")
    stats_spent_sub = StringProperty("Sin gastos registrados")
    stats_products_str = StringProperty("0")
    stats_purchases_str = StringProperty("0 listas")
    stats_p1_name = StringProperty("Sin registrar")
    stats_p1_lbl = StringProperty("0 veces")
    stats_p1_pct = NumericProperty(0.0)
    stats_p2_name = StringProperty("Sin registrar")
    stats_p2_lbl = StringProperty("0 veces")
    stats_p2_pct = NumericProperty(0.0)
    stats_p3_name = StringProperty("Sin registrar")
    stats_p3_lbl = StringProperty("0 veces")
    stats_p3_pct = NumericProperty(0.0)
    stats_status_title = StringProperty("Bienvenido")
    stats_status_desc = StringProperty("Agrega alimentos para monitorear tu despensa.")

    # Configuración Remota (Remote Config JSON)
    remote_banner_visible = BooleanProperty(False)
    remote_banner_title = StringProperty("Configuración Remota")
    remote_banner_message = StringProperty("")
    remote_banner_badge = StringProperty("REMOTO")
    remote_banner_type = StringProperty("promo")

    # Referencias auxiliares
    profile_modal = None
    analytics = None
    notifications = None
    remote_config = None

    # Paletas de color centralizadas
    COLOR_LIGHT = COLOR_LIGHT
    COLOR_DARK = COLOR_DARK
    TAGS_MAP = TAGS_MAP

    # Propiedades reactivas de color (enlazadas a las plantillas KV)
    bg_color = ListProperty(COLOR_LIGHT["bg"])
    sage_container_color = ListProperty(COLOR_LIGHT["sage_container"])
    card_white_color = ListProperty(COLOR_LIGHT["card_white"])
    text_primary_color = ListProperty(COLOR_LIGHT["text_primary"])
    text_secondary_color = ListProperty(COLOR_LIGHT["text_secondary"])
    category_tag_color = ListProperty(COLOR_LIGHT["category_tag"])
    accent_green_color = ListProperty(COLOR_LIGHT["accent_green"])
    active_pill_color = ListProperty(COLOR_LIGHT["active_pill"])
    divider_color = ListProperty(COLOR_LIGHT["divider"])
    leaf_badge_bg_color = ListProperty(COLOR_LIGHT["leaf_badge_bg"])
    avatar_border_color = ListProperty(COLOR_LIGHT["avatar_border"])
    chart_card_dark_color = ListProperty(COLOR_LIGHT["chart_card_dark"])
    chart_card_text_dim_color = ListProperty(COLOR_LIGHT["chart_card_text_dim"])
    progress_track_color = ListProperty(COLOR_LIGHT["progress_track"])
    icon_badge_pink_color = ListProperty(COLOR_LIGHT["icon_badge_pink"])
    icon_badge_amber_color = ListProperty(COLOR_LIGHT["icon_badge_amber"])
    input_text_color = ListProperty(COLOR_LIGHT.get("input_text", [0.0, 0.0, 0.0, 1.0]))
    input_placeholder_color = ListProperty(COLOR_LIGHT.get("input_placeholder", [0.55, 0.60, 0.68, 1.0]))

    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        self._aplicar_tema(False)
        return None

    def on_stop(self):
        """Cierra la sesión de telemetría y guarda la duración total."""
        if hasattr(self, 'analytics') and self.analytics:
            self.analytics.end_session()

    def on_start(self):
        """Inicia la secuencia de bienvenida con pantalla de carga progresiva."""
        if self.root:
            self.root.current = "splash"

        self.splash_progress = 0.05
        self.splash_status_text = "Iniciando DespensAPP..."
        Clock.schedule_once(self._splash_paso_bd, 0.25)

    def _splash_paso_bd(self, dt):
        """Paso 1: Conexión con base de datos, autenticación y telemetría mediante MainController."""
        self.splash_progress = 0.35
        self.splash_status_text = "Conectando con la base de datos..."
        self.controller = MainController()
        self.db = self.controller.db
        self.auth = self.controller.auth
        self.analytics = self.controller.analytics
        self.sync = self.controller.sync
        self.cart_ctrl = self.controller.cart
        self.pantry_ctrl = self.controller.pantry
        self.list_ctrl = self.controller.lists
        self.notifications = getattr(self.controller, "notifications", None)
        self.remote_config = getattr(self.controller, "remote_config", None)
        self.actualizar_config_remota()
        user_id = self.auth.current_user.id if self.auth.current_user else None
        self.analytics.start_session(user_id=user_id, platform="Windows")
        Clock.schedule_once(self._splash_paso_datos, 0.35)

    def _splash_paso_datos(self, dt):
        """Paso 2: Sincronización de usuario e inventario."""
        self.splash_progress = 0.70
        self.splash_status_text = "Sincronizando inventario y compras..."

        if self.auth.is_authenticated():
            self._sincronizar_datos_usuario()
            if hasattr(self, 'sync') and self.sync and self.db.is_mysql:
                self.ejecutar_sincronizacion(self.auth.current_user.email)
            self.cargar_todo()

        Clock.schedule_once(self._splash_paso_final, 0.35)

    def _splash_paso_final(self, dt):
        """Paso 3: Carga completa al 100%."""
        self.splash_progress = 1.0
        self.splash_status_text = "¡Todo listo!"
        Clock.schedule_once(self._splash_completar, 0.30)

    def _splash_completar(self, dt):
        """Transición fluida a la aplicación principal."""
        if self.root:
            self.root.current = "main_app"

        # Programar chequeo periódico de alertas de despensa cada 10 minutos
        Clock.schedule_interval(self._verificar_notificaciones_periodicas, 600)

        if self.auth.is_authenticated():
            self.cambiar_pantalla(self.current_screen_name)
        else:
            self._sincronizar_datos_usuario()
            self.abrir_modal_auth(can_cancel=False)

    def _sincronizar_datos_usuario(self):
        """Actualiza las variables de perfil con el usuario activo y notifica a telemetría."""
        user = self.auth.current_user
        if user:
            self.user_name_str = user.name
            self.user_email_str = user.email
            self.user_initials_str = user.avatar_initials
            first_name = user.name.split()[0] if user.name else "Usuario"
            self.user_greeting_str = f"Bienvenida, {first_name}"
            if hasattr(self, 'analytics') and self.analytics:
                self.analytics.update_user(user.id)
        else:
            self.user_name_str = "Iniciar Sesión"
            self.user_email_str = "cuenta@despensapp.com"
            self.user_initials_str = "??"
            self.user_greeting_str = "Bienvenido a DespensAPP"

    def actualizar_config_remota(self):
        """Carga o refresca la configuración remota y actualiza el estado reactivo de la UI."""
        if not hasattr(self, "remote_config") or not self.remote_config:
            return
        self.remote_config.fetch_config()
        banner_info = self.remote_config.get_banner_info()
        self.remote_banner_visible = self.remote_config.is_banner_enabled()
        self.remote_banner_title = banner_info.get("title", "Configuración Remota")
        self.remote_banner_message = banner_info.get("message", "")
        self.remote_banner_badge = banner_info.get("badge_text", "REMOTO")
        self.remote_banner_type = banner_info.get("type", "promo")

    def get_container(self, name: str):
        """Busca un widget contenedor por su ID en el árbol raíz o dentro de las pantallas activas."""
        if not self.root:
            return None
        if name in self.root.ids:
            return self.root.ids[name]
        sm = self.root.ids.get("screen_manager")
        if sm:
            for scr in sm.screens:
                if name in scr.ids:
                    return scr.ids[name]
        return None

    def cambiar_pantalla(self, name_option):
        """Cambia suavemente a la pantalla seleccionada y registra tiempo en telemetría."""
        self.current_screen_name = name_option
        self.screen_header_tag = self.TAGS_MAP.get(name_option, "DESPENSAPP")

        if hasattr(self, 'analytics') and self.analytics:
            self.analytics.track_screen(name_option)

        sm = self.root.ids.get("screen_manager") if self.root else None
        if sm:
            sm.current = name_option

        # Actualizar vistas dinámicas al entrar
        if name_option == "home":
            self.actualizar_inicio()
        elif name_option == "stats":
            self.actualizar_estadisticas()

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
        """Aplica la paleta de colores reactiva correspondiente."""
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
        self.input_text_color = paleta.get("input_text", [0.0, 0.0, 0.0, 1.0])
        self.input_placeholder_color = paleta.get("input_placeholder", [0.55, 0.60, 0.68, 1.0])

    # ----------------------------------------------------
    # Carga y Actualización Reactiva de Datos
    # ----------------------------------------------------
    def cargar_todo(self):
        """Recarga todas las secciones desde la base de datos."""
        self.cargar_carrito()
        self.cargar_despensa()
        self.cargar_listas()
        self.actualizar_inicio()
        self.actualizar_estadisticas()

    def _crear_divisor(self):
        """Crea una línea divisoria sutil para mantener el diseño original."""
        w = Widget(size_hint_y=None, height="1dp")
        with w.canvas:
            Color(rgba=self.divider_color)
            w.rect = Rectangle(pos=w.pos, size=w.size)
        w.bind(pos=lambda inst, val: setattr(inst.rect, 'pos', val),
               size=lambda inst, val: setattr(inst.rect, 'size', val))
        return w

    def cargar_carrito(self):
        """Carga y renderiza los productos del carrito con divisores."""
        container = self.get_container("cart_items_container")

        if not self.auth.current_user:
            self.total_carrito_str = "$0"
            if container:
                container.clear_widgets()
            return

        items = self.db.get_cart_items(self.auth.current_user.id)
        total = sum(it.price for it in items if not it.is_checked)
        self.total_carrito_str = f"${int(total):,}".replace(",", ".")

        if not container:
            return

        container.clear_widgets()
        for idx, it in enumerate(items):
            row = CartItemRow(
                item_id=it.id,
                title=it.title,
                subtitle=it.subtitle,
                price_val=it.price,
                price_str=it.formatted_price,
                checked=it.is_checked,
            )
            container.add_widget(row)
            if idx < len(items) - 1:
                container.add_widget(self._crear_divisor())

    def cargar_despensa(self):
        """Carga y renderiza los productos de la despensa con divisores."""
        container = self.get_container("pantry_items_container")
        if not container:
            return

        container.clear_widgets()
        if not self.auth.current_user:
            return

        items = self.db.get_pantry_items(self.auth.current_user.id)

        # Evaluar alertas automáticas de caducidad y stock mediante Plyer
        if hasattr(self, 'notifications') and self.notifications:
            self.notifications.check_pantry_items(items)

        for idx, it in enumerate(items):
            row = PantryItemRow(
                item_id=it.id,
                name=it.name,
                quantity_str=it.formatted_quantity,
                status_str=it.status,
                status_color=it.status_text_color,
                expiration_str=it.expiration_status,
                expiration_color=it.expiration_text_color,
                raw_expiration=it.expiration_date or "",
            )
            container.add_widget(row)
            if idx < len(items) - 1:
                container.add_widget(self._crear_divisor())

    def cargar_listas(self):
        """Carga y renderiza las tarjetas de listas de compras."""
        container = self.get_container("shopping_lists_container")
        if not container:
            return

        container.clear_widgets()
        if not self.auth.current_user:
            return

        lists = self.db.get_shopping_lists(self.auth.current_user.id)

        for lst in lists:
            sub = f"{lst.pending_count} pendientes · {lst.items_count} productos"
            card = ShoppingListCard(
                list_id=lst.id,
                list_name=lst.name,
                icon_name=lst.icon_name,
                icon_color_rgba=lst.color_rgba,
                badge_bg_color=lst.badge_bg_rgba,
                info_subtitle=sub,
            )
            container.add_widget(card)

    def actualizar_inicio(self):
        """Actualiza la pantalla de inicio delegando el cálculo al controlador MVC."""
        self._sincronizar_datos_usuario()
        uid = self.auth.current_user.id if (hasattr(self, 'auth') and self.auth and self.auth.current_user) else None
        summary = self.controller.get_home_summary(uid) if hasattr(self, 'controller') else {}

        self.home_spent_str = summary.get("spent_str", "$0")
        self.home_alert_title_str = summary.get("alert_title", "Despensa")
        self.home_alert_desc_str = summary.get("alert_desc", "Sin productos")
        self.home_recipe_str = summary.get("recipe_str", "Añade alimentos para sugerir recetas")

    def actualizar_estadisticas(self):
        """Calcula dinámicamente las métricas de estadísticas delegando en el controlador MVC."""
        uid = self.auth.current_user.id if (hasattr(self, 'auth') and self.auth and self.auth.current_user) else None
        stats = self.controller.get_stats_summary(uid) if hasattr(self, 'controller') else {}

        self.stats_spent_str = stats.get("spent_str", "$0")
        self.stats_spent_sub = stats.get("spent_sub", "Sin gastos registrados")
        self.stats_products_str = stats.get("products_str", "0")
        self.stats_purchases_str = stats.get("purchases_str", "0 listas")

        self.stats_p1_name = stats.get("p1_name", "Sin registrar")
        self.stats_p1_lbl = stats.get("p1_lbl", "0 veces")
        self.stats_p1_pct = stats.get("p1_pct", 0.0)

        self.stats_p2_name = stats.get("p2_name", "Sin registrar")
        self.stats_p2_lbl = stats.get("p2_lbl", "0 veces")
        self.stats_p2_pct = stats.get("p2_pct", 0.0)

        self.stats_p3_name = stats.get("p3_name", "Sin registrar")
        self.stats_p3_lbl = stats.get("p3_lbl", "0 veces")
        self.stats_p3_pct = stats.get("p3_pct", 0.0)

        self.stats_status_title = stats.get("status_title", "Bienvenido")
        self.stats_status_desc = stats.get("status_desc", "Agrega alimentos para monitorear tu despensa.")

    # ----------------------------------------------------
    # Interacción: Botón '+' según Pantalla Activa
    # ----------------------------------------------------
    def accion_agregar(self):
        """Despliega el modal correspondiente a la pestaña activa."""
        if not self.auth.current_user:
            self.abrir_modal_auth(can_cancel=False)
            return

        scr = self.current_screen_name
        if scr == "cart":
            modal = AddCartItemModal(callback_add=self.agregar_item_carrito)
            modal.open()
        elif scr == "cupboard":
            modal = AddPantryItemModal(callback_add=self.agregar_item_despensa)
            modal.open()
        elif scr == "lists":
            modal = AddShoppingListModal(callback_add=self.agregar_lista_compras)
            modal.open()
        else:
            modal = AddCartItemModal(callback_add=self.agregar_item_carrito)
            modal.open()

    # ----------------------------------------------------
    # Controladores CRUD (Delegados en controladores MVC)
    # ----------------------------------------------------
    def agregar_item_carrito(self, title, price, subtitle):
        if not self.auth.current_user:
            return
        if hasattr(self, 'cart_ctrl'):
            self.cart_ctrl.add_item(self.auth.current_user.id, title, price, subtitle)
        else:
            self.db.add_cart_item(self.auth.current_user.id, title, subtitle, price, 1)
        self.cargar_carrito()
        self.actualizar_inicio()
        self.actualizar_estadisticas()

    def toggle_item_carrito(self, item_id, is_checked):
        if hasattr(self, 'cart_ctrl'):
            self.cart_ctrl.toggle_item(item_id, is_checked)
        else:
            self.db.toggle_cart_item(item_id, is_checked)
        self.cargar_carrito()
        self.actualizar_inicio()
        self.actualizar_estadisticas()

    def eliminar_item_carrito(self, item_id):
        if hasattr(self, 'cart_ctrl'):
            self.cart_ctrl.delete_item(item_id)
        else:
            self.db.delete_cart_item(item_id)
        self.cargar_carrito()
        self.actualizar_inicio()
        self.actualizar_estadisticas()

    def agregar_item_despensa(self, name, quantity, unit, threshold, expiration_date=None):
        if not self.auth.current_user:
            return
        if hasattr(self, 'pantry_ctrl'):
            self.pantry_ctrl.add_item(self.auth.current_user.id, name, quantity, unit, threshold, expiration_date)
        else:
            self.db.add_pantry_item(self.auth.current_user.id, name, quantity, unit, threshold, "General", expiration_date)
        self.cargar_despensa()
        self.actualizar_inicio()
        self.actualizar_estadisticas()

    def actualizar_vencimiento_despensa(self, item_id, new_expiration_date):
        if hasattr(self, 'pantry_ctrl'):
            self.pantry_ctrl.update_expiration(item_id, new_expiration_date)
        else:
            self.db.update_pantry_expiration(item_id, new_expiration_date)
        self.cargar_despensa()
        self.actualizar_inicio()
        self.actualizar_estadisticas()

    def cambiar_cantidad_despensa(self, item_id, delta):
        if hasattr(self, 'pantry_ctrl'):
            self.pantry_ctrl.change_quantity(item_id, delta)
        else:
            self.db.update_pantry_quantity(item_id, delta)
        self.cargar_despensa()
        self.actualizar_inicio()
        self.actualizar_estadisticas()

    def eliminar_item_despensa(self, item_id):
        if hasattr(self, 'pantry_ctrl'):
            self.pantry_ctrl.delete_item(item_id)
        else:
            self.db.delete_pantry_item(item_id)
        self.cargar_despensa()
        self.actualizar_inicio()
        self.actualizar_estadisticas()

    def agregar_lista_compras(self, name, color_hex, initial_items=""):
        if not self.auth.current_user:
            return
        if hasattr(self, 'list_ctrl'):
            self.list_ctrl.add_list(self.auth.current_user.id, name, color_hex, initial_items)
        else:
            new_list_id = self.db.add_shopping_list(self.auth.current_user.id, name, color_hex, "clipboard-text-outline")
            if new_list_id and initial_items:
                items_list = [it.strip() for it in initial_items.replace("\n", ",").split(",") if it.strip()]
                for it_name in items_list:
                    self.db.add_shopping_list_item(new_list_id, it_name)
        self.cargar_listas()
        self.actualizar_estadisticas()

    def eliminar_lista_compras(self, list_id):
        if hasattr(self, 'list_ctrl'):
            self.list_ctrl.delete_list(list_id)
        else:
            self.db.delete_shopping_list(list_id)
        self.cargar_listas()
        self.actualizar_estadisticas()

    # ----------------------------------------------------
    # Controladores de Modales de Usuario y Sesión
    # ----------------------------------------------------
    def abrir_modal_auth(self, can_cancel=True):
        """Abre el diálogo de inicio de sesión o registro."""
        modal = AuthModal(
            auth_manager=self.auth,
            callback_success=self.al_autenticar_usuario,
            can_cancel=can_cancel,
        )
        modal.open()

    def al_autenticar_usuario(self, user):
        """Callback al iniciar sesión o crear cuenta."""
        if hasattr(self, 'analytics') and self.analytics:
            self.analytics.update_user(user.id)
            self.analytics.track_event("user_authenticated", metadata={"user_id": user.id, "email": user.email})
        self._sincronizar_datos_usuario()
        if hasattr(self, 'sync') and self.sync and self.db.is_mysql and user:
            self.ejecutar_sincronizacion(user.email)
        self.cargar_todo()
        self.cambiar_pantalla("home")

    def ejecutar_sincronizacion(self, email: str):
        """Ejecuta la migración de datos offline a MySQL y notifica el resultado."""
        if not hasattr(self, 'sync') or not self.sync or not email:
            return
        summary = self.sync.sync_user_data(email)
        if summary.get("success") and summary.get("total", 0) > 0:
            print(f"[DespensAPP] {summary.get('message')}")

    def _verificar_notificaciones_periodicas(self, dt=None):
        """Revisa periódicamente el estado de la despensa para alertar sobre stock o vencimientos."""
        if hasattr(self, 'auth') and self.auth and self.auth.current_user:
            if hasattr(self, 'notifications') and self.notifications:
                items = self.db.get_pantry_items(self.auth.current_user.id)
                self.notifications.check_pantry_items(items)

    def cerrar_sesion_usuario(self):
        """Cierra la sesión, limpia las pantallas y exige inicio de sesión."""
        if hasattr(self, 'analytics') and self.analytics:
            self.analytics.track_event("user_logout")
            self.analytics.update_user(None)
        if hasattr(self, 'notifications') and self.notifications:
            self.notifications.clear_history()
        self.cerrar_menu_perfil()
        self.auth.logout()
        self._sincronizar_datos_usuario()
        self.cargar_todo()
        self.abrir_modal_auth(can_cancel=False)


if __name__ == '__main__':
    MainApp().run()
