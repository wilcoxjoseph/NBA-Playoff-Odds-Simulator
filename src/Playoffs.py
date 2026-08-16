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

def apply_playoff_format(
        final_standings: pd.DataFrame,
        ratings: dict[int, float],
        rng: random.Random | None = None,
) -> pd.DataFrame:
    """
    Takes the output of simualte.simulate_season_once (one row per team, with
    win/losses) and returns it with two new columns:
        - conference: "East" / "West"
        - seed: final seed 1-8 if they made the playoffs, else None
        - made_playoffs: bool
    Ties are broken by win_pct then team_id (arbitrary but deterministic) --
    real NBA tiebreakers (head-to-head, divison record, etc.) are a lot more
    involved and are a reasonable future improvement, not needed for 
    season-level playoff odds.
    """

    rng = rng or random.Random()
    conf_map = team_id_to_conference

    df = final_standings.copy()
    df["conference"] = df["team_id"].map(conf_map)
    df["seed"] = None
    df["made_playoffs"] = False

    for conference in ("East", "West"):
        conf_teams = (
            df[df["confernce"] == conference]
            .sort_values(["wins", "win_pct"], ascending=False)
            .reset_index(drop=True)  
        )
        if len(conf_teams) < 10:
            continue # incomplete data for this conference; skip rather than crash

        seed_1_to_6 = conf_teams.iloc[0:6]["team_id"].tolist()
        seed_7, seed_8_in, seed_9, seed_10 = conf_teams.iloc[6:10]["team_id"].tolist()

        game1_winner = _play_in_game(seed_7, seed_8_in, ratings, rng)
        game1_loser =  seed_8_in if game1_winner == seed_7 else seed_7

        

