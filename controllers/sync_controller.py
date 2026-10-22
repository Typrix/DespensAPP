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

            sqlite_cur.execute("SELECT id FROM users WHERE LOWER(email) = ?;", (user_email.strip().lower(),))
            user_row = sqlite_cur.fetchone()
            sqlite_user_id = user_row["id"] if user_row else 1

            # A. Sincronizar Listas de Compras
            sqlite_cur.execute("""
                SELECT id, name, icon_name, icon_color 
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
                if l_key not in existing_list_names:
                    new_id = self.db.add_shopping_list(
                        user_id=mysql_user_id,
                        name=l_name,
                        icon_name=l_row["icon_name"] or "clipboard-text-outline",
                        icon_color=l_row["icon_color"] or "#286ED3"
                    )
                    if new_id:
                        list_id_mapping[l_row["id"]] = new_id
                        existing_list_names[l_key] = new_id
                        summary["synced_lists"] += 1
                else:
                    list_id_mapping[l_row["id"]] = existing_list_names[l_key]

            for local_list_id, mysql_list_id in list_id_mapping.items():
                try:
                    sqlite_cur.execute("""
                        SELECT name, is_checked 
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
                                new_item_id = self.db.add_shopping_list_item(mysql_list_id, it_name)
                                if new_item_id and it_row["is_checked"]:
                                    self.db.toggle_shopping_list_item(new_item_id, True)
                except Exception as e:
                    print(f"[SyncController] Error al sincronizar shopping_list_items: {e}")

            # B. Sincronizar Despensa
            sqlite_cur.execute("""
                SELECT id, name, quantity, unit, min_threshold, category, expiration_date 
                FROM pantry_items 
                WHERE user_id = ?;
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
                elif exp_date and not existing_pantry_names[p_key].expiration_date:
                    self.db.update_pantry_expiration(existing_pantry_names[p_key].id, exp_date)

            # C. Sincronizar Carrito de Compras
            sqlite_cur.execute("""
                SELECT id, title, subtitle, price, quantity, is_checked, list_id 
                FROM cart_items 
                WHERE user_id = ?;
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

            # E. Limpieza de cola local
            sqlite_cur.execute("DELETE FROM app_events;")
            sqlite_cur.execute("DELETE FROM app_sessions;")
            sqlite_conn.commit()
            sqlite_conn.close()

            summary["total"] = (
                summary["synced_pantry"] +
                summary["synced_cart"] +
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


# Alias de compatibilidad
SyncManager = SyncController
