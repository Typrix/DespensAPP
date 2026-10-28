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

    def __init__(self, db: DatabaseManager, analytics=None, notifications=None):
        self.db = db
        self.analytics = analytics
        self.notifications = notifications

    def get_items(self, user_id: int) -> List[PantryItem]:
        """Obtiene la lista de productos en despensa para un usuario."""
        return self.db.get_pantry_items(user_id)

    def add_item(self, user_id: int, name: str, quantity: float, unit: str,
                 threshold: float, expiration_date: Optional[str] = None):
        """Registra un nuevo producto en la despensa y verifica alertas si corresponde."""
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
        # Disparar alertas de stock o caducidad para el producto nuevo si aplica
        if self.notifications and item_id:
            new_item = self.db.get_pantry_item_by_id(item_id)
            if new_item:
                self.notifications.check_item_alerts(new_item, force=True)
        return item_id

    def change_quantity(self, item_id: int, delta: float):
        """Modifica la cantidad disponible de un producto y alerta si cae bajo el umbral o se agota."""
        self.db.update_pantry_quantity(item_id, delta)
        if self.notifications:
            item = self.db.get_pantry_item_by_id(item_id)
            if item:
                self.notifications.check_item_alerts(item, force=True, check_stock=True, check_expiration=False)

    def update_expiration(self, item_id: int, new_expiration_date: Optional[str]):
        """Actualiza la fecha de vencimiento y alerta de inmediato si está por vencer o venció."""
        self.db.update_pantry_expiration(item_id, new_expiration_date)
        if self.analytics:
            self.analytics.track_event(
                "update_pantry_expiration",
                metadata={"item_id": item_id, "expiration": new_expiration_date}
            )
        if self.notifications:
            item = self.db.get_pantry_item_by_id(item_id)
            if item:
                self.notifications.check_item_alerts(item, force=True, check_stock=False, check_expiration=True)

    def delete_item(self, item_id: int):
        """Elimina un producto del inventario de despensa."""
        self.db.delete_pantry_item(item_id)
        if self.analytics:
            self.analytics.track_event("delete_pantry_item", metadata={"item_id": item_id})
