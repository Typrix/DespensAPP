# -*- coding: utf-8 -*-
"""Pruebas de la lectura de precios en pesos chilenos."""

import unittest

from controllers.validators import parse_price, validate_cart_form


class ParsePriceTests(unittest.TestCase):
    def test_plain_and_thousands(self):
        self.assertEqual(parse_price("2000"), 2000)
        self.assertEqual(parse_price("2.000"), 2000)
        self.assertEqual(parse_price("$12.345.678"), 12345678)

    def test_extra_digit_after_formatted_price(self):
        # Al editar "2.000" y agregar un 0 queda "2.0000": debe ser 20.000, no 2
        self.assertEqual(parse_price("2.0000"), 20000)
        self.assertEqual(parse_price("20.00"), 2000)

    def test_comma_decimal(self):
        self.assertEqual(parse_price("1.500,5"), 1500.5)

    def test_invalid(self):
        for text in ("", "abc", "1,2,3", "$", "1,5a"):
            self.assertIsNone(parse_price(text), text)

    def test_cart_form_uses_price_rules(self):
        ok, _, data = validate_cart_form("Leche", "2.0000")
        self.assertTrue(ok)
        self.assertEqual(data["price"], 20000)


if __name__ == "__main__":
    unittest.main()
