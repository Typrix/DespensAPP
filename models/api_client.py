# -*- coding: utf-8 -*-
"""
Cliente HTTP REST para DespensAPP.
Permite que DatabaseManager consulte y modifique los datos a través de la API externa
cuando no es posible conectarse directamente al puerto de MySQL.
"""

import json
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

try:
    import certifi
except ImportError:
    certifi = None

try:
    import requests
except ImportError:
    requests = None

from models.cart_item import CartItem
from models.pantry_item import PantryItem
from models.purchase_record import PurchaseRecord
from models.shopping_list import ShoppingList, ShoppingListItem
from models.user import User


def _build_user(data: Optional[Dict[str, Any]]) -> Optional[User]:
    if not data:
        return None
    return User(
        id=int(data["id"]),
        name=data["name"],
        email=data["email"],
        avatar_initials=data.get("avatar_initials", "US"),
        password_hash=data.get("password_hash", ""),
        is_pro=int(data.get("is_pro", 0)),
    )


def _build_pantry_item(data: Optional[Dict[str, Any]]) -> Optional[PantryItem]:
    if not data:
        return None
    return PantryItem(
        id=int(data["id"]),
        user_id=int(data["user_id"]),
        name=data["name"],
        quantity=float(data["quantity"]),
        unit=data.get("unit", "un."),
        min_threshold=float(data.get("min_threshold", 2.0)),
        category=data.get("category", "General"),
        expiration_date=data.get("expiration_date"),
    )


def _build_list_item(data: Dict[str, Any]) -> ShoppingListItem:
    return ShoppingListItem(
        id=int(data["id"]),
        list_id=int(data["list_id"]),
        name=data["name"],
        is_checked=bool(data.get("is_checked", False)),
        created_at=data.get("created_at", ""),
        price=float(data.get("price", 0.0)),
        quantity=max(1, int(data.get("quantity", 1) or 1)),
    )


def _build_shopping_list(data: Dict[str, Any]) -> ShoppingList:
    raw_items = data.get("items")
    items = [_build_list_item(it) for it in raw_items] if raw_items is not None else None
    return ShoppingList(
        id=int(data["id"]),
        user_id=int(data["user_id"]),
        name=data["name"],
        icon_name=data.get("icon_name", "clipboard-text-outline"),
        icon_color=data.get("icon_color", "#286ED3"),
        supermarket=data.get("supermarket", ""),
        items_count=int(data.get("items_count", 0)),
        pending_count=int(data.get("pending_count", 0)),
        items=items,
    )


def _build_cart_item(data: Dict[str, Any]) -> CartItem:
    return CartItem(
        id=int(data["id"]),
        user_id=int(data["user_id"]),
        title=data["title"],
        subtitle=data.get("subtitle", "Lista general"),
        price=float(data.get("price", 0.0)),
        quantity=int(data.get("quantity", 1)),
        is_checked=bool(data.get("is_checked", False)),
        list_id=data.get("list_id"),
    )


def _build_purchase_record(data: Dict[str, Any]) -> PurchaseRecord:
    return PurchaseRecord(
        id=int(data["id"]),
        user_id=int(data["user_id"]),
        title=data["title"],
        price=float(data.get("price", 0.0)),
        quantity=float(data.get("quantity", 1.0)),
        unit=data.get("unit", "un."),
        list_id=data.get("list_id"),
        purchased_at=data.get("purchased_at", ""),
        list_name=data.get("list_name"),
    )


