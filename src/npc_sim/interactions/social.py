"""Social interactions, conversation, gossip propagation, contextual dialogue, and child interaction modes."""
import random
from typing import List, Optional, Tuple, Dict, Set, FrozenSet, TYPE_CHECKING

if TYPE_CHECKING:
    from npc_sim.core.npc import NPC
    from npc_sim.world.world import World


def handle_talk(actor: "NPC", others: List[str], world: "World") -> None:
    """Legacy conversation and secondhand belief/gossip sharing for deterministic daily_life."""
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


def determine_interaction_context(actor: "NPC", partner: "NPC", location: str) -> Tuple[str, str, Dict[str, float]]:
    """
    Determine the behavioral reason, natural description, and relationship delta effects.
    Returns (category, description, deltas_dict).
    """
    deltas: Dict[str, float] = {"affinity": 0.0, "trust": 0.0, "respect": 0.0, "resentment": 0.0}

    # 1. Toddler-specific interactions
    if actor.is_toddler:
        if partner.name in actor.family:
            deltas["affinity"] = 0.03
            deltas["trust"] = 0.02
            return "SEEK_COMFORT", f"Sought comfort and affection from {partner.name}", deltas
        deltas["affinity"] = 0.01
        return "IMITATE", f"Curiously watched and imitated {partner.name}", deltas

    if partner.is_toddler:
        if actor.name in partner.family:
            deltas["affinity"] = 0.03
            deltas["trust"] = 0.02
            return "FAMILY_BOND", f"Cared for and comforted toddler {partner.name}", deltas
        deltas["affinity"] = 0.01
        return "SHOW_OBJECT", f"Showed a playful toy to toddler {partner.name}", deltas

    # 2. Young Child interactions
    if actor.is_young_child:
        if partner.is_child:
            if location == "village_school":
                deltas["affinity"] = 0.02
                deltas["trust"] = 0.01
                return "CONVERSE", f"Discussed school lessons with {partner.name}", deltas
            deltas["affinity"] = 0.03
            deltas["trust"] = 0.01
            return "PLAY", f"Played a game with {partner.name}", deltas
        if partner.name in actor.family:
            deltas["affinity"] = 0.02
            deltas["trust"] = 0.02
            return "ASK_QUESTION", f"Asked curious questions to {partner.name}", deltas
        deltas["affinity"] = 0.01
        return "GREETING", f"Said hello to {partner.name}", deltas

    # 3. Grumpy / Irritable Interaction (due to extreme fatigue or hunger)
    if (actor.fatigue > 75 or actor.hunger > 75) and actor.aggression > 0.3:
        deltas["affinity"] = -0.02
        deltas["resentment"] = 0.02
        return "ARGUE", f"Exchanged a short, irritable remark with {partner.name}", deltas

    # 4. Family Interactions
    if partner.name in actor.family:
        role = actor.family[partner.name]
        deltas["affinity"] = 0.025
        deltas["trust"] = 0.02
        if role in ("child", "grandchild", "niece", "nephew"):
            return "FAMILY_BOND", f"Checked in with {role} {partner.name}", deltas
        elif role in ("mother", "father", "grandfather", "grandmother", "aunt", "uncle"):
            deltas["respect"] = 0.02
            return "FAMILY_BOND", f"Shared a warm moment with {role} {partner.name}", deltas
        elif role == "spouse":
            deltas["affinity"] = 0.03
            deltas["trust"] = 0.02
            return "FAMILY_BOND", f"Shared a warm conversation with spouse {partner.name}", deltas
        elif role == "sibling":
            return "FAMILY_BOND", f"Talked with sibling {partner.name}", deltas
        else:
            return "FAMILY_BOND", f"Conversed with family member {partner.name}", deltas

    # 5. Work / Trade Discussions
    if location in ("general_store", "workshop", "clinic", "farms"):
        if actor.occupation == "shopkeeper" or partner.occupation == "shopkeeper":
            deltas["respect"] = 0.02
            deltas["trust"] = 0.02
            return "TRADE", f"Discussed store goods and village supplies with {partner.name}", deltas
        elif actor.occupation in ("builder", "blacksmith") and partner.occupation in ("builder", "blacksmith"):
            deltas["respect"] = 0.03
            deltas["trust"] = 0.01
            return "DISCUSS_WORK", f"Talked about materials and workshop projects with {partner.name}", deltas
        elif actor.occupation in ("farmer", "farmhand") and partner.occupation in ("farmer", "farmhand"):
            deltas["respect"] = 0.02
            deltas["trust"] = 0.02
            return "DISCUSS_WORK", f"Discussed the harvest and farm work with {partner.name}", deltas
        elif actor.occupation == "doctor" or partner.occupation == "doctor":
            deltas["trust"] = 0.03
            deltas["respect"] = 0.02
            return "DISCUSS_WORK", f"Consulted with {partner.name} on remedies and well-being", deltas

    # 6. Friendly / Community Interaction
    if actor.rel(partner.name) > 0.4:
        deltas["affinity"] = 0.015
        deltas["trust"] = 0.01
        return "CONVERSE", f"Caught up warmly on personal news with {partner.name}", deltas

    # Default polite greeting (minimal relationship shift)
    deltas["trust"] = 0.005
    return "GREETING", f"Exchanged a friendly greeting with {partner.name}", deltas


