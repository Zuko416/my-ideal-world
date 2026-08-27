"""Minute-capable 24-hour simulation clock."""
from dataclasses import dataclass


@dataclass
class SimulationClock:
    """Tracks simulation time with minute-level precision across days."""
    day: int = 1
    hour: int = 8
    minute: int = 0

    def tick(self, minutes: int = 60) -> None:
        """Advance time by a specified number of minutes (handles hour and day rollover)."""
        if minutes <= 0:
            return
        total_minutes = self.minute + minutes
        added_hours = total_minutes // 60
        self.minute = total_minutes % 60

        total_hours = self.hour + added_hours
        added_days = total_hours // 24
        self.hour = total_hours % 24

        self.day += added_days

    @property
    def total_minutes(self) -> int:
        """Total cumulative minutes since Day 1, 00:00."""
        return ((self.day - 1) * 24 * 60) + (self.hour * 60) + self.minute

    @property
    def is_night(self) -> bool:
        """Standard night hours (22:00 - 05:59)."""
        return self.hour >= 22 or self.hour < 6

    @property
    def time_string(self) -> str:
        """Formatted time string (e.g., 'Day 1, 08:00')."""
        return f"Day {self.day}, {self.hour:02d}:{self.minute:02d}"

    def advance_to(self, day: int, hour: int = 0, minute: int = 0) -> None:
        """Advance the clock to a specific future point in time."""
        target_total = ((day - 1) * 24 * 60) + (hour * 60) + minute
        current_total = self.total_minutes
        if target_total > current_total:
            self.tick(target_total - current_total)
