import random
import copy


class Enemy:
    def __init__(self, name, max_hp, moveset, elite=False, boss=False):
        self.name = name
        self.max_hp = max_hp
        self.hp = max_hp
        self.block = 0
        self.strength = 0
        self.vulnerable = 0
        self.weak = 0
        self.frail = 0
        self.poison = 0
        self.burning = 0  # queued damage that fires at the start of this enemy's next turn
        self.wound = 0    # Lophis-style Bleed stacks; a marker other cards react to, doesn't decay on its own
        self.moveset = moveset  # list of dicts: {type, damage/block/etc, weight}
        self.elite = elite
        self.boss = boss
        self.key = None
        self.revive_in = None  # used by Slime Swarm and self-reviving enemies (e.g. Skeleton)
        self.self_revives = False  # if True, this exact enemy stands back up after reviving
        self.revives_left = 0  # how many more times it can revive before staying dead
        self.revive_hp_frac = 0.5  # fraction of max_hp restored on self-revival
        self.flee_after_turn = None  # used only by the Gold Goblin encounter
        self.escaped = False
        self.guard_shield = False  # blocks the next single hit entirely (Castle Guard)
        self.rage_on_death = 0  # when this enemy dies, other alive enemies gain this much Strength
        self.death_processed = False  # prevents rage_on_death from double-firing
        self.current_move = None
        self.pick_move()

    def alive(self):
        return self.hp > 0

    def pick_move(self):
        weights = [m.get("weight", 1) for m in self.moveset]
        self.current_move = random.choices(self.moveset, weights=weights, k=1)[0]

    def take_damage(self, dmg):
        if self.guard_shield and dmg > 0:
            self.guard_shield = False
            return
        if self.block > 0:
            absorbed = min(self.block, dmg)
            self.block -= absorbed
            dmg -= absorbed
        if dmg > 0:
            self.hp -= dmg
        self.hp = max(0, self.hp)

    def intent_desc(self, ascension=0):
        mult = 1 + 0.05 * ascension
        m = self.current_move
        t = m["type"]
        if t == "attack":
            dmg = int(round((m["damage"] + self.strength) * mult))
            if self.weak > 0:
                dmg = int(dmg * 0.75)
            hits = m.get("hits", 1)
            if hits > 1:
                return f"Attack {dmg}x{hits}"
            return f"Attack {dmg}"
        if t == "defend":
            return f"Defend {m['block']}"
        if t == "buff":
            return "Buff"
        if t == "attack_defend":
            dmg = int(round((m["damage"] + self.strength) * mult))
            if self.weak > 0:
                dmg = int(dmg * 0.75)
            return f"Atk {dmg} + Def {m['block']}"
        if t == "weaken":
            return f"Weaken {m['amount']}"
        if t == "expose":
            return f"Expose {m['amount']} (Vulnerable)"
        if t == "steal":
            return f"Steal {m['amount']} gold"
        if t == "hex":
            base = f"Hex (Weak {m['weak']}, Vulnerable {m['vulnerable']}"
            if m.get("frail"):
                base += f", Frail {m['frail']}"
            return base + ")"
        if t == "heal":
            return f"Heal {m['amount']}"
        if t == "mirror_turn":
            return "Plays entire hand (∞ Energy)"
        return "???"


def make_enemy(key):
    e = ENEMY_TEMPLATES[key]
    enemy = Enemy(e["name"], e["hp"], copy.deepcopy(e["moves"]), elite=e.get("elite", False),
                  boss=e.get("boss", False))
    enemy.key = key
    if key == "lich":  # real passive: phylactery — revives once
        enemy.self_revives = True
        enemy.revives_left = 1
        enemy.revive_hp_frac = 0.4
    elif key == "crow_butler":  # real passive: shrugs off a hit whenever it turtles up
        enemy.guard_shield = True
    return enemy


