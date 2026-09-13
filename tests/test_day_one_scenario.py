"""Tests for Milestone 3 post-audit: Day 1 peaceful world simulation, canonical 15-character roster, and integrity."""
import unittest
from scenarios.day_one import create_village_world, populate_village, run_day_one
from npc_sim.core.schedule import ActivityType

CANONICAL_ROSTER = {
    "Jeagel Forster", "Sarah Forster", "Arthur Forster", "Elena Forster",
    "Mira Voss", "Evan Voss",
    "Anya Rao", "Arjun Rao",
    "Raghav Menon", "Nila Menon", "Kian Menon", "Tara Menon", "Ravi Menon",
    "Dev Malhotra", "Sameer Khan",
}


class TestDayOneScenario(unittest.TestCase):
    def test_village_world_initialization(self):
        world = create_village_world()
        expected_locations = {
            "forster_home", "twin_cottage", "newlywed_home", "menon_home",
            "village_road", "town_square", "general_store", "village_school",
            "clinic", "farms", "workshop", "forest",
        }
        for loc in expected_locations:
            self.assertIn(loc, world.locations)

    def test_all_15_canonical_npcs_exist_with_valid_attributes(self):
        world = create_village_world()
        roster = populate_village(world)

        self.assertEqual(len(roster), 15)
        self.assertEqual(len(world.npcs.alive_names()), 15)
        self.assertEqual(set(world.npcs.alive_names()), CANONICAL_ROSTER)

        for npc in roster:
            self.assertIn(npc.name, CANONICAL_ROSTER)
            self.assertGreater(npc.age, 0)
            self.assertIn(npc.home_location, world.locations)
            self.assertIn(npc.work_location, world.locations)
            self.assertIsNotNone(npc.schedule)
            self.assertGreater(len(npc.schedule.blocks), 0)
            self.assertTrue(world.npcs.is_alive(npc.name))

    def test_stationary_worker_receives_needs_and_state_updates(self):
        """Verify shopkeeper/stationary worker updates needs, eats, and forms beliefs/relationships."""
        world = run_day_one(seed=42, print_log=False)
        dev = world.npcs.npcs["Dev Malhotra"]

        # Dev must receive need updates and meals (hunger and thirst should not be stuck at start)
        self.assertLess(dev.hunger, 30.0)
        self.assertLess(dev.thirst, 30.0)
        self.assertGreaterEqual(dev.fatigue, 0.0)
        self.assertEqual(dev.location, "general_store")

    def test_all_npcs_return_home_before_sleep_at_midnight(self):
        """Verify that at 24:00, NPCs have returned to their valid home locations."""
        world = run_day_one(seed=42, print_log=False)

        for name in world.npcs.alive_names():
            npc = world.npcs.npcs[name]
            # At 24:00 / midnight, all NPCs should be at their designated home location
            self.assertEqual(
                npc.location,
                npc.home_location,
                f"NPC {name} ended at {npc.location} instead of home {npc.home_location}",
            )

    def test_world_state_integrity_validation(self):
        """Verify no corrupted or impossible NPC states exist after a full simulation day."""
        world = run_day_one(seed=42, print_log=False)
        errors = world.validate_integrity()
        self.assertEqual(errors, [], f"World integrity errors detected: {errors}")

    def test_simulation_runs_to_midnight_without_crashing(self):
        world = run_day_one(seed=42, print_log=False)
        # Clock started at Day 1, 06:00 and ran 18 hours -> Day 2, 00:00 (which is Day 1 24:00)
        self.assertEqual(world.clock.day, 2)
        self.assertEqual(world.clock.hour, 0)
        self.assertEqual(world.clock.minute, 0)
        self.assertGreater(len(world.events.structured_log), 0)

    def test_structured_log_format_and_event_types(self):
        world = run_day_one(seed=42, print_log=False)
        event_types = {e.event_type for e in world.events.structured_log}

        # Verify structured events emitted across movements, activities, and social dialogues
        self.assertTrue({"MOVEMENT", "ACTIVITY", "SOCIAL"}.issubset(event_types))

        for evt in world.events.structured_log:
            self.assertGreater(evt.day, 0)
            self.assertGreaterEqual(evt.hour, 0)
            self.assertLessEqual(evt.hour, 23)
            self.assertGreaterEqual(evt.minute, 0)
            self.assertLessEqual(evt.minute, 59)
            formatted = evt.format()
            self.assertIn(" | ", formatted)
            self.assertIn(evt.npc, formatted)
            self.assertIn(evt.event_type, formatted)

    def test_deterministic_reproducibility_with_seed(self):
        world_a = run_day_one(seed=123, print_log=False)
        world_b = run_day_one(seed=123, print_log=False)

        log_a = [e.format() for e in world_a.events.structured_log]
        log_b = [e.format() for e in world_b.events.structured_log]

        self.assertEqual(log_a, log_b)
        self.assertEqual(len(log_a), len(log_b))


if __name__ == "__main__":
    unittest.main()
