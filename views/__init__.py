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
    show_undo_snackbar,
    hide_undo_snackbar,
    show_info_toast,
    EmptyState,
    PurchaseHistoryRow,
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
    CheckoutModal,
    AlertsModal,
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
    "show_undo_snackbar",
    "hide_undo_snackbar",
    "show_info_toast",
    "EmptyState",
    "PurchaseHistoryRow",
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
    "CheckoutModal",
    "AlertsModal",
]
