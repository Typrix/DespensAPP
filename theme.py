# -*- coding: utf-8 -*-
"""
Configuración de Temas y Paletas de Color para DespensAPP.
Centraliza las paletas cromáticas reactivas para Modo Claro y Modo Oscuro,
así como las etiquetas globales de navegación.
"""

# Paleta de Colores Modo Claro
COLOR_LIGHT = {
    "bg": [0.949, 0.965, 0.984, 1],
    "sage_container": [0.890, 0.918, 0.957, 1],
    "card_white": [1.0, 1.0, 1.0, 1],
    "text_primary": [0.086, 0.149, 0.251, 1],
    "text_secondary": [0.380, 0.471, 0.592, 1],
    "category_tag": [0.157, 0.431, 0.831, 1],
    "accent_green": [0.157, 0.431, 0.831, 1],
    "active_pill": [0.835, 0.886, 0.957, 1],
    "divider": [0.851, 0.882, 0.925, 1],
    "leaf_badge_bg": [0.875, 0.910, 0.961, 1],
    "avatar_border": [0.157, 0.431, 0.831, 1],
    "chart_card_dark": [0.110, 0.184, 0.306, 1],
    "chart_card_text_dim": [0.776, 0.835, 0.910, 1],
    "progress_track": [0.890, 0.914, 0.945, 1],
    "icon_badge_pink": [0.835, 0.886, 0.957, 1],
    "icon_badge_amber": [0.890, 0.918, 0.957, 1],
    "input_text": [0.0, 0.0, 0.0, 1.0],
    "input_placeholder": [0.55, 0.60, 0.68, 1.0],
}

# Paleta de Colores Modo Oscuro
COLOR_DARK = {
    "bg": [0.059, 0.086, 0.133, 1],
    "sage_container": [0.114, 0.161, 0.239, 1],
    "card_white": [0.161, 0.220, 0.314, 1],
    "text_primary": [0.902, 0.941, 0.988, 1],
    "text_secondary": [0.584, 0.675, 0.792, 1],
    "category_tag": [0.353, 0.608, 0.941, 1],
    "accent_green": [0.392, 0.651, 0.980, 1],
    "active_pill": [0.165, 0.275, 0.435, 1],
    "divider": [0.200, 0.267, 0.365, 1],
    "leaf_badge_bg": [0.165, 0.275, 0.435, 1],
    "avatar_border": [0.392, 0.651, 0.980, 1],
    "chart_card_dark": [0.082, 0.125, 0.192, 1],
    "chart_card_text_dim": [0.651, 0.745, 0.863, 1],
    "progress_track": [0.200, 0.267, 0.365, 1],
    "icon_badge_pink": [0.216, 0.345, 0.529, 1],
    "icon_badge_amber": [0.137, 0.196, 0.286, 1],
    "input_text": [0.95, 0.97, 1.0, 1.0],
    "input_placeholder": [0.45, 0.52, 0.62, 1.0],
}

# Mapeo de Etiquetas de Encabezado por Pantalla
TAGS_MAP = {
    "home": "INICIO",
    "cart": "COMPRAS",
    "cupboard": "DESPENSA",
    "lists": "LISTAS",
    "stats": "ESTADÍSTICAS",
}
