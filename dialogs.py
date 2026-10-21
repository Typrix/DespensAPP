# -*- coding: utf-8 -*-
"""
Controladores de Diálogos y Modales para DespensAPP.
Gestiona la captura de datos, validaciones y eventos de formulario para
carrito, despensa con fecha de caducidad, listas de supermercado interactivas
y autenticación de cuentas de usuario.
"""

from kivymd.app import MDApp
from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.properties import BooleanProperty, StringProperty, NumericProperty, ListProperty
from kivy.graphics import Color, Ellipse, Line
from kivy.lang import Builder


class BaseFormModal(ModalView):
    """Clase base para modales de formulario con cierre automático."""
    pass


class AddCartItemModal(BaseFormModal):
    """Modal para ingresar un nuevo producto al carrito de compras."""

    def __init__(self, callback_add, **kwargs):
        super().__init__(**kwargs)
        self.callback_add = callback_add

    def submit(self):
        title = self.ids.field_title.ids.text_input.text.strip()
        price_str = self.ids.field_price.ids.text_input.text.strip()
        subtitle = self.ids.field_subtitle.ids.text_input.text.strip() or "General"

        if not title:
            return

        try:
            price = float(price_str) if price_str else 0.0
        except ValueError:
            price = 0.0

        if self.callback_add:
            self.callback_add(title, price, subtitle)
        self.dismiss()


class AddPantryItemModal(BaseFormModal):
    """Modal para ingresar un producto a la despensa con umbral numérico y fecha de vencimiento."""
    has_no_expiration = BooleanProperty(False)

    def __init__(self, callback_add, **kwargs):
        super().__init__(**kwargs)
        self.callback_add = callback_add

    def toggle_no_expiration(self):
        """Alterna entre producto con fecha de vencimiento y producto no perecible."""
        self.has_no_expiration = not self.has_no_expiration
        if self.has_no_expiration:
            self.ids.field_expiration.input_text = ""
            self.ids.field_expiration.ids.text_input.text = ""
            self.ids.field_expiration.ids.text_input.disabled = True
            self.ids.field_expiration.hint_text = "No vence (producto no perecible)"
        else:
            self.ids.field_expiration.ids.text_input.disabled = False
            self.ids.field_expiration.hint_text = "AAAA-MM-DD (ej: 2026-11-20)"

    def submit(self):
        name = self.ids.field_name.ids.text_input.text.strip()
        quantity_str = self.ids.field_quantity.ids.text_input.text.strip()
        unit = self.ids.field_unit.ids.text_input.text.strip() or "un."
        thresh_str = self.ids.field_threshold.ids.text_input.text.strip()
        exp_date = None if self.has_no_expiration else self.ids.field_expiration.ids.text_input.text.strip()

        if not name:
            return

        try:
            quantity = float(quantity_str) if quantity_str else 1.0
        except ValueError:
            quantity = 1.0

        try:
            threshold = float(thresh_str) if thresh_str else 2.0
        except ValueError:
            threshold = 2.0

        if self.callback_add:
            self.callback_add(name, quantity, unit, threshold, exp_date)
        self.dismiss()


class EditItemModal(BaseFormModal):
    """Modal interactivo para editar el nombre de un producto o de una lista."""
    title_text = StringProperty("Editar")

    def __init__(self, title_text, initial_value, callback_save, **kwargs):
        super().__init__(**kwargs)
        self.title_text = title_text
        self.callback_save = callback_save
        self.ids.field_edit.input_text = initial_value
        self.ids.field_edit.ids.text_input.text = initial_value

    def submit(self):
        val = self.ids.field_edit.ids.text_input.text.strip()
        if self.callback_save and val:
            self.callback_save(val)
        self.dismiss()


