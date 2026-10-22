# -*- coding: utf-8 -*-
"""
Widget BottomNavButton para DespensAPP.
Botón de la barra de navegación inferior con píldora activa redondeada.
"""

from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import BooleanProperty, StringProperty


class BottomNavButton(ButtonBehavior, BoxLayout):
    """Botón de la barra de navegación inferior con píldora activa redondeada."""
    icon_name = StringProperty("home-outline")
    label_text = StringProperty("Inicio")
    screen_target = StringProperty("home")
    is_active = BooleanProperty(False)
