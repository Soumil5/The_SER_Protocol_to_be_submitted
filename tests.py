# These testcases only verify the rules applied correctly in engine and don not comment anything about the smart BOT, greedy bot or random bot made
# I have not included the testacse of shooting bullets at same time and both getting damages as that seemed obvious to me;

from engine import (
    init_game, apply_actions, BULLET_DAMAGE, HEALTH_PACK_RESTORE, AMMO_PACK_RESTORE, MAX_TURNS
)


def make_state(map_lines=None, t0_pos=None, t1_pos=None,
               t0_hp=100, t1_hp=100, t0_ammo=10, t1_ammo=10, powerups=None):
    """Create a customisable state for testing."""
    state = init_game(map_lines)
    if t0_pos:
        state.tanks[0].row, state.tanks[0].col = t0_pos
    if t1_pos:
        state.tanks[1].row, state.tanks[1].col = t1_pos
    state.tanks[0].hp = t0_hp
    state.tanks[1].hp = t1_hp
    state.tanks[0].ammo = t0_ammo
    state.tanks[1].ammo = t1_ammo
    if powerups is not None:
        state.powerups = powerups
    return state


def move(d):   return {"type": "move",  "direction": d}
def shoot(d):  return {"type": "shoot", "direction": d}
def pass_():   return {"type": "pass"}


# TEST 1 — Bullet fires the exact turn a tank moves out of its path

# For eg, Tank0 at (7,1) shoots RIGHT. tank1 is at (7,5) and moves UP this turn.
# Now, tank1 is at (6,5).  Bullet should not hit tank1.

def test_bullet_misses_after_dodge():
    state = make_state(t0_pos=(7,1), t1_pos=(7,5), t0_ammo=5, t1_ammo=5)

    initial_hp = state.tanks[1].hp
    next_state = apply_actions(state, shoot("right"), move("up"))
    # Tank1 dodged to (6,5); bullet passed through (7,5) which is now empty
    assert next_state.tanks[1].hp == initial_hp, (
        f"Tank1 should not be hit after dodging; HP={next_state.tanks[1].hp}")
    assert next_state.tanks[1].row == 6, "Tank1 should have moved up"
    print("PASS test_bullet_misses_after_dodge")




# TEST 2 — If two tanks trying to move into the same tile, both are cancelled. (rule assumed)
def test_collision_both_moves_cancelled():
    # Tank0 at (7,6), Tank1 at (7,8); (equidistant from an open centre tile.) Both try to move toward (7,7).
    state = make_state(t0_pos=(7,6), t1_pos=(7,8))
    assert state.grid[7][7] == '.', "Centre tile must be open"

    next_state = apply_actions(state, move("right"), move("left"))

    assert next_state.tanks[0].col == 6, (
        f"Tank0 should stay at col 6, got {next_state.tanks[0].col}")
    assert next_state.tanks[1].col == 8, (
        f"Tank1 should stay at col 8, got {next_state.tanks[1].col}")
    print("PASS test_collision_both_moves_cancelled")


# TEST 3 — Powerup collected the same turn a bullet hits
# Eg- Tank0 : (5,1). Health pack : (5,2). Tank1 : (5,6) (tank1 shoots left).
# Tank0 moves RIGHT, lands on health pack and gains up to 30 HP. 
# Tank1's bullet also travels left and hits Tank0 at (5,2) casuing 25 damage.
# Net: HP = min(100+30, 100) - 25
# Have the made rules victim favouring that prioritise movement first and then anyalses shooting
def test_powerup_and_bullet_same_turn():
    pu = {(5, 2): 'H'}
    state = make_state(t0_pos=(5,1), t1_pos=(5,6), t1_ammo=5, powerups=pu)
    assert state.grid[5][2] == '.', "(5,2) must be open"

    next_state = apply_actions(state, move("right"), shoot("left"))

    assert next_state.tanks[0].row == 5 and next_state.tanks[0].col == 2, \
        "Tank0 should have moved onto health pack tile"
    assert (5, 2) not in next_state.powerups, "Health pack should be consumed"

    expected_hp = min(100 + HEALTH_PACK_RESTORE, 100) - BULLET_DAMAGE 
    assert next_state.tanks[0].hp == expected_hp, (
        f"Expected HP {expected_hp}, got {next_state.tanks[0].hp}")
    print("PASS test_powerup_and_bullet_same_turn")

# TEST 4 — Shooting with 0 ammo ahould be treated as pass. Hence, no HP loss for opponent
def test_shoot_with_zero_ammo_is_pass():
    state = make_state(t0_pos=(7,1), t1_pos=(7,5), t0_ammo=0)

    initial_hp = state.tanks[1].hp
    next_state = apply_actions(state, shoot("right"), pass_())
    assert next_state.tanks[1].hp == initial_hp, (
        f"Tank1 should take no damage; HP={next_state.tanks[1].hp}")
    assert next_state.tanks[0].ammo == 0, "Ammo should remain 0"
    print("PASS test_shoot_with_zero_ammo_is_pass")


# TEST 5 — Tanks try to swap (Tanks try to pass through each other). This should be prevented
def test_tanks_cannot_swap_positions():
    # Tank0 at (7,5), Tank1 at (7,6). Tank0 moves right, Tank1 moves left.
    # They should not swap or rather engine should cancel both.
    state = make_state(t0_pos=(7,5), t1_pos=(7,6))
    next_state = apply_actions(state, move("right"), move("left"))
    assert (next_state.tanks[0].col == 5 and next_state.tanks[1].col == 6), (
        f"Tanks should not swap: T0.col={next_state.tanks[0].col}, "
        f"T1.col={next_state.tanks[1].col}")
    print("PASS test_tanks_cannot_swap_positions")


if __name__ == "__main__":
    test_bullet_misses_after_dodge()
    test_collision_both_moves_cancelled()
    test_powerup_and_bullet_same_turn()
    test_shoot_with_zero_ammo_is_pass()
    test_tanks_cannot_swap_positions()
    print("\n✓ All tests passed.")
