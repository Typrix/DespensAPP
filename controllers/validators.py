# -*- coding: utf-8 -*-
"""
Validación y parseo de formularios para DespensAPP.
Lógica pura (sin Kivy) para interpretar números en formato chileno
(punto de miles, coma decimal) y validar los formularios de carrito, despensa y listas.
"""

import re
from datetime import datetime, date

# Unidades predefinidas disponibles en el menú desplegable de despensa
PANTRY_UNITS = ["un.", "kg", "g", "L", "ml", "paquete", "caja", "lata", "botella"]
NAME_MAX_LENGTH = 50
SUBTITLE_MAX_LENGTH = 40
QUANTITY_MAX = 100000
PRICE_MAX = 99_999_999
LIST_ITEMS_MAX = 50

# Paso de ajuste rápido de stock según la unidad (+/- en el detalle de despensa)
UNIT_STEPS = {"g": 100.0, "ml": 100.0, "kg": 0.5, "L": 0.5}

# Caracteres permitidos al escribir números (dígitos, separadores y signo peso)
_NUMERIC_CHARS = set("0123456789.,$")
# Número con punto de miles: 1.500 / 12.345.678
_THOUSANDS_RE = re.compile(r"^\d{1,3}(\.\d{3})+$")


def numeric_input_filter(substring, from_undo=False):
    """Filtro de TextInput: deja pasar solo dígitos, '.', ',' y '$'."""
    return "".join(ch for ch in substring if ch in _NUMERIC_CHARS)


def parse_number(raw):
    """
    Convierte texto numérico en float aceptando formato chileno.
    - '1.500' / '$1.500' / '12.345.678' -> miles (1500, 12345678)
    - '1,5' / '1.500,75' -> coma decimal
    - '0.5' / '2.25' -> punto decimal (no calza con patrón de miles)
    Retorna None si el texto está vacío o no es un número válido.
    """
    text = (raw or "").strip().replace("$", "").replace(" ", "")
    if not text:
        return None

    if "," in text:
        # Coma decimal: los puntos solo pueden ser separadores de miles
        if text.count(",") > 1:
            return None
        int_part, dec_part = text.split(",")
        if "." in int_part and not _THOUSANDS_RE.match(int_part):
            return None
        text = int_part.replace(".", "") + "." + dec_part
    elif _THOUSANDS_RE.match(text):
        text = text.replace(".", "")

    try:
        value = float(text)
    except ValueError:
        return None
    if value != value or value in (float("inf"), float("-inf")):
        return None
    return value


def format_number(value):
    """Muestra un número sin decimales innecesarios y con coma decimal (ej: 1,5 / 500)."""
    if value == int(value):
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".").replace(".", ",")


def step_for_unit(unit):
    """Retorna el paso de ajuste rápido de stock adecuado para la unidad."""
    return UNIT_STEPS.get(unit, 1.0)


def _validate_name(name, label="el nombre"):
    """Valida un nombre de texto libre. Retorna (nombre_limpio, error)."""
    name = (name or "").strip()
    if not name:
        return None, f"Ingresa {label}."
    if len(name) < 2:
        return None, f"{label.capitalize()} debe tener al menos 2 caracteres."
    if len(name) > NAME_MAX_LENGTH:
        return None, f"{label.capitalize()} no puede superar {NAME_MAX_LENGTH} caracteres."
    return name, ""


def validate_quantity(quantity_str, label="La cantidad"):
    """Valida una cantidad de stock. Retorna (valor, error)."""
    if not (quantity_str or "").strip():
        return None, f"Ingresa {label.lower()}."
    value = parse_number(quantity_str)
    if value is None:
        return None, f"{label} debe ser un número válido (ej: 2, 1,5 o 500)."
    if value < 0 or value > QUANTITY_MAX:
        return None, f"{label} debe estar entre 0 y {QUANTITY_MAX}."
    return value, ""


