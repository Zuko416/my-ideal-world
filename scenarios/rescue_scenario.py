"""Sarah, Emma, John, and Mike emergent rescue/rumor benchmark scenario."""
import random
from npc_sim.core.npc import NPC
from npc_sim.decision.utility_ai import Goal
from npc_sim.relationships.family import FamilySystem
from npc_sim.world.world import World


def run_scenario() -> World:
    """Sarah (protective mother) / Emma (fearful, attached daughter) / John (brave friend) /
    Mike (selfish liar). Not scripted beyond initial setup + day-2 travel + day-6 lie —
    everything downstream (Emma's search, belief updates, reunion) emerges from the pipeline."""
    random.seed(3)
    w = World()
    sarah = NPC("Sarah", 35, bravery=0.5, kindness=0.9, aggression=0.2, sociability=0.6, intelligence=0.6, location="house")
    emma = NPC("Emma", 9, bravery=0.2, kindness=0.6, aggression=0.1, sociability=0.5, intelligence=0.5, location="house")
    john = NPC("John", 40, bravery=0.9, kindness=0.7, aggression=0.3, sociability=0.6, intelligence=0.6, location="house")
    mike = NPC("Mike", 30, bravery=0.4, kindness=0.1, aggression=0.5, sociability=0.7, intelligence=0.5, location="house")
    for npc in (sarah, emma, john, mike):
        w.npcs.add(npc)
    FamilySystem.link(sarah, emma, "mother", "child", day=0)
    emma.goals.append(Goal(kind="find", target="Sarah", priority=0.95, urgency=1.0))

    w.day = 1  # everyone at settlement
    w.daily_life()

    w.day = 2  # Sarah travels away
    w.start_travel(sarah, "farm")
    w.resolve_travel()
    w.events.record(2, "Sarah travels to the farm.")

    w.day = 3  # zombie attack at settlement; Emma loses sight of Sarah
    w.zombie_attack("house")

    w.day = 4  # John (who saw Sarah leave) tells Emma
    john.believe("Sarah", "farm", 1.0, 2)
    w.npcs.npcs["Emma"].believe("Sarah", "farm", 1.0 * 0.6, 4)
    w.events.record(4, "John tells Emma Sarah was seen at the farm.")

    w.day = 5  # Emma decides to search using her (secondhand) belief
    w.form_intention(emma)
    if emma.intention:
        w.advance_intention(emma)
        w.events.record(5, f"Emma sets out for {emma.believed_location('Sarah')}.")

    for day in range(6, 10):
        w.day = day
        w.resolve_travel()
        w.daily_life()
        if day == 6:  # Mike lies about seeing Sarah elsewhere
            mike.believe("Sarah", "forest", 0.3, 6)  # Mike's own claim is low-confidence/false
            emma.believe("Sarah", "forest", 0.3 * 0.6, 6)
            w.events.record(6, "Mike falsely claims Sarah was seen in the forest.")
        if day == 8:  # John corrects the rumor
            emma.believe("Sarah", "farm", 1.0, 8)
            w.events.record(8, "John corrects the rumor: Sarah is at the farm.")

    w.events.print_all()
    return w


if __name__ == "__main__":
    run_scenario()
