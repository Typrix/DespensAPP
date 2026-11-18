# -*- coding: utf-8 -*-
"""
Modal de Autenticación para DespensAPP.
Permite iniciar sesión, registrar nuevas cuentas de usuario y cambiar credenciales.
"""

from kivy.properties import BooleanProperty, StringProperty
from views.dialogs.base import BaseFormModal


class AuthModal(BaseFormModal):
    """Modal de autenticación (Inicio de sesión, Creación de cuenta y Edición de cuenta)."""
    is_login_mode = BooleanProperty(True)
    is_edit_profile_mode = BooleanProperty(False)
    can_cancel = BooleanProperty(False)
    can_submit = BooleanProperty(True)
    message_text = StringProperty("")
    is_error_message = BooleanProperty(False)

    # Palabras que identifican un mensaje de error (rojo); el resto se muestra en azul
    ERROR_HINTS = (
        "error",
        "incorrect",
        "campo",
        "requerid",
        "conexión",
        "modo local",
        "completa",
        "vacío",
        "válido",
        "uso",
        "al menos",
        "no se pudo",
        "no coinciden",
    )

    def on_message_text(self, instance, value):
        """Recalcula el color del mensaje (en KV, message_text.lower() no se reevalúa)."""
        text = (value or "").lower()
        self.is_error_message = any(hint in text for hint in self.ERROR_HINTS)

    def __init__(self, auth_manager, callback_success, can_cancel=False, edit_profile=False, **kwargs):
        super().__init__(**kwargs)
        self.auth_manager = auth_manager
        self.callback_success = callback_success
        self.can_cancel = can_cancel
        self.auto_dismiss = can_cancel
        self._initial_name = ""
        self._initial_email = ""
        self.is_edit_profile_mode = bool(edit_profile and auth_manager and auth_manager.current_user)
        if self.is_edit_profile_mode:
            user = auth_manager.current_user
            self._initial_name = (user.name or "").strip()
            self._initial_email = (user.email or "").strip().lower()
            self.ids.field_auth_name.text = self._initial_name
            self.ids.field_auth_email.ids.text_input.text = self._initial_email
            self.ids.field_auth_password.text = ""
            if "field_auth_password_confirm" in self.ids:
                self.ids.field_auth_password_confirm.text = ""
            self.can_submit = False
            self.ids.field_auth_name.bind(text=self._on_profile_field_change)
            self.ids.field_auth_email.ids.text_input.bind(text=self._on_profile_field_change)
            self.ids.field_auth_password.bind(text=self._on_profile_field_change)
            if "field_auth_password_confirm" in self.ids:
                self.ids.field_auth_password_confirm.bind(text=self._on_profile_field_change)
        else:
            self.can_submit = True

    def _on_profile_field_change(self, *args):
        """Habilita el botón de guardar solo cuando existe algún cambio en los datos del perfil."""
        if not self.is_edit_profile_mode:
            self.can_submit = True
            return
        if self.message_text:
            self.message_text = ""
        cur_name = self.ids.field_auth_name.text.strip()
        cur_email = self.ids.field_auth_email.ids.text_input.text.strip().lower()
        cur_pass = self.ids.field_auth_password.text.strip()
        cur_confirm = (
            self.ids.field_auth_password_confirm.text.strip()
            if "field_auth_password_confirm" in self.ids
            else ""
        )
        name_changed = bool(cur_name and cur_name != self._initial_name)
        email_changed = bool(cur_email and cur_email != self._initial_email)
        pass_touched = bool(cur_pass or cur_confirm)
        if pass_touched:
            self.can_submit = bool(cur_name and cur_email and cur_pass and cur_confirm)
        else:
            self.can_submit = bool(cur_name and cur_email and (name_changed or email_changed))

    def set_mode(self, is_login: bool):
        """Alterna entre modo Iniciar Sesión y modo Registrarse."""
        if self.is_edit_profile_mode:
            return
        self.is_login_mode = is_login
        if not is_login and hasattr(self.auth_manager, "db") and not self.auth_manager.db.is_mysql:
            self.message_text = "Modo Local: El registro de nuevas cuentas requiere conexión a la base central."
        else:
            self.message_text = ""

    def submit(self):
        """Procesa el envío del formulario de login, registro o edición de cuenta."""
        email = self.ids.field_auth_email.ids.text_input.text.strip()
        password = self.ids.field_auth_password.text.strip()

        if self.is_edit_profile_mode:
            if not self.can_submit:
                return
            name = self.ids.field_auth_name.text.strip()
            confirm_pass = (
                self.ids.field_auth_password_confirm.text.strip()
                if "field_auth_password_confirm" in self.ids
                else ""
            )
            if not name or not email:
                self.message_text = "Completa tu nombre y correo electrónico."
                return
            if password or confirm_pass:
                if password != confirm_pass:
                    self.message_text = "Las contraseñas no coinciden."
                    return
            success, msg = self.auth_manager.update_profile(name, email, password)
            self.message_text = msg
            if success:
                if self.callback_success:
                    self.callback_success(self.auth_manager.current_user)
                self.dismiss()
            return

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
