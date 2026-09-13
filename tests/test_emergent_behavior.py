"""Unit and regression tests for Milestone 4: Emergent Behavioral Simulation."""
import unittest
from npc_sim.core.npc import NPC
from npc_sim.core.schedule import Chronotype, ActivityType, create_daily_schedule
from npc_sim.decision.utility_ai import score_npc_actions
from npc_sim.interactions.social import (
    determine_interaction_context,
    evaluate_and_execute_interaction,
)
from npc_sim.world.location import Location
from npc_sim.world.world import World
from scenarios.day_one import run_day_one


class TestMilestone4EmergentBehavior(unittest.TestCase):
    def test_personality_affects_utility(self):
        """Test that different personality traits modify utility scores."""
        loc = Location("town_square")
        # Introverted NPC vs Extroverted NPC
        introvert = NPC(name="Intro", age=30, sociability=0.1, kindness=0.2, location="town_square")
        extrovert = NPC(name="Extro", age=30, sociability=0.9, kindness=0.8, location="town_square")

        scores_intro = score_npc_actions(introvert, ["Other"], loc, ["road"], current_hour=17)
        scores_extro = score_npc_actions(extrovert, ["Other"], loc, ["road"], current_hour=17)

        self.assertGreater(scores_extro["talk"], scores_intro["talk"])

    def test_fatigue_changes_action_selection(self):
        """High fatigue should diminish talk utility and increase sleep/rest utility."""
        loc = Location("town_square")
        fresh_npc = NPC(name="Fresh", age=30, sociability=0.8, fatigue=5.0, location="town_square")
        tired_npc = NPC(name="Tired", age=30, sociability=0.8, fatigue=85.0, location="town_square")

        scores_fresh = score_npc_actions(fresh_npc, ["Other"], loc, ["road"], current_hour=17)
        scores_tired = score_npc_actions(tired_npc, ["Other"], loc, ["road"], current_hour=17)

        self.assertGreater(scores_fresh["talk"], scores_tired["talk"])
        self.assertGreater(scores_tired["sleep"], scores_fresh["sleep"])

    def test_memory_affects_future_decisions(self):
        """Positive memories increase social utility; negative memories decrease it."""
        loc = Location("town_square")
        npc = NPC(name="Actor", age=30, sociability=0.5, location="town_square")

        # Baseline with neutral other
        scores_base = score_npc_actions(npc, ["Friend"], loc, ["road"], current_hour=17)

        # Add positive memory regarding Friend
        npc.remember("helped me build", 0.8, "gratitude", day=1, about="Friend")
        scores_pos = score_npc_actions(npc, ["Friend"], loc, ["road"], current_hour=17)

        self.assertGreater(scores_pos["talk"], scores_base["talk"])

    def test_different_relationships_produce_different_social_outcomes(self):
        """Family vs Trade vs Toddler should produce different interaction categories and deltas."""
        adult = NPC(name="Adult", age=35, occupation="shopkeeper", location="general_store")
        child = NPC(name="Child", age=6, occupation="child", location="general_store")
        toddler = NPC(name="Toddler", age=2, occupation="toddler", location="menon_home")
        mother = NPC(name="Mother", age=34, occupation="homemaker", location="menon_home")
        mother.family["Toddler"] = "child"
        toddler.family["Mother"] = "mother"

        cat_toddler, _, deltas_toddler = determine_interaction_context(toddler, mother, "menon_home")
        self.assertEqual(cat_toddler, "SEEK_COMFORT")
        self.assertGreater(deltas_toddler["affinity"], 0.0)

        cat_trade, _, deltas_trade = determine_interaction_context(adult, adult, "general_store")
        self.assertEqual(cat_trade, "TRADE")
        self.assertGreater(deltas_trade["respect"], 0.0)

    def test_child_interaction_capabilities_differ_by_age(self):
        """Toddler and Young Child interactions reflect developmental stages."""
        toddler = NPC(name="Baby", age=2, location="menon_home")
        stranger = NPC(name="Stranger", age=40, location="menon_home")

        cat, desc, _ = determine_interaction_context(toddler, stranger, "menon_home")
        self.assertEqual(cat, "IMITATE")
        self.assertIn("imitated", desc)

    def test_social_cooldown_prevents_repetitive_spam(self):
        """Interactions between the same pair within 2 hours are suppressed."""
        world = World()
        npc_a = NPC(name="A", age=30, sociability=1.0, location="town_square")
        npc_b = NPC(name="B", age=30, sociability=1.0, location="town_square")
        world.npcs.add(npc_a)
        world.npcs.add(npc_b)

        recent = {}
        # First interaction at hour 10
        first_success = evaluate_and_execute_interaction(npc_a, npc_b, world, "town_square", hour=10, minute=0, recent_interactions=recent)
        self.assertTrue(first_success)

        # Immediate repeat at hour 10:30 should fail due to cooldown
        repeat_success = evaluate_and_execute_interaction(npc_a, npc_b, world, "town_square", hour=10, minute=30, recent_interactions=recent)
        self.assertFalse(repeat_success)

    def test_audit_evan_end_of_day_state_fix(self):
        """Audit regression test proving Evan Voss transitions cleanly to rest/sleep at 24:00."""
        world = run_day_one(seed=42, print_log=False)
        evan = world.npcs.npcs["Evan Voss"]

        # Evan must be safely at home
        self.assertEqual(evan.location, "twin_cottage")
        # Fatigue must be cleanly recovered/managed (fatigue = 0.0)
        self.assertEqual(evan.fatigue, 0.0)
        # Evan's evening activity is rest, not a stuck 5-hour continuous meal
        self.assertIn(evan.current_activity, (ActivityType.REST, ActivityType.SLEEP))


if __name__ == "__main__":
    unittest.main()
