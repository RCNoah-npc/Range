# Multiple Compression Signal Detector — Build Instructions

You are building a scoring pipeline that detects **multiple compression risk** — 
when valuation multiples (P/E, EV/EBITDA, P/S, P/B) are likely to contract.

## What Is Multiple Compression

A company's stock price = Earnings × Multiple. When the multiple falls (investors 
pay less per dollar of earnings), the stock drops even if earnings are flat or growing.
This is multiple compression. It tends to happen in waves across sectors or the 
whole market, triggered by macro shifts.

## Your Goal

Build a Python scoring pipeline under `src/rangers/noah/` (alongside the existing `index.js`) that:

1. **Ingests data** from `agent_drops/data/`
2. **Identifies historical compression events** in the stock data
3. **Builds a leading-indicator model** that fires BEFORE compression hits
4. **Scores current market conditions** on compression risk
5. **Ranks individual stocks** by compression vulnerability
6. **Outputs rankings** as CSV + JSON suitable for a dashboard widget

---

## Phase 1: Data Ingestion (`src/rangers/noah/ingest.py`)

Load all data from `agent_drops/data/`:

```python
# Stocks
stocks/all_tickers_5y_daily.csv        # Combined OHLCV, 70 tickers, 5yr daily
stocks/{TICKER}_5y.csv                 # Individual ticker histories
stocks/fundamentals_top50.json         # Current: PE, EV/EBITDA, margins, growth, beta

# Macro (FRED CSVs — all have DATE, VALUE columns)
economic/FED_FUNDS_RATE.csv            # Fed funds rate
economic/10Y_TREASURY.csv             # 10yr yield
economic/2Y_TREASURY.csv              # 2yr yield  
economic/YIELD_SPREAD_10Y2Y.csv       # Yield curve (negative = inverted)
economic/CPI.csv                       # Inflation
economic/CORE_PCE.csv                  # Fed's preferred inflation gauge
economic/GDP.csv                       # Nominal GDP
economic/UNEMPLOYMENT.csv              # Unemployment rate
economic/INITIAL_CLAIMS.csv            # Weekly jobless claims
economic/CONSUMER_SENTIMENT.csv        # UMich sentiment
economic/INDUSTRIAL_PROD.csv           # Industrial production
economic/VIX.csv                       # Volatility index
economic/M2_MONEY_SUPPLY.csv           # Money supply
economic/DOLLAR_INDEX.csv              # USD strength

# Prediction Markets
kalshi/markets_settled_*.json          # Resolved markets (outcomes known)
kalshi/markets_open_*.json             # Live markets

# Crypto
crypto/bitcoin_1y.json                 # BTC daily (prices, market_caps, total_volumes)
crypto/ethereum_1y.json                # ETH daily
```

## Phase 2: Label Historical Compression Events (`src/rangers/noah/labeler.py`)

For each stock in the dataset, compute rolling valuation metrics and flag compression:

```
Compression Event = trailing P/E drops > 20% within a 6-month window
                    OR forward P/E drops > 15% within a 6-month window
```

Since we only have current fundamentals (not historical P/E), approximate:
- Use price / trailing-12mo-earnings (derive earnings from price ÷ current PE, then scale by price history)
- Or simply use **price drawdowns that are NOT earnings-driven** — price drops while the broader earnings trend is flat/up

Label each trading day as:
- `0` = normal
- `1` = compression approaching (within 3 months before a compression event)
- `2` = compression underway

This is your target variable for the model.

## Phase 3: Feature Engineering (`src/rangers/noah/features.py`)

Build features from the data. These are your candidate leading indicators:

### Macro Features
- Fed funds rate: level, 3mo change, 6mo change, acceleration
- Yield curve: level, slope direction, days since inversion
- CPI/PCE: level, YoY change, acceleration (is inflation accelerating?)
- Unemployment: level, 3mo moving average, direction
- Initial claims: 4wk MA, YoY change
- Consumer sentiment: level, 3mo change
- VIX: level, 20d MA, percentile rank (over 2yr window)
- M2 growth rate: YoY change
- Dollar index: 3mo change

### Market Features (per stock)
- Price momentum: 1mo, 3mo, 6mo, 12mo returns
- Relative strength vs SPY: 1mo, 3mo
- Volatility: 20d realized vol, vol-of-vol
- Volume: 20d avg volume change vs 60d
- Distance from 52wk high
- Beta (rolling 60d)
- Sector ETF performance (XLK, XLF, XLE, etc.)

### Valuation Features (per stock)
- Current P/E vs 5yr average P/E (percentile)
- Current EV/EBITDA vs sector median
- P/E expansion over last 12mo (how much multiple has expanded — more expansion = more compression risk)
- Price-to-sales vs historical
- Earnings growth rate vs multiple growth rate (divergence = risk)

