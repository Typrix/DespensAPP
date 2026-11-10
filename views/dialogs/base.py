# -*- coding: utf-8 -*-
"""
Modales Base y de Edición para DespensAPP.
Proporciona la estructura común para ventanas modulares y edición de texto en línea.
"""

from kivy.uix.modalview import ModalView
from kivy.properties import StringProperty


class BaseFormModal(ModalView):
    """Clase base para modales de formulario con cierre automático y mensaje de error."""
    error_text = StringProperty("")

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
