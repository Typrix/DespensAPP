# -*- coding: utf-8 -*-
"""Pruebas del orden de la lista y el resumen de compra."""

import unittest
from types import SimpleNamespace

from controllers.purchase_controller import PurchaseController, sort_by_creation
from controllers.unit_selector import clamp_quantity, to_stock_quantity
from models.shopping_list import ShoppingListItem


def _item(item_id, name, checked, qty=1.0, unit="un.", price=1000.0):
    return ShoppingListItem(id=item_id, list_id=1, name=name, is_checked=checked,
                            created_at="", price=price, quantity=qty, unit=unit)


class FakeDb:
    """Despensa mínima en memoria para build_checkout y finalize_purchase."""

    def __init__(self, pantry):
        self.pantry = pantry
        self.added, self.records, self.deleted = [], [], []

    def get_pantry_items(self, _uid):
        return self.pantry

    def set_pantry_quantity(self, item_id, qty):
        for p in self.pantry:
            if p.id == item_id:
                p.quantity = qty

    def add_pantry_item(self, *args):
        self.added.append(args)

    def add_purchase_record(self, *args, **kwargs):
        self.records.append(args)
        return len(self.records)

    def delete_shopping_list_item(self, item_id):
        self.deleted.append(item_id)


class ListOrderTests(unittest.TestCase):
    def test_checked_items_keep_their_place(self):
        # La API puede devolver los tachados al final: se vuelve al orden de creación
        api_order = [_item(1, "Pan", False), _item(3, "Huevos", False), _item(2, "Leche", True)]
        self.assertEqual([it.id for it in sort_by_creation(api_order)], [1, 2, 3])


class CheckoutTests(unittest.TestCase):
    def setUp(self):
        self.pantry = [SimpleNamespace(id=10, name="Arroz", quantity=1.0, unit="kg")]
        self.db = FakeDb(self.pantry)
        self.ctrl = PurchaseController(self.db)
        self.ctrl.find_pantry_match = lambda _uid, name: next(
            (p for p in self.pantry if p.name == name), None)

    def test_checkout_uses_list_quantity_and_unit(self):
        rows = self.ctrl.build_checkout(1, [
            _item(2, "Arroz", True, qty=500, unit="g", price=2),
            _item(1, "Leche", True, qty=2, unit="L", price=1200),
            _item(3, "Sal", False),
        ])
        self.assertEqual([r["title"] for r in rows], ["Leche", "Arroz"])
        arroz = rows[1]
        self.assertEqual((arroz["quantity"], arroz["unit"]), (500, "g"))
        self.assertEqual((arroz["stock_quantity"], arroz["stock_unit"]), (0.5, "kg"))

    def test_finalize_adds_converted_stock_and_list_total(self):
        rows = self.ctrl.build_checkout(1, [_item(2, "Arroz", True, qty=500, unit="g", price=2)])
        entries = [{"ref": r["ref"], "quantity": r["quantity"], "unit": r["unit"],
                    "stock_quantity": r["stock_quantity"]} for r in rows]
        summary = self.ctrl.finalize_purchase(1, 1, "Semanal", entries)
        self.assertEqual(self.pantry[0].quantity, 1.5)
        self.assertEqual(summary["total"], 1000)

    def test_stock_conversion_only_within_family(self):
        self.assertEqual(to_stock_quantity(250, "ml", "L"), 0.25)
        self.assertEqual(to_stock_quantity(2, "paquete", "kg"), 2.0)

    def test_count_unit_never_rounds_below_minimum(self):
        self.assertEqual(clamp_quantity(0.01, "un.", minimum=0.01), 1.0)
        self.assertEqual(clamp_quantity(0, "un.", minimum=0), 0.0)


if __name__ == "__main__":
    unittest.main()
