"""
Turns one simulated season's final standings into actual playoffs results:
conference seeding, the play-in tournament (seeds 7-10), and a final
playoffs/out call for every team.

NBA play-in format, per conference:
    Game 1: 7 seed (home) vs 8 seed      -> winner becomes the 7 seed
    Game 2: 9 seed (home) vs 10 seed     -> loser is eliminated
    Game 3: loser of Game 1 (home) vs winner of Game 2 -> winner becomes 8 seed
Seeds 1-6 make the playoffs automatically. Everyone else is out.
"""