def validate_cart_form(title, price_str, subtitle):
    """
    Valida el formulario de carrito.
    El precio es opcional (vacío = $0 para anotar sin conocerlo aún).
    Retorna (True, "", datos) o (False, mensaje_error, None).
    """
    title, error = _validate_name(title, "el nombre del producto")
    if error:
        return False, error, None

    price = 0.0
    if (price_str or "").strip():
        price = parse_number(price_str)
        if price is None:
            return False, "El precio debe ser un número (ej: 1.500 o $2.990).", None
        if price < 0 or price > PRICE_MAX:
            return False, "El precio está fuera de rango.", None

    subtitle = (subtitle or "").strip() or "General"
    if len(subtitle) > SUBTITLE_MAX_LENGTH:
        return False, f"La categoría no puede superar {SUBTITLE_MAX_LENGTH} caracteres.", None

    return True, "", {"title": title, "price": price, "subtitle": subtitle}


def validate_list_form(name, initial_items):
    """
    Valida el formulario de nueva lista de compras.
    Los productos iniciales se separan por coma o salto de línea.
    Retorna (True, "", datos) o (False, mensaje_error, None).
    """
    name, error = _validate_name(name, "el nombre de la lista")
    if error:
        return False, error, None

    items = [it.strip() for it in (initial_items or "").replace("\n", ",").split(",") if it.strip()]
    if len(items) > LIST_ITEMS_MAX:
        return False, f"Puedes anotar hasta {LIST_ITEMS_MAX} productos iniciales.", None
    too_long = [it for it in items if len(it) > NAME_MAX_LENGTH]
    if too_long:
        return False, f"'{too_long[0][:20]}…' supera {NAME_MAX_LENGTH} caracteres.", None

    return True, "", {"name": name, "initial_items": ", ".join(items)}


def expiration_warning(expiration_str):
    """Retorna un aviso si la fecha (AAAA-MM-DD) ya pasó; cadena vacía en otro caso."""
    try:
        parsed = datetime.strptime((expiration_str or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        return ""
    if parsed < date.today():
        return "Ojo: este producto ya está vencido."
    return ""


def validate_pantry_details(name, unit, threshold_str):
    """
    Valida la edición de un producto de despensa (nombre, unidad y mínimo de alerta).
    Retorna (True, "", datos) o (False, mensaje_error, None).
    """
    name, error = _validate_name(name, "el nombre del producto")
    if error:
        return False, error, None
    if unit not in PANTRY_UNITS:
        return False, "Selecciona una unidad de la lista.", None
    threshold, error = validate_quantity(threshold_str, "La cantidad mínima")
    if error:
        return False, error, None
    return True, "", {"name": name, "unit": unit, "threshold": threshold}


def validate_pantry_form(name, quantity_str, unit, threshold_str, expiration_str, has_no_expiration):
    """
    Valida los campos del formulario de despensa.
    Permite fechas pasadas (producto ya vencido); el aviso se muestra aparte.
    Retorna (True, "", datos_limpios) si es válido, o (False, mensaje_error, None).
    """
    name, error = _validate_name(name, "el nombre del producto")
    if error:
        return False, error, None

    quantity, error = validate_quantity(quantity_str, "La cantidad")
    if error:
        return False, error, None

    if unit not in PANTRY_UNITS:
        return False, "Selecciona una unidad de la lista.", None

    threshold, error = validate_quantity(threshold_str, "La cantidad mínima")
    if error:
        return False, error, None

    if has_no_expiration:
        exp_date = None
    else:
        expiration_str = (expiration_str or "").strip()
        if not expiration_str:
            return False, "Elige la fecha de vencimiento o marca 'no perecible'.", None
        try:
            parsed = datetime.strptime(expiration_str, "%Y-%m-%d").date()
        except ValueError:
            return False, "La fecha debe tener el formato AAAA-MM-DD.", None
        exp_date = parsed.strftime("%Y-%m-%d")

    return True, "", {
        "name": name,
        "quantity": quantity,
        "unit": unit,
        "threshold": threshold,
        "expiration_date": exp_date,
    }
