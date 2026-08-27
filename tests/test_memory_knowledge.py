"""Tests for memory sentiment and belief system."""
import unittest
from npc_sim.core.npc import NPC
from npc_sim.memory.knowledge import update_belief, get_believed_location


class TestMemoryKnowledge(unittest.TestCase):
    def test_memory_sentiment_calculation(self):
        npc = NPC("John", 40, 0.9, 0.7, 0.3, 0.6, 0.6, "house")
        npc.remember("Sarah gave medicine", importance=0.8, emotion="gratitude", day=1, about="Sarah", rel_delta=0.2)
        npc.remember("Sarah attacked someone", importance=0.5, emotion="resentment", day=2, about="Sarah", rel_delta=-0.1)

        # 1 gratitude (+0.8) and 1 resentment (-0.5) -> (0.8 - 0.5) / 2 = 0.15
        self.assertAlmostEqual(npc.sentiment("Sarah"), 0.15, places=3)

    def test_sentiment_recent_days_filter(self):
        npc = NPC("John", 40, 0.9, 0.7, 0.3, 0.6, 0.6, "house")
        npc.remember("Old deed", importance=1.0, emotion="gratitude", day=1, about="Sarah")
        npc.remember("Recent bad deed", importance=1.0, emotion="resentment", day=10, about="Sarah")

        self.assertEqual(npc.sentiment("Sarah", recent_days=3, today=11), -1.0)
        self.assertEqual(npc.sentiment("Sarah", recent_days=15, today=11), 0.0)

    def test_belief_confidence_and_recency_updates(self):
        beliefs = {}
        update_belief(beliefs, "Sarah", "house", confidence=0.5, day=1)
        self.assertEqual(get_believed_location(beliefs, "Sarah"), "house")

        # Lower confidence on same day should not overwrite
        update_belief(beliefs, "Sarah", "forest", confidence=0.3, day=1)
        self.assertEqual(get_believed_location(beliefs, "Sarah"), "house")

        # Higher confidence overwrites
        update_belief(beliefs, "Sarah", "farm", confidence=0.9, day=1)
        self.assertEqual(get_believed_location(beliefs, "Sarah"), "farm")

        # Later day overwrites even with lower confidence
        update_belief(beliefs, "Sarah", "clinic", confidence=0.4, day=2)
        self.assertEqual(get_believed_location(beliefs, "Sarah"), "clinic")


if __name__ == "__main__":
    unittest.main()
