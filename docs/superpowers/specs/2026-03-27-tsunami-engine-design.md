# Tsunami Engine: AI Disruption Multiple Compression Scanner

## Overview

A Python CLI tool that identifies publicly traded companies vulnerable to AI disruption, calculates their projected price drop via multiple compression math, filters for cost-efficient put options, and sizes positions using the Kelly Criterion.

**Strategy:** Buy puts on legacy companies whose earnings multiples will compress as AI competitors steal market share. We don't need the company to die -- we need the market to stop paying a growth premium.

**Not in scope:** Direct equity shorts, margin/HTB logic, aggressor/narrative attack equation, real-time dark pool data (future enhancement).

**Known limitations:** The free yfinance adapter cannot provide dark pool volume, net gamma exposure, or IV rank directly. Stage 5 (Flow Radar) is deferred to the paid adapter upgrade. Stages 1-4 and 6-7 are fully functional with yfinance.

## Decisions

| Decision      | Choice                                                          |
| ------------- | --------------------------------------------------------------- |
| Strategy      | Puts only, 10% hard cap per position, multiple compression      |
| Data source   | Pluggable adapters (yfinance free start, FMP/Polygon upgrade)   |
| Location      | `src/rangers/noah/tsunami/`                                     |
| Interface     | Python CLI (Click)                                              |
| Database      | SQLite now, PostgreSQL migration path                           |
| Training data | Seed 10 historical casualties + scraper for new ones            |
| Language      | Python                                                         |

## Project Structure

```text
src/rangers/noah/tsunami/
├── __init__.py
├── cli.py                  # Click-based CLI entry point
├── db.py                   # SQLite connection + schema init
├── config.py               # Gate thresholds, sector defaults, configurable constants
├── adapters/
│   ├── __init__.py
│   ├── base.py             # Abstract adapter interface
│   └── yfinance_adapter.py # Free data source
├── pipeline/
│   ├── __init__.py
│   ├── scanner.py          # Phase 1: Vulnerability scoring
│   ├── compressor.py       # Phase 2: Multiple compression math
│   ├── backtester.py       # Phase 3: Train on historical casualties
│   ├── filter.py           # Phase 4: VRP filter
│   ├── sizer.py            # Phase 5: Kelly criterion sizing
│   └── underwriter.py      # Phase 6: Strike selection + execution matrix
├── models/
│   ├── __init__.py
│   └── schemas.py          # Dataclasses for Target, Prediction, Signal, Position
└── data/
    ├── casualties.csv       # Seed: 10+ Patient Zero companies
    └── sector_defaults.json # Sector eps_decay and terminal_PE defaults
```

**Removed from initial build:** `flow_radar.py` (requires paid dark pool data), `industry_vars.csv` (folded into `sector_defaults.json`), `sensitivity.csv` (generated on-demand, not persisted as file).

## CLI Commands

| Command                   | Description                                              |
| ------------------------- | -------------------------------------------------------- |
| `tsunami seed`            | Load historical casualties into DB                       |
| `tsunami scan <ticker>`   | Run vulnerability score on a ticker                      |
| `tsunami compress <ticker>` | Calculate price target via multiple compression        |
| `tsunami backtest`        | Train model on casualties, extract feature weights       |
| `tsunami filter`          | Rank targets by VRP (cheapest puts first)                |
| `tsunami size`            | Kelly allocation across approved targets                 |
| `tsunami underwrite`      | Generate execution matrix (strikes, expiry, contracts)   |
| `tsunami run`             | Full pipeline end-to-end                                 |
| `tsunami run --paper`     | Full pipeline in paper trading mode                      |
| `tsunami test`            | Smoke test against known casualties                      |

## Database Schema

### target_companies

| Column        | Type      | Description                    |
| ------------- | --------- | ------------------------------ |
| target_id     | TEXT PK   | e.g. 'TGT_001'                |
| ticker        | TEXT UNIQUE | e.g. 'CHGG'                 |
| company       | TEXT      | e.g. 'Chegg'                  |
| sector        | TEXT      | e.g. 'EdTech'                 |
| added_date    | TIMESTAMP | When added to watchlist        |

### fundamental_predictions

