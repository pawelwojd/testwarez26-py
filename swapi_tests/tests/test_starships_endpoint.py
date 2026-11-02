"""Generic contract tests for the /starships endpoint."""

import unittest

from swapi_tests.client import client

REQUIRED_FIELDS = {
    "name", "model", "manufacturer", "cost_in_credits", "length",
    "max_atmosphering_speed", "crew", "passengers", "cargo_capacity",
    "consumables", "hyperdrive_rating", "MGLT", "starship_class",
    "pilots", "films", "created", "edited", "url",
}


class TestStarshipsEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.first_page = client.starships_page(1)
        cls.all_ships = list(client.iter_starships())

    def test_list_returns_200(self):
        self.assertEqual(self.first_page.status, 200)

    def test_list_has_pagination_envelope(self):
        body = self.first_page.body
        for key in ("count", "next", "previous", "results"):
            self.assertIn(key, body)
        self.assertIsNone(body["previous"], "First page should have no previous link")
        self.assertLessEqual(len(body["results"]), 10, "Page size should be at most 10")

    def test_pagination_returns_every_ship_once(self):
        count = self.first_page.body["count"]
        self.assertEqual(len(self.all_ships), count)
        urls = [s["url"] for s in self.all_ships]
        self.assertEqual(len(urls), len(set(urls)), "Duplicate starships across pages")

    def test_every_ship_has_required_fields(self):
        for ship in self.all_ships:
            with self.subTest(ship=ship.get("name")):
                missing = REQUIRED_FIELDS - ship.keys()
                self.assertFalse(missing, f"Missing fields: {sorted(missing)}")

    def test_every_ship_has_a_class_and_appears_in_a_film(self):
        for ship in self.all_ships:
            with self.subTest(ship=ship["name"]):
                self.assertTrue(ship["starship_class"].strip())
                self.assertGreaterEqual(len(ship["films"]), 1)

    def test_unknown_starship_returns_404(self):
        self.assertEqual(client.starship(99999).status, 404)

    def test_non_starship_id_returns_404(self):
        # Starship IDs are not contiguous: ID 1 is unused (IDs are shared with /vehicles/).
        self.assertEqual(client.starship(1).status, 404)


if __name__ == "__main__":
    unittest.main()
