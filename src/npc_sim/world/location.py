"""Location node definitions and danger/resource state."""
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Location:
    """A map node with danger level and available resources."""
    name: str
    danger: float = 0.1
    resources: dict = field(default_factory=dict)
