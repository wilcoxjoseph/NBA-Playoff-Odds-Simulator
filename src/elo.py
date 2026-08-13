"""
Elo rating model for NBA teams.

Builds a rating for every team by replaying completed games from the cached
schedule in chronological order. These ratings feed the Monte Carlo
simulation's win probability calculations.
"""

from __future__ import annotations

