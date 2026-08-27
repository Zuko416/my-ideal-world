"""Tests for Goal evaluation and threat reactions."""
import unittest
from npc_sim.core.npc import NPC
from npc_sim.decision.utility_ai import Goal, score_npc_actions, decide_threat_response
from npc_sim.world.location import Location


class TestDecisionUtilityAI(unittest.TestCase):
    def test_goal_scoring_and_top_goal(self):
        g1 = Goal(kind="gather_medicine", priority=0.5, urgency=0.5)  # 0.5*0.6 + 0.5*0.4 = 0.5
        g2 = Goal(kind="find", target="Emma", priority=0.9, urgency=0.8)  # 0.9*0.6 + 0.8*0.4 = 0.86

        npc = NPC("Sarah", 35, 0.5, 0.9, 0.2, 0.6, 0.6, "house", goals=[g1, g2])
        self.assertEqual(npc.top_goal(), g2)

    def test_action_scoring_needs_override(self):
        npc = NPC("Bob", 30, 0.5, 0.5, 0.5, 0.5, 0.5, "house", hunger=80.0, thirst=20.0, fatigue=10.0)
        loc = Location("house")
        scores = score_npc_actions(npc, others_present=["Alice"], loc=loc, connections=["farm"])

        self.assertIn("eat", scores)
        self.assertEqual(scores["eat"], 0.8)

    def test_child_threat_reaction(self):
        emma = NPC("Emma", 9, bravery=0.2, kindness=0.6, aggression=0.1, sociability=0.5, intelligence=0.5, location="house")
        sarah = NPC("Sarah", 35, bravery=0.5, kindness=0.9, aggression=0.2, sociability=0.6, intelligence=0.6, location="house")
        emma.family["Sarah"] = "mother"
        emma.believe("Sarah", "house", 1.0, 1)

        # When guardian is present, child follows guardian
        action, target = decide_threat_response(emma, danger_level=0.5, others_present=["Sarah"], today=1)
        self.assertEqual(action, "follow_guardian")
        self.assertEqual(target, "Sarah")

        # When alone, child hides
        action_alone, target_alone = decide_threat_response(emma, danger_level=0.5, others_present=[], today=1)
        self.assertEqual(action_alone, "hide")
        self.assertIsNone(target_alone)


if __name__ == "__main__":
    unittest.main()
