# -*- coding: utf-8 -*-
"""
Widget de Banner de Configuración Remota (RemoteConfigBanner) para DespensAPP.
Muestra avisos dinámicos, promociones o alertas cargadas desde un JSON remoto o local.
"""

from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, BooleanProperty


class RemoteConfigBanner(ButtonBehavior, BoxLayout):
    """
    Banner interactivo que refleja datos de la configuración remota (Remote Config).
    Permite refrescar la configuración al ser pulsado.
    """
    title = StringProperty("Configuración Remota")
    message = StringProperty("")
    badge_text = StringProperty("REMOTO")
    banner_type = StringProperty("promo")
    is_active = BooleanProperty(False)
