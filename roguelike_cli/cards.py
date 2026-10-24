import copy

# card types: attack, skill, power
# effects executed by combat engine via 'effect' key (function name) + params

CARD_LIBRARY = {
    "strike": dict(name="Strike", type="attack", cost=1, damage=6,
                   desc="Deal 6 damage.", rarity="starter"),
    "defend": dict(name="Defend", type="skill", cost=1, block=5,
                   desc="Gain 5 Block.", rarity="starter"),
    "bash": dict(name="Bash", type="attack", cost=2, damage=8, vulnerable=2,
                 desc="Deal 8 damage. Apply 2 Vulnerable.", rarity="starter"),

    "cleave": dict(name="Cleave", type="attack", cost=1, damage=8, aoe=True,
                   desc="Deal 8 damage to ALL enemies.", rarity="common"),
    "iron_wave": dict(name="Iron Wave", type="attack", cost=1, damage=5, block=5,
                       desc="Deal 5 damage. Gain 5 Block.", rarity="common"),
    "quick_slash": dict(name="Quick Slash", type="attack", cost=1, damage=8, draw=1,
                         desc="Deal 8 damage. Draw 1 card.", rarity="common"),
    "true_strike": dict(name="True Strike", type="attack", cost=1, damage=7,
                         desc="Deal 7 damage. Never misses.", rarity="common"),

    "shrug_it_off": dict(name="Shrug It Off", type="skill", cost=1, block=8, draw=1,
                          desc="Gain 8 Block. Draw 1 card.", rarity="common"),
    "battle_trance": dict(name="Battle Trance", type="skill", cost=1, draw=3,
                           desc="Draw 3 cards.", rarity="common"),
    "flex": dict(name="Flex", type="skill", cost=0, temp_str=2,
                 desc="Gain 2 Strength this turn only.", rarity="common"),
    "impervious": dict(name="Impervious", type="skill", cost=2, block=16,
                        desc="Gain 16 Block.", rarity="uncommon"),

    "bloodletting": dict(name="Bloodletting", type="skill", cost=0, lose_hp=3, gain_energy=2,
                          desc="Lose 3 HP. Gain 2 Energy.", rarity="uncommon"),
    "inflame": dict(name="Inflame", type="power", cost=1, strength=2,
                    desc="Gain 2 Strength (permanent).", rarity="uncommon"),
    "metallicize": dict(name="Metallicize", type="power", cost=1, metallicize=3,
                         desc="At end of turn, gain 3 Block (permanent).", rarity="uncommon"),

    "heavy_blade": dict(name="Heavy Blade", type="attack", cost=2, damage=14, str_mult=3,
                         desc="Deal 14 damage. Strength affects this 3x.", rarity="uncommon"),
    "whirlwind": dict(name="Whirlwind", type="attack", cost=1, damage=5, aoe=True, x_cost=True,
                       desc="Deal 5 damage to ALL enemies X times (uses all Energy).", rarity="rare"),

    "twin_strike": dict(name="Twin Strike", type="attack", cost=1, damage=5, hits=2,
                         desc="Deal 5 damage twice to the same enemy.", rarity="common"),
    "pommel_strike": dict(name="Pommel Strike", type="attack", cost=1, damage=9, draw=1,
                           desc="Deal 9 damage. Draw 1 card.", rarity="common"),
    "footwork": dict(name="Footwork", type="power", cost=1, dexterity=2,
                      desc="Gain 2 Dexterity (this combat, permanent).", rarity="uncommon"),
    "entrench": dict(name="Entrench", type="skill", cost=1, double_block=True,
                      desc="Double your current Block.", rarity="uncommon"),

    "clothesline": dict(name="Clothesline", type="attack", cost=2, damage=12, weak=2,
                         desc="Deal 12 damage. Apply 2 Weak.", rarity="uncommon"),
    "combust": dict(name="Combust", type="power", cost=1, combust=5,
                     desc="At end of turn, deal 5 damage to ALL enemies (permanent).", rarity="rare"),
    "adrenaline": dict(name="Adrenaline", type="skill", cost=0, gain_energy=1, draw=1,
                        desc="Costs 0. Gain 1 Energy. Draw 1 card.", rarity="rare"),
    "sever_soul": dict(name="Sever Soul", type="attack", cost=2, damage=16, vulnerable=3,
                        desc="Deal 16 damage. Apply 3 Vulnerable.", rarity="rare"),
    "shield_bash": dict(name="Shield Bash", type="attack", cost=1, damage_eq_block=True,
                         desc="Deal damage equal to your current Block.", rarity="uncommon"),
    "second_life": dict(name="Second Life", type="skill", cost=2, block=12, draw=2,
                         desc="Gain 12 Block. Draw 2 cards.", rarity="rare"),
    "bulwark": dict(name="Bulwark", type="skill", cost=2, block=12, metallicize=2,
                     desc="Gain 12 Block. At end of turn, gain 2 Block (permanent).", rarity="uncommon"),
    "rampage": dict(name="Rampage", type="attack", cost=1, damage=8, strength_on_kill=2,
                     rarity="rare"),
    "crippling_blow": dict(name="Crippling Blow", type="attack", cost=1, damage=7, frail=2,
                            rarity="uncommon"),
    "impale": dict(name="Impale", type="attack", cost=2, damage=20, exhaust=True, rarity="rare"),

    # ---- Curses (unplayable, and some inflict a passive penalty each combat) ----
    "curse_of_pain": dict(name="Curse of Pain", type="curse", cost=99,
                           desc="Unplayable. A curse — remove it at a Smith.", rarity="curse"),
    "curse_of_doubt": dict(name="Curse of Doubt", type="curse", cost=99,
                            desc="Unplayable. A curse — remove it at a Smith.", rarity="curse"),
    "curse_of_weakness": dict(name="Curse of Weakness", type="curse", cost=99, on_start_weak=1,
                               desc="Unplayable. At the start of each combat, gain 1 Weak.", rarity="curse"),
    "curse_of_frailty": dict(name="Curse of Frailty", type="curse", cost=99, on_start_frail=1,
                              desc="Unplayable. At the start of each combat, gain 1 Frail.", rarity="curse"),
    "vault": dict(name="Vault", type="skill", cost=3, block=30, rarity="rare"),
    "focus": dict(name="Focus", type="power", cost=1, strength=1, dexterity=1, rarity="uncommon"),

    # ---- Rogue exclusives (poison) ----
    "poison_dagger": dict(name="Poison Dagger", type="attack", cost=1, damage=4, poison=4,
                           desc="Deal 4 damage. Apply 4 Poison.", rarity="exclusive"),
    "backstab": dict(name="Backstab", type="attack", cost=2, damage=16,
                      desc="Deal 16 damage.", rarity="exclusive"),
    "toxic_cloud": dict(name="Toxic Cloud", type="skill", cost=2, aoe=True, damage=2, poison=2,
                         desc="Deal 2 damage and apply 2 Poison to ALL enemies.", rarity="exclusive"),
    "venom_strike": dict(name="Venom Strike", type="attack", cost=1, damage=3, poison=5,
                          desc="Deal 3 damage. Apply 5 Poison.", rarity="exclusive"),
    "finish_him": dict(name="Finish Him", type="attack", cost=1, poison_execute=True,
                        poison_mult=2, min_damage=4, exhaust=True, rarity="exclusive"),
    "assassinate": dict(name="Assassinate", type="attack", cost=2, poison_execute=True,
                         poison_mult=3, min_damage=8, exhaust=True, rarity="exclusive"),

    # ---- Twin exclusives (echo synergy: every 4th card doubles the next) ----
    "echo_strike": dict(name="Echo Strike", type="attack", cost=1, damage=6,
                         desc="Deal 6 damage. (Echo: every 4th card played doubles the next.)", rarity="exclusive"),
    "mirror_ward": dict(name="Mirror Ward", type="skill", cost=1, block=6,
                         desc="Gain 6 Block.", rarity="exclusive"),
    "twinned_blade": dict(name="Twinned Blade", type="attack", cost=2, damage=8, hits=2,
                           desc="Deal 8 damage twice to the same enemy.", rarity="exclusive"),
    "tally_strike": dict(name="Tally Strike", type="attack", cost=1, scales_with_cards_played=True,
                          cards_played_mult=2, rarity="exclusive"),
    "splitting_image": dict(name="Splitting Image", type="skill", cost=1, block=4, grant_echo=True,
                             rarity="exclusive"),

    # ---- Sord exclusives (every 3rd Attack played grants a free Stab) ----
    "stab": dict(name="Stab", type="attack", cost=1, damage=7,
                 desc="Deal 7 damage. (Every 3rd Attack played grants a free Stab.)", rarity="exclusive"),
    "bonus_stab": dict(name="Stab", type="attack", cost=0, damage=7,
                        desc="Deal 7 damage. Free — granted by Sord's passive.", rarity="exclusive"),
    "parry": dict(name="Parry", type="skill", cost=1, block=7,
                   desc="Gain 7 Block.", rarity="exclusive"),
    "quick_stab": dict(name="Quick Stab", type="attack", cost=0, damage=4,
                        desc="Deal 4 damage. Cheap way to ramp the Stab passive.", rarity="exclusive"),
    "blade_storm": dict(name="Blade Storm", type="attack", cost=1, damage=1, hits=3,
                         scales_with_deck_attacks=True, grants_card="stab", max_upgrades=3,
                         rarity="exclusive"),
    "secret_kill": dict(name="Secret Kill", type="attack", cost=1, damage=5,
                         refund_energy_on_kill=True, max_upgrades=2, upgrade_damage_flat=5,
                         rarity="exclusive"),
    "secret_power": dict(name="Secret Power", type="attack", cost=1, damage=6,
                          scales_with_attacks_played=True, attacks_played_mult=1,
                          no_damage_upgrade=True, max_upgrades=2, rarity="exclusive"),

    # ---- Berserker exclusives (gains Strength from taking damage) ----
    "reckless_swing": dict(name="Reckless Swing", type="attack", cost=1, damage=10, lose_hp=2,
                            desc="Deal 10 damage. Lose 2 HP.", rarity="exclusive"),
    "adrenal_rage": dict(name="Adrenal Rage", type="skill", cost=0, temp_str=3,
                          desc="Gain 3 Strength this turn only.", rarity="exclusive"),
    "last_stand": dict(name="Last Stand", type="skill", cost=2, block=20,
                        desc="Gain 20 Block.", rarity="exclusive"),
    "blood_for_power": dict(name="Blood for Power", type="skill", cost=1, lose_hp=10, strength=5,
                             exhaust=True, rarity="exclusive"),
    "vengeance": dict(name="Vengeance", type="attack", cost=1, damage=4,
                       scales_with_missing_hp=True, missing_hp_divisor=8, rarity="exclusive"),

    "double_strike": dict(name="Double Strike", type="attack", cost=2, damage=9, hits=2, rarity="common"),
    "iron_skin": dict(name="Iron Skin", type="power", cost=1, metallicize=4, rarity="uncommon"),
    "toxic_stab": dict(name="Toxic Stab", type="attack", cost=1, damage=5, poison=3, rarity="common"),
    "guard_break": dict(name="Guard Break", type="attack", cost=2, damage=10, vulnerable=3, weak=2, rarity="rare"),
    "flurry_strike": dict(name="Flurry Strike", type="attack", cost=1, damage=4, hits=3, rarity="uncommon"),
    "aegis": dict(name="Aegis", type="skill", cost=2, block=16, metallicize=2, rarity="rare"),
    "surge": dict(name="Surge", type="skill", cost=0, gain_energy=2, exhaust=True, rarity="uncommon"),
    "piercing_shot": dict(name="Piercing Shot", type="attack", cost=1, damage=7, vulnerable=1, rarity="common"),
    "fortress": dict(name="Fortress", type="skill", cost=2, block=14, strength=1, rarity="uncommon"),
    "reckoning": dict(name="Reckoning", type="attack", cost=3, damage=24, rarity="rare"),
    "wind_blade": dict(name="Wind Blade", type="attack", cost=1, damage=6, grants_random_card=True,
                        rarity="exclusive"),

    # ---- Mirror Card: reward for winning the Mirror Fight, not found any other way ----
    "mirror_card": dict(name="Mirror Card", type="skill", cost=0, is_mirror_card=True,
                         desc="Replay the last card you played this turn, for its same Energy cost. "
                              "If you haven't played a card yet this turn, it fizzles.", rarity="mirror"),

    # ---- Reaper's Scythe: reward for clearing all 4 stages of The Castle ----
    "reapers_scythe": dict(name="Reaper's Scythe", type="attack", cost=2, damage=10,
                            growth=0, grows_on_kill=1, rarity="castle"),

    # ---- Fireball ----
    "fireball": dict(name="Fireball", type="attack", cost=2, damage=12, burning=1,
                      max_upgrades=3, upgrade_damage_flat=4, rarity="rare"),

    # ==== Lophis mode: class-exclusive signature cards, ported from Call of Lophis ====
    # -- Twin Gunner --
    "quick_shot": dict(name="Quick Shot", type="attack", cost=1, damage=7,
                        draw_if_hand_empty=True, max_upgrades=2, upgrade_damage_flat=7, rarity="exclusive"),
    "double_shoot": dict(name="Double Shot", type="attack", cost=1, damage=6,
                          splash_half_random=True, max_upgrades=2, upgrade_damage_flat=6, rarity="exclusive"),
    "snipe": dict(name="Snipe", type="attack", cost=1, damage=10, wound=1,
                  max_upgrades=2, upgrade_damage_flat=8, rarity="exclusive"),

    # -- Blacksmith --
    "recast": dict(name="Recast", type="skill", cost=0, discard_gain_energy_draw=True, rarity="exclusive"),
    "drop_protect": dict(name="Forge", type="skill", cost=1, block=12, resist=2, discard_then_bonus=True,
                          max_upgrades=2, upgrade_block_flat=4, rarity="exclusive"),
    "copy": dict(name="Copy", type="skill", cost=1, duplicate_hand_cards=1, max_upgrades=2, rarity="exclusive"),

    # -- Swordsman --
    "wind_blade": dict(name="Wind Blade", type="attack", cost=1, damage=6, draw=1,
                        max_upgrades=2, upgrade_damage_flat=3, rarity="exclusive"),
    "swords_random_stab": dict(name="Secret·Wind", type="attack", cost=1, damage=3, base_hits=2,
                                hits_scale_with_hand_attacks=True, max_upgrades=2, rarity="exclusive"),
    "secret_damage": dict(name="Secret·Power", type="attack", cost=0, damage=6,
                           scales_with_cards_played=True, cards_played_mult=1,
                           max_upgrades=2, rarity="exclusive"),

    # -- Pharmacist --
    "poison_honor": dict(name="Honor of Poison", type="skill", cost=1, draw_per_poisoned_enemy=True, rarity="exclusive"),
    "poison_cloud": dict(name="Poison Cloud", type="attack", cost=1, damage=4, poison=1, aoe=True,
                          max_upgrades=2, upgrade_damage_flat=2, rarity="exclusive"),
    "poison_inject": dict(name="Inject Poison", type="attack", cost=1, damage=1, poison=3,
                           max_upgrades=2, rarity="exclusive"),

    # -- Assassin --
    "hurt_attack": dict(name="Blood Blade", type="attack", cost=1, damage=10, heal_half_if_wounded=True,
                         max_upgrades=2, upgrade_damage_flat=4, rarity="exclusive"),
    "back_dagger_attack": dict(name="Backstab", type="attack", cost=1, damage=6, wound=1, double_if_sneak=True,
                                max_upgrades=2, upgrade_damage_flat=4, rarity="exclusive"),
    "sap": dict(name="Sap", type="attack", cost=1, damage=3, consumes_sneak=True,
                max_upgrades=2, upgrade_damage_flat=3, rarity="exclusive"),
    "sneak": dict(name="Sneak", type="skill", cost=0, sneak_flag=True, rarity="exclusive"),

    # -- Soldier --
    "shield_bash": dict(name="Shield Bash", type="attack", cost=0, damage_eq_armor_pct=50,
                         max_upgrades=2, rarity="exclusive"),
    "defence_state": dict(name="Counter", type="skill", cost=0, guard=4, max_upgrades=2, rarity="exclusive"),
    "shield_equip": dict(name="Power Defend", type="skill", cost=1, block=5, draw=1,
                          max_upgrades=2, upgrade_block_flat=5, rarity="exclusive"),

    # -- Monk --
    "mind_clean": dict(name="Redemption", type="skill", cost=1, remove_sin=3, heal_per_sin=3,
                        max_upgrades=2, rarity="exclusive"),
    "forget_can_happy": dict(name="Eliminate", type="skill", cost=1, remove_sin_all=10, draw=1,
                              max_upgrades=2, rarity="exclusive"),
    "sin_box": dict(name="Suffering", type="attack", cost=1, sin_scaled_aoe=True, sin_pct=100,
                     aoe=True, max_upgrades=2, rarity="exclusive"),
}