class PantryItemDetailModal(BaseFormModal):
    """Modal flotante para ajustar stock numérico, fecha de caducidad o eliminar producto."""
    item_id = NumericProperty(0)
    item_name = StringProperty("")
    item_qty_str = StringProperty("")
    expiration_str = StringProperty("Sin vencimiento")
    raw_expiration = StringProperty("")

    def __init__(self, item_id, item_name, item_qty_str, expiration_str="", raw_expiration="", callback_change=None, callback_delete=None, callback_update_exp=None, **kwargs):
        super().__init__(**kwargs)
        self.item_id = item_id
        self.item_name = item_name
        self.item_qty_str = item_qty_str
        self.expiration_str = expiration_str or "Sin vencimiento"
        self.raw_expiration = raw_expiration or ""
        self.callback_change = callback_change
        self.callback_delete = callback_delete
        self.callback_update_exp = callback_update_exp

    def change_qty(self, delta):
        if self.callback_change:
            self.callback_change(self.item_id, delta)
        self.dismiss()

    def edit_expiration(self):
        def save_exp(new_date):
            clean_date = new_date.strip()
            if clean_date.lower() in ("no vence", "sin vencimiento", "", "none"):
                clean_date = None
            if self.callback_update_exp:
                self.callback_update_exp(self.item_id, clean_date)
            self.dismiss()

        init_val = self.raw_expiration if self.raw_expiration else ""
        modal = EditItemModal(
            title_text="Fecha de Vencimiento (AAAA-MM-DD o 'No vence')",
            initial_value=init_val,
            callback_save=save_exp
        )
        modal.open()

    def delete_item(self):
        if self.callback_delete:
            self.callback_delete(self.item_id)
        self.dismiss()


class ColorChipButton(Button):
    """Botón circular interactivo para seleccionar color de icono."""
    color_hex = StringProperty("#286ED3")
    is_selected = BooleanProperty(False)

    def __init__(self, color_hex, on_select, **kwargs):
        super().__init__(**kwargs)
        self.color_hex = color_hex
        self.on_select = on_select
        self.size_hint = (None, None)
        self.size = ("34dp", "34dp")
        self.background_color = [0, 0, 0, 0]
        self.bind(pos=self._update_canvas, size=self._update_canvas, is_selected=self._update_canvas)

    def _update_canvas(self, *args):
        self.canvas.before.clear()
        rgba = self._hex_to_rgba(self.color_hex)
        with self.canvas.before:
            Color(rgba=rgba)
            Ellipse(pos=self.pos, size=self.size)
            if self.is_selected:
                Color(rgba=[1, 1, 1, 1])
                Line(circle=(self.center_x, self.center_y, 14), width=1.8)
                Color(rgba=rgba)
                Line(circle=(self.center_x, self.center_y, 16), width=1.5)

    def on_release(self):
        if self.on_select:
            self.on_select(self.color_hex)

    @staticmethod
    def _hex_to_rgba(hex_str):
        h = hex_str.lstrip("#")
        return [int(h[0:2], 16)/255.0, int(h[2:4], 16)/255.0, int(h[4:6], 16)/255.0, 1.0]


class AddShoppingListModal(BaseFormModal):
    """Modal para crear una nueva lista de compras con color y productos iniciales opcionales."""
    COLOR_PALETTE = ["#286ED3", "#10B981", "#E05A6D", "#F59E0B", "#8B5CF6", "#06B6D4"]

    def __init__(self, callback_add, **kwargs):
        super().__init__(**kwargs)
        self.callback_add = callback_add
        self.selected_color = self.COLOR_PALETTE[0]
        self.chip_widgets = []
        self._build_color_chips()

    def _build_color_chips(self):
        container = self.ids.color_chips_box
        container.clear_widgets()
        for color_hex in self.COLOR_PALETTE:
            chip = ColorChipButton(
                color_hex=color_hex,
                on_select=self.set_color,
                is_selected=(color_hex == self.selected_color)
            )
            self.chip_widgets.append(chip)
            container.add_widget(chip)

    def set_color(self, color_hex):
        self.selected_color = color_hex
        for chip in self.chip_widgets:
            chip.is_selected = (chip.color_hex == color_hex)

    def submit(self):
        name = self.ids.field_name.ids.text_input.text.strip()
        initial_items = self.ids.field_initial_items.ids.text_input.text.strip()
        if not name:
            return
        if self.callback_add:
            self.callback_add(name, self.selected_color, initial_items)
        self.dismiss()


class ShoppingListItemRow(BoxLayout):
    """Fila de producto individual dentro de una lista de compras de supermercado."""
    item_id = NumericProperty(0)
    name = StringProperty("")
    is_checked = BooleanProperty(False)

    def __init__(self, item_id, name, is_checked, callback_toggle, callback_edit, callback_delete, **kwargs):
        super().__init__(**kwargs)
        self.item_id = item_id
        self.name = name
        self.is_checked = is_checked
        self.callback_toggle = callback_toggle
        self.callback_edit = callback_edit
        self.callback_delete = callback_delete

    def toggle(self):
        if self.callback_toggle:
            self.callback_toggle(self.item_id, not self.is_checked)

    def edit(self):
        if self.callback_edit:
            self.callback_edit(self.item_id, self.name)

    def delete(self):
        if self.callback_delete:
            self.callback_delete(self.item_id)


