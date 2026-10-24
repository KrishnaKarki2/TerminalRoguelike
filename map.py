import random

NODE_TYPES = {
    "fight": {"color": (200, 90, 90), "icon": "F"},
    "elite": {"color": (170, 90, 200), "icon": "E"},
    "rest": {"color": (90, 190, 110), "icon": "R"},
    "shop": {"color": (220, 190, 80), "icon": "$"},
    "boss": {"color": (230, 60, 60), "icon": "B"},
    "treasure": {"color": (250, 215, 90), "icon": "T"},
    "event": {"color": (170, 120, 200), "icon": "?"},
    "gauntlet": {"color": (210, 130, 40), "icon": "G"},
}


class Node:
    def __init__(self, row, col, ntype):
        self.row = row
        self.col = col
        self.ntype = ntype
        self.next_nodes = []  # list of Node
        self.visited = False
        self.available = False
        self.x = 0
        self.y = 0


class GameMap:
    ROWS = 26
    COLS_PER_ROW = 7
    REST_INTERVAL = 6  # a guaranteed rest checkpoint every N rows

    # Lophis mode: real dungeon shapes from Call of Lophis's dungeon.lua (per-floor
    # width x node-count; the game has 4 floors before the boss, we compress that
    # into rows here). method 'full' = fully connected grid, 'prim' = a pruned maze.
    LOPHIS_FLOORS = [
        dict(width=8, num=16, method="full"),
        dict(width=13, num=14, method="full"),
        dict(width=13, num=12, method="prim"),
        dict(width=4, num=2, method="full"),
    ]

    def __init__(self, lophis=False):
        self.rows = []
        self.current_row = -1
        self.lophis = lophis
        if lophis:
            self._generate_lophis()
        else:
            self._generate()

    def _generate_lophis(self):
        """Lay out rows using the real per-floor widths/densities from Call of Lophis,
        instead of this engine's usual fixed 26-row spire. Each floor ends on a boss row."""
        row_idx = 0
        for floor_i, floor in enumerate(self.LOPHIS_FLOORS):
            is_last_floor = floor_i == len(self.LOPHIS_FLOORS) - 1
            avg_per_row = max(1, floor["num"] // max(1, floor["width"] // 3))
            remaining = floor["num"]
            floor_rows = max(1, floor["width"] // 3)
            for fr in range(floor_rows):
                is_boss_row = is_last_floor and fr == floor_rows - 1
                if is_boss_row:
                    self.rows.append([Node(row_idx, 0, "boss")])
                else:
                    ncols = max(1, min(remaining, random.randint(max(1, avg_per_row - 1), avg_per_row + 1)))
                    remaining -= ncols
                    row_nodes = []
                    for c in range(ncols):
                        if row_idx == 0:
                            t = "fight"
                        elif floor["method"] == "prim":
                            # a pruned maze skews toward events/treasure over straight fights
                            t = random.choices(
                                ["fight", "event", "shop", "elite", "treasure", "rest"],
                                weights=[3, 3, 2, 1, 2, 1])[0]
                        else:
                            t = random.choices(
                                ["fight", "event", "shop", "rest", "elite", "treasure"],
                                weights=[5, 3, 2, 1, 1, 1])[0]
                        row_nodes.append(Node(row_idx, c, t))
                    self.rows.append(row_nodes)
                row_idx += 1
        self._connect_rows()

    def _generate(self):
        rest_rows = set(range(self.REST_INTERVAL, self.ROWS - 1, self.REST_INTERVAL))
        rest_rows.add(self.ROWS - 2)  # always rest right before the boss

        for r in range(self.ROWS):
            row_nodes = []
            if r == self.ROWS - 1:
                row_nodes.append(Node(r, 0, "boss"))
            elif r in rest_rows:
                row_nodes.append(Node(r, 0, "rest"))
            else:
                ncols = random.randint(2, self.COLS_PER_ROW)
                pre_rest = (r + 1) in rest_rows
                for c in range(ncols):
                    if r == 0:
                        t = "fight"
                    elif pre_rest:
                        t = random.choice(["elite", "shop", "fight", "treasure", "event"])
                    else:
                        t = random.choices(
                            ["fight", "shop", "rest", "elite", "treasure", "event", "gauntlet"],
                            weights=[5, 2, 1, 1, 1, 2, 1])[0]
                    row_nodes.append(Node(r, c, t))
            self.rows.append(row_nodes)
        self._connect_rows()

    def _connect_rows(self):
        # connect rows: each node connects to 1-2 nodes in next row
        for r in range(len(self.rows) - 1):
            cur = self.rows[r]
            nxt = self.rows[r + 1]
            for node in cur:
                if len(nxt) == 1:
                    targets = nxt
                else:
                    # connect to nearest column(s)
                    base = min(int(node.col * (len(nxt) - 1) / max(1, len(cur) - 1)), len(nxt) - 1) if len(cur) > 1 else 0
                    choices = {base}
                    if random.random() < 0.5 and base + 1 < len(nxt):
                        choices.add(base + 1)
                    if random.random() < 0.3 and base - 1 >= 0:
                        choices.add(base - 1)
                    targets = [nxt[i] for i in sorted(choices)]
                node.next_nodes = targets
            # ensure every node in nxt has an incoming edge
            reached = set()
            for node in cur:
                for t in node.next_nodes:
                    reached.add(id(t))
            for t in nxt:
                if id(t) not in reached:
                    random.choice(cur).next_nodes.append(t)

        # mark first row available
        for node in self.rows[0]:
            node.available = True

    def get_current_options(self):
        if self.current_row == -1:
            return self.rows[0]
        cur_nodes = [n for n in self.rows[self.current_row] if n.visited]
        options = []
        for n in cur_nodes:
            options.extend(n.next_nodes)
        return options

    def choose(self, node):
        node.visited = True
        self.current_row = node.row
        # update availability
        options = self.get_current_options()
        for row in self.rows:
            for n in row:
                n.available = n in options