CLASS_EXCLUSIVES = {
    "rogue": ["poison_dagger", "backstab", "toxic_cloud", "venom_strike", "finish_him", "assassinate"],
    "twin": ["echo_strike", "mirror_ward", "twinned_blade", "tally_strike", "splitting_image"],
    "sord": ["stab", "bonus_stab", "parry", "quick_stab", "blade_storm", "secret_kill", "secret_power", "wind_blade"],
    "berserker": ["reckless_swing", "adrenal_rage", "last_stand", "blood_for_power", "vengeance"],
}


def make_card(card_id):
    d = copy.deepcopy(CARD_LIBRARY[card_id])
    d["id"] = card_id
    if "desc" not in d:
        d["desc"] = describe_card(d)
    return d


FLAVOR_SUFFIX = {
    "echo_strike": " (Echo: every 4th card played doubles the next.)",
    "stab": " (Every 3rd Attack card played grants a free Stab.)",
    "bonus_stab": " Free — granted by Sord's passive.",
    "quick_stab": " Cheap way to ramp the Stab passive.",
}


def describe_card(c):
    """Build a description string from a card's numeric fields. Used mainly so
    upgraded cards automatically show correct numbers without hand-authoring text."""
    parts = []
    if c.get("x_cost"):
        parts.append(f"Deal {c.get('damage', 0)} damage to ALL enemies X times (uses all Energy).")
    elif c.get("damage_eq_block"):
        parts.append("Deal damage equal to your current Block.")
    elif c.get("poison_execute"):
        parts.append(f"Deal {c.get('poison_mult', 2)}x the target's Poison as damage "
                      f"(minimum {c.get('min_damage', 0)}).")
    elif c.get("scales_with_cards_played"):
        parts.append(f"Deal {c.get('cards_played_mult', 2)} damage for each card played earlier this turn.")
    elif c.get("scales_with_attacks_played"):
        parts.append(f"Deal {c.get('damage', 0)} damage, +{c.get('attacks_played_mult', 1)} for each "
                      f"Attack card played earlier this turn.")
    elif c.get("scales_with_missing_hp"):
        parts.append(f"Deal {c.get('damage', 0)} damage, +1 for every {c.get('missing_hp_divisor', 8)} "
                      f"missing HP you have.")
    elif c.get("damage_eq_armor_pct"):
        parts.append(f"Deal damage equal to {c['damage_eq_armor_pct']}% of your current Block, "
                      f"then lose half your Block.")
    elif c.get("sin_scaled_aoe"):
        parts.append(f"Deal magic damage equal to {c.get('sin_pct', 100)}% of your Sin to ALL enemies.")
    elif c.get("damage"):
        base = c["damage"] + c.get("growth", 0)
        dmg_txt = f"Deal {base} damage"
        if c.get("growth"):
            dmg_txt += f" ({c['growth']} permanent bonus earned so far)"
        if c.get("aoe"):
            dmg_txt += " to ALL enemies"
        hits = c.get("hits", 1)
        if hits > 1:
            dmg_txt += f" {hits} times" + ("" if c.get("aoe") else " to the same enemy")
        mult = c.get("str_mult", 1)
        if mult > 1:
            dmg_txt += f". Strength affects this {mult}x"
        parts.append(dmg_txt + ".")
        if c.get("grows_on_kill"):
            parts.append(f"Permanently gains +{c['grows_on_kill']} damage whenever it deals the killing blow.")

    if c.get("block"):
        parts.append(f"Gain {c['block']} Block.")
    if c.get("double_block"):
        parts.append("Double your current Block.")
    if c.get("poison"):
        parts.append(f"Apply {c['poison']} Poison.")
    if c.get("vulnerable"):
        parts.append(f"Apply {c['vulnerable']} Vulnerable.")
    if c.get("weak"):
        parts.append(f"Apply {c['weak']} Weak.")
    if c.get("frail"):
        parts.append(f"Apply {c['frail']} Frail.")
    if c.get("burning"):
        parts.append(f"Apply {c['burning']} Burning (deals that much damage at the start of "
                      f"the target's next turn, then clears).")
    if c.get("wound"):
        parts.append(f"Apply {c['wound']} Wound.")
    if c.get("resist"):
        parts.append(f"Gain {c['resist']}% damage resistance until your next turn.")
    if c.get("guard"):
        parts.append(f"Gain {c['guard']} Counter (your next hit taken is reflected back at its source, then clears).")
    if c.get("draw_if_hand_empty"):
        parts.append("If your hand is empty after this, draw a card.")
    if c.get("splash_half_random"):
        parts.append("Then deal half that damage to a random other enemy.")
    if c.get("heal_half_if_wounded"):
        parts.append("If the target has Wound, heal for half the damage dealt.")
    if c.get("double_if_sneak"):
        parts.append("Damage and Wound are doubled while you have Sneak.")
    if c.get("consumes_sneak"):
        parts.append("Does not break Sneak.")
    if c.get("discard_gain_energy_draw"):
        parts.append("Discard a random card, gain Energy equal to its cost, and draw a card.")
    if c.get("discard_then_bonus"):
        parts.append("Discard a random card first, then apply the effects above.")
    if c.get("duplicate_hand_cards"):
        parts.append(f"Clone {c['duplicate_hand_cards']} random card(s) from your hand.")
    if c.get("hits_scale_with_hand_attacks"):
        parts.append(f"Deal {c.get('damage',0)} damage, {c.get('base_hits',1)} times "
                      f"+1 for each Attack card in your hand.")
    if c.get("draw_per_poisoned_enemy"):
        parts.append("Draw a card for each enemy that currently has Poison.")
    if c.get("sneak_flag"):
        parts.append("Gain Sneak.")
    if c.get("remove_sin"):
        parts.append(f"Remove up to {c['remove_sin']} Sin; heal {c.get('heal_per_sin',0)} HP for each Sin removed.")
    if c.get("remove_sin_all"):
        parts.append(f"Remove {c['remove_sin_all']} Sin.")
    if c.get("draw"):
        parts.append(f"Draw {c['draw']} card{'s' if c['draw'] > 1 else ''}.")
    if c.get("temp_str"):
        parts.append(f"Gain {c['temp_str']} Strength this turn only.")
    if c.get("strength"):
        parts.append(f"Gain {c['strength']} Strength (permanent).")
    if c.get("dexterity"):
        parts.append(f"Gain {c['dexterity']} Dexterity (this combat, permanent).")
    if c.get("metallicize"):
        parts.append(f"At end of turn, gain {c['metallicize']} Block (permanent).")
    if c.get("combust"):
        parts.append(f"At end of turn, deal {c['combust']} damage to ALL enemies (permanent).")
    if c.get("lose_hp"):
        parts.append(f"Lose {c['lose_hp']} HP.")
    if c.get("gain_energy"):
        parts.append(f"Gain {c['gain_energy']} Energy.")
    if c.get("scales_with_deck_attacks"):
        parts.append("Hits 1 additional time for each Attack card in your deck.")
    if c.get("grants_card"):
        granted_name = CARD_LIBRARY.get(c["grants_card"], {}).get("name", c["grants_card"])
        parts.append(f"Grants a free {granted_name} into your hand when played.")
    if c.get("grants_random_card"):
        parts.append("Draws a random card into your hand.")
    if c.get("refund_energy_on_kill"):
        parts.append("Refund this card's Energy cost if it defeats an enemy.")
    if c.get("strength_on_kill"):
        parts.append(f"Gain {c['strength_on_kill']} Strength (permanent) if it defeats an enemy.")
    if c.get("grant_echo"):
        parts.append("Immediately charge Echo — your next card played is doubled.")
    if c.get("exhaust"):
        parts.append("Exhaust.")

    text = " ".join(parts) if parts else c.get("desc", "")
    text += FLAVOR_SUFFIX.get(c.get("id"), "")
    return text


