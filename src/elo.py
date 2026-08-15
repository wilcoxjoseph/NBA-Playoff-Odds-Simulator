"""
Elo rating model for NBA teams.

Builds a rating for every team by replaying completed games from the cached
schedule in chronological order. These ratings feed the Monte Carlo
simulation's win probability calculations.
"""

from __future__ import annotations
 
import math
 
import pandas as pd
 
# ---- COLUMN MAP: adjust these if your pulled schedule uses different names ----
COL_GAME_DATE = "gameDateEst"
COL_STATUS = "gameStatus"        # 1 = not started, 2 = in progress, 3 = final
COL_HOME_TEAM_ID = "homeTeam_teamId"
COL_AWAY_TEAM_ID = "awayTeam_teamId"
COL_HOME_SCORE = "homeTeam_score"
COL_AWAY_SCORE = "awayTeam_score"
STATUS_FINAL = 3
# ---------------------------------------------------------------------------
 
DEFAULT_RATING = 1500.0
K_FACTOR = 20.0          # how much one game moves a rating
HOME_ADVANTAGE = 75.0    # Elo points added to home team's rating pre-game
 
 
def expected_win_prob(rating_a: float, rating_b: float) -> float:
    """Probability that team A beats team B, given their Elo ratings."""
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))
 
 
def completed_games(schedule: pd.DataFrame) -> pd.DataFrame:
    """
    Rows where the game is final, sorted chronologically. gameStatus can come
    back from nba_api as a string rather than an int, so we coerce before
    comparing — otherwise the filter silently matches nothing.
    """
    status = pd.to_numeric(schedule[COL_STATUS], errors="coerce")
    completed = schedule[status == STATUS_FINAL].copy()
    return completed.sort_values(COL_GAME_DATE)
 
 
def build_ratings(schedule: pd.DataFrame) -> dict[int, float]:
    """
    Replay all completed games in chronological order, updating Elo ratings
    after each one. Returns {team_id: rating}.
    """
    completed = completed_games(schedule)
 
    ratings: dict[int, float] = {}
 
    def get_rating(team_id: int) -> float:
        return ratings.get(team_id, DEFAULT_RATING)
 
    for _, game in completed.iterrows():
        home_id = game[COL_HOME_TEAM_ID]
        away_id = game[COL_AWAY_TEAM_ID]
        home_score = game[COL_HOME_SCORE]
        away_score = game[COL_AWAY_SCORE]
 
        home_rating = get_rating(home_id) + HOME_ADVANTAGE
        away_rating = get_rating(away_id)
 
        expected_home = expected_win_prob(home_rating, away_rating)
        actual_home = 1.0 if home_score > away_score else 0.0
 
        # Margin-of-victory multiplier (a la 538) so blowouts move ratings more
        margin = abs(home_score - away_score)
        mov_multiplier = math.log(margin + 1) * (2.2 / ((abs(get_rating(home_id) - get_rating(away_id)) * 0.001) + 2.2))
 
        delta = K_FACTOR * mov_multiplier * (actual_home - expected_home)
 
        ratings[home_id] = get_rating(home_id) + delta
        ratings[away_id] = get_rating(away_id) - delta
 
    return ratings
 
 
def backtest(schedule: pd.DataFrame, ratings_over_time: bool = False) -> float:
    """
    Sanity check: replay the season game-by-game, predicting each game with
    the ratings as they stood *before* that game, and report accuracy
    (how often the favored team actually won). A well-behaved Elo model on
    an NBA season usually lands around 65-70% — if you're way off that,
    double-check the column map and the home advantage constant.
    """
    completed = completed_games(schedule)
 
    ratings: dict[int, float] = {}
    correct = 0
    total = 0
 
    def get_rating(team_id: int) -> float:
        return ratings.get(team_id, DEFAULT_RATING)
 
    for _, game in completed.iterrows():
        home_id = game[COL_HOME_TEAM_ID]
        away_id = game[COL_AWAY_TEAM_ID]
        home_score = game[COL_HOME_SCORE]
        away_score = game[COL_AWAY_SCORE]
 
        home_rating = get_rating(home_id) + HOME_ADVANTAGE
        away_rating = get_rating(away_id)
        predicted_home_win = home_rating > away_rating
        actual_home_win = home_score > away_score
 
        if predicted_home_win == actual_home_win:
            correct += 1
        total += 1
 
        expected_home = expected_win_prob(home_rating, away_rating)
        actual_home = 1.0 if actual_home_win else 0.0
        delta = K_FACTOR * (actual_home - expected_home)
        ratings[home_id] = get_rating(home_id) + delta
        ratings[away_id] = get_rating(away_id) - delta
 
    accuracy = correct / total if total else 0.0
    print(f"Backtest accuracy: {accuracy:.1%} over {total} completed games")
    return accuracy
 
 
if __name__ == "__main__":
    from data_pipeline import load_cached
 
    schedule = load_cached("schedule")
    if schedule is None:
        print("No cached schedule found — run `python src/data_pipeline.py` first.")
    else:
        ratings = build_ratings(schedule)
        ranked = sorted(ratings.items(), key=lambda kv: kv[1], reverse=True)
        print("Current Elo ratings:")
        for team_id, rating in ranked:
            print(f"  {team_id}: {rating:.0f}")
        backtest(schedule)