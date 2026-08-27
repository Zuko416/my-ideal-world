"""Family bonds, guardianship links, and protective goals."""
from typing import List, Optional, Callable, Dict, TYPE_CHECKING
from npc_sim.decision.utility_ai import Goal
from npc_sim.relationships.relationships import adjust_relationship_dimension

if TYPE_CHECKING:
    from npc_sim.core.npc import NPC, NPCManager


def get_guardians(family: Dict[str, str]) -> List[str]:
    """Retrieve all family members serving as a guardian or parent."""
    return [n for n, role in family.items() if role in ("mother", "father", "guardian", "grandfather", "grandmother")]


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
        base_affinity = {
            "mother": 0.9,
            "father": 0.9,
            "child": 0.9,
            "sibling": 0.6,
            "spouse": 0.85,
            "grandfather": 0.85,
            "grandmother": 0.85,
            "grandchild": 0.85,
            "aunt": 0.6,
            "uncle": 0.6,
            "niece": 0.6,
            "nephew": 0.6,
        }
        a.adjust_rel(b.name, base_affinity.get(a_to_b_role, 0.5))
        b.adjust_rel(a.name, base_affinity.get(b_to_a_role, 0.5))

        # Multi-dimensional trust, respect, and attachment setup
        adjust_relationship_dimension(a.relationships, b.name, "trust", 0.8)
        adjust_relationship_dimension(b.relationships, a.name, "trust", 0.8)

        if a_to_b_role in ("mother", "father", "grandfather", "grandmother"):
            b.attachment[a.name] = 0.9
            adjust_relationship_dimension(b.relationships, a.name, "attachment", 0.9)
            adjust_relationship_dimension(b.relationships, a.name, "respect", 0.8)
            b.believe(a.name, a.location, 1.0, day)

        if b_to_a_role in ("mother", "father", "grandfather", "grandmother"):
            a.attachment[b.name] = 0.9
            adjust_relationship_dimension(a.relationships, b.name, "attachment", 0.9)
            adjust_relationship_dimension(a.relationships, b.name, "respect", 0.8)
            a.believe(b.name, b.location, 1.0, day)

        if a_to_b_role == "sibling":
            adjust_relationship_dimension(a.relationships, b.name, "attachment", 0.6)
            adjust_relationship_dimension(b.relationships, a.name, "attachment", 0.6)

    @staticmethod
    def derive_protective_goals(npc_manager: "NPCManager") -> None:
        """Add protective goals for family members towards their children."""
        for npc in npc_manager.npcs.values():
            for other_name, role in npc.family.items():
                if role in ("child", "grandchild", "niece", "nephew") and not any(
                    g.kind == "protect" and g.target == other_name for g in npc.goals
                ):
                    npc.goals.append(Goal(kind="protect", target=other_name, priority=0.9, urgency=0.5))