def is_upgradeable(card):
    return card.get("upgrade_level", 0) < card.get("max_upgrades", 1)


STATUS_KEYS = ("vulnerable", "weak", "frail", "poison", "burning", "wound", "resist", "guard")


def upgrade_offers_path_choice(card):
    """True if a card has both a primary damage/block value AND a status effect,
    meaning an upgrade can go two ways (Type A vs Type B)."""
    has_status = any(card.get(k) for k in STATUS_KEYS)
    has_primary = bool(card.get("damage") or card.get("block"))
    return has_status and has_primary


def upgrade_card(card, path=None):
    """Return an upgraded copy of a card.

    path=None or 'A': Type A upgrade — costs >=2 drop by 1; costs <=1 get a ~30%
    boost to their primary damage/block value (or a flat bump if the card defines
    'upgrade_damage_flat'). This is the only behavior for cards that don't carry a
    status effect, so passing no path is fully backward compatible.

    path='B': Type B upgrade — only meaningful on cards that have BOTH a primary
    damage/block value and a status effect (see upgrade_offers_path_choice). The
    primary damage/block value is left alone and the status effect (poison,
    vulnerable, weak, frail, burning) grows twice as fast instead.

    Cards with hits > 1 gain +1 hit per upgrade. Secondary effects (draw, strength,
    dexterity, metallicize, combust, energy, etc.) always improve a bit regardless
    of path. Most cards allow one upgrade (max_upgrades=1); a few allow more."""
    new_card = copy.deepcopy(card)
    if not is_upgradeable(new_card):
        return new_card
    new_card["upgrade_level"] = new_card.get("upgrade_level", 0) + 1
    new_card["upgraded"] = True
    base_name = card["name"].rstrip("+")
    new_card["name"] = base_name + "+" * new_card["upgrade_level"]

    dual_path = upgrade_offers_path_choice(new_card)
    path = path if path in ("A", "B") else "A"
    new_card["upgrade_path"] = path if dual_path else None
    boost_primary = not dual_path or path == "A"
    status_mult = 2 if (dual_path and path == "B") else 1

    cost = new_card["cost"]
    if new_card.get("x_cost"):
        if new_card.get("damage"):
            new_card["damage"] += 2
    elif new_card.get("upgrade_damage_flat") or new_card.get("upgrade_block_flat"):
        if boost_primary and new_card.get("damage") and new_card.get("upgrade_damage_flat"):
            new_card["damage"] += new_card["upgrade_damage_flat"]
        if boost_primary and new_card.get("block") and new_card.get("upgrade_block_flat"):
            new_card["block"] += new_card["upgrade_block_flat"]
    elif cost >= 2:
        new_card["cost"] = cost - 1
    elif boost_primary:
        if new_card.get("damage") and not new_card.get("damage_eq_block") and not new_card.get("no_damage_upgrade"):
            new_card["damage"] = int(round(new_card["damage"] * 1.3))
        if new_card.get("block"):
            new_card["block"] = int(round(new_card["block"] * 1.3))

    if new_card.get("hits", 1) > 1:
        new_card["hits"] += 1
    if new_card.get("poison"):
        new_card["poison"] += status_mult
    if new_card.get("vulnerable"):
        new_card["vulnerable"] += status_mult
    if new_card.get("weak"):
        new_card["weak"] += status_mult
    if new_card.get("frail"):
        new_card["frail"] += status_mult
    if new_card.get("burning"):
        new_card["burning"] += status_mult
    if new_card.get("wound"):
        new_card["wound"] += status_mult
    if new_card.get("resist"):
        new_card["resist"] += status_mult
    if new_card.get("guard"):
        new_card["guard"] += status_mult
    if new_card.get("draw"):
        new_card["draw"] += 1
    if new_card.get("strength"):
        new_card["strength"] += 1
    if new_card.get("dexterity"):
        new_card["dexterity"] += 1
    if new_card.get("metallicize"):
        new_card["metallicize"] += 2
    if new_card.get("combust"):
        new_card["combust"] += 2
    if new_card.get("gain_energy"):
        new_card["gain_energy"] += 1
    if new_card.get("temp_str"):
        new_card["temp_str"] += 1
    if new_card.get("lose_hp"):
        new_card["lose_hp"] = max(0, new_card["lose_hp"] - 2)
    if new_card.get("poison_mult"):
        new_card["poison_mult"] += 1
    if new_card.get("cards_played_mult"):
        new_card["cards_played_mult"] += 1
    if new_card.get("strength_on_kill"):
        new_card["strength_on_kill"] += 1
    if new_card.get("min_damage"):
        new_card["min_damage"] += 2
    if new_card.get("attacks_played_mult"):
        new_card["attacks_played_mult"] += 1
    if new_card.get("missing_hp_divisor"):
        new_card["missing_hp_divisor"] = max(2, new_card["missing_hp_divisor"] - 2)
    if new_card.get("duplicate_hand_cards"):
        new_card["duplicate_hand_cards"] += 1
    if new_card.get("base_hits"):
        new_card["base_hits"] += 1
    if new_card.get("damage_eq_armor_pct"):
        new_card["damage_eq_armor_pct"] += 25
    if new_card.get("remove_sin"):
        new_card["remove_sin"] += 1
    if new_card.get("heal_per_sin"):
        new_card["heal_per_sin"] += 1
    if new_card.get("remove_sin_all"):
        new_card["remove_sin_all"] += 10
    if new_card.get("sin_pct"):
        new_card["sin_pct"] += 25

    new_card["desc"] = describe_card(new_card)
    return new_card


