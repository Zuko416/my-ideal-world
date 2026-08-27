"""Simulation loop runner and coordinator."""
from typing import Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from npc_sim.world.world import World


def run_simulation(world: "World", days: int, attacks: Tuple[Tuple[int, str], ...] = ()) -> None:
    """Execute the simulation runner across specified days."""
    world.run(days, attacks=attacks)
