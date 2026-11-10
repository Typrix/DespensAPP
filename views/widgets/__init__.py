# -*- coding: utf-8 -*-
"""
Paquete de Widgets para DespensAPP.
Reexporta todos los componentes visuales personalizados.
"""

from views.widgets.progress_bar import CustomProgressBar
from views.widgets.nav_button import BottomNavButton
from views.widgets.cart_row import CartItemRow
from views.widgets.pantry_row import PantryItemRow
from views.widgets.list_card import ShoppingListCard
from views.widgets.buttons import AddCircleButton, AvatarCircleButton
from views.widgets.profile_modal import ProfileModalView
from views.widgets.remote_banner import RemoteConfigBanner
from views.widgets.undo_snackbar import show_undo_snackbar, hide_undo_snackbar, show_info_toast
from views.widgets.empty_state import EmptyState
from views.widgets.purchase_row import PurchaseHistoryRow, PurchaseGroupCard

__all__ = [
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
    "PurchaseGroupCard",
]
