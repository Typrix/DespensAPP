# -*- coding: utf-8 -*-
"""
Hoja inferior compacta para registrar una cantidad y su medida.
Se abre al tocar una cantidad en la despensa, en una lista o al finalizar la compra.
"""

from kivy.clock import Clock
from kivy.properties import BooleanProperty, NumericProperty, StringProperty

from views.dialogs.base import BaseFormModal


class QuantitySheet(BaseFormModal):
    """Título, cantidad actual, selector de medida y cantidad, y botón Guardar."""
    title_text = StringProperty("")
    subtitle_text = StringProperty("")
    save_text = StringProperty("Guardar")
    show_units = BooleanProperty(True)
    integer_only = BooleanProperty(False)
    minimum = NumericProperty(0)

    def __init__(self, title, quantity, unit, on_save, subtitle="", show_units=True,
                 integer_only=False, minimum=0, save_label="Guardar", **kwargs):
        self._on_save = on_save
        self._save_label = save_label
        super().__init__(title_text=title, subtitle_text=subtitle, show_units=show_units,
                         integer_only=integer_only, minimum=minimum, **kwargs)
        picker = self.ids.picker
        picker.unit = unit or "un."
        picker.quantity = quantity
        picker._sync_text()
        picker.bind(on_change=lambda *_: self._refresh_save_text(), error_text=lambda *_: self._refresh_save_text())
        self._refresh_save_text()

    def _refresh_save_text(self):
        picker = self.ids.picker
        self.save_text = self._save_label if picker.error_text else f"{self._save_label} {picker.amount_text()}"

    def submit(self):
        """Guarda la cantidad y la medida; si lo escrito no es válido, deja el foco en el número."""
        picker = self.ids.picker
        if not picker.is_valid():
            Clock.schedule_once(lambda _dt: setattr(picker.ids.qty_input, "focus", True), 0)
            return
        if self._on_save:
            self._on_save(picker.quantity, picker.unit)
        self.dismiss()
