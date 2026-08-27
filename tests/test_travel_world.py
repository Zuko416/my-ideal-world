"""Tests for BFS pathfinding, intention formation, and travel mechanics."""
import unittest
from npc_sim.core.npc import NPC
from npc_sim.decision.utility_ai import Goal
from npc_sim.world.travel import bfs_route, form_intention, DEFAULT_CONNECTIONS
from npc_sim.world.world import World


class TestTravelWorld(unittest.TestCase):
    def test_bfs_shortest_path(self):
        # house -> clinic -> watchtower
        route = bfs_route(DEFAULT_CONNECTIONS, "house", "watchtower")
        self.assertEqual(route, ["clinic", "watchtower"])

        # same location returns empty plan
        self.assertEqual(bfs_route(DEFAULT_CONNECTIONS, "house", "house"), [])

    def test_intention_formation_from_beliefs_only(self):
        w = World()
        emma = NPC("Emma", 9, 0.2, 0.6, 0.1, 0.5, 0.5, "house")
        emma.goals.append(Goal(kind="find", target="Sarah", priority=0.9, urgency=1.0))

        # Sarah is actually at watchtower, but Emma believes she is at farm
        sarah = NPC("Sarah", 35, 0.5, 0.9, 0.2, 0.6, 0.6, "watchtower")
        w.npcs.add(emma)
        w.npcs.add(sarah)

        emma.believe("Sarah", "farm", 0.8, 1)
        form_intention(emma, w.CONNECTIONS)

        self.assertIsNotNone(emma.intention)
        self.assertEqual(emma.intention.plan, ["farm"])  # Believed destination, not true world destination

    def test_travel_arrival_and_resolution(self):
        w = World()
        sarah = NPC("Sarah", 35, 0.5, 0.9, 0.2, 0.6, 0.6, "house")
        w.npcs.add(sarah)

        self.assertTrue(w.start_travel(sarah, "farm"))
        self.assertEqual(sarah.traveling_to, "farm")
        self.assertEqual(sarah.travel_days_left, 1)

        w.resolve_travel()
        self.assertEqual(sarah.location, "farm")
        self.assertIsNone(sarah.traveling_to)


if __name__ == "__main__":
    unittest.main()
