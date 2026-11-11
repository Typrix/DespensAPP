# -*- coding: utf-8 -*-
"""
Modal "Historial de compras" para DespensAPP.
Muestra todas las compras finalizadas del periodo (semana, mes o año), la más reciente primero.
"""

from kivy.properties import NumericProperty, StringProperty

from views.dialogs.base import BaseFormModal
from views.widgets.empty_state import EmptyState
from views.widgets.purchase_row import build_purchase_card


class PurchaseHistoryModal(BaseFormModal):
    """Historial completo del periodo, abierto con "Ver todas" o desde Inicio."""
    period_label = StringProperty("")
    summary = StringProperty("")
    group_count = NumericProperty(0)

    def __init__(self, spending, **kwargs):
        """spending: resultado de PurchaseController.get_spending (label, total_str, groups)."""
        super().__init__(**kwargs)
        groups = spending.get("groups", [])
        self.group_count = len(groups)
        self.period_label = spending.get("label", "")
        n = len(groups)
        self.summary = (f"{self.period_label} · {n} {'compra' if n == 1 else 'compras'} · "
                        f"{spending.get('total_str', '$0')}")
        box = self.ids.history_box
        if not groups:
            box.add_widget(EmptyState(
                icon="receipt-text-outline",
                title="Sin compras en este periodo",
                message="Cuando finalices una compra desde una lista, aparecerá aquí.",
            ))
            return
        for group in groups:
            box.add_widget(build_purchase_card(group, in_modal=True))