| Column              | Type      | Description                                  |
| ------------------- | --------- | -------------------------------------------- |
| model_id            | INTEGER PK | Auto-increment                              |
| target_id           | TEXT FK   | References target_companies                  |
| calculated_at       | TIMESTAMP | When prediction was generated                |
| sga_pct             | REAL      | SG&A as % of revenue                        |
| gross_margin_pct    | REAL      | Gross margin percentage                      |
| debt_to_equity      | REAL      | Debt-to-equity ratio                         |
| fcf_yield_pct       | REAL      | Free cash flow yield                         |
| roic_pct            | REAL      | Return on invested capital                   |
| vulnerability_score | REAL      | Composite weighted score (0-1)               |
| current_eps         | REAL      | Current EPS from adapter                     |
| current_pe          | REAL      | Current P/E multiple                         |
| eps_decay_pct       | REAL      | Estimated AI shock to earnings               |
| terminal_pe         | REAL      | Utility re-rating target multiple            |
| projected_price     | REAL      | Calculated price target                      |
| predicted_drop_pct  | REAL      | Implied total percentage drop                |

### market_friction_log

| Column            | Type      | Description                                    |
| ----------------- | --------- | ---------------------------------------------- |
| log_id            | INTEGER PK | Auto-increment                                |
| target_id         | TEXT FK   | References target_companies                    |
| logged_at         | TIMESTAMP | Timestamp of data point                        |
| live_spot         | REAL      | Current stock price                            |
| atm_put_iv        | REAL      | ATM put implied volatility (from options chain) |
| put_call_ratio    | REAL      | Derived from options chain volume              |
| est_premium_ask   | REAL      | ATM put premium (mid of bid/ask)               |
| hv_252d           | REAL      | 252-day historical volatility (calculated)     |
| vrp_spread        | REAL      | atm_put_iv minus hv_252d (cost gate)           |

### model_weights

Persists the output of the backtester so the scanner can load weights across sessions.

| Column       | Type      | Description                                |
| ------------ | --------- | ------------------------------------------ |
| weight_id    | INTEGER PK | Auto-increment                            |
| created_at   | TIMESTAMP | When weights were calculated               |
| feature_name | TEXT      | e.g. 'sga_pct', 'gross_margin_pct'        |
| weight_pct   | REAL      | Feature importance as percentage            |
| r_squared    | REAL      | Model R-squared at time of training         |

### positions

| Column           | Type      | Description                                    |
| ---------------- | --------- | ---------------------------------------------- |
| position_id      | INTEGER PK | Auto-increment                                |
| target_id        | TEXT FK   | References target_companies                    |
| opened_at        | TIMESTAMP | Trade open date                                |
| strike           | REAL      | Put strike price                               |
| expiry_date      | TEXT      | Option expiration date                         |
| premium_paid     | REAL      | Premium per share                              |
| contracts        | INTEGER   | Number of contracts                            |
| capital_deployed | REAL      | Total capital in position                      |
| kelly_pct        | REAL      | Kelly allocation percentage                    |
| status           | TEXT      | OPEN, TAKE_PROFIT, STOP_LOSS, EXPIRED          |
| closed_at        | TIMESTAMP | Trade close date (nullable)                    |
| realized_pnl     | REAL      | Realized profit/loss (nullable)                |

### paper_positions

Mirrors the `positions` table with additional tracking columns for paper trading validation.

| Column              | Type      | Description                                   |
| ------------------- | --------- | --------------------------------------------- |
| paper_id            | INTEGER PK | Auto-increment                               |
| target_id           | TEXT FK   | References target_companies                   |
| opened_at           | TIMESTAMP | When paper trade was opened                   |
| strike              | REAL      | Put strike price                              |
| expiry_date         | TEXT      | Option expiration date                        |
| premium_at_open     | REAL      | Premium when trade was signaled               |
| contracts           | INTEGER   | Number of contracts                           |
| capital_deployed    | REAL      | Hypothetical capital                          |
| spot_at_open        | REAL      | Stock price when trade was signaled           |
| spot_at_close       | REAL      | Stock price at expiry or review (nullable)    |
| predicted_drop_pct  | REAL      | What the model predicted                      |
| actual_drop_pct     | REAL      | What actually happened (nullable)             |
| status              | TEXT      | OPEN, CLOSED, EXPIRED                         |

## Configurable Constants (config.py)

```python
# Gate thresholds
VULNERABILITY_GATE = 0.6       # minimum vulnerability_score to proceed
COMPRESSION_GATE = 0.25        # minimum predicted_drop to qualify (25%)
VRP_REJECT_THRESHOLD = 0.15    # VRP above 15% = puts too expensive
ROP_MINIMUM = 3.0              # minimum 300% return on premium

# Kelly sizing
KELLY_FRACTION = 0.25          # quarter-Kelly
MAX_POSITION_PCT = 0.10        # 10% hard cap per position
DEFAULT_WIN_PROB = 0.55        # default p before backtest calibration

# Underwriter
TARGET_DTE_MIN = 180           # minimum days to expiry
TARGET_DTE_MAX = 300           # maximum days to expiry

# Exit triggers
TAKE_PROFIT_ROI = 2.0          # close when ROI >= 200% of premium
STOP_LOSS_ROI = -0.50          # close when premium decays 50% from peak
```

