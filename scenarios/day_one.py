"""Day One peaceful life simulation for the canonical 15-character village prototype."""
import random
from typing import Dict, List

from npc_sim.core.npc import NPC
from npc_sim.core.schedule import Chronotype, create_daily_schedule
from npc_sim.relationships.family import FamilySystem
from npc_sim.world.location import Location
from npc_sim.world.world import World


def create_village_world() -> World:
    """Create the interconnected village locations and road network."""
    locations: Dict[str, Location] = {
        "forster_home": Location("forster_home"),
        "twin_cottage": Location("twin_cottage"),
        "newlywed_home": Location("newlywed_home"),
        "menon_home": Location("menon_home"),
        "village_road": Location("village_road"),
        "town_square": Location("town_square"),
        "general_store": Location("general_store"),
        "village_school": Location("village_school"),
        "clinic": Location("clinic"),
        "farms": Location("farms"),
        "workshop": Location("workshop"),
        "forest": Location("forest", danger=0.3),
    }

    connections: Dict[str, List[str]] = {
        "forster_home": ["village_road"],
        "twin_cottage": ["village_road"],
        "newlywed_home": ["village_road"],
        "menon_home": ["village_road"],
        "village_road": [
            "forster_home",
            "twin_cottage",
            "newlywed_home",
            "menon_home",
            "town_square",
            "farms",
            "workshop",
        ],
        "town_square": ["village_road", "general_store", "village_school", "clinic", "farms"],
        "general_store": ["town_square"],
        "village_school": ["town_square"],
        "clinic": ["town_square"],
        "farms": ["village_road", "town_square", "forest"],
        "workshop": ["village_road"],
        "forest": ["farms"],
    }

    return World(locations=locations, connections=connections)


