"""Relationships, multi-dimensional tracking, and family system."""
from npc_sim.relationships.relationships import (
    Relationship,
    get_relationship,
    get_relationship_record,
    adjust_relationship,
    adjust_relationship_dimension,
)
from npc_sim.relationships.family import (
    FamilySystem,
    get_guardians,
    get_known_nearby_guardian,
)

__all__ = [
    "Relationship",
    "get_relationship",
    "get_relationship_record",
    "adjust_relationship",
    "adjust_relationship_dimension",
    "FamilySystem",
    "get_guardians",
    "get_known_nearby_guardian",
]
