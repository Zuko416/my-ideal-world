"""World coordinator managing simulation ticks, locations, and threats."""
import random
from typing import Dict, List, Set, Tuple

from npc_sim.core.npc import NPC, NPCManager
from npc_sim.world.location import Location
from npc_sim.world.travel import (
    DEFAULT_CONNECTIONS,
    bfs_route,
    form_intention,
    advance_intention,
    start_travel,
    resolve_travel,
)
from npc_sim.interactions.social import handle_talk, handle_work_crime
from npc_sim.simulation.statistics import EventLog


class World:
    """The game environment containing locations, time progression, and world entities."""

    CONNECTIONS = DEFAULT_CONNECTIONS

    def __init__(self):
        self.day: int = 0
        self.npcs: NPCManager = NPCManager()
        self.friend_pairs: Set[frozenset] = set()
        self.events: EventLog = EventLog()
        self.locations: Dict[str, Location] = {n: Location(n) for n in self.CONNECTIONS}

    def _bfs_route(self, start: str, target: str) -> List[str]:
        return bfs_route(self.CONNECTIONS, start, target)

    def form_intention(self, npc: NPC) -> None:
        form_intention(npc, self.CONNECTIONS)

    def advance_intention(self, npc: NPC) -> bool:
        return advance_intention(npc, self)

    def start_travel(self, npc: NPC, dest: str) -> bool:
        return start_travel(npc, dest, self.CONNECTIONS)

    def resolve_travel(self) -> None:
        resolve_travel(self)

    def daily_life(self) -> None:
        """Advance one day of regular NPC routines, needs decay, and interactions."""
        self.resolve_travel()
        for name in self.npcs.alive_names():
            npc = self.npcs.npcs[name]
            if npc.traveling_to:
                continue
            npc.update_needs()
            loc = self.locations[npc.location]
            others = [n for n in self.npcs.at(npc.location) if n != name]
            for o in others:
                npc.believe(o, npc.location, 1.0, self.day)  # direct perception = full confidence

            scores = npc.score_actions(others, loc, self.CONNECTIONS[npc.location])
            action = max(scores, key=scores.get) if scores else "work"

            if action == "pursue_goal":
                if not npc.intention:
                    self.form_intention(npc)
                if npc.intention:
                    self.advance_intention(npc)
            elif action == "talk" and others:
                handle_talk(npc, others, self)
            elif action == "work":
                handle_work_crime(npc, others, self)
            elif action == "eat":
                npc.hunger = max(0.0, npc.hunger - 50)
            elif action == "drink":
                npc.thirst = max(0.0, npc.thirst - 50)
            elif action == "sleep":
                npc.fatigue = max(0.0, npc.fatigue - 60)

    def zombie_attack(self, location_name: str) -> None:
        """Simulate a zombie attack event at a specific location."""
        names = self.npcs.at(location_name)
        loc = self.locations[location_name]
        danger = min(1.0, loc.danger + random.uniform(0.3, 0.6))
        self.events.record(self.day, f"Zombie attack at {location_name}.")
        for name in names:
            npc = self.npcs.npcs[name]
            others = [n for n in names if n != name]
            action, target = npc.decide_on_threat(danger, others, self.day)

            if action == "protect" and target:
                self.events.record(self.day, f"{name} protected {target}.")
                self.npcs.npcs[target].remember(f"{name} protected me", 0.9, "gratitude", self.day, name, rel_delta=0.3)
                if random.random() < danger * 0.25:
                    npc.alive = False
                    self.events.record(self.day, f"{name} died protecting {target}.")
                    self.npcs.npcs[target].remember(f"{name} died protecting me", 1.0, "grief", self.day, name, rel_delta=0.2)
            elif action == "follow_guardian" and target:
                self.events.record(self.day, f"{name} followed guardian {target} to safety.")
            elif action == "approach_trusted" and target:
                self.events.record(self.day, f"{name} ran to trusted {target}.")
            elif action == "hide":
                self.events.record(self.day, f"{name} lost sight of everyone and hid.")
                # child no longer perceives family here -> belief goes stale, may trigger a search goal
            elif action == "attack" and random.random() < danger * 0.18:
                npc.alive = False
                self.events.record(self.day, f"{name} died fighting.")

    def run(self, days: int, attacks: Tuple[Tuple[int, str], ...] = ()) -> None:
        """Run the simulation loop for a set number of days."""
        for day in range(1, days + 1):
            self.day = day
            self.daily_life()
            for d, loc in attacks:
                if d == day:
                    self.zombie_attack(loc)
