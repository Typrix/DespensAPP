# -*- coding: utf-8 -*-
"""
Módulo de compatibilidad para el gestor de sincronización de DespensAPP.
Reexporta SyncManager (SyncController) desde controllers/sync_controller.py.
"""

from controllers.sync_controller import SyncController, SyncManager

__all__ = [
    "SyncController",
    "SyncManager",
]
