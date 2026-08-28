import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from rates import quote, haversine_miles, UnknownCityError, UnknownModeError


class RatesLogicTests(unittest.TestCase):
    def test_haversine_known_cities(self):
        d = haversine_miles("Orlando, FL", "Atlanta, GA")
        self.assertTrue(400 < d < 450, f"unexpected distance {d}")

    def test_haversine_unknown_city_raises(self):
        with self.assertRaises(UnknownCityError):
            haversine_miles("Nowhereville, ZZ", "Atlanta, GA")

    def test_quote_basic(self):
        q = quote("Orlando, FL", "Atlanta, GA", "Truck", 1200)
        self.assertIn("estimated_cost_usd", q)
        self.assertGreater(q["estimated_cost_usd"], 0)
        self.assertGreaterEqual(q["estimated_transit_days"], 1)

    def test_quote_unknown_mode_raises(self):
        with self.assertRaises(UnknownModeError):
            quote("Orlando, FL", "Atlanta, GA", "Teleport", 100)

    def test_quote_bad_weight_raises(self):
        with self.assertRaises(ValueError):
            quote("Orlando, FL", "Atlanta, GA", "Truck", -5)

    def test_ocean_slower_than_air(self):
        ocean = quote("Los Angeles, CA", "Seattle, WA", "Ocean", 1000)
        air = quote("Los Angeles, CA", "Seattle, WA", "Air", 1000)
        self.assertGreater(ocean["estimated_transit_days"], air["estimated_transit_days"])


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["status"], "ok")

    def test_meta(self):
        r = self.client.get("/api/meta")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertIn("Orlando, FL", body["cities"])
        self.assertIn("Truck", body["modes"])

    def test_quote_success(self):
        r = self.client.post("/api/quote", json={
            "origin": "Orlando, FL", "destination": "Atlanta, GA",
            "mode": "Truck", "weight_lbs": 1200,
        })
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body["mode"], "Truck")
        self.assertIn("estimated_delivery", body)

    def test_quote_missing_fields(self):
        r = self.client.post("/api/quote", json={"origin": "Orlando, FL"})
        self.assertEqual(r.status_code, 400)

    def test_quote_bad_city(self):
        r = self.client.post("/api/quote", json={
            "origin": "Nowhere, ZZ", "destination": "Atlanta, GA",
            "mode": "Truck", "weight_lbs": 500,
        })
        self.assertEqual(r.status_code, 422)

    def test_quote_bad_date_format(self):
        r = self.client.post("/api/quote", json={
            "origin": "Orlando, FL", "destination": "Atlanta, GA",
            "mode": "Truck", "weight_lbs": 500, "ship_date": "not-a-date",
        })
        self.assertEqual(r.status_code, 400)

    def test_docs_page_served(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Freight Rate", r.data)


if __name__ == "__main__":
    unittest.main()
