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

def _team_name_map() -> dict[int, str]:
    """Returns a mapping of team_id to team_name."""
    return {t["id"]: t["full_name"] for t in static_teams.get_teams()}

def current_records(schedule: pd.DataFrame) -> dict[int, list[int]]:
    """Tally {team_id: [wins, losses]} from completed games in the schedule."""
    records: dict[int, list[int]] = {}

    def bump(team_id: int, won: bool) -> None:
        record = records.setdefault(team_id, [0, 0])
        record[0 if won else 1] += 1

    completed = schedule[schedule[COL_STATUS] == STATUS_FINAL]
    for _, game in completed.iterrows():
        home_won = game[COL_HOME_SCORE] > game[COL_AWAY_SCORE]
        bump(game[COL_HOME_TEAM_ID], home_won)
        bump(game[COL_AWAY_TEAM_ID], not home_won)

    return records

def simulate_season_one(
        schedule: pd.DataFrame,
        ratings: dict[int, float],
        rng: random.Random | None = None,
) -> pd.DataFrame:
    """Simulates one full pass of the remaining NBA season.

    Args:
        schedule: DataFrame of all games in the season, including completed and
            remaining games.
        ratings: Mapping of team_id to Elo rating.
        rng: Optional random number generator for reproducibility.

    Returns:
        DataFrame of final standings for that one simulated timeline.
    """
    rng = rng or random.Random()
    records = current_records(schedule)

    remaining = schedule[schedule[COL_STATUS] != STATUS_FINAL]

    def get_rating(team_id: int) -> float:
        """Returns the Elo rating for a given team_id."""
        return ratings.get(team_id, 1500.0)

    # Walk through each remaining game and sample a winner from the Elo win probability.
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
                "games": games,
                "win_pct": wins / games if games else 0.0,
            }
        )
    result = pd.DataFrame(rows).sort_values("wins", ascending=False).reset_index(drop=True)
    return result

if __name__ == "__main__":
    from data_pipeline import load_schedule 