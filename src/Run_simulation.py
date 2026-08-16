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
