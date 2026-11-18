# -*- coding: utf-8 -*-
"""
Lógica del selector de cantidad y medida (sin Kivy).
Define las medidas disponibles, los atajos de cantidad, la conversión entre
kg/g y L/ml y el ajuste de valores para el componente QuantityPicker.
"""

import math

from controllers.validators import PANTRY_UNITS, QUANTITY_MAX, step_for_unit, parse_number, format_number

# Medidas que se convierten entre sí: unidad -> (familia, factor respecto a la base)
_CONVERTIBLE = {
    "g": ("weight", 1.0),
    "kg": ("weight", 1000.0),
    "ml": ("volume", 1.0),
    "L": ("volume", 1000.0),
}
# Medidas que se cuentan (no admiten decimales)
COUNT_UNITS = ("un.", "paquete", "caja", "lata", "botella")

# Atajos de cantidad según la medida (los más usados al comprar)
QUICK_AMOUNTS = {
    "g": (250, 500, 1000),
    "ml": (250, 500, 1000),
    "kg": (0.5, 1, 2),
    "L": (1, 2, 3),
}
DEFAULT_QUICK_AMOUNTS = (1, 2, 6)

# Medida sugerida al crear un producto según su categoría (solo donde casi siempre aplica:
# en Lácteos conviven leche, queso y yogur, así que ahí se deja la unidad)
_UNIT_BY_CATEGORY = {
    "Bebidas": "L",
    "Carnes": "kg",
}


def unit_options():
    """Medidas disponibles, en el orden en que se muestran."""
    return list(PANTRY_UNITS)


def is_count_unit(unit):
    """True si la medida se cuenta en enteros (unidades, paquetes, latas...)."""
    return unit in COUNT_UNITS


def quick_amounts(unit, integer_only=False):
    """Atajos de cantidad para la medida (en listas solo enteros)."""
    if integer_only:
        return DEFAULT_QUICK_AMOUNTS
    return QUICK_AMOUNTS.get(unit, DEFAULT_QUICK_AMOUNTS)


def step_for(unit, integer_only=False):
    """Paso de los botones − y + (en listas siempre de a 1)."""
    return 1.0 if integer_only else step_for_unit(unit)


def clamp_quantity(value, unit, integer_only=False, minimum=0.0):
    """Ajusta la cantidad al rango válido y a los decimales que admite la medida."""
    value = max(float(minimum), min(float(QUANTITY_MAX), float(value)))
    if integer_only or is_count_unit(unit):
        # Al redondear no se baja del mínimo (mínimo 0,01 en una medida que se cuenta = 1)
        return float(max(round(value), math.ceil(float(minimum))))
    return round(value, 2)


def convert_quantity(value, from_unit, to_unit):
    """Convierte la cantidad al cambiar de medida.

    - kg <-> g y L <-> ml: conversión exacta (1,5 kg -> 1500 g).
    - Hacia una medida que se cuenta: entero, mínimo 1.
    - Otros cambios: conserva el número.
    """
    if from_unit == to_unit:
        return value
    src, dst = _CONVERTIBLE.get(from_unit), _CONVERTIBLE.get(to_unit)
    if src and dst and src[0] == dst[0]:
        return round(value * src[1] / dst[1], 3)
    if is_count_unit(to_unit):
        return float(max(1, round(value)))
    return value


def to_stock_quantity(value, list_unit, stock_unit):
    """Cantidad a sumar al stock en la medida de la despensa.

    Solo convierte entre medidas de la misma familia (500 g -> 0,5 kg); si no se
    pueden convertir (paquete y kg), se suma el número tal cual.
    """
    src, dst = _CONVERTIBLE.get(list_unit), _CONVERTIBLE.get(stock_unit)
    if src and dst and src[0] == dst[0]:
        return convert_quantity(value, list_unit, stock_unit)
    return float(value)


def parse_typed_quantity(text, minimum=0.0):
    """Interpreta lo que el usuario escribe (1,5 / 500 / 1.500). Retorna (valor, error)."""
    value = parse_number(text)
    if value is None:
        return None, "Escribe la cantidad con números, por ejemplo 2 o 1,5."
    if value < minimum:
        return None, f"La cantidad mínima es {format_number(minimum)}."
    if value < 0:
        return None, "La cantidad no puede ser negativa."
    if value > QUANTITY_MAX:
        return None, f"La cantidad no puede superar {format_number(QUANTITY_MAX)}."
    return value, ""


def format_amount(value, unit=""):
    """Texto de una cantidad con su medida: '1,5 kg', '2 un.'."""
    text = format_number(value)
    return f"{text} {unit}".strip()


def suggested_unit(category):
    """Medida sugerida para un producto nuevo según su categoría."""
    return _UNIT_BY_CATEGORY.get(category, PANTRY_UNITS[0])
