# -*- coding: utf-8 -*-
"""
Controlador de Telemetría y Analítica de Producto para DespensAPP.
Mide la duración de las sesiones, tiempo de permanencia por pantalla y eventos clave.
"""

import time
from typing import Optional


class AnalyticsController:
    """Controlador centralizado de telemetría y analítica para DespensAPP."""

    def __init__(self, db_manager):
        self.db = db_manager
        self.session_id: Optional[int] = None
        self.session_start_time: float = 0.0
        self.current_screen: str = "home"
        self.screen_start_time: float = 0.0
        self.active_user_id: Optional[int] = None

    def start_session(self, user_id: Optional[int] = None, platform: str = "Windows"):
        """Inicia una sesión de usuario y cronometra el tiempo total."""
        self.active_user_id = user_id
        self.session_start_time = time.time()
        self.screen_start_time = time.time()
        self.current_screen = "home"

        self.session_id = self.db.create_session(
            user_id=user_id,
            platform=platform,
            app_version="1.0.0"
        )
        self.track_event("app_opened", screen_name="splash", metadata={"platform": platform})

    def update_user(self, user_id: Optional[int]):
        """Actualiza el ID de usuario activo en la sesión."""
        self.active_user_id = user_id

    def track_screen(self, new_screen: str):
        """Mide y registra el tiempo de permanencia en la pantalla anterior y cambia a la nueva."""
        now = time.time()
        if self.screen_start_time > 0:
            duration = int(now - self.screen_start_time)
            if duration >= 1:
                self.db.log_event(
                    session_id=self.session_id,
                    user_id=self.active_user_id,
                    event_name="screen_view",
                    screen_name=self.current_screen,
                    duration_seconds=duration,
                    metadata={"to_screen": new_screen}
                )

        self.current_screen = new_screen
        self.screen_start_time = now

    def track_event(self, event_name: str, screen_name: Optional[str] = None, metadata: Optional[dict] = None):
        """Registra un evento puntual de interacción."""
        scr = screen_name or self.current_screen
        self.db.log_event(
            session_id=self.session_id,
            user_id=self.active_user_id,
            event_name=event_name,
            screen_name=scr,
            duration_seconds=0,
            metadata=metadata or {}
        )

    def end_session(self):
        """Cierra la sesión registrando el tiempo total acumulado."""
        if not self.session_id:
            return

        now = time.time()
        total_duration = int(now - self.session_start_time)

        last_screen_dur = int(now - self.screen_start_time)
        if last_screen_dur >= 1:
            self.db.log_event(
                session_id=self.session_id,
                user_id=self.active_user_id,
                event_name="screen_view",
                screen_name=self.current_screen,
                duration_seconds=last_screen_dur
            )

        self.track_event("app_closed", screen_name=self.current_screen, metadata={"total_seconds": total_duration})
        self.db.close_session(self.session_id, total_duration)
        self.session_id = None


# Alias de compatibilidad
AnalyticsManager = AnalyticsController
