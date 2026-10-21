# -*- coding: utf-8 -*-
"""
Modelos de datos para DespensAPP.
Define las entidades User, CartItem, PantryItem y ShoppingList con
cálculo reactivo de estado y formato.
"""

from datetime import date, datetime
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class User:
    """Entidad que representa un usuario registrado."""
    id: int
    name: str
    email: str
    avatar_initials: str = "US"
    password_hash: str = ""

    @staticmethod
    def generate_initials(full_name: str) -> str:
        """Genera las iniciales a partir del nombre completo (ej: Sofía Martínez -> SO)."""
        parts = full_name.strip().split()
        if not parts:
            return "US"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[1][0]).upper()


@dataclass
class CartItem:
    """Entidad que representa un artículo en el carrito de compras."""
    id: int
    user_id: int
    title: str
    subtitle: str = "Lista general"
    price: float = 0.0
    quantity: int = 1
    is_checked: bool = False
    list_id: Optional[int] = None

    @property
    def formatted_price(self) -> str:
        """Formatea el precio a moneda local (ej: $2.500)."""
        formatted = f"${int(self.price):,}".replace(",", ".")
        return formatted


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
    def status_text_color(self) -> list:
        """Color del texto de estado según nivel de stock."""
        st = self.status
        if st == "Reponer":
            return [0.85, 0.20, 0.25, 1.0]      # Rojo intenso suave
        if st == "Por agotarse":
            return [0.82, 0.48, 0.12, 1.0]      # Ámbar / Naranja
        return [0.12, 0.58, 0.32, 1.0]          # Verde esmeralda

    @property
    def status_badge_bg(self) -> list:
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
        days = self.days_until_expiration
        return days is not None and days < 0

    @property
    def is_expiring_soon(self) -> bool:
        days = self.days_until_expiration
        return days is not None and 0 <= days <= 3

    @property
    def expiration_text_color(self) -> list:
        if self.is_expired:
            return [0.85, 0.20, 0.25, 1.0]     # Rojo alerta
        if self.is_expiring_soon:
            return [0.82, 0.48, 0.12, 1.0]     # Ámbar advertencia
        return [0.45, 0.55, 0.65, 1.0]         # Gris sutil neutro


@dataclass
class ShoppingListItem:
    """Entidad que representa un producto anotado en una lista de compras de supermercado."""
    id: int
    list_id: int
    name: str
    is_checked: bool = False
    created_at: str = ""


@dataclass
class ShoppingList:
    """Entidad que representa una lista de compras personalizada."""
    id: int
    user_id: int
    name: str
    icon_name: str = "clipboard-text-outline"
    icon_color: str = "#286ED3"
    items_count: int = 0
    pending_count: int = 0
    items: Optional[List[ShoppingListItem]] = None

    @property
    def color_rgba(self) -> list:
        """Convierte el código hexadecimal de color a formato RGBA normalizado [r, g, b, 1]."""
        hex_str = self.icon_color.lstrip("#")
        if len(hex_str) != 6:
            return [0.157, 0.431, 0.831, 1.0]  # Azul por defecto
        try:
            r = int(hex_str[0:2], 16) / 255.0
            g = int(hex_str[2:4], 16) / 255.0
            b = int(hex_str[4:6], 16) / 255.0
            return [r, g, b, 1.0]
        except ValueError:
            return [0.157, 0.431, 0.831, 1.0]

    @property
    def badge_bg_rgba(self) -> list:
        """Genera un fondo pastel transparente o tenue coordinado con el color del icono."""
        rgba = self.color_rgba
        return [rgba[0], rgba[1], rgba[2], 0.15]
