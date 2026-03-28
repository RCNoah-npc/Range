# Tsunami Variable Universe

Every variable has a weight. Every weight is calibrated from historical compression autopsies. The more variables pointing down simultaneously, the stronger the signal -- no single trigger required.

## Variable Categories

### 1. VALUATION PRESSURE (Company-Level)
How overpriced is this company relative to what it actually produces?

| Variable | Source | Signal | Weight Direction |
|----------|--------|--------|-----------------|
| P/E Ratio | yfinance | Higher = more compression room | Higher is worse |
| P/E vs Sector Median | calculated | Above sector = overpriced relative to peers | Higher is worse |
| EV/EBITDA | yfinance | Enterprise value to cash earnings | Higher is worse |
| Price/Sales | yfinance | Revenue multiple (for pre-profit companies) | Higher is worse |
| PEG Ratio | yfinance | P/E divided by growth rate. >2 = overpaying for growth | Higher is worse |
| Forward P/E vs Trailing | yfinance | If forward > trailing, analysts expect DECELERATION | Forward > Trailing is worse |

### 2. MARGIN FRAGILITY (Company-Level)
How vulnerable are the margins to competition or economic pressure?

| Variable | Source | Signal | Weight Direction |
|----------|--------|--------|-----------------|
| SGA % Revenue | income_stmt | Human capital intensity | Higher is worse |
| Gross Margin | yfinance | Fat margins = fat target for disruption | Context-dependent |
| SGA x Gross Margin | calculated | Composite "fat target" metric | Higher is worse |
| Operating Margin Trend | quarterly | Declining margins = compression in progress | Declining is worse |
| R&D % Revenue | income_stmt | Low R&D = not building moat | Lower is worse |
| Revenue per Employee | calculated | Low = labor-intensive, automatable | Lower is worse |

### 3. MOAT STRENGTH (Company-Level)
Can this company defend its position or is it a feature waiting to be cloned?

| Variable | Source | Signal | Weight Direction |
|----------|--------|--------|-----------------|
| ROIC | calculated | High ROIC = moat protecting returns | Higher is better |
| Revenue Retention Rate | earnings calls, 10-K | Customer stickiness | Higher is better |
| Product Count | manual/research | Single product = feature, multi = platform | More is better |
| Customer Concentration | 10-K | Top 10 customers = % revenue | More concentrated is worse |
| B2B vs B2C | manual | Enterprise = sticky, Consumer = fickle | B2B is better |
| Patent Portfolio | SEC/research | IP protection depth | More is better |
| Ecosystem Size | research | Developer/app ecosystem around platform | Larger is better |

### 4. FINANCIAL STRESS (Company-Level)
How much runway does the company have if things go wrong?

| Variable | Source | Signal | Weight Direction |
|----------|--------|--------|-----------------|
| FCF Yield | calculated | Cash generation relative to market cap | Lower/negative is worse |
| Debt/Equity | yfinance | Leverage amplifies compression | Higher is worse |
| Interest Coverage | income_stmt | Can they service their debt? | Lower is worse |
| Cash Runway (months) | calculated | Cash / monthly burn rate | Fewer months is worse |
| Debt Maturity Wall | 10-K | When does debt come due? | Sooner is worse |
| Current Ratio | balance_sheet | Short-term liquidity | Lower is worse |

### 5. MARKET CYCLE POSITION (Macro)
Where are we in the overall economic cycle? Late cycle = compression amplifier.

| Variable | Source | Signal | Weight Direction |
|----------|--------|--------|-----------------|
| Fed Funds Rate | FRED API | Rising rates compress multiples | Rising is worse |
| Fed Funds Rate Direction | FRED API | Hiking vs cutting cycle | Hiking is worse |
| 10Y-2Y Yield Spread | FRED API | Inverted = recession signal | Inverted is worse |
| VIX Level | yfinance (^VIX) | Market fear gauge | Elevated is worse |
| VIX Term Structure | calculated | Backwardation = near-term fear | Backwardation is worse |
| S&P 500 Breadth | calculated | % of stocks above 200 DMA | Narrow breadth is worse |
| High Yield Spread | FRED API | Credit stress indicator | Widening is worse |
| ISM Manufacturing | FRED API | Economic expansion/contraction | Below 50 is worse |
| Consumer Confidence | FRED API | Spending outlook | Declining is worse |
| M2 Money Supply Growth | FRED API | Liquidity conditions | Contracting is worse |

### 6. SECTOR CYCLE (Industry-Level)
Is this specific sector in expansion or contraction?