def evaluate_and_execute_interaction(
    actor: "NPC",
    partner: "NPC",
    world: "World",
    location: str,
    hour: int,
    minute: int,
    recent_interactions: Dict[FrozenSet[str], int],
) -> bool:
    """
    Evaluate if an interaction should happen based on personality, relationship,
    state, and cooldowns, then execute it with multi-dimensional outcome.
    """
    pair = frozenset((actor.name, partner.name))
    last_time = recent_interactions.get(pair, -999)
    current_time_total = world.day * 24 + hour

    # Cooldown enforcement: at least 2 hour interval (1 hour for close family living together)
    min_gap = 1 if partner.name in actor.family else 2
    if current_time_total - last_time < min_gap:
        return False

    # Mutual readiness checks (severe fatigue/hunger inhibits interaction)
    if actor.fatigue > 85.0 or partner.fatigue > 85.0:
        return False
    if actor.hunger > 80.0 or partner.hunger > 80.0:
        return False

    # Interaction probability calculation
    base_chance = actor.sociability * 0.5 + partner.sociability * 0.3 + 0.2
    if partner.name in actor.family:
        base_chance += 0.3
    if actor.rel(partner.name) > 0.3:
        base_chance += 0.2

    # Negative memory or resentment check reduces interaction chance
    for mem in getattr(actor, "memories", []):
        if getattr(mem, "about", None) == partner.name and getattr(mem, "emotion", "") in ("resentment", "fear"):
            base_chance -= 0.2

    if random.random() > base_chance:
        return False

    # Execute interaction
    recent_interactions[pair] = current_time_total

    # Determine context and relationship deltas
    cat, desc, deltas = determine_interaction_context(actor, partner, location)

    # Track family vs non-family interactions in daily stats
    if world.day in world.events.daily_stats:
        if partner.name in actor.family:
            world.events.daily_stats[world.day].family_interactions_count += 1
        else:
            world.events.daily_stats[world.day].non_family_interactions_count += 1

    # Apply relationship adjustments with natural diminishing returns
    aff_delta = deltas.get("affinity", 0.0)
    trust_delta = deltas.get("trust", 0.0)
    resp_delta = deltas.get("respect", 0.0)

    if aff_delta != 0.0:
        cur_aff = actor.rel(partner.name)
        # Asymptotic dampening above 0.85 so relationships approach but don't artificially lock at 1.00
        scale = max(0.1, 1.0 - abs(cur_aff)) if abs(cur_aff) > 0.85 else 1.0
        actor.adjust_rel(partner.name, aff_delta * scale)
        partner.adjust_rel(actor.name, aff_delta * scale)

    if trust_delta != 0.0:
        cur_trust = actor.trust_in(partner.name)
        scale_t = max(0.1, 1.0 - cur_trust) if cur_trust > 0.85 else 1.0
        actor.adjust_rel_dim(partner.name, "trust", trust_delta * scale_t)
        partner.adjust_rel_dim(actor.name, "trust", trust_delta * scale_t)

    if resp_delta != 0.0:
        cur_resp = actor.respect_for(partner.name)
        scale_r = max(0.1, 1.0 - cur_resp) if cur_resp > 0.85 else 1.0
        actor.adjust_rel_dim(partner.name, "respect", resp_delta * scale_r)
        partner.adjust_rel_dim(actor.name, "respect", resp_delta * scale_r)

    world.events.record_structured(
        day=world.day,
        hour=hour,
        minute=minute,
        npc=actor.name,
        event_type="SOCIAL",
        description=desc,
        location=location,
    )

    # Meaningful memory formation for impactful interaction categories
    if cat in ("FAMILY_BOND", "SEEK_COMFORT"):
        actor.remember(desc, 0.4, "affection", world.day, about=partner.name)
    elif cat == "ARGUE":
        actor.remember(desc, 0.5, "resentment", world.day, about=partner.name)
        partner.remember(f"Had a sharp disagreement with {actor.name}", 0.5, "resentment", world.day, about=actor.name)
    elif cat in ("DISCUSS_WORK", "TRADE") and random.random() < 0.2:
        actor.remember(desc, 0.3, "gratitude", world.day, about=partner.name)
    elif cat == "PLAY" and random.random() < 0.3:
        actor.remember(desc, 0.3, "affection", world.day, about=partner.name)

    # Secondary Knowledge / Gossip sharing (only if belief confidence is reasonable)
    if random.random() < 0.35 and actor.beliefs:
        candidates = [s for s, b in actor.beliefs.items() if s != partner.name and s != actor.name and b.confidence >= 0.3]
        if candidates:
            subj = random.choice(candidates)
            belief = actor.beliefs[subj]
            partner.believe(subj, belief.location, belief.confidence * 0.7, world.day)
            world.events.record_structured(
                day=world.day,
                hour=hour,
                minute=minute,
                npc=partner.name,
                event_type="KNOWLEDGE",
                description=f"Learned from {actor.name} that {subj} was at {belief.location}",
                location=location,
            )

    return True
