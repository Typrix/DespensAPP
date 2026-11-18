# -*- coding: utf-8 -*-
"""
Modales de Despensa para DespensAPP.
Controla adición de alimentos, umbrales mínimos, control de caducidad y detalle.
"""

from dataclasses import replace

from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty, StringProperty, NumericProperty
from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.pickers import MDModalDatePicker
from views.dialogs.base import BaseFormModal
from controllers.pantry_organizer import (PANTRY_CATEGORIES, DEFAULT_CATEGORY, category_icon, category_of,
                                          category_tint)
from controllers.product_icons import product_icon, suggest_category
from controllers.validators import (
    PANTRY_UNITS,
    NAME_MAX_LENGTH,
    QUANTITY_MAX,
    validate_pantry_form,
    validate_pantry_details,
    expiration_warning,
    format_number,
    step_for_unit,
)
from controllers.unit_selector import suggested_unit

# Re-exportado para compatibilidad con código que lo importaba desde este módulo
__all__ = [
    "PANTRY_UNITS", "NAME_MAX_LENGTH", "QUANTITY_MAX", "validate_pantry_form",
    "AddPantryItemModal", "PantryItemDetailModal",
]


def _open_date_picker(on_date):
    """Abre el calendario de KivyMD y entrega la fecha elegida (AAAA-MM-DD) al callback."""
    date_picker = MDModalDatePicker()

    def on_ok(picker_instance):
        selected_dates = picker_instance.get_date()
        picker_instance.dismiss()
        if selected_dates:
            on_date(selected_dates[0].strftime("%Y-%m-%d"))

    def on_cancel(picker_instance):
        picker_instance.dismiss()

    date_picker.bind(on_ok=on_ok, on_cancel=on_cancel)
    date_picker.open()


def _category_menu(caller, on_pick):
    """Menú desplegable con las categorías del catálogo."""
    return MDDropdownMenu(
        caller=caller,
        items=[{"text": c, "leading_icon": category_icon(c), "on_release": lambda c=c: on_pick(c)}
               for c in PANTRY_CATEGORIES],
        position="bottom",
        width=max(caller.width, dp(180)),
        max_height=dp(260),
    )


class AddPantryItemModal(BaseFormModal):
    """Modal para ingresar un producto a la despensa con umbral numérico y fecha de vencimiento."""
    has_no_expiration = BooleanProperty(False)
    expiration_date_str = StringProperty("")
    selected_category = StringProperty(DEFAULT_CATEGORY)
    selected_category_icon = StringProperty(category_icon(DEFAULT_CATEGORY))
    warning_text = StringProperty("")

    def __init__(self, callback_add, **kwargs):
        super().__init__(**kwargs)
        self.callback_add = callback_add
        self.category_menu = None
        self._category_picked = False
        # La medida se sugiere según la categoría hasta que el usuario elige una
        self._unit_picked = False
        self._auto_unit = False
        self.ids.picker.bind(unit=self._on_unit_changed, on_change=lambda *_: setattr(self, "error_text", ""))
        self.ids.field_name.ids.text_input.bind(text=lambda inst, val: self._suggest_category(val))
        self.clear_error_on_input(
            self.ids.field_name.ids.text_input,
            self.ids.field_threshold.ids.text_input,
        )

    def _on_unit_changed(self, *_):
        if not self._auto_unit:
            self._unit_picked = True

    def on_dismiss(self):
        """Cierra el menú de categorías junto con el modal."""
        if self.category_menu:
            self.category_menu.dismiss()

    def open_category_menu(self, caller):
        """Despliega las categorías bajo el campo."""
        if self.category_menu is None:
            self.category_menu = _category_menu(caller, self.set_category)
        self.category_menu.open()

    def set_category(self, category, picked=True):
        """picked=False cuando la categoría viene de la sugerencia automática."""
        self._category_picked = self._category_picked or picked
        self.selected_category = category
        self.selected_category_icon = category_icon(category)
        if self.category_menu:
            self.category_menu.dismiss()
        if not self._unit_picked:
            self._auto_unit = True
            self.ids.picker.select_unit(suggested_unit(category))
            self._auto_unit = False

    def _suggest_category(self, name):
        """'Yogur' -> Lácteos; respeta la categoría si el usuario ya la eligió."""
        if not self._category_picked:
            self.set_category(suggest_category(name) or DEFAULT_CATEGORY, picked=False)

    def open_date_picker(self):
        """Abre el selector interactivo de fecha mediante calendario visual (MDModalDatePicker)."""
        if self.has_no_expiration:
            return

        def set_date(formatted_date):
            self.expiration_date_str = formatted_date
            self.error_text = ""
            self.warning_text = expiration_warning(formatted_date)

        _open_date_picker(set_date)

    def toggle_no_expiration(self):
        """Alterna entre producto con fecha de vencimiento y producto no perecible."""
        self.has_no_expiration = not self.has_no_expiration
        self.error_text = ""
        if self.has_no_expiration:
            self.expiration_date_str = ""
            self.warning_text = ""

    def submit(self):
        """Valida y registra el alimento en el inventario."""
        picker = self.ids.picker
        if not picker.is_valid():
            self.error_text = picker.error_text
            return
        ok, error, data = validate_pantry_form(
            name=self.ids.field_name.ids.text_input.text,
            quantity_str=format_number(picker.quantity),
            unit=picker.unit,
            threshold_str=self.ids.field_threshold.ids.text_input.text,
            expiration_str=self.expiration_date_str,
            has_no_expiration=self.has_no_expiration,
            category=self.selected_category,
        )
        if not ok:
            self.error_text = error
            return

        self.error_text = ""
        if self.callback_add:
            self.callback_add(data["name"], data["quantity"], data["unit"], data["threshold"],
                              data["expiration_date"], data["category"])
        self.dismiss()


