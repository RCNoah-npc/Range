# Noah's Compression Modules

Python scoring pipeline for Multiple Compression Signal Detection.

## Files
- `run.py` — Entry point. Run with `python -m src.rangers.noah.run`
- `ingest.py` — Loads all data from `agent_drops/data/`
- `features.py` — Engineers macro + stock + valuation features
- `scorer.py` — Scores compression risk (0-100) per stock + market-wide
- `output.py` — Writes dashboard JSON + CSV to `agent_drops/output/`
- `compression-widget.js` — Dashboard widget that displays results
- `index.js` — Widget exports for Rangers registry

## Quick Start
```bash
# 1. Collect data (one-time, ~5 min)
pip install yfinance pandas numpy requests
python agent_drops/collect_all_market_data.py

# 2. Run the scorer
python -m src.rangers.noah.run

# 3. Results appear in agent_drops/output/
#    - compression_dashboard.json (widget reads this)
#    - compression_rankings.csv
#    - market_score.json
```
