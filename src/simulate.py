"""
Simulates one full pass of the remaining NBA season.

Tallies each team's current record from completed games, then walks through
every remaining game, sampling a winner from the Elo win probability. Returns
projected final standings for that one simulated timeline.

This is the core loop milestone 4 will wrap in a 10,000x Monte Carlo loop and
layer playoff-format logic on top of.

Run directly to see one simulated season's final standings:
    python src/simulate.py
"""

from __future__ import annotations
 
import random
 
import pandas as pd
from nba_api.stats.static import teams as static_teams
 
from elo import COL_AWAY_SCORE, COL_AWAY_TEAM_ID, COL_HOME_SCORE, COL_HOME_TEAM_ID
from elo import COL_STATUS, STATUS_FINAL, HOME_ADVANTAGE, build_ratings, expected_win_prob
from elo import known_mask, regular_season_mask
 
 
def _team_name_map() -> dict[int, str]:
    return {t["id"]: t["full_name"] for t in static_teams.get_teams()}
 
 
def current_records(schedule: pd.DataFrame, as_of_date: str | None = None) -> dict[int, list[int]]:
    """Tally {team_id: [wins, losses]} from known games (see elo.known_mask)."""
    records: dict[int, list[int]] = {}
 
    def bump(team_id: int, won: bool) -> None:
        record = records.setdefault(team_id, [0, 0])
        record[0 if won else 1] += 1
 
    completed = schedule[known_mask(schedule, as_of_date)]
    for _, game in completed.iterrows():
        home_won = game[COL_HOME_SCORE] > game[COL_AWAY_SCORE]
        bump(game[COL_HOME_TEAM_ID], home_won)
        bump(game[COL_AWAY_TEAM_ID], not home_won)
 
    return records
 
 
def simulate_season_once(
    schedule: pd.DataFrame,
    ratings: dict[int, float],
    rng: random.Random | None = None,
    as_of_date: str | None = None,
) -> pd.DataFrame:
    """
    Run one simulated timeline of the season from as_of_date forward (or from
    "now" if as_of_date is None — i.e. whatever nba_api says isn't Final yet).
    Team strength (Elo ratings) is held fixed for the simulation — only home
    advantage and the random game-to-game bounce vary. Returns a DataFrame
    sorted by wins desc: team_id, team_name, wins, losses, win_pct.
    """
    rng = rng or random.Random()
    records = current_records(schedule, as_of_date)
 
    remaining = schedule[regular_season_mask(schedule) & ~known_mask(schedule, as_of_date)]
 
    def get_rating(team_id: int) -> float:
        return ratings.get(team_id, 1500.0)
 
    for _, game in remaining.iterrows():
        home_id = game[COL_HOME_TEAM_ID]
        away_id = game[COL_AWAY_TEAM_ID]
 
        home_rating = get_rating(home_id) + HOME_ADVANTAGE
        away_rating = get_rating(away_id)
        home_win_prob = expected_win_prob(home_rating, away_rating)
 
        home_won = rng.random() < home_win_prob
 
        record = records.setdefault(home_id, [0, 0])
        record[0 if home_won else 1] += 1
        record = records.setdefault(away_id, [0, 0])
        record[0 if not home_won else 1] += 1
 
    name_map = _team_name_map()
    rows = []
    for team_id, (wins, losses) in records.items():
        games = wins + losses
        rows.append(
            {
                "team_id": team_id,
                "team_name": name_map.get(team_id, str(team_id)),
                "wins": wins,
                "losses": losses,
                "win_pct": wins / games if games else 0.0,
            }
        )
 
    result = pd.DataFrame(rows).sort_values("wins", ascending=False).reset_index(drop=True)
    return result
 
 
if __name__ == "__main__":
    from data_pipeline import load_cached
 
    # Off-season safe default: rewind to partway through last season so
    # there's actually something to simulate. Change this once the 2026-27
    # schedule exists and you want to run it live (as_of_date=None).
    AS_OF_DATE = "2026-01-01"
 
    schedule = load_cached("schedule")
    if schedule is None:
        print("No cached schedule found — run `python src/data_pipeline.py` first.")
    else:
        ratings = build_ratings(schedule, as_of_date=AS_OF_DATE)
        final = simulate_season_once(schedule, ratings, as_of_date=AS_OF_DATE)
        print(f"One simulated season's final standings (rewound to {AS_OF_DATE}):\n")
        print(final.to_string(index=False))