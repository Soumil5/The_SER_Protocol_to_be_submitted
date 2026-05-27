"""
main.py - Run sample matches between bots and print outcomes.
"""

from engine import run_match, init_game, print_board
from my_bot import my_bot

# ---- Opponent bots for testing -----------------------------------------------

def random_bot(snapshot):
    """Picks a random valid-looking action."""
    import random
    my_pos = tuple(snapshot["my_pos"])
    grid   = snapshot["grid"]
    powerups = {tuple(k): v for k, v in snapshot["powerups"].items()}
    dirs   = ["up", "down", "left", "right"]
    random.shuffle(dirs)
    result = random.choice([1, 2])
    if result==1:
        for d in dirs:
            dr, dc = {"up": (-1,0),"down":(1,0),"left":(0,-1),"right":(0,1)}[d]
            nr, nc = my_pos[0]+dr, my_pos[1]+dc
            if (0 <= nr < 15 and 0 <= nc < 15 and grid[nr][nc] != '#'):
                opp = tuple(snapshot["opp_pos"])
                if (nr, nc) != opp:
                    return {"type": "move", "direction": d}
        if snapshot["my_ammo"] > 0:
            return {"type": "shoot", "direction": random.choice(dirs)}
    else:
        if snapshot["my_ammo"] > 0:
            return {"type": "shoot", "direction": random.choice(dirs)}

        for d in dirs:
            dr, dc = {"up": (-1,0),"down":(1,0),"left":(0,-1),"right":(0,1)}[d]
            nr, nc = my_pos[0]+dr, my_pos[1]+dc
            if (0 <= nr < 15 and 0 <= nc < 15 and grid[nr][nc] != '#'):
                opp = tuple(snapshot["opp_pos"])
                if (nr, nc) != opp:
                    return {"type": "move", "direction": d}

    return {"type": "pass"}


def greedy_bot(snapshot):
    """
    Greedy bot: always shoot if in LOS, otherwise step directly toward enemy
    using manhattan distance (ignores walls, so it can get stuck).
    """
    my_pos = tuple(snapshot["my_pos"])
    opp_pos = tuple(snapshot["opp_pos"])
    grid = snapshot["grid"]
    ammo = snapshot["my_ammo"]

    # Check LOS
    dirs = {"up": (-1,0),"down":(1,0),"left":(0,-1),"right":(0,1)}
    if ammo > 0:
        for dname, (dr, dc) in dirs.items():
            r, c = my_pos[0]+dr, my_pos[1]+dc
            while 0<=r<15 and 0<=c<15:
                if grid[r][c] == '#':
                    break
                if (r,c) == opp_pos:
                    return {"type": "shoot", "direction": dname}
                r+=dr; c+=dc

    # Step toward enemy (simple, ignores walls)
    mr, mc = my_pos
    or_, oc = opp_pos
    possible=[]
    if abs(mr - or_) >= abs(mc - oc):
        if or_ > mr:
            possible.appned("down") 
        elif or_ < mr:
            possible.append("up")
    else:
        if oc > mc:
            possible.appned("right") 
        elif oc < mc:
            possible.append("up")

    for i in possible:
        dr2, dc2 = dirs[i]
        nr, nc = mr+dr2, mc+dc2
        if 0<=nr<15 and 0<=nc<15 and grid[nr][nc] != '#' and (nr,nc) != opp_pos:
            return {"type": "move", "direction": i}

    # Try other directions
    for dname, (dr, dc) in dirs.items():
        if dname in possible:
            continue
        nr, nc = mr+dr, mc+dc
        if 0<=nr<15 and 0<=nc<15 and grid[nr][nc] != '#' and (nr,nc) != opp_pos:
            return {"type": "move", "direction": dname}

    return {"type": "pass"}


def run_tournament():
    opponents = [
        ("Random Bot",  random_bot),
        ("Greedy Bot",  greedy_bot),
    ]

    print("=" * 60)
    print("   SER PROTOCOL BATTLE SIMULATOR — APEX DYNAMICS AI")
    print("=" * 60)
    print("\n\n")
    print("--- Showing starting board ---")
    state = init_game()
    print_board(state)


    for name, opp in opponents:
        print(f"\n--- my_bot(Tank0)  vs  {name} (Tank1)---")
        result = run_match(my_bot, opp, verbose=True)
        w = result["winner"]
        winner_label = "my_bot" if w == 0 else (name if w == 1 else "DRAW")
        print(f"→ Winner: {winner_label}")


if __name__ == "__main__":
    run_tournament()
