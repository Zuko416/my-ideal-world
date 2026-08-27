"""Goal, Intention, and Utility AI decision evaluations."""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple, TYPE_CHECKING
from npc_sim.core.schedule import ActivityType

if TYPE_CHECKING:
    from npc_sim.core.npc import NPC
    from npc_sim.world.location import Location


@dataclass
class Goal:
    """A high-level drive or objective for an NPC."""
    kind: str
    target: Optional[str] = None
    priority: float = 0.5
    urgency: float = 0.5
    progress: float = 0.0
    deadline: Optional[int] = None

    def score(self) -> float:
        return self.priority * 0.6 + self.urgency * 0.4


@dataclass
class Intention:
    """An active commitment to pursue a Goal via a multi-step plan."""
    goal: Goal
    plan: list = field(default_factory=list)  # list of location names, retained across days
    destination: Optional[str] = None


def get_top_goal(goals: List[Goal]) -> Optional[Goal]:
    """Return the highest scoring goal from an NPC's active goals."""
    if not goals:
        return None
    return max(goals, key=lambda g: g.score())


def score_npc_actions(
    npc: "NPC",
    others_present: List[str],
    loc: "Location",
    connections: List[str],
    current_hour: Optional[int] = None,
) -> Dict[str, float]:
    """Calculate utility scores for available daily life actions."""
    if current_hour is None:
        # Legacy exact scoring behavior
        scores: Dict[str, float] = {
            "work": npc.intelligence * 0.1,
            "talk": npc.sociability * 0.4,
        }
        if npc.hunger > 55:
            scores["eat"] = npc.hunger / 100
        if npc.thirst > 55:
            scores["drink"] = npc.thirst / 100
        if npc.fatigue > 70:
            scores["sleep"] = npc.fatigue / 100

        g = npc.top_goal()
        if g and connections:
            scores["pursue_goal"] = g.score() + 0.2
        return scores

    # Fine-grained hourly schedule scoring
    scores = {}
    if others_present:
        scores["talk"] = npc.sociability * 0.5
        if npc.is_child:
            scores["talk"] += 0.2
    else:
        scores["talk"] = 0.0

    scores["work"] = (1.0 - npc.sociability) * 0.3 * (npc.labor_efficiency if hasattr(npc, "labor_efficiency") else 1.0)
    scores["eat"] = (npc.hunger / 100.0) * 0.8
    scores["drink"] = (npc.thirst / 100.0) * 0.8
    scores["sleep"] = (npc.fatigue / 100.0) * 0.8

    block = npc.get_scheduled_activity(current_hour)
    activity = block.activity
    weight = block.base_weight

    if activity == ActivityType.WORK and npc.can_work:
        scores["work"] = max(scores.get("work", 0.0), weight)
    elif activity == ActivityType.SCHOOL and npc.is_child:
        scores["school"] = weight
    elif activity == ActivityType.SLEEP:
        scores["sleep"] = max(scores.get("sleep", 0.0), weight + (npc.fatigue / 100.0) * 0.4)
    elif activity == ActivityType.MEAL:
        scores["eat"] = max(scores.get("eat", 0.0), weight)
        scores["drink"] = max(scores.get("drink", 0.0), weight)
    elif activity in (ActivityType.SOCIALIZE, ActivityType.RECREATION):
        if others_present:
            scores["talk"] = max(scores.get("talk", 0.0), weight)
        else:
            scores["recreation"] = weight
    elif activity in (ActivityType.REST, ActivityType.IDLE):
        scores["rest"] = weight

    top_g = npc.top_goal()
    if top_g and connections:
        scores["pursue_goal"] = top_g.score() + 0.2
    return scores


def decide_threat_response(
    npc: "NPC",
    danger_level: float,
    others_present: List[str],
    today: int,
) -> Tuple[str, Optional[str]]:
    """Determine threat reaction (attack, flee, protect, help, or child-specific behavior)."""
    if npc.is_child:
        return decide_child_threat_response(npc, danger_level, others_present)

    best_bond = max(
        (npc.rel(o) + npc.sentiment(o, recent_days=10, today=today) for o in others_present),
        default=0.0,
    )
    protect_target = None
    for g in npc.goals:
        if g.kind == "protect" and g.target in others_present:
            protect_target = g.target
            break

    scores = {
        "attack": npc.bravery * 0.5 + npc.aggression * 0.3 - danger_level * 0.6 + max(best_bond, 0) * 0.3,
        "flee": (1 - npc.bravery) * 0.6 + danger_level * 0.4 - npc.kindness * 0.1 - max(best_bond, 0) * 0.2,
        "protect": npc.kindness * 0.4 + npc.bravery * 0.2 + (0.5 if protect_target else 0),
        "help": npc.kindness * 0.3 + max(best_bond, 0) * 0.4,
    }
    return max(scores, key=scores.get), protect_target


def decide_child_threat_response(
    npc: "NPC",
    danger_level: float,
    others_present: List[str],
) -> Tuple[str, Optional[str]]:
    """Child-specific fear response and guardian attachment logic."""
    npc.fear = min(1.0, npc.fear + danger_level * (1 - npc.bravery * 0.3))
    g = npc.known_nearby_guardian(npc.location)
    if g and g in others_present:
        return "follow_guardian", g
    trusted = max((o for o in others_present if npc.rel(o) > 0.5), key=lambda o: npc.rel(o), default=None)
    if trusted:
        return "approach_trusted", trusted
    if npc.fear > 0.5:
        return "hide", None
    if npc.bravery > 0.7 and npc.age > 10:
        return "help", None
    return "hide", None
