# -*- coding: utf-8 -*-
"""Pruebas de las preferencias del dispositivo (modo oscuro persistente)."""

import os
import tempfile
import unittest

import controllers.preferences as prefs


class PreferencesTests(unittest.TestCase):
    def setUp(self):
        self._orig = prefs.PREFS_PATH
        self._dir = tempfile.TemporaryDirectory()
        prefs.PREFS_PATH = os.path.join(self._dir.name, "user_prefs.json")

    def tearDown(self):
        prefs.PREFS_PATH = self._orig
        self._dir.cleanup()

    def test_default_is_light(self):
        self.assertFalse(prefs.is_dark_mode())

    def test_dark_mode_persists(self):
        prefs.set_dark_mode(True)
        self.assertTrue(prefs.is_dark_mode())
        prefs.set_dark_mode(False)
        self.assertFalse(prefs.is_dark_mode())

    def test_keeps_other_preferences(self):
        prefs.save_preference("otra", 1)
        prefs.set_dark_mode(True)
        self.assertEqual(prefs.load_preferences(), {"otra": 1, "dark_mode": True})

    def test_corrupt_file_falls_back_to_light(self):
        with open(prefs.PREFS_PATH, "w", encoding="utf-8") as f:
            f.write("{no es json")
        self.assertFalse(prefs.is_dark_mode())


if __name__ == "__main__":
    unittest.main()
