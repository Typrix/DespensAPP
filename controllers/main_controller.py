# -*- coding: utf-8 -*-
"""
Controlador Principal de DespensAPP (MainController).
Orquesta los modelos de datos, persistencia y sub-controladores funcionales,
sirviendo como puente entre las Vistas Kivy y el dominio de negocio.
"""

from typing import Dict, Any, Optional

from models.database import DatabaseManager
from controllers.auth_controller import AuthController
from controllers.analytics_controller import AnalyticsController
from controllers.sync_controller import SyncController
from controllers.cart_controller import CartController
from controllers.pantry_controller import PantryController
from controllers.list_controller import ListController
from controllers.notification_controller import NotificationController
from controllers.remote_config_controller import RemoteConfigController


class MainController:
    """Controlador central orquestador de DespensAPP."""

    def __init__(self):
        # 1. Capa de Persistencia (Model)
        self.db = DatabaseManager()

        # 2. Controladores de Servicios
        self.auth = AuthController(self.db)
        self.analytics = AnalyticsController(self.db)
        self.sync = SyncController(self.db)
        self.notifications = NotificationController()
        self.remote_config = RemoteConfigController()

        # 3. Controladores de Dominio
        self.cart = CartController(self.db, self.analytics)
        self.pantry = PantryController(self.db, self.analytics, self.notifications)
        self.lists = ListController(self.db, self.analytics)

    @property
    def current_user(self):
        """Retorna el usuario activo actualmente autenticado."""
        return self.auth.current_user

    def get_home_summary(self, user_id: Optional[int]) -> Dict[str, Any]:
        """Calcula el resumen de datos para la pantalla de inicio."""
        if not user_id:
            return {
                "spent_str": "$0",
                "alert_title": "Despensa",
                "alert_desc": "Inicia sesión para ver tu inventario",
                "recipe_str": "Añade alimentos para sugerir recetas",
            }

        stats = self.db.get_user_statistics(user_id)
        cart_total = stats.get("cart_total", 0.0)
        spent_str = f"${int(cart_total):,}".replace(",", ".") if cart_total > 0 else "$0"

        first_venc = stats.get("first_vencido")
        first_por_venc = stats.get("first_por_vencer")
        first_rep = stats.get("first_reponer")
        first_agot = stats.get("first_por_agotar")

        if first_venc:
            alert_title = "Alimento vencido"
            alert_desc = f"{first_venc.name} ({first_venc.expiration_status})"
        elif first_por_venc:
            alert_title = "Por caducar pronto"
            alert_desc = f"{first_por_venc.name} ({first_por_venc.expiration_status})"
        elif first_rep:
            alert_title = "Por reponer urgente"
            alert_desc = f"{first_rep.name} (Stock en 0 {first_rep.unit})"
        elif first_agot:
            alert_title = "Por agotarse pronto"
            alert_desc = f"{first_agot.name} ({first_agot.formatted_quantity})"
        elif stats.get("pantry_items_count", 0) > 0:
            alert_title = "Despensa al día"
            alert_desc = f"{stats.get('suficiente_count', 0)} productos con buen stock"
        else:
            alert_title = "Despensa vacía"
            alert_desc = "Agrega productos a tu inventario"

        return {
            "spent_str": spent_str,
            "alert_title": alert_title,
            "alert_desc": alert_desc,
            "recipe_str": stats.get("suggested_recipe", "Añade alimentos para sugerir recetas"),
        }

    def get_stats_summary(self, user_id: Optional[int]) -> Dict[str, Any]:
        """Calcula las métricas de gasto, ranking y alertas para la pantalla de estadísticas."""
        if not user_id:
            return {
                "spent_str": "$0",
                "spent_sub": "Sin gastos registrados",
                "products_str": "0",
                "purchases_str": "0 listas",
                "p1_name": "Sin registrar", "p1_lbl": "0 veces", "p1_pct": 0.0,
                "p2_name": "Sin registrar", "p2_lbl": "0 veces", "p2_pct": 0.0,
                "p3_name": "Sin registrar", "p3_lbl": "0 veces", "p3_pct": 0.0,
                "status_title": "Bienvenido",
                "status_desc": "Inicia sesión para ver estadísticas reales de tu despensa.",
            }

        stats = self.db.get_user_statistics(user_id)
        cart_total = stats.get("cart_total", 0.0)

        spent_str = f"${int(cart_total):,}".replace(",", ".") if cart_total > 0 else "$0"
        spent_sub = f"En {stats.get('cart_items_count', 0)} producto(s) en lista" if cart_total > 0 else "Sin gastos registrados"

        total_p = stats.get("pantry_items_count", 0)
        products_str = str(total_p)
        list_cnt = stats.get("shopping_lists_count", 0)
        purchases_str = f"En {list_cnt} lista(s) de compras" if list_cnt > 0 else "Sin listas creadas"

        top = stats.get("top_products", [])
        p1 = top[0] if len(top) >= 1 else {"name": "Sin registrar", "count_lbl": "0 veces", "percent": 0.0}
        p2 = top[1] if len(top) >= 2 else {"name": "Sin registrar", "count_lbl": "0 veces", "percent": 0.0}
        p3 = top[2] if len(top) >= 3 else {"name": "Sin registrar", "count_lbl": "0 veces", "percent": 0.0}

        if stats.get("reponer_count", 0) > 0:
            status_title = f"{stats.get('reponer_count')} producto(s) por reponer"
            status_desc = "Revisa tu despensa y agrégalos a tu carrito de compras."
        elif stats.get("por_agotar_count", 0) > 0:
            status_title = f"{stats.get('por_agotar_count')} producto(s) por agotarse"
            status_desc = "Queda poco stock de algunos alimentos básicos."
        elif total_p > 0:
            status_title = "Despensa abastecida"
            status_desc = f"Tus {total_p} alimentos se encuentran en niveles óptimos."
        else:
            status_title = "Empieza tu despensa"
            status_desc = "Agrega alimentos para monitorear tu consumo y alertas."

        return {
            "spent_str": spent_str,
            "spent_sub": spent_sub,
            "products_str": products_str,
            "purchases_str": purchases_str,
            "p1_name": p1["name"], "p1_lbl": p1["count_lbl"], "p1_pct": p1["percent"],
            "p2_name": p2["name"], "p2_lbl": p2["count_lbl"], "p2_pct": p2["percent"],
            "p3_name": p3["name"], "p3_lbl": p3["count_lbl"], "p3_pct": p3["percent"],
            "status_title": status_title,
            "status_desc": status_desc,
        }
