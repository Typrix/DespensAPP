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
from controllers.purchase_controller import summarize_items, format_money
from controllers.pantry_organizer import (
    FILTER_ALL, FILTER_EXPIRING, FILTER_LOW, CATEGORY_FILTER_PREFIX,
    group_pantry, filter_counts, used_categories, restock_candidates,
)
from controllers.validators import step_for_unit
from dataclasses import replace as dc_replace
from controllers import (
    MainController,
    AuthController,
    AnalyticsController,
    SyncController,
    NotificationController,
    UndoController,
)
from views import (
    COLOR_LIGHT,
    COLOR_DARK,
    TAGS_MAP,
    CustomProgressBar,
    BottomNavButton,
    PantryItemRow,
    PantryFilterChip,
    PantrySectionHeader,
    ShoppingListCard,
    AddCircleButton,
    AvatarCircleButton,
    ProfileModalView,
    RemoteConfigBanner,
    show_undo_snackbar,
    hide_undo_snackbar,
    show_info_toast,
    EmptyState,
    PurchaseHistoryRow,
    PurchaseGroupCard,
    AddPantryItemModal,
    PantryItemDetailModal,
    AddShoppingListModal,
    AuthModal,
    CheckoutModal,
    AlertsModal,
    PurchaseHistoryModal,
    build_purchase_card,
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


    # Alertas de despensa (campana de Inicio)
    alerts_count = NumericProperty(0)
    home_alert_item_id = NumericProperty(0)

    # Historial de compras por periodo (Estadísticas)
    stats_period = StringProperty("week")
    stats_period_label = StringProperty("Última semana")
    # Textos derivados (KV no reevalúa expresiones como prop.upper(), por eso se calculan aquí)
    stats_period_tag = StringProperty("ÚLTIMA SEMANA")
    stats_spent_title = StringProperty("Gasto · última semana")
    stats_purchase_count = NumericProperty(0)  # compras del periodo (para "Ver todas")

    # Mi Despensa: búsqueda, filtro activo y reposición en bloque
    pantry_filter = StringProperty("all")
    pantry_restock_count = NumericProperty(0)
    pantry_restock_text = StringProperty("")

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
        # Cola de borrados diferidos (ventana de 4 s para "Deshacer")
        self.undo = UndoController(scheduler=Clock.schedule_once)
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        self._aplicar_tema(False)
        return None

    def on_stop(self):
        """Confirma borrados pendientes y cierra la sesión de telemetría."""
        if getattr(self, "undo", None):
            self.undo.flush()
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
        self._migrar_carrito_a_listas()
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

    def _migrar_carrito_a_listas(self):
        """Paso único: lo que quedó en el carrito antiguo vuelve a sus listas (o a 'Mi carrito')."""
        if not self.auth.current_user or not hasattr(self, 'controller'):
            return
        moved = self.controller.purchases.migrate_cart_to_lists(self.auth.current_user.id)
        if moved:
            print(f"[DespensAPP] {moved} producto(s) del carrito movidos a tus listas.")

    def cargar_despensa(self):
        """Lee la despensa de la base de datos, evalúa alertas y la dibuja ordenada por urgencia."""
        container = self.get_container("pantry_items_container")
        if not container:
            return

        container.clear_widgets()
        if not self.auth.current_user:
            self._pantry_items = []
            self.pantry_restock_count = 0
            filters = self.get_container("pantry_filters_container")
            if filters:
                filters.clear_widgets()
            return

        items = [it for it in self.db.get_pantry_items(self.auth.current_user.id)
                 if not self.is_pending_delete("pantry", it.id)]

        # Evaluar alertas automáticas de caducidad y stock mediante Plyer
        if hasattr(self, 'notifications') and self.notifications:
            self.notifications.check_pantry_items(items)

        self._pantry_items = items
        self._render_despensa()

    def _render_despensa(self):
        """Dibuja chips, botón de reponer y secciones por urgencia según búsqueda y filtro."""
        container = self.get_container("pantry_items_container")
        if not container:
            return
        container.clear_widgets()
        items = getattr(self, "_pantry_items", [])

        # Si el filtro de categoría ya no tiene productos, vuelve a "Todos"
        counts = filter_counts(items)
        if self.pantry_filter != FILTER_ALL and not counts.get(self.pantry_filter):
            self.pantry_filter = FILTER_ALL
        self._render_filtros_despensa(items, counts)

        restock = restock_candidates(items)
        self.pantry_restock_count = len(restock)
        self.pantry_restock_text = (
            f"Añadir lo que falta a una lista ({len(restock)})" if restock else "")

        if not items:
            container.add_widget(EmptyState(
                icon="cupboard-outline",
                title="Tu despensa está vacía",
                message="Registra lo que tienes en casa o finaliza una compra para llenarla.",
                action_text="Agregar producto",
                action=lambda: self.abrir_formulario("cupboard"),
            ))
            return

        sections = group_pantry(items, getattr(self, "_pantry_query", ""), self.pantry_filter)
        if not sections:
            container.add_widget(EmptyState(
                icon="magnify-close",
                title="Sin resultados",
                message="No hay productos que coincidan con la búsqueda o el filtro.",
                action_text="Limpiar filtros",
                action=self.limpiar_filtros_despensa,
            ))
            return
        for section in sections:
            container.add_widget(PantrySectionHeader(
                title=section["title"].upper(), count=len(section["items"]), dot_color=section["color"]))
            for idx, it in enumerate(section["items"]):
                container.add_widget(PantryItemRow(item=it))
                if idx < len(section["items"]) - 1:
                    container.add_widget(self._crear_divisor())

    def _render_filtros_despensa(self, items, counts):
        """Chips: Todos, Por vencer, Por agotarse y una por categoría en uso."""
        box = self.get_container("pantry_filters_container")
        if not box:
            return
        box.clear_widgets()
        chips = [(FILTER_ALL, f"Todos {counts[FILTER_ALL]}")]
        if counts[FILTER_EXPIRING]:
            chips.append((FILTER_EXPIRING, f"Por vencer {counts[FILTER_EXPIRING]}"))
        if counts[FILTER_LOW]:
            chips.append((FILTER_LOW, f"Por agotarse {counts[FILTER_LOW]}"))
        categories = used_categories(items)
        if len(categories) > 1:  # con una sola categoría el chip no filtra nada
            for cat in categories:
                key = CATEGORY_FILTER_PREFIX + cat
                chips.append((key, f"{cat} {counts[key]}"))
        for key, text in chips:
            box.add_widget(PantryFilterChip(filter_key=key, text=text))

    def buscar_despensa(self, text):
        """Buscador de Mi Despensa (en vivo, sin consultar la base de datos)."""
        self._pantry_query = text or ""
        self._render_despensa()

    def filtrar_despensa(self, filter_key):
        """Chip de filtro: tocar el activo vuelve a 'Todos'."""
        self.pantry_filter = FILTER_ALL if filter_key == self.pantry_filter else filter_key
        self._render_despensa()

    def limpiar_filtros_despensa(self):
        self.pantry_filter = FILTER_ALL
        search = self.get_container("pantry_search_input")
        if search and search.text:
            search.text = ""  # dispara buscar_despensa
        else:
            self._pantry_query = ""
            self._render_despensa()

    def ajuste_rapido_despensa(self, row, direction):
        """
        -/+ en la fila: guarda al instante y actualiza solo esa fila; el reordenamiento
        y las alertas se aplican tras una pausa breve para no mover la lista mientras se toca.
        """
        item = row.item
        new_qty = max(0.0, round(item.quantity + direction * step_for_unit(item.unit), 3))
        if new_qty == item.quantity:
            return
        self.fijar_cantidad_despensa(item.id, new_qty)
        updated = dc_replace(item, quantity=new_qty)
        row.set_item(updated)
        items = getattr(self, "_pantry_items", [])
        self._pantry_items = [updated if it.id == item.id else it for it in items]
        if not hasattr(self, "_pantry_adjusted"):
            self._pantry_adjusted = set()
        self._pantry_adjusted.add(item.id)
        if getattr(self, "_pantry_refresh_ev", None):
            self._pantry_refresh_ev.cancel()
        self._pantry_refresh_ev = Clock.schedule_once(lambda dt: self._cerrar_ajuste_rapido(), 1.5)

    def _cerrar_ajuste_rapido(self):
        """Fin de la ráfaga de -/+: alertas una vez por producto y refresco general."""
        self._pantry_refresh_ev = None
        adjusted, self._pantry_adjusted = getattr(self, "_pantry_adjusted", set()), set()
        if hasattr(self, 'pantry_ctrl'):
            for item_id in adjusted:
                self.pantry_ctrl.check_stock_alerts(item_id)
        self._render_despensa()
        self.actualizar_inicio()
        self.actualizar_estadisticas()

    def reponer_todo_despensa(self):
        """Anota en 'Reponer despensa' todo lo que está por agotarse o sin stock (sin duplicar)."""
        if not self.auth.current_user:
            return
        candidates = restock_candidates(getattr(self, "_pantry_items", []))
        if not candidates:
            return
        purchases = self.controller.purchases
        list_id = purchases.find_or_create_list(self.auth.current_user.id, "Reponer despensa", "#F59E0B")
        added = purchases.add_many_to_list(list_id, candidates)
        self.cargar_listas()
        if added:
            show_info_toast(f"{added} producto(s) anotados en Reponer despensa")
        else:
            show_info_toast("Todo lo que falta ya estaba en Reponer despensa")

    def cargar_listas(self):
        """Carga y renderiza las tarjetas de listas de compras."""
        container = self.get_container("shopping_lists_container")
        if not container:
            return

        container.clear_widgets()
        if not self.auth.current_user:
            return

        lists = [lst for lst in self.db.get_shopping_lists(self.auth.current_user.id)
                 if not self.is_pending_delete("list", lst.id)]
        if not lists:
            container.add_widget(EmptyState(
                icon="clipboard-text-outline",
                title="Aún no tienes listas",
                message="Crea una lista, anota lo que necesitas y táchalo mientras compras.",
                action_text="Crear lista",
                action=lambda: self.abrir_formulario("lists"),
            ))
            return

        for lst in lists:
            items = [it for it in self.db.get_shopping_list_items(lst.id)
                     if not self.is_pending_delete("list_item", it.id)]
            summary = summarize_items(items)
            if not items:
                sub = "Lista vacía"
            elif summary["in_cart"] > 0:
                sub = f"{summary['pending']} por comprar · {format_money(summary['in_cart'])} en el carro"
            else:
                sub = f"{summary['pending']} por comprar · {summary['checked']} en el carro"
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
        self.home_alert_item_id = summary.get("alert_item_id", 0) or 0
        self.alerts_count = len(self.controller.get_alerts(uid)) if hasattr(self, 'controller') else 0

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
        self.cargar_historial_compras()

    # ----------------------------------------------------
    # Historial de Compras por Periodo (Semana / Mes / Año)
    # ----------------------------------------------------
    def cambiar_periodo_estadisticas(self, period):
        """Cambia el periodo del historial y recalcula el gasto mostrado."""
        self.stats_period = period
        self.cargar_historial_compras()

    def cargar_historial_compras(self, max_rows=3):
        """Muestra el gasto del periodo y solo la última compra (el resto en "Ver todas")."""
        if not hasattr(self, 'controller'):
            return
        uid = self.auth.current_user.id if self.auth.current_user else None
        data = self.controller.purchases.get_spending(uid, self.stats_period)
        self.stats_period_label = data["label"]
        self.stats_period_tag = data["label"].upper()
        self.stats_spent_title = f"Gasto · {data['label'].lower()}"
        self.stats_spent_str = data["total_str"]
        count = data["count"]
        self.stats_spent_sub = (f"{count} producto(s) comprados" if count else "Sin compras en este periodo")

        container = self.get_container("purchase_history_container")
        if not container:
            return
        container.clear_widgets()
        self._stats_spending = data
        self.stats_purchase_count = len(data["groups"])
        if not data["records"]:
            container.add_widget(EmptyState(
                icon="receipt-text-outline",
                title="Sin compras registradas",
                message="Cuando finalices una compra desde una lista, aparecerá aquí.",
                action_text="Ir a mis listas",
                action=lambda: self.cambiar_pantalla("lists"),
            ))
            return
        # Solo la compra más reciente, resumida; tocarla abre el historial completo
        card = build_purchase_card(data["groups"][0], max_rows=max_rows, tappable=True)
        card.bind(on_release=lambda *_: self.ver_todas_compras())
        container.add_widget(card)

    def ver_todas_compras(self):
        """Abre el historial completo del periodo elegido en Estadísticas."""
        data = getattr(self, "_stats_spending", None)
        if data is None:
            uid = self.auth.current_user.id if self.auth.current_user else None
            data = self.controller.purchases.get_spending(uid, self.stats_period)
        PurchaseHistoryModal(spending=data).open()

    def abrir_historial_compras(self):
        """Desde Inicio: abre el historial de la última semana sin salir de Inicio."""
        uid = self.auth.current_user.id if self.auth.current_user else None
        PurchaseHistoryModal(spending=self.controller.purchases.get_spending(uid, "week")).open()

    # ----------------------------------------------------
    # Interacción: Botón '+' según Pantalla Activa
    # ----------------------------------------------------
    def accion_agregar(self):
        """Despliega el modal correspondiente a la pestaña activa."""
        if not self.auth.current_user:
            self.abrir_modal_auth(can_cancel=False)
            return

        self.abrir_formulario(self.current_screen_name)

    def abrir_formulario(self, scr):
        """Abre el formulario de alta de la sección indicada (despensa o listas)."""
        if not self.auth.current_user:
            self.abrir_modal_auth(can_cancel=False)
            return
        if scr == "cupboard":
            modal = AddPantryItemModal(callback_add=self.agregar_item_despensa)
            modal.open()
        else:  # listas (y el '+' de Inicio): crear una lista nueva
            modal = AddShoppingListModal(callback_add=self.agregar_lista_compras)
            modal.open()

    # ----------------------------------------------------
    # Controladores CRUD (Delegados en controladores MVC)
    # ----------------------------------------------------
    def abrir_finalizar_compra(self, list_id, list_name, on_done=None):
        """Abre el resumen con los productos tachados de la lista para registrar la compra."""
        if not self.auth.current_user:
            return
        items = [it for it in self.db.get_shopping_list_items(list_id)
                 if not self.is_pending_delete("list_item", it.id)]
        rows = self.controller.purchases.build_checkout(self.auth.current_user.id, items)
        if not rows:
            show_info_toast("Tacha lo que echaste al carro para finalizar.")
            return

        def confirm(entries):
            summary = self.controller.purchases.finalize_purchase(
                self.auth.current_user.id, list_id, list_name, entries)
            self.cargar_todo()
            if on_done:
                on_done()
            detalle = []
            if summary["updated"]:
                detalle.append(f"{summary['updated']} actualizado(s)")
            if summary["created"]:
                detalle.append(f"{summary['created']} nuevo(s)")
            show_info_toast(f"Compra registrada · despensa: {', '.join(detalle)}")

        CheckoutModal(checkout_rows=rows, callback_confirm=confirm).open()

    def abrir_detalle_despensa(self, item_id):
        """Abre el detalle de un producto de la despensa (desde la lista, Inicio o alertas)."""
        item = self.db.get_pantry_item_by_id(item_id)
        if not item:
            return
        PantryItemDetailModal(
            item=item,
            callback_set_qty=self.fijar_cantidad_despensa,
            callback_finish=self.finalizar_ajuste_despensa,
            callback_delete=self.eliminar_item_despensa,
            callback_update_exp=self.actualizar_vencimiento_despensa,
            callback_add_to_list=self.anotar_despensa_en_lista,
            callback_list_options=self.opciones_listas,
            callback_update_details=self.actualizar_detalles_despensa,
        ).open()

    def actualizar_detalles_despensa(self, item_id, name, unit, min_threshold, category=None):
        """Guarda nombre, unidad, mínimo y categoría; retorna el producto actualizado."""
        updated = self.pantry_ctrl.update_details(item_id, name, unit, min_threshold, category)
        self.cargar_despensa()
        self.actualizar_inicio()
        return updated

    def opciones_listas(self):
        """(id, nombre) de las listas del usuario para el menú 'Añadir a una lista'."""
        if not self.auth.current_user:
            return []
        return [(lst.id, lst.name) for lst in self.db.get_shopping_lists(self.auth.current_user.id)
                if not self.is_pending_delete("list", lst.id)]

    def anotar_despensa_en_lista(self, item_id, list_id=None):
        """
        Anota un producto de la despensa en una lista para reponerlo.
        Sin list_id usa (o crea) la lista 'Reponer despensa'. Retorna (agregado, nombre_lista).
        """
        item = self.db.get_pantry_item_by_id(item_id)
        if not item or not self.auth.current_user:
            return False, ""
        uid = self.auth.current_user.id
        if list_id is None:
            list_id = self.controller.purchases.find_or_create_list(uid, "Reponer despensa", "#F59E0B")
        list_name = next((name for lid, name in self.opciones_listas() if lid == list_id), "tu lista")
        added = self.controller.purchases.add_pantry_item_to_list(list_id, item)
        self.cargar_listas()
        return added, list_name

    def abrir_alerta_principal(self):
        """Tarjeta de Inicio: abre el producto de la alerta más urgente o la despensa."""
        if self.home_alert_item_id:
            self.cambiar_pantalla("cupboard")
            self.abrir_detalle_despensa(self.home_alert_item_id)
        else:
            self.cambiar_pantalla("cupboard")

    def abrir_alertas(self):
        """Campana de Inicio: muestra todas las alertas de la despensa."""
        uid = self.auth.current_user.id if self.auth.current_user else None
        alerts = self.controller.get_alerts(uid) if hasattr(self, 'controller') else []

        def open_item(item_id):
            self.cambiar_pantalla("cupboard")
            self.abrir_detalle_despensa(item_id)

        AlertsModal(alerts=alerts, callback_open_item=open_item).open()

    def agregar_item_despensa(self, name, quantity, unit, threshold, expiration_date=None, category="General"):
        if not self.auth.current_user:
            return
        if hasattr(self, 'pantry_ctrl'):
            self.pantry_ctrl.add_item(self.auth.current_user.id, name, quantity, unit, threshold,
                                      expiration_date, category)
        else:
            self.db.add_pantry_item(self.auth.current_user.id, name, quantity, unit, threshold, category, expiration_date)
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

    def fijar_cantidad_despensa(self, item_id, quantity):
        """Guarda la cantidad exacta sin refrescar ni alertar (ajustes en vivo del modal)."""
        if hasattr(self, 'pantry_ctrl'):
            self.pantry_ctrl.set_quantity(item_id, quantity, notify=False)
        else:
            self.db.set_pantry_quantity(item_id, quantity)

    def finalizar_ajuste_despensa(self, item_id):
        """Al cerrar el modal de stock: evalúa alertas una vez y refresca las vistas."""
        if hasattr(self, 'pantry_ctrl'):
            self.pantry_ctrl.check_stock_alerts(item_id)
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

    def eliminar_item_despensa(self, item_id, name="Producto"):
        """Oculta el producto y lo borra tras la ventana de 'Deshacer'."""
        def commit():
            if hasattr(self, 'pantry_ctrl'):
                self.pantry_ctrl.delete_item(item_id)
            else:
                self.db.delete_pantry_item(item_id)

        def refresh():
            self.cargar_despensa()
            self.actualizar_inicio()
            self.actualizar_estadisticas()

        self.programar_borrado("pantry", item_id, f"'{name}' eliminado de la despensa", refresh, commit)

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

    def eliminar_lista_compras(self, list_id, name="Lista"):
        """Oculta la lista y la borra tras la ventana de 'Deshacer'."""
        def commit():
            if hasattr(self, 'list_ctrl'):
                self.list_ctrl.delete_list(list_id)
            else:
                self.db.delete_shopping_list(list_id)

        def refresh():
            self.cargar_listas()
            self.actualizar_estadisticas()

        self.programar_borrado("list", list_id, f"Lista '{name}' eliminada", refresh, commit)

    # ----------------------------------------------------
    # Borrado diferido con opción de "Deshacer"
    # ----------------------------------------------------
    def is_pending_delete(self, kind, item_id):
        """Indica si un elemento está oculto esperando confirmación de borrado."""
        undo = getattr(self, "undo", None)
        return bool(undo and undo.is_pending(kind, item_id))

    def programar_borrado(self, kind, item_id, message, refresh, commit=None):
        """
        Oculta el elemento al instante y muestra "Deshacer".
        Si se abre otro aviso, el borrado anterior se confirma de inmediato.
        """
        if commit is None:
            commit = self._commit_por_tipo(kind, item_id)
        self.undo.flush()
        self.undo.schedule(kind, item_id, commit, on_done=refresh)
        refresh()
        show_undo_snackbar(message, on_undo=lambda: self.undo.undo(kind, item_id),
                           duration=self.undo.delay)

    def _commit_por_tipo(self, kind, item_id):
        """Función de borrado real para tipos sin callback propio (productos de una lista)."""
        if kind == "list_item":
            if hasattr(self, 'list_ctrl'):
                return lambda: self.list_ctrl.delete_list_item(item_id)
            return lambda: self.db.delete_shopping_list_item(item_id)
        raise ValueError(f"Tipo de borrado desconocido: {kind}")

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
        if getattr(self, "undo", None):
            self.undo.flush()
        hide_undo_snackbar()
        self.auth.logout()
        self.pantry_filter = FILTER_ALL
        self._pantry_query = ""
        search = self.get_container("pantry_search_input")
        if search:
            search.text = ""
        self._sincronizar_datos_usuario()
        self.cargar_todo()
        self.abrir_modal_auth(can_cancel=False)


if __name__ == '__main__':
    MainApp().run()
