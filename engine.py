"""
engine.py - SER Protocol Battle Engine
Turn-based 2-player grid combat simulation.
"""

# --- Constants ---
GRID_ROWS = 15
GRID_COLS = 15
MAX_TURNS = 150
STARTING_HP = 100
STARTING_AMMO = 10
BULLET_DAMAGE = 25
HEALTH_PACK_RESTORE = 30
AMMO_PACK_RESTORE = 5

DIRECTIONS = {
    "up":    (-1,  0),
    "down":  ( 1,  0),
    "left":  ( 0, -1),
    "right": ( 0,  1),
}

DEFAULT_MAP = [
    "###############",
    "#.....#.#.....#",
    "#.###.....###.#",
    "#.#..H...H..#.#",
    "#.#.###.###.#.#",
    "#...A.....A...#",
    "#.###.#.#.###.#",
    "#.....A.A.....#",
    "#.###.#.#.###.#",
    "#...A.....A...#",
    "#.#.###.###.#.#",
    "#.#..H...H..#.#",
    "#.###.....###.#",
    "#.....#.#.....#",
    "###############",
]

class Tank:
    def __init__(self, tank_id, row, col):
        self.tank_id = tank_id   # 0 or 1
        self.hp = STARTING_HP
        self.ammo = STARTING_AMMO
        self.row = row
        self.col = col
        self.alive = True
        self.last_shot_hit = False
        self.pre_shoot = False

    def copy(self):
        t = Tank(self.tank_id, self.row, self.col)
        t.hp = self.hp
        t.ammo = self.ammo
        t.alive = self.alive
        t.last_shot_hit = self.last_shot_hit
        t.pre_shoot=self.pre_shoot
        return t

class GameState:

    def __init__(self, grid, tanks, turn=0, powerups=None):
        """
        grid     : list of lists of chars (mutable copy)
        tanks    : list of two Tank objects [tank0, tank1]
        turn     : current turn number (starts at 0)
        powerups : dict {(r,c): 'H'|'A'} of remaining pickups
        """
        self.grid = grid          # base terrain (walls only after init)
        self.tanks = tanks
        self.turn = turn
        # powerups are tracked separately so they can be removed
        self.powerups = powerups if powerups is not None else {}

    def copy(self):
        new_grid = [row[:] for row in self.grid]
        new_tanks = [t.copy() for t in self.tanks]
        new_pu = dict(self.powerups)
        return GameState(new_grid, new_tanks, self.turn, new_pu)

    def is_wall(self, r, c):
        return self.grid[r][c] == '#'

    def in_bounds(self, r, c):
        return 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS

    def get_snapshot(self, for_tank_id):
        """
        Returns a plain dict representing the full game state,
        passed to bots each turn.
        """

        me = self.tanks[for_tank_id] #0 and 1 
        opp = self.tanks[1 - for_tank_id] #1 and 0
        return {
            "my_id": for_tank_id,
            "turn": self.turn,
            "my_hp": me.hp,
            "my_ammo": me.ammo,
            "my_pos": (me.row, me.col),
            "opp_hp": opp.hp,
            "opp_ammo": opp.ammo,
            "opp_pos": (opp.row, opp.col),
            "opp_alive": opp.alive,
            "grid": [row[:] for row in self.grid],   # walls only
            "powerups": dict(self.powerups),          # {(r,c): 'H'|'A'}
            "max_turns": MAX_TURNS,
            "last_shot_hit": me.last_shot_hit,
            "pre_shoot" : me.pre_shoot
        }

    def render(self):
        """Return a human-readable ASCII board string."""
        display = [list(row) for row in self.grid]
        # Place powerups
        for (r, c), kind in self.powerups.items():
            display[r][c] = kind
        # Place tanks (T0, T1; or X if dead)
        for t in self.tanks:
            sym = str(t.tank_id) if t.alive else 'X'
            display[t.row][t.col] = sym
        lines = ["  " + "".join(str(i % 10) for i in range(GRID_COLS))]
        for i, row in enumerate(display):
            lines.append(f"{i:2d} {''.join(row)}")
        return "\n".join(lines)


def parse_map(map_lines):
    """
    Parse a list of strings into:
      - grid: list of lists (walls=# or .  only; powerups extracted)
      - powerups: {(r,c): 'H'|'A'}
      - spawn0, spawn1: (row,col) tuples (if P0/P1 markers found, else defaults)
    Returns (grid, powerups, spawn0, spawn1)
    """
    grid = []
    powerups = {}
    spawn0 = None
    spawn1 = None

    for r, line in enumerate(map_lines):
        row = []
        for c, ch in enumerate(line):
            if ch == '#':
                row.append('#')
            elif ch == 'H':
                row.append('.')
                powerups[(r, c)] = 'H'
            elif ch == 'A':
                row.append('.')
                powerups[(r, c)] = 'A'
            elif ch == '0':
                row.append('.')
                spawn0 = (r, c)
            elif ch == '1':
                row.append('.')
                spawn1 = (r, c)
            else:
                row.append('.')
        grid.append(row)

    # Default spawns: top-left interior and bottom-right interior
    if spawn0 is None:
        spawn0 = (1, 1)
    if spawn1 is None:
        spawn1 = (GRID_ROWS - 2, GRID_COLS - 2)

    return grid, powerups, spawn0, spawn1


