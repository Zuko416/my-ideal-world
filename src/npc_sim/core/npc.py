"""NPC entity definition and NPCManager collection."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING

from npc_sim.core.traits import (
    CHILD_AGE_THRESHOLD,
    TODDLER_MAX_AGE,
    YOUNG_CHILD_MAX_AGE,
    ELDER_AGE_THRESHOLD,
    AgeGroup,
    get_age_group,
    Traits,
    PsychologyState,
)
from npc_sim.core.schedule import (
    ActivityType,
    Chronotype,
    ScheduleBlock,
    DailySchedule,
    create_daily_schedule,
)
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
from npc_sim.relationships.relationships import (
    Relationship,
    get_relationship,
    get_relationship_record,
    adjust_relationship,
    adjust_relationship_dimension,
)
from npc_sim.relationships.family import get_guardians, get_known_nearby_guardian

if TYPE_CHECKING:
    from npc_sim.world.location import Location


@dataclass
class NPC:
    """Core autonomous NPC agent in the survival world."""
    name: str
    age: int
    bravery: float = 0.5
    kindness: float = 0.5
    aggression: float = 0.5
    sociability: float = 0.5
    intelligence: float = 0.5
    location: str = "house"
    hunger: float = 20.0
    thirst: float = 20.0
    fatigue: float = 10.0
    relationships: dict = field(default_factory=dict)
    memories: list = field(default_factory=list)
    beliefs: dict = field(default_factory=dict)  # name -> Belief
    goals: list = field(default_factory=list)     # list[Goal]
    intention: Optional[Intention] = None
    family: dict = field(default_factory=dict)
    attachment: dict = field(default_factory=dict)
    alive: bool = True
    traveling_to: Optional[str] = None
    travel_days_left: int = 0
    stability: float = 0.5
    psychology: PsychologyState = field(default_factory=PsychologyState)
    chronotype: Chronotype = Chronotype.NORMAL
    occupation: str = "resident"
    home_location: str = "house"
    work_location: Optional[str] = None
    schedule: Optional[DailySchedule] = None
    current_activity: ActivityType = ActivityType.IDLE

    def __post_init__(self):
        # Sync initial fear field if provided during legacy constructor calls
        if hasattr(self, "_initial_fear"):
            self.psychology.fear = self._initial_fear

    @property
    def fear(self) -> float:
        return self.psychology.fear

    @fear.setter
    def fear(self, val: float) -> None:
        self.psychology.fear = max(0.0, min(1.0, val))

    @property
    def stress(self) -> float:
        return self.psychology.stress

    @stress.setter
    def stress(self, val: float) -> None:
        self.psychology.stress = max(0.0, min(1.0, val))

    @property
    def morale(self) -> float:
        return self.psychology.morale

    @morale.setter
    def morale(self, val: float) -> None:
        self.psychology.morale = max(0.0, min(1.0, val))

    @property
    def age_group(self) -> AgeGroup:
        return get_age_group(self.age)

    @property
    def is_toddler(self) -> bool:
        return self.age <= TODDLER_MAX_AGE

    @property
    def is_young_child(self) -> bool:
        return self.age <= YOUNG_CHILD_MAX_AGE

    @property
    def is_child(self) -> bool:
        return self.age < CHILD_AGE_THRESHOLD

    @property
    def is_elder(self) -> bool:
        return self.age >= ELDER_AGE_THRESHOLD

    @property
    def can_fight(self) -> bool:
        """Physical capability to engage in lethal combat."""
        return self.age >= YOUNG_CHILD_MAX_AGE + 1

    @property
    def can_work(self) -> bool:
        """Physical and developmental capability to perform structured community labor."""
        return self.age >= CHILD_AGE_THRESHOLD

    @property
    def labor_efficiency(self) -> float:
        """Work output multiplier based on age and stamina."""
        if self.is_child:
            return 0.0
        elif self.is_elder:
            return 0.6
        return 1.0

    def get_scheduled_activity(self, hour: int) -> ScheduleBlock:
        """Retrieve scheduled desire for a specific hour, lazily building schedule if missing."""
        if self.schedule is None:
            self.schedule = create_daily_schedule(
                age=self.age,
                chronotype=self.chronotype,
                occupation=self.occupation,
                home_location=self.home_location,
                work_location=self.work_location,
            )
        return self.schedule.get_desired_activity(hour)

    def rel(self, other: str) -> float:
        return get_relationship(self.relationships, other)

    def rel_record(self, other: str) -> Relationship:
        return get_relationship_record(self.relationships, other)

    def adjust_rel(self, other: str, delta: float) -> None:
        adjust_relationship(self.relationships, other, delta)

    def adjust_rel_dim(self, other: str, dimension: str, delta: float) -> None:
        adjust_relationship_dimension(self.relationships, other, dimension, delta)

    def trust_in(self, other: str) -> float:
        return self.rel_record(other).trust

    def respect_for(self, other: str) -> float:
        return self.rel_record(other).respect

    def attachment_to(self, other: str) -> float:
        # Check attachment dictionary or relationship dimension
        if other in self.attachment:
            return self.attachment[other]
        return self.rel_record(other).attachment

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
            if emotion in ("resentment", "fear"):
                self.adjust_rel_dim(about, "trust", -0.1 * (0.5 if hearsay else 1.0))
            elif emotion in ("gratitude", "affection"):
                self.adjust_rel_dim(about, "trust", 0.1 * (0.5 if hearsay else 1.0))

    def believe(self, name: str, location: str, confidence: float, day: int) -> None:
        """Update belief only if new info is more confident or more recent."""
        update_belief(self.beliefs, name, location, confidence, day)

    def believed_location(self, name: str) -> Optional[str]:
        return get_believed_location(self.beliefs, name)

    def guardians(self) -> List[str]:
        return get_guardians(self.family)

    def known_nearby_guardian(self, here: str) -> Optional[str]:
        return get_known_nearby_guardian(self.family, self.believed_location, here)

    def update_needs(self, hours: float = 24.0) -> None:
        update_npc_needs(self, hours=hours)

    def top_goal(self) -> Optional[Goal]:
        return get_top_goal(self.goals)

    def score_actions(
        self,
        others_present: List[str],
        loc: "Location",
        connections: List[str],
        current_hour: Optional[int] = None,
    ) -> Dict[str, float]:
        return score_npc_actions(self, others_present, loc, connections, current_hour=current_hour)

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
