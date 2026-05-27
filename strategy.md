# Strategy Document

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
] This default map I have used in my engine also for every match

## Core Idea

Every turn, `my_bot` runs through a priority ladder and executes the **first applicable action**:

1. Pre-Shoot
    `Whenever my bot finds that difference between the rows (or cols) is exactly one, it pre-shoots the opponent if no wall is there in between. This is an attcking move from my bot which is very helpful in winning. This is the first priority as it can never happen that this can kead to a loss(though its possible that it might not even result in damage on other opponent if opponent doesn't come after our bot like in random)`
2. **Rush a health pack** if HP ≤ 30 (critical)
    `This is very important as if we had shot the very moment enemy was in LOS then it would have surely resulted in a draw with every other greedy bot or smart bot. Both bots would have fired shots till they both had drained their hp's to 0.`
    `This tries to dodge my bot the last shot and start running towards the health pack. After` `this there is a high chance that the greedy bot/ opponent smart bot might start chasing him and eventually my bot gets in LOS of greedy bot when he has chnaged dir of movement for health_pack, again resulting in a draw. Therefore, my bot also tries to pre-shoot as in 1st priority which saves it from this.`
    
    My bot would never go for a health pack if it is possible that it might get shot on the same turn it makes movement. Example: In reference to the default map I have used, if my bot is at (3,7) with HP=25 and opponent at (3,8) with HP=100. The health pack is present at (3,5). According to the preiority order I have ised, my bot should go LEFT in search of the health pack present at (3,5) but it doesn't as it knows that it would get shot the very turn itself if it moves LEFT as enemy has LOS. Hence, it rather tries to dodge the bullet or in other words change its row to (2,.) or (4,.).

    
3. **Shoot if the enemy is in line-of-sight** and ammo > 0  
    `Should have been the natural instinct but have shifted it to 3rd priority to ensure maximum chances of win`
4. **Rush an ammo pack** if ammo ≤ 1  
5. **Grab a nearby health pack opportunistically** if HP ≤ 70 and one is within 3 tiles  
6. **BFS-chase the enemy** to close distance  
    ` We have used BFS and not manhattan distance as BFS takes into account the walls and opponent and then finds the shortest distance while manhattan distance doesn't do so`
7. **Pass** as a last resort  

Hence, my bot focuses on firstly attack if it is guaranteed that it will not have any loss except ammo. Then it goes for ultimate defense if HP<=30 (critical HP). Then it looks to trade off HP in direct LOS combat. (Natural instinct shoot if enemy in lOS). Then it prefers other options which are mere strategic options with future benefits.
---

## Strengths of my bot

**ALL THE COORDINATES USED ARE WITH RESPECT TO THE DEAFULT MAP I HAVE USED IN MY ENGINE (indexing starting from 0)**

## A - Obvious 
My tank always tries to shoot, run for health pack and find ammo when required but these are the basics and not worth mentioning as any average bot can also do so.

### B — Corridor ambush at (7, 1) vs (7, 9)

Both tanks are near opposite sides of the open centre corridor (row 7 is passable from col 1 to col 13) with HP=25 (suppose). `my_bot` has `_has_line_of_sight` and could have shooted immediately but it doesn't as it would have forced game into a draw. It rather goes in search of HP and pre-shoots whenever there is an opportunity.

### C — Chance of infinite repition of moves resulting in a draw

Suppose `my_bot` is at (2, 5) and opponent is at (3, 9), not yet in line-of-sight. If my bot didn't have the pre-shoot intelligence, it would have surely gone into repositioning itsself for taking shot in next turn. This would have meant MOVING DOWN for my bot. While the opposition (greedy or semi-smart bot) would have also done same (MOVE UP HERE) to get LOS for next turn. The new position of my bot would have been (3,5) and enemy (2,9). Again the similar situation in which both bots will try to reposition again. This wouls have let in into an infinte cycles (capped at 150) resulting in a draw finally.

But my bot counters this using its brain of pre-shoot. It wouldn't go down in first step itself for LOS but would pre-shoot already predicting that enenmy will itself come into its LOS, hence dealing a damage of 25 with no loss of itself(except ammo).

---

## Known Weakness

**`my_bot` can be out-manoeuvred into a draw (NOT LOSS) in one case.**
    Suppose my bot is at (3,7) and enemy at (2,8), both with HP=25. There is a health pack at (3,5) according to the default map of mine. Then my bot would pre-fire in up direcction but enemy(greedy) might go DOWN instead of coming LEFT to have LOS. This would result in wastage of that move and shot. And now the new positions of my bot and enemy are respectively (3,7) and (3,8). Now there is LOS but according to my bot's strategy, it should run fot the health pack that is towards left or towards (3,5). In this way it could have got shot by enemy as it would have shooted left due to LOS it has in the 4th (3,.) row. BUT my bot is intelligent enough to not go for health pack and get shot in the same turn. Rather it will have only one option left that is to either dodge the 4th row or in worst case shoot directly towards RIGHT as enemy in LOS. Same would be the move of enemy resulting in an ambush in 4th row and hence a draw.

---

*Word count: ~530*
