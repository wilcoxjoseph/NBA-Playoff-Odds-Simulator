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