## Pipeline Logic

### Stage 1: Scanner

Pulls financial metrics via the data adapter and calculates a composite vulnerability score.

**Metrics:** SGA% of Revenue, Gross Margin, Debt-to-Equity, FCF Yield, ROIC

**yfinance derivation notes:**

- `sga_pct`: `income_stmt['SellingGeneralAndAdministration'] / income_stmt['TotalRevenue']`. Field name varies; adapter normalizes.
- `fcf_yield`: `cashflow['FreeCashFlow'] / (info['sharesOutstanding'] * info['currentPrice'])`. Derived, not a direct field.
- `roic`: `(income_stmt['NetIncome'] * (1 - 0.21)) / (balance_sheet['TotalAssets'] - balance_sheet['CurrentLiabilities'])`. Manual calculation.
- `gross_margin`, `debt_to_equity`: Available directly from `info` dict.

**Scoring:** Weighted composite using backtester-derived weights loaded from `model_weights` table. Before first backtest, uses equal weights (20% each).

**Gate:** `vulnerability_score > VULNERABILITY_GATE` (default 0.6) advances to compressor.

### Stage 2: Compressor

Calculates the projected share price after AI-driven multiple compression.

**Formula:**

```python
if current_eps <= 0:
    # Already unprofitable: use revenue-based valuation instead
    projected_price = current_spot * (1 - eps_decay)  # simple percentage haircut
else:
    projected_price = (current_eps * (1 - eps_decay)) * terminal_pe

predicted_drop = (current_spot - projected_price) / current_spot
```

**Sector defaults** (loaded from `data/sector_defaults.json`):

| Sector             | eps_decay | terminal_PE |
| ------------------ | --------- | ----------- |
| EdTech             | 25%       | 13x         |
| BPO/CallCenter     | 15%       | 12x         |
| IT Services        | 10%       | 14x         |
| Legal Services     | 12%       | 10x         |
| Freelance/Gig      | 20%       | 11x         |
| Media/Stock Images | 18%       | 12x         |

**Unknown sector fallback:** Uses median values (eps_decay=15%, terminal_PE=12x) with a warning.

**Gate:** `predicted_drop > COMPRESSION_GATE` (default 25%) qualifies.

### Stage 3: Backtester

Trains the predictive model on historical "Patient Zero" casualties.

**Training set (seed):** CHGG, FVRR, UPWK, TEP.PA, TASK, SSTK, TWOU, GETY, EPAM, COUR

Note: LZB (La-Z-Boy) removed from original spec -- its decline is tied to housing cycles, not AI disruption. Replaced with COUR (Coursera), a cleaner AI casualty in EdTech.

**Training features (X):** The same 5 metrics from Stage 1: sga_pct, gross_margin_pct, debt_to_equity, fcf_yield_pct, roic_pct.

**Target variable (y):** `Abnormal_Return_12M` -- the 12-month return relative to the S&P 500.

**Method:**

1. Random Forest (n=1000, max_depth=5) for feature importance and non-linear thresholds
2. Output: feature importance weights persisted to `model_weights` table

**Note on OLS:** With only 10 training samples and 5 features, OLS p-values are unreliable (4 degrees of freedom). OLS is omitted from the initial build. When the training set grows to 25+ casualties, OLS can be added for statistical validation. For now, Random Forest handles both weighting and prediction.

**Quality gate:** R-squared > 0.75 = model is valid. Below 0.60 = warning to add/prune features.

### Stage 4: Filter (VRP Gate)

Prevents buying overpriced puts by comparing implied volatility to historical realized volatility.

**Formula:** `VRP = atm_put_iv - hv_252d`

Where:

- `atm_put_iv`: Implied volatility of the nearest ATM put from yfinance options chain
- `hv_252d`: Annualized standard deviation of 252 trailing daily log returns (calculated from OHLCV)

**Decision logic:**

- VRP > `VRP_REJECT_THRESHOLD` (15%): **REJECT** (puts too expensive)
- VRP 0-15%: **FAIR VALUE** (acceptable entry)
- VRP < 0%: **PREMIUM DISCOUNT** (puts are cheap, priority target)

**Output:** Targets ranked by VRP ascending (cheapest first).

### Stage 5: Sizer

Position sizing via fractional Kelly Criterion.

**Formula:**

