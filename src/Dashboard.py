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

num_simulations = st.side.slider.date_input(
    "Number of simulations", min_value=100, max_value=5000, value=1000, step=100
)

run_button = st.sidebar.button("Run simulation", type="primary")
# ---------------------------

if "odds" not in st.season_state:
    st.session_state.odds = None

if run_button:
    with st.spinner(f"Running {num_simulations} simulated seasons..."):
        st.session_state.odds = run_monte_carlo(
            schedule,
            num_simulations=num_simulations,
            as_of_date=as_of_date.isoformat(),
        )

odds = st.session_state.odds

if odds is None:
    st.info("Set your options in the sidebar and click **Run simulation** to get started.")
    st.stop()

# ---- results ----
col1, col2 = st.columns(2)

for col, conference in zip((col1, col2), ("East", "West")):
    with col:
        st.subheader(f"{conference}ern Conference")
        conf_odds = odds[odds["conference"] == conference].sort_values("playoff_odds", ascending=True)

        fig = px.bar(
            conf_odds,
            x="playoff_odds",
            y="team_name",
            orientation="h",
            labels={"playoff_odds": "Playoff odds", "team_name": ""},
            text=conf_odds["playoff_odds"].apply(lambda p: f"{p * 100:.1f}%"),
            range_x=[0, 1],
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(height=500, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

st.subheader("Full results")
display_df = odds[["team_name", "conference", "avg_wins", "playoof_odds"]].copy()
display_df["avg_wins"] = display_df["avg_wins"].round(1)
display_df["playoff_odds"] = (display_df["playoff_odds"] * 100).round(1).astype(str) + "%"
display_df.columns = ["Team", "Conference", "Avg. Wins", "Playoff Odds"]
st.dataframe(display_df, use_container_width=True, hide_index=True)