CLASSES = {
    "warrior": dict(name="Warrior", max_hp=70, max_energy=3, pool="normal",
                     desc="Balanced fighter. No gimmicks, just Strength and steel."),
    "rogue": dict(name="Rogue", max_hp=65, max_energy=3, pool="normal",
                   desc="Fragile but lethal. Poisons stack and melt enemies over time."),
    "twin": dict(name="Twin", max_hp=70, max_energy=3, pool="normal",
                  desc="Echo passive: every 4th card played in a turn doubles the effect of the next card."),
    "sord": dict(name="Sord", max_hp=65, max_energy=3, pool="normal",
                  desc="Every 3rd Attack card played in a turn grants a free Stab card into hand."),
    "berserker": dict(name="Berserker", max_hp=80, max_energy=3, pool="normal",
                       desc="Passive: whenever you take unblocked damage, gain 1 Strength for the rest of combat."),

    # ==== Lophis mode classes — the 7 professions from Call of Lophis ====
    "twingunner": dict(name="Twin Gunner", max_hp=68, max_energy=3, pool="lophis",
                        desc="Quick Shot draws when your hand is empty; Double Shot splashes; "
                             "Snipe always lands and wounds."),
    "blacksmith": dict(name="Blacksmith", max_hp=75, max_energy=3, pool="lophis",
                        desc="Fuels itself by discarding: Recast refunds Energy, Forge trades a card "
                             "for Armor and Resist, Copy clones your hand."),
    "swordsman": dict(name="Swordsman", max_hp=72, max_energy=3, pool="lophis",
                       desc="Wind Blade cycles your hand, Secret路Wind hits once per Attack card held, "
                            "Secret路Power snowballs with every card played this turn."),
    "pharmacist": dict(name="Pharmacist", max_hp=65, max_energy=3, pool="lophis",
                        desc="Poison specialist: Poison Cloud spreads it to everyone, Inject Poison "
                             "stacks it hard, Honor of Poison refills your hand off it."),
    "assassin": dict(name="Assassin", max_hp=62, max_energy=3, pool="lophis",
                      desc="Sneak doubles Backstab's damage and Wound; Sap keeps Sneak alive while "
                           "it works; Blood Blade heals off Wounded targets."),
    "soldier": dict(name="Soldier", max_hp=78, max_energy=3, pool="lophis",
                     desc="Armor-fueled bruiser: Power Defend stacks Armor, Shield Bash spends it as "
                          "damage, Counter reflects the next hit you take."),
    "monk": dict(name="Monk", max_hp=70, max_energy=3, pool="lophis",
                  desc="Carries 3 Sin into every fight. Suffering weaponizes it against all enemies; "
                       "Redemption and Eliminate burn it off for healing and cards."),
}


