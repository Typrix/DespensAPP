# -*- coding: utf-8 -*-
"""
Modelo de Ítem del Carrito para DespensAPP.
Representa un artículo agregado al carrito de compras con formateo de moneda.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CartItem:
    """Entidad que representa un artículo en el carrito de compras."""
    id: int
    user_id: int
    title: str
    subtitle: str = "Lista general"
    price: float = 0.0
    quantity: int = 1
    is_checked: bool = False
    list_id: Optional[int] = None

    @property
    def formatted_price(self) -> str:
        """Formatea el precio a moneda local (ej: $2.500)."""
        return f"${int(self.price):,}".replace(",", ".")
