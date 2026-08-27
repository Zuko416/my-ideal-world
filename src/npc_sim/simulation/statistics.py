"""Simulation event tracking and logging."""
from typing import List, Tuple


class EventLog:
    """Stores and prints chronological simulation events."""

    def __init__(self):
        self.log: List[Tuple[int, str]] = []

    def record(self, day: int, text: str) -> None:
        self.log.append((day, text))

    def print_all(self) -> None:
        print("\n=== Events ===")
        for day, text in self.log:
            print(f"DAY {day}: {text}")
