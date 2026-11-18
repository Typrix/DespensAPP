# -*- coding: utf-8 -*-
"""
Preferencias del dispositivo (no del usuario): por ahora el modo oscuro.
Se guardan en un JSON aparte de session.json para que sobrevivan al cerrar la
app y al cerrar sesión.
"""

import json
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PREFS_PATH = os.path.join(PROJECT_ROOT, "user_prefs.json")


def load_preferences() -> dict:
    """Lee las preferencias; si el archivo falta o está dañado, retorna {}."""
    try:
        with open(PREFS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_preference(key: str, value) -> bool:
    """Guarda una preferencia conservando las demás. Retorna False si no se pudo escribir."""
    data = load_preferences()
    data[key] = value
    try:
        with open(PREFS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except OSError as e:
        print(f"[Prefs] No se pudo guardar la preferencia: {e}")
        return False


def is_dark_mode() -> bool:
    return bool(load_preferences().get("dark_mode", False))


def set_dark_mode(enabled: bool) -> bool:
    return save_preference("dark_mode", bool(enabled))
