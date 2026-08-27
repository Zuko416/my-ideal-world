"""Personality traits, psychological states, and age category constants for NPCs."""
from dataclasses import dataclass, field
from enum import Enum
from typing import List

# Age boundaries
TODDLER_MAX_AGE = 3
YOUNG_CHILD_MAX_AGE = 7
CHILD_AGE_THRESHOLD = 14
ELDER_AGE_THRESHOLD = 60


class AgeGroup(Enum):
    TODDLER = "toddler"          # 0 - 3
    YOUNG_CHILD = "young_child"  # 4 - 7
    OLDER_CHILD = "older_child"  # 8 - 13
    ADULT = "adult"              # 14 - 59
    ELDER = "elder"              # 60+


def get_age_group(age: int) -> AgeGroup:
    """Determine the developmental age group for a given age in years."""
    if age <= TODDLER_MAX_AGE:
        return AgeGroup.TODDLER
    elif age <= YOUNG_CHILD_MAX_AGE:
        return AgeGroup.YOUNG_CHILD
    elif age < CHILD_AGE_THRESHOLD:
        return AgeGroup.OLDER_CHILD
    elif age >= ELDER_AGE_THRESHOLD:
        return AgeGroup.ELDER
    return AgeGroup.ADULT


@dataclass
class Traits:
    """Core personality traits defining an NPC's baseline temperament."""
    bravery: float = 0.5
    kindness: float = 0.5
    aggression: float = 0.5
    sociability: float = 0.5
    intelligence: float = 0.5
    stability: float = 0.5  # Emotional resilience under stress and danger


@dataclass
class PsychologyState:
    """Dynamic, non-pathological psychological states and stress metrics."""
    stress: float = 0.0       # 0.0 (calm) to 1.0 (overwhelmed)
    fear: float = 0.1         # 0.0 (composed) to 1.0 (terrified)
    morale: float = 1.0       # 1.0 (optimistic/determined) to 0.0 (hopeless)
    trauma_memories: List[str] = field(default_factory=list)
