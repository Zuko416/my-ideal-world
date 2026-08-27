"""Tests for 24-hour simulation clock and minute/hour/day rollover."""
import unittest
from npc_sim.simulation.clock import SimulationClock


class TestSimulationClock(unittest.TestCase):
    def test_clock_initialization(self):
        clock = SimulationClock(day=1, hour=8, minute=0)
        self.assertEqual(clock.day, 1)
        self.assertEqual(clock.hour, 8)
        self.assertEqual(clock.minute, 0)
        self.assertEqual(clock.time_string, "Day 1, 08:00")
        self.assertFalse(clock.is_night)

    def test_minute_advancement_and_hour_rollover(self):
        clock = SimulationClock(day=1, hour=8, minute=30)
        clock.tick(45)  # 08:30 + 45m = 09:15
        self.assertEqual(clock.day, 1)
        self.assertEqual(clock.hour, 9)
        self.assertEqual(clock.minute, 15)
        self.assertEqual(clock.time_string, "Day 1, 09:15")

    def test_midnight_day_rollover(self):
        clock = SimulationClock(day=1, hour=23, minute=0)
        clock.tick(120)  # +2 hours -> Day 2, 01:00
        self.assertEqual(clock.day, 2)
        self.assertEqual(clock.hour, 1)
        self.assertEqual(clock.minute, 0)
        self.assertTrue(clock.is_night)
        self.assertEqual(clock.time_string, "Day 2, 01:00")

    def test_multi_day_advance_to(self):
        clock = SimulationClock(day=1, hour=8, minute=0)
        clock.advance_to(day=3, hour=14, minute=30)
        self.assertEqual(clock.day, 3)
        self.assertEqual(clock.hour, 14)
        self.assertEqual(clock.minute, 30)
        self.assertEqual(clock.total_minutes, ((3 - 1) * 24 * 60) + (14 * 60) + 30)


if __name__ == "__main__":
    unittest.main()