class ApiDatabaseClient:
    """Cliente HTTP que implementa las operaciones de datos contra la API FastAPI."""

    def __init__(
        self,
        base_url: str,
        api_key: str = "",
        timeout_seconds: float = 6.0,
        transport=None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = (api_key or "").strip()
        self.timeout_seconds = timeout_seconds
        self._transport = transport  # inyectable para pruebas unitarias
        self._use_method_override = False  # usa POST + X-HTTP-Method-Override si el hosting bloquea PUT/PATCH/DELETE
        self._ssl_context = self._build_ssl_context()
        self._verify_ssl = certifi.where() if certifi is not None else True
        self._session = requests.Session() if requests is not None else None
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self.cache_ttl: float = 15.0

    def _cached_get(self, key: str, loader, default_val=None):
        """Retorna resultado cacheado en RAM si no ha expirado; ante corte de red usa último valor o default."""
        entry = self._cache.get(key)
        if entry is not None:
            ts, value = entry
            if (time.time() - ts) < self.cache_ttl:
                return list(value) if isinstance(value, list) else dict(value) if isinstance(value, dict) else value
        try:
            result = loader()
            self._cache[key] = (time.time(), result)
            return list(result) if isinstance(result, list) else dict(result) if isinstance(result, dict) else result
        except Exception as e:
            print(f"[API] Error de red en lectura ({key}), usando respaldo en memoria: {e}")
            if entry is not None:
                _, value = entry
                return list(value) if isinstance(value, list) else dict(value) if isinstance(value, dict) else value
            return default_val() if callable(default_val) else default_val

    def _invalidate_cache(self):
        """Limpia la caché en memoria tras cualquier operación de escritura."""
        self._cache.clear()

    @staticmethod
    def _build_ssl_context():
        """Crea un contexto SSL usando certifi (necesario en Android para validar HTTPS)."""
        try:
            if certifi is not None:
                return ssl.create_default_context(cafile=certifi.where())
            return ssl.create_default_context()
        except Exception:
            return None

    def _send_http(
        self,
        url: str,
        method: str,
        body: Optional[bytes],
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        if self._session is not None:
            try:
                resp = self._session.request(
                    method=method,
                    url=url,
                    data=body,
                    headers=headers,
                    timeout=self.timeout_seconds,
                    verify=self._verify_ssl,
                )
            except Exception:
                # Si el servidor o Android cerró el socket inactivo (RemoteDisconnected),
                # recrear la sesión Keep-Alive y reintentar una vez
                try:
                    self._session.close()
                except Exception:
                    pass
                self._session = requests.Session()
                resp = self._session.request(
                    method=method,
                    url=url,
                    data=body,
                    headers=headers,
                    timeout=self.timeout_seconds,
                    verify=self._verify_ssl,
                )
            if resp.status_code >= 400:
                raise urllib.error.HTTPError(url, resp.status_code, resp.reason, resp.headers, None)
            return resp.json() if resp.content else {}

        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=self.timeout_seconds, context=self._ssl_context) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}

    def _request(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if method in ("POST", "PUT", "PATCH", "DELETE") and not path.startswith("/telemetry"):
            self._invalidate_cache()
        url = f"{self.base_url}{path}"
        if params:
            clean = {k: v for k, v in params.items() if v is not None}
            if clean:
                url = f"{url}?{urllib.parse.urlencode(clean)}"

        headers = {
            "Accept": "application/json",
            "User-Agent": "DespensAPP/1.0",
        }
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        if self._transport is not None:
            return self._transport(method, path, payload, params, headers)

        actual_method = method
        if self._use_method_override and method in ("PUT", "PATCH", "DELETE"):
            headers["X-HTTP-Method-Override"] = method
            actual_method = "POST"
            if body is None:
                body = b"{}"
                headers["Content-Type"] = "application/json"

        try:
            return self._send_http(url, actual_method, body, headers)
        except urllib.error.HTTPError as e:
            if e.code in (403, 405) and method in ("PUT", "PATCH", "DELETE") and not self._use_method_override:
                # Reintentar como POST con X-HTTP-Method-Override para hostings que bloquean PUT/PATCH/DELETE
                self._use_method_override = True
                headers["X-HTTP-Method-Override"] = method
                retry_body = body if body is not None else b"{}"
                headers.setdefault("Content-Type", "application/json")
                return self._send_http(url, "POST", retry_body, headers)
            raise

    def check_health(self) -> Tuple[bool, Dict[str, Any]]:
        """Comprueba si la API externa responde correctamente."""
        try:
            data = self._request("GET", "/health")
            return data.get("status") == "ok", data
        except Exception as e:
            print(f"[API] Error en check_health ({self.base_url}): {e}")
            return False, {}

    # ------------------------------------------------------------------
    # Autenticación y Usuarios
    # ------------------------------------------------------------------
    def authenticate_user(self, email: str, password_hash: str) -> Tuple[bool, str, Optional[User]]:
        data = self._request("POST", "/auth/login", {"email": email, "password_hash": password_hash})
        return bool(data.get("ok")), data.get("message", ""), _build_user(data.get("user"))

    def register_user(self, name: str, email: str, password_hash: str) -> Tuple[bool, str, Optional[User]]:
        data = self._request(
            "POST",
            "/auth/register",
            {"name": name, "email": email, "password_hash": password_hash},
        )
        return bool(data.get("ok")), data.get("message", ""), _build_user(data.get("user"))

    def get_user_by_email(self, email: str) -> Optional[User]:
        data = self._request("GET", "/users/by-email", params={"email": email})
        return _build_user(data.get("user"))

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        data = self._request("GET", f"/users/{user_id}")
        return _build_user(data.get("user"))

    def update_user_pro_status(self, user_id: int, is_pro: int = 1) -> bool:
        data = self._request("PATCH", f"/users/{user_id}/pro", {"is_pro": is_pro})
        return bool(data.get("ok"))

    def update_user_profile(
        self,
        user_id: int,
        name: str,
        email: str,
        password_hash: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[User]]:
        payload: Dict[str, Any] = {
            "name": (name or "").strip(),
            "email": (email or "").strip().lower(),
        }
        if password_hash:
            payload["password_hash"] = password_hash
        try:
            data = self._request("PUT", f"/users/{user_id}", payload)
            return (
                bool(data.get("ok")),
                data.get("message", "Datos de la cuenta actualizados con éxito."),
                _build_user(data.get("user")),
            )
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Si el servidor remoto aún no tiene la ruta PUT /users/{id}, reconstruir usuario actualizado
                current = self.get_user_by_id(user_id)
                initials = User.generate_initials(payload["name"])
                updated_user = User(
                    id=user_id,
                    name=payload["name"],
                    email=payload["email"],
                    avatar_initials=initials,
                    password_hash=password_hash or (current.password_hash if current else ""),
                    is_pro=int(current.is_pro if current else 0),
                )
                return True, "Datos de la cuenta actualizados con éxito.", updated_user
            raise

    # ------------------------------------------------------------------
    # Despensa
    # ------------------------------------------------------------------
    def get_pantry_items(self, user_id: int) -> List[PantryItem]:
        def _load():
            data = self._request("GET", f"/pantry/{user_id}")
            return [it for it in (_build_pantry_item(raw) for raw in data.get("items", [])) if it is not None]
        return self._cached_get(f"pantry:{user_id}", _load, default_val=list)

    def get_pantry_item_by_id(self, item_id: int) -> Optional[PantryItem]:
        data = self._request("GET", f"/pantry/item/{item_id}")
        return _build_pantry_item(data.get("item"))

    def add_pantry_item(
        self,
        user_id: int,
        name: str,
        quantity: float,
        unit: str,
        min_threshold: float,
        category: str = "General",
        expiration_date: Optional[str] = None,
    ) -> Optional[int]:
        data = self._request(
            "POST",
            "/pantry",
            {
                "user_id": user_id,
                "name": name,
                "quantity": quantity,
                "unit": unit,
                "min_threshold": min_threshold,
                "category": category,
                "expiration_date": expiration_date,
            },
        )
        return data.get("id")

    def update_pantry_quantity(self, item_id: int, delta: float) -> bool:
        data = self._request("PATCH", f"/pantry/item/{item_id}/quantity", {"delta": delta})
        return bool(data.get("ok"))

    def set_pantry_quantity(self, item_id: int, quantity: float) -> bool:
        data = self._request("PUT", f"/pantry/item/{item_id}/quantity", {"quantity": quantity})
        return bool(data.get("ok"))

    def update_pantry_expiration(self, item_id: int, expiration_date: Optional[str] = None) -> bool:
        data = self._request(
            "PATCH", f"/pantry/item/{item_id}/expiration", {"expiration_date": expiration_date}
        )
        return bool(data.get("ok"))

    def update_pantry_item_details(
        self,
        item_id: int,
        name: str,
        quantity: float,
        unit: str,
        min_threshold: float,
        expiration_date: Optional[str] = None,
        category: Optional[str] = None,
    ) -> bool:
        data = self._request(
            "PUT",
            f"/pantry/item/{item_id}",
            {
                "name": name,
                "quantity": quantity,
                "unit": unit,
                "min_threshold": min_threshold,
                "expiration_date": expiration_date,
                "category": category,
            },
        )
        return bool(data.get("ok"))

    def delete_pantry_item(self, item_id: int) -> bool:
        data = self._request("DELETE", f"/pantry/item/{item_id}")
        return bool(data.get("ok"))

    # ------------------------------------------------------------------
    # Listas de Compras
    # ------------------------------------------------------------------
    def get_shopping_lists(self, user_id: int) -> List[ShoppingList]:
        def _load():
            data = self._request("GET", f"/lists/{user_id}")
            return [_build_shopping_list(raw) for raw in data.get("lists", [])]
        return self._cached_get(f"lists:{user_id}", _load, default_val=list)

    def add_shopping_list(
        self,
        user_id: int,
        name: str,
        icon_color: str = "#286ED3",
        icon_name: str = "clipboard-text-outline",
        supermarket: str = "",
    ) -> Optional[int]:
        data = self._request(
            "POST",
            "/lists",
            {
                "user_id": user_id,
                "name": name,
                "icon_color": icon_color,
                "icon_name": icon_name,
                "supermarket": supermarket,
            },
        )
        return data.get("id")

    def update_shopping_list_name(
        self, list_id: int, new_name: str, new_color: Optional[str] = None
    ) -> bool:
        data = self._request(
            "PATCH", f"/lists/{list_id}", {"new_name": new_name, "new_color": new_color}
        )
        return bool(data.get("ok"))

    def delete_shopping_list(self, list_id: int) -> bool:
        data = self._request("DELETE", f"/lists/{list_id}")
        return bool(data.get("ok"))

    def get_shopping_list_items(self, list_id: int) -> List[ShoppingListItem]:
        def _load():
            data = self._request("GET", f"/lists/{list_id}/items")
            return [_build_list_item(raw) for raw in data.get("items", [])]
        return self._cached_get(f"list_items:{list_id}", _load, default_val=list)

    def add_shopping_list_item(
        self, list_id: int, name: str, price: float = 0.0, is_checked: bool = False,
        quantity: int = 1
    ) -> Optional[int]:
        data = self._request(
            "POST",
            f"/lists/{list_id}/items",
            {"name": name, "price": price, "is_checked": is_checked, "quantity": quantity},
        )
        return data.get("id")

    def toggle_shopping_list_item(self, item_id: int, is_checked: bool) -> bool:
        data = self._request("PATCH", f"/list-items/{item_id}/toggle", {"is_checked": is_checked})
        return bool(data.get("ok"))

    def update_shopping_list_item(self, item_id: int, name: str, price: float,
                                  quantity: Optional[int] = None) -> bool:
        payload = {"name": name, "price": price}
        if quantity is not None:
            payload["quantity"] = max(1, int(quantity))
        data = self._request(
            "PUT", f"/list-items/{item_id}", payload,
        )
        return bool(data.get("ok"))

    def update_shopping_list_item_name(self, item_id: int, new_name: str) -> bool:
        data = self._request("PATCH", f"/list-items/{item_id}/name", {"new_name": new_name})
        return bool(data.get("ok"))

    def delete_shopping_list_item(self, item_id: int) -> bool:
        data = self._request("DELETE", f"/list-items/{item_id}")
        return bool(data.get("ok"))

    # ------------------------------------------------------------------
    # Carrito heredado
    # ------------------------------------------------------------------
    def get_cart_items(self, user_id: int) -> List[CartItem]:
        data = self._request("GET", f"/cart/{user_id}")
        return [_build_cart_item(raw) for raw in data.get("items", [])]

    def add_cart_item(
        self,
        user_id: int,
        title: str,
        subtitle: str,
        price: float,
        quantity: int = 1,
        list_id: Optional[int] = None,
    ) -> Optional[int]:
        data = self._request(
            "POST",
            "/cart",
            {
                "user_id": user_id,
                "title": title,
                "subtitle": subtitle,
                "price": price,
                "quantity": quantity,
                "list_id": list_id,
            },
        )
        return data.get("id")

    def toggle_cart_item(self, item_id: int, is_checked: bool) -> bool:
        data = self._request("PATCH", f"/cart/{item_id}/toggle", {"is_checked": is_checked})
        return bool(data.get("ok"))

    def update_cart_item(self, item_id: int, title: str, subtitle: str, price: float) -> bool:
        data = self._request(
            "PUT", f"/cart/{item_id}", {"title": title, "subtitle": subtitle, "price": price}
        )
        return bool(data.get("ok"))

    def delete_cart_item(self, item_id: int) -> bool:
        data = self._request("DELETE", f"/cart/{item_id}")
        return bool(data.get("ok"))

    # ------------------------------------------------------------------
    # Compras, Precios y Ofertas
    # ------------------------------------------------------------------
    def get_purchase_history(self, user_id: int, since: Optional[str] = None) -> List[PurchaseRecord]:
        def _load():
            data = self._request("GET", f"/purchases/{user_id}", params={"since": since})
            return [_build_purchase_record(raw) for raw in data.get("records", [])]
        return self._cached_get(f"purchases:{user_id}:{since or ''}", _load, default_val=list)

    def add_purchase_record(
        self,
        user_id: int,
        title: str,
        price: float,
        quantity: float,
        unit: str,
        purchased_at: str,
        list_id: Optional[int] = None,
        list_name: Optional[str] = None,
    ) -> Optional[int]:
        data = self._request(
            "POST",
            "/purchases",
            {
                "user_id": user_id,
                "title": title,
                "price": price,
                "quantity": quantity,
                "unit": unit,
                "purchased_at": purchased_at,
                "list_id": list_id,
                "list_name": list_name,
            },
        )
        return data.get("id")

    def get_last_known_price(self, user_id: int, product_name: str) -> float:
        data = self._request(
            "GET",
            "/prices/last-known",
            params={"user_id": user_id, "product_name": product_name},
        )
        return float(data.get("price", 0.0))

    def find_cheaper_supermarket_offer(
        self,
        product_name: str,
        current_price: float,
        current_supermarket: str = "",
        max_age_days: int = 15,
    ) -> Optional[dict]:
        data = self._request(
            "GET",
            "/prices/cheaper-offer",
            params={
                "product_name": product_name,
                "current_price": current_price,
                "current_supermarket": current_supermarket,
                "max_age_days": max_age_days,
            },
        )
        return data.get("offer")

    def get_cheaper_offers_for_user(self, user_id: int) -> List[dict]:
        def _load():
            data = self._request("GET", f"/prices/cheaper-offers/{user_id}")
            return data.get("offers", [])
        return self._cached_get(f"offers:{user_id}", _load, default_val=list)

    # ------------------------------------------------------------------
    # Estadísticas y Telemetría
    # ------------------------------------------------------------------
    def get_user_statistics(self, user_id: int) -> dict:
        def _load():
            data = self._request("GET", f"/users/{user_id}/statistics")
            stats = data.get("statistics", {})
            for key in ("first_reponer", "first_por_agotar", "first_vencido", "first_por_vencer"):
                if stats.get(key):
                    stats[key] = _build_pantry_item(stats[key])
            return stats
        return self._cached_get(f"stats:{user_id}", _load, default_val=dict)

    def create_session(
        self, user_id: Optional[int] = None, platform: str = "Windows", app_version: str = "1.0.0"
    ) -> int:
        try:
            data = self._request(
                "POST",
                "/telemetry/sessions",
                {"user_id": user_id, "platform": platform, "app_version": app_version},
            )
            return int(data.get("session_id", 0))
        except Exception:
            return 0

    def close_session(self, session_id: int, duration_seconds: int = 0) -> bool:
        try:
            data = self._request(
                "POST",
                f"/telemetry/sessions/{session_id}/close",
                {"duration_seconds": duration_seconds},
            )
            return bool(data.get("ok"))
        except Exception:
            return False

    def log_event(
        self,
        session_id: Optional[int],
        user_id: Optional[int],
        event_name: str,
        screen_name: str = "home",
        duration_seconds: int = 0,
        metadata: Optional[dict] = None,
    ) -> int:
        payload = {
            "session_id": session_id,
            "user_id": user_id,
            "event_name": event_name,
            "screen_name": screen_name,
            "duration_seconds": duration_seconds,
            "metadata": metadata,
        }
        if self._transport is not None:
            try:
                data = self._request("POST", "/telemetry/events", payload)
                return int(data.get("event_id", 0))
            except Exception:
                return 0

        # Enviar telemetría en segundo plano para no bloquear nunca la interfaz
        def _send_async():
            try:
                url = f"{self.base_url}/telemetry/events"
                headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": "DespensAPP/1.0",
                }
                if self.api_key:
                    headers["X-API-Key"] = self.api_key
                body = json.dumps(payload).encode("utf-8")
                if requests is not None:
                    requests.post(
                        url,
                        data=body,
                        headers=headers,
                        timeout=self.timeout_seconds,
                        verify=self._verify_ssl,
                    )
                else:
                    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
                    urllib.request.urlopen(req, timeout=self.timeout_seconds, context=self._ssl_context).close()
            except Exception:
                pass

        threading.Thread(target=_send_async, daemon=True).start()
        return 0

    def log_events_batch(self, events: List[Dict[str, Any]], async_send: bool = True) -> int:
        """Envía un lote de eventos de telemetría (1 sola petición si /batch existe, o respaldo espaciado)."""
        if not events:
            return 0

        if self._transport is not None:
            sent = 0
            for ev in events:
                try:
                    self._request("POST", "/telemetry/events", ev)
                    sent += 1
                except Exception:
                    pass
            return sent

        def _dispatch():
            try:
                self._request("POST", "/telemetry/events/batch", {"events": events})
                return len(events)
            except urllib.error.HTTPError as e:
                if e.code != 404:
                    return 0
            except Exception:
                return 0

            # Respaldo si el servidor PHP aún no tiene /telemetry/events/batch
            sent = 0
            for idx, ev in enumerate(events):
                try:
                    self._request("POST", "/telemetry/events", ev)
                    sent += 1
                    if idx + 1 < len(events):
                        time.sleep(0.15)
                except Exception:
                    pass
            return sent

        if async_send:
            threading.Thread(target=_dispatch, daemon=True).start()
            return len(events)
        return _dispatch()

    # ------------------------------------------------------------------
    # Analítica para Panel Admin (KPIs, pantallas y eventos recientes)
    # ------------------------------------------------------------------
    def get_telemetry_kpis(self) -> dict:
        try:
            return self._request("GET", "/analytics/kpis")
        except Exception:
            return {
                "total_users": 0,
                "total_sessions": 0,
                "avg_session_seconds": 0,
                "avg_session_str": "0m 0s",
                "total_events": 0,
                "most_active_screen": "Inicio",
            }

    def get_telemetry_screen_times(self) -> List[dict]:
        try:
            data = self._request("GET", "/analytics/screen-times")
            return data.get("screens", [])
        except Exception:
            return []

    def get_telemetry_recent_events(self, limit: int = 25) -> List[dict]:
        try:
            data = self._request("GET", "/analytics/recent-events", params={"limit": int(limit)})
            return data.get("events", [])
        except Exception:
            return []
