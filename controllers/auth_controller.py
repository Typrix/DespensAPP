# -*- coding: utf-8 -*-
"""
Controlador de Autenticación y Sesiones para DespensAPP.
Controla el inicio de sesión, registro con hash SHA-256 y persistencia
del usuario activo en la sesión.
"""

import os
import json
import hashlib
from typing import Optional, Tuple

from models.user import User
from models.database import DatabaseManager

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SESSION_PATH = os.path.join(PROJECT_ROOT, "session.json")


class AuthController:
    """Gestiona la sesión del usuario activo y la seguridad de contraseñas."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.current_user: Optional[User] = None
        self._load_session()

    @staticmethod
    def hash_password(password: str) -> str:
        """Genera un hash SHA-256 seguro a partir de la contraseña."""
        return hashlib.sha256(password.strip().encode("utf-8")).hexdigest()

    def is_authenticated(self) -> bool:
        """Indica si hay un usuario autenticado activo."""
        return self.current_user is not None

    def _load_session(self):
        """Restaura la sesión del último usuario si existe archivo session.json."""
        if os.path.exists(SESSION_PATH):
            try:
                with open(SESSION_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    user_email = data.get("email")
                    user_id = data.get("user_id")

                    if user_email and hasattr(self.db, "get_user_by_email"):
                        user = self.db.get_user_by_email(user_email)
                        if user:
                            self.current_user = user
                            return

                    if user_id:
                        user = self.db.get_user_by_id(user_id)
                        if user:
                            self.current_user = user
                            return
            except Exception as e:
                print(f"[Auth] Error al cargar sesión: {e}")

        self.current_user = None

    def _save_session(self):
        """Persiste los datos de sesión en session.json."""
        if not self.current_user:
            return
        try:
            with open(SESSION_PATH, "w", encoding="utf-8") as f:
                json.dump({
                    "user_id": self.current_user.id,
                    "email": self.current_user.email,
                    "name": self.current_user.name
                }, f, indent=4)
        except Exception as e:
            print(f"[Auth] Error al guardar sesión: {e}")

    def login(self, email: str, password: str) -> Tuple[bool, str]:
        """Inicia sesión con correo y contraseña, validando disponibilidad de servidor."""
        email = email.strip().lower()
        pwd_hash = self.hash_password(password)

        if not self.db.is_mysql:
            success, message, user = self.db.authenticate_user(email, pwd_hash)
            if success and user:
                self.current_user = user
                self._save_session()
                return True, f"¡Bienvenido/a de nuevo, {user.name}! (Modo Local)"
            return False, "⚠️ Sin conexión a la base central: Solo es posible acceder con cuentas previamente almacenadas en este equipo."

        success, message, user = self.db.authenticate_user(email, pwd_hash)
        if success and user:
            self.current_user = user
            self._save_session()
            return True, f"¡Bienvenido/a de nuevo, {user.name}!"
        return False, message

    def register(self, name: str, email: str, password: str) -> Tuple[bool, str]:
        """Crea una nueva cuenta de usuario. Requiere conexión al servidor central."""
        if not self.db.is_mysql:
            return False, "⚠️ Conexión requerida: Para registrar una nueva cuenta necesitas estar conectado a la base de datos central (MySQL)."

        if len(password.strip()) < 4:
            return False, "La contraseña debe tener al menos 4 caracteres."
        pwd_hash = self.hash_password(password)
        success, message, user = self.db.register_user(name, email, pwd_hash)
        if success and user:
            self.current_user = user
            self._save_session()
            return True, f"Cuenta creada con éxito. ¡Bienvenido/a, {user.name}!"
        return False, message

    def logout(self):
        """Cierra la sesión actual y elimina la persistencia de sesión."""
        self.current_user = None
        if os.path.exists(SESSION_PATH):
            try:
                os.remove(SESSION_PATH)
            except Exception as e:
                print(f"[Auth] Error al eliminar sesión: {e}")


# Alias de compatibilidad
AuthManager = AuthController
