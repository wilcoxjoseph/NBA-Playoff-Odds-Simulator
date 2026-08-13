"""
Elo rating model for NBA teams.

Builds a rating for every team by replaying completed games from the cached
schedule in chronological order. These ratings feed the Monte Carlo
simulation's win probability calculations.
"""

from __future__ import annotations

import math

import pandas as pd

# COLUMN MAP: adjust these if your pulled schedule uses different names
COL_GAME_DATE = "gameDateEst"
COL_STATUS = "gameStatus"   # 1 = not started, 2 = in progress, 3 = final
COL_HOME_TEAM_ID = "homeTeam_teamId"
COL_AWAY_TEAM_ID = "awayTeam_teamId"
COL_HOME_TEAM_SCORE = "homeTeam_score"
COL_AWAY_TEAM_SCORE = "awayTeam_score"
STATUS_FINAL = "3"

DEFAULT_RATING = 1500.0
K_FACTOR = 20.0       # How much one game moves a rating
HOME_ADVANTAGE = 75.0 # Elo points added to home team's rating pre-game

def expected_win_prob(rating_a: float, rating_b: float) -> float:
    """ Probability that team A beats team B, given their Elo ratings. """
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))

def build_ratings(schedule: pd.DataFrame) -> dict[int, float]:
    """ 
    Replay all completed games in chronological order, updating Elo ratings
    after each game. Returns {team_id: rating}
    """
    completed = schedule[schedule[COL_STATUS] == STATUS_FINAL].copy()
    completed = completed.sort_values(by=COL_GAME_DATE)

    ratings: dict[int, float] = {}

    def get_rating(team_id: int) -> float:
        return ratings.get(team_id, DEFAULT_RATING)

    for _, game in completed.iterrows():
        home_id = game[COL_HOME_TEAM_ID]
        away_id = game[COL_AWAY_TEAM_ID]
        home_score = game[COL_HOME_TEAM_SCORE]
        away_score = game[COL_AWAY_TEAM_SCORE]

        home_rating = get_rating(home_id) + HOME_ADVANTAGE  
        away_rating = get_rating(away_id)

        expected_home = expected_win_prob(home_rating, away_rating)
        actual_home = 1.0 if home_score > away_score else 0.0

        # Margin-of-victory multiplier so blowouts move ratings more
        margin = abs(home_score - away_score)
        mov_multiplier = math.log(margin + 1) * (2.2 / (abs(get_rating(home_id) - get_rating(away_id)) * 0.001 + 2.2))

        delta = K_FACTOR * mov_multiplier * (actual_home - expected_home)

        ratings[home_id] = get_rating(home_id) + delta
        ratings[away_id] = get_rating(away_id) - delta

    return ratings
