"""Tests for multi-dimensional relationship vectors and adjustments."""
import unittest
from npc_sim.core.npc import NPC
from npc_sim.relationships.relationships import (
    Relationship,
    adjust_relationship,
    adjust_relationship_dimension,
    get_relationship,
    get_relationship_record,
)


class TestRelationshipDimensions(unittest.TestCase):
    def test_multi_dimensional_initialization(self):
        rel = Relationship()
        self.assertEqual(rel.affinity, 0.0)
        self.assertEqual(rel.trust, 0.0)
        self.assertEqual(rel.respect, 0.0)
        self.assertEqual(rel.fear, 0.0)
        self.assertEqual(rel.attachment, 0.0)
        self.assertEqual(rel.debt, 0)

    def test_independent_dimension_adjustments(self):
        rels = {}
        adjust_relationship_dimension(rels, "Sarah", "affinity", 0.6)
        adjust_relationship_dimension(rels, "Sarah", "trust", 0.9)
        adjust_relationship_dimension(rels, "Sarah", "respect", 0.7)
        adjust_relationship_dimension(rels, "Sarah", "fear", 0.2)
        adjust_relationship_dimension(rels, "Sarah", "attachment", 0.8)
        adjust_relationship_dimension(rels, "Sarah", "debt", 3)

        rec = get_relationship_record(rels, "Sarah")
        self.assertEqual(rec.affinity, 0.6)
        self.assertEqual(rec.trust, 0.9)
        self.assertEqual(rec.respect, 0.7)
        self.assertEqual(rec.fear, 0.2)
        self.assertEqual(rec.attachment, 0.8)
        self.assertEqual(rec.debt, 3)

    def test_clamping_boundaries(self):
        rels = {}
        adjust_relationship_dimension(rels, "Mike", "trust", 1.5)
        adjust_relationship_dimension(rels, "Mike", "fear", -0.5)
        adjust_relationship_dimension(rels, "Mike", "affinity", -2.0)

        rec = get_relationship_record(rels, "Mike")
        self.assertEqual(rec.trust, 1.0)
        self.assertEqual(rec.fear, 0.0)
        self.assertEqual(rec.affinity, -1.0)

    def test_npc_helper_integration(self):
        john = NPC("John", 40, 0.9, 0.7, 0.3, 0.6, 0.6, "house")
        john.adjust_rel("Sarah", 0.4)
        john.adjust_rel_dim("Sarah", "trust", 0.8)
        john.adjust_rel_dim("Sarah", "respect", 0.9)

        self.assertEqual(john.rel("Sarah"), 0.4)
        self.assertEqual(john.trust_in("Sarah"), 0.8)
        self.assertEqual(john.respect_for("Sarah"), 0.9)


if __name__ == "__main__":
    unittest.main()
