# -*- coding: utf-8 -*-
"""Pruebas de la validación del correo."""

import unittest

from controllers.validators import validate_email


class EmailTests(unittest.TestCase):
    def test_valid_emails_are_normalized(self):
        self.assertEqual(validate_email("  Camila.Rojas+casa@Correo.CL "), ("camila.rojas+casa@correo.cl", ""))
        self.assertEqual(validate_email("ana@mail.uc.cl")[1], "")

    def test_invalid_emails(self):
        for raw in ["", "ana", "ana@", "@correo.cl", "ana@correo", "ana@correo.", "ana b@correo.cl",
                    "ana@@correo.cl", "ana..rojas@correo.cl", ".ana@correo.cl", "ana@-correo.cl", "ana@correo.c"]:
            with self.subTest(raw=raw):
                self.assertTrue(validate_email(raw)[1])


if __name__ == "__main__":
    unittest.main()
