"""Episodic memory data structure and sentiment scoring."""
from dataclasses import dataclass
from typing import Optional, List

SIGN = {"gratitude": 1, "affection": 1, "resentment": -1, "fear": -1, "grief": -1}


@dataclass
class Memory:
    """An episodic memory record formed by direct perception or hearsay."""
    text: str
    importance: float
    emotion: str
    day: int
    about: Optional[str] = None
    hearsay: bool = False


def calculate_sentiment(
    memories: List[Memory],
    other: str,
    recent_days: Optional[int] = None,
    today: Optional[int] = None,
) -> float:
    """Calculate emotional valence sentiment toward another NPC based on memories."""
    mems = [m for m in memories if m.about == other]
    if recent_days is not None and today is not None:
        mems = [m for m in mems if today - m.day <= recent_days]
    if not mems:
        return 0.0
    return sum(SIGN.get(m.emotion, 0) * m.importance for m in mems) / len(mems)
