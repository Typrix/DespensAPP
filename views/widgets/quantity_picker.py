# -*- coding: utf-8 -*-
"""
Selector compacto de cantidad y medida (QuantityPicker).
Una fila de medidas (un., kg, g, L...), el número con − y + (se puede escribir)
y atajos de cantidad. La lógica vive en controllers.unit_selector.
"""

from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

from controllers.unit_selector import (
    clamp_quantity,
    convert_quantity,
    format_amount,
    parse_typed_quantity,
    quick_amounts,
    step_for,
    unit_options,
)
from controllers.validators import format_number


class UnitChip(ButtonBehavior, Label):
    """Píldora seleccionable de medida o de atajo de cantidad."""
    is_active = BooleanProperty(False)
    value = StringProperty("")


class UnitChipRow(ScrollView):
    """Fila deslizable de medidas (un., kg, g, L...). Emite on_select(unit) al tocar una."""
    unit = StringProperty("un.")
    __events__ = ("on_select",)

    def on_kv_post(self, base_widget):
        box = self.ids.units_box
        box.clear_widgets()
        for unit in unit_options():
            chip = UnitChip(text=unit, value=unit, is_active=(unit == self.unit))
            chip.bind(on_release=lambda c: self.dispatch("on_select", c.value))
            box.add_widget(chip)

    def on_unit(self, *_):
        if "units_box" in self.ids:
            for chip in self.ids.units_box.children:
                chip.is_active = chip.value == self.unit

    def on_select(self, unit):
        """Evento: el usuario tocó una medida."""


class QuantityPicker(BoxLayout):
    """Elige la medida y la cantidad. Emite on_change(quantity, unit) en cada cambio válido."""
    quantity = NumericProperty(1)
    unit = StringProperty("un.")
    show_units = BooleanProperty(True)
    integer_only = BooleanProperty(False)
    minimum = NumericProperty(0)
    error_text = StringProperty("")
    unit_label = StringProperty("un.")
    quantity_label = StringProperty("Cantidad")
    __events__ = ("on_change",)

    def __init__(self, **kwargs):
        self._syncing = False
        super().__init__(**kwargs)

    def on_kv_post(self, base_widget):
        self._build_quick()
        self._sync_text()

    # ------------------------------------------------------------------
    # Atajos de cantidad
    # ------------------------------------------------------------------
    def _build_quick(self):
        box = self.ids.quick_box
        box.clear_widgets()
        for amount in quick_amounts(self.unit, self.integer_only):
            text = format_number(amount) if self.integer_only else format_amount(amount, self.unit)
            chip = UnitChip(text=text, value=str(amount))
            chip.quick = True
            chip.bind(on_release=lambda c: self.set_quantity(float(c.value)))
            box.add_widget(chip)

    def on_unit(self, *_):
        self.unit_label = "" if self.integer_only else self.unit
        if "quick_box" in self.ids:
            self._build_quick()

    def on_integer_only(self, *_):
        self.on_unit()

    # ------------------------------------------------------------------
    # Acciones del usuario
    # ------------------------------------------------------------------
    def select_unit(self, unit):
        """Cambia la medida convirtiendo la cantidad cuando corresponde (1,5 kg -> 1500 g)."""
        if unit == self.unit:
            return
        new_qty = convert_quantity(self.quantity, self.unit, unit)
        self.unit = unit
        self.set_quantity(new_qty)

    def step_by(self, direction):
        """Suma o resta un paso según la medida (100 g, 0,5 kg, 1 un.)."""
        self.set_quantity(self.quantity + direction * step_for(self.unit, self.integer_only))

    def set_quantity(self, value):
        self.quantity = clamp_quantity(value, self.unit, self.integer_only, self.minimum)
        self.error_text = ""
        self._sync_text()
        self.dispatch("on_change", self.quantity, self.unit)

    def on_typed(self, text):
        """Valida lo escrito sin reescribir el campo mientras se escribe."""
        if self._syncing:
            return
        value, error = parse_typed_quantity(text, self.minimum)
        if error:
            self.error_text = error
            return
        self.error_text = ""
        self.quantity = clamp_quantity(value, self.unit, self.integer_only, self.minimum)
        self.dispatch("on_change", self.quantity, self.unit)

    def on_input_focus(self, focused):
        """Al salir del campo muestra el valor final (redondeado) si lo escrito era válido."""
        if not focused and not self.error_text:
            self._sync_text()

    def is_valid(self):
        """False si lo escrito tiene un error (para no guardar un valor distinto al que se ve)."""
        return not self.error_text

    def amount_text(self):
        return format_number(self.quantity) if self.integer_only else format_amount(self.quantity, self.unit)

    def _sync_text(self):
        if "qty_input" not in self.ids:
            return
        self._syncing = True
        self.ids.qty_input.text = format_number(self.quantity)
        self._syncing = False

    def on_change(self, quantity, unit):
        """Evento: la cantidad o la medida cambió."""
