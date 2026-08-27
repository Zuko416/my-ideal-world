"""Personality traits and behavioral constants for NPCs."""
from dataclasses import dataclass

CHILD_AGE_THRESHOLD = 14


@dataclass
class Traits:
    """Personality traits defining an NPC's character."""
    bravery: float = 0.5
    kindness: float = 0.5
    aggression: float = 0.5
    sociability: float = 0.5
    intelligence: float = 0.5
