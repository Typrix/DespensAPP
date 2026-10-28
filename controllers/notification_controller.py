# -*- coding: utf-8 -*-
"""
Controlador de Notificaciones para DespensAPP.
Gestiona alertas del sistema operativo utilizando la librería Plyer para avisar al usuario
cuando los productos están por agotarse, se agotaron, están por vencer o ya vencieron.
Diseñado con arquitectura desacoplada, control de frecuencia (anti-spam) y tolerancia a fallos.
"""

import sys
import time
import threading
from typing import List, Dict, Tuple, Optional
from models.pantry_item import PantryItem

# Captura elegante de excepciones internas en hilos de Plyer (evita rastros sucios en Windows)
if hasattr(threading, "excepthook"):
    _orig_thread_hook = threading.excepthook

    def _plyer_thread_hook(args):
        if "Shell_NotifyIconW" in str(args.exc_value) or "balloontip" in str(getattr(args, "thread", "")):
            return
        if _orig_thread_hook:
            _orig_thread_hook(args)

    threading.excepthook = _plyer_thread_hook

try:
    from plyer import notification
    PLYER_AVAILABLE = True
except Exception:
    notification = None
    PLYER_AVAILABLE = False


def _safe_log(message: str):
    """Imprime mensajes de forma segura evitando excepciones de codificación en terminales Windows."""
    try:
        print(message)
    except Exception:
        try:
            encoding = getattr(sys.stdout, "encoding", "utf-8") or "utf-8"
            print(message.encode(encoding, errors="replace").decode(encoding))
        except Exception:
            pass


