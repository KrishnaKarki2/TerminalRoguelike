import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import random
import pickle
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.markup import escape

from player import Player
from map import GameMap, NODE_TYPES
from enemies import make_enemy, FIGHT_POOLS, ACT2_FIGHT_POOLS, LOPHIS_FIGHT_POOLS, Enemy
from cards import make_card, REWARD_POOL, CARD_LIBRARY, CLASSES, upgrade_card, is_upgradeable, CURSE_POOL, upgrade_offers_path_choice, TALENT_LIBRARY
from combat_cli import Combat, TYPE_COLOR
from relics import RELIC_LIBRARY, RELIC_POOL, RELIC_POOL_ACT1
from potions import POTION_LIBRARY, POTION_POOL
from ascii_art import SHOW_ASCII_ART, get_class_art, SHOW_ATTACK_ANIMATIONS, play_attack_animation

console = Console()

SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "savegame.pkl")

ROW_LABELS = {"fight": "Fight", "elite": "Elite", "rest": "Rest Site", "shop": "Shop", "boss": "BOSS",
              "treasure": "Treasure", "event": "Event", "gauntlet": "Gauntlet"}
ROW_COLOR = {"fight": "red", "elite": "magenta", "rest": "green", "shop": "yellow", "boss": "bold red",
             "treasure": "gold1", "event": "purple", "gauntlet": "orange3"}


def prompt(msg, choices=None):
    while True:
        raw = console.input(msg).strip().lower()
        if choices is None or raw in choices:
            return raw
        console.print(f"[red]Invalid choice.[/red] Options: {', '.join(choices)}")


def choose_character(game_mode="normal"):
    console.clear()
    console.rule("[bold]Choose your character[/bold]")
    pool = "lophis" if game_mode == "lophis" else "normal"
    keys = [k for k in CLASSES if CLASSES[k].get("pool", "normal") == pool]

    if SHOW_ASCII_ART:
        panels = []
        for i, key in enumerate(keys):
            art = get_class_art(key)
            body = f"[grey70]{escape(art.strip(chr(10)))}[/grey70]" if art else "[grey50](no art)[/grey50]"
            panels.append(Panel(body, title=f"[{i + 1}] {CLASSES[key]['name']}", border_style="cyan", width=22))
        console.print(Columns(panels))

    table = Table()
    table.add_column("#")
    table.add_column("Class")
    table.add_column("HP")
    table.add_column("Description")
    for i, key in enumerate(keys):
        info = CLASSES[key]
        table.add_row(str(i + 1), info["name"], str(info["max_hp"]), info["desc"])
    console.print(table)
    choice = prompt("Pick a class #: ", choices=[str(i + 1) for i in range(len(keys))])
    return keys[int(choice) - 1]


def choose_seed():
    console.clear()
    console.rule("[bold]Choose your seed[/bold]")
    console.print("Pick a fixed seed (1-20) for a reproducible run, or randomize completely.")
    console.print("[grey62]The same seed + same choices always produces the same run.[/grey62]")
    choice = prompt("Enter a seed number 1-20, or 'r' for random: ",
                     choices=[str(i) for i in range(1, 21)] + ["r"])
    if choice == "r":
        seed_val = random.randint(0, 999_999_999)
    else:
        seed_val = int(choice)
    random.seed(seed_val)
    console.print(f"[grey62]Using seed: {seed_val}[/grey62]")
    return seed_val


def choose_ascension():
    console.clear()
    console.rule("[bold]Choose Ascension Level[/bold]")
    console.print("Higher levels scale enemy HP (+8%/level) and damage (+5%/level). 0 = normal difficulty.")
    choice = prompt("Ascension level (0-10): ", choices=[str(i) for i in range(0, 11)])
    level = int(choice)
    if level > 0:
        console.print(f"[red]Ascension {level}: enemies +{level*8}% HP, +{level*5}% damage.[/red]")
    return level


def choose_game_mode():
    console.clear()
    console.rule("[bold]Choose Game Mode[/bold]")
    console.print("1) Normal — Energy resets to your max every turn.")
    console.print("2) [gold1]Lophis Style[/gold1] — unspent Energy carries over into your next turn "
                   "(capped at 4x your max), so you can bank up for a huge attack.")
    console.print("3) [cyan]Retain Mode[/cyan] — cards stay in your hand at end of turn instead of "
                   "being discarded. Use 'x' during combat to discard cards you don't want.")
    choice = prompt("Choose mode #: ", choices=["1", "2", "3"])
    if choice == "2":
        return "lophis"
    if choice == "3":
        return "retain"
    return "normal"