def starter_deck(character="warrior"):
    deck = []
    if character == "rogue":
        for _ in range(2):
            deck.append(make_card("strike"))
        for _ in range(4):
            deck.append(make_card("defend"))
        deck.append(make_card("poison_dagger"))
        deck.append(make_card("backstab"))
        deck.append(make_card("toxic_cloud"))
        deck.append(make_card("finish_him"))
    elif character == "twin":
        for _ in range(3):
            deck.append(make_card("strike"))
        for _ in range(4):
            deck.append(make_card("defend"))
        deck.append(make_card("echo_strike"))
        deck.append(make_card("mirror_ward"))
        deck.append(make_card("tally_strike"))
    elif character == "sord":
        for _ in range(3):
            deck.append(make_card("strike"))
        for _ in range(2):
            deck.append(make_card("defend"))
        deck.append(make_card("stab"))
        deck.append(make_card("parry"))
        deck.append(make_card("blade_storm"))
        deck.append(make_card("secret_kill"))
        deck.append(make_card("secret_power"))
    elif character == "berserker":
        for _ in range(3):
            deck.append(make_card("strike"))
        for _ in range(2):
            deck.append(make_card("defend"))
        for _ in range(2):
            deck.append(make_card("reckless_swing"))
        deck.append(make_card("adrenal_rage"))
        deck.append(make_card("last_stand"))
        deck.append(make_card("blood_for_power"))
    elif character == "twingunner":
        for _ in range(3):
            deck.append(make_card("strike"))
        for _ in range(3):
            deck.append(make_card("defend"))
        deck.append(make_card("quick_shot"))
        deck.append(make_card("double_shoot"))
        deck.append(make_card("snipe"))
    elif character == "blacksmith":
        for _ in range(3):
            deck.append(make_card("strike"))
        for _ in range(3):
            deck.append(make_card("defend"))
        deck.append(make_card("recast"))
        deck.append(make_card("drop_protect"))
        deck.append(make_card("copy"))
    elif character == "swordsman":
        for _ in range(3):
            deck.append(make_card("strike"))
        for _ in range(3):
            deck.append(make_card("defend"))
        deck.append(make_card("wind_blade"))
        deck.append(make_card("swords_random_stab"))
        deck.append(make_card("secret_damage"))
    elif character == "pharmacist":
        for _ in range(3):
            deck.append(make_card("strike"))
        for _ in range(3):
            deck.append(make_card("defend"))
        deck.append(make_card("poison_honor"))
        deck.append(make_card("poison_cloud"))
        deck.append(make_card("poison_inject"))
    elif character == "assassin":
        for _ in range(3):
            deck.append(make_card("strike"))
        for _ in range(3):
            deck.append(make_card("defend"))
        deck.append(make_card("hurt_attack"))
        deck.append(make_card("back_dagger_attack"))
        deck.append(make_card("sap"))
        deck.append(make_card("sneak"))
    elif character == "soldier":
        for _ in range(3):
            deck.append(make_card("strike"))
        for _ in range(3):
            deck.append(make_card("defend"))
        deck.append(make_card("shield_bash"))
        deck.append(make_card("defence_state"))
        deck.append(make_card("shield_equip"))
    elif character == "monk":
        for _ in range(3):
            deck.append(make_card("strike"))
        for _ in range(3):
            deck.append(make_card("defend"))
        deck.append(make_card("mind_clean"))
        deck.append(make_card("forget_can_happy"))
        deck.append(make_card("sin_box"))
    else:
        for _ in range(5):
            deck.append(make_card("strike"))
        for _ in range(4):
            deck.append(make_card("defend"))
        deck.append(make_card("bash"))
    return deck


