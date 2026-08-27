"""Regression test ensuring exact deterministic behavior of the Sarah/Emma rescue scenario."""
import unittest
from scenarios.rescue_scenario import run_scenario


class TestScenarioRegression(unittest.TestCase):
    def test_scenario_deterministic_events(self):
        world = run_scenario()
        expected_events = [
            (1, "Mike told John Sarah was seen at house."),
            (2, "Sarah travels to the farm."),
            (3, "Zombie attack at house."),
            (3, "Emma lost sight of everyone and hid."),
            (4, "John tells Emma Sarah was seen at the farm."),
            (5, "Emma sets out for farm."),
            (6, "Emma found Sarah at farm!"),
            (6, "Mike falsely claims Sarah was seen in the forest."),
            (8, "Sarah told Emma Mike was seen at house."),
            (8, "John corrects the rumor: Sarah is at the farm."),
            (9, "John told Mike Emma was seen at house."),
        ]
        self.assertEqual(world.events.log, expected_events)


if __name__ == "__main__":
    unittest.main()