class NotificationController:
    """Controlador encargado de emitir notificaciones de stock y caducidad mediante Plyer."""

    # Tipos de alerta admitidos
    ALERT_OUT_OF_STOCK = "out_of_stock"
    ALERT_LOW_STOCK = "low_stock"
    ALERT_EXPIRED = "expired"
    ALERT_EXPIRING_SOON = "expiring_soon"

    def __init__(self, cooldown_seconds: int = 900):
        """
        Inicializa el controlador.
        :param cooldown_seconds: Segundos mínimos antes de repetir la misma alerta
                                 para el mismo producto (por defecto 15 minutos).
        """
        self.cooldown_seconds = cooldown_seconds
        # Registro en memoria de alertas emitidas: (item_id, alert_type) -> timestamp
        self._sent_history: Dict[Tuple[int, str], float] = {}

    def is_available(self) -> bool:
        """Verifica si el módulo Plyer está disponible en el entorno de ejecución."""
        return PLYER_AVAILABLE and notification is not None

    def send_notification(self, title: str, message: str, app_name: str = "DespensAPP", timeout: int = 7) -> bool:
        """
        Emite una notificación al sistema operativo de forma segura y tolerante a fallos.
        Captura cualquier excepción interna de Plyer/Win32 para proteger el ciclo de vida de la app.
        """
        if not self.is_available():
            _safe_log(f"[Notificaciones] Plyer no disponible: {title} | {message}")
            return False

        try:
            notification.notify(
                title=title,
                message=message,
                app_name=app_name,
                timeout=timeout,
            )
            _safe_log(f"[Notificaciones] Enviada a Plyer: {title} | {message}")
            return True
        except Exception as err:
            # En Windows, ciertos contextos de terminal o restricciones de bandeja del shell
            # pueden arrojar advertencias en el hilo de Win32. Se captura con gracia.
            _safe_log(f"[Notificaciones] Advertencia al emitir con Plyer: {err}")
            return False

    def check_item_alerts(
        self,
        item: PantryItem,
        force: bool = False,
        check_stock: bool = True,
        check_expiration: bool = True,
    ) -> List[str]:
        """
        Evalúa el estado de stock y caducidad de un producto individual, emitiendo
        las notificaciones necesarias si aplican los criterios de advertencia.

        :param item: Instancia de PantryItem a evaluar.
        :param force: Si es True, ignora el cooldown de tiempo para este producto.
        :param check_stock: Si se evalúa nivel de stock (por agotarse / agotado).
        :param check_expiration: Si se evalúa fecha de caducidad (por vencer / vencido).
        :return: Lista con los tipos de alerta emitidos.
        """
        if not item or not isinstance(item, PantryItem):
            return []

        now = time.time()
        triggered_alerts: List[str] = []

        # ---------------------------------------------------------------------
        # 1. Verificación de Nivel de Stock (Por agotarse o Agotado)
        # ---------------------------------------------------------------------
        if check_stock:
            if item.quantity <= 0:
                alert_type = self.ALERT_OUT_OF_STOCK
                if self._can_send_alert(item.id, alert_type, now, force):
                    title = "DespensAPP: ¡Producto agotado!"
                    message = f"'{item.name}' se ha terminado por completo. Es momento de reponerlo."
                    self.send_notification(title, message)
                    self._record_sent(item.id, alert_type, now)
                    triggered_alerts.append(alert_type)

            elif item.quantity <= item.min_threshold:
                alert_type = self.ALERT_LOW_STOCK
                if self._can_send_alert(item.id, alert_type, now, force):
                    title = "DespensAPP: ¡Queda poco stock!"
                    message = (
                        f"'{item.name}' está por agotarse ({item.formatted_quantity} restantes, "
                        f"umbral: {item.min_threshold} {item.unit}). ¡Agrégalo al carrito!"
                    )
                    self.send_notification(title, message)
                    self._record_sent(item.id, alert_type, now)
                    triggered_alerts.append(alert_type)

        # ---------------------------------------------------------------------
        # 2. Verificación de Vencimiento (Por vencerse o Vencido)
        # ---------------------------------------------------------------------
        if check_expiration:
            days = item.days_until_expiration
            if days is not None:
                if days < 0:
                    alert_type = self.ALERT_EXPIRED
                    if self._can_send_alert(item.id, alert_type, now, force):
                        title = "DespensAPP: ¡Producto vencido!"
                        dias_str = f"hace {abs(days)} día(s)" if abs(days) > 0 else "hoy"
                        message = f"'{item.name}' ya venció ({dias_str}, fecha: {item.formatted_expiration_date}). Revisa tu despensa."
                        self.send_notification(title, message)
                        self._record_sent(item.id, alert_type, now)
                        triggered_alerts.append(alert_type)

                elif 0 <= days <= 3:
                    alert_type = self.ALERT_EXPIRING_SOON
                    if self._can_send_alert(item.id, alert_type, now, force):
                        title = "DespensAPP: ¡Por vencer pronto!"
                        if days == 0:
                            vence_str = "vence HOY"
                        elif days == 1:
                            vence_str = "vence MAÑANA"
                        else:
                            vence_str = f"vence en {days} días"
                        message = f"'{item.name}' {vence_str} ({item.formatted_expiration_date}). ¡Aprovecha de consumirlo!"
                        self.send_notification(title, message)
                        self._record_sent(item.id, alert_type, now)
                        triggered_alerts.append(alert_type)

        return triggered_alerts

    def check_pantry_items(
        self,
        items: List[PantryItem],
        force: bool = False,
    ) -> int:
        """
        Evalúa una lista completa de productos en la despensa.
        Útil al iniciar la app, iniciar sesión o ejecutar revisiones periódicas.

        :param items: Lista de productos en despensa.
        :param force: Si es True, ignora el cooldown.
        :return: Cantidad total de notificaciones emitidas.
        """
        if not items:
            return 0

        total_sent = 0
        for item in items:
            alerts = self.check_item_alerts(item, force=force)
            total_sent += len(alerts)

        return total_sent

    def _can_send_alert(self, item_id: int, alert_type: str, now: float, force: bool) -> bool:
        """Determina si una alerta puede enviarse en base a la configuración de cooldown."""
        if force:
            return True
        key = (item_id, alert_type)
        last_sent = self._sent_history.get(key)
        if last_sent is None:
            return True
        return (now - last_sent) >= self.cooldown_seconds

    def _record_sent(self, item_id: int, alert_type: str, now: float):
        """Registra el timestamp en que fue emitida una alerta para un producto."""
        self._sent_history[(item_id, alert_type)] = now

    def clear_history(self):
        """Reinicia la memoria de alertas emitidas (cooldowns)."""
        self._sent_history.clear()
