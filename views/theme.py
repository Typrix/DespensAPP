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
    "text_secondary": [0.298, 0.376, 0.490, 1],
    "category_tag": [0.122, 0.373, 0.761, 1],
    "accent_green": [0.122, 0.373, 0.761, 1],
    # Relleno de botones principales (texto blanco encima)
    "accent_fill": [0.122, 0.373, 0.761, 1],
    "active_pill": [0.835, 0.886, 0.957, 1],
    "divider": [0.851, 0.882, 0.925, 1],
    "leaf_badge_bg": [0.875, 0.910, 0.961, 1],
    "avatar_border": [0.122, 0.373, 0.761, 1],
    "chart_card_dark": [0.110, 0.184, 0.306, 1],
    "chart_card_text_dim": [0.776, 0.835, 0.910, 1],
    "progress_track": [0.890, 0.914, 0.945, 1],
    "icon_badge_pink": [0.835, 0.886, 0.957, 1],
    "icon_badge_amber": [0.890, 0.918, 0.957, 1],
    "input_text": [0.0, 0.0, 0.0, 1.0],
    "input_placeholder": [0.431, 0.482, 0.561, 1.0],
}

# Paleta de Colores Modo Oscuro
COLOR_DARK = {
    "bg": [0.059, 0.086, 0.133, 1],
    "sage_container": [0.114, 0.161, 0.239, 1],
    "card_white": [0.161, 0.220, 0.314, 1],
    "text_primary": [0.902, 0.941, 0.988, 1],
    "text_secondary": [0.584, 0.675, 0.792, 1],
    "category_tag": [0.478, 0.698, 1.0, 1],
    "accent_green": [0.478, 0.698, 1.0, 1],
    # En oscuro el acento es claro: el relleno usa un azul más profundo para que el texto blanco se lea
    "accent_fill": [0.184, 0.435, 0.816, 1],
    "active_pill": [0.165, 0.275, 0.435, 1],
    "divider": [0.200, 0.267, 0.365, 1],
    "leaf_badge_bg": [0.165, 0.275, 0.435, 1],
    "avatar_border": [0.478, 0.698, 1.0, 1],
    "chart_card_dark": [0.082, 0.125, 0.192, 1],
    "chart_card_text_dim": [0.651, 0.745, 0.863, 1],
    "progress_track": [0.200, 0.267, 0.365, 1],
    "icon_badge_pink": [0.216, 0.345, 0.529, 1],
    "icon_badge_amber": [0.137, 0.196, 0.286, 1],
    "input_text": [0.95, 0.97, 1.0, 1.0],
    "input_placeholder": [0.549, 0.604, 0.690, 1.0],
}

# Mapeo de Etiquetas de Encabezado por Pantalla
TAGS_MAP = {
    "home": "INICIO",
    "cupboard": "DESPENSA",
    "lists": "LISTAS",
    "stats": "ESTADÍSTICAS",
}


# ---------------------------------------------------------
# Legibilidad de colores de estado (rojo, ámbar, verde)
# ---------------------------------------------------------
# Fondos más exigentes donde aparecen textos de estado en cada tema
_LEGIBLE_BG_LIGHT = COLOR_LIGHT["sage_container"]
_LEGIBLE_BG_DARK = COLOR_DARK["card_white"]
MIN_TEXT_CONTRAST = 4.5


def _luminance(color):
    """Luminancia relativa WCAG de un color RGB(A) en rango 0-1."""
    def channel(v):
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(v) for v in color[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg, bg):
    """Relación de contraste WCAG entre dos colores (1 a 21)."""
    high, low = sorted((_luminance(fg), _luminance(bg)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def legible_color(color, dark=False):
    """Oscurece (modo claro) o aclara (modo oscuro) un color hasta que el texto se lea bien.

    Conserva el tono: solo lo mezcla con negro o blanco en pasos pequeños.
    """
    color = list(color[:3])
    alpha = color[3] if len(color) > 3 else 1.0
    bg = _LEGIBLE_BG_DARK if dark else _LEGIBLE_BG_LIGHT
    target = 1.0 if dark else 0.0
    for _ in range(20):
        if contrast_ratio(color, bg) >= MIN_TEXT_CONTRAST:
            break
        color = [c + (target - c) * 0.08 for c in color]
    return color + [alpha]
