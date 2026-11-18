# -*- coding: utf-8 -*-
"""
Simulador de uso de DespensAPP para el dashboard (solo Android e iOS).

Crea admin_dashboard/demo_metrics.db con N usuarios y D días de actividad realista:
sesiones, pantallas, eventos de la app, despensa, listas y compras con precios chilenos.
Nunca escribe en MySQL ni en la base local de la app.

Uso:
    .\\venv\\Scripts\\python admin_dashboard\\simulate.py [--users 100] [--days 90] [--seed 7]
Luego:
    $env:DESPENSAPP_METRICS_DB = "demo"; .\\venv\\Scripts\\python -m uvicorn server:app --app-dir admin_dashboard
"""

import argparse
import json
import os
import random
import sqlite3
import sys
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
for path in (BASE_DIR, PARENT_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

import metrics  # noqa: E402
import models.database as dbm  # noqa: E402

PLATFORMS = (("Android", 0.62), ("iOS", 0.38))
APP_VERSIONS = (("1.2.0", 0.55), ("1.1.0", 0.30), ("1.0.0", 0.15))
FIRST_NAMES = ["Camila", "Matías", "Valentina", "Benjamín", "Isidora", "Vicente", "Florencia", "Agustín",
               "Catalina", "Tomás", "Antonia", "Joaquín", "Martina", "Cristóbal", "Josefa", "Lucas",
               "Fernanda", "Diego", "Javiera", "Felipe", "Constanza", "Sebastián", "Paz", "Nicolás"]
LAST_NAMES = ["González", "Muñoz", "Rojas", "Díaz", "Pérez", "Soto", "Contreras", "Silva", "Martínez",
              "Sepúlveda", "Morales", "Rodríguez", "López", "Fuentes", "Hernández", "Torres", "Araya"]
# (nombre, precio por unidad de medida, cantidad típica, unidad, categoría)
PRODUCTS = [
    ("Leche entera", 1190, 2, "L", "Lácteos"), ("Pan de molde", 2490, 1, "un.", "Panadería"),
    ("Huevos x12", 3990, 1, "un.", "Despensa"), ("Arroz", 1690, 1, "kg", "Despensa"),
    ("Fideos spaghetti", 990, 2, "paquete", "Despensa"), ("Aceite maravilla", 3290, 1, "botella", "Despensa"),
    ("Pollo trutro", 3990, 1, "kg", "Carnes"), ("Carne molida", 8990, 0.5, "kg", "Carnes"),
    ("Tomates", 1590, 1, "kg", "Frutas y verduras"), ("Plátanos", 1290, 1, "kg", "Frutas y verduras"),
    ("Paltas", 4990, 0.5, "kg", "Frutas y verduras"), ("Manzanas", 1490, 1, "kg", "Frutas y verduras"),
    ("Yogur natural", 450, 4, "un.", "Lácteos"), ("Queso gauda", 13990, 0.25, "kg", "Lácteos"),
    ("Jugo de naranja", 1290, 1.5, "L", "Bebidas"), ("Bebida cola", 990, 3, "L", "Bebidas"),
    ("Café molido", 5490, 1, "paquete", "Despensa"), ("Detergente", 6990, 1, "botella", "Limpieza"),
    ("Papel higiénico", 5990, 1, "paquete", "Limpieza"), ("Atún en lata", 1290, 3, "lata", "Despensa"),
]
SUPERMARKETS = ["Lider", "Jumbo", "Santa Isabel", "Unimarc", "Tottus"]
LIST_NAMES = ["Compra semanal", "Feria del sábado", "Para el mes", "Once", "Asado del domingo"]
SCREENS = (("home", 0.30), ("lists", 0.32), ("cupboard", 0.26), ("stats", 0.12))


def pick(rng, weighted):
    """Elige un valor de [(valor, peso), ...]."""
    r, acc = rng.random() * sum(w for _, w in weighted), 0.0
    for value, weight in weighted:
        acc += weight
        if r <= acc:
            return value
    return weighted[-1][0]


def fmt(t: datetime) -> str:
    return t.strftime("%Y-%m-%d %H:%M:%S")


def ensure_safe_target(path: str):
    """Se niega a escribir en la base real de la app o fuera de admin_dashboard."""
    real = os.path.abspath(dbm.LOCAL_DB_PATH)
    target = os.path.abspath(path)
    if target == real or os.path.dirname(target) != BASE_DIR:
        raise SystemExit(f"Destino no permitido para datos simulados: {target}")


def create_schema(path: str):
    """Crea las tablas con el mismo esquema SQLite que usa la app (sin conectar a MySQL)."""
    original = dbm.LOCAL_DB_PATH
    dbm.LOCAL_DB_PATH = path
    try:
        manager = dbm.DatabaseManager.__new__(dbm.DatabaseManager)
        manager.use_api = False
        manager.is_mysql = False
        manager._init_sqlite()
    finally:
        dbm.LOCAL_DB_PATH = original


def simulate(path: str = metrics.DEMO_DB_PATH, users: int = 100, days: int = 90, seed: int = 7,
             now: datetime = None) -> dict:
    """Genera la base simulada y retorna un resumen de lo creado."""
    ensure_safe_target(path)
    rng = random.Random(seed)
    now = (now or datetime.now()).replace(microsecond=0)
    start_day = (now - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0)

    if os.path.exists(path):
        os.remove(path)
    create_schema(path)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    counts = {"users": 0, "sessions": 0, "events": 0, "purchases": 0, "pantry": 0, "lists": 0}

    def event(session_id, uid, name, screen, t, duration=0, meta=None):
        cur.execute(
            "INSERT INTO app_events (session_id, user_id, event_name, screen_name, duration_seconds, metadata_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (session_id, uid, name, screen, duration, json.dumps(meta or {}, ensure_ascii=False), fmt(t)),
        )
        counts["events"] += 1

    for n in range(users):
        # Registro repartido en el periodo, con más altas al inicio (lanzamiento) y un repunte reciente
        signup_offset = int(min(days - 1, rng.betavariate(1.1, 1.6) * days))
        signup = start_day + timedelta(days=signup_offset, hours=rng.randint(8, 22), minutes=rng.randint(0, 59))
        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        platform = pick(rng, PLATFORMS)
        version = pick(rng, APP_VERSIONS)
        engagement = rng.choice([0.08, 0.15, 0.25, 0.4, 0.6, 0.8])  # probabilidad base de abrir la app un día
        churn_day = int(rng.expovariate(1 / 35))  # día en que la persona deja de volver
        will_be_pro = rng.random() < (0.02 + 0.20 * engagement)

        cur.execute(
            "INSERT INTO users (name, email, password_hash, avatar_initials, is_pro, created_at) VALUES (?, ?, ?, ?, 0, ?)",
            (name, f"demo{n + 1}@despensapp.test", "simulado", "".join(w[0] for w in name.split())[:2].upper(), fmt(signup)),
        )
        uid = cur.lastrowid
        counts["users"] += 1

        # Despensa y listas iniciales
        products = rng.sample(PRODUCTS, rng.randint(5, 14))
        for pname, _price, qty, unit, cat in products:
            stock = round(qty * rng.choice([0, 0.5, 1, 2, 2, 3, 3, 4]), 2)
            cur.execute(
                "INSERT INTO pantry_items (user_id, name, quantity, unit, min_threshold, category, expiration_date) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (uid, pname, stock, unit, qty, cat, None),
            )
            counts["pantry"] += 1
        list_ids = []
        for _ in range(rng.choice([1, 1, 2, 2, 3])):
            cur.execute(
                "INSERT INTO shopping_lists (user_id, name, icon_color, supermarket, created_at) VALUES (?, ?, ?, ?, ?)",
                (uid, rng.choice(LIST_NAMES), "#286ED3", rng.choice(SUPERMARKETS), fmt(signup)),
            )
            list_ids.append(cur.lastrowid)
            counts["lists"] += 1

        is_pro = False
        day = signup.replace(hour=0, minute=0, second=0)
        first = True
        while day <= now:
            age = (day.date() - signup.date()).days
            fade = 1.0 if age <= churn_day else 0.12  # tras "irse" casi no vuelve
            weekend = 1.25 if day.weekday() >= 5 else 1.0
            if first or rng.random() < min(0.95, engagement * fade * weekend):
                for _s in range(1 if rng.random() < 0.8 else 2):
                    t = signup if first else day + timedelta(hours=rng.randint(7, 22), minutes=rng.randint(0, 59))
                    if t > now:
                        break
                    first = False
                    duration = 0
                    cur.execute(
                        "INSERT INTO app_sessions (user_id, platform, app_version, start_time, end_time, duration_seconds) "
                        "VALUES (?, ?, ?, ?, ?, 0)", (uid, platform, version, fmt(t), None),
                    )
                    sid = cur.lastrowid
                    counts["sessions"] += 1
                    event(sid, uid, "app_opened", "splash", t, meta={"platform": platform})
                    if age == 0 and t == signup:
                        event(sid, uid, "user_authenticated", "home", t + timedelta(seconds=5))
                    clock = t + timedelta(seconds=8)
                    for _v in range(rng.randint(2, 6)):
                        screen = pick(rng, SCREENS)
                        secs = int(rng.lognormvariate(3.6, 0.7))  # ~35 s típico, cola larga
                        secs = max(3, min(secs, 600))
                        if screen == "lists" and rng.random() < 0.55:
                            for _i in range(rng.randint(1, 4)):
                                prod = rng.choice(PRODUCTS)
                                event(sid, uid, "add_shopping_list_item", "lists", clock + timedelta(seconds=rng.randint(1, secs)),
                                      meta={"list_id": rng.choice(list_ids)})
                            if rng.random() < 0.38:
                                bought = rng.sample(PRODUCTS, rng.randint(3, 9))
                                when = clock + timedelta(seconds=secs)
                                total = 0.0
                                for pname, price, qty, unit, _cat in bought:
                                    price = round(price * rng.uniform(0.85, 1.2) / 10) * 10
                                    cur.execute(
                                        "INSERT INTO purchase_history (user_id, list_id, list_name, title, price, quantity, unit, purchased_at) "
                                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                        (uid, list_ids[0], "Compra semanal", pname, price, qty, unit, fmt(when)),
                                    )
                                    counts["purchases"] += 1
                                    total += price * qty
                                event(sid, uid, "finalize_purchase", "lists", when,
                                      meta={"items": len(bought), "total": round(total)})
                        elif screen == "cupboard":
                            r = rng.random()
                            if r < 0.30:
                                event(sid, uid, "add_pantry_item", "cupboard", clock + timedelta(seconds=4),
                                      meta={"unit": rng.choice(["un.", "kg", "L", "g"])})
                            elif r < 0.45:
                                event(sid, uid, "edit_pantry_item", "cupboard", clock + timedelta(seconds=4))
                            elif r < 0.55:
                                event(sid, uid, "restock_all_to_list", "cupboard", clock + timedelta(seconds=4),
                                      meta={"items": rng.randint(2, 6)})
                        elif screen == "stats" and will_be_pro and not is_pro and age >= 3 and rng.random() < 0.6:
                            event(sid, uid, "upgrade_to_pro", "stats", clock + timedelta(seconds=6),
                                  meta={"target_period": rng.choice(["semester", "year", "profile"])})
                            cur.execute("UPDATE users SET is_pro = 1 WHERE id = ?", (uid,))
                            is_pro = True
                        clock += timedelta(seconds=secs)
                        event(sid, uid, "screen_view", screen, clock, duration=secs)
                        duration += secs
                    end = clock + timedelta(seconds=2)
                    if end > now:
                        end = now
                    duration = max(duration, int((end - t).total_seconds()))
                    event(sid, uid, "app_closed", screen, end, meta={"total_seconds": duration})
                    cur.execute("UPDATE app_sessions SET end_time = ?, duration_seconds = ? WHERE id = ?",
                                (fmt(end), duration, sid))
            day += timedelta(days=1)

    conn.commit()
    conn.close()
    return counts


def main():
    parser = argparse.ArgumentParser(description="Genera datos simulados para el dashboard de DespensAPP.")
    parser.add_argument("--users", type=int, default=100)
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    counts = simulate(users=args.users, days=args.days, seed=args.seed)
    print(f"[Simulación] Base: {metrics.DEMO_DB_PATH}")
    print("[Simulación] " + ", ".join(f"{k}: {v}" for k, v in counts.items()))


if __name__ == "__main__":
    main()
