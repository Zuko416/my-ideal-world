"""Social interactions, conversation, gossip propagation, and petty theft."""
import random
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from npc_sim.core.npc import NPC
    from npc_sim.world.world import World


def handle_talk(actor: "NPC", others: List[str], world: "World") -> None:
    """Execute conversation and secondhand belief/gossip sharing."""
    if not others:
        return
    other_name = random.choice(others)
    other = world.npcs.npcs[other_name]

    if random.random() < actor.sociability * 0.4:
        actor.adjust_rel(other_name, 0.03)
        other.adjust_rel(actor.name, 0.03)
        pair = frozenset((actor.name, other_name))
        if actor.rel(other_name) > 0.3 and other.rel(actor.name) > 0.3 and pair not in world.friend_pairs:
            world.friend_pairs.add(pair)
            world.events.record(world.day, f"{actor.name} became friends with {other_name}.")

    # gossip propagates BELIEF, with confidence penalty (secondhand)
    if random.random() < 0.2 and actor.beliefs:
        subj, belief = random.choice(list(actor.beliefs.items()))
        if subj != other_name:
            other.believe(subj, belief.location, belief.confidence * 0.6, world.day)
            world.events.record(world.day, f"{actor.name} told {other_name} {subj} was seen at {belief.location}.")


def handle_work_crime(actor: "NPC", others: List[str], world: "World") -> None:
    """Handle opportunist theft during work actions."""
    if random.random() < 0.02 and actor.kindness < 0.3 and others:
        victim_name = random.choice(others)
        victim = world.npcs.npcs[victim_name]
        actor.remember(f"stole from {victim_name}", 0.5, "resentment", world.day, victim_name, rel_delta=-0.1)
        victim.remember(f"{actor.name} stole from me", 0.7, "resentment", world.day, actor.name, rel_delta=-0.3)
        world.events.record(world.day, f"{actor.name} stole from {victim_name} at {actor.location}.")
