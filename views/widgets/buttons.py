# -*- coding: utf-8 -*-
"""
Botones Circulares Personalizados para DespensAPP.
Incluye el botón flotante de adición (+) y el botón de avatar con iniciales.
"""

from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.anchorlayout import AnchorLayout


class AddCircleButton(ButtonBehavior, AnchorLayout):
    """Botón circular con icono '+' perfectamente centrado."""
    pass


class AvatarCircleButton(ButtonBehavior, AnchorLayout):
    """Botón circular del avatar con texto centrado dinámico."""
    pass
