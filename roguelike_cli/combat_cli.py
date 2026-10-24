import sys, os
import copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import random
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.markup import escape

from ascii_art import SHOW_ASCII_ART, get_enemy_art

console = Console()

TYPE_COLOR = {"attack": "red", "skill": "cyan", "power": "magenta", "curse": "grey50"}
TYPE_ICON = {"attack": "⚔", "skill": "🛡", "power": "✦", "curse": "☠"}


class Combat:
    def __init__(self, player, enemies, slime_swarm=False, mirror_fight=False):
        self.player = player
        self.enemies = enemies
        self.slime_swarm = slime_swarm
        self.mirror_fight = mirror_fight
        self.mirror_defeated = False
        if mirror_fight:
            self.mirror_draw_pile = [c for c in copy.deepcopy(player.deck) if c["type"] != "curse"]
            random.shuffle(self.mirror_draw_pile)
            self.mirror_discard_pile = []

        self.draw_pile = player.deck[:]
        random.shuffle(self.draw_pile)
        self.hand = []
        self.discard_pile = []
        self.exhaust_pile = []

        self.energy_bonus = 1 if "storm_charm" in player.relics else 0
        self.energy = player.max_energy + self.energy_bonus
        self.block = 3 if "thread_spool" in player.relics else 0
        self.strength = 1 if "vajra" in player.relics else 0
        self.dexterity = 1 if "oddly_smooth_stone" in player.relics else 0
        if "philosophers_stone" in player.relics:
            self.strength += 2
            self.dexterity += 2
        self.strength += player.bonus_strength
        self.dexterity += player.bonus_dexterity
        self.temp_strength = 0
        self.vulnerable = 0
        self.weak = 0
        self.frail = 0
        self.metallicize = 0
        self.combust = 0
        self.resist = 0     # Lophis: flat % reduction on incoming damage, expires at your next turn
        self.guard = 0      # Lophis: Counter — next hit you take this reflects this much back, then clears
        self.sneak = False  # Lophis (assassin): boosts Backstab, cleared by Sap
        self.sin = 3 if player.character == "monk" else 0  # Lophis (monk): resource spent by Redemption/Suffering

        self.turn = 1
        self.over = False
        self.won = False
        self.fled = False
        self.reward_cards = []
        self.log = []
        self.cards_played = 0
        self.echo_active = False
        self.attacks_played = 0
        self.last_played_card = None
        self.regen_turns_left = 0
        self.regen_amount = 0
        self.second_chance_used = False
        self.free_card_used_this_turn = False
        self.next_card_free = False
        self.iron_will_triggered = False
        self.next_hit_blocked = False

        if "bag_of_marbles" in player.relics:
            for e in self.enemies:
                e.vulnerable += 1
            self.add_log("[magenta]Bag of Marbles: enemies Vulnerable +1.[/magenta]")

        curse_weak = sum(c.get("on_start_weak", 0) for c in player.deck)
        curse_frail = sum(c.get("on_start_frail", 0) for c in player.deck)
        curse_vulnerable = sum(c.get("on_start_vulnerable", 0) for c in player.deck)
        if curse_weak:
            self.weak += curse_weak
            self.add_log(f"[red]A curse weighs on you: +{curse_weak} Weak.[/red]")
        if curse_frail:
            self.frail += curse_frail
            self.add_log(f"[red]A curse weighs on you: +{curse_frail} Frail.[/red]")
        if curse_vulnerable:
            self.vulnerable += curse_vulnerable
            self.add_log(f"[red]A curse weighs on you: +{curse_vulnerable} Vulnerable.[/red]")

        self.draw_hand()

    def _mark_win(self):
        if not self.won:
            self.won = True
            self.over = True
            self.player.stats["enemies_defeated"] += len(self.enemies)

    def apply_weak(self, dmg):
        if self.weak > 0:
            return int(dmg * 0.75)
        return dmg

    # ---------------- deck mechanics ----------------
    def add_log(self, msg):
        self.log.append(msg)
        self.log = self.log[-5:]

    def draw_hand(self, n=5):
        for _ in range(n):
            self.draw_one()

    def draw_one(self):
        if not self.draw_pile:
            if not self.discard_pile:
                return
            self.draw_pile = self.discard_pile[:]
            random.shuffle(self.draw_pile)
            self.discard_pile = []
        if self.draw_pile and len(self.hand) < 10 + self.player.talent_hand_limit:
            self.hand.append(self.draw_pile.pop())

    def _discard_random_hand_card(self, exclude=None):
        """Lophis helper: discard a random OTHER card from hand. Returns the
        discarded card dict, or None if there was nothing eligible to discard."""
        candidates = [c for c in self.hand if c is not exclude]
        if not candidates:
            return None
        chosen = random.choice(candidates)
        self.hand.remove(chosen)
        self.discard_pile.append(chosen)
        return chosen

    def start_turn(self):
        gain = self.player.max_energy + self.energy_bonus
        if self.player.game_mode == "lophis":
            cap = self.player.max_energy * 4
            self.energy = min(cap, self.energy + gain)
        else:
            self.energy = gain
        if self.player.game_mode != "lophis":
            self.block = 0  # Lophis Armor persists across turns instead of resetting
        self.resist = 0
        self.temp_strength = 0
        self.cards_played = 0
        self.echo_active = False
        self.attacks_played = 0
        self.last_played_card = None
        self.free_card_used_this_turn = False
        self.player.stats["turns_survived"] += 1
        if self.weak > 0:
            self.weak -= 1
        if self.vulnerable > 0:
            self.vulnerable -= 1
        if self.frail > 0:
            self.frail -= 1
        draw_n = 5 + (1 if "pocket_watch" in self.player.relics else 0) + self.player.talent_draw
        self.draw_hand(draw_n)
        if self.regen_turns_left > 0:
            self.block += self.regen_amount
            self.regen_turns_left -= 1
            self.add_log(f"[cyan]Regeneration: +{self.regen_amount} Block.[/cyan]")
        self.add_log(f"[bold]-- Turn {self.turn} --[/bold]")

    def end_turn(self):
        if self.player.talent_guard_per_turn > 0:
            self.guard += self.player.talent_guard_per_turn
        if "orichalcum" in self.player.relics and self.block == 0:
            self.block += 6
            self.add_log("[magenta]Orichalcum: +6 Block.[/magenta]")
        if self.metallicize:
            self.block += self.metallicize
        if self.combust:
            for e in self.alive_enemies():
                e.hp = max(0, e.hp - self.combust)
            self.add_log(f"[red]Combust burns all enemies for {self.combust}![/red]")
            if self._combat_can_end_in_victory():
                self.discard_pile.extend(self.hand)
                self.hand = []
                self._mark_win()
                return
        if "runic_pyramid" not in self.player.relics and self.player.game_mode != "retain":
            self.discard_pile.extend(self.hand)
            self.hand = []
        self.enemy_turn()
        for e in self.enemies:
            if e.alive():
                if e.vulnerable > 0:
                    e.vulnerable -= 1
                if e.weak > 0:
                    e.weak -= 1
                if e.frail > 0:
                    e.frail -= 1
        if not self.over:
            self.turn += 1
            self.start_turn()

    def _slime_duplicate_phase(self):
        from enemies import make_enemy
        # Advance decay on empty slots; a slot that was never occupied stays at 0 (available).
        for e in self.enemies:
            if e.alive():
                e.revive_in = None
            elif e.revive_in is None:
                e.revive_in = 3  # just discovered dead this round — starts decaying
            elif e.revive_in > 0:
                e.revive_in -= 1

        alive_slimes = [e for e in self.enemies if e.alive()]
        open_slots = [i for i, e in enumerate(self.enemies) if not e.alive() and e.revive_in == 0]
        asc_hp_mult = 1 + 0.08 * getattr(self.player, "ascension", 0)
        for src in alive_slimes:
            if not open_slots:
                break
            idx = open_slots.pop(0)
            clone = make_enemy("lophis_slime")
            clone.max_hp = int(round(clone.max_hp * asc_hp_mult))
            clone.hp = min(src.hp, clone.max_hp)
            clone.revive_in = None
            self.enemies[idx] = clone
            self.add_log(f"[green]A Slime splits! New Slime appears with {clone.hp} HP.[/green]")

    def _mirror_turn(self, mirror_enemy):
        hand = []
        for _ in range(5):
            if not self.mirror_draw_pile:
                if not self.mirror_discard_pile:
                    break
                self.mirror_draw_pile = self.mirror_discard_pile[:]
                random.shuffle(self.mirror_draw_pile)
                self.mirror_discard_pile = []
            if self.mirror_draw_pile:
                hand.append(self.mirror_draw_pile.pop())
        played = 0
        for card in hand:
            if not self.player.alive():
                break
            self._mirror_play_effect(card, mirror_enemy)
            self.mirror_discard_pile.append(card)
            played += 1
        self.add_log(f"[magenta]{mirror_enemy.name} plays {played} cards with infinite Energy![/magenta]")
        mirror_enemy.pick_move()

    def _mirror_play_effect(self, card, mirror_enemy):
        """A simplified replay of a card as if the mirror played it. Covers the core
        numeric effects (damage, block, debuffs, strength); it does not replicate
        Poison, Exhaust, Echo, or other class-specific synergy mechanics."""
        dmg = card.get("damage", 0)
        if card.get("damage_eq_block"):
            dmg = mirror_enemy.block
        if dmg:
            hits = card.get("hits", 1)
            for _ in range(hits):
                self.damage_player(dmg, source=mirror_enemy)
        if card.get("block"):
            mirror_enemy.block += card["block"]
        if card.get("vulnerable"):
            self.vulnerable += card["vulnerable"]
        if card.get("weak"):
            self.weak += card["weak"]
        if card.get("frail"):
            self.frail += card["frail"]
        if card.get("strength"):
            mirror_enemy.strength += card["strength"]

    def _revival_phase(self):
        for e in self.enemies:
            if not e.alive() and e.self_revives and e.revives_left > 0:
                if e.revive_in is None:
                    e.revive_in = 3
                elif e.revive_in > 0:
                    e.revive_in -= 1
                if e.revive_in == 0:
                    e.hp = max(1, int(e.max_hp * e.revive_hp_frac))
                    e.revive_in = None
                    e.revives_left -= 1
                    e.death_processed = False
                    e.pick_move()
                    self.add_log(f"[bold white]{e.name} rises from its bones![/bold white]")

    def _rage_phase(self):
        for e in self.enemies:
            if not e.alive() and e.rage_on_death and not e.death_processed:
                e.death_processed = True
                gained = e.rage_on_death
                buffed = False
                for other in self.enemies:
                    if other.alive():
                        other.strength += gained
                        buffed = True
                if buffed:
                    self.add_log(f"[red]{e.name}'s death enrages its allies! (+{gained} Strength each)[/red]")

    def enemy_turn(self):
        self._revival_phase()
        self._rage_phase()
        if self.slime_swarm:
            self._slime_duplicate_phase()
        asc_mult = 1 + 0.05 * getattr(self.player, "ascension", 0)
        for e in self.enemies:
            if not e.alive():
                continue
            if self.mirror_fight:
                self._mirror_turn(e)
                continue
            if e.flee_after_turn is not None and self.turn >= e.flee_after_turn \
                    and "greed_charm" not in self.player.relics:
                e.hp = 0
                e.escaped = True
                self.add_log(f"[yellow]{e.name} flees with your gold![/yellow]")
                continue
            if e.poison > 0:
                e.hp = max(0, e.hp - e.poison)
                self.add_log(f"{e.name} takes {e.poison} poison damage.")
                e.poison -= 1
                if not e.alive():
                    continue
            if e.burning > 0:
                burn_dmg = e.burning
                e.hp = max(0, e.hp - burn_dmg)
                self.add_log(f"[orange3]{e.name} is scorched by Burning for {burn_dmg}![/orange3]")
                e.burning = 0
                if not e.alive():
                    continue
            m = e.current_move
            if m["type"] == "attack":
                dmg = int(round((m["damage"] + e.strength) * asc_mult))
                if e.weak > 0:
                    dmg = int(dmg * 0.75)
                for _ in range(m.get("hits", 1)):
                    self.damage_player(dmg, source=e)
                self.add_log(f"{e.name} attacks for {dmg}!")
            elif m["type"] == "defend":
                gained = int(m["block"] * (0.75 if e.frail > 0 else 1))
                e.block += gained
                self.add_log(f"{e.name} gains {gained} block.")
            elif m["type"] == "buff":
                e.strength += 2
                self.add_log(f"{e.name} grows stronger (+2 STR).")
            elif m["type"] == "attack_defend":
                dmg = int(round((m["damage"] + e.strength) * asc_mult))
                if e.weak > 0:
                    dmg = int(dmg * 0.75)
                self.damage_player(dmg, source=e)
                gained = int(m["block"] * (0.75 if e.frail > 0 else 1))
                e.block += gained
                self.add_log(f"{e.name} attacks and defends.")
            elif m["type"] == "weaken":
                self.weak += m["amount"]
                self.add_log(f"{e.name} weakens you (+{m['amount']} Weak).")
            elif m["type"] == "expose":
                self.vulnerable += m["amount"]
                self.add_log(f"{e.name} exposes you (+{m['amount']} Vulnerable).")
            elif m["type"] == "steal":
                stolen = min(self.player.gold, m["amount"])
                self.player.gold -= stolen
                self.add_log(f"{e.name} steals {stolen} gold!")
            elif m["type"] == "hex":
                self.weak += m["weak"]
                self.vulnerable += m["vulnerable"]
                if m.get("frail"):
                    self.frail += m["frail"]
                self.add_log(f"{e.name} hexes you (+{m['weak']} Weak, +{m['vulnerable']} Vulnerable"
                             + (f", +{m['frail']} Frail" if m.get("frail") else "") + ").")
            elif m["type"] == "heal":
                healed = min(m["amount"], e.max_hp - e.hp)
                e.hp += healed
                self.add_log(f"{e.name} heals {healed} HP.")
            e.pick_move()
        if self._combat_can_end_in_victory():
            if any(e.escaped for e in self.enemies):
                self.over = True
                self.won = False
                self.fled = True
                return
            self._mark_win()
            return
        if self.player.hp <= 0:
            if "second_chance" in self.player.relics and not self.second_chance_used:
                self.second_chance_used = True
                self.player.relics.remove("second_chance")
                self.player.hp = max(1, int(self.player.max_hp * 0.15))
                self.add_log("[magenta]Second Chance shatters, pulling you back from death![/magenta]")
                return
            self.over = True
            self.won = False
            if self.mirror_fight:
                self.mirror_defeated = True
                self.player.hp = 1

    def damage_player(self, dmg, source=None):
        if self.next_hit_blocked:
            self.next_hit_blocked = False
            self.add_log("[cyan]The attack passes right through you![/cyan]")
            return
        if self.vulnerable > 0:
            dmg = int(dmg * 1.5)
        if self.resist > 0 and dmg > 0:
            dmg = max(0, dmg - int(dmg * self.resist / 100))
        if self.player.talent_strong > 0 and dmg > 0:
            dmg = max(0, dmg - self.player.talent_strong)
        raw_dmg = dmg
        if self.block > 0:
            absorbed = min(self.block, dmg)
            self.block -= absorbed
            dmg -= absorbed
        if "torii" in self.player.relics and 0 < dmg <= 5:
            dmg = 1
        if self.guard > 0 and raw_dmg > 0 and source is not None and source.alive():
            reflected = self.guard
            source.take_damage(reflected)
            self.add_log(f"[gold1]Counter reflects {reflected} damage back at {source.name}![/gold1]")
            self.guard = 0
        if dmg > 0:
            self.player.hp -= dmg
            self.player.stats["damage_taken"] += dmg
            if self.player.character == "berserker":
                self.strength += 1
                self.add_log("[gold1]Berserker fury: +1 Strength![/gold1]")
        self.player.hp = max(0, self.player.hp)
        if "iron_will" in self.player.relics and not self.iron_will_triggered \
                and self.player.hp < self.player.max_hp * 0.25:
            self.iron_will_triggered = True
            self.strength += 1
            self.add_log("[gold1]Iron Will: +1 Strength![/gold1]")
        if "bronze_scales" in self.player.relics and raw_dmg > 0 and source is not None and source.alive():
            source.take_damage(3)
            self.add_log("[cyan]Bronze Scales reflects 3 damage![/cyan]")

    def alive_enemies(self):
        return [e for e in self.enemies if e.alive()]

    def _combat_can_end_in_victory(self):
        """False if any enemy is dead but still has self-revivals pending —
        the fight isn't really over yet."""
        for e in self.enemies:
            if e.alive():
                return False
            if e.self_revives and e.revives_left > 0:
                return False
        return True

    def _deal_damage(self, enemy, dmg):
        dmg = self.apply_weak(dmg)
        if enemy.vulnerable > 0:
            dmg = int(dmg * 1.5)
        if "boot" in self.player.relics and dmg > 0:
            dmg = max(dmg, 5)
        enemy.take_damage(dmg)
        self.player.stats["damage_dealt"] += dmg
        if self.player.talent_lifesteal_pct > 0 and dmg > 0:
            healed = (dmg * self.player.talent_lifesteal_pct) // 100
            if healed > 0:
                self.player.hp = min(self.player.max_hp, self.player.hp + healed)

    def can_play(self, card):
        if card.get("x_cost"):
            return True
        base_cost = card.get("cost", 0)
        if base_cost == 0:
            return True
        if self.next_card_free:
            return True
        if not self.free_card_used_this_turn and "windfall_charm" in self.player.relics:
            return True
        return self.energy >= base_cost

    def _execute_mirror_replay(self, target_enemy):
        if self.last_played_card is None:
            self.add_log("[grey62]Mirror Card has nothing to copy — it fizzles.[/grey62]")
            return
        original = self.last_played_card
        replay_cost = original.get("cost", 0)
        if self.energy < replay_cost:
            self.add_log(f"[red]Not enough Energy to echo {original['name']} — it fizzles.[/red]")
            return
        replay_target = target_enemy
        if replay_target is None and original["type"] == "attack" and not original.get("aoe") \
                and not original.get("x_cost"):
            alive = self.alive_enemies()
            if alive:
                replay_target = min(alive, key=lambda en: en.hp)
        self.add_log(f"[gold1]Mirror Card echoes {original['name']}![/gold1]")
        echo_copy = copy.deepcopy(original)
        self.play_card(echo_copy, replay_target)

    def play_card(self, card, target_enemy=None):
        if not self.can_play(card):
            return False
        cost = card["cost"]
        if card.get("x_cost"):
            cost = self.energy
        elif cost > 0:
            if self.next_card_free:
                cost = 0
                self.next_card_free = False
                self.add_log("[cyan]Haste: this card is free![/cyan]")
            elif not self.free_card_used_this_turn and "windfall_charm" in self.player.relics:
                cost = 0
                self.free_card_used_this_turn = True
                self.add_log("[cyan]Windfall Charm: this card is free![/cyan]")

        eff_str = self.strength + self.temp_strength
        echo_mult = 2 if (self.player.character == "twin" and self.echo_active) else 1
        refunded = False

        if self.player.talent_bless > 0 and card["type"] in ("skill", "magic"):
            self.player.hp = min(self.player.max_hp, self.player.hp + self.player.talent_bless)

        if card["type"] == "attack":
            if card.get("x_cost"):
                hits = cost
                for _ in range(hits):
                    for t in self.alive_enemies():
                        self._deal_damage(t, (card["damage"] + eff_str) * echo_mult)
            elif card.get("aoe"):
                if card.get("sin_scaled_aoe"):
                    dmg = (self.sin * card.get("sin_pct", 100)) // 100
                else:
                    dmg = (card["damage"] + eff_str) * echo_mult
                for t in self.alive_enemies():
                    self._deal_damage(t, dmg)
                    if card.get("vulnerable"):
                        t.vulnerable += card["vulnerable"]
                        if "champion_belt" in self.player.relics:
                            t.weak += 1
                    if card.get("poison"):
                        t.poison += card["poison"] * echo_mult
                    if card.get("weak"):
                        t.weak += card["weak"]
                    if card.get("frail"):
                        t.frail += card["frail"]
                    if card.get("burning"):
                        t.burning += card["burning"]
                    if card.get("wound"):
                        t.wound += card["wound"]
            else:
                if card.get("poison_execute"):
                    base_dmg = max(card.get("min_damage", 0),
                                    (target_enemy.poison if target_enemy else 0) * card.get("poison_mult", 2))
                    dmg = base_dmg * echo_mult
                elif card.get("scales_with_cards_played"):
                    base_dmg = self.cards_played * card.get("cards_played_mult", 2)
                    dmg = base_dmg * echo_mult
                elif card.get("scales_with_attacks_played"):
                    base_dmg = card.get("damage", 0) + self.attacks_played * card.get("attacks_played_mult", 1)
                    dmg = base_dmg * echo_mult
                elif card.get("scales_with_missing_hp"):
                    missing = max(0, self.player.max_hp - self.player.hp)
                    base_dmg = card.get("damage", 0) + missing // card.get("missing_hp_divisor", 8)
                    dmg = base_dmg * echo_mult
                elif card.get("damage_eq_armor_pct"):
                    dmg = (self.block * card["damage_eq_armor_pct"]) // 100
                else:
                    mult = card.get("str_mult", 1)
                    base_dmg = self.block if card.get("damage_eq_block") else card.get("damage", 0) + card.get("growth", 0)
                    dmg = (base_dmg + eff_str * mult) * echo_mult
                hits = card.get("hits", 1)
                if card.get("hits_scale_with_hand_attacks"):
                    hits = card.get("base_hits", 1) + sum(
                        1 for hc in self.hand if hc.get("type") == "attack" and hc is not card)
                if card.get("double_if_sneak") and self.sneak:
                    dmg *= 2
                if card.get("scales_with_deck_attacks"):
                    hits += sum(1 for dc in self.player.deck
                                if dc.get("type") == "attack" and dc is not card)
                if target_enemy:
                    was_wounded = target_enemy.wound > 0
                    pre_block = self.block
                    for _ in range(hits):
                        self._deal_damage(target_enemy, dmg)
                    if card.get("damage_eq_armor_pct"):
                        self.block -= pre_block // 2
                    if card.get("heal_half_if_wounded") and was_wounded:
                        healed = dmg // 2
                        self.player.hp = min(self.player.max_hp, self.player.hp + healed)
                        self.add_log(f"[green]{card['name']} heals {healed} HP (target was Wounded).[/green]")
                    if card.get("consumes_sneak"):
                        self.sneak = False
                    if card.get("refund_energy_on_kill") and not target_enemy.alive():
                        refunded = True
                        self.add_log(f"[gold1]{card['name']} refunds its Energy cost![/gold1]")
                    if card.get("strength_on_kill") and not target_enemy.alive():
                        self.strength += card["strength_on_kill"]
                        self.add_log(f"[gold1]{card['name']} grants +{card['strength_on_kill']} Strength![/gold1]")
                    if card.get("grows_on_kill") and not target_enemy.alive():
                        card["growth"] = card.get("growth", 0) + card["grows_on_kill"]
                        from cards import describe_card as _describe_card
                        card["desc"] = _describe_card(card)
                        self.add_log(f"[gold1]{card['name']} grows stronger! (+{card['grows_on_kill']} damage, permanent)[/gold1]")
                    if card.get("vulnerable"):
                        target_enemy.vulnerable += card["vulnerable"]
                        if "champion_belt" in self.player.relics:
                            target_enemy.weak += 1
                    if card.get("poison"):
                        target_enemy.poison += card["poison"] * echo_mult
                    if card.get("weak"):
                        target_enemy.weak += card["weak"]
                    if card.get("frail"):
                        target_enemy.frail += card["frail"]
                    if card.get("burning"):
                        target_enemy.burning += card["burning"]
                        self.add_log(f"[orange3]{target_enemy.name} catches fire ({card['burning']} Burning).[/orange3]")
                    if card.get("wound"):
                        wound_amt = card["wound"] * (2 if (card.get("double_if_sneak") and self.sneak) else 1)
                        target_enemy.wound += wound_amt
                    if card.get("splash_half_random"):
                        others = [e for e in self.alive_enemies() if e is not target_enemy]
                        if others:
                            splash_target = random.choice(others)
                            self._deal_damage(splash_target, dmg // 2)
                            self.add_log(f"[cyan]{card['name']} splashes {dmg // 2} onto {splash_target.name}![/cyan]")
                    if card.get("draw_if_hand_empty") and not self.hand:
                        self.draw_one()

        if card.get("discard_then_bonus"):
            dropped = self._discard_random_hand_card(exclude=card)
            if dropped:
                if card.get("block"):
                    gained = (card["block"] + self.dexterity) * echo_mult
                    if self.frail > 0:
                        gained = int(gained * 0.75)
                    self.block += gained
                if card.get("resist"):
                    self.resist += card["resist"]
                self.add_log(f"[cyan]{card['name']} discards {dropped['name']} to fuel itself.[/cyan]")
            else:
                self.add_log(f"[grey62]{card['name']} has nothing to discard — it fizzles.[/grey62]")
        else:
            if card.get("block"):
                gained = (card["block"] + self.dexterity) * echo_mult
                if self.frail > 0:
                    gained = int(gained * 0.75)
                self.block += gained
        if card.get("guard") and not card.get("discard_then_bonus"):
            self.guard += card["guard"]
        if card.get("double_block"):
            self.block *= 2
        if card.get("draw"):
            for _ in range(card["draw"]):
                self.draw_one()
        if card.get("temp_str"):
            self.temp_strength += card["temp_str"]
        if card.get("strength"):
            self.strength += card["strength"]
        if card.get("dexterity"):
            self.dexterity += card["dexterity"]
        if card.get("metallicize"):
            self.metallicize += card["metallicize"]
        if card.get("combust"):
            self.combust += card["combust"]
        if card.get("lose_hp"):
            self.player.hp = max(0, self.player.hp - card["lose_hp"])
        if card.get("gain_energy"):
            self.energy += card["gain_energy"]
        if card.get("grants_card"):
            from cards import make_card as _make_card
            granted = _make_card(card["grants_card"])
            self.hand.append(granted)
            self.add_log(f"[gold1]Gained a free {granted['name']}![/gold1]")
        if card.get("grants_random_card"):
            from cards import make_card as _make_card, REWARD_POOL as _REWARD_POOL
            granted = _make_card(random.choice(_REWARD_POOL))
            self.hand.append(granted)
            self.add_log(f"[gold1]Wind Blade draws forth: {granted['name']}![/gold1]")
        if card.get("grant_echo"):
            self.echo_active = True
            self.add_log("[gold1]Echo charged instantly! Next card is doubled.[/gold1]")
        if card.get("is_mirror_card"):
            self._execute_mirror_replay(target_enemy)
        if card.get("discard_gain_energy_draw"):
            dropped = self._discard_random_hand_card(exclude=card)
            if dropped:
                gained_e = 0 if dropped.get("x_cost") else dropped.get("cost", 0)
                self.energy += gained_e
                self.draw_one()
                self.add_log(f"[cyan]Recast discards {dropped['name']}, gaining {gained_e} Energy.[/cyan]")
            else:
                self.add_log("[grey62]Recast has nothing to discard — it fizzles.[/grey62]")
        if card.get("duplicate_hand_cards"):
            candidates = [c for c in self.hand if c is not card]
            n = min(card["duplicate_hand_cards"], len(candidates))
            for _ in range(n):
                pick = random.choice(candidates)
                self.hand.append(copy.deepcopy(pick))
            if n:
                self.add_log(f"[gold1]Copy clones {n} card(s) into your hand![/gold1]")
            else:
                self.add_log("[grey62]Copy has nothing to clone — it fizzles.[/grey62]")
        if card.get("draw_per_poisoned_enemy"):
            n = sum(1 for e in self.alive_enemies() if e.poison > 0)
            if n:
                for _ in range(n):
                    self.draw_one()
                self.add_log(f"[cyan]Honor of Poison draws {n} card(s)![/cyan]")
        if card.get("sneak_flag"):
            self.sneak = True
            self.add_log("[magenta]You vanish into the shadows (Sneak).[/magenta]")
        if card.get("remove_sin"):
            n = min(card["remove_sin"], self.sin)
            self.sin -= n
            if n:
                heal = n * card.get("heal_per_sin", 0)
                self.player.hp = min(self.player.max_hp, self.player.hp + heal)
                self.add_log(f"[green]Redemption clears {n} Sin, healing {heal} HP.[/green]")
        if card.get("remove_sin_all"):
            n = min(card["remove_sin_all"], self.sin)
            self.sin -= n
            self.add_log(f"[cyan]Eliminate clears {n} Sin.[/cyan]")

        if not refunded:
            self.energy -= cost
        self.player.stats["cards_played"] += 1
        if not card.get("is_mirror_card"):
            self.last_played_card = card
        # Remove by identity, not value equality — avoids duplicate-card confusion
        for i, hcard in enumerate(self.hand):
            if hcard is card:
                self.hand.pop(i)
                break
        if card.get("exhaust"):
            self.exhaust_pile.append(card)
            if "charons_ashes" in self.player.relics:
                for e in self.alive_enemies():
                    e.hp = max(0, e.hp - 3)
                self.add_log("[red]Charon's Ashes burns all enemies for 3![/red]")
                if self._combat_can_end_in_victory():
                    self._mark_win()
        else:
            self.discard_pile.append(card)
        if echo_mult == 2:
            self.add_log(f"[gold1]Echo doubles {card['name']}![/gold1]")
            self.echo_active = False
        else:
            self.add_log(f"You play {card['name']}.")

        if self.player.character == "twin":
            self.cards_played += 1
            if self.cards_played % 4 == 0:
                self.echo_active = True
                self.add_log("[gold1]Echo charged! Next card is doubled.[/gold1]")

        if card["type"] == "attack":
            self.attacks_played += 1
            if self.player.character == "sord" and self.attacks_played % 3 == 0:
                from cards import make_card
                bonus = make_card("bonus_stab")
                self.hand.append(bonus)
                self.add_log("[gold1]Sord's technique: a free Stab appears in hand![/gold1]")
            if "shuriken" in self.player.relics and self.attacks_played % 3 == 0:
                self.strength += 1
                self.add_log("[gold1]Shuriken: +1 Strength![/gold1]")
            if "kunai" in self.player.relics and self.attacks_played % 3 == 0:
                self.dexterity += 1
                self.add_log("[gold1]Kunai: +1 Dexterity![/gold1]")

        if self._combat_can_end_in_victory():
            self._mark_win()
        return True

    def use_potion(self, potion_id, target_enemy=None):
        from potions import POTION_LIBRARY
        p = POTION_LIBRARY[potion_id]
        m = 2 if "sacred_bark" in self.player.relics else 1
        if potion_id == "fire_potion" and target_enemy:
            self._deal_damage(target_enemy, 20 * m)
        elif potion_id == "block_potion":
            self.block += 12 * m
        elif potion_id == "energy_potion":
            self.energy += 2 * m
        elif potion_id == "strength_potion":
            self.strength += 2 * m
        elif potion_id == "weak_potion" and target_enemy:
            target_enemy.weak += 3 * m
        elif potion_id == "vulnerable_potion" and target_enemy:
            target_enemy.vulnerable += 2 * m
        elif potion_id == "heal_potion":
            self.player.hp = min(self.player.max_hp, self.player.hp + 15 * m)
        elif potion_id == "frail_potion" and target_enemy:
            target_enemy.frail += 3 * m
        elif potion_id == "swift_potion":
            for _ in range(2 * m):
                self.draw_one()
        elif potion_id == "elixir":
            self.player.hp = self.player.max_hp
            self.weak = 0
            self.vulnerable = 0
            self.frail = 0
        elif potion_id == "toxic_potion" and target_enemy:
            target_enemy.poison += 4 * m
        elif potion_id == "cunning_potion":
            self.energy += 1 * m
            for _ in range(1 * m):
                self.draw_one()
        elif potion_id == "gamblers_brew":
            outcome = random.choice(["damage", "block", "strength", "cost"])
            if outcome == "damage" and target_enemy:
                self._deal_damage(target_enemy, 25 * m)
                self.add_log("[red]Gambler's Brew: big damage![/red]")
            elif outcome == "block":
                self.block += 20 * m
                self.add_log("[blue]Gambler's Brew: big block![/blue]")
            elif outcome == "strength":
                self.strength += 3 * m
                self.add_log("[gold1]Gambler's Brew: Strength surge![/gold1]")
            else:
                self.player.hp = max(1, self.player.hp - 5)
                self.add_log("[red]Gambler's Brew backfires: -5 HP![/red]")
        elif potion_id == "ambrosia":
            self.player.hp = self.player.max_hp
            self.strength += 3 * m
            self.dexterity += 3 * m
        elif potion_id == "insight_potion":
            for _ in range(3 * m):
                self.draw_one()
            self.energy += 1 * m
        elif potion_id == "regeneration_potion":
            self.regen_turns_left = 2
            self.regen_amount = 4 * m
        elif potion_id == "haste_potion":
            self.next_card_free = True
        elif potion_id == "invisibility_potion":
            self.next_hit_blocked = True
        elif potion_id == "berserk_potion":
            self.strength += 3 * m
            self.vulnerable += 2
        self.add_log(f"You drink {p['name']}.")
        self.player.stats["potions_used"] += 1
        if self._combat_can_end_in_victory():
            self._mark_win()

    def generate_rewards(self):
        from cards import REWARD_POOL, make_card
        pool = REWARD_POOL[:]
        random.shuffle(pool)
        self.reward_cards = [make_card(c) for c in pool[:3]]

    # ---------------- rendering ----------------
    def render(self):
        console.clear()
        console.rule(f"[bold yellow]Turn {self.turn}[/bold yellow]")

        # enemies
        panels = []
        for i, e in enumerate(self.enemies):
            if e.alive():
                body = ""
                if SHOW_ASCII_ART:
                    art = get_enemy_art(e.key)
                    if art:
                        body += f"[grey70]{escape(art.strip(chr(10)))}[/grey70]\n"
                body += f"HP: [red]{e.hp}/{e.max_hp}[/red]\n"
                if e.block:
                    body += f"Block: [blue]{e.block}[/blue]\n"
                if e.strength:
                    body += f"STR: [gold1]+{e.strength}[/gold1]\n"
                if e.poison:
                    body += f"Poison: [green]{e.poison}[/green]\n"
                if e.weak:
                    body += f"Weak: [grey62]{e.weak}[/grey62]\n"
                if e.vulnerable:
                    body += f"Vulnerable: [orange3]{e.vulnerable}[/orange3]\n"
                if e.frail:
                    body += f"Frail: [grey62]{e.frail}[/grey62]\n"
                if e.burning:
                    body += f"Burning: [orange3]{e.burning}[/orange3]\n"
                if e.wound:
                    body += f"Wound: [red3]{e.wound}[/red3]\n"
                if e.guard_shield:
                    body += "[bold cyan]Shielded — first hit blocked[/bold cyan]\n"
                if e.flee_after_turn is not None and "greed_charm" not in self.player.relics:
                    if self.turn >= e.flee_after_turn:
                        body += "[bold yellow]Fleeing this turn![/bold yellow]\n"
                    else:
                        body += f"[yellow]Flees after turn {e.flee_after_turn}![/yellow]\n"
                body += f"Intent: [yellow]{e.intent_desc(getattr(self.player, 'ascension', 0))}[/yellow]"
                title = f"[{i+1}] {e.name}"
                if e.elite:
                    title += " [magenta](ELITE)[/magenta]"
                if e.boss:
                    title += " [red](BOSS)[/red]"
            else:
                if self.slime_swarm:
                    if e.revive_in and e.revive_in > 0:
                        body = f"[dim]Decaying corpse[/dim]\n[grey62]Slot opens in {e.revive_in} turn(s)[/grey62]"
                    else:
                        body = "[green]Empty slot — ready[/green]"
                elif e.escaped:
                    body = "[yellow]Fled with your gold![/yellow]"
                elif e.self_revives and e.revives_left > 0 and e.revive_in is not None:
                    body = f"[dim]A pile of bones...[/dim]\n[grey62]Rises again in {e.revive_in} turn(s)[/grey62]"
                else:
                    body = "[dim]defeated[/dim]"
                title = f"[{i+1}] {e.name}"
            panels.append(Panel(body, title=title, border_style="red" if e.alive() else "grey50", width=34))
        console.print(Columns(panels))

        # player status
        if self.player.game_mode == "lophis":
            cap = self.player.max_energy * 4
            energy_txt = f"Energy: [yellow]{self.energy}[/yellow] [grey62](cap {cap}, banking)[/grey62]"
        else:
            energy_txt = f"Energy: [yellow]{self.energy}/{self.player.max_energy}[/yellow]"
        block_label = "Armor" if self.player.game_mode == "lophis" else "Block"
        pstat = (f"HP: [red]{self.player.hp}/{self.player.max_hp}[/red]   "
                 f"{block_label}: [blue]{self.block}[/blue]   "
                 f"{energy_txt}")
        if self.strength or self.temp_strength:
            pstat += f"   STR: [gold1]+{self.strength + self.temp_strength}[/gold1]"
        if self.dexterity:
            pstat += f"   DEX: [gold1]+{self.dexterity}[/gold1]"
        if self.weak:
            pstat += f"   WEAK: [grey62]{self.weak}[/grey62]"
        if self.frail:
            pstat += f"   FRAIL: [grey62]{self.frail}[/grey62]"
        if self.resist:
            pstat += f"   RESIST: [cyan]{self.resist}%[/cyan]"
        if self.guard:
            pstat += f"   COUNTER: [cyan]{self.guard}[/cyan]"
        if self.sneak:
            pstat += "   [magenta]SNEAK[/magenta]"
        if self.player.character == "monk":
            pstat += f"   SIN: [red3]{self.sin}[/red3]"
        if self.player.character == "twin":
            charge = self.cards_played % 4
            if self.echo_active:
                pstat += "   [gold1]ECHO READY![/gold1]"
            else:
                pstat += f"   Echo: [grey62]{charge}/4[/grey62]"
        if (self.player.character == "sord" or "shuriken" in self.player.relics
                or "kunai" in self.player.relics):
            pstat += f"   Attacks: [grey62]{self.attacks_played % 3}/3[/grey62]"
        if self.exhaust_pile:
            pstat += f"   Exhausted: [grey62]{len(self.exhaust_pile)}[/grey62]"
        if self.player.potions:
            from potions import POTION_LIBRARY
            names = ", ".join(POTION_LIBRARY[p]["name"] for p in self.player.potions)
            pstat += f"\nPotions: [green]{names}[/green]"
        console.print(Panel(pstat, title="You", border_style="green"))

        # log
        if self.log:
            console.print(Panel("\n".join(self.log), title="Log", border_style="grey50"))

        # hand
        table = Table(title="Your Hand")
        table.add_column("#")
        table.add_column("Name")
        table.add_column("Cost")
        table.add_column("Type")
        table.add_column("Effect")
        for i, card in enumerate(self.hand):
            color = TYPE_COLOR[card["type"]]
            icon = TYPE_ICON[card["type"]]
            afford = self.can_play(card)
            style = color if afford else "grey50"
            cost_disp = "X" if card.get("x_cost") else str(card["cost"])
            table.add_row(str(i + 1), f"[{style}]{icon} {card['name']}[/{style}]", cost_disp,
                          card["type"], card["desc"])
        console.print(table)

    def render_reward(self):
        console.print(Panel("[bold gold1]Victory![/bold gold1]", border_style="gold1"))
        table = Table(title="Choose a card reward (or 's' to skip)")
        table.add_column("#")
        table.add_column("Name")
        table.add_column("Cost")
        table.add_column("Effect")
        for i, card in enumerate(self.reward_cards):
            color = TYPE_COLOR[card["type"]]
            table.add_row(str(i + 1), f"[{color}]{card['name']}[/{color}]", str(card["cost"]), card["desc"])
        console.print(table)
