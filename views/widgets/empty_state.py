# -*- coding: utf-8 -*-
"""
Widget EmptyState para DespensAPP.
Mensaje guía con icono y botón de acción para pantallas o secciones sin datos.
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ObjectProperty


class EmptyState(BoxLayout):
    """Estado vacío: icono, título, descripción y un botón opcional."""
    icon = StringProperty("information-outline")
    title = StringProperty("")
    message = StringProperty("")
    action_text = StringProperty("")
    action = ObjectProperty(None, allownone=True)

    def run_action(self):
        if self.action:
            self.action()
