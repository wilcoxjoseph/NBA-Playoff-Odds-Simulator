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


