# -*- coding: utf-8 -*-
"""
Controlador de Despensa para DespensAPP.
Gestiona el inventario de alimentos, niveles de stock, umbrales mínimos y alertas de caducidad.
"""

from typing import List, Optional
from models.pantry_item import PantryItem
from models.database import DatabaseManager


class PantryController:
    """Controlador para operaciones de negocio sobre los alimentos en la despensa."""

    def __init__(self, db: DatabaseManager, analytics=None):
        self.db = db
        self.analytics = analytics

    def get_items(self, user_id: int) -> List[PantryItem]:
        """Obtiene la lista de productos en despensa para un usuario."""
        return self.db.get_pantry_items(user_id)

    def add_item(self, user_id: int, name: str, quantity: float, unit: str,
                 threshold: float, expiration_date: Optional[str] = None):
        """Registra un nuevo producto en la despensa."""
        item_id = self.db.add_pantry_item(
            user_id=user_id,
            name=name,
            quantity=quantity,
            unit=unit,
            min_threshold=threshold,
            category="General",
            expiration_date=expiration_date
        )
        if self.analytics:
            self.analytics.track_event(
                "add_pantry_item",
                metadata={"name": name, "quantity": quantity, "unit": unit, "expiration": expiration_date}
            )
        return item_id

    def change_quantity(self, item_id: int, delta: float):
        """Modifica la cantidad disponible de un producto en la despensa."""
        self.db.update_pantry_quantity(item_id, delta)

    def update_expiration(self, item_id: int, new_expiration_date: Optional[str]):
        """Actualiza la fecha de vencimiento de un alimento."""
        self.db.update_pantry_expiration(item_id, new_expiration_date)
        if self.analytics:
            self.analytics.track_event(
                "update_pantry_expiration",
                metadata={"item_id": item_id, "expiration": new_expiration_date}
            )

    def delete_item(self, item_id: int):
        """Elimina un producto del inventario de despensa."""
        self.db.delete_pantry_item(item_id)
        if self.analytics:
            self.analytics.track_event("delete_pantry_item", metadata={"item_id": item_id})
