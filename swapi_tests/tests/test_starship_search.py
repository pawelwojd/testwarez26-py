"""Tests for the ?search= filter on /starships."""

import unittest

from swapi_tests.client import client


class TestStarshipSearch(unittest.TestCase):
    def test_search_wing_returns_all_wing_fighters(self):
        body = client.search_starships("wing").body
        names = {s["name"] for s in body["results"]}
        self.assertTrue({"X-wing", "Y-wing", "A-wing", "B-wing"} <= names, names)
        self.assertEqual(body["count"], len(body["results"]))

    def test_search_is_case_insensitive(self):
        lower = client.search_starships("death").body["results"]
        upper = client.search_starships("DEATH").body["results"]
        self.assertEqual([s["url"] for s in lower], [s["url"] for s in upper])
        self.assertIn("Death Star", {s["name"] for s in lower})

    def test_search_matches_model_field(self):
        # "YT-1300" only appears in the model, not the name.
        names = {s["name"] for s in client.search_starships("YT-1300").body["results"]}
        self.assertIn("Millennium Falcon", names)

    def test_search_with_no_match_returns_empty_list(self):
        body = client.search_starships("definitely-not-a-ship").body
        self.assertEqual(body["count"], 0)
        self.assertEqual(body["results"], [])


if __name__ == "__main__":
    unittest.main()