ENEMY_TEMPLATES = {
    "slime": dict(name="Acid Slime", hp=42, moves=[
        dict(type="attack", damage=8, weight=2),
        dict(type="defend", block=6, weight=1),
    ]),
    "cultist": dict(name="Cultist", hp=48, moves=[
        dict(type="buff", weight=1),
        dict(type="attack", damage=7, weight=3),
    ]),
    "goblin": dict(name="Goblin Raider", hp=36, moves=[
        dict(type="attack", damage=6, hits=2, weight=2),
        dict(type="attack", damage=10, weight=1),
    ]),
    "jaw_worm": dict(name="Jaw Worm", hp=52, moves=[
        dict(type="attack", damage=11, weight=2),
        dict(type="attack_defend", damage=7, block=5, weight=1),
        dict(type="defend", block=9, weight=1),
    ]),
    "spider": dict(name="Venom Spider", hp=34, moves=[
        dict(type="attack", damage=6, weight=2),
        dict(type="weaken", amount=2, weight=1),
    ]),
    "brute": dict(name="Brute", hp=58, moves=[
        dict(type="attack", damage=13, weight=2),
        dict(type="attack_defend", damage=9, block=7, weight=1),
    ]),
    "knight_elite": dict(name="Iron Knight", hp=80, elite=True, moves=[
        dict(type="attack", damage=16, weight=2),
        dict(type="defend", block=12, weight=1),
        dict(type="buff", weight=1),
    ]),
    "wraith": dict(name="Wraith", hp=40, moves=[
        dict(type="attack", damage=7, weight=2),
        dict(type="expose", amount=2, weight=1),
    ]),
    "bandit": dict(name="Bandit", hp=44, moves=[
        dict(type="attack", damage=9, weight=2),
        dict(type="steal", amount=15, weight=1),
    ]),
    "specter": dict(name="Specter", hp=38, moves=[
        dict(type="attack", damage=6, weight=2),
        dict(type="hex", weak=2, vulnerable=1, weight=1),
    ]),
    "ooze": dict(name="Ooze", hp=50, moves=[
        dict(type="attack", damage=7, weight=1),
        dict(type="defend", block=10, weight=1),
        dict(type="weaken", amount=1, weight=1),
    ]),
    "ogre_elite": dict(name="Ogre", hp=95, elite=True, moves=[
        dict(type="attack", damage=20, weight=2),
        dict(type="attack_defend", damage=12, block=10, weight=1),
        dict(type="buff", weight=1),
    ]),
    "banshee_elite": dict(name="Banshee", hp=85, elite=True, moves=[
        dict(type="attack", damage=14, weight=2),
        dict(type="hex", weak=3, vulnerable=2, weight=1),
        dict(type="defend", block=10, weight=1),
    ]),
    "guardian_boss": dict(name="The Guardian", hp=150, boss=True, moves=[
        dict(type="attack", damage=12, hits=2, weight=2),
        dict(type="defend", block=15, weight=1),
        dict(type="attack", damage=22, weight=1),
    ]),
    "lich_boss": dict(name="The Lich", hp=135, boss=True, moves=[
        dict(type="attack", damage=15, weight=2),
        dict(type="weaken", amount=2, weight=1),
        dict(type="attack_defend", damage=10, block=12, weight=1),
    ]),
    "dragon_boss": dict(name="Young Dragon", hp=160, boss=True, moves=[
        dict(type="attack", damage=18, weight=2),
        dict(type="attack", damage=10, hits=3, weight=1),
        dict(type="buff", weight=1),
    ]),

    # ---- ACT 2 ----
    "revenant": dict(name="Revenant", hp=64, moves=[
        dict(type="attack", damage=12, weight=2),
        dict(type="heal", amount=10, weight=1),
    ]),
    "golem": dict(name="Stone Golem", hp=100, moves=[
        dict(type="attack", damage=16, weight=2),
        dict(type="defend", block=14, weight=1),
    ]),
    "cursed_knight": dict(name="Cursed Knight", hp=80, moves=[
        dict(type="attack_defend", damage=13, block=8, weight=2),
        dict(type="hex", weak=2, vulnerable=2, frail=1, weight=1),
    ]),
    "shade_elite": dict(name="Shade", hp=120, elite=True, moves=[
        dict(type="attack", damage=18, weight=2),
        dict(type="hex", weak=3, vulnerable=3, weight=1),
        dict(type="heal", amount=15, weight=1),
    ]),
    "warlord_elite": dict(name="Warlord", hp=130, elite=True, moves=[
        dict(type="attack", damage=15, hits=2, weight=2),
        dict(type="buff", weight=1),
        dict(type="defend", block=16, weight=1),
    ]),
    "hydra_boss": dict(name="The Hydra", hp=220, boss=True, moves=[
        dict(type="attack", damage=14, hits=2, weight=2),
        dict(type="attack", damage=26, weight=1),
        dict(type="heal", amount=20, weight=1),
        dict(type="hex", weak=2, vulnerable=2, weight=1),
    ]),

    # ---- Special: Slime Swarm encounter (spawned directly, not via FIGHT_POOLS) ----
    "lophis_slime": dict(name="Slime", hp=18, moves=[
        dict(type="attack", damage=5, weight=1),
    ]),

    # ---- Special: Gold Goblin encounter (spawned directly, not via FIGHT_POOLS) ----
    "gold_goblin": dict(name="Gold Goblin", hp=22, moves=[
        dict(type="attack", damage=4, weight=1),
    ]),

    # ---- Special: The Castle encounter (spawned directly, not via FIGHT_POOLS) ----
    "skeleton": dict(name="Skeleton", hp=24, moves=[
        dict(type="attack", damage=7, weight=1),
    ]),
    "castle_guard": dict(name="Castle Guard", hp=45, moves=[
        dict(type="attack", damage=13, weight=2),
        dict(type="defend", block=8, weight=1),
    ]),
    "enraged_duck": dict(name="Enraged Duck", hp=14, moves=[
        dict(type="attack", damage=5, weight=1),
    ]),

    # ==== Lophis mode: real bosses ported from Call of Lophis (monster.lua / battle.lua) ====
    "crow_butler": dict(name="Crow Butler", hp=120, boss=True, moves=[
        dict(type="attack", damage=11, hits=3, weight=2),
        dict(type="hex", weak=2, vulnerable=1, weight=1),
        dict(type="defend", block=12, weight=1),
    ]),  # real passive: immune to one fatal hit per turn -> modeled as guard_shield, set at spawn
    "butcher": dict(name="Butcher", hp=140, boss=True, moves=[
        dict(type="attack", damage=22, weight=2),
        dict(type="attack", damage=12, hits=2, weight=2),
        dict(type="buff", weight=1),
    ]),  # real passive: bloodthirsty (hits harder as it takes damage) + immune to Bleed
    "goblin_king": dict(name="Goblin King", hp=110, boss=True, moves=[
        dict(type="attack", damage=14, weight=2),
        dict(type="steal", amount=25, weight=1),
        dict(type="attack_defend", damage=10, block=10, weight=1),
    ]),
    "green_dragon": dict(name="Green Dragon", hp=190, boss=True, moves=[
        dict(type="attack", damage=18, weight=2),
        dict(type="heal", amount=18, weight=1),
        dict(type="attack", damage=10, hits=2, weight=1),
    ]),  # real passive: lifeblood (regenerates each turn) -> modeled via frequent Heal move
    "cyclops": dict(name="Cyclops", hp=155, boss=True, moves=[
        dict(type="attack", damage=16, weight=3),
        dict(type="attack", damage=28, weight=1),
        dict(type="defend", block=14, weight=1),
    ]),  # real passive: soul_angry (rage builds, hits harder late) -> approximated with a big hit option
    "lich": dict(name="Lich", hp=90, boss=True, moves=[
        dict(type="attack", damage=13, weight=2),
        dict(type="hex", weak=3, vulnerable=2, weight=1),
        dict(type="weaken", amount=2, weight=1),
    ]),  # real passive: phylactery (revives once) -> modeled via self_revives below
    "vampire_lord": dict(name="Vampire Lord", hp=130, boss=True, moves=[
        dict(type="attack", damage=15, weight=2),
        dict(type="heal", amount=12, weight=1),
        dict(type="attack", damage=9, hits=2, weight=1),
    ]),  # real passive: lifesteal on hit -> approximated via frequent Heal move
    "death_knight": dict(name="Death Knight", hp=145, boss=True, moves=[
        dict(type="attack", damage=17, weight=2),
        dict(type="hex", weak=2, vulnerable=2, frail=1, weight=1),
        dict(type="defend", block=13, weight=1),
    ]),  # real passive: shackles (extra debuffs)
}

FIGHT_POOLS = {
    "normal": ["slime", "cultist", "goblin", "jaw_worm", "spider", "brute", "wraith", "bandit", "specter", "ooze"],
    "elite": ["knight_elite", "ogre_elite", "banshee_elite"],
    "boss": ["guardian_boss", "lich_boss", "dragon_boss"],
}

ACT2_FIGHT_POOLS = {
    "normal": ["revenant", "golem", "cursed_knight", "brute", "specter", "ooze", "bandit"],
    "elite": ["shade_elite", "warlord_elite"],
    "boss": ["hydra_boss"],
}

# Lophis mode: same normal/elite trash pool (this engine doesn't port the game's ~85 regular
# monster cards), but the boss pool is swapped for the 8 real Call of Lophis bosses above.
LOPHIS_FIGHT_POOLS = {
    "normal": FIGHT_POOLS["normal"],
    "elite": FIGHT_POOLS["elite"],
    "boss": ["crow_butler", "butcher", "goblin_king", "green_dragon", "cyclops", "lich",
             "vampire_lord", "death_knight"],
}
