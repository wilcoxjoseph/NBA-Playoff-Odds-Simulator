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
COL_WEEK_NUMBER = "weekNumber"   # kept for reference; not used for filtering (see regular_season_mask)
COL_GAME_LABEL = "gameLabel"
COL_GAME_SUBTYPE = "gameSubtype"
STATUS_FINAL = 3
 
# Every non-blank gameLabel that is NOT part of the 82-game regular season.
# ("Emirates NBA Cup" is handled separately below since it covers both the
# group stage, which counts, and the knockout rounds, which don't.)
NON_REGULAR_SEASON_LABELS = {
    "Preseason",
    "East First Round", "West First Round",
    "East Conf. Semifinals", "West Conf. Semifinals",
    "East Conf. Finals", "West Conf. Finals",
    "NBA Finals",
    "SoFi Play-In Tournament",
    "All-Star", "All-Star Championship",
    "Rising Stars Semifinal", "Rising Stars Final",
}
# ---------------------------------------------------------------------------
 
DEFAULT_RATING = 1500.0
K_FACTOR = 20.0          # how much one game moves a rating
HOME_ADVANTAGE = 75.0    # Elo points added to home team's rating pre-game
 
 
def expected_win_prob(rating_a: float, rating_b: float) -> float:
    """Probability that team A beats team B, given their Elo ratings."""
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))
 
 
def regular_season_mask(schedule: pd.DataFrame) -> pd.Series:
    """
    True for actual 82-game regular season games only. nba_api's full
    schedule also includes preseason, playoffs, play-in, and All-Star
    weekend (all tagged with a specific gameLabel), plus the NBA Cup
    knockout rounds (same gameLabel as the Cup group stage, but a
    different gameSubtype) — all of those get excluded here.
    """
    label = schedule[COL_GAME_LABEL].fillna("").astype(str).str.strip()
    subtype = schedule[COL_GAME_SUBTYPE].fillna("").astype(str).str.strip()
 
    excluded_by_label = label.isin(NON_REGULAR_SEASON_LABELS)
    excluded_cup_knockout = (label == "Emirates NBA Cup") & (subtype == "in-season-knockout")
 
    return ~(excluded_by_label | excluded_cup_knockout)
 
 
def known_mask(schedule: pd.DataFrame, as_of_date: str | None = None) -> pd.Series:
    """
    Boolean mask of games we treat as "known" (real result available to us),
    restricted to the regular season (see regular_season_mask).
 
    Normally "known" is just games nba_api marks Final. But when as_of_date is
    given, we instead treat every game on/after that date as unknown —
    regardless of whether it was actually already played — so we can rewind
    to a point mid-season and simulate forward from there, even outside a
    live season.
    """
    in_season = regular_season_mask(schedule)
    status = pd.to_numeric(schedule[COL_STATUS], errors="coerce")
    is_final = status == STATUS_FINAL
 
    if as_of_date is None:
        return in_season & is_final
 
    game_dates = pd.to_datetime(schedule[COL_GAME_DATE], utc=True).dt.tz_localize(None)
    cutoff = pd.to_datetime(as_of_date)
    return in_season & is_final & (game_dates < cutoff)
 
 
def completed_games(schedule: pd.DataFrame, as_of_date: str | None = None) -> pd.DataFrame:
    """Known games, sorted chronologically. See known_mask for as_of_date."""
    completed = schedule[known_mask(schedule, as_of_date)].copy()
    return completed.sort_values(COL_GAME_DATE)
 
 
def build_ratings(schedule: pd.DataFrame, as_of_date: str | None = None) -> dict[int, float]:
    """
    Replay all known games in chronological order, updating Elo ratings
    after each one. Returns {team_id: rating}. Pass as_of_date to build
    ratings using only games before that date (so a simulation starting
    there isn't cheating by learning from its own future).
    """
    completed = completed_games(schedule, as_of_date)
 
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
 