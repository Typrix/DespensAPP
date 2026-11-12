# -*- coding: utf-8 -*-
"""
Modal de Suscripción / Activación DespensAPP Pro.
Permite al usuario desbloquear las métricas avanzadas de Estadísticas ("6 meses" y "Año"),
activando is_pro = 1 en la base de datos.
"""

from kivy.properties import StringProperty

from views.dialogs.base import BaseFormModal

PERIOD_DISPLAY_NAMES = {
    "semester": "6 meses",
    "year": "Año",
}


class ProUpgradeModal(BaseFormModal):
    """Modal interactivo para adquirir y activar la versión Pro de DespensAPP."""
    target_period = StringProperty("")
    context_subtitle = StringProperty("")

    def __init__(self, target_period: str = "", callback_confirm=None, **kwargs):
        super().__init__(**kwargs)
        self.target_period = target_period or ""
        self.callback_confirm = callback_confirm
        period_name = PERIOD_DISPLAY_NAMES.get(self.target_period)
        if self.target_period == "lists":
            self.context_subtitle = (
                "La versión básica incluye 1 lista gratuita. "
                "Activa la versión Pro para crear todas las listas que necesites."
            )
        elif period_name:
            self.context_subtitle = (
                f"El filtro \"{period_name}\" es exclusivo de la versión Pro. "
                "Actívala para desbloquear tu historial de 6 meses y 1 año."
            )
        else:
            self.context_subtitle = (
                "Desbloquea listas ilimitadas y estadísticas de 6 meses y 1 año "
                "con un único pago."
            )

    def confirm_upgrade(self):
        """Ejecuta la activación de la versión Pro (is_pro = 1) y cierra el modal."""
        if self.callback_confirm:
            ok = self.callback_confirm(self.target_period)
            if ok is False:
                return
        self.dismiss()

