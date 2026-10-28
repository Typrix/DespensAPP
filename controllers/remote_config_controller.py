# -*- coding: utf-8 -*-
"""
Controlador de Configuración Remota (RemoteConfigController).
Gestiona la obtención, fallback local y lectura de parámetros de configuración
dinámica en formato JSON (feature flags, banners informativos, URLs y modo mantenimiento).
"""

import json
import os
import urllib.request
import urllib.error
from typing import Dict, Any, Optional


class RemoteConfigController:
    """Controlador que administra la configuración remota de la aplicación."""

    DEFAULT_CONFIG = {
        "app_version": "1.0.0",
        "min_supported_version": "1.0.0",
        "maintenance_mode": False,
        "banner": {
            "enabled": False,
            "title": "Aviso",
            "message": "",
            "type": "info",
            "badge_text": "REMOTO",
        },
        "features": {
            "cloud_sync": True,
            "advanced_analytics": True,
            "smart_notifications": True,
        },
        "endpoints": {
            "api_base_url": "http://localhost:8000/api/v1",
            "sync_interval_seconds": 600,
        },
    }

    def __init__(
        self,
        remote_url: str = "http://localhost:8000/remote_config.json",
        fallback_file: str = "remote_config.json",
        timeout_seconds: float = 0.8,
    ):
        self.remote_url = remote_url
        self.fallback_file = fallback_file
        self.timeout_seconds = timeout_seconds

        self.config_data: Dict[str, Any] = dict(self.DEFAULT_CONFIG)
        self.source: str = "default"
        self.is_loaded: bool = False
        self.last_error: Optional[str] = None

    def fetch_config(self) -> Dict[str, Any]:
        """
        Obtiene la configuración remota.
        Intenta primero consultar el endpoint remoto vía HTTP. Si falla o no está disponible,
        hace fallback automático al archivo local JSON sin interrumpir la experiencia de usuario.
        """
        # 1. Intentar descargar desde endpoint remoto
        try:
            req = urllib.request.Request(
                self.remote_url,
                headers={"User-Agent": "DespensAPP-KivyClient/1.0"},
            )
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                if response.status == 200:
                    raw_data = response.read().decode("utf-8")
                    parsed_json = json.loads(raw_data)
                    self.config_data = parsed_json
                    self.source = "network_remote"
                    self.is_loaded = True
                    self.last_error = None
                    return self.config_data
        except Exception as exc:
            self.last_error = f"Remote fetch failed: {str(exc)}"

        # 2. Fallback a archivo local JSON
        if os.path.exists(self.fallback_file):
            try:
                with open(self.fallback_file, "r", encoding="utf-8") as f:
                    self.config_data = json.load(f)
                    self.source = "local_json_file"
                    self.is_loaded = True
                    return self.config_data
            except Exception as file_exc:
                self.last_error = f"Local file read failed: {str(file_exc)}"

        # 3. Fallback a configuración por defecto en memoria
        self.config_data = dict(self.DEFAULT_CONFIG)
        self.source = "memory_default"
        self.is_loaded = True
        return self.config_data

    def reload(self) -> Dict[str, Any]:
        """Fuerza la recarga de la configuración."""
        return self.fetch_config()

    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor del diccionario de configuración."""
        return self.config_data.get(key, default)

    def is_banner_enabled(self) -> bool:
        """Verifica si el banner informativo está activo en la configuración."""
        banner = self.config_data.get("banner", {})
        return bool(banner.get("enabled", False))

    def get_banner_info(self) -> Dict[str, str]:
        """Retorna los datos consolidados del banner remoto."""
        banner = self.config_data.get("banner", {})
        return {
            "title": str(banner.get("title", "Aviso")),
            "message": str(banner.get("message", "")),
            "type": str(banner.get("type", "info")),
            "badge_text": str(banner.get("badge_text", "REMOTO")),
        }

    def is_feature_enabled(self, feature_name: str, default: bool = True) -> bool:
        """Comprueba si un módulo o función específica está habilitado remotamente."""
        features = self.config_data.get("features", {})
        return bool(features.get(feature_name, default))

    def is_maintenance_mode(self) -> bool:
        """Determina si la aplicación debe presentarse en modo de mantenimiento."""
        return bool(self.config_data.get("maintenance_mode", False))