def populate_village(world: World) -> List[NPC]:
    """Create and configure all 15 canonical village characters with families, traits, and schedules."""
    # 1. Forster Family (Family of 4)
    jeagel = NPC(
        name="Jeagel Forster",
        age=34,
        bravery=0.7,
        kindness=0.8,
        aggression=0.3,
        sociability=0.6,
        intelligence=0.6,
        location="forster_home",
        home_location="forster_home",
        work_location="workshop",
        occupation="builder",
        chronotype=Chronotype.EARLY_RISER,
    )
    sarah = NPC(
        name="Sarah Forster",
        age=8,
        bravery=0.3,
        kindness=0.7,
        aggression=0.1,
        sociability=0.7,
        intelligence=0.6,
        location="forster_home",
        home_location="forster_home",
        work_location="village_school",
        occupation="student",
        chronotype=Chronotype.NORMAL,
    )
    arthur = NPC(
        name="Arthur Forster",
        age=61,
        bravery=0.5,
        kindness=0.8,
        aggression=0.2,
        sociability=0.5,
        intelligence=0.7,
        location="forster_home",
        home_location="forster_home",
        work_location="town_square",
        occupation="gardener",
        chronotype=Chronotype.EARLY_RISER,
    )
    elena_f = NPC(
        name="Elena Forster",
        age=27,
        bravery=0.5,
        kindness=0.7,
        aggression=0.2,
        sociability=0.8,
        intelligence=0.7,
        location="forster_home",
        home_location="forster_home",
        work_location="general_store",
        occupation="tailor",
        chronotype=Chronotype.NORMAL,
    )

    # 2. Voss Twins
    mira = NPC(
        name="Mira Voss",
        age=19,
        bravery=0.6,
        kindness=0.7,
        aggression=0.2,
        sociability=0.6,
        intelligence=0.8,
        location="twin_cottage",
        home_location="twin_cottage",
        work_location="clinic",
        occupation="herbalist",
        chronotype=Chronotype.NORMAL,
    )
    evan = NPC(
        name="Evan Voss",
        age=19,
        bravery=0.7,
        kindness=0.6,
        aggression=0.4,
        sociability=0.7,
        intelligence=0.5,
        location="twin_cottage",
        home_location="twin_cottage",
        work_location="farms",
        occupation="farmhand",
        chronotype=Chronotype.LATE_SLEEPER,
    )

    # 3. Rao Newlyweds (~3 months married)
    anya = NPC(
        name="Anya Rao",
        age=23,
        bravery=0.5,
        kindness=0.9,
        aggression=0.1,
        sociability=0.7,
        intelligence=0.7,
        location="newlywed_home",
        home_location="newlywed_home",
        work_location="general_store",
        occupation="baker",
        chronotype=Chronotype.NORMAL,
    )
    arjun = NPC(
        name="Arjun Rao",
        age=24,
        bravery=0.6,
        kindness=0.8,
        aggression=0.3,
        sociability=0.6,
        intelligence=0.6,
        location="newlywed_home",
        home_location="newlywed_home",
        work_location="workshop",
        occupation="blacksmith",
        chronotype=Chronotype.EARLY_RISER,
    )

    # 4. Menon Family (Adults + 3 children under 7)
    raghav = NPC(
        name="Raghav Menon",
        age=38,
        bravery=0.6,
        kindness=0.7,
        aggression=0.3,
        sociability=0.6,
        intelligence=0.6,
        location="menon_home",
        home_location="menon_home",
        work_location="farms",
        occupation="farmer",
        chronotype=Chronotype.EARLY_RISER,
    )
    nila = NPC(
        name="Nila Menon",
        age=35,
        bravery=0.5,
        kindness=0.9,
        aggression=0.1,
        sociability=0.7,
        intelligence=0.7,
        location="menon_home",
        home_location="menon_home",
        work_location="menon_home",
        occupation="homemaker",
        chronotype=Chronotype.NORMAL,
    )
    kian = NPC(
        name="Kian Menon",
        age=6,
        bravery=0.4,
        kindness=0.7,
        aggression=0.2,
        sociability=0.8,
        intelligence=0.5,
        location="menon_home",
        home_location="menon_home",
        work_location="village_school",
        occupation="child",
        chronotype=Chronotype.EARLY_RISER,
    )
    tara = NPC(
        name="Tara Menon",
        age=4,
        bravery=0.3,
        kindness=0.8,
        aggression=0.1,
        sociability=0.6,
        intelligence=0.5,
        location="menon_home",
        home_location="menon_home",
        work_location="menon_home",
        occupation="child",
        chronotype=Chronotype.NORMAL,
    )
    ravi = NPC(
        name="Ravi Menon",
        age=2,
        bravery=0.2,
        kindness=0.6,
        aggression=0.1,
        sociability=0.5,
        intelligence=0.4,
        location="menon_home",
        home_location="menon_home",
        work_location="menon_home",
        occupation="toddler",
        chronotype=Chronotype.EARLY_RISER,
    )

    # 5. Village Adults
    dev = NPC(
        name="Dev Malhotra",
        age=50,
        bravery=0.4,
        kindness=0.6,
        aggression=0.3,
        sociability=0.7,
        intelligence=0.7,
        location="general_store",
        home_location="general_store",
        work_location="general_store",
        occupation="shopkeeper",
        chronotype=Chronotype.NORMAL,
    )
    sameer = NPC(
        name="Sameer Khan",
        age=42,
        bravery=0.7,
        kindness=0.8,
        aggression=0.2,
        sociability=0.6,
        intelligence=0.9,
        location="clinic",
        home_location="clinic",
        work_location="clinic",
        occupation="doctor",
        chronotype=Chronotype.NORMAL,
    )

    roster = [
        jeagel, sarah, arthur, elena_f,
        mira, evan,
        anya, arjun,
        raghav, nila, kian, tara, ravi,
        dev, sameer,
    ]

    for npc in roster:
        world.npcs.add(npc)
        npc.schedule = create_daily_schedule(
            age=npc.age,
            chronotype=npc.chronotype,
            occupation=npc.occupation,
            home_location=npc.home_location,
            work_location=npc.work_location,
            social_location="town_square",
        )

    # Kinship links: FamilySystem.link(a, b, a_sees_b_as, b_sees_a_as)
    # Forster family
    FamilySystem.link(jeagel, sarah, "child", "father", day=1)
    FamilySystem.link(arthur, jeagel, "child", "father", day=1)
    FamilySystem.link(arthur, sarah, "grandchild", "grandfather", day=1)
    FamilySystem.link(arthur, elena_f, "child", "father", day=1)
    FamilySystem.link(jeagel, elena_f, "sibling", "sibling", day=1)
    FamilySystem.link(elena_f, sarah, "niece", "aunt", day=1)

    # Voss twins
    FamilySystem.link(mira, evan, "sibling", "sibling", day=1)

    # Rao newlyweds
    FamilySystem.link(anya, arjun, "spouse", "spouse", day=1)

    # Menon family
    FamilySystem.link(raghav, nila, "spouse", "spouse", day=1)
    FamilySystem.link(raghav, kian, "child", "father", day=1)
    FamilySystem.link(raghav, tara, "child", "father", day=1)
    FamilySystem.link(raghav, ravi, "child", "father", day=1)
    FamilySystem.link(nila, kian, "child", "mother", day=1)
    FamilySystem.link(nila, tara, "child", "mother", day=1)
    FamilySystem.link(nila, ravi, "child", "mother", day=1)
    FamilySystem.link(kian, tara, "sibling", "sibling", day=1)
    FamilySystem.link(kian, ravi, "sibling", "sibling", day=1)
    FamilySystem.link(tara, ravi, "sibling", "sibling", day=1)

    return roster


def run_day_one(seed: int = 42, print_log: bool = False) -> World:
    """
    Run Day 1 from 06:00 to 24:00 (18 hours) under peaceful peacetime conditions.
    Returns the simulated World instance.
    """
    random.seed(seed)
    world = create_village_world()
    populate_village(world)

    # Set clock to Day 1, 06:00
    world.clock.day = 1
    world.clock.hour = 6
    world.clock.minute = 0

    # Advance hour by hour until midnight (24:00) -> 18 hourly ticks
    for _ in range(18):
        world.step_simulation(minutes=60)

    if print_log:
        world.events.print_structured()

    return world


if __name__ == "__main__":
    run_day_one(seed=42, print_log=True)