class Game:
    def __init__(self):
        self.seed = choose_seed()
        game_mode = choose_game_mode()
        character = choose_character(game_mode)
        ascension = choose_ascension()
        self.player = Player(character, ascension, game_mode)
        self.act = 1
        self.game_map = GameMap(lophis=(game_mode == "lophis"))

    @classmethod
    def load_or_new(cls):
        if os.path.exists(SAVE_PATH):
            console.clear()
            console.rule("[bold]Saved Run Found[/bold]")
            choice = prompt("Continue your saved run? (y/n): ", choices=["y", "n"])
            if choice == "y":
                try:
                    with open(SAVE_PATH, "rb") as f:
                        data = pickle.load(f)
                    game = cls.__new__(cls)
                    game.player = data["player"]
                    game.game_map = data["game_map"]
                    game.act = data["act"]
                    game.seed = data["seed"]
                    console.print("[green]Run loaded![/green]")
                    console.input("Press Enter to continue...")
                    return game
                except Exception:
                    console.print("[red]Save file was corrupted — starting fresh.[/red]")
                    console.input("Press Enter to continue...")
            os.remove(SAVE_PATH)
        return cls()

    def save_game(self):
        data = {"player": self.player, "game_map": self.game_map, "act": self.act, "seed": self.seed}
        with open(SAVE_PATH, "wb") as f:
            pickle.dump(data, f)
        console.print("[green]Run saved! Quit anytime — pick 'Continue' next launch to resume here.[/green]")

    def current_pools(self):
        if self.player.game_mode == "lophis":
            return LOPHIS_FIGHT_POOLS
        return FIGHT_POOLS if self.act == 1 else ACT2_FIGHT_POOLS

    def relic_pool(self):
        return RELIC_POOL_ACT1 if self.act == 1 else RELIC_POOL

    # ---------------- MAP ----------------
    def show_map(self):
        console.clear()
        console.rule("[bold]The Spire[/bold]")
        asc_txt = f"  Asc: {self.player.ascension}" if self.player.ascension else ""
        mode_txt = "  [gold1]Lophis Style[/gold1]" if self.player.game_mode == "lophis" else ""
        hp_txt = (f"[{CLASSES[self.player.character]['name']}]  Act {self.act}  Seed: {self.seed}{asc_txt}{mode_txt}  "
                  f"HP: [red]{self.player.hp}/{self.player.max_hp}[/red]  "
                  f"Gold: [yellow]{self.player.gold}[/yellow]  Deck: {len(self.player.deck)} cards")
        console.print(Panel(hp_txt, border_style="green"))

        options = self.game_map.get_current_options()
        table = Table(title="Choose your next stop")
        table.add_column("#")
        table.add_column("Type")
        for i, node in enumerate(options):
            col = ROW_COLOR[node.ntype]
            table.add_row(str(i + 1), f"[{col}]{ROW_LABELS[node.ntype]}[/{col}]")
        console.print(table)
        return options

    def map_loop(self):
        while True:
            options = self.show_map()
            choice = prompt("Pick a node number, 'm' for full map, 's' to save & quit, or 'd' to view deck: ",
                             choices=[str(i + 1) for i in range(len(options))] + ["m", "d", "s"])
            if choice == "d":
                self.show_deck()
                continue
            if choice == "m":
                self.render_full_map()
                continue
            if choice == "s":
                self.save_game()
                console.input("Press Enter to exit...")
                sys.exit(0)
            node = options[int(choice) - 1]
            result = self.visit_node(node)
            if result == "dead":
                return False
            if result == "won_game":
                return True

    def render_full_map(self):
        console.clear()
        console.rule("[bold]Full Map[/bold]")
        console.print("[grey62]< > = available now    ( ) = visited    dim = locked[/grey62]")
        options = self.game_map.get_current_options()
        letter = {"fight": "F", "elite": "E", "rest": "R", "shop": "S", "boss": "B",
                  "treasure": "T", "event": "?", "gauntlet": "G"}
        for r in reversed(range(len(self.game_map.rows))):
            row = self.game_map.rows[r]
            parts = []
            for node in row:
                ch = letter[node.ntype]
                col = ROW_COLOR[node.ntype]
                if node.visited:
                    parts.append(f"[grey50]({ch})[/grey50]")
                elif node in options:
                    parts.append(f"[{col}]<{ch}>[/{col}]")
                else:
                    parts.append(f"[grey35] {ch} [/grey35]")
            row_label = "Boss " if r == len(self.game_map.rows) - 1 else (
                "Start" if r == 0 else f"Row{r:>2} ")
            console.print(f"{row_label} " + "  ".join(parts))
        console.input("Press Enter to go back...")

    def show_deck(self):
        console.clear()
        table = Table(title="Your Deck")
        table.add_column("Name")
        table.add_column("Cost")
        table.add_column("Type")
        table.add_column("Effect")
        for card in self.player.deck:
            color = TYPE_COLOR[card["type"]]
            table.add_row(f"[{color}]{card['name']}[/{color}]", str(card["cost"]), card["type"], card["desc"])
        console.print(table)

        if self.player.relics:
            rtable = Table(title="Relics")
            rtable.add_column("Name")
            rtable.add_column("Effect")
            for rid in self.player.relics:
                r = RELIC_LIBRARY[rid]
                rtable.add_row(f"[magenta]{r['name']}[/magenta]", r["desc"])
            console.print(rtable)

        if self.player.potions:
            ptable = Table(title="Potions")
            ptable.add_column("Name")
            ptable.add_column("Effect")
            for pid in self.player.potions:
                p = POTION_LIBRARY[pid]
                ptable.add_row(f"[green]{p['name']}[/green]", p["desc"])
            console.print(ptable)

        console.input("Press Enter to go back...")

    def spawn_enemy(self, key):
        e = make_enemy(key)
        mult = 1 + 0.08 * getattr(self.player, "ascension", 0)
        e.max_hp = int(round(e.max_hp * mult))
        e.hp = e.max_hp
        return e

    def spawn_slime_swarm(self):
        """4 slots total: 2 start filled with Slimes, 2 start empty and immediately available."""
        slots = []
        for i in range(4):
            e = self.spawn_enemy("lophis_slime")
            if i >= 2:
                e.hp = 0
                e.revive_in = 0
            slots.append(e)
        return slots

    def spawn_gold_goblin(self):
        e = self.spawn_enemy("gold_goblin")
        e.flee_after_turn = 3  # flees on turn 3 if still alive
        return [e]

    def spawn_mirror(self):
        mirror = Enemy("Your Reflection", self.player.hp, [dict(type="mirror_turn", weight=1)])
        return [mirror]

    def spawn_skeleton(self):
        e = self.spawn_enemy("skeleton")
        e.self_revives = True
        e.revives_left = 2
        return e

    def spawn_castle_guard(self):
        e = self.spawn_enemy("castle_guard")
        e.guard_shield = True
        return e

    def spawn_enraged_duck(self):
        e = self.spawn_enemy("enraged_duck")
        e.rage_on_death = 3
        return e

    def do_castle(self):
        console.clear()
        console.rule("[bold white]The Castle[/bold white]")
        console.print("Four trials guard this ruined keep. Clear them all for a legendary blade.")
        console.input("Press Enter to begin...")

        stages = [
            ("Stage 1: The Crypt", lambda: [self.spawn_skeleton()]),
            ("Stage 2: The Gatehouse", lambda: [self.spawn_castle_guard()]),
            ("Stage 3: The Pond", lambda: [self.spawn_enraged_duck() for _ in range(4)]),
            ("Stage 4: The Throne Room", lambda: [self.spawn_castle_guard(), self.spawn_skeleton()]),
        ]

        for i, (title, spawner) in enumerate(stages):
            console.clear()
            console.print(Panel(f"[bold white]{title}[/bold white] ({i + 1}/4)", border_style="white"))
            console.input("Press Enter to continue...")
            enemies = spawner()
            result = self.run_combat(enemies, boss=False)
            if result != "ok":
                return result

        console.clear()
        console.print(Panel("[gold1]You have conquered The Castle![/gold1]", border_style="gold1"))
        blade = make_card("reapers_scythe")
        self.player.deck.append(blade)
        console.print(f"[gold1]Gained: {blade['name']}[/gold1] — {blade['desc']}")
        console.input("Press Enter to continue...")
        return "ok"

    def visit_node(self, node):
        self.game_map.choose(node)
        pools = self.current_pools()
        if node.ntype == "fight":
            roll = random.random()
            if roll < 0.12:
                enemies = self.spawn_slime_swarm()
                return self.run_combat(enemies, boss=False, slime_swarm=True)
            elif roll < 0.22:
                enemies = self.spawn_gold_goblin()
                return self.run_combat(enemies, boss=False, gold_goblin=True)
            pool = pools["normal"]
            enemies = [self.spawn_enemy(random.choice(pool))]
            if random.random() < 0.4:
                enemies.append(self.spawn_enemy(random.choice(pool)))
            return self.run_combat(enemies, boss=False)
        elif node.ntype == "elite":
            return self.run_combat([self.spawn_enemy(random.choice(pools["elite"]))], boss=False, elite=True)
        elif node.ntype == "boss":
            result = self.run_combat([self.spawn_enemy(random.choice(pools["boss"]))], boss=True)
            if result == "won_game" and self.act == 1 and self.player.game_mode != "lophis":
                self.start_act2()
                return "ok"
            return result
        elif node.ntype == "rest":
            self.do_rest()
        elif node.ntype == "shop":
            self.do_shop()
        elif node.ntype == "treasure":
            self.do_treasure()
        elif node.ntype == "event":
            result = self.do_event()
            if result:
                return result
        elif node.ntype == "gauntlet":
            return self.do_gauntlet(pools)
        return "ok"

    def do_gauntlet(self, pools):
        console.clear()
        console.rule("[orange3]Gauntlet[/orange3]")
        console.print("Two waves of enemies, back to back. Clear both for a bonus reward.")
        console.input("Press Enter to begin...")

        pool = pools["normal"]
        enemies1 = [self.spawn_enemy(random.choice(pool))]
        result1 = self.run_combat(enemies1, boss=False)
        if result1 != "ok":
            return result1

        console.clear()
        console.print(Panel("[orange3]Wave 1 cleared! The second wave approaches...[/orange3]", border_style="orange3"))
        console.input("Press Enter to continue...")

        enemies2 = [self.spawn_enemy(random.choice(pool))]
        if random.random() < 0.6:
            enemies2.append(self.spawn_enemy(random.choice(pool)))
        result2 = self.run_combat(enemies2, boss=False)
        if result2 == "ok":
            bonus = random.randint(40, 70)
            self.player.gold += bonus
            console.print(f"[gold1]Gauntlet cleared! Bonus {bonus} gold.[/gold1]")
            console.input("Press Enter to continue...")
        return result2

    def start_act2(self):
        self.act = 2
        console.clear()
        console.rule("[bold red]ACT 2[/bold red]")
        console.print("You descend deeper into the Spire. The air grows heavier, and the enemies grow fiercer...")
        gold_bonus = 50
        self.player.gold += gold_bonus
        console.print(f"[yellow]+{gold_bonus} gold for surviving Act 1.[/yellow]")

        avail = [r for r in RELIC_POOL if r not in self.player.relics]
        random.shuffle(avail)
        offer = avail[:3]
        if offer:
            table = Table(title="Choose a relic for the journey ahead")
            table.add_column("#")
            table.add_column("Name")
            table.add_column("Effect")
            for i, rid in enumerate(offer):
                r = RELIC_LIBRARY[rid]
                table.add_row(str(i + 1), f"[magenta]{r['name']}[/magenta]", r["desc"])
            console.print(table)
            choices = [str(i + 1) for i in range(len(offer))] + ["s"]
            pick = prompt("Pick relic # or 's' to skip: ", choices=choices)
            if pick != "s":
                self.player.relics.append(offer[int(pick) - 1])
                console.print("[magenta]Relic acquired![/magenta]")

        console.input("Press Enter to descend into Act 2...")
        self.game_map = GameMap()

    # ---------------- TREASURE ----------------
    def do_treasure(self):
        console.clear()
        console.rule("[gold1]Treasure Room[/gold1]")
        gold_gain = random.randint(20, 40)
        self.player.gold += gold_gain
        console.print(f"[yellow]Found {gold_gain} gold![/yellow]")
        avail = [r for r in self.relic_pool() if r not in self.player.relics]
        if avail:
            rid = random.choice(avail)
            self.player.relics.append(rid)
            r = RELIC_LIBRARY[rid]
            console.print(f"[magenta]Found relic: {r['name']}[/magenta] — {r['desc']}")
        else:
            console.print("[grey62]The chest holds nothing else of note.[/grey62]")
        console.input("Press Enter to continue...")

    # ---------------- EVENT ----------------
    EVENTS = [
        dict(title="Ancient Shrine", desc="A worn shrine hums with old power.",
             options=[("Pray and lose 8 HP for a free relic", "pray"), ("Leave quietly", "leave")]),
        dict(title="Wandering Merchant", desc="A merchant offers a discounted potion for 25 gold.",
             options=[("Buy the potion (25g)", "buy_potion"), ("Decline", "leave")]),
        dict(title="Strange Trial", desc="A spectral challenger offers a duel for a reward.",
             options=[("Accept the duel", "duel"), ("Walk away", "leave")]),
        dict(title="Cursed Altar", desc="An altar promises to purge a card from your deck, at a cost.",
             options=[("Remove a card (lose 5 HP)", "remove_card"), ("Leave", "leave")]),
        dict(title="Golden Idol", desc="A golden idol sits on a pressure plate. Tempting, but risky.",
             options=[("Grab it (+60 gold, trigger a trap for 10 damage)", "idol"), ("Leave it", "leave")]),
        dict(title="Mysterious Fountain", desc="Its waters shimmer, promising to mend all wounds — at a cost.",
             options=[("Drink (full heal, -5 max HP permanently)", "fountain"), ("Walk past", "leave")]),
        dict(title="Abandoned Camp", desc="A hastily abandoned campsite. Someone left their supplies.",
             options=[("Search the camp (find 2 potions)", "free_potions"), ("Move on", "leave")]),
        dict(title="Weary Traveler", desc="A traveler offers you a relic in exchange for gold to get home.",
             options=[("Give 40 gold for the relic", "gold_for_relic"), ("Refuse", "leave")]),
        dict(title="Card Vendor", desc="A vendor offers to sharpen one of your cards for a fee.",
             options=[("Pay 45 gold to upgrade a card", "vendor_upgrade"), ("Decline", "leave")]),
        dict(title="Beggar", desc="A beggar asks for a little gold, promising a blessing in return.",
             options=[("Give 10 gold (+10 HP blessing)", "beggar"), ("Ignore", "leave")]),
        dict(title="Whispering Statue", desc="The statue offers to erase a memory — a card — from your deck. Free of charge.",
             options=[("Remove a card (free)", "free_remove"), ("Leave", "leave")]),
        dict(title="Locked Chest", desc="A sturdy chest, maybe trapped, maybe not.",
             options=[("Open it", "trap_chest"), ("Leave it shut", "leave")]),
        dict(title="Old Library", desc="Dusty tomes line the shelves. One might teach you something useful.",
             options=[("Study a tome (learn a free card)", "study_tome"), ("Leave", "leave")]),
        dict(title="Sacrificial Circle", desc="Blood magic hums in the air, promising great reward for great pain.",
             options=[("Sacrifice 15 HP for 2 relics", "sacrifice_relics"), ("Step away", "leave")]),
        dict(title="Lost Merchant's Stash", desc="A hidden stash of alchemical supplies.",
             options=[("Take a potion", "free_potion"), ("Leave it", "leave")]),
        dict(title="Rigged Coinflip", desc="A shady figure offers a 50/50 gamble: double your bet or lose it.",
             options=[("Bet 30 gold", "coinflip"), ("Walk away", "leave")]),
        dict(title="Ambush!", desc="Bandits block the path ahead, demanding a toll.",
             options=[("Pay 20 gold to sneak past", "pay_sneak"), ("Fight your way through", "duel")]),
        dict(title="Mirror of Fate", desc="The mirror offers to swap one of your cards for a random new one.",
             options=[("Swap a card", "mirror_swap"), ("Leave", "leave")]),
        dict(title="Ritual Grounds", desc="Strange sigils on the ground hum with free-flowing magic.",
             options=[("Upgrade a card (free)", "free_upgrade"), ("Leave", "leave")]),
        dict(title="Traveling Blacksmith", desc="A blacksmith offers to remove a card from your deck for a fee.",
             options=[("Pay 60 gold to remove a card", "vendor_remove"), ("Decline", "leave")]),
        dict(title="Pandora's Box", desc="An ornate box promises great power... if you dare open it.",
             options=[("Open it (gain a powerful relic, but also a Curse)", "pandora"), ("Leave it sealed", "leave")]),
        dict(title="Forbidden Tome", desc="A tome of forbidden knowledge. Reading it grants a rare technique — but such knowledge always has a price.",
             options=[("Read it (learn a rare card, risk a Curse)", "forbidden_tome"), ("Leave it closed", "leave")]),
        dict(title="Mirror Chamber", desc="A still pool reflects an exact copy of yourself, deck and all. "
                                           "It has infinite Energy, but losing costs you nothing.",
             options=[("Fight your reflection", "mirror_fight"), ("Walk past", "leave")]),
        dict(title="The Castle", desc="An ancient keep looms, said to hold four trials and a legendary "
                                       "blade for those who conquer them all.",
             options=[("Enter the Castle", "castle_trial"), ("Leave it be", "leave")]),
    ]

    # ==== Lophis mode: real events ported from Call of Lophis (fate_event.lua) ====
    LOPHIS_EVENTS = [
        dict(title="Littleman!", desc="You stumble on a den of little folk. They give you a gift and "
                                        "ask you not to tell anyone about this place.",
             options=[("Accept the gift (free card)", "study_tome"), ("Leave", "leave")]),
        dict(title="Forest Sprite", desc="You wander into a small sprite habitat by accident. They give "
                                          "you a gift and ask you not to tell anyone about this place.",
             options=[("Accept the gift (free card)", "study_tome"), ("Leave", "leave")]),
        dict(title="Bounty Hunter", desc="An old bounty hunter lives in a shabby hut. He's happy for the "
                                          "company and offers to teach you a trick or two.",
             options=[("Learn a trick (free card)", "study_tome"), ("Leave", "leave")]),
        dict(title="Martial Artist", desc="You meet a martial artist in orange dress. After a short talk, "
                                           "he offers to teach you some martial arts.",
             options=[("Train with him (free card)", "study_tome"), ("Leave", "leave")]),
        dict(title="Witch", desc="The owner of this house is a witch. She'll show you some of her magic "
                                  "— if you lend her some coin.",
             options=[("Pay 30 gold to learn a spell", "buy_card_event"), ("Leave", "leave")]),
        dict(title="Alchemist", desc="The room reeks of chemicals. An alchemist eyes you: "
                                      "\"Would you like to try one of my potions? I just made a batch.\"",
             options=[("Pay 30 gold for a concoction", "buy_card_event"), ("Leave", "leave")]),
        dict(title="Traveler From East", desc="A traveler in Oriental dress sits in the tavern, drinking "
                                               "and telling stories of a distant land.",
             options=[("Buy him a drink (30 gold, choose 1 of 2 cards)", "buy_choose_card"), ("Leave", "leave")]),
        dict(title="Statue of Light", desc="The statue scatters the nearby darkness, and everything around "
                                            "it is revived. Your soul feels purified.",
             options=[("Touch the statue (full heal, free)", "full_heal_free"), ("Leave", "leave")]),
        dict(title="Moon Well", desc="A moonlit well shines bright. Its water looks sweet.",
             options=[("Drink (heal 20 HP)", "heal_20"), ("Leave", "leave")]),
        dict(title="Ambush!", desc="Bandits leap from the shadows — there's no talking your way out of this one.",
             options=[("Fight", "duel")]),
        dict(title="Treasure", desc="You spot a chest in the shadows not far away.",
             options=[("Open it", "treasure_gamble"), ("Leave", "leave")]),
        dict(title="Injured Giant", desc="A giant lies wounded in a cave, groaning in pain. It might be "
                                          "grateful if you help — or it might just be hungry.",
             options=[("Help it (fight, then reward)", "duel"), ("Leave", "leave")]),
    ]

    def do_event(self):
        pool = self.LOPHIS_EVENTS if self.player.game_mode == "lophis" else self.EVENTS
        ev = random.choice(pool)
        console.clear()
        console.rule(f"[purple]{ev['title']}[/purple]")
        console.print(ev["desc"])
        for i, (label, _) in enumerate(ev["options"]):
            console.print(f"{i + 1}. {label}")
        choice = prompt("Choose #: ", choices=[str(i + 1) for i in range(len(ev["options"]))])
        action = ev["options"][int(choice) - 1][1]

        if action == "pray":
            self.player.hp = max(1, self.player.hp - 8)
            avail = [r for r in self.relic_pool() if r not in self.player.relics]
            if avail:
                rid = random.choice(avail)
                self.player.relics.append(rid)
                console.print(f"[magenta]Gained relic: {RELIC_LIBRARY[rid]['name']}[/magenta]")
            else:
                console.print("[grey62]Nothing happens.[/grey62]")
            console.input("Press Enter to continue...")
        elif action == "buy_potion":
            if self.player.gold >= 25 and len(self.player.potions) < self.player.max_potions:
                self.player.gold -= 25
                pid = random.choice(POTION_POOL)
                self.player.potions.append(pid)
                console.print(f"[green]Received {POTION_LIBRARY[pid]['name']}![/green]")
            else:
                console.print("[red]Not enough gold, or your potion belt is full.[/red]")
            console.input("Press Enter to continue...")
        elif action == "duel":
            return self.run_combat([self.spawn_enemy(random.choice(self.current_pools()["normal"]))], boss=False)
        elif action == "remove_card":
            if len(self.player.deck) <= 5:
                console.print("[grey62]Your deck is too thin to risk it.[/grey62]")
                console.input("Press Enter to continue...")
            else:
                self.player.hp = max(1, self.player.hp - 5)
                self.do_remove_card()
        elif action == "idol":
            self.player.gold += 60
            self.player.hp = max(1, self.player.hp - 10)
            console.print("[yellow]Gained 60 gold[/yellow] but [red]took 10 damage[/red] from the trap!")
            console.input("Press Enter to continue...")
        elif action == "fountain":
            self.player.hp = self.player.max_hp
            self.player.max_hp = max(10, self.player.max_hp - 5)
            self.player.hp = min(self.player.hp, self.player.max_hp)
            console.print(f"[cyan]Fully healed, but max HP is now {self.player.max_hp}.[/cyan]")
            console.input("Press Enter to continue...")
        elif action == "free_potions":
            gained = []
            for _ in range(2):
                if len(self.player.potions) < self.player.max_potions:
                    pid = random.choice(POTION_POOL)
                    self.player.potions.append(pid)
                    gained.append(POTION_LIBRARY[pid]["name"])
            if gained:
                console.print(f"[green]Found: {', '.join(gained)}[/green]")
            else:
                console.print("[grey62]Your potion belt is already full.[/grey62]")
            console.input("Press Enter to continue...")
        elif action == "gold_for_relic":
            if self.player.gold >= 40:
                avail = [r for r in self.relic_pool() if r not in self.player.relics]
                if avail:
                    self.player.gold -= 40
                    rid = random.choice(avail)
                    self.player.relics.append(rid)
                    console.print(f"[magenta]Received relic: {RELIC_LIBRARY[rid]['name']}[/magenta]")
                else:
                    console.print("[grey62]The traveler has nothing left to offer.[/grey62]")
            else:
                console.print("[red]Not enough gold.[/red]")
            console.input("Press Enter to continue...")
        elif action == "vendor_upgrade":
            if self.player.gold >= 45:
                self.player.gold -= 45
                self.do_upgrade_card()
            else:
                console.print("[red]Not enough gold.[/red]")
                console.input("Press Enter to continue...")
        elif action == "vendor_remove":
            if self.player.gold >= 60:
                if len(self.player.deck) <= 5:
                    console.print("[grey62]Your deck is too thin to risk it.[/grey62]")
                    console.input("Press Enter to continue...")
                else:
                    self.player.gold -= 60
                    self.do_remove_card()
            else:
                console.print("[red]Not enough gold.[/red]")
                console.input("Press Enter to continue...")
        elif action == "beggar":
            if self.player.gold >= 10:
                self.player.gold -= 10
                self.player.hp = min(self.player.max_hp, self.player.hp + 10)
                console.print("[green]The beggar blesses you. +10 HP.[/green]")
            else:
                console.print("[red]Not enough gold.[/red]")
            console.input("Press Enter to continue...")
        elif action == "free_remove":
            self.do_remove_card()
        elif action == "trap_chest":
            if random.random() < 0.5:
                gold_gain = random.randint(30, 60)
                self.player.gold += gold_gain
                console.print(f"[yellow]The chest was safe! +{gold_gain} gold.[/yellow]")
                console.input("Press Enter to continue...")
            else:
                console.print("[red]It's a trap! Enemies emerge![/red]")
                console.input("Press Enter to continue...")
                return self.run_combat([self.spawn_enemy(random.choice(self.current_pools()["normal"]))], boss=False)
        elif action == "study_tome":
            pool = REWARD_POOL[:]
            random.shuffle(pool)
            options_cards = [make_card(c) for c in pool[:3]]
            table = Table(title="Choose a card to learn")
            table.add_column("#")
            table.add_column("Name")
            table.add_column("Cost")
            table.add_column("Effect")
            for i, card in enumerate(options_cards):
                color = TYPE_COLOR[card["type"]]
                table.add_row(str(i + 1), f"[{color}]{card['name']}[/{color}]", str(card["cost"]), card["desc"])
            console.print(table)
            pick = prompt("Choose # or 's' to skip: ", choices=[str(i + 1) for i in range(len(options_cards))] + ["s"])
            if pick != "s":
                self.player.deck.append(options_cards[int(pick) - 1])
                console.print("[green]Card added to deck![/green]")
            console.input("Press Enter to continue...")
        elif action == "sacrifice_relics":
            self.player.hp = max(1, self.player.hp - 15)
            avail = [r for r in self.relic_pool() if r not in self.player.relics]
            random.shuffle(avail)
            gained = avail[:2]
            self.player.relics.extend(gained)
            if gained:
                names = ", ".join(RELIC_LIBRARY[r]["name"] for r in gained)
                console.print(f"[magenta]Gained: {names}[/magenta]")
            else:
                console.print("[grey62]Nothing left to gain.[/grey62]")
            console.input("Press Enter to continue...")
        elif action == "free_potion":
            if len(self.player.potions) < self.player.max_potions:
                pid = random.choice(POTION_POOL)
                self.player.potions.append(pid)
                console.print(f"[green]Found {POTION_LIBRARY[pid]['name']}![/green]")
            else:
                console.print("[grey62]Potion belt full.[/grey62]")
            console.input("Press Enter to continue...")
        elif action == "coinflip":
            bet = 30
            if self.player.gold >= bet:
                if random.random() < 0.5:
                    self.player.gold += bet
                    console.print(f"[green]You won! +{bet} gold.[/green]")
                else:
                    self.player.gold -= bet
                    console.print(f"[red]You lost {bet} gold.[/red]")
            else:
                console.print("[red]Not enough gold to bet.[/red]")
            console.input("Press Enter to continue...")
        elif action == "pay_sneak":
            if self.player.gold >= 20:
                self.player.gold -= 20
                console.print("[grey62]You sneak past safely.[/grey62]")
                console.input("Press Enter to continue...")
            else:
                console.print("[red]Not enough gold — you're forced to fight![/red]")
                console.input("Press Enter to continue...")
                return self.run_combat([self.spawn_enemy(random.choice(self.current_pools()["normal"]))], boss=False)
        elif action == "mirror_swap":
            removed = self.do_remove_card()
            if removed:
                new_card = make_card(random.choice(REWARD_POOL))
                self.player.deck.append(new_card)
                console.print(f"[gold1]The mirror grants you: {new_card['name']}[/gold1]")
                console.input("Press Enter to continue...")
        elif action == "free_upgrade":
            self.do_upgrade_card()
        elif action == "pandora":
            avail = [r for r in RELIC_POOL if r not in self.player.relics]
            if avail:
                rid = random.choice(avail)
                self.player.relics.append(rid)
                console.print(f"[magenta]The box grants you: {RELIC_LIBRARY[rid]['name']}![/magenta]")
            else:
                console.print("[grey62]The box has nothing left to give.[/grey62]")
            if "purity" in self.player.relics:
                console.print("[cyan]Purity shields you from the curse within.[/cyan]")
            else:
                curse_id = random.choice(CURSE_POOL)
                curse = make_card(curse_id)
                self.player.deck.append(curse)
                console.print(f"[red]...but a {curse['name']} slithers into your deck.[/red]")
            console.input("Press Enter to continue...")
        elif action == "forbidden_tome":
            all_exclusive = [k for k in CARD_LIBRARY if CARD_LIBRARY[k]["rarity"] == "exclusive"]
            card = make_card(random.choice(all_exclusive))
            self.player.deck.append(card)
            console.print(f"[gold1]You learn: {card['name']}![/gold1] {card['desc']}")
            if "purity" in self.player.relics:
                console.print("[cyan]Purity shields you from the curse within.[/cyan]")
            else:
                curse = make_card(random.choice(CURSE_POOL))
                self.player.deck.append(curse)
                console.print(f"[red]...but a {curse['name']} slithers into your deck.[/red]")
            console.input("Press Enter to continue...")
        elif action == "mirror_fight":
            mirror = self.spawn_mirror()
            return self.run_combat(mirror, boss=False, mirror_fight=True)
        elif action == "castle_trial":
            return self.do_castle()
        elif action == "buy_card_event":
            if self.player.gold >= 30:
                self.player.gold -= 30
                pool = REWARD_POOL[:]
                random.shuffle(pool)
                gained = make_card(pool[0])
                self.player.deck.append(gained)
                console.print(f"[green]Learned: {gained['name']}![/green]")
            else:
                console.print("[red]Not enough gold.[/red]")
            console.input("Press Enter to continue...")
        elif action == "buy_choose_card":
            if self.player.gold >= 30:
                self.player.gold -= 30
                pool = REWARD_POOL[:]
                random.shuffle(pool)
                options_cards = [make_card(c) for c in pool[:2]]
                table = Table(title="Choose a card to learn")
                table.add_column("#")
                table.add_column("Name")
                table.add_column("Cost")
                table.add_column("Effect")
                for i, card in enumerate(options_cards):
                    color = TYPE_COLOR[card["type"]]
                    table.add_row(str(i + 1), f"[{color}]{card['name']}[/{color}]", str(card["cost"]), card["desc"])
                console.print(table)
                pick = prompt("Choose #: ", choices=[str(i + 1) for i in range(len(options_cards))])
                self.player.deck.append(options_cards[int(pick) - 1])
                console.print("[green]Card added to deck![/green]")
            else:
                console.print("[red]Not enough gold.[/red]")
            console.input("Press Enter to continue...")
        elif action == "full_heal_free":
            self.player.hp = self.player.max_hp
            console.print("[cyan]Your wounds close and your soul feels purified. Fully healed.[/cyan]")
            console.input("Press Enter to continue...")
        elif action == "heal_20":
            healed = min(20, self.player.max_hp - self.player.hp)
            self.player.hp += healed
            console.print(f"[cyan]The water is sweet and cool. Healed {healed} HP.[/cyan]")
            console.input("Press Enter to continue...")
        elif action == "treasure_gamble":
            if random.random() < 0.5:
                pool = REWARD_POOL[:]
                random.shuffle(pool)
                gained = make_card(pool[0])
                self.player.deck.append(gained)
                console.print(f"[gold1]It's real! Gained: {gained['name']}![/gold1]")
                console.input("Press Enter to continue...")
            else:
                console.print("[red]It's a mimic![/red]")
                console.input("Press Enter to continue...")
                result = self.run_combat([self.spawn_enemy(random.choice(self.current_pools()["normal"]))], boss=False)
                if result == "ok":
                    pool = REWARD_POOL[:]
                    random.shuffle(pool)
                    gained = make_card(pool[0])
                    self.player.deck.append(gained)
                    console.print(f"[gold1]Gained: {gained['name']}![/gold1]")
                    console.input("Press Enter to continue...")
                return result
        else:
            console.input("Press Enter to continue...")
        return None

    # ---------------- TALENTS (Lophis mode) ----------------
    def do_talent_offer(self):
        pool = [t for t in TALENT_LIBRARY if self.player.talents.get(t, 0) < 99]
        if not pool:
            return
        random.shuffle(pool)
        offer = pool[:3]
        console.print(Panel("Choose a Talent — a permanent boost for the rest of this run.",
                             title="[bold cyan]Talent[/bold cyan]", border_style="cyan"))
        ttable = Table()
        ttable.add_column("#")
        ttable.add_column("Name")
        ttable.add_column("Effect")
        ttable.add_column("Lvl")
        for i, tid in enumerate(offer):
            t = TALENT_LIBRARY[tid]
            lvl = self.player.talents.get(tid, 0)
            ttable.add_row(str(i + 1), f"[cyan]{t['name']}[/cyan]", t["desc"], f"{lvl}->{lvl + 1}")
        console.print(ttable)
        choices = [str(i + 1) for i in range(len(offer))] + ["s"]
        pick = prompt("Pick talent # or 's' to skip: ", choices=choices)
        if pick == "s":
            return
        tid = offer[int(pick) - 1]
        t = TALENT_LIBRARY[tid]
        self.player.talents[tid] = self.player.talents.get(tid, 0) + 1
        current = getattr(self.player, t["stat"], 0)
        setattr(self.player, t["stat"], current + t["amount"])
        if t["stat"] == "max_hp":
            self.player.hp += t["amount"]
        console.print(f"[cyan]{t['name']} learned![/cyan] {t['desc']}")

    # ---------------- REST ----------------
    def do_rest(self):
        console.clear()
        console.rule("[green]Rest Site[/green]")
        heal = int(self.player.max_hp * 0.3)
        upgradeable = [c for c in self.player.deck if is_upgradeable(c)]
        options = ["1"]
        console.print(f"1) Rest and heal {heal} HP")
        if upgradeable:
            console.print("2) Upgrade a card")
            options.append("2")
        choice = prompt("Choose #: ", choices=options)
        if choice == "1":
            self.player.hp = min(self.player.max_hp, self.player.hp + heal)
            console.print(f"[green]Healed to {self.player.hp}/{self.player.max_hp} HP.[/green]")
            console.input("Press Enter to continue...")
        else:
            self.do_upgrade_card()

    def do_upgrade_card(self):
        upgradeable = [c for c in self.player.deck if is_upgradeable(c)]
        if not upgradeable:
            console.print("[grey62]Nothing left to upgrade.[/grey62]")
            console.input("Press Enter to continue...")
            return
        table = Table(title="Choose a card to upgrade")
        table.add_column("#")
        table.add_column("Name")
        table.add_column("Cost")
        table.add_column("Effect")
        for i, card in enumerate(upgradeable):
            color = TYPE_COLOR[card["type"]]
            table.add_row(str(i + 1), f"[{color}]{card['name']}[/{color}]", str(card["cost"]), card["desc"])
        console.print(table)
        choices = [str(i + 1) for i in range(len(upgradeable))] + ["c"]
        choice = prompt("Upgrade which card? # (or 'c' to cancel): ", choices=choices)
        if choice == "c":
            return
        card_obj = upgradeable[int(choice) - 1]

        path = None
        if upgrade_offers_path_choice(card_obj):
            console.print(f"[bold]{card_obj['name']}[/bold] can be upgraded two ways:")
            console.print("  [gold1]a[/gold1]) Type A — hits harder (more damage/block)")
            console.print("  [gold1]b[/gold1]) Type B — status effect grows stronger")
            path_choice = prompt("Choose upgrade path a/b: ", choices=["a", "b"])
            path = "A" if path_choice == "a" else "B"

        upgraded = upgrade_card(card_obj, path=path)
        if "warped_tongs" in self.player.relics:
            upgraded = upgrade_card(upgraded, path=path)
        for i, c in enumerate(self.player.deck):
            if c is card_obj:
                self.player.deck[i] = upgraded
                break
        console.print(f"[gold1]{upgraded['name']} is ready![/gold1] {upgraded['desc']}")
        console.input("Press Enter to continue...")

    def do_remove_card(self):
        if len(self.player.deck) <= 5:
            console.print("[grey62]Your deck is too thin to remove anything.[/grey62]")
            console.input("Press Enter to continue...")
            return
        table = Table(title="Choose a card to remove")
        table.add_column("#")
        table.add_column("Name")
        table.add_column("Cost")
        table.add_column("Effect")
        for i, card in enumerate(self.player.deck):
            color = TYPE_COLOR[card["type"]]
            table.add_row(str(i + 1), f"[{color}]{card['name']}[/{color}]", str(card["cost"]), card["desc"])
        console.print(table)
        choices = [str(i + 1) for i in range(len(self.player.deck))] + ["c"]
        choice = prompt("Remove which card? # (or 'c' to cancel): ", choices=choices)
        if choice == "c":
            return None
        removed = self.player.deck.pop(int(choice) - 1)
        console.print(f"[grey62]Removed {removed['name']} from your deck.[/grey62]")
        return removed

    # ---------------- SHOP ----------------
    def do_shop(self):
        pool = REWARD_POOL[:]
        random.shuffle(pool)
        shop_cards = [make_card(c) for c in pool[:4]]
        pot_pool = POTION_POOL[:]
        random.shuffle(pot_pool)
        shop_potions = pot_pool[:2]
        while True:
            console.clear()
            console.rule("[yellow]Shop[/yellow]")
            console.print(f"Gold: [yellow]{self.player.gold}[/yellow]")
            table = Table(title="Cards")
            table.add_column("#")
            table.add_column("Name")
            table.add_column("Price")
            table.add_column("Effect")
            prices = []
            for i, card in enumerate(shop_cards):
                price = 40 + card["cost"] * 15
                prices.append(price)
                color = TYPE_COLOR[card["type"]]
                table.add_row(str(i + 1), f"[{color}]{card['name']}[/{color}]", f"{price}g", card["desc"])
            console.print(table)

            pot_labels = []
            if shop_potions:
                ptable = Table(title="Potions")
                ptable.add_column("#")
                ptable.add_column("Name")
                ptable.add_column("Price")
                ptable.add_column("Effect")
                for i, pid in enumerate(shop_potions):
                    label = f"p{i + 1}"
                    pot_labels.append(label)
                    p = POTION_LIBRARY[pid]
                    ptable.add_row(label, f"[green]{p['name']}[/green]", "35g", p["desc"])
                console.print(ptable)

            has_upgradeable = any(is_upgradeable(c) for c in self.player.deck)
            can_remove = len(self.player.deck) > 5
            service_choices = []
            if has_upgradeable:
                console.print("[gold1]u[/gold1]) Smith: upgrade a card (50g)")
                service_choices.append("u")
            if can_remove:
                console.print("[gold1]x[/gold1]) Smith: remove a card (75g)")
                service_choices.append("x")

            choices = [str(i + 1) for i in range(len(shop_cards))] + pot_labels + service_choices + ["l"]
            choice = prompt("Buy a card #, potion (e.g. p1), service (u/x), or 'l' to leave: ", choices=choices)
            if choice == "l":
                return
            if choice == "u":
                if self.player.gold >= 50:
                    self.player.gold -= 50
                    self.do_upgrade_card()
                else:
                    console.print("[red]Not enough gold.[/red]")
                    console.input("Press Enter to continue...")
                continue
            if choice == "x":
                if self.player.gold >= 75:
                    self.player.gold -= 75
                    self.do_remove_card()
                else:
                    console.print("[red]Not enough gold.[/red]")
                    console.input("Press Enter to continue...")
                continue
            if choice.startswith("p"):
                idx = int(choice[1:]) - 1
                if self.player.gold >= 35:
                    if len(self.player.potions) >= self.player.max_potions:
                        console.print("[red]Potion belt full.[/red]")
                    else:
                        self.player.gold -= 35
                        self.player.potions.append(shop_potions.pop(idx))
                        console.print("[green]Purchased![/green]")
                else:
                    console.print("[red]Not enough gold.[/red]")
            else:
                idx = int(choice) - 1
                price = prices[idx]
                if self.player.gold >= price:
                    self.player.gold -= price
                    self.player.deck.append(shop_cards.pop(idx))
                    console.print("[green]Purchased![/green]")
                else:
                    console.print("[red]Not enough gold.[/red]")
            console.input("Press Enter to continue...")
            if not shop_cards and not shop_potions:
                return

    # ---------------- COMBAT ----------------
    def read_play_input(self, c):
        """Prompt for one or more card indices (e.g. '1,2'), 'e' to end turn, 'p' for potions,
        or 'x1,2' to discard specific cards from hand."""
        while True:
            raw = console.input("Play card #(s), e.g. 1,2  (e=end turn, p=potion, x1,2=discard): ").strip().lower()
            if raw == "e":
                return ("end", None)
            if raw == "p":
                return ("potion", None)
            if raw.startswith("x"):
                parts = [p.strip() for p in raw[1:].split(",") if p.strip()]
                if not parts:
                    console.print("[red]Specify card number(s) to discard, e.g. x1,2.[/red]")
                    continue
                try:
                    idxs = [int(p) - 1 for p in parts]
                except ValueError:
                    console.print("[red]Invalid discard input.[/red]")
                    continue
                if any(i < 0 or i >= len(c.hand) for i in idxs):
                    console.print("[red]Index out of range.[/red]")
                    continue
                if len(set(idxs)) != len(idxs):
                    console.print("[red]Duplicate indices.[/red]")
                    continue
                return ("discard", idxs)
            parts = [p.strip() for p in raw.split(",") if p.strip()]
            if not parts:
                console.print("[red]Enter a card number, list like 1,2, 'e', or 'p'.[/red]")
                continue
            try:
                idxs = [int(p) - 1 for p in parts]
            except ValueError:
                console.print("[red]Invalid input.[/red]")
                continue
            if any(i < 0 or i >= len(c.hand) for i in idxs):
                console.print("[red]Index out of range.[/red]")
                continue
            if len(set(idxs)) != len(idxs):
                console.print("[red]Duplicate indices.[/red]")
                continue
            return ("play", idxs)

    def choose_target(self, c, prompt_msg="Target enemy #"):
        alive_idxs = [i for i in range(len(c.enemies)) if c.enemies[i].alive()]
        if not alive_idxs:
            return None
        if len(alive_idxs) == 1:
            return c.enemies[alive_idxs[0]]
        t_choice = prompt(f"{prompt_msg} ({', '.join(str(i + 1) for i in alive_idxs)}): ",
                           choices=[str(i + 1) for i in alive_idxs])
        return c.enemies[int(t_choice) - 1]

    def handle_potion_menu(self, c):
        if not self.player.potions:
            console.print("[red]No potions in your belt.[/red]")
            console.input("Press Enter...")
            return
        table = Table(title="Potions")
        table.add_column("#")
        table.add_column("Name")
        table.add_column("Effect")
        for i, pid in enumerate(self.player.potions):
            p = POTION_LIBRARY[pid]
            table.add_row(str(i + 1), f"[green]{p['name']}[/green]", p["desc"])
        console.print(table)
        choices = [str(i + 1) for i in range(len(self.player.potions))] + ["c"]
        choice = prompt("Drink potion # (or 'c' to cancel): ", choices=choices)
        if choice == "c":
            return
        idx = int(choice) - 1
        pid = self.player.potions[idx]
        p = POTION_LIBRARY[pid]
        target = None
        if p.get("targeted"):
            target = self.choose_target(c, "Aim potion at enemy #")
        c.use_potion(pid, target)
        self.player.potions.pop(idx)

    def _animation_kind_for(self, card):
        if card.get("poison"):
            return "poison"
        if card.get("aoe"):
            return "cleave"
        if card.get("damage", 0) >= 15 or card.get("str_mult", 1) > 1 or card.get("upgrade_damage_flat"):
            return "heavy"
        if card.get("hits", 1) > 1 or card.get("scales_with_deck_attacks") or \
           card.get("scales_with_attacks_played") or card.get("scales_with_cards_played") or \
           card.get("poison_execute"):
            return "stab"
        return "slash"

    def run_combat(self, enemies, boss, elite=False, slime_swarm=False, gold_goblin=False, mirror_fight=False):
        c = Combat(self.player, enemies, slime_swarm=slime_swarm, mirror_fight=mirror_fight)
        c.add_log("Combat begins!")
        if slime_swarm:
            c.add_log("[green]The Slime Swarm stirs...[/green]")
        if gold_goblin:
            c.add_log("[yellow]A Gold Goblin! Kill it fast before it flees...[/yellow]")
        if mirror_fight:
            c.add_log("[magenta]Your reflection steps out of the pool. It has infinite Energy.[/magenta]")
        while not c.over:
            c.render()
            action, data = self.read_play_input(c)
            if action == "end":
                c.end_turn()
                continue
            if action == "potion":
                self.handle_potion_menu(c)
                continue
            if action == "discard":
                to_discard = [c.hand[i] for i in data]
                for card in to_discard:
                    for i, h in enumerate(c.hand):
                        if h is card:
                            c.hand.pop(i)
                            break
                    c.discard_pile.append(card)
                    c.add_log(f"Discarded {card['name']}.")
                continue

            idxs = data
            selected_cards = [c.hand[i] for i in idxs]
            needs_target = any(
                card["type"] == "attack" and not card.get("aoe") and not card.get("x_cost")
                for card in selected_cards
            )
            target = self.choose_target(c) if needs_target else None

            for card in selected_cards:
                if c.over:
                    break
                if not any(hcard is card for hcard in c.hand):
                    continue
                if not c.can_play(card):
                    console.print(f"[red]Not enough energy for {card['name']} — skipping rest of batch.[/red]")
                    console.input("Press Enter...")
                    break
                this_target = target if (card["type"] == "attack" and not card.get("aoe") and not card.get("x_cost")) else None
                c.play_card(card, this_target)
                if SHOW_ATTACK_ANIMATIONS:
                    deals_damage = card.get("damage") or card.get("poison") or card.get("damage_eq_block") or \
                                    card.get("poison_execute") or card.get("scales_with_cards_played") or \
                                    card.get("scales_with_attacks_played") or card.get("scales_with_missing_hp")
                    if card["type"] == "attack" or deals_damage:
                        play_attack_animation(console, self._animation_kind_for(card))
                    elif card["type"] == "skill" and card.get("block"):
                        play_attack_animation(console, "block")

        if c.fled:
            console.clear()
            console.print(Panel("[yellow]The Gold Goblin escaped with its loot! No reward this time.[/yellow]",
                                 border_style="yellow"))
            console.input("Press Enter to continue...")
            return "ok"

        if getattr(c, "mirror_defeated", False):
            console.clear()
            console.print(Panel("[magenta]Your reflection bested you — but it was never truly real. "
                                 "You step back from the pool, shaken but unharmed.[/magenta]",
                                 border_style="magenta"))
            console.input("Press Enter to continue...")
            return "ok"

        if c.won:
            if mirror_fight:
                console.clear()
                console.print(Panel("[gold1]You defeated your reflection! It dissolves, leaving behind "
                                     "a shard of the mirror itself.[/gold1]", border_style="gold1"))
                mirror_card = make_card("mirror_card")
                self.player.deck.append(mirror_card)
                console.print(f"[gold1]Gained: {mirror_card['name']}[/gold1] — {mirror_card['desc']}")
                console.input("Press Enter to continue...")
                return "ok"
            if "burning_blood" in self.player.relics:
                self.player.hp = min(self.player.max_hp, self.player.hp + 6)
            if "meat_on_the_bone" in self.player.relics and self.player.hp <= self.player.max_hp * 0.5:
                self.player.hp = min(self.player.max_hp, self.player.hp + 12)
                console.print("[green]Meat on the Bone: +12 HP.[/green]")

            c.generate_rewards()
            console.clear()
            c.render()
            c.render_reward()
            choices = [str(i + 1) for i in range(len(c.reward_cards))] + ["s"]
            pick = prompt("Choose card # or 's' to skip: ", choices=choices)
            if pick != "s":
                self.player.deck.append(c.reward_cards[int(pick) - 1])
                console.print("[green]Card added to deck![/green]")

            gold_gain = random.randint(15, 30)
            if gold_goblin:
                bonus = random.randint(80, 120)
                gold_gain += bonus
                console.print(f"[gold1]The Gold Goblin's hoard spills out: +{bonus} bonus gold![/gold1]")
            if "compounding_interest" in self.player.relics:
                interest = self.player.stats["enemies_defeated"] // 5
                if interest:
                    gold_gain += interest
                    console.print(f"[gold1]Compounding Interest: +{interest} gold.[/gold1]")
            self.player.gold += gold_gain
            console.print(f"[yellow]Found {gold_gain} gold.[/yellow]")

            if not elite and len(self.player.potions) < self.player.max_potions and random.random() < 0.3:
                pid = random.choice(POTION_POOL)
                self.player.potions.append(pid)
                console.print(f"[green]Found a {POTION_LIBRARY[pid]['name']}![/green]")

            if elite:
                if "runic_cube" in self.player.relics:
                    self.player.bonus_strength += 1
                    self.player.bonus_dexterity += 1
                    console.print("[gold1]Runic Cube: permanent +1 Strength, +1 Dexterity![/gold1]")
                choices_pool = [r for r in self.relic_pool() if r not in self.player.relics]
                random.shuffle(choices_pool)
                offer = choices_pool[:2] if len(choices_pool) >= 2 else choices_pool
                if offer:
                    rtable = Table(title="Choose a relic")
                    rtable.add_column("#")
                    rtable.add_column("Name")
                    rtable.add_column("Effect")
                    for i, rid in enumerate(offer):
                        r = RELIC_LIBRARY[rid]
                        rtable.add_row(str(i + 1), f"[magenta]{r['name']}[/magenta]", r["desc"])
                    console.print(rtable)
                    rchoices = [str(i + 1) for i in range(len(offer))] + ["s"]
                    rpick = prompt("Pick relic # or 's' to skip: ", choices=rchoices)
                    if rpick != "s":
                        self.player.relics.append(offer[int(rpick) - 1])
                        console.print("[magenta]Relic acquired![/magenta]")

            if self.player.game_mode == "lophis" and (elite or boss):
                self.do_talent_offer()

            console.input("Press Enter to continue...")
            if boss:
                return "won_game"
            return "ok"
        else:
            console.clear()
            console.print(Panel("[bold red]You have died.[/bold red]", border_style="red"))
            return "dead"

    def run(self):
        while True:
            result = self.map_loop()
            if os.path.exists(SAVE_PATH):
                os.remove(SAVE_PATH)
            console.clear()
            if result:
                console.print(Panel("[bold gold1]VICTORY! You defeated the Guardian![/bold gold1]", border_style="gold1"))
            else:
                console.print(Panel("[bold red]GAME OVER[/bold red]", border_style="red"))

            s = self.player.stats
            stats_txt = (
                f"Seed: {self.seed}   Class: {CLASSES[self.player.character]['name']}   Ascension: {self.player.ascension}\n"
                f"Damage dealt: [red]{s['damage_dealt']}[/red]   Damage taken: [red]{s['damage_taken']}[/red]\n"
                f"Cards played: {s['cards_played']}   Potions used: {s['potions_used']}\n"
                f"Enemies defeated: {s['enemies_defeated']}   Turns survived: {s['turns_survived']}\n"
                f"Final gold: [yellow]{self.player.gold}[/yellow]   Relics: {len(self.player.relics)}   "
                f"Final deck size: {len(self.player.deck)}"
            )
            console.print(Panel(stats_txt, title="Run Summary", border_style="cyan"))

            again = prompt("Start a new run? (y/n): ", choices=["y", "n"])
            if again != "y":
                break
            self.seed = choose_seed()
            new_mode = choose_game_mode()
            self.player = Player(choose_character(new_mode), choose_ascension(), new_mode)
            self.game_map = GameMap(lophis=(new_mode == "lophis"))
            self.act = 1


if __name__ == "__main__":
    Game.load_or_new().run()
