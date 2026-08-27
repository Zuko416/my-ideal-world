"""Multi-dimensional pairwise relationship tracking and affinity adjustments."""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Relationship:
    """Multi-dimensional relationship vector between two characters."""
    affinity: float = 0.0      # -1.0 (hatred) to 1.0 (love/adoration)
    trust: float = 0.0         # 0.0 (total suspicion) to 1.0 (unquestioning trust)
    respect: float = 0.0       # 0.0 (contempt) to 1.0 (deep admiration/deference)
    fear: float = 0.0          # 0.0 (unafraid) to 1.0 (terrified/intimidated)
    attachment: float = 0.0    # 0.0 (independent) to 1.0 (deep emotional dependency)
    debt: int = 0              # Favors owed (>0) or due (<0)


def ensure_relationship_record(relationships: Dict[str, Any], other: str) -> Relationship:
    """Ensure that the entry in the relationships dict is a Relationship instance."""
    val = relationships.get(other)
    if isinstance(val, Relationship):
        return val
    elif isinstance(val, (int, float)):
        record = Relationship(affinity=float(val))
        relationships[other] = record
        return record
    else:
        record = Relationship()
        relationships[other] = record
        return record


def get_relationship(relationships: Dict[str, Any], other: str) -> float:
    """Get the primary affinity score with another NPC, bounded within [-1.0, 1.0]."""
    val = relationships.get(other)
    if isinstance(val, Relationship):
        return val.affinity
    elif isinstance(val, (int, float)):
        return float(val)
    return 0.0


def get_relationship_record(relationships: Dict[str, Any], other: str) -> Relationship:
    """Get the full multi-dimensional Relationship record."""
    return ensure_relationship_record(relationships, other)


def adjust_relationship(relationships: Dict[str, Any], other: str, delta: float) -> None:
    """Adjust relationship affinity bounded within [-1.0, 1.0]."""
    record = ensure_relationship_record(relationships, other)
    record.affinity = max(-1.0, min(1.0, record.affinity + delta))


def adjust_relationship_dimension(
    relationships: Dict[str, Any],
    other: str,
    dimension: str,
    delta: float,
) -> None:
    """Adjust a specific relationship dimension with appropriate clamping."""
    record = ensure_relationship_record(relationships, other)
    if dimension == "affinity":
        record.affinity = max(-1.0, min(1.0, record.affinity + delta))
    elif dimension in ("trust", "respect", "fear", "attachment"):
        curr = getattr(record, dimension)
        setattr(record, dimension, max(0.0, min(1.0, curr + delta)))
    elif dimension == "debt":
        record.debt += int(delta)
