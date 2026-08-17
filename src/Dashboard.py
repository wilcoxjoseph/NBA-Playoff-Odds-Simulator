"""
Streamlit dashboard for the NBA Playoff Odds Simulator.

Run with:
    streamlit run src/dashboard.py
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
import plotly.express as px
import streamlit as st

from data_pipeline import load_cached
from Run_simulation import run_monte_carlo

st.set_page_config(page_title="NBA Playoff Odds Simulator", layout="wide")
st.title("🏀 NBA Playoff Odds Simulator")
st.caption("Monte Carlo simulation over an Elo rating model, build on nba_api data.")

@st.cache_data
def get_schedule() -> pd.DataFrame | None:
    return load_cached("schedule")

schedule = get_schedule()

if schedule is None:
    st.error("No cached data found. Run 'python src/data_pipeline.py' first, then reload this page.")
    st.stop()

# ---- sidebar controls ----
st.sidebar.header("Simulation settings")

as_of_date = st.sidebar.date_input(
    "Simulate from this date forward",
    value=dt.date(2026, 1, 1),
    help=(
        "Games before this date are treated as known results; everything on "
        "or after it gets simulated. Useful for testing outside a live "
        "season - pick a date mid-way through last season to see how the "
        "rest would have played out."
    ),
)


