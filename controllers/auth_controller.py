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

    def _ensure_local_users_table(self):
        """Asegura que la tabla local de usuarios y de cambios de perfil exista en SQLite."""
        if not hasattr(self.db, "get_sqlite_connection"):
            return None
        try:
            conn = self.db.get_sqlite_connection()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    avatar_initials TEXT DEFAULT 'US',
                    is_pro INTEGER DEFAULT 0
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS local_user_overrides (
                    user_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    avatar_initials TEXT DEFAULT 'US',
                    is_pro INTEGER DEFAULT 0
                );
            """)
            conn.commit()
            return conn
        except Exception as e:
            print(f"[Auth] Error asegurando tabla local users: {e}")
            return None

    def _save_local_override(self, user: User):
        """Guarda los datos actualizados del usuario en SQLite local para persistir cambios de nombre, correo y contraseña."""
        if not user:
            return
        conn = self._ensure_local_users_table()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM users WHERE id = ? OR LOWER(email) = ?;", (user.id, user.email.lower()))
            cur.execute(
                """INSERT INTO users (id, name, email, password_hash, avatar_initials, is_pro)
                   VALUES (?, ?, ?, ?, ?, ?);""",
                (
                    user.id,
                    user.name,
                    user.email.lower(),
                    user.password_hash or "",
                    user.avatar_initials or User.generate_initials(user.name),
                    int(user.is_pro or 0),
                ),
            )
            cur.execute(
                """INSERT OR REPLACE INTO local_user_overrides
                   (user_id, name, email, password_hash, avatar_initials, is_pro)
                   VALUES (?, ?, ?, ?, ?, ?);""",
                (
                    user.id,
                    user.name,
                    user.email.lower(),
                    user.password_hash or "",
                    user.avatar_initials or User.generate_initials(user.name),
                    int(user.is_pro or 0),
                ),
            )
            conn.commit()
        except Exception as e:
            print(f"[Auth] Error guardando override local de usuario: {e}")
        finally:
            conn.close()

    def _get_local_override_by_user_id(self, user_id: int) -> Optional[User]:
        """Obtiene el perfil actualizado localmente por ID de usuario."""
        conn = self._ensure_local_users_table()
        if not conn:
            return None
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM local_user_overrides WHERE user_id = ?;", (user_id,))
            row = cur.fetchone()
            if row:
                return User(
                    id=row["user_id"],
                    name=row["name"],
                    email=row["email"],
                    avatar_initials=row["avatar_initials"] or User.generate_initials(row["name"]),
                    password_hash=row["password_hash"] or "",
                    is_pro=int(row["is_pro"] or 0),
                )
        except Exception:
            pass
        finally:
            conn.close()
        return None

    def _get_local_override_by_email(self, email: str) -> Optional[User]:
        """Obtiene el perfil actualizado localmente por correo electrónico."""
        conn = self._ensure_local_users_table()
        if not conn:
            return None
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM local_user_overrides WHERE LOWER(email) = ?;", (email.strip().lower(),))
            row = cur.fetchone()
            if row:
                return User(
                    id=row["user_id"],
                    name=row["name"],
                    email=row["email"],
                    avatar_initials=row["avatar_initials"] or User.generate_initials(row["name"]),
                    password_hash=row["password_hash"] or "",
                    is_pro=int(row["is_pro"] or 0),
                )
        except Exception:
            pass
        finally:
            conn.close()
        return None

    def _apply_override_to_user(self, user: Optional[User]) -> Optional[User]:
        """Si existen cambios locales de perfil para este usuario, los aplica sobre la entidad."""
        if not user:
            return None
        override = self._get_local_override_by_user_id(user.id)
        if override:
            user.name = override.name
            user.email = override.email
            user.avatar_initials = override.avatar_initials
            if override.password_hash:
                user.password_hash = override.password_hash
        return user

    def _load_session(self):
        """Restaura la sesión del último usuario si existe archivo session.json."""
        if os.path.exists(SESSION_PATH):
            try:
                with open(SESSION_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    user_email = data.get("email")
                    user_id = data.get("user_id")

                    if user_id:
                        override = self._get_local_override_by_user_id(user_id)
                        user = self.db.get_user_by_id(user_id)
                        if user:
                            self.current_user = self._apply_override_to_user(user)
                            return
                        if override:
                            self.current_user = override
                            return

                    if user_email and hasattr(self.db, "get_user_by_email"):
                        override = self._get_local_override_by_email(user_email)
                        if override:
                            self.current_user = override
                            return
                        user = self.db.get_user_by_email(user_email)
                        if user:
                            self.current_user = self._apply_override_to_user(user)
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
                    "name": self.current_user.name,
                    "is_pro": int(self.current_user.is_pro or 0),
                }, f, indent=4)
        except Exception as e:
            print(f"[Auth] Error al guardar sesión: {e}")

    def update_profile(self, name: str, email: str, new_password: str = "") -> Tuple[bool, str]:
        """Actualiza nombre, correo electrónico y opcionalmente contraseña del usuario activo."""
        if not self.current_user:
            return False, "No hay una sesión activa para actualizar."

        clean_name = (name or "").strip()
        clean_email = (email or "").strip().lower()
        clean_pass = (new_password or "").strip()

        if not clean_name:
            return False, "El nombre no puede estar vacío."
        if not clean_email or "@" not in clean_email or "." not in clean_email.split("@")[-1]:
            return False, "Ingresa un correo electrónico válido."
        if clean_pass and len(clean_pass) < 4:
            return False, "La nueva contraseña debe tener al menos 4 caracteres."

        pwd_hash = self.hash_password(clean_pass) if clean_pass else None

        try:
            ok, msg, updated_user = self.db.update_user_profile(
                self.current_user.id,
                clean_name,
                clean_email,
                pwd_hash,
            )
        except Exception as e:
            return False, f"Error al actualizar la cuenta: {e}"

        if not ok:
            return False, msg or "No se pudo actualizar la cuenta."

        if updated_user:
            if pwd_hash:
                updated_user.password_hash = pwd_hash
            elif self.current_user and self.current_user.password_hash and not updated_user.password_hash:
                updated_user.password_hash = self.current_user.password_hash
            self.current_user = updated_user
        else:
            self.current_user.name = clean_name
            self.current_user.email = clean_email
            self.current_user.avatar_initials = User.generate_initials(clean_name)
            if pwd_hash:
                self.current_user.password_hash = pwd_hash

        self._save_local_override(self.current_user)
        self._save_session()
        return True, msg or "Datos de la cuenta actualizados con éxito."

    def is_pro_user(self) -> bool:
        """Indica si el usuario activo tiene la versión Pro activada (is_pro == 1)."""
        return bool(self.current_user and int(self.current_user.is_pro or 0) == 1)

    def upgrade_to_pro(self) -> Tuple[bool, str]:
        """Activa la versión Pro (is_pro = 1) en la base de datos para el usuario actual."""
        if not self.current_user:
            return False, "Debes iniciar sesión para activar la versión Pro."
        updated = self.db.update_user_pro_status(self.current_user.id, 1)
        if not updated:
            return False, "No se pudo actualizar el estado Pro en la base de datos."
        self.current_user.is_pro = 1
        self._save_local_override(self.current_user)
        self._save_session()
        return True, "¡Versión Pro activada con éxito!"

    def login(self, email: str, password: str) -> Tuple[bool, str]:
        """Inicia sesión con correo y contraseña, respetando cambios de perfil y contraseña guardados."""
        email = email.strip().lower()
        pwd_hash = self.hash_password(password)

        # 1. Verificar si la cuenta fue actualizada localmente (nuevo correo o nueva contraseña)
        override_by_email = self._get_local_override_by_email(email)
        if override_by_email and override_by_email.password_hash:
            if override_by_email.password_hash != pwd_hash:
                return False, "Contraseña incorrecta"
            # Recuperar estado Pro más reciente del servidor si está disponible
            remote_user = self.db.get_user_by_id(override_by_email.id)
            if remote_user:
                override_by_email.is_pro = int(remote_user.is_pro or override_by_email.is_pro or 0)
            self.current_user = override_by_email
            self._save_session()
            return True, f"¡Bienvenido/a de nuevo, {override_by_email.name}!"

        if not self.db.is_mysql:
            success, message, user = self.db.authenticate_user(email, pwd_hash)
            if success and user:
                user = self._apply_override_to_user(user)
                self.current_user = user
                self._save_session()
                return True, f"¡Bienvenido/a de nuevo, {user.name}! (Modo Local)"
            return False, "⚠️ Sin conexión a la base central: Solo es posible acceder con cuentas previamente almacenadas en este equipo."

        # 2. Si el usuario cambió su correo o contraseña localmente, impedir acceso con credenciales antiguas
        existing_remote = self.db.get_user_by_email(email)
        if existing_remote:
            override_by_id = self._get_local_override_by_user_id(existing_remote.id)
            if override_by_id:
                if override_by_id.email.lower() != email:
                    return False, "No existe ninguna cuenta con ese correo."
                if override_by_id.password_hash and override_by_id.password_hash != pwd_hash:
                    return False, "Contraseña incorrecta"
                override_by_id.is_pro = int(existing_remote.is_pro or override_by_id.is_pro or 0)
                self.current_user = override_by_id
                self._save_session()
                return True, f"¡Bienvenido/a de nuevo, {override_by_id.name}!"

        success, message, user = self.db.authenticate_user(email, pwd_hash)
        if success and user:
            user = self._apply_override_to_user(user)
            self.current_user = user
            self._save_local_override(user)
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
