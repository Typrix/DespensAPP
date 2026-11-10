# -*- coding: utf-8 -*-
"""
Modal de Alertas para DespensAPP.
Lista los productos vencidos, por vencer, por reponer o por agotarse; al tocar uno
se abre su detalle en la despensa.
"""

from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout

from views.dialogs.base import BaseFormModal
from views.widgets.empty_state import EmptyState


class AlertRow(ButtonBehavior, BoxLayout):
    """Fila tocable de una alerta (punto de color, producto y motivo)."""
    alert_title = StringProperty("")
    alert_desc = StringProperty("")
    alert_color = ListProperty([0.85, 0.20, 0.25, 1.0])


class AlertsModal(BaseFormModal):
    """Panel de alertas abierto desde la campana de Inicio."""
    alert_count = NumericProperty(0)

    def __init__(self, alerts, callback_open_item, **kwargs):
        """
        alerts: lista de dicts {item_id, title, desc, color} (MainController.get_alerts).
        callback_open_item(item_id): abre el detalle del producto.
        """
        super().__init__(**kwargs)
        self.callback_open_item = callback_open_item
        self.alert_count = len(alerts)
        box = self.ids.alerts_box
        if not alerts:
            box.add_widget(EmptyState(
                icon="check-circle-outline",
                title="Todo en orden",
                message="No hay productos vencidos ni por agotarse.",
            ))
            return
        for alert in alerts:
            row = AlertRow(
                alert_title=alert["title"],
                alert_desc=alert["desc"],
                alert_color=alert["color"],
            )
            row.bind(on_release=lambda inst, item_id=alert["item_id"]: self._open(item_id))
            box.add_widget(row)

    def _open(self, item_id):
        self.dismiss()
        if self.callback_open_item:
            self.callback_open_item(item_id)
