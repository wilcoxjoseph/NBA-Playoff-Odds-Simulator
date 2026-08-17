import pandas as pd
from data_pipeline import load_cached

schedule = load_cached("schedule")
pd.set_option("display.max_rows", 200)
pd.set_option("display.width", 160)

print("ALL unique gameLabel values:")
print(schedule["gameLabel"].value_counts(dropna=False))

print("\nALL unique gameSubtype values:")
print(schedule["gameSubtype"].value_counts(dropna=False))

print("\nweekNumber range and how it splits by gameLabel:")
print(schedule.groupby("gameLabel")["weekNumber"].agg(["min", "max", "count"]))

print("\nseriesGameNumber: empty vs non-empty, by gameLabel:")
has_series = schedule["seriesGameNumber"].fillna("").astype(str).str.strip() != ""
print(schedule.groupby("gameLabel")[[]].size().to_frame("total").assign(
    has_series_game_number=schedule.groupby("gameLabel").apply(
        lambda g: has_series.loc[g.index].sum()
    )
))

print("\nTotal games where gameLabel == '' (blank):", (schedule["gameLabel"].fillna("") == "").sum())
print("Total games where gameLabel == '' AND weekNumber > 0:",
      ((schedule["gameLabel"].fillna("") == "") & (pd.to_numeric(schedule["weekNumber"], errors="coerce") > 0)).sum())