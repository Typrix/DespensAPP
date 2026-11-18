# -*- coding: utf-8 -*-
"""Pruebas de la lógica del selector de cantidad y medida (sin Kivy)."""

import unittest

from controllers.unit_selector import (
    clamp_quantity,
    convert_quantity,
    format_amount,
    parse_typed_quantity,
    quick_amounts,
    step_for,
    suggested_unit,
)


class ConvertQuantityTests(unittest.TestCase):
    def test_kg_to_g_and_back(self):
        self.assertEqual(convert_quantity(1.5, "kg", "g"), 1500)
        self.assertEqual(convert_quantity(750, "g", "kg"), 0.75)

    def test_l_to_ml(self):
        self.assertEqual(convert_quantity(2, "L", "ml"), 2000)

    def test_to_count_unit_rounds_to_at_least_one(self):
        self.assertEqual(convert_quantity(0.5, "kg", "un."), 1)
        self.assertEqual(convert_quantity(2.6, "L", "botella"), 3)

    def test_unrelated_units_keep_value(self):
        self.assertEqual(convert_quantity(3, "un.", "kg"), 3)
        self.assertEqual(convert_quantity(2, "kg", "L"), 2)


class ClampAndStepTests(unittest.TestCase):
    def test_count_units_are_integers(self):
        self.assertEqual(clamp_quantity(2.4, "un."), 2)

    def test_decimals_kept_for_weight(self):
        self.assertEqual(clamp_quantity(1.234, "kg"), 1.23)

    def test_limits(self):
        self.assertEqual(clamp_quantity(-3, "kg"), 0)
        self.assertEqual(clamp_quantity(0, "un.", integer_only=True, minimum=1), 1)
        self.assertEqual(clamp_quantity(10 ** 9, "g"), 100000)

    def test_steps(self):
        self.assertEqual(step_for("g"), 100)
        self.assertEqual(step_for("kg"), 0.5)
        self.assertEqual(step_for("kg", integer_only=True), 1)


class TextTests(unittest.TestCase):
    def test_parse_chilean_numbers(self):
        self.assertEqual(parse_typed_quantity("1,5"), (1.5, ""))
        self.assertEqual(parse_typed_quantity("1.500"), (1500, ""))

    def test_parse_errors(self):
        self.assertIsNone(parse_typed_quantity("")[0])
        self.assertEqual(parse_typed_quantity("0"), (0, ""))
        self.assertIsNone(parse_typed_quantity("0", minimum=1)[0])
        self.assertIsNone(parse_typed_quantity("abc")[0])

    def test_format_amount(self):
        self.assertEqual(format_amount(1.5, "kg"), "1,5 kg")
        self.assertEqual(format_amount(2, "un."), "2 un.")

    def test_quick_amounts_and_suggestions(self):
        self.assertEqual(quick_amounts("ml"), (250, 500, 1000))
        self.assertEqual(quick_amounts("kg", integer_only=True), (1, 2, 6))
        self.assertEqual(suggested_unit("Bebidas"), "L")
        self.assertEqual(suggested_unit("Lácteos"), "un.")
        self.assertEqual(suggested_unit("Limpieza"), "un.")


if __name__ == "__main__":
    unittest.main()
