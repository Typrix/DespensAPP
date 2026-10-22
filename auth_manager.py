# -*- coding: utf-8 -*-
"""
Módulo de compatibilidad para el gestor de autenticación de DespensAPP.
Reexporta AuthManager (AuthController) desde controllers/auth_controller.py.
"""

from controllers.auth_controller import AuthController, AuthManager, SESSION_PATH

__all__ = [
    "AuthController",
    "AuthManager",
    "SESSION_PATH",
]
