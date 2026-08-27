"""Tests for age-differentiated capabilities, groups, and physical boundaries."""
import unittest
from npc_sim.core.npc import NPC
from npc_sim.core.traits import AgeGroup, get_age_group


class TestAgeCapabilities(unittest.TestCase):
    def test_age_group_classification(self):
        self.assertEqual(get_age_group(2), AgeGroup.TODDLER)
        self.assertEqual(get_age_group(6), AgeGroup.YOUNG_CHILD)
        self.assertEqual(get_age_group(10), AgeGroup.OLDER_CHILD)
        self.assertEqual(get_age_group(35), AgeGroup.ADULT)
        self.assertEqual(get_age_group(65), AgeGroup.ELDER)

    def test_toddler_and_young_child_capabilities(self):
        toddler = NPC("Baby", age=2)
        young_child = NPC("Kid", age=5)

        self.assertTrue(toddler.is_toddler)
        self.assertTrue(toddler.is_child)
        self.assertFalse(toddler.can_work)
        self.assertFalse(toddler.can_fight)
        self.assertEqual(toddler.labor_efficiency, 0.0)

        self.assertTrue(young_child.is_young_child)
        self.assertTrue(young_child.is_child)
        self.assertFalse(young_child.can_work)
        self.assertFalse(young_child.can_fight)
        self.assertEqual(young_child.labor_efficiency, 0.0)

    def test_older_child_and_adult_capabilities(self):
        older_child = NPC("Teen", age=10)
        adult = NPC("Worker", age=30)
        elder = NPC("Grandpa", age=65)

        self.assertTrue(older_child.is_child)
        self.assertFalse(older_child.can_work)
        self.assertTrue(older_child.can_fight)  # e.g., can attempt defense if high bravery

        self.assertFalse(adult.is_child)
        self.assertTrue(adult.can_work)
        self.assertTrue(adult.can_fight)
        self.assertEqual(adult.labor_efficiency, 1.0)

        self.assertTrue(elder.is_elder)
        self.assertTrue(elder.can_work)
        self.assertTrue(elder.can_fight)
        self.assertEqual(elder.labor_efficiency, 0.6)


if __name__ == "__main__":
    unittest.main()
