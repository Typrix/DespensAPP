# -*- coding: utf-8 -*-
"""
Widget PantryItemRow para DespensAPP.
Fila de inventario de la despensa con alerta cromática y estado de vencimiento.
"""

from kivymd.app import MDApp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, NumericProperty, ListProperty


class PantryItemRow(ButtonBehavior, BoxLayout):
    """Fila de inventario de la despensa con alerta cromática y estado de vencimiento."""
    item_id = NumericProperty(0)
    name = StringProperty("")
    quantity_str = StringProperty("")
    status_str = StringProperty("Suficiente")
    status_color = ListProperty([0.18, 0.44, 0.25, 1.0])
    expiration_str = StringProperty("Sin vencimiento")
    expiration_color = ListProperty([0.5, 0.5, 0.5, 1.0])
    raw_expiration = StringProperty("")
    quantity_val = NumericProperty(0)
    unit = StringProperty("un.")

    def open_detail(self):
        """Abre la ventana modal de detalle para ajustar stock o caducidad."""
        app = MDApp.get_running_app()
        if app:
            from views.dialogs.pantry_dialog import PantryItemDetailModal
            modal = PantryItemDetailModal(
                item_id=self.item_id,
                item_name=self.name,
                quantity_val=self.quantity_val,
                unit=self.unit,
                expiration_str=self.expiration_str,
                raw_expiration=self.raw_expiration,
                callback_set_qty=app.fijar_cantidad_despensa,
                callback_finish=app.finalizar_ajuste_despensa,
                callback_delete=app.eliminar_item_despensa,
                callback_update_exp=getattr(app, "actualizar_vencimiento_despensa", None)
            )
            modal.open()