RESTOCK_LABEL = "Añadir a una lista"


class PantryItemDetailModal(BaseFormModal):
    """
    Detalle de un producto de la despensa.
    - Vista: estado, stock con +/- (sin cerrar), cantidad exacta, aviso de mínimo,
      vencimiento claro, reponer al carrito y eliminar.
    - Edición (lápiz): nombre, unidad y mínimo de alerta en el mismo modal.
    La lista de la despensa se refresca una sola vez al cerrar.
    """
    item_id = NumericProperty(0)
    item_name = StringProperty("")
    quantity_val = NumericProperty(0)
    unit = StringProperty("un.")
    min_threshold = NumericProperty(0)
    step = NumericProperty(1)
    qty_display = StringProperty("")
    step_display = StringProperty("1")
    threshold_hint = StringProperty("")
    status_str = StringProperty("Suficiente")
    status_color = ListProperty([0.18, 0.44, 0.25, 1.0])
    status_text_color = ListProperty([0.18, 0.44, 0.25, 1.0])
    exp_title = StringProperty("")
    exp_desc = StringProperty("")
    exp_color = ListProperty([0.5, 0.5, 0.5, 1.0])
    has_expiration = BooleanProperty(False)
    needs_restock = BooleanProperty(False)
    restock_text = StringProperty(RESTOCK_LABEL)
    is_editing = BooleanProperty(False)
    edit_unit = StringProperty("un.")
    item_category = StringProperty(DEFAULT_CATEGORY)
    item_category_icon = StringProperty(category_icon(DEFAULT_CATEGORY))
    edit_category = StringProperty(DEFAULT_CATEGORY)
    edit_category_icon = StringProperty(category_icon(DEFAULT_CATEGORY))
    item_icon = StringProperty(category_icon(DEFAULT_CATEGORY))
    tint_light = ListProperty(category_tint(DEFAULT_CATEGORY))
    tint_dark = ListProperty(category_tint(DEFAULT_CATEGORY, dark=True))

    def __init__(self, item, callback_set_qty=None, callback_finish=None, callback_delete=None,
                 callback_update_exp=None, callback_add_to_list=None, callback_list_options=None,
                 callback_update_details=None, **kwargs):
        super().__init__(**kwargs)
        self.callback_set_qty = callback_set_qty
        self.callback_finish = callback_finish
        self.callback_delete = callback_delete
        self.callback_update_exp = callback_update_exp
        self.callback_add_to_list = callback_add_to_list
        self.callback_list_options = callback_list_options
        self._lists_menu = None
        self.callback_update_details = callback_update_details
        self._changed = False
        self._category_menu = None
        # Contenedores de vista y edición: se intercambian dentro de 'body'.
        # ids guarda referencias débiles: __self__ retiene el widget mientras está fuera del árbol.
        self._view_box = self.ids.view_box.__self__
        self._edit_box = self.ids.edit_box.__self__
        self.ids.body.remove_widget(self._edit_box)
        self.clear_error_on_input(
            self.ids.edit_name.ids.text_input,
            self.ids.edit_threshold.ids.text_input,
        )
        self._load(item)

    # ------------------------------------------------------------------
    # Estado mostrado
    # ------------------------------------------------------------------
    def _load(self, item):
        """Carga los datos del producto en el modal."""
        self.item = item
        self.item_id = item.id
        self.item_name = item.name
        self.unit = item.unit or "un."
        self.item_category = category_of(item)
        self.item_category_icon = category_icon(self.item_category)
        self.item_icon = product_icon(item.name, self.item_category)
        self.tint_light = category_tint(self.item_category)
        self.tint_dark = category_tint(self.item_category, dark=True)
        self.min_threshold = float(item.min_threshold)
        self.step = step_for_unit(self.unit)
        self.step_display = format_number(self.step)
        self.quantity_val = float(item.quantity)
        picker = self.ids.stock_picker
        picker.unit = self.unit
        picker.quantity = self.quantity_val
        picker._sync_text()
        self._refresh_status()
        self._refresh_expiration(item)

    def _refresh_status(self):
        """Recalcula estado, color, aviso de mínimo y botón de reponer según la cantidad actual."""
        current = replace(self.item, quantity=self.quantity_val, unit=self.unit, min_threshold=self.min_threshold)
        self.qty_display = f"{format_number(self.quantity_val)} {self.unit}"
        self.status_str = current.status
        self.status_color = current.status_text_color
        # En modo oscuro se aclara el texto de la píldora para mantener el contraste
        app = MDApp.get_running_app()
        if app and getattr(app, "modo_oscuro", False):
            self.status_text_color = [min(1.0, c * 0.5 + 0.5) for c in self.status_color[:3]] + [1.0]
        else:
            self.status_text_color = list(self.status_color)
        self.threshold_hint = f"Te avisamos cuando baje de {format_number(self.min_threshold)} {self.unit}"
        self.needs_restock = current.status in ("Reponer", "Por agotarse") and self.callback_add_to_list is not None

    def _refresh_expiration(self, item):
        """Arma el título y la descripción del vencimiento con su color."""
        days = item.days_until_expiration
        self.has_expiration = days is not None
        if days is None:
            self.exp_title = "Sin fecha de vencimiento"
            self.exp_desc = "Producto no perecible"
            self.exp_color = [0.45, 0.50, 0.58, 1.0]
            return
        self.exp_title = f"Vence el {item.formatted_expiration_date}"
        if days < 0:
            self.exp_desc = f"Venció hace {abs(days)} día(s)"
            self.exp_color = [0.85, 0.20, 0.25, 1.0]
        elif days == 0:
            self.exp_desc = "Vence hoy"
            self.exp_color = [0.85, 0.20, 0.25, 1.0]
        elif days <= 3:
            self.exp_desc = "Vence mañana" if days == 1 else f"Vence en {days} días"
            self.exp_color = [0.82, 0.48, 0.12, 1.0]
        else:
            self.exp_desc = f"Faltan {days} días"
            self.exp_color = [0.18, 0.55, 0.32, 1.0]

    # ------------------------------------------------------------------
    # Stock
    # ------------------------------------------------------------------
    def _apply_quantity(self, new_qty):
        """Guarda la nueva cantidad sin cerrar el modal."""
        new_qty = max(0.0, min(float(QUANTITY_MAX), round(new_qty, 3)))
        if new_qty == self.quantity_val:
            return
        self.quantity_val = new_qty
        self._changed = True
        self._refresh_status()
        if self.callback_set_qty:
            self.callback_set_qty(self.item_id, new_qty)

    def on_picker_change(self, quantity):
        """El selector de stock cambió (−, +, atajo o número escrito): se guarda al instante."""
        self._apply_quantity(quantity)

    def on_dismiss(self):
        """Al cerrar, refresca la despensa y evalúa alertas una sola vez."""
        for menu in (self._category_menu, self._lists_menu):
            if menu:
                menu.dismiss()
        if self._changed and self.callback_finish:
            self.callback_finish(self.item_id)
        self._changed = False

    # ------------------------------------------------------------------
    # Edición de nombre, unidad y mínimo
    # ------------------------------------------------------------------
    def start_edit(self):
        """Pasa al modo edición con los datos actuales."""
        self.error_text = ""
        self.ids.edit_name.ids.text_input.text = self.item_name
        self.ids.edit_threshold.ids.text_input.text = format_number(self.min_threshold)
        self.edit_unit = self.unit
        self._set_edit_category(self.item_category)
        self.ids.body.remove_widget(self._view_box)
        self.ids.body.add_widget(self._edit_box)
        self.is_editing = True

    def cancel_edit(self):
        """Vuelve a la vista sin guardar."""
        self.error_text = ""
        self.ids.body.remove_widget(self._edit_box)
        self.ids.body.add_widget(self._view_box)
        self.is_editing = False

    def _set_edit_unit(self, unit):
        self.edit_unit = unit
        self.error_text = ""

    def open_edit_category_menu(self, caller):
        if self._category_menu is None:
            self._category_menu = _category_menu(caller, self._set_edit_category)
        self._category_menu.open()

    def _set_edit_category(self, category):
        self.edit_category = category
        self.edit_category_icon = category_icon(category)
        if self._category_menu:
            self._category_menu.dismiss()

    def save_edit(self):
        """Valida y guarda nombre, unidad y mínimo; recarga el modal con los datos nuevos."""
        ok, error, data = validate_pantry_details(
            self.ids.edit_name.ids.text_input.text,
            self.edit_unit,
            self.ids.edit_threshold.ids.text_input.text,
            self.edit_category,
        )
        if not ok:
            self.error_text = error
            return
        updated = None
        if self.callback_update_details:
            updated = self.callback_update_details(self.item_id, data["name"], data["unit"],
                                                   data["threshold"], data["category"])
        if updated is not None:
            self._load(updated)
        self._changed = True
        self.cancel_edit()

    # ------------------------------------------------------------------
    # Vencimiento, reponer y eliminar
    # ------------------------------------------------------------------
    def add_to_list(self, caller):
        """Muestra las listas para anotar el producto (si no hay listas, crea 'Reponer despensa')."""
        if not self.callback_add_to_list:
            return
        options = self.callback_list_options() if self.callback_list_options else []
        if not options:
            self._add_to_list(None)
            return
        if self._lists_menu:
            self._lists_menu.dismiss()
        self._lists_menu = MDDropdownMenu(
            caller=caller,
            items=[{"text": name, "on_release": lambda lid=lid: self._add_to_list(lid)} for lid, name in options],
            position="top",
            width=caller.width,
            max_height=dp(220),
        )
        self._lists_menu.open()

    def _add_to_list(self, list_id):
        if self._lists_menu:
            self._lists_menu.dismiss()
        added, list_name = self.callback_add_to_list(self.item_id, list_id)
        self.restock_text = f"Anotado en {list_name}" if added else f"Ya estaba en {list_name}"

    def edit_expiration(self):
        """Abre el calendario para elegir o cambiar la fecha de vencimiento."""
        def set_date(formatted_date):
            if self.callback_update_exp:
                self.callback_update_exp(self.item_id, formatted_date)
            self._refresh_expiration(replace(self.item, expiration_date=formatted_date))
            self.item = replace(self.item, expiration_date=formatted_date)

        _open_date_picker(set_date)

    def clear_expiration(self):
        """Marca el producto como no perecible (sin fecha)."""
        if self.callback_update_exp:
            self.callback_update_exp(self.item_id, None)
        self.item = replace(self.item, expiration_date=None)
        self._refresh_expiration(self.item)

    def delete_item(self):
        """Elimina el producto de la despensa (con opción de deshacer)."""
        self._changed = False
        self.dismiss()
        if self.callback_delete:
            self.callback_delete(self.item_id, self.item_name)
