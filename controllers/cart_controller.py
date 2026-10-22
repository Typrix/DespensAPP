# -*- coding: utf-8 -*-
"""
Controlador de Carrito de Compras para DespensAPP.
Gestiona la lógica de artículos, cálculo de totales monetarios y estados de compra.
"""

from typing import List
from models.cart_item import CartItem
from models.database import DatabaseManager


class CartController:
    """Controlador para operaciones de negocio sobre el carrito de compras."""

    def __init__(self, db: DatabaseManager, analytics=None):
        self.db = db
        self.analytics = analytics

    def get_items(self, user_id: int) -> List[CartItem]:
        """Obtiene la lista de artículos del carrito para un usuario."""
        return self.db.get_cart_items(user_id)

    def calculate_total(self, user_id: int) -> float:
        """Calcula el monto total de los artículos pendientes en el carrito."""
        items = self.get_items(user_id)
        return sum(it.price for it in items if not it.is_checked)

    def add_item(self, user_id: int, title: str, price: float, subtitle: str = "General"):
        """Añade un nuevo artículo al carrito y registra telemetría."""
        item_id = self.db.add_cart_item(
            user_id=user_id,
            title=title,
            subtitle=subtitle,
            price=price,
            quantity=1
        )
        if self.analytics:
            self.analytics.track_event("add_cart_item", metadata={"title": title, "price": price})
        return item_id

    def toggle_item(self, item_id: int, is_checked: bool):
        """Alterna el estado completado de un artículo del carrito."""
        self.db.toggle_cart_item(item_id, is_checked)
        if self.analytics:
            self.analytics.track_event("toggle_cart_item", metadata={"item_id": item_id, "checked": is_checked})

    def delete_item(self, item_id: int):
        """Elimina un artículo del carrito."""
        self.db.delete_cart_item(item_id)
        if self.analytics:
            self.analytics.track_event("delete_cart_item", metadata={"item_id": item_id})
