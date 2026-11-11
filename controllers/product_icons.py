# -*- coding: utf-8 -*-
"""
Íconos por producto para DespensAPP (lógica pura, sin Kivy).
Asocia el nombre del producto a un ícono de Material Design y a una categoría sugerida.
Si el nombre no coincide con nada conocido, se usa el ícono de la categoría.
"""

from typing import Optional, Tuple

from models.pantry_item import PantryItem
from controllers.pantry_organizer import normalize_text, category_icon, category_of, DEFAULT_CATEGORY

# Frases de varias palabras: ganan siempre (p. ej. "pasta de dientes" no es "pasta")
PHRASE_ICONS = {
    "papel higienico": ("paper-roll", "Higiene"),
    "pasta de dientes": ("toothbrush", "Higiene"),
    "pasta dental": ("toothbrush", "Higiene"),
    "toalla higienica": ("paper-roll-outline", "Higiene"),
    "toalla de papel": ("paper-roll-outline", "Limpieza"),
    "salsa de soya": ("soy-sauce", "Despensa seca"),
    "lava loza": ("spray-bottle", "Limpieza"),
    "comida de perro": ("dog", "General"),
    "comida de gato": ("cat", "General"),
    "pan de molde": ("bread-slice", "Despensa seca"),
    "crema corporal": ("lotion-outline", "Higiene"),
    "crema de manos": ("lotion-outline", "Higiene"),
}

