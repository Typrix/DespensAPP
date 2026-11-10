# -*- coding: utf-8 -*-
"""
Controlador de Compras para DespensAPP.
Cada lista funciona como su propio carrito: se tachan los productos al echarlos
al carro y se finaliza la compra desde la lista. Al finalizar, lo comprado pasa a
la despensa, queda en el historial (agrupado por fecha) y sale de la lista.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from models.database import DatabaseManager
from models.pantry_item import PantryItem
from models.purchase_record import PURCHASE_DATETIME_FORMAT
from models.shopping_list import ShoppingListItem

# Periodos del historial: clave -> (días hacia atrás, etiqueta visible)
PERIODS = {
    "week": (7, "Última semana"),
    "month": (30, "Último mes"),
    "year": (365, "Último año"),
}
DEFAULT_NEW_THRESHOLD = 1.0
LOOSE_PURCHASES = "Compras sueltas"     # compras sin lista (registros antiguos del carrito)
MIGRATED_CART_LIST = "Mi carrito"       # lista que recibe lo que estaba en el carrito sin lista
MIGRATED_CART_COLOR = "#06B6D4"


def _normalize(name: str) -> str:
    """Clave de comparación de nombres (sin mayúsculas ni espacios extra)."""
    return " ".join((name or "").lower().split())


def format_money(value: float) -> str:
    """Formatea montos a moneda local (ej: $12.500)."""
    return f"${int(round(value)):,}".replace(",", ".")


def summarize_items(items: List[ShoppingListItem]) -> Dict[str, Any]:
    """
    Resumen de una lista usada como carrito: lo tachado ("en el carro") parte en $0
    y sube al tachar; el estimado suma todos los precios anotados.
    """
    return {
        "in_cart": sum(it.price for it in items if it.is_checked),
        "estimated": sum(it.price for it in items),
        "checked": sum(1 for it in items if it.is_checked),
        "pending": sum(1 for it in items if not it.is_checked),
        "total_items": len(items),
    }


class PurchaseController:
    """Lógica de compras: finalizar desde una lista, reponer, migración del carrito e historial."""

    def __init__(self, db: DatabaseManager, analytics=None, clock=datetime.now):
        self.db = db
        self.analytics = analytics
        self.clock = clock  # inyectable para pruebas

    # ------------------------------------------------------------------
    # Migración única: carrito antiguo -> listas
    # ------------------------------------------------------------------
    def migrate_cart_to_lists(self, user_id: int) -> int:
        """
        Mueve los productos del carrito antiguo a las listas (paso único e idempotente):
        - con lista de origen: vuelven a esa lista con su precio y estado de tachado;
        - sin lista (o lista borrada): van a la lista "Mi carrito".
        Si el producto ya existe en la lista, solo completa el precio si faltaba.
        Retorna cuántos productos del carrito se procesaron.
        """
        cart = self.db.get_cart_items(user_id)
        if not cart:
            return 0
        lists = {lst.id: lst for lst in self.db.get_shopping_lists(user_id)}
        fallback_id = None
        moved = 0
        for item in cart:
            target_id = item.list_id if item.list_id in lists else None
            if target_id is None:
                if fallback_id is None:
                    fallback_id = self.find_or_create_list(user_id, MIGRATED_CART_LIST, MIGRATED_CART_COLOR)
                target_id = fallback_id
            existing = {_normalize(it.name): it for it in self.db.get_shopping_list_items(target_id)}
            match = existing.get(_normalize(item.title))
            if match:
                if not match.price and item.price:
                    self.db.update_shopping_list_item(match.id, match.name, item.price)
                if item.is_checked and not match.is_checked:
                    self.db.toggle_shopping_list_item(match.id, True)
            else:
                self.db.add_shopping_list_item(target_id, item.title, price=item.price, is_checked=item.is_checked)
            self.db.delete_cart_item(item.id)
            moved += 1
        if self.analytics and moved:
            self.analytics.track_event("migrate_cart_to_lists", metadata={"items": moved})
        return moved

    def find_or_create_list(self, user_id: int, name: str, color: str) -> int:
        for lst in self.db.get_shopping_lists(user_id):
            if _normalize(lst.name) == _normalize(name):
                return lst.id
        return self.db.add_shopping_list(user_id, name, color, "clipboard-text-outline")

    # ------------------------------------------------------------------
    # Despensa -> Lista (reponer)
    # ------------------------------------------------------------------
    def add_pantry_item_to_list(self, list_id: int, pantry_item: PantryItem) -> bool:
        """Anota un producto de la despensa en una lista. False si ya estaba pendiente ahí."""
        pending = {_normalize(it.name) for it in self.db.get_shopping_list_items(list_id) if not it.is_checked}
        if _normalize(pantry_item.name) in pending:
            return False
        self.db.add_shopping_list_item(list_id, pantry_item.name)
        return True

    def add_many_to_list(self, list_id: int, pantry_items: List[PantryItem]) -> int:
        """Anota varios productos de la despensa en una lista. Retorna cuántos se agregaron."""
        pending = {_normalize(it.name) for it in self.db.get_shopping_list_items(list_id) if not it.is_checked}
        added = 0
        for item in pantry_items:
            key = _normalize(item.name)
            if key in pending:
                continue
            self.db.add_shopping_list_item(list_id, item.name)
            pending.add(key)
            added += 1
        if self.analytics and added:
            self.analytics.track_event("restock_all_to_list", metadata={"list_id": list_id, "items": added})
        return added

    # ------------------------------------------------------------------
    # Lista -> Despensa (Finalizar compra)
    # ------------------------------------------------------------------
    def find_pantry_match(self, user_id: int, name: str) -> Optional[PantryItem]:
        """Busca en la despensa un producto con el mismo nombre (ignora mayúsculas)."""
        key = _normalize(name)
        for item in self.db.get_pantry_items(user_id):
            if _normalize(item.name) == key:
                return item
        return None

    def build_checkout(self, user_id: int, list_items: List[ShoppingListItem]) -> List[Dict[str, Any]]:
        """
        Una fila por producto tachado con la unidad sugerida:
        la del producto existente en la despensa o 'un.' si es nuevo.
        """
        pantry = {_normalize(p.name): p for p in self.db.get_pantry_items(user_id)}
        rows = []
        for item in list_items:
            if not item.is_checked:
                continue
            match = pantry.get(_normalize(item.name))
            rows.append({
                "ref": item,
                "title": item.name,
                "price": item.price,
                "unit": match.unit if match else "un.",
                "is_new": match is None,
            })
        return rows

    def finalize_purchase(self, user_id: int, list_id: int, list_name: str,
                          entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Registra la compra de una lista. Cada entrada: {ref (ShoppingListItem), quantity, unit}.
        - Suma la cantidad al producto de la despensa o lo crea.
        - Guarda cada producto en el historial con la misma fecha (una compra = un grupo).
        - Saca de la lista lo comprado (lo no encontrado queda pendiente).
        """
        now = self.clock().strftime(PURCHASE_DATETIME_FORMAT)
        summary = {"updated": 0, "created": 0, "total": 0.0, "count": 0}
        for entry in entries:
            item: ShoppingListItem = entry["ref"]
            quantity = float(entry["quantity"])
            match = self.find_pantry_match(user_id, item.name)
            if match:
                self.db.set_pantry_quantity(match.id, match.quantity + quantity)
                unit = match.unit
                summary["updated"] += 1
            else:
                unit = entry.get("unit") or "un."
                self.db.add_pantry_item(user_id, item.name, quantity, unit, DEFAULT_NEW_THRESHOLD, "General", None)
                summary["created"] += 1
            self.db.add_purchase_record(user_id, item.name, item.price, quantity, unit, now,
                                        list_id=list_id, list_name=list_name)
            self.db.delete_shopping_list_item(item.id)
            summary["total"] += item.price
            summary["count"] += 1
        if self.analytics and summary["count"]:
            self.analytics.track_event("finalize_purchase", metadata={
                "list_id": list_id, "items": summary["count"], "total": summary["total"]})
        return summary

    # ------------------------------------------------------------------
    # Historial y gasto por periodo
    # ------------------------------------------------------------------
    def period_start(self, period: str) -> str:
        """Fecha de inicio del periodo (texto comparable con purchased_at)."""
        days = PERIODS.get(period, PERIODS["week"])[0]
        return (self.clock() - timedelta(days=days)).strftime(PURCHASE_DATETIME_FORMAT)

    def get_spending(self, user_id: Optional[int], period: str = "week") -> Dict[str, Any]:
        """Total gastado, cantidad de productos y compras (agrupadas por fecha) del periodo."""
        label = PERIODS.get(period, PERIODS["week"])[1]
        if not user_id:
            return {"period": period, "label": label, "total": 0.0, "total_str": "$0",
                    "count": 0, "records": [], "groups": []}
        records = self.db.get_purchase_history(user_id, since=self.period_start(period))
        total = sum(r.price for r in records)
        return {
            "period": period,
            "label": label,
            "total": total,
            "total_str": format_money(total),
            "count": len(records),
            "records": records,
            "groups": self.group_by_purchase(records),
        }

    @staticmethod
    def group_by_purchase(records) -> List[Dict[str, Any]]:
        """
        Agrupa el historial por compra: los productos de una misma finalización comparten
        fecha y hora (y lista). Orden: la compra más reciente primero.
        """
        groups: Dict[tuple, Dict[str, Any]] = {}
        for rec in records:  # ya vienen ordenados por fecha descendente
            dt = rec.purchased_datetime
            stamp = dt.strftime("%Y-%m-%d %H:%M") if dt else str(rec.purchased_at)[:16]
            name = rec.list_name or LOOSE_PURCHASES
            group = groups.setdefault((stamp, name), {
                "name": name,
                "date_str": dt.strftime("%d/%m/%Y %H:%M") if dt else "",
                "records": [],
                "subtotal": 0.0,
            })
            group["records"].append(rec)
            group["subtotal"] += rec.price
        result = list(groups.values())
        for g in result:
            g["count"] = len(g["records"])
            g["subtotal_str"] = format_money(g["subtotal"])
        return result
