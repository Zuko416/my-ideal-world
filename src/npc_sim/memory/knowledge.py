"""Belief and subjective knowledge representation."""
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class Belief:
    """What an NPC believes about another's location. May be wrong."""
    location: str
    confidence: float
    day: int


def update_belief(
    beliefs: Dict[str, Belief],
    name: str,
    location: str,
    confidence: float,
    day: int,
) -> None:
    """Update belief only if new info is more confident or more recent."""
    cur = beliefs.get(name)
    if cur is None or confidence >= cur.confidence or day > cur.day:
        beliefs[name] = Belief(location=location, confidence=confidence, day=day)


def get_believed_location(beliefs: Dict[str, Belief], name: str) -> Optional[str]:
    """Retrieve the believed location for a given NPC name."""
    b = beliefs.get(name)
    return b.location if b else None