| Variable | Source | Signal | Weight Direction |
|----------|--------|--------|-----------------|
| Sector P/E vs Historical | calculated | Current vs 10Y average for sector | Above average is worse |
| Sector Revenue Growth | aggregated | Industry growth deceleration | Decelerating is worse |
| Sector ETF Relative Strength | yfinance | Sector vs S&P 500 momentum | Underperforming is worse |
| IPO Volume in Sector | research | High IPO volume = late cycle euphoria | High is worse |
| M&A Volume in Sector | research | Defensive M&A = incumbents scared | Rising from low is worse |
| Regulatory Pressure | research/news | New regulation compresses multiples | Increasing is worse |

### 7. INSTITUTIONAL BEHAVIOR (Flow)
What are the big players doing? Smart money moves first.

| Variable | Source | Signal | Weight Direction |
|----------|--------|--------|-----------------|
| Insider Selling Ratio | SEC Form 4 | Insiders dumping their own stock | Selling is worse |
| Institutional Ownership Change | 13-F filings | Are funds adding or trimming? | Decreasing is worse |
| Short Interest % Float | yfinance/FINRA | Smart money betting against | Increasing is worse |
| Put/Call Ratio | options chain | Hedging activity increasing | Rising is worse |
| Analyst Revision Direction | yfinance | Estimates being cut | Downgrades are worse |
| Earnings Surprise Trend | quarterly | Missing estimates repeatedly | Misses are worse |

### 8. COMPETITIVE THREAT (Company-Specific)
Is there a specific competitor eating this company's lunch?

| Variable | Source | Signal | Weight Direction |
|----------|--------|--------|-----------------|
| Competitor Revenue Growth | research | Is the disruptor growing fast? | Faster is worse for incumbent |
| Market Share Trend | research | Incumbent losing share? | Losing is worse |
| Price Differential | research | Competitor offering same thing cheaper? | Larger gap is worse |
| Technology Gap | research/manual | Is the competitor technologically superior? | Wider gap is worse |
| Time to Parity | estimated | How long until competitor matches features? | Shorter is worse |

## Scoring Architecture

```
TOTAL_PRESSURE = (
    valuation_pressure    * w1 +    # How overpriced
    margin_fragility      * w2 +    # How vulnerable to margin attack
    (1 - moat_strength)   * w3 +    # How defenseless (inverted)
    financial_stress      * w4 +    # How little runway
    cycle_pressure        * w5 +    # How late in macro cycle
    sector_pressure       * w6 +    # How extended the sector is
    institutional_exit    * w7 +    # Are smart money leaving
    competitive_threat    * w8      # Is someone eating the lunch
)
```

## The Convergence Signal

The model does NOT require any single variable to be extreme. The signal comes from CONVERGENCE:

- 4 out of 8 categories pointing down with moderate scores = WATCH
- 6 out of 8 categories pointing down = STRONG SIGNAL
- All 8 categories converging downward = MAXIMUM CONVICTION

This is why the model doesn't need a catalyst. When everything is aligned against a company, the catalyst can be ANYTHING -- a missed earnings, a competitor announcement, a rate hike, an analyst downgrade. The convergence means any match lights the fire.

## Weight Calibration Method

Weights are NOT guessed. They are extracted from historical compression autopsies:

1. For each historical compression event, document the cited reasons from 10-K, earnings calls, analyst reports, and post-mortems
2. Map each cited reason to a variable in this universe
3. Count how often each variable category appears as a cited factor
4. Normalize the counts to derive weights

Example calibration from Zoom (ZM):
- Cited reasons: "Microsoft Teams competition" (competitive threat), "post-COVID normalization" (sector cycle), "multiple compression from 130x" (valuation pressure), "no enterprise lock-in" (moat weakness)
- Variables activated: competitive_threat, sector_pressure, valuation_pressure, moat_strength
- 4 out of 8 categories = strong convergence

## Data Sources (Free Tier)

| Category | Primary Source | Cost |
|----------|---------------|------|
| Valuation | yfinance | Free |
| Margins | yfinance income_stmt | Free |
| Moat | Manual research + 10-K | Free |
| Financial Stress | yfinance balance_sheet | Free |
| Market Cycle | FRED API | Free |
| Sector Cycle | yfinance sector ETFs | Free |
| Institutional | yfinance + SEC EDGAR | Free |
| Competitive | Manual research | Free |

All 8 categories can be populated with free data sources. The manual/research items (moat, competitive threat) are entered through the dashboard per-company.