### Cross-Asset Features
- Stock-bond correlation (rolling)
- Equity risk premium (earnings yield minus 10Y treasury)
- Credit spreads proxy (HYG vs TLT relative performance)
- Crypto correlation with equities (risk-on/risk-off regime)

## Phase 4: Model (`src/rangers/noah/model.py`)

Use **gradient boosted trees** (scikit-learn GradientBoostingClassifier or HistGradientBoostingClassifier) as the primary model. They handle mixed feature types well and give feature importances.

```python
# Train/test split: time-based (no lookahead!)
# Train: first 70% of timeline
# Validation: next 15%
# Test: final 15%

# Target: binary (0 = no compression coming, 1 = compression within 3 months)
# Evaluate: precision, recall, F1, and especially precision at top decile
#   (we care more about: when the model says compression is coming, is it right?)

# Also train a regression variant: predicted magnitude of P/E contraction
```

**Important constraints:**
- NO lookahead bias. All features must use data available at prediction time.
- Time-series cross-validation (expanding window), not random splits.
- Feature importance analysis — which indicators matter most?

## Phase 5: Scoring & Ranking (`src/rangers/noah/scorer.py`)

Using the trained model + latest data:

```python
def score_market() -> dict:
    """Overall market compression risk score 0-100"""
    
def rank_stocks() -> pd.DataFrame:
    """
    Returns DataFrame with columns:
    - ticker
    - compression_risk_score (0-100)
    - current_pe
    - pe_vs_5yr_avg (percentile)  
    - ev_ebitda
    - earnings_growth
    - price_momentum_3mo
    - sector
    - risk_factors (list of top 3 reasons for the score)
    
    Sorted by compression_risk_score descending.
    """
```

## Phase 6: Output (`src/rangers/noah/output.py`)

Generate:
1. `output/compression_rankings.csv` — full ranked list
2. `output/compression_rankings.json` — same, JSON format for dashboard
3. `output/market_score.json` — overall market compression risk
4. `output/model_report.json` — model performance metrics, feature importances
5. `output/backtest_results.csv` — historical signal accuracy

### Dashboard JSON format:
```json
{
  "market_score": {
    "compression_risk": 72,
    "label": "Elevated",
    "top_drivers": ["Fed rate acceleration", "Yield curve flattening", "P/E expansion above historical"],
    "as_of": "2026-03-28T09:00:00Z"
  },
  "stock_rankings": [
    {
      "ticker": "NVDA",
      "compression_risk": 89,
      "current_pe": 65.2,
      "pe_percentile_5yr": 92,
      "ev_ebitda": 48.3,
      "sector": "Technology",
      "risk_factors": ["Extreme P/E expansion", "High beta", "Sector crowding"]
    }
  ]
}
```

## Phase 7: Iterate

After the first pass:
1. Check backtest metrics. If precision < 60% at top decile, revisit features.
2. Try adding/removing feature groups to see what moves the needle.
3. Consider an ensemble: GBT + logistic regression + simple rules-based overlay.
4. Look at sector-level compression vs individual — sometimes it's a tide, not a stock.

## Run Entry Point

Create `src/rangers/noah/run.py`:
```python
"""
Main entry point. Run from project root:
    python -m src.rangers.noah.run

Or:
    python src/rangers/noah/run.py
"""
from .ingest import load_all_data
from .labeler import label_compression_events  
from .features import build_features
from .model import train_and_evaluate
from .scorer import score_market, rank_stocks
from .output import write_outputs

def main():
    print("Loading data...")
    data = load_all_data("agent_drops/data")
    
    print("Labeling compression events...")
    labeled = label_compression_events(data)
    
    print("Engineering features...")  
    features = build_features(labeled, data)
    
    print("Training model...")
    model, metrics = train_and_evaluate(features)
    
    print("Scoring current market...")
    market_score = score_market(model, data)
    rankings = rank_stocks(model, data)
    
    print("Writing outputs...")
    write_outputs(market_score, rankings, metrics)
    
    print(f"\nMarket compression risk: {market_score['compression_risk']}/100 ({market_score['label']})")
    print(f"Top 5 compression candidates:")
    for _, row in rankings.head().iterrows():
        print(f"  {row['ticker']:6s}  risk={row['compression_risk_score']:3.0f}  P/E={row.get('current_pe', 'N/A')}")

if __name__ == "__main__":
    main()
```

## Key Principles

- **No lookahead bias.** This is the #1 sin in financial modeling. Every feature must be computable from data available at prediction time.
- **Precision over recall.** False positives (crying wolf) are worse than missing some compression events. Tune for precision.
- **Interpretability matters.** For each stock's score, provide the top 3 reasons WHY. This is for a dashboard — humans need to understand it.
- **Start simple, then complicate.** Get a basic version working end-to-end first. Then iterate.
- **Time-series discipline.** Always split by time. Never shuffle. Expanding window CV.