REWARD_POOL = [k for k in CARD_LIBRARY if CARD_LIBRARY[k]["rarity"] not in ("starter", "exclusive", "curse", "mirror", "castle")]
CURSE_POOL = [k for k in CARD_LIBRARY if CARD_LIBRARY[k]["rarity"] == "curse"]

# ==== Lophis mode: real Talents ported from Call of Lophis (talent_1.lua). Offered as
# permanent, run-long picks after elites and the final boss instead of the game's original
# cross-run meta-currency tree (this engine has no persistent save-across-runs system). ====
TALENT_LIBRARY = {
    "health": dict(name="Constitution", desc="+5 Max HP.", stat="max_hp", amount=5),
    "energy": dict(name="Stamina", desc="+1 Energy per turn.", stat="max_energy", amount=1),
    "limit": dict(name="Willpower", desc="+1 hand size limit.", stat="talent_hand_limit", amount=1),
    "draw": dict(name="Dexterity", desc="+1 card drawn per turn.", stat="talent_draw", amount=1),
    "power": dict(name="Combat Strength", desc="+1 Strength.", stat="bonus_strength", amount=1),
    "lifesteal": dict(name="Life Drain", desc="Heal 10% of the physical damage you deal.",
                       stat="talent_lifesteal_pct", amount=10),
    "bless": dict(name="Magic Blessing", desc="Heal 1 HP whenever you play a Skill/Magic card.",
                   stat="talent_bless", amount=1),
    "strong": dict(name="Hardened Body", desc="Reduce all incoming physical damage by 1.",
                    stat="talent_strong", amount=1),
    "auto_cs": dict(name="Combat Instinct", desc="Gain 1 Counter at the end of your turn.",
                     stat="talent_guard_per_turn", amount=1),
}
