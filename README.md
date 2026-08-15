# NBA Playoff Odds Simulator
 
Monte Carlo simulator that estimates each NBA team's odds of making the playoffs,
their projected seed, and (eventually) title odds — based on an Elo rating model
run over the remaining schedule.
 
## How it works
1. Pull current standings + remaining schedule + completed games (`nba_api`)
2. Build Elo ratings for every team from completed games this season
3. Simulate the rest of the season thousands of times, sampling each remaining
   game's outcome from the Elo win probability
4. Apply the real playoff format (top 6 auto-seed, 7-10 play-in tournament)
5. Aggregate across simulations into per-team probabilities
## Project layout
```
playoff-odds-simulator/
├── data/                  # cached pulls (json/csv), gitignored
├── src/
│   ├── data_pipeline.py   # nba_api pulls + local caching
│   ├── elo.py             # Elo rating model
│   ├── simulate.py        # Monte Carlo season simulation (milestone 3-4)
│   ├── playoffs.py        # play-in + bracket logic (milestone 4)
│   └── dashboard.py        # Streamlit UI (milestone 6)
├── tests/
├── requirements.txt
└── README.md
```
 
## Setup
```bash
python -m venv venv
venv\Scripts\activate          # Windows (PowerShell: venv\Scripts\Activate.ps1)
pip install -r requirements.txt
```
 
## Status
- [x] Milestone 1: Data pipeline (standings, schedule, game log pull + caching)
- [x] Milestone 2: Elo model (build + backtest)
- [x] Milestone 3: Single simulation of remaining season
- [ ] Milestone 4: Monte Carlo loop + play-in/bracket logic
- [ ] Milestone 5: Output tables/probabilities
- [ ] Milestone 6: Streamlit dashboard
## Note on running this
`nba_api` calls `stats.nba.com` directly, so it needs to run somewhere with
normal internet access (your own machine) — it won't work from a sandboxed
environment with restricted network egress. Run `python src/data_pipeline.py`
locally to do the first data pull.
