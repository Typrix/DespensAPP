# -*- coding: utf-8 -*-
"""
Modelo de Registro de Compra para DespensAPP.
Representa un producto comprado al finalizar una compra (historial de gasto).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

PURCHASE_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


@dataclass
class PurchaseRecord:
    """Entidad que representa un producto comprado y registrado en el historial."""
    id: int
    user_id: int
    title: str
    price: float = 0.0
    quantity: float = 1.0
    unit: str = "un."
    list_id: Optional[int] = None
    purchased_at: str = ""

    @property
    def formatted_price(self) -> str:
        """Formatea el precio a moneda local (ej: $2.500)."""
        return f"${int(self.price):,}".replace(",", ".")

    @property
    def purchased_datetime(self) -> Optional[datetime]:
        """Convierte la fecha guardada (texto o datetime de MySQL) a datetime."""
        if isinstance(self.purchased_at, datetime):
            return self.purchased_at
        try:
            return datetime.strptime(str(self.purchased_at)[:19], PURCHASE_DATETIME_FORMAT)
        except ValueError:
            return None

    @property
    def formatted_date(self) -> str:
        """Fecha corta para listas (ej: 12/11/2026)."""
        dt = self.purchased_datetime
        return dt.strftime("%d/%m/%Y") if dt else ""
