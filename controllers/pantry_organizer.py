# -*- coding: utf-8 -*-
"""
Organizador de la despensa para DespensAPP (lógica pura, sin Kivy).
Ordena los productos por urgencia, los agrupa en secciones y aplica búsqueda y filtros.
"""

import unicodedata
from typing import Any, Dict, Iterable, List

from models.pantry_item import PantryItem

DEFAULT_CATEGORY = "General"

# Categoría -> icono Material Design para la fila de despensa
CATEGORY_ICONS = {
    "General": "leaf",
    "Lácteos": "cup-water",
    "Frescos": "food-apple-outline",
    "Carnes": "food-drumstick-outline",
    "Despensa seca": "grain",
    "Bebidas": "bottle-soda-classic-outline",
    "Congelados": "snowflake",
    "Limpieza": "spray-bottle",
    "Higiene": "hand-wash-outline",
}
PANTRY_CATEGORIES = list(CATEGORY_ICONS.keys())

# Categorías antiguas (datos de ejemplo previos) -> categoría del catálogo
LEGACY_CATEGORIES = {
    "Legumbres": "Despensa seca",
    "Aceites": "Despensa seca",
    "Granos": "Despensa seca",
    "Frutas": "Frescos",
    "Verduras": "Frescos",
}

# Secciones visibles: clave -> (título, color del punto)
SECTION_ATTENTION = "attention"
SECTION_LOW = "low"
SECTION_OK = "ok"
SECTIONS = {
    SECTION_ATTENTION: ("Necesita atención", [0.85, 0.20, 0.25, 1.0]),
    SECTION_LOW: ("Por agotarse", [0.82, 0.48, 0.12, 1.0]),
    SECTION_OK: ("Todo bien", [0.12, 0.58, 0.32, 1.0]),
}

# Filtros rápidos
FILTER_ALL = "all"
FILTER_EXPIRING = "expiring"
FILTER_LOW = "low"
CATEGORY_FILTER_PREFIX = "category:"


def normalize_text(text: str) -> str:
    """Minúsculas, sin tildes y sin espacios extra (para buscar 'cafe' y encontrar 'Café')."""
    decomposed = unicodedata.normalize("NFKD", text or "")
    plain = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join(plain.lower().split())


def category_of(item: PantryItem) -> str:
    """Categoría visible del producto (antiguas se mapean; desconocidas o vacías -> 'General')."""
    cat = (item.category or "").strip()
    cat = LEGACY_CATEGORIES.get(cat, cat)
    return cat if cat in CATEGORY_ICONS else DEFAULT_CATEGORY


def category_icon(category: str) -> str:
    return CATEGORY_ICONS.get(category, CATEGORY_ICONS[DEFAULT_CATEGORY])


def is_low_stock(item: PantryItem) -> bool:
    """Sin stock o bajo el mínimo de alerta."""
    return item.status in ("Reponer", "Por agotarse")


def urgency_rank(item: PantryItem) -> int:
    """Prioridad (menor = más urgente): vencido, sin stock, por vencer, por agotarse, bien."""
    if item.is_expired:
        return 0
    if item.quantity <= 0:
        return 1
    if item.is_expiring_soon:
        return 2
    if item.status == "Por agotarse":
        return 3
    return 4


def section_of(item: PantryItem) -> str:
    rank = urgency_rank(item)
    if rank <= 2:
        return SECTION_ATTENTION
    if rank == 3:
        return SECTION_LOW
    return SECTION_OK


def _sort_key(item: PantryItem):
    days = item.days_until_expiration
    return (urgency_rank(item), days if days is not None else 10 ** 6, normalize_text(item.name))


def matches_filter(item: PantryItem, filter_key: str) -> bool:
    if not filter_key or filter_key == FILTER_ALL:
        return True
    if filter_key == FILTER_EXPIRING:
        return item.is_expired or item.is_expiring_soon
    if filter_key == FILTER_LOW:
        return is_low_stock(item)
    if filter_key.startswith(CATEGORY_FILTER_PREFIX):
        return category_of(item) == filter_key[len(CATEGORY_FILTER_PREFIX):]
    return True


def matches_query(item: PantryItem, query: str) -> bool:
    q = normalize_text(query)
    return not q or q in normalize_text(item.name)


def filter_counts(items: Iterable[PantryItem]) -> Dict[str, int]:
    """Conteos para los chips: total, por vencer, por agotarse y por categoría en uso."""
    items = list(items)
    counts = {
        FILTER_ALL: len(items),
        FILTER_EXPIRING: sum(1 for it in items if matches_filter(it, FILTER_EXPIRING)),
        FILTER_LOW: sum(1 for it in items if is_low_stock(it)),
    }
    for it in items:
        key = CATEGORY_FILTER_PREFIX + category_of(it)
        counts[key] = counts.get(key, 0) + 1
    return counts


def used_categories(items: Iterable[PantryItem]) -> List[str]:
    """Categorías presentes, en el orden del catálogo."""
    present = {category_of(it) for it in items}
    return [c for c in PANTRY_CATEGORIES if c in present]


def group_pantry(items: Iterable[PantryItem], query: str = "", filter_key: str = FILTER_ALL) -> List[Dict[str, Any]]:
    """
    Aplica búsqueda y filtro, ordena por urgencia y agrupa en secciones no vacías:
    [{key, title, color, items}] en el orden Necesita atención -> Por agotarse -> Todo bien.
    """
    visible = [it for it in items if matches_query(it, query) and matches_filter(it, filter_key)]
    visible.sort(key=_sort_key)
    grouped: Dict[str, List[PantryItem]] = {key: [] for key in SECTIONS}
    for it in visible:
        grouped[section_of(it)].append(it)
    return [
        {"key": key, "title": SECTIONS[key][0], "color": SECTIONS[key][1], "items": grouped[key]}
        for key in SECTIONS if grouped[key]
    ]


def restock_candidates(items: Iterable[PantryItem]) -> List[PantryItem]:
    """Productos sin stock o por agotarse (para 'Añadir lo que falta a una lista')."""
    return sorted((it for it in items if is_low_stock(it)), key=_sort_key)
