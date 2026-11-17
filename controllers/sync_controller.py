# -*- coding: utf-8 -*-
"""
Motor de Sincronización Offline-to-Online para DespensAPP (SyncController).
Migra de forma segura, inteligente y sin duplicados los datos creados
en la base de datos local SQLite (despensapp_local.db) hacia el servidor
central MySQL (despensapp_db) una vez restablecida la conexión.
"""

import os
import sqlite3
from typing import Dict, Any

from models.database import LOCAL_DB_PATH, DatabaseManager


class SyncController:
    """Gestiona la sincronización bidireccional entre SQLite y MySQL."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def has_offline_database(self) -> bool:
        """Comprueba si existe el archivo de base de datos local SQLite."""
        return os.path.exists(LOCAL_DB_PATH)

    def sync_user_data(self, user_email: str) -> Dict[str, Any]:
        """
        Sincroniza los artículos y eventos creados offline hacia MySQL
        para el usuario especificado por su correo electrónico.
        """
        summary = {
            "synced_lists": 0,
            "synced_pantry": 0,
            "synced_cart": 0,
            "synced_purchases": 0,
            "synced_sessions": 0,
            "synced_events": 0,
            "total": 0,
            "success": False,
            "message": ""
        }

        if not self.db.is_mysql:
            summary["message"] = "No hay conexión activa a MySQL para sincronizar."
            return summary

        if not self.has_offline_database():
            summary["message"] = "No se encontraron datos locales offline pendientes."
            summary["success"] = True
            return summary

        mysql_user = self.db.get_user_by_email(user_email)
        if not mysql_user:
            summary["message"] = f"El usuario {user_email} no fue encontrado en MySQL."
            return summary
        mysql_user_id = mysql_user.id

        try:
            sqlite_conn = sqlite3.connect(LOCAL_DB_PATH)
            sqlite_conn.row_factory = sqlite3.Row
            sqlite_cur = sqlite_conn.cursor()
            self._ensure_sqlite_sync_schema(sqlite_cur)

            sqlite_cur.execute("SELECT id, is_pro FROM users WHERE LOWER(email) = ?;", (user_email.strip().lower(),))
            user_row = sqlite_cur.fetchone()
            # Si el usuario no existe en SQLite no hay datos offline suyos que migrar.
            # Con None, los filtros "WHERE user_id = ?" no devuelven filas (evita copiar
            # los datos de otro usuario).
            sqlite_user_id = user_row["id"] if user_row else None
            if user_row and "is_pro" in user_row.keys() and int(user_row["is_pro"] or 0) == 1 and not mysql_user.is_pro:
                self.db.update_user_pro_status(mysql_user_id, 1)

            # 0. Aplicar primero los borrados realizados sin conexión (pending_deletes)
            if sqlite_user_id is not None:
                self._apply_pending_deletes(sqlite_cur, sqlite_user_id, mysql_user_id)

            # A. Sincronizar Listas de Compras creadas offline (is_synced = 0)
            try:
                sqlite_cur.execute("""
                    SELECT id, name, icon_name, icon_color, supermarket, COALESCE(is_synced, 0) AS is_synced
                    FROM shopping_lists
                    WHERE user_id = ?;
                """, (sqlite_user_id,))
            except sqlite3.OperationalError:
                sqlite_cur.execute("""
                    SELECT id, name, icon_name, icon_color, '' AS supermarket, 0 AS is_synced
                    FROM shopping_lists
                    WHERE user_id = ?;
                """, (sqlite_user_id,))
            local_lists = sqlite_cur.fetchall()

            existing_mysql_lists = self.db.get_shopping_lists(mysql_user_id)
            existing_list_names = {l.name.strip().lower(): l.id for l in existing_mysql_lists}
            list_id_mapping = {}

            for l_row in local_lists:
                l_name = l_row["name"].strip()
                l_key = l_name.lower()
                if l_key in existing_list_names:
                    list_id_mapping[l_row["id"]] = existing_list_names[l_key]
                elif int(l_row["is_synced"] or 0) == 0:
                    l_keys = l_row.keys() if hasattr(l_row, "keys") else ()
                    market_val = (l_row["supermarket"] if "supermarket" in l_keys else "") or ""
                    new_id = self.db.add_shopping_list(
                        user_id=mysql_user_id,
                        name=l_name,
                        icon_name=l_row["icon_name"] or "clipboard-text-outline",
                        icon_color=l_row["icon_color"] or "#286ED3",
                        supermarket=market_val,
                    )
                    if new_id:
                        list_id_mapping[l_row["id"]] = new_id
                        existing_list_names[l_key] = new_id
                        summary["synced_lists"] += 1

            for local_list_id, mysql_list_id in list_id_mapping.items():
                try:
                    try:
                        sqlite_cur.execute("""
                            SELECT name, is_checked, price
                            FROM shopping_list_items
                            WHERE list_id = ? AND COALESCE(is_synced, 0) = 0;
                        """, (local_list_id,))
                    except sqlite3.OperationalError:
                        sqlite_cur.execute("""
                            SELECT name, is_checked, 0 AS price
                            FROM shopping_list_items
                            WHERE list_id = ?;
                        """, (local_list_id,))
                    local_list_items = sqlite_cur.fetchall()
                    if local_list_items:
                        existing_items = self.db.get_shopping_list_items(mysql_list_id)
                        existing_item_names = {it.name.strip().lower() for it in existing_items}
                        for it_row in local_list_items:
                            it_name = it_row["name"].strip()
                            if it_name.lower() not in existing_item_names:
                                self.db.add_shopping_list_item(
                                    mysql_list_id, it_name,
                                    price=float(it_row["price"] or 0.0),
                                    is_checked=bool(it_row["is_checked"]),
                                )
                except Exception as e:
                    print(f"[SyncController] Error al sincronizar shopping_list_items: {e}")

            # B. Sincronizar Despensa creada offline (is_synced = 0)
            sqlite_cur.execute("""
                SELECT id, name, quantity, unit, min_threshold, category, expiration_date
                FROM pantry_items
                WHERE user_id = ? AND COALESCE(is_synced, 0) = 0;
            """, (sqlite_user_id,))
            local_pantry = sqlite_cur.fetchall()

            existing_mysql_pantry = self.db.get_pantry_items(mysql_user_id)
            existing_pantry_names = {p.name.strip().lower(): p for p in existing_mysql_pantry}

            for p_row in local_pantry:
                p_name = p_row["name"].strip()
                p_key = p_name.lower()
                exp_date = p_row["expiration_date"] if "expiration_date" in p_row.keys() else None
                if p_key not in existing_pantry_names:
                    self.db.add_pantry_item(
                        user_id=mysql_user_id,
                        name=p_name,
                        quantity=float(p_row["quantity"] or 1.0),
                        unit=p_row["unit"] or "un.",
                        min_threshold=float(p_row["min_threshold"] or 2.0),
                        category=p_row["category"] or "General",
                        expiration_date=exp_date
                    )
                    summary["synced_pantry"] += 1
                else:
                    remote = existing_pantry_names[p_key]
                    if exp_date and not remote.expiration_date:
                        self.db.update_pantry_expiration(remote.id, exp_date)
                    local_cat = (p_row["category"] or "General").strip()
                    if local_cat != "General" and (remote.category or "General") == "General":
                        self.db.update_pantry_item_details(remote.id, remote.name, remote.quantity, remote.unit,
                                                           remote.min_threshold, remote.expiration_date,
                                                           category=local_cat)

            # C. Sincronizar Carrito de Compras creado offline (is_synced = 0)
            sqlite_cur.execute("""
                SELECT id, title, subtitle, price, quantity, is_checked, list_id
                FROM cart_items
                WHERE user_id = ? AND COALESCE(is_synced, 0) = 0;
            """, (sqlite_user_id,))
            local_cart = sqlite_cur.fetchall()

            existing_mysql_cart = self.db.get_cart_items(mysql_user_id)
            existing_cart_titles = {c.title.strip().lower() for c in existing_mysql_cart}

            for c_row in local_cart:
                c_title = c_row["title"].strip()
                if c_title.lower() not in existing_cart_titles:
                    mapped_list_id = list_id_mapping.get(c_row["list_id"])
                    self.db.add_cart_item(
                        user_id=mysql_user_id,
                        title=c_title,
                        subtitle=c_row["subtitle"] or "General",
                        price=float(c_row["price"] or 0.0),
                        quantity=int(c_row["quantity"] or 1),
                        list_id=mapped_list_id
                    )
                    summary["synced_cart"] += 1

            # C2. Sincronizar Historial de Compras creado offline (is_synced = 0)
            try:
                sqlite_cur.execute("""
                    SELECT title, price, quantity, unit, list_id, list_name, purchased_at
                    FROM purchase_history
                    WHERE user_id = ? AND COALESCE(is_synced, 0) = 0;
                """, (sqlite_user_id,))
                local_purchases = sqlite_cur.fetchall()
            except sqlite3.OperationalError:
                local_purchases = []

            existing_purchases = {
                (p.title.strip().lower(), str(p.purchased_at)[:19])
                for p in self.db.get_purchase_history(mysql_user_id)
            }
            for ph_row in local_purchases:
                key = (ph_row["title"].strip().lower(), str(ph_row["purchased_at"])[:19])
                if key in existing_purchases:
                    continue
                self.db.add_purchase_record(
                    user_id=mysql_user_id,
                    title=ph_row["title"],
                    price=float(ph_row["price"] or 0.0),
                    quantity=float(ph_row["quantity"] or 1.0),
                    unit=ph_row["unit"] or "un.",
                    purchased_at=str(ph_row["purchased_at"])[:19],
                    list_id=list_id_mapping.get(ph_row["list_id"]),
                    list_name=ph_row["list_name"],
                )
                summary["synced_purchases"] += 1

            # D. Sincronizar Métricas y Sesiones de Telemetría
            sqlite_cur.execute("""
                SELECT id, platform, app_version, start_time, end_time, duration_seconds
                FROM app_sessions
                WHERE duration_seconds > 0;
            """)
            local_sessions = sqlite_cur.fetchall()

            session_id_mapping = {}
            for s_row in local_sessions:
                mysql_sess_id = self.db.create_session(
                    user_id=mysql_user_id,
                    platform=s_row["platform"] or "Windows",
                    app_version=s_row["app_version"] or "1.0.0"
                )
                if mysql_sess_id:
                    self.db.close_session(mysql_sess_id, int(s_row["duration_seconds"] or 0))
                    session_id_mapping[s_row["id"]] = mysql_sess_id
                    summary["synced_sessions"] += 1

            sqlite_cur.execute("""
                SELECT id, session_id, event_name, screen_name, duration_seconds, metadata_json
                FROM app_events;
            """)
            local_events = sqlite_cur.fetchall()

            for ev_row in local_events:
                mapped_sess = session_id_mapping.get(ev_row["session_id"])
                self.db.log_event(
                    session_id=mapped_sess,
                    user_id=mysql_user_id,
                    event_name=ev_row["event_name"],
                    screen_name=ev_row["screen_name"] or "home",
                    duration_seconds=int(ev_row["duration_seconds"] or 0)
                )
                summary["synced_events"] += 1

            # E. Limpieza de cola de telemetría y actualización de caché espejo local
            sqlite_cur.execute("DELETE FROM app_events;")
            sqlite_cur.execute("DELETE FROM app_sessions;")
            self._refresh_local_cache(sqlite_cur, mysql_user)
            sqlite_conn.commit()
            sqlite_conn.close()

            summary["total"] = (
                summary["synced_pantry"] +
                summary["synced_cart"] +
                summary["synced_purchases"] +
                summary["synced_lists"] +
                summary["synced_sessions"] +
                summary["synced_events"]
            )
            summary["success"] = True
            if summary["total"] > 0:
                summary["message"] = (
                    f"¡Sincronización completada! {summary['synced_pantry']} productos de despensa, "
                    f"{summary['synced_cart']} artículos de compra y {summary['synced_events']} eventos "
                    f"respaldados en el servidor central."
                )
            else:
                summary["message"] = "Tus datos locales ya estaban al día con el servidor."

            print(f"[SyncController] {summary['message']}")
            return summary

        except Exception as e:
            summary["success"] = False
            summary["message"] = f"Error durante la sincronización: {e}"
            print(f"[SyncController] {summary['message']}")
            return summary

    @staticmethod
    def _ensure_sqlite_sync_schema(sqlite_cur):
        """Asegura las columnas is_synced/remote_id y la tabla pending_deletes en SQLite."""
        sqlite_cur.execute("""
            CREATE TABLE IF NOT EXISTS pending_deletes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                entity_type TEXT NOT NULL,
                remote_id INTEGER,
                item_key TEXT DEFAULT '',
                parent_key TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        for tbl in ("shopping_lists", "shopping_list_items", "pantry_items", "cart_items", "purchase_history"):
            for col_def in ("is_synced INTEGER NOT NULL DEFAULT 0", "remote_id INTEGER"):
                try:
                    sqlite_cur.execute(f"ALTER TABLE {tbl} ADD COLUMN {col_def};")
                except Exception:
                    pass

    def _apply_pending_deletes(self, sqlite_cur, sqlite_user_id: int, mysql_user_id: int):
        """Aplica en el servidor los borrados realizados mientras la app estaba sin internet."""
        sqlite_cur.execute(
            "SELECT id, entity_type, remote_id, item_key, parent_key FROM pending_deletes WHERE user_id = ?;",
            (sqlite_user_id,),
        )
        rows = sqlite_cur.fetchall()
        if not rows:
            return

        remote_pantry = None
        remote_lists = None

        for row in rows:
            etype = row["entity_type"]
            rid = row["remote_id"]
            ikey = (row["item_key"] or "").strip().lower()
            pkey = (row["parent_key"] or "").strip().lower()

            if etype == "pantry_item":
                if rid:
                    self.db.delete_pantry_item(int(rid))
                elif ikey:
                    if remote_pantry is None:
                        remote_pantry = self.db.get_pantry_items(mysql_user_id)
                    for item in remote_pantry:
                        if item.name.strip().lower() == ikey:
                            self.db.delete_pantry_item(item.id)
            elif etype == "shopping_list":
                if rid:
                    self.db.delete_shopping_list(int(rid))
                elif ikey:
                    if remote_lists is None:
                        remote_lists = self.db.get_shopping_lists(mysql_user_id)
                    for lst in remote_lists:
                        if lst.name.strip().lower() == ikey:
                            self.db.delete_shopping_list(lst.id)
            elif etype == "shopping_list_item":
                if rid:
                    self.db.delete_shopping_list_item(int(rid))
                elif ikey and pkey:
                    if remote_lists is None:
                        remote_lists = self.db.get_shopping_lists(mysql_user_id)
                    for lst in remote_lists:
                        if lst.name.strip().lower() == pkey:
                            for it in self.db.get_shopping_list_items(lst.id):
                                if it.name.strip().lower() == ikey:
                                    self.db.delete_shopping_list_item(it.id)

        sqlite_cur.execute("DELETE FROM pending_deletes WHERE user_id = ?;", (sqlite_user_id,))

    def _refresh_local_cache(self, sqlite_cur, mysql_user):
        """Actualiza la caché espejo local en SQLite con los datos actuales del servidor."""
        email_norm = mysql_user.email.strip().lower()
        sqlite_cur.execute("SELECT id FROM users WHERE LOWER(email) = ?;", (email_norm,))
        u_row = sqlite_cur.fetchone()
        if u_row:
            local_uid = u_row["id"]
            sqlite_cur.execute(
                "UPDATE users SET name = ?, password_hash = ?, avatar_initials = ?, is_pro = ? WHERE id = ?;",
                (
                    mysql_user.name,
                    mysql_user.password_hash,
                    mysql_user.avatar_initials,
                    int(mysql_user.is_pro or 0),
                    local_uid,
                ),
            )
        else:
            sqlite_cur.execute(
                "INSERT INTO users (name, email, password_hash, avatar_initials, is_pro) VALUES (?, ?, ?, ?, ?);",
                (
                    mysql_user.name,
                    email_norm,
                    mysql_user.password_hash,
                    mysql_user.avatar_initials,
                    int(mysql_user.is_pro or 0),
                ),
            )
            local_uid = sqlite_cur.lastrowid

        # Limpiar datos previos del usuario en caché local
        sqlite_cur.execute(
            "DELETE FROM shopping_list_items WHERE list_id IN (SELECT id FROM shopping_lists WHERE user_id = ?);",
            (local_uid,),
        )
        sqlite_cur.execute("DELETE FROM shopping_lists WHERE user_id = ?;", (local_uid,))
        sqlite_cur.execute("DELETE FROM pantry_items WHERE user_id = ?;", (local_uid,))
        sqlite_cur.execute("DELETE FROM cart_items WHERE user_id = ?;", (local_uid,))
        sqlite_cur.execute("DELETE FROM purchase_history WHERE user_id = ?;", (local_uid,))

        # Re-poblar desde el servidor con is_synced = 1 y remote_id
        for lst in self.db.get_shopping_lists(mysql_user.id):
            sqlite_cur.execute(
                """INSERT INTO shopping_lists (user_id, name, icon_name, icon_color, supermarket, is_synced, remote_id)
                   VALUES (?, ?, ?, ?, ?, 1, ?);""",
                (local_uid, lst.name, lst.icon_name, lst.icon_color, lst.supermarket, lst.id),
            )
            local_list_id = sqlite_cur.lastrowid
            for it in self.db.get_shopping_list_items(lst.id):
                sqlite_cur.execute(
                    """INSERT INTO shopping_list_items (list_id, name, price, is_checked, is_synced, remote_id)
                       VALUES (?, ?, ?, ?, 1, ?);""",
                    (local_list_id, it.name, float(it.price or 0.0), 1 if it.is_checked else 0, it.id),
                )

        for p in self.db.get_pantry_items(mysql_user.id):
            sqlite_cur.execute(
                """INSERT INTO pantry_items (user_id, name, quantity, unit, min_threshold, category, expiration_date, is_synced, remote_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?);""",
                (local_uid, p.name, float(p.quantity), p.unit, float(p.min_threshold), p.category, p.expiration_date, p.id),
            )

        for ph in self.db.get_purchase_history(mysql_user.id):
            sqlite_cur.execute(
                """INSERT INTO purchase_history (user_id, list_id, list_name, title, price, quantity, unit, purchased_at, is_synced, remote_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?);""",
                (local_uid, ph.list_id, ph.list_name, ph.title, float(ph.price or 0.0), float(ph.quantity or 1.0), ph.unit, str(ph.purchased_at)[:19], ph.id),
            )

    def refresh_cache_for_user(self, mysql_user) -> bool:
        """Permite refrescar la caché local en segundo plano o al cerrar la app estando online."""
        if not self.db.is_mysql or not mysql_user:
            return False
        try:
            sqlite_conn = sqlite3.connect(LOCAL_DB_PATH)
            sqlite_conn.row_factory = sqlite3.Row
            sqlite_cur = sqlite_conn.cursor()
            self._ensure_sqlite_sync_schema(sqlite_cur)
            self._refresh_local_cache(sqlite_cur, mysql_user)
            sqlite_conn.commit()
            sqlite_conn.close()
            return True
        except Exception as e:
            print(f"[SyncController] Error refrescando caché local: {e}")
            return False


# Alias de compatibilidad
SyncManager = SyncController
