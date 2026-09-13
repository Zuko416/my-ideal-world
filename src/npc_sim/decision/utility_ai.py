"""Goal, Intention, and Utility AI decision evaluations."""
import random
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
        # Legacy exact scoring behavior preserved for regression parity
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

    # Milestone 6: Emergent Behavioral Utility Scoring with Dynamic Routine Modulation
    scores: Dict[str, float] = {}

    hunger_factor = npc.hunger / 100.0
    thirst_factor = npc.thirst / 100.0
    fatigue_factor = npc.fatigue / 100.0

    # 1. Base physiological need drives (scaled non-linearly when high)
    scores["eat"] = hunger_factor * 0.85 + (0.35 if hunger_factor > 0.55 else 0.0)
    scores["drink"] = thirst_factor * 0.85 + (0.35 if thirst_factor > 0.55 else 0.0)
    scores["sleep"] = fatigue_factor * 0.85 + (0.45 if fatigue_factor > 0.65 else 0.0)
    scores["rest"] = fatigue_factor * 0.65 + (1.0 - npc.sociability) * 0.25

    # 2. Labor / Work utility influenced by personality, efficiency, and stamina
    labor_mult = npc.labor_efficiency if hasattr(npc, "labor_efficiency") else 1.0
    base_work = (1.0 - npc.sociability * 0.3) * (0.3 + npc.intelligence * 0.3) * labor_mult
    scores["work"] = base_work * max(0.1, 1.0 - fatigue_factor * 0.6 - hunger_factor * 0.4)

    # 3. Social utility influenced by personality, fatigue, hunger, relationships, and memories
    if others_present:
        base_social = npc.sociability * 0.55 + npc.kindness * 0.25
        if npc.is_child:
            base_social += 0.25

        # Fatigue and severe hunger reduce patience to socialize
        social_patience = max(0.1, 1.0 - fatigue_factor * 0.8 - hunger_factor * 0.4)
        social_utility = base_social * social_patience

        # Relationship and Memory affinity modifiers
        rel_scores = [npc.rel(other) for other in others_present]
        max_rel = max(rel_scores)
        min_rel = min(rel_scores)

        if max_rel > 0.3:
            social_utility += max_rel * 0.25
        if min_rel < -0.1:
            social_utility += min_rel * 0.3

        # Check for positive/negative memories regarding present individuals
        for mem in getattr(npc, "memories", []):
            mem_target = getattr(mem, "about", None)
            if mem_target in others_present:
                if getattr(mem, "emotion", "") in ("gratitude", "affection"):
                    social_utility += 0.15
                elif getattr(mem, "emotion", "") in ("resentment", "fear"):
                    social_utility -= 0.15

        scores["talk"] = max(0.0, social_utility)
    else:
        scores["talk"] = 0.0

    # 4. Solitary recreation / play
    scores["recreation"] = (0.35 if npc.is_child else 0.15) + (1.0 - npc.sociability) * 0.25

    # 5. Scheduled routine integration (as desire baseline, not rigid order)
    block = npc.get_scheduled_activity(current_hour)
    activity = block.activity
    weight = block.base_weight

    if activity == ActivityType.WORK and npc.can_work:
        scores["work"] = max(scores.get("work", 0.0), weight * max(0.3, 1.0 - fatigue_factor * 0.4))
    elif activity == ActivityType.SCHOOL and npc.is_child:
        scores["school"] = weight * max(0.4, 1.0 - fatigue_factor * 0.4)
    elif activity == ActivityType.SLEEP:
        scores["sleep"] = max(scores.get("sleep", 0.0), weight + fatigue_factor * 0.4)
    elif activity == ActivityType.MEAL:
        scores["eat"] = max(scores.get("eat", 0.0), weight)
        scores["drink"] = max(scores.get("drink", 0.0), weight)
    elif activity == ActivityType.REST:
        scores["rest"] = max(scores.get("rest", 0.0), weight + fatigue_factor * 0.3)
    elif activity in (ActivityType.SOCIALIZE, ActivityType.RECREATION):
        if others_present:
            scores["talk"] = scores.get("talk", 0.0) + weight * 0.35
        else:
            scores["recreation"] = scores.get("recreation", 0.0) + weight * 0.35
    elif activity == ActivityType.ERRAND:
        scores["errand"] = weight

    # 6. Active goal pursuit
    g = npc.top_goal()
    if g and connections:
        scores["pursue_goal"] = g.score() + 0.2 * (1.0 - fatigue_factor * 0.5)

    return scores


def decide_threat_response(
    npc: "NPC",
    danger_level: float = 0.5,
    others_present: Optional[List[str]] = None,
    today: int = 1,
    danger: Optional[float] = None,
) -> Tuple[str, Optional[str]]:
    """Determine an adult or older youth's action during high-stress threat events."""
    if danger is not None:
        danger_level = danger
    if others_present is None:
        others_present = []

    if npc.is_child:
        return decide_child_threat_response(npc, danger_level, others_present, today)

    # Check active protective goals and high-affinity bonds
    for other in others_present:
        if npc.rel(other) > 0.4 and npc.bravery > 0.3:
            return "protect", other
        for g in npc.goals:
            if g.kind == "protect" and g.target == other and npc.bravery > 0.3:
                return "protect", other

    if npc.bravery > danger_level:
        return "attack", None

    return "flee", None


def decide_child_threat_response(
    npc: "NPC",
    danger: float,
    others_present: List[str],
    day: int = 1,
) -> Tuple[str, Optional[str]]:
    """Determine a child's specialized threat response (attachment and guardian seeking)."""
    from npc_sim.relationships.family import get_known_nearby_guardian

    guardian = get_known_nearby_guardian(
        npc.family,
        lambda name: npc.believed_location(name),
        npc.location,
    )
    if guardian and guardian in others_present:
        return "follow_guardian", guardian

    if others_present:
        trusted = max(others_present, key=lambda o: npc.rel(o))
        if npc.rel(trusted) > 0.2:
            return "approach_trusted", trusted

    return "hide", None
