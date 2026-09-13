"""World simulation grid, locations, event logging, and tick dispatch."""
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, FrozenSet, Tuple

from npc_sim.core.npc import NPC, NPCManager
from npc_sim.core.schedule import ActivityType
from npc_sim.world.location import Location
from npc_sim.simulation.clock import SimulationClock
from npc_sim.simulation.statistics import EventLog
from npc_sim.world.travel import form_intention, advance_intention, start_travel, resolve_travel, DEFAULT_CONNECTIONS
from npc_sim.interactions.social import evaluate_and_execute_interaction


DEFAULT_LOCATIONS: Dict[str, Location] = {k: Location(k) for k in DEFAULT_CONNECTIONS}


@dataclass
class World:
    """Simulation world containing locations, connectivity, simulation clock, and NPCs."""
    LOCATIONS: Dict[str, Location] = field(default_factory=lambda: dict(DEFAULT_LOCATIONS))
    CONNECTIONS: Dict[str, List[str]] = field(default_factory=lambda: dict(DEFAULT_CONNECTIONS))

    locations: Dict[str, Location] = field(default_factory=lambda: dict(DEFAULT_LOCATIONS))
    connections: Dict[str, List[str]] = field(default_factory=lambda: dict(DEFAULT_CONNECTIONS))
    npcs: NPCManager = field(default_factory=NPCManager)
    day: int = 1
    clock: SimulationClock = field(default_factory=SimulationClock)
    events: EventLog = field(default_factory=EventLog)
    friend_pairs: Set[FrozenSet[str]] = field(default_factory=set)
    recent_interactions: Dict[FrozenSet[str], int] = field(default_factory=dict)

    def validate_integrity(self) -> List[str]:
        """Verify structural consistency of the entire world simulation."""
        errors: List[str] = []

        # 1. Location graph integrity
        for loc_name, loc in self.locations.items():
            if loc_name not in self.connections:
                errors.append(f"Location {loc_name} has no connections entry.")
            for neighbor in self.connections.get(loc_name, []):
                if neighbor not in self.locations:
                    errors.append(f"Location {loc_name} connects to nonexistent location {neighbor}.")

        # 2. NPC state integrity
        for name in self.npcs.alive_names():
            npc = self.npcs.npcs[name]
            if npc.location not in self.locations:
                errors.append(f"{name} is at nonexistent location {npc.location}.")
            if npc.home_location not in self.locations:
                errors.append(f"{name} has nonexistent home_location {npc.home_location}.")
            if npc.work_location and npc.work_location not in self.locations:
                errors.append(f"{name} has nonexistent work_location {npc.work_location}.")

            # Need bounds
            if not (0.0 <= npc.hunger <= 100.0):
                errors.append(f"{name} has out-of-bounds hunger {npc.hunger}.")
            if not (0.0 <= npc.thirst <= 100.0):
                errors.append(f"{name} has out-of-bounds thirst {npc.thirst}.")
            if not (0.0 <= npc.fatigue <= 100.0):
                errors.append(f"{name} has out-of-bounds fatigue {npc.fatigue}.")

            # Schedule integrity
            if npc.schedule is None:
                errors.append(f"{name} has no daily schedule defined.")
            elif len(npc.schedule.blocks) == 0:
                errors.append(f"{name} has an empty schedule block list.\n")

            # Activity validity
            if npc.current_activity is not None and not isinstance(npc.current_activity, ActivityType):
                errors.append(f"{name} has invalid activity type {type(npc.current_activity)}.")

            # Age capabilities
            if npc.age < 0:
                errors.append(f"{name} has negative age {npc.age}.")
            if npc.is_toddler and npc.can_work:
                errors.append(f"Toddler {name} has can_work=True which violates age capabilities.")

        return errors

    def step_simulation(self, minutes: int = 60) -> None:
        """Advance simulation time with fine-grained utility decisions, movement, and structured events."""
        dt_hours = minutes / 60.0
        current_hour = self.clock.hour
        current_minute = self.clock.minute
        day = self.clock.day

        # Stale belief decay at midnight of each new day
        if current_hour == 0 and current_minute == 0:
            for name in self.npcs.alive_names():
                npc = self.npcs.npcs[name]
                stale_keys = []
                for s, b in list(npc.beliefs.items()):
                    if day - b.day >= 3:
                        b.confidence *= 0.8
                        if b.confidence < 0.2:
                            stale_keys.append(s)
                for s in stale_keys:
                    del npc.beliefs[s]

        # 1. Update needs for all living NPCs
        for name in self.npcs.alive_names():
            npc = self.npcs.npcs[name]
            npc.update_needs(hours=dt_hours)

        # 2. Direct perception: update location beliefs of visible co-located NPCs
        for loc_name in self.locations:
            present = self.npcs.at(loc_name)
            for name in present:
                npc = self.npcs.npcs[name]
                for other in present:
                    if other != name:
                        npc.believe(other, loc_name, 1.0, day)

        # 3. Utility decisions and activities
        for name in list(self.npcs.alive_names()):
            npc = self.npcs.npcs[name]
            if npc.traveling_to:
                continue

            others = [o for o in self.npcs.at(npc.location) if o != name]
            loc = self.locations.get(npc.location, Location(npc.location))
            conn = self.connections.get(npc.location, [])
            scores = npc.score_actions(others, loc, conn, current_hour=current_hour)
            best_action = max(scores, key=scores.get) if scores else "rest"
            block = npc.get_scheduled_activity(current_hour)

            # Determine target destination dynamically based on chosen utility action
            if best_action == "pursue_goal" and npc.intention and npc.intention.plan:
                target_dest = npc.intention.plan[0]
            elif best_action == "sleep":
                target_dest = npc.home_location
            elif best_action in ("eat", "drink"):
                if npc.hunger > 50 or npc.thirst > 50:
                    target_dest = npc.home_location
                elif block.target_location and block.target_location in self.locations:
                    target_dest = block.target_location
                else:
                    target_dest = npc.home_location
            elif best_action == "rest":
                target_dest = npc.home_location
            elif best_action == "work" and npc.can_work:
                target_dest = npc.work_location if npc.work_location else (block.target_location or npc.location)
            elif best_action == "school" and npc.is_child:
                target_dest = npc.work_location if npc.work_location else "village_school"
            elif best_action in ("talk", "socialize"):
                target_dest = npc.location if others else (block.target_location or "town_square")
            elif best_action == "recreation":
                target_dest = block.target_location or "town_square"
            elif block.target_location and block.target_location in self.locations:
                target_dest = block.target_location
            else:
                target_dest = npc.location

            # Movement execution
            if target_dest != npc.location and target_dest in self.locations:
                old_loc = npc.location
                npc.location = target_dest
                self.events.record_structured(
                    day=day,
                    hour=current_hour,
                    minute=current_minute,
                    npc=name,
                    event_type="MOVEMENT",
                    description=f"Moved from {old_loc} to {target_dest}",
                    location=target_dest,
                )

            # Execute chosen activity and apply physiological effects
            chosen_activity = ActivityType.IDLE
            if best_action in ("eat", "drink"):
                chosen_activity = ActivityType.MEAL
                npc.hunger = max(0.0, npc.hunger - 30.0)
                npc.thirst = max(0.0, npc.thirst - 30.0)
                self.events.record_structured(
                    day=day,
                    hour=current_hour,
                    minute=current_minute,
                    npc=name,
                    event_type="ACTIVITY",
                    description="Having a meal",
                    location=npc.location,
                )
            elif best_action == "sleep":
                chosen_activity = ActivityType.SLEEP
                npc.fatigue = max(0.0, npc.fatigue - 25.0)
            elif best_action == "rest":
                chosen_activity = ActivityType.REST
                npc.fatigue = max(0.0, npc.fatigue - 10.0)
                if block.activity not in (ActivityType.REST, ActivityType.SLEEP):
                    self.events.record_structured(
                        day=day,
                        hour=current_hour,
                        minute=current_minute,
                        npc=name,
                        event_type="ACTIVITY",
                        description="Resting to recover energy",
                        location=npc.location,
                    )
            elif best_action == "work" and npc.can_work:
                chosen_activity = ActivityType.WORK
                self.events.record_structured(
                    day=day,
                    hour=current_hour,
                    minute=current_minute,
                    npc=name,
                    event_type="ACTIVITY",
                    description=f"Working as {npc.occupation}",
                    location=npc.location,
                )
            elif best_action == "school" and npc.is_child:
                chosen_activity = ActivityType.SCHOOL
                self.events.record_structured(
                    day=day,
                    hour=current_hour,
                    minute=current_minute,
                    npc=name,
                    event_type="ACTIVITY",
                    description="Attending school classes",
                    location=npc.location,
                )
            elif best_action == "recreation":
                chosen_activity = ActivityType.RECREATION
                self.events.record_structured(
                    day=day,
                    hour=current_hour,
                    minute=current_minute,
                    npc=name,
                    event_type="ACTIVITY",
                    description="Engaged in leisure recreation",
                    location=npc.location,
                )
            elif best_action in ("talk", "socialize"):
                chosen_activity = ActivityType.SOCIALIZE
                # Evening home relaxation / chat also recovers fatigue
                if block.activity in (ActivityType.REST, ActivityType.SLEEP) or npc.location == npc.home_location:
                    npc.fatigue = max(0.0, npc.fatigue - 10.0)
                self.events.record_structured(
                    day=day,
                    hour=current_hour,
                    minute=current_minute,
                    npc=name,
                    event_type="ACTIVITY",
                    description="Socializing with community",
                    location=npc.location,
                )
            else:
                chosen_activity = ActivityType.IDLE

            npc.current_activity = chosen_activity

            # Track routine deviations
            if chosen_activity != block.activity and day in self.events.daily_stats:
                self.events.daily_stats[day].routine_deviations_count += 1

        # 4. Social dialogue and contextual knowledge exchange among co-located NPCs
        for loc_name in self.locations:
            present = self.npcs.at(loc_name)
            if len(present) >= 2:
                awake_present = [n for n in present if self.npcs.npcs[n].current_activity != ActivityType.SLEEP]
                for name in awake_present:
                    actor = self.npcs.npcs[name]
                    partners = [n for n in awake_present if n != name]
                    if partners:
                        partner_name = random.choice(partners)
                        partner = self.npcs.npcs[partner_name]
                        evaluate_and_execute_interaction(
                            actor=actor,
                            partner=partner,
                            world=self,
                            location=loc_name,
                            hour=current_hour,
                            minute=current_minute,
                            recent_interactions=self.recent_interactions,
                        )

        # 5. Advance clock
        self.clock.tick(minutes)

    def form_intention(self, npc: NPC) -> None:
        """Derive an active route intention for an NPC towards their goal destination."""
        form_intention(npc, self.connections)

    def advance_intention(self, npc: NPC) -> bool:
        """Advance an NPC along their planned route."""
        return advance_intention(npc, self)

    def start_travel(self, npc: NPC, dest: str) -> bool:
        return start_travel(npc, dest, self.connections)

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
            loc = self.locations.get(npc.location, Location(npc.location))
            conn = self.connections.get(npc.location, [])
            scores = npc.score_actions([o for o in self.npcs.at(npc.location) if o != name], loc, conn)
            best = max(scores, key=scores.get) if scores else "rest"
            if best == "pursue_goal":
                self.advance_intention(npc)
            elif best == "eat":
                npc.hunger = max(0, npc.hunger - 30)
            elif best == "drink":
                npc.thirst = max(0, npc.thirst - 30)
            elif best == "sleep":
                npc.fatigue = max(0, npc.fatigue - 30)
            elif best == "work":
                pass
            elif best == "talk":
                from npc_sim.interactions.social import handle_talk
                handle_talk(npc, [o for o in self.npcs.at(npc.location) if o != name], self)

    def zombie_attack(self, loc_name: str, danger_level: float = 0.5) -> None:
        """Simulate a zombie incursion at a specific location."""
        present = self.npcs.at(loc_name)
        if not present:
            return
        self.events.record(self.day, f"Zombie attack at {loc_name}.")
        for name in list(present):
            npc = self.npcs.npcs[name]
            others = [n for n in present if n != name]
            action, target = npc.decide_on_threat(danger_level, others, self.day)
            if action == "attack":
                if random.random() < 0.3:
                    npc.alive = False
                    self.events.record(self.day, f"{name} died fighting zombies at {loc_name}.")
                else:
                    self.events.record(self.day, f"{name} fought off zombies at {loc_name}.")
            elif action == "flee":
                conn = self.connections.get(loc_name, [])
                if conn:
                    escape_to = random.choice(conn)
                    npc.location = escape_to
                    self.events.record(self.day, f"{name} fled from {loc_name} to {escape_to}.")
                else:
                    self.events.record(self.day, f"{name} had nowhere to flee at {loc_name}.")
            elif action == "hide":
                self.events.record(self.day, f"{name} hid at {loc_name}.")
            elif action == "follow_guardian" and target:
                self.events.record(self.day, f"{name} stayed close to {target} during the attack at {loc_name}.")
            elif action == "approach_trusted" and target:
                self.events.record(self.day, f"{name} sought safety with {target} at {loc_name}.")
            elif action == "protect" and target:
                self.events.record(self.day, f"{name} stepped in to protect {target} at {loc_name}!")
