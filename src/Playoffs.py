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

from __future__ import annotations

import random

import pandas as pd

from conferences import team_id_to_conference
from elo import HOME_ADVANTAGE, expected_win_prob

def _play_in_game(team_a: int, team_b: int, ratings: dict[int, float], rng: random.Random) -> int:
    """team_a is the home team (higher seed). Returns the winner's team_id."""
    rating_a = ratings.get(team_a, 1500.0) + HOME_ADVANTAGE
    rating_b = ratings.get(team_b, 1500.0)
    return team_a if rng.random() < expected_win_prob(rating_a, rating_b) else team_b