# Palabra (normalizada y en singular) -> (ícono, categoría sugerida)
WORD_ICONS = {
    # Lácteos
    "leche": ("cup-water", "Lácteos"),
    "yogur": ("cup-outline", "Lácteos"),
    "yogurt": ("cup-outline", "Lácteos"),
    "yoghurt": ("cup-outline", "Lácteos"),
    "queso": ("cheese", "Lácteos"),
    "quesillo": ("cheese", "Lácteos"),
    "mantequilla": ("cube-outline", "Lácteos"),
    "margarina": ("cube-outline", "Lácteos"),
    "crema": ("cup-outline", "Lácteos"),
    "manjar": ("cup-outline", "Lácteos"),
    # Frescos
    "huevo": ("egg", "Frescos"),
    "manzana": ("food-apple", "Frescos"),
    "platano": ("nutrition", "Frescos"),
    "banana": ("nutrition", "Frescos"),
    "naranja": ("fruit-citrus", "Frescos"),
    "mandarina": ("fruit-citrus", "Frescos"),
    "limon": ("fruit-citrus", "Frescos"),
    "uva": ("fruit-grapes", "Frescos"),
    "cereza": ("fruit-cherries", "Frescos"),
    "frutilla": ("fruit-cherries", "Frescos"),
    "fresa": ("fruit-cherries", "Frescos"),
    "pera": ("fruit-pear", "Frescos"),
    "palta": ("fruit-pear", "Frescos"),
    "aguacate": ("fruit-pear", "Frescos"),
    "pina": ("fruit-pineapple", "Frescos"),
    "sandia": ("fruit-watermelon", "Frescos"),
    "melon": ("fruit-watermelon", "Frescos"),
    "zanahoria": ("carrot", "Frescos"),
    "choclo": ("corn", "Frescos"),
    "maiz": ("corn", "Frescos"),
    "champinon": ("mushroom-outline", "Frescos"),
    "hongo": ("mushroom-outline", "Frescos"),
    "aji": ("chili-mild", "Frescos"),
    "pimenton": ("chili-mild", "Frescos"),
    "pimiento": ("chili-mild", "Frescos"),
    "tomate": ("food-apple-outline", "Frescos"),
    "lechuga": ("leaf", "Frescos"),
    "espinaca": ("leaf", "Frescos"),
    "acelga": ("leaf", "Frescos"),
    "cilantro": ("leaf", "Frescos"),
    "perejil": ("leaf", "Frescos"),
    "brocoli": ("sprout-outline", "Frescos"),
    "cebolla": ("sprout-outline", "Frescos"),
    "ajo": ("sprout-outline", "Frescos"),
    "papa": ("sprout-outline", "Frescos"),
    "patata": ("sprout-outline", "Frescos"),
    "fruta": ("food-apple-outline", "Frescos"),
    "verdura": ("sprout-outline", "Frescos"),
    # Carnes y pescados
    "pollo": ("food-drumstick", "Carnes"),
    "pavo": ("food-turkey", "Carnes"),
    "carne": ("food-steak", "Carnes"),
    "vacuno": ("food-steak", "Carnes"),
    "res": ("food-steak", "Carnes"),
    "bistec": ("food-steak", "Carnes"),
    "cerdo": ("pig-variant-outline", "Carnes"),
    "chuleta": ("food-steak", "Carnes"),
    "tocino": ("pig-variant-outline", "Carnes"),
    "jamon": ("pig-variant-outline", "Carnes"),
    "salchicha": ("sausage", "Carnes"),
    "vienesa": ("sausage", "Carnes"),
    "chorizo": ("sausage", "Carnes"),
    "longaniza": ("sausage", "Carnes"),
    "pescado": ("fish", "Carnes"),
    "salmon": ("fish", "Carnes"),
    "merluza": ("fish", "Carnes"),
    "atun": ("fish", "Despensa seca"),
    "sardina": ("fish", "Despensa seca"),
    "camaron": ("fish", "Carnes"),
    # Despensa seca
    "arroz": ("rice", "Despensa seca"),
    "fideo": ("pasta", "Despensa seca"),
    "pasta": ("pasta", "Despensa seca"),
    "spaghetti": ("pasta", "Despensa seca"),
    "tallarin": ("noodles", "Despensa seca"),
    "ramen": ("noodles", "Despensa seca"),
    "pan": ("bread-slice-outline", "Despensa seca"),
    "marraqueta": ("baguette", "Despensa seca"),
    "hallulla": ("baguette", "Despensa seca"),
    "baguette": ("baguette", "Despensa seca"),
    "croissant": ("food-croissant", "Despensa seca"),
    "harina": ("sack-outline", "Despensa seca"),
    "azucar": ("spoon-sugar", "Despensa seca"),
    "endulzante": ("spoon-sugar", "Despensa seca"),
    "sal": ("shaker-outline", "Despensa seca"),
    "pimienta": ("shaker-outline", "Despensa seca"),
    "oregano": ("shaker-outline", "Despensa seca"),
    "comino": ("shaker-outline", "Despensa seca"),
    "aceite": ("bottle-tonic-outline", "Despensa seca"),
    "vinagre": ("bottle-tonic-outline", "Despensa seca"),
    "salsa": ("bottle-tonic-outline", "Despensa seca"),
    "ketchup": ("bottle-tonic-outline", "Despensa seca"),
    "mayonesa": ("bottle-tonic-outline", "Despensa seca"),
    "mostaza": ("bottle-tonic-outline", "Despensa seca"),
    "frijol": ("seed-outline", "Despensa seca"),
    "poroto": ("seed-outline", "Despensa seca"),
    "lenteja": ("seed-outline", "Despensa seca"),
    "garbanzo": ("seed-outline", "Despensa seca"),
    "mani": ("peanut-outline", "Despensa seca"),
    "almendra": ("peanut-outline", "Despensa seca"),
    "nuez": ("peanut-outline", "Despensa seca"),
    "avena": ("grain", "Despensa seca"),
    "cereal": ("bowl-mix-outline", "Despensa seca"),
    "granola": ("bowl-mix-outline", "Despensa seca"),
    "sopa": ("bowl-mix-outline", "Despensa seca"),
    "galleta": ("cookie-outline", "Despensa seca"),
    "chocolate": ("candy-outline", "Despensa seca"),
    "dulce": ("candy-outline", "Despensa seca"),
    "mermelada": ("fruit-cherries", "Despensa seca"),
    "miel": ("bee", "Despensa seca"),
    "cafe": ("coffee-outline", "Despensa seca"),
    "te": ("tea-outline", "Despensa seca"),
    "palomita": ("popcorn", "Despensa seca"),
    "cabrita": ("popcorn", "Despensa seca"),
    # Bebidas
    "agua": ("water-outline", "Bebidas"),
    "jugo": ("glass-tulip", "Bebidas"),
    "bebida": ("bottle-soda-classic-outline", "Bebidas"),
    "gaseosa": ("bottle-soda-classic-outline", "Bebidas"),
    "soda": ("bottle-soda-classic-outline", "Bebidas"),
    "coca": ("bottle-soda-classic-outline", "Bebidas"),
    "vino": ("bottle-wine-outline", "Bebidas"),
    "cerveza": ("beer-outline", "Bebidas"),
    "pisco": ("glass-cocktail", "Bebidas"),
    # Congelados
    "helado": ("ice-cream", "Congelados"),
    "hielo": ("cube-outline", "Congelados"),
    "pizza": ("pizza", "Congelados"),
    "hamburguesa": ("hamburger", "Congelados"),
    "nugget": ("food-drumstick", "Congelados"),
    # Limpieza
    "detergente": ("spray-bottle", "Limpieza"),
    "lavaloza": ("spray-bottle", "Limpieza"),
    "cloro": ("spray-bottle", "Limpieza"),
    "limpiador": ("spray-bottle", "Limpieza"),
    "desinfectante": ("spray-bottle", "Limpieza"),
    "suavizante": ("spray-bottle", "Limpieza"),
    "esponja": ("spray-bottle", "Limpieza"),
    "escoba": ("broom", "Limpieza"),
    "servilleta": ("paper-roll-outline", "Limpieza"),
    "bolsa": ("sack-outline", "Limpieza"),
    # Higiene
    "jabon": ("hand-wash-outline", "Higiene"),
    "shampoo": ("lotion-outline", "Higiene"),
    "champu": ("lotion-outline", "Higiene"),
    "acondicionador": ("lotion-outline", "Higiene"),
    "desodorante": ("spray", "Higiene"),
    "dentifrico": ("toothbrush", "Higiene"),
    "cepillo": ("toothbrush", "Higiene"),
    "panal": ("baby-face-outline", "Higiene"),
    # Mascotas
    "perro": ("dog", "General"),
    "gato": ("cat", "General"),
}


