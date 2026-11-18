# -*- coding: utf-8 -*-
"""
Métricas de producto para el dashboard de DespensAPP.

Lee filas crudas (usuarios, sesiones, eventos, compras, despensa y listas) y calcula
los KPIs en Python, así funciona igual con SQLite y con MySQL. No escribe nada.
"""

import json
import os
import sqlite3
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from statistics import median
from typing import Any, Dict, Iterable, List, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEMO_DB_PATH = os.path.join(BASE_DIR, "demo_metrics.db")
DEMO_ENV = "DESPENSAPP_METRICS_DB"

PERIODS = (7, 30, 90)
DEFAULT_PERIOD = 30

# Nombre visible de cada pantalla de la app
SCREEN_LABELS = {
    "home": "Inicio",
    "cupboard": "Despensa",
    "lists": "Listas",
    "stats": "Estadísticas",
    "splash": "Carga",
}

# Nombre visible de cada evento que registra la app
EVENT_LABELS = {
    "app_opened": "Abrió la app",
    "app_closed": "Cerró la app",
    "screen_view": "Vio una pantalla",
    "user_authenticated": "Inició sesión",
    "user_logout": "Cerró sesión",
    "user_profile_updated": "Editó su cuenta",
    "add_pantry_item": "Agregó a la despensa",
    "edit_pantry_item": "Editó un producto",
    "delete_pantry_item": "Eliminó un producto",
    "update_pantry_expiration": "Cambió un vencimiento",
    "create_shopping_list": "Creó una lista",
    "add_shopping_list_item": "Anotó en una lista",
    "restock_all_to_list": "Añadió lo que falta",
    "finalize_purchase": "Finalizó una compra",
    "migrate_cart_to_lists": "Migró el carrito",
    "upgrade_to_pro": "Se pasó a Pro",
}

# Datos que nunca se muestran en el dashboard aunque vengan en los eventos
_PRIVATE_KEYS = {"email", "name", "password", "password_hash"}


# ----------------------------------------------------------------------
# Fuente de datos
# ----------------------------------------------------------------------
def demo_mode() -> bool:
    """True si el servidor debe usar la base simulada (nunca MySQL ni la base local real)."""
    return os.environ.get(DEMO_ENV, "").strip().lower() == "demo"


class SqliteSource:
    """Lee una base SQLite (la simulada o una copia local)."""

    def __init__(self, path: str, label: str):
        self.path = path
        self.label = label
        self.is_demo = path == DEMO_DB_PATH

    def available(self) -> bool:
        return os.path.isfile(self.path)

    def query(self, sql: str) -> List[Dict[str, Any]]:
        # Solo lectura: abre en modo ro para no poder modificar la base
        uri = "file:" + self.path.replace("\\", "/") + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row
        try:
            return [dict(r) for r in conn.execute(sql).fetchall()]
        except sqlite3.OperationalError:
            return []  # tabla que no existe en bases antiguas
        finally:
            conn.close()


class DatabaseManagerSource:
    """Lee la base configurada de la app (MySQL central o SQLite local) sin escribir."""

    def __init__(self, db):
        self.db = db
        self.label = db.status_message
        self.is_demo = False

    def available(self) -> bool:
        return True

    def query(self, sql: str) -> List[Dict[str, Any]]:
        try:
            if self.db.is_mysql:
                conn = self.db.get_mysql_connection()
                try:
                    with conn.cursor() as cur:
                        cur.execute(sql)
                        return list(cur.fetchall())
                finally:
                    conn.close()
            conn = self.db.get_sqlite_connection()
            try:
                return [dict(r) for r in conn.execute(sql).fetchall()]
            finally:
                conn.close()
        except Exception as e:
            print(f"[Metrics] Error de consulta: {e}")
            return []


# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------
def to_datetime(value) -> Optional[datetime]:
    """Convierte lo que entrega SQLite (texto) o MySQL (datetime) a datetime."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    text = str(value).strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def pct(part: float, total: float) -> float:
    return round(100.0 * part / total, 1) if total else 0.0


def duration_text(seconds: float) -> str:
    seconds = int(round(seconds or 0))
    if seconds < 60:
        return f"{seconds} s"
    return f"{seconds // 60} min {seconds % 60:02d} s"


def money(value: float) -> str:
    return "$" + f"{int(round(value or 0)):,}".replace(",", ".")


def safe_metadata(raw) -> Dict[str, Any]:
    """Metadatos del evento sin datos personales."""
    try:
        data = json.loads(raw) if isinstance(raw, str) else (raw or {})
    except ValueError:
        return {}
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items() if k not in _PRIVATE_KEYS}


# ----------------------------------------------------------------------
# Carga de filas
# ----------------------------------------------------------------------
def load_rows(source) -> Dict[str, List[Dict[str, Any]]]:
    """Trae las filas necesarias (sin contraseñas ni correos)."""
    return {
        "users": source.query("SELECT id, is_pro, created_at FROM users"),
        "sessions": source.query(
            "SELECT id, user_id, platform, start_time, duration_seconds FROM app_sessions"),
        "events": source.query(
            "SELECT id, session_id, user_id, event_name, screen_name, duration_seconds, created_at "
            "FROM app_events"),
        "purchases": source.query(
            "SELECT user_id, price, quantity, purchased_at FROM purchase_history"),
        "pantry": source.query("SELECT user_id, quantity, min_threshold FROM pantry_items"),
        "lists": source.query("SELECT id, user_id FROM shopping_lists"),
    }


# ----------------------------------------------------------------------
# Cálculo
# ----------------------------------------------------------------------
def compute(rows: Dict[str, List[Dict[str, Any]]], days: int = DEFAULT_PERIOD,
            now: Optional[datetime] = None) -> Dict[str, Any]:
    """Calcula los KPIs y series de los últimos `days` días completos (hasta ayer).

    El día en curso se deja fuera para que el gráfico y los promedios no caigan
    a cero solo porque el día recién empieza.
    """
    now = now or datetime.now()
    end = datetime.combine(now.date(), datetime.min.time())  # inicio de hoy (excluido)
    today = end.date() - timedelta(days=1)                    # último día completo
    start = end - timedelta(days=days)

    users = rows.get("users", [])
    sessions = [dict(s, _t=to_datetime(s.get("start_time"))) for s in rows.get("sessions", [])]
    sessions = [s for s in sessions if s["_t"]]
    events = [dict(e, _t=to_datetime(e.get("created_at"))) for e in rows.get("events", [])]
    events = [e for e in events if e["_t"]]
    purchases = [dict(p, _t=to_datetime(p.get("purchased_at"))) for p in rows.get("purchases", [])]
    purchases = [p for p in purchases if p["_t"]]

    in_period = lambda t: start <= t < end  # noqa: E731
    p_sessions = [s for s in sessions if in_period(s["_t"])]
    p_events = [e for e in events if in_period(e["_t"])]
    p_purchases = [p for p in purchases if in_period(p["_t"])]

    # Días activos por usuario (con cualquier sesión)
    active_days = defaultdict(set)
    for s in sessions:
        if s.get("user_id"):
            active_days[s["user_id"]].add(s["_t"].date())

    def actives_between(d0: date, d1: date) -> int:
        return sum(1 for ds in active_days.values() if any(d0 <= d <= d1 for d in ds))

    # --- Usuarios ---
    created = {u["id"]: to_datetime(u.get("created_at")) for u in users}
    total_users = len(users)
    new_users = sum(1 for t in created.values() if t and in_period(t))
    pro_users = sum(1 for u in users if int(u.get("is_pro") or 0) == 1)

    # --- Actividad ---
    daily = []
    for i in range(days):
        d = today - timedelta(days=days - 1 - i)
        daily.append({
            "date": d.isoformat(),
            "active": actives_between(d, d),
            "new": sum(1 for t in created.values() if t and t.date() == d),
        })
    avg_dau = sum(x["active"] for x in daily) / days if days else 0
    dau = actives_between(today, today)
    wau = actives_between(today - timedelta(days=6), today)
    mau = actives_between(today - timedelta(days=29), today)
    period_active = actives_between(start.date(), today)

    durations = [int(s.get("duration_seconds") or 0) for s in p_sessions if int(s.get("duration_seconds") or 0) > 0]

    # --- Retención (sobre los usuarios que ya cumplieron ese día) ---
    def retention(day_from: int, day_to: int) -> Dict[str, Any]:
        eligible = returned = 0
        for uid, t in created.items():
            if not t or (today - t.date()).days < day_to:
                continue
            eligible += 1
            base = t.date()
            if any(day_from <= (d - base).days <= day_to for d in active_days.get(uid, ())):
                returned += 1
        return {"rate": pct(returned, eligible), "returned": returned, "eligible": eligible}

    # --- Compras (una compra = misma persona y misma fecha y hora) ---
    baskets = defaultdict(float)
    for p in p_purchases:
        baskets[(p.get("user_id"), p["_t"])] += float(p.get("price") or 0) * float(p.get("quantity") or 0)
    spend = sum(baskets.values())
    buyers = len({k[0] for k in baskets})

    # --- Despensa y listas (estado actual) ---
    pantry_by_user = Counter(p.get("user_id") for p in rows.get("pantry", []))
    low_stock = sum(1 for p in rows.get("pantry", [])
                    if float(p.get("quantity") or 0) <= float(p.get("min_threshold") or 0))
    lists_by_user = Counter(l.get("user_id") for l in rows.get("lists", []))

    # --- Eventos ---
    by_name = Counter(e["event_name"] for e in p_events)
    users_with = lambda name: {e.get("user_id") for e in p_events if e["event_name"] == name and e.get("user_id")}  # noqa: E731
    opened_users = {s.get("user_id") for s in p_sessions if s.get("user_id")}
    listed_users = users_with("add_shopping_list_item") & opened_users
    bought_users = users_with("finalize_purchase") & listed_users
    pro_ids = {u["id"] for u in users if int(u.get("is_pro") or 0) == 1}
    funnel = [
        {"step": "Abrieron la app", "users": len(opened_users)},
        {"step": "Anotaron en una lista", "users": len(listed_users)},
        {"step": "Finalizaron una compra", "users": len(bought_users)},
        {"step": "Son Pro", "users": len(bought_users & pro_ids)},
    ]
    for i, f in enumerate(funnel):
        f["rate"] = pct(f["users"], funnel[0]["users"])
        f["step_rate"] = pct(f["users"], funnel[i - 1]["users"]) if i else 100.0

    # --- Pantallas ---
    screen_secs = Counter()
    screen_views = Counter()
    for e in p_events:
        if e["event_name"] == "screen_view" and e.get("screen_name") in SCREEN_LABELS and e.get("screen_name") != "splash":
            screen_secs[e["screen_name"]] += int(e.get("duration_seconds") or 0)
            screen_views[e["screen_name"]] += 1
    total_screen = sum(screen_secs.values())
    screens = [
        {"key": k, "label": SCREEN_LABELS[k], "minutes": round(v / 60.0, 1),
         "views": screen_views[k], "share": pct(v, total_screen)}
        for k, v in screen_secs.most_common()
    ]

    # --- Plataformas (usuarios distintos por plataforma en el periodo) ---
    # (solo sesiones con usuario: las de antes de iniciar sesión no tienen a quién contar)
    platform_users = defaultdict(set)
    for s in p_sessions:
        if s.get("user_id"):
            platform_users[(s.get("platform") or "Otra").strip() or "Otra"].add(s["user_id"])
    platform_total = sum(len(v) for v in platform_users.values())
    platforms = sorted(
        ({"platform": k, "users": len(v), "share": pct(len(v), platform_total)} for k, v in platform_users.items()),
        key=lambda x: -x["users"],
    )

    top_events = [
        {"event": k, "label": EVENT_LABELS.get(k, k), "count": v}
        for k, v in by_name.most_common()
        if k not in ("screen_view", "app_closed")
    ][:8]

    sess_count = len(p_sessions)
    return {
        "period_days": days,
        "generated_at": now.strftime("%Y-%m-%d %H:%M"),
        "period_start": start.date().isoformat(),
        "period_end": today.isoformat(),
        "kpis": {
            "total_users": total_users,
            "new_users": new_users,
            "pro_users": pro_users,
            "pro_rate": pct(pro_users, total_users),
            "dau": dau,
            "avg_dau": round(avg_dau, 1),
            "wau": wau,
            "mau": mau,
            "stickiness": pct(avg_dau, mau),
            "period_active": period_active,
            "sessions": sess_count,
            "sessions_per_user": round(sess_count / period_active, 1) if period_active else 0,
            "avg_session": duration_text(sum(durations) / len(durations)) if durations else "0 s",
            "median_session": duration_text(median(durations)) if durations else "0 s",
            "purchases": len(baskets),
            "buyers": buyers,
            "spend": round(spend),
            "spend_str": money(spend),
            "avg_ticket_str": money(spend / len(baskets)) if baskets else "$0",
            "pantry_per_user": round(sum(pantry_by_user.values()) / len(pantry_by_user), 1) if pantry_by_user else 0,
            "low_stock_share": pct(low_stock, sum(pantry_by_user.values())),
            "lists_per_user": round(sum(lists_by_user.values()) / len(lists_by_user), 1) if lists_by_user else 0,
            "restock_uses": by_name.get("restock_all_to_list", 0),
            "list_items_added": by_name.get("add_shopping_list_item", 0),
        },
        "retention": {
            "d1": retention(1, 1),
            "d7": retention(7, 13),
            "d30": retention(30, 36),
        },
        "daily": daily,
        "funnel": funnel,
        "screens": screens,
        "platforms": platforms,
        "top_events": top_events,
    }


def recent_events(source, limit: int = 15) -> List[Dict[str, Any]]:
    """Últimos eventos con nombres legibles y sin datos personales."""
    limit = max(1, min(int(limit), 100))
    rows = source.query(
        "SELECT id, user_id, event_name, screen_name, duration_seconds, metadata_json, created_at "
        f"FROM app_events ORDER BY created_at DESC, id DESC LIMIT {limit}"
    )
    out = []
    for r in rows:
        t = to_datetime(r.get("created_at"))
        out.append({
            "id": r.get("id"),
            "user_id": r.get("user_id"),
            "event": r.get("event_name"),
            "label": EVENT_LABELS.get(r.get("event_name"), r.get("event_name")),
            "screen": SCREEN_LABELS.get(r.get("screen_name"), r.get("screen_name") or ""),
            "duration": int(r.get("duration_seconds") or 0),
            "metadata": safe_metadata(r.get("metadata_json")),
            "created_at": t.strftime("%d-%m %H:%M") if t else "",
        })
    return out


def collect(source, days: int = DEFAULT_PERIOD, now: Optional[datetime] = None) -> Dict[str, Any]:
    """Punto de entrada del servidor: métricas del periodo o un aviso si no hay datos."""
    days = days if days in PERIODS else DEFAULT_PERIOD
    if not source.available():
        return {"available": False, "is_demo": source.is_demo, "source": source.label}
    data = compute(load_rows(source), days=days, now=now)
    data.update({"available": True, "is_demo": source.is_demo, "source": source.label})
    return data
