"""
my_bot.py - Apex Dynamics Combat AI
Strategy: Tactical Opportunist with Resource Awareness

Decision priority (each turn):
  1. Shoot if enemy is in line of sight and we have ammo
  2. Seek health pack if HP is critical
  3. Seek ammo pack if ammo is very low
  4. Reposition to get line-of-sight on enemy
  5. Advance toward enemy if nothing else
"""

from collections import deque

# ---- Utilities ----------------------------------------------------------------

def _directions():
    return {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}

def _in_bounds(r, c, rows=15, cols=15):
    return 0 <= r < rows and 0 <= c < cols

def _is_passable(grid, powerups, r, c, opp_pos=None):
    """True if the tile can be walked on."""
    if not _in_bounds(r, c):
        return 0
    if grid[r][c] == '#':
        return 0
    if opp_pos and (r, c) == opp_pos:
        return 2
    return 1

def _bfs(grid, powerups, start, goal, opp_pos):
    """
    BFS from start to goal. Returns first step direction string, or None.
    Avoids walls and opponent's current position.
    """
    if start == goal:
        return "pass"
    visited = {start}
    queue = deque()
    # (position, first_step_direction)
    dirs = _directions()
    for dname, (dr, dc) in dirs.items():
        nr, nc = start[0] + dr, start[1] + dc
        if _is_passable(grid, powerups, nr, nc, opp_pos) != 0:
            queue.append(((nr, nc), dname))
            visited.add((nr, nc))
    while queue:
        (r, c), first_step = queue.popleft()
        if (r, c) == goal:
            return first_step
        for dname, (dr, dc) in dirs.items():
            nr, nc = r + dr, c + dc
            if ((nr, nc) not in visited) and (_is_passable(grid, powerups, nr, nc, opp_pos)!=0):
                visited.add((nr, nc))
                queue.append(((nr, nc), first_step))
    return None  # unreachable

def _has_line_of_sight(grid, my_pos, opp_pos):
    """
    Returns direction string if enemy is in a clear cardinal line, else None.
    Bullets travel in a straight line and stop at walls.
    """
    mr, mc = my_pos
    or_, oc = opp_pos
    dirs = _directions()

    for dname, (dr, dc) in dirs.items():
        r, c = mr + dr, mc + dc
        while _in_bounds(r, c):
            if grid[r][c] == '#':
                break
            if (r, c) == (or_, oc):
                return dname
            r += dr
            c += dc
    return None

def _closest_item(grid, powerups, my_pos, opp_pos, item_type, restricted_row=None, restricted_col=None, flag =0):
    """
    BFS to find the nearest powerup of item_type ('H' or 'A').
    Returns (goal_pos, first_step_dir) or (None, None).
    """
    candidates = [(pos, kind) for pos, kind in powerups.items() if kind == item_type]
    if not candidates:
        return None, None

    # BFS from my_pos; return the closest reachable item
    visited = {my_pos}
    queue = deque()
    dirs = _directions()
    for dname, (dr, dc) in dirs.items():
        nr, nc = my_pos[0] + dr, my_pos[1] + dc
        if (nr==restricted_row) or (nc==restricted_col):
            print(dname)
            flag+=1
            continue
        if _is_passable(grid, powerups, nr, nc, opp_pos):
            queue.append(((nr, nc), dname))
            visited.add((nr, nc))
    # Also check if already on one (shouldn't happen but safe)
    if my_pos in powerups and powerups[my_pos] == item_type:
        return my_pos, "pass", flag

    while queue:
        (r, c), first_step = queue.popleft()
        if (r, c) in powerups and powerups[(r, c)] == item_type:
            return (r, c), first_step, flag
        for dname, (dr, dc) in dirs.items():
            nr, nc = r + dr, c + dc
            if (nr, nc) not in visited and _is_passable(grid, powerups, nr, nc, opp_pos):
                visited.add((nr, nc))
                queue.append(((nr, nc), first_step))
    return None, None, flag


def _step_toward(grid, powerups, my_pos, opp_pos):
    """Simple step toward opponent via BFS."""
    return _bfs(grid, powerups, my_pos, opp_pos, opp_pos)

# ---- Main bot function -------------------------------------------------------

