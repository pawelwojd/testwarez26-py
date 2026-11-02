"""Data checks for different types (classes) of starships.

Each TestCase groups one type of ship, so the report shows results per type.
"""

import unittest

from swapi_tests.client import client, parse_number


class StarshipTypeTestCase(unittest.TestCase):
    """Base class: fetch a ship by ID and provide shared assertions."""

    def get_ship(self, ship_id: int) -> dict:
        resp = client.starship(ship_id)
        self.assertEqual(resp.status, 200, f"starships/{ship_id}/ returned HTTP {resp.status}")
        return resp.body

    def assertShip(self, ship_id: int, *, name: str, model: str, starship_class: str, manufacturer: str):
        ship = self.get_ship(ship_id)
        self.assertEqual(ship["name"], name)
        self.assertEqual(ship["model"], model)
        self.assertEqual(ship["starship_class"].lower(), starship_class.lower())
        self.assertIn(manufacturer, ship["manufacturer"])
        return ship


class TestStarfighters(StarshipTypeTestCase):
    def test_x_wing(self):
        ship = self.assertShip(12, name="X-wing", model="T-65 X-wing",
                               starship_class="Starfighter", manufacturer="Incom Corporation")
        self.assertEqual(ship["hyperdrive_rating"], "1.0")
        self.assertEqual(ship["MGLT"], "100")

    def test_tie_advanced_x1(self):
        ship = self.assertShip(13, name="TIE Advanced x1", model="Twin Ion Engine Advanced x1",
                               starship_class="Starfighter", manufacturer="Sienar Fleet Systems")
        self.assertEqual(ship["cost_in_credits"], "unknown")

    def test_y_wing_is_assault_starfighter(self):
        self.assertShip(11, name="Y-wing", model="BTL Y-wing",
                        starship_class="assault starfighter", manufacturer="Koensayr Manufacturing")

    def test_starfighters_are_small_crewed_and_carry_no_passengers(self):
        fighters = [s for s in client.iter_starships() if "starfighter" in s["starship_class"].lower()]
        self.assertGreaterEqual(len(fighters), 5)
        for ship in fighters:
            with self.subTest(ship=ship["name"]):
                self.assertLessEqual(parse_number(ship["crew"]), 3)
                self.assertIn(parse_number(ship["passengers"]), (0, None))
                self.assertLess(parse_number(ship["length"]), 30)


class TestFreighters(StarshipTypeTestCase):
    def test_millennium_falcon(self):
        ship = self.assertShip(10, name="Millennium Falcon", model="YT-1300 light freighter",
                               starship_class="Light freighter",
                               manufacturer="Corellian Engineering Corporation")
        self.assertEqual(parse_number(ship["crew"]), 4)
        self.assertEqual(parse_number(ship["passengers"]), 6)

    def test_millennium_falcon_has_fastest_hyperdrive(self):
        ratings = {s["name"]: parse_number(s["hyperdrive_rating"]) for s in client.iter_starships()}
        known = {name: r for name, r in ratings.items() if r is not None}
        fastest = min(known.values())  # lower rating == faster
        self.assertEqual(known["Millennium Falcon"], fastest)

    def test_millennium_falcon_has_known_pilots(self):
        ship = self.get_ship(10)
        self.assertGreaterEqual(len(ship["pilots"]), 2, "Han and Chewbacca should be listed")


class TestCapitalShips(StarshipTypeTestCase):
    def test_cr90_corvette(self):
        ship = self.assertShip(2, name="CR90 corvette", model="CR90 corvette",
                               starship_class="corvette",
                               manufacturer="Corellian Engineering Corporation")
        self.assertEqual(ship["crew"], "30-165")  # range values are preserved as strings

    def test_star_destroyer(self):
        ship = self.assertShip(3, name="Star Destroyer", model="Imperial I-class Star Destroyer",
                               starship_class="Star Destroyer", manufacturer="Kuat Drive Yards")
        self.assertEqual(parse_number(ship["length"]), 1600)
        self.assertEqual(ship["passengers"], "n/a")

    def test_executor_star_dreadnought(self):
        ship = self.assertShip(15, name="Executor", model="Executor-class star dreadnought",
                               starship_class="Star dreadnought", manufacturer="Kuat Drive Yards")
        self.assertGreater(parse_number(ship["crew"]), 250_000)

    def test_capital_ships_outsize_starfighters(self):
        smallest_capital = min(parse_number(self.get_ship(i)["length"]) for i in (2, 3, 15))
        largest_fighter = max(parse_number(self.get_ship(i)["length"]) for i in (11, 12, 13))
        self.assertGreater(smallest_capital, largest_fighter * 10)


class TestBattlestations(StarshipTypeTestCase):
    def test_death_star(self):
        ship = self.assertShip(9, name="Death Star", model="DS-1 Orbital Battle Station",
                               starship_class="Deep Space Mobile Battlestation",
                               manufacturer="Imperial Department of Military Research")
        self.assertEqual(ship["cost_in_credits"], "1000000000000")
        self.assertEqual(ship["max_atmosphering_speed"], "n/a")

    def test_death_star_is_the_largest_ship(self):
        lengths = {s["name"]: parse_number(s["length"]) for s in client.iter_starships()}
        largest = max((n for n in lengths if lengths[n] is not None), key=lengths.get)
        self.assertEqual(largest, "Death Star")

    def test_death_star_is_the_most_expensive_ship(self):
        costs = {s["name"]: parse_number(s["cost_in_credits"]) for s in client.iter_starships()}
        priciest = max((n for n in costs if costs[n] is not None), key=costs.get)
        self.assertEqual(priciest, "Death Star")


if __name__ == "__main__":
    unittest.main()
