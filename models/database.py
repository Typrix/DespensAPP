# -*- coding: utf-8 -*-
"""
Capa de Persistencia para DespensAPP.
Gestiona la conexión y consultas a MySQL (PyMySQL) con soporte resiliente
para SQLite local como fallback de contingencia offline.
"""

import os
import json
import sqlite3
from typing import Optional, List, Tuple
try:
    import pymysql
    import pymysql.cursors
except ImportError:
    pymysql = None

from models.user import User
from models.cart_item import CartItem
from models.pantry_item import PantryItem
from models.shopping_list import ShoppingList, ShoppingListItem

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_PATH = os.path.join(PROJECT_ROOT, 'db_config.json')
LOCAL_DB_PATH = os.path.join(PROJECT_ROOT, 'despensapp_local.db')



class DatabaseManager:
    """Administrador centralizado de base de datos."""

    def __init__(self):
        self.is_mysql = False
        self.status_message = "Inicializando..."
        self.config = self._load_config()
        self.init_database()

    def _load_config(self) -> dict:
        """Carga la configuración de MySQL desde db_config.json."""
        default_cfg = {
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": "",
            "database": "despensapp_db"
        }
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[DB] Error al leer db_config.json: {e}")
        return default_cfg

    def save_config(self, host: str, port: int, user: str, password: str, database: str) -> bool:
        """Guarda la nueva configuración en db_config.json."""
        self.config = {
            "host": host.strip(),
            "port": int(port),
            "user": user.strip(),
            "password": password,
            "database": database.strip()
        }
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            print(f"[DB] Error al guardar db_config.json: {e}")
            return False

    def get_mysql_connection(self):
        """Retorna una conexión activa con el servidor MySQL."""
        return pymysql.connect(
            host=self.config.get("host", "localhost"),
            port=int(self.config.get("port", 3306)),
            user=self.config.get("user", "root"),
            password=self.config.get("password", ""),
            database=self.config.get("database", "despensapp_db"),
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
            connect_timeout=3
        )

    def get_sqlite_connection(self):
        """Retorna una conexión activa a la base local SQLite."""
        conn = sqlite3.connect(LOCAL_DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """Intenta inicializar las tablas en MySQL; si falla, inicializa SQLite."""
        try:
            # 1. Intentar conectar al servidor MySQL sin especificar BD para crearla si no existe
            server_conn = pymysql.connect(
                host=self.config.get("host", "localhost"),
                port=int(self.config.get("port", 3306)),
                user=self.config.get("user", "root"),
                password=self.config.get("password", ""),
                charset="utf8mb4",
                autocommit=True,
                connect_timeout=3
            )
            with server_conn.cursor() as cur:
                db_name = self.config.get("database", "despensapp_db")
                cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            server_conn.close()

            # 2. Conectar a la base de datos MySQL y crear tablas
            conn = self.get_mysql_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS `users` (
                        `id` INT AUTO_INCREMENT PRIMARY KEY,
                        `name` VARCHAR(100) NOT NULL,
                        `email` VARCHAR(150) NOT NULL UNIQUE,
                        `password_hash` VARCHAR(255) NOT NULL,
                        `avatar_initials` VARCHAR(4) DEFAULT 'US',
                        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS `shopping_lists` (
                        `id` INT AUTO_INCREMENT PRIMARY KEY,
                        `user_id` INT NOT NULL,
                        `name` VARCHAR(100) NOT NULL,
                        `icon_name` VARCHAR(50) DEFAULT 'clipboard-text-outline',
                        `icon_color` VARCHAR(25) DEFAULT '#286ED3',
                        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS `cart_items` (
                        `id` INT AUTO_INCREMENT PRIMARY KEY,
                        `user_id` INT NOT NULL,
                        `list_id` INT NULL,
                        `title` VARCHAR(150) NOT NULL,
                        `subtitle` VARCHAR(100) DEFAULT 'Lista general',
                        `price` DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
                        `quantity` INT NOT NULL DEFAULT 1,
                        `is_checked` TINYINT(1) NOT NULL DEFAULT 0,
                        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS `pantry_items` (
                        `id` INT AUTO_INCREMENT PRIMARY KEY,
                        `user_id` INT NOT NULL,
                        `name` VARCHAR(150) NOT NULL,
                        `quantity` DECIMAL(10, 2) NOT NULL DEFAULT 1.00,
                        `unit` VARCHAR(30) DEFAULT 'un.',
                        `min_threshold` DECIMAL(10, 2) NOT NULL DEFAULT 2.00,
                        `category` VARCHAR(50) DEFAULT 'General',
                        `expiration_date` VARCHAR(20) NULL,
                        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS `shopping_list_items` (
                        `id` INT AUTO_INCREMENT PRIMARY KEY,
                        `list_id` INT NOT NULL,
                        `name` VARCHAR(150) NOT NULL,
                        `is_checked` TINYINT(1) NOT NULL DEFAULT 0,
                        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT `fk_shopping_list_items_list`
                            FOREIGN KEY (`list_id`) REFERENCES `shopping_lists` (`id`)
                            ON DELETE CASCADE
                            ON UPDATE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
                # Migración segura de columnas existentes en MySQL
                try:
                    cur.execute("ALTER TABLE `pantry_items` ADD COLUMN `expiration_date` VARCHAR(20) NULL;")
                except Exception:
                    pass
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS `app_sessions` (
                        `id` INT AUTO_INCREMENT PRIMARY KEY,
                        `user_id` INT NULL,
                        `platform` VARCHAR(50) DEFAULT 'Windows',
                        `app_version` VARCHAR(20) DEFAULT '1.0.0',
                        `start_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        `end_time` TIMESTAMP NULL,
                        `duration_seconds` INT DEFAULT 0
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS `app_events` (
                        `id` INT AUTO_INCREMENT PRIMARY KEY,
                        `session_id` INT NULL,
                        `user_id` INT NULL,
                        `event_name` VARCHAR(80) NOT NULL,
                        `screen_name` VARCHAR(50) DEFAULT 'home',
                        `duration_seconds` INT DEFAULT 0,
                        `metadata_json` TEXT NULL,
                        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                # Semilla si no hay usuarios
                cur.execute("SELECT COUNT(*) AS total FROM `users`;")
                row = cur.fetchone()
                if row and row["total"] == 0:
                    self._seed_mysql(cur)

            conn.close()
            self.is_mysql = True
            self.status_message = "Conectado a MySQL"
            print("[DB] Conexión exitosa a MySQL.")

        except Exception as e:
            self.is_mysql = False
            self.status_message = "Modo Local (MySQL no disponible)"
            print(f"[DB] MySQL no accesible ({e}). Iniciando respaldo local SQLite...")
            self._init_sqlite()

    def _seed_mysql(self, cur):
        """Inserta los datos iniciales de Sofía Martínez en MySQL."""
        cur.execute("""
            INSERT INTO `users` (`id`, `name`, `email`, `password_hash`, `avatar_initials`)
            VALUES (1, 'Sofía Martínez', 'sofia@despensapp.com', '3863ba7b7e6ba371d3897dc4fb569e8c6ae524af16f46abab3ab04c3aa32b31c', 'SO');
        """)
        cur.execute("""
            INSERT INTO `shopping_lists` (`id`, `user_id`, `name`, `icon_name`, `icon_color`) VALUES
            (1, 1, 'Compra quincenal', 'clipboard-text-outline', '#286ED3'),
            (2, 1, 'Cena de cumpleaños', 'clipboard-text-outline', '#E05A6D');
        """)
        cur.execute("""
            INSERT INTO `cart_items` (`id`, `user_id`, `list_id`, `title`, `subtitle`, `price`, `quantity`, `is_checked`) VALUES
            (1, 1, 1, 'Leche entera', 'Lista quincenal', 2500.00, 1, 0),
            (2, 1, 1, 'Arroz integral', 'Lista quincenal', 1200.00, 1, 0),
            (3, 1, 1, 'Huevos · docena', 'Lista quincenal', 3000.00, 1, 0),
            (4, 1, 1, 'Pan de molde', 'Lista quincenal', 2100.00, 1, 0);
        """)
        cur.execute("""
            INSERT INTO `pantry_items` (`id`, `user_id`, `name`, `quantity`, `unit`, `min_threshold`, `category`, `expiration_date`) VALUES
            (1, 1, 'Frijoles', 500.00, 'g', 200.00, 'Legumbres', NULL),
            (2, 1, 'Aceite de oliva', 1.00, 'L', 2.00, 'Aceites', NULL),
            (3, 1, 'Huevos', 2.00, 'un.', 6.00, 'Frescos', '2026-10-23'),
            (4, 1, 'Café en grano', 0.00, 'g', 100.00, 'Bebidas', NULL);
        """)
        cur.execute("""
            INSERT INTO `shopping_list_items` (`id`, `list_id`, `name`, `is_checked`) VALUES
            (1, 1, 'Leche entera', 0),
            (2, 1, 'Arroz integral', 0),
            (3, 1, 'Huevos · docena', 1),
            (4, 1, 'Pan de molde', 0),
            (5, 2, 'Vino tinto', 0),
            (6, 2, 'Queso maduro', 0),
            (7, 2, 'Pasta fresca', 1);
        """)

    def _init_sqlite(self):
        """Inicializa la base de datos local SQLite si MySQL está apagado."""
        conn = self.get_sqlite_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                avatar_initials TEXT DEFAULT 'US',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS shopping_lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                icon_name TEXT DEFAULT 'clipboard-text-outline',
                icon_color TEXT DEFAULT '#286ED3',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cart_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                list_id INTEGER,
                title TEXT NOT NULL,
                subtitle TEXT DEFAULT 'Lista general',
                price REAL NOT NULL DEFAULT 0.0,
                quantity INTEGER NOT NULL DEFAULT 1,
                is_checked INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pantry_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                quantity REAL NOT NULL DEFAULT 1.0,
                unit TEXT DEFAULT 'un.',
                min_threshold REAL NOT NULL DEFAULT 2.0,
                category TEXT DEFAULT 'General',
                expiration_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS shopping_list_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                list_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                is_checked INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (list_id) REFERENCES shopping_lists (id) ON DELETE CASCADE
            );
        """)
        # Migración segura en SQLite
        try:
            cur.execute("ALTER TABLE pantry_items ADD COLUMN expiration_date TEXT;")
        except Exception:
            pass
        cur.execute("""
            CREATE TABLE IF NOT EXISTS app_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                platform TEXT DEFAULT 'Windows',
                app_version TEXT DEFAULT '1.0.0',
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                duration_seconds INTEGER DEFAULT 0
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS app_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                user_id INTEGER,
                event_name TEXT NOT NULL,
                screen_name TEXT DEFAULT 'home',
                duration_seconds INTEGER DEFAULT 0,
                metadata_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cur.execute("SELECT COUNT(*) AS total FROM users;")
        if cur.fetchone()["total"] == 0:
            cur.execute("""
                INSERT INTO users (id, name, email, password_hash, avatar_initials)
                VALUES (1, 'Sofía Martínez', 'sofia@despensapp.com', '3863ba7b7e6ba371d3897dc4fb569e8c6ae524af16f46abab3ab04c3aa32b31c', 'SO');
            """)
            cur.execute("""
                INSERT INTO shopping_lists (id, user_id, name, icon_name, icon_color) VALUES
                (1, 1, 'Compra quincenal', 'clipboard-text-outline', '#286ED3'),
                (2, 1, 'Cena de cumpleaños', 'clipboard-text-outline', '#E05A6D');
            """)
            cur.execute("""
                INSERT INTO cart_items (id, user_id, list_id, title, subtitle, price, quantity, is_checked) VALUES
                (1, 1, 1, 'Leche entera', 'Lista quincenal', 2500.0, 1, 0),
                (2, 1, 1, 'Arroz integral', 'Lista quincenal', 1200.0, 1, 0),
                (3, 1, 1, 'Huevos · docena', 'Lista quincenal', 3000.0, 1, 0),
                (4, 1, 1, 'Pan de molde', 'Lista quincenal', 2100.0, 1, 0);
            """)
            cur.execute("""
                INSERT INTO pantry_items (id, user_id, name, quantity, unit, min_threshold, category, expiration_date) VALUES
                (1, 1, 'Frijoles', 500.0, 'g', 200.0, 'Legumbres', NULL),
                (2, 1, 'Aceite de oliva', 1.0, 'L', 2.0, 'Aceites', NULL),
                (3, 1, 'Huevos', 2.0, 'un.', 6.0, 'Frescos', '2026-10-23'),
                (4, 1, 'Café en grano', 0.0, 'g', 100.0, 'Bebidas', NULL);
            """)
            cur.execute("""
                INSERT INTO shopping_list_items (id, list_id, name, is_checked) VALUES
                (1, 1, 'Leche entera', 0),
                (2, 1, 'Arroz integral', 0),
                (3, 1, 'Huevos · docena', 1),
                (4, 1, 'Pan de molde', 0),
                (5, 2, 'Vino tinto', 0),
                (6, 2, 'Queso maduro', 0),
                (7, 2, 'Pasta fresca', 1);
            """)
        conn.commit()
        conn.close()

    # ----------------------------------------------------
    # Usuarios y Autenticación
    # ----------------------------------------------------
    def register_user(self, name: str, email: str, password_hash: str) -> Tuple[bool, str, Optional[User]]:
        """Registra un nuevo usuario en la base de datos."""
        name = name.strip()
        email = email.strip().lower()
        initials = User.generate_initials(name)

        if not name or not email or not password_hash:
            return False, "Todos los campos son obligatorios", None

        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM users WHERE email = %s;", (email,))
                    if cur.fetchone():
                        conn.close()
                        return False, "Ya existe una cuenta con este correo", None
                    cur.execute("""
                        INSERT INTO users (name, email, password_hash, avatar_initials)
                        VALUES (%s, %s, %s, %s);
                    """, (name, email, password_hash, initials))
                    new_id = cur.lastrowid
                conn.close()
                return True, "Cuenta creada con éxito", User(new_id, name, email, initials, password_hash)
            except Exception as e:
                return False, f"Error en MySQL: {e}", None
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute("SELECT id FROM users WHERE email = ?;", (email,))
                if cur.fetchone():
                    conn.close()
                    return False, "Ya existe una cuenta con este correo", None
                cur.execute("""
                    INSERT INTO users (name, email, password_hash, avatar_initials)
                    VALUES (?, ?, ?, ?);
                """, (name, email, password_hash, initials))
                new_id = cur.lastrowid
                conn.commit()
                conn.close()
                return True, "Cuenta creada en modo local", User(new_id, name, email, initials, password_hash)
            except Exception as e:
                return False, f"Error en BD local: {e}", None

    def authenticate_user(self, email: str, password_hash: str) -> Tuple[bool, str, Optional[User]]:
        """Valida credenciales e inicia sesión."""
        email = email.strip().lower()
        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM users WHERE email = %s;", (email,))
                    row = cur.fetchone()
                conn.close()
                if not row:
                    return False, "Usuario no encontrado", None
                if row["password_hash"] != password_hash:
                    return False, "Contraseña incorrecta", None
                user = User(
                    id=row["id"],
                    name=row["name"],
                    email=row["email"],
                    avatar_initials=row.get("avatar_initials", "US"),
                    password_hash=row["password_hash"]
                )
                return True, "Inicio de sesión correcto", user
            except Exception as e:
                return False, f"Error en MySQL: {e}", None
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute("SELECT * FROM users WHERE email = ?;", (email,))
                row = cur.fetchone()
                conn.close()
                if not row:
                    return False, "Usuario no encontrado", None
                if row["password_hash"] != password_hash:
                    return False, "Contraseña incorrecta", None
                user = User(
                    id=row["id"],
                    name=row["name"],
                    email=row["email"],
                    avatar_initials=row["avatar_initials"] or "US",
                    password_hash=row["password_hash"]
                )
                return True, "Inicio de sesión correcto", user
            except Exception as e:
                return False, f"Error en BD local: {e}", None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Obtiene un usuario por su ID."""
        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM users WHERE id = %s;", (user_id,))
                    row = cur.fetchone()
                conn.close()
                if row:
                    return User(row["id"], row["name"], row["email"], row.get("avatar_initials", "US"), row["password_hash"])
            except Exception:
                pass
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute("SELECT * FROM users WHERE id = ?;", (user_id,))
                row = cur.fetchone()
                conn.close()
                if row:
                    return User(row["id"], row["name"], row["email"], row["avatar_initials"] or "US", row["password_hash"])
            except Exception:
                pass
        return None

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Obtiene un usuario por su correo electrónico."""
        if not email:
            return None
        email = email.strip().lower()
        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM users WHERE LOWER(email) = %s;", (email,))
                    row = cur.fetchone()
                conn.close()
                if row:
                    return User(row["id"], row["name"], row["email"], row.get("avatar_initials", "US"), row["password_hash"])
            except Exception:
                pass
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute("SELECT * FROM users WHERE LOWER(email) = ?;", (email,))
                row = cur.fetchone()
                conn.close()
                if row:
                    return User(row["id"], row["name"], row["email"], row["avatar_initials"] or "US", row["password_hash"])
            except Exception:
                pass
        return None

    # ----------------------------------------------------
    # Carrito de Compras
    # ----------------------------------------------------
    def get_cart_items(self, user_id: int) -> List[CartItem]:
        """Obtiene todos los artículos del carrito para el usuario."""
        items = []
        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, user_id, title, subtitle, price, quantity, is_checked, list_id
                        FROM cart_items
                        WHERE user_id = %s
                        ORDER BY id DESC;
                    """, (user_id,))
                    rows = cur.fetchall()
                conn.close()
                for r in rows:
                    items.append(CartItem(
                        id=r["id"],
                        user_id=r["user_id"],
                        title=r["title"],
                        subtitle=r["subtitle"] or "General",
                        price=float(r["price"]),
                        quantity=r["quantity"],
                        is_checked=bool(r["is_checked"]),
                        list_id=r["list_id"]
                    ))
            except Exception as e:
                print(f"[DB] Error get_cart_items MySQL: {e}")
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, user_id, title, subtitle, price, quantity, is_checked, list_id
                    FROM cart_items
                    WHERE user_id = ?
                    ORDER BY id DESC;
                """, (user_id,))
                rows = cur.fetchall()
                conn.close()
                for r in rows:
                    items.append(CartItem(
                        id=r["id"],
                        user_id=r["user_id"],
                        title=r["title"],
                        subtitle=r["subtitle"] or "General",
                        price=float(r["price"]),
                        quantity=r["quantity"],
                        is_checked=bool(r["is_checked"]),
                        list_id=r["list_id"]
                    ))
            except Exception as e:
                print(f"[DB] Error get_cart_items SQLite: {e}")
        return items

    def add_cart_item(self, user_id: int, title: str, subtitle: str, price: float, quantity: int = 1, list_id: Optional[int] = None) -> Optional[int]:
        """Añade un nuevo producto al carrito."""
        title = title.strip()
        subtitle = subtitle.strip() or "General"
        price = max(0.0, float(price))
        quantity = max(1, int(quantity))

        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO cart_items (user_id, list_id, title, subtitle, price, quantity, is_checked)
                        VALUES (%s, %s, %s, %s, %s, %s, 0);
                    """, (user_id, list_id, title, subtitle, price, quantity))
                    new_id = cur.lastrowid
                conn.close()
                return new_id
            except Exception as e:
                print(f"[DB] Error add_cart_item MySQL: {e}")
                return None
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO cart_items (user_id, list_id, title, subtitle, price, quantity, is_checked)
                    VALUES (?, ?, ?, ?, ?, ?, 0);
                """, (user_id, list_id, title, subtitle, price, quantity))
                new_id = cur.lastrowid
                conn.commit()
                conn.close()
                return new_id
            except Exception as e:
                print(f"[DB] Error add_cart_item SQLite: {e}")
                return None

    def toggle_cart_item(self, item_id: int, is_checked: bool) -> bool:
        """Marca o desmarca un artículo del carrito."""
        val = 1 if is_checked else 0
        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute("UPDATE cart_items SET is_checked = %s WHERE id = %s;", (val, item_id))
                conn.close()
                return True
            except Exception as e:
                print(f"[DB] Error toggle_cart_item MySQL: {e}")
                return False
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute("UPDATE cart_items SET is_checked = ? WHERE id = ?;", (val, item_id))
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                print(f"[DB] Error toggle_cart_item SQLite: {e}")
                return False

    def delete_cart_item(self, item_id: int) -> bool:
        """Elimina un artículo del carrito."""
        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM cart_items WHERE id = %s;", (item_id,))
                conn.close()
                return True
            except Exception as e:
                print(f"[DB] Error delete_cart_item MySQL: {e}")
                return False
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute("DELETE FROM cart_items WHERE id = ?;", (item_id,))
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                print(f"[DB] Error delete_cart_item SQLite: {e}")
                return False

    # ----------------------------------------------------
    # Despensa
    # ----------------------------------------------------
    def get_pantry_items(self, user_id: int) -> List[PantryItem]:
        """Obtiene todos los artículos de la despensa de un usuario, incluyendo fecha de caducidad."""
        items = []
        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, user_id, name, quantity, unit, min_threshold, category, expiration_date
                        FROM pantry_items
                        WHERE user_id = %s
                        ORDER BY id DESC;
                    """, (user_id,))
                    rows = cur.fetchall()
                conn.close()
                for r in rows:
                    items.append(PantryItem(
                        id=r["id"],
                        user_id=r["user_id"],
                        name=r["name"],
                        quantity=float(r["quantity"]),
                        unit=r["unit"] or "un.",
                        min_threshold=float(r["min_threshold"]),
                        category=r["category"] or "General",
                        expiration_date=r.get("expiration_date")
                    ))
            except Exception as e:
                print(f"[DB] Error get_pantry_items MySQL: {e}")
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, user_id, name, quantity, unit, min_threshold, category, expiration_date
                    FROM pantry_items
                    WHERE user_id = ?
                    ORDER BY id DESC;
                """, (user_id,))
                rows = cur.fetchall()
                conn.close()
                for r in rows:
                    items.append(PantryItem(
                        id=r["id"],
                        user_id=r["user_id"],
                        name=r["name"],
                        quantity=float(r["quantity"]),
                        unit=r["unit"] or "un.",
                        min_threshold=float(r["min_threshold"]),
                        category=r["category"] or "General",
                        expiration_date=r["expiration_date"] if "expiration_date" in r.keys() else None
                    ))
            except Exception as e:
                print(f"[DB] Error get_pantry_items SQLite: {e}")
        return items

    def add_pantry_item(self, user_id: int, name: str, quantity: float, unit: str, min_threshold: float, category: str = "General", expiration_date: Optional[str] = None) -> Optional[int]:
        """Añade un producto a la despensa con cantidades numéricas, umbral y fecha de vencimiento opcional."""
        name = name.strip()
        unit = unit.strip() or "un."
        category = category.strip() or "General"
        quantity = float(quantity)
        min_threshold = float(min_threshold)
        clean_exp = expiration_date.strip() if expiration_date and expiration_date.strip().lower() not in ("none", "null", "no vence", "") else None

        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO pantry_items (user_id, name, quantity, unit, min_threshold, category, expiration_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """, (user_id, name, quantity, unit, min_threshold, category, clean_exp))
                    new_id = cur.lastrowid
                conn.close()
                return new_id
            except Exception as e:
                print(f"[DB] Error add_pantry_item MySQL: {e}")
                return None
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO pantry_items (user_id, name, quantity, unit, min_threshold, category, expiration_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                """, (user_id, name, quantity, unit, min_threshold, category, clean_exp))
                new_id = cur.lastrowid
                conn.commit()
                conn.close()
                return new_id
            except Exception as e:
                print(f"[DB] Error add_pantry_item SQLite: {e}")
                return None

    def update_pantry_quantity(self, item_id: int, delta: float) -> bool:
        """Aumenta o disminuye la cantidad numérica de un producto en la despensa."""
        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute("SELECT quantity FROM pantry_items WHERE id = %s;", (item_id,))
                    row = cur.fetchone()
                    if row:
                        new_q = max(0.0, float(row["quantity"]) + delta)
                        cur.execute("UPDATE pantry_items SET quantity = %s WHERE id = %s;", (new_q, item_id))
                conn.close()
                return True
            except Exception as e:
                print(f"[DB] Error update_pantry_quantity MySQL: {e}")
                return False
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute("SELECT quantity FROM pantry_items WHERE id = ?;", (item_id,))
                row = cur.fetchone()
                if row:
                    new_q = max(0.0, float(row["quantity"]) + delta)
                    cur.execute("UPDATE pantry_items SET quantity = ? WHERE id = ?;", (new_q, item_id))
                    conn.commit()
                conn.close()
                return True
            except Exception as e:
                print(f"[DB] Error update_pantry_quantity SQLite: {e}")
                return False

    def update_pantry_item_details(self, item_id: int, name: str, quantity: float, unit: str, min_threshold: float, expiration_date: Optional[str] = None) -> bool:
        """Actualiza los datos completos de un producto de despensa, incluyendo fecha de caducidad."""
        name = name.strip()
        unit = unit.strip() or "un."
        quantity = max(0.0, float(quantity))
        min_threshold = max(0.0, float(min_threshold))
        clean_exp = expiration_date.strip() if expiration_date and expiration_date.strip().lower() not in ("none", "null", "no vence", "") else None

        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE pantry_items
                        SET name = %s, quantity = %s, unit = %s, min_threshold = %s, expiration_date = %s
                        WHERE id = %s;
                    """, (name, quantity, unit, min_threshold, clean_exp, item_id))
                conn.close()
                return True
            except Exception as e:
                print(f"[DB] Error update_pantry_item_details MySQL: {e}")
                return False
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute("""
                    UPDATE pantry_items
                    SET name = ?, quantity = ?, unit = ?, min_threshold = ?, expiration_date = ?
                    WHERE id = ?;
                """, (name, quantity, unit, min_threshold, clean_exp, item_id))
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                print(f"[DB] Error update_pantry_item_details SQLite: {e}")
                return False

    def update_pantry_expiration(self, item_id: int, expiration_date: Optional[str] = None) -> bool:
        """Actualiza únicamente la fecha de caducidad de un producto en la despensa."""
        clean_exp = expiration_date.strip() if expiration_date and expiration_date.strip().lower() not in ("none", "null", "no vence", "sin vencimiento", "") else None
        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute("UPDATE pantry_items SET expiration_date = %s WHERE id = %s;", (clean_exp, item_id))
                conn.close()
                return True
            except Exception as e:
                print(f"[DB] Error update_pantry_expiration MySQL: {e}")
                return False
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute("UPDATE pantry_items SET expiration_date = ? WHERE id = ?;", (clean_exp, item_id))
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                print(f"[DB] Error update_pantry_expiration SQLite: {e}")
                return False

    def get_pantry_item_by_id(self, item_id: int) -> Optional[PantryItem]:
        """Obtiene un producto de despensa específico por su identificador único."""
        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, user_id, name, quantity, unit, min_threshold, category, expiration_date
                        FROM pantry_items
                        WHERE id = %s LIMIT 1;
                    """, (item_id,))
                    r = cur.fetchone()
                conn.close()
                if r:
                    return PantryItem(
                        id=r["id"],
                        user_id=r["user_id"],
                        name=r["name"],
                        quantity=float(r["quantity"]),
                        unit=r["unit"] or "un.",
                        min_threshold=float(r["min_threshold"]),
                        category=r["category"] or "General",
                        expiration_date=r.get("expiration_date")
                    )
            except Exception as e:
                print(f"[DB] Error get_pantry_item_by_id MySQL: {e}")
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, user_id, name, quantity, unit, min_threshold, category, expiration_date
                    FROM pantry_items
                    WHERE id = ? LIMIT 1;
                """, (item_id,))
                r = cur.fetchone()
                conn.close()
                if r:
                    return PantryItem(
                        id=r["id"],
                        user_id=r["user_id"],
                        name=r["name"],
                        quantity=float(r["quantity"]),
                        unit=r["unit"] or "un.",
                        min_threshold=float(r["min_threshold"]),
                        category=r["category"] or "General",
                        expiration_date=r["expiration_date"] if "expiration_date" in r.keys() else None
                    )
            except Exception as e:
                print(f"[DB] Error get_pantry_item_by_id SQLite: {e}")
        return None

    def delete_pantry_item(self, item_id: int) -> bool:
        """Elimina un producto de la despensa."""
        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM pantry_items WHERE id = %s;", (item_id,))
                conn.close()
                return True
            except Exception as e:
                print(f"[DB] Error delete_pantry_item MySQL: {e}")
                return False
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute("DELETE FROM pantry_items WHERE id = ?;", (item_id,))
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                print(f"[DB] Error delete_pantry_item SQLite: {e}")
                return False

    # ----------------------------------------------------
    # Listas de Compras
    # ----------------------------------------------------
    def get_shopping_lists(self, user_id: int) -> List[ShoppingList]:
        """Obtiene todas las listas de compras y la cantidad real de productos anotados y pendientes."""
        lists = []
        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT l.id, l.user_id, l.name, l.icon_name, l.icon_color,
                               COUNT(s.id) AS items_count,
                               SUM(CASE WHEN s.is_checked = 0 THEN 1 ELSE 0 END) AS pending_count
                        FROM shopping_lists l
                        LEFT JOIN shopping_list_items s ON s.list_id = l.id
                        WHERE l.user_id = %s
                        GROUP BY l.id
                        ORDER BY l.id DESC;
                    """, (user_id,))
                    rows = cur.fetchall()
                conn.close()
                for r in rows:
                    lists.append(ShoppingList(
                        id=r["id"],
                        user_id=r["user_id"],
                        name=r["name"],
                        icon_name=r["icon_name"] or "clipboard-text-outline",
                        icon_color=r["icon_color"] or "#286ED3",
                        items_count=int(r["items_count"] or 0),
                        pending_count=int(r["pending_count"] or 0)
                    ))
            except Exception as e:
                print(f"[DB] Error get_shopping_lists MySQL: {e}")
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute("""
                    SELECT l.id, l.user_id, l.name, l.icon_name, l.icon_color,
                           COUNT(s.id) AS items_count,
                           SUM(CASE WHEN s.is_checked = 0 THEN 1 ELSE 0 END) AS pending_count
                    FROM shopping_lists l
                    LEFT JOIN shopping_list_items s ON s.list_id = l.id
                    WHERE l.user_id = ?
                    GROUP BY l.id
                    ORDER BY l.id DESC;
                """, (user_id,))
                rows = cur.fetchall()
                conn.close()
                for r in rows:
                    lists.append(ShoppingList(
                        id=r["id"],
                        user_id=r["user_id"],
                        name=r["name"],
                        icon_name=r["icon_name"] or "clipboard-text-outline",
                        icon_color=r["icon_color"] or "#286ED3",
                        items_count=int(r["items_count"] or 0),
                        pending_count=int(r["pending_count"] or 0)
                    ))
            except Exception as e:
                print(f"[DB] Error get_shopping_lists SQLite: {e}")
        return lists

    def add_shopping_list(self, user_id: int, name: str, icon_color: str = "#286ED3", icon_name: str = "clipboard-text-outline") -> Optional[int]:
        """Crea una nueva lista de compras con color e icono personalizados."""
        name = name.strip()
        icon_color = icon_color.strip() or "#286ED3"
        icon_name = icon_name.strip() or "clipboard-text-outline"

        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO shopping_lists (user_id, name, icon_name, icon_color)
                        VALUES (%s, %s, %s, %s);
                    """, (user_id, name, icon_name, icon_color))
                    new_id = cur.lastrowid
                conn.close()
                return new_id
            except Exception as e:
                print(f"[DB] Error add_shopping_list MySQL: {e}")
                return None
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO shopping_lists (user_id, name, icon_name, icon_color)
                    VALUES (?, ?, ?, ?);
                """, (user_id, name, icon_name, icon_color))
                new_id = cur.lastrowid
                conn.commit()
                conn.close()
                return new_id
            except Exception as e:
                print(f"[DB] Error add_shopping_list SQLite: {e}")
                return None

    def update_shopping_list_name(self, list_id: int, new_name: str, new_color: Optional[str] = None) -> bool:
        """Permite renombrar o cambiar color a una lista de compras existente."""
        new_name = new_name.strip()
        if not new_name:
            return False

        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    if new_color:
                        cur.execute("UPDATE shopping_lists SET name = %s, icon_color = %s WHERE id = %s;", (new_name, new_color, list_id))
                    else:
                        cur.execute("UPDATE shopping_lists SET name = %s WHERE id = %s;", (new_name, list_id))
                conn.close()
                return True
            except Exception as e:
                print(f"[DB] Error update_shopping_list_name MySQL: {e}")
                return False
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                if new_color:
                    cur.execute("UPDATE shopping_lists SET name = ?, icon_color = ? WHERE id = ?;", (new_name, new_color, list_id))
                else:
                    cur.execute("UPDATE shopping_lists SET name = ? WHERE id = ?;", (new_name, list_id))
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                print(f"[DB] Error update_shopping_list_name SQLite: {e}")
                return False

    def delete_shopping_list(self, list_id: int) -> bool:
        """Elimina una lista de compras y sus productos asociados."""
        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM shopping_lists WHERE id = %s;", (list_id,))
                conn.close()
                return True
            except Exception as e:
                print(f"[DB] Error delete_shopping_list MySQL: {e}")
                return False
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute("DELETE FROM shopping_lists WHERE id = ?;", (list_id,))
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                print(f"[DB] Error delete_shopping_list SQLite: {e}")
                return False

    # ----------------------------------------------------
    # Artículos de Listas de Compras (Estilo Supermercado)
    # ----------------------------------------------------
    def get_shopping_list_items(self, list_id: int) -> List[ShoppingListItem]:
        """Obtiene los productos anotados en una lista de compras de supermercado."""
        items = []
        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, list_id, name, is_checked, created_at
                        FROM shopping_list_items
                        WHERE list_id = %s
                        ORDER BY is_checked ASC, id ASC;
                    """, (list_id,))
                    rows = cur.fetchall()
                conn.close()
                for r in rows:
                    items.append(ShoppingListItem(
                        id=r["id"],
                        list_id=r["list_id"],
                        name=r["name"],
                        is_checked=bool(r["is_checked"]),
                        created_at=str(r.get("created_at") or "")
                    ))
            except Exception as e:
                print(f"[DB] Error get_shopping_list_items MySQL: {e}")
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, list_id, name, is_checked, created_at
                    FROM shopping_list_items
                    WHERE list_id = ?
                    ORDER BY is_checked ASC, id ASC;
                """, (list_id,))
                rows = cur.fetchall()
                conn.close()
                for r in rows:
                    items.append(ShoppingListItem(
                        id=r["id"],
                        list_id=r["list_id"],
                        name=r["name"],
                        is_checked=bool(r["is_checked"]),
                        created_at=str(r["created_at"] or "")
                    ))
            except Exception as e:
                print(f"[DB] Error get_shopping_list_items SQLite: {e}")
        return items

    def add_shopping_list_item(self, list_id: int, name: str) -> Optional[int]:
        """Añade un producto a la lista de compras del supermercado (sin precio)."""
        name = name.strip()
        if not name:
            return None

        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO shopping_list_items (list_id, name, is_checked)
                        VALUES (%s, %s, 0);
                    """, (list_id, name))
                    new_id = cur.lastrowid
                conn.close()
                return new_id
            except Exception as e:
                print(f"[DB] Error add_shopping_list_item MySQL: {e}")
                return None
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO shopping_list_items (list_id, name, is_checked)
                    VALUES (?, ?, 0);
                """, (list_id, name))
                new_id = cur.lastrowid
                conn.commit()
                conn.close()
                return new_id
            except Exception as e:
                print(f"[DB] Error add_shopping_list_item SQLite: {e}")
                return None

    def toggle_shopping_list_item(self, item_id: int, is_checked: bool) -> bool:
        """Marca o tacha un producto de la lista al ir comprándolo."""
        val = 1 if is_checked else 0
        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute("UPDATE shopping_list_items SET is_checked = %s WHERE id = %s;", (val, item_id))
                conn.close()
                return True
            except Exception as e:
                print(f"[DB] Error toggle_shopping_list_item MySQL: {e}")
                return False
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute("UPDATE shopping_list_items SET is_checked = ? WHERE id = ?;", (val, item_id))
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                print(f"[DB] Error toggle_shopping_list_item SQLite: {e}")
                return False

    def update_shopping_list_item_name(self, item_id: int, new_name: str) -> bool:
        """Permite editar el nombre de un producto de la lista si el usuario se equivocó."""
        new_name = new_name.strip()
        if not new_name:
            return False

        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute("UPDATE shopping_list_items SET name = %s WHERE id = %s;", (new_name, item_id))
                conn.close()
                return True
            except Exception as e:
                print(f"[DB] Error update_shopping_list_item_name MySQL: {e}")
                return False
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute("UPDATE shopping_list_items SET name = ? WHERE id = ?;", (new_name, item_id))
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                print(f"[DB] Error update_shopping_list_item_name SQLite: {e}")
                return False

    def delete_shopping_list_item(self, item_id: int) -> bool:
        """Elimina un producto individual de la lista de compras."""
        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM shopping_list_items WHERE id = %s;", (item_id,))
                conn.close()
                return True
            except Exception as e:
                print(f"[DB] Error delete_shopping_list_item MySQL: {e}")
                return False
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute("DELETE FROM shopping_list_items WHERE id = ?;", (item_id,))
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                print(f"[DB] Error delete_shopping_list_item SQLite: {e}")
                return False

    # ----------------------------------------------------
    # Estadísticas y Métricas Dinámicas del Usuario
    # ----------------------------------------------------
    def get_user_statistics(self, user_id: int) -> dict:
        """
        Calcula las estadísticas completas de compras, despensa, listas y vencimientos
        para el usuario especificado, tanto en MySQL como en SQLite.
        """
        cart_items = self.get_cart_items(user_id)
        pantry_items = self.get_pantry_items(user_id)
        shopping_lists = self.get_shopping_lists(user_id)

        # 1. Gasto total del carrito (productos pendientes o en lista)
        cart_total = sum(it.price for it in cart_items if not it.is_checked)
        if cart_total == 0 and cart_items:
            cart_total = sum(it.price for it in cart_items)

        # 2. Desglose de estados de despensa y vencimientos
        reponer = [p for p in pantry_items if p.status == "Reponer"]
        por_agotar = [p for p in pantry_items if p.status == "Por agotarse"]
        suficiente = [p for p in pantry_items if p.status == "Suficiente"]

        # 2b. Análisis de Vencimiento de Alimentos
        vencidos = [p for p in pantry_items if p.is_expired]
        por_vencer = [p for p in pantry_items if p.is_expiring_soon]
        vencidos.sort(key=lambda x: (x.days_until_expiration if x.days_until_expiration is not None else -9999))
        por_vencer.sort(key=lambda x: (x.days_until_expiration if x.days_until_expiration is not None else 9999))
        first_vencido = vencidos[0] if vencidos else None
        first_por_vencer = por_vencer[0] if por_vencer else None

        # 3. Lo más comprado / productos más frecuentes
        product_freq = {}
        for it in cart_items:
            name = it.title.strip()
            product_freq[name] = product_freq.get(name, 0) + max(1, it.quantity)
        for it in pantry_items:
            name = it.name.strip()
            product_freq[name] = product_freq.get(name, 0) + 1

        sorted_freq = sorted(product_freq.items(), key=lambda x: x[1], reverse=True)
        top_products = []
        if sorted_freq:
            max_cnt = sorted_freq[0][1]
            for name, cnt in sorted_freq[:3]:
                pct = min(1.0, max(0.2, cnt / max_cnt)) if max_cnt > 0 else 0.5
                lbl = f"{int(cnt)} veces" if cnt > 1 else "1 vez"
                top_products.append({
                    "name": name,
                    "count_lbl": lbl,
                    "percent": pct
                })

        # 4. Receta sugerida inteligente
        pantry_names = [p.name for p in pantry_items if p.quantity > 0]
        suggested_recipe = self._generate_suggested_recipe(pantry_names)

        return {
            "cart_total": cart_total,
            "cart_items_count": len(cart_items),
            "pantry_items_count": len(pantry_items),
            "shopping_lists_count": len(shopping_lists),
            "reponer_count": len(reponer),
            "por_agotar_count": len(por_agotar),
            "suficiente_count": len(suficiente),
            "vencidos_count": len(vencidos),
            "por_vencer_count": len(por_vencer),
            "first_reponer": reponer[0] if reponer else None,
            "first_por_agotar": por_agotar[0] if por_agotar else None,
            "first_vencido": first_vencido,
            "first_por_vencer": first_por_vencer,
            "top_products": top_products,
            "suggested_recipe": suggested_recipe,
        }

    def _generate_suggested_recipe(self, pantry_names: List[str]) -> str:
        """Genera una receta contextual basada únicamente en los ingredientes del usuario."""
        if not pantry_names:
            return "Añade alimentos para sugerir recetas"

        names_lower = [n.lower() for n in pantry_names]
        text_all = " ".join(names_lower)

        if "arroz" in text_all and "huevo" in text_all:
            return "Arroz salteado con huevo y verduras"
        elif "frijol" in text_all or "lenteja" in text_all or "garbanzo" in text_all:
            return "Guiso casero de legumbres"
        elif "pasta" in text_all or "fideo" in text_all or "espagueti" in text_all:
            return "Pasta casera al dente"
        elif "harina" in text_all:
            return "Panqueques o pan artesanal"
        elif "leche" in text_all and "avena" in text_all:
            return "Bowl de avena con leche tibia"
        elif "manzana" in text_all or "platano" in text_all or "banana" in text_all:
            return "Ensalada fresca de frutas"
        elif "aceite" in text_all and len(pantry_names) >= 2:
            primer_ing = [n for n in pantry_names if "aceite" not in n.lower()][0]
            return f"Salteado con {primer_ing}"
        else:
            return f"Plato casero con {pantry_names[0]}"

    # ----------------------------------------------------
    # Métodos de Telemetría y Analítica de Producto
    # ----------------------------------------------------
    def create_session(self, user_id: Optional[int] = None, platform: str = "Windows", app_version: str = "1.0.0") -> int:
        """Registra el inicio de una nueva sesión de la aplicación."""
        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO app_sessions (user_id, platform, app_version, start_time)
                        VALUES (%s, %s, %s, NOW());
                    """, (user_id, platform, app_version))
                    new_id = cur.lastrowid
                conn.close()
                return new_id
            except Exception as e:
                print(f"[DB] Error create_session MySQL: {e}")
                return 0
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO app_sessions (user_id, platform, app_version)
                    VALUES (?, ?, ?);
                """, (user_id, platform, app_version))
                new_id = cur.lastrowid
                conn.commit()
                conn.close()
                return new_id
            except Exception as e:
                print(f"[DB] Error create_session SQLite: {e}")
                return 0

    def close_session(self, session_id: int, duration_seconds: int = 0) -> bool:
        """Cierra una sesión guardando la duración exacta en segundos."""
        if not session_id:
            return False
        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE app_sessions
                        SET end_time = NOW(), duration_seconds = %s
                        WHERE id = %s;
                    """, (max(1, duration_seconds), session_id))
                conn.close()
                return True
            except Exception as e:
                print(f"[DB] Error close_session MySQL: {e}")
                return False
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute("""
                    UPDATE app_sessions
                    SET end_time = CURRENT_TIMESTAMP, duration_seconds = ?
                    WHERE id = ?;
                """, (max(1, duration_seconds), session_id))
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                print(f"[DB] Error close_session SQLite: {e}")
                return False

    def log_event(self, session_id: Optional[int], user_id: Optional[int], event_name: str,
                  screen_name: str = "home", duration_seconds: int = 0, metadata: Optional[dict] = None) -> int:
        """Registra una acción, cambio de pantalla o interacción clave."""
        meta_str = json.dumps(metadata or {}, ensure_ascii=False)
        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO app_events (session_id, user_id, event_name, screen_name, duration_seconds, metadata_json)
                        VALUES (%s, %s, %s, %s, %s, %s);
                    """, (session_id, user_id, event_name, screen_name, duration_seconds, meta_str))
                    new_id = cur.lastrowid
                conn.close()
                return new_id
            except Exception as e:
                print(f"[DB] Error log_event MySQL: {e}")
                return 0
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO app_events (session_id, user_id, event_name, screen_name, duration_seconds, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?);
                """, (session_id, user_id, event_name, screen_name, duration_seconds, meta_str))
                new_id = cur.lastrowid
                conn.commit()
                conn.close()
                return new_id
            except Exception as e:
                print(f"[DB] Error log_event SQLite: {e}")
                return 0

    def get_telemetry_kpis(self) -> dict:
        """Obtiene las métricas consolidadas de telemetría para el Dashboard Web."""
        default_kpis = {
            "total_users": 0,
            "total_sessions": 0,
            "avg_session_seconds": 0,
            "avg_session_str": "0m 0s",
            "total_events": 0,
            "most_active_screen": "Inicio",
        }
        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) AS total FROM users;")
                    default_kpis["total_users"] = cur.fetchone()["total"]

                    cur.execute("SELECT COUNT(*) AS total, IFNULL(AVG(duration_seconds), 0) AS avg_sec FROM app_sessions;")
                    s_row = cur.fetchone()
                    default_kpis["total_sessions"] = s_row["total"]
                    avg_s = int(s_row["avg_sec"])
                    default_kpis["avg_session_seconds"] = avg_s
                    default_kpis["avg_session_str"] = f"{avg_s // 60}m {avg_s % 60}s"

                    cur.execute("SELECT COUNT(*) AS total FROM app_events;")
                    default_kpis["total_events"] = cur.fetchone()["total"]

                    cur.execute("""
                        SELECT screen_name, COUNT(*) AS count
                        FROM app_events
                        WHERE screen_name IS NOT NULL AND screen_name != ''
                        GROUP BY screen_name
                        ORDER BY count DESC
                        LIMIT 1;
                    """)
                    scr_row = cur.fetchone()
                    if scr_row:
                        default_kpis["most_active_screen"] = scr_row["screen_name"].capitalize()
                conn.close()
            except Exception as e:
                print(f"[DB] Error get_telemetry_kpis MySQL: {e}")
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) AS total FROM users;")
                default_kpis["total_users"] = cur.fetchone()["total"]

                cur.execute("SELECT COUNT(*) AS total, IFNULL(AVG(duration_seconds), 0) AS avg_sec FROM app_sessions;")
                s_row = cur.fetchone()
                default_kpis["total_sessions"] = s_row["total"]
                avg_s = int(s_row["avg_sec"])
                default_kpis["avg_session_seconds"] = avg_s
                default_kpis["avg_session_str"] = f"{avg_s // 60}m {avg_s % 60}s"

                cur.execute("SELECT COUNT(*) AS total FROM app_events;")
                default_kpis["total_events"] = cur.fetchone()["total"]

                cur.execute("""
                    SELECT screen_name, COUNT(*) AS count
                    FROM app_events
                    WHERE screen_name IS NOT NULL AND screen_name != ''
                    GROUP BY screen_name
                    ORDER BY count DESC
                    LIMIT 1;
                """)
                scr_row = cur.fetchone()
                if scr_row:
                    default_kpis["most_active_screen"] = scr_row["screen_name"].capitalize()
                conn.close()
            except Exception as e:
                print(f"[DB] Error get_telemetry_kpis SQLite: {e}")
        return default_kpis

    def get_telemetry_screen_times(self) -> List[dict]:
        """Obtiene el tiempo total dedicado a cada pantalla."""
        res = []
        sql = """
            SELECT screen_name,
                   COUNT(*) AS views_count,
                   SUM(duration_seconds) AS total_seconds
            FROM app_events
            WHERE screen_name IS NOT NULL AND screen_name != ''
            GROUP BY screen_name
            ORDER BY total_seconds DESC;
        """
        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute(sql)
                    rows = cur.fetchall()
                conn.close()
                for r in rows:
                    sec = int(r["total_seconds"] or 0)
                    res.append({
                        "screen": r["screen_name"],
                        "views": int(r["views_count"] or 0),
                        "total_seconds": sec,
                        "minutes": round(sec / 60.0, 1)
                    })
            except Exception as e:
                print(f"[DB] Error get_telemetry_screen_times MySQL: {e}")
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute(sql)
                rows = cur.fetchall()
                conn.close()
                for r in rows:
                    sec = int(r["total_seconds"] or 0)
                    res.append({
                        "screen": r["screen_name"],
                        "views": int(r["views_count"] or 0),
                        "total_seconds": sec,
                        "minutes": round(sec / 60.0, 1)
                    })
            except Exception as e:
                print(f"[DB] Error get_telemetry_screen_times SQLite: {e}")
        return res

    def get_telemetry_recent_events(self, limit: int = 25) -> List[dict]:
        """Obtiene los últimos eventos registrados con información de usuario."""
        events = []
        sql = f"""
            SELECT e.id, e.session_id, e.event_name, e.screen_name, e.duration_seconds,
                   e.metadata_json, e.created_at, IFNULL(u.name, 'Anónimo') AS user_name
            FROM app_events e
            LEFT JOIN users u ON u.id = e.user_id
            ORDER BY e.id DESC
            LIMIT {int(limit)};
        """
        if self.is_mysql:
            try:
                conn = self.get_mysql_connection()
                with conn.cursor() as cur:
                    cur.execute(sql)
                    rows = cur.fetchall()
                conn.close()
                for r in rows:
                    created_str = r["created_at"].strftime("%H:%M:%S") if hasattr(r["created_at"], "strftime") else str(r["created_at"])
                    events.append({
                        "id": r["id"],
                        "event_name": r["event_name"],
                        "screen_name": r["screen_name"] or "home",
                        "duration_seconds": r["duration_seconds"] or 0,
                        "user_name": r["user_name"],
                        "created_at": created_str,
                    })
            except Exception as e:
                print(f"[DB] Error get_telemetry_recent_events MySQL: {e}")
        else:
            try:
                conn = self.get_sqlite_connection()
                cur = conn.cursor()
                cur.execute(sql)
                rows = cur.fetchall()
                conn.close()
                for r in rows:
                    events.append({
                        "id": r["id"],
                        "event_name": r["event_name"],
                        "screen_name": r["screen_name"] or "home",
                        "duration_seconds": r["duration_seconds"] or 0,
                        "user_name": r["user_name"],
                        "created_at": str(r["created_at"]),
                    })
            except Exception as e:
                print(f"[DB] Error get_telemetry_recent_events SQLite: {e}")
        return events


