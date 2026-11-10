# -*- coding: utf-8 -*-
"""
Aviso inferior "Elemento eliminado · Deshacer" para DespensAPP.
Barra propia (sin MDSnackbar: en KivyMD 2.0.0 su efecto ripple falla al crearse
con altura 0). Se muestra sobre la barra de navegación durante la ventana de gracia.
"""

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivymd.app import MDApp

_current_bar = None


class UndoBar(BoxLayout):
    """Barra flotante con mensaje y botón 'Deshacer' que se cierra sola."""

    def __init__(self, message, on_undo, duration, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint=(None, None),
            height=dp(52),
            padding=[dp(16), 0, dp(6), 0],
            spacing=dp(8),
            opacity=0,
            **kwargs,
        )
        self.on_undo = on_undo
        self.duration = duration
        self._close_event = None

        app = MDApp.get_running_app()
        dark = bool(app and app.modo_oscuro)
        # Colores invertidos respecto al tema activo para destacar sobre el fondo
        bg = list(app.text_primary_color) if app else [0.086, 0.149, 0.251, 1]
        fg = list(app.bg_color) if app else [1, 1, 1, 1]
        accent = [0.157, 0.431, 0.831, 1] if dark else [0.62, 0.78, 1.0, 1]

        with self.canvas.before:
            Color(0, 0, 0, 0.18)
            self._shadow = RoundedRectangle(radius=[dp(14)] * 4)
            Color(rgba=bg)
            self._bg = RoundedRectangle(radius=[dp(14)] * 4)
        self.bind(pos=self._update_canvas, size=self._update_canvas)

        self.add_widget(Label(
            text=message,
            font_size="13.5sp",
            color=fg,
            halign="left",
            valign="middle",
            shorten=True,
            shorten_from="right",
            text_size=(None, None),
        ))
        self.children[0].bind(size=lambda lbl, size: setattr(lbl, "text_size", size))

        if on_undo is None:
            # Aviso informativo: solo mensaje, sin botón
            self.padding = [dp(16), 0, dp(16), 0]
            Window.bind(size=self._reposition)
            self._reposition()
            return

        undo_btn = Button(
            text="Deshacer",
            bold=True,
            font_size="13.5sp",
            color=accent,
            background_color=[0, 0, 0, 0],
            background_normal="",
            size_hint_x=None,
            width=dp(92),
        )
        undo_btn.bind(on_release=self._handle_undo)
        self.add_widget(undo_btn)

        Window.bind(size=self._reposition)
        self._reposition()

    def _update_canvas(self, *args):
        self._shadow.pos = (self.x, self.y - dp(2))
        self._shadow.size = self.size
        self._bg.pos = self.pos
        self._bg.size = self.size

    def _reposition(self, *args):
        self.width = min(Window.width * 0.92, dp(420))
        self.x = (Window.width - self.width) / 2
        self.y = dp(76)

    def open(self):
        Window.add_widget(self)
        Animation(opacity=1, d=0.15).start(self)
        self._close_event = Clock.schedule_once(lambda dt: self.dismiss(), self.duration)

    def dismiss(self, *args):
        global _current_bar
        if self._close_event:
            self._close_event.cancel()
            self._close_event = None
        Window.unbind(size=self._reposition)
        if _current_bar is self:
            _current_bar = None
        anim = Animation(opacity=0, d=0.15)
        anim.bind(on_complete=lambda *a: Window.remove_widget(self))
        anim.start(self)

    def _handle_undo(self, *args):
        self.dismiss()
        if self.on_undo:
            self.on_undo()


def hide_undo_snackbar():
    """Cierra la barra visible (ej: al confirmar borrados pendientes por cierre de sesión)."""
    if _current_bar is not None:
        _current_bar.dismiss()


def show_info_toast(message, duration=3.0):
    """Muestra un aviso breve sin acción (ej: 'Compra registrada')."""
    return show_undo_snackbar(message, None, duration)


def show_undo_snackbar(message, on_undo, duration=4.0):
    """Muestra la barra de 'Deshacer'. Solo hay una visible: si se abre otra, la anterior se cierra."""
    global _current_bar
    if _current_bar is not None:
        _current_bar.dismiss()
    bar = UndoBar(message, on_undo, duration)
    bar.open()
    _current_bar = bar
    return bar
