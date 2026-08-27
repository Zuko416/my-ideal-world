"""Physiological drive updates and thresholds for NPCs."""
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from npc_sim.core.npc import NPC


def update_npc_needs(npc: "NPC") -> None:
    """Increment physiological needs with random variance."""
    npc.hunger = min(100.0, npc.hunger + random.uniform(2, 5))
    npc.thirst = min(100.0, npc.thirst + random.uniform(2, 5))
    npc.fatigue = min(100.0, npc.fatigue + random.uniform(1, 4))
