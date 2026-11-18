# -*- coding: utf-8 -*-
"""
Modales Base y de Edición para DespensAPP.
Proporciona la estructura común para ventanas modulares y edición de texto en línea.
"""

from kivy.metrics import dp
from kivy.uix.modalview import ModalView
from kivy.properties import BooleanProperty, StringProperty

# Distancia que hay que arrastrar hacia abajo la hoja para cerrarla
SHEET_DRAG_CLOSE = dp(70)
# Zona superior de la hoja (con la barrita) desde donde se puede arrastrar
SHEET_HANDLE_ZONE = dp(44)


class BaseFormModal(ModalView):
    """Base de los formularios: se muestran como hoja inferior (bottom sheet) al estilo Android.

    La hoja ocupa el ancho de la pantalla (con un máximo en pantallas anchas), queda pegada abajo,
    sube con una animación corta y se cierra tocando afuera o arrastrando la barrita hacia abajo.
    """
    error_text = StringProperty("")
    as_sheet = BooleanProperty(True)

    def _align_center(self, *_args):
        """Ubica la hoja pegada al borde inferior; sin hoja, conserva el centrado de Kivy."""
        if not self._is_open:
            return
        if not self.as_sheet:
            super()._align_center()
            return
        win = self._window
        self.center_x = win.width / 2.0
        # Mientras se anima, la hoja sube desde un poco más abajo
        self.y = -self.height * 0.12 * (1.0 - self._anim_alpha) + getattr(self, "_drag_offset", 0)

    def open(self, *args, **kwargs):
        # ModalView.open centra la vista y la anima desde alpha 0 (sin cambio = sin reubicar):
        # sin esto el primer cuadro se dibuja en medio de la pantalla y luego salta abajo.
        super().open(*args, **kwargs)
        self._align_center()

    def on__anim_alpha(self, instance, value):
        super().on__anim_alpha(instance, value)
        if self.as_sheet:
            self._align_center()

    def on_touch_down(self, touch):
        self._drag_start = None
        if (self.as_sheet and self.auto_dismiss and self.collide_point(*touch.pos)
                and touch.y >= self.top - SHEET_HANDLE_ZONE):
            self._drag_start = touch.y
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if getattr(self, "_drag_start", None) is not None:
            self._drag_offset = min(0, touch.y - self._drag_start)
            self._align_center()
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        start = getattr(self, "_drag_start", None)
        if start is not None:
            self._drag_start = None
            offset = getattr(self, "_drag_offset", 0)
            self._drag_offset = 0
            if offset <= -SHEET_DRAG_CLOSE:
                self.dismiss()
                return True
            self._align_center()
        return super().on_touch_up(touch)

    def clear_error_on_input(self, *inputs):
        """Borra el mensaje de error apenas el usuario vuelve a escribir en alguno de los campos."""
        for text_input in inputs:
            text_input.bind(text=self._clear_error)

    def _clear_error(self, *args):
        self.error_text = ""


class EditItemModal(BaseFormModal):
    """Modal interactivo para editar el nombre de un producto o de una lista."""
    title_text = StringProperty("Editar")

    def __init__(self, title_text, initial_value, callback_save, **kwargs):
        super().__init__(**kwargs)
        self.title_text = title_text
        self.callback_save = callback_save
        self.ids.field_edit.input_text = initial_value
        self.ids.field_edit.ids.text_input.text = initial_value
        self.clear_error_on_input(self.ids.field_edit.ids.text_input)

    def submit(self):
        """Confirma y guarda el nuevo valor editado (no permite dejarlo vacío)."""
        val = self.ids.field_edit.ids.text_input.text.strip()
        if not val:
            self.error_text = "El nombre no puede quedar vacío."
            return
        if self.callback_save:
            self.callback_save(val)
        self.dismiss()
