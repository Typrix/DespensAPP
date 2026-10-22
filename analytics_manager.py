# -*- coding: utf-8 -*-
"""
Módulo de compatibilidad para el gestor de analítica de DespensAPP.
Reexporta AnalyticsManager (AnalyticsController) desde controllers/analytics_controller.py.
"""

from controllers.analytics_controller import AnalyticsController, AnalyticsManager

__all__ = [
    "AnalyticsController",
    "AnalyticsManager",
]
