# -*- coding: utf-8 -*-
"""Pruebas del simulador del dashboard (base temporal en admin_dashboard, nunca la real)."""

import os
import sqlite3
import sys
import unittest
from datetime import datetime

ADMIN_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "admin_dashboard")
if ADMIN_DIR not in sys.path:
    sys.path.insert(0, ADMIN_DIR)

import metrics  # noqa: E402
import simulate  # noqa: E402

NOW = datetime(2026, 11, 18, 10, 0, 0)


class SimulatorTests(unittest.TestCase):
    PATH = os.path.join(ADMIN_DIR, "test_sim_tmp.db")

    def tearDown(self):
        if os.path.exists(self.PATH):
            os.remove(self.PATH)

    def test_refuses_real_database(self):
        with self.assertRaises(SystemExit):
            simulate.simulate(path=simulate.dbm.LOCAL_DB_PATH, users=1, days=2)

    def test_generates_only_android_and_ios(self):
        counts = simulate.simulate(path=self.PATH, users=12, days=20, seed=3, now=NOW)
        self.assertEqual(counts["users"], 12)
        conn = sqlite3.connect(self.PATH)
        platforms = {r[0] for r in conn.execute("SELECT DISTINCT platform FROM app_sessions")}
        conn.close()
        self.assertTrue(platforms and platforms <= {"Android", "iOS"}, platforms)
        data = metrics.collect(metrics.SqliteSource(self.PATH, "prueba"), days=7, now=NOW)
        self.assertTrue(data["available"])
        self.assertEqual(data["kpis"]["total_users"], 12)


if __name__ == "__main__":
    unittest.main()
