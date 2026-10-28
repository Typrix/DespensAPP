# -*- coding: utf-8 -*-
"""
Paquete de Controladores (Controllers) para DespensAPP.
Expone el orquestador principal y los controladores especializados de cada módulo.
"""

from controllers.auth_controller import AuthController, AuthManager
from controllers.analytics_controller import AnalyticsController, AnalyticsManager
from controllers.sync_controller import SyncController, SyncManager
from controllers.cart_controller import CartController
from controllers.pantry_controller import PantryController
from controllers.list_controller import ListController
from controllers.notification_controller import NotificationController
from controllers.remote_config_controller import RemoteConfigController
from controllers.main_controller import MainController

__all__ = [
    "MainController",
    "RemoteConfigController",
    "AuthController",
    "AuthManager",
    "AnalyticsController",
    "AnalyticsManager",
    "SyncController",
    "SyncManager",
    "CartController",
    "PantryController",
    "ListController",
    "NotificationController",
]
