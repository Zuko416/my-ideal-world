"""Biological and physiological need updates."""
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from npc_sim.core.npc import NPC


def update_npc_needs(npc: "NPC", hours: float = 24.0) -> None:
    """
    Increment NPC hunger, thirst, and fatigue based on elapsed time.
    Default hours=24.0 maintains exact legacy daily decay intervals.
    """
    factor = hours / 24.0
    npc.hunger = min(100.0, npc.hunger + random.uniform(2.0, 5.0) * factor)
    npc.thirst = min(100.0, npc.thirst + random.uniform(2.0, 5.0) * factor)
    npc.fatigue = min(100.0, npc.fatigue + random.uniform(1.0, 4.0) * factor)
