"""Pairwise relationship tracking and affinity adjustments."""
from typing import Dict


def get_relationship(relationships: Dict[str, float], other: str) -> float:
    """Get the relationship score with another NPC, default 0.0."""
    return relationships.get(other, 0.0)


def adjust_relationship(relationships: Dict[str, float], other: str, delta: float) -> None:
    """Adjust relationship score bounded within [-1.0, 1.0]."""
    current = relationships.get(other, 0.0)
    relationships[other] = max(-1.0, min(1.0, current + delta))
