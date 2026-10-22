# -*- coding: utf-8 -*-
"""
Modelos de Lista de Compras para DespensAPP.
Representa listas personalizadas de supermercado y sus elementos asociados.
"""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class ShoppingListItem:
    """Entidad que representa un producto anotado en una lista de compras de supermercado."""
    id: int
    list_id: int
    name: str
    is_checked: bool = False
    created_at: str = ""


@dataclass
class ShoppingList:
    """Entidad que representa una lista de compras personalizada."""
    id: int
    user_id: int
    name: str
    icon_name: str = "clipboard-text-outline"
    icon_color: str = "#286ED3"
    items_count: int = 0
    pending_count: int = 0
    items: Optional[List[ShoppingListItem]] = None

    @property
    def color_rgba(self) -> List[float]:
        """Convierte el código hexadecimal de color a formato RGBA normalizado [r, g, b, 1]."""
        hex_str = self.icon_color.lstrip("#")
        if len(hex_str) != 6:
            return [0.157, 0.431, 0.831, 1.0]  # Azul por defecto
        try:
            r = int(hex_str[0:2], 16) / 255.0
            g = int(hex_str[2:4], 16) / 255.0
            b = int(hex_str[4:6], 16) / 255.0
            return [r, g, b, 1.0]
        except ValueError:
            return [0.157, 0.431, 0.831, 1.0]

    @property
    def badge_bg_rgba(self) -> List[float]:
        """Genera un fondo pastel transparente coordinado con el color del icono."""
        rgba = self.color_rgba
        return [rgba[0], rgba[1], rgba[2], 0.15]