def my_bot(snapshot):
    """
    Tactical Opportunist Bot.
    Returns one of:
      {"type": "shoot", "direction": "..."}
      {"type": "move",  "direction": "..."}
      {"type": "pass"}
    """
    my_pos   = tuple(snapshot["my_pos"])
    opp_pos  = tuple(snapshot["opp_pos"])
    my_hp    = snapshot["my_hp"]
    my_ammo  = snapshot["my_ammo"]
    opp_hp   = snapshot["opp_hp"]
    opp_alive = snapshot["opp_alive"]
    grid     = snapshot["grid"]
    powerups = {tuple(k): v for k, v in snapshot["powerups"].items()}
    turn     = snapshot["turn"]
    max_turns = snapshot["max_turns"]
    last_shot_hit = snapshot["last_shot_hit"]
    pre_shoot=snapshot["pre_shoot"]

    #print(my_pos, opp_pos, my_hp, my_ammo, opp_hp, opp_alive, grid, powerups, turn, max_turns)

    # 1. PRE-SHOOT : Predicts that enemy might come into LOS in this turn and hence pre-shoots
    if abs(opp_pos[0]-my_pos[0])==1 or abs(opp_pos[1]-my_pos[1])==1:
        pre_shoot=True
    else:
        pre_shoot=False
    if pre_shoot==True:
        if abs(opp_pos[0]-my_pos[0])==1:
            if opp_pos[1]>my_pos[1]:
                wall=0
                for i in range(my_pos[1], opp_pos[1]+1):
                    if grid[my_pos[0]][i]=='#':
                        wall=1
                        break
                if wall==0:
                    return {"type":"shoot", "direction":"right"}
            elif opp_pos[1]<my_pos[1]:
                wall=0
                for i in range(opp_pos[1], my_pos[1]+1):
                    if grid[my_pos[0]][i]=='#':
                        wall=1
                        break
                if wall==0:
                    return {"type":"shoot", "direction":"left"}
        elif abs(opp_pos[1]-my_pos[1])==1:
            if opp_pos[0]>my_pos[0]:
                wall=0
                for i in range(my_pos[0], opp_pos[0]+1):
                    if grid[i][my_pos[1]]=='#':
                        wall=1
                        break
                if wall==0:
                    return {"type":"shoot", "direction":"down"}
            elif opp_pos[0]<my_pos[0]:
                wall=0
                for i in range(opp_pos[0], my_pos[0]+1):
                    if grid[i][my_pos[1]]=='#':
                        wall=1
                        break
                if wall==0:
                    return {"type":"shoot", "direction":"up"}


    # ------------------------------------------------------------------ #
    # 2. CRITICAL HP: rush nearest health pack
    # ------------------------------------------------------------------ #
    if my_hp <= 30:
        restricted_row=opp_pos[0]
        restricted_col=opp_pos[1]
        _ , step, flag  = _closest_item(grid, powerups, my_pos, opp_pos, 'H', restricted_row, restricted_col) 
        if flag==1:
            pre_shoot=True
        if step and step != "pass":
            return {"type": "move", "direction": step, "pre_shoot": True}
        
    # ------------------------------------------------------------------ #
    # 3. SHOOT if enemy is in line of sight and we have ammo
    # ------------------------------------------------------------------ #
    if my_ammo > 0 and opp_alive:
        los_dir = _has_line_of_sight(grid, my_pos, opp_pos)
        if los_dir:
            return {"type": "shoot", "direction": los_dir}

    # ------------------------------------------------------------------ #
    # 4. LOW AMMO: rush nearest ammo pack
    # ------------------------------------------------------------------ #
    if my_ammo <= 1:
        _, step = _closest_item(grid, powerups, my_pos, opp_pos, 'A')[:2]
        if step and step != "pass":
            return {"type": "move", "direction": step}

    # ------------------------------------------------------------------ #
    # 5. Opportunistic pickup: grab H/A if it's on the path or adjacent
    # ------------------------------------------------------------------ #
    # Grab health pack if mildly hurt and one is adjacent
    if my_hp <= 70:
        _, step = _closest_item(grid, powerups, my_pos, opp_pos, 'H')[:2]
        if step and step != "pass":
            # Only divert if it's close (within 3 BFS steps)
            goal, _ = _closest_item(grid, powerups, my_pos, opp_pos, 'H')[:2]
            if goal:
                dist = abs(goal[0] - my_pos[0]) + abs(goal[1] - my_pos[1])
                if dist <= 3:
                    return {"type": "move", "direction": step}


    # ------------------------------------------------------------------ #
    # 6. Advance toward enemy (chase / close distance)
    # ------------------------------------------------------------------ #
    if opp_alive:
        step = _step_toward(grid, powerups, my_pos, opp_pos)
        if step and step != "pass":
            return {"type": "move", "direction": step}

    # ------------------------------------------------------------------ #
    # 7. Nothing useful to do - pass
    # ------------------------------------------------------------------ #
    return {"type": "pass"}
