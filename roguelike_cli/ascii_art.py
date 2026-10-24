# ============================================================
# ASCII ART TOGGLE
# Set this to False to hide all ASCII art (enemies + characters)
# and just show plain text. Set to True to show it.
# ============================================================
SHOW_ASCII_ART = True

# ============================================================
# ATTACK ANIMATION TOGGLE
# Set this to False to skip the quick ASCII animation that plays
# after an attack card lands. Set to True to show it.
# ============================================================
SHOW_ATTACK_ANIMATIONS = True
ANIMATION_FRAME_DELAY = 0.12  # seconds between frames — tweak for taste


CLASS_ART = {
    "warrior": r"""
   [####]
   |o  o|
   |    |
  /|====|\
 / |{__}|  \
   |    |
  _|    |_
 |_|    |_|
""",
    "rogue": r"""
    .---.
   / o o \
   \  ~  /
    '---'
   /||||\
  / |||| \
    |  |
   _|  |_
""",
    "twin": r"""
  .-. .-.
 (o.o)(o.o)
  |=|  |=|
 /| |\/| |\
   |    |
  _|    |_
""",
    "sord": r"""
    _/\_
   |o  o|
   | -- |
  /|>==<|\
 / |    | \
   |    |
  _|    |_
""",
    "berserker": r"""
   \  |  /
  \ .-. /
 --( ò_ó )--
    |=|
   /| |\
  / | | \
""",
}

ENEMY_ART = {
    "slime": r"""
   _______
  /       \
 |  o   o  |
 |   ___   |
  \_______/
   ~ ~ ~ ~
""",
    "cultist": r"""
    /\
   /  \
  | () |
  |    |
 /|robe|\
  |    |
""",
    "goblin": r"""
   ,   ,
   (o.o)
  <)   )>
   /   \
  _|   |_
""",
    "jaw_worm": r"""
  ______
 <(o  o)>
  \ vv /
   |  |
  _|  |_
""",
    "spider": r"""
 \  |  |  /
  \ | | /
   (o.o)
  / | | \
 /  |  |  \
""",
    "brute": r"""
  .-----.
 /  o o  \
 |   ^   |
 |  ___  |
/|_______|\
""",
    "wraith": r"""
   .-""-.
  / .--. \
  | |  | |
  | '--' |
   \.--./
    '  '
""",
    "bandit": r"""
   ,-----.
  ( o   o )
  |  [_]  |
  |  /$\  |
   \_____/
""",
    "specter": r"""
    .;;;.
   ;  o  ;
   ;  o  ;
    ';;;'
     | |
""",
    "ooze": r"""
   .-~~~-.
  (  o o  )
  ( ~___~ )
   '-...-'
    ~ ~ ~
""",
    "knight_elite": r"""
   [=====]
   |o   o|
   |  V  |
  /|=====|\
 / |     | \
   |=====|
""",
    "ogre_elite": r"""
  .-------.
 /  O   O  \
 |    ^    |
 |  \___/  |
/|_________|\
   |     |
""",
    "banshee_elite": r"""
    .-'"'-.
   /  ; ;  \
  |   ~~~   |
   \  ...  /
    '.___.'
     | | |
""",
    "guardian_boss": r"""
  #############
  #  [O] [O]  #
  #     ^     #
  #   =====   #
 ##/#########\##
""",
    "lich_boss": r"""
    .-'''-.
   / .-. .-\
   | ( ) ( )|
   |   ---  |
    \_______/
    /|     |\
""",
    "dragon_boss": r"""
     /\   /\
    (  \-/  )
   __\     /__
  <   O   O   >
    \  ---  /
     \_____/
""",
    "revenant": r"""
   .-~~~-.
  /  x x  \
 |    ~    |
  \  ---  /
   '-...-'
""",
    "golem": r"""
  [========]
  [ O    O ]
  [   ==   ]
  [========]
   |      |
""",
    "cursed_knight": r"""
   ,-----.
  ( x   x )
  |  ###  |
 /|_______|\
   |     |
""",
    "shade_elite": r"""
    .;;;;;.
   ;   .   ;
   ;  ;;;  ;
    ';;;;;'
    /  |  \
   /   |   \
""",
    "warlord_elite": r"""
  .---------.
 /  \\   //  \
 |   O   O   |
 |   =====   |
/|___________|\
""",
    "hydra_boss": r"""
  /^\  /^\  /^\
 ( o )( o )( o )
  \_/  \_/  \_/
   \    |    /
    \___|___/
""",
    "lophis_slime": r"""
   _______
  /  ; ;  \
 |   ...   |
  \_______/
   ~ ~ ~ ~
""",
    "gold_goblin": r"""
   ,   ,
   ($.$)
  <)   )> $
   /   \
  _|   |_
""",
    "skeleton": r"""
   .-.
  (o.o)
   |=|
  __|__
 //   \\
""",
    "castle_guard": r"""
   [#####]
   |o   o|
   |  =  |
  /|#####|\
   |  |A|
""",
    "enraged_duck": r"""
   __
  <(o )___
   ( ._> /
    `---'
""",
}


def get_enemy_art(enemy_key):
    return ENEMY_ART.get(enemy_key)


def get_class_art(character_key):
    return CLASS_ART.get(character_key)


# ============================================================
# ATTACK ANIMATIONS
# Each entry is a list of frames, printed in sequence with a short
# pause between them. The last frame is the "impact" beat.
# ============================================================
ATTACK_FRAMES = {
    "slash": [
        "        ⚔",
        "       ╱",
        "      ╱",
        "  ╲  ╱",
        "   ╲╱",
        "[bold white]   ─────╳─────[/bold white]",
        "[bold red]  ✦═══ SLASH ═══✦[/bold red]",
    ],
    "cleave": [
        "   ⚔     ⚔     ⚔",
        "    ╲    │    ╱",
        "     ╲   │   ╱",
        "[bold white]  ───╲──┼──╱───[/bold white]",
        "[bold red]  ✦══ CLEAVE ══✦[/bold red]",
    ],
    "stab": [
        "   ▷",
        "    ▷▷",
        "      ▷▷▷",
        "[bold white]        ▷▷▷▶[/bold white]",
        "[bold red]  ✦═ IMPALE ═✦[/bold red]",
    ],
    "poison": [
        "    ☠",
        "   ╲│╱",
        "    ▼",
        "[bold green]  ~ ~ TOXIC ~ ~[/bold green]",
    ],
    "block": [
        "   ┌───┐",
        "   │ ▓ │",
        "[bold cyan]   └───┘ GUARD[/bold cyan]",
    ],
    "heavy": [
        "     ⚒",
        "      ╲",
        "       ╲",
        "        ╲",
        "[bold white]   ────╲────[/bold white]",
        "[bold red]  ✦══ CRUSH ══✦[/bold red]",
    ],
}


def play_attack_animation(console, kind="slash"):
    """Print a short ASCII animation. Caller is responsible for checking
    SHOW_ATTACK_ANIMATIONS before calling this."""
    import time
    frames = ATTACK_FRAMES.get(kind, ATTACK_FRAMES["slash"])
    for frame in frames:
        console.print(frame)
        time.sleep(ANIMATION_FRAME_DELAY)
