"""Seven Days peacetime village simulation scenario (Day 1 06:00 through Day 7 24:00)."""
import random
from typing import Dict, Any, List
from npc_sim.world.world import World
from scenarios.day_one import create_village_world, populate_village


def run_seven_days(seed: int = 42, print_log: bool = False) -> World:
    """
    Run the 15-character canonical village simulation across seven full peaceful days.
    Simulation spans from Day 1, 06:00 through Day 7, 24:00 (Day 8, 00:00).
    Total duration: 162 hourly ticks.
    """
    random.seed(seed)

    world = create_village_world()
    populate_village(world)

    # Initialize simulation clock at Day 1, 06:00
    world.clock.day = 1
    world.clock.hour = 6
    world.clock.minute = 0

    # Total hourly steps: 18 hours on Day 1 + 24 * 6 hours on Days 2-7 = 162 hours
    total_hours = (24 - 6) + 24 * 6

    for step in range(total_hours):
        world.step_simulation(minutes=60)

    if print_log:
        world.events.print_structured()

    return world


def get_seven_days_summary(world: World) -> Dict[str, Any]:
    """Compile aggregated 7-day summary metrics and per-day analytics."""
    daily_summaries = {}
    for d in range(1, 8):
        daily_summaries[d] = world.events.get_daily_summary(d)

    total_events = len(world.events.structured_log)
    event_types = {}
    for evt in world.events.structured_log:
        event_types[evt.event_type] = event_types.get(evt.event_type, 0) + 1

    npc_stats = {}
    for name, npc in world.npcs.npcs.items():
        npc_stats[name] = {
            "age": npc.age,
            "occupation": npc.occupation,
            "location": npc.location,
            "activity": npc.current_activity.value if npc.current_activity else "idle",
            "hunger": round(npc.hunger, 1),
            "thirst": round(npc.thirst, 1),
            "fatigue": round(npc.fatigue, 1),
            "relationships_count": len(npc.relationships),
            "memories_count": len(npc.memories),
            "beliefs_count": len(npc.beliefs),
            "top_relationships": sorted(
                [(other, round(npc.rel(other), 2)) for other in npc.relationships],
                key=lambda x: x[1],
                reverse=True,
            )[:3],
        }

    return {
        "final_clock": world.clock.time_string,
        "total_events": total_events,
        "event_types": event_types,
        "daily_summaries": daily_summaries,
        "npc_stats": npc_stats,
        "integrity_errors": world.validate_integrity(),
    }


if __name__ == "__main__":
    world = run_seven_days(seed=42, print_log=False)
    summary = get_seven_days_summary(world)
    print("=== SEVEN DAYS SIMULATION REPORT ===")
    print(f"Final Clock: {summary['final_clock']}")
    print(f"Total Events: {summary['total_events']}")
    print(f"Event Types: {summary['event_types']}")
    print(f"Integrity Errors: {summary['integrity_errors']}")
    print("\nDaily Breakdown:")
    for d, ds in summary["daily_summaries"].items():
        print(f"  Day {d}: Total={ds['total_events']}, Types={ds['events_by_type']}")
    print("\nNPC Final States:")
    for name, stat in summary["npc_stats"].items():
        print(f"  {name}: Loc={stat['location']}, Activity={stat['activity']}, Needs=(H:{stat['hunger']}, T:{stat['thirst']}, F:{stat['fatigue']}), Rels={stat['relationships_count']}, Mems={stat['memories_count']}, Beliefs={stat['beliefs_count']}")
