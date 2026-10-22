# -*- coding: utf-8 -*-
"""
Modal de Autenticación para DespensAPP.
Permite iniciar sesión, registrar nuevas cuentas de usuario y cambiar credenciales.
"""

from kivy.properties import BooleanProperty, StringProperty
from views.dialogs.base import BaseFormModal


class AuthModal(BaseFormModal):
    """Modal de autenticación (Inicio de sesión y Creación de cuenta)."""
    is_login_mode = BooleanProperty(True)
    can_cancel = BooleanProperty(False)
    message_text = StringProperty("")

    def __init__(self, auth_manager, callback_success, can_cancel=False, **kwargs):
        super().__init__(**kwargs)
        self.auth_manager = auth_manager
        self.callback_success = callback_success
        self.can_cancel = can_cancel
        self.auto_dismiss = can_cancel

    def set_mode(self, is_login: bool):
        """Alterna entre modo Iniciar Sesión y modo Registrarse."""
        self.is_login_mode = is_login
        if not is_login and hasattr(self.auth_manager, "db") and not self.auth_manager.db.is_mysql:
            self.message_text = "Modo Local: El registro de nuevas cuentas requiere conexión a la base central."
        else:
            self.message_text = ""

    def fill_demo(self):
        """Autocompleta los campos con la cuenta de Sofía Martínez."""
        self.set_mode(True)
        self.ids.field_auth_email.ids.text_input.text = "sofia@despensapp.com"
        self.ids.field_auth_password.text = "despensapp123"
        self.submit()

    def submit(self):
        """Procesa el envío del formulario de login o registro."""
        email = self.ids.field_auth_email.ids.text_input.text.strip()
        password = self.ids.field_auth_password.text.strip()

        if self.is_login_mode:
            if not email or not password:
                self.message_text = "Completa correo y contraseña"
                return
            success, msg = self.auth_manager.login(email, password)
            self.message_text = msg
            if success:
                if self.callback_success:
                    self.callback_success(self.auth_manager.current_user)
                self.dismiss()
        else:
            name = self.ids.field_auth_name.text.strip()
            if not name or not email or not password:
                self.message_text = "Todos los campos son requeridos"
                return
            success, msg = self.auth_manager.register(name, email, password)
            self.message_text = msg
            if success:
                if self.callback_success:
                    self.callback_success(self.auth_manager.current_user)
                self.dismiss()
