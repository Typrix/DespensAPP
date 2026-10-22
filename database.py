# -*- coding: utf-8 -*-
"""
Módulo de compatibilidad para la base de datos de DespensAPP.
Reexporta DatabaseManager y las constantes de conexión desde models/database.py.
"""

from models.database import (
    DatabaseManager,
    CONFIG_PATH,
    LOCAL_DB_PATH,
)

__all__ = [
    "DatabaseManager",
    "CONFIG_PATH",
    "LOCAL_DB_PATH",
]
