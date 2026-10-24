POTION_LIBRARY = {
    "fire_potion": dict(name="Fire Potion", desc="Deal 20 damage to target enemy.", targeted=True),
    "block_potion": dict(name="Block Potion", desc="Gain 12 Block.", targeted=False),
    "energy_potion": dict(name="Energy Potion", desc="Gain 2 Energy.", targeted=False),
    "strength_potion": dict(name="Strength Potion", desc="Gain 2 Strength this combat.", targeted=False),
    "weak_potion": dict(name="Weak Potion", desc="Apply 3 Weak to target enemy.", targeted=True),
    "vulnerable_potion": dict(name="Vulnerable Potion", desc="Apply 2 Vulnerable to target enemy.", targeted=True),
    "heal_potion": dict(name="Healing Potion", desc="Heal 15 HP.", targeted=False),
    "frail_potion": dict(name="Frail Potion", desc="Apply 3 Frail to target enemy.", targeted=True),
    "swift_potion": dict(name="Swift Potion", desc="Draw 2 cards.", targeted=False),
    "elixir": dict(name="Elixir", desc="Fully heal and remove Weak, Vulnerable, and Frail.", targeted=False),
    "toxic_potion": dict(name="Toxic Potion", desc="Apply 4 Poison to target enemy.", targeted=True),
    "cunning_potion": dict(name="Cunning Potion", desc="Gain 1 Energy and draw 1 card.", targeted=False),
    "gamblers_brew": dict(name="Gambler's Brew", desc="Random effect: big damage, big block, Strength, or a small HP cost.", targeted=True),
    "ambrosia": dict(name="Ambrosia", desc="Fully heal and gain 3 Strength and 3 Dexterity this combat.", targeted=False),
    "insight_potion": dict(name="Insight Potion", desc="Draw 3 cards and gain 1 Energy.", targeted=False),
    "regeneration_potion": dict(name="Regeneration Potion", desc="Gain 4 Block at the start of each of your next 2 turns.", targeted=False),
    "haste_potion": dict(name="Haste Potion", desc="Your next card played this turn costs 0 Energy.", targeted=False),
    "invisibility_potion": dict(name="Invisibility Potion", desc="The next attack against you this combat is completely ignored.", targeted=False),
    "berserk_potion": dict(name="Berserk Potion", desc="Gain 3 Strength but 2 Vulnerable for the rest of combat.", targeted=False),
}

POTION_POOL = list(POTION_LIBRARY.keys())
