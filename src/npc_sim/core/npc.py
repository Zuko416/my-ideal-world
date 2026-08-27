"""NPC entity definition and NPCManager collection."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from npc_sim.core.traits import CHILD_AGE_THRESHOLD
from npc_sim.memory.memory import Memory, calculate_sentiment
from npc_sim.memory.knowledge import Belief, update_belief, get_believed_location
from npc_sim.decision.utility_ai import (
    Goal,
    Intention,
    get_top_goal,
    score_npc_actions,
    decide_threat_response,
    decide_child_threat_response,
)
from npc_sim.needs.needs import update_npc_needs
from npc_sim.relationships.relationships import get_relationship, adjust_relationship
from npc_sim.relationships.family import get_guardians, get_known_nearby_guardian

if TYPE_CHECKING:
    from npc_sim.world.location import Location


@dataclass
class NPC:
    """Core autonomous NPC agent in the survival world."""
    name: str
    age: int
    bravery: float
    kindness: float
    aggression: float
    sociability: float
    intelligence: float
    location: str
    hunger: float = 20.0
    thirst: float = 20.0
    fatigue: float = 10.0
    relationships: dict = field(default_factory=dict)
    memories: list = field(default_factory=list)
    beliefs: dict = field(default_factory=dict)  # name -> Belief
    goals: list = field(default_factory=list)     # list[Goal]
    intention: Optional[Intention] = None
    family: dict = field(default_factory=dict)
    fear: float = 0.1
    attachment: dict = field(default_factory=dict)
    alive: bool = True
    traveling_to: Optional[str] = None
    travel_days_left: int = 0

    @property
    def is_child(self) -> bool:
        return self.age < CHILD_AGE_THRESHOLD

    def rel(self, other: str) -> float:
        return get_relationship(self.relationships, other)

    def adjust_rel(self, other: str, delta: float) -> None:
        adjust_relationship(self.relationships, other, delta)

    def sentiment(self, other: str, recent_days: Optional[int] = None, today: Optional[int] = None) -> float:
        return calculate_sentiment(self.memories, other, recent_days=recent_days, today=today)

    def remember(
        self,
        text: str,
        importance: float,
        emotion: str,
        day: int,
        about: Optional[str] = None,
        rel_delta: Optional[float] = None,
        hearsay: bool = False,
    ) -> None:
        self.memories.append(Memory(text, importance, emotion, day, about, hearsay))
        if about and rel_delta is not None:
            self.adjust_rel(about, rel_delta * (0.5 if hearsay else 1.0))

    def believe(self, name: str, location: str, confidence: float, day: int) -> None:
        """Update belief only if new info is more confident or more recent."""
        update_belief(self.beliefs, name, location, confidence, day)

    def believed_location(self, name: str) -> Optional[str]:
        return get_believed_location(self.beliefs, name)

    def guardians(self) -> List[str]:
        return get_guardians(self.family)

    def known_nearby_guardian(self, here: str) -> Optional[str]:
        return get_known_nearby_guardian(self.family, self.believed_location, here)

    def update_needs(self) -> None:
        update_npc_needs(self)

    def top_goal(self) -> Optional[Goal]:
        return get_top_goal(self.goals)

    def score_actions(self, others_present: List[str], loc: "Location", connections: List[str]) -> Dict[str, float]:
        return score_npc_actions(self, others_present, loc, connections)

    def decide_on_threat(
        self,
        danger_level: float,
        others_present: List[str],
        today: int,
    ) -> Tuple[str, Optional[str]]:
        return decide_threat_response(self, danger_level, others_present, today)

    def child_threat_response(
        self,
        danger_level: float,
        others_present: List[str],
    ) -> Tuple[str, Optional[str]]:
        return decide_child_threat_response(self, danger_level, others_present)


class NPCManager:
    """Registry and query interface for all living and deceased NPCs."""

    def __init__(self):
        self.npcs: Dict[str, NPC] = {}

    def add(self, npc: NPC) -> None:
        self.npcs[npc.name] = npc

    def alive_names(self) -> List[str]:
        return [n for n, npc in self.npcs.items() if npc.alive]

    def is_alive(self, name: str) -> bool:
        return name in self.npcs and self.npcs[name].alive

    def at(self, location_name: str) -> List[str]:
        return [
            n for n in self.alive_names()
            if self.npcs[n].location == location_name and not self.npcs[n].traveling_to
        ]
