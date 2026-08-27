"""Navigation, pathfinding, and intention-driven travel execution."""
from typing import Dict, List, Optional, TYPE_CHECKING
from npc_sim.decision.utility_ai import Intention

if TYPE_CHECKING:
    from npc_sim.core.npc import NPC
    from npc_sim.world.world import World

DEFAULT_CONNECTIONS: Dict[str, List[str]] = {
    "house": ["farm", "clinic"],
    "farm": ["house", "forest"],
    "clinic": ["house", "watchtower"],
    "watchtower": ["clinic", "forest"],
    "forest": ["farm", "watchtower"],
}


def bfs_route(connections: Dict[str, List[str]], start: str, target: str) -> List[str]:
    """Find the shortest path between start and target locations using BFS."""
    if start == target:
        return []
    visited, queue = {start}, [(start, [])]
    while queue:
        cur, path = queue.pop(0)
        for nxt in connections.get(cur, []):
            if nxt == target:
                return path + [nxt]
            if nxt not in visited:
                visited.add(nxt)
                queue.append((nxt, path + [nxt]))
    return []


def form_intention(npc: "NPC", connections: Dict[str, List[str]]) -> None:
    """Form an intention and route plan based strictly on NPC beliefs."""
    g = npc.top_goal()
    if not g:
        npc.intention = None
        return
    dest = None
    if g.kind == "find" and g.target:
        dest = npc.believed_location(g.target)  # belief only, never world truth
    elif g.kind == "gather_medicine":
        dest = "clinic"
    if dest and dest != npc.location:
        route = bfs_route(connections, npc.location, dest)
        npc.intention = Intention(goal=g, plan=route)
    else:
        npc.intention = None


def advance_intention(npc: "NPC", world: "World") -> bool:
    """Follow the retained plan one hop per call; keeps destination across days."""
    if not npc.intention or not npc.intention.plan:
        return False
    next_hop = npc.intention.plan[0]
    if world.start_travel(npc, next_hop):
        npc.intention.plan.pop(0)
        return True
    return False


def start_travel(npc: "NPC", dest: str, connections: Dict[str, List[str]]) -> bool:
    """Initiate travel towards an adjacent location."""
    if dest not in connections.get(npc.location, []):
        return False
    npc.traveling_to = dest
    npc.travel_days_left = 1
    return True


def resolve_travel(world: "World") -> None:
    """Resolve in-flight travel, location arrival, and intention goal completions."""
    for name in world.npcs.alive_names():
        npc = world.npcs.npcs[name]
        if npc.traveling_to:
            npc.travel_days_left -= 1
            if npc.travel_days_left <= 0:
                npc.location = npc.traveling_to
                npc.traveling_to = None
                if npc.intention and not npc.intention.plan:
                    g = npc.intention.goal
                    # goal completion checked via belief/perception only
                    if g.kind == "find" and g.target in world.npcs.at(npc.location):
                        npc.believe(g.target, npc.location, 1.0, world.day)
                        world.events.record(world.day, f"{npc.name} found {g.target} at {npc.location}!")
                        npc.goals = [x for x in npc.goals if x is not g]
                        npc.intention = None
                    elif g.kind == "gather_medicine":
                        world.locations["clinic"].resources["medicine"] = (
                            world.locations["clinic"].resources.get("medicine", 0) - 1
                        )
                        npc.goals = [x for x in npc.goals if x is not g]
                        npc.intention = None
                        world.events.record(world.day, f"{npc.name} reached the clinic for medicine.")
