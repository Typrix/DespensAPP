# -*- coding: utf-8 -*-
"""
Módulo de compatibilidad para diálogos y modales de DespensAPP.
Reexporta todos los controladores de formulario desde views/dialogs/.
"""

from views.dialogs import (
    BaseFormModal,
    EditItemModal,
    AddCartItemModal,
    AddPantryItemModal,
    PantryItemDetailModal,
    ColorChipButton,
    AddShoppingListModal,
    ShoppingListItemRow,
    ShoppingListDetailModal,
    AuthModal,
)

__all__ = [
    "BaseFormModal",
    "EditItemModal",
    "AddCartItemModal",
    "AddPantryItemModal",
    "PantryItemDetailModal",
    "ColorChipButton",
    "AddShoppingListModal",
    "ShoppingListItemRow",
    "ShoppingListDetailModal",
    "AuthModal",
]