```python
q = 1 - p                              # probability of loss
f_full = p - (q / b)                    # full Kelly fraction
f_applied = min(f_full * KELLY_FRACTION, MAX_POSITION_PCT)  # quarter-Kelly, capped at 10%

if f_full <= 0:
    # negative expected value -- reject the trade
    f_applied = 0

capital_to_deploy = portfolio_value * f_applied
```

**Inputs:**

- `p` = win probability (from backtest hit rate, default 0.55)
- `q` = probability of loss = `1 - p`
- `b` = payoff ratio = `(projected_intrinsic_value - premium_paid) / premium_paid`

**Hard cap:** No single position exceeds **10%** of total portfolio value.

### Stage 6: Underwriter

Selects the optimal put contract and generates the execution matrix.

**Strike selection rule:** Select the listed strike price nearest to `current_spot * (1 + predicted_drop / 2)`. This targets the midpoint between the current price and the projected price -- buying "halfway to the target" maximizes the balance between intrinsic value at target and premium cost.

**DTE target:** Select the expiration date closest to 240 days out, within the range of `TARGET_DTE_MIN` (180) to `TARGET_DTE_MAX` (300).

**ROP formula:**

```python
intrinsic_at_target = max(0, strike - projected_price)
rop = (intrinsic_at_target - premium_paid) / premium_paid
# Must be >= ROP_MINIMUM (3.0 = 300%)
```

**Output:** Execution matrix with ticker, strike, expiry, contracts, premium, capital, ROP, decision (EXECUTE/REJECT).

## Position Management (Exit Triggers)

Positions are monitored via `tsunami monitor` (or checked during `tsunami run`).

**Take-Profit trigger:** Close position when unrealized ROI >= `TAKE_PROFIT_ROI` (200% of premium paid).

```python
current_premium = get_option_premium(ticker, strike, expiry)
roi = (current_premium - premium_paid) / premium_paid
if roi >= TAKE_PROFIT_ROI:
    status = 'TAKE_PROFIT'
```

**Stop-Loss trigger:** Close position when premium decays 50% from the highest premium observed since opening.

```python
if current_premium <= peak_premium * (1 + STOP_LOSS_ROI):  # peak * 0.5
    status = 'STOP_LOSS'
```

**Expiry:** If the option reaches 30 DTE without hitting take-profit or stop-loss, close to avoid accelerating theta decay.

## Testing & Validation

### Backtest Validation

- Run model against seed casualties with known 12-month outcomes
- Target: R-squared > 0.75
- Warning threshold: R-squared < 0.60

### Paper Trading

- `tsunami run --paper` writes to `paper_positions` table
- Records `predicted_drop_pct` at open and `actual_drop_pct` at close/expiry
- After 30 days of paper trades, compare predicted vs actual via simple scatter plot

### Smoke Tests

- Each pipeline stage tested against seed data
- `tsunami test` runs CHGG as known-good input
- **Pass criteria:** predicted drop between 50% and 80% (known actual: ~65%)
- Individual stage tests verify data flows correctly between stages

### Error Handling

- Adapter failures: graceful fallback to last cached data in SQLite
- Missing data fields: skip ticker with warning, don't halt pipeline
- Negative EPS: compressor falls back to revenue-based percentage haircut
- Unknown sector: uses median defaults with warning
- No qualifying targets: "No actionable signals" message
- No options chain data: skip VRP filter for that ticker with warning

## Data Adapter Interface

```python
class DataAdapter(ABC):
    @abstractmethod
    def get_financials(self, ticker: str) -> dict:
        """Returns sga_pct, gross_margin, debt_equity, fcf_yield, roic.
        FCF yield and ROIC are derived calculations -- see Stage 1 notes."""

    @abstractmethod
    def get_price(self, ticker: str) -> float:
        """Returns current spot price."""

    @abstractmethod
    def get_valuation(self, ticker: str) -> dict:
        """Returns EPS, P/E ratio."""

    @abstractmethod
    def get_historical_prices(self, ticker: str, period: str) -> pd.DataFrame:
        """Returns OHLCV data for volatility calculations (hv_252d)."""

    @abstractmethod
    def get_options_chain(self, ticker: str, min_dte: int) -> pd.DataFrame:
        """Returns puts options chain filtered to min_dte.
        Columns: strike, bid, ask, volume, openInterest, impliedVolatility, expiry.
        Used by filter (VRP) and underwriter (strike selection, premium)."""
```

Initial implementation: `YFinanceAdapter`. Future: `FMPAdapter`, `PolygonAdapter`.

## Dependencies

```text
click          # CLI framework
yfinance       # Free financial data
pandas         # Data manipulation
numpy          # Numerical computation
scikit-learn   # Random Forest, train/test split
```

No paid APIs required at launch.
