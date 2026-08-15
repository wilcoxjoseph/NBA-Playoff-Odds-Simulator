"""
Data pipeline for the Playoff Odds Simulator.
 
Pulls current standings and the full season schedule (completed + remaining
games) from nba_api and caches them locally in SQLite so we don't hammer
stats.nba.com on every run.
 
Run directly to do a fresh pull:
    python src/data_pipeline.py
"""
 
from __future__ import annotations
 
import sqlite3
import time
from pathlib import Path
 
import pandas as pd
from nba_api.stats.endpoints import leaguestandingsv3, scheduleleaguev2
from nba_api.stats.static import teams
 
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "nba_cache.sqlite"
 
CURRENT_SEASON = "2025-26"  # nba_api season format: "YYYY-YY"
 
 
def _get_conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)
 
 
def fetch_standings(season: str = CURRENT_SEASON) -> pd.DataFrame:
    """Current conference standings: wins, losses, win pct, games back, etc."""
    resp = leaguestandingsv3.LeagueStandingsV3(season=season)
    df = resp.get_data_frames()[0]
    return df
 
 
def fetch_full_schedule(season: str = CURRENT_SEASON) -> pd.DataFrame:
    """
    Full season schedule — completed games (with final scores) and remaining
    games (no score yet). This is the single source we need for both the
    Elo backtest and the Monte Carlo simulation input.
    """
    resp = scheduleleaguev2.ScheduleLeagueV2(season=season)
    df = resp.get_data_frames()[0]
    return df
 
 
def cache_dataframe(df: pd.DataFrame, table_name: str) -> None:
    conn = _get_conn()
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()
 
 
def load_cached(table_name: str) -> pd.DataFrame | None:
    conn = _get_conn()
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    except pd.errors.DatabaseError:
        df = None
    conn.close()
    return df
 
 
def refresh_all(season: str = CURRENT_SEASON) -> None:
    """Pull fresh standings + schedule and overwrite the local cache."""
    print(f"Pulling standings for {season}...")
    standings = fetch_standings(season)
    cache_dataframe(standings, "standings")
    print(f"  -> {len(standings)} teams cached")
 
    time.sleep(1)  # be polite to stats.nba.com between calls
 
    print(f"Pulling full schedule for {season}...")
    schedule = fetch_full_schedule(season)
    cache_dataframe(schedule, "schedule")
    print(f"  -> {len(schedule)} games cached")
 
 
if __name__ == "__main__":
    refresh_all()
    standings = load_cached("standings")
    schedule = load_cached("schedule")
    print("\nStandings sample:")
    print(standings[["TeamCity", "TeamName", "WINS", "LOSSES", "WinPCT"]].head())
    print("\nSchedule sample:")
    print(schedule.head())
 