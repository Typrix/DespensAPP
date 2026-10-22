# -*- coding: utf-8 -*-
"""
Widget CustomProgressBar para DespensAPP.
Barra de progreso moderna con bordes redondeados y colores configurables.
"""

from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ListProperty
from kivy.graphics import Color, RoundedRectangle


class CustomProgressBar(Widget):
    """Barra de progreso moderna con bordes redondeados y colores configurables."""
    value = NumericProperty(0.5)
    track_color = ListProperty([0.890, 0.914, 0.945, 1])
    fill_color = ListProperty([0.157, 0.431, 0.831, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pos=self._update_canvas,
            size=self._update_canvas,
            value=self._update_canvas,
            track_color=self._update_canvas,
            fill_color=self._update_canvas,
        )

    def _update_canvas(self, *args):
        self.canvas.clear()
        with self.canvas:
            Color(rgba=self.track_color)
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[self.height / 2.0]
            )
            clamped_val = max(0.0, min(1.0, self.value))
            fill_width = self.width * clamped_val
            if fill_width > 0:
                Color(rgba=self.fill_color)
                RoundedRectangle(
                    pos=self.pos,
                    size=(fill_width, self.height),
                    radius=[self.height / 2.0]
                )
