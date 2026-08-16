"""
Runs the season simulation thousands of times and aggregates thr results
into playoffs odds per team.

Run directly:
    python src/run_similation.py
"""

from __future__ import annotations

import random

import pandas as pd

from data_pipeline import load_cached
from elo import build_ratings
from playoffs import apply_playoff_format
from simulate import simulate_season_once

# Off-season safe default - see simulate.py for why. Set to None to run live
# once the current season's schedule has games left to play.
AS_OF_DATE = "2026-01-01"
NUM_SIMULATIONS = 2000

def run_monte_carlo(
        schedule: pd.DataFrame,
        num_simulations: int = NUM_SIMULATIONS,
        as_of_date: str | None = AS_OF_DATE,
        seed: int | None = None,
) -> pd.DataFrame:

    """
    Runs num_simulations simulated seasons and returns one row per team:
    team_name, conference, playoffs_odds (0-1), avg_wins, seed distribution
    columns (seed_1 .. seed_8 = fraction of sims finsihing at that seed). 
    """
    rng = random.Random(seed)
    ratings = build_ratings(schedule, as_of_date=as_of_date)

    # team_id -> running totals across simulations
    made_playoffs_count: dict[int, int] = {}
    win_totals: dict[int, list[int]] = {}
    seed_counts: dict[int, dict[int, int]] = {}
    team_names: dict[int, str] = {}
    conferences: dict[int, str] = {}

    for i in range(num_simulations):
        final = simulate_season_once(schedule, ratings, rng=rng, as_of_date=as_of_date)
        result = apply_playoff_format(final, ratings, rng=rng)

        for _, row in result.iterrows():
            team_id = row["team_id"]
            team_names[team_id] = row["team_name"]
            conferences[team_id] = row["conference"]

            win_totals.setdefault(team_id, []).append(row["wins"])

            if row["made_playoffs"]:
                made_playoffs_count[team_id] = made_playoffs_count.get(team_id, 0)

                seed = int(row["seed"])
                