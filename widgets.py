# -*- coding: utf-8 -*-
"""
Módulo de compatibilidad para widgets personalizados de DespensAPP.
Reexporta todos los componentes visuales desde views/widgets/.
"""

from views.widgets import (
    CustomProgressBar,
    BottomNavButton,
    CartItemRow,
    PantryItemRow,
    ShoppingListCard,
    AddCircleButton,
    AvatarCircleButton,
    ProfileModalView,
)

__all__ = [
    "CustomProgressBar",
    "BottomNavButton",
    "CartItemRow",
    "PantryItemRow",
    "ShoppingListCard",
    "AddCircleButton",
    "AvatarCircleButton",
    "ProfileModalView",
]
