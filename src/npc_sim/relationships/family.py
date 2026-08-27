"""Family bonds, guardianship links, and protective goals."""
from typing import List, Optional, Callable, Dict, TYPE_CHECKING
from npc_sim.decision.utility_ai import Goal

if TYPE_CHECKING:
    from npc_sim.core.npc import NPC, NPCManager


def get_guardians(family: Dict[str, str]) -> List[str]:
    """Retrieve all family members serving as a guardian or parent."""
    return [n for n, role in family.items() if role in ("mother", "father", "guardian")]


def get_known_nearby_guardian(
    family: Dict[str, str],
    believed_loc_fn: Callable[[str], Optional[str]],
    here: str,
) -> Optional[str]:
    """Find a guardian whose believed location matches the current location."""
    for g in get_guardians(family):
        if believed_loc_fn(g) == here:
            return g
    return None


class FamilySystem:
    """Manages familial connections, attachment bonds, and protective instincts."""

    @staticmethod
    def link(a: "NPC", b: "NPC", a_to_b_role: str, b_to_a_role: str, day: int = 0) -> None:
        """Establish bidirectional family relationship and initial attachments."""
        a.family[b.name] = a_to_b_role
        b.family[a.name] = b_to_a_role
        base = {"mother": 0.9, "father": 0.9, "child": 0.9, "sibling": 0.6, "spouse": 0.85}
        a.adjust_rel(b.name, base.get(a_to_b_role, 0.5))
        b.adjust_rel(a.name, base.get(b_to_a_role, 0.5))
        if a_to_b_role in ("mother", "father"):
            b.attachment[a.name] = 0.9
            b.believe(a.name, a.location, 1.0, day)

    @staticmethod
    def derive_protective_goals(npc_manager: "NPCManager") -> None:
        """Add protective goals for family members towards their children."""
        for npc in npc_manager.npcs.values():
            for other_name, role in npc.family.items():
                if role == "child" and not any(g.kind == "protect" and g.target == other_name for g in npc.goals):
                    npc.goals.append(Goal(kind="protect", target=other_name, priority=0.9, urgency=0.5))
