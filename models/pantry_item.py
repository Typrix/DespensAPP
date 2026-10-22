# -*- coding: utf-8 -*-
"""
Modelo de Producto de Despensa para DespensAPP.
Calcula reactivamente estados de stock, umbrales y caducidad.
"""

from datetime import date, datetime
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class PantryItem:
    """
    Entidad que representa un producto en la despensa.
    Calcula automáticamente si hay suficiente, está por agotarse o requiere reposición
    en base a los umbrales numéricos definidos por el usuario, y supervisa la fecha de caducidad.
    """
    id: int
    user_id: int
    name: str
    quantity: float
    unit: str = "un."
    min_threshold: float = 2.0
    category: str = "General"
    expiration_date: Optional[str] = None

    @property
    def status(self) -> str:
        """Determina el estado del stock según la cantidad numérica y el umbral."""
        if self.quantity <= 0:
            return "Reponer"
        if self.quantity <= self.min_threshold:
            return "Por agotarse"
        return "Suficiente"

    @property
    def formatted_quantity(self) -> str:
        """Muestra la cantidad formateada sin decimales innecesarios (ej: 500 g, 1.5 kg)."""
        if self.quantity == int(self.quantity):
            return f"{int(self.quantity)} {self.unit}"
        return f"{self.quantity:.1f} {self.unit}"

    @property
    def status_text_color(self) -> List[float]:
        """Color del texto de estado según nivel de stock."""
        st = self.status
        if st == "Reponer":
            return [0.85, 0.20, 0.25, 1.0]      # Rojo intenso suave
        if st == "Por agotarse":
            return [0.82, 0.48, 0.12, 1.0]      # Ámbar / Naranja
        return [0.12, 0.58, 0.32, 1.0]          # Verde esmeralda

    @property
    def status_badge_bg(self) -> List[float]:
        """Color de fondo para la píldora de estado."""
        st = self.status
        if st == "Reponer":
            return [0.98, 0.88, 0.88, 1.0]      # Rosa tenue
        if st == "Por agotarse":
            return [0.98, 0.93, 0.85, 1.0]      # Ámbar tenue
        return [0.88, 0.96, 0.90, 1.0]          # Menta tenue

    @property
    def days_until_expiration(self) -> Optional[int]:
        """Calcula los días restantes hasta la fecha de caducidad."""
        if not self.expiration_date or self.expiration_date.strip().lower() in ("", "none", "null", "no vence"):
            return None
        try:
            clean_date = self.expiration_date.strip()
            if "/" in clean_date:
                parts = clean_date.split("/")
                exp_dt = date(int(parts[2]), int(parts[1]), int(parts[0]))
            else:
                exp_dt = datetime.strptime(clean_date, "%Y-%m-%d").date()
            return (exp_dt - date.today()).days
        except Exception:
            return None

    @property
    def expiration_status(self) -> str:
        """Etiqueta descriptiva del estado de vencimiento del producto."""
        days = self.days_until_expiration
        if days is None:
            return "Sin vencimiento"
        if days < 0:
            return f"Venció hace {abs(days)}d"
        if days == 0:
            return "Vence hoy"
        if days == 1:
            return "Vence mañana"
        if days <= 3:
            return f"Vence en {days} días"
        return f"Vence: {self.formatted_expiration_date}"

    @property
    def formatted_expiration_date(self) -> str:
        """Retorna la fecha formateada en formato DD/MM/AAAA."""
        if not self.expiration_date or self.expiration_date.strip().lower() in ("", "none", "null", "no vence"):
            return "No vence"
        try:
            clean_date = self.expiration_date.strip()
            if "/" in clean_date:
                return clean_date
            exp_dt = datetime.strptime(clean_date, "%Y-%m-%d").date()
            return exp_dt.strftime("%d/%m/%Y")
        except Exception:
            return self.expiration_date

    @property
    def is_expired(self) -> bool:
        """Verifica si el producto ya expiró."""
        days = self.days_until_expiration
        return days is not None and days < 0

    @property
    def is_expiring_soon(self) -> bool:
        """Verifica si el producto está próximo a expirar (dentro de los próximos 3 días)."""
        days = self.days_until_expiration
        return days is not None and 0 <= days <= 3

    @property
    def expiration_text_color(self) -> List[float]:
        """Color de la advertencia de vencimiento."""
        if self.is_expired:
            return [0.85, 0.20, 0.25, 1.0]     # Rojo alerta
        if self.is_expiring_soon:
            return [0.82, 0.48, 0.12, 1.0]     # Ámbar advertencia
        return [0.45, 0.55, 0.65, 1.0]         # Gris sutil neutro
