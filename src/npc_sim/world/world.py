"""World simulation manager, location registry, and event dispatch."""
import random
from typing import Dict, List, Tuple, Optional, Set, FrozenSet

from npc_sim.core.npc import NPC, NPCManager
from npc_sim.core.schedule import ActivityType
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
from npc_sim.simulation.clock import SimulationClock


class World:
    """Central simulation state, managing the location graph, NPCs, and time progression."""

    CONNECTIONS = DEFAULT_CONNECTIONS

    def __init__(self):
        self.locations: Dict[str, Location] = {
            "house": Location("house"),
            "farm": Location("farm"),
            "clinic": Location("clinic"),
            "watchtower": Location("watchtower"),
            "forest": Location("forest", danger=0.4),
        }
        self.npcs = NPCManager()
        self.events = EventLog()
        self.clock = SimulationClock(day=1, hour=8, minute=0)
        self.friend_pairs: Set[FrozenSet[str]] = set()

    @property
    def day(self) -> int:
        return self.clock.day

    @day.setter
    def day(self, val: int) -> None:
        self.clock.day = val

    def tick_minutes(self, minutes: int = 60) -> None:
        """Advance the simulation by a specified number of minutes."""
        self.clock.tick(minutes)

    def tick_hour(self) -> None:
        """Advance the simulation by one hour, updating needs and actions."""
        current_hour = self.clock.hour
        for name in self.npcs.alive_names():
            npc = self.npcs.npcs[name]
            npc.update_needs(hours=1.0)
            others = [o for o in self.npcs.at(npc.location) if o != name]
            loc = self.locations.get(npc.location, Location(npc.location))
            scores = npc.score_actions(others, loc, self.CONNECTIONS.get(npc.location, []), current_hour=current_hour)
            # Pick highest utility action
            if scores:
                best_action = max(scores, key=scores.get)
                if best_action == "eat":
                    npc.hunger = max(0.0, npc.hunger - 15.0)
                elif best_action == "drink":
                    npc.thirst = max(0.0, npc.thirst - 20.0)
                elif best_action == "sleep":
                    npc.fatigue = max(0.0, npc.fatigue - 15.0)

        self.clock.tick(60)

    def form_intention(self, npc: NPC) -> None:
        """Derive an active route intention for an NPC towards their goal destination."""
        form_intention(npc, self.CONNECTIONS)

    def advance_intention(self, npc: NPC) -> bool:
        """Advance an NPC along their planned route."""
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
