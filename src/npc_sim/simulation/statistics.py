"""Simulation event tracking, structured logging, and daily statistics."""
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from collections import Counter, defaultdict


@dataclass
class SimEvent:
    """A structured simulation event entry."""
    day: int
    hour: int
    minute: int
    npc: str
    event_type: str  # "MOVEMENT", "ACTIVITY", "SOCIAL", "KNOWLEDGE", "RELATIONSHIP", "NEED"
    description: str
    location: str

    def format(self) -> str:
        return f"Day {self.day:02d} {self.hour:02d}:{self.minute:02d} | {self.npc} | {self.event_type} | {self.description} | {self.location}"


@dataclass
class DailyStats:
    """Aggregated daily statistics for simulation reporting."""
    day: int
    total_events: int = 0
    events_by_type: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    active_npcs: set = field(default_factory=set)
    social_interactions_count: int = 0
    family_interactions_count: int = 0
    non_family_interactions_count: int = 0
    routine_deviations_count: int = 0


class EventLog:
    """Stores and prints chronological simulation events with structured metadata support."""

    def __init__(self):
        self.log: List[Tuple[int, str]] = []
        self.structured_log: List[SimEvent] = []
        self.daily_stats: Dict[int, DailyStats] = {}

    def record(self, day: int, text: str) -> None:
        """Legacy day-level event logger for backwards compatibility."""
        self.log.append((day, text))

    def record_structured(
        self,
        day: int,
        hour: int,
        minute: int,
        npc: str,
        event_type: str,
        description: str,
        location: str,
    ) -> SimEvent:
        """Record a structured event entry and update daily stats."""
        evt = SimEvent(day, hour, minute, npc, event_type, description, location)
        self.structured_log.append(evt)
        self.log.append((day, f"{npc} [{event_type}]: {description} at {location}"))

        # Update daily statistics
        if day not in self.daily_stats:
            self.daily_stats[day] = DailyStats(day=day)
        stats = self.daily_stats[day]
        stats.total_events += 1
        stats.events_by_type[event_type] += 1
        stats.active_npcs.add(npc)

        if event_type == "SOCIAL":
            stats.social_interactions_count += 1

        return evt

    def get_day_events(self, day: int) -> List[SimEvent]:
        """Retrieve all structured events recorded for a specific day."""
        return [e for e in self.structured_log if e.day == day]

    def get_daily_summary(self, day: int) -> Dict[str, Any]:
        """Get summary statistics for a specific day."""
        stats = self.daily_stats.get(day, DailyStats(day=day))
        return {
            "day": day,
            "total_events": stats.total_events,
            "events_by_type": dict(stats.events_by_type),
            "active_npcs_count": len(stats.active_npcs),
            "social_interactions": stats.social_interactions_count,
            "family_interactions": stats.family_interactions_count,
            "non_family_interactions": stats.non_family_interactions_count,
            "routine_deviations": stats.routine_deviations_count,
        }

    def print_all(self) -> None:
        print("\n=== Events ===")
        for day, text in self.log:
            print(f"DAY {day}: {text}")

    def print_structured(self) -> None:
        print("\n=== Structured Simulation Log ===")
        for evt in self.structured_log:
            print(evt.format())
