"""Tests for NPC entity and NPCManager."""
import unittest
from npc_sim.core.npc import NPC, NPCManager
from npc_sim.needs.needs import update_npc_needs


class TestNPCCore(unittest.TestCase):
    def test_npc_creation_and_child_property(self):
        adult = NPC("Sarah", age=35, bravery=0.5, kindness=0.9, aggression=0.2, sociability=0.6, intelligence=0.6, location="house")
        child = NPC("Emma", age=9, bravery=0.2, kindness=0.6, aggression=0.1, sociability=0.5, intelligence=0.5, location="house")

        self.assertFalse(adult.is_child)
        self.assertTrue(child.is_child)
        self.assertTrue(adult.alive)
        self.assertEqual(adult.hunger, 20.0)

    def test_npc_manager_tracking(self):
        manager = NPCManager()
        sarah = NPC("Sarah", 35, 0.5, 0.9, 0.2, 0.6, 0.6, "house")
        emma = NPC("Emma", 9, 0.2, 0.6, 0.1, 0.5, 0.5, "house")
        manager.add(sarah)
        manager.add(emma)

        self.assertTrue(manager.is_alive("Sarah"))
        self.assertTrue(manager.is_alive("Emma"))
        self.assertFalse(manager.is_alive("Unknown"))
        self.assertEqual(set(manager.alive_names()), {"Sarah", "Emma"})
        self.assertEqual(set(manager.at("house")), {"Sarah", "Emma"})

        sarah.alive = False
        self.assertFalse(manager.is_alive("Sarah"))
        self.assertEqual(manager.alive_names(), ["Emma"])
        self.assertEqual(manager.at("house"), ["Emma"])

    def test_npc_needs_increase(self):
        npc = NPC("Bob", 25, 0.5, 0.5, 0.5, 0.5, 0.5, "house", hunger=10.0, thirst=10.0, fatigue=10.0)
        update_npc_needs(npc)
        self.assertGreater(npc.hunger, 10.0)
        self.assertGreater(npc.thirst, 10.0)
        self.assertGreater(npc.fatigue, 10.0)


if __name__ == "__main__":
    unittest.main()
