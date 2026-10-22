# -*- coding: utf-8 -*-
"""
Controlador de Listas de Compras para DespensAPP.
Gestiona la creación de listas de supermercado, productos individuales y anotaciones.
"""

from typing import List, Optional
from models.shopping_list import ShoppingList, ShoppingListItem
from models.database import DatabaseManager


class ListController:
    """Controlador para operaciones de negocio sobre listas de supermercado."""

    def __init__(self, db: DatabaseManager, analytics=None):
        self.db = db
        self.analytics = analytics

    def get_lists(self, user_id: int) -> List[ShoppingList]:
        """Obtiene todas las listas de compras del usuario."""
        return self.db.get_shopping_lists(user_id)

    def add_list(self, user_id: int, name: str, color_hex: str, initial_items: str = "") -> Optional[int]:
        """Crea una nueva lista de compras con color y posibles productos iniciales."""
        new_list_id = self.db.add_shopping_list(
            user_id=user_id,
            name=name,
            icon_color=color_hex,
            icon_name="clipboard-text-outline"
        )
        if new_list_id and initial_items:
            items_list = [it.strip() for it in initial_items.replace("\n", ",").split(",") if it.strip()]
            for it_name in items_list:
                self.db.add_shopping_list_item(new_list_id, it_name)

        if self.analytics:
            self.analytics.track_event(
                "create_shopping_list",
                metadata={"name": name, "initial_items": initial_items}
            )
        return new_list_id

    def delete_list(self, list_id: int):
        """Elimina una lista de compras completa."""
        self.db.delete_shopping_list(list_id)

    def get_list_items(self, list_id: int) -> List[ShoppingListItem]:
        """Obtiene los productos anotados en una lista específica."""
        return self.db.get_shopping_list_items(list_id)

    def add_list_item(self, list_id: int, name: str) -> Optional[int]:
        """Añade un producto a la lista de compras."""
        item_id = self.db.add_shopping_list_item(list_id, name)
        if self.analytics:
            self.analytics.track_event(
                "add_shopping_list_item",
                metadata={"list_id": list_id, "name": name}
            )
        return item_id

    def toggle_list_item(self, item_id: int, is_checked: bool):
        """Marca o tacha un producto en la lista."""
        self.db.toggle_shopping_list_item(item_id, is_checked)

    def update_list_item_name(self, item_id: int, new_name: str):
        """Renombra un producto en la lista."""
        self.db.update_shopping_list_item_name(item_id, new_name)

    def delete_list_item(self, item_id: int):
        """Elimina un producto individual de la lista."""
        self.db.delete_shopping_list_item(item_id)