def _singular_variants(word: str):
    """'huevos' -> huevos, huevo; 'limones' -> limones, limone, limon."""
    yield word
    if len(word) > 3 and word.endswith("s"):
        yield word[:-1]
        if word.endswith("es"):
            yield word[:-2]


def match_product(name: str) -> Optional[Tuple[str, str]]:
    """
    (ícono, categoría) para un nombre, o None si no se reconoce.
    Primero frases ("pasta de dientes"); luego la primera palabra reconocida,
    que en español suele ser el sustantivo principal ("leche de almendra" -> leche).
    """
    text = normalize_text(name)
    if not text:
        return None
    padded = f" {text} "
    for phrase, value in PHRASE_ICONS.items():
        if f" {phrase} " in padded:
            return value
    for word in text.replace("-", " ").split():
        for variant in _singular_variants(word):
            if variant in WORD_ICONS:
                return WORD_ICONS[variant]
    return None


def suggest_category(name: str) -> Optional[str]:
    """Categoría sugerida para el formulario al escribir el nombre (None si no se reconoce)."""
    match = match_product(name)
    return match[1] if match else None


def product_icon(name: str, category: str) -> str:
    """Ícono del producto; si el nombre no se reconoce, el de su categoría."""
    match = match_product(name)
    return match[0] if match else category_icon(category)


def item_icon(item: PantryItem) -> str:
    return product_icon(item.name, category_of(item))


def name_visual(name: str) -> Tuple[str, str]:
    """(ícono, categoría para el color) de un nombre suelto, p. ej. un producto de una lista."""
    match = match_product(name)
    return match if match else (category_icon(DEFAULT_CATEGORY), DEFAULT_CATEGORY)
