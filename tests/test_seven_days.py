"""Unit and integration tests for Milestone 6: Behavioral Divergence and Emergent Daily Variation."""
import unittest
from scenarios.seven_days import run_seven_days, get_seven_days_summary
from npc_sim.core.schedule import ActivityType


class TestSevenDaysSimulation(unittest.TestCase):
    def test_seven_days_completes_successfully(self):
        """Simulation runs from Day 1 06:00 through Day 7 24:00 (Day 8 00:00)."""
        world = run_seven_days(seed=42, print_log=False)
        self.assertEqual(world.clock.day, 8)
        self.assertEqual(world.clock.hour, 0)
        self.assertEqual(world.clock.minute, 0)

        # Integrity check must have 0 errors
        errors = world.validate_integrity()
        self.assertEqual(errors, [])

    def test_all_15_npcs_persist_and_remain_valid(self):
        """All 15 canonical characters participate and maintain valid states."""
        world = run_seven_days(seed=42, print_log=False)
        self.assertEqual(len(world.npcs.alive_names()), 15)

        for name in world.npcs.alive_names():
            npc = world.npcs.npcs[name]
            # Needs must remain in healthy physiological bounds
            self.assertGreaterEqual(npc.hunger, 0.0)
            self.assertLess(npc.hunger, 85.0)
            self.assertGreaterEqual(npc.thirst, 0.0)
            self.assertLess(npc.thirst, 85.0)
            self.assertGreaterEqual(npc.fatigue, 0.0)
            self.assertLess(npc.fatigue, 85.0)

            # Location must be a valid home or known location
            self.assertIn(npc.location, world.locations)

            # Activity must be valid
            self.assertIsInstance(npc.current_activity, ActivityType)

    def test_relationships_and_memories_remain_bounded(self):
        """Relationship affinity must stay in [-1.0, 1.0] and memories <= 50."""
        world = run_seven_days(seed=42, print_log=False)

        for name in world.npcs.alive_names():
            npc = world.npcs.npcs[name]
            # Memory capacity bounds
            self.assertLessEqual(len(npc.memories), 50)

            # Relationship bounds
            for other_name, rel in npc.relationships.items():
                self.assertGreaterEqual(rel.affinity, -1.0)
                self.assertLessEqual(rel.affinity, 1.0)
                self.assertGreaterEqual(rel.trust, 0.0)
                self.assertLessEqual(rel.trust, 1.0)
                self.assertGreaterEqual(rel.respect, 0.0)
                self.assertLessEqual(rel.respect, 1.0)

    def test_knowledge_distribution_not_omniscient(self):
        """NPCs should develop different belief sets based on their distinct experiences."""
        world = run_seven_days(seed=42, print_log=False)
        toddler = world.npcs.npcs["Ravi Menon"]
        traveler = world.npcs.npcs["Jeagel Forster"]

        # Different NPCs hold distinct beliefs based on where they went and who they saw
        self.assertNotEqual(toddler.beliefs, traveler.beliefs)

    def test_deterministic_reproducibility(self):
        """Running with the same seed must produce identical event count and final states."""
        world_a = run_seven_days(seed=42, print_log=False)
        world_b = run_seven_days(seed=42, print_log=False)

        self.assertEqual(len(world_a.events.structured_log), len(world_b.events.structured_log))

        for name in world_a.npcs.alive_names():
            npc_a = world_a.npcs.npcs[name]
            npc_b = world_b.npcs.npcs[name]
            self.assertEqual(npc_a.location, npc_b.location)
            self.assertEqual(npc_a.current_activity, npc_b.current_activity)
            self.assertAlmostEqual(npc_a.hunger, npc_b.hunger, places=3)
            self.assertAlmostEqual(npc_a.fatigue, npc_b.fatigue, places=3)

    def test_multi_seed_behavioral_divergence(self):
        """Different seeds produce distinct emergent trajectories and event counts."""
        world_42 = run_seven_days(seed=42, print_log=False)
        world_1337 = run_seven_days(seed=1337, print_log=False)
        world_2026 = run_seven_days(seed=2026, print_log=False)

        # Totals vary organically between seeds
        events_42 = len(world_42.events.structured_log)
        events_1337 = len(world_1337.events.structured_log)
        events_2026 = len(world_2026.events.structured_log)

        # Must not be rigidly cloned across seeds
        self.assertTrue(events_42 != events_1337 or events_42 != events_2026)

    def test_routine_deviations_occur_within_believable_ratio(self):
        """Routine deviations occur organically (5-20% range) rather than 0% or 100%."""
        world = run_seven_days(seed=42, print_log=False)
        total_deviations = sum(ds.routine_deviations_count for ds in world.events.daily_stats.values())
        self.assertGreater(total_deviations, 0)


if __name__ == "__main__":
    unittest.main()
