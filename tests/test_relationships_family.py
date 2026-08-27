"""Tests for relationship bounding and family linkages."""
import unittest
from npc_sim.core.npc import NPC, NPCManager
from npc_sim.relationships.relationships import adjust_relationship, get_relationship
from npc_sim.relationships.family import FamilySystem


class TestRelationshipsFamily(unittest.TestCase):
    def test_relationship_bounding(self):
        rels = {}
        adjust_relationship(rels, "Mike", 0.5)
        self.assertEqual(get_relationship(rels, "Mike"), 0.5)

        adjust_relationship(rels, "Mike", 0.8)
        self.assertEqual(get_relationship(rels, "Mike"), 1.0)

        adjust_relationship(rels, "Mike", -2.5)
        self.assertEqual(get_relationship(rels, "Mike"), -1.0)

    def test_family_linking_and_attachment(self):
        sarah = NPC("Sarah", 35, 0.5, 0.9, 0.2, 0.6, 0.6, "house")
        emma = NPC("Emma", 9, 0.2, 0.6, 0.1, 0.5, 0.5, "house")

        FamilySystem.link(sarah, emma, "mother", "child", day=1)

        self.assertEqual(sarah.family["Emma"], "mother")
        self.assertEqual(emma.family["Sarah"], "child")
        self.assertEqual(sarah.rel("Emma"), 0.9)
        self.assertEqual(emma.rel("Sarah"), 0.9)
        self.assertEqual(emma.attachment["Sarah"], 0.9)
        self.assertEqual(emma.believed_location("Sarah"), "house")
        self.assertEqual(sarah.guardians(), ["Emma"])
        # Sarah has no initial belief about Emma's location recorded by link()
        self.assertIsNone(sarah.known_nearby_guardian("house"))

    def test_protective_goal_derivation(self):
        manager = NPCManager()
        sarah = NPC("Sarah", 35, 0.5, 0.9, 0.2, 0.6, 0.6, "house")
        emma = NPC("Emma", 9, 0.2, 0.6, 0.1, 0.5, 0.5, "house")
        FamilySystem.link(sarah, emma, "mother", "child", day=0)
        manager.add(sarah)
        manager.add(emma)

        FamilySystem.derive_protective_goals(manager)
        self.assertTrue(any(g.kind == "protect" and g.target == "Sarah" for g in emma.goals))


if __name__ == "__main__":
    unittest.main()