class ShoppingListDetailModal(BaseFormModal):
    """Modal de detalle de lista estilo supermercado en papel (productos anotados, tachado y edición)."""
    list_id = NumericProperty(0)
    list_name = StringProperty("")
    icon_color_rgba = ListProperty([0.157, 0.431, 0.831, 1.0])
    subtitle_info = StringProperty("0 productos")

    def __init__(self, list_id, list_name, icon_color_rgba, **kwargs):
        super().__init__(**kwargs)
        self.list_id = list_id
        self.list_name = list_name
        self.icon_color_rgba = icon_color_rgba
        self.load_items()

    def load_items(self):
        """Carga y renderiza todos los productos anotados en la lista."""
        app = MDApp.get_running_app()
        if not app or not app.db:
            return
        items = app.db.get_shopping_list_items(self.list_id)
        container = self.ids.items_list_box
        container.clear_widgets()

        checked_count = sum(1 for it in items if it.is_checked)
        self.subtitle_info = f"{len(items)} productos anotados · {checked_count} tachados"

        if not items:
            from kivy.uix.label import Label
            empty_lbl = Label(
                text="Lista vacía.\nAñade los productos que vas a comprar arriba.",
                font_size="13sp",
                color=app.text_secondary_color,
                halign="center",
                size_hint_y=None,
                height="80dp"
            )
            container.add_widget(empty_lbl)
            return

        for it in items:
            row = ShoppingListItemRow(
                item_id=it.id,
                name=it.name,
                is_checked=it.is_checked,
                callback_toggle=self.toggle_item,
                callback_edit=self.open_edit_item,
                callback_delete=self.delete_item
            )
            container.add_widget(row)

    def add_item(self):
        """Añade un nuevo producto a la lista (sin precios, como en papel)."""
        name = self.ids.new_item_input.text.strip()
        if not name:
            return
        app = MDApp.get_running_app()
        if app and app.db:
            app.db.add_shopping_list_item(self.list_id, name)
            if hasattr(app, "analytics") and app.analytics:
                app.analytics.track_event("add_shopping_list_item", metadata={"list_id": self.list_id, "name": name})
            self.ids.new_item_input.text = ""
            self.load_items()
            app.cargar_listas()

    def toggle_item(self, item_id, is_checked):
        """Tacha o desmarca un producto al comprarlo."""
        app = MDApp.get_running_app()
        if app and app.db:
            app.db.toggle_shopping_list_item(item_id, is_checked)
            self.load_items()
            app.cargar_listas()

    def open_edit_item(self, item_id, current_name):
        """Abre modal para corregir el nombre del producto."""
        def save_edit(new_name):
            app = MDApp.get_running_app()
            if app and app.db:
                app.db.update_shopping_list_item_name(item_id, new_name)
                self.load_items()
                app.cargar_listas()

        modal = EditItemModal(
            title_text="Editar Producto",
            initial_value=current_name,
            callback_save=save_edit
        )
        modal.open()

    def delete_item(self, item_id):
        """Elimina un producto individual de la lista."""
        app = MDApp.get_running_app()
        if app and app.db:
            app.db.delete_shopping_list_item(item_id)
            self.load_items()
            app.cargar_listas()

    def edit_list_name(self):
        """Abre modal para renombrar la lista."""
        def save_list_name(new_name):
            app = MDApp.get_running_app()
            if app and app.db:
                app.db.update_shopping_list_name(self.list_id, new_name)
                self.list_name = new_name
                app.cargar_listas()

        modal = EditItemModal(
            title_text="Editar Nombre de Lista",
            initial_value=self.list_name,
            callback_save=save_list_name
        )
        modal.open()

    def delete_this_list(self):
        """Elimina la lista completa."""
        app = MDApp.get_running_app()
        if app:
            app.eliminar_lista_compras(self.list_id)
            self.dismiss()


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


# Carga de estilos KV para diálogos (al final para que todas las clases estén en memoria)
Builder.load_file("dialogs.kv")
