from data_pipeline import load_cached

schedule = load_cached("schedule")

keywords =["label", "type", "week", "series", "subtype", "season"]
matches = sorted(c for c in schedule.columns if any(k.lower() in c.lower() for k in keywords))

print(f"Candidate game-type columns:\n")
for c in matches:
    print(f" {c}")
    print(f"    unique values: {schedule[c].unique()[:15]}\n")
    