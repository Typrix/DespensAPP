# -*- coding: utf-8 -*-
"""
Modelo de Usuario para DespensAPP.
Representa un usuario registrado y gestiona sus iniciales de perfil.
"""

from dataclasses import dataclass


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
