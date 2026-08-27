"""Tests for dynamic routine interruption via urgent goals, severe needs, and threat AI."""
import unittest
from npc_sim.core.npc import NPC
from npc_sim.decision.utility_ai import Goal
from npc_sim.world.location import Location


class TestRoutineInterruptions(unittest.TestCase):
    def test_urgent_goal_interrupts_work_schedule(self):
        npc = NPC("John", age=40, bravery=0.8, kindness=0.8, sociability=0.5, occupation="worker", location="house")
        loc = Location("house")

        # Under normal conditions during work hour (10:00), work utility is highest
        normal_scores = npc.score_actions(others_present=[], loc=loc, connections=["clinic"], current_hour=10)
        self.assertEqual(max(normal_scores, key=normal_scores.get), "work")

        # When an urgent goal arises (find missing daughter, priority=1.0, urgency=1.0)
        npc.goals.append(Goal(kind="find", target="Emma", priority=1.0, urgency=1.0))
        interrupted_scores = npc.score_actions(others_present=[], loc=loc, connections=["clinic"], current_hour=10)

        # pursue_goal should now outscore work (1.0 vs ~0.6)
        self.assertEqual(max(interrupted_scores, key=interrupted_scores.get), "pursue_goal")
        self.assertGreater(interrupted_scores["pursue_goal"], interrupted_scores["work"])

    def test_severe_hunger_interrupts_work_schedule(self):
        npc = NPC("Bob", age=30, bravery=0.5, kindness=0.5, sociability=0.5, occupation="worker", location="house", hunger=95.0)
        loc = Location("house")

        scores = npc.score_actions(others_present=[], loc=loc, connections=["farm"], current_hour=10)
        # Hunger 95 -> eat score is ~0.76, surpassing baseline work score (0.6)
        self.assertEqual(max(scores, key=scores.get), "eat")
        self.assertGreater(scores["eat"], scores["work"])

    def test_threat_stays_awake_during_sleep_hour(self):
        npc = NPC("Sarah", age=35, bravery=0.5, kindness=0.9, aggression=0.2, location="house")
        npc.goals.append(Goal(kind="protect", target="Emma", priority=1.0, urgency=1.0))
        # Sarah is asleep at 02:00
        self.assertEqual(npc.get_scheduled_activity(2).activity.value, "sleep")

        # Threat occurs: decide_on_threat engages protect goal
        action, target = npc.decide_on_threat(danger_level=0.5, others_present=["Emma"], today=1)
        self.assertEqual(action, "protect")
        self.assertEqual(target, "Emma")


if __name__ == "__main__":
    unittest.main()
