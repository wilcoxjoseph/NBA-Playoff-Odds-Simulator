"""
Team-to-conference mapping. This is fixed league structure (barring a
realignment, which is rare), so it's hardcoded rather than pulled from an 
API every run.
"""

from __future__ import annotations

from nba_api.stats.static import teams as static_teams

EASTERN_TRICODES = {
    "ATL", "BOS", "BKN", "CHA", "CHI", "CLE", "DET", "IND",
    "MIA", "MIL", "NYK", "ORL", "PHI", "TOR", "WAS",
}
WESTERN_TRICODES = {
    "DAL", "DEN", "GSW", "HOU", "LAC", "LAL", "MEM", "MIN",
    "NOP", "OKC", "PHX", "POR", "SAC", "SAS", "UTA",
}

def team_id_to_conference() -> dict[int, str]:
    """{team_id: "East" | "West"} for all 30 teams."""
    mapping: dict[int, str] = {}
    for t in static_teams.get_teams():
        tricode = t["abbreviation"]
        if tricode in EASTERN_TRICODES:
            mapping[t["id"]] = "East"
        elif tricode in WESTERN_TRICODES:
            mapping[t["id"]] = "West"
    return mapping