'''def initial_facing(pos, grid_rows=GRID_ROWS, grid_cols=GRID_COLS):
    """Return direction facing toward centre from spawn."""
    cr, cc = grid_rows // 2, grid_cols // 2
    r, c = pos
    dr = cr - r
    dc = cc - c
    if abs(dr) >= abs(dc):
        return "down" if dr > 0 else "up"
    return "right" if dc > 0 else "left"'''


def init_game(map_lines=None):
    """Create and return a fresh GameState."""
    if map_lines is None:
        map_lines = DEFAULT_MAP
    grid, powerups, spawn0, spawn1 = parse_map(map_lines)
    tank0 = Tank(0, spawn0[0], spawn0[1])
    tank1 = Tank(1, spawn1[0], spawn1[1])
    return GameState(grid, [tank0, tank1], turn=0, powerups=powerups)


# ---------------------------------------------------------------------------
# Action validation
# ---------------------------------------------------------------------------

def _move_dest(tank, direction):
    dr, dc = DIRECTIONS[direction]
    return tank.row + dr, tank.col + dc


def is_valid_action(state, tank_id, action):
    """
    Returns True if action is legal for tank_id given current state.
    action is a dict: {"type": "move"|"shoot"|"pass", "direction": ...}
    """
    tank = state.tanks[tank_id]
    if not tank.alive:
        return False

    atype = action.get("type", "pass")

    if atype == "pass":
        return True

    if atype == "move":
        direction = action.get("direction")
        if direction not in DIRECTIONS:
            return False
        nr, nc = _move_dest(tank, direction)
        if not state.in_bounds(nr, nc):
            return False
        if state.is_wall(nr, nc):
            return False
        # Can't move into the other tank's current position
        opp = state.tanks[1 - tank_id]
        if opp.alive and opp.row == nr and opp.col == nc:
            return False
        return True

    if atype == "shoot":
        direction = action.get("direction")
        if direction not in DIRECTIONS:
            return False
        if tank.ammo <= 0:
            return False
        return True

    return False  # unknown action type


# ---------------------------------------------------------------------------
# State advancement
# ---------------------------------------------------------------------------

def _trace_bullet(state, origin_r, origin_c, direction, exclude_pos=None):
    """
    Trace a bullet from (origin_r, origin_c) in direction.
    exclude_pos: a position to treat as empty (the shooting tank itself).
    Returns ('wall', r, c) if it hits a wall, or ('tank', tank_id) if it hits a tank.
    The bullet does NOT pass through the shooter's current tile (origin is already
    the cell after the shooter).
    """
    dr, dc = DIRECTIONS[direction]
    r, c = origin_r + dr, origin_c + dc

    while state.in_bounds(r, c):
        if state.grid[r][c] == '#':
            return ('wall', r, c)
        for t in state.tanks:
            if t.alive and t.row == r and t.col == c:
                return ('tank', t.tank_id)
        r += dr
        c += dc

    return ('oob', r - dr, c - dc) #bounds exceeded therefore subtract to go to end pos


