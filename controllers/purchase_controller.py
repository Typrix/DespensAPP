# -*- coding: utf-8 -*-
"""
Controlador de Compras para DespensAPP.
Conecta el ciclo Listas -> Carrito -> Despensa y calcula el gasto real por periodo
a partir del historial de compras finalizadas.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from models.cart_item import CartItem
from models.database import DatabaseManager
from models.pantry_item import PantryItem
from models.purchase_record import PURCHASE_DATETIME_FORMAT

# Periodos del historial: clave -> (días hacia atrás, etiqueta visible)
PERIODS = {
    "week": (7, "Última semana"),
    "month": (30, "Último mes"),
    "year": (365, "Último año"),
}
DEFAULT_NEW_THRESHOLD = 1.0
RESTOCK_SUBTITLE = "Reponer despensa"
LOOSE_PURCHASES = "Compras sueltas"  # productos agregados al carrito sin venir de una lista


def _normalize(name: str) -> str:
    """Clave de comparación de nombres (sin mayúsculas ni espacios extra)."""
    return " ".join((name or "").lower().split())


def format_money(value: float) -> str:
    """Formatea montos a moneda local (ej: $12.500)."""
    return f"${int(round(value)):,}".replace(",", ".")


class PurchaseController:
    """Lógica de negocio de compras: pasar listas al carrito, finalizar compra e historial."""

    def __init__(self, db: DatabaseManager, analytics=None, clock=datetime.now):
        self.db = db
        self.analytics = analytics
        self.clock = clock  # inyectable para pruebas

    # ------------------------------------------------------------------
    # Listas -> Carrito
    # ------------------------------------------------------------------
    def send_list_to_cart(self, user_id: int, list_id: int, list_name: str) -> int:
        """
        Copia al carrito los productos sin tachar de una lista y los tacha en la lista.
        Omite los que ya están pendientes en el carrito (evita duplicados).
        Retorna cuántos productos se agregaron.
        """
        in_cart = {_normalize(c.title) for c in self.db.get_cart_items(user_id) if not c.is_checked}
        added = 0
        for item in self.db.get_shopping_list_items(list_id):
            if item.is_checked:
                continue
            key = _normalize(item.name)
            if key not in in_cart:
                self.db.add_cart_item(user_id, item.name, list_name, 0.0, 1, list_id=list_id)
                in_cart.add(key)
                added += 1
            self.db.toggle_shopping_list_item(item.id, True)
        if self.analytics and added:
            self.analytics.track_event("send_list_to_cart", metadata={"list_id": list_id, "added": added})
        return added

    def pending_list_count(self, list_id: int) -> int:
        """Cantidad de productos sin tachar en una lista."""
        return sum(1 for it in self.db.get_shopping_list_items(list_id) if not it.is_checked)

    # ------------------------------------------------------------------
    # Despensa -> Carrito
    # ------------------------------------------------------------------
    def add_pantry_item_to_cart(self, user_id: int, pantry_item: PantryItem) -> bool:
        """Agrega al carrito un producto de la despensa por reponer. False si ya estaba pendiente."""
        in_cart = {_normalize(c.title) for c in self.db.get_cart_items(user_id) if not c.is_checked}
        if _normalize(pantry_item.name) in in_cart:
            return False
        self.db.add_cart_item(user_id, pantry_item.name, RESTOCK_SUBTITLE, 0.0, 1)
        return True

    # ------------------------------------------------------------------
    # Carrito -> Despensa (Finalizar compra)
    # ------------------------------------------------------------------
    def find_pantry_match(self, user_id: int, name: str) -> Optional[PantryItem]:
        """Busca en la despensa un producto con el mismo nombre (ignora mayúsculas)."""
        key = _normalize(name)
        for item in self.db.get_pantry_items(user_id):
            if _normalize(item.name) == key:
                return item
        return None

    def build_checkout(self, user_id: int, cart_items: List[CartItem]) -> List[Dict[str, Any]]:
        """
        Prepara una fila por cada producto marcado del carrito con la unidad sugerida:
        la del producto existente en la despensa o 'un.' si es nuevo.
        """
        pantry = {_normalize(p.name): p for p in self.db.get_pantry_items(user_id)}
        rows = []
        for item in cart_items:
            if not item.is_checked:
                continue
            match = pantry.get(_normalize(item.title))
            rows.append({
                "cart_item": item,
                "unit": match.unit if match else "un.",
                "is_new": match is None,
            })
        return rows

    def finalize_purchase(self, user_id: int, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Registra la compra. Cada entrada: {cart_item, quantity, unit}.
        - Suma la cantidad al producto existente de la despensa o lo crea.
        - Guarda el producto en el historial con la fecha actual.
        - Quita el producto del carrito.
        """
        now = self.clock().strftime(PURCHASE_DATETIME_FORMAT)
        summary = {"updated": 0, "created": 0, "total": 0.0, "count": 0}
        list_names = self._list_names(user_id)
        for entry in entries:
            cart_item: CartItem = entry["cart_item"]
            quantity = float(entry["quantity"])
            match = self.find_pantry_match(user_id, cart_item.title)
            if match:
                self.db.set_pantry_quantity(match.id, match.quantity + quantity)
                unit = match.unit
                summary["updated"] += 1
            else:
                unit = entry.get("unit") or "un."
                self.db.add_pantry_item(user_id, cart_item.title, quantity, unit, DEFAULT_NEW_THRESHOLD, "General", None)
                summary["created"] += 1
            self.db.add_purchase_record(user_id, cart_item.title, cart_item.price, quantity, unit, now,
                                        list_id=cart_item.list_id,
                                        list_name=list_names.get(cart_item.list_id))
            self.db.delete_cart_item(cart_item.id)
            summary["total"] += cart_item.price
            summary["count"] += 1
        if self.analytics and summary["count"]:
            self.analytics.track_event("finalize_purchase", metadata={
                "items": summary["count"], "total": summary["total"]})
        return summary

    # ------------------------------------------------------------------
    # Historial y gasto por periodo
    # ------------------------------------------------------------------
    def period_start(self, period: str) -> str:
        """Fecha de inicio del periodo (texto comparable con purchased_at)."""
        days = PERIODS.get(period, PERIODS["week"])[0]
        return (self.clock() - timedelta(days=days)).strftime(PURCHASE_DATETIME_FORMAT)

    def get_spending(self, user_id: Optional[int], period: str = "week") -> Dict[str, Any]:
        """Total gastado, cantidad de compras y registros del periodo (semana, mes o año)."""
        label = PERIODS.get(period, PERIODS["week"])[1]
        if not user_id:
            return {"period": period, "label": label, "total": 0.0, "total_str": "$0",
                    "count": 0, "records": []}
        records = self.db.get_purchase_history(user_id, since=self.period_start(period))
        total = sum(r.price for r in records)
        return {
            "period": period,
            "label": label,
            "total": total,
            "total_str": format_money(total),
            "count": len(records),
            "records": records,
            "groups": self.group_by_list(records, self._list_names(user_id)),
        }

    def _list_names(self, user_id: int) -> Dict[int, str]:
        """Mapa id -> nombre de las listas actuales del usuario."""
        return {lst.id: lst.name for lst in self.db.get_shopping_lists(user_id)}

    @staticmethod
    def group_by_list(records, current_list_names: Optional[Dict[int, str]] = None) -> List[Dict[str, Any]]:
        """
        Agrupa las compras por lista, de la compra más reciente a la más antigua.
        Usa el nombre guardado al comprar; si no existe (registros antiguos) busca la
        lista actual por id, y si no hay lista va a "Compras sueltas".
        """
        current_list_names = current_list_names or {}
        groups: Dict[str, Dict[str, Any]] = {}
        for rec in records:  # ya vienen ordenados por fecha descendente
            name = rec.list_name or current_list_names.get(rec.list_id) or LOOSE_PURCHASES
            group = groups.setdefault(name, {
                "name": name, "records": [], "subtotal": 0.0, "last_date": rec.formatted_date,
            })
            group["records"].append(rec)
            group["subtotal"] += rec.price
        result = list(groups.values())
        for g in result:
            g["count"] = len(g["records"])
            g["subtotal_str"] = format_money(g["subtotal"])
        return result
