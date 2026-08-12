"""
Data pipeline for the Playoff Odds Simulator.

Pulls current standings and the full season season schedule (completed remaining games)
from nba_api and caches them locally in SQLite so we don't hammer 
stats.nba.com on every run.

Run directly to do a fresh pull:
    src/data_pipeline.py
"""

import sqlite3
import time
from pathlib import Path

import pandas as pd
from nba_api.stats.endpoints import leaguestandingsv3, scheduleleaguev2
from nba_api.stats.static import teams

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "nba_cache.sqlite"

CURRENT_SEASON = "2025-26"  # Update this each season format: "YYYY-YY"

def _get_conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)