def apply_actions(state, action0, action1):
    """
    Given two actions (one per tank), compute and return the next GameState.
    Invalid actions are silently treated as PASS.
    """
    state = state.copy()
    actions = [action0, action1]

    # Normalise / validate
    cleaned = []
    for tid, act in enumerate(actions):
        if not isinstance(act, dict): #empty dictionary thoguh not possible here
            act = {"type": "pass"}
        if not is_valid_action(state, tid, act):
            act = {"type": "pass"}
        cleaned.append(act)

    # movement
    new_posi = [None, None]
    for tid, act in enumerate(cleaned):
        tank = state.tanks[tid]
        if not tank.alive:
            continue
        if act["type"] == "move":
            nr, nc = _move_dest(tank, act["direction"])
            new_posi[tid] = (nr, nc)
        else:
            new_posi[tid] = (tank.row, tank.col)

    # If both tanks try to move into same place, cancel both moves. Resolution adopted by me as nothing given.
    tank0, tank1 = state.tanks
    if (new_posi[0] == new_posi[1]):
        new_posi[0] = (tank0.row, tank0.col)
        new_posi[1] = (tank1.row, tank1.col) #Why we made copy of position

    '''# Also handle swapping positions (pass-through): if they'd swap, cancel
    if (t0.alive and t1.alive and
            new_posi[0] == (t1.row, t1.col) and
            new_posi[1] == (t0.row, t0.col)):
        new_posi[0] = (t0.row, t0.col)
        new_posi[1] = (t1.row, t1.col)'''

    # Apply movements
    for tid in range(2):
        tank = state.tanks[tid]
        if tank.alive and new_posi[tid] is not None:
            tank.row, tank.col = new_posi[tid]

    # Powerup (after movement, before shooting)
    for tank in state.tanks:
        pos = (tank.row, tank.col)
        if pos in state.powerups:
            kind = state.powerups.pop(pos)
            if kind == 'H':
                tank.hp = min(tank.hp + HEALTH_PACK_RESTORE, 100)
            elif kind == 'A':
                tank.ammo += AMMO_PACK_RESTORE

    # Assumption that first any of those tank will move and then we check bullets for new position
    # --- Phase 3: Shooting (both bullets resolved simultaneously) ---
    # First, collect shoot actions from both tanks (before consuming ammo)
    bullets = []
    for tid, act in enumerate(cleaned):
        tank = state.tanks[tid]
        if act["type"] == "shoot":
            direction = act["direction"]
            tank.ammo -= 1
            bullets.append((tid, tank.row, tank.col, direction))

    # Resolve bullets (using positions AFTER movement)
    damage = [0, 0]  # damage[tid] = damage dealt TO tank tid
    for (shooter_id, sr, sc, direction) in bullets:
        result = _trace_bullet(state, sr, sc, direction)
        if result[0] == 'tank':
            victim_id = result[1]
            damage[victim_id] += BULLET_DAMAGE
    
    state.tanks[0].last_shot_hit = False
    state.tanks[1].last_shot_hit = False

    for tid in range(2):
        if damage[tid] > 0:
            state.tanks[tid].hp -= damage[tid]
            state.tanks[tid].last_shot_hit = True
            if state.tanks[tid].hp <= 0:
                state.tanks[tid].alive = False

    state.turn += 1
    return state


# ---------------------------------------------------------------------------
# Game runner
# ---------------------------------------------------------------------------

def run_match(bot0_fn, bot1_fn, map_lines=None, verbose=False, print_board=False):
    """

    Bot :
        action = bot_fn(snapshot_dict) -> dict
        e.g. {"type": "move", "direction": "up"}
             {"type": "shoot", "direction": "right"}
             {"type": "pass"}

    Returns:
        result dict:
          {
            "winner": 0 | 1 | None,   # None = draw
            "reason": str,
            "turns": int,
            "final_hp": [hp0, hp1],
          }
    """
    state = init_game(map_lines)

    if verbose:
        print(f"=== SER PROTOCOL: MATCH START ===")
        if print_board:
            print(state.render())
            print()

    while state.turn < MAX_TURNS:
        t0, t1 = state.tanks

        if not t0.alive or not t1.alive:
            break

        snap0 = state.get_snapshot(0)
        snap1 = state.get_snapshot(1)

        try:
            action0 = bot0_fn(snap0)
            state.tanks[0].pre_shoot=action0.get("pre_shoot", False)
        except Exception:
            action0 = {"type": "pass"}

        try:
            action1 = bot1_fn(snap1)
        except Exception:
            action1 = {"type": "pass"}

        if verbose:
            print(f"Turn {state.turn}: Tank0 -> {action0} | Tank1 -> {action1}")

        state = apply_actions(state, action0, action1)

        if verbose and print_board:
            print(state.render())
            print()

    # Determine result
    t0, t1 = state.tanks
    turns = state.turn

    if not t0.alive and not t1.alive:
        result = {"winner": None, "reason": "Both tanks destroyed simultaneously",
                  "turns": turns, "final_hp": [t0.hp, t1.hp]}
    elif not t1.alive:
        result = {"winner": 0, "reason": "Tank 1 destroyed",
                  "turns": turns, "final_hp": [t0.hp, t1.hp]}
    elif not t0.alive:
        result = {"winner": 1, "reason": "Tank 0 destroyed",
                  "turns": turns, "final_hp": [t0.hp, t1.hp]}
    else:
        # Turn limit reached
        if t0.hp > t1.hp:
            result = {"winner": 0, "reason": "Turn limit - HP advantage",
                      "turns": turns, "final_hp": [t0.hp, t1.hp]}
        elif t1.hp > t0.hp:
            result = {"winner": 1, "reason": "Turn limit - HP advantage",
                      "turns": turns, "final_hp": [t0.hp, t1.hp]}
        else:
            result = {"winner": None, "reason": "Turn limit - HP tied (draw)",
                      "turns": turns, "final_hp": [t0.hp, t1.hp]}

    if verbose:
        print(f"\n=== MATCH OVER ===")
        print(f"Winner : Tank {result['winner']} | Reason: {result['reason']}")
        print(f"Turns  : {result['turns']}")
        print(f"HP     : Tank0={result['final_hp'][0]}  Tank1={result['final_hp'][1]}")

    return result


def print_board(state):
    print(state.render())
