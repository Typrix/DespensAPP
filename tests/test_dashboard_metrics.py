# -*- coding: utf-8 -*-
"""Pruebas de las métricas del dashboard (datos en memoria, nunca la base real)."""

import os
import sys
import unittest
from datetime import datetime

ADMIN_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "admin_dashboard")
if ADMIN_DIR not in sys.path:
    sys.path.insert(0, ADMIN_DIR)

import metrics  # noqa: E402

NOW = datetime(2026, 11, 18, 10, 0, 0)


def _rows():
    """Dos usuarios: el 1 vuelve al día siguiente, compra y es Pro; el 2 entra una sola vez."""
    return {
        "users": [
            {"id": 1, "is_pro": 1, "created_at": "2026-11-10 09:00:00"},
            {"id": 2, "is_pro": 0, "created_at": "2026-11-12 18:00:00"},
        ],
        "sessions": [
            {"id": 1, "user_id": 1, "platform": "Android", "start_time": "2026-11-10 09:00:00", "duration_seconds": 120},
            {"id": 2, "user_id": 1, "platform": "Android", "start_time": "2026-11-11 08:00:00", "duration_seconds": 300},
            {"id": 3, "user_id": 2, "platform": "iOS", "start_time": "2026-11-12 18:00:00", "duration_seconds": 60},
            # Hoy (día incompleto): no cuenta
            {"id": 4, "user_id": 2, "platform": "iOS", "start_time": "2026-11-18 08:00:00", "duration_seconds": 60},
        ],
        "events": [
            {"event_name": "add_shopping_list_item", "user_id": 1, "screen_name": "lists",
             "duration_seconds": 0, "created_at": "2026-11-11 08:01:00"},
            {"event_name": "finalize_purchase", "user_id": 1, "screen_name": "lists",
             "duration_seconds": 0, "created_at": "2026-11-11 08:03:00"},
            {"event_name": "screen_view", "user_id": 1, "screen_name": "lists",
             "duration_seconds": 240, "created_at": "2026-11-11 08:04:00"},
            {"event_name": "screen_view", "user_id": 2, "screen_name": "home",
             "duration_seconds": 60, "created_at": "2026-11-12 18:01:00"},
        ],
        "purchases": [
            {"user_id": 1, "price": 1000, "quantity": 2, "purchased_at": "2026-11-11 08:03:00"},
            {"user_id": 1, "price": 2500, "quantity": 1, "purchased_at": "2026-11-11 08:03:00"},
        ],
        "pantry": [
            {"user_id": 1, "quantity": 0, "min_threshold": 1},
            {"user_id": 1, "quantity": 3, "min_threshold": 1},
        ],
        "lists": [{"id": 1, "user_id": 1}],
    }


class ComputeTests(unittest.TestCase):
    def setUp(self):
        self.data = metrics.compute(_rows(), days=30, now=NOW)

    def test_period_uses_complete_days_only(self):
        self.assertEqual(self.data["period_end"], "2026-11-17")
        self.assertEqual(self.data["kpis"]["sessions"], 3)  # la sesión de hoy no entra
        self.assertEqual(len(self.data["daily"]), 30)
        self.assertEqual(self.data["daily"][-1]["date"], "2026-11-17")

    def test_users_and_pro(self):
        k = self.data["kpis"]
        self.assertEqual((k["total_users"], k["new_users"], k["pro_users"], k["pro_rate"]), (2, 2, 1, 50.0))

    def test_purchases_group_by_basket(self):
        k = self.data["kpis"]
        self.assertEqual((k["purchases"], k["buyers"], k["spend"]), (1, 1, 4500))
        self.assertEqual(k["avg_ticket_str"], "$4.500")

    def test_retention_day_one(self):
        d1 = self.data["retention"]["d1"]
        self.assertEqual((d1["returned"], d1["eligible"]), (1, 2))

    def test_funnel_and_screens(self):
        self.assertEqual([s["users"] for s in self.data["funnel"]], [2, 1, 1, 1])
        self.assertEqual(self.data["screens"][0]["label"], "Listas")
        self.assertEqual({p["platform"] for p in self.data["platforms"]}, {"Android", "iOS"})

    def test_pantry_facts(self):
        k = self.data["kpis"]
        self.assertEqual((k["pantry_per_user"], k["low_stock_share"], k["lists_per_user"]), (2.0, 50.0, 1.0))

    def test_private_metadata_is_removed(self):
        meta = metrics.safe_metadata('{"user_id": 3, "email": "a@b.cl", "list_id": 9}')
        self.assertEqual(meta, {"user_id": 3, "list_id": 9})


if __name__ == "__main__":
    unittest.main()
