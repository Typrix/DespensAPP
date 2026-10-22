# -*- coding: utf-8 -*-
"""
Módulo de compatibilidad para modelos de DespensAPP.
Reexporta todas las entidades y definiciones desde el paquete models/.
"""

from models.user import User
from models.cart_item import CartItem
from models.pantry_item import PantryItem
from models.shopping_list import ShoppingList, ShoppingListItem

__all__ = [
    "User",
    "CartItem",
    "PantryItem",
    "ShoppingList",
    "ShoppingListItem",
]
