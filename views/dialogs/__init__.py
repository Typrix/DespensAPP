# -*- coding: utf-8 -*-
"""
Paquete de Diálogos y Modales para DespensAPP.
Exporta todos los controladores de formulario y carga automáticamente dialogs.kv.
"""

import os
from kivy.lang import Builder

from views.dialogs.base import BaseFormModal, EditItemModal
from views.dialogs.cart_dialog import AddCartItemModal
from views.dialogs.pantry_dialog import AddPantryItemModal, PantryItemDetailModal
from views.dialogs.list_dialog import (
    ColorChipButton,
    AddShoppingListModal,
    ShoppingListItemRow,
    ShoppingListDetailModal,
)
from views.dialogs.auth_dialog import AuthModal

# Cargar la definición declarativa dialogs.kv desde la carpeta kv/
DIALOGS_KV_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "kv", "dialogs.kv")
)
if os.path.exists(DIALOGS_KV_PATH):
    Builder.load_file(DIALOGS_KV_PATH)

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
