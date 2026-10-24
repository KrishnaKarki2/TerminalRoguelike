from cards import starter_deck, CLASSES


class Player:
    def __init__(self, character="warrior", ascension=0, game_mode="normal"):
        info = CLASSES[character]
        self.character = character
        self.ascension = ascension
        self.game_mode = game_mode
        self.max_hp = info["max_hp"]
        self.hp = self.max_hp
        self.gold = 99
        self.deck = starter_deck(character)
        self.max_energy = info["max_energy"]
        self.relics = []
        self.potions = []
        self.max_potions = 3
        self.stats = dict(damage_dealt=0, damage_taken=0, cards_played=0,
                           enemies_defeated=0, potions_used=0, turns_survived=0)
        self.bonus_strength = 0
        self.bonus_dexterity = 0
        self.talents = {}          # {talent_id: level}, Lophis mode only
        self.talent_hand_limit = 0
        self.talent_draw = 0
        self.talent_lifesteal_pct = 0
        self.talent_bless = 0
        self.talent_strong = 0
        self.talent_guard_per_turn = 0

    def alive(self):
        return self.hp > 0
