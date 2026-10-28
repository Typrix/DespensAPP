# -*- coding: utf-8 -*-
"""
Paquete de Vistas (Views) para DespensAPP.
Expone los temas de diseño, componentes visuales y modales interactivos.
"""

from views.theme import COLOR_LIGHT, COLOR_DARK, TAGS_MAP
from views.widgets import (
    CustomProgressBar,
    BottomNavButton,
    CartItemRow,
    PantryItemRow,
    ShoppingListCard,
    AddCircleButton,
    AvatarCircleButton,
    ProfileModalView,
    RemoteConfigBanner,
)
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
    "COLOR_LIGHT",
    "COLOR_DARK",
    "TAGS_MAP",
    "CustomProgressBar",
    "BottomNavButton",
    "CartItemRow",
    "PantryItemRow",
    "ShoppingListCard",
    "AddCircleButton",
    "AvatarCircleButton",
    "ProfileModalView",
    "RemoteConfigBanner",
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
