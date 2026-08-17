"""
Runs the season simulation thousands of times and aggregates thr results
into playoffs odds per team.

Run directly:
    python src/run_similation.py
"""

from __future__ import annotations
 
from pathlib import Path
 
import numpy as np
import pandas as pd
 
from data_pipeline import load_cached
from elo import (
    COL_AWAY_TEAM_ID,
    COL_HOME_TEAM_ID,
    HOME_ADVANTAGE,
    build_ratings,
    expected_win_prob,
    known_mask,
    regular_season_mask,
)
from Playoffs import apply_playoff_format
from simulate import _team_name_map, current_records
 
# Off-season safe default — see simulate.py for why. Set to None to run live
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
    team_name, conference, playoff_odds (0-1), avg_wins, seed distribution
    columns (seed_1 .. seed_8 = fraction of sims finishing at that seed).
    """
    rng = np.random.default_rng(seed)
    ratings = build_ratings(schedule, as_of_date=as_of_date)
    name_map = _team_name_map()
 
    # ---- one-time setup, NOT repeated per simulation ----
    base_records = current_records(schedule, as_of_date)  # {team_id: [wins, losses]}
 
    remaining = schedule[regular_season_mask(schedule) & ~known_mask(schedule, as_of_date)]
    home_ids = remaining[COL_HOME_TEAM_ID].to_numpy()
    away_ids = remaining[COL_AWAY_TEAM_ID].to_numpy()
    home_win_probs = np.array([
        expected_win_prob(ratings.get(h, 1500.0) + HOME_ADVANTAGE, ratings.get(a, 1500.0))
        for h, a in zip(home_ids, away_ids)
    ])
    n_games = len(home_win_probs)
    print(f"{n_games} remaining games per simulated season, {len(base_records)} teams with a known record")
    # -------------------------------------------------------
 
    made_playoffs_count: dict[int, int] = {}
    win_totals: dict[int, list[int]] = {}
    seed_counts: dict[int, dict[int, int]] = {}
    conferences: dict[int, str] = {}
 
    for i in range(num_simulations):
        records = {tid: list(wl) for tid, wl in base_records.items()}
 
        draws = rng.random(n_games)
        home_wins = draws < home_win_probs
        for home_id, away_id, home_won in zip(home_ids, away_ids, home_wins):
            hrec = records.setdefault(home_id, [0, 0])
            arec = records.setdefault(away_id, [0, 0])
            if home_won:
                hrec[0] += 1
                arec[1] += 1
            else:
                hrec[1] += 1
                arec[0] += 1
 
        final_rows = [
            {
                "team_id": tid,
                "team_name": name_map.get(tid, str(tid)),
                "wins": w,
                "losses": l,
                "win_pct": w / (w + l) if (w + l) else 0.0,
            }
            for tid, (w, l) in records.items()
        ]
        final_df = pd.DataFrame(final_rows)
        result = apply_playoff_format(final_df, ratings, rng=rng)
 
        for _, row in result.iterrows():
            team_id = row["team_id"]
            conferences[team_id] = row["conference"]
            win_totals.setdefault(team_id, []).append(row["wins"])
 
            if row["made_playoffs"]:
                made_playoffs_count[team_id] = made_playoffs_count.get(team_id, 0) + 1
                seed = int(row["seed"])
                seed_counts.setdefault(team_id, {}).setdefault(seed, 0)
                seed_counts[team_id][seed] += 1
 
        if (i + 1) % 250 == 0:
            print(f"  ...{i + 1}/{num_simulations} simulations done")
 
    rows = []
    for team_id, wins_list in win_totals.items():
        n = len(wins_list)
        row = {
            "team_id": team_id,
            "team_name": name_map.get(team_id, str(team_id)),
            "conference": conferences[team_id],
            "avg_wins": sum(wins_list) / n,
            "playoff_odds": made_playoffs_count.get(team_id, 0) / n,
        }
        for seed_num in range(1, 9):
            count = seed_counts.get(team_id, {}).get(seed_num, 0)
            row[f"seed_{seed_num}_pct"] = count / n
        rows.append(row)
 
    result_df = pd.DataFrame(rows).sort_values(
        ["conference", "playoff_odds"], ascending=[True, False]
    ).reset_index(drop=True)
    return result_df
 
 
if __name__ == "__main__":
    schedule = load_cached("schedule")
    if schedule is None:
        print("No cached schedule found — run `python src/data_pipeline.py` first.")
    else:
        print(f"Running {NUM_SIMULATIONS} simulations from as_of_date={AS_OF_DATE}...")
        odds = run_monte_carlo(schedule)
 
        out_path = Path(__file__).resolve().parent.parent / "data" / "playoff_odds.csv"
        odds.to_csv(out_path, index=False)
        print(f"\nFull results saved to {out_path}")
 
        pd.set_option("display.width", 140)
        for conference in ("East", "West"):
            print(f"\n{conference}ern Conference playoff odds:")
            conf_odds = odds[odds["conference"] == conference]
            print(
                conf_odds[["team_name", "avg_wins", "playoff_odds"]]
                .assign(playoff_odds=lambda d: (d["playoff_odds"] * 100).round(1).astype(str) + "%")
                .to_string(index=False)